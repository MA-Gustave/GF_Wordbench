from __future__ import annotations

import os
import shutil
import stat
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from .manifest.hashing import (
    FileHash,
    hash_file,
    normalize_sha256,
)

SUMMARY_FILENAME: Final[str] = "summary.json"
MANIFEST_FILENAME: Final[str] = "manifest.json"
DEFAULT_COPY_CHUNK_SIZE_BYTES: Final[int] = 1024 * 1024
MAX_COPY_CHUNK_SIZE_BYTES: Final[int] = 64 * 1024 * 1024
MAX_PUBLICATION_ENTRIES: Final[int] = 100_000
MAX_ERROR_LENGTH: Final[int] = 4_000

MetadataValue: TypeAlias = str | int | bool | float | None
PublicationMetadata: TypeAlias = Mapping[str, MetadataValue]


@unique
class PublicationKind(StrEnum):
    ARTIFACT_SET = "artifact_set"
    COMPLETE_RUN = "complete_run"
    RELEASE_PACKAGE = "release_package"


@unique
class PublicationConflictPolicy(StrEnum):
    FAIL = "fail"
    REUSE_IDENTICAL = "reuse_identical"
    REPLACE = "replace"


@unique
class PublicationEntryStatus(StrEnum):
    PUBLISHED = "published"
    ALREADY_PRESENT = "already_present"
    FAILED = "failed"
    SKIPPED = "skipped"


@unique
class PublicationStatus(StrEnum):
    PUBLISHED = "published"
    ALREADY_PRESENT = "already_present"
    FAILED = "failed"


class PublicationError(Exception):
    pass


class PublicationContractError(PublicationError):
    pass


class PublicationSourceError(PublicationError):
    pass


class PublicationDestinationError(PublicationError):
    pass


class PublicationVerificationError(PublicationError):
    pass


class PublicationConflictError(PublicationError):
    pass


@dataclass(frozen=True, slots=True)
class PublicationEntry:
    source_path: str
    published_path: str | None = None
    role: str = "artifact"
    media_type: str = "application/octet-stream"
    required: bool = True
    expected_size_bytes: int | None = None
    expected_sha256: str | None = None
    metadata: PublicationMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_path = _relative_path_text(
            self.source_path,
            "source_path",
        )
        published_path = (
            source_path
            if self.published_path is None
            else _relative_path_text(
                self.published_path,
                "published_path",
            )
        )
        role = _token(self.role, "role")
        media_type = _media_type(self.media_type)
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        expected_size_bytes = _optional_non_negative_int(
            self.expected_size_bytes,
            "expected_size_bytes",
        )
        expected_sha256 = (
            None
            if self.expected_sha256 is None
            else normalize_sha256(self.expected_sha256)
        )
        metadata = _freeze_metadata(self.metadata)

        object.__setattr__(self, "source_path", source_path)
        object.__setattr__(self, "published_path", published_path)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(
            self,
            "expected_size_bytes",
            expected_size_bytes,
        )
        object.__setattr__(
            self,
            "expected_sha256",
            expected_sha256,
        )
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True, slots=True)
class PublicationRequest:
    source_root: Path
    destination: Path
    entries: tuple[PublicationEntry, ...]
    kind: PublicationKind = PublicationKind.ARTIFACT_SET
    conflict_policy: PublicationConflictPolicy = (
        PublicationConflictPolicy.FAIL
    )
    require_finalized_run: bool = True
    require_summary: bool = True
    require_manifest: bool = True
    verify_source_stability: bool = True
    verify_destination: bool = True
    preserve_timestamps: bool = True
    copy_chunk_size_bytes: int = DEFAULT_COPY_CHUNK_SIZE_BYTES
    source_manifest_sha256: str | None = None
    metadata: PublicationMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_root = _absolute_path(
            self.source_root,
            "source_root",
        )
        destination = _absolute_path(
            self.destination,
            "destination",
        )
        entries = _entries(self.entries)
        if not isinstance(self.kind, PublicationKind):
            raise TypeError("kind must be PublicationKind")
        if not isinstance(
            self.conflict_policy,
            PublicationConflictPolicy,
        ):
            raise TypeError(
                "conflict_policy must be PublicationConflictPolicy"
            )
        for field_name in (
            "require_finalized_run",
            "require_summary",
            "require_manifest",
            "verify_source_stability",
            "verify_destination",
            "preserve_timestamps",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        copy_chunk_size_bytes = _chunk_size(
            self.copy_chunk_size_bytes
        )
        source_manifest_sha256 = (
            None
            if self.source_manifest_sha256 is None
            else normalize_sha256(self.source_manifest_sha256)
        )
        metadata = _freeze_metadata(self.metadata)

        if _paths_overlap(source_root, destination):
            raise PublicationContractError(
                "source_root and destination must not overlap"
            )
        if self.require_summary and not _contains_published_path(
            entries,
            SUMMARY_FILENAME,
        ):
            raise PublicationContractError(
                "required summary.json is absent from publication entries"
            )
        if self.require_manifest and not _contains_published_path(
            entries,
            MANIFEST_FILENAME,
        ):
            raise PublicationContractError(
                "required manifest.json is absent from publication entries"
            )
        if (
            source_manifest_sha256 is not None
            and not _contains_source_path(entries, MANIFEST_FILENAME)
        ):
            raise PublicationContractError(
                "source_manifest_sha256 requires manifest.json"
            )

        object.__setattr__(self, "source_root", source_root)
        object.__setattr__(self, "destination", destination)
        object.__setattr__(self, "entries", entries)
        object.__setattr__(
            self,
            "copy_chunk_size_bytes",
            copy_chunk_size_bytes,
        )
        object.__setattr__(
            self,
            "source_manifest_sha256",
            source_manifest_sha256,
        )
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True, slots=True)
class PublicationEntryOutcome:
    source_path: str
    published_path: str
    role: str
    required: bool
    status: PublicationEntryStatus
    size_bytes: int | None = None
    sha256: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        source_path = _relative_path_text(
            self.source_path,
            "source_path",
        )
        published_path = _relative_path_text(
            self.published_path,
            "published_path",
        )
        role = _token(self.role, "role")
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if not isinstance(self.status, PublicationEntryStatus):
            raise TypeError(
                "status must be PublicationEntryStatus"
            )
        size_bytes = _optional_non_negative_int(
            self.size_bytes,
            "size_bytes",
        )
        sha256 = (
            None
            if self.sha256 is None
            else normalize_sha256(self.sha256)
        )
        error = (
            None
            if self.error is None
            else _bounded_text(self.error, "error")
        )

        if self.status in {
            PublicationEntryStatus.PUBLISHED,
            PublicationEntryStatus.ALREADY_PRESENT,
        }:
            if size_bytes is None or sha256 is None:
                raise ValueError(
                    "successful entry outcome requires size and sha256"
                )
            if error is not None:
                raise ValueError(
                    "successful entry outcome cannot contain error"
                )
        if self.status is PublicationEntryStatus.FAILED:
            if error is None:
                raise ValueError(
                    "failed entry outcome requires error"
                )

        object.__setattr__(self, "source_path", source_path)
        object.__setattr__(
            self,
            "published_path",
            published_path,
        )
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "size_bytes", size_bytes)
        object.__setattr__(self, "sha256", sha256)
        object.__setattr__(self, "error", error)


@dataclass(frozen=True, slots=True)
class PublicationResult:
    source_root: Path
    destination: Path
    kind: PublicationKind
    status: PublicationStatus
    started_at: datetime
    finished_at: datetime
    outcomes: tuple[PublicationEntryOutcome, ...]
    source_manifest_sha256: str | None
    publication_id: str
    metadata: PublicationMetadata = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        source_root = _absolute_path(
            self.source_root,
            "source_root",
        )
        destination = _absolute_path(
            self.destination,
            "destination",
        )
        if not isinstance(self.kind, PublicationKind):
            raise TypeError("kind must be PublicationKind")
        if not isinstance(self.status, PublicationStatus):
            raise TypeError("status must be PublicationStatus")
        started_at = _aware_utc(self.started_at, "started_at")
        finished_at = _aware_utc(
            self.finished_at,
            "finished_at",
        )
        if finished_at < started_at:
            raise ValueError(
                "finished_at must not precede started_at"
            )
        if not isinstance(self.outcomes, tuple):
            raise TypeError("outcomes must be a tuple")
        for outcome in self.outcomes:
            if not isinstance(outcome, PublicationEntryOutcome):
                raise TypeError(
                    "outcomes must contain PublicationEntryOutcome"
                )
        source_manifest_sha256 = (
            None
            if self.source_manifest_sha256 is None
            else normalize_sha256(self.source_manifest_sha256)
        )
        publication_id = _token(
            self.publication_id,
            "publication_id",
        )
        metadata = _freeze_metadata(self.metadata)
        error = (
            None
            if self.error is None
            else _bounded_text(self.error, "error")
        )
        if self.status is PublicationStatus.FAILED and error is None:
            raise ValueError("failed publication requires error")
        if self.status is not PublicationStatus.FAILED and error is not None:
            raise ValueError(
                "successful publication cannot contain error"
            )
        if self.status is PublicationStatus.PUBLISHED and any(
            outcome.status
            not in {
                PublicationEntryStatus.PUBLISHED,
                PublicationEntryStatus.ALREADY_PRESENT,
            }
            for outcome in self.outcomes
        ):
            raise ValueError(
                "published result contains unsuccessful entries"
            )
        if self.status is PublicationStatus.ALREADY_PRESENT and any(
            outcome.status
            is not PublicationEntryStatus.ALREADY_PRESENT
            for outcome in self.outcomes
        ):
            raise ValueError(
                "already-present result contains changed entries"
            )

        object.__setattr__(self, "source_root", source_root)
        object.__setattr__(self, "destination", destination)
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "finished_at", finished_at)
        object.__setattr__(
            self,
            "source_manifest_sha256",
            source_manifest_sha256,
        )
        object.__setattr__(
            self,
            "publication_id",
            publication_id,
        )
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "error", error)

    @property
    def successful(self) -> bool:
        return self.status in {
            PublicationStatus.PUBLISHED,
            PublicationStatus.ALREADY_PRESENT,
        }

    @property
    def required_failures(
        self,
    ) -> tuple[PublicationEntryOutcome, ...]:
        return tuple(
            outcome
            for outcome in self.outcomes
            if outcome.required
            and outcome.status is PublicationEntryStatus.FAILED
        )

    @property
    def duration_ms(self) -> int:
        return max(
            0,
            int(
                (self.finished_at - self.started_at).total_seconds()
                * 1000
            ),
        )


@runtime_checkable
class PublicationClock(Protocol):
    def utc_now(self) -> datetime:
        ...


@runtime_checkable
class ArtifactPublisher(Protocol):
    def publish(
        self,
        request: PublicationRequest,
    ) -> PublicationResult:
        ...


class SystemPublicationClock:
    __slots__ = ()

    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)


class FilesystemArtifactPublisher:
    __slots__ = ("_clock",)

    def __init__(
        self,
        *,
        clock: PublicationClock | None = None,
    ) -> None:
        self._clock = (
            SystemPublicationClock()
            if clock is None
            else clock
        )
        if not isinstance(self._clock, PublicationClock):
            raise TypeError(
                "clock must satisfy PublicationClock"
            )

    def publish(
        self,
        request: PublicationRequest,
    ) -> PublicationResult:
        if not isinstance(request, PublicationRequest):
            raise TypeError(
                "request must be PublicationRequest"
            )
        return _publish(request, clock=self._clock)


def publish_artifacts(
    request: PublicationRequest,
    *,
    clock: PublicationClock | None = None,
) -> PublicationResult:
    return FilesystemArtifactPublisher(clock=clock).publish(request)


def publish_run(
    source_root: Path,
    destination: Path,
    *,
    conflict_policy: PublicationConflictPolicy = (
        PublicationConflictPolicy.FAIL
    ),
    verify_source_stability: bool = True,
    verify_destination: bool = True,
    preserve_timestamps: bool = True,
    copy_chunk_size_bytes: int = DEFAULT_COPY_CHUNK_SIZE_BYTES,
    source_manifest_sha256: str | None = None,
    exclude_paths: Iterable[str] = (),
    metadata: PublicationMetadata = MappingProxyType({}),
    clock: PublicationClock | None = None,
) -> PublicationResult:
    entries = discover_publication_entries(
        source_root,
        exclude_paths=exclude_paths,
    )
    request = PublicationRequest(
        source_root=source_root,
        destination=destination,
        entries=entries,
        kind=PublicationKind.COMPLETE_RUN,
        conflict_policy=conflict_policy,
        require_finalized_run=True,
        require_summary=True,
        require_manifest=True,
        verify_source_stability=verify_source_stability,
        verify_destination=verify_destination,
        preserve_timestamps=preserve_timestamps,
        copy_chunk_size_bytes=copy_chunk_size_bytes,
        source_manifest_sha256=source_manifest_sha256,
        metadata=metadata,
    )
    return publish_artifacts(request, clock=clock)


def discover_publication_entries(
    source_root: Path,
    *,
    exclude_paths: Iterable[str] = (),
    role_resolver: Callable[[str], str] | None = None,
    media_type_resolver: Callable[[str], str] | None = None,
) -> tuple[PublicationEntry, ...]:
    root = _absolute_path(source_root, "source_root")
    if not root.exists():
        raise PublicationSourceError(
            f"source root does not exist: {root}"
        )
    if not root.is_dir():
        raise PublicationSourceError(
            f"source root is not a directory: {root}"
        )
    excluded = frozenset(
        _relative_path_text(value, "exclude_path")
        for value in exclude_paths
    )
    entries: list[PublicationEntry] = []
    for directory, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current = Path(directory)
        directory_names[:] = sorted(
            directory_names,
            key=lambda value: (value.casefold(), value),
        )
        file_names.sort(
            key=lambda value: (value.casefold(), value)
        )

        retained_directories: list[str] = []
        for name in directory_names:
            candidate = current / name
            relative = _relative_from_root(candidate, root)
            if relative in excluded:
                continue
            identity = candidate.lstat()
            if stat.S_ISLNK(identity.st_mode):
                raise PublicationSourceError(
                    f"symbolic-link directory is not publishable: "
                    f"{candidate}"
                )
            if not stat.S_ISDIR(identity.st_mode):
                raise PublicationSourceError(
                    f"non-directory tree entry is not publishable: "
                    f"{candidate}"
                )
            retained_directories.append(name)
        directory_names[:] = retained_directories

        for name in file_names:
            candidate = current / name
            relative = _relative_from_root(candidate, root)
            if relative in excluded:
                continue
            identity = candidate.lstat()
            if stat.S_ISLNK(identity.st_mode):
                raise PublicationSourceError(
                    f"symbolic-link file is not publishable: "
                    f"{candidate}"
                )
            if not stat.S_ISREG(identity.st_mode):
                raise PublicationSourceError(
                    f"non-regular file is not publishable: "
                    f"{candidate}"
                )
            role = (
                _default_role(relative)
                if role_resolver is None
                else _token(
                    role_resolver(relative),
                    "resolved role",
                )
            )
            media_type = (
                _default_media_type(relative)
                if media_type_resolver is None
                else _media_type(media_type_resolver(relative))
            )
            entries.append(
                PublicationEntry(
                    source_path=relative,
                    role=role,
                    media_type=media_type,
                    required=relative
                    in {SUMMARY_FILENAME, MANIFEST_FILENAME},
                )
            )
            if len(entries) > MAX_PUBLICATION_ENTRIES:
                raise PublicationSourceError(
                    "publication tree exceeds entry limit"
                )

    entries.sort(
        key=lambda item: (
            item.published_path.casefold(),
            item.published_path,
        )
    )
    return tuple(entries)


def _publish(
    request: PublicationRequest,
    *,
    clock: PublicationClock,
) -> PublicationResult:
    started_at = _clock_now(clock)
    publication_id = uuid.uuid4().hex
    staging = _staging_path(
        request.destination,
        publication_id,
    )
    backup = _backup_path(
        request.destination,
        publication_id,
    )
    source_hashes: dict[str, FileHash] = {}
    copied_outcomes: list[PublicationEntryOutcome] = []
    committed = False
    destination_preexisted = request.destination.exists()

    try:
        _validate_source_root(request)
        _validate_destination_parent(request.destination)
        source_hashes = _verify_sources(request)
        _prepare_staging(staging)

        for entry in request.entries:
            source_hash = source_hashes[entry.source_path]
            source = _contained_child(
                request.source_root,
                entry.source_path,
            )
            target = _contained_child(
                staging,
                entry.published_path,
            )
            _copy_file(
                source,
                target,
                chunk_size_bytes=request.copy_chunk_size_bytes,
                preserve_timestamps=request.preserve_timestamps,
            )
            destination_hash = hash_file(
                target,
                chunk_size_bytes=request.copy_chunk_size_bytes,
                reject_symlinks=True,
                verify_reopen=request.verify_destination,
            )
            _require_same_bytes(
                entry,
                source_hash,
                destination_hash,
                label="staging copy",
            )
            copied_outcomes.append(
                PublicationEntryOutcome(
                    source_path=entry.source_path,
                    published_path=entry.published_path,
                    role=entry.role,
                    required=entry.required,
                    status=PublicationEntryStatus.PUBLISHED,
                    size_bytes=destination_hash.size_bytes,
                    sha256=destination_hash.sha256,
                )
            )

        if request.destination.exists():
            if (
                request.conflict_policy
                is PublicationConflictPolicy.FAIL
            ):
                raise PublicationConflictError(
                    f"publication destination already exists: "
                    f"{request.destination}"
                )
            if (
                request.conflict_policy
                is PublicationConflictPolicy.REUSE_IDENTICAL
            ):
                _verify_existing_destination(
                    request,
                    source_hashes,
                )
                _remove_tree(staging)
                finished_at = _clock_now(clock)
                return PublicationResult(
                    source_root=request.source_root,
                    destination=request.destination,
                    kind=request.kind,
                    status=PublicationStatus.ALREADY_PRESENT,
                    started_at=started_at,
                    finished_at=finished_at,
                    outcomes=tuple(
                        PublicationEntryOutcome(
                            source_path=entry.source_path,
                            published_path=entry.published_path,
                            role=entry.role,
                            required=entry.required,
                            status=(
                                PublicationEntryStatus.ALREADY_PRESENT
                            ),
                            size_bytes=source_hashes[
                                entry.source_path
                            ].size_bytes,
                            sha256=source_hashes[
                                entry.source_path
                            ].sha256,
                        )
                        for entry in request.entries
                    ),
                    source_manifest_sha256=_manifest_digest(
                        request,
                        source_hashes,
                    ),
                    publication_id=publication_id,
                    metadata=request.metadata,
                )
            _move_existing_to_backup(
                request.destination,
                backup,
            )

        os.replace(staging, request.destination)
        committed = True

        if request.verify_destination:
            _verify_existing_destination(
                request,
                source_hashes,
            )

        if backup.exists():
            _remove_tree(backup)

        finished_at = _clock_now(clock)
        return PublicationResult(
            source_root=request.source_root,
            destination=request.destination,
            kind=request.kind,
            status=PublicationStatus.PUBLISHED,
            started_at=started_at,
            finished_at=finished_at,
            outcomes=tuple(copied_outcomes),
            source_manifest_sha256=_manifest_digest(
                request,
                source_hashes,
            ),
            publication_id=publication_id,
            metadata=request.metadata,
        )
    except Exception as exc:
        _cleanup_failed_publication(
            destination=request.destination,
            staging=staging,
            backup=backup,
            committed=committed,
            destination_preexisted=destination_preexisted,
        )
        finished_at = _safe_clock_now(clock, started_at)
        failure_outcomes = _failure_outcomes(
            request,
            copied_outcomes,
            exc,
        )
        return PublicationResult(
            source_root=request.source_root,
            destination=request.destination,
            kind=request.kind,
            status=PublicationStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            outcomes=failure_outcomes,
            source_manifest_sha256=_manifest_digest(
                request,
                source_hashes,
            ),
            publication_id=publication_id,
            metadata=request.metadata,
            error=_exception_text(exc),
        )


def _validate_source_root(
    request: PublicationRequest,
) -> None:
    root = request.source_root
    try:
        identity = root.lstat()
    except FileNotFoundError as exc:
        raise PublicationSourceError(
            f"source root does not exist: {root}"
        ) from exc
    if stat.S_ISLNK(identity.st_mode):
        raise PublicationSourceError(
            f"source root cannot be a symbolic link: {root}"
        )
    if not stat.S_ISDIR(identity.st_mode):
        raise PublicationSourceError(
            f"source root is not a directory: {root}"
        )
    if request.require_finalized_run:
        summary = _contained_child(root, SUMMARY_FILENAME)
        manifest = _contained_child(root, MANIFEST_FILENAME)
        if request.require_summary and not summary.is_file():
            raise PublicationSourceError(
                f"finalized source run lacks {SUMMARY_FILENAME}"
            )
        if request.require_manifest and not manifest.is_file():
            raise PublicationSourceError(
                f"finalized source run lacks {MANIFEST_FILENAME}"
            )


def _verify_sources(
    request: PublicationRequest,
) -> dict[str, FileHash]:
    hashes: dict[str, FileHash] = {}
    for entry in request.entries:
        source = _contained_child(
            request.source_root,
            entry.source_path,
        )
        try:
            source_identity = source.lstat()
        except FileNotFoundError as exc:
            if entry.required:
                raise PublicationSourceError(
                    f"required publication source is missing: "
                    f"{source}"
                ) from exc
            continue
        if stat.S_ISLNK(source_identity.st_mode):
            raise PublicationSourceError(
                f"symbolic-link source is not publishable: {source}"
            )
        if not stat.S_ISREG(source_identity.st_mode):
            raise PublicationSourceError(
                f"publication source is not a regular file: {source}"
            )
        hashed = hash_file(
            source,
            chunk_size_bytes=request.copy_chunk_size_bytes,
            reject_symlinks=True,
            verify_reopen=request.verify_source_stability,
        )
        if (
            entry.expected_size_bytes is not None
            and hashed.size_bytes != entry.expected_size_bytes
        ):
            raise PublicationVerificationError(
                f"source size mismatch for {entry.source_path}: "
                f"expected {entry.expected_size_bytes}, "
                f"observed {hashed.size_bytes}"
            )
        if (
            entry.expected_sha256 is not None
            and hashed.sha256 != entry.expected_sha256
        ):
            raise PublicationVerificationError(
                f"source hash mismatch for {entry.source_path}"
            )
        hashes[entry.source_path] = hashed

    optional_missing = tuple(
        entry
        for entry in request.entries
        if not entry.required
        and entry.source_path not in hashes
    )
    if optional_missing:
        retained = tuple(
            entry
            for entry in request.entries
            if entry.source_path in hashes
        )
        object.__setattr__(request, "entries", retained)

    manifest_hash = hashes.get(MANIFEST_FILENAME)
    if (
        request.source_manifest_sha256 is not None
        and (
            manifest_hash is None
            or manifest_hash.sha256
            != request.source_manifest_sha256
        )
    ):
        raise PublicationVerificationError(
            "source manifest hash does not match the approved digest"
        )
    return hashes


def _verify_existing_destination(
    request: PublicationRequest,
    source_hashes: Mapping[str, FileHash],
) -> None:
    destination = request.destination
    try:
        identity = destination.lstat()
    except FileNotFoundError as exc:
        raise PublicationDestinationError(
            f"published destination is missing: {destination}"
        ) from exc
    if stat.S_ISLNK(identity.st_mode):
        raise PublicationDestinationError(
            f"published destination is a symbolic link: {destination}"
        )
    if not stat.S_ISDIR(identity.st_mode):
        raise PublicationDestinationError(
            f"published destination is not a directory: "
            f"{destination}"
        )

    expected_paths = {
        entry.published_path
        for entry in request.entries
    }
    actual_paths = _regular_tree_paths(destination)
    if actual_paths != expected_paths:
        missing = sorted(
            expected_paths - actual_paths,
            key=lambda value: (value.casefold(), value),
        )
        extra = sorted(
            actual_paths - expected_paths,
            key=lambda value: (value.casefold(), value),
        )
        detail: list[str] = []
        if missing:
            detail.append("missing=" + ",".join(missing[:8]))
        if extra:
            detail.append("extra=" + ",".join(extra[:8]))
        raise PublicationVerificationError(
            "published artifact set differs from requested set: "
            + "; ".join(detail)
        )

    for entry in request.entries:
        source_hash = source_hashes[entry.source_path]
        target = _contained_child(
            destination,
            entry.published_path,
        )
        target_hash = hash_file(
            target,
            chunk_size_bytes=request.copy_chunk_size_bytes,
            reject_symlinks=True,
            verify_reopen=request.verify_destination,
        )
        _require_same_bytes(
            entry,
            source_hash,
            target_hash,
            label="published destination",
        )


def _regular_tree_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for directory, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current = Path(directory)
        retained: list[str] = []
        for name in directory_names:
            candidate = current / name
            identity = candidate.lstat()
            if stat.S_ISLNK(identity.st_mode):
                raise PublicationVerificationError(
                    f"published tree contains symbolic link: "
                    f"{candidate}"
                )
            if not stat.S_ISDIR(identity.st_mode):
                raise PublicationVerificationError(
                    f"published tree contains invalid directory entry: "
                    f"{candidate}"
                )
            retained.append(name)
        directory_names[:] = retained
        for name in file_names:
            candidate = current / name
            identity = candidate.lstat()
            if stat.S_ISLNK(identity.st_mode):
                raise PublicationVerificationError(
                    f"published tree contains symbolic link: "
                    f"{candidate}"
                )
            if not stat.S_ISREG(identity.st_mode):
                raise PublicationVerificationError(
                    f"published tree contains non-regular file: "
                    f"{candidate}"
                )
            paths.add(_relative_from_root(candidate, root))
    return paths


def _copy_file(
    source: Path,
    destination: Path,
    *,
    chunk_size_bytes: int,
    preserve_timestamps: bool,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.{uuid.uuid4().hex}.tmp"
    )
    source_descriptor = -1
    destination_descriptor = -1
    try:
        source_descriptor = _open_source(source)
        destination_descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        while True:
            block = os.read(
                source_descriptor,
                chunk_size_bytes,
            )
            if not block:
                break
            view = memoryview(block)
            while view:
                written = os.write(
                    destination_descriptor,
                    view,
                )
                if written <= 0:
                    raise PublicationDestinationError(
                        f"short write while publishing {destination}"
                    )
                view = view[written:]
        os.fsync(destination_descriptor)
        source_stat = os.fstat(source_descriptor)
        destination_stat = os.fstat(destination_descriptor)
        if source_stat.st_size != destination_stat.st_size:
            raise PublicationVerificationError(
                f"copied size mismatch for {source}"
            )
        os.close(destination_descriptor)
        destination_descriptor = -1
        if preserve_timestamps:
            os.utime(
                temporary,
                ns=(
                    int(source_stat.st_atime_ns),
                    int(source_stat.st_mtime_ns),
                ),
                follow_symlinks=False,
            )
        os.replace(temporary, destination)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        if source_descriptor >= 0:
            os.close(source_descriptor)
        if destination_descriptor >= 0:
            os.close(destination_descriptor)


def _open_source(path: Path) -> int:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError as exc:
        raise PublicationSourceError(
            f"publication source disappeared: {path}"
        ) from exc
    identity = os.fstat(descriptor)
    if not stat.S_ISREG(identity.st_mode):
        os.close(descriptor)
        raise PublicationSourceError(
            f"publication source is not a regular file: {path}"
        )
    return descriptor


def _require_same_bytes(
    entry: PublicationEntry,
    source_hash: FileHash,
    destination_hash: FileHash,
    *,
    label: str,
) -> None:
    if source_hash.size_bytes != destination_hash.size_bytes:
        raise PublicationVerificationError(
            f"{label} size mismatch for {entry.published_path}"
        )
    if source_hash.sha256 != destination_hash.sha256:
        raise PublicationVerificationError(
            f"{label} hash mismatch for {entry.published_path}"
        )


def _prepare_staging(staging: Path) -> None:
    if staging.exists():
        _remove_tree(staging)
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir(mode=0o700)


def _move_existing_to_backup(
    destination: Path,
    backup: Path,
) -> None:
    if backup.exists():
        _remove_tree(backup)
    os.replace(destination, backup)


def _cleanup_failed_publication(
    *,
    destination: Path,
    staging: Path,
    backup: Path,
    committed: bool,
    destination_preexisted: bool,
) -> None:
    if staging.exists():
        try:
            _remove_tree(staging)
        except OSError:
            pass
    if backup.exists():
        try:
            if destination.exists():
                _remove_tree(destination)
            os.replace(backup, destination)
        except OSError:
            pass
    elif committed and not destination_preexisted:
        try:
            _remove_tree(destination)
        except OSError:
            pass


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    identity = path.lstat()
    if stat.S_ISLNK(identity.st_mode):
        path.unlink()
        return
    if stat.S_ISDIR(identity.st_mode):
        shutil.rmtree(path)
        return
    path.unlink()


def _validate_destination_parent(destination: Path) -> None:
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    identity = parent.lstat()
    if stat.S_ISLNK(identity.st_mode):
        raise PublicationDestinationError(
            f"destination parent cannot be a symbolic link: {parent}"
        )
    if not stat.S_ISDIR(identity.st_mode):
        raise PublicationDestinationError(
            f"destination parent is not a directory: {parent}"
        )


def _failure_outcomes(
    request: PublicationRequest,
    copied_outcomes: list[PublicationEntryOutcome],
    exc: BaseException,
) -> tuple[PublicationEntryOutcome, ...]:
    completed = {
        outcome.source_path: outcome
        for outcome in copied_outcomes
    }
    error = _exception_text(exc)
    outcomes: list[PublicationEntryOutcome] = []
    failed_assigned = False
    for entry in request.entries:
        previous = completed.get(entry.source_path)
        if previous is not None:
            outcomes.append(
                PublicationEntryOutcome(
                    source_path=entry.source_path,
                    published_path=entry.published_path,
                    role=entry.role,
                    required=entry.required,
                    status=PublicationEntryStatus.SKIPPED,
                    error=None,
                )
            )
            continue
        if not failed_assigned:
            outcomes.append(
                PublicationEntryOutcome(
                    source_path=entry.source_path,
                    published_path=entry.published_path,
                    role=entry.role,
                    required=entry.required,
                    status=PublicationEntryStatus.FAILED,
                    error=error,
                )
            )
            failed_assigned = True
        else:
            outcomes.append(
                PublicationEntryOutcome(
                    source_path=entry.source_path,
                    published_path=entry.published_path,
                    role=entry.role,
                    required=entry.required,
                    status=PublicationEntryStatus.SKIPPED,
                )
            )
    if not outcomes:
        return ()
    return tuple(outcomes)


def _manifest_digest(
    request: PublicationRequest,
    source_hashes: Mapping[str, FileHash],
) -> str | None:
    if request.source_manifest_sha256 is not None:
        return request.source_manifest_sha256
    hashed = source_hashes.get(MANIFEST_FILENAME)
    return None if hashed is None else hashed.sha256


def _entries(
    values: object,
) -> tuple[PublicationEntry, ...]:
    if not isinstance(values, tuple):
        raise TypeError("entries must be a tuple")
    if not values:
        raise ValueError("entries must not be empty")
    if len(values) > MAX_PUBLICATION_ENTRIES:
        raise ValueError("entries exceed publication limit")

    source_paths: set[str] = set()
    published_paths: set[str] = set()
    prepared: list[PublicationEntry] = []
    for value in values:
        if not isinstance(value, PublicationEntry):
            raise TypeError(
                "entries must contain PublicationEntry"
            )
        source_key = value.source_path.casefold()
        published_key = value.published_path.casefold()
        if source_key in source_paths:
            raise ValueError(
                f"duplicate source path: {value.source_path}"
            )
        if published_key in published_paths:
            raise ValueError(
                f"duplicate published path: "
                f"{value.published_path}"
            )
        source_paths.add(source_key)
        published_paths.add(published_key)
        prepared.append(value)
    return tuple(
        sorted(
            prepared,
            key=lambda item: (
                item.published_path.casefold(),
                item.published_path,
            ),
        )
    )


def _contains_source_path(
    entries: tuple[PublicationEntry, ...],
    value: str,
) -> bool:
    key = value.casefold()
    return any(
        entry.source_path.casefold() == key
        for entry in entries
    )


def _contains_published_path(
    entries: tuple[PublicationEntry, ...],
    value: str,
) -> bool:
    key = value.casefold()
    return any(
        entry.published_path.casefold() == key
        for entry in entries
    )


def _contained_child(root: Path, relative: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    normalized = Path(os.path.abspath(candidate))
    try:
        normalized.relative_to(root)
    except ValueError as exc:
        raise PublicationContractError(
            f"path escapes publication root: {relative}"
        ) from exc
    return normalized


def _relative_from_root(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise PublicationContractError(
            f"path is outside publication root: {path}"
        ) from exc
    return _relative_path_text(
        relative.as_posix(),
        "relative path",
    )


def _staging_path(
    destination: Path,
    publication_id: str,
) -> Path:
    return destination.with_name(
        f".{destination.name}.publish-{publication_id}.tmp"
    )


def _backup_path(
    destination: Path,
    publication_id: str,
) -> Path:
    return destination.with_name(
        f".{destination.name}.publish-{publication_id}.bak"
    )


def _paths_overlap(left: Path, right: Path) -> bool:
    return _within(left, right) or _within(right, left)


def _within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def _absolute_path(value: object, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    text = os.fspath(value)
    if "\x00" in text:
        raise ValueError(f"{field_name} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return Path(os.path.abspath(value))


def _relative_path_text(
    value: object,
    field_name: str,
) -> str:
    text = _required_text(value, field_name)
    if "\\" in text:
        raise ValueError(
            f"{field_name} must use forward slashes"
        )
    posix = PurePosixPath(text)
    windows = PureWindowsPath(text)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError(
            f"{field_name} must be a relative path"
        )
    if text == "." or any(
        part in {"", ".", ".."}
        for part in posix.parts
    ):
        raise ValueError(
            f"{field_name} contains an unsafe path segment"
        )
    canonical = posix.as_posix()
    if canonical != text:
        raise ValueError(
            f"{field_name} is not canonical"
        )
    return canonical


def _required_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(
            f"{field_name} must not have outer whitespace"
        )
    if "\x00" in value:
        raise ValueError(
            f"{field_name} must not contain NUL"
        )
    return value


def _bounded_text(
    value: object,
    field_name: str,
) -> str:
    text = _required_text(value, field_name)
    return text[:MAX_ERROR_LENGTH]


def _token(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if any(character.isspace() for character in text):
        raise ValueError(
            f"{field_name} must not contain whitespace"
        )
    return text


def _media_type(value: object) -> str:
    text = _required_text(value, "media_type").lower()
    if text.count("/") != 1:
        raise ValueError(
            "media_type must use type/subtype syntax"
        )
    major, minor = text.split("/", 1)
    if not major or not minor:
        raise ValueError(
            "media_type must use type/subtype syntax"
        )
    return text


def _optional_non_negative_int(
    value: object,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(
            f"{field_name} must be an integer or None"
        )
    if value < 0:
        raise ValueError(
            f"{field_name} must be non-negative"
        )
    return value


def _chunk_size(value: object) -> int:
    if type(value) is not int:
        raise TypeError(
            "copy_chunk_size_bytes must be an integer"
        )
    if value <= 0:
        raise ValueError(
            "copy_chunk_size_bytes must be positive"
        )
    if value > MAX_COPY_CHUNK_SIZE_BYTES:
        raise ValueError(
            "copy_chunk_size_bytes exceeds the supported maximum"
        )
    return value


def _freeze_metadata(
    values: PublicationMetadata,
) -> PublicationMetadata:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")
    copied: dict[str, MetadataValue] = {}
    for key, value in values.items():
        key = _token(key, "metadata key")
        if value is not None and type(value) not in {
            str,
            int,
            bool,
            float,
        }:
            raise TypeError(
                f"unsupported metadata value for {key!r}"
            )
        if type(value) is float and (
            value != value
            or value in {float("inf"), float("-inf")}
        ):
            raise ValueError(
                f"metadata value for {key!r} must be finite"
            )
        if isinstance(value, str):
            value = _required_text(
                value,
                f"metadata[{key!r}]",
            )
        copied[key] = value
    return MappingProxyType(copied)


def _aware_utc(
    value: object,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _clock_now(clock: PublicationClock) -> datetime:
    return _aware_utc(clock.utc_now(), "clock result")


def _safe_clock_now(
    clock: PublicationClock,
    fallback: datetime,
) -> datetime:
    try:
        value = _clock_now(clock)
    except Exception:
        return fallback
    return value if value >= fallback else fallback


def _exception_text(exc: BaseException) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text.replace("\x00", "\\x00")[:MAX_ERROR_LENGTH]


def _default_role(path: str) -> str:
    name = PurePosixPath(path).name
    if path == SUMMARY_FILENAME:
        return "machine_summary"
    if path == MANIFEST_FILENAME:
        return "artifact_manifest"
    if name == "summary.md":
        return "human_summary"
    if name == "AI_READY.md":
        return "ai_packet"
    if name == "top_errors.txt":
        return "top_errors"
    if path.startswith("raw/"):
        return "raw_evidence"
    if path.startswith("details/"):
        return "detail_report"
    if path.startswith("artifacts/pgf/"):
        return "pgf"
    if path.startswith("artifacts/gfo/"):
        return "gfo"
    if path.startswith("artifacts/"):
        return "generated_artifact"
    if path.startswith("logs/"):
        return "log"
    return "artifact"


def _default_media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.casefold()
    return {
        ".json": "application/json",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".log": "text/plain",
        ".out": "text/plain",
        ".diff": "text/plain",
        ".pgf": "application/octet-stream",
        ".gfo": "application/octet-stream",
        ".zip": "application/zip",
    }.get(suffix, "application/octet-stream")


__all__ = (
    "ArtifactPublisher",
    "DEFAULT_COPY_CHUNK_SIZE_BYTES",
    "FilesystemArtifactPublisher",
    "MANIFEST_FILENAME",
    "MAX_COPY_CHUNK_SIZE_BYTES",
    "MAX_PUBLICATION_ENTRIES",
    "MetadataValue",
    "PublicationClock",
    "PublicationConflictError",
    "PublicationConflictPolicy",
    "PublicationContractError",
    "PublicationDestinationError",
    "PublicationEntry",
    "PublicationEntryOutcome",
    "PublicationEntryStatus",
    "PublicationError",
    "PublicationKind",
    "PublicationMetadata",
    "PublicationRequest",
    "PublicationResult",
    "PublicationSourceError",
    "PublicationStatus",
    "PublicationVerificationError",
    "SUMMARY_FILENAME",
    "SystemPublicationClock",
    "discover_publication_entries",
    "publish_artifacts",
    "publish_run",
)
