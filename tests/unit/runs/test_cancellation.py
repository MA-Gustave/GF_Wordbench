"""Unit tests for cooperative run cancellation and structural adapters."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
import threading
from typing import Final

import pytest

from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.runs import cancellation
from gf_wordbench.runs.cancellation import (
    CancellationController,
    CancellationReason,
    CancellationSnapshot,
    cancellation_reason,
    cancellation_requested,
    create_cancellation_controller,
    raise_if_cancellation_requested,
)

_FIXED_UTC: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
_FIXED_MONOTONIC: Final[float] = 1234.5
_EXPECTED_PUBLIC_NAMES: Final[tuple[str, ...]] = (
    "CancellationCheck",
    "CancellationController",
    "CancellationReason",
    "CancellationSnapshot",
    "Clock",
    "UtcClock",
    "cancellation_reason",
    "cancellation_requested",
    "create_cancellation_controller",
    "raise_if_cancellation_requested",
)


class _ApplicationCancellationSource:
    def __init__(self, *, requested: object, reason: object = None) -> None:
        self._requested = requested
        self._reason = reason

    def is_cancellation_requested(self) -> object:
        return self._requested

    def cancellation_reason(self) -> object:
        return self._reason


class _ProcessCancellationToken:
    def __init__(self, *, cancelled: object, reason: object = None) -> None:
        self._cancelled = cancelled
        self._reason = reason

    def is_cancelled(self) -> object:
        return self._cancelled

    def reason(self) -> object:
        return self._reason


class _PropertyReasonSource:
    def __init__(self, reason: object) -> None:
        self.is_cancelled = lambda: True
        self.reason = reason


class _ClockSequence:
    def __init__(self, *values: object) -> None:
        self._values = iter(values)
        self.calls = 0

    def __call__(self) -> object:
        self.calls += 1
        return next(self._values)


def _controller() -> CancellationController:
    return CancellationController(
        monotonic_clock=lambda: _FIXED_MONOTONIC,
        utc_clock=lambda: _FIXED_UTC,
    )


def test_module_exposes_only_the_canonical_public_api() -> None:
    assert cancellation.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(cancellation, name) for name in cancellation.__all__)


def test_canonical_reasons_match_the_execution_contract() -> None:
    assert tuple(CancellationReason) == (
        CancellationReason.USER,
        CancellationReason.APPLICATION_SHUTDOWN,
        CancellationReason.OUTPUT_LIMIT,
        CancellationReason.CONTROLLER_POLICY,
    )
    assert tuple(reason.value for reason in CancellationReason) == (
        "user",
        "application_shutdown",
        "output_limit",
        "controller_policy",
    )


def test_fresh_controller_is_not_cancelled() -> None:
    controller = _controller()

    assert controller.is_cancellation_requested() is False
    assert controller.is_cancelled() is False
    assert controller.cancellation_reason() is None
    assert controller.reason() is None
    assert controller.requested_at is None
    assert controller.requested_at_monotonic is None
    assert controller.snapshot() == CancellationSnapshot(
        requested=False,
        reason=None,
        requested_at=None,
        requested_at_monotonic=None,
    )
    assert controller.wait(0) is False
    controller.check()


def test_first_request_wins_and_records_both_clocks_atomically() -> None:
    controller = _controller()

    assert controller.request(CancellationReason.USER) is True
    assert controller.request(CancellationReason.OUTPUT_LIMIT) is False
    assert controller.cancel(CancellationReason.APPLICATION_SHUTDOWN) is False

    assert controller.snapshot() == CancellationSnapshot(
        requested=True,
        reason="user",
        requested_at=_FIXED_UTC,
        requested_at_monotonic=_FIXED_MONOTONIC,
    )
    assert controller.is_cancellation_requested() is True
    assert controller.is_cancelled() is True
    assert controller.cancellation_reason() == "user"
    assert controller.reason() == "user"
    assert controller.wait(0) is True


def test_losing_requests_do_not_read_clocks_again() -> None:
    monotonic = _ClockSequence(10.0, 20.0)
    utc = _ClockSequence(_FIXED_UTC, _FIXED_UTC + timedelta(seconds=1))
    controller = CancellationController(
        monotonic_clock=monotonic,  # type: ignore[arg-type]
        utc_clock=utc,  # type: ignore[arg-type]
    )

    assert controller.request("first") is True
    assert controller.request("second") is False
    assert monotonic.calls == 1
    assert utc.calls == 1
    assert controller.reason() == "first"


def test_cancel_is_an_alias_for_request() -> None:
    controller = _controller()

    assert controller.cancel(CancellationReason.CONTROLLER_POLICY) is True
    assert controller.reason() == "controller_policy"


def test_factory_builds_independent_controllers() -> None:
    first = create_cancellation_controller(
        monotonic_clock=lambda: 1.0,
        utc_clock=lambda: _FIXED_UTC,
    )
    second = create_cancellation_controller(
        monotonic_clock=lambda: 2.0,
        utc_clock=lambda: _FIXED_UTC,
    )

    assert first is not second
    assert first.request("user") is True
    assert first.is_cancelled() is True
    assert second.is_cancelled() is False


def test_as_check_returns_a_stable_zero_argument_callback() -> None:
    controller = _controller()
    check = controller.as_check()

    check()
    controller.request(CancellationReason.USER)

    with pytest.raises(CancellationRequested):
        check()


def test_wait_is_released_when_cancellation_is_requested() -> None:
    controller = _controller()
    waiter_started = threading.Event()
    waiter_finished = threading.Event()
    observations: list[bool] = []

    def wait_for_cancellation() -> None:
        waiter_started.set()
        observations.append(controller.wait(1.0))
        waiter_finished.set()

    thread = threading.Thread(
        target=wait_for_cancellation,
        name="gf-wordbench-cancellation-unit-test",
        daemon=False,
    )
    thread.start()
    assert waiter_started.wait(1.0)

    assert controller.request(CancellationReason.USER) is True
    assert waiter_finished.wait(1.0)
    thread.join(1.0)

    assert not thread.is_alive()
    assert observations == [True]


def test_wait_timeout_returns_false_without_mutating_state() -> None:
    controller = _controller()

    assert controller.wait(0.001) is False
    assert controller.snapshot().requested is False


@pytest.mark.parametrize("timeout", (-1, -0.01, float("inf"), float("-inf"), float("nan")))
def test_wait_rejects_invalid_numeric_timeouts(timeout: float) -> None:
    with pytest.raises(ValueError):
        _controller().wait(timeout)


@pytest.mark.parametrize("timeout", (True, False, "1", object()))
def test_wait_rejects_non_numeric_timeouts(timeout: object) -> None:
    with pytest.raises(TypeError):
        _controller().wait(timeout)  # type: ignore[arg-type]


def test_raise_if_cancelled_preserves_structured_context() -> None:
    controller = _controller()
    controller.request(CancellationReason.OUTPUT_LIMIT)

    with pytest.raises(CancellationRequested) as captured:
        controller.raise_if_cancelled(
            message="Run cancelled during compilation.",
            stage="compile",
            operation="compile-module",
            subject="src/Main.gf",
            evidence_paths=("raw/compile/Main.stdout.log",),
        )

    error = captured.value
    assert error.message == "Run cancelled during compilation."
    assert str(error) == error.message
    assert error.detail == "Cancellation reason: output_limit."
    assert error.stage == "compile"
    assert error.operation == "compile-module"
    assert error.subject == "src/Main.gf"
    assert error.retryable is False
    assert error.evidence_paths == ("raw/compile/Main.stdout.log",)


def test_check_uses_the_canonical_default_message() -> None:
    controller = _controller()
    controller.request()

    with pytest.raises(CancellationRequested) as captured:
        controller.check()

    assert captured.value.message == "Cancellation requested."
    assert captured.value.detail == "Cancellation reason: user."


def test_snapshot_converts_aware_timestamp_to_utc() -> None:
    local_timestamp = datetime(
        2026,
        7,
        25,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    snapshot = CancellationSnapshot(
        requested=True,
        reason="user",
        requested_at=local_timestamp,
        requested_at_monotonic=1.0,
    )

    assert snapshot.requested_at == _FIXED_UTC
    assert snapshot.requested_at is not local_timestamp


@pytest.mark.parametrize(
    ("values", "expected_exception"),
    (
        (
            {
                "requested": 1,
                "reason": None,
                "requested_at": None,
                "requested_at_monotonic": None,
            },
            TypeError,
        ),
        (
            {
                "requested": True,
                "reason": None,
                "requested_at": _FIXED_UTC,
                "requested_at_monotonic": 1.0,
            },
            ValueError,
        ),
        (
            {
                "requested": True,
                "reason": "user",
                "requested_at": None,
                "requested_at_monotonic": 1.0,
            },
            ValueError,
        ),
        (
            {
                "requested": True,
                "reason": "user",
                "requested_at": _FIXED_UTC,
                "requested_at_monotonic": None,
            },
            ValueError,
        ),
        (
            {
                "requested": False,
                "reason": "user",
                "requested_at": None,
                "requested_at_monotonic": None,
            },
            ValueError,
        ),
    ),
)
def test_snapshot_rejects_inconsistent_state(
    values: dict[str, object],
    expected_exception: type[Exception],
) -> None:
    with pytest.raises(expected_exception):
        CancellationSnapshot(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("reason", ("", "   ", "bad\x00reason", "x" * 513))
def test_request_rejects_invalid_reasons(reason: str) -> None:
    with pytest.raises(ValueError):
        _controller().request(reason)


def test_request_rejects_non_string_reason() -> None:
    with pytest.raises(TypeError):
        _controller().request(1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "clock_value",
    (True, "1.0", float("inf"), float("-inf"), float("nan")),
)
def test_request_validates_monotonic_clock_output(clock_value: object) -> None:
    controller = CancellationController(
        monotonic_clock=lambda: clock_value,  # type: ignore[arg-type,return-value]
        utc_clock=lambda: _FIXED_UTC,
    )

    expected = TypeError if isinstance(clock_value, (bool, str)) else ValueError
    with pytest.raises(expected):
        controller.request()

    assert controller.is_cancelled() is False


@pytest.mark.parametrize(
    "clock_value",
    (
        "2026-07-25T12:00:00Z",
        datetime(2026, 7, 25, 12, 0),
    ),
)
def test_request_validates_utc_clock_output(clock_value: object) -> None:
    controller = CancellationController(
        monotonic_clock=lambda: 1.0,
        utc_clock=lambda: clock_value,  # type: ignore[arg-type,return-value]
    )

    expected = TypeError if isinstance(clock_value, str) else ValueError
    with pytest.raises(expected):
        controller.request()

    assert controller.is_cancelled() is False


def test_constructor_requires_callable_clocks() -> None:
    with pytest.raises(TypeError, match="monotonic_clock"):
        CancellationController(monotonic_clock=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="utc_clock"):
        CancellationController(utc_clock=1)  # type: ignore[arg-type]


def test_structural_state_reader_accepts_both_canonical_interfaces() -> None:
    assert cancellation_requested(None) is False
    assert cancellation_requested(_ApplicationCancellationSource(requested=True)) is True
    assert cancellation_requested(_ProcessCancellationToken(cancelled=False)) is False


def test_application_state_method_takes_precedence_over_process_alias() -> None:
    class Source:
        def is_cancellation_requested(self) -> bool:
            return False

        def is_cancelled(self) -> bool:
            raise AssertionError("fallback method must not be called")

    assert cancellation_requested(Source()) is False


def test_structural_state_reader_rejects_missing_or_invalid_methods() -> None:
    with pytest.raises(TypeError, match="must expose"):
        cancellation_requested(object())

    with pytest.raises(TypeError, match="must return bool"):
        cancellation_requested(_ApplicationCancellationSource(requested=1))


def test_structural_reason_reader_accepts_methods_properties_and_none() -> None:
    assert cancellation_reason(None) is None
    assert (
        cancellation_reason(
            _ApplicationCancellationSource(
                requested=True,
                reason="application_shutdown",
            )
        )
        == "application_shutdown"
    )
    assert (
        cancellation_reason(
            _ProcessCancellationToken(
                cancelled=True,
                reason=CancellationReason.OUTPUT_LIMIT,
            )
        )
        == "output_limit"
    )
    assert cancellation_reason(_PropertyReasonSource("controller_policy")) == ("controller_policy")


def test_application_reason_method_takes_precedence_over_process_alias() -> None:
    class Source:
        def cancellation_reason(self) -> str:
            return "user"

        def reason(self) -> str:
            raise AssertionError("fallback reason must not be called")

    assert cancellation_reason(Source()) == "user"


def test_structural_reason_reader_validates_returned_reason() -> None:
    with pytest.raises(TypeError):
        cancellation_reason(_PropertyReasonSource(1))

    with pytest.raises(ValueError):
        cancellation_reason(_PropertyReasonSource("   "))


def test_generic_raise_helper_is_a_noop_without_cancellation() -> None:
    raise_if_cancellation_requested(None)
    raise_if_cancellation_requested(_ApplicationCancellationSource(requested=False, reason="user"))


def test_generic_raise_helper_builds_the_canonical_exception() -> None:
    source = _ProcessCancellationToken(
        cancelled=True,
        reason=CancellationReason.APPLICATION_SHUTDOWN,
    )

    with pytest.raises(CancellationRequested) as captured:
        raise_if_cancellation_requested(
            source,
            message="Application shutdown interrupted the run.",
            stage="finalize",
            operation="write-reports",
            subject="run-001",
            evidence_paths=("summary.json", "manifest.json"),
        )

    error = captured.value
    assert error.message == "Application shutdown interrupted the run."
    assert error.detail == "Cancellation reason: application_shutdown."
    assert error.stage == "finalize"
    assert error.operation == "write-reports"
    assert error.subject == "run-001"
    assert error.retryable is False
    assert error.evidence_paths == ("summary.json", "manifest.json")


def test_generic_raise_helper_records_missing_reason_explicitly() -> None:
    source = _ProcessCancellationToken(cancelled=True, reason=None)

    with pytest.raises(CancellationRequested) as captured:
        raise_if_cancellation_requested(source)

    assert captured.value.detail == ("Cancellation was accepted without a supplied reason.")


@pytest.mark.parametrize(
    ("field", "value", "expected_exception"),
    (
        ("message", "", ValueError),
        ("message", "bad\x00message", ValueError),
        ("message", 1, TypeError),
        ("stage", "", ValueError),
        ("stage", "bad\x00stage", ValueError),
        ("stage", 1, TypeError),
        ("operation", "", ValueError),
        ("subject", "   ", ValueError),
    ),
)
def test_raise_helper_validates_exception_context(
    field: str,
    value: object,
    expected_exception: type[Exception],
) -> None:
    source = _ProcessCancellationToken(cancelled=True, reason="user")
    kwargs: dict[str, object] = {field: value}

    with pytest.raises(expected_exception):
        raise_if_cancellation_requested(source, **kwargs)  # type: ignore[arg-type]


def test_maximum_length_reason_is_preserved_in_state_and_detail() -> None:
    reason = "r" * 512
    controller = _controller()
    controller.request(reason)

    with pytest.raises(CancellationRequested) as captured:
        controller.check()

    assert controller.reason() == reason
    assert captured.value.detail == f"Cancellation reason: {reason}."
    assert len(captured.value.detail) < 4_096
