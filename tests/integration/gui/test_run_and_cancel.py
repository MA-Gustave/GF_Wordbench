from __future__ import annotations

import inspect
import threading
from typing import Any

import pytest

pytest.importorskip("PySide6")

from gf_wordbench.entrypoints.gui.workers import (
    CancellationCheck,
    RunApplicationUseCase,
    RunWorker,
    RunWorkerRequest,
    WorkerCancellationRequest,
    WorkerEventSink,
)
from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.runs.public import RunConfig, RunResult

pytestmark = pytest.mark.gui


class _BlockingRun:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.cancellation: WorkerCancellationRequest | None = None

    def __call__(
        self,
        run_config: RunConfig,
        event_sink: WorkerEventSink,
        cancellation_check: CancellationCheck,
    ) -> RunResult:
        del run_config, event_sink, cancellation_check
        self.started.set()
        cancellation = self.cancellation
        if cancellation is None:
            raise RuntimeError("worker cancellation request was not attached")
        while True:
            cancellation.check()
            cancellation.wait(0.01)


def _request_cancellation(target: object, reason: str) -> object:
    method = getattr(target, "request_cancellation", None)
    if not callable(method):
        method = getattr(target, "request", None)
    if not callable(method):
        raise AssertionError("object exposes no cancellation request method")

    signature = inspect.signature(method)
    parameters = tuple(signature.parameters.values())
    required = tuple(
        parameter
        for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind
        not in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
    )
    if not required:
        return method()

    parameter = required[0]
    if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
        return method(**{parameter.name: reason})
    return method(reason)


def _run_config_placeholder() -> RunConfig:
    return object.__new__(RunConfig)


def _worker_request(application: RunApplicationUseCase) -> RunWorkerRequest:
    return RunWorkerRequest(
        run_id="gui-run-cancel-test",
        run_config=_run_config_placeholder(),
        execute=application,
    )


def _run_worker(request: RunWorkerRequest) -> RunWorker:
    return RunWorker(request)


def _terminal(state: object) -> bool:
    value: Any = getattr(state, "is_terminal", False)
    return bool(value() if callable(value) else value)


def test_worker_cancellation_request_is_shared_and_idempotent() -> None:
    cancellation = WorkerCancellationRequest()

    assert cancellation.is_requested() is False
    assert cancellation.is_cancellation_requested() is False
    assert cancellation.is_cancelled() is False

    _request_cancellation(cancellation, "user requested cancellation")
    _request_cancellation(cancellation, "duplicate request")

    assert cancellation.is_requested() is True
    assert cancellation.is_cancellation_requested() is True
    assert cancellation.is_cancelled() is True
    assert cancellation.wait(0) is True
    assert cancellation.reason()
    assert cancellation.cancellation_reason()

    with pytest.raises(CancellationRequested):
        cancellation.check()


def test_run_worker_accepts_cancellation_and_stops_without_thread_leak() -> None:
    application = _BlockingRun()
    worker = _run_worker(_worker_request(application))
    application.cancellation = worker.cancellation_request()
    escaped: list[BaseException] = []

    def invoke() -> None:
        try:
            worker.run()
        except BaseException as exc:
            escaped.append(exc)

    thread = threading.Thread(
        target=invoke,
        name="gf-wordbench-gui-run-cancel-test",
        daemon=False,
    )
    thread.start()

    assert application.started.wait(1.0), "worker did not start"
    assert worker.cancellation_request().is_requested() is False

    _request_cancellation(worker, "user")
    thread.join(2.0)

    assert thread.is_alive() is False, "GUI worker thread did not stop"
    assert escaped == []
    assert worker.cancellation_request().is_requested() is True
    assert _terminal(worker.state())
    assert worker.state().is_terminal
