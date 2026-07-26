"""Component tests for deterministic validation-pipeline orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.validation.pipeline import (
    CANONICAL_STAGE_ORDER,
    PipelineStageContext,
    PipelineStageResult,
    StageParticipation,
    ValidationPipelinePlan,
    ValidationStageClass,
    ValidationStageId,
    aggregate_pipeline_status,
    execute_validation_pipeline,
)

_NOW: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

_STAGE_CLASSES: Final[Mapping[ValidationStageId, ValidationStageClass]] = (
    MappingProxyType(
        {
            ValidationStageId.SELECT: ValidationStageClass.INVENTORY,
            ValidationStageId.INVENTORY: ValidationStageClass.INVENTORY,
            ValidationStageId.STATIC_SCAN: ValidationStageClass.ANALYSIS,
            ValidationStageId.COMPILE: ValidationStageClass.ANALYSIS,
            ValidationStageId.NORMALIZE_DIAGNOSTICS: (
                ValidationStageClass.ANALYSIS
            ),
            ValidationStageId.CLASSIFY_FAILURES: (
                ValidationStageClass.ANALYSIS
            ),
            ValidationStageId.EXECUTE_SCENARIOS: (
                ValidationStageClass.SCENARIO
            ),
            ValidationStageId.NORMALIZE_SCENARIOS: (
                ValidationStageClass.SCENARIO
            ),
            ValidationStageId.COMPARE_GOLD: (
                ValidationStageClass.SCENARIO
            ),
            ValidationStageId.BUILD_RELEASE_ARTIFACTS: (
                ValidationStageClass.RELEASE
            ),
            ValidationStageId.EVALUATE_RELEASE: (
                ValidationStageClass.RELEASE
            ),
            ValidationStageId.COMPARE_PREVIOUS: (
                ValidationStageClass.FINALIZATION
            ),
        }
    )
)

_QUICK_REQUIRED_STAGES: Final[tuple[ValidationStageId, ...]] = (
    ValidationStageId.SELECT,
    ValidationStageId.INVENTORY,
    ValidationStageId.STATIC_SCAN,
    ValidationStageId.COMPILE,
    ValidationStageId.NORMALIZE_DIAGNOSTICS,
)


@dataclass(slots=True)
class _CancellationSequence:
    responses: list[bool]
    reason: str | None = "Cancelled by test."

    def is_cancellation_requested(self) -> bool:
        if not self.responses:
            return False
        return self.responses.pop(0)

    def cancellation_reason(self) -> str | None:
        return self.reason


def _result(
    context: PipelineStageContext,
    *,
    status: ValidationStatus = ValidationStatus.OK,
    error_kind: ErrorKind | None = None,
    message: str = "Stage completed.",
    execution_state: ExecutionState | None = None,
    blocked_by: tuple[ValidationStageId, ...] = (),
    payload: object | None = None,
    abort_pipeline: bool = False,
) -> PipelineStageResult:
    resolved_error_kind = error_kind
    if resolved_error_kind is None:
        resolved_error_kind = (
            ErrorKind.OK
            if status in {ValidationStatus.OK, ValidationStatus.SKIPPED}
            else ErrorKind.OTHER
        )

    return PipelineStageResult(
        stage_id=context.stage_id,
        stage_name=context.stage_id.name.replace("_", " ").title(),
        stage_class=_STAGE_CLASSES[context.stage_id],
        required=(
            context.participation is StageParticipation.REQUIRED
        ),
        started_at=_NOW,
        finished_at=_NOW,
        duration_ms=0,
        validation_status=status,
        execution_state=execution_state,
        error_kind=resolved_error_kind,
        message=message,
        blocked_by=blocked_by,
        payload=payload,
        abort_pipeline=abort_pipeline,
    )


def _executor(
    calls: list[ValidationStageId],
    *,
    status: ValidationStatus = ValidationStatus.OK,
    error_kind: ErrorKind | None = None,
    message: str = "Stage completed.",
    abort_pipeline: bool = False,
) -> Callable[[PipelineStageContext], PipelineStageResult]:
    def execute(context: PipelineStageContext) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _result(
            context,
            status=status,
            error_kind=error_kind,
            message=message,
            abort_pipeline=abort_pipeline,
        )

    return execute


def _focused_plan(
    *,
    required: tuple[ValidationStageId, ...],
    optional: tuple[ValidationStageId, ...] = (),
    conditional: tuple[ValidationStageId, ...] = (),
    enabled_conditional: frozenset[ValidationStageId] = frozenset(),
    executors: Mapping[
        ValidationStageId,
        Callable[[PipelineStageContext], PipelineStageResult],
    ],
    guards: Mapping[
        ValidationStageId,
        Callable[[PipelineStageContext], tuple[ValidationStageId, ...]],
    ] | None = None,
    metadata: Mapping[str, str] | None = None,
) -> ValidationPipelinePlan:
    overrides = {
        stage_id: StageParticipation.SKIPPED
        for stage_id in CANONICAL_STAGE_ORDER
    }
    overrides.update(
        {
            stage_id: StageParticipation.REQUIRED
            for stage_id in required
        }
    )
    overrides.update(
        {
            stage_id: StageParticipation.OPTIONAL
            for stage_id in optional
        }
    )
    overrides.update(
        {
            stage_id: StageParticipation.CONDITIONAL
            for stage_id in conditional
        }
    )

    return ValidationPipelinePlan(
        mode=ValidationMode.DIAGNOSTIC,
        request={"request_id": "component-test"},
        executors=executors,
        guards={} if guards is None else guards,
        participation_overrides=overrides,
        enabled_conditional_stages=enabled_conditional,
        metadata={} if metadata is None else metadata,
    )


def _run(
    plan: ValidationPipelinePlan,
    *,
    cancellation_source: _CancellationSequence | None = None,
):
    return execute_validation_pipeline(
        plan,
        cancellation_source=cancellation_source,
        utc_now=lambda: _NOW,
        monotonic_now=lambda: 10.0,
    )


def test_canonical_stage_order_is_stable_and_unique() -> None:
    assert CANONICAL_STAGE_ORDER == tuple(ValidationStageId)
    assert len(CANONICAL_STAGE_ORDER) == 12
    assert len(set(CANONICAL_STAGE_ORDER)) == len(
        CANONICAL_STAGE_ORDER
    )
    assert CANONICAL_STAGE_ORDER[0] is ValidationStageId.SELECT
    assert (
        CANONICAL_STAGE_ORDER[-1]
        is ValidationStageId.COMPARE_PREVIOUS
    )


def test_quick_mode_requires_executors_for_every_required_stage() -> None:
    with pytest.raises(
        ValueError,
        match=r"required stage VAL-080 has no executor",
    ):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors={},
        )


def test_quick_mode_executes_required_stages_in_canonical_order() -> None:
    calls: list[ValidationStageId] = []
    observed_previous: dict[
        ValidationStageId,
        tuple[ValidationStageId, ...],
    ] = {}

    def executor(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        calls.append(context.stage_id)
        observed_previous[context.stage_id] = tuple(
            context.previous_results
        )
        assert context.metadata == {"run_id": "run-test"}
        return _result(context)

    plan = ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request={"target": "Main.gf"},
        executors={
            stage_id: executor
            for stage_id in _QUICK_REQUIRED_STAGES
        },
        metadata={"run_id": "run-test"},
    )

    result = _run(plan)

    assert calls == list(_QUICK_REQUIRED_STAGES)
    assert observed_previous[ValidationStageId.SELECT] == ()
    assert observed_previous[ValidationStageId.INVENTORY] == (
        ValidationStageId.SELECT,
    )
    assert tuple(item.stage_id for item in result.stage_results) == (
        CANONICAL_STAGE_ORDER
    )
    assert all(
        result.result_for(stage_id).validation_status
        is ValidationStatus.OK
        for stage_id in _QUICK_REQUIRED_STAGES
    )
    assert all(
        result.result_for(stage_id).validation_status
        is ValidationStatus.SKIPPED
        for stage_id in CANONICAL_STAGE_ORDER
        if stage_id not in _QUICK_REQUIRED_STAGES
    )
    assert result.overall_status is OverallStatus.OK
    assert result.cancelled is False
    assert result.cancellation_reason is None


def test_disabled_conditional_stage_is_skipped_without_execution() -> None:
    calls: list[ValidationStageId] = []
    stage_id = ValidationStageId.COMPARE_GOLD
    plan = _focused_plan(
        required=(),
        conditional=(stage_id,),
        executors={stage_id: _executor(calls)},
    )

    result = _run(plan)
    stage_result = result.result_for(stage_id)

    assert calls == []
    assert stage_result.validation_status is ValidationStatus.SKIPPED
    assert stage_result.required is False
    assert result.overall_status is OverallStatus.OK


def test_enabled_conditional_stage_executes() -> None:
    calls: list[ValidationStageId] = []
    stage_id = ValidationStageId.COMPARE_GOLD
    plan = _focused_plan(
        required=(),
        conditional=(stage_id,),
        enabled_conditional=frozenset({stage_id}),
        executors={stage_id: _executor(calls)},
    )

    result = _run(plan)

    assert calls == [stage_id]
    assert (
        result.result_for(stage_id).validation_status
        is ValidationStatus.OK
    )
    assert result.overall_status is OverallStatus.OK


def test_optional_stage_without_executor_is_non_fatal() -> None:
    stage_id = ValidationStageId.COMPARE_PREVIOUS
    plan = _focused_plan(
        required=(),
        optional=(stage_id,),
        executors={},
    )

    result = _run(plan)
    stage_result = result.result_for(stage_id)

    assert stage_result.validation_status is ValidationStatus.SKIPPED
    assert stage_result.required is False
    assert result.overall_status is OverallStatus.OK


def test_executor_exception_becomes_error_and_blocks_required_dependent() -> None:
    calls: list[ValidationStageId] = []

    def failing_executor(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        calls.append(context.stage_id)
        raise RuntimeError("scanner exploded")

    plan = _focused_plan(
        required=(
            ValidationStageId.INVENTORY,
            ValidationStageId.STATIC_SCAN,
        ),
        executors={
            ValidationStageId.INVENTORY: failing_executor,
            ValidationStageId.STATIC_SCAN: _executor(calls),
        },
    )

    result = _run(plan)
    inventory = result.result_for(ValidationStageId.INVENTORY)
    scan = result.result_for(ValidationStageId.STATIC_SCAN)

    assert calls == [ValidationStageId.INVENTORY]
    assert inventory.validation_status is ValidationStatus.ERROR
    assert inventory.error_kind is ErrorKind.INTERNAL
    assert inventory.message == "RuntimeError: scanner exploded"
    assert scan.validation_status is ValidationStatus.SKIPPED
    assert scan.blocked_by == (ValidationStageId.INVENTORY,)
    assert scan.required is True
    assert result.overall_status is OverallStatus.ERROR


def test_required_validation_failure_remains_available_to_later_analysis() -> None:
    calls: list[ValidationStageId] = []
    plan = _focused_plan(
        required=(
            ValidationStageId.COMPILE,
            ValidationStageId.NORMALIZE_DIAGNOSTICS,
        ),
        executors={
            ValidationStageId.COMPILE: _executor(
                calls,
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.TYPE,
                message="GF type error.",
            ),
            ValidationStageId.NORMALIZE_DIAGNOSTICS: _executor(calls),
        },
    )

    result = _run(plan)

    assert calls == [
        ValidationStageId.COMPILE,
        ValidationStageId.NORMALIZE_DIAGNOSTICS,
    ]
    assert (
        result.result_for(
            ValidationStageId.NORMALIZE_DIAGNOSTICS
        ).validation_status
        is ValidationStatus.OK
    )
    assert result.overall_status is OverallStatus.FAIL


def test_guard_can_block_a_required_stage_with_explicit_provenance() -> None:
    calls: list[ValidationStageId] = []
    guarded_stage = ValidationStageId.CLASSIFY_FAILURES

    def guard(
        context: PipelineStageContext,
    ) -> tuple[ValidationStageId, ...]:
        assert context.stage_id is guarded_stage
        return (
            ValidationStageId.COMPILE,
            ValidationStageId.NORMALIZE_DIAGNOSTICS,
        )

    plan = _focused_plan(
        required=(guarded_stage,),
        executors={guarded_stage: _executor(calls)},
        guards={guarded_stage: guard},
    )

    result = _run(plan)
    guarded = result.result_for(guarded_stage)

    assert calls == []
    assert guarded.validation_status is ValidationStatus.SKIPPED
    assert guarded.blocked_by == (
        ValidationStageId.COMPILE,
        ValidationStageId.NORMALIZE_DIAGNOSTICS,
    )
    assert result.overall_status is OverallStatus.FAIL


def test_abort_flag_skips_all_later_stages() -> None:
    calls: list[ValidationStageId] = []
    first = ValidationStageId.SELECT
    second = ValidationStageId.INVENTORY

    plan = _focused_plan(
        required=(first, second),
        executors={
            first: _executor(calls, abort_pipeline=True),
            second: _executor(calls),
        },
    )

    result = _run(plan)

    assert calls == [first]
    assert result.result_for(first).abort_pipeline is True
    assert (
        result.result_for(second).validation_status
        is ValidationStatus.SKIPPED
    )
    assert result.result_for(second).required is True
    assert result.overall_status is OverallStatus.FAIL


def test_cancellation_before_first_stage_skips_required_work() -> None:
    calls: list[ValidationStageId] = []
    stage_id = ValidationStageId.SELECT
    source = _CancellationSequence(
        responses=[True],
        reason="User cancelled validation.",
    )
    plan = _focused_plan(
        required=(stage_id,),
        executors={stage_id: _executor(calls)},
    )

    result = _run(plan, cancellation_source=source)
    stage_result = result.result_for(stage_id)

    assert calls == []
    assert result.cancelled is True
    assert result.cancellation_reason == "User cancelled validation."
    assert stage_result.validation_status is ValidationStatus.SKIPPED
    assert stage_result.message == "User cancelled validation."
    assert result.overall_status is OverallStatus.FAIL


def test_cancellation_between_stages_preserves_completed_result() -> None:
    calls: list[ValidationStageId] = []
    first = ValidationStageId.SELECT
    second = ValidationStageId.INVENTORY
    source = _CancellationSequence(
        responses=[False, True],
        reason=None,
    )
    plan = _focused_plan(
        required=(first, second),
        executors={
            first: _executor(calls),
            second: _executor(calls),
        },
    )

    result = _run(plan, cancellation_source=source)

    assert calls == [first]
    assert (
        result.result_for(first).validation_status
        is ValidationStatus.OK
    )
    assert (
        result.result_for(second).validation_status
        is ValidationStatus.SKIPPED
    )
    assert result.cancelled is True
    assert result.cancellation_reason == "Cancellation requested."
    assert result.overall_status is OverallStatus.FAIL


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (
            (
                (ValidationStatus.OK, True),
                (ValidationStatus.FAIL, False),
            ),
            OverallStatus.OK,
        ),
        (
            (
                (ValidationStatus.OK, True),
                (ValidationStatus.FAIL, True),
            ),
            OverallStatus.FAIL,
        ),
        (
            (
                (ValidationStatus.SKIPPED, True),
                (ValidationStatus.FAIL, False),
            ),
            OverallStatus.FAIL,
        ),
        (
            (
                (ValidationStatus.ERROR, False),
                (ValidationStatus.FAIL, True),
            ),
            OverallStatus.ERROR,
        ),
    ],
)
def test_aggregate_pipeline_status_obeys_error_and_requiredness_precedence(
    statuses: tuple[tuple[ValidationStatus, bool], ...],
    expected: OverallStatus,
) -> None:
    results = tuple(
        PipelineStageResult(
            stage_id=CANONICAL_STAGE_ORDER[index],
            stage_name=f"Stage {index}",
            stage_class=_STAGE_CLASSES[
                CANONICAL_STAGE_ORDER[index]
            ],
            required=required,
            started_at=_NOW,
            finished_at=_NOW,
            duration_ms=0,
            validation_status=status,
            execution_state=None,
            error_kind=(
                ErrorKind.OK
                if status
                in {
                    ValidationStatus.OK,
                    ValidationStatus.SKIPPED,
                }
                else ErrorKind.OTHER
            ),
            message=f"Result {index}.",
        )
        for index, (status, required) in enumerate(statuses)
    )

    assert aggregate_pipeline_status(results) is expected


def test_executor_must_return_result_for_active_stage() -> None:
    stage_id = ValidationStageId.SELECT

    def wrong_stage(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        result = _result(context)
        return PipelineStageResult(
            stage_id=ValidationStageId.INVENTORY,
            stage_name=result.stage_name,
            stage_class=ValidationStageClass.INVENTORY,
            required=result.required,
            started_at=result.started_at,
            finished_at=result.finished_at,
            duration_ms=result.duration_ms,
            validation_status=result.validation_status,
            execution_state=result.execution_state,
            error_kind=result.error_kind,
            message=result.message,
        )

    plan = _focused_plan(
        required=(stage_id,),
        executors={stage_id: wrong_stage},
    )

    with pytest.raises(
        ValueError,
        match="result for another stage",
    ):
        _run(plan)


def test_executor_cannot_change_planned_required_flag() -> None:
    stage_id = ValidationStageId.SELECT

    def wrong_required(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        return PipelineStageResult(
            stage_id=context.stage_id,
            stage_name="Select",
            stage_class=ValidationStageClass.INVENTORY,
            required=False,
            started_at=_NOW,
            finished_at=_NOW,
            duration_ms=0,
            validation_status=ValidationStatus.OK,
            execution_state=None,
            error_kind=ErrorKind.OK,
            message="Completed.",
        )

    plan = _focused_plan(
        required=(stage_id,),
        executors={stage_id: wrong_required},
    )

    with pytest.raises(
        ValueError,
        match="changed the planned required flag",
    ):
        _run(plan)


def test_stage_result_rejects_inconsistent_error_kind() -> None:
    with pytest.raises(
        ValueError,
        match="FAIL or ERROR stage results require a non-OK error kind",
    ):
        PipelineStageResult(
            stage_id=ValidationStageId.COMPILE,
            stage_name="Compile",
            stage_class=ValidationStageClass.ANALYSIS,
            required=True,
            started_at=_NOW,
            finished_at=_NOW,
            duration_ms=0,
            validation_status=ValidationStatus.FAIL,
            execution_state=ExecutionState.COMPLETED,
            error_kind=ErrorKind.OK,
            message="GF validation failed.",
            artifact_paths=(Path("stderr.log"),),
        )
