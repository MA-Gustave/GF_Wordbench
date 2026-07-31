from __future__ import annotations

import ast
import dataclasses
import inspect
import threading
from collections.abc import Callable
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
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


_PROGRESS = object()
_RESULT_A = object()
_RESULT_B = object()


@dataclass(frozen=True, slots=True)
class _ResolvedLanguageRunRequest:
    """Opaque request already bound to one resolved language runtime.

    The real GUI request model may contain more fields. These tests intentionally
    retain only the identity-bearing values needed to prove that the generic run
    controller neither reloads a project nor changes language identity.
    """

    language_key: str
    selected_language_path: Path
    validation_profile_path: Path | None
    target_file: str


@dataclass(frozen=True, slots=True)
class _RunPlan:
    request: _ResolvedLanguageRunRequest


@dataclass(frozen=True, slots=True)
class _RunConfig:
    language_key: str
    selected_language_path: Path
    validation_profile_path: Path | None
    target_file: str


_REQUEST_A = _ResolvedLanguageRunRequest(
    language_key="english",
    selected_language_path=Path("C:/work/gf-rgl/src/english"),
    validation_profile_path=None,
    target_file="LangEng.gf",
)

_REQUEST_B = _ResolvedLanguageRunRequest(
    language_key="french",
    selected_language_path=Path("C:/work/gf-rgl/src/french/LangFre.gf"),
    validation_profile_path=Path("C:/work/profiles/french-release.toml"),
    target_file="LangFre.gf",
)


@dataclass(slots=True)
class _Worker:
    config: _RunConfig
    callbacks: WorkerCallbacks[object, object]
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
        self.request = _REQUEST_A
        self.confirmed = True
        self.close_confirmed = True
        self.validation_errors: list[tuple[str, ...]] = []
        self.plans: list[_RunPlan] = []
        self.snapshots: list[ControllerSnapshot] = []
        self.progress: list[object] = []
        self.results: list[object] = []
        self.errors: list[ControllerError] = []
        self.warnings: list[str] = []
        self.close_requests = 0

    def collect_request(self) -> _ResolvedLanguageRunRequest:
        return self.request

    def show_validation_errors(self, errors: tuple[str, ...]) -> None:
        self.validation_errors.append(errors)

    def show_plan(self, plan: _RunPlan) -> None:
        self.plans.append(plan)

    def confirm_run(self, plan: _RunPlan) -> bool:
        del plan
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
        self.validation_errors: tuple[str, ...] = ()
        self.workers: list[_Worker] = []
        self.recorded_results: list[object] = []
        self.persist_calls = 0
        self.persist_failure: Exception | None = None

    def validate_request(
        self,
        request: _ResolvedLanguageRunRequest,
    ) -> tuple[str, ...]:
        assert isinstance(request, _ResolvedLanguageRunRequest)
        return self.validation_errors

    @staticmethod
    def validation_has_errors(validation: tuple[str, ...]) -> bool:
        return bool(validation)

    @staticmethod
    def preview_run(request: _ResolvedLanguageRunRequest) -> _RunPlan:
        return _RunPlan(request=request)

    @staticmethod
    def run_config_from_plan(plan: _RunPlan) -> _RunConfig:
        request = plan.request
        return _RunConfig(
            language_key=request.language_key,
            selected_language_path=request.selected_language_path,
            validation_profile_path=request.validation_profile_path,
            target_file=request.target_file,
        )

    def create_worker(
        self,
        config: _RunConfig,
        callbacks: WorkerCallbacks[object, object],
    ) -> _Worker:
        worker = _Worker(config=config, callbacks=callbacks)
        self.workers.append(worker)
        return worker

    def record_completed_run(self, result: object) -> None:
        self.recorded_results.append(result)

    def persist_state(self) -> None:
        self.persist_calls += 1
        if self.persist_failure is not None:
            raise self.persist_failure

    def services(
        self,
    ) -> GuiControllerServices[
        _ResolvedLanguageRunRequest,
        tuple[str, ...],
        _RunPlan,
        _RunConfig,
        object,
        object,
    ]:
        return GuiControllerServices(
            validate_request=self.validate_request,
            validation_has_errors=self.validation_has_errors,
            preview_run=self.preview_run,
            run_config_from_plan=self.run_config_from_plan,
            create_worker=self.create_worker,
            record_completed_run=self.record_completed_run,
            persist_state=self.persist_state,
            error_from_exception=default_controller_error,
        )

    def controller(
        self,
    ) -> GuiController[
        _ResolvedLanguageRunRequest,
        tuple[str, ...],
        _RunPlan,
        _RunConfig,
        object,
        object,
    ]:
        return GuiController(view=self.view, services=self.services())


def _assert_disposition(value: Enum, *tokens: str) -> None:
    text = f"{value.name} {value.value}".casefold()
    assert any(token.casefold() in text for token in tokens), value


def _emit(
    callbacks: WorkerCallbacks[object, object],
    token: str,
    value: object | None = None,
) -> None:
    callback = next(
        (
            getattr(callbacks, field.name)
            for field in fields(callbacks)
            if token in field.name.casefold()
        ),
        None,
    )
    if callback is None:
        raise AssertionError(f"WorkerCallbacks has no {token!r} callback")
    if value is None:
        callback()
    else:
        callback(value)


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
        snapshot = ControllerSnapshot(
            phase=phase,
            generation=1,
            has_active_worker=phase
            in {
                ControllerPhase.STARTING,
                ControllerPhase.RUNNING,
                ControllerPhase.CANCELLING,
                ControllerPhase.FINISHING,
            },
            cancellation_requested=phase is ControllerPhase.CANCELLING,
            close_pending=phase is ControllerPhase.CLOSING,
            has_last_result=False,
            has_last_error=False,
        )
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
    callback_values: dict[str, Callable[..., None]] = {
        field.name: (lambda *args, **kwargs: None)
        for field in fields(WorkerCallbacks)
    }
    WorkerCallbacks(**callback_values)

    for field in fields(WorkerCallbacks):
        invalid = dict(callback_values)
        invalid[field.name] = object()  # type: ignore[assignment]
        with pytest.raises(TypeError):
            WorkerCallbacks(**invalid)

    required_services = {
        "validate_request": lambda request: (),
        "validation_has_errors": lambda validation: False,
        "preview_run": lambda request: _RunPlan(request),
        "run_config_from_plan": lambda plan: _RunConfig(
            language_key=plan.request.language_key,
            selected_language_path=plan.request.selected_language_path,
            validation_profile_path=plan.request.validation_profile_path,
            target_file=plan.request.target_file,
        ),
        "create_worker": lambda config, callbacks: _Worker(config, callbacks),
    }
    GuiControllerServices(**required_services)

    for name in required_services:
        invalid = dict(required_services)
        invalid[name] = object()
        with pytest.raises(TypeError):
            GuiControllerServices(**invalid)


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

    _assert_disposition(disposition, "reject")
    assert harness.view.plans == [_RunPlan(_REQUEST_A)]
    assert not harness.workers


def test_resolved_language_identity_reaches_the_worker_unchanged() -> None:
    harness = _Harness()
    controller = harness.controller()

    disposition = controller.request_run()

    _assert_disposition(disposition, "start")
    assert len(harness.workers) == 1
    config = harness.workers[0].config
    assert config.language_key == "english"
    assert config.selected_language_path == Path("C:/work/gf-rgl/src/english")
    assert config.validation_profile_path is None
    assert config.target_file == "LangEng.gf"


def test_second_language_request_is_rejected_while_first_run_is_active() -> None:
    harness = _Harness()
    controller = harness.controller()

    first = controller.request_run()
    harness.view.request = _REQUEST_B
    second = controller.request_run()

    _assert_disposition(first, "start")
    _assert_disposition(second, "busy", "active", "reject")
    assert len(harness.workers) == 1
    assert harness.workers[0].config.language_key == "english"
    assert harness.workers[0].started == 1
    assert controller.snapshot.can_cancel
    assert not controller.snapshot.can_start


def test_new_language_request_can_start_only_after_previous_worker_stops() -> None:
    harness = _Harness()
    controller = harness.controller()

    controller.request_run()
    first_worker = harness.workers[0]
    _emit(first_worker.callbacks, "finish", _RESULT_A)
    _emit(first_worker.callbacks, "stop")

    harness.view.request = _REQUEST_B
    disposition = controller.request_run()

    _assert_disposition(disposition, "start")
    assert [worker.config.language_key for worker in harness.workers] == [
        "english",
        "french",
    ]
    assert first_worker.disposals == 1
    assert harness.workers[1].config.validation_profile_path == Path(
        "C:/work/profiles/french-release.toml"
    )


def test_progress_result_persistence_and_worker_cleanup_are_routed() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    _emit(worker.callbacks, "start")
    _emit(worker.callbacks, "progress", _PROGRESS)
    _emit(worker.callbacks, "finish", _RESULT_A)
    _emit(worker.callbacks, "stop")

    assert harness.view.progress == [_PROGRESS]
    assert harness.view.results == [_RESULT_A]
    assert controller.last_result is _RESULT_A
    assert controller.last_error is None
    assert harness.recorded_results == [_RESULT_A]
    assert harness.persist_calls == 1
    assert worker.disposals == 1
    assert controller.snapshot.can_start
    assert not controller.snapshot.can_cancel


def test_cancellation_is_forwarded_to_the_active_worker() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    accepted = controller.cancel_run()

    assert accepted is True
    assert controller.cancel_run() is False
    assert worker.cancellations == 1
    assert not controller.snapshot.can_start


def test_close_during_run_requires_confirmation_and_cancellation() -> None:
    harness = _Harness()
    controller = harness.controller()
    controller.request_run()
    worker = harness.workers[0]

    harness.view.close_confirmed = False
    declined = controller.request_close()
    assert worker.cancellations == 0
    _assert_disposition(declined, "stay", "open")

    harness.view.close_confirmed = True
    accepted = controller.request_close()
    assert worker.cancellations == 1
    _assert_disposition(accepted, "wait", "run")

    _emit(worker.callbacks, "stop")
    assert harness.view.close_requests == 1


def test_state_save_failure_is_presented_as_warning_not_run_failure() -> None:
    harness = _Harness()
    harness.persist_failure = OSError("state store unavailable")
    controller = harness.controller()

    controller.request_run()
    worker = harness.workers[0]
    _emit(worker.callbacks, "finish", _RESULT_A)
    _emit(worker.callbacks, "stop")

    assert harness.view.results == [_RESULT_A]
    assert harness.view.errors == []
    assert harness.view.warnings
    assert controller.last_result is _RESULT_A


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


def test_controller_does_not_own_language_probe_or_project_loading() -> None:
    source = inspect.getsource(controller_module)
    lowered = source.casefold()

    forbidden_text = {
        "languageprobeservice",
        "resolvedlanguagecontext",
        "projectconfig",
        "project.toml",
        "rgl-language-catalog",
        "qfiledialog",
        "pyside6",
    }
    assert all(token not in lowered for token in forbidden_text)

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
