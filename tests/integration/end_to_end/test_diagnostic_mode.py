from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

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
    execute_validation_pipeline,
)

_TIMESTAMP: Final = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

_STAGE_CLASSES: Final = {
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


def _stage_result(
    context: PipelineStageContext,
    *,
    status: ValidationStatus = ValidationStatus.OK,
    error_kind: ErrorKind = ErrorKind.OK,
    execution_state: ExecutionState | None = None,
    message: str = "stage completed",
    artifact_paths: tuple[Path, ...] = (),
) -> PipelineStageResult:
    return PipelineStageResult(
        stage_id=context.stage_id,
        stage_name=context.stage_id.name,
        stage_class=_STAGE_CLASSES[context.stage_id],
        required=context.participation is StageParticipation.REQUIRED,
        started_at=_TIMESTAMP,
        finished_at=_TIMESTAMP,
        duration_ms=0,
        validation_status=status,
        execution_state=execution_state,
        error_kind=error_kind,
        message=message,
        artifact_paths=artifact_paths,
    )


def _successful_executor(
    calls: list[ValidationStageId],
    *,
    artifact: Path | None = None,
) -> Callable[[PipelineStageContext], PipelineStageResult]:
    def execute(context: PipelineStageContext) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _stage_result(
            context,
            artifact_paths=() if artifact is None else (artifact,),
        )

    return execute


def test_diagnostic_mode_runs_broad_evidence_pipeline_after_language_failure(
    tmp_path: Path,
) -> None:
    calls: list[ValidationStageId] = []
    raw_log = tmp_path / "raw" / "compile.stderr.log"

    def static_scan(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _stage_result(
            context,
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.SYNTAX,
            message="deterministic source defect",
        )

    executors = {
        ValidationStageId.SELECT: _successful_executor(calls),
        ValidationStageId.INVENTORY: _successful_executor(calls),
        ValidationStageId.STATIC_SCAN: static_scan,
        ValidationStageId.COMPILE: _successful_executor(
            calls,
            artifact=raw_log,
        ),
        ValidationStageId.NORMALIZE_DIAGNOSTICS: _successful_executor(calls),
        ValidationStageId.CLASSIFY_FAILURES: _successful_executor(calls),
        ValidationStageId.EXECUTE_SCENARIOS: _successful_executor(calls),
        ValidationStageId.NORMALIZE_SCENARIOS: _successful_executor(calls),
        ValidationStageId.COMPARE_GOLD: _successful_executor(calls),
    }
    enabled = frozenset(
        {
            ValidationStageId.COMPILE,
            ValidationStageId.NORMALIZE_DIAGNOSTICS,
            ValidationStageId.EXECUTE_SCENARIOS,
            ValidationStageId.NORMALIZE_SCENARIOS,
        }
    )

    result = execute_validation_pipeline(
        ValidationPipelinePlan(
            mode=ValidationMode.DIAGNOSTIC,
            request={"mode": "diagnostic"},
            executors=executors,
            enabled_conditional_stages=enabled,
            metadata={"evidence_policy": "expanded"},
        ),
        utc_now=lambda: _TIMESTAMP,
        monotonic_now=lambda: 1.0,
    )

    assert result.mode is ValidationMode.DIAGNOSTIC
    assert result.overall_status is OverallStatus.FAIL
    assert result.cancelled is False
    assert tuple(item.stage_id for item in result.stage_results) == (CANONICAL_STAGE_ORDER)
    assert calls == [
        ValidationStageId.SELECT,
        ValidationStageId.INVENTORY,
        ValidationStageId.STATIC_SCAN,
        ValidationStageId.COMPILE,
        ValidationStageId.NORMALIZE_DIAGNOSTICS,
        ValidationStageId.CLASSIFY_FAILURES,
        ValidationStageId.EXECUTE_SCENARIOS,
        ValidationStageId.NORMALIZE_SCENARIOS,
        ValidationStageId.COMPARE_GOLD,
    ]

    scan = result.result_for(ValidationStageId.STATIC_SCAN)
    compile_result = result.result_for(ValidationStageId.COMPILE)
    scenario_result = result.result_for(ValidationStageId.EXECUTE_SCENARIOS)

    assert scan.validation_status is ValidationStatus.FAIL
    assert scan.error_kind is ErrorKind.SYNTAX
    assert compile_result.validation_status is ValidationStatus.OK
    assert compile_result.artifact_paths == (raw_log,)
    assert scenario_result.validation_status is ValidationStatus.OK

    for stage_id in (
        ValidationStageId.BUILD_RELEASE_ARTIFACTS,
        ValidationStageId.EVALUATE_RELEASE,
        ValidationStageId.COMPARE_PREVIOUS,
    ):
        stage = result.result_for(stage_id)
        assert stage.required is False
        assert stage.validation_status is ValidationStatus.SKIPPED


def test_diagnostic_scan_only_marks_compile_stages_skipped() -> None:
    calls: list[ValidationStageId] = []
    executors = {
        ValidationStageId.SELECT: _successful_executor(calls),
        ValidationStageId.INVENTORY: _successful_executor(calls),
        ValidationStageId.STATIC_SCAN: _successful_executor(calls),
        ValidationStageId.CLASSIFY_FAILURES: _successful_executor(calls),
    }

    result = execute_validation_pipeline(
        ValidationPipelinePlan(
            mode=ValidationMode.DIAGNOSTIC,
            request={"mode": "diagnostic", "no_compile": True},
            executors=executors,
        ),
        utc_now=lambda: _TIMESTAMP,
        monotonic_now=lambda: 1.0,
    )

    assert result.overall_status is OverallStatus.OK
    assert calls == [
        ValidationStageId.SELECT,
        ValidationStageId.INVENTORY,
        ValidationStageId.STATIC_SCAN,
        ValidationStageId.CLASSIFY_FAILURES,
    ]

    for stage_id in (
        ValidationStageId.COMPILE,
        ValidationStageId.NORMALIZE_DIAGNOSTICS,
    ):
        stage = result.result_for(stage_id)
        assert stage.required is False
        assert stage.validation_status is ValidationStatus.SKIPPED
        assert stage.execution_state is None
        assert stage.error_kind is ErrorKind.OK


def test_diagnostic_timeout_remains_error_while_classification_continues() -> None:
    calls: list[ValidationStageId] = []

    def timed_out_compile(
        context: PipelineStageContext,
    ) -> PipelineStageResult:
        calls.append(context.stage_id)
        return _stage_result(
            context,
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.TIMEOUT,
            execution_state=ExecutionState.TIMED_OUT,
            message="finite diagnostic timeout reached",
        )

    executors = {
        ValidationStageId.SELECT: _successful_executor(calls),
        ValidationStageId.INVENTORY: _successful_executor(calls),
        ValidationStageId.STATIC_SCAN: _successful_executor(calls),
        ValidationStageId.COMPILE: timed_out_compile,
        ValidationStageId.NORMALIZE_DIAGNOSTICS: _successful_executor(calls),
        ValidationStageId.CLASSIFY_FAILURES: _successful_executor(calls),
    }

    result = execute_validation_pipeline(
        ValidationPipelinePlan(
            mode=ValidationMode.DIAGNOSTIC,
            request={"mode": "diagnostic", "timeout_sec": 30},
            executors=executors,
            enabled_conditional_stages=frozenset(
                {
                    ValidationStageId.COMPILE,
                    ValidationStageId.NORMALIZE_DIAGNOSTICS,
                }
            ),
        ),
        utc_now=lambda: _TIMESTAMP,
        monotonic_now=lambda: 1.0,
    )

    compile_result = result.result_for(ValidationStageId.COMPILE)
    classification = result.result_for(ValidationStageId.CLASSIFY_FAILURES)

    assert result.overall_status is OverallStatus.ERROR
    assert compile_result.validation_status is ValidationStatus.ERROR
    assert compile_result.execution_state is ExecutionState.TIMED_OUT
    assert compile_result.error_kind is ErrorKind.TIMEOUT
    assert classification.validation_status is ValidationStatus.OK
    assert ValidationStageId.CLASSIFY_FAILURES in calls
