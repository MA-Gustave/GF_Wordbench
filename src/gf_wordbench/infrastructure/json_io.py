"""Strict JSON I/O for canonical GF Wordbench documents."""

from __future__ import annotations

import json
import math
from os import PathLike
from pathlib import Path
from typing import Final, NoReturn, TypeAlias, cast

from gf_wordbench.kernel.errors import (
    ContractViolationError,
    EvidenceIOError,
    GFWordbenchError,
)

from .atomic_io import atomic_write_text

__all__ = [
    "JSON_ENCODING",
    "JSON_INDENT",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "format_json",
    "parse_json",
    "read_json",
    "write_json",
]

JSON_ENCODING: Final[str] = "utf-8"
JSON_INDENT: Final[int] = 2

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class _DuplicateKey(ValueError):
    pass


class _NonFiniteNumber(ValueError):
    pass


def _bounded(value: str, limit: int = 160) -> str:
    compact = value.replace("\r", "\\r").replace("\n", "\\n")
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def _os_detail(error: OSError) -> str:
    suffix = "" if error.errno is None else f" (errno {error.errno})"
    return f"{type(error).__name__}{suffix}"


def _io_error(
    message: str,
    *,
    operation: str,
    subject: str,
    detail: str = "",
    retryable: bool = False,
) -> EvidenceIOError:
    return EvidenceIOError(
        message,
        detail=_bounded(detail),
        stage="infrastructure",
        operation=operation,
        subject=subject,
        retryable=retryable,
    )


def _contract(message: str, detail: str) -> NoReturn:
    raise ContractViolationError(
        message,
        detail=_bounded(detail),
        stage="infrastructure",
        operation="serialize-json",
    )


def _validate(value: object, *, location: str, active: set[int]) -> None:
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _contract("JSON contains a non-finite number", location)
        return
    if isinstance(value, str):
        try:
            value.encode(JSON_ENCODING)
        except UnicodeEncodeError as error:
            _contract(
                "JSON contains text that cannot be encoded as UTF-8",
                f"{location}: invalid Unicode scalar at character {error.start}",
            )
        return
    if not isinstance(value, (list, dict)):
        _contract("JSON contains a non-JSON value", f"{location}: {type(value).__name__}")

    identity = id(value)
    if identity in active:
        _contract("JSON contains a circular reference", location)
    active.add(identity)
    try:
        if isinstance(value, list):
            for index, item in enumerate(value):
                _validate(item, location=f"{location}[{index}]", active=active)
        else:
            for key, item in value.items():
                if not isinstance(key, str):
                    _contract(
                        "JSON object keys must be strings",
                        f"{location}: {type(key).__name__}",
                    )
                _validate(key, location=f"{location} object key", active=active)
                _validate(item, location=f"{location}.{_bounded(key, 80)}", active=active)
    finally:
        active.remove(identity)


def _validate_document(value: object) -> JsonObject:
    if not isinstance(value, dict):
        _contract(
            "Canonical JSON documents must have one object at the root",
            f"root type {type(value).__name__}",
        )
    _validate(value, location="$", active=set())
    return cast(JsonObject, value)


def _reject_constant(token: str) -> NoReturn:
    raise _NonFiniteNumber(token)


def _object_from_pairs(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _decode_text(text: str, *, source: str) -> JsonObject:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
        )
    except _DuplicateKey as error:
        raise _io_error(
            "JSON object contains a duplicate key",
            operation="parse-json",
            subject=source,
            detail=f"duplicate key: {_bounded(str(error))!r}",
        ) from error
    except _NonFiniteNumber as error:
        raise _io_error(
            "JSON contains a prohibited non-finite number",
            operation="parse-json",
            subject=source,
            detail=f"token: {error}",
        ) from error
    except json.JSONDecodeError as error:
        raise _io_error(
            "JSON document is malformed",
            operation="parse-json",
            subject=source,
            detail=f"line {error.lineno}, column {error.colno}: {error.msg}",
        ) from error
    except RecursionError as error:
        raise _io_error(
            "JSON document nesting is too deep",
            operation="parse-json",
            subject=source,
        ) from error

    if not isinstance(value, dict):
        raise _io_error(
            "Canonical JSON documents must have one object at the root",
            operation="parse-json",
            subject=source,
            detail=f"root type {type(value).__name__}",
        )
    try:
        _validate(value, location="$", active=set())
    except ContractViolationError as error:
        raise _io_error(
            "JSON document contains invalid Unicode data",
            operation="parse-json",
            subject=source,
            detail=error.detail,
        ) from error
    return cast(JsonObject, value)


def _decode_bytes(data: bytes, *, source: str) -> JsonObject:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise _io_error(
            "JSON document is not valid UTF-8",
            operation="decode-json",
            subject=source,
            detail=f"invalid byte sequence at offset {error.start}",
        ) from error
    return _decode_text(text, source=source)


def parse_json(text: str, *, source: str = "<memory>") -> JsonObject:
    """Parse one strict JSON object from text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(source, str) or not source:
        raise ValueError("source must be a non-empty string")
    return _decode_text(text, source=source)


def read_json(
    path: str | PathLike[str],
    *,
    max_bytes: int | None = None,
) -> JsonObject:
    """Read one UTF-8 JSON object, accepting a BOM for compatibility."""
    source = Path(path)
    if max_bytes is not None and (
        isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0
    ):
        raise ValueError("max_bytes must be a non-negative integer or None")
    try:
        with source.open("rb") as stream:
            data = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
    except OSError as error:
        raise _io_error(
            "Unable to read JSON document",
            operation="read-json",
            subject=str(source),
            detail=_os_detail(error),
            retryable=True,
        ) from error
    if max_bytes is not None and len(data) > max_bytes:
        raise _io_error(
            "JSON document exceeds the configured size limit",
            operation="read-json",
            subject=str(source),
            detail=f"limit: {max_bytes} bytes",
        )
    return _decode_bytes(data, source=str(source))


def format_json(document: JsonObject) -> str:
    """Render canonical JSON while preserving documented field order."""
    validated = _validate_document(document)
    try:
        rendered = json.dumps(
            validated,
            ensure_ascii=False,
            allow_nan=False,
            check_circular=True,
            indent=JSON_INDENT,
            sort_keys=False,
        )
    except (TypeError, ValueError, RecursionError) as error:
        raise ContractViolationError(
            "Unable to serialize the canonical JSON document",
            detail=type(error).__name__,
            stage="infrastructure",
            operation="serialize-json",
        ) from error
    return rendered.rstrip("\n") + "\n"


def write_json(path: str | PathLike[str], document: JsonObject) -> Path:
    """Serialize, verify and atomically replace one canonical JSON document."""
    destination = Path(path)
    rendered = format_json(document)
    expected = rendered.encode(JSON_ENCODING)

    def verify(temporary_path: Path) -> None:
        try:
            actual = temporary_path.read_bytes()
        except OSError as error:
            raise _io_error(
                "Unable to verify temporary JSON document",
                operation="verify-json-write",
                subject=str(destination),
                detail=_os_detail(error),
            ) from error
        if actual != expected:
            raise _io_error(
                "Temporary JSON document differs from canonical serialization",
                operation="verify-json-write",
                subject=str(destination),
            )
        _decode_bytes(actual, source=str(temporary_path))

    try:
        atomic_write_text(
            destination,
            rendered,
            encoding=JSON_ENCODING,
            newline="\n",
            validator=verify,
        )
    except GFWordbenchError:
        raise
    except OSError as error:
        raise _io_error(
            "Unable to write JSON document",
            operation="write-json",
            subject=str(destination),
            detail=_os_detail(error),
            retryable=True,
        ) from error
    return destination
