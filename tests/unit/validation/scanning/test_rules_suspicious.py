"""Unit tests for canonical suspicious-source scan detectors."""

from __future__ import annotations

import pytest

from gf_wordbench.validation.scanning.masking import build_source_views
from gf_wordbench.validation.scanning.rules.suspicious import (
    DOUBLE_SLASH_DASH_FIELD,
    RUNTIME_STR_MATCH_FIELD,
    SCAN_NOTATION_001,
    SCAN_NOTATION_002,
    SCAN_PATTERN_001,
    SCAN_PATTERN_002,
    SCAN_RUNTIME_001,
    SCAN_STYLE_001,
    SINGLE_SLASH_EQ_FIELD,
    TRAILING_SPACES_FIELD,
    UNTYPED_CASE_STR_PAT_FIELD,
    UNTYPED_TABLE_STR_PAT_FIELD,
    find_double_slash_dash,
    find_runtime_string_matches,
    find_single_slash_eq,
    find_trailing_spaces,
    find_untyped_case_string_patterns,
    find_untyped_table_string_patterns,
)


def _views(source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    views = build_source_views(source)
    return views.string_masked_lines, views.comment_stripped_lines


def _single_slash(source: str) -> tuple[tuple[int, int], ...]:
    structural, _ = _views(source)
    return find_single_slash_eq(structural)


def _double_slash(source: str) -> tuple[tuple[int, int], ...]:
    structural, _ = _views(source)
    return find_double_slash_dash(structural)


def _runtime(source: str) -> tuple[tuple[int, int], ...]:
    structural, content = _views(source)
    return find_runtime_string_matches(structural, content)


def _case_pattern(source: str) -> tuple[tuple[int, int], ...]:
    structural, content = _views(source)
    return find_untyped_case_string_patterns(structural, content)


def _table_pattern(source: str) -> tuple[tuple[int, int], ...]:
    structural, content = _views(source)
    return find_untyped_table_string_patterns(structural, content)


def test_rule_ids_and_scan_count_fields_are_stable() -> None:
    assert (
        SCAN_NOTATION_001,
        SCAN_NOTATION_002,
        SCAN_RUNTIME_001,
        SCAN_PATTERN_001,
        SCAN_PATTERN_002,
        SCAN_STYLE_001,
    ) == (
        "SCAN-NOTATION-001",
        "SCAN-NOTATION-002",
        "SCAN-RUNTIME-001",
        "SCAN-PATTERN-001",
        "SCAN-PATTERN-002",
        "SCAN-STYLE-001",
    )
    assert (
        SINGLE_SLASH_EQ_FIELD,
        DOUBLE_SLASH_DASH_FIELD,
        RUNTIME_STR_MATCH_FIELD,
        UNTYPED_CASE_STR_PAT_FIELD,
        UNTYPED_TABLE_STR_PAT_FIELD,
        TRAILING_SPACES_FIELD,
    ) == (
        "single_slash_eq",
        "double_slash_dash",
        "runtime_str_match",
        "untyped_case_str_pat",
        "untyped_table_str_pat",
        "trailing_spaces",
    )


def test_single_backslash_before_fat_arrow_matches_source_line() -> None:
    assert _single_slash("oper bad = \\x => x ;\n") == ((1, 1),)


def test_double_backslash_before_thin_arrow_matches_source_line() -> None:
    assert _double_slash("oper bad = \\\\x -> x ;\n") == ((1, 1),)


def test_notation_rules_count_lines_not_occurrences() -> None:
    source = "oper first = \\x => x ; second = \\y => y ;\noper third = \\z => z ;\n"

    assert _single_slash(source) == ((1, 1), (2, 2))


def test_notation_rules_respect_first_arrow_in_statement_segment() -> None:
    assert _single_slash("oper safe = \\x -> x => y ;\n") == ()
    assert _double_slash("oper safe = \\\\x => x -> y ;\n") == ()


def test_semicolon_starts_an_independent_notation_segment() -> None:
    source = "oper safe = \\x -> x ; bad = \\y => y ;\n"

    assert _single_slash(source) == ((1, 1),)


def test_single_and_double_backslash_rules_do_not_cross_match() -> None:
    assert _single_slash("oper x = \\\\y => y ;\n") == ()
    assert _double_slash("oper x = \\y -> y ;\n") == ()


def test_notation_like_text_in_comments_and_strings_is_ignored() -> None:
    source = (
        'oper text = "\\x => x and \\\\y -> y" ;\n'
        "-- \\comment => ignored\n"
        "{- \\\\comment -> ignored -}\n"
        "oper real = \\z => z ;\n"
    )

    assert _single_slash(source) == ((4, 4),)
    assert _double_slash(source) == ()


def test_runtime_string_match_requires_dot_s_and_literal_branch() -> None:
    source = 'oper f x = case x.s of {\n  "abc" => foo ;\n  _ => bar\n} ;\n'

    assert _runtime(source) == ((1, 4),)


def test_runtime_string_match_counts_block_once_with_multiple_literals() -> None:
    source = 'oper f x = case x.s of {\n  "a" => foo ;\n  "b" => bar ;\n  _ => baz\n} ;\n'

    assert _runtime(source) == ((1, 5),)


def test_runtime_string_match_rejects_missing_dot_s_or_literal_branch() -> None:
    no_projection = 'oper f x = case x of { "a" => foo ; _ => bar } ;\n'
    no_literal = "oper f x = case x.s of { A => foo ; _ => bar } ;\n"

    assert _runtime(no_projection) == ()
    assert _runtime(no_literal) == ()


def test_runtime_string_match_supports_multiline_case_header() -> None:
    source = 'oper f x = case\n  x.s\nof {\n  "abc" => foo ;\n  _ => bar\n} ;\n'

    assert _runtime(source) == ((1, 6),)


def test_two_separate_runtime_blocks_count_twice() -> None:
    source = (
        'oper a x = case x.s of { "a" => one ; _ => other } ;\n'
        'oper b x = case x.s of { "b" => two ; _ => other } ;\n'
    )

    assert _runtime(source) == ((1, 1), (2, 2))


def test_untyped_case_string_concatenation_pattern_matches() -> None:
    source = 'oper f stem = case stem of {\n  _ + "s" => mkN stem ;\n  _ => mkN stem\n} ;\n'

    assert _case_pattern(source) == ((1, 4),)


def test_untyped_table_string_concatenation_pattern_matches() -> None:
    source = 'oper endings = table {\n  "s" + _ => "plural" ;\n  _ => "other"\n} ;\n'

    assert _table_pattern(source) == ((1, 4),)


@pytest.mark.parametrize(
    "detector, source",
    [
        (
            _case_pattern,
            'oper f x = case x of { _ + "s" : Str > => one ; _ => two } ;\n',
        ),
        (
            _table_pattern,
            'oper f = table { "s" + _ : Str > => one ; _ => two } ;\n',
        ),
    ],
)
def test_explicit_str_pattern_type_exempts_block(
    detector: object,
    source: str,
) -> None:
    assert detector(source) == ()  # type: ignore[operator]


def test_pattern_detectors_accept_whitespace_variants() -> None:
    case_source = 'oper f x = case x of {\n  _+"s"=>one ;\n  _=>two\n} ;\n'
    table_source = 'oper f = table {\n  "s"+_=>one ;\n  _=>two\n} ;\n'

    assert _case_pattern(case_source) == ((1, 4),)
    assert _table_pattern(table_source) == ((1, 4),)


def test_pattern_like_text_in_comment_does_not_match() -> None:
    source = 'oper f x = case x of {\n  -- _ + "s" => fake ;\n  _ => real\n} ;\n'

    assert _case_pattern(source) == ()


def test_braces_inside_strings_and_comments_do_not_end_block() -> None:
    source = (
        "oper f x = case x.s of {\n"
        '  "a}" => one ; -- } ignored\n'
        "  {- } ignored -}\n"
        '  "b" => two\n'
        "} ;\n"
    )

    assert _runtime(source) == ((1, 5),)


def test_nested_braces_are_part_of_outer_block_span() -> None:
    source = (
        "oper f x = case x.s of {\n"
        '  "a" => table {\n'
        '    A => "{" ;\n'
        '    B => "}"\n'
        "  } ;\n"
        "  _ => fallback\n"
        "} ;\n"
    )

    assert _runtime(source) == ((1, 7),)


def test_nested_case_is_not_counted_independently_in_same_traversal() -> None:
    source = (
        "oper f x = case x.s of {\n"
        '  "outer" => case x.s of {\n'
        '    "inner" => one ;\n'
        "    _ => two\n"
        "  } ;\n"
        "  _ => three\n"
        "} ;\n"
    )

    assert _runtime(source) == ((1, 7),)


def test_unbalanced_case_block_is_not_reported() -> None:
    source = 'oper f x = case x.s of {\n  "a" => one ;\n  _ => two\n'

    assert _runtime(source) == ()
    assert _case_pattern(source) == ()


def test_closing_brace_without_opening_block_is_ignored() -> None:
    source = '} ; oper x = "a" ;\n'

    assert _runtime(source) == ()
    assert _case_pattern(source) == ()
    assert _table_pattern(source) == ()


def test_trailing_whitespace_counts_physical_lines_once() -> None:
    lines = (
        "one   \n",
        "two\t\n",
        "three\n",
        "four    ",
    )

    assert find_trailing_spaces(lines) == (
        (1, 1),
        (2, 2),
        (4, 4),
    )


def test_trailing_whitespace_applies_inside_comments_and_strings() -> None:
    lines = (
        "-- comment  \n",
        'oper text = "value"; \n',
    )

    assert find_trailing_spaces(lines) == ((1, 1), (2, 2))


def test_empty_input_returns_no_matches() -> None:
    assert find_single_slash_eq(()) == ()
    assert find_double_slash_dash(()) == ()
    assert find_runtime_string_matches((), ()) == ()
    assert find_untyped_case_string_patterns((), ()) == ()
    assert find_untyped_table_string_patterns((), ()) == ()
    assert find_trailing_spaces(()) == ()


@pytest.mark.parametrize(
    "function, arguments",
    [
        (find_single_slash_eq, ("not-lines",)),
        (find_double_slash_dash, (b"not-lines",)),
        (find_trailing_spaces, ("not-lines",)),
        (find_runtime_string_matches, ("bad", ())),
        (find_untyped_case_string_patterns, ((), "bad")),
        (find_untyped_table_string_patterns, ("bad", "bad")),
    ],
)
def test_detectors_reject_scalar_text_as_line_sequence(
    function: object,
    arguments: tuple[object, ...],
) -> None:
    with pytest.raises(TypeError, match="sequence of lines"):
        function(*arguments)  # type: ignore[operator]


def test_detectors_require_aligned_structural_and_content_views() -> None:
    with pytest.raises(ValueError, match="line-aligned"):
        find_runtime_string_matches(("case x of {\n",), ())


def test_detectors_reject_non_string_lines_and_nul() -> None:
    with pytest.raises(TypeError, match=r"string_masked_lines\[1\]"):
        find_single_slash_eq(("ok\n", 1))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"original_lines\[0\].*NUL"):
        find_trailing_spaces(("bad\x00line",))
