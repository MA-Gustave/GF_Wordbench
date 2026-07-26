"""Scenario marker parsing and section validation for GF Wordbench."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Iterable, Sequence

from gf_wordbench.kernel.ids import SectionId, validate_section_id

from .models import ScenarioSectionResult

BEGIN_MARKER_PREFIX: Final[str] = "GF_WORDBENCH_BEGIN"
END_MARKER_PREFIX: Final[str] = "GF_WORDBENCH_END"

_MARKER_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[ \t]*GF_WORDBENCH_(?P<kind>BEGIN|END)"
    r"[ \t]+(?P<section>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)[ \t]*$"
)
_MARKER_PREFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"^[ \t]*GF_WORDBENCH_[A-Z_]*"
)


@unique
class MarkerKind(StrEnum):
    BEGIN = "begin"
    END = "end"


@unique
class MarkerState(StrEnum):
    NOT_SEEN = "not_seen"
    OPEN = "open"
    COMPLETED = "completed"


@unique
class UnexpectedMarkerPolicy(StrEnum):
    WARN = "warn"
    FAIL = "fail"


@unique
class MarkerIssueSeverity(StrEnum):
    WARNING = "warning"
    FAILURE = "failure"


@unique
class MarkerIssueKind(StrEnum):
    MALFORMED_MARKER = "malformed_marker"
    UNEXPECTED_MARKER = "unexpected_marker"
    OUT_OF_ORDER_SECTION = "out_of_order_section"
    NESTED_SECTION = "nested_section"
    END_OUT_OF_ORDER = "end_out_of_order"
    END_BEFORE_BEGIN = "end_before_begin"
    DUPLICATE_BEGIN = "duplicate_begin"
    BEGIN_AFTER_COMPLETED = "begin_after_completed"
    DUPLICATE_END = "duplicate_end"
    MISSING_BEGIN = "missing_begin"
    MISSING_END = "missing_end"


@dataclass(frozen=True, slots=True)
class MarkerEvent:
    kind: MarkerKind
    section_id: SectionId
    line_number: int
    raw_line: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MarkerKind):
            raise TypeError("kind must be a MarkerKind")
        object.__setattr__(
            self,
            "section_id",
            validate_section_id(self.section_id, field="marker section ID"),
        )
        if type(self.line_number) is not int or self.line_number <= 0:
            raise ValueError("line_number must be a positive integer")
        if not isinstance(self.raw_line, str):
            raise TypeError("raw_line must be a string")


@dataclass(frozen=True, slots=True)
class MalformedMarker:
    line_number: int
    raw_line: str
    message: str

    def __post_init__(self) -> None:
        if type(self.line_number) is not int or self.line_number <= 0:
            raise ValueError("line_number must be a positive integer")
        if not isinstance(self.raw_line, str):
            raise TypeError("raw_line must be a string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")


@dataclass(frozen=True, slots=True)
class MarkerParseResult:
    events: tuple[MarkerEvent, ...]
    malformed: tuple[MalformedMarker, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "malformed", tuple(self.malformed))

        if any(
            left.line_number > right.line_number
            for left, right in zip(self.events, self.events[1:])
        ):
            raise ValueError("marker events must preserve source order")

        if any(
            left.line_number > right.line_number
            for left, right in zip(self.malformed, self.malformed[1:])
        ):
            raise ValueError("malformed markers must preserve source order")


@dataclass(frozen=True, slots=True)
class MarkerIssue:
    kind: MarkerIssueKind
    severity: MarkerIssueSeverity
    message: str
    section_id: SectionId | None = None
    line_number: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MarkerIssueKind):
            raise TypeError("kind must be a MarkerIssueKind")
        if not isinstance(self.severity, MarkerIssueSeverity):
            raise TypeError("severity must be a MarkerIssueSeverity")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")
        if self.section_id is not None:
            object.__setattr__(
                self,
                "section_id",
                validate_section_id(
                    self.section_id,
                    field="marker issue section ID",
                ),
            )
        if self.line_number is not None:
            if type(self.line_number) is not int or self.line_number <= 0:
                raise ValueError(
                    "line_number must be a positive integer when present"
                )


@dataclass(frozen=True, slots=True)
class MarkerValidationResult:
    expected_section_ids: tuple[SectionId, ...]
    events: tuple[MarkerEvent, ...]
    sections: tuple[ScenarioSectionResult, ...]
    issues: tuple[MarkerIssue, ...]
    raw_output_path: Path | None = None

    def __post_init__(self) -> None:
        expected = _normalize_expected_sections(self.expected_section_ids)
        object.__setattr__(self, "expected_section_ids", expected)
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "issues", tuple(self.issues))

        if self.raw_output_path is not None:
            object.__setattr__(
                self,
                "raw_output_path",
                Path(self.raw_output_path),
            )

        section_ids = tuple(
            validate_section_id(item.id, field="section result ID")
            for item in self.sections
        )
        if section_ids != expected:
            raise ValueError(
                "section results must match expected section order exactly"
            )

    @property
    def valid(self) -> bool:
        return not any(
            issue.severity is MarkerIssueSeverity.FAILURE
            for issue in self.issues
        )

    @property
    def complete(self) -> bool:
        return all(section.completed for section in self.sections)

    @property
    def warnings(self) -> tuple[MarkerIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is MarkerIssueSeverity.WARNING
        )

    @property
    def failures(self) -> tuple[MarkerIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is MarkerIssueSeverity.FAILURE
        )

    @property
    def completed_section_ids(self) -> tuple[SectionId, ...]:
        return tuple(
            validate_section_id(section.id, field="completed section ID")
            for section in self.sections
            if section.completed
        )


def format_begin_marker(section_id: str) -> str:
    section = validate_section_id(section_id)
    return f"{BEGIN_MARKER_PREFIX} {section}"


def format_end_marker(section_id: str) -> str:
    section = validate_section_id(section_id)
    return f"{END_MARKER_PREFIX} {section}"


def parse_marker_events(output: str) -> MarkerParseResult:
    if not isinstance(output, str):
        raise TypeError("output must be a string")

    events: list[MarkerEvent] = []
    malformed: list[MalformedMarker] = []

    for line_number, raw_line in enumerate(output.splitlines(), start=1):
        match = _MARKER_LINE_RE.fullmatch(raw_line)
        if match is not None:
            kind = (
                MarkerKind.BEGIN
                if match.group("kind") == "BEGIN"
                else MarkerKind.END
            )
            events.append(
                MarkerEvent(
                    kind=kind,
                    section_id=validate_section_id(
                        match.group("section"),
                        field="marker section ID",
                    ),
                    line_number=line_number,
                    raw_line=raw_line,
                )
            )
            continue

        if _MARKER_PREFIX_RE.match(raw_line) is not None:
            malformed.append(
                MalformedMarker(
                    line_number=line_number,
                    raw_line=raw_line,
                    message=(
                        "marker line must be exactly "
                        "'GF_WORDBENCH_BEGIN <section-id>' or "
                        "'GF_WORDBENCH_END <section-id>'"
                    ),
                )
            )

    return MarkerParseResult(
        events=tuple(events),
        malformed=tuple(malformed),
    )


def validate_marker_events(
    events: Iterable[MarkerEvent],
    expected_section_ids: Sequence[str],
    *,
    malformed: Iterable[MalformedMarker] = (),
    unexpected_policy: UnexpectedMarkerPolicy = UnexpectedMarkerPolicy.FAIL,
    allow_nested: bool = False,
    raw_output_path: Path | None = None,
) -> MarkerValidationResult:
    expected = _normalize_expected_sections(expected_section_ids)
    normalized_events = _normalize_events(events)
    normalized_malformed = _normalize_malformed(malformed)

    if not isinstance(unexpected_policy, UnexpectedMarkerPolicy):
        raise TypeError(
            "unexpected_policy must be an UnexpectedMarkerPolicy"
        )
    if type(allow_nested) is not bool:
        raise TypeError("allow_nested must be a bool")

    states = {
        section_id: MarkerState.NOT_SEEN
        for section_id in expected
    }
    begin_lines: dict[SectionId, int | None] = {
        section_id: None
        for section_id in expected
    }
    end_lines: dict[SectionId, int | None] = {
        section_id: None
        for section_id in expected
    }
    section_issues: dict[SectionId, list[MarkerIssue]] = {
        section_id: []
        for section_id in expected
    }
    issues: list[MarkerIssue] = []
    open_stack: list[SectionId] = []
    next_expected_index = 0
    expected_indexes = {
        section_id: index
        for index, section_id in enumerate(expected)
    }

    for item in normalized_malformed:
        issues.append(
            MarkerIssue(
                kind=MarkerIssueKind.MALFORMED_MARKER,
                severity=MarkerIssueSeverity.FAILURE,
                message=item.message,
                line_number=item.line_number,
            )
        )

    for event in normalized_events:
        section_id = event.section_id

        if section_id not in states:
            issue = MarkerIssue(
                kind=MarkerIssueKind.UNEXPECTED_MARKER,
                severity=(
                    MarkerIssueSeverity.WARNING
                    if unexpected_policy is UnexpectedMarkerPolicy.WARN
                    else MarkerIssueSeverity.FAILURE
                ),
                message=(
                    f"unexpected {event.kind.value} marker for section "
                    f"{section_id!r}"
                ),
                section_id=section_id,
                line_number=event.line_number,
            )
            issues.append(issue)
            continue

        state = states[section_id]

        if event.kind is MarkerKind.BEGIN:
            if state is MarkerState.NOT_SEEN:
                section_index = expected_indexes[section_id]
                if section_index != next_expected_index:
                    issue = MarkerIssue(
                        kind=MarkerIssueKind.OUT_OF_ORDER_SECTION,
                        severity=MarkerIssueSeverity.FAILURE,
                        message=(
                            f"section {section_id!r} began out of configured "
                            "order"
                        ),
                        section_id=section_id,
                        line_number=event.line_number,
                    )
                    issues.append(issue)
                    section_issues[section_id].append(issue)

                if open_stack and not allow_nested:
                    issue = MarkerIssue(
                        kind=MarkerIssueKind.NESTED_SECTION,
                        severity=MarkerIssueSeverity.FAILURE,
                        message=(
                            f"section {section_id!r} began before section "
                            f"{open_stack[-1]!r} ended"
                        ),
                        section_id=section_id,
                        line_number=event.line_number,
                    )
                    issues.append(issue)
                    section_issues[section_id].append(issue)

                states[section_id] = MarkerState.OPEN
                begin_lines[section_id] = event.line_number
                open_stack.append(section_id)

                while (
                    next_expected_index < len(expected)
                    and states[expected[next_expected_index]]
                    is not MarkerState.NOT_SEEN
                ):
                    next_expected_index += 1
                continue

            if state is MarkerState.OPEN:
                issue = MarkerIssue(
                    kind=MarkerIssueKind.DUPLICATE_BEGIN,
                    severity=MarkerIssueSeverity.FAILURE,
                    message=(
                        f"section {section_id!r} has a duplicate begin marker"
                    ),
                    section_id=section_id,
                    line_number=event.line_number,
                )
            else:
                issue = MarkerIssue(
                    kind=MarkerIssueKind.BEGIN_AFTER_COMPLETED,
                    severity=MarkerIssueSeverity.FAILURE,
                    message=(
                        f"section {section_id!r} began again after completion"
                    ),
                    section_id=section_id,
                    line_number=event.line_number,
                )
            issues.append(issue)
            section_issues[section_id].append(issue)
            continue

        if state is MarkerState.NOT_SEEN:
            issue = MarkerIssue(
                kind=MarkerIssueKind.END_BEFORE_BEGIN,
                severity=MarkerIssueSeverity.FAILURE,
                message=(
                    f"section {section_id!r} ended before its begin marker"
                ),
                section_id=section_id,
                line_number=event.line_number,
            )
            issues.append(issue)
            section_issues[section_id].append(issue)
            continue

        if state is MarkerState.COMPLETED:
            issue = MarkerIssue(
                kind=MarkerIssueKind.DUPLICATE_END,
                severity=MarkerIssueSeverity.FAILURE,
                message=(
                    f"section {section_id!r} has a duplicate end marker"
                ),
                section_id=section_id,
                line_number=event.line_number,
            )
            issues.append(issue)
            section_issues[section_id].append(issue)
            continue

        if open_stack and open_stack[-1] != section_id:
            issue = MarkerIssue(
                kind=MarkerIssueKind.END_OUT_OF_ORDER,
                severity=MarkerIssueSeverity.FAILURE,
                message=(
                    f"section {section_id!r} ended while section "
                    f"{open_stack[-1]!r} was the active section"
                ),
                section_id=section_id,
                line_number=event.line_number,
            )
            issues.append(issue)
            section_issues[section_id].append(issue)
            open_stack.remove(section_id)
        elif open_stack:
            open_stack.pop()

        states[section_id] = MarkerState.COMPLETED
        end_lines[section_id] = event.line_number

    for section_id in expected:
        state = states[section_id]
        if state is MarkerState.NOT_SEEN:
            begin_issue = MarkerIssue(
                kind=MarkerIssueKind.MISSING_BEGIN,
                severity=MarkerIssueSeverity.FAILURE,
                message=f"section {section_id!r} has no begin marker",
                section_id=section_id,
            )
            end_issue = MarkerIssue(
                kind=MarkerIssueKind.MISSING_END,
                severity=MarkerIssueSeverity.FAILURE,
                message=f"section {section_id!r} has no end marker",
                section_id=section_id,
            )
            issues.extend((begin_issue, end_issue))
            section_issues[section_id].extend((begin_issue, end_issue))
        elif state is MarkerState.OPEN:
            issue = MarkerIssue(
                kind=MarkerIssueKind.MISSING_END,
                severity=MarkerIssueSeverity.FAILURE,
                message=f"section {section_id!r} has no end marker",
                section_id=section_id,
            )
            issues.append(issue)
            section_issues[section_id].append(issue)

    sections = tuple(
        _build_section_result(
            section_id=section_id,
            state=states[section_id],
            begin_line=begin_lines[section_id],
            end_line=end_lines[section_id],
            issues=section_issues[section_id],
        )
        for section_id in expected
    )

    return MarkerValidationResult(
        expected_section_ids=expected,
        events=normalized_events,
        sections=sections,
        issues=tuple(issues),
        raw_output_path=raw_output_path,
    )


def validate_scenario_markers(
    output: str,
    expected_section_ids: Sequence[str],
    *,
    unexpected_policy: UnexpectedMarkerPolicy = UnexpectedMarkerPolicy.FAIL,
    allow_nested: bool = False,
    raw_output_path: Path | None = None,
) -> MarkerValidationResult:
    parsed = parse_marker_events(output)
    return validate_marker_events(
        parsed.events,
        expected_section_ids,
        malformed=parsed.malformed,
        unexpected_policy=unexpected_policy,
        allow_nested=allow_nested,
        raw_output_path=raw_output_path,
    )


def _normalize_expected_sections(
    section_ids: Iterable[str],
) -> tuple[SectionId, ...]:
    if isinstance(section_ids, (str, bytes)):
        raise TypeError(
            "expected_section_ids must be an iterable of section IDs"
        )

    try:
        normalized = tuple(
            validate_section_id(
                section_id,
                field=f"expected_section_ids[{index}]",
            )
            for index, section_id in enumerate(section_ids)
        )
    except TypeError as exc:
        raise TypeError(
            "expected_section_ids must be an iterable of section IDs"
        ) from exc

    if len(normalized) != len(set(normalized)):
        raise ValueError("expected section IDs must be unique")

    return normalized


def _normalize_events(
    events: Iterable[MarkerEvent],
) -> tuple[MarkerEvent, ...]:
    if isinstance(events, (str, bytes)):
        raise TypeError("events must be an iterable of MarkerEvent values")

    try:
        normalized = tuple(events)
    except TypeError as exc:
        raise TypeError(
            "events must be an iterable of MarkerEvent values"
        ) from exc

    if not all(isinstance(event, MarkerEvent) for event in normalized):
        raise TypeError("events must contain only MarkerEvent values")

    if any(
        left.line_number > right.line_number
        for left, right in zip(normalized, normalized[1:])
    ):
        raise ValueError("events must preserve source line order")

    return normalized


def _normalize_malformed(
    malformed: Iterable[MalformedMarker],
) -> tuple[MalformedMarker, ...]:
    if isinstance(malformed, (str, bytes)):
        raise TypeError(
            "malformed must be an iterable of MalformedMarker values"
        )

    try:
        normalized = tuple(malformed)
    except TypeError as exc:
        raise TypeError(
            "malformed must be an iterable of MalformedMarker values"
        ) from exc

    if not all(
        isinstance(item, MalformedMarker)
        for item in normalized
    ):
        raise TypeError(
            "malformed must contain only MalformedMarker values"
        )

    return normalized


def _build_section_result(
    *,
    section_id: SectionId,
    state: MarkerState,
    begin_line: int | None,
    end_line: int | None,
    issues: Sequence[MarkerIssue],
) -> ScenarioSectionResult:
    has_failure = any(
        issue.severity is MarkerIssueSeverity.FAILURE
        for issue in issues
    )
    completed = state is MarkerState.COMPLETED and not has_failure

    if completed:
        message = "section completed"
    elif issues:
        message = issues[0].message
    elif state is MarkerState.OPEN:
        message = "section began but did not complete"
    else:
        message = "section did not complete"

    return ScenarioSectionResult(
        id=str(section_id),
        completed=completed,
        message=message,
        begin_line=begin_line,
        end_line=end_line,
    )


__all__ = (
    "BEGIN_MARKER_PREFIX",
    "END_MARKER_PREFIX",
    "MalformedMarker",
    "MarkerEvent",
    "MarkerIssue",
    "MarkerIssueKind",
    "MarkerIssueSeverity",
    "MarkerKind",
    "MarkerParseResult",
    "MarkerState",
    "MarkerValidationResult",
    "UnexpectedMarkerPolicy",
    "format_begin_marker",
    "format_end_marker",
    "parse_marker_events",
    "validate_marker_events",
    "validate_scenario_markers",
)
