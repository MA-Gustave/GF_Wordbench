from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest

from gf_wordbench.config.models import (
    ResolvedEnvironment,
    RunConfig,
    ValidationTarget,
)
from gf_wordbench.kernel.errors import (
    ConfigurationError,
    EvidenceIOError,
    PathSecurityError,
)
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.validation.selection.service import (
    SelectionFilesystem,
    SelectionService,
    extract_module_name,
    select_files,
)


@dataclass(slots=True)
class RecordingFilesystem:
    """Controllable adapter implementing the selection filesystem port."""

    fail_method: str | None = None
    fail_name: str | None = None
    unreadable_names: frozenset[str] = frozenset()
    rglob_result: tuple[Path, ...] | None = None
    calls: list[tuple[str, Path]] = field(default_factory=list)

    def _record(self, method: str, path: Path) -> None:
        self.calls.append((method, path))
        if self.fail_method == method and (
            self.fail_name is None or path.name == self.fail_name
        ):
            raise OSError(f"forced {method} failure for {path}")

    def resolve(self, path: Path, *, strict: bool) -> Path:
        self._record("resolve", path)
        return path.resolve(strict=strict)

    def exists(self, path: Path) -> bool:
        self._record("exists", path)
        return path.exists()

    def is_file(self, path: Path) -> bool:
        self._record("is_file", path)
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        self._record("is_directory", path)
        return path.is_dir()

    def is_readable(self, path: Path) -> bool:
        self._record("is_readable", path)
        return path.name not in self.unreadable_names and os.access(path, os.R_OK)

    def rglob(self, root: Path, pattern: str) -> tuple[Path, ...]:
        self._record("rglob", root)
        if self.rglob_result is not None:
            return self.rglob_result
        return tuple(root.rglob(pattern))


def _write_gf(path: Path, module_name: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    name = module_name or path.stem
    path.write_text(f"resource {name} = {{}}\n", encoding="utf-8")
    return path.resolve()


def _run_config(
    tmp_path: Path,
    *,
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
    target: str | None = None,
    source_glob: str = "**/*.gf",
    include_regex: str = r".*\.gf$",
    exclude_regex: str = r"\A\Z",
    max_files: int = 0,
    selected_checkpoints: tuple[Path, ...] = (),
    selected_entrypoints: tuple[Path, ...] = (),
) -> RunConfig:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "src"
    source_root.mkdir(parents=True, exist_ok=True)
    (project_root / "project.toml").write_text(
        "# selection service fixture\n",
        encoding="utf-8",
    )

    rgl_root = (tmp_path / "rgl").resolve()
    gf_executable = (tmp_path / "tools" / "gf").resolve()
    output_root = (tmp_path / "runs-not-created-by-selection").resolve()

    project = ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="selection-service-fixture",
            name="Selection Service Fixture",
            language_code="xss",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob=source_glob,
            include_regex=include_regex,
            exclude_regex=exclude_regex,
        ),
        gf=GFProjectConfig(path_parts=("src",), minimum_version=""),
        modules=ModuleTargets(
            entrypoints=tuple(
                path.relative_to(source_root)
                if path.is_absolute()
                else path
                for path in selected_entrypoints
            ),
            checkpoints=tuple(
                path.relative_to(source_root)
                if path.is_absolute()
                else path
                for path in selected_checkpoints
            ),
        ),
        validation=ValidationPolicy(
            required_scenarios=(),
            optional_scenarios=(),
            release_requires_pgf=False,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )

    if mode is ValidationMode.QUICK:
        resolved_target = target or "src/Alpha.gf"
        validation_target = ValidationTarget(
            kind=TargetKind.FILE,
            value=resolved_target,
        )
    else:
        validation_target = None

    if mode is ValidationMode.CHECKPOINT and not selected_checkpoints:
        selected_checkpoints = (source_root / "Checkpoint.gf",)
    if mode is ValidationMode.RELEASE and not selected_entrypoints:
        selected_entrypoints = (source_root / "Grammar.gf",)

    return RunConfig(
        project=project,
        environment=ResolvedEnvironment(
            project_root=project_root,
            rgl_root=rgl_root,
            gf_executable=gf_executable,
            output_root=output_root,
            gf_path=(source_root, rgl_root),
        ),
        mode=mode,
        target=validation_target,
        timeout_sec=30,
        max_files=max_files,
        keep_ok_details=False,
        diff_previous=False,
        skip_version_probe=True,
        no_compile=False,
        emit_cpu_stats=False,
        selected_checkpoints=selected_checkpoints,
        selected_entrypoints=selected_entrypoints,
        selected_scenarios=(),
        release_requires_pgf=False,
        evidence_level="standard",
    )


def _tree_snapshot(root: Path) -> dict[str, tuple[str, int]]:
    snapshot: dict[str, tuple[str, int]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot[relative] = (digest, path.stat().st_mtime_ns)
    return snapshot


def test_selection_filesystem_protocol_is_runtime_checkable(tmp_path: Path) -> None:
    filesystem = RecordingFilesystem()

    assert isinstance(filesystem, SelectionFilesystem)

    with pytest.raises(TypeError, match="filesystem must satisfy"):
        SelectionService(filesystem=object())  # type: ignore[arg-type]


def test_select_files_requires_a_run_config() -> None:
    with pytest.raises(TypeError, match="run_config must be a RunConfig"):
        select_files(object())  # type: ignore[arg-type]


def test_select_files_uses_the_supplied_filesystem_port(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    alpha = _write_gf(run_config.project.source_root / "Alpha.gf")
    filesystem = RecordingFilesystem(rglob_result=(alpha,))

    selected, excluded = select_files(run_config, filesystem=filesystem)

    assert selected == [alpha]
    assert excluded == []
    assert ("rglob", run_config.project.source_root) in filesystem.calls


def test_service_returns_absolute_resolved_paths(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    alpha = _write_gf(run_config.project.source_root / "nested" / "Alpha.gf")

    selected, excluded = SelectionService().select(run_config)

    assert selected == [alpha]
    assert excluded == []
    assert all(path.is_absolute() for path in selected)
    assert all(path == path.resolve() for path in selected)


def test_service_rejects_a_missing_project_root(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    shutil.rmtree(run_config.project.project_root)

    with pytest.raises(ConfigurationError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-CONFIG-234"
    assert captured.value.subject == "project.project_root"


def test_service_rejects_a_missing_source_root(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    run_config.project.source_root.rmdir()

    with pytest.raises(ConfigurationError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-CONFIG-234"
    assert captured.value.subject == "project.source_root"


def test_service_rejects_a_source_root_that_is_a_file(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    source_root = run_config.project.source_root
    source_root.rmdir()
    source_root.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(ConfigurationError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-CONFIG-235"
    assert captured.value.subject == "project.source_root"


def test_service_rejects_an_unreadable_required_root(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    filesystem = RecordingFilesystem(
        unreadable_names=frozenset({run_config.project.source_root.name})
    )

    with pytest.raises(EvidenceIOError) as captured:
        SelectionService(filesystem=filesystem).select(run_config)

    assert captured.value.code == "GF-WB-IO-221"
    assert captured.value.operation == "resolve_selection_roots"
    assert captured.value.subject == "project.source_root"
    assert captured.value.retryable is True


def test_service_rejects_environment_project_root_drift(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    other_root = (tmp_path / "other-project").resolve()
    drifted_environment = replace(
        run_config.environment,
        project_root=other_root,
    )
    run_config = replace(run_config, environment=drifted_environment)

    with pytest.raises(ConfigurationError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-CONFIG-222"
    assert captured.value.subject == "environment.project_root"


def test_service_rejects_loaded_source_root_drift(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    drifted_root = (run_config.project.project_root / "other-src").resolve()
    object.__setattr__(run_config.project, "source_root", drifted_root)

    with pytest.raises(ConfigurationError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-CONFIG-221"
    assert captured.value.subject == "project.source_root"


def test_service_rejects_a_source_root_symlink_escape(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    source_root = run_config.project.source_root
    source_root.rmdir()
    outside = (tmp_path / "outside-source").resolve()
    outside.mkdir()

    try:
        source_root.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    with pytest.raises(PathSecurityError) as captured:
        SelectionService().select(run_config)

    assert captured.value.code == "GF-WB-PATH-220"
    assert captured.value.operation == "resolve_source_root"


@pytest.mark.parametrize(
    ("fail_method", "fail_name", "expected_code", "expected_operation"),
    [
        ("resolve", "project", "GF-WB-IO-223", "resolve_required_directory"),
        ("exists", "project", "GF-WB-IO-224", "exists"),
        ("is_directory", "project", "GF-WB-IO-226", "is_directory"),
        ("is_readable", "project", "GF-WB-IO-227", "is_readable"),
    ],
)
def test_service_adapts_required_root_os_errors(
    tmp_path: Path,
    fail_method: str,
    fail_name: str,
    expected_code: str,
    expected_operation: str,
) -> None:
    run_config = _run_config(tmp_path)
    filesystem = RecordingFilesystem(
        fail_method=fail_method,
        fail_name=fail_name,
    )

    with pytest.raises(EvidenceIOError) as captured:
        SelectionService(filesystem=filesystem).select(run_config)

    assert captured.value.code == expected_code
    assert captured.value.operation == expected_operation
    assert captured.value.stage == "selection"
    assert captured.value.retryable is True
    assert isinstance(captured.value.__cause__, OSError)


def test_service_adapts_candidate_enumeration_os_errors(tmp_path: Path) -> None:
    run_config = _run_config(tmp_path)
    filesystem = RecordingFilesystem(
        fail_method="rglob",
        fail_name=run_config.project.source_root.name,
    )

    with pytest.raises(EvidenceIOError) as captured:
        SelectionService(filesystem=filesystem).select(run_config)

    assert captured.value.code == "GF-WB-IO-222"
    assert captured.value.operation == "enumerate_candidate_files"
    assert captured.value.subject == str(run_config.project.source_root)
    assert captured.value.retryable is True
    assert isinstance(captured.value.__cause__, OSError)


@pytest.mark.parametrize(
    ("fail_method", "expected_code", "expected_operation"),
    [
        ("resolve", "GF-WB-IO-223", "normalize_candidate"),
        ("exists", "GF-WB-IO-224", "exists"),
        ("is_file", "GF-WB-IO-225", "is_file"),
        ("is_readable", "GF-WB-IO-227", "is_readable"),
    ],
)
def test_service_adapts_candidate_inspection_os_errors(
    tmp_path: Path,
    fail_method: str,
    expected_code: str,
    expected_operation: str,
) -> None:
    run_config = _run_config(tmp_path)
    alpha = _write_gf(run_config.project.source_root / "Alpha.gf")
    filesystem = RecordingFilesystem(
        fail_method=fail_method,
        fail_name=alpha.name,
        rglob_result=(alpha,),
    )

    with pytest.raises(EvidenceIOError) as captured:
        SelectionService(filesystem=filesystem).select(run_config)

    assert captured.value.code == expected_code
    assert captured.value.operation == expected_operation
    assert captured.value.stage == "selection"
    assert captured.value.retryable is True
    assert isinstance(captured.value.__cause__, OSError)


def test_service_does_not_create_output_directories_or_modify_sources(
    tmp_path: Path,
) -> None:
    run_config = _run_config(tmp_path)
    _write_gf(run_config.project.source_root / "Alpha.gf")
    _write_gf(run_config.project.source_root / "nested" / "Beta.gf")
    before = _tree_snapshot(run_config.project.project_root)

    selected, excluded = SelectionService().select(run_config)

    after = _tree_snapshot(run_config.project.project_root)
    assert [path.name for path in selected] == ["Alpha.gf", "Beta.gf"]
    assert excluded == []
    assert before == after
    assert not run_config.environment.output_root.exists()


def test_extract_module_name_returns_the_filename_stem() -> None:
    assert extract_module_name(Path("nested/GrammarX.gf")) == "GrammarX"
    assert extract_module_name(Path("Compound.Name.gf")) == "Compound.Name"


def test_extract_module_name_validates_its_path_contract() -> None:
    with pytest.raises(TypeError, match="pathlib.Path"):
        extract_module_name("GrammarX.gf")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="identify a file"):
        extract_module_name(Path())
