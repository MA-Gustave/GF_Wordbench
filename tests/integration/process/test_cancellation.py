"""Integration tests for cooperative process cancellation and bounded termination."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

from gf_wordbench.infrastructure.process import run_process
from gf_wordbench.infrastructure.process.models import (
    CancellationReason,
    ProcessEvent,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.kernel.statuses import ExecutionState


@dataclass(slots=True)
class _CancellationToken:
    cancelled: bool = False
    reason_value: str | None = None

    def cancel(self, reason: str = CancellationReason.USER.value) -> None:
        self.cancelled = True
        self.reason_value = reason

    def is_cancelled(self) -> bool:
        return self.cancelled

    def reason(self) -> str | None:
        return self.reason_value


@dataclass(slots=True)
class _EventCollector:
    events: list[ProcessEvent] = field(default_factory=list)

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)


@dataclass(slots=True)
class _CancelOnProcessStart(_EventCollector):
    token: _CancellationToken = field(default_factory=_CancellationToken)

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)
        if event.name == "process_started":
            self.token.cancel()


def _request(
    tmp_path: Path,
    *,
    operation_id: str,
    source: str,
    timeout_sec: float = 10.0,
) -> ProcessRequest:
    executable = Path(sys.executable).resolve()

    return ProcessRequest(
        request_id=f"request-{operation_id}",
        tool_id="python",
        operation_id=operation_id,
        operation_kind=ProcessOperationKind.OPTIONAL_TOOL,
        executable=executable,
        args=("-c", source),
        cwd=tmp_path.resolve(),
        stdout_path=(tmp_path / "stdout.log").resolve(),
        stderr_path=(tmp_path / "stderr.log").resolve(),
        timeout_sec=timeout_sec,
        approved_read_roots=(tmp_path.resolve(),),
        approved_write_roots=(tmp_path.resolve(),),
        evidence_policy="integration-test",
        termination_grace_sec=0.25,
        output_limit_bytes=1024 * 1024,
    )


def test_prelaunch_cancellation_does_not_start_a_process(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "launched.txt"
    token = _CancellationToken(
        cancelled=True,
        reason_value=CancellationReason.USER.value,
    )
    events = _EventCollector()

    result = run_process(
        _request(
            tmp_path,
            operation_id="prelaunch-cancellation",
            source=(
                "from pathlib import Path; "
                f"Path({str(marker)!r}).write_text('started', encoding='utf-8')"
            ),
        ),
        cancellation_token=token,
        event_sink=events,
    )

    assert result.execution_state is ExecutionState.CANCELLED
    assert result.cancelled is True
    assert result.timed_out is False
    assert result.cancellation_reason is CancellationReason.USER
    assert result.pid is None
    assert result.exit_code is None
    assert result.termination_attempted is False
    assert result.termination_succeeded is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True

    assert marker.exists() is False
    assert result.stdout_path.is_file()
    assert result.stderr_path.is_file()
    assert result.stdout_path.read_bytes() == b""
    assert result.stderr_path.read_bytes() == b""

    event_names = tuple(event.name for event in events.events)
    assert event_names == (
        "request_validated",
        "capture_opened",
        "capture_finalized",
    )
    assert all(event.pid is None for event in events.events)


def test_running_cancellation_terminates_the_owned_process(
    tmp_path: Path,
) -> None:
    token = _CancellationToken()
    events = _CancelOnProcessStart(token=token)

    result = run_process(
        _request(
            tmp_path,
            operation_id="running-cancellation",
            source=(
                "import sys, time; "
                "print('process-started', flush=True); "
                "print('stderr-started', file=sys.stderr, flush=True); "
                "time.sleep(60)"
            ),
        ),
        cancellation_token=token,
        event_sink=events,
    )

    assert token.is_cancelled() is True
    assert result.execution_state is ExecutionState.CANCELLED
    assert result.cancelled is True
    assert result.timed_out is False
    assert result.cancellation_reason is CancellationReason.USER
    assert result.pid is not None
    assert result.termination_attempted is True
    assert result.termination_succeeded is True
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True
    assert result.stdout_path.is_file()
    assert result.stderr_path.is_file()

    event_names = tuple(event.name for event in events.events)
    assert event_names == (
        "request_validated",
        "capture_opened",
        "process_started",
        "termination_requested",
        "termination_completed",
        "process_exited",
        "capture_finalized",
    )

    termination_requested = next(
        event for event in events.events if event.name == "termination_requested"
    )
    assert termination_requested.execution_state is ExecutionState.CANCELLED
    assert termination_requested.details["cause"] == "cancelled"

    termination_completed = next(
        event for event in events.events if event.name == "termination_completed"
    )
    assert termination_completed.details["termination_succeeded"] is True


def test_unknown_controller_reason_is_normalized_without_becoming_a_timeout(
    tmp_path: Path,
) -> None:
    token = _CancellationToken(
        cancelled=True,
        reason_value="operator-requested",
    )

    result = run_process(
        _request(
            tmp_path,
            operation_id="unknown-cancellation-reason",
            source="raise SystemExit(0)",
        ),
        cancellation_token=token,
    )

    assert result.execution_state is ExecutionState.CANCELLED
    assert result.cancellation_reason is CancellationReason.CONTROLLER_POLICY
    assert result.timed_out is False
    assert result.pid is None
    assert result.termination_attempted is False
