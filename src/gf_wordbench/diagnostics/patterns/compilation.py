"""Canonical GF compilation diagnostic patterns."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import re
from typing import Final

from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticLine,
    DiagnosticPattern,
    DiagnosticSeverity,
    DiagnosticStream,
    PatternConfidence,
    PatternMatch,
)
from gf_wordbench.kernel.statuses import ErrorKind

_INTERNAL_ANCHOR: Final = "Internal error in GeneratePMCFG"
_INTERNAL_DETAIL: Final = "GeneratePMCFG"
_TYPE_EXPECTED_RE: Final = re.compile(r"^\s*expected:\s*(.*)$")
_TYPE_INFERRED_RE: Final = re.compile(r"^\s*inferred:\s*(.*)$")
_TYPE_CONTEXT_RE: Final = re.compile(r"Happened in[^\r\n]*")
_SYNTAX_RE: Final = re.compile(r"^(?P<message>.*(?:Syntax error|Parse error|Unexpected token).*)$")
_CIRCULAR_DEFINITION_RE: Final = re.compile(
    r"^\s*(?P<message>circular definitions?:\s*.+?)\s*$",
    re.IGNORECASE,
)
_UNIFY_INFORMATION_RE: Final = re.compile(
    r"^\s*(?P<message>cannot unify the information)\s*$",
    re.IGNORECASE,
)
_CONSTANT_NOT_FOUND_RE: Final = re.compile(
    r"^\s*(?P<message>(?:constant not found:\s*.+?|unknown qualified constant\s+.+?))\s*$",
    re.IGNORECASE,
)
_MAX_EXCERPT_LINES: Final = 7
_MAX_EXCERPT_CHARS: Final = 4096

_COMPILE_OPERATIONS: Final = frozenset({"compile", "pgf_build", "scenario"})
_TEXT_STREAMS: Final = frozenset({"stdout", "stderr"})


def _operation_value(evidence: DiagnosticEvidence) -> str:
    value = evidence.operation_kind
    return value.value if hasattr(value, "value") else str(value)


def _evidence_lines(evidence: DiagnosticEvidence) -> tuple[DiagnosticLine, ...]:
    lines: list[DiagnosticLine] = []
    for stream, text in (
        (DiagnosticStream.STDOUT, evidence.stdout_text),
        (DiagnosticStream.STDERR, evidence.stderr_text),
    ):
        if text is None:
            continue
        lines.extend(
            DiagnosticLine(
                stream=stream,
                line_number=line_number,
                text=line_text,
            )
            for line_number, line_text in enumerate(text.splitlines(), start=1)
        )
    return tuple(lines)


def _ordered_lines(evidence: DiagnosticEvidence) -> tuple[DiagnosticLine, ...]:
    return tuple(
        sorted(
            _evidence_lines(evidence),
            key=lambda item: (
                0 if item.stream is DiagnosticStream.STDOUT else 1,
                item.line_number,
            ),
        )
    )


def _stream_lines(
    lines: Sequence[DiagnosticLine],
    stream: DiagnosticStream,
) -> tuple[DiagnosticLine, ...]:
    return tuple(line for line in lines if line.stream is stream)


def _bounded_excerpt(
    lines: Sequence[DiagnosticLine],
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


def _combined_excerpt(lines: Sequence[DiagnosticLine]) -> str:
    rendered = "\n".join(f"[{line.stream.value}:{line.line_number}] {line.text}" for line in lines)
    if len(rendered) <= _MAX_EXCERPT_CHARS:
        return rendered
    return rendered[: _MAX_EXCERPT_CHARS - 1] + "…"


def _build_match(
    *,
    pattern_id: str,
    source_stream: DiagnosticStream | None,
    line_number: int,
    severity: DiagnosticSeverity,
    error_kind: ErrorKind,
    confidence: PatternConfidence,
    message: str,
    detail: str,
    raw_excerpt: str,
    combined_streams: bool = False,
) -> PatternMatch:
    metadata = {"legacy_source_stream": "combined"} if combined_streams else {}
    return PatternMatch(
        pattern_id=pattern_id,
        operation="compile",
        stream=source_stream,
        start_line=line_number,
        end_line=line_number,
        severity=severity,
        error_kind=error_kind,
        message=message,
        detail=detail,
        confidence=confidence,
        raw_excerpt=raw_excerpt,
        metadata=metadata,
    )


def _match_internal(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in (DiagnosticStream.STDOUT, DiagnosticStream.STDERR):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            if _INTERNAL_ANCHOR not in line.text:
                continue
            message = line.text.strip() or _INTERNAL_ANCHOR
            return _build_match(
                pattern_id="DP-GFINT-001",
                source_stream=stream,
                line_number=line.line_number,
                severity=DiagnosticSeverity.FATAL,
                error_kind=ErrorKind.INTERNAL,
                confidence=PatternConfidence.HIGH,
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
    expected: tuple[DiagnosticLine, str] | None = None
    inferred: tuple[DiagnosticLine, str] | None = None
    context: tuple[DiagnosticLine, str] | None = None

    for line in ordered:
        expected_match = _TYPE_EXPECTED_RE.match(line.text)
        if expected is None and expected_match is not None:
            expected = (line, expected_match.group(1))
        inferred_match = _TYPE_INFERRED_RE.match(line.text)
        if inferred is None and inferred_match is not None:
            inferred = (line, inferred_match.group(1))
        context_match = _TYPE_CONTEXT_RE.search(line.text)
        if context is None and context_match is not None:
            context = (line, context_match.group(0).strip())

    if expected is None or inferred is None:
        return None

    expected_line, expected_value = expected
    inferred_line, inferred_value = inferred
    selected = [expected_line, inferred_line]
    if context is not None:
        selected.append(context[0])
    selected.sort(
        key=lambda item: (
            0 if item.stream is DiagnosticStream.STDOUT else 1,
            item.line_number,
        )
    )

    same_stream = expected_line.stream is inferred_line.stream
    source_stream = expected_line.stream if same_stream else None
    message = context[1] if context is not None else "Type error"
    detail = f"expected: {expected_value} | inferred: {inferred_value}"

    if source_stream is None:
        excerpt = _combined_excerpt(selected)
        line_number = min(expected_line.line_number, inferred_line.line_number)
    else:
        stream_lines = _stream_lines(ordered, source_stream)
        line_to_index = {line.line_number: index for index, line in enumerate(stream_lines)}
        selected_indexes = [
            line_to_index[expected_line.line_number],
            line_to_index[inferred_line.line_number],
        ]
        if context is not None and context[0].stream is source_stream:
            selected_indexes.append(line_to_index[context[0].line_number])
        excerpt = _bounded_excerpt(stream_lines, selected_indexes)
        line_number = min(
            expected_line.line_number,
            inferred_line.line_number,
        )

    return _build_match(
        pattern_id="DP-GFTYPE-001",
        source_stream=source_stream,
        line_number=line_number,
        severity=DiagnosticSeverity.ERROR,
        error_kind=ErrorKind.TYPE,
        confidence=PatternConfidence.HIGH,
        message=message,
        detail=detail,
        raw_excerpt=excerpt,
        combined_streams=not same_stream,
    )


def _match_unify_information(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in (DiagnosticStream.STDERR, DiagnosticStream.STDOUT):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            match = _UNIFY_INFORMATION_RE.match(line.text)
            if match is None:
                continue
            return _build_match(
                pattern_id="DP-GFUNIFY-001",
                source_stream=stream,
                line_number=line.line_number,
                severity=DiagnosticSeverity.ERROR,
                error_kind=ErrorKind.TYPE,
                confidence=PatternConfidence.HIGH,
                message=match.group("message").strip(),
                detail="GF could not merge two declarations/overloads with incompatible information",
                raw_excerpt=_bounded_excerpt(stream_lines, (index,)),
            )
    return None


def _match_constant_not_found(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in (DiagnosticStream.STDERR, DiagnosticStream.STDOUT):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            match = _CONSTANT_NOT_FOUND_RE.match(line.text)
            if match is None:
                continue
            return _build_match(
                pattern_id="DP-GFCONST-001",
                source_stream=stream,
                line_number=line.line_number,
                severity=DiagnosticSeverity.ERROR,
                error_kind=ErrorKind.TYPE,
                confidence=PatternConfidence.HIGH,
                message=match.group("message").strip(),
                detail="GF could not resolve a referenced constant/type in the active module scope",
                raw_excerpt=_bounded_excerpt(stream_lines, (index,)),
            )
    return None


def _match_circular_definition(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in (DiagnosticStream.STDERR, DiagnosticStream.STDOUT):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            match = _CIRCULAR_DEFINITION_RE.match(line.text)
            if match is None:
                continue
            return _build_match(
                pattern_id="DP-GFCIRC-001",
                source_stream=stream,
                line_number=line.line_number,
                severity=DiagnosticSeverity.ERROR,
                error_kind=ErrorKind.TYPE,
                confidence=PatternConfidence.HIGH,
                message=match.group("message").strip(),
                detail="GF rejected a circular definition group",
                raw_excerpt=_bounded_excerpt(stream_lines, (index,)),
            )
    return None


def _match_syntax(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    if _operation_value(evidence) not in _COMPILE_OPERATIONS:
        return None
    ordered = _ordered_lines(evidence)
    for stream in (DiagnosticStream.STDOUT, DiagnosticStream.STDERR):
        stream_lines = _stream_lines(ordered, stream)
        for index, line in enumerate(stream_lines):
            match = _SYNTAX_RE.match(line.text)
            if match is None:
                continue
            return _build_match(
                pattern_id="DP-GFSYN-001",
                source_stream=stream,
                line_number=line.line_number,
                severity=DiagnosticSeverity.ERROR,
                error_kind=ErrorKind.SYNTAX,
                confidence=PatternConfidence.MEDIUM,
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
    confidence=PatternConfidence.HIGH,
    error_kind=ErrorKind.INTERNAL,
    severity=DiagnosticSeverity.FATAL,
    matcher=_match_internal,
)

GF_TYPE_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFTYPE-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=400,
    confidence=PatternConfidence.HIGH,
    error_kind=ErrorKind.TYPE,
    severity=DiagnosticSeverity.ERROR,
    matcher=_match_type,
)

GF_UNIFY_INFORMATION_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFUNIFY-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=460,
    confidence=PatternConfidence.HIGH,
    error_kind=ErrorKind.TYPE,
    severity=DiagnosticSeverity.ERROR,
    matcher=_match_unify_information,
)

GF_CONSTANT_NOT_FOUND_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFCONST-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=455,
    confidence=PatternConfidence.HIGH,
    error_kind=ErrorKind.TYPE,
    severity=DiagnosticSeverity.ERROR,
    matcher=_match_constant_not_found,
)

GF_CIRCULAR_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFCIRC-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=450,
    confidence=PatternConfidence.HIGH,
    error_kind=ErrorKind.TYPE,
    severity=DiagnosticSeverity.ERROR,
    matcher=_match_circular_definition,
)

GF_SYNTAX_PATTERN: Final = DiagnosticPattern(
    pattern_id="DP-GFSYN-001",
    operations=_COMPILE_OPERATIONS,
    streams=_TEXT_STREAMS,
    priority=500,
    confidence=PatternConfidence.MEDIUM,
    error_kind=ErrorKind.SYNTAX,
    severity=DiagnosticSeverity.ERROR,
    matcher=_match_syntax,
)

COMPILATION_PATTERNS: Final = (
    GF_INTERNAL_PATTERN,
    GF_TYPE_PATTERN,
    GF_UNIFY_INFORMATION_PATTERN,
    GF_CONSTANT_NOT_FOUND_PATTERN,
    GF_CIRCULAR_PATTERN,
    GF_SYNTAX_PATTERN,
)


def compilation_patterns() -> tuple[DiagnosticPattern, ...]:
    return COMPILATION_PATTERNS


__all__ = (
    "COMPILATION_PATTERNS",
    "GF_CIRCULAR_PATTERN",
    "GF_CONSTANT_NOT_FOUND_PATTERN",
    "GF_INTERNAL_PATTERN",
    "GF_SYNTAX_PATTERN",
    "GF_TYPE_PATTERN",
    "GF_UNIFY_INFORMATION_PATTERN",
    "compilation_patterns",
)
