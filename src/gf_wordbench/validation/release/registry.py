"""Canonical release-gate registry for GF Wordbench."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final

GATE_POLICY_VERSION: Final[str] = "1.1.0"

_FRAMEWORK_GATE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^RG-(?:0[0-9]|1[0-4])$"
)
_PROJECT_GATE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^RC-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}$"
)
_CONDITION_KEY_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
)


@unique
class ReleaseGateApplicability(StrEnum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    NOT_APPLICABLE = "not_applicable"


@unique
class ReleaseGatePhase(StrEnum):
    EVALUATION = "evaluation"
    DECISION = "decision"


@dataclass(frozen=True, slots=True)
class ReleaseGateDefinition:
    gate_id: str
    name: str
    applicability: ReleaseGateApplicability
    owner: str
    purpose: str
    phase: ReleaseGatePhase = ReleaseGatePhase.EVALUATION
    activation_condition: str | None = None
    hard_gate: bool = True

    def __post_init__(self) -> None:
        _validate_gate_id(self.gate_id)
        _validate_text(self.name, field_name="name")
        _validate_text(self.owner, field_name="owner")
        _validate_text(self.purpose, field_name="purpose")

        if not isinstance(
            self.applicability,
            ReleaseGateApplicability,
        ):
            raise TypeError(
                "applicability must be a ReleaseGateApplicability"
            )
        if not isinstance(self.phase, ReleaseGatePhase):
            raise TypeError("phase must be a ReleaseGatePhase")
        if not isinstance(self.hard_gate, bool):
            raise TypeError("hard_gate must be a bool")

        condition = self.activation_condition
        if self.applicability is ReleaseGateApplicability.CONDITIONAL:
            if condition is None:
                raise ValueError(
                    "conditional gates require activation_condition"
                )
            _validate_condition_key(condition)
        elif condition is not None:
            raise ValueError(
                "activation_condition is valid only for conditional gates"
            )

        if (
            self.phase is ReleaseGatePhase.DECISION
            and self.gate_id != "RG-14"
        ):
            raise ValueError(
                "only RG-14 may use the decision phase"
            )
        if (
            self.gate_id == "RG-14"
            and self.phase is not ReleaseGatePhase.DECISION
        ):
            raise ValueError("RG-14 must use the decision phase")

    @property
    def is_framework_gate(self) -> bool:
        return _FRAMEWORK_GATE_ID_RE.fullmatch(self.gate_id) is not None

    @property
    def is_project_gate(self) -> bool:
        return _PROJECT_GATE_ID_RE.fullmatch(self.gate_id) is not None

    def is_active(
        self,
        conditions: Mapping[str, bool] | None = None,
    ) -> bool:
        if self.applicability is ReleaseGateApplicability.REQUIRED:
            return True
        if self.applicability is ReleaseGateApplicability.NOT_APPLICABLE:
            return False
        if conditions is None:
            return False

        condition = self.activation_condition
        if condition is None:
            raise AssertionError(
                "conditional gate has no activation condition"
            )
        value = conditions.get(condition, False)
        if not isinstance(value, bool):
            raise TypeError(
                f"condition {condition!r} must resolve to a bool"
            )
        return value


CANONICAL_RELEASE_GATES: Final[
    tuple[ReleaseGateDefinition, ...]
] = (
    ReleaseGateDefinition(
        gate_id="RG-00",
        name="Release request",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Release orchestrator",
        purpose=(
            "Confirm that the run intentionally requests a release "
            "decision with valid release execution settings."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-01",
        name="Project identity and configuration",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Project loader and configuration validator",
        purpose=(
            "Prove that one coherent active language project is "
            "defined by valid configuration."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-02",
        name="Environment and toolchain",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Toolchain compatibility service",
        purpose=(
            "Prove that the release uses an accepted GF, RGL, "
            "platform, path, locale, and encoding environment."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-03",
        name="Release scope and project contracts",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Project contract checker",
        purpose=(
            "Verify that release files, entrypoints, checkpoints, "
            "scenarios, gold files, documents, and relationships are "
            "completely and consistently declared."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-04",
        name="Source inventory and static policy",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="File selector and scanner",
        purpose=(
            "Prove that release source selection is deterministic, "
            "complete, fingerprinted, and free from blocking static "
            "findings."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-05",
        name="Clean checkpoint compilation",
        applicability=ReleaseGateApplicability.CONDITIONAL,
        activation_condition="checkpoints_declared",
        owner="Compiler and audit orchestrator",
        purpose=(
            "Prove that every required checkpoint compiles from "
            "current source in a clean run-owned artifact context."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-06",
        name="Release entrypoint compilation",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Compiler and release orchestrator",
        purpose=(
            "Prove that every configured release entrypoint compiles "
            "without substitution and with current-run evidence."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-07",
        name="Required grammar-load and runtime scenarios",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Scenario runner",
        purpose=(
            "Prove required grammar loading and runtime behavior "
            "through registered GF scenarios, markers, assertions, "
            "and artifacts."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-08",
        name="Golden regression validation",
        applicability=ReleaseGateApplicability.CONDITIONAL,
        activation_condition="required_gold_backed_scenarios_declared",
        owner="Gold comparator",
        purpose=(
            "Prove that every required gold-backed scenario matches "
            "its reviewed normalized expectation without modifying "
            "gold files."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-09",
        name="Missing-function and completeness policy",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Project validation policy and scenario runner",
        purpose=(
            "Prove that missing functions, placeholders, fallbacks, "
            "and intentional omissions satisfy explicit project "
            "release policy."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-10",
        name="PGF release build",
        applicability=ReleaseGateApplicability.CONDITIONAL,
        activation_condition="release_requires_pgf",
        owner="PGF builder",
        purpose=(
            "Build and verify the current run's declared PGF release "
            "artifact from configured release entrypoints."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-11",
        name="Regression and known-issue review",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Diff engine and project release policy",
        purpose=(
            "Prevent release while required regressions or "
            "release-blocking known issues remain unresolved."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-12",
        name="Framework contract and schema integrity",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Contract and schema validators",
        purpose=(
            "Prove that framework interfaces, active-project "
            "contracts, and persisted schemas remain valid and "
            "supported."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-13",
        name="Evidence, reports, and manifest integrity",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Result finalizer, report writers, and manifest writer",
        purpose=(
            "Ensure release evidence is complete, reproducible, "
            "internally consistent, and verified by the manifest."
        ),
    ),
    ReleaseGateDefinition(
        gate_id="RG-14",
        name="Release decision",
        applicability=ReleaseGateApplicability.REQUIRED,
        owner="Release decision engine",
        purpose=(
            "Aggregate applicable required gate outcomes without "
            "reinterpretation and produce the terminal release "
            "decision."
        ),
        phase=ReleaseGatePhase.DECISION,
    ),
)

CANONICAL_RELEASE_GATE_IDS: Final[tuple[str, ...]] = tuple(
    gate.gate_id for gate in CANONICAL_RELEASE_GATES
)

CANONICAL_RELEASE_GATE_BY_ID: Final[
    Mapping[str, ReleaseGateDefinition]
] = MappingProxyType(
    {gate.gate_id: gate for gate in CANONICAL_RELEASE_GATES}
)


def iter_release_gates(
    *,
    include_decision_gate: bool = True,
) -> Iterator[ReleaseGateDefinition]:
    if not isinstance(include_decision_gate, bool):
        raise TypeError("include_decision_gate must be a bool")

    for gate in CANONICAL_RELEASE_GATES:
        if (
            not include_decision_gate
            and gate.phase is ReleaseGatePhase.DECISION
        ):
            continue
        yield gate


def evaluation_gate_definitions() -> tuple[ReleaseGateDefinition, ...]:
    return tuple(
        iter_release_gates(include_decision_gate=False)
    )


def decision_gate_definition() -> ReleaseGateDefinition:
    return CANONICAL_RELEASE_GATE_BY_ID["RG-14"]


def get_release_gate(
    gate_id: str,
) -> ReleaseGateDefinition | None:
    _validate_text(gate_id, field_name="gate_id")
    return CANONICAL_RELEASE_GATE_BY_ID.get(gate_id)


def require_release_gate(
    gate_id: str,
) -> ReleaseGateDefinition:
    gate = get_release_gate(gate_id)
    if gate is None:
        raise KeyError(f"unknown release gate {gate_id!r}")
    return gate


def active_release_gates(
    conditions: Mapping[str, bool] | None = None,
    *,
    include_decision_gate: bool = False,
) -> tuple[ReleaseGateDefinition, ...]:
    if conditions is not None:
        _validate_conditions(conditions)
    return tuple(
        gate
        for gate in iter_release_gates(
            include_decision_gate=include_decision_gate
        )
        if gate.is_active(conditions)
    )


def inactive_conditional_gates(
    conditions: Mapping[str, bool] | None = None,
) -> tuple[ReleaseGateDefinition, ...]:
    if conditions is not None:
        _validate_conditions(conditions)
    return tuple(
        gate
        for gate in evaluation_gate_definitions()
        if (
            gate.applicability
            is ReleaseGateApplicability.CONDITIONAL
            and not gate.is_active(conditions)
        )
    )


def build_release_gate_registry(
    project_gates: Iterable[ReleaseGateDefinition] = (),
) -> tuple[ReleaseGateDefinition, ...]:
    if isinstance(project_gates, (str, bytes)):
        raise TypeError(
            "project_gates must be an iterable of gate definitions"
        )

    extensions = tuple(project_gates)
    validate_release_gate_registry(
        (*CANONICAL_RELEASE_GATES, *extensions),
        require_canonical_prefix=True,
    )
    return (*CANONICAL_RELEASE_GATES, *extensions)


def index_release_gate_registry(
    gates: Iterable[ReleaseGateDefinition],
) -> Mapping[str, ReleaseGateDefinition]:
    normalized = tuple(gates)
    validate_release_gate_registry(normalized)
    return MappingProxyType(
        {gate.gate_id: gate for gate in normalized}
    )


def validate_release_gate_registry(
    gates: Iterable[ReleaseGateDefinition],
    *,
    require_canonical_prefix: bool = False,
) -> None:
    if isinstance(gates, (str, bytes)):
        raise TypeError("gates must be an iterable of gate definitions")
    if not isinstance(require_canonical_prefix, bool):
        raise TypeError("require_canonical_prefix must be a bool")

    normalized = tuple(gates)
    seen: set[str] = set()

    for position, gate in enumerate(normalized):
        if not isinstance(gate, ReleaseGateDefinition):
            raise TypeError(
                f"gates[{position}] must be a ReleaseGateDefinition"
            )
        if gate.gate_id in seen:
            raise ValueError(
                f"duplicate release gate ID {gate.gate_id!r}"
            )
        seen.add(gate.gate_id)

    if require_canonical_prefix:
        prefix = normalized[: len(CANONICAL_RELEASE_GATES)]
        if prefix != CANONICAL_RELEASE_GATES:
            raise ValueError(
                "canonical release gates must remain the registry prefix "
                "in canonical order"
            )
        for gate in normalized[len(CANONICAL_RELEASE_GATES) :]:
            if not gate.is_project_gate:
                raise ValueError(
                    "release-gate extensions must use project gate IDs "
                    "matching RC-<DOMAIN>-<NNN>"
                )
            if gate.phase is ReleaseGatePhase.DECISION:
                raise ValueError(
                    "project gates cannot define a decision phase"
                )


def _validate_gate_id(value: str) -> None:
    _validate_text(value, field_name="gate_id")
    if (
        _FRAMEWORK_GATE_ID_RE.fullmatch(value) is None
        and _PROJECT_GATE_ID_RE.fullmatch(value) is None
    ):
        raise ValueError(
            "gate_id must match RG-00 through RG-14 or "
            "RC-<DOMAIN>-<NNN>"
        )


def _validate_condition_key(value: str) -> None:
    _validate_text(value, field_name="activation_condition")
    if _CONDITION_KEY_RE.fullmatch(value) is None:
        raise ValueError(
            "activation_condition must use lowercase snake_case"
        )


def _validate_conditions(
    conditions: Mapping[str, bool],
) -> None:
    if not isinstance(conditions, Mapping):
        raise TypeError("conditions must be a mapping")
    for key, value in conditions.items():
        _validate_condition_key(key)
        if not isinstance(value, bool):
            raise TypeError(
                f"condition {key!r} must map to a bool"
            )


def _validate_text(value: str, *, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(
            f"{field_name} must not contain NUL characters"
        )


validate_release_gate_registry(CANONICAL_RELEASE_GATES)

__all__ = (
    "CANONICAL_RELEASE_GATE_BY_ID",
    "CANONICAL_RELEASE_GATE_IDS",
    "CANONICAL_RELEASE_GATES",
    "GATE_POLICY_VERSION",
    "ReleaseGateApplicability",
    "ReleaseGateDefinition",
    "ReleaseGatePhase",
    "active_release_gates",
    "build_release_gate_registry",
    "decision_gate_definition",
    "evaluation_gate_definitions",
    "get_release_gate",
    "inactive_conditional_gates",
    "index_release_gate_registry",
    "iter_release_gates",
    "require_release_gate",
    "validate_release_gate_registry",
)
