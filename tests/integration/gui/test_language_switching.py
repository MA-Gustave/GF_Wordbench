"""Headless integration coverage for path-resolved GUI language switching.

The tests exercise the public startup runtime rather than requiring a second,
parallel ``LanguageRuntimeSwitcher`` abstraction.

Canonical behavior:

* startup is inert until ``start()`` and never probes automatically;
* opening the remembered language still requires an explicit user action;
* a successful resolution builds one runtime and only then persists its path;
* switching is rejected while a validation run is active;
* an accepted switch disposes the old runtime before returning to introduction;
* the replacement language is resolved from a new explicit selection;
* failed replacement never restores the disposed runtime;
* no paths, targets, scenarios, or runtime state leak between languages;
* shutdown is idempotent.

English and French are integration fixtures, not startup defaults.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import importlib
from pathlib import Path
from types import ModuleType
from typing import Final, Protocol, cast

import pytest

from gf_wordbench.projects.languages.models import (
    CapabilityAvailability,
    LanguageCapability,
    LanguageCapabilityStatus,
    ResolvedLanguageContext,
    SelectedPathKind,
)

pytestmark = pytest.mark.gui

_STARTUP_MODULE: Final[str] = "gf_wordbench.entrypoints.gui.startup"


class _ResolvedContextLike(Protocol):
    selected_path: Path
    language_key: str
    language_directory: Path
    rgl_source_root: Path
    gf_path_requirements: tuple[Path, ...]


class _StartupRuntimeLike(Protocol):
    def start(self) -> None: ...

    def shutdown(self) -> None: ...


_ResolvedContext = ResolvedLanguageContext


@dataclass(slots=True)
class _Signal:
    callbacks: list[Callable[..., None]] = field(default_factory=list)

    def connect(self, callback: Callable[..., None]) -> None:
        self.callbacks.append(callback)

    def disconnect(self) -> None:
        self.callbacks.clear()

    def emit(self, *args: object) -> None:
        for callback in tuple(self.callbacks):
            callback(*args)


@dataclass(slots=True)
class _DialogRecorder:
    events: list[str]

    def information(self, title: str, message: str, **_kwargs: object) -> None:
        self.events.append(f"information:{title}:{message}")

    def warning(self, title: str, message: str, **_kwargs: object) -> None:
        self.events.append(f"warning:{title}:{message}")


class _FakeIntroductionWindow:
    """Toolkit-neutral replacement for ``IntroductionWindow``."""

    def __init__(self, *, events: list[str]) -> None:
        self.events = events
        self.open_last_requested = _Signal()
        self.choose_directory_requested = _Signal()
        self.choose_file_requested = _Signal()
        self.configure_environment_requested = _Signal()
        self.candidate_requested = _Signal()
        self.quit_requested = _Signal()
        self.dialog_service = _DialogRecorder(events)

        self.next_directory: Path | None = None
        self.next_file: Path | None = None
        self.next_rgl_root: Path | None = None
        self._rgl_root: Path | None = None
        self.visible = False
        self.closed = False
        self.close_allowed = False
        self.snapshots: list[object] = []
        self.probe_results: list[object] = []
        self.exceptions: list[object] = []

    def choose_language_directory(self) -> Path | None:
        self.events.append("choose_directory")
        return self.next_directory

    def choose_gf_file(self) -> Path | None:
        self.events.append("choose_file")
        return self.next_file

    @property
    def rgl_root(self) -> Path | None:
        return self._rgl_root

    def choose_rgl_root(self) -> Path | None:
        self.events.append("choose_rgl_root")
        return self.next_rgl_root

    def set_rgl_root(self, path: Path | None) -> None:
        self._rgl_root = path
        self.events.append(f"set_rgl_root:{path}")

    def show_snapshot(self, snapshot: object) -> None:
        self.snapshots.append(snapshot)

    def show_probe_result(self, result: object) -> None:
        self.probe_results.append(result)

    def show_exception(self, presentation: object) -> None:
        self.exceptions.append(presentation)

    def show(self) -> None:
        self.visible = True
        self.events.append("show:introduction")

    def hide(self) -> None:
        self.visible = False
        self.events.append("hide:introduction")

    def raise_(self) -> None:
        self.events.append("raise:introduction")

    def activateWindow(self) -> None:
        self.events.append("activate:introduction")

    def allow_close(self) -> None:
        self.close_allowed = True

    def close(self) -> None:
        self.closed = True
        self.visible = False
        self.events.append("close:introduction")


class _ImmediateProbeThread:
    """Synchronous test seam for the production probe-thread boundary."""

    def __init__(
        self,
        request: object,
        probe: Callable[[object], object],
        *,
        parent: object | None = None,
    ) -> None:
        del parent
        self._request = request
        self._probe = probe
        self._running = False
        self._interrupted = False
        self.result_ready = _Signal()
        self.probe_failed = _Signal()
        self.finished = _Signal()

    def start(self) -> None:
        self._running = True
        try:
            if self._interrupted:
                return
            result = self._probe(self._request)
        except Exception as exc:
            if not self._interrupted:
                self.probe_failed.emit(exc)
        else:
            if not self._interrupted:
                self.result_ready.emit(result)
        finally:
            self._running = False
            self.finished.emit()

    def isRunning(self) -> bool:
        return self._running

    def requestInterruption(self) -> None:
        self._interrupted = True

    def isInterruptionRequested(self) -> bool:
        return self._interrupted

    def wait(self, _timeout_ms: int) -> bool:
        return True

    def deleteLater(self) -> None:
        return None


@dataclass(slots=True)
class _FakeMainWindow:
    language_key: str
    events: list[str]
    language_switch_requested: _Signal = field(default_factory=_Signal)
    visible: bool = False

    def show(self) -> None:
        self.visible = True
        self.events.append(f"show:{self.language_key}")

    def hide(self) -> None:
        self.visible = False
        self.events.append(f"hide:{self.language_key}")

    def raise_(self) -> None:
        self.events.append(f"raise:{self.language_key}")

    def activateWindow(self) -> None:
        self.events.append(f"activate:{self.language_key}")


@dataclass(slots=True)
class _FakeMainRuntime:
    context: _ResolvedContext
    events: list[str]
    window: _FakeMainWindow = field(init=False)
    shutdown_count: int = 0

    def __post_init__(self) -> None:
        self.window = _FakeMainWindow(self.context.language_key, self.events)

    def shutdown(self) -> None:
        self.shutdown_count += 1
        self.events.append(f"shutdown:{self.context.language_key}")


@dataclass(slots=True)
class _Probe:
    module: ModuleType
    contexts: dict[Path, _ResolvedContext]
    events: list[str]
    failure_path: Path | None = None
    calls: list[Path] = field(default_factory=list)

    def __call__(self, request: object) -> object:
        selected_path = getattr(request, "selected_path", None)
        if not isinstance(selected_path, Path):
            raise TypeError("probe request must expose selected_path: Path")

        path = selected_path.resolve(strict=False)
        self.calls.append(path)
        self.events.append(f"probe:{path.name}")

        if self.failure_path is not None and path == self.failure_path:
            raise _ProbeFailure(f"cannot resolve {path}")

        try:
            context = self.contexts[path]
        except KeyError as exc:
            raise AssertionError(f"unexpected selected path: {path}") from exc

        presentation = self.module.ResolvedLanguagePresentation(
            language_key=context.language_key,
            language_directory=context.language_directory,
            rgl_source_root=context.rgl_source_root,
            selected_path=context.selected_path,
            selected_path_kind="directory",
            focused_target=context.focused_target,
            source_count=1,
        )
        return self.module.LanguageProbeResult(
            disposition=self.module.LanguageProbeDisposition.RESOLVED,
            context=context,
            presentation=presentation,
        )


@dataclass(slots=True)
class _RuntimeFactory:
    events: list[str]
    failure_language_key: str | None = None
    runtimes: list[_FakeMainRuntime] = field(default_factory=list)
    contexts: list[_ResolvedContext] = field(default_factory=list)

    def __call__(
        self,
        application: object,
        context: _ResolvedContextLike,
    ) -> _FakeMainRuntime:
        del application
        if not isinstance(context, _ResolvedContext):
            raise TypeError("test runtime factory requires _ResolvedContext")
        self.events.append(f"build:{context.language_key}")
        self.contexts.append(context)
        if context.language_key == self.failure_language_key:
            raise _RuntimeBuildFailure(f"cannot build {context.language_key}")
        runtime = _FakeMainRuntime(context=context, events=self.events)
        self.runtimes.append(runtime)
        return runtime


@dataclass(slots=True)
class _PathRecorder:
    events: list[str]
    values: list[Path] = field(default_factory=list)

    def __call__(self, selected_path: Path) -> None:
        normalized = selected_path.resolve(strict=False)
        self.values.append(normalized)
        self.events.append(f"persist:{normalized.name}")


@dataclass(slots=True)
class _FakeApplication:
    events: list[str]

    def quit(self) -> None:
        self.events.append("quit")


class _ProbeFailure(RuntimeError):
    pass


class _RuntimeBuildFailure(RuntimeError):
    pass


def _load_startup_module() -> ModuleType:
    try:
        return importlib.import_module(_STARTUP_MODULE)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"missing {_STARTUP_MODULE}; implement the ADR-0015 GUI startup layer",
            pytrace=False,
        )
        raise AssertionError("unreachable") from exc


def _context(
    root: Path,
    *,
    directory_name: str,
    language_key: str,
    module_suffix: str,
) -> _ResolvedContext:
    source_root = (root / "gf-rgl" / "src").resolve(strict=False)
    rgl_root = source_root.parent.resolve(strict=False)
    language_directory = (source_root / directory_name).resolve(strict=False)
    focused_target = (language_directory / f"Lang{module_suffix}.gf").resolve(strict=False)
    shared = (
        language_directory,
        source_root / "abstract",
        source_root / "common",
        source_root / "api",
        source_root / "prelude",
    )
    return _ResolvedContext(
        selected_path=language_directory,
        selected_path_kind=SelectedPathKind.DIRECTORY,
        language_key=language_key,
        language_directory=language_directory,
        rgl_source_root=source_root,
        rgl_root=rgl_root,
        focused_target=None,
        module_suffix=module_suffix,
        available_entrypoints=(focused_target,),
        source_inventory=(focused_target,),
        gf_path_requirements=tuple(path.resolve(strict=False) for path in shared),
        capability_statuses=(
            LanguageCapabilityStatus(
                capability=LanguageCapability.SOURCE_READY,
                availability=CapabilityAvailability.AVAILABLE,
            ),
        ),
    )


def _fixture_data(
    tmp_path: Path,
) -> tuple[_ResolvedContext, _ResolvedContext]:
    english = _context(
        tmp_path,
        directory_name="english",
        language_key="english",
        module_suffix="Eng",
    )
    french = _context(
        tmp_path,
        directory_name="french",
        language_key="french",
        module_suffix="Fre",
    )
    return english, french


def _patch_headless_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
) -> None:
    monkeypatch.setattr(
        module,
        "IntroductionWindow",
        _FakeIntroductionWindow,
        raising=True,
    )
    monkeypatch.setattr(
        module,
        "_ProbeThread",
        _ImmediateProbeThread,
        raising=True,
    )


def _build_services(
    module: ModuleType,
    *,
    probe_language: Callable[[object], object],
    build_main_runtime: Callable[[object, _ResolvedContextLike], object],
    load_last_selected_path: Callable[[], Path | None],
    remember_selected_path: Callable[[Path], None],
    has_active_run: Callable[[], bool],
) -> object:
    try:
        return module.StartupServices(
            probe_language=probe_language,
            build_main_runtime=build_main_runtime,
            load_last_selected_path=load_last_selected_path,
            remember_selected_path=remember_selected_path,
            has_active_run=has_active_run,
        )
    except TypeError as exc:
        if "has_active_run" in str(exc):
            pytest.fail(
                "StartupServices must expose has_active_run so language switching "
                "can be rejected during an active validation run",
                pytrace=False,
            )
        raise


def _build_runtime(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tmp_path: Path,
    run_active: Callable[[], bool] = lambda: False,
    failure_path: Path | None = None,
    failure_language_key: str | None = None,
) -> tuple[
    ModuleType,
    _StartupRuntimeLike,
    _FakeIntroductionWindow,
    _Probe,
    _RuntimeFactory,
    _PathRecorder,
    _ResolvedContext,
    _ResolvedContext,
    list[str],
]:
    module = _load_startup_module()
    _patch_headless_boundaries(monkeypatch, module)

    english, french = _fixture_data(tmp_path)
    events: list[str] = []
    probe = _Probe(
        module=module,
        contexts={
            english.selected_path: english,
            french.selected_path: french,
        },
        events=events,
        failure_path=failure_path,
    )
    factory = _RuntimeFactory(
        events=events,
        failure_language_key=failure_language_key,
    )
    recorder = _PathRecorder(events)
    window = _FakeIntroductionWindow(events=events)
    application = _FakeApplication(events)
    services = _build_services(
        module,
        probe_language=probe,
        build_main_runtime=factory,
        load_last_selected_path=lambda: english.selected_path,
        remember_selected_path=recorder,
        has_active_run=run_active,
    )
    runtime = cast(
        _StartupRuntimeLike,
        module.build_startup_runtime(
            application,
            (),
            services=services,
            window=window,
        ),
    )
    return (
        module,
        runtime,
        window,
        probe,
        factory,
        recorder,
        english,
        french,
        events,
    )


def _open_remembered_language(
    runtime: _StartupRuntimeLike,
    window: _FakeIntroductionWindow,
) -> None:
    runtime.start()
    window.open_last_requested.emit()


def _request_switch(factory: _RuntimeFactory) -> None:
    assert factory.runtimes
    factory.runtimes[-1].window.language_switch_requested.emit()


def _choose_directory(
    window: _FakeIntroductionWindow,
    selected_path: Path,
) -> None:
    window.next_directory = selected_path
    window.choose_directory_requested.emit()


def test_external_project_prompts_for_rgl_dependency_and_retries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_startup_module()
    _patch_headless_boundaries(monkeypatch, module)

    events: list[str] = []
    external_language = (tmp_path / "external-project" / "albanian").resolve(strict=False)
    rgl_root = (tmp_path / "gf-rgl").resolve(strict=False)
    source_root = (rgl_root / "src").resolve(strict=False)
    lang_file = (external_language / "LangSqi.gf").resolve(strict=False)
    context = _ResolvedContext(
        selected_path=external_language,
        selected_path_kind=SelectedPathKind.DIRECTORY,
        language_key="albanian",
        language_directory=external_language,
        rgl_source_root=source_root,
        rgl_root=rgl_root,
        focused_target=None,
        module_suffix="Sqi",
        available_entrypoints=(lang_file,),
        source_inventory=(lang_file,),
        gf_path_requirements=(
            external_language,
            external_language.parent,
            source_root / "abstract",
            source_root / "common",
            source_root / "api",
            source_root / "prelude",
        ),
        capability_statuses=(
            LanguageCapabilityStatus(
                capability=LanguageCapability.SOURCE_READY,
                availability=CapabilityAvailability.AVAILABLE,
            ),
        ),
    )

    calls: list[Path | None] = []

    def probe(request: object) -> object:
        explicit = getattr(request, "explicit_rgl_root", None)
        calls.append(explicit)
        if explicit is None:
            diagnostic = module.LanguageProbeDiagnostic(
                code="GF-WB-PATH-253",
                severity=module.LanguageProbeSeverity.ERROR,
                stage="language_probe",
                subject=str(external_language),
                message="A supported RGL source root could not be derived from the selected path.",
                remediation="Provide an explicit RGL root.",
                relevant_path=external_language,
            )
            return module.LanguageProbeResult(
                status=module.LanguageProbeDisposition.UNSUPPORTED_LAYOUT,
                diagnostics=(diagnostic,),
            )

        presentation = module.ResolvedLanguagePresentation(
            language_key=context.language_key,
            language_directory=context.language_directory,
            rgl_source_root=context.rgl_source_root,
            selected_path=context.selected_path,
            selected_path_kind="directory",
            focused_target=context.focused_target,
            source_count=1,
        )
        return module.LanguageProbeResult(
            status=module.LanguageProbeDisposition.RESOLVED,
            context=context,
            presentation=presentation,
        )

    factory = _RuntimeFactory(events=events)
    recorder = _PathRecorder(events)
    window = _FakeIntroductionWindow(events=events)
    window.next_rgl_root = rgl_root
    services = _build_services(
        module,
        probe_language=probe,
        build_main_runtime=factory,
        load_last_selected_path=lambda: None,
        remember_selected_path=recorder,
        has_active_run=lambda: False,
    )
    runtime = cast(
        _StartupRuntimeLike,
        module.build_startup_runtime(
            _FakeApplication(events),
            (),
            services=services,
            window=window,
        ),
    )

    runtime.start()
    _choose_directory(window, external_language)

    assert calls == [None, rgl_root]
    assert window.rgl_root == rgl_root
    assert "choose_rgl_root" in events
    assert factory.contexts == [context]
    assert window.exceptions == []


def test_startup_and_construction_do_not_probe_or_build_automatically(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        _window,
        probe,
        factory,
        recorder,
        _english,
        _french,
        events,
    ) = _build_runtime(monkeypatch, tmp_path=tmp_path)

    assert probe.calls == []
    assert factory.contexts == []
    assert recorder.values == []
    assert events == []

    start = runtime.start
    start()

    assert probe.calls == []
    assert factory.contexts == []
    assert recorder.values == []
    assert events == []


def test_explicit_open_probes_builds_then_persists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        probe,
        factory,
        recorder,
        english,
        _french,
        events,
    ) = _build_runtime(monkeypatch, tmp_path=tmp_path)

    _open_remembered_language(runtime, window)

    assert events[:3] == [
        "probe:english",
        "build:english",
        "persist:english",
    ]
    assert probe.calls == [english.selected_path]
    assert factory.contexts == [english]
    assert recorder.values == [english.selected_path]
    assert len(factory.runtimes) == 1
    assert factory.runtimes[0].window.visible is True
    assert window.visible is False


def test_switch_disposes_old_runtime_before_resolving_explicit_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        probe,
        factory,
        recorder,
        english,
        french,
        events,
    ) = _build_runtime(monkeypatch, tmp_path=tmp_path)

    _open_remembered_language(runtime, window)
    english_runtime = factory.runtimes[0]

    _request_switch(factory)

    assert english_runtime.shutdown_count == 1
    assert window.visible is True
    assert probe.calls == [english.selected_path]
    assert len(factory.runtimes) == 1

    _choose_directory(window, french.selected_path)

    assert len(factory.runtimes) == 2
    french_runtime = factory.runtimes[1]
    assert french_runtime.shutdown_count == 0
    assert events.index("shutdown:english") < events.index("probe:french")
    assert events.index("probe:french") < events.index("build:french")
    assert events.index("build:french") < events.index("persist:french")
    assert recorder.values == [english.selected_path, french.selected_path]


def test_switch_does_not_carry_language_state_between_runtimes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        _probe,
        factory,
        _recorder,
        english,
        french,
        _events,
    ) = _build_runtime(monkeypatch, tmp_path=tmp_path)

    _open_remembered_language(runtime, window)
    _request_switch(factory)
    _choose_directory(window, french.selected_path)

    assert factory.contexts == [english, french]
    french_context = factory.contexts[-1]
    english_directory = str(english.language_directory).casefold()

    assert french_context.language_key == "french"
    assert french_context.language_directory == french.language_directory
    assert french_context.focused_target is None
    assert french_context.entrypoint_paths == french.entrypoint_paths
    assert english.language_directory not in french_context.gf_path_requirements
    assert all(
        english_directory not in str(path).casefold()
        for path in french_context.gf_path_requirements
    )
    assert all(
        english_directory not in str(path).casefold()
        for path in french_context.source_inventory
    )


def test_switch_is_rejected_while_a_run_is_active(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_active = False

    def has_active_run() -> bool:
        return run_active

    (
        _module,
        runtime,
        window,
        probe,
        factory,
        recorder,
        english,
        _french,
        events,
    ) = _build_runtime(
        monkeypatch,
        tmp_path=tmp_path,
        run_active=has_active_run,
    )

    _open_remembered_language(runtime, window)
    active_runtime = factory.runtimes[0]
    run_active = True

    _request_switch(factory)

    assert active_runtime.shutdown_count == 0
    assert active_runtime.window.visible is True
    assert window.visible is False
    assert probe.calls == [english.selected_path]
    assert recorder.values == [english.selected_path]
    assert "shutdown:english" not in events
    assert len(factory.runtimes) == 1


def test_failed_initial_resolution_does_not_build_persist_or_activate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    english, _french = _fixture_data(tmp_path)
    (
        _module,
        runtime,
        window,
        probe,
        factory,
        recorder,
        _english,
        _french,
        events,
    ) = _build_runtime(
        monkeypatch,
        tmp_path=tmp_path,
        failure_path=english.selected_path,
    )

    _open_remembered_language(runtime, window)

    assert events == ["probe:english"]
    assert probe.calls == [english.selected_path]
    assert factory.contexts == []
    assert factory.runtimes == []
    assert recorder.values == []
    assert window.exceptions


def test_failed_initial_runtime_build_does_not_persist_or_activate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        _probe,
        factory,
        recorder,
        _english,
        _french,
        events,
    ) = _build_runtime(
        monkeypatch,
        tmp_path=tmp_path,
        failure_language_key="english",
    )

    _open_remembered_language(runtime, window)

    assert events == ["probe:english", "build:english"]
    assert factory.runtimes == []
    assert recorder.values == []
    assert window.exceptions


def test_failed_replacement_does_not_restore_disposed_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _english, french = _fixture_data(tmp_path)
    (
        _module,
        runtime,
        window,
        _probe,
        factory,
        recorder,
        english,
        _french,
        events,
    ) = _build_runtime(
        monkeypatch,
        tmp_path=tmp_path,
        failure_path=french.selected_path,
    )

    _open_remembered_language(runtime, window)
    english_runtime = factory.runtimes[0]
    _request_switch(factory)
    _choose_directory(window, french.selected_path)

    assert english_runtime.shutdown_count == 1
    assert english_runtime.window.visible is False
    assert len(factory.runtimes) == 1
    assert recorder.values == [english.selected_path]
    assert events.index("shutdown:english") < events.index("probe:french")
    assert window.visible is True
    assert window.exceptions


def test_failed_replacement_build_does_not_restore_or_persist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        _probe,
        factory,
        recorder,
        english,
        french,
        events,
    ) = _build_runtime(
        monkeypatch,
        tmp_path=tmp_path,
        failure_language_key="french",
    )

    _open_remembered_language(runtime, window)
    english_runtime = factory.runtimes[0]
    _request_switch(factory)
    _choose_directory(window, french.selected_path)

    assert english_runtime.shutdown_count == 1
    assert len(factory.runtimes) == 1
    assert recorder.values == [english.selected_path]
    assert events.index("shutdown:english") < events.index("probe:french")
    assert events.index("probe:french") < events.index("build:french")
    assert "persist:french" not in events
    assert window.visible is True
    assert window.exceptions


def test_shutdown_disposes_only_current_runtime_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        _module,
        runtime,
        window,
        _probe,
        factory,
        _recorder,
        _english,
        _french,
        _events,
    ) = _build_runtime(monkeypatch, tmp_path=tmp_path)

    _open_remembered_language(runtime, window)
    active_runtime = factory.runtimes[0]

    shutdown = runtime.shutdown
    assert shutdown() is None
    assert shutdown() is None

    assert active_runtime.shutdown_count == 1
    assert window.closed is True


def test_default_startup_services_use_standard_workspace_defaults_and_remember_overrides(
    tmp_path: Path,
) -> None:
    module = _load_startup_module()

    suite_root = (tmp_path / "Grammatical_Framework").resolve(strict=False)
    workspace_root = suite_root / "GF_Wordbench" / "GF_Wordbench"
    workspace_root.mkdir(parents=True)

    default_language = (
        suite_root
        / "Grammatical_Framework-Albanian"
        / "AlbanianSQI"
        / "GF"
        / "lib"
        / "src"
        / "albanian"
    )
    default_language.mkdir(parents=True)
    (default_language / "LangSqi.gf").write_text("-- default Albanian\n", encoding="utf-8")

    default_rgl = suite_root / "gf-rgl"
    (default_rgl / "src").mkdir(parents=True)

    services = module._build_default_startup_services(workspace_root=workspace_root)

    assert services.load_last_selected_path() == default_language.resolve(strict=False)
    assert services.load_rgl_root is not None
    assert services.load_rgl_root() == default_rgl.resolve(strict=False)

    remembered_language = suite_root / "external" / "lib" / "src" / "albanian"
    remembered_language.mkdir(parents=True)
    (remembered_language / "GrammarSqi.gf").write_text("-- remembered\n", encoding="utf-8")
    remembered_rgl = suite_root / "alternate-rgl"
    (remembered_rgl / "src").mkdir(parents=True)

    assert services.remember_selected_path is not None
    assert services.remember_rgl_root is not None
    services.remember_selected_path(remembered_language)
    services.remember_rgl_root(remembered_rgl)

    reloaded = module._build_default_startup_services(workspace_root=workspace_root)
    assert reloaded.load_last_selected_path() == remembered_language.resolve(strict=False)
    assert reloaded.load_rgl_root is not None
    assert reloaded.load_rgl_root() == remembered_rgl.resolve(strict=False)
