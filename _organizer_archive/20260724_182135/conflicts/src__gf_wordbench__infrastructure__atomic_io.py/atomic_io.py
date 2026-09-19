"""Atomic replacement primitives for persistent GF Wordbench files.

Serialization and schema validation remain the responsibility of the owning
module. This module only manages sibling temporary files, flushing, optional
validation, replacement, permission preservation, and cleanup.
"""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import secrets
import stat
from typing import BinaryIO, Final, TypeAlias

PathLike: TypeAlias = str | os.PathLike[str]
BinaryWriter: TypeAlias = Callable[[BinaryIO], None]
TemporaryValidator: TypeAlias = Callable[[Path], None]

_TEMPORARY_TOKEN_BYTES: Final[int] = 8
_MAX_TEMPORARY_NAME_ATTEMPTS: Final[int] = 32
_DEFAULT_CREATE_MODE: Final[int] = 0o666


def atomic_write(
    destination: PathLike,
    writer: BinaryWriter,
    *,
    validator: TemporaryValidator | None = None,
    create_parent: bool = False,
    sync: bool = True,
    cleanup_on_error: bool = True,
    preserve_destination_mode: bool = True,
    file_mode: int | None = None,
) -> Path:
    """Write and atomically replace *destination* using a sibling temporary file.

    The writer receives an open binary stream and must not close it. When
    supplied, ``validator`` runs after the temporary file has been flushed and
    closed, but before publication. Any exception leaves the previous
    destination untouched. Temporary-file retention after failure is selected
    explicitly with ``cleanup_on_error``.

    ``file_mode`` overrides destination-mode preservation. For a new file with
    no explicit mode, normal ``0o666`` creation filtered by the process umask is
    used.
    """

    target = _coerce_destination(destination)
    parent = target.parent

    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)

    if not parent.is_dir():
        raise NotADirectoryError(f"Atomic-write parent is not a directory: {parent}")
    if target.exists() and target.is_dir():
        raise IsADirectoryError(f"Atomic-write destination is a directory: {target}")

    requested_mode = _select_file_mode(
        target,
        preserve_destination_mode=preserve_destination_mode,
        file_mode=file_mode,
    )

    temporary: Path | None = None
    try:
        temporary, descriptor = _create_sibling_temporary(target)
        try:
            stream = os.fdopen(descriptor, "wb", closefd=True)
        except BaseException:
            os.close(descriptor)
            raise

        with stream:
            writer(stream)
            stream.flush()
            if sync:
                os.fsync(stream.fileno())

        if validator is not None:
            validator(temporary)

        if requested_mode is not None:
            os.chmod(temporary, requested_mode)

        os.replace(temporary, target)
        temporary = None
        return target
    except BaseException as exc:
        exc.add_note(f"Atomic-write destination: {target}")
        if temporary is not None:
            exc.add_note(f"Atomic-write temporary file: {temporary}")
            if cleanup_on_error:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    exc.add_note(
                        "Temporary-file cleanup failed: "
                        f"{cleanup_error.__class__.__name__}: {cleanup_error}"
                    )
        raise


def atomic_write_bytes(
    destination: PathLike,
    data: bytes | bytearray | memoryview,
    *,
    validator: TemporaryValidator | None = None,
    create_parent: bool = False,
    sync: bool = True,
    cleanup_on_error: bool = True,
    preserve_destination_mode: bool = True,
    file_mode: int | None = None,
) -> Path:
    """Atomically write bytes to *destination*."""

    payload = bytes(data)

    def write_payload(stream: BinaryIO) -> None:
        stream.write(payload)

    return atomic_write(
        destination,
        write_payload,
        validator=validator,
        create_parent=create_parent,
        sync=sync,
        cleanup_on_error=cleanup_on_error,
        preserve_destination_mode=preserve_destination_mode,
        file_mode=file_mode,
    )


def atomic_write_text(
    destination: PathLike,
    text: str,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    validator: TemporaryValidator | None = None,
    create_parent: bool = False,
    sync: bool = True,
    cleanup_on_error: bool = True,
    preserve_destination_mode: bool = True,
    file_mode: int | None = None,
) -> Path:
    """Atomically write text without platform newline translation or a BOM.

    Callers remain responsible for supplying canonical content, including the
    required final newline for human-readable reports.
    """

    return atomic_write_bytes(
        destination,
        text.encode(encoding, errors),
        validator=validator,
        create_parent=create_parent,
        sync=sync,
        cleanup_on_error=cleanup_on_error,
        preserve_destination_mode=preserve_destination_mode,
        file_mode=file_mode,
    )


def _coerce_destination(destination: PathLike) -> Path:
    target = Path(destination)
    if not target.name or target.name in {".", ".."}:
        raise ValueError(f"Invalid atomic-write destination: {target}")
    return target


def _select_file_mode(
    destination: Path,
    *,
    preserve_destination_mode: bool,
    file_mode: int | None,
) -> int | None:
    if file_mode is not None:
        if isinstance(file_mode, bool) or not isinstance(file_mode, int):
            raise TypeError("file_mode must be an integer permission mode")
        if file_mode < 0 or file_mode > 0o7777:
            raise ValueError("file_mode must be between 0o0000 and 0o7777")
        return file_mode

    if not preserve_destination_mode:
        return None

    try:
        destination_stat = destination.stat(follow_symlinks=False)
    except FileNotFoundError:
        return None

    if stat.S_ISREG(destination_stat.st_mode):
        return stat.S_IMODE(destination_stat.st_mode)
    return None


def _create_sibling_temporary(destination: Path) -> tuple[Path, int]:
    hidden_name = destination.name if destination.name.startswith(".") else f".{destination.name}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)

    last_collision: FileExistsError | None = None
    for _ in range(_MAX_TEMPORARY_NAME_ATTEMPTS):
        token = secrets.token_hex(_TEMPORARY_TOKEN_BYTES)
        temporary = destination.with_name(f"{hidden_name}.{token}.tmp")
        try:
            descriptor = os.open(temporary, flags, _DEFAULT_CREATE_MODE)
        except FileExistsError as exc:
            last_collision = exc
            continue
        return temporary, descriptor

    raise FileExistsError(
        f"Could not allocate a collision-safe sibling temporary file for {destination}"
    ) from last_collision


__all__ = (
    "BinaryWriter",
    "PathLike",
    "TemporaryValidator",
    "atomic_write",
    "atomic_write_bytes",
    "atomic_write_text",
)
