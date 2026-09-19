"""Bounded, deterministic orchestration of validation-owned stages."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
import math
from pathlib import Path
from time import monotonic
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)


@unique
class ValidationStageId(StrEnum):
    SELECT = "VAL-080"
    INVENTORY = "VAL-090"
    STATIC_SCAN = "VAL-100"
    COMPILE = "VAL-110"
    NORMALIZE_DIAGNOSTICS = "VAL-120"
    CLASSIFY_FAILURES = "VAL-130"
    EXECUTE_SCENARIOS = "VAL-140"
    NORMALIZE_SCENARIOS = "VAL-150"
    COMPARE_GOLD = "VAL-160"
    BUILD_RELEASE_ARTIFACTS = "VAL-170"
    EVALUATE_RELEASE = "VAL-180"
    COMPARE_PREVIOUS = "VAL-190"


@unique
class ValidationStageClass(StrEnum):
    INVENTORY = "inventory"
    ANALYSIS = "analysis"
    SCENARIO = "scenario"
    RELEASE = "release"
    FINALIZATION = "finalization"


@unique
class StageParticipation(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    SKIPPED = "skipped"


CANONICAL_STAGE_ORDER: Final[tuple[ValidationStageId, ...]] = tuple(ValidationStageId)

_STAGE_NAMES: Final[Mapping[ValidationStageId, str]] = MappingProxyType(
    {
        ValidationStageId.SELECT: "Select validation subjects",
        ValidationStageId.INVENTORY: "Inventory and fingerprint sources",
        ValidationStageId.STATIC_SCAN: "Run static source scans",
        ValidationStageId.COMPILE: "Compile selected GF modules",
        ValidationStageId.NORMALIZE_DIAGNOSTICS: ("Normalize compile diagnostics"),
        ValidationStageId.CLASSIFY_FAILURES: ("Classify validation failures"),
        ValidationStageId.EXECUTE_SCENARIOS: ("Execute selected GF scenarios"),
        ValidationStageId.NORMALIZE_SCENARIOS: ("Normalize scenario output and verify markers"),
        ValidationStageId.COMPARE_GOLD: ("Compare normalized scenario output with gold"),
        ValidationStageId.BUILD_RELEASE_ARTIFACTS: ("Build required release artifacts"),
        ValidationStageId.EVALUATE_RELEASE: ("Evaluate artifact and release gates"),
        ValidationStageId.COMPARE_PREVIOUS: ("Compare with the previous compatible run"),
    }
)

_STAGE_CLASSES: Final[Mapping[ValidationStageId, ValidationStageClass]] = MappingProxyType(
    {
        ValidationStageId.SELECT: ValidationStageClass.INVENTORY,
        ValidationStageId.INVENTORY: ValidationStageClass.INVENTORY,
        ValidationStageId.STATIC_SCAN: ValidationStageClass.ANALYSIS,
        ValidationStageId.COMPILE: ValidationStageClass.ANALYSIS,
        ValidationStageId.NORMALIZE_DIAGNOSTICS: (ValidationStageClass.ANALYSIS),
        ValidationStageId.CLASSIFY_FAILURES: (ValidationStageClass.ANALYSIS),
        ValidationStageId.EXECUTE_SCENARIOS: (ValidationStageClass.SCENARIO),
        ValidationStageId.NORMALIZE_SCENARIOS: (ValidationStageClass.SCENARIO),
        ValidationStageId.COMPARE_GOLD: (ValidationStageClass.SCENARIO),
        ValidationStageId.BUILD_RELEASE_ARTIFACTS: (ValidationStageClass.RELEASE),
        ValidationStageId.EVALUATE_RELEASE: (ValidationStageClass.RELEASE),
        ValidationStageId.COMPARE_PREVIOUS: (ValidationStageClass.FINALIZATION),
    }
)

_STAGE_DEPENDENCIES: Final[Mapping[ValidationStageId, tuple[ValidationStageId, ...]]] = (
    MappingProxyType(
        {
            ValidationStageId.SELECT: (),
            ValidationStageId.INVENTORY: (ValidationStageId.SELECT,),
            ValidationStageId.STATIC_SCAN: (ValidationStageId.INVENTORY,),
            ValidationStageId.COMPILE: (ValidationStageId.INVENTORY,),
            ValidationStageId.NORMALIZE_DIAGNOSTICS: (ValidationStageId.COMPILE,),
            ValidationStageId.CLASSIFY_FAILURES: (ValidationStageId.NORMALIZE_DIAGNOSTICS,),
            ValidationStageId.EXECUTE_SCENARIOS: (
                ValidationStageId.SELECT,
                ValidationStageId.CLASSIFY_FAILURES,
            ),
            ValidationStageId.NORMALIZE_SCENARIOS: (ValidationStageId.EXECUTE_SCENARIOS,),
            ValidationStageId.COMPARE_GOLD: (ValidationStageId.NORMALIZE_SCENARIOS,),
            ValidationStageId.BUILD_RELEASE_ARTIFACTS: (ValidationStageId.CLASSIFY_FAILURES,),
            ValidationStageId.EVALUATE_RELEASE: (ValidationStageId.CLASSIFY_FAILURES,),
            ValidationStageId.COMPARE_PREVIOUS: (ValidationStageId.EVALUATE_RELEASE,),
        }
    )
)

_MODE_MATRIX: Final[
    Mapping[
        ValidationMode,
        Mapping[ValidationStageId, StageParticipation],
    ]
] = MappingProxyType(
    {
        ValidationMode.QUICK: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: StageParticipation.REQUIRED,
                ValidationStageId.NORMALIZE_DIAGNOSTICS: (StageParticipation.REQUIRED),
                ValidationStageId.CLASSIFY_FAILURES: (StageParticipation.OPTIONAL),
                ValidationStageId.EXECUTE_SCENARIOS: (StageParticipation.OPTIONAL),
                ValidationStageId.NORMALIZE_SCENARIOS: (StageParticipation.CONDITIONAL),
                ValidationStageId.COMPARE_GOLD: (StageParticipation.OPTIONAL),
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: (StageParticipation.SKIPPED),
                ValidationStageId.EVALUATE_RELEASE: (StageParticipation.SKIPPED),
                ValidationStageId.COMPARE_PREVIOUS: (StageParticipation.OPTIONAL),
            }
        ),
        ValidationMode.CHECKPOINT: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: StageParticipation.REQUIRED,
                ValidationStageId.NORMALIZE_DIAGNOSTICS: (StageParticipation.REQUIRED),
                ValidationStageId.CLASSIFY_FAILURES: (StageParticipation.REQUIRED),
                ValidationStageId.EXECUTE_SCENARIOS: (StageParticipation.REQUIRED),
                ValidationStageId.NORMALIZE_SCENARIOS: (StageParticipation.REQUIRED),
                ValidationStageId.COMPARE_GOLD: (StageParticipation.CONDITIONAL),
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: (StageParticipation.OPTIONAL),
                ValidationStageId.EVALUATE_RELEASE: (StageParticipation.REQUIRED),
                ValidationStageId.COMPARE_PREVIOUS: (StageParticipation.CONDITIONAL),
            }
        ),
        ValidationMode.RELEASE: MappingProxyType(
            {
                stage_id: (
                    StageParticipation.CONDITIONAL
                    if stage_id
                    in {
                        ValidationStageId.COMPARE_GOLD,
                        ValidationStageId.BUILD_RELEASE_ARTIFACTS,
                    }
                    else StageParticipation.REQUIRED
                )
                for stage_id in CANONICAL_STAGE_ORDER
            }
        ),
        ValidationMode.DIAGNOSTIC: MappingProxyType(
            {
                ValidationStageId.SELECT: StageParticipation.REQUIRED,
                ValidationStageId.INVENTORY: StageParticipation.REQUIRED,
                ValidationStageId.STATIC_SCAN: StageParticipation.REQUIRED,
                ValidationStageId.COMPILE: (StageParticipation.CONDITIONAL),
                ValidationStageId.NORMALIZE_DIAGNOSTICS: (StageParticipation.CONDITIONAL),
                ValidationStageId.CLASSIFY_FAILURES: (StageParticipation.REQUIRED),
                ValidationStageId.EXECUTE_SCENARIOS: (StageParticipation.CONDITIONAL),
                ValidationStageId.NORMALIZE_SCENARIOS: (StageParticipation.CONDITIONAL),
                ValidationStageId.COMPARE_GOLD: (StageParticipation.OPTIONAL),
                ValidationStageId.BUILD_RELEASE_ARTIFACTS: (StageParticipation.OPTIONAL),
                ValidationStageId.EVALUATE_RELEASE: (StageParticipation.OPTIONAL),
                ValidationStageId.COMPARE_PREVIOUS: (StageParticipation.OPTIONAL),
            }
        ),
    }
)


@dataclass(frozen=True, slots=True)
class PipelineStageResult:
    stage_id: ValidationStageId
    stage_name: str
    stage_class: ValidationStageClass
    required: bool
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    validation_status: ValidationStatus
    execution_state: ExecutionState | None
    error_kind: ErrorKind
    message: str
    warnings: tuple[str, ...] = ()
    blocked_by: tuple[ValidationStageId, ...] = ()
    input_count: int = 0
    output_count: int = 0
    artifact_paths: tuple[Path, ...] = ()
    payload: object | None = None
    abort_pipeline: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.stage_id, ValidationStageId):
            raise TypeError("stage_id must be a ValidationStageId")
        if not isinstance(self.stage_class, ValidationStageClass):
            raise TypeError("stage_class must be a ValidationStageClass")
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")
        started_at = _utc_datetime(
            self.started_at,
            field_name="started_at",
        )
        finished_at = _utc_datetime(
            self.finished_at,
            field_name="finished_at",
        )
        if finished_at < started_at:
            raise ValueError("finished_at must not precede started_at")
        _non_negative_integer(
            self.duration_ms,
            field_name="duration_ms",
        )
        if not isinstance(
            self.validation_status,
            ValidationStatus,
        ):
            raise TypeError("validation_status must be a ValidationStatus")
        if self.execution_state is not None and not isinstance(
            self.execution_state,
            ExecutionState,
        ):
            raise TypeError("execution_state must be an ExecutionState or None")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be an ErrorKind")
        message = _required_text(
            self.message,
            field_name="message",
        )
        warnings = _text_tuple(
            self.warnings,
            field_name="warnings",
        )
        blocked_by = _stage_id_tuple(
            self.blocked_by,
            field_name="blocked_by",
        )
        _non_negative_integer(
            self.input_count,
            field_name="input_count",
        )
        _non_negative_integer(
            self.output_count,
            field_name="output_count",
        )
        artifact_paths = _path_tuple(
            self.artifact_paths,
            field_name="artifact_paths",
        )
        if not isinstance(self.abort_pipeline, bool):
            raise TypeError("abort_pipeline must be a bool")
        if (
            self.validation_status in {ValidationStatus.OK, ValidationStatus.SKIPPED}
            and self.error_kind is not ErrorKind.OK
        ):
            raise ValueError("OK or SKIPPED stage results require ErrorKind.OK")
        if (
            self.validation_status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
            and self.error_kind is ErrorKind.OK
        ):
            raise ValueError("FAIL or ERROR stage results require a non-OK error kind")
        if self.validation_status is ValidationStatus.SKIPPED and self.execution_state is not None:
            raise ValueError("SKIPPED stage results cannot have execution_state")
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "finished_at", finished_at)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "blocked_by", blocked_by)
        object.__setattr__(
            self,
            "artifact_paths",
            artifact_paths,
        )


@dataclass(frozen=True, slots=True)
class PipelineStageContext:
    mode: ValidationMode
    stage_id: ValidationStageId
    participation: StageParticipation
    request: object
    previous_results: Mapping[
        ValidationStageId,
        PipelineStageResult,
    ]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        if not isinstance(self.stage_id, ValidationStageId):
            raise TypeError("stage_id must be a ValidationStageId")
        if not isinstance(
            self.participation,
            StageParticipation,
        ):
            raise TypeError("participation must be a StageParticipation")
        previous_results = _result_mapping(self.previous_results)
        metadata = _string_mapping(
            self.metadata,
            field_name="metadata",
        )
        object.__setattr__(
            self,
            "previous_results",
            previous_results,
        )
        object.__setattr__(self, "metadata", metadata)


@runtime_checkable
class CancellationSource(Protocol):
    def is_cancellation_requested(self) -> bool: ...

    def cancellation_reason(self) -> str | None: ...


StageExecutor: TypeAlias = Callable[
    [PipelineStageContext],
    PipelineStageResult,
]
StageGuard: TypeAlias = Callable[
    [PipelineStageContext],
    tuple[ValidationStageId, ...],
]
UtcNow: TypeAlias = Callable[[], datetime]
MonotonicNow: TypeAlias = Callable[[], float]


@dataclass(frozen=True, slots=True)
class ValidationPipelinePlan:
    mode: ValidationMode
    request: object
    executors: Mapping[ValidationStageId, StageExecutor]
    guards: Mapping[ValidationStageId, StageGuard] = field(default_factory=dict)
    participation_overrides: Mapping[
        ValidationStageId,
        StageParticipation,
    ] = field(default_factory=dict)
    enabled_conditional_stages: frozenset[ValidationStageId] = frozenset()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        executors = _executor_mapping(self.executors)
        guards = _guard_mapping(self.guards)
        overrides = _participation_mapping(self.participation_overrides)
        enabled = frozenset(self.enabled_conditional_stages)
        if not all(isinstance(item, ValidationStageId) for item in enabled):
            raise TypeError("enabled_conditional_stages must contain ValidationStageId values")
        metadata = _string_mapping(
            self.metadata,
            field_name="metadata",
        )

        for stage_id in CANONICAL_STAGE_ORDER:
            participation = overrides.get(
                stage_id,
                _MODE_MATRIX[self.mode][stage_id],
            )
            if participation is StageParticipation.REQUIRED and stage_id not in executors:
                raise ValueError(f"required stage {stage_id.value} has no executor")

        object.__setattr__(self, "executors", executors)
        object.__setattr__(self, "guards", guards)
        object.__setattr__(
            self,
            "participation_overrides",
            overrides,
        )
        object.__setattr__(
            self,
            "enabled_conditional_stages",
            enabled,
        )
        object.__setattr__(self, "metadata", metadata)

    def participation_for(
        self,
        stage_id: ValidationStageId,
    ) -> StageParticipation:
        participation = self.participation_overrides.get(
            stage_id,
            _MODE_MATRIX[self.mode][stage_id],
        )
        if (
            participation is StageParticipation.CONDITIONAL
            and stage_id not in self.enabled_conditional_stages
        ):
            return StageParticipation.SKIPPED
        return participation


@dataclass(frozen=True, slots=True)
class ValidationPipelineResult:
    mode: ValidationMode
    stage_results: tuple[PipelineStageResult, ...]
    overall_status: OverallStatus
    cancelled: bool
    cancellation_reason: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        stage_results = tuple(self.stage_results)
        if not all(isinstance(item, PipelineStageResult) for item in stage_results):
            raise TypeError("stage_results must contain PipelineStageResult values")
        if tuple(item.stage_id for item in stage_results) != CANONICAL_STAGE_ORDER:
            raise ValueError("stage_results must follow the canonical stage order")
        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be an OverallStatus")
        if not isinstance(self.cancelled, bool):
            raise TypeError("cancelled must be a bool")
        reason = self.cancellation_reason
        if reason is not None:
            reason = _required_text(
                reason,
                field_name="cancellation_reason",
            )
        if self.cancelled != (reason is not None):
            raise ValueError("cancelled must agree with cancellation_reason")
        object.__setattr__(
            self,
            "stage_results",
            stage_results,
        )
        object.__setattr__(
            self,
            "cancellation_reason",
            reason,
        )

    def result_for(
        self,
        stage_id: ValidationStageId,
    ) -> PipelineStageResult:
        for result in self.stage_results:
            if result.stage_id is stage_id:
                return result
        raise KeyError(stage_id)


def preflight_external_tools(*args: object, **kwargs: object) -> object:
    """Run an injected external-tool preflight callable."""
    operation = kwargs.pop("operation", None)
    if operation is None and args and callable(args[0]):
        operation, args = args[0], args[1:]
    if not callable(operation):
        raise TypeError("operation must be callable")
    return operation(*args, **kwargs)


def run_file_pipeline(*args: object, **kwargs: object) -> object:
    operation = kwargs.pop("operation", None)
    if operation is None and args and callable(args[0]):
        operation, args = args[0], args[1:]
    if not callable(operation):
        raise TypeError("operation must be callable")
    return operation(*args, **kwargs)


def run_pgf_stage_if_required(
    *args: object, required: bool = True, **kwargs: object
) -> object | None:
    if type(required) is not bool:
        raise TypeError("required must be a bool")
    if not required:
        return None
    return run_file_pipeline(*args, **kwargs)


def run_selected_scenarios(*args: object, **kwargs: object) -> object:
    return run_file_pipeline(*args, **kwargs)


def execute_validation_pipeline(
    plan: ValidationPipelinePlan,
    *,
    cancellation_source: CancellationSource | None = None,
    utc_now: UtcNow = lambda: datetime.now(UTC),
    monotonic_now: MonotonicNow = monotonic,
) -> ValidationPipelineResult:
    if not isinstance(plan, ValidationPipelinePlan):
        raise TypeError("plan must be a ValidationPipelinePlan")
    if cancellation_source is not None and not isinstance(
        cancellation_source,
        CancellationSource,
    ):
        raise TypeError("cancellation_source must implement CancellationSource")
    if not callable(utc_now):
        raise TypeError("utc_now must be callable")
    if not callable(monotonic_now):
        raise TypeError("monotonic_now must be callable")

    results: dict[
        ValidationStageId,
        PipelineStageResult,
    ] = {}
    aborted = False
    cancelled = False
    cancellation_reason: str | None = None

    for stage_id in CANONICAL_STAGE_ORDER:
        participation = plan.participation_for(stage_id)
        required = participation is StageParticipation.REQUIRED

        if cancellation_source is not None:
            if cancellation_source.is_cancellation_requested():
                cancelled = True
                cancellation_reason = (
                    cancellation_source.cancellation_reason() or "Cancellation requested."
                )

        if cancelled:
            result = _skipped_result(
                stage_id,
                required=required,
                message=cancellation_reason or "Cancellation requested.",
                blocked_by=(),
                utc_now=utc_now,
            )
        elif aborted:
            result = _skipped_result(
                stage_id,
                required=required,
                message=(
                    "Stage was not scheduled because an earlier "
                    "stage aborted the validation pipeline."
                ),
                blocked_by=(),
                utc_now=utc_now,
            )
        elif participation is StageParticipation.SKIPPED:
            result = _skipped_result(
                stage_id,
                required=False,
                message=(f"Stage is not selected by the active {plan.mode.value} mode policy."),
                blocked_by=(),
                utc_now=utc_now,
            )
        elif stage_id not in plan.executors:
            result = _skipped_result(
                stage_id,
                required=required,
                message=("Optional or conditional stage has no active executor for this run."),
                blocked_by=(),
                utc_now=utc_now,
            )
        else:
            context = PipelineStageContext(
                mode=plan.mode,
                stage_id=stage_id,
                participation=participation,
                request=plan.request,
                previous_results=MappingProxyType(dict(results)),
                metadata=plan.metadata,
            )
            blockers = _default_blockers(
                stage_id,
                results=results,
            )
            guard = plan.guards.get(stage_id)
            if guard is not None:
                blockers = _merge_stage_ids(
                    blockers,
                    guard(context),
                )

            if blockers:
                result = _skipped_result(
                    stage_id,
                    required=required,
                    message=("Stage prerequisites did not produce trustworthy executable inputs."),
                    blocked_by=blockers,
                    utc_now=utc_now,
                )
            else:
                result = _execute_stage(
                    stage_id,
                    required=required,
                    executor=plan.executors[stage_id],
                    context=context,
                    utc_now=utc_now,
                    monotonic_now=monotonic_now,
                )

        results[stage_id] = result
        aborted = aborted or result.abort_pipeline

    ordered = tuple(results[stage_id] for stage_id in CANONICAL_STAGE_ORDER)
    overall = aggregate_pipeline_status(ordered)

    return ValidationPipelineResult(
        mode=plan.mode,
        stage_results=ordered,
        overall_status=overall,
        cancelled=cancelled,
        cancellation_reason=cancellation_reason,
    )


def aggregate_pipeline_status(
    results: Sequence[PipelineStageResult],
) -> OverallStatus:
    normalized = tuple(results)
    if not all(isinstance(item, PipelineStageResult) for item in normalized):
        raise TypeError("results must contain PipelineStageResult values")
    if any(item.validation_status is ValidationStatus.ERROR for item in normalized):
        return OverallStatus.ERROR
    if any(
        item.required
        and item.validation_status in {ValidationStatus.FAIL, ValidationStatus.SKIPPED}
        for item in normalized
    ):
        return OverallStatus.FAIL
    return OverallStatus.OK


def _execute_stage(
    stage_id: ValidationStageId,
    *,
    required: bool,
    executor: StageExecutor,
    context: PipelineStageContext,
    utc_now: UtcNow,
    monotonic_now: MonotonicNow,
) -> PipelineStageResult:
    started_at = _utc_datetime(
        utc_now(),
        field_name="utc_now result",
    )
    started_tick = _finite_number(
        monotonic_now(),
        field_name="monotonic_now result",
    )

    try:
        result = executor(context)
    except Exception as exc:
        finished_at = _utc_datetime(
            utc_now(),
            field_name="utc_now result",
        )
        finished_tick = _finite_number(
            monotonic_now(),
            field_name="monotonic_now result",
        )
        return PipelineStageResult(
            stage_id=stage_id,
            stage_name=_STAGE_NAMES[stage_id],
            stage_class=_STAGE_CLASSES[stage_id],
            required=required,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=_duration_ms(
                started_tick,
                finished_tick,
            ),
            validation_status=ValidationStatus.ERROR,
            execution_state=None,
            error_kind=ErrorKind.INTERNAL,
            message=(f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__),
            abort_pipeline=False,
        )

    if not isinstance(result, PipelineStageResult):
        raise TypeError("stage executor must return PipelineStageResult")
    if result.stage_id is not stage_id:
        raise ValueError("stage executor returned a result for another stage")
    if result.required is not required:
        raise ValueError("stage executor changed the planned required flag")
    return result


def _default_blockers(
    stage_id: ValidationStageId,
    *,
    results: Mapping[
        ValidationStageId,
        PipelineStageResult,
    ],
) -> tuple[ValidationStageId, ...]:
    blockers: list[ValidationStageId] = []
    for dependency in _STAGE_DEPENDENCIES[stage_id]:
        result = results.get(dependency)
        if result is None:
            blockers.append(dependency)
            continue
        if result.required and result.validation_status in {
            ValidationStatus.ERROR,
            ValidationStatus.SKIPPED,
        }:
            blockers.append(dependency)
    return tuple(blockers)


def _skipped_result(
    stage_id: ValidationStageId,
    *,
    required: bool,
    message: str,
    blocked_by: tuple[ValidationStageId, ...],
    utc_now: UtcNow,
) -> PipelineStageResult:
    timestamp = _utc_datetime(
        utc_now(),
        field_name="utc_now result",
    )
    return PipelineStageResult(
        stage_id=stage_id,
        stage_name=_STAGE_NAMES[stage_id],
        stage_class=_STAGE_CLASSES[stage_id],
        required=required,
        started_at=timestamp,
        finished_at=timestamp,
        duration_ms=0,
        validation_status=ValidationStatus.SKIPPED,
        execution_state=None,
        error_kind=ErrorKind.OK,
        message=message,
        blocked_by=blocked_by,
    )


def _merge_stage_ids(
    first: tuple[ValidationStageId, ...],
    second: Sequence[ValidationStageId],
) -> tuple[ValidationStageId, ...]:
    combined = (
        *first,
        *_stage_id_tuple(
            tuple(second),
            field_name="guard blockers",
        ),
    )
    seen: set[ValidationStageId] = set()
    result: list[ValidationStageId] = []
    for stage_id in CANONICAL_STAGE_ORDER:
        if stage_id in combined and stage_id not in seen:
            seen.add(stage_id)
            result.append(stage_id)
    return tuple(result)


def _duration_ms(start: float, finish: float) -> int:
    if finish < start:
        raise ValueError("monotonic clock moved backwards")
    return max(0, round((finish - start) * 1000))


def _executor_mapping(
    value: object,
) -> Mapping[ValidationStageId, StageExecutor]:
    if not isinstance(value, Mapping):
        raise TypeError("executors must be a mapping")
    result: dict[ValidationStageId, StageExecutor] = {}
    for key, executor in value.items():
        if not isinstance(key, ValidationStageId):
            raise TypeError("executor keys must be ValidationStageId values")
        if not callable(executor):
            raise TypeError(f"executor for {key.value} must be callable")
        result[key] = executor
    return MappingProxyType(result)


def _guard_mapping(
    value: object,
) -> Mapping[ValidationStageId, StageGuard]:
    if not isinstance(value, Mapping):
        raise TypeError("guards must be a mapping")
    result: dict[ValidationStageId, StageGuard] = {}
    for key, guard in value.items():
        if not isinstance(key, ValidationStageId):
            raise TypeError("guard keys must be ValidationStageId values")
        if not callable(guard):
            raise TypeError(f"guard for {key.value} must be callable")
        result[key] = guard
    return MappingProxyType(result)


def _participation_mapping(
    value: object,
) -> Mapping[ValidationStageId, StageParticipation]:
    if not isinstance(value, Mapping):
        raise TypeError("participation_overrides must be a mapping")
    result: dict[
        ValidationStageId,
        StageParticipation,
    ] = {}
    for key, participation in value.items():
        if not isinstance(key, ValidationStageId):
            raise TypeError("participation keys must be ValidationStageId values")
        if not isinstance(
            participation,
            StageParticipation,
        ):
            raise TypeError("participation values must be StageParticipation values")
        result[key] = participation
    return MappingProxyType(result)


def _result_mapping(
    value: object,
) -> Mapping[ValidationStageId, PipelineStageResult]:
    if not isinstance(value, Mapping):
        raise TypeError("previous_results must be a mapping")
    result: dict[
        ValidationStageId,
        PipelineStageResult,
    ] = {}
    for key, item in value.items():
        if not isinstance(key, ValidationStageId):
            raise TypeError("previous_results keys must be ValidationStageId values")
        if not isinstance(item, PipelineStageResult):
            raise TypeError("previous_results values must be PipelineStageResult values")
        if item.stage_id is not key:
            raise ValueError("previous_results key does not match result stage_id")
        result[key] = item
    return MappingProxyType(result)


def _string_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    result: dict[str, str] = {}
    for key, item in value.items():
        result[
            _required_text(
                key,
                field_name=f"{field_name} key",
            )
        ] = _required_text(
            item,
            field_name=f"{field_name} value",
        )
    return MappingProxyType(dict(sorted(result.items())))


def _stage_id_tuple(
    value: object,
    *,
    field_name: str,
) -> tuple[ValidationStageId, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not all(isinstance(item, ValidationStageId) for item in value):
        raise TypeError(f"{field_name} must contain ValidationStageId values")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _text_tuple(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    return tuple(
        _required_text(
            item,
            field_name=f"{field_name} item",
        )
        for item in value
    )


def _path_tuple(
    value: object,
    *,
    field_name: str,
) -> tuple[Path, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    result: list[Path] = []
    for item in value:
        if not isinstance(item, Path):
            raise TypeError(f"{field_name} must contain pathlib.Path values")
        if "\x00" in str(item):
            raise ValueError(f"{field_name} paths must not contain NUL characters")
        result.append(item)
    return tuple(result)


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
    return value


def _utc_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _finite_number(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{field_name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


__all__ = (
    "CANONICAL_STAGE_ORDER",
    "CancellationSource",
    "PipelineStageContext",
    "PipelineStageResult",
    "StageGuard",
    "StageParticipation",
    "ValidationPipelinePlan",
    "ValidationPipelineResult",
    "ValidationStageClass",
    "ValidationStageId",
    "aggregate_pipeline_status",
    "execute_validation_pipeline",
)
