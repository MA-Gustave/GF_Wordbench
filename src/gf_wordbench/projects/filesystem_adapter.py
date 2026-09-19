"""Filesystem adapter for safe project lifecycle operations."""

from __future__ import annotations

import codecs
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
from typing import TYPE_CHECKING, Final

from gf_wordbench.infrastructure.atomic_io import atomic_write_text

from .ports import TreeEntry, TreeEntryKind

if TYPE_CHECKING:
    from .ports import ProjectFilesystem


_HASH_CHUNK_SIZE: Final[int] = 1024 * 1024


@dataclass(frozen=True, slots=True)
class _TreeFingerprint:
    """Private content fingerprint used to verify tree copies."""

    relative_path: Path
    kind: TreeEntryKind
    size_bytes: int | None
    link_target: Path | None = None
    sha256: str | None = None


class ProjectFilesystemAdapter:
    """Concrete, non-shell implementation of the project filesystem port."""

    def resolve(self, path: Path) -> Path:
        """Return a normalized absolute path after resolving existing links."""

        return _absolute_path(path).resolve(strict=False)

    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
        allow_root: bool = False,
    ) -> Path:
        """Resolve *path* and require it to remain within resolved *root*."""

        if not isinstance(allow_root, bool):
            raise TypeError("allow_root must be a bool")

        resolved_root = self.resolve(root)
        resolved_path = self.resolve(path)

        if _same_path(resolved_path, resolved_root):
            if allow_root:
                return resolved_path
            raise ValueError("path must identify an entry below root")

        if not _within(resolved_path, resolved_root):
            raise ValueError(f"path escapes the permitted root: {resolved_path!s}")

        return resolved_path

    def exists(self, path: Path) -> bool:
        """Return whether an entry exists, including a broken link."""

        return os.path.lexists(_absolute_path(path))

    def is_file(self, path: Path) -> bool:
        """Return whether *path* is a regular file and not a link."""

        checked = _absolute_path(path)

        try:
            metadata = os.lstat(checked)
        except FileNotFoundError:
            return False

        return stat.S_ISREG(metadata.st_mode) and not _is_link(checked)

    def is_directory(self, path: Path) -> bool:
        """Return whether *path* is a directory and not a link or junction."""

        checked = _absolute_path(path)

        try:
            metadata = os.lstat(checked)
        except FileNotFoundError:
            return False

        return stat.S_ISDIR(metadata.st_mode) and not _is_link(checked)

    def inspect_tree(self, root: Path) -> tuple[TreeEntry, ...]:
        """Return deterministic tree metadata without following links."""

        fingerprints = _scan_tree(
            _directory(root),
            include_hashes=False,
        )

        return tuple(
            TreeEntry(
                relative_path=entry.relative_path,
                kind=entry.kind,
                size_bytes=entry.size_bytes,
                link_target=entry.link_target,
            )
            for entry in fingerprints
        )

    def create_empty_directory(self, path: Path) -> None:
        """Create one empty directory and fail if it already exists."""

        destination = _absolute_path(path)
        _directory(destination.parent)
        destination.mkdir()

    def copy_tree(
        self,
        source: Path,
        destination: Path,
        *,
        preserved_links: Sequence[Path] = (),
    ) -> None:
        """Copy and verify a tree, preserving only approved links."""

        source_root = _directory(source)
        destination_root = _absolute_path(destination)

        _directory(destination_root.parent)
        _require_absent(destination_root)
        _reject_overlap(source_root, destination_root)

        approved_links = _relative_path_set(
            preserved_links,
            field="preserved_links",
        )
        expected = _scan_tree(source_root, include_hashes=True)

        actual_links = {
            entry.relative_path for entry in expected if entry.kind is TreeEntryKind.SYMLINK
        }
        unsupported = tuple(
            entry.relative_path for entry in expected if entry.kind is TreeEntryKind.OTHER
        )

        if unsupported:
            paths = ", ".join(path.as_posix() for path in unsupported)
            raise OSError(f"unsupported filesystem entries: {paths}")

        unapproved_links = actual_links - approved_links
        if unapproved_links:
            paths = ", ".join(path.as_posix() for path in _sorted_relative_paths(unapproved_links))
            raise OSError(f"unapproved links in source tree: {paths}")

        missing_links = approved_links - actual_links
        if missing_links:
            paths = ", ".join(path.as_posix() for path in _sorted_relative_paths(missing_links))
            raise ValueError(f"approved links not found in source tree: {paths}")

        try:
            shutil.copytree(
                source_root,
                destination_root,
                symlinks=True,
                copy_function=shutil.copy2,
            )

            observed = _scan_tree(
                destination_root,
                include_hashes=True,
            )
            if observed != expected:
                raise OSError("copied tree does not match its source")
        except BaseException:
            if os.path.lexists(destination_root):
                _remove_entry(destination_root)
            raise

    def atomic_replace_directory(
        self,
        *,
        staged: Path,
        active: Path,
        rollback: Path,
    ) -> None:
        """Publish a staged directory and retain the previous active tree."""

        staged_path = _directory(staged)
        active_path = _absolute_path(active)
        rollback_path = _absolute_path(rollback)

        _directory(active_path.parent)
        _directory(rollback_path.parent)
        _require_absent(rollback_path)
        _reject_pairwise_overlap(
            staged_path,
            active_path,
            rollback_path,
        )

        if not _same_filesystem(
            staged_path,
            active_path.parent,
        ):
            raise OSError("staged and active paths must be on the same filesystem")

        if not _same_filesystem(
            active_path.parent,
            rollback_path.parent,
        ):
            raise OSError("active and rollback paths must be on the same filesystem")

        active_existed = os.path.lexists(active_path)

        if active_existed:
            _directory(active_path)
            os.replace(active_path, rollback_path)

        try:
            os.replace(staged_path, active_path)
        except BaseException as publication_error:
            if (
                active_existed
                and os.path.lexists(rollback_path)
                and not os.path.lexists(active_path)
            ):
                try:
                    os.replace(rollback_path, active_path)
                except BaseException as restoration_error:
                    publication_error.add_note(
                        "automatic restoration of the previous active "
                        "directory also failed: "
                        f"{restoration_error!r}"
                    )
            raise

    def restore_directory(
        self,
        *,
        rollback: Path,
        active: Path,
    ) -> None:
        """Restore a retained rollback directory as the active project."""

        rollback_path = _directory(rollback)
        active_path = _absolute_path(active)

        _directory(active_path.parent)
        _reject_overlap(rollback_path, active_path)

        if not _same_filesystem(
            rollback_path,
            active_path.parent,
        ):
            raise OSError("rollback and active paths must be on the same filesystem")

        if os.path.lexists(active_path):
            _directory(active_path)
            _remove_entry(active_path)

        os.replace(rollback_path, active_path)

    def remove_tree(self, path: Path) -> None:
        """Remove exactly one validated directory tree."""

        _remove_entry(_directory(path))

    def read_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        """Read one regular text file without following a link."""

        return _regular_file(path).read_text(encoding=_encoding(encoding))

    def write_text_atomic(
        self,
        path: Path,
        content: str,
        *,
        encoding: str = "utf-8",
        overwrite: bool = False,
    ) -> None:
        """Atomically publish text to one regular project-owned file."""

        destination = _absolute_path(path)

        if not isinstance(content, str):
            raise TypeError("content must be a string")
        if "\x00" in content:
            raise ValueError("content must not contain NUL characters")
        if not isinstance(overwrite, bool):
            raise TypeError("overwrite must be a bool")

        selected_encoding = _encoding(encoding)
        _directory(destination.parent)

        if os.path.lexists(destination):
            if not overwrite:
                raise FileExistsError(os.fspath(destination))
            if _is_link(destination):
                raise OSError(f"atomic-write destination must not be a link: {destination}")
            if destination.is_dir():
                raise IsADirectoryError(os.fspath(destination))

        atomic_write_text(
            destination,
            content,
            encoding=selected_encoding,
            newline="\n",
        )


def _scan_tree(
    root: Path,
    *,
    include_hashes: bool,
) -> tuple[_TreeFingerprint, ...]:
    output: list[_TreeFingerprint] = []

    _scan_directory(
        root,
        root,
        include_hashes=include_hashes,
        output=output,
    )
    output.sort(key=lambda entry: _relative_sort_key(entry.relative_path))
    return tuple(output)


def _scan_directory(
    root: Path,
    directory: Path,
    *,
    include_hashes: bool,
    output: list[_TreeFingerprint],
) -> None:
    with os.scandir(directory) as scan:
        children = sorted(
            scan,
            key=lambda entry: _name_sort_key(entry.name),
        )

    for child in children:
        path = Path(child.path)
        relative_path = Path(path.relative_to(root).as_posix())
        metadata = os.lstat(path)

        if _is_link(path):
            output.append(
                _TreeFingerprint(
                    relative_path=relative_path,
                    kind=TreeEntryKind.SYMLINK,
                    size_bytes=metadata.st_size,
                    link_target=Path(os.readlink(path)),
                )
            )
            continue

        if stat.S_ISDIR(metadata.st_mode):
            output.append(
                _TreeFingerprint(
                    relative_path=relative_path,
                    kind=TreeEntryKind.DIRECTORY,
                    size_bytes=None,
                )
            )
            _scan_directory(
                root,
                path,
                include_hashes=include_hashes,
                output=output,
            )
            continue

        if stat.S_ISREG(metadata.st_mode):
            output.append(
                _TreeFingerprint(
                    relative_path=relative_path,
                    kind=TreeEntryKind.FILE,
                    size_bytes=metadata.st_size,
                    sha256=(_sha256(path) if include_hashes else None),
                )
            )
            continue

        output.append(
            _TreeFingerprint(
                relative_path=relative_path,
                kind=TreeEntryKind.OTHER,
                size_bytes=metadata.st_size,
            )
        )


def _absolute_path(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")

    text = os.fspath(path)
    if "\x00" in text:
        raise ValueError("path must not contain NUL characters")
    if not path.is_absolute():
        raise ValueError(f"path must be absolute: {path}")

    return Path(os.path.normpath(text))


def _directory(path: Path) -> Path:
    checked = _absolute_path(path)

    try:
        metadata = os.lstat(checked)
    except FileNotFoundError:
        raise FileNotFoundError(os.fspath(checked)) from None

    if _is_link(checked) or not stat.S_ISDIR(metadata.st_mode):
        raise NotADirectoryError(os.fspath(checked))

    return checked


def _regular_file(path: Path) -> Path:
    checked = _absolute_path(path)

    try:
        metadata = os.lstat(checked)
    except FileNotFoundError:
        raise FileNotFoundError(os.fspath(checked)) from None

    if _is_link(checked) or not stat.S_ISREG(metadata.st_mode):
        raise OSError(f"path is not a regular file: {checked}")

    return checked


def _encoding(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError("encoding must be a non-empty string")

    return codecs.lookup(value).name


def _relative_path_set(
    values: Sequence[Path],
    *,
    field: str,
) -> set[Path]:
    raw_values: object = values
    if isinstance(raw_values, (str, bytes)) or not isinstance(
        raw_values,
        Sequence,
    ):
        raise TypeError(f"{field} must be a sequence of pathlib.Path values")

    output: set[Path] = set()

    for index, value in enumerate(values):
        relative = _relative_path(
            value,
            field=f"{field}[{index}]",
        )

        if relative in output:
            raise ValueError(f"{field} contains duplicate path {relative.as_posix()!r}")

        output.add(relative)

    return output


def _relative_path(
    value: Path,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")

    text = value.as_posix()
    windows_path = PureWindowsPath(text)
    posix_path = PurePosixPath(text)

    if (
        not text
        or text == "."
        or "\x00" in text
        or "\\" in os.fspath(value)
        or value.is_absolute()
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or ".." in posix_path.parts
        or posix_path.as_posix() != text
    ):
        raise ValueError(f"{field} must be a canonical contained relative path")

    return Path(text)


def _require_absent(path: Path) -> None:
    if os.path.lexists(path):
        raise FileExistsError(os.fspath(path))


def _remove_entry(path: Path) -> None:
    if _is_link(path):
        try:
            path.unlink()
        except IsADirectoryError:
            os.rmdir(path)
        return

    metadata = os.lstat(path)

    if stat.S_ISDIR(metadata.st_mode):
        shutil.rmtree(
            path,
            onerror=_retry_readonly,
        )
        return

    try:
        path.unlink()
    except PermissionError:
        os.chmod(path, stat.S_IWRITE)
        path.unlink()


def _retry_readonly(
    function: Callable[[str], object],
    path: str,
    error_info: object,
) -> None:
    del error_info

    os.chmod(path, stat.S_IWRITE)
    function(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while chunk := stream.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True

    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _same_filesystem(
    left: Path,
    right: Path,
) -> bool:
    left_device = os.stat(_nearest_existing(left)).st_dev
    right_device = os.stat(_nearest_existing(right)).st_dev

    return left_device == right_device


def _nearest_existing(path: Path) -> Path:
    current = _absolute_path(path)

    while not os.path.lexists(current):
        if current.parent == current:
            raise FileNotFoundError(os.fspath(path))
        current = current.parent

    return current


def _reject_pairwise_overlap(
    *paths: Path,
) -> None:
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            _reject_overlap(left, right)


def _reject_overlap(
    source: Path,
    destination: Path,
) -> None:
    if _same_path(source, destination):
        raise ValueError("paths must be distinct")

    if _within(destination, source) or _within(source, destination):
        raise ValueError("lifecycle paths must not contain one another")


def _within(
    candidate: Path,
    root: Path,
) -> bool:
    try:
        common = os.path.commonpath((candidate, root))
    except ValueError:
        return False

    return _path_key(Path(common)) == _path_key(root)


def _same_path(
    left: Path,
    right: Path,
) -> bool:
    return _path_key(left) == _path_key(right)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _name_sort_key(
    value: str,
) -> tuple[str, str]:
    return (
        os.path.normcase(value),
        value,
    )


def _relative_sort_key(
    value: Path,
) -> tuple[str, str]:
    text = value.as_posix()
    return (
        os.path.normcase(text),
        text,
    )


def _sorted_relative_paths(
    values: set[Path],
) -> tuple[Path, ...]:
    return tuple(
        sorted(
            values,
            key=_relative_sort_key,
        )
    )


if TYPE_CHECKING:
    _project_filesystem_port: ProjectFilesystem = ProjectFilesystemAdapter()


__all__ = ("ProjectFilesystemAdapter",)
