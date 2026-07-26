"""Shared immutable diagnostic-pattern contracts and GF text patterns."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.ids import (
    DiagnosticPatternId,
    validate_diagnostic_pattern_id,
)
from gf_wordbench.kernel.statuses import ErrorKind

PARSER_PATTERN_VERSION: Final[str] = "1.0"
MAX_STREAM_CHARACTERS: Final[int] = 16 * 1024 * 1024
MAX_DIAGNOSTIC_LINE_CHARACTERS: Final[int] = 32 * 1024
MAX_EXCERPT_CHARACTERS: Final[int] = 128 * 1024
MAX_EXTRACTED_FIELDS: Final[int] = 32
MAX_FIELD_CHARACTERS: Final[int] = 32 * 1024

INTERNAL_GENERATE_PMCFG_PATTERN_ID: Final[DiagnosticPatternId] = (
    validate_diagnostic_pattern_id("GF-DIAG-INTERNAL-001")
)
EXPECTED_INFERRED_TYPE_PATTERN_ID: Final[DiagnosticPatternId] = (
    validate_diagnostic_pattern_id("GF-DIAG-TYPE-001")
)
SOURCE_SYNTAX_PATTERN_ID: Final[DiagnosticPatternId] = (
    validate_diagnostic_pattern_id("GF-DIAG-SYNTAX-001")
)
GF_SOURCE_REFERENCE_PATTERN_ID: Final[DiagnosticPatternId] = (
    validate_diagnostic_pattern_id("GF-DIAG-LOCATION-001")
)
FATAL_CONTEXT_PATTERN_ID: Final[DiagnosticPatternId] = (
    validate_diagnostic_pattern_id("GF-DIAG-CONTEXT-001")
)
UNKNOWN_PATTERN_ID: Final[str] = "DIAG-UNKNOWN"

_INTERNAL_GENERATE_PMCFG_RE: Final[re.Pattern[str]] = re.compile(
    r"Internal error in GeneratePMCFG"
)
_EXPECTED_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*expected:\s*(?P<value>.*)$"
)
_INFERRED_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*inferred:\s*(?P<value>.*)$"
)
_HAPPENED_IN_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?P<message>Happened in[^\r\n]*)\s*$"
)
_SOURCE_SYNTAX_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<message>.*(?:Syntax error|Parse error|Unexpected token).*)$"
)
_GF_SOURCE_REFERENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<path>[A-Za-z0-9_./\\-]+\.gf)\b",
    re.IGNORECASE,
)
_PROGRESS_COMPILE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*-\s+compiling\b"
)
_PROGRESS_LINK_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:linking|Writing)\b"
)
_FATAL_CONTEXT_RES: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"Internal error"),
    re.compile(r"Cannot find an inflection rule"),
    re.compile(r"\bCallStack\b"),
    re.compile(r"^\s*error:", re.IGNORECASE),
    re.compile(r"^\s*Exception:"),
    re.compile(r"^\s*Traceback\b"),
)
_NUL: Final[str] = "\x00"


@unique
class DiagnosticOperation(StrEnum):
    PROBE_VERSION = "probe_version"
    COMPILE_MODULE = "compile_module"
    BUILD_PGF = "build_pgf"
    RUN_SCENARIO = "run_scenario"
    INSPECT_GRAMMAR = "inspect_grammar"


@unique
class DiagnosticStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


@unique
class DiagnosticStreamScope(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    EITHER = "either"
    BOTH_STRUCTURE = "both-structure"


@unique
class PatternLifecycle(StrEnum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@unique
class PatternConfidence(StrEnum):
    EXACT = "exact"
    STRONG = "strong"
    FALLBACK = "fallback"
    UNKNOWN = "unknown"


@unique
class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True, slots=True)
class DiagnosticLine:
    stream: DiagnosticStream
    number: int
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.stream, DiagnosticStream):
            raise TypeError("stream must be DiagnosticStream")
        if type(self.number) is not int or self.number < 1:
            raise ValueError("number must be a positive integer")
        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            maximum=MAX_DIAGNOSTIC_LINE_CHARACTERS,
        )
        if "\r" in text or "\n" in text:
            raise ValueError("DiagnosticLine.text must contain exactly one line")
        object.__setattr__(self, "text", text)


@dataclass(frozen=True, slots=True)
class DiagnosticPatternInput:
    operation: DiagnosticOperation
    stdout: str = ""
    stderr: str = ""
    gf_version: str | None = None
    platform: str = field(default_factory=lambda: _canonical_platform(sys.platform))

    def __post_init__(self) -> None:
        if not isinstance(self.operation, DiagnosticOperation):
            raise TypeError("operation must be DiagnosticOperation")
        stdout = _require_text(
            self.stdout,
            field_name="stdout",
            allow_empty=True,
            maximum=MAX_STREAM_CHARACTERS,
        )
        stderr = _require_text(
            self.stderr,
            field_name="stderr",
            allow_empty=True,
            maximum=MAX_STREAM_CHARACTERS,
        )
        gf_version = _optional_text(
            self.gf_version,
            field_name="gf_version",
            maximum=256,
        )
        platform = _canonical_platform(
            _require_text(
                self.platform,
                field_name="platform",
                allow_empty=False,
                maximum=32,
            )
        )
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)
        object.__setattr__(self, "gf_version", gf_version)
        object.__setattr__(self, "platform", platform)

    def lines(
        self,
        scope: DiagnosticStreamScope = DiagnosticStreamScope.EITHER,
    ) -> tuple[DiagnosticLine, ...]:
        if not isinstance(scope, DiagnosticStreamScope):
            raise TypeError("scope must be DiagnosticStreamScope")
        if scope is DiagnosticStreamScope.STDOUT:
            return _split_stream(self.stdout, DiagnosticStream.STDOUT)
        if scope is DiagnosticStreamScope.STDERR:
            return _split_stream(self.stderr, DiagnosticStream.STDERR)
        return (
            *_split_stream(self.stdout, DiagnosticStream.STDOUT),
            *_split_stream(self.stderr, DiagnosticStream.STDERR),
        )


ExtractedFields: TypeAlias = Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PatternMatch:
    pattern_id: DiagnosticPatternId
    error_kind: ErrorKind | None
    severity: DiagnosticSeverity | None
    confidence: PatternConfidence
    message: str
    detail: str
    evidence_lines: tuple[DiagnosticLine, ...]
    extracted_fields: ExtractedFields = field(default_factory=dict)
    primary_eligible: bool = True

    def __post_init__(self) -> None:
        pattern_id = validate_diagnostic_pattern_id(self.pattern_id)
        if self.error_kind is not None and not isinstance(
            self.error_kind,
            ErrorKind,
        ):
            raise TypeError("error_kind must be ErrorKind or None")
        if self.severity is not None and not isinstance(
            self.severity,
            DiagnosticSeverity,
        ):
            raise TypeError("severity must be DiagnosticSeverity or None")
        if not isinstance(self.confidence, PatternConfidence):
            raise TypeError("confidence must be PatternConfidence")
        message = _require_text(
            self.message,
            field_name="message",
            allow_empty=False,
            maximum=MAX_FIELD_CHARACTERS,
        )
        detail = _require_text(
            self.detail,
            field_name="detail",
            allow_empty=True,
            maximum=MAX_FIELD_CHARACTERS,
        )
        evidence_lines = _freeze_lines(self.evidence_lines)
        extracted_fields = _freeze_fields(self.extracted_fields)
        if type(self.primary_eligible) is not bool:
            raise TypeError("primary_eligible must be a boolean")
        if self.primary_eligible and self.error_kind is None:
            raise ValueError(
                "a primary-eligible match must define an error kind"
            )
        object.__setattr__(self, "pattern_id", pattern_id)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "detail", detail)
        object.__setattr__(self, "evidence_lines", evidence_lines)
        object.__setattr__(self, "extracted_fields", extracted_fields)

    @property
    def raw_excerpt(self) -> str:
        return render_evidence_lines(self.evidence_lines)


@runtime_checkable
class DiagnosticPatternMatcher(Protocol):
    def __call__(
        self,
        evidence: DiagnosticPatternInput,
    ) -> PatternMatch | None:
        ...


@dataclass(frozen=True, slots=True)
class DiagnosticPattern:
    pattern_id: DiagnosticPatternId
    lifecycle_state: PatternLifecycle
    supported_operations: frozenset[DiagnosticOperation]
    supported_gf_versions: tuple[str, ...]
    supported_platforms: frozenset[str]
    stream_scope: DiagnosticStreamScope
    precedence: int
    confidence: PatternConfidence
    error_kind: ErrorKind | None
    severity: DiagnosticSeverity | None
    matcher: DiagnosticPatternMatcher
    false_positive_guards: tuple[str, ...] = ()
    fixtures: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        pattern_id = validate_diagnostic_pattern_id(self.pattern_id)
        if not isinstance(self.lifecycle_state, PatternLifecycle):
            raise TypeError("lifecycle_state must be PatternLifecycle")
        operations = frozenset(self.supported_operations)
        if not operations:
            raise ValueError("supported_operations must not be empty")
        if any(
            not isinstance(operation, DiagnosticOperation)
            for operation in operations
        ):
            raise TypeError(
                "supported_operations must contain DiagnosticOperation values"
            )
        versions = _freeze_text_tuple(
            self.supported_gf_versions,
            field_name="supported_gf_versions",
            allow_empty=False,
            maximum=128,
        )
        platforms = frozenset(
            _canonical_platform(platform)
            for platform in self.supported_platforms
        )
        if not platforms:
            raise ValueError("supported_platforms must not be empty")
        if not isinstance(self.stream_scope, DiagnosticStreamScope):
            raise TypeError("stream_scope must be DiagnosticStreamScope")
        if type(self.precedence) is not int or self.precedence < 0:
            raise ValueError("precedence must be a non-negative integer")
        if not isinstance(self.confidence, PatternConfidence):
            raise TypeError("confidence must be PatternConfidence")
        if self.error_kind is not None and not isinstance(
            self.error_kind,
            ErrorKind,
        ):
            raise TypeError("error_kind must be ErrorKind or None")
        if self.severity is not None and not isinstance(
            self.severity,
            DiagnosticSeverity,
        ):
            raise TypeError("severity must be DiagnosticSeverity or None")
        if not isinstance(self.matcher, DiagnosticPatternMatcher):
            raise TypeError(
                "matcher must satisfy DiagnosticPatternMatcher"
            )
        guards = _freeze_text_tuple(
            self.false_positive_guards,
            field_name="false_positive_guards",
            allow_empty=False,
            maximum=1_024,
        )
        fixtures = _freeze_text_tuple(
            self.fixtures,
            field_name="fixtures",
            allow_empty=False,
            maximum=1_024,
        )
        notes = _require_text(
            self.notes,
            field_name="notes",
            allow_empty=True,
            maximum=MAX_FIELD_CHARACTERS,
        )
        object.__setattr__(self, "pattern_id", pattern_id)
        object.__setattr__(self, "supported_operations", operations)
        object.__setattr__(self, "supported_gf_versions", versions)
        object.__setattr__(self, "supported_platforms", platforms)
        object.__setattr__(self, "false_positive_guards", guards)
        object.__setattr__(self, "fixtures", fixtures)
        object.__setattr__(self, "notes", notes)

    def applies_to(self, evidence: DiagnosticPatternInput) -> bool:
        if not isinstance(evidence, DiagnosticPatternInput):
            raise TypeError("evidence must be DiagnosticPatternInput")
        if self.lifecycle_state is PatternLifecycle.RETIRED:
            return False
        if evidence.operation not in self.supported_operations:
            return False
        if evidence.platform not in self.supported_platforms:
            return False
        return _version_supported(
            evidence.gf_version,
            self.supported_gf_versions,
        )

    def match(
        self,
        evidence: DiagnosticPatternInput,
    ) -> PatternMatch | None:
        if not self.applies_to(evidence):
            return None
        result = self.matcher(evidence)
        if result is None:
            return None
        if result.pattern_id != self.pattern_id:
            raise ValueError(
                f"matcher returned {result.pattern_id!r} for "
                f"{self.pattern_id!r}"
            )
        if result.confidence is not self.confidence:
            raise ValueError(
                f"matcher confidence does not match {self.pattern_id!r}"
            )
        if result.error_kind is not self.error_kind:
            raise ValueError(
                f"matcher error kind does not match {self.pattern_id!r}"
            )
        if result.severity is not self.severity:
            raise ValueError(
                f"matcher severity does not match {self.pattern_id!r}"
            )
        return result


def match_internal_generate_pmcfg(
    evidence: DiagnosticPatternInput,
) -> PatternMatch | None:
    for line in evidence.lines(DiagnosticStreamScope.EITHER):
        if _INTERNAL_GENERATE_PMCFG_RE.search(line.text) is None:
            continue
        return PatternMatch(
            pattern_id=INTERNAL_GENERATE_PMCFG_PATTERN_ID,
            error_kind=ErrorKind.INTERNAL,
            severity=DiagnosticSeverity.FATAL,
            confidence=PatternConfidence.STRONG,
            message=line.text.strip()
            or "Internal error in GeneratePMCFG",
            detail="GeneratePMCFG",
            evidence_lines=bounded_context(
                evidence,
                line,
                before=1,
                after=6,
            ),
            extracted_fields={"component": "GeneratePMCFG"},
        )
    return None


def match_expected_inferred_type(
    evidence: DiagnosticPatternInput,
) -> PatternMatch | None:
    lines = evidence.lines(DiagnosticStreamScope.BOTH_STRUCTURE)
    expected_line: DiagnosticLine | None = None
    inferred_line: DiagnosticLine | None = None
    expected_value = ""
    inferred_value = ""

    for line in lines:
        expected = _EXPECTED_RE.fullmatch(line.text)
        if expected is not None and expected_line is None:
            expected_line = line
            expected_value = expected.group("value")
            continue
        inferred = _INFERRED_RE.fullmatch(line.text)
        if inferred is not None and inferred_line is None:
            inferred_line = line
            inferred_value = inferred.group("value")

    if expected_line is None or inferred_line is None:
        return None

    context_line = _nearest_happened_in(
        lines,
        expected_line=expected_line,
        inferred_line=inferred_line,
    )
    message = (
        context_line.text.strip()
        if context_line is not None
        else "Type error"
    )
    evidence_lines = tuple(
        sorted(
            {
                (line.stream, line.number): line
                for line in (
                    expected_line,
                    inferred_line,
                    *(() if context_line is None else (context_line,)),
                )
            }.values(),
            key=_line_sort_key,
        )
    )
    return PatternMatch(
        pattern_id=EXPECTED_INFERRED_TYPE_PATTERN_ID,
        error_kind=ErrorKind.TYPE,
        severity=DiagnosticSeverity.ERROR,
        confidence=PatternConfidence.STRONG,
        message=message,
        detail=(
            f"expected: {expected_value} | "
            f"inferred: {inferred_value}"
        ),
        evidence_lines=evidence_lines,
        extracted_fields={
            "expected": expected_value,
            "inferred": inferred_value,
        },
    )


def match_source_syntax(
    evidence: DiagnosticPatternInput,
) -> PatternMatch | None:
    for line in evidence.lines(DiagnosticStreamScope.EITHER):
        matched = _SOURCE_SYNTAX_RE.fullmatch(line.text)
        if matched is None:
            continue
        message = matched.group("message").strip()
        if not message:
            continue
        return PatternMatch(
            pattern_id=SOURCE_SYNTAX_PATTERN_ID,
            error_kind=ErrorKind.SYNTAX,
            severity=DiagnosticSeverity.ERROR,
            confidence=PatternConfidence.STRONG,
            message=message,
            detail="",
            evidence_lines=bounded_context(
                evidence,
                line,
                before=1,
                after=2,
            ),
        )
    return None


INTERNAL_GENERATE_PMCFG_PATTERN: Final[DiagnosticPattern] = DiagnosticPattern(
    pattern_id=INTERNAL_GENERATE_PMCFG_PATTERN_ID,
    lifecycle_state=PatternLifecycle.ACTIVE,
    supported_operations=frozenset(
        {
            DiagnosticOperation.COMPILE_MODULE,
            DiagnosticOperation.BUILD_PGF,
            DiagnosticOperation.RUN_SCENARIO,
        }
    ),
    supported_gf_versions=("tested",),
    supported_platforms=frozenset({"windows", "posix"}),
    stream_scope=DiagnosticStreamScope.EITHER,
    precedence=100,
    confidence=PatternConfidence.STRONG,
    error_kind=ErrorKind.INTERNAL,
    severity=DiagnosticSeverity.FATAL,
    matcher=match_internal_generate_pmcfg,
    false_positive_guards=(
        "tool-output evidence only",
        "case-sensitive confirmed anchor",
    ),
    fixtures=(
        "internal_generate_pmcfg_stdout",
        "internal_generate_pmcfg_stderr",
        "internal_generate_pmcfg_negative",
    ),
)

EXPECTED_INFERRED_TYPE_PATTERN: Final[DiagnosticPattern] = DiagnosticPattern(
    pattern_id=EXPECTED_INFERRED_TYPE_PATTERN_ID,
    lifecycle_state=PatternLifecycle.ACTIVE,
    supported_operations=frozenset(
        {
            DiagnosticOperation.COMPILE_MODULE,
            DiagnosticOperation.BUILD_PGF,
            DiagnosticOperation.RUN_SCENARIO,
        }
    ),
    supported_gf_versions=("tested",),
    supported_platforms=frozenset({"windows", "posix"}),
    stream_scope=DiagnosticStreamScope.BOTH_STRUCTURE,
    precedence=200,
    confidence=PatternConfidence.STRONG,
    error_kind=ErrorKind.TYPE,
    severity=DiagnosticSeverity.ERROR,
    matcher=match_expected_inferred_type,
    false_positive_guards=(
        "both expected and inferred lines are required",
        "each structural line is anchored",
    ),
    fixtures=(
        "expected_inferred_stdout",
        "expected_inferred_stderr",
        "expected_inferred_split_streams",
        "expected_only_negative",
        "inferred_only_negative",
    ),
)

SOURCE_SYNTAX_PATTERN: Final[DiagnosticPattern] = DiagnosticPattern(
    pattern_id=SOURCE_SYNTAX_PATTERN_ID,
    lifecycle_state=PatternLifecycle.ACTIVE,
    supported_operations=frozenset(
        {
            DiagnosticOperation.COMPILE_MODULE,
            DiagnosticOperation.BUILD_PGF,
            DiagnosticOperation.RUN_SCENARIO,
        }
    ),
    supported_gf_versions=("tested",),
    supported_platforms=frozenset({"windows", "posix"}),
    stream_scope=DiagnosticStreamScope.EITHER,
    precedence=300,
    confidence=PatternConfidence.STRONG,
    error_kind=ErrorKind.SYNTAX,
    severity=DiagnosticSeverity.ERROR,
    matcher=match_source_syntax,
    false_positive_guards=(
        "tool-output evidence only",
        "complete diagnostic line retained",
        "operation scope required",
    ),
    fixtures=(
        "syntax_error",
        "parse_error",
        "unexpected_token",
        "linguistic_zero_parse_negative",
    ),
)

COMMON_PATTERNS: Final[tuple[DiagnosticPattern, ...]] = (
    INTERNAL_GENERATE_PMCFG_PATTERN,
    EXPECTED_INFERRED_TYPE_PATTERN,
    SOURCE_SYNTAX_PATTERN,
)


def match_common_patterns(
    evidence: DiagnosticPatternInput,
) -> tuple[PatternMatch, ...]:
    if not isinstance(evidence, DiagnosticPatternInput):
        raise TypeError("evidence must be DiagnosticPatternInput")
    matches: list[tuple[int, PatternMatch]] = []
    for pattern in COMMON_PATTERNS:
        matched = pattern.match(evidence)
        if matched is not None:
            matches.append((pattern.precedence, matched))
    matches.sort(
        key=lambda item: (
            item[0],
            item[1].pattern_id,
            _first_line_sort_key(item[1]),
        )
    )
    return tuple(match for _, match in matches)


def extract_gf_source_references(
    value: str | DiagnosticPatternInput,
) -> tuple[str, ...]:
    texts: tuple[str, ...]
    if isinstance(value, DiagnosticPatternInput):
        texts = (value.stdout, value.stderr)
    elif isinstance(value, str):
        texts = (
            _require_text(
                value,
                field_name="value",
                allow_empty=True,
                maximum=MAX_STREAM_CHARACTERS,
            ),
        )
    else:
        raise TypeError(
            "value must be a string or DiagnosticPatternInput"
        )

    references: dict[str, str] = {}
    for text in texts:
        for matched in _GF_SOURCE_REFERENCE_RE.finditer(text):
            original = matched.group("path")
            normalized = original.replace("\\", "/")
            normalized = re.sub(r"/+", "/", normalized)
            key = normalized.casefold()
            existing = references.get(key)
            if existing is None or (normalized.casefold(), normalized) < (
                existing.casefold(),
                existing,
            ):
                references[key] = normalized
    return tuple(
        sorted(
            references.values(),
            key=lambda item: (item.casefold(), item),
        )
    )


def select_fallback_candidate_line(
    evidence: DiagnosticPatternInput,
) -> DiagnosticLine | None:
    if not isinstance(evidence, DiagnosticPatternInput):
        raise TypeError("evidence must be DiagnosticPatternInput")
    for line in evidence.lines(DiagnosticStreamScope.EITHER):
        stripped = line.text.strip()
        if not stripped:
            continue
        if _is_progress_line(stripped):
            continue
        return line
    return None


def fatal_context_lines(
    evidence: DiagnosticPatternInput,
) -> tuple[DiagnosticLine, ...]:
    if not isinstance(evidence, DiagnosticPatternInput):
        raise TypeError("evidence must be DiagnosticPatternInput")
    return tuple(
        line
        for line in evidence.lines(DiagnosticStreamScope.EITHER)
        if any(pattern.search(line.text) for pattern in _FATAL_CONTEXT_RES)
    )


def bounded_context(
    evidence: DiagnosticPatternInput,
    anchor: DiagnosticLine,
    *,
    before: int,
    after: int,
) -> tuple[DiagnosticLine, ...]:
    if not isinstance(evidence, DiagnosticPatternInput):
        raise TypeError("evidence must be DiagnosticPatternInput")
    if not isinstance(anchor, DiagnosticLine):
        raise TypeError("anchor must be DiagnosticLine")
    _require_non_negative_int(before, field_name="before")
    _require_non_negative_int(after, field_name="after")
    stream_lines = evidence.lines(
        DiagnosticStreamScope.STDOUT
        if anchor.stream is DiagnosticStream.STDOUT
        else DiagnosticStreamScope.STDERR
    )
    if anchor.number > len(stream_lines):
        raise ValueError("anchor line is outside the selected stream")
    selected = stream_lines[
        max(0, anchor.number - before - 1):
        min(len(stream_lines), anchor.number + after)
    ]
    if not any(
        line.number == anchor.number and line.text == anchor.text
        for line in selected
    ):
        raise ValueError("anchor does not match the supplied evidence")
    return _bound_excerpt_lines(selected)


def render_evidence_lines(lines: Iterable[DiagnosticLine]) -> str:
    prepared = _freeze_lines(lines)
    rendered = "\n".join(
        f"[{line.stream.value}:{line.number}] {line.text}"
        for line in prepared
    )
    if len(rendered) <= MAX_EXCERPT_CHARACTERS:
        return rendered
    return (
        rendered[: MAX_EXCERPT_CHARACTERS - 26]
        + "\n... <excerpt omitted> ..."
    )


def canonical_pattern_order(
    patterns: Iterable[DiagnosticPattern],
) -> tuple[DiagnosticPattern, ...]:
    if isinstance(patterns, (str, bytes)):
        raise TypeError(
            "patterns must be an iterable of DiagnosticPattern"
        )
    prepared = tuple(patterns)
    seen: set[DiagnosticPatternId] = set()
    for pattern in prepared:
        if not isinstance(pattern, DiagnosticPattern):
            raise TypeError(
                "patterns must contain DiagnosticPattern objects"
            )
        if pattern.pattern_id in seen:
            raise ValueError(
                f"duplicate diagnostic pattern ID {pattern.pattern_id!r}"
            )
        seen.add(pattern.pattern_id)
    return tuple(
        sorted(
            prepared,
            key=lambda pattern: (
                pattern.precedence,
                pattern.pattern_id,
            ),
        )
    )


def _split_stream(
    text: str,
    stream: DiagnosticStream,
) -> tuple[DiagnosticLine, ...]:
    if not text:
        return ()
    return tuple(
        DiagnosticLine(
            stream=stream,
            number=index,
            text=line,
        )
        for index, line in enumerate(text.splitlines(), start=1)
    )


def _nearest_happened_in(
    lines: Sequence[DiagnosticLine],
    *,
    expected_line: DiagnosticLine,
    inferred_line: DiagnosticLine,
) -> DiagnosticLine | None:
    candidates: list[tuple[int, int, DiagnosticLine]] = []
    for line in lines:
        if _HAPPENED_IN_RE.fullmatch(line.text) is None:
            continue
        distance = min(
            _line_distance(line, expected_line),
            _line_distance(line, inferred_line),
        )
        candidates.append(
            (
                distance,
                0 if line.stream is DiagnosticStream.STDOUT else 1,
                line,
            )
        )
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2].number,
        )
    )
    return candidates[0][2]


def _line_distance(
    left: DiagnosticLine,
    right: DiagnosticLine,
) -> int:
    if left.stream is not right.stream:
        return MAX_STREAM_CHARACTERS
    return abs(left.number - right.number)


def _is_progress_line(value: str) -> bool:
    return (
        _PROGRESS_COMPILE_RE.match(value) is not None
        or _PROGRESS_LINK_RE.match(value) is not None
    )


def _version_supported(
    gf_version: str | None,
    supported: tuple[str, ...],
) -> bool:
    if "all" in supported or "tested" in supported:
        return True
    if gf_version is None:
        return False
    return gf_version in supported


def _bound_excerpt_lines(
    lines: Sequence[DiagnosticLine],
) -> tuple[DiagnosticLine, ...]:
    selected: list[DiagnosticLine] = []
    characters = 0
    for line in lines:
        increment = len(line.text) + 32
        if selected and characters + increment > MAX_EXCERPT_CHARACTERS:
            break
        selected.append(line)
        characters += increment
    return tuple(selected)


def _freeze_lines(
    values: Iterable[DiagnosticLine],
) -> tuple[DiagnosticLine, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            "evidence_lines must be an iterable of DiagnosticLine"
        )
    prepared = tuple(values)
    if not prepared:
        raise ValueError("evidence_lines must not be empty")
    for line in prepared:
        if not isinstance(line, DiagnosticLine):
            raise TypeError(
                "evidence_lines must contain DiagnosticLine objects"
            )
    keys = tuple(
        (line.stream, line.number)
        for line in prepared
    )
    if len(keys) != len(set(keys)):
        raise ValueError(
            "evidence_lines must not repeat a stream line"
        )
    return tuple(sorted(prepared, key=_line_sort_key))


def _freeze_fields(values: ExtractedFields) -> ExtractedFields:
    if not isinstance(values, Mapping):
        raise TypeError("extracted_fields must be a mapping")
    if len(values) > MAX_EXTRACTED_FIELDS:
        raise ValueError(
            "extracted_fields exceeds the supported item limit"
        )
    prepared: dict[str, str] = {}
    for key, value in values.items():
        key = _require_text(
            key,
            field_name="extracted_fields key",
            allow_empty=False,
            maximum=128,
        )
        if not re.fullmatch(
            r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*",
            key,
        ):
            raise ValueError(
                f"invalid extracted field name {key!r}"
            )
        prepared[key] = _require_text(
            value,
            field_name=f"extracted_fields[{key!r}]",
            allow_empty=True,
            maximum=MAX_FIELD_CHARACTERS,
        )
    return MappingProxyType(prepared)


def _freeze_text_tuple(
    values: Iterable[str],
    *,
    field_name: str,
    allow_empty: bool,
    maximum: int,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    prepared = tuple(
        _require_text(
            value,
            field_name=f"{field_name} item",
            allow_empty=allow_empty,
            maximum=maximum,
        )
        for value in values
    )
    if len(prepared) != len(set(prepared)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return prepared


def _canonical_platform(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.startswith("win"):
        return "windows"
    if normalized in {
        "posix",
        "linux",
        "darwin",
        "freebsd",
        "openbsd",
        "netbsd",
        "aix",
    }:
        return "posix"
    raise ValueError(f"unsupported platform {value!r}")


def _line_sort_key(
    line: DiagnosticLine,
) -> tuple[int, int]:
    return (
        0 if line.stream is DiagnosticStream.STDOUT else 1,
        line.number,
    )


def _first_line_sort_key(
    match: PatternMatch,
) -> tuple[int, int]:
    return _line_sort_key(match.evidence_lines[0])


def _require_non_negative_int(
    value: object,
    *,
    field_name: str,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_text(
    value: object,
    *,
    field_name: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    return _require_text(
        value,
        field_name=field_name,
        allow_empty=False,
        maximum=maximum,
    )


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if _NUL in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > maximum:
        raise ValueError(
            f"{field_name} exceeds the supported length limit"
        )
    return value


__all__ = (
    "COMMON_PATTERNS",
    "EXPECTED_INFERRED_TYPE_PATTERN",
    "EXPECTED_INFERRED_TYPE_PATTERN_ID",
    "FATAL_CONTEXT_PATTERN_ID",
    "GF_SOURCE_REFERENCE_PATTERN_ID",
    "INTERNAL_GENERATE_PMCFG_PATTERN",
    "INTERNAL_GENERATE_PMCFG_PATTERN_ID",
    "MAX_DIAGNOSTIC_LINE_CHARACTERS",
    "MAX_EXCERPT_CHARACTERS",
    "MAX_STREAM_CHARACTERS",
    "PARSER_PATTERN_VERSION",
    "SOURCE_SYNTAX_PATTERN",
    "SOURCE_SYNTAX_PATTERN_ID",
    "UNKNOWN_PATTERN_ID",
    "DiagnosticLine",
    "DiagnosticOperation",
    "DiagnosticPattern",
    "DiagnosticPatternInput",
    "DiagnosticPatternMatcher",
    "DiagnosticSeverity",
    "DiagnosticStream",
    "DiagnosticStreamScope",
    "ExtractedFields",
    "PatternConfidence",
    "PatternLifecycle",
    "PatternMatch",
    "bounded_context",
    "canonical_pattern_order",
    "extract_gf_source_references",
    "fatal_context_lines",
    "match_common_patterns",
    "match_expected_inferred_type",
    "match_internal_generate_pmcfg",
    "match_source_syntax",
    "render_evidence_lines",
    "select_fallback_candidate_line",
)
