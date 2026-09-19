"""TOML transport adapter for the active GF Wordbench project.

This module reads and writes the external ``project.toml`` representation. It
preserves declared array order and emits canonical UTF-8/LF TOML, while schema
identity, field validation, path resolution, and cross-field policy remain the
responsibility of the project schema, validator, and loader modules.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
import math
from pathlib import Path
import tomllib
from typing import Final, TypeAlias

from gf_wordbench.infrastructure.atomic_io import atomic_write_text

TomlScalar: TypeAlias = str | int | float | bool | date | datetime | time
TomlValue: TypeAlias = TomlScalar | list["TomlValue"] | dict[str, "TomlValue"]
TomlDocument: TypeAlias = dict[str, TomlValue]

__all__ = (
    "ProjectTomlDecodeError",
    "ProjectTomlEncodeError",
    "ProjectTomlError",
    "TomlDocument",
    "TomlScalar",
    "TomlValue",
    "parse_project_toml",
    "read_project_toml",
    "render_project_toml",
    "write_project_toml",
)

_CANONICAL_ROOT_SCALARS: Final[tuple[str, ...]] = (
    "schema_id",
    "schema_version",
)

_CANONICAL_ROOT_TABLES: Final[tuple[str, ...]] = (
    "project",
    "sources",
    "gf",
    "modules",
    "validation",
)

_CANONICAL_FIELD_ORDER: Final[dict[tuple[str, ...], tuple[str, ...]]] = {
    ("project",): (
        "id",
        "name",
        "language_code",
        "root",
    ),
    ("sources",): (
        "directory",
        "glob",
        "include_regex",
        "exclude_regex",
    ),
    ("gf",): (
        "path_parts",
        "minimum_version",
    ),
    ("modules",): (
        "entrypoints",
        "checkpoints",
    ),
    ("validation",): (
        "required_scenarios",
        "optional_scenarios",
        "release_requires_pgf",
    ),
}

_BARE_KEY_CHARS: Final[frozenset[str]] = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)


class ProjectTomlError(Exception):
    """Base class for project-TOML transport failures."""


class ProjectTomlDecodeError(ProjectTomlError, ValueError):
    """Raised when project TOML cannot be decoded or parsed."""


class ProjectTomlEncodeError(ProjectTomlError, TypeError):
    """Raised when a document cannot be represented as canonical TOML."""


def read_project_toml(project_file: Path) -> TomlDocument:
    """Read and parse a project TOML file as UTF-8.

    UTF-8 with a legacy BOM and CRLF newlines are accepted. Filesystem errors
    propagate unchanged with the project path attached as diagnostic context.
    """

    path = Path(project_file)

    try:
        payload = path.read_bytes()
    except OSError as exc:
        exc.add_note(f"Project TOML path: {path}")
        raise

    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProjectTomlDecodeError(f"Project TOML is not valid UTF-8: {path}") from exc

    return parse_project_toml(text, source=path)


def parse_project_toml(
    text: str,
    *,
    source: Path | None = None,
) -> TomlDocument:
    """Parse project TOML text without applying project-schema semantics."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized_text = text.removeprefix("\ufeff")

    try:
        parsed = tomllib.loads(normalized_text)
    except tomllib.TOMLDecodeError as exc:
        location = f" in {source}" if source is not None else ""
        raise ProjectTomlDecodeError(f"Invalid project TOML{location}: {exc}") from exc

    return _normalize_document(parsed)


def render_project_toml(document: Mapping[str, object]) -> str:
    """Render a project document in deterministic canonical TOML form.

    Known schema keys and tables use the documented order. Additional keys are
    emitted deterministically after known keys so a schema-approved compatible
    minor extension can be represented without changing this transport layer.
    """

    normalized = _normalize_document(document)
    return _render_normalized_document(normalized)


def write_project_toml(
    project_file: Path,
    document: Mapping[str, object],
    *,
    create_parents: bool = False,
) -> Path:
    """Atomically write a canonical project TOML document.

    This operation is intended for explicit initialization and migration. A
    normal validation run must only read the active file and must not rewrite
    its comments or formatting.

    Parent-directory creation is delegated exclusively to ``atomic_io``.
    """

    path = Path(project_file)
    expected = _normalize_document(document)
    rendered = _render_normalized_document(expected)

    def validate_temporary(temporary: Path) -> None:
        actual = read_project_toml(temporary)

        if actual != expected:
            raise ProjectTomlEncodeError("Written project TOML failed semantic validation")

    return atomic_write_text(
        path,
        rendered,
        encoding="utf-8",
        newline="\n",
        validator=validate_temporary,
        create_parents=create_parents,
    )


def _render_normalized_document(document: TomlDocument) -> str:
    """Render and round-trip validate an already normalized document."""

    lines: list[str] = []
    root_scalars, root_tables = _partition_table(document, path=())

    for key in _ordered_keys(root_scalars, _CANONICAL_ROOT_SCALARS):
        lines.extend(_render_assignment(key, root_scalars[key]))

    for table_name in _ordered_keys(root_tables, _CANONICAL_ROOT_TABLES):
        if lines:
            lines.append("")

        _render_table(
            lines,
            path=(table_name,),
            table=root_tables[table_name],
        )

    rendered = "\n".join(lines) + "\n"

    try:
        reparsed = tomllib.loads(rendered)
    except tomllib.TOMLDecodeError as exc:
        raise ProjectTomlEncodeError(f"Canonical project TOML rendering is invalid: {exc}") from exc

    if _normalize_document(reparsed) != document:
        raise ProjectTomlEncodeError("Canonical project TOML failed semantic round-trip validation")

    return rendered


def _normalize_document(document: Mapping[str, object]) -> TomlDocument:
    """Normalize and validate the root TOML document."""

    if not isinstance(document, Mapping):
        raise ProjectTomlEncodeError("Project TOML document must be a mapping")

    normalized: TomlDocument = {}

    for key, value in document.items():
        if not isinstance(key, str) or not key:
            raise ProjectTomlEncodeError("Project TOML keys must be non-empty strings")

        normalized[key] = _normalize_value(
            value,
            path=(key,),
        )

    return normalized


def _normalize_value(
    value: object,
    *,
    path: tuple[str, ...],
) -> TomlValue:
    """Normalize one supported TOML value recursively."""

    if isinstance(value, Mapping):
        table: dict[str, TomlValue] = {}

        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise ProjectTomlEncodeError(
                    f"TOML key at {_display_path(path)} must be a non-empty string"
                )

            table[key] = _normalize_value(
                child,
                path=(*path, key),
            )

        return table

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray, memoryview),
    ):
        return [
            _normalize_value(
                item,
                path=(*path, f"[{index}]"),
            )
            for index, item in enumerate(value)
        ]

    if isinstance(value, (str, bool, int, datetime, date, time)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ProjectTomlEncodeError(
                f"Non-finite float is not allowed at {_display_path(path)}"
            )

        return value

    raise ProjectTomlEncodeError(
        f"Unsupported TOML value at {_display_path(path)}: {type(value).__name__}"
    )


def _partition_table(
    table: Mapping[str, TomlValue],
    *,
    path: tuple[str, ...],
) -> tuple[dict[str, TomlValue], dict[str, dict[str, TomlValue]]]:
    """Partition a table into assignments and child tables."""

    scalars: dict[str, TomlValue] = {}
    child_tables: dict[str, dict[str, TomlValue]] = {}

    for key, value in table.items():
        if isinstance(value, dict):
            child_tables[key] = value
        else:
            scalars[key] = value

    for key, value in scalars.items():
        if _contains_mapping(value):
            raise ProjectTomlEncodeError(
                f"Arrays of tables are not supported at {_display_path((*path, key))}"
            )

    return scalars, child_tables


def _render_table(
    lines: list[str],
    *,
    path: tuple[str, ...],
    table: Mapping[str, TomlValue],
) -> None:
    """Append one table and its child tables to the output."""

    header = ".".join(_format_key(part) for part in path)
    lines.append(f"[{header}]")

    scalars, child_tables = _partition_table(
        table,
        path=path,
    )
    preferred = _CANONICAL_FIELD_ORDER.get(path, ())

    for key in _ordered_keys(scalars, preferred):
        lines.extend(_render_assignment(key, scalars[key]))

    for child_name in _ordered_keys(child_tables, ()):
        lines.append("")

        _render_table(
            lines,
            path=(*path, child_name),
            table=child_tables[child_name],
        )


def _render_assignment(
    key: str,
    value: TomlValue,
) -> list[str]:
    """Render one TOML assignment."""

    formatted_key = _format_key(key)

    if isinstance(value, list):
        if not value:
            return [f"{formatted_key} = []"]

        return [
            f"{formatted_key} = [",
            *(f"  {_format_scalar(item)}," for item in value),
            "]",
        ]

    return [f"{formatted_key} = {_format_scalar(value)}"]


def _format_scalar(value: TomlValue) -> str:
    """Render one TOML scalar value."""

    if isinstance(value, dict):
        raise ProjectTomlEncodeError("Inline tables are not emitted")

    if isinstance(value, list):
        raise ProjectTomlEncodeError("Nested arrays are not emitted")

    if isinstance(value, str):
        return _quote_basic_string(value)

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return repr(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, time):
        return value.isoformat()

    raise ProjectTomlEncodeError(f"Unsupported TOML scalar: {type(value).__name__}")


def _format_key(key: str) -> str:
    """Render a TOML bare or quoted key."""

    if key and all(character in _BARE_KEY_CHARS for character in key):
        return key

    return _quote_basic_string(key)


def _quote_basic_string(value: str) -> str:
    """Render a TOML basic string with deterministic escaping."""

    escaped: list[str] = ['"']
    replacements = {
        "\\": "\\\\",
        '"': '\\"',
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
    }

    for character in value:
        replacement = replacements.get(character)

        if replacement is not None:
            escaped.append(replacement)
            continue

        codepoint = ord(character)

        if codepoint < 0x20 or codepoint == 0x7F:
            escaped.append(f"\\u{codepoint:04X}")
        else:
            escaped.append(character)

    escaped.append('"')
    return "".join(escaped)


def _ordered_keys(
    mapping: Mapping[str, object],
    preferred: Sequence[str],
) -> list[str]:
    """Return known keys first and extension keys alphabetically."""

    preferred_set = set(preferred)

    return [key for key in preferred if key in mapping] + sorted(
        key for key in mapping if key not in preferred_set
    )


def _contains_mapping(value: TomlValue) -> bool:
    """Return whether a value recursively contains a table."""

    if isinstance(value, dict):
        return True

    if isinstance(value, list):
        return any(_contains_mapping(item) for item in value)

    return False


def _display_path(path: tuple[str, ...]) -> str:
    """Return a readable diagnostic path."""

    return ".".join(path) if path else "<root>"
