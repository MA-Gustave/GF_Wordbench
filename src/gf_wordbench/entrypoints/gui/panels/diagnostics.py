"""Diagnostic-result panel for the GF Wordbench Qt entrypoint."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, TypeVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

__all__ = (
    "DiagnosticEvidenceAction",
    "DiagnosticEvidenceActionKind",
    "DiagnosticPanelGroup",
    "DiagnosticPanelItem",
    "DiagnosticPanelModel",
    "DiagnosticSourceLocation",
    "DiagnosticsPanel",
)
_MAX_IDENTIFIER: Final[int] = 256
_MAX_SUBJECT: Final[int] = 2_048
_MAX_MESSAGE: Final[int] = 8_192
_MAX_DETAIL: Final[int] = 32_768
_MAX_EXCERPT: Final[int] = 65_536
_MAX_ITEMS: Final[int] = 100_000
_DISPLAY_LIMIT: Final[int] = 48_000
_ITEM_ID_ROLE: Final[int] = int(Qt.ItemDataRole.UserRole)
_E = TypeVar("_E", bound=StrEnum)
_T = TypeVar("_T")


@unique
class DiagnosticPanelGroup(StrEnum):
    FRAMEWORK_ENVIRONMENT = "framework_environment"
    DIRECT_FAILURES = "direct_failures"
    REQUIRED_SCENARIO_FAILURES = "required_scenario_failures"
    AMBIGUOUS_FAILURES = "ambiguous_failures"
    DOWNSTREAM_FAILURES = "downstream_failures"
    GOLD_MISMATCHES = "gold_mismatches"
    ARTIFACT_FAILURES = "artifact_failures"
    NONBLOCKING_SCAN_FINDINGS = "nonblocking_scan_findings"
    REGRESSIONS = "regressions"


@unique
class DiagnosticEvidenceActionKind(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    SCAN_LOG = "scan_log"
    DETAIL_REPORT = "detail_report"
    SOURCE_LOCATION = "source_location"
    SCENARIO_OUTPUT = "scenario_output"
    GOLD_DIFF = "gold_diff"


_GROUP_ORDER: Final[tuple[DiagnosticPanelGroup, ...]] = tuple(DiagnosticPanelGroup)
_GROUP_TITLES: Final[dict[DiagnosticPanelGroup, str]] = {
    DiagnosticPanelGroup.FRAMEWORK_ENVIRONMENT: "Framework and environment errors",
    DiagnosticPanelGroup.DIRECT_FAILURES: "Direct failures",
    DiagnosticPanelGroup.REQUIRED_SCENARIO_FAILURES: "Required scenario failures",
    DiagnosticPanelGroup.AMBIGUOUS_FAILURES: "Ambiguous failures",
    DiagnosticPanelGroup.DOWNSTREAM_FAILURES: "Downstream failures",
    DiagnosticPanelGroup.GOLD_MISMATCHES: "Gold mismatches",
    DiagnosticPanelGroup.ARTIFACT_FAILURES: "Artifact failures",
    DiagnosticPanelGroup.NONBLOCKING_SCAN_FINDINGS: "Nonblocking scan findings",
    DiagnosticPanelGroup.REGRESSIONS: "Regressions",
}
_ACTION_LABELS: Final[dict[DiagnosticEvidenceActionKind, str]] = {
    DiagnosticEvidenceActionKind.STDOUT: "Open stdout",
    DiagnosticEvidenceActionKind.STDERR: "Open stderr",
    DiagnosticEvidenceActionKind.SCAN_LOG: "Open scan log",
    DiagnosticEvidenceActionKind.DETAIL_REPORT: "Open detail report",
    DiagnosticEvidenceActionKind.SOURCE_LOCATION: "Open source location",
    DiagnosticEvidenceActionKind.SCENARIO_OUTPUT: "Open scenario output",
    DiagnosticEvidenceActionKind.GOLD_DIFF: "Open gold diff",
}


@dataclass(frozen=True, slots=True)
class DiagnosticSourceLocation:
    path: Path
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _coerce_path(self.path, "path"))
        for name in ("line", "column", "end_line", "end_column"):
            _positive_or_none(getattr(self, name), name)
        if self.end_line is not None and self.line is None:
            raise ValueError("end_line requires line")
        if self.end_column is not None and self.column is None:
            raise ValueError("end_column requires column")
        if self.line is not None and self.end_line is not None and self.end_line < self.line:
            raise ValueError("end_line must not precede line")

    def display_text(self) -> str:
        result = self.path.as_posix()
        if self.line is not None:
            result += f":{self.line}"
            if self.column is not None:
                result += f":{self.column}"
        return result


@dataclass(frozen=True, slots=True)
class DiagnosticEvidenceAction:
    kind: DiagnosticEvidenceActionKind
    target: Path
    available: bool = True
    location: DiagnosticSourceLocation | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "kind",
            _coerce_enum(self.kind, DiagnosticEvidenceActionKind, "kind"),
        )
        object.__setattr__(self, "target", _coerce_path(self.target, "target"))
        if type(self.available) is not bool:
            raise TypeError("available must be bool")
        if self.location is not None and not isinstance(self.location, DiagnosticSourceLocation):
            raise TypeError("location must be DiagnosticSourceLocation or None")
        if self.kind is DiagnosticEvidenceActionKind.SOURCE_LOCATION and self.location is None:
            object.__setattr__(
                self,
                "location",
                DiagnosticSourceLocation(self.target),
            )

    @property
    def label(self) -> str:
        return _ACTION_LABELS[self.kind]

    def is_enabled(self) -> bool:
        return self.available and self.target.exists()


@dataclass(frozen=True, slots=True)
class DiagnosticPanelItem:
    item_id: str
    group: DiagnosticPanelGroup
    subject: str
    status: str
    message: str
    error_kind: str = ""
    diagnostic_class: str = ""
    detail: str = ""
    blockers: tuple[str, ...] = ()
    location: DiagnosticSourceLocation | None = None
    raw_excerpt: str = ""
    actions: tuple[DiagnosticEvidenceAction, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_id", _text(self.item_id, "item_id", _MAX_IDENTIFIER))
        object.__setattr__(
            self,
            "group",
            _coerce_enum(self.group, DiagnosticPanelGroup, "group"),
        )
        object.__setattr__(self, "subject", _text(self.subject, "subject", _MAX_SUBJECT))
        object.__setattr__(self, "status", _text(self.status, "status", _MAX_IDENTIFIER))
        object.__setattr__(self, "message", _text(self.message, "message", _MAX_MESSAGE))
        object.__setattr__(
            self,
            "error_kind",
            _optional_text(self.error_kind, "error_kind", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "diagnostic_class",
            _optional_text(self.diagnostic_class, "diagnostic_class", _MAX_IDENTIFIER),
        )
        object.__setattr__(self, "detail", _plain_text(self.detail, "detail", _MAX_DETAIL))
        object.__setattr__(
            self,
            "blockers",
            _unique_texts(self.blockers, "blockers", _MAX_SUBJECT),
        )
        if self.location is not None and not isinstance(self.location, DiagnosticSourceLocation):
            raise TypeError("location must be DiagnosticSourceLocation or None")
        object.__setattr__(
            self,
            "raw_excerpt",
            _plain_text(self.raw_excerpt, "raw_excerpt", _MAX_EXCERPT),
        )
        actions = _typed_tuple(self.actions, DiagnosticEvidenceAction, "actions")
        kinds = tuple(action.kind for action in actions)
        if len(kinds) != len(set(kinds)):
            raise ValueError("actions must contain unique action kinds")
        object.__setattr__(self, "actions", actions)

    def searchable_text(self) -> str:
        location = "" if self.location is None else self.location.display_text()
        return " ".join(
            (
                _GROUP_TITLES[self.group],
                self.subject,
                self.status,
                self.error_kind,
                self.diagnostic_class,
                self.message,
                self.detail,
                " ".join(self.blockers),
                location,
            )
        ).casefold()


@dataclass(frozen=True, slots=True)
class DiagnosticPanelModel:
    items: tuple[DiagnosticPanelItem, ...] = ()
    selected_item_id: str | None = None

    def __post_init__(self) -> None:
        items = _typed_tuple(self.items, DiagnosticPanelItem, "items")
        if len(items) > _MAX_ITEMS:
            raise ValueError(f"items must contain at most {_MAX_ITEMS} entries")
        identifiers = tuple(item.item_id for item in items)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("items contain duplicate item IDs")
        if self.selected_item_id is not None:
            selected = _text(
                self.selected_item_id,
                "selected_item_id",
                _MAX_IDENTIFIER,
            )
            if selected not in set(identifiers):
                raise ValueError("selected_item_id does not identify an item")
            object.__setattr__(self, "selected_item_id", selected)
        object.__setattr__(self, "items", items)


class DiagnosticsPanel(QWidget):
    evidence_action_requested = Signal(object)
    selected_item_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = DiagnosticPanelModel()
        self._items_by_id: dict[str, DiagnosticPanelItem] = {}
        self._current_actions: dict[
            DiagnosticEvidenceActionKind,
            DiagnosticEvidenceAction,
        ] = {}
        self._action_buttons: dict[
            DiagnosticEvidenceActionKind,
            QPushButton,
        ] = {}
        self._build_ui()
        self._connect_signals()
        self._render()

    def model(self) -> DiagnosticPanelModel:
        return self._model

    def set_model(self, model: DiagnosticPanelModel) -> None:
        if not isinstance(model, DiagnosticPanelModel):
            raise TypeError("model must be DiagnosticPanelModel")
        self._model = model
        self._items_by_id = {item.item_id: item for item in model.items}
        self._render()
        if model.selected_item_id is not None:
            self.select_item(model.selected_item_id)

    def set_items(
        self,
        items: Iterable[DiagnosticPanelItem],
        *,
        selected_item_id: str | None = None,
    ) -> None:
        self.set_model(DiagnosticPanelModel(tuple(items), selected_item_id))

    def clear(self) -> None:
        self.set_model(DiagnosticPanelModel())

    def selected_item(self) -> DiagnosticPanelItem | None:
        current: object = self._tree.currentItem()
        if not isinstance(current, QTreeWidgetItem):
            return None
        item_id = current.data(0, _ITEM_ID_ROLE)
        return self._items_by_id.get(item_id) if isinstance(item_id, str) else None

    def select_item(self, item_id: str) -> bool:
        canonical = _text(item_id, "item_id", _MAX_IDENTIFIER)
        root = self._tree.invisibleRootItem()
        for group_index in range(root.childCount()):
            group = root.child(group_index)
            for row_index in range(group.childCount()):
                row = group.child(row_index)
                if row.data(0, _ITEM_ID_ROLE) == canonical:
                    self._tree.setCurrentItem(row)
                    self._tree.scrollToItem(row)
                    return True
        return False

    def refresh_action_availability(self) -> None:
        self._update_actions(self.selected_item())

    def _build_ui(self) -> None:
        self.setObjectName("diagnosticsPanel")
        self.setAccessibleName(self.tr("Diagnostic results"))
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self._summary = QLabel(self)
        self._summary.setAccessibleName(self.tr("Diagnostic result count"))
        controls.addWidget(self._summary)
        controls.addStretch(1)
        self._group_filter = QComboBox(self)
        self._group_filter.setAccessibleName(self.tr("Diagnostic category filter"))
        self._group_filter.addItem(self.tr("All diagnostic categories"), None)
        for group in _GROUP_ORDER:
            self._group_filter.addItem(self.tr(_GROUP_TITLES[group]), group)
        controls.addWidget(self._group_filter)
        self._search = QLineEdit(self)
        self._search.setAccessibleName(self.tr("Search diagnostic results"))
        self._search.setPlaceholderText(self.tr("Search diagnostics"))
        self._search.setClearButtonEnabled(True)
        controls.addWidget(self._search)
        layout.addLayout(controls)
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setChildrenCollapsible(False)
        self._tree = self._build_tree(splitter)
        detail = self._build_detail(splitter)
        splitter.addWidget(self._tree)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def _build_tree(self, parent: QWidget) -> QTreeWidget:
        tree = QTreeWidget(parent)
        tree.setAccessibleName(self.tr("Diagnostic result table"))
        tree.setColumnCount(6)
        tree.setHeaderLabels(
            (
                self.tr("Subject"),
                self.tr("Status"),
                self.tr("Error kind"),
                self.tr("Class"),
                self.tr("Message"),
                self.tr("Blocked by"),
            )
        )
        tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setAlternatingRowColors(True)
        tree.setUniformRowHeights(True)
        header = tree.header()
        for column in (0, 1, 2, 3, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        return tree

    def _build_detail(self, parent: QWidget) -> QWidget:
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        group = QGroupBox(self.tr("Diagnostic details"), container)
        group_layout = QVBoxLayout(group)
        fields = QWidget(group)
        form = QFormLayout(fields)
        self._detail_subject = QLabel(fields)
        self._detail_status = QLabel(fields)
        self._detail_location = QLabel(fields)
        for label in (self._detail_subject, self._detail_status, self._detail_location):
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow(self.tr("Subject"), self._detail_subject)
        form.addRow(self.tr("Status"), self._detail_status)
        form.addRow(self.tr("Location"), self._detail_location)
        group_layout.addWidget(fields)
        self._detail_text = QPlainTextEdit(group)
        self._detail_text.setAccessibleName(self.tr("Selected diagnostic details"))
        self._detail_text.setReadOnly(True)
        self._detail_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        group_layout.addWidget(self._detail_text)
        action_layout = QHBoxLayout()
        for kind in DiagnosticEvidenceActionKind:
            button = QPushButton(self.tr(_ACTION_LABELS[kind]), group)
            button.setAccessibleName(self.tr(_ACTION_LABELS[kind]))
            button.setEnabled(False)
            button.clicked.connect(lambda checked=False, value=kind: self._request_action(value))
            self._action_buttons[kind] = button
            action_layout.addWidget(button)
        action_layout.addStretch(1)
        group_layout.addLayout(action_layout)
        layout.addWidget(group)
        return container

    def _connect_signals(self) -> None:
        self._group_filter.currentIndexChanged.connect(self._render)
        self._search.textChanged.connect(self._render)
        self._tree.currentItemChanged.connect(self._selection_changed)

    def _render(self, *_: object) -> None:
        current = self.selected_item()
        selected_id = current.item_id if current is not None else self._model.selected_item_id
        selected_group = self._group_filter.currentData()
        query = self._search.text().strip().casefold()
        visible = 0
        self._tree.setUpdatesEnabled(False)
        self._tree.clear()
        for group in _GROUP_ORDER:
            if selected_group is not None and selected_group != group:
                continue
            items = tuple(
                item
                for item in self._model.items
                if item.group is group and (not query or query in item.searchable_text())
            )
            if not items:
                continue
            heading = QTreeWidgetItem((self.tr(_GROUP_TITLES[group]),))
            heading.setFlags(heading.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            heading.setFirstColumnSpanned(True)
            self._tree.addTopLevelItem(heading)
            for item in items:
                row = QTreeWidgetItem(
                    (
                        item.subject,
                        item.status,
                        item.error_kind,
                        item.diagnostic_class,
                        item.message,
                        ", ".join(item.blockers),
                    )
                )
                row.setData(0, _ITEM_ID_ROLE, item.item_id)
                row.setToolTip(4, item.message)
                heading.addChild(row)
                visible += 1
            heading.setExpanded(True)
        self._tree.setUpdatesEnabled(True)
        total = len(self._model.items)
        self._summary.setText(
            self.tr("%1 of %2 diagnostic results")
            .replace("%1", str(visible))
            .replace("%2", str(total))
        )
        restored = selected_id is not None and self.select_item(selected_id)
        if not restored:
            self._select_first()
        if self.selected_item() is None:
            self._show_item(None)

    def _select_first(self) -> None:
        root = self._tree.invisibleRootItem()
        for index in range(root.childCount()):
            group = root.child(index)
            if group.childCount():
                self._tree.setCurrentItem(group.child(0))
                return

    def _selection_changed(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        item_id = None if current is None else current.data(0, _ITEM_ID_ROLE)
        item = self._items_by_id.get(item_id) if isinstance(item_id, str) else None
        self._show_item(item)
        if item is not None:
            self.selected_item_changed.emit(item.item_id)

    def _show_item(self, item: DiagnosticPanelItem | None) -> None:
        if item is None:
            self._detail_subject.clear()
            self._detail_status.clear()
            self._detail_location.clear()
            self._detail_text.setPlainText(
                self.tr("Select a diagnostic result to inspect its details.")
            )
            self._update_actions(None)
            return
        status = [item.status]
        if item.error_kind:
            status.append(item.error_kind)
        if item.diagnostic_class:
            status.append(item.diagnostic_class)
        self._detail_subject.setText(item.subject)
        self._detail_status.setText(" · ".join(status))
        self._detail_location.setText(
            self.tr("Not available") if item.location is None else item.location.display_text()
        )
        self._detail_text.setPlainText(_detail_text(item))
        self._update_actions(item)

    def _update_actions(self, item: DiagnosticPanelItem | None) -> None:
        self._current_actions = (
            {} if item is None else {action.kind: action for action in item.actions}
        )
        for kind, button in self._action_buttons.items():
            action = self._current_actions.get(kind)
            button.setEnabled(action is not None and action.is_enabled())
            if action is None:
                tooltip = self.tr("No artifact is available for this result.")
            elif not action.available:
                tooltip = self.tr("This action is not available for this result.")
            elif not action.target.exists():
                tooltip = self.tr("The referenced artifact does not exist: %1").replace(
                    "%1", action.target.as_posix()
                )
            else:
                tooltip = action.target.as_posix()
            button.setToolTip(tooltip)

    def _request_action(self, kind: DiagnosticEvidenceActionKind) -> None:
        action = self._current_actions.get(kind)
        if action is not None and action.is_enabled():
            self.evidence_action_requested.emit(action)


def _detail_text(item: DiagnosticPanelItem) -> str:
    parts = [item.message]
    if item.detail:
        parts.extend(("", item.detail))
    if item.blockers:
        parts.extend(("", "Blocked by:", *(f"- {value}" for value in item.blockers)))
    if item.raw_excerpt:
        parts.extend(("", "Evidence excerpt:", item.raw_excerpt))
    text = "\n".join(parts)
    if len(text) <= _DISPLAY_LIMIT:
        return text
    omitted = len(text) - _DISPLAY_LIMIT
    return (
        text[:_DISPLAY_LIMIT]
        + f"\n\n[Diagnostic detail truncated in the GUI: {omitted} characters omitted]"
    )


def _coerce_enum(value: object, enum_type: type[_E], field: str) -> _E:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or {enum_type.__name__}")
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} has an unsupported value: {value!r}") from exc


def _text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    return _plain_text(value, field, maximum)


def _optional_text(value: object, field: str, maximum: int) -> str:
    return "" if value == "" else _text(value, field, maximum)


def _plain_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return value


def _coerce_path(value: object, field: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{field} must be a string or Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    return Path(value)


def _positive_or_none(value: object, field: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer or None")
    if value < 1:
        raise ValueError(f"{field} must be positive")


def _unique_texts(
    values: Iterable[str],
    field: str,
    maximum: int,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field} must be an iterable of strings")
    result = tuple(_text(value, f"{field} item", maximum) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    return result


def _typed_tuple(
    values: Iterable[_T],
    item_type: type[_T],
    field: str,
) -> tuple[_T, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field} must be an iterable")
    result = tuple(values)
    if not all(isinstance(value, item_type) for value in result):
        raise TypeError(f"{field} must contain only {item_type.__name__} values")
    return result
