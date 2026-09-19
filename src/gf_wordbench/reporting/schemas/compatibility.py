"""Pure persisted-schema identity and compatibility evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from functools import total_ordering
import re
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)

__all__ = (
    "CompatibilityReason",
    "CompatibilityStatus",
    "SchemaCompatibilityPolicy",
    "SchemaCompatibilityResult",
    "SchemaIdentity",
    "SchemaVersion",
    "check_schema_compatibility",
    "extract_schema_identity",
    "is_schema_compatible",
    "parse_schema_version",
    "require_current_schema",
    "require_schema_compatibility",
)

SchemaDocument: TypeAlias = Mapping[str, object]

_SCHEMA_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*)+$"
)
_SCHEMA_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)"
    r"(?:\.(?P<patch>0|[1-9][0-9]*))?"
)
_EMPTY_METADATA: Final[Mapping[str, str]] = MappingProxyType({})


@unique
class CompatibilityStatus(StrEnum):
    EXACT = "exact"
    COMPATIBLE = "compatible"
    HISTORICAL_READ = "historical_read"
    MIGRATION_REQUIRED = "migration_required"
    INCOMPATIBLE = "incompatible"


@unique
class CompatibilityReason(StrEnum):
    EXACT_MATCH = "exact_match"
    EXPLICIT_READ_SUPPORT = "explicit_read_support"
    COMPATIBLE_NEWER_PATCH = "compatible_newer_patch"
    COMPATIBLE_NEWER_MINOR = "compatible_newer_minor"
    HISTORICAL_ADAPTER = "historical_adapter"
    EXPLICIT_MIGRATION = "explicit_migration"
    MISSING_SCHEMA_ID = "missing_schema_id"
    MISSING_SCHEMA_VERSION = "missing_schema_version"
    MALFORMED_SCHEMA_ID = "malformed_schema_id"
    MALFORMED_SCHEMA_VERSION = "malformed_schema_version"
    WRONG_SCHEMA_ID = "wrong_schema_id"
    UNSUPPORTED_MAJOR = "unsupported_major"
    UNSUPPORTED_OLDER_VERSION = "unsupported_older_version"
    UNSUPPORTED_NEWER_PATCH = "unsupported_newer_patch"
    UNSUPPORTED_NEWER_MINOR = "unsupported_newer_minor"


@total_ordering
@dataclass(frozen=True, slots=True)
class SchemaVersion:
    major: int
    minor: int
    patch: int = 0
    components: int = 2

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.components not in (2, 3):
            raise ValueError("components must be 2 or 3")
        if self.components == 2 and self.patch != 0:
            raise ValueError("a two-component version cannot have a patch value")

    @classmethod
    def parse(cls, value: str | SchemaVersion) -> SchemaVersion:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("schema version must be a string")
        if value != value.strip() or not value:
            raise ValueError("schema version must be non-empty without surrounding whitespace")
        if "\x00" in value:
            raise ValueError("schema version must not contain NUL characters")
        match = _SCHEMA_VERSION_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("schema version must use major.minor or major.minor.patch")
        patch_text = match.group("patch")
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=0 if patch_text is None else int(patch_text),
            components=2 if patch_text is None else 3,
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}"
        return base if self.components == 2 else f"{base}.{self.patch}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return self.sort_key < other.sort_key

    @property
    def sort_key(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def same_major(self, other: SchemaVersion) -> bool:
        return self.major == other.major

    def same_minor_line(self, other: SchemaVersion) -> bool:
        return self.major == other.major and self.minor == other.minor


@dataclass(frozen=True, slots=True)
class SchemaIdentity:
    schema_id: str
    schema_version: SchemaVersion

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_id",
            _validate_schema_id(self.schema_id),
        )
        object.__setattr__(
            self,
            "schema_version",
            SchemaVersion.parse(self.schema_version),
        )

    @classmethod
    def from_values(
        cls,
        schema_id: str,
        schema_version: str | SchemaVersion,
    ) -> SchemaIdentity:
        return cls(
            schema_id=schema_id,
            schema_version=SchemaVersion.parse(schema_version),
        )

    def as_mapping(self) -> Mapping[str, str]:
        return MappingProxyType(
            {
                "schema_id": self.schema_id,
                "schema_version": str(self.schema_version),
            }
        )


@dataclass(frozen=True, slots=True)
class SchemaCompatibilityPolicy:
    schema_id: str
    current_version: SchemaVersion
    readable_versions: frozenset[SchemaVersion] = frozenset()
    historical_versions: frozenset[SchemaVersion] = frozenset()
    migration_sources: frozenset[SchemaVersion] = frozenset()
    allow_newer_patch: bool = False
    allow_newer_minor: bool = False
    allow_unknown_optional_fields: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_id",
            _validate_schema_id(self.schema_id),
        )
        current = SchemaVersion.parse(self.current_version)
        object.__setattr__(self, "current_version", current)

        readable = _version_set(self.readable_versions, "readable_versions")
        historical = _version_set(
            self.historical_versions,
            "historical_versions",
        )
        migrations = _version_set(
            self.migration_sources,
            "migration_sources",
        )

        if current in historical or current in migrations:
            raise ValueError("current_version cannot be historical or require migration")
        if readable.intersection(historical):
            raise ValueError("readable_versions and historical_versions must not overlap")
        if readable.intersection(migrations):
            raise ValueError("readable_versions and migration_sources must not overlap")
        if historical.intersection(migrations):
            raise ValueError("historical_versions and migration_sources must not overlap")

        for name in (
            "allow_newer_patch",
            "allow_newer_minor",
            "allow_unknown_optional_fields",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")

        if self.allow_newer_minor and not self.allow_unknown_optional_fields:
            raise ValueError("allow_newer_minor requires allow_unknown_optional_fields")

        object.__setattr__(self, "readable_versions", readable)
        object.__setattr__(self, "historical_versions", historical)
        object.__setattr__(self, "migration_sources", migrations)

    @classmethod
    def exact(
        cls,
        schema_id: str,
        current_version: str | SchemaVersion,
    ) -> SchemaCompatibilityPolicy:
        return cls(
            schema_id=schema_id,
            current_version=SchemaVersion.parse(current_version),
        )

    @classmethod
    def additive_minor_reader(
        cls,
        schema_id: str,
        current_version: str | SchemaVersion,
        *,
        readable_versions: Iterable[str | SchemaVersion] = (),
        historical_versions: Iterable[str | SchemaVersion] = (),
        migration_sources: Iterable[str | SchemaVersion] = (),
        allow_newer_patch: bool = True,
    ) -> SchemaCompatibilityPolicy:
        return cls(
            schema_id=schema_id,
            current_version=SchemaVersion.parse(current_version),
            readable_versions=frozenset(SchemaVersion.parse(value) for value in readable_versions),
            historical_versions=frozenset(
                SchemaVersion.parse(value) for value in historical_versions
            ),
            migration_sources=frozenset(SchemaVersion.parse(value) for value in migration_sources),
            allow_newer_patch=allow_newer_patch,
            allow_newer_minor=True,
            allow_unknown_optional_fields=True,
        )

    @property
    def current_identity(self) -> SchemaIdentity:
        return SchemaIdentity(
            schema_id=self.schema_id,
            schema_version=self.current_version,
        )

    @property
    def all_explicit_versions(self) -> frozenset[SchemaVersion]:
        return frozenset(
            {
                self.current_version,
                *self.readable_versions,
                *self.historical_versions,
                *self.migration_sources,
            }
        )


@dataclass(frozen=True, slots=True)
class SchemaCompatibilityResult:
    status: CompatibilityStatus
    reason: CompatibilityReason
    expected: SchemaIdentity
    observed: SchemaIdentity | None
    message: str
    metadata: Mapping[str, str] = _EMPTY_METADATA

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _compatibility_status(self.status))
        object.__setattr__(self, "reason", _compatibility_reason(self.reason))
        if not isinstance(self.expected, SchemaIdentity):
            raise TypeError("expected must be a SchemaIdentity")
        if self.observed is not None and not isinstance(
            self.observed,
            SchemaIdentity,
        ):
            raise TypeError("observed must be a SchemaIdentity or None")
        object.__setattr__(
            self,
            "message",
            _required_text(self.message, "message"),
        )
        object.__setattr__(
            self,
            "metadata",
            _metadata(self.metadata),
        )

    @property
    def readable(self) -> bool:
        return self.status in {
            CompatibilityStatus.EXACT,
            CompatibilityStatus.COMPATIBLE,
            CompatibilityStatus.HISTORICAL_READ,
        }

    @property
    def exact(self) -> bool:
        return self.status is CompatibilityStatus.EXACT

    @property
    def historical(self) -> bool:
        return self.status is CompatibilityStatus.HISTORICAL_READ

    @property
    def requires_migration(self) -> bool:
        return self.status is CompatibilityStatus.MIGRATION_REQUIRED

    @property
    def canonical_write_allowed(self) -> bool:
        return self.status is CompatibilityStatus.EXACT


def parse_schema_version(value: str | SchemaVersion) -> SchemaVersion:
    return SchemaVersion.parse(value)


def extract_schema_identity(document: SchemaDocument) -> SchemaIdentity:
    if not isinstance(document, Mapping):
        raise SchemaValidationError(
            "Persisted schema document must be a mapping",
            code="GF-WB-SCHEMA-001",
            stage="reporting",
            operation="extract-schema-identity",
        )

    if "schema_id" not in document:
        raise SchemaValidationError(
            "Persisted schema document is missing schema_id",
            code="GF-WB-SCHEMA-002",
            stage="reporting",
            operation="extract-schema-identity",
        )
    if "schema_version" not in document:
        raise SchemaValidationError(
            "Persisted schema document is missing schema_version",
            code="GF-WB-SCHEMA-003",
            stage="reporting",
            operation="extract-schema-identity",
        )

    raw_schema_id = document["schema_id"]
    raw_schema_version = document["schema_version"]

    if not isinstance(raw_schema_id, str):
        raise SchemaValidationError(
            "schema_id must be a string",
            code="GF-WB-SCHEMA-004",
            stage="reporting",
            operation="extract-schema-identity",
        )
    if not isinstance(raw_schema_version, str):
        raise SchemaValidationError(
            "schema_version must be a string",
            code="GF-WB-SCHEMA-005",
            stage="reporting",
            operation="extract-schema-identity",
            subject=raw_schema_id or None,
        )

    try:
        return SchemaIdentity.from_values(
            raw_schema_id,
            raw_schema_version,
        )
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(
            "Persisted schema identity is malformed",
            code="GF-WB-SCHEMA-006",
            detail=str(exc),
            stage="reporting",
            operation="extract-schema-identity",
            subject=raw_schema_id or None,
        ) from exc


def _compatibility_status(value: object) -> CompatibilityStatus:
    if isinstance(value, CompatibilityStatus):
        return value
    if not isinstance(value, str):
        raise TypeError("status must be a CompatibilityStatus or string")
    try:
        return CompatibilityStatus(value)
    except ValueError as exc:
        raise ValueError("status must be a canonical CompatibilityStatus") from exc


def _compatibility_reason(value: object) -> CompatibilityReason:
    if isinstance(value, CompatibilityReason):
        return value
    if not isinstance(value, str):
        raise TypeError("reason must be a CompatibilityReason or string")
    try:
        return CompatibilityReason(value)
    except ValueError as exc:
        raise ValueError("reason must be a canonical CompatibilityReason") from exc


def check_schema_compatibility(
    document_or_identity: SchemaDocument | SchemaIdentity,
    policy: SchemaCompatibilityPolicy,
) -> SchemaCompatibilityResult:
    if not isinstance(policy, SchemaCompatibilityPolicy):
        raise TypeError("policy must be a SchemaCompatibilityPolicy")

    expected = policy.current_identity

    if isinstance(document_or_identity, SchemaIdentity):
        observed = document_or_identity
    elif isinstance(document_or_identity, Mapping):
        malformed = _identity_failure(document_or_identity, expected)
        if malformed is not None:
            return malformed
        observed = extract_schema_identity(document_or_identity)
    else:
        raise TypeError("document_or_identity must be a mapping or SchemaIdentity")

    if observed.schema_id != policy.schema_id:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.WRONG_SCHEMA_ID,
            expected=expected,
            observed=observed,
            message=(f"Expected schema {policy.schema_id!r}, observed {observed.schema_id!r}."),
        )

    version = observed.schema_version
    current = policy.current_version

    if version == current:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.EXACT,
            reason=CompatibilityReason.EXACT_MATCH,
            expected=expected,
            observed=observed,
            message=(
                f"Schema {observed.schema_id} {version} exactly matches "
                "the current reader contract."
            ),
        )

    if version in policy.readable_versions:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            reason=CompatibilityReason.EXPLICIT_READ_SUPPORT,
            expected=expected,
            observed=observed,
            message=(
                f"Schema {observed.schema_id} {version} is explicitly supported by this reader."
            ),
        )

    if version in policy.historical_versions:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.HISTORICAL_READ,
            reason=CompatibilityReason.HISTORICAL_ADAPTER,
            expected=expected,
            observed=observed,
            message=(
                f"Schema {observed.schema_id} {version} is accepted only "
                "through documented historical read support."
            ),
        )

    if version in policy.migration_sources:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.MIGRATION_REQUIRED,
            reason=CompatibilityReason.EXPLICIT_MIGRATION,
            expected=expected,
            observed=observed,
            message=(
                f"Schema {observed.schema_id} {version} requires migration "
                f"to {current} before canonical use."
            ),
        )

    if version.major != current.major:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.UNSUPPORTED_MAJOR,
            expected=expected,
            observed=observed,
            message=(
                f"Schema major version {version.major} is unsupported; "
                f"the current major version is {current.major}."
            ),
        )

    if version > current:
        if version.minor == current.minor:
            if policy.allow_newer_patch:
                return SchemaCompatibilityResult(
                    status=CompatibilityStatus.COMPATIBLE,
                    reason=CompatibilityReason.COMPATIBLE_NEWER_PATCH,
                    expected=expected,
                    observed=observed,
                    message=(
                        f"Schema patch version {version} is accepted by "
                        "the current patch-compatible reader."
                    ),
                )
            reason = CompatibilityReason.UNSUPPORTED_NEWER_PATCH
        elif policy.allow_newer_minor and policy.allow_unknown_optional_fields:
            return SchemaCompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                reason=CompatibilityReason.COMPATIBLE_NEWER_MINOR,
                expected=expected,
                observed=observed,
                message=(
                    f"Schema minor version {version} is accepted under the "
                    "documented optional-field compatibility policy."
                ),
            )
        else:
            reason = CompatibilityReason.UNSUPPORTED_NEWER_MINOR

        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=reason,
            expected=expected,
            observed=observed,
            message=(
                f"Schema version {version} is newer than the supported "
                f"version {current} and no compatible reader policy applies."
            ),
        )

    return SchemaCompatibilityResult(
        status=CompatibilityStatus.INCOMPATIBLE,
        reason=CompatibilityReason.UNSUPPORTED_OLDER_VERSION,
        expected=expected,
        observed=observed,
        message=(
            f"Schema version {version} is older than {current} and has no "
            "explicit read or migration contract."
        ),
    )


def is_schema_compatible(
    document_or_identity: SchemaDocument | SchemaIdentity,
    policy: SchemaCompatibilityPolicy,
) -> bool:
    return check_schema_compatibility(
        document_or_identity,
        policy,
    ).readable


def require_schema_compatibility(
    document_or_identity: SchemaDocument | SchemaIdentity,
    policy: SchemaCompatibilityPolicy,
    *,
    allow_historical: bool = True,
) -> SchemaCompatibilityResult:
    result = check_schema_compatibility(document_or_identity, policy)

    accepted = result.status in {
        CompatibilityStatus.EXACT,
        CompatibilityStatus.COMPATIBLE,
    }
    if allow_historical:
        accepted = accepted or (result.status is CompatibilityStatus.HISTORICAL_READ)

    if accepted:
        return result

    observed_version = str(result.observed.schema_version) if result.observed is not None else None
    subject = result.observed.schema_id if result.observed is not None else policy.schema_id

    if result.reason in {
        CompatibilityReason.MISSING_SCHEMA_ID,
        CompatibilityReason.MISSING_SCHEMA_VERSION,
        CompatibilityReason.MALFORMED_SCHEMA_ID,
        CompatibilityReason.MALFORMED_SCHEMA_VERSION,
        CompatibilityReason.WRONG_SCHEMA_ID,
    }:
        raise SchemaValidationError(
            result.message,
            code="GF-WB-SCHEMA-007",
            detail=f"reason={result.reason.value}",
            stage="reporting",
            operation="require-schema-compatibility",
            subject=subject,
        )

    raise UnsupportedVersionError(
        result.message,
        code="GF-WB-SCHEMA-008",
        detail=(
            f"reason={result.reason.value}; "
            f"observed_version={observed_version!r}; "
            f"current_version={policy.current_version}"
        ),
        stage="reporting",
        operation="require-schema-compatibility",
        subject=subject,
    )


def require_current_schema(
    document_or_identity: SchemaDocument | SchemaIdentity,
    policy: SchemaCompatibilityPolicy,
) -> SchemaCompatibilityResult:
    result = check_schema_compatibility(document_or_identity, policy)
    if result.status is CompatibilityStatus.EXACT:
        return result

    observed = result.observed.schema_id if result.observed is not None else policy.schema_id
    raise UnsupportedVersionError(
        (
            f"Canonical writing requires schema "
            f"{policy.schema_id} {policy.current_version}; "
            f"{result.message}"
        ),
        code="GF-WB-SCHEMA-009",
        detail=f"reason={result.reason.value}",
        stage="reporting",
        operation="require-current-schema",
        subject=observed,
    )


def _identity_failure(
    document: Mapping[str, object],
    expected: SchemaIdentity,
) -> SchemaCompatibilityResult | None:
    if "schema_id" not in document:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MISSING_SCHEMA_ID,
            expected=expected,
            observed=None,
            message="Persisted document is missing schema_id.",
        )
    if "schema_version" not in document:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MISSING_SCHEMA_VERSION,
            expected=expected,
            observed=None,
            message="Persisted document is missing schema_version.",
        )

    raw_id = document["schema_id"]
    raw_version = document["schema_version"]

    if not isinstance(raw_id, str):
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MALFORMED_SCHEMA_ID,
            expected=expected,
            observed=None,
            message="schema_id must be a string.",
        )
    try:
        _validate_schema_id(raw_id)
    except (TypeError, ValueError) as exc:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MALFORMED_SCHEMA_ID,
            expected=expected,
            observed=None,
            message=f"Malformed schema_id: {exc}",
        )

    if not isinstance(raw_version, str):
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MALFORMED_SCHEMA_VERSION,
            expected=expected,
            observed=None,
            message="schema_version must be a string.",
        )
    try:
        SchemaVersion.parse(raw_version)
    except (TypeError, ValueError) as exc:
        return SchemaCompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            reason=CompatibilityReason.MALFORMED_SCHEMA_VERSION,
            expected=expected,
            observed=None,
            message=f"Malformed schema_version: {exc}",
        )
    return None


def _validate_schema_id(value: str) -> str:
    value = _required_text(value, "schema_id")
    if value != value.strip():
        raise ValueError("schema_id must not contain surrounding whitespace")
    if not value.isascii():
        raise ValueError("schema_id must use ASCII characters")
    if _SCHEMA_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(
            "schema_id must be lowercase dotted identifiers using letters, digits, and hyphens"
        )
    return value


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _version_set(
    values: Iterable[str | SchemaVersion],
    field_name: str,
) -> frozenset[SchemaVersion]:
    if isinstance(values, (str, bytes, SchemaVersion)):
        raise TypeError(f"{field_name} must be an iterable of versions")
    try:
        return frozenset(SchemaVersion.parse(value) for value in values)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of versions") from exc


def _metadata(values: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")
    copied: dict[str, str] = {}
    for key, value in values.items():
        copied[_required_text(key, "metadata key")] = _required_text(value, f"metadata[{key!r}]")
    return _EMPTY_METADATA if not copied else MappingProxyType(copied)
