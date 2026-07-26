"""Artifact navigation panel for the GF Wordbench desktop GUI."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

_MAX_ITEMS: Final[int] = 10_000
_MAX_VISIBLE_ITEMS: Final[int] = 2_000
_MAX_TEXT_LENGTH: Final[int] = 4_096
_ITEM_ID_ROLE: Final[int] = int(Qt.ItemDataRole.UserRole)


@unique
class ArtifactAction(StrEnum):
    RUN_DIRECTORY = "run_directory"
    MACHINE_SUMMARY = "machine_summary"
    HUMAN_SUMMARY = "human_summary"
    AI_READY_PACKET = "ai_ready_packet"
    MASTER_LOG = "master_log"
    ALL_OPERATION_LOGS = "all_operation_logs"
    ALL_SCAN_LOGS = "all_scan_logs"
    MANIFEST = "manifest"
    PGF_DIRECTORY = "pgf_directory"
    SCENARIO_OUTPUT = "scenario_output"
    GOLD_DIFF = "gold_diff"
    DETAIL_REPORT = "detail_report"
    OTHER = "other"


@unique
class ArtifactTargetKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


@unique
class ArtifactIntegrity(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    NOT_CHECKED = "not_checked"


_CORE_ACTION_ORDER: Final[tuple[ArtifactAction, ...]] = (
    ArtifactAction.RUN_DIRECTORY,
    ArtifactAction.MACHINE_SUMMARY,
    ArtifactAction.HUMAN_SUMMARY,
    ArtifactAction.AI_READY_PACKET,
    ArtifactAction.MASTER_LOG,
    ArtifactAction.ALL_OPERATION_LOGS,
    ArtifactAction.ALL_SCAN_LOGS,
    ArtifactAction.MANIFEST,
)

_ACTION_LABELS: Final[Mapping[ArtifactAction, str]] = MappingProxyType(
    {
        ArtifactAction.RUN_DIRECTORY: "Open Run Directory",
        ArtifactAction.MACHINE_SUMMARY: "Open Machine Summary",
        ArtifactAction.HUMAN_SUMMARY: "Open Human Summary",
        ArtifactAction.AI_READY_PACKET: "Open AI Ready Packet",
        ArtifactAction.MASTER_LOG: "Open Master Log",
        ArtifactAction.ALL_OPERATION_LOGS: "Open All Operation Logs",
        ArtifactAction.ALL_SCAN_LOGS: "Open All Scan Logs",
        ArtifactAction.MANIFEST: "Open Manifest",
        ArtifactAction.PGF_DIRECTORY: "PGF Directory",
        ArtifactAction.SCENARIO_OUTPUT: "Scenario Output",
        ArtifactAction.GOLD_DIFF: "Gold Diff",
        ArtifactAction.DETAIL_REPORT: "Detail Report",
        ArtifactAction.OTHER: "Artifact",
    }
)

_ACTION_ORDER: Final[Mapping[ArtifactAction, int]] = MappingProxyType(
    {
        action: index
        for index, action in enumerate(
            (
                *_CORE_ACTION_ORDER,
                ArtifactAction.PGF_DIRECTORY,
                ArtifactAction.SCENARIO_OUTPUT,
                ArtifactAction.GOLD_DIFF,
                ArtifactAction.DETAIL_REPORT,
                ArtifactAction.OTHER,
            )
        )
    }
)


@dataclass(frozen=True, slots=True)
class ArtifactLink:
    item_id: str
    action: ArtifactAction
    label: str
    target_kind: ArtifactTargetKind
    path: Path | None
    required: bool = False
    integrity: ArtifactIntegrity = ArtifactIntegrity.NOT_CHECKED
    detail: str = ""

    def __post_init__(self) -> None:
        item_id = _require_text(self.item_id, field="item_id")
        label = _require_text(self.label, field="label")
        detail = _require_text(
            self.detail,
            field="detail",
            allow_empty=True,
        )
        if not isinstance(self.action, ArtifactAction):
            raise TypeError("action must be ArtifactAction")
        if not isinstance(self.target_kind, ArtifactTargetKind):
            raise TypeError("target_kind must be ArtifactTargetKind")
        if self.path is not None:
            if not isinstance(self.path, Path):
                raise TypeError("path must be pathlib.Path or None")
            if not self.path.is_absolute():
                raise ValueError("artifact paths must be absolute")
            if "\x00" in str(self.path):
                raise ValueError("artifact path must not contain NUL")
        if type(self.required) is not bool:
            raise TypeError("required must be bool")
        if not isinstance(self.integrity, ArtifactIntegrity):
            raise TypeError("integrity must be ArtifactIntegrity")
        object.__setattr__(self, "item_id", item_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "detail", detail)

    @property
    def available(self) -> bool:
        if self.path is None:
            return False
        try:
            if self.target_kind is ArtifactTargetKind.FILE:
                return self.path.is_file()
            return self.path.is_dir()
        except OSError:
            return False


@dataclass(frozen=True, slots=True)
class ArtifactsPanelState:
    run_id: str | None = None
    items: tuple[ArtifactLink, ...] = ()
    integrity_message: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        run_id = self.run_id
        if run_id is not None:
            run_id = _require_text(run_id, field="run_id")
        if not isinstance(self.items, tuple):
            raise TypeError("items must be a tuple")
        if len(self.items) > _MAX_ITEMS:
            raise ValueError(f"items exceeds the supported limit of {_MAX_ITEMS}")
        if not all(isinstance(item, ArtifactLink) for item in self.items):
            raise TypeError("items must contain ArtifactLink values")
        item_ids = tuple(item.item_id for item in self.items)
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("artifact item IDs must be unique")
        for action in _CORE_ACTION_ORDER:
            if sum(item.action is action for item in self.items) > 1:
                raise ValueError(
                    f"core artifact action {action.value!r} must be unique"
                )
        integrity_message = _require_text(
            self.integrity_message,
            field="integrity_message",
            allow_empty=True,
        )
        if type(self.read_only) is not bool:
            raise TypeError("read_only must be bool")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "integrity_message", integrity_message)

    def item(self, item_id: str) -> ArtifactLink | None:
        checked = _require_text(item_id, field="item_id")
        return next((item for item in self.items if item.item_id == checked), None)

    def first_for_action(self, action: ArtifactAction) -> ArtifactLink | None:
        if not isinstance(action, ArtifactAction):
            raise TypeError("action must be ArtifactAction")
        return next((item for item in self.items if item.action is action), None)


PathOpener = Callable[[Path], bool]


class ArtifactsPanel(QWidget):
    path_opened = Signal(object)
    open_failed = Signal(str, str)
    availability_changed = Signal()
    selection_changed = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        path_opener: PathOpener | None = None,
    ) -> None:
        super().__init__(parent)
        self._state = ArtifactsPanelState()
        self._path_opener = path_opener or _open_local_path
        self._buttons: dict[ArtifactAction, QPushButton] = {}
        self._tree_items: dict[str, QTreeWidgetItem] = {}
        self._build_ui()
        self._render()

    @property
    def state(self) -> ArtifactsPanelState:
        return self._state

    def set_state(self, state: ArtifactsPanelState) -> None:
        if not isinstance(state, ArtifactsPanelState):
            raise TypeError("state must be ArtifactsPanelState")
        self._state = state
        self._render()

    def set_items(
        self,
        items: Iterable[ArtifactLink],
        *,
        run_id: str | None = None,
        integrity_message: str = "",
    ) -> None:
        if isinstance(items, (str, bytes, bytearray, Mapping)):
            raise TypeError("items must be an iterable of ArtifactLink values")
        self.set_state(
            ArtifactsPanelState(
                run_id=run_id,
                items=tuple(items),
                integrity_message=integrity_message,
            )
        )

    def clear(self) -> None:
        self.set_state(ArtifactsPanelState())

    def refresh_availability(self) -> None:
        self._render_availability()
        self.availability_changed.emit()

    def selected_item(self) -> ArtifactLink | None:
        current = self._tree.currentItem()
        if current is None:
            return None
        item_id = current.data(0, _ITEM_ID_ROLE)
        if not isinstance(item_id, str):
            return None
        return self._state.item(item_id)

    def open_selected(self) -> bool:
        selected = self.selected_item()
        if selected is None:
            self._show_notice("Select an artifact to open.", error=False)
            return False
        return self.open_item(selected.item_id)

    def open_action(self, action: ArtifactAction) -> bool:
        if not isinstance(action, ArtifactAction):
            raise TypeError("action must be ArtifactAction")
        item = self._state.first_for_action(action)
        if item is None:
            self._report_unavailable(
                _ACTION_LABELS[action],
                "No structured artifact reference is available.",
            )
            return False
        return self.open_item(item.item_id)

    def open_item(self, item_id: str) -> bool:
        item = self._state.item(item_id)
        if item is None:
            raise KeyError(f"unknown artifact item {item_id!r}")
        if item.path is None:
            self._report_unavailable(
                item.label,
                "The run result does not expose a path for this artifact.",
            )
            return False
        if not item.available:
            self._report_unavailable(
                item.label,
                "The referenced artifact is missing or unavailable.",
            )
            return False
        try:
            opened = self._path_opener(item.path)
        except Exception as exc:
            self._report_unavailable(
                item.label,
                f"{type(exc).__name__}: {_safe_message(str(exc))}",
            )
            return False
        if type(opened) is not bool:
            self._report_unavailable(
                item.label,
                "The local path opener returned an invalid result.",
            )
            return False
        if not opened:
            self._report_unavailable(
                item.label,
                "The operating system could not open the referenced path.",
            )
            return False
        self._show_notice(f"Opened: {item.path}", error=False)
        self.path_opened.emit(item.path)
        return True

    def _build_ui(self) -> None:
        self.setObjectName("artifactsPanel")
        self.setAccessibleName("Run artifacts")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QHBoxLayout()
        self._title = QLabel("Run artifacts", self)
        self._title.setObjectName("artifactsTitle")
        self._title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._run_label = QLabel("No completed run loaded", self)
        self._run_label.setObjectName("artifactsRunLabel")
        self._run_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        header.addWidget(self._title)
        header.addWidget(self._run_label)
        root.addLayout(header)

        self._integrity_label = QLabel(self)
        self._integrity_label.setObjectName("artifactsIntegrityLabel")
        self._integrity_label.setWordWrap(True)
        self._integrity_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        root.addWidget(self._integrity_label)

        core_group = QGroupBox("Primary artifacts", self)
        core_group.setObjectName("primaryArtifactsGroup")
        core_layout = QGridLayout(core_group)
        core_layout.setContentsMargins(8, 8, 8, 8)
        core_layout.setHorizontalSpacing(8)
        core_layout.setVerticalSpacing(8)

        for index, action in enumerate(_CORE_ACTION_ORDER):
            button = QPushButton(_ACTION_LABELS[action], core_group)
            button.setObjectName(f"artifactAction_{action.value}")
            button.setAccessibleName(_ACTION_LABELS[action])
            button.clicked.connect(
                lambda checked=False, selected_action=action: self.open_action(
                    selected_action
                )
            )
            row, column = divmod(index, 2)
            core_layout.addWidget(button, row, column)
            self._buttons[action] = button

        root.addWidget(core_group)

        self._tree = QTreeWidget(self)
        self._tree.setObjectName("artifactTree")
        self._tree.setAccessibleName("Additional run artifacts")
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(("Artifact", "Status", "Path"))
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tree.setSortingEnabled(False)
        self._tree.header().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self._tree.header().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self._tree.header().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        self._tree.itemDoubleClicked.connect(self._on_item_activated)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self._tree, 1)

        controls = QHBoxLayout()
        self._open_selected_button = QPushButton("Open Selected", self)
        self._open_selected_button.setObjectName("openSelectedArtifactButton")
        self._open_selected_button.clicked.connect(self.open_selected)
        self._refresh_button = QPushButton("Refresh Availability", self)
        self._refresh_button.setObjectName("refreshArtifactAvailabilityButton")
        self._refresh_button.clicked.connect(self.refresh_availability)
        controls.addWidget(self._open_selected_button)
        controls.addWidget(self._refresh_button)
        controls.addStretch(1)
        root.addLayout(controls)

        self._notice = QLabel(self)
        self._notice.setObjectName("artifactsNotice")
        self._notice.setWordWrap(True)
        self._notice.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        root.addWidget(self._notice)

    def _render(self) -> None:
        self._run_label.setText(
            f"Run: {self._state.run_id}"
            if self._state.run_id is not None
            else "No completed run loaded"
        )
        self._integrity_label.setText(self._state.integrity_message)
        self._integrity_label.setVisible(bool(self._state.integrity_message))
        self._notice.clear()
        self._render_core_actions()
        self._render_tree()
        self._render_availability()

    def _render_core_actions(self) -> None:
        for action, button in self._buttons.items():
            item = self._state.first_for_action(action)
            button.setProperty("artifactItemId", None if item is None else item.item_id)
            if item is None:
                button.setText(_ACTION_LABELS[action])
                button.setToolTip("No structured artifact reference is available.")
            else:
                button.setToolTip(_item_tooltip(item))

    def _render_tree(self) -> None:
        self._tree.clear()
        self._tree_items.clear()

        items = tuple(
            item
            for item in self._state.items
            if item.action not in _CORE_ACTION_ORDER
        )
        ordered = sorted(items, key=_artifact_sort_key)
        visible = ordered[:_MAX_VISIBLE_ITEMS]

        for artifact in visible:
            row = QTreeWidgetItem(
                (
                    artifact.label,
                    _status_text(artifact),
                    "" if artifact.path is None else str(artifact.path),
                )
            )
            row.setData(0, _ITEM_ID_ROLE, artifact.item_id)
            row.setToolTip(0, _item_tooltip(artifact))
            row.setToolTip(1, _item_tooltip(artifact))
            row.setToolTip(2, _item_tooltip(artifact))
            self._tree.addTopLevelItem(row)
            self._tree_items[artifact.item_id] = row

        omitted = len(ordered) - len(visible)
        if omitted > 0:
            self._show_notice(
                f"{omitted} additional artifacts are omitted from the bounded view.",
                error=False,
            )

    def _render_availability(self) -> None:
        for action, button in self._buttons.items():
            item = self._state.first_for_action(action)
            enabled = item is not None and item.available
            button.setEnabled(enabled)
            if item is not None:
                button.setText(_button_text(item))

        for item_id, row in self._tree_items.items():
            item = self._state.item(item_id)
            if item is None:
                continue
            row.setText(1, _status_text(item))
            row.setDisabled(not item.available)
            row.setIcon(0, self._icon_for(item))

        selected = self.selected_item()
        self._open_selected_button.setEnabled(
            selected is not None and selected.available
        )
        self._refresh_button.setEnabled(bool(self._state.items))

    def _icon_for(self, item: ArtifactLink):
        if not item.available:
            return self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        if item.target_kind is ArtifactTargetKind.DIRECTORY:
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def _on_item_activated(self, row: QTreeWidgetItem, column: int) -> None:
        del column
        item_id = row.data(0, _ITEM_ID_ROLE)
        if isinstance(item_id, str):
            self.open_item(item_id)

    def _on_selection_changed(self) -> None:
        selected = self.selected_item()
        self._open_selected_button.setEnabled(
            selected is not None and selected.available
        )
        self.selection_changed.emit(selected)

    def _report_unavailable(self, label: str, message: str) -> None:
        safe_label = _require_text(label, field="label")
        safe_message = _require_text(message, field="message")
        rendered = f"{safe_label}: {safe_message}"
        self._show_notice(rendered, error=True)
        self.open_failed.emit(safe_label, safe_message)

    def _show_notice(self, message: str, *, error: bool) -> None:
        checked = _require_text(message, field="message")
        self._notice.setText(checked)
        self._notice.setProperty("error", error)
        self._notice.style().unpolish(self._notice)
        self._notice.style().polish(self._notice)


def _artifact_sort_key(item: ArtifactLink) -> tuple[int, str, str]:
    return (
        _ACTION_ORDER[item.action],
        item.label.casefold(),
        item.item_id,
    )


def _button_text(item: ArtifactLink) -> str:
    base = _ACTION_LABELS[item.action]
    if item.required and not item.available:
        return f"{base} — Missing"
    if item.integrity is ArtifactIntegrity.FAILED:
        return f"{base} — Integrity Warning"
    if item.integrity is ArtifactIntegrity.UNVERIFIED:
        return f"{base} — Unverified"
    return base


def _status_text(item: ArtifactLink) -> str:
    if not item.available:
        return "Missing" if item.required else "Unavailable"
    if item.integrity is ArtifactIntegrity.VERIFIED:
        return "Verified"
    if item.integrity is ArtifactIntegrity.FAILED:
        return "Integrity warning"
    if item.integrity is ArtifactIntegrity.UNVERIFIED:
        return "Unverified"
    return "Available"


def _item_tooltip(item: ArtifactLink) -> str:
    parts = [item.label, _status_text(item)]
    if item.detail:
        parts.append(item.detail)
    if item.path is not None:
        parts.append(str(item.path))
    return "\n".join(parts)


def _open_local_path(path: Path) -> bool:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))))


def _safe_message(value: str) -> str:
    text = " ".join(value.replace("\x00", "\\x00").split())
    if not text:
        return "No diagnostic message was provided."
    if len(text) > _MAX_TEXT_LENGTH:
        return f"{text[: _MAX_TEXT_LENGTH - 3]}..."
    return text


def _require_text(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds the supported length")
    return value


__all__ = (
    "ArtifactAction",
    "ArtifactIntegrity",
    "ArtifactLink",
    "ArtifactTargetKind",
    "ArtifactsPanel",
    "ArtifactsPanelState",
    "PathOpener",
)
