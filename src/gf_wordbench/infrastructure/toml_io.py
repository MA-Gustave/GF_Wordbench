"""Strict TOML reading and canonical TOML text serialization.

This module owns format-level I/O only. Project schemas choose fields, field
order, defaults, compatibility rules, and validation policy. Atomic replacement
is owned by :mod:`gf_wordbench.infrastructure.atomic_io`.
"""

from __future__ import annotations

import math
import re
import tomllib
from collections.abc import Mapping
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path, PurePath
from typing import Final, TypeAlias, cast

from gf_wordbench.kernel.serialization import (
    format_rfc3339_utc,
    path_to_portable_string,
)

TomlScalar: TypeAlias = str | int | float | bool | datetime | date | time
TomlValue: TypeAlias = TomlScalar | list["TomlValue"] | dict[str, "TomlValue"]
TomlDocument: TypeAlias = dict[str, TomlValue]

_UTF8_BOM: Final[str] = "\ufeff"
_BARE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]+$")

__all__ = [
    "TomlDocument",
    "TomlScalar",
    "TomlValue",
    "dumps_canonical_toml",
    "loads_toml",
    "read_toml",
]


def read_toml(path: Path) -> TomlDocument:
    """Read and parse one TOML document from *path*.

    Canonical files are UTF-8 without a byte-order mark. Readers accept one
    legacy UTF-8 BOM and either LF or CRLF newlines. Filesystem, decoding, and
    TOML syntax failures remain explicit and preserve their original exception
    type; the path is attached as diagnostic context when supported.
    """

    try:
        text = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        _add_exception_note(exc, f"while reading TOML document: {path}")
        raise

    try:
        return loads_toml(text)
    except tomllib.TOMLDecodeError as exc:
        _add_exception_note(exc, f"while parsing TOML document: {path}")
        raise


def loads_toml(text: str) -> TomlDocument:
    """Parse TOML text and return its root table.

    A single leading Unicode BOM is accepted for callers that already decoded
    legacy bytes. Parsing is delegated to the Python standard-library TOML 1.0
    parser; schema validation belongs to the owning configuration adapter.
    """

    if text.startswith(_UTF8_BOM):
        text = text.removeprefix(_UTF8_BOM)
    return cast(TomlDocument, tomllib.loads(text))


def dumps_canonical_toml(document: Mapping[str, object]) -> str:
    """Serialize an explicitly ordered mapping as canonical TOML text.

    The serializer emits UTF-8-ready text with LF newlines, no BOM, double-
    quoted strings, deterministic traversal, and one final newline. Mapping and
    array order are preserved. Sets, ``None``, naive datetimes, non-finite
    floats, arbitrary objects, and cyclic containers are rejected.

    Root and table scalar fields are emitted before child tables because TOML
    cannot return to a parent table after opening a child table. Schema writers
    therefore remain responsible for supplying the intended order within each
    scalar group and each child-table group.
    """

    _require_string_keys(document)
    lines: list[str] = []
    _emit_table(
        document,
        table_path=(),
        lines=lines,
        active_containers=set(),
        emit_header=False,
    )
    return "\n".join(lines).rstrip("\n") + "\n"


def _emit_table(
    table: Mapping[str, object],
    *,
    table_path: tuple[str, ...],
    lines: list[str],
    active_containers: set[int],
    emit_header: bool,
) -> None:
    container_id = _enter_container(table, active_containers)
    try:
        scalar_items: list[tuple[str, object]] = []
        child_tables: list[tuple[str, Mapping[str, object]]] = []

        for key, value in table.items():
            _require_plain_string_key(key)
            if isinstance(value, Mapping):
                child_tables.append((key, cast(Mapping[str, object], value)))
            else:
                scalar_items.append((key, value))

        if emit_header:
            _append_section_break(lines)
            lines.append(f"[{_format_dotted_key(table_path)}]")

        for key, value in scalar_items:
            rendered = _format_value(value, active_containers=active_containers)
            if "\n" not in rendered:
                lines.append(f"{_format_key(key)} = {rendered}")
                continue

            rendered_lines = rendered.splitlines()
            lines.append(f"{_format_key(key)} = {rendered_lines[0]}")
            lines.extend(rendered_lines[1:])

        for key, child in child_tables:
            _emit_table(
                child,
                table_path=(*table_path, key),
                lines=lines,
                active_containers=active_containers,
                emit_header=True,
            )
    finally:
        active_containers.remove(container_id)


def _format_value(value: object, *, active_containers: set[int]) -> str:
    if isinstance(value, Enum):
        enum_value = value.value
        if not isinstance(enum_value, str):
            raise TypeError(
                "Canonical TOML enums must expose string values, got "
                f"{type(enum_value).__name__}"
            )
        return _format_basic_string(enum_value)

    if isinstance(value, PurePath):
        return _format_basic_string(path_to_portable_string(value))

    if isinstance(value, str):
        return _format_basic_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical TOML does not permit non-finite floats")
        return repr(value)
    if isinstance(value, datetime):
        return format_rfc3339_utc(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        if value.tzinfo is not None and value.utcoffset() is not None:
            raise ValueError("Canonical TOML time values must not carry a timezone")
        timespec = "microseconds" if value.microsecond else "seconds"
        return value.isoformat(timespec=timespec)

    if isinstance(value, (list, tuple)):
        return _format_array(value, active_containers=active_containers)

    if isinstance(value, Mapping):
        return _format_inline_table(value, active_containers=active_containers)

    if value is None:
        raise TypeError("TOML has no null value; omit the field or use a schema value")
    if isinstance(value, (set, frozenset)):
        raise TypeError("Sets must be converted to an explicitly ordered array")

    raise TypeError(
        "Unsupported canonical TOML type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _format_array(
    values: list[object] | tuple[object, ...],
    *,
    active_containers: set[int],
) -> str:
    container_id = _enter_container(values, active_containers)
    try:
        if not values:
            return "[]"

        rendered = [
            _format_value(item, active_containers=active_containers)
            for item in values
        ]
        lines = ["["]
        for item in rendered:
            item_lines = item.splitlines()
            lines.append(f"  {item_lines[0]}")
            lines.extend(f"  {line}" for line in item_lines[1:])
            lines[-1] += ","
        lines.append("]")
        return "\n".join(lines)
    finally:
        active_containers.remove(container_id)


def _format_inline_table(
    table: Mapping[object, object],
    *,
    active_containers: set[int],
) -> str:
    container_id = _enter_container(table, active_containers)
    try:
        entries: list[str] = []
        for key, value in table.items():
            _require_plain_string_key(key)
            rendered = _format_value(value, active_containers=active_containers)
            if "\n" in rendered:
                rendered = " ".join(line.strip() for line in rendered.splitlines())
            entries.append(f"{_format_key(key)} = {rendered}")
        return "{ " + ", ".join(entries) + " }"
    finally:
        active_containers.remove(container_id)


def _format_dotted_key(parts: tuple[str, ...]) -> str:
    return ".".join(_format_key(part) for part in parts)


def _format_key(key: str) -> str:
    if _BARE_KEY_PATTERN.fullmatch(key):
        return key
    return _format_basic_string(key)


def _format_basic_string(value: str) -> str:
    escaped: list[str] = ['"']
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError("TOML strings cannot contain Unicode surrogate code points")

        replacement = {
            '"': '\\"',
            "\\": "\\\\",
            "\b": "\\b",
            "\t": "\\t",
            "\n": "\\n",
            "\f": "\\f",
            "\r": "\\r",
        }.get(character)
        if replacement is not None:
            escaped.append(replacement)
        elif codepoint < 0x20 or codepoint == 0x7F:
            escaped.append(f"\\u{codepoint:04X}")
        else:
            escaped.append(character)
    escaped.append('"')
    return "".join(escaped)


def _require_string_keys(value: Mapping[object, object]) -> None:
    for key in value:
        _require_plain_string_key(key)


def _require_plain_string_key(key: object) -> None:
    if isinstance(key, Enum) or not isinstance(key, str):
        raise TypeError("Canonical TOML keys must be plain strings")


def _enter_container(value: object, active_containers: set[int]) -> int:
    container_id = id(value)
    if container_id in active_containers:
        raise ValueError("Cyclic structures cannot be serialized as canonical TOML")
    active_containers.add(container_id)
    return container_id


def _append_section_break(lines: list[str]) -> None:
    if lines and lines[-1] != "":
        lines.append("")


def _add_exception_note(exc: BaseException, note: str) -> None:
    exc.add_note(note)
