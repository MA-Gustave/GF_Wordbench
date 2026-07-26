from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.validation.scenarios.markers import (
    BEGIN_MARKER_PREFIX,
    END_MARKER_PREFIX,
    MalformedMarker,
    MarkerEvent,
    MarkerIssue,
    MarkerIssueKind,
    MarkerIssueSeverity,
    MarkerKind,
    MarkerParseResult,
    MarkerState,
    MarkerValidationResult,
    UnexpectedMarkerPolicy,
    format_begin_marker,
    format_end_marker,
    parse_marker_events,
    validate_marker_events,
    validate_scenario_markers,
)
from gf_wordbench.validation.scenarios.models import ScenarioSectionResult


def _event(
    kind: MarkerKind,
    section_id: str,
    line_number: int,
) -> MarkerEvent:
    prefix = (
        BEGIN_MARKER_PREFIX
        if kind is MarkerKind.BEGIN
        else END_MARKER_PREFIX
    )
    return MarkerEvent(
        kind=kind,
        section_id=section_id,
        line_number=line_number,
        raw_line=f"{prefix} {section_id}",
    )


def _issue_kinds(result: MarkerValidationResult) -> tuple[MarkerIssueKind, ...]:
    return tuple(issue.kind for issue in result.issues)


def test_marker_prefixes_and_formatters_are_canonical() -> None:
    assert BEGIN_MARKER_PREFIX == "GF_WORDBENCH_BEGIN"
    assert END_MARKER_PREFIX == "GF_WORDBENCH_END"
    assert format_begin_marker("load-main") == (
        "GF_WORDBENCH_BEGIN load-main"
    )
    assert format_end_marker("load-main") == "GF_WORDBENCH_END load-main"


@pytest.mark.parametrize(
    "section_id",
    [
        "",
        "Load-main",
        "load_main",
        "load main",
        "load-main-",
        "1-load-main",
    ],
)
def test_marker_formatters_reject_noncanonical_section_ids(
    section_id: str,
) -> None:
    with pytest.raises(ValueError):
        format_begin_marker(section_id)
    with pytest.raises(ValueError):
        format_end_marker(section_id)


def test_parse_marker_events_ignores_unrelated_output_and_preserves_evidence(
) -> None:
    output = "\n".join(
        (
            "GF shell banner",
            "  GF_WORDBENCH_BEGIN load-main\t",
            "ordinary linguistic output",
            "\tGF_WORDBENCH_END load-main  ",
        )
    )

    parsed = parse_marker_events(output)

    assert parsed.malformed == ()
    assert parsed.events == (
        MarkerEvent(
            kind=MarkerKind.BEGIN,
            section_id="load-main",
            line_number=2,
            raw_line="  GF_WORDBENCH_BEGIN load-main\t",
        ),
        MarkerEvent(
            kind=MarkerKind.END,
            section_id="load-main",
            line_number=4,
            raw_line="\tGF_WORDBENCH_END load-main  ",
        ),
    )


@pytest.mark.parametrize(
    "raw_line",
    [
        "GF_WORDBENCH_BEGIN",
        "GF_WORDBENCH_END",
        "GF_WORDBENCH_BEGIN Load-main",
        "GF_WORDBENCH_BEGIN load_main",
        "GF_WORDBENCH_END load-main trailing",
        "GF_WORDBENCH_UNKNOWN load-main",
    ],
)
def test_parse_marker_events_reports_malformed_reserved_lines(
    raw_line: str,
) -> None:
    parsed = parse_marker_events(f"before\n{raw_line}\nafter")

    assert parsed.events == ()
    assert parsed.malformed == (
        MalformedMarker(
            line_number=2,
            raw_line=raw_line,
            message=(
                "marker line must be exactly "
                "'GF_WORDBENCH_BEGIN <section-id>' or "
                "'GF_WORDBENCH_END <section-id>'"
            ),
        ),
    )


def test_parse_marker_events_does_not_reserve_lowercase_normal_output() -> None:
    parsed = parse_marker_events(
        "gf_wordbench_begin load-main\n"
        "text containing GF_WORDBENCH_BEGIN load-main"
    )

    assert parsed == MarkerParseResult(events=(), malformed=())


def test_parse_marker_events_requires_text() -> None:
    with pytest.raises(TypeError, match="output must be a string"):
        parse_marker_events(b"GF_WORDBENCH_BEGIN load-main")  # type: ignore[arg-type]


def test_validate_scenario_markers_accepts_complete_ordered_sections(
    tmp_path: Path,
) -> None:
    raw_output_path = tmp_path / "scenario.stdout.txt"
    output = "\n".join(
        (
            "GF_WORDBENCH_BEGIN load-main",
            "loaded",
            "GF_WORDBENCH_END load-main",
            "GF_WORDBENCH_BEGIN parse-basic",
            "parsed",
            "GF_WORDBENCH_END parse-basic",
        )
    )

    result = validate_scenario_markers(
        output,
        ("load-main", "parse-basic"),
        raw_output_path=raw_output_path,
    )

    assert result.valid is True
    assert result.complete is True
    assert result.warnings == ()
    assert result.failures == ()
    assert result.raw_output_path == raw_output_path
    assert tuple(map(str, result.completed_section_ids)) == (
        "load-main",
        "parse-basic",
    )
    assert result.sections == (
        ScenarioSectionResult(
            id="load-main",
            completed=True,
            message="section completed",
            begin_line=1,
            end_line=3,
        ),
        ScenarioSectionResult(
            id="parse-basic",
            completed=True,
            message="section completed",
            begin_line=4,
            end_line=6,
        ),
    )


def test_validate_scenario_markers_reports_both_markers_missing() -> None:
    result = validate_scenario_markers("ordinary output", ("load-main",))

    assert result.valid is False
    assert result.complete is False
    assert _issue_kinds(result) == (
        MarkerIssueKind.MISSING_BEGIN,
        MarkerIssueKind.MISSING_END,
    )
    assert result.sections == (
        ScenarioSectionResult(
            id="load-main",
            completed=False,
            message="section 'load-main' has no begin marker",
        ),
    )


def test_validate_scenario_markers_reports_open_section_at_end_of_output(
) -> None:
    result = validate_scenario_markers(
        "GF_WORDBENCH_BEGIN load-main\npartial output",
        ("load-main",),
    )

    assert result.valid is False
    assert result.complete is False
    assert _issue_kinds(result) == (MarkerIssueKind.MISSING_END,)
    assert result.sections == (
        ScenarioSectionResult(
            id="load-main",
            completed=False,
            message="section 'load-main' has no end marker",
            begin_line=1,
        ),
    )


def test_end_before_begin_is_not_treated_as_completion() -> None:
    result = validate_scenario_markers(
        "GF_WORDBENCH_END load-main",
        ("load-main",),
    )

    assert result.valid is False
    assert result.complete is False
    assert _issue_kinds(result) == (
        MarkerIssueKind.END_BEFORE_BEGIN,
        MarkerIssueKind.MISSING_BEGIN,
        MarkerIssueKind.MISSING_END,
    )
    assert result.sections[0].completed is False
    assert result.sections[0].begin_line is None
    assert result.sections[0].end_line is None


def test_unexpected_markers_fail_by_default_without_corrupting_expected_state(
) -> None:
    result = validate_scenario_markers(
        "\n".join(
            (
                "GF_WORDBENCH_BEGIN extra",
                "GF_WORDBENCH_END extra",
                "GF_WORDBENCH_BEGIN load-main",
                "GF_WORDBENCH_END load-main",
            )
        ),
        ("load-main",),
    )

    assert result.valid is False
    assert result.complete is True
    assert _issue_kinds(result) == (
        MarkerIssueKind.UNEXPECTED_MARKER,
        MarkerIssueKind.UNEXPECTED_MARKER,
    )
    assert all(
        issue.severity is MarkerIssueSeverity.FAILURE
        for issue in result.issues
    )
    assert tuple(map(str, result.completed_section_ids)) == ("load-main",)


def test_unexpected_markers_can_be_warnings() -> None:
    result = validate_scenario_markers(
        "\n".join(
            (
                "GF_WORDBENCH_BEGIN extra",
                "GF_WORDBENCH_END extra",
                "GF_WORDBENCH_BEGIN load-main",
                "GF_WORDBENCH_END load-main",
            )
        ),
        ("load-main",),
        unexpected_policy=UnexpectedMarkerPolicy.WARN,
    )

    assert result.valid is True
    assert result.complete is True
    assert result.failures == ()
    assert len(result.warnings) == 2
    assert all(
        issue.kind is MarkerIssueKind.UNEXPECTED_MARKER
        for issue in result.warnings
    )


def test_malformed_reserved_line_is_a_protocol_failure() -> None:
    result = validate_scenario_markers(
        "\n".join(
            (
                "GF_WORDBENCH_BEGIN load-main",
                "GF_WORDBENCH_END load-main",
                "GF_WORDBENCH_BEGIN Load-main",
            )
        ),
        ("load-main",),
    )

    assert result.valid is False
    assert result.complete is True
    assert _issue_kinds(result) == (MarkerIssueKind.MALFORMED_MARKER,)
    assert result.failures[0].line_number == 3
    assert result.failures[0].section_id is None


def test_nested_sections_are_supported_only_when_explicitly_enabled() -> None:
    events = (
        _event(MarkerKind.BEGIN, "outer", 1),
        _event(MarkerKind.BEGIN, "inner", 2),
        _event(MarkerKind.END, "inner", 3),
        _event(MarkerKind.END, "outer", 4),
    )

    allowed = validate_marker_events(
        events,
        ("outer", "inner"),
        allow_nested=True,
    )

    assert allowed.valid is True
    assert allowed.complete is True
    assert tuple(map(str, allowed.completed_section_ids)) == (
        "outer",
        "inner",
    )


def test_nested_begin_is_reported_when_nesting_is_disabled() -> None:
    result = validate_marker_events(
        (
            _event(MarkerKind.BEGIN, "outer", 1),
            _event(MarkerKind.BEGIN, "inner", 2),
        ),
        ("outer", "inner"),
        allow_nested=False,
    )

    assert result.valid is False
    assert result.complete is False
    assert MarkerIssueKind.NESTED_SECTION in _issue_kinds(result)
    assert _issue_kinds(result).count(MarkerIssueKind.MISSING_END) == 2


def test_beginning_a_later_section_first_is_out_of_order() -> None:
    result = validate_marker_events(
        (_event(MarkerKind.BEGIN, "second", 1),),
        ("first", "second"),
    )

    assert result.valid is False
    assert result.complete is False
    assert _issue_kinds(result) == (
        MarkerIssueKind.OUT_OF_ORDER_SECTION,
        MarkerIssueKind.MISSING_BEGIN,
        MarkerIssueKind.MISSING_END,
        MarkerIssueKind.MISSING_END,
    )


def test_duplicate_begin_is_reported() -> None:
    result = validate_marker_events(
        (
            _event(MarkerKind.BEGIN, "load-main", 1),
            _event(MarkerKind.BEGIN, "load-main", 2),
        ),
        ("load-main",),
    )

    assert result.valid is False
    assert result.complete is False
    assert _issue_kinds(result) == (
        MarkerIssueKind.DUPLICATE_BEGIN,
        MarkerIssueKind.MISSING_END,
    )


def test_validate_marker_events_accepts_preparsed_malformed_evidence() -> None:
    malformed = MalformedMarker(
        line_number=7,
        raw_line="GF_WORDBENCH_BEGIN BAD",
        message="invalid marker",
    )
    result = validate_marker_events(
        (
            _event(MarkerKind.BEGIN, "load-main", 1),
            _event(MarkerKind.END, "load-main", 2),
        ),
        ("load-main",),
        malformed=(malformed,),
    )

    assert result.valid is False
    assert result.complete is True
    assert result.issues == (
        MarkerIssue(
            kind=MarkerIssueKind.MALFORMED_MARKER,
            severity=MarkerIssueSeverity.FAILURE,
            message="invalid marker",
            line_number=7,
        ),
    )


def test_empty_expected_section_list_accepts_output_without_reserved_markers(
) -> None:
    result = validate_scenario_markers("ordinary output", ())

    assert result.valid is True
    assert result.complete is True
    assert result.expected_section_ids == ()
    assert result.sections == ()
    assert result.completed_section_ids == ()


@pytest.mark.parametrize(
    ("expected", "exception", "message"),
    [
        ("load-main", TypeError, "iterable of section IDs"),
        (("load-main", "load-main"), ValueError, "must be unique"),
        (("Load-main",), ValueError, r"expected_section_ids\[0\]"),
    ],
)
def test_expected_section_ids_are_validated(
    expected: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        validate_marker_events((), expected)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("events", "exception", "message"),
    [
        ("events", TypeError, "iterable of MarkerEvent"),
        ((object(),), TypeError, "only MarkerEvent"),
        (
            (
                _event(MarkerKind.BEGIN, "load-main", 2),
                _event(MarkerKind.END, "load-main", 1),
            ),
            ValueError,
            "source line order",
        ),
    ],
)
def test_event_collection_is_validated(
    events: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        validate_marker_events(events, ())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("malformed", "message"),
    [
        ("malformed", "iterable of MalformedMarker"),
        ((object(),), "only MalformedMarker"),
    ],
)
def test_malformed_collection_is_validated(
    malformed: object,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        validate_marker_events(
            (),
            (),
            malformed=malformed,  # type: ignore[arg-type]
        )


def test_validation_options_require_exact_enum_and_bool_types() -> None:
    with pytest.raises(
        TypeError,
        match="unexpected_policy must be an UnexpectedMarkerPolicy",
    ):
        validate_marker_events(
            (),
            (),
            unexpected_policy="warn",  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="allow_nested must be a bool"):
        validate_marker_events((), (), allow_nested=1)  # type: ignore[arg-type]


def test_marker_event_and_malformed_marker_validate_evidence_fields() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        MarkerEvent(
            kind=MarkerKind.BEGIN,
            section_id="load-main",
            line_number=0,
            raw_line="GF_WORDBENCH_BEGIN load-main",
        )

    with pytest.raises(TypeError, match="raw_line must be a string"):
        MalformedMarker(
            line_number=1,
            raw_line=b"bad",  # type: ignore[arg-type]
            message="invalid marker",
        )

    with pytest.raises(ValueError, match="non-empty string"):
        MalformedMarker(
            line_number=1,
            raw_line="bad",
            message="",
        )


def test_marker_parse_result_requires_monotonic_source_order() -> None:
    with pytest.raises(ValueError, match="events must preserve source order"):
        MarkerParseResult(
            events=(
                _event(MarkerKind.BEGIN, "load-main", 2),
                _event(MarkerKind.END, "load-main", 1),
            ),
            malformed=(),
        )

    with pytest.raises(
        ValueError,
        match="malformed markers must preserve source order",
    ):
        MarkerParseResult(
            events=(),
            malformed=(
                MalformedMarker(2, "bad-two", "bad"),
                MalformedMarker(1, "bad-one", "bad"),
            ),
        )


def test_marker_issue_validates_optional_location() -> None:
    with pytest.raises(TypeError, match="kind must be a MarkerIssueKind"):
        MarkerIssue(
            kind="missing_end",  # type: ignore[arg-type]
            severity=MarkerIssueSeverity.FAILURE,
            message="missing",
        )

    with pytest.raises(ValueError, match="positive integer"):
        MarkerIssue(
            kind=MarkerIssueKind.MISSING_END,
            severity=MarkerIssueSeverity.FAILURE,
            message="missing",
            line_number=0,
        )


def test_marker_validation_result_requires_exact_expected_section_order() -> None:
    with pytest.raises(
        ValueError,
        match="section results must match expected section order exactly",
    ):
        MarkerValidationResult(
            expected_section_ids=("first", "second"),
            events=(),
            sections=(
                ScenarioSectionResult(id="second", completed=False),
                ScenarioSectionResult(id="first", completed=False),
            ),
            issues=(),
        )


def test_marker_state_values_are_stable() -> None:
    assert MarkerState.NOT_SEEN.value == "not_seen"
    assert MarkerState.OPEN.value == "open"
    assert MarkerState.COMPLETED.value == "completed"
