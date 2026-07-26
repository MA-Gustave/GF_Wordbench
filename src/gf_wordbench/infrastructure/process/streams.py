"""Bounded, concurrent capture of external-process stdout and stderr."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
import os
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from typing import BinaryIO, Final, Literal

from gf_wordbench.kernel.errors import ContractViolationError, EvidenceIOError

StreamName = Literal["stdout", "stderr"]
CaptureOperation = Literal["read", "write", "flush", "close_source", "close_sink",
                           "stat", "drain", "output_limit_callback"]
_DEFAULT_CHUNK_SIZE: Final = 64 * 1024
_RESERVATION_LOCK = Lock()
_RESERVED_CAPTURE_PATHS: set[str] = set()


@dataclass(frozen=True, slots=True)
class CaptureFailure:
    stream: StreamName | None
    operation: CaptureOperation
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class StreamCaptureSummary:
    stream: StreamName
    path: Path
    size_bytes: int
    observed_size_bytes: int
    truncated: bool
    source_closed: bool
    sink_closed: bool
    reached_eof: bool


@dataclass(frozen=True, slots=True)
class CaptureSummary:
    stdout: StreamCaptureSummary
    stderr: StreamCaptureSummary
    output_limit_bytes: int
    output_limit_exceeded: bool
    capture_complete: bool
    failures: tuple[CaptureFailure, ...]

    @property
    def captured_size_bytes(self) -> int:
        return self.stdout.size_bytes + self.stderr.size_bytes

    @property
    def observed_size_bytes(self) -> int:
        return self.stdout.observed_size_bytes + self.stderr.observed_size_bytes


@dataclass(slots=True)
class _MutableStreamState:
    stream: StreamName
    path: Path
    source: BinaryIO | None = None
    sink: BinaryIO | None = None
    observed_size_bytes: int = 0
    captured_size_bytes: int = 0
    truncated: bool = False
    reached_eof: bool = False
    source_closed: bool = False
    sink_closed: bool = False


class _OutputBudget:
    def __init__(self, limit_bytes: int) -> None:
        self._limit_bytes = limit_bytes
        self._observed_bytes = 0
        self._exceeded = False
        self._lock = Lock()

    @property
    def exceeded(self) -> bool:
        with self._lock:
            return self._exceeded

    def account(self, amount: int) -> tuple[int, bool]:
        with self._lock:
            previous = self._observed_bytes
            self._observed_bytes += amount
            writable = min(amount, max(0, self._limit_bytes - previous))
            crossed = not self._exceeded and self._observed_bytes > self._limit_bytes
            if crossed:
                self._exceeded = True
            return writable, crossed


class ProcessStreamCapture:
    """Capture two child streams without shell merging or unbounded buffering."""

    def __init__(
        self,
        stdout_path: Path,
        stderr_path: Path,
        output_limit_bytes: int,
        *,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        on_output_limit: Callable[[], None] | None = None,
    ) -> None:
        _validate_path(stdout_path, "stdout_path")
        _validate_path(stderr_path, "stderr_path")
        if _path_key(stdout_path) == _path_key(stderr_path):
            raise ContractViolationError("stdout_path and stderr_path must be distinct.")
        _validate_positive_integer(output_limit_bytes, "output_limit_bytes")
        _validate_positive_integer(chunk_size, "chunk_size")

        self._stdout = _MutableStreamState("stdout", stdout_path)
        self._stderr = _MutableStreamState("stderr", stderr_path)
        self._budget = _OutputBudget(output_limit_bytes)
        self._output_limit_bytes = output_limit_bytes
        self._chunk_size = chunk_size
        self._on_output_limit = on_output_limit
        self._limit_event = Event()
        self._failure_event = Event()
        self._failures: list[CaptureFailure] = []
        self._failure_lock = Lock()
        self._lifecycle_lock = Lock()
        self._threads: list[Thread] = []
        self._lifecycle = "new"
        self._reservation_keys: tuple[str, str] | None = None
        self._summary: CaptureSummary | None = None

    @property
    def output_limit_event(self) -> Event:
        return self._limit_event

    @property
    def capture_failure_event(self) -> Event:
        return self._failure_event

    @property
    def output_limit_exceeded(self) -> bool:
        return self._budget.exceeded

    def open(self) -> None:
        with self._lifecycle_lock:
            if self._lifecycle != "new":
                raise ContractViolationError("Process stream capture can be opened only once.")
            self._reserve_paths()
            try:
                self._stdout.path.parent.mkdir(parents=True, exist_ok=True)
                self._stderr.path.parent.mkdir(parents=True, exist_ok=True)
                self._stdout.sink = self._stdout.path.open("xb", buffering=0)
                self._stderr.sink = self._stderr.path.open("xb", buffering=0)
            except OSError as exc:
                self._rollback_open_failure()
                raise EvidenceIOError("Could not open process stream capture files.") from exc
            self._lifecycle = "open"

    def start(self, stdout_source: BinaryIO, stderr_source: BinaryIO) -> None:
        with self._lifecycle_lock:
            if self._lifecycle != "open":
                raise ContractViolationError(
                    "Process stream pumps require an open, unused capture session."
                )
            if stdout_source is stderr_source:
                raise ContractViolationError("stdout and stderr sources must be distinct.")
            _validate_source(stdout_source, "stdout")
            _validate_source(stderr_source, "stderr")
            self._stdout.source = stdout_source
            self._stderr.source = stderr_source
            candidates = (
                Thread(
                    target=self._pump,
                    args=(self._stdout,),
                    name="gfwb-process-stdout",
                    daemon=True,
                ),
                Thread(
                    target=self._pump,
                    args=(self._stderr,),
                    name="gfwb-process-stderr",
                    daemon=True,
                ),
            )
            self._lifecycle = "running"

        try:
            for thread in candidates:
                thread.start()
                self._threads.append(thread)
        except RuntimeError as exc:
            self._record_failure(None, "read", exc)
            self._stdout.truncated = True
            self._stderr.truncated = True
            self._close_source(self._stdout)
            self._close_source(self._stderr)
            if len(self._threads) < 2:
                unstarted = self._stderr if self._threads else self._stdout
                self._close_sink(unstarted)
            raise EvidenceIOError("Could not start process stream capture threads.") from exc

    def finalize(self, *, drain_timeout_sec: float) -> CaptureSummary:
        _validate_non_negative_finite(drain_timeout_sec, "drain_timeout_sec")
        with self._lifecycle_lock:
            if self._lifecycle == "finalized":
                assert self._summary is not None
                return self._summary
            if self._lifecycle == "new":
                raise ContractViolationError("Process stream capture was not opened.")
            lifecycle = self._lifecycle

        if lifecycle == "running":
            deadline = monotonic() + drain_timeout_sec
            for thread in tuple(self._threads):
                thread.join(max(0.0, deadline - monotonic()))
            alive = tuple(thread for thread in self._threads if thread.is_alive())
            if alive:
                self._record_failure(
                    None,
                    "drain",
                    TimeoutError("Process stream drain deadline expired."),
                )
                self._stdout.truncated = True
                self._stderr.truncated = True
                self._close_source(self._stdout)
                self._close_source(self._stderr)
                for thread in alive:
                    thread.join(0.5)
        else:
            for state in (self._stdout, self._stderr):
                state.reached_eof = True
                state.source_closed = True
                self._close_sink(state)

        summary = self._build_summary()
        with self._lifecycle_lock:
            self._summary = summary
            self._lifecycle = "finalized"
        if summary.stdout.sink_closed and summary.stderr.sink_closed:
            self._release_paths()
        return summary

    def _pump(self, state: _MutableStreamState) -> None:
        source = state.source
        sink = state.sink
        assert source is not None
        assert sink is not None
        write_failed = False
        try:
            while True:
                try:
                    data = source.read(self._chunk_size)
                except (OSError, ValueError) as exc:
                    state.truncated = True
                    self._record_failure(state.stream, "read", exc)
                    break
                if data == b"":
                    state.reached_eof = True
                    break
                if not isinstance(data, bytes):
                    state.truncated = True
                    self._record_failure(
                        state.stream,
                        "read",
                        TypeError("Process stream returned non-byte data."),
                    )
                    break

                state.observed_size_bytes += len(data)
                writable, crossed = self._budget.account(len(data))
                state.truncated = state.truncated or writable < len(data)
                if writable and not write_failed:
                    try:
                        _write_all(sink, memoryview(data)[:writable])
                        state.captured_size_bytes += writable
                    except (OSError, ValueError) as exc:
                        write_failed = True
                        state.truncated = True
                        self._record_failure(state.stream, "write", exc)
                if crossed:
                    self._signal_output_limit()
        finally:
            self._close_source(state)
            self._close_sink(state)

    def _signal_output_limit(self) -> None:
        self._limit_event.set()
        if self._on_output_limit is None:
            return
        try:
            self._on_output_limit()
        except Exception as exc:
            self._record_failure(None, "output_limit_callback", exc)

    def _build_summary(self) -> CaptureSummary:
        stdout = self._stream_summary(self._stdout)
        stderr = self._stream_summary(self._stderr)
        with self._failure_lock:
            failures = tuple(self._failures)
        threads_stopped = all(not thread.is_alive() for thread in self._threads)
        complete = (
            threads_stopped
            and stdout.reached_eof
            and stderr.reached_eof
            and stdout.source_closed
            and stderr.source_closed
            and stdout.sink_closed
            and stderr.sink_closed
            and not stdout.truncated
            and not stderr.truncated
            and not failures
        )
        return CaptureSummary(
            stdout=stdout,
            stderr=stderr,
            output_limit_bytes=self._output_limit_bytes,
            output_limit_exceeded=self._budget.exceeded,
            capture_complete=complete,
            failures=failures,
        )

    def _stream_summary(self, state: _MutableStreamState) -> StreamCaptureSummary:
        size = state.captured_size_bytes
        if state.sink_closed:
            try:
                size = state.path.stat().st_size
            except OSError as exc:
                self._record_failure(state.stream, "stat", exc)
        return StreamCaptureSummary(
            stream=state.stream,
            path=state.path,
            size_bytes=size,
            observed_size_bytes=state.observed_size_bytes,
            truncated=state.truncated,
            source_closed=state.source_closed,
            sink_closed=state.sink_closed,
            reached_eof=state.reached_eof,
        )

    def _close_source(self, state: _MutableStreamState) -> None:
        if state.source is None or state.source_closed:
            state.source_closed = True
            return
        try:
            state.source.close()
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "close_source", exc)
        else:
            state.source_closed = True

    def _close_sink(self, state: _MutableStreamState) -> None:
        if state.sink is None or state.sink_closed:
            state.sink_closed = True
            return
        try:
            state.sink.flush()
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "flush", exc)
        try:
            state.sink.close()
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "close_sink", exc)
        else:
            state.sink_closed = True

    def _record_failure(
        self,
        stream: StreamName | None,
        operation: CaptureOperation,
        exc: BaseException,
    ) -> None:
        with self._failure_lock:
            self._failures.append(
                CaptureFailure(
                    stream=stream,
                    operation=operation,
                    exception_type=type(exc).__name__,
                    message=str(exc),
                )
            )
        self._failure_event.set()

    def _reserve_paths(self) -> None:
        keys = (_path_key(self._stdout.path), _path_key(self._stderr.path))
        with _RESERVATION_LOCK:
            if any(key in _RESERVED_CAPTURE_PATHS for key in keys):
                raise ContractViolationError(
                    "A process stream capture path is already reserved by an active request."
                )
            _RESERVED_CAPTURE_PATHS.update(keys)
        self._reservation_keys = keys

    def _release_paths(self) -> None:
        if self._reservation_keys is None:
            return
        with _RESERVATION_LOCK:
            _RESERVED_CAPTURE_PATHS.difference_update(self._reservation_keys)
        self._reservation_keys = None

    def _rollback_open_failure(self) -> None:
        for state in (self._stdout, self._stderr):
            self._close_sink(state)
            try:
                state.path.unlink(missing_ok=True)
            except OSError:
                pass
        self._release_paths()


def _write_all(sink: BinaryIO, data: memoryview) -> None:
    written = 0
    while written < len(data):
        count = sink.write(data[written:])
        if count is None or count <= 0:
            raise OSError("Process stream capture made no forward write progress.")
        written += count


def _validate_source(value: object, stream: StreamName) -> None:
    if not callable(getattr(value, "read", None)):
        raise ContractViolationError(f"{stream} source must be a readable binary stream.")


def _validate_path(value: object, field: str) -> None:
    if not isinstance(value, Path):
        raise ContractViolationError(f"{field} must be a pathlib.Path instance.")
    if not value.is_absolute():
        raise ContractViolationError(f"{field} must be an absolute path.")
    if "\x00" in str(value):
        raise ContractViolationError(f"{field} must not contain a NUL character.")


def _validate_positive_integer(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractViolationError(f"{field} must be a positive integer.")


def _validate_non_negative_finite(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolationError(f"{field} must be a finite non-negative number.")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ContractViolationError(f"{field} must be a finite non-negative number.")


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))
