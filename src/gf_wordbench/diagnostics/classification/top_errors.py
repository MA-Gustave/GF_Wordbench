"""Deterministic aggregation of structured GF Wordbench top errors."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)
from gf_wordbench.runs.models.results import TopError

_SUBJECT_KINDS: Final[frozenset[str]] = frozenset({"file", "scenario", "run"})
_SPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
_MAX_MESSAGE_LENGTH: Final[int] = 8_192
_MAX_IDENTITY_LENGTH: Final[int] = 2_048
_MAX_SUBJECTS: Final[int] = 1_000_000


@dataclass(frozen=True, slots=True)
class TopErrorCandidate:
    """One structured failing diagnostic eligible for top-error aggregation."""

    subject_kind: str
    subject_id: str
    status: ValidationStatus
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    message: str
    occurrence_count: int = 1
    diagnostic_code: str | None = None
    origin: str | None = None
    is_warning: bool = False

    def __post_init__(self) -> None:
        subject_kind = _require_text(
            self.subject_kind,
            field="subject_kind",
            maximum=_MAX_IDENTITY_LENGTH,
        )
        if subject_kind not in _SUBJECT_KINDS:
            expected = ", ".join(sorted(_SUBJECT_KINDS))
            raise ValueError(
                f"unsupported subject_kind {subject_kind!r}; expected {expected}"
            )

        subject_id = _require_text(
            self.subject_id,
            field="subject_id",
            maximum=_MAX_IDENTITY_LENGTH,
        )
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be ValidationStatus")
        if not isinstance(self.diagnostic_class, DiagnosticClass):
            raise TypeError("diagnostic_class must be DiagnosticClass")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be ErrorKind")
        if type(self.occurrence_count) is not int:
            raise TypeError("occurrence_count must be an integer")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")
        if type(self.is_warning) is not bool:
            raise TypeError("is_warning must be a boolean")

        message = _require_string(
            self.message,
            field="message",
            maximum=_MAX_MESSAGE_LENGTH,
        )
        diagnostic_code = _optional_text(
            self.diagnostic_code,
            field="diagnostic_code",
            maximum=256,
        )
        origin = _optional_text(
            self.origin,
            field="origin",
            maximum=256,
        )

        object.__setattr__(self, "subject_kind", subject_kind)
        object.__setattr__(self, "subject_id", subject_id)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "diagnostic_code", diagnostic_code)
        object.__setattr__(self, "origin", origin)


@dataclass(frozen=True, slots=True)
class TopErrorAggregationPolicy:
    """Explicit policy for top-error inclusion and occurrence counting."""

    include_ambiguous: bool = True
    include_downstream: bool = False
    include_warnings: bool = False
    count_occurrences: bool = False
    include_subject_kinds: tuple[str, ...] = ("file", "scenario", "run")

    def __post_init__(self) -> None:
        for field_name in (
            "include_ambiguous",
            "include_downstream",
            "include_warnings",
            "count_occurrences",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")

        if isinstance(self.include_subject_kinds, (str, bytes)):
            raise TypeError("include_subject_kinds must be a tuple of strings")
        kinds = tuple(self.include_subject_kinds)
        if len(kinds) != len(set(kinds)):
            raise ValueError("include_subject_kinds must not contain duplicates")
        for kind in kinds:
            if kind not in _SUBJECT_KINDS:
                expected = ", ".join(sorted(_SUBJECT_KINDS))
                raise ValueError(
                    f"unsupported included subject kind {kind!r}; expected {expected}"
                )
        object.__setattr__(self, "include_subject_kinds", kinds)


DEFAULT_TOP_ERROR_POLICY: Final[TopErrorAggregationPolicy] = (
    TopErrorAggregationPolicy()
)


@dataclass(slots=True)
class _Bucket:
    error_kind: ErrorKind
    message: str
    count: int
    subject_kinds: set[str]


def normalize_top_error_message(message: str) -> str:
    """Normalize presentation-neutral whitespace without changing semantics."""

    value = _require_string(
        message,
        field="message",
        maximum=_MAX_MESSAGE_LENGTH,
    )
    value = unicodedata.normalize("NFC", value)
    return _SPACE_RE.sub(" ", value).strip()


def bucket_top_errors(
    candidates: Iterable[TopErrorCandidate],
    *,
    policy: TopErrorAggregationPolicy = DEFAULT_TOP_ERROR_POLICY,
) -> tuple[TopError, ...]:
    """Aggregate classified failures into canonical deterministic records."""

    if isinstance(candidates, (str, bytes)):
        raise TypeError("candidates must be an iterable of TopErrorCandidate")
    if not isinstance(policy, TopErrorAggregationPolicy):
        raise TypeError("policy must be TopErrorAggregationPolicy")

    buckets: dict[tuple[ErrorKind, str], _Bucket] = {}
    seen_subject_groups: set[tuple[str, str, ErrorKind, str]] = set()
    accepted_subjects = frozenset(policy.include_subject_kinds)
    processed = 0

    for candidate in candidates:
        processed += 1
        if processed > _MAX_SUBJECTS:
            raise ValueError("candidate count exceeds the supported limit")
        if not isinstance(candidate, TopErrorCandidate):
            raise TypeError("candidates must contain TopErrorCandidate objects")
        if candidate.subject_kind not in accepted_subjects:
            continue
        if not _is_eligible(candidate, policy):
            continue

        message = normalize_top_error_message(candidate.message)
        if not message:
            continue

        message_key = message.casefold()
        group_key = (candidate.error_kind, message_key)
        subject_group_key = (
            candidate.subject_kind,
            candidate.subject_id,
            candidate.error_kind,
            message_key,
        )

        if not policy.count_occurrences:
            if subject_group_key in seen_subject_groups:
                continue
            seen_subject_groups.add(subject_group_key)
            increment = 1
        else:
            increment = candidate.occurrence_count

        bucket = buckets.get(group_key)
        if bucket is None:
            bucket = _Bucket(
                error_kind=candidate.error_kind,
                message=message,
                count=0,
                subject_kinds=set(),
            )
            buckets[group_key] = bucket
        else:
            bucket.message = _stable_message(bucket.message, message)

        bucket.count += increment
        bucket.subject_kinds.add(candidate.subject_kind)

    records = tuple(
        TopError(
            error_kind=bucket.error_kind,
            message=bucket.message,
            count=bucket.count,
            subject_kinds=tuple(sorted(bucket.subject_kinds)),
        )
        for bucket in buckets.values()
        if bucket.count > 0
    )
    return sort_top_errors(records)


def sort_top_errors(records: Iterable[TopError]) -> tuple[TopError, ...]:
    """Validate and return top errors in canonical deterministic order."""

    if isinstance(records, (str, bytes)):
        raise TypeError("records must be an iterable of TopError")
    prepared = tuple(records)
    for record in prepared:
        _validate_top_error(record)
    return tuple(sorted(prepared, key=top_error_sort_key))


def top_error_sort_key(record: TopError) -> tuple[int, str, str, str]:
    """Return the canonical top-error ordering key."""

    _validate_top_error(record)
    return (
        -record.count,
        record.error_kind.value,
        record.message.casefold(),
        record.message,
    )


def validate_top_error_order(records: Iterable[TopError]) -> tuple[TopError, ...]:
    """Require canonical ordering and unique canonical aggregation keys."""

    prepared = tuple(records)
    ordered = sort_top_errors(prepared)
    if prepared != ordered:
        raise ValueError("top errors are not in canonical order")

    seen: set[tuple[ErrorKind, str]] = set()
    for record in prepared:
        key = (record.error_kind, record.message.casefold())
        if key in seen:
            raise ValueError(
                "top errors contain duplicate canonical aggregation keys"
            )
        seen.add(key)
    return prepared


def _is_eligible(
    candidate: TopErrorCandidate,
    policy: TopErrorAggregationPolicy,
) -> bool:
    if candidate.status not in (ValidationStatus.FAIL, ValidationStatus.ERROR):
        return False
    if candidate.error_kind is ErrorKind.OK:
        return False
    if candidate.is_warning and not policy.include_warnings:
        return False

    diagnostic_class = candidate.diagnostic_class
    if diagnostic_class in (
        DiagnosticClass.OK,
        DiagnosticClass.NOISE,
        DiagnosticClass.SKIPPED,
    ):
        return False
    if diagnostic_class is DiagnosticClass.DOWNSTREAM:
        return policy.include_downstream
    if diagnostic_class is DiagnosticClass.AMBIGUOUS:
        return policy.include_ambiguous
    return diagnostic_class is DiagnosticClass.DIRECT


def _stable_message(left: str, right: str) -> str:
    return min(left, right, key=lambda value: (value.casefold(), value))


def _validate_top_error(record: object) -> None:
    if not isinstance(record, TopError):
        raise TypeError("records must contain TopError objects")
    if not isinstance(record.error_kind, ErrorKind):
        raise TypeError("TopError.error_kind must be ErrorKind")
    if record.error_kind is ErrorKind.OK:
        raise ValueError("TopError.error_kind must not be OK")
    message = normalize_top_error_message(record.message)
    if message != record.message:
        raise ValueError("TopError.message must be canonically normalized")
    if type(record.count) is not int or record.count < 1:
        raise ValueError("TopError.count must be a positive integer")
    subject_kinds = tuple(record.subject_kinds)
    if len(subject_kinds) != len(set(subject_kinds)):
        raise ValueError("TopError.subject_kinds must not contain duplicates")
    if subject_kinds != tuple(sorted(subject_kinds)):
        raise ValueError("TopError.subject_kinds must be sorted")
    for subject_kind in subject_kinds:
        if subject_kind not in _SUBJECT_KINDS:
            raise ValueError(
                f"TopError contains unsupported subject kind {subject_kind!r}"
            )


def _optional_text(
    value: str | None,
    *,
    field: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    return _require_text(value, field=field, maximum=maximum)


def _require_text(value: object, *, field: str, maximum: int) -> str:
    text = _require_string(value, field=field, maximum=maximum).strip()
    if not text:
        raise ValueError(f"{field} must not be empty")
    return text


def _require_string(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL characters")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds the supported length limit")
    return value


__all__ = (
    "DEFAULT_TOP_ERROR_POLICY",
    "TopErrorAggregationPolicy",
    "TopErrorCandidate",
    "bucket_top_errors",
    "normalize_top_error_message",
    "sort_top_errors",
    "top_error_sort_key",
    "validate_top_error_order",
)
