"""Main-window composition for the GF Wordbench Qt entrypoint.

This module owns presentation composition and GUI intent signals. It does not
resolve configuration, execute validation stages, interpret reports, persist
application state, or call GF. Controllers bind the emitted intents to the same
application services used by the command-line entrypoint.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, TypeAlias

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.version import __version__

__all__ = (
    "CloseConfirmation",
    "MainWindow",
    "WindowPanels",
    "WindowRunState",
    "create_default_panels",
)

CloseConfirmation: TypeAlias = Callable[[QWidget], bool]
PanelFactory: TypeAlias = Callable[[QWidget], "WindowPanels"]

_APP_NAME: Final[str] = "GF Wordbench"
_READY_LABEL: Final[str] = "Ready"
_RUNNING_LABEL: Final[str] = "Running"
_CANCELLING_LABEL: Final[str] = "Cancelling"
_MINIMUM_WIDTH: Final[int] = 960
_MINIMUM_HEIGHT: Final[int] = 680
_DEFAULT_WIDTH: Final[int] = 1220
_DEFAULT_HEIGHT: Final[int] = 840


@unique
class WindowRunState(StrEnum):
    """Presentation-only active-run state."""

    READY = "ready"
    RUNNING = "running"
    CANCELLING = "cancelling"


@dataclass(frozen=True, slots=True)
class WindowPanels:
    """Widgets composed by :class:`MainWindow`.

    Panel implementations own their local presentation and expose application
    intents through their own Qt signals. The window only places and enables
    them according to the active-run policy.
    """

    project: QWidget
    validation: QWidget
    progress: QWidget
    results: QWidget
    diagnostics: QWidget
    artifacts: QWidget

    def __post_init__(self) -> None:
        for name in (
            "project",
            "validation",
            "progress",
            "results",
            "diagnostics",
            "artifacts",
        ):
            if not isinstance(getattr(self, name), QWidget):
                raise TypeError(f"{name} must be a QWidget")


def create_default_panels(parent: QWidget) -> WindowPanels:
    """Construct the canonical panel set without importing it at CLI startup."""

    from .panels.artifacts import ArtifactsPanel
    from .panels.diagnostics import DiagnosticsPanel
    from .panels.progress import ProgressPanel
    from .panels.project import ProjectPanel
    from .panels.results import ResultsPanel
    from .panels.validation import ValidationPanel

    return WindowPanels(
        project=ProjectPanel(parent),
        validation=ValidationPanel(parent),
        progress=ProgressPanel(parent),
        results=ResultsPanel(parent),
        diagnostics=DiagnosticsPanel(parent),
        artifacts=ArtifactsPanel(parent),
    )


class MainWindow(QMainWindow):
    """Canonical desktop shell for one active GF Wordbench project."""

    run_requested = Signal()
    cancel_requested = Signal()
    open_project_requested = Signal()
    test_environment_requested = Signal()
    open_last_run_requested = Signal()
    open_reports_requested = Signal()
    settings_requested = Signal()
    help_requested = Signal()
    focus_results_requested = Signal()
    close_requested = Signal(bool)

    def __init__(
        self,
        *,
        panels: WindowPanels | None = None,
        panel_factory: PanelFactory = create_default_panels,
        app_version: str = __version__,
        confirm_active_close: CloseConfirmation | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not callable(panel_factory):
            raise TypeError("panel_factory must be callable")
        if not isinstance(app_version, str) or not app_version.strip():
            raise ValueError("app_version must be a non-empty string")
        if confirm_active_close is not None and not callable(confirm_active_close):
            raise TypeError("confirm_active_close must be callable or None")

        self._app_version = app_version.strip()
        self._confirm_active_close = confirm_active_close
        self._run_state = WindowRunState.READY
        self._close_after_run = False
        self._allow_close = False
        self._close_signal_emitted = False
        self._project_name: str | None = None
        self._run_available = False

        self.setObjectName("gfWordbenchMainWindow")
        self.setMinimumSize(_MINIMUM_WIDTH, _MINIMUM_HEIGHT)
        self.resize(_DEFAULT_WIDTH, _DEFAULT_HEIGHT)

        self._create_actions()
        self._panels = panels if panels is not None else panel_factory(self)
        if not isinstance(self._panels, WindowPanels):
            raise TypeError("panel_factory must return WindowPanels")
        self._build_window()
        self._connect_actions()
        self._apply_run_state()
        self.set_last_run_available(False)
        self.set_reports_available(False)
        self.set_project_identity(None)

    @property
    def panels(self) -> WindowPanels:
        return self._panels

    @property
    def run_state(self) -> WindowRunState:
        return self._run_state

    @property
    def close_after_run(self) -> bool:
        return self._close_after_run

    def _create_actions(self) -> None:
        self.open_project_action = self._new_action(
            "Open Project…",
            shortcut=QKeySequence("Ctrl+O"),
            object_name="openProjectAction",
        )
        self.run_action = self._new_action(
            "Run Validation",
            shortcut=QKeySequence("Ctrl+R"),
            object_name="runValidationAction",
        )
        self.cancel_action = self._new_action(
            "Cancel",
            shortcut=QKeySequence(Qt.Key.Key_Escape),
            object_name="cancelRunAction",
        )
        self.test_environment_action = self._new_action(
            "Test Environment",
            object_name="testEnvironmentAction",
        )
        self.open_last_run_action = self._new_action(
            "Open Run Directory",
            shortcut=QKeySequence("Ctrl+Shift+O"),
            object_name="openLastRunAction",
        )
        self.open_reports_action = self._new_action(
            "Open Reports",
            object_name="openReportsAction",
        )
        self.focus_results_action = self._new_action(
            "Focus Results",
            shortcut=QKeySequence("Ctrl+L"),
            object_name="focusResultsAction",
        )
        self.settings_action = self._new_action(
            "Settings…",
            shortcut=QKeySequence("Ctrl+,"),
            object_name="settingsAction",
        )
        self.help_action = self._new_action(
            "Help",
            shortcut=QKeySequence(Qt.Key.Key_F1),
            object_name="helpAction",
        )
        self.exit_action = self._new_action(
            "Exit",
            shortcut=QKeySequence.StandardKey.Quit,
            object_name="exitAction",
        )

    def _new_action(
        self,
        text: str,
        *,
        shortcut: QKeySequence | None = None,
        object_name: str,
    ) -> QAction:
        action = QAction(text, self)
        action.setObjectName(object_name)
        if shortcut is not None:
            action.setShortcut(shortcut)
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        return action

    def _build_window(self) -> None:
        self._build_menus()

        central = QWidget(self)
        central.setObjectName("mainWindowCentralWidget")
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        root.addWidget(self._build_header())

        self._splitter = QSplitter(Qt.Orientation.Vertical, central)
        self._splitter.setObjectName("mainWindowSplitter")
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(self._build_configuration_area())
        self._splitter.addWidget(self._build_results_area())
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 4)
        root.addWidget(self._splitter, 1)

        self.setCentralWidget(central)
        self._status_bar = QStatusBar(self)
        self._status_bar.setObjectName("mainStatusBar")
        self._status_bar.setSizeGripEnabled(True)
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel(_READY_LABEL, self._status_bar)
        self._status_label.setObjectName("runStatusLabel")
        self._status_label.setAccessibleName("Run status")
        self._status_bar.addWidget(self._status_label, 1)

    def _build_menus(self) -> None:
        project_menu = self.menuBar().addMenu("&Project")
        project_menu.addAction(self.open_project_action)
        project_menu.addSeparator()
        project_menu.addAction(self.exit_action)

        run_menu = self.menuBar().addMenu("&Run")
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.cancel_action)
        run_menu.addSeparator()
        run_menu.addAction(self.test_environment_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.open_last_run_action)
        view_menu.addAction(self.open_reports_action)
        view_menu.addAction(self.focus_results_action)
        view_menu.addSeparator()
        view_menu.addAction(self.settings_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.help_action)

    def _build_header(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("mainHeader")
        frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(2, 0, 2, 0)

        self._title_label = QLabel(frame)
        self._title_label.setObjectName("applicationTitleLabel")
        self._title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self._title_label, 1)

        version_label = QLabel(self._app_version, frame)
        version_label.setObjectName("applicationVersionLabel")
        version_label.setAccessibleName("GF Wordbench version")
        version_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(version_label)
        return frame

    def _build_configuration_area(self) -> QWidget:
        container = QWidget(self._splitter)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        scroll = QScrollArea(container)
        scroll.setObjectName("configurationScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget(scroll)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(8)
        content_layout.addWidget(self._section("Project", self._panels.project))
        content_layout.addWidget(
            self._section("Validation", self._panels.validation)
        )
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        layout.addWidget(self._build_action_bar())
        layout.addWidget(self._section("Progress", self._panels.progress))
        return container

    def _build_action_bar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("runActionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.run_button = QPushButton("Run Validation", bar)
        self.run_button.setObjectName("runValidationButton")
        self.run_button.setDefault(True)
        self.run_button.setAccessibleName("Run validation")

        self.cancel_button = QPushButton("Cancel", bar)
        self.cancel_button.setObjectName("cancelRunButton")
        self.cancel_button.setAccessibleName("Cancel active validation run")

        self.open_last_run_button = QPushButton("Open Run Directory", bar)
        self.open_last_run_button.setObjectName("openLastRunButton")

        self.open_reports_button = QPushButton("Open Reports", bar)
        self.open_reports_button.setObjectName("openReportsButton")

        layout.addWidget(self.run_button)
        layout.addWidget(self.cancel_button)
        layout.addStretch(1)
        layout.addWidget(self.open_last_run_button)
        layout.addWidget(self.open_reports_button)
        return bar

    def _build_results_area(self) -> QWidget:
        self._results_tabs = QTabWidget(self._splitter)
        self._results_tabs.setObjectName("resultsTabs")
        self._results_tabs.setDocumentMode(True)
        self._results_tabs.addTab(self._panels.results, "Results")
        self._results_tabs.addTab(self._panels.diagnostics, "Diagnostics")
        self._results_tabs.addTab(self._panels.artifacts, "Artifacts")
        self._results_tabs.setAccessibleName("Results and activity")
        return self._results_tabs

    @staticmethod
    def _section(title: str, widget: QWidget) -> QGroupBox:
        section = QGroupBox(title)
        section.setObjectName(f"{title.lower().replace(' ', '')}Section")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        return section

    def _connect_actions(self) -> None:
        self.open_project_action.triggered.connect(
            lambda _checked=False: self.open_project_requested.emit()
        )
        self.run_action.triggered.connect(
            lambda _checked=False: self.run_requested.emit()
        )
        self.cancel_action.triggered.connect(self._request_cancel)
        self.test_environment_action.triggered.connect(
            lambda _checked=False: self.test_environment_requested.emit()
        )
        self.open_last_run_action.triggered.connect(
            lambda _checked=False: self.open_last_run_requested.emit()
        )
        self.open_reports_action.triggered.connect(
            lambda _checked=False: self.open_reports_requested.emit()
        )
        self.focus_results_action.triggered.connect(self.focus_results)
        self.settings_action.triggered.connect(
            lambda _checked=False: self.settings_requested.emit()
        )
        self.help_action.triggered.connect(
            lambda _checked=False: self.help_requested.emit()
        )
        self.exit_action.triggered.connect(self.close)

        self.run_button.clicked.connect(
            lambda _checked=False: self.run_requested.emit()
        )
        self.cancel_button.clicked.connect(self._request_cancel)
        self.open_last_run_button.clicked.connect(
            lambda _checked=False: self.open_last_run_requested.emit()
        )
        self.open_reports_button.clicked.connect(
            lambda _checked=False: self.open_reports_requested.emit()
        )

    def set_project_identity(
        self,
        project_name: str | None,
        *,
        language_code: str | None = None,
    ) -> None:
        if project_name is not None:
            if not isinstance(project_name, str) or not project_name.strip():
                raise ValueError("project_name must be non-empty or None")
            project_name = project_name.strip()
        if language_code is not None:
            if not isinstance(language_code, str) or not language_code.strip():
                raise ValueError("language_code must be non-empty or None")
            language_code = language_code.strip()

        self._project_name = project_name
        suffix = project_name or "No active project"
        if language_code is not None:
            suffix = f"{suffix} — {language_code}"
        title = f"{_APP_NAME} — {suffix}"
        self.setWindowTitle(title)
        self._title_label.setText(title)

    def set_run_state(
        self,
        state: WindowRunState,
        *,
        status_message: str | None = None,
    ) -> None:
        if not isinstance(state, WindowRunState):
            raise TypeError("state must be WindowRunState")
        if status_message is not None:
            if not isinstance(status_message, str) or not status_message.strip():
                raise ValueError("status_message must be non-empty or None")
            status_message = status_message.strip()
        self._run_state = state
        self._apply_run_state(status_message=status_message)

    def _apply_run_state(self, *, status_message: str | None = None) -> None:
        running = self._run_state is not WindowRunState.READY
        cancelling = self._run_state is WindowRunState.CANCELLING

        self.run_action.setEnabled(not running and self._run_available)
        self.open_project_action.setEnabled(not running)
        self.test_environment_action.setEnabled(not running)
        self.settings_action.setEnabled(not running)
        self.cancel_action.setEnabled(running and not cancelling)

        self.run_button.setEnabled(not running and self._run_available)
        self.cancel_button.setEnabled(running and not cancelling)
        self.cancel_button.setText("Cancelling…" if cancelling else "Cancel")

        self._panels.project.setEnabled(not running)
        self._panels.validation.setEnabled(not running)

        default_status = {
            WindowRunState.READY: _READY_LABEL,
            WindowRunState.RUNNING: _RUNNING_LABEL,
            WindowRunState.CANCELLING: _CANCELLING_LABEL,
        }[self._run_state]
        self._status_label.setText(status_message or default_status)
        self._status_label.setAccessibleDescription(
            f"Current GF Wordbench status: {self._status_label.text()}"
        )

    def set_run_available(self, available: bool) -> None:
        if type(available) is not bool:
            raise TypeError("available must be bool")
        self._run_available = available
        self._apply_run_state()

    def set_last_run_available(self, available: bool) -> None:
        if type(available) is not bool:
            raise TypeError("available must be bool")
        self.open_last_run_action.setEnabled(available)
        self.open_last_run_button.setEnabled(available)

    def set_reports_available(self, available: bool) -> None:
        if type(available) is not bool:
            raise TypeError("available must be bool")
        self.open_reports_action.setEnabled(available)
        self.open_reports_button.setEnabled(available)

    def focus_results(self) -> None:
        self._results_tabs.setCurrentWidget(self._panels.results)
        self._panels.results.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.focus_results_requested.emit()

    def _request_cancel(self) -> None:
        if self._run_state is not WindowRunState.RUNNING:
            return
        self.set_run_state(WindowRunState.CANCELLING)
        self.cancel_requested.emit()

    def notify_run_finished(self) -> None:
        """Return to ready state and complete a pending close-after-cancel flow."""

        self.set_run_state(WindowRunState.READY)
        if self._close_after_run:
            self._allow_close = True
            self.close()

    def allow_close_after_shutdown(self) -> None:
        """Allow the controller to complete a bounded shutdown sequence."""

        self._allow_close = True
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close or self._run_state is WindowRunState.READY:
            if not self._close_signal_emitted:
                self._close_signal_emitted = True
                self.close_requested.emit(False)
            event.accept()
            return

        if self._run_state is WindowRunState.CANCELLING:
            self._close_after_run = True
            if not self._close_signal_emitted:
                self._close_signal_emitted = True
                self.close_requested.emit(True)
            event.ignore()
            return

        if not self._confirm_cancel_and_close():
            event.ignore()
            return

        self._close_after_run = True
        if not self._close_signal_emitted:
            self._close_signal_emitted = True
            self.close_requested.emit(True)
        self._request_cancel()
        event.ignore()

    def _confirm_cancel_and_close(self) -> bool:
        if self._confirm_active_close is not None:
            return bool(self._confirm_active_close(self))

        try:
            from .dialogs import confirm_cancel_and_close
        except (ImportError, AttributeError):
            return self._fallback_close_confirmation()
        return bool(confirm_cancel_and_close(self))

    def _fallback_close_confirmation(self) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Active validation run")
        box.setText("A validation run is active.")
        box.setInformativeText("Cancel the run and close GF Wordbench?")
        continue_button = box.addButton(
            "Continue running",
            QMessageBox.ButtonRole.RejectRole,
        )
        cancel_button = box.addButton(
            "Cancel and close",
            QMessageBox.ButtonRole.AcceptRole,
        )
        box.setDefaultButton(continue_button)
        box.setEscapeButton(continue_button)
        box.exec()
        return box.clickedButton() is cancel_button
