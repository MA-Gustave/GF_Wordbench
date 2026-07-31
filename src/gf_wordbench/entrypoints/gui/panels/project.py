"""Read-only active-language presentation panel for the desktop GUI.

The canonical product terminology is language context, not active project.  The
legacy ``ProjectPanel`` and ``ProjectConfigurationStatus`` import names remain
exported as compatibility aliases while the surrounding GUI is migrated to
ADR-0015.
"""

from __future__ import annotations

from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Iterable

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
    "LanguageContextStatus",
    "LanguageContextPanel",
    "ProjectConfigurationStatus",
    "ProjectPanel",
)

_EMPTY_VALUE: Final[str] = "—"
_MAX_TEXT_LENGTH: Final[int] = 4_096
_MAX_SEQUENCE_ITEMS: Final[int] = 10_000


@unique
class LanguageContextStatus(StrEnum):
    """Presentation states for one path-resolved language context."""

    UNSELECTED = "unselected"
    PROBING = "probing"
    READY = "ready"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"
    MISSING = "missing"


_STATUS_TITLES: Final[dict[LanguageContextStatus, str]] = {
    LanguageContextStatus.UNSELECTED: "No language selected",
    LanguageContextStatus.PROBING: "Resolving language context",
    LanguageContextStatus.READY: "Language context ready",
    LanguageContextStatus.INVALID: "Language selection invalid",
    LanguageContextStatus.UNSUPPORTED: "Source layout unsupported",
    LanguageContextStatus.MISSING: "Previously selected language is missing",
}

_STATUS_ICONS: Final[dict[LanguageContextStatus, QStyle.StandardPixmap]] = {
    LanguageContextStatus.UNSELECTED: QStyle.StandardPixmap.SP_MessageBoxInformation,
    LanguageContextStatus.PROBING: QStyle.StandardPixmap.SP_MessageBoxInformation,
    LanguageContextStatus.READY: QStyle.StandardPixmap.SP_DialogApplyButton,
    LanguageContextStatus.INVALID: QStyle.StandardPixmap.SP_MessageBoxCritical,
    LanguageContextStatus.UNSUPPORTED: QStyle.StandardPixmap.SP_MessageBoxWarning,
    LanguageContextStatus.MISSING: QStyle.StandardPixmap.SP_MessageBoxWarning,
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


class LanguageContextPanel(QGroupBox):
    """Display one immutable active-language context and emit user intent.

    The panel performs no filesystem discovery, recursive enumeration, source
    parsing, GF-path construction, preflight, external-process work, profile
    loading or state persistence.  A GUI controller supplies resolved
    presentation values and handles every emitted action.
    """

    select_language_requested = Signal()
    recheck_language_requested = Signal()
    open_validation_profile_requested = Signal(object)
    language_ready_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Language", parent)

        self._status = LanguageContextStatus.UNSELECTED
        self._language_ready = False
        self._busy = False
        self._run_active = False
        self._selected_path: Path | None = None
        self._language_directory: Path | None = None
        self._validation_profile: Path | None = None

        self._status_icon = QLabel(self)
        self._status_icon.setFixedSize(20, 20)
        self._status_icon.setScaledContents(True)
        self._status_icon.setAccessibleName("Language context status icon")

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
        self._status_message.setAccessibleName("Language context details")

        self._language_key = _ValueLabel(self)
        self._module_suffix = _ValueLabel(self)
        self._selected_path_value = _ValueLabel(self)
        self._language_directory_value = _ValueLabel(self)
        self._selected_path_kind = _ValueLabel(self)
        self._rgl_source_root = _ValueLabel(self)
        self._rgl_root = _ValueLabel(self)
        self._focused_target = _ValueLabel(self)
        self._entrypoints = _ValueLabel(self)
        self._source_count = _ValueLabel(self)
        self._capabilities = _ValueLabel(self)
        self._profile_status = _ValueLabel(self)

        self._select_button = QPushButton("Change Language…", self)
        self._select_button.setAccessibleName("Choose language directory or GF file")
        self._select_button.clicked.connect(self.select_language_requested.emit)

        self._recheck_button = QPushButton("Recheck Language", self)
        self._recheck_button.setAccessibleName("Revalidate selected language path")
        self._recheck_button.clicked.connect(self.recheck_language_requested.emit)

        self._open_profile_button = QPushButton("Open Validation Profile", self)
        self._open_profile_button.setAccessibleName(
            "Open optional validation profile"
        )
        self._open_profile_button.clicked.connect(
            self._emit_open_validation_profile_requested
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
        form.addRow("Language key", self._language_key)
        form.addRow("Module suffix", self._module_suffix)
        form.addRow("Selected path", self._selected_path_value)
        form.addRow("Selection kind", self._selected_path_kind)
        form.addRow("Language directory", self._language_directory_value)
        form.addRow("RGL source root", self._rgl_source_root)
        form.addRow("RGL root", self._rgl_root)
        form.addRow("Focused target", self._focused_target)
        form.addRow("Entrypoint candidates", self._entrypoints)
        form.addRow("Eligible GF sources", self._source_count)
        form.addRow("Capabilities", self._capabilities)
        form.addRow("Validation profile", self._profile_status)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self._select_button)
        actions.addWidget(self._recheck_button)
        actions.addWidget(self._open_profile_button)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(status_layout)
        layout.addSpacing(6)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addLayout(actions)

        self.set_status(LanguageContextStatus.UNSELECTED)

    @property
    def status(self) -> LanguageContextStatus:
        return self._status

    @property
    def language_ready(self) -> bool:
        return self._language_ready

    @property
    def selected_path(self) -> Path | None:
        return self._selected_path

    @property
    def language_directory(self) -> Path | None:
        return self._language_directory

    @property
    def validation_profile(self) -> Path | None:
        return self._validation_profile

    def show_language(
        self,
        *,
        language_key: str,
        selected_path: Path,
        selected_path_kind: str,
        language_directory: Path,
        rgl_source_root: Path,
        rgl_root: Path | None,
        module_suffix: str | None,
        focused_target: Path | None,
        entrypoints: Iterable[Path | str],
        source_count: int,
        capabilities: Iterable[str],
        validation_profile: Path | None = None,
        resolution_message: str = "The selected language context is ready.",
    ) -> None:
        """Present one fully resolved base language context."""

        selected = _absolute_path(selected_path, field="selected_path")
        language_dir = _absolute_path(
            language_directory,
            field="language_directory",
        )
        path_kind = _selected_path_kind(selected_path_kind)
        source_root = _absolute_path(rgl_source_root, field="rgl_source_root")
        repository_root = (
            None if rgl_root is None else _absolute_path(rgl_root, field="rgl_root")
        )
        target = (
            None
            if focused_target is None
            else _absolute_path(focused_target, field="focused_target")
        )
        profile = (
            None
            if validation_profile is None
            else _absolute_path(validation_profile, field="validation_profile")
        )

        if repository_root is not None:
            _require_descendant_or_equal(
                source_root,
                repository_root,
                field="rgl_source_root",
                root_field="rgl_root",
            )
        _require_descendant_or_equal(
            language_dir,
            source_root,
            field="language_directory",
            root_field="rgl_source_root",
        )
        _require_descendant_or_equal(
            selected,
            language_dir,
            field="selected_path",
            root_field="language_directory",
        )
        if path_kind == "file" and selected.suffix.lower() != ".gf":
            raise ValueError("selected_path file must use the .gf extension")
        if path_kind == "directory" and selected != language_dir:
            raise ValueError(
                "directory selected_path must equal language_directory"
            )
        if target is not None:
            _require_descendant_or_equal(
                target,
                language_dir,
                field="focused_target",
                root_field="language_directory",
            )
            if target.suffix.lower() != ".gf":
                raise ValueError("focused_target must use the .gf extension")

        rendered_entrypoints = _render_sequence(
            entrypoints,
            field="entrypoints",
            empty_text="None detected",
        )
        rendered_capabilities = _render_sequence(
            capabilities,
            field="capabilities",
            empty_text="source-ready",
        )

        self._selected_path = selected
        self._language_directory = language_dir
        self._validation_profile = profile
        self._language_key.set_value(
            _required_text(language_key, field="language_key")
        )
        self._module_suffix.set_value(
            None
            if module_suffix is None
            else _required_text(module_suffix, field="module_suffix")
        )
        self._selected_path_value.set_value(selected)
        self._selected_path_kind.set_value(path_kind)
        self._language_directory_value.set_value(language_dir)
        self._rgl_source_root.set_value(source_root)
        self._rgl_root.set_value(repository_root)
        self._focused_target.set_value(target)
        self._entrypoints.set_value(rendered_entrypoints)
        self._source_count.set_value(
            _non_negative_count(source_count, field="source_count")
        )
        self._capabilities.set_value(rendered_capabilities)
        self._profile_status.set_value(profile if profile is not None else "Not loaded")
        self.set_status(
            LanguageContextStatus.READY,
            message=resolution_message,
        )

    def show_invalid_language(
        self,
        *,
        selected_path: Path | None,
        message: str,
    ) -> None:
        """Present a selected path that could not produce a valid context."""

        self._prepare_unresolved_language(selected_path=selected_path)
        self.set_status(LanguageContextStatus.INVALID, message=message)

    def show_unsupported_language(
        self,
        *,
        selected_path: Path,
        message: str,
    ) -> None:
        """Present a valid path whose source layout requires explicit input."""

        self._prepare_unresolved_language(selected_path=selected_path)
        self.set_status(LanguageContextStatus.UNSUPPORTED, message=message)

    def show_missing_language(
        self,
        *,
        selected_path: Path,
        message: str = "The previously selected language path could not be found.",
    ) -> None:
        """Present a stale remembered path without searching for a replacement."""

        selected = _absolute_path(selected_path, field="selected_path")
        self._clear_language_values()
        self._selected_path = selected
        self._selected_path_value.set_value(selected)
        self.set_status(LanguageContextStatus.MISSING, message=message)

    def show_probing(self, selected_path: Path | None = None) -> None:
        """Present bounded language-probe activity."""

        if selected_path is not None:
            selected = _absolute_path(selected_path, field="selected_path")
            self._selected_path = selected
            self._selected_path_value.set_value(selected)
        self.set_status(LanguageContextStatus.PROBING)

    def clear_language(
        self,
        message: str = "Choose a GF language directory or a .gf file.",
    ) -> None:
        """Clear all resolved-language presentation values."""

        self._selected_path = None
        self._language_directory = None
        self._validation_profile = None
        self._clear_language_values()
        self.set_status(LanguageContextStatus.UNSELECTED, message=message)

    def set_validation_profile(self, profile: Path | None) -> None:
        """Update only the optional validation-profile presentation."""

        resolved = (
            None
            if profile is None
            else _absolute_path(profile, field="validation_profile")
        )
        self._validation_profile = resolved
        self._profile_status.set_value(
            resolved if resolved is not None else "Not loaded"
        )
        self._refresh_actions()

    def set_status(
        self,
        status: LanguageContextStatus,
        *,
        message: str | None = None,
    ) -> None:
        if not isinstance(status, LanguageContextStatus):
            raise TypeError("status must be LanguageContextStatus")

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

        ready = status is LanguageContextStatus.READY
        if ready != self._language_ready:
            self._language_ready = ready
            self.language_ready_changed.emit(ready)

        self._refresh_actions()

    def set_busy(self, busy: bool) -> None:
        if type(busy) is not bool:
            raise TypeError("busy must be bool")
        self._busy = busy
        self._refresh_actions()

    def set_run_active(self, active: bool) -> None:
        """Prevent language replacement while a validation run is active."""

        if type(active) is not bool:
            raise TypeError("active must be bool")
        self._run_active = active
        self._refresh_actions()

    def _prepare_unresolved_language(
        self,
        *,
        selected_path: Path | None,
    ) -> None:
        self._clear_language_values()
        selected = (
            None
            if selected_path is None
            else _absolute_path(selected_path, field="selected_path")
        )
        self._selected_path = selected
        self._language_directory = None
        self._validation_profile = None
        self._selected_path_value.set_value(selected)

    def _clear_language_values(self) -> None:
        for label in (
            self._language_key,
            self._module_suffix,
            self._selected_path_value,
            self._selected_path_kind,
            self._language_directory_value,
            self._rgl_source_root,
            self._rgl_root,
            self._focused_target,
            self._entrypoints,
            self._source_count,
            self._capabilities,
            self._profile_status,
        ):
            label.set_value(None)

    def _refresh_actions(self) -> None:
        can_change_language = not self._busy and not self._run_active
        has_selected_path = self._selected_path is not None
        has_profile = self._validation_profile is not None

        self._select_button.setEnabled(can_change_language)
        self._recheck_button.setEnabled(can_change_language and has_selected_path)
        self._open_profile_button.setEnabled(can_change_language and has_profile)

        if self._run_active:
            reason = "Language switching is disabled while a run is active."
            self._select_button.setToolTip(reason)
            self._recheck_button.setToolTip(reason)
        elif self._busy:
            reason = "Language controls are temporarily unavailable."
            self._select_button.setToolTip(reason)
            self._recheck_button.setToolTip(reason)
        else:
            self._select_button.setToolTip(
                "Choose a GF language directory or a focused .gf file."
            )
            self._recheck_button.setToolTip(
                "Revalidate the selected path through the shared language probe."
                if has_selected_path
                else "Choose a language path before rechecking it."
            )

        self._open_profile_button.setToolTip(
            "Open the explicitly loaded validation profile."
            if has_profile and can_change_language
            else "No optional validation profile is loaded."
        )

    def _emit_open_validation_profile_requested(self) -> None:
        if (
            self._validation_profile is not None
            and not self._busy
            and not self._run_active
        ):
            self.open_validation_profile_requested.emit(self._validation_profile)


# Compatibility aliases.  New code should use the language-context names.
ProjectConfigurationStatus = LanguageContextStatus
ProjectPanel = LanguageContextPanel


def _display_text(value: object | None) -> str:
    if value is None:
        return _EMPTY_VALUE
    rendered = str(value).strip()
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



def _selected_path_kind(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("selected_path_kind must be a string")
    normalized = value.strip().lower()
    if normalized not in {"file", "directory"}:
        raise ValueError("selected_path_kind must be 'file' or 'directory'")
    return normalized

def _require_descendant_or_equal(
    value: Path,
    root: Path,
    *,
    field: str,
    root_field: str,
) -> None:
    if value != root and root not in value.parents:
        raise ValueError(f"{field} must remain inside {root_field}")


def _non_negative_count(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _render_sequence(
    values: Iterable[Path | str],
    *,
    field: str,
    empty_text: str,
) -> str:
    try:
        items = list(values)
    except TypeError as exc:
        raise TypeError(f"{field} must be iterable") from exc
    if len(items) > _MAX_SEQUENCE_ITEMS:
        raise ValueError(f"{field} contains too many items")

    rendered: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if isinstance(item, Path):
            value = item.name if item.name else str(item)
        elif isinstance(item, str):
            value = _required_text(item, field=f"{field}[{index}]")
        else:
            raise TypeError(f"{field}[{index}] must be pathlib.Path or str")
        value = value.strip()
        if not value:
            raise ValueError(f"{field}[{index}] must not be empty")
        if value not in seen:
            seen.add(value)
            rendered.append(value)

    return ", ".join(rendered) if rendered else empty_text
