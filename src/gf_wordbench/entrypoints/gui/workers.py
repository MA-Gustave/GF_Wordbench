"""Background-run transport and lifecycle management for the Qt GUI."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from threading import Event, Lock
import traceback
from typing import Final, Protocol, TypeAlias, TypeVar, runtime_checkable

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    GFWordbenchError,
)
from gf_wordbench.kernel.events import LifecycleEvent, ProgressEvent
from gf_wordbench.runs.public import RunConfig, RunResult

__all__ = (
    "RunApplicationUseCase",
    "RunWorker",
    "RunWorkerHandle",
    "RunWorkerRequest",
    "WorkerCancellation",
    "WorkerCancellationRequest",
    "WorkerEvent",
    "WorkerEventSink",
    "WorkerFailure",
    "WorkerState",
    "create_run_worker",
    "start_run_worker",
)

_MAX_IDENTIFIER: Final[int] = 256
_MAX_MESSAGE: Final[int] = 1_024
_MAX_DETAIL: Final[int] = 8_192
_MAX_TRACEBACK: Final[int] = 32_768
_MAX_EVIDENCE_PATHS: Final[int] = 128
_ALLOWED_CANCELLATION_REASONS: Final[frozenset[str]] = frozenset(
    {
        "user",
        "application_shutdown",
        "output_limit",
        "controller_policy",
    }
)

WorkerEvent: TypeAlias = ProgressEvent | LifecycleEvent
WorkerEventSink: TypeAlias = Callable[[WorkerEvent], None]
CancellationCheck: TypeAlias = Callable[[], None]

_E = TypeVar("_E", bound=StrEnum)


@unique
class WorkerState(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    CANCELLING = "cancelling"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    FAILED = "failed"
    STOPPED = "stopped"

    @property
    def is_terminal(self) -> bool:
        return self in {
            WorkerState.FINISHED,
            WorkerState.CANCELLED,
            WorkerState.FAILED,
            WorkerState.STOPPED,
        }


@dataclass(frozen=True, slots=True)
class WorkerFailure:
    occurred_at: datetime
    run_id: str
    exception_type: str
    message: str
    detail: str = ""
    stage: str | None = None
    operation: str | None = None
    subject: str | None = None
    retryable: bool = False
    evidence_paths: tuple[str, ...] = ()
    traceback_text: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "occurred_at",
            _utc_datetime(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(
            self,
            "run_id",
            _text(self.run_id, "run_id", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "exception_type",
            _text(
                self.exception_type,
                "exception_type",
                _MAX_IDENTIFIER,
            ),
        )
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message", _MAX_MESSAGE),
        )
        object.__setattr__(
            self,
            "detail",
            _bounded_plain_text(self.detail, "detail", _MAX_DETAIL),
        )
        for field_name in ("stage", "operation", "subject"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _text(value, field_name, _MAX_IDENTIFIER),
                )
        if type(self.retryable) is not bool:
            raise TypeError("retryable must be bool")
        object.__setattr__(
            self,
            "evidence_paths",
            _evidence_paths(self.evidence_paths),
        )
        object.__setattr__(
            self,
            "traceback_text",
            _bounded_plain_text(
                self.traceback_text,
                "traceback_text",
                _MAX_TRACEBACK,
            ),
        )

    @classmethod
    def from_exception(
        cls,
        run_id: str,
        exception: Exception,
    ) -> WorkerFailure:
        if not isinstance(exception, Exception):
            raise TypeError("exception must be an Exception")

        message = _exception_message(exception)
        detail = ""
        stage = None
        operation = None
        subject = None
        retryable = False
        evidence_paths: tuple[str, ...] = ()

        if isinstance(exception, GFWordbenchError):
            detail = exception.detail
            stage = exception.stage
            operation = exception.operation
            subject = exception.subject
            retryable = exception.retryable
            evidence_paths = exception.evidence_paths

        rendered = "".join(
            traceback.TracebackException.from_exception(
                exception,
                capture_locals=False,
            ).format()
        )

        return cls(
            occurred_at=datetime.now(UTC),
            run_id=run_id,
            exception_type=type(exception).__name__,
            message=message,
            detail=detail,
            stage=stage,
            operation=operation,
            subject=subject,
            retryable=retryable,
            evidence_paths=evidence_paths,
            traceback_text=rendered[-_MAX_TRACEBACK:],
        )


@dataclass(frozen=True, slots=True)
class WorkerCancellation:
    occurred_at: datetime
    run_id: str
    reason: str
    message: str = "Run cancelled"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "occurred_at",
            _utc_datetime(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(
            self,
            "run_id",
            _text(self.run_id, "run_id", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "reason",
            _cancellation_reason(self.reason),
        )
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message", _MAX_MESSAGE),
        )


class WorkerCancellationRequest:
    """Thread-safe cancellation bridge shared by the GUI and run worker."""

    __slots__ = ("_event", "_lock", "_reason")

    def __init__(self) -> None:
        self._event = Event()
        self._lock = Lock()
        self._reason: str | None = None

    def request(self, reason: str = "user") -> bool:
        canonical = _cancellation_reason(reason)
        with self._lock:
            if self._event.is_set():
                return False
            self._reason = canonical
            self._event.set()
            return True

    def is_requested(self) -> bool:
        return self._event.is_set()

    def is_cancellation_requested(self) -> bool:
        return self.is_requested()

    def is_cancelled(self) -> bool:
        return self.is_requested()

    def reason(self) -> str | None:
        with self._lock:
            return self._reason

    def cancellation_reason(self) -> str | None:
        return self.reason()

    def wait(self, timeout_sec: float | None = None) -> bool:
        if timeout_sec is not None:
            if isinstance(timeout_sec, bool) or not isinstance(timeout_sec, (int, float)):
                raise TypeError("timeout_sec must be a number or None")
            if timeout_sec < 0:
                raise ValueError("timeout_sec cannot be negative")
        return self._event.wait(timeout_sec)

    def check(self) -> None:
        if not self.is_requested():
            return
        reason = self.reason() or "controller_policy"
        raise CancellationRequested(
            "Cancellation requested.",
            detail=f"reason={reason}",
            stage="run",
            operation="execute_run",
        )


@runtime_checkable
class RunApplicationUseCase(Protocol):
    """One injected application use case executed by a worker thread."""

    def __call__(
        self,
        run_config: RunConfig,
        event_sink: WorkerEventSink,
        cancellation_check: CancellationCheck,
    ) -> RunResult: ...


@dataclass(frozen=True, slots=True)
class RunWorkerRequest:
    run_id: str
    run_config: RunConfig
    execute: RunApplicationUseCase

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "run_id",
            _text(self.run_id, "run_id", _MAX_IDENTIFIER),
        )
        if not isinstance(self.run_config, RunConfig):
            raise TypeError("run_config must be RunConfig")
        if not callable(self.execute):
            raise TypeError("execute must be callable")


class RunWorker(QObject):
    """Single-use QObject that executes one resolved run outside the GUI thread."""

    started = Signal(str)
    progress = Signal(object)
    finished = Signal(object)
    cancelled = Signal(object)
    failed = Signal(object)
    stopped = Signal()

    def __init__(
        self,
        request: RunWorkerRequest,
        cancellation: WorkerCancellationRequest | None = None,
    ) -> None:
        super().__init__(None)
        if not isinstance(request, RunWorkerRequest):
            raise TypeError("request must be RunWorkerRequest")
        if cancellation is not None and not isinstance(
            cancellation,
            WorkerCancellationRequest,
        ):
            raise TypeError("cancellation must be WorkerCancellationRequest or None")
        self._request = request
        self._cancellation = cancellation or WorkerCancellationRequest()
        self._lock = Lock()
        self._state = WorkerState.CREATED

    @property
    def run_id(self) -> str:
        return self._request.run_id

    def state(self) -> WorkerState:
        with self._lock:
            return self._state

    def cancellation_request(self) -> WorkerCancellationRequest:
        return self._cancellation

    def request_cancellation(self, reason: str = "user") -> bool:
        accepted = self._cancellation.request(reason)
        if accepted:
            with self._lock:
                if self._state is WorkerState.RUNNING:
                    self._state = WorkerState.CANCELLING
        return accepted

    @Slot()
    def run(self) -> None:
        with self._lock:
            if self._state is not WorkerState.CREATED:
                return
            self._state = WorkerState.RUNNING

        self.started.emit(self.run_id)

        try:
            self._cancellation.check()
            result = self._request.execute(
                self._request.run_config,
                self._emit_progress,
                self._cancellation.check,
            )
            if not isinstance(result, RunResult):
                raise TypeError("run use case must return RunResult")
            with self._lock:
                self._state = WorkerState.FINISHED
            self.finished.emit(result)
        except CancellationRequested as exception:
            reason = self._cancellation.reason() or _reason_from_exception(exception)
            outcome = WorkerCancellation(
                occurred_at=datetime.now(UTC),
                run_id=self.run_id,
                reason=reason,
                message=_exception_message(exception),
            )
            with self._lock:
                self._state = WorkerState.CANCELLED
            self.cancelled.emit(outcome)
        except Exception as exception:
            failure = WorkerFailure.from_exception(
                self.run_id,
                exception,
            )
            with self._lock:
                self._state = WorkerState.FAILED
            self.failed.emit(failure)
        finally:
            with self._lock:
                self._state = WorkerState.STOPPED
            self.stopped.emit()

    def _emit_progress(self, event: WorkerEvent) -> None:
        if not isinstance(event, (ProgressEvent, LifecycleEvent)):
            raise TypeError("event_sink accepts only ProgressEvent or LifecycleEvent")
        self.progress.emit(event)


class RunWorkerHandle(QObject):
    """GUI-thread owner of one worker, thread and cancellation lifecycle."""

    started = Signal(str)
    progress = Signal(object)
    finished = Signal(object)
    cancelled = Signal(object)
    failed = Signal(object)
    cancellation_requested = Signal(str)
    cleaned_up = Signal(str)

    def __init__(
        self,
        request: RunWorkerRequest,
        *,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if not isinstance(request, RunWorkerRequest):
            raise TypeError("request must be RunWorkerRequest")

        self._lock = Lock()
        self._started = False
        self._cleaned = False
        self._thread: QThread | None = QThread(self)
        self._thread.setObjectName(f"gf-wordbench-run-{request.run_id}")
        self._worker: RunWorker | None = RunWorker(request)
        self._worker.moveToThread(self._thread)
        self._connect()

    @property
    def run_id(self) -> str:
        worker = self._worker
        if worker is not None:
            return worker.run_id
        thread = self._thread
        if thread is not None:
            name = thread.objectName()
            prefix = "gf-wordbench-run-"
            if name.startswith(prefix):
                return name[len(prefix) :]
        raise RuntimeError("worker handle has already been cleaned up")

    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.isRunning()

    def state(self) -> WorkerState:
        worker = self._worker
        return WorkerState.STOPPED if worker is None else worker.state()

    def start(self) -> None:
        with self._lock:
            if self._cleaned:
                raise RuntimeError("worker handle has been cleaned up")
            if self._started:
                raise RuntimeError("worker handle is single-use")
            self._started = True
            thread = self._thread
        if thread is None:
            raise RuntimeError("worker thread is unavailable")
        thread.start()

    def request_cancellation(self, reason: str = "user") -> bool:
        worker = self._worker
        if worker is None:
            return False
        accepted = worker.request_cancellation(reason)
        if accepted:
            self.cancellation_requested.emit(reason)
        return accepted

    def wait_for_shutdown(self, timeout_ms: int) -> bool:
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be an integer")
        if timeout_ms < 0:
            raise ValueError("timeout_ms cannot be negative")
        thread = self._thread
        return True if thread is None else thread.wait(timeout_ms)

    def _connect(self) -> None:
        thread = self._thread
        worker = self._worker
        assert thread is not None
        assert worker is not None

        thread.started.connect(worker.run)

        # Do not forward worker-thread signals signal-to-signal.  A Python
        # callable connected downstream to such a forwarded signal can then be
        # invoked synchronously on the worker thread, which is unsafe for Qt
        # widgets and can leave the GUI apparently stuck after the run itself
        # has completed.  Queue every public event through slots owned by this
        # GUI-affine handle first; the handle then re-emits from the GUI thread.
        queued = Qt.ConnectionType.QueuedConnection
        worker.started.connect(self._forward_started, queued)
        worker.progress.connect(self._forward_progress, queued)
        worker.finished.connect(self._forward_finished, queued)
        worker.cancelled.connect(self._forward_cancelled, queued)
        worker.failed.connect(self._forward_failed, queued)

        worker.stopped.connect(worker.deleteLater)
        worker.stopped.connect(thread.quit)
        thread.finished.connect(self._on_thread_finished)
        thread.finished.connect(thread.deleteLater)

    @Slot(str)
    def _forward_started(self, run_id: str) -> None:
        self.started.emit(run_id)

    @Slot(object)
    def _forward_progress(self, event: object) -> None:
        self.progress.emit(event)

    @Slot(object)
    def _forward_finished(self, result: object) -> None:
        self.finished.emit(result)

    @Slot(object)
    def _forward_cancelled(self, outcome: object) -> None:
        self.cancelled.emit(outcome)

    @Slot(object)
    def _forward_failed(self, failure: object) -> None:
        self.failed.emit(failure)

    @Slot()
    def _on_thread_finished(self) -> None:
        with self._lock:
            if self._cleaned:
                return
            run_id = self.run_id
            self._cleaned = True
            self._worker = None
            self._thread = None
        self.cleaned_up.emit(run_id)


def create_run_worker(
    run_id: str,
    run_config: RunConfig,
    execute: RunApplicationUseCase,
    *,
    parent: QObject | None = None,
) -> RunWorkerHandle:
    return RunWorkerHandle(
        RunWorkerRequest(
            run_id=run_id,
            run_config=run_config,
            execute=execute,
        ),
        parent=parent,
    )


def start_run_worker(
    run_id: str,
    run_config: RunConfig,
    execute: RunApplicationUseCase,
    *,
    parent: QObject | None = None,
) -> RunWorkerHandle:
    handle = create_run_worker(
        run_id,
        run_config,
        execute,
        parent=parent,
    )
    handle.start()
    return handle


def _reason_from_exception(exception: CancellationRequested) -> str:
    detail = exception.detail
    prefix = "reason="
    if detail.startswith(prefix):
        candidate = detail[len(prefix) :].strip()
        if candidate in _ALLOWED_CANCELLATION_REASONS:
            return candidate
    return "controller_policy"


def _cancellation_reason(value: object) -> str:
    canonical = _text(
        value,
        "cancellation reason",
        _MAX_IDENTIFIER,
    )
    if canonical not in _ALLOWED_CANCELLATION_REASONS:
        allowed = ", ".join(sorted(_ALLOWED_CANCELLATION_REASONS))
        raise ValueError(
            f"unsupported cancellation reason {canonical!r}; expected one of: {allowed}"
        )
    return canonical


def _exception_message(exception: Exception) -> str:
    value = str(exception).strip() or type(exception).__name__
    value = value.replace("\x00", "�")
    return value[:_MAX_MESSAGE]


def _evidence_paths(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError("evidence_paths must be an iterable of strings")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value, "evidence path", _MAX_DETAIL)
        if text in seen:
            continue
        result.append(text)
        seen.add(text)
        if len(result) >= _MAX_EVIDENCE_PATHS:
            break
    return tuple(result)


def _text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return value


def _bounded_plain_text(
    value: object,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    value = value.replace("\x00", "�")
    return value[:maximum]


def _utc_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)
