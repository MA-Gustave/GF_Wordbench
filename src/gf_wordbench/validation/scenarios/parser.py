"""Scenario source parsing and preflight validation for GF Wordbench."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
from hashlib import sha256
from pathlib import Path
from typing import Final

from gf_wordbench.kernel.errors import ProjectConfigurationError
from gf_wordbench.kernel.ids import (
    ScenarioId,
    SectionId,
    validate_scenario_id,
    validate_section_id,
)

DEFAULT_SCENARIO_MAX_BYTES: Final[int] = 1_048_576
DEFAULT_SCENARIO_MAX_LINE_CHARS: Final[int] = 16_384

_ID_PATTERN: Final[str] = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
_MARKER_RE: Final[re.Pattern[str]] = re.compile(
    rf"@@GF-WORDBENCH (?P<phase>BEGIN|END) "
    rf"(?P<scenario>{_ID_PATTERN}) "
    rf"(?P<section>{_ID_PATTERN})@@"
)
_RESERVED_MARKER_PREFIX: Final[str] = "@@GF-WORDBENCH"
_WINDOWS_ABSOLUTE_PATH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\[^\\/\s]+[\\/])"
)
_POSIX_MACHINE_PATH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9_])/"
    r"(?:home|Users|private|tmp|var|etc|opt|usr|mnt|Volumes)(?:/|\b)"
)
_ENVIRONMENT_REFERENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:"
    r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[^}\r\n]+\})"
    r"|%[A-Za-z_][A-Za-z0-9_]*%"
    r"|\$env:[A-Za-z_][A-Za-z0-9_]*"
    r")",
    re.IGNORECASE,
)
_PROHIBITED_COMMAND_NAMES: Final[frozenset[str]] = frozenset(
    {
        "exec",
        "pipe",
        "process",
        "run-process",
        "shell",
        "spawn",
        "system",
    }
)
_GENERATION_COMMAND_NAMES: Final[frozenset[str]] = frozenset(
    {
        "generate_random",
        "generate_trees",
        "gr",
        "gt",
    }
)
_GENERATION_BOUND_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:"
    r"(?:^|\s)-(?:cat|category|depth|n|number|max|max-count|limit)"
    r"(?:=|\s+)\S+"
    r"|(?:^|\s)(?:cat|category|depth|number|limit)\s*=\s*\S+"
    r")",
    re.IGNORECASE,
)


@unique
class ScenarioScriptIssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@unique
class ScenarioScriptIssueCode(StrEnum):
    EMPTY_SCRIPT = "empty_script"
    INVALID_UTF8 = "invalid_utf8"
    NUL_CHARACTER = "nul_character"
    FILE_TOO_LARGE = "file_too_large"
    LINE_TOO_LONG = "line_too_long"
    MISSING_FINAL_NEWLINE = "missing_final_newline"
    UNTERMINATED_BLOCK_COMMENT = "unterminated_block_comment"
    PROHIBITED_SHELL_ESCAPE = "prohibited_shell_escape"
    MACHINE_LOCAL_ABSOLUTE_PATH = "machine_local_absolute_path"
    ENVIRONMENT_REFERENCE = "environment_reference"
    MALFORMED_RESERVED_MARKER = "malformed_reserved_marker"
    WRONG_SCENARIO_MARKER = "wrong_scenario_marker"
    DUPLICATE_BEGIN_MARKER = "duplicate_begin_marker"
    DUPLICATE_END_MARKER = "duplicate_end_marker"
    END_WITHOUT_BEGIN = "end_without_begin"
    NESTED_BEGIN_MARKER = "nested_begin_marker"
    MISMATCHED_END_MARKER = "mismatched_end_marker"
    OPEN_SECTION_AT_EOF = "open_section_at_eof"
    MISSING_TERMINATION = "missing_termination"
    MULTIPLE_TERMINATION = "multiple_termination"
    COMMAND_AFTER_TERMINATION = "command_after_termination"
    UNBOUNDED_GENERATION = "unbounded_generation"


@unique
class ScenarioScriptLineKind(StrEnum):
    BLANK = "blank"
    COMMENT = "comment"
    COMMAND = "command"
    TERMINATION = "termination"


@unique
class ScenarioMarkerPhase(StrEnum):
    BEGIN = "BEGIN"
    END = "END"



def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a bool")
    return value


def _require_positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class ScenarioParserPolicy:
    max_bytes: int = DEFAULT_SCENARIO_MAX_BYTES
    max_line_chars: int = DEFAULT_SCENARIO_MAX_LINE_CHARS
    require_final_newline: bool = True
    require_explicit_termination: bool = True
    reject_shell_escape: bool = True
    reject_machine_absolute_paths: bool = True
    reject_environment_references: bool = True
    require_generation_bound: bool = True
    timeout_is_generation_bound: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("max_bytes", self.max_bytes)
        _require_positive_int("max_line_chars", self.max_line_chars)
        _require_bool("require_final_newline", self.require_final_newline)
        _require_bool(
            "require_explicit_termination",
            self.require_explicit_termination,
        )
        _require_bool("reject_shell_escape", self.reject_shell_escape)
        _require_bool(
            "reject_machine_absolute_paths",
            self.reject_machine_absolute_paths,
        )
        _require_bool(
            "reject_environment_references",
            self.reject_environment_references,
        )
        _require_bool(
            "require_generation_bound",
            self.require_generation_bound,
        )
        _require_bool(
            "timeout_is_generation_bound",
            self.timeout_is_generation_bound,
        )


DEFAULT_SCENARIO_PARSER_POLICY: Final[ScenarioParserPolicy] = (
    ScenarioParserPolicy()
)


@dataclass(frozen=True, slots=True)
class ScenarioScriptIssue:
    severity: ScenarioScriptIssueSeverity
    code: ScenarioScriptIssueCode
    message: str
    line: int | None = None
    column: int | None = None
    excerpt: str = ""

    def __post_init__(self) -> None:
        if not isinstance(
            self.severity,
            ScenarioScriptIssueSeverity,
        ):
            raise TypeError(
                "severity must be a ScenarioScriptIssueSeverity"
            )
        if not isinstance(self.code, ScenarioScriptIssueCode):
            raise TypeError("code must be a ScenarioScriptIssueCode")
        _require_non_empty_text("message", self.message)
        _require_optional_positive_int("line", self.line)
        _require_optional_positive_int("column", self.column)
        if self.column is not None and self.line is None:
            raise ValueError("column requires line")
        _require_text("excerpt", self.excerpt)


@dataclass(frozen=True, slots=True)
class ScenarioMarkerLiteral:
    phase: ScenarioMarkerPhase
    scenario_id: ScenarioId
    section_id: SectionId
    line: int
    column: int
    literal: str

    def __post_init__(self) -> None:
        if not isinstance(self.phase, ScenarioMarkerPhase):
            raise TypeError("phase must be a ScenarioMarkerPhase")
        object.__setattr__(
            self,
            "scenario_id",
            validate_scenario_id(
                self.scenario_id,
                field="marker scenario ID",
            ),
        )
        object.__setattr__(
            self,
            "section_id",
            validate_section_id(
                self.section_id,
                field="marker section ID",
            ),
        )
        _require_positive_int("line", self.line)
        _require_positive_int("column", self.column)
        _require_non_empty_text("literal", self.literal)


@dataclass(frozen=True, slots=True)
class ScenarioScriptLine:
    line_number: int
    raw_text: str
    code_text: str
    kind: ScenarioScriptLineKind
    command_name: str | None
    markers: tuple[ScenarioMarkerLiteral, ...]

    def __post_init__(self) -> None:
        _require_positive_int("line_number", self.line_number)
        if not isinstance(self.raw_text, str):
            raise TypeError("raw_text must be a string")
        if not isinstance(self.code_text, str):
            raise TypeError("code_text must be a string")
        if not isinstance(self.kind, ScenarioScriptLineKind):
            raise TypeError("kind must be a ScenarioScriptLineKind")
        if self.command_name is not None:
            _require_non_empty_text("command_name", self.command_name)
        if not isinstance(self.markers, tuple):
            raise TypeError("markers must be a tuple")
        for index, marker in enumerate(self.markers):
            if not isinstance(marker, ScenarioMarkerLiteral):
                raise TypeError(
                    f"markers[{index}] must be a ScenarioMarkerLiteral"
                )


class ScenarioScriptParseError(ProjectConfigurationError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedScenarioScript:
    scenario_id: ScenarioId
    source_path: Path | None
    sha256: str
    size_bytes: int
    line_count: int
    lines: tuple[ScenarioScriptLine, ...]
    markers: tuple[ScenarioMarkerLiteral, ...]
    completed_sections: tuple[SectionId, ...]
    termination_line: int | None
    issues: tuple[ScenarioScriptIssue, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_id",
            validate_scenario_id(self.scenario_id),
        )
        if self.source_path is not None:
            if not isinstance(self.source_path, Path):
                raise TypeError("source_path must be pathlib.Path or None")
            if "\x00" in str(self.source_path):
                raise ValueError("source_path must not contain NUL")
        if (
            not isinstance(self.sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None
        ):
            raise ValueError("sha256 must be a lowercase SHA-256 digest")
        _require_non_negative_int("size_bytes", self.size_bytes)
        _require_non_negative_int("line_count", self.line_count)
        _require_optional_positive_int(
            "termination_line",
            self.termination_line,
        )
        _require_tuple_members(
            "lines",
            self.lines,
            ScenarioScriptLine,
        )
        _require_tuple_members(
            "markers",
            self.markers,
            ScenarioMarkerLiteral,
        )
        if not isinstance(self.completed_sections, tuple):
            raise TypeError("completed_sections must be a tuple")
        for index, section_id in enumerate(self.completed_sections):
            validate_section_id(
                section_id,
                field=f"completed_sections[{index}]",
            )
        _require_tuple_members(
            "issues",
            self.issues,
            ScenarioScriptIssue,
        )

    @property
    def errors(self) -> tuple[ScenarioScriptIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is ScenarioScriptIssueSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ScenarioScriptIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is ScenarioScriptIssueSeverity.WARNING
        )

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def command_lines(self) -> tuple[ScenarioScriptLine, ...]:
        return tuple(
            line
            for line in self.lines
            if line.kind
            in {
                ScenarioScriptLineKind.COMMAND,
                ScenarioScriptLineKind.TERMINATION,
            }
        )

    @property
    def section_ids(self) -> tuple[SectionId, ...]:
        seen: set[SectionId] = set()
        ordered: list[SectionId] = []
        for marker in self.markers:
            if marker.section_id not in seen:
                seen.add(marker.section_id)
                ordered.append(marker.section_id)
        return tuple(ordered)

    def require_valid(self) -> ParsedScenarioScript:
        if self.valid:
            return self

        details = "; ".join(
            _format_issue(issue)
            for issue in self.errors
        )
        subject = (
            str(self.source_path)
            if self.source_path is not None
            else str(self.scenario_id)
        )
        evidence_paths = (
            ()
            if self.source_path is None
            else (str(self.source_path),)
        )

        raise ScenarioScriptParseError(
            "scenario source failed preflight parsing",
            code="GF-WB-SCENARIO-006",
            detail=details,
            stage="scenario",
            operation="parse_scenario_script",
            subject=subject,
            evidence_paths=evidence_paths,
        )


@dataclass(slots=True)
class _MarkerState:
    open_section: SectionId | None
    begun: set[SectionId]
    ended: set[SectionId]
    completed: list[SectionId]


def parse_scenario_file(
    path: Path,
    *,
    scenario_id: str | ScenarioId,
    policy: ScenarioParserPolicy = DEFAULT_SCENARIO_PARSER_POLICY,
) -> ParsedScenarioScript:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    if "\x00" in str(path):
        raise ValueError("path must not contain NUL")
    if path.suffix.casefold() != ".gfs":
        raise ScenarioScriptParseError(
            "scenario source must use the .gfs extension",
            code="GF-WB-SCENARIO-007",
            detail=str(path),
            stage="scenario",
            operation="parse_scenario_file",
            subject=str(path),
            evidence_paths=(str(path),),
        )
    if not isinstance(policy, ScenarioParserPolicy):
        raise TypeError("policy must be a ScenarioParserPolicy")

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ScenarioScriptParseError(
            "scenario source could not be read",
            code="GF-WB-IO-001",
            detail=str(exc),
            stage="scenario",
            operation="read_scenario_file",
            subject=str(path),
            evidence_paths=(str(path),),
        ) from exc

    return parse_scenario_bytes(
        data,
        scenario_id=scenario_id,
        source_path=path,
        policy=policy,
    )


def parse_scenario_text(
    text: str,
    *,
    scenario_id: str | ScenarioId,
    source_path: Path | None = None,
    policy: ScenarioParserPolicy = DEFAULT_SCENARIO_PARSER_POLICY,
) -> ParsedScenarioScript:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    try:
        data = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        validated_id = validate_scenario_id(scenario_id)
        digest = sha256(text.encode("utf-8", errors="replace")).hexdigest()
        issue = ScenarioScriptIssue(
            severity=ScenarioScriptIssueSeverity.ERROR,
            code=ScenarioScriptIssueCode.INVALID_UTF8,
            message="scenario text cannot be encoded as UTF-8",
        )
        return ParsedScenarioScript(
            scenario_id=validated_id,
            source_path=source_path,
            sha256=digest,
            size_bytes=0,
            line_count=0,
            lines=(),
            markers=(),
            completed_sections=(),
            termination_line=None,
            issues=(issue,),
        )

    return parse_scenario_bytes(
        data,
        scenario_id=scenario_id,
        source_path=source_path,
        policy=policy,
    )


def parse_scenario_bytes(
    data: bytes,
    *,
    scenario_id: str | ScenarioId,
    source_path: Path | None = None,
    policy: ScenarioParserPolicy = DEFAULT_SCENARIO_PARSER_POLICY,
) -> ParsedScenarioScript:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if source_path is not None and not isinstance(source_path, Path):
        raise TypeError("source_path must be pathlib.Path or None")
    if not isinstance(policy, ScenarioParserPolicy):
        raise TypeError("policy must be a ScenarioParserPolicy")

    validated_id = validate_scenario_id(scenario_id)
    digest = sha256(data).hexdigest()
    issues: list[ScenarioScriptIssue] = []

    if len(data) > policy.max_bytes:
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.FILE_TOO_LARGE,
                message=(
                    f"scenario source exceeds {policy.max_bytes} bytes"
                ),
            )
        )

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.INVALID_UTF8,
                message="scenario source is not valid UTF-8",
                line=None,
                column=None,
                excerpt=(
                    f"byte offset {exc.start}: "
                    f"{_bounded_hex_excerpt(data, exc.start)}"
                ),
            )
        )
        return ParsedScenarioScript(
            scenario_id=validated_id,
            source_path=source_path,
            sha256=digest,
            size_bytes=len(data),
            line_count=0,
            lines=(),
            markers=(),
            completed_sections=(),
            termination_line=None,
            issues=tuple(issues),
        )

    if "\x00" in text:
        index = text.index("\x00")
        line, column = _line_column(text, index)
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.NUL_CHARACTER,
                message="scenario source contains a NUL character",
                line=line,
                column=column,
                excerpt=_line_excerpt(text, line),
            )
        )

    if (
        policy.require_final_newline
        and data
        and not data.endswith(b"\n")
    ):
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.MISSING_FINAL_NEWLINE,
                message="scenario source must end with a newline",
                line=_physical_line_count(text),
                column=None,
                excerpt=_last_line_excerpt(text),
            )
        )

    raw_lines = text.splitlines()
    if text.endswith(("\n", "\r")):
        line_count = len(raw_lines)
    else:
        line_count = len(raw_lines)

    parsed_lines: list[ScenarioScriptLine] = []
    all_markers: list[ScenarioMarkerLiteral] = []
    marker_state = _MarkerState(
        open_section=None,
        begun=set(),
        ended=set(),
        completed=[],
    )
    block_comment_depth = 0
    termination_line: int | None = None
    command_count = 0

    for line_number, raw_line in enumerate(raw_lines, start=1):
        if len(raw_line) > policy.max_line_chars:
            issues.append(
                ScenarioScriptIssue(
                    severity=ScenarioScriptIssueSeverity.ERROR,
                    code=ScenarioScriptIssueCode.LINE_TOO_LONG,
                    message=(
                        "scenario line exceeds "
                        f"{policy.max_line_chars} characters"
                    ),
                    line=line_number,
                    column=policy.max_line_chars + 1,
                    excerpt=_bounded_excerpt(raw_line),
                )
            )

        code_text, block_comment_depth, had_comment = _strip_comments(
            raw_line,
            block_comment_depth,
        )
        stripped = code_text.strip()

        if not raw_line.strip():
            kind = ScenarioScriptLineKind.BLANK
            command_name = None
        elif not stripped and had_comment:
            kind = ScenarioScriptLineKind.COMMENT
            command_name = None
        elif not stripped:
            kind = ScenarioScriptLineKind.BLANK
            command_name = None
        else:
            command_count += 1
            command_name = _command_name(stripped)
            if stripped == "q":
                kind = ScenarioScriptLineKind.TERMINATION
            else:
                kind = ScenarioScriptLineKind.COMMAND

        line_markers = _parse_line_markers(
            code_text,
            line_number=line_number,
            expected_scenario_id=validated_id,
            issues=issues,
        )
        all_markers.extend(line_markers)
        _advance_marker_state(
            line_markers,
            marker_state,
            issues,
        )

        if stripped:
            _inspect_security(
                stripped,
                line_number=line_number,
                policy=policy,
                issues=issues,
            )
            _inspect_generation_bound(
                stripped,
                command_name=command_name,
                line_number=line_number,
                policy=policy,
                issues=issues,
            )

            if kind is ScenarioScriptLineKind.TERMINATION:
                if termination_line is None:
                    termination_line = line_number
                else:
                    issues.append(
                        ScenarioScriptIssue(
                            severity=ScenarioScriptIssueSeverity.ERROR,
                            code=ScenarioScriptIssueCode.MULTIPLE_TERMINATION,
                            message=(
                                "scenario contains more than one "
                                "termination command"
                            ),
                            line=line_number,
                            column=_first_non_space_column(code_text),
                            excerpt=_bounded_excerpt(raw_line),
                        )
                    )
            elif termination_line is not None:
                issues.append(
                    ScenarioScriptIssue(
                        severity=ScenarioScriptIssueSeverity.ERROR,
                        code=ScenarioScriptIssueCode.COMMAND_AFTER_TERMINATION,
                        message=(
                            "scenario command appears after "
                            "the termination command"
                        ),
                        line=line_number,
                        column=_first_non_space_column(code_text),
                        excerpt=_bounded_excerpt(raw_line),
                    )
                )

        parsed_lines.append(
            ScenarioScriptLine(
                line_number=line_number,
                raw_text=raw_line,
                code_text=code_text,
                kind=kind,
                command_name=command_name,
                markers=line_markers,
            )
        )

    if block_comment_depth:
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.UNTERMINATED_BLOCK_COMMENT,
                message="scenario source contains an unterminated block comment",
                line=max(1, line_count),
                excerpt=_last_line_excerpt(text),
            )
        )

    if command_count == 0:
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.EMPTY_SCRIPT,
                message="scenario source contains no executable GF command",
            )
        )

    if (
        policy.require_explicit_termination
        and termination_line is None
    ):
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.MISSING_TERMINATION,
                message="scenario source must terminate explicitly with q",
                line=max(1, line_count) if line_count else None,
                excerpt=_last_line_excerpt(text),
            )
        )

    if marker_state.open_section is not None:
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.OPEN_SECTION_AT_EOF,
                message=(
                    "scenario marker section remains open at end of file: "
                    f"{marker_state.open_section}"
                ),
                line=max(1, line_count) if line_count else None,
                excerpt=_last_line_excerpt(text),
            )
        )

    ordered_issues = tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.line is None,
                issue.line or 0,
                issue.column is None,
                issue.column or 0,
                issue.code.value,
                issue.message,
            ),
        )
    )

    return ParsedScenarioScript(
        scenario_id=validated_id,
        source_path=source_path,
        sha256=digest,
        size_bytes=len(data),
        line_count=line_count,
        lines=tuple(parsed_lines),
        markers=tuple(all_markers),
        completed_sections=tuple(marker_state.completed),
        termination_line=termination_line,
        issues=ordered_issues,
    )


def validate_scenario_file(
    path: Path,
    *,
    scenario_id: str | ScenarioId,
    policy: ScenarioParserPolicy = DEFAULT_SCENARIO_PARSER_POLICY,
) -> ParsedScenarioScript:
    return parse_scenario_file(
        path,
        scenario_id=scenario_id,
        policy=policy,
    ).require_valid()


def validate_scenario_text(
    text: str,
    *,
    scenario_id: str | ScenarioId,
    source_path: Path | None = None,
    policy: ScenarioParserPolicy = DEFAULT_SCENARIO_PARSER_POLICY,
) -> ParsedScenarioScript:
    return parse_scenario_text(
        text,
        scenario_id=scenario_id,
        source_path=source_path,
        policy=policy,
    ).require_valid()


def _parse_line_markers(
    code_text: str,
    *,
    line_number: int,
    expected_scenario_id: ScenarioId,
    issues: list[ScenarioScriptIssue],
) -> tuple[ScenarioMarkerLiteral, ...]:
    matches = tuple(_MARKER_RE.finditer(code_text))
    markers: list[ScenarioMarkerLiteral] = []

    for match in matches:
        scenario_id = validate_scenario_id(
            match.group("scenario"),
            field="marker scenario ID",
        )
        section_id = validate_section_id(
            match.group("section"),
            field="marker section ID",
        )
        phase = ScenarioMarkerPhase(match.group("phase"))
        column = match.start() + 1

        marker = ScenarioMarkerLiteral(
            phase=phase,
            scenario_id=scenario_id,
            section_id=section_id,
            line=line_number,
            column=column,
            literal=match.group(0),
        )
        markers.append(marker)

        if scenario_id != expected_scenario_id:
            issues.append(
                ScenarioScriptIssue(
                    severity=ScenarioScriptIssueSeverity.ERROR,
                    code=ScenarioScriptIssueCode.WRONG_SCENARIO_MARKER,
                    message=(
                        f"marker scenario ID {scenario_id!r} does not "
                        f"match registered ID {expected_scenario_id!r}"
                    ),
                    line=line_number,
                    column=column,
                    excerpt=_bounded_excerpt(code_text),
                )
            )

    reserved_positions = [
        match.start()
        for match in re.finditer(
            re.escape(_RESERVED_MARKER_PREFIX),
            code_text,
        )
    ]
    covered_positions = {
        position
        for match in matches
        for position in range(match.start(), match.end())
    }

    for position in reserved_positions:
        if position in covered_positions:
            continue
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.MALFORMED_RESERVED_MARKER,
                message="scenario contains a malformed reserved marker",
                line=line_number,
                column=position + 1,
                excerpt=_bounded_excerpt(code_text),
            )
        )

    return tuple(markers)


def _advance_marker_state(
    markers: Iterable[ScenarioMarkerLiteral],
    state: _MarkerState,
    issues: list[ScenarioScriptIssue],
) -> None:
    for marker in markers:
        section_id = marker.section_id

        if marker.phase is ScenarioMarkerPhase.BEGIN:
            if state.open_section is not None:
                issues.append(
                    ScenarioScriptIssue(
                        severity=ScenarioScriptIssueSeverity.ERROR,
                        code=ScenarioScriptIssueCode.NESTED_BEGIN_MARKER,
                        message=(
                            f"section {section_id!r} begins while "
                            f"{state.open_section!r} is still open"
                        ),
                        line=marker.line,
                        column=marker.column,
                        excerpt=marker.literal,
                    )
                )

            if section_id in state.begun:
                issues.append(
                    ScenarioScriptIssue(
                        severity=ScenarioScriptIssueSeverity.ERROR,
                        code=ScenarioScriptIssueCode.DUPLICATE_BEGIN_MARKER,
                        message=(
                            f"section {section_id!r} has more than one "
                            "begin marker"
                        ),
                        line=marker.line,
                        column=marker.column,
                        excerpt=marker.literal,
                    )
                )

            state.begun.add(section_id)
            if state.open_section is None:
                state.open_section = section_id
            continue

        if section_id in state.ended:
            issues.append(
                ScenarioScriptIssue(
                    severity=ScenarioScriptIssueSeverity.ERROR,
                    code=ScenarioScriptIssueCode.DUPLICATE_END_MARKER,
                    message=(
                        f"section {section_id!r} has more than one "
                        "end marker"
                    ),
                    line=marker.line,
                    column=marker.column,
                    excerpt=marker.literal,
                )
            )

        if state.open_section is None:
            issues.append(
                ScenarioScriptIssue(
                    severity=ScenarioScriptIssueSeverity.ERROR,
                    code=ScenarioScriptIssueCode.END_WITHOUT_BEGIN,
                    message=(
                        f"section {section_id!r} ends without "
                        "an open begin marker"
                    ),
                    line=marker.line,
                    column=marker.column,
                    excerpt=marker.literal,
                )
            )
        elif state.open_section != section_id:
            issues.append(
                ScenarioScriptIssue(
                    severity=ScenarioScriptIssueSeverity.ERROR,
                    code=ScenarioScriptIssueCode.MISMATCHED_END_MARKER,
                    message=(
                        f"section {section_id!r} ends while "
                        f"{state.open_section!r} is open"
                    ),
                    line=marker.line,
                    column=marker.column,
                    excerpt=marker.literal,
                )
            )
        else:
            state.open_section = None
            if section_id not in state.completed:
                state.completed.append(section_id)

        state.ended.add(section_id)


def _inspect_security(
    command: str,
    *,
    line_number: int,
    policy: ScenarioParserPolicy,
    issues: list[ScenarioScriptIssue],
) -> None:
    if policy.reject_shell_escape and _contains_shell_escape(command):
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.PROHIBITED_SHELL_ESCAPE,
                message=(
                    "scenario contains a prohibited operating-system "
                    "shell or pipe construct"
                ),
                line=line_number,
                column=_first_non_space_column(command),
                excerpt=_bounded_excerpt(command),
            )
        )

    if (
        policy.reject_machine_absolute_paths
        and (
            _WINDOWS_ABSOLUTE_PATH_RE.search(command)
            or _POSIX_MACHINE_PATH_RE.search(command)
        )
    ):
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.MACHINE_LOCAL_ABSOLUTE_PATH,
                message=(
                    "scenario contains a machine-local absolute path"
                ),
                line=line_number,
                column=_first_machine_path_column(command),
                excerpt=_bounded_excerpt(command),
            )
        )

    if (
        policy.reject_environment_references
        and _ENVIRONMENT_REFERENCE_RE.search(command)
    ):
        match = _ENVIRONMENT_REFERENCE_RE.search(command)
        assert match is not None
        issues.append(
            ScenarioScriptIssue(
                severity=ScenarioScriptIssueSeverity.ERROR,
                code=ScenarioScriptIssueCode.ENVIRONMENT_REFERENCE,
                message=(
                    "scenario contains an environment-variable reference"
                ),
                line=line_number,
                column=match.start() + 1,
                excerpt=_bounded_excerpt(command),
            )
        )


def _inspect_generation_bound(
    command: str,
    *,
    command_name: str | None,
    line_number: int,
    policy: ScenarioParserPolicy,
    issues: list[ScenarioScriptIssue],
) -> None:
    if (
        not policy.require_generation_bound
        or policy.timeout_is_generation_bound
        or command_name is None
        or command_name.casefold() not in _GENERATION_COMMAND_NAMES
    ):
        return

    if _GENERATION_BOUND_RE.search(command):
        return

    issues.append(
        ScenarioScriptIssue(
            severity=ScenarioScriptIssueSeverity.ERROR,
            code=ScenarioScriptIssueCode.UNBOUNDED_GENERATION,
            message=(
                "generation command has no explicit category, depth, "
                "number, or limit bound"
            ),
            line=line_number,
            column=_first_non_space_column(command),
            excerpt=_bounded_excerpt(command),
        )
    )


def _contains_shell_escape(command: str) -> bool:
    stripped = command.lstrip()
    if stripped.startswith("!"):
        return True

    command_name = _command_name(stripped)
    if (
        command_name is not None
        and command_name.casefold() in _PROHIBITED_COMMAND_NAMES
    ):
        return True

    in_string = False
    escaped = False
    index = 0

    while index < len(command):
        char = command[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue

        if char == "`" or char == "|":
            return True

        if char == "$" and index + 1 < len(command):
            if command[index + 1] == "(":
                return True

        index += 1

    return False


def _strip_comments(
    line: str,
    block_depth: int,
) -> tuple[str, int, bool]:
    output: list[str] = []
    in_string = False
    escaped = False
    had_comment = block_depth > 0
    index = 0

    while index < len(line):
        if block_depth:
            had_comment = True
            if line.startswith("{-", index):
                block_depth += 1
                index += 2
                continue
            if line.startswith("-}", index):
                block_depth -= 1
                index += 2
                continue
            index += 1
            continue

        char = line[index]

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue

        if line.startswith("--", index):
            had_comment = True
            break

        if line.startswith("{-", index):
            had_comment = True
            block_depth = 1
            index += 2
            continue

        output.append(char)
        index += 1

    return "".join(output), block_depth, had_comment


def _command_name(command: str) -> str | None:
    stripped = command.lstrip()
    if not stripped:
        return None

    end = 0
    while end < len(stripped):
        char = stripped[end]
        if char.isspace() or char in {'"', "'", "(", ")", "[", "]", "{", "}"}:
            break
        end += 1

    if end == 0:
        return stripped[0]
    return stripped[:end]


def _format_issue(issue: ScenarioScriptIssue) -> str:
    location = ""
    if issue.line is not None:
        location = f"line {issue.line}"
        if issue.column is not None:
            location += f", column {issue.column}"
        location += ": "
    return f"{location}{issue.code.value}: {issue.message}"


def _line_column(text: str, index: int) -> tuple[int, int]:
    prefix = text[:index]
    line = prefix.count("\n") + 1
    last_newline = prefix.rfind("\n")
    column = index + 1 if last_newline < 0 else index - last_newline
    return line, column


def _line_excerpt(text: str, line: int) -> str:
    lines = text.splitlines()
    if line < 1 or line > len(lines):
        return ""
    return _bounded_excerpt(lines[line - 1])


def _last_line_excerpt(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    return _bounded_excerpt(lines[-1])


def _bounded_excerpt(value: str, limit: int = 240) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _bounded_hex_excerpt(
    data: bytes,
    index: int,
    radius: int = 12,
) -> str:
    start = max(0, index - radius)
    end = min(len(data), index + radius)
    return data[start:end].hex(" ")


def _physical_line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _first_non_space_column(value: str) -> int:
    return len(value) - len(value.lstrip()) + 1


def _first_machine_path_column(value: str) -> int:
    matches = [
        match
        for pattern in (
            _WINDOWS_ABSOLUTE_PATH_RE,
            _POSIX_MACHINE_PATH_RE,
        )
        if (match := pattern.search(value)) is not None
    ]
    if not matches:
        return _first_non_space_column(value)
    return min(match.start() for match in matches) + 1

def _require_non_negative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _require_optional_positive_int(
    name: str,
    value: object,
) -> int | None:
    if value is None:
        return None
    return _require_positive_int(name, value)


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _require_non_empty_text(name: str, value: object) -> str:
    text = _require_text(name, value)
    if not text.strip():
        raise ValueError(f"{name} must not be empty")
    return text


def _require_tuple_members(
    name: str,
    values: object,
    expected: type[object],
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    for index, value in enumerate(values):
        if not isinstance(value, expected):
            raise TypeError(
                f"{name}[{index}] must be {expected.__name__}"
            )


__all__ = (
    "DEFAULT_SCENARIO_MAX_BYTES",
    "DEFAULT_SCENARIO_MAX_LINE_CHARS",
    "DEFAULT_SCENARIO_PARSER_POLICY",
    "ParsedScenarioScript",
    "ScenarioMarkerLiteral",
    "ScenarioMarkerPhase",
    "ScenarioParserPolicy",
    "ScenarioScriptIssue",
    "ScenarioScriptIssueCode",
    "ScenarioScriptIssueSeverity",
    "ScenarioScriptLine",
    "ScenarioScriptLineKind",
    "ScenarioScriptParseError",
    "parse_scenario_bytes",
    "parse_scenario_file",
    "parse_scenario_text",
    "validate_scenario_file",
    "validate_scenario_text",
)
