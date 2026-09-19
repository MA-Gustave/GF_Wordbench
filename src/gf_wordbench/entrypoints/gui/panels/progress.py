"""Structured run-progress presentation for the GF Wordbench Qt GUI."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, TypeVar

from PySide6.QtCore import QElapsedTimer, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.kernel.events import EventLevel, ProgressEvent

__all__ = (
    "ProgressActivityItem",
    "ProgressPanel",
    "ProgressPanelModel",
    "ProgressRunState",
)

_MAX_IDENTIFIER: Final[int] = 256
_MAX_STATUS_TEXT: Final[int] = 1_024
_MAX_SUBJECT_TEXT: Final[int] = 4_096
_MAX_ACTIVITY_MESSAGE: Final[int] = 4_096
_MAX_ACTIVITY_ITEMS: Final[int] = 500
_MAX_ELAPSED_SECONDS: Final[float] = 365.0 * 24.0 * 60.0 * 60.0
_TIMER_INTERVAL_MS: Final[int] = 250

_COUNT_FIELD_ALIASES: Final[Mapping[str, tuple[str, ...]]] = {
    "warning_count": ("warning_count", "warnings"),
    "failure_count": ("failure_count", "failures", "error_count"),
    "elapsed_seconds": ("elapsed_seconds",),
}

_E = TypeVar("_E", bound=StrEnum)
_T = TypeVar("_T")


@unique
class ProgressRunState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

    @property
    def is_active(self) -> bool:
        return self in {
            ProgressRunState.RUNNING,
            ProgressRunState.CANCELLING,
        }

    @property
    def is_terminal(self) -> bool:
        return self in {
            ProgressRunState.COMPLETED,
            ProgressRunState.CANCELLED,
            ProgressRunState.FAILED,
        }


@dataclass(frozen=True, slots=True)
class ProgressActivityItem:
    timestamp: datetime
    message: str
    severity: EventLevel = EventLevel.INFO
    stage: str | None = None
    subject: str | None = None
    artifact_path: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "timestamp",
            _utc_timestamp(self.timestamp, "timestamp"),
        )
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message", _MAX_ACTIVITY_MESSAGE),
        )
        if not isinstance(self.severity, EventLevel):
            raise TypeError("severity must be EventLevel")
        object.__setattr__(
            self,
            "stage",
            _optional_text(self.stage, "stage", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "subject",
            _optional_text(self.subject, "subject", _MAX_SUBJECT_TEXT),
        )
        if self.artifact_path is not None:
            object.__setattr__(
                self,
                "artifact_path",
                _path(self.artifact_path, "artifact_path"),
            )

    @classmethod
    def from_event(cls, event: ProgressEvent) -> ProgressActivityItem:
        if not isinstance(event, ProgressEvent):
            raise TypeError("event must be ProgressEvent")
        return cls(
            timestamp=event.timestamp,
            message=event.message,
            severity=event.severity,
            stage=event.stage,
            subject=event.subject,
            artifact_path=_artifact_path_from_event(event),
        )

    def render(self) -> str:
        timestamp = self.timestamp.strftime("%H:%M:%S")
        context = tuple(value for value in (self.stage, self.subject) if value is not None)
        prefix = f"[{timestamp}] [{self.severity.value}]"
        if context:
            prefix += f" [{' · '.join(context)}]"
        line = f"{prefix} {self.message}"
        if self.artifact_path is not None:
            line += f" — {self.artifact_path.as_posix()}"
        return line


@dataclass(frozen=True, slots=True)
class ProgressPanelModel:
    run_id: str | None = None
    state: ProgressRunState = ProgressRunState.IDLE
    status_text: str = "Ready"
    stage: str | None = None
    subject: str | None = None
    completed: int | None = None
    total: int | None = None
    elapsed_seconds: float = 0.0
    warning_count: int = 0
    failure_count: int = 0
    activity: tuple[ProgressActivityItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "run_id",
            _optional_text(self.run_id, "run_id", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "state",
            _enum(self.state, ProgressRunState, "state"),
        )
        object.__setattr__(
            self,
            "status_text",
            _text(self.status_text, "status_text", _MAX_STATUS_TEXT),
        )
        object.__setattr__(
            self,
            "stage",
            _optional_text(self.stage, "stage", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "subject",
            _optional_text(self.subject, "subject", _MAX_SUBJECT_TEXT),
        )
        _count_or_none(self.completed, "completed")
        _count_or_none(self.total, "total")
        if self.completed is not None and self.total is not None and self.completed > self.total:
            raise ValueError("completed cannot exceed total")
        object.__setattr__(
            self,
            "elapsed_seconds",
            _elapsed(self.elapsed_seconds),
        )
        _count(self.warning_count, "warning_count")
        _count(self.failure_count, "failure_count")
        items = _typed_tuple(
            self.activity,
            ProgressActivityItem,
            "activity",
        )
        if len(items) > _MAX_ACTIVITY_ITEMS:
            items = items[-_MAX_ACTIVITY_ITEMS:]
        object.__setattr__(self, "activity", items)

        if self.state is ProgressRunState.IDLE:
            if self.run_id is not None:
                raise ValueError("idle progress cannot identify an active run")
            if self.completed is not None or self.total is not None:
                raise ValueError("idle progress cannot contain work counts")
        elif self.run_id is None:
            raise ValueError("non-idle progress requires run_id")

    @property
    def is_indeterminate(self) -> bool:
        return self.state.is_active and self.total is None

    @property
    def progress_fraction(self) -> float | None:
        if self.completed is None or self.total is None:
            return None
        if self.total == 0:
            return 1.0 if self.state.is_terminal else 0.0
        return self.completed / self.total


class ProgressPanel(QWidget):
    cancellation_requested = Signal(str)
    activity_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = ProgressPanelModel()
        self._elapsed_clock = QElapsedTimer()
        self._elapsed_baseline = 0.0
        self._timed_run_id: str | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(_TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._update_elapsed_display)
        self._build_ui()
        self._connect_signals()
        self._render(reset_activity=True)

    def model(self) -> ProgressPanelModel:
        elapsed = self._current_elapsed_seconds()
        if elapsed == self._model.elapsed_seconds:
            return self._model
        return replace(self._model, elapsed_seconds=elapsed)

    def set_model(self, model: ProgressPanelModel) -> None:
        if not isinstance(model, ProgressPanelModel):
            raise TypeError("model must be ProgressPanelModel")
        previous_run_id = self._model.run_id
        previous_active = self._model.state.is_active
        self._model = model
        self._synchronize_clock(
            previous_run_id=previous_run_id,
            previous_active=previous_active,
        )
        self._render(reset_activity=True)

    def begin_run(
        self,
        run_id: str,
        *,
        status_text: str = "Running",
        total: int | None = None,
        stage: str | None = None,
        subject: str | None = None,
    ) -> None:
        self._activity_toggle.setChecked(True)
        self.set_model(
            ProgressPanelModel(
                run_id=run_id,
                state=ProgressRunState.RUNNING,
                status_text=status_text,
                stage=stage,
                subject=subject,
                completed=0 if total is not None else None,
                total=total,
            )
        )

    @Slot(object)
    def apply_event(self, event: ProgressEvent) -> None:
        if not isinstance(event, ProgressEvent):
            raise TypeError("event must be ProgressEvent")

        current = self.model()
        run_id = event.run_id or current.run_id
        if run_id is None:
            raise ValueError("a progress event without run_id requires an active run")
        if current.run_id is not None and event.run_id not in {None, current.run_id}:
            raise ValueError("progress event belongs to another run")

        fields = {field.key: field.value for field in event.fields}
        completed = event.completed if event.completed is not None else current.completed
        total = event.total if event.total is not None else current.total
        if total is not None and completed is None:
            completed = 0

        warning_count = _field_count(
            fields,
            _COUNT_FIELD_ALIASES["warning_count"],
            current.warning_count,
        )
        failure_count = _field_count(
            fields,
            _COUNT_FIELD_ALIASES["failure_count"],
            current.failure_count,
        )
        elapsed_seconds = _field_elapsed(
            fields,
            _COUNT_FIELD_ALIASES["elapsed_seconds"],
            current.elapsed_seconds,
        )

        activity = (
            *current.activity,
            ProgressActivityItem.from_event(event),
        )[-_MAX_ACTIVITY_ITEMS:]

        state = current.state
        if state is ProgressRunState.IDLE:
            state = ProgressRunState.RUNNING

        self.set_model(
            ProgressPanelModel(
                run_id=run_id,
                state=state,
                status_text=event.message,
                stage=event.stage if event.stage is not None else current.stage,
                subject=event.subject if event.subject is not None else current.subject,
                completed=completed,
                total=total,
                elapsed_seconds=elapsed_seconds,
                warning_count=warning_count,
                failure_count=failure_count,
                activity=activity,
            )
        )

    def update_progress(
        self,
        *,
        completed: int | None = None,
        total: int | None = None,
        stage: str | None = None,
        subject: str | None = None,
        status_text: str | None = None,
        warning_count: int | None = None,
        failure_count: int | None = None,
    ) -> None:
        current = self.model()
        if not current.state.is_active:
            raise RuntimeError("progress can be updated only during an active run")
        next_completed = completed if completed is not None else current.completed
        next_total = total if total is not None else current.total
        if next_total is not None and next_completed is None:
            next_completed = 0
        self.set_model(
            replace(
                current,
                completed=next_completed,
                total=next_total,
                stage=stage if stage is not None else current.stage,
                subject=subject if subject is not None else current.subject,
                status_text=(status_text if status_text is not None else current.status_text),
                warning_count=(
                    warning_count if warning_count is not None else current.warning_count
                ),
                failure_count=(
                    failure_count if failure_count is not None else current.failure_count
                ),
            )
        )

    def append_activity(self, item: ProgressActivityItem) -> None:
        if not isinstance(item, ProgressActivityItem):
            raise TypeError("item must be ProgressActivityItem")
        current = self.model()
        activity = (*current.activity, item)[-_MAX_ACTIVITY_ITEMS:]
        self._model = replace(current, activity=activity)
        self._append_activity_text(item)

    def finish_run(
        self,
        status_text: str,
        *,
        state: ProgressRunState = ProgressRunState.COMPLETED,
        warning_count: int | None = None,
        failure_count: int | None = None,
    ) -> None:
        terminal_state = _enum(state, ProgressRunState, "state")
        if not terminal_state.is_terminal:
            raise ValueError("finish_run requires a terminal state")
        current = self.model()
        if current.run_id is None:
            raise RuntimeError("there is no active or completed run")
        completed = current.completed
        if terminal_state is ProgressRunState.COMPLETED and current.total is not None:
            completed = current.total
        self.set_model(
            replace(
                current,
                state=terminal_state,
                status_text=status_text,
                completed=completed,
                warning_count=(current.warning_count if warning_count is None else warning_count),
                failure_count=(current.failure_count if failure_count is None else failure_count),
            )
        )

    def mark_cancelled(self, status_text: str = "Run cancelled") -> None:
        self.finish_run(status_text, state=ProgressRunState.CANCELLED)

    def mark_failed(self, status_text: str = "Validation error") -> None:
        self.finish_run(status_text, state=ProgressRunState.FAILED)

    def reset(self) -> None:
        self.set_model(ProgressPanelModel())

    @Slot()
    def request_cancellation(self) -> None:
        current = self.model()
        if current.state is not ProgressRunState.RUNNING:
            return
        self.set_model(
            replace(
                current,
                state=ProgressRunState.CANCELLING,
                status_text="Cancelling…",
            )
        )
        assert current.run_id is not None
        self.cancellation_requested.emit(current.run_id)

    @Slot()
    def clear_activity(self) -> None:
        current = self.model()
        self._model = replace(current, activity=())
        self._activity.clear()
        self.activity_cleared.emit()

    def _build_ui(self) -> None:
        self.setObjectName("progressPanel")
        self.setAccessibleName(self.tr("Validation progress"))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        summary_group = QGroupBox(self.tr("Progress"), self)
        summary_layout = QGridLayout(summary_group)

        self._status_value = QLabel(summary_group)
        self._stage_value = QLabel(summary_group)
        self._subject_value = QLabel(summary_group)
        self._elapsed_value = QLabel(summary_group)
        self._warning_value = QLabel(summary_group)
        self._failure_value = QLabel(summary_group)

        for label in (
            self._status_value,
            self._stage_value,
            self._subject_value,
            self._elapsed_value,
            self._warning_value,
            self._failure_value,
        ):
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        summary_layout.addWidget(QLabel(self.tr("Status"), summary_group), 0, 0)
        summary_layout.addWidget(self._status_value, 0, 1)
        summary_layout.addWidget(QLabel(self.tr("Stage"), summary_group), 1, 0)
        summary_layout.addWidget(self._stage_value, 1, 1)
        summary_layout.addWidget(QLabel(self.tr("Subject"), summary_group), 2, 0)
        summary_layout.addWidget(self._subject_value, 2, 1)
        summary_layout.addWidget(QLabel(self.tr("Elapsed"), summary_group), 0, 2)
        summary_layout.addWidget(self._elapsed_value, 0, 3)
        summary_layout.addWidget(QLabel(self.tr("Warnings"), summary_group), 1, 2)
        summary_layout.addWidget(self._warning_value, 1, 3)
        summary_layout.addWidget(QLabel(self.tr("Failures"), summary_group), 2, 2)
        summary_layout.addWidget(self._failure_value, 2, 3)
        summary_layout.setColumnStretch(1, 3)
        summary_layout.setColumnStretch(3, 1)

        self._progress = QProgressBar(summary_group)
        self._progress.setAccessibleName(self.tr("Validation completion"))
        self._progress.setTextVisible(True)
        summary_layout.addWidget(self._progress, 3, 0, 1, 4)

        actions = QHBoxLayout()
        self._cancel_button = QPushButton(self.tr("Cancel"), summary_group)
        self._cancel_button.setAccessibleName(self.tr("Cancel active validation run"))
        actions.addWidget(self._cancel_button)
        actions.addStretch(1)
        summary_layout.addLayout(actions, 4, 0, 1, 4)

        root.addWidget(summary_group)

        self._activity_toggle = QToolButton(self)
        self._activity_toggle.setObjectName("progressActivityToggle")
        self._activity_toggle.setText(self.tr("Show Activity"))
        self._activity_toggle.setCheckable(True)
        self._activity_toggle.setChecked(False)
        self._activity_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._activity_toggle.setArrowType(Qt.ArrowType.RightArrow)
        root.addWidget(self._activity_toggle, 0, Qt.AlignmentFlag.AlignLeft)

        self._activity_group = QGroupBox(self.tr("Activity"), self)
        self._activity_group.setObjectName("progressActivityGroup")
        activity_layout = QVBoxLayout(self._activity_group)

        self._activity = QPlainTextEdit(self._activity_group)
        self._activity.setObjectName("progressActivity")
        self._activity.setAccessibleName(self.tr("Bounded validation activity"))
        self._activity.setReadOnly(True)
        self._activity.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._activity.document().setMaximumBlockCount(_MAX_ACTIVITY_ITEMS)
        activity_layout.addWidget(self._activity)

        activity_actions = QHBoxLayout()
        activity_actions.addStretch(1)
        self._clear_activity_button = QPushButton(
            self.tr("Clear Activity"),
            self._activity_group,
        )
        self._clear_activity_button.setAccessibleName(self.tr("Clear displayed activity"))
        activity_actions.addWidget(self._clear_activity_button)
        activity_layout.addLayout(activity_actions)

        root.addWidget(self._activity_group, 1)
        self._set_activity_visible(False)

    def _connect_signals(self) -> None:
        self._cancel_button.clicked.connect(self.request_cancellation)
        self._clear_activity_button.clicked.connect(self.clear_activity)
        self._activity_toggle.toggled.connect(self._set_activity_visible)

    def _set_activity_visible(self, visible: bool) -> None:
        self._activity_group.setVisible(visible)
        self._activity_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self._activity_toggle.setText(
            self.tr("Hide Activity") if visible else self.tr("Show Activity")
        )

    def _synchronize_clock(
        self,
        *,
        previous_run_id: str | None,
        previous_active: bool,
    ) -> None:
        if self._model.state.is_active:
            should_restart = (
                not previous_active
                or previous_run_id != self._model.run_id
                or self._timed_run_id != self._model.run_id
                or not self._elapsed_clock.isValid()
            )
            if should_restart:
                self._elapsed_baseline = self._model.elapsed_seconds
                self._elapsed_clock.start()
                self._timed_run_id = self._model.run_id
            elif self._model.elapsed_seconds > self._current_elapsed_seconds():
                self._elapsed_baseline = self._model.elapsed_seconds
                self._elapsed_clock.restart()
            if not self._timer.isActive():
                self._timer.start()
            return

        self._elapsed_baseline = self._model.elapsed_seconds
        self._elapsed_clock.invalidate()
        self._timed_run_id = None
        self._timer.stop()

    def _current_elapsed_seconds(self) -> float:
        if self._model.state.is_active and self._elapsed_clock.isValid():
            elapsed = self._elapsed_baseline + (self._elapsed_clock.elapsed() / 1_000.0)
            return min(elapsed, _MAX_ELAPSED_SECONDS)
        return self._model.elapsed_seconds

    def _render(self, *, reset_activity: bool) -> None:
        model = self._model
        self._status_value.setText(model.status_text)
        self._status_value.setAccessibleName(self.tr("Status: %1").replace("%1", model.status_text))
        self._stage_value.setText(model.stage or self.tr("Not started"))
        self._subject_value.setText(model.subject or self.tr("None"))
        self._warning_value.setText(str(model.warning_count))
        self._failure_value.setText(str(model.failure_count))
        self._update_elapsed_display()
        self._render_progress_bar()

        self._cancel_button.setEnabled(model.state is ProgressRunState.RUNNING)
        if model.state is ProgressRunState.CANCELLING:
            self._cancel_button.setText(self.tr("Cancelling…"))
        else:
            self._cancel_button.setText(self.tr("Cancel"))

        if reset_activity:
            self._activity.setPlainText("\n".join(item.render() for item in model.activity))

    @Slot()
    def _update_elapsed_display(self) -> None:
        elapsed = self._current_elapsed_seconds()
        self._elapsed_value.setText(_format_elapsed(elapsed))

    def _render_progress_bar(self) -> None:
        model = self._model
        if model.is_indeterminate:
            self._progress.setRange(0, 0)
            self._progress.setFormat(self.tr("In progress"))
            return

        self._progress.setRange(0, 1000)
        fraction = model.progress_fraction
        if fraction is None:
            value = 1000 if model.state.is_terminal else 0
            text = model.status_text
        else:
            value = max(0, min(1000, round(fraction * 1000)))
            assert model.completed is not None
            assert model.total is not None
            text = (
                self.tr("%1 of %2")
                .replace("%1", str(model.completed))
                .replace("%2", str(model.total))
            )
        self._progress.setValue(value)
        self._progress.setFormat(text)

    def _append_activity_text(self, item: ProgressActivityItem) -> None:
        self._activity.appendPlainText(item.render())


def _artifact_path_from_event(event: ProgressEvent) -> Path | None:
    for field in event.fields:
        if field.key not in {"artifact_path", "evidence_path", "output_path"}:
            continue
        if isinstance(field.value, str) and field.value.strip():
            return Path(field.value)
    return None


def _field_count(
    fields: Mapping[str, object],
    aliases: Iterable[str],
    default: int,
) -> int:
    for key in aliases:
        if key not in fields:
            continue
        value = fields[key]
        return _count(value, key)
    return default


def _field_elapsed(
    fields: Mapping[str, object],
    aliases: Iterable[str],
    default: float,
) -> float:
    for key in aliases:
        if key not in fields:
            continue
        return _elapsed(fields[key])
    return default


def _format_elapsed(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3_600)
    minutes, seconds_part = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds_part:02d}"
    return f"{minutes:02d}:{seconds_part:02d}"


def _enum(value: object, enum_type: type[_E], field: str) -> _E:
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
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return value


def _optional_text(
    value: object,
    field: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    return _text(value, field, maximum)


def _path(value: object, field: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{field} must be a string or Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    return Path(value)


def _utc_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} cannot be negative")


def _count_or_none(value: object, field: str) -> None:
    if value is not None:
        _count(value, field)


def _elapsed(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("elapsed_seconds must be a number")
    result = float(value)
    if result < 0.0:
        raise ValueError("elapsed_seconds cannot be negative")
    if result > _MAX_ELAPSED_SECONDS:
        raise ValueError(f"elapsed_seconds exceeds {_MAX_ELAPSED_SECONDS}")
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
