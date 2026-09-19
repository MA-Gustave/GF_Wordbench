"""Generic, explicit filesystem primitives used by GF Wordbench adapters."""

from __future__ import annotations

import errno
import os
from pathlib import Path
import shutil
from typing import BinaryIO, Final, TypeAlias

PathInput: TypeAlias = str | os.PathLike[str]

UTF8: Final = "utf-8"
_COPY_BUFFER_SIZE: Final = 1024 * 1024


class PathContainmentError(PermissionError):
    """Raised when a resolved filesystem target escapes its required root."""

    def __init__(
        self,
        candidate: Path,
        root: Path,
        *,
        role: str,
        stage: str,
    ) -> None:
        self.candidate = candidate
        self.root = root
        self.role = role
        self.stage = stage
        super().__init__(
            errno.EPERM,
            (
                f"{role} escapes its required root during {stage}: "
                f"candidate={candidate!s}, root={root!s}"
            ),
            os.fspath(candidate),
        )


def resolve_existing(path: PathInput) -> Path:
    """Return the strict, absolute resolution of an existing path."""

    candidate = _absolute_path(path)
    try:
        return candidate.resolve(strict=True)
    except RuntimeError as exc:
        raise OSError(
            errno.ELOOP,
            "filesystem path contains a symbolic-link loop",
            os.fspath(candidate),
        ) from exc


def resolve_for_output(path: PathInput) -> Path:
    """Resolve the nearest existing ancestor of a prospective output path.

    The returned path is absolute. Existing ancestors, including symlinks and
    junctions, are resolved strictly; missing final components are appended
    without requiring their existence.
    """

    candidate = _absolute_path(path)
    ancestor, missing = _nearest_existing_ancestor(candidate)
    resolved = resolve_existing(ancestor)
    return resolved.joinpath(*reversed(missing))


def is_within(
    candidate: PathInput,
    root: PathInput,
    *,
    allow_equal: bool = True,
    for_output: bool = False,
) -> bool:
    """Return whether the resolved candidate is contained by the resolved root."""

    resolved_root = resolve_existing(root)
    resolved_candidate = (
        resolve_for_output(candidate) if for_output else resolve_existing(candidate)
    )
    if not allow_equal and resolved_candidate == resolved_root:
        return False
    return _is_relative_to(resolved_candidate, resolved_root)


def require_within(
    candidate: PathInput,
    root: PathInput,
    *,
    role: str = "path",
    stage: str = "resolved containment",
    allow_equal: bool = True,
    for_output: bool = False,
) -> Path:
    """Resolve and return a candidate, raising when it escapes *root*."""

    resolved_root = resolve_existing(root)
    resolved_candidate = (
        resolve_for_output(candidate) if for_output else resolve_existing(candidate)
    )
    contained = _is_relative_to(resolved_candidate, resolved_root)
    if (not contained) or (not allow_equal and resolved_candidate == resolved_root):
        raise PathContainmentError(
            resolved_candidate,
            resolved_root,
            role=role,
            stage=stage,
        )
    return resolved_candidate


def require_regular_file(
    path: PathInput,
    *,
    root: PathInput | None = None,
    role: str = "file",
) -> Path:
    """Return an existing resolved regular file, optionally contained by *root*."""

    resolved = _resolve_existing_with_optional_root(path, root, role=role)
    if not resolved.is_file():
        raise IsADirectoryError(
            errno.EISDIR,
            f"{role} must be a regular file",
            os.fspath(resolved),
        )
    return resolved


def require_directory(
    path: PathInput,
    *,
    root: PathInput | None = None,
    role: str = "directory",
) -> Path:
    """Return an existing resolved directory, optionally contained by *root*."""

    resolved = _resolve_existing_with_optional_root(path, root, role=role)
    if not resolved.is_dir():
        raise NotADirectoryError(
            errno.ENOTDIR,
            f"{role} must be a directory",
            os.fspath(resolved),
        )
    return resolved


def read_bytes(
    path: PathInput,
    *,
    max_bytes: int | None = None,
    root: PathInput | None = None,
    role: str = "input file",
) -> bytes:
    """Read a regular file, optionally enforcing containment and a byte limit."""

    limit = _validated_limit(max_bytes)
    source = require_regular_file(path, root=root, role=role)
    with source.open("rb") as stream:
        if limit is None:
            return stream.read()
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise OSError(
            errno.EFBIG,
            f"{role} exceeds the configured {limit}-byte read limit",
            os.fspath(source),
        )
    return data


def read_text(
    path: PathInput,
    *,
    max_bytes: int | None = None,
    root: PathInput | None = None,
    role: str = "UTF-8 input file",
) -> str:
    """Read and strictly decode UTF-8 without newline transformation."""

    return read_bytes(path, max_bytes=max_bytes, root=root, role=role).decode(UTF8)


def write_bytes(
    path: PathInput,
    data: bytes | bytearray | memoryview,
    *,
    overwrite: bool = False,
    create_parents: bool = False,
    root: PathInput | None = None,
    role: str = "output file",
) -> Path:
    """Write bytes non-atomically with explicit collision and containment policy.

    Canonical persisted files that replace an existing target should use the
    dedicated atomic-I/O adapter instead.
    """

    payload = bytes(data)
    destination = _prepare_output_file(
        path,
        overwrite=overwrite,
        create_parents=create_parents,
        root=root,
        role=role,
    )
    with _open_output_binary(destination, overwrite=overwrite) as stream:
        stream.write(payload)
        stream.flush()
    return _verify_created_file(destination, root=root, role=role)


def write_text(
    path: PathInput,
    text: str,
    *,
    overwrite: bool = False,
    create_parents: bool = False,
    root: PathInput | None = None,
    role: str = "UTF-8 output file",
) -> Path:
    """Encode *text* as strict UTF-8 and write it without newline conversion."""

    if not isinstance(text, str):
        raise TypeError("text must be str")
    return write_bytes(
        path,
        text.encode(UTF8),
        overwrite=overwrite,
        create_parents=create_parents,
        root=root,
        role=role,
    )


def create_directory(
    path: PathInput,
    *,
    parents: bool = False,
    exist_ok: bool = False,
    root: PathInput | None = None,
    role: str = "output directory",
) -> Path:
    """Create a directory and verify its resolved containment after creation."""

    destination = _validated_output_path(path, root=root, role=role)
    destination.mkdir(parents=parents, exist_ok=exist_ok)
    resolved = require_directory(destination, role=role)
    if root is not None:
        return require_within(
            resolved,
            root,
            role=role,
            stage="post-creation containment",
        )
    return resolved


def create_directory_exclusive(
    path: PathInput,
    *,
    root: PathInput | None = None,
    role: str = "exclusive output directory",
) -> Path:
    """Create one new directory without reusing an existing target."""

    return create_directory(
        path,
        parents=False,
        exist_ok=False,
        root=root,
        role=role,
    )


def copy_file(
    source: PathInput,
    destination: PathInput,
    *,
    overwrite: bool = False,
    create_parents: bool = False,
    preserve_metadata: bool = False,
    source_root: PathInput | None = None,
    destination_root: PathInput | None = None,
    role: str = "copied file",
) -> Path:
    """Copy one regular file through explicit source and destination policies."""

    resolved_source = require_regular_file(
        source,
        root=source_root,
        role=f"{role} source",
    )
    resolved_destination = _prepare_output_file(
        destination,
        overwrite=overwrite,
        create_parents=create_parents,
        root=destination_root,
        role=f"{role} destination",
    )

    if _same_existing_file(resolved_source, resolved_destination):
        raise shutil.SameFileError(resolved_source, resolved_destination)

    with resolved_source.open("rb") as source_stream, _open_output_binary(
        resolved_destination,
        overwrite=overwrite,
    ) as destination_stream:
        shutil.copyfileobj(
            source_stream,
            destination_stream,
            length=_COPY_BUFFER_SIZE,
        )
        destination_stream.flush()

    if preserve_metadata:
        shutil.copystat(resolved_source, resolved_destination, follow_symlinks=False)

    return _verify_created_file(
        resolved_destination,
        root=destination_root,
        role=f"{role} destination",
    )


def unlink_file(
    path: PathInput,
    *,
    missing_ok: bool = False,
    root: PathInput | None = None,
    role: str = "file",
) -> None:
    """Remove one file or link without recursive deletion."""

    candidate = _absolute_path(path)
    if not os.path.lexists(candidate):
        if missing_ok:
            return
        raise FileNotFoundError(
            errno.ENOENT,
            f"{role} does not exist",
            os.fspath(candidate),
        )

    resolved_for_policy = resolve_for_output(candidate)
    if root is not None:
        require_within(
            resolved_for_policy,
            root,
            role=role,
            stage="pre-removal containment",
            for_output=True,
        )

    if candidate.is_dir() and not candidate.is_symlink():
        raise IsADirectoryError(
            errno.EISDIR,
            f"{role} is a directory",
            os.fspath(candidate),
        )
    candidate.unlink(missing_ok=missing_ok)


def remove_empty_directory(
    path: PathInput,
    *,
    root: PathInput | None = None,
    role: str = "directory",
) -> None:
    """Remove one empty directory; recursive deletion is intentionally absent."""

    candidate = _absolute_path(path)
    if _is_link_like(candidate):
        raise OSError(
            errno.ELOOP,
            f"refusing to remove {role} through a symbolic link or junction",
            os.fspath(candidate),
        )
    resolved = require_directory(candidate, root=root, role=role)
    resolved.rmdir()


def iter_directory(path: PathInput, *, root: PathInput | None = None) -> tuple[Path, ...]:
    """Return a stable name-ordered snapshot of one directory."""

    directory = require_directory(path, root=root)
    return tuple(sorted(directory.iterdir(), key=lambda item: item.name))


def _prepare_output_file(
    path: PathInput,
    *,
    overwrite: bool,
    create_parents: bool,
    root: PathInput | None,
    role: str,
) -> Path:
    destination = _absolute_path(path)
    parent = destination.parent
    if create_parents:
        create_directory(
            parent,
            parents=True,
            exist_ok=True,
            root=root,
            role=f"{role} parent",
        )
    else:
        require_directory(parent, root=root, role=f"{role} parent")

    if _is_link_like(destination):
        raise OSError(
            errno.ELOOP,
            f"refusing to write {role} through a symbolic link or junction",
            os.fspath(destination),
        )

    resolved = _validated_output_path(destination, root=root, role=role)
    if os.path.lexists(resolved):
        if resolved.is_dir():
            raise IsADirectoryError(
                errno.EISDIR,
                f"{role} points to a directory",
                os.fspath(resolved),
            )
        if not overwrite:
            raise FileExistsError(
                errno.EEXIST,
                f"{role} already exists",
                os.fspath(resolved),
            )
    return resolved


def _validated_output_path(
    path: PathInput,
    *,
    root: PathInput | None,
    role: str,
) -> Path:
    resolved = resolve_for_output(path)
    if root is None:
        return resolved
    return require_within(
        resolved,
        root,
        role=role,
        stage="pre-write containment",
        for_output=True,
    )


def _verify_created_file(
    path: Path,
    *,
    root: PathInput | None,
    role: str,
) -> Path:
    resolved = require_regular_file(path, role=role)
    if root is not None:
        return require_within(
            resolved,
            root,
            role=role,
            stage="post-write containment",
        )
    return resolved


def _resolve_existing_with_optional_root(
    path: PathInput,
    root: PathInput | None,
    *,
    role: str,
) -> Path:
    if root is None:
        return resolve_existing(path)
    return require_within(path, root, role=role)


def _nearest_existing_ancestor(path: Path) -> tuple[Path, tuple[str, ...]]:
    current = path
    missing: list[str] = []
    while not os.path.lexists(current):
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(
                errno.ENOENT,
                "no existing ancestor is available for the output path",
                os.fspath(path),
            )
        missing.append(current.name)
        current = parent
    return current, tuple(missing)


def _absolute_path(path: PathInput) -> Path:
    raw = os.fspath(path)
    raw_value: object = raw
    if isinstance(raw_value, bytes):
        raise TypeError("filesystem paths must be text, not bytes")
    if "\x00" in raw:
        raise ValueError("filesystem path contains NUL")
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise ValueError(f"filesystem path must be absolute: {raw!r}")
    return Path(os.path.abspath(candidate))


def _validated_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_bytes must be an integer or None")
    if value < 0:
        raise ValueError("max_bytes must be non-negative")
    return value


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _open_output_binary(path: Path, *, overwrite: bool) -> BinaryIO:
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o666)
    return os.fdopen(descriptor, "wb")


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def _same_existing_file(source: Path, destination: Path) -> bool:
    if not os.path.lexists(destination):
        return False
    try:
        return os.path.samefile(source, destination)
    except OSError:
        return False


__all__ = [
    "UTF8",
    "PathContainmentError",
    "PathInput",
    "copy_file",
    "create_directory",
    "create_directory_exclusive",
    "is_within",
    "iter_directory",
    "read_bytes",
    "read_text",
    "remove_empty_directory",
    "require_directory",
    "require_regular_file",
    "require_within",
    "resolve_existing",
    "resolve_for_output",
    "unlink_file",
    "write_bytes",
    "write_text",
]
