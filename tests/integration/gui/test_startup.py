"""Headless integration coverage for the canonical GUI startup boundary."""

from __future__ import annotations

import ast
import importlib
import inspect
import sys
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

GUI_MODULE: Final = "gf_wordbench.entrypoints.gui.main"
GUI_SCRIPT_NAME: Final = "gf-wordbench-gui"
GUI_SCRIPT_TARGET: Final = f"{GUI_MODULE}:main"
SUCCESS_EXIT_CODE: Final = 23

pytestmark = pytest.mark.gui


@dataclass(slots=True)
class _Signal:
    callbacks: list[Callable[[], None]] = field(default_factory=list)

    def connect(self, callback: Callable[[], None]) -> None:
        self.callbacks.append(callback)

    def emit(self) -> None:
        for callback in tuple(self.callbacks):
            callback()


@dataclass(slots=True)
class _FakeApplication:
    events: list[str]
    aboutToQuit: _Signal = field(default_factory=_Signal)

    def exec(self) -> int:
        self.events.append("event_loop")
        self.aboutToQuit.emit()
        return SUCCESS_EXIT_CODE

    def exec_(self) -> int:
        return self.exec()

    def quit(self) -> None:
        self.events.append("quit")

    def setApplicationName(self, _value: str) -> None:
        self.events.append("application_name")

    def setApplicationDisplayName(self, _value: str) -> None:
        self.events.append("application_display_name")

    def setApplicationVersion(self, _value: str) -> None:
        self.events.append("application_version")

    def setOrganizationName(self, _value: str) -> None:
        self.events.append("organization_name")


@dataclass(slots=True)
class _FakeWindow:
    events: list[str]

    def show(self) -> None:
        self.events.append("show")

    def raise_(self) -> None:
        self.events.append("raise")

    def activateWindow(self) -> None:
        self.events.append("activate")


@dataclass(slots=True)
class _FakeRuntime:
    events: list[str]
    window: _FakeWindow = field(init=False)

    def __post_init__(self) -> None:
        self.window = _FakeWindow(self.events)

    def shutdown(self) -> None:
        self.events.append("shutdown")


@dataclass(slots=True)
class _Reporter:
    events: list[str]
    reports: list[BaseException] = field(default_factory=list)

    def report(
        self,
        exception_type: type[BaseException],
        exception: BaseException,
        traceback: Any = None,
        **_kwargs: object,
    ) -> None:
        del exception_type, traceback
        self.events.append("report")
        self.reports.append(exception)

    def report_thread_exception(self, args: object) -> None:
        exception = getattr(args, "exc_value", RuntimeError("thread failure"))
        self.report(type(exception), exception)


class _ReporterFactory:
    def __init__(self, reporter: _Reporter) -> None:
        self.reporter = reporter

    def __call__(self, *_args: object, **_kwargs: object) -> _Reporter:
        return self.reporter


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_gui_module() -> ModuleType:
    return importlib.import_module(GUI_MODULE)


def _patch_startup_seams(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    *,
    application: _FakeApplication,
    runtime_factory: Callable[[], _FakeRuntime],
    reporter: _Reporter,
    events: list[str],
) -> None:
    hook_state = object()

    def create_application(*_args: object, **_kwargs: object) -> _FakeApplication:
        events.append("create_application")
        return application

    def configure_application(*_args: object, **_kwargs: object) -> None:
        events.append("configure_application")

    def default_runtime_factory(*_args: object, **_kwargs: object) -> _FakeRuntime:
        events.append("create_runtime")
        return runtime_factory()

    def validate_runtime(runtime: _FakeRuntime) -> _FakeRuntime:
        events.append("validate_runtime")
        return runtime

    def show_window(window: _FakeWindow) -> None:
        events.append("show_window")
        window.show()

    def install_hooks(*_args: object, **_kwargs: object) -> object:
        events.append("install_hooks")
        return hook_state

    def restore_hooks(state: object) -> None:
        assert state is hook_state
        events.append("restore_hooks")

    monkeypatch.setattr(module, "_create_qapplication", create_application)
    monkeypatch.setattr(module, "_configure_application", configure_application)
    monkeypatch.setattr(module, "_default_runtime_factory", default_runtime_factory)
    monkeypatch.setattr(module, "_validate_runtime", validate_runtime)
    monkeypatch.setattr(module, "_show_window", show_window)
    monkeypatch.setattr(module, "install_exception_hooks", install_hooks)
    monkeypatch.setattr(module, "restore_exception_hooks", restore_hooks)
    monkeypatch.setattr(module, "FatalErrorReporter", _ReporterFactory(reporter))


def _invoke_main(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    runtime_factory: Callable[[], _FakeRuntime],
) -> int:
    main = getattr(module, "main")
    signature = inspect.signature(main)
    arguments = [GUI_SCRIPT_NAME, "--startup-smoke-test"]
    positional: list[object] = []
    keywords: dict[str, object] = {}

    if "argv" in signature.parameters:
        keywords["argv"] = arguments
    else:
        positional_parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if positional_parameters:
            positional.append(arguments)
        else:
            monkeypatch.setattr(sys, "argv", arguments)

    for name in ("runtime_factory", "gui_runtime_factory"):
        if name in signature.parameters:
            keywords[name] = runtime_factory
            break

    value = main(*positional, **keywords)
    assert isinstance(value, int) and not isinstance(value, bool)
    return value


def _top_level_imports(module_path: Path) -> Iterator[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    for node in tree.body:
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            yield node.module


def test_distribution_declares_the_canonical_gui_entrypoint() -> None:
    pyproject_path = _repository_root() / "pyproject.toml"
    document = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert document["project"]["gui-scripts"] == {
        GUI_SCRIPT_NAME: GUI_SCRIPT_TARGET,
    }


def test_importing_the_gui_entrypoint_does_not_eagerly_import_qt() -> None:
    module_path = (
        _repository_root()
        / "src"
        / "gf_wordbench"
        / "entrypoints"
        / "gui"
        / "main.py"
    )

    imported_modules = tuple(_top_level_imports(module_path))

    assert not any(name == "PySide6" or name.startswith("PySide6.") for name in imported_modules)


def test_headless_startup_constructs_shows_runs_and_shuts_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(events)
    runtime = _FakeRuntime(events)
    reporter = _Reporter(events)

    def runtime_factory() -> _FakeRuntime:
        return runtime

    _patch_startup_seams(
        monkeypatch,
        module,
        application=application,
        runtime_factory=runtime_factory,
        reporter=reporter,
        events=events,
    )

    exit_code = _invoke_main(monkeypatch, module, runtime_factory)

    assert exit_code == SUCCESS_EXIT_CODE
    assert reporter.reports == []
    assert events.index("create_application") < events.index("configure_application")
    assert events.index("configure_application") < events.index("create_runtime")
    assert events.index("create_runtime") < events.index("validate_runtime")
    assert events.index("validate_runtime") < events.index("show_window")
    assert events.index("show_window") < events.index("event_loop")
    assert events.index("event_loop") < events.index("shutdown")
    assert events.index("shutdown") < events.index("restore_hooks")
    assert events.count("event_loop") == 1
    assert events.count("shutdown") == 1


def test_startup_failure_is_reported_and_hooks_are_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(events)
    reporter = _Reporter(events)
    failure = RuntimeError("simulated GUI bootstrap failure")

    def failing_runtime_factory() -> _FakeRuntime:
        raise failure

    _patch_startup_seams(
        monkeypatch,
        module,
        application=application,
        runtime_factory=failing_runtime_factory,
        reporter=reporter,
        events=events,
    )

    exit_code = _invoke_main(monkeypatch, module, failing_runtime_factory)

    assert exit_code != 0
    assert reporter.reports == [failure]
    assert "event_loop" not in events
    assert "shutdown" not in events
    assert events[-1] == "restore_hooks"
