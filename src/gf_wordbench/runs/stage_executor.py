"""Dependency-aware execution of one resolved GF Wordbench run plan."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, cast, runtime_checkable

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    StageExecutionError,
)
from gf_wordbench.kernel.statuses import ErrorKind, ValidationStatus

from .planner import (
    PlannedStage,
    RunPlan,
    StageId,
    StageRequirement,
)

StageHandler: TypeAlias = Callable[["StageInvocation"], object]
CancellationCheck: TypeAlias = Callable[[], bool]
CancellationReasonProvider: TypeAlias = Callable[[], str | None]
RemainingBudgetProvider: TypeAlias = Callable[[], float | None]
TimeoutResolver: TypeAlias = Callable[[PlannedStage, bool], float | None]
StageRecordSink: TypeAlias = Callable[["StageExecutionRecord"], None]
Clock: TypeAlias = Callable[[], int]

_FINALIZATION_STAGES: Final[frozenset[StageId]] = frozenset(
    {
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    }
)
_STATUS_RANK: Final[dict[ValidationStatus, int]] = {
    ValidationStatus.OK: 0,
    ValidationStatus.SKIPPED: 1,
    ValidationStatus.FAIL: 2,
    ValidationStatus.ERROR: 3,
}


@runtime_checkable
class StageResultLike(Protocol):
    status: ValidationStatus
    duration_ms: int
    error_kind: ErrorKind
    primary_message: str
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StageInvocation:
    stage: PlannedStage
    timeout_seconds: float | None
    prior_records: Mapping[StageId, "StageExecutionRecord"]
    finalizing: bool

    def __post_init__(self) -> None:
        if not isinstance(self.stage, PlannedStage):
            raise TypeError("stage must be a PlannedStage")
        if self.timeout_seconds is not None:
            if isinstance(self.timeout_seconds, bool) or not isinstance(
                self.timeout_seconds,
                (int, float),
            ):
                raise TypeError(
                    "timeout_seconds must be a number or None"
                )
            if not math.isfinite(float(self.timeout_seconds)):
                raise ValueError("timeout_seconds must be finite")
            if self.timeout_seconds <= 0:
                raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.prior_records, Mapping):
            raise TypeError("prior_records must be a mapping")
        if type(self.finalizing) is not bool:
            raise TypeError("finalizing must be a bool")


@dataclass(frozen=True, slots=True)
class StageExecutionRecord:
    stage_id: StageId
    requirement: StageRequirement
    status: ValidationStatus
    duration_ms: int
    error_kind: ErrorKind
    primary_message: str
    error_detail: str
    evidence_paths: tuple[str, ...]
    blocks_dependents: bool
    evidence_trustworthy: bool
    abort_run: bool
    payload: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage_id, StageId):
            raise TypeError("stage_id must be a StageId")
        if not isinstance(self.requirement, StageRequirement):
            raise TypeError("requirement must be a StageRequirement")
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be a ValidationStatus")
        if isinstance(self.duration_ms, bool) or not isinstance(
            self.duration_ms,
            int,
        ):
            raise TypeError("duration_ms must be an integer")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be an ErrorKind")
        _validate_text(
            self.primary_message,
            field="primary_message",
            required=self.status is not ValidationStatus.OK,
        )
        _validate_text(
            self.error_detail,
            field="error_detail",
            required=False,
        )
        _validate_evidence_paths(self.evidence_paths)
        for field_name in (
            "blocks_dependents",
            "evidence_trustworthy",
            "abort_run",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a bool")

        if (
            self.status is ValidationStatus.OK
            and self.error_kind is not ErrorKind.OK
        ):
            raise ValueError("OK stage status requires error_kind OK")
        if (
            self.status is ValidationStatus.SKIPPED
            and self.error_kind is not ErrorKind.OK
        ):
            raise ValueError("SKIPPED stage status requires error_kind OK")
        if (
            self.status in {
                ValidationStatus.FAIL,
                ValidationStatus.ERROR,
            }
            and self.error_kind is ErrorKind.OK
        ):
            raise ValueError(
                "FAIL and ERROR stage statuses require a non-OK error kind"
            )
        if (
            self.status is ValidationStatus.ERROR
            and not self.blocks_dependents
        ):
            raise ValueError("ERROR stage records must block dependents")
        if not self.evidence_trustworthy and not self.blocks_dependents:
            raise ValueError(
                "untrustworthy stage evidence must block dependents"
            )
        if self.abort_run and not self.blocks_dependents:
            raise ValueError("abort_run requires blocks_dependents")

    @property
    def completed(self) -> bool:
        return self.status is not ValidationStatus.SKIPPED

    @property
    def required(self) -> bool:
        return self.requirement is StageRequirement.REQUIRED

    @property
    def successful(self) -> bool:
        return self.status is ValidationStatus.OK

    @property
    def prerequisite_available(self) -> bool:
        return (
            self.status not in {
                ValidationStatus.ERROR,
                ValidationStatus.SKIPPED,
            }
            and not self.blocks_dependents
            and self.evidence_trustworthy
        )


@dataclass(frozen=True, slots=True)
class StageExecutionReport:
    records: tuple[StageExecutionRecord, ...]
    aborted: bool
    abort_reason: str | None
    fatal_stage: StageId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise TypeError("records must be a tuple")
        if any(
            not isinstance(record, StageExecutionRecord)
            for record in self.records
        ):
            raise TypeError(
                "records must contain StageExecutionRecord values"
            )
        stage_ids = tuple(record.stage_id for record in self.records)
        if len(set(stage_ids)) != len(stage_ids):
            raise ValueError("records must contain unique stage IDs")
        if type(self.aborted) is not bool:
            raise TypeError("aborted must be a bool")
        if self.aborted:
            _validate_text(
                self.abort_reason,
                field="abort_reason",
                required=True,
            )
        elif self.abort_reason is not None:
            raise ValueError(
                "abort_reason must be None when execution was not aborted"
            )
        if self.fatal_stage is not None and not isinstance(
            self.fatal_stage,
            StageId,
        ):
            raise TypeError("fatal_stage must be a StageId or None")
        if self.fatal_stage is not None and not self.aborted:
            raise ValueError("fatal_stage requires aborted execution")

    @property
    def by_stage(self) -> Mapping[StageId, StageExecutionRecord]:
        return MappingProxyType(
            {record.stage_id: record for record in self.records}
        )

    @property
    def required_status(self) -> ValidationStatus:
        required = tuple(
            record.status
            for record in self.records
            if record.required
        )
        if not required:
            return ValidationStatus.OK
        return max(required, key=_STATUS_RANK.__getitem__)

    @property
    def incomplete_required_stages(self) -> tuple[StageId, ...]:
        return tuple(
            record.stage_id
            for record in self.records
            if record.required
            and record.status is ValidationStatus.SKIPPED
        )

    def record(self, stage_id: StageId) -> StageExecutionRecord:
        if not isinstance(stage_id, StageId):
            raise TypeError("stage_id must be a StageId")
        for record in self.records:
            if record.stage_id is stage_id:
                return record
        raise KeyError(stage_id.value)


class StageExecutionAborted(StageExecutionError):
    report: StageExecutionReport
    failed_stage: StageId
    cause: BaseException

    def __init__(
        self,
        message: str,
        *,
        report: StageExecutionReport,
        failed_stage: StageId,
        cause: BaseException,
    ) -> None:
        if not isinstance(report, StageExecutionReport):
            raise TypeError("report must be a StageExecutionReport")
        if not isinstance(failed_stage, StageId):
            raise TypeError("failed_stage must be a StageId")
        if not isinstance(cause, BaseException):
            raise TypeError("cause must be a BaseException")
        self.report = report
        self.failed_stage = failed_stage
        self.cause = cause
        super().__init__(
            message,
            code="GF-WB-INTERNAL-001",
            detail=_bounded_exception(cause),
            stage=failed_stage.value,
            operation="execute-stage",
            subject=failed_stage.value,
        )


def execute_plan(
    plan: RunPlan,
    handlers: Mapping[StageId, StageHandler],
    *,
    cancellation_requested: CancellationCheck | None = None,
    cancellation_reason: CancellationReasonProvider | None = None,
    remaining_execution_seconds: RemainingBudgetProvider | None = None,
    timeout_resolver: TimeoutResolver | None = None,
    fail_fast: bool = False,
    finalization_allowed: bool = True,
    record_sink: StageRecordSink | None = None,
    clock_ns: Clock = time.monotonic_ns,
) -> StageExecutionReport:
    if not isinstance(plan, RunPlan):
        raise TypeError("plan must be a RunPlan")
    normalized_handlers = _validate_handlers(handlers)
    cancel_check = cancellation_requested or _never_cancelled
    reason_provider = cancellation_reason or _no_cancellation_reason
    budget_provider = remaining_execution_seconds or _unbounded_budget
    resolve_timeout = timeout_resolver or _default_timeout_resolver
    if type(fail_fast) is not bool:
        raise TypeError("fail_fast must be a bool")
    if type(finalization_allowed) is not bool:
        raise TypeError("finalization_allowed must be a bool")
    if not callable(record_sink) and record_sink is not None:
        raise TypeError("record_sink must be callable or None")
    if not callable(clock_ns):
        raise TypeError("clock_ns must be callable")

    records: list[StageExecutionRecord] = []
    records_by_stage: dict[StageId, StageExecutionRecord] = {}
    aborted = False
    abort_reason: str | None = None
    fatal_stage: StageId | None = None
    fatal_cause: BaseException | None = None

    for planned in plan.stages:
        finalizing = planned.stage_id in _FINALIZATION_STAGES

        if planned.requirement is StageRequirement.SKIPPED:
            record = _skipped_record(
                planned,
                planned.reason or "stage is not selected by the run plan",
            )
            _append_record(
                record,
                records=records,
                records_by_stage=records_by_stage,
                sink=record_sink,
            )
            continue

        if aborted and not finalizing:
            record = _skipped_record(
                planned,
                abort_reason or "run execution was aborted",
            )
            _append_record(
                record,
                records=records,
                records_by_stage=records_by_stage,
                sink=record_sink,
            )
            continue

        if finalizing and not finalization_allowed:
            record = _skipped_record(
                planned,
                "finalization is unavailable because run ownership is unsafe",
            )
            _append_record(
                record,
                records=records,
                records_by_stage=records_by_stage,
                sink=record_sink,
            )
            continue

        if not finalizing:
            if _call_cancellation_check(cancel_check):
                aborted = True
                abort_reason = (
                    _call_cancellation_reason(reason_provider)
                    or "cancellation was requested"
                )
                record = _skipped_record(planned, abort_reason)
                _append_record(
                    record,
                    records=records,
                    records_by_stage=records_by_stage,
                    sink=record_sink,
                )
                continue

            remaining = _remaining_seconds(budget_provider)
            if remaining is not None and remaining <= 0:
                aborted = True
                abort_reason = "the usable run execution budget was exhausted"
                record = _skipped_record(planned, abort_reason)
                _append_record(
                    record,
                    records=records,
                    records_by_stage=records_by_stage,
                    sink=record_sink,
                )
                continue
        else:
            remaining = None

        blockers = _blocking_prerequisites(
            planned,
            records_by_stage,
            ignore_failures=finalizing,
        )
        if blockers:
            reason = (
                "blocked by unavailable prerequisites: "
                + ", ".join(stage_id.value for stage_id in blockers)
            )
            record = _skipped_record(planned, reason)
            _append_record(
                record,
                records=records,
                records_by_stage=records_by_stage,
                sink=record_sink,
            )
            continue

        handler = normalized_handlers.get(planned.stage_id)
        if handler is None:
            cause = LookupError(
                f"no handler registered for stage {planned.stage_id.value}"
            )
            record = _internal_error_record(
                planned,
                duration_ms=0,
                message="Stage handler is not registered.",
                detail=str(cause),
            )
            _append_record(
                record,
                records=records,
                records_by_stage=records_by_stage,
                sink=record_sink,
            )
            aborted = True
            abort_reason = (
                f"stage {planned.stage_id.value} has no registered handler"
            )
            fatal_stage = planned.stage_id
            fatal_cause = cause
            continue

        timeout_seconds = _resolve_timeout(
            planned,
            finalizing=finalizing,
            remaining_seconds=remaining,
            resolver=resolve_timeout,
        )
        invocation = StageInvocation(
            stage=planned,
            timeout_seconds=timeout_seconds,
            prior_records=MappingProxyType(dict(records_by_stage)),
            finalizing=finalizing,
        )

        started_ns = _clock_value(clock_ns)
        try:
            raw_result = handler(invocation)
            record = _normalize_stage_result(
                planned,
                raw_result,
                measured_duration_ms=_elapsed_ms(
                    started_ns,
                    _clock_value(clock_ns),
                ),
            )
        except CancellationRequested as exc:
            record = _cancellation_error_record(
                planned,
                duration_ms=_elapsed_ms(
                    started_ns,
                    _clock_value(clock_ns),
                ),
                reason=exc.message,
                detail=exc.detail,
                evidence_paths=exc.evidence_paths,
            )
            aborted = True
            abort_reason = exc.message
        except BaseException as exc:
            record = _internal_error_record(
                planned,
                duration_ms=_elapsed_ms(
                    started_ns,
                    _clock_value(clock_ns),
                ),
                message="Stage execution raised an unexpected exception.",
                detail=_bounded_exception(exc),
            )
            aborted = True
            abort_reason = (
                f"unexpected failure in stage {planned.stage_id.value}"
            )
            fatal_stage = planned.stage_id
            fatal_cause = exc

        _append_record(
            record,
            records=records,
            records_by_stage=records_by_stage,
            sink=record_sink,
        )

        if record.abort_run or not record.evidence_trustworthy:
            aborted = True
            abort_reason = (
                record.primary_message
                or f"stage {record.stage_id.value} requires run abort"
            )
        elif (
            fail_fast
            and record.required
            and record.status
            in {
                ValidationStatus.FAIL,
                ValidationStatus.ERROR,
            }
        ):
            aborted = True
            abort_reason = (
                f"fail-fast stopped execution after "
                f"{record.stage_id.value}"
            )

    report = StageExecutionReport(
        records=tuple(records),
        aborted=aborted,
        abort_reason=abort_reason if aborted else None,
        fatal_stage=fatal_stage,
    )
    if fatal_stage is not None and fatal_cause is not None:
        raise StageExecutionAborted(
            "Run stage execution aborted after an unexpected failure.",
            report=report,
            failed_stage=fatal_stage,
            cause=fatal_cause,
        ) from fatal_cause
    return report


def execute_stage(
    stage: PlannedStage,
    handler: StageHandler,
    *,
    prior_records: Mapping[StageId, StageExecutionRecord] | None = None,
    timeout_seconds: float | None = None,
    finalizing: bool = False,
    clock_ns: Clock = time.monotonic_ns,
) -> StageExecutionRecord:
    if not isinstance(stage, PlannedStage):
        raise TypeError("stage must be a PlannedStage")
    if stage.requirement is StageRequirement.SKIPPED:
        return _skipped_record(
            stage,
            stage.reason or "stage is not selected by the run plan",
        )
    if not callable(handler):
        raise TypeError("handler must be callable")
    if type(finalizing) is not bool:
        raise TypeError("finalizing must be a bool")
    if timeout_seconds is not None:
        timeout_seconds = _positive_finite_seconds(
            timeout_seconds,
            field="timeout_seconds",
        )

    prior = dict(prior_records or {})
    invocation = StageInvocation(
        stage=stage,
        timeout_seconds=timeout_seconds,
        prior_records=MappingProxyType(prior),
        finalizing=finalizing,
    )
    started_ns = _clock_value(clock_ns)
    raw_result = handler(invocation)
    return _normalize_stage_result(
        stage,
        raw_result,
        measured_duration_ms=_elapsed_ms(
            started_ns,
            _clock_value(clock_ns),
        ),
    )


def _normalize_stage_result(
    planned: PlannedStage,
    result: object,
    *,
    measured_duration_ms: int,
) -> StageExecutionRecord:
    if result is None:
        raise TypeError("stage handler returned None")

    status = getattr(result, "status", None)
    duration_ms = getattr(result, "duration_ms", measured_duration_ms)
    error_kind = getattr(result, "error_kind", None)
    primary_message = getattr(result, "primary_message", "")
    error_detail = getattr(result, "error_detail", "")
    evidence_paths = getattr(result, "evidence_paths", ())
    blocks_dependents = getattr(
        result,
        "blocks_dependents",
        status is ValidationStatus.ERROR,
    )
    evidence_trustworthy = getattr(
        result,
        "evidence_trustworthy",
        status is not ValidationStatus.ERROR,
    )
    abort_run = getattr(result, "abort_run", False)

    if not isinstance(status, ValidationStatus):
        raise TypeError(
            "stage result status must be a ValidationStatus"
        )
    if not isinstance(error_kind, ErrorKind):
        raise TypeError("stage result error_kind must be an ErrorKind")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int):
        raise TypeError("stage result duration_ms must be an integer")
    if duration_ms < 0:
        raise ValueError(
            "stage result duration_ms must be non-negative"
        )
    if not isinstance(primary_message, str):
        raise TypeError(
            "stage result primary_message must be a string"
        )
    if not isinstance(error_detail, str):
        raise TypeError("stage result error_detail must be a string")
    normalized_evidence = _validate_evidence_paths(evidence_paths)

    return StageExecutionRecord(
        stage_id=planned.stage_id,
        requirement=planned.requirement,
        status=status,
        duration_ms=duration_ms,
        error_kind=error_kind,
        primary_message=primary_message,
        error_detail=error_detail,
        evidence_paths=normalized_evidence,
        blocks_dependents=_strict_bool(
            blocks_dependents,
            field="stage result blocks_dependents",
        ),
        evidence_trustworthy=_strict_bool(
            evidence_trustworthy,
            field="stage result evidence_trustworthy",
        ),
        abort_run=_strict_bool(
            abort_run,
            field="stage result abort_run",
        ),
        payload=result,
    )


def _blocking_prerequisites(
    planned: PlannedStage,
    records: Mapping[StageId, StageExecutionRecord],
    *,
    ignore_failures: bool,
) -> tuple[StageId, ...]:
    if ignore_failures:
        return ()
    blockers: list[StageId] = []
    for prerequisite in planned.prerequisites:
        result = records.get(prerequisite)
        if result is None or not result.prerequisite_available:
            blockers.append(prerequisite)
    return tuple(blockers)


def _resolve_timeout(
    planned: PlannedStage,
    *,
    finalizing: bool,
    remaining_seconds: float | None,
    resolver: TimeoutResolver,
) -> float | None:
    value = resolver(planned, finalizing)
    if value is not None:
        value = _positive_finite_seconds(
            value,
            field=f"{planned.stage_id.value} timeout",
        )
    if not finalizing and remaining_seconds is not None:
        remaining = _positive_finite_seconds(
            remaining_seconds,
            field="remaining execution budget",
        )
        value = remaining if value is None else min(value, remaining)
    return value


def _default_timeout_resolver(
    planned: PlannedStage,
    finalizing: bool,
) -> float | None:
    del finalizing
    return (
        None
        if planned.timeout_sec is None
        else float(planned.timeout_sec)
    )


def _skipped_record(
    planned: PlannedStage,
    reason: str,
) -> StageExecutionRecord:
    _validate_text(reason, field="skip reason", required=True)
    return StageExecutionRecord(
        stage_id=planned.stage_id,
        requirement=planned.requirement,
        status=ValidationStatus.SKIPPED,
        duration_ms=0,
        error_kind=ErrorKind.OK,
        primary_message=reason,
        error_detail="",
        evidence_paths=(),
        blocks_dependents=True,
        evidence_trustworthy=True,
        abort_run=False,
    )


def _cancellation_error_record(
    planned: PlannedStage,
    *,
    duration_ms: int,
    reason: str,
    detail: str,
    evidence_paths: tuple[str, ...],
) -> StageExecutionRecord:
    return StageExecutionRecord(
        stage_id=planned.stage_id,
        requirement=planned.requirement,
        status=ValidationStatus.ERROR,
        duration_ms=duration_ms,
        error_kind=ErrorKind.OTHER,
        primary_message=reason or "Stage execution was cancelled.",
        error_detail=detail,
        evidence_paths=_validate_evidence_paths(evidence_paths),
        blocks_dependents=True,
        evidence_trustworthy=False,
        abort_run=True,
    )


def _internal_error_record(
    planned: PlannedStage,
    *,
    duration_ms: int,
    message: str,
    detail: str,
) -> StageExecutionRecord:
    return StageExecutionRecord(
        stage_id=planned.stage_id,
        requirement=planned.requirement,
        status=ValidationStatus.ERROR,
        duration_ms=duration_ms,
        error_kind=ErrorKind.INTERNAL,
        primary_message=message,
        error_detail=detail,
        evidence_paths=(),
        blocks_dependents=True,
        evidence_trustworthy=False,
        abort_run=True,
    )


def _append_record(
    record: StageExecutionRecord,
    *,
    records: list[StageExecutionRecord],
    records_by_stage: dict[StageId, StageExecutionRecord],
    sink: StageRecordSink | None,
) -> None:
    if record.stage_id in records_by_stage:
        raise ValueError(
            f"duplicate stage record: {record.stage_id.value}"
        )
    records.append(record)
    records_by_stage[record.stage_id] = record
    if sink is not None:
        sink(record)


def _validate_handlers(
    handlers: Mapping[StageId, StageHandler],
) -> dict[StageId, StageHandler]:
    if not isinstance(handlers, Mapping):
        raise TypeError("handlers must be a mapping")
    normalized: dict[StageId, StageHandler] = {}
    for stage_id, handler in handlers.items():
        if not isinstance(stage_id, StageId):
            raise TypeError("handler keys must be StageId values")
        if not callable(handler):
            raise TypeError(
                f"handler for {stage_id.value} must be callable"
            )
        normalized[stage_id] = handler
    return normalized


def _remaining_seconds(
    provider: RemainingBudgetProvider,
) -> float | None:
    value = provider()
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            "remaining_execution_seconds must return a number or None"
        )
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(
            "remaining execution budget must be finite"
        )
    return max(0.0, numeric)


def _call_cancellation_check(check: CancellationCheck) -> bool:
    value = check()
    if type(value) is not bool:
        raise TypeError(
            "cancellation_requested must return a bool"
        )
    return cast(bool, value)


def _call_cancellation_reason(
    provider: CancellationReasonProvider,
) -> str | None:
    value = provider()
    if value is None:
        return None
    _validate_text(
        value,
        field="cancellation reason",
        required=True,
    )
    return value


def _positive_finite_seconds(
    value: object,
    *,
    field: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite")
    if numeric <= 0:
        raise ValueError(f"{field} must be positive")
    return numeric


def _clock_value(clock_ns: Clock) -> int:
    value = clock_ns()
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("clock_ns must return an integer")
    if value < 0:
        raise ValueError("clock_ns must return a non-negative value")
    return value


def _elapsed_ms(start_ns: int, finish_ns: int) -> int:
    if finish_ns < start_ns:
        raise ValueError("clock moved backwards during stage execution")
    return (finish_ns - start_ns) // 1_000_000


def _validate_evidence_paths(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(
            "evidence_paths must be an iterable of path strings"
        )
    try:
        paths = tuple(value)
    except TypeError as exc:
        raise TypeError(
            "evidence_paths must be an iterable of path strings"
        ) from exc
    for index, path in enumerate(paths):
        _validate_text(
            path,
            field=f"evidence_paths[{index}]",
            required=True,
        )
    if len(set(paths)) != len(paths):
        raise ValueError("evidence_paths must not contain duplicates")
    return paths


def _validate_text(
    value: object,
    *,
    field: str,
    required: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if required and not value.strip():
        raise ValueError(f"{field} must not be empty")
    return value


def _strict_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a bool")
    return cast(bool, value)


def _bounded_exception(
    exc: BaseException,
    *,
    maximum: int = 480,
) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= maximum:
        return text
    return text[: maximum - 1] + "…"


def _never_cancelled() -> bool:
    return False


def _no_cancellation_reason() -> None:
    return None


def _unbounded_budget() -> None:
    return None


__all__ = (
    "CancellationCheck",
    "CancellationReasonProvider",
    "Clock",
    "RemainingBudgetProvider",
    "StageExecutionAborted",
    "StageExecutionRecord",
    "StageExecutionReport",
    "StageHandler",
    "StageInvocation",
    "StageRecordSink",
    "StageResultLike",
    "TimeoutResolver",
    "execute_plan",
    "execute_stage",
)
