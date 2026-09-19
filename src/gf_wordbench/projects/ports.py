"""Mechanism-neutral ports owned by the active-project module.

These interfaces isolate TOML transport, filesystem access, template
materialization, archive creation, lifecycle locking, and clock access from
project-domain and application services.

They remain language-neutral and never infer project identity from application
state, previous runs, process-global working directories, or external portfolio
data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from gf_wordbench.projects.models import ProjectConfig

__all__ = (
    "ArchiveFormat",
    "ArchiveReceipt",
    "ClockPort",
    "LifecycleLease",
    "LifecycleLockRequest",
    "ProjectArchiveWriter",
    "ProjectConfigReader",
    "ProjectConfigWriter",
    "ProjectFilesystem",
    "ProjectLifecycleLock",
    "ProjectMigrationWorkspacePort",
    "ProjectTemplateSource",
    "TreeEntry",
    "TreeEntryKind",
)


@unique
class TreeEntryKind(StrEnum):
    """Filesystem entry kinds relevant to project lifecycle operations."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    OTHER = "other"


@unique
class ArchiveFormat(StrEnum):
    """Supported project-archive container formats."""

    DIRECTORY = "directory"
    ZIP = "zip"


@dataclass(frozen=True, slots=True)
class TreeEntry:
    """Mechanism-neutral metadata for one project-tree entry."""

    relative_path: Path
    kind: TreeEntryKind
    size_bytes: int | None = None
    link_target: Path | None = None

    def __post_init__(self) -> None:
        relative_path = _relative_path(
            self.relative_path,
            field_name="relative_path",
        )

        if not isinstance(self.kind, TreeEntryKind):
            raise TypeError("kind must be a TreeEntryKind")

        _validate_optional_non_negative_integer(
            self.size_bytes,
            field_name="size_bytes",
        )

        link_target = self.link_target
        if self.kind is TreeEntryKind.SYMLINK:
            if link_target is None:
                raise ValueError("a symlink entry requires link_target")
            link_target = _path(
                link_target,
                field_name="link_target",
            )
        elif link_target is not None:
            raise ValueError("link_target is valid only for symlink entries")

        object.__setattr__(self, "relative_path", relative_path)
        object.__setattr__(self, "link_target", link_target)


@dataclass(frozen=True, slots=True)
class ArchiveReceipt:
    """Verified facts returned after creation of a project archive."""

    destination: Path
    format: ArchiveFormat
    entry_count: int
    size_bytes: int
    verified: bool

    def __post_init__(self) -> None:
        destination = _path(
            self.destination,
            field_name="destination",
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

        if not isinstance(self.verified, bool):
            raise TypeError("verified must be a bool")

        object.__setattr__(self, "destination", destination)


@dataclass(frozen=True, slots=True)
class LifecycleLockRequest:
    """Bounded, non-secret metadata for one project lifecycle writer."""

    operation_id: str
    operation_type: str
    process_id: int
    started_at: datetime
    workspace_root: Path

    def __post_init__(self) -> None:
        _validate_required_text(
            self.operation_id,
            field_name="operation_id",
        )
        _validate_required_text(
            self.operation_type,
            field_name="operation_type",
        )
        _validate_positive_integer(
            self.process_id,
            field_name="process_id",
        )

        if not isinstance(self.started_at, datetime):
            raise TypeError("started_at must be a datetime")
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware")

        workspace_root = _path(
            self.workspace_root,
            field_name="workspace_root",
            require_absolute=True,
        )

        object.__setattr__(
            self,
            "started_at",
            self.started_at.astimezone(UTC),
        )
        object.__setattr__(
            self,
            "workspace_root",
            workspace_root,
        )


@runtime_checkable
class ClockPort(Protocol):
    """Provide the current timezone-aware UTC time."""

    def utc_now(self) -> datetime:
        """Return the current time as a timezone-aware UTC datetime."""
        ...


@runtime_checkable
class ProjectConfigReader(Protocol):
    """Read and decode one active-project TOML document."""

    def read(
        self,
        project_file: Path,
    ) -> Mapping[str, object]:
        """Return decoded TOML without applying project-domain semantics."""
        ...


@runtime_checkable
class ProjectConfigWriter(Protocol):
    """Persist an explicitly created or migrated project configuration."""

    def write(
        self,
        project_file: Path,
        config: ProjectConfig,
        *,
        overwrite: bool = False,
    ) -> None:
        """Write canonical project TOML atomically."""
        ...


@runtime_checkable
class ProjectFilesystem(Protocol):
    """Safe filesystem operations required by project lifecycle use cases."""

    def resolve(
        self,
        path: Path,
    ) -> Path:
        """Return a normalized absolute, link-aware path."""
        ...

    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
        allow_root: bool = False,
    ) -> Path:
        """Return the resolved path or raise when it escapes ``root``."""
        ...

    def exists(
        self,
        path: Path,
    ) -> bool:
        """Return whether the path exists, including a filesystem link."""
        ...

    def is_file(
        self,
        path: Path,
    ) -> bool:
        """Return whether the path identifies a regular file."""
        ...

    def is_directory(
        self,
        path: Path,
    ) -> bool:
        """Return whether the path identifies a directory."""
        ...

    def inspect_tree(
        self,
        root: Path,
    ) -> tuple[TreeEntry, ...]:
        """Return deterministic metadata without following unknown links."""
        ...

    def create_empty_directory(
        self,
        path: Path,
    ) -> None:
        """Create a directory and fail if the destination already exists."""
        ...

    def copy_tree(
        self,
        source: Path,
        destination: Path,
        *,
        preserved_links: Sequence[Path] = (),
    ) -> None:
        """Copy a tree while preserving only explicitly approved links."""
        ...

    def atomic_replace_directory(
        self,
        *,
        staged: Path,
        active: Path,
        rollback: Path,
    ) -> None:
        """Publish a staged project while retaining rollback material."""
        ...

    def restore_directory(
        self,
        *,
        rollback: Path,
        active: Path,
    ) -> None:
        """Restore a prior active-project directory after a failed swap."""
        ...

    def remove_tree(
        self,
        path: Path,
    ) -> None:
        """Remove exactly one prevalidated lifecycle-owned tree."""
        ...

    def read_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        """Read one text file using the explicit encoding."""
        ...

    def write_text_atomic(
        self,
        path: Path,
        content: str,
        *,
        encoding: str = "utf-8",
        overwrite: bool = False,
    ) -> None:
        """Write one text file through atomic publication."""
        ...


@runtime_checkable
class ProjectMigrationWorkspacePort(Protocol):
    """Provide the operations required by explicit project migration."""

    def inspect_source(
        self,
        source_root: Path,
    ) -> object:
        """Inspect the legacy source tree without modifying it."""
        ...

    def inspect_destination(
        self,
        *,
        project_root: Path,
        migration_id: str,
        project_id: object,
        language_code: str,
        source_directory: Path,
        source_root: Path,
        strategy: object,
    ) -> object:
        """Inspect whether the destination already matches the request."""
        ...

    def is_cancelled(self) -> bool:
        """Return whether migration cancellation was requested."""
        ...

    def apply(
        self,
        plan: object,
    ) -> object:
        """Apply an approved migration plan."""
        ...

    def verify(
        self,
        plan: object,
    ) -> object:
        """Verify the published destination against the plan."""
        ...

    def rollback(
        self,
        receipt: object,
    ) -> str | None:
        """Attempt rollback and return a bounded warning on incomplete recovery."""
        ...


@runtime_checkable
class ProjectTemplateSource(Protocol):
    """Read-only source of the reusable blank active-project structure."""

    @property
    def root(self) -> Path:
        """Return the canonical template root."""
        ...

    def inventory(self) -> tuple[TreeEntry, ...]:
        """Return the deterministic template inventory."""
        ...

    def materialize(
        self,
        destination: Path,
        *,
        replacements: Mapping[str, str],
    ) -> None:
        """Create a staged template instance without changing the template."""
        ...


@runtime_checkable
class ProjectArchiveWriter(Protocol):
    """Create and verify evidence before destructive replacement."""

    def create_verified_archive(
        self,
        source: Path,
        destination: Path,
        *,
        format: ArchiveFormat,
        excluded_roots: Sequence[Path] = (),
        preserved_links: Sequence[Path] = (),
    ) -> ArchiveReceipt:
        """Create an archive and return only after verification."""
        ...

    def verify(
        self,
        receipt: ArchiveReceipt,
    ) -> ArchiveReceipt:
        """Reopen and revalidate an existing archive receipt."""
        ...


@runtime_checkable
class LifecycleLease(Protocol):
    """Held lifecycle-writer lease returned by the lock adapter."""

    @property
    def path(self) -> Path:
        """Return the lifecycle-lock evidence path."""
        ...

    @property
    def request(self) -> LifecycleLockRequest:
        """Return the request represented by this lease."""
        ...


@runtime_checkable
class ProjectLifecycleLock(Protocol):
    """Coordinate one project-changing lifecycle writer per workspace."""

    def acquire(
        self,
        request: LifecycleLockRequest,
    ) -> AbstractContextManager[LifecycleLease]:
        """Acquire the lock or fail explicitly and release it on exit."""
        ...


def _validate_required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
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
        raise ValueError(f"{field_name} must not contain NUL characters")

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
        raise ValueError(f"{field_name} must identify a tree entry")
    if ".." in path.parts:
        raise ValueError(f"{field_name} must not contain parent traversal")

    return path


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
