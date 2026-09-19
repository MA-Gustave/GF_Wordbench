"""Deterministic test doubles for the GF Wordbench process boundary.

All factories return real production ``ProcessResult`` values.  The helpers
model generic execution facts only and never assign GF, validation, diagnostic,
or reporting semantics.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
import stat
from threading import RLock
from typing import Final, Protocol, TypeAlias, TypedDict, Unpack, cast

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
    CancellationReason,
    ProcessErrorKind,
    ProcessEvent,
    ProcessEventSink,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.infrastructure.process.termination import CancellationToken
from gf_wordbench.kernel.statuses import ExecutionState

__all__ = (
    "DEFAULT_DURATION_MS",
    "DEFAULT_PID",
    "DEFAULT_STARTED_AT",
    "FakeCancellationToken",
    "FakeProcessRunner",
    "ProcessCall",
    "ProcessOutcomeFactory",
    "ProcessResultOverrides",
    "RecordingProcessEventSink",
    "make_cancelled_process_result",
    "make_completed_process_result",
    "make_launch_failed_process_result",
    "make_output_limited_process_result",
    "make_process_result",
    "make_timed_out_process_result",
)

DEFAULT_STARTED_AT: Final = datetime(2026, 1, 1, tzinfo=UTC)
DEFAULT_DURATION_MS: Final = 25
DEFAULT_PID: Final = 4200
_UNSET: Final = object()

StreamContent: TypeAlias = str | bytes | bytearray | memoryview


class ProcessResultOverrides(TypedDict, total=False):
    """Typed keyword overrides accepted by the deterministic result factories."""

    operation_id: str
    operation_kind: ProcessOperationKind
    executable: Path | str
    args: Sequence[str]
    cwd: Path | str
    exit_code: object
    pid: object
    started_at: datetime
    duration_ms: int
    cancellation_reason: object
    launch_error_kind: object
    launch_error_message: object
    termination_attempted: object
    termination_succeeded: object
    stdout: StreamContent
    stderr: StreamContent
    stdout_path: Path | str | None
    stderr_path: Path | str | None
    capture_root: Path | str | None
    write_captures: bool | None
    output_limit_exceeded: object
    capture_complete: bool
    environment_policy: str | None
    recorded_env_overrides: Mapping[str, str] | None
    artifact_observations: Iterable[ArtifactObservation] | None


class ProcessOutcomeFactory(Protocol):
    """Build one result from a recorded fake-runner call."""

    def __call__(self, call: ProcessCall, /) -> ProcessResult: ...


QueuedOutcome: TypeAlias = ProcessResult | ProcessOutcomeFactory | BaseException


@dataclass(frozen=True, slots=True)
class ProcessCall:
    """One invocation captured by :class:`FakeProcessRunner`."""

    request: ProcessRequest
    cancellation_token: CancellationToken | None
    event_sink: ProcessEventSink | None
    ordinal: int

    def __post_init__(self) -> None:
        if not isinstance(self.request, ProcessRequest):
            raise TypeError("request must be a ProcessRequest")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int):
            raise TypeError("ordinal must be an integer")
        if self.ordinal < 1:
            raise ValueError("ordinal must be greater than zero")


@dataclass(slots=True)
class FakeCancellationToken:
    """Thread-safe cancellation token implementing the production protocol."""

    cancelled: bool = False
    cancellation_reason: CancellationReason | str | None = None
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.cancelled, bool):
            raise TypeError("cancelled must be a bool")
        if self.cancellation_reason is not None:
            self.cancellation_reason = _reason_text(self.cancellation_reason)
        if not self.cancelled and self.cancellation_reason is not None:
            raise ValueError("a non-cancelled token cannot carry a reason")

    def cancel(
        self,
        reason: CancellationReason | str = CancellationReason.USER,
    ) -> bool:
        """Cancel once and return whether the state changed."""

        with self._lock:
            changed = not self.cancelled
            self.cancelled = True
            self.cancellation_reason = _reason_text(reason)
            return changed

    def is_cancelled(self) -> bool:
        with self._lock:
            return self.cancelled

    def reason(self) -> str | None:
        with self._lock:
            value = self.cancellation_reason
            return value.value if isinstance(value, CancellationReason) else value


@dataclass(slots=True)
class RecordingProcessEventSink:
    """Thread-safe ordered collector for production ``ProcessEvent`` values."""

    _events: list[ProcessEvent] = field(default_factory=list, init=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def emit(self, event: ProcessEvent, /) -> None:
        if not isinstance(event, ProcessEvent):
            raise TypeError("event must be a ProcessEvent")
        with self._lock:
            self._events.append(event)

    @property
    def events(self) -> tuple[ProcessEvent, ...]:
        with self._lock:
            return tuple(self._events)

    @property
    def names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(event.name for event in self._events)


class FakeProcessRunner:
    """FIFO scripted callable matching ``run_process`` exactly.

    A queued callable receives the complete :class:`ProcessCall`.  Static
    results are also accepted.  In strict mode, result identity and capture
    paths must match the request, preventing unrealistic test doubles.
    """

    __slots__ = ("_calls", "_lock", "_outcomes", "_strict")

    def __init__(
        self,
        outcomes: Iterable[QueuedOutcome] = (),
        *,
        strict: bool = True,
    ) -> None:
        if not isinstance(strict, bool):
            raise TypeError("strict must be a bool")
        self._outcomes: deque[QueuedOutcome] = deque()
        self._calls: list[ProcessCall] = []
        self._strict = strict
        self._lock = RLock()
        for outcome in outcomes:
            self.enqueue(outcome)

    def __call__(
        self,
        request: ProcessRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult:
        if not isinstance(request, ProcessRequest):
            raise TypeError("request must be a ProcessRequest")
        with self._lock:
            call = ProcessCall(
                request=request,
                cancellation_token=cancellation_token,
                event_sink=event_sink,
                ordinal=len(self._calls) + 1,
            )
            self._calls.append(call)
            if not self._outcomes:
                raise AssertionError(f"unexpected fake process request: {request.operation_id!r}")
            outcome = self._outcomes.popleft()

        if isinstance(outcome, BaseException):
            raise outcome
        result = outcome(call) if callable(outcome) else outcome
        if not isinstance(result, ProcessResult):
            raise TypeError("fake outcome must produce a ProcessResult")
        if self._strict:
            _assert_matches(result, request)
        return result

    def enqueue(self, outcome: QueuedOutcome) -> FakeProcessRunner:
        if not (isinstance(outcome, (ProcessResult, BaseException)) or callable(outcome)):
            raise TypeError("outcome must be ProcessResult, callable, or BaseException")
        with self._lock:
            self._outcomes.append(outcome)
        return self

    def enqueue_completed(
        self,
        **changes: Unpack[ProcessResultOverrides],
    ) -> FakeProcessRunner:
        return self.enqueue(
            lambda call: make_completed_process_result(call.request, **changes)
        )

    def enqueue_timed_out(
        self,
        **changes: Unpack[ProcessResultOverrides],
    ) -> FakeProcessRunner:
        return self.enqueue(lambda call: make_timed_out_process_result(call.request, **changes))

    def enqueue_cancelled(
        self,
        *,
        reason: CancellationReason | str = CancellationReason.USER,
        **changes: Unpack[ProcessResultOverrides],
    ) -> FakeProcessRunner:
        return self.enqueue(
            lambda call: make_cancelled_process_result(
                call.request,
                reason=reason,
                **changes,
            )
        )

    def enqueue_launch_failed(
        self,
        *,
        error_kind: ProcessErrorKind | str = ProcessErrorKind.LAUNCH,
        message: str = "fake process launch failed",
        **changes: Unpack[ProcessResultOverrides],
    ) -> FakeProcessRunner:
        return self.enqueue(
            lambda call: make_launch_failed_process_result(
                call.request,
                error_kind=error_kind,
                message=message,
                **changes,
            )
        )

    @property
    def calls(self) -> tuple[ProcessCall, ...]:
        with self._lock:
            return tuple(self._calls)

    @property
    def requests(self) -> tuple[ProcessRequest, ...]:
        return tuple(call.request for call in self.calls)

    @property
    def last_call(self) -> ProcessCall:
        calls = self.calls
        if not calls:
            raise AssertionError("FakeProcessRunner has not been called")
        return calls[-1]

    @property
    def last_request(self) -> ProcessRequest:
        return self.last_call.request

    @property
    def remaining(self) -> int:
        with self._lock:
            return len(self._outcomes)

    def assert_consumed(self) -> None:
        if self.remaining:
            raise AssertionError(f"{self.remaining} fake process outcome(s) were not consumed")


def make_process_result(
    request: ProcessRequest | None = None,
    *,
    execution_state: ExecutionState = ExecutionState.COMPLETED,
    operation_id: str = "test-operation",
    operation_kind: ProcessOperationKind = ProcessOperationKind.COMPILE,
    executable: Path | str = Path("gf"),
    args: Sequence[str] = (),
    cwd: Path | str = Path("."),
    exit_code: int | object | None = _UNSET,
    pid: int | object | None = _UNSET,
    started_at: datetime = DEFAULT_STARTED_AT,
    duration_ms: int = DEFAULT_DURATION_MS,
    cancellation_reason: CancellationReason | str | object | None = _UNSET,
    launch_error_kind: ProcessErrorKind | str | object | None = _UNSET,
    launch_error_message: str | object = _UNSET,
    termination_attempted: bool | object = _UNSET,
    termination_succeeded: bool | object = _UNSET,
    stdout: StreamContent = b"",
    stderr: StreamContent = b"",
    stdout_path: Path | str | None = None,
    stderr_path: Path | str | None = None,
    capture_root: Path | str | None = None,
    write_captures: bool | None = None,
    output_limit_exceeded: bool | object = _UNSET,
    capture_complete: bool = True,
    environment_policy: str | None = None,
    recorded_env_overrides: Mapping[str, str] | None = None,
    artifact_observations: Iterable[ArtifactObservation] | None = None,
) -> ProcessResult:
    """Create a valid production result with safe deterministic defaults."""

    if request is not None and not isinstance(request, ProcessRequest):
        raise TypeError("request must be a ProcessRequest or None")
    state = (
        execution_state
        if isinstance(execution_state, ExecutionState)
        else ExecutionState(execution_state)
    )
    if request is not None:
        operation_id = request.operation_id
        operation_kind = request.operation_kind
        executable = request.executable
        args = request.args
        cwd = request.cwd
        environment_policy = request.environment_policy

    stdout_bytes = _bytes(stdout, "stdout")
    stderr_bytes = _bytes(stderr, "stderr")
    stdout_path, stderr_path = _capture_paths(
        request,
        operation_id,
        capture_root,
        stdout_path,
        stderr_path,
    )
    if write_captures is None:
        write_captures = request is not None or capture_root is not None
    if not isinstance(write_captures, bool):
        raise TypeError("write_captures must be a bool or None")
    if write_captures:
        _write(stdout_path, stdout_bytes)
        _write(stderr_path, stderr_bytes)

    defaults = _state_defaults(state)

    def resolved(supplied: object, key: str) -> object:
        return defaults[key] if supplied is _UNSET else supplied
    observations = (
        _observe_expected(request.expected_artifacts)
        if artifact_observations is None and request is not None
        else tuple(artifact_observations or ())
    )

    return ProcessResult(
        operation_id=operation_id,
        operation_kind=operation_kind,
        executable=Path(executable),
        args=tuple(args),
        cwd=Path(cwd),
        execution_state=state,
        exit_code=cast("int | None", resolved(exit_code, "exit_code")),
        pid=cast("int | None", resolved(pid, "pid")),
        started_at=started_at,
        finished_at=started_at + timedelta(milliseconds=duration_ms),
        duration_ms=duration_ms,
        cancellation_reason=cast(
            "CancellationReason | None",
            resolved(cancellation_reason, "cancellation_reason"),
        ),
        launch_error_kind=cast(
            "ProcessErrorKind | None",
            resolved(launch_error_kind, "launch_error_kind"),
        ),
        launch_error_message=cast(
            "str",
            resolved(launch_error_message, "launch_error_message"),
        ),
        termination_attempted=cast(
            "bool",
            resolved(termination_attempted, "termination_attempted"),
        ),
        termination_succeeded=cast(
            "bool",
            resolved(termination_succeeded, "termination_succeeded"),
        ),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_size_bytes=len(stdout_bytes),
        stderr_size_bytes=len(stderr_bytes),
        output_limit_exceeded=cast(
            "bool",
            resolved(output_limit_exceeded, "output_limit_exceeded"),
        ),
        capture_complete=capture_complete,
        environment_policy=environment_policy or "controlled-inherit-v1",
        recorded_env_overrides=dict(recorded_env_overrides or {}),
        artifact_observations=observations,
    )


def _result_with_overrides(
    request: ProcessRequest | None,
    fixed: Mapping[str, object],
    changes: ProcessResultOverrides,
) -> ProcessResult:
    values: dict[str, object] = dict(changes)
    values.update(fixed)
    return make_process_result(request, **cast("ProcessResultOverrides", values))


def make_completed_process_result(
    request: ProcessRequest | None = None,
    **changes: Unpack[ProcessResultOverrides],
) -> ProcessResult:
    return _result_with_overrides(
        request,
        {"execution_state": ExecutionState.COMPLETED},
        changes,
    )


def make_timed_out_process_result(
    request: ProcessRequest | None = None,
    **changes: Unpack[ProcessResultOverrides],
) -> ProcessResult:
    return _result_with_overrides(
        request,
        {"execution_state": ExecutionState.TIMED_OUT},
        changes,
    )


def make_cancelled_process_result(
    request: ProcessRequest | None = None,
    *,
    reason: CancellationReason | str = CancellationReason.USER,
    **changes: Unpack[ProcessResultOverrides],
) -> ProcessResult:
    return _result_with_overrides(
        request,
        {
            "execution_state": ExecutionState.CANCELLED,
            "cancellation_reason": reason,
        },
        changes,
    )


def make_output_limited_process_result(
    request: ProcessRequest | None = None,
    **changes: Unpack[ProcessResultOverrides],
) -> ProcessResult:
    return _result_with_overrides(
        request,
        {
            "execution_state": ExecutionState.CANCELLED,
            "cancellation_reason": CancellationReason.OUTPUT_LIMIT,
            "output_limit_exceeded": True,
        },
        changes,
    )


def make_launch_failed_process_result(
    request: ProcessRequest | None = None,
    *,
    error_kind: ProcessErrorKind | str = ProcessErrorKind.LAUNCH,
    message: str = "fake process launch failed",
    **changes: Unpack[ProcessResultOverrides],
) -> ProcessResult:
    return _result_with_overrides(
        request,
        {
            "execution_state": ExecutionState.LAUNCH_FAILED,
            "launch_error_kind": error_kind,
            "launch_error_message": message,
        },
        changes,
    )


def _state_defaults(state: ExecutionState) -> dict[str, object]:
    common = {
        "launch_error_kind": None,
        "launch_error_message": "",
        "output_limit_exceeded": False,
    }
    if state is ExecutionState.COMPLETED:
        return common | {
            "exit_code": 0,
            "pid": DEFAULT_PID,
            "cancellation_reason": None,
            "termination_attempted": False,
            "termination_succeeded": False,
        }
    if state is ExecutionState.TIMED_OUT:
        return common | {
            "exit_code": None,
            "pid": DEFAULT_PID,
            "cancellation_reason": None,
            "termination_attempted": True,
            "termination_succeeded": True,
        }
    if state is ExecutionState.CANCELLED:
        return common | {
            "exit_code": None,
            "pid": DEFAULT_PID,
            "cancellation_reason": CancellationReason.USER,
            "termination_attempted": True,
            "termination_succeeded": True,
        }
    if state is ExecutionState.LAUNCH_FAILED:
        return {
            "exit_code": None,
            "pid": None,
            "cancellation_reason": None,
            "launch_error_kind": ProcessErrorKind.LAUNCH,
            "launch_error_message": "fake process launch failed",
            "termination_attempted": False,
            "termination_succeeded": False,
            "output_limit_exceeded": False,
        }
    raise ValueError(f"unsupported execution state: {state!r}")


def _capture_paths(
    request: ProcessRequest | None,
    operation_id: str,
    capture_root: Path | str | None,
    stdout_path: Path | str | None,
    stderr_path: Path | str | None,
) -> tuple[Path, Path]:
    root = (
        Path(capture_root)
        if capture_root is not None
        else request.stdout_path.parent
        if request is not None
        else Path(".test-process-evidence")
    )
    safe_id = (
        "".join(char if char.isalnum() or char in "-_." else "_" for char in operation_id)
        or "process"
    )
    stdout = (
        Path(stdout_path)
        if stdout_path is not None
        else request.stdout_path
        if request is not None
        else root / f"{safe_id}.stdout.log"
    )
    stderr = (
        Path(stderr_path)
        if stderr_path is not None
        else request.stderr_path
        if request is not None
        else root / f"{safe_id}.stderr.log"
    )
    return stdout, stderr


def _observe_expected(
    expectations: Iterable[ArtifactExpectation],
) -> tuple[ArtifactObservation, ...]:
    observations: list[ArtifactObservation] = []
    for item in expectations:
        try:
            metadata = item.path.stat()
        except OSError:
            exists, kind_matches, size_bytes = False, False, None
        else:
            exists = True
            if item.kind is ArtifactKind.FILE:
                kind_matches = stat.S_ISREG(metadata.st_mode)
                size_bytes = metadata.st_size if kind_matches else None
            else:
                kind_matches = stat.S_ISDIR(metadata.st_mode)
                size_bytes = None
        observations.append(
            ArtifactObservation(
                path=item.path,
                role=item.role,
                required=item.required,
                exists=exists,
                kind_matches=kind_matches,
                size_bytes=size_bytes,
            )
        )
    return tuple(observations)


def _assert_matches(result: ProcessResult, request: ProcessRequest) -> None:
    pairs = {
        "operation_id": (result.operation_id, request.operation_id),
        "operation_kind": (result.operation_kind, request.operation_kind),
        "executable": (result.executable, request.executable),
        "args": (result.args, request.args),
        "cwd": (result.cwd, request.cwd),
        "stdout_path": (result.stdout_path, request.stdout_path),
        "stderr_path": (result.stderr_path, request.stderr_path),
    }
    errors = [
        f"{name}: {actual!r} != {expected!r}"
        for name, (actual, expected) in pairs.items()
        if actual != expected
    ]
    if errors:
        raise AssertionError("fake result does not match request: " + "; ".join(errors))


def _bytes(value: StreamContent, field_name: str) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    raise TypeError(f"{field_name} must be text or bytes-like")


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _reason_text(reason: CancellationReason | str) -> str:
    if isinstance(reason, CancellationReason):
        return reason.value
    if not isinstance(reason, str):
        raise TypeError("reason must be a string or CancellationReason")
    normalized = reason.strip()
    if not normalized or "\x00" in normalized:
        raise ValueError("reason must be non-empty and NUL-free")
    return normalized
