"""Integration tests for the CLI maintenance-command boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest

from gf_wordbench.entrypoints.cli.maintenance_commands import (
    ApplyProjectMigrationCommand,
    ApplyProjectResetCommand,
    InitializeProjectCommand,
    MaintenanceCommandKind,
    MaintenanceCommandServices,
    PlanProjectMigrationCommand,
    PlanProjectResetCommand,
    ResetApplicationStateCommand,
    StateResetResult,
    execute_maintenance_command,
    maintenance_command_is_destructive,
    maintenance_command_is_dry_run,
    maintenance_command_kind,
    reset_application_state,
)
from gf_wordbench.projects.initializer import ProjectInitializationResult
from gf_wordbench.projects.migrator import (
    ProjectMigrationPlan,
    ProjectMigrationResult,
)
from gf_wordbench.projects.resetter import ResetPlan, ResetResult

T = TypeVar("T")


def _uninitialized(model_type: type[T]) -> T:
    return object.__new__(model_type)


def _command_with_payload(command_type: type[T], payload: object) -> T:
    command_fields = fields(cast(Any, command_type))
    assert len(command_fields) == 1, f"{command_type.__name__} must own exactly one payload field"

    command = _uninitialized(command_type)
    object.__setattr__(command, command_fields[0].name, payload)
    return command


def _construct_state_reset_command(
    workspace_root: Path,
    *,
    state_path: Path | None = None,
    replace_with_defaults: bool = False,
) -> ResetApplicationStateCommand:
    return ResetApplicationStateCommand(
        workspace_root=workspace_root,
        state_path=state_path,
        replace_with_defaults=replace_with_defaults,
    )


def _service_bundle(
    service: Callable[[object], object],
) -> MaintenanceCommandServices:
    return cast(
        MaintenanceCommandServices,
        cast(Any, MaintenanceCommandServices)(
            initialize_project=service,
            plan_project_reset=service,
            apply_project_reset=service,
            plan_project_migration=service,
            apply_project_migration=service,
            reset_application_state=service,
        ),
    )


def _dispatch_cases() -> tuple[tuple[type[object], type[object], type[object]], ...]:
    return (
        (
            InitializeProjectCommand,
            ProjectInitializationResult,
            object,
        ),
        (PlanProjectResetCommand, ResetPlan, object),
        (ApplyProjectResetCommand, ResetResult, object),
        (PlanProjectMigrationCommand, ProjectMigrationPlan, object),
        (ApplyProjectMigrationCommand, ProjectMigrationResult, object),
    )


def test_command_kinds_are_stable_unique_and_owned_by_the_enum() -> None:
    commands = (
        _command_with_payload(InitializeProjectCommand, object()),
        _command_with_payload(PlanProjectResetCommand, object()),
        _command_with_payload(ApplyProjectResetCommand, object()),
        _command_with_payload(PlanProjectMigrationCommand, object()),
        _command_with_payload(ApplyProjectMigrationCommand, object()),
    )

    observed = tuple(maintenance_command_kind(command) for command in commands)

    assert all(isinstance(kind, MaintenanceCommandKind) for kind in observed)
    assert observed == tuple(command.kind for command in commands)
    assert len(set(observed)) == len(observed)


def test_plan_and_apply_commands_expose_explicit_safety_semantics() -> None:
    reset_plan = _command_with_payload(PlanProjectResetCommand, object())
    reset_apply = _command_with_payload(ApplyProjectResetCommand, object())
    migration_plan = _command_with_payload(
        PlanProjectMigrationCommand,
        object(),
    )
    migration_apply = _command_with_payload(
        ApplyProjectMigrationCommand,
        object(),
    )

    assert maintenance_command_is_dry_run(reset_plan) is True
    assert maintenance_command_is_dry_run(migration_plan) is True
    assert maintenance_command_is_destructive(reset_plan) is False
    assert maintenance_command_is_destructive(migration_plan) is False

    assert maintenance_command_is_dry_run(reset_apply) is False
    assert maintenance_command_is_dry_run(migration_apply) is False
    assert maintenance_command_is_destructive(reset_apply) is True
    assert maintenance_command_is_destructive(migration_apply) is True


@pytest.mark.parametrize(
    ("command_type", "result_type", "payload_factory"),
    _dispatch_cases(),
)
def test_execute_maintenance_command_routes_to_one_injected_service(
    command_type: type[object],
    result_type: type[object],
    payload_factory: type[object],
) -> None:
    payload = payload_factory()
    command = _command_with_payload(command_type, payload)
    expected = _uninitialized(result_type)
    calls: list[object] = []

    def service(received: object) -> object:
        calls.append(received)
        return expected

    result = execute_maintenance_command(
        cast(Any, command),
        services=_service_bundle(service),
    )

    assert result is expected
    assert calls == [payload]


@pytest.mark.parametrize(
    ("command_type", "payload_factory"),
    tuple((case[0], case[2]) for case in _dispatch_cases()),
)
def test_execute_maintenance_command_rejects_wrong_service_result_type(
    command_type: type[object],
    payload_factory: type[object],
) -> None:
    command = _command_with_payload(command_type, payload_factory())

    with pytest.raises(TypeError, match="result|return|expected"):
        execute_maintenance_command(
            cast(Any, command),
            services=_service_bundle(lambda _payload: object()),
        )


def test_reset_application_state_removes_only_workspace_state(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path.resolve()
    state_path = workspace_root / ".gf_wordbench_state.json"
    unrelated = workspace_root / "project.toml"
    state_path.write_text("{}\n", encoding="utf-8")
    unrelated.write_text("schema_id = 'gf-wordbench.project'\n", encoding="utf-8")

    result = reset_application_state(
        _construct_state_reset_command(
            workspace_root,
            state_path=state_path,
        )
    )

    assert isinstance(result, StateResetResult)
    assert result.changed is True
    assert not state_path.exists()
    assert unrelated.read_text(encoding="utf-8").startswith("schema_id")


def test_reset_application_state_is_idempotent_when_state_is_absent(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path.resolve()
    state_path = workspace_root / ".gf_wordbench_state.json"

    first = reset_application_state(
        _construct_state_reset_command(
            workspace_root,
            state_path=state_path,
        )
    )
    second = reset_application_state(
        _construct_state_reset_command(
            workspace_root,
            state_path=state_path,
        )
    )

    assert isinstance(first, StateResetResult)
    assert isinstance(second, StateResetResult)
    assert first.changed is False
    assert second.changed is False
    assert not state_path.exists()
