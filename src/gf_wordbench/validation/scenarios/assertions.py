"""Bounded deterministic scenario-assertion evaluation for GF Wordbench."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, TypeVar, overload

from gf_wordbench.kernel.statuses import ValidationStatus

_ASSERTION_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SECTION_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_DIAGNOSTIC_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z][A-Za-z0-9]*(?:[-_.][A-Za-z0-9]+)*$"
)
_ARTIFACT_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")
_COUNT_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*$")
_MAX_MESSAGE_LENGTH: Final[int] = 2_000
_MAX_PATTERN_LENGTH: Final[int] = 512
_MAX_TEXT_LENGTH: Final[int] = 8 * 1024 * 1024
_MAX_PARAMETER_ITEMS: Final[int] = 32
_MAX_COLLECTION_ITEMS: Final[int] = 100_000

AssertionParameter: TypeAlias = str | int | bool | tuple[str, ...] | None
AssertionParameters: TypeAlias = Mapping[str, AssertionParameter]
_TypedItemT = TypeVar("_TypedItemT")


@unique
class AssertionStatus(StrEnum):
    """Canonical outcome of one scenario assertion."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@unique
class AssertionCategory(StrEnum):
    """Canonical bounded scenario-assertion families."""

    PROCESS = "process"
    SECTION = "section"
    DIAGNOSTIC = "diagnostic"
    TEXT = "text"
    COUNT = "count"
    ARTIFACT = "artifact"
    GOLD = "gold"


@unique
class AssertionKind(StrEnum):
    """Stable built-in assertion type identifiers."""

    PROCESS_COMPLETED = "process-completed"
    EXIT_CODE_EQUALS = "exit-code-equals"
    NOT_TIMED_OUT = "not-timed-out"
    NOT_CANCELLED = "not-cancelled"
    OUTPUT_LIMIT_NOT_EXCEEDED = "output-limit-not-exceeded"
    CAPTURE_COMPLETED = "capture-completed"
    SECTION_EXISTS = "section-exists"
    SECTION_COMPLETED = "section-completed"
    SECTION_NON_EMPTY = "section-non-empty"
    DIAGNOSTIC_PRESENT = "diagnostic-present"
    DIAGNOSTIC_ABSENT = "diagnostic-absent"
    TEXT_CONTAINS = "text-contains"
    TEXT_EXCLUDES = "text-excludes"
    TEXT_EQUALS = "text-equals"
    TEXT_MATCHES = "text-matches"
    COUNT_COMPARE = "count-compare"
    ARTIFACT_EXISTS = "artifact-exists"
    ARTIFACT_NON_EMPTY = "artifact-non-empty"
    ARTIFACT_CONTAINED = "artifact-contained"
    ARTIFACT_CURRENT = "artifact-current"
    GOLD_MATCHES = "gold-matches"

    @property
    def category(self) -> AssertionCategory:
        return _ASSERTION_CATEGORIES[self]


@unique
class AssertionInputSource(StrEnum):
    """Structured evidence source consumed by an assertion."""

    PROCESS = "process"
    SECTIONS = "sections"
    RAW_STDOUT = "raw-stdout"
    RAW_STDERR = "raw-stderr"
    NORMALIZED_OUTPUT = "normalized-output"
    NORMALIZED_SECTION = "normalized-section"
    DIAGNOSTICS = "diagnostics"
    COUNTS = "counts"
    ARTIFACTS = "artifacts"
    GOLD = "gold"


@unique
class CountComparison(StrEnum):
    """Supported integer-comparison operators."""

    EQUAL = "eq"
    NOT_EQUAL = "ne"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "le"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "ge"


_ASSERTION_CATEGORIES: Final[Mapping[AssertionKind, AssertionCategory]] = MappingProxyType(
    {
        AssertionKind.PROCESS_COMPLETED: AssertionCategory.PROCESS,
        AssertionKind.EXIT_CODE_EQUALS: AssertionCategory.PROCESS,
        AssertionKind.NOT_TIMED_OUT: AssertionCategory.PROCESS,
        AssertionKind.NOT_CANCELLED: AssertionCategory.PROCESS,
        AssertionKind.OUTPUT_LIMIT_NOT_EXCEEDED: AssertionCategory.PROCESS,
        AssertionKind.CAPTURE_COMPLETED: AssertionCategory.PROCESS,
        AssertionKind.SECTION_EXISTS: AssertionCategory.SECTION,
        AssertionKind.SECTION_COMPLETED: AssertionCategory.SECTION,
        AssertionKind.SECTION_NON_EMPTY: AssertionCategory.SECTION,
        AssertionKind.DIAGNOSTIC_PRESENT: AssertionCategory.DIAGNOSTIC,
        AssertionKind.DIAGNOSTIC_ABSENT: AssertionCategory.DIAGNOSTIC,
        AssertionKind.TEXT_CONTAINS: AssertionCategory.TEXT,
        AssertionKind.TEXT_EXCLUDES: AssertionCategory.TEXT,
        AssertionKind.TEXT_EQUALS: AssertionCategory.TEXT,
        AssertionKind.TEXT_MATCHES: AssertionCategory.TEXT,
        AssertionKind.COUNT_COMPARE: AssertionCategory.COUNT,
        AssertionKind.ARTIFACT_EXISTS: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_NON_EMPTY: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_CONTAINED: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_CURRENT: AssertionCategory.ARTIFACT,
        AssertionKind.GOLD_MATCHES: AssertionCategory.GOLD,
    }
)

_ALLOWED_SOURCES: Final[Mapping[AssertionKind, frozenset[AssertionInputSource]]] = MappingProxyType(
    {
        AssertionKind.PROCESS_COMPLETED: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.EXIT_CODE_EQUALS: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.NOT_TIMED_OUT: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.NOT_CANCELLED: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.OUTPUT_LIMIT_NOT_EXCEEDED: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.CAPTURE_COMPLETED: frozenset({AssertionInputSource.PROCESS}),
        AssertionKind.SECTION_EXISTS: frozenset({AssertionInputSource.SECTIONS}),
        AssertionKind.SECTION_COMPLETED: frozenset({AssertionInputSource.SECTIONS}),
        AssertionKind.SECTION_NON_EMPTY: frozenset(
            {
                AssertionInputSource.SECTIONS,
                AssertionInputSource.NORMALIZED_SECTION,
            }
        ),
        AssertionKind.DIAGNOSTIC_PRESENT: frozenset({AssertionInputSource.DIAGNOSTICS}),
        AssertionKind.DIAGNOSTIC_ABSENT: frozenset({AssertionInputSource.DIAGNOSTICS}),
        AssertionKind.TEXT_CONTAINS: frozenset(
            {
                AssertionInputSource.RAW_STDOUT,
                AssertionInputSource.RAW_STDERR,
                AssertionInputSource.NORMALIZED_OUTPUT,
                AssertionInputSource.NORMALIZED_SECTION,
            }
        ),
        AssertionKind.TEXT_EXCLUDES: frozenset(
            {
                AssertionInputSource.RAW_STDOUT,
                AssertionInputSource.RAW_STDERR,
                AssertionInputSource.NORMALIZED_OUTPUT,
                AssertionInputSource.NORMALIZED_SECTION,
            }
        ),
        AssertionKind.TEXT_EQUALS: frozenset(
            {
                AssertionInputSource.RAW_STDOUT,
                AssertionInputSource.RAW_STDERR,
                AssertionInputSource.NORMALIZED_OUTPUT,
                AssertionInputSource.NORMALIZED_SECTION,
            }
        ),
        AssertionKind.TEXT_MATCHES: frozenset(
            {
                AssertionInputSource.RAW_STDOUT,
                AssertionInputSource.RAW_STDERR,
                AssertionInputSource.NORMALIZED_OUTPUT,
                AssertionInputSource.NORMALIZED_SECTION,
            }
        ),
        AssertionKind.COUNT_COMPARE: frozenset({AssertionInputSource.COUNTS}),
        AssertionKind.ARTIFACT_EXISTS: frozenset({AssertionInputSource.ARTIFACTS}),
        AssertionKind.ARTIFACT_NON_EMPTY: frozenset({AssertionInputSource.ARTIFACTS}),
        AssertionKind.ARTIFACT_CONTAINED: frozenset({AssertionInputSource.ARTIFACTS}),
        AssertionKind.ARTIFACT_CURRENT: frozenset({AssertionInputSource.ARTIFACTS}),
        AssertionKind.GOLD_MATCHES: frozenset({AssertionInputSource.GOLD}),
    }
)


@dataclass(frozen=True, slots=True)
class ScenarioAssertionSpec:
    """One ordered, explicit, bounded scenario assertion."""

    assertion_id: str
    kind: AssertionKind
    source: AssertionInputSource
    failure_message: str
    required: bool = True
    release_significant: bool = False
    section_id: str | None = None
    parameters: AssertionParameters = field(default_factory=dict)

    def __post_init__(self) -> None:
        assertion_id = _require_identifier(
            self.assertion_id,
            field_name="assertion_id",
            pattern=_ASSERTION_ID_RE,
        )
        if not isinstance(self.kind, AssertionKind):
            raise TypeError("kind must be an AssertionKind")
        if not isinstance(self.source, AssertionInputSource):
            raise TypeError("source must be an AssertionInputSource")
        if self.source not in _ALLOWED_SOURCES[self.kind]:
            allowed = ", ".join(
                source.value
                for source in sorted(
                    _ALLOWED_SOURCES[self.kind],
                    key=lambda item: item.value,
                )
            )
            raise ValueError(
                f"source {self.source.value!r} is invalid for assertion kind "
                f"{self.kind.value!r}; expected one of {allowed}"
            )
        failure_message = _require_text(
            self.failure_message,
            field_name="failure_message",
            allow_empty=False,
            max_length=_MAX_MESSAGE_LENGTH,
        )
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if type(self.release_significant) is not bool:
            raise TypeError("release_significant must be a boolean")
        section_id = self.section_id
        if section_id is not None:
            section_id = _require_identifier(
                section_id,
                field_name="section_id",
                pattern=_SECTION_ID_RE,
            )
        parameters = _freeze_parameters(self.parameters)
        _validate_spec_parameters(
            kind=self.kind,
            source=self.source,
            section_id=section_id,
            parameters=parameters,
        )
        object.__setattr__(self, "assertion_id", assertion_id)
        object.__setattr__(self, "failure_message", failure_message)
        object.__setattr__(self, "section_id", section_id)
        object.__setattr__(self, "parameters", parameters)


@dataclass(frozen=True, slots=True)
class ProcessAssertionEvidence:
    """Structured process facts available to process assertions."""

    completed: bool
    exit_code: int | None
    timed_out: bool
    cancelled: bool
    output_limit_exceeded: bool
    capture_completed: bool
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        for name in (
            "completed",
            "timed_out",
            "cancelled",
            "output_limit_exceeded",
            "capture_completed",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise TypeError("exit_code must be an integer or None")
        if self.completed and (self.timed_out or self.cancelled):
            raise ValueError("completed cannot be true when timed_out or cancelled is true")
        object.__setattr__(
            self,
            "evidence_path",
            _coerce_optional_path(self.evidence_path, field_name="evidence_path"),
        )


@dataclass(frozen=True, slots=True)
class SectionAssertionEvidence:
    """Marker-parser output for one declared scenario section."""

    section_id: str
    completed: bool
    text: str = ""
    begin_line: int | None = None
    end_line: int | None = None
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        section_id = _require_identifier(
            self.section_id,
            field_name="section_id",
            pattern=_SECTION_ID_RE,
        )
        if type(self.completed) is not bool:
            raise TypeError("completed must be a boolean")
        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            max_length=_MAX_TEXT_LENGTH,
        )
        _validate_optional_positive_int(self.begin_line, field_name="begin_line")
        _validate_optional_positive_int(self.end_line, field_name="end_line")
        if self.end_line is not None and self.begin_line is None:
            raise ValueError("end_line requires begin_line")
        if (
            self.begin_line is not None
            and self.end_line is not None
            and self.end_line < self.begin_line
        ):
            raise ValueError("end_line must not precede begin_line")
        if self.completed and self.end_line is None:
            raise ValueError("a completed section must have an end_line")
        object.__setattr__(self, "section_id", section_id)
        object.__setattr__(self, "text", text)
        object.__setattr__(
            self,
            "evidence_path",
            _coerce_optional_path(self.evidence_path, field_name="evidence_path"),
        )


@dataclass(frozen=True, slots=True)
class DiagnosticAssertionEvidence:
    """One structured diagnostic available to assertion evaluation."""

    diagnostic_id: str
    kind: str
    message: str
    fatal: bool
    section_id: str | None = None
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        diagnostic_id = _require_identifier(
            self.diagnostic_id,
            field_name="diagnostic_id",
            pattern=_DIAGNOSTIC_ID_RE,
        )
        kind = _require_text(
            self.kind,
            field_name="kind",
            allow_empty=False,
            max_length=128,
        )
        message = _require_text(
            self.message,
            field_name="message",
            allow_empty=False,
            max_length=_MAX_MESSAGE_LENGTH,
        )
        if type(self.fatal) is not bool:
            raise TypeError("fatal must be a boolean")
        section_id = self.section_id
        if section_id is not None:
            section_id = _require_identifier(
                section_id,
                field_name="section_id",
                pattern=_SECTION_ID_RE,
            )
        object.__setattr__(self, "diagnostic_id", diagnostic_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "section_id", section_id)
        object.__setattr__(
            self,
            "evidence_path",
            _coerce_optional_path(self.evidence_path, field_name="evidence_path"),
        )


@dataclass(frozen=True, slots=True)
class ArtifactAssertionEvidence:
    """Observed state of one declared scenario artifact."""

    artifact_id: str
    path: Path
    exists: bool
    size_bytes: int | None
    contained: bool
    current: bool | None = None
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        artifact_id = _require_identifier(
            self.artifact_id,
            field_name="artifact_id",
            pattern=_ARTIFACT_ID_RE,
        )
        path = _coerce_path(self.path, field_name="path")
        if type(self.exists) is not bool:
            raise TypeError("exists must be a boolean")
        if self.size_bytes is not None:
            if type(self.size_bytes) is not int:
                raise TypeError("size_bytes must be an integer or None")
            if self.size_bytes < 0:
                raise ValueError("size_bytes must be non-negative")
        if not self.exists and self.size_bytes not in (None, 0):
            raise ValueError("a missing artifact cannot have a positive size")
        if type(self.contained) is not bool:
            raise TypeError("contained must be a boolean")
        if self.current is not None and type(self.current) is not bool:
            raise TypeError("current must be a boolean or None")
        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "path", path)
        object.__setattr__(
            self,
            "evidence_path",
            _coerce_optional_path(self.evidence_path, field_name="evidence_path"),
        )


@dataclass(frozen=True, slots=True)
class GoldAssertionEvidence:
    """Structured gold-comparison outcome available to assertions."""

    evaluated: bool
    matched: bool | None
    missing_required_gold: bool = False
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        if type(self.evaluated) is not bool:
            raise TypeError("evaluated must be a boolean")
        if self.matched is not None and type(self.matched) is not bool:
            raise TypeError("matched must be a boolean or None")
        if type(self.missing_required_gold) is not bool:
            raise TypeError("missing_required_gold must be a boolean")
        if not self.evaluated and self.matched is not None:
            raise ValueError("matched must be None when gold was not evaluated")
        if self.missing_required_gold and self.matched is not None:
            raise ValueError("missing required gold cannot have a match result")
        object.__setattr__(
            self,
            "evidence_path",
            _coerce_optional_path(self.evidence_path, field_name="evidence_path"),
        )


@dataclass(frozen=True, slots=True)
class AssertionEvaluationContext:
    """Immutable structured evidence consumed by scenario assertions."""

    process: ProcessAssertionEvidence
    sections: Mapping[str, SectionAssertionEvidence] = field(default_factory=dict)
    raw_stdout: str = ""
    raw_stderr: str = ""
    normalized_output: str | None = None
    normalized_sections: Mapping[str, str] = field(default_factory=dict)
    diagnostics: tuple[DiagnosticAssertionEvidence, ...] = ()
    counts: Mapping[str, int] = field(default_factory=dict)
    artifacts: Mapping[str, ArtifactAssertionEvidence] = field(default_factory=dict)
    gold: GoldAssertionEvidence | None = None
    run_root: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.process, ProcessAssertionEvidence):
            raise TypeError("process must be ProcessAssertionEvidence")
        sections = _freeze_sections(self.sections)
        raw_stdout = _require_text(
            self.raw_stdout,
            field_name="raw_stdout",
            allow_empty=True,
            max_length=_MAX_TEXT_LENGTH,
        )
        raw_stderr = _require_text(
            self.raw_stderr,
            field_name="raw_stderr",
            allow_empty=True,
            max_length=_MAX_TEXT_LENGTH,
        )
        normalized_output = self.normalized_output
        if normalized_output is not None:
            normalized_output = _require_text(
                normalized_output,
                field_name="normalized_output",
                allow_empty=True,
                max_length=_MAX_TEXT_LENGTH,
            )
        normalized_sections = _freeze_text_mapping(
            self.normalized_sections,
            field_name="normalized_sections",
            key_pattern=_SECTION_ID_RE,
        )
        diagnostics = _freeze_typed_tuple(
            self.diagnostics,
            item_type=DiagnosticAssertionEvidence,
            field_name="diagnostics",
        )
        counts = _freeze_counts(self.counts)
        artifacts = _freeze_artifacts(self.artifacts)
        if self.gold is not None and not isinstance(self.gold, GoldAssertionEvidence):
            raise TypeError("gold must be GoldAssertionEvidence or None")
        run_root = self.run_root
        if run_root is not None:
            run_root = _coerce_path(run_root, field_name="run_root")
            if not run_root.is_absolute():
                raise ValueError("run_root must be absolute")
            _validate_evidence_containment(
                run_root=run_root,
                process=self.process,
                sections=sections,
                diagnostics=diagnostics,
                artifacts=artifacts,
                gold=self.gold,
            )
        object.__setattr__(self, "sections", sections)
        object.__setattr__(self, "raw_stdout", raw_stdout)
        object.__setattr__(self, "raw_stderr", raw_stderr)
        object.__setattr__(self, "normalized_output", normalized_output)
        object.__setattr__(self, "normalized_sections", normalized_sections)
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "counts", counts)
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "run_root", run_root)


@dataclass(frozen=True, slots=True)
class ScenarioAssertionResult:
    """Canonical result of one evaluated scenario assertion."""

    assertion_id: str
    assertion_kind: str
    status: AssertionStatus
    message: str
    evidence_path: Path | None
    section_id: str | None

    def __post_init__(self) -> None:
        assertion_id = _require_identifier(
            self.assertion_id,
            field_name="assertion_id",
            pattern=_ASSERTION_ID_RE,
        )
        assertion_kind = _require_text(
            self.assertion_kind,
            field_name="assertion_kind",
            allow_empty=False,
            max_length=128,
        )
        if not isinstance(self.status, AssertionStatus):
            raise TypeError("status must be an AssertionStatus")
        message = _require_text(
            self.message,
            field_name="message",
            allow_empty=False,
            max_length=_MAX_MESSAGE_LENGTH,
        )
        evidence_path = _coerce_optional_path(
            self.evidence_path,
            field_name="evidence_path",
        )
        section_id = self.section_id
        if section_id is not None:
            section_id = _require_identifier(
                section_id,
                field_name="section_id",
                pattern=_SECTION_ID_RE,
            )
        object.__setattr__(self, "assertion_id", assertion_id)
        object.__setattr__(self, "assertion_kind", assertion_kind)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "evidence_path", evidence_path)
        object.__setattr__(self, "section_id", section_id)


@dataclass(frozen=True, slots=True)
class AssertionBatchResult:
    """Ordered assertion results and their scenario-level aggregation."""

    results: tuple[ScenarioAssertionResult, ...]
    scenario_status: ValidationStatus
    warning_assertion_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        results = _freeze_typed_tuple(
            self.results,
            item_type=ScenarioAssertionResult,
            field_name="results",
        )
        if not isinstance(self.scenario_status, ValidationStatus):
            raise TypeError("scenario_status must be ValidationStatus")
        warning_ids = tuple(self.warning_assertion_ids)
        if len(warning_ids) > _MAX_COLLECTION_ITEMS:
            raise ValueError("warning_assertion_ids exceeds the supported limit")
        for assertion_id in warning_ids:
            _require_identifier(
                assertion_id,
                field_name="warning_assertion_ids item",
                pattern=_ASSERTION_ID_RE,
            )
        if len(set(warning_ids)) != len(warning_ids):
            raise ValueError("warning_assertion_ids must not contain duplicates")
        object.__setattr__(self, "results", results)
        object.__setattr__(self, "warning_assertion_ids", warning_ids)


@dataclass(frozen=True, slots=True)
class _Outcome:
    status: AssertionStatus
    message: str
    evidence_path: Path | None = None


class ScenarioAssertionEvaluator:
    """Evaluate built-in scenario assertions from structured evidence."""

    __slots__ = ()

    def evaluate(
        self,
        spec: ScenarioAssertionSpec,
        context: AssertionEvaluationContext,
    ) -> ScenarioAssertionResult:
        if not isinstance(spec, ScenarioAssertionSpec):
            raise TypeError("spec must be ScenarioAssertionSpec")
        if not isinstance(context, AssertionEvaluationContext):
            raise TypeError("context must be AssertionEvaluationContext")
        try:
            outcome = _evaluate_builtin(spec, context)
        except Exception as exc:
            outcome = _Outcome(
                status=AssertionStatus.ERROR,
                message=(f"Assertion could not be evaluated reliably: {_safe_exception_text(exc)}"),
                evidence_path=_default_evidence_path(spec, context),
            )
        return ScenarioAssertionResult(
            assertion_id=spec.assertion_id,
            assertion_kind=spec.kind.value,
            status=outcome.status,
            message=outcome.message,
            evidence_path=outcome.evidence_path,
            section_id=spec.section_id,
        )

    def evaluate_many(
        self,
        specs: Iterable[ScenarioAssertionSpec],
        context: AssertionEvaluationContext,
    ) -> AssertionBatchResult:
        ordered_specs = _prepare_specs(specs)
        results = tuple(self.evaluate(spec, context) for spec in ordered_specs)
        scenario_status, warnings = aggregate_assertion_results(
            ordered_specs,
            results,
        )
        return AssertionBatchResult(
            results=results,
            scenario_status=scenario_status,
            warning_assertion_ids=warnings,
        )


def evaluate_assertion(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> ScenarioAssertionResult:
    """Evaluate one assertion without reading files or reparsing reports."""

    return ScenarioAssertionEvaluator().evaluate(spec, context)


def evaluate_assertion_results(
    specs: Iterable[ScenarioAssertionSpec],
    context: AssertionEvaluationContext,
) -> tuple[ScenarioAssertionResult, ...]:
    """Evaluate assertions in scenario-spec order."""

    return ScenarioAssertionEvaluator().evaluate_many(specs, context).results


def evaluate_assertions(
    specs: Iterable[ScenarioAssertionSpec],
    context: AssertionEvaluationContext,
) -> AssertionBatchResult:
    """Evaluate and aggregate an ordered assertion sequence."""

    return ScenarioAssertionEvaluator().evaluate_many(specs, context)


def aggregate_assertion_results(
    specs: Sequence[ScenarioAssertionSpec],
    results: Sequence[ScenarioAssertionResult],
) -> tuple[ValidationStatus, tuple[str, ...]]:
    """Aggregate required assertions using ERROR, FAIL, then OK precedence."""

    ordered_specs = tuple(specs)
    ordered_results = tuple(results)
    if len(ordered_specs) != len(ordered_results):
        raise ValueError("specs and results must have identical lengths")
    result_by_id: dict[str, ScenarioAssertionResult] = {}
    for assertion_result in ordered_results:
        if not isinstance(assertion_result, ScenarioAssertionResult):
            raise TypeError("results must contain ScenarioAssertionResult objects")
        if assertion_result.assertion_id in result_by_id:
            raise ValueError(
                f"duplicate assertion result ID {assertion_result.assertion_id!r}"
            )
        result_by_id[assertion_result.assertion_id] = assertion_result
    warning_ids: list[str] = []
    required_statuses: list[AssertionStatus] = []
    for spec in ordered_specs:
        if not isinstance(spec, ScenarioAssertionSpec):
            raise TypeError("specs must contain ScenarioAssertionSpec objects")
        result = result_by_id.get(spec.assertion_id)
        if result is None:
            raise ValueError(f"missing result for assertion {spec.assertion_id!r}")
        if result.assertion_kind != spec.kind.value:
            raise ValueError(
                f"result kind for assertion {spec.assertion_id!r} does not match its specification"
            )
        if spec.required:
            required_statuses.append(result.status)
        elif result.status in (AssertionStatus.FAILED, AssertionStatus.ERROR):
            warning_ids.append(spec.assertion_id)
    unexpected = set(result_by_id).difference(spec.assertion_id for spec in ordered_specs)
    if unexpected:
        rendered = ", ".join(sorted(unexpected))
        raise ValueError(f"results contain unknown assertion IDs: {rendered}")
    if AssertionStatus.ERROR in required_statuses:
        return ValidationStatus.ERROR, tuple(warning_ids)
    if AssertionStatus.SKIPPED in required_statuses:
        return ValidationStatus.ERROR, tuple(warning_ids)
    if AssertionStatus.FAILED in required_statuses:
        return ValidationStatus.FAIL, tuple(warning_ids)
    return ValidationStatus.OK, tuple(warning_ids)


def _evaluate_builtin(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> _Outcome:
    kind = spec.kind
    if kind is AssertionKind.PROCESS_COMPLETED:
        return _boolean_outcome(
            spec,
            passed=context.process.completed,
            success_message="Scenario process completed.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.EXIT_CODE_EQUALS:
        expected = _parameter_int(spec, "expected")
        if context.process.exit_code is None:
            return _error_outcome(
                spec,
                "Process exit code is unavailable.",
                context.process.evidence_path,
            )
        return _boolean_outcome(
            spec,
            passed=context.process.exit_code == expected,
            success_message=f"Process exit code equals {expected}.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.NOT_TIMED_OUT:
        return _boolean_outcome(
            spec,
            passed=not context.process.timed_out,
            success_message="Scenario process did not time out.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.NOT_CANCELLED:
        return _boolean_outcome(
            spec,
            passed=not context.process.cancelled,
            success_message="Scenario process was not cancelled.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.OUTPUT_LIMIT_NOT_EXCEEDED:
        return _boolean_outcome(
            spec,
            passed=not context.process.output_limit_exceeded,
            success_message="Scenario output limit was not exceeded.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.CAPTURE_COMPLETED:
        return _boolean_outcome(
            spec,
            passed=context.process.capture_completed,
            success_message="Scenario output capture completed.",
            evidence_path=context.process.evidence_path,
        )
    if kind is AssertionKind.SECTION_EXISTS:
        section = _section_for(spec, context, allow_missing=True)
        if section is None:
            return _error_outcome(
                spec,
                f"Required section {spec.section_id!r} is absent.",
                None,
            )
        return _boolean_outcome(
            spec,
            passed=True,
            success_message=f"Section {spec.section_id!r} exists.",
            evidence_path=section.evidence_path,
        )
    if kind is AssertionKind.SECTION_COMPLETED:
        section = _section_for(spec, context, allow_missing=False)
        if not section.completed:
            return _error_outcome(
                spec,
                f"Section {spec.section_id!r} did not complete its marker contract.",
                section.evidence_path,
            )
        return _boolean_outcome(
            spec,
            passed=True,
            success_message=f"Section {spec.section_id!r} completed.",
            evidence_path=section.evidence_path,
        )
    if kind is AssertionKind.SECTION_NON_EMPTY:
        section = _section_for(spec, context, allow_missing=False)
        if not section.completed:
            return _error_outcome(
                spec,
                f"Section {spec.section_id!r} did not complete its marker contract.",
                section.evidence_path,
            )
        text, evidence_path = _section_text_for(spec, context)
        return _boolean_outcome(
            spec,
            passed=bool(text.strip()),
            success_message=f"Section {spec.section_id!r} output is non-empty.",
            evidence_path=evidence_path,
        )
    if kind in (
        AssertionKind.DIAGNOSTIC_PRESENT,
        AssertionKind.DIAGNOSTIC_ABSENT,
    ):
        matched = _matching_diagnostics(spec, context)
        expected_present = kind is AssertionKind.DIAGNOSTIC_PRESENT
        return _boolean_outcome(
            spec,
            passed=bool(matched) is expected_present,
            success_message=(
                "Expected diagnostic evidence is present."
                if expected_present
                else "Prohibited diagnostic evidence is absent."
            ),
            evidence_path=(
                matched[0].evidence_path if matched else _default_evidence_path(spec, context)
            ),
        )
    if kind in (
        AssertionKind.TEXT_CONTAINS,
        AssertionKind.TEXT_EXCLUDES,
        AssertionKind.TEXT_EQUALS,
        AssertionKind.TEXT_MATCHES,
    ):
        return _evaluate_text(spec, context)
    if kind is AssertionKind.COUNT_COMPARE:
        return _evaluate_count(spec, context)
    if kind in (
        AssertionKind.ARTIFACT_EXISTS,
        AssertionKind.ARTIFACT_NON_EMPTY,
        AssertionKind.ARTIFACT_CONTAINED,
        AssertionKind.ARTIFACT_CURRENT,
    ):
        return _evaluate_artifact(spec, context)
    if kind is AssertionKind.GOLD_MATCHES:
        return _evaluate_gold(spec, context)
    raise ValueError(f"unsupported assertion kind {kind!r}")


def _evaluate_text(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> _Outcome:
    text, evidence_path = _text_for(spec, context)
    expected = _parameter_text(spec, "expected", allow_empty=True)
    ignore_case = _parameter_bool(spec, "ignore_case", default=False)
    actual_value = text.casefold() if ignore_case else text
    expected_value = expected.casefold() if ignore_case else expected
    if spec.kind is AssertionKind.TEXT_CONTAINS:
        passed = expected_value in actual_value
        success_message = "Expected text is present."
    elif spec.kind is AssertionKind.TEXT_EXCLUDES:
        passed = expected_value not in actual_value
        success_message = "Prohibited text is absent."
    elif spec.kind is AssertionKind.TEXT_EQUALS:
        passed = actual_value == expected_value
        success_message = "Text equals the reviewed expected value."
    elif spec.kind is AssertionKind.TEXT_MATCHES:
        pattern = _compile_safe_pattern(
            expected,
            ignore_case=ignore_case,
            full_match=_parameter_bool(spec, "full_match", default=False),
        )
        passed = (
            pattern.fullmatch(text) is not None
            if _parameter_bool(
                spec,
                "full_match",
                default=False,
            )
            else pattern.search(text) is not None
        )
        success_message = "Text matches the reviewed pattern."
    else:
        raise AssertionError("unreachable text assertion kind")
    return _boolean_outcome(
        spec,
        passed=passed,
        success_message=success_message,
        evidence_path=evidence_path,
    )


def _evaluate_count(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> _Outcome:
    name = _parameter_identifier(
        spec,
        "name",
        pattern=_COUNT_NAME_RE,
    )
    expected = _parameter_int(spec, "expected")
    operator_value = _parameter_text(spec, "operator", allow_empty=False)
    try:
        comparison = CountComparison(operator_value)
    except ValueError as exc:
        raise ValueError(f"unsupported count comparison operator {operator_value!r}") from exc
    if name not in context.counts:
        return _error_outcome(
            spec,
            f"Count {name!r} is unavailable.",
            _default_evidence_path(spec, context),
        )
    actual = context.counts[name]
    passed = _compare_count(actual, expected, comparison)
    return _boolean_outcome(
        spec,
        passed=passed,
        success_message=(
            f"Count {name!r} satisfies {comparison.value} {expected}; actual value is {actual}."
        ),
        evidence_path=_default_evidence_path(spec, context),
    )


def _evaluate_artifact(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> _Outcome:
    artifact_id = _parameter_identifier(
        spec,
        "artifact_id",
        pattern=_ARTIFACT_ID_RE,
    )
    artifact = context.artifacts.get(artifact_id)
    if artifact is None:
        if spec.kind is AssertionKind.ARTIFACT_EXISTS:
            return _boolean_outcome(
                spec,
                passed=False,
                success_message=f"Artifact {artifact_id!r} exists.",
                evidence_path=None,
            )
        return _error_outcome(
            spec,
            f"Artifact observation {artifact_id!r} is unavailable.",
            None,
        )
    if spec.kind is AssertionKind.ARTIFACT_EXISTS:
        passed = artifact.exists
        success_message = f"Artifact {artifact_id!r} exists."
    elif spec.kind is AssertionKind.ARTIFACT_NON_EMPTY:
        if not artifact.exists:
            passed = False
        elif artifact.size_bytes is None:
            return _error_outcome(
                spec,
                f"Artifact size for {artifact_id!r} is unavailable.",
                artifact.evidence_path,
            )
        else:
            passed = artifact.size_bytes > 0
        success_message = f"Artifact {artifact_id!r} is non-empty."
    elif spec.kind is AssertionKind.ARTIFACT_CONTAINED:
        passed = artifact.contained
        success_message = f"Artifact {artifact_id!r} is contained in its owned root."
    elif spec.kind is AssertionKind.ARTIFACT_CURRENT:
        if artifact.current is None:
            return _error_outcome(
                spec,
                f"Artifact freshness for {artifact_id!r} is unavailable.",
                artifact.evidence_path,
            )
        passed = artifact.current
        success_message = f"Artifact {artifact_id!r} is current."
    else:
        raise AssertionError("unreachable artifact assertion kind")
    return _boolean_outcome(
        spec,
        passed=passed,
        success_message=success_message,
        evidence_path=artifact.evidence_path,
    )


def _evaluate_gold(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> _Outcome:
    gold = context.gold
    if gold is None:
        return _error_outcome(spec, "Gold comparison evidence is unavailable.", None)
    if gold.missing_required_gold:
        return _error_outcome(
            spec,
            "Required gold input is missing.",
            gold.evidence_path,
        )
    if not gold.evaluated or gold.matched is None:
        return _error_outcome(
            spec,
            "Gold comparison was not completed.",
            gold.evidence_path,
        )
    return _boolean_outcome(
        spec,
        passed=gold.matched,
        success_message="Normalized output matches reviewed gold.",
        evidence_path=gold.evidence_path,
    )


def _boolean_outcome(
    spec: ScenarioAssertionSpec,
    *,
    passed: bool,
    success_message: str,
    evidence_path: Path | None,
) -> _Outcome:
    if type(passed) is not bool:
        raise TypeError("assertion predicate must return a boolean")
    return _Outcome(
        status=AssertionStatus.PASSED if passed else AssertionStatus.FAILED,
        message=success_message if passed else spec.failure_message,
        evidence_path=evidence_path,
    )


def _error_outcome(
    spec: ScenarioAssertionSpec,
    message: str,
    evidence_path: Path | None,
) -> _Outcome:
    return _Outcome(
        status=AssertionStatus.ERROR,
        message=_require_text(
            message,
            field_name=f"{spec.assertion_id}.error_message",
            allow_empty=False,
            max_length=_MAX_MESSAGE_LENGTH,
        ),
        evidence_path=evidence_path,
    )


@overload
def _section_for(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
    *,
    allow_missing: Literal[False],
) -> SectionAssertionEvidence: ...


@overload
def _section_for(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
    *,
    allow_missing: Literal[True],
) -> SectionAssertionEvidence | None: ...


def _section_for(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
    *,
    allow_missing: bool,
) -> SectionAssertionEvidence | None:
    section_id = spec.section_id
    if section_id is None:
        raise ValueError(f"assertion {spec.assertion_id!r} requires section_id")
    section = context.sections.get(section_id)
    if section is None and not allow_missing:
        raise ValueError(f"section {section_id!r} is unavailable")
    return section


def _section_text_for(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> tuple[str, Path | None]:
    section_id = spec.section_id
    if section_id is None:
        raise ValueError(f"assertion {spec.assertion_id!r} requires section_id")
    section = context.sections.get(section_id)
    if spec.source is AssertionInputSource.NORMALIZED_SECTION:
        text = context.normalized_sections.get(section_id)
        if text is None:
            raise ValueError(f"normalized section {section_id!r} is unavailable")
        return text, None if section is None else section.evidence_path
    if section is None:
        raise ValueError(f"section {section_id!r} is unavailable")
    return section.text, section.evidence_path


def _text_for(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> tuple[str, Path | None]:
    source = spec.source
    if source is AssertionInputSource.RAW_STDOUT:
        return context.raw_stdout, context.process.evidence_path
    if source is AssertionInputSource.RAW_STDERR:
        return context.raw_stderr, context.process.evidence_path
    if source is AssertionInputSource.NORMALIZED_OUTPUT:
        if context.normalized_output is None:
            raise ValueError("normalized output is unavailable")
        return context.normalized_output, None
    if source is AssertionInputSource.NORMALIZED_SECTION:
        return _section_text_for(spec, context)
    raise ValueError(f"source {source.value!r} does not provide text")


def _matching_diagnostics(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> tuple[DiagnosticAssertionEvidence, ...]:
    diagnostic_id = _optional_parameter_text(spec, "diagnostic_id")
    kind = _optional_parameter_text(spec, "kind")
    message_pattern = _optional_parameter_text(spec, "message_pattern")
    fatal = _optional_parameter_bool(spec, "fatal")
    section_id = spec.section_id
    compiled_pattern = None
    if message_pattern is not None:
        compiled_pattern = _compile_safe_pattern(
            message_pattern,
            ignore_case=_parameter_bool(spec, "ignore_case", default=False),
            full_match=False,
        )
    matches: list[DiagnosticAssertionEvidence] = []
    for diagnostic in context.diagnostics:
        if diagnostic_id is not None and diagnostic.diagnostic_id != diagnostic_id:
            continue
        if kind is not None and diagnostic.kind != kind:
            continue
        if fatal is not None and diagnostic.fatal is not fatal:
            continue
        if section_id is not None and diagnostic.section_id != section_id:
            continue
        if compiled_pattern is not None and compiled_pattern.search(diagnostic.message) is None:
            continue
        matches.append(diagnostic)
    return tuple(matches)


def _default_evidence_path(
    spec: ScenarioAssertionSpec,
    context: AssertionEvaluationContext,
) -> Path | None:
    if spec.section_id is not None:
        section = context.sections.get(spec.section_id)
        if section is not None and section.evidence_path is not None:
            return section.evidence_path
    return context.process.evidence_path


def _compare_count(
    actual: int,
    expected: int,
    comparison: CountComparison,
) -> bool:
    if comparison is CountComparison.EQUAL:
        return actual == expected
    if comparison is CountComparison.NOT_EQUAL:
        return actual != expected
    if comparison is CountComparison.LESS_THAN:
        return actual < expected
    if comparison is CountComparison.LESS_THAN_OR_EQUAL:
        return actual <= expected
    if comparison is CountComparison.GREATER_THAN:
        return actual > expected
    if comparison is CountComparison.GREATER_THAN_OR_EQUAL:
        return actual >= expected
    raise ValueError(f"unsupported comparison {comparison!r}")


def _prepare_specs(
    specs: object,
) -> tuple[ScenarioAssertionSpec, ...]:
    if isinstance(specs, (str, bytes)) or not isinstance(specs, Iterable):
        raise TypeError("specs must be an iterable of ScenarioAssertionSpec")
    ordered = tuple(specs)
    if len(ordered) > _MAX_COLLECTION_ITEMS:
        raise ValueError("assertion count exceeds the supported limit")
    seen: set[str] = set()
    for spec in ordered:
        if not isinstance(spec, ScenarioAssertionSpec):
            raise TypeError("specs must contain ScenarioAssertionSpec objects")
        if spec.assertion_id in seen:
            raise ValueError(f"duplicate assertion ID {spec.assertion_id!r}")
        seen.add(spec.assertion_id)
    return ordered


def _validate_spec_parameters(
    *,
    kind: AssertionKind,
    source: AssertionInputSource,
    section_id: str | None,
    parameters: AssertionParameters,
) -> None:
    required: set[str] = set()
    optional: set[str] = set()
    if kind is AssertionKind.EXIT_CODE_EQUALS:
        required = {"expected"}
    elif kind in (
        AssertionKind.SECTION_EXISTS,
        AssertionKind.SECTION_COMPLETED,
        AssertionKind.SECTION_NON_EMPTY,
    ):
        if section_id is None:
            raise ValueError(f"assertion kind {kind.value!r} requires section_id")
    elif kind in (
        AssertionKind.DIAGNOSTIC_PRESENT,
        AssertionKind.DIAGNOSTIC_ABSENT,
    ):
        optional = {
            "diagnostic_id",
            "kind",
            "message_pattern",
            "fatal",
            "ignore_case",
        }
        if (
            not any(
                name in parameters for name in ("diagnostic_id", "kind", "message_pattern", "fatal")
            )
            and section_id is None
        ):
            raise ValueError(
                f"assertion kind {kind.value!r} requires at least one "
                "diagnostic filter or section_id"
            )
    elif kind in (
        AssertionKind.TEXT_CONTAINS,
        AssertionKind.TEXT_EXCLUDES,
        AssertionKind.TEXT_EQUALS,
    ):
        required = {"expected"}
        optional = {"ignore_case"}
    elif kind is AssertionKind.TEXT_MATCHES:
        required = {"expected"}
        optional = {"ignore_case", "full_match"}
    elif kind is AssertionKind.COUNT_COMPARE:
        required = {"name", "operator", "expected"}
    elif kind in (
        AssertionKind.ARTIFACT_EXISTS,
        AssertionKind.ARTIFACT_NON_EMPTY,
        AssertionKind.ARTIFACT_CONTAINED,
        AssertionKind.ARTIFACT_CURRENT,
    ):
        required = {"artifact_id"}
    missing = required.difference(parameters)
    if missing:
        rendered = ", ".join(sorted(missing))
        raise ValueError(f"assertion kind {kind.value!r} is missing parameters: {rendered}")
    unexpected = set(parameters).difference(required | optional)
    if unexpected:
        rendered = ", ".join(sorted(unexpected))
        raise ValueError(f"assertion kind {kind.value!r} has unsupported parameters: {rendered}")
    if source is AssertionInputSource.NORMALIZED_SECTION and section_id is None:
        raise ValueError("normalized-section assertions require section_id")
    if kind is AssertionKind.TEXT_MATCHES:
        pattern = _parameter_text_from(parameters, "expected", allow_empty=False)
        _compile_safe_pattern(
            pattern,
            ignore_case=_bool_from_parameters(parameters, "ignore_case", False),
            full_match=_bool_from_parameters(parameters, "full_match", False),
        )
    if kind is AssertionKind.COUNT_COMPARE:
        name = _parameter_text_from(parameters, "name", allow_empty=False)
        if _COUNT_NAME_RE.fullmatch(name) is None:
            raise ValueError(f"invalid count name {name!r}")
        operator_value = _parameter_text_from(
            parameters,
            "operator",
            allow_empty=False,
        )
        try:
            CountComparison(operator_value)
        except ValueError as exc:
            raise ValueError(f"unsupported count comparison operator {operator_value!r}") from exc
        expected = parameters["expected"]
        if type(expected) is not int:
            raise TypeError("count comparison expected must be an integer")


def _freeze_parameters(values: AssertionParameters) -> AssertionParameters:
    if not isinstance(values, Mapping):
        raise TypeError("parameters must be a mapping")
    if len(values) > _MAX_PARAMETER_ITEMS:
        raise ValueError("parameters exceeds the supported item limit")
    copied: dict[str, AssertionParameter] = {}
    for key, value in values.items():
        key = _require_identifier(
            key,
            field_name="parameters key",
            pattern=_COUNT_NAME_RE,
        )
        if type(value) not in (str, int, bool, type(None), tuple):
            raise TypeError(f"parameter {key!r} has unsupported type {type(value).__name__}")
        if isinstance(value, str):
            value = _require_text(
                value,
                field_name=f"parameters[{key!r}]",
                allow_empty=True,
                max_length=_MAX_TEXT_LENGTH,
            )
        elif isinstance(value, tuple):
            if len(value) > _MAX_COLLECTION_ITEMS:
                raise ValueError(f"parameter {key!r} tuple is too large")
            normalized_items: list[str] = []
            for item in value:
                normalized_items.append(
                    _require_text(
                        item,
                        field_name=f"parameters[{key!r}] item",
                        allow_empty=True,
                        max_length=_MAX_MESSAGE_LENGTH,
                    )
                )
            value = tuple(normalized_items)
        copied[key] = value
    return MappingProxyType(copied)


def _freeze_sections(
    values: Mapping[str, SectionAssertionEvidence],
) -> Mapping[str, SectionAssertionEvidence]:
    if not isinstance(values, Mapping):
        raise TypeError("sections must be a mapping")
    if len(values) > _MAX_COLLECTION_ITEMS:
        raise ValueError("sections exceeds the supported item limit")
    copied: dict[str, SectionAssertionEvidence] = {}
    for key, value in values.items():
        key = _require_identifier(
            key,
            field_name="sections key",
            pattern=_SECTION_ID_RE,
        )
        if not isinstance(value, SectionAssertionEvidence):
            raise TypeError("sections values must be SectionAssertionEvidence")
        if value.section_id != key:
            raise ValueError(
                f"section mapping key {key!r} does not match value identity {value.section_id!r}"
            )
        copied[key] = value
    return MappingProxyType(copied)


def _freeze_text_mapping(
    values: Mapping[str, str],
    *,
    field_name: str,
    key_pattern: re.Pattern[str],
) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    if len(values) > _MAX_COLLECTION_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported item limit")
    copied: dict[str, str] = {}
    for key, value in values.items():
        key = _require_identifier(
            key,
            field_name=f"{field_name} key",
            pattern=key_pattern,
        )
        copied[key] = _require_text(
            value,
            field_name=f"{field_name}[{key!r}]",
            allow_empty=True,
            max_length=_MAX_TEXT_LENGTH,
        )
    return MappingProxyType(copied)


def _freeze_counts(values: Mapping[str, int]) -> Mapping[str, int]:
    if not isinstance(values, Mapping):
        raise TypeError("counts must be a mapping")
    if len(values) > _MAX_COLLECTION_ITEMS:
        raise ValueError("counts exceeds the supported item limit")
    copied: dict[str, int] = {}
    for key, value in values.items():
        key = _require_identifier(
            key,
            field_name="counts key",
            pattern=_COUNT_NAME_RE,
        )
        if type(value) is not int:
            raise TypeError(f"count {key!r} must be an integer")
        if value < 0:
            raise ValueError(f"count {key!r} must be non-negative")
        copied[key] = value
    return MappingProxyType(copied)


def _freeze_artifacts(
    values: Mapping[str, ArtifactAssertionEvidence],
) -> Mapping[str, ArtifactAssertionEvidence]:
    if not isinstance(values, Mapping):
        raise TypeError("artifacts must be a mapping")
    if len(values) > _MAX_COLLECTION_ITEMS:
        raise ValueError("artifacts exceeds the supported item limit")
    copied: dict[str, ArtifactAssertionEvidence] = {}
    for key, value in values.items():
        key = _require_identifier(
            key,
            field_name="artifacts key",
            pattern=_ARTIFACT_ID_RE,
        )
        if not isinstance(value, ArtifactAssertionEvidence):
            raise TypeError("artifacts values must be ArtifactAssertionEvidence")
        if value.artifact_id != key:
            raise ValueError(
                f"artifact mapping key {key!r} does not match value identity {value.artifact_id!r}"
            )
        copied[key] = value
    return MappingProxyType(copied)


def _freeze_typed_tuple(
    values: object,
    *,
    item_type: type[_TypedItemT],
    field_name: str,
) -> tuple[_TypedItemT, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"{field_name} must be an iterable of {item_type.__name__}")
    copied = tuple(values)
    if len(copied) > _MAX_COLLECTION_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported item limit")
    prepared: list[_TypedItemT] = []
    for item in copied:
        if not isinstance(item, item_type):
            raise TypeError(f"{field_name} must contain {item_type.__name__} objects")
        prepared.append(item)
    return tuple(prepared)


def _validate_evidence_containment(
    *,
    run_root: Path,
    process: ProcessAssertionEvidence,
    sections: Mapping[str, SectionAssertionEvidence],
    diagnostics: tuple[DiagnosticAssertionEvidence, ...],
    artifacts: Mapping[str, ArtifactAssertionEvidence],
    gold: GoldAssertionEvidence | None,
) -> None:
    evidence_paths: list[Path] = []
    if process.evidence_path is not None:
        evidence_paths.append(process.evidence_path)
    evidence_paths.extend(
        section.evidence_path for section in sections.values() if section.evidence_path is not None
    )
    evidence_paths.extend(
        diagnostic.evidence_path
        for diagnostic in diagnostics
        if diagnostic.evidence_path is not None
    )
    evidence_paths.extend(
        artifact.evidence_path
        for artifact in artifacts.values()
        if artifact.evidence_path is not None
    )
    if gold is not None and gold.evidence_path is not None:
        evidence_paths.append(gold.evidence_path)
    for path in evidence_paths:
        if not path.is_absolute():
            raise ValueError(f"evidence path must be absolute: {path!s}")
        if not _is_relative_to(path, run_root):
            raise ValueError(f"evidence path escapes run_root: {path!s}")


def _compile_safe_pattern(
    pattern: str,
    *,
    ignore_case: bool,
    full_match: bool,
) -> re.Pattern[str]:
    pattern = _require_text(
        pattern,
        field_name="pattern",
        allow_empty=False,
        max_length=_MAX_PATTERN_LENGTH,
    )
    if "(?" in pattern:
        raise ValueError("regex extensions and lookarounds are not supported")
    if re.search(r"\\[1-9]", pattern) is not None:
        raise ValueError("regex backreferences are not supported")
    if re.search(r"(?:\*|\+|\?|\{[^}]+\})\s*(?:\*|\+|\?|\{)", pattern):
        raise ValueError("nested or repeated quantifiers are not supported")
    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"invalid assertion regex: {exc}") from exc
    if full_match and pattern.startswith("^") and pattern.endswith("$"):
        return compiled
    return compiled


def _parameter_text(
    spec: ScenarioAssertionSpec,
    name: str,
    *,
    allow_empty: bool,
) -> str:
    return _parameter_text_from(spec.parameters, name, allow_empty=allow_empty)


def _parameter_text_from(
    parameters: AssertionParameters,
    name: str,
    *,
    allow_empty: bool,
) -> str:
    value = parameters.get(name)
    if not isinstance(value, str):
        raise TypeError(f"parameter {name!r} must be a string")
    return _require_text(
        value,
        field_name=f"parameter {name!r}",
        allow_empty=allow_empty,
        max_length=_MAX_TEXT_LENGTH,
    )


def _optional_parameter_text(
    spec: ScenarioAssertionSpec,
    name: str,
) -> str | None:
    value = spec.parameters.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"parameter {name!r} must be a string")
    return _require_text(
        value,
        field_name=f"parameter {name!r}",
        allow_empty=False,
        max_length=_MAX_PATTERN_LENGTH,
    )


def _parameter_int(spec: ScenarioAssertionSpec, name: str) -> int:
    value = spec.parameters.get(name)
    if type(value) is not int:
        raise TypeError(f"parameter {name!r} must be an integer")
    return value


def _parameter_bool(
    spec: ScenarioAssertionSpec,
    name: str,
    *,
    default: bool,
) -> bool:
    return _bool_from_parameters(spec.parameters, name, default)


def _bool_from_parameters(
    parameters: AssertionParameters,
    name: str,
    default: bool,
) -> bool:
    value = parameters.get(name, default)
    if type(value) is not bool:
        raise TypeError(f"parameter {name!r} must be a boolean")
    return value


def _optional_parameter_bool(
    spec: ScenarioAssertionSpec,
    name: str,
) -> bool | None:
    value = spec.parameters.get(name)
    if value is None:
        return None
    if type(value) is not bool:
        raise TypeError(f"parameter {name!r} must be a boolean")
    return value


def _parameter_identifier(
    spec: ScenarioAssertionSpec,
    name: str,
    *,
    pattern: re.Pattern[str],
) -> str:
    return _require_identifier(
        _parameter_text(spec, name, allow_empty=False),
        field_name=f"parameter {name!r}",
        pattern=pattern,
    )


def _require_identifier(
    value: object,
    *,
    field_name: str,
    pattern: re.Pattern[str],
) -> str:
    text = _require_text(
        value,
        field_name=field_name,
        allow_empty=False,
        max_length=256,
    )
    if not text.isascii():
        raise ValueError(f"{field_name} must use ASCII characters only")
    if pattern.fullmatch(text) is None:
        raise ValueError(f"invalid {field_name} {text!r}")
    return text


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length limit")
    return value


def _coerce_path(value: object, *, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _coerce_optional_path(value: object, *, field_name: str) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value, field_name=field_name)


def _validate_optional_positive_int(
    value: int | None,
    *,
    field_name: str,
) -> None:
    if value is None:
        return
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer or None")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_exception_text(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    text = text.replace("\x00", "\\x00")
    if len(text) > _MAX_MESSAGE_LENGTH:
        text = text[: _MAX_MESSAGE_LENGTH - 1] + "…"
    return text


__all__ = (
    "ArtifactAssertionEvidence",
    "AssertionBatchResult",
    "AssertionCategory",
    "AssertionEvaluationContext",
    "AssertionInputSource",
    "AssertionKind",
    "AssertionParameters",
    "AssertionStatus",
    "CountComparison",
    "DiagnosticAssertionEvidence",
    "GoldAssertionEvidence",
    "ProcessAssertionEvidence",
    "ScenarioAssertionEvaluator",
    "ScenarioAssertionResult",
    "ScenarioAssertionSpec",
    "SectionAssertionEvidence",
    "aggregate_assertion_results",
    "evaluate_assertion",
    "evaluate_assertion_results",
    "evaluate_assertions",
)
