"""Unit tests for canonical persisted-value serialization."""

from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import pytest

from gf_wordbench.kernel import serialization
from gf_wordbench.kernel.serialization import (
    CANONICAL_JSON_INDENT,
    ProducerInfo,
    dumps_canonical_json,
    format_rfc3339_utc,
    path_to_portable_string,
    to_json_object,
    to_json_value,
)

_EXPECTED_PUBLIC_NAMES = (
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


class _TextEnum(StrEnum):
    READY = "ready"
    FAILED = "failed"


class _PlainTextEnum(Enum):
    FIRST = "first"


class _NumericEnum(Enum):
    ONE = 1


@dataclass
class _ArbitraryDataclass:
    value: str


def test_module_exposes_only_the_canonical_public_contract() -> None:
    assert serialization.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(serialization, name) for name in serialization.__all__)
    assert CANONICAL_JSON_INDENT == 2


def test_producer_info_is_frozen_slotted_and_value_comparable() -> None:
    producer = ProducerInfo(name="gf-wordbench", version="1.2.3")

    assert producer == ProducerInfo(name="gf-wordbench", version="1.2.3")
    assert producer.name == "gf-wordbench"
    assert producer.version == "1.2.3"
    assert not hasattr(producer, "__dict__")

    with pytest.raises(FrozenInstanceError):
        producer.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["name", "version"])
@pytest.mark.parametrize("value", ["", "   ", "bad\x00value"])
def test_producer_info_rejects_empty_or_nul_text(
    field: str,
    value: str,
) -> None:
    arguments = {
        "name": "gf-wordbench",
        "version": "1.2.3",
    }
    arguments[field] = value

    with pytest.raises(ValueError, match=field):
        ProducerInfo(**arguments)


@pytest.mark.parametrize("field", ["name", "version"])
@pytest.mark.parametrize("value", [None, 1, Path("producer")])
def test_producer_info_rejects_non_string_fields(
    field: str,
    value: object,
) -> None:
    arguments: dict[str, Any] = {
        "name": "gf-wordbench",
        "version": "1.2.3",
    }
    arguments[field] = value

    with pytest.raises(TypeError, match=field):
        ProducerInfo(**arguments)


def test_rfc3339_formatter_converts_offsets_to_utc_seconds() -> None:
    source = datetime(
        2026,
        7,
        25,
        12,
        34,
        56,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    assert format_rfc3339_utc(source) == "2026-07-25T16:34:56Z"


def test_rfc3339_formatter_preserves_microseconds_when_present() -> None:
    source = datetime(
        2026,
        7,
        25,
        12,
        34,
        56,
        123_400,
        tzinfo=UTC,
    )

    assert format_rfc3339_utc(source) == "2026-07-25T12:34:56.123400Z"


@pytest.mark.parametrize(
    ("value", "error_type", "message"),
    [
        ("2026-07-25T12:00:00Z", TypeError, "datetime"),
        (datetime(2026, 7, 25, 12, 0), ValueError, "timezone-aware"),
    ],
)
def test_rfc3339_formatter_rejects_invalid_values(
    value: object,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        format_rfc3339_utc(value)  # type: ignore[arg-type]


def test_portable_path_serialization_uses_forward_slashes() -> None:
    assert path_to_portable_string(
        PureWindowsPath(r"C:\workspace\project\src\Main.gf")
    ) == "C:/workspace/project/src/Main.gf"
    assert path_to_portable_string(
        PureWindowsPath(r"project\src\Main.gf")
    ) == "project/src/Main.gf"
    assert path_to_portable_string(
        PurePosixPath("project/src/Main.gf")
    ) == "project/src/Main.gf"


def test_portable_path_serialization_rejects_invalid_values() -> None:
    with pytest.raises(TypeError, match="PurePath"):
        path_to_portable_string("project/src/Main.gf")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="NUL"):
        path_to_portable_string(PurePosixPath("project/bad\x00name.gf"))


def test_json_value_converts_all_documented_boundary_types() -> None:
    value = OrderedDict(
        (
            ("none", None),
            ("boolean", True),
            ("integer", 7),
            ("floating", 2.5),
            ("text", "élève"),
            ("enum", _TextEnum.READY),
            ("plain_enum", _PlainTextEnum.FIRST),
            ("timestamp", datetime(2026, 7, 25, 12, 0, tzinfo=UTC)),
            ("path", PureWindowsPath(r"raw\compile\Main.stderr.log")),
            ("tuple", ("first", 2)),
            ("list", [False, 3.0]),
            ("set", {"β", "z", "a"}),
            ("frozen_set", frozenset({10, 2, 1})),
        )
    )

    converted = to_json_value(value)

    assert converted == {
        "none": None,
        "boolean": True,
        "integer": 7,
        "floating": 2.5,
        "text": "élève",
        "enum": "ready",
        "plain_enum": "first",
        "timestamp": "2026-07-25T12:00:00Z",
        "path": "raw/compile/Main.stderr.log",
        "tuple": ["first", 2],
        "list": [False, 3.0],
        "set": ["a", "z", "β"],
        "frozen_set": [1, 10, 2],
    }
    assert list(converted) == list(value)


def test_mapping_order_is_preserved_and_containers_are_copied() -> None:
    nested = ["original"]
    source = OrderedDict(
        (
            ("zeta", nested),
            ("alpha", {"inner": (1, 2)}),
        )
    )

    converted = to_json_object(source)

    assert list(converted) == ["zeta", "alpha"]
    assert converted == {
        "zeta": ["original"],
        "alpha": {"inner": [1, 2]},
    }
    assert converted is not source
    assert converted["zeta"] is not nested

    nested.append("later")
    assert converted["zeta"] == ["original"]


def test_shared_noncyclic_container_is_allowed() -> None:
    shared = ["value"]

    assert to_json_value([shared, shared]) == [
        ["value"],
        ["value"],
    ]


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        {"nested": [float("nan")]},
    ],
)
def test_non_finite_numbers_are_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="NaN and infinite"):
        to_json_value(value)


def test_enums_must_expose_string_values() -> None:
    with pytest.raises(TypeError, match="string values"):
        to_json_value(_NumericEnum.ONE)


@pytest.mark.parametrize(
    "value",
    [
        b"bytes",
        bytearray(b"bytes"),
        complex(1, 2),
        _ArbitraryDataclass("value"),
        object(),
    ],
)
def test_unsupported_runtime_types_are_rejected(value: object) -> None:
    with pytest.raises(TypeError, match="Unsupported canonical serialization type"):
        to_json_value(value)


@pytest.mark.parametrize(
    "mapping",
    [
        {1: "integer key"},
        {_TextEnum.READY: "enum key"},
        {PurePosixPath("path"): "path key"},
    ],
)
def test_object_keys_must_be_plain_strings(mapping: dict[object, object]) -> None:
    with pytest.raises(TypeError, match="plain strings"):
        to_json_value(mapping)


def test_root_document_must_be_a_mapping() -> None:
    for value in (None, [], (), "text", 1):
        with pytest.raises(TypeError, match="mapping at the root"):
            to_json_object(value)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="mapping at the root"):
            dumps_canonical_json(value)  # type: ignore[arg-type]


def test_direct_self_referential_list_is_rejected() -> None:
    value: list[object] = []
    value.append(value)

    with pytest.raises(ValueError, match="Cyclic structures"):
        to_json_value(value)


def test_indirect_mapping_cycle_is_rejected() -> None:
    first: dict[str, object] = {}
    second: dict[str, object] = {"first": first}
    first["second"] = second

    with pytest.raises(ValueError, match="Cyclic structures"):
        to_json_object(first)


def test_cyclic_failure_does_not_poison_later_serialization() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    with pytest.raises(ValueError):
        to_json_value(cyclic)

    assert to_json_value([1, 2, 3]) == [1, 2, 3]


def test_canonical_json_text_preserves_unicode_order_and_formatting() -> None:
    document = OrderedDict(
        (
            ("producer", {"name": "gf-wordbench", "version": "1.2.3"}),
            ("message", "résultat β"),
            ("status", _TextEnum.READY),
            ("path", PureWindowsPath(r"raw\compile\Main.stdout.log")),
            ("generated_at", datetime(2026, 7, 25, 12, 0, tzinfo=UTC)),
        )
    )

    rendered = dumps_canonical_json(document)

    assert rendered == (
        "{\n"
        '  "producer": {\n'
        '    "name": "gf-wordbench",\n'
        '    "version": "1.2.3"\n'
        "  },\n"
        '  "message": "résultat β",\n'
        '  "status": "ready",\n'
        '  "path": "raw/compile/Main.stdout.log",\n'
        '  "generated_at": "2026-07-25T12:00:00Z"\n'
        "}\n"
    )
    assert "\\u00e9" not in rendered
    assert "\r" not in rendered
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")
    assert json.loads(rendered) == to_json_object(document)


def test_canonical_json_rejects_nonfinite_values_before_json_encoding() -> None:
    with pytest.raises(ValueError, match="NaN and infinite"):
        dumps_canonical_json({"value": float("nan")})
