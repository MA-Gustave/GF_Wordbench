"""Unit tests for dependency-aware run-stage execution."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType, SimpleNamespace
from typing import Iterator

import pytest

from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.runs.planner import (
    PlannedStage,
    RunPlan,
    StageId,
    StageRequirement,
)
from gf_wordbench.runs.stage_executor import (
    StageExecutionAborted,
    StageExecutionRecord,
    StageExecutionReport,
    StageInvocation,
    execute_plan,
    execute_stage,
)


@dataclass(frozen=True, slots=True)
class _Result:
    status: ValidationStatus = ValidationStatus.OK
    duration_ms: int = 7
    error_kind: ErrorKind = ErrorKind.OK
    primary_message: str = ""
    error_detail: str = ""
    evidence_paths: tuple[str, ...] = ()
    blocks_dependents: bool = False
    evidence_trustworthy: bool = True
    abort_run: bool = False


def _stage(
    stage_id: StageId,
    *,
    requirement: StageRequirement = StageRequirement.REQUIRED,
    prerequisites: tuple[StageId, ...] = (),
    timeout_sec: int | None = None,
    reason: str | None = None,
) -> PlannedStage:
    return PlannedStage(
        stage_id=stage_id,
        requirement=requirement,
        prerequisites=prerequisites,
        timeout_sec=timeout_sec,
        reason=reason,
    )


def _plan(*stages: PlannedStage) -> RunPlan:
    return RunPlan(
        mode=ValidationMode.DIAGNOSTIC,
        target=None,
        stages=tuple(stages),
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        compare_previous=False,
        build_pgf=False,
        evidence_level="standard",
        release_eligible=False,
    )


def _record(
    stage_id: StageId,
    *,
    requirement: StageRequirement = StageRequirement.REQUIRED,
    status: ValidationStatus = ValidationStatus.OK,
    error_kind: ErrorKind = ErrorKind.OK,
    message: str = "",
    blocks_dependents: bool = False,
    evidence_trustworthy: bool = True,
    abort_run: bool = False,
) -> StageExecutionRecord:
    return StageExecutionRecord(
        stage_id=stage_id,
        requirement=requirement,
        status=status,
        duration_ms=3,
        error_kind=error_kind,
        primary_message=message,
        error_detail="",
        evidence_paths=(),
        blocks_dependents=blocks_dependents,
        evidence_trustworthy=evidence_trustworthy,
        abort_run=abort_run,
    )


def _clock(*values: int):
    iterator: Iterator[int] = iter(values)
    return lambda: next(iterator)


def test_execute_stage_passes_an_immutable_invocation_snapshot() -> None:
    stage = _stage(StageId.STATIC_SCAN, timeout_sec=20)
    prior = _record(StageId.SELECTION)
    observed: list[StageInvocation] = []

    def handler(invocation: StageInvocation) -> _Result:
        observed.append(invocation)
        assert invocation.stage is stage
        assert invocation.timeout_seconds == 4.5
        assert invocation.finalizing is False
        assert invocation.prior_records == {StageId.SELECTION: prior}
        with pytest.raises(TypeError):
            invocation.prior_records[StageId.CONFIGURATION] = prior  # type: ignore[index]
        return _Result(
            duration_ms=12,
            evidence_paths=("raw/static-scan.jsonl",),
        )

    record = execute_stage(
        stage,
        handler,
        prior_records={StageId.SELECTION: prior},
        timeout_seconds=4.5,
        clock_ns=_clock(1_000_000, 9_000_000),
    )

    assert len(observed) == 1
    assert record.stage_id is StageId.STATIC_SCAN
    assert record.status is ValidationStatus.OK
    assert record.duration_ms == 12
    assert record.evidence_paths == ("raw/static-scan.jsonl",)
    assert record.payload == _Result(
        duration_ms=12,
        evidence_paths=("raw/static-scan.jsonl",),
    )


def test_execute_stage_uses_measured_duration_when_result_omits_it() -> None:
    stage = _stage(StageId.FINGERPRINT)
    result = SimpleNamespace(
        status=ValidationStatus.OK,
        error_kind=ErrorKind.OK,
        primary_message="",
        evidence_paths=(),
    )

    record = execute_stage(
        stage,
        lambda invocation: result,
        clock_ns=_clock(2_000_000, 13_900_000),
    )

    assert record.duration_ms == 11
    assert record.payload is result


def test_execute_stage_returns_planned_skip_without_calling_handler() -> None:
    stage = _stage(
        StageId.COMPARE_PREVIOUS,
        requirement=StageRequirement.SKIPPED,
        reason="previous-run comparison is disabled",
    )
    called = False

    def handler(invocation: StageInvocation) -> _Result:
        nonlocal called
        called = True
        return _Result()

    record = execute_stage(stage, handler)

    assert called is False
    assert record.status is ValidationStatus.SKIPPED
    assert record.primary_message == "previous-run comparison is disabled"
    assert record.error_kind is ErrorKind.OK
    assert record.blocks_dependents is True


def test_execute_stage_rejects_unstructured_or_inconsistent_results() -> None:
    stage = _stage(StageId.CONFIGURATION)

    with pytest.raises(TypeError, match="returned None"):
        execute_stage(stage, lambda invocation: None)

    with pytest.raises(TypeError, match="status"):
        execute_stage(
            stage,
            lambda invocation: SimpleNamespace(
                status="OK",
                error_kind=ErrorKind.OK,
                primary_message="",
                evidence_paths=(),
            ),
        )

    with pytest.raises(ValueError, match="non-OK error kind"):
        execute_stage(
            stage,
            lambda invocation: _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.OK,
                primary_message="configuration failed",
            ),
        )


def test_execute_plan_runs_enabled_stages_in_plan_order() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(
            StageId.ENVIRONMENT,
            prerequisites=(StageId.CONFIGURATION,),
        ),
        _stage(
            StageId.VERSION_PROBE,
            requirement=StageRequirement.SKIPPED,
            reason="version probe disabled",
        ),
    )
    calls: list[StageId] = []
    sink: list[StageExecutionRecord] = []

    def handler(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        return _Result()

    report = execute_plan(
        plan,
        {
            StageId.CONFIGURATION: handler,
            StageId.ENVIRONMENT: handler,
        },
        record_sink=sink.append,
    )

    assert calls == [StageId.CONFIGURATION, StageId.ENVIRONMENT]
    assert tuple(record.stage_id for record in report.records) == (
        StageId.CONFIGURATION,
        StageId.ENVIRONMENT,
        StageId.VERSION_PROBE,
    )
    assert sink == list(report.records)
    assert report.aborted is False
    assert report.required_status is ValidationStatus.OK


def test_blocked_dependents_are_skipped_but_independent_work_continues() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(
            StageId.ENVIRONMENT,
            prerequisites=(StageId.CONFIGURATION,),
        ),
        _stage(StageId.SELECTION),
    )
    calls: list[StageId] = []

    def configuration(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        return _Result(
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.CONFIG,
            primary_message="configuration is invalid",
            blocks_dependents=True,
        )

    def success(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        return _Result()

    report = execute_plan(
        plan,
        {
            StageId.CONFIGURATION: configuration,
            StageId.ENVIRONMENT: success,
            StageId.SELECTION: success,
        },
    )

    assert calls == [StageId.CONFIGURATION, StageId.SELECTION]
    blocked = report.record(StageId.ENVIRONMENT)
    assert blocked.status is ValidationStatus.SKIPPED
    assert blocked.primary_message == (
        "blocked by unavailable prerequisites: configuration"
    )
    assert report.record(StageId.SELECTION).status is ValidationStatus.OK
    assert report.aborted is False


def test_nonblocking_failure_does_not_prevent_a_dependent_stage() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(
            StageId.ENVIRONMENT,
            prerequisites=(StageId.CONFIGURATION,),
        ),
    )
    calls: list[StageId] = []

    report = execute_plan(
        plan,
        {
            StageId.CONFIGURATION: lambda invocation: _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.CONFIG,
                primary_message="non-blocking policy failure",
            ),
            StageId.ENVIRONMENT: lambda invocation: (
                calls.append(invocation.stage.stage_id) or _Result()
            ),
        },
    )

    assert calls == [StageId.ENVIRONMENT]
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.OK
    assert report.required_status is ValidationStatus.FAIL


def test_fail_fast_skips_remaining_required_work_but_runs_finalization() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
        _stage(StageId.WRITE_REPORTS),
        _stage(
            StageId.WRITE_MANIFEST,
            prerequisites=(StageId.WRITE_REPORTS,),
        ),
    )
    calls: list[StageId] = []

    def handler(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        if invocation.stage.stage_id is StageId.CONFIGURATION:
            return _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.CONFIG,
                primary_message="invalid configuration",
            )
        return _Result()

    report = execute_plan(
        plan,
        {stage.stage_id: handler for stage in plan.stages},
        fail_fast=True,
    )

    assert calls == [
        StageId.CONFIGURATION,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    ]
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED
    assert "fail-fast" in report.record(StageId.ENVIRONMENT).primary_message
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert report.record(StageId.WRITE_MANIFEST).status is ValidationStatus.OK
    assert report.aborted is True
    assert report.abort_reason == (
        "fail-fast stopped execution after configuration"
    )


def test_fail_fast_does_not_abort_after_an_optional_failure() -> None:
    plan = _plan(
        _stage(
            StageId.VERSION_PROBE,
            requirement=StageRequirement.OPTIONAL,
        ),
        _stage(StageId.SELECTION),
    )

    report = execute_plan(
        plan,
        {
            StageId.VERSION_PROBE: lambda invocation: _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.TOOL,
                primary_message="optional probe failed",
            ),
            StageId.SELECTION: lambda invocation: _Result(),
        },
        fail_fast=True,
    )

    assert report.aborted is False
    assert report.record(StageId.SELECTION).status is ValidationStatus.OK


def test_pre_stage_cancellation_stops_normal_work_and_preserves_finalization() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
        _stage(StageId.WRITE_REPORTS),
        _stage(StageId.WRITE_MANIFEST),
    )
    calls: list[StageId] = []

    def handler(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        return _Result()

    report = execute_plan(
        plan,
        {stage.stage_id: handler for stage in plan.stages},
        cancellation_requested=lambda: True,
        cancellation_reason=lambda: "cancelled by operator",
    )

    assert calls == [StageId.WRITE_REPORTS, StageId.WRITE_MANIFEST]
    assert report.record(StageId.CONFIGURATION).status is ValidationStatus.SKIPPED
    assert report.record(StageId.CONFIGURATION).primary_message == (
        "cancelled by operator"
    )
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert report.aborted is True
    assert report.abort_reason == "cancelled by operator"


def test_handler_cancellation_becomes_structured_error_and_finalizes() -> None:
    plan = _plan(
        _stage(StageId.RUN_SCENARIOS),
        _stage(StageId.NORMALIZE_OUTPUTS),
        _stage(StageId.WRITE_REPORTS),
    )
    calls: list[StageId] = []

    def scenarios(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        raise CancellationRequested(
            "scenario execution cancelled",
            detail="termination acknowledged",
            evidence_paths=("raw/scenario.stderr.bin",),
        )

    def success(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        return _Result()

    report = execute_plan(
        plan,
        {
            StageId.RUN_SCENARIOS: scenarios,
            StageId.NORMALIZE_OUTPUTS: success,
            StageId.WRITE_REPORTS: success,
        },
        clock_ns=_clock(0, 2_500_000, 3_000_000, 4_000_000),
    )

    cancelled = report.record(StageId.RUN_SCENARIOS)
    assert cancelled.status is ValidationStatus.ERROR
    assert cancelled.error_kind is ErrorKind.OTHER
    assert cancelled.duration_ms == 2
    assert cancelled.primary_message == "scenario execution cancelled"
    assert cancelled.error_detail == "termination acknowledged"
    assert cancelled.evidence_paths == ("raw/scenario.stderr.bin",)
    assert cancelled.abort_run is True
    assert cancelled.evidence_trustworthy is False
    assert report.record(StageId.NORMALIZE_OUTPUTS).status is ValidationStatus.SKIPPED
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert calls == [StageId.RUN_SCENARIOS, StageId.WRITE_REPORTS]


def test_unexpected_stage_exception_raises_after_independent_finalization() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
        _stage(StageId.WRITE_REPORTS),
        _stage(StageId.WRITE_MANIFEST),
    )
    calls: list[StageId] = []

    def handler(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        if invocation.stage.stage_id is StageId.CONFIGURATION:
            raise RuntimeError("sensitive internal failure\nsecond line")
        return _Result()

    with pytest.raises(StageExecutionAborted) as raised:
        execute_plan(
            plan,
            {stage.stage_id: handler for stage in plan.stages},
            clock_ns=_clock(0, 1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000),
        )

    error = raised.value
    assert error.failed_stage is StageId.CONFIGURATION
    assert isinstance(error.cause, RuntimeError)
    assert error.__cause__ is error.cause
    assert error.report.aborted is True
    assert error.report.fatal_stage is StageId.CONFIGURATION
    assert error.report.record(StageId.CONFIGURATION).status is ValidationStatus.ERROR
    assert error.report.record(StageId.CONFIGURATION).error_kind is ErrorKind.INTERNAL
    assert error.report.record(StageId.CONFIGURATION).error_detail == (
        "RuntimeError: sensitive internal failure\\nsecond line"
    )
    assert error.report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED
    assert error.report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert error.report.record(StageId.WRITE_MANIFEST).status is ValidationStatus.OK
    assert calls == [
        StageId.CONFIGURATION,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    ]


def test_missing_handler_is_a_fatal_internal_stage_error() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.WRITE_REPORTS),
    )

    with pytest.raises(StageExecutionAborted) as raised:
        execute_plan(
            plan,
            {StageId.WRITE_REPORTS: lambda invocation: _Result()},
        )

    report = raised.value.report
    missing = report.record(StageId.CONFIGURATION)
    assert isinstance(raised.value.cause, LookupError)
    assert missing.status is ValidationStatus.ERROR
    assert missing.error_kind is ErrorKind.INTERNAL
    assert missing.primary_message == "Stage handler is not registered."
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK


def test_exhausted_execution_budget_skips_validation_but_not_finalization() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
        _stage(StageId.WRITE_REPORTS),
    )
    calls: list[StageId] = []

    report = execute_plan(
        plan,
        {
            stage.stage_id: (
                lambda invocation: calls.append(invocation.stage.stage_id)
                or _Result()
            )
            for stage in plan.stages
        },
        remaining_execution_seconds=lambda: 0,
    )

    assert calls == [StageId.WRITE_REPORTS]
    assert report.record(StageId.CONFIGURATION).primary_message == (
        "the usable run execution budget was exhausted"
    )
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert report.aborted is True


def test_timeout_is_bounded_by_the_remaining_execution_budget() -> None:
    plan = _plan(_stage(StageId.COMPILE_SOURCES, timeout_sec=30))
    observed: list[tuple[float | None, bool]] = []

    def handler(invocation: StageInvocation) -> _Result:
        observed.append((invocation.timeout_seconds, invocation.finalizing))
        return _Result()

    report = execute_plan(
        plan,
        {StageId.COMPILE_SOURCES: handler},
        remaining_execution_seconds=lambda: 5.25,
        timeout_resolver=lambda stage, finalizing: 12,
    )

    assert report.aborted is False
    assert observed == [(5.25, False)]


def test_finalization_uses_its_own_timeout_and_does_not_consume_normal_budget() -> None:
    plan = _plan(_stage(StageId.WRITE_REPORTS, timeout_sec=9))
    budget_called = False
    observed: list[tuple[float | None, bool]] = []

    def budget() -> float:
        nonlocal budget_called
        budget_called = True
        return 0

    report = execute_plan(
        plan,
        {
            StageId.WRITE_REPORTS: lambda invocation: (
                observed.append(
                    (invocation.timeout_seconds, invocation.finalizing)
                )
                or _Result()
            )
        },
        remaining_execution_seconds=budget,
    )

    assert report.aborted is False
    assert budget_called is False
    assert observed == [(9.0, True)]


def test_finalization_ignores_validation_prerequisite_failures() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(
            StageId.WRITE_REPORTS,
            prerequisites=(StageId.CONFIGURATION,),
        ),
        _stage(
            StageId.WRITE_MANIFEST,
            prerequisites=(StageId.WRITE_REPORTS,),
        ),
    )
    calls: list[StageId] = []

    def handler(invocation: StageInvocation) -> _Result:
        calls.append(invocation.stage.stage_id)
        if invocation.stage.stage_id is StageId.CONFIGURATION:
            return _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.CONFIG,
                primary_message="configuration rejected",
                blocks_dependents=True,
            )
        return _Result()

    report = execute_plan(
        plan,
        {stage.stage_id: handler for stage in plan.stages},
    )

    assert report.aborted is False
    assert calls == [
        StageId.CONFIGURATION,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    ]
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK
    assert report.record(StageId.WRITE_MANIFEST).status is ValidationStatus.OK


def test_unsafe_run_ownership_disables_all_finalization_handlers() -> None:
    plan = _plan(
        _stage(StageId.WRITE_REPORTS),
        _stage(StageId.WRITE_MANIFEST),
    )
    called = False

    def handler(invocation: StageInvocation) -> _Result:
        nonlocal called
        called = True
        return _Result()

    report = execute_plan(
        plan,
        {
            StageId.WRITE_REPORTS: handler,
            StageId.WRITE_MANIFEST: handler,
        },
        finalization_allowed=False,
    )

    assert called is False
    assert all(
        record.status is ValidationStatus.SKIPPED
        for record in report.records
    )
    assert all(
        "run ownership is unsafe" in record.primary_message
        for record in report.records
    )
    assert report.aborted is False


def test_abort_run_flag_stops_normal_work_even_with_trustworthy_evidence() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
        _stage(StageId.WRITE_REPORTS),
    )

    report = execute_plan(
        plan,
        {
            StageId.CONFIGURATION: lambda invocation: _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.CONFIG,
                primary_message="policy requires abort",
                blocks_dependents=True,
                evidence_trustworthy=True,
                abort_run=True,
            ),
            StageId.ENVIRONMENT: lambda invocation: _Result(),
            StageId.WRITE_REPORTS: lambda invocation: _Result(),
        },
    )

    assert report.aborted is True
    assert report.abort_reason == "policy requires abort"
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED
    assert report.record(StageId.WRITE_REPORTS).status is ValidationStatus.OK


def test_untrustworthy_evidence_forces_abort_without_explicit_abort_flag() -> None:
    plan = _plan(
        _stage(StageId.CONFIGURATION),
        _stage(StageId.ENVIRONMENT),
    )

    report = execute_plan(
        plan,
        {
            StageId.CONFIGURATION: lambda invocation: _Result(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.IO,
                primary_message="evidence capture incomplete",
                blocks_dependents=True,
                evidence_trustworthy=False,
            ),
            StageId.ENVIRONMENT: lambda invocation: _Result(),
        },
    )

    assert report.aborted is True
    assert report.abort_reason == "evidence capture incomplete"
    assert report.record(StageId.ENVIRONMENT).status is ValidationStatus.SKIPPED


def test_report_aggregates_only_required_stage_statuses() -> None:
    report = StageExecutionReport(
        records=(
            _record(StageId.CONFIGURATION),
            _record(
                StageId.VERSION_PROBE,
                requirement=StageRequirement.OPTIONAL,
                status=ValidationStatus.ERROR,
                error_kind=ErrorKind.TOOL,
                message="optional tool failed",
                blocks_dependents=True,
            ),
            _record(
                StageId.ENVIRONMENT,
                status=ValidationStatus.SKIPPED,
                message="not reached",
                blocks_dependents=True,
            ),
        ),
        aborted=True,
        abort_reason="incomplete required work",
    )

    assert report.required_status is ValidationStatus.SKIPPED
    assert report.incomplete_required_stages == (StageId.ENVIRONMENT,)
    assert report.record(StageId.CONFIGURATION).successful is True
    assert report.record(StageId.VERSION_PROBE).required is False
    assert report.by_stage[StageId.ENVIRONMENT].completed is False
    with pytest.raises(TypeError):
        report.by_stage[StageId.SELECTION] = report.records[0]  # type: ignore[index]
    with pytest.raises(KeyError):
        report.record(StageId.SELECTION)


def test_record_model_enforces_status_and_evidence_invariants() -> None:
    with pytest.raises(ValueError, match="error_kind OK"):
        _record(
            StageId.CONFIGURATION,
            status=ValidationStatus.OK,
            error_kind=ErrorKind.CONFIG,
        )

    with pytest.raises(ValueError, match="must block dependents"):
        _record(
            StageId.CONFIGURATION,
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.INTERNAL,
            message="internal error",
            blocks_dependents=False,
        )

    with pytest.raises(ValueError, match="untrustworthy"):
        _record(
            StageId.CONFIGURATION,
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.IO,
            message="evidence lost",
            blocks_dependents=False,
            evidence_trustworthy=False,
        )

    with pytest.raises(ValueError, match="abort_run"):
        _record(
            StageId.CONFIGURATION,
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.CONFIG,
            message="abort",
            abort_run=True,
        )


def test_executor_rejects_invalid_callback_contracts() -> None:
    plan = _plan(_stage(StageId.CONFIGURATION))
    handler = {StageId.CONFIGURATION: lambda invocation: _Result()}

    with pytest.raises(TypeError, match="handlers must be a mapping"):
        execute_plan(plan, ())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must return a bool"):
        execute_plan(
            plan,
            handler,
            cancellation_requested=lambda: 1,  # type: ignore[return-value]
        )

    with pytest.raises(TypeError, match="must return a number or None"):
        execute_plan(
            plan,
            handler,
            remaining_execution_seconds=lambda: "many",  # type: ignore[return-value]
        )

    with pytest.raises(ValueError, match="timeout.*positive"):
        execute_plan(
            plan,
            handler,
            timeout_resolver=lambda stage, finalizing: 0,
        )


def test_clock_must_be_monotonic_and_return_non_negative_integers() -> None:
    stage = _stage(StageId.CONFIGURATION)

    with pytest.raises(TypeError, match="clock_ns must return an integer"):
        execute_stage(
            stage,
            lambda invocation: _Result(),
            clock_ns=lambda: 1.5,  # type: ignore[return-value]
        )

    with pytest.raises(ValueError, match="non-negative"):
        execute_stage(
            stage,
            lambda invocation: _Result(),
            clock_ns=lambda: -1,
        )

    with pytest.raises(ValueError, match="moved backwards"):
        execute_stage(
            stage,
            lambda invocation: _Result(),
            clock_ns=_clock(10, 9),
        )
