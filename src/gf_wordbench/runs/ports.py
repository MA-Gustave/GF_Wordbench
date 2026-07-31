"""Mechanism-neutral ports owned by the run lifecycle module."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from gf_wordbench.kernel.ids import RunId, validate_run_id

if TYPE_CHECKING:
    from gf_wordbench.infrastructure.process.models import (
        ProcessEvent,
        ProcessRequest,
        ProcessResult,
    )

__all__ = (
    "ArchiveFormat",
    "ArtifactVerificationIssue",
    "ArtifactVerificationResult",
    "ArtifactVerifier",
    "CancellationSource",
    "ClockPort",
    "FileDigest",
    "FileHasher",
    "ProcessEventSink",
    "ProcessExecutor",
    "RunArchiveReceipt",
    "RunArchiveStore",
    "RunDirectoryStore",
    "RunHistoryReader",
    "RunLifecycleLease",
    "RunLifecycleLock",
    "RunLockRequest",
    "RunTreeEntry",
    "RunTreeEntryKind",
)


@unique
class RunTreeEntryKind(StrEnum):
    """Filesystem entry kinds relevant to run lifecycle operations."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    OTHER = "other"


@unique
class ArchiveFormat(StrEnum):
    """Supported run-archive container formats."""

    DIRECTORY = "directory"
    ZIP = "zip"
    TAR = "tar"


@dataclass(frozen=True, slots=True)
class RunTreeEntry:
    """Mechanism-neutral metadata for one entry beneath a run directory."""

    relative_path: Path
    kind: RunTreeEntryKind
    size_bytes: int | None = None
    link_target: Path | None = None

    def __post_init__(self) -> None:
        relative_path = _relative_path(
            self.relative_path,
            field_name="relative_path",
        )

        if not isinstance(self.kind, RunTreeEntryKind):
            raise TypeError("kind must be a RunTreeEntryKind")

        _validate_optional_non_negative_integer(
            self.size_bytes,
            field_name="size_bytes",
        )

        link_target = self.link_target
        if self.kind is RunTreeEntryKind.SYMLINK:
            if link_target is None:
                raise ValueError("a symlink entry requires link_target")
            link_target = _path(
                link_target,
                field_name="link_target",
            )
        elif link_target is not None:
            raise ValueError(
                "link_target is valid only for symlink entries"
            )

        object.__setattr__(self, "relative_path", relative_path)
        object.__setattr__(self, "link_target", link_target)


@dataclass(frozen=True, slots=True)
class FileDigest:
    """Verified SHA-256 facts for one finalized regular file."""

    path: Path
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        path = _path(
            self.path,
            field_name="path",
            require_absolute=True,
        )
        _validate_non_negative_integer(
            self.size_bytes,
            field_name="size_bytes",
        )
        sha256 = _validate_sha256(self.sha256)

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "sha256", sha256)


@dataclass(frozen=True, slots=True)
class ArtifactVerificationIssue:
    """One structured artifact-integrity problem."""

    code: str
    message: str
    path: Path | None = None
    required: bool = True

    def __post_init__(self) -> None:
        code = _required_text(
            self.code,
            field_name="code",
        )
        message = _required_text(
            self.message,
            field_name="message",
        )

        path = self.path
        if path is not None:
            path = _path(
                path,
                field_name="path",
                require_absolute=True,
            )

        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")

        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "path", path)


@dataclass(frozen=True, slots=True)
class ArtifactVerificationResult:
    """Structured result of read-only run artifact verification."""

    run_id: RunId
    manifest_path: Path
    valid: bool
    checked_files: int
    checked_bytes: int
    issues: tuple[ArtifactVerificationIssue, ...] = ()

    def __post_init__(self) -> None:
        run_id = validate_run_id(self.run_id)
        manifest_path = _path(
            self.manifest_path,
            field_name="manifest_path",
            require_absolute=True,
        )

        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a bool")

        _validate_non_negative_integer(
            self.checked_files,
            field_name="checked_files",
        )
        _validate_non_negative_integer(
            self.checked_bytes,
            field_name="checked_bytes",
        )

        issues = _typed_tuple(
            self.issues,
            item_type=ArtifactVerificationIssue,
            field_name="issues",
        )

        if self.valid and any(issue.required for issue in issues):
            raise ValueError(
                "valid verification cannot contain a required issue"
            )

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "manifest_path", manifest_path)
        object.__setattr__(self, "issues", issues)


@dataclass(frozen=True, slots=True)
class RunArchiveReceipt:
    """Verified facts returned after creation or extraction of a run archive."""

    run_id: RunId
    archive_path: Path
    format: ArchiveFormat
    entry_count: int
    size_bytes: int
    sha256: str | None
    verified: bool

    def __post_init__(self) -> None:
        run_id = validate_run_id(self.run_id)
        archive_path = _path(
            self.archive_path,
            field_name="archive_path",
            require_absolute=True,
        )

        if not isinstance(self.format, ArchiveFormat):
            raise TypeError("format must be an ArchiveFormat")

        _validate_non_negative_integer(
            self.entry_count,
            field_name="entry_count",
        )
        _validate_non_negative_integer(
            self.size_bytes,
            field_name="size_bytes",
        )

        sha256 = self.sha256
        if sha256 is not None:
            sha256 = _validate_sha256(sha256)

        if not isinstance(self.verified, bool):
            raise TypeError("verified must be a bool")
        if self.verified and sha256 is None:
            raise ValueError(
                "a verified archive receipt requires a SHA-256 digest"
            )

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "archive_path", archive_path)
        object.__setattr__(self, "sha256", sha256)


@dataclass(frozen=True, slots=True)
class RunLockRequest:
    """Bounded metadata for one active run lifecycle owner."""

    run_id: RunId
    process_id: int
    acquired_at: datetime
    run_dir: Path
    operation: str = "execute"

    def __post_init__(self) -> None:
        run_id = validate_run_id(self.run_id)
        _validate_positive_integer(
            self.process_id,
            field_name="process_id",
        )
        acquired_at = _utc_datetime(
            self.acquired_at,
            field_name="acquired_at",
        )
        run_dir = _path(
            self.run_dir,
            field_name="run_dir",
            require_absolute=True,
        )
        operation = _required_text(
            self.operation,
            field_name="operation",
        )

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "acquired_at", acquired_at)
        object.__setattr__(self, "run_dir", run_dir)
        object.__setattr__(self, "operation", operation)


ProcessEventSink = Callable[["ProcessEvent"], None]


@runtime_checkable
class ClockPort(Protocol):
    """Provide wall-clock and monotonic time without hidden global reads."""

    def utc_now(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        ...

    def monotonic_now(self) -> float:
        """Return a monotonic instant in fractional seconds."""
        ...


@runtime_checkable
class RunDirectoryStore(Protocol):
    """Perform bounded filesystem mechanisms for one run lifecycle."""

    def resolve(self, path: Path) -> Path:
        """Return a normalized absolute, link-aware path."""
        ...

    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
        allow_root: bool = False,
    ) -> Path:
        """Return the resolved path or fail when it escapes the root."""
        ...

    def exists(self, path: Path) -> bool:
        """Return whether a path or filesystem link exists."""
        ...

    def is_file(self, path: Path) -> bool:
        """Return whether a path identifies a regular file."""
        ...

    def is_directory(self, path: Path) -> bool:
        """Return whether a path identifies a directory."""
        ...

    def is_symlink(self, path: Path) -> bool:
        """Return whether a path is a symbolic link or equivalent."""
        ...

    def create_directory(self, path: Path) -> None:
        """Atomically create one directory and fail if it exists."""
        ...

    def create_directories(
        self,
        paths: Sequence[Path],
    ) -> None:
        """Create a deterministic set of already validated directories."""
        ...

    def inspect_tree(
        self,
        root: Path,
    ) -> tuple[RunTreeEntry, ...]:
        """Return deterministic metadata without following unknown links."""
        ...

    def list_directories(
        self,
        root: Path,
    ) -> tuple[Path, ...]:
        """Return immediate child directories in deterministic order."""
        ...

    def read_bytes(self, path: Path) -> bytes:
        """Read one regular file as exact bytes."""
        ...

    def write_bytes_atomic(
        self,
        path: Path,
        payload: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        """Publish exact bytes through atomic sibling replacement."""
        ...

    def append_text(
        self,
        path: Path,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> None:
        """Append one run-owned text record without rewriting prior bytes."""
        ...

    def remove_tree(self, path: Path) -> None:
        """Remove exactly one prevalidated run-owned directory tree."""
        ...


@runtime_checkable
class RunHistoryReader(Protocol):
    """Read historical run evidence without mutating it."""

    def list_run_directories(
        self,
        output_root: Path,
    ) -> tuple[Path, ...]:
        """Return candidate run directories in deterministic order."""
        ...

    def read_optional_bytes(
        self,
        path: Path,
    ) -> bytes | None:
        """Return exact file bytes or None when the file is absent."""
        ...

    def inspect_tree(
        self,
        run_dir: Path,
    ) -> tuple[RunTreeEntry, ...]:
        """Return read-only deterministic metadata for a run tree."""
        ...


@runtime_checkable
class CancellationSource(Protocol):
    """Expose controlled cancellation state to run orchestration."""

    def is_cancellation_requested(self) -> bool:
        """Return whether controlled cancellation has been requested."""
        ...

    def cancellation_reason(self) -> str | None:
        """Return a non-secret reason when one was supplied."""
        ...

    def wait(self, timeout_sec: float | None = None) -> bool:
        """Wait until cancellation or timeout and report cancellation."""
        ...


@runtime_checkable
class ProcessExecutor(Protocol):
    """Execute one validated process request and preserve raw evidence."""

    def run(
        self,
        request: ProcessRequest,
        *,
        cancellation_source: CancellationSource | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult:
        """Return structured process facts without validation semantics."""
        ...


@runtime_checkable
class FileHasher(Protocol):
    """Compute exact finalized-file hashes."""

    def sha256(self, path: Path) -> FileDigest:
        """Return size and lowercase SHA-256 for one regular file."""
        ...


@runtime_checkable
class ArtifactVerifier(Protocol):
    """Verify a finalized run manifest and every declared artifact."""

    def verify(
        self,
        *,
        run_id: RunId,
        run_dir: Path,
        manifest_path: Path,
        strict: bool = False,
    ) -> ArtifactVerificationResult:
        """Return structured read-only integrity verification."""
        ...


@runtime_checkable
class RunArchiveStore(Protocol):
    """Create, verify, extract, and remove run archives."""

    def create_verified_archive(
        self,
        *,
        run_id: RunId,
        source_run_dir: Path,
        destination: Path,
        format: ArchiveFormat,
    ) -> RunArchiveReceipt:
        """Create an archive and return only after verification."""
        ...

    def verify(
        self,
        receipt: RunArchiveReceipt,
    ) -> RunArchiveReceipt:
        """Reopen and revalidate an existing archive receipt."""
        ...

    def extract_verified(
        self,
        receipt: RunArchiveReceipt,
        destination: Path,
    ) -> Path:
        """Extract into an empty destination and verify the restored run."""
        ...

    def remove_archive(self, receipt: RunArchiveReceipt) -> None:
        """Remove exactly the archive represented by a verified receipt."""
        ...


@runtime_checkable
class RunLifecycleLease(Protocol):
    """Held active-run lease returned by the lifecycle lock."""

    @property
    def path(self) -> Path:
        """Return the lock evidence path."""
        ...

    @property
    def request(self) -> RunLockRequest:
        """Return the request represented by this lease."""
        ...


@runtime_checkable
class RunLifecycleLock(Protocol):
    """Coordinate one lifecycle owner for a run directory."""

    def acquire(
        self,
        request: RunLockRequest,
    ) -> AbstractContextManager[RunLifecycleLease]:
        """Acquire the lease or fail explicitly and release it on exit."""
        ...


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(
            f"{field_name} must not contain NUL characters"
        )
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(
            f"{field_name} must not have outer whitespace"
        )
    return value


def _path(
    value: object,
    *,
    field_name: str,
    require_absolute: bool = False,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(
            f"{field_name} must not contain NUL characters"
        )
    if require_absolute and not value.is_absolute():
        raise ValueError(f"{field_name} must be an absolute path")
    return value


def _relative_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    path = _path(value, field_name=field_name)

    if path.is_absolute():
        raise ValueError(f"{field_name} must be relative")
    if not path.parts:
        raise ValueError(
            f"{field_name} must identify a tree entry"
        )
    if ".." in path.parts:
        raise ValueError(
            f"{field_name} must not contain parent traversal"
        )

    return path


def _utc_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _validate_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _validate_optional_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    return _validate_non_negative_integer(
        value,
        field_name=field_name,
    )


def _validate_sha256(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("sha256 must be a string")
    if len(value) != 64:
        raise ValueError("sha256 must contain exactly 64 hexadecimal digits")
    if value.lower() != value:
        raise ValueError("sha256 must use lowercase hexadecimal digits")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("sha256 must contain only hexadecimal digits")
    return value


def _typed_tuple(
    value: object,
    *,
    item_type: type[ArtifactVerificationIssue],
    field_name: str,
) -> tuple[ArtifactVerificationIssue, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not all(isinstance(item, item_type) for item in value):
        raise TypeError(
            f"every {field_name} item must be "
            f"{item_type.__name__}"
        )
    return value
