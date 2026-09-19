from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from gf_wordbench.kernel.statuses import ValidationMode

ValidationStageId: TypeAlias = Literal[
    "configuration",
    "environment",
    "version_probe",
    "selection",
    "static_scan",
    "fingerprint",
    "compile_files",
    "compile_checkpoints",
    "compile_entrypoints",
    "build_pgf",
    "run_scenarios",
    "normalize_outputs",
    "evaluate_assertions",
    "compare_gold",
    "classify_failures",
    "compare_previous",
    "evaluate_release_gates",
    "write_reports",
    "write_manifest",
    "verify_manifest",
]

ModeTargetKind: TypeAlias = Literal[
    "file",
    "module",
    "checkpoint",
    "entrypoint",
    "scenario",
    "project",
    "regression",
]

EvidencePolicy: TypeAlias = Literal[
    "bounded",
    "standard",
    "complete",
    "expanded",
]

ModeOverrideName: TypeAlias = Literal[
    "target",
    "extra_target",
    "extra_checkpoint",
    "extra_entrypoint",
    "extra_scenario",
    "timeout_increase",
    "keep_full_details",
    "diff_previous",
    "skip_version_probe",
    "scan_only",
    "no_compile",
    "skip_required_scenarios",
    "skip_required_gold",
    "skip_required_pgf",
    "skip_manifest",
    "ignore_blocking_issues",
    "strict_scan_policy",
    "manifest_verification",
    "expanded_evidence",
]

ModeConditionKey: TypeAlias = Literal[
    "target_is_scenario",
    "checkpoints_selected",
    "entrypoints_selected",
    "scenarios_selected",
    "gold_comparison_required",
    "release_requires_pgf",
    "compatible_history_exists",
    "manifest_requested",
    "manifest_verification_requested",
]

VALIDATION_MODE_CONTRACT_VERSION: Final[str] = "1.0.0"

CANONICAL_VALIDATION_STAGES: Final[tuple[ValidationStageId, ...]] = (
    "configuration",
    "environment",
    "version_probe",
    "selection",
    "static_scan",
    "fingerprint",
    "compile_files",
    "compile_checkpoints",
    "compile_entrypoints",
    "build_pgf",
    "run_scenarios",
    "normalize_outputs",
    "evaluate_assertions",
    "compare_gold",
    "classify_failures",
    "compare_previous",
    "evaluate_release_gates",
    "write_reports",
    "write_manifest",
    "verify_manifest",
)

CANONICAL_VALIDATION_MODES: Final[tuple[ValidationMode, ...]] = (
    ValidationMode.QUICK,
    ValidationMode.CHECKPOINT,
    ValidationMode.RELEASE,
    ValidationMode.DIAGNOSTIC,
)

LEGACY_VALIDATION_MODE_ALIASES: Final[Mapping[str, ValidationMode]] = {
    "file": ValidationMode.QUICK,
    "all": ValidationMode.DIAGNOSTIC,
}


# Early validation helpers are intentionally defined before the module-level
# policy registry.  Dataclass instances are constructed while this module is
# imported, so their __post_init__ methods must not depend on functions defined
# later in the file.
def _require_stage(value: object) -> ValidationStageId:
    if not isinstance(value, str):
        raise TypeError("validation stage must be a string")
    if value not in CANONICAL_VALIDATION_STAGES:
        raise ValueError(f"unsupported validation stage {value!r}")
    return value


def _require_target_kind(value: object) -> ModeTargetKind:
    if not isinstance(value, str):
        raise TypeError("target kind must be a string")
    allowed = {"file", "module", "checkpoint", "entrypoint", "scenario", "project", "regression"}
    if value not in allowed:
        raise ValueError(f"unsupported target kind {value!r}")
    return cast("ModeTargetKind", value)


def _require_override(value: object) -> ModeOverrideName:
    if not isinstance(value, str):
        raise TypeError("override name must be a string")
    allowed = {
        "target",
        "extra_target",
        "extra_checkpoint",
        "extra_entrypoint",
        "extra_scenario",
        "timeout_increase",
        "keep_full_details",
        "diff_previous",
        "skip_version_probe",
        "scan_only",
        "no_compile",
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
        "strict_scan_policy",
        "manifest_verification",
        "expanded_evidence",
    }
    if value not in allowed:
        raise ValueError(f"unsupported override name {value!r}")
    return cast("ModeOverrideName", value)


def _require_condition(value: object) -> ModeConditionKey:
    if not isinstance(value, str):
        raise TypeError("condition must be a string")
    allowed = {
        "target_is_scenario",
        "checkpoints_selected",
        "entrypoints_selected",
        "scenarios_selected",
        "gold_comparison_required",
        "release_requires_pgf",
        "compatible_history_exists",
        "manifest_requested",
        "manifest_verification_requested",
    }
    if value not in allowed:
        raise ValueError(f"unsupported mode condition {value!r}")
    return cast("ModeConditionKey", value)


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _normalize_stages(
    values: Iterable[ValidationStageId], *, field_name: str
) -> tuple[ValidationStageId, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of stages")
    normalized = tuple(values)
    for value in normalized:
        _require_stage(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicate stages")
    return normalized


def _normalize_target_kinds(values: Iterable[ModeTargetKind]) -> tuple[ModeTargetKind, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("allowed_target_kinds must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        _require_target_kind(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError("allowed_target_kinds must not contain duplicates")
    return normalized


def _normalize_overrides(
    values: Iterable[ModeOverrideName], *, field_name: str
) -> tuple[ModeOverrideName, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of override names")
    normalized = tuple(values)
    for value in normalized:
        _require_override(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicate overrides")
    return normalized


@dataclass(frozen=True, slots=True)
class ConditionalStage:
    stage: ValidationStageId
    condition: ModeConditionKey
    required_when_active: bool = True

    def __post_init__(self) -> None:
        _require_stage(self.stage)
        _require_condition(self.condition)
        if not isinstance(self.required_when_active, bool):
            raise TypeError("required_when_active must be a bool")


@dataclass(frozen=True, slots=True)
class ModePolicy:
    mode: ValidationMode
    purpose: str
    evidence_policy: EvidencePolicy
    release_eligible: bool
    target_required: bool
    full_project_scope: bool
    continue_after_independent_failure: bool
    required_stages: tuple[ValidationStageId, ...]
    conditional_stages: tuple[ConditionalStage, ...] = ()
    recommended_stages: tuple[ValidationStageId, ...] = ()
    optional_stages: tuple[ValidationStageId, ...] = ()
    allowed_target_kinds: tuple[ModeTargetKind, ...] = ()
    allowed_overrides: tuple[ModeOverrideName, ...] = ()
    prohibited_overrides: tuple[ModeOverrideName, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        _require_text(self.purpose, field_name="purpose")
        if self.evidence_policy not in {
            "bounded",
            "standard",
            "complete",
            "expanded",
        }:
            raise ValueError("unsupported evidence_policy")
        for field_name in (
            "release_eligible",
            "target_required",
            "full_project_scope",
            "continue_after_independent_failure",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")

        required = _normalize_stages(
            self.required_stages,
            field_name="required_stages",
        )
        recommended = _normalize_stages(
            self.recommended_stages,
            field_name="recommended_stages",
        )
        optional = _normalize_stages(
            self.optional_stages,
            field_name="optional_stages",
        )
        conditional = tuple(self.conditional_stages)

        if not all(isinstance(item, ConditionalStage) for item in conditional):
            raise TypeError("conditional_stages must contain ConditionalStage values")

        conditional_ids = tuple(item.stage for item in conditional)
        if len(conditional_ids) != len(set(conditional_ids)):
            raise ValueError("conditional_stages must not contain duplicate stages")

        all_declared = (
            *required,
            *conditional_ids,
            *recommended,
            *optional,
        )
        if len(all_declared) != len(set(all_declared)):
            raise ValueError("a stage may appear in only one mode-policy category")

        target_kinds = _normalize_target_kinds(self.allowed_target_kinds)
        allowed_overrides = _normalize_overrides(
            self.allowed_overrides,
            field_name="allowed_overrides",
        )
        prohibited_overrides = _normalize_overrides(
            self.prohibited_overrides,
            field_name="prohibited_overrides",
        )

        overlap = set(allowed_overrides).intersection(prohibited_overrides)
        if overlap:
            raise ValueError(
                "overrides cannot be both allowed and prohibited: " + ", ".join(sorted(overlap))
            )

        if self.target_required and not target_kinds:
            raise ValueError("target_required policies must allow target kinds")
        if self.release_eligible and self.mode is not ValidationMode.RELEASE:
            raise ValueError("only release mode may be release eligible")
        if self.mode is ValidationMode.RELEASE and not self.full_project_scope:
            raise ValueError("release mode must use full project scope")
        if self.mode is ValidationMode.RELEASE and "evaluate_release_gates" not in required:
            raise ValueError("release mode must require release-gate evaluation")
        if self.mode is ValidationMode.RELEASE and "verify_manifest" not in required:
            raise ValueError("release mode must require manifest verification")

        object.__setattr__(self, "required_stages", required)
        object.__setattr__(
            self,
            "conditional_stages",
            conditional,
        )
        object.__setattr__(
            self,
            "recommended_stages",
            recommended,
        )
        object.__setattr__(self, "optional_stages", optional)
        object.__setattr__(
            self,
            "allowed_target_kinds",
            target_kinds,
        )
        object.__setattr__(
            self,
            "allowed_overrides",
            allowed_overrides,
        )
        object.__setattr__(
            self,
            "prohibited_overrides",
            prohibited_overrides,
        )


@dataclass(frozen=True, slots=True)
class ModeContext:
    target_kind: ModeTargetKind | None = None
    checkpoints_selected: bool = False
    entrypoints_selected: bool = False
    scenarios_selected: bool = False
    gold_comparison_required: bool = False
    release_requires_pgf: bool = False
    compatible_history_exists: bool = False
    manifest_requested: bool = False
    manifest_verification_requested: bool = False

    def __post_init__(self) -> None:
        if self.target_kind is not None:
            _require_target_kind(self.target_kind)
        for field_name in (
            "checkpoints_selected",
            "entrypoints_selected",
            "scenarios_selected",
            "gold_comparison_required",
            "release_requires_pgf",
            "compatible_history_exists",
            "manifest_requested",
            "manifest_verification_requested",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")

    def condition_values(self) -> Mapping[ModeConditionKey, bool]:
        return {
            "target_is_scenario": self.target_kind == "scenario",
            "checkpoints_selected": self.checkpoints_selected,
            "entrypoints_selected": self.entrypoints_selected,
            "scenarios_selected": self.scenarios_selected,
            "gold_comparison_required": self.gold_comparison_required,
            "release_requires_pgf": self.release_requires_pgf,
            "compatible_history_exists": (self.compatible_history_exists),
            "manifest_requested": self.manifest_requested,
            "manifest_verification_requested": (self.manifest_verification_requested),
        }


@dataclass(frozen=True, slots=True)
class ModeStageResolution:
    mode: ValidationMode
    required_stages: tuple[ValidationStageId, ...]
    recommended_stages: tuple[ValidationStageId, ...]
    optional_stages: tuple[ValidationStageId, ...]
    inactive_conditional_stages: tuple[ValidationStageId, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")

        required = _normalize_stages(
            self.required_stages,
            field_name="required_stages",
        )
        recommended = _normalize_stages(
            self.recommended_stages,
            field_name="recommended_stages",
        )
        optional = _normalize_stages(
            self.optional_stages,
            field_name="optional_stages",
        )
        inactive = _normalize_stages(
            self.inactive_conditional_stages,
            field_name="inactive_conditional_stages",
        )

        all_stages = (
            *required,
            *recommended,
            *optional,
            *inactive,
        )
        if len(all_stages) != len(set(all_stages)):
            raise ValueError("resolved stage categories must not overlap")

        object.__setattr__(self, "required_stages", required)
        object.__setattr__(
            self,
            "recommended_stages",
            recommended,
        )
        object.__setattr__(self, "optional_stages", optional)
        object.__setattr__(
            self,
            "inactive_conditional_stages",
            inactive,
        )


@dataclass(frozen=True, slots=True)
class ModeOverrideViolation:
    override: ModeOverrideName
    message: str

    def __post_init__(self) -> None:
        _require_override(self.override)
        _require_text(self.message, field_name="message")


_QUICK_POLICY: Final[ModePolicy] = ModePolicy(
    mode=ValidationMode.QUICK,
    purpose=(
        "Provide fast, focused feedback for a bounded development "
        "target without creating release evidence."
    ),
    evidence_policy="bounded",
    release_eligible=False,
    target_required=True,
    full_project_scope=False,
    continue_after_independent_failure=False,
    required_stages=(
        "configuration",
        "environment",
        "version_probe",
        "selection",
        "static_scan",
        "fingerprint",
        "compile_files",
        "classify_failures",
        "write_reports",
    ),
    conditional_stages=(
        ConditionalStage(
            stage="run_scenarios",
            condition="target_is_scenario",
        ),
        ConditionalStage(
            stage="normalize_outputs",
            condition="target_is_scenario",
        ),
        ConditionalStage(
            stage="evaluate_assertions",
            condition="target_is_scenario",
        ),
        ConditionalStage(
            stage="compare_gold",
            condition="gold_comparison_required",
        ),
    ),
    optional_stages=(
        "compile_checkpoints",
        "compile_entrypoints",
        "compare_previous",
        "write_manifest",
        "verify_manifest",
    ),
    allowed_target_kinds=(
        "file",
        "module",
        "entrypoint",
        "scenario",
    ),
    allowed_overrides=(
        "target",
        "extra_target",
        "extra_checkpoint",
        "extra_entrypoint",
        "extra_scenario",
        "timeout_increase",
        "keep_full_details",
        "diff_previous",
        "skip_version_probe",
        "scan_only",
        "no_compile",
        "strict_scan_policy",
        "manifest_verification",
        "expanded_evidence",
    ),
    prohibited_overrides=(
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
    ),
)

_CHECKPOINT_POLICY: Final[ModePolicy] = ModePolicy(
    mode=ValidationMode.CHECKPOINT,
    purpose=(
        "Validate one or more configured development checkpoints "
        "with their prerequisite closure and required evidence."
    ),
    evidence_policy="standard",
    release_eligible=False,
    target_required=True,
    full_project_scope=False,
    continue_after_independent_failure=False,
    required_stages=(
        "configuration",
        "environment",
        "version_probe",
        "selection",
        "static_scan",
        "fingerprint",
        "compile_files",
        "compile_checkpoints",
        "compile_entrypoints",
        "run_scenarios",
        "normalize_outputs",
        "evaluate_assertions",
        "compare_gold",
        "classify_failures",
        "write_reports",
    ),
    recommended_stages=(
        "compare_previous",
        "write_manifest",
        "verify_manifest",
    ),
    optional_stages=("build_pgf",),
    allowed_target_kinds=("checkpoint",),
    allowed_overrides=(
        "target",
        "extra_checkpoint",
        "extra_entrypoint",
        "extra_scenario",
        "timeout_increase",
        "keep_full_details",
        "diff_previous",
        "strict_scan_policy",
        "manifest_verification",
        "expanded_evidence",
    ),
    prohibited_overrides=(
        "skip_version_probe",
        "scan_only",
        "no_compile",
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
    ),
)

_RELEASE_POLICY: Final[ModePolicy] = ModePolicy(
    mode=ValidationMode.RELEASE,
    purpose=(
        "Produce complete reproducible evidence and decide whether "
        "the active project satisfies every configured release "
        "requirement."
    ),
    evidence_policy="complete",
    release_eligible=True,
    target_required=False,
    full_project_scope=True,
    continue_after_independent_failure=False,
    required_stages=(
        "configuration",
        "environment",
        "version_probe",
        "selection",
        "static_scan",
        "fingerprint",
        "compile_files",
        "compile_checkpoints",
        "compile_entrypoints",
        "run_scenarios",
        "normalize_outputs",
        "evaluate_assertions",
        "compare_gold",
        "classify_failures",
        "evaluate_release_gates",
        "write_reports",
        "write_manifest",
        "verify_manifest",
    ),
    conditional_stages=(
        ConditionalStage(
            stage="build_pgf",
            condition="release_requires_pgf",
        ),
        ConditionalStage(
            stage="compare_previous",
            condition="compatible_history_exists",
        ),
    ),
    allowed_target_kinds=("project",),
    allowed_overrides=(
        "extra_target",
        "extra_checkpoint",
        "extra_entrypoint",
        "extra_scenario",
        "timeout_increase",
        "keep_full_details",
        "strict_scan_policy",
        "expanded_evidence",
    ),
    prohibited_overrides=(
        "target",
        "skip_version_probe",
        "scan_only",
        "no_compile",
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
    ),
)

_DIAGNOSTIC_POLICY: Final[ModePolicy] = ModePolicy(
    mode=ValidationMode.DIAGNOSTIC,
    purpose=(
        "Maximize actionable evidence and causal understanding for "
        "complex, cascading, intermittent, or poorly classified "
        "failures."
    ),
    evidence_policy="expanded",
    release_eligible=False,
    target_required=False,
    full_project_scope=False,
    continue_after_independent_failure=True,
    required_stages=(
        "configuration",
        "environment",
        "version_probe",
        "selection",
        "static_scan",
        "fingerprint",
        "compile_files",
        "classify_failures",
        "write_reports",
    ),
    conditional_stages=(
        ConditionalStage(
            stage="compile_checkpoints",
            condition="checkpoints_selected",
        ),
        ConditionalStage(
            stage="compile_entrypoints",
            condition="entrypoints_selected",
        ),
        ConditionalStage(
            stage="run_scenarios",
            condition="scenarios_selected",
        ),
        ConditionalStage(
            stage="normalize_outputs",
            condition="scenarios_selected",
        ),
        ConditionalStage(
            stage="evaluate_assertions",
            condition="scenarios_selected",
        ),
        ConditionalStage(
            stage="compare_gold",
            condition="gold_comparison_required",
        ),
        ConditionalStage(
            stage="build_pgf",
            condition="release_requires_pgf",
            required_when_active=False,
        ),
        ConditionalStage(
            stage="compare_previous",
            condition="compatible_history_exists",
            required_when_active=False,
        ),
        ConditionalStage(
            stage="write_manifest",
            condition="manifest_requested",
            required_when_active=False,
        ),
        ConditionalStage(
            stage="verify_manifest",
            condition="manifest_verification_requested",
            required_when_active=False,
        ),
    ),
    allowed_target_kinds=(
        "file",
        "module",
        "checkpoint",
        "entrypoint",
        "scenario",
        "project",
        "regression",
    ),
    allowed_overrides=(
        "target",
        "extra_target",
        "extra_checkpoint",
        "extra_entrypoint",
        "extra_scenario",
        "timeout_increase",
        "keep_full_details",
        "diff_previous",
        "skip_version_probe",
        "scan_only",
        "no_compile",
        "strict_scan_policy",
        "manifest_verification",
        "expanded_evidence",
    ),
    prohibited_overrides=(
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
    ),
)

MODE_POLICIES: Final[Mapping[ValidationMode, ModePolicy]] = {
    ValidationMode.QUICK: _QUICK_POLICY,
    ValidationMode.CHECKPOINT: _CHECKPOINT_POLICY,
    ValidationMode.RELEASE: _RELEASE_POLICY,
    ValidationMode.DIAGNOSTIC: _DIAGNOSTIC_POLICY,
}


def parse_validation_mode(
    value: object,
    *,
    allow_legacy_aliases: bool = False,
) -> ValidationMode:
    if not isinstance(allow_legacy_aliases, bool):
        raise TypeError("allow_legacy_aliases must be a bool")
    if isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise TypeError("validation mode must be a ValidationMode or string")

    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError("validation mode must not be empty")

    try:
        return ValidationMode(normalized)
    except ValueError:
        if allow_legacy_aliases:
            migrated = LEGACY_VALIDATION_MODE_ALIASES.get(normalized)
            if migrated is not None:
                return migrated
        raise ValueError(f"unsupported validation mode {value!r}") from None


def migrate_legacy_validation_mode(
    value: object,
) -> tuple[ValidationMode, bool]:
    if isinstance(value, ValidationMode):
        return value, False
    if not isinstance(value, str):
        raise TypeError("validation mode must be a ValidationMode or string")

    normalized = value.strip().casefold()
    migrated = LEGACY_VALIDATION_MODE_ALIASES.get(normalized)
    if migrated is not None:
        return migrated, True
    return parse_validation_mode(normalized), False


def validation_mode_name(
    value: object,
    *,
    allow_legacy_aliases: bool = False,
) -> str:
    return parse_validation_mode(
        value,
        allow_legacy_aliases=allow_legacy_aliases,
    ).value


def get_mode_policy(
    mode: object,
    *,
    allow_legacy_aliases: bool = False,
) -> ModePolicy:
    normalized = parse_validation_mode(
        mode,
        allow_legacy_aliases=allow_legacy_aliases,
    )
    return MODE_POLICIES[normalized]


def resolve_mode_stages(
    mode: object,
    context: ModeContext | None = None,
    *,
    allow_legacy_aliases: bool = False,
) -> ModeStageResolution:
    policy = get_mode_policy(
        mode,
        allow_legacy_aliases=allow_legacy_aliases,
    )
    resolved_context = ModeContext() if context is None else context
    if not isinstance(resolved_context, ModeContext):
        raise TypeError("context must be a ModeContext or None")

    condition_values = resolved_context.condition_values()
    required = list(policy.required_stages)
    recommended = list(policy.recommended_stages)
    optional = list(policy.optional_stages)
    inactive: list[ValidationStageId] = []

    for conditional in policy.conditional_stages:
        active = condition_values[conditional.condition]
        if not active:
            inactive.append(conditional.stage)
            continue
        destination = required if conditional.required_when_active else recommended
        destination.append(conditional.stage)

    if policy.mode is ValidationMode.QUICK and resolved_context.target_kind == "scenario":
        required = [
            stage
            for stage in required
            if stage
            not in {
                "static_scan",
                "fingerprint",
                "compile_files",
                "classify_failures",
            }
        ]

    return ModeStageResolution(
        mode=policy.mode,
        required_stages=_canonical_stage_order(required),
        recommended_stages=_canonical_stage_order(recommended),
        optional_stages=_canonical_stage_order(optional),
        inactive_conditional_stages=_canonical_stage_order(inactive),
    )


def validate_mode_target(
    mode: object,
    target_kind: ModeTargetKind | None,
    *,
    allow_legacy_aliases: bool = False,
) -> None:
    policy = get_mode_policy(
        mode,
        allow_legacy_aliases=allow_legacy_aliases,
    )
    if target_kind is None:
        if policy.target_required:
            raise ValueError(f"{policy.mode.value} mode requires a target")
        return

    normalized_target = _require_target_kind(target_kind)
    if normalized_target not in policy.allowed_target_kinds:
        raise ValueError(
            f"target kind {normalized_target!r} is not valid for {policy.mode.value} mode"
        )
    if policy.full_project_scope and normalized_target != "project":
        raise ValueError("release mode cannot be narrowed by a target")


def validate_mode_overrides(
    mode: object,
    overrides: Iterable[ModeOverrideName],
    *,
    allow_legacy_aliases: bool = False,
) -> tuple[ModeOverrideViolation, ...]:
    policy = get_mode_policy(
        mode,
        allow_legacy_aliases=allow_legacy_aliases,
    )
    normalized = _normalize_overrides(
        overrides,
        field_name="overrides",
    )
    violations: list[ModeOverrideViolation] = []

    for override in normalized:
        if override in policy.prohibited_overrides:
            violations.append(
                ModeOverrideViolation(
                    override=override,
                    message=(f"{override} is prohibited in {policy.mode.value} mode."),
                )
            )
            continue
        if override not in policy.allowed_overrides:
            violations.append(
                ModeOverrideViolation(
                    override=override,
                    message=(
                        f"{override} is not an accepted override for {policy.mode.value} mode."
                    ),
                )
            )

    return tuple(violations)


def require_valid_mode_overrides(
    mode: object,
    overrides: Iterable[ModeOverrideName],
    *,
    allow_legacy_aliases: bool = False,
) -> None:
    violations = validate_mode_overrides(
        mode,
        overrides,
        allow_legacy_aliases=allow_legacy_aliases,
    )
    if violations:
        raise ValueError("; ".join(item.message for item in violations))


def is_release_eligible_mode(mode: object) -> bool:
    return get_mode_policy(mode).release_eligible


def canonical_mode_names() -> tuple[str, ...]:
    return tuple(mode.value for mode in CANONICAL_VALIDATION_MODES)


def canonical_stage_names() -> tuple[str, ...]:
    return tuple(CANONICAL_VALIDATION_STAGES)


def _canonical_stage_order(
    stages: Iterable[ValidationStageId],
) -> tuple[ValidationStageId, ...]:
    normalized = _normalize_stages(
        stages,
        field_name="stages",
    )
    stage_set = set(normalized)
    return tuple(stage for stage in CANONICAL_VALIDATION_STAGES if stage in stage_set)


__all__ = (
    "CANONICAL_VALIDATION_MODES",
    "CANONICAL_VALIDATION_STAGES",
    "LEGACY_VALIDATION_MODE_ALIASES",
    "MODE_POLICIES",
    "VALIDATION_MODE_CONTRACT_VERSION",
    "ConditionalStage",
    "EvidencePolicy",
    "ModeConditionKey",
    "ModeContext",
    "ModeOverrideName",
    "ModeOverrideViolation",
    "ModePolicy",
    "ModeStageResolution",
    "ModeTargetKind",
    "ValidationStageId",
    "canonical_mode_names",
    "canonical_stage_names",
    "get_mode_policy",
    "is_release_eligible_mode",
    "migrate_legacy_validation_mode",
    "parse_validation_mode",
    "require_valid_mode_overrides",
    "resolve_mode_stages",
    "validate_mode_overrides",
    "validate_mode_target",
    "validation_mode_name",
)
