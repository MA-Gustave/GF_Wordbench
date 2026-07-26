"""Deterministic regression comparison for structured validation subjects."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import PurePosixPath
from typing import Final

from gf_wordbench.kernel.statuses import ChangeKind, OverallStatus, ValidationStatus

from .models import ComparisonSubject, DiffEntry, RegressionSubjectKind

_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    status.value
    for status in (
        *tuple(ValidationStatus),
        *tuple(OverallStatus),
    )
)

_CHANGE_ORDER: Final[Mapping[ChangeKind, int]] = {
    ChangeKind.REGRESSED: 0,
    ChangeKind.NEW: 1,
    ChangeKind.IMPROVED: 2,
    ChangeKind.REMOVED: 3,
    ChangeKind.UNCHANGED: 4,
}

_SUBJECT_ORDER: Final[Mapping[RegressionSubjectKind, int]] = {
    RegressionSubjectKind.RUN: 0,
    RegressionSubjectKind.FILE: 1,
    RegressionSubjectKind.SCENARIO: 2,
}


def build_diff_entries(
    previous_subjects: Iterable[ComparisonSubject],
    current_subjects: Iterable[ComparisonSubject],
    *,
    include_unchanged: bool = True,
) -> tuple[DiffEntry, ...]:
    if not isinstance(include_unchanged, bool):
        raise TypeError("include_unchanged must be a bool")

    previous_index = index_subjects(previous_subjects, side="previous")
    current_index = index_subjects(current_subjects, side="current")
    identities = previous_index.keys() | current_index.keys()
    entries: list[DiffEntry] = []

    for identity in identities:
        previous = previous_index.get(identity)
        current = current_index.get(identity)

        if previous is None:
            if current is None:
                raise AssertionError("comparison identity has no subject")
            entries.append(build_new_entry(current))
            continue

        if current is None:
            entries.append(build_removed_entry(previous))
            continue

        entry = build_transition_entry(previous, current)
        if include_unchanged or entry.change_kind is not ChangeKind.UNCHANGED:
            entries.append(entry)

    return sort_diff_entries(entries)


def index_subjects(
    subjects: Iterable[ComparisonSubject],
    *,
    side: str,
) -> dict[tuple[RegressionSubjectKind, str], ComparisonSubject]:
    if isinstance(subjects, (str, bytes)):
        raise TypeError("subjects must be an iterable of ComparisonSubject values")
    if not isinstance(side, str) or not side.strip():
        raise ValueError("side must be a non-empty string")

    indexed: dict[
        tuple[RegressionSubjectKind, str],
        ComparisonSubject,
    ] = {}

    for position, subject in enumerate(subjects):
        if not isinstance(subject, ComparisonSubject):
            raise TypeError(
                f"{side} subjects[{position}] must be a ComparisonSubject"
            )

        normalized = normalize_subject(subject)
        identity = (normalized.subject_kind, normalized.subject_id)

        if identity in indexed:
            kind, subject_id = identity
            raise ValueError(
                f"duplicate {side} subject identity "
                f"{kind.value}:{subject_id}"
            )

        indexed[identity] = normalized

    return indexed


def normalize_subject(subject: ComparisonSubject) -> ComparisonSubject:
    if not isinstance(subject, ComparisonSubject):
        raise TypeError("subject must be a ComparisonSubject")

    subject_id = normalize_subject_id(
        subject.subject_kind,
        subject.subject_id,
    )
    status = normalize_status(
        subject.status,
        subject_kind=subject.subject_kind,
    )

    if subject_id == subject.subject_id and status == subject.status:
        return subject

    return ComparisonSubject(
        subject_kind=subject.subject_kind,
        subject_id=subject_id,
        status=status,
        required=subject.required,
        execution_reliable=subject.execution_reliable,
        error_kind=subject.error_kind,
        diagnostic_class=subject.diagnostic_class,
        blocked_by=subject.blocked_by,
        timed_out=subject.timed_out,
        first_error=subject.first_error,
        fingerprint=subject.fingerprint,
        scan_counts=subject.scan_counts,
        execution_state=subject.execution_state,
        gold_match=subject.gold_match,
        normalization_version=subject.normalization_version,
        script_hash=subject.script_hash,
        section_completion=subject.section_completion,
        artifact_ids=subject.artifact_ids,
    )


def normalize_subject_id(
    subject_kind: RegressionSubjectKind,
    subject_id: str,
) -> str:
    if not isinstance(subject_kind, RegressionSubjectKind):
        raise TypeError("subject_kind must be a RegressionSubjectKind")
    if not isinstance(subject_id, str):
        raise TypeError("subject_id must be a string")
    if not subject_id or not subject_id.strip():
        raise ValueError("subject_id must not be empty")
    if "\x00" in subject_id:
        raise ValueError("subject_id must not contain NUL characters")

    if subject_kind is not RegressionSubjectKind.FILE:
        return subject_id

    portable = subject_id.replace("\\", "/")
    path = PurePosixPath(portable)

    if path.is_absolute():
        raise ValueError("file subject_id must be project-relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(
            "file subject_id must not contain empty, '.' or '..' segments"
        )
    if path.parts and path.parts[0].endswith(":"):
        raise ValueError("file subject_id must not contain a drive prefix")

    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ValueError("file subject_id must identify a project file")
    return normalized


def normalize_status(
    status: str | ValidationStatus | OverallStatus,
    *,
    subject_kind: RegressionSubjectKind,
) -> str:
    if isinstance(status, (ValidationStatus, OverallStatus)):
        value = status.value
    elif isinstance(status, str):
        value = status
    else:
        raise TypeError(
            "status must be a ValidationStatus, OverallStatus or string"
        )

    if value not in _STATUS_VALUES:
        raise ValueError(f"unsupported regression status {value!r}")

    if (
        subject_kind is RegressionSubjectKind.RUN
        and value == ValidationStatus.SKIPPED.value
    ):
        raise ValueError("run subjects cannot use SKIPPED status")

    return value


def classify_transition(
    previous: ComparisonSubject,
    current: ComparisonSubject,
) -> ChangeKind:
    _require_same_identity(previous, current)
    previous_status = normalize_status(
        previous.status,
        subject_kind=previous.subject_kind,
    )
    current_status = normalize_status(
        current.status,
        subject_kind=current.subject_kind,
    )

    if previous_status == current_status:
        return ChangeKind.UNCHANGED

    if previous_status == ValidationStatus.OK.value:
        if current_status in {
            ValidationStatus.FAIL.value,
            ValidationStatus.ERROR.value,
        }:
            return ChangeKind.REGRESSED
        if current_status == ValidationStatus.SKIPPED.value:
            return (
                ChangeKind.REGRESSED
                if previous.required is True
                else ChangeKind.UNCHANGED
            )

    if previous_status == ValidationStatus.FAIL.value:
        if current_status == ValidationStatus.OK.value:
            return ChangeKind.IMPROVED
        if current_status == ValidationStatus.ERROR.value:
            return ChangeKind.REGRESSED
        return ChangeKind.UNCHANGED

    if previous_status == ValidationStatus.ERROR.value:
        if current_status == ValidationStatus.OK.value:
            return ChangeKind.IMPROVED
        if current_status == ValidationStatus.FAIL.value:
            return (
                ChangeKind.IMPROVED
                if current.execution_reliable is True
                else ChangeKind.UNCHANGED
            )
        return ChangeKind.UNCHANGED

    if previous_status == ValidationStatus.SKIPPED.value:
        required_in_both = (
            previous.required is True and current.required is True
        )
        newly_required = (
            previous.required is False and current.required is True
        )

        if current_status == ValidationStatus.OK.value:
            return (
                ChangeKind.IMPROVED
                if required_in_both
                else ChangeKind.UNCHANGED
            )

        if current_status in {
            ValidationStatus.FAIL.value,
            ValidationStatus.ERROR.value,
        }:
            return (
                ChangeKind.REGRESSED
                if newly_required
                else ChangeKind.UNCHANGED
            )

    return ChangeKind.UNCHANGED


def build_new_entry(subject: ComparisonSubject) -> DiffEntry:
    normalized = normalize_subject(subject)
    return DiffEntry(
        subject_kind=normalized.subject_kind,
        subject_id=normalized.subject_id,
        previous_status=None,
        current_status=normalized.status,
        change_kind=ChangeKind.NEW,
        message=(
            f"New {normalized.subject_kind.value} "
            f"with status {normalized.status}."
        ),
    )


def build_removed_entry(subject: ComparisonSubject) -> DiffEntry:
    normalized = normalize_subject(subject)
    return DiffEntry(
        subject_kind=normalized.subject_kind,
        subject_id=normalized.subject_id,
        previous_status=normalized.status,
        current_status=None,
        change_kind=ChangeKind.REMOVED,
        message=(
            f"Removed {normalized.subject_kind.value}; "
            f"previous status was {normalized.status}."
        ),
    )


def build_transition_entry(
    previous: ComparisonSubject,
    current: ComparisonSubject,
) -> DiffEntry:
    previous_normalized = normalize_subject(previous)
    current_normalized = normalize_subject(current)
    _require_same_identity(previous_normalized, current_normalized)

    change_kind = classify_transition(
        previous_normalized,
        current_normalized,
    )
    message = build_transition_message(
        previous_normalized,
        current_normalized,
        change_kind=change_kind,
    )

    return DiffEntry(
        subject_kind=current_normalized.subject_kind,
        subject_id=current_normalized.subject_id,
        previous_status=previous_normalized.status,
        current_status=current_normalized.status,
        change_kind=change_kind,
        message=message,
    )


def build_transition_message(
    previous: ComparisonSubject,
    current: ComparisonSubject,
    *,
    change_kind: ChangeKind | None = None,
) -> str:
    _require_same_identity(previous, current)
    resolved_change = (
        classify_transition(previous, current)
        if change_kind is None
        else change_kind
    )

    if not isinstance(resolved_change, ChangeKind):
        raise TypeError("change_kind must be a ChangeKind or None")

    if previous.status != current.status:
        suffix = _transition_context(previous, current, resolved_change)
        message = f"Status changed: {previous.status} -> {current.status}."
        return f"{message} {suffix}" if suffix else message

    detail = _first_detail_message(previous, current)
    if detail is not None:
        return f"Status unchanged at {current.status}; {detail}."

    return f"Status unchanged at {current.status}."


def sort_diff_entries(
    entries: Iterable[DiffEntry],
) -> tuple[DiffEntry, ...]:
    if isinstance(entries, (str, bytes)):
        raise TypeError("entries must be an iterable of DiffEntry values")

    normalized = tuple(entries)
    if not all(isinstance(entry, DiffEntry) for entry in normalized):
        raise TypeError("entries must contain only DiffEntry values")

    return tuple(
        sorted(
            normalized,
            key=lambda entry: (
                _CHANGE_ORDER[entry.change_kind],
                _SUBJECT_ORDER[entry.subject_kind],
                _subject_sort_key(
                    entry.subject_kind,
                    entry.subject_id,
                ),
            ),
        )
    )


def count_changes(
    entries: Iterable[DiffEntry],
) -> dict[ChangeKind, int]:
    counts = {change_kind: 0 for change_kind in ChangeKind}

    for entry in entries:
        if not isinstance(entry, DiffEntry):
            raise TypeError("entries must contain only DiffEntry values")
        counts[entry.change_kind] += 1

    return counts


def has_regressions(
    entries: Iterable[DiffEntry],
    *,
    subject_kinds: Sequence[RegressionSubjectKind] | None = None,
) -> bool:
    allowed = (
        None
        if subject_kinds is None
        else _normalize_subject_kinds(subject_kinds)
    )

    for entry in entries:
        if not isinstance(entry, DiffEntry):
            raise TypeError("entries must contain only DiffEntry values")
        if entry.change_kind is not ChangeKind.REGRESSED:
            continue
        if allowed is None or entry.subject_kind in allowed:
            return True

    return False


def _transition_context(
    previous: ComparisonSubject,
    current: ComparisonSubject,
    change_kind: ChangeKind,
) -> str:
    if (
        previous.status == ValidationStatus.ERROR.value
        and current.status == ValidationStatus.FAIL.value
    ):
        if change_kind is ChangeKind.IMPROVED:
            return "Execution is now reliable, but validation still fails."
        return "Execution reliability is not proven."

    if previous.status == ValidationStatus.OK.value and (
        current.status == ValidationStatus.SKIPPED.value
    ):
        return (
            "The previously required subject was skipped."
            if previous.required is True
            else "The skip is not classified as a regression."
        )

    if previous.status == ValidationStatus.SKIPPED.value:
        if current.required is True and previous.required is False:
            return "The subject is now required."
        if previous.required is True and current.required is True:
            return "The subject is required in both scopes."
        return "Required-scope equivalence is not established."

    return ""


def _first_detail_message(
    previous: ComparisonSubject,
    current: ComparisonSubject,
) -> str | None:
    comparisons = (
        ("error kind", previous.error_kind, current.error_kind),
        (
            "diagnostic class",
            previous.diagnostic_class,
            current.diagnostic_class,
        ),
        (
            "blocker roots",
            previous.blocked_by,
            current.blocked_by,
        ),
        (
            "timeout state",
            previous.timed_out,
            current.timed_out,
        ),
        (
            "first error",
            previous.first_error,
            current.first_error,
        ),
        (
            "source fingerprint",
            previous.fingerprint,
            current.fingerprint,
        ),
        (
            "scan findings",
            previous.scan_counts,
            current.scan_counts,
        ),
        (
            "required flag",
            previous.required,
            current.required,
        ),
        (
            "execution state",
            previous.execution_state,
            current.execution_state,
        ),
        (
            "gold match",
            previous.gold_match,
            current.gold_match,
        ),
        (
            "normalization version",
            previous.normalization_version,
            current.normalization_version,
        ),
        (
            "script hash",
            previous.script_hash,
            current.script_hash,
        ),
        (
            "section completion",
            previous.section_completion,
            current.section_completion,
        ),
        (
            "produced artifact set",
            previous.artifact_ids,
            current.artifact_ids,
        ),
    )

    for label, old_value, new_value in comparisons:
        if old_value != new_value:
            return (
                f"{label} changed: "
                f"{_display_value(old_value)} -> "
                f"{_display_value(new_value)}"
            )

    return None


def _display_value(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, tuple):
        if not value:
            return "none"
        return ", ".join(str(item) for item in value)
    return str(value)


def _require_same_identity(
    previous: ComparisonSubject,
    current: ComparisonSubject,
) -> None:
    if not isinstance(previous, ComparisonSubject):
        raise TypeError("previous must be a ComparisonSubject")
    if not isinstance(current, ComparisonSubject):
        raise TypeError("current must be a ComparisonSubject")

    previous_identity = (
        previous.subject_kind,
        normalize_subject_id(
            previous.subject_kind,
            previous.subject_id,
        ),
    )
    current_identity = (
        current.subject_kind,
        normalize_subject_id(
            current.subject_kind,
            current.subject_id,
        ),
    )

    if previous_identity != current_identity:
        raise ValueError(
            "previous and current subjects must have the same identity"
        )


def _subject_sort_key(
    subject_kind: RegressionSubjectKind,
    subject_id: str,
) -> str:
    normalized = normalize_subject_id(subject_kind, subject_id)
    return normalized.casefold()


def _normalize_subject_kinds(
    values: Sequence[RegressionSubjectKind],
) -> frozenset[RegressionSubjectKind]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            "subject_kinds must be a sequence of RegressionSubjectKind values"
        )

    normalized = frozenset(values)
    if not all(
        isinstance(value, RegressionSubjectKind)
        for value in normalized
    ):
        raise TypeError(
            "subject_kinds must contain only RegressionSubjectKind values"
        )
    return normalized


__all__ = (
    "build_diff_entries",
    "build_new_entry",
    "build_removed_entry",
    "build_transition_entry",
    "build_transition_message",
    "classify_transition",
    "count_changes",
    "has_regressions",
    "index_subjects",
    "normalize_status",
    "normalize_subject",
    "normalize_subject_id",
    "sort_diff_entries",
)
