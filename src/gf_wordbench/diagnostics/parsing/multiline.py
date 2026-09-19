"""Finite, deterministic grouping of classified diagnostic lines."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum, unique
from typing import Final


@unique
class LineRole(StrEnum):
    DIAGNOSTIC_START = "diagnostic_start"
    DIAGNOSTIC_CONTINUATION = "diagnostic_continuation"
    CONTEXT = "context"
    KNOWN_NOISE = "known_noise"
    UNKNOWN = "unknown"


@unique
class CloseReason(StrEnum):
    EXPLICIT_TERMINATION = "explicit_termination"
    NEW_DIAGNOSTIC_START = "new_diagnostic_start"
    HIGHER_PRECEDENCE_START = "higher_precedence_start"
    NON_CONTINUATION_BOUNDARY = "non_continuation_boundary"
    CONTINUATION_LIMIT = "continuation_limit"
    CHARACTER_LIMIT = "character_limit"
    RECORD_LIMIT = "record_limit"
    TOTAL_CHARACTER_LIMIT = "total_character_limit"
    STREAM_END = "stream_end"
    STREAM_TRUNCATED = "stream_truncated"


@unique
class MultilineWarningCode(StrEnum):
    ORPHAN_CONTINUATION = "orphan_continuation"
    ORPHAN_CONTEXT = "orphan_context"
    PATTERN_MISMATCH = "pattern_mismatch"
    CONTINUATION_LIMIT_REACHED = "continuation_limit_reached"
    CHARACTER_LIMIT_REACHED = "character_limit_reached"
    RECORD_LIMIT_REACHED = "record_limit_reached"
    TOTAL_CHARACTER_LIMIT_REACHED = "total_character_limit_reached"
    STREAM_TRUNCATED = "stream_truncated"


@dataclass(frozen=True, slots=True)
class MultilineLimits:
    max_continuation_lines: int = 64
    max_characters_per_record: int = 32_768
    max_records: int = 4_096
    max_total_characters: int = 8_388_608

    def __post_init__(self) -> None:
        for name in (
            "max_continuation_lines",
            "max_characters_per_record",
            "max_records",
            "max_total_characters",
        ):
            value = getattr(self, name)
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer")
            if value < 1:
                raise ValueError(f"{name} must be positive")


DEFAULT_MULTILINE_LIMITS: Final = MultilineLimits()


@dataclass(frozen=True, slots=True)
class ClassifiedLine:
    line_number: int
    text: str
    role: LineRole
    pattern_id: str | None = None
    precedence: int | None = None
    terminates: bool = False
    max_continuation_lines: int | None = None
    max_characters: int | None = None

    def __post_init__(self) -> None:
        _positive_int(self.line_number, "line_number")
        _text(self.text, "text", allow_empty=True)
        if not isinstance(self.role, LineRole):
            raise TypeError("role must be a LineRole")
        if self.pattern_id is not None:
            _identifier(self.pattern_id, "pattern_id")
        if self.role is LineRole.DIAGNOSTIC_START:
            if self.pattern_id is None:
                raise ValueError("diagnostic starts require pattern_id")
            if self.precedence is None:
                raise ValueError("diagnostic starts require precedence")
        elif self.max_continuation_lines is not None or self.max_characters is not None:
            raise ValueError("per-record limits are valid only on diagnostic starts")
        if self.precedence is not None:
            _non_negative_int(self.precedence, "precedence")
        if type(self.terminates) is not bool:
            raise TypeError("terminates must be a boolean")
        _optional_positive_int(self.max_continuation_lines, "max_continuation_lines")
        _optional_positive_int(self.max_characters, "max_characters")


@dataclass(frozen=True, slots=True)
class DiagnosticBlock:
    pattern_id: str
    precedence: int
    start_line: int
    end_line: int
    lines: tuple[str, ...]
    truncated: bool
    incomplete: bool
    close_reason: CloseReason

    def __post_init__(self) -> None:
        _identifier(self.pattern_id, "pattern_id")
        _non_negative_int(self.precedence, "precedence")
        _positive_int(self.start_line, "start_line")
        _positive_int(self.end_line, "end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        if not isinstance(self.lines, tuple) or not self.lines:
            raise ValueError("lines must be a non-empty tuple")
        for line in self.lines:
            _text(line, "lines item", allow_empty=True)
        if type(self.truncated) is not bool or type(self.incomplete) is not bool:
            raise TypeError("truncated and incomplete must be booleans")
        if not isinstance(self.close_reason, CloseReason):
            raise TypeError("close_reason must be a CloseReason")

    @property
    def continuation_lines(self) -> int:
        return len(self.lines) - 1

    @property
    def character_count(self) -> int:
        return _character_count(self.lines)

    @property
    def raw_excerpt(self) -> str:
        return "\n".join(self.lines)


@dataclass(frozen=True, slots=True)
class MultilineWarning:
    code: MultilineWarningCode
    line_number: int
    message: str
    pattern_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, MultilineWarningCode):
            raise TypeError("code must be a MultilineWarningCode")
        _positive_int(self.line_number, "line_number")
        _text(self.message, "message", allow_empty=False)
        if self.pattern_id is not None:
            _identifier(self.pattern_id, "pattern_id")


@dataclass(frozen=True, slots=True)
class MultilineGroupingResult:
    blocks: tuple[DiagnosticBlock, ...]
    unclaimed_lines: tuple[ClassifiedLine, ...]
    warnings: tuple[MultilineWarning, ...]
    consumed_line_count: int
    consumed_character_count: int
    stopped_early: bool
    stream_truncated: bool

    def __post_init__(self) -> None:
        _typed_tuple(self.blocks, DiagnosticBlock, "blocks")
        _typed_tuple(self.unclaimed_lines, ClassifiedLine, "unclaimed_lines")
        _typed_tuple(self.warnings, MultilineWarning, "warnings")
        _non_negative_int(self.consumed_line_count, "consumed_line_count")
        _non_negative_int(self.consumed_character_count, "consumed_character_count")
        if type(self.stopped_early) is not bool:
            raise TypeError("stopped_early must be a boolean")
        if type(self.stream_truncated) is not bool:
            raise TypeError("stream_truncated must be a boolean")


@dataclass(slots=True)
class _OpenBlock:
    pattern_id: str
    precedence: int
    start_line: int
    end_line: int
    max_continuation_lines: int
    max_characters: int
    lines: list[str] = field(default_factory=list)

    @property
    def continuation_count(self) -> int:
        return len(self.lines) - 1


def group_multiline_diagnostics(
    lines: Iterable[ClassifiedLine],
    *,
    limits: MultilineLimits = DEFAULT_MULTILINE_LIMITS,
    stream_truncated: bool = False,
) -> MultilineGroupingResult:
    if not isinstance(limits, MultilineLimits):
        raise TypeError("limits must be MultilineLimits")
    if type(stream_truncated) is not bool:
        raise TypeError("stream_truncated must be a boolean")
    raw_lines: object = lines
    if isinstance(raw_lines, (str, bytes)):
        raise TypeError("lines must be an iterable of ClassifiedLine")

    ordered = tuple(lines)
    _validate_order(ordered)
    blocks: list[DiagnosticBlock] = []
    unclaimed: list[ClassifiedLine] = []
    warnings: list[MultilineWarning] = []
    current: _OpenBlock | None = None
    consumed_lines = 0
    consumed_characters = 0
    stopped_early = False

    def close(
        reason: CloseReason,
        *,
        truncated: bool = False,
        incomplete: bool = False,
    ) -> None:
        nonlocal current
        if current is None:
            return
        blocks.append(
            DiagnosticBlock(
                pattern_id=current.pattern_id,
                precedence=current.precedence,
                start_line=current.start_line,
                end_line=current.end_line,
                lines=tuple(current.lines),
                truncated=truncated,
                incomplete=incomplete,
                close_reason=reason,
            )
        )
        current = None

    for line in ordered:
        cost = len(line.text) + (1 if consumed_lines else 0)
        if consumed_characters + cost > limits.max_total_characters:
            close(CloseReason.TOTAL_CHARACTER_LIMIT, truncated=True, incomplete=True)
            warnings.append(
                _warning(
                    MultilineWarningCode.TOTAL_CHARACTER_LIMIT_REACHED,
                    line,
                    "Total parsed-character limit was reached.",
                )
            )
            stopped_early = True
            break

        consumed_lines += 1
        consumed_characters += cost

        if line.role is LineRole.DIAGNOSTIC_START:
            if len(blocks) + (1 if current is not None else 0) >= limits.max_records:
                close(CloseReason.RECORD_LIMIT, truncated=True, incomplete=True)
                warnings.append(
                    _warning(
                        MultilineWarningCode.RECORD_LIMIT_REACHED,
                        line,
                        "Diagnostic-record limit was reached.",
                    )
                )
                stopped_early = True
                break

            if current is not None:
                reason = (
                    CloseReason.HIGHER_PRECEDENCE_START
                    if (line.precedence or 0) < current.precedence
                    else CloseReason.NEW_DIAGNOSTIC_START
                )
                close(reason)

            record_limit = min(
                line.max_characters or limits.max_characters_per_record,
                limits.max_characters_per_record,
            )
            start_text = line.text[:record_limit]
            start_truncated = len(start_text) != len(line.text)
            current = _OpenBlock(
                pattern_id=line.pattern_id or "",
                precedence=line.precedence or 0,
                start_line=line.line_number,
                end_line=line.line_number,
                max_continuation_lines=min(
                    line.max_continuation_lines or limits.max_continuation_lines,
                    limits.max_continuation_lines,
                ),
                max_characters=record_limit,
                lines=[start_text],
            )
            if start_truncated:
                pattern_id = current.pattern_id
                close(CloseReason.CHARACTER_LIMIT, truncated=True, incomplete=True)
                warnings.append(
                    MultilineWarning(
                        MultilineWarningCode.CHARACTER_LIMIT_REACHED,
                        line.line_number,
                        "Diagnostic record exceeded its character limit.",
                        pattern_id,
                    )
                )
            elif line.terminates:
                close(CloseReason.EXPLICIT_TERMINATION)
            continue

        if line.role in (LineRole.DIAGNOSTIC_CONTINUATION, LineRole.CONTEXT):
            if current is None:
                unclaimed.append(line)
                warnings.append(
                    _warning(
                        MultilineWarningCode.ORPHAN_CONTINUATION
                        if line.role is LineRole.DIAGNOSTIC_CONTINUATION
                        else MultilineWarningCode.ORPHAN_CONTEXT,
                        line,
                        "Continuation line has no open diagnostic."
                        if line.role is LineRole.DIAGNOSTIC_CONTINUATION
                        else "Context line has no open diagnostic.",
                    )
                )
                continue

            if line.pattern_id is not None and line.pattern_id != current.pattern_id:
                close(CloseReason.NON_CONTINUATION_BOUNDARY)
                unclaimed.append(line)
                warnings.append(
                    _warning(
                        MultilineWarningCode.PATTERN_MISMATCH,
                        line,
                        "Continuation pattern does not match the open diagnostic.",
                    )
                )
                continue

            if current.continuation_count >= current.max_continuation_lines:
                pattern_id = current.pattern_id
                close(CloseReason.CONTINUATION_LIMIT, truncated=True, incomplete=True)
                unclaimed.append(line)
                warnings.append(
                    MultilineWarning(
                        MultilineWarningCode.CONTINUATION_LIMIT_REACHED,
                        line.line_number,
                        "Diagnostic continuation-line limit was reached.",
                        pattern_id,
                    )
                )
                continue

            prospective = (*current.lines, line.text)
            if _character_count(prospective) > current.max_characters:
                pattern_id = current.pattern_id
                close(CloseReason.CHARACTER_LIMIT, truncated=True, incomplete=True)
                unclaimed.append(line)
                warnings.append(
                    MultilineWarning(
                        MultilineWarningCode.CHARACTER_LIMIT_REACHED,
                        line.line_number,
                        "Diagnostic record exceeded its character limit.",
                        pattern_id,
                    )
                )
                continue

            current.lines.append(line.text)
            current.end_line = line.line_number
            if line.terminates:
                close(CloseReason.EXPLICIT_TERMINATION)
            continue

        close(CloseReason.NON_CONTINUATION_BOUNDARY)
        unclaimed.append(line)

    close(
        CloseReason.STREAM_TRUNCATED if stream_truncated else CloseReason.STREAM_END,
        truncated=stream_truncated,
        incomplete=stream_truncated,
    )

    if stream_truncated:
        warnings.append(
            MultilineWarning(
                MultilineWarningCode.STREAM_TRUNCATED,
                ordered[-1].line_number if ordered else 1,
                "The source stream was truncated.",
            )
        )

    return MultilineGroupingResult(
        tuple(blocks),
        tuple(unclaimed),
        tuple(warnings),
        consumed_lines,
        consumed_characters,
        stopped_early,
        stream_truncated,
    )


def _warning(
    code: MultilineWarningCode,
    line: ClassifiedLine,
    message: str,
) -> MultilineWarning:
    return MultilineWarning(code, line.line_number, message, line.pattern_id)


def _validate_order(lines: tuple[ClassifiedLine, ...]) -> None:
    previous = 0
    for line in lines:
        if not isinstance(line, ClassifiedLine):
            raise TypeError("lines must contain ClassifiedLine objects")
        if line.line_number <= previous:
            raise ValueError("line numbers must be strictly increasing")
        previous = line.line_number


def _character_count(lines: tuple[str, ...]) -> int:
    return sum(map(len, lines)) + max(0, len(lines) - 1)


def _typed_tuple(value: object, item_type: type, field_name: str) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if any(not isinstance(item, item_type) for item in value):
        raise TypeError(f"{field_name} contains an invalid item")


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name, allow_empty=False)
    if len(text) > 128:
        raise ValueError(f"{field_name} exceeds the supported length")
    return text


def _text(value: object, field_name: str, *, allow_empty: bool) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_positive_int(value: object, field_name: str) -> None:
    if value is not None:
        _positive_int(value, field_name)


__all__ = (
    "DEFAULT_MULTILINE_LIMITS",
    "ClassifiedLine",
    "CloseReason",
    "DiagnosticBlock",
    "LineRole",
    "MultilineGroupingResult",
    "MultilineLimits",
    "MultilineWarning",
    "MultilineWarningCode",
    "group_multiline_diagnostics",
)
