"""Headless integration coverage for the ADR-0015 GUI startup boundary."""

from __future__ import annotations

import ast
import importlib
import sys
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

GUI_MODULE: Final = "gf_wordbench.entrypoints.gui.main"
BOOTSTRAP_MODULE: Final = "gf_wordbench.bootstrap"
GUI_SCRIPT_NAME: Final = "gf-wordbench-gui"
GUI_SCRIPT_TARGET: Final = f"{GUI_MODULE}:main"
STARTUP_RUNTIME_FACTORY: Final = "build_startup_gui_runtime"
QT_SUCCESS_EXIT_CODE: Final = 0
QT_FAILURE_EXIT_CODE: Final = 23

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
    qt_exit_code: int = QT_SUCCESS_EXIT_CODE
    aboutToQuit: _Signal = field(default_factory=_Signal)

    def exec(self) -> int:
        self.events.append("event_loop")
        self.aboutToQuit.emit()
        return self.qt_exit_code

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

    def setOrganizationDomain(self, _value: str) -> None:
        self.events.append("organization_domain")

    def setQuitOnLastWindowClosed(self, _value: bool) -> None:
        self.events.append("quit_on_last_window")


@dataclass(slots=True)
class _FakeIntroductionWindow:
    events: list[str]

    def show(self) -> None:
        self.events.append("show_introduction")

    def raise_(self) -> None:
        self.events.append("raise_introduction")

    def activateWindow(self) -> None:
        self.events.append("activate_introduction")


@dataclass(slots=True)
class _FakeStartupRuntime:
    events: list[str]
    window: _FakeIntroductionWindow = field(init=False)

    def __post_init__(self) -> None:
        self.window = _FakeIntroductionWindow(self.events)

    def shutdown(self) -> None:
        self.events.append("shutdown_startup_runtime")


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


def _load_bootstrap_module() -> ModuleType:
    return importlib.import_module(BOOTSTRAP_MODULE)


def _patch_process_seams(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    *,
    application: _FakeApplication,
    reporter: _Reporter,
    events: list[str],
    owns_application: bool = True,
) -> None:
    """Patch process and Qt boundaries without replacing runtime composition."""

    hook_state = object()

    def create_application(
        *_args: object,
        **_kwargs: object,
    ) -> tuple[_FakeApplication, bool]:
        events.append("create_application")
        return application, owns_application

    def configure_application(*_args: object, **_kwargs: object) -> None:
        events.append("configure_application")

    def install_hooks(*_args: object, **_kwargs: object) -> object:
        events.append("install_hooks")
        return hook_state

    def restore_hooks(state: object) -> None:
        assert state is hook_state
        events.append("restore_hooks")

    monkeypatch.setattr(module, "_create_qapplication", create_application)
    monkeypatch.setattr(module, "_configure_application", configure_application)
    monkeypatch.setattr(module, "install_exception_hooks", install_hooks)
    monkeypatch.setattr(module, "restore_exception_hooks", restore_hooks)
    monkeypatch.setattr(module, "FatalErrorReporter", _ReporterFactory(reporter))


def _patch_startup_runtime_builder(
    monkeypatch: pytest.MonkeyPatch,
    *,
    application: _FakeApplication,
    events: list[str],
    factory: Callable[[], _FakeStartupRuntime],
) -> None:
    """Patch the public bootstrap provider used by the real default factory."""

    bootstrap = _load_bootstrap_module()

    def build_startup_gui_runtime(
        provided_application: object,
    ) -> _FakeStartupRuntime:
        assert provided_application is application
        events.append("build_startup_runtime")
        return factory()

    monkeypatch.setattr(
        bootstrap,
        STARTUP_RUNTIME_FACTORY,
        build_startup_gui_runtime,
        raising=True,
    )


def _invoke_main(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
) -> int:
    main = getattr(module, "main")
    arguments = [GUI_SCRIPT_NAME, "--startup-smoke-test"]

    try:
        value = main(argv=arguments)
    except TypeError as exc:
        if "argv" not in str(exc):
            raise
        monkeypatch.setattr(sys, "argv", arguments)
        value = main()

    assert isinstance(value, int) and not isinstance(value, bool)
    return value


def _top_level_imports(module_path: Path) -> Iterator[str]:
    tree = ast.parse(
        module_path.read_text(encoding="utf-8"),
        filename=str(module_path),
    )
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

    assert not any(
        name == "PySide6" or name.startswith("PySide6.")
        for name in imported_modules
    )


def test_default_factory_uses_the_startup_runtime_bootstrap_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    bootstrap = _load_bootstrap_module()
    events: list[str] = []
    application = _FakeApplication(events)
    runtime = _FakeStartupRuntime(events)

    def build_startup_gui_runtime(provided_application: object) -> object:
        assert provided_application is application
        events.append("build_startup_runtime")
        return runtime

    monkeypatch.setattr(
        bootstrap,
        STARTUP_RUNTIME_FACTORY,
        build_startup_gui_runtime,
        raising=True,
    )

    actual = module._default_runtime_factory(application)

    assert actual is runtime
    assert events == ["build_startup_runtime"]


def test_headless_startup_shows_introduction_runs_and_shuts_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(events)
    runtime = _FakeStartupRuntime(events)
    reporter = _Reporter(events)

    _patch_process_seams(
        monkeypatch,
        module,
        application=application,
        reporter=reporter,
        events=events,
    )
    _patch_startup_runtime_builder(
        monkeypatch,
        application=application,
        events=events,
        factory=lambda: runtime,
    )

    exit_code = _invoke_main(monkeypatch, module)

    assert exit_code == module.EXIT_OK
    assert reporter.reports == []
    assert events.index("create_application") < events.index(
        "configure_application"
    )
    assert events.index("configure_application") < events.index(
        "build_startup_runtime"
    )
    assert events.index("build_startup_runtime") < events.index(
        "show_introduction"
    )
    assert events.index("show_introduction") < events.index("event_loop")
    assert events.index("event_loop") < events.index(
        "shutdown_startup_runtime"
    )
    assert events.index("shutdown_startup_runtime") < events.index(
        "restore_hooks"
    )
    assert events.count("event_loop") == 1
    assert events.count("show_introduction") == 1
    assert events.count("shutdown_startup_runtime") == 1


def test_existing_qapplication_shows_introduction_without_nested_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(events)
    runtime = _FakeStartupRuntime(events)
    reporter = _Reporter(events)

    _patch_process_seams(
        monkeypatch,
        module,
        application=application,
        reporter=reporter,
        events=events,
        owns_application=False,
    )
    _patch_startup_runtime_builder(
        monkeypatch,
        application=application,
        events=events,
        factory=lambda: runtime,
    )

    exit_code = _invoke_main(monkeypatch, module)

    assert exit_code == module.EXIT_OK
    assert reporter.reports == []
    assert "show_introduction" in events
    assert "event_loop" not in events
    assert events.count("shutdown_startup_runtime") == 1
    assert events[-1] == "restore_hooks"


def test_nonzero_qt_exit_is_mapped_to_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(
        events,
        qt_exit_code=QT_FAILURE_EXIT_CODE,
    )
    runtime = _FakeStartupRuntime(events)
    reporter = _Reporter(events)

    _patch_process_seams(
        monkeypatch,
        module,
        application=application,
        reporter=reporter,
        events=events,
    )
    _patch_startup_runtime_builder(
        monkeypatch,
        application=application,
        events=events,
        factory=lambda: runtime,
    )

    exit_code = _invoke_main(monkeypatch, module)

    assert exit_code == module.EXIT_RUNTIME_ERROR
    assert reporter.reports == []
    assert events.count("event_loop") == 1
    assert events.count("shutdown_startup_runtime") == 1


def test_startup_failure_is_reported_and_hooks_are_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_gui_module()
    events: list[str] = []
    application = _FakeApplication(events)
    reporter = _Reporter(events)
    failure = RuntimeError("simulated startup-runtime bootstrap failure")

    def failing_runtime_factory() -> _FakeStartupRuntime:
        raise failure

    _patch_process_seams(
        monkeypatch,
        module,
        application=application,
        reporter=reporter,
        events=events,
    )
    _patch_startup_runtime_builder(
        monkeypatch,
        application=application,
        events=events,
        factory=failing_runtime_factory,
    )

    exit_code = _invoke_main(monkeypatch, module)

    assert exit_code == module.EXIT_RUNTIME_ERROR
    assert reporter.reports == [failure]
    assert "event_loop" not in events
    assert "show_introduction" not in events
    assert "shutdown_startup_runtime" not in events
    assert events[-1] == "restore_hooks"
