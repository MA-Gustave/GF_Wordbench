"""Integration tests for bounded process timeout handling."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from gf_wordbench.infrastructure.process import ProcessRequest, run_process
from gf_wordbench.infrastructure.process.models import (
    ProcessEvent,
    ProcessOperationKind,
)
from gf_wordbench.kernel.statuses import ExecutionState


@dataclass(slots=True)
class _EventRecorder:
    events: list[ProcessEvent] = field(default_factory=list)

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)


def _request(
    tmp_path: Path,
    *,
    script: str,
    timeout_sec: float,
    termination_grace_sec: float = 0.25,
) -> ProcessRequest:
    root = tmp_path.resolve()
    executable = Path(sys.executable).resolve()
    return ProcessRequest(
        request_id="integration.process.timeout",
        tool_id="python-test-helper",
        operation_id="integration.process.timeout",
        operation_kind=ProcessOperationKind.OPTIONAL_TOOL,
        executable=executable,
        args=("-u", "-c", script),
        cwd=root,
        stdout_path=root / "stdout.txt",
        stderr_path=root / "stderr.txt",
        timeout_sec=timeout_sec,
        termination_grace_sec=termination_grace_sec,
        output_limit_bytes=1024 * 1024,
        approved_read_roots=(root, executable.parent),
        approved_write_roots=(root,),
        evidence_policy="integration-test-evidence-v1",
        metadata={"test_case": "timeout"},
    )


def _event_names(recorder: _EventRecorder) -> tuple[str, ...]:
    return tuple(event.name for event in recorder.events)


def test_timeout_terminates_process_and_preserves_partial_evidence(
    tmp_path: Path,
) -> None:
    script = (
        "import sys, time\n"
        "print('stdout-before-timeout', flush=True)\n"
        "print('stderr-before-timeout', file=sys.stderr, flush=True)\n"
        "time.sleep(30)\n"
        "print('stdout-after-sleep', flush=True)\n"
    )
    recorder = _EventRecorder()
    request = _request(
        tmp_path,
        script=script,
        timeout_sec=0.30,
    )

    started = time.monotonic()
    result = run_process(request, event_sink=recorder)
    elapsed = time.monotonic() - started

    assert result.execution_state is ExecutionState.TIMED_OUT
    assert result.pid is not None
    assert result.cancellation_reason is None
    assert result.launch_error_kind is None
    assert result.launch_error_message == ""
    assert result.termination_attempted is True
    assert result.termination_succeeded is True
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True
    assert result.started_at <= result.finished_at
    assert 0 <= result.duration_ms < 10_000
    assert 0.20 <= elapsed < 10.0

    assert result.stdout_path == request.stdout_path
    assert result.stderr_path == request.stderr_path
    assert result.stdout_path.is_file()
    assert result.stderr_path.is_file()
    assert result.stdout_size_bytes == result.stdout_path.stat().st_size
    assert result.stderr_size_bytes == result.stderr_path.stat().st_size

    stdout = result.stdout_path.read_text(encoding="utf-8")
    stderr = result.stderr_path.read_text(encoding="utf-8")
    assert "stdout-before-timeout" in stdout
    assert "stderr-before-timeout" in stderr
    assert "stdout-after-sleep" not in stdout

    assert _event_names(recorder) == (
        "request_validated",
        "capture_opened",
        "process_started",
        "termination_requested",
        "termination_completed",
        "process_exited",
        "capture_finalized",
    )

    termination_requested = recorder.events[3]
    termination_completed = recorder.events[4]
    process_exited = recorder.events[5]

    assert termination_requested.execution_state is ExecutionState.TIMED_OUT
    assert termination_requested.details["cause"] == "timed_out"
    assert termination_completed.execution_state is ExecutionState.TIMED_OUT
    assert termination_completed.details["termination_succeeded"] is True
    assert process_exited.execution_state is ExecutionState.TIMED_OUT
    assert process_exited.details["termination_succeeded"] is True


def test_fast_nonzero_exit_remains_completed_instead_of_timed_out(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        script=(
            "import sys\n"
            "print('ordinary-failure', file=sys.stderr, flush=True)\n"
            "raise SystemExit(23)\n"
        ),
        timeout_sec=5.0,
    )

    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 23
    assert result.pid is not None
    assert result.cancellation_reason is None
    assert result.termination_attempted is False
    assert result.termination_succeeded is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True
    assert result.stdout_path.read_bytes() == b""
    assert "ordinary-failure" in result.stderr_path.read_text(encoding="utf-8")
