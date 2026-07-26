"""Unit tests for active-project reset lifecycle planning and orchestration."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from gf_wordbench.kernel.ids import validate_project_id
from gf_wordbench.projects.ports import LifecycleLockRequest
from gf_wordbench.projects.resetter import (
    LifecycleErrorCategory,
    PhaseStatus,
    PreservationMode,
    ProjectResetError,
    ProjectResetter,
    ResetOutcome,
    ResetPhase,
    ResetPlan,
    ResetRequest,
    ResetResult,
    ResetScope,
    plan_project_reset,
    reset_project,
)


@dataclass(slots=True)
class _ResetOperations:
    failures: dict[str, BaseException] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)

    def _call(self, name: str) -> None:
        self.calls.append(name)
        failure = self.failures.get(name)
        if failure is not None:
            raise failure

    @contextmanager
    def lifecycle_lock(self, plan: ResetPlan) -> Iterator[None]:
        assert isinstance(plan, ResetPlan)
        self._call("lifecycle_lock_enter")
        try:
            yield
        finally:
            self.calls.append("lifecycle_lock_exit")

    def preflight(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("preflight")

    def archive_project(self, plan: ResetPlan) -> None:
        assert plan.request.preservation is PreservationMode.ARCHIVE
        self._call("archive_project")

    def authorize_discard(self, plan: ResetPlan) -> None:
        assert plan.request.preservation is PreservationMode.DISCARD
        self._call("authorize_discard")

    def stage_template(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("stage_template")

    def validate_staged_project(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("validate_staged_project")

    def swap_project(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("swap_project")

    def validate_active_project(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("validate_active_project")

    def cleanup_runs(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("cleanup_runs")

    def reset_application_state(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("reset_application_state")

    def complete(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("complete")

    def discard_stage(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("discard_stage")

    def rollback(self, plan: ResetPlan) -> None:
        assert isinstance(plan, ResetPlan)
        self._call("rollback")


def _archive_request(
    tmp_path: Path,
    *,
    scope: ResetScope = ResetScope.NEW_PROJECT,
    dry_run: bool = False,
    warnings: tuple[str, ...] = (),
) -> ResetRequest:
    workspace_root = (tmp_path / "workspace").resolve()
    return ResetRequest(
        workspace_root=workspace_root,
        scope=scope,
        preservation=PreservationMode.ARCHIVE,
        archive_destination=(tmp_path / "archives" / "project.zip").resolve(),
        expected_project_id=validate_project_id("example-language"),
        current_project_id=validate_project_id("example-language"),
        dry_run=dry_run,
        run_paths=(
            workspace_root / "run_20260725_120000",
            workspace_root / "run_20260725_130000",
        ),
        external_source_roots=((tmp_path / "external-source").resolve(),),
        warnings=warnings,
    )


def _discard_request(
    tmp_path: Path,
    *,
    scope: ResetScope = ResetScope.PROJECT_ONLY,
) -> ResetRequest:
    workspace_root = (tmp_path / "workspace").resolve()
    return ResetRequest(
        workspace_root=workspace_root,
        scope=scope,
        preservation=PreservationMode.DISCARD,
        discard_authorized=True,
        confirmation_token="replace-example-language",
        current_project_id=validate_project_id("example-language"),
        run_paths=(workspace_root / "run_20260725_120000",),
    )


def _phase_values(
    result: ResetResult,
) -> tuple[tuple[ResetPhase, PhaseStatus], ...]:
    return tuple((record.phase, record.status) for record in result.phases)


def test_lifecycle_lock_request_normalizes_time_and_preserves_identity(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()
    started_at = datetime(2026, 7, 25, 15, 30, tzinfo=UTC)

    request = LifecycleLockRequest(
        operation_id="reset-0123456789abcdefabcd",
        operation_type="project-reset",
        process_id=1234,
        started_at=started_at,
        workspace_root=workspace_root,
    )

    assert request.operation_id == "reset-0123456789abcdefabcd"
    assert request.operation_type == "project-reset"
    assert request.process_id == 1234
    assert request.started_at == started_at
    assert request.workspace_root == workspace_root


def test_lifecycle_lock_request_rejects_naive_time_and_relative_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        LifecycleLockRequest(
            operation_id="reset-0123456789abcdefabcd",
            operation_type="project-reset",
            process_id=1234,
            started_at=datetime(2026, 7, 25, 15, 30),
            workspace_root=tmp_path.resolve(),
        )

    with pytest.raises(ValueError, match="absolute"):
        LifecycleLockRequest(
            operation_id="reset-0123456789abcdefabcd",
            operation_type="project-reset",
            process_id=1234,
            started_at=datetime(2026, 7, 25, 15, 30, tzinfo=UTC),
            workspace_root=Path("workspace"),
        )


def test_reset_request_requires_archive_or_explicit_discard(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()

    with pytest.raises(ValueError, match="archive mode requires"):
        ResetRequest(workspace_root=workspace_root)

    with pytest.raises(ValueError, match="explicit authorization"):
        ResetRequest(
            workspace_root=workspace_root,
            preservation=PreservationMode.DISCARD,
        )

    with pytest.raises(ValueError, match="forbids discard_authorized"):
        ResetRequest(
            workspace_root=workspace_root,
            archive_destination=(tmp_path / "archive.zip").resolve(),
            discard_authorized=True,
        )


def test_reset_request_rejects_mismatched_project_identity(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="does not match"):
        ResetRequest(
            workspace_root=(tmp_path / "workspace").resolve(),
            archive_destination=(tmp_path / "archive.zip").resolve(),
            expected_project_id=validate_project_id("expected-language"),
            current_project_id=validate_project_id("different-language"),
        )


def test_reset_request_rejects_noncanonical_run_paths(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()

    with pytest.raises(ValueError, match="canonical run"):
        ResetRequest(
            workspace_root=workspace_root,
            archive_destination=(tmp_path / "archive.zip").resolve(),
            run_paths=(workspace_root / "runs" / "run_20260725_120000",),
        )

    with pytest.raises(ValueError, match="canonical run"):
        ResetRequest(
            workspace_root=workspace_root,
            archive_destination=(tmp_path / "archive.zip").resolve(),
            run_paths=(workspace_root / "results",),
        )


def test_new_project_reset_plan_is_deterministic_and_path_safe(
    tmp_path: Path,
) -> None:
    request = _archive_request(tmp_path)

    first = plan_project_reset(request)
    second = plan_project_reset(request)

    assert first == second
    assert first.operation_id.startswith("reset-")
    assert len(first.operation_id) == len("reset-") + 20
    assert first.project_path == request.workspace_root / "project"
    assert first.template_path == request.workspace_root / "templates" / "project"
    assert first.state_path == request.workspace_root / ".gf_wordbench_state.json"
    assert first.staging_path.parent == request.workspace_root
    assert first.rollback_path.parent == request.workspace_root
    assert first.replace_paths == (first.project_path,)
    assert set(first.removal_paths) == {*request.run_paths, first.state_path}
    assert len(first.removal_paths) == 3
    assert first.template_path in first.preserve_paths
    assert request.external_source_roots[0] in first.preserve_paths
    assert first.project_path not in first.preserve_paths
    assert first.remaining_initialization_actions
    assert any("External source roots" in warning for warning in first.warnings)


def test_operation_identity_ignores_dry_run_and_display_warnings(
    tmp_path: Path,
) -> None:
    normal = _archive_request(tmp_path)
    dry_run = _archive_request(tmp_path, dry_run=True, warnings=("display only",))

    assert plan_project_reset(normal).operation_id == plan_project_reset(dry_run).operation_id


def test_project_only_plan_preserves_runs_and_state(
    tmp_path: Path,
) -> None:
    request = _discard_request(tmp_path)

    plan = plan_project_reset(request)

    assert plan.removal_paths == ()
    assert request.run_paths[0] in plan.preserve_paths
    assert plan.state_path in plan.preserve_paths
    assert any("retains runs and state" in warning for warning in plan.warnings)


def test_plan_warns_when_expected_identity_requires_preflight_verification(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()
    request = ResetRequest(
        workspace_root=workspace_root,
        archive_destination=(tmp_path / "archive.zip").resolve(),
        expected_project_id=validate_project_id("example-language"),
    )

    plan = plan_project_reset(request)

    assert any("verify expected_project_id" in warning for warning in plan.warnings)


def test_reset_plan_rejects_archive_overlap_with_controlled_paths(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()
    request = ResetRequest(
        workspace_root=workspace_root,
        archive_destination=workspace_root / "project" / "archive.zip",
    )

    with pytest.raises(ValueError, match="overlaps"):
        plan_project_reset(request)


def test_reset_plan_rejects_external_source_overlap(
    tmp_path: Path,
) -> None:
    workspace_root = (tmp_path / "workspace").resolve()
    request = ResetRequest(
        workspace_root=workspace_root,
        archive_destination=(tmp_path / "archive.zip").resolve(),
        external_source_roots=(workspace_root / "project" / "src",),
    )

    with pytest.raises(ValueError, match="external source roots"):
        plan_project_reset(request)


def test_dry_run_performs_preflight_and_no_mutating_operation(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations()

    result = reset_project(
        _archive_request(tmp_path, dry_run=True),
        operations=operations,
    )

    assert result.outcome is ResetOutcome.DRY_RUN
    assert result.succeeded is True
    assert operations.calls == ["preflight"]
    assert _phase_values(result)[0:2] == (
        (ResetPhase.PLAN, PhaseStatus.COMPLETED),
        (ResetPhase.PREFLIGHT, PhaseStatus.COMPLETED),
    )
    assert all(
        status is PhaseStatus.SKIPPED
        for _, status in _phase_values(result)[2:]
    )
    assert result.project_replacement_completed is False
    assert result.run_cleanup_completed is None
    assert result.state_reset_completed is None


def test_dry_run_preflight_failure_is_nonmutating_and_path_safe(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"preflight": OSError("template missing")}
    )

    result = reset_project(
        _archive_request(tmp_path, dry_run=True),
        operations=operations,
    )

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.PREFLIGHT
    assert result.failure.category is LifecycleErrorCategory.PATH_SAFETY
    assert operations.calls == ["preflight"]


def test_new_project_archive_reset_executes_canonical_phase_order(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations()

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.SUCCESS
    assert result.succeeded is True
    assert operations.calls == [
        "lifecycle_lock_enter",
        "preflight",
        "archive_project",
        "stage_template",
        "validate_staged_project",
        "swap_project",
        "validate_active_project",
        "cleanup_runs",
        "reset_application_state",
        "complete",
        "lifecycle_lock_exit",
    ]
    assert tuple(phase for phase, _ in _phase_values(result)) == (
        ResetPhase.PLAN,
        ResetPhase.PREFLIGHT,
        ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD,
        ResetPhase.STAGE,
        ResetPhase.VALIDATE_STAGE,
        ResetPhase.SWAP,
        ResetPhase.VALIDATE_ACTIVE_PROJECT,
        ResetPhase.CLEAN_GENERATED_STATE,
        ResetPhase.COMPLETE,
    )
    assert all(
        status is PhaseStatus.COMPLETED
        for _, status in _phase_values(result)
    )
    assert result.archive_completed is True
    assert result.project_staged is True
    assert result.project_replacement_completed is True
    assert result.active_project_validation_completed is True
    assert result.rollback_completed is None
    assert result.run_cleanup_completed is True
    assert result.state_reset_completed is True
    assert result.remaining_actions == result.plan.remaining_initialization_actions


def test_project_only_discard_reset_retains_runs_and_state(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations()

    result = reset_project(_discard_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.SUCCESS
    assert "archive_project" not in operations.calls
    assert "authorize_discard" in operations.calls
    assert "cleanup_runs" not in operations.calls
    assert "reset_application_state" not in operations.calls
    clean_phase = next(
        record
        for record in result.phases
        if record.phase is ResetPhase.CLEAN_GENERATED_STATE
    )
    assert clean_phase.status is PhaseStatus.SKIPPED
    assert result.archive_completed is None
    assert result.run_cleanup_completed is None
    assert result.state_reset_completed is None


def test_preflight_failure_blocks_archive_and_staging(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={
            "preflight": ProjectResetError(
                LifecycleErrorCategory.TEMPLATE,
                "Canonical template is incomplete.",
            )
        }
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.PREFLIGHT
    assert result.failure.category is LifecycleErrorCategory.TEMPLATE
    assert operations.calls == [
        "lifecycle_lock_enter",
        "preflight",
        "lifecycle_lock_exit",
    ]


def test_archive_failure_blocks_stage_and_preserves_original_project(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"archive_project": OSError("archive verification failed")}
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD
    assert result.failure.category is LifecycleErrorCategory.ARCHIVE
    assert result.project_staged is False
    assert result.project_replacement_completed is False
    assert "stage_template" not in operations.calls


def test_stage_validation_failure_discards_stage_and_keeps_project_unswapped(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={
            "validate_staged_project": ProjectResetError(
                LifecycleErrorCategory.VALIDATION,
                "Staged project is invalid.",
            )
        }
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.VALIDATE_STAGE
    assert result.failure.category is LifecycleErrorCategory.VALIDATION
    assert result.project_staged is True
    assert result.project_replacement_completed is False
    assert result.rollback_completed is None
    assert "discard_stage" in operations.calls
    assert "swap_project" not in operations.calls


def test_swap_failure_attempts_rollback_even_before_swap_is_recorded(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"swap_project": OSError("rename failed")}
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.SWAP
    assert result.failure.category is LifecycleErrorCategory.SWAP
    assert result.project_replacement_completed is False
    assert result.rollback_completed is True
    assert "rollback" in operations.calls


def test_active_validation_failure_restores_rollback_project(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={
            "validate_active_project": RuntimeError("active project invalid")
        }
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.VALIDATE_ACTIVE_PROJECT
    assert result.failure.category is LifecycleErrorCategory.VALIDATION
    assert result.project_replacement_completed is True
    assert result.active_project_validation_completed is False
    assert result.rollback_completed is True
    assert operations.calls.index("rollback") > operations.calls.index("swap_project")
    rollback_phase = next(
        record for record in result.phases if record.phase is ResetPhase.ROLLBACK
    )
    assert rollback_phase.status is PhaseStatus.COMPLETED


def test_rollback_failure_produces_critical_recovery_result(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={
            "validate_active_project": RuntimeError("active project invalid"),
            "rollback": OSError("rollback unavailable"),
        }
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.CRITICAL
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.ROLLBACK
    assert result.failure.category is LifecycleErrorCategory.ROLLBACK
    assert result.rollback_completed is False
    assert any("manual recovery" in action for action in result.remaining_actions)


def test_cleanup_failure_is_partial_and_attempts_both_cleanup_services(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"cleanup_runs": OSError("run cleanup failed")}
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.PARTIAL
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.CLEAN_GENERATED_STATE
    assert result.failure.category is LifecycleErrorCategory.CLEANUP
    assert result.project_replacement_completed is True
    assert result.active_project_validation_completed is True
    assert result.run_cleanup_completed is False
    assert result.state_reset_completed is True
    assert "reset_application_state" in operations.calls
    assert "complete" not in operations.calls
    assert any(
        "run-lifecycle service" in action
        for action in result.remaining_actions
    )


def test_state_cleanup_failure_does_not_undo_successful_run_cleanup(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={
            "reset_application_state": OSError("state reset failed")
        }
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.PARTIAL
    assert result.run_cleanup_completed is True
    assert result.state_reset_completed is False
    assert any(
        "application-state cleanup" in action
        for action in result.remaining_actions
    )


def test_completion_failure_keeps_validated_project_and_reports_partial(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"complete": OSError("temporary cleanup failed")}
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.PARTIAL
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.COMPLETE
    assert result.failure.category is LifecycleErrorCategory.CLEANUP
    assert result.project_replacement_completed is True
    assert result.active_project_validation_completed is True
    assert result.run_cleanup_completed is True
    assert result.state_reset_completed is True
    assert any(
        "Preserve the validated active project" in action
        for action in result.remaining_actions
    )


def test_lifecycle_lock_failure_is_classified_as_concurrency(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations(
        failures={"lifecycle_lock_enter": RuntimeError("lock held")}
    )

    result = reset_project(_archive_request(tmp_path), operations=operations)

    assert result.outcome is ResetOutcome.FAILED
    assert result.plan_created is True
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.PREFLIGHT
    assert result.failure.category is LifecycleErrorCategory.CONCURRENCY
    assert operations.calls == ["lifecycle_lock_enter"]


def test_invalid_planner_result_fails_before_lifecycle_lock(
    tmp_path: Path,
) -> None:
    operations = _ResetOperations()
    resetter = ProjectResetter(
        operations=operations,
        planner=lambda request: object(),  # type: ignore[arg-type,return-value]
    )

    result = resetter.reset(_archive_request(tmp_path))

    assert result.outcome is ResetOutcome.FAILED
    assert result.plan is None
    assert result.failure is not None
    assert result.failure.phase is ResetPhase.PLAN
    assert result.failure.category is LifecycleErrorCategory.CONFIGURATION
    assert operations.calls == []
