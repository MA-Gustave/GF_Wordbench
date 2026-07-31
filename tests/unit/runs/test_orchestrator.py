"""Unit tests for complete-run orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Final

import pytest

from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.kernel.events import EventLevel, LifecycleEvent
from gf_wordbench.runs.orchestrator import (
    OrchestrationFailure,
    RunOrchestrationServices,
    RunOrchestrator,
    run_validation,
)

_FIXED_TIME: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _Paths:
    run_id: str = "20260725_120000"


@dataclass(slots=True)
class _Harness:
    trace: list[str] = field(default_factory=list)
    plans: list[object] = field(default_factory=list)
    preflights: list[object] = field(default_factory=list)
    executions: list[object] = field(default_factory=list)
    failures: list[OrchestrationFailure] = field(default_factory=list)
    fatal_preflight: bool = False
    final_suffix: str = ":final"
    fail_phase: str | None = None
    cancellation_phase: str | None = None
    finalize_error: Exception | None = None
    cancelled_builder_error: Exception | None = None
    fatal_builder_error: Exception | None = None

    def plan(self, config: object, paths: object) -> object:
        self.trace.append("plan")
        self._raise_for("planning")
        value = ("plan", config, paths)
        self.plans.append(value)
        return value

    def preflight(
        self,
        config: object,
        paths: object,
        plan: object,
    ) -> object:
        self.trace.append("preflight")
        self._raise_for("preflight")
        value = ("preflight", config, paths, plan)
        self.preflights.append(value)
        return value

    def preflight_is_fatal(self, preflight: object) -> bool:
        self.trace.append("preflight_is_fatal")
        self._raise_for("preflight_is_fatal")
        assert preflight is self.preflights[-1]
        return self.fatal_preflight

    def execute(
        self,
        config: object,
        paths: object,
        plan: object,
        preflight: object,
        cancellation_check: Any,
        event_sink: Any,
    ) -> object:
        self.trace.append("execute")
        self._raise_for("executing")
        if self.cancellation_phase == "inside_execute":
            raise CancellationRequested("cancelled inside execute")
        value = (
            "execution",
            config,
            paths,
            plan,
            preflight,
            cancellation_check,
            event_sink,
        )
        self.executions.append(value)
        return value

    def build_completed_result(
        self,
        config: object,
        paths: object,
        plan: object,
        preflight: object,
        execution: object,
    ) -> str:
        self.trace.append("build_completed_result")
        self._raise_for("building_result")
        assert plan is self.plans[-1]
        assert preflight is self.preflights[-1]
        assert execution is self.executions[-1]
        return "completed"

    def build_preflight_failure_result(
        self,
        config: object,
        paths: object,
        plan: object,
        preflight: object,
    ) -> str:
        del config, paths
        self.trace.append("build_preflight_failure_result")
        assert plan is self.plans[-1]
        assert preflight is self.preflights[-1]
        return "preflight-failure"

    def build_cancelled_result(
        self,
        config: object,
        paths: object,
        plan: object | None,
        preflight: object | None,
        execution: object | None,
        failure: OrchestrationFailure,
    ) -> str:
        del config, paths, plan, preflight, execution
        self.trace.append("build_cancelled_result")
        self.failures.append(failure)
        if self.cancelled_builder_error is not None:
            raise self.cancelled_builder_error
        return "cancelled"

    def build_fatal_result(
        self,
        config: object,
        paths: object,
        plan: object | None,
        preflight: object | None,
        execution: object | None,
        failure: OrchestrationFailure,
    ) -> str:
        del config, paths, plan, preflight, execution
        self.trace.append("build_fatal_result")
        self.failures.append(failure)
        if self.fatal_builder_error is not None:
            raise self.fatal_builder_error
        return "fatal"

    def finalize(self, result: str) -> str:
        self.trace.append(f"finalize:{result}")
        if self.finalize_error is not None:
            raise self.finalize_error
        return result + self.final_suffix

    def services(
        self,
    ) -> RunOrchestrationServices[
        object,
        object,
        object,
        object,
        object,
        str,
    ]:
        return RunOrchestrationServices(
            plan=self.plan,
            preflight=self.preflight,
            preflight_is_fatal=self.preflight_is_fatal,
            execute=self.execute,
            build_completed_result=self.build_completed_result,
            build_preflight_failure_result=(
                self.build_preflight_failure_result
            ),
            build_cancelled_result=self.build_cancelled_result,
            build_fatal_result=self.build_fatal_result,
            finalize=self.finalize,
        )

    def _raise_for(self, phase: str) -> None:
        if self.fail_phase == phase:
            raise RuntimeError(f"{phase} failed")


class _Clock:
    def __init__(self, *values: object) -> None:
        self.values = iter(values)
        self.calls = 0

    def __call__(self) -> object:
        self.calls += 1
        return next(self.values)


def _orchestrator(
    harness: _Harness,
    *,
    clock: Any = lambda: _FIXED_TIME,
) -> RunOrchestrator[object, object, object, object, object, str]:
    return RunOrchestrator(services=harness.services(), clock=clock)


def _event_names(events: list[LifecycleEvent]) -> list[str]:
    return [event.event for event in events]


def test_successful_run_executes_each_phase_once_in_order() -> None:
    harness = _Harness()
    events: list[LifecycleEvent] = []
    cancellation_checks: list[str] = []

    result = _orchestrator(harness).run(
        {"mode": "diagnostic"},
        _Paths(),
        cancellation_check=lambda: cancellation_checks.append("checked"),
        event_sink=events.append,
    )

    assert result == "completed:final"
    assert cancellation_checks == ["checked", "checked", "checked", "checked"]
    assert harness.trace == [
        "plan",
        "preflight",
        "preflight_is_fatal",
        "execute",
        "build_completed_result",
        "finalize:completed",
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
    assert all(event.run_id == "20260725_120000" for event in events)
    assert all(event.operation == "orchestrate_run" for event in events)


def test_successful_phase_events_have_canonical_levels_and_statuses() -> None:
    harness = _Harness()
    events: list[LifecycleEvent] = []

    _orchestrator(harness).run(object(), _Paths(), event_sink=events.append)

    by_name = {event.event: event for event in events}
    assert by_name["run_started"].level is EventLevel.INFO
    assert by_name["run_started"].status is None
    for phase in (
        "planning",
        "preflight",
        "executing",
        "building_result",
        "finalizing",
    ):
        started = by_name[f"{phase}_started"]
        completed = by_name[f"{phase}_completed"]
        assert started.stage == phase
        assert started.status == "STARTED"
        assert completed.stage == phase
        assert completed.status == "COMPLETED"
        assert started.level is EventLevel.INFO
        assert completed.level is EventLevel.INFO


def test_fatal_preflight_skips_execution_and_builds_preflight_result() -> None:
    harness = _Harness(fatal_preflight=True)
    events: list[LifecycleEvent] = []

    result = _orchestrator(harness).run(
        object(),
        _Paths(),
        event_sink=events.append,
    )

    assert result == "preflight-failure:final"
    assert harness.trace == [
        "plan",
        "preflight",
        "preflight_is_fatal",
        "build_preflight_failure_result",
        "finalize:preflight-failure",
    ]
    assert _event_names(events) == [
        "run_started",
        "planning_started",
        "planning_completed",
        "preflight_started",
        "preflight_failed",
        "finalizing_started",
        "finalizing_completed",
        "run_completed",
    ]
    failed = next(event for event in events if event.event == "preflight_failed")
    assert failed.level is EventLevel.ERROR
    assert failed.status == "FAILED"


@pytest.mark.parametrize(
    ("raise_on_call", "expected_phase", "expected_trace"),
    (
        (1, "initializing", []),
        (2, "planning", ["plan"]),
        (
            3,
            "preflight",
            ["plan", "preflight", "preflight_is_fatal"],
        ),
        (
            4,
            "executing",
            [
                "plan",
                "preflight",
                "preflight_is_fatal",
                "execute",
            ],
        ),
    ),
)
def test_cancellation_checks_create_cancelled_results(
    raise_on_call: int,
    expected_phase: str,
    expected_trace: list[str],
) -> None:
    harness = _Harness()
    calls = 0
    events: list[LifecycleEvent] = []

    def check() -> None:
        nonlocal calls
        calls += 1
        if calls == raise_on_call:
            raise CancellationRequested("stop requested")

    result = _orchestrator(harness).run(
        object(),
        _Paths(),
        cancellation_check=check,
        event_sink=events.append,
    )

    assert result == "cancelled:final"
    assert harness.trace[:-2] == expected_trace
    assert harness.trace[-2:] == [
        "build_cancelled_result",
        "finalize:cancelled",
    ]
    failure = harness.failures[-1]
    assert failure.phase == expected_phase
    assert failure.cancelled is True
    assert isinstance(failure.exception, CancellationRequested)

    event = next(item for item in events if item.event == "run_cancelled")
    assert event.level is EventLevel.WARN
    assert event.stage == expected_phase
    assert event.status == "CANCELLED"
    assert event.message == "stop requested"


def test_cancellation_raised_by_execution_preserves_completed_context() -> None:
    harness = _Harness(cancellation_phase="inside_execute")

    result = _orchestrator(harness).run(object(), _Paths())

    assert result == "cancelled:final"
    assert harness.failures[-1].phase == "executing"
    assert harness.plans
    assert harness.preflights
    assert harness.executions == []


@pytest.mark.parametrize(
    ("fail_phase", "expected_phase"),
    (
        ("planning", "planning"),
        ("preflight", "preflight"),
        ("preflight_is_fatal", "preflight"),
        ("executing", "executing"),
        ("building_result", "building_result"),
    ),
)
def test_phase_exceptions_become_finalizable_fatal_results(
    fail_phase: str,
    expected_phase: str,
) -> None:
    harness = _Harness(fail_phase=fail_phase)
    events: list[LifecycleEvent] = []

    result = _orchestrator(harness).run(
        object(),
        _Paths(),
        event_sink=events.append,
    )

    assert result == "fatal:final"
    failure = harness.failures[-1]
    assert failure.phase == expected_phase
    assert failure.cancelled is False
    assert isinstance(failure.exception, RuntimeError)

    event = next(
        item for item in events
        if item.event == "run_orchestration_failed"
    )
    assert event.level is EventLevel.FATAL
    assert event.stage == expected_phase
    assert event.status == "ERROR"


def test_non_boolean_preflight_decision_is_a_contract_failure() -> None:
    harness = _Harness()
    services = harness.services()
    invalid = RunOrchestrationServices(
        plan=services.plan,
        preflight=services.preflight,
        preflight_is_fatal=lambda value: 1,  # type: ignore[return-value]
        execute=services.execute,
        build_completed_result=services.build_completed_result,
        build_preflight_failure_result=(
            services.build_preflight_failure_result
        ),
        build_cancelled_result=services.build_cancelled_result,
        build_fatal_result=services.build_fatal_result,
        finalize=services.finalize,
    )

    result = RunOrchestrator(
        services=invalid,
        clock=lambda: _FIXED_TIME,
    ).run(object(), _Paths())

    assert result == "fatal:final"
    failure = harness.failures[-1]
    assert failure.phase == "preflight"
    assert isinstance(failure.exception, TypeError)
    assert str(failure.exception) == "preflight_is_fatal must return a bool"


def test_cancelled_result_builder_failure_preserves_both_errors() -> None:
    builder_error = RuntimeError("cancelled builder failed")
    harness = _Harness(cancelled_builder_error=builder_error)

    with pytest.raises(ExceptionGroup) as captured:
        _orchestrator(harness).run(
            object(),
            _Paths(),
            cancellation_check=lambda: (_ for _ in ()).throw(
                CancellationRequested("cancelled")
            ),
        )

    group = captured.value
    assert str(group).startswith("cancellation result construction failed")
    assert len(group.exceptions) == 2
    assert isinstance(group.exceptions[0], CancellationRequested)
    assert group.exceptions[1] is builder_error
    assert all(not item.startswith("finalize:") for item in harness.trace)


def test_fatal_result_builder_failure_preserves_both_errors() -> None:
    builder_error = RuntimeError("fatal builder failed")
    harness = _Harness(
        fail_phase="planning",
        fatal_builder_error=builder_error,
    )

    with pytest.raises(ExceptionGroup) as captured:
        _orchestrator(harness).run(object(), _Paths())

    group = captured.value
    assert str(group).startswith("fatal run-result construction failed")
    assert len(group.exceptions) == 2
    assert isinstance(group.exceptions[0], RuntimeError)
    assert group.exceptions[1] is builder_error
    assert all(not item.startswith("finalize:") for item in harness.trace)


def test_finalization_error_after_success_is_re_raised() -> None:
    finalization_error = OSError("cannot publish reports")
    harness = _Harness(finalize_error=finalization_error)
    events: list[LifecycleEvent] = []

    with pytest.raises(OSError) as captured:
        _orchestrator(harness).run(
            object(),
            _Paths(),
            event_sink=events.append,
        )

    assert captured.value is finalization_error
    assert _event_names(events)[-2:] == [
        "finalizing_started",
        "run_finalization_failed",
    ]
    event = events[-1]
    assert event.level is EventLevel.FATAL
    assert event.stage == "finalizing"
    assert event.status == "ERROR"


def test_finalization_error_after_primary_failure_is_grouped() -> None:
    finalization_error = OSError("cannot finalize")
    harness = _Harness(
        fail_phase="planning",
        finalize_error=finalization_error,
    )

    with pytest.raises(ExceptionGroup) as captured:
        _orchestrator(harness).run(object(), _Paths())

    group = captured.value
    assert str(group).startswith("run orchestration and finalization failed")
    assert len(group.exceptions) == 2
    assert group.exceptions[0] is harness.failures[-1].exception
    assert group.exceptions[1] is finalization_error


def test_event_sink_failures_never_change_run_outcome() -> None:
    harness = _Harness()
    calls = 0

    def broken_sink(event: LifecycleEvent) -> None:
        nonlocal calls
        del event
        calls += 1
        raise RuntimeError("consumer unavailable")

    result = _orchestrator(harness).run(
        object(),
        _Paths(),
        event_sink=broken_sink,
    )

    assert result == "completed:final"
    assert calls == 12


def test_failure_messages_are_nul_safe_and_bounded() -> None:
    harness = _Harness()
    services = harness.services()
    long_message = "bad\x00" + ("x" * 2_000)

    def fail_plan(config: object, paths: object) -> object:
        del config, paths
        raise RuntimeError(long_message)

    overridden = RunOrchestrationServices(
        plan=fail_plan,
        preflight=services.preflight,
        preflight_is_fatal=services.preflight_is_fatal,
        execute=services.execute,
        build_completed_result=services.build_completed_result,
        build_preflight_failure_result=(
            services.build_preflight_failure_result
        ),
        build_cancelled_result=services.build_cancelled_result,
        build_fatal_result=services.build_fatal_result,
        finalize=services.finalize,
    )
    events: list[LifecycleEvent] = []

    result = RunOrchestrator(
        services=overridden,
        clock=lambda: _FIXED_TIME,
    ).run(object(), _Paths(), event_sink=events.append)

    assert result == "fatal:final"
    message = next(
        event.message
        for event in events
        if event.event == "run_orchestration_failed"
    )
    assert len(message) == 1_024
    assert "\x00" not in message
    assert "�" in message


def test_clock_values_are_normalized_to_utc() -> None:
    local_time = datetime(
        2026,
        7,
        25,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    harness = _Harness()
    events: list[LifecycleEvent] = []

    _orchestrator(harness, clock=lambda: local_time).run(
        object(),
        _Paths(),
        event_sink=events.append,
    )

    assert all(event.timestamp == _FIXED_TIME for event in events)
    assert all(event.timestamp.tzinfo is UTC for event in events)


@pytest.mark.parametrize(
    ("clock", "exception_type", "message"),
    (
        (lambda: "not a datetime", TypeError, "clock must return a datetime"),
        (
            lambda: datetime(2026, 7, 25, 12, 0),
            ValueError,
            "clock must return a timezone-aware datetime",
        ),
    ),
)
def test_invalid_clock_results_are_rejected_before_services_run(
    clock: Any,
    exception_type: type[Exception],
    message: str,
) -> None:
    harness = _Harness()

    with pytest.raises(exception_type, match=message):
        _orchestrator(harness, clock=clock).run(object(), _Paths())

    assert harness.trace == []


@pytest.mark.parametrize("run_id", ("", "   ", "bad\x00id", 42))
def test_invalid_run_ids_are_rejected_before_events(
    run_id: object,
) -> None:
    harness = _Harness()
    events: list[LifecycleEvent] = []

    with pytest.raises(
        ValueError,
        match="run_paths.run_id must be a non-empty string",
    ):
        _orchestrator(harness).run(
            object(),
            _Paths(run_id=run_id),  # type: ignore[arg-type]
            event_sink=events.append,
        )

    assert harness.trace == []
    assert events == []


def test_paths_without_run_id_are_supported() -> None:
    harness = _Harness()
    events: list[LifecycleEvent] = []

    result = _orchestrator(harness).run(
        object(),
        object(),
        event_sink=events.append,
    )

    assert result == "completed:final"
    assert all(event.run_id is None for event in events)


@pytest.mark.parametrize(
    ("keyword", "value", "message"),
    (
        (
            "cancellation_check",
            object(),
            "cancellation_check must be callable or None",
        ),
        (
            "event_sink",
            object(),
            "event_sink must be callable or None",
        ),
    ),
)
def test_run_rejects_non_callable_optional_callbacks(
    keyword: str,
    value: object,
    message: str,
) -> None:
    harness = _Harness()
    arguments = {keyword: value}

    with pytest.raises(TypeError, match=message):
        _orchestrator(harness).run(
            object(),
            _Paths(),
            **arguments,  # type: ignore[arg-type]
        )

    assert harness.trace == []


@pytest.mark.parametrize(
    "field_name",
    (
        "plan",
        "preflight",
        "preflight_is_fatal",
        "execute",
        "build_completed_result",
        "build_preflight_failure_result",
        "build_cancelled_result",
        "build_fatal_result",
        "finalize",
    ),
)
def test_services_require_every_callback_to_be_callable(
    field_name: str,
) -> None:
    harness = _Harness()
    values = {
        "plan": harness.plan,
        "preflight": harness.preflight,
        "preflight_is_fatal": harness.preflight_is_fatal,
        "execute": harness.execute,
        "build_completed_result": harness.build_completed_result,
        "build_preflight_failure_result": (
            harness.build_preflight_failure_result
        ),
        "build_cancelled_result": harness.build_cancelled_result,
        "build_fatal_result": harness.build_fatal_result,
        "finalize": harness.finalize,
    }
    values[field_name] = None

    with pytest.raises(TypeError, match=f"{field_name} must be callable"):
        RunOrchestrationServices(**values)  # type: ignore[arg-type]


def test_orchestrator_validates_services_and_clock() -> None:
    with pytest.raises(
        TypeError,
        match="services must be RunOrchestrationServices",
    ):
        RunOrchestrator(services=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="clock must be callable"):
        RunOrchestrator(
            services=_Harness().services(),
            clock=object(),  # type: ignore[arg-type]
        )


def test_orchestration_failure_is_immutable_and_normalizes_timestamp() -> None:
    local_time = datetime(
        2026,
        7,
        25,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    error = RuntimeError("failure")

    failure = OrchestrationFailure(
        phase="executing",
        occurred_at=local_time,
        exception=error,
        cancelled=False,
    )

    assert failure.phase == "executing"
    assert failure.occurred_at == _FIXED_TIME
    assert failure.occurred_at.tzinfo is UTC
    assert failure.exception is error
    assert failure.cancelled is False

    with pytest.raises(AttributeError):
        failure.phase = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "exception_type"),
    (
        (
            {
                "phase": "",
                "occurred_at": _FIXED_TIME,
                "exception": RuntimeError(),
            },
            ValueError,
        ),
        (
            {
                "phase": "bad\x00phase",
                "occurred_at": _FIXED_TIME,
                "exception": RuntimeError(),
            },
            ValueError,
        ),
        (
            {
                "phase": "planning",
                "occurred_at": datetime(2026, 7, 25, 12, 0),
                "exception": RuntimeError(),
            },
            ValueError,
        ),
        (
            {
                "phase": "planning",
                "occurred_at": _FIXED_TIME,
                "exception": "error",
            },
            TypeError,
        ),
        (
            {
                "phase": "planning",
                "occurred_at": _FIXED_TIME,
                "exception": RuntimeError(),
                "cancelled": 1,
            },
            TypeError,
        ),
    ),
)
def test_orchestration_failure_rejects_invalid_values(
    kwargs: dict[str, object],
    exception_type: type[Exception],
) -> None:
    with pytest.raises(exception_type):
        OrchestrationFailure(**kwargs)  # type: ignore[arg-type]


def test_run_validation_facade_uses_the_same_orchestration_contract() -> None:
    harness = _Harness()
    events: list[LifecycleEvent] = []

    result = run_validation(
        {"mode": "release"},
        _Paths(),
        harness.services(),
        event_sink=events.append,
        clock=lambda: _FIXED_TIME,
    )

    assert result == "completed:final"
    assert harness.trace[-1] == "finalize:completed"
    assert events[0].event == "run_started"
    assert events[-1].event == "run_completed"
