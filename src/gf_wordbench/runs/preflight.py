"""Read-only run preflight validation for GF Wordbench."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.config.models import IssueSeverity, RunConfig
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    lexically_contains,
    normalize_environment_path,
    require_lexical_containment,
)
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.paths import (
    ProjectPaths,
    resolve_module_path,
    resolve_scenario_path,
)

__all__ = (
    "PreflightCheck",
    "PreflightFilesystem",
    "PreflightIssue",
    "PreflightResult",
    "preflight_run",
    "require_preflight",
)

_MAX_ISSUES: Final[int] = 256
_MAX_DETAIL_ISSUES: Final[int] = 32


@unique
class PreflightCheck(StrEnum):
    PROJECT_ROOT = "project_root"
    PROJECT_CONFIG = "project_config"
    SOURCE_ROOT = "source_root"
    ENVIRONMENT_PROJECT_ROOT = "environment_project_root"
    GF_EXECUTABLE = "gf_executable"
    RGL_ROOT = "rgl_root"
    OUTPUT_ROOT = "output_root"
    GF_PATH = "gf_path"
    MODE = "mode"
    TARGET = "target"
    CHECKPOINTS = "checkpoints"
    ENTRYPOINTS = "entrypoints"
    SCENARIOS = "scenarios"
    RELEASE_POLICY = "release_policy"
    COMPATIBILITY = "compatibility"


@runtime_checkable
class PreflightFilesystem(Protocol):
    def normalize(self, path: Path) -> Path:
        ...

    def resolve(self, path: Path) -> Path:
        ...

    def exists(self, path: Path) -> bool:
        ...

    def is_file(self, path: Path) -> bool:
        ...

    def is_directory(self, path: Path) -> bool:
        ...

    def is_readable(self, path: Path) -> bool:
        ...

    def is_executable(self, path: Path) -> bool:
        ...

    def is_writable_directory(self, path: Path) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    severity: IssueSeverity
    check: PreflightCheck
    field_path: str
    message: str
    remediation: str
    path: Path | None = None

    def __post_init__(self) -> None:
        _require_non_empty_text("code", self.code)
        if not self.code.startswith("GF-WB-CONFIG-"):
            raise ValueError(
                "code must use the GF-WB-CONFIG-<NNN> domain"
            )
        suffix = self.code.removeprefix("GF-WB-CONFIG-")
        if len(suffix) != 3 or not suffix.isdigit():
            raise ValueError(
                "code must use the GF-WB-CONFIG-<NNN> form"
            )
        if not isinstance(self.severity, IssueSeverity):
            raise TypeError("severity must be an IssueSeverity")
        if not isinstance(self.check, PreflightCheck):
            raise TypeError("check must be a PreflightCheck")
        _require_non_empty_text("field_path", self.field_path)
        _require_non_empty_text("message", self.message)
        _require_non_empty_text("remediation", self.remediation)
        if self.path is not None:
            object.__setattr__(
                self,
                "path",
                normalize_environment_path(
                    self.path,
                    role=f"{self.field_path} preflight path",
                ),
            )


@dataclass(frozen=True, slots=True)
class PreflightResult:
    configuration: RunConfig
    issues: tuple[PreflightIssue, ...] = ()
    checked_paths: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, RunConfig):
            raise TypeError(
                "configuration must be a RunConfig"
            )
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")
        if len(self.issues) > _MAX_ISSUES:
            raise ValueError(
                f"issues must contain at most {_MAX_ISSUES} entries"
            )
        if any(
            not isinstance(issue, PreflightIssue)
            for issue in self.issues
        ):
            raise TypeError(
                "issues must contain PreflightIssue values"
            )
        if not isinstance(self.checked_paths, tuple):
            raise TypeError("checked_paths must be a tuple")

        normalized_paths = tuple(
            normalize_environment_path(
                path,
                role=f"checked_paths[{index}]",
            )
            for index, path in enumerate(self.checked_paths)
        )
        if len(
            {
                os.path.normcase(os.path.normpath(os.fspath(path)))
                for path in normalized_paths
            }
        ) != len(normalized_paths):
            raise ValueError(
                "checked_paths must not contain duplicate paths"
            )
        object.__setattr__(
            self,
            "checked_paths",
            normalized_paths,
        )

    @property
    def succeeded(self) -> bool:
        return not any(
            issue.severity is IssueSeverity.ERROR
            for issue in self.issues
        )

    @property
    def errors(self) -> tuple[PreflightIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is IssueSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[PreflightIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is IssueSeverity.WARNING
        )

    @property
    def information(self) -> tuple[PreflightIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is IssueSeverity.INFO
        )

    def require(self) -> RunConfig:
        if self.succeeded:
            return self.configuration

        errors = self.errors
        detail_issues = errors[:_MAX_DETAIL_ISSUES]
        detail = "\n".join(
            (
                f"{issue.code} {issue.field_path}: "
                f"{issue.message} "
                f"Remediation: {issue.remediation}"
            )
            for issue in detail_issues
        )
        omitted = len(errors) - len(detail_issues)
        if omitted:
            detail = (
                f"{detail}\n"
                f"{omitted} additional preflight error(s) omitted."
            )

        first = errors[0]
        raise ConfigurationError(
            "Run preflight failed.",
            code=first.code,
            detail=detail,
            stage="preflight",
            operation="validate_run",
            subject=first.field_path,
        )


class _LocalPreflightFilesystem:
    __slots__ = ()

    def normalize(self, path: Path) -> Path:
        return normalize_environment_path(
            path,
            role="preflight path",
        )

    def resolve(self, path: Path) -> Path:
        normalized = self.normalize(path)
        return normalized.resolve(strict=False)

    def exists(self, path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False

    def is_file(self, path: Path) -> bool:
        try:
            return path.is_file()
        except OSError:
            return False

    def is_directory(self, path: Path) -> bool:
        try:
            return path.is_dir()
        except OSError:
            return False

    def is_readable(self, path: Path) -> bool:
        try:
            return os.access(path, os.R_OK)
        except OSError:
            return False

    def is_executable(self, path: Path) -> bool:
        try:
            if os.name == "nt":
                return path.is_file() and os.access(path, os.R_OK)
            return path.is_file() and os.access(path, os.X_OK)
        except OSError:
            return False

    def is_writable_directory(self, path: Path) -> bool:
        try:
            return path.is_dir() and os.access(
                path,
                os.W_OK | os.X_OK,
            )
        except OSError:
            return False


_LOCAL_FILESYSTEM: Final[PreflightFilesystem] = (
    _LocalPreflightFilesystem()
)


class _IssueCollector:
    __slots__ = ("_issues",)

    def __init__(self) -> None:
        self._issues: list[PreflightIssue] = []

    def add(
        self,
        *,
        code: str,
        severity: IssueSeverity,
        check: PreflightCheck,
        field_path: str,
        message: str,
        remediation: str,
        path: Path | None = None,
    ) -> None:
        if len(self._issues) >= _MAX_ISSUES:
            return
        self._issues.append(
            PreflightIssue(
                code=code,
                severity=severity,
                check=check,
                field_path=field_path,
                message=message,
                remediation=remediation,
                path=path,
            )
        )

    def error(
        self,
        *,
        code: str,
        check: PreflightCheck,
        field_path: str,
        message: str,
        remediation: str,
        path: Path | None = None,
    ) -> None:
        self.add(
            code=code,
            severity=IssueSeverity.ERROR,
            check=check,
            field_path=field_path,
            message=message,
            remediation=remediation,
            path=path,
        )

    def warning(
        self,
        *,
        code: str,
        check: PreflightCheck,
        field_path: str,
        message: str,
        remediation: str,
        path: Path | None = None,
    ) -> None:
        self.add(
            code=code,
            severity=IssueSeverity.WARNING,
            check=check,
            field_path=field_path,
            message=message,
            remediation=remediation,
            path=path,
        )

    def freeze(self) -> tuple[PreflightIssue, ...]:
        return tuple(self._issues)


def preflight_run(
    configuration: RunConfig,
    *,
    filesystem: PreflightFilesystem | None = None,
) -> PreflightResult:
    if not isinstance(configuration, RunConfig):
        raise TypeError(
            "configuration must be a RunConfig"
        )

    fs = filesystem or _LOCAL_FILESYSTEM
    if not isinstance(fs, PreflightFilesystem):
        raise TypeError(
            "filesystem must satisfy PreflightFilesystem"
        )

    issues = _IssueCollector()
    checked_paths: list[Path] = []

    project = configuration.validation_profile
    environment = configuration.environment
    project_paths: ProjectPaths | None = None
    project_root: Path | None = None

    if project is not None:
        project_paths = ProjectPaths.from_root(project.project_root)
        project_root = _check_directory(
            fs,
            issues,
            check=PreflightCheck.PROJECT_ROOT,
            field_path="project.project_root",
            path=project.project_root,
            checked_paths=checked_paths,
            missing_code="GF-WB-CONFIG-101",
            type_code="GF-WB-CONFIG-102",
            readable=True,
        )
        _check_project_config(
            fs,
            issues,
            project_file=project.project_file,
            project_root=project_root,
            checked_paths=checked_paths,
        )

    source_field = (
        "project.source_root"
        if project is not None
        else "language_context.language_directory"
    )
    source_root = _check_directory(
        fs,
        issues,
        check=PreflightCheck.SOURCE_ROOT,
        field_path=source_field,
        path=configuration.source_root,
        checked_paths=checked_paths,
        missing_code="GF-WB-CONFIG-105",
        type_code="GF-WB-CONFIG-106",
        readable=True,
    )

    if (
        project is not None
        and project_root is not None
        and source_root is not None
    ):
        _check_containment(
            issues,
            check=PreflightCheck.SOURCE_ROOT,
            field_path="project.source_root",
            root=project_root,
            candidate=source_root,
            code="GF-WB-CONFIG-107",
            remediation=(
                "Set sources.directory to a portable path "
                "inside the validation-profile root."
            ),
        )

    if project is not None:
        compatibility_root = environment.project_root
        profile_root = environment.validation_profile_root
        if compatibility_root is not None:
            normalized_compatibility_root = _normalized_checked_path(
                fs,
                compatibility_root,
                checked_paths,
            )
            if (
                project_root is not None
                and normalized_compatibility_root != project_root
            ):
                issues.error(
                    code="GF-WB-CONFIG-108",
                    check=PreflightCheck.ENVIRONMENT_PROJECT_ROOT,
                    field_path="environment.project_root",
                    message=(
                        "The compatibility project root does not match the "
                        "loaded validation-profile root."
                    ),
                    remediation=(
                        "Resolve one explicit validation profile and rebuild "
                        "RunConfig before starting the run."
                    ),
                    path=normalized_compatibility_root,
                )
        if profile_root is None:
            issues.error(
                code="GF-WB-CONFIG-108",
                check=PreflightCheck.ENVIRONMENT_PROJECT_ROOT,
                field_path="environment.validation_profile_root",
                message=(
                    "The resolved environment does not identify the "
                    "loaded validation-profile root."
                ),
                remediation=(
                    "Resolve the explicit validation profile and rebuild "
                    "RunConfig before starting the run."
                ),
            )
        else:
            normalized_profile_root = _normalized_checked_path(
                fs,
                profile_root,
                checked_paths,
            )
            if (
                project_root is not None
                and normalized_profile_root != project_root
            ):
                issues.error(
                    code="GF-WB-CONFIG-108",
                    check=PreflightCheck.ENVIRONMENT_PROJECT_ROOT,
                    field_path="environment.validation_profile_root",
                    message=(
                        "The resolved environment validation-profile root "
                        "does not match the loaded profile root."
                    ),
                    remediation=(
                        "Resolve one explicit validation profile and rebuild "
                        "RunConfig before starting the run."
                    ),
                    path=normalized_profile_root,
                )

    _check_gf_executable(
        fs,
        issues,
        environment.gf_executable,
        checked_paths,
    )

    _check_directory(
        fs,
        issues,
        check=PreflightCheck.RGL_ROOT,
        field_path="environment.rgl_root",
        path=environment.rgl_root,
        checked_paths=checked_paths,
        missing_code="GF-WB-CONFIG-112",
        type_code="GF-WB-CONFIG-113",
        readable=True,
    )

    output_root = _check_directory(
        fs,
        issues,
        check=PreflightCheck.OUTPUT_ROOT,
        field_path="environment.output_root",
        path=environment.output_root,
        checked_paths=checked_paths,
        missing_code="GF-WB-CONFIG-114",
        type_code="GF-WB-CONFIG-115",
        readable=False,
    )
    if output_root is not None:
        if not fs.is_writable_directory(output_root):
            issues.error(
                code="GF-WB-CONFIG-116",
                check=PreflightCheck.OUTPUT_ROOT,
                field_path="environment.output_root",
                message=(
                    "The output root is not writable for run "
                    "directory allocation."
                ),
                remediation=(
                    "Choose an existing writable output directory "
                    "outside language sources and validation assets."
                ),
                path=output_root,
            )
        if source_root is not None:
            _check_output_root_safety(
                fs,
                issues,
                output_root=output_root,
                source_root=source_root,
                project_paths=project_paths,
            )

    _check_gf_path(
        fs,
        issues,
        configuration,
        checked_paths,
    )
    _check_mode_policy(issues, configuration)
    _check_target(
        fs,
        issues,
        configuration,
        checked_paths,
    )
    _check_modules(
        fs,
        issues,
        configuration,
        source_root=source_root,
        checked_paths=checked_paths,
    )
    _check_scenarios(
        fs,
        issues,
        configuration,
        project_paths=project_paths,
        checked_paths=checked_paths,
    )
    _check_release_policy(issues, configuration)
    _copy_compatibility_warnings(issues, configuration)

    return PreflightResult(
        configuration=configuration,
        issues=issues.freeze(),
        checked_paths=_deduplicate_paths(checked_paths),
    )


def require_preflight(
    configuration: RunConfig,
    *,
    filesystem: PreflightFilesystem | None = None,
) -> RunConfig:
    return preflight_run(
        configuration,
        filesystem=filesystem,
    ).require()


def _check_project_config(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    *,
    project_file: Path,
    project_root: Path | None,
    checked_paths: list[Path],
) -> None:
    normalized = _normalized_checked_path(
        fs,
        project_file,
        checked_paths,
    )
    if not fs.exists(normalized):
        issues.error(
            code="GF-WB-CONFIG-103",
            check=PreflightCheck.PROJECT_CONFIG,
            field_path="project.project_file",
            message=(
                "The authoritative active-project configuration "
                "does not exist."
            ),
            remediation=(
                "Restore project/project.toml or select the "
                "correct GF Wordbench workspace."
            ),
            path=normalized,
        )
        return
    if not fs.is_file(normalized) or not fs.is_readable(normalized):
        issues.error(
            code="GF-WB-CONFIG-104",
            check=PreflightCheck.PROJECT_CONFIG,
            field_path="project.project_file",
            message=(
                "The authoritative project configuration is not "
                "a readable regular file."
            ),
            remediation=(
                "Provide a readable project.toml file and correct "
                "filesystem permissions."
            ),
            path=normalized,
        )
    if project_root is not None:
        _check_containment(
            issues,
            check=PreflightCheck.PROJECT_CONFIG,
            field_path="project.project_file",
            root=project_root,
            candidate=normalized,
            code="GF-WB-CONFIG-109",
            remediation=(
                "Use the canonical project.toml located directly "
                "under the active project root."
            ),
        )


def _check_gf_executable(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    path: Path,
    checked_paths: list[Path],
) -> None:
    normalized = _normalized_checked_path(
        fs,
        path,
        checked_paths,
    )
    if not fs.exists(normalized):
        issues.error(
            code="GF-WB-CONFIG-110",
            check=PreflightCheck.GF_EXECUTABLE,
            field_path="environment.gf_executable",
            message="The resolved GF executable does not exist.",
            remediation=(
                "Select the installed gf or gf.exe executable "
                "and rebuild the resolved environment."
            ),
            path=normalized,
        )
        return
    if not fs.is_file(normalized) or not fs.is_executable(normalized):
        issues.error(
            code="GF-WB-CONFIG-111",
            check=PreflightCheck.GF_EXECUTABLE,
            field_path="environment.gf_executable",
            message=(
                "The resolved GF executable is not an executable "
                "regular file."
            ),
            remediation=(
                "Select a readable executable file and correct "
                "its execute permissions where applicable."
            ),
            path=normalized,
        )


def _check_gf_path(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    configuration: RunConfig,
    checked_paths: list[Path],
) -> None:
    if not configuration.environment.gf_path:
        issues.error(
            code="GF-WB-CONFIG-117",
            check=PreflightCheck.GF_PATH,
            field_path="environment.gf_path",
            message="The effective GF search path is empty.",
            remediation=(
                "Resolve the language directory, required GF path parts, "
                "and RGL paths in deterministic order."
            ),
        )
        return

    for index, path in enumerate(
        configuration.environment.gf_path
    ):
        _check_directory(
            fs,
            issues,
            check=PreflightCheck.GF_PATH,
            field_path=f"environment.gf_path[{index}]",
            path=path,
            checked_paths=checked_paths,
            missing_code="GF-WB-CONFIG-118",
            type_code="GF-WB-CONFIG-119",
            readable=True,
        )


def _check_mode_policy(
    issues: _IssueCollector,
    configuration: RunConfig,
) -> None:
    project = configuration.validation_profile

    if (
        configuration.mode is ValidationMode.QUICK
        and configuration.target is None
    ):
        issues.error(
            code="GF-WB-CONFIG-120",
            check=PreflightCheck.MODE,
            field_path="mode",
            message="Quick mode has no bounded target.",
            remediation=(
                "Select one file, module, entrypoint, checkpoint, "
                "scenario, or another documented bounded target."
            ),
        )

    if configuration.mode is ValidationMode.CHECKPOINT:
        if project is None:
            issues.error(
                code="GF-WB-CONFIG-121",
                check=PreflightCheck.MODE,
                field_path="project",
                message=(
                    "Checkpoint mode requires an explicit compatible "
                    "validation profile."
                ),
                remediation=(
                    "Select a validation profile that declares checkpoint "
                    "modules for the resolved language."
                ),
            )
        elif not configuration.selected_checkpoints:
            issues.error(
                code="GF-WB-CONFIG-121",
                check=PreflightCheck.MODE,
                field_path="selected_checkpoints",
                message="Checkpoint mode selected no checkpoint modules.",
                remediation=(
                    "Resolve at least one configured checkpoint in "
                    "validation-profile order."
                ),
            )

    if configuration.mode is ValidationMode.RELEASE:
        if project is None:
            issues.error(
                code="GF-WB-CONFIG-122",
                check=PreflightCheck.MODE,
                field_path="project",
                message=(
                    "Release mode requires an explicit compatible "
                    "validation profile."
                ),
                remediation=(
                    "Select a validation profile that declares release "
                    "entrypoints, scenarios, and release policy."
                ),
            )
        elif not configuration.selected_entrypoints:
            issues.error(
                code="GF-WB-CONFIG-122",
                check=PreflightCheck.MODE,
                field_path="selected_entrypoints",
                message="Release mode selected no entrypoint modules.",
                remediation=(
                    "Resolve every required release entrypoint before "
                    "starting the run."
                ),
            )


def _check_target(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    configuration: RunConfig,
    checked_paths: list[Path],
) -> None:
    target = configuration.target
    if target is None:
        return

    project = configuration.validation_profile

    if target.kind is TargetKind.PROJECT:
        expected_identity = (
            str(project.project_id)
            if project is not None
            else configuration.language_key
        )
        if (
            target.value is not None
            and target.value != expected_identity
        ):
            issues.error(
                code="GF-WB-CONFIG-123",
                check=PreflightCheck.TARGET,
                field_path="target.value",
                message=(
                    "The broad target does not match the active language "
                    "or validation-profile identity."
                ),
                remediation=(
                    "Use the resolved language key, the compatible profile "
                    "ID, or omit the value for a language-wide target."
                ),
            )
        return

    if target.kind is TargetKind.SCENARIO:
        if project is None:
            issues.error(
                code="GF-WB-CONFIG-124",
                check=PreflightCheck.TARGET,
                field_path="target.value",
                message=(
                    "Scenario targets require an explicit compatible "
                    "validation profile."
                ),
                remediation=(
                    "Select a validation profile that declares the requested "
                    "scenario before starting the run."
                ),
            )
        elif target.value not in {
            str(value)
            for value in project.validation.all_scenarios
        }:
            issues.error(
                code="GF-WB-CONFIG-124",
                check=PreflightCheck.TARGET,
                field_path="target.value",
                message=(
                    "The scenario target is not declared by the "
                    "validation profile."
                ),
                remediation=(
                    "Select a scenario ID declared in project.toml."
                ),
            )
        return

    if target.kind is TargetKind.REGRESSION:
        return

    if target.value is None:
        issues.error(
            code="GF-WB-CONFIG-125",
            check=PreflightCheck.TARGET,
            field_path="target.value",
            message="The selected target has no identity.",
            remediation="Provide a stable target identity.",
        )
        return

    target_path = _resolve_target_path(
        configuration,
        target.kind,
        target.value,
    )
    if target_path is None:
        return

    normalized = _normalized_checked_path(
        fs,
        target_path,
        checked_paths,
    )
    if not fs.exists(normalized) or not fs.is_file(normalized):
        issues.error(
            code="GF-WB-CONFIG-126",
            check=PreflightCheck.TARGET,
            field_path="target.value",
            message=(
                "The selected file or module target does not "
                "identify an existing regular file."
            ),
            remediation=(
                "Select an existing GF source file owned by the "
                "resolved language."
            ),
            path=normalized,
        )
        return

    if normalized.suffix.casefold() != ".gf":
        issues.error(
            code="GF-WB-CONFIG-127",
            check=PreflightCheck.TARGET,
            field_path="target.value",
            message="A GF source target must end in .gf.",
            remediation="Select a canonical GF source file.",
            path=normalized,
        )

    _check_containment(
        issues,
        check=PreflightCheck.TARGET,
        field_path="target.value",
        root=configuration.source_root,
        candidate=normalized,
        code="GF-WB-CONFIG-128",
        remediation=(
            "Select a target contained by the resolved language directory."
        ),
    )


def _check_modules(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    configuration: RunConfig,
    *,
    source_root: Path | None,
    checked_paths: list[Path],
) -> None:
    if source_root is None:
        return

    project = configuration.validation_profile
    if project is None:
        declared_checkpoints: tuple[Path, ...] | None = None
        declared_entrypoints: tuple[Path, ...] | None = None
    else:
        declared_checkpoints = tuple(
            resolve_module_path(source_root, path)
            for path in project.modules.checkpoints
        )
        declared_entrypoints = tuple(
            resolve_module_path(source_root, path)
            for path in project.modules.entrypoints
        )

    _check_module_collection(
        fs,
        issues,
        check=PreflightCheck.CHECKPOINTS,
        field_path="selected_checkpoints",
        selected=configuration.selected_checkpoints,
        declared=declared_checkpoints,
        source_root=source_root,
        checked_paths=checked_paths,
        missing_code="GF-WB-CONFIG-129",
        undeclared_code="GF-WB-CONFIG-130",
    )
    _check_module_collection(
        fs,
        issues,
        check=PreflightCheck.ENTRYPOINTS,
        field_path="selected_entrypoints",
        selected=configuration.selected_entrypoints,
        declared=declared_entrypoints,
        source_root=source_root,
        checked_paths=checked_paths,
        missing_code="GF-WB-CONFIG-131",
        undeclared_code="GF-WB-CONFIG-132",
    )

    if (
        project is not None
        and configuration.mode is ValidationMode.RELEASE
    ):
        assert declared_entrypoints is not None
        selected_keys = {
            _path_key(path)
            for path in configuration.selected_entrypoints
        }
        for path in declared_entrypoints:
            if _path_key(path) not in selected_keys:
                issues.error(
                    code="GF-WB-CONFIG-133",
                    check=PreflightCheck.ENTRYPOINTS,
                    field_path="selected_entrypoints",
                    message=(
                        "Release mode omitted a configured "
                        "entrypoint."
                    ),
                    remediation=(
                        "Include every configured entrypoint in "
                        "validation-profile order."
                    ),
                    path=path,
                )


def _check_module_collection(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    *,
    check: PreflightCheck,
    field_path: str,
    selected: tuple[Path, ...],
    declared: tuple[Path, ...] | None,
    source_root: Path,
    checked_paths: list[Path],
    missing_code: str,
    undeclared_code: str,
) -> None:
    declared_keys = (
        {_path_key(path) for path in declared}
        if declared is not None
        else None
    )

    for index, path in enumerate(selected):
        normalized = _normalized_checked_path(
            fs,
            path,
            checked_paths,
        )
        item_field = f"{field_path}[{index}]"
        _check_containment(
            issues,
            check=check,
            field_path=item_field,
            root=source_root,
            candidate=normalized,
            code=undeclared_code,
            remediation=(
                "Select only GF modules inside the resolved language "
                "directory."
            ),
        )
        if normalized.suffix.casefold() != ".gf":
            issues.error(
                code=undeclared_code,
                check=check,
                field_path=item_field,
                message="The selected module path does not end in .gf.",
                remediation="Select a GF source module.",
                path=normalized,
            )
        if not fs.exists(normalized) or not fs.is_file(normalized):
            issues.error(
                code=missing_code,
                check=check,
                field_path=item_field,
                message=(
                    "The selected module does not identify an "
                    "existing regular file."
                ),
                remediation=(
                    "Restore the selected module or correct the resolved "
                    "run configuration."
                ),
                path=normalized,
            )
        if (
            declared_keys is not None
            and _path_key(normalized) not in declared_keys
        ):
            issues.error(
                code=undeclared_code,
                check=check,
                field_path=item_field,
                message=(
                    "The selected module is not declared in the "
                    "corresponding validation-profile registry."
                ),
                remediation=(
                    "Resolve module selections from the explicit compatible "
                    "validation profile without substitution."
                ),
                path=normalized,
            )


def _check_scenarios(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    configuration: RunConfig,
    *,
    project_paths: ProjectPaths | None,
    checked_paths: list[Path],
) -> None:
    project = configuration.validation_profile
    if project is None:
        for index, _scenario_id in enumerate(
            configuration.selected_scenarios
        ):
            issues.error(
                code="GF-WB-CONFIG-134",
                check=PreflightCheck.SCENARIOS,
                field_path=f"selected_scenarios[{index}]",
                message=(
                    "Scenario selection requires an explicit compatible "
                    "validation profile."
                ),
                remediation=(
                    "Select a validation profile that declares scenarios for "
                    "the resolved language."
                ),
            )
        return

    assert project_paths is not None
    declared = tuple(
        str(value)
        for value in project.validation.all_scenarios
    )
    declared_set = set(declared)
    selected_set = set(configuration.selected_scenarios)

    for index, scenario_id in enumerate(
        configuration.selected_scenarios
    ):
        field_path = f"selected_scenarios[{index}]"
        if scenario_id not in declared_set:
            issues.error(
                code="GF-WB-CONFIG-134",
                check=PreflightCheck.SCENARIOS,
                field_path=field_path,
                message=(
                    "The selected scenario is not declared by "
                    "the validation profile."
                ),
                remediation=(
                    "Select only scenario IDs declared in project.toml."
                ),
            )
            continue

        scenario_path = resolve_scenario_path(
            project_paths,
            scenario_id,
        )
        normalized = _normalized_checked_path(
            fs,
            scenario_path,
            checked_paths,
        )
        if not fs.exists(normalized) or not fs.is_file(normalized):
            issues.error(
                code="GF-WB-CONFIG-135",
                check=PreflightCheck.SCENARIOS,
                field_path=field_path,
                message=(
                    "The selected scenario file is missing or "
                    "is not a regular file."
                ),
                remediation=(
                    "Restore the canonical validation/scenarios/"
                    "<scenario-id>.gfs file."
                ),
                path=normalized,
            )
        elif not fs.is_readable(normalized):
            issues.error(
                code="GF-WB-CONFIG-136",
                check=PreflightCheck.SCENARIOS,
                field_path=field_path,
                message="The selected scenario file is not readable.",
                remediation=(
                    "Correct file permissions without changing "
                    "the scenario identity."
                ),
                path=normalized,
            )

    if configuration.mode is ValidationMode.RELEASE:
        for scenario_id in project.validation.required_scenarios:
            if str(scenario_id) not in selected_set:
                issues.error(
                    code="GF-WB-CONFIG-137",
                    check=PreflightCheck.SCENARIOS,
                    field_path="selected_scenarios",
                    message=(
                        "Release mode omitted a required validation-profile "
                        f"scenario: {scenario_id}."
                    ),
                    remediation=(
                        "Include every required scenario in "
                        "validation-profile order."
                    ),
                )


def _check_release_policy(
    issues: _IssueCollector,
    configuration: RunConfig,
) -> None:
    project = configuration.validation_profile

    if project is None:
        if (
            configuration.mode is ValidationMode.RELEASE
            or configuration.release_requires_pgf
        ):
            issues.error(
                code="GF-WB-CONFIG-138",
                check=PreflightCheck.RELEASE_POLICY,
                field_path="project",
                message=(
                    "Release policy requires an explicit compatible "
                    "validation profile."
                ),
                remediation=(
                    "Select a validation profile before enabling release "
                    "policy or release validation."
                ),
            )
    elif (
        configuration.release_requires_pgf
        != project.validation.release_requires_pgf
    ):
        issues.error(
            code="GF-WB-CONFIG-138",
            check=PreflightCheck.RELEASE_POLICY,
            field_path="release_requires_pgf",
            message=(
                "The resolved PGF release requirement differs "
                "from the authoritative validation-profile policy."
            ),
            remediation=(
                "Rebuild RunConfig without weakening or replacing "
                "validation-profile release policy."
            ),
        )

    if configuration.mode is not ValidationMode.RELEASE:
        return

    if configuration.skip_version_probe:
        issues.error(
            code="GF-WB-CONFIG-139",
            check=PreflightCheck.RELEASE_POLICY,
            field_path="skip_version_probe",
            message="Release mode cannot skip the GF version probe.",
            remediation=(
                "Enable the version probe and apply the documented "
                "compatibility policy."
            ),
        )

    if configuration.no_compile:
        issues.error(
            code="GF-WB-CONFIG-140",
            check=PreflightCheck.RELEASE_POLICY,
            field_path="no_compile",
            message=(
                "Release mode cannot omit required compilation."
            ),
            remediation=(
                "Enable compilation for release validation."
            ),
        )


def _copy_compatibility_warnings(
    issues: _IssueCollector,
    configuration: RunConfig,
) -> None:
    for index, warning in enumerate(
        configuration.compatibility_warnings
    ):
        issues.warning(
            code="GF-WB-CONFIG-141",
            check=PreflightCheck.COMPATIBILITY,
            field_path=f"compatibility_warnings[{index}]",
            message=warning,
            remediation=(
                "Review the compatibility warning before relying "
                "on the resulting evidence."
            ),
        )


def _check_directory(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    *,
    check: PreflightCheck,
    field_path: str,
    path: Path,
    checked_paths: list[Path],
    missing_code: str,
    type_code: str,
    readable: bool,
) -> Path | None:
    normalized = _normalized_checked_path(
        fs,
        path,
        checked_paths,
    )
    if not fs.exists(normalized):
        issues.error(
            code=missing_code,
            check=check,
            field_path=field_path,
            message="The required directory does not exist.",
            remediation=(
                "Provide the documented directory and rebuild "
                "the resolved configuration."
            ),
            path=normalized,
        )
        return None
    if not fs.is_directory(normalized):
        issues.error(
            code=type_code,
            check=check,
            field_path=field_path,
            message="The required path is not a directory.",
            remediation="Select a canonical directory path.",
            path=normalized,
        )
        return None
    if readable and not fs.is_readable(normalized):
        issues.error(
            code=type_code,
            check=check,
            field_path=field_path,
            message="The required directory is not readable.",
            remediation="Correct directory permissions.",
            path=normalized,
        )
        return None
    return normalized


def _check_output_root_safety(
    fs: PreflightFilesystem,
    issues: _IssueCollector,
    *,
    output_root: Path,
    source_root: Path,
    project_paths: ProjectPaths | None,
) -> None:
    prohibited: list[tuple[str, Path]] = [
        ("language source root", source_root),
    ]
    if project_paths is not None:
        prohibited.extend(
            (
                ("validation-profile root", project_paths.root),
                (
                    "validation-profile validation directory",
                    project_paths.validation_dir,
                ),
                (
                    "validation-profile scenario directory",
                    project_paths.scenarios_dir,
                ),
                (
                    "validation-profile input directory",
                    project_paths.inputs_dir,
                ),
                (
                    "validation-profile gold directory",
                    project_paths.gold_dir,
                ),
            )
        )

    output_real = fs.resolve(output_root)
    for label, path in prohibited:
        protected = fs.resolve(path)
        if _paths_overlap(output_real, protected):
            issues.error(
                code="GF-WB-CONFIG-142",
                check=PreflightCheck.OUTPUT_ROOT,
                field_path="environment.output_root",
                message=(
                    "The output root overlaps a protected path: "
                    f"{label}."
                ),
                remediation=(
                    "Choose a dedicated machine-local output root outside "
                    "language sources and validation-profile assets."
                ),
                path=output_root,
            )
            return


def _check_containment(
    issues: _IssueCollector,
    *,
    check: PreflightCheck,
    field_path: str,
    root: Path,
    candidate: Path,
    code: str,
    remediation: str,
) -> None:
    if not lexically_contains(
        root,
        candidate,
        mode=ContainmentMode.INSIDE_OR_EQUAL,
    ):
        issues.error(
            code=code,
            check=check,
            field_path=field_path,
            message=(
                "The resolved path escapes its approved ownership root."
            ),
            remediation=remediation,
            path=candidate,
        )


def _resolve_target_path(
    configuration: RunConfig,
    kind: TargetKind,
    value: str,
) -> Path | None:
    raw = Path(value)
    if raw.is_absolute():
        return normalize_environment_path(
            raw,
            role="validation target",
        )

    if kind in {
        TargetKind.FILE,
        TargetKind.MODULE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }:
        if (
            kind is not TargetKind.FILE
            and raw.suffix.casefold() != ".gf"
        ):
            return None
        return require_lexical_containment(
            configuration.source_root,
            configuration.source_root / raw,
            role="validation target",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )

    return None


def _normalized_checked_path(
    fs: PreflightFilesystem,
    path: Path,
    checked_paths: list[Path],
) -> Path:
    normalized = fs.normalize(path)
    checked_paths.append(normalized)
    return normalized


def _deduplicate_paths(
    paths: Iterable[Path],
) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = _path_key(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return tuple(result)


def _path_key(path: Path) -> str:
    return os.path.normcase(
        os.path.normpath(os.fspath(path))
    )


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        common = Path(os.path.commonpath((left, right)))
    except ValueError:
        return False
    return common == left or common == right


def _require_non_empty_text(
    field: str,
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value
