"""Bounded capture of external-process stdout and stderr.

Two compatible capture APIs are provided:

* :class:`CaptureSession` exposes two binary files that can be passed directly
  to ``subprocess.Popen``.
* :class:`ProcessStreamCapture` concurrently drains two readable binary streams.

Both APIs preserve stdout and stderr separately, enforce one combined output
budget, retain immutable summaries, and never overwrite existing evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
import os
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from typing import BinaryIO, Final, Literal, TypeAlias

from gf_wordbench.kernel.errors import ContractViolationError, EvidenceIOError

StreamName = Literal["stdout", "stderr"]
CaptureOperation = Literal[
    "read",
    "write",
    "flush",
    "close_source",
    "close_sink",
    "stat",
    "truncate",
    "drain",
    "output_limit_callback",
]
_DEFAULT_CHUNK_SIZE: Final[int] = 64 * 1024
_POST_CLOSE_JOIN_SEC: Final[float] = 0.5
_RESERVATION_LOCK = Lock()
_RESERVED_CAPTURE_PATHS: set[str] = set()


@dataclass(frozen=True, slots=True)
class CaptureFailure:
    """One non-fatal failure encountered while preserving process evidence."""

    stream: StreamName | None
    operation: CaptureOperation
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class StreamCaptureSummary:
    """Immutable final state of one captured byte stream."""

    stream: StreamName
    path: Path
    size_bytes: int
    observed_size_bytes: int
    truncated: bool
    source_closed: bool
    sink_closed: bool
    reached_eof: bool


@dataclass(frozen=True, slots=True)
class ProcessCapture:
    """Immutable final result for one stdout/stderr capture pair."""

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


# Backward-compatible name used by the concurrent stream-pump API.
CaptureSummary: TypeAlias = ProcessCapture


@dataclass(slots=True)
class _DirectStreamState:
    stream: StreamName
    path: Path
    sink: BinaryIO | None = None
    created: bool = False


class CaptureSession:
    """Context-managed capture files suitable for ``subprocess.Popen``.

    The child process writes directly to ``stdout`` and ``stderr``.  The
    ``output_limit_exceeded`` property observes current file sizes so a process
    monitor can terminate a child that crosses the combined budget.  Finalize
    then truncates any overshoot while preserving a prefix of each stream.
    """

    def __init__(
        self,
        *,
        stdout_path: Path,
        stderr_path: Path,
        output_limit_bytes: int,
    ) -> None:
        _validate_capture_contract(
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_limit_bytes=output_limit_bytes,
        )
        self._stdout_state = _DirectStreamState("stdout", stdout_path)
        self._stderr_state = _DirectStreamState("stderr", stderr_path)
        self._output_limit_bytes = output_limit_bytes
        self._output_limit_exceeded = False
        self._failures: list[CaptureFailure] = []
        self._failure_keys: set[tuple[object, ...]] = set()
        self._failure_lock = Lock()
        self._lifecycle_lock = Lock()
        self._lifecycle = "new"
        self._reservation_keys: tuple[str, str] | None = None
        self._summary: ProcessCapture | None = None

    @property
    def stdout(self) -> BinaryIO:
        sink = self._stdout_state.sink
        if sink is None:
            raise ContractViolationError("Capture session has not been opened.")
        return sink

    @property
    def stderr(self) -> BinaryIO:
        sink = self._stderr_state.sink
        if sink is None:
            raise ContractViolationError("Capture session has not been opened.")
        return sink

    @property
    def output_limit_exceeded(self) -> bool:
        if self._output_limit_exceeded:
            return True
        if self._lifecycle == "new":
            return False
        stdout_size, stderr_size = self._observe_file_sizes()
        if stdout_size + stderr_size > self._output_limit_bytes:
            self._output_limit_exceeded = True
        return self._output_limit_exceeded

    def __enter__(self) -> CaptureSession:
        with self._lifecycle_lock:
            if self._lifecycle != "new":
                raise ContractViolationError("Capture session can be opened only once.")
            self._reserve_paths()
            try:
                self._open_sink(self._stdout_state)
                self._open_sink(self._stderr_state)
            except OSError as exc:
                self._rollback_open_failure()
                raise EvidenceIOError("Could not open process stream capture files.") from exc
            self._lifecycle = "open"
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> Literal[False]:
        del exc_type, exc, traceback
        self.finalize()
        return False

    def flush(self) -> None:
        """Flush both evidence files or raise when preservation fails."""

        if self._lifecycle == "new":
            raise ContractViolationError("Capture session has not been opened.")
        if self._lifecycle == "finalized":
            return

        failed = False
        for state in self._states:
            sink = state.sink
            if sink is None or sink.closed:
                continue
            try:
                sink.flush()
            except (OSError, ValueError) as exc:
                failed = True
                self._record_failure(state.stream, "flush", exc)
        if failed:
            raise EvidenceIOError("Could not flush process stream capture files.")

    def finalize(self) -> ProcessCapture:
        """Close, bound, summarize, and release the capture exactly once."""

        with self._lifecycle_lock:
            if self._lifecycle == "finalized":
                assert self._summary is not None
                return self._summary
            if self._lifecycle == "new":
                raise ContractViolationError("Capture session has not been opened.")

            self._flush_without_raising()
            observed_stdout, observed_stderr = self._observe_file_sizes()
            observed_total = observed_stdout + observed_stderr
            exceeded = observed_total > self._output_limit_bytes
            self._output_limit_exceeded = self._output_limit_exceeded or exceeded

            keep_stdout, keep_stderr = _bounded_stream_sizes(
                stdout_size=observed_stdout,
                stderr_size=observed_stderr,
                limit_bytes=self._output_limit_bytes,
            )
            self._truncate_if_needed(self._stdout_state, keep_stdout)
            self._truncate_if_needed(self._stderr_state, keep_stderr)
            self._flush_without_raising()

            for state in self._states:
                self._close_sink(state)

            final_stdout, final_stderr = self._observe_file_sizes(
                fallback=(keep_stdout, keep_stderr)
            )
            failures = self._failure_snapshot()
            stdout_summary = _direct_stream_summary(
                self._stdout_state,
                observed_size=observed_stdout,
                final_size=final_stdout,
            )
            stderr_summary = _direct_stream_summary(
                self._stderr_state,
                observed_size=observed_stderr,
                final_size=final_stderr,
            )
            complete = (
                stdout_summary.sink_closed
                and stderr_summary.sink_closed
                and not stdout_summary.truncated
                and not stderr_summary.truncated
                and not failures
            )
            summary = ProcessCapture(
                stdout=stdout_summary,
                stderr=stderr_summary,
                output_limit_bytes=self._output_limit_bytes,
                output_limit_exceeded=self._output_limit_exceeded,
                capture_complete=complete,
                failures=failures,
            )
            self._summary = summary
            self._lifecycle = "finalized"
            self._release_paths()
            return summary

    @property
    def _states(self) -> tuple[_DirectStreamState, _DirectStreamState]:
        return self._stdout_state, self._stderr_state

    def _open_sink(self, state: _DirectStreamState) -> None:
        state.path.parent.mkdir(parents=True, exist_ok=True)
        state.sink = state.path.open("xb", buffering=0)
        state.created = True

    def _flush_without_raising(self) -> None:
        for state in self._states:
            sink = state.sink
            if sink is None or sink.closed:
                continue
            try:
                sink.flush()
            except (OSError, ValueError) as exc:
                self._record_failure(state.stream, "flush", exc)

    def _truncate_if_needed(
        self,
        state: _DirectStreamState,
        keep_bytes: int,
    ) -> None:
        sink = state.sink
        if sink is None or sink.closed:
            return
        try:
            current_size = state.path.stat().st_size
        except OSError as exc:
            self._record_failure(state.stream, "stat", exc)
            return
        if current_size <= keep_bytes:
            return
        try:
            sink.truncate(keep_bytes)
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "truncate", exc)

    def _close_sink(self, state: _DirectStreamState) -> None:
        sink = state.sink
        if sink is None or sink.closed:
            return
        try:
            sink.close()
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "close_sink", exc)

    def _observe_file_sizes(
        self,
        *,
        fallback: tuple[int, int] = (0, 0),
    ) -> tuple[int, int]:
        sizes: list[int] = []
        for state, fallback_size in zip(self._states, fallback, strict=True):
            try:
                sizes.append(state.path.stat().st_size)
            except OSError as exc:
                self._record_failure(state.stream, "stat", exc)
                sizes.append(fallback_size)
        return sizes[0], sizes[1]

    def _record_failure(
        self,
        stream: StreamName | None,
        operation: CaptureOperation,
        exc: BaseException,
    ) -> None:
        failure = _capture_failure(stream, operation, exc)
        key = (
            failure.stream,
            failure.operation,
            failure.exception_type,
            failure.message,
        )
        with self._failure_lock:
            if key not in self._failure_keys:
                self._failure_keys.add(key)
                self._failures.append(failure)

    def _failure_snapshot(self) -> tuple[CaptureFailure, ...]:
        with self._failure_lock:
            return tuple(self._failures)

    def _reserve_paths(self) -> None:
        self._reservation_keys = _reserve_capture_paths(
            self._stdout_state.path,
            self._stderr_state.path,
        )

    def _release_paths(self) -> None:
        _release_capture_paths(self._reservation_keys)
        self._reservation_keys = None

    def _rollback_open_failure(self) -> None:
        for state in self._states:
            self._close_sink(state)
            if not state.created:
                continue
            try:
                state.path.unlink(missing_ok=True)
            except OSError:
                pass
            state.created = False
        self._release_paths()


def open_capture_session(
    *,
    stdout_path: Path,
    stderr_path: Path,
    output_limit_bytes: int,
) -> CaptureSession:
    """Return a fresh context-managed direct-file capture session."""

    return CaptureSession(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_limit_bytes=output_limit_bytes,
    )


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
    created: bool = False


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
            writable = min(
                amount,
                max(0, self._limit_bytes - previous),
            )
            crossed = not self._exceeded and self._observed_bytes > self._limit_bytes
            if crossed:
                self._exceeded = True
            return writable, crossed


class ProcessStreamCapture:
    """Concurrently drain two readable byte streams into bounded evidence files."""

    def __init__(
        self,
        stdout_path: Path,
        stderr_path: Path,
        output_limit_bytes: int,
        *,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        on_output_limit: Callable[[], None] | None = None,
    ) -> None:
        _validate_capture_contract(
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_limit_bytes=output_limit_bytes,
        )
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
        self._failure_keys: set[tuple[object, ...]] = set()
        self._failure_lock = Lock()
        self._lifecycle_lock = Lock()
        self._threads: list[Thread] = []
        self._lifecycle = "new"
        self._reservation_keys: tuple[str, str] | None = None
        self._summary: ProcessCapture | None = None

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
            self._reservation_keys = _reserve_capture_paths(
                self._stdout.path,
                self._stderr.path,
            )
            try:
                self._open_sink(self._stdout)
                self._open_sink(self._stderr)
            except OSError as exc:
                self._rollback_open_failure()
                raise EvidenceIOError("Could not open process stream capture files.") from exc
            self._lifecycle = "open"

    def start(
        self,
        stdout_source: BinaryIO,
        stderr_source: BinaryIO,
    ) -> None:
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
            for thread in tuple(self._threads):
                thread.join(_POST_CLOSE_JOIN_SEC)
            self._close_sink(self._stdout)
            self._close_sink(self._stderr)
            summary = self._build_summary()
            with self._lifecycle_lock:
                self._summary = summary
                self._lifecycle = "finalized"
            self._release_paths()
            raise EvidenceIOError("Could not start process stream capture threads.") from exc

    def finalize(self, *, drain_timeout_sec: float) -> ProcessCapture:
        _validate_non_negative_finite(
            drain_timeout_sec,
            "drain_timeout_sec",
        )
        with self._lifecycle_lock:
            if self._lifecycle == "finalized":
                assert self._summary is not None
                return self._summary
            if self._lifecycle == "new":
                raise ContractViolationError("Process stream capture was not opened.")
            lifecycle = self._lifecycle

        if lifecycle == "running":
            self._drain_running_threads(drain_timeout_sec)
        else:
            for state in self._states:
                state.reached_eof = True
                state.source_closed = True
                self._close_sink(state)

        summary = self._build_summary()
        with self._lifecycle_lock:
            self._summary = summary
            self._lifecycle = "finalized"
        self._release_paths()
        return summary

    @property
    def _states(self) -> tuple[_MutableStreamState, _MutableStreamState]:
        return self._stdout, self._stderr

    def _open_sink(self, state: _MutableStreamState) -> None:
        state.path.parent.mkdir(parents=True, exist_ok=True)
        state.sink = state.path.open("xb", buffering=0)
        state.created = True

    def _drain_running_threads(self, drain_timeout_sec: float) -> None:
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
                thread.join(_POST_CLOSE_JOIN_SEC)

        for state in self._states:
            self._close_sink(state)

    def _pump(self, state: _MutableStreamState) -> None:
        source = state.source
        sink = state.sink
        assert source is not None
        assert sink is not None
        write_failed = False
        try:
            while True:
                try:
                    raw_data: object = source.read(self._chunk_size)
                except (OSError, ValueError) as exc:
                    state.truncated = True
                    self._record_failure(state.stream, "read", exc)
                    break
                if raw_data == b"":
                    state.reached_eof = True
                    break
                if not isinstance(raw_data, bytes):
                    state.truncated = True
                    self._record_failure(
                        state.stream,
                        "read",
                        TypeError("Process stream returned non-byte data."),
                    )
                    break
                data = raw_data

                state.observed_size_bytes += len(data)
                writable, crossed = self._budget.account(len(data))
                if writable < len(data):
                    state.truncated = True
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
        callback = self._on_output_limit
        if callback is None:
            return
        try:
            callback()
        except Exception as exc:
            self._record_failure(
                None,
                "output_limit_callback",
                exc,
            )

    def _build_summary(self) -> ProcessCapture:
        stdout = self._stream_summary(self._stdout)
        stderr = self._stream_summary(self._stderr)
        failures = self._failure_snapshot()
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
        return ProcessCapture(
            stdout=stdout,
            stderr=stderr,
            output_limit_bytes=self._output_limit_bytes,
            output_limit_exceeded=self._budget.exceeded,
            capture_complete=complete,
            failures=failures,
        )

    def _stream_summary(
        self,
        state: _MutableStreamState,
    ) -> StreamCaptureSummary:
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
        source = state.source
        if source is None or state.source_closed:
            state.source_closed = True
            return
        try:
            source.close()
        except (OSError, ValueError) as exc:
            self._record_failure(
                state.stream,
                "close_source",
                exc,
            )
        finally:
            state.source_closed = bool(getattr(source, "closed", False))

    def _close_sink(self, state: _MutableStreamState) -> None:
        sink = state.sink
        if sink is None or state.sink_closed:
            state.sink_closed = True
            return
        try:
            sink.flush()
        except (OSError, ValueError) as exc:
            self._record_failure(state.stream, "flush", exc)
        try:
            sink.close()
        except (OSError, ValueError) as exc:
            self._record_failure(
                state.stream,
                "close_sink",
                exc,
            )
        finally:
            state.sink_closed = bool(getattr(sink, "closed", False))

    def _record_failure(
        self,
        stream: StreamName | None,
        operation: CaptureOperation,
        exc: BaseException,
    ) -> None:
        failure = _capture_failure(stream, operation, exc)
        key = (
            failure.stream,
            failure.operation,
            failure.exception_type,
            failure.message,
        )
        with self._failure_lock:
            if key not in self._failure_keys:
                self._failure_keys.add(key)
                self._failures.append(failure)
        self._failure_event.set()

    def _failure_snapshot(self) -> tuple[CaptureFailure, ...]:
        with self._failure_lock:
            return tuple(self._failures)

    def _release_paths(self) -> None:
        _release_capture_paths(self._reservation_keys)
        self._reservation_keys = None

    def _rollback_open_failure(self) -> None:
        for state in self._states:
            self._close_sink(state)
            if not state.created:
                continue
            try:
                state.path.unlink(missing_ok=True)
            except OSError:
                pass
            state.created = False
        self._release_paths()


def _direct_stream_summary(
    state: _DirectStreamState,
    *,
    observed_size: int,
    final_size: int,
) -> StreamCaptureSummary:
    sink = state.sink
    sink_closed = sink is None or sink.closed
    return StreamCaptureSummary(
        stream=state.stream,
        path=state.path,
        size_bytes=final_size,
        observed_size_bytes=observed_size,
        truncated=final_size < observed_size,
        source_closed=True,
        sink_closed=sink_closed,
        reached_eof=True,
    )


def _bounded_stream_sizes(
    *,
    stdout_size: int,
    stderr_size: int,
    limit_bytes: int,
) -> tuple[int, int]:
    total = stdout_size + stderr_size
    if total <= limit_bytes:
        return stdout_size, stderr_size
    if total == 0:
        return 0, 0

    stdout_keep = min(
        stdout_size,
        (limit_bytes * stdout_size) // total,
    )
    stderr_keep = min(
        stderr_size,
        limit_bytes - stdout_keep,
    )
    remaining = limit_bytes - stdout_keep - stderr_keep
    if remaining:
        stdout_extra = min(remaining, stdout_size - stdout_keep)
        stdout_keep += stdout_extra
        remaining -= stdout_extra
    if remaining:
        stderr_keep += min(remaining, stderr_size - stderr_keep)
    return stdout_keep, stderr_keep


def _write_all(sink: BinaryIO, data: memoryview) -> None:
    written = 0
    while written < len(data):
        count = sink.write(data[written:])
        if count is None or count <= 0:
            raise OSError("Process stream capture made no forward write progress.")
        written += count


def _capture_failure(
    stream: StreamName | None,
    operation: CaptureOperation,
    exc: BaseException,
) -> CaptureFailure:
    message = " ".join(str(exc).replace("\x00", "\N{REPLACEMENT CHARACTER}").split())
    return CaptureFailure(
        stream=stream,
        operation=operation,
        exception_type=type(exc).__name__,
        message=message or type(exc).__name__,
    )


def _validate_capture_contract(
    *,
    stdout_path: Path,
    stderr_path: Path,
    output_limit_bytes: int,
) -> None:
    _validate_path(stdout_path, "stdout_path")
    _validate_path(stderr_path, "stderr_path")
    if _path_key(stdout_path) == _path_key(stderr_path):
        raise ContractViolationError("stdout_path and stderr_path must be distinct.")
    _validate_positive_integer(
        output_limit_bytes,
        "output_limit_bytes",
    )


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


def _reserve_capture_paths(
    stdout_path: Path,
    stderr_path: Path,
) -> tuple[str, str]:
    keys = (_path_key(stdout_path), _path_key(stderr_path))
    with _RESERVATION_LOCK:
        if any(key in _RESERVED_CAPTURE_PATHS for key in keys):
            raise ContractViolationError(
                "A process stream capture path is already reserved by an active request."
            )
        _RESERVED_CAPTURE_PATHS.update(keys)
    return keys


def _release_capture_paths(
    keys: tuple[str, str] | None,
) -> None:
    if keys is None:
        return
    with _RESERVATION_LOCK:
        _RESERVED_CAPTURE_PATHS.difference_update(keys)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


__all__ = (
    "CaptureFailure",
    "CaptureSession",
    "CaptureSummary",
    "ProcessCapture",
    "ProcessStreamCapture",
    "StreamCaptureSummary",
    "open_capture_session",
)
