"""Unit tests for brace-balanced structural static-scan rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from gf_wordbench.validation.scanning.masking import build_source_views
from gf_wordbench.validation.scanning.rules.structure import (
    RUNTIME_STRING_MATCH_COUNT_FIELD,
    RUNTIME_STRING_MATCH_RULE_ID,
    UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD,
    UNTYPED_CASE_STRING_PATTERN_RULE_ID,
    UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD,
    UNTYPED_TABLE_STRING_PATTERN_RULE_ID,
    StructuralBlockKind,
    StructureDiagnostic,
    StructureDiagnosticCode,
    StructureFinding,
    StructureRuleResult,
    collect_structural_blocks,
    contains_explicit_str_pattern_type,
    contains_string_concatenation_pattern,
    contains_string_literal_branch,
    scan_structure_rules,
)


@dataclass(frozen=True, slots=True)
class _AlignedViews:
    """Line-oriented adapter for the structural-rule protocol."""

    original_lines: tuple[str, ...]
    comment_stripped_lines: tuple[str, ...]
    string_masked_lines: tuple[str, ...]


def _views(source: str) -> _AlignedViews:
    masked = build_source_views(source)
    return _AlignedViews(
        original_lines=tuple(masked.original.splitlines()),
        comment_stripped_lines=tuple(masked.comment_stripped.splitlines()),
        string_masked_lines=tuple(masked.string_masked.splitlines()),
    )


def test_literal_and_concatenation_predicates_cover_canonical_forms() -> None:
    assert contains_string_literal_branch('"yes" => True') is True
    assert contains_string_literal_branch('x + "yes" => x') is True
    assert contains_string_literal_branch("_ => True") is False

    assert contains_string_concatenation_pattern('prefix + "-x" => prefix') is True
    assert contains_string_concatenation_pattern('"x-" + suffix => suffix') is True
    assert contains_string_concatenation_pattern("prefix => prefix") is False

    assert contains_explicit_str_pattern_type('prefix + "x" : Str > => prefix') is True
    assert contains_explicit_str_pattern_type('prefix + "x" => prefix') is False


@pytest.mark.parametrize(
    "value",
    (None, b'"x" => y', 7),
)
def test_text_predicates_reject_non_strings(value: object) -> None:
    with pytest.raises(TypeError, match="value must be a string"):
        contains_string_literal_branch(value)  # type: ignore[arg-type]


def test_collects_balanced_case_and_table_blocks_with_exact_locations() -> None:
    source = """lin choose = case record.s of {
  \"yes\" => True ;
  _ => False
} ;
oper suffix : Str => Str = table {
  stem + \"s\" => stem ;
  _ => \"\"
} ;"""

    blocks = collect_structural_blocks(_views(source))

    assert blocks.diagnostics == ()
    assert len(blocks.case_blocks) == 1
    assert len(blocks.table_blocks) == 1

    case_block = blocks.case_blocks[0]
    assert case_block.kind is StructuralBlockKind.CASE
    assert (case_block.start_line, case_block.end_line) == (1, 4)
    assert case_block.start_column == 14
    assert case_block.header_text == "case record.s of {"
    assert '"yes" => True' in case_block.source_text
    assert '"yes"' not in case_block.structural_text

    table_block = blocks.table_blocks[0]
    assert table_block.kind is StructuralBlockKind.TABLE
    assert (table_block.start_line, table_block.end_line) == (5, 8)
    assert table_block.header_text == "table {"
    assert 'stem + "s" => stem' in table_block.source_text


def test_runtime_string_match_requires_s_projection_and_literal_branch() -> None:
    positive = """lin choose = case record.s of {
  \"yes\" => True ;
  _ => False
} ;"""
    without_projection = positive.replace("record.s", "record")
    without_literal_branch = positive.replace('"yes" =>', "Yes =>")

    positive_result = scan_structure_rules(_views(positive))
    assert positive_result.runtime_str_match == 1
    finding = positive_result.findings[0]
    assert finding.rule_id == RUNTIME_STRING_MATCH_RULE_ID
    assert finding.count_field == RUNTIME_STRING_MATCH_COUNT_FIELD
    assert (finding.start_line, finding.end_line) == (1, 4)

    assert scan_structure_rules(_views(without_projection)).runtime_str_match == 0
    assert scan_structure_rules(_views(without_literal_branch)).runtime_str_match == 0


def test_case_string_concatenation_requires_explicit_pattern_type() -> None:
    untyped = """lin normalize = case value of {
  stem + \"s\" => stem ;
  _ => value
} ;"""
    typed = untyped.replace('stem + "s" =>', 'stem + "s" : Str > =>')

    untyped_result = scan_structure_rules(_views(untyped))
    assert untyped_result.untyped_case_str_pat == 1
    assert untyped_result.findings[0].rule_id == (
        UNTYPED_CASE_STRING_PATTERN_RULE_ID
    )
    assert untyped_result.findings[0].count_field == (
        UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD
    )

    typed_result = scan_structure_rules(_views(typed))
    assert typed_result.untyped_case_str_pat == 0
    assert typed_result.findings == ()


def test_table_string_concatenation_requires_explicit_pattern_type() -> None:
    untyped = """oper suffix : Str => Str = table {
  stem + \"s\" => stem ;
  _ => \"\"
} ;"""
    typed = untyped.replace('stem + "s" =>', 'stem + "s" : Str > =>')

    untyped_result = scan_structure_rules(_views(untyped))
    assert untyped_result.untyped_table_str_pat == 1
    assert untyped_result.findings[0].rule_id == (
        UNTYPED_TABLE_STRING_PATTERN_RULE_ID
    )
    assert untyped_result.findings[0].count_field == (
        UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD
    )

    assert scan_structure_rules(_views(typed)).untyped_table_str_pat == 0


def test_one_case_block_can_emit_runtime_and_pattern_findings() -> None:
    source = """lin normalize = case value.s of {
  stem + \"s\" => stem ;
  _ => value.s
} ;"""

    result = scan_structure_rules(_views(source))

    assert tuple(finding.rule_id for finding in result.findings) == (
        RUNTIME_STRING_MATCH_RULE_ID,
        UNTYPED_CASE_STRING_PATTERN_RULE_ID,
    )
    assert result.counts() == {
        RUNTIME_STRING_MATCH_COUNT_FIELD: 1,
        UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD: 1,
        UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD: 0,
    }


def test_keywords_and_braces_inside_comments_or_strings_are_ignored() -> None:
    source = '''lin literal = "case record.s of { \\"yes\\" => True }" ;
-- case record.s of { "yes" => True }
{- table { stem + "s" => stem } -}
lin ordinary = ordinary ;'''

    result = scan_structure_rules(_views(source))

    assert result.findings == ()
    assert result.diagnostics == ()


def test_nested_braces_and_masked_braces_do_not_end_case_early() -> None:
    source = """lin choose = case record.s of {
  \"}\" => table {
    \"x\" => {s = \"ok\"} ;
    _ => {s = \"fallback\"}
  } ;
  _ => {s = \"none\"}
} ;"""

    blocks = collect_structural_blocks(_views(source))

    assert blocks.diagnostics == ()
    assert len(blocks.case_blocks) == 1
    assert len(blocks.table_blocks) == 1
    assert blocks.case_blocks[0].end_line == 7
    assert blocks.table_blocks[0].end_line == 5


def test_case_header_limit_is_reported_without_creating_a_block() -> None:
    source = """lin choose = case record
  line2
  line3
  line4
  of {
    _ => False
  } ;"""

    blocks = collect_structural_blocks(
        _views(source),
        max_case_header_lines=3,
    )

    assert blocks.case_blocks == ()
    assert blocks.diagnostics == (
        StructureDiagnostic(
            code=StructureDiagnosticCode.CASE_HEADER_LIMIT,
            kind=StructuralBlockKind.CASE,
            start_line=1,
            end_line=3,
            message=(
                "Case header did not reach a code-visible 'of {' "
                "within the configured header bound."
            ),
        ),
    )


def test_unbalanced_case_is_diagnostic_but_nested_balanced_table_is_kept() -> None:
    source = """lin choose = case record of {
  _ => table {
    _ => value ;
  } ;"""

    blocks = collect_structural_blocks(_views(source))

    assert blocks.case_blocks == ()
    assert len(blocks.table_blocks) == 1
    assert tuple(diagnostic.code for diagnostic in blocks.diagnostics) == (
        StructureDiagnosticCode.UNBALANCED_BLOCK,
    )
    assert blocks.diagnostics[0].kind is StructuralBlockKind.CASE
    assert (blocks.diagnostics[0].start_line, blocks.diagnostics[0].end_line) == (
        1,
        4,
    )


def test_block_line_limit_fails_boundedly() -> None:
    source = """lin choose = case record of {
  First => one ;
  Second => two ;
  _ => fallback
} ;"""

    blocks = collect_structural_blocks(
        _views(source),
        max_block_lines=2,
    )

    assert blocks.case_blocks == ()
    assert len(blocks.diagnostics) == 1
    diagnostic = blocks.diagnostics[0]
    assert diagnostic.code is StructureDiagnosticCode.BLOCK_LINE_LIMIT
    assert diagnostic.kind is StructuralBlockKind.CASE
    assert (diagnostic.start_line, diagnostic.end_line) == (1, 3)


def test_findings_preserve_source_path_and_bound_excerpt() -> None:
    source = """lin normalize = case value.s of {
  stem + \"s\" => stem ;
  Other => other ;
  Another => another ;
  _ => value.s
} ;"""
    source_path = Path("lib/src/Fixture.gf")

    result = scan_structure_rules(
        _views(source),
        source_path=source_path,
        max_excerpt_lines=2,
        max_excerpt_chars=52,
    )

    assert len(result.findings) == 2
    for finding in result.findings:
        assert finding.source_path == source_path
        assert finding.excerpt.endswith("\n…")
        assert len(finding.excerpt) <= 52
        assert finding.excerpt.startswith("lin normalize = case value.s of {")


def test_result_sorts_findings_by_rule_then_location_and_counts_them() -> None:
    later_runtime = StructureFinding(
        rule_id=RUNTIME_STRING_MATCH_RULE_ID,
        count_field=RUNTIME_STRING_MATCH_COUNT_FIELD,
        source_path=None,
        start_line=20,
        end_line=22,
        start_column=1,
        excerpt="runtime later",
        message="runtime",
    )
    earlier_runtime = StructureFinding(
        rule_id=RUNTIME_STRING_MATCH_RULE_ID,
        count_field=RUNTIME_STRING_MATCH_COUNT_FIELD,
        source_path=None,
        start_line=2,
        end_line=4,
        start_column=1,
        excerpt="runtime earlier",
        message="runtime",
    )
    case_pattern = StructureFinding(
        rule_id=UNTYPED_CASE_STRING_PATTERN_RULE_ID,
        count_field=UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD,
        source_path=None,
        start_line=1,
        end_line=3,
        start_column=1,
        excerpt="case pattern",
        message="pattern",
    )

    result = StructureRuleResult(
        findings=(case_pattern, later_runtime, earlier_runtime),
        diagnostics=(),
    )

    assert result.findings == (
        earlier_runtime,
        later_runtime,
        case_pattern,
    )
    assert result.runtime_str_match == 2
    assert result.untyped_case_str_pat == 1
    assert result.untyped_table_str_pat == 0
    assert result.count_for("UNKNOWN-RULE") == 0


def test_structural_collection_rejects_misaligned_views() -> None:
    views = _AlignedViews(
        original_lines=("case value of {", "}"),
        comment_stripped_lines=("case value of {", "}"),
        string_masked_lines=("case value", "}"),
    )

    with pytest.raises(
        ValueError,
        match="string-masked view must preserve character alignment on line 1",
    ):
        collect_structural_blocks(views)


@pytest.mark.parametrize(
    ("keyword", "argument"),
    (
        ("max_case_header_lines", 0),
        ("max_block_lines", -1),
        ("max_excerpt_lines", False),
        ("max_excerpt_chars", 0),
    ),
)
def test_public_bounds_must_be_positive_integers(
    keyword: str,
    argument: object,
) -> None:
    kwargs = {keyword: argument}

    with pytest.raises((TypeError, ValueError), match="must be (an integer|positive)"):
        scan_structure_rules(_views("lin x = x ;"), **kwargs)  # type: ignore[arg-type]
