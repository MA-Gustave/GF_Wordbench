from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, TypeAlias

from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

_MAX_IDENTIFIER: Final[int] = 256
_MAX_MESSAGE: Final[int] = 8_192
_MAX_DETAIL: Final[int] = 32_768
_MAX_EXCERPT: Final[int] = 65_536
_MAX_ITEMS: Final[int] = 100_000
_PATTERN_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:DP|GF-DIAG)-[A-Z0-9]+(?:-[A-Z0-9]+)+$"
)
_RECORD_ID_RE: Final[re.Pattern[str]] = re.compile(r"^diag-[0-9a-f]{16}$")

MetadataValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | Path
    | tuple["MetadataValue", ...]
    | Mapping[str, "MetadataValue"]
)
Metadata: TypeAlias = Mapping[str, MetadataValue]
PatternMatcher: TypeAlias = Callable[
    ["DiagnosticEvidence"],
    "PatternMatch | Iterable[PatternMatch] | None",
]


@unique
class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"
    UNKNOWN = "unknown"


@unique
class PatternConfidence(StrEnum):
    AUTHORITATIVE = "authoritative"
    EXACT = "exact"
    HIGH = "high"
    STRONG = "strong"
    MEDIUM = "medium"
    FALLBACK = "fallback"
    LOW = "low"
    UNKNOWN = "unknown"


@unique
class PatternLifecycle(StrEnum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@unique
class DiagnosticStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    PROCESS_STATE = "process-state"
    FILESYSTEM = "filesystem"
    FRAMEWORK_STATE = "framework-state"


@unique
class StreamScope(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    EITHER = "either"
    BOTH_STRUCTURE = "both-structure"
    PROCESS_STATE = "process-state"
    FILESYSTEM = "filesystem"
    FRAMEWORK_STATE = "framework-state"


@unique
class LineClassification(StrEnum):
    DIAGNOSTIC_START = "diagnostic_start"
    DIAGNOSTIC_CONTINUATION = "diagnostic_continuation"
    CONTEXT = "context"
    KNOWN_NOISE = "known_noise"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ArtifactObservation:
    path: Path
    role: str
    required: bool
    exists: bool
    kind_matches: bool
    size_bytes: int | None
    current: bool | None = None
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _coerce_path(self.path, "path"))
        object.__setattr__(self, "role", _text(self.role, "role", _MAX_IDENTIFIER))
        _bool(self.required, "required")
        _bool(self.exists, "exists")
        _bool(self.kind_matches, "kind_matches")
        _optional_bool(self.current, "current")
        if self.size_bytes is not None:
            _nonnegative_int(self.size_bytes, "size_bytes")
        if not self.exists and self.size_bytes not in (None, 0):
            raise ValueError("a missing artifact cannot have positive size")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class DiagnosticLocation:
    source_path: Path | None = None
    source_module: str | None = None
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    symbol: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_path",
            _optional_path(self.source_path, "source_path"),
        )
        object.__setattr__(
            self,
            "source_module",
            _optional_text(self.source_module, "source_module", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "symbol",
            _optional_text(self.symbol, "symbol", _MAX_IDENTIFIER),
        )
        for name in ("line", "column", "end_line", "end_column"):
            _optional_positive_int(getattr(self, name), name)
        if self.end_line is not None and self.line is None:
            raise ValueError("end_line requires line")
        if self.end_column is not None and self.column is None:
            raise ValueError("end_column requires column")
        if self.line is not None and self.end_line is not None:
            if self.end_line < self.line:
                raise ValueError("end_line must not precede line")
        if (
            self.line is not None
            and self.end_line == self.line
            and self.column is not None
            and self.end_column is not None
            and self.end_column < self.column
        ):
            raise ValueError("end_column must not precede column")

    @property
    def file_path(self) -> Path | None:
        return self.source_path

    @property
    def module_name(self) -> str | None:
        return self.source_module


@dataclass(frozen=True, slots=True)
class DiagnosticLine:
    stream: DiagnosticStream
    line_number: int
    text: str
    classification: LineClassification = LineClassification.UNKNOWN
    raw_path: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "stream", _stream(self.stream, "stream"))
        _positive_int(self.line_number, "line_number")
        object.__setattr__(self, "text", _plain_text(self.text, "text", _MAX_EXCERPT))
        object.__setattr__(
            self,
            "classification",
            _enum(self.classification, LineClassification, "classification"),
        )
        object.__setattr__(self, "raw_path", _optional_path(self.raw_path, "raw_path"))


@dataclass(frozen=True, slots=True)
class DiagnosticStreamEvidence:
    stream: DiagnosticStream
    raw_path: Path
    text: str
    truncated: bool = False
    decoding_lossy: bool = False
    encoding: str = "utf-8"
    lines: tuple[DiagnosticLine, ...] = ()

    def __post_init__(self) -> None:
        stream = _stream(self.stream, "stream")
        if stream not in (DiagnosticStream.STDOUT, DiagnosticStream.STDERR):
            raise ValueError("stream evidence must be stdout or stderr")
        object.__setattr__(self, "stream", stream)
        object.__setattr__(self, "raw_path", _coerce_path(self.raw_path, "raw_path"))
        object.__setattr__(self, "text", _plain_text(self.text, "text", _MAX_EXCERPT * 128))
        _bool(self.truncated, "truncated")
        _bool(self.decoding_lossy, "decoding_lossy")
        object.__setattr__(self, "encoding", _text(self.encoding, "encoding", 128))
        lines = _typed_tuple(self.lines, DiagnosticLine, "lines")
        if any(line.stream is not stream for line in lines):
            raise ValueError("all diagnostic lines must match the stream")
        object.__setattr__(self, "lines", lines)

    @property
    def source_stream(self) -> DiagnosticStream:
        return self.stream


@dataclass(frozen=True, slots=True)
class DiagnosticEvidence:
    operation_kind: str
    execution_state: ExecutionState | str | None
    exit_code: int | None
    stdout_path: Path
    stderr_path: Path
    artifact_observations: tuple[ArtifactObservation, ...] = ()
    metadata: Metadata = field(default_factory=dict)
    gf_version: str | None = None
    platform: str | None = None
    stdout_text: str | None = None
    stderr_text: str | None = None
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    decoding_lossy: bool = False
    capture_complete: bool = True
    stream: DiagnosticStream | str | None = None
    raw_path: Path | None = None
    text: str | None = None
    framework_facts: Metadata = field(default_factory=dict)
    scenario_facts: Metadata = field(default_factory=dict)
    contract_facts: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation_kind",
            _text(self.operation_kind, "operation_kind", _MAX_IDENTIFIER),
        )
        if self.execution_state is not None:
            object.__setattr__(
                self,
                "execution_state",
                _enum_or_string(self.execution_state, ExecutionState, "execution_state"),
            )
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise TypeError("exit_code must be int or None")
        object.__setattr__(self, "stdout_path", _coerce_path(self.stdout_path, "stdout_path"))
        object.__setattr__(self, "stderr_path", _coerce_path(self.stderr_path, "stderr_path"))
        object.__setattr__(
            self,
            "artifact_observations",
            _typed_tuple(
                self.artifact_observations,
                ArtifactObservation,
                "artifact_observations",
            ),
        )
        for name in ("metadata", "framework_facts", "scenario_facts", "contract_facts"):
            object.__setattr__(self, name, _freeze_metadata(getattr(self, name)))
        object.__setattr__(
            self,
            "gf_version",
            _optional_text(self.gf_version, "gf_version", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "platform",
            _optional_text(self.platform, "platform", _MAX_IDENTIFIER),
        )
        for name in ("stdout_text", "stderr_text", "text"):
            object.__setattr__(
                self,
                name,
                _optional_plain_text(getattr(self, name), name, _MAX_EXCERPT * 128),
            )
        for name in (
            "stdout_truncated",
            "stderr_truncated",
            "decoding_lossy",
            "capture_complete",
        ):
            _bool(getattr(self, name), name)
        if self.stream is not None:
            object.__setattr__(self, "stream", _stream(self.stream, "stream"))
        object.__setattr__(self, "raw_path", _optional_path(self.raw_path, "raw_path"))
        if self.stream is not None and self.stream in (
            DiagnosticStream.STDOUT,
            DiagnosticStream.STDERR,
        ):
            expected = self.stdout_path if self.stream is DiagnosticStream.STDOUT else self.stderr_path
            if self.raw_path is not None and self.raw_path != expected:
                raise ValueError("raw_path must match the selected stream path")

    @property
    def operation(self) -> str:
        return self.operation_kind

    @property
    def tool_version(self) -> str | None:
        return self.gf_version

    @property
    def platform_id(self) -> str | None:
        return self.platform

    @property
    def source_stream(self) -> DiagnosticStream | None:
        return self.stream

    def for_stream(
        self,
        stream: DiagnosticStream | str,
        *,
        text: str | None = None,
    ) -> DiagnosticEvidence:
        selected = _stream(stream, "stream")
        if selected not in (DiagnosticStream.STDOUT, DiagnosticStream.STDERR):
            raise ValueError("selected stream must be stdout or stderr")
        selected_text = text
        if selected_text is None:
            selected_text = self.stdout_text if selected is DiagnosticStream.STDOUT else self.stderr_text
        return DiagnosticEvidence(
            operation_kind=self.operation_kind,
            execution_state=self.execution_state,
            exit_code=self.exit_code,
            stdout_path=self.stdout_path,
            stderr_path=self.stderr_path,
            artifact_observations=self.artifact_observations,
            metadata=self.metadata,
            gf_version=self.gf_version,
            platform=self.platform,
            stdout_text=self.stdout_text,
            stderr_text=self.stderr_text,
            stdout_truncated=self.stdout_truncated,
            stderr_truncated=self.stderr_truncated,
            decoding_lossy=self.decoding_lossy,
            capture_complete=self.capture_complete,
            stream=selected,
            raw_path=self.stdout_path if selected is DiagnosticStream.STDOUT else self.stderr_path,
            text=selected_text,
            framework_facts=self.framework_facts,
            scenario_facts=self.scenario_facts,
            contract_facts=self.contract_facts,
        )


@dataclass(frozen=True, slots=True)
class PatternMatch:
    pattern_id: str
    operation: str
    stream: DiagnosticStream | str | None
    start_line: int | None
    end_line: int | None
    severity: DiagnosticSeverity | str
    error_kind: ErrorKind | str
    message: str
    detail: str = ""
    source_path: Path | None = None
    source_module: str | None = None
    line: int | None = None
    column: int | None = None
    end_line_number: int | None = None
    end_column: int | None = None
    symbol: str | None = None
    pattern_version: str = "1.0"
    confidence: PatternConfidence | str = PatternConfidence.UNKNOWN
    raw_excerpt: str = ""
    normalized_signature: str = ""
    continuation_lines: tuple[str, ...] = ()
    is_fatal: bool = False
    is_warning: bool = False
    is_unknown: bool = False
    references: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_id", _pattern_id(self.pattern_id))
        object.__setattr__(self, "operation", _text(self.operation, "operation", _MAX_IDENTIFIER))
        if self.stream is not None:
            object.__setattr__(self, "stream", _stream(self.stream, "stream"))
        _optional_positive_int(self.start_line, "start_line")
        _optional_positive_int(self.end_line, "end_line")
        if self.end_line is not None and self.start_line is None:
            raise ValueError("end_line requires start_line")
        if self.start_line is not None and self.end_line is not None:
            if self.end_line < self.start_line:
                raise ValueError("end_line must not precede start_line")
        object.__setattr__(
            self,
            "severity",
            _enum(self.severity, DiagnosticSeverity, "severity"),
        )
        object.__setattr__(
            self,
            "error_kind",
            _enum_or_string(self.error_kind, ErrorKind, "error_kind"),
        )
        object.__setattr__(self, "message", _text(self.message, "message", _MAX_MESSAGE))
        object.__setattr__(self, "detail", _plain_text(self.detail, "detail", _MAX_DETAIL))
        object.__setattr__(self, "source_path", _optional_path(self.source_path, "source_path"))
        object.__setattr__(
            self,
            "source_module",
            _optional_text(self.source_module, "source_module", _MAX_IDENTIFIER),
        )
        for name in ("line", "column", "end_line_number", "end_column"):
            _optional_positive_int(getattr(self, name), name)
        object.__setattr__(self, "symbol", _optional_text(self.symbol, "symbol", _MAX_IDENTIFIER))
        object.__setattr__(
            self,
            "pattern_version",
            _text(self.pattern_version, "pattern_version", 64),
        )
        object.__setattr__(
            self,
            "confidence",
            _enum(self.confidence, PatternConfidence, "confidence"),
        )
        object.__setattr__(
            self,
            "raw_excerpt",
            _plain_text(self.raw_excerpt, "raw_excerpt", _MAX_EXCERPT),
        )
        signature_value = self.normalized_signature.strip()
        if not signature_value:
            signature_value = normalized_diagnostic_signature(
                self.error_kind,
                self.message,
            )
        object.__setattr__(
            self,
            "normalized_signature",
            _text(signature_value, "normalized_signature", _MAX_MESSAGE),
        )
        object.__setattr__(
            self,
            "continuation_lines",
            _plain_text_tuple(self.continuation_lines, "continuation_lines", _MAX_EXCERPT),
        )
        for name in ("is_fatal", "is_warning", "is_unknown"):
            _bool(getattr(self, name), name)
        if self.severity is DiagnosticSeverity.FATAL and not self.is_fatal:
            object.__setattr__(self, "is_fatal", True)
        if self.severity is DiagnosticSeverity.WARNING and not self.is_warning:
            object.__setattr__(self, "is_warning", True)
        if self.confidence is PatternConfidence.UNKNOWN and not self.is_unknown:
            object.__setattr__(self, "is_unknown", True)
        object.__setattr__(self, "references", _text_tuple(self.references, "references", _MAX_MESSAGE))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def operation_kind(self) -> str:
        return self.operation

    @property
    def source_stream(self) -> DiagnosticStream | None:
        return self.stream

    @property
    def file_path(self) -> Path | None:
        return self.source_path

    @property
    def module_name(self) -> str | None:
        return self.source_module

    @property
    def signature(self) -> str:
        return self.normalized_signature

    @property
    def location(self) -> DiagnosticLocation:
        return DiagnosticLocation(
            source_path=self.source_path,
            source_module=self.source_module,
            line=self.line,
            column=self.column,
            end_line=self.end_line_number,
            end_column=self.end_column,
            symbol=self.symbol,
        )


@dataclass(frozen=True, slots=True)
class DiagnosticRecord:
    record_id: str
    operation: str
    stream: DiagnosticStream | str | None
    start_line: int | None
    end_line: int | None
    severity: DiagnosticSeverity | str
    error_kind: ErrorKind | str
    message: str
    detail: str
    source_path: Path | None
    source_module: str | None
    line: int | None
    column: int | None
    end_line_number: int | None
    end_column: int | None
    symbol: str | None
    pattern_id: str
    pattern_version: str
    confidence: PatternConfidence | str
    raw_excerpt: str
    normalized_signature: str
    continuation_lines: tuple[str, ...]
    is_fatal: bool
    is_warning: bool
    is_unknown: bool
    references: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or _RECORD_ID_RE.fullmatch(self.record_id) is None:
            raise ValueError("record_id must use canonical diag-<16 hex> form")
        match = PatternMatch(
            pattern_id=self.pattern_id,
            operation=self.operation,
            stream=self.stream,
            start_line=self.start_line,
            end_line=self.end_line,
            severity=self.severity,
            error_kind=self.error_kind,
            message=self.message,
            detail=self.detail,
            source_path=self.source_path,
            source_module=self.source_module,
            line=self.line,
            column=self.column,
            end_line_number=self.end_line_number,
            end_column=self.end_column,
            symbol=self.symbol,
            pattern_version=self.pattern_version,
            confidence=self.confidence,
            raw_excerpt=self.raw_excerpt,
            normalized_signature=self.normalized_signature,
            continuation_lines=self.continuation_lines,
            is_fatal=self.is_fatal,
            is_warning=self.is_warning,
            is_unknown=self.is_unknown,
            references=self.references,
            metadata=self.metadata,
        )
        for name in (
            "operation",
            "stream",
            "severity",
            "error_kind",
            "message",
            "detail",
            "source_path",
            "source_module",
            "symbol",
            "pattern_id",
            "pattern_version",
            "confidence",
            "raw_excerpt",
            "normalized_signature",
            "continuation_lines",
            "is_fatal",
            "is_warning",
            "is_unknown",
            "references",
            "metadata",
        ):
            object.__setattr__(self, name, getattr(match, name))

    @classmethod
    def from_match(cls, match: PatternMatch) -> DiagnosticRecord:
        if not isinstance(match, PatternMatch):
            raise TypeError("match must be PatternMatch")
        record_id = build_record_id(
            stream=match.stream,
            start_line=match.start_line,
            end_line=match.end_line,
            pattern_id=match.pattern_id,
            normalized_signature=match.normalized_signature,
        )
        return cls(
            record_id=record_id,
            operation=match.operation,
            stream=match.stream,
            start_line=match.start_line,
            end_line=match.end_line,
            severity=match.severity,
            error_kind=match.error_kind,
            message=match.message,
            detail=match.detail,
            source_path=match.source_path,
            source_module=match.source_module,
            line=match.line,
            column=match.column,
            end_line_number=match.end_line_number,
            end_column=match.end_column,
            symbol=match.symbol,
            pattern_id=match.pattern_id,
            pattern_version=match.pattern_version,
            confidence=match.confidence,
            raw_excerpt=match.raw_excerpt,
            normalized_signature=match.normalized_signature,
            continuation_lines=match.continuation_lines,
            is_fatal=match.is_fatal,
            is_warning=match.is_warning,
            is_unknown=match.is_unknown,
            references=match.references,
            metadata=match.metadata,
        )

    @property
    def operation_kind(self) -> str:
        return self.operation

    @property
    def source_stream(self) -> DiagnosticStream | None:
        return self.stream

    @property
    def file_path(self) -> Path | None:
        return self.source_path

    @property
    def module_name(self) -> str | None:
        return self.source_module

    @property
    def location(self) -> DiagnosticLocation:
        return DiagnosticLocation(
            source_path=self.source_path,
            source_module=self.source_module,
            line=self.line,
            column=self.column,
            end_line=self.end_line_number,
            end_column=self.end_column,
            symbol=self.symbol,
        )


@dataclass(frozen=True, slots=True)
class DiagnosticMatchResult:
    """Immutable result returned by diagnostic stream matching."""

    records: tuple[DiagnosticRecord, ...] = ()
    warnings: tuple[str, ...] = ()
    patterns_considered: int = 0
    patterns_matched: int = 0
    unknown_lines: int = 0
    limits_reached: bool = False
    parse_complete: bool = True
    contract_error: bool = False

    def __post_init__(self) -> None:
        records = _typed_tuple(self.records, DiagnosticRecord, "records")
        warnings = _plain_text_tuple(
            self.warnings,
            "warnings",
            _MAX_MESSAGE,
        )
        for name in (
            "patterns_considered",
            "patterns_matched",
            "unknown_lines",
        ):
            _nonnegative_int(getattr(self, name), name)
        if self.patterns_matched > self.patterns_considered:
            raise ValueError(
                "patterns_matched must not exceed patterns_considered"
            )
        for name in (
            "limits_reached",
            "parse_complete",
            "contract_error",
        ):
            _bool(getattr(self, name), name)
        record_ids = tuple(record.record_id for record in records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("records contain duplicate record_id values")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Portable reference to evidence supporting one diagnostic finding."""

    role: str
    path: str
    stream: str | None = None
    line: int | None = None
    column: int | None = None
    excerpt: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "role",
            _text(self.role, "role", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "path",
            _text(self.path, "path", _MAX_DETAIL),
        )
        object.__setattr__(
            self,
            "stream",
            _optional_text(self.stream, "stream", _MAX_IDENTIFIER),
        )
        _optional_positive_int(self.line, "line")
        _optional_positive_int(self.column, "column")
        object.__setattr__(
            self,
            "excerpt",
            _optional_plain_text(self.excerpt, "excerpt", _MAX_EXCERPT),
        )


@dataclass(frozen=True, slots=True)
class Finding:
    """Immutable structured finding produced by diagnostics or static scanning."""

    finding_id: str
    severity: str
    diagnostic_class: DiagnosticClass | None
    error_kind: ErrorKind | None
    kind: str
    message: str
    target: str
    evidence_refs: tuple[EvidenceRef, ...]
    producer: ProducerInfo
    rule_id: str | None = None
    blocking: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "finding_id",
            _text(self.finding_id, "finding_id", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "severity",
            _text(self.severity, "severity", _MAX_IDENTIFIER),
        )
        if self.diagnostic_class is not None and not isinstance(
            self.diagnostic_class,
            DiagnosticClass,
        ):
            raise TypeError(
                "diagnostic_class must be DiagnosticClass or None"
            )
        if self.error_kind is not None and not isinstance(
            self.error_kind,
            ErrorKind,
        ):
            raise TypeError("error_kind must be ErrorKind or None")
        object.__setattr__(
            self,
            "kind",
            _text(self.kind, "kind", _MAX_IDENTIFIER),
        )
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message", _MAX_MESSAGE),
        )
        object.__setattr__(
            self,
            "target",
            _text(self.target, "target", _MAX_DETAIL),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _typed_tuple(self.evidence_refs, EvidenceRef, "evidence_refs"),
        )
        if not isinstance(self.producer, ProducerInfo):
            raise TypeError("producer must be ProducerInfo")
        object.__setattr__(
            self,
            "rule_id",
            _optional_text(self.rule_id, "rule_id", _MAX_IDENTIFIER),
        )
        _bool(self.blocking, "blocking")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        normalized_metadata: dict[str, str] = {}
        for key, value in self.metadata.items():
            canonical_key = _text(
                key,
                "metadata key",
                _MAX_IDENTIFIER,
            )
            canonical_value = _plain_text(
                value,
                f"metadata[{canonical_key!r}]",
                _MAX_DETAIL,
            )
            normalized_metadata[canonical_key] = canonical_value
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(
                    sorted(
                        normalized_metadata.items(),
                        key=lambda item: (
                            item[0].casefold(),
                            item[0],
                        ),
                    )
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class TopError:
    """Canonical top-error aggregation record.

    Validation and canonical ordering are owned by
    ``diagnostics.classification.top_errors`` so invalid candidate records can
    still be constructed and rejected explicitly by that service.
    """

    error_kind: ErrorKind
    message: str
    count: int
    subject_kinds: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DiagnosticPattern:
    pattern_id: str
    operations: frozenset[str]
    streams: frozenset[str]
    priority: int
    confidence: PatternConfidence | str
    error_kind: ErrorKind | str
    severity: DiagnosticSeverity | str
    matcher: PatternMatcher
    lifecycle_state: PatternLifecycle | str = PatternLifecycle.ACTIVE
    pattern_version: str = "1.0"
    supported_gf_versions: frozenset[str] = frozenset({"all"})
    supported_platforms: frozenset[str] = frozenset({"all"})
    fixtures: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_id", _pattern_id(self.pattern_id))
        object.__setattr__(self, "operations", _scope_set(self.operations, "operations"))
        object.__setattr__(self, "streams", _scope_set(self.streams, "streams"))
        _nonnegative_int(self.priority, "priority")
        object.__setattr__(
            self,
            "confidence",
            _enum(self.confidence, PatternConfidence, "confidence"),
        )
        object.__setattr__(
            self,
            "error_kind",
            _enum_or_string(self.error_kind, ErrorKind, "error_kind"),
        )
        object.__setattr__(
            self,
            "severity",
            _enum(self.severity, DiagnosticSeverity, "severity"),
        )
        if not callable(self.matcher):
            raise TypeError("matcher must be callable")
        object.__setattr__(
            self,
            "lifecycle_state",
            _enum(self.lifecycle_state, PatternLifecycle, "lifecycle_state"),
        )
        object.__setattr__(
            self,
            "pattern_version",
            _text(self.pattern_version, "pattern_version", 64),
        )
        object.__setattr__(
            self,
            "supported_gf_versions",
            _compatibility_scope(
                self.supported_gf_versions,
                "supported_gf_versions",
            ),
        )
        object.__setattr__(
            self,
            "supported_platforms",
            _compatibility_scope(
                self.supported_platforms,
                "supported_platforms",
            ),
        )
        object.__setattr__(self, "fixtures", _text_tuple(self.fixtures, "fixtures", _MAX_MESSAGE))
        object.__setattr__(self, "notes", _plain_text(self.notes, "notes", _MAX_DETAIL))

    @property
    def supported_operations(self) -> frozenset[str]:
        return self.operations

    @property
    def stream_scope(self) -> str:
        if len(self.streams) == 1:
            return next(iter(self.streams))
        if self.streams == frozenset({"stdout", "stderr"}):
            return StreamScope.EITHER.value
        return StreamScope.BOTH_STRUCTURE.value

    @property
    def precedence(self) -> int:
        return self.priority

    @property
    def lifecycle(self) -> PatternLifecycle:
        return self.lifecycle_state

    @property
    def gf_versions(self) -> frozenset[str]:
        return self.supported_gf_versions

    @property
    def platforms(self) -> frozenset[str]:
        return self.supported_platforms


@dataclass(frozen=True, slots=True)
class DiagnosticParseWarning:
    code: str
    message: str
    pattern_id: str | None = None
    stream: DiagnosticStream | str | None = None
    line: int | None = None
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _text(self.code, "code", _MAX_IDENTIFIER))
        object.__setattr__(self, "message", _text(self.message, "message", _MAX_MESSAGE))
        if self.pattern_id is not None:
            object.__setattr__(self, "pattern_id", _pattern_id(self.pattern_id))
        if self.stream is not None:
            object.__setattr__(self, "stream", _stream(self.stream, "stream"))
        _optional_positive_int(self.line, "line")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, init=False)
class DiagnosticParseResult:
    """Immutable public result of diagnostic parsing.

    ``operation_kind`` is canonical. The legacy ``operation`` keyword and
    property remain as a compatibility alias for existing callers.
    """

    parser_version: str
    status: ValidationStatus | str
    gf_version: str | None
    operation_kind: str
    records: tuple[DiagnosticRecord, ...]
    warnings: tuple[DiagnosticParseWarning | str, ...]
    primary_record_id: str | None
    primary_error_kind: ErrorKind | str | None
    primary_message: str
    primary_detail: str
    fatal_detected: bool
    unknown_failure_output: bool
    stdout_truncated: bool
    stderr_truncated: bool
    decoding_lossy: bool
    parse_complete: bool
    patterns_considered: int
    patterns_matched: int
    records_emitted: int
    unknown_lines: int
    limits_reached: bool
    metadata: Metadata

    def __init__(
        self,
        parser_version: str,
        status: ValidationStatus | str,
        gf_version: str | None,
        operation_kind: str | None = None,
        records: Iterable[DiagnosticRecord] = (),
        warnings: Iterable[DiagnosticParseWarning | str] = (),
        primary_record_id: str | None = None,
        primary_error_kind: ErrorKind | str | None = None,
        primary_message: str = "",
        primary_detail: str = "",
        fatal_detected: bool = False,
        unknown_failure_output: bool = False,
        stdout_truncated: bool = False,
        stderr_truncated: bool = False,
        decoding_lossy: bool = False,
        parse_complete: bool = True,
        patterns_considered: int = 0,
        patterns_matched: int = 0,
        records_emitted: int | None = None,
        unknown_lines: int = 0,
        limits_reached: bool = False,
        metadata: Metadata | None = None,
        *,
        operation: str | None = None,
    ) -> None:
        if operation_kind is None:
            operation_kind = operation
        elif operation is not None and operation != operation_kind:
            raise ValueError(
                "operation and operation_kind must identify the same operation"
            )
        if operation_kind is None:
            raise TypeError("operation_kind is required")

        parser_version_value = _text(
            parser_version,
            "parser_version",
            64,
        )
        status_value = _enum_or_string(
            status,
            ValidationStatus,
            "status",
        )
        gf_version_value = _optional_text(
            gf_version,
            "gf_version",
            _MAX_IDENTIFIER,
        )
        operation_value = _text(
            operation_kind,
            "operation_kind",
            _MAX_IDENTIFIER,
        )
        record_values = _typed_tuple(
            records,
            DiagnosticRecord,
            "records",
        )
        warning_values = _diagnostic_warning_tuple(warnings)

        record_ids = tuple(record.record_id for record in record_values)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("records contain duplicate record_id values")

        selected_primary_id = primary_record_id
        if selected_primary_id is not None:
            selected_primary_id = _text(
                selected_primary_id,
                "primary_record_id",
                _MAX_IDENTIFIER,
            )
            if selected_primary_id not in set(record_ids):
                raise ValueError(
                    "primary_record_id does not identify a record"
                )
        elif record_values:
            selected_primary_id = record_values[0].record_id

        primary_record = next(
            (
                record
                for record in record_values
                if record.record_id == selected_primary_id
            ),
            None,
        )

        if primary_error_kind is None:
            if primary_record is not None:
                primary_error_kind_value: ErrorKind | str | None = (
                    primary_record.error_kind
                )
            elif status_value is ValidationStatus.OK:
                primary_error_kind_value = ErrorKind.OK
            else:
                primary_error_kind_value = None
        else:
            primary_error_kind_value = _enum_or_string(
                primary_error_kind,
                ErrorKind,
                "primary_error_kind",
            )

        primary_message_value = _plain_text(
            primary_message,
            "primary_message",
            _MAX_MESSAGE,
        )
        primary_detail_value = _plain_text(
            primary_detail,
            "primary_detail",
            _MAX_DETAIL,
        )
        if primary_record is not None:
            if not primary_message_value:
                primary_message_value = primary_record.message
            if not primary_detail_value:
                primary_detail_value = primary_record.detail

        for name, value in (
            ("fatal_detected", fatal_detected),
            ("unknown_failure_output", unknown_failure_output),
            ("stdout_truncated", stdout_truncated),
            ("stderr_truncated", stderr_truncated),
            ("decoding_lossy", decoding_lossy),
            ("parse_complete", parse_complete),
            ("limits_reached", limits_reached),
        ):
            _bool(value, name)

        for name, value in (
            ("patterns_considered", patterns_considered),
            ("patterns_matched", patterns_matched),
            ("unknown_lines", unknown_lines),
        ):
            _nonnegative_int(value, name)
        if patterns_matched > patterns_considered:
            raise ValueError(
                "patterns_matched must not exceed patterns_considered"
            )

        if records_emitted is None:
            records_emitted_value = len(record_values)
        else:
            _nonnegative_int(records_emitted, "records_emitted")
            records_emitted_value = records_emitted
            if records_emitted_value != len(record_values):
                raise ValueError(
                    "records_emitted must equal the number of records"
                )

        fatal_value = fatal_detected or any(
            record.is_fatal for record in record_values
        )
        unknown_value = unknown_failure_output or any(
            record.is_unknown for record in record_values
        )

        metadata_value = _freeze_metadata(
            {} if metadata is None else metadata
        )

        values = {
            "parser_version": parser_version_value,
            "status": status_value,
            "gf_version": gf_version_value,
            "operation_kind": operation_value,
            "records": record_values,
            "warnings": warning_values,
            "primary_record_id": selected_primary_id,
            "primary_error_kind": primary_error_kind_value,
            "primary_message": primary_message_value,
            "primary_detail": primary_detail_value,
            "fatal_detected": fatal_value,
            "unknown_failure_output": unknown_value,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "decoding_lossy": decoding_lossy,
            "parse_complete": parse_complete,
            "patterns_considered": patterns_considered,
            "patterns_matched": patterns_matched,
            "records_emitted": records_emitted_value,
            "unknown_lines": unknown_lines,
            "limits_reached": limits_reached,
            "metadata": metadata_value,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def operation(self) -> str:
        """Legacy alias for the canonical operation kind."""

        return self.operation_kind

    @property
    def primary(self) -> DiagnosticRecord | None:
        if self.primary_record_id is None:
            return None
        for record in self.records:
            if record.record_id == self.primary_record_id:
                return record
        return None

    @property
    def secondary(self) -> tuple[DiagnosticRecord, ...]:
        primary = self.primary
        if primary is None:
            return self.records
        return tuple(
            record
            for record in self.records
            if record.record_id != primary.record_id
        )

    @property
    def references(self) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()
        for record in self.records:
            for reference in record.references:
                if reference not in seen:
                    result.append(reference)
                    seen.add(reference)
        return tuple(result)

    @property
    def parse_warnings(self) -> tuple[str, ...]:
        return tuple(
            warning.message
            if isinstance(warning, DiagnosticParseWarning)
            else warning
            for warning in self.warnings
        )


@dataclass(frozen=True, slots=True)
class DiagnosticPatternRegistry:
    parser_version: str
    patterns: tuple[DiagnosticPattern, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parser_version",
            _text(self.parser_version, "parser_version", 64),
        )
        patterns = _typed_tuple(self.patterns, DiagnosticPattern, "patterns")
        ids = tuple(pattern.pattern_id for pattern in patterns)
        if len(ids) != len(set(ids)):
            raise ValueError("pattern registry contains duplicate pattern IDs")
        priorities = tuple(pattern.priority for pattern in patterns)
        if priorities != tuple(sorted(priorities)):
            raise ValueError("pattern registry must be in priority order")
        object.__setattr__(self, "patterns", patterns)

    def get(self, pattern_id: str) -> DiagnosticPattern:
        canonical = _pattern_id(pattern_id)
        for pattern in self.patterns:
            if pattern.pattern_id == canonical:
                return pattern
        raise KeyError(canonical)

    def applicable(
        self,
        operation: str,
        *,
        stream: str | None = None,
    ) -> tuple[DiagnosticPattern, ...]:
        operation = _text(operation, "operation", _MAX_IDENTIFIER)
        selected: list[DiagnosticPattern] = []
        for pattern in self.patterns:
            if not _scope_accepts(pattern.operations, operation):
                continue
            if stream is not None and not _scope_accepts(pattern.streams, stream):
                continue
            if pattern.lifecycle_state is PatternLifecycle.RETIRED:
                continue
            selected.append(pattern)
        return tuple(selected)


def build_record_id(
    *,
    stream: DiagnosticStream | str | None,
    start_line: int | None,
    end_line: int | None,
    pattern_id: str,
    normalized_signature: str,
) -> str:
    stream_value = "none" if stream is None else _stream(stream, "stream").value
    _optional_positive_int(start_line, "start_line")
    _optional_positive_int(end_line, "end_line")
    pattern_value = _pattern_id(pattern_id)
    signature_value = _text(normalized_signature, "normalized_signature", _MAX_MESSAGE)
    payload = json.dumps(
        [stream_value, start_line, end_line, pattern_value, signature_value],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"diag-{hashlib.sha256(payload).hexdigest()[:16]}"


def normalized_diagnostic_signature(
    error_kind: ErrorKind | str,
    message: str,
) -> str:
    kind_value = _enum_or_string(error_kind, ErrorKind, "error_kind")
    kind_text = getattr(kind_value, "value", kind_value)
    message_value = _text(message, "message", _MAX_MESSAGE)
    normalized = " ".join(message_value.split())
    normalized = re.sub(r"(?i)(?:[A-Za-z]:)?[/\\][^\s:]+", "<path>", normalized)
    normalized = re.sub(r"(?<![A-Za-z_])\d+(?![A-Za-z_])", "<n>", normalized)
    return f"{kind_text}|{normalized}"


def records_from_matches(
    matches: Iterable[PatternMatch],
) -> tuple[DiagnosticRecord, ...]:
    if isinstance(matches, (str, bytes, bytearray, Mapping)):
        raise TypeError("matches must be an iterable of PatternMatch")
    result: list[DiagnosticRecord] = []
    seen: set[str] = set()
    for match in matches:
        if not isinstance(match, PatternMatch):
            raise TypeError("matches must contain PatternMatch values")
        record = DiagnosticRecord.from_match(match)
        if record.record_id in seen:
            continue
        result.append(record)
        seen.add(record.record_id)
        if len(result) > _MAX_ITEMS:
            raise ValueError("too many diagnostic records")
    return tuple(result)



def _diagnostic_warning_tuple(
    value: Iterable[DiagnosticParseWarning | str],
) -> tuple[DiagnosticParseWarning | str, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(
            "warnings must be an iterable of DiagnosticParseWarning or str"
        )
    result: list[DiagnosticParseWarning | str] = []
    for item in value:
        if isinstance(item, DiagnosticParseWarning):
            result.append(item)
        elif isinstance(item, str):
            result.append(
                _plain_text(item, "warning", _MAX_MESSAGE)
            )
        else:
            raise TypeError(
                "warnings must contain DiagnosticParseWarning or str values"
            )
        if len(result) > _MAX_ITEMS:
            raise ValueError("warnings exceeds the supported limit")
    return tuple(result)

def _scope_accepts(scope: frozenset[str], value: str) -> bool:
    normalized = value.strip().lower().replace("-", "_")
    if scope.intersection({"all", "any", "*", "either", "both-structure"}):
        return True
    return normalized in {item.lower().replace("-", "_") for item in scope}


def _pattern_id(value: object) -> str:
    text = _text(value, "pattern_id", _MAX_IDENTIFIER)
    if _PATTERN_ID_RE.fullmatch(text) is None:
        raise ValueError(f"invalid diagnostic pattern ID {text!r}")
    return text


def _stream(value: DiagnosticStream | str, field_name: str) -> DiagnosticStream:
    if isinstance(value, DiagnosticStream):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be DiagnosticStream or str")
    try:
        return DiagnosticStream(value)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name} {value!r}") from exc


def _enum(value: object, enum_type: type[_T], field_name: str) -> _T:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be {enum_type.__name__} or str")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name} {value!r}") from exc


def _enum_or_string(value: object, enum_type: type[_T], field_name: str) -> _T | str:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be {enum_type.__name__} or str")
    try:
        return enum_type(value)
    except ValueError:
        return _text(value, field_name, _MAX_IDENTIFIER)


def _scope_set(value: Iterable[object], field_name: str) -> frozenset[str]:
    if isinstance(value, str):
        value = (value,)
    if isinstance(value, Mapping):
        raise TypeError(f"{field_name} must not be a mapping")
    result: set[str] = set()
    for item in value:
        raw = getattr(item, "value", item)
        result.add(_text(raw, f"{field_name} item", _MAX_IDENTIFIER))
        if len(result) > _MAX_ITEMS:
            raise ValueError(f"{field_name} exceeds the supported limit")
    if not result:
        raise ValueError(f"{field_name} must not be empty")
    return frozenset(result)



def _compatibility_scope(
    value: Iterable[object],
    field_name: str,
) -> frozenset[str]:
    scope = _scope_set(value, field_name)
    normalized = {item.strip().lower() for item in scope}
    if normalized.intersection({"all", "any", "*"}):
        return frozenset()
    return scope

def _freeze_metadata(value: Metadata) -> Metadata:
    if not isinstance(value, Mapping):
        raise TypeError("metadata values must be mappings")
    if len(value) > _MAX_ITEMS:
        raise ValueError("metadata exceeds the supported limit")
    result: dict[str, MetadataValue] = {}
    for key, item in value.items():
        canonical_key = _text(key, "metadata key", _MAX_IDENTIFIER)
        result[canonical_key] = _freeze_metadata_value(item)
    return MappingProxyType(result)


def _freeze_metadata_value(value: Any) -> MetadataValue:
    if value is None or type(value) in (str, int, float, bool) or isinstance(value, Path):
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("metadata text must not contain NUL")
        return value
    if isinstance(value, Mapping):
        return _freeze_metadata(value)
    if isinstance(value, (str, bytes, bytearray)):
        raise TypeError("unsupported metadata value")
    if isinstance(value, Iterable):
        result = tuple(_freeze_metadata_value(item) for item in value)
        if len(result) > _MAX_ITEMS:
            raise ValueError("metadata sequence exceeds the supported limit")
        return result
    raise TypeError(f"unsupported metadata value type {type(value).__name__}")


def _typed_tuple(value: Iterable[Any], item_type: type[_T], field_name: str) -> tuple[_T, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be an iterable of {item_type.__name__}")
    result = tuple(value)
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported limit")
    if any(not isinstance(item, item_type) for item in result):
        raise TypeError(f"{field_name} must contain {item_type.__name__} values")
    return result


def _text_tuple(value: Iterable[object], field_name: str, max_length: int) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _text(item, f"{field_name} item", max_length)
        if text not in seen:
            result.append(text)
            seen.add(text)
        if len(result) > _MAX_ITEMS:
            raise ValueError(f"{field_name} exceeds the supported limit")
    return tuple(result)


def _plain_text_tuple(value: Iterable[object], field_name: str, max_length: int) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_plain_text(item, f"{field_name} item", max_length) for item in value)
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported limit")
    return result


def _text(value: object, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return _plain_text(value, field_name, max_length)


def _plain_text(value: object, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length")
    return value


def _optional_text(value: object, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    return _text(value, field_name, max_length)


def _optional_plain_text(value: object, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    return _plain_text(value, field_name, max_length)


def _coerce_path(value: object, field_name: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{field_name} must be str or Path")
    path = Path(value)
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    return path


def _optional_path(value: object, field_name: str) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value, field_name)


def _bool(value: object, field_name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be bool")


def _optional_bool(value: object, field_name: str) -> None:
    if value is not None:
        _bool(value, field_name)


def _positive_int(value: object, field_name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")


def _optional_positive_int(value: object, field_name: str) -> None:
    if value is not None:
        _positive_int(value, field_name)


def _nonnegative_int(value: object, field_name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


__all__ = (
    "ArtifactObservation",
    "DiagnosticEvidence",
    "DiagnosticLine",
    "DiagnosticLocation",
    "DiagnosticMatchResult",
    "DiagnosticParseResult",
    "DiagnosticParseWarning",
    "DiagnosticPattern",
    "DiagnosticPatternRegistry",
    "DiagnosticRecord",
    "DiagnosticSeverity",
    "DiagnosticStream",
    "DiagnosticStreamEvidence",
    "EvidenceRef",
    "Finding",
    "LineClassification",
    "Metadata",
    "MetadataValue",
    "PatternConfidence",
    "PatternLifecycle",
    "PatternMatch",
    "PatternMatcher",
    "StreamScope",
    "TopError",
    "build_record_id",
    "normalized_diagnostic_signature",
    "records_from_matches",
)
