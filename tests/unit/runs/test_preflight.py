"""Unit tests for read-only run preflight validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
import os
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.config.models import (
    IssueSeverity,
    ResolvedEnvironment,
    RunConfig,
    ValidationTarget,
)
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.ids import validate_project_id, validate_scenario_id
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    PROJECT_CONFIG_FILENAME,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.projects.paths import ProjectPaths, resolve_scenario_path
from gf_wordbench.runs.preflight import (
    PreflightCheck,
    PreflightFilesystem,
    PreflightIssue,
    PreflightResult,
    preflight_run,
    require_preflight,
)


def _key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


@dataclass(slots=True)
class _FakeFilesystem:
    files: set[Path]
    directories: set[Path]
    readable: set[Path]
    executable: set[Path]
    writable: set[Path]
    resolved: dict[Path, Path]

    def normalize(self, path: Path) -> Path:
        return Path(os.path.normpath(os.fspath(path)))

    def resolve(self, path: Path) -> Path:
        normalized = self.normalize(path)
        return self.resolved.get(normalized, normalized)

    def exists(self, path: Path) -> bool:
        normalized = self.normalize(path)
        return normalized in self.files or normalized in self.directories

    def is_file(self, path: Path) -> bool:
        return self.normalize(path) in self.files

    def is_directory(self, path: Path) -> bool:
        return self.normalize(path) in self.directories

    def is_readable(self, path: Path) -> bool:
        return self.normalize(path) in self.readable

    def is_executable(self, path: Path) -> bool:
        return self.normalize(path) in self.executable

    def is_writable_directory(self, path: Path) -> bool:
        normalized = self.normalize(path)
        return normalized in self.directories and normalized in self.writable


@dataclass(frozen=True, slots=True)
class _Harness:
    configuration: RunConfig
    filesystem: _FakeFilesystem


def _project(tmp_path: Path, **overrides: object) -> ProjectConfig:
    project_root = tmp_path / "active-project"
    sources = SourceConfig(
        directory=Path("src"),
        glob="**/*.gf",
        include_regex="",
        exclude_regex="",
    )
    values: dict[str, object] = {
        "schema_id": PROJECT_SCHEMA_ID,
        "schema_version": PROJECT_SCHEMA_VERSION,
        "identity": ProjectIdentity(
            id=validate_project_id("example-language"),
            name="Example Language",
            language_code="Exa",
            root=Path("."),
        ),
        "sources": sources,
        "gf": GFProjectConfig(
            path_parts=("src", "rgl"),
            minimum_version="3.12",
        ),
        "modules": ModuleTargets(
            entrypoints=(Path("Main.gf"), Path("Secondary.gf")),
            checkpoints=(Path("Checkpoint.gf"),),
        ),
        "validation": ValidationPolicy(
            required_scenarios=(
                validate_scenario_id("parse-basic"),
                validate_scenario_id("generate-basic"),
            ),
            optional_scenarios=(validate_scenario_id("unicode-smoke"),),
            release_requires_pgf=True,
        ),
        "project_file": project_root / PROJECT_CONFIG_FILENAME,
        "project_root": project_root,
        "source_root": project_root / sources.directory,
    }
    values.update(overrides)
    return ProjectConfig(**cast("Any", values))


def _configuration(tmp_path: Path, **overrides: object) -> RunConfig:
    project = cast("ProjectConfig", overrides.pop("project", _project(tmp_path)))
    environment = ResolvedEnvironment(
        project_root=project.project_root,
        rgl_root=tmp_path / "rgl",
        gf_executable=tmp_path / "bin" / "gf",
        output_root=tmp_path / "runs",
        gf_path=(project.source_root, tmp_path / "rgl"),
    )
    values: dict[str, object] = {
        "project": project,
        "environment": environment,
        "mode": ValidationMode.DIAGNOSTIC,
        "target": ValidationTarget(TargetKind.PROJECT, None),
        "timeout_sec": 60,
        "max_files": 0,
        "keep_ok_details": False,
        "diff_previous": False,
        "skip_version_probe": False,
        "no_compile": False,
        "emit_cpu_stats": False,
        "selected_checkpoints": tuple(
            project.source_root / path for path in project.modules.checkpoints
        ),
        "selected_entrypoints": tuple(
            project.source_root / path for path in project.modules.entrypoints
        ),
        "selected_scenarios": tuple(str(value) for value in project.validation.all_scenarios),
        "release_requires_pgf": project.validation.release_requires_pgf,
        "evidence_level": "standard",
        "compatibility_warnings": (),
    }
    values.update(overrides)
    return RunConfig(**cast("Any", values))


def _project_of(configuration: RunConfig) -> ProjectConfig:
    project = configuration.project
    assert isinstance(project, ProjectConfig)
    return project


def _filesystem(configuration: RunConfig) -> _FakeFilesystem:
    project = _project_of(configuration)
    environment = configuration.environment
    project_paths = ProjectPaths.from_root(project.project_root)

    declared_modules = {
        project.source_root / path
        for path in (
            *project.modules.entrypoints,
            *project.modules.checkpoints,
        )
    }
    scenario_files = {
        resolve_scenario_path(project_paths, str(scenario_id))
        for scenario_id in project.validation.all_scenarios
    }
    files = {
        project.project_file,
        environment.gf_executable,
        *declared_modules,
        *scenario_files,
    }
    if configuration.target is not None and configuration.target.value:
        raw_target = Path(configuration.target.value)
        if raw_target.is_absolute():
            files.add(raw_target)

    directories = {
        project.project_root,
        project.source_root,
        environment.rgl_root,
        environment.output_root,
        *environment.gf_path,
        project_paths.validation_dir,
        project_paths.scenarios_dir,
        project_paths.inputs_dir,
        project_paths.gold_dir,
    }
    return _FakeFilesystem(
        files=set(files),
        directories=set(directories),
        readable=set(files | directories),
        executable={environment.gf_executable},
        writable={environment.output_root},
        resolved={},
    )


def _harness(tmp_path: Path, **overrides: object) -> _Harness:
    configuration = _configuration(tmp_path, **overrides)
    return _Harness(configuration, _filesystem(configuration))


def _codes(result: PreflightResult) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)


def _issues_for(
    result: PreflightResult,
    code: str,
) -> tuple[PreflightIssue, ...]:
    return tuple(issue for issue in result.issues if issue.code == code)


def test_preflight_check_values_are_closed_and_canonical() -> None:
    assert {member.name: member.value for member in PreflightCheck} == {
        "PROJECT_ROOT": "project_root",
        "PROJECT_CONFIG": "project_config",
        "SOURCE_ROOT": "source_root",
        "ENVIRONMENT_PROJECT_ROOT": "environment_project_root",
        "GF_EXECUTABLE": "gf_executable",
        "RGL_ROOT": "rgl_root",
        "OUTPUT_ROOT": "output_root",
        "GF_PATH": "gf_path",
        "MODE": "mode",
        "TARGET": "target",
        "CHECKPOINTS": "checkpoints",
        "ENTRYPOINTS": "entrypoints",
        "SCENARIOS": "scenarios",
        "RELEASE_POLICY": "release_policy",
        "COMPATIBILITY": "compatibility",
    }


def test_preflight_filesystem_protocol_is_runtime_checkable(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)

    assert isinstance(harness.filesystem, PreflightFilesystem)
    assert not isinstance(object(), PreflightFilesystem)


def test_preflight_issue_is_frozen_and_preserves_structured_context(
    tmp_path: Path,
) -> None:
    issue = PreflightIssue(
        code="GF-WB-CONFIG-101",
        severity=IssueSeverity.ERROR,
        check=PreflightCheck.PROJECT_ROOT,
        field_path="project.project_root",
        message="The required directory does not exist.",
        remediation="Restore the active project directory.",
        path=tmp_path / "project" / ".." / "missing",
    )

    assert issue.path == tmp_path / "missing"
    with pytest.raises(FrozenInstanceError):
        issue.code = "GF-WB-CONFIG-102"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"code": "CONFIG-101"}, ValueError, "GF-WB-CONFIG"),
        ({"code": "GF-WB-CONFIG-1"}, ValueError, "<NNN>"),
        ({"code": "GF-WB-PATH-101"}, ValueError, "GF-WB-CONFIG"),
        ({"severity": "error"}, TypeError, "IssueSeverity"),
        ({"check": "project_root"}, TypeError, "PreflightCheck"),
        ({"field_path": ""}, ValueError, "field_path"),
        ({"message": ""}, ValueError, "message"),
        ({"remediation": ""}, ValueError, "remediation"),
    ],
)
def test_preflight_issue_rejects_invalid_contract_values(
    tmp_path: Path,
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    values: dict[str, object] = {
        "code": "GF-WB-CONFIG-101",
        "severity": IssueSeverity.ERROR,
        "check": PreflightCheck.PROJECT_ROOT,
        "field_path": "project.project_root",
        "message": "Invalid project root.",
        "remediation": "Choose the active project root.",
        "path": tmp_path / "project",
    }
    values.update(overrides)

    with pytest.raises(exception, match=message):
        PreflightIssue(**cast("Any", values))


def test_preflight_result_partitions_issues_and_requires_success(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    error = PreflightIssue(
        code="GF-WB-CONFIG-101",
        severity=IssueSeverity.ERROR,
        check=PreflightCheck.PROJECT_ROOT,
        field_path="project.project_root",
        message="Missing.",
        remediation="Restore it.",
    )
    warning = PreflightIssue(
        code="GF-WB-CONFIG-141",
        severity=IssueSeverity.WARNING,
        check=PreflightCheck.COMPATIBILITY,
        field_path="compatibility_warnings[0]",
        message="Untested GF version.",
        remediation="Review it.",
    )
    information = PreflightIssue(
        code="GF-WB-CONFIG-141",
        severity=IssueSeverity.INFO,
        check=PreflightCheck.COMPATIBILITY,
        field_path="compatibility_warnings[1]",
        message="Informational compatibility note.",
        remediation="Record it.",
    )
    result = PreflightResult(
        configuration=configuration,
        issues=(warning, error, information),
        checked_paths=(tmp_path / "project", tmp_path / "gf"),
    )

    assert result.succeeded is False
    assert result.errors == (error,)
    assert result.warnings == (warning,)
    assert result.information == (information,)

    with pytest.raises(ConfigurationError) as captured:
        result.require()

    error_value = captured.value
    assert error_value.code == "GF-WB-CONFIG-101"
    assert error_value.stage == "preflight"
    assert error_value.operation == "validate_run"
    assert error_value.subject == "project.project_root"
    assert "Remediation: Restore it." in error_value.detail


def test_preflight_result_rejects_duplicate_checked_paths(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    duplicate = tmp_path / "project"

    with pytest.raises(ValueError, match="duplicate"):
        PreflightResult(
            configuration=configuration,
            checked_paths=(duplicate, duplicate),
        )


def test_valid_preflight_succeeds_without_mutation(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    configuration = harness.configuration

    result = preflight_run(
        configuration,
        filesystem=harness.filesystem,
    )

    assert result.configuration is configuration
    assert result.succeeded is True
    assert result.issues == ()
    assert result.require() is configuration
    assert (
        require_preflight(
            configuration,
            filesystem=harness.filesystem,
        )
        is configuration
    )
    assert len({_key(path) for path in result.checked_paths}) == len(result.checked_paths)
    assert result.checked_paths[:3] == (
        _project_of(configuration).project_root,
        _project_of(configuration).project_file,
        _project_of(configuration).source_root,
    )


def test_preflight_rejects_invalid_boundary_inputs(tmp_path: Path) -> None:
    harness = _harness(tmp_path)

    with pytest.raises(TypeError, match="RunConfig"):
        preflight_run(cast("Any", object()))

    with pytest.raises(TypeError, match="PreflightFilesystem"):
        preflight_run(
            harness.configuration,
            filesystem=cast("Any", object()),
        )


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-101"),
        ("file", "GF-WB-CONFIG-102"),
        ("unreadable", "GF-WB-CONFIG-102"),
    ],
)
def test_project_root_failures_are_structured(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    path = _project_of(harness.configuration).project_root

    if kind == "missing":
        harness.filesystem.directories.remove(path)
        harness.filesystem.readable.discard(path)
    elif kind == "file":
        harness.filesystem.directories.remove(path)
        harness.filesystem.files.add(path)
    else:
        harness.filesystem.readable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)
    issue = _issues_for(result, expected_code)[0]
    assert issue.check is PreflightCheck.PROJECT_ROOT
    assert issue.field_path == "project.project_root"
    assert issue.path == path


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-103"),
        ("directory", "GF-WB-CONFIG-104"),
        ("unreadable", "GF-WB-CONFIG-104"),
    ],
)
def test_project_config_failures_are_structured(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    path = _project_of(harness.configuration).project_file

    if kind == "missing":
        harness.filesystem.files.remove(path)
        harness.filesystem.readable.discard(path)
    elif kind == "directory":
        harness.filesystem.files.remove(path)
        harness.filesystem.directories.add(path)
    else:
        harness.filesystem.readable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)
    issue = _issues_for(result, expected_code)[0]
    assert issue.check is PreflightCheck.PROJECT_CONFIG
    assert issue.field_path == "project.project_file"


def test_project_config_must_remain_inside_project_root(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    outside = tmp_path / "foreign" / "project.toml"
    object.__setattr__(configuration.project, "project_file", outside)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert "GF-WB-CONFIG-109" in _codes(result)


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-105"),
        ("file", "GF-WB-CONFIG-106"),
        ("unreadable", "GF-WB-CONFIG-106"),
    ],
)
def test_source_root_failures_are_structured(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    path = _project_of(harness.configuration).source_root

    if kind == "missing":
        harness.filesystem.directories.remove(path)
        harness.filesystem.readable.discard(path)
    elif kind == "file":
        harness.filesystem.directories.remove(path)
        harness.filesystem.files.add(path)
    else:
        harness.filesystem.readable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)


def test_source_root_must_remain_inside_project_root(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    outside = tmp_path / "foreign-source"
    object.__setattr__(configuration.project, "source_root", outside)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert "GF-WB-CONFIG-107" in _codes(result)


def test_environment_project_root_must_match_loaded_project(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    environment = replace(
        configuration.environment,
        project_root=tmp_path / "other-project",
    )
    configuration = replace(configuration, environment=environment)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    issue = _issues_for(result, "GF-WB-CONFIG-108")[0]
    assert issue.check is PreflightCheck.ENVIRONMENT_PROJECT_ROOT
    assert issue.path == environment.project_root


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-110"),
        ("directory", "GF-WB-CONFIG-111"),
        ("not-executable", "GF-WB-CONFIG-111"),
    ],
)
def test_gf_executable_failures_are_structured(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    path = harness.configuration.environment.gf_executable

    if kind == "missing":
        harness.filesystem.files.remove(path)
        harness.filesystem.readable.discard(path)
        harness.filesystem.executable.discard(path)
    elif kind == "directory":
        harness.filesystem.files.remove(path)
        harness.filesystem.directories.add(path)
        harness.filesystem.executable.discard(path)
    else:
        harness.filesystem.executable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)


@pytest.mark.parametrize(
    ("field", "kind", "expected_code"),
    [
        ("rgl", "missing", "GF-WB-CONFIG-112"),
        ("rgl", "file", "GF-WB-CONFIG-113"),
        ("rgl", "unreadable", "GF-WB-CONFIG-113"),
        ("output", "missing", "GF-WB-CONFIG-114"),
        ("output", "file", "GF-WB-CONFIG-115"),
        ("output", "unwritable", "GF-WB-CONFIG-116"),
    ],
)
def test_environment_directory_failures_are_structured(
    tmp_path: Path,
    field: str,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    environment = harness.configuration.environment
    path = environment.rgl_root if field == "rgl" else environment.output_root

    if kind == "missing":
        harness.filesystem.directories.remove(path)
        harness.filesystem.readable.discard(path)
        harness.filesystem.writable.discard(path)
    elif kind == "file":
        harness.filesystem.directories.remove(path)
        harness.filesystem.files.add(path)
    elif kind == "unreadable":
        harness.filesystem.readable.remove(path)
    else:
        harness.filesystem.writable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)


def test_output_root_must_not_overlap_project_owned_paths(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    environment = replace(
        configuration.environment,
        output_root=_project_of(configuration).project_root,
    )
    configuration = replace(configuration, environment=environment)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    issue = _issues_for(result, "GF-WB-CONFIG-142")[0]
    assert issue.check is PreflightCheck.OUTPUT_ROOT
    assert issue.path == _project_of(configuration).project_root


def test_resolved_output_symlink_overlap_is_detected(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    output = harness.configuration.environment.output_root
    project_root = _project_of(harness.configuration).project_root
    harness.filesystem.resolved[output] = project_root / "generated"

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-142" in _codes(result)


def test_empty_gf_path_is_rejected(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    environment = replace(configuration.environment, gf_path=())
    configuration = replace(configuration, environment=environment)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert "GF-WB-CONFIG-117" in _codes(result)


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-118"),
        ("file", "GF-WB-CONFIG-119"),
        ("unreadable", "GF-WB-CONFIG-119"),
    ],
)
def test_each_gf_path_component_must_be_a_readable_directory(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path)
    path = harness.configuration.environment.gf_path[0]

    if kind == "missing":
        harness.filesystem.directories.remove(path)
        harness.filesystem.readable.discard(path)
    elif kind == "file":
        harness.filesystem.directories.remove(path)
        harness.filesystem.files.add(path)
    else:
        harness.filesystem.readable.remove(path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)
    assert _issues_for(result, expected_code)[0].field_path == ("environment.gf_path[0]")


@pytest.mark.parametrize(
    ("mode", "field", "expected_code"),
    [
        (ValidationMode.QUICK, "target", "GF-WB-CONFIG-120"),
        (
            ValidationMode.CHECKPOINT,
            "selected_checkpoints",
            "GF-WB-CONFIG-121",
        ),
        (
            ValidationMode.RELEASE,
            "selected_entrypoints",
            "GF-WB-CONFIG-122",
        ),
    ],
)
def test_preflight_defensively_rejects_incomplete_mode_state(
    tmp_path: Path,
    mode: ValidationMode,
    field: str,
    expected_code: str,
) -> None:
    configuration = _configuration(tmp_path)
    object.__setattr__(configuration, "mode", mode)
    object.__setattr__(configuration, field, None if field == "target" else ())
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert expected_code in _codes(result)


def test_project_target_must_match_active_project_identity(
    tmp_path: Path,
) -> None:
    harness = _harness(
        tmp_path,
        target=ValidationTarget(TargetKind.PROJECT, "different-project"),
    )

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-123" in _codes(result)


def test_scenario_target_must_be_declared(tmp_path: Path) -> None:
    harness = _harness(
        tmp_path,
        target=ValidationTarget(TargetKind.SCENARIO, "unknown-scenario"),
    )

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-124" in _codes(result)


def test_non_project_target_requires_identity(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    target = ValidationTarget(TargetKind.MODULE, "Main.gf")
    object.__setattr__(target, "value", None)
    configuration = replace(configuration, target=target)
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert "GF-WB-CONFIG-125" in _codes(result)


def test_missing_file_target_is_rejected(tmp_path: Path) -> None:
    target_path = tmp_path / "active-project" / "src" / "Missing.gf"
    harness = _harness(
        tmp_path,
        target=ValidationTarget(TargetKind.FILE, str(target_path)),
    )
    harness.filesystem.files.discard(target_path)
    harness.filesystem.readable.discard(target_path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-126" in _codes(result)


def test_non_gf_source_target_is_rejected(tmp_path: Path) -> None:
    target_path = tmp_path / "active-project" / "README.md"
    harness = _harness(
        tmp_path,
        target=ValidationTarget(TargetKind.FILE, str(target_path)),
    )

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-127" in _codes(result)


def test_absolute_target_must_remain_inside_active_project(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "foreign" / "Outside.gf"
    harness = _harness(
        tmp_path,
        target=ValidationTarget(TargetKind.FILE, str(target_path)),
    )

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-128" in _codes(result)


@pytest.mark.parametrize(
    ("collection", "path", "expected_code"),
    [
        ("selected_checkpoints", "MissingCheckpoint.gf", "GF-WB-CONFIG-129"),
        ("selected_checkpoints", "ExtraCheckpoint.gf", "GF-WB-CONFIG-130"),
        ("selected_entrypoints", "MissingEntrypoint.gf", "GF-WB-CONFIG-131"),
        ("selected_entrypoints", "ExtraEntrypoint.gf", "GF-WB-CONFIG-132"),
    ],
)
def test_selected_module_membership_and_existence_are_enforced(
    tmp_path: Path,
    collection: str,
    path: str,
    expected_code: str,
) -> None:
    configuration = _configuration(tmp_path)
    selected_path = _project_of(configuration).source_root / path
    if collection == "selected_checkpoints":
        configuration = replace(
            configuration,
            selected_checkpoints=(selected_path,),
        )
    else:
        assert collection == "selected_entrypoints"
        configuration = replace(
            configuration,
            selected_entrypoints=(selected_path,),
        )
    filesystem = _filesystem(configuration)

    if "Missing" in path:
        filesystem.files.discard(selected_path)
        filesystem.readable.discard(selected_path)
    else:
        filesystem.files.add(selected_path)
        filesystem.readable.add(selected_path)

    result = preflight_run(configuration, filesystem=filesystem)

    assert expected_code in _codes(result)


def test_release_must_select_every_declared_entrypoint(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    configuration = replace(
        configuration,
        mode=ValidationMode.RELEASE,
        selected_entrypoints=(configuration.selected_entrypoints[0],),
    )
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    issue = _issues_for(result, "GF-WB-CONFIG-133")[0]
    assert issue.path == _project_of(configuration).source_root / "Secondary.gf"


def test_selected_scenario_must_be_declared(tmp_path: Path) -> None:
    harness = _harness(
        tmp_path,
        selected_scenarios=("unknown-scenario",),
    )

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-134" in _codes(result)


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        ("missing", "GF-WB-CONFIG-135"),
        ("unreadable", "GF-WB-CONFIG-136"),
    ],
)
def test_selected_scenario_file_must_exist_and_be_readable(
    tmp_path: Path,
    kind: str,
    expected_code: str,
) -> None:
    harness = _harness(tmp_path, selected_scenarios=("parse-basic",))
    scenario_path = resolve_scenario_path(
        ProjectPaths.from_root(_project_of(harness.configuration).project_root),
        "parse-basic",
    )

    if kind == "missing":
        harness.filesystem.files.remove(scenario_path)
        harness.filesystem.readable.discard(scenario_path)
    else:
        harness.filesystem.readable.remove(scenario_path)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert expected_code in _codes(result)


def test_release_must_select_every_required_scenario(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    configuration = replace(
        configuration,
        mode=ValidationMode.RELEASE,
        selected_scenarios=("parse-basic", "unicode-smoke"),
    )
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert "GF-WB-CONFIG-137" in _codes(result)
    assert any(
        "generate-basic" in issue.message for issue in _issues_for(result, "GF-WB-CONFIG-137")
    )


def test_resolved_release_policy_must_match_project_policy(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path, release_requires_pgf=False)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert "GF-WB-CONFIG-138" in _codes(result)


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"skip_version_probe": True}, "GF-WB-CONFIG-139"),
        ({"no_compile": True}, "GF-WB-CONFIG-140"),
    ],
)
def test_release_cannot_weaken_required_execution_policy(
    tmp_path: Path,
    overrides: dict[str, object],
    expected_code: str,
) -> None:
    configuration = _configuration(tmp_path)
    if "skip_version_probe" in overrides:
        configuration = replace(
            configuration,
            mode=ValidationMode.RELEASE,
            skip_version_probe=cast("bool", overrides["skip_version_probe"]),
        )
    else:
        configuration = replace(
            configuration,
            mode=ValidationMode.RELEASE,
            no_compile=cast("bool", overrides["no_compile"]),
        )
    filesystem = _filesystem(configuration)

    result = preflight_run(configuration, filesystem=filesystem)

    assert expected_code in _codes(result)


def test_compatibility_warnings_are_preserved_without_failing_preflight(
    tmp_path: Path,
) -> None:
    warnings = (
        "GF 3.13 has not yet been certified.",
        "A compatibility profile was inferred.",
    )
    harness = _harness(tmp_path, compatibility_warnings=warnings)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert result.succeeded is True
    assert tuple(issue.message for issue in result.warnings) == warnings
    assert {issue.code for issue in result.warnings} == {"GF-WB-CONFIG-141"}
    assert result.require() is harness.configuration


def test_issue_collection_is_bounded_to_256_entries(tmp_path: Path) -> None:
    warnings = tuple(f"Compatibility warning {index}." for index in range(300))
    harness = _harness(tmp_path, compatibility_warnings=warnings)

    result = preflight_run(
        harness.configuration,
        filesystem=harness.filesystem,
    )

    assert len(result.issues) == 256
    assert all(issue.code == "GF-WB-CONFIG-141" for issue in result.issues)


def test_require_preflight_raises_first_structured_error(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    project_root = _project_of(harness.configuration).project_root
    project_file = _project_of(harness.configuration).project_file
    harness.filesystem.directories.remove(project_root)
    harness.filesystem.files.remove(project_file)

    with pytest.raises(ConfigurationError) as captured:
        require_preflight(
            harness.configuration,
            filesystem=harness.filesystem,
        )

    error = captured.value
    assert error.code == "GF-WB-CONFIG-101"
    assert error.subject == "project.project_root"
    assert "GF-WB-CONFIG-101" in error.detail
    assert "GF-WB-CONFIG-103" in error.detail
