"""Canonical PGF-specific diagnostic pattern recognition."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final

GENERATE_PMCFG_PATTERN_ID: Final[str] = "DP-GFINT-001"
GENERATE_PMCFG_ANCHOR: Final[str] = "Internal error in GeneratePMCFG"
MISSING_INFLECTION_RULE_ANCHOR: Final[str] = "Cannot find an inflection rule"
PATTERN_CATALOG_VERSION: Final[str] = "1.1"

_MAX_STREAM_CHARS: Final[int] = 16 * 1024 * 1024
_MAX_EXCERPT_CHARS: Final[int] = 16_384
_MAX_METADATA_ITEMS: Final[int] = 256
_DEFAULT_CONTEXT_LINES: Final[int] = 3
_MAX_CONTEXT_LINES: Final[int] = 50

_LINE_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"\r\n|\n|\r")
_ALLOWED_OPERATION_VALUES: Final[frozenset[str]] = frozenset(
    {
        "compile",
        "compilation",
        "pgf",
        "pgf_build",
        "pgf-build",
        "pgf_construction",
        "pgf-construction",
        "scenario",
        "scenario_load",
        "scenario-load",
        "scenario_runtime",
        "scenario-runtime",
        "generation",
    }
)
_OPERATION_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "compilation": "compile",
        "pgf": "pgf_build",
        "pgf-build": "pgf_build",
        "pgf_construction": "pgf_build",
        "pgf-construction": "pgf_build",
        "scenario-load": "scenario_load",
        "scenario-runtime": "scenario_runtime",
    }
)
_STREAM_ORDER: Final[Mapping[str, int]] = MappingProxyType(
    {"stderr": 0, "stdout": 1}
)


@unique
class PGFDiagnosticStream(StrEnum):
    STDERR = "stderr"
    STDOUT = "stdout"


@unique
class PGFPatternConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"


@unique
class PGFDiagnosticSeverity(StrEnum):
    FATAL = "fatal"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PGFDiagnosticInput:
    operation_kind: str
    stdout: str = ""
    stderr: str = ""
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        operation_kind = _normalize_operation(self.operation_kind)
        stdout = _stream_text(self.stdout, field_name="stdout")
        stderr = _stream_text(self.stderr, field_name="stderr")
        stdout_path = _optional_path(self.stdout_path, field_name="stdout_path")
        stderr_path = _optional_path(self.stderr_path, field_name="stderr_path")
        metadata = _freeze_metadata(self.metadata)
        object.__setattr__(self, "operation_kind", operation_kind)
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True, slots=True)
class PGFPatternMatch:
    pattern_id: str
    pattern_version: str
    operation_kind: str
    stream: PGFDiagnosticStream
    start_line: int
    end_line: int
    error_kind: str
    severity: PGFDiagnosticSeverity
    confidence: PGFPatternConfidence
    message: str
    detail: str
    raw_excerpt: str
    raw_artifact_path: Path | None
    normalized_signature: str
    is_fatal: bool
    is_warning: bool
    is_unknown: bool
    references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required_text(self.pattern_id, field_name="pattern_id", max_length=128)
        _required_text(
            self.pattern_version,
            field_name="pattern_version",
            max_length=64,
        )
        object.__setattr__(
            self,
            "operation_kind",
            _normalize_operation(self.operation_kind),
        )
        if not isinstance(self.stream, PGFDiagnosticStream):
            raise TypeError("stream must be PGFDiagnosticStream")
        _positive_int(self.start_line, field_name="start_line")
        _positive_int(self.end_line, field_name="end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        _required_text(self.error_kind, field_name="error_kind", max_length=64)
        if not isinstance(self.severity, PGFDiagnosticSeverity):
            raise TypeError("severity must be PGFDiagnosticSeverity")
        if not isinstance(self.confidence, PGFPatternConfidence):
            raise TypeError("confidence must be PGFPatternConfidence")
        _required_text(self.message, field_name="message", max_length=4096)
        _text(self.detail, field_name="detail", max_length=4096)
        _required_text(
            self.raw_excerpt,
            field_name="raw_excerpt",
            max_length=_MAX_EXCERPT_CHARS,
        )
        object.__setattr__(
            self,
            "raw_artifact_path",
            _optional_path(
                self.raw_artifact_path,
                field_name="raw_artifact_path",
            ),
        )
        _required_text(
            self.normalized_signature,
            field_name="normalized_signature",
            max_length=8192,
        )
        for name in ("is_fatal", "is_warning", "is_unknown"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")
        references = _text_tuple(self.references, field_name="references")
        object.__setattr__(self, "references", references)


@dataclass(frozen=True, slots=True)
class PGFObservedEvidence:
    operation_kind: str
    stream: PGFDiagnosticStream
    start_line: int
    end_line: int
    anchor: str
    message: str
    raw_excerpt: str
    raw_artifact_path: Path | None
    confidence: PGFPatternConfidence
    canonical_pattern_id: str | None = None
    references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation_kind",
            _normalize_operation(self.operation_kind),
        )
        if not isinstance(self.stream, PGFDiagnosticStream):
            raise TypeError("stream must be PGFDiagnosticStream")
        _positive_int(self.start_line, field_name="start_line")
        _positive_int(self.end_line, field_name="end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        _required_text(self.anchor, field_name="anchor", max_length=512)
        _required_text(self.message, field_name="message", max_length=4096)
        _required_text(
            self.raw_excerpt,
            field_name="raw_excerpt",
            max_length=_MAX_EXCERPT_CHARS,
        )
        object.__setattr__(
            self,
            "raw_artifact_path",
            _optional_path(
                self.raw_artifact_path,
                field_name="raw_artifact_path",
            ),
        )
        if not isinstance(self.confidence, PGFPatternConfidence):
            raise TypeError("confidence must be PGFPatternConfidence")
        if self.canonical_pattern_id is not None:
            _required_text(
                self.canonical_pattern_id,
                field_name="canonical_pattern_id",
                max_length=128,
            )
        object.__setattr__(
            self,
            "references",
            _text_tuple(self.references, field_name="references"),
        )


@dataclass(frozen=True, slots=True)
class PGFPatternResult:
    matches: tuple[PGFPatternMatch, ...]
    observations: tuple[PGFObservedEvidence, ...]

    def __post_init__(self) -> None:
        if any(not isinstance(item, PGFPatternMatch) for item in self.matches):
            raise TypeError("matches must contain PGFPatternMatch values")
        if any(
            not isinstance(item, PGFObservedEvidence)
            for item in self.observations
        ):
            raise TypeError(
                "observations must contain PGFObservedEvidence values"
            )
        if tuple(sorted(self.matches, key=_match_sort_key)) != self.matches:
            raise ValueError("matches must use canonical deterministic order")
        if tuple(
            sorted(self.observations, key=_observation_sort_key)
        ) != self.observations:
            raise ValueError(
                "observations must use canonical deterministic order"
            )

    @property
    def primary(self) -> PGFPatternMatch | None:
        return self.matches[0] if self.matches else None

    @property
    def secondary(self) -> tuple[PGFPatternMatch, ...]:
        return self.matches[1:]


def match_pgf_patterns(
    evidence: PGFDiagnosticInput,
    *,
    context_lines: int = _DEFAULT_CONTEXT_LINES,
) -> PGFPatternResult:
    if not isinstance(evidence, PGFDiagnosticInput):
        raise TypeError("evidence must be PGFDiagnosticInput")
    context_lines = _context_line_count(context_lines)
    matches = match_generate_pmcfg_internal_error(
        evidence,
        context_lines=context_lines,
    )
    observations = find_missing_inflection_rule_evidence(
        evidence,
        context_lines=context_lines,
        canonical_matches=matches,
    )
    return PGFPatternResult(matches=matches, observations=observations)


def match_generate_pmcfg_internal_error(
    evidence: PGFDiagnosticInput,
    *,
    context_lines: int = _DEFAULT_CONTEXT_LINES,
) -> tuple[PGFPatternMatch, ...]:
    if not isinstance(evidence, PGFDiagnosticInput):
        raise TypeError("evidence must be PGFDiagnosticInput")
    context_lines = _context_line_count(context_lines)
    matches: list[PGFPatternMatch] = []
    for stream, stream_text, artifact_path in _streams(evidence):
        stream_lines = _split_lines(stream_text)
        for index, line in enumerate(stream_lines):
            if GENERATE_PMCFG_ANCHOR not in line:
                continue
            excerpt, excerpt_start, excerpt_end = _bounded_excerpt(
                stream_lines,
                match_index=index,
                context_lines=context_lines,
            )
            message = line.strip() or GENERATE_PMCFG_ANCHOR
            matches.append(
                PGFPatternMatch(
                    pattern_id=GENERATE_PMCFG_PATTERN_ID,
                    pattern_version=PATTERN_CATALOG_VERSION,
                    operation_kind=evidence.operation_kind,
                    stream=stream,
                    start_line=index + 1,
                    end_line=index + 1,
                    error_kind="INTERNAL",
                    severity=PGFDiagnosticSeverity.FATAL,
                    confidence=PGFPatternConfidence.HIGH,
                    message=message,
                    detail="GeneratePMCFG",
                    raw_excerpt=excerpt,
                    raw_artifact_path=artifact_path,
                    normalized_signature=_generate_pmcfg_signature(message),
                    is_fatal=True,
                    is_warning=False,
                    is_unknown=False,
                    references=(
                        _reference(stream, index + 1, index + 1),
                        _reference(stream, excerpt_start, excerpt_end),
                    ),
                )
            )
    return tuple(sorted(matches, key=_match_sort_key))


def find_missing_inflection_rule_evidence(
    evidence: PGFDiagnosticInput,
    *,
    context_lines: int = _DEFAULT_CONTEXT_LINES,
    canonical_matches: Iterable[PGFPatternMatch] = (),
) -> tuple[PGFObservedEvidence, ...]:
    if not isinstance(evidence, PGFDiagnosticInput):
        raise TypeError("evidence must be PGFDiagnosticInput")
    context_lines = _context_line_count(context_lines)
    matches = tuple(canonical_matches)
    if any(not isinstance(item, PGFPatternMatch) for item in matches):
        raise TypeError(
            "canonical_matches must contain PGFPatternMatch values"
        )
    observations: list[PGFObservedEvidence] = []
    for stream, stream_text, artifact_path in _streams(evidence):
        stream_lines = _split_lines(stream_text)
        for index, line in enumerate(stream_lines):
            if MISSING_INFLECTION_RULE_ANCHOR not in line:
                continue
            excerpt, excerpt_start, excerpt_end = _bounded_excerpt(
                stream_lines,
                match_index=index,
                context_lines=context_lines,
            )
            associated = any(
                item.pattern_id == GENERATE_PMCFG_PATTERN_ID
                and item.stream is stream
                and excerpt_start <= item.start_line <= excerpt_end
                for item in matches
            )
            observations.append(
                PGFObservedEvidence(
                    operation_kind=evidence.operation_kind,
                    stream=stream,
                    start_line=index + 1,
                    end_line=index + 1,
                    anchor=MISSING_INFLECTION_RULE_ANCHOR,
                    message=line.strip() or MISSING_INFLECTION_RULE_ANCHOR,
                    raw_excerpt=excerpt,
                    raw_artifact_path=artifact_path,
                    confidence=PGFPatternConfidence.MEDIUM,
                    canonical_pattern_id=(
                        GENERATE_PMCFG_PATTERN_ID if associated else None
                    ),
                    references=(
                        _reference(stream, index + 1, index + 1),
                        _reference(stream, excerpt_start, excerpt_end),
                    ),
                )
            )
    return tuple(sorted(observations, key=_observation_sort_key))


def supports_pgf_operation(operation_kind: str) -> bool:
    try:
        _normalize_operation(operation_kind)
    except (TypeError, ValueError):
        return False
    return True


def _streams(
    evidence: PGFDiagnosticInput,
) -> tuple[tuple[PGFDiagnosticStream, str, Path | None], ...]:
    return (
        (
            PGFDiagnosticStream.STDERR,
            evidence.stderr,
            evidence.stderr_path,
        ),
        (
            PGFDiagnosticStream.STDOUT,
            evidence.stdout,
            evidence.stdout_path,
        ),
    )


def _split_lines(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(_LINE_SPLIT_RE.split(value))


def _bounded_excerpt(
    lines: tuple[str, ...],
    *,
    match_index: int,
    context_lines: int,
) -> tuple[str, int, int]:
    start_index = max(0, match_index - context_lines)
    end_index = min(len(lines), match_index + context_lines + 1)
    selected = lines[start_index:end_index]
    excerpt = "\n".join(selected)
    if len(excerpt) > _MAX_EXCERPT_CHARS:
        excerpt = excerpt[: _MAX_EXCERPT_CHARS - 1] + "…"
    return excerpt, start_index + 1, end_index


def _generate_pmcfg_signature(message: str) -> str:
    prefix, separator, suffix = message.partition(GENERATE_PMCFG_ANCHOR)
    if not separator:
        return GENERATE_PMCFG_ANCHOR
    stable_prefix = prefix.strip()
    stable_suffix = suffix.strip()
    parts = [GENERATE_PMCFG_ANCHOR]
    if stable_prefix and not _looks_like_unstable_prefix(stable_prefix):
        parts.insert(0, stable_prefix)
    if stable_suffix:
        parts.append(stable_suffix)
    return " | ".join(parts)


def _looks_like_unstable_prefix(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return (
        ":/" in normalized
        or normalized.startswith("/")
        or normalized.startswith("./")
        or normalized.startswith("../")
    )


def _match_sort_key(item: PGFPatternMatch) -> tuple[int, int, str, str]:
    return (
        _STREAM_ORDER[item.stream.value],
        item.start_line,
        item.pattern_id,
        item.message,
    )


def _observation_sort_key(
    item: PGFObservedEvidence,
) -> tuple[int, int, str, str]:
    return (
        _STREAM_ORDER[item.stream.value],
        item.start_line,
        item.anchor,
        item.message,
    )


def _reference(
    stream: PGFDiagnosticStream,
    start_line: int,
    end_line: int,
) -> str:
    if start_line == end_line:
        return f"{stream.value}:{start_line}"
    return f"{stream.value}:{start_line}-{end_line}"


def _normalize_operation(value: object) -> str:
    text = _required_text(
        value,
        field_name="operation_kind",
        max_length=128,
    )
    normalized = text.strip().lower().replace(" ", "_")
    if normalized not in _ALLOWED_OPERATION_VALUES:
        raise ValueError(f"unsupported PGF diagnostic operation: {text!r}")
    return _OPERATION_ALIASES.get(normalized, normalized)


def _stream_text(value: object, *, field_name: str) -> str:
    text = _text(value, field_name=field_name, max_length=_MAX_STREAM_CHARS)
    return text[1:] if text.startswith("\ufeff") else text


def _freeze_metadata(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    if len(value) > _MAX_METADATA_ITEMS:
        raise ValueError("metadata exceeds the supported item limit")
    copied: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _required_text(
            key,
            field_name="metadata key",
            max_length=256,
        )
        copied[normalized_key] = _text(
            item,
            field_name=f"metadata[{normalized_key!r}]",
            max_length=8192,
        )
    return MappingProxyType(copied)


def _context_line_count(value: object) -> int:
    if type(value) is not int:
        raise TypeError("context_lines must be an integer")
    if not 0 <= value <= _MAX_CONTEXT_LINES:
        raise ValueError(
            f"context_lines must be between 0 and {_MAX_CONTEXT_LINES}"
        )
    return value


def _optional_path(value: object, *, field_name: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path or None")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _text_tuple(
    values: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(values)
    for item in result:
        _required_text(
            item,
            field_name=f"{field_name} item",
            max_length=2048,
        )
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _positive_int(value: object, *, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")
    return value


def _required_text(
    value: object,
    *,
    field_name: str,
    max_length: int,
) -> str:
    text = _text(value, field_name=field_name, max_length=max_length)
    if not text.strip():
        raise ValueError(f"{field_name} must not be empty")
    return text


def _text(
    value: object,
    *,
    field_name: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length limit")
    return value


__all__ = (
    "GENERATE_PMCFG_ANCHOR",
    "GENERATE_PMCFG_PATTERN_ID",
    "MISSING_INFLECTION_RULE_ANCHOR",
    "PATTERN_CATALOG_VERSION",
    "PGFDiagnosticInput",
    "PGFDiagnosticSeverity",
    "PGFDiagnosticStream",
    "PGFObservedEvidence",
    "PGFPatternConfidence",
    "PGFPatternMatch",
    "PGFPatternResult",
    "find_missing_inflection_rule_evidence",
    "match_generate_pmcfg_internal_error",
    "match_pgf_patterns",
    "supports_pgf_operation",
)
