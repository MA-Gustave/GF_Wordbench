"""Canonical semantic-stage contracts for GF Wordbench validation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.statuses import ValidationMode


@unique
class StageId(StrEnum):
    CONFIGURATION = "configuration"
    ENVIRONMENT = "environment"
    VERSION_PROBE = "version_probe"
    SELECTION = "selection"
    STATIC_SCAN = "static_scan"
    FINGERPRINT = "fingerprint"
    COMPILE_FILES = "compile_files"
    COMPILE_CHECKPOINTS = "compile_checkpoints"
    COMPILE_ENTRYPOINTS = "compile_entrypoints"
    BUILD_PGF = "build_pgf"
    RUN_SCENARIOS = "run_scenarios"
    NORMALIZE_OUTPUTS = "normalize_outputs"
    EVALUATE_ASSERTIONS = "evaluate_assertions"
    COMPARE_GOLD = "compare_gold"
    CLASSIFY_FAILURES = "classify_failures"
    COMPARE_PREVIOUS = "compare_previous"
    EVALUATE_RELEASE_GATES = "evaluate_release_gates"
    WRITE_REPORTS = "write_reports"
    WRITE_MANIFEST = "write_manifest"
    VERIFY_MANIFEST = "verify_manifest"


@unique
class StageRequirement(StrEnum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    NOT_APPLICABLE = "not_applicable"


@unique
class StageOwner(StrEnum):
    CONFIGURATION = "gf_wordbench.config"
    RUNS = "gf_wordbench.runs"
    VALIDATION_SELECTION = "gf_wordbench.validation.selection"
    VALIDATION_SCANNING = "gf_wordbench.validation.scanning"
    VALIDATION_COMPILATION = "gf_wordbench.validation.compilation"
    VALIDATION_SCENARIOS = "gf_wordbench.validation.scenarios"
    VALIDATION_REGRESSION = "gf_wordbench.validation.regression"
    VALIDATION_RELEASE = "gf_wordbench.validation.release"
    DIAGNOSTICS = "gf_wordbench.diagnostics"
    REPORTING = "gf_wordbench.reporting"


@unique
class StageFailurePolicy(StrEnum):
    FATAL_PRECONDITION = "fatal_precondition"
    BLOCK_DEPENDENTS = "block_dependents"
    CONTINUE_INDEPENDENT = "continue_independent"
    AGGREGATE = "aggregate"
    FINALIZE = "finalize"


@unique
class StageEffect(StrEnum):
    READ_PROJECT_CONFIGURATION = "read_project_configuration"
    READ_PROJECT_SOURCE = "read_project_source"
    READ_PROJECT_VALIDATION_ASSET = "read_project_validation_asset"
    READ_RUN_EVIDENCE = "read_run_evidence"
    READ_PREVIOUS_RUN = "read_previous_run"
    EXECUTE_GF = "execute_gf"
    WRITE_RAW_EVIDENCE = "write_raw_evidence"
    WRITE_DERIVED_EVIDENCE = "write_derived_evidence"
    WRITE_REPORT = "write_report"
    WRITE_MANIFEST = "write_manifest"


ModeRequirementMap: TypeAlias = Mapping[ValidationMode, StageRequirement]
StageIdLike: TypeAlias = StageId | str

_ALL_MODES: Final[tuple[ValidationMode, ...]] = tuple(ValidationMode)
_ALL_MODE_SET: Final[frozenset[ValidationMode]] = frozenset(_ALL_MODES)


@dataclass(frozen=True, slots=True)
class StageContract:
    stage_id: StageId
    order: int
    purpose: str
    owner: StageOwner
    mode_requirements: ModeRequirementMap
    required_predecessors: tuple[StageId, ...] = ()
    blocking_predecessors: tuple[StageId, ...] = ()
    ordered_after: tuple[StageId, ...] = ()
    effects: tuple[StageEffect, ...] = ()
    owned_outputs: tuple[str, ...] = ()
    failure_policy: StageFailurePolicy = StageFailurePolicy.CONTINUE_INDEPENDENT
    process_backed: bool = False
    cancellation_aware: bool = False
    preserves_raw_evidence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.stage_id, StageId):
            raise TypeError("stage_id must be StageId")
        if type(self.order) is not int or self.order < 0:
            raise ValueError("order must be a non-negative integer")
        _require_text(self.purpose, field="purpose")
        if not isinstance(self.owner, StageOwner):
            raise TypeError("owner must be StageOwner")
        if not isinstance(self.failure_policy, StageFailurePolicy):
            raise TypeError("failure_policy must be StageFailurePolicy")

        requirements = _freeze_mode_requirements(self.mode_requirements)
        object.__setattr__(self, "mode_requirements", requirements)

        required_predecessors = _stage_tuple(
            self.required_predecessors,
            field="required_predecessors",
            current=self.stage_id,
        )
        blocking_predecessors = _stage_tuple(
            self.blocking_predecessors,
            field="blocking_predecessors",
            current=self.stage_id,
        )
        ordered_after = _stage_tuple(
            self.ordered_after,
            field="ordered_after",
            current=self.stage_id,
        )
        effects = _effect_tuple(self.effects)
        owned_outputs = _text_tuple(self.owned_outputs, field="owned_outputs")

        if not set(blocking_predecessors).issubset(required_predecessors):
            raise ValueError(
                "blocking_predecessors must be a subset of required_predecessors"
            )
        if self.process_backed and StageEffect.EXECUTE_GF not in effects:
            raise ValueError("process-backed stages must declare EXECUTE_GF")
        if self.process_backed and not self.cancellation_aware:
            raise ValueError("process-backed stages must be cancellation-aware")
        if self.process_backed and not self.preserves_raw_evidence:
            raise ValueError("process-backed stages must preserve raw evidence")
        if self.preserves_raw_evidence and StageEffect.WRITE_RAW_EVIDENCE not in effects:
            raise ValueError(
                "stages preserving raw evidence must declare WRITE_RAW_EVIDENCE"
            )

        object.__setattr__(self, "required_predecessors", required_predecessors)
        object.__setattr__(self, "blocking_predecessors", blocking_predecessors)
        object.__setattr__(self, "ordered_after", ordered_after)
        object.__setattr__(self, "effects", effects)
        object.__setattr__(self, "owned_outputs", owned_outputs)

    def requirement_for(self, mode: ValidationMode | str) -> StageRequirement:
        return self.mode_requirements[_coerce_mode(mode)]

    def is_applicable(self, mode: ValidationMode | str) -> bool:
        return self.requirement_for(mode) is not StageRequirement.NOT_APPLICABLE

    def is_required(self, mode: ValidationMode | str) -> bool:
        return self.requirement_for(mode) is StageRequirement.REQUIRED

    def is_conditional(self, mode: ValidationMode | str) -> bool:
        return self.requirement_for(mode) is StageRequirement.CONDITIONAL

    def is_recommended(self, mode: ValidationMode | str) -> bool:
        return self.requirement_for(mode) is StageRequirement.RECOMMENDED

    def may_write_project_assets(self) -> bool:
        return False


class StageContractRegistry:
    __slots__ = ("_contracts", "_by_id", "_positions")

    def __init__(self, contracts: Iterable[StageContract]) -> None:
        prepared = tuple(contracts)
        _validate_contract_set(prepared)
        self._contracts = prepared
        self._by_id = MappingProxyType(
            {contract.stage_id: contract for contract in prepared}
        )
        self._positions = MappingProxyType(
            {contract.stage_id: index for index, contract in enumerate(prepared)}
        )

    def __iter__(self) -> Iterator[StageContract]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def __contains__(self, stage_id: object) -> bool:
        try:
            canonical = _coerce_stage_id(stage_id)
        except (TypeError, ValueError):
            return False
        return canonical in self._by_id

    @property
    def contracts(self) -> tuple[StageContract, ...]:
        return self._contracts

    @property
    def stage_ids(self) -> tuple[StageId, ...]:
        return tuple(contract.stage_id for contract in self._contracts)

    def get(self, stage_id: StageIdLike) -> StageContract:
        canonical = _coerce_stage_id(stage_id)
        try:
            return self._by_id[canonical]
        except KeyError as exc:
            raise KeyError(f"unknown validation stage: {canonical.value}") from exc

    def position(self, stage_id: StageIdLike) -> int:
        return self._positions[_coerce_stage_id(stage_id)]

    def for_mode(
        self,
        mode: ValidationMode | str,
        *,
        include_conditional: bool = True,
        include_recommended: bool = False,
        include_optional: bool = False,
    ) -> tuple[StageContract, ...]:
        canonical_mode = _coerce_mode(mode)
        accepted = {StageRequirement.REQUIRED}
        if include_conditional:
            accepted.add(StageRequirement.CONDITIONAL)
        if include_recommended:
            accepted.add(StageRequirement.RECOMMENDED)
        if include_optional:
            accepted.add(StageRequirement.OPTIONAL)
        return tuple(
            contract
            for contract in self._contracts
            if contract.requirement_for(canonical_mode) in accepted
        )

    def required_for_mode(
        self,
        mode: ValidationMode | str,
    ) -> tuple[StageContract, ...]:
        canonical_mode = _coerce_mode(mode)
        return tuple(
            contract
            for contract in self._contracts
            if contract.is_required(canonical_mode)
        )

    def ordered(
        self,
        stage_ids: Iterable[StageIdLike],
        *,
        include_required_predecessors: bool = False,
    ) -> tuple[StageId, ...]:
        selected = _coerce_stage_ids(stage_ids)
        if include_required_predecessors:
            selected = self.expand_required_predecessors(selected)
        return tuple(sorted(selected, key=self.position))

    def expand_required_predecessors(
        self,
        stage_ids: Iterable[StageIdLike],
    ) -> tuple[StageId, ...]:
        selected = set(_coerce_stage_ids(stage_ids))
        pending = list(selected)
        while pending:
            current = pending.pop()
            for predecessor in self.get(current).required_predecessors:
                if predecessor not in selected:
                    selected.add(predecessor)
                    pending.append(predecessor)
        return tuple(sorted(selected, key=self.position))

    def validate_sequence(
        self,
        stage_ids: Sequence[StageIdLike],
        *,
        require_predecessors: bool = True,
    ) -> tuple[StageId, ...]:
        sequence = _coerce_stage_ids(stage_ids)
        if len(sequence) != len(set(sequence)):
            raise ValueError("stage sequence contains duplicate stage IDs")

        positions = [self.position(stage_id) for stage_id in sequence]
        if positions != sorted(positions):
            raise ValueError("stage sequence does not follow canonical order")

        selected = set(sequence)
        seen: set[StageId] = set()
        for stage_id in sequence:
            contract = self.get(stage_id)
            if require_predecessors:
                missing = tuple(
                    predecessor
                    for predecessor in contract.required_predecessors
                    if predecessor not in selected
                )
                if missing:
                    names = ", ".join(item.value for item in missing)
                    raise ValueError(
                        f"stage {stage_id.value!r} is missing required "
                        f"predecessors: {names}"
                    )
            misplaced = tuple(
                predecessor
                for predecessor in (
                    *contract.required_predecessors,
                    *contract.ordered_after,
                )
                if predecessor in selected and predecessor not in seen
            )
            if misplaced:
                names = ", ".join(item.value for item in misplaced)
                raise ValueError(
                    f"stage {stage_id.value!r} appears before: {names}"
                )
            seen.add(stage_id)
        return sequence

    def validate_mode_selection(
        self,
        mode: ValidationMode | str,
        stage_ids: Sequence[StageIdLike],
        *,
        require_all_required: bool = True,
    ) -> tuple[StageId, ...]:
        canonical_mode = _coerce_mode(mode)
        sequence = self.validate_sequence(stage_ids)
        selected = set(sequence)

        prohibited = tuple(
            stage_id
            for stage_id in sequence
            if not self.get(stage_id).is_applicable(canonical_mode)
        )
        if prohibited:
            names = ", ".join(item.value for item in prohibited)
            raise ValueError(
                f"mode {canonical_mode.value!r} does not permit stages: {names}"
            )

        if require_all_required:
            missing = tuple(
                contract.stage_id
                for contract in self.required_for_mode(canonical_mode)
                if contract.stage_id not in selected
            )
            if missing:
                names = ", ".join(item.value for item in missing)
                raise ValueError(
                    f"mode {canonical_mode.value!r} is missing required "
                    f"stages: {names}"
                )
        return sequence

    def blocking_predecessors(
        self,
        stage_id: StageIdLike,
    ) -> tuple[StageId, ...]:
        return self.get(stage_id).blocking_predecessors



def _validate_contract_set(contracts: tuple[StageContract, ...]) -> None:
    if not contracts:
        raise ValueError("at least one stage contract is required")
    if len(contracts) != len(StageId):
        raise ValueError("the canonical registry must define every StageId exactly once")

    ids = tuple(contract.stage_id for contract in contracts)
    if len(ids) != len(set(ids)):
        raise ValueError("stage contract IDs must be unique")
    if frozenset(ids) != frozenset(StageId):
        missing = frozenset(StageId).difference(ids)
        extra = frozenset(ids).difference(StageId)
        raise ValueError(
            "stage registry does not match canonical StageId values; "
            f"missing={sorted(item.value for item in missing)!r}, "
            f"extra={sorted(item.value for item in extra)!r}"
        )

    expected_orders = tuple(range(len(contracts)))
    actual_orders = tuple(contract.order for contract in contracts)
    if actual_orders != expected_orders:
        raise ValueError("stage orders must be contiguous and match registry order")

    positions = {contract.stage_id: contract.order for contract in contracts}
    output_owners: dict[str, StageId] = {}
    for contract in contracts:
        predecessors = (
            *contract.required_predecessors,
            *contract.ordered_after,
        )
        for predecessor in predecessors:
            if predecessor not in positions:
                raise ValueError(
                    f"stage {contract.stage_id.value!r} references unknown "
                    f"predecessor {predecessor.value!r}"
                )
            if positions[predecessor] >= contract.order:
                raise ValueError(
                    f"stage {contract.stage_id.value!r} predecessor "
                    f"{predecessor.value!r} must appear earlier"
                )

        for output in contract.owned_outputs:
            previous_owner = output_owners.get(output)
            if previous_owner is not None:
                raise ValueError(
                    f"owned output {output!r} is duplicated by "
                    f"{previous_owner.value!r} and {contract.stage_id.value!r}"
                )
            output_owners[output] = contract.stage_id


def _freeze_mode_requirements(value: ModeRequirementMap) -> ModeRequirementMap:
    if not isinstance(value, Mapping):
        raise TypeError("mode_requirements must be a mapping")
    copied: dict[ValidationMode, StageRequirement] = {}
    for mode, requirement in value.items():
        if not isinstance(mode, ValidationMode):
            raise TypeError("mode_requirements keys must be ValidationMode")
        if not isinstance(requirement, StageRequirement):
            raise TypeError("mode_requirements values must be StageRequirement")
        copied[mode] = requirement
    if frozenset(copied) != _ALL_MODE_SET:
        raise ValueError("mode_requirements must define every canonical mode")
    return MappingProxyType(copied)


def _stage_tuple(
    values: Iterable[StageId],
    *,
    field: str,
    current: StageId,
) -> tuple[StageId, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of StageId")
    result = tuple(values)
    if any(not isinstance(value, StageId) for value in result):
        raise TypeError(f"{field} must contain StageId values")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    if current in result:
        raise ValueError(f"{field} must not contain the current stage")
    return result


def _effect_tuple(values: Iterable[StageEffect]) -> tuple[StageEffect, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("effects must be an iterable of StageEffect")
    result = tuple(values)
    if any(not isinstance(value, StageEffect) for value in result):
        raise TypeError("effects must contain StageEffect values")
    if len(result) != len(set(result)):
        raise ValueError("effects must not contain duplicates")
    return result


def _text_tuple(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of strings")
    result = tuple(values)
    for value in result:
        _require_text(value, field=f"{field} item")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    return result


def _coerce_mode(value: ValidationMode | str) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise TypeError("mode must be ValidationMode or string")
    try:
        return ValidationMode(value)
    except ValueError as exc:
        raise ValueError(f"unknown validation mode: {value!r}") from exc


def _coerce_stage_id(value: object) -> StageId:
    if isinstance(value, StageId):
        return value
    if not isinstance(value, str):
        raise TypeError("stage ID must be StageId or string")
    try:
        return StageId(value)
    except ValueError as exc:
        raise ValueError(f"unknown validation stage: {value!r}") from exc


def _coerce_stage_ids(values: Iterable[StageIdLike]) -> tuple[StageId, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("stage IDs must be an iterable, not one string")
    return tuple(_coerce_stage_id(value) for value in values)


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip() or "\x00" in value:
        raise ValueError(f"{field} must be non-empty and contain no NUL")
    return value


def _requirements(
    *,
    quick: StageRequirement,
    checkpoint: StageRequirement,
    release: StageRequirement,
    diagnostic: StageRequirement,
) -> ModeRequirementMap:
    return MappingProxyType(
        {
            ValidationMode.QUICK: quick,
            ValidationMode.CHECKPOINT: checkpoint,
            ValidationMode.RELEASE: release,
            ValidationMode.DIAGNOSTIC: diagnostic,
        }
    )


_REQUIRED_ALL: Final[ModeRequirementMap] = _requirements(
    quick=StageRequirement.REQUIRED,
    checkpoint=StageRequirement.REQUIRED,
    release=StageRequirement.REQUIRED,
    diagnostic=StageRequirement.REQUIRED,
)


STAGE_CONTRACTS: Final[tuple[StageContract, ...]] = (
    StageContract(
        stage_id=StageId.CONFIGURATION,
        order=0,
        purpose="Resolve and validate the authoritative active-project run configuration.",
        owner=StageOwner.CONFIGURATION,
        mode_requirements=_REQUIRED_ALL,
        effects=(StageEffect.READ_PROJECT_CONFIGURATION,),
        owned_outputs=("resolved_run_configuration", "configuration_provenance"),
        failure_policy=StageFailurePolicy.FATAL_PRECONDITION,
    ),
    StageContract(
        stage_id=StageId.ENVIRONMENT,
        order=1,
        purpose="Resolve the executable, workspace, output, RGL, and effective GF paths.",
        owner=StageOwner.CONFIGURATION,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.CONFIGURATION,),
        blocking_predecessors=(StageId.CONFIGURATION,),
        ordered_after=(StageId.CONFIGURATION,),
        effects=(StageEffect.READ_PROJECT_CONFIGURATION,),
        owned_outputs=("resolved_environment", "environment_provenance"),
        failure_policy=StageFailurePolicy.FATAL_PRECONDITION,
    ),
    StageContract(
        stage_id=StageId.VERSION_PROBE,
        order=2,
        purpose="Probe GF and evaluate the documented version-compatibility policy.",
        owner=StageOwner.VALIDATION_COMPILATION,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.ENVIRONMENT,),
        blocking_predecessors=(StageId.ENVIRONMENT,),
        ordered_after=(StageId.ENVIRONMENT,),
        effects=(
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
        ),
        owned_outputs=("gf_version_probe", "version_stdout", "version_stderr"),
        failure_policy=StageFailurePolicy.BLOCK_DEPENDENTS,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.SELECTION,
        order=3,
        purpose="Resolve deterministic files, checkpoints, entrypoints, and scenarios.",
        owner=StageOwner.VALIDATION_SELECTION,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.CONFIGURATION, StageId.ENVIRONMENT),
        blocking_predecessors=(StageId.CONFIGURATION, StageId.ENVIRONMENT),
        ordered_after=(StageId.VERSION_PROBE,),
        effects=(
            StageEffect.READ_PROJECT_CONFIGURATION,
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.READ_PROJECT_VALIDATION_ASSET,
        ),
        owned_outputs=("validation_selection", "selection_reasons"),
        failure_policy=StageFailurePolicy.BLOCK_DEPENDENTS,
    ),
    StageContract(
        stage_id=StageId.STATIC_SCAN,
        order=4,
        purpose="Run the stable language-neutral static scanner over selected sources.",
        owner=StageOwner.VALIDATION_SCANNING,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.SELECTION,),
        blocking_predecessors=(StageId.SELECTION,),
        ordered_after=(StageId.SELECTION,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.WRITE_RAW_EVIDENCE,
        ),
        owned_outputs=("scan_results", "per_file_scan_logs"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.FINGERPRINT,
        order=5,
        purpose="Record stable current-source fingerprints for selected validation subjects.",
        owner=StageOwner.VALIDATION_SELECTION,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.SELECTION,),
        blocking_predecessors=(StageId.SELECTION,),
        ordered_after=(StageId.STATIC_SCAN,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("source_fingerprints",),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
    ),
    StageContract(
        stage_id=StageId.COMPILE_FILES,
        order=6,
        purpose="Compile selected GF source targets and verify required current artifacts.",
        owner=StageOwner.VALIDATION_COMPILATION,
        mode_requirements=_requirements(
            quick=StageRequirement.REQUIRED,
            checkpoint=StageRequirement.REQUIRED,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.CONDITIONAL,
        ),
        required_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        blocking_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        ordered_after=(StageId.FINGERPRINT,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("file_compile_results", "file_compile_logs", "gfo_observations"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.COMPILE_CHECKPOINTS,
        order=7,
        purpose="Compile configured checkpoint closure in deterministic prerequisite order.",
        owner=StageOwner.VALIDATION_COMPILATION,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.REQUIRED,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.OPTIONAL,
        ),
        required_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        blocking_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        ordered_after=(StageId.COMPILE_FILES,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("checkpoint_compile_results", "checkpoint_compile_logs"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.COMPILE_ENTRYPOINTS,
        order=8,
        purpose="Compile configured entrypoints and preserve downstream reachability evidence.",
        owner=StageOwner.VALIDATION_COMPILATION,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.CONDITIONAL,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.OPTIONAL,
        ),
        required_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        blocking_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        ordered_after=(StageId.COMPILE_CHECKPOINTS,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("entrypoint_compile_results", "entrypoint_compile_logs"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.BUILD_PGF,
        order=9,
        purpose="Build configured PGF targets and verify the produced current artifacts.",
        owner=StageOwner.VALIDATION_COMPILATION,
        mode_requirements=_requirements(
            quick=StageRequirement.NOT_APPLICABLE,
            checkpoint=StageRequirement.OPTIONAL,
            release=StageRequirement.CONDITIONAL,
            diagnostic=StageRequirement.OPTIONAL,
        ),
        required_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        blocking_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        ordered_after=(StageId.COMPILE_ENTRYPOINTS,),
        effects=(
            StageEffect.READ_PROJECT_SOURCE,
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("pgf_build_results", "pgf_build_logs", "pgf_observations"),
        failure_policy=StageFailurePolicy.BLOCK_DEPENDENTS,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.RUN_SCENARIOS,
        order=10,
        purpose="Execute selected native GF scenarios with bounded isolated processes.",
        owner=StageOwner.VALIDATION_SCENARIOS,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.CONDITIONAL,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.OPTIONAL,
        ),
        required_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        blocking_predecessors=(StageId.ENVIRONMENT, StageId.SELECTION),
        ordered_after=(StageId.BUILD_PGF,),
        effects=(
            StageEffect.READ_PROJECT_VALIDATION_ASSET,
            StageEffect.EXECUTE_GF,
            StageEffect.WRITE_RAW_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("scenario_process_results", "scenario_stdout", "scenario_stderr"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
        process_backed=True,
        cancellation_aware=True,
        preserves_raw_evidence=True,
    ),
    StageContract(
        stage_id=StageId.NORMALIZE_OUTPUTS,
        order=11,
        purpose="Create versioned stable scenario output without modifying raw evidence.",
        owner=StageOwner.VALIDATION_SCENARIOS,
        mode_requirements=_requirements(
            quick=StageRequirement.CONDITIONAL,
            checkpoint=StageRequirement.CONDITIONAL,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.CONDITIONAL,
        ),
        required_predecessors=(StageId.RUN_SCENARIOS,),
        ordered_after=(StageId.RUN_SCENARIOS,),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("normalized_scenario_outputs", "normalization_results"),
        failure_policy=StageFailurePolicy.BLOCK_DEPENDENTS,
    ),
    StageContract(
        stage_id=StageId.EVALUATE_ASSERTIONS,
        order=12,
        purpose="Evaluate bounded structured scenario assertions in specification order.",
        owner=StageOwner.VALIDATION_SCENARIOS,
        mode_requirements=_requirements(
            quick=StageRequirement.CONDITIONAL,
            checkpoint=StageRequirement.CONDITIONAL,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.CONDITIONAL,
        ),
        required_predecessors=(StageId.RUN_SCENARIOS,),
        ordered_after=(StageId.NORMALIZE_OUTPUTS,),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("scenario_assertion_results",),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
    ),
    StageContract(
        stage_id=StageId.COMPARE_GOLD,
        order=13,
        purpose="Compare normalized scenario output with declared reviewed gold evidence.",
        owner=StageOwner.VALIDATION_SCENARIOS,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.CONDITIONAL,
            release=StageRequirement.CONDITIONAL,
            diagnostic=StageRequirement.OPTIONAL,
        ),
        required_predecessors=(StageId.NORMALIZE_OUTPUTS,),
        blocking_predecessors=(StageId.NORMALIZE_OUTPUTS,),
        ordered_after=(StageId.EVALUATE_ASSERTIONS,),
        effects=(
            StageEffect.READ_PROJECT_VALIDATION_ASSET,
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("gold_comparison_results", "gold_diffs"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
    ),
    StageContract(
        stage_id=StageId.CLASSIFY_FAILURES,
        order=14,
        purpose="Classify structured failures as direct, downstream, ambiguous, noise, or skipped.",
        owner=StageOwner.DIAGNOSTICS,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.SELECTION,),
        ordered_after=(
            StageId.STATIC_SCAN,
            StageId.COMPILE_FILES,
            StageId.COMPILE_CHECKPOINTS,
            StageId.COMPILE_ENTRYPOINTS,
            StageId.BUILD_PGF,
            StageId.RUN_SCENARIOS,
            StageId.EVALUATE_ASSERTIONS,
            StageId.COMPARE_GOLD,
        ),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("classified_file_results", "classified_scenario_results"),
        failure_policy=StageFailurePolicy.AGGREGATE,
    ),
    StageContract(
        stage_id=StageId.COMPARE_PREVIOUS,
        order=15,
        purpose="Compare the current structured result with one compatible previous run.",
        owner=StageOwner.VALIDATION_REGRESSION,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.RECOMMENDED,
            release=StageRequirement.CONDITIONAL,
            diagnostic=StageRequirement.RECOMMENDED,
        ),
        required_predecessors=(StageId.CLASSIFY_FAILURES,),
        ordered_after=(StageId.CLASSIFY_FAILURES,),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.READ_PREVIOUS_RUN,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("regression_comparison", "diff_entries"),
        failure_policy=StageFailurePolicy.CONTINUE_INDEPENDENT,
    ),
    StageContract(
        stage_id=StageId.EVALUATE_RELEASE_GATES,
        order=16,
        purpose="Evaluate the single structured release decision from completed evidence.",
        owner=StageOwner.VALIDATION_RELEASE,
        mode_requirements=_requirements(
            quick=StageRequirement.NOT_APPLICABLE,
            checkpoint=StageRequirement.NOT_APPLICABLE,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.NOT_APPLICABLE,
        ),
        required_predecessors=(StageId.CLASSIFY_FAILURES,),
        ordered_after=(StageId.COMPARE_PREVIOUS,),
        effects=(
            StageEffect.READ_PROJECT_CONFIGURATION,
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("release_gate_results", "release_decision"),
        failure_policy=StageFailurePolicy.AGGREGATE,
    ),
    StageContract(
        stage_id=StageId.WRITE_REPORTS,
        order=17,
        purpose="Render required machine and human reports from one structured run result.",
        owner=StageOwner.REPORTING,
        mode_requirements=_REQUIRED_ALL,
        required_predecessors=(StageId.CONFIGURATION,),
        ordered_after=(
            StageId.CLASSIFY_FAILURES,
            StageId.COMPARE_PREVIOUS,
            StageId.EVALUATE_RELEASE_GATES,
        ),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_REPORT,
        ),
        owned_outputs=(
            "summary_json",
            "summary_markdown",
            "ai_ready",
            "top_errors",
            "detail_reports",
            "aggregate_logs",
        ),
        failure_policy=StageFailurePolicy.FINALIZE,
    ),
    StageContract(
        stage_id=StageId.WRITE_MANIFEST,
        order=18,
        purpose="Write the canonical artifact manifest after finalized artifact bytes exist.",
        owner=StageOwner.REPORTING,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.RECOMMENDED,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.RECOMMENDED,
        ),
        required_predecessors=(StageId.WRITE_REPORTS,),
        ordered_after=(StageId.WRITE_REPORTS,),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_MANIFEST,
        ),
        owned_outputs=("manifest_json",),
        failure_policy=StageFailurePolicy.FINALIZE,
    ),
    StageContract(
        stage_id=StageId.VERIFY_MANIFEST,
        order=19,
        purpose="Verify required artifact existence, containment, size, and finalized hashes.",
        owner=StageOwner.REPORTING,
        mode_requirements=_requirements(
            quick=StageRequirement.OPTIONAL,
            checkpoint=StageRequirement.RECOMMENDED,
            release=StageRequirement.REQUIRED,
            diagnostic=StageRequirement.RECOMMENDED,
        ),
        required_predecessors=(StageId.WRITE_MANIFEST,),
        blocking_predecessors=(StageId.WRITE_MANIFEST,),
        ordered_after=(StageId.WRITE_MANIFEST,),
        effects=(
            StageEffect.READ_RUN_EVIDENCE,
            StageEffect.WRITE_DERIVED_EVIDENCE,
        ),
        owned_outputs=("manifest_verification",),
        failure_policy=StageFailurePolicy.FINALIZE,
    ),
)

STAGE_REGISTRY: Final[StageContractRegistry] = StageContractRegistry(STAGE_CONTRACTS)
CANONICAL_STAGE_IDS: Final[tuple[StageId, ...]] = STAGE_REGISTRY.stage_ids


def get_stage_contract(stage_id: StageIdLike) -> StageContract:
    return STAGE_REGISTRY.get(stage_id)


def get_stage_requirement(
    stage_id: StageIdLike,
    mode: ValidationMode | str,
) -> StageRequirement:
    return get_stage_contract(stage_id).requirement_for(mode)


def canonical_stage_contracts() -> tuple[StageContract, ...]:
    return STAGE_CONTRACTS


def canonical_stage_ids() -> tuple[StageId, ...]:
    return CANONICAL_STAGE_IDS


def required_stage_ids(
    mode: ValidationMode | str,
) -> tuple[StageId, ...]:
    return tuple(
        contract.stage_id for contract in STAGE_REGISTRY.required_for_mode(mode)
    )


def applicable_stage_ids(
    mode: ValidationMode | str,
    *,
    include_conditional: bool = True,
    include_recommended: bool = False,
    include_optional: bool = False,
) -> tuple[StageId, ...]:
    return tuple(
        contract.stage_id
        for contract in STAGE_REGISTRY.for_mode(
            mode,
            include_conditional=include_conditional,
            include_recommended=include_recommended,
            include_optional=include_optional,
        )
    )


def order_stage_ids(
    stage_ids: Iterable[StageIdLike],
    *,
    include_required_predecessors: bool = False,
) -> tuple[StageId, ...]:
    return STAGE_REGISTRY.ordered(
        stage_ids,
        include_required_predecessors=include_required_predecessors,
    )


def validate_stage_sequence(
    stage_ids: Sequence[StageIdLike],
    *,
    require_predecessors: bool = True,
) -> tuple[StageId, ...]:
    return STAGE_REGISTRY.validate_sequence(
        stage_ids,
        require_predecessors=require_predecessors,
    )


def validate_mode_stage_selection(
    mode: ValidationMode | str,
    stage_ids: Sequence[StageIdLike],
    *,
    require_all_required: bool = True,
) -> tuple[StageId, ...]:
    return STAGE_REGISTRY.validate_mode_selection(
        mode,
        stage_ids,
        require_all_required=require_all_required,
    )




__all__ = (
    "CANONICAL_STAGE_IDS",
    "STAGE_CONTRACTS",
    "STAGE_REGISTRY",
    "ModeRequirementMap",
    "StageContract",
    "StageContractRegistry",
    "StageEffect",
    "StageFailurePolicy",
    "StageId",
    "StageIdLike",
    "StageOwner",
    "StageRequirement",
    "applicable_stage_ids",
    "canonical_stage_contracts",
    "canonical_stage_ids",
    "get_stage_contract",
    "get_stage_requirement",
    "order_stage_ids",
    "required_stage_ids",
    "validate_mode_stage_selection",
    "validate_stage_sequence",
)
