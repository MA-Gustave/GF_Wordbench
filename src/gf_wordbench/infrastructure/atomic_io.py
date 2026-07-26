"""Atomic sibling-file writes for GF Wordbench-owned persistent files."""

from __future__ import annotations

import errno
import math
import os
import stat
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, TextIO, TypeAlias, TypeVar

from .filesystem import require_directory, require_within, resolve_for_output

__all__ = [
    "AtomicPathValidator",
    "atomic_binary_writer",
    "atomic_text_writer",
    "atomic_write_bytes",
    "atomic_write_text",
]

AtomicPathValidator: TypeAlias = Callable[[Path], None]

_PathLike: TypeAlias = str | os.PathLike[str]
_StreamT = TypeVar("_StreamT", BinaryIO, TextIO)

_RETRYABLE_ERRNOS = frozenset(
    value
    for value in (errno.EACCES, errno.EBUSY, errno.EPERM)
    if value is not None
)
_RETRYABLE_WINDOWS_ERRORS = frozenset({5, 32, 33})


@contextmanager
def atomic_binary_writer(
    destination: _PathLike,
    *,
    create_parents: bool = False,
    root: _PathLike | None = None,
    role: str = "binary output file",
    validator: AtomicPathValidator | None = None,
    sync: bool = True,
    preserve_existing_mode: bool = True,
    file_mode: int | None = None,
    replace_retry_delays: Sequence[float] = (),
    keep_temporary_on_failure: bool = False,
) -> Iterator[BinaryIO]:
    """Yield a binary sibling temporary file and atomically publish it on success."""

    destination_path = _prepare_destination(
        destination,
        create_parents=create_parents,
        root=root,
        role=role,
    )

    def open_stream(file_descriptor: int) -> BinaryIO:
        return os.fdopen(file_descriptor, "wb")

    with _atomic_writer(
        destination_path,
        open_stream=open_stream,
        root=root,
        role=role,
        validator=validator,
        sync=sync,
        preserve_existing_mode=preserve_existing_mode,
        file_mode=file_mode,
        replace_retry_delays=replace_retry_delays,
        keep_temporary_on_failure=keep_temporary_on_failure,
    ) as stream:
        yield stream


@contextmanager
def atomic_text_writer(
    destination: _PathLike,
    *,
    encoding: str = "utf-8",
    newline: str | None = "\n",
    create_parents: bool = False,
    root: _PathLike | None = None,
    role: str = "text output file",
    validator: AtomicPathValidator | None = None,
    sync: bool = True,
    preserve_existing_mode: bool = True,
    file_mode: int | None = None,
    replace_retry_delays: Sequence[float] = (),
    keep_temporary_on_failure: bool = False,
) -> Iterator[TextIO]:
    """Yield a text sibling temporary file and atomically publish it on success."""

    _validate_text_options(encoding=encoding, newline=newline)
    destination_path = _prepare_destination(
        destination,
        create_parents=create_parents,
        root=root,
        role=role,
    )

    def open_stream(file_descriptor: int) -> TextIO:
        return os.fdopen(
            file_descriptor,
            "w",
            encoding=encoding,
            errors="strict",
            newline=newline,
        )

    with _atomic_writer(
        destination_path,
        open_stream=open_stream,
        root=root,
        role=role,
        validator=validator,
        sync=sync,
        preserve_existing_mode=preserve_existing_mode,
        file_mode=file_mode,
        replace_retry_delays=replace_retry_delays,
        keep_temporary_on_failure=keep_temporary_on_failure,
    ) as stream:
        yield stream


def atomic_write_bytes(
    destination: _PathLike,
    data: bytes | bytearray | memoryview,
    *,
    create_parents: bool = False,
    root: _PathLike | None = None,
    role: str = "binary output file",
    validator: AtomicPathValidator | None = None,
    sync: bool = True,
    preserve_existing_mode: bool = True,
    file_mode: int | None = None,
    replace_retry_delays: Sequence[float] = (),
    keep_temporary_on_failure: bool = False,
) -> Path:
    """Write bytes through atomic sibling replacement."""

    with atomic_binary_writer(
        destination,
        create_parents=create_parents,
        root=root,
        role=role,
        validator=validator,
        sync=sync,
        preserve_existing_mode=preserve_existing_mode,
        file_mode=file_mode,
        replace_retry_delays=replace_retry_delays,
        keep_temporary_on_failure=keep_temporary_on_failure,
    ) as stream:
        stream.write(bytes(data))

    return _absolute_destination_path(destination)


def atomic_write_text(
    destination: _PathLike,
    text: str,
    *,
    encoding: str = "utf-8",
    newline: str | None = "\n",
    create_parents: bool = False,
    root: _PathLike | None = None,
    role: str = "text output file",
    validator: AtomicPathValidator | None = None,
    sync: bool = True,
    preserve_existing_mode: bool = True,
    file_mode: int | None = None,
    replace_retry_delays: Sequence[float] = (),
    keep_temporary_on_failure: bool = False,
) -> Path:
    """Write text through atomic sibling replacement."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    with atomic_text_writer(
        destination,
        encoding=encoding,
        newline=newline,
        create_parents=create_parents,
        root=root,
        role=role,
        validator=validator,
        sync=sync,
        preserve_existing_mode=preserve_existing_mode,
        file_mode=file_mode,
        replace_retry_delays=replace_retry_delays,
        keep_temporary_on_failure=keep_temporary_on_failure,
    ) as stream:
        stream.write(text)

    return _absolute_destination_path(destination)


@contextmanager
def _atomic_writer(
    destination_path: Path,
    *,
    open_stream: Callable[[int], _StreamT],
    root: _PathLike | None,
    role: str,
    validator: AtomicPathValidator | None,
    sync: bool,
    preserve_existing_mode: bool,
    file_mode: int | None,
    replace_retry_delays: Sequence[float],
    keep_temporary_on_failure: bool,
) -> Iterator[_StreamT]:
    role = _validated_role(role)
    validator = _validated_validator(validator)
    retry_delays = _validated_retry_delays(replace_retry_delays)
    requested_mode = _validated_file_mode(file_mode)
    existing_mode = _existing_regular_file_mode(destination_path)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=destination_path.parent,
    )
    temporary_path = Path(temporary_name)
    stream: _StreamT | None = None
    committed = False

    try:
        effective_mode = requested_mode
        if effective_mode is None and preserve_existing_mode:
            effective_mode = existing_mode
        if effective_mode is not None:
            os.chmod(temporary_path, effective_mode)

        stream = open_stream(file_descriptor)
        file_descriptor = -1

        yield stream

        _flush_close_and_sync(stream, sync=sync)

        if validator is not None:
            validator(temporary_path)

        _validate_temporary_path(
            temporary_path,
            destination_path=destination_path,
            root=root,
            role=role,
        )
        _revalidate_destination(
            destination_path,
            root=root,
            role=role,
        )
        _replace_with_retry(
            temporary_path,
            destination_path,
            retry_delays=retry_delays,
        )
        committed = True
    except BaseException as error:
        _close_quietly(stream)
        _close_descriptor_quietly(file_descriptor)

        if not keep_temporary_on_failure:
            _unlink_quietly(temporary_path)

        _add_failure_context(
            error,
            destination_path,
            temporary_path,
        )
        raise
    finally:
        _close_quietly(stream)
        _close_descriptor_quietly(file_descriptor)

        if committed or not keep_temporary_on_failure:
            _unlink_quietly(temporary_path)


def _prepare_destination(
    destination: _PathLike,
    *,
    create_parents: bool,
    root: _PathLike | None,
    role: str,
) -> Path:
    role = _validated_role(role)

    if not isinstance(create_parents, bool):
        raise TypeError("create_parents must be a boolean")

    lexical_path = _absolute_destination_path(destination)
    _reject_link_like(lexical_path, role=role)

    destination_path = resolve_for_output(lexical_path)

    if root is not None:
        destination_path = require_within(
            destination_path,
            root,
            role=role,
            stage="pre-write containment",
            for_output=True,
        )

    parent = destination_path.parent
    if create_parents:
        parent.mkdir(parents=True, exist_ok=True)

    parent = require_directory(
        parent,
        root=root,
        role=f"{role} parent",
    )
    destination_path = parent / destination_path.name

    _validate_destination_entry(
        destination_path,
        role=role,
    )

    if root is not None:
        destination_path = require_within(
            destination_path,
            root,
            role=role,
            stage="post-parent-creation containment",
            for_output=True,
        )

    return destination_path


def _revalidate_destination(
    destination_path: Path,
    *,
    root: _PathLike | None,
    role: str,
) -> None:
    _validate_destination_entry(
        destination_path,
        role=role,
    )

    if root is not None:
        require_within(
            destination_path,
            root,
            role=role,
            stage="pre-replacement containment",
            for_output=True,
        )


def _validate_temporary_path(
    temporary_path: Path,
    *,
    destination_path: Path,
    root: _PathLike | None,
    role: str,
) -> None:
    try:
        metadata = temporary_path.lstat()
    except FileNotFoundError:
        raise FileNotFoundError(
            errno.ENOENT,
            f"{role} temporary file disappeared before replacement",
            os.fspath(temporary_path),
        ) from None

    if not stat.S_ISREG(metadata.st_mode):
        raise OSError(
            errno.EINVAL,
            f"{role} temporary path must remain a regular file",
            os.fspath(temporary_path),
        )

    resolved_temporary = temporary_path.resolve(strict=True)
    resolved_parent = destination_path.parent.resolve(strict=True)

    if resolved_temporary.parent != resolved_parent:
        raise OSError(
            errno.EXDEV,
            f"{role} temporary file is no longer beside its destination",
            os.fspath(temporary_path),
        )

    if root is not None:
        require_within(
            resolved_temporary,
            root,
            role=f"{role} temporary file",
            stage="temporary-file containment",
        )


def _absolute_destination_path(destination: _PathLike) -> Path:
    raw = os.fspath(destination)

    if isinstance(raw, bytes):
        raise TypeError("destination paths must be text, not bytes")
    if "\x00" in raw:
        raise ValueError("destination path contains NUL")

    path = Path(raw)

    if not path.is_absolute():
        raise ValueError(f"destination path must be absolute: {raw!r}")
    if not path.name or path.name in {".", ".."}:
        raise ValueError("destination must name a file")

    return Path(os.path.abspath(path))


def _validate_destination_entry(
    path: Path,
    *,
    role: str,
) -> None:
    _reject_link_like(path, role=role)

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return

    if stat.S_ISDIR(metadata.st_mode):
        raise IsADirectoryError(
            errno.EISDIR,
            f"{role} is a directory",
            os.fspath(path),
        )

    if not stat.S_ISREG(metadata.st_mode):
        raise OSError(
            errno.EINVAL,
            f"{role} must be a regular file or an absent path",
            os.fspath(path),
        )


def _reject_link_like(
    path: Path,
    *,
    role: str,
) -> None:
    is_junction = getattr(path, "is_junction", None)
    is_link_like = path.is_symlink() or (
        is_junction is not None and is_junction()
    )

    if not is_link_like:
        return

    raise OSError(
        errno.ELOOP,
        f"refusing to replace {role} through a symbolic link or junction",
        os.fspath(path),
    )


def _validate_text_options(
    *,
    encoding: str,
    newline: str | None,
) -> None:
    if not isinstance(encoding, str):
        raise TypeError("encoding must be a string")
    if not encoding:
        raise ValueError("encoding cannot be empty")
    if "\x00" in encoding:
        raise ValueError("encoding cannot contain NUL")
    if newline not in {None, "", "\n", "\r", "\r\n"}:
        raise ValueError(
            "newline must be None, '', '\\n', '\\r', or '\\r\\n'"
        )


def _validated_role(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("role must be a string")
    if not value or value.isspace():
        raise ValueError("role cannot be empty")
    if "\x00" in value:
        raise ValueError("role cannot contain NUL")

    return value


def _validated_validator(
    value: AtomicPathValidator | None,
) -> AtomicPathValidator | None:
    if value is not None and not callable(value):
        raise TypeError("validator must be callable or None")

    return value


def _validated_retry_delays(
    values: Sequence[float],
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(
            "replace_retry_delays must be a sequence of numbers"
        )

    delays: list[float] = []

    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("replace retry delays must be numeric")

        delay = float(value)

        if not math.isfinite(delay) or delay < 0:
            raise ValueError(
                "replace retry delays must be finite and non-negative"
            )

        delays.append(delay)

    return tuple(delays)


def _validated_file_mode(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("file_mode must be an integer or None")
    if value < 0 or value > 0o7777:
        raise ValueError("file_mode must be between 0 and 0o7777")

    return value


def _existing_regular_file_mode(path: Path) -> int | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None

    if not stat.S_ISREG(metadata.st_mode):
        return None

    return stat.S_IMODE(metadata.st_mode)


def _flush_close_and_sync(
    stream: BinaryIO | TextIO,
    *,
    sync: bool,
) -> None:
    if stream.closed:
        raise ValueError("atomic writer stream was closed by the caller")

    stream.flush()

    if sync:
        os.fsync(stream.fileno())

    stream.close()


def _replace_with_retry(
    temporary_path: Path,
    destination_path: Path,
    *,
    retry_delays: tuple[float, ...],
) -> None:
    for attempt in range(len(retry_delays) + 1):
        try:
            os.replace(
                temporary_path,
                destination_path,
            )
            return
        except OSError as error:
            retries_exhausted = attempt == len(retry_delays)

            if retries_exhausted or not _is_retryable_replace_error(error):
                raise

            time.sleep(retry_delays[attempt])


def _is_retryable_replace_error(error: OSError) -> bool:
    if error.errno in _RETRYABLE_ERRNOS:
        return True

    return getattr(error, "winerror", None) in _RETRYABLE_WINDOWS_ERRORS


def _close_quietly(
    stream: BinaryIO | TextIO | None,
) -> None:
    if stream is None or stream.closed:
        return

    try:
        stream.close()
    except OSError:
        pass


def _close_descriptor_quietly(file_descriptor: int) -> None:
    if file_descriptor < 0:
        return

    try:
        os.close(file_descriptor)
    except OSError:
        pass


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _add_failure_context(
    error: BaseException,
    destination: Path,
    temporary: Path,
) -> None:
    add_note = getattr(error, "add_note", None)

    if callable(add_note):
        add_note(f"atomic destination: {destination}")
        add_note(f"atomic temporary file: {temporary}")