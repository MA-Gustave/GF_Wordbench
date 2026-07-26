"""Contract-focused tests for non-destructive diagnostic deduplication."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import SimpleNamespace

import pytest

from gf_wordbench.diagnostics.parsing.deduplication import (
    DiagnosticOccurrence,
    deduplicate_diagnostics,
    deduplicated_records,
    diagnostic_duplicate_key,
    diagnostic_occurrence,
    duplicate_groups,
    normalize_source_path,
)


@dataclass(frozen=True, slots=True)
class _Record:
    record_id: str
    pattern_id: str = "GF-DIAG-COMPILE-TYPE"
    error_kind: str = "TYPE"
    normalized_signature: str | None = "type mismatch"
    message: str = "type mismatch"
    source_path: Path | str | None = Path("src/Main.gf")
    source_module: str | None = "Main"
    symbol: str | None = "value"
    line: int | None = 12
    column: int | None = 4
    origin: str | None = "gf"
    severity: str | None = "error"
    detail: str | None = "expected A, got B"
    expected: str | None = "A"
    actual: str | None = "B"
    expected_type: str | None = None
    actual_type: str | None = None
    assertion_id: str | None = None
    artifact_role: str | None = None
    blocker: str | None = None
    blocked_by: str | None = None
    execution_state: str | None = "completed"
    is_fatal: bool = False
    is_warning: bool = False
    is_unknown: bool = False
    stream: str = "stderr"
    start_line: int = 3
    end_line: int = 4
    raw_artifact_path: Path | None = Path("raw/compile.stderr.txt")
    raw_excerpt: str = "Main.gf:12:4: type mismatch"


def _record(index: int, **changes: object) -> _Record:
    base = _Record(record_id=f"diag-{index:016x}")
    return replace(base, **changes)


def test_empty_input_produces_an_empty_stable_view() -> None:
    result = deduplicate_diagnostics(())

    assert result.records == ()
    assert result.groups == ()
    assert result.representatives == ()
    assert result.duplicate_occurrence_count == 0
    assert not result.has_duplicates


def test_equivalent_records_collapse_without_losing_occurrences() -> None:
    first = _record(1, raw_excerpt="first raw occurrence")
    second = _record(
        2,
        stream="stdout",
        start_line=20,
        end_line=20,
        raw_artifact_path=Path("raw/compile.stdout.txt"),
        raw_excerpt="second raw occurrence",
    )

    result = deduplicate_diagnostics((first, second))

    assert result.records == (first, second)
    assert result.representatives == (first,)
    assert result.duplicate_occurrence_count == 1
    assert result.has_duplicates
    assert len(result.groups) == 1

    group = result.groups[0]
    assert group.representative is first
    assert group.occurrences == (first, second)
    assert group.record_ids == (first.record_id, second.record_id)
    assert group.streams == ("stderr", "stdout")
    assert group.occurrence_count == 2
    assert group.is_duplicate
    assert tuple(item.raw_excerpt for item in group.provenance) == (
        "first raw occurrence",
        "second raw occurrence",
    )
    assert tuple(item.raw_artifact_path for item in group.provenance) == (
        Path("raw/compile.stderr.txt"),
        Path("raw/compile.stdout.txt"),
    )


def test_representative_is_the_first_occurrence_not_stream_priority() -> None:
    stdout_first = _record(1, stream="stdout", start_line=1, end_line=1)
    stderr_second = _record(2, stream="stderr", start_line=2, end_line=2)

    group = deduplicate_diagnostics((stdout_first, stderr_second)).groups[0]

    assert group.representative is stdout_first
    assert group.occurrences == (stdout_first, stderr_second)
    assert group.streams == ("stderr", "stdout")


def test_interleaved_duplicates_preserve_original_record_order() -> None:
    first_a = _record(1, normalized_signature="A", message="A")
    record_b = _record(2, normalized_signature="B", message="B")
    second_a = _record(
        3,
        normalized_signature="A",
        message="A",
        start_line=30,
        end_line=30,
    )

    result = deduplicate_diagnostics((first_a, record_b, second_a))

    assert result.records == (first_a, record_b, second_a)
    assert result.representatives == (first_a, record_b)
    assert result.groups[0].occurrences == (first_a, second_a)
    assert result.groups[1].occurrences == (record_b,)


def test_helper_views_share_the_same_stable_grouping_policy() -> None:
    first = _record(1)
    duplicate = _record(2, start_line=50, end_line=50)
    distinct = _record(3, normalized_signature="different", message="different")
    records = (first, duplicate, distinct)

    assert deduplicated_records(records) == (first, distinct)
    groups = duplicate_groups(records)
    assert len(groups) == 1
    assert groups[0].occurrences == (first, duplicate)


@pytest.mark.parametrize(
    ("field_name", "different_value"),
    [
        ("expected", "DifferentExpected"),
        ("actual", "DifferentActual"),
        ("expected_type", "ExpectedType"),
        ("actual_type", "ActualType"),
        ("assertion_id", "ASSERT-002"),
        ("artifact_role", "pgf"),
        ("blocker", "missing_dependency"),
        ("blocked_by", "diag-dependency"),
        ("execution_state", "timed_out"),
        ("source_module", "OtherModule"),
        ("symbol", "otherSymbol"),
        ("origin", "wrapper"),
        ("severity", "fatal"),
        ("detail", "semantically different detail"),
        ("is_fatal", True),
        ("is_warning", True),
        ("is_unknown", True),
    ],
)
def test_semantically_distinct_diagnostics_are_never_merged(
    field_name: str,
    different_value: object,
) -> None:
    first = _record(1)
    second = replace(
        _record(2),
        **{field_name: different_value},
    )

    result = deduplicate_diagnostics((first, second))

    assert result.representatives == (first, second)
    assert all(not group.is_duplicate for group in result.groups)


def test_source_location_dimensions_prevent_semantic_merging() -> None:
    base = _record(1)
    records = (
        base,
        _record(2, source_path=Path("src/Other.gf")),
        _record(3, line=13),
        _record(4, column=5),
        _record(5, pattern_id="GF-DIAG-COMPILE-OTHER"),
        _record(6, error_kind="SYNTAX"),
    )

    result = deduplicate_diagnostics(records)

    assert result.representatives == records
    assert len(result.groups) == len(records)


def test_known_root_normalization_collapses_windows_path_variants() -> None:
    first = _record(
        1,
        source_path=PureWindowsPath(r"C:\Work\GF\project\src\Main.gf"),
    )
    second = _record(
        2,
        source_path=r"c:/work/gf/project/src/Main.gf",
        start_line=30,
        end_line=30,
    )

    result = deduplicate_diagnostics(
        (first, second),
        known_roots=(PureWindowsPath(r"C:\Work\GF\project"),),
    )

    assert result.representatives == (first,)
    assert result.groups[0].key.source_path_normalized == "src/Main.gf"


def test_longest_known_root_wins_without_filesystem_access() -> None:
    normalized = normalize_source_path(
        PureWindowsPath(r"C:\Work\GF\project\src\Main.gf"),
        known_roots=(
            PureWindowsPath(r"C:\Work"),
            PureWindowsPath(r"C:\Work\GF\project"),
        ),
    )

    assert normalized == "src/Main.gf"


def test_posix_path_normalization_is_lexical_and_preserves_case() -> None:
    normalized = normalize_source_path(
        PurePosixPath("/workspace/project/src/Été.gf"),
        known_roots=(PurePosixPath("/workspace/project"),),
    )

    assert normalized == "src/Été.gf"


def test_message_fallback_normalizes_only_nonsemantic_whitespace() -> None:
    first = _record(
        1,
        normalized_signature=None,
        message="  Unknown   constructor\tFoo  ",
    )
    second = _record(
        2,
        normalized_signature=None,
        message="Unknown constructor Foo",
        start_line=40,
        end_line=40,
    )

    result = deduplicate_diagnostics((first, second))

    assert result.representatives == (first,)
    assert result.groups[0].key.normalized_signature.startswith(
        "Unknown constructor Foo"
    )


def test_meaningful_numbers_and_language_text_remain_in_the_identity() -> None:
    first = _record(
        1,
        normalized_signature=None,
        message="Expected 2 arguments for constructor Chien",
    )
    second = _record(
        2,
        normalized_signature=None,
        message="Expected 3 arguments for constructor Chien",
    )
    third = _record(
        3,
        normalized_signature=None,
        message="Expected 2 arguments for constructor Chat",
    )

    result = deduplicate_diagnostics((first, second, third))

    assert result.representatives == (first, second, third)


def test_duplicate_key_is_deterministic_for_mapping_order() -> None:
    first = _record(1)
    second = _record(2)
    first_view = SimpleNamespace(
        **{
            field: getattr(first, field)
            for field in first.__dataclass_fields__
            if field != "expected"
        },
        expected={"b": 2, "a": 1},
    )
    second_view = SimpleNamespace(
        **{
            field: getattr(second, field)
            for field in second.__dataclass_fields__
            if field != "expected"
        },
        expected={"a": 1, "b": 2},
    )

    assert diagnostic_duplicate_key(first_view) == diagnostic_duplicate_key(
        second_view
    )


def test_occurrence_extraction_preserves_exact_raw_evidence_reference() -> None:
    record = _record(
        1,
        stream="stdout",
        start_line=7,
        end_line=9,
        raw_artifact_path=Path("raw/scenario.stdout.txt"),
        raw_excerpt="line 7\nline 8\nline 9",
    )

    occurrence = diagnostic_occurrence(record)

    assert occurrence == DiagnosticOccurrence(
        record_id=record.record_id,
        stream="stdout",
        start_line=7,
        end_line=9,
        raw_artifact_path=Path("raw/scenario.stdout.txt"),
        raw_excerpt="line 7\nline 8\nline 9",
    )


def test_occurrence_accepts_legacy_evidence_path_field() -> None:
    record = SimpleNamespace(
        record_id="diag-0000000000000001",
        stream="stderr",
        start_line=2,
        end_line=2,
        evidence_path=Path("raw/evidence.txt"),
        raw_excerpt="failure",
    )

    occurrence = diagnostic_occurrence(record)

    assert occurrence.raw_artifact_path == Path("raw/evidence.txt")


@pytest.mark.parametrize(
    "invalid_records",
    ["not records", b"not records"],
)
def test_record_collection_rejects_scalar_text(invalid_records: object) -> None:
    with pytest.raises(TypeError, match="iterable of diagnostic records"):
        deduplicate_diagnostics(invalid_records)  # type: ignore[arg-type]


def test_missing_required_record_fields_fail_explicitly() -> None:
    with pytest.raises(TypeError, match="missing required field 'pattern_id'"):
        diagnostic_duplicate_key(SimpleNamespace())


def test_source_path_rejects_non_path_values() -> None:
    with pytest.raises(TypeError, match="source_path"):
        normalize_source_path(42)


def test_occurrence_rejects_an_inverted_line_range() -> None:
    with pytest.raises(ValueError, match="end_line must not precede start_line"):
        DiagnosticOccurrence(
            record_id="diag-0000000000000001",
            stream="stderr",
            start_line=4,
            end_line=3,
            raw_artifact_path=None,
            raw_excerpt="",
        )
