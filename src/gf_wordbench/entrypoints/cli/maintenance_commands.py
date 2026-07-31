"""Typed CLI adapters for explicit GF Wordbench maintenance use cases."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from typing import (
    TYPE_CHECKING,
    Final,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

from gf_wordbench.kernel.errors import (
    ConfigurationError,
    ContractViolationError,
    SchemaValidationError,
)
from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.statuses import OverallStatus

if TYPE_CHECKING:
    from gf_wordbench.projects.initializer import (
        ProjectInitializationRequest,
        ProjectInitializationResult,
    )
    from gf_wordbench.projects.migrator import (
        ProjectMigrationPlan,
        ProjectMigrationRequest,
        ProjectMigrationResult,
    )
    from gf_wordbench.projects.resetter import (
        ResetPlan,
        ResetRequest,
        ResetResult,
    )

from gf_wordbench.state.repository import StateRepository

from .parser import CliCommand, CliRequest


@unique
class MaintenanceCommandKind(StrEnum):
    INITIALIZE_PROJECT = "initialize-project"
    PLAN_PROJECT_RESET = "plan-project-reset"
    APPLY_PROJECT_RESET = "apply-project-reset"
    PLAN_PROJECT_MIGRATION = "plan-project-migration"
    APPLY_PROJECT_MIGRATION = "apply-project-migration"
    RESET_APPLICATION_STATE = "reset-application-state"


@dataclass(frozen=True, slots=True)
class InitializeProjectCommand:
    request: ProjectInitializationRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, _project_initialization_request_type()):
            raise TypeError(
                "request must be ProjectInitializationRequest"
            )

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.INITIALIZE_PROJECT


@dataclass(frozen=True, slots=True)
class PlanProjectResetCommand:
    request: ResetRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, _reset_request_type()):
            raise TypeError("request must be ResetRequest")

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.PLAN_PROJECT_RESET


@dataclass(frozen=True, slots=True)
class ApplyProjectResetCommand:
    request: ResetRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, _reset_request_type()):
            raise TypeError("request must be ResetRequest")

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.APPLY_PROJECT_RESET


@dataclass(frozen=True, slots=True)
class PlanProjectMigrationCommand:
    request: ProjectMigrationRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, _project_migration_request_type()):
            raise TypeError(
                "request must be ProjectMigrationRequest"
            )

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.PLAN_PROJECT_MIGRATION


@dataclass(frozen=True, slots=True)
class ApplyProjectMigrationCommand:
    request: ProjectMigrationRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, _project_migration_request_type()):
            raise TypeError(
                "request must be ProjectMigrationRequest"
            )

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.APPLY_PROJECT_MIGRATION


@dataclass(frozen=True, slots=True)
class ResetApplicationStateCommand:
    workspace_root: Path
    state_path: Path | None = None
    replace_with_defaults: bool = False

    def __post_init__(self) -> None:
        workspace_root = _absolute_path(
            self.workspace_root,
            field="workspace_root",
        )
        state_path = self.state_path
        if state_path is not None:
            state_path = _absolute_path(
                state_path,
                field="state_path",
            )
        if type(self.replace_with_defaults) is not bool:
            raise TypeError("replace_with_defaults must be bool")
        object.__setattr__(self, "workspace_root", workspace_root)
        object.__setattr__(self, "state_path", state_path)

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.RESET_APPLICATION_STATE


@dataclass(frozen=True, slots=True)
class StateResetResult:
    state_path: Path
    existed: bool
    replaced_with_defaults: bool

    def __post_init__(self) -> None:
        state_path = _absolute_path(
            self.state_path,
            field="state_path",
        )
        if type(self.existed) is not bool:
            raise TypeError("existed must be bool")
        if type(self.replaced_with_defaults) is not bool:
            raise TypeError("replaced_with_defaults must be bool")
        object.__setattr__(self, "state_path", state_path)

    @property
    def changed(self) -> bool:
        return self.existed or self.replaced_with_defaults



@dataclass(frozen=True, slots=True)
class MaintenanceCheckIssue:
    """One bounded read-only checker failure."""

    path: Path
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be pathlib.Path")
        message = _bounded_text(
            self.message,
            field="message",
            max_length=2_000,
        )
        object.__setattr__(self, "path", self.path.resolve(strict=False))
        object.__setattr__(self, "message", message)


@dataclass(frozen=True, slots=True)
class MaintenanceCheckResult:
    """Structured CLI result for schema and report checks."""

    command: str
    overall_status: OverallStatus
    checked: int
    issues: tuple[MaintenanceCheckIssue, ...] = ()
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        command = _bounded_text(
            self.command,
            field="command",
            max_length=128,
        )
        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be OverallStatus")
        if type(self.checked) is not int or self.checked < 0:
            raise ValueError("checked must be a non-negative integer")

        issues = tuple(self.issues)
        if any(not isinstance(item, MaintenanceCheckIssue) for item in issues):
            raise TypeError(
                "issues must contain MaintenanceCheckIssue values"
            )

        details = tuple(
            _bounded_text(
                item,
                field="details item",
                max_length=2_000,
            )
            for item in self.details
        )

        if self.overall_status is OverallStatus.OK and issues:
            raise ValueError(
                "an OK maintenance result cannot contain issues"
            )

        object.__setattr__(self, "command", command)
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "details", details)

    @property
    def ok(self) -> bool:
        return self.overall_status is OverallStatus.OK


@dataclass(frozen=True, slots=True)
class GoldUpdateCommandRequest:
    """Interface-neutral reviewed gold-update application request."""

    scenario_ids: tuple[str, ...]
    all_scenarios: bool
    confirmed: bool
    strict: bool = False
    show_diff: bool = False
    scenario_timeout_seconds: int | None = None
    quiet: bool = False
    verbose: bool = False
    project_root: Path | None = None
    gf_executable: Path | None = None
    rgl_root: Path | None = None
    output_root: Path | None = None
    compatibility_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        scenario_ids = _scenario_id_tuple(
            self.scenario_ids,
            field="scenario_ids",
        )
        warnings = _text_tuple(
            self.compatibility_warnings,
            field="compatibility_warnings",
        )

        for field_name in (
            "all_scenarios",
            "confirmed",
            "strict",
            "show_diff",
            "quiet",
            "verbose",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be bool")

        if self.all_scenarios == bool(scenario_ids):
            raise ValueError(
                "gold update requires exactly one of scenario_ids "
                "or all_scenarios"
            )
        if self.quiet and self.verbose:
            raise ValueError("quiet and verbose cannot both be enabled")

        timeout = self.scenario_timeout_seconds
        if timeout is not None:
            if type(timeout) is not int:
                raise TypeError(
                    "scenario_timeout_seconds must be int or None"
                )
            if timeout <= 0:
                raise ValueError(
                    "scenario_timeout_seconds must be positive"
                )

        for field_name in (
            "project_root",
            "gf_executable",
            "rgl_root",
            "output_root",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, Path):
                raise TypeError(
                    f"{field_name} must be pathlib.Path or None"
                )
            if value is not None and "\x00" in str(value):
                raise ValueError(f"{field_name} must not contain NUL")

        object.__setattr__(self, "scenario_ids", scenario_ids)
        object.__setattr__(self, "compatibility_warnings", warnings)


@runtime_checkable
class GoldUpdateCliApplication(Protocol):
    """Application boundary composed by :mod:`gf_wordbench.bootstrap`."""

    def execute_gold_update(
        self,
        request: GoldUpdateCommandRequest,
    ) -> object:
        ...


GoldUpdateApplicationFactory: TypeAlias = Callable[
    [],
    GoldUpdateCliApplication,
]


MaintenanceCommand: TypeAlias = (
    InitializeProjectCommand
    | PlanProjectResetCommand
    | ApplyProjectResetCommand
    | PlanProjectMigrationCommand
    | ApplyProjectMigrationCommand
    | ResetApplicationStateCommand
)

_ResultT = TypeVar("_ResultT")

if TYPE_CHECKING:
    MaintenanceCommandResult: TypeAlias = (
        ProjectInitializationResult
        | ResetPlan
        | ResetResult
        | ProjectMigrationPlan
        | ProjectMigrationResult
        | StateResetResult
    )

    InitializeProjectService: TypeAlias = Callable[
        [ProjectInitializationRequest],
        ProjectInitializationResult,
    ]
    PlanProjectResetService: TypeAlias = Callable[
        [ResetRequest],
        ResetPlan,
    ]
    ApplyProjectResetService: TypeAlias = Callable[
        [ResetRequest],
        ResetResult,
    ]
    PlanProjectMigrationService: TypeAlias = Callable[
        [ProjectMigrationRequest],
        ProjectMigrationPlan,
    ]
    ApplyProjectMigrationService: TypeAlias = Callable[
        [ProjectMigrationRequest],
        ProjectMigrationResult,
    ]
else:
    MaintenanceCommandResult: TypeAlias = object
    InitializeProjectService: TypeAlias = Callable[[object], object]
    PlanProjectResetService: TypeAlias = Callable[[object], object]
    ApplyProjectResetService: TypeAlias = Callable[[object], object]
    PlanProjectMigrationService: TypeAlias = Callable[[object], object]
    ApplyProjectMigrationService: TypeAlias = Callable[[object], object]

ResetApplicationStateService: TypeAlias = Callable[
    [ResetApplicationStateCommand],
    StateResetResult,
]


@dataclass(frozen=True, slots=True)
class MaintenanceCommandServices:
    initialize_project: InitializeProjectService
    plan_project_reset: PlanProjectResetService
    apply_project_reset: ApplyProjectResetService
    plan_project_migration: PlanProjectMigrationService
    apply_project_migration: ApplyProjectMigrationService
    reset_application_state: ResetApplicationStateService

    def __post_init__(self) -> None:
        for field_name in (
            "initialize_project",
            "plan_project_reset",
            "apply_project_reset",
            "plan_project_migration",
            "apply_project_migration",
            "reset_application_state",
        ):
            if not callable(getattr(self, field_name)):
                raise TypeError(f"{field_name} must be callable")


_DEFAULT_STATE_RESET_SERVICE: Final[ResetApplicationStateService]


def reset_application_state(
    command: ResetApplicationStateCommand,
) -> StateResetResult:
    if not isinstance(command, ResetApplicationStateCommand):
        raise TypeError(
            "command must be ResetApplicationStateCommand"
        )

    repository = StateRepository(
        workspace_root=command.workspace_root,
        state_path=command.state_path,
    )
    state_path = repository.resolved_state_path
    existed = state_path.exists() or state_path.is_symlink()
    repository.reset(
        replace_with_defaults=command.replace_with_defaults,
    )
    return StateResetResult(
        state_path=state_path,
        existed=existed,
        replaced_with_defaults=command.replace_with_defaults,
    )


_DEFAULT_STATE_RESET_SERVICE = reset_application_state


def execute_maintenance_command(
    command: MaintenanceCommand,
    *,
    services: MaintenanceCommandServices,
) -> MaintenanceCommandResult:
    if not isinstance(services, MaintenanceCommandServices):
        raise TypeError(
            "services must be MaintenanceCommandServices"
        )

    if isinstance(command, InitializeProjectCommand):
        from gf_wordbench.projects.initializer import (
            ProjectInitializationResult,
        )

        result = services.initialize_project(command.request)
        return _require_result(
            result,
            ProjectInitializationResult,
            service="initialize_project",
        )

    if isinstance(command, PlanProjectResetCommand):
        from gf_wordbench.projects.resetter import ResetPlan

        result = services.plan_project_reset(command.request)
        return _require_result(
            result,
            ResetPlan,
            service="plan_project_reset",
        )

    if isinstance(command, ApplyProjectResetCommand):
        from gf_wordbench.projects.resetter import ResetResult

        result = services.apply_project_reset(command.request)
        return _require_result(
            result,
            ResetResult,
            service="apply_project_reset",
        )

    if isinstance(command, PlanProjectMigrationCommand):
        from gf_wordbench.projects.migrator import ProjectMigrationPlan

        result = services.plan_project_migration(command.request)
        return _require_result(
            result,
            ProjectMigrationPlan,
            service="plan_project_migration",
        )

    if isinstance(command, ApplyProjectMigrationCommand):
        from gf_wordbench.projects.migrator import (
            ProjectMigrationResult,
        )

        result = services.apply_project_migration(command.request)
        return _require_result(
            result,
            ProjectMigrationResult,
            service="apply_project_migration",
        )

    if isinstance(command, ResetApplicationStateCommand):
        result = services.reset_application_state(command)
        return _require_result(
            result,
            StateResetResult,
            service="reset_application_state",
        )

    raise TypeError(
        "command must be a supported maintenance command"
    )


def default_state_reset_service() -> ResetApplicationStateService:
    return _DEFAULT_STATE_RESET_SERVICE


def maintenance_command_kind(
    command: MaintenanceCommand,
) -> MaintenanceCommandKind:
    if isinstance(
        command,
        (
            InitializeProjectCommand,
            PlanProjectResetCommand,
            ApplyProjectResetCommand,
            PlanProjectMigrationCommand,
            ApplyProjectMigrationCommand,
            ResetApplicationStateCommand,
        ),
    ):
        return command.kind
    raise TypeError(
        "command must be a supported maintenance command"
    )


def maintenance_command_is_destructive(
    command: MaintenanceCommand,
) -> bool:
    kind = maintenance_command_kind(command)
    if kind in {
        MaintenanceCommandKind.PLAN_PROJECT_RESET,
        MaintenanceCommandKind.PLAN_PROJECT_MIGRATION,
    }:
        return False
    if isinstance(command, ApplyProjectResetCommand):
        return not command.request.dry_run
    if isinstance(command, ApplyProjectMigrationCommand):
        return not command.request.dry_run
    return True


def maintenance_command_is_dry_run(
    command: MaintenanceCommand,
) -> bool:
    if isinstance(command, PlanProjectResetCommand):
        return True
    if isinstance(command, PlanProjectMigrationCommand):
        return True
    if isinstance(command, ApplyProjectResetCommand):
        return command.request.dry_run
    if isinstance(command, ApplyProjectMigrationCommand):
        return command.request.dry_run
    return False




def execute_gold_update_command(
    request: CliRequest,
) -> object:
    """Translate one CLI request and invoke the bootstrap-composed service."""

    application = _build_gold_update_application()
    return execute_gold_update_with_application(
        gold_update_request_from_cli_request(request),
        application,
    )


def execute_gold_update_with_application(
    request: GoldUpdateCommandRequest,
    application: GoldUpdateCliApplication,
) -> object:
    """Execute a typed gold-update request through an injected application."""

    if not isinstance(request, GoldUpdateCommandRequest):
        raise TypeError(
            "request must be GoldUpdateCommandRequest"
        )
    if not isinstance(application, GoldUpdateCliApplication):
        raise TypeError(
            "application must satisfy GoldUpdateCliApplication"
        )

    result = application.execute_gold_update(request)
    overall_status = getattr(result, "overall_status", None)
    if not isinstance(overall_status, OverallStatus):
        raise TypeError(
            "gold update application must return a result exposing "
            "OverallStatus overall_status"
        )
    return result


def gold_update_request_from_cli_request(
    request: CliRequest,
) -> GoldUpdateCommandRequest:
    """Translate canonical parser values into an application request."""

    _require_cli_request(request, CliCommand.GOLD_UPDATE)

    return GoldUpdateCommandRequest(
        scenario_ids=_request_text_sequence(
            request,
            "scenarios",
            "scenario_ids",
        ),
        all_scenarios=_request_bool(request, "all_scenarios"),
        confirmed=_request_bool(request, "yes"),
        strict=_request_bool(request, "strict"),
        show_diff=_request_bool(request, "show_diff"),
        scenario_timeout_seconds=_optional_request_int(
            request,
            "scenario_timeout_seconds",
            "scenario_timeout_sec",
            "scenario_timeout",
        ),
        quiet=_request_bool(request, "quiet"),
        verbose=_request_bool(request, "verbose"),
        project_root=_optional_request_path(
            request,
            "project_root",
        ),
        gf_executable=_optional_request_path_any(
            request,
            "gf_executable",
            "gf_exe",
        ),
        rgl_root=_optional_request_path(
            request,
            "rgl_root",
        ),
        output_root=_optional_request_path_any(
            request,
            "output_root",
            "out_root",
        ),
        compatibility_warnings=tuple(
            request.compatibility_warnings
        ),
    )


def _build_gold_update_application() -> GoldUpdateCliApplication:
    """Resolve the gold-update service from the sole composition root."""

    try:
        from gf_wordbench.bootstrap import (
            build_gold_update_application,
        )
    except ImportError as exc:
        raise ConfigurationError(
            "gold update application builder is unavailable",
            code="GF-WB-CONFIG-901",
            stage="bootstrap",
            operation="compose-gold-update",
            subject="gold.update",
        ) from exc

    application = build_gold_update_application()
    if not isinstance(application, GoldUpdateCliApplication):
        raise TypeError(
            "build_gold_update_application() must return an object "
            "satisfying GoldUpdateCliApplication"
        )
    return application


def execute_schemas_check_command(
    request: CliRequest,
) -> MaintenanceCheckResult:
    """Validate persisted assets without rewriting them."""

    _require_cli_request(request, CliCommand.SCHEMAS_CHECK)
    strict = _request_bool(request, "strict")
    recursive = _request_bool(request, "recursive")
    project_root = _optional_request_path(request, "project_root")
    base = (
        project_root.resolve(strict=False)
        if project_root is not None
        else Path.cwd().resolve()
    )
    raw_paths = _request_path_sequence(request, "paths")

    targets = _expand_schema_targets(
        raw_paths,
        base=base,
        recursive=recursive,
    )
    issues: list[MaintenanceCheckIssue] = []
    details: list[str] = []

    for target in targets:
        try:
            kind = _validate_schema_asset(
                target,
                strict=strict,
            )
        except (
            ConfigurationError,
            ContractViolationError,
            ValueError,
            TypeError,
            UnicodeError,
        ) as exc:
            issues.append(
                MaintenanceCheckIssue(
                    path=target,
                    message=_exception_message(exc),
                )
            )
        except FileNotFoundError:
            issues.append(
                MaintenanceCheckIssue(
                    path=target,
                    message="file does not exist",
                )
            )
        else:
            details.append(f"{target}: {kind}")

    if issues:
        _raise_schema_check_failure(issues)

    return MaintenanceCheckResult(
        command=CliCommand.SCHEMAS_CHECK.value,
        overall_status=OverallStatus.OK,
        checked=len(targets),
        details=tuple(details),
    )


def execute_reports_check_command(
    request: CliRequest,
) -> MaintenanceCheckResult:
    """Verify one completed or partial run directory without modifying it."""

    _require_cli_request(request, CliCommand.REPORTS_CHECK)
    strict = _request_bool(request, "strict")
    verify_hashes = _request_bool(request, "verify_hashes") or strict
    run_dir = _required_request_path(request, "run_dir").resolve(
        strict=False
    )

    if not run_dir.exists():
        raise ContractViolationError(
            f"run directory does not exist: {run_dir}",
            code="GF-WB-REPORT-901",
            stage="reporting",
            operation="reports-check",
            subject=str(run_dir),
        )
    if not run_dir.is_dir():
        raise ContractViolationError(
            f"run directory is not a directory: {run_dir}",
            code="GF-WB-REPORT-902",
            stage="reporting",
            operation="reports-check",
            subject=str(run_dir),
        )

    issues: list[MaintenanceCheckIssue] = []
    details: list[str] = []
    summary_path = run_dir / "summary.json"

    try:
        summary_document = _read_json_document(summary_path)
        _validate_summary_document(
            summary_document,
            strict=True,
        )
    except (
        ConfigurationError,
        ContractViolationError,
        ValueError,
        TypeError,
        UnicodeError,
        FileNotFoundError,
    ) as exc:
        issues.append(
            MaintenanceCheckIssue(
                path=summary_path,
                message=_exception_message(exc),
            )
        )
        summary_document = None
    else:
        details.append(f"{summary_path}: run summary")

    if isinstance(summary_document, Mapping):
        _check_declared_report_artifacts(
            run_dir,
            summary_document,
            issues,
        )

    manifest_path = run_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = _read_and_validate_manifest(
                manifest_path,
                strict=strict,
            )
            _check_manifest_artifacts(
                run_dir,
                manifest,
                verify_hashes=verify_hashes,
                issues=issues,
            )
            _check_run_identity(
                summary_document,
                manifest,
                manifest_path=manifest_path,
                issues=issues,
            )
        except (
            ConfigurationError,
            ContractViolationError,
            ValueError,
            TypeError,
            UnicodeError,
        ) as exc:
            issues.append(
                MaintenanceCheckIssue(
                    path=manifest_path,
                    message=_exception_message(exc),
                )
            )
        else:
            details.append(f"{manifest_path}: artifact manifest")
    elif strict:
        issues.append(
            MaintenanceCheckIssue(
                path=manifest_path,
                message="strict report checking requires manifest.json",
            )
        )
    else:
        details.append(
            f"{manifest_path}: absent; hash verification skipped"
        )

    summary_md = run_dir / "summary.md"
    if summary_md.is_file():
        try:
            _validate_summary_markdown(summary_md)
        except (ValueError, UnicodeError) as exc:
            issues.append(
                MaintenanceCheckIssue(
                    path=summary_md,
                    message=_exception_message(exc),
                )
            )
        else:
            details.append(f"{summary_md}: Markdown summary")

    if issues:
        _raise_report_check_failure(run_dir, issues)

    return MaintenanceCheckResult(
        command=CliCommand.REPORTS_CHECK.value,
        overall_status=OverallStatus.OK,
        checked=1,
        details=tuple(details),
    )


def _require_cli_request(
    request: CliRequest,
    command: CliCommand,
) -> None:
    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")
    if request.command is not command:
        raise ValueError(
            f"request command must be {command.value!r}"
        )


def _request_bool(
    request: CliRequest,
    name: str,
) -> bool:
    value = request.get(name, False)
    if type(value) is not bool:
        raise TypeError(f"CLI argument {name!r} must be bool")
    return value


def _optional_request_int(
    request: CliRequest,
    *names: str,
) -> int | None:
    value = _first_request_value(request, names)
    if value is None:
        return None
    if type(value) is not int:
        joined = ", ".join(repr(name) for name in names)
        raise TypeError(
            f"CLI argument {joined} must be int or None"
        )
    if value <= 0:
        joined = ", ".join(repr(name) for name in names)
        raise ValueError(
            f"CLI argument {joined} must be positive"
        )
    return value


def _request_text_sequence(
    request: CliRequest,
    *names: str,
) -> tuple[str, ...]:
    value = _first_request_value(request, names)
    if value is None:
        return ()
    if isinstance(value, str):
        raw = (value,)
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        raw = tuple(value)
    else:
        joined = ", ".join(repr(name) for name in names)
        raise TypeError(
            f"CLI argument {joined} must contain strings"
        )

    result: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, str):
            raise TypeError(
                f"CLI text sequence item {index} must be str"
            )
        result.append(item)
    return tuple(result)


def _optional_request_path_any(
    request: CliRequest,
    *names: str,
) -> Path | None:
    value = _first_request_value(request, names)
    if value is None:
        return None
    if not isinstance(value, Path):
        joined = ", ".join(repr(name) for name in names)
        raise TypeError(
            f"CLI argument {joined} must be pathlib.Path or None"
        )
    return value


def _first_request_value(
    request: CliRequest,
    names: Sequence[str],
) -> object:
    for name in names:
        if name in request.arguments:
            return request.arguments[name]
    return None


def _optional_request_path(
    request: CliRequest,
    name: str,
) -> Path | None:
    value = request.get(name)
    if value is None:
        return None
    if not isinstance(value, Path):
        raise TypeError(
            f"CLI argument {name!r} must be pathlib.Path or None"
        )
    return value


def _required_request_path(
    request: CliRequest,
    name: str,
) -> Path:
    value = request.require(name)
    if not isinstance(value, Path):
        raise TypeError(
            f"CLI argument {name!r} must be pathlib.Path"
        )
    return value


def _request_path_sequence(
    request: CliRequest,
    name: str,
) -> tuple[Path, ...]:
    value = request.require(name)
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes, bytearray),
    ):
        raise TypeError(
            f"CLI argument {name!r} must be a sequence of paths"
        )
    paths = tuple(value)
    if not paths:
        raise ValueError(
            f"CLI argument {name!r} must not be empty"
        )
    if any(not isinstance(item, Path) for item in paths):
        raise TypeError(
            f"CLI argument {name!r} must contain pathlib.Path values"
        )
    return paths


_SUPPORTED_SCHEMA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "project.toml",
        ".gf_wordbench_state.json",
        "summary.json",
        "manifest.json",
    }
)
_SUPPORTED_SCHEMA_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".gold", ".out"}
)
_SUMMARY_DIRECTORY_ARTIFACT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "details_dir",
        "raw_dir",
        "compile_logs_dir",
        "scan_logs_dir",
        "scenario_logs_dir",
        "artifacts_dir",
        "gfo_dir",
        "out_dir",
        "pgf_dir",
    }
)


def _expand_schema_targets(
    paths: tuple[Path, ...],
    *,
    base: Path,
    recursive: bool,
) -> tuple[Path, ...]:
    selected: dict[str, Path] = {}

    for raw in paths:
        target = (
            raw.resolve(strict=False)
            if raw.is_absolute()
            else (base / raw).resolve(strict=False)
        )

        if not target.exists():
            selected[str(target)] = target
            continue

        if target.is_file():
            selected[str(target)] = target
            continue

        if not target.is_dir():
            selected[str(target)] = target
            continue

        if recursive:
            for child in target.rglob("*"):
                if child.is_file() and _is_supported_schema_asset(child):
                    resolved = child.resolve(strict=False)
                    selected[str(resolved)] = resolved
            continue

        run_assets = tuple(
            target / name
            for name in ("summary.json", "manifest.json")
            if (target / name).is_file()
        )
        if run_assets:
            for child in run_assets:
                resolved = child.resolve(strict=False)
                selected[str(resolved)] = resolved
        else:
            selected[str(target)] = target

    return tuple(
        selected[key]
        for key in sorted(selected, key=str.casefold)
    )


def _is_supported_schema_asset(path: Path) -> bool:
    return (
        path.name in _SUPPORTED_SCHEMA_NAMES
        or path.suffix.lower() in _SUPPORTED_SCHEMA_SUFFIXES
    )


def _validate_schema_asset(
    path: Path,
    *,
    strict: bool,
) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise SchemaValidationError(
            "schema target must be a supported file or run directory",
            code="GF-WB-SCHEMA-901",
            stage="schema",
            operation="schemas-check",
            subject=str(path),
        )

    if path.name == "project.toml":
        from gf_wordbench.projects.schema import (
            ProjectSchemaCompatibility,
            validate_project_schema,
        )
        from gf_wordbench.projects.toml_adapter import (
            read_project_toml,
        )

        document = read_project_toml(path)
        validate_project_schema(
            document,
            source=path,
            compatibility=(
                ProjectSchemaCompatibility.STRICT
                if strict
                else ProjectSchemaCompatibility.FORWARD_MINOR
            ),
        )
        return "project schema"

    if path.name == ".gf_wordbench_state.json":
        from gf_wordbench.infrastructure.json_io import read_json
        from gf_wordbench.state.schema import parse_app_state

        document = read_json(path)
        parse_app_state(
            document,
            strict=strict,
            source=path,
        )
        return "application state schema"

    if path.name == "summary.json":
        document = _read_json_document(path)
        _validate_summary_document(
            document,
            strict=strict,
        )
        return "run summary schema"

    if path.name == "manifest.json":
        _read_and_validate_manifest(
            path,
            strict=strict,
        )
        return "artifact manifest schema"

    if path.suffix.lower() == ".gold":
        from gf_wordbench.validation.scenarios.gold_update import (
            parse_gold_document,
        )

        parse_gold_document(_read_utf8_text(path))
        return "scenario gold schema"

    if path.suffix.lower() == ".out":
        from gf_wordbench.validation.scenarios.gold_update import (
            NORMALIZATION_HEADER_PREFIX,
            SCENARIO_HEADER_PREFIX,
            parse_normalized_output_document,
        )

        text = _read_utf8_text(path)
        lines = text.splitlines()
        if len(lines) < 3:
            raise ValueError(
                "normalized output is missing canonical headers"
            )
        scenario_id = _header_value(
            lines[1],
            SCENARIO_HEADER_PREFIX,
        )
        normalization_version = _header_value(
            lines[2],
            NORMALIZATION_HEADER_PREFIX,
        )
        parse_normalized_output_document(
            text,
            expected_scenario_id=scenario_id,
            expected_normalization_version=normalization_version,
        )
        return "normalized scenario-output schema"

    raise SchemaValidationError(
        f"unsupported persisted asset: {path.name}",
        code="GF-WB-SCHEMA-902",
        stage="schema",
        operation="schemas-check",
        subject=str(path),
    )


def _read_json_document(path: Path) -> Mapping[str, object]:
    from gf_wordbench.infrastructure.json_io import read_json

    document = read_json(path)
    if not isinstance(document, Mapping):
        raise SchemaValidationError(
            "JSON root must be an object",
            code="GF-WB-SCHEMA-903",
            stage="schema",
            operation="read-json",
            subject=str(path),
        )
    return document


def _validate_summary_document(
    document: Mapping[str, object],
    *,
    strict: bool,
) -> None:
    from gf_wordbench.reporting.schemas.summary_v1 import (
        validate_summary_v1,
    )

    issues = validate_summary_v1(
        document,
        strict=strict,
        check_ordering=True,
    )
    if issues:
        rendered = "; ".join(
            f"{issue.path}: {issue.message}"
            for issue in issues[:20]
        )
        if len(issues) > 20:
            rendered += (
                f"; {len(issues) - 20} additional issue(s) omitted"
            )
        raise SchemaValidationError(
            "run summary schema is invalid",
            code="GF-WB-SCHEMA-904",
            detail=rendered,
            stage="reporting",
            operation="validate-summary",
        )


def _read_and_validate_manifest(
    path: Path,
    *,
    strict: bool,
) -> object:
    from gf_wordbench.reporting.schemas.manifest_v1 import (
        parse_manifest,
        validate_manifest,
    )

    manifest = parse_manifest(
        _read_json_document(path),
        strict=strict,
    )
    validate_manifest(manifest)
    return manifest


def _check_declared_report_artifacts(
    run_dir: Path,
    summary: Mapping[str, object],
    issues: list[MaintenanceCheckIssue],
) -> None:
    artifacts = summary.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return

    for field, value in artifacts.items():
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            issues.append(
                MaintenanceCheckIssue(
                    path=run_dir / "summary.json",
                    message=(
                        f"artifacts.{field} must be a non-empty "
                        "run-relative path or null"
                    ),
                )
            )
            continue

        try:
            candidate = _contained_artifact_path(
                run_dir,
                value,
            )
        except ValueError as exc:
            issues.append(
                MaintenanceCheckIssue(
                    path=run_dir / "summary.json",
                    message=(
                        f"artifacts.{field}: "
                        f"{_exception_message(exc)}"
                    ),
                )
            )
            continue

        expected_directory = (
            field in _SUMMARY_DIRECTORY_ARTIFACT_FIELDS
        )
        present = (
            candidate.is_dir()
            if expected_directory
            else candidate.is_file()
        )
        if not present:
            expected_kind = (
                "directory"
                if expected_directory
                else "file"
            )
            issues.append(
                MaintenanceCheckIssue(
                    path=candidate,
                    message=(
                        f"{expected_kind} declared by summary field "
                        f"{field!r} is missing"
                    ),
                )
            )


def _check_manifest_artifacts(
    run_dir: Path,
    manifest: object,
    *,
    verify_hashes: bool,
    issues: list[MaintenanceCheckIssue],
) -> None:
    artifacts = tuple(getattr(manifest, "artifacts", ()))
    for entry in artifacts:
        declared_path = getattr(entry, "path", None)
        required = getattr(entry, "required", None)
        size_bytes = getattr(entry, "size_bytes", None)
        expected_hash = getattr(entry, "sha256", None)

        if not isinstance(declared_path, str):
            raise TypeError(
                "manifest entry path must be a string"
            )
        if type(required) is not bool:
            raise TypeError(
                "manifest entry required must be bool"
            )
        if type(size_bytes) is not int or size_bytes < 0:
            raise TypeError(
                "manifest entry size_bytes must be a "
                "non-negative integer"
            )
        if not isinstance(expected_hash, str):
            raise TypeError(
                "manifest entry sha256 must be a string"
            )

        try:
            candidate = _contained_artifact_path(
                run_dir,
                declared_path,
            )
        except ValueError as exc:
            issues.append(
                MaintenanceCheckIssue(
                    path=run_dir / declared_path,
                    message=_exception_message(exc),
                )
            )
            continue

        if not candidate.is_file():
            if required:
                issues.append(
                    MaintenanceCheckIssue(
                        path=candidate,
                        message="required manifest artifact is missing",
                    )
                )
            continue

        observed_size = candidate.stat().st_size
        if observed_size != size_bytes:
            issues.append(
                MaintenanceCheckIssue(
                    path=candidate,
                    message=(
                        f"size mismatch: expected {size_bytes}, "
                        f"observed {observed_size}"
                    ),
                )
            )

        if verify_hashes:
            observed_hash = _sha256_file(candidate)
            if observed_hash != expected_hash.lower():
                issues.append(
                    MaintenanceCheckIssue(
                        path=candidate,
                        message=(
                            f"SHA-256 mismatch: expected "
                            f"{expected_hash.lower()}, "
                            f"observed {observed_hash}"
                        ),
                    )
                )


def _check_run_identity(
    summary: Mapping[str, object] | None,
    manifest: object,
    *,
    manifest_path: Path,
    issues: list[MaintenanceCheckIssue],
) -> None:
    if not isinstance(summary, Mapping):
        return
    metadata = summary.get("metadata")
    if not isinstance(metadata, Mapping):
        return

    summary_run_id = metadata.get("run_id")
    manifest_run_id = getattr(manifest, "run_id", None)
    if (
        isinstance(summary_run_id, str)
        and isinstance(manifest_run_id, str)
        and summary_run_id != manifest_run_id
    ):
        issues.append(
            MaintenanceCheckIssue(
                path=manifest_path,
                message=(
                    f"run ID mismatch: summary={summary_run_id!r}, "
                    f"manifest={manifest_run_id!r}"
                ),
            )
        )


def _validate_summary_markdown(path: Path) -> None:
    text = _read_utf8_text(path)
    first = next(
        (line.strip() for line in text.splitlines() if line.strip()),
        "",
    )
    if first != "# GF Wordbench Audit Summary":
        raise ValueError(
            "summary.md must begin with "
            "'# GF Wordbench Audit Summary'"
        )


def _contained_artifact_path(
    run_dir: Path,
    value: str,
) -> Path:
    if "\\" in value:
        raise ValueError(
            "artifact paths must use canonical '/' separators"
        )
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(
        part in {"", ".", ".."}
        for part in pure.parts
    ):
        raise ValueError(
            "artifact path must be a contained non-empty "
            "run-relative POSIX path"
        )

    root = run_dir.resolve(strict=False)
    candidate = root.joinpath(*pure.parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "artifact path escapes the run directory"
        ) from exc
    return resolved


def _read_utf8_text(path: Path) -> str:
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is prohibited")
    return payload.decode("utf-8")


def _header_value(line: str, prefix: str) -> str:
    if not line.startswith(prefix):
        raise ValueError(
            f"expected header prefix {prefix!r}"
        )
    value = line[len(prefix):]
    if not value:
        raise ValueError(
            f"header {prefix!r} must have a value"
        )
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raise_schema_check_failure(
    issues: Sequence[MaintenanceCheckIssue],
) -> None:
    detail = _format_issues(issues)
    raise SchemaValidationError(
        f"{len(issues)} persisted asset(s) failed schema validation",
        code="GF-WB-SCHEMA-905",
        detail=detail,
        stage="schema",
        operation="schemas-check",
        evidence_paths=tuple(str(item.path) for item in issues),
    )


def _raise_report_check_failure(
    run_dir: Path,
    issues: Sequence[MaintenanceCheckIssue],
) -> None:
    detail = _format_issues(issues)
    raise ContractViolationError(
        f"run report integrity check failed with {len(issues)} issue(s)",
        code="GF-WB-REPORT-903",
        detail=detail,
        stage="reporting",
        operation="reports-check",
        subject=str(run_dir),
        evidence_paths=tuple(str(item.path) for item in issues),
    )


def _format_issues(
    issues: Sequence[MaintenanceCheckIssue],
) -> str:
    rendered = "; ".join(
        f"{item.path}: {item.message}"
        for item in tuple(issues)[:20]
    )
    if len(issues) > 20:
        rendered += (
            f"; {len(issues) - 20} additional issue(s) omitted"
        )
    return rendered[:8_000]


def _exception_message(error: BaseException) -> str:
    message = " ".join(
        str(error).replace("\x00", "\\x00").split()
    )
    if not message:
        message = type(error).__name__
    return f"{type(error).__name__}: {message}"[:2_000]


def _bounded_text(
    value: object,
    *,
    field: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > max_length:
        raise ValueError(
            f"{field} exceeds {max_length} characters"
        )
    return value




def _scenario_id_tuple(
    values: Sequence[object],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field} must be a sequence of scenario IDs")

    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(tuple(values)):
        if not isinstance(value, str):
            raise TypeError(
                f"{field}[{index}] must be a string"
            )
        scenario_id = str(validate_scenario_id(value))
        if scenario_id in seen:
            raise ValueError(
                f"{field} contains duplicate scenario ID "
                f"{scenario_id!r}"
            )
        seen.add(scenario_id)
        result.append(scenario_id)
    return tuple(result)


def _text_tuple(
    values: Sequence[object],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field} must be a sequence of strings")

    result: list[str] = []
    for index, value in enumerate(tuple(values)):
        result.append(
            _bounded_text(
                value,
                field=f"{field}[{index}]",
                max_length=2_000,
            )
        )
    return tuple(result)


def _project_initialization_request_type() -> type[object]:
    from gf_wordbench.projects.initializer import (
        ProjectInitializationRequest,
    )

    return ProjectInitializationRequest


def _reset_request_type() -> type[object]:
    from gf_wordbench.projects.resetter import ResetRequest

    return ResetRequest


def _project_migration_request_type() -> type[object]:
    from gf_wordbench.projects.migrator import (
        ProjectMigrationRequest,
    )

    return ProjectMigrationRequest


def _absolute_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    return value


def _require_result(
    value: object,
    expected_type: type[_ResultT],
    *,
    service: str,
) -> _ResultT:
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{service} returned {type(value).__name__}; "
            f"expected {expected_type.__name__}"
        )
    return value


__all__ = (
    "ApplyProjectMigrationCommand",
    "ApplyProjectMigrationService",
    "ApplyProjectResetCommand",
    "ApplyProjectResetService",
    "GoldUpdateApplicationFactory",
    "GoldUpdateCliApplication",
    "GoldUpdateCommandRequest",
    "InitializeProjectCommand",
    "InitializeProjectService",
    "MaintenanceCheckIssue",
    "MaintenanceCheckResult",
    "MaintenanceCommand",
    "MaintenanceCommandKind",
    "MaintenanceCommandResult",
    "MaintenanceCommandServices",
    "PlanProjectMigrationCommand",
    "PlanProjectMigrationService",
    "PlanProjectResetCommand",
    "PlanProjectResetService",
    "ResetApplicationStateCommand",
    "ResetApplicationStateService",
    "StateResetResult",
    "default_state_reset_service",
    "execute_gold_update_command",
    "execute_gold_update_with_application",
    "execute_maintenance_command",
    "execute_reports_check_command",
    "execute_schemas_check_command",
    "gold_update_request_from_cli_request",
    "maintenance_command_is_destructive",
    "maintenance_command_is_dry_run",
    "maintenance_command_kind",
    "reset_application_state",
)
