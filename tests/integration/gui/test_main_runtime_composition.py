"""Integration coverage for the path-resolved main GUI runtime."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from gf_wordbench.entrypoints.gui.panels.validation import ValidationPanelValues
from gf_wordbench.entrypoints.gui.runtime import (
    PathResolvedMainGuiRuntime,
    _workspace_default_gf_executable,
    build_main_runtime,
)
from gf_wordbench.entrypoints.gui.window import WindowRunState
from gf_wordbench.entrypoints.gui.workers import create_run_worker
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from tests.helpers.builders import make_run_config, make_run_result
from gf_wordbench.projects.languages.models import (
    CapabilityAvailability,
    LanguageCapability,
    LanguageCapabilityStatus,
    LanguageModuleCandidate,
    LanguageModuleRole,
    ResolvedLanguageContext,
    SelectedPathKind,
)

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapplication() -> Iterator[QApplication]:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        yield existing
        return

    application = QApplication([])
    yield application
    application.processEvents()
    application.quit()


def _external_context(tmp_path: Path) -> ResolvedLanguageContext:
    language_directory = tmp_path / "external" / "GF" / "lib" / "src" / "albanian"
    language_directory.mkdir(parents=True)
    rgl_root = tmp_path / "gf-rgl"
    rgl_source_root = rgl_root / "src"
    (rgl_source_root / "abstract").mkdir(parents=True)
    (rgl_source_root / "common").mkdir()
    (rgl_source_root / "prelude").mkdir()

    grammar = language_directory / "GrammarSqi.gf"
    lang = language_directory / "LangSqi.gf"
    noun = language_directory / "NounSqi.gf"
    for source in (grammar, lang, noun):
        source.write_text(f"-- {source.name}\n", encoding="utf-8")

    return ResolvedLanguageContext(
        language_key="albanian",
        selected_path=language_directory,
        selected_path_kind=SelectedPathKind.DIRECTORY,
        language_directory=language_directory,
        rgl_source_root=rgl_source_root,
        rgl_root=rgl_root,
        focused_target=None,
        module_suffix="Sqi",
        available_entrypoints=(
            LanguageModuleCandidate(grammar, LanguageModuleRole.GRAMMAR, "Sqi"),
            LanguageModuleCandidate(lang, LanguageModuleRole.LANG, "Sqi"),
        ),
        source_inventory=(grammar, lang, noun),
        gf_path_requirements=(
            language_directory,
            language_directory.parent,
            rgl_source_root / "abstract",
            rgl_source_root / "common",
            rgl_source_root / "prelude",
        ),
        capability_statuses=(
            LanguageCapabilityStatus(
                LanguageCapability.SOURCE_READY,
                CapabilityAvailability.AVAILABLE,
            ),
            LanguageCapabilityStatus(
                LanguageCapability.SCAN_READY,
                CapabilityAvailability.AVAILABLE,
            ),
        ),
    )


def test_external_language_context_composes_source_ready_main_window(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    context = _external_context(tmp_path)

    runtime = build_main_runtime(qapplication, context)

    assert isinstance(runtime, PathResolvedMainGuiRuntime)
    assert runtime.context is context
    assert runtime.window.panels.project.language_ready is True
    assert runtime.window.panels.project.language_directory == context.language_directory
    assert runtime.window.panels.project.selected_path == context.selected_path
    assert "albanian" in runtime.window.windowTitle().casefold()
    assert runtime.window.run_button.isEnabled() is False

    validation = runtime.window.panels.validation
    assert validation.mode() is ValidationMode.QUICK
    assert tuple(choice.identifier for choice in validation.catalog.targets) == (
        "GrammarSqi.gf",
        "LangSqi.gf",
        "NounSqi.gf",
    )
    assert validation.values().target_file is None

    runtime.shutdown()
    assert runtime.closed is True
    runtime.shutdown()



def test_quick_target_selection_enables_run_action(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    runtime = build_main_runtime(qapplication, _external_context(tmp_path))
    validation = runtime.window.panels.validation

    validation.set_values(
        ValidationPanelValues(
            mode=ValidationMode.QUICK,
            target_file="GrammarSqi.gf",
        )
    )
    qapplication.processEvents()

    assert validation.values().target_file == "GrammarSqi.gf"
    assert runtime.window.run_button.isEnabled() is True
    runtime.shutdown()


def test_diagnostic_empty_target_enables_global_scan_action(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    runtime = build_main_runtime(qapplication, _external_context(tmp_path))
    validation = runtime.window.panels.validation

    validation.set_values(
        ValidationPanelValues(
            mode=ValidationMode.DIAGNOSTIC,
            target_file=None,
            max_files=None,
        )
    )
    qapplication.processEvents()

    assert validation.values().target_file is None
    assert "Global Scan" in validation.target_label.text()
    assert runtime.window.run_button.text() == "Run Global Scan"
    assert runtime.window.run_button.isEnabled() is True
    runtime.shutdown()


def test_focused_file_is_preserved_as_quick_target(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    directory_context = _external_context(tmp_path)
    focused = directory_context.language_directory / "NounSqi.gf"
    context = ResolvedLanguageContext(
        language_key=directory_context.language_key,
        selected_path=focused,
        selected_path_kind=SelectedPathKind.FILE,
        language_directory=directory_context.language_directory,
        rgl_source_root=directory_context.rgl_source_root,
        rgl_root=directory_context.rgl_root,
        focused_target=focused,
        module_suffix=directory_context.module_suffix,
        available_entrypoints=directory_context.available_entrypoints,
        source_inventory=directory_context.source_inventory,
        gf_path_requirements=directory_context.gf_path_requirements,
        capability_statuses=directory_context.capability_statuses,
    )

    runtime = build_main_runtime(qapplication, context)

    assert runtime.window.panels.validation.values().target_file == "NounSqi.gf"
    runtime.shutdown()


def test_main_window_language_change_intents_use_startup_switch_signal(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    runtime = build_main_runtime(qapplication, _external_context(tmp_path))
    emitted: list[str] = []
    runtime.window.language_switch_requested.connect(lambda: emitted.append("switch"))

    runtime.window.open_project_action.trigger()

    assert emitted == ["switch"]
    runtime.shutdown()


def test_main_window_uses_compact_vertical_workspace(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    runtime = build_main_runtime(qapplication, _external_context(tmp_path))
    window = runtime.window

    details = window.panels.project.findChild(QWidget, "languageContextDetailsFrame")
    activity = window.panels.progress.findChild(QWidget, "progressActivityGroup")
    assert details is not None
    assert activity is not None
    assert details.isHidden() is True
    assert activity.isHidden() is True

    # Results are the useful idle default.  During a run the lower workspace
    # automatically becomes the Progress tab and returns to Results at finish.
    assert window._results_tabs.currentWidget() is window.panels.results
    window.set_run_state(WindowRunState.RUNNING)
    assert window._results_tabs.currentWidget() is window.panels.progress
    window.notify_run_finished()
    assert window._results_tabs.currentWidget() is window.panels.results

    runtime.shutdown()


def test_workspace_default_gf_executable_is_derived_from_repository_location(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "GF_Wordbench" / "GF_Wordbench"
    repository_root.mkdir(parents=True)
    executable = tmp_path / "gf-3.12-windows" / "gf.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"GF placeholder")

    resolved = _workspace_default_gf_executable(repository_root=repository_root)

    assert resolved == executable.resolve()


def test_workspace_default_gf_executable_is_optional_when_missing(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "GF_Wordbench" / "GF_Wordbench"
    repository_root.mkdir(parents=True)

    assert _workspace_default_gf_executable(repository_root=repository_root) is None


def test_results_panel_renders_path_resolved_run_without_validation_profile(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    context = _external_context(tmp_path)
    runtime = build_main_runtime(qapplication, context)
    run_dir = tmp_path / "runs" / "run_20260917_154815"
    run_dir.mkdir(parents=True)

    result = SimpleNamespace(
        run_config=SimpleNamespace(
            project=None,
            validation_profile=None,
            language_context=context,
            mode=ValidationMode.QUICK,
            compatibility_warnings=(),
        ),
        run_paths=SimpleNamespace(
            run_id="20260917_154815",
            run_dir=run_dir,
        ),
        duration_ms=250,
        gf_version="3.12",
        overall_status=OverallStatus.OK,
        file_results=[],
        scenario_results=[],
        diff_entries=[],
        top_errors=[],
        totals=SimpleNamespace(
            files_ok=0,
            files_fail=0,
            files_error=0,
            files_skipped=0,
            scenarios_ok=0,
            scenarios_fail=0,
            scenarios_error=0,
            scenarios_skipped=0,
            direct_fail=0,
            downstream_fail=0,
            ambiguous_fail=0,
            required_scenario_fail=0,
        ),
    )

    runtime.window.panels.results.set_result(result)

    assert runtime.window.panels.results._summary_labels["project"].text() == "albanian (Sqi)"
    assert runtime.window.panels.results._summary_labels["gf_version"].text() == "3.12"
    runtime.shutdown()


def test_run_worker_terminal_signal_is_reemitted_on_gui_thread(
    tmp_path: Path,
    qapplication: QApplication,
) -> None:
    config = make_run_config(
        project_root=tmp_path / "project",
        output_root=tmp_path / "runs",
    )
    result = make_run_result(run_config=config)
    loop = QEventLoop()
    callback_threads: list[QThread] = []
    failures: list[object] = []

    def execute(_config, _event_sink, _cancellation_check):
        return result

    handle = create_run_worker(
        "20260917_161500",
        config,
        execute,
    )

    def on_finished(_result: object) -> None:
        callback_threads.append(QThread.currentThread())
        loop.quit()

    handle.finished.connect(on_finished)
    handle.failed.connect(lambda failure: (failures.append(failure), loop.quit()))
    handle.start()
    QTimer.singleShot(5_000, loop.quit)
    loop.exec()

    assert failures == []
    assert callback_threads, "worker finished signal was not delivered"
    assert callback_threads[0] == qapplication.thread()
    assert handle.wait_for_shutdown(1_000) is True
