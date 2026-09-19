"""Unit tests for generic process-runner orchestration and evidence assembly."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
import sys
from types import MappingProxyType, SimpleNamespace
from typing import Literal, cast

import pytest

from gf_wordbench.infrastructure.environment import PreparedEnvironment
from gf_wordbench.infrastructure.process import runner as process_runner
from gf_wordbench.infrastructure.process.launcher import ProcessHandle
from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    CancellationReason,
    ProcessErrorKind,
    ProcessEvent,
    ProcessInput,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.termination import (
    ContainmentKind,
    ProcessContainment,
    TerminationOutcome,
)
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import ExecutionState

_FIXED_TIME = datetime(2026, 7, 25, 19, 30, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _StreamSummary:
    size_bytes: int


@dataclass(frozen=True, slots=True)
class _CaptureSummary:
    stdout: _StreamSummary
    stderr: _StreamSummary
    output_limit_exceeded: bool = False
    capture_complete: bool = True
    failures: tuple[object, ...] = ()


@dataclass(slots=True)
class _CaptureSession:
    summary: _CaptureSummary
    output_limit_exceeded: bool = False
    stdout: object = field(default_factory=object)
    stderr: object = field(default_factory=object)
    flush_count: int = 0
    finalize_count: int = 0

    def flush(self) -> None:
        self.flush_count += 1

    def finalize(self) -> _CaptureSummary:
        self.finalize_count += 1
        return self.summary


@dataclass(slots=True)
class _EventRecorder:
    events: list[ProcessEvent] = field(default_factory=list)

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)


@dataclass(slots=True)
class _CancellationToken:
    cancelled: bool
    reason_value: str | None

    def is_cancelled(self) -> bool:
        return self.cancelled

    def reason(self) -> str | None:
        return self.reason_value


@dataclass(slots=True)
class _FakeProcess:
    pid: int = 4321
    exit_code: int | None = None
    stdin: object | None = None

    def poll(self) -> int | None:
        return self.exit_code


@contextmanager
def _capture_context(capture: _CaptureSession) -> Iterator[_CaptureSession]:
    yield capture


def _request(
    tmp_path: Path,
    *,
    stdin: ProcessInput | None = None,
    expected_artifacts: tuple[ArtifactExpectation, ...] = (),
    env_overrides: Mapping[str, str] | None = None,
    sensitive_env_keys: frozenset[str] = frozenset(),
) -> ProcessRequest:
    root = tmp_path.resolve()
    capture_root = root / "capture"
    capture_root.mkdir(exist_ok=True)
    executable = Path(sys.executable).resolve()

    return ProcessRequest(
        request_id="unit-process-runner",
        tool_id="python-test-helper",
        operation_id="unit-process-runner",
        operation_kind=ProcessOperationKind.OPTIONAL_TOOL,
        executable=executable,
        args=("-c", "raise SystemExit(7)"),
        cwd=root,
        stdout_path=(capture_root / "stdout.bin").resolve(),
        stderr_path=(capture_root / "stderr.bin").resolve(),
        timeout_sec=10.0,
        termination_grace_sec=0.25,
        output_limit_bytes=1024 * 1024,
        approved_read_roots=(root, executable.parent),
        approved_write_roots=(root,),
        evidence_policy="unit-test-evidence-v1",
        stdin=ProcessInput.none() if stdin is None else stdin,
        env_overrides={} if env_overrides is None else env_overrides,
        sensitive_env_keys=sensitive_env_keys,
        expected_artifacts=expected_artifacts,
        metadata={"test_case": "process_runner"},
    )


def _prepared_environment() -> PreparedEnvironment:
    return PreparedEnvironment(
        policy="controlled-inherit-v1",
        values=MappingProxyType({"PATH": "/controlled/bin"}),
        recorded_overrides=MappingProxyType({"TOKEN": "<redacted>"}),
    )


def _install_capture(
    monkeypatch: pytest.MonkeyPatch,
    capture: _CaptureSession,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def open_capture_session(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return _capture_context(capture)

    monkeypatch.setattr(
        process_runner,
        "open_capture_session",
        open_capture_session,
    )
    return calls


def _install_clock(
    monkeypatch: pytest.MonkeyPatch,
    *monotonic_values: float,
) -> None:
    values = iter(monotonic_values)
    monkeypatch.setattr(process_runner, "_utc_now", lambda: _FIXED_TIME)
    monkeypatch.setattr(
        process_runner,
        "time",
        SimpleNamespace(monotonic=lambda: next(values)),
    )


def _install_completed_execution(
    monkeypatch: pytest.MonkeyPatch,
    *,
    exit_code: int = 7,
    pid: int = 4321,
) -> None:
    def execute(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return process_runner._ExecutionFacts(
            execution_state=ExecutionState.COMPLETED,
            exit_code=exit_code,
            pid=pid,
            process_tree_contained=True,
        )

    monkeypatch.setattr(process_runner, "_launch_and_monitor", execute)


def test_run_process_invalid_request_fails_before_environment_or_capture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    def reject(_: ProcessRequest) -> None:
        raise ContractViolationError("invalid request")

    def unexpected(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("side effect occurred before request validation")

    monkeypatch.setattr(process_runner, "validate_process_request", reject)
    monkeypatch.setattr(process_runner, "build_child_environment", unexpected)
    monkeypatch.setattr(process_runner, "open_capture_session", unexpected)

    with pytest.raises(ContractViolationError, match="invalid request"):
        process_runner.run_process(request)


def test_run_process_completed_builds_canonical_result_and_observes_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifact_file = tmp_path / "artifacts" / "result.pgf"
    artifact_file.parent.mkdir()
    artifact_file.write_bytes(b"PGF\x00payload")
    artifact_directory = tmp_path / "artifacts" / "bundle"
    artifact_directory.mkdir()
    wrong_kind = tmp_path / "artifacts" / "directory-as-file"
    wrong_kind.mkdir()
    missing = tmp_path / "artifacts" / "missing.bin"

    expectations = (
        ArtifactExpectation(
            path=artifact_file,
            role="pgf",
            required=True,
            kind=ArtifactKind.FILE,
            minimum_size_bytes=1,
        ),
        ArtifactExpectation(
            path=artifact_directory,
            role="bundle",
            required=False,
            kind=ArtifactKind.DIRECTORY,
        ),
        ArtifactExpectation(
            path=wrong_kind,
            role="wrong-kind",
            required=False,
            kind=ArtifactKind.FILE,
        ),
        ArtifactExpectation(
            path=missing,
            role="missing",
            required=False,
            kind=ArtifactKind.FILE,
        ),
    )
    request = _request(
        tmp_path,
        expected_artifacts=expectations,
        env_overrides={"TOKEN": "secret"},
        sensitive_env_keys=frozenset({"TOKEN"}),
    )
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(13),
            stderr=_StreamSummary(5),
        )
    )
    capture_calls = _install_capture(monkeypatch, capture)
    prepared = _prepared_environment()
    environment_calls: list[dict[str, object]] = []

    def build_environment(**kwargs: object) -> PreparedEnvironment:
        environment_calls.append(dict(kwargs))
        return prepared

    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        build_environment,
    )
    _install_completed_execution(monkeypatch)
    _install_clock(monkeypatch, 100.0, 100.125)
    events = _EventRecorder()

    result = process_runner.run_process(request, event_sink=events)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 7
    assert result.pid == 4321
    assert result.started_at == _FIXED_TIME
    assert result.finished_at == _FIXED_TIME
    assert result.duration_ms == 125
    assert result.stdout_size_bytes == 13
    assert result.stderr_size_bytes == 5
    assert result.total_output_size_bytes == 18
    assert result.capture_complete is True
    assert result.recorded_env_overrides == {"TOKEN": "<redacted>"}
    assert result.environment_policy == "controlled-inherit-v1"

    assert environment_calls == [
        {
            "policy": request.environment_policy,
            "overrides": request.env_overrides,
            "sensitive_keys": request.sensitive_env_keys,
        }
    ]
    assert capture_calls == [
        {
            "stdout_path": request.stdout_path,
            "stderr_path": request.stderr_path,
            "output_limit_bytes": request.output_limit_bytes,
        }
    ]
    assert capture.flush_count == 1
    assert capture.finalize_count == 1

    observations = {item.role: item for item in result.artifact_observations}
    assert observations["pgf"].exists is True
    assert observations["pgf"].kind_matches is True
    assert observations["pgf"].size_bytes == len(b"PGF\x00payload")
    assert observations["bundle"].exists is True
    assert observations["bundle"].kind_matches is True
    assert observations["bundle"].size_bytes is None
    assert observations["wrong-kind"].exists is True
    assert observations["wrong-kind"].kind_matches is False
    assert observations["wrong-kind"].size_bytes is None
    assert observations["missing"].exists is False
    assert observations["missing"].kind_matches is False
    assert observations["missing"].size_bytes is None

    assert [event.name for event in events.events] == [
        "request_validated",
        "capture_opened",
        "capture_finalized",
    ]
    finalized = events.events[-1]
    assert finalized.execution_state is ExecutionState.COMPLETED
    assert finalized.pid == 4321
    assert finalized.details == {
        "stdout_size_bytes": 13,
        "stderr_size_bytes": 5,
        "output_limit_exceeded": False,
        "capture_complete": True,
        "capture_failure_count": 0,
    }


def test_run_process_prelaunch_cancellation_never_calls_launcher(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(0),
            stderr=_StreamSummary(0),
        )
    )
    _install_capture(monkeypatch, capture)
    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        lambda **kwargs: _prepared_environment(),
    )

    def unexpected(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("launcher called for prelaunch cancellation")

    monkeypatch.setattr(process_runner, "_launch_and_monitor", unexpected)
    _install_clock(monkeypatch, 10.0, 10.001)

    result = process_runner.run_process(
        request,
        cancellation_token=_CancellationToken(True, "user"),
    )

    assert result.execution_state is ExecutionState.CANCELLED
    assert result.cancellation_reason is CancellationReason.USER
    assert result.pid is None
    assert result.exit_code is None
    assert result.termination_attempted is False
    assert result.termination_succeeded is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True


@pytest.mark.parametrize("reason", (None, "", "   ", "unknown-controller"))
def test_run_process_unknown_prelaunch_cancellation_reason_uses_controller_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    reason: str | None,
) -> None:
    request = _request(tmp_path)
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(0),
            stderr=_StreamSummary(0),
        )
    )
    _install_capture(monkeypatch, capture)
    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        lambda **kwargs: _prepared_environment(),
    )
    _install_clock(monkeypatch, 1.0, 1.0)

    result = process_runner.run_process(
        request,
        cancellation_token=_CancellationToken(True, reason),
    )

    assert result.execution_state is ExecutionState.CANCELLED
    assert result.cancellation_reason is CancellationReason.CONTROLLER_POLICY


def test_run_process_launch_failure_is_structured_and_capture_is_finalized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(0),
            stderr=_StreamSummary(0),
        )
    )
    _install_capture(monkeypatch, capture)
    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        lambda **kwargs: _prepared_environment(),
    )

    def fail_launch(**kwargs: object) -> object:
        del kwargs
        raise FileNotFoundError("missing launch dependency")

    monkeypatch.setattr(process_runner, "launch_without_shell", fail_launch)
    _install_clock(monkeypatch, 5.0, 5.01)

    result = process_runner.run_process(request)

    assert result.execution_state is ExecutionState.LAUNCH_FAILED
    assert result.pid is None
    assert result.exit_code is None
    assert result.launch_error_kind is ProcessErrorKind.LAUNCH
    assert result.launch_error_message == ("executable or launch dependency was not found")
    assert result.termination_attempted is False
    assert result.termination_succeeded is False
    assert capture.flush_count == 1
    assert capture.finalize_count == 1


def test_run_process_event_sink_failure_does_not_change_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = _request(tmp_path)
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(1),
            stderr=_StreamSummary(2),
        )
    )
    _install_capture(monkeypatch, capture)
    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        lambda **kwargs: _prepared_environment(),
    )
    _install_completed_execution(monkeypatch, exit_code=0)
    _install_clock(monkeypatch, 8.0, 8.02)

    class FailingEventSink:
        def emit(self, _: ProcessEvent, /) -> None:
            raise OSError("event transport unavailable")

    result = process_runner.run_process(
        request,
        event_sink=FailingEventSink(),
    )

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert "process event sink failed" in caplog.text


def test_open_standard_input_none_yields_no_stream() -> None:
    with process_runner._open_standard_input(ProcessInput.none()) as stream:
        assert stream is None


def test_open_standard_input_text_encodes_exact_bytes() -> None:
    with process_runner._open_standard_input(
        ProcessInput.from_text("café 日本語\n", encoding="utf-8")
    ) as stream:
        assert stream is not None
        assert not isinstance(stream, int)
        assert stream.read() == "café 日本語\n".encode()


def test_open_standard_input_file_preserves_raw_bytes(tmp_path: Path) -> None:
    source = tmp_path / "stdin.bin"
    payload = b"alpha\x00\xffomega\r\n"
    source.write_bytes(payload)

    with process_runner._open_standard_input(ProcessInput.from_file(source)) as stream:
        assert stream is not None
        assert not isinstance(stream, int)
        assert stream.read() == payload


def test_internal_runner_failure_contains_launched_process_before_reraising(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    capture = _CaptureSession(
        _CaptureSummary(
            stdout=_StreamSummary(0),
            stderr=_StreamSummary(0),
        )
    )
    _install_capture(monkeypatch, capture)
    monkeypatch.setattr(
        process_runner,
        "build_child_environment",
        lambda **kwargs: _prepared_environment(),
    )
    process = _FakeProcess()
    monkeypatch.setattr(
        process_runner,
        "launch_without_shell",
        lambda **kwargs: process,
    )

    def fail_monitor(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise RuntimeError("monitor failed")

    monkeypatch.setattr(process_runner, "_monitor_process", fail_monitor)
    termination_calls: list[tuple[object, ProcessContainment, float]] = []

    def terminate(
        owned_process: object,
        *,
        containment: ProcessContainment,
        grace_sec: float,
    ) -> TerminationOutcome:
        termination_calls.append((owned_process, containment, grace_sec))
        return TerminationOutcome(
            soft_termination_attempted=True,
            forced_termination_attempted=False,
            termination_succeeded=True,
            process_tree_contained=containment.process_tree_contained,
            termination_error=None,
        )

    monkeypatch.setattr(process_runner, "terminate_owned_processes", terminate)
    monkeypatch.setattr(process_runner, "_utc_now", lambda: _FIXED_TIME)
    monkeypatch.setattr(
        process_runner,
        "time",
        SimpleNamespace(monotonic=lambda: 20.0),
    )

    with pytest.raises(RuntimeError, match="monitor failed"):
        process_runner.run_process(request)

    assert len(termination_calls) == 1
    owned_process, containment, grace_sec = termination_calls[0]
    assert owned_process is process
    assert containment.identifier == process.pid
    assert grace_sec == request.termination_grace_sec
    assert capture.finalize_count == 0


@pytest.mark.parametrize(
    ("cause", "expected_state", "expected_reason", "output_limited"),
    (
        ("timed_out", ExecutionState.TIMED_OUT, None, False),
        (
            "cancelled",
            ExecutionState.CANCELLED,
            CancellationReason.USER,
            False,
        ),
        (
            "output_limit",
            ExecutionState.CANCELLED,
            CancellationReason.OUTPUT_LIMIT,
            True,
        ),
    ),
)
def test_termination_causes_remain_distinct(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    cause: Literal["timed_out", "cancelled", "output_limit"],
    expected_state: ExecutionState,
    expected_reason: CancellationReason | None,
    output_limited: bool,
) -> None:
    request = _request(tmp_path)
    process = _FakeProcess(exit_code=-15)
    containment = ProcessContainment(
        kind=ContainmentKind.ROOT_PROCESS,
        identifier=process.pid,
        process_tree_contained=False,
    )
    outcome = TerminationOutcome(
        soft_termination_attempted=True,
        forced_termination_attempted=False,
        termination_succeeded=True,
        process_tree_contained=False,
        termination_error=None,
    )
    monkeypatch.setattr(
        process_runner,
        "terminate_owned_processes",
        lambda *args, **kwargs: outcome,
    )
    events = _EventRecorder()

    facts = process_runner._terminate_for_cause(
        request,
        cast("ProcessHandle", process),
        containment,
        cause,
        cancellation_token=_CancellationToken(True, "user"),
        event_sink=events,
    )

    assert facts.execution_state is expected_state
    assert facts.cancellation_reason is expected_reason
    assert facts.output_limit_exceeded is output_limited
    assert facts.pid == process.pid
    assert facts.exit_code == -15
    assert facts.soft_termination_attempted is True
    assert facts.forced_termination_attempted is False
    assert facts.termination_succeeded is True
    assert [event.name for event in events.events] == [
        "termination_requested",
        "termination_completed",
    ]
    assert events.events[0].details["cause"] == cause


def test_observe_artifact_records_only_generic_filesystem_facts(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "artifact.bin"
    file_path.write_bytes(b"abc")
    directory_path = tmp_path / "artifact-directory"
    directory_path.mkdir()
    missing_path = tmp_path / "missing.bin"

    file_observation = process_runner._observe_artifact(
        ArtifactExpectation(
            path=file_path,
            role="file",
            required=True,
            kind=ArtifactKind.FILE,
        )
    )
    directory_observation = process_runner._observe_artifact(
        ArtifactExpectation(
            path=directory_path,
            role="directory",
            required=False,
            kind=ArtifactKind.DIRECTORY,
        )
    )
    mismatch_observation = process_runner._observe_artifact(
        ArtifactExpectation(
            path=directory_path,
            role="mismatch",
            required=False,
            kind=ArtifactKind.FILE,
        )
    )
    missing_observation = process_runner._observe_artifact(
        ArtifactExpectation(
            path=missing_path,
            role="missing",
            required=False,
            kind=ArtifactKind.FILE,
        )
    )

    assert (
        file_observation.exists,
        file_observation.kind_matches,
        file_observation.size_bytes,
    ) == (True, True, 3)
    assert (
        directory_observation.exists,
        directory_observation.kind_matches,
        directory_observation.size_bytes,
    ) == (True, True, None)
    assert (
        mismatch_observation.exists,
        mismatch_observation.kind_matches,
        mismatch_observation.size_bytes,
    ) == (True, False, None)
    assert (
        missing_observation.exists,
        missing_observation.kind_matches,
        missing_observation.size_bytes,
    ) == (False, False, None)


def test_classify_launch_error_sanitizes_and_bounds_messages() -> None:
    kind, missing = process_runner._classify_launch_error(FileNotFoundError("secret path"))
    assert kind is ProcessErrorKind.LAUNCH
    assert missing == "executable or launch dependency was not found"

    _, denied = process_runner._classify_launch_error(PermissionError("private path"))
    assert denied == "permission was denied while launching the executable"

    _, generic = process_runner._classify_launch_error(OSError("unsafe\x00" + "x" * 2_000))
    assert "\x00" not in generic
    assert "\N{REPLACEMENT CHARACTER}" in generic
    assert len(generic) == process_runner._MAX_ERROR_MESSAGE_CHARS
    assert generic.endswith("…")


def test_duration_ms_is_non_negative_and_truncated_to_milliseconds() -> None:
    assert process_runner._duration_ms(10.0, 9.0) == 0
    assert process_runner._duration_ms(10.0, 10.1259) == 125
