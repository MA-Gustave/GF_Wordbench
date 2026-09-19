"""Unit tests for canonical declaration-notation scanning rules."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gf_wordbench.validation.scanning.masking import build_source_views
from gf_wordbench.validation.scanning.rules.declarations import (
    DECLARATION_RULES,
    DOUBLE_SLASH_DASH_RULE,
    SINGLE_SLASH_EQ_RULE,
    DeclarationFinding,
    DeclarationRule,
    DeclarationScanResult,
    count_double_slash_dash,
    count_single_slash_eq,
    scan_declaration_rules,
    scan_double_slash_dash,
    scan_single_slash_eq,
)


def _scan(source: str) -> DeclarationScanResult:
    views = build_source_views(source)
    return scan_declaration_rules(
        views.original_lines,
        views.string_masked_lines,
    )


def test_rule_registry_is_stable_ordered_and_canonical() -> None:
    assert DECLARATION_RULES == (
        SINGLE_SLASH_EQ_RULE,
        DOUBLE_SLASH_DASH_RULE,
    )
    assert DeclarationRule(
        rule_id="SCAN-NOTATION-001",
        field_name="single_slash_eq",
        count_unit="matching source line",
        default_interpretation=("suspicious single-backslash before '=>'"),
    ) == SINGLE_SLASH_EQ_RULE
    assert DeclarationRule(
        rule_id="SCAN-NOTATION-002",
        field_name="double_slash_dash",
        count_unit="matching source line",
        default_interpretation=("suspicious double-backslash before '->'"),
    ) == DOUBLE_SLASH_DASH_RULE
    assert len({rule.rule_id for rule in DECLARATION_RULES}) == len(DECLARATION_RULES)
    assert len({rule.field_name for rule in DECLARATION_RULES}) == len(DECLARATION_RULES)


def test_rule_and_result_models_are_frozen() -> None:
    finding = DeclarationFinding(
        rule_id="SCAN-NOTATION-001",
        field_name="single_slash_eq",
        line=1,
        column=1,
        end_column=4,
        excerpt=r"\x => x",
        message="Suspicious notation.",
    )
    result = DeclarationScanResult(single_slash_eq=(finding,))

    with pytest.raises(FrozenInstanceError):
        SINGLE_SLASH_EQ_RULE.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        finding.line = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.single_slash_eq = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value", "error_type", "message"),
    (
        ("rule_id", 1, TypeError, "rule_id must be a string"),
        ("field_name", None, TypeError, "field_name must be a string"),
        ("count_unit", "", ValueError, "count_unit must be non-empty"),
        (
            "default_interpretation",
            "bad\x00value",
            ValueError,
            "default_interpretation must be non-empty",
        ),
    ),
)
def test_declaration_rule_validates_all_fields(
    field_name: str,
    value: object,
    error_type: type[Exception],
    message: str,
) -> None:
    values: dict[str, object] = {
        "rule_id": "SCAN-NOTATION-999",
        "field_name": "example",
        "count_unit": "matching source line",
        "default_interpretation": "example interpretation",
    }
    values[field_name] = value

    with pytest.raises(error_type, match=message):
        DeclarationRule(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"rule_id": ""}, "rule_id must be a non-empty string"),
        ({"field_name": ""}, "field_name must be a non-empty string"),
        ({"line": 0}, "line must be a positive integer"),
        ({"line": True}, "line must be a positive integer"),
        ({"column": 0}, "column must be a positive integer"),
        ({"column": True}, "column must be a positive integer"),
        ({"end_column": 2}, "end_column must be an integer"),
        ({"end_column": True}, "end_column must be an integer"),
        ({"excerpt": "bad\x00excerpt"}, "excerpt must be a NUL-free string"),
        ({"message": " "}, "message must be a non-empty string"),
    ),
)
def test_declaration_finding_rejects_invalid_contract_values(
    overrides: dict[str, object],
    message: str,
) -> None:
    values: dict[str, object] = {
        "rule_id": "SCAN-NOTATION-001",
        "field_name": "single_slash_eq",
        "line": 1,
        "column": 3,
        "end_column": 7,
        "excerpt": r"\x => x",
        "message": "Suspicious notation.",
    }
    values.update(overrides)

    with pytest.raises(ValueError, match=message):
        DeclarationFinding(**values)  # type: ignore[arg-type]


def test_scan_result_requires_tuples_of_findings() -> None:
    finding = DeclarationFinding(
        rule_id="SCAN-NOTATION-001",
        field_name="single_slash_eq",
        line=1,
        column=1,
        end_column=4,
        excerpt=r"\x => x",
        message="Suspicious notation.",
    )

    with pytest.raises(TypeError, match="single_slash_eq must be a tuple"):
        DeclarationScanResult(single_slash_eq=[finding])  # type: ignore[arg-type]
    with pytest.raises(
        TypeError,
        match="double_slash_dash must contain DeclarationFinding objects",
    ):
        DeclarationScanResult(
            double_slash_dash=("not-a-finding",),  # type: ignore[arg-type]
        )


def test_empty_source_returns_zero_counts_and_no_findings() -> None:
    result = _scan("")

    assert result == DeclarationScanResult()
    assert result.findings == ()
    assert result.counts == {
        "single_slash_eq": 0,
        "double_slash_dash": 0,
    }
    assert count_single_slash_eq("") == 0
    assert count_double_slash_dash("") == 0


def test_single_slash_before_fat_arrow_is_reported_with_precise_evidence() -> None:
    source = r"oper bad = \x => x ;"

    result = _scan(source)

    assert len(result.single_slash_eq) == 1
    assert result.double_slash_dash == ()
    finding = result.single_slash_eq[0]
    assert finding.rule_id == "SCAN-NOTATION-001"
    assert finding.field_name == "single_slash_eq"
    assert finding.line == 1
    assert finding.column == source.index("\\") + 1
    assert finding.end_column == source.index("=>") + len("=>")
    assert finding.excerpt == source
    assert finding.message == (
        "Suspicious single backslash appears before '=>' in the same statement segment."
    )
    assert result.counts == {
        "single_slash_eq": 1,
        "double_slash_dash": 0,
    }


def test_double_slash_before_thin_arrow_is_reported_with_precise_evidence() -> None:
    source = r"oper bad = \\x -> x ;"

    result = _scan(source)

    assert result.single_slash_eq == ()
    assert len(result.double_slash_dash) == 1
    finding = result.double_slash_dash[0]
    assert finding.rule_id == "SCAN-NOTATION-002"
    assert finding.field_name == "double_slash_dash"
    assert finding.line == 1
    assert finding.column == source.index("\\") + 1
    assert finding.end_column == source.index("->") + len("->")
    assert finding.excerpt == source
    assert finding.message == (
        "Suspicious double backslash appears before '->' in the same statement segment."
    )
    assert result.counts == {
        "single_slash_eq": 0,
        "double_slash_dash": 1,
    }


def test_each_rule_counts_a_physical_line_at_most_once() -> None:
    source = "\n".join(
        (
            r"oper one = \x => x ; oper two = \y => y ;",
            r"oper three = \\x -> x ; oper four = \\y -> y ;",
        )
    )

    result = _scan(source)

    assert tuple(item.line for item in result.single_slash_eq) == (1,)
    assert tuple(item.line for item in result.double_slash_dash) == (2,)
    assert result.counts == {
        "single_slash_eq": 1,
        "double_slash_dash": 1,
    }


def test_multiple_physical_lines_are_counted_independently() -> None:
    source = "\r\n".join(
        (
            r"oper one = \x => x ;",
            r"oper safe = \x -> x ;",
            r"oper two = \y => y ;",
            r"oper three = \\z -> z ;",
        )
    )

    result = _scan(source)

    assert tuple(item.line for item in result.single_slash_eq) == (1, 3)
    assert tuple(item.line for item in result.double_slash_dash) == (4,)
    assert result.counts == {
        "single_slash_eq": 2,
        "double_slash_dash": 1,
    }


def test_comments_and_string_literals_do_not_trigger_notation_rules() -> None:
    source = "\n".join(
        (
            r'oper literalOne = "\x => x" ;',
            r'oper literalTwo = "\\x -> x" ;',
            r"-- oper commentedOne = \x => x ;",
            r"{- oper commentedTwo = \\x -> x ; -}",
            r"oper realOne = \x => x ; -- \\ignored -> ignored",
            r"oper realTwo = \\x -> x ;",
        )
    )

    result = _scan(source)

    assert tuple(item.line for item in result.single_slash_eq) == (5,)
    assert tuple(item.line for item in result.double_slash_dash) == (6,)


def test_arrow_order_exclusions_are_scoped_to_statement_segments() -> None:
    source = "\n".join(
        (
            r"oper safeSingle = \x -> x => y ;",
            r"oper safeDouble = \\x => x -> y ;",
            r"oper flaggedSingle = a -> b ; \x => x ;",
            r"oper flaggedDouble = a => b ; \\x -> x ;",
        )
    )

    result = _scan(source)

    assert tuple(item.line for item in result.single_slash_eq) == (3,)
    assert tuple(item.line for item in result.double_slash_dash) == (4,)


@pytest.mark.parametrize(
    "source",
    (
        r"oper safe = \x -> x ;",
        r"oper safe = \\x => x ;",
        r"oper safe = \\\x => x ;",
        r"oper safe = \\\x -> x ;",
        r"oper safe = \x ; later = y => y ;",
        r"oper safe = \\x ; later = y -> y ;",
    ),
)
def test_nonmatching_or_wrong_arity_forms_are_excluded(source: str) -> None:
    result = _scan(source)

    assert result.findings == ()
    assert result.counts == {
        "single_slash_eq": 0,
        "double_slash_dash": 0,
    }


def test_wrapper_functions_return_the_corresponding_finding_group() -> None:
    source = "\n".join(
        (
            r"oper one = \x => x ;",
            r"oper two = \\y -> y ;",
        )
    )
    views = build_source_views(source)

    complete = scan_declaration_rules(
        views.original_lines,
        views.string_masked_lines,
    )

    assert (
        scan_single_slash_eq(
            views.original_lines,
            views.string_masked_lines,
        )
        == complete.single_slash_eq
    )
    assert (
        scan_double_slash_dash(
            views.original_lines,
            views.string_masked_lines,
        )
        == complete.double_slash_dash
    )


def test_count_helpers_use_matching_source_lines_without_original_view() -> None:
    source = "\n".join(
        (
            r"oper one = \x => x ; oper repeated = \y => y ;",
            r"oper safe = \x -> x ;",
            r"oper two = \\x -> x ;",
            r"oper three = \\y -> y ;",
        )
    )
    masked_lines = build_source_views(source).string_masked_lines

    assert count_single_slash_eq(masked_lines) == 1
    assert count_double_slash_dash(masked_lines) == 2


def test_findings_property_groups_canonical_rule_results() -> None:
    source = "\n".join(
        (
            r"oper doubleFirst = \\x -> x ;",
            r"oper singleSecond = \x => x ;",
        )
    )

    result = _scan(source)

    assert result.findings == (
        *result.single_slash_eq,
        *result.double_slash_dash,
    )
    assert tuple(item.rule_id for item in result.findings) == (
        "SCAN-NOTATION-001",
        "SCAN-NOTATION-002",
    )


def test_original_excerpt_is_trimmed_and_bounded() -> None:
    source = "   " + r"\x => x" + ("a" * 300) + "   "

    finding = _scan(source).single_slash_eq[0]

    assert len(finding.excerpt) == 240
    assert finding.excerpt.startswith(r"\x => x")
    assert finding.excerpt.endswith("…")
    assert not finding.excerpt.startswith(" ")
    assert not finding.excerpt.endswith(" ")


def test_string_input_and_iterable_input_have_identical_semantics() -> None:
    lines = (
        "oper one = \\x => x ;\r\n",
        "oper two = \\\\y -> y ;\n",
    )
    masked = tuple(build_source_views(line).string_masked for line in lines)

    tuple_result = scan_declaration_rules(lines, masked)
    generator_result = scan_declaration_rules(
        (line for line in lines),
        (line for line in masked),
    )
    text_result = scan_declaration_rules(
        "".join(lines),
        "".join(masked),
    )

    assert tuple_result == generator_result == text_result
    assert tuple(item.line for item in text_result.findings) == (1, 2)


def test_source_views_must_have_equal_line_counts() -> None:
    with pytest.raises(
        ValueError,
        match="source views must contain the same number of lines",
    ):
        scan_declaration_rules(
            (r"oper one = \x => x ;", "second line"),
            (r"oper one = \x => x ;",),
        )


def test_source_views_must_preserve_character_alignment() -> None:
    with pytest.raises(
        ValueError,
        match=r"line 1 has lengths 20 and 19",
    ):
        scan_declaration_rules(
            (r"oper bad = \x => x ;",),
            (r"oper bad = \x => x;",),
        )


@pytest.mark.parametrize(
    ("original", "masked", "message"),
    (
        (b"source", (), "original_lines must contain text lines"),
        ((), bytearray(b"source"), "string_masked_lines must contain text lines"),
        (("ok", 1), ("ok", "x"), r"original_lines\[2\] must be a string"),
        (("ok",), (None,), r"string_masked_lines\[1\] must be a string"),
    ),
)
def test_scan_rejects_non_text_line_inputs(
    original: object,
    masked: object,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        scan_declaration_rules(original, masked)  # type: ignore[arg-type]


def test_scan_rejects_non_iterable_line_input() -> None:
    with pytest.raises(
        TypeError,
        match="original_lines must be text or an iterable of strings",
    ):
        scan_declaration_rules(42, ())  # type: ignore[arg-type]


def test_scan_rejects_nul_in_iterable_lines() -> None:
    with pytest.raises(
        ValueError,
        match=r"original_lines\[1\] must not contain NUL",
    ):
        scan_declaration_rules(("bad\x00line",), ("bad line",))


def test_count_helpers_share_line_input_validation() -> None:
    with pytest.raises(
        TypeError,
        match="string_masked_lines must contain text lines",
    ):
        count_single_slash_eq(b"not text lines")  # type: ignore[arg-type]

    with pytest.raises(
        ValueError,
        match=r"string_masked_lines\[1\] must not contain NUL",
    ):
        count_double_slash_dash(("bad\x00line",))
