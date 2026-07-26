"""Neutral, immutable event contracts shared across GF Wordbench layers."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
from itertools import islice
from typing import Protocol, TypeAlias, TypeVar

__all__ = (
    "EventField",
    "EventFields",
    "EventLevel",
    "EventScalar",
    "EventSink",
    "LifecycleEvent",
    "ProgressEvent",
    "event_fields",
)

_MAX_EVENT_NAME_CHARS = 96
_MAX_EVENT_MESSAGE_CHARS = 1_024
_MAX_EVENT_TEXT_CHARS = 4_096
_MAX_EVENT_FIELD_KEY_CHARS = 64
_MAX_EVENT_FIELDS = 32

_LOWER_SNAKE_CASE = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
)

EventScalar: TypeAlias = str | int | float | bool | None


@unique
class EventLevel(StrEnum):
    """Canonical lifecycle levels used by progress consumers and master logs."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass(frozen=True, slots=True, order=True)
class EventField:
    """One bounded scalar field attached to an event."""

    key: str
    value: EventScalar = field(compare=False)

    def __post_init__(self) -> None:
        _validate_lower_snake_case(
            self.key,
            field_name="event field key",
            max_chars=_MAX_EVENT_FIELD_KEY_CHARS,
        )
        _validate_scalar(
            self.value,
            field_name=f"event field {self.key!r}",
        )


EventFields: TypeAlias = tuple[EventField, ...]


def event_fields(
    values: Mapping[str, EventScalar]
    | Iterable[tuple[str, EventScalar]] = (),
    /,
) -> EventFields:
    """Create deterministic, validated event fields."""

    items = values.items() if isinstance(values, Mapping) else values
    return _normalize_fields(
        EventField(key, value)
        for key, value in items
    )


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """Presentation-neutral progress emitted through an injected sink."""

    timestamp: datetime
    message: str
    severity: EventLevel = EventLevel.INFO
    run_id: str | None = None
    stage: str | None = None
    subject: str | None = None
    completed: int | None = None
    total: int | None = None
    fields: EventFields = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "timestamp",
            _normalize_timestamp(self.timestamp),
        )
        _validate_event_level(
            self.severity,
            field_name="severity",
        )
        _validate_text(
            self.message,
            field_name="message",
            max_chars=_MAX_EVENT_MESSAGE_CHARS,
            allow_empty=False,
        )
        _validate_optional_text(
            self.run_id,
            field_name="run_id",
        )
        _validate_optional_text(
            self.stage,
            field_name="stage",
        )
        _validate_optional_text(
            self.subject,
            field_name="subject",
        )
        _validate_count(
            self.completed,
            field_name="completed",
        )
        _validate_count(
            self.total,
            field_name="total",
        )

        if (
            self.completed is not None
            and self.total is not None
            and self.completed > self.total
        ):
            raise ValueError("completed cannot exceed total")

        object.__setattr__(
            self,
            "fields",
            _normalize_fields(self.fields),
        )


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """Structured lifecycle event for logging and progress consumers."""

    timestamp: datetime
    event: str
    level: EventLevel = EventLevel.INFO
    run_id: str | None = None
    stage: str | None = None
    operation: str | None = None
    subject: str | None = None
    status: str | None = None
    error_code: str | None = None
    message: str = ""
    evidence_path: str | None = None
    fields: EventFields = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "timestamp",
            _normalize_timestamp(self.timestamp),
        )
        _validate_event_level(
            self.level,
            field_name="level",
        )
        _validate_lower_snake_case(
            self.event,
            field_name="event",
            max_chars=_MAX_EVENT_NAME_CHARS,
        )
        _validate_optional_text(
            self.run_id,
            field_name="run_id",
        )
        _validate_optional_text(
            self.stage,
            field_name="stage",
        )
        _validate_optional_text(
            self.operation,
            field_name="operation",
        )
        _validate_optional_text(
            self.subject,
            field_name="subject",
        )
        _validate_optional_text(
            self.status,
            field_name="status",
        )
        _validate_optional_text(
            self.error_code,
            field_name="error_code",
        )
        _validate_text(
            self.message,
            field_name="message",
            max_chars=_MAX_EVENT_MESSAGE_CHARS,
            allow_empty=True,
        )
        _validate_optional_text(
            self.evidence_path,
            field_name="evidence_path",
        )

        object.__setattr__(
            self,
            "fields",
            _normalize_fields(self.fields),
        )


_EventT_contra = TypeVar(
    "_EventT_contra",
    contravariant=True,
)


class EventSink(Protocol[_EventT_contra]):
    """Callable boundary for publishing events without importing consumers."""

    def __call__(
        self,
        event: _EventT_contra,
        /,
    ) -> None: ...


def _normalize_fields(
    fields: Iterable[EventField],
) -> EventFields:
    if isinstance(fields, (str, bytes)):
        raise TypeError(
            "fields must be an iterable of EventField values"
        )

    # Consume only enough values to enforce the public bound. This prevents an
    # accidentally unbounded iterable from being materialized in full.
    normalized = tuple(
        islice(
            fields,
            _MAX_EVENT_FIELDS + 1,
        )
    )

    if len(normalized) > _MAX_EVENT_FIELDS:
        raise ValueError(
            f"an event may contain at most {_MAX_EVENT_FIELDS} fields"
        )

    if not all(
        isinstance(item, EventField)
        for item in normalized
    ):
        raise TypeError(
            "fields must contain only EventField values"
        )

    keys = tuple(item.key for item in normalized)
    if len(keys) != len(set(keys)):
        raise ValueError(
            "event field keys must be unique"
        )

    return tuple(
        sorted(
            normalized,
            key=lambda item: item.key,
        )
    )


def _normalize_timestamp(
    value: datetime,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "timestamp must be timezone-aware"
        )

    return value.astimezone(UTC)


def _validate_event_level(
    value: EventLevel,
    *,
    field_name: str,
) -> None:
    if not isinstance(value, EventLevel):
        raise TypeError(
            f"{field_name} must be an EventLevel"
        )


def _validate_count(
    value: int | None,
    *,
    field_name: str,
) -> None:
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer or None"
        )

    if value < 0:
        raise ValueError(
            f"{field_name} cannot be negative"
        )


def _validate_optional_text(
    value: str | None,
    *,
    field_name: str,
) -> None:
    if value is None:
        return

    _validate_text(
        value,
        field_name=field_name,
        max_chars=_MAX_EVENT_TEXT_CHARS,
        allow_empty=False,
    )


def _validate_text(
    value: str,
    *,
    field_name: str,
    max_chars: int,
    allow_empty: bool,
) -> None:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    if not allow_empty and not value.strip():
        raise ValueError(
            f"{field_name} cannot be empty"
        )

    if len(value) > max_chars:
        raise ValueError(
            f"{field_name} exceeds {max_chars} characters"
        )

    if "\x00" in value:
        raise ValueError(
            f"{field_name} cannot contain NUL characters"
        )


def _validate_lower_snake_case(
    value: str,
    *,
    field_name: str,
    max_chars: int,
) -> None:
    _validate_text(
        value,
        field_name=field_name,
        max_chars=max_chars,
        allow_empty=False,
    )

    if _LOWER_SNAKE_CASE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must use lower_snake_case"
        )


def _validate_scalar(
    value: EventScalar,
    *,
    field_name: str,
) -> None:
    if value is None or isinstance(value, (bool, int)):
        return

    if isinstance(value, str):
        _validate_text(
            value,
            field_name=field_name,
            max_chars=_MAX_EVENT_TEXT_CHARS,
            allow_empty=True,
        )
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(
                f"{field_name} must be a finite float"
            )
        return

    raise TypeError(
        f"{field_name} must be a scalar event value"
    )