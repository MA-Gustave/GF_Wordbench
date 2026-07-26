"""Typed CLI adapters for explicit GF Wordbench maintenance use cases."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, TypeAlias, TypeVar

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
        if not isinstance(self.request, ProjectInitializationRequest):
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
        if not isinstance(self.request, ResetRequest):
            raise TypeError("request must be ResetRequest")

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.PLAN_PROJECT_RESET


@dataclass(frozen=True, slots=True)
class ApplyProjectResetCommand:
    request: ResetRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, ResetRequest):
            raise TypeError("request must be ResetRequest")

    @property
    def kind(self) -> MaintenanceCommandKind:
        return MaintenanceCommandKind.APPLY_PROJECT_RESET


@dataclass(frozen=True, slots=True)
class PlanProjectMigrationCommand:
    request: ProjectMigrationRequest

    def __post_init__(self) -> None:
        if not isinstance(self.request, ProjectMigrationRequest):
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
        if not isinstance(self.request, ProjectMigrationRequest):
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


MaintenanceCommand: TypeAlias = (
    InitializeProjectCommand
    | PlanProjectResetCommand
    | ApplyProjectResetCommand
    | PlanProjectMigrationCommand
    | ApplyProjectMigrationCommand
    | ResetApplicationStateCommand
)

_ResultT = TypeVar("_ResultT")

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
PlanProjectResetService: TypeAlias = Callable[[ResetRequest], ResetPlan]
ApplyProjectResetService: TypeAlias = Callable[[ResetRequest], ResetResult]
PlanProjectMigrationService: TypeAlias = Callable[
    [ProjectMigrationRequest],
    ProjectMigrationPlan,
]
ApplyProjectMigrationService: TypeAlias = Callable[
    [ProjectMigrationRequest],
    ProjectMigrationResult,
]
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
        result = services.initialize_project(command.request)
        return _require_result(
            result,
            ProjectInitializationResult,
            service="initialize_project",
        )

    if isinstance(command, PlanProjectResetCommand):
        result = services.plan_project_reset(command.request)
        return _require_result(
            result,
            ResetPlan,
            service="plan_project_reset",
        )

    if isinstance(command, ApplyProjectResetCommand):
        result = services.apply_project_reset(command.request)
        return _require_result(
            result,
            ResetResult,
            service="apply_project_reset",
        )

    if isinstance(command, PlanProjectMigrationCommand):
        result = services.plan_project_migration(command.request)
        return _require_result(
            result,
            ProjectMigrationPlan,
            service="plan_project_migration",
        )

    if isinstance(command, ApplyProjectMigrationCommand):
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
    "InitializeProjectCommand",
    "InitializeProjectService",
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
    "execute_maintenance_command",
    "maintenance_command_is_destructive",
    "maintenance_command_is_dry_run",
    "maintenance_command_kind",
    "reset_application_state",
)
