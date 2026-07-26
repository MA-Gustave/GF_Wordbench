from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Final

import pytest

from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.kernel.events import EventLevel, LifecycleEvent
from gf_wordbench.runs.orchestrator import (
    OrchestrationFailure,
    RunOrchestrationServices,
    RunOrchestrator,
    run_validation,
)

_STARTED_AT: Final = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _Config:
    name: str = "config"


@dataclass(frozen=True, slots=True)
class _Paths:
    run_id: str = "run_20260725_120000_abcd1234"


@dataclass(frozen=True, slots=True)
class _Plan:
    name: str = "plan"


@dataclass(frozen=True, slots=True)
class _Preflight:
    fatal: bool = False


@dataclass(frozen=True, slots=True)
class _Execution:
    name: str = "execution"


@dataclass(frozen=True, slots=True)
class _Result:
    kind: str
    finalized: bool = False


class _Clock:
    def __init__(self, start: datetime = _STARTED_AT) -> None:
        self._start = start
        self.calls = 0

    def __call__(self) -> datetime:
        value = self._start + timedelta(microseconds=self.calls)
        self.calls += 1
        return value


class _CancellationProbe:
    def __init__(self, cancel_on_call: int | None = None) -> None:
        self.cancel_on_call = cancel_on_call
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1
        if self.calls == self.cancel_on_call:
            raise CancellationRequested("cancelled by test")


class _Harness:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.execution_error: Exception | None = None
        self.completed_builder_error: Exception | None = None
        self.cancelled_builder_error: Exception | None = None
        self.fatal_builder_error: Exception | None = None
        self.finalizer_error: Exception | None = None
        self.cancelled_failure: OrchestrationFailure | None = None
        self.fatal_failure: OrchestrationFailure | None = None
        self.cancelled_state: tuple[
            _Plan | None,
            _Preflight | None,
            _Execution | None,
        ] | None = None
        self.fatal_state: tuple[
            _Plan | None,
            _Preflight | None,
            _Execution | None,
        ] | None = None

    def plan(self, config: _Config, paths: _Paths) -> _Plan:
        assert config == _Config()
        assert paths == _Paths()
        self.calls.append("plan")
        return _Plan()

    def preflight(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan,
    ) -> _Preflight:
        assert config == _Config()
        assert paths == _Paths()
        assert plan == _Plan()
        self.calls.append("preflight")
        return _Preflight()

    def preflight_is_fatal(self, preflight: _Preflight) -> bool:
        self.calls.append("preflight_is_fatal")
        return preflight.fatal

    def execute(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan,
        preflight: _Preflight,
        cancellation_check: object,
        event_sink: object,
    ) -> _Execution:
        assert config == _Config()
        assert paths == _Paths()
        assert plan == _Plan()
        assert preflight == _Preflight()
        assert callable(cancellation_check)
        assert event_sink is None or callable(event_sink)
        self.calls.append("execute")
        if self.execution_error is not None:
            raise self.execution_error
        return _Execution()

    def build_completed_result(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan,
        preflight: _Preflight,
        execution: _Execution,
    ) -> _Result:
        assert config == _Config()
        assert paths == _Paths()
        assert plan == _Plan()
        assert preflight == _Preflight()
        assert execution == _Execution()
        self.calls.append("build_completed_result")
        if self.completed_builder_error is not None:
            raise self.completed_builder_error
        return _Result("completed")

    def build_preflight_failure_result(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan,
        preflight: _Preflight,
    ) -> _Result:
        assert config == _Config()
        assert paths == _Paths()
        assert plan == _Plan()
        assert preflight.fatal
        self.calls.append("build_preflight_failure_result")
        return _Result("preflight_failure")

    def build_cancelled_result(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan | None,
        preflight: _Preflight | None,
        execution: _Execution | None,
        failure: OrchestrationFailure,
    ) -> _Result:
        assert config == _Config()
        assert paths == _Paths()
        self.calls.append("build_cancelled_result")
        self.cancelled_failure = failure
        self.cancelled_state = (plan, preflight, execution)
        if self.cancelled_builder_error is not None:
            raise self.cancelled_builder_error
        return _Result("cancelled")

    def build_fatal_result(
        self,
        config: _Config,
        paths: _Paths,
        plan: _Plan | None,
        preflight: _Preflight | None,
        execution: _Execution | None,
        failure: OrchestrationFailure,
    ) -> _Result:
        assert config == _Config()
        assert paths == _Paths()
        self.calls.append("build_fatal_result")
        self.fatal_failure = failure
        self.fatal_state = (plan, preflight, execution)
        if self.fatal_builder_error is not None:
            raise self.fatal_builder_error
        return _Result("fatal")

    def finalize(self, result: _Result) -> _Result:
        self.calls.append("finalize")
        if self.finalizer_error is not None:
            raise self.finalizer_error
        return replace(result, finalized=True)

    def services(
        self,
        *,
        fatal_preflight: bool = False,
    ) -> RunOrchestrationServices[
        _Config,
        _Paths,
        _Plan,
        _Preflight,
        _Execution,
        _Result,
    ]:
        if fatal_preflight:
            preflight = self.preflight

            def fatal_preflight_service(
                config: _Config,
                paths: _Paths,
                plan: _Plan,
            ) -> _Preflight:
                return replace(preflight(config, paths, plan), fatal=True)

            preflight_service = fatal_preflight_service
        else:
            preflight_service = self.preflight

        return RunOrchestrationServices(
            plan=self.plan,
            preflight=preflight_service,
            preflight_is_fatal=self.preflight_is_fatal,
            execute=self.execute,
            build_completed_result=self.build_completed_result,
            build_preflight_failure_result=self.build_preflight_failure_result,
            build_cancelled_result=self.build_cancelled_result,
            build_fatal_result=self.build_fatal_result,
            finalize=self.finalize,
        )


def _event_names(events: list[LifecycleEvent]) -> list[str]:
    return [event.event for event in events]


def test_completed_run_executes_each_phase_once_and_emits_ordered_events() -> None:
    harness = _Harness()
    clock = _Clock()
    cancellation = _CancellationProbe()
    events: list[LifecycleEvent] = []

    result = RunOrchestrator(harness.services(), clock=clock).run(
        _Config(),
        _Paths(),
        cancellation_check=cancellation,
        event_sink=events.append,
    )

    assert result == _Result("completed", finalized=True)
    assert cancellation.calls == 4
    assert harness.calls == [
        "plan",
        "preflight",
        "preflight_is_fatal",
        "execute",
        "build_completed_result",
        "finalize",
    ]
    assert _event_names(events) == [
        "run_started",
        "planning_started",
        "planning_completed",
        "preflight_started",
        "preflight_completed",
        "executing_started",
        "executing_completed",
        "building_result_started",
        "building_result_completed",
        "finalizing_started",
        "finalizing_completed",
        "run_completed",
    ]
    assert all(event.run_id == _Paths().run_id for event in events)
    assert [event.timestamp for event in events] == sorted(
        event.timestamp for event in events
    )


def test_fatal_preflight_stops_execution_but_still_finalizes() -> None:
    harness = _Harness()
    cancellation = _CancellationProbe()
    events: list[LifecycleEvent] = []

    result = RunOrchestrator(harness.services(fatal_preflight=True)).run(
        _Config(),
        _Paths(),
        cancellation_check=cancellation,
        event_sink=events.append,
    )

    assert result == _Result("preflight_failure", finalized=True)
    assert cancellation.calls == 2
    assert harness.calls == [
        "plan",
        "preflight",
        "preflight_is_fatal",
        "build_preflight_failure_result",
        "finalize",
    ]
    failed_event = next(event for event in events if event.event == "preflight_failed")
    assert failed_event.level is EventLevel.ERROR
    assert failed_event.status == "FAILED"
    assert "executing_started" not in _event_names(events)


def test_cancellation_before_planning_builds_a_cancelled_result() -> None:
    harness = _Harness()
    cancellation = _CancellationProbe(cancel_on_call=1)
    events: list[LifecycleEvent] = []

    result = RunOrchestrator(harness.services()).run(
        _Config(),
        _Paths(),
        cancellation_check=cancellation,
        event_sink=events.append,
    )

    assert result == _Result("cancelled", finalized=True)
    assert harness.calls == ["build_cancelled_result", "finalize"]
    assert harness.cancelled_state == (None, None, None)
    assert harness.cancelled_failure is not None
    assert harness.cancelled_failure.phase == "initializing"
    assert harness.cancelled_failure.cancelled is True
    cancelled_event = next(event for event in events if event.event == "run_cancelled")
    assert cancelled_event.level is EventLevel.WARN
    assert cancelled_event.stage == "initializing"
    assert cancelled_event.status == "CANCELLED"


def test_cancellation_after_execution_preserves_partial_execution_state() -> None:
    harness = _Harness()
    cancellation = _CancellationProbe(cancel_on_call=4)

    result = RunOrchestrator(harness.services()).run(
        _Config(),
        _Paths(),
        cancellation_check=cancellation,
    )

    assert result == _Result("cancelled", finalized=True)
    assert harness.cancelled_state == (_Plan(), _Preflight(), _Execution())
    assert harness.cancelled_failure is not None
    assert harness.cancelled_failure.phase == "executing"
    assert isinstance(harness.cancelled_failure.exception, CancellationRequested)
    assert "build_completed_result" not in harness.calls


def test_execution_failure_becomes_a_fatal_result_with_partial_state() -> None:
    harness = _Harness()
    execution_error = RuntimeError("executor failed")
    harness.execution_error = execution_error
    events: list[LifecycleEvent] = []

    result = RunOrchestrator(harness.services()).run(
        _Config(),
        _Paths(),
        event_sink=events.append,
    )

    assert result == _Result("fatal", finalized=True)
    assert harness.fatal_state == (_Plan(), _Preflight(), None)
    assert harness.fatal_failure is not None
    assert harness.fatal_failure.phase == "executing"
    assert harness.fatal_failure.exception is execution_error
    failed_event = next(
        event for event in events if event.event == "run_orchestration_failed"
    )
    assert failed_event.level is EventLevel.FATAL
    assert failed_event.stage == "executing"
    assert failed_event.status == "ERROR"
    assert failed_event.message == "executor failed"


def test_completed_result_builder_failure_is_attributed_to_building_result() -> None:
    harness = _Harness()
    builder_error = RuntimeError("result builder failed")
    harness.completed_builder_error = builder_error

    result = RunOrchestrator(harness.services()).run(_Config(), _Paths())

    assert result == _Result("fatal", finalized=True)
    assert harness.fatal_state == (_Plan(), _Preflight(), _Execution())
    assert harness.fatal_failure is not None
    assert harness.fatal_failure.phase == "building_result"
    assert harness.fatal_failure.exception is builder_error


def test_event_sink_failure_never_changes_the_run_outcome() -> None:
    harness = _Harness()
    sink_calls = 0

    def failing_sink(event: LifecycleEvent) -> None:
        nonlocal sink_calls
        assert isinstance(event, LifecycleEvent)
        sink_calls += 1
        raise RuntimeError("presentation sink failed")

    result = RunOrchestrator(harness.services()).run(
        _Config(),
        _Paths(),
        event_sink=failing_sink,
    )

    assert result == _Result("completed", finalized=True)
    assert sink_calls > 0


def test_finalization_failure_is_propagated_when_orchestration_succeeded() -> None:
    harness = _Harness()
    finalizer_error = RuntimeError("finalization failed")
    harness.finalizer_error = finalizer_error
    events: list[LifecycleEvent] = []

    with pytest.raises(RuntimeError, match="finalization failed") as raised:
        RunOrchestrator(harness.services()).run(
            _Config(),
            _Paths(),
            event_sink=events.append,
        )

    assert raised.value is finalizer_error
    finalization_event = next(
        event for event in events if event.event == "run_finalization_failed"
    )
    assert finalization_event.level is EventLevel.FATAL
    assert finalization_event.stage == "finalizing"
    assert "run_completed" not in _event_names(events)


def test_finalization_failure_after_orchestration_failure_preserves_both_causes() -> None:
    harness = _Harness()
    execution_error = RuntimeError("execution failed")
    finalizer_error = OSError("finalization failed")
    harness.execution_error = execution_error
    harness.finalizer_error = finalizer_error

    with pytest.raises(ExceptionGroup) as raised:
        RunOrchestrator(harness.services()).run(_Config(), _Paths())

    assert raised.value.message == "run orchestration and finalization failed"
    assert raised.value.exceptions == (execution_error, finalizer_error)


def test_cancelled_result_builder_failure_preserves_cancellation_and_builder_error() -> None:
    harness = _Harness()
    builder_error = RuntimeError("cancelled result failed")
    harness.cancelled_builder_error = builder_error

    with pytest.raises(ExceptionGroup) as raised:
        RunOrchestrator(harness.services()).run(
            _Config(),
            _Paths(),
            cancellation_check=_CancellationProbe(cancel_on_call=1),
        )

    assert raised.value.message == "cancellation result construction failed"
    assert isinstance(raised.value.exceptions[0], CancellationRequested)
    assert raised.value.exceptions[1] is builder_error
    assert "finalize" not in harness.calls


def test_fatal_result_builder_failure_preserves_original_and_builder_error() -> None:
    harness = _Harness()
    execution_error = RuntimeError("execution failed")
    builder_error = OSError("fatal result failed")
    harness.execution_error = execution_error
    harness.fatal_builder_error = builder_error

    with pytest.raises(ExceptionGroup) as raised:
        RunOrchestrator(harness.services()).run(_Config(), _Paths())

    assert raised.value.message == "fatal run-result construction failed"
    assert raised.value.exceptions == (execution_error, builder_error)
    assert "finalize" not in harness.calls


def test_run_validation_delegates_to_the_same_orchestration_contract() -> None:
    harness = _Harness()
    clock = _Clock()

    result = run_validation(
        _Config(),
        _Paths(),
        harness.services(),
        clock=clock,
    )

    assert result == _Result("completed", finalized=True)
    assert clock.calls > 0


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("plan", None),
        ("preflight", None),
        ("preflight_is_fatal", None),
        ("execute", None),
        ("build_completed_result", None),
        ("build_preflight_failure_result", None),
        ("build_cancelled_result", None),
        ("build_fatal_result", None),
        ("finalize", None),
    ],
)
def test_service_bundle_rejects_non_callable_members(
    field_name: str,
    replacement: object,
) -> None:
    services = _Harness().services()

    with pytest.raises(TypeError, match=rf"^{field_name} must be callable$"):
        replace(services, **{field_name: replacement})


def test_orchestrator_rejects_invalid_callbacks_and_run_id() -> None:
    orchestrator = RunOrchestrator(_Harness().services())

    with pytest.raises(TypeError, match="cancellation_check must be callable or None"):
        orchestrator.run(_Config(), _Paths(), cancellation_check=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="event_sink must be callable or None"):
        orchestrator.run(_Config(), _Paths(), event_sink=object())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="run_paths.run_id must be a non-empty string"):
        orchestrator.run(_Config(), _Paths(run_id=" "))


def test_clock_must_return_a_timezone_aware_datetime() -> None:
    harness = _Harness()

    with pytest.raises(ValueError, match="clock must return a timezone-aware datetime"):
        RunOrchestrator(
            harness.services(),
            clock=lambda: datetime(2026, 7, 25, 12, 0),
        ).run(_Config(), _Paths())

    with pytest.raises(TypeError, match="clock must return a datetime"):
        RunOrchestrator(
            harness.services(),
            clock=lambda: "not-a-datetime",  # type: ignore[arg-type,return-value]
        ).run(_Config(), _Paths())


def test_failure_model_normalizes_time_and_validates_contract() -> None:
    local_time = datetime.fromisoformat("2026-07-25T08:00:00-04:00")
    error = RuntimeError("failed")

    failure = OrchestrationFailure(
        phase="executing",
        occurred_at=local_time,
        exception=error,
    )

    assert failure.occurred_at == _STARTED_AT
    assert failure.exception is error
    assert failure.cancelled is False

    with pytest.raises(ValueError, match="phase must be a non-empty string"):
        OrchestrationFailure(" ", _STARTED_AT, error)

    with pytest.raises(ValueError, match="occurred_at must be timezone-aware"):
        OrchestrationFailure(
            "executing",
            datetime(2026, 7, 25, 12, 0),
            error,
        )
