"""Deterministic validation-stage planning for one resolved GF Wordbench run."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.config.models import RunConfig, ValidationTarget
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode


@unique
class StageId(StrEnum):
    CONFIGURATION = "configuration"
    ENVIRONMENT = "environment"
    VERSION_PROBE = "version_probe"
    SELECTION = "selection"
    STATIC_SCAN = "static_scan"
    FINGERPRINT = "fingerprint"
    COMPILE_SOURCES = "compile_sources"
    COMPILE_CHECKPOINTS = "compile_checkpoints"
    COMPILE_ENTRYPOINTS = "compile_entrypoints"
    CLASSIFY_FAILURES = "classify_failures"
    RUN_SCENARIOS = "run_scenarios"
    NORMALIZE_OUTPUTS = "normalize_outputs"
    EVALUATE_ASSERTIONS = "evaluate_assertions"
    COMPARE_GOLD = "compare_gold"
    BUILD_PGF = "build_pgf"
    COMPARE_PREVIOUS = "compare_previous"
    EVALUATE_RELEASE_GATES = "evaluate_release_gates"
    WRITE_REPORTS = "write_reports"
    WRITE_MANIFEST = "write_manifest"


@unique
class StageRequirement(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    SKIPPED = "skipped"


@runtime_checkable
class PreflightFacts(Protocol):
    gf_available: bool
    version_compatible: bool
    pgf_supported: bool


@dataclass(frozen=True, slots=True)
class PlannedStage:
    stage_id: StageId
    requirement: StageRequirement
    prerequisites: tuple[StageId, ...] = ()
    timeout_sec: int | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage_id, StageId):
            raise TypeError("stage_id must be a StageId")
        if not isinstance(self.requirement, StageRequirement):
            raise TypeError("requirement must be a StageRequirement")
        if not isinstance(self.prerequisites, tuple):
            raise TypeError("prerequisites must be a tuple")
        if any(not isinstance(item, StageId) for item in self.prerequisites):
            raise TypeError("prerequisites must contain StageId values")
        if len(set(self.prerequisites)) != len(self.prerequisites):
            raise ValueError("prerequisites must not contain duplicates")
        if self.stage_id in self.prerequisites:
            raise ValueError("a stage cannot depend on itself")
        if self.timeout_sec is not None:
            if isinstance(self.timeout_sec, bool) or not isinstance(self.timeout_sec, int):
                raise TypeError("timeout_sec must be an integer or None")
            if self.timeout_sec < 1:
                raise ValueError("timeout_sec must be positive")
        if self.reason is not None:
            if not isinstance(self.reason, str):
                raise TypeError("reason must be a string or None")
            if not self.reason.strip():
                raise ValueError("reason must not be blank")
            if "\x00" in self.reason:
                raise ValueError("reason must not contain NUL")
        if self.requirement is StageRequirement.SKIPPED and self.reason is None:
            raise ValueError("skipped stages require a reason")
        if self.requirement is not StageRequirement.SKIPPED and self.reason:
            raise ValueError("enabled stages must not have a skip reason")

    @property
    def enabled(self) -> bool:
        return self.requirement is not StageRequirement.SKIPPED

    @property
    def required(self) -> bool:
        return self.requirement is StageRequirement.REQUIRED


@dataclass(frozen=True, slots=True)
class RunPlan:
    mode: ValidationMode
    target: ValidationTarget | None
    stages: tuple[PlannedStage, ...]
    selected_checkpoints: tuple[Path, ...]
    selected_entrypoints: tuple[Path, ...]
    selected_scenarios: tuple[str, ...]
    compare_previous: bool
    build_pgf: bool
    evidence_level: str
    release_eligible: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        if self.target is not None and not isinstance(self.target, ValidationTarget):
            raise TypeError("target must be a ValidationTarget or None")
        if not isinstance(self.stages, tuple):
            raise TypeError("stages must be a tuple")
        if not self.stages:
            raise ValueError("stages must not be empty")
        if any(not isinstance(stage, PlannedStage) for stage in self.stages):
            raise TypeError("stages must contain PlannedStage values")

        stage_ids = tuple(stage.stage_id for stage in self.stages)
        if len(set(stage_ids)) != len(stage_ids):
            raise ValueError("stage IDs must be unique")

        positions = {stage_id: index for index, stage_id in enumerate(stage_ids)}
        for stage in self.stages:
            for prerequisite in stage.prerequisites:
                if prerequisite not in positions:
                    raise ValueError(
                        f"{stage.stage_id.value} references an absent prerequisite "
                        f"{prerequisite.value}"
                    )
                if positions[prerequisite] >= positions[stage.stage_id]:
                    raise ValueError(f"{prerequisite.value} must precede {stage.stage_id.value}")

        for name, values, expected_type in (
            ("selected_checkpoints", self.selected_checkpoints, Path),
            ("selected_entrypoints", self.selected_entrypoints, Path),
            ("selected_scenarios", self.selected_scenarios, str),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            if any(not isinstance(value, expected_type) for value in values):
                raise TypeError(f"{name} contains an invalid {expected_type.__name__} value")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must not contain duplicates")

        if any(not value for value in self.selected_scenarios):
            raise ValueError("selected_scenarios must not contain empty IDs")
        if type(self.compare_previous) is not bool:
            raise TypeError("compare_previous must be a bool")
        if type(self.build_pgf) is not bool:
            raise TypeError("build_pgf must be a bool")
        if type(self.release_eligible) is not bool:
            raise TypeError("release_eligible must be a bool")
        if not isinstance(self.evidence_level, str):
            raise TypeError("evidence_level must be a string")
        if not self.evidence_level:
            raise ValueError("evidence_level must not be empty")
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple")
        if any(not isinstance(value, str) or not value for value in self.warnings):
            raise ValueError("warnings must contain non-empty strings")

        if self.release_eligible and self.mode is not ValidationMode.RELEASE:
            raise ValueError("only release mode may be release-eligible")
        if self.release_eligible and not self.build_pgf:
            raise ValueError("release eligibility requires a PGF build")

    @property
    def selected_stage_ids(self) -> tuple[StageId, ...]:
        return tuple(stage.stage_id for stage in self.stages if stage.enabled)

    @property
    def required_stage_ids(self) -> tuple[StageId, ...]:
        return tuple(stage.stage_id for stage in self.stages if stage.required)

    @property
    def skipped_stage_ids(self) -> tuple[StageId, ...]:
        return tuple(
            stage.stage_id for stage in self.stages if stage.requirement is StageRequirement.SKIPPED
        )

    def stage(self, stage_id: StageId) -> PlannedStage:
        if not isinstance(stage_id, StageId):
            raise TypeError("stage_id must be a StageId")
        for stage in self.stages:
            if stage.stage_id is stage_id:
                return stage
        raise KeyError(stage_id.value)


_STAGE_ORDER: Final[tuple[StageId, ...]] = (
    StageId.CONFIGURATION,
    StageId.ENVIRONMENT,
    StageId.VERSION_PROBE,
    StageId.SELECTION,
    StageId.STATIC_SCAN,
    StageId.FINGERPRINT,
    StageId.COMPILE_SOURCES,
    StageId.COMPILE_CHECKPOINTS,
    StageId.COMPILE_ENTRYPOINTS,
    StageId.CLASSIFY_FAILURES,
    StageId.RUN_SCENARIOS,
    StageId.NORMALIZE_OUTPUTS,
    StageId.EVALUATE_ASSERTIONS,
    StageId.COMPARE_GOLD,
    StageId.BUILD_PGF,
    StageId.COMPARE_PREVIOUS,
    StageId.EVALUATE_RELEASE_GATES,
    StageId.WRITE_REPORTS,
    StageId.WRITE_MANIFEST,
)

_PREREQUISITES: Final[dict[StageId, tuple[StageId, ...]]] = {
    StageId.ENVIRONMENT: (StageId.CONFIGURATION,),
    StageId.VERSION_PROBE: (StageId.ENVIRONMENT,),
    StageId.SELECTION: (StageId.CONFIGURATION,),
    StageId.STATIC_SCAN: (StageId.SELECTION,),
    StageId.FINGERPRINT: (StageId.SELECTION,),
    StageId.COMPILE_SOURCES: (
        StageId.SELECTION,
        StageId.FINGERPRINT,
    ),
    StageId.COMPILE_CHECKPOINTS: (
        StageId.SELECTION,
        StageId.FINGERPRINT,
    ),
    StageId.COMPILE_ENTRYPOINTS: (
        StageId.SELECTION,
        StageId.FINGERPRINT,
    ),
    StageId.CLASSIFY_FAILURES: (StageId.SELECTION,),
    StageId.RUN_SCENARIOS: (StageId.SELECTION,),
    StageId.NORMALIZE_OUTPUTS: (StageId.RUN_SCENARIOS,),
    StageId.EVALUATE_ASSERTIONS: (StageId.NORMALIZE_OUTPUTS,),
    StageId.COMPARE_GOLD: (StageId.NORMALIZE_OUTPUTS,),
    StageId.BUILD_PGF: (StageId.COMPILE_ENTRYPOINTS,),
    StageId.COMPARE_PREVIOUS: (StageId.CLASSIFY_FAILURES,),
    StageId.EVALUATE_RELEASE_GATES: (
        StageId.CLASSIFY_FAILURES,
        StageId.EVALUATE_ASSERTIONS,
        StageId.COMPARE_GOLD,
    ),
    StageId.WRITE_REPORTS: (StageId.CLASSIFY_FAILURES,),
    StageId.WRITE_MANIFEST: (StageId.WRITE_REPORTS,),
}


def resolve_execution_plan(
    request: RunConfig,
    preflight: PreflightFacts | object | None = None,
) -> RunPlan:
    if not isinstance(request, RunConfig):
        raise TypeError("request must be a RunConfig")

    _validate_mode_request(request)
    warnings = list(request.compatibility_warnings)
    enabled = _enabled_stages(request)
    required = _required_stages(request, enabled)
    skip_reasons = _skip_reasons(request, enabled)
    _validate_preflight(request, preflight)

    stages = tuple(
        PlannedStage(
            stage_id=stage_id,
            requirement=(
                StageRequirement.REQUIRED
                if stage_id in required
                else StageRequirement.OPTIONAL
                if stage_id in enabled
                else StageRequirement.SKIPPED
            ),
            prerequisites=tuple(
                prerequisite
                for prerequisite in _PREREQUISITES.get(stage_id, ())
                if prerequisite in enabled
            ),
            timeout_sec=_stage_timeout(request, stage_id),
            reason=skip_reasons.get(stage_id),
        )
        for stage_id in _STAGE_ORDER
    )

    build_pgf = StageId.BUILD_PGF in enabled
    release_eligible = (
        request.mode is ValidationMode.RELEASE
        and build_pgf
        and StageId.EVALUATE_RELEASE_GATES in required
    )

    if request.mode is not ValidationMode.RELEASE:
        warnings.append(f"{request.mode.value} mode cannot establish release eligibility")

    return RunPlan(
        mode=request.mode,
        target=request.target,
        stages=stages,
        selected_checkpoints=_ordered_paths(request.selected_checkpoints),
        selected_entrypoints=_ordered_paths(request.selected_entrypoints),
        selected_scenarios=_ordered_strings(request.selected_scenarios),
        compare_previous=StageId.COMPARE_PREVIOUS in enabled,
        build_pgf=build_pgf,
        evidence_level=request.evidence_level,
        release_eligible=release_eligible,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _validate_mode_request(request: RunConfig) -> None:
    mode = request.mode
    target = request.target

    if mode is ValidationMode.QUICK:
        if target is None:
            raise ValueError("quick mode requires an explicit target")
        if target.kind not in {TargetKind.FILE, TargetKind.MODULE}:
            raise ValueError("quick mode requires a file or module target")
        if request.selected_checkpoints:
            raise ValueError("quick mode does not accept checkpoints")
        if request.max_files:
            raise ValueError("quick mode does not accept max_files")
        if request.no_compile:
            raise ValueError("quick mode cannot disable compilation")

    elif mode is ValidationMode.CHECKPOINT:
        if target is not None and target.kind is not TargetKind.CHECKPOINT:
            raise ValueError("checkpoint mode requires a checkpoint target")
        if not request.selected_checkpoints:
            raise ValueError("checkpoint mode requires selected checkpoints")
        if request.max_files:
            raise ValueError("checkpoint mode does not accept max_files")
        if request.no_compile:
            raise ValueError("checkpoint mode cannot disable compilation")

    elif mode is ValidationMode.RELEASE:
        if target is not None and target.kind not in {
            TargetKind.PROJECT,
            TargetKind.ENTRYPOINT,
        }:
            raise ValueError("release mode requires a project or entrypoint target")
        if request.skip_version_probe:
            raise ValueError("release mode cannot skip the version probe")
        if request.no_compile:
            raise ValueError("release mode cannot disable compilation")
        if request.max_files:
            raise ValueError("release mode cannot limit selected files")
        if not request.selected_entrypoints:
            raise ValueError("release mode requires selected entrypoints")
        if not request.selected_scenarios:
            raise ValueError("release mode requires selected scenarios")
        if not request.release_requires_pgf:
            raise ValueError("release mode requires PGF verification")

    elif mode is ValidationMode.DIAGNOSTIC:
        if target is not None and target.kind is TargetKind.REGRESSION:
            raise ValueError("regression is not an executable diagnostic target")

    else:
        raise ValueError(f"unsupported validation mode: {mode!r}")


def _enabled_stages(request: RunConfig) -> frozenset[StageId]:
    enabled: set[StageId] = {
        StageId.CONFIGURATION,
        StageId.ENVIRONMENT,
        StageId.SELECTION,
        StageId.STATIC_SCAN,
        StageId.FINGERPRINT,
        StageId.CLASSIFY_FAILURES,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    }

    if not request.skip_version_probe:
        enabled.add(StageId.VERSION_PROBE)

    if not request.no_compile:
        enabled.add(StageId.COMPILE_SOURCES)

    if request.selected_checkpoints and not request.no_compile:
        enabled.add(StageId.COMPILE_CHECKPOINTS)

    if request.selected_entrypoints and not request.no_compile:
        enabled.add(StageId.COMPILE_ENTRYPOINTS)

    if request.selected_scenarios:
        enabled.update(
            {
                StageId.RUN_SCENARIOS,
                StageId.NORMALIZE_OUTPUTS,
                StageId.EVALUATE_ASSERTIONS,
                StageId.COMPARE_GOLD,
            }
        )

    if request.release_requires_pgf and request.selected_entrypoints and not request.no_compile:
        enabled.add(StageId.BUILD_PGF)

    if request.diff_previous:
        enabled.add(StageId.COMPARE_PREVIOUS)

    if request.mode is ValidationMode.RELEASE:
        enabled.add(StageId.EVALUATE_RELEASE_GATES)

    return frozenset(enabled)


def _required_stages(
    request: RunConfig,
    enabled: frozenset[StageId],
) -> frozenset[StageId]:
    required: set[StageId] = {
        StageId.CONFIGURATION,
        StageId.ENVIRONMENT,
        StageId.SELECTION,
        StageId.STATIC_SCAN,
        StageId.FINGERPRINT,
        StageId.CLASSIFY_FAILURES,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    }

    if StageId.VERSION_PROBE in enabled:
        required.add(StageId.VERSION_PROBE)

    if not request.no_compile:
        required.add(StageId.COMPILE_SOURCES)

    if (
        request.mode
        in {
            ValidationMode.CHECKPOINT,
            ValidationMode.RELEASE,
        }
        and StageId.COMPILE_CHECKPOINTS in enabled
    ):
        required.add(StageId.COMPILE_CHECKPOINTS)

    if request.mode is ValidationMode.RELEASE:
        required.update(
            {
                StageId.COMPILE_ENTRYPOINTS,
                StageId.RUN_SCENARIOS,
                StageId.NORMALIZE_OUTPUTS,
                StageId.EVALUATE_ASSERTIONS,
                StageId.COMPARE_GOLD,
                StageId.BUILD_PGF,
                StageId.EVALUATE_RELEASE_GATES,
            }
        )

    if request.mode is ValidationMode.CHECKPOINT and request.selected_scenarios:
        required.update(
            {
                StageId.RUN_SCENARIOS,
                StageId.NORMALIZE_OUTPUTS,
                StageId.EVALUATE_ASSERTIONS,
                StageId.COMPARE_GOLD,
            }
        )

    return frozenset(required & enabled)


def _skip_reasons(
    request: RunConfig,
    enabled: frozenset[StageId],
) -> dict[StageId, str]:
    reasons: dict[StageId, str] = {}

    for stage_id in _STAGE_ORDER:
        if stage_id in enabled:
            continue
        if stage_id is StageId.VERSION_PROBE:
            reasons[stage_id] = "disabled by the resolved skip-version-probe policy"
        elif stage_id in {
            StageId.COMPILE_SOURCES,
            StageId.COMPILE_CHECKPOINTS,
            StageId.COMPILE_ENTRYPOINTS,
        }:
            reasons[stage_id] = (
                "compilation is disabled"
                if request.no_compile
                else "no applicable compile subjects were selected"
            )
        elif stage_id in {
            StageId.RUN_SCENARIOS,
            StageId.NORMALIZE_OUTPUTS,
            StageId.EVALUATE_ASSERTIONS,
            StageId.COMPARE_GOLD,
        }:
            reasons[stage_id] = "no scenarios were selected"
        elif stage_id is StageId.BUILD_PGF:
            reasons[stage_id] = "PGF construction is not required by this plan"
        elif stage_id is StageId.COMPARE_PREVIOUS:
            reasons[stage_id] = "previous-run comparison is disabled"
        elif stage_id is StageId.EVALUATE_RELEASE_GATES:
            reasons[stage_id] = "release gates apply only to release mode"
        else:
            reasons[stage_id] = "stage is not applicable to the resolved plan"

    return reasons


def _validate_preflight(
    request: RunConfig,
    preflight: PreflightFacts | object | None,
) -> None:
    if preflight is None:
        return

    gf_available = getattr(preflight, "gf_available", True)
    version_compatible = getattr(preflight, "version_compatible", True)
    pgf_supported = getattr(preflight, "pgf_supported", True)

    for name, value in (
        ("gf_available", gf_available),
        ("version_compatible", version_compatible),
        ("pgf_supported", pgf_supported),
    ):
        if type(value) is not bool:
            raise TypeError(f"preflight.{name} must be a bool")

    if not gf_available and not request.no_compile:
        raise ValueError("GF is unavailable for the resolved execution plan")
    if request.mode is ValidationMode.RELEASE and not version_compatible:
        raise ValueError("release mode requires a compatible GF version")
    if (
        request.mode is ValidationMode.RELEASE
        and request.release_requires_pgf
        and not pgf_supported
    ):
        raise ValueError("release mode requires supported PGF construction")


def _stage_timeout(
    request: RunConfig,
    stage_id: StageId,
) -> int | None:
    if stage_id in {
        StageId.VERSION_PROBE,
        StageId.COMPILE_SOURCES,
        StageId.COMPILE_CHECKPOINTS,
        StageId.COMPILE_ENTRYPOINTS,
        StageId.RUN_SCENARIOS,
        StageId.BUILD_PGF,
    }:
        return request.timeout_sec
    return None


def _ordered_paths(values: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(
        sorted(
            dict.fromkeys(values),
            key=lambda value: value.as_posix().casefold(),
        )
    )


def _ordered_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(values), key=str.casefold))


__all__ = (
    "PlannedStage",
    "PreflightFacts",
    "RunPlan",
    "StageId",
    "StageRequirement",
    "resolve_execution_plan",
)
