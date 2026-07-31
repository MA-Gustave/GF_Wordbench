"""Construction of canonical GF Wordbench artifact manifests."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Protocol, cast, runtime_checkable

from gf_wordbench.infrastructure.json_io import JsonObject, read_json, write_json
from gf_wordbench.kernel.errors import ArtifactError
from gf_wordbench.kernel.serialization import format_rfc3339_utc
from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.version import __version__

from .declarations import ArtifactDeclaration
from .hashing import FileHash, hash_file
from .media_types import validate_role_media_type
from .models import (
    ArtifactManifest,
    ArtifactManifestEntry,
    ManifestWriteResult,
)

MANIFEST_SCHEMA_ID: Final[str] = "gf-wordbench.artifact-manifest"
MANIFEST_SCHEMA_VERSION: Final[str] = "1.0"
MANIFEST_FILENAME: Final[str] = "manifest.json"
MANIFEST_HASH_ALGORITHM: Final[str] = "sha256"
MANIFEST_PRODUCER_NAME: Final[str] = "gf-wordbench"

_MAX_ARTIFACTS: Final[int] = 100_000
_DEFAULT_HASH_CHUNK_SIZE: Final[int] = 1024 * 1024
_NON_EMPTY_REQUIRED_ROLES: Final[frozenset[str]] = frozenset(
    {
        "machine_summary",
        "scenario_output",
        "pgf",
    }
)


class ManifestBuildError(ArtifactError):
    """The finalized artifact set cannot form a trustworthy manifest."""


class MissingRequiredArtifactError(ManifestBuildError):
    """A required declaration does not identify a finalized file."""


class UnsafeManifestPathError(ManifestBuildError):
    """An artifact declaration escapes or violates the run-root contract."""


class DuplicateManifestPathError(ManifestBuildError):
    """Two declarations resolve to the same canonical manifest identity."""


class ArtifactMutationError(ManifestBuildError):
    """An artifact changed while its final bytes were being measured."""


@runtime_checkable
class RunPathsLike(Protocol):
    run_id: object
    run_dir: Path
    manifest_json: Path


@runtime_checkable
class RunResultLike(Protocol):
    run_paths: RunPathsLike


@dataclass(frozen=True, slots=True)
class ManifestBuildPolicy:
    reject_symlinks: bool = True
    reject_undeclared_directories: bool = True
    verify_hash_stability: bool = True
    case_sensitive_paths: bool | None = None
    hash_chunk_size: int = _DEFAULT_HASH_CHUNK_SIZE
    max_artifacts: int = _MAX_ARTIFACTS
    non_empty_required_roles: frozenset[str] = _NON_EMPTY_REQUIRED_ROLES

    def __post_init__(self) -> None:
        for name in (
            "reject_symlinks",
            "reject_undeclared_directories",
            "verify_hash_stability",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")
        if (
            self.case_sensitive_paths is not None
            and type(self.case_sensitive_paths) is not bool
        ):
            raise TypeError("case_sensitive_paths must be a bool or None")
        if type(self.hash_chunk_size) is not int or self.hash_chunk_size < 1:
            raise ValueError("hash_chunk_size must be a positive integer")
        if type(self.max_artifacts) is not int or self.max_artifacts < 1:
            raise ValueError("max_artifacts must be a positive integer")
        roles = frozenset(self.non_empty_required_roles)
        if any(not isinstance(role, str) or not role.strip() for role in roles):
            raise ValueError(
                "non_empty_required_roles must contain non-empty strings"
            )
        object.__setattr__(self, "non_empty_required_roles", roles)


@dataclass(frozen=True, slots=True)
class ManifestBuildWarning:
    code: str
    path: str
    message: str

    def __post_init__(self) -> None:
        for name in ("code", "path", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
            if "\x00" in value:
                raise ValueError(f"{name} must not contain NUL")


@dataclass(frozen=True, slots=True)
class ManifestBuildResult:
    manifest: ArtifactManifest
    warnings: tuple[ManifestBuildWarning, ...]
    entry_count: int
    required_entry_count: int
    total_size_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, ArtifactManifest):
            raise TypeError("manifest must be ArtifactManifest")
        warnings = tuple(self.warnings)
        if any(not isinstance(item, ManifestBuildWarning) for item in warnings):
            raise TypeError(
                "warnings must contain ManifestBuildWarning values"
            )
        for name in (
            "entry_count",
            "required_entry_count",
            "total_size_bytes",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.entry_count != len(self.manifest.artifacts):
            raise ValueError(
                "entry_count must equal the manifest artifact count"
            )
        if self.required_entry_count > self.entry_count:
            raise ValueError(
                "required_entry_count must not exceed entry_count"
            )
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True, slots=True)
class _PreparedDeclaration:
    declaration: ArtifactDeclaration
    absolute_path: Path
    manifest_path: str


def build_manifest(
    run_result: RunResultLike,
    run_paths: RunPathsLike,
    artifact_declarations: Sequence[ArtifactDeclaration],
    *,
    generated_at: datetime | None = None,
    producer_version: str = __version__,
    policy: ManifestBuildPolicy | None = None,
) -> ArtifactManifest:
    """Build one canonical manifest from finalized declared artifact bytes."""

    return build_manifest_result(
        run_result,
        run_paths,
        artifact_declarations,
        generated_at=generated_at,
        producer_version=producer_version,
        policy=policy,
    ).manifest


def build_manifest_result(
    run_result: RunResultLike,
    run_paths: RunPathsLike,
    artifact_declarations: Sequence[ArtifactDeclaration],
    *,
    generated_at: datetime | None = None,
    producer_version: str = __version__,
    policy: ManifestBuildPolicy | None = None,
) -> ManifestBuildResult:
    """Build a manifest and retain bounded non-fatal declaration warnings."""

    selected_policy = ManifestBuildPolicy() if policy is None else policy
    if not isinstance(selected_policy, ManifestBuildPolicy):
        raise TypeError("policy must be ManifestBuildPolicy or None")

    authoritative_paths = _require_run_paths(run_paths)
    _validate_run_result_paths(run_result, authoritative_paths)
    run_root, manifest_target = _manifest_location(authoritative_paths)

    run_id = _canonical_run_id(authoritative_paths.run_id)
    producer_version = _non_empty_text(
        producer_version,
        field_name="producer_version",
    )
    timestamp = _generation_timestamp(generated_at)

    declarations = _prepare_declaration_sequence(
        artifact_declarations,
        run_root=run_root,
        manifest_target=manifest_target,
        policy=selected_policy,
    )

    entries: list[ArtifactManifestEntry] = []
    warnings: list[ManifestBuildWarning] = []

    for prepared in declarations:
        declaration = prepared.declaration
        artifact_path = prepared.absolute_path

        try:
            entry = _build_entry(
                declaration,
                artifact_path=artifact_path,
                manifest_path=prepared.manifest_path,
                run_root=run_root,
                policy=selected_policy,
            )
        except FileNotFoundError:
            if declaration.required:
                raise MissingRequiredArtifactError(
                    "required artifact is missing: "
                    f"{prepared.manifest_path}"
                ) from None
            warnings.append(
                ManifestBuildWarning(
                    code="optional_artifact_missing",
                    path=prepared.manifest_path,
                    message="Optional artifact was not present and was omitted.",
                )
            )
            continue
        except PermissionError as exc:
            if declaration.required:
                raise MissingRequiredArtifactError(
                    "required artifact is unreadable: "
                    f"{prepared.manifest_path}: {exc}"
                ) from exc
            warnings.append(
                ManifestBuildWarning(
                    code="optional_artifact_unreadable",
                    path=prepared.manifest_path,
                    message=(
                        "Optional artifact could not be read and was omitted."
                    ),
                )
            )
            continue

        entries.append(entry)

    entries.sort(key=lambda item: item.path)
    _validate_entry_uniqueness(
        entries,
        case_sensitive=_case_sensitive(selected_policy),
    )

    manifest = ArtifactManifest(
        schema_id=MANIFEST_SCHEMA_ID,
        schema_version=MANIFEST_SCHEMA_VERSION,
        producer_name=MANIFEST_PRODUCER_NAME,
        producer_version=producer_version,
        run_id=run_id,
        generated_at=timestamp,
        hash_algorithm=MANIFEST_HASH_ALGORITHM,
        artifacts=tuple(entries),
    )

    return ManifestBuildResult(
        manifest=manifest,
        warnings=tuple(warnings),
        entry_count=manifest.entry_count,
        required_entry_count=manifest.required_entry_count,
        total_size_bytes=manifest.total_size_bytes,
    )


def build_manifest_from_result(
    run_result: RunResultLike,
    artifact_declarations: Sequence[ArtifactDeclaration],
    *,
    generated_at: datetime | None = None,
    producer_version: str = __version__,
    policy: ManifestBuildPolicy | None = None,
) -> ArtifactManifest:
    """Build a manifest using the authoritative paths carried by RunResult."""

    if not isinstance(run_result, RunResultLike):
        raise TypeError("run_result must expose a RunPaths-compatible run_paths")
    return build_manifest(
        run_result,
        run_result.run_paths,
        artifact_declarations,
        generated_at=generated_at,
        producer_version=producer_version,
        policy=policy,
    )


def write_manifest(
    manifest: ArtifactManifest,
    run_paths: RunPathsLike,
) -> ManifestWriteResult:
    """Atomically persist and re-validate one canonical artifact manifest.

    The function never claims success until the final ``manifest.json`` has
    been re-read, schema-validated, and confirmed equal to the supplied model.
    Runtime or persistence failures are contained in ``ManifestWriteResult``;
    invalid manifest argument types still fail fast with ``TypeError``.
    """

    if not isinstance(manifest, ArtifactManifest):
        raise TypeError("manifest must be ArtifactManifest")

    try:
        authoritative_paths = _require_run_paths(run_paths)
        _, manifest_target = _manifest_location(authoritative_paths)
        _validate_manifest_run_id(manifest, authoritative_paths)

        document = _serialize_manifest_document(manifest)
        written_path = write_json(manifest_target, document)
        persisted_document = read_json(written_path)
        persisted_manifest = _parse_manifest_document(persisted_document)

        if persisted_document != document:
            raise ManifestBuildError(
                "persisted manifest document differs from canonical serialization"
            )
        if persisted_manifest != manifest:
            raise ManifestBuildError(
                "persisted manifest model differs from the supplied manifest"
            )

        return ManifestWriteResult(
            status=ValidationStatus.OK,
            manifest_path=written_path.resolve(strict=True),
            entry_count=manifest.entry_count,
            required_entry_count=manifest.required_entry_count,
            total_size_bytes=manifest.total_size_bytes,
            warnings=(),
            message="Canonical artifact manifest written and validated.",
        )
    except Exception as exc:  # reporting boundary: return structured failure
        return ManifestWriteResult(
            status=ValidationStatus.ERROR,
            manifest_path=None,
            entry_count=manifest.entry_count,
            required_entry_count=manifest.required_entry_count,
            total_size_bytes=manifest.total_size_bytes,
            warnings=(),
            message=_manifest_write_error_message(exc),
        )


def _serialize_manifest_document(manifest: ArtifactManifest) -> JsonObject:
    # Lazy import avoids coupling package initialization to schema loading.
    from gf_wordbench.reporting.schemas.manifest_v1 import (
        serialize_artifact_manifest,
    )

    return cast(JsonObject, serialize_artifact_manifest(manifest))


def _parse_manifest_document(document: JsonObject) -> ArtifactManifest:
    from gf_wordbench.reporting.schemas.manifest_v1 import parse_artifact_manifest

    return parse_artifact_manifest(document, strict=True)


def _manifest_write_error_message(exc: Exception) -> str:
    detail = " ".join(str(exc).replace("\x00", "").split())
    if not detail:
        detail = type(exc).__name__
    elif not detail.startswith(type(exc).__name__):
        detail = f"{type(exc).__name__}: {detail}"
    return f"Canonical artifact manifest write failed: {detail[:1000]}"


def canonical_manifest_path(
    artifact_path: Path,
    *,
    run_root: Path,
    case_sensitive: bool | None = None,
) -> str:
    """Return a safe canonical run-relative POSIX artifact identity."""

    if not isinstance(artifact_path, Path):
        raise TypeError("artifact_path must be pathlib.Path")
    if case_sensitive is not None and type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool or None")

    root = _resolved_directory(run_root, field_name="run_root")
    candidate = _resolved_candidate(
        artifact_path,
        run_root=root,
        field_name="artifact_path",
        require_exists=False,
    )
    return _canonical_manifest_path_from_resolved(candidate, run_root=root)


def _canonical_manifest_path_from_resolved(
    artifact_path: Path,
    *,
    run_root: Path,
) -> str:
    try:
        relative = artifact_path.relative_to(run_root)
    except ValueError as exc:
        raise UnsafeManifestPathError(
            f"artifact path escapes run root: {artifact_path}"
        ) from exc

    normalized = relative.as_posix()
    _validate_manifest_relative_path(normalized)
    if normalized == MANIFEST_FILENAME:
        raise UnsafeManifestPathError("manifest.json must not include itself")
    return normalized


def manifest_path_comparison_key(
    manifest_path: str,
    *,
    case_sensitive: bool | None = None,
) -> str:
    """Return the platform-policy comparison key for a manifest path."""

    _validate_manifest_relative_path(manifest_path)
    sensitive = (
        _platform_paths_are_case_sensitive()
        if case_sensitive is None
        else case_sensitive
    )
    if type(sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool or None")
    return manifest_path if sensitive else manifest_path.casefold()


def _prepare_declaration_sequence(
    declarations: Sequence[ArtifactDeclaration],
    *,
    run_root: Path,
    manifest_target: Path,
    policy: ManifestBuildPolicy,
) -> tuple[_PreparedDeclaration, ...]:
    if isinstance(declarations, (str, bytes)):
        raise TypeError(
            "artifact_declarations must be a sequence of ArtifactDeclaration"
        )
    prepared_input = tuple(declarations)
    if len(prepared_input) > policy.max_artifacts:
        raise ManifestBuildError(
            "artifact declaration count exceeds the configured maximum"
        )

    prepared: list[_PreparedDeclaration] = []
    seen: dict[str, str] = {}
    sensitive = _case_sensitive(policy)

    for declaration in prepared_input:
        if not isinstance(declaration, ArtifactDeclaration):
            raise TypeError(
                "artifact_declarations must contain ArtifactDeclaration values"
            )
        if type(declaration.required) is not bool:
            raise TypeError("ArtifactDeclaration.required must be a bool")

        validate_role_media_type(
            declaration.role,
            declaration.media_type,
            strict=True,
        )

        candidate = declaration.path
        if not isinstance(candidate, Path):
            raise TypeError("ArtifactDeclaration.path must be pathlib.Path")
        if not candidate.is_absolute():
            candidate = run_root / candidate

        absolute = _resolved_candidate(
            candidate,
            run_root=run_root,
            field_name=f"artifact declaration {declaration.path!s}",
            require_exists=False,
        )
        if absolute == manifest_target:
            raise UnsafeManifestPathError(
                "manifest.json must not include itself"
            )

        manifest_path = _canonical_manifest_path_from_resolved(
            absolute,
            run_root=run_root,
        )
        key = manifest_path_comparison_key(
            manifest_path,
            case_sensitive=sensitive,
        )

        previous = seen.get(key)
        if previous is not None:
            raise DuplicateManifestPathError(
                "duplicate artifact path after normalization: "
                f"{previous!r} and {manifest_path!r}"
            )
        seen[key] = manifest_path

        prepared.append(
            _PreparedDeclaration(
                declaration=declaration,
                absolute_path=absolute,
                manifest_path=manifest_path,
            )
        )

    prepared.sort(key=lambda item: item.manifest_path)
    return tuple(prepared)


def _build_entry(
    declaration: ArtifactDeclaration,
    *,
    artifact_path: Path,
    manifest_path: str,
    run_root: Path,
    policy: ManifestBuildPolicy,
) -> ArtifactManifestEntry:
    try:
        link_metadata = artifact_path.lstat()
    except FileNotFoundError:
        raise

    is_symlink = stat.S_ISLNK(link_metadata.st_mode)
    if is_symlink and policy.reject_symlinks:
        raise UnsafeManifestPathError(
            f"symlink artifacts are prohibited: {manifest_path}"
        )

    resolved = artifact_path.resolve(strict=True)
    try:
        resolved.relative_to(run_root)
    except ValueError as exc:
        raise UnsafeManifestPathError(
            f"artifact resolves outside the run root: {manifest_path}"
        ) from exc

    metadata = resolved.stat()
    if stat.S_ISDIR(metadata.st_mode):
        if policy.reject_undeclared_directories:
            raise UnsafeManifestPathError(
                f"directories cannot be manifest entries: {manifest_path}"
            )
        raise FileNotFoundError(manifest_path)
    if not stat.S_ISREG(metadata.st_mode):
        raise UnsafeManifestPathError(
            f"artifact is not a regular file: {manifest_path}"
        )

    file_hash = hash_file(
        resolved,
        algorithm=MANIFEST_HASH_ALGORITHM,
        chunk_size=policy.hash_chunk_size,
        verify_stability=policy.verify_hash_stability,
    )
    if not isinstance(file_hash, FileHash):
        raise TypeError("hash_file must return FileHash")
    if file_hash.algorithm != MANIFEST_HASH_ALGORITHM:
        raise ManifestBuildError(
            f"unsupported hash algorithm returned for {manifest_path}"
        )
    if file_hash.changed_during_read:
        raise ArtifactMutationError(
            f"artifact changed while hashing: {manifest_path}"
        )
    if file_hash.size_bytes != metadata.st_size:
        raise ArtifactMutationError(
            f"artifact size changed while hashing: {manifest_path}"
        )

    if (
        declaration.required
        and declaration.role in policy.non_empty_required_roles
        and file_hash.size_bytes == 0
    ):
        raise MissingRequiredArtifactError(
            f"required artifact must be non-empty: {manifest_path}"
        )

    return ArtifactManifestEntry(
        path=manifest_path,
        role=declaration.role,
        media_type=declaration.media_type,
        required=declaration.required,
        size_bytes=file_hash.size_bytes,
        sha256=file_hash.digest,
        created_by=declaration.created_by,
    )


def _validate_entry_uniqueness(
    entries: Iterable[ArtifactManifestEntry],
    *,
    case_sensitive: bool,
) -> None:
    seen: dict[str, str] = {}
    for entry in entries:
        key = manifest_path_comparison_key(
            entry.path,
            case_sensitive=case_sensitive,
        )
        previous = seen.get(key)
        if previous is not None:
            raise DuplicateManifestPathError(
                f"duplicate manifest entries: {previous!r}, {entry.path!r}"
            )
        seen[key] = entry.path


def _manifest_location(run_paths: RunPathsLike) -> tuple[Path, Path]:
    run_root = _resolved_directory(
        run_paths.run_dir,
        field_name="run_paths.run_dir",
    )
    manifest_target = _resolved_candidate(
        run_paths.manifest_json,
        run_root=run_root,
        field_name="run_paths.manifest_json",
    )
    if manifest_target.name != MANIFEST_FILENAME:
        raise UnsafeManifestPathError(
            f"manifest target must be named {MANIFEST_FILENAME!r}"
        )
    if manifest_target.parent != run_root:
        raise UnsafeManifestPathError(
            "manifest target must be a direct child of the run directory"
        )
    return run_root, manifest_target


def _validate_manifest_run_id(
    manifest: ArtifactManifest,
    run_paths: RunPathsLike,
) -> None:
    expected = _canonical_run_id(run_paths.run_id)
    if manifest.run_id != expected:
        raise ManifestBuildError(
            "manifest and run_paths use different run identifiers"
        )


def _validate_run_result_paths(
    run_result: RunResultLike,
    run_paths: RunPathsLike,
) -> None:
    if not isinstance(run_result, RunResultLike):
        raise TypeError("run_result must expose a RunPaths-compatible run_paths")
    result_paths = _require_run_paths(run_result.run_paths)
    if _canonical_run_id(result_paths.run_id) != _canonical_run_id(
        run_paths.run_id
    ):
        raise ManifestBuildError(
            "run_result and run_paths use different run identifiers"
        )
    if result_paths.run_dir.resolve(strict=False) != run_paths.run_dir.resolve(
        strict=False
    ):
        raise ManifestBuildError(
            "run_result and run_paths use different run directories"
        )
    if result_paths.manifest_json.resolve(
        strict=False
    ) != run_paths.manifest_json.resolve(strict=False):
        raise ManifestBuildError(
            "run_result and run_paths use different manifest targets"
        )


def _require_run_paths(value: object) -> RunPathsLike:
    if not isinstance(value, RunPathsLike):
        raise TypeError(
            "run_paths must expose run_id, run_dir, and manifest_json"
        )
    if not isinstance(value.run_dir, Path):
        raise TypeError("run_paths.run_dir must be pathlib.Path")
    if not isinstance(value.manifest_json, Path):
        raise TypeError("run_paths.manifest_json must be pathlib.Path")
    return value


def _resolved_directory(path: Path, *, field_name: str) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    resolved = path.resolve(strict=True)
    if not resolved.is_dir():
        raise ManifestBuildError(f"{field_name} is not a directory")
    return resolved


def _resolved_candidate(
    path: Path,
    *,
    run_root: Path,
    field_name: str,
    require_exists: bool = False,
) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")

    candidate = path if path.is_absolute() else run_root / path
    resolved = candidate.resolve(strict=require_exists)
    try:
        resolved.relative_to(run_root)
    except ValueError as exc:
        raise UnsafeManifestPathError(
            f"{field_name} escapes the run root"
        ) from exc
    return resolved


def _validate_manifest_relative_path(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("manifest path must be a string")
    if not value or not value.strip():
        raise UnsafeManifestPathError("manifest path must not be empty")
    if "\x00" in value:
        raise UnsafeManifestPathError(
            "manifest path must not contain NUL"
        )
    if "\\" in value:
        raise UnsafeManifestPathError(
            "manifest path must use forward slashes"
        )
    if value.startswith(("/", "//")):
        raise UnsafeManifestPathError(
            "manifest path must be run-relative"
        )
    if "://" in value:
        raise UnsafeManifestPathError(
            "manifest path must not contain a URI scheme"
        )
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise UnsafeManifestPathError(
            "manifest path must not contain a drive prefix"
        )

    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise UnsafeManifestPathError(
            "manifest path contains an unsafe or unresolved segment"
        )


def _generation_timestamp(value: datetime | None) -> str:
    timestamp = datetime.now(timezone.utc) if value is None else value
    if not isinstance(timestamp, datetime):
        raise TypeError("generated_at must be datetime or None")
    return format_rfc3339_utc(timestamp)


def _canonical_run_id(value: object) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raw = str(raw)
    return _non_empty_text(raw, field_name="run_id")


def _non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _case_sensitive(policy: ManifestBuildPolicy) -> bool:
    if policy.case_sensitive_paths is not None:
        return policy.case_sensitive_paths
    return _platform_paths_are_case_sensitive()


def _platform_paths_are_case_sensitive() -> bool:
    return os.path.normcase("Manifest-A") != os.path.normcase("manifest-a")


__all__ = (
    "ArtifactMutationError",
    "DuplicateManifestPathError",
    "MANIFEST_FILENAME",
    "MANIFEST_HASH_ALGORITHM",
    "MANIFEST_PRODUCER_NAME",
    "MANIFEST_SCHEMA_ID",
    "MANIFEST_SCHEMA_VERSION",
    "ManifestBuildError",
    "ManifestBuildPolicy",
    "ManifestBuildResult",
    "ManifestBuildWarning",
    "MissingRequiredArtifactError",
    "RunPathsLike",
    "RunResultLike",
    "UnsafeManifestPathError",
    "build_manifest",
    "build_manifest_from_result",
    "build_manifest_result",
    "canonical_manifest_path",
    "manifest_path_comparison_key",
    "write_manifest",
)
