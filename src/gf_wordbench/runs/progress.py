"""Presentation-neutral progress coordination for GF Wordbench runs."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Final, TypeAlias, cast

from gf_wordbench.kernel.events import (
    EventField,
    EventFields,
    EventLevel,
    EventScalar,
    EventSink,
    ProgressEvent,
    event_fields,
)
from gf_wordbench.kernel.ids import validate_run_id

Clock: TypeAlias = Callable[[], datetime]
ProgressSink: TypeAlias = EventSink[ProgressEvent]
ProgressFieldInput: TypeAlias = (
    EventFields | Mapping[str, EventScalar] | Iterable[tuple[str, EventScalar]]
)

_UNSET: Final = object()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _validate_optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _normalize_fields(values: ProgressFieldInput) -> EventFields:
    if isinstance(values, tuple) and all(isinstance(item, EventField) for item in values):
        return values
    normalized_input = cast(
        Mapping[str, EventScalar] | Iterable[tuple[str, EventScalar]],
        values,
    )
    return event_fields(normalized_input)


def emit_progress(
    sink: ProgressSink | None,
    *,
    timestamp: datetime,
    message: str,
    severity: EventLevel = EventLevel.INFO,
    run_id: str | None = None,
    stage: str | None = None,
    subject: str | None = None,
    completed: int | None = None,
    total: int | None = None,
    fields: ProgressFieldInput = (),
) -> ProgressEvent:
    event = ProgressEvent(
        timestamp=timestamp,
        message=message,
        severity=severity,
        run_id=run_id,
        stage=stage,
        subject=subject,
        completed=completed,
        total=total,
        fields=_normalize_fields(fields),
    )
    if sink is not None:
        sink(event)
    return event


@dataclass(frozen=True, slots=True)
class ProgressReporter:
    run_id: str
    sink: ProgressSink | None = None
    clock: Clock = _utc_now
    stage: str | None = None
    subject: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "run_id",
            str(validate_run_id(self.run_id, field="run ID")),
        )
        if self.sink is not None and not callable(self.sink):
            raise TypeError("sink must be callable or None")
        if not callable(self.clock):
            raise TypeError("clock must be callable")
        object.__setattr__(
            self,
            "stage",
            _validate_optional_text(self.stage, field_name="stage"),
        )
        object.__setattr__(
            self,
            "subject",
            _validate_optional_text(self.subject, field_name="subject"),
        )

    def scoped(
        self,
        *,
        stage: str | object | None = _UNSET,
        subject: str | object | None = _UNSET,
    ) -> ProgressReporter:
        next_stage = self.stage if stage is _UNSET else stage
        next_subject = self.subject if subject is _UNSET else subject
        if next_stage is not None and not isinstance(next_stage, str):
            raise TypeError("stage must be a string or None")
        if next_subject is not None and not isinstance(next_subject, str):
            raise TypeError("subject must be a string or None")
        return replace(
            self,
            stage=next_stage,
            subject=next_subject,
        )

    def for_stage(self, stage: str) -> ProgressReporter:
        return self.scoped(stage=stage, subject=None)

    def for_subject(
        self,
        subject: str,
        *,
        stage: str | object | None = _UNSET,
    ) -> ProgressReporter:
        return self.scoped(stage=stage, subject=subject)

    def emit(
        self,
        message: str,
        *,
        severity: EventLevel = EventLevel.INFO,
        completed: int | None = None,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        timestamp = self.clock()
        if not isinstance(timestamp, datetime):
            raise TypeError("clock must return a datetime")
        return emit_progress(
            self.sink,
            timestamp=timestamp,
            message=message,
            severity=severity,
            run_id=self.run_id,
            stage=self.stage,
            subject=self.subject,
            completed=completed,
            total=total,
            fields=fields,
        )

    def started(
        self,
        message: str,
        *,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        completed = 0 if total is not None else None
        return self.emit(
            message,
            completed=completed,
            total=total,
            fields=fields,
        )

    def updated(
        self,
        completed: int,
        total: int,
        message: str,
        *,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        return self.emit(
            message,
            completed=completed,
            total=total,
            fields=fields,
        )

    def completed(
        self,
        message: str,
        *,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        return self.emit(
            message,
            completed=total,
            total=total,
            fields=fields,
        )

    def warning(
        self,
        message: str,
        *,
        completed: int | None = None,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        return self.emit(
            message,
            severity=EventLevel.WARN,
            completed=completed,
            total=total,
            fields=fields,
        )

    def error(
        self,
        message: str,
        *,
        completed: int | None = None,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        return self.emit(
            message,
            severity=EventLevel.ERROR,
            completed=completed,
            total=total,
            fields=fields,
        )

    def fatal(
        self,
        message: str,
        *,
        completed: int | None = None,
        total: int | None = None,
        fields: ProgressFieldInput = (),
    ) -> ProgressEvent:
        return self.emit(
            message,
            severity=EventLevel.FATAL,
            completed=completed,
            total=total,
            fields=fields,
        )


__all__ = (
    "Clock",
    "ProgressFieldInput",
    "ProgressReporter",
    "ProgressSink",
    "emit_progress",
)
