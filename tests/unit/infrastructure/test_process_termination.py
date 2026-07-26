"""Unit tests for bounded, owned-process termination."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Final

import pytest

import gf_wordbench.infrastructure.process.termination as termination
from gf_wordbench.infrastructure.process.termination import (
    ContainmentKind,
    ProcessContainment,
    TerminationOutcome,
    terminate_owned_processes,
)

_PID: Final = 41_001


class _Stdin:
    def __init__(self, *, error: BaseException | None = None) -> None:
        self.closed = False
        self.close_calls = 0
        self._error = error

    def close(self) -> None:
        self.close_calls += 1
        self.closed = True
        if self._error is not None:
            raise self._error


@dataclass(slots=True)
class _Process:
    pid: int = _PID
    stdin: _Stdin | None = field(default_factory=_Stdin)
    running: bool = True
    return_code: int = 0
    stop_on_terminate: bool = True
    stop_on_signal: bool = True
    stop_on_kill: bool = True
    terminate_error: BaseException | None = None
    signal_error: BaseException | None = None
    kill_error: BaseException | None = None
    stop_before_terminate_error: bool = False
    stop_before_signal_error: bool = False
    stop_before_kill_error: bool = False
    terminate_calls: int = 0
    kill_calls: int = 0
    sent_signals: list[int] = field(default_factory=list)
    wait_timeouts: list[float | None] = field(default_factory=list)

    def poll(self) -> int | None:
        return None if self.running else self.return_code

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        if self.running:
            raise termination.subprocess.TimeoutExpired("fake", timeout)
        return self.return_code

    def send_signal(self, sig: int) -> None:
        self.sent_signals.append(sig)
        if self.stop_before_signal_error:
            self.running = False
        if self.signal_error is not None:
            raise self.signal_error
        if self.stop_on_signal:
            self.running = False

    def terminate(self) -> None:
        self.terminate_calls += 1
        if self.stop_before_terminate_error:
            self.running = False
        if self.terminate_error is not None:
            raise self.terminate_error
        if self.stop_on_terminate:
            self.running = False

    def kill(self) -> None:
        self.kill_calls += 1
        if self.stop_before_kill_error:
            self.running = False
        if self.kill_error is not None:
            raise self.kill_error
        if self.stop_on_kill:
            self.running = False


@dataclass(slots=True)
class _Clock:
    now: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        return self.now

    def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.now += duration


def _root_containment(
    process: _Process,
    *,
    tree_contained: bool = False,
) -> ProcessContainment:
    return ProcessContainment(
        kind=ContainmentKind.ROOT_PROCESS,
        identifier=process.pid,
        process_tree_contained=tree_contained,
    )


def _install_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> _Clock:
    clock = _Clock()
    monkeypatch.setattr(termination.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(termination.time, "sleep", clock.sleep)
    return clock


def test_already_stopped_process_requires_no_termination() -> None:
    process = _Process(running=False)

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=0.5,
    )

    assert outcome == TerminationOutcome(
        soft_termination_attempted=False,
        forced_termination_attempted=False,
        termination_succeeded=True,
        process_tree_contained=False,
        termination_error=None,
    )
    assert process.stdin is not None
    assert process.stdin.close_calls == 0
    assert process.terminate_calls == 0
    assert process.kill_calls == 0


def test_root_process_soft_termination_closes_stdin_and_succeeds() -> None:
    process = _Process(stop_on_terminate=True)

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=1.0,
    )

    assert outcome.soft_termination_attempted is True
    assert outcome.forced_termination_attempted is False
    assert outcome.termination_succeeded is True
    assert outcome.process_tree_contained is False
    assert outcome.termination_error is None
    assert process.stdin is not None
    assert process.stdin.closed is True
    assert process.stdin.close_calls == 1
    assert process.terminate_calls == 1
    assert process.kill_calls == 0
    assert process.wait_timeouts == [0]


def test_force_termination_runs_after_zero_grace_period() -> None:
    process = _Process(
        stop_on_terminate=False,
        stop_on_kill=True,
    )

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=0,
        force_wait_sec=1.0,
    )

    assert outcome.soft_termination_attempted is True
    assert outcome.forced_termination_attempted is True
    assert outcome.termination_succeeded is True
    assert outcome.termination_error is None
    assert process.terminate_calls == 1
    assert process.kill_calls == 1


def test_unconfirmed_force_termination_is_bounded_and_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _install_clock(monkeypatch)
    process = _Process(
        stop_on_terminate=False,
        stop_on_kill=False,
    )

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=0,
        force_wait_sec=0.2,
        poll_interval_sec=0.05,
    )

    assert outcome.soft_termination_attempted is True
    assert outcome.forced_termination_attempted is True
    assert outcome.termination_succeeded is False
    assert outcome.termination_error == (
        "confirmation: owned process termination could not be confirmed "
        "within policy limits"
    )
    assert clock.now == pytest.approx(0.2)
    assert all(duration <= 0.05 for duration in clock.sleeps)
    assert process.terminate_calls == 1
    assert process.kill_calls == 1


def test_cleanup_errors_are_preserved_in_deterministic_phase_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_clock(monkeypatch)
    process = _Process(
        stdin=_Stdin(error=OSError("stdin locked")),
        stop_on_terminate=False,
        stop_on_kill=False,
        terminate_error=OSError("soft denied"),
        kill_error=OSError("force denied"),
    )

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=0,
        force_wait_sec=0.1,
        poll_interval_sec=0.05,
    )

    assert outcome.termination_succeeded is False
    assert outcome.termination_error == (
        "stdin_close: stdin locked; "
        "soft_termination: soft denied; "
        "forced_termination: force denied; "
        "confirmation: owned process termination could not be confirmed "
        "within policy limits"
    )


def test_soft_signal_error_is_not_recorded_when_process_already_stopped() -> None:
    process = _Process(
        stop_on_terminate=False,
        terminate_error=OSError("raced with exit"),
        stop_before_terminate_error=True,
    )

    outcome = terminate_owned_processes(
        process,
        containment=_root_containment(process),
        grace_sec=1.0,
    )

    assert outcome.termination_succeeded is True
    assert outcome.forced_termination_attempted is False
    assert outcome.termination_error is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are unavailable")
def test_posix_soft_termination_targets_only_the_owned_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _Process(stop_on_terminate=False)
    calls: list[tuple[int, int]] = []

    def killpg(group_id: int, sig: int) -> None:
        calls.append((group_id, sig))
        if sig == termination.signal.SIGTERM:
            process.running = False
        elif sig == 0:
            raise ProcessLookupError

    monkeypatch.setattr(termination.os, "getpgrp", lambda: process.pid + 1)
    monkeypatch.setattr(termination.os, "killpg", killpg)

    containment = ProcessContainment(
        kind=ContainmentKind.POSIX_PROCESS_GROUP,
        identifier=process.pid,
        process_tree_contained=True,
    )
    outcome = terminate_owned_processes(
        process,
        containment=containment,
        grace_sec=1.0,
    )

    assert outcome.termination_succeeded is True
    assert outcome.forced_termination_attempted is False
    assert outcome.process_tree_contained is True
    assert calls == [
        (process.pid, termination.signal.SIGTERM),
        (process.pid, 0),
    ]
    assert process.terminate_calls == 0
    assert process.kill_calls == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are unavailable")
def test_posix_remaining_child_forces_group_kill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _Process(stop_on_terminate=False)
    group_alive = True
    calls: list[tuple[int, int]] = []

    def killpg(group_id: int, sig: int) -> None:
        nonlocal group_alive
        calls.append((group_id, sig))
        if sig == termination.signal.SIGTERM:
            process.running = False
        elif sig == termination.signal.SIGKILL:
            group_alive = False
        elif sig == 0 and not group_alive:
            raise ProcessLookupError

    monkeypatch.setattr(termination.os, "getpgrp", lambda: process.pid + 1)
    monkeypatch.setattr(termination.os, "killpg", killpg)

    outcome = terminate_owned_processes(
        process,
        containment=ProcessContainment(
            kind=ContainmentKind.POSIX_PROCESS_GROUP,
            identifier=process.pid,
            process_tree_contained=True,
        ),
        grace_sec=0,
        force_wait_sec=1.0,
    )

    assert outcome.termination_succeeded is True
    assert outcome.forced_termination_attempted is True
    assert calls == [
        (process.pid, termination.signal.SIGTERM),
        (process.pid, 0),
        (process.pid, termination.signal.SIGKILL),
        (process.pid, 0),
    ]


def test_windows_group_uses_ctrl_break_for_soft_termination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl_break = 0x1234
    process = _Process(stop_on_signal=True)
    monkeypatch.setattr(
        termination,
        "os",
        SimpleNamespace(name="nt"),
    )
    monkeypatch.setattr(
        termination,
        "signal",
        SimpleNamespace(CTRL_BREAK_EVENT=ctrl_break),
    )

    outcome = terminate_owned_processes(
        process,
        containment=ProcessContainment(
            kind=ContainmentKind.WINDOWS_PROCESS_GROUP,
            identifier=process.pid,
            process_tree_contained=True,
        ),
        grace_sec=1.0,
    )

    assert outcome.termination_succeeded is True
    assert outcome.forced_termination_attempted is False
    assert outcome.process_tree_contained is True
    assert process.sent_signals == [ctrl_break]
    assert process.terminate_calls == 0
    assert process.kill_calls == 0


def test_unavailable_windows_ctrl_break_escalates_and_records_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _Process(stop_on_kill=True)
    monkeypatch.setattr(
        termination,
        "os",
        SimpleNamespace(name="nt"),
    )
    monkeypatch.setattr(termination, "signal", SimpleNamespace())

    outcome = terminate_owned_processes(
        process,
        containment=ProcessContainment(
            kind=ContainmentKind.WINDOWS_PROCESS_GROUP,
            identifier=process.pid,
            process_tree_contained=True,
        ),
        grace_sec=0,
        force_wait_sec=1.0,
    )

    assert outcome.termination_succeeded is True
    assert outcome.forced_termination_attempted is True
    assert outcome.termination_error == (
        "soft_termination: CTRL_BREAK_EVENT is unavailable"
    )
    assert process.kill_calls == 1


@pytest.mark.parametrize(
    ("changes", "exception", "message"),
    [
        ({"kind": "root_process"}, TypeError, "kind must be a ContainmentKind"),
        ({"identifier": True}, TypeError, "identifier must be an integer"),
        ({"identifier": 0}, ValueError, "identifier must be greater than zero"),
        (
            {"process_tree_contained": 1},
            TypeError,
            "process_tree_contained must be a boolean",
        ),
        (
            {"process_tree_contained": True},
            ValueError,
            "root-process containment cannot claim tree containment",
        ),
    ],
)
def test_process_containment_rejects_invalid_facts(
    changes: dict[str, Any],
    exception: type[Exception],
    message: str,
) -> None:
    values: dict[str, Any] = {
        "kind": ContainmentKind.ROOT_PROCESS,
        "identifier": _PID,
        "process_tree_contained": False,
    }
    values.update(changes)

    with pytest.raises(exception, match=message):
        ProcessContainment(**values)


@pytest.mark.parametrize(
    ("changes", "exception", "message"),
    [
        (
            {"soft_termination_attempted": 1},
            TypeError,
            "soft_termination_attempted must be a boolean",
        ),
        (
            {"termination_error": 1},
            TypeError,
            "termination_error must be a string or None",
        ),
        (
            {"termination_error": "   "},
            ValueError,
            "termination_error must not be empty",
        ),
    ],
)
def test_termination_outcome_rejects_invalid_evidence(
    changes: dict[str, Any],
    exception: type[Exception],
    message: str,
) -> None:
    values: dict[str, Any] = {
        "soft_termination_attempted": True,
        "forced_termination_attempted": False,
        "termination_succeeded": True,
        "process_tree_contained": False,
        "termination_error": None,
    }
    values.update(changes)

    with pytest.raises(exception, match=message):
        TerminationOutcome(**values)


@pytest.mark.parametrize(
    ("field_name", "value", "exception", "message"),
    [
        ("grace_sec", True, TypeError, "grace_sec must be a real number"),
        ("grace_sec", -0.1, ValueError, "grace_sec must be non-negative"),
        ("grace_sec", float("inf"), ValueError, "grace_sec must be finite"),
        (
            "force_wait_sec",
            0,
            ValueError,
            "force_wait_sec must be greater than zero",
        ),
        (
            "poll_interval_sec",
            0,
            ValueError,
            "poll_interval_sec must be greater than zero",
        ),
    ],
)
def test_termination_durations_are_finite_and_bounded(
    field_name: str,
    value: object,
    exception: type[Exception],
    message: str,
) -> None:
    process = _Process()
    arguments: dict[str, object] = {
        "containment": _root_containment(process),
        "grace_sec": 1.0,
        "force_wait_sec": 1.0,
        "poll_interval_sec": 0.1,
    }
    arguments[field_name] = value

    with pytest.raises(exception, match=message):
        terminate_owned_processes(process, **arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("pid", "exception", "message"),
    [
        (True, TypeError, "process.pid must be an integer"),
        ("41001", TypeError, "process.pid must be an integer"),
        (0, ValueError, "process.pid must be greater than zero"),
    ],
)
def test_process_pid_is_validated(
    pid: Any,
    exception: type[Exception],
    message: str,
) -> None:
    process = _Process()
    process.pid = pid

    with pytest.raises(exception, match=message):
        terminate_owned_processes(
            process,
            containment=ProcessContainment(
                kind=ContainmentKind.ROOT_PROCESS,
                identifier=_PID,
                process_tree_contained=False,
            ),
            grace_sec=1.0,
        )


def test_missing_process_method_is_rejected() -> None:
    complete = _Process()
    process = SimpleNamespace(
        pid=complete.pid,
        stdin=complete.stdin,
        poll=complete.poll,
        wait=complete.wait,
        send_signal=complete.send_signal,
        terminate=complete.terminate,
        kill=None,
    )

    with pytest.raises(TypeError, match="process.kill must be callable"):
        terminate_owned_processes(
            process,
            containment=ProcessContainment(
                kind=ContainmentKind.ROOT_PROCESS,
                identifier=complete.pid,
                process_tree_contained=False,
            ),
            grace_sec=1.0,
        )


def test_containment_identifier_must_match_owned_process() -> None:
    process = _Process()

    with pytest.raises(
        ValueError,
        match="root-process containment identifier must equal process.pid",
    ):
        terminate_owned_processes(
            process,
            containment=ProcessContainment(
                kind=ContainmentKind.ROOT_PROCESS,
                identifier=process.pid + 1,
                process_tree_contained=False,
            ),
            grace_sec=1.0,
        )


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only safety invariant")
def test_current_posix_process_group_is_never_targeted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _Process()
    monkeypatch.setattr(termination.os, "getpgrp", lambda: process.pid)

    with pytest.raises(
        ValueError,
        match="refusing to terminate the current process group",
    ):
        terminate_owned_processes(
            process,
            containment=ProcessContainment(
                kind=ContainmentKind.POSIX_PROCESS_GROUP,
                identifier=process.pid,
                process_tree_contained=True,
            ),
            grace_sec=1.0,
        )


def test_platform_incompatible_containment_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _Process()
    monkeypatch.setattr(
        termination,
        "os",
        SimpleNamespace(name="posix"),
    )

    with pytest.raises(
        ValueError,
        match="Windows containment cannot be used on this platform",
    ):
        terminate_owned_processes(
            process,
            containment=ProcessContainment(
                kind=ContainmentKind.WINDOWS_PROCESS_GROUP,
                identifier=process.pid,
                process_tree_contained=True,
            ),
            grace_sec=1.0,
        )


def test_public_termination_surface_has_one_canonical_owner() -> None:
    assert termination.__all__ == (
        "CancellationToken",
        "ContainmentKind",
        "DEFAULT_FORCE_WAIT_SEC",
        "DEFAULT_POLL_INTERVAL_SEC",
        "ProcessContainment",
        "TerminableProcess",
        "TerminationOutcome",
        "terminate_owned_processes",
    )
    assert not hasattr(termination, "terminate_process_tree")
