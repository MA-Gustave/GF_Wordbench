"""Unit tests for canonical active-project validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.kernel.errors import (
    GFWordbenchError,
    ProjectConfigurationError,
)
from gf_wordbench.projects.models import (
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectCheckScope,
    ProjectConfig,
    ProjectDiagnosticSeverity,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.projects.paths import (
    ProjectPaths,
    resolve_module_path,
    resolve_scenario_path,
)
from gf_wordbench.projects.policies import REQUIRED_PROJECT_ASSETS
from gf_wordbench.projects.validator import (
    ProjectValidator,
    check_project,
    ensure_project_valid,
    validate_project,
)

_PROJECT_FILE: Final = Path("project.toml")
_ENTRYPOINT: Final = Path("GrammarFixture.gf")
_CHECKPOINT: Final = Path("CoreFixture.gf")
_REQUIRED_SCENARIO: Final = "smoke"
_OPTIONAL_SCENARIO: Final = "optional"


def _absolute(path: Path) -> Path:
    """Return a lexical absolute path without requiring filesystem access."""

    return Path(os.path.abspath(os.fspath(path)))


@dataclass(slots=True)
class _MemoryProjectFilesystem:
    """Read-only, deterministic implementation of the project filesystem port."""

    files: dict[Path, str] = field(default_factory=dict)
    directories: set[Path] = field(default_factory=set)
    resolved_paths: dict[Path, Path] = field(default_factory=dict)
    failures: dict[tuple[str, Path], BaseException] = field(default_factory=dict)
    calls: list[tuple[str, Path]] = field(default_factory=list)

    def add_directory(self, path: Path) -> None:
        current = _absolute(path)
        while True:
            self.directories.add(current)
            if current.parent == current:
                break
            current = current.parent

    def add_file(self, path: Path, content: str = "fixture\n") -> None:
        normalized = _absolute(path)
        self.add_directory(normalized.parent)
        self.files[normalized] = content

    def remove(self, path: Path) -> None:
        normalized = _absolute(path)
        self.files.pop(normalized, None)
        self.directories.discard(normalized)

    def redirect_resolution(self, source: Path, destination: Path) -> None:
        self.resolved_paths[_absolute(source)] = _absolute(destination)

    def fail(
        self,
        operation: str,
        path: Path,
        error: BaseException,
    ) -> None:
        self.failures[(operation, _absolute(path))] = error

    def snapshot(
        self,
    ) -> tuple[
        tuple[tuple[str, str], ...],
        tuple[str, ...],
        tuple[tuple[str, str], ...],
    ]:
        return (
            tuple(
                sorted(
                    (path.as_posix(), content)
                    for path, content in self.files.items()
                )
            ),
            tuple(sorted(path.as_posix() for path in self.directories)),
            tuple(
                sorted(
                    (source.as_posix(), destination.as_posix())
                    for source, destination in self.resolved_paths.items()
                )
            ),
        )

    def _record(self, operation: str, path: Path) -> Path:
        normalized = _absolute(path)
        self.calls.append((operation, normalized))
        error = self.failures.get((operation, normalized))
        if error is not None:
            raise error
        return normalized

    def resolve(self, path: Path) -> Path:
        normalized = self._record("resolve", path)
        return self.resolved_paths.get(normalized, normalized)

    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
        allow_root: bool = False,
    ) -> Path:
        normalized = self._record("require_contained", path)
        normalized_root = _absolute(root)
        try:
            relative = normalized.relative_to(normalized_root)
        except ValueError as error:
            raise ProjectConfigurationError(
                "Project path escapes its permitted root",
                subject=str(normalized),
            ) from error
        if not allow_root and relative == Path("."):
            raise ProjectConfigurationError(
                "Project path must be below its permitted root",
                subject=str(normalized),
            )
        return normalized

    def exists(self, path: Path) -> bool:
        normalized = self._record("exists", path)
        return normalized in self.files or normalized in self.directories

    def is_file(self, path: Path) -> bool:
        normalized = self._record("is_file", path)
        return normalized in self.files

    def is_directory(self, path: Path) -> bool:
        normalized = self._record("is_directory", path)
        return normalized in self.directories

    def read_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        normalized = self._record("read_text", path)
        if encoding.casefold().replace("_", "-") != "utf-8":
            raise UnicodeError("unsupported fixture encoding")
        try:
            return self.files[normalized]
        except KeyError as error:
            raise FileNotFoundError(normalized) from error


def _project(root: Path) -> ProjectConfig:
    project_root = _absolute(root)
    source_root = project_root / "src"
    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="fixture",
            name="Fixture Language",
            language_code="fx",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="*.gf",
            include_regex=r"^[A-Z][A-Za-z0-9_]*\.gf$",
            exclude_regex=r"(?:\.bak\.gf$|\.tmp\.gf$|\s)",
        ),
        gf=GFProjectConfig(
            path_parts=("src",),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(_ENTRYPOINT,),
            checkpoints=(_CHECKPOINT,),
        ),
        validation=ValidationPolicy(
            required_scenarios=(_REQUIRED_SCENARIO,),
            optional_scenarios=(_OPTIONAL_SCENARIO,),
            release_requires_pgf=False,
        ),
        project_file=project_root / _PROJECT_FILE,
        project_root=project_root,
        source_root=source_root,
    )


def _complete_filesystem(project: ProjectConfig) -> _MemoryProjectFilesystem:
    filesystem = _MemoryProjectFilesystem()
    project_paths = ProjectPaths.from_root(project.project_root)

    filesystem.add_file(project.project_file, "schema_id = 'gf-wordbench.project'\n")
    filesystem.add_directory(project.source_root)

    for target in project.modules.entrypoints + project.modules.checkpoints:
        filesystem.add_file(resolve_module_path(project.source_root, target))

    for scenario_id in project.validation.all_scenarios:
        filesystem.add_file(
            resolve_scenario_path(project_paths, str(scenario_id)),
            f'ps "GF_WORDBENCH_SCENARIO_BEGIN:{scenario_id}"\n'
            f'ps "GF_WORDBENCH_SCENARIO_END:{scenario_id}"\n'
            "q\n",
        )

    for relative_path in REQUIRED_PROJECT_ASSETS:
        filesystem.add_file(
            project.project_root / relative_path,
            "Reviewed fixture project asset.\n",
        )

    return filesystem


def _diagnostic_codes(result: object) -> tuple[str, ...]:
    diagnostics = getattr(result, "diagnostics")
    return tuple(item.code for item in diagnostics)


def test_validate_project_accepts_complete_project_without_mutation(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    before = filesystem.snapshot()

    result = validate_project(
        project,
        filesystem,
        scope=ProjectCheckScope.NORMAL,
        strict=True,
    )

    assert result.ok
    assert result.diagnostics == ()
    assert filesystem.snapshot() == before
    assert filesystem.calls
    assert all(
        operation
        in {
            "resolve",
            "require_contained",
            "exists",
            "is_file",
            "is_directory",
            "read_text",
        }
        for operation, _ in filesystem.calls
    )


def test_configuration_scope_performs_no_filesystem_access(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path / "absent-project")
    filesystem = _MemoryProjectFilesystem()

    result = validate_project(
        project,
        filesystem,
        scope=ProjectCheckScope.CONFIGURATION,
        strict=True,
    )

    assert result.ok
    assert result.diagnostics == ()
    assert filesystem.calls == []


@pytest.mark.parametrize(
    ("missing", "expected_code", "expected_field"),
    [
        (
            "project_file",
            "PROJECT_CONFIG_MISSING",
            "project_file",
        ),
        (
            "source_root",
            "PROJECT_SOURCE_ROOT_MISSING",
            "sources.directory",
        ),
        (
            "entrypoint",
            "PROJECT_ENTRYPOINT_MISSING",
            "modules.entrypoints[0]",
        ),
        (
            "checkpoint",
            "PROJECT_CHECKPOINT_MISSING",
            "modules.checkpoints[0]",
        ),
        (
            "required_scenario",
            "PROJECT_SCENARIO_MISSING",
            "validation.required_scenarios[0]",
        ),
        (
            "required_asset",
            "PROJECT_DOCUMENT_MISSING",
            REQUIRED_PROJECT_ASSETS[0].as_posix(),
        ),
    ],
)
def test_missing_required_project_inputs_are_errors(
    tmp_path: Path,
    missing: str,
    expected_code: str,
    expected_field: str,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    project_paths = ProjectPaths.from_root(project.project_root)

    missing_path = {
        "project_file": project.project_file,
        "source_root": project.source_root,
        "entrypoint": resolve_module_path(
            project.source_root,
            project.modules.entrypoints[0],
        ),
        "checkpoint": resolve_module_path(
            project.source_root,
            project.modules.checkpoints[0],
        ),
        "required_scenario": resolve_scenario_path(
            project_paths,
            str(project.validation.required_scenarios[0]),
        ),
        "required_asset": project.project_root / REQUIRED_PROJECT_ASSETS[0],
    }[missing]
    filesystem.remove(missing_path)

    result = validate_project(project, filesystem)

    matching = tuple(
        item
        for item in result.errors
        if item.code == expected_code and item.field == expected_field
    )
    assert len(matching) == 1
    assert matching[0].severity is ProjectDiagnosticSeverity.ERROR
    assert matching[0].source_file == project.project_file
    assert matching[0].subject == _absolute(missing_path)
    assert not result.ok


def test_missing_optional_scenario_is_warning_only(tmp_path: Path) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    optional_path = resolve_scenario_path(
        ProjectPaths.from_root(project.project_root),
        str(project.validation.optional_scenarios[0]),
    )
    filesystem.remove(optional_path)

    result = validate_project(project, filesystem)

    assert result.ok
    assert result.errors == ()
    assert len(result.warnings) == 1
    warning = result.warnings[0]
    assert warning.code == "PROJECT_SCENARIO_MISSING"
    assert warning.field == "validation.optional_scenarios[0]"
    assert warning.severity is ProjectDiagnosticSeverity.WARNING
    assert warning.subject == optional_path


@pytest.mark.parametrize(
    ("scope", "strict", "expected_error"),
    [
        (ProjectCheckScope.NORMAL, False, False),
        (ProjectCheckScope.NORMAL, True, True),
        (ProjectCheckScope.RELEASE, False, True),
        (ProjectCheckScope.RELEASE, True, True),
    ],
)
def test_placeholder_inspection_follows_strict_and_release_policy(
    tmp_path: Path,
    scope: ProjectCheckScope,
    strict: bool,
    expected_error: bool,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    contract = project.project_root / "docs" / "INTERFILE_CONTRACT_LOCK.md"
    filesystem.add_file(contract, "Owner: <OWNER>\n")

    result = validate_project(
        project,
        filesystem,
        scope=scope,
        strict=strict,
    )

    placeholders = tuple(
        item
        for item in result.diagnostics
        if item.code == "PROJECT_PLACEHOLDER_UNRESOLVED"
    )
    assert bool(placeholders) is expected_error
    if expected_error:
        assert placeholders[0].subject == contract
        assert not result.ok
    else:
        assert result.ok


def test_module_resolution_escape_is_reported_as_structured_error(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    entrypoint = resolve_module_path(
        project.source_root,
        project.modules.entrypoints[0],
    )
    outside = _absolute(tmp_path / "outside" / entrypoint.name)
    filesystem.redirect_resolution(entrypoint, outside)

    result = validate_project(project, filesystem)

    matching = tuple(
        item
        for item in result.errors
        if item.code == "PROJECT_SOURCE_ROOT_OUTSIDE"
        and item.field == "modules.entrypoints[0]"
    )
    assert len(matching) == 1
    assert matching[0].subject == entrypoint


@pytest.mark.parametrize(
    "error",
    [
        PermissionError("denied"),
        OSError("filesystem unavailable"),
        GFWordbenchError("bounded project filesystem failure"),
    ],
)
def test_filesystem_failures_become_bounded_diagnostics(
    tmp_path: Path,
    error: BaseException,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    filesystem.fail("exists", project.project_file, error)

    result = validate_project(project, filesystem)

    matching = tuple(
        item
        for item in result.errors
        if item.code == "PROJECT_FILESYSTEM_ERROR"
        and item.field == "project_file"
    )
    assert len(matching) == 1
    diagnostic = matching[0]
    assert type(error).__name__ in diagnostic.message
    assert "denied" not in diagnostic.message
    assert diagnostic.subject == project.project_file


@pytest.mark.parametrize(
    ("keyword", "value", "expected_exception"),
    [
        ("scope", "normal", TypeError),
        ("strict", 1, TypeError),
        ("strict", None, TypeError),
    ],
)
def test_validate_project_rejects_untyped_policy_arguments(
    tmp_path: Path,
    keyword: str,
    value: object,
    expected_exception: type[Exception],
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    arguments: dict[str, object] = {keyword: value}

    with pytest.raises(expected_exception):
        validate_project(project, filesystem, **arguments)  # type: ignore[arg-type]


def test_ensure_project_valid_returns_validated_result(tmp_path: Path) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)

    result = ensure_project_valid(
        project,
        filesystem,
        scope=ProjectCheckScope.NORMAL,
        strict=True,
    )

    assert result.ok
    assert result.diagnostics == ()


def test_ensure_project_valid_raises_structured_bounded_error(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _MemoryProjectFilesystem()

    with pytest.raises(
        ProjectConfigurationError,
        match="Active project validation failed",
    ) as captured:
        ensure_project_valid(project, filesystem, strict=True)

    error = captured.value
    assert error.code == "GF-WB-PROJECT-001"
    assert error.stage == "projects"
    assert error.operation == "validate-project"
    assert error.subject == str(project.project_file)
    assert "PROJECT_CONFIG_MISSING" in error.detail
    assert "additional error(s)" in error.detail
    assert error.detail.count(";") <= 8


def test_check_project_matches_functional_validator(tmp_path: Path) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)

    direct = validate_project(
        project,
        filesystem,
        scope=ProjectCheckScope.RELEASE,
        strict=True,
    )
    public = check_project(
        project,
        filesystem,
        scope=ProjectCheckScope.RELEASE,
        strict=True,
    )

    assert public == direct


def test_project_validator_supports_load_validation(tmp_path: Path) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    validator = ProjectValidator(filesystem)

    result = validator.validate_for_load(project)

    assert result.ok
    assert result.diagnostics == ()


def test_project_validator_rejects_invalid_load_project(tmp_path: Path) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    filesystem.remove(project.project_file)
    validator = ProjectValidator(filesystem)

    with pytest.raises(ProjectConfigurationError) as captured:
        validator.validate_for_load(project)

    assert captured.value.code == "GF-WB-PROJECT-001"
    assert "PROJECT_CONFIG_MISSING" in captured.value.detail


def test_diagnostics_preserve_deterministic_validation_order(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path / "project")
    filesystem = _complete_filesystem(project)
    filesystem.remove(project.project_file)
    filesystem.remove(
        resolve_module_path(
            project.source_root,
            project.modules.entrypoints[0],
        )
    )
    filesystem.remove(
        resolve_scenario_path(
            ProjectPaths.from_root(project.project_root),
            str(project.validation.required_scenarios[0]),
        )
    )
    filesystem.remove(project.project_root / REQUIRED_PROJECT_ASSETS[0])

    first = validate_project(project, filesystem)
    second = validate_project(project, filesystem)

    assert first == second
    assert _diagnostic_codes(first) == (
        "PROJECT_CONFIG_MISSING",
        "PROJECT_ENTRYPOINT_MISSING",
        "PROJECT_SCENARIO_MISSING",
        "PROJECT_DOCUMENT_MISSING",
    )
