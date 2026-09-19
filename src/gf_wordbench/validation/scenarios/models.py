"""Native scenario domain models for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final, TypeVar

from gf_wordbench.infrastructure.process import (
    ArtifactExpectation,
    ArtifactObservation,
)
from gf_wordbench.kernel.ids import (
    ScenarioId,
    SectionId,
    validate_scenario_id,
    validate_section_id,
)
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationMode,
    ValidationStatus,
)

__all__ = (
    "ScenarioAssertionResult",
    "ScenarioAssertionStatus",
    "ScenarioComparisonPolicy",
    "ScenarioResult",
    "ScenarioSectionResult",
    "ScenarioSpec",
)

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_ASSERTION_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ASSERTION_KIND_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_NORMALIZATION_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$"
)
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_BLOCKER_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,255}$")

_MAX_COMMAND_PARTS: Final[int] = 4096
_MAX_TEXT_LENGTH: Final[int] = 4096
_MAX_MESSAGE_LENGTH: Final[int] = 16384
_MAX_SECTIONS: Final[int] = 4096
_MAX_ASSERTIONS: Final[int] = 16384
_MAX_ARTIFACTS: Final[int] = 4096
_MAX_INPUT_PATHS: Final[int] = 4096
_MAX_TAGS: Final[int] = 256
_MAX_BLOCKERS: Final[int] = 4096
_MAX_OUTPUT_LIMIT_BYTES: Final[int] = 1 << 40

_EnumT = TypeVar("_EnumT", bound=StrEnum)


@unique
class ScenarioComparisonPolicy(StrEnum):
    NONE = "none"
    EXACT = "exact"


@unique
class ScenarioAssertionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: ScenarioId
    script_path: Path
    required: bool
    enabled_modes: tuple[ValidationMode, ...]
    working_directory: Path
    timeout_sec: float
    output_limit_bytes: int
    gold_path: Path | None
    comparison_policy: ScenarioComparisonPolicy
    normalization_version: str
    expected_sections: tuple[SectionId, ...]
    expected_artifacts: tuple[ArtifactExpectation, ...]
    input_paths: tuple[Path, ...]
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        scenario_id = validate_scenario_id(
            self.scenario_id,
            field="scenario_id",
        )
        script_path = _normalize_project_relative_path(
            self.script_path,
            field="script_path",
            suffix=".gfs",
        )
        required = _require_bool(
            self.required,
            field="required",
        )
        enabled_modes = _normalize_unique_enums(
            self.enabled_modes,
            ValidationMode,
            field="enabled_modes",
            allow_empty=False,
        )
        working_directory = _normalize_absolute_path(
            self.working_directory,
            field="working_directory",
        )
        timeout_sec = _require_positive_finite_number(
            self.timeout_sec,
            field="timeout_sec",
        )
        output_limit_bytes = _require_plain_int(
            self.output_limit_bytes,
            field="output_limit_bytes",
            minimum=1,
        )
        if output_limit_bytes > _MAX_OUTPUT_LIMIT_BYTES:
            raise ValueError("output_limit_bytes exceeds the supported bound")

        gold_path = (
            None
            if self.gold_path is None
            else _normalize_project_relative_path(
                self.gold_path,
                field="gold_path",
                suffix=".gold",
            )
        )
        comparison_policy = _require_enum(
            self.comparison_policy,
            ScenarioComparisonPolicy,
            field="comparison_policy",
        )
        normalization_version = _normalize_identifier(
            self.normalization_version,
            field="normalization_version",
            pattern=_NORMALIZATION_VERSION_RE,
        )
        expected_sections = _normalize_section_ids(
            self.expected_sections,
            field="expected_sections",
        )
        expected_artifacts = _normalize_artifact_expectations(
            self.expected_artifacts,
        )
        input_paths = _normalize_unique_project_paths(
            self.input_paths,
            field="input_paths",
            maximum=_MAX_INPUT_PATHS,
        )
        tags = _normalize_unique_identifiers(
            self.tags,
            field="tags",
            pattern=_TAG_RE,
            maximum=_MAX_TAGS,
        )

        if comparison_policy is ScenarioComparisonPolicy.EXACT and gold_path is None:
            raise ValueError("exact comparison requires gold_path")
        if comparison_policy is ScenarioComparisonPolicy.NONE and gold_path is not None:
            raise ValueError("gold_path requires exact comparison policy")

        expected_artifact_paths = {
            _path_key(expectation.path) for expectation in expected_artifacts
        }
        if len(expected_artifact_paths) != len(expected_artifacts):
            raise ValueError("expected_artifacts must not contain duplicate paths")

        object.__setattr__(
            self,
            "scenario_id",
            scenario_id,
        )
        object.__setattr__(
            self,
            "script_path",
            script_path,
        )
        object.__setattr__(self, "required", required)
        object.__setattr__(
            self,
            "enabled_modes",
            enabled_modes,
        )
        object.__setattr__(
            self,
            "working_directory",
            working_directory,
        )
        object.__setattr__(
            self,
            "timeout_sec",
            timeout_sec,
        )
        object.__setattr__(
            self,
            "output_limit_bytes",
            output_limit_bytes,
        )
        object.__setattr__(self, "gold_path", gold_path)
        object.__setattr__(
            self,
            "comparison_policy",
            comparison_policy,
        )
        object.__setattr__(
            self,
            "normalization_version",
            normalization_version,
        )
        object.__setattr__(
            self,
            "expected_sections",
            expected_sections,
        )
        object.__setattr__(
            self,
            "expected_artifacts",
            expected_artifacts,
        )
        object.__setattr__(
            self,
            "input_paths",
            input_paths,
        )
        object.__setattr__(self, "tags", tags)

    @property
    def uses_gold(self) -> bool:
        return self.comparison_policy is ScenarioComparisonPolicy.EXACT

    def is_enabled_for(
        self,
        mode: ValidationMode,
    ) -> bool:
        normalized_mode = _require_enum(
            mode,
            ValidationMode,
            field="mode",
        )
        return normalized_mode in self.enabled_modes


@dataclass(frozen=True, slots=True)
class ScenarioSectionResult:
    id: SectionId
    completed: bool
    message: str = ""
    begin_line: int | None = None
    end_line: int | None = None

    def __post_init__(self) -> None:
        section_id = validate_section_id(
            self.id,
            field="id",
        )
        completed = _require_bool(
            self.completed,
            field="completed",
        )
        message = _normalize_evidence_text(
            self.message,
            field="message",
            maximum=_MAX_MESSAGE_LENGTH,
            allow_empty=True,
        )
        begin_line = _normalize_optional_positive_int(
            self.begin_line,
            field="begin_line",
        )
        end_line = _normalize_optional_positive_int(
            self.end_line,
            field="end_line",
        )

        if end_line is not None and begin_line is None:
            raise ValueError("end_line requires begin_line")
        if begin_line is not None and end_line is not None and end_line < begin_line:
            raise ValueError("end_line must not precede begin_line")
        if completed and end_line is None:
            raise ValueError("a completed section requires end_line")
        if not completed and end_line is not None:
            raise ValueError("an incomplete section must not claim end_line")

        object.__setattr__(self, "id", section_id)
        object.__setattr__(
            self,
            "completed",
            completed,
        )
        object.__setattr__(self, "message", message)
        object.__setattr__(
            self,
            "begin_line",
            begin_line,
        )
        object.__setattr__(self, "end_line", end_line)


@dataclass(frozen=True, slots=True)
class ScenarioAssertionResult:
    assertion_id: str
    assertion_kind: str
    status: ScenarioAssertionStatus
    message: str
    evidence_path: Path | None = None
    section_id: SectionId | None = None
    required: bool = True

    def __post_init__(self) -> None:
        assertion_id = _normalize_identifier(
            self.assertion_id,
            field="assertion_id",
            pattern=_ASSERTION_ID_RE,
        )
        assertion_kind = _normalize_identifier(
            self.assertion_kind,
            field="assertion_kind",
            pattern=_ASSERTION_KIND_RE,
        )
        status = _require_enum(
            self.status,
            ScenarioAssertionStatus,
            field="status",
        )
        message = _normalize_evidence_text(
            self.message,
            field="message",
            maximum=_MAX_MESSAGE_LENGTH,
            allow_empty=False,
        )
        evidence_path = (
            None
            if self.evidence_path is None
            else _normalize_run_relative_path(
                self.evidence_path,
                field="evidence_path",
            )
        )
        section_id = (
            None
            if self.section_id is None
            else validate_section_id(
                self.section_id,
                field="section_id",
            )
        )
        required = _require_bool(
            self.required,
            field="required",
        )

        object.__setattr__(
            self,
            "assertion_id",
            assertion_id,
        )
        object.__setattr__(
            self,
            "assertion_kind",
            assertion_kind,
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "message", message)
        object.__setattr__(
            self,
            "evidence_path",
            evidence_path,
        )
        object.__setattr__(
            self,
            "section_id",
            section_id,
        )
        object.__setattr__(self, "required", required)

    @property
    def blocks_success(self) -> bool:
        return self.required and self.status in {
            ScenarioAssertionStatus.FAILED,
            ScenarioAssertionStatus.ERROR,
            ScenarioAssertionStatus.SKIPPED,
        }


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: ScenarioId
    script_path: Path
    script_sha256: str
    required: bool
    status: ValidationStatus
    execution_state: ExecutionState | None
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    timed_out: bool
    cancelled: bool
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    normalized_output_path: Path | None
    gold_path: Path | None
    gold_match: bool | None
    gold_diff_path: Path | None
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    primary_message: str
    sections: tuple[ScenarioSectionResult, ...]
    assertions: tuple[ScenarioAssertionResult, ...]
    artifacts: tuple[ArtifactObservation, ...]
    blocked_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        scenario_id = validate_scenario_id(
            self.scenario_id,
            field="scenario_id",
        )
        script_path = _normalize_project_relative_path(
            self.script_path,
            field="script_path",
            suffix=".gfs",
        )
        script_sha256 = _normalize_identifier(
            self.script_sha256,
            field="script_sha256",
            pattern=_SHA256_RE,
        )
        required = _require_bool(
            self.required,
            field="required",
        )
        status = _require_enum(
            self.status,
            ValidationStatus,
            field="status",
        )
        execution_state = (
            None
            if self.execution_state is None
            else _require_enum(
                self.execution_state,
                ExecutionState,
                field="execution_state",
            )
        )
        command = _normalize_command(self.command)
        working_directory = _normalize_absolute_path(
            self.working_directory,
            field="working_directory",
        )
        exit_code = _normalize_exit_code(self.exit_code)
        timed_out = _require_bool(
            self.timed_out,
            field="timed_out",
        )
        cancelled = _require_bool(
            self.cancelled,
            field="cancelled",
        )
        duration_ms = _require_plain_int(
            self.duration_ms,
            field="duration_ms",
            minimum=0,
        )
        stdout_path = _normalize_optional_run_path(
            self.stdout_path,
            field="stdout_path",
        )
        stderr_path = _normalize_optional_run_path(
            self.stderr_path,
            field="stderr_path",
        )
        normalized_output_path = _normalize_optional_run_path(
            self.normalized_output_path,
            field="normalized_output_path",
        )
        gold_path = (
            None
            if self.gold_path is None
            else _normalize_project_relative_path(
                self.gold_path,
                field="gold_path",
                suffix=".gold",
            )
        )
        gold_match = _normalize_optional_bool(
            self.gold_match,
            field="gold_match",
        )
        gold_diff_path = _normalize_optional_run_path(
            self.gold_diff_path,
            field="gold_diff_path",
        )
        diagnostic_class = _require_enum(
            self.diagnostic_class,
            DiagnosticClass,
            field="diagnostic_class",
        )
        error_kind = _require_enum(
            self.error_kind,
            ErrorKind,
            field="error_kind",
        )
        primary_message = _normalize_evidence_text(
            self.primary_message,
            field="primary_message",
            maximum=_MAX_MESSAGE_LENGTH,
            allow_empty=False,
        )
        sections = _normalize_sections(self.sections)
        assertions = _normalize_assertions(
            self.assertions,
            sections=sections,
        )
        artifacts = _normalize_artifact_observations(self.artifacts)
        blocked_by = _normalize_unique_identifiers(
            self.blocked_by,
            field="blocked_by",
            pattern=_BLOCKER_RE,
            maximum=_MAX_BLOCKERS,
        )

        _validate_execution_facts(
            status=status,
            execution_state=execution_state,
            command=command,
            exit_code=exit_code,
            timed_out=timed_out,
            cancelled=cancelled,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        _validate_status_classification(
            status=status,
            diagnostic_class=diagnostic_class,
            error_kind=error_kind,
            blocked_by=blocked_by,
        )
        _validate_scenario_evidence(
            status=status,
            execution_state=execution_state,
            exit_code=exit_code,
            sections=sections,
            assertions=assertions,
            normalized_output_path=normalized_output_path,
            gold_path=gold_path,
            gold_match=gold_match,
            gold_diff_path=gold_diff_path,
            artifacts=artifacts,
        )

        object.__setattr__(
            self,
            "scenario_id",
            scenario_id,
        )
        object.__setattr__(
            self,
            "script_path",
            script_path,
        )
        object.__setattr__(
            self,
            "script_sha256",
            script_sha256,
        )
        object.__setattr__(self, "required", required)
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "execution_state",
            execution_state,
        )
        object.__setattr__(self, "command", command)
        object.__setattr__(
            self,
            "working_directory",
            working_directory,
        )
        object.__setattr__(self, "exit_code", exit_code)
        object.__setattr__(self, "timed_out", timed_out)
        object.__setattr__(self, "cancelled", cancelled)
        object.__setattr__(
            self,
            "duration_ms",
            duration_ms,
        )
        object.__setattr__(
            self,
            "stdout_path",
            stdout_path,
        )
        object.__setattr__(
            self,
            "stderr_path",
            stderr_path,
        )
        object.__setattr__(
            self,
            "normalized_output_path",
            normalized_output_path,
        )
        object.__setattr__(self, "gold_path", gold_path)
        object.__setattr__(
            self,
            "gold_match",
            gold_match,
        )
        object.__setattr__(
            self,
            "gold_diff_path",
            gold_diff_path,
        )
        object.__setattr__(
            self,
            "diagnostic_class",
            diagnostic_class,
        )
        object.__setattr__(
            self,
            "error_kind",
            error_kind,
        )
        object.__setattr__(
            self,
            "primary_message",
            primary_message,
        )
        object.__setattr__(self, "sections", sections)
        object.__setattr__(
            self,
            "assertions",
            assertions,
        )
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(
            self,
            "blocked_by",
            blocked_by,
        )

    @property
    def is_direct(self) -> bool:
        return self.diagnostic_class is DiagnosticClass.DIRECT

    @property
    def completed_sections(self) -> int:
        return sum(section.completed for section in self.sections)

    @property
    def required_assertions_passed(self) -> bool:
        return all(
            not assertion.required or assertion.status is ScenarioAssertionStatus.PASSED
            for assertion in self.assertions
        )

    @property
    def has_framework_error(self) -> bool:
        return self.status is ValidationStatus.ERROR


def _validate_execution_facts(
    *,
    status: ValidationStatus,
    execution_state: ExecutionState | None,
    command: tuple[str, ...],
    exit_code: int | None,
    timed_out: bool,
    cancelled: bool,
    stdout_path: Path | None,
    stderr_path: Path | None,
) -> None:
    if execution_state is None:
        if status is not ValidationStatus.SKIPPED:
            raise ValueError("execution_state may be None only for SKIPPED")
        if command:
            raise ValueError("an unexecuted scenario must not claim a command")
        if exit_code is not None:
            raise ValueError("an unexecuted scenario must not claim exit_code")
        if timed_out or cancelled:
            raise ValueError("an unexecuted scenario cannot time out or cancel")
        if stdout_path is not None or stderr_path is not None:
            raise ValueError("an unexecuted scenario must not claim raw evidence")
        return

    if not command:
        raise ValueError("an attempted scenario requires a command")
    if stdout_path is None or stderr_path is None:
        raise ValueError("an attempted scenario requires stdout and stderr paths")

    if execution_state is ExecutionState.COMPLETED:
        if timed_out or cancelled:
            raise ValueError("completed execution cannot time out or cancel")
        if exit_code is None:
            raise ValueError("completed execution requires exit_code")
    elif execution_state is ExecutionState.TIMED_OUT:
        if not timed_out or cancelled:
            raise ValueError("timed_out execution flags are inconsistent")
        if status is not ValidationStatus.ERROR:
            raise ValueError("timed_out execution requires ERROR status")
    elif execution_state is ExecutionState.CANCELLED:
        if timed_out or not cancelled:
            raise ValueError("cancelled execution flags are inconsistent")
        if status is not ValidationStatus.ERROR:
            raise ValueError("cancelled execution requires ERROR status")
    elif execution_state is ExecutionState.LAUNCH_FAILED:
        if timed_out or cancelled:
            raise ValueError("launch_failed flags are inconsistent")
        if exit_code is not None:
            raise ValueError("launch_failed execution must not claim exit_code")
        if status is not ValidationStatus.ERROR:
            raise ValueError("launch_failed execution requires ERROR status")


def _validate_status_classification(
    *,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    error_kind: ErrorKind,
    blocked_by: tuple[str, ...],
) -> None:
    if status is ValidationStatus.OK:
        if diagnostic_class is not DiagnosticClass.OK:
            raise ValueError("OK status requires diagnostic_class=ok")
        if error_kind is not ErrorKind.OK:
            raise ValueError("OK status requires error_kind=OK")
        if blocked_by:
            raise ValueError("OK status must not contain blockers")
        return

    if status is ValidationStatus.SKIPPED:
        if diagnostic_class is not DiagnosticClass.SKIPPED:
            raise ValueError("SKIPPED status requires diagnostic_class=skipped")
        if error_kind is not ErrorKind.OK:
            raise ValueError("intentional SKIPPED status requires error_kind=OK")
        return

    if diagnostic_class is DiagnosticClass.OK:
        raise ValueError("FAIL or ERROR must not use diagnostic_class=ok")
    if diagnostic_class is DiagnosticClass.SKIPPED:
        raise ValueError("FAIL or ERROR must not use diagnostic_class=skipped")
    if diagnostic_class is DiagnosticClass.DOWNSTREAM and not blocked_by:
        raise ValueError("downstream classification requires blocked_by")

    if status is ValidationStatus.ERROR:
        if error_kind is ErrorKind.OK:
            raise ValueError("ERROR status requires a technical error kind")
    elif error_kind is ErrorKind.OK:
        raise ValueError("FAIL status requires OTHER or a more specific error kind")


def _validate_scenario_evidence(
    *,
    status: ValidationStatus,
    execution_state: ExecutionState | None,
    exit_code: int | None,
    sections: tuple[ScenarioSectionResult, ...],
    assertions: tuple[ScenarioAssertionResult, ...],
    normalized_output_path: Path | None,
    gold_path: Path | None,
    gold_match: bool | None,
    gold_diff_path: Path | None,
    artifacts: tuple[ArtifactObservation, ...],
) -> None:
    if gold_match is not None:
        if gold_path is None:
            raise ValueError("gold_match requires gold_path")
        if normalized_output_path is None:
            raise ValueError("gold_match requires normalized_output_path")

    if gold_match is True and gold_diff_path is not None:
        raise ValueError("matching gold must not claim a diff path")
    if gold_match is False and gold_diff_path is None:
        raise ValueError("gold mismatch requires gold_diff_path")
    if gold_diff_path is not None and gold_match is not False:
        raise ValueError("gold_diff_path is valid only for a mismatch")

    if status is ValidationStatus.OK:
        if execution_state is not ExecutionState.COMPLETED:
            raise ValueError("OK scenario requires completed execution")
        if exit_code != 0:
            raise ValueError("OK scenario requires exit_code zero")
        if any(not section.completed for section in sections):
            raise ValueError("OK scenario requires every declared section to complete")
        if any(assertion.blocks_success for assertion in assertions):
            raise ValueError("OK scenario requires every required assertion to pass")
        if gold_match is False:
            raise ValueError("OK scenario cannot contain a gold mismatch")
        if any(
            observation.required and (not observation.exists or not observation.kind_matches)
            for observation in artifacts
        ):
            raise ValueError("OK scenario requires all required artifacts")

    if status is ValidationStatus.FAIL:
        if execution_state is not ExecutionState.COMPLETED:
            raise ValueError("FAIL scenario requires completed execution")
        if not (
            any(not section.completed for section in sections)
            or any(
                assertion.required and assertion.status is ScenarioAssertionStatus.FAILED
                for assertion in assertions
            )
            or gold_match is False
            or any(
                observation.required and (not observation.exists or not observation.kind_matches)
                for observation in artifacts
            )
            or exit_code not in {None, 0}
        ):
            raise ValueError("FAIL scenario requires observable validation failure")

    if status is ValidationStatus.SKIPPED:
        if sections or assertions or artifacts:
            raise ValueError("SKIPPED scenario must not contain evaluated results")
        if normalized_output_path is not None:
            raise ValueError("SKIPPED scenario must not claim normalized output")
        if gold_match is not None or gold_diff_path is not None:
            raise ValueError("SKIPPED scenario must not claim gold comparison")


def _normalize_sections(
    values: tuple[ScenarioSectionResult, ...],
) -> tuple[ScenarioSectionResult, ...]:
    if not isinstance(values, tuple):
        raise TypeError("sections must be a tuple")
    if len(values) > _MAX_SECTIONS:
        raise ValueError("sections exceeds the supported bound")

    seen: set[str] = set()
    normalized: list[ScenarioSectionResult] = []
    for index, value in enumerate(values):
        if not isinstance(
            value,
            ScenarioSectionResult,
        ):
            raise TypeError(f"sections[{index}] must be a ScenarioSectionResult")
        key = str(value.id)
        if key in seen:
            raise ValueError("section IDs must be unique")
        seen.add(key)
        normalized.append(value)
    return tuple(normalized)


def _normalize_assertions(
    values: tuple[ScenarioAssertionResult, ...],
    *,
    sections: tuple[ScenarioSectionResult, ...],
) -> tuple[ScenarioAssertionResult, ...]:
    if not isinstance(values, tuple):
        raise TypeError("assertions must be a tuple")
    if len(values) > _MAX_ASSERTIONS:
        raise ValueError("assertions exceeds the supported bound")

    section_ids = {str(section.id) for section in sections}
    seen: set[str] = set()
    normalized: list[ScenarioAssertionResult] = []

    for index, value in enumerate(values):
        if not isinstance(
            value,
            ScenarioAssertionResult,
        ):
            raise TypeError(f"assertions[{index}] must be a ScenarioAssertionResult")
        if value.assertion_id in seen:
            raise ValueError("assertion IDs must be unique")
        if value.section_id is not None and str(value.section_id) not in section_ids:
            raise ValueError("assertion section_id must reference a known section")
        seen.add(value.assertion_id)
        normalized.append(value)

    return tuple(normalized)


def _normalize_artifact_expectations(
    values: tuple[ArtifactExpectation, ...],
) -> tuple[ArtifactExpectation, ...]:
    if not isinstance(values, tuple):
        raise TypeError("expected_artifacts must be a tuple")
    if len(values) > _MAX_ARTIFACTS:
        raise ValueError("expected_artifacts exceeds the supported bound")
    if any(not isinstance(value, ArtifactExpectation) for value in values):
        raise TypeError("expected_artifacts must contain ArtifactExpectation values")
    return values


def _normalize_artifact_observations(
    values: tuple[ArtifactObservation, ...],
) -> tuple[ArtifactObservation, ...]:
    if not isinstance(values, tuple):
        raise TypeError("artifacts must be a tuple")
    if len(values) > _MAX_ARTIFACTS:
        raise ValueError("artifacts exceeds the supported bound")

    seen: set[str] = set()
    normalized: list[ArtifactObservation] = []
    for index, value in enumerate(values):
        if not isinstance(
            value,
            ArtifactObservation,
        ):
            raise TypeError(f"artifacts[{index}] must be an ArtifactObservation")
        key = _path_key(value.path)
        if key in seen:
            raise ValueError("artifact observation paths must be unique")
        seen.add(key)
        normalized.append(value)
    return tuple(normalized)


def _normalize_section_ids(
    values: tuple[SectionId, ...],
    *,
    field: str,
) -> tuple[SectionId, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > _MAX_SECTIONS:
        raise ValueError(f"{field} exceeds the supported bound")

    seen: set[str] = set()
    normalized: list[SectionId] = []
    for index, value in enumerate(values):
        section_id = validate_section_id(
            value,
            field=f"{field}[{index}]",
        )
        key = str(section_id)
        if key in seen:
            raise ValueError(f"{field} must not contain duplicate IDs")
        seen.add(key)
        normalized.append(section_id)
    return tuple(normalized)


def _normalize_unique_enums(
    values: tuple[_EnumT, ...],
    enum_type: type[_EnumT],
    *,
    field: str,
    allow_empty: bool,
) -> tuple[_EnumT, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field} must not be empty")

    seen: set[_EnumT] = set()
    normalized: list[_EnumT] = []
    for index, value in enumerate(values):
        item = _require_enum(
            value,
            enum_type,
            field=f"{field}[{index}]",
        )
        if item in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_unique_project_paths(
    values: tuple[Path, ...],
    *,
    field: str,
    maximum: int,
) -> tuple[Path, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > maximum:
        raise ValueError(f"{field} exceeds the supported bound")

    seen: set[str] = set()
    normalized: list[Path] = []
    for index, value in enumerate(values):
        path = _normalize_project_relative_path(
            value,
            field=f"{field}[{index}]",
        )
        key = path.as_posix()
        if key in seen:
            raise ValueError(f"{field} must not contain duplicate paths")
        seen.add(key)
        normalized.append(path)
    return tuple(normalized)


def _normalize_unique_identifiers(
    values: tuple[str, ...],
    *,
    field: str,
    pattern: re.Pattern[str],
    maximum: int,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")
    if len(values) > maximum:
        raise ValueError(f"{field} exceeds the supported bound")

    seen: set[str] = set()
    normalized: list[str] = []
    for index, value in enumerate(values):
        item = _normalize_identifier(
            value,
            field=f"{field}[{index}]",
            pattern=pattern,
        )
        if item in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_command(
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError("command must be a tuple")
    if len(values) > _MAX_COMMAND_PARTS:
        raise ValueError("command exceeds the supported argument bound")

    normalized: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"command[{index}] must be a string")
        if "\x00" in value:
            raise ValueError(f"command[{index}] must not contain NUL")
        if not value:
            raise ValueError(f"command[{index}] must not be empty")
        normalized.append(value)
    return tuple(normalized)


def _normalize_optional_run_path(
    value: Path | None,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    return _normalize_run_relative_path(
        value,
        field=field,
    )


def _normalize_project_relative_path(
    value: object,
    *,
    field: str,
    suffix: str | None = None,
) -> Path:
    path = _normalize_relative_path(
        value,
        field=field,
    )
    if suffix is not None and path.suffix.casefold() != suffix.casefold():
        raise ValueError(f"{field} must end in {suffix}")
    return path


def _normalize_run_relative_path(
    value: object,
    *,
    field: str,
) -> Path:
    return _normalize_relative_path(
        value,
        field=field,
    )


def _normalize_relative_path(
    value: object,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")

    rendered = value.as_posix()
    if not rendered:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in rendered:
        raise ValueError(f"{field} must not contain NUL")
    if _is_absolute_path_text(rendered):
        raise ValueError(f"{field} must be relative")

    portable = PurePosixPath(rendered)
    if portable == PurePosixPath("."):
        raise ValueError(f"{field} must identify a path")
    if any(part in {"", ".", ".."} for part in portable.parts):
        raise ValueError(f"{field} must be normalized without traversal")

    normalized = Path(*portable.parts)
    if normalized.as_posix() != rendered:
        raise ValueError(f"{field} must use canonical forward slashes")
    return normalized


def _normalize_absolute_path(
    value: object,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    rendered = str(value)
    if not rendered:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in rendered:
        raise ValueError(f"{field} must not contain NUL")
    if not _is_absolute_path_text(rendered):
        raise ValueError(f"{field} must be absolute")

    portable = PurePosixPath(rendered.replace("\\", "/"))
    windows = PureWindowsPath(rendered)
    if ".." in portable.parts or ".." in windows.parts:
        raise ValueError(f"{field} must not contain traversal")
    return value


def _is_absolute_path_text(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )


def _normalize_identifier(
    value: object,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not value.isascii():
        raise ValueError(f"{field} must use ASCII characters")
    if pattern.fullmatch(value) is None:
        raise ValueError(f"{field} has an invalid canonical form")
    return value


def _normalize_evidence_text(
    value: object,
    *,
    field: str,
    maximum: int,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    normalized = value.replace("\r\n", "\n").replace(
        "\r",
        "\n",
    )
    if not allow_empty and not normalized.strip():
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return normalized


def _normalize_exit_code(
    value: object,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError("exit_code must be an integer or None")
    return value


def _normalize_optional_bool(
    value: object,
    *,
    field: str,
) -> bool | None:
    if value is None:
        return None
    return _require_bool(
        value,
        field=field,
    )


def _normalize_optional_positive_int(
    value: object,
    *,
    field: str,
) -> int | None:
    if value is None:
        return None
    return _require_plain_int(
        value,
        field=field,
        minimum=1,
    )


def _require_bool(
    value: object,
    *,
    field: str,
) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _require_plain_int(
    value: object,
    *,
    field: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return value


def _require_positive_finite_number(
    value: object,
    *,
    field: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{field} must be a number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return normalized


def _require_enum(
    value: object,
    enum_type: type[_EnumT],
    *,
    field: str,
) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    allowed = ", ".join(member.value for member in enum_type)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be one of: {allowed}")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be one of: {allowed}") from exc


def _path_key(path: Path) -> str:
    return path.as_posix().casefold()
