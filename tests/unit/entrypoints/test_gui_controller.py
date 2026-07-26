from __future__ import annotations

import ast
import dataclasses
import inspect
import threading
from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from enum import Enum
from types import ModuleType
from typing import Any

import pytest

from gf_wordbench.entrypoints.gui import controller as controller_module
from gf_wordbench.entrypoints.gui.controller import (
    CloseDisposition,
    ControllerError,
    ControllerPhase,
    ControllerSnapshot,
    GuiController,
    GuiControllerServices,
    GuiControllerView,
    RunRequestDisposition,
    WorkerCallbacks,
    WorkerHandle,
    default_controller_error,
)


_REQUEST = object()
_PLAN = object()
_RESULT = object()
_PROGRESS = object()


def _required_fields(cls: type[Any]) -> tuple[dataclasses.Field[Any], ...]:
    return tuple(
        field
        for field in fields(cls)
        if field.default is MISSING and field.default_factory is MISSING
    )


def _enum_member(enum_type: type[Enum], *tokens: str) -> Enum:
    normalized = tuple(token.casefold() for token in tokens)
    for member in enum_type:
        candidate = f"{member.name} {member.value}".casefold()
        if any(token in candidate for token in normalized):
            return member
    raise AssertionError(
        f"{enum_type.__name__} has no member matching {tokens!r}: "
        f"{tuple(enum_type)!r}"
    )


def _default_value(field: dataclasses.Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default
    if field.default_factory is not MISSING:
        return field.default_factory()

    name = field.name.casefold()
    if "phase" in name:
        return _enum_member(ControllerPhase, "ready", "idle")
    if "error" in name or "result" in name or "worker" in name:
        return None
    if "close" in name or name.startswith("is_") or name.startswith("has_"):
        return False
    if "generation" in name or "sequence" in name or "count" in name:
        return 0
    if "thread" in name:
        return threading.get_ident()
    if "title" in name:
        return "Validation error"
    if "message" in name:
        return "The validation request could not be completed."
    if "details" in name or "trace" in name:
        return "technical details"
    if "code" in name or "kind" in name or "category" in name:
        return "runtime_error"
    if "recover" in name or "retry" in name:
        return False
    raise AssertionError(
        f"No test value is defined for required field "
        f"{field.name!r} on {field._field_type!r}"
    )


def _construct(cls: type[Any], **overrides: Any) -> Any:
    values = {
        field.name: overrides.get(field.name, _default_value(field))
        for field in fields(cls)
    }
    return cls(**values)


def _callback_value(name: str, harness: "_Harness") -> Callable[..., Any]:
    token = name.casefold()

    if "validate" in token:
        return lambda request: harness.validation_errors
    if "plan" in token or "preview" in token or "resolve" in token:
        return lambda request: harness.plan
    if "worker" in token and (
        "create" in token or "factory" in token or "build" in token
    ):
        return harness.create_worker
    if "persist" in token or "save" in token or "store" in token:
        return harness.persist
    if "error" in token or "exception" in token:
        return default_controller_error
    if "queue" in token or "dispatch" in token or "invoke" in token:
        return lambda callback: callback()
    if "thread" in token and "id" in token:
        return threading.get_ident
    if "current" in token and "thread" in token:
        return lambda: True
    if "clock" in token or token.endswith("now"):
        return lambda: 0.0
    if "warning" in token:
        return harness.warnings.append

    raise AssertionError(f"Unhandled GuiControllerServices field: {name}")


@dataclass(slots=True)
class _Worker:
    callbacks: WorkerCallbacks[Any, Any]
    started: int = 0
    cancellations: int = 0
    disposals: int = 0

    def start(self) -> None:
        self.started += 1

    def request_cancellation(self) -> bool:
        self.cancellations += 1
        return True

    def dispose(self) -> None:
        self.disposals += 1


class _View:
    def __init__(self) -> None:
        self.request: object = _REQUEST
        self.confirmed = True
        self.close_confirmed = True
        self.validation_errors: list[object] = []
        self.plans: list[object] = []
        self.snapshots: list[ControllerSnapshot] = []
        self.progress: list[object] = []
        self.results: list[object] = []
        self.errors: list[ControllerError] = []
        self.warnings: list[str] = []
        self.close_requests = 0

    def collect_request(self) -> object:
        return self.request

    def show_validation_errors(self, errors: object) -> None:
        self.validation_errors.append(errors)

    def show_plan(self, plan: object) -> None:
        self.plans.append(plan)

    def confirm_run(self, plan: object) -> bool:
        return self.confirmed

    def show_controller_state(self, snapshot: ControllerSnapshot) -> None:
        self.snapshots.append(snapshot)

    def show_progress(self, progress: object) -> None:
        self.progress.append(progress)

    def show_result(self, result: object) -> None:
        self.results.append(result)

    def show_error(self, error: ControllerError) -> None:
        self.errors.append(error)

    def show_warning(self, message: str) -> None:
        self.warnings.append(message)

    def confirm_cancel_and_close(self) -> bool:
        return self.close_confirmed

    def close_when_ready(self) -> None:
        self.close_requests += 1


class _Harness:
    def __init__(self) -> None:
        self.view = _View()
        self.plan = _PLAN
        self.validation_errors: tuple[str, ...] = ()
        self.workers: list[_Worker] = []
        self.persisted: list[object] = []
        self.warnings: list[str] = []

    def create_worker(self, *args: Any, **kwargs: Any) -> _Worker:
        callbacks = next(
            (
                value
                for value in (*args, *kwargs.values())
                if isinstance(value, WorkerCallbacks)
            ),
            None,
        )
        assert callbacks is not None, "worker factory did not receive WorkerCallbacks"
        worker = _Worker(callbacks)
        self.workers.append(worker)
        return worker

    def persist(self, *values: object) -> None:
        self.persisted.extend(values or (None,))

    def services(self) -> GuiControllerServices[Any, Any, Any, Any]:
        kwargs = {
            field.name: _callback_value(field.name, self)
            for field in _required_fields(GuiControllerServices)
        }
        return GuiControllerServices(**kwargs)

    def controller(self) -> GuiController[Any, Any, Any, Any]:
        parameters = inspect.signature(GuiController).parameters
        kwargs: dict[str, object] = {}
        for name, parameter in parameters.items():
            if name == "self":
                continue
            token = name.casefold()
            if "view" in token:
                kwargs[name] = self.view
            elif "service" in token:
                kwargs[name] = self.services()
            elif parameter.default is inspect.Parameter.empty:
                raise AssertionError(f"Unhandled GuiController parameter: {name}")
        return GuiController(**kwargs)


def _assert_disposition(value: Enum, *tokens: str) -> None:
    text = f"{value.name} {value.value}".casefold()
    assert any(token.casefold() in text for token in tokens), value


def _emit(callbacks: WorkerCallbacks[Any, Any], token: str, value: Any = None) -> None:
    for field in fields(callbacks):
        if token in field.name.casefold():
            callback = getattr(callbacks, field.name)
            if value is None:
                callback()
            else:
                callback(value)
            return
    raise AssertionError(f"WorkerCallbacks has no {token!r} callback")


def test_controller_module_owns_the_locked_public_surface() -> None:
    expected = {
        "CloseDisposition",
        "ControllerError",
        "ControllerPhase",
        "ControllerSnapshot",
        "GuiController",
        "GuiControllerServices",
        "GuiControllerView",
        "RunRequestDisposition",
        "WorkerCallbacks",
        "WorkerHandle",
        "default_controller_error",
    }

    assert expected <= set(controller_module.__all__)
    assert all(getattr(controller_module, name) is globals()[name] for name in expected)


def test_controller_enums_use_unique_stable_string_tokens() -> None:
    for enum_type in (ControllerPhase, RunRequestDisposition, CloseDisposition):
        values = tuple(member.value for member in enum_type)
        assert values
        assert len(values) == len(set(values))
        assert all(isinstance(value, str) and value.strip() == value for value in values)
        assert all(value and value.casefold() == value for value in values)


def test_controller_value_objects_are_frozen_slotted_dataclasses() -> None:
    for cls in (
        ControllerSnapshot,
        ControllerError,
        WorkerCallbacks,
        GuiControllerServices,
    ):
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen
        assert hasattr(cls, "__slots__")


def test_snapshot_capabilities_never_allow_start_and_cancel_together() -> None:
    observed_start = False
    observed_cancel = False

    for phase in ControllerPhase:
        overrides = {
            field.name: phase
            for field in fields(ControllerSnapshot)
            if "phase" in field.name.casefold()
        }
        snapshot = _construct(ControllerSnapshot, **overrides)
        observed_start |= snapshot.can_start
        observed_cancel |= snapshot.can_cancel
        assert not (snapshot.can_start and snapshot.can_cancel)

    assert observed_start
    assert observed_cancel


def test_runtime_protocols_describe_only_transport_and_presentation() -> None:
    assert inspect.isclass(WorkerHandle)
    assert inspect.isclass(GuiControllerView)

    worker_members = {
        name
        for name, value in WorkerHandle.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    view_members = {
        name
        for name, value in GuiControllerView.__dict__.items()
        if callable(value) and not name.startswith("_")
    }

    assert worker_members == {"start", "request_cancellation", "dispose"}
    assert view_members == {
        "collect_request",
        "show_validation_errors",
        "show_plan",
        "confirm_run",
        "show_controller_state",
        "show_progress",
        "show_result",
        "show_error",
        "show_warning",
        "confirm_cancel_and_close",
        "close_when_ready",
    }


def test_callback_and_service_bundles_reject_non_callable_dependencies() -> None:
    for cls in (WorkerCallbacks, GuiControllerServices):
        required = _required_fields(cls)
        assert required
        valid = {field.name: (lambda *args, **kwargs: None) for field in required}
        cls(**valid)

        for field in required:
            invalid = dict(valid)
            invalid[field.name] = object()
            with pytest.raises(TypeError):
                cls(**invalid)


def test_invalid_request_does_not_create_or_start_worker() -> None:
    harness = _Harness()
    harness.validation_errors = ("target is required",)
    controller = harness.controller()

    disposition = controller.request_run()

    _assert_disposition(disposition, "invalid", "reject")
    assert not harness.workers
    assert harness.view.validation_errors == [harness.validation_errors]
    assert harness.view.plans == []


def test_rejected_confirmation_does_not_create_worker() -> None:
    harness = _Harness()
    harness.view.confirmed = False
    controller = harness.controller()

    disposition = controller.request_run()

    _assert_disposition(disposition, "cancel", "declin", "reject")
    assert harness.view.plans == [_PLAN]
    assert not harness.workers


def test_one_worker_is_started_and_second_run_is_rejected() -> None:
    harness = _Harness()
    controller = harness.controller()

    first = controller.request_run()
    second = controller.request_run()

    _assert_disposition(first, "start")
    _assert_disposition(second, "busy", "active", "reject")
    assert len(harness.workers) == 1
    assert harness.workers[0].started == 1
    assert controller.snapshot().can_cancel
    assert not controller.snapshot().can_start


def test_progress_result_persistence_and_worker_cleanup_are_routed() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    _emit(worker.callbacks, "start")
    _emit(worker.callbacks, "progress", _PROGRESS)
    _emit(worker.callbacks, "finish", _RESULT)
    _emit(worker.callbacks, "stop")

    assert harness.view.progress == [_PROGRESS]
    assert harness.view.results == [_RESULT]
    assert controller.last_result is _RESULT
    assert controller.last_error is None
    assert harness.persisted
    assert worker.disposals == 1
    assert controller.snapshot().can_start
    assert not controller.snapshot().can_cancel


def test_cancellation_is_forwarded_to_the_active_worker() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    disposition = controller.cancel_run()

    _assert_disposition(disposition, "request", "cancel")
    assert worker.cancellations == 1
    assert not controller.snapshot().can_start


def test_close_during_run_requires_confirmation_and_cancellation() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    harness.view.close_confirmed = False
    declined = controller.request_close()
    assert worker.cancellations == 0
    _assert_disposition(declined, "continue", "stay", "reject")

    harness.view.close_confirmed = True
    accepted = controller.request_close()
    assert worker.cancellations == 1
    _assert_disposition(accepted, "wait", "cancel", "defer")

    _emit(worker.callbacks, "stop")
    assert harness.view.close_requests == 1


def test_state_save_failure_is_presented_as_warning_not_run_failure() -> None:
    harness = _Harness()

    def fail_persist(*values: object) -> None:
        raise OSError("state store unavailable")

    services = harness.services()
    replacements = {
        field.name: fail_persist
        for field in fields(services)
        if any(token in field.name.casefold() for token in ("persist", "save", "store"))
    }
    assert replacements
    services = dataclasses.replace(services, **replacements)

    parameters = inspect.signature(GuiController).parameters
    kwargs = {
        name: harness.view if "view" in name.casefold() else services
        for name, parameter in parameters.items()
        if name != "self" and parameter.default is inspect.Parameter.empty
    }
    controller = GuiController(**kwargs)
    controller.request_run()
    worker = harness.workers[0]
    _emit(worker.callbacks, "finish", _RESULT)
    _emit(worker.callbacks, "stop")

    assert harness.view.results == [_RESULT]
    assert harness.view.errors == []
    assert harness.view.warnings


def test_default_controller_error_is_bounded_and_actionable() -> None:
    error = default_controller_error(RuntimeError("boom\nsecret detail"))

    assert isinstance(error, ControllerError)
    text = " ".join(
        str(getattr(error, field.name))
        for field in fields(error)
        if getattr(error, field.name) is not None
    )
    assert "RuntimeError" in text or "runtime" in text.casefold()
    assert "boom" in text
    assert len(text) < 20_000


def test_controller_module_has_no_validation_stage_dependency() -> None:
    source = inspect.getsource(controller_module)
    tree = ast.parse(source)
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "gf_wordbench" not in imported_roots
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "enum",
        "threading",
        "traceback",
        "typing",
    }
