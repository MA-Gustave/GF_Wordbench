"""Component and contract tests for the GF Wordbench bootstrap boundary."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from typing import Final

import pytest

from gf_wordbench.config.models import (
    ResolvedEnvironment,
    RunConfig,
    ValidationTarget,
)
from gf_wordbench.kernel.errors import UnsupportedVersionError
from gf_wordbench.kernel.ids import ProjectId, ScenarioId, SchemaId
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.projects.schema import validate_project_schema
from gf_wordbench.runs.paths import allocate_run_paths
from gf_wordbench.runs.planner import resolve_execution_plan
from gf_wordbench.runs.preflight import PreflightFilesystem, preflight_run

_RUN_ID: Final[str] = "20260725_120000"
_PUBLIC_FUNCTIONAL_FACADES: Final[dict[str, str]] = {
    "gf_wordbench.projects": "gf_wordbench.projects.public",
    "gf_wordbench.runs": "gf_wordbench.runs.public",
    "gf_wordbench.validation": "gf_wordbench.validation.public",
    "gf_wordbench.diagnostics": "gf_wordbench.diagnostics.public",
    "gf_wordbench.reporting": "gf_wordbench.reporting.public",
}
_FORBIDDEN_RUN_PATH_LITERALS: Final[frozenset[str]] = frozenset(
    {
        "run_",
        "summary.json",
        "summary.md",
        "AI_READY.md",
        "top_errors.txt",
        "manifest.json",
        "details",
        "raw",
        "master.log",
        "ALL_SCAN_LOGS.TXT",
        "ALL_LOGS.TXT",
        "artifacts",
        "gfo",
        "out",
        "pgf",
    }
)


class _FakeFilesystem:
    def __init__(
        self,
        *,
        missing: frozenset[Path] = frozenset(),
        unwritable: frozenset[Path] = frozenset(),
    ) -> None:
        self._missing = {
            path.resolve(strict=False)
            for path in missing
        }
        self._unwritable = {
            path.resolve(strict=False)
            for path in unwritable
        }

    def normalize(self, path: Path) -> Path:
        if not isinstance(path, Path):
            raise TypeError("path must be pathlib.Path")
        return path.resolve(strict=False)

    def resolve(self, path: Path) -> Path:
        return self.normalize(path)

    def exists(self, path: Path) -> bool:
        return self.normalize(path) not in self._missing

    def is_file(self, path: Path) -> bool:
        normalized = self.normalize(path)
        if normalized in self._missing:
            return False
        return (
            normalized.name in {"project.toml", "gf", "gf.exe"}
            or normalized.suffix.casefold() in {".gf", ".gfs"}
        )

    def is_directory(self, path: Path) -> bool:
        normalized = self.normalize(path)
        return normalized not in self._missing and not self.is_file(normalized)

    def is_readable(self, path: Path) -> bool:
        return self.exists(path)

    def is_executable(self, path: Path) -> bool:
        return self.is_file(path)

    def is_writable_directory(self, path: Path) -> bool:
        normalized = self.normalize(path)
        return (
            self.is_directory(normalized)
            and normalized not in self._unwritable
        )


def _bootstrap_source_path() -> Path:
    specification = importlib.util.find_spec("gf_wordbench.bootstrap")
    assert specification is not None, "gf_wordbench.bootstrap is missing"
    assert specification.origin is not None
    source_path = Path(specification.origin)
    assert source_path.name == "bootstrap.py"
    assert source_path.is_file()
    return source_path


def _project_document(
    *,
    schema_version: str = "1.0",
) -> dict[str, object]:
    return {
        "schema_id": "gf-wordbench.project",
        "schema_version": schema_version,
        "project": {
            "id": "example-language",
            "name": "Example Language",
            "language_code": "eng",
            "root": ".",
        },
        "sources": {
            "directory": "src",
            "glob": "*.gf",
            "include_regex": r"^[A-Z][A-Za-z0-9_]*\.gf$",
            "exclude_regex": r"(\.bak\.gf$|\s)",
        },
        "gf": {
            "path_parts": ["src"],
            "minimum_version": "",
        },
        "modules": {
            "entrypoints": ["GrammarEng.gf"],
            "checkpoints": ["MorphoEng.gf"],
        },
        "validation": {
            "required_scenarios": ["load"],
            "optional_scenarios": [],
            "release_requires_pgf": True,
        },
    }


def _project_config(tmp_path: Path) -> ProjectConfig:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "src"
    return ProjectConfig(
        schema_id=SchemaId("gf-wordbench.project"),
        schema_version="1.0",
        identity=ProjectIdentity(
            id=ProjectId("example-language"),
            name="Example Language",
            language_code="eng",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="*.gf",
            include_regex=r"^[A-Z][A-Za-z0-9_]*\.gf$",
            exclude_regex=r"(\.bak\.gf$|\s)",
        ),
        gf=GFProjectConfig(
            path_parts=("src",),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("GrammarEng.gf"),),
            checkpoints=(Path("MorphoEng.gf"),),
        ),
        validation=ValidationPolicy(
            required_scenarios=(ScenarioId("load"),),
            optional_scenarios=(),
            release_requires_pgf=True,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )


def _run_config(
    tmp_path: Path,
    *,
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
    target: ValidationTarget | None = None,
    selected_checkpoints: tuple[Path, ...] | None = None,
    selected_entrypoints: tuple[Path, ...] | None = None,
    selected_scenarios: tuple[str, ...] | None = None,
    no_compile: bool = False,
    skip_version_probe: bool = False,
    max_files: int = 0,
) -> RunConfig:
    project = _project_config(tmp_path)
    source_root = project.source_root
    rgl_root = (tmp_path / "rgl").resolve()
    output_root = (tmp_path / "runs").resolve()

    if selected_checkpoints is None:
        selected_checkpoints = (
            (source_root / "MorphoEng.gf",)
            if mode is ValidationMode.CHECKPOINT
            else ()
        )
    if selected_entrypoints is None:
        selected_entrypoints = (
            (source_root / "GrammarEng.gf",)
            if mode is ValidationMode.RELEASE
            else ()
        )
    if selected_scenarios is None:
        selected_scenarios = (
            ("load",)
            if mode is ValidationMode.RELEASE
            else ()
        )

    return RunConfig(
        project=project,
        environment=ResolvedEnvironment(
            project_root=project.project_root,
            rgl_root=rgl_root,
            gf_executable=(tmp_path / "bin" / "gf").resolve(),
            output_root=output_root,
            gf_path=(source_root, rgl_root),
        ),
        mode=mode,
        target=target,
        timeout_sec=60,
        max_files=max_files,
        keep_ok_details=False,
        diff_previous=True,
        skip_version_probe=skip_version_probe,
        no_compile=no_compile,
        emit_cpu_stats=False,
        selected_checkpoints=selected_checkpoints,
        selected_entrypoints=selected_entrypoints,
        selected_scenarios=selected_scenarios,
        release_requires_pgf=True,
        evidence_level="standard",
    )


def _issue_codes(result: object) -> frozenset[str]:
    issues = getattr(result, "issues")
    return frozenset(issue.code for issue in issues)


def test_bootstrap_module_exists_at_the_canonical_path() -> None:
    assert _bootstrap_source_path().as_posix().endswith(
        "/gf_wordbench/bootstrap.py"
    )


def test_bootstrap_import_has_no_mutation_process_or_ui_side_effects(
    tmp_path: Path,
) -> None:
    script = r"""
import os
from pathlib import Path
import subprocess
import sys
import webbrowser

sys.dont_write_bytecode = True
events = []

def blocked(name):
    def fail(*args, **kwargs):
        events.append(name)
        raise AssertionError(name)
    return fail

subprocess.Popen = blocked("subprocess.Popen")
subprocess.run = blocked("subprocess.run")
subprocess.call = blocked("subprocess.call")
subprocess.check_call = blocked("subprocess.check_call")
subprocess.check_output = blocked("subprocess.check_output")
os.system = blocked("os.system")
webbrowser.open = blocked("webbrowser.open")

for name in (
    "mkdir",
    "rename",
    "replace",
    "rmdir",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
):
    setattr(Path, name, blocked(f"Path.{name}"))

before = tuple(sorted(item.name for item in Path.cwd().iterdir()))
import gf_wordbench.bootstrap
after = tuple(sorted(item.name for item in Path.cwd().iterdir()))

assert events == []
assert before == after
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )


def test_bootstrap_uses_public_functional_module_facades() -> None:
    source_path = _bootstrap_source_path()
    tree = ast.parse(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
    )

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        for package, facade in _PUBLIC_FUNCTIONAL_FACADES.items():
            if (
                node.module.startswith(f"{package}.")
                and node.module != facade
            ):
                violations.append(node.module)

    assert violations == []


def test_bootstrap_does_not_reconstruct_run_owned_paths() -> None:
    source_path = _bootstrap_source_path()
    tree = ast.parse(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
    )
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }
    assert literals.isdisjoint(_FORBIDDEN_RUN_PATH_LITERALS)


def test_bootstrap_exposes_the_gui_runtime_factory() -> None:
    module = importlib.import_module("gf_wordbench.bootstrap")
    exported = tuple(getattr(module, "__all__", ()))
    assert "build_gui_runtime" in exported
    assert callable(getattr(module, "build_gui_runtime", None))


def test_missing_project_is_rejected_before_execution(
    tmp_path: Path,
) -> None:
    configuration = _run_config(tmp_path)
    filesystem = _FakeFilesystem(
        missing=frozenset(
            {
                configuration.project.project_root,
                configuration.project.project_file,
            }
        )
    )

    result = preflight_run(
        configuration,
        filesystem=filesystem,
    )

    assert not result.succeeded
    assert {"GF-WB-CONFIG-101", "GF-WB-CONFIG-103"} <= _issue_codes(
        result
    )


def test_unsupported_project_schema_is_rejected() -> None:
    with pytest.raises(
        UnsupportedVersionError,
        match="unsupported major",
    ):
        validate_project_schema(
            _project_document(schema_version="2.0")
        )


def test_invalid_mode_type_is_rejected(
    tmp_path: Path,
) -> None:
    valid = _run_config(tmp_path)

    with pytest.raises(
        TypeError,
        match="mode must be a ValidationMode",
    ):
        RunConfig(
            project=valid.project,
            environment=valid.environment,
            mode="release",  # type: ignore[arg-type]
            target=None,
            timeout_sec=valid.timeout_sec,
            max_files=valid.max_files,
            keep_ok_details=valid.keep_ok_details,
            diff_previous=valid.diff_previous,
            skip_version_probe=valid.skip_version_probe,
            no_compile=valid.no_compile,
            emit_cpu_stats=valid.emit_cpu_stats,
            selected_checkpoints=(),
            selected_entrypoints=valid.selected_entrypoints,
            selected_scenarios=valid.selected_scenarios,
            release_requires_pgf=valid.release_requires_pgf,
            evidence_level=valid.evidence_level,
        )


def test_quick_mode_requires_a_target(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="quick mode requires a resolved target",
    ):
        _run_config(
            tmp_path,
            mode=ValidationMode.QUICK,
            target=None,
        )


def test_unknown_checkpoint_is_rejected_before_execution(
    tmp_path: Path,
) -> None:
    project = _project_config(tmp_path)
    configuration = _run_config(
        tmp_path,
        mode=ValidationMode.CHECKPOINT,
        target=ValidationTarget(
            kind=TargetKind.CHECKPOINT,
            value="Unknown.gf",
        ),
        selected_checkpoints=(
            project.source_root / "Unknown.gf",
        ),
    )

    result = preflight_run(
        configuration,
        filesystem=_FakeFilesystem(),
    )

    assert not result.succeeded
    assert "GF-WB-CONFIG-130" in _issue_codes(result)


@pytest.mark.parametrize(
    ("field_name", "overrides", "message"),
    (
        (
            "no_compile",
            {"no_compile": True},
            "release mode cannot disable compilation",
        ),
        (
            "skip_version_probe",
            {"skip_version_probe": True},
            "release mode cannot skip the version probe",
        ),
        (
            "max_files",
            {"max_files": 1},
            "release mode cannot limit selected files",
        ),
    ),
)
def test_release_mode_rejects_incompatible_flags(
    tmp_path: Path,
    field_name: str,
    overrides: dict[str, object],
    message: str,
) -> None:
    del field_name
    configuration = _run_config(
        tmp_path,
        mode=ValidationMode.RELEASE,
        target=ValidationTarget(
            kind=TargetKind.PROJECT,
            value=None,
        ),
        **overrides,
    )

    with pytest.raises(ValueError, match=message):
        resolve_execution_plan(configuration)


def test_unwritable_output_root_is_rejected_before_execution(
    tmp_path: Path,
) -> None:
    configuration = _run_config(tmp_path)
    filesystem = _FakeFilesystem(
        unwritable=frozenset(
            {configuration.environment.output_root}
        )
    )

    result = preflight_run(
        configuration,
        filesystem=filesystem,
    )

    assert not result.succeeded
    assert "GF-WB-CONFIG-116" in _issue_codes(result)


def test_run_id_collision_never_reuses_an_existing_run_directory(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    output_root.mkdir()
    collision = output_root / f"run_{_RUN_ID}"
    collision.mkdir()
    sentinel = collision / "existing.txt"
    sentinel.write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError):
        allocate_run_paths(output_root.resolve(), _RUN_ID)

    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert tuple(collision.iterdir()) == (sentinel,)
