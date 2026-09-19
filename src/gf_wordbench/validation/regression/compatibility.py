"""Pure compatibility rules for previous-run regression baselines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import re
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import ValidationMode, ValidationStatus

RUN_SUMMARY_SCHEMA_ID: Final[str] = "gf-wordbench.run-summary"
SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR: Final[int] = 1
SUBJECT_IDENTITY_V1: Final[str] = "subject-kind-id-v1"
LEGACY_FILE_IDENTITY_V0: Final[str] = "legacy-file-path-v0"

_MODE_ALIASES: Final[Mapping[str, ValidationMode]] = MappingProxyType(
    {
        "file": ValidationMode.QUICK,
        "all": ValidationMode.DIAGNOSTIC,
    }
)
_CANONICAL_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    status.value for status in ValidationStatus
)
_SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)$"
)
_DRIVE_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


class CompatibilitySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class CompatibilityCode(str, Enum):
    LEGACY_MODE_ALIAS = "legacy_mode_alias"
    LEGACY_SCHEMA = "legacy_schema"
    LEGACY_SUBJECT_IDENTITY = "legacy_subject_identity"
    INFERRED_PROJECT_IDENTITY = "inferred_project_identity"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    PROJECT_MISMATCH = "project_mismatch"
    MODE_MISMATCH = "mode_mismatch"
    QUICK_TARGET_MISSING = "quick_target_missing"
    QUICK_TARGET_MISMATCH = "quick_target_mismatch"
    CHECKPOINT_SCOPE_MISSING = "checkpoint_scope_missing"
    CHECKPOINT_SCOPE_MISMATCH = "checkpoint_scope_mismatch"
    STATUS_VOCABULARY_MISMATCH = "status_vocabulary_mismatch"
    SUBJECT_IDENTITY_MISMATCH = "subject_identity_mismatch"
    RELEASE_CONTRACT_CHANGED = "release_contract_changed"
    GF_VERSION_CHANGED = "gf_version_changed"
    NORMALIZATION_VERSION_CHANGED = "normalization_version_changed"


class IncompatibleBaselineError(ContractViolationError):
    """Raised when an explicit baseline cannot be compared authoritatively."""


@dataclass(frozen=True, slots=True)
class RunCompatibilityDescriptor:
    """Comparison-relevant identity and execution scope for one run summary."""

    project_id: str
    mode: ValidationMode | str
    schema_id: str = RUN_SUMMARY_SCHEMA_ID
    schema_version: str | None = "1.0"
    target_id: str | None = None
    selected_subject_ids: tuple[str, ...] = ()
    subject_identity: str = SUBJECT_IDENTITY_V1
    status_values: frozenset[str] = _CANONICAL_STATUS_VALUES
    gf_version: str = ""
    normalization_versions: tuple[tuple[str, str], ...] = ()
    release_contract_id: str | None = None
    project_identity_inferred: bool = False
    legacy_schema: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "project_id",
            _require_text(self.project_id, field_name="project_id"),
        )
        object.__setattr__(
            self,
            "schema_id",
            _require_text(self.schema_id, field_name="schema_id"),
        )
        if self.schema_version is not None:
            object.__setattr__(
                self,
                "schema_version",
                _require_text(
                    self.schema_version,
                    field_name="schema_version",
                ),
            )
        object.__setattr__(
            self,
            "target_id",
            _optional_identity(self.target_id, field_name="target_id"),
        )
        object.__setattr__(
            self,
            "selected_subject_ids",
            _canonical_subject_set(self.selected_subject_ids),
        )
        object.__setattr__(
            self,
            "subject_identity",
            _require_text(
                self.subject_identity,
                field_name="subject_identity",
            ),
        )
        object.__setattr__(
            self,
            "status_values",
            _normalize_status_values(self.status_values),
        )
        object.__setattr__(
            self,
            "gf_version",
            _optional_text(self.gf_version, field_name="gf_version") or "",
        )
        object.__setattr__(
            self,
            "normalization_versions",
            _normalize_version_map(self.normalization_versions),
        )
        object.__setattr__(
            self,
            "release_contract_id",
            _optional_text(
                self.release_contract_id,
                field_name="release_contract_id",
            ),
        )
        if not isinstance(self.project_identity_inferred, bool):
            raise TypeError("project_identity_inferred must be a bool")
        if not isinstance(self.legacy_schema, bool):
            raise TypeError("legacy_schema must be a bool")

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> RunCompatibilityDescriptor:
        """Build a descriptor from canonical or migrated summary metadata."""

        if not isinstance(value, Mapping):
            raise TypeError("value must be a mapping")

        normalization_value = value.get("normalization_versions", ())
        if isinstance(normalization_value, Mapping):
            normalization_versions = tuple(
                (str(key), str(item)) for key, item in normalization_value.items()
            )
        else:
            normalization_versions = tuple(normalization_value)  # type: ignore[arg-type]

        status_value = value.get(
            "status_values",
            _CANONICAL_STATUS_VALUES,
        )
        if isinstance(status_value, str):
            status_values: Iterable[object] = (status_value,)
        else:
            status_values = status_value  # type: ignore[assignment]

        selected_value = value.get("selected_subject_ids", ())
        if isinstance(selected_value, str):
            selected_subject_ids: Iterable[object] = (selected_value,)
        else:
            selected_subject_ids = selected_value  # type: ignore[assignment]

        return cls(
            project_id=_mapping_text(value, "project_id"),
            mode=_mapping_text(value, "mode"),
            schema_id=str(value.get("schema_id", RUN_SUMMARY_SCHEMA_ID)),
            schema_version=_mapping_optional_text(value, "schema_version"),
            target_id=_mapping_optional_text(value, "target_id"),
            selected_subject_ids=tuple(str(item) for item in selected_subject_ids),
            subject_identity=str(value.get("subject_identity", SUBJECT_IDENTITY_V1)),
            status_values=frozenset(str(item) for item in status_values),
            gf_version=str(value.get("gf_version", "")),
            normalization_versions=normalization_versions,
            release_contract_id=_mapping_optional_text(
                value,
                "release_contract_id",
            ),
            project_identity_inferred=bool(value.get("project_identity_inferred", False)),
            legacy_schema=bool(value.get("legacy_schema", False)),
        )

    @property
    def normalization_version_map(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self.normalization_versions))


@dataclass(frozen=True, slots=True)
class CompatibilityIssue:
    """One deterministic warning or incompatibility reason."""

    code: CompatibilityCode
    severity: CompatibilitySeverity
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, CompatibilityCode):
            raise TypeError("code must be a CompatibilityCode")
        if not isinstance(self.severity, CompatibilitySeverity):
            raise TypeError("severity must be a CompatibilitySeverity")
        object.__setattr__(
            self,
            "message",
            _require_text(self.message, field_name="message"),
        )


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    """Complete compatibility decision for one baseline and current run."""

    previous_mode: ValidationMode
    current_mode: ValidationMode
    issues: tuple[CompatibilityIssue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.previous_mode, ValidationMode):
            raise TypeError("previous_mode must be a ValidationMode")
        if not isinstance(self.current_mode, ValidationMode):
            raise TypeError("current_mode must be a ValidationMode")
        issues = tuple(self.issues)
        if not all(isinstance(issue, CompatibilityIssue) for issue in issues):
            raise TypeError("issues must contain CompatibilityIssue values")
        object.__setattr__(self, "issues", _sort_issues(issues))

    @property
    def compatible(self) -> bool:
        return not any(issue.severity is CompatibilitySeverity.ERROR for issue in self.issues)

    @property
    def warnings(self) -> tuple[CompatibilityIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity is CompatibilitySeverity.WARNING
        )

    @property
    def errors(self) -> tuple[CompatibilityIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity is CompatibilitySeverity.ERROR
        )

    def require(self) -> CompatibilityResult:
        if self.compatible:
            return self
        detail = "; ".join(issue.message for issue in self.errors)
        raise IncompatibleBaselineError(f"Regression baseline is incompatible: {detail}")


def normalize_validation_mode(
    value: ValidationMode | str,
) -> tuple[ValidationMode, bool]:
    """Return the canonical mode and whether a legacy alias was consumed."""

    if isinstance(value, ValidationMode):
        return value, False
    text = _require_text(value, field_name="mode").strip().lower()
    alias = _MODE_ALIASES.get(text)
    if alias is not None:
        return alias, True
    try:
        return ValidationMode(text), False
    except ValueError as exc:
        raise ValueError(f"unsupported validation mode {value!r}") from exc


def check_run_compatibility(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
    *,
    explicit_baseline: bool = False,
) -> CompatibilityResult:
    """Evaluate whether two runs may produce authoritative regression diffs."""

    if not isinstance(previous, RunCompatibilityDescriptor):
        raise TypeError("previous must be a RunCompatibilityDescriptor")
    if not isinstance(current, RunCompatibilityDescriptor):
        raise TypeError("current must be a RunCompatibilityDescriptor")
    if not isinstance(explicit_baseline, bool):
        raise TypeError("explicit_baseline must be a bool")

    previous_mode, previous_alias = normalize_validation_mode(previous.mode)
    current_mode, current_alias = normalize_validation_mode(current.mode)
    issues: list[CompatibilityIssue] = []

    _check_schema(previous, label="baseline", issues=issues)
    _check_schema(current, label="current run", issues=issues)

    if previous_alias:
        issues.append(
            _warning(
                CompatibilityCode.LEGACY_MODE_ALIAS,
                f"Baseline mode {previous.mode!r} was normalized to {previous_mode.value!r}",
            )
        )
    if current_alias:
        issues.append(
            _warning(
                CompatibilityCode.LEGACY_MODE_ALIAS,
                f"Current mode {current.mode!r} was normalized to {current_mode.value!r}",
            )
        )

    if previous.project_identity_inferred:
        issues.append(
            _warning(
                CompatibilityCode.INFERRED_PROJECT_IDENTITY,
                "Baseline project identity was inferred by a documented migration rule",
            )
        )
    if current.project_identity_inferred:
        issues.append(
            _warning(
                CompatibilityCode.INFERRED_PROJECT_IDENTITY,
                "Current project identity was inferred by a documented migration rule",
            )
        )

    if previous.project_id != current.project_id:
        issues.append(
            _error(
                CompatibilityCode.PROJECT_MISMATCH,
                "Baseline and current run have different project identities",
            )
        )

    if previous_mode is not current_mode:
        issues.append(
            _error(
                CompatibilityCode.MODE_MISMATCH,
                "Baseline and current run have different canonical "
                f"validation modes: {previous_mode.value!r} and "
                f"{current_mode.value!r}",
            )
        )
    else:
        _check_mode_scope(
            previous,
            current,
            mode=current_mode,
            explicit_baseline=explicit_baseline,
            issues=issues,
        )

    _check_status_vocabulary(previous, current, issues=issues)
    _check_subject_identity(previous, current, issues=issues)
    _check_context_changes(previous, current, issues=issues)

    return CompatibilityResult(
        previous_mode=previous_mode,
        current_mode=current_mode,
        issues=tuple(issues),
    )


def runs_are_comparable(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
) -> bool:
    """Return whether an automatically discovered baseline is compatible."""

    return check_run_compatibility(previous, current).compatible


def require_explicit_baseline_compatibility(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
) -> CompatibilityResult:
    """Validate an explicit baseline and raise when comparison is unsafe."""

    return check_run_compatibility(
        previous,
        current,
        explicit_baseline=True,
    ).require()


def _check_schema(
    descriptor: RunCompatibilityDescriptor,
    *,
    label: str,
    issues: list[CompatibilityIssue],
) -> None:
    if descriptor.legacy_schema:
        issues.append(
            _warning(
                CompatibilityCode.LEGACY_SCHEMA,
                f"{label.capitalize()} uses a supported legacy summary migrated in memory",
            )
        )
        return

    if descriptor.schema_id != RUN_SUMMARY_SCHEMA_ID:
        issues.append(
            _error(
                CompatibilityCode.UNSUPPORTED_SCHEMA,
                f"{label.capitalize()} schema ID {descriptor.schema_id!r} is unsupported",
            )
        )
        return

    version = descriptor.schema_version
    if version is None:
        issues.append(
            _error(
                CompatibilityCode.UNSUPPORTED_SCHEMA,
                f"{label.capitalize()} summary has no schema version",
            )
        )
        return

    match = _SCHEMA_VERSION_RE.fullmatch(version)
    if match is None:
        issues.append(
            _error(
                CompatibilityCode.UNSUPPORTED_SCHEMA,
                f"{label.capitalize()} schema version {version!r} is invalid",
            )
        )
        return

    major = int(match.group("major"))
    if major != SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR:
        issues.append(
            _error(
                CompatibilityCode.UNSUPPORTED_SCHEMA,
                f"{label.capitalize()} summary schema major {major} is "
                f"unsupported; expected "
                f"{SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR}",
            )
        )


def _check_mode_scope(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
    *,
    mode: ValidationMode,
    explicit_baseline: bool,
    issues: list[CompatibilityIssue],
) -> None:
    if mode is ValidationMode.QUICK:
        if previous.target_id is None or current.target_id is None:
            issues.append(
                _error(
                    CompatibilityCode.QUICK_TARGET_MISSING,
                    "Comparable quick runs require explicit stable target identities",
                )
            )
        elif previous.target_id != current.target_id:
            issues.append(
                _error(
                    CompatibilityCode.QUICK_TARGET_MISMATCH,
                    "Quick-run target identities differ",
                )
            )
        return

    if mode is ValidationMode.CHECKPOINT:
        previous_scope = previous.selected_subject_ids
        current_scope = current.selected_subject_ids
        if not previous_scope or not current_scope:
            severity = (
                CompatibilitySeverity.WARNING if explicit_baseline else CompatibilitySeverity.ERROR
            )
            issues.append(
                CompatibilityIssue(
                    code=CompatibilityCode.CHECKPOINT_SCOPE_MISSING,
                    severity=severity,
                    message=(
                        "Checkpoint comparison scope is not fully persisted; "
                        "automatic comparison is unsafe"
                        if not explicit_baseline
                        else "Checkpoint comparison scope is not fully "
                        "persisted for the explicit baseline"
                    ),
                )
            )
        elif previous_scope != current_scope:
            issues.append(
                _error(
                    CompatibilityCode.CHECKPOINT_SCOPE_MISMATCH,
                    "Checkpoint runs contain different selected subject sets",
                )
            )
        return

    if mode is ValidationMode.RELEASE:
        previous_contract = previous.release_contract_id
        current_contract = current.release_contract_id
        if (
            previous_contract is not None
            and current_contract is not None
            and previous_contract != current_contract
        ):
            issues.append(
                _warning(
                    CompatibilityCode.RELEASE_CONTRACT_CHANGED,
                    "Project release requirements changed between baseline and current run",
                )
            )


def _check_status_vocabulary(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
    *,
    issues: list[CompatibilityIssue],
) -> None:
    if previous.status_values != _CANONICAL_STATUS_VALUES:
        issues.append(
            _error(
                CompatibilityCode.STATUS_VOCABULARY_MISMATCH,
                "Baseline status vocabulary is not the canonical validation status set",
            )
        )
    if current.status_values != _CANONICAL_STATUS_VALUES:
        issues.append(
            _error(
                CompatibilityCode.STATUS_VOCABULARY_MISMATCH,
                "Current status vocabulary is not the canonical validation status set",
            )
        )


def _check_subject_identity(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
    *,
    issues: list[CompatibilityIssue],
) -> None:
    previous_identity = previous.subject_identity
    current_identity = current.subject_identity

    if previous_identity == LEGACY_FILE_IDENTITY_V0:
        issues.append(
            _warning(
                CompatibilityCode.LEGACY_SUBJECT_IDENTITY,
                "Baseline file_path identities require documented in-memory "
                "migration to subject_kind and subject_id",
            )
        )
        previous_identity = SUBJECT_IDENTITY_V1

    if current_identity == LEGACY_FILE_IDENTITY_V0:
        issues.append(
            _warning(
                CompatibilityCode.LEGACY_SUBJECT_IDENTITY,
                "Current file_path identities require documented in-memory "
                "migration to subject_kind and subject_id",
            )
        )
        current_identity = SUBJECT_IDENTITY_V1

    if (
        previous_identity != SUBJECT_IDENTITY_V1
        or current_identity != SUBJECT_IDENTITY_V1
        or previous_identity != current_identity
    ):
        issues.append(
            _error(
                CompatibilityCode.SUBJECT_IDENTITY_MISMATCH,
                "Baseline and current run do not use compatible subject identity conventions",
            )
        )


def _check_context_changes(
    previous: RunCompatibilityDescriptor,
    current: RunCompatibilityDescriptor,
    *,
    issues: list[CompatibilityIssue],
) -> None:
    if previous.gf_version and current.gf_version and previous.gf_version != current.gf_version:
        issues.append(
            _warning(
                CompatibilityCode.GF_VERSION_CHANGED,
                "GF version changed between baseline and current run",
            )
        )

    previous_versions = previous.normalization_version_map
    current_versions = current.normalization_version_map
    changed = tuple(
        key
        for key in sorted(previous_versions.keys() | current_versions.keys())
        if previous_versions.get(key) != current_versions.get(key)
    )
    if changed:
        scope = ", ".join(changed)
        issues.append(
            _warning(
                CompatibilityCode.NORMALIZATION_VERSION_CHANGED,
                f"Normalization version changed for comparison scope: {scope}",
            )
        )


def _canonical_subject_set(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("selected_subject_ids must be an iterable of strings")
    normalized = tuple(
        _canonical_identity(value, field_name="selected_subject_ids") for value in values
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("selected_subject_ids must not contain duplicates")
    return tuple(sorted(normalized))


def _canonical_identity(value: object, *, field_name: str) -> str:
    text = _require_text(value, field_name=field_name).replace("\\", "/")
    if text.startswith("/") or _DRIVE_PREFIX_RE.match(text):
        raise ValueError(f"{field_name} must be project-relative")
    parts: list[str] = []
    for part in text.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError(f"{field_name} must not escape its project root")
        parts.append(part)
    if not parts:
        raise ValueError(f"{field_name} must not be empty")
    return "/".join(parts)


def _optional_identity(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _canonical_identity(value, field_name=field_name)


def _normalize_status_values(values: Iterable[object]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        values = (values,)
    normalized = frozenset(
        _require_text(value, field_name="status_values").upper() for value in values
    )
    if not normalized:
        raise ValueError("status_values must not be empty")
    return normalized


def _normalize_version_map(
    values: Mapping[str, str] | Iterable[tuple[object, object]],
) -> tuple[tuple[str, str], ...]:
    items = values.items() if isinstance(values, Mapping) else values
    normalized: dict[str, str] = {}
    for raw_key, raw_value in items:
        key = _canonical_identity(
            raw_key,
            field_name="normalization_versions key",
        )
        value = _require_text(
            raw_value,
            field_name=f"normalization_versions[{key!r}]",
        )
        if key in normalized:
            raise ValueError(f"duplicate normalization version scope {key!r}")
        normalized[key] = value
    return tuple(sorted(normalized.items()))


def _mapping_text(value: Mapping[str, object], key: str) -> str:
    if key not in value:
        raise ValueError(f"missing required compatibility field {key!r}")
    return _require_text(value[key], field_name=key)


def _mapping_optional_text(
    value: Mapping[str, object],
    key: str,
) -> str | None:
    item = value.get(key)
    return _optional_text(item, field_name=key)


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name=field_name)


def _warning(
    code: CompatibilityCode,
    message: str,
) -> CompatibilityIssue:
    return CompatibilityIssue(
        code=code,
        severity=CompatibilitySeverity.WARNING,
        message=message,
    )


def _error(
    code: CompatibilityCode,
    message: str,
) -> CompatibilityIssue:
    return CompatibilityIssue(
        code=code,
        severity=CompatibilitySeverity.ERROR,
        message=message,
    )


def _sort_issues(
    issues: tuple[CompatibilityIssue, ...],
) -> tuple[CompatibilityIssue, ...]:
    severity_order = {
        CompatibilitySeverity.ERROR: 0,
        CompatibilitySeverity.WARNING: 1,
    }
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                severity_order[issue.severity],
                issue.code.value,
                issue.message,
            ),
        )
    )


__all__ = (
    "LEGACY_FILE_IDENTITY_V0",
    "RUN_SUMMARY_SCHEMA_ID",
    "SUBJECT_IDENTITY_V1",
    "SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR",
    "CompatibilityCode",
    "CompatibilityIssue",
    "CompatibilityResult",
    "CompatibilitySeverity",
    "IncompatibleBaselineError",
    "RunCompatibilityDescriptor",
    "check_run_compatibility",
    "normalize_validation_mode",
    "require_explicit_baseline_compatibility",
    "runs_are_comparable",
)
