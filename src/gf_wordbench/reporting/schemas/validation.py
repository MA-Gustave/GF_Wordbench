from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final, Never, Protocol, Self, TypeAlias, TypeVar, cast

from gf_wordbench.kernel.errors import SchemaValidationError, UnsupportedVersionError
from gf_wordbench.kernel.serialization import JsonValue

_SCHEMA_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_UTC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?P<fraction>\.[0-9]{1,6})?Z$"
)
_WINDOWS_DRIVE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")
_WINDOWS_RESERVED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)
_MAX_SCHEMA_TEXT: Final[int] = 1_000_000
_MAX_CONTAINER_ITEMS: Final[int] = 1_000_000
_MAX_NESTING_DEPTH: Final[int] = 128

JsonObject: TypeAlias = Mapping[str, object]
PathLike: TypeAlias = str | Path
_T = TypeVar("_T")


class _OrderKey(Protocol):
    def __lt__(self, other: Self, /) -> bool: ...


_K = TypeVar("_K", bound=_OrderKey)


@unique
class SchemaCompatibility(StrEnum):
    STRICT = "strict"
    FORWARD_MINOR = "forward_minor"


@dataclass(frozen=True, slots=True, order=True)
class SchemaVersion:
    major: int
    minor: int

    def __post_init__(self) -> None:
        if type(self.major) is not int or self.major < 0:
            raise ValueError("major must be a non-negative integer")
        if type(self.minor) is not int or self.minor < 0:
            raise ValueError("minor must be a non-negative integer")

    @classmethod
    def parse(cls, value: str) -> SchemaVersion:
        checked = require_text_value(value, path="schema_version")
        match = _SCHEMA_VERSION_PATTERN.fullmatch(checked)
        if match is None:
            raise ValueError("schema version must use canonical major.minor form")
        return cls(major=int(match.group(1)), minor=int(match.group(2)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True, slots=True)
class SchemaIdentity:
    schema_id: str
    version: SchemaVersion

    def __post_init__(self) -> None:
        require_text_value(self.schema_id, path="schema_id")
        if not isinstance(self.version, SchemaVersion):
            raise TypeError("version must be SchemaVersion")


@dataclass(frozen=True, slots=True)
class ValidationContext:
    source: Path | None = None
    schema_id: str | None = None

    def __post_init__(self) -> None:
        raw_source: object = self.source
        if raw_source is not None and not isinstance(raw_source, Path):
            if not isinstance(raw_source, (str, os.PathLike)):
                raise TypeError("source must be path-like or None")
            object.__setattr__(self, "source", Path(raw_source))
        if self.schema_id is not None:
            require_text_value(self.schema_id, path="schema_id")

    def fail(self, path: str, message: str) -> Never:
        raise SchemaValidationError(self.format(path, message))

    def unsupported(self, path: str, message: str) -> Never:
        raise UnsupportedVersionError(self.format(path, message))

    def format(self, path: str, message: str) -> str:
        checked_path = require_text_value(path, path="validation path")
        checked_message = require_text_value(message, path="validation message")
        prefix = f"{self.source}: " if self.source is not None else ""
        schema = f"[{self.schema_id}] " if self.schema_id is not None else ""
        return f"{prefix}{schema}{checked_path}: {checked_message}"


def validation_context(
    *,
    source: PathLike | None = None,
    schema_id: str | None = None,
) -> ValidationContext:
    return ValidationContext(
        source=None if source is None else Path(source),
        schema_id=schema_id,
    )


def parse_schema_version(
    value: object,
    *,
    path: str = "$.schema_version",
    context: ValidationContext | None = None,
) -> SchemaVersion:
    checked = require_string_value(value, path=path, context=context)
    match = _SCHEMA_VERSION_PATTERN.fullmatch(checked)
    if match is None:
        _fail(
            context,
            path,
            "must use canonical major.minor form",
        )
    return SchemaVersion(
        major=int(match.group(1)),
        minor=int(match.group(2)),
    )


def validate_schema_identity(
    document: object,
    *,
    expected_schema_id: str,
    current_version: SchemaVersion | str,
    compatibility: SchemaCompatibility = SchemaCompatibility.STRICT,
    source: PathLike | None = None,
) -> tuple[Mapping[str, object], SchemaVersion, bool]:
    if not isinstance(compatibility, SchemaCompatibility):
        raise TypeError("compatibility must be SchemaCompatibility")
    expected_id = require_text_value(expected_schema_id, path="expected_schema_id")
    current = (
        current_version
        if isinstance(current_version, SchemaVersion)
        else SchemaVersion.parse(current_version)
    )
    context = validation_context(source=source, schema_id=expected_id)
    root = require_object(document, path="$", context=context)
    schema_id = require_string(root, "schema_id", path="$", context=context)
    if schema_id != expected_id:
        context.fail(
            "$.schema_id",
            f"expected {expected_id!r}, received {schema_id!r}",
        )
    version_text = require_string(
        root,
        "schema_version",
        path="$",
        context=context,
    )
    version = parse_schema_version(
        version_text,
        path="$.schema_version",
        context=context,
    )
    if version.major != current.major:
        context.unsupported(
            "$.schema_version",
            f"unsupported major version {version.major}; supported major is {current.major}",
        )
    if version.minor > current.minor and compatibility is SchemaCompatibility.STRICT:
        context.unsupported(
            "$.schema_version",
            f"unsupported minor version {version.minor}; current minor is {current.minor}",
        )
    allow_unknown = (
        compatibility is SchemaCompatibility.FORWARD_MINOR
        and version.major == current.major
        and version.minor > current.minor
    )
    return root, version, allow_unknown


def validate_fields(
    value: Mapping[str, object],
    *,
    required: Iterable[str] = (),
    optional: Iterable[str] = (),
    path: str,
    context: ValidationContext | None = None,
    allow_unknown: bool = False,
) -> None:
    if type(allow_unknown) is not bool:
        raise TypeError("allow_unknown must be bool")
    required_set = _field_set(required, name="required")
    optional_set = _field_set(optional, name="optional")
    overlap = required_set.intersection(optional_set)
    if overlap:
        raise ValueError("required and optional fields overlap: " + ", ".join(sorted(overlap)))
    actual = set(value)
    missing = required_set.difference(actual)
    if missing:
        _fail(
            context,
            path,
            "missing required fields: " + ", ".join(sorted(missing)),
        )
    if not allow_unknown:
        unknown = actual.difference(required_set | optional_set)
        if unknown:
            _fail(
                context,
                path,
                "contains unknown fields: " + ", ".join(sorted(unknown)),
            )


def require_object(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(context, path, "must be an object")
    if len(value) > _MAX_CONTAINER_ITEMS:
        _fail(context, path, "contains too many fields")
    for key in value:
        if not isinstance(key, str):
            _fail(context, path, "contains a non-string key")
        if not key or "\x00" in key:
            _fail(context, path, "contains an invalid field name")
    return cast("Mapping[str, object]", value)


def require_array_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        _fail(context, path, "must be an array")
    if len(value) > _MAX_CONTAINER_ITEMS:
        _fail(context, path, "contains too many items")
    return cast("Sequence[object]", value)


def require_field(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> object:
    checked_key = require_text_value(key, path="field key")
    if checked_key not in parent:
        _fail(context, path, f"missing required field {checked_key!r}")
    return parent[checked_key]


def optional_field(
    parent: Mapping[str, object],
    key: str,
) -> object | None:
    checked_key = require_text_value(key, path="field key")
    return parent.get(checked_key)


def require_object_field(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> Mapping[str, object]:
    return require_object(
        require_field(parent, key, path=path, context=context),
        path=json_path(path, key),
        context=context,
    )


def require_array(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> Sequence[object]:
    return require_array_value(
        require_field(parent, key, path=path, context=context),
        path=json_path(path, key),
        context=context,
    )


def require_string_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_empty: bool = False,
    max_length: int = _MAX_SCHEMA_TEXT,
) -> str:
    if not isinstance(value, str):
        _fail(context, path, "must be a string")
    if "\x00" in value:
        _fail(context, path, "must not contain NUL")
    if not allow_empty and not value.strip():
        _fail(context, path, "must not be empty")
    if len(value) > max_length:
        _fail(context, path, f"exceeds maximum length {max_length}")
    return value


def require_string(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_empty: bool = False,
    max_length: int = _MAX_SCHEMA_TEXT,
) -> str:
    return require_string_value(
        require_field(parent, key, path=path, context=context),
        path=json_path(path, key),
        context=context,
        allow_empty=allow_empty,
        max_length=max_length,
    )


def optional_string(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_null: bool = True,
    allow_empty: bool = False,
    max_length: int = _MAX_SCHEMA_TEXT,
) -> str | None:
    if key not in parent:
        return None
    value = parent[key]
    if value is None and allow_null:
        return None
    return require_string_value(
        value,
        path=json_path(path, key),
        context=context,
        allow_empty=allow_empty,
        max_length=max_length,
    )


def require_bool_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> bool:
    if type(value) is not bool:
        _fail(context, path, "must be a boolean")
    return value


def require_bool(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> bool:
    return require_bool_value(
        require_field(parent, key, path=path, context=context),
        path=json_path(path, key),
        context=context,
    )


def optional_bool(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_null: bool = True,
) -> bool | None:
    if key not in parent:
        return None
    value = parent[key]
    if value is None and allow_null:
        return None
    return require_bool_value(
        value,
        path=json_path(path, key),
        context=context,
    )


def require_integer_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if type(value) is not int:
        _fail(context, path, "must be an integer")
    checked = value
    if minimum is not None and checked < minimum:
        _fail(context, path, f"must be at least {minimum}")
    if maximum is not None and checked > maximum:
        _fail(context, path, f"must be at most {maximum}")
    return checked


def require_integer(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    return require_integer_value(
        require_field(parent, key, path=path, context=context),
        path=json_path(path, key),
        context=context,
        minimum=minimum,
        maximum=maximum,
    )


def optional_integer(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_null: bool = True,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    if key not in parent:
        return None
    value = parent[key]
    if value is None and allow_null:
        return None
    return require_integer_value(
        value,
        path=json_path(path, key),
        context=context,
        minimum=minimum,
        maximum=maximum,
    )


def require_number_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> int | float:
    if type(value) not in (int, float):
        _fail(context, path, "must be a number")
    checked = cast("int | float", value)
    if isinstance(checked, float) and not math.isfinite(checked):
        _fail(context, path, "must be finite")
    if minimum is not None and checked < minimum:
        _fail(context, path, f"must be at least {minimum}")
    if maximum is not None and checked > maximum:
        _fail(context, path, f"must be at most {maximum}")
    return checked


def require_enum_value(
    value: object,
    allowed: Iterable[str],
    *,
    path: str,
    context: ValidationContext | None = None,
) -> str:
    checked = require_string_value(value, path=path, context=context)
    allowed_set = _field_set(allowed, name="allowed")
    if checked not in allowed_set:
        _fail(
            context,
            path,
            "must be one of: " + ", ".join(sorted(allowed_set)),
        )
    return checked


def require_enum(
    parent: Mapping[str, object],
    key: str,
    allowed: Iterable[str],
    *,
    path: str,
    context: ValidationContext | None = None,
) -> str:
    return require_enum_value(
        require_field(parent, key, path=path, context=context),
        allowed,
        path=json_path(path, key),
        context=context,
    )


def require_string_array(
    parent: Mapping[str, object],
    key: str,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_empty_items: bool = False,
    unique: bool = False,
    max_items: int = _MAX_CONTAINER_ITEMS,
) -> tuple[str, ...]:
    items = require_array(parent, key, path=path, context=context)
    array_path = json_path(path, key)
    if len(items) > max_items:
        _fail(context, array_path, f"contains more than {max_items} items")
    result = tuple(
        require_string_value(
            item,
            path=json_index(array_path, index),
            context=context,
            allow_empty=allow_empty_items,
        )
        for index, item in enumerate(items)
    )
    if unique:
        validate_unique(result, path=array_path, context=context)
    return result


def validate_rfc3339_utc(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> str:
    checked = require_string_value(value, path=path, context=context)
    match = _RFC3339_UTC_PATTERN.fullmatch(checked)
    if match is None:
        _fail(context, path, "must be an RFC 3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(checked.removesuffix("Z") + "+00:00")
    except ValueError:
        _fail(context, path, "contains an invalid calendar timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        _fail(context, path, "must identify UTC")
    return checked


def validate_sha256(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
) -> str:
    checked = require_string_value(value, path=path, context=context)
    if _SHA256_PATTERN.fullmatch(checked) is None:
        _fail(context, path, "must be 64 lowercase hexadecimal SHA-256 characters")
    return checked


def validate_portable_relative_path(
    value: object,
    *,
    path: str,
    context: ValidationContext | None = None,
    allow_dot: bool = False,
) -> str:
    checked = require_string_value(value, path=path, context=context)
    if "\\" in checked:
        _fail(context, path, "must use forward-slash separators")
    if checked.startswith("/") or checked.startswith("//"):
        _fail(context, path, "must be relative")
    if _WINDOWS_DRIVE_PATTERN.match(checked):
        _fail(context, path, "must not contain a drive prefix")
    windows = PureWindowsPath(checked)
    if windows.is_absolute() or windows.drive or windows.root:
        _fail(context, path, "must be a portable relative path")
    candidate = PurePosixPath(checked)
    if candidate.is_absolute():
        _fail(context, path, "must be relative")
    parts = candidate.parts
    if checked == "." and allow_dot:
        return checked
    if not parts or parts == (".",):
        _fail(context, path, "must identify a relative file or directory")
    for segment in parts:
        if segment in ("", ".", ".."):
            _fail(context, path, "contains a prohibited path segment")
        if segment.endswith((" ", ".")):
            _fail(context, path, "contains a segment ending in space or dot")
        if any(ord(character) < 32 or ord(character) == 127 for character in segment):
            _fail(context, path, "contains a control character")
        base = segment.split(".", 1)[0].upper()
        if base in _WINDOWS_RESERVED_NAMES:
            _fail(context, path, "contains a reserved Windows device name")
    return candidate.as_posix()


def validate_unique(
    values: Sequence[_T],
    *,
    path: str,
    context: ValidationContext | None = None,
    key: Callable[[_T], object] | None = None,
) -> None:
    identity = key or (lambda item: item)
    seen: dict[object, int] = {}
    for index, item in enumerate(values):
        marker = identity(item)
        try:
            previous = seen.get(marker)
        except TypeError:
            _fail(context, json_index(path, index), "has an unhashable identity")
        if previous is not None:
            _fail(
                context,
                json_index(path, index),
                f"duplicates item at index {previous}",
            )
        seen[marker] = index


def validate_order(
    values: Sequence[_T],
    *,
    path: str,
    context: ValidationContext | None = None,
    key: Callable[[_T], _K],
) -> None:
    if not callable(key):
        raise TypeError("key must be callable")
    for index in range(1, len(values)):
        current = key(values[index])
        previous = key(values[index - 1])
        try:
            out_of_order = current < previous
        except TypeError:
            _fail(context, json_index(path, index), "has non-comparable order keys")
        if out_of_order:
            _fail(
                context,
                json_index(path, index),
                "is not in canonical order",
            )


def validate_json_value(
    value: object,
    *,
    path: str = "$",
    context: ValidationContext | None = None,
) -> JsonValue:
    active: set[int] = set()
    return _validate_json_value(
        value,
        path=path,
        context=context,
        active=active,
        depth=0,
    )


def json_path(parent: str, key: str) -> str:
    checked_parent = require_text_value(parent, path="parent path")
    checked_key = require_text_value(key, path="field key")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", checked_key):
        return f"{checked_parent}.{checked_key}"
    escaped = checked_key.replace("\\", "\\\\").replace("'", "\\'")
    return f"{checked_parent}['{escaped}']"


def json_index(parent: str, index: int) -> str:
    checked_parent = require_text_value(parent, path="parent path")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a non-negative integer")
    return f"{checked_parent}[{index}]"


def require_text_value(
    value: object,
    *,
    path: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{path} must be a string")
    if not value.strip():
        raise ValueError(f"{path} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{path} must not contain NUL")
    return value


def _validate_json_value(
    value: object,
    *,
    path: str,
    context: ValidationContext | None,
    active: set[int],
    depth: int,
) -> JsonValue:
    if depth > _MAX_NESTING_DEPTH:
        _fail(context, path, "exceeds maximum nesting depth")
    if value is None or type(value) in (bool, int, str):
        if isinstance(value, str):
            if "\x00" in value:
                _fail(context, path, "contains NUL")
            if len(value) > _MAX_SCHEMA_TEXT:
                _fail(context, path, "exceeds maximum string length")
        return cast("JsonValue", value)
    if type(value) is float:
        if not math.isfinite(value):
            _fail(context, path, "contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        container_id = _enter(value, active, path, context)
        try:
            if len(value) > _MAX_CONTAINER_ITEMS:
                _fail(context, path, "contains too many fields")
            result: dict[str, JsonValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    _fail(context, path, "contains a non-string key")
                result[key] = _validate_json_value(
                    item,
                    path=json_path(path, key),
                    context=context,
                    active=active,
                    depth=depth + 1,
                )
            return result
        finally:
            active.remove(container_id)
    if isinstance(value, (list, tuple)):
        container_id = _enter(value, active, path, context)
        try:
            if len(value) > _MAX_CONTAINER_ITEMS:
                _fail(context, path, "contains too many items")
            return [
                _validate_json_value(
                    item,
                    path=json_index(path, index),
                    context=context,
                    active=active,
                    depth=depth + 1,
                )
                for index, item in enumerate(value)
            ]
        finally:
            active.remove(container_id)
    _fail(context, path, f"contains unsupported JSON type {type(value).__name__}")


def _enter(
    value: object,
    active: set[int],
    path: str,
    context: ValidationContext | None,
) -> int:
    container_id = id(value)
    if container_id in active:
        _fail(context, path, "contains a cycle")
    active.add(container_id)
    return container_id


def _field_set(values: Iterable[str], *, name: str) -> frozenset[str]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{name} must be an iterable of strings")
    result: set[str] = set()
    for value in values:
        checked = require_text_value(value, path=f"{name} field")
        result.add(checked)
    return frozenset(result)


def _fail(
    context: ValidationContext | None,
    path: str,
    message: str,
) -> Never:
    if context is None:
        raise SchemaValidationError(f"{path}: {message}")
    context.fail(path, message)


__all__ = (
    "JsonObject",
    "PathLike",
    "SchemaCompatibility",
    "SchemaIdentity",
    "SchemaVersion",
    "ValidationContext",
    "json_index",
    "json_path",
    "optional_bool",
    "optional_field",
    "optional_integer",
    "optional_string",
    "parse_schema_version",
    "require_array",
    "require_array_value",
    "require_bool",
    "require_bool_value",
    "require_enum",
    "require_enum_value",
    "require_field",
    "require_integer",
    "require_integer_value",
    "require_number_value",
    "require_object",
    "require_object_field",
    "require_string",
    "require_string_array",
    "require_string_value",
    "require_text_value",
    "validate_fields",
    "validate_json_value",
    "validate_order",
    "validate_portable_relative_path",
    "validate_rfc3339_utc",
    "validate_schema_identity",
    "validate_sha256",
    "validate_unique",
    "validation_context",
)
