from __future__ import annotations

import json
import math
import os
import re
import stat
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Final, TypeAlias

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.infrastructure.filesystem import (
    require_directory,
    require_within,
    resolve_for_output,
)
from gf_wordbench.kernel.events import (
    EventField,
    EventLevel,
    EventScalar,
    LifecycleEvent,
)

LifecycleValueRedactor: TypeAlias = Callable[[str, EventScalar], EventScalar]

MASTER_LOG_RELATIVE_PATH: Final[Path] = Path("raw/master.log")
MASTER_LOG_ENCODING: Final[str] = "utf-8"
MASTER_LOG_NEWLINE: Final[str] = "\n"
MASTER_LOG_ROLE: Final[str] = "master lifecycle log"
REDACTED_VALUE: Final[str] = "[REDACTED]"
_MAX_LINE_BYTES: Final[int] = 64 * 1024
_MAX_STRING_CHARS: Final[int] = 4_096
_SAFE_VALUE = re.compile(r"^[^\s\x00-\x1f\x7f=\[\]\{\},\"']+$")
_FIELD_KEY = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_SENSITIVE_KEY = re.compile(
    r"(?:^|_)(?:api_key|authorization|credential|password|secret|token)(?:$|_)",
    re.IGNORECASE,
)
_RESERVED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "run_id",
        "stage",
        "operation",
        "subject",
        "status",
        "error_code",
        "message",
        "evidence_path",
    }
)
_SYNC_LEVELS: Final[frozenset[EventLevel]] = frozenset(
    {EventLevel.ERROR, EventLevel.FATAL}
)
_SYNC_EVENTS: Final[frozenset[str]] = frozenset(
    {
        "stage_completed",
        "cancellation_requested",
        "fatal_error",
        "reports_completed",
        "manifest_completed",
        "run_finalizing",
        "run_completed",
    }
)


@dataclass(frozen=True, slots=True)
class LifecycleLogPolicy:
    emit_debug: bool = False
    sync_every_event: bool = False
    sync_levels: frozenset[EventLevel] = _SYNC_LEVELS
    sync_events: frozenset[str] = _SYNC_EVENTS
    maximum_line_bytes: int = _MAX_LINE_BYTES

    def __post_init__(self) -> None:
        if type(self.emit_debug) is not bool:
            raise TypeError("emit_debug must be a boolean")
        if type(self.sync_every_event) is not bool:
            raise TypeError("sync_every_event must be a boolean")
        sync_levels = frozenset(self.sync_levels)
        if not all(isinstance(level, EventLevel) for level in sync_levels):
            raise TypeError("sync_levels must contain EventLevel values")
        sync_events = frozenset(self.sync_events)
        for event in sync_events:
            _validate_field_name(event, "sync event")
        maximum_line_bytes = _positive_int(
            self.maximum_line_bytes,
            "maximum_line_bytes",
        )
        object.__setattr__(self, "sync_levels", sync_levels)
        object.__setattr__(self, "sync_events", sync_events)
        object.__setattr__(self, "maximum_line_bytes", maximum_line_bytes)

    def should_emit(self, event: LifecycleEvent) -> bool:
        if not isinstance(event, LifecycleEvent):
            raise TypeError("event must be LifecycleEvent")
        return self.emit_debug or event.level is not EventLevel.DEBUG

    def should_sync(self, event: LifecycleEvent) -> bool:
        if not isinstance(event, LifecycleEvent):
            raise TypeError("event must be LifecycleEvent")
        return (
            self.sync_every_event
            or event.level in self.sync_levels
            or event.event in self.sync_events
        )


@dataclass(frozen=True, slots=True)
class LifecycleLogReceipt:
    path: Path
    bytes_written: int
    synchronized: bool
    emitted: bool

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            raise ValueError("path must be an absolute pathlib.Path")
        _non_negative_int(self.bytes_written, "bytes_written")
        if type(self.synchronized) is not bool:
            raise TypeError("synchronized must be a boolean")
        if type(self.emitted) is not bool:
            raise TypeError("emitted must be a boolean")
        if not self.emitted and self.bytes_written != 0:
            raise ValueError("a suppressed event cannot write bytes")


class LifecycleLogWriter:
    __slots__ = (
        "_run_root",
        "_path",
        "_policy",
        "_redactor",
        "_lock",
        "_finalized",
        "_initialized",
    )

    def __init__(
        self,
        run_root: Path,
        *,
        path: Path | None = None,
        policy: LifecycleLogPolicy | None = None,
        redactor: LifecycleValueRedactor | None = None,
        initialize: bool = True,
    ) -> None:
        root = _existing_absolute_directory(run_root, "run_root")
        candidate = root / MASTER_LOG_RELATIVE_PATH if path is None else path
        destination = _contained_output_path(
            candidate,
            root=root,
            field_name="path",
        )
        if redactor is not None and not callable(redactor):
            raise TypeError("redactor must be callable or None")
        self._run_root = root
        self._path = destination
        self._policy = policy or LifecycleLogPolicy()
        self._redactor = redactor
        self._lock = RLock()
        self._finalized = False
        self._initialized = False
        if initialize:
            self.initialize()

    @property
    def run_root(self) -> Path:
        return self._run_root

    @property
    def path(self) -> Path:
        return self._path

    @property
    def policy(self) -> LifecycleLogPolicy:
        return self._policy

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def finalized(self) -> bool:
        return self._finalized

    def initialize(self) -> Path:
        with self._lock:
            if self._finalized:
                raise RuntimeError("lifecycle log is finalized")
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path = _contained_output_path(
                self._path,
                root=self._run_root,
                field_name="path",
            )
            if self._path.exists():
                _require_regular_non_link(self._path)
            else:
                _create_empty_log(self._path, root=self._run_root)
            self._initialized = True
            return self._path

    def append(
        self,
        event: LifecycleEvent,
        *,
        synchronize: bool | None = None,
    ) -> LifecycleLogReceipt:
        if not isinstance(event, LifecycleEvent):
            raise TypeError("event must be LifecycleEvent")
        if synchronize is not None and type(synchronize) is not bool:
            raise TypeError("synchronize must be a boolean or None")
        with self._lock:
            if self._finalized:
                raise RuntimeError("lifecycle log is finalized")
            if not self._policy.should_emit(event):
                return LifecycleLogReceipt(
                    path=self._path,
                    bytes_written=0,
                    synchronized=False,
                    emitted=False,
                )
            if not self._initialized:
                self.initialize()
            line = format_lifecycle_event(
                event,
                redactor=self._redactor,
                maximum_line_bytes=self._policy.maximum_line_bytes,
            )
            payload = line.encode(MASTER_LOG_ENCODING)
            should_sync = (
                self._policy.should_sync(event)
                if synchronize is None
                else synchronize
            )
            _append_bytes(
                self._path,
                payload,
                root=self._run_root,
                synchronize=should_sync,
            )
            return LifecycleLogReceipt(
                path=self._path,
                bytes_written=len(payload),
                synchronized=should_sync,
                emitted=True,
            )

    def write_master_event(
        self,
        event: LifecycleEvent,
        *,
        synchronize: bool | None = None,
    ) -> LifecycleLogReceipt:
        return self.append(event, synchronize=synchronize)

    def flush(self) -> None:
        with self._lock:
            if not self._initialized:
                self.initialize()
            _synchronize_file(self._path, root=self._run_root)

    def finalize(self) -> Path:
        with self._lock:
            if self._finalized:
                return self._path
            if not self._initialized:
                self.initialize()
            _normalize_final_newline(
                self._path,
                root=self._run_root,
            )
            _synchronize_file(self._path, root=self._run_root)
            self._finalized = True
            return self._path

    def __call__(self, event: LifecycleEvent, /) -> None:
        self.append(event)



def format_lifecycle_event(
    event: LifecycleEvent,
    *,
    redactor: LifecycleValueRedactor | None = None,
    maximum_line_bytes: int = _MAX_LINE_BYTES,
) -> str:
    if not isinstance(event, LifecycleEvent):
        raise TypeError("event must be LifecycleEvent")
    if redactor is not None and not callable(redactor):
        raise TypeError("redactor must be callable or None")
    limit = _positive_int(maximum_line_bytes, "maximum_line_bytes")
    fields = _event_field_values(event)
    rendered = [
        _format_timestamp(event),
        event.level.value,
        event.event,
    ]
    for key, value in fields:
        effective = _redact_value(key, value, redactor)
        rendered.append(f"{key}={_render_value(effective)}")
    line = " ".join(rendered) + MASTER_LOG_NEWLINE
    if len(line.encode(MASTER_LOG_ENCODING)) > limit:
        raise ValueError(
            f"lifecycle event exceeds the {limit}-byte line limit"
        )
    return line



def create_lifecycle_log(
    run_root: Path,
    *,
    path: Path | None = None,
    replace: bool = False,
) -> Path:
    if type(replace) is not bool:
        raise TypeError("replace must be a boolean")
    root = _existing_absolute_directory(run_root, "run_root")
    candidate = root / MASTER_LOG_RELATIVE_PATH if path is None else path
    destination = _contained_output_path(
        candidate,
        root=root,
        field_name="path",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination = _contained_output_path(
        destination,
        root=root,
        field_name="path",
    )
    if destination.exists() and not replace:
        _require_regular_non_link(destination)
        return destination
    atomic_write_text(
        destination,
        "",
        encoding=MASTER_LOG_ENCODING,
        newline=MASTER_LOG_NEWLINE,
        create_parents=True,
        root=root,
        role=MASTER_LOG_ROLE,
        sync=True,
    )
    return destination



def append_lifecycle_event(
    path: Path,
    event: LifecycleEvent,
    *,
    run_root: Path,
    redactor: LifecycleValueRedactor | None = None,
    synchronize: bool = False,
    maximum_line_bytes: int = _MAX_LINE_BYTES,
) -> LifecycleLogReceipt:
    if type(synchronize) is not bool:
        raise TypeError("synchronize must be a boolean")
    root = _existing_absolute_directory(run_root, "run_root")
    destination = _contained_output_path(
        path,
        root=root,
        field_name="path",
    )
    line = format_lifecycle_event(
        event,
        redactor=redactor,
        maximum_line_bytes=maximum_line_bytes,
    )
    payload = line.encode(MASTER_LOG_ENCODING)
    _append_bytes(
        destination,
        payload,
        root=root,
        synchronize=synchronize,
    )
    return LifecycleLogReceipt(
        path=destination,
        bytes_written=len(payload),
        synchronized=synchronize,
        emitted=True,
    )



def write_master_event(
    writer: LifecycleLogWriter,
    event: LifecycleEvent,
    *,
    synchronize: bool | None = None,
) -> LifecycleLogReceipt:
    if not isinstance(writer, LifecycleLogWriter):
        raise TypeError("writer must be LifecycleLogWriter")
    return writer.append(event, synchronize=synchronize)



def finalize_lifecycle_log(writer: LifecycleLogWriter) -> Path:
    if not isinstance(writer, LifecycleLogWriter):
        raise TypeError("writer must be LifecycleLogWriter")
    return writer.finalize()



def _event_field_values(
    event: LifecycleEvent,
) -> tuple[tuple[str, EventScalar], ...]:
    values: list[tuple[str, EventScalar]] = []
    canonical = (
        ("run_id", event.run_id),
        ("stage", event.stage),
        ("operation", event.operation),
        ("subject", event.subject),
        ("status", event.status),
        ("error_code", event.error_code),
        ("evidence_path", event.evidence_path),
        ("message", event.message or None),
    )
    values.extend((key, value) for key, value in canonical if value is not None)
    seen = {key for key, _ in values}
    for field in event.fields:
        if not isinstance(field, EventField):
            raise TypeError("event fields must contain EventField values")
        if field.key in _RESERVED_FIELDS:
            raise ValueError(
                f"event field {field.key!r} duplicates a canonical field"
            )
        if field.key in seen:
            raise ValueError(f"duplicate event field {field.key!r}")
        seen.add(field.key)
        values.append((field.key, field.value))
    canonical_count = sum(1 for _, value in canonical if value is not None)
    head = tuple(values[:canonical_count])
    tail = tuple(sorted(values[canonical_count:], key=lambda item: item[0]))
    return head + tail



def _format_timestamp(event: LifecycleEvent) -> str:
    timestamp = event.timestamp
    milliseconds = timestamp.microsecond // 1000
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{milliseconds:03d}Z"



def _redact_value(
    key: str,
    value: EventScalar,
    redactor: LifecycleValueRedactor | None,
) -> EventScalar:
    _validate_field_name(key, "event field key")
    if _SENSITIVE_KEY.search(key) is not None:
        return REDACTED_VALUE
    if redactor is None:
        return value
    redacted = redactor(key, value)
    _validate_scalar(redacted, f"redacted value for {key!r}")
    return redacted



def _render_value(value: EventScalar) -> str:
    _validate_scalar(value, "event value")
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".17g")
    text = value
    if _SAFE_VALUE.fullmatch(text) is not None:
        return text
    return json.dumps(
        text,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )



def _append_bytes(
    path: Path,
    payload: bytes,
    *,
    root: Path,
    synchronize: bool,
) -> None:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if not payload.endswith(b"\n"):
        raise ValueError("lifecycle payload must end with LF")
    path.parent.mkdir(parents=True, exist_ok=True)
    destination = _contained_output_path(
        path,
        root=root,
        field_name="path",
    )
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        flags |= nofollow
    descriptor = -1
    try:
        descriptor = os.open(destination, flags, 0o600)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("master lifecycle log must be a regular file")
        view = memoryview(payload)
        total = 0
        while total < len(view):
            written = os.write(descriptor, view[total:])
            if written <= 0:
                raise OSError("master lifecycle log append made no progress")
            total += written
        if synchronize:
            os.fsync(descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    _require_regular_non_link(destination)
    require_within(
        destination,
        root,
        role=MASTER_LOG_ROLE,
        stage="post-append containment",
    )



def _synchronize_file(path: Path, *, root: Path) -> None:
    destination = _contained_existing_file(path, root=root)
    descriptor = os.open(destination, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)



def _normalize_final_newline(path: Path, *, root: Path) -> None:
    destination = _contained_existing_file(path, root=root)
    data = destination.read_bytes()
    if not data:
        return
    normalized = data.rstrip(b"\r\n") + b"\n"
    if normalized == data:
        return
    text = normalized.decode(MASTER_LOG_ENCODING, errors="strict")
    atomic_write_text(
        destination,
        text,
        encoding=MASTER_LOG_ENCODING,
        newline=MASTER_LOG_NEWLINE,
        create_parents=False,
        root=root,
        role=MASTER_LOG_ROLE,
        sync=True,
    )



def _create_empty_log(path: Path, *, root: Path) -> None:
    destination = _contained_output_path(
        path,
        root=root,
        field_name="path",
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        flags |= nofollow
    descriptor = -1
    try:
        descriptor = os.open(destination, flags, 0o600)
        os.fsync(descriptor)
    except FileExistsError:
        _require_regular_non_link(destination)
    finally:
        if descriptor >= 0:
            os.close(descriptor)



def _contained_output_path(
    path: Path,
    *,
    root: Path,
    field_name: str,
) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    if not path.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    resolved = resolve_for_output(path)
    return require_within(
        resolved,
        root,
        role=MASTER_LOG_ROLE,
        stage="output containment",
        for_output=True,
    )



def _contained_existing_file(path: Path, *, root: Path) -> Path:
    destination = _contained_output_path(
        path,
        root=root,
        field_name="path",
    )
    _require_regular_non_link(destination)
    return require_within(
        destination,
        root,
        role=MASTER_LOG_ROLE,
        stage="existing-file containment",
    )



def _require_regular_non_link(path: Path) -> Path:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        raise FileNotFoundError(f"master lifecycle log does not exist: {path}") from None
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise OSError("master lifecycle log must be a non-link regular file")
    return path



def _existing_absolute_directory(value: object, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return require_directory(value, role=field_name)



def _validate_field_name(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if _FIELD_KEY.fullmatch(text) is None:
        raise ValueError(f"{field_name} must use lower_snake_case")
    return text



def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value



def _validate_scalar(value: object, field_name: str) -> None:
    if value is None or type(value) in (bool, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{field_name} must be finite")
        return
    if isinstance(value, str):
        if "\x00" in value:
            raise ValueError(f"{field_name} must not contain NUL")
        if len(value) > _MAX_STRING_CHARS:
            raise ValueError(
                f"{field_name} exceeds {_MAX_STRING_CHARS} characters"
            )
        return
    raise TypeError(f"{field_name} must be a scalar event value")



def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value



def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


__all__ = (
    "LifecycleLogPolicy",
    "LifecycleLogReceipt",
    "LifecycleLogWriter",
    "LifecycleValueRedactor",
    "MASTER_LOG_ENCODING",
    "MASTER_LOG_NEWLINE",
    "MASTER_LOG_RELATIVE_PATH",
    "MASTER_LOG_ROLE",
    "REDACTED_VALUE",
    "append_lifecycle_event",
    "create_lifecycle_log",
    "finalize_lifecycle_log",
    "format_lifecycle_event",
    "write_master_event",
)
