"""Stable subject identity and deterministic run-result matching."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
from types import MappingProxyType
from typing import Final, Generic, Literal, TypeAlias, TypeVar

from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    normalize_environment_path,
    normalize_portable_path,
    portable_identity_key,
    relative_portable_path,
)
from gf_wordbench.kernel.statuses import OverallStatus, ValidationStatus
from gf_wordbench.runs.models.results import FileResult, RunResult
from gf_wordbench.validation.scenarios.models import ScenarioResult

SubjectKind: TypeAlias = Literal["run", "file", "scenario"]
SubjectKey: TypeAlias = tuple[SubjectKind, str]

_SubjectT = TypeVar("_SubjectT", bound=object)

_SUBJECT_KIND_ORDER: Final[Mapping[SubjectKind, int]] = MappingProxyType(
    {"run": 0, "file": 1, "scenario": 2}
)
_DOCUMENTED_RUN_SUBJECT_IDS: Final[frozenset[str]] = frozenset(
    {"overall-status", "release-pgf", "required-scenarios"}
)


class SubjectMatchingError(ValueError):
    """Base error for invalid or ambiguous regression subject matching."""


class DuplicateSubjectIdentityError(SubjectMatchingError):
    """Raised when one run exposes the same canonical identity more than once."""


@dataclass(frozen=True, slots=True)
class SubjectIdentity:
    """Canonical display identity for one comparable subject."""

    subject_kind: SubjectKind
    subject_id: str

    def __post_init__(self) -> None:
        _require_subject_kind(self.subject_kind)
        _require_subject_id(self.subject_id, field="subject_id")

    @property
    def display(self) -> str:
        return f"{self.subject_kind}:{self.subject_id}"


@dataclass(frozen=True, slots=True)
class RunComparableSubject:
    """One documented run-level comparison subject."""

    subject_id: str
    status: OverallStatus

    def __post_init__(self) -> None:
        subject_id = _require_run_subject_id(self.subject_id)
        if not isinstance(self.status, OverallStatus):
            raise TypeError("status must be an OverallStatus")
        object.__setattr__(self, "subject_id", subject_id)


ComparableSubject: TypeAlias = FileResult | ScenarioResult | RunComparableSubject


@dataclass(frozen=True, slots=True)
class IndexedSubject(Generic[_SubjectT]):
    """A subject paired with its canonical identity and comparison key."""

    identity: SubjectIdentity
    comparison_key: SubjectKey
    subject: _SubjectT

    def __post_init__(self) -> None:
        if not isinstance(self.identity, SubjectIdentity):
            raise TypeError("identity must be a SubjectIdentity")
        _validate_subject_key(self.comparison_key)
        if self.comparison_key[0] != self.identity.subject_kind:
            raise ValueError("comparison key kind must match identity kind")


@dataclass(frozen=True, slots=True)
class SubjectMatch:
    """One deterministic previous/current subject match."""

    identity: SubjectIdentity
    previous: ComparableSubject | None
    current: ComparableSubject | None

    def __post_init__(self) -> None:
        if not isinstance(self.identity, SubjectIdentity):
            raise TypeError("identity must be a SubjectIdentity")
        if self.previous is None and self.current is None:
            raise ValueError("a subject match requires at least one side")

    @property
    def is_new(self) -> bool:
        return self.previous is None

    @property
    def is_removed(self) -> bool:
        return self.current is None

    @property
    def is_paired(self) -> bool:
        return self.previous is not None and self.current is not None


def canonical_file_subject_id(
    file_path: Path,
    *,
    source_root: Path,
) -> str:
    """Return a canonical language-source-relative file subject ID."""

    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a Path")

    root = normalize_environment_path(
        source_root,
        role="language source root",
    )
    if file_path.is_absolute():
        portable = relative_portable_path(
            root,
            file_path,
            role="regression file subject",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
    else:
        portable = normalize_portable_path(
            file_path,
            role="regression file subject",
            allow_root=False,
            accept_backslash=True,
        )
    return portable.as_posix()


def file_subject_identity(
    result: FileResult,
    *,
    source_root: Path,
) -> SubjectIdentity:
    """Build the canonical identity of one file result."""

    if not isinstance(result, FileResult):
        raise TypeError("result must be a FileResult")
    if not isinstance(result.status, ValidationStatus):
        raise TypeError("file result status must be a ValidationStatus")
    return SubjectIdentity(
        subject_kind="file",
        subject_id=canonical_file_subject_id(
            result.file_path,
            source_root=source_root,
        ),
    )


def scenario_subject_identity(result: ScenarioResult) -> SubjectIdentity:
    """Build the canonical identity of one scenario result."""

    if not isinstance(result, ScenarioResult):
        raise TypeError("result must be a ScenarioResult")
    if not isinstance(result.status, ValidationStatus):
        raise TypeError("scenario result status must be a ValidationStatus")
    return SubjectIdentity(
        subject_kind="scenario",
        subject_id=str(validate_scenario_id(result.scenario_id)),
    )


def run_subject_identity(result: RunComparableSubject) -> SubjectIdentity:
    """Build the canonical identity of one documented run-level subject."""

    if not isinstance(result, RunComparableSubject):
        raise TypeError("result must be a RunComparableSubject")
    return SubjectIdentity(subject_kind="run", subject_id=result.subject_id)


def index_comparable_subjects(
    run_result: RunResult,
    *,
    run_subjects: Iterable[RunComparableSubject] = (),
    include_overall_status: bool = True,
    case_sensitive_paths: bool | None = None,
) -> Mapping[SubjectKey, IndexedSubject[ComparableSubject]]:
    """Index one run by stable subject identity without resolving duplicates."""

    if not isinstance(run_result, RunResult):
        raise TypeError("run_result must be a RunResult")
    if not isinstance(include_overall_status, bool):
        raise TypeError("include_overall_status must be a boolean")

    case_sensitive = _resolve_case_policy(case_sensitive_paths)
    source_root = _source_root(run_result)
    index: dict[SubjectKey, IndexedSubject[ComparableSubject]] = {}

    if include_overall_status:
        overall = RunComparableSubject(
            subject_id="overall-status",
            status=_require_overall_status(run_result.overall_status),
        )
        _insert_subject(
            index,
            overall,
            run_subject_identity(overall),
            case_sensitive_paths=case_sensitive,
        )

    for position, subject in enumerate(run_subjects):
        if not isinstance(subject, RunComparableSubject):
            raise TypeError(f"run_subjects[{position}] must be a RunComparableSubject")
        _insert_subject(
            index,
            subject,
            run_subject_identity(subject),
            case_sensitive_paths=case_sensitive,
        )

    for position, file_result in enumerate(run_result.file_results):
        if not isinstance(file_result, FileResult):
            raise TypeError(f"file_results[{position}] must be a FileResult")
        _insert_subject(
            index,
            file_result,
            file_subject_identity(file_result, source_root=source_root),
            case_sensitive_paths=case_sensitive,
        )

    for position, scenario_result in enumerate(run_result.scenario_results):
        if not isinstance(scenario_result, ScenarioResult):
            raise TypeError(f"scenario_results[{position}] must be a ScenarioResult")
        _insert_subject(
            index,
            scenario_result,
            scenario_subject_identity(scenario_result),
            case_sensitive_paths=case_sensitive,
        )

    ordered = dict(sorted(index.items(), key=_indexed_item_sort_key))
    return MappingProxyType(ordered)


def match_comparable_subjects(
    previous_run_result: RunResult,
    current_run_result: RunResult,
    *,
    previous_run_subjects: Iterable[RunComparableSubject] = (),
    current_run_subjects: Iterable[RunComparableSubject] = (),
    include_overall_status: bool = True,
    case_sensitive_paths: bool | None = None,
) -> tuple[SubjectMatch, ...]:
    """Match previous and current subjects by canonical identity."""

    case_sensitive = _resolve_case_policy(case_sensitive_paths)
    previous = index_comparable_subjects(
        previous_run_result,
        run_subjects=previous_run_subjects,
        include_overall_status=include_overall_status,
        case_sensitive_paths=case_sensitive,
    )
    current = index_comparable_subjects(
        current_run_result,
        run_subjects=current_run_subjects,
        include_overall_status=include_overall_status,
        case_sensitive_paths=case_sensitive,
    )

    matches: list[SubjectMatch] = []
    for key in sorted(previous.keys() | current.keys(), key=_subject_key_sort_key):
        previous_item = previous.get(key)
        current_item = current.get(key)
        identity = (
            current_item.identity
            if current_item is not None
            else _require_indexed(previous_item).identity
        )
        matches.append(
            SubjectMatch(
                identity=identity,
                previous=(previous_item.subject if previous_item is not None else None),
                current=(current_item.subject if current_item is not None else None),
            )
        )
    return tuple(matches)


def subject_status(subject: ComparableSubject) -> ValidationStatus | OverallStatus:
    """Return the canonical primary status of a comparable subject."""

    if isinstance(subject, RunComparableSubject):
        return subject.status
    if isinstance(subject, FileResult):
        if not isinstance(subject.status, ValidationStatus):
            raise TypeError("file result status must be a ValidationStatus")
        return subject.status
    if isinstance(subject, ScenarioResult):
        if not isinstance(subject.status, ValidationStatus):
            raise TypeError("scenario result status must be a ValidationStatus")
        return subject.status
    raise TypeError("unsupported comparable subject type")


def subject_required(subject: ComparableSubject) -> bool | None:
    """Return requiredness when the subject model defines it."""

    if isinstance(subject, ScenarioResult):
        if not isinstance(subject.required, bool):
            raise TypeError("scenario required must be a boolean")
        return subject.required
    if isinstance(subject, RunComparableSubject):
        return True
    if isinstance(subject, FileResult):
        return None
    raise TypeError("unsupported comparable subject type")


def _insert_subject(
    index: dict[SubjectKey, IndexedSubject[ComparableSubject]],
    subject: ComparableSubject,
    identity: SubjectIdentity,
    *,
    case_sensitive_paths: bool,
) -> None:
    key = _comparison_key(
        identity,
        case_sensitive_paths=case_sensitive_paths,
    )
    existing = index.get(key)
    if existing is not None:
        raise DuplicateSubjectIdentityError(
            "duplicate canonical regression subject identity: "
            f"{existing.identity.display!r} conflicts with "
            f"{identity.display!r}"
        )
    index[key] = IndexedSubject(
        identity=identity,
        comparison_key=key,
        subject=subject,
    )


def _comparison_key(
    identity: SubjectIdentity,
    *,
    case_sensitive_paths: bool,
) -> SubjectKey:
    if identity.subject_kind == "file":
        normalized = portable_identity_key(
            identity.subject_id,
            role="regression file subject",
            case_sensitive=case_sensitive_paths,
        )
    else:
        normalized = identity.subject_id
    return identity.subject_kind, normalized


def _source_root(run_result: RunResult) -> Path:
    """Return the public language source root recorded by the run config.

    ``RunConfig.source_root`` resolves to the active
    ``ResolvedLanguageContext.language_directory`` and retains the documented
    legacy-profile fallback during migration. Regression matching therefore
    does not depend on ``project.project_root`` or rediscover source ownership.
    """

    try:
        source_root = run_result.run_config.source_root
    except AttributeError as exc:
        raise SubjectMatchingError("run_result.run_config.source_root is required") from exc
    if not isinstance(source_root, Path):
        raise TypeError("source_root must be a Path")
    return normalize_environment_path(
        source_root,
        role="language source root",
    )


def _resolve_case_policy(value: bool | None) -> bool:
    if value is None:
        return os.name != "nt"
    if not isinstance(value, bool):
        raise TypeError("case_sensitive_paths must be a boolean or None")
    return value


def _require_subject_kind(value: object) -> SubjectKind:
    if value == "run":
        return "run"
    if value == "file":
        return "file"
    if value == "scenario":
        return "scenario"
    raise ValueError(f"unsupported subject kind: {value!r}")


def _require_subject_id(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty without surrounding whitespace")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be single-line text without NUL")
    return value


def _require_run_subject_id(value: object) -> str:
    subject_id = _require_subject_id(value, field="run subject ID")
    if subject_id not in _DOCUMENTED_RUN_SUBJECT_IDS:
        supported = ", ".join(sorted(_DOCUMENTED_RUN_SUBJECT_IDS))
        raise ValueError(f"unsupported run subject ID {subject_id!r}; expected one of {supported}")
    return subject_id


def _require_overall_status(value: object) -> OverallStatus:
    if not isinstance(value, OverallStatus):
        raise TypeError("overall_status must be an OverallStatus")
    return value


def _validate_subject_key(value: object) -> SubjectKey:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError("comparison_key must be a two-item tuple")
    kind = _require_subject_kind(value[0])
    subject_id = _require_subject_id(value[1], field="comparison key subject ID")
    return kind, subject_id


def _require_indexed(
    value: IndexedSubject[ComparableSubject] | None,
) -> IndexedSubject[ComparableSubject]:
    if value is None:
        raise AssertionError("missing indexed subject")
    return value


def _indexed_item_sort_key(
    item: tuple[SubjectKey, IndexedSubject[ComparableSubject]],
) -> tuple[int, str, str]:
    return _subject_key_sort_key(item[0])


def _subject_key_sort_key(key: SubjectKey) -> tuple[int, str, str]:
    kind, subject_id = _validate_subject_key(key)
    return _SUBJECT_KIND_ORDER[kind], subject_id.casefold(), subject_id


__all__ = (
    "ComparableSubject",
    "DuplicateSubjectIdentityError",
    "IndexedSubject",
    "RunComparableSubject",
    "SubjectIdentity",
    "SubjectKey",
    "SubjectKind",
    "SubjectMatch",
    "SubjectMatchingError",
    "canonical_file_subject_id",
    "file_subject_identity",
    "index_comparable_subjects",
    "match_comparable_subjects",
    "run_subject_identity",
    "scenario_subject_identity",
    "subject_required",
    "subject_status",
)
