"""Pure detectors for the canonical suspicious-source scan rules."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, TypeAlias

LineSpan: TypeAlias = tuple[int, int]

SCAN_NOTATION_001: Final[str] = "SCAN-NOTATION-001"
SCAN_NOTATION_002: Final[str] = "SCAN-NOTATION-002"
SCAN_RUNTIME_001: Final[str] = "SCAN-RUNTIME-001"
SCAN_PATTERN_001: Final[str] = "SCAN-PATTERN-001"
SCAN_PATTERN_002: Final[str] = "SCAN-PATTERN-002"
SCAN_STYLE_001: Final[str] = "SCAN-STYLE-001"

SINGLE_SLASH_EQ_FIELD: Final[str] = "single_slash_eq"
DOUBLE_SLASH_DASH_FIELD: Final[str] = "double_slash_dash"
RUNTIME_STR_MATCH_FIELD: Final[str] = "runtime_str_match"
UNTYPED_CASE_STR_PAT_FIELD: Final[str] = "untyped_case_str_pat"
UNTYPED_TABLE_STR_PAT_FIELD: Final[str] = "untyped_table_str_pat"
TRAILING_SPACES_FIELD: Final[str] = "trailing_spaces"

_MAX_CASE_HEADER_LINES: Final[int] = 8
_CASE_START_RE: Final[re.Pattern[str]] = re.compile(r"\bcase\b")
_CASE_OPEN_RE: Final[re.Pattern[str]] = re.compile(r"\bof\s*\{")
_TABLE_OPEN_RE: Final[re.Pattern[str]] = re.compile(r"\btable\s*\{")
_DOT_S_RE: Final[re.Pattern[str]] = re.compile(r"\.\s*s\b")
_EXPLICIT_STR_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r":\s*Str\s*>"
)
_GF_STRING_PATTERN: Final[str] = r'"(?:(?:"")|(?:\\.)|[^"\\])*"'
_LITERAL_BRANCH_RE: Final[re.Pattern[str]] = re.compile(
    rf"{_GF_STRING_PATTERN}\s*=>",
    re.DOTALL,
)
_STRING_CONCAT_RE: Final[re.Pattern[str]] = re.compile(
    rf"(?:_\s*\+\s*{_GF_STRING_PATTERN}|"
    rf"{_GF_STRING_PATTERN}\s*\+\s*_)",
    re.DOTALL,
)
_EXACT_SINGLE_BACKSLASH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!\\)\\(?!\\)"
)
_EXACT_DOUBLE_BACKSLASH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!\\)\\\\(?!\\)"
)


@dataclass(frozen=True, slots=True)
class _StructuralBlock:
    start_index: int
    end_index: int
    header: str

    @property
    def span(self) -> LineSpan:
        return (self.start_index + 1, self.end_index + 1)


def _require_lines(
    lines: Sequence[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(lines, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence of lines")

    normalized = tuple(lines)
    for index, line in enumerate(normalized):
        if not isinstance(line, str):
            raise TypeError(
                f"{field_name}[{index}] must be a string"
            )
        if "\x00" in line:
            raise ValueError(
                f"{field_name}[{index}] must not contain NUL"
            )
    return normalized


def _require_aligned(
    structural_lines: Sequence[str],
    content_lines: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    structural = _require_lines(
        structural_lines,
        field_name="structural_lines",
    )
    content = _require_lines(
        content_lines,
        field_name="content_lines",
    )
    if len(structural) != len(content):
        raise ValueError(
            "structural_lines and content_lines must be line-aligned"
        )
    return structural, content


def _physical_text(line: str) -> str:
    return line.rstrip("\r\n")


def _statement_segments(line: str) -> tuple[str, ...]:
    return tuple(line.split(";"))


def _first_arrow_after(
    segment: str,
    start: int,
) -> tuple[str, int] | None:
    fat = segment.find("=>", start)
    thin = segment.find("->", start)

    if fat < 0 and thin < 0:
        return None
    if fat < 0:
        return ("->", thin)
    if thin < 0:
        return ("=>", fat)
    if fat <= thin:
        return ("=>", fat)
    return ("->", thin)


def _has_slash_arrow_confusion(
    segment: str,
    *,
    slash_pattern: re.Pattern[str],
    expected_first_arrow: str,
) -> bool:
    for match in slash_pattern.finditer(segment):
        arrow = _first_arrow_after(segment, match.end())
        if arrow is not None and arrow[0] == expected_first_arrow:
            return True
    return False


def find_single_slash_eq(
    string_masked_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    lines = _require_lines(
        string_masked_lines,
        field_name="string_masked_lines",
    )
    matches: list[LineSpan] = []

    for index, raw_line in enumerate(lines):
        line = _physical_text(raw_line)
        if any(
            _has_slash_arrow_confusion(
                segment,
                slash_pattern=_EXACT_SINGLE_BACKSLASH_RE,
                expected_first_arrow="=>",
            )
            for segment in _statement_segments(line)
        ):
            matches.append((index + 1, index + 1))

    return tuple(matches)


def find_double_slash_dash(
    string_masked_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    lines = _require_lines(
        string_masked_lines,
        field_name="string_masked_lines",
    )
    matches: list[LineSpan] = []

    for index, raw_line in enumerate(lines):
        line = _physical_text(raw_line)
        if any(
            _has_slash_arrow_confusion(
                segment,
                slash_pattern=_EXACT_DOUBLE_BACKSLASH_RE,
                expected_first_arrow="->",
            )
            for segment in _statement_segments(line)
        ):
            matches.append((index + 1, index + 1))

    return tuple(matches)


def find_runtime_string_matches(
    string_masked_lines: Sequence[str],
    comment_stripped_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    structural, content = _require_aligned(
        string_masked_lines,
        comment_stripped_lines,
    )
    matches: list[LineSpan] = []

    for block in _iter_case_blocks(structural):
        if _DOT_S_RE.search(block.header) is None:
            continue
        block_text = "".join(
            content[block.start_index : block.end_index + 1]
        )
        if _LITERAL_BRANCH_RE.search(block_text) is not None:
            matches.append(block.span)

    return tuple(matches)


def find_untyped_case_string_patterns(
    string_masked_lines: Sequence[str],
    comment_stripped_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    structural, content = _require_aligned(
        string_masked_lines,
        comment_stripped_lines,
    )
    return _find_untyped_string_patterns(
        blocks=_iter_case_blocks(structural),
        content_lines=content,
    )


def find_untyped_table_string_patterns(
    string_masked_lines: Sequence[str],
    comment_stripped_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    structural, content = _require_aligned(
        string_masked_lines,
        comment_stripped_lines,
    )
    return _find_untyped_string_patterns(
        blocks=_iter_table_blocks(structural),
        content_lines=content,
    )


def find_trailing_spaces(
    original_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    lines = _require_lines(
        original_lines,
        field_name="original_lines",
    )
    matches: list[LineSpan] = []

    for index, line in enumerate(lines):
        physical = _physical_text(line)
        if physical.endswith((" ", "\t")):
            matches.append((index + 1, index + 1))

    return tuple(matches)


def _find_untyped_string_patterns(
    *,
    blocks: Sequence[_StructuralBlock],
    content_lines: Sequence[str],
) -> tuple[LineSpan, ...]:
    matches: list[LineSpan] = []

    for block in blocks:
        block_text = "".join(
            content_lines[block.start_index : block.end_index + 1]
        )
        if _STRING_CONCAT_RE.search(block_text) is None:
            continue
        if _EXPLICIT_STR_TYPE_RE.search(block_text) is not None:
            continue
        matches.append(block.span)

    return tuple(matches)


def _iter_case_blocks(
    structural_lines: Sequence[str],
) -> tuple[_StructuralBlock, ...]:
    return _iter_blocks(
        structural_lines,
        kind="case",
    )


def _iter_table_blocks(
    structural_lines: Sequence[str],
) -> tuple[_StructuralBlock, ...]:
    return _iter_blocks(
        structural_lines,
        kind="table",
    )


def _iter_blocks(
    structural_lines: Sequence[str],
    *,
    kind: str,
) -> tuple[_StructuralBlock, ...]:
    lines = tuple(structural_lines)
    blocks: list[_StructuralBlock] = []
    index = 0

    while index < len(lines):
        located = _locate_block_start(
            lines,
            start_index=index,
            kind=kind,
        )
        if located is None:
            break

        start_index, open_index, open_column, header = located
        end_index = _find_balanced_end(
            lines,
            open_index=open_index,
            open_column=open_column,
        )
        if end_index is None:
            index = open_index + 1
            continue

        blocks.append(
            _StructuralBlock(
                start_index=start_index,
                end_index=end_index,
                header=header,
            )
        )
        index = end_index + 1

    return tuple(blocks)


def _locate_block_start(
    lines: Sequence[str],
    *,
    start_index: int,
    kind: str,
) -> tuple[int, int, int, str] | None:
    for index in range(start_index, len(lines)):
        line = _physical_text(lines[index])

        if kind == "table":
            table_match = _TABLE_OPEN_RE.search(line)
            if table_match is None:
                continue
            open_column = line.find("{", table_match.start())
            return (
                index,
                index,
                open_column,
                line[table_match.start() : open_column + 1],
            )

        case_match = _CASE_START_RE.search(line)
        if case_match is None:
            continue

        upper_bound = min(
            len(lines),
            index + _MAX_CASE_HEADER_LINES,
        )
        header_parts: list[str] = []
        for header_index in range(index, upper_bound):
            header_line = _physical_text(lines[header_index])
            if header_index == index:
                header_line = header_line[case_match.start() :]
            header_parts.append(header_line)
            joined = "\n".join(header_parts)
            open_match = _CASE_OPEN_RE.search(joined)
            if open_match is None:
                continue

            relative_open = joined.find("{", open_match.start())
            before_open = joined[:relative_open]
            line_offset = before_open.count("\n")
            open_index = index + line_offset
            if line_offset == 0:
                open_column = (
                    case_match.start()
                    + len(before_open.rsplit("\n", 1)[-1])
                )
            else:
                open_column = len(
                    before_open.rsplit("\n", 1)[-1]
                )
            return (
                index,
                open_index,
                open_column,
                joined[: relative_open + 1],
            )

    return None


def _find_balanced_end(
    lines: Sequence[str],
    *,
    open_index: int,
    open_column: int,
) -> int | None:
    depth = 0
    opened = False

    for index in range(open_index, len(lines)):
        line = _physical_text(lines[index])
        start_column = open_column if index == open_index else 0

        for character in line[start_column:]:
            if character == "{":
                depth += 1
                opened = True
            elif character == "}" and opened:
                depth -= 1
                if depth == 0:
                    return index

    return None


__all__ = (
    "DOUBLE_SLASH_DASH_FIELD",
    "LineSpan",
    "RUNTIME_STR_MATCH_FIELD",
    "SCAN_NOTATION_001",
    "SCAN_NOTATION_002",
    "SCAN_PATTERN_001",
    "SCAN_PATTERN_002",
    "SCAN_RUNTIME_001",
    "SCAN_STYLE_001",
    "SINGLE_SLASH_EQ_FIELD",
    "TRAILING_SPACES_FIELD",
    "UNTYPED_CASE_STR_PAT_FIELD",
    "UNTYPED_TABLE_STR_PAT_FIELD",
    "find_double_slash_dash",
    "find_runtime_string_matches",
    "find_single_slash_eq",
    "find_trailing_spaces",
    "find_untyped_case_string_patterns",
    "find_untyped_table_string_patterns",
)
