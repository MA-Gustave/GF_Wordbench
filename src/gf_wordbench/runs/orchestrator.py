"""Complete-run coordination for GF Wordbench."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Generic, TypeAlias, TypeVar

from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.kernel.events import EventLevel, EventSink, LifecycleEvent

ConfigT = TypeVar("ConfigT")
PathsT = TypeVar("PathsT")
PlanT = TypeVar("PlanT")
PreflightT = TypeVar("PreflightT")
ExecutionT = TypeVar("ExecutionT")
ResultT = TypeVar("ResultT")

CancellationCheck: TypeAlias = Callable[[], None]
LifecycleSink: TypeAlias = EventSink[LifecycleEvent]
Clock: TypeAlias = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class OrchestrationFailure:
    phase: str
    occurred_at: datetime
    exception: Exception
    cancelled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.phase, str) or not self.phase.strip():
            raise ValueError("phase must be a non-empty string")
        if "\x00" in self.phase:
            raise ValueError("phase must not contain NUL characters")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError("occurred_at must be a datetime")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        if not isinstance(self.exception, Exception):
            raise TypeError("exception must be an Exception")
        if type(self.cancelled) is not bool:
            raise TypeError("cancelled must be a bool")
        object.__setattr__(self, "occurred_at", self.occurred_at.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class RunOrchestrationServices(
    Generic[
        ConfigT,
        PathsT,
        PlanT,
        PreflightT,
        ExecutionT,
        ResultT,
    ]
):
    plan: Callable[[ConfigT, PathsT], PlanT]
    preflight: Callable[[ConfigT, PathsT, PlanT], PreflightT]
    preflight_is_fatal: Callable[[PreflightT], bool]
    execute: Callable[
        [
            ConfigT,
            PathsT,
            PlanT,
            PreflightT,
            CancellationCheck,
            LifecycleSink | None,
        ],
        ExecutionT,
    ]
    build_completed_result: Callable[
        [ConfigT, PathsT, PlanT, PreflightT, ExecutionT],
        ResultT,
    ]
    build_preflight_failure_result: Callable[
        [ConfigT, PathsT, PlanT, PreflightT],
        ResultT,
    ]
    build_cancelled_result: Callable[
        [
            ConfigT,
            PathsT,
            PlanT | None,
            PreflightT | None,
            ExecutionT | None,
            OrchestrationFailure,
        ],
        ResultT,
    ]
    build_fatal_result: Callable[
        [
            ConfigT,
            PathsT,
            PlanT | None,
            PreflightT | None,
            ExecutionT | None,
            OrchestrationFailure,
        ],
        ResultT,
    ]
    finalize: Callable[[ResultT], ResultT]

    def __post_init__(self) -> None:
        for field_name in (
            "plan",
            "preflight",
            "preflight_is_fatal",
            "execute",
            "build_completed_result",
            "build_preflight_failure_result",
            "build_cancelled_result",
            "build_fatal_result",
            "finalize",
        ):
            if not callable(getattr(self, field_name)):
                raise TypeError(f"{field_name} must be callable")


@dataclass(frozen=True, slots=True)
class RunOrchestrator(
    Generic[
        ConfigT,
        PathsT,
        PlanT,
        PreflightT,
        ExecutionT,
        ResultT,
    ]
):
    services: RunOrchestrationServices[
        ConfigT,
        PathsT,
        PlanT,
        PreflightT,
        ExecutionT,
        ResultT,
    ]
    clock: Clock = lambda: datetime.now(UTC)

    def __post_init__(self) -> None:
        if not isinstance(self.services, RunOrchestrationServices):
            raise TypeError("services must be RunOrchestrationServices")
        if not callable(self.clock):
            raise TypeError("clock must be callable")

    def run(
        self,
        run_config: ConfigT,
        run_paths: PathsT,
        *,
        cancellation_check: CancellationCheck | None = None,
        event_sink: LifecycleSink | None = None,
    ) -> ResultT:
        check_cancelled = cancellation_check or _no_cancellation
        if not callable(check_cancelled):
            raise TypeError("cancellation_check must be callable or None")
        if event_sink is not None and not callable(event_sink):
            raise TypeError("event_sink must be callable or None")

        run_id = _run_id(run_paths)
        plan: PlanT | None = None
        preflight: PreflightT | None = None
        execution: ExecutionT | None = None
        failure: OrchestrationFailure | None = None
        phase = "initializing"

        _emit(
            event_sink,
            LifecycleEvent(
                timestamp=self._now(),
                event="run_started",
                run_id=run_id,
                operation="orchestrate_run",
                message="Run orchestration started",
            ),
        )

        try:
            check_cancelled()

            phase = "planning"
            _emit_phase(event_sink, self._now(), run_id, phase, "started")
            plan = self.services.plan(run_config, run_paths)
            _emit_phase(event_sink, self._now(), run_id, phase, "completed")

            check_cancelled()

            phase = "preflight"
            _emit_phase(event_sink, self._now(), run_id, phase, "started")
            preflight = self.services.preflight(run_config, run_paths, plan)
            is_fatal = self.services.preflight_is_fatal(preflight)
            if type(is_fatal) is not bool:
                raise TypeError("preflight_is_fatal must return a bool")
            _emit_phase(
                event_sink,
                self._now(),
                run_id,
                phase,
                "failed" if is_fatal else "completed",
                level=EventLevel.ERROR if is_fatal else EventLevel.INFO,
            )

            if is_fatal:
                phase = "building_result"
                result = self.services.build_preflight_failure_result(
                    run_config,
                    run_paths,
                    plan,
                    preflight,
                )
            else:
                check_cancelled()

                phase = "executing"
                _emit_phase(event_sink, self._now(), run_id, phase, "started")
                execution = self.services.execute(
                    run_config,
                    run_paths,
                    plan,
                    preflight,
                    check_cancelled,
                    event_sink,
                )
                _emit_phase(event_sink, self._now(), run_id, phase, "completed")

                check_cancelled()

                phase = "building_result"
                _emit_phase(event_sink, self._now(), run_id, phase, "started")
                result = self.services.build_completed_result(
                    run_config,
                    run_paths,
                    plan,
                    preflight,
                    execution,
                )
                _emit_phase(event_sink, self._now(), run_id, phase, "completed")

        except CancellationRequested as exc:
            failure = OrchestrationFailure(
                phase=phase,
                occurred_at=self._now(),
                exception=exc,
                cancelled=True,
            )
            _emit_failure(event_sink, run_id, failure)
            result = self._build_cancelled_result(
                run_config,
                run_paths,
                plan,
                preflight,
                execution,
                failure,
            )
        except Exception as exc:
            failure = OrchestrationFailure(
                phase=phase,
                occurred_at=self._now(),
                exception=exc,
                cancelled=False,
            )
            _emit_failure(event_sink, run_id, failure)
            result = self._build_fatal_result(
                run_config,
                run_paths,
                plan,
                preflight,
                execution,
                failure,
            )

        phase = "finalizing"
        _emit_phase(event_sink, self._now(), run_id, phase, "started")
        try:
            finalized = self.services.finalize(result)
        except Exception as finalization_error:
            _emit(
                event_sink,
                LifecycleEvent(
                    timestamp=self._now(),
                    event="run_finalization_failed",
                    level=EventLevel.FATAL,
                    run_id=run_id,
                    stage="finalizing",
                    operation="orchestrate_run",
                    status="ERROR",
                    message=_bounded_message(finalization_error),
                ),
            )
            if failure is not None:
                raise ExceptionGroup(
                    "run orchestration and finalization failed",
                    [failure.exception, finalization_error],
                ) from finalization_error
            raise

        _emit_phase(event_sink, self._now(), run_id, phase, "completed")
        _emit(
            event_sink,
            LifecycleEvent(
                timestamp=self._now(),
                event="run_completed",
                run_id=run_id,
                operation="orchestrate_run",
                message="Run orchestration completed",
            ),
        )
        return finalized

    def _build_cancelled_result(
        self,
        run_config: ConfigT,
        run_paths: PathsT,
        plan: PlanT | None,
        preflight: PreflightT | None,
        execution: ExecutionT | None,
        failure: OrchestrationFailure,
    ) -> ResultT:
        try:
            return self.services.build_cancelled_result(
                run_config,
                run_paths,
                plan,
                preflight,
                execution,
                failure,
            )
        except Exception as build_error:
            raise ExceptionGroup(
                "cancellation result construction failed",
                [failure.exception, build_error],
            ) from build_error

    def _build_fatal_result(
        self,
        run_config: ConfigT,
        run_paths: PathsT,
        plan: PlanT | None,
        preflight: PreflightT | None,
        execution: ExecutionT | None,
        failure: OrchestrationFailure,
    ) -> ResultT:
        try:
            return self.services.build_fatal_result(
                run_config,
                run_paths,
                plan,
                preflight,
                execution,
                failure,
            )
        except Exception as build_error:
            raise ExceptionGroup(
                "fatal run-result construction failed",
                [failure.exception, build_error],
            ) from build_error

    def _now(self) -> datetime:
        value = self.clock()
        if not isinstance(value, datetime):
            raise TypeError("clock must return a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)


def run_validation(
    run_config: ConfigT,
    run_paths: PathsT,
    services: RunOrchestrationServices[
        ConfigT,
        PathsT,
        PlanT,
        PreflightT,
        ExecutionT,
        ResultT,
    ],
    *,
    cancellation_check: CancellationCheck | None = None,
    event_sink: LifecycleSink | None = None,
    clock: Clock = lambda: datetime.now(UTC),
) -> ResultT:
    return RunOrchestrator(services=services, clock=clock).run(
        run_config,
        run_paths,
        cancellation_check=cancellation_check,
        event_sink=event_sink,
    )


def _no_cancellation() -> None:
    return None


def _run_id(run_paths: object) -> str | None:
    value = getattr(run_paths, "run_id", None)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("run_paths.run_id must be a non-empty string")
    return value


def _emit_phase(
    sink: LifecycleSink | None,
    timestamp: datetime,
    run_id: str | None,
    phase: str,
    state: str,
    *,
    level: EventLevel = EventLevel.INFO,
) -> None:
    _emit(
        sink,
        LifecycleEvent(
            timestamp=timestamp,
            event=f"{phase}_{state}",
            level=level,
            run_id=run_id,
            stage=phase,
            operation="orchestrate_run",
            status=state.upper(),
            message=f"Run phase {phase} {state}",
        ),
    )


def _emit_failure(
    sink: LifecycleSink | None,
    run_id: str | None,
    failure: OrchestrationFailure,
) -> None:
    _emit(
        sink,
        LifecycleEvent(
            timestamp=failure.occurred_at,
            event=(
                "run_cancelled"
                if failure.cancelled
                else "run_orchestration_failed"
            ),
            level=(
                EventLevel.WARN
                if failure.cancelled
                else EventLevel.FATAL
            ),
            run_id=run_id,
            stage=failure.phase,
            operation="orchestrate_run",
            status="CANCELLED" if failure.cancelled else "ERROR",
            message=_bounded_message(failure.exception),
        ),
    )


def _emit(
    sink: LifecycleSink | None,
    event: LifecycleEvent,
) -> None:
    if sink is None:
        return
    try:
        sink(event)
    except Exception:
        return


def _bounded_message(error: Exception) -> str:
    text = str(error).strip() or type(error).__name__
    text = text.replace("\x00", "�")
    return text[:1_024]


__all__ = (
    "CancellationCheck",
    "Clock",
    "LifecycleSink",
    "OrchestrationFailure",
    "RunOrchestrationServices",
    "RunOrchestrator",
    "run_validation",
)
