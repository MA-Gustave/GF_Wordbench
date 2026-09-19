"""Pure helpers for canonical persisted-value serialization.

Schema and report modules remain responsible for selecting and ordering fields.
This module only converts explicitly supplied values into canonical JSON values;
it never traverses dataclasses, ``__dict__`` attributes, or arbitrary objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import json
import math
from pathlib import PurePath
from typing import Final, TypeAlias, TypeVar

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

_MappingKeyT = TypeVar("_MappingKeyT")

CANONICAL_JSON_INDENT: Final[int] = 2

__all__ = (
    "CANONICAL_JSON_INDENT",
    "JsonScalar",
    "JsonValue",
    "ProducerInfo",
    "dumps_canonical_json",
    "format_rfc3339_utc",
    "path_to_portable_string",
    "to_json_object",
    "to_json_value",
)


@dataclass(frozen=True, slots=True)
class ProducerInfo:
    """Stable identity of the component that produced a persisted artifact."""

    name: str
    version: str

    def __post_init__(self) -> None:
        _require_non_empty_text("name", self.name)
        _require_non_empty_text("version", self.version)


def format_rfc3339_utc(value: datetime) -> str:
    """Return an aware datetime as an RFC 3339 UTC timestamp.

    Naive datetimes are rejected because a serializer must not invent a
    timezone. Fractional seconds are retained when present.
    """

    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Canonical timestamps require a timezone-aware datetime")

    utc_value = value.astimezone(UTC)
    timespec = "microseconds" if utc_value.microsecond else "seconds"
    return utc_value.isoformat(timespec=timespec).removesuffix("+00:00") + "Z"


def path_to_portable_string(value: PurePath) -> str:
    """Return a path string with canonical forward-slash separators.

    Path ownership, root containment, and relative-base selection must already
    have been resolved by the owning path or schema component.
    """

    if not isinstance(value, PurePath):
        raise TypeError("value must be a pathlib.PurePath")

    serialized = value.as_posix()
    if "\x00" in serialized:
        raise ValueError("Paths containing NUL cannot be serialized")

    return serialized


def to_json_value(value: object) -> JsonValue:
    """Convert an explicitly selected value to a canonical JSON value.

    Supported runtime conversions are intentionally limited to documented
    boundary types. Mappings preserve their supplied field order; sets are
    converted to deterministically ordered arrays. Cyclic containers and
    non-finite floating-point values are rejected.
    """

    return _to_json_value(
        value,
        active_containers=set(),
    )


def to_json_object(
    value: Mapping[str, object],
) -> dict[str, JsonValue]:
    """Convert a mapping and require the canonical root-object shape."""

    if not isinstance(value, Mapping):
        raise TypeError("Canonical JSON documents require a mapping at the root")

    return _mapping_to_json(
        value,
        active_containers=set(),
    )


def dumps_canonical_json(
    value: Mapping[str, object],
) -> str:
    """Serialize one canonical JSON object as UTF-8-ready text.

    The returned text preserves Unicode, uses two-space indentation, contains
    LF line endings, rejects non-JSON numeric values, and ends with one LF.
    File encoding and atomic replacement remain infrastructure concerns.
    """

    return (
        json.dumps(
            to_json_object(value),
            ensure_ascii=False,
            allow_nan=False,
            indent=CANONICAL_JSON_INDENT,
        )
        + "\n"
    )


def _to_json_value(
    value: object,
    *,
    active_containers: set[int],
) -> JsonValue:
    if isinstance(value, Enum):
        enum_value = value.value
        if not isinstance(enum_value, str):
            raise TypeError(
                f"Canonical enums must expose string values, got {type(enum_value).__name__}"
            )
        return enum_value

    if isinstance(value, datetime):
        return format_rfc3339_utc(value)

    if isinstance(value, PurePath):
        return path_to_portable_string(value)

    if value is None or isinstance(value, (bool, str)):
        return value

    if isinstance(value, int):
        return int(value)

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN and infinite numbers are not valid canonical JSON")
        return float(value)

    if isinstance(value, Mapping):
        return _mapping_to_json(
            value,
            active_containers=active_containers,
        )

    if isinstance(value, (list, tuple)):
        return _sequence_to_json(
            value,
            active_containers=active_containers,
        )

    if isinstance(value, (set, frozenset)):
        converted = _sequence_to_json(
            value,
            active_containers=active_containers,
        )
        converted.sort(key=_deterministic_json_sort_key)
        return converted

    value_type = type(value)
    raise TypeError(
        "Unsupported canonical serialization type: "
        f"{value_type.__module__}.{value_type.__qualname__}"
    )


def _mapping_to_json(
    value: Mapping[_MappingKeyT, object],
    *,
    active_containers: set[int],
) -> dict[str, JsonValue]:
    container_id = _enter_container(
        value,
        active_containers,
    )

    try:
        result: dict[str, JsonValue] = {}

        for key, item in value.items():
            if isinstance(key, Enum) or not isinstance(key, str):
                raise TypeError("Canonical JSON object keys must be plain strings")

            result[key] = _to_json_value(
                item,
                active_containers=active_containers,
            )

        return result
    finally:
        active_containers.remove(container_id)


def _sequence_to_json(
    value: Iterable[object],
    *,
    active_containers: set[int],
) -> list[JsonValue]:
    container_id = _enter_container(
        value,
        active_containers,
    )

    try:
        return [
            _to_json_value(
                item,
                active_containers=active_containers,
            )
            for item in value
        ]
    finally:
        active_containers.remove(container_id)


def _enter_container(
    value: object,
    active_containers: set[int],
) -> int:
    container_id = id(value)

    if container_id in active_containers:
        raise ValueError("Cyclic structures cannot be serialized as canonical JSON")

    active_containers.add(container_id)
    return container_id


def _deterministic_json_sort_key(
    value: JsonValue,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_non_empty_text(
    name: str,
    value: object,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")

    if not value.strip():
        raise ValueError(f"{name} must not be empty")

    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL characters")
