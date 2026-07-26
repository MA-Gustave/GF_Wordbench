"""Read-only active-project presentation panel for the desktop GUI."""

from __future__ import annotations

from enum import StrEnum, unique
from pathlib import Path
from typing import Final

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

__all__ = (
    "ProjectConfigurationStatus",
    "ProjectPanel",
)

_EMPTY_VALUE: Final[str] = "—"
_MAX_TEXT_LENGTH: Final[int] = 4_096


@unique
class ProjectConfigurationStatus(StrEnum):
    """Presentation states for the canonical active-project configuration."""

    UNSELECTED = "unselected"
    LOADING = "loading"
    VALID = "valid"
    INVALID = "invalid"
    UNINITIALIZED = "uninitialized"
    MISSING = "missing"


_STATUS_TITLES: Final[dict[ProjectConfigurationStatus, str]] = {
    ProjectConfigurationStatus.UNSELECTED: "No active project selected",
    ProjectConfigurationStatus.LOADING: "Loading project configuration",
    ProjectConfigurationStatus.VALID: "Configuration valid",
    ProjectConfigurationStatus.INVALID: "Configuration invalid",
    ProjectConfigurationStatus.UNINITIALIZED: "Project not initialized",
    ProjectConfigurationStatus.MISSING: "Previously selected project is missing",
}

_STATUS_ICONS: Final[dict[ProjectConfigurationStatus, QStyle.StandardPixmap]] = {
    ProjectConfigurationStatus.UNSELECTED: QStyle.StandardPixmap.SP_MessageBoxInformation,
    ProjectConfigurationStatus.LOADING: QStyle.StandardPixmap.SP_MessageBoxInformation,
    ProjectConfigurationStatus.VALID: QStyle.StandardPixmap.SP_DialogApplyButton,
    ProjectConfigurationStatus.INVALID: QStyle.StandardPixmap.SP_MessageBoxCritical,
    ProjectConfigurationStatus.UNINITIALIZED: QStyle.StandardPixmap.SP_MessageBoxWarning,
    ProjectConfigurationStatus.MISSING: QStyle.StandardPixmap.SP_MessageBoxWarning,
}


class _ValueLabel(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(_EMPTY_VALUE, parent)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_value(self, value: object | None) -> None:
        rendered = _display_text(value)
        self.setText(rendered)
        self.setToolTip("" if rendered == _EMPTY_VALUE else rendered)


class ProjectPanel(QGroupBox):
    """Display one active project and emit project-related user intent.

    The panel performs no project discovery, TOML parsing, filesystem mutation,
    validation orchestration, or external-process work. A GUI controller supplies
    resolved presentation values and handles all emitted actions.
    """

    select_project_requested = Signal()
    check_project_requested = Signal()
    open_configuration_requested = Signal(object)
    configuration_valid_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Project", parent)

        self._status = ProjectConfigurationStatus.UNSELECTED
        self._configuration_valid = False
        self._busy = False
        self._run_active = False
        self._project_root: Path | None = None
        self._project_file: Path | None = None

        self._status_icon = QLabel(self)
        self._status_icon.setFixedSize(20, 20)
        self._status_icon.setScaledContents(True)
        self._status_icon.setAccessibleName("Project configuration status icon")

        self._status_title = QLabel(self)
        self._status_title.setTextFormat(Qt.TextFormat.PlainText)
        title_font = QFont(self._status_title.font())
        title_font.setBold(True)
        self._status_title.setFont(title_font)

        self._status_message = QLabel(self)
        self._status_message.setTextFormat(Qt.TextFormat.PlainText)
        self._status_message.setWordWrap(True)
        self._status_message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._status_message.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._status_message.setAccessibleName("Project configuration details")

        self._name = _ValueLabel(self)
        self._project_id = _ValueLabel(self)
        self._language_code = _ValueLabel(self)
        self._project_root_value = _ValueLabel(self)
        self._project_file_status = _ValueLabel(self)
        self._source_root = _ValueLabel(self)
        self._entrypoint_count = _ValueLabel(self)
        self._checkpoint_count = _ValueLabel(self)
        self._required_scenario_count = _ValueLabel(self)

        self._select_button = QPushButton("Select Project…", self)
        self._select_button.setAccessibleName("Select active project")
        self._select_button.clicked.connect(self.select_project_requested.emit)

        self._check_button = QPushButton("Check Project", self)
        self._check_button.setAccessibleName("Check active project configuration")
        self._check_button.clicked.connect(self.check_project_requested.emit)

        self._open_configuration_button = QPushButton("Open project.toml", self)
        self._open_configuration_button.setAccessibleName(
            "Open active project configuration"
        )
        self._open_configuration_button.clicked.connect(
            self._emit_open_configuration_requested
        )

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        status_layout.addWidget(self._status_icon, 0, Qt.AlignmentFlag.AlignTop)

        status_text_layout = QVBoxLayout()
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(2)
        status_text_layout.addWidget(self._status_title)
        status_text_layout.addWidget(self._status_message)
        status_layout.addLayout(status_text_layout, 1)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.addRow("Project name", self._name)
        form.addRow("Project ID", self._project_id)
        form.addRow("Language code", self._language_code)
        form.addRow("Project root", self._project_root_value)
        form.addRow("project.toml status", self._project_file_status)
        form.addRow("Source directory", self._source_root)
        form.addRow("Entrypoints", self._entrypoint_count)
        form.addRow("Checkpoints", self._checkpoint_count)
        form.addRow("Required scenarios", self._required_scenario_count)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self._select_button)
        actions.addWidget(self._check_button)
        actions.addWidget(self._open_configuration_button)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(status_layout)
        layout.addSpacing(6)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addLayout(actions)

        self.set_status(ProjectConfigurationStatus.UNSELECTED)

    @property
    def status(self) -> ProjectConfigurationStatus:
        return self._status

    @property
    def configuration_valid(self) -> bool:
        return self._configuration_valid

    @property
    def project_root(self) -> Path | None:
        return self._project_root

    @property
    def project_file(self) -> Path | None:
        return self._project_file

    def show_project(
        self,
        *,
        name: str,
        project_id: str,
        language_code: str,
        project_root: Path,
        project_file: Path,
        source_root: Path,
        entrypoint_count: int,
        checkpoint_count: int,
        required_scenario_count: int,
        configuration_message: str = "The active project configuration is valid.",
    ) -> None:
        """Present a fully resolved and valid active project."""

        root = _absolute_path(project_root, field="project_root")
        config_file = _absolute_path(project_file, field="project_file")
        source = _absolute_path(source_root, field="source_root")

        if config_file.name != "project.toml":
            raise ValueError("project_file must name project.toml")
        if config_file.parent != root:
            raise ValueError("project_file must equal project_root/project.toml")

        self._project_root = root
        self._project_file = config_file
        self._name.set_value(_required_text(name, field="name"))
        self._project_id.set_value(_required_text(project_id, field="project_id"))
        self._language_code.set_value(
            _required_text(language_code, field="language_code")
        )
        self._project_root_value.set_value(root)
        self._project_file_status.set_value("Valid")
        self._source_root.set_value(source)
        self._entrypoint_count.set_value(
            _non_negative_count(entrypoint_count, field="entrypoint_count")
        )
        self._checkpoint_count.set_value(
            _non_negative_count(checkpoint_count, field="checkpoint_count")
        )
        self._required_scenario_count.set_value(
            _non_negative_count(
                required_scenario_count,
                field="required_scenario_count",
            )
        )
        self.set_status(
            ProjectConfigurationStatus.VALID,
            message=configuration_message,
        )

    def show_invalid_project(
        self,
        *,
        project_root: Path | None,
        message: str,
        project_file: Path | None = None,
    ) -> None:
        """Present precise active-project configuration errors."""

        self._prepare_unresolved_project(
            project_root=project_root,
            project_file=project_file,
        )
        self._project_file_status.set_value("Invalid")
        self.set_status(ProjectConfigurationStatus.INVALID, message=message)

    def show_uninitialized_project(
        self,
        *,
        project_root: Path,
        message: str = "The project template contains unresolved required placeholders.",
        project_file: Path | None = None,
    ) -> None:
        """Present a template or project that is not initialized."""

        self._prepare_unresolved_project(
            project_root=project_root,
            project_file=project_file,
        )
        self._project_file_status.set_value("Uninitialized")
        self.set_status(ProjectConfigurationStatus.UNINITIALIZED, message=message)

    def show_missing_project(
        self,
        *,
        project_root: Path,
        message: str = "The previously selected project could not be found.",
    ) -> None:
        """Present a missing previous selection without selecting another root."""

        root = _absolute_path(project_root, field="project_root")
        self._clear_project_values()
        self._project_root = root
        self._project_file = root / "project.toml"
        self._project_root_value.set_value(root)
        self._project_file_status.set_value("Missing")
        self.set_status(ProjectConfigurationStatus.MISSING, message=message)

    def show_loading(self, project_root: Path | None = None) -> None:
        """Present bounded project-loading activity."""

        if project_root is not None:
            root = _absolute_path(project_root, field="project_root")
            self._project_root = root
            self._project_file = root / "project.toml"
            self._project_root_value.set_value(root)
            self._project_file_status.set_value("Loading")
        self.set_status(ProjectConfigurationStatus.LOADING)

    def clear_project(
        self,
        message: str = "Select a workspace containing project/project.toml.",
    ) -> None:
        """Clear project-derived presentation values."""

        self._project_root = None
        self._project_file = None
        self._clear_project_values()
        self.set_status(ProjectConfigurationStatus.UNSELECTED, message=message)

    def set_status(
        self,
        status: ProjectConfigurationStatus,
        *,
        message: str | None = None,
    ) -> None:
        if not isinstance(status, ProjectConfigurationStatus):
            raise TypeError("status must be ProjectConfigurationStatus")

        rendered_message = (
            _STATUS_TITLES[status]
            if message is None
            else _required_text(message, field="message", multiline=True)
        )

        self._status = status
        self._status_title.setText(_STATUS_TITLES[status])
        self._status_message.setText(rendered_message)
        self._status_icon.setPixmap(
            self.style()
            .standardIcon(_STATUS_ICONS[status])
            .pixmap(self._status_icon.size())
        )
        self._status_icon.setToolTip(_STATUS_TITLES[status])

        valid = status is ProjectConfigurationStatus.VALID
        if valid != self._configuration_valid:
            self._configuration_valid = valid
            self.configuration_valid_changed.emit(valid)

        self._refresh_actions()

    def set_busy(self, busy: bool) -> None:
        if type(busy) is not bool:
            raise TypeError("busy must be bool")
        self._busy = busy
        self._refresh_actions()

    def set_run_active(self, active: bool) -> None:
        """Prevent project switching while a validation run is active."""

        if type(active) is not bool:
            raise TypeError("active must be bool")
        self._run_active = active
        self._refresh_actions()

    def _prepare_unresolved_project(
        self,
        *,
        project_root: Path | None,
        project_file: Path | None,
    ) -> None:
        self._clear_project_values()

        root = (
            None
            if project_root is None
            else _absolute_path(project_root, field="project_root")
        )
        config_file = (
            None
            if project_file is None
            else _absolute_path(project_file, field="project_file")
        )

        if config_file is not None and config_file.name != "project.toml":
            raise ValueError("project_file must name project.toml")
        if root is not None and config_file is not None and config_file.parent != root:
            raise ValueError("project_file must equal project_root/project.toml")

        self._project_root = root
        self._project_file = config_file or (
            None if root is None else root / "project.toml"
        )
        self._project_root_value.set_value(root)

    def _clear_project_values(self) -> None:
        for label in (
            self._name,
            self._project_id,
            self._language_code,
            self._project_root_value,
            self._project_file_status,
            self._source_root,
            self._entrypoint_count,
            self._checkpoint_count,
            self._required_scenario_count,
        ):
            label.set_value(None)

    def _refresh_actions(self) -> None:
        can_change_project = not self._busy and not self._run_active
        has_project_root = self._project_root is not None
        has_project_file = self._project_file is not None

        self._select_button.setEnabled(can_change_project)
        self._check_button.setEnabled(can_change_project and has_project_root)
        self._open_configuration_button.setEnabled(
            can_change_project and has_project_file
        )

        if self._run_active:
            reason = "Project switching is disabled while a run is active."
            self._select_button.setToolTip(reason)
            self._check_button.setToolTip(reason)
        elif self._busy:
            reason = "Project controls are temporarily unavailable."
            self._select_button.setToolTip(reason)
            self._check_button.setToolTip(reason)
        else:
            self._select_button.setToolTip(
                "Select the workspace containing the canonical active project."
            )
            self._check_button.setToolTip(
                "Run the shared read-only active-project checker."
                if has_project_root
                else "Select a project before checking it."
            )

        self._open_configuration_button.setToolTip(
            "Open project.toml through the configured project workflow."
            if has_project_file and can_change_project
            else "No active project configuration is available."
        )

    def _emit_open_configuration_requested(self) -> None:
        if self._project_file is not None and not self._busy and not self._run_active:
            self.open_configuration_requested.emit(self._project_file)


def _display_text(value: object | None) -> str:
    if value is None:
        return _EMPTY_VALUE
    if isinstance(value, Path):
        rendered = str(value)
    else:
        rendered = str(value)
    rendered = rendered.strip()
    return rendered if rendered else _EMPTY_VALUE


def _required_text(
    value: object,
    *,
    field: str,
    multiline: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds {_MAX_TEXT_LENGTH} characters")
    if not multiline and any(character in value for character in ("\r", "\n")):
        raise ValueError(f"{field} must be a single line")
    return value.strip()


def _absolute_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    if ".." in value.parts:
        raise ValueError(f"{field} must be lexically normalized")
    return value


def _non_negative_count(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value
