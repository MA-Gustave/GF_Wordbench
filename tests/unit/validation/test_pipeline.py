"""Unit tests for the validation-pipeline contract and value models."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

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
    ValidationPipelineResult,
    ValidationStageClass,
    ValidationStageId,
    aggregate_pipeline_status,
    execute_validation_pipeline,
)

_NOW: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

_STAGE_CLASSES: Final[Mapping[ValidationStageId, ValidationStageClass]] = MappingProxyType(
    {
        ValidationStageId.SELECT: ValidationStageClass.INVENTORY,
        ValidationStageId.INVENTORY: ValidationStageClass.INVENTORY,
        ValidationStageId.STATIC_SCAN: ValidationStageClass.ANALYSIS,
        ValidationStageId.COMPILE: ValidationStageClass.ANALYSIS,
        ValidationStageId.NORMALIZE_DIAGNOSTICS: ValidationStageClass.ANALYSIS,
        ValidationStageId.CLASSIFY_FAILURES: ValidationStageClass.ANALYSIS,
        ValidationStageId.EXECUTE_SCENARIOS: ValidationStageClass.SCENARIO,
        ValidationStageId.NORMALIZE_SCENARIOS: ValidationStageClass.SCENARIO,
        ValidationStageId.COMPARE_GOLD: ValidationStageClass.SCENARIO,
        ValidationStageId.BUILD_RELEASE_ARTIFACTS: ValidationStageClass.RELEASE,
        ValidationStageId.EVALUATE_RELEASE: ValidationStageClass.RELEASE,
        ValidationStageId.COMPARE_PREVIOUS: ValidationStageClass.FINALIZATION,
    }
)

_MODE_PARTICIPATION: Final[
    Mapping[ValidationMode, Mapping[ValidationStageId, StageParticipation]]
] = MappingProxyType(
    {
        ValidationMode.QUICK: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: StageParticipation.REQUIRED,
                ValidationStageId.NORMALIZE_DIAGNOSTICS: StageParticipation.REQUIRED,
                ValidationStageId.CLASSIFY_FAILURES: StageParticipation.OPTIONAL,
                ValidationStageId.EXECUTE_SCENARIOS: StageParticipation.OPTIONAL,
                ValidationStageId.NORMALIZE_SCENARIOS: StageParticipation.CONDITIONAL,
                ValidationStageId.COMPARE_GOLD: StageParticipation.OPTIONAL,
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: StageParticipation.SKIPPED,
                ValidationStageId.EVALUATE_RELEASE: StageParticipation.SKIPPED,
                ValidationStageId.COMPARE_PREVIOUS: StageParticipation.OPTIONAL,
            }
        ),
        ValidationMode.CHECKPOINT: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: StageParticipation.REQUIRED,
                ValidationStageId.NORMALIZE_DIAGNOSTICS: StageParticipation.REQUIRED,
                ValidationStageId.CLASSIFY_FAILURES: StageParticipation.REQUIRED,
                ValidationStageId.EXECUTE_SCENARIOS: StageParticipation.REQUIRED,
                ValidationStageId.NORMALIZE_SCENARIOS: StageParticipation.REQUIRED,
                ValidationStageId.COMPARE_GOLD: StageParticipation.CONDITIONAL,
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: StageParticipation.OPTIONAL,
                ValidationStageId.EVALUATE_RELEASE: StageParticipation.REQUIRED,
                ValidationStageId.COMPARE_PREVIOUS: StageParticipation.CONDITIONAL,
            }
        ),
        ValidationMode.RELEASE: MappingProxyType(
            {
                stage_id: (
                    StageParticipation.CONDITIONAL
                    if stage_id
                    in {
                        ValidationStageId.COMPARE_GOLD,
                        ValidationStageId.BUILD_RELEASE_ARTIFACTS,
                    }
                    else StageParticipation.REQUIRED
                )
                for stage_id in CANONICAL_STAGE_ORDER
            }
        ),
        ValidationMode.DIAGNOSTIC: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: StageParticipation.CONDITIONAL,
                ValidationStageId.NORMALIZE_DIAGNOSTICS: StageParticipation.CONDITIONAL,
                ValidationStageId.CLASSIFY_FAILURES: StageParticipation.REQUIRED,
                ValidationStageId.EXECUTE_SCENARIOS: StageParticipation.CONDITIONAL,
                ValidationStageId.NORMALIZE_SCENARIOS: StageParticipation.CONDITIONAL,
                ValidationStageId.COMPARE_GOLD: StageParticipation.OPTIONAL,
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: StageParticipation.OPTIONAL,
                ValidationStageId.EVALUATE_RELEASE: StageParticipation.OPTIONAL,
                ValidationStageId.COMPARE_PREVIOUS: StageParticipation.OPTIONAL,
            }
        ),
    }
)


def _stage_result(
    stage_id: ValidationStageId,
    *,
    required: bool = False,
    status: ValidationStatus = ValidationStatus.OK,
    error_kind: ErrorKind | None = None,
    started_at: datetime = _NOW,
    finished_at: datetime = _NOW,
    duration_ms: int = 0,
    execution_state: ExecutionState | None = None,
    message: str = "Stage completed.",
    warnings: tuple[str, ...] = (),
    blocked_by: tuple[ValidationStageId, ...] = (),
    input_count: int = 0,
    output_count: int = 0,
    artifact_paths: tuple[Path, ...] = (),
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
        stage_id=stage_id,
        stage_name=f"Stage {stage_id.value}",
        stage_class=_STAGE_CLASSES[stage_id],
        required=required,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        validation_status=status,
        execution_state=execution_state,
        error_kind=resolved_error_kind,
        message=message,
        warnings=warnings,
        blocked_by=blocked_by,
        input_count=input_count,
        output_count=output_count,
        artifact_paths=artifact_paths,
        payload=payload,
        abort_pipeline=abort_pipeline,
    )


def _executor(
    context: PipelineStageContext,
) -> PipelineStageResult:
    return _stage_result(
        context.stage_id,
        required=context.participation is StageParticipation.REQUIRED,
    )


def _all_executors() -> Mapping[
    ValidationStageId,
    Callable[[PipelineStageContext], PipelineStageResult],
]:
    return dict.fromkeys(CANONICAL_STAGE_ORDER, _executor)


def _focused_plan(
    stage_id: ValidationStageId,
    executor: Callable[[PipelineStageContext], PipelineStageResult] = _executor,
    *,
    participation: StageParticipation = StageParticipation.REQUIRED,
    metadata: Mapping[str, str] | None = None,
) -> ValidationPipelinePlan:
    overrides = dict.fromkeys(CANONICAL_STAGE_ORDER, StageParticipation.SKIPPED)
    overrides[stage_id] = participation
    return ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request={"stage": stage_id.value},
        executors={stage_id: executor},
        participation_overrides=overrides,
        enabled_conditional_stages=(
            frozenset({stage_id})
            if participation is StageParticipation.CONDITIONAL
            else frozenset()
        ),
        metadata={} if metadata is None else metadata,
    )


def _canonical_results() -> tuple[PipelineStageResult, ...]:
    return tuple(_stage_result(stage_id) for stage_id in CANONICAL_STAGE_ORDER)


@pytest.mark.parametrize("mode", tuple(ValidationMode))
def test_mode_matrix_matches_the_normative_pipeline_contract(
    mode: ValidationMode,
) -> None:
    expected = _MODE_PARTICIPATION[mode]
    conditional = frozenset(
        stage_id
        for stage_id, participation in expected.items()
        if participation is StageParticipation.CONDITIONAL
    )
    plan = ValidationPipelinePlan(
        mode=mode,
        request=object(),
        executors=_all_executors(),
        enabled_conditional_stages=conditional,
    )

    assert tuple(plan.participation_for(stage_id) for stage_id in CANONICAL_STAGE_ORDER) == tuple(
        expected[stage_id] for stage_id in CANONICAL_STAGE_ORDER
    )


@pytest.mark.parametrize("mode", tuple(ValidationMode))
def test_disabled_conditional_stages_are_effectively_skipped(
    mode: ValidationMode,
) -> None:
    plan = ValidationPipelinePlan(
        mode=mode,
        request=object(),
        executors=_all_executors(),
    )

    for stage_id, participation in _MODE_PARTICIPATION[mode].items():
        expected = (
            StageParticipation.SKIPPED
            if participation is StageParticipation.CONDITIONAL
            else participation
        )
        assert plan.participation_for(stage_id) is expected


def test_participation_override_is_authoritative_and_conditional_is_bounded() -> None:
    stage_id = ValidationStageId.BUILD_RELEASE_ARTIFACTS
    plan = ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request=object(),
        executors=_all_executors(),
        participation_overrides={stage_id: StageParticipation.CONDITIONAL},
    )

    assert plan.participation_for(stage_id) is StageParticipation.SKIPPED

    enabled = ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request=object(),
        executors=_all_executors(),
        participation_overrides={stage_id: StageParticipation.CONDITIONAL},
        enabled_conditional_stages=frozenset({stage_id}),
    )

    assert enabled.participation_for(stage_id) is StageParticipation.CONDITIONAL


def test_required_override_requires_an_executor() -> None:
    with pytest.raises(
        ValueError,
        match=r"required stage VAL-190 has no executor",
    ):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors=dict.fromkeys((ValidationStageId.SELECT, ValidationStageId.INVENTORY, ValidationStageId.STATIC_SCAN, ValidationStageId.COMPILE, ValidationStageId.NORMALIZE_DIAGNOSTICS), _executor),
            participation_overrides={
                ValidationStageId.COMPARE_PREVIOUS: StageParticipation.REQUIRED
            },
        )


def test_plan_copies_and_freezes_mappings_and_sorts_metadata() -> None:
    executors = dict(_all_executors())
    overrides: dict[ValidationStageId, StageParticipation] = {}
    metadata = {"zeta": "last", "alpha": "first"}
    plan = ValidationPipelinePlan(
        mode=ValidationMode.RELEASE,
        request=object(),
        executors=executors,
        participation_overrides=overrides,
        enabled_conditional_stages=frozenset(CANONICAL_STAGE_ORDER),
        metadata=metadata,
    )

    executors.clear()
    overrides[ValidationStageId.SELECT] = StageParticipation.SKIPPED
    metadata["alpha"] = "changed"

    assert tuple(plan.executors) == CANONICAL_STAGE_ORDER
    assert plan.participation_for(ValidationStageId.SELECT) is StageParticipation.REQUIRED
    assert tuple(plan.metadata.items()) == (("alpha", "first"), ("zeta", "last"))
    with pytest.raises(TypeError):
        plan.metadata["new"] = "value"  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("executors", [], "executors must be a mapping"),
        ("guards", [], "guards must be a mapping"),
        (
            "participation_overrides",
            [],
            "participation_overrides must be a mapping",
        ),
    ],
)
def test_plan_rejects_non_mapping_configuration(
    field: str,
    value: object,
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "mode": ValidationMode.QUICK,
        "request": object(),
        "executors": _all_executors(),
    }
    arguments[field] = value

    with pytest.raises(TypeError, match=message):
        ValidationPipelinePlan(**arguments)  # type: ignore[arg-type]


def test_plan_rejects_wrong_mapping_key_and_value_types() -> None:
    with pytest.raises(TypeError, match="executor keys must be ValidationStageId"):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors={"VAL-080": _executor},  # type: ignore[dict-item]
        )

    with pytest.raises(TypeError, match="must be callable"):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors={ValidationStageId.SELECT: object()},  # type: ignore[dict-item]
        )

    with pytest.raises(TypeError, match="participation values"):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors=_all_executors(),
            participation_overrides={
                ValidationStageId.SELECT: "required"  # type: ignore[dict-item]
            },
        )


def test_stage_result_normalizes_datetimes_and_preserves_structured_evidence() -> None:
    east = timezone(timedelta(hours=2))
    started = datetime(2026, 7, 25, 14, 0, tzinfo=east)
    finished = datetime(2026, 7, 25, 14, 0, 1, tzinfo=east)
    payload = {"subject": "Main.gf"}

    result = _stage_result(
        ValidationStageId.COMPILE,
        required=True,
        started_at=started,
        finished_at=finished,
        duration_ms=1000,
        execution_state=ExecutionState.COMPLETED,
        warnings=("Compiler warning.",),
        input_count=1,
        output_count=2,
        artifact_paths=(Path("raw/compile.stdout.txt"), Path("raw/compile.stderr.txt")),
        payload=payload,
    )

    assert result.started_at == _NOW
    assert result.finished_at == _NOW + timedelta(seconds=1)
    assert result.warnings == ("Compiler warning.",)
    assert result.input_count == 1
    assert result.output_count == 2
    assert result.artifact_paths == (
        Path("raw/compile.stdout.txt"),
        Path("raw/compile.stderr.txt"),
    )
    assert result.payload is payload


@pytest.mark.parametrize(
    ("changes", "error", "message"),
    [
        ({"started_at": datetime(2026, 7, 25, 12, 0)}, ValueError, "timezone-aware"),
        ({"finished_at": _NOW - timedelta(seconds=1)}, ValueError, "must not precede"),
        ({"duration_ms": -1}, ValueError, "must be non-negative"),
        ({"input_count": True}, TypeError, "must be an integer"),
        ({"output_count": -1}, ValueError, "must be non-negative"),
        ({"message": " stage "}, ValueError, "outer whitespace"),
        ({"warnings": ("",)}, ValueError, "must not be empty"),
        (
            {
                "blocked_by": (
                    ValidationStageId.SELECT,
                    ValidationStageId.SELECT,
                )
            },
            ValueError,
            "must not contain duplicates",
        ),
        ({"artifact_paths": (Path("bad\x00path"),)}, ValueError, "NUL"),
    ],
)
def test_stage_result_rejects_invalid_structured_fields(
    changes: Mapping[str, object],
    error: type[Exception],
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "stage_id": ValidationStageId.STATIC_SCAN,
        "stage_name": "Static scan",
        "stage_class": ValidationStageClass.ANALYSIS,
        "required": True,
        "started_at": _NOW,
        "finished_at": _NOW,
        "duration_ms": 0,
        "validation_status": ValidationStatus.OK,
        "execution_state": None,
        "error_kind": ErrorKind.OK,
        "message": "Completed.",
    }
    arguments.update(changes)

    with pytest.raises(error, match=message):
        PipelineStageResult(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("status", "execution_state", "error_kind", "message"),
    [
        (
            ValidationStatus.OK,
            None,
            ErrorKind.INTERNAL,
            "OK or SKIPPED stage results require ErrorKind.OK",
        ),
        (
            ValidationStatus.SKIPPED,
            None,
            ErrorKind.IO,
            "OK or SKIPPED stage results require ErrorKind.OK",
        ),
        (
            ValidationStatus.FAIL,
            ExecutionState.COMPLETED,
            ErrorKind.OK,
            "FAIL or ERROR stage results require a non-OK error kind",
        ),
        (
            ValidationStatus.ERROR,
            ExecutionState.LAUNCH_FAILED,
            ErrorKind.OK,
            "FAIL or ERROR stage results require a non-OK error kind",
        ),
        (
            ValidationStatus.SKIPPED,
            ExecutionState.CANCELLED,
            ErrorKind.OK,
            "SKIPPED stage results cannot have execution_state",
        ),
    ],
)
def test_stage_result_enforces_status_dimension_consistency(
    status: ValidationStatus,
    execution_state: ExecutionState | None,
    error_kind: ErrorKind,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _stage_result(
            ValidationStageId.COMPILE,
            status=status,
            execution_state=execution_state,
            error_kind=error_kind,
        )


def test_stage_context_copies_previous_results_and_metadata() -> None:
    previous = {ValidationStageId.SELECT: _stage_result(ValidationStageId.SELECT, required=True)}
    metadata = {"zeta": "2", "alpha": "1"}
    context = PipelineStageContext(
        mode=ValidationMode.QUICK,
        stage_id=ValidationStageId.INVENTORY,
        participation=StageParticipation.REQUIRED,
        request=object(),
        previous_results=previous,
        metadata=metadata,
    )

    previous.clear()
    metadata["alpha"] = "changed"

    assert tuple(context.previous_results) == (ValidationStageId.SELECT,)
    assert tuple(context.metadata.items()) == (("alpha", "1"), ("zeta", "2"))
    with pytest.raises(TypeError):
        context.previous_results[ValidationStageId.INVENTORY] = _stage_result(  # type: ignore[index]
            ValidationStageId.INVENTORY
        )


def test_stage_context_rejects_mismatched_previous_result_key() -> None:
    with pytest.raises(
        ValueError,
        match="previous_results key does not match result stage_id",
    ):
        PipelineStageContext(
            mode=ValidationMode.QUICK,
            stage_id=ValidationStageId.INVENTORY,
            participation=StageParticipation.REQUIRED,
            request=object(),
            previous_results={ValidationStageId.SELECT: _stage_result(ValidationStageId.INVENTORY)},
            metadata={},
        )


def test_pipeline_result_requires_canonical_complete_order() -> None:
    with pytest.raises(ValueError, match="canonical stage order"):
        ValidationPipelineResult(
            mode=ValidationMode.QUICK,
            stage_results=_canonical_results()[:-1],
            overall_status=OverallStatus.OK,
            cancelled=False,
            cancellation_reason=None,
        )

    reversed_results = tuple(reversed(_canonical_results()))
    with pytest.raises(ValueError, match="canonical stage order"):
        ValidationPipelineResult(
            mode=ValidationMode.QUICK,
            stage_results=reversed_results,
            overall_status=OverallStatus.OK,
            cancelled=False,
            cancellation_reason=None,
        )


def test_pipeline_result_enforces_cancellation_consistency_and_lookup() -> None:
    results = _canonical_results()
    pipeline = ValidationPipelineResult(
        mode=ValidationMode.DIAGNOSTIC,
        stage_results=results,
        overall_status=OverallStatus.OK,
        cancelled=True,
        cancellation_reason="Operator requested cancellation.",
    )

    assert pipeline.result_for(ValidationStageId.COMPILE) is results[3]

    with pytest.raises(ValueError, match="must agree with cancellation_reason"):
        ValidationPipelineResult(
            mode=ValidationMode.DIAGNOSTIC,
            stage_results=results,
            overall_status=OverallStatus.OK,
            cancelled=False,
            cancellation_reason="Unexpected reason.",
        )

    with pytest.raises(ValueError, match="must agree with cancellation_reason"):
        ValidationPipelineResult(
            mode=ValidationMode.DIAGNOSTIC,
            stage_results=results,
            overall_status=OverallStatus.OK,
            cancelled=True,
            cancellation_reason=None,
        )


def test_execute_pipeline_passes_request_metadata_and_prior_results() -> None:
    observed: list[
        tuple[ValidationStageId, object, tuple[ValidationStageId, ...], Mapping[str, str]]
    ] = []
    request = {"target": "Main.gf"}

    def executor(context: PipelineStageContext) -> PipelineStageResult:
        observed.append(
            (
                context.stage_id,
                context.request,
                tuple(context.previous_results),
                context.metadata,
            )
        )
        return _stage_result(context.stage_id, required=True)

    overrides = dict.fromkeys(CANONICAL_STAGE_ORDER, StageParticipation.SKIPPED)
    overrides[ValidationStageId.SELECT] = StageParticipation.REQUIRED
    overrides[ValidationStageId.INVENTORY] = StageParticipation.REQUIRED
    plan = ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request=request,
        executors={
            ValidationStageId.SELECT: executor,
            ValidationStageId.INVENTORY: executor,
        },
        participation_overrides=overrides,
        metadata={"run_id": "run_20260725_120000"},
    )

    result = execute_validation_pipeline(
        plan,
        utc_now=lambda: _NOW,
        monotonic_now=lambda: 10.0,
    )

    assert observed == [
        (
            ValidationStageId.SELECT,
            request,
            (),
            {"run_id": "run_20260725_120000"},
        ),
        (
            ValidationStageId.INVENTORY,
            request,
            (ValidationStageId.SELECT,),
            {"run_id": "run_20260725_120000"},
        ),
    ]
    assert tuple(item.stage_id for item in result.stage_results) == CANONICAL_STAGE_ORDER


@dataclass(slots=True)
class _ValueSequence:
    values: list[float]

    def __call__(self) -> float:
        return self.values.pop(0)


def test_executor_exception_is_bounded_with_type_message_and_duration() -> None:
    stage_id = ValidationStageId.SELECT

    def fail(_context: PipelineStageContext) -> PipelineStageResult:
        raise RuntimeError("selection failed")

    plan = _focused_plan(stage_id, fail)
    result = execute_validation_pipeline(
        plan,
        utc_now=lambda: _NOW,
        monotonic_now=_ValueSequence([10.0, 10.126]),
    ).result_for(stage_id)

    assert result.validation_status is ValidationStatus.ERROR
    assert result.error_kind is ErrorKind.INTERNAL
    assert result.message == "RuntimeError: selection failed"
    assert result.duration_ms == 126
    assert result.required is True


def test_executor_exception_without_text_uses_exception_type() -> None:
    stage_id = ValidationStageId.SELECT

    def fail(_context: PipelineStageContext) -> PipelineStageResult:
        raise RuntimeError

    result = execute_validation_pipeline(
        _focused_plan(stage_id, fail),
        utc_now=lambda: _NOW,
        monotonic_now=_ValueSequence([1.0, 1.0]),
    ).result_for(stage_id)

    assert result.message == "RuntimeError"


@pytest.mark.parametrize(
    ("utc_now", "monotonic_now", "error", "message"),
    [
        (
            lambda: datetime(2026, 7, 25, 12, 0),
            lambda: 1.0,
            ValueError,
            "timezone-aware",
        ),
        (
            lambda: _NOW,
            lambda: float("nan"),
            ValueError,
            "must be finite",
        ),
    ],
)
def test_execute_pipeline_validates_clock_outputs(
    utc_now: Callable[[], datetime],
    monotonic_now: Callable[[], float],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        execute_validation_pipeline(
            _focused_plan(ValidationStageId.SELECT),
            utc_now=utc_now,
            monotonic_now=monotonic_now,
        )


def test_execute_pipeline_rejects_backwards_monotonic_clock_on_exception() -> None:
    def fail(_context: PipelineStageContext) -> PipelineStageResult:
        raise OSError("disk failure")

    with pytest.raises(ValueError, match="monotonic clock moved backwards"):
        execute_validation_pipeline(
            _focused_plan(ValidationStageId.SELECT, fail),
            utc_now=lambda: _NOW,
            monotonic_now=_ValueSequence([5.0, 4.0]),
        )


def test_optional_error_does_not_block_required_dependent_but_is_overall_error() -> None:
    calls: list[ValidationStageId] = []

    def optional_error(context: PipelineStageContext) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _stage_result(
            context.stage_id,
            required=False,
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.IO,
            message="Inventory evidence unavailable.",
        )

    def compile_ok(context: PipelineStageContext) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _stage_result(context.stage_id, required=True)

    overrides = dict.fromkeys(CANONICAL_STAGE_ORDER, StageParticipation.SKIPPED)
    overrides[ValidationStageId.INVENTORY] = StageParticipation.OPTIONAL
    overrides[ValidationStageId.COMPILE] = StageParticipation.REQUIRED
    plan = ValidationPipelinePlan(
        mode=ValidationMode.QUICK,
        request=object(),
        executors={
            ValidationStageId.INVENTORY: optional_error,
            ValidationStageId.COMPILE: compile_ok,
        },
        participation_overrides=overrides,
    )

    result = execute_validation_pipeline(
        plan,
        utc_now=lambda: _NOW,
        monotonic_now=lambda: 1.0,
    )

    assert calls == [ValidationStageId.INVENTORY, ValidationStageId.COMPILE]
    assert result.result_for(ValidationStageId.COMPILE).validation_status is ValidationStatus.OK
    assert result.overall_status is OverallStatus.ERROR


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ((), OverallStatus.OK),
        (
            (
                _stage_result(
                    ValidationStageId.SELECT,
                    required=False,
                    status=ValidationStatus.FAIL,
                ),
            ),
            OverallStatus.OK,
        ),
        (
            (
                _stage_result(
                    ValidationStageId.SELECT,
                    required=True,
                    status=ValidationStatus.SKIPPED,
                ),
            ),
            OverallStatus.FAIL,
        ),
        (
            (
                _stage_result(
                    ValidationStageId.SELECT,
                    required=False,
                    status=ValidationStatus.ERROR,
                ),
            ),
            OverallStatus.ERROR,
        ),
    ],
)
def test_aggregate_pipeline_status_contract(
    results: tuple[PipelineStageResult, ...],
    expected: OverallStatus,
) -> None:
    assert aggregate_pipeline_status(results) is expected


def test_aggregate_pipeline_status_rejects_non_results() -> None:
    with pytest.raises(TypeError, match="must contain PipelineStageResult"):
        aggregate_pipeline_status(
            cast(
                "Sequence[PipelineStageResult]",
                (_stage_result(ValidationStageId.SELECT), object()),
            )
        )


def test_execute_pipeline_rejects_invalid_public_arguments() -> None:
    plan = _focused_plan(ValidationStageId.SELECT)

    with pytest.raises(TypeError, match="plan must be a ValidationPipelinePlan"):
        execute_validation_pipeline(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must implement CancellationSource"):
        execute_validation_pipeline(plan, cancellation_source=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="utc_now must be callable"):
        execute_validation_pipeline(plan, utc_now=None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="monotonic_now must be callable"):
        execute_validation_pipeline(plan, monotonic_now=None)  # type: ignore[arg-type]
