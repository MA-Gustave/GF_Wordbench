"""Canonical declaration-notation scan rules for GF Wordbench."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Final, TypeAlias

LineInput: TypeAlias = str | Sequence[str] | Iterable[str]

_MAX_EXCERPT_LENGTH: Final[int] = 240
_SINGLE_SLASH_EQ_MESSAGE: Final = (
    "Suspicious single backslash appears before '=>' in the same statement segment."
)
_DOUBLE_SLASH_DASH_MESSAGE: Final = (
    "Suspicious double backslash appears before '->' in the same statement segment."
)


@dataclass(frozen=True, slots=True)
class DeclarationRule:
    rule_id: str
    field_name: str
    count_unit: str
    default_interpretation: str

    def __post_init__(self) -> None:
        for field_name in (
            "rule_id",
            "field_name",
            "count_unit",
            "default_interpretation",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if not value.strip() or "\x00" in value:
                raise ValueError(f"{field_name} must be non-empty and contain no NUL")


@dataclass(frozen=True, slots=True)
class DeclarationFinding:
    rule_id: str
    field_name: str
    line: int
    column: int
    end_column: int
    excerpt: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id:
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.field_name, str) or not self.field_name:
            raise ValueError("field_name must be a non-empty string")
        if type(self.line) is not int or self.line < 1:
            raise ValueError("line must be a positive integer")
        if type(self.column) is not int or self.column < 1:
            raise ValueError("column must be a positive integer")
        if type(self.end_column) is not int or self.end_column < self.column:
            raise ValueError("end_column must be an integer not less than column")
        if not isinstance(self.excerpt, str) or "\x00" in self.excerpt:
            raise ValueError("excerpt must be a NUL-free string")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DeclarationScanResult:
    single_slash_eq: tuple[DeclarationFinding, ...] = ()
    double_slash_dash: tuple[DeclarationFinding, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("single_slash_eq", "double_slash_dash"):
            value = getattr(self, field_name)
            if not isinstance(value, tuple):
                raise TypeError(f"{field_name} must be a tuple")
            if not all(isinstance(item, DeclarationFinding) for item in value):
                raise TypeError(f"{field_name} must contain DeclarationFinding objects")

    @property
    def findings(self) -> tuple[DeclarationFinding, ...]:
        return (*self.single_slash_eq, *self.double_slash_dash)

    @property
    def counts(self) -> dict[str, int]:
        return {
            SINGLE_SLASH_EQ_RULE.field_name: len(self.single_slash_eq),
            DOUBLE_SLASH_DASH_RULE.field_name: len(self.double_slash_dash),
        }


SINGLE_SLASH_EQ_RULE: Final = DeclarationRule(
    rule_id="SCAN-NOTATION-001",
    field_name="single_slash_eq",
    count_unit="matching source line",
    default_interpretation="suspicious single-backslash before '=>'",
)

DOUBLE_SLASH_DASH_RULE: Final = DeclarationRule(
    rule_id="SCAN-NOTATION-002",
    field_name="double_slash_dash",
    count_unit="matching source line",
    default_interpretation="suspicious double-backslash before '->'",
)

DECLARATION_RULES: Final = (
    SINGLE_SLASH_EQ_RULE,
    DOUBLE_SLASH_DASH_RULE,
)


def scan_declaration_rules(
    original_lines: LineInput,
    string_masked_lines: LineInput,
) -> DeclarationScanResult:
    original = _coerce_lines(original_lines, field_name="original_lines")
    masked = _coerce_lines(
        string_masked_lines,
        field_name="string_masked_lines",
    )
    _require_aligned_views(original, masked)

    single: list[DeclarationFinding] = []
    double: list[DeclarationFinding] = []

    for line_number, (original_line, masked_line) in enumerate(
        zip(original, masked, strict=True),
        start=1,
    ):
        single_match = _first_notation_match(
            masked_line,
            slash_count=1,
            expected_arrow="=>",
            excluded_arrow="->",
        )
        if single_match is not None:
            start, end = single_match
            single.append(
                _finding(
                    rule=SINGLE_SLASH_EQ_RULE,
                    original_line=original_line,
                    line_number=line_number,
                    start=start,
                    end=end,
                    message=_SINGLE_SLASH_EQ_MESSAGE,
                )
            )

        double_match = _first_notation_match(
            masked_line,
            slash_count=2,
            expected_arrow="->",
            excluded_arrow="=>",
        )
        if double_match is not None:
            start, end = double_match
            double.append(
                _finding(
                    rule=DOUBLE_SLASH_DASH_RULE,
                    original_line=original_line,
                    line_number=line_number,
                    start=start,
                    end=end,
                    message=_DOUBLE_SLASH_DASH_MESSAGE,
                )
            )

    return DeclarationScanResult(
        single_slash_eq=tuple(single),
        double_slash_dash=tuple(double),
    )


def scan_single_slash_eq(
    original_lines: LineInput,
    string_masked_lines: LineInput,
) -> tuple[DeclarationFinding, ...]:
    return scan_declaration_rules(
        original_lines,
        string_masked_lines,
    ).single_slash_eq


def scan_double_slash_dash(
    original_lines: LineInput,
    string_masked_lines: LineInput,
) -> tuple[DeclarationFinding, ...]:
    return scan_declaration_rules(
        original_lines,
        string_masked_lines,
    ).double_slash_dash


def count_single_slash_eq(string_masked_lines: LineInput) -> int:
    masked = _coerce_lines(
        string_masked_lines,
        field_name="string_masked_lines",
    )
    return sum(
        _first_notation_match(
            line,
            slash_count=1,
            expected_arrow="=>",
            excluded_arrow="->",
        )
        is not None
        for line in masked
    )


def count_double_slash_dash(string_masked_lines: LineInput) -> int:
    masked = _coerce_lines(
        string_masked_lines,
        field_name="string_masked_lines",
    )
    return sum(
        _first_notation_match(
            line,
            slash_count=2,
            expected_arrow="->",
            excluded_arrow="=>",
        )
        is not None
        for line in masked
    )


def _first_notation_match(
    line: str,
    *,
    slash_count: int,
    expected_arrow: str,
    excluded_arrow: str,
) -> tuple[int, int] | None:
    for segment_start, segment_end in _statement_segments(line):
        match = _match_segment(
            line,
            segment_start=segment_start,
            segment_end=segment_end,
            slash_count=slash_count,
            expected_arrow=expected_arrow,
            excluded_arrow=excluded_arrow,
        )
        if match is not None:
            return match
    return None


def _match_segment(
    line: str,
    *,
    segment_start: int,
    segment_end: int,
    slash_count: int,
    expected_arrow: str,
    excluded_arrow: str,
) -> tuple[int, int] | None:
    index = segment_start
    while index < segment_end:
        if line[index] != "\\":
            index += 1
            continue

        run_start = index
        while index < segment_end and line[index] == "\\":
            index += 1
        run_length = index - run_start
        if run_length != slash_count:
            continue

        expected_index = line.find(expected_arrow, index, segment_end)
        if expected_index < 0:
            continue

        excluded_index = line.find(excluded_arrow, index, segment_end)
        if excluded_index >= 0 and excluded_index < expected_index:
            continue

        return run_start, expected_index + len(expected_arrow)

    return None


def _statement_segments(line: str) -> tuple[tuple[int, int], ...]:
    segments: list[tuple[int, int]] = []
    start = 0
    for index, character in enumerate(line):
        if character == ";":
            segments.append((start, index))
            start = index + 1
    if start < len(line):
        segments.append((start, len(line)))
    elif not segments:
        segments.append((0, 0))
    return tuple(segments)


def _finding(
    *,
    rule: DeclarationRule,
    original_line: str,
    line_number: int,
    start: int,
    end: int,
    message: str,
) -> DeclarationFinding:
    return DeclarationFinding(
        rule_id=rule.rule_id,
        field_name=rule.field_name,
        line=line_number,
        column=start + 1,
        end_column=end,
        excerpt=_bounded_excerpt(original_line),
        message=message,
    )


def _bounded_excerpt(line: str) -> str:
    excerpt = line.strip()
    if len(excerpt) <= _MAX_EXCERPT_LENGTH:
        return excerpt
    return f"{excerpt[: _MAX_EXCERPT_LENGTH - 1]}…"


def _coerce_lines(value: LineInput, *, field_name: str) -> tuple[str, ...]:
    raw_value: object = value
    if isinstance(raw_value, str):
        return tuple(raw_value.splitlines())
    if isinstance(raw_value, (bytes, bytearray)):
        raise TypeError(f"{field_name} must contain text lines")

    try:
        lines = tuple(value)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be text or an iterable of strings") from exc

    for index, line in enumerate(lines, start=1):
        if not isinstance(line, str):
            raise TypeError(f"{field_name}[{index}] must be a string")
        if "\x00" in line:
            raise ValueError(f"{field_name}[{index}] must not contain NUL")

    return tuple(_without_line_ending(line) for line in lines)


def _without_line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\n", "\r")):
        return line[:-1]
    return line


def _require_aligned_views(
    original: tuple[str, ...],
    masked: tuple[str, ...],
) -> None:
    if len(original) != len(masked):
        raise ValueError("source views must contain the same number of lines")

    for line_number, (original_line, masked_line) in enumerate(
        zip(original, masked, strict=True),
        start=1,
    ):
        if len(original_line) != len(masked_line):
            raise ValueError(
                "source views must preserve character alignment; "
                f"line {line_number} has lengths "
                f"{len(original_line)} and {len(masked_line)}"
            )


__all__ = (
    "DECLARATION_RULES",
    "DOUBLE_SLASH_DASH_RULE",
    "SINGLE_SLASH_EQ_RULE",
    "DeclarationFinding",
    "DeclarationRule",
    "DeclarationScanResult",
    "count_double_slash_dash",
    "count_single_slash_eq",
    "scan_declaration_rules",
    "scan_double_slash_dash",
    "scan_single_slash_eq",
)
