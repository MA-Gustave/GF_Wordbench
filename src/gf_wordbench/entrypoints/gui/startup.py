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

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Generic, Protocol, TypeVar, runtime_checkable

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
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

__all__ = (
    "IntroductionWindow",
    "LanguageCandidatePresentation",
    "LanguageProbeDisposition",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "PathResolvedGuiRuntime",
    "ResolvedLanguagePresentation",
    "StartupDiagnostic",
    "StartupDiagnosticSeverity",
    "StartupPhase",
    "StartupServices",
    "StartupSnapshot",
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


@unique
class LanguageProbeDisposition(StrEnum):
    """Typed outcome returned by the language-probe application service."""

    RESOLVED = "resolved"
    NEEDS_USER_INPUT = "needs_user_input"
    INVALID_SELECTION = "invalid_selection"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    INTERNAL_ERROR = "internal_error"


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
    """One exact choice returned when language resolution is ambiguous."""

    candidate_id: str
    label: str
    path: Path | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, field="candidate_id", maximum=512)
        _require_text(self.label, field="label", maximum=1_024)
        if self.path is not None and not isinstance(self.path, Path):
            raise TypeError("path must be a pathlib.Path or None")
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
        if self.focused_target is not None and not isinstance(
            self.focused_target, Path
        ):
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
class LanguageProbeRequest:
    """Explicit input to the path-resolved language probe."""

    selected_path: Path
    candidate_id: str | None = None
    explicit_rgl_root: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.selected_path, Path):
            raise TypeError("selected_path must be a pathlib.Path")
        if self.candidate_id is not None:
            _require_text(
                self.candidate_id,
                field="candidate_id",
                maximum=512,
            )
        if self.explicit_rgl_root is not None and not isinstance(
            self.explicit_rgl_root, Path
        ):
            raise TypeError("explicit_rgl_root must be a pathlib.Path or None")


@dataclass(frozen=True, slots=True)
class LanguageProbeResult(Generic[ContextT]):
    """Structured result returned by the language-probe application service."""

    disposition: LanguageProbeDisposition
    context: ContextT | None = None
    presentation: ResolvedLanguagePresentation | None = None
    diagnostics: tuple[StartupDiagnostic, ...] = ()
    candidates: tuple[LanguageCandidatePresentation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, LanguageProbeDisposition):
            raise TypeError("disposition must be a LanguageProbeDisposition")
        if self.presentation is not None and not isinstance(
            self.presentation, ResolvedLanguagePresentation
        ):
            raise TypeError(
                "presentation must be a ResolvedLanguagePresentation or None"
            )
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("diagnostics must be a tuple")
        if any(not isinstance(item, StartupDiagnostic) for item in self.diagnostics):
            raise TypeError("diagnostics must contain StartupDiagnostic values")
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates must be a tuple")
        if len(self.candidates) > _MAX_CANDIDATES:
            raise ValueError(f"candidates must contain at most {_MAX_CANDIDATES} items")
        if any(
            not isinstance(item, LanguageCandidatePresentation)
            for item in self.candidates
        ):
            raise TypeError(
                "candidates must contain LanguageCandidatePresentation values"
            )

        if self.disposition is LanguageProbeDisposition.RESOLVED:
            if self.context is None:
                raise ValueError("a resolved result must include context")
            if self.presentation is None:
                raise ValueError("a resolved result must include presentation")
            if self.candidates:
                raise ValueError("a resolved result must not include candidates")
        elif self.context is not None:
            raise ValueError("an unresolved result must not include context")

        if self.disposition is LanguageProbeDisposition.NEEDS_USER_INPUT:
            if not self.candidates:
                raise ValueError(
                    "a needs-user-input result must include exact candidates"
                )
        elif self.candidates:
            raise ValueError(
                "candidates are permitted only for needs-user-input results"
            )


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


@dataclass(frozen=True, slots=True)
class StartupServices(Generic[ContextT]):
    """Injected application services required by interactive startup."""

    probe_language: Callable[[LanguageProbeRequest], LanguageProbeResult[ContextT]]
    build_main_runtime: Callable[[object, ContextT], MainGuiRuntime]
    load_last_selected_path: Callable[[], Path | None]
    remember_selected_path: Callable[[Path], None] | None = None
    clear_last_selected_path: Callable[[], None] | None = None
    configure_environment: Callable[[object], None] | None = None
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
            "configure_environment",
            "error_from_exception",
        )
        for field_name in required:
            if not callable(getattr(self, field_name)):
                raise TypeError(f"{field_name} must be callable")
        for field_name in optional:
            value = getattr(self, field_name)
            if value is not None and not callable(value):
                raise TypeError(f"{field_name} must be callable or None")


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

    def show_snapshot(self, snapshot: StartupSnapshot) -> None:
        if not isinstance(snapshot, StartupSnapshot):
            raise TypeError("snapshot must be a StartupSnapshot")
        self._last_selected_path = snapshot.last_selected_path
        self._selected_path = snapshot.selected_path
        self._last_path_value.setText(
            str(snapshot.last_selected_path)
            if snapshot.last_selected_path is not None
            else "None"
        )
        self._selected_path_value.setText(
            str(snapshot.selected_path)
            if snapshot.selected_path is not None
            else "None"
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

    def show_probe_result(self, result: LanguageProbeResult[object]) -> None:
        if not isinstance(result, LanguageProbeResult):
            raise TypeError("result must be a LanguageProbeResult")
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
            "Wordbench will resolve the language context before opening the main window.",
            root,
        )
        explanation.setWordWrap(True)
        explanation.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(explanation)

        path_frame = QFrame(root)
        path_frame.setFrameShape(QFrame.Shape.StyledPanel)
        path_layout = QVBoxLayout(path_frame)

        last_label = QLabel("Last selected language path", path_frame)
        last_label.setStyleSheet("font-weight: 600;")
        path_layout.addWidget(last_label)
        self._last_path_value = QLabel("None", path_frame)
        self._last_path_value.setWordWrap(True)
        self._last_path_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
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
        self._environment_button = QPushButton("Configure GF environment…", root)
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
        self._choose_directory_button.clicked.connect(
            self.choose_directory_requested.emit
        )
        self._choose_file_button.clicked.connect(self.choose_file_requested.emit)
        self._environment_button.clicked.connect(
            self.configure_environment_requested.emit
        )
        self._quit_button.clicked.connect(self.quit_requested.emit)
        self._use_candidate_button.clicked.connect(self._emit_candidate)
        self._candidates.itemSelectionChanged.connect(
            self._update_candidate_button
        )
        self._candidates.itemDoubleClicked.connect(
            lambda _item: self._emit_candidate()
        )

    @Slot()
    def _update_candidate_button(self) -> None:
        self._use_candidate_button.setEnabled(
            self._candidates.currentItem() is not None
        )

    @Slot()
    def _emit_candidate(self) -> None:
        item = self._candidates.currentItem()
        if item is None:
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
                f"[{diagnostic.severity.value.upper()}] "
                f"{diagnostic.code}: {diagnostic.message}"
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
                "Entrypoints: "
                + ", ".join(path.name for path in value.available_entrypoints)
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
        probe: Callable[[LanguageProbeRequest], LanguageProbeResult[object]],
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
            if not isinstance(result, LanguageProbeResult):
                raise TypeError("probe_language must return LanguageProbeResult")
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.probe_failed.emit(exc)
            return
        if not self.isInterruptionRequested():
            self.result_ready.emit(result)


class _StartupController(Generic[ContextT]):
    """Coordinate introduction interaction without owning domain resolution."""

    __slots__ = (
        "_application",
        "_window",
        "_services",
        "_phase",
        "_last_path",
        "_selected_path",
        "_candidate_id",
        "_worker",
        "_generation",
        "_main_runtime",
        "_closed",
    )

    def __init__(
        self,
        application: object,
        window: IntroductionWindow,
        services: StartupServices[ContextT],
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
        self._selected_path: Path | None = None
        self._candidate_id: str | None = None
        self._worker: _ProbeThread | None = None
        self._generation = 0
        self._main_runtime: MainGuiRuntime | None = None
        self._closed = False
        self._connect()

    @property
    def main_runtime(self) -> MainGuiRuntime | None:
        return self._main_runtime

    def start(self) -> None:
        try:
            remembered = self._services.load_last_selected_path()
            if remembered is not None and not isinstance(remembered, Path):
                remembered = Path(str(remembered))
            self._last_path = remembered
        except Exception as exc:
            self._last_path = None
            self._window.show_exception(self._error_from_exception(exc))
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
        self._window.configure_environment_requested.connect(
            self._configure_environment
        )
        self._window.candidate_requested.connect(self._choose_candidate)
        self._window.quit_requested.connect(self._quit)

    @Slot()
    def _open_last(self) -> None:
        if self._last_path is None:
            self._publish("No remembered language path is available.")
            return
        self._selected_path = self._last_path
        self._candidate_id = None
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
        self._begin_probe(from_remembered=False)

    @Slot(str)
    def _choose_candidate(self, candidate_id: str) -> None:
        if self._phase is not StartupPhase.NEEDS_USER_INPUT:
            return
        _require_text(candidate_id, field="candidate_id", maximum=512)
        self._candidate_id = candidate_id
        self._begin_probe(from_remembered=False)

    @Slot()
    def _configure_environment(self) -> None:
        if self._services.configure_environment is None:
            self._window.dialog_service.information(
                "GF environment",
                "Environment configuration is not available in this build.",
            )
            return
        try:
            self._services.configure_environment(self._window)
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

        request = LanguageProbeRequest(
            selected_path=self._selected_path,
            candidate_id=self._candidate_id,
        )
        self._generation += 1
        generation = self._generation
        self._phase = StartupPhase.PROBING
        self._publish(f"Resolving language from {self._selected_path}…")

        worker = _ProbeThread(
            request,
            self._services.probe_language,  # type: ignore[arg-type]
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
        if not isinstance(result, LanguageProbeResult):
            self._handle_probe_failure(
                generation,
                TypeError("probe_language returned an invalid result"),
            )
            return

        self._window.show_probe_result(result)
        if result.disposition is LanguageProbeDisposition.RESOLVED:
            self._phase = StartupPhase.RESOLVED
            self._publish("Language resolved. Opening GF Wordbench…")
            self._compose_main_runtime(result)
            return

        if result.disposition is LanguageProbeDisposition.NEEDS_USER_INPUT:
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
        self._publish(_failure_message(result.disposition))

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
        result: LanguageProbeResult[ContextT],
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
            runtime = self._services.build_main_runtime(
                self._application,
                result.context,
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
                "Review the details, select a valid GF language directory or .gf "
                "file, and retry."
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
        return (
            not self._closed
            and self._phase
            not in {
                StartupPhase.PROBING,
                StartupPhase.COMPOSING,
                StartupPhase.RUNNING,
                StartupPhase.CLOSING,
                StartupPhase.CLOSED,
            }
        )


class PathResolvedGuiRuntime(Generic[ContextT]):
    """GUI runtime that owns startup and the eventual language main runtime."""

    __slots__ = ("_window", "_controller")

    def __init__(
        self,
        application: object,
        services: StartupServices[ContextT],
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
        self._controller.start()

    @property
    def window(self) -> IntroductionWindow:
        return self._window

    @property
    def main_runtime(self) -> MainGuiRuntime | None:
        return self._controller.main_runtime

    def shutdown(self) -> None:
        self._controller.shutdown()


def _validate_main_runtime(runtime: object) -> None:
    if not isinstance(runtime, MainGuiRuntime):
        raise TypeError(
            "build_main_runtime must return an object satisfying MainGuiRuntime"
        )
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


def _failure_message(disposition: LanguageProbeDisposition) -> str:
    messages = {
        LanguageProbeDisposition.INVALID_SELECTION: (
            "The selected path is not a valid GF language source."
        ),
        LanguageProbeDisposition.UNSUPPORTED_LAYOUT: (
            "The selected source layout is not supported automatically."
        ),
        LanguageProbeDisposition.CAPABILITY_UNAVAILABLE: (
            "The language was found, but a requested capability is unavailable."
        ),
        LanguageProbeDisposition.INTERNAL_ERROR: (
            "Language resolution failed because of an internal error."
        ),
        LanguageProbeDisposition.NEEDS_USER_INPUT: (
            "Additional input is required."
        ),
        LanguageProbeDisposition.RESOLVED: "Language resolved.",
    }
    return messages[disposition]


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
