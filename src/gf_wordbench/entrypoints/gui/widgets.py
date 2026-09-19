"""Reusable, presentation-only Qt widgets for the GF Wordbench GUI."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFontMetrics, QIcon, QKeySequence, QResizeEvent, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

_MAX_TEXT_LENGTH: Final[int] = 1_000_000
_MAX_ACTIVITY_LINES: Final[int] = 100_000
_MAX_ACTIVITY_ENTRY_LENGTH: Final[int] = 64_000
_MAX_KEY_VALUE_ITEMS: Final[int] = 2_000
_MAX_PATH_LENGTH: Final[int] = 32_768


@unique
class PresentationStatus(StrEnum):
    NEUTRAL = "neutral"
    READY = "ready"
    RUNNING = "running"
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


@unique
class MessageSeverity(StrEnum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


_STATUS_GLYPHS: Final[Mapping[PresentationStatus, str]] = MappingProxyType(
    {
        PresentationStatus.NEUTRAL: "•",
        PresentationStatus.READY: "●",
        PresentationStatus.RUNNING: "▶",
        PresentationStatus.OK: "✓",
        PresentationStatus.WARNING: "!",
        PresentationStatus.FAIL: "×",
        PresentationStatus.ERROR: "×",
        PresentationStatus.CANCELLED: "■",
        PresentationStatus.UNAVAILABLE: "—",
    }
)

_STATUS_ACCESSIBLE_NAMES: Final[Mapping[PresentationStatus, str]] = MappingProxyType(
    {
        PresentationStatus.NEUTRAL: "Neutral status",
        PresentationStatus.READY: "Ready",
        PresentationStatus.RUNNING: "Running",
        PresentationStatus.OK: "Successful",
        PresentationStatus.WARNING: "Warning",
        PresentationStatus.FAIL: "Validation failure",
        PresentationStatus.ERROR: "Framework error",
        PresentationStatus.CANCELLED: "Cancelled",
        PresentationStatus.UNAVAILABLE: "Unavailable",
    }
)


@dataclass(frozen=True, slots=True)
class ProgressPresentation:
    status: PresentationStatus = PresentationStatus.NEUTRAL
    status_text: str = ""
    stage: str = ""
    subject: str = ""
    completed: int = 0
    total: int | None = None
    elapsed_text: str = ""
    warning_count: int = 0
    failure_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.status, PresentationStatus):
            raise TypeError("status must be PresentationStatus")
        for field_name in ("status_text", "stage", "subject", "elapsed_text"):
            _require_text(
                getattr(self, field_name),
                field=field_name,
                allow_empty=True,
            )
        _require_non_negative_int(self.completed, field="completed")
        if self.total is not None:
            _require_non_negative_int(self.total, field="total")
            if self.completed > self.total:
                raise ValueError("completed must not exceed total")
        _require_non_negative_int(self.warning_count, field="warning_count")
        _require_non_negative_int(self.failure_count, field="failure_count")


@dataclass(frozen=True, slots=True)
class KeyValueItem:
    key: str
    value: str
    accessible_name: str = ""
    tooltip: str = ""

    def __post_init__(self) -> None:
        _require_text(self.key, field="key")
        _require_text(self.value, field="value", allow_empty=True)
        _require_text(
            self.accessible_name,
            field="accessible_name",
            allow_empty=True,
        )
        _require_text(self.tooltip, field="tooltip", allow_empty=True)


class ElidingLabel(QLabel):
    """A label that preserves full text while eliding visual overflow."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        *,
        elide_mode: Qt.TextElideMode = Qt.TextElideMode.ElideMiddle,
    ) -> None:
        super().__init__(parent)
        self._full_text = ""
        self._elide_mode = elide_mode
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.set_full_text(text)

    @property
    def full_text(self) -> str:
        return self._full_text

    def set_full_text(self, text: str) -> None:
        checked = _require_text(text, field="text", allow_empty=True)
        self._full_text = checked
        self.setToolTip(checked if checked else "")
        self.setAccessibleName(checked)
        self._refresh_elision()

    def setText(self, text: str) -> None:
        self.set_full_text(text)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh_elision()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.ApplicationFontChange,
            QEvent.Type.StyleChange,
        }:
            self._refresh_elision()

    def _refresh_elision(self) -> None:
        width = max(0, self.contentsRect().width())
        if width <= 0:
            rendered = self._full_text
        else:
            metrics = QFontMetrics(self.font())
            rendered = metrics.elidedText(self._full_text, self._elide_mode, width)
        QLabel.setText(self, rendered)


class SelectableValue(QLineEdit):
    """Read-only, keyboard-selectable single-line presentation text."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrame(False)
        self.setClearButtonEnabled(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setText(text)

    def setText(self, text: str | None) -> None:
        checked = _require_text(
            "" if text is None else text,
            field="text",
            allow_empty=True,
        )
        super().setText(checked)
        self.setToolTip(checked if checked else "")


class StatusBadge(QFrame):
    """Text-and-symbol status badge whose meaning does not depend on color."""

    status_changed = Signal(object, str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        status: PresentationStatus = PresentationStatus.NEUTRAL,
        text: str = "",
    ) -> None:
        super().__init__(parent)
        self._status = PresentationStatus.NEUTRAL
        self._text = ""
        self.setObjectName("statusBadge")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 3, 7, 3)
        layout.setSpacing(5)

        self._glyph_label = QLabel(self)
        self._glyph_label.setObjectName("statusBadgeGlyph")
        self._glyph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._glyph_label.setFixedWidth(16)
        layout.addWidget(self._glyph_label)

        self._text_label = QLabel(self)
        self._text_label.setObjectName("statusBadgeText")
        self._text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._text_label)

        self.set_status(status, text)

    @property
    def status(self) -> PresentationStatus:
        return self._status

    @property
    def text(self) -> str:
        return self._text

    def set_status(
        self,
        status: PresentationStatus,
        text: str = "",
    ) -> None:
        if not isinstance(status, PresentationStatus):
            raise TypeError("status must be PresentationStatus")
        checked_text = _require_text(text, field="text", allow_empty=True)
        visible_text = checked_text or _STATUS_ACCESSIBLE_NAMES[status]
        changed = status is not self._status or checked_text != self._text

        self._status = status
        self._text = checked_text
        self.setProperty("status", status.value)
        self._glyph_label.setText(_STATUS_GLYPHS[status])
        self._text_label.setText(visible_text)
        accessible = f"{_STATUS_ACCESSIBLE_NAMES[status]}: {visible_text}"
        self.setAccessibleName(accessible)
        self.setToolTip(accessible)
        _refresh_style(self)

        if changed:
            self.status_changed.emit(status, checked_text)


class PathField(QWidget):
    """Generic path editor/display that emits intent instead of opening dialogs."""

    text_changed = Signal(str)
    browse_requested = Signal()
    open_requested = Signal(object)
    copy_completed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        text: str = "",
        editable: bool = True,
        browse_label: str = "Browse…",
        open_label: str = "Open",
        copy_label: str = "Copy",
        show_browse: bool = True,
        show_open: bool = False,
        show_copy: bool = True,
    ) -> None:
        super().__init__(parent)
        self._path: Path | None = None
        self._editable = bool(editable)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("pathFieldLineEdit")
        self.line_edit.setReadOnly(not self._editable)
        self.line_edit.setClearButtonEnabled(self._editable)
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit, 1)

        self.browse_button = QPushButton(
            _require_text(browse_label, field="browse_label"),
            self,
        )
        self.browse_button.setObjectName("pathFieldBrowseButton")
        self.browse_button.setVisible(show_browse)
        self.browse_button.clicked.connect(self.browse_requested.emit)
        layout.addWidget(self.browse_button)

        self.open_button = QPushButton(
            _require_text(open_label, field="open_label"),
            self,
        )
        self.open_button.setObjectName("pathFieldOpenButton")
        self.open_button.setVisible(show_open)
        self.open_button.clicked.connect(self._emit_open_requested)
        layout.addWidget(self.open_button)

        self.copy_button = QPushButton(
            _require_text(copy_label, field="copy_label"),
            self,
        )
        self.copy_button.setObjectName("pathFieldCopyButton")
        self.copy_button.setVisible(show_copy)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_button)

        self.set_text(text)

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def text(self) -> str:
        return self.line_edit.text()

    @property
    def editable(self) -> bool:
        return self._editable

    def set_editable(self, editable: bool) -> None:
        self._editable = bool(editable)
        self.line_edit.setReadOnly(not self._editable)
        self.line_edit.setClearButtonEnabled(self._editable)

    def set_text(self, text: str) -> None:
        checked = _require_text(
            text,
            field="text",
            allow_empty=True,
            max_length=_MAX_PATH_LENGTH,
        )
        self.line_edit.setText(checked)

    def set_path(self, path: Path | str | None) -> None:
        if path is None:
            self._path = None
            self.line_edit.clear()
            return
        checked = _coerce_path(path)
        self._path = checked
        self.line_edit.setText(str(checked))

    def set_open_available(self, available: bool) -> None:
        self.open_button.setEnabled(bool(available) and self._path is not None)

    def copy_to_clipboard(self) -> None:
        text = self.line_edit.text()
        if not text:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.copy_completed.emit(text)

    def _on_text_changed(self, text: str) -> None:
        if not text:
            self._path = None
        else:
            try:
                self._path = Path(text)
            except (TypeError, ValueError, OSError):
                self._path = None
        self.line_edit.setToolTip(text)
        self.open_button.setEnabled(self._path is not None)
        self.copy_button.setEnabled(bool(text))
        self.text_changed.emit(text)

    def _emit_open_requested(self) -> None:
        if self._path is not None:
            self.open_requested.emit(self._path)


class InlineMessage(QFrame):
    """Concise message with optional selectable technical details."""

    details_visibility_changed = Signal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        severity: MessageSeverity = MessageSeverity.INFORMATION,
        title: str = "",
        message: str = "",
        details: str = "",
    ) -> None:
        super().__init__(parent)
        self._severity = MessageSeverity.INFORMATION
        self.setObjectName("inlineMessage")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        root = QVBoxLayout(self)
        root.setContentsMargins(9, 7, 9, 7)
        root.setSpacing(6)

        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(7)
        root.addLayout(heading)

        self._icon_label = QLabel(self)
        self._icon_label.setFixedSize(20, 20)
        heading.addWidget(self._icon_label)

        text_container = QWidget(self)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        heading.addWidget(text_container, 1)

        self._title_label = QLabel(text_container)
        self._title_label.setObjectName("inlineMessageTitle")
        self._title_label.setWordWrap(True)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(self._title_label)

        self._message_label = QLabel(text_container)
        self._message_label.setObjectName("inlineMessageBody")
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        text_layout.addWidget(self._message_label)

        self._details_button = QToolButton(self)
        self._details_button.setText("Show details")
        self._details_button.setCheckable(True)
        self._details_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._details_button.setArrowType(Qt.ArrowType.RightArrow)
        self._details_button.toggled.connect(self._toggle_details)
        root.addWidget(self._details_button, 0, Qt.AlignmentFlag.AlignLeft)

        self._details_view = QPlainTextEdit(self)
        self._details_view.setReadOnly(True)
        self._details_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._details_view.setMinimumHeight(90)
        self._details_view.setMaximumBlockCount(5_000)
        self._details_view.setVisible(False)
        root.addWidget(self._details_view)

        self.set_message(
            severity=severity,
            title=title,
            message=message,
            details=details,
        )

    @property
    def severity(self) -> MessageSeverity:
        return self._severity

    def set_message(
        self,
        *,
        severity: MessageSeverity,
        title: str,
        message: str,
        details: str = "",
    ) -> None:
        if not isinstance(severity, MessageSeverity):
            raise TypeError("severity must be MessageSeverity")
        checked_title = _require_text(title, field="title", allow_empty=True)
        checked_message = _require_text(message, field="message", allow_empty=True)
        checked_details = _require_text(details, field="details", allow_empty=True)

        self._severity = severity
        self.setProperty("severity", severity.value)
        self._title_label.setText(checked_title)
        self._title_label.setVisible(bool(checked_title))
        self._message_label.setText(checked_message)
        self._details_view.setPlainText(checked_details)
        self._details_button.setVisible(bool(checked_details))
        if not checked_details:
            self._details_button.setChecked(False)
            self._details_view.setVisible(False)
        self._icon_label.setPixmap(self._severity_icon(severity).pixmap(18, 18))
        accessible = ": ".join(part for part in (checked_title, checked_message) if part)
        self.setAccessibleName(accessible)
        _refresh_style(self)

    def _toggle_details(self, visible: bool) -> None:
        self._details_view.setVisible(visible)
        self._details_button.setText("Hide details" if visible else "Show details")
        self._details_button.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.details_visibility_changed.emit(visible)

    def _severity_icon(self, severity: MessageSeverity) -> QIcon:
        standard = {
            MessageSeverity.INFORMATION: QStyle.StandardPixmap.SP_MessageBoxInformation,
            MessageSeverity.WARNING: QStyle.StandardPixmap.SP_MessageBoxWarning,
            MessageSeverity.ERROR: QStyle.StandardPixmap.SP_MessageBoxCritical,
        }[severity]
        return self.style().standardIcon(standard)


class BoundedActivityView(QPlainTextEdit):
    """Read-only activity presentation with bounded memory and rendering cost."""

    cleared = Signal()
    entry_appended = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        maximum_lines: int = 2_000,
    ) -> None:
        super().__init__(parent)
        self._maximum_lines = 0
        self.setObjectName("boundedActivityView")
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.setMaximumLines(maximum_lines)

    @property
    def maximum_lines(self) -> int:
        return self._maximum_lines

    def setMaximumLines(self, maximum_lines: int) -> None:
        checked = _require_positive_int(
            maximum_lines,
            field="maximum_lines",
            maximum=_MAX_ACTIVITY_LINES,
        )
        self._maximum_lines = checked
        self.document().setMaximumBlockCount(checked)

    def append_entry(self, text: str) -> None:
        checked = _require_text(
            text,
            field="text",
            allow_empty=True,
            max_length=_MAX_ACTIVITY_ENTRY_LENGTH,
        )
        normalized = checked.replace("\x00", "\\x00")
        self.appendPlainText(normalized)
        self.ensureCursorVisible()
        self.entry_appended.emit(normalized)

    def append_entries(self, entries: Iterable[str]) -> None:
        if isinstance(entries, (str, bytes, bytearray, Mapping)):
            raise TypeError("entries must be an iterable of strings")
        for entry in entries:
            self.append_entry(entry)

    def clear(self) -> None:
        self.clear_presentation()

    def clear_presentation(self) -> None:
        super().clear()
        self.cleared.emit()


class ProgressWidget(QWidget):
    """Structured progress display that supports determinate and unknown totals."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presentation = ProgressPresentation()
        self.setObjectName("progressWidget")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        root.addLayout(header)

        self.status_badge = StatusBadge(self)
        header.addWidget(self.status_badge)

        self.stage_label = ElidingLabel(parent=self)
        self.stage_label.setObjectName("progressStageLabel")
        header.addWidget(self.stage_label, 1)

        self.elapsed_label = QLabel(self)
        self.elapsed_label.setObjectName("progressElapsedLabel")
        self.elapsed_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.elapsed_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        header.addWidget(self.elapsed_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setTextVisible(True)
        root.addWidget(self.progress_bar)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)
        root.addLayout(footer)

        self.subject_label = ElidingLabel(parent=self)
        self.subject_label.setObjectName("progressSubjectLabel")
        footer.addWidget(self.subject_label, 1)

        self.counts_label = QLabel(self)
        self.counts_label.setObjectName("progressCountsLabel")
        self.counts_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.counts_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        footer.addWidget(self.counts_label)

        self.set_presentation(self._presentation)

    @property
    def presentation(self) -> ProgressPresentation:
        return self._presentation

    def set_presentation(self, presentation: ProgressPresentation) -> None:
        if not isinstance(presentation, ProgressPresentation):
            raise TypeError("presentation must be ProgressPresentation")
        self._presentation = presentation

        self.status_badge.set_status(presentation.status, presentation.status_text)
        self.stage_label.set_full_text(presentation.stage or "No active stage")
        self.subject_label.set_full_text(presentation.subject or "No active subject")
        self.elapsed_label.setText(presentation.elapsed_text)
        self.elapsed_label.setVisible(bool(presentation.elapsed_text))

        if presentation.total is None:
            self.progress_bar.setRange(0, 0)
            progress_text = f"{presentation.completed} completed"
        elif presentation.total == 0:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0 / 0")
            progress_text = "0 of 0 completed"
        else:
            self.progress_bar.setRange(0, presentation.total)
            self.progress_bar.setValue(presentation.completed)
            self.progress_bar.setFormat(f"{presentation.completed} / {presentation.total}")
            progress_text = f"{presentation.completed} of {presentation.total} completed"

        self.counts_label.setText(
            f"Warnings: {presentation.warning_count}  Failures: {presentation.failure_count}"
        )
        accessible = "; ".join(
            (
                _STATUS_ACCESSIBLE_NAMES[presentation.status],
                presentation.status_text or "",
                f"Stage: {presentation.stage or 'none'}",
                f"Subject: {presentation.subject or 'none'}",
                progress_text,
                f"Warnings: {presentation.warning_count}",
                f"Failures: {presentation.failure_count}",
                f"Elapsed: {presentation.elapsed_text or 'not available'}",
            )
        )
        self.setAccessibleName(accessible)
        self.progress_bar.setAccessibleName(progress_text)


class KeyValueView(QWidget):
    """Accessible read-only key/value presentation with selectable values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: tuple[KeyValueItem, ...] = ()
        self._value_widgets: list[SelectableValue] = []
        self._layout = QFormLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self._layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    @property
    def items(self) -> tuple[KeyValueItem, ...]:
        return self._items

    def set_items(self, items: Iterable[KeyValueItem]) -> None:
        if isinstance(items, (str, bytes, bytearray, Mapping)):
            raise TypeError("items must be an iterable of KeyValueItem values")
        prepared = tuple(items)
        if len(prepared) > _MAX_KEY_VALUE_ITEMS:
            raise ValueError(f"items exceeds the supported limit of {_MAX_KEY_VALUE_ITEMS}")
        if not all(isinstance(item, KeyValueItem) for item in prepared):
            raise TypeError("items must contain KeyValueItem values")

        _clear_layout(self._layout)
        self._value_widgets.clear()
        self._items = prepared

        for item in prepared:
            label = QLabel(item.key, self)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value = SelectableValue(item.value, self)
            value.setAccessibleName(item.accessible_name or item.key)
            value.setToolTip(item.tooltip or item.value)
            label.setBuddy(value)
            self._layout.addRow(label, value)
            self._value_widgets.append(value)


class CollapsibleSection(QWidget):
    """Presentation-only disclosure section suitable for advanced options."""

    expanded_changed = Signal(bool)

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        expanded: bool = False,
    ) -> None:
        super().__init__(parent)
        self._title = _require_text(title, field="title")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        self.toggle_button = QToolButton(self)
        self.toggle_button.setObjectName("collapsibleSectionToggle")
        self.toggle_button.setText(self._title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.toggled.connect(self.set_expanded)
        root.addWidget(self.toggle_button)

        self.content = QWidget(self)
        self.content.setObjectName("collapsibleSectionContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(18, 0, 0, 0)
        self.content_layout.setSpacing(6)
        root.addWidget(self.content)

        self.set_expanded(expanded)

    @property
    def expanded(self) -> bool:
        return self.toggle_button.isChecked()

    def set_expanded(self, expanded: bool) -> None:
        checked = bool(expanded)
        if self.toggle_button.isChecked() != checked:
            self.toggle_button.setChecked(checked)
            return
        self.content.setVisible(checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self.toggle_button.setAccessibleName(
            f"{self._title}, {'expanded' if checked else 'collapsed'}"
        )
        self.expanded_changed.emit(checked)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be QWidget")
        self.content_layout.addWidget(widget, stretch)

    def add_layout(self, layout: QLayout, stretch: int = 0) -> None:
        if not isinstance(layout, QLayout):
            raise TypeError("layout must be QLayout")
        self.content_layout.addLayout(layout, stretch)


class EmptyState(QWidget):
    """Reusable empty-state presentation with one optional action."""

    action_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "",
        message: str = "",
        action_label: str = "",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(7)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(self)
        self.title_label.setObjectName("emptyStateTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.title_label)

        self.message_label = QLabel(self)
        self.message_label.setObjectName("emptyStateMessage")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.message_label)

        self.action_button = QPushButton(self)
        self.action_button.clicked.connect(self.action_requested.emit)
        root.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.set_content(
            title=title,
            message=message,
            action_label=action_label,
        )

    def set_content(
        self,
        *,
        title: str,
        message: str,
        action_label: str = "",
    ) -> None:
        checked_title = _require_text(title, field="title", allow_empty=True)
        checked_message = _require_text(message, field="message", allow_empty=True)
        checked_action = _require_text(
            action_label,
            field="action_label",
            allow_empty=True,
        )
        self.title_label.setText(checked_title)
        self.title_label.setVisible(bool(checked_title))
        self.message_label.setText(checked_message)
        self.message_label.setVisible(bool(checked_message))
        self.action_button.setText(checked_action)
        self.action_button.setVisible(bool(checked_action))
        self.setAccessibleName(": ".join(part for part in (checked_title, checked_message) if part))


def install_copy_shortcut(
    widget: QWidget,
    text_provider: Callable[[], str],
) -> QShortcut:
    """Install a standard Copy shortcut using a side-effect-free text provider."""

    if not isinstance(widget, QWidget):
        raise TypeError("widget must be QWidget")
    if not callable(text_provider):
        raise TypeError("text_provider must be callable")
    shortcut = QShortcut(QKeySequence.StandardKey.Copy, widget)

    def copy_text() -> None:
        value = text_provider()
        if not isinstance(value, str):
            raise TypeError("text_provider must return str")
        QApplication.clipboard().setText(value)

    shortcut.activated.connect(copy_text)
    return shortcut


def set_validation_error(
    widget: QWidget,
    message: str | None,
) -> None:
    """Attach or clear presentation validation state without owning validation rules."""

    if not isinstance(widget, QWidget):
        raise TypeError("widget must be QWidget")
    checked = None
    if message is not None:
        checked = _require_text(message, field="message")
    widget.setProperty("validationState", "error" if checked else "")
    widget.setProperty("validationMessage", checked or "")
    widget.setAccessibleDescription(checked or "")
    if checked:
        widget.setToolTip(checked)
    _refresh_style(widget)


def clear_validation_error(widget: QWidget) -> None:
    set_validation_error(widget, None)


def set_widgets_enabled(
    widgets: Iterable[QWidget],
    enabled: bool,
) -> None:
    if isinstance(widgets, (str, bytes, bytearray, Mapping)):
        raise TypeError("widgets must be an iterable of QWidget values")
    for widget in widgets:
        if not isinstance(widget, QWidget):
            raise TypeError("widgets must contain QWidget values")
        widget.setEnabled(bool(enabled))


def _clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            break
        child_layout = item.layout()
        child_widget = item.widget()
        if child_layout is not None:
            _clear_layout(child_layout)
            child_layout.deleteLater()
        if child_widget is not None:
            child_widget.deleteLater()


def _refresh_style(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _coerce_path(value: Path | str) -> Path:
    if not isinstance(value, (Path, str)):
        raise TypeError("path must be pathlib.Path or str")
    text = str(value)
    _require_text(
        text,
        field="path",
        max_length=_MAX_PATH_LENGTH,
    )
    return Path(text)


def _require_text(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
    max_length: int = _MAX_TEXT_LENGTH,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds the supported length")
    return value


def _require_non_negative_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _require_positive_int(
    value: object,
    *,
    field: str,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1 or value > maximum:
        raise ValueError(f"{field} must be between 1 and {maximum}")
    return value


__all__ = (
    "BoundedActivityView",
    "CollapsibleSection",
    "ElidingLabel",
    "EmptyState",
    "InlineMessage",
    "KeyValueItem",
    "KeyValueView",
    "MessageSeverity",
    "PathField",
    "PresentationStatus",
    "ProgressPresentation",
    "ProgressWidget",
    "SelectableValue",
    "StatusBadge",
    "clear_validation_error",
    "install_copy_shortcut",
    "set_validation_error",
    "set_widgets_enabled",
)
