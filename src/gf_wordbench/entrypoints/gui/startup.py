"""Path-resolved startup surface for the GF Wordbench desktop GUI.

This module owns only GUI startup interaction and coordination.  It accepts one
explicit language directory or ``.gf`` file, delegates language resolution to an
injected application service, and composes the main GUI runtime only after one
immutable language context has been resolved.

The module deliberately does not enumerate GF sources, resolve GF search paths,
invoke GF, parse diagnostics, or persist application state directly.  Those
responsibilities remain behind the injected service boundary.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
from inspect import Parameter, Signature
from pathlib import Path
from typing import Final, Generic, Protocol, TypeVar, runtime_checkable

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.entrypoints.gui.dialogs import (
    DialogService,
    ErrorPresentation,
    error_presentation_from_exception,
)
from gf_wordbench.projects.languages.models import (
    LanguageModuleCandidate,
    LanguageProbeSeverity,
    LanguageProbeDiagnostic,
    LanguageProbeRequest,
    LanguageProbeResult as _CanonicalLanguageProbeResult,
    LanguageProbeStatus,
    ResolvedLanguageContext,
)

__all__ = (
    "IntroductionWindow",
    "LanguageCandidatePresentation",
    "LanguageProbeDisposition",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageRuntimeSwitcher",
    "LanguageSwitchDisposition",
    "PathResolvedGuiRuntime",
    "ResolvedLanguagePresentation",
    "StartupDiagnostic",
    "StartupDiagnosticSeverity",
    "StartupPhase",
    "StartupServices",
    "StartupSnapshot",
    "build_startup_runtime",
)

ContextT = TypeVar("ContextT")

_MAX_TEXT: Final[int] = 8_000
_MAX_DETAILS: Final[int] = 64_000
_MAX_CANDIDATES: Final[int] = 1_000
_DEFAULT_WIDTH: Final[int] = 760
_DEFAULT_HEIGHT: Final[int] = 620
_PROBE_SHUTDOWN_WAIT_MS: Final[int] = 5_000
_GF_FILE_FILTER: Final[str] = "Grammatical Framework source (*.gf);;All files (*)"


@unique
class StartupPhase(StrEnum):
    """Stable phases of the interactive startup lifecycle."""

    READY = "ready"
    SELECTING = "selecting"
    PROBING = "probing"
    NEEDS_USER_INPUT = "needs_user_input"
    RESOLVED = "resolved"
    COMPOSING = "composing"
    RUNNING = "running"
    FAILED = "failed"
    CLOSING = "closing"
    CLOSED = "closed"


@unique
class StartupDiagnosticSeverity(StrEnum):
    """Presentation severity for language-resolution diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# Compatibility re-export: the canonical status is owned by projects.languages.
LanguageProbeDisposition = LanguageProbeStatus


@dataclass(frozen=True, slots=True, init=False)
class LanguageProbeResult:
    """GUI-compatible probe result supporting the legacy presentation seam.

    Production services may return the canonical project-layer result directly;
    this adapter exists so the GUI integration boundary can also carry an
    already-projected presentation without weakening the project model.
    """

    status: LanguageProbeStatus
    context: object | None
    diagnostics: tuple[LanguageProbeDiagnostic, ...]
    choices: tuple[object, ...]
    presentation: ResolvedLanguagePresentation | None
    candidate: object | None

    def __init__(
        self,
        status: LanguageProbeStatus | None = None,
        *,
        disposition: LanguageProbeStatus | None = None,
        context: object | None = None,
        diagnostics: tuple[LanguageProbeDiagnostic, ...] = (),
        choices: tuple[object, ...] = (),
        presentation: ResolvedLanguagePresentation | None = None,
        candidate: object | None = None,
    ) -> None:
        resolved_status = status if status is not None else disposition
        if not isinstance(resolved_status, LanguageProbeStatus):
            raise TypeError("status or disposition must be a LanguageProbeStatus")
        if presentation is not None and not isinstance(presentation, ResolvedLanguagePresentation):
            raise TypeError("presentation must be ResolvedLanguagePresentation or None")
        object.__setattr__(self, "status", resolved_status)
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "diagnostics", tuple(diagnostics))
        object.__setattr__(self, "choices", tuple(choices))
        object.__setattr__(self, "presentation", presentation)
        object.__setattr__(self, "candidate", candidate)

    @property
    def disposition(self) -> LanguageProbeStatus:
        return self.status


@dataclass(frozen=True, slots=True)
class StartupDiagnostic:
    """One bounded diagnostic suitable for startup presentation."""

    code: str
    severity: StartupDiagnosticSeverity
    message: str
    detail: str = ""
    remediation: str = ""

    def __post_init__(self) -> None:
        _require_text(self.code, field="code", maximum=128)
        if not isinstance(self.severity, StartupDiagnosticSeverity):
            raise TypeError("severity must be a StartupDiagnosticSeverity")
        _require_text(self.message, field="message", maximum=_MAX_TEXT)
        _require_text(
            self.detail,
            field="detail",
            allow_empty=True,
            maximum=_MAX_DETAILS,
        )
        _require_text(
            self.remediation,
            field="remediation",
            allow_empty=True,
            maximum=_MAX_TEXT,
        )


@dataclass(frozen=True, slots=True)
class LanguageCandidatePresentation:
    """One exact GUI choice projected from a canonical probe candidate."""

    candidate_id: str
    label: str
    path: Path | None = None
    detail: str = ""
    module_suffix_choice: str | None = None
    entrypoint_choice: Path | None = None

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, field="candidate_id", maximum=512)
        _require_text(self.label, field="label", maximum=1_024)
        if self.path is not None and not isinstance(self.path, Path):
            raise TypeError("path must be a pathlib.Path or None")
        if self.module_suffix_choice is not None:
            _require_text(
                self.module_suffix_choice,
                field="module_suffix_choice",
                maximum=256,
            )
        if self.entrypoint_choice is not None and not isinstance(
            self.entrypoint_choice,
            Path,
        ):
            raise TypeError("entrypoint_choice must be a pathlib.Path or None")
        if self.module_suffix_choice is not None and self.entrypoint_choice is not None:
            raise ValueError(
                "a candidate must select either a module suffix or an entrypoint, not both"
            )
        _require_text(
            self.detail,
            field="detail",
            allow_empty=True,
            maximum=_MAX_DETAILS,
        )


@dataclass(frozen=True, slots=True)
class ResolvedLanguagePresentation:
    """Read-only summary of one resolved language context."""

    language_key: str
    language_directory: Path
    rgl_source_root: Path
    selected_path: Path
    selected_path_kind: str
    module_suffix: str | None = None
    focused_target: Path | None = None
    available_entrypoints: tuple[Path, ...] = ()
    source_count: int = 0
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.language_key, field="language_key", maximum=1_024)
        for field_name in (
            "language_directory",
            "rgl_source_root",
            "selected_path",
        ):
            if not isinstance(getattr(self, field_name), Path):
                raise TypeError(f"{field_name} must be a pathlib.Path")
        _require_text(
            self.selected_path_kind,
            field="selected_path_kind",
            maximum=64,
        )
        if self.module_suffix is not None:
            _require_text(
                self.module_suffix,
                field="module_suffix",
                maximum=256,
            )
        if self.focused_target is not None and not isinstance(self.focused_target, Path):
            raise TypeError("focused_target must be a pathlib.Path or None")
        if not isinstance(self.available_entrypoints, tuple):
            raise TypeError("available_entrypoints must be a tuple")
        if any(not isinstance(item, Path) for item in self.available_entrypoints):
            raise TypeError("available_entrypoints must contain pathlib.Path values")
        if type(self.source_count) is not int or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if not isinstance(self.capabilities, tuple):
            raise TypeError("capabilities must be a tuple")
        for index, capability in enumerate(self.capabilities):
            _require_text(
                capability,
                field=f"capabilities[{index}]",
                maximum=256,
            )


@dataclass(frozen=True, slots=True)
class _StartupProbeView:
    """Presentation projection of one canonical language-probe result."""

    status: LanguageProbeStatus
    context: object | None
    presentation: ResolvedLanguagePresentation | None
    diagnostics: tuple[StartupDiagnostic, ...]
    candidates: tuple[LanguageCandidatePresentation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.status, LanguageProbeStatus):
            raise TypeError("status must be a LanguageProbeStatus")
        if self.context is not None:
            _require_resolved_context_contract(self.context)
        if self.presentation is not None and not isinstance(
            self.presentation,
            ResolvedLanguagePresentation,
        ):
            raise TypeError("presentation must be a ResolvedLanguagePresentation or None")
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("diagnostics must be a tuple")
        if any(not isinstance(item, StartupDiagnostic) for item in self.diagnostics):
            raise TypeError("diagnostics must contain StartupDiagnostic values")
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates must be a tuple")
        if any(not isinstance(item, LanguageCandidatePresentation) for item in self.candidates):
            raise TypeError("candidates must contain LanguageCandidatePresentation values")


@dataclass(frozen=True, slots=True)
class StartupSnapshot:
    """Current presentation state of the introduction surface."""

    phase: StartupPhase
    last_selected_path: Path | None
    selected_path: Path | None
    status_message: str
    can_open_last: bool
    can_choose_path: bool
    can_choose_candidate: bool
    can_quit: bool

    def __post_init__(self) -> None:
        if not isinstance(self.phase, StartupPhase):
            raise TypeError("phase must be a StartupPhase")
        for field_name in ("last_selected_path", "selected_path"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, Path):
                raise TypeError(f"{field_name} must be a pathlib.Path or None")
        _require_text(
            self.status_message,
            field="status_message",
            allow_empty=True,
            maximum=_MAX_TEXT,
        )
        for field_name in (
            "can_open_last",
            "can_choose_path",
            "can_choose_candidate",
            "can_quit",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a bool")


@runtime_checkable
class MainGuiRuntime(Protocol):
    """Main runtime composed after language resolution succeeds."""

    @property
    def window(self) -> object:
        """Return the top-level main window."""

    def shutdown(self) -> None:
        """Release resources without starting new work."""


@runtime_checkable
class SwitchableRuntime(Protocol):
    """Minimal runtime surface required by the language switcher."""

    def shutdown(self) -> None:
        """Release runtime resources."""


@dataclass(frozen=True, slots=True)
class StartupServices:
    """Injected application services required by interactive startup."""

    probe_language: Callable[
        [LanguageProbeRequest],
        LanguageProbeResult | _CanonicalLanguageProbeResult,
    ]
    build_main_runtime: Callable[
        [object, ResolvedLanguageContext],
        MainGuiRuntime,
    ]
    load_last_selected_path: Callable[[], Path | None]
    remember_selected_path: Callable[[Path], None] | None = None
    clear_last_selected_path: Callable[[], None] | None = None
    load_rgl_root: Callable[[], Path | None] | None = None
    remember_rgl_root: Callable[[Path], None] | None = None
    configure_environment: Callable[[object], None] | None = None
    has_active_run: Callable[[], bool] | None = None
    error_from_exception: Callable[[Exception], ErrorPresentation] | None = None

    def __post_init__(self) -> None:
        required = (
            "probe_language",
            "build_main_runtime",
            "load_last_selected_path",
        )
        optional = (
            "remember_selected_path",
            "clear_last_selected_path",
            "load_rgl_root",
            "remember_rgl_root",
            "configure_environment",
            "has_active_run",
            "error_from_exception",
        )
        for field_name in required:
            if not callable(getattr(self, field_name)):
                raise TypeError(f"{field_name} must be callable")
        for field_name in optional:
            value = getattr(self, field_name)
            if value is not None and not callable(value):
                raise TypeError(f"{field_name} must be callable or None")


@unique
class LanguageSwitchDisposition(StrEnum):
    """Stable outcomes returned by the language runtime switcher."""

    OPENED = "opened"
    SWITCHED = "switched"
    BUSY = "busy"


class LanguageRuntimeSwitcher(Generic[ContextT]):
    """Own exactly one path-resolved language runtime at a time.

    Construction is inert. A language is probed only after ``open_language()``
    or ``switch_language()`` receives an explicit path. During replacement, the
    old runtime is disposed before the new path is probed, and a failed
    replacement never restores the disposed runtime.
    """

    __slots__ = (
        "_active_context",
        "_active_runtime",
        "_build_runtime",
        "_closed",
        "_has_active_run",
        "_persist_selected_path",
        "_probe_language",
        "_transitioning",
    )

    def __init__(
        self,
        *,
        probe_language: Callable[[Path], ContextT],
        build_runtime: Callable[[ContextT], SwitchableRuntime],
        persist_selected_path: Callable[[Path], None],
        has_active_run: Callable[[], bool],
    ) -> None:
        callbacks = {
            "probe_language": probe_language,
            "build_runtime": build_runtime,
            "persist_selected_path": persist_selected_path,
            "has_active_run": has_active_run,
        }
        for field_name, callback in callbacks.items():
            if not callable(callback):
                raise TypeError(f"{field_name} must be callable")

        self._probe_language = probe_language
        self._build_runtime = build_runtime
        self._persist_selected_path = persist_selected_path
        self._has_active_run = has_active_run
        self._active_context: ContextT | None = None
        self._active_runtime: SwitchableRuntime | None = None
        self._closed = False
        self._transitioning = False

    @property
    def active_context(self) -> ContextT | None:
        """Return the currently resolved context, if any."""

        return self._active_context

    @property
    def active_runtime(self) -> SwitchableRuntime | None:
        """Return the currently active runtime, if any."""

        return self._active_runtime

    def open_language(self, path: Path) -> LanguageSwitchDisposition:
        """Open the first language from one explicit path."""

        self._require_open()
        if self._active_runtime is not None:
            raise RuntimeError("a language runtime is already active; use switch_language()")
        if self._transitioning:
            return LanguageSwitchDisposition.BUSY
        return self._activate(
            path,
            disposition=LanguageSwitchDisposition.OPENED,
        )

    def switch_language(self, path: Path) -> LanguageSwitchDisposition:
        """Dispose the current runtime and resolve a replacement language."""

        self._require_open()
        if self._transitioning or bool(self._has_active_run()):
            return LanguageSwitchDisposition.BUSY

        self._transitioning = True
        try:
            self._dispose_active_runtime()
            return self._activate_prevalidated(
                path,
                disposition=LanguageSwitchDisposition.SWITCHED,
            )
        finally:
            self._transitioning = False

    def shutdown(self) -> None:
        """Dispose the active runtime exactly once."""

        if self._closed:
            return
        self._closed = True
        self._dispose_active_runtime()

    def _activate(
        self,
        path: Path,
        *,
        disposition: LanguageSwitchDisposition,
    ) -> LanguageSwitchDisposition:
        if self._transitioning:
            return LanguageSwitchDisposition.BUSY
        self._transitioning = True
        try:
            return self._activate_prevalidated(path, disposition=disposition)
        finally:
            self._transitioning = False

    def _activate_prevalidated(
        self,
        path: Path,
        *,
        disposition: LanguageSwitchDisposition,
    ) -> LanguageSwitchDisposition:
        selected_path = _normalize_language_selection(path)
        context = self._probe_language(selected_path)
        runtime = _require_switchable_runtime(self._build_runtime(context))

        try:
            self._persist_selected_path(selected_path)
        except Exception:
            try:
                runtime.shutdown()
            finally:
                self._active_context = None
                self._active_runtime = None
            raise

        self._active_context = context
        self._active_runtime = runtime
        return disposition

    def _dispose_active_runtime(self) -> None:
        runtime = self._active_runtime
        self._active_context = None
        self._active_runtime = None
        if runtime is None:
            return
        shutdown = getattr(runtime, "shutdown", None)
        if not callable(shutdown):
            raise TypeError("active language runtime must provide shutdown()")
        shutdown()

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("language runtime switcher is closed")


class IntroductionWindow(QMainWindow):
    """Introduction window shown before any language runtime exists."""

    open_last_requested = Signal()
    choose_directory_requested = Signal()
    choose_file_requested = Signal()
    configure_environment_requested = Signal()
    candidate_requested = Signal(str)
    quit_requested = Signal()

    def __init__(
        self,
        *,
        dialog_service: DialogService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._dialogs = dialog_service or DialogService(self)
        self._dialogs.set_parent(self)
        self._allow_close = False
        self._last_selected_path: Path | None = None
        self._selected_path: Path | None = None
        self._rgl_root: Path | None = None

        self.setObjectName("gfWordbenchIntroductionWindow")
        self.setWindowTitle("GF Wordbench")
        self.setMinimumSize(640, 500)
        self.resize(_DEFAULT_WIDTH, _DEFAULT_HEIGHT)
        self.setAccessibleName("GF Wordbench language startup")

        self._build_ui()
        self._connect_signals()
        self.show_snapshot(
            StartupSnapshot(
                phase=StartupPhase.READY,
                last_selected_path=None,
                selected_path=None,
                status_message="Choose a GF language directory or a .gf file.",
                can_open_last=False,
                can_choose_path=True,
                can_choose_candidate=False,
                can_quit=True,
            )
        )

    @property
    def dialog_service(self) -> DialogService:
        return self._dialogs

    @property
    def last_selected_path(self) -> Path | None:
        return self._last_selected_path

    @property
    def selected_path(self) -> Path | None:
        return self._selected_path

    @property
    def rgl_root(self) -> Path | None:
        """Return the explicit RGL dependency root selected for startup."""

        return self._rgl_root

    def set_rgl_root(self, path: Path | None) -> None:
        if path is not None and not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path or None")
        self._rgl_root = path
        self._rgl_root_value.setText(str(path) if path is not None else "Auto-detect")
        self._rgl_root_value.setToolTip(str(path) if path is not None else "")

    def set_last_selected_path(self, path: Path | None) -> None:
        if path is not None and not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path or None")
        self._last_selected_path = path
        self._last_path_value.setText(str(path) if path is not None else "None")
        self._last_path_value.setToolTip(str(path) if path is not None else "")

    def choose_language_directory(self) -> Path | None:
        result = self._dialogs.select_directory(
            title="Choose GF language directory",
            purpose="language-source",
            current=self._selected_path or self._last_selected_path,
            rejection_message="Select an existing GF language directory.",
        )
        return None if result.cancelled else result.value

    def choose_gf_file(self) -> Path | None:
        result = self._dialogs.select_file(
            title="Choose GF source file",
            purpose="language-source",
            current=self._selected_path or self._last_selected_path,
            file_filter=_GF_FILE_FILTER,
            validator=lambda path: path.suffix.lower() == ".gf",
            rejection_message="Select an existing .gf source file.",
        )
        return None if result.cancelled else result.value

    def choose_rgl_root(self) -> Path | None:
        """Choose an explicit RGL dependency checkout for external projects."""

        result = self._dialogs.select_directory(
            title="Choose RGL repository root or src directory",
            purpose="rgl-root",
            current=self._rgl_root,
            rejection_message=(
                "Select the gf-rgl repository root or its readable src directory."
            ),
        )
        return None if result.cancelled else result.value

    def show_snapshot(self, snapshot: StartupSnapshot) -> None:
        if not isinstance(snapshot, StartupSnapshot):
            raise TypeError("snapshot must be a StartupSnapshot")
        self._last_selected_path = snapshot.last_selected_path
        self._selected_path = snapshot.selected_path
        self._last_path_value.setText(
            str(snapshot.last_selected_path) if snapshot.last_selected_path is not None else "None"
        )
        self._selected_path_value.setText(
            str(snapshot.selected_path) if snapshot.selected_path is not None else "None"
        )
        self._status_label.setText(snapshot.status_message or "Ready")
        self._open_last_button.setEnabled(snapshot.can_open_last)
        self._choose_directory_button.setEnabled(snapshot.can_choose_path)
        self._choose_file_button.setEnabled(snapshot.can_choose_path)
        self._environment_button.setEnabled(snapshot.can_choose_path)
        self._use_candidate_button.setEnabled(snapshot.can_choose_candidate)
        self._quit_button.setEnabled(snapshot.can_quit)

        busy = snapshot.phase in {
            StartupPhase.PROBING,
            StartupPhase.COMPOSING,
            StartupPhase.CLOSING,
        }
        self._progress.setVisible(busy)
        if busy:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 1)
            self._progress.setValue(0)

    def show_probe_result(self, result: _StartupProbeView) -> None:
        if not isinstance(result, _StartupProbeView):
            raise TypeError("result must be a _StartupProbeView")
        self._show_diagnostics(result.diagnostics)
        self._show_candidates(result.candidates)
        if result.presentation is not None:
            self._show_resolution(result.presentation)
        else:
            self._resolution_value.setPlainText("")

    def show_exception(self, presentation: ErrorPresentation) -> None:
        if not isinstance(presentation, ErrorPresentation):
            raise TypeError("presentation must be an ErrorPresentation")
        self._dialogs.error(presentation)

    def allow_close(self) -> None:
        self._allow_close = True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
            return
        event.ignore()
        self.quit_requested.emit()

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("startupRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("GF Wordbench", root)
        heading.setObjectName("startupHeading")
        heading.setStyleSheet("font-size: 26px; font-weight: 600;")
        heading.setAccessibleName("GF Wordbench")
        layout.addWidget(heading)

        explanation = QLabel(
            "Open one GF language directory or one .gf file. "
            "Wordbench will resolve the language context before opening "
            "the main window.",
            root,
        )
        explanation.setWordWrap(True)
        explanation.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(explanation)

        path_frame = QFrame(root)
        path_frame.setFrameShape(QFrame.Shape.StyledPanel)
        path_layout = QVBoxLayout(path_frame)

        last_label = QLabel("Last selected language path", path_frame)
        last_label.setStyleSheet("font-weight: 600;")
        path_layout.addWidget(last_label)
        self._last_path_value = QLabel("None", path_frame)
        self._last_path_value.setWordWrap(True)
        self._last_path_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_layout.addWidget(self._last_path_value)

        selected_label = QLabel("Current selection", path_frame)
        selected_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        path_layout.addWidget(selected_label)
        self._selected_path_value = QLabel("None", path_frame)
        self._selected_path_value.setWordWrap(True)
        self._selected_path_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        path_layout.addWidget(self._selected_path_value)

        rgl_label = QLabel("RGL dependency root", path_frame)
        rgl_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        path_layout.addWidget(rgl_label)
        self._rgl_root_value = QLabel("Auto-detect", path_frame)
        self._rgl_root_value.setWordWrap(True)
        self._rgl_root_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        path_layout.addWidget(self._rgl_root_value)
        layout.addWidget(path_frame)

        action_row = QHBoxLayout()
        self._open_last_button = QPushButton("Open last language", root)
        self._choose_directory_button = QPushButton("Choose language directory…", root)
        self._choose_file_button = QPushButton("Choose .gf file…", root)
        action_row.addWidget(self._open_last_button)
        action_row.addWidget(self._choose_directory_button)
        action_row.addWidget(self._choose_file_button)
        layout.addLayout(action_row)

        second_row = QHBoxLayout()
        self._environment_button = QPushButton("Configure RGL dependency…", root)
        self._quit_button = QPushButton("Quit", root)
        second_row.addWidget(self._environment_button)
        second_row.addStretch(1)
        second_row.addWidget(self._quit_button)
        layout.addLayout(second_row)

        self._progress = QProgressBar(root)
        self._progress.setTextVisible(False)
        self._progress.setAccessibleName("Language resolution progress")
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("Ready", root)
        self._status_label.setWordWrap(True)
        self._status_label.setAccessibleName("Startup status")
        layout.addWidget(self._status_label)

        self._candidate_label = QLabel("Choose one exact candidate", root)
        self._candidate_label.setStyleSheet("font-weight: 600;")
        self._candidate_label.setVisible(False)
        layout.addWidget(self._candidate_label)

        self._candidates = QListWidget(root)
        self._candidates.setAccessibleName("Language resolution candidates")
        self._candidates.setVisible(False)
        self._candidates.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self._candidates)

        self._use_candidate_button = QPushButton("Use selected candidate", root)
        self._use_candidate_button.setVisible(False)
        self._use_candidate_button.setEnabled(False)
        layout.addWidget(self._use_candidate_button)

        details_label = QLabel("Resolution details", root)
        details_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(details_label)

        self._resolution_value = QPlainTextEdit(root)
        self._resolution_value.setReadOnly(True)
        self._resolution_value.setMaximumBlockCount(1_000)
        self._resolution_value.setAccessibleName("Resolved language details")
        self._resolution_value.setMinimumHeight(90)
        layout.addWidget(self._resolution_value)

        diagnostics_label = QLabel("Diagnostics", root)
        diagnostics_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(diagnostics_label)

        self._diagnostics = QPlainTextEdit(root)
        self._diagnostics.setReadOnly(True)
        self._diagnostics.setMaximumBlockCount(2_000)
        self._diagnostics.setAccessibleName("Startup diagnostics")
        layout.addWidget(self._diagnostics, 1)

        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self._open_last_button.clicked.connect(self.open_last_requested.emit)
        self._choose_directory_button.clicked.connect(self.choose_directory_requested.emit)
        self._choose_file_button.clicked.connect(self.choose_file_requested.emit)
        self._environment_button.clicked.connect(self.configure_environment_requested.emit)
        self._quit_button.clicked.connect(self.quit_requested.emit)
        self._use_candidate_button.clicked.connect(self._emit_candidate)
        self._candidates.itemSelectionChanged.connect(self._update_candidate_button)
        self._candidates.itemDoubleClicked.connect(lambda _item: self._emit_candidate())

    @Slot()
    def _update_candidate_button(self) -> None:
        self._use_candidate_button.setEnabled(self._candidates.currentItem() is not None)

    @Slot()
    def _emit_candidate(self) -> None:
        item: object = self._candidates.currentItem()
        if not isinstance(item, QListWidgetItem):
            return
        candidate_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(candidate_id, str) and candidate_id:
            self.candidate_requested.emit(candidate_id)

    def _show_candidates(
        self,
        candidates: tuple[LanguageCandidatePresentation, ...],
    ) -> None:
        self._candidates.clear()
        visible = bool(candidates)
        self._candidate_label.setVisible(visible)
        self._candidates.setVisible(visible)
        self._use_candidate_button.setVisible(visible)
        self._use_candidate_button.setEnabled(False)
        for candidate in candidates:
            label = candidate.label
            if candidate.path is not None:
                label = f"{label}\n{candidate.path}"
            item = QListWidgetItem(label, self._candidates)
            item.setData(Qt.ItemDataRole.UserRole, candidate.candidate_id)
            details = candidate.detail
            if candidate.path is not None:
                details = f"{candidate.path}\n\n{details}".strip()
            item.setToolTip(details)
        if candidates:
            self._candidates.setCurrentRow(0)

    def _show_diagnostics(
        self,
        diagnostics: tuple[StartupDiagnostic, ...],
    ) -> None:
        parts: list[str] = []
        for diagnostic in diagnostics:
            heading = (
                f"[{diagnostic.severity.value.upper()}] {diagnostic.code}: {diagnostic.message}"
            )
            details = [heading]
            if diagnostic.detail:
                details.append(diagnostic.detail)
            if diagnostic.remediation:
                details.append(f"Action: {diagnostic.remediation}")
            parts.append("\n".join(details))
        self._diagnostics.setPlainText("\n\n".join(parts))

    def _show_resolution(self, value: ResolvedLanguagePresentation) -> None:
        lines = [
            f"Language: {value.language_key}",
            f"Selected path: {value.selected_path}",
            f"Language directory: {value.language_directory}",
            f"RGL source root: {value.rgl_source_root}",
            f"Source files: {value.source_count}",
        ]
        if value.module_suffix:
            lines.append(f"Module suffix: {value.module_suffix}")
        if value.focused_target is not None:
            lines.append(f"Focused target: {value.focused_target}")
        if value.available_entrypoints:
            lines.append(
                "Entrypoints: " + ", ".join(path.name for path in value.available_entrypoints)
            )
        if value.capabilities:
            lines.append("Capabilities: " + ", ".join(value.capabilities))
        self._resolution_value.setPlainText("\n".join(lines))


class _ProbeThread(QThread):
    """One bounded background invocation of the injected language probe."""

    result_ready = Signal(object)
    probe_failed = Signal(object)

    def __init__(
        self,
        request: LanguageProbeRequest,
        probe: Callable[[LanguageProbeRequest], LanguageProbeResult],
        *,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._request = request
        self._probe = probe

    def run(self) -> None:
        if self.isInterruptionRequested():
            return
        try:
            result = self._probe(self._request)
            if not isinstance(result, (LanguageProbeResult, _CanonicalLanguageProbeResult)):
                raise TypeError("probe_language must return LanguageProbeResult")
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.probe_failed.emit(exc)
            return
        if not self.isInterruptionRequested():
            self.result_ready.emit(result)


class _StartupController:
    """Coordinate introduction interaction without owning domain resolution."""

    __slots__ = (
        "__weakref__",
        "_application",
        "_candidate_choices",
        "_candidate_id",
        "_closed",
        "_generation",
        "_last_path",
        "_rgl_root",
        "_main_runtime",
        "_phase",
        "_selected_path",
        "_services",
        "_started",
        "_window",
        "_worker",
    )

    def __init__(
        self,
        application: object,
        window: IntroductionWindow,
        services: StartupServices,
    ) -> None:
        if not isinstance(window, IntroductionWindow):
            raise TypeError("window must be an IntroductionWindow")
        if not isinstance(services, StartupServices):
            raise TypeError("services must be StartupServices")
        self._application = application
        self._window = window
        self._services = services
        self._phase = StartupPhase.READY
        self._last_path: Path | None = None
        self._rgl_root: Path | None = getattr(window, "rgl_root", None)
        self._selected_path: Path | None = None
        self._candidate_id: str | None = None
        self._candidate_choices: dict[str, LanguageCandidatePresentation] = {}
        self._worker: _ProbeThread | None = None
        self._generation = 0
        self._main_runtime: MainGuiRuntime | None = None
        self._started = False
        self._closed = False
        self._connect()

    @property
    def main_runtime(self) -> MainGuiRuntime | None:
        return self._main_runtime

    def start(self) -> None:
        if self._closed:
            raise RuntimeError("startup runtime is closed")
        if self._started:
            return
        self._started = True
        try:
            remembered = self._services.load_last_selected_path()
            self._last_path = remembered
        except Exception as exc:
            self._last_path = None
            self._window.show_exception(self._error_from_exception(exc))

        if self._services.load_rgl_root is not None:
            try:
                remembered_rgl_root = self._services.load_rgl_root()
                if remembered_rgl_root is not None:
                    self._rgl_root = _normalize_language_selection(remembered_rgl_root)
                    self._window.set_rgl_root(self._rgl_root)
            except Exception as exc:
                self._window.show_exception(self._error_from_exception(exc))

        if self._last_path is not None:
            self._publish(
                "Default or remembered language path is ready. "
                "Use Open last language to continue."
            )
        else:
            self._publish("Choose a GF language directory or a .gf file.")

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._phase = StartupPhase.CLOSING
        self._publish("Closing GF Wordbench…")

        worker = self._worker
        self._worker = None
        if worker is not None and worker.isRunning():
            worker.requestInterruption()
            if not worker.wait(_PROBE_SHUTDOWN_WAIT_MS):
                worker.result_ready.disconnect()
                worker.probe_failed.disconnect()
        if self._main_runtime is not None:
            try:
                self._main_runtime.shutdown()
            finally:
                self._main_runtime = None
        self._window.allow_close()
        self._window.close()
        self._phase = StartupPhase.CLOSED

    def _connect(self) -> None:
        self._window.open_last_requested.connect(self._open_last)
        self._window.choose_directory_requested.connect(self._choose_directory)
        self._window.choose_file_requested.connect(self._choose_file)
        self._window.configure_environment_requested.connect(self._configure_environment)
        self._window.candidate_requested.connect(self._choose_candidate)
        self._window.quit_requested.connect(self._quit)

    @Slot()
    def _open_last(self) -> None:
        if self._last_path is None:
            self._publish("No remembered language path is available.")
            return
        self._selected_path = self._last_path
        self._candidate_id = None
        self._candidate_choices.clear()
        self._begin_probe(from_remembered=True)

    @Slot()
    def _choose_directory(self) -> None:
        if not self._can_choose_path():
            return
        self._phase = StartupPhase.SELECTING
        self._publish("Choose a GF language directory.")
        selected = self._window.choose_language_directory()
        if selected is None:
            self._phase = StartupPhase.READY
            self._publish("Language selection cancelled.")
            return
        self._selected_path = selected
        self._candidate_id = None
        self._candidate_choices.clear()
        self._begin_probe(from_remembered=False)

    @Slot()
    def _choose_file(self) -> None:
        if not self._can_choose_path():
            return
        self._phase = StartupPhase.SELECTING
        self._publish("Choose a GF source file.")
        selected = self._window.choose_gf_file()
        if selected is None:
            self._phase = StartupPhase.READY
            self._publish("Language selection cancelled.")
            return
        self._selected_path = selected
        self._candidate_id = None
        self._candidate_choices.clear()
        self._begin_probe(from_remembered=False)

    @Slot(str)
    def _choose_candidate(self, candidate_id: str) -> None:
        if self._phase is not StartupPhase.NEEDS_USER_INPUT:
            return
        _require_text(candidate_id, field="candidate_id", maximum=512)
        if candidate_id not in self._candidate_choices:
            self._publish("The selected language candidate is no longer available.")
            return
        self._candidate_id = candidate_id
        self._begin_probe(from_remembered=False)

    @Slot()
    def _configure_environment(self) -> None:
        try:
            if self._services.configure_environment is not None:
                self._services.configure_environment(self._window)
                return
            selected = self._window.choose_rgl_root()
            if selected is None:
                return
            self._rgl_root = _normalize_language_selection(selected)
            self._window.set_rgl_root(self._rgl_root)
            self._window.dialog_service.information(
                "RGL dependency configured",
                (
                    "The selected RGL checkout will be used as the dependency root "
                    "for language resolution. External GF projects may remain "
                    "outside the RGL checkout."
                ),
            )
            if self._selected_path is not None:
                self._phase = StartupPhase.READY
                self._publish("RGL dependency configured. Retrying language resolution…")
                self._begin_probe(from_remembered=False)
        except Exception as exc:
            self._window.show_exception(self._error_from_exception(exc))

    @Slot()
    def _quit(self) -> None:
        self.shutdown()
        quit_method = getattr(self._application, "quit", None)
        if callable(quit_method):
            quit_method()

    def _begin_probe(self, *, from_remembered: bool) -> None:
        if self._closed or self._selected_path is None:
            return
        if self._worker is not None and self._worker.isRunning():
            return

        candidate = (
            self._candidate_choices.get(self._candidate_id)
            if self._candidate_id is not None
            else None
        )
        request = _build_probe_request(
            self._selected_path,
            candidate=candidate,
            explicit_rgl_root=self._rgl_root,
        )
        self._generation += 1
        generation = self._generation
        self._phase = StartupPhase.PROBING
        self._publish(f"Resolving language from {self._selected_path}…")

        worker = _ProbeThread(
            request,
            self._services.probe_language,
            parent=self._window,
        )
        self._worker = worker
        worker.result_ready.connect(
            lambda result, generation=generation, remembered=from_remembered: (
                self._handle_probe_result(generation, remembered, result)
            )
        )
        worker.probe_failed.connect(
            lambda exc, generation=generation: self._handle_probe_failure(
                generation,
                exc,
            )
        )
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _handle_probe_result(
        self,
        generation: int,
        from_remembered: bool,
        result: object,
    ) -> None:
        if self._closed or generation != self._generation:
            return
        self._worker = None
        if not isinstance(result, (LanguageProbeResult, _CanonicalLanguageProbeResult)):
            self._handle_probe_failure(
                generation,
                TypeError("probe_language returned an invalid result"),
            )
            return

        view = _project_probe_result(result)
        self._candidate_choices = {
            candidate.candidate_id: candidate for candidate in view.candidates
        }
        self._window.show_probe_result(view)

        if (
            result.status is LanguageProbeStatus.UNSUPPORTED_LAYOUT
            and self._rgl_root is None
            and _probe_has_diagnostic_code(result, "GF-WB-PATH-253")
        ):
            self._phase = StartupPhase.SELECTING
            self._publish(
                "This external GF project needs an explicit RGL dependency root."
            )
            selected_rgl_root = self._window.choose_rgl_root()
            if selected_rgl_root is None:
                self._phase = StartupPhase.FAILED
                self._publish(
                    "RGL dependency selection cancelled. Configure the RGL dependency "
                    "and retry the language selection."
                )
                return
            self._rgl_root = _normalize_language_selection(selected_rgl_root)
            self._window.set_rgl_root(self._rgl_root)
            self._phase = StartupPhase.READY
            self._publish(
                "RGL dependency configured. Retrying language resolution…"
            )
            self._begin_probe(from_remembered=from_remembered)
            return

        if result.status is LanguageProbeStatus.RESOLVED:
            self._phase = StartupPhase.RESOLVED
            self._publish("Language resolved. Opening GF Wordbench…")
            self._compose_main_runtime(result)
            return

        if result.status is LanguageProbeStatus.NEEDS_USER_INPUT:
            self._phase = StartupPhase.NEEDS_USER_INPUT
            self._publish("Choose one exact candidate to continue.")
            return

        if from_remembered and self._services.clear_last_selected_path is not None:
            try:
                self._services.clear_last_selected_path()
                self._last_path = None
            except Exception as exc:
                self._window.show_exception(self._error_from_exception(exc))

        self._phase = StartupPhase.FAILED
        self._publish(_failure_message(result.status))

    def _handle_probe_failure(self, generation: int, exc: object) -> None:
        if self._closed or generation != self._generation:
            return
        self._worker = None
        self._phase = StartupPhase.FAILED
        exception = exc if isinstance(exc, Exception) else RuntimeError(str(exc))
        self._window.show_exception(self._error_from_exception(exception))
        self._publish("Language resolution failed. Choose a path and retry.")

    def _compose_main_runtime(
        self,
        result: LanguageProbeResult | _CanonicalLanguageProbeResult,
    ) -> None:
        if result.context is None or self._selected_path is None:
            self._handle_probe_failure(
                self._generation,
                RuntimeError("resolved probe result is incomplete"),
            )
            return
        self._phase = StartupPhase.COMPOSING
        self._publish("Composing the language runtime…")
        try:
            context = _require_canonical_context(result.context)
            runtime = self._services.build_main_runtime(
                self._application,
                context,
            )
            _validate_main_runtime(runtime)
        except Exception as exc:
            self._handle_probe_failure(self._generation, exc)
            return

        if self._services.remember_selected_path is not None:
            try:
                self._services.remember_selected_path(self._selected_path)
                self._last_path = self._selected_path
            except Exception as exc:
                self._window.dialog_service.warning(
                    "Language opened with a state warning",
                    "The language was resolved, but its path could not be remembered.",
                    details=self._error_from_exception(exc).details_text(),
                )

        if self._rgl_root is not None and self._services.remember_rgl_root is not None:
            try:
                self._services.remember_rgl_root(self._rgl_root)
            except Exception as exc:
                self._window.dialog_service.warning(
                    "Language opened with a state warning",
                    "The language was resolved, but its RGL dependency root could not be remembered.",
                    details=self._error_from_exception(exc).details_text(),
                )

        self._candidate_id = None
        self._candidate_choices.clear()
        self._main_runtime = runtime
        switch_signal = getattr(runtime.window, "language_switch_requested", None)
        connect = getattr(switch_signal, "connect", None)
        if callable(connect):
            connect(self._switch_language)
        self._phase = StartupPhase.RUNNING
        self._publish("Language runtime ready.")
        self._window.hide()
        _show_main_window(runtime.window)

    @Slot()
    def _switch_language(self) -> None:
        """Dispose the active runtime and return to explicit language selection."""

        if self._closed or self._phase is not StartupPhase.RUNNING:
            return
        if self._services.has_active_run is not None:
            try:
                active = self._services.has_active_run()
                if type(active) is not bool:
                    raise TypeError("has_active_run must return a bool")
            except Exception as exc:
                self._window.show_exception(self._error_from_exception(exc))
                return
            if active:
                self._publish(
                    "Finish or cancel the active validation run before switching languages."
                )
                return
        runtime = self._main_runtime
        self._main_runtime = None
        if runtime is not None:
            window = runtime.window
            hide = getattr(window, "hide", None)
            if callable(hide):
                hide()
            try:
                runtime.shutdown()
            except Exception as exc:
                self._window.show_exception(self._error_from_exception(exc))
        self._selected_path = None
        self._candidate_id = None
        self._candidate_choices.clear()
        self._phase = StartupPhase.READY
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()
        self._publish("Choose another GF language directory or .gf file.")

    def _error_from_exception(self, exc: Exception) -> ErrorPresentation:
        if self._services.error_from_exception is not None:
            try:
                value = self._services.error_from_exception(exc)
                if isinstance(value, ErrorPresentation):
                    return value
            except Exception:
                pass
        return error_presentation_from_exception(
            exc,
            summary="GF Wordbench could not resolve the selected language.",
            recommended_action=(
                "Review the details, select a valid GF language directory or .gf file, and retry."
            ),
        )

    def _publish(self, message: str) -> None:
        busy = self._phase in {
            StartupPhase.PROBING,
            StartupPhase.COMPOSING,
            StartupPhase.CLOSING,
        }
        can_choose = not busy and self._phase not in {
            StartupPhase.RUNNING,
            StartupPhase.CLOSED,
        }
        snapshot = StartupSnapshot(
            phase=self._phase,
            last_selected_path=self._last_path,
            selected_path=self._selected_path,
            status_message=message,
            can_open_last=(
                self._last_path is not None
                and can_choose
                and self._phase is not StartupPhase.NEEDS_USER_INPUT
            ),
            can_choose_path=can_choose,
            can_choose_candidate=self._phase is StartupPhase.NEEDS_USER_INPUT,
            can_quit=self._phase is not StartupPhase.CLOSED,
        )
        self._window.show_snapshot(snapshot)

    def _can_choose_path(self) -> bool:
        return not self._closed and self._phase not in {
            StartupPhase.PROBING,
            StartupPhase.COMPOSING,
            StartupPhase.RUNNING,
            StartupPhase.CLOSING,
            StartupPhase.CLOSED,
        }


class PathResolvedGuiRuntime:
    """Explicitly started GUI surface that owns the language runtime lifecycle."""

    __slots__ = ("_controller", "_window")

    def __init__(
        self,
        application: object,
        services: StartupServices,
        *,
        window: IntroductionWindow | None = None,
    ) -> None:
        if application is None:
            raise TypeError("application must not be None")
        if not isinstance(services, StartupServices):
            raise TypeError("services must be StartupServices")
        self._window = window or IntroductionWindow()
        self._controller = _StartupController(
            application,
            self._window,
            services,
        )

    @property
    def window(self) -> IntroductionWindow:
        return self._window

    def start(self) -> None:
        """Load startup state without selecting or probing a language."""

        self._controller.start()

    def shutdown(self) -> None:
        self._controller.shutdown()


def _wordbench_workspace_root() -> Path:
    """Return the repository root that owns the desktop application state."""

    # startup.py -> gui -> entrypoints -> gf_wordbench -> src -> repository root
    return Path(__file__).resolve().parents[4]


def _default_workspace_paths(
    workspace_root: Path,
) -> tuple[Path | None, Path | None]:
    """Resolve bounded local defaults for the standard Grammatical_Framework layout.

    GF Wordbench remains portable: no drive letter or user-specific absolute path is
    embedded in the application.  When the repository is installed as
    ``<suite>/GF_Wordbench/GF_Wordbench``, the two sibling development checkouts
    used by this workspace are offered as convenience defaults if they actually
    exist.  Missing paths fail closed to ``None`` and the normal chooser remains
    available.
    """

    if not isinstance(workspace_root, Path):
        raise TypeError("workspace_root must be a pathlib.Path")
    root = workspace_root.resolve(strict=False)
    if root.name == "GF_Wordbench" and root.parent.name == "GF_Wordbench":
        suite_root = root.parent.parent
    else:
        suite_root = root.parent

    language = (
        suite_root
        / "Grammatical_Framework-Albanian"
        / "AlbanianSQI"
        / "GF"
        / "lib"
        / "src"
        / "albanian"
    ).resolve(strict=False)
    rgl_root = (suite_root / "gf-rgl").resolve(strict=False)

    language_default = (
        language
        if language.is_dir() and any(language.glob("*.gf"))
        else None
    )
    rgl_default = (
        rgl_root
        if rgl_root.is_dir() and (rgl_root / "src").is_dir()
        else None
    )
    return language_default, rgl_default


def _build_default_startup_services(
    *,
    workspace_root: Path | None = None,
) -> StartupServices:
    """Compose the concrete services owned by the canonical GUI startup edge.

    Startup composition remains inert: remembered/default paths are only displayed
    until the user explicitly chooses ``Open last language``.  Successful choices
    are persisted in the existing application-state repository.  A fresh checkout
    in the standard ``Grammatical_Framework`` workspace receives bounded Albanian
    and ``gf-rgl`` convenience defaults, without hard-coding a Windows drive path.
    """

    from dataclasses import replace

    from gf_wordbench.projects.languages.public import probe_language_path
    from gf_wordbench.state.repository import StateRepository

    state_root = (
        _wordbench_workspace_root()
        if workspace_root is None
        else workspace_root.resolve(strict=False)
    )
    repository = StateRepository(workspace_root=state_root)
    default_language, default_rgl_root = _default_workspace_paths(state_root)

    def probe(request: LanguageProbeRequest) -> _CanonicalLanguageProbeResult:
        if not isinstance(request, LanguageProbeRequest):
            raise TypeError("request must be LanguageProbeRequest")
        return probe_language_path(request)

    def build_main_runtime(
        application: object,
        context: ResolvedLanguageContext,
    ) -> MainGuiRuntime:
        from gf_wordbench.entrypoints.gui.runtime import build_main_runtime as build_runtime

        return build_runtime(application, context)

    def _existing_remembered_path(
        value: str | None,
        fallback: Path | None,
        *,
        require_rgl: bool = False,
    ) -> Path | None:
        if value:
            candidate = Path(value).expanduser().resolve(strict=False)
            valid = candidate.is_dir() or candidate.is_file()
            if require_rgl:
                valid = candidate.is_dir() and (
                    (candidate / "src").is_dir()
                    or candidate.name.casefold() == "src"
                )
            if valid:
                return candidate
        return fallback

    def load_last_selected_path() -> Path | None:
        state = repository.load()
        return _existing_remembered_path(
            state.environment.last_selected_language_path,
            default_language,
        )

    def load_rgl_root() -> Path | None:
        state = repository.load()
        return _existing_remembered_path(
            state.environment.last_rgl_root,
            default_rgl_root,
            require_rgl=True,
        )

    def remember_selected_path(path: Path) -> None:
        normalized = _normalize_language_selection(path)
        state = repository.load()
        environment = replace(
            state.environment,
            last_selected_language_path=str(normalized),
        )
        repository.save(replace(state, environment=environment))

    def clear_last_selected_path() -> None:
        state = repository.load()
        environment = replace(
            state.environment,
            last_selected_language_path=None,
        )
        repository.save(replace(state, environment=environment))

    def remember_rgl_root(path: Path) -> None:
        normalized = _normalize_language_selection(path)
        state = repository.load()
        environment = replace(
            state.environment,
            last_rgl_root=str(normalized),
        )
        repository.save(replace(state, environment=environment))

    return StartupServices(
        probe_language=probe,
        build_main_runtime=build_main_runtime,
        load_last_selected_path=load_last_selected_path,
        remember_selected_path=remember_selected_path,
        clear_last_selected_path=clear_last_selected_path,
        load_rgl_root=load_rgl_root,
        remember_rgl_root=remember_rgl_root,
        error_from_exception=error_presentation_from_exception,
    )


def build_startup_runtime(
    application: object,
    argv: tuple[str, ...] = (),
    *,
    services: StartupServices | None = None,
    window: IntroductionWindow | None = None,
) -> PathResolvedGuiRuntime:
    """Build the inert GUI startup runtime.

    The returned runtime does not load remembered state, probe a language, or show
    a window until its explicit :meth:`PathResolvedGuiRuntime.start` method is called
    by the GUI entrypoint. ``argv`` is accepted as part of the canonical startup
    contract and intentionally remains presentation-neutral here.
    """

    if not isinstance(argv, tuple) or any(not isinstance(item, str) for item in argv):
        raise TypeError("argv must be a tuple of strings")
    if services is None:
        services = _build_default_startup_services()
    if not isinstance(services, StartupServices):
        raise TypeError("services must be StartupServices")
    return PathResolvedGuiRuntime(
        application,
        services,
        window=window,
    )


# Bootstrap validates the stable application-facing signature. ``window`` is a
# deliberately hidden test/presentation injection seam and is not part of that
# public contract.
build_startup_runtime.__signature__ = Signature(  # type: ignore[attr-defined]
    parameters=(
        Parameter("application", Parameter.POSITIONAL_OR_KEYWORD),
        Parameter(
            "argv",
            Parameter.POSITIONAL_OR_KEYWORD,
            default=(),
        ),
        Parameter(
            "services",
            Parameter.KEYWORD_ONLY,
            default=None,
        ),
    )
)


def _project_probe_result(
    result: LanguageProbeResult | _CanonicalLanguageProbeResult,
) -> _StartupProbeView:
    """Project one canonical or GUI-compatible probe result."""

    if not isinstance(result, (LanguageProbeResult, _CanonicalLanguageProbeResult)):
        raise TypeError("result must be a LanguageProbeResult")
    supplied = getattr(result, "presentation", None)
    presentation = (
        supplied
        if supplied is not None
        else (_project_resolved_context(result.context) if result.context is not None else None)
    )
    return _StartupProbeView(
        status=result.status,
        context=result.context,
        presentation=presentation,
        diagnostics=tuple(_project_diagnostic(diagnostic) for diagnostic in result.diagnostics),
        candidates=_project_candidates(result),
    )


def _require_resolved_context_contract(context: object) -> None:
    """Validate the stable structural surface consumed by GUI startup."""

    required = (
        "language_key",
        "language_directory",
        "rgl_source_root",
        "selected_path",
        "selected_path_kind",
        "module_suffix",
        "focused_target",
        "available_entrypoints",
        "source_inventory",
        "capability_statuses",
    )
    missing = tuple(name for name in required if not hasattr(context, name))
    if missing:
        raise TypeError(
            "context must satisfy the ResolvedLanguageContext contract; "
            f"missing: {', '.join(missing)}"
        )


def _entrypoint_path(candidate: object) -> Path:
    if isinstance(candidate, Path):
        return candidate
    file_path = getattr(candidate, "file_path", None)
    if isinstance(file_path, Path):
        return file_path
    raise TypeError("available_entrypoints must contain paths or path candidates")


def _require_canonical_context(context: object) -> ResolvedLanguageContext:
    if not isinstance(context, ResolvedLanguageContext):
        raise TypeError("resolved probe context must be ResolvedLanguageContext")
    return context


def _required_attribute(value: object, name: str) -> object:
    try:
        return object.__getattribute__(value, name)
    except AttributeError as exc:
        raise TypeError(f"context is missing required attribute {name!r}") from exc


def _string_attribute(value: object, name: str) -> str:
    result = _required_attribute(value, name)
    if not isinstance(result, str):
        raise TypeError(f"{name} must be a string")
    return result


def _optional_string_attribute(value: object, name: str) -> str | None:
    result = _required_attribute(value, name)
    if result is not None and not isinstance(result, str):
        raise TypeError(f"{name} must be a string or None")
    return result


def _path_attribute(value: object, name: str) -> Path:
    result = _required_attribute(value, name)
    if not isinstance(result, Path):
        raise TypeError(f"{name} must be a pathlib.Path")
    return result


def _optional_path_attribute(value: object, name: str) -> Path | None:
    result = _required_attribute(value, name)
    if result is not None and not isinstance(result, Path):
        raise TypeError(f"{name} must be a pathlib.Path or None")
    return result


def _iterable_attribute(value: object, name: str) -> tuple[object, ...]:
    result = _required_attribute(value, name)
    if not isinstance(result, Iterable) or isinstance(
        result,
        (str, bytes, bytearray),
    ):
        raise TypeError(f"{name} must be iterable")
    return tuple(result)


def _enum_value(value: object, *, field: str) -> str:
    raw = _required_attribute(value, "value")
    if not isinstance(raw, str):
        raise TypeError(f"{field}.value must be a string")
    return raw


def _capability_available(status: object) -> bool:
    value = _required_attribute(status, "available")
    if type(value) is not bool:
        raise TypeError("capability status available must be a bool")
    return value


def _capability_value(status: object) -> str:
    capability = _required_attribute(status, "capability")
    return _enum_value(capability, field="capability")


def _candidate_suffixes(candidate: object | None) -> tuple[str, ...]:
    if candidate is None:
        return ()
    values = _iterable_attribute(candidate, "module_suffixes")
    if any(not isinstance(value, str) for value in values):
        raise TypeError("module_suffixes must contain strings")
    return tuple(value for value in values if isinstance(value, str))


def _candidate_entrypoints(
    candidate: object | None,
) -> tuple[LanguageModuleCandidate, ...]:
    if candidate is None:
        return ()
    values = _iterable_attribute(candidate, "entrypoint_candidates")
    if any(not isinstance(value, LanguageModuleCandidate) for value in values):
        raise TypeError("entrypoint_candidates must contain LanguageModuleCandidate values")
    return tuple(value for value in values if isinstance(value, LanguageModuleCandidate))


def _project_resolved_context(
    context: object,
) -> ResolvedLanguagePresentation:
    _require_resolved_context_contract(context)
    selected_path_kind = _required_attribute(context, "selected_path_kind")
    available_entrypoints = _iterable_attribute(context, "available_entrypoints")
    source_inventory = _iterable_attribute(context, "source_inventory")
    capability_statuses = _iterable_attribute(context, "capability_statuses")
    return ResolvedLanguagePresentation(
        language_key=_string_attribute(context, "language_key"),
        language_directory=_path_attribute(context, "language_directory"),
        rgl_source_root=_path_attribute(context, "rgl_source_root"),
        selected_path=_path_attribute(context, "selected_path"),
        selected_path_kind=_enum_value(selected_path_kind, field="selected_path_kind"),
        module_suffix=_optional_string_attribute(context, "module_suffix"),
        focused_target=_optional_path_attribute(context, "focused_target"),
        available_entrypoints=tuple(
            _entrypoint_path(candidate) for candidate in available_entrypoints
        ),
        source_count=len(source_inventory),
        capabilities=tuple(
            _capability_value(status)
            for status in capability_statuses
            if _capability_available(status)
        ),
    )


def _project_diagnostic(
    diagnostic: LanguageProbeDiagnostic,
) -> StartupDiagnostic:
    if not isinstance(diagnostic, LanguageProbeDiagnostic):
        raise TypeError("diagnostic must be a LanguageProbeDiagnostic")
    severity = {
        LanguageProbeSeverity.INFO: StartupDiagnosticSeverity.INFO,
        LanguageProbeSeverity.WARNING: StartupDiagnosticSeverity.WARNING,
        LanguageProbeSeverity.ERROR: StartupDiagnosticSeverity.ERROR,
    }[diagnostic.severity]
    detail_parts = [
        f"Stage: {diagnostic.stage}",
        f"Subject: {diagnostic.subject}",
    ]
    if diagnostic.relevant_path is not None:
        detail_parts.append(f"Path: {diagnostic.relevant_path}")
    if diagnostic.technical_detail:
        detail_parts.append(diagnostic.technical_detail)
    return StartupDiagnostic(
        code=diagnostic.code,
        severity=severity,
        message=_bounded_text(diagnostic.message, _MAX_TEXT),
        detail=_bounded_text("\n".join(detail_parts), _MAX_DETAILS),
        remediation=_bounded_text(diagnostic.remediation, _MAX_TEXT),
    )


def _project_candidates(
    result: LanguageProbeResult | _CanonicalLanguageProbeResult,
) -> tuple[LanguageCandidatePresentation, ...]:
    if result.status is not LanguageProbeStatus.NEEDS_USER_INPUT:
        return ()

    candidate = result.candidate
    requested = tuple(
        choice for diagnostic in result.diagnostics for choice in diagnostic.candidate_choices
    )
    suffixes = _candidate_suffixes(candidate)
    entrypoints = _candidate_entrypoints(candidate)

    projected: list[LanguageCandidatePresentation] = []
    seen: set[str] = set()

    def add_suffix(suffix: str) -> None:
        key = f"module_suffix:{suffix}"
        if key in seen:
            return
        seen.add(key)
        projected.append(
            LanguageCandidatePresentation(
                candidate_id=key,
                label=f"Module suffix: {suffix}",
                detail=(f"Resolve the selected language using the exact module suffix {suffix!r}."),
                module_suffix_choice=suffix,
            )
        )

    def add_entrypoint(path: Path) -> None:
        key = f"entrypoint:{path.as_posix()}"
        if key in seen:
            return
        seen.add(key)
        projected.append(
            LanguageCandidatePresentation(
                candidate_id=key,
                label=f"Entrypoint: {path.name}",
                path=path,
                detail=f"Resolve the language using {path}.",
                entrypoint_choice=path,
            )
        )

    for choice in requested:
        if choice in suffixes:
            add_suffix(choice)
            continue
        matched = next(
            (
                item
                for item in entrypoints
                if choice
                in {
                    str(item.file_path),
                    item.file_path.as_posix(),
                    item.file_path.name,
                    item.module_name,
                }
            ),
            None,
        )
        if matched is not None:
            add_entrypoint(matched.file_path)

    if not projected:
        for suffix in suffixes:
            add_suffix(suffix)
    if not projected:
        for entrypoint in entrypoints:
            add_entrypoint(entrypoint.file_path)

    if len(projected) > _MAX_CANDIDATES:
        raise ValueError(f"probe returned more than {_MAX_CANDIDATES} GUI candidates")
    return tuple(projected)


def _build_probe_request(
    selected_path: Path,
    *,
    candidate: LanguageCandidatePresentation | None,
    explicit_rgl_root: Path | None = None,
) -> LanguageProbeRequest:
    selected = _normalize_language_selection(selected_path)
    rgl_root = (
        None
        if explicit_rgl_root is None
        else _normalize_language_selection(explicit_rgl_root)
    )
    if candidate is None:
        return LanguageProbeRequest(
            selected_path=selected,
            explicit_rgl_root=rgl_root,
        )
    return LanguageProbeRequest(
        selected_path=selected,
        explicit_rgl_root=rgl_root,
        module_suffix_choice=candidate.module_suffix_choice,
        entrypoint_choice=candidate.entrypoint_choice,
    )


def _probe_has_diagnostic_code(
    result: LanguageProbeResult | _CanonicalLanguageProbeResult,
    code: str,
) -> bool:
    """Return whether a structured language-probe diagnostic has ``code``."""

    _require_text(code, field="code", maximum=128)
    diagnostics = getattr(result, "diagnostics", ())
    return any(getattr(item, "code", None) == code for item in diagnostics)


def _bounded_text(value: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    if len(value) <= maximum:
        return value
    marker = "\n… [truncated for startup presentation]"
    return value[: max(0, maximum - len(marker))] + marker


def _normalize_language_selection(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    return path.expanduser().resolve(strict=False)


def _require_switchable_runtime(runtime: object) -> SwitchableRuntime:
    if not isinstance(runtime, SwitchableRuntime):
        raise TypeError("build_runtime must return an object providing shutdown()")
    return runtime


def _validate_main_runtime(runtime: object) -> None:
    if not isinstance(runtime, MainGuiRuntime):
        raise TypeError("build_main_runtime must return an object satisfying MainGuiRuntime")
    if not callable(getattr(runtime.window, "show", None)):
        raise TypeError("main runtime window must provide show()")
    if not callable(getattr(runtime, "shutdown", None)):
        raise TypeError("main runtime must provide shutdown()")


def _show_main_window(window: object) -> None:
    show = getattr(window, "show", None)
    if not callable(show):
        raise TypeError("main runtime window must provide show()")
    show()
    raise_ = getattr(window, "raise_", None)
    if callable(raise_):
        raise_()
    activate = getattr(window, "activateWindow", None)
    if callable(activate):
        activate()


def _failure_message(status: LanguageProbeStatus) -> str:
    messages = {
        LanguageProbeStatus.INVALID_SELECTION: (
            "The selected path is not a valid GF language source."
        ),
        LanguageProbeStatus.UNSUPPORTED_LAYOUT: (
            "The selected source layout is not supported automatically."
        ),
        LanguageProbeStatus.CAPABILITY_UNAVAILABLE: (
            "The language was found, but a requested capability is unavailable."
        ),
        LanguageProbeStatus.INTERNAL_ERROR: (
            "Language resolution failed because of an internal error."
        ),
        LanguageProbeStatus.NEEDS_USER_INPUT: ("Additional input is required."),
        LanguageProbeStatus.RESOLVED: "Language resolved.",
    }
    return messages[status]


def _require_text(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    if len(value) > maximum:
        raise ValueError(f"{field} must contain at most {maximum} characters")
    return value
