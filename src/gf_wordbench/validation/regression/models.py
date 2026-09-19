"""Immutable models for deterministic GF Wordbench regression comparison."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import PurePosixPath
import re
from types import MappingProxyType
from typing import Final, TypeAlias, TypeVar

from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)

StatusValue: TypeAlias = ValidationStatus | OverallStatus
SubjectIdentity: TypeAlias = tuple["RegressionSubjectKind", str]
StringMap: TypeAlias = Mapping[str, str]
CountMap: TypeAlias = Mapping[str, int]
BooleanMap: TypeAlias = Mapping[str, bool]

_EnumT = TypeVar("_EnumT", bound=StrEnum)
_MapKeyT = TypeVar("_MapKeyT")
_MapValueT = TypeVar("_MapValueT")

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9]+(?:\.[0-9]+){1,2}$")
_CANONICAL_RUN_SUBJECT_IDS: Final[frozenset[str]] = frozenset(
    {
        "overall-status",
        "release-pgf",
        "required-scenarios",
    }
)
_CHANGE_ORDER: Final[dict[ChangeKind, int]] = {
    ChangeKind.REGRESSED: 0,
    ChangeKind.NEW: 1,
    ChangeKind.IMPROVED: 2,
    ChangeKind.REMOVED: 3,
    ChangeKind.UNCHANGED: 4,
}
@unique
class RegressionSubjectKind(StrEnum):
    FILE = "file"
    SCENARIO = "scenario"
    RUN = "run"


_SUBJECT_ORDER: Final[dict[RegressionSubjectKind, int]] = {
    RegressionSubjectKind.RUN: 0,
    RegressionSubjectKind.FILE: 1,
    RegressionSubjectKind.SCENARIO: 2,
}


@unique
class ComparisonState(StrEnum):
    DISABLED = "disabled"
    NO_BASELINE = "no_baseline"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _optional_text(
    value: object | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name=field_name)


def _require_bool(value: object, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a bool")
    return value


def _optional_bool(
    value: object | None,
    *,
    field_name: str,
) -> bool | None:
    if value is None:
        return None
    return _require_bool(value, field_name=field_name)


def _optional_int(
    value: object | None,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer or None")
    return value


def _normalize_strings(
    values: Iterable[object],
    *,
    field_name: str,
    unique: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        item = _require_text(
            value,
            field_name=f"{field_name}[{index}]",
        )
        if unique and item in seen:
            raise ValueError(f"{field_name} contains duplicate value {item!r}")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _freeze_string_map(
    values: Mapping[_MapKeyT, _MapValueT],
    *,
    field_name: str,
) -> StringMap:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, str] = {}
    for raw_key, raw_value in values.items():
        key = _require_text(
            raw_key,
            field_name=f"{field_name} key",
        )
        value = _require_text(
            raw_value,
            field_name=f"{field_name}[{key!r}]",
            allow_empty=True,
        )
        normalized[key] = value
    return MappingProxyType(normalized)


def _freeze_count_map(
    values: Mapping[_MapKeyT, _MapValueT],
    *,
    field_name: str,
) -> CountMap:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, int] = {}
    for raw_key, raw_value in values.items():
        key = _require_text(
            raw_key,
            field_name=f"{field_name} key",
        )
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise TypeError(f"{field_name}[{key!r}] must be an integer")
        if raw_value < 0:
            raise ValueError(f"{field_name}[{key!r}] must be non-negative")
        normalized[key] = raw_value
    return MappingProxyType(normalized)


def _freeze_boolean_map(
    values: Mapping[_MapKeyT, _MapValueT],
    *,
    field_name: str,
) -> BooleanMap:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, bool] = {}
    for raw_key, raw_value in values.items():
        key = _require_text(
            raw_key,
            field_name=f"{field_name} key",
        )
        normalized[key] = _require_bool(
            raw_value,
            field_name=f"{field_name}[{key!r}]",
        )
    return MappingProxyType(normalized)


def _coerce_subject_kind(
    value: RegressionSubjectKind | str,
) -> RegressionSubjectKind:
    if isinstance(value, RegressionSubjectKind):
        return value
    try:
        return RegressionSubjectKind(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("subject_kind must be file, scenario, or run") from exc


def _coerce_change_kind(value: ChangeKind | str) -> ChangeKind:
    if isinstance(value, ChangeKind):
        return value
    try:
        return ChangeKind(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "change_kind must be unchanged, improved, regressed, new, or removed"
        ) from exc


def _coerce_comparison_state(
    value: ComparisonState | str,
) -> ComparisonState:
    if isinstance(value, ComparisonState):
        return value
    try:
        return ComparisonState(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "state must be disabled, no_baseline, completed, unavailable, or error"
        ) from exc


def _coerce_validation_mode(
    value: ValidationMode | str,
) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    try:
        return ValidationMode(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("mode must be quick, checkpoint, release, or diagnostic") from exc


def _coerce_optional_enum(
    value: object | None,
    enum_type: type[_EnumT],
    *,
    field_name: str,
) -> _EnumT | None:
    if value is None:
        return None
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be {enum_type.__name__}, string, or None")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a canonical {enum_type.__name__}") from exc


def _normalize_subject_id(
    kind: RegressionSubjectKind,
    value: object,
) -> str:
    subject_id = _require_text(value, field_name="subject_id")

    if kind is RegressionSubjectKind.SCENARIO:
        return str(validate_scenario_id(subject_id))

    if kind is RegressionSubjectKind.RUN:
        if subject_id not in _CANONICAL_RUN_SUBJECT_IDS:
            supported = ", ".join(sorted(_CANONICAL_RUN_SUBJECT_IDS))
            raise ValueError(
                f"unsupported run subject_id {subject_id!r}; expected one of {supported}"
            )
        return subject_id

    if "\\" in subject_id:
        raise ValueError("file subject_id must use forward-slash separators")
    path = PurePosixPath(subject_id)
    if path.is_absolute():
        raise ValueError("file subject_id must be project-relative")
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("file subject_id must be a normalized contained path")
    if re.match(r"^[A-Za-z]:", subject_id):
        raise ValueError("file subject_id must not contain a drive letter")
    return path.as_posix()


def _coerce_status(
    value: object,
    *,
    subject_kind: RegressionSubjectKind,
    field_name: str,
) -> StatusValue:
    enum_type: type[ValidationStatus] | type[OverallStatus]
    if subject_kind is RegressionSubjectKind.RUN:
        enum_type = OverallStatus
    else:
        enum_type = ValidationStatus

    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a canonical status or string")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not valid for {subject_kind.value}") from exc


def _coerce_optional_status(
    value: object | None,
    *,
    subject_kind: RegressionSubjectKind,
    field_name: str,
) -> StatusValue | None:
    if value is None:
        return None
    return _coerce_status(
        value,
        subject_kind=subject_kind,
        field_name=field_name,
    )


@dataclass(frozen=True, slots=True)
class SubjectDetails:
    required: bool | None = None
    execution_state: ExecutionState | None = None
    error_kind: ErrorKind | None = None
    diagnostic_class: DiagnosticClass | None = None
    blocked_by: tuple[str, ...] = ()
    first_error: str = ""
    timed_out: bool | None = None
    exit_code: int | None = None
    fingerprint_sha256: str | None = None
    scan_counts: CountMap = field(default_factory=dict)
    gold_match: bool | None = None
    normalization_version: str | None = None
    script_sha256: str | None = None
    section_completion: BooleanMap = field(default_factory=dict)
    produced_artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = _optional_bool(
            self.required,
            field_name="required",
        )
        execution_state = _coerce_optional_enum(
            self.execution_state,
            ExecutionState,
            field_name="execution_state",
        )
        error_kind = _coerce_optional_enum(
            self.error_kind,
            ErrorKind,
            field_name="error_kind",
        )
        diagnostic_class = _coerce_optional_enum(
            self.diagnostic_class,
            DiagnosticClass,
            field_name="diagnostic_class",
        )
        blocked_by = _normalize_strings(
            self.blocked_by,
            field_name="blocked_by",
            unique=True,
        )
        _require_text(
            self.first_error,
            field_name="first_error",
            allow_empty=True,
        )
        timed_out = _optional_bool(
            self.timed_out,
            field_name="timed_out",
        )
        exit_code = _optional_int(
            self.exit_code,
            field_name="exit_code",
        )
        fingerprint = _optional_text(
            self.fingerprint_sha256,
            field_name="fingerprint_sha256",
        )
        script_hash = _optional_text(
            self.script_sha256,
            field_name="script_sha256",
        )
        scan_counts = _freeze_count_map(
            self.scan_counts,
            field_name="scan_counts",
        )
        gold_match = _optional_bool(
            self.gold_match,
            field_name="gold_match",
        )
        normalization_version = _optional_text(
            self.normalization_version,
            field_name="normalization_version",
        )
        sections = _freeze_boolean_map(
            self.section_completion,
            field_name="section_completion",
        )
        artifacts = _normalize_strings(
            self.produced_artifacts,
            field_name="produced_artifacts",
            unique=True,
        )

        for field_name, digest in (
            ("fingerprint_sha256", fingerprint),
            ("script_sha256", script_hash),
        ):
            if digest is not None and _SHA256_RE.fullmatch(digest) is None:
                raise ValueError(f"{field_name} must contain 64 lowercase hexadecimal characters")

        if timed_out is True and execution_state not in {
            None,
            ExecutionState.TIMED_OUT,
        }:
            raise ValueError("timed_out=True conflicts with execution_state")
        if execution_state is ExecutionState.TIMED_OUT and timed_out is False:
            raise ValueError("execution_state timed_out conflicts with timed_out=False")
        if execution_state is ExecutionState.LAUNCH_FAILED and exit_code is not None:
            raise ValueError("a launch failure must not fabricate an exit code")

        object.__setattr__(self, "required", required)
        object.__setattr__(
            self,
            "execution_state",
            execution_state,
        )
        object.__setattr__(self, "error_kind", error_kind)
        object.__setattr__(
            self,
            "diagnostic_class",
            diagnostic_class,
        )
        object.__setattr__(self, "blocked_by", blocked_by)
        object.__setattr__(self, "timed_out", timed_out)
        object.__setattr__(self, "exit_code", exit_code)
        object.__setattr__(
            self,
            "fingerprint_sha256",
            fingerprint,
        )
        object.__setattr__(self, "scan_counts", scan_counts)
        object.__setattr__(self, "gold_match", gold_match)
        object.__setattr__(
            self,
            "normalization_version",
            normalization_version,
        )
        object.__setattr__(self, "script_sha256", script_hash)
        object.__setattr__(
            self,
            "section_completion",
            sections,
        )
        object.__setattr__(
            self,
            "produced_artifacts",
            artifacts,
        )


@dataclass(frozen=True, slots=True)
class RegressionSubject:
    subject_kind: RegressionSubjectKind
    subject_id: str
    status: StatusValue
    message: str = ""
    details: SubjectDetails = field(default_factory=SubjectDetails)

    def __post_init__(self) -> None:
        kind = _coerce_subject_kind(self.subject_kind)
        subject_id = _normalize_subject_id(kind, self.subject_id)
        status = _coerce_status(
            self.status,
            subject_kind=kind,
            field_name="status",
        )
        _require_text(
            self.message,
            field_name="message",
            allow_empty=True,
        )
        if not isinstance(self.details, SubjectDetails):
            raise TypeError("details must be SubjectDetails")

        if kind is RegressionSubjectKind.RUN:
            if self.details.required is not None:
                raise ValueError("run subjects do not use a required flag")
            if self.details.execution_state is not None:
                raise ValueError("run subjects do not own execution_state")
            if self.details.gold_match is not None:
                raise ValueError("run subjects do not own gold_match")

        object.__setattr__(self, "subject_kind", kind)
        object.__setattr__(self, "subject_id", subject_id)
        object.__setattr__(self, "status", status)

    @property
    def identity(self) -> SubjectIdentity:
        return (self.subject_kind, self.subject_id)

    @property
    def identity_key(self) -> tuple[int, str]:
        return (
            _SUBJECT_ORDER[self.subject_kind],
            self.subject_id.casefold(),
        )


@dataclass(frozen=True, slots=True)
class DiffEntry:
    subject_kind: RegressionSubjectKind
    subject_id: str
    previous_status: StatusValue | None
    current_status: StatusValue | None
    change_kind: ChangeKind
    message: str

    def __post_init__(self) -> None:
        kind = _coerce_subject_kind(self.subject_kind)
        subject_id = _normalize_subject_id(kind, self.subject_id)
        previous_status = _coerce_optional_status(
            self.previous_status,
            subject_kind=kind,
            field_name="previous_status",
        )
        current_status = _coerce_optional_status(
            self.current_status,
            subject_kind=kind,
            field_name="current_status",
        )
        change_kind = _coerce_change_kind(self.change_kind)
        message = _require_text(
            self.message,
            field_name="message",
        )

        if change_kind is ChangeKind.NEW:
            if previous_status is not None or current_status is None:
                raise ValueError(
                    "new requires an absent previous status and a present current status"
                )
        elif change_kind is ChangeKind.REMOVED:
            if previous_status is None or current_status is not None:
                raise ValueError(
                    "removed requires a present previous status and an absent current status"
                )
        elif previous_status is None or current_status is None:
            raise ValueError("unchanged, improved, and regressed require both statuses")

        if change_kind is ChangeKind.UNCHANGED:
            if previous_status != current_status:
                raise ValueError("unchanged requires equal primary statuses")

        object.__setattr__(self, "subject_kind", kind)
        object.__setattr__(self, "subject_id", subject_id)
        object.__setattr__(
            self,
            "previous_status",
            previous_status,
        )
        object.__setattr__(self, "current_status", current_status)
        object.__setattr__(self, "change_kind", change_kind)
        object.__setattr__(self, "message", message)

    @property
    def identity(self) -> SubjectIdentity:
        return (self.subject_kind, self.subject_id)

    @property
    def sort_key(self) -> tuple[int, int, str, str]:
        return (
            _CHANGE_ORDER[self.change_kind],
            _SUBJECT_ORDER[self.subject_kind],
            self.subject_id.casefold(),
            self.subject_id,
        )


RegressionChange = DiffEntry


@dataclass(frozen=True, slots=True)
class RunSnapshotMetadata:
    run_id: str
    project_id: str
    mode: ValidationMode
    schema_id: str
    schema_version: str
    target_identity: str | None = None
    gf_version: str | None = None
    completed: bool = True
    manifest_available: bool = False
    legacy_schema: bool = False
    attributes: StringMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        run_id = _require_text(self.run_id, field_name="run_id")
        project_id = _require_text(
            self.project_id,
            field_name="project_id",
        )
        mode = _coerce_validation_mode(self.mode)
        schema_id = _require_text(
            self.schema_id,
            field_name="schema_id",
        )
        schema_version = _require_text(
            self.schema_version,
            field_name="schema_version",
        )
        if _SCHEMA_VERSION_RE.fullmatch(schema_version) is None:
            raise ValueError(
                "schema_version must use major.minor or major.minor.patch numeric form"
            )
        target_identity = _optional_text(
            self.target_identity,
            field_name="target_identity",
        )
        gf_version = _optional_text(
            self.gf_version,
            field_name="gf_version",
        )
        completed = _require_bool(
            self.completed,
            field_name="completed",
        )
        manifest_available = _require_bool(
            self.manifest_available,
            field_name="manifest_available",
        )
        legacy_schema = _require_bool(
            self.legacy_schema,
            field_name="legacy_schema",
        )
        attributes = _freeze_string_map(
            self.attributes,
            field_name="attributes",
        )

        if mode is ValidationMode.QUICK and target_identity is None:
            raise ValueError("quick snapshot metadata requires target_identity")

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(
            self,
            "schema_version",
            schema_version,
        )
        object.__setattr__(
            self,
            "target_identity",
            target_identity,
        )
        object.__setattr__(self, "gf_version", gf_version)
        object.__setattr__(self, "completed", completed)
        object.__setattr__(
            self,
            "manifest_available",
            manifest_available,
        )
        object.__setattr__(
            self,
            "legacy_schema",
            legacy_schema,
        )
        object.__setattr__(self, "attributes", attributes)


@dataclass(frozen=True, slots=True)
class RegressionSnapshot:
    metadata: RunSnapshotMetadata
    subjects: tuple[RegressionSubject, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, RunSnapshotMetadata):
            raise TypeError("metadata must be RunSnapshotMetadata")

        subjects = tuple(self.subjects)
        if not all(isinstance(subject, RegressionSubject) for subject in subjects):
            raise TypeError("subjects must contain RegressionSubject values")

        seen: set[SubjectIdentity] = set()
        for subject in subjects:
            if subject.identity in seen:
                raise ValueError(
                    "duplicate regression subject identity: "
                    f"{subject.subject_kind.value}:{subject.subject_id}"
                )
            seen.add(subject.identity)

        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
        )

        object.__setattr__(self, "subjects", subjects)
        object.__setattr__(self, "warnings", warnings)

    def index(self) -> Mapping[SubjectIdentity, RegressionSubject]:
        return MappingProxyType({subject.identity: subject for subject in self.subjects})

    @property
    def ordered_subjects(self) -> tuple[RegressionSubject, ...]:
        return tuple(
            sorted(
                self.subjects,
                key=lambda subject: subject.identity_key,
            )
        )


@dataclass(frozen=True, slots=True)
class CompatibilityDecision:
    compatible: bool
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        compatible = _require_bool(
            self.compatible,
            field_name="compatible",
        )
        reasons = _normalize_strings(
            self.reasons,
            field_name="reasons",
            unique=True,
        )
        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
            unique=True,
        )

        if compatible and reasons:
            raise ValueError("a compatible decision must not contain rejection reasons")
        if not compatible and not reasons:
            raise ValueError("an incompatible decision requires at least one reason")

        object.__setattr__(self, "compatible", compatible)
        object.__setattr__(self, "reasons", reasons)
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True, slots=True)
class RegressionComparison:
    state: ComparisonState
    entries: tuple[DiffEntry, ...] = ()
    warnings: tuple[str, ...] = ()
    baseline: RunSnapshotMetadata | None = None

    def __post_init__(self) -> None:
        state = _coerce_comparison_state(self.state)
        entries = tuple(self.entries)
        if not all(isinstance(entry, DiffEntry) for entry in entries):
            raise TypeError("entries must contain DiffEntry values")

        seen: set[SubjectIdentity] = set()
        for entry in entries:
            if entry.identity in seen:
                raise ValueError(
                    f"duplicate diff identity: {entry.subject_kind.value}:{entry.subject_id}"
                )
            seen.add(entry.identity)

        canonical_entries = tuple(sorted(entries, key=lambda entry: entry.sort_key))
        if entries != canonical_entries:
            raise ValueError("entries must use canonical regression ordering")

        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
        )
        if self.baseline is not None and not isinstance(
            self.baseline,
            RunSnapshotMetadata,
        ):
            raise TypeError("baseline must be RunSnapshotMetadata or None")

        if state is ComparisonState.COMPLETED:
            if self.baseline is None:
                raise ValueError("completed comparison requires baseline metadata")
        else:
            if entries:
                raise ValueError("only a completed comparison may contain entries")

        if (
            state
            in {
                ComparisonState.DISABLED,
                ComparisonState.NO_BASELINE,
            }
            and self.baseline is not None
        ):
            raise ValueError(f"{state.value} comparison must not contain a baseline")

        if (
            state
            in {
                ComparisonState.UNAVAILABLE,
                ComparisonState.ERROR,
            }
            and not warnings
        ):
            raise ValueError(f"{state.value} comparison requires a warning")

        object.__setattr__(self, "state", state)
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "warnings", warnings)

    @property
    def counts(self) -> Mapping[ChangeKind, int]:
        counts = dict.fromkeys(ChangeKind, 0)
        for entry in self.entries:
            counts[entry.change_kind] += 1
        return MappingProxyType(counts)

    @property
    def regressions(self) -> tuple[DiffEntry, ...]:
        return tuple(entry for entry in self.entries if entry.change_kind is ChangeKind.REGRESSED)


# Historical internal name retained for comparator compatibility.
ComparisonSubject = RegressionSubject

__all__ = (
    "BooleanMap",
    "ComparisonState",
    "CompatibilityDecision",
    "CountMap",
    "DiffEntry",
    "RegressionChange",
    "RegressionComparison",
    "RegressionSnapshot",
    "RegressionSubject",
    "RegressionSubjectKind",
    "RunSnapshotMetadata",
    "StatusValue",
    "StringMap",
    "SubjectDetails",
    "SubjectIdentity",
)
