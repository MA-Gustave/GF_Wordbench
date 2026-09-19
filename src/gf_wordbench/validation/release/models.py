"""Immutable release-gate and release-decision models for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final, TypeVar

from gf_wordbench.kernel.ids import (
    ProjectId,
    RunId,
    validate_project_id,
    validate_run_id,
)
from gf_wordbench.kernel.statuses import ValidationStatus

__all__ = (
    "RELEASE_GATE_POLICY_VERSION",
    "ReleaseDecision",
    "ReleaseDecisionValue",
    "ReleaseGate",
    "ReleaseGateApplicability",
    "ReleaseGateResult",
    "validate_release_gate_id",
)

RELEASE_GATE_POLICY_VERSION: Final[str] = "1.1.0"

_GATE_ID_RE: Final[re.Pattern[str]] = re.compile(r"^RG-(?P<order>[0-9]{2})$")
_MAX_GATE_RESULTS: Final[int] = 256
_MAX_TEXT_ITEMS: Final[int] = 1024
_MAX_TEXT_LENGTH: Final[int] = 4096
_MAX_SUMMARY_LENGTH: Final[int] = 16384
_MAX_PATHS: Final[int] = 4096

_EnumT = TypeVar("_EnumT", bound=StrEnum)


@unique
class ReleaseGateApplicability(StrEnum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    NOT_APPLICABLE = "not_applicable"


@unique
class ReleaseDecisionValue(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    ERROR = "ERROR"


# Historical internal name retained for release decision services that still
# import the pre-canonical symbol.  It intentionally remains outside __all__.
ReleaseDecisionStatus = ReleaseDecisionValue


@dataclass(frozen=True, slots=True)
class ReleaseGate:
    gate_id: str
    name: str
    applicability: ReleaseGateApplicability
    owner: str
    order: int

    def __post_init__(self) -> None:
        gate_id = validate_release_gate_id(self.gate_id)
        name = _normalize_text(
            self.name,
            field="name",
            maximum=_MAX_TEXT_LENGTH,
        )
        owner = _normalize_text(
            self.owner,
            field="owner",
            maximum=_MAX_TEXT_LENGTH,
        )
        applicability = _require_enum(
            self.applicability,
            ReleaseGateApplicability,
            field="applicability",
        )
        order = _require_plain_int(
            self.order,
            field="order",
            minimum=0,
        )

        canonical_order = _gate_order(gate_id)
        if order != canonical_order:
            raise ValueError("order must match the numeric component of gate_id")

        object.__setattr__(self, "gate_id", gate_id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(
            self,
            "applicability",
            applicability,
        )


@dataclass(frozen=True, slots=True)
class ReleaseGateResult:
    gate_id: str
    name: str
    applicability: ReleaseGateApplicability
    status: ValidationStatus
    summary: str
    criteria_total: int
    criteria_passed: int
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_paths: tuple[Path, ...]
    blocked_by: tuple[str, ...] = ()
    duration_ms: int = 0

    def __post_init__(self) -> None:
        gate_id = validate_release_gate_id(self.gate_id)
        name = _normalize_text(
            self.name,
            field="name",
            maximum=_MAX_TEXT_LENGTH,
        )
        applicability = _require_enum(
            self.applicability,
            ReleaseGateApplicability,
            field="applicability",
        )
        status = _require_enum(
            self.status,
            ValidationStatus,
            field="status",
        )
        summary = _normalize_text(
            self.summary,
            field="summary",
            maximum=_MAX_SUMMARY_LENGTH,
        )
        criteria_total = _require_plain_int(
            self.criteria_total,
            field="criteria_total",
            minimum=0,
        )
        criteria_passed = _require_plain_int(
            self.criteria_passed,
            field="criteria_passed",
            minimum=0,
        )
        if criteria_passed > criteria_total:
            raise ValueError("criteria_passed must not exceed criteria_total")

        blockers = _normalize_unique_texts(
            self.blockers,
            field="blockers",
        )
        warnings = _normalize_unique_texts(
            self.warnings,
            field="warnings",
        )
        evidence_paths = _normalize_unique_paths(
            self.evidence_paths,
            field="evidence_paths",
        )
        blocked_by = _normalize_gate_ids(
            self.blocked_by,
            field="blocked_by",
        )
        duration_ms = _require_plain_int(
            self.duration_ms,
            field="duration_ms",
            minimum=0,
        )

        if gate_id in blocked_by:
            raise ValueError("a release gate cannot be blocked by itself")

        if applicability is ReleaseGateApplicability.NOT_APPLICABLE:
            if status is not ValidationStatus.SKIPPED:
                raise ValueError("a not_applicable gate must use SKIPPED status")

        if status is ValidationStatus.OK:
            if criteria_passed != criteria_total:
                raise ValueError("an OK gate must pass every criterion")
            if blockers:
                raise ValueError("an OK gate must not contain blockers")
            if blocked_by:
                raise ValueError("an OK gate must not be blocked")

        if status is ValidationStatus.FAIL:
            if not blockers:
                raise ValueError("a FAIL gate must identify at least one blocker")
            if criteria_total == 0:
                raise ValueError("a FAIL gate must evaluate at least one criterion")

        if status is ValidationStatus.ERROR and not blockers:
            raise ValueError("an ERROR gate must identify at least one blocker")

        if status is ValidationStatus.SKIPPED:
            if criteria_passed != 0:
                raise ValueError("a SKIPPED gate must not report passed criteria")
        elif blocked_by:
            raise ValueError("blocked_by is valid only for a SKIPPED gate")

        object.__setattr__(self, "gate_id", gate_id)
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "applicability",
            applicability,
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(
            self,
            "criteria_total",
            criteria_total,
        )
        object.__setattr__(
            self,
            "criteria_passed",
            criteria_passed,
        )
        object.__setattr__(self, "blockers", blockers)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(
            self,
            "evidence_paths",
            evidence_paths,
        )
        object.__setattr__(self, "blocked_by", blocked_by)
        object.__setattr__(
            self,
            "duration_ms",
            duration_ms,
        )

    @property
    def order(self) -> int:
        return _gate_order(self.gate_id)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def is_required(self) -> bool:
        return self.applicability is ReleaseGateApplicability.REQUIRED

    @property
    def is_not_applicable(self) -> bool:
        return self.applicability is ReleaseGateApplicability.NOT_APPLICABLE


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    decision: ReleaseDecisionValue
    gate_policy_version: str
    project_id: ProjectId
    run_id: RunId
    gf_wordbench_version: str
    gf_version: str
    rgl_identity: str
    gate_results: tuple[ReleaseGateResult, ...]
    required_gate_count: int
    passed_gate_count: int
    failed_gate_ids: tuple[str, ...]
    error_gate_ids: tuple[str, ...]
    skipped_required_gate_ids: tuple[str, ...]
    warning_count: int
    release_artifact_paths: tuple[Path, ...]
    decided_at: datetime

    def __post_init__(self) -> None:
        decision = _require_enum(
            self.decision,
            ReleaseDecisionValue,
            field="decision",
        )
        gate_policy_version = _normalize_version(
            self.gate_policy_version,
            field="gate_policy_version",
        )
        project_id = validate_project_id(
            self.project_id,
            field="project_id",
        )
        run_id = validate_run_id(
            self.run_id,
            field="run_id",
        )
        gf_wordbench_version = _normalize_version(
            self.gf_wordbench_version,
            field="gf_wordbench_version",
        )
        gf_version = _normalize_text(
            self.gf_version,
            field="gf_version",
            maximum=_MAX_TEXT_LENGTH,
        )
        rgl_identity = _normalize_text(
            self.rgl_identity,
            field="rgl_identity",
            maximum=_MAX_TEXT_LENGTH,
        )
        gate_results = _normalize_gate_results(
            self.gate_results,
        )
        required_gate_count = _require_plain_int(
            self.required_gate_count,
            field="required_gate_count",
            minimum=0,
        )
        passed_gate_count = _require_plain_int(
            self.passed_gate_count,
            field="passed_gate_count",
            minimum=0,
        )
        failed_gate_ids = _normalize_gate_ids(
            self.failed_gate_ids,
            field="failed_gate_ids",
        )
        error_gate_ids = _normalize_gate_ids(
            self.error_gate_ids,
            field="error_gate_ids",
        )
        skipped_required_gate_ids = _normalize_gate_ids(
            self.skipped_required_gate_ids,
            field="skipped_required_gate_ids",
        )
        warning_count = _require_plain_int(
            self.warning_count,
            field="warning_count",
            minimum=0,
        )
        release_artifact_paths = _normalize_unique_paths(
            self.release_artifact_paths,
            field="release_artifact_paths",
        )
        decided_at = _normalize_utc_datetime(
            self.decided_at,
            field="decided_at",
        )

        if required_gate_count > len(gate_results):
            raise ValueError("required_gate_count must not exceed gate result count")
        if passed_gate_count > required_gate_count:
            raise ValueError("passed_gate_count must not exceed required_gate_count")

        blocking_count = len(failed_gate_ids) + len(error_gate_ids) + len(skipped_required_gate_ids)
        if passed_gate_count + blocking_count != required_gate_count:
            raise ValueError(
                "required gate counts must equal passed, failed, "
                "error, and skipped-required gate counts"
            )

        gate_index = {result.gate_id: result for result in gate_results}
        _require_gate_statuses(
            failed_gate_ids,
            gate_index,
            expected=ValidationStatus.FAIL,
            field="failed_gate_ids",
        )
        _require_gate_statuses(
            error_gate_ids,
            gate_index,
            expected=ValidationStatus.ERROR,
            field="error_gate_ids",
        )
        _require_gate_statuses(
            skipped_required_gate_ids,
            gate_index,
            expected=ValidationStatus.SKIPPED,
            field="skipped_required_gate_ids",
        )

        listed_blockers = (
            set(failed_gate_ids) | set(error_gate_ids) | set(skipped_required_gate_ids)
        )
        if len(listed_blockers) != blocking_count:
            raise ValueError("failed, error, and skipped-required gate IDs must be disjoint")

        calculated_warning_count = sum(result.warning_count for result in gate_results)
        if warning_count != calculated_warning_count:
            raise ValueError("warning_count must equal the total gate warning count")

        expected_decision = _expected_decision(
            failed_gate_ids=failed_gate_ids,
            error_gate_ids=error_gate_ids,
            skipped_required_gate_ids=skipped_required_gate_ids,
        )
        if decision is not expected_decision:
            raise ValueError("decision does not match canonical release precedence")

        if decision is ReleaseDecisionValue.READY:
            for result in gate_results:
                if (
                    result.applicability is ReleaseGateApplicability.REQUIRED
                    and result.status is not ValidationStatus.OK
                ):
                    raise ValueError("READY requires every required gate to be OK")

        object.__setattr__(self, "decision", decision)
        object.__setattr__(
            self,
            "gate_policy_version",
            gate_policy_version,
        )
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(
            self,
            "gf_wordbench_version",
            gf_wordbench_version,
        )
        object.__setattr__(self, "gf_version", gf_version)
        object.__setattr__(
            self,
            "rgl_identity",
            rgl_identity,
        )
        object.__setattr__(
            self,
            "gate_results",
            gate_results,
        )
        object.__setattr__(
            self,
            "required_gate_count",
            required_gate_count,
        )
        object.__setattr__(
            self,
            "passed_gate_count",
            passed_gate_count,
        )
        object.__setattr__(
            self,
            "failed_gate_ids",
            failed_gate_ids,
        )
        object.__setattr__(
            self,
            "error_gate_ids",
            error_gate_ids,
        )
        object.__setattr__(
            self,
            "skipped_required_gate_ids",
            skipped_required_gate_ids,
        )
        object.__setattr__(
            self,
            "warning_count",
            warning_count,
        )
        object.__setattr__(
            self,
            "release_artifact_paths",
            release_artifact_paths,
        )
        object.__setattr__(self, "decided_at", decided_at)

    @property
    def is_ready(self) -> bool:
        return self.decision is ReleaseDecisionValue.READY

    @property
    def statement(self) -> str:
        if self.decision is ReleaseDecisionValue.READY:
            return "GF Wordbench release gates passed."
        if self.decision is ReleaseDecisionValue.NOT_READY:
            return "GF Wordbench release gates did not pass."
        return "GF Wordbench could not complete the release decision reliably."


def validate_release_gate_id(
    value: object,
    *,
    field: str = "gate_id",
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if _GATE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must match RG-NN, got {value!r}")
    return value


def _normalize_gate_results(
    values: tuple[ReleaseGateResult, ...],
) -> tuple[ReleaseGateResult, ...]:
    if not isinstance(values, tuple):
        raise TypeError("gate_results must be a tuple")
    if not values:
        raise ValueError("gate_results must not be empty")
    if len(values) > _MAX_GATE_RESULTS:
        raise ValueError("gate_results exceeds the bounded result limit")

    seen: set[str] = set()
    previous_order = -1
    normalized: list[ReleaseGateResult] = []

    for index, result in enumerate(values):
        if not isinstance(result, ReleaseGateResult):
            raise TypeError(f"gate_results[{index}] must be a ReleaseGateResult")
        if result.gate_id in seen:
            raise ValueError("gate_results must not contain duplicate gate IDs")
        if result.order <= previous_order:
            raise ValueError("gate_results must use strictly increasing canonical gate order")

        seen.add(result.gate_id)
        previous_order = result.order
        normalized.append(result)

    return tuple(normalized)


def _normalize_gate_ids(
    values: tuple[str, ...],
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > _MAX_GATE_RESULTS:
        raise ValueError(f"{field} exceeds the bounded gate limit")

    seen: set[str] = set()
    normalized: list[str] = []
    previous_order = -1

    for index, value in enumerate(values):
        gate_id = validate_release_gate_id(
            value,
            field=f"{field}[{index}]",
        )
        order = _gate_order(gate_id)
        if gate_id in seen:
            raise ValueError(f"{field} must not contain duplicate gate IDs")
        if order <= previous_order:
            raise ValueError(f"{field} must use canonical gate order")
        seen.add(gate_id)
        previous_order = order
        normalized.append(gate_id)

    return tuple(normalized)


def _require_gate_statuses(
    gate_ids: tuple[str, ...],
    gate_index: dict[str, ReleaseGateResult],
    *,
    expected: ValidationStatus,
    field: str,
) -> None:
    for gate_id in gate_ids:
        result = gate_index.get(gate_id)
        if result is None:
            raise ValueError(f"{field} references unknown gate {gate_id!r}")
        if result.status is not expected:
            raise ValueError(
                f"{field} contains {gate_id!r}, but its status "
                f"is {result.status.value}, not {expected.value}"
            )


def _expected_decision(
    *,
    failed_gate_ids: tuple[str, ...],
    error_gate_ids: tuple[str, ...],
    skipped_required_gate_ids: tuple[str, ...],
) -> ReleaseDecisionValue:
    if error_gate_ids or skipped_required_gate_ids:
        return ReleaseDecisionValue.ERROR
    if failed_gate_ids:
        return ReleaseDecisionValue.NOT_READY
    return ReleaseDecisionValue.READY


def _normalize_unique_texts(
    values: tuple[str, ...],
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > _MAX_TEXT_ITEMS:
        raise ValueError(f"{field} exceeds the bounded item limit")

    seen: set[str] = set()
    normalized: list[str] = []

    for index, value in enumerate(values):
        text = _normalize_text(
            value,
            field=f"{field}[{index}]",
            maximum=_MAX_TEXT_LENGTH,
        )
        if text in seen:
            raise ValueError(f"{field} must not contain duplicate values")
        seen.add(text)
        normalized.append(text)

    return tuple(normalized)


def _normalize_unique_paths(
    values: tuple[Path, ...],
    *,
    field: str,
) -> tuple[Path, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > _MAX_PATHS:
        raise ValueError(f"{field} exceeds the bounded path limit")

    seen: set[str] = set()
    normalized: list[Path] = []

    for index, value in enumerate(values):
        path = _normalize_run_relative_path(
            value,
            field=f"{field}[{index}]",
        )
        key = path.as_posix()
        if key in seen:
            raise ValueError(f"{field} must not contain duplicate paths")
        seen.add(key)
        normalized.append(path)

    return tuple(normalized)


def _normalize_run_relative_path(
    value: Path,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")

    rendered = value.as_posix()
    if not rendered:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in rendered:
        raise ValueError(f"{field} must not contain NUL")
    if value.is_absolute():
        raise ValueError(f"{field} must be run-relative")

    if PureWindowsPath(rendered).is_absolute():
        raise ValueError(f"{field} must not use an absolute Windows path")

    portable = PurePosixPath(rendered)
    if portable == PurePosixPath("."):
        raise ValueError(f"{field} must identify an artifact")
    if any(part in {"", ".", ".."} for part in portable.parts):
        raise ValueError(f"{field} must be normalized and must not traverse")

    normalized = Path(*portable.parts)
    if normalized.as_posix() != rendered:
        raise ValueError(f"{field} must use canonical forward-slash form")

    return normalized


def _normalize_text(
    value: object,
    *,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return normalized


def _normalize_version(
    value: object,
    *,
    field: str,
) -> str:
    normalized = _normalize_text(
        value,
        field=field,
        maximum=256,
    )
    if any(character.isspace() for character in normalized):
        raise ValueError(f"{field} must not contain whitespace")
    return normalized


def _normalize_utc_datetime(
    value: datetime,
    *,
    field: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _require_enum(
    value: object,
    enum_type: type[_EnumT],
    *,
    field: str,
) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    allowed = ", ".join(member.value for member in enum_type)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be one of: {allowed}")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be one of: {allowed}") from exc


def _require_plain_int(
    value: object,
    *,
    field: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return value


def _gate_order(gate_id: str) -> int:
    match = _GATE_ID_RE.fullmatch(gate_id)
    if match is None:
        raise ValueError(f"invalid release gate ID: {gate_id!r}")
    return int(match.group("order"))
