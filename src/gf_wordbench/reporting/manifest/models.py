"""Immutable artifact-manifest domain models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from typing import Final

from gf_wordbench.kernel.ids import RunId, validate_run_id
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationStatus

ARTIFACT_MANIFEST_SCHEMA_ID: Final = "gf-wordbench.artifact-manifest"
ARTIFACT_MANIFEST_SCHEMA_VERSION: Final = "1.0"
ARTIFACT_MANIFEST_FILENAME: Final = "manifest.json"
ARTIFACT_MANIFEST_HASH_ALGORITHM: Final = "sha256"

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/"
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*"
    r"(?:\s*;\s*[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*="
    r"(?:[A-Za-z0-9][A-Za-z0-9!#$&^_.+:-]*|\"[^\"\r\n]*\"))*$"
)
_ROLE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
)
_CREATOR_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$"
)
_SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
_RFC3339_UTC_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?P<fraction>\.[0-9]{1,6})?Z$"
)
_DRIVE_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


@unique
class ManifestVerificationMode(StrEnum):
    STANDARD = "standard"
    STRICT = "strict"
    RELEASE = "release"


@dataclass(frozen=True, slots=True)
class ManifestVerificationPolicy:
    """Immutable policy controlling artifact-manifest verification."""

    mode: ManifestVerificationMode | str = ManifestVerificationMode.STANDARD
    expected_run_id: RunId | str | None = None
    verify_summary: bool = False
    require_pgf: bool = False
    detect_unlisted_files: bool = False
    reject_unlisted_files: bool = False
    allow_symlinks: bool | None = None
    required_paths: tuple[str, ...] = ()
    owned_directories: tuple[str, ...] = ()
    allowed_roles: tuple[str, ...] = ()
    allowed_creators: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        mode = _coerce_manifest_verification_mode(self.mode)

        expected_run_id = self.expected_run_id
        if expected_run_id is not None:
            expected_run_id = _require_text(
                expected_run_id,
                field="expected_run_id",
            )

        verify_summary = _validate_bool(
            self.verify_summary,
            field="verify_summary",
        )
        require_pgf = _validate_bool(
            self.require_pgf,
            field="require_pgf",
        )
        detect_unlisted_files = _validate_bool(
            self.detect_unlisted_files,
            field="detect_unlisted_files",
        )
        reject_unlisted_files = _validate_bool(
            self.reject_unlisted_files,
            field="reject_unlisted_files",
        )

        allow_symlinks = self.allow_symlinks
        if allow_symlinks is None:
            allow_symlinks = mode is ManifestVerificationMode.STANDARD
        else:
            allow_symlinks = _validate_bool(
                allow_symlinks,
                field="allow_symlinks",
            )

        required_paths = _validate_policy_values(
            self.required_paths,
            field="required_paths",
            validator=validate_manifest_artifact_path,
        )
        owned_directories = _validate_policy_values(
            self.owned_directories,
            field="owned_directories",
            validator=_validate_owned_directory,
        )
        allowed_roles = _validate_policy_values(
            self.allowed_roles,
            field="allowed_roles",
            validator=_validate_role,
        )
        allowed_creators = _validate_policy_values(
            self.allowed_creators,
            field="allowed_creators",
            validator=_validate_creator,
        )

        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "expected_run_id", expected_run_id)
        object.__setattr__(self, "verify_summary", verify_summary)
        object.__setattr__(self, "require_pgf", require_pgf)
        object.__setattr__(
            self,
            "detect_unlisted_files",
            detect_unlisted_files or reject_unlisted_files,
        )
        object.__setattr__(
            self,
            "reject_unlisted_files",
            reject_unlisted_files,
        )
        object.__setattr__(self, "allow_symlinks", allow_symlinks)
        object.__setattr__(self, "required_paths", required_paths)
        object.__setattr__(self, "owned_directories", owned_directories)
        object.__setattr__(self, "allowed_roles", allowed_roles)
        object.__setattr__(self, "allowed_creators", allowed_creators)

    @property
    def strict(self) -> bool:
        return self.mode in {
            ManifestVerificationMode.STRICT,
            ManifestVerificationMode.RELEASE,
        }

    @property
    def release(self) -> bool:
        return self.mode is ManifestVerificationMode.RELEASE


@dataclass(frozen=True, slots=True)
class ArtifactManifestEntry:
    path: str
    role: str
    media_type: str
    required: bool
    size_bytes: int
    sha256: str
    created_by: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", validate_manifest_artifact_path(self.path))
        object.__setattr__(self, "role", _validate_role(self.role))
        object.__setattr__(
            self,
            "media_type",
            _validate_media_type(self.media_type),
        )
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if type(self.size_bytes) is not int:
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        object.__setattr__(self, "sha256", validate_sha256(self.sha256))
        object.__setattr__(
            self,
            "created_by",
            _validate_creator(self.created_by),
        )

    @property
    def posix_path(self) -> PurePosixPath:
        return PurePosixPath(self.path)


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    schema_id: str
    schema_version: str
    producer_name: str
    producer_version: str
    run_id: str
    generated_at: str
    hash_algorithm: str
    artifacts: tuple[ArtifactManifestEntry, ...]

    def __post_init__(self) -> None:
        schema_id = _require_text(self.schema_id, field="schema_id")
        if schema_id != ARTIFACT_MANIFEST_SCHEMA_ID:
            raise ValueError(
                "schema_id must be "
                f"{ARTIFACT_MANIFEST_SCHEMA_ID!r}"
            )
        schema_version = _validate_schema_version(self.schema_version)
        if schema_version != ARTIFACT_MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                "schema_version must be "
                f"{ARTIFACT_MANIFEST_SCHEMA_VERSION!r}"
            )
        producer = ProducerInfo(
            name=self.producer_name,
            version=self.producer_version,
        )
        run_id = validate_run_id(self.run_id)
        generated_at = validate_generated_at(self.generated_at)
        hash_algorithm = _require_text(
            self.hash_algorithm,
            field="hash_algorithm",
        ).lower()
        if hash_algorithm != ARTIFACT_MANIFEST_HASH_ALGORITHM:
            raise ValueError(
                "hash_algorithm must be "
                f"{ARTIFACT_MANIFEST_HASH_ALGORITHM!r}"
            )
        artifacts = _validate_artifacts(self.artifacts)

        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "producer_name", producer.name)
        object.__setattr__(self, "producer_version", producer.version)
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "hash_algorithm", hash_algorithm)
        object.__setattr__(self, "artifacts", artifacts)

    @property
    def producer(self) -> ProducerInfo:
        return ProducerInfo(
            name=self.producer_name,
            version=self.producer_version,
        )

    @property
    def required_artifacts(self) -> tuple[ArtifactManifestEntry, ...]:
        return tuple(entry for entry in self.artifacts if entry.required)

    @property
    def entry_count(self) -> int:
        return len(self.artifacts)

    @property
    def required_entry_count(self) -> int:
        return sum(entry.required for entry in self.artifacts)

    @property
    def total_size_bytes(self) -> int:
        return sum(entry.size_bytes for entry in self.artifacts)

    def get_entry(self, path: str) -> ArtifactManifestEntry | None:
        normalized = validate_manifest_artifact_path(path)
        for entry in self.artifacts:
            if entry.path == normalized:
                return entry
        return None


@dataclass(frozen=True, slots=True)
class ManifestWriteResult:
    status: ValidationStatus
    manifest_path: Path | None
    entry_count: int
    required_entry_count: int
    total_size_bytes: int
    warnings: tuple[str, ...]
    message: str

    def __post_init__(self) -> None:
        status = _coerce_validation_status(self.status)
        manifest_path = _validate_optional_path(
            self.manifest_path,
            field="manifest_path",
        )
        entry_count = _validate_non_negative_int(
            self.entry_count,
            field="entry_count",
        )
        required_entry_count = _validate_non_negative_int(
            self.required_entry_count,
            field="required_entry_count",
        )
        if required_entry_count > entry_count:
            raise ValueError(
                "required_entry_count must not exceed entry_count"
            )
        total_size_bytes = _validate_non_negative_int(
            self.total_size_bytes,
            field="total_size_bytes",
        )
        warnings = _validate_messages(self.warnings, field="warnings")
        message = _require_text(self.message, field="message")
        if status is ValidationStatus.OK and manifest_path is None:
            raise ValueError("an OK manifest write requires manifest_path")

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "manifest_path", manifest_path)
        object.__setattr__(self, "entry_count", entry_count)
        object.__setattr__(
            self,
            "required_entry_count",
            required_entry_count,
        )
        object.__setattr__(self, "total_size_bytes", total_size_bytes)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "message", message)

    @property
    def succeeded(self) -> bool:
        return self.status is ValidationStatus.OK


@dataclass(frozen=True, slots=True)
class ManifestVerificationResult:
    status: ValidationStatus
    manifest_path: Path
    schema_version: str | None
    artifacts_checked: int
    required_artifacts_checked: int
    missing_paths: tuple[str, ...]
    mismatched_paths: tuple[str, ...]
    unsafe_paths: tuple[str, ...]
    warnings: tuple[str, ...]
    message: str

    def __post_init__(self) -> None:
        status = _coerce_validation_status(self.status)
        manifest_path = _validate_path(
            self.manifest_path,
            field="manifest_path",
        )
        schema_version = self.schema_version
        if schema_version is not None:
            schema_version = _validate_schema_version(schema_version)
        artifacts_checked = _validate_non_negative_int(
            self.artifacts_checked,
            field="artifacts_checked",
        )
        required_artifacts_checked = _validate_non_negative_int(
            self.required_artifacts_checked,
            field="required_artifacts_checked",
        )
        if required_artifacts_checked > artifacts_checked:
            raise ValueError(
                "required_artifacts_checked must not exceed artifacts_checked"
            )
        missing_paths = _validate_path_messages(
            self.missing_paths,
            field="missing_paths",
            require_safe=True,
        )
        mismatched_paths = _validate_path_messages(
            self.mismatched_paths,
            field="mismatched_paths",
            require_safe=True,
        )
        unsafe_paths = _validate_path_messages(
            self.unsafe_paths,
            field="unsafe_paths",
            require_safe=False,
        )
        warnings = _validate_messages(self.warnings, field="warnings")
        message = _require_text(self.message, field="message")
        if status is ValidationStatus.OK and (
            missing_paths or mismatched_paths or unsafe_paths
        ):
            raise ValueError(
                "an OK verification result cannot contain integrity failures"
            )

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "manifest_path", manifest_path)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "artifacts_checked", artifacts_checked)
        object.__setattr__(
            self,
            "required_artifacts_checked",
            required_artifacts_checked,
        )
        object.__setattr__(self, "missing_paths", missing_paths)
        object.__setattr__(self, "mismatched_paths", mismatched_paths)
        object.__setattr__(self, "unsafe_paths", unsafe_paths)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "message", message)

    @property
    def verified(self) -> bool:
        return self.status is ValidationStatus.OK

    @property
    def failure_paths(self) -> tuple[str, ...]:
        return _stable_unique(
            (*self.missing_paths, *self.mismatched_paths, *self.unsafe_paths)
        )


def validate_manifest_artifact_path(value: object) -> str:
    path = _require_text(value, field="artifact path")
    if "\\" in path:
        raise ValueError("artifact path must use forward slashes")
    if path.startswith("/") or _DRIVE_PREFIX_RE.match(path):
        raise ValueError("artifact path must be run-relative")
    if path.endswith("/"):
        raise ValueError("artifact path must identify a file")

    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(
            "artifact path must be normalized and contain no traversal"
        )
    if any("\x00" in part for part in parts):
        raise ValueError("artifact path must not contain NUL characters")

    normalized = PurePosixPath(*parts).as_posix()
    if normalized != path:
        raise ValueError("artifact path is not in canonical form")
    if normalized == ARTIFACT_MANIFEST_FILENAME:
        raise ValueError("the artifact manifest cannot list itself")
    return normalized


def validate_sha256(value: object) -> str:
    digest = _require_text(value, field="sha256")
    if _SHA256_RE.fullmatch(digest) is None:
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return digest


def validate_generated_at(value: object) -> str:
    timestamp = _require_text(value, field="generated_at")
    match = _RFC3339_UTC_RE.fullmatch(timestamp)
    if match is None:
        raise ValueError(
            "generated_at must be an RFC 3339 UTC timestamp ending in Z"
        )
    try:
        datetime.fromisoformat(timestamp.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("generated_at is not a valid UTC timestamp") from exc
    return timestamp


def _validate_artifacts(
    values: tuple[ArtifactManifestEntry, ...],
) -> tuple[ArtifactManifestEntry, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("artifacts must be an iterable of manifest entries")
    artifacts = tuple(values)
    if any(not isinstance(entry, ArtifactManifestEntry) for entry in artifacts):
        raise TypeError(
            "artifacts must contain ArtifactManifestEntry values"
        )
    paths = tuple(entry.path for entry in artifacts)
    if len(paths) != len(set(paths)):
        raise ValueError("artifact paths must be unique")
    if paths != tuple(sorted(paths)):
        raise ValueError("artifacts must be sorted by canonical path")
    return artifacts


def _validate_role(value: object) -> str:
    role = _require_text(value, field="role")
    if len(role) > 128 or _ROLE_RE.fullmatch(role) is None:
        raise ValueError("role must be a lowercase snake-case identifier")
    return role


def _validate_creator(value: object) -> str:
    creator = _require_text(value, field="created_by")
    if len(creator) > 128 or _CREATOR_RE.fullmatch(creator) is None:
        raise ValueError("created_by must be a stable lowercase identifier")
    return creator


def _validate_media_type(value: object) -> str:
    media_type = _require_text(value, field="media_type")
    if len(media_type) > 256 or _MEDIA_TYPE_RE.fullmatch(media_type) is None:
        raise ValueError("media_type must be a valid declared media type")
    return media_type


def _validate_schema_version(value: object) -> str:
    version = _require_text(value, field="schema_version")
    if _SCHEMA_VERSION_RE.fullmatch(version) is None:
        raise ValueError("schema_version must use MAJOR.MINOR form")
    return version


def _coerce_manifest_verification_mode(
    value: object,
) -> ManifestVerificationMode:
    if isinstance(value, ManifestVerificationMode):
        return value
    if not isinstance(value, str):
        raise TypeError(
            "mode must be ManifestVerificationMode or string"
        )
    try:
        return ManifestVerificationMode(value.strip().lower())
    except ValueError as exc:
        raise ValueError(
            f"unsupported manifest verification mode: {value!r}"
        ) from exc


def _validate_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a boolean")
    return value


def _validate_policy_values(
    values: tuple[str, ...],
    *,
    field: str,
    validator: object,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of strings")
    if not callable(validator):
        raise TypeError("validator must be callable")

    prepared = tuple(
        validator(value)  # type: ignore[operator]
        for value in values
    )
    if len(prepared) != len(set(prepared)):
        raise ValueError(f"{field} must not contain duplicates")
    return prepared


def _validate_owned_directory(value: object) -> str:
    path = _require_text(value, field="owned directory")
    if "\\" in path:
        raise ValueError("owned directory must use forward slashes")
    if path.startswith("/") or _DRIVE_PREFIX_RE.match(path):
        raise ValueError("owned directory must be run-relative")
    if path.endswith("/"):
        raise ValueError("owned directory must not end with a slash")

    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(
            "owned directory must be normalized and contain no traversal"
        )

    normalized = PurePosixPath(*parts).as_posix()
    if normalized != path:
        raise ValueError("owned directory is not in canonical form")
    return normalized


def _validate_non_negative_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _validate_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL characters")
    return value


def _validate_optional_path(value: object, *, field: str) -> Path | None:
    if value is None:
        return None
    return _validate_path(value, field=field)


def _validate_messages(
    values: tuple[str, ...],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of strings")
    messages = tuple(
        _require_text(value, field=f"{field} item") for value in values
    )
    if len(messages) != len(set(messages)):
        raise ValueError(f"{field} must not contain duplicates")
    return messages


def _validate_path_messages(
    values: tuple[str, ...],
    *,
    field: str,
    require_safe: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of strings")
    result: list[str] = []
    for value in values:
        if require_safe:
            result.append(validate_manifest_artifact_path(value))
        else:
            result.append(_require_text(value, field=f"{field} item"))
    paths = tuple(result)
    if len(paths) != len(set(paths)):
        raise ValueError(f"{field} must not contain duplicates")
    return paths


def _coerce_validation_status(value: object) -> ValidationStatus:
    if isinstance(value, ValidationStatus):
        return value
    if not isinstance(value, str):
        raise TypeError("status must be ValidationStatus or string")
    try:
        return ValidationStatus(value)
    except ValueError as exc:
        raise ValueError(f"unsupported validation status: {value!r}") from exc


def _stable_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL characters")
    return value


__all__ = (
    "ARTIFACT_MANIFEST_FILENAME",
    "ARTIFACT_MANIFEST_HASH_ALGORITHM",
    "ARTIFACT_MANIFEST_SCHEMA_ID",
    "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "ManifestVerificationMode",
    "ManifestVerificationPolicy",
    "ManifestVerificationResult",
    "ManifestWriteResult",
    "validate_generated_at",
    "validate_manifest_artifact_path",
    "validate_sha256",
)
