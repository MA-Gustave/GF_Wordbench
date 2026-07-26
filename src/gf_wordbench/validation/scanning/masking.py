"""GF-aware lexical masking for static source scanning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, TypeAlias


@unique
class MaskKind(StrEnum):
    """Lexical region hidden from one or more scanner views."""

    LINE_COMMENT = "line_comment"
    BLOCK_COMMENT = "block_comment"
    STRING = "string"


@unique
class MaskingIssueKind(StrEnum):
    """Recoverable lexical problems detected while building scanner views."""

    UNTERMINATED_BLOCK_COMMENT = "unterminated_block_comment"
    UNTERMINATED_STRING = "unterminated_string"


@dataclass(frozen=True, slots=True)
class MaskedSpan:
    """One aligned lexical span in the original source."""

    kind: MaskKind
    start_offset: int
    end_offset: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    terminated: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MaskKind):
            raise TypeError("kind must be a MaskKind")
        _require_non_negative_int("start_offset", self.start_offset)
        _require_non_negative_int("end_offset", self.end_offset)
        _require_positive_int("start_line", self.start_line)
        _require_positive_int("start_column", self.start_column)
        _require_positive_int("end_line", self.end_line)
        _require_positive_int("end_column", self.end_column)
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must not precede start_offset")
        if (self.end_line, self.end_column) < (
            self.start_line,
            self.start_column,
        ):
            raise ValueError("span end must not precede span start")
        if not isinstance(self.terminated, bool):
            raise TypeError("terminated must be a boolean")


@dataclass(frozen=True, slots=True)
class MaskingIssue:
    """One bounded diagnostic produced by lexical masking."""

    kind: MaskingIssueKind
    line: int
    column: int
    offset: int
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MaskingIssueKind):
            raise TypeError("kind must be a MaskingIssueKind")
        _require_positive_int("line", self.line)
        _require_positive_int("column", self.column)
        _require_non_negative_int("offset", self.offset)
        if not isinstance(self.message, str):
            raise TypeError("message must be a string")
        if not self.message.strip():
            raise ValueError("message must not be empty")
        if "\x00" in self.message:
            raise ValueError("message must not contain NUL characters")


@dataclass(frozen=True, slots=True)
class SourceViews:
    """Aligned source representations consumed by static scanning rules."""

    original: str
    comment_stripped: str
    string_masked: str
    spans: tuple[MaskedSpan, ...] = ()
    issues: tuple[MaskingIssue, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("original", self.original),
            ("comment_stripped", self.comment_stripped),
            ("string_masked", self.string_masked),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")

        expected_length = len(self.original)
        if len(self.comment_stripped) != expected_length:
            raise ValueError(
                "comment_stripped must preserve original character alignment"
            )
        if len(self.string_masked) != expected_length:
            raise ValueError(
                "string_masked must preserve original character alignment"
            )
        if not isinstance(self.spans, tuple):
            raise TypeError("spans must be a tuple")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")
        if any(not isinstance(span, MaskedSpan) for span in self.spans):
            raise TypeError("spans must contain only MaskedSpan values")
        if any(not isinstance(issue, MaskingIssue) for issue in self.issues):
            raise TypeError("issues must contain only MaskingIssue values")

        previous_end = 0
        for span in self.spans:
            if span.start_offset < previous_end:
                raise ValueError("spans must be ordered and non-overlapping")
            if span.end_offset > expected_length:
                raise ValueError("span exceeds source length")
            previous_end = span.end_offset

    @property
    def original_lines(self) -> tuple[str, ...]:
        """Return physical original lines with line endings retained."""

        return tuple(self.original.splitlines(keepends=True))

    @property
    def comment_stripped_lines(self) -> tuple[str, ...]:
        """Return aligned comment-stripped physical lines."""

        return tuple(self.comment_stripped.splitlines(keepends=True))

    @property
    def string_masked_lines(self) -> tuple[str, ...]:
        """Return aligned comment- and string-masked physical lines."""

        return tuple(self.string_masked.splitlines(keepends=True))

    @property
    def has_lexical_issues(self) -> bool:
        """Whether masking encountered an unterminated lexical construct."""

        return bool(self.issues)


MaskedSource: TypeAlias = SourceViews

_STATE_CODE: Final = "code"
_STATE_LINE_COMMENT: Final = "line_comment"
_STATE_BLOCK_COMMENT: Final = "block_comment"
_STATE_STRING: Final = "string"
_SPACE: Final = " "


def build_source_views(source: str) -> SourceViews:
    """Build aligned original, comment-stripped, and string-masked views."""

    if not isinstance(source, str):
        raise TypeError("source must be a string")

    comment_view: list[str] = []
    structural_view: list[str] = []
    spans: list[MaskedSpan] = []
    issues: list[MaskingIssue] = []

    state = _STATE_CODE
    block_depth = 0
    index = 0
    line = 1
    column = 1

    span_kind: MaskKind | None = None
    span_start_offset = 0
    span_start_line = 1
    span_start_column = 1

    while index < len(source):
        newline_length = _newline_length(source, index)
        if newline_length:
            newline = source[index : index + newline_length]
            previous_line = line
            previous_column = column
            comment_view.append(newline)
            structural_view.append(newline)
            index += newline_length
            line += 1
            column = 1
            if state == _STATE_LINE_COMMENT:
                _append_span(
                    spans,
                    kind=MaskKind.LINE_COMMENT,
                    start_offset=span_start_offset,
                    end_offset=index - newline_length,
                    start_line=span_start_line,
                    start_column=span_start_column,
                    end_line=previous_line,
                    end_column=previous_column,
                    terminated=True,
                )
                state = _STATE_CODE
                span_kind = None
            continue

        if state == _STATE_CODE:
            if source.startswith("--", index):
                state = _STATE_LINE_COMMENT
                span_kind = MaskKind.LINE_COMMENT
                span_start_offset = index
                span_start_line = line
                span_start_column = column
                _append_mask(comment_view, 2)
                _append_mask(structural_view, 2)
                index += 2
                column += 2
                continue

            if source.startswith("{-", index):
                state = _STATE_BLOCK_COMMENT
                block_depth = 1
                span_kind = MaskKind.BLOCK_COMMENT
                span_start_offset = index
                span_start_line = line
                span_start_column = column
                _append_mask(comment_view, 2)
                _append_mask(structural_view, 2)
                index += 2
                column += 2
                continue

            if source[index] == '"':
                state = _STATE_STRING
                span_kind = MaskKind.STRING
                span_start_offset = index
                span_start_line = line
                span_start_column = column
                comment_view.append('"')
                structural_view.append(_SPACE)
                index += 1
                column += 1
                continue

            character = source[index]
            comment_view.append(character)
            structural_view.append(character)
            index += 1
            column += 1
            continue

        if state == _STATE_LINE_COMMENT:
            comment_view.append(_SPACE)
            structural_view.append(_SPACE)
            index += 1
            column += 1
            continue

        if state == _STATE_BLOCK_COMMENT:
            if source.startswith("{-", index):
                block_depth += 1
                _append_mask(comment_view, 2)
                _append_mask(structural_view, 2)
                index += 2
                column += 2
                continue

            if source.startswith("-}", index):
                block_depth -= 1
                _append_mask(comment_view, 2)
                _append_mask(structural_view, 2)
                index += 2
                column += 2
                if block_depth == 0:
                    _append_span(
                        spans,
                        kind=MaskKind.BLOCK_COMMENT,
                        start_offset=span_start_offset,
                        end_offset=index,
                        start_line=span_start_line,
                        start_column=span_start_column,
                        end_line=line,
                        end_column=column,
                        terminated=True,
                    )
                    state = _STATE_CODE
                    span_kind = None
                continue

            comment_view.append(_SPACE)
            structural_view.append(_SPACE)
            index += 1
            column += 1
            continue

        if state == _STATE_STRING:
            character = source[index]

            if character == "\\":
                comment_view.append(character)
                structural_view.append(_SPACE)
                index += 1
                column += 1
                if index < len(source) and not _newline_length(source, index):
                    comment_view.append(source[index])
                    structural_view.append(_SPACE)
                    index += 1
                    column += 1
                continue

            if character == '"':
                if source.startswith('""', index):
                    comment_view.extend(('"', '"'))
                    structural_view.extend((_SPACE, _SPACE))
                    index += 2
                    column += 2
                    continue

                comment_view.append('"')
                structural_view.append(_SPACE)
                index += 1
                column += 1
                _append_span(
                    spans,
                    kind=MaskKind.STRING,
                    start_offset=span_start_offset,
                    end_offset=index,
                    start_line=span_start_line,
                    start_column=span_start_column,
                    end_line=line,
                    end_column=column,
                    terminated=True,
                )
                state = _STATE_CODE
                span_kind = None
                continue

            comment_view.append(character)
            structural_view.append(_SPACE)
            index += 1
            column += 1
            continue

        raise AssertionError(f"unknown lexical state {state!r}")

    if state == _STATE_LINE_COMMENT:
        _append_span(
            spans,
            kind=MaskKind.LINE_COMMENT,
            start_offset=span_start_offset,
            end_offset=len(source),
            start_line=span_start_line,
            start_column=span_start_column,
            end_line=line,
            end_column=column,
            terminated=True,
        )
    elif state == _STATE_BLOCK_COMMENT:
        _append_span(
            spans,
            kind=MaskKind.BLOCK_COMMENT,
            start_offset=span_start_offset,
            end_offset=len(source),
            start_line=span_start_line,
            start_column=span_start_column,
            end_line=line,
            end_column=column,
            terminated=False,
        )
        issues.append(
            MaskingIssue(
                kind=MaskingIssueKind.UNTERMINATED_BLOCK_COMMENT,
                line=span_start_line,
                column=span_start_column,
                offset=span_start_offset,
                message="Unterminated GF block comment.",
            )
        )
    elif state == _STATE_STRING:
        _append_span(
            spans,
            kind=MaskKind.STRING,
            start_offset=span_start_offset,
            end_offset=len(source),
            start_line=span_start_line,
            start_column=span_start_column,
            end_line=line,
            end_column=column,
            terminated=False,
        )
        issues.append(
            MaskingIssue(
                kind=MaskingIssueKind.UNTERMINATED_STRING,
                line=span_start_line,
                column=span_start_column,
                offset=span_start_offset,
                message="Unterminated GF string literal.",
            )
        )

    if span_kind is not None and state == _STATE_CODE:
        raise AssertionError("closed lexical span retained active state")

    comment_stripped = "".join(comment_view)
    string_masked = "".join(structural_view)

    if len(comment_stripped) != len(source):
        raise AssertionError("comment masking changed source length")
    if len(string_masked) != len(source):
        raise AssertionError("string masking changed source length")

    return SourceViews(
        original=source,
        comment_stripped=comment_stripped,
        string_masked=string_masked,
        spans=tuple(spans),
        issues=tuple(issues),
    )


def mask_source(source: str) -> SourceViews:
    """Compatibility name for building all aligned scanner source views."""

    return build_source_views(source)


def mask_comments(source: str) -> str:
    """Return source with comments replaced by aligned spaces."""

    return build_source_views(source).comment_stripped


def mask_comments_and_strings(source: str) -> str:
    """Return source with comments and string literals replaced by spaces."""

    return build_source_views(source).string_masked


def mask_source_lines(
    source: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return aligned physical-line tuples for all three scanner views."""

    views = build_source_views(source)
    return (
        views.original_lines,
        views.comment_stripped_lines,
        views.string_masked_lines,
    )


def _append_mask(target: list[str], length: int) -> None:
    target.extend(_SPACE for _ in range(length))


def _append_span(
    spans: list[MaskedSpan],
    *,
    kind: MaskKind,
    start_offset: int,
    end_offset: int,
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
    terminated: bool,
) -> None:
    spans.append(
        MaskedSpan(
            kind=kind,
            start_offset=start_offset,
            end_offset=end_offset,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            terminated=terminated,
        )
    )


def _newline_length(source: str, index: int) -> int:
    character = source[index]
    if character == "\n":
        return 1
    if character == "\r":
        return 2 if index + 1 < len(source) and source[index + 1] == "\n" else 1
    return 0


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be positive")


__all__ = (
    "MaskKind",
    "MaskedSource",
    "MaskedSpan",
    "MaskingIssue",
    "MaskingIssueKind",
    "SourceViews",
    "build_source_views",
    "mask_comments",
    "mask_comments_and_strings",
    "mask_source",
    "mask_source_lines",
)
