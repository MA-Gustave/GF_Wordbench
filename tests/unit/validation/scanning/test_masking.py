"""Unit tests for GF-aware lexical masking."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gf_wordbench.validation.scanning.masking import (
    MaskKind,
    MaskedSpan,
    MaskingIssue,
    MaskingIssueKind,
    SourceViews,
    build_source_views,
    mask_comments,
    mask_comments_and_strings,
    mask_source,
    mask_source_lines,
)


def _assert_aligned(source: str, *views: str) -> None:
    for view in views:
        assert len(view) == len(source)
        assert [index for index, char in enumerate(view) if char == "\n"] == [
            index for index, char in enumerate(source) if char == "\n"
        ]
        assert [index for index, char in enumerate(view) if char == "\r"] == [
            index for index, char in enumerate(source) if char == "\r"
        ]


def _only_span(views: SourceViews) -> MaskedSpan:
    assert len(views.spans) == 1
    return views.spans[0]


def _only_issue(views: SourceViews) -> MaskingIssue:
    assert len(views.issues) == 1
    return views.issues[0]


def test_empty_source_builds_empty_aligned_views() -> None:
    views = build_source_views("")

    assert views.original == ""
    assert views.comment_stripped == ""
    assert views.string_masked == ""
    assert views.spans == ()
    assert views.issues == ()
    assert views.original_lines == ()
    assert views.comment_stripped_lines == ()
    assert views.string_masked_lines == ()
    assert views.has_lexical_issues is False


def test_line_comment_after_code_masks_to_physical_line_end() -> None:
    source = "oper x = y ; -- suspicious =>\noper z = q ;\n"

    views = build_source_views(source)

    assert views.comment_stripped == (
        "oper x = y ;                 \noper z = q ;\n"
    )
    assert views.string_masked == views.comment_stripped
    _assert_aligned(source, views.comment_stripped, views.string_masked)

    span = _only_span(views)
    assert span.kind is MaskKind.LINE_COMMENT
    assert source[span.start_offset : span.end_offset] == "-- suspicious =>"
    assert (span.start_line, span.start_column) == (1, 14)
    assert span.end_line == 1
    assert span.terminated is True
    assert views.issues == ()


def test_line_comment_without_terminal_newline_is_closed_at_eof() -> None:
    source = "x -- comment"

    views = build_source_views(source)

    assert views.comment_stripped == "x           "
    span = _only_span(views)
    assert span.kind is MaskKind.LINE_COMMENT
    assert span.end_offset == len(source)
    assert span.terminated is True
    assert views.issues == ()


def test_crlf_boundaries_are_preserved_exactly() -> None:
    source = 'a -- comment\r\nb "text"\r\n'

    views = build_source_views(source)

    assert views.comment_stripped == 'a           \r\nb "text"\r\n'
    assert views.string_masked == "a           \r\nb       \r\n"
    assert views.original_lines == (
        "a -- comment\r\n",
        'b "text"\r\n',
    )
    assert views.comment_stripped_lines == (
        "a           \r\n",
        'b "text"\r\n',
    )
    assert views.string_masked_lines == (
        "a           \r\n",
        "b       \r\n",
    )
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_multiline_block_comment_is_masked_and_code_after_end_remains() -> None:
    source = "before {- first\nsecond -} after\n"

    views = build_source_views(source)

    assert views.comment_stripped == "before         \n          after\n"
    assert views.string_masked == views.comment_stripped
    span = _only_span(views)
    assert span.kind is MaskKind.BLOCK_COMMENT
    assert source[span.start_offset : span.end_offset] == "{- first\nsecond -}"
    assert (span.start_line, span.start_column) == (1, 8)
    assert span.end_line == 2
    assert span.terminated is True
    assert views.issues == ()


def test_nested_block_comment_markers_are_supported() -> None:
    source = "a {- outer {- nested -} outer -} b"

    views = build_source_views(source)

    assert views.comment_stripped == "a                                b"
    assert views.string_masked == views.comment_stripped
    span = _only_span(views)
    assert source[span.start_offset : span.end_offset] == (
        "{- outer {- nested -} outer -}"
    )
    assert span.terminated is True


def test_comment_delimiters_inside_string_are_not_comments() -> None:
    source = 'oper text = "-- {- still text -}" ; -- real comment\n'

    views = build_source_views(source)

    assert '"-- {- still text -}"' in views.comment_stripped
    assert "real comment" not in views.comment_stripped
    assert "--" not in views.string_masked
    assert "{-" not in views.string_masked
    assert [span.kind for span in views.spans] == [
        MaskKind.STRING,
        MaskKind.LINE_COMMENT,
    ]
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_braces_arrows_and_backslashes_inside_string_are_structurally_masked() -> None:
    source = 'oper example = "case x of { \\x => x ; y -> z }" ;\n'

    views = build_source_views(source)

    assert views.comment_stripped == source
    assert "case" not in views.string_masked
    assert "{" not in views.string_masked
    assert "}" not in views.string_masked
    assert "=>" not in views.string_masked
    assert "->" not in views.string_masked
    assert "\\" not in views.string_masked
    assert views.string_masked.endswith(" ;\n")
    assert _only_span(views).kind is MaskKind.STRING
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_backslash_escape_does_not_close_string_early() -> None:
    source = 'oper text = "a \\" quoted -- text" ; -- comment\n'

    views = build_source_views(source)

    assert [span.kind for span in views.spans] == [
        MaskKind.STRING,
        MaskKind.LINE_COMMENT,
    ]
    string_span, comment_span = views.spans
    assert source[string_span.start_offset : string_span.end_offset] == (
        '"a \\" quoted -- text"'
    )
    assert source[comment_span.start_offset : comment_span.end_offset] == (
        "-- comment"
    )
    assert views.issues == ()


def test_gf_doubled_quotes_keep_one_coherent_string_span() -> None:
    source = 'oper example = "case x of { ""a"" => y }" ;\n'

    views = build_source_views(source)

    span = _only_span(views)
    assert span.kind is MaskKind.STRING
    assert source[span.start_offset : span.end_offset] == (
        '"case x of { ""a"" => y }"'
    )
    assert "case" not in views.string_masked
    assert "=>" not in views.string_masked
    assert views.issues == ()


def test_string_ending_immediately_before_comment_marker() -> None:
    source = 'oper text = "value"-- comment\nnext\n'

    views = build_source_views(source)

    assert [span.kind for span in views.spans] == [
        MaskKind.STRING,
        MaskKind.LINE_COMMENT,
    ]
    assert views.comment_stripped == 'oper text = "value"          \nnext\n'
    assert views.string_masked == "oper text =                  \nnext\n"


def test_unicode_and_utf8_bom_are_preserved_outside_masked_regions() -> None:
    source = '\ufeffabstract Français = { oper élève = "café ☕" ; } -- été\n'

    views = build_source_views(source)

    assert views.comment_stripped.startswith("\ufeffabstract Français")
    assert "élève" in views.string_masked
    assert "café" in views.comment_stripped
    assert "café" not in views.string_masked
    assert "été" not in views.comment_stripped
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_unterminated_string_records_bounded_issue_and_span() -> None:
    source = 'oper text = "unterminated\ncontinued'

    views = build_source_views(source)

    span = _only_span(views)
    issue = _only_issue(views)
    assert span.kind is MaskKind.STRING
    assert span.terminated is False
    assert span.end_offset == len(source)
    assert (span.start_line, span.start_column) == (1, 13)
    assert issue.kind is MaskingIssueKind.UNTERMINATED_STRING
    assert (issue.line, issue.column, issue.offset) == (1, 13, 12)
    assert "Unterminated GF string literal" in issue.message
    assert views.has_lexical_issues is True
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_unterminated_block_comment_records_bounded_issue_and_span() -> None:
    source = "oper x = y ; {- unterminated\ncontinued"

    views = build_source_views(source)

    span = _only_span(views)
    issue = _only_issue(views)
    assert span.kind is MaskKind.BLOCK_COMMENT
    assert span.terminated is False
    assert span.end_offset == len(source)
    assert (span.start_line, span.start_column) == (1, 14)
    assert issue.kind is MaskingIssueKind.UNTERMINATED_BLOCK_COMMENT
    assert (issue.line, issue.column, issue.offset) == (1, 14, 13)
    assert "Unterminated GF block comment" in issue.message
    assert views.has_lexical_issues is True
    _assert_aligned(source, views.comment_stripped, views.string_masked)


def test_public_masking_helpers_are_consistent() -> None:
    source = 'x = "-- text" ; -- comment\ny = z ;\n'
    expected = build_source_views(source)

    assert mask_source(source) == expected
    assert mask_comments(source) == expected.comment_stripped
    assert mask_comments_and_strings(source) == expected.string_masked
    assert mask_source_lines(source) == (
        expected.original_lines,
        expected.comment_stripped_lines,
        expected.string_masked_lines,
    )


def test_source_views_are_immutable() -> None:
    views = build_source_views("x")

    with pytest.raises(FrozenInstanceError):
        views.original = "changed"  # type: ignore[misc]


def test_source_views_reject_misaligned_derived_views() -> None:
    with pytest.raises(
        ValueError,
        match="comment_stripped must preserve original character alignment",
    ):
        SourceViews(
            original="abc",
            comment_stripped="ab",
            string_masked="abc",
        )

    with pytest.raises(
        ValueError,
        match="string_masked must preserve original character alignment",
    ):
        SourceViews(
            original="abc",
            comment_stripped="abc",
            string_masked="ab",
        )


def test_source_views_reject_overlapping_or_out_of_bounds_spans() -> None:
    first = MaskedSpan(
        kind=MaskKind.STRING,
        start_offset=0,
        end_offset=2,
        start_line=1,
        start_column=1,
        end_line=1,
        end_column=3,
    )
    overlapping = MaskedSpan(
        kind=MaskKind.LINE_COMMENT,
        start_offset=1,
        end_offset=3,
        start_line=1,
        start_column=2,
        end_line=1,
        end_column=4,
    )
    out_of_bounds = MaskedSpan(
        kind=MaskKind.STRING,
        start_offset=0,
        end_offset=4,
        start_line=1,
        start_column=1,
        end_line=1,
        end_column=5,
    )

    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        SourceViews(
            original="abc",
            comment_stripped="abc",
            string_masked="abc",
            spans=(first, overlapping),
        )

    with pytest.raises(ValueError, match="span exceeds source length"):
        SourceViews(
            original="abc",
            comment_stripped="abc",
            string_masked="abc",
            spans=(out_of_bounds,),
        )


def test_masked_span_validates_coordinates_and_types() -> None:
    with pytest.raises(TypeError, match="kind must be a MaskKind"):
        MaskedSpan(  # type: ignore[arg-type]
            kind="string",
            start_offset=0,
            end_offset=1,
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=2,
        )

    with pytest.raises(ValueError, match="end_offset must not precede"):
        MaskedSpan(
            kind=MaskKind.STRING,
            start_offset=2,
            end_offset=1,
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=2,
        )

    with pytest.raises(ValueError, match="span end must not precede"):
        MaskedSpan(
            kind=MaskKind.STRING,
            start_offset=0,
            end_offset=1,
            start_line=2,
            start_column=1,
            end_line=1,
            end_column=2,
        )


def test_masking_issue_validates_message_and_location() -> None:
    with pytest.raises(ValueError, match="message must not be empty"):
        MaskingIssue(
            kind=MaskingIssueKind.UNTERMINATED_STRING,
            line=1,
            column=1,
            offset=0,
            message="   ",
        )

    with pytest.raises(ValueError, match="must not contain NUL"):
        MaskingIssue(
            kind=MaskingIssueKind.UNTERMINATED_STRING,
            line=1,
            column=1,
            offset=0,
            message="bad\x00message",
        )


def test_build_source_views_rejects_non_text_input() -> None:
    with pytest.raises(TypeError, match="source must be a string"):
        build_source_views(b"source")  # type: ignore[arg-type]
