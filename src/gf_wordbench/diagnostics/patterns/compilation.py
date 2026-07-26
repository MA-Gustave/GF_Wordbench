"""Canonical GF compilation diagnostic patterns."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Final

from gf_wordbench.diagnostics.models import DiagnosticEvidence

from .common import DiagnosticPattern, EvidenceLine, PatternMatch

_INTERNAL_ANCHOR: Final = "Internal error in GeneratePMCFG"
_INTERNAL_DETAIL: Final = "GeneratePMCFG"
_TYPE_EXPECTED_RE: Final = re.compile(r"^\s*expected:\s*(.*)$")
_TYPE_INFERRED_RE: Final = re.compile(r"^\s*inferred:\s*(.*)$")
_TYPE_CONTEXT_RE: Final = re.compile(r"Happened in[^\r\n]*")
_SYNTAX_RE: Final = re.compile(
    r"^(?P<message>.*(?:Syntax error|Parse error|Unexpected token).*)$"
)
_MAX_EXCERPT_LINES: Final = 7
_MAX_EXCERPT_CHARS: Final = 4096

_COMPILE_OPERATIONS: Final = frozenset({"compile", "pgf_build", "scenario"})
_TEXT_STREAMS: Final = frozenset({"stdout", "stderr"})


def _operation_value(evidence: DiagnosticEvidence) -> str:
    value = evidence.operation_kind
    return value.value if hasattr(value, "value") else str(value)


def _ordered_lines(evidence: DiagnosticEvidence) -> tuple[EvidenceLine, ...]:
    lines = tuple(evidence.lines)
    return tuple(
        sorted(
            lines,
            key=lambda item: (
                0 if item.stream == "stdout" else 1,
                item.line_number,
            ),
        )
    )


def _stream_lines(
    lines: Sequence[EvidenceLine],
    stream: str,
) -> tuple[EvidenceLine, ...]:
    return tuple(line for line in lines if line.stream == stream)


def _bounded_excerpt(
    lines: Sequence[EvidenceLine],
    selected_indexes: Iterable[int],
) -> str:
    indexes = tuple(sorted(set(selected_indexes)))
    if not indexes:
        return ""
    first = max(0, indexes[0] - 2)
    last = min(len(lines), indexes[-1] + 3)
    if last - first > _MAX_EXCERPT_LINES:
        last = first + _MAX_EXCERPT_LINES
    rendered = "\n".join(lines[index].text for index in range(first, last))
    if len(rendered) <= _MAX_EXCERPT_CHARS:
        return rendered
    return rendered[: _MAX_EXCERPT_CHARS - 1] + "…"


def _combined_excerpt(lines: Sequence[EvidenceLine]) -> str:
    rendered = "\n".join(
        f"[{line.stream}:{line.line_number}] {line.text}" for line in lines
    )
    if len(rendered) <= _MAX_EXCERPT_CHARS:
        return rendered
    return rendered[: _MAX_EXCERPT_CHARS - 1] + "…"


def _match_internal(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in ("stdout", "stderr"):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            if _INTERNAL_ANCHOR not in line.text:
                continue
            message = line.text.strip() or _INTERNAL_ANCHOR
            return PatternMatch(
                pattern_id="DP-GFINT-001",
                source_stream=stream,
                line_number=line.line_number,
                message=message,
                detail=_INTERNAL_DETAIL,
                raw_excerpt=_bounded_excerpt(stream_lines, (index,)),
            )
    return None


def _match_type(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    expected: tuple[int, EvidenceLine, str] | None = None
    inferred: tuple[int, EvidenceLine, str] | None = None
    context: tuple[int, EvidenceLine, str] | None = None

    for index, line in enumerate(ordered):
        expected_match = _TYPE_EXPECTED_RE.match(line.text)
        if expected is None and expected_match is not None:
            expected = (index, line, expected_match.group(1))
        inferred_match = _TYPE_INFERRED_RE.match(line.text)
        if inferred is None and inferred_match is not None:
            inferred = (index, line, inferred_match.group(1))
        context_match = _TYPE_CONTEXT_RE.search(line.text)
        if context is None and context_match is not None:
            context = (index, line, context_match.group(0).strip())

    if expected is None or inferred is None:
        return None

    expected_index, expected_line, expected_value = expected
    inferred_index, inferred_line, inferred_value = inferred
    selected = [expected_line, inferred_line]
    if context is not None:
        selected.append(context[1])
    selected.sort(
        key=lambda item: (
            0 if item.stream == "stdout" else 1,
            item.line_number,
        )
    )

    source_stream = (
        expected_line.stream
        if expected_line.stream == inferred_line.stream
        else "combined"
    )
    message = context[2] if context is not None else "Type error"
    detail = f"expected: {expected_value} | inferred: {inferred_value}"

    if source_stream == "combined":
        excerpt = _combined_excerpt(selected)
        line_number = min(expected_line.line_number, inferred_line.line_number)
    else:
        stream_lines = _stream_lines(ordered, source_stream)
        line_to_index = {
            line.line_number: index for index, line in enumerate(stream_lines)
        }
        selected_indexes = [
            line_to_index[expected_line.line_number],
            line_to_index[inferred_line.line_number],
        ]
        if context is not None and context[1].stream == source_stream:
            selected_indexes.append(line_to_index[context[1].line_number])
        excerpt = _bounded_excerpt(stream_lines, selected_indexes)
        line_number = min(
            expected_line.line_number,
            inferred_line.line_number,
        )

    return PatternMatch(
        pattern_id="DP-GFTYPE-001",
        source_stream=source_stream,
        line_number=line_number,
        message=message,
        detail=detail,
        raw_excerpt=excerpt,
    )


def _match_syntax(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in ("stdout", "stderr"):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            match = _SYNTAX_RE.match(line.text)
            if match is None:
                continue
            return PatternMatch(
                pattern_id="DP-GFSYN-001",
                source_stream=stream,
                line_number=line.line_number,
                message=match.group("message").strip(),
                detail="",
                raw_excerpt=_bounded_excerpt(stream_lines, (index,)),
            )
    return None


GF_INTERNAL_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFINT-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=300,
    confidence="high",
    error_kind="INTERNAL",
    severity="fatal",
    matcher=_match_internal,
)

GF_TYPE_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFTYPE-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=400,
    confidence="high",
    error_kind="TYPE",
    severity="error",
    matcher=_match_type,
)

GF_SYNTAX_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFSYN-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=500,
    confidence="medium",
    error_kind="SYNTAX",
    severity="error",
    matcher=_match_syntax,
)

COMPILATION_PATTERNS: Final = (
    GF_INTERNAL_PATTERN,
    GF_TYPE_PATTERN,
    GF_SYNTAX_PATTERN,
)


def compilation_patterns() -> tuple[DiagnosticPattern, ...]:
    return COMPILATION_PATTERNS


__all__ = (
    "COMPILATION_PATTERNS",
    "GF_INTERNAL_PATTERN",
    "GF_SYNTAX_PATTERN",
    "GF_TYPE_PATTERN",
    "compilation_patterns",
)
