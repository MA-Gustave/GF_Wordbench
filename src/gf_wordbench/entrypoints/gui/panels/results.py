"""Read-only presentation of one terminal GF Wordbench run result."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, Final

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    OverallStatus,
    ValidationStatus,
)

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import RunResult

__all__ = ("ResultsPanel",)

_MAX_DISPLAY_TEXT: Final[int] = 16_384
_MAX_ROWS: Final[int] = 100_000


@unique
class _EvidenceKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


@dataclass(frozen=True, slots=True)
class _ArtifactAction:
    key: str
    label: str
    path_attribute: str
    kind: _EvidenceKind


_ARTIFACT_ACTIONS: Final[tuple[_ArtifactAction, ...]] = (
    _ArtifactAction(
        "run_directory",
        "Open Run Directory",
        "run_dir",
        _EvidenceKind.DIRECTORY,
    ),
    _ArtifactAction(
        "machine_summary",
        "Open Machine Summary",
        "summary_json",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "human_summary",
        "Open Human Summary",
        "summary_md",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "ai_ready",
        "Open AI Ready Packet",
        "ai_ready_md",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "master_log",
        "Open Master Log",
        "master_log",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "all_operation_logs",
        "Open All Operation Logs",
        "all_logs",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "all_scan_logs",
        "Open All Scan Logs",
        "all_scan_logs",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "manifest",
        "Open Manifest",
        "manifest_json",
        _EvidenceKind.FILE,
    ),
    _ArtifactAction(
        "pgf_directory",
        "Open PGF Directory",
        "pgf_dir",
        _EvidenceKind.DIRECTORY,
    ),
)

_STATUS_WORDING: Final[Mapping[OverallStatus, str]] = {
    OverallStatus.OK: "Validation passed",
    OverallStatus.FAIL: "Validation completed with failures",
    OverallStatus.ERROR: "Validation error",
}

_CATEGORY_ORDER: Final[Mapping[str, int]] = {
    "Framework and environment errors": 0,
    "Direct failures": 1,
    "Required scenario failures": 2,
    "Ambiguous failures": 3,
    "Downstream failures": 4,
    "Gold mismatches": 5,
    "Artifact failures": 6,
    "Nonblocking scan findings": 7,
    "Regressions": 8,
}


@dataclass(frozen=True, slots=True)
class _DiagnosticRow:
    category: str
    status: str
    subject_kind: str
    subject: str
    message: str
    blocked_by: str
    evidence_path: Path | None

    def sort_key(self) -> tuple[int, str, str, str, str]:
        return (
            _CATEGORY_ORDER.get(self.category, 999),
            self.subject_kind.casefold(),
            self.subject.casefold(),
            self.status.casefold(),
            self.message.casefold(),
        )


@dataclass(frozen=True, slots=True)
class _TopErrorRow:
    count: int
    error_kind: str
    message: str
    subject_kinds: str


class _DiagnosticTableModel(QAbstractTableModel):
    _HEADERS: Final[tuple[str, ...]] = (
        "Category",
        "Status",
        "Subject Type",
        "Subject",
        "Message",
        "Blocked By",
        "Evidence",
    )

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[_DiagnosticRow, ...] = ()

    def set_rows(self, rows: Iterable[_DiagnosticRow]) -> None:
        prepared = tuple(rows)
        if len(prepared) > _MAX_ROWS:
            raise ValueError(f"diagnostic rows exceed {_MAX_ROWS}")
        if not all(isinstance(row, _DiagnosticRow) for row in prepared):
            raise TypeError("rows must contain _DiagnosticRow values")
        self.beginResetModel()
        self._rows = prepared
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        return 0 if parent.isValid() else len(self._HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        values = (
            row.category,
            row.status,
            row.subject_kind,
            row.subject,
            row.message,
            row.blocked_by,
            "" if row.evidence_path is None else str(row.evidence_path),
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.ToolTipRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.UserRole:
            return row.evidence_path
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return ", ".join(
                part
                for part in (
                    row.category,
                    row.status,
                    row.subject_kind,
                    row.subject,
                    row.message,
                )
                if part
            )
        if role == Qt.ItemDataRole.FontRole and index.column() == 1:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._HEADERS):
            return self._HEADERS[section]
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        return None

    def row_at(self, row: int) -> _DiagnosticRow | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


class _TopErrorsTableModel(QAbstractTableModel):
    _HEADERS: Final[tuple[str, ...]] = (
        "Count",
        "Error Kind",
        "Message",
        "Subject Types",
    )

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[_TopErrorRow, ...] = ()

    def set_rows(self, rows: Iterable[_TopErrorRow]) -> None:
        prepared = tuple(rows)
        if len(prepared) > _MAX_ROWS:
            raise ValueError(f"top-error rows exceed {_MAX_ROWS}")
        if not all(isinstance(row, _TopErrorRow) for row in prepared):
            raise TypeError("rows must contain _TopErrorRow values")
        self.beginResetModel()
        self._rows = prepared
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        return 0 if parent.isValid() else len(self._HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        values: tuple[object, ...] = (
            row.count,
            row.error_kind,
            row.message,
            row.subject_kinds,
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(values[index.column()])
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() == 0:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._HEADERS):
            return self._HEADERS[section]
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        return None


class ResultsPanel(QWidget):
    """Render a terminal ``RunResult`` without deriving validation semantics."""

    open_path_requested = Signal(object)
    unavailable_path_requested = Signal(str, object)
    result_rendered = Signal(object)
    result_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: RunResult | None = None
        self._artifact_paths: dict[str, Path] = {}
        self._artifact_buttons: dict[str, QPushButton] = {}

        self._diagnostic_model = _DiagnosticTableModel(self)
        self._top_errors_model = _TopErrorsTableModel(self)

        self._build_ui()
        self.clear_result()

    @property
    def current_result(self) -> RunResult | None:
        return self._result

    def _build_ui(self) -> None:
        self.setObjectName("results_panel")
        self.setAccessibleName("Validation results")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("results_status_label")
        self._status_label.setAccessibleName("Overall validation status")
        status_font = self._status_label.font()
        status_font.setBold(True)
        status_font.setPointSize(status_font.pointSize() + 2)
        self._status_label.setFont(status_font)
        self._status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._status_label)

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setObjectName("results_splitter")
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        summary_container = QWidget(splitter)
        summary_layout = QHBoxLayout(summary_container)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(8)

        summary_layout.addWidget(self._build_run_summary_group(), 1)
        summary_layout.addWidget(self._build_counts_group(), 1)
        summary_layout.addWidget(self._build_artifacts_group(), 1)
        splitter.addWidget(summary_container)

        self._tabs = QTabWidget(splitter)
        self._tabs.setObjectName("results_tabs")
        self._tabs.setAccessibleName("Result details")
        self._tabs.addTab(self._build_diagnostics_tab(), "Diagnostics")
        self._tabs.addTab(self._build_top_errors_tab(), "Top Errors")
        self._tabs.addTab(self._build_warnings_tab(), "Warnings")
        splitter.addWidget(self._tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    def _build_run_summary_group(self) -> QGroupBox:
        group = QGroupBox("Run Summary", self)
        group.setObjectName("run_summary_group")
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self._summary_labels: dict[str, QLabel] = {}
        fields = (
            ("mode", "Mode"),
            ("project", "Project"),
            ("run_id", "Run ID"),
            ("gf_version", "GF version"),
            ("duration", "Duration"),
            ("run_directory", "Run directory"),
        )
        for key, label_text in fields:
            value = QLabel(group)
            value.setObjectName(f"result_{key}_value")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setWordWrap(key in {"project", "run_directory"})
            value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            form.addRow(label_text, value)
            self._summary_labels[key] = value
        return group

    def _build_counts_group(self) -> QGroupBox:
        group = QGroupBox("Counts", self)
        group.setObjectName("result_counts_group")
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self._count_labels: dict[str, QLabel] = {}
        fields = (
            ("files", "Files OK / FAIL / ERROR / SKIPPED"),
            ("scenarios", "Scenarios OK / FAIL / ERROR / SKIPPED"),
            ("causality", "Direct / Downstream / Ambiguous"),
            ("required_scenarios", "Required scenario failures"),
            ("regressions", "Regressed / New / Improved / Removed"),
        )
        for key, label_text in fields:
            value = QLabel(group)
            value.setObjectName(f"result_{key}_count")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(label_text, value)
            self._count_labels[key] = value
        return group

    def _build_artifacts_group(self) -> QGroupBox:
        group = QGroupBox("Artifacts", self)
        group.setObjectName("result_artifacts_group")
        layout = QGridLayout(group)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        for index, action in enumerate(_ARTIFACT_ACTIONS):
            button = QPushButton(action.label, group)
            button.setObjectName(f"{action.key}_button")
            button.setAccessibleName(action.label)
            button.clicked.connect(
                lambda checked=False, key=action.key: self._request_artifact(key)
            )
            layout.addWidget(button, index // 2, index % 2)
            self._artifact_buttons[action.key] = button

        self._artifact_status = QLabel(group)
        self._artifact_status.setObjectName("artifact_status_label")
        self._artifact_status.setWordWrap(True)
        self._artifact_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(
            self._artifact_status,
            (len(_ARTIFACT_ACTIONS) + 1) // 2,
            0,
            1,
            2,
        )
        return group

    def _build_diagnostics_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        self._diagnostic_table = QTableView(tab)
        self._diagnostic_table.setObjectName("diagnostic_results_table")
        self._diagnostic_table.setAccessibleName("Categorized diagnostic results")
        self._diagnostic_table.setModel(self._diagnostic_model)
        self._configure_table(self._diagnostic_table)
        self._diagnostic_table.doubleClicked.connect(self._open_diagnostic_index)
        self._diagnostic_table.selectionModel().selectionChanged.connect(
            self._update_selected_evidence_button
        )
        layout.addWidget(self._diagnostic_table, 1)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self._open_selected_evidence_button = QPushButton(
            "Open Selected Evidence",
            tab,
        )
        self._open_selected_evidence_button.setObjectName("open_selected_evidence_button")
        self._open_selected_evidence_button.clicked.connect(self._open_selected_evidence)
        controls.addWidget(self._open_selected_evidence_button)
        layout.addLayout(controls)
        return tab

    def _build_top_errors_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self._top_errors_table = QTableView(tab)
        self._top_errors_table.setObjectName("top_errors_table")
        self._top_errors_table.setAccessibleName("Top errors")
        self._top_errors_table.setModel(self._top_errors_model)
        self._configure_table(self._top_errors_table)
        layout.addWidget(self._top_errors_table)
        return tab

    def _build_warnings_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        self._warnings_label = QLabel(tab)
        self._warnings_label.setObjectName("results_warnings_label")
        self._warnings_label.setAccessibleName("Run warnings")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._warnings_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._warnings_label, 1)
        return tab

    @staticmethod
    def _configure_table(table: QTableView) -> None:
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSortingEnabled(False)
        table.setWordWrap(False)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        if table.model() is not None and table.model().columnCount() >= 5:
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

    @Slot(object)
    def render_result(self, result: RunResult) -> None:
        self.set_result(result)

    def set_result(self, result: RunResult) -> None:
        self._validate_result_shape(result)
        self._result = result

        self._render_status(result)
        self._render_summary(result)
        self._render_counts(result)
        self._render_diagnostics(result)
        self._render_top_errors(result)
        self._render_warnings(result)
        self.refresh_artifact_availability()
        self.result_rendered.emit(result)

    @Slot()
    def clear_result(self) -> None:
        self._result = None
        self._artifact_paths.clear()
        self._status_label.setText("No completed run")
        self._status_label.setAccessibleDescription("No completed validation run is loaded")
        for label in self._summary_labels.values():
            label.setText("—")
        for label in self._count_labels.values():
            label.setText("0")
        self._diagnostic_model.set_rows(())
        self._top_errors_model.set_rows(())
        self._warnings_label.setText("No warnings")
        self._artifact_status.setText("No run artifacts are available.")
        for button in self._artifact_buttons.values():
            button.setEnabled(False)
        self._open_selected_evidence_button.setEnabled(False)
        self.result_cleared.emit()

    @Slot()
    def refresh_artifact_availability(self) -> None:
        self._artifact_paths.clear()
        result = self._result
        if result is None:
            for button in self._artifact_buttons.values():
                button.setEnabled(False)
            self._artifact_status.setText("No run artifacts are available.")
            return

        run_paths = result.run_paths
        available = 0
        missing: list[str] = []
        for action in _ARTIFACT_ACTIONS:
            raw = getattr(run_paths, action.path_attribute, None)
            path = raw if isinstance(raw, Path) else None
            safe = self._safe_existing_owned_path(path, action.kind)
            button = self._artifact_buttons[action.key]
            button.setEnabled(safe is not None)
            if safe is None:
                missing.append(action.label.removeprefix("Open "))
                button.setToolTip(
                    "Unavailable: the structured run result does not identify an "
                    "existing owned path for this action."
                )
            else:
                available += 1
                self._artifact_paths[action.key] = safe
                button.setToolTip(str(safe))

        if missing:
            self._artifact_status.setText(
                f"{available} artifact action(s) available; {len(missing)} unavailable."
            )
        else:
            self._artifact_status.setText(
                f"All {available} standard artifact actions are available."
            )

    def _render_status(self, result: RunResult) -> None:
        status = result.overall_status
        if not isinstance(status, OverallStatus):
            raise TypeError("result.overall_status must be OverallStatus")
        wording = _STATUS_WORDING[status]
        cancelled = bool(getattr(result, "cancelled", False))
        if cancelled:
            wording = "Run cancelled"
        self._status_label.setText(f"{wording} — {status.value}")
        self._status_label.setAccessibleDescription(f"Overall status {status.value}: {wording}")

    def _render_summary(self, result: RunResult) -> None:
        config = result.run_config
        paths = result.run_paths
        project = config.project
        mode = config.mode

        mode_text = _enum_text(mode).replace("_", " ").title()
        if project is not None:
            identity = project.identity
            project_name = _safe_text(identity.name, fallback="Unknown project")
            language_code = _safe_text(
                getattr(identity, "language_code", ""),
                fallback="",
            )
            if language_code:
                project_name = f"{project_name} ({language_code})"
        else:
            # ADR-0015 path-resolved runs intentionally do not require a
            # validation profile / ProjectConfig.  The resolved language context
            # is the identity authority for these runs, so the results UI must
            # not dereference the compatibility ``project`` alias unconditionally.
            context = getattr(config, "language_context", None)
            if context is None:
                project_name = "Resolved language"
            else:
                project_name = _safe_text(
                    getattr(context, "language_key", None),
                    fallback="Resolved language",
                )
                module_suffix = _safe_text(
                    getattr(context, "module_suffix", None),
                    fallback="",
                )
                if module_suffix:
                    project_name = f"{project_name} ({module_suffix})"

        self._summary_labels["mode"].setText(mode_text)
        self._summary_labels["project"].setText(project_name)
        self._summary_labels["run_id"].setText(_safe_text(paths.run_id, fallback="—"))
        self._summary_labels["gf_version"].setText(
            _safe_text(getattr(result, "gf_version", ""), fallback="Unknown")
        )
        self._summary_labels["duration"].setText(
            _format_duration_ms(result.duration_ms)
        )
        run_dir = paths.run_dir
        self._summary_labels["run_directory"].setText(str(run_dir))
        self._summary_labels["run_directory"].setToolTip(str(run_dir))

    def _render_counts(self, result: RunResult) -> None:
        totals = result.totals
        self._count_labels["files"].setText(
            " / ".join(
                str(_non_negative_count(getattr(totals, field)))
                for field in (
                    "files_ok",
                    "files_fail",
                    "files_error",
                    "files_skipped",
                )
            )
        )
        self._count_labels["scenarios"].setText(
            " / ".join(
                str(_non_negative_count(getattr(totals, field)))
                for field in (
                    "scenarios_ok",
                    "scenarios_fail",
                    "scenarios_error",
                    "scenarios_skipped",
                )
            )
        )
        self._count_labels["causality"].setText(
            " / ".join(
                str(_non_negative_count(getattr(totals, field)))
                for field in (
                    "direct_fail",
                    "downstream_fail",
                    "ambiguous_fail",
                )
            )
        )
        self._count_labels["required_scenarios"].setText(
            str(_non_negative_count(totals.required_scenario_fail))
        )

        changes = Counter(
            _enum_text(entry.change_kind) for entry in result.diff_entries
        )
        self._count_labels["regressions"].setText(
            " / ".join(
                str(changes[kind.value])
                for kind in (
                    ChangeKind.REGRESSED,
                    ChangeKind.NEW,
                    ChangeKind.IMPROVED,
                    ChangeKind.REMOVED,
                )
            )
        )

    def _render_diagnostics(self, result: RunResult) -> None:
        rows: list[_DiagnosticRow] = []
        run_root = result.run_paths.run_dir

        for file_result in result.file_results:
            status = file_result.status
            diagnostic_class = file_result.diagnostic_class
            if status is ValidationStatus.OK and diagnostic_class is DiagnosticClass.OK:
                continue
            subject = str(file_result.file_path)
            compile_summary = getattr(file_result, "compile_summary", None)
            message = _safe_text(
                getattr(file_result, "primary_message", "")
                or getattr(compile_summary, "first_error", ""),
                fallback="No normalized diagnostic message",
            )
            evidence = self._first_safe_evidence(
                run_root,
                (
                    getattr(compile_summary, "stderr_path", None),
                    getattr(compile_summary, "stdout_path", None),
                    getattr(file_result, "scan_log_path", None),
                ),
            )
            rows.append(
                _DiagnosticRow(
                    category=_diagnostic_category(
                        status=status,
                        diagnostic_class=diagnostic_class,
                        required_scenario=False,
                        gold_mismatch=False,
                    ),
                    status=_enum_text(status),
                    subject_kind="file",
                    subject=subject,
                    message=message,
                    blocked_by=_join_text(getattr(file_result, "blocked_by", ())),
                    evidence_path=evidence,
                )
            )

        for scenario in result.scenario_results:
            status = scenario.status
            diagnostic_class = scenario.diagnostic_class
            gold_mismatch = getattr(scenario, "gold_match", None) is False
            if status is ValidationStatus.OK and not gold_mismatch:
                continue
            evidence = self._first_safe_evidence(
                run_root,
                (
                    getattr(scenario, "gold_diff_path", None),
                    getattr(scenario, "stderr_path", None),
                    getattr(scenario, "stdout_path", None),
                    getattr(scenario, "normalized_output_path", None),
                ),
            )
            rows.append(
                _DiagnosticRow(
                    category=_diagnostic_category(
                        status=status,
                        diagnostic_class=diagnostic_class,
                        required_scenario=bool(getattr(scenario, "required", False)),
                        gold_mismatch=gold_mismatch,
                    ),
                    status=_enum_text(status),
                    subject_kind="scenario",
                    subject=_safe_text(
                        scenario.scenario_id,
                        fallback="unknown-scenario",
                    ),
                    message=_safe_text(
                        getattr(scenario, "primary_message", ""),
                        fallback="No normalized diagnostic message",
                    ),
                    blocked_by=_join_text(getattr(scenario, "blocked_by", ())),
                    evidence_path=evidence,
                )
            )

        for entry in result.diff_entries:
            change_kind = entry.change_kind
            if change_kind not in {ChangeKind.REGRESSED, ChangeKind.NEW}:
                continue
            rows.append(
                _DiagnosticRow(
                    category="Regressions",
                    status=_enum_text(change_kind),
                    subject_kind=_enum_text(entry.subject_kind),
                    subject=_safe_text(
                        entry.subject_id,
                        fallback="unknown-subject",
                    ),
                    message=_safe_text(
                        getattr(entry, "message", ""),
                        fallback="Regression detected",
                    ),
                    blocked_by="",
                    evidence_path=None,
                )
            )

        rows.sort(key=_DiagnosticRow.sort_key)
        self._diagnostic_model.set_rows(rows)
        self._open_selected_evidence_button.setEnabled(False)

    def _render_top_errors(self, result: RunResult) -> None:
        rows: list[_TopErrorRow] = []
        for record in result.top_errors:
            count = record.count
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ValueError("top error count must be a positive integer")
            subject_kinds = getattr(record, "subject_kinds", ())
            rows.append(
                _TopErrorRow(
                    count=count,
                    error_kind=_enum_text(record.error_kind),
                    message=_safe_text(
                        record.message,
                        fallback="Unknown diagnostic",
                    ),
                    subject_kinds=_join_text(subject_kinds),
                )
            )
        self._top_errors_model.set_rows(rows)

    def _render_warnings(self, result: RunResult) -> None:
        config = result.run_config
        warnings = tuple(
            _safe_text(value, fallback="")
            for value in getattr(config, "compatibility_warnings", ())
        )
        warnings = tuple(value for value in warnings if value)
        if warnings:
            self._warnings_label.setText("\n".join(f"• {warning}" for warning in warnings))
        else:
            self._warnings_label.setText("No warnings")

    @Slot(str)
    def _request_artifact(self, key: str) -> None:
        path = self._artifact_paths.get(key)
        if path is None:
            action = next(
                (item for item in _ARTIFACT_ACTIONS if item.key == key),
                None,
            )
            label = key if action is None else action.label
            expected = None
            if self._result is not None and action is not None:
                expected = getattr(
                    self._result.run_paths,
                    action.path_attribute,
                    None,
                )
            self._artifact_status.setText(
                f"{label} is unavailable. Open the run directory to inspect the available evidence."
            )
            self.unavailable_path_requested.emit(label, expected)
            return
        self.open_path_requested.emit(path)

    @Slot(QModelIndex)
    def _open_diagnostic_index(self, index: QModelIndex) -> None:
        row = self._diagnostic_model.row_at(index.row())
        if row is not None and row.evidence_path is not None:
            self.open_path_requested.emit(row.evidence_path)

    @Slot()
    def _open_selected_evidence(self) -> None:
        selection_model = self._diagnostic_table.selectionModel()
        rows = selection_model.selectedRows()
        if not rows:
            return
        row = self._diagnostic_model.row_at(rows[0].row())
        if row is not None and row.evidence_path is not None:
            self.open_path_requested.emit(row.evidence_path)

    @Slot()
    def _update_selected_evidence_button(self, *_: object) -> None:
        selection_model = self._diagnostic_table.selectionModel()
        enabled = False
        rows = selection_model.selectedRows()
        if rows:
            row = self._diagnostic_model.row_at(rows[0].row())
            enabled = row is not None and row.evidence_path is not None
        self._open_selected_evidence_button.setEnabled(enabled)

    def _first_safe_evidence(
        self,
        run_root: Path,
        candidates: Iterable[object],
    ) -> Path | None:
        for candidate in candidates:
            if not isinstance(candidate, Path):
                continue
            safe = _safe_existing_path(candidate, run_root, _EvidenceKind.FILE)
            if safe is not None:
                return safe
        return None

    def _safe_existing_owned_path(
        self,
        path: Path | None,
        kind: _EvidenceKind,
    ) -> Path | None:
        if path is None or self._result is None:
            return None
        run_root = self._result.run_paths.run_dir
        return _safe_existing_path(path, run_root, kind)

    @staticmethod
    def _validate_result_shape(result: object) -> None:
        if result is None:
            raise TypeError("result must not be None")
        required = (
            "run_config",
            "run_paths",
            "duration_ms",
            "gf_version",
            "overall_status",
            "file_results",
            "scenario_results",
            "diff_entries",
            "top_errors",
            "totals",
        )
        missing = tuple(name for name in required if not hasattr(result, name))
        if missing:
            raise TypeError(
                "result does not satisfy the RunResult contract; missing: " + ", ".join(missing)
            )


def _safe_existing_path(
    path: Path,
    run_root: Path,
    kind: _EvidenceKind,
) -> Path | None:
    try:
        if not path.exists() or not run_root.exists():
            return None
        resolved_root = run_root.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(resolved_root)
        if kind is _EvidenceKind.FILE and not resolved.is_file():
            return None
        if kind is _EvidenceKind.DIRECTORY and not resolved.is_dir():
            return None
        return resolved
    except (OSError, RuntimeError, ValueError):
        return None


def _diagnostic_category(
    *,
    status: object,
    diagnostic_class: object,
    required_scenario: bool,
    gold_mismatch: bool,
) -> str:
    if status is ValidationStatus.ERROR:
        return "Framework and environment errors"
    if gold_mismatch:
        return "Gold mismatches"
    if required_scenario and status is ValidationStatus.FAIL:
        return "Required scenario failures"
    if diagnostic_class is DiagnosticClass.DIRECT:
        return "Direct failures"
    if diagnostic_class is DiagnosticClass.AMBIGUOUS:
        return "Ambiguous failures"
    if diagnostic_class is DiagnosticClass.DOWNSTREAM:
        return "Downstream failures"
    if diagnostic_class is DiagnosticClass.NOISE:
        return "Nonblocking scan findings"
    return "Direct failures"


def _enum_text(value: object) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise TypeError(f"expected string enum value, got {type(value).__name__}")
    return _safe_text(raw, fallback="unknown")


def _safe_text(value: object, *, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).replace("\x00", "")
    text = " ".join(text.split())
    if not text:
        return fallback
    if len(text) > _MAX_DISPLAY_TEXT:
        return text[: _MAX_DISPLAY_TEXT - 14].rstrip() + " … [truncated]"
    return text


def _join_text(values: object) -> str:
    if values is None:
        return ""
    if isinstance(values, (str, bytes, bytearray)):
        return _safe_text(values, fallback="")
    if not isinstance(values, Iterable):
        return _safe_text(values, fallback="")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _safe_text(value, fallback="")
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return ", ".join(result)


def _non_negative_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("result count must be an integer")
    if value < 0:
        raise ValueError("result count must be non-negative")
    return value


def _format_duration_ms(value: object) -> str:
    duration_ms = _non_negative_count(value)
    total_seconds, milliseconds = divmod(duration_ms, 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    if minutes:
        return f"{minutes:d}:{seconds:02d}.{milliseconds:03d}"
    return f"{seconds:d}.{milliseconds:03d} s"
