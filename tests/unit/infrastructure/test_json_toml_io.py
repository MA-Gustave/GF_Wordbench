"""Unit tests for strict JSON and canonical TOML infrastructure I/O."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from enum import Enum
import math
from pathlib import Path, PureWindowsPath
import tomllib
from typing import cast

import pytest

from gf_wordbench.infrastructure.json_io import (
    JSON_ENCODING,
    JSON_INDENT,
    JsonObject,
    format_json,
    parse_json,
    read_json,
    write_json,
)
from gf_wordbench.infrastructure.toml_io import (
    dumps_canonical_toml,
    loads_toml,
    read_toml,
)
from gf_wordbench.kernel.errors import ContractViolationError, EvidenceIOError


class _TextMode(Enum):
    QUICK = "quick"


class _NumericMode(Enum):
    ONE = 1


def _assert_evidence_error(
    error: EvidenceIOError,
    *,
    message: str,
    operation: str,
    subject: str,
) -> None:
    assert error.message == message
    assert error.stage == "infrastructure"
    assert error.operation == operation
    assert error.subject == subject


def test_json_public_format_constants_are_canonical() -> None:
    assert JSON_ENCODING == "utf-8"
    assert JSON_INDENT == 2


def test_parse_json_preserves_order_unicode_and_nested_values() -> None:
    document = parse_json(
        '{"schema_id":"gf-wordbench.test","label":"élève","values":[1,true,null,{"z":2,"a":3}]}',
        source="memory.json",
    )

    assert tuple(document) == ("schema_id", "label", "values")
    assert document["label"] == "élève"
    assert document["values"] == [1, True, None, {"z": 2, "a": 3}]


@pytest.mark.parametrize(
    "text",
    [
        "[1, 2, 3]",
        '"text"',
        "42",
        "true",
        "null",
    ],
)
def test_parse_json_requires_an_object_root(text: str) -> None:
    with pytest.raises(EvidenceIOError) as captured:
        parse_json(text, source="root.json")

    _assert_evidence_error(
        captured.value,
        message="Canonical JSON documents must have one object at the root",
        operation="parse-json",
        subject="root.json",
    )


@pytest.mark.parametrize(
    "text",
    [
        '{"key":1,"key":2}',
        '{"outer":{"key":1,"key":2}}',
    ],
)
def test_parse_json_rejects_duplicate_object_keys(text: str) -> None:
    with pytest.raises(EvidenceIOError) as captured:
        parse_json(text, source="duplicate.json")

    error = captured.value
    _assert_evidence_error(
        error,
        message="JSON object contains a duplicate key",
        operation="parse-json",
        subject="duplicate.json",
    )
    assert "duplicate key" in error.detail


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_parse_json_rejects_non_finite_number_tokens(token: str) -> None:
    with pytest.raises(EvidenceIOError) as captured:
        parse_json(f'{{"value":{token}}}', source="number.json")

    error = captured.value
    _assert_evidence_error(
        error,
        message="JSON contains a prohibited non-finite number",
        operation="parse-json",
        subject="number.json",
    )
    assert token in error.detail


def test_parse_json_reports_bounded_syntax_location() -> None:
    with pytest.raises(EvidenceIOError) as captured:
        parse_json('{"value": ]}', source="broken.json")

    error = captured.value
    _assert_evidence_error(
        error,
        message="JSON document is malformed",
        operation="parse-json",
        subject="broken.json",
    )
    assert "line 1" in error.detail
    assert "column" in error.detail


def test_parse_json_rejects_decoded_surrogate_code_points() -> None:
    with pytest.raises(EvidenceIOError) as captured:
        parse_json(r'{"value":"\ud800"}', source="surrogate.json")

    _assert_evidence_error(
        captured.value,
        message="JSON document contains invalid Unicode data",
        operation="parse-json",
        subject="surrogate.json",
    )


@pytest.mark.parametrize(
    ("text", "source", "exception", "match"),
    [
        (cast("str", 1), "source", TypeError, "text must be a string"),
        ("{}", "", ValueError, "source must be a non-empty string"),
        ("{}", cast("str", 1), ValueError, "source must be a non-empty string"),
    ],
)
def test_parse_json_validates_public_arguments(
    text: str,
    source: str,
    exception: type[Exception],
    match: str,
) -> None:
    with pytest.raises(exception, match=match):
        parse_json(text, source=source)


def test_read_json_accepts_utf8_bom_and_crlf(tmp_path: Path) -> None:
    source = tmp_path / "legacy.json"
    source.write_bytes(b'\xef\xbb\xbf{\r\n  "label": "caf\xc3\xa9"\r\n}\r\n')

    assert read_json(source) == {"label": "café"}


def test_read_json_rejects_invalid_utf8(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_bytes(b'{"value":"\xff"}')

    with pytest.raises(EvidenceIOError) as captured:
        read_json(source)

    _assert_evidence_error(
        captured.value,
        message="JSON document is not valid UTF-8",
        operation="decode-json",
        subject=str(source),
    )


def test_read_json_enforces_exact_byte_limit(tmp_path: Path) -> None:
    source = tmp_path / "bounded.json"
    payload = b'{"value":1}'
    source.write_bytes(payload)

    assert read_json(source, max_bytes=len(payload)) == {"value": 1}

    with pytest.raises(EvidenceIOError) as captured:
        read_json(source, max_bytes=len(payload) - 1)

    error = captured.value
    _assert_evidence_error(
        error,
        message="JSON document exceeds the configured size limit",
        operation="read-json",
        subject=str(source),
    )
    assert f"limit: {len(payload) - 1} bytes" == error.detail


@pytest.mark.parametrize("limit", [-1, True, 1.5, "10"])
def test_read_json_rejects_invalid_size_limits(tmp_path: Path, limit: object) -> None:
    source = tmp_path / "document.json"
    source.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="max_bytes"):
        read_json(source, max_bytes=limit)  # type: ignore[arg-type]


def test_read_json_wraps_filesystem_failure_with_retry_context(tmp_path: Path) -> None:
    source = tmp_path / "missing.json"

    with pytest.raises(EvidenceIOError) as captured:
        read_json(source)

    error = captured.value
    _assert_evidence_error(
        error,
        message="Unable to read JSON document",
        operation="read-json",
        subject=str(source),
    )
    assert error.retryable is True
    assert error.__cause__ is not None
    assert isinstance(error.__cause__, OSError)


def test_format_json_is_utf8_ready_ordered_and_newline_terminated() -> None:
    document: JsonObject = {
        "schema_id": "gf-wordbench.test",
        "label": "élève",
        "nested": {"z": 2, "a": 1},
    }

    rendered = format_json(document)

    assert rendered == (
        "{\n"
        '  "schema_id": "gf-wordbench.test",\n'
        '  "label": "élève",\n'
        '  "nested": {\n'
        '    "z": 2,\n'
        '    "a": 1\n'
        "  }\n"
        "}\n"
    )
    assert rendered.encode(JSON_ENCODING).decode(JSON_ENCODING) == rendered


@pytest.mark.parametrize(
    ("document", "message"),
    [
        (cast("JsonObject", []), "one object at the root"),
        (cast("JsonObject", {1: "value"}), "keys must be strings"),
        (cast("JsonObject", {"value": object()}), "non-JSON value"),
        (cast("JsonObject", {"value": math.inf}), "non-finite number"),
        (cast("JsonObject", {"value": "\ud800"}), "cannot be encoded as UTF-8"),
    ],
)
def test_format_json_rejects_noncanonical_values(
    document: JsonObject,
    message: str,
) -> None:
    with pytest.raises(ContractViolationError, match=message) as captured:
        format_json(document)

    assert captured.value.stage == "infrastructure"
    assert captured.value.operation == "serialize-json"


def test_format_json_rejects_circular_containers() -> None:
    values: list[object] = []
    values.append(values)
    document = cast("JsonObject", {"values": values})

    with pytest.raises(ContractViolationError, match="circular reference"):
        format_json(document)


def test_write_json_atomically_publishes_canonical_bytes(tmp_path: Path) -> None:
    destination = tmp_path / "summary.json"
    destination.write_text('{"old":true}\n', encoding="utf-8")
    document: JsonObject = {"status": "OK", "label": "café"}

    returned = write_json(destination, document)

    assert returned == destination
    assert destination.read_bytes() == format_json(document).encode("utf-8")
    assert read_json(destination) == document
    assert not tuple(tmp_path.glob(f".{destination.name}.*.tmp"))


def test_write_json_does_not_replace_existing_file_when_formatting_fails(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "summary.json"
    original = b'{"status":"OLD"}\n'
    destination.write_bytes(original)

    with pytest.raises(ContractViolationError):
        write_json(destination, cast("JsonObject", {"value": math.nan}))

    assert destination.read_bytes() == original


def test_loads_toml_accepts_a_single_leading_bom() -> None:
    document = loads_toml('\ufeffname = "café"\n[tool]\nenabled = true\n')

    assert document == {"name": "café", "tool": {"enabled": True}}


def test_loads_toml_preserves_standard_library_syntax_failures() -> None:
    with pytest.raises(tomllib.TOMLDecodeError):
        loads_toml("value = [1,, 2]\n")


def test_read_toml_accepts_utf8_bom_and_crlf(tmp_path: Path) -> None:
    source = tmp_path / "project.toml"
    source.write_bytes(b'\xef\xbb\xbfproject_id = "demo"\r\n[validation]\r\nstrict = true\r\n')

    assert read_toml(source) == {
        "project_id": "demo",
        "validation": {"strict": True},
    }


def test_read_toml_preserves_decode_error_and_adds_path_note(tmp_path: Path) -> None:
    source = tmp_path / "invalid.toml"
    source.write_bytes(b'name = "\xff"')

    with pytest.raises(UnicodeDecodeError) as captured:
        read_toml(source)

    notes = getattr(captured.value, "__notes__", ())
    assert any(str(source) in note for note in notes)


def test_read_toml_preserves_syntax_error_and_adds_path_note(tmp_path: Path) -> None:
    source = tmp_path / "invalid.toml"
    source.write_text("value = [1,, 2]\n", encoding="utf-8")

    with pytest.raises(tomllib.TOMLDecodeError) as captured:
        read_toml(source)

    notes = getattr(captured.value, "__notes__", ())
    assert any(str(source) in note for note in notes)


def test_read_toml_preserves_filesystem_error_and_adds_path_note(
    tmp_path: Path,
) -> None:
    source = tmp_path / "missing.toml"

    with pytest.raises(FileNotFoundError) as captured:
        read_toml(source)

    notes = getattr(captured.value, "__notes__", ())
    assert any(str(source) in note for note in notes)


def test_dumps_canonical_toml_preserves_scalar_order_before_child_tables() -> None:
    document = {
        "project": {"z": 2, "a": "first"},
        "schema_version": "1.0",
        "enabled": True,
    }

    assert dumps_canonical_toml(document) == (
        'schema_version = "1.0"\nenabled = true\n\n[project]\nz = 2\na = "first"\n'
    )


def test_dumps_canonical_toml_quotes_keys_and_escapes_strings() -> None:
    rendered = dumps_canonical_toml(
        {
            "key with spaces": 'line1\nline2\t"quoted"\\end\x7f',
            "bare_key-1": "ok",
        }
    )

    assert rendered == (
        '"key with spaces" = "line1\\nline2\\t\\"quoted\\"\\\\end\\u007F"\nbare_key-1 = "ok"\n'
    )


def test_dumps_canonical_toml_renders_arrays_and_inline_tables() -> None:
    rendered = dumps_canonical_toml(
        {
            "values": [1, "two", True],
            "records": [{"name": "alpha", "count": 2}],
        }
    )

    assert rendered == (
        'values = [\n  1,\n  "two",\n  true,\n]\nrecords = [\n  { name = "alpha", count = 2 },\n]\n'
    )


def test_dumps_canonical_toml_renders_supported_semantic_scalars() -> None:
    local = datetime(
        2026,
        7,
        25,
        12,
        34,
        56,
        123456,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    rendered = dumps_canonical_toml(
        {
            "mode": _TextMode.QUICK,
            "path": PureWindowsPath(r"C:\GF Root\Language.gf"),
            "timestamp": local,
            "day": date(2026, 7, 25),
            "clock": time(12, 34, 56, 123456),
        }
    )

    assert rendered == (
        'mode = "quick"\n'
        'path = "C:/GF Root/Language.gf"\n'
        "timestamp = 2026-07-25T16:34:56.123456Z\n"
        "day = 2026-07-25\n"
        "clock = 12:34:56.123456\n"
    )


def test_dumps_canonical_toml_round_trips_supported_document() -> None:
    document = {
        "schema_id": "gf-wordbench.project",
        "enabled": True,
        "limits": [1, 2, 3],
        "project": {
            "project_id": "demo",
            "ratio": 1.5,
        },
    }

    rendered = dumps_canonical_toml(document)

    assert rendered.endswith("\n")
    assert "\r" not in rendered
    assert not rendered.startswith("\ufeff")
    assert loads_toml(rendered) == document


@pytest.mark.parametrize(
    ("document", "exception", "match"),
    [
        ({"value": None}, TypeError, "TOML has no null value"),
        ({"value": {1, 2}}, TypeError, "Sets must be converted"),
        ({"value": object()}, TypeError, "Unsupported canonical TOML type"),
        ({"value": math.nan}, ValueError, "non-finite floats"),
        ({"value": math.inf}, ValueError, "non-finite floats"),
        ({"value": datetime(2026, 7, 25, 12, 0)}, ValueError, "timezone-aware"),
        (
            {"value": time(12, 0, tzinfo=UTC)},
            ValueError,
            "must not carry a timezone",
        ),
        ({"value": "\ud800"}, ValueError, "surrogate code points"),
        ({"value": _NumericMode.ONE}, TypeError, "string values"),
    ],
)
def test_dumps_canonical_toml_rejects_unsupported_values(
    document: dict[str, object],
    exception: type[Exception],
    match: str,
) -> None:
    with pytest.raises(exception, match=match):
        dumps_canonical_toml(document)


@pytest.mark.parametrize(
    "document",
    [
        cast("dict[str, object]", {1: "value"}),
        cast("dict[str, object]", {_TextMode.QUICK: "value"}),
        {"table": cast("dict[str, object]", {1: "value"})},
        {"items": [cast("dict[str, object]", {1: "value"})]},
    ],
)
def test_dumps_canonical_toml_requires_plain_string_keys(
    document: dict[str, object],
) -> None:
    with pytest.raises(TypeError, match="keys must be plain strings"):
        dumps_canonical_toml(document)


def test_dumps_canonical_toml_rejects_cyclic_mapping() -> None:
    document: dict[str, object] = {}
    document["self"] = document

    with pytest.raises(ValueError, match="Cyclic structures"):
        dumps_canonical_toml(document)


def test_dumps_canonical_toml_rejects_cyclic_array() -> None:
    values: list[object] = []
    values.append(values)

    with pytest.raises(ValueError, match="Cyclic structures"):
        dumps_canonical_toml({"values": values})


def test_empty_toml_document_has_one_final_newline() -> None:
    assert dumps_canonical_toml({}) == "\n"
