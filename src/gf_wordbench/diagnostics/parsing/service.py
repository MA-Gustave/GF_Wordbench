from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Final, cast

from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticLine,
    DiagnosticMatchResult,
    DiagnosticParseResult,
    DiagnosticPattern,
    DiagnosticRecord,
    DiagnosticSeverity,
    DiagnosticStream,
    PatternConfidence,
    PatternMatch,
    records_from_matches,
)
from gf_wordbench.diagnostics.patterns.common import select_diagnostic_patterns
from gf_wordbench.kernel.statuses import ErrorKind, ExecutionState, ValidationStatus

from .deduplication import deduplicated_records
from .matcher import MatcherWarningCode, PatternMatchBatch, match_diagnostic_patterns
from .primary import DiagnosticRecordLike, select_primary_diagnostic

PARSER_VERSION: Final[str] = "1.0"
MAX_PARSE_WARNINGS: Final[int] = 64
MAX_WARNING_LENGTH: Final[int] = 1_000
_MAX_FALLBACK_EXCERPT: Final[int] = 8_192
PatternProvider = Callable[[DiagnosticEvidence], Sequence[DiagnosticPattern]]


@dataclass(frozen=True, slots=True)
class DiagnosticParsingService:
    pattern_provider: PatternProvider = select_diagnostic_patterns
    max_warnings: int = MAX_PARSE_WARNINGS

    def __post_init__(self) -> None:
        if not callable(self.pattern_provider):
            raise TypeError("pattern_provider must be callable")
        if type(self.max_warnings) is not int or self.max_warnings < 1:
            raise ValueError("max_warnings must be a positive integer")

    def parse(
        self,
        evidence: DiagnosticEvidence,
        *,
        patterns: Sequence[DiagnosticPattern] | None = None,
    ) -> DiagnosticParseResult:
        if not isinstance(evidence, DiagnosticEvidence):
            raise TypeError("evidence must be DiagnosticEvidence")
        preflight = _preflight(evidence, max_warnings=self.max_warnings)
        if preflight is not None:
            return preflight
        try:
            return self._parse(evidence, patterns=patterns)
        except Exception as exc:
            return _failure(evidence, exc, max_warnings=self.max_warnings)

    def _parse(
        self,
        evidence: DiagnosticEvidence,
        *,
        patterns: Sequence[DiagnosticPattern] | None,
    ) -> DiagnosticParseResult:
        selected = _resolve_patterns(evidence, patterns=patterns, provider=self.pattern_provider)
        matched = _match(evidence, selected)
        records = matched.records
        if not records and evidence.exit_code not in (None, 0):
            records = (_fallback_record(evidence),)
            matched = DiagnosticMatchResult(
                records=records,
                warnings=matched.warnings,
                patterns_considered=matched.patterns_considered + 1,
                patterns_matched=matched.patterns_matched + 1,
                unknown_lines=matched.unknown_lines,
                limits_reached=matched.limits_reached,
                parse_complete=matched.parse_complete,
                contract_error=matched.contract_error,
            )
        primary_candidate = select_primary_diagnostic(
            cast(
                "Iterable[DiagnosticRecordLike]",
                deduplicated_records(records),
            ),
            exit_code=evidence.exit_code,
        )
        primary = primary_candidate
        if primary is not None and not isinstance(primary, DiagnosticRecord):
            raise TypeError("select_primary_diagnostic must return DiagnosticRecord or None")
        complete = not any(
            (
                evidence.stdout_truncated,
                evidence.stderr_truncated,
                evidence.decoding_lossy,
                not evidence.capture_complete,
                matched.limits_reached,
                not matched.parse_complete,
            )
        )
        warnings = _merge_warnings(
            _evidence_warnings(evidence),
            matched.warnings,
            limit=self.max_warnings,
        )
        if not complete:
            warnings = _merge_warnings(
                warnings,
                ("diagnostic parsing requires complete and lossless evidence",),
                limit=self.max_warnings,
            )
        status = ValidationStatus.OK
        if matched.contract_error or not complete:
            status = ValidationStatus.ERROR
        return _result(
            evidence=evidence,
            status=status,
            records=records,
            warnings=warnings,
            primary=primary,
            parse_complete=complete,
            patterns_considered=matched.patterns_considered,
            patterns_matched=matched.patterns_matched,
            unknown_lines=matched.unknown_lines,
            limits_reached=matched.limits_reached,
        )


_DEFAULT_SERVICE: Final[DiagnosticParsingService] = DiagnosticParsingService()


def parse_diagnostics(
    evidence: DiagnosticEvidence,
    *,
    patterns: Sequence[DiagnosticPattern] | None = None,
) -> DiagnosticParseResult:
    return _DEFAULT_SERVICE.parse(evidence, patterns=patterns)


def _preflight(
    evidence: DiagnosticEvidence,
    *,
    max_warnings: int,
) -> DiagnosticParseResult | None:
    if evidence.stdout_text is not None or evidence.stderr_text is not None:
        return None
    if evidence.execution_state is ExecutionState.LAUNCH_FAILED:
        return _result(
            evidence=evidence,
            status=ValidationStatus.SKIPPED,
            records=(),
            warnings=(
                "diagnostic text parsing was skipped because the process did "
                "not launch and no streams exist",
            ),
            primary=None,
            parse_complete=True,
            patterns_considered=0,
            patterns_matched=0,
            unknown_lines=0,
            limits_reached=False,
        )
    return _result(
        evidence=evidence,
        status=ValidationStatus.ERROR,
        records=(),
        warnings=_merge_warnings(
            ("raw stdout and stderr text are unavailable for diagnostic parsing",),
            _evidence_warnings(evidence),
            limit=max_warnings,
        ),
        primary=None,
        parse_complete=False,
        patterns_considered=0,
        patterns_matched=0,
        unknown_lines=0,
        limits_reached=False,
    )


def _resolve_patterns(
    evidence: DiagnosticEvidence,
    *,
    patterns: Sequence[DiagnosticPattern] | None,
    provider: PatternProvider,
) -> tuple[DiagnosticPattern, ...]:
    provided: object = provider(evidence) if patterns is None else patterns
    if isinstance(provided, (str, bytes, bytearray)) or not isinstance(
        provided, Sequence
    ):
        raise TypeError("patterns must be a sequence of DiagnosticPattern")
    resolved = tuple(provided)
    identifiers: set[str] = set()
    for index, pattern in enumerate(resolved):
        if not isinstance(pattern, DiagnosticPattern):
            raise TypeError(f"patterns[{index}] must be DiagnosticPattern")
        if pattern.pattern_id in identifiers:
            raise ValueError(f"duplicate diagnostic pattern ID: {pattern.pattern_id}")
        identifiers.add(pattern.pattern_id)
    return tuple(sorted(resolved, key=lambda item: (item.priority, item.pattern_id)))


def _match(
    evidence: DiagnosticEvidence,
    patterns: tuple[DiagnosticPattern, ...],
) -> DiagnosticMatchResult:
    batch = match_diagnostic_patterns(patterns, evidence)
    if not isinstance(batch, PatternMatchBatch):
        raise TypeError("match_diagnostic_patterns must return PatternMatchBatch")
    matches: list[PatternMatch] = []
    for index, value in enumerate(batch.matches):
        if not isinstance(value, PatternMatch):
            raise TypeError(f"matcher result {index} must be PatternMatch")
        matches.append(value)
    records = records_from_matches(matches)
    limit_codes = {
        MatcherWarningCode.MATCH_LIMIT_REACHED,
        MatcherWarningCode.WARNING_LIMIT_REACHED,
    }
    warnings = tuple(
        (
            f"{warning.code.value} [{warning.pattern_id}]: {warning.message}"
            if warning.pattern_id is not None
            else f"{warning.code.value}: {warning.message}"
        )
        for warning in batch.warnings
    )
    return DiagnosticMatchResult(
        records=records,
        warnings=warnings,
        patterns_considered=len(batch.attempted_pattern_ids),
        patterns_matched=len({record.pattern_id for record in records}),
        unknown_lines=_unknown_lines(evidence, records),
        limits_reached=any(warning.code in limit_codes for warning in batch.warnings),
        parse_complete=batch.complete,
        contract_error=False,
    )


def _fallback_record(evidence: DiagnosticEvidence) -> DiagnosticRecord:
    candidate = _fallback_line(evidence)
    if candidate is None:
        match = PatternMatch(
            pattern_id="DP-FALLBACK-001",
            operation=evidence.operation_kind,
            stream=None,
            start_line=None,
            end_line=None,
            severity=DiagnosticSeverity.ERROR,
            error_kind=ErrorKind.OTHER,
            message=(
                f"Process exited with code {evidence.exit_code} without a "
                "recognized diagnostic message"
            ),
            confidence=PatternConfidence.FALLBACK,
            is_unknown=True,
            metadata={"exit_code": evidence.exit_code},
        )
    else:
        raw = (
            evidence.stderr_text
            if candidate.stream is DiagnosticStream.STDERR
            else evidence.stdout_text
        ) or ""
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        if len(raw) > _MAX_FALLBACK_EXCERPT:
            raw = raw[: _MAX_FALLBACK_EXCERPT - 1] + "…"
        match = PatternMatch(
            pattern_id="DP-FALLBACK-002",
            operation=evidence.operation_kind,
            stream=candidate.stream,
            start_line=candidate.line_number,
            end_line=candidate.line_number,
            severity=DiagnosticSeverity.ERROR,
            error_kind=ErrorKind.OTHER,
            message=candidate.text.strip(),
            detail=f"unrecognized process failure; exit_code={evidence.exit_code}",
            confidence=PatternConfidence.FALLBACK,
            raw_excerpt=raw,
            is_unknown=True,
            metadata={"exit_code": evidence.exit_code},
        )
    return DiagnosticRecord.from_match(match)


def _fallback_line(evidence: DiagnosticEvidence) -> DiagnosticLine | None:
    ordered = sorted(
        _lines(evidence),
        key=lambda line: (
            0 if line.stream is DiagnosticStream.STDERR else 1,
            line.line_number,
        ),
    )
    for line in ordered:
        text = line.text.strip()
        folded = text.casefold()
        progress = (
            folded.startswith("- compiling")
            or folded.startswith("linking")
            or folded.startswith("writing")
        )
        if text and not progress:
            return line
    return None


def _lines(evidence: DiagnosticEvidence) -> tuple[DiagnosticLine, ...]:
    sources = (
        (DiagnosticStream.STDOUT, evidence.stdout_text, evidence.stdout_path),
        (DiagnosticStream.STDERR, evidence.stderr_text, evidence.stderr_path),
    )
    return tuple(
        DiagnosticLine(stream=stream, line_number=number, text=value, raw_path=path)
        for stream, text, path in sources
        if text is not None
        for number, value in enumerate(text.splitlines(), start=1)
    )


def _unknown_lines(
    evidence: DiagnosticEvidence,
    records: tuple[DiagnosticRecord, ...],
) -> int:
    claimed = {
        (stream, number)
        for record in records
        if isinstance((stream := record.stream), DiagnosticStream)
        and stream in (DiagnosticStream.STDOUT, DiagnosticStream.STDERR)
        and record.start_line is not None
        for number in range(record.start_line, (record.end_line or record.start_line) + 1)
    }
    return sum(
        line.text.strip() != "" and (line.stream, line.line_number) not in claimed
        for line in _lines(evidence)
    )


def _evidence_warnings(evidence: DiagnosticEvidence) -> tuple[str, ...]:
    candidates = (
        (evidence.stdout_truncated, "stdout evidence is truncated"),
        (evidence.stderr_truncated, "stderr evidence is truncated"),
        (evidence.decoding_lossy, "stream decoding was lossy"),
        (not evidence.capture_complete, "diagnostic evidence capture is incomplete"),
    )
    return tuple(message for active, message in candidates if active)


def _result(
    *,
    evidence: DiagnosticEvidence,
    status: ValidationStatus,
    records: tuple[DiagnosticRecord, ...],
    warnings: tuple[str, ...],
    primary: DiagnosticRecord | None,
    parse_complete: bool,
    patterns_considered: int,
    patterns_matched: int,
    unknown_lines: int,
    limits_reached: bool,
) -> DiagnosticParseResult:
    if status is ValidationStatus.FAIL:
        raise ValueError("the diagnostic parser must not return FAIL")
    primary_kind: ErrorKind | str | None = None
    if primary is not None:
        primary_kind = primary.error_kind
    elif status is ValidationStatus.OK:
        primary_kind = ErrorKind.OK
    return DiagnosticParseResult(
        status=status,
        parser_version=PARSER_VERSION,
        gf_version=evidence.gf_version,
        operation_kind=evidence.operation_kind,
        records=records,
        warnings=warnings,
        primary_record_id=primary.record_id if primary is not None else None,
        primary_error_kind=primary_kind,
        primary_message=primary.message if primary is not None else "",
        primary_detail=primary.detail if primary is not None else "",
        fatal_detected=any(record.is_fatal for record in records),
        unknown_failure_output=any(record.is_unknown for record in records),
        stdout_truncated=evidence.stdout_truncated,
        stderr_truncated=evidence.stderr_truncated,
        decoding_lossy=evidence.decoding_lossy,
        parse_complete=parse_complete,
        patterns_considered=patterns_considered,
        patterns_matched=patterns_matched,
        records_emitted=len(records),
        unknown_lines=unknown_lines,
        limits_reached=limits_reached,
    )


def _failure(
    evidence: DiagnosticEvidence,
    exc: Exception,
    *,
    max_warnings: int,
) -> DiagnosticParseResult:
    return _result(
        evidence=evidence,
        status=ValidationStatus.ERROR,
        records=(),
        warnings=_merge_warnings(
            _evidence_warnings(evidence),
            (f"diagnostic parser failed: {type(exc).__name__}",),
            limit=max_warnings,
        ),
        primary=None,
        parse_complete=False,
        patterns_considered=0,
        patterns_matched=0,
        unknown_lines=0,
        limits_reached=False,
    )


def _merge_warnings(
    *groups: Iterable[str],
    limit: int,
) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        if isinstance(group, (str, bytes, bytearray)):
            raise TypeError("warning groups must be iterables of strings")
        for item in group:
            if not isinstance(item, str):
                raise TypeError("warnings must contain strings")
            normalized = " ".join(item.split())
            if not normalized:
                continue
            if len(normalized) > MAX_WARNING_LENGTH:
                normalized = normalized[: MAX_WARNING_LENGTH - 1] + "…"
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)
            if len(merged) == limit:
                return tuple(merged)
    return tuple(merged)


__all__ = (
    "MAX_PARSE_WARNINGS",
    "PARSER_VERSION",
    "DiagnosticParsingService",
    "PatternProvider",
    "parse_diagnostics",
)
