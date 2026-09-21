"""Validation-selection panel for the GF Wordbench desktop GUI."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final

from PySide6.QtCore import QSignalBlocker, Qt, Signal, Slot
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.kernel.statuses import ValidationMode

_MODE_LABELS: Final[Mapping[ValidationMode, str]] = MappingProxyType(
    {
        ValidationMode.QUICK: "Quick",
        ValidationMode.CHECKPOINT: "Checkpoint",
        ValidationMode.RELEASE: "Release",
        ValidationMode.DIAGNOSTIC: "Diagnostic",
    }
)

_MAX_TEXT_LENGTH: Final[int] = 4096
_MAX_TIMEOUT_SECONDS: Final[int] = 86_400
_MAX_FILES: Final[int] = 1_000_000

_FIELD_MODE: Final[str] = "mode"
_FIELD_TARGET: Final[str] = "target_file"
_FIELD_CHECKPOINT: Final[str] = "checkpoint_id"
_FIELD_SCENARIOS: Final[str] = "scenario_filter"
_FIELD_TIMEOUT: Final[str] = "timeout_override"
_FIELD_MAX_FILES: Final[str] = "max_files"
_FIELD_NO_COMPILE: Final[str] = "no_compile"
_FIELD_SKIP_VERSION: Final[str] = "skip_version_probe"

_REQUIRED_RELEASE_CHECKPOINT_ID: Final[str] = "__all_required_checkpoints__"


@unique
class LocalIssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ValidationChoice:
    identifier: str
    label: str
    description: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "identifier",
            _required_text(self.identifier, field="identifier"),
        )
        object.__setattr__(
            self,
            "label",
            _required_text(self.label, field="label"),
        )
        object.__setattr__(
            self,
            "description",
            _optional_text(self.description, field="description"),
        )
        if type(self.enabled) is not bool:
            raise TypeError("enabled must be bool")


@dataclass(frozen=True, slots=True)
class ValidationPanelCatalog:
    targets: tuple[ValidationChoice, ...] = ()
    checkpoints: tuple[ValidationChoice, ...] = ()
    scenarios: tuple[ValidationChoice, ...] = ()
    checkpoint_scenarios: Mapping[str, tuple[str, ...]] = MappingProxyType({})
    release_scenarios: tuple[str, ...] = ()
    release_checkpoint_count: int = 0

    def __post_init__(self) -> None:
        targets = _choice_tuple(self.targets, field="targets")
        checkpoints = _choice_tuple(self.checkpoints, field="checkpoints")
        scenarios = _choice_tuple(self.scenarios, field="scenarios")
        checkpoint_scenarios = _freeze_checkpoint_scenarios(
            self.checkpoint_scenarios,
            checkpoints=checkpoints,
            scenarios=scenarios,
        )
        release_scenarios = _identifier_tuple(
            self.release_scenarios,
            field="release_scenarios",
        )
        known_scenarios = {choice.identifier for choice in scenarios}
        unknown_release = set(release_scenarios).difference(known_scenarios)
        if unknown_release:
            rendered = ", ".join(sorted(unknown_release))
            raise ValueError(f"release_scenarios contains unknown IDs: {rendered}")
        if type(self.release_checkpoint_count) is not int:
            raise TypeError("release_checkpoint_count must be int")
        if self.release_checkpoint_count < 0:
            raise ValueError("release_checkpoint_count must be non-negative")
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "checkpoints", checkpoints)
        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "checkpoint_scenarios", checkpoint_scenarios)
        object.__setattr__(self, "release_scenarios", release_scenarios)


@dataclass(frozen=True, slots=True)
class ValidationPanelValues:
    mode: ValidationMode = ValidationMode.CHECKPOINT
    target_file: str | None = None
    checkpoint_id: str | None = None
    scenario_filter: tuple[str, ...] = ()
    timeout_override: int | None = None
    keep_ok_details: bool = False
    diff_previous: bool = True
    skip_version_probe: bool = False
    no_compile: bool = False
    emit_cpu_stats: bool = False
    strict: bool = False
    verbose_gf_output: bool = False
    max_files: int | None = None

    def __post_init__(self) -> None:
        raw_mode: object = object.__getattribute__(self, "mode")
        if not isinstance(raw_mode, ValidationMode):
            object.__setattr__(self, "mode", ValidationMode(raw_mode))
        object.__setattr__(
            self,
            "target_file",
            _optional_identifier_text(self.target_file, field="target_file"),
        )
        object.__setattr__(
            self,
            "checkpoint_id",
            _optional_identifier_text(
                self.checkpoint_id,
                field="checkpoint_id",
            ),
        )
        object.__setattr__(
            self,
            "scenario_filter",
            _identifier_tuple(
                self.scenario_filter,
                field="scenario_filter",
            ),
        )
        object.__setattr__(
            self,
            "timeout_override",
            _optional_positive_int(
                self.timeout_override,
                field="timeout_override",
                maximum=_MAX_TIMEOUT_SECONDS,
            ),
        )
        object.__setattr__(
            self,
            "max_files",
            _optional_positive_int(
                self.max_files,
                field="max_files",
                maximum=_MAX_FILES,
            ),
        )
        for field_name in (
            "keep_ok_details",
            "diff_previous",
            "skip_version_probe",
            "no_compile",
            "emit_cpu_stats",
            "strict",
            "verbose_gf_output",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be bool")


@dataclass(frozen=True, slots=True)
class ValidationLocalIssue:
    field: str
    message: str
    severity: LocalIssueSeverity = LocalIssueSeverity.ERROR
    code: str = "invalid_value"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field",
            _required_text(self.field, field="field"),
        )
        object.__setattr__(
            self,
            "message",
            _required_text(self.message, field="message"),
        )
        object.__setattr__(
            self,
            "code",
            _required_text(self.code, field="code"),
        )
        raw_severity: object = object.__getattribute__(self, "severity")
        if not isinstance(raw_severity, LocalIssueSeverity):
            object.__setattr__(
                self,
                "severity",
                LocalIssueSeverity(raw_severity),
            )


@dataclass(frozen=True, slots=True)
class ValidationLocalResult:
    issues: tuple[ValidationLocalIssue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be tuple")
        if not all(isinstance(item, ValidationLocalIssue) for item in self.issues):
            raise TypeError("issues must contain ValidationLocalIssue values")

    @property
    def errors(self) -> tuple[ValidationLocalIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is LocalIssueSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationLocalIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is LocalIssueSeverity.WARNING)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def first_error_field(self) -> str | None:
        return self.errors[0].field if self.errors else None


class ValidationPanel(QWidget):
    values_changed = Signal(object)
    mode_changed = Signal(str)
    validation_changed = Signal(object)
    browse_target_requested = Signal()
    preview_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("validationPanel")
        self.setAccessibleName("Validation")

        self._catalog = ValidationPanelCatalog()
        self._external_issues: tuple[ValidationLocalIssue, ...] = ()
        self._running = False
        self._loading = False
        self._active_mode = ValidationMode.CHECKPOINT
        self._scenario_selection_by_mode: dict[
            ValidationMode,
            set[str],
        ] = {mode: set() for mode in ValidationMode}

        self._build_ui()
        self._connect_signals()
        self.set_catalog(self._catalog)
        self.set_values(ValidationPanelValues())

    @property
    def catalog(self) -> ValidationPanelCatalog:
        return self._catalog

    @property
    def running(self) -> bool:
        return self._running

    def values(self) -> ValidationPanelValues:
        mode = self.mode()
        target = self._normalized_combo_text(self.target_combo)
        checkpoint = self._selected_identifier(self.checkpoint_combo)
        selected_scenarios = self.selected_scenarios()

        if mode is ValidationMode.RELEASE:
            checkpoint = None
            selected_scenarios = self._catalog.release_scenarios

        timeout = self.timeout_spin.value() or None
        max_files = self.max_files_spin.value() or None

        return ValidationPanelValues(
            mode=mode,
            target_file=target,
            checkpoint_id=checkpoint,
            scenario_filter=selected_scenarios,
            timeout_override=timeout,
            keep_ok_details=self.keep_ok_checkbox.isChecked(),
            diff_previous=self.diff_previous_checkbox.isChecked(),
            skip_version_probe=self.skip_version_probe_checkbox.isChecked(),
            no_compile=self.scan_only_checkbox.isChecked(),
            emit_cpu_stats=self.cpu_stats_checkbox.isChecked(),
            strict=self.strict_checkbox.isChecked(),
            verbose_gf_output=self.verbose_output_checkbox.isChecked(),
            max_files=max_files,
        )

    def mode(self) -> ValidationMode:
        value = self.mode_combo.currentData(Qt.ItemDataRole.UserRole)
        if not isinstance(value, str):
            return ValidationMode.CHECKPOINT
        return ValidationMode(value)

    def selected_scenarios(self) -> tuple[str, ...]:
        selected: list[str] = []
        for index in range(self.scenario_list.count()):
            item = self.scenario_list.item(index)
            if item.isHidden():
                continue
            if item.checkState() == Qt.CheckState.Checked:
                identifier = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(identifier, str):
                    selected.append(identifier)
        return tuple(selected)

    def local_validation(self) -> ValidationLocalResult:
        values = self.values()
        issues: list[ValidationLocalIssue] = []

        if values.mode is ValidationMode.QUICK and values.target_file is None:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_TARGET,
                    code="target_required",
                    message="Select a target file or module for Quick validation.",
                )
            )

        if values.mode is ValidationMode.CHECKPOINT and values.checkpoint_id is None:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_CHECKPOINT,
                    code="checkpoint_required",
                    message="Select a declared checkpoint.",
                )
            )

        if values.checkpoint_id is not None:
            known_checkpoints = {choice.identifier for choice in self._catalog.checkpoints}
            if known_checkpoints and values.checkpoint_id not in known_checkpoints:
                issues.append(
                    ValidationLocalIssue(
                        field=_FIELD_CHECKPOINT,
                        code="checkpoint_unknown",
                        message="The selected checkpoint is not declared by the active project.",
                    )
                )

        known_scenarios = {choice.identifier for choice in self._catalog.scenarios}
        unknown_scenarios = set(values.scenario_filter).difference(known_scenarios)
        if unknown_scenarios:
            rendered = ", ".join(sorted(unknown_scenarios))
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_SCENARIOS,
                    code="scenario_unknown",
                    message=f"Unknown scenario selection: {rendered}.",
                )
            )

        if values.mode is ValidationMode.RELEASE and values.no_compile:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_NO_COMPILE,
                    code="release_compile_required",
                    message="Release validation cannot run in scan-only mode.",
                )
            )

        if values.mode is ValidationMode.RELEASE and values.skip_version_probe:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_SKIP_VERSION,
                    code="release_probe_required",
                    message="Release validation requires the GF version probe.",
                )
            )

        if values.mode is not ValidationMode.DIAGNOSTIC and values.max_files is not None:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_MAX_FILES,
                    code="max_files_mode",
                    message="Maximum files is available only in Diagnostic mode.",
                )
            )

        if values.mode is ValidationMode.DIAGNOSTIC and values.no_compile:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_NO_COMPILE,
                    severity=LocalIssueSeverity.WARNING,
                    code="scan_only_incomplete",
                    message=(
                        "Compilation-dependent conclusions are unavailable. "
                        "This run cannot satisfy checkpoint or release criteria."
                    ),
                )
            )

        if values.mode is ValidationMode.QUICK and values.skip_version_probe:
            issues.append(
                ValidationLocalIssue(
                    field=_FIELD_SKIP_VERSION,
                    severity=LocalIssueSeverity.WARNING,
                    code="version_probe_skipped",
                    message="The resolved plan may contain incomplete GF version evidence.",
                )
            )

        return ValidationLocalResult(issues=tuple(issues) + self._external_issues)

    def set_catalog(self, catalog: ValidationPanelCatalog) -> None:
        if not isinstance(catalog, ValidationPanelCatalog):
            raise TypeError("catalog must be ValidationPanelCatalog")

        previous = self.values() if hasattr(self, "mode_combo") else None
        self._catalog = catalog

        with self._block_widget_signals(
            self.target_combo,
            self.checkpoint_combo,
            self.scenario_list,
        ):
            self._populate_targets()
            self._populate_checkpoints()
            self._populate_scenarios()

        if previous is not None:
            self.set_values(previous)
        else:
            self._apply_mode(self._active_mode)

    def set_values(self, values: ValidationPanelValues) -> None:
        if not isinstance(values, ValidationPanelValues):
            raise TypeError("values must be ValidationPanelValues")

        self._loading = True
        try:
            with self._block_widget_signals(*self._input_widgets()):
                self._set_combo_data(
                    self.mode_combo,
                    values.mode.value,
                )
                self._set_editable_combo_text(
                    self.target_combo,
                    values.target_file,
                )
                self._set_combo_data(
                    self.checkpoint_combo,
                    values.checkpoint_id,
                )
                self.timeout_spin.setValue(values.timeout_override or 0)
                self.keep_ok_checkbox.setChecked(values.keep_ok_details)
                self.diff_previous_checkbox.setChecked(values.diff_previous)
                self.skip_version_probe_checkbox.setChecked(values.skip_version_probe)
                self.scan_only_checkbox.setChecked(values.no_compile)
                self.cpu_stats_checkbox.setChecked(values.emit_cpu_stats)
                self.strict_checkbox.setChecked(values.strict)
                self.verbose_output_checkbox.setChecked(values.verbose_gf_output)
                self.max_files_spin.setValue(values.max_files or 0)

                self._scenario_selection_by_mode[values.mode] = set(values.scenario_filter)
                self._active_mode = values.mode
                self._apply_mode(values.mode)
        finally:
            self._loading = False

        self._refresh_validation(emit_values=True)

    def set_external_issues(
        self,
        issues: Iterable[ValidationLocalIssue],
    ) -> None:
        prepared = tuple(issues)
        if not all(isinstance(issue, ValidationLocalIssue) for issue in prepared):
            raise TypeError("issues must contain ValidationLocalIssue values")
        self._external_issues = prepared
        self._refresh_validation(emit_values=False)

    def clear_external_issues(self) -> None:
        if not self._external_issues:
            return
        self._external_issues = ()
        self._refresh_validation(emit_values=False)

    def set_running(self, running: bool) -> None:
        if type(running) is not bool:
            raise TypeError("running must be bool")
        self._running = running
        self._apply_mode(self.mode())

    def focus_field(self, field: str) -> bool:
        widget = self._field_widget(field)
        if widget is None:
            return False
        widget.setFocus(Qt.FocusReason.OtherFocusReason)
        return True

    def focus_first_error(self) -> bool:
        field = self.local_validation().first_error_field
        return field is not None and self.focus_field(field)

    def set_mode(self, mode: ValidationMode | str) -> None:
        canonical = mode if isinstance(mode, ValidationMode) else ValidationMode(mode)
        self._set_combo_data(self.mode_combo, canonical.value)
        self._on_mode_changed()

    def set_target_file(self, target_file: str | None) -> None:
        checked = _optional_identifier_text(
            target_file,
            field="target_file",
        )
        self._set_editable_combo_text(self.target_combo, checked)
        self._on_values_changed()

    def set_checkpoint_id(self, checkpoint_id: str | None) -> None:
        checked = _optional_identifier_text(
            checkpoint_id,
            field="checkpoint_id",
        )
        self._set_combo_data(self.checkpoint_combo, checked)
        self._on_checkpoint_changed()

    def set_selected_scenarios(
        self,
        scenario_ids: Iterable[str],
    ) -> None:
        selected = set(
            _identifier_tuple(
                tuple(scenario_ids),
                field="scenario_ids",
            )
        )
        self._scenario_selection_by_mode[self.mode()] = selected
        with self._block_widget_signals(self.scenario_list):
            self._apply_scenario_visibility_and_selection(self.mode())
        self._on_values_changed()

    @Slot()
    def _on_mode_changed(self) -> None:
        if self._loading:
            return

        previous_mode = self._active_mode
        self._scenario_selection_by_mode[previous_mode] = set(self.selected_scenarios())

        mode = self.mode()
        self._active_mode = mode
        self._external_issues = ()
        self._apply_mode(mode)
        self.mode_changed.emit(mode.value)
        self._refresh_validation(emit_values=True)

    @Slot()
    def _on_checkpoint_changed(self) -> None:
        if self._loading:
            return
        self._external_issues = ()
        if self.mode() is ValidationMode.CHECKPOINT:
            with self._block_widget_signals(self.scenario_list):
                self._apply_scenario_visibility_and_selection(ValidationMode.CHECKPOINT)
        self._refresh_validation(emit_values=True)

    @Slot()
    def _on_scenario_changed(self) -> None:
        if self._loading:
            return
        self._scenario_selection_by_mode[self.mode()] = set(self.selected_scenarios())
        self._external_issues = ()
        self._refresh_validation(emit_values=True)

    @Slot()
    def _on_values_changed(self) -> None:
        if self._loading:
            return
        self._external_issues = ()
        self._refresh_validation(emit_values=True)

    @Slot(bool)
    def _toggle_advanced(self, visible: bool) -> None:
        self.advanced_frame.setVisible(visible)
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        form_group = QGroupBox("Validation", self)
        form_group.setObjectName("validationSelectionGroup")
        form_layout = QFormLayout(form_group)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.mode_combo = QComboBox(form_group)
        self.mode_combo.setObjectName("validationModeCombo")
        self.mode_combo.setAccessibleName("Validation mode")
        for mode in ValidationMode:
            self.mode_combo.addItem(
                _MODE_LABELS[mode],
                mode.value,
            )
        form_layout.addRow("Mode", self.mode_combo)

        self.target_label = QLabel("Target file or module", form_group)
        self.target_combo = QComboBox(form_group)
        self.target_combo.setObjectName("validationTargetCombo")
        self.target_combo.setAccessibleName("Target file or module")
        self.target_combo.setEditable(True)
        self.target_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.target_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.target_browse_button = QPushButton("Browse…", form_group)
        self.target_browse_button.setObjectName("validationTargetBrowseButton")
        self.target_browse_button.setAccessibleName("Browse for target file")
        target_row = QWidget(form_group)
        target_layout = QHBoxLayout(target_row)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(6)
        target_layout.addWidget(self.target_combo, 1)
        target_layout.addWidget(self.target_browse_button)
        self.target_row = target_row
        form_layout.addRow(self.target_label, target_row)

        self.checkpoint_label = QLabel("Checkpoint", form_group)
        self.checkpoint_combo = QComboBox(form_group)
        self.checkpoint_combo.setObjectName("validationCheckpointCombo")
        self.checkpoint_combo.setAccessibleName("Checkpoint")
        self.checkpoint_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        form_layout.addRow(self.checkpoint_label, self.checkpoint_combo)

        root.addWidget(form_group)

        scenario_group = QGroupBox("Scenario scope", self)
        scenario_group.setObjectName("validationScenarioGroup")
        scenario_layout = QVBoxLayout(scenario_group)
        self.scenario_hint = QLabel(
            "Leave optional scenarios unselected to use the resolved project defaults.",
            scenario_group,
        )
        self.scenario_hint.setWordWrap(True)
        self.scenario_hint.setObjectName("validationScenarioHint")
        scenario_layout.addWidget(self.scenario_hint)

        self.scenario_list = QListWidget(scenario_group)
        self.scenario_list.setObjectName("validationScenarioList")
        self.scenario_list.setAccessibleName("Scenario filter")
        self.scenario_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.scenario_list.setMinimumHeight(72)
        self.scenario_list.setMaximumHeight(120)
        scenario_layout.addWidget(self.scenario_list)
        root.addWidget(scenario_group)

        option_group = QGroupBox("Main options", self)
        option_group.setObjectName("validationOptionsGroup")
        option_layout = QGridLayout(option_group)

        self.scan_only_checkbox = QCheckBox("Scan only", option_group)
        self.scan_only_checkbox.setObjectName("validationScanOnlyCheck")
        self.keep_ok_checkbox = QCheckBox("Keep OK details", option_group)
        self.keep_ok_checkbox.setObjectName("validationKeepOkCheck")
        self.diff_previous_checkbox = QCheckBox(
            "Compare with previous compatible run",
            option_group,
        )
        self.diff_previous_checkbox.setObjectName("validationDiffPreviousCheck")
        self.cpu_stats_checkbox = QCheckBox(
            "Emit GF CPU statistics",
            option_group,
        )
        self.cpu_stats_checkbox.setObjectName("validationCpuStatsCheck")

        option_layout.addWidget(self.scan_only_checkbox, 0, 0)
        option_layout.addWidget(self.keep_ok_checkbox, 0, 1)
        option_layout.addWidget(self.diff_previous_checkbox, 1, 0)
        option_layout.addWidget(self.cpu_stats_checkbox, 1, 1)
        root.addWidget(option_group)

        self.advanced_toggle = QToolButton(self)
        self.advanced_toggle.setObjectName("validationAdvancedToggle")
        self.advanced_toggle.setText("Advanced Options")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        root.addWidget(self.advanced_toggle, 0, Qt.AlignmentFlag.AlignLeft)

        self.advanced_frame = QFrame(self)
        self.advanced_frame.setObjectName("validationAdvancedFrame")
        advanced_form = QFormLayout(self.advanced_frame)
        advanced_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.timeout_spin = QSpinBox(self.advanced_frame)
        self.timeout_spin.setObjectName("validationTimeoutSpin")
        self.timeout_spin.setAccessibleName("Timeout override")
        self.timeout_spin.setRange(0, _MAX_TIMEOUT_SECONDS)
        self.timeout_spin.setSpecialValueText("Project default")
        self.timeout_spin.setSuffix(" s")
        advanced_form.addRow("Timeout override", self.timeout_spin)

        self.max_files_spin = QSpinBox(self.advanced_frame)
        self.max_files_spin.setObjectName("validationMaxFilesSpin")
        self.max_files_spin.setAccessibleName("Maximum files")
        self.max_files_spin.setRange(0, _MAX_FILES)
        self.max_files_spin.setSpecialValueText("Unlimited")
        advanced_form.addRow("Maximum files", self.max_files_spin)

        self.skip_version_probe_checkbox = QCheckBox(
            "Skip GF version probe",
            self.advanced_frame,
        )
        self.skip_version_probe_checkbox.setObjectName("validationSkipVersionProbeCheck")
        advanced_form.addRow("", self.skip_version_probe_checkbox)

        self.verbose_output_checkbox = QCheckBox(
            "Verbose GF output",
            self.advanced_frame,
        )
        self.verbose_output_checkbox.setObjectName("validationVerboseOutputCheck")
        advanced_form.addRow("", self.verbose_output_checkbox)

        self.strict_checkbox = QCheckBox(
            "Strict mode",
            self.advanced_frame,
        )
        self.strict_checkbox.setObjectName("validationStrictCheck")
        advanced_form.addRow("", self.strict_checkbox)

        self.advanced_frame.setVisible(False)
        root.addWidget(self.advanced_frame)

        self.scan_only_notice = QLabel(
            "Compilation-dependent conclusions are unavailable. "
            "This run cannot satisfy checkpoint or release criteria.",
            self,
        )
        self.scan_only_notice.setObjectName("validationScanOnlyNotice")
        self.scan_only_notice.setWordWrap(True)
        self.scan_only_notice.setVisible(False)
        root.addWidget(self.scan_only_notice)

        self.validation_summary = QLabel(self)
        self.validation_summary.setObjectName("validationErrorSummary")
        self.validation_summary.setAccessibleName("Validation input messages")
        self.validation_summary.setWordWrap(True)
        self.validation_summary.setVisible(False)
        root.addWidget(self.validation_summary)

        self.preview_button = QPushButton("Refresh Resolved Plan", self)
        self.preview_button.setObjectName("validationPreviewButton")
        self.preview_button.setAccessibleName("Refresh resolved plan")
        root.addWidget(
            self.preview_button,
            0,
            Qt.AlignmentFlag.AlignRight,
        )

    def _connect_signals(self) -> None:
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.target_combo.currentTextChanged.connect(self._on_values_changed)
        self.target_browse_button.clicked.connect(self.browse_target_requested.emit)
        self.checkpoint_combo.currentIndexChanged.connect(self._on_checkpoint_changed)
        self.scenario_list.itemChanged.connect(self._on_scenario_changed)

        for checkbox in (
            self.scan_only_checkbox,
            self.keep_ok_checkbox,
            self.diff_previous_checkbox,
            self.cpu_stats_checkbox,
            self.skip_version_probe_checkbox,
            self.verbose_output_checkbox,
            self.strict_checkbox,
        ):
            checkbox.toggled.connect(self._on_values_changed)

        self.timeout_spin.valueChanged.connect(self._on_values_changed)
        self.max_files_spin.valueChanged.connect(self._on_values_changed)
        self.scan_only_checkbox.toggled.connect(self._update_scan_only_notice)
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        self.preview_button.clicked.connect(self.preview_requested.emit)

    def _populate_targets(self) -> None:
        self.target_combo.clear()
        for choice in self._catalog.targets:
            self.target_combo.addItem(
                choice.label,
                choice.identifier,
            )
            index = self.target_combo.count() - 1
            self.target_combo.setItemData(
                index,
                choice.description,
                Qt.ItemDataRole.ToolTipRole,
            )
            _set_combo_item_enabled(self.target_combo, index, choice.enabled)
        self.target_combo.setCurrentIndex(-1)
        self.target_combo.setEditText("")

    def _populate_checkpoints(self) -> None:
        self.checkpoint_combo.clear()
        self.checkpoint_combo.addItem("Select a checkpoint…", None)
        _set_combo_item_enabled(self.checkpoint_combo, 0, False)

        for choice in self._catalog.checkpoints:
            self.checkpoint_combo.addItem(
                choice.label,
                choice.identifier,
            )
            index = self.checkpoint_combo.count() - 1
            self.checkpoint_combo.setItemData(
                index,
                choice.description,
                Qt.ItemDataRole.ToolTipRole,
            )
            _set_combo_item_enabled(self.checkpoint_combo, index, choice.enabled)

        release_label = f"All required checkpoints ({self._catalog.release_checkpoint_count})"
        self.checkpoint_combo.addItem(
            release_label,
            _REQUIRED_RELEASE_CHECKPOINT_ID,
        )
        release_index = self.checkpoint_combo.count() - 1
        self.checkpoint_combo.setItemData(
            release_index,
            "Release validation uses the complete required checkpoint set.",
            Qt.ItemDataRole.ToolTipRole,
        )
        self.checkpoint_combo.setCurrentIndex(0)

    def _populate_scenarios(self) -> None:
        self.scenario_list.clear()
        for choice in self._catalog.scenarios:
            item = QListWidgetItem(choice.label)
            item.setData(
                Qt.ItemDataRole.UserRole,
                choice.identifier,
            )
            item.setToolTip(choice.description)
            flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            if choice.enabled:
                item.setFlags(flags)
            else:
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.scenario_list.addItem(item)

    def _apply_mode(self, mode: ValidationMode) -> None:
        enabled = not self._running

        target_visible = mode in {
            ValidationMode.QUICK,
            ValidationMode.DIAGNOSTIC,
        }
        checkpoint_visible = mode in {
            ValidationMode.CHECKPOINT,
            ValidationMode.RELEASE,
            ValidationMode.DIAGNOSTIC,
        }

        self.target_label.setVisible(target_visible)
        self.target_row.setVisible(target_visible)
        self.target_combo.setEnabled(enabled and target_visible)
        self.target_browse_button.setEnabled(enabled and target_visible)
        self.target_label.setText(
            "Target (optional; empty = Global Scan)"
            if mode is ValidationMode.DIAGNOSTIC
            else "Target file or module"
        )
        line_edit = self.target_combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(
                "All GF sources (Global Scan)"
                if mode is ValidationMode.DIAGNOSTIC
                else "Select a GF source file or module"
            )

        self.checkpoint_label.setVisible(checkpoint_visible)
        self.checkpoint_combo.setVisible(checkpoint_visible)

        if mode is ValidationMode.RELEASE:
            with self._block_widget_signals(self.checkpoint_combo):
                self._set_combo_data(
                    self.checkpoint_combo,
                    _REQUIRED_RELEASE_CHECKPOINT_ID,
                )
            self.checkpoint_combo.setEnabled(False)
        else:
            if self._selected_identifier(self.checkpoint_combo) == _REQUIRED_RELEASE_CHECKPOINT_ID:
                with self._block_widget_signals(self.checkpoint_combo):
                    self.checkpoint_combo.setCurrentIndex(0)
            self.checkpoint_combo.setEnabled(enabled and checkpoint_visible)

        scan_only_allowed = mode in {
            ValidationMode.QUICK,
            ValidationMode.DIAGNOSTIC,
        }
        self.scan_only_checkbox.setEnabled(enabled and scan_only_allowed)
        if not scan_only_allowed:
            with self._block_widget_signals(self.scan_only_checkbox):
                self.scan_only_checkbox.setChecked(False)

        skip_probe_allowed = mode in {
            ValidationMode.QUICK,
            ValidationMode.DIAGNOSTIC,
        }
        self.skip_version_probe_checkbox.setEnabled(enabled and skip_probe_allowed)
        if not skip_probe_allowed:
            with self._block_widget_signals(self.skip_version_probe_checkbox):
                self.skip_version_probe_checkbox.setChecked(False)

        self.max_files_spin.setEnabled(enabled and mode is ValidationMode.DIAGNOSTIC)
        if mode is not ValidationMode.DIAGNOSTIC:
            with self._block_widget_signals(self.max_files_spin):
                self.max_files_spin.setValue(0)

        self.strict_checkbox.setEnabled(enabled)
        if mode is ValidationMode.RELEASE:
            with self._block_widget_signals(self.strict_checkbox):
                self.strict_checkbox.setChecked(True)
            self.strict_checkbox.setEnabled(False)

        self.mode_combo.setEnabled(enabled)
        self.scenario_list.setEnabled(enabled)
        self.keep_ok_checkbox.setEnabled(enabled)
        self.diff_previous_checkbox.setEnabled(enabled)
        self.cpu_stats_checkbox.setEnabled(enabled)
        self.timeout_spin.setEnabled(enabled)
        self.verbose_output_checkbox.setEnabled(enabled)
        self.preview_button.setEnabled(enabled)
        self.advanced_toggle.setEnabled(enabled)

        with self._block_widget_signals(self.scenario_list):
            self._apply_scenario_visibility_and_selection(mode)

        self._update_mode_tooltips(mode)
        self._update_scan_only_notice(self.scan_only_checkbox.isChecked())

    def _apply_scenario_visibility_and_selection(
        self,
        mode: ValidationMode,
    ) -> None:
        visible_ids = self._visible_scenario_ids(mode)
        selected_ids = self._scenario_selection_by_mode[mode]

        if mode is ValidationMode.RELEASE:
            selected_ids = set(self._catalog.release_scenarios)
            self._scenario_selection_by_mode[mode] = selected_ids

        for index in range(self.scenario_list.count()):
            item = self.scenario_list.item(index)
            identifier = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(identifier, str):
                continue
            visible = identifier in visible_ids
            item.setHidden(not visible)
            item.setCheckState(
                Qt.CheckState.Checked if identifier in selected_ids else Qt.CheckState.Unchecked
            )
            choice = self._scenario_choice(identifier)
            enabled = (
                not self._running
                and mode is not ValidationMode.RELEASE
                and choice is not None
                and choice.enabled
            )
            flags = Qt.ItemFlag.ItemIsUserCheckable
            if enabled:
                flags |= Qt.ItemFlag.ItemIsEnabled
            item.setFlags(flags)

    def _visible_scenario_ids(
        self,
        mode: ValidationMode,
    ) -> frozenset[str]:
        all_ids = frozenset(choice.identifier for choice in self._catalog.scenarios)

        if mode is ValidationMode.RELEASE:
            return frozenset(self._catalog.release_scenarios)

        if mode is ValidationMode.CHECKPOINT:
            checkpoint_id = self._selected_identifier(self.checkpoint_combo)
            if checkpoint_id is None:
                return all_ids
            scoped = self._catalog.checkpoint_scenarios.get(checkpoint_id)
            if scoped is not None:
                return frozenset(scoped)

        return all_ids

    def _scenario_choice(
        self,
        identifier: str,
    ) -> ValidationChoice | None:
        return next(
            (choice for choice in self._catalog.scenarios if choice.identifier == identifier),
            None,
        )

    def _update_mode_tooltips(
        self,
        mode: ValidationMode,
    ) -> None:
        if mode is ValidationMode.QUICK:
            self.mode_combo.setToolTip(
                "Fast validation during editing. A target file or module is required."
            )
            self.scenario_hint.setText("Optionally select configured smoke scenarios.")
        elif mode is ValidationMode.CHECKPOINT:
            self.mode_combo.setToolTip("Validate a declared project subsystem.")
            self.scenario_hint.setText("Scenario choices are limited by the selected checkpoint.")
        elif mode is ValidationMode.RELEASE:
            self.mode_combo.setToolTip("Evaluate every declared release criterion.")
            self.scenario_hint.setText("The required release scenario set is read-only.")
        else:
            self.mode_combo.setToolTip(
                "Collect broad evidence. Leave Target empty to run a Global Scan over "
                "the complete resolved GF source inventory and continue after failures."
            )
            self.target_combo.setToolTip(
                "Optional in Diagnostic mode. Leave empty for Global Scan; choose a source "
                "to focus the diagnostic run."
            )
            self.scenario_hint.setText(
                "Global Scan inventories GF sources first. Optional configured scenarios "
                "remain a separate diagnostic scope."
            )

        self.scan_only_checkbox.setToolTip(
            "Skip compilation and collect scan evidence only."
            if mode in {ValidationMode.QUICK, ValidationMode.DIAGNOSTIC}
            else "Compilation is required by this validation mode."
        )
        self.skip_version_probe_checkbox.setToolTip(
            "The resolved plan may reject this override when version evidence is required."
            if mode is ValidationMode.QUICK
            else "Version probing may be skipped only in Diagnostic mode."
            if mode is ValidationMode.DIAGNOSTIC
            else "GF version probing is required by this validation mode."
        )

    @Slot(bool)
    def _update_scan_only_notice(self, checked: bool) -> None:
        self.scan_only_notice.setVisible(checked and self.mode() is ValidationMode.DIAGNOSTIC)

    def _refresh_validation(
        self,
        *,
        emit_values: bool,
    ) -> None:
        result = self.local_validation()
        self._render_validation(result)
        self.validation_changed.emit(result)
        if emit_values:
            self.values_changed.emit(self.values())

    def _render_validation(
        self,
        result: ValidationLocalResult,
    ) -> None:
        self._clear_field_messages()

        if not result.issues:
            self.validation_summary.clear()
            self.validation_summary.setVisible(False)
            return

        lines: list[str] = []
        for issue in result.issues:
            prefix = "Error" if issue.severity is LocalIssueSeverity.ERROR else "Warning"
            lines.append(f"{prefix}: {issue.message}")
            widget = self._field_widget(issue.field)
            if widget is not None:
                widget.setProperty(
                    "validationSeverity",
                    issue.severity.value,
                )
                widget.setToolTip(issue.message)
                widget.setAccessibleDescription(issue.message)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

        self.validation_summary.setText("\n".join(lines))
        self.validation_summary.setVisible(True)

    def _clear_field_messages(self) -> None:
        for field in (
            _FIELD_MODE,
            _FIELD_TARGET,
            _FIELD_CHECKPOINT,
            _FIELD_SCENARIOS,
            _FIELD_TIMEOUT,
            _FIELD_MAX_FILES,
            _FIELD_NO_COMPILE,
            _FIELD_SKIP_VERSION,
        ):
            widget = self._field_widget(field)
            if widget is None:
                continue
            widget.setProperty("validationSeverity", None)
            widget.setAccessibleDescription("")
            widget.setToolTip("")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self._update_mode_tooltips(self.mode())

    def _field_widget(self, field: str) -> QWidget | None:
        return {
            _FIELD_MODE: self.mode_combo,
            _FIELD_TARGET: self.target_combo,
            _FIELD_CHECKPOINT: self.checkpoint_combo,
            _FIELD_SCENARIOS: self.scenario_list,
            _FIELD_TIMEOUT: self.timeout_spin,
            _FIELD_MAX_FILES: self.max_files_spin,
            _FIELD_NO_COMPILE: self.scan_only_checkbox,
            _FIELD_SKIP_VERSION: self.skip_version_probe_checkbox,
        }.get(field)

    def _input_widgets(self) -> tuple[QWidget, ...]:
        return (
            self.mode_combo,
            self.target_combo,
            self.checkpoint_combo,
            self.scenario_list,
            self.timeout_spin,
            self.max_files_spin,
            self.scan_only_checkbox,
            self.keep_ok_checkbox,
            self.diff_previous_checkbox,
            self.cpu_stats_checkbox,
            self.skip_version_probe_checkbox,
            self.verbose_output_checkbox,
            self.strict_checkbox,
        )

    @staticmethod
    def _selected_identifier(combo: QComboBox) -> str | None:
        value = combo.currentData(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _normalized_combo_text(combo: QComboBox) -> str | None:
        data = combo.currentData(Qt.ItemDataRole.UserRole)
        if combo.currentIndex() >= 0 and isinstance(data, str) and data:
            return data
        value = combo.currentText().strip()
        return value or None

    @staticmethod
    def _set_combo_data(
        combo: QComboBox,
        value: str | None,
    ) -> None:
        if value is None:
            combo.setCurrentIndex(-1 if combo.isEditable() else 0)
            return
        index = combo.findData(
            value,
            role=Qt.ItemDataRole.UserRole,
        )
        combo.setCurrentIndex(index if index >= 0 else -1)

    @staticmethod
    def _set_editable_combo_text(
        combo: QComboBox,
        value: str | None,
    ) -> None:
        if value is None:
            combo.setCurrentIndex(-1)
            combo.setEditText("")
            return
        index = combo.findData(
            value,
            role=Qt.ItemDataRole.UserRole,
        )
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(-1)
            combo.setEditText(value)

    @contextmanager
    def _block_widget_signals(
        self,
        *widgets: QWidget,
    ) -> Iterator[None]:
        blockers = [QSignalBlocker(widget) for widget in widgets]
        try:
            yield
        finally:
            blockers.clear()


def _choice_tuple(
    values: Sequence[ValidationChoice],
    *,
    field: str,
) -> tuple[ValidationChoice, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be tuple")
    if not all(isinstance(item, ValidationChoice) for item in values):
        raise TypeError(f"{field} must contain ValidationChoice values")
    identifiers = [item.identifier for item in values]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{field} must contain unique identifiers")
    return values


def _freeze_checkpoint_scenarios(
    values: Mapping[str, tuple[str, ...]],
    *,
    checkpoints: tuple[ValidationChoice, ...],
    scenarios: tuple[ValidationChoice, ...],
) -> Mapping[str, tuple[str, ...]]:
    if not isinstance(values, Mapping):
        raise TypeError("checkpoint_scenarios must be a mapping")

    known_checkpoints = {choice.identifier for choice in checkpoints}
    known_scenarios = {choice.identifier for choice in scenarios}
    prepared: dict[str, tuple[str, ...]] = {}

    for checkpoint_id, scenario_ids in values.items():
        checked_checkpoint = _required_text(
            checkpoint_id,
            field="checkpoint ID",
        )
        if checked_checkpoint not in known_checkpoints:
            raise ValueError(
                f"checkpoint_scenarios contains unknown checkpoint {checked_checkpoint!r}"
            )
        checked_scenarios = _identifier_tuple(
            scenario_ids,
            field=f"checkpoint_scenarios[{checked_checkpoint!r}]",
        )
        unknown = set(checked_scenarios).difference(known_scenarios)
        if unknown:
            rendered = ", ".join(sorted(unknown))
            raise ValueError(
                f"checkpoint {checked_checkpoint!r} contains unknown scenario IDs: {rendered}"
            )
        prepared[checked_checkpoint] = checked_scenarios

    return MappingProxyType(dict(prepared))


def _identifier_tuple(
    values: Iterable[str],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field} must be an iterable of strings")

    prepared: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        checked = _required_text(
            value,
            field=f"{field}[{index}]",
        )
        if checked in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(checked)
        prepared.append(checked)
    return tuple(prepared)


def _set_combo_item_enabled(combo: QComboBox, index: int, enabled: bool) -> None:
    model = combo.model()
    if not isinstance(model, QStandardItemModel):
        raise TypeError("QComboBox must use a QStandardItemModel")
    item = model.item(index)
    if item is None:
        raise IndexError(f"combo item {index} does not exist")
    item.setEnabled(enabled)


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be str")
    checked = value.strip()
    if not checked:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in checked:
        raise ValueError(f"{field} must not contain NUL")
    if len(checked) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds the supported length")
    return checked


def _optional_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be str")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds the supported length")
    return value.strip()


def _optional_identifier_text(
    value: object,
    *,
    field: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be str or None")
    checked = value.strip()
    if not checked:
        return None
    if "\x00" in checked:
        raise ValueError(f"{field} must not contain NUL")
    if len(checked) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds the supported length")
    return checked


def _optional_positive_int(
    value: object,
    *,
    field: str,
    maximum: int,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{field} must be int or None")
    if value < 1 or value > maximum:
        raise ValueError(f"{field} must be between 1 and {maximum}")
    return value


__all__ = (
    "LocalIssueSeverity",
    "ValidationChoice",
    "ValidationLocalIssue",
    "ValidationLocalResult",
    "ValidationPanel",
    "ValidationPanelCatalog",
    "ValidationPanelValues",
)
