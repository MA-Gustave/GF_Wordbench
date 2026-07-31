"""Headless integration coverage for path-resolved GUI language switching.

The production contract exercised here is intentionally toolkit-neutral.  The
GUI startup layer owns one ``LanguageRuntimeSwitcher`` that:

* resolves one explicitly selected language path;
* builds exactly one language runtime from the resolved context;
* disposes the old runtime before resolving a replacement language;
* rejects switching while a validation run is active;
* persists only successfully opened language paths;
* never preserves source, path, target, scenario, or runtime state from the
  previous language.

The expected production symbol is:

``gf_wordbench.entrypoints.gui.startup.LanguageRuntimeSwitcher``
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Protocol, TypeAlias, cast

import pytest

pytestmark = pytest.mark.gui

_STARTUP_MODULE: Final[str] = "gf_wordbench.entrypoints.gui.startup"
_SWITCHER_SYMBOL: Final[str] = "LanguageRuntimeSwitcher"


class _ResolvedContextLike(Protocol):
    selected_path: Path
    language_key: str
    language_directory: Path
    rgl_source_root: Path
    gf_search_paths: tuple[Path, ...]


class _RuntimeLike(Protocol):
    context: _ResolvedContextLike

    def shutdown(self) -> None: ...


ProbeLanguage: TypeAlias = Callable[[Path], _ResolvedContextLike]
BuildRuntime: TypeAlias = Callable[[_ResolvedContextLike], _RuntimeLike]
PersistPath: TypeAlias = Callable[[Path], None]
HasActiveRun: TypeAlias = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class _ResolvedContext:
    selected_path: Path
    language_key: str
    language_directory: Path
    rgl_source_root: Path
    gf_search_paths: tuple[Path, ...]
    focused_target: Path | None = None
    scenario_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class _FakeLanguageRuntime:
    context: _ResolvedContextLike
    events: list[str]
    shutdown_count: int = 0

    def shutdown(self) -> None:
        self.shutdown_count += 1
        self.events.append(f"shutdown:{self.context.language_key}")


@dataclass(slots=True)
class _Probe:
    contexts: dict[Path, _ResolvedContext]
    events: list[str]
    failure_path: Path | None = None
    calls: list[Path] = field(default_factory=list)

    def __call__(self, selected_path: Path) -> _ResolvedContext:
        path = selected_path.resolve(strict=False)
        self.calls.append(path)
        self.events.append(f"probe:{path.name}")
        if self.failure_path is not None and path == self.failure_path:
            raise _ProbeFailure(f"cannot resolve {path}")
        try:
            return self.contexts[path]
        except KeyError as exc:
            raise AssertionError(f"unexpected selected path: {path}") from exc


@dataclass(slots=True)
class _RuntimeFactory:
    events: list[str]
    runtimes: list[_FakeLanguageRuntime] = field(default_factory=list)
    contexts: list[_ResolvedContextLike] = field(default_factory=list)

    def __call__(self, context: _ResolvedContextLike) -> _FakeLanguageRuntime:
        self.events.append(f"build:{context.language_key}")
        self.contexts.append(context)
        runtime = _FakeLanguageRuntime(context=context, events=self.events)
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


class _ProbeFailure(RuntimeError):
    pass


def _load_switcher_type() -> type[object]:
    """Load the required production type with an actionable failure message."""

    try:
        module = importlib.import_module(_STARTUP_MODULE)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"missing {_STARTUP_MODULE}; implement the ADR-0015 GUI startup layer",
            pytrace=False,
        )
        raise AssertionError("unreachable") from exc

    switcher_type = getattr(module, _SWITCHER_SYMBOL, None)
    if not isinstance(switcher_type, type):
        pytest.fail(
            f"{_STARTUP_MODULE} must export {_SWITCHER_SYMBOL}",
            pytrace=False,
        )
    return cast(type[object], switcher_type)


def _build_switcher(
    *,
    probe_language: ProbeLanguage,
    build_runtime: BuildRuntime,
    persist_selected_path: PersistPath,
    has_active_run: HasActiveRun,
) -> object:
    switcher_type = _load_switcher_type()
    return switcher_type(
        probe_language=probe_language,
        build_runtime=build_runtime,
        persist_selected_path=persist_selected_path,
        has_active_run=has_active_run,
    )


def _call(target: object, name: str, *args: object) -> object:
    method = getattr(target, name, None)
    if not callable(method):
        pytest.fail(
            f"{_SWITCHER_SYMBOL} must expose {name}()",
            pytrace=False,
        )
    return method(*args)


def _attribute(target: object, name: str) -> object:
    if not hasattr(target, name):
        pytest.fail(
            f"{_SWITCHER_SYMBOL} must expose {name}",
            pytrace=False,
        )
    return getattr(target, name)


def _disposition(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().casefold()


def _context(
    root: Path,
    *,
    directory_name: str,
    language_key: str,
    module_suffix: str,
) -> _ResolvedContext:
    source_root = (root / "gf-rgl" / "src").resolve(strict=False)
    language_directory = (source_root / directory_name).resolve(strict=False)
    selected_path = language_directory
    focused_target = language_directory / f"Lang{module_suffix}.gf"
    shared = (
        language_directory,
        source_root / "abstract",
        source_root / "common",
        source_root / "api",
        source_root / "prelude",
    )
    return _ResolvedContext(
        selected_path=selected_path,
        language_key=language_key,
        language_directory=language_directory,
        rgl_source_root=source_root,
        gf_search_paths=tuple(path.resolve(strict=False) for path in shared),
        focused_target=focused_target.resolve(strict=False),
        scenario_ids=(f"{language_key}-smoke",),
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


def test_switching_language_disposes_the_old_runtime_before_probing_the_new_one(
    tmp_path: Path,
) -> None:
    english, french = _fixture_data(tmp_path)
    events: list[str] = []
    probe = _Probe(
        contexts={
            english.selected_path: english,
            french.selected_path: french,
        },
        events=events,
    )
    factory = _RuntimeFactory(events)
    recorder = _PathRecorder(events)
    switcher = _build_switcher(
        probe_language=probe,
        build_runtime=factory,
        persist_selected_path=recorder,
        has_active_run=lambda: False,
    )

    opened = _call(switcher, "open_language", english.selected_path)
    switched = _call(switcher, "switch_language", french.selected_path)

    assert _disposition(opened) in {"opened", "resolved", "success"}
    assert _disposition(switched) in {"switched", "opened", "resolved", "success"}
    assert len(factory.runtimes) == 2
    english_runtime, french_runtime = factory.runtimes
    assert english_runtime.shutdown_count == 1
    assert french_runtime.shutdown_count == 0

    assert events.index("shutdown:english") < events.index("probe:french")
    assert events.index("probe:french") < events.index("build:french")
    assert events.index("build:french") < events.index("persist:french")

    assert _attribute(switcher, "active_context") is french
    assert _attribute(switcher, "active_runtime") is french_runtime
    assert recorder.values == [english.selected_path, french.selected_path]


def test_switching_does_not_carry_paths_targets_or_scenarios_between_languages(
    tmp_path: Path,
) -> None:
    english, french = _fixture_data(tmp_path)
    events: list[str] = []
    probe = _Probe(
        contexts={
            english.selected_path: english,
            french.selected_path: french,
        },
        events=events,
    )
    factory = _RuntimeFactory(events)
    switcher = _build_switcher(
        probe_language=probe,
        build_runtime=factory,
        persist_selected_path=_PathRecorder(events),
        has_active_run=lambda: False,
    )

    _call(switcher, "open_language", english.selected_path)
    _call(switcher, "switch_language", french.selected_path)

    assert factory.contexts == [english, french]
    french_context = cast(_ResolvedContext, factory.contexts[-1])
    english_directory = str(english.language_directory).casefold()

    assert french_context.language_key == "french"
    assert french_context.language_directory == french.language_directory
    assert french_context.focused_target == french.focused_target
    assert french_context.scenario_ids == ("french-smoke",)
    assert english.language_directory not in french_context.gf_search_paths
    assert all(
        english_directory not in str(path).casefold()
        for path in french_context.gf_search_paths
    )
    assert all("english" not in scenario for scenario in french_context.scenario_ids)


def test_switch_is_rejected_while_a_run_is_active_and_keeps_current_runtime(
    tmp_path: Path,
) -> None:
    english, french = _fixture_data(tmp_path)
    events: list[str] = []
    run_active = False

    def has_active_run() -> bool:
        return run_active

    probe = _Probe(
        contexts={
            english.selected_path: english,
            french.selected_path: french,
        },
        events=events,
    )
    factory = _RuntimeFactory(events)
    recorder = _PathRecorder(events)
    switcher = _build_switcher(
        probe_language=probe,
        build_runtime=factory,
        persist_selected_path=recorder,
        has_active_run=has_active_run,
    )

    _call(switcher, "open_language", english.selected_path)
    run_active = True
    result = _call(switcher, "switch_language", french.selected_path)

    assert _disposition(result) in {"busy", "rejected", "run-active", "run_active"}
    assert probe.calls == [english.selected_path]
    assert len(factory.runtimes) == 1
    assert factory.runtimes[0].shutdown_count == 0
    assert _attribute(switcher, "active_context") is english
    assert _attribute(switcher, "active_runtime") is factory.runtimes[0]
    assert recorder.values == [english.selected_path]
    assert "probe:french" not in events
    assert "build:french" not in events


def test_failed_replacement_resolution_does_not_restore_the_disposed_language(
    tmp_path: Path,
) -> None:
    english, french = _fixture_data(tmp_path)
    events: list[str] = []
    probe = _Probe(
        contexts={english.selected_path: english},
        events=events,
        failure_path=french.selected_path,
    )
    factory = _RuntimeFactory(events)
    recorder = _PathRecorder(events)
    switcher = _build_switcher(
        probe_language=probe,
        build_runtime=factory,
        persist_selected_path=recorder,
        has_active_run=lambda: False,
    )

    _call(switcher, "open_language", english.selected_path)

    with pytest.raises(_ProbeFailure, match="cannot resolve"):
        _call(switcher, "switch_language", french.selected_path)

    assert factory.runtimes[0].shutdown_count == 1
    assert events.index("shutdown:english") < events.index("probe:french")
    assert _attribute(switcher, "active_context") is None
    assert _attribute(switcher, "active_runtime") is None
    assert recorder.values == [english.selected_path]
    assert len(factory.runtimes) == 1


def test_shutdown_disposes_only_the_current_runtime_and_is_idempotent(
    tmp_path: Path,
) -> None:
    english, _french = _fixture_data(tmp_path)
    events: list[str] = []
    probe = _Probe(contexts={english.selected_path: english}, events=events)
    factory = _RuntimeFactory(events)
    switcher = _build_switcher(
        probe_language=probe,
        build_runtime=factory,
        persist_selected_path=_PathRecorder(events),
        has_active_run=lambda: False,
    )

    _call(switcher, "open_language", english.selected_path)
    runtime = factory.runtimes[0]

    _call(switcher, "shutdown")
    _call(switcher, "shutdown")

    assert runtime.shutdown_count == 1
    assert _attribute(switcher, "active_context") is None
    assert _attribute(switcher, "active_runtime") is None
