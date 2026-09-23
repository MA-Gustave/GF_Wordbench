"""Path-resolved main-window composition for the desktop GUI.

The runtime owns presentation and worker lifecycle only.  Language/RGL facts
come from one immutable :class:`ResolvedLanguageContext`; executable run
configuration is resolved through the canonical configuration service; GF work
runs through the runs application service on the existing Qt worker boundary.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import os
from pathlib import Path
import shutil
from typing import Final

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from gf_wordbench.bootstrap import load_active_project
from gf_wordbench.config.environment import GF_EXECUTABLE_ENV, OUTPUT_ROOT_ENV
from gf_wordbench.config.models import ConfigurationResolutionRequest, ValidationTarget
from gf_wordbench.config.precedence import ConfigurationSource
from gf_wordbench.config.resolver import resolve_configuration
from gf_wordbench.entrypoints.gui.dialogs import DialogService, error_presentation_from_exception
from gf_wordbench.kernel.events import ProgressEvent
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.languages.models import ResolvedLanguageContext
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.runs.application import execute_diagnostic_run, execute_quick_run
from gf_wordbench.runs.identity import iter_run_id_candidates

from .panels.project import LanguageContextPanel
from .panels.validation import (
    ValidationChoice,
    ValidationPanel,
    ValidationPanelCatalog,
    ValidationPanelValues,
)
from .view_model import LanguageView, language_view_from_context
from .window import MainWindow, WindowRunState
from .workers import RunWorkerHandle, WorkerCancellation, WorkerFailure, create_run_worker

__all__ = (
    "PathResolvedMainGuiRuntime",
    "build_main_runtime",
)

_QUICK_READY_STATUS: Final[str] = (
    "Ready. Choose Entire language or File / module, then Run Scan."
)
_RUNNING_STATUS: Final[str] = "GF scan is running…"
_CANCELLING_STATUS: Final[str] = "Cancelling GF scan…"
_SHUTDOWN_WAIT_MS: Final[int] = 5_000
_GF_FILE_NAMES: Final[frozenset[str]] = frozenset({"gf", "gf.exe"})


class PathResolvedMainGuiRuntime:
    """Main GUI runtime owned by one immutable resolved language context."""

    __slots__ = (
        "__weakref__",
        "_application",
        "_closed",
        "_context",
        "_dialogs",
        "_gf_executable",
        "_last_run_dir",
        "_output_root",
        "_validation_profile",
        "_window",
        "_worker",
    )

    def __init__(
        self,
        application: object,
        context: ResolvedLanguageContext,
        *,
        window: MainWindow | None = None,
    ) -> None:
        if application is None:
            raise TypeError("application must not be None")
        if not isinstance(context, ResolvedLanguageContext):
            raise TypeError("context must be ResolvedLanguageContext")
        if window is not None and not isinstance(window, MainWindow):
            raise TypeError("window must be MainWindow or None")

        self._application = application
        self._context = context
        self._window = window or MainWindow()
        self._dialogs = DialogService(self._window)
        self._worker: RunWorkerHandle | None = None
        self._closed = False
        self._last_run_dir: Path | None = None
        self._gf_executable = _initial_gf_executable()
        self._output_root = _initial_output_root()
        self._validation_profile = _discover_validation_profile(context)

        self._render_language_context()
        self._configure_validation_surface()
        self._connect_language_switch_intents()
        self._connect_run_intents()
        self._refresh_run_available()
        self._window.set_run_state(
            WindowRunState.READY,
            status_message=_QUICK_READY_STATUS,
        )

    @property
    def window(self) -> MainWindow:
        return self._window

    @property
    def context(self) -> ResolvedLanguageContext:
        return self._context

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def gf_executable(self) -> Path | None:
        return self._gf_executable

    @property
    def output_root(self) -> Path:
        return self._output_root

    def shutdown(self) -> None:
        """Cancel bounded background work and dispose the main shell."""

        if self._closed:
            return
        self._closed = True
        worker = self._worker
        if worker is not None and worker.is_running():
            worker.request_cancellation("application_shutdown")
            worker.wait_for_shutdown(_SHUTDOWN_WAIT_MS)
        self._worker = None
        self._window.hide()
        self._window.deleteLater()

    def _render_language_context(self) -> None:
        view = language_view_from_context(self._context)
        project_panel = self._require_project_panel()
        project_panel.show_language(
            language_key=view.language_key,
            selected_path=view.selected_path,
            selected_path_kind=view.selected_path_kind.value,
            language_directory=view.language_directory,
            rgl_source_root=view.rgl_source_root,
            rgl_root=view.rgl_root,
            module_suffix=view.module_suffix,
            focused_target=view.focused_target,
            entrypoints=view.available_entrypoints,
            source_count=_global_census_size(self._context),
            capabilities=view.capability_statuses,
            validation_profile=(
                None if self._validation_profile is None else self._validation_profile.project_file
            ),
            resolution_message=_resolution_message(view),
        )
        self._window.set_project_identity(
            self._context.display_name,
            language_code=self._context.language_key,
        )

    def _configure_validation_surface(self) -> None:
        panel = self._require_validation_panel()
        target_choices = tuple(
            _target_choice(path, language_directory=self._context.language_directory)
            for path in self._context.source_inventory
        )
        profile = self._validation_profile
        if profile is None:
            panel.set_catalog(ValidationPanelCatalog(targets=target_choices))
        else:
            checkpoints = tuple(
                ValidationChoice(
                    identifier=path.as_posix(),
                    label=path.name,
                    description="Validation-profile checkpoint",
                )
                for path in profile.modules.checkpoints
            )
            required = tuple(str(value) for value in profile.validation.required_scenarios)
            optional = tuple(str(value) for value in profile.validation.optional_scenarios)
            scenarios = tuple(
                ValidationChoice(
                    identifier=scenario_id,
                    label=(f"[required] {scenario_id}" if scenario_id in required else scenario_id),
                    description="Albanian linguistic campaign scenario",
                )
                for scenario_id in (*required, *optional)
            )
            panel.set_catalog(
                ValidationPanelCatalog(
                    targets=target_choices,
                    checkpoints=checkpoints,
                    scenarios=scenarios,
                    release_scenarios=required,
                    release_checkpoint_count=len(checkpoints),
                )
            )
        focused_target = _focused_target_identifier(self._context)
        if profile is not None:
            panel.set_values(
                ValidationPanelValues(
                    mode=ValidationMode.DIAGNOSTIC,
                    target_file=None,
                    scenario_filter=tuple(str(value) for value in profile.validation.required_scenarios),
                    timeout_override=300,
                    keep_ok_details=True,
                    diff_previous=True,
                    emit_cpu_stats=True,
                    strict=True,
                    verbose_gf_output=True,
                )
            )
        else:
            panel.set_values(
                ValidationPanelValues(
                    # Directory selections open on the simplest useful action:
                    # scan the whole resolved language.  Selecting a .gf file at
                    # startup keeps the focused Quick target.
                    mode=(
                        ValidationMode.QUICK
                        if focused_target is not None
                        else ValidationMode.DIAGNOSTIC
                    ),
                    target_file=focused_target,
                )
            )

    def _connect_language_switch_intents(self) -> None:
        self._window.open_project_requested.connect(
            self._window.language_switch_requested.emit
        )
        project_panel = self._require_project_panel()
        project_panel.select_language_requested.connect(
            self._window.language_switch_requested.emit
        )
        project_panel.open_validation_profile_requested.connect(
            self._open_validation_profile
        )

    def _connect_run_intents(self) -> None:
        self._window.run_requested.connect(self._start_validation_run)
        self._window.cancel_requested.connect(self._cancel_run)
        self._window.settings_requested.connect(self._configure_gf_executable)
        self._window.test_environment_requested.connect(self._test_environment)
        self._window.open_last_run_requested.connect(self._open_last_run)
        self._window.open_reports_requested.connect(self._open_reports)
        panel = self._require_validation_panel()
        panel.values_changed.connect(lambda _values: self._refresh_run_available())
        panel.browse_target_requested.connect(self._browse_target)

    def _open_validation_profile(self, profile_path: object) -> None:
        path = Path(profile_path)
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _browse_target(self) -> None:
        panel = self._require_validation_panel()
        current_identifier = panel.values().target_file
        current = (
            self._context.language_directory / current_identifier
            if current_identifier
            else self._context.language_directory
        )
        allowed: set[Path] = set()
        for source in self._context.source_inventory:
            try:
                allowed.add(source.resolve(strict=False))
            except OSError:
                continue

        def is_allowed(path: Path) -> bool:
            try:
                return path.suffix.casefold() == ".gf" and path.resolve(strict=False) in allowed
            except OSError:
                return False

        selection = self._dialogs.select_file(
            title="Select GF scan target",
            purpose="validation_target",
            current=current,
            base_root=self._context.language_directory,
            file_filter="Grammatical Framework source (*.gf);;All files (*)",
            validator=is_allowed,
            rejection_message=(
                "Select a resolved GF source from the active language. "
                "Recheck the language first if a new source was added."
            ),
        )
        if selection.cancelled or selection.value is None:
            return
        panel.set_target_file(
            _relative_target(
                selection.value,
                language_directory=self._context.language_directory,
            )
        )

    def _refresh_run_available(self) -> None:
        if self._closed or (self._worker is not None and self._worker.is_running()):
            self._window.set_run_available(False)
            return
        values = self._require_validation_panel().values()
        local = self._require_validation_panel().local_validation()
        supported = values.mode in {ValidationMode.QUICK, ValidationMode.DIAGNOSTIC}
        quick_ready = values.mode is not ValidationMode.QUICK or values.target_file is not None
        # The primary UI presents one operation: scan the selected scope.
        # Internal validation modes remain an Advanced concern.
        self._window.set_run_action_label("Run Scan")
        available = supported and quick_ready and not local.has_errors
        self._window.set_run_available(available)

    def _start_validation_run(self) -> None:
        if self._worker is not None and self._worker.is_running():
            return
        panel = self._require_validation_panel()
        local = panel.local_validation()
        if local.has_errors:
            panel.focus_first_error()
            return
        values = panel.values()
        if values.mode not in {ValidationMode.QUICK, ValidationMode.DIAGNOSTIC}:
            self._dialogs.information(
                "Path-resolved execution runtime",
                "This runtime executes Quick and Diagnostic validation. "
                "Checkpoint and Release remain profile-driven stages.",
            )
            return
        if values.mode is ValidationMode.QUICK and values.no_compile:
            self._dialogs.information(
                "Quick execution runtime",
                "Scan-only Quick execution is not available. Clear Scan only to run GF.",
            )
            return
        if values.mode is ValidationMode.QUICK and values.target_file is None:
            panel.focus_first_error()
            return

        executable = self._require_gf_executable()
        if executable is None:
            return
        try:
            self._output_root.mkdir(parents=True, exist_ok=True)
            run_config = self._build_run_config(values, executable=executable)
            run_id = self._next_run_id()
        except Exception as exc:
            self._show_exception("Validation could not be configured.", exc)
            return

        def execute(config, event_sink, cancellation_check):
            runner = (
                execute_diagnostic_run
                if config.mode is ValidationMode.DIAGNOSTIC
                else execute_quick_run
            )
            return runner(
                config,
                event_sink,
                cancellation_check,
                run_id=run_id,
            )

        is_global = values.mode is ValidationMode.DIAGNOSTIC and values.target_file is None
        subject = "all GF sources" if is_global else values.target_file
        if values.mode is ValidationMode.DIAGNOSTIC:
            source_count = _global_census_size(self._context) if is_global else 1
            if is_global and values.max_files is not None:
                source_count = min(source_count, values.max_files)
            scenario_count = 0
            if self._validation_profile is not None:
                required_ids = {str(value) for value in self._validation_profile.validation.required_scenarios}
                optional_ids = set(values.scenario_filter).difference(required_ids)
                scenario_count = len(required_ids) + len(optional_ids)
            total = 2 + (2 * source_count) + scenario_count
        else:
            total = 3
        mode_label = (
            "Global Diagnostic scan"
            if is_global
            else f"{values.mode.value.title()} validation"
        )
        self._window.panels.results.clear_result()
        self._window.panels.progress.begin_run(
            run_id,
            status_text=f"Starting {mode_label}…",
            total=total,
            stage="prepare",
            subject=subject,
        )
        panel.set_running(True)
        self._window.set_run_available(False)
        self._window.set_run_state(
            WindowRunState.RUNNING,
            status_message=_RUNNING_STATUS,
        )

        try:
            worker = create_run_worker(
                run_id,
                run_config,
                execute,
                parent=self._window,
            )
            worker.progress.connect(self._on_worker_event)
            worker.finished.connect(self._on_run_finished)
            worker.cancelled.connect(self._on_run_cancelled)
            worker.failed.connect(self._on_run_failed)
            worker.cleaned_up.connect(self._on_worker_cleaned)
            self._worker = worker
            worker.start()
        except Exception as exc:
            self._worker = None
            panel.set_running(False)
            self._window.panels.progress.mark_failed("Worker startup failed")
            self._window.set_run_state(WindowRunState.READY)
            self._refresh_run_available()
            self._show_exception("Validation worker could not start.", exc)
            return

    def _build_run_config(self, values: ValidationPanelValues, *, executable: Path):
        if values.mode is ValidationMode.QUICK and values.target_file is None:
            raise ValueError("Quick target is required")
        if values.mode not in {ValidationMode.QUICK, ValidationMode.DIAGNOSTIC}:
            raise ValueError("Path-resolved execution supports Quick and Diagnostic")
        from gf_wordbench.config.defaults import build_framework_defaults

        if values.mode is ValidationMode.DIAGNOSTIC and values.target_file is None:
            target = ValidationTarget(TargetKind.PROJECT, None)
        elif values.target_file is not None:
            target = ValidationTarget(TargetKind.FILE, values.target_file)
        else:
            target = None

        gui_values: dict[str, object] = {
            "gf_executable": executable,
            "rgl_root": self._context.rgl_root,
            "output_root": self._output_root,
            "mode": values.mode,
            "target": target,
            "timeout_sec": values.timeout_override or 60,
            "max_files": values.max_files or 0,
            "keep_ok_details": values.keep_ok_details,
            "diff_previous": values.diff_previous,
            "skip_version_probe": values.skip_version_probe,
            "no_compile": values.no_compile if values.mode is ValidationMode.DIAGNOSTIC else False,
            "emit_cpu_stats": values.emit_cpu_stats,
        }
        resolution = resolve_configuration(
            ConfigurationResolutionRequest(
                defaults=build_framework_defaults(),
                language_context=self._context,
                validation_profile=self._validation_profile,
                source_values={ConfigurationSource.GUI: gui_values},
            )
        )
        config = resolution.require()
        if self._validation_profile is not None:
            config = replace(config, selected_scenarios=values.scenario_filter)
        return replace(config, strict=values.strict)

    def _next_run_id(self) -> str:
        now = datetime.now(UTC)
        for candidate in iter_run_id_candidates(now):
            if not (self._output_root / f"run_{candidate}").exists():
                return str(candidate)
        raise RuntimeError("unable to reserve a run identifier")

    def _require_gf_executable(self) -> Path | None:
        current = self._gf_executable
        if current is not None and _is_gf_executable(current):
            return current
        return self._configure_gf_executable()

    def _configure_gf_executable(self) -> Path | None:
        selection = self._dialogs.select_file(
            title="Select Grammatical Framework executable (gf.exe)",
            purpose="gf_executable",
            current=self._gf_executable,
            file_filter="Grammatical Framework (gf.exe gf);;All files (*)",
            validator=_is_gf_executable,
            rejection_message="Select an existing gf.exe (Windows) or gf executable.",
        )
        if selection.cancelled or selection.value is None:
            return None
        self._gf_executable = selection.value.resolve(strict=True)
        self._window.set_run_state(
            WindowRunState.READY,
            status_message=f"GF executable configured: {self._gf_executable}",
        )
        self._refresh_run_available()
        return self._gf_executable

    def _test_environment(self) -> None:
        executable = self._require_gf_executable()
        if executable is None:
            return
        values = self._require_validation_panel().values()
        target = values.target_file
        if target is None:
            target = _first_target_identifier(self._context)
        if target is None:
            self._dialogs.information(
                "GF environment",
                "No GF source target is available in the resolved language context.",
            )
            return
        try:
            probe_values = ValidationPanelValues(
                mode=ValidationMode.QUICK,
                target_file=target,
                timeout_override=values.timeout_override,
                skip_version_probe=False,
            )
            config = self._build_run_config(probe_values, executable=executable)
        except Exception as exc:
            self._show_exception("GF environment resolution failed.", exc)
            return
        rendered_path = os.pathsep.join(str(path) for path in config.environment.gf_path)
        self._dialogs.information(
            "GF environment ready",
            f"GF executable: {config.environment.gf_executable}\n"
            f"RGL root: {config.environment.rgl_root}\n"
            f"Run output: {config.environment.output_root}\n\n"
            f"GF path:\n{rendered_path}",
        )

    def _cancel_run(self) -> None:
        worker = self._worker
        if worker is None or not worker.is_running():
            return
        worker.request_cancellation("user")
        self._window.panels.progress.request_cancellation()
        self._window.set_run_state(
            WindowRunState.CANCELLING,
            status_message=_CANCELLING_STATUS,
        )

    def _on_worker_event(self, event: object) -> None:
        if isinstance(event, ProgressEvent):
            self._window.panels.progress.apply_event(event)

    def _on_run_finished(self, result: object) -> None:
        from gf_wordbench.runs.public import RunResult

        if not isinstance(result, RunResult):
            self._on_run_failed(
                WorkerFailure.from_exception(
                    self._window.panels.progress.model().run_id or "unknown",
                    TypeError("worker returned an invalid run result"),
                )
            )
            return
        # Result rendering is presentation work and must never keep the shell in
        # RUNNING/CANCELLING if a panel encounters an unexpected value.  The
        # worker has already returned a valid RunResult at this point, so make
        # the terminal UI transition exception-safe and preserve the run
        # directory even if rendering fails.
        self._last_run_dir = result.run_paths.run_dir
        try:
            self._window.panels.results.set_result(result)
            failures = result.totals.files_fail + result.totals.files_error
            label = (
                "Global Diagnostic scan"
                if result.run_config.mode is ValidationMode.DIAGNOSTIC
                and (
                    result.run_config.target is None
                    or result.run_config.target.kind is TargetKind.PROJECT
                )
                else f"{result.run_config.mode.value.title()} validation"
            )
            self._window.panels.progress.finish_run(
                f"{label} {result.overall_status.value}",
                warning_count=len(result.run_config.compatibility_warnings),
                failure_count=failures,
            )
            self._window.set_last_run_available(True)
            self._window.set_reports_available(
                result.run_paths.summary_md.exists()
                or result.run_paths.summary_json.exists()
            )
        except Exception as exc:
            self._window.panels.progress.mark_failed(
                "Validation completed, but the result UI could not be rendered"
            )
            self._finish_worker_ui(
                "Validation completed; result rendering failed"
            )
            self._show_exception(
                "Validation completed, but the result view failed.",
                exc,
            )
            return

        self._finish_worker_ui(
            f"Scan complete: {result.overall_status.value}"
        )

    def _on_run_cancelled(self, outcome: object) -> None:
        if isinstance(outcome, WorkerCancellation):
            message = outcome.message
        else:
            message = "Run cancelled"
        self._window.panels.progress.mark_cancelled(message)
        self._finish_worker_ui(message)

    def _on_run_failed(self, failure: object) -> None:
        if isinstance(failure, WorkerFailure):
            message = failure.message
            detail = failure.detail or failure.traceback_text
            exc = RuntimeError(f"{failure.exception_type}: {message}\n{detail}".strip())
        elif isinstance(failure, Exception):
            message = str(failure) or type(failure).__name__
            exc = failure
        else:
            message = "Validation failed"
            exc = RuntimeError(repr(failure))
        self._window.panels.progress.mark_failed(message)
        self._finish_worker_ui("Validation failed")
        self._show_exception("Validation failed.", exc)

    def _finish_worker_ui(self, status_message: str) -> None:
        self._require_validation_panel().set_running(False)
        self._window.notify_run_finished()
        self._window.set_run_state(
            WindowRunState.READY,
            status_message=status_message,
        )
        self._refresh_run_available()

    def _on_worker_cleaned(self, _run_id: str) -> None:
        self._worker = None
        self._refresh_run_available()

    def _open_last_run(self) -> None:
        if self._last_run_dir is not None and self._last_run_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_run_dir)))

    def _open_reports(self) -> None:
        self._open_last_run()

    def _show_exception(self, summary: str, exc: Exception) -> None:
        self._dialogs.error(
            error_presentation_from_exception(
                exc,
                summary=summary,
                recommended_action="Review the details, correct the configuration if needed, and retry.",
            )
        )

    def _require_project_panel(self) -> LanguageContextPanel:
        panel = self._window.panels.project
        if not isinstance(panel, LanguageContextPanel):
            raise TypeError("main window project panel must be LanguageContextPanel")
        return panel

    def _require_validation_panel(self) -> ValidationPanel:
        panel = self._window.panels.validation
        if not isinstance(panel, ValidationPanel):
            raise TypeError("main window validation panel must be ValidationPanel")
        return panel



_STANDARD_API_FACADE_PREFIXES: tuple[str, ...] = (
    "Combinators", "Constructors", "Symbolic", "Syntax", "Try"
)


def _global_census_size(context: ResolvedLanguageContext) -> int:
    """Return the same conservative source count used by Diagnostic Global Scan."""

    base = len(context.source_inventory)
    language_root = context.language_directory.resolve(strict=False)
    rgl_source_root = context.rgl_source_root.resolve(strict=False)
    suffix = context.module_suffix
    if not suffix:
        return base

    owned = {path.resolve(strict=False) for path in context.source_inventory}
    if language_root.parent == rgl_source_root:
        candidates = tuple(rgl_source_root.glob(f"*{suffix}.gf"))
    else:
        facade_root = language_root.parent
        candidates = tuple(
            facade_root / f"{prefix}{suffix}.gf"
            for prefix in _STANDARD_API_FACADE_PREFIXES
        )
    facades = sum(
        1
        for candidate in candidates
        if candidate.is_file() and candidate.resolve(strict=False) not in owned
    )
    return base + facades

def build_main_runtime(
    application: object,
    context: ResolvedLanguageContext,
) -> PathResolvedMainGuiRuntime:
    """Compose the canonical executable main runtime for one language."""

    return PathResolvedMainGuiRuntime(application, context)


def _discover_validation_profile(context: ResolvedLanguageContext) -> ProjectConfig | None:
    """Find the nearest compatible project.toml without changing language authority."""

    language_directory = context.language_directory.resolve(strict=True)
    candidates = (language_directory, *language_directory.parents)
    for root in candidates[:10]:
        candidate = root / "project.toml"
        if not candidate.is_file():
            continue
        try:
            profile = load_active_project(candidate.resolve(strict=True), strict=False)
        except Exception:
            continue
        try:
            source_root = profile.source_root.resolve(strict=True)
        except OSError:
            continue
        if source_root != language_directory:
            continue
        if profile.identity.language_code.casefold() != context.language_key.casefold():
            continue
        return profile
    return None


def _initial_gf_executable() -> Path | None:
    configured = os.environ.get(GF_EXECUTABLE_ENV, "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve(strict=False)
        if _is_gf_executable(candidate):
            return candidate

    workspace_default = _workspace_default_gf_executable()
    if workspace_default is not None:
        return workspace_default

    discovered = shutil.which("gf.exe") or shutil.which("gf")
    if discovered:
        candidate = Path(discovered).resolve(strict=False)
        if _is_gf_executable(candidate):
            return candidate
    return None


def _workspace_default_gf_executable(
    *,
    repository_root: Path | None = None,
) -> Path | None:
    """Return the workspace-local GF 3.12 executable when present.

    The installed Wordbench repository normally lives at
    ``<workspace>/GF_Wordbench/GF_Wordbench``.  Keep the default portable by
    deriving the workspace from the running package instead of hard-coding a
    drive letter.  Explicit ``GF_WORDBENCH_GF_EXE`` configuration still has
    higher precedence, while PATH discovery remains the final fallback.
    """

    root = repository_root
    if root is None:
        root = Path(__file__).resolve().parents[4]
    workspace_root = root.parent.parent
    candidate = (workspace_root / "gf-3.12-windows" / "gf.exe").resolve(
        strict=False
    )
    if _is_gf_executable(candidate):
        return candidate
    return None


def _initial_output_root() -> Path:
    configured = os.environ.get(OUTPUT_ROOT_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve(strict=False)
    repository_root = Path(__file__).resolve().parents[4]
    return (repository_root / ".wordbench-runs").resolve(strict=False)


def _is_gf_executable(path: Path) -> bool:
    try:
        return path.is_file() and path.name.casefold() in _GF_FILE_NAMES
    except OSError:
        return False


def _resolution_message(view: LanguageView) -> str:
    if not view.issues:
        return "The selected language context is ready."
    if len(view.issues) == 1:
        return f"Language context ready with warning: {view.issues[0]}"
    return f"Language context ready with {len(view.issues)} nonblocking warnings."


def _target_choice(path: Path, *, language_directory: Path) -> ValidationChoice:
    identifier = _relative_target(path, language_directory=language_directory)
    return ValidationChoice(
        identifier=identifier,
        label=identifier,
        description=str(path),
    )


def _focused_target_identifier(context: ResolvedLanguageContext) -> str | None:
    target = context.focused_target
    if target is None:
        return None
    return _relative_target(target, language_directory=context.language_directory)


def _first_target_identifier(context: ResolvedLanguageContext) -> str | None:
    if not context.source_inventory:
        return None
    return _relative_target(
        context.source_inventory[0],
        language_directory=context.language_directory,
    )


def _relative_target(path: Path, *, language_directory: Path) -> str:
    try:
        relative = path.relative_to(language_directory)
    except ValueError as exc:
        raise ValueError("validation target must remain inside language_directory") from exc
    rendered = relative.as_posix()
    if not rendered or rendered == ".":
        raise ValueError("validation target must identify a GF source file")
    return rendered
