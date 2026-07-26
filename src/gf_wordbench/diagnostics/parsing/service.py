from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Final

from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticMatchResult,
    DiagnosticParseResult,
    DiagnosticPattern,
    DiagnosticRecord,
)
from gf_wordbench.diagnostics.patterns.common import select_diagnostic_patterns
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

from .deduplication import deduplicated_record_view
from .matcher import match_diagnostic_streams
from .primary import select_primary_record
from .streams import build_stream_views

PARSER_VERSION: Final[str] = "1.0"
MAX_PARSE_WARNINGS: Final[int] = 64
MAX_WARNING_LENGTH: Final[int] = 1_000

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

        preflight = _preflight_result(
            evidence,
            max_warnings=self.max_warnings,
        )
        if preflight is not None:
            return preflight

        try:
            return self._parse(evidence, patterns=patterns)
        except Exception as exc:
            return _parser_failure_result(
                evidence,
                exc,
                max_warnings=self.max_warnings,
            )

    def _parse(
        self,
        evidence: DiagnosticEvidence,
        *,
        patterns: Sequence[DiagnosticPattern] | None,
    ) -> DiagnosticParseResult:
        selected_patterns = _resolve_patterns(
            evidence,
            patterns=patterns,
            provider=self.pattern_provider,
        )
        stream_views = build_stream_views(evidence)
        matched = match_diagnostic_streams(
            evidence=evidence,
            streams=stream_views,
            patterns=selected_patterns,
        )
        if not isinstance(matched, DiagnosticMatchResult):
            raise TypeError(
                "match_diagnostic_streams must return DiagnosticMatchResult"
            )

        records = _record_tuple(matched.records)
        primary_candidates = deduplicated_record_view(records)
        primary = select_primary_record(
            primary_candidates,
            evidence=evidence,
        )
        if primary is not None and not isinstance(primary, DiagnosticRecord):
            raise TypeError(
                "select_primary_record must return DiagnosticRecord or None"
            )

        request_warnings = _request_warnings(evidence)
        warnings = _merge_warnings(
            request_warnings,
            matched.warnings,
            limit=self.max_warnings,
        )
        parse_complete = _parse_complete(evidence, matched)
        status = _parser_status(
            evidence,
            matched,
            parse_complete=parse_complete,
        )
        if evidence.strict and not parse_complete:
            warnings = _merge_warnings(
                warnings,
                (
                    "strict diagnostic parsing requires complete and lossless "
                    "evidence",
                ),
                limit=self.max_warnings,
            )

        return _build_result(
            evidence=evidence,
            status=status,
            records=records,
            warnings=warnings,
            primary=primary,
            parse_complete=parse_complete,
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


def _preflight_result(
    evidence: DiagnosticEvidence,
    *,
    max_warnings: int,
) -> DiagnosticParseResult | None:
    stdout_missing = evidence.stdout_text is None
    stderr_missing = evidence.stderr_text is None

    if not stdout_missing or not stderr_missing:
        return None

    if evidence.execution_state is ExecutionState.LAUNCH_FAILED:
        return _build_result(
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

    return _build_result(
        evidence=evidence,
        status=ValidationStatus.ERROR,
        records=(),
        warnings=_merge_warnings(
            (
                "raw stdout and stderr text are unavailable for diagnostic "
                "parsing",
            ),
            _request_warnings(evidence),
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
    provided = provider(evidence) if patterns is None else patterns
    if isinstance(provided, (str, bytes)):
        raise TypeError("patterns must be a sequence of DiagnosticPattern")

    resolved = tuple(provided)
    identifiers: set[str] = set()
    for index, pattern in enumerate(resolved):
        if not isinstance(pattern, DiagnosticPattern):
            raise TypeError(
                f"patterns[{index}] must be DiagnosticPattern"
            )
        if pattern.pattern_id in identifiers:
            raise ValueError(
                f"duplicate diagnostic pattern ID: {pattern.pattern_id}"
            )
        identifiers.add(pattern.pattern_id)

    return tuple(
        sorted(
            resolved,
            key=lambda pattern: (
                pattern.precedence,
                pattern.pattern_id,
            ),
        )
    )


def _record_tuple(
    records: Iterable[DiagnosticRecord],
) -> tuple[DiagnosticRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise TypeError("records must be an iterable of DiagnosticRecord")
    frozen = tuple(records)
    for index, record in enumerate(frozen):
        if not isinstance(record, DiagnosticRecord):
            raise TypeError(
                f"records[{index}] must be DiagnosticRecord"
            )
    return frozen


def _request_warnings(
    evidence: DiagnosticEvidence,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if evidence.stdout_truncated:
        warnings.append("stdout evidence is truncated")
    if evidence.stderr_truncated:
        warnings.append("stderr evidence is truncated")
    if evidence.decoding_lossy:
        warnings.append("stream decoding was lossy")
    return tuple(warnings)


def _parse_complete(
    evidence: DiagnosticEvidence,
    matched: DiagnosticMatchResult,
) -> bool:
    return not any(
        (
            evidence.stdout_truncated,
            evidence.stderr_truncated,
            evidence.decoding_lossy,
            matched.limits_reached,
            not matched.parse_complete,
        )
    )


def _parser_status(
    evidence: DiagnosticEvidence,
    matched: DiagnosticMatchResult,
    *,
    parse_complete: bool,
) -> ValidationStatus:
    if matched.contract_error:
        return ValidationStatus.ERROR
    if evidence.strict and not parse_complete:
        return ValidationStatus.ERROR
    return ValidationStatus.OK


def _build_result(
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
    if not isinstance(status, ValidationStatus):
        raise TypeError("status must be ValidationStatus")
    if status is ValidationStatus.FAIL:
        raise ValueError("the diagnostic parser must not return FAIL")
    if type(parse_complete) is not bool:
        raise TypeError("parse_complete must be a bool")
    if type(limits_reached) is not bool:
        raise TypeError("limits_reached must be a bool")

    for name, value in (
        ("patterns_considered", patterns_considered),
        ("patterns_matched", patterns_matched),
        ("unknown_lines", unknown_lines),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    primary_record_id: str | None
    primary_error_kind: ErrorKind | None
    primary_message: str
    primary_detail: str

    if primary is None:
        primary_record_id = None
        primary_error_kind = (
            ErrorKind.OK if status is ValidationStatus.OK else None
        )
        primary_message = ""
        primary_detail = ""
    else:
        primary_record_id = primary.record_id
        primary_error_kind = primary.error_kind
        primary_message = primary.message
        primary_detail = primary.detail

    return DiagnosticParseResult(
        status=status,
        parser_version=PARSER_VERSION,
        gf_version=evidence.gf_version,
        operation_kind=evidence.operation_kind,
        records=records,
        warnings=warnings,
        primary_record_id=primary_record_id,
        primary_error_kind=primary_error_kind,
        primary_message=primary_message,
        primary_detail=primary_detail,
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


def _parser_failure_result(
    evidence: DiagnosticEvidence,
    exc: Exception,
    *,
    max_warnings: int,
) -> DiagnosticParseResult:
    warning = f"diagnostic parser failed: {type(exc).__name__}"
    return _build_result(
        evidence=evidence,
        status=ValidationStatus.ERROR,
        records=(),
        warnings=_merge_warnings(
            _request_warnings(evidence),
            (warning,),
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
        if isinstance(group, (str, bytes)):
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
