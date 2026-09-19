"""Integration tests for owned process-tree containment and termination."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Final

import pytest

from gf_wordbench.infrastructure.process import ProcessRequest, run_process
from gf_wordbench.infrastructure.process.models import ProcessOperationKind
from gf_wordbench.kernel.statuses import ExecutionState

if TYPE_CHECKING:
    from gf_wordbench.infrastructure.process.models import ProcessEvent, ProcessResult

pytestmark = pytest.mark.security

_PROCESS_SLEEP_SEC: Final = 30.0
_POSIX_TERMINATION_WAIT_SEC: Final = 5.0

_PARENT_SOURCE: Final = """\
from pathlib import Path
import subprocess
import sys
import time

child_script = Path(sys.argv[1])
pid_path = Path(sys.argv[2])
heartbeat_path = Path(sys.argv[3])
child = subprocess.Popen(
    [sys.executable, str(child_script), str(heartbeat_path)],
    stdin=subprocess.DEVNULL,
)
pid_path.write_text(str(child.pid), encoding="ascii")
print(f"child_pid={child.pid}", flush=True)
time.sleep(30)
"""

_CHILD_SOURCE: Final = """\
from pathlib import Path
import os
import sys
import time

heartbeat_path = Path(sys.argv[1])
print(f"child_started={os.getpid()}", flush=True)
while True:
    heartbeat_path.write_text(str(time.monotonic_ns()), encoding="ascii")
    time.sleep(0.05)
"""

_SLEEP_SOURCE: Final = """\
import time
print("owned-root-started", flush=True)
time.sleep(30)
"""


class _EventSink:
    """Collect process events without coupling the test to logging output."""

    def __init__(self) -> None:
        self.events: list[ProcessEvent] = []

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)

    def one(self, name: str) -> ProcessEvent:
        matches = [event for event in self.events if event.name == name]
        assert len(matches) == 1, (
            f"expected one {name!r} event, received {[event.name for event in self.events]!r}"
        )
        return matches[0]


def _request(
    *,
    workspace: Path,
    script: Path,
    operation_id: str,
    extra_args: tuple[str, ...] = (),
    timeout_sec: float,
) -> ProcessRequest:
    evidence_root = workspace / "evidence" / operation_id
    return ProcessRequest(
        request_id=operation_id,
        tool_id="python",
        operation_id=operation_id,
        operation_kind=ProcessOperationKind.OPTIONAL_TOOL,
        executable=Path(sys.executable).resolve(strict=True),
        args=(str(script), *extra_args),
        cwd=workspace,
        stdout_path=evidence_root / "stdout.bin",
        stderr_path=evidence_root / "stderr.bin",
        timeout_sec=timeout_sec,
        approved_read_roots=(workspace,),
        approved_write_roots=(workspace,),
        evidence_policy="complete",
        termination_grace_sec=0.5,
        mutability_class="run_artifacts_only",
    )


def _write_script(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8", newline="\n")
    return path


def _captured_evidence(result: ProcessResult) -> str:
    stdout = result.stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = result.stderr_path.read_text(encoding="utf-8", errors="replace")
    return f"stdout:\n{stdout}\n\nstderr:\n{stderr}"


def _posix_process_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

    proc_stat = Path(f"/proc/{pid}/stat")
    try:
        state = proc_stat.read_text(encoding="ascii").split()[2]
    except (IndexError, OSError, UnicodeError):
        return True
    return state != "Z"


def _wait_until_posix_process_stops(pid: int, *, timeout_sec: float) -> bool:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if not _posix_process_is_running(pid):
            return True
        time.sleep(0.05)
    return not _posix_process_is_running(pid)


def _kill_posix_pid_for_cleanup(pid: int) -> None:
    if not _posix_process_is_running(pid):
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def _stop_subprocess(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


@pytest.mark.posix
@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
def test_timeout_terminates_the_root_and_owned_child_process(
    tmp_path: Path,
) -> None:
    parent_script = _write_script(tmp_path / "parent.py", _PARENT_SOURCE)
    child_script = _write_script(tmp_path / "child.py", _CHILD_SOURCE)
    child_pid_path = tmp_path / "child.pid"
    heartbeat_path = tmp_path / "child.heartbeat"
    sink = _EventSink()

    request = _request(
        workspace=tmp_path,
        script=parent_script,
        operation_id="process-tree-timeout",
        extra_args=(str(child_script), str(child_pid_path), str(heartbeat_path)),
        timeout_sec=2.0,
    )

    child_pid: int | None = None
    try:
        result = run_process(request, event_sink=sink)
        evidence = _captured_evidence(result)

        assert result.execution_state is ExecutionState.TIMED_OUT, evidence
        assert result.termination_attempted, evidence
        assert result.termination_succeeded, evidence
        assert result.capture_complete, evidence
        assert child_pid_path.is_file(), evidence

        child_pid = int(child_pid_path.read_text(encoding="ascii"))
        assert child_pid > 0
        assert _wait_until_posix_process_stops(
            child_pid,
            timeout_sec=_POSIX_TERMINATION_WAIT_SEC,
        ), evidence

        started = sink.one("process_started")
        terminated = sink.one("termination_completed")
        exited = sink.one("process_exited")

        assert started.details["process_tree_contained"] is True
        assert terminated.details["process_tree_contained"] is True
        assert terminated.details["soft_termination_attempted"] is True
        assert terminated.details["termination_succeeded"] is True
        assert exited.execution_state is ExecutionState.TIMED_OUT
    finally:
        if child_pid is not None:
            _kill_posix_pid_for_cleanup(child_pid)


def test_termination_is_scoped_to_the_owned_process_tree(
    tmp_path: Path,
) -> None:
    owned_script = _write_script(tmp_path / "owned.py", _SLEEP_SOURCE)
    unrelated = subprocess.Popen(
        (
            sys.executable,
            "-c",
            f"import time; time.sleep({_PROCESS_SLEEP_SEC!r})",
        ),
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        request = _request(
            workspace=tmp_path,
            script=owned_script,
            operation_id="process-tree-scope",
            timeout_sec=0.75,
        )
        result = run_process(request)
        evidence = _captured_evidence(result)

        assert result.execution_state is ExecutionState.TIMED_OUT, evidence
        assert result.termination_attempted, evidence
        assert result.termination_succeeded, evidence
        assert unrelated.poll() is None, (
            "termination escaped the owned process tree and stopped an unrelated process"
        )
    finally:
        _stop_subprocess(unrelated)


@pytest.mark.windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows process groups")
def test_windows_reports_process_tree_containment_conservatively(
    tmp_path: Path,
) -> None:
    script = _write_script(tmp_path / "owned.py", _SLEEP_SOURCE)
    sink = _EventSink()
    request = _request(
        workspace=tmp_path,
        script=script,
        operation_id="windows-process-group",
        timeout_sec=0.75,
    )

    result = run_process(request, event_sink=sink)
    evidence = _captured_evidence(result)

    assert result.execution_state is ExecutionState.TIMED_OUT, evidence
    assert result.termination_attempted, evidence
    assert result.termination_succeeded, evidence
    assert sink.one("process_started").details["process_tree_contained"] is False
    assert sink.one("termination_completed").details["process_tree_contained"] is False
