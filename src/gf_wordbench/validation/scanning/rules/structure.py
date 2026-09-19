"""Structural static-scan rules for brace-balanced GF case and table blocks."""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
import re
from typing import Final, Protocol, runtime_checkable

RUNTIME_STRING_MATCH_RULE_ID: Final[str] = "SCAN-RUNTIME-001"
UNTYPED_CASE_STRING_PATTERN_RULE_ID: Final[str] = "SCAN-PATTERN-001"
UNTYPED_TABLE_STRING_PATTERN_RULE_ID: Final[str] = "SCAN-PATTERN-002"

RUNTIME_STRING_MATCH_COUNT_FIELD: Final[str] = "runtime_str_match"
UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD: Final[str] = "untyped_case_str_pat"
UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD: Final[str] = "untyped_table_str_pat"

DEFAULT_MAX_CASE_HEADER_LINES: Final[int] = 8
DEFAULT_MAX_BLOCK_LINES: Final[int] = 20_000
DEFAULT_MAX_EXCERPT_LINES: Final[int] = 12
DEFAULT_MAX_EXCERPT_CHARS: Final[int] = 2_000

_CASE_START_RE: Final[re.Pattern[str]] = re.compile(r"\bcase\b")
_TABLE_START_RE: Final[re.Pattern[str]] = re.compile(
    r"\btable\s*\{",
    re.MULTILINE,
)
_CASE_HEADER_END_RE: Final[re.Pattern[str]] = re.compile(
    r"\bof\s*\{",
    re.MULTILINE,
)
_STRING_LITERAL_RE: Final[re.Pattern[str]] = re.compile(
    r'"(?:[^"\\]|\\.|"")*"',
    re.DOTALL,
)
_STRING_BRANCH_RE: Final[re.Pattern[str]] = re.compile(
    r'"(?:[^"\\]|\\.|"")*"\s*=>',
    re.DOTALL,
)
_STRING_CONCAT_LEFT_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:\b[A-Za-z][A-Za-z0-9_]*\b|_)\s*\+\s*"
    r'"(?:[^"\\]|\\.|"")*"',
    re.DOTALL,
)
_STRING_CONCAT_RIGHT_RE: Final[re.Pattern[str]] = re.compile(
    r'"(?:[^"\\]|\\.|"")*"\s*\+\s*'
    r"(?:\b[A-Za-z][A-Za-z0-9_]*\b|_)",
    re.DOTALL,
)
_EXPLICIT_STR_PATTERN_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r":\s*Str\s*>",
    re.MULTILINE,
)
_STRING_PATTERN_BRANCH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<pattern>[^;{}\n]*"
    r"(?:(?:\b[A-Za-z][A-Za-z0-9_]*\b|_)\s*\+\s*"
    r'"(?:[^"\\]|\\.|"")*"|'
    r'"(?:[^"\\]|\\.|"")*"\s*\+\s*'
    r"(?:\b[A-Za-z][A-Za-z0-9_]*\b|_))"
    r"[^;{}]*?)\s*=>",
    re.DOTALL,
)
_S_PROJECTION_RE: Final[re.Pattern[str]] = re.compile(
    r"\.\s*s\b",
    re.MULTILINE,
)


@unique
class StructuralBlockKind(StrEnum):
    CASE = "case"
    TABLE = "table"


@unique
class StructureDiagnosticCode(StrEnum):
    UNBALANCED_BLOCK = "unbalanced_block"
    CASE_HEADER_LIMIT = "case_header_limit"
    BLOCK_LINE_LIMIT = "block_line_limit"


@dataclass(frozen=True, slots=True)
class StructuralBlock:
    kind: StructuralBlockKind
    start_line: int
    end_line: int
    start_column: int
    opening_brace_column: int
    header_text: str
    structural_text: str
    source_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StructuralBlockKind):
            raise TypeError("kind must be a StructuralBlockKind")
        _positive_integer(self.start_line, field_name="start_line")
        _positive_integer(self.end_line, field_name="end_line")
        _positive_integer(self.start_column, field_name="start_column")
        _positive_integer(
            self.opening_brace_column,
            field_name="opening_brace_column",
        )
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        for field_name in (
            "header_text",
            "structural_text",
            "source_text",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if "\x00" in value:
                raise ValueError(f"{field_name} must not contain NUL characters")


@dataclass(frozen=True, slots=True)
class StructureDiagnostic:
    code: StructureDiagnosticCode
    kind: StructuralBlockKind
    start_line: int
    end_line: int
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, StructureDiagnosticCode):
            raise TypeError("code must be a StructureDiagnosticCode")
        if not isinstance(self.kind, StructuralBlockKind):
            raise TypeError("kind must be a StructuralBlockKind")
        _positive_integer(self.start_line, field_name="start_line")
        _positive_integer(self.end_line, field_name="end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        _required_text(self.message, field_name="message")


@dataclass(frozen=True, slots=True)
class StructureFinding:
    rule_id: str
    count_field: str
    source_path: Path | None
    start_line: int
    end_line: int
    start_column: int
    excerpt: str
    message: str

    def __post_init__(self) -> None:
        _required_text(self.rule_id, field_name="rule_id")
        _required_text(self.count_field, field_name="count_field")
        _positive_integer(self.start_line, field_name="start_line")
        _positive_integer(self.end_line, field_name="end_line")
        _positive_integer(
            self.start_column,
            field_name="start_column",
        )
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        if not isinstance(self.excerpt, str):
            raise TypeError("excerpt must be a string")
        if "\x00" in self.excerpt:
            raise ValueError("excerpt must not contain NUL characters")
        _required_text(self.message, field_name="message")

        source_path = self.source_path
        if source_path is not None:
            if not isinstance(source_path, Path):
                raise TypeError("source_path must be a pathlib.Path or None")
            if "\x00" in str(source_path):
                raise ValueError("source_path must not contain NUL characters")


@dataclass(frozen=True, slots=True)
class StructureRuleResult:
    findings: tuple[StructureFinding, ...]
    diagnostics: tuple[StructureDiagnostic, ...]

    def __post_init__(self) -> None:
        findings = tuple(self.findings)
        diagnostics = tuple(self.diagnostics)

        if not all(isinstance(item, StructureFinding) for item in findings):
            raise TypeError("findings must contain StructureFinding values")
        if not all(isinstance(item, StructureDiagnostic) for item in diagnostics):
            raise TypeError("diagnostics must contain StructureDiagnostic values")

        object.__setattr__(
            self,
            "findings",
            tuple(sorted(findings, key=_finding_sort_key)),
        )
        object.__setattr__(
            self,
            "diagnostics",
            tuple(
                sorted(
                    diagnostics,
                    key=_diagnostic_sort_key,
                )
            ),
        )

    @property
    def runtime_str_match(self) -> int:
        return self.count_for(RUNTIME_STRING_MATCH_RULE_ID)

    @property
    def untyped_case_str_pat(self) -> int:
        return self.count_for(UNTYPED_CASE_STRING_PATTERN_RULE_ID)

    @property
    def untyped_table_str_pat(self) -> int:
        return self.count_for(UNTYPED_TABLE_STRING_PATTERN_RULE_ID)

    def count_for(self, rule_id: str) -> int:
        rule_id = _required_text(
            rule_id,
            field_name="rule_id",
        )
        return sum(1 for finding in self.findings if finding.rule_id == rule_id)

    def counts(self) -> dict[str, int]:
        return {
            RUNTIME_STRING_MATCH_COUNT_FIELD: (self.runtime_str_match),
            UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD: (self.untyped_case_str_pat),
            UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD: (self.untyped_table_str_pat),
        }


@runtime_checkable
class SourceViews(Protocol):
    @property
    def original_lines(self) -> Sequence[str]: ...

    @property
    def comment_stripped_lines(self) -> Sequence[str]: ...

    @property
    def string_masked_lines(self) -> Sequence[str]: ...


@dataclass(frozen=True, slots=True)
class StructuralBlockCollection:
    case_blocks: tuple[StructuralBlock, ...]
    table_blocks: tuple[StructuralBlock, ...]
    diagnostics: tuple[StructureDiagnostic, ...]

    def __post_init__(self) -> None:
        case_blocks = tuple(self.case_blocks)
        table_blocks = tuple(self.table_blocks)
        diagnostics = tuple(self.diagnostics)

        if not all(
            isinstance(item, StructuralBlock) and item.kind is StructuralBlockKind.CASE
            for item in case_blocks
        ):
            raise TypeError("case_blocks must contain case StructuralBlock values")
        if not all(
            isinstance(item, StructuralBlock) and item.kind is StructuralBlockKind.TABLE
            for item in table_blocks
        ):
            raise TypeError("table_blocks must contain table StructuralBlock values")
        if not all(isinstance(item, StructureDiagnostic) for item in diagnostics):
            raise TypeError("diagnostics must contain StructureDiagnostic values")

        object.__setattr__(
            self,
            "case_blocks",
            tuple(sorted(case_blocks, key=_block_sort_key)),
        )
        object.__setattr__(
            self,
            "table_blocks",
            tuple(sorted(table_blocks, key=_block_sort_key)),
        )
        object.__setattr__(
            self,
            "diagnostics",
            tuple(
                sorted(
                    diagnostics,
                    key=_diagnostic_sort_key,
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class _JoinedLines:
    lines: tuple[str, ...]
    text: str
    starts: tuple[int, ...]

    def line_number(self, offset: int) -> int:
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise TypeError("offset must be an integer")
        if offset < 0 or offset > len(self.text):
            raise ValueError("offset is outside the joined source")
        return bisect.bisect_right(self.starts, offset)

    def column_number(self, offset: int) -> int:
        line_number = self.line_number(offset)
        return offset - self.starts[line_number - 1] + 1

    def offset_for_line(self, line_number: int) -> int:
        _positive_integer(
            line_number,
            field_name="line_number",
        )
        if line_number > len(self.lines):
            raise ValueError("line_number exceeds the number of source lines")
        return self.starts[line_number - 1]


def collect_structural_blocks(
    views: SourceViews,
    *,
    max_case_header_lines: int = (DEFAULT_MAX_CASE_HEADER_LINES),
    max_block_lines: int = DEFAULT_MAX_BLOCK_LINES,
) -> StructuralBlockCollection:
    original_lines, comment_lines, masked_lines = _validated_views(views)
    max_case_header_lines = _positive_integer(
        max_case_header_lines,
        field_name="max_case_header_lines",
    )
    max_block_lines = _positive_integer(
        max_block_lines,
        field_name="max_block_lines",
    )

    original = _join_lines(original_lines)
    comments = _join_lines(comment_lines)
    masked = _join_lines(masked_lines)

    case_blocks, case_diagnostics = _collect_kind(
        kind=StructuralBlockKind.CASE,
        original=original,
        comments=comments,
        masked=masked,
        max_case_header_lines=max_case_header_lines,
        max_block_lines=max_block_lines,
    )
    table_blocks, table_diagnostics = _collect_kind(
        kind=StructuralBlockKind.TABLE,
        original=original,
        comments=comments,
        masked=masked,
        max_case_header_lines=max_case_header_lines,
        max_block_lines=max_block_lines,
    )

    return StructuralBlockCollection(
        case_blocks=case_blocks,
        table_blocks=table_blocks,
        diagnostics=(
            *case_diagnostics,
            *table_diagnostics,
        ),
    )


def scan_structure_rules(
    views: SourceViews,
    *,
    source_path: Path | None = None,
    max_case_header_lines: int = (DEFAULT_MAX_CASE_HEADER_LINES),
    max_block_lines: int = DEFAULT_MAX_BLOCK_LINES,
    max_excerpt_lines: int = DEFAULT_MAX_EXCERPT_LINES,
    max_excerpt_chars: int = DEFAULT_MAX_EXCERPT_CHARS,
) -> StructureRuleResult:
    source_path = _optional_path(
        source_path,
        field_name="source_path",
    )
    max_excerpt_lines = _positive_integer(
        max_excerpt_lines,
        field_name="max_excerpt_lines",
    )
    max_excerpt_chars = _positive_integer(
        max_excerpt_chars,
        field_name="max_excerpt_chars",
    )

    blocks = collect_structural_blocks(
        views,
        max_case_header_lines=max_case_header_lines,
        max_block_lines=max_block_lines,
    )
    original_lines, _, _ = _validated_views(views)

    findings: list[StructureFinding] = []

    findings.extend(
        find_runtime_string_matches(
            blocks.case_blocks,
            original_lines=original_lines,
            source_path=source_path,
            max_excerpt_lines=max_excerpt_lines,
            max_excerpt_chars=max_excerpt_chars,
        )
    )
    findings.extend(
        find_untyped_case_string_patterns(
            blocks.case_blocks,
            original_lines=original_lines,
            source_path=source_path,
            max_excerpt_lines=max_excerpt_lines,
            max_excerpt_chars=max_excerpt_chars,
        )
    )
    findings.extend(
        find_untyped_table_string_patterns(
            blocks.table_blocks,
            original_lines=original_lines,
            source_path=source_path,
            max_excerpt_lines=max_excerpt_lines,
            max_excerpt_chars=max_excerpt_chars,
        )
    )

    return StructureRuleResult(
        findings=tuple(findings),
        diagnostics=blocks.diagnostics,
    )


def find_runtime_string_matches(
    blocks: Iterable[StructuralBlock],
    *,
    original_lines: Sequence[str],
    source_path: Path | None = None,
    max_excerpt_lines: int = DEFAULT_MAX_EXCERPT_LINES,
    max_excerpt_chars: int = DEFAULT_MAX_EXCERPT_CHARS,
) -> tuple[StructureFinding, ...]:
    case_blocks = _block_tuple(
        blocks,
        expected_kind=StructuralBlockKind.CASE,
    )
    original = _line_tuple(
        original_lines,
        field_name="original_lines",
    )
    source_path = _optional_path(
        source_path,
        field_name="source_path",
    )
    max_excerpt_lines = _positive_integer(
        max_excerpt_lines,
        field_name="max_excerpt_lines",
    )
    max_excerpt_chars = _positive_integer(
        max_excerpt_chars,
        field_name="max_excerpt_chars",
    )

    findings: list[StructureFinding] = []

    for block in case_blocks:
        if _S_PROJECTION_RE.search(block.header_text) is None:
            continue
        if _STRING_BRANCH_RE.search(block.source_text) is None:
            continue

        findings.append(
            _finding(
                rule_id=RUNTIME_STRING_MATCH_RULE_ID,
                count_field=RUNTIME_STRING_MATCH_COUNT_FIELD,
                source_path=source_path,
                block=block,
                original_lines=original,
                max_excerpt_lines=max_excerpt_lines,
                max_excerpt_chars=max_excerpt_chars,
                message=(
                    "Brace-balanced case block matches realized "
                    "string material from an expression containing .s."
                ),
            )
        )

    return tuple(findings)


def find_untyped_case_string_patterns(
    blocks: Iterable[StructuralBlock],
    *,
    original_lines: Sequence[str],
    source_path: Path | None = None,
    max_excerpt_lines: int = DEFAULT_MAX_EXCERPT_LINES,
    max_excerpt_chars: int = DEFAULT_MAX_EXCERPT_CHARS,
) -> tuple[StructureFinding, ...]:
    return _find_untyped_patterns(
        blocks,
        expected_kind=StructuralBlockKind.CASE,
        rule_id=UNTYPED_CASE_STRING_PATTERN_RULE_ID,
        count_field=UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD,
        original_lines=original_lines,
        source_path=source_path,
        max_excerpt_lines=max_excerpt_lines,
        max_excerpt_chars=max_excerpt_chars,
        message=(
            "Brace-balanced case block contains a concatenation-style "
            "string pattern without an explicit ': Str >' form."
        ),
    )


def find_untyped_table_string_patterns(
    blocks: Iterable[StructuralBlock],
    *,
    original_lines: Sequence[str],
    source_path: Path | None = None,
    max_excerpt_lines: int = DEFAULT_MAX_EXCERPT_LINES,
    max_excerpt_chars: int = DEFAULT_MAX_EXCERPT_CHARS,
) -> tuple[StructureFinding, ...]:
    return _find_untyped_patterns(
        blocks,
        expected_kind=StructuralBlockKind.TABLE,
        rule_id=UNTYPED_TABLE_STRING_PATTERN_RULE_ID,
        count_field=UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD,
        original_lines=original_lines,
        source_path=source_path,
        max_excerpt_lines=max_excerpt_lines,
        max_excerpt_chars=max_excerpt_chars,
        message=(
            "Brace-balanced table block contains a concatenation-style "
            "string pattern without an explicit ': Str >' form."
        ),
    )


def contains_string_literal_branch(value: str) -> bool:
    value = _text(value, field_name="value")
    return _STRING_BRANCH_RE.search(value) is not None


def contains_string_concatenation_pattern(value: str) -> bool:
    value = _text(value, field_name="value")
    return (
        _STRING_PATTERN_BRANCH_RE.search(value) is not None
        or _STRING_CONCAT_LEFT_RE.search(value) is not None
        or _STRING_CONCAT_RIGHT_RE.search(value) is not None
    )


def contains_explicit_str_pattern_type(value: str) -> bool:
    value = _text(value, field_name="value")
    return _EXPLICIT_STR_PATTERN_TYPE_RE.search(value) is not None


def _find_untyped_patterns(
    blocks: Iterable[StructuralBlock],
    *,
    expected_kind: StructuralBlockKind,
    rule_id: str,
    count_field: str,
    original_lines: Sequence[str],
    source_path: Path | None,
    max_excerpt_lines: int,
    max_excerpt_chars: int,
    message: str,
) -> tuple[StructureFinding, ...]:
    normalized_blocks = _block_tuple(
        blocks,
        expected_kind=expected_kind,
    )
    original = _line_tuple(
        original_lines,
        field_name="original_lines",
    )
    source_path = _optional_path(
        source_path,
        field_name="source_path",
    )
    max_excerpt_lines = _positive_integer(
        max_excerpt_lines,
        field_name="max_excerpt_lines",
    )
    max_excerpt_chars = _positive_integer(
        max_excerpt_chars,
        field_name="max_excerpt_chars",
    )

    findings: list[StructureFinding] = []

    for block in normalized_blocks:
        if not contains_string_concatenation_pattern(block.source_text):
            continue
        if contains_explicit_str_pattern_type(block.source_text):
            continue

        findings.append(
            _finding(
                rule_id=rule_id,
                count_field=count_field,
                source_path=source_path,
                block=block,
                original_lines=original,
                max_excerpt_lines=max_excerpt_lines,
                max_excerpt_chars=max_excerpt_chars,
                message=message,
            )
        )

    return tuple(findings)


def _collect_kind(
    *,
    kind: StructuralBlockKind,
    original: _JoinedLines,
    comments: _JoinedLines,
    masked: _JoinedLines,
    max_case_header_lines: int,
    max_block_lines: int,
) -> tuple[
    tuple[StructuralBlock, ...],
    tuple[StructureDiagnostic, ...],
]:
    starts, start_diagnostics = _candidate_starts(
        kind=kind,
        masked=masked,
        max_case_header_lines=max_case_header_lines,
    )
    blocks: list[StructuralBlock] = []
    diagnostics: list[StructureDiagnostic] = list(start_diagnostics)
    accepted_until = -1

    for start_offset, opening_brace_offset in starts:
        if start_offset <= accepted_until:
            continue

        start_line = masked.line_number(start_offset)
        end_offset, end_line, diagnostic = _balanced_end(
            kind=kind,
            masked=masked,
            start_offset=start_offset,
            opening_brace_offset=opening_brace_offset,
            max_block_lines=max_block_lines,
        )

        if diagnostic is not None:
            diagnostics.append(diagnostic)
            accepted_until = max(
                accepted_until,
                masked.offset_for_line(diagnostic.end_line)
                + len(masked.lines[diagnostic.end_line - 1]),
            )
            continue

        assert end_offset is not None
        assert end_line is not None

        header_text = masked.text[start_offset : opening_brace_offset + 1]
        structural_text = masked.text[start_offset : end_offset + 1]
        source_text = comments.text[start_offset : end_offset + 1]

        blocks.append(
            StructuralBlock(
                kind=kind,
                start_line=start_line,
                end_line=end_line,
                start_column=masked.column_number(start_offset),
                opening_brace_column=masked.column_number(opening_brace_offset),
                header_text=header_text,
                structural_text=structural_text,
                source_text=source_text,
            )
        )
        accepted_until = end_offset

    return tuple(blocks), tuple(diagnostics)


def _candidate_starts(
    *,
    kind: StructuralBlockKind,
    masked: _JoinedLines,
    max_case_header_lines: int,
) -> tuple[
    tuple[tuple[int, int], ...],
    tuple[StructureDiagnostic, ...],
]:
    if kind is StructuralBlockKind.TABLE:
        return (
            tuple(
                (match.start(), match.end() - 1) for match in _TABLE_START_RE.finditer(masked.text)
            ),
            (),
        )

    starts: list[tuple[int, int]] = []
    diagnostics: list[StructureDiagnostic] = []

    for match in _CASE_START_RE.finditer(masked.text):
        start_offset = match.start()
        start_line = masked.line_number(start_offset)
        last_header_line = min(
            len(masked.lines),
            start_line + max_case_header_lines - 1,
        )
        if last_header_line < len(masked.lines):
            limit_offset = masked.offset_for_line(last_header_line + 1)
        else:
            limit_offset = len(masked.text)

        header_match = _CASE_HEADER_END_RE.search(
            masked.text,
            match.end(),
            limit_offset,
        )
        if header_match is not None:
            starts.append((start_offset, header_match.end() - 1))
            continue

        next_case = _CASE_START_RE.search(
            masked.text,
            match.end(),
            limit_offset,
        )
        if next_case is not None:
            continue

        diagnostics.append(
            StructureDiagnostic(
                code=StructureDiagnosticCode.CASE_HEADER_LIMIT,
                kind=StructuralBlockKind.CASE,
                start_line=start_line,
                end_line=last_header_line,
                message=(
                    "Case header did not reach a code-visible 'of {' "
                    "within the configured header bound."
                ),
            )
        )

    return tuple(starts), tuple(diagnostics)


def _balanced_end(
    *,
    kind: StructuralBlockKind,
    masked: _JoinedLines,
    start_offset: int,
    opening_brace_offset: int,
    max_block_lines: int,
) -> tuple[
    int | None,
    int | None,
    StructureDiagnostic | None,
]:
    start_line = masked.line_number(start_offset)
    depth = 0

    for offset in range(opening_brace_offset, len(masked.text)):
        current_line = masked.line_number(offset)
        if current_line - start_line + 1 > max_block_lines:
            return (
                None,
                None,
                StructureDiagnostic(
                    code=StructureDiagnosticCode.BLOCK_LINE_LIMIT,
                    kind=kind,
                    start_line=start_line,
                    end_line=current_line,
                    message=(
                        "Structural block exceeded the configured "
                        "line bound before brace balance returned to zero."
                    ),
                ),
            )

        character = masked.text[offset]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return offset, current_line, None
            if depth < 0:
                break

    return (
        None,
        None,
        StructureDiagnostic(
            code=StructureDiagnosticCode.UNBALANCED_BLOCK,
            kind=kind,
            start_line=start_line,
            end_line=min(
                len(masked.lines),
                start_line + max_block_lines - 1,
            ),
            message=(
                "Structural block did not reach balanced brace depth "
                "within the available bounded source range."
            ),
        ),
    )


def _finding(
    *,
    rule_id: str,
    count_field: str,
    source_path: Path | None,
    block: StructuralBlock,
    original_lines: tuple[str, ...],
    max_excerpt_lines: int,
    max_excerpt_chars: int,
    message: str,
) -> StructureFinding:
    return StructureFinding(
        rule_id=rule_id,
        count_field=count_field,
        source_path=source_path,
        start_line=block.start_line,
        end_line=block.end_line,
        start_column=block.start_column,
        excerpt=_bounded_excerpt(
            original_lines,
            start_line=block.start_line,
            end_line=block.end_line,
            max_lines=max_excerpt_lines,
            max_chars=max_excerpt_chars,
        ),
        message=message,
    )


def _bounded_excerpt(
    lines: tuple[str, ...],
    *,
    start_line: int,
    end_line: int,
    max_lines: int,
    max_chars: int,
) -> str:
    selected = list(lines[start_line - 1 : end_line])
    truncated_lines = len(selected) > max_lines

    if truncated_lines:
        selected = selected[:max_lines]

    excerpt = "\n".join(selected)
    truncated_chars = len(excerpt) > max_chars

    if truncated_chars:
        excerpt = excerpt[:max_chars].rstrip()

    if truncated_lines or truncated_chars:
        marker = "\n…"
        if len(excerpt) + len(marker) > max_chars:
            excerpt = excerpt[: max(0, max_chars - len(marker))].rstrip()
        excerpt += marker

    return excerpt


def _validated_views(
    views: SourceViews,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    if not isinstance(views, SourceViews):
        raise TypeError(
            "views must expose original_lines, comment_stripped_lines, and string_masked_lines"
        )

    original = _line_tuple(
        views.original_lines,
        field_name="original_lines",
    )
    comments = _line_tuple(
        views.comment_stripped_lines,
        field_name="comment_stripped_lines",
    )
    masked = _line_tuple(
        views.string_masked_lines,
        field_name="string_masked_lines",
    )

    if not (len(original) == len(comments) == len(masked)):
        raise ValueError("all source views must contain the same number of lines")

    for index, (
        original_line,
        comment_line,
        masked_line,
    ) in enumerate(
        zip(original, comments, masked, strict=True),
        start=1,
    ):
        if len(original_line) != len(comment_line):
            raise ValueError(
                f"comment-stripped view must preserve character alignment on line {index}"
            )
        if len(original_line) != len(masked_line):
            raise ValueError(
                f"string-masked view must preserve character alignment on line {index}"
            )

    return original, comments, masked


def _join_lines(lines: tuple[str, ...]) -> _JoinedLines:
    starts: list[int] = []
    offset = 0

    for index, line in enumerate(lines):
        starts.append(offset)
        offset += len(line)
        if index + 1 < len(lines):
            offset += 1

    return _JoinedLines(
        lines=lines,
        text="\n".join(lines),
        starts=tuple(starts),
    )


def _line_tuple(
    values: Sequence[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence of source lines")

    result = tuple(values)
    for index, value in enumerate(result, start=1):
        if not isinstance(value, str):
            raise TypeError(f"{field_name}[{index}] must be a string")
        if "\n" in value or "\r" in value:
            raise ValueError(f"{field_name}[{index}] must not contain newline characters")
        if "\x00" in value:
            raise ValueError(f"{field_name}[{index}] must not contain NUL characters")

    return result


def _block_tuple(
    values: Iterable[StructuralBlock],
    *,
    expected_kind: StructuralBlockKind,
) -> tuple[StructuralBlock, ...]:
    raw_values: object = values
    if isinstance(raw_values, (str, bytes)):
        raise TypeError("blocks must be an iterable of StructuralBlock values")

    result = tuple(values)
    if not all(isinstance(item, StructuralBlock) and item.kind is expected_kind for item in result):
        raise TypeError(f"blocks must contain {expected_kind.value} StructuralBlock values")

    return tuple(sorted(result, key=_block_sort_key))


def _optional_path(
    value: object,
    *,
    field_name: str,
) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path or None")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    text = _text(value, field_name=field_name)
    if not text.strip():
        raise ValueError(f"{field_name} must not be empty")
    if text != text.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
    return text


def _positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _block_sort_key(
    block: StructuralBlock,
) -> tuple[int, int, int, str]:
    return (
        block.start_line,
        block.end_line,
        block.start_column,
        block.source_text,
    )


def _diagnostic_sort_key(
    diagnostic: StructureDiagnostic,
) -> tuple[int, int, str, str]:
    return (
        diagnostic.start_line,
        diagnostic.end_line,
        diagnostic.kind.value,
        diagnostic.code.value,
    )


def _finding_sort_key(
    finding: StructureFinding,
) -> tuple[int, int, int, int, str]:
    rule_order = {
        RUNTIME_STRING_MATCH_RULE_ID: 0,
        UNTYPED_CASE_STRING_PATTERN_RULE_ID: 1,
        UNTYPED_TABLE_STRING_PATTERN_RULE_ID: 2,
    }
    return (
        rule_order.get(finding.rule_id, 99),
        finding.start_line,
        finding.end_line,
        finding.start_column,
        finding.excerpt,
    )


__all__ = (
    "DEFAULT_MAX_BLOCK_LINES",
    "DEFAULT_MAX_CASE_HEADER_LINES",
    "DEFAULT_MAX_EXCERPT_CHARS",
    "DEFAULT_MAX_EXCERPT_LINES",
    "RUNTIME_STRING_MATCH_COUNT_FIELD",
    "RUNTIME_STRING_MATCH_RULE_ID",
    "UNTYPED_CASE_STRING_PATTERN_COUNT_FIELD",
    "UNTYPED_CASE_STRING_PATTERN_RULE_ID",
    "UNTYPED_TABLE_STRING_PATTERN_COUNT_FIELD",
    "UNTYPED_TABLE_STRING_PATTERN_RULE_ID",
    "SourceViews",
    "StructuralBlock",
    "StructuralBlockCollection",
    "StructuralBlockKind",
    "StructureDiagnostic",
    "StructureDiagnosticCode",
    "StructureFinding",
    "StructureRuleResult",
    "collect_structural_blocks",
    "contains_explicit_str_pattern_type",
    "contains_string_concatenation_pattern",
    "contains_string_literal_branch",
    "find_runtime_string_matches",
    "find_untyped_case_string_patterns",
    "find_untyped_table_string_patterns",
    "scan_structure_rules",
)
