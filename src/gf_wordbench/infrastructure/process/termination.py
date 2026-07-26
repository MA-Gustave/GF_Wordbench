"""Bounded, platform-aware termination of an owned process."""

from __future__ import annotations

import math
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import IO, Final, Protocol, TypeAlias

Seconds: TypeAlias = float

DEFAULT_FORCE_WAIT_SEC: Final[Seconds] = 5.0
DEFAULT_POLL_INTERVAL_SEC: Final[Seconds] = 0.05


class CancellationToken(Protocol):
    """Minimal cooperative-cancellation surface consumed by process runners."""

    def is_cancelled(self) -> bool: ...

    def reason(self) -> str | None: ...


class ContainmentKind(StrEnum):
    """Process containment mechanism established by the launcher."""

    POSIX_PROCESS_GROUP = "posix_process_group"
    WINDOWS_PROCESS_GROUP = "windows_process_group"
    ROOT_PROCESS = "root_process"


@dataclass(frozen=True, slots=True)
class ProcessContainment:
    """Immutable process-containment facts created at launch time."""

    kind: ContainmentKind
    identifier: int
    process_tree_contained: bool

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ContainmentKind):
            raise TypeError("kind must be a ContainmentKind")
        if isinstance(self.identifier, bool) or not isinstance(self.identifier, int):
            raise TypeError("identifier must be an integer")
        if self.identifier <= 0:
            raise ValueError("identifier must be greater than zero")
        if not isinstance(self.process_tree_contained, bool):
            raise TypeError("process_tree_contained must be a boolean")
        if self.kind is ContainmentKind.ROOT_PROCESS and self.process_tree_contained:
            raise ValueError("root-process containment cannot claim tree containment")


@dataclass(frozen=True, slots=True)
class TerminationOutcome:
    """Structured evidence produced by one termination sequence."""

    soft_termination_attempted: bool
    forced_termination_attempted: bool
    termination_succeeded: bool
    process_tree_contained: bool
    termination_error: str | None

    def __post_init__(self) -> None:
        for name in (
            "soft_termination_attempted",
            "forced_termination_attempted",
            "termination_succeeded",
            "process_tree_contained",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")

        if self.termination_error is None:
            return
        if not isinstance(self.termination_error, str):
            raise TypeError("termination_error must be a string or None")
        if not self.termination_error.strip():
            raise ValueError("termination_error must not be empty")


class TerminableProcess(Protocol):
    """Minimal subprocess surface required by this module."""

    pid: int
    stdin: IO[bytes] | IO[str] | None

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def send_signal(self, sig: int) -> None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


class _ErrorCollector:
    __slots__ = ("_messages",)

    def __init__(self) -> None:
        self._messages: list[str] = []

    def add(self, phase: str, error: BaseException) -> None:
        message = str(error).strip() or error.__class__.__name__
        self._messages.append(f"{phase}: {message}")

    def add_message(self, phase: str, message: str) -> None:
        self._messages.append(f"{phase}: {message}")

    def render(self) -> str | None:
        return "; ".join(self._messages) or None


def terminate_owned_processes(
    process: TerminableProcess,
    *,
    containment: ProcessContainment,
    grace_sec: Seconds,
    force_wait_sec: Seconds = DEFAULT_FORCE_WAIT_SEC,
    poll_interval_sec: Seconds = DEFAULT_POLL_INTERVAL_SEC,
) -> TerminationOutcome:
    """Terminate an owned process using a finite soft-to-force escalation."""

    _validate_process(process)

    grace = _validated_duration(
        "grace_sec",
        grace_sec,
        allow_zero=True,
    )
    force_wait = _validated_duration(
        "force_wait_sec",
        force_wait_sec,
        allow_zero=False,
    )
    poll_interval = _validated_duration(
        "poll_interval_sec",
        poll_interval_sec,
        allow_zero=False,
    )

    _validate_containment(process, containment)

    if _is_stopped(process, containment):
        return _outcome(
            containment=containment,
            soft_attempted=False,
            forced_attempted=False,
            succeeded=True,
        )

    errors = _ErrorCollector()
    _close_stdin(process, errors)
    _request_soft_termination(process, containment, errors)

    if _wait_until_stopped(
        process,
        containment,
        timeout_sec=grace,
        poll_interval_sec=poll_interval,
    ):
        return _outcome(
            containment=containment,
            soft_attempted=True,
            forced_attempted=False,
            succeeded=True,
            error=errors.render(),
        )

    _request_forced_termination(process, containment, errors)

    succeeded = _wait_until_stopped(
        process,
        containment,
        timeout_sec=force_wait,
        poll_interval_sec=poll_interval,
    )

    if not succeeded:
        errors.add_message(
            "confirmation",
            "owned process termination could not be confirmed within policy limits",
        )

    return _outcome(
        containment=containment,
        soft_attempted=True,
        forced_attempted=True,
        succeeded=succeeded,
        error=errors.render(),
    )


def _outcome(
    *,
    containment: ProcessContainment,
    soft_attempted: bool,
    forced_attempted: bool,
    succeeded: bool,
    error: str | None = None,
) -> TerminationOutcome:
    return TerminationOutcome(
        soft_termination_attempted=soft_attempted,
        forced_termination_attempted=forced_attempted,
        termination_succeeded=succeeded,
        process_tree_contained=containment.process_tree_contained,
        termination_error=error,
    )


def _validate_process(process: TerminableProcess) -> None:
    pid = getattr(process, "pid", None)
    if isinstance(pid, bool) or not isinstance(pid, int):
        raise TypeError("process.pid must be an integer")
    if pid <= 0:
        raise ValueError("process.pid must be greater than zero")

    for method_name in ("poll", "wait", "send_signal", "terminate", "kill"):
        if not callable(getattr(process, method_name, None)):
            raise TypeError(f"process.{method_name} must be callable")


def _validated_duration(
    name: str,
    value: object,
    *,
    allow_zero: bool,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")

    duration = float(value)
    if not math.isfinite(duration):
        raise ValueError(f"{name} must be finite")

    if duration < 0 or (duration == 0 and not allow_zero):
        relation = "non-negative" if allow_zero else "greater than zero"
        raise ValueError(f"{name} must be {relation}")

    return duration


def _validate_containment(
    process: TerminableProcess,
    containment: ProcessContainment,
) -> None:
    if not isinstance(containment, ProcessContainment):
        raise TypeError("containment must be a ProcessContainment")

    if containment.identifier != process.pid:
        label = (
            "root-process containment identifier"
            if containment.kind is ContainmentKind.ROOT_PROCESS
            else "owned process-group identifier"
        )
        raise ValueError(f"{label} must equal process.pid")

    if containment.kind is ContainmentKind.ROOT_PROCESS:
        return

    if containment.kind is ContainmentKind.POSIX_PROCESS_GROUP:
        if os.name == "nt":
            raise ValueError("POSIX containment cannot be used on Windows")

        try:
            own_group = os.getpgrp()
        except OSError as error:
            raise ValueError(
                "unable to validate POSIX process-group containment"
            ) from error

        if containment.identifier == own_group:
            raise ValueError("refusing to terminate the current process group")

        return

    if os.name != "nt":
        raise ValueError("Windows containment cannot be used on this platform")


def _close_stdin(
    process: TerminableProcess,
    errors: _ErrorCollector,
) -> None:
    stream = process.stdin
    if stream is None or stream.closed:
        return

    try:
        stream.close()
    except (OSError, ValueError) as error:
        errors.add("stdin_close", error)


def _request_soft_termination(
    process: TerminableProcess,
    containment: ProcessContainment,
    errors: _ErrorCollector,
) -> None:
    try:
        if containment.kind is ContainmentKind.POSIX_PROCESS_GROUP:
            os.killpg(containment.identifier, signal.SIGTERM)
        elif containment.kind is ContainmentKind.WINDOWS_PROCESS_GROUP:
            ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
            if ctrl_break is None:
                raise RuntimeError("CTRL_BREAK_EVENT is unavailable")
            process.send_signal(ctrl_break)
        else:
            process.terminate()
    except (OSError, RuntimeError, ValueError) as error:
        if not _is_stopped(process, containment):
            errors.add("soft_termination", error)


def _request_forced_termination(
    process: TerminableProcess,
    containment: ProcessContainment,
    errors: _ErrorCollector,
) -> None:
    try:
        if containment.kind is ContainmentKind.POSIX_PROCESS_GROUP:
            os.killpg(containment.identifier, signal.SIGKILL)
        else:
            process.kill()
    except (OSError, RuntimeError, ValueError) as error:
        if not _is_stopped(process, containment):
            errors.add("forced_termination", error)


def _wait_until_stopped(
    process: TerminableProcess,
    containment: ProcessContainment,
    *,
    timeout_sec: float,
    poll_interval_sec: float,
) -> bool:
    deadline = time.monotonic() + timeout_sec

    while True:
        _reap_if_available(process)

        if _is_stopped(process, containment):
            return True

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False

        time.sleep(min(poll_interval_sec, remaining))


def _reap_if_available(process: TerminableProcess) -> None:
    if process.poll() is None:
        return

    try:
        process.wait(timeout=0)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _is_stopped(
    process: TerminableProcess,
    containment: ProcessContainment,
) -> bool:
    root_stopped = process.poll() is not None

    if containment.kind is not ContainmentKind.POSIX_PROCESS_GROUP:
        return root_stopped

    return root_stopped and not _posix_group_exists(containment.identifier)


def _posix_group_exists(group_id: int) -> bool:
    try:
        os.killpg(group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

    return True


__all__ = (
    "CancellationToken",
    "ContainmentKind",
    "DEFAULT_FORCE_WAIT_SEC",
    "DEFAULT_POLL_INTERVAL_SEC",
    "ProcessContainment",
    "TerminableProcess",
    "TerminationOutcome",
    "terminate_owned_processes",
)