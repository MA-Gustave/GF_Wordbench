from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, unique
import threading
import traceback
from typing import Generic, Protocol, TypeVar, runtime_checkable

RequestT = TypeVar("RequestT")
ValidationT = TypeVar("ValidationT")
PlanT = TypeVar("PlanT")
ConfigT = TypeVar("ConfigT")
ProgressT = TypeVar("ProgressT")
ResultT = TypeVar("ResultT")
ViewRequestT_co = TypeVar("ViewRequestT_co", covariant=True)
ViewValidationT_contra = TypeVar("ViewValidationT_contra", contravariant=True)
ViewPlanT_contra = TypeVar("ViewPlanT_contra", contravariant=True)
ViewProgressT_contra = TypeVar("ViewProgressT_contra", contravariant=True)
ViewResultT_contra = TypeVar("ViewResultT_contra", contravariant=True)
UiAction = Callable[[], None]
UiDispatcher = Callable[[UiAction], None]
_MAX_MESSAGE = 2_048
_MAX_DETAILS = 32_768


@unique
class ControllerPhase(StrEnum):
    IDLE = "idle"
    VALIDATING = "validating"
    PREVIEWING = "previewing"
    CONFIRMING = "confirming"
    STARTING = "starting"
    RUNNING = "running"
    CANCELLING = "cancelling"
    FINISHING = "finishing"
    CLOSING = "closing"
    SWITCHING = "switching"
    CLOSED = "closed"


@unique
class RunRequestDisposition(StrEnum):
    STARTED = "started"
    INVALID = "invalid"
    REJECTED = "rejected"
    BUSY = "busy"
    FAILED = "failed"
    CLOSED = "closed"


@unique
class CloseDisposition(StrEnum):
    READY = "ready"
    WAITING_FOR_RUN = "waiting_for_run"
    STAY_OPEN = "stay_open"
    ALREADY_CLOSED = "already_closed"


@unique
class LanguageSwitchDisposition(StrEnum):
    READY = "ready"
    BUSY = "busy"
    REJECTED = "rejected"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ControllerSnapshot:
    phase: ControllerPhase
    generation: int
    has_active_worker: bool
    cancellation_requested: bool
    close_pending: bool
    has_last_result: bool
    has_last_error: bool

    @property
    def can_start(self) -> bool:
        return (
            self.phase is ControllerPhase.IDLE
            and not self.has_active_worker
            and not self.close_pending
        )

    @property
    def can_cancel(self) -> bool:
        return (
            self.has_active_worker
            and not self.cancellation_requested
            and self.phase in {ControllerPhase.STARTING, ControllerPhase.RUNNING}
        )

    @property
    def can_switch_language(self) -> bool:
        return (
            self.phase is ControllerPhase.IDLE
            and not self.has_active_worker
            and not self.close_pending
        )


@dataclass(frozen=True, slots=True)
class ControllerError:
    category: str
    message: str
    code: str | None = None
    details: str | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        for name in ("category", "message"):
            _text(getattr(self, name), name)
        if self.code is not None:
            _text(self.code, "code")
        if self.details is not None:
            _text(self.details, "details")
        if type(self.retryable) is not bool:
            raise TypeError("retryable must be bool")


@dataclass(frozen=True, slots=True)
class WorkerCallbacks(Generic[ProgressT, ResultT]):
    started: Callable[[], None]
    progress: Callable[[ProgressT], None]
    finished: Callable[[ResultT], None]
    failed: Callable[[Exception], None]
    stopped: Callable[[], None]

    def __post_init__(self) -> None:
        for name in ("started", "progress", "finished", "failed", "stopped"):
            if not callable(getattr(self, name)):
                raise TypeError(f"{name} must be callable")


@runtime_checkable
class WorkerHandle(Protocol):
    def start(self) -> None: ...
    def request_cancellation(self) -> bool | None: ...
    def dispose(self) -> None: ...


@runtime_checkable
class GuiControllerView(
    Protocol[
        ViewRequestT_co,
        ViewValidationT_contra,
        ViewPlanT_contra,
        ViewProgressT_contra,
        ViewResultT_contra,
    ]
):
    def collect_request(self) -> ViewRequestT_co: ...
    def show_validation_errors(self, validation: ViewValidationT_contra) -> None: ...
    def show_plan(self, plan: ViewPlanT_contra) -> None: ...
    def confirm_run(self, plan: ViewPlanT_contra) -> bool: ...
    def show_controller_state(self, snapshot: ControllerSnapshot) -> None: ...
    def show_progress(self, event: ViewProgressT_contra) -> None: ...
    def show_result(self, result: ViewResultT_contra) -> None: ...
    def show_error(self, error: ControllerError) -> None: ...
    def show_warning(self, message: str) -> None: ...
    def confirm_cancel_and_close(self) -> bool: ...
    def close_when_ready(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GuiControllerServices(Generic[RequestT, ValidationT, PlanT, ConfigT, ProgressT, ResultT]):
    validate_request: Callable[[RequestT], ValidationT]
    validation_has_errors: Callable[[ValidationT], bool]
    preview_run: Callable[[RequestT], PlanT]
    run_config_from_plan: Callable[[PlanT], ConfigT]
    create_worker: Callable[[ConfigT, WorkerCallbacks[ProgressT, ResultT]], WorkerHandle]
    record_completed_run: Callable[[ResultT], None] | None = None
    persist_state: Callable[[], None] | None = None
    request_language_switch: Callable[[], bool | None] | None = None
    error_from_exception: Callable[[Exception], ControllerError] | None = None

    def __post_init__(self) -> None:
        required = (
            "validate_request",
            "validation_has_errors",
            "preview_run",
            "run_config_from_plan",
            "create_worker",
        )
        optional = (
            "record_completed_run",
            "persist_state",
            "request_language_switch",
            "error_from_exception",
        )
        for name in required:
            if not callable(getattr(self, name)):
                raise TypeError(f"{name} must be callable")
        for name in optional:
            value = getattr(self, name)
            if value is not None and not callable(value):
                raise TypeError(f"{name} must be callable or None")


class GuiController(Generic[RequestT, ValidationT, PlanT, ConfigT, ProgressT, ResultT]):
    """Toolkit-neutral GUI/application coordinator.
    Worker adapters may use Qt signals, but callbacks supplied here must reach
    this controller through the injected UI dispatcher before touching views.

    Language switching is coordinated here only as a lifecycle transition. The
    injected callback owns disposal of the current runtime and return to the
    language-introduction surface; this controller never probes paths itself.
    """

    __slots__ = (
        "_cancel_requested",
        "_close_pending",
        "_dispatch",
        "_generation",
        "_last_error",
        "_last_result",
        "_lock",
        "_phase",
        "_services",
        "_terminal_received",
        "_view",
        "_worker",
    )

    def __init__(
        self,
        view: GuiControllerView[RequestT, ValidationT, PlanT, ProgressT, ResultT],
        services: GuiControllerServices[RequestT, ValidationT, PlanT, ConfigT, ProgressT, ResultT],
        *,
        dispatch: UiDispatcher | None = None,
    ) -> None:
        if view is None:
            raise TypeError("view must not be None")
        if not isinstance(services, GuiControllerServices):
            raise TypeError("services must be GuiControllerServices")
        if dispatch is not None and not callable(dispatch):
            raise TypeError("dispatch must be callable or None")
        self._view = view
        self._services = services
        self._dispatch = dispatch or _immediate
        self._lock = threading.RLock()
        self._phase = ControllerPhase.IDLE
        self._generation = 0
        self._worker: WorkerHandle | None = None
        self._cancel_requested = False
        self._close_pending = False
        self._terminal_received = False
        self._last_result: ResultT | None = None
        self._last_error: ControllerError | None = None
        self._publish()

    @property
    def snapshot(self) -> ControllerSnapshot:
        with self._lock:
            return ControllerSnapshot(
                phase=self._phase,
                generation=self._generation,
                has_active_worker=self._worker is not None,
                cancellation_requested=self._cancel_requested,
                close_pending=self._close_pending,
                has_last_result=self._last_result is not None,
                has_last_error=self._last_error is not None,
            )

    @property
    def last_result(self) -> ResultT | None:
        with self._lock:
            return self._last_result

    @property
    def last_error(self) -> ControllerError | None:
        with self._lock:
            return self._last_error

    def request_run(self) -> RunRequestDisposition:
        with self._lock:
            if self._phase is ControllerPhase.CLOSED:
                return RunRequestDisposition.CLOSED
            if not self.snapshot.can_start:
                return RunRequestDisposition.BUSY
            self._phase = ControllerPhase.VALIDATING
        self._publish()
        try:
            request = self._view.collect_request()
            validation = self._services.validate_request(request)
            invalid = self._services.validation_has_errors(validation)
            if type(invalid) is not bool:
                raise TypeError("validation_has_errors must return bool")
        except Exception as exc:
            self._pre_worker_failure(exc, "GUI_REQUEST")
            return RunRequestDisposition.FAILED
        if invalid:
            self._set_phase(ControllerPhase.IDLE)
            self._view.show_validation_errors(validation)
            return RunRequestDisposition.INVALID
        self._set_phase(ControllerPhase.PREVIEWING)
        try:
            plan = self._services.preview_run(request)
        except Exception as exc:
            self._pre_worker_failure(exc, "CONFIGURATION")
            return RunRequestDisposition.FAILED
        self._view.show_plan(plan)
        self._set_phase(ControllerPhase.CONFIRMING)
        try:
            confirmed = self._view.confirm_run(plan)
            if type(confirmed) is not bool:
                raise TypeError("confirm_run must return bool")
        except Exception as exc:
            self._pre_worker_failure(exc, "GUI_CONFIRMATION")
            return RunRequestDisposition.FAILED
        if not confirmed:
            self._set_phase(ControllerPhase.IDLE)
            return RunRequestDisposition.REJECTED
        try:
            config = self._services.run_config_from_plan(plan)
        except Exception as exc:
            self._pre_worker_failure(exc, "CONFIGURATION")
            return RunRequestDisposition.FAILED
        return (
            RunRequestDisposition.STARTED
            if self.start_run(config)
            else RunRequestDisposition.FAILED
        )

    def start_run(self, config: ConfigT) -> bool:
        with self._lock:
            if self._phase is ControllerPhase.CLOSED or self._worker is not None:
                return False
            self._generation += 1
            generation = self._generation
            self._phase = ControllerPhase.STARTING
            self._cancel_requested = False
            self._terminal_received = False
            self._last_error = None
        self._publish()
        callbacks = WorkerCallbacks[ProgressT, ResultT](
            started=lambda: self._queue(lambda: self._worker_started(generation)),
            progress=lambda event: self._queue(lambda: self._worker_progress(generation, event)),
            finished=lambda result: self._queue(lambda: self._worker_finished(generation, result)),
            failed=lambda exc: self._queue(lambda: self._worker_failed(generation, exc)),
            stopped=lambda: self._queue(lambda: self._worker_stopped(generation)),
        )
        try:
            worker = self._services.create_worker(config, callbacks)
            if not isinstance(worker, WorkerHandle):
                raise TypeError("create_worker must return WorkerHandle")
        except Exception as exc:
            self._pre_worker_failure(exc, "WORKER")
            return False
        with self._lock:
            if generation != self._generation:
                _dispose(worker)
                return False
            self._worker = worker
        self._publish()
        try:
            worker.start()
        except Exception as exc:
            with self._lock:
                if self._worker is worker:
                    self._worker = None
                    self._phase = ControllerPhase.IDLE
            _dispose(worker)
            self._present_exception(exc, "WORKER_START")
            self._publish()
            return False
        return True

    def cancel_run(self) -> bool:
        with self._lock:
            worker = self._worker
            if (
                worker is None
                or self._cancel_requested
                or self._phase not in {ControllerPhase.STARTING, ControllerPhase.RUNNING}
            ):
                return False
            self._cancel_requested = True
            self._phase = ControllerPhase.CANCELLING
        self._publish()
        try:
            accepted = worker.request_cancellation()
            if accepted is not None and type(accepted) is not bool:
                raise TypeError("request_cancellation must return bool or None")
        except Exception as exc:
            self._cancel_rejected(worker)
            self._present_exception(exc, "CANCELLATION")
            return False
        if accepted is False:
            self._cancel_rejected(worker)
            return False
        return True

    def request_close(self) -> CloseDisposition:
        with self._lock:
            if self._phase in {
                ControllerPhase.CLOSED,
                ControllerPhase.SWITCHING,
            }:
                return CloseDisposition.ALREADY_CLOSED
            active = self._worker is not None
        if not active:
            self._persist()
            self._set_phase(ControllerPhase.CLOSED)
            return CloseDisposition.READY
        try:
            confirmed = self._view.confirm_cancel_and_close()
            if type(confirmed) is not bool:
                raise TypeError("confirm_cancel_and_close must return bool")
        except Exception as exc:
            self._present_exception(exc, "GUI_CONFIRMATION")
            return CloseDisposition.STAY_OPEN
        if not confirmed:
            return CloseDisposition.STAY_OPEN
        with self._lock:
            self._close_pending = True
            finishing = self._phase is ControllerPhase.FINISHING
            if finishing:
                self._phase = ControllerPhase.CLOSING
        self._publish()
        if not finishing:
            self.cancel_run()
        return CloseDisposition.WAITING_FOR_RUN

    def abandon_close_request(self) -> None:
        with self._lock:
            if self._phase is ControllerPhase.CLOSED:
                return
            self._close_pending = False
            if self._worker is None:
                self._phase = ControllerPhase.IDLE
            elif self._cancel_requested:
                self._phase = ControllerPhase.CANCELLING
            else:
                self._phase = ControllerPhase.RUNNING
        self._publish()

    def request_language_switch(self) -> LanguageSwitchDisposition:
        with self._lock:
            if self._phase is ControllerPhase.CLOSED:
                return LanguageSwitchDisposition.CLOSED
            if not self.snapshot.can_switch_language:
                return LanguageSwitchDisposition.BUSY
            callback = self._services.request_language_switch
            if callback is None:
                return LanguageSwitchDisposition.REJECTED
            self._phase = ControllerPhase.SWITCHING
        self._publish()
        self._persist()
        try:
            accepted = callback()
            if accepted is not None and type(accepted) is not bool:
                raise TypeError("request_language_switch must return bool or None")
        except Exception as exc:
            with self._lock:
                if self._phase is ControllerPhase.SWITCHING:
                    self._phase = ControllerPhase.IDLE
            self._present_exception(exc, "LANGUAGE_SWITCH")
            self._publish()
            return LanguageSwitchDisposition.FAILED
        if accepted is False:
            self._set_phase(ControllerPhase.IDLE)
            return LanguageSwitchDisposition.REJECTED
        self._set_phase(ControllerPhase.CLOSED)
        return LanguageSwitchDisposition.READY

    def save_state(self) -> bool:
        return self._persist()

    def _worker_started(self, generation: int) -> None:
        with self._lock:
            if not self._current(generation):
                return
            if self._phase is ControllerPhase.STARTING:
                self._phase = ControllerPhase.RUNNING
        self._publish()

    def _worker_progress(self, generation: int, event: ProgressT) -> None:
        with self._lock:
            if not self._current(generation) or self._terminal_received:
                return
        self._view.show_progress(event)

    def _worker_finished(self, generation: int, result: ResultT) -> None:
        with self._lock:
            if not self._current(generation) or self._terminal_received:
                return
            self._terminal_received = True
            self._phase = ControllerPhase.FINISHING
            self._last_result = result
            self._last_error = None
        self._publish()
        record = self._services.record_completed_run
        if record is not None:
            try:
                record(result)
            except Exception as exc:
                self._warning(
                    "Completed run could not be recorded in application "
                    f"state: {type(exc).__name__}: {exc}"
                )
        self._view.show_result(result)
        self._persist()

    def _worker_failed(self, generation: int, exc: Exception) -> None:
        with self._lock:
            if not self._current(generation) or self._terminal_received:
                return
            self._terminal_received = True
            self._phase = ControllerPhase.FINISHING
        self._present_exception(exc, "RUNTIME")
        self._publish()

    def _worker_stopped(self, generation: int) -> None:
        with self._lock:
            if not self._current(generation):
                return
            worker = self._worker
            missing_terminal = not self._terminal_received
            cancelled = missing_terminal and self._cancel_requested
            close_pending = self._close_pending
            self._worker = None
            self._cancel_requested = False
            self._terminal_received = False
            self._phase = ControllerPhase.CLOSED if close_pending else ControllerPhase.IDLE
        if worker is not None:
            _dispose(worker)
        if missing_terminal:
            if cancelled:
                self._warning(
                    "Run cancellation completed without a structured result. "
                    "Partial evidence remains authoritative."
                )
            else:
                self._present_exception(
                    RuntimeError("worker stopped without a result or framework error"),
                    "WORKER",
                )
        self._publish()
        if close_pending:
            self._persist()
            self._view.close_when_ready()

    def _cancel_rejected(self, worker: WorkerHandle) -> None:
        with self._lock:
            if self._worker is worker:
                self._cancel_requested = False
                self._phase = ControllerPhase.RUNNING
        self._publish()

    def _pre_worker_failure(self, exc: Exception, category: str) -> None:
        with self._lock:
            if self._worker is None:
                self._phase = ControllerPhase.IDLE
        self._present_exception(exc, category)
        self._publish()

    def _present_exception(self, exc: Exception, category: str) -> ControllerError:
        converter = self._services.error_from_exception
        try:
            error = (
                converter(exc)
                if converter is not None
                else default_controller_error(exc, category=category)
            )
            if not isinstance(error, ControllerError):
                raise TypeError("error_from_exception must return ControllerError")
        except Exception as mapping_error:
            error = default_controller_error(mapping_error, category="ERROR_MAPPING")
        with self._lock:
            self._last_error = error
        self._view.show_error(error)
        return error

    def _persist(self) -> bool:
        persist = self._services.persist_state
        if persist is None:
            return True
        try:
            persist()
            return True
        except Exception as exc:
            self._warning(f"Application state could not be saved: {type(exc).__name__}: {exc}")
            return False

    def _warning(self, message: object) -> None:
        self._view.show_warning(_bounded(str(message), _MAX_MESSAGE))

    def _set_phase(self, phase: ControllerPhase) -> None:
        with self._lock:
            self._phase = phase
        self._publish()

    def _publish(self) -> None:
        self._view.show_controller_state(self.snapshot)

    def _queue(self, action: UiAction) -> None:
        try:
            self._dispatch(action)
        except Exception as exc:
            self._present_exception(exc, "UI_DISPATCH")

    def _current(self, generation: int) -> bool:
        return (
            type(generation) is int and generation == self._generation and self._worker is not None
        )


def default_controller_error(exc: Exception, *, category: str = "RUNTIME") -> ControllerError:
    if not isinstance(exc, Exception):
        raise TypeError("exc must be an Exception")
    message = str(exc).strip() or type(exc).__name__
    code_value = getattr(exc, "code", None)
    code = str(code_value).strip() if code_value is not None else None
    retryable = getattr(exc, "retryable", False)
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
    return ControllerError(
        category=_bounded(category.upper(), _MAX_MESSAGE),
        message=_bounded(message, _MAX_MESSAGE),
        code=_bounded(code, _MAX_MESSAGE) if code else None,
        details=_bounded(details, _MAX_DETAILS) if details else None,
        retryable=retryable if type(retryable) is bool else False,
    )


def _immediate(action: UiAction) -> None:
    action()


def _dispose(worker: WorkerHandle) -> None:
    try:
        worker.dispose()
    except Exception:
        pass


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _bounded(value: str, limit: int) -> str:
    normalized = value.replace("\x00", "�").strip()
    if not normalized:
        normalized = "Unknown error"
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 3]}..."


__all__ = (
    "CloseDisposition",
    "ControllerError",
    "ControllerPhase",
    "ControllerSnapshot",
    "GuiController",
    "GuiControllerServices",
    "GuiControllerView",
    "LanguageSwitchDisposition",
    "RunRequestDisposition",
    "UiAction",
    "UiDispatcher",
    "WorkerCallbacks",
    "WorkerHandle",
    "default_controller_error",
)
