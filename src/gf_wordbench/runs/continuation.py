"""Dependency-aware continuation policy for GF Wordbench runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final

from gf_wordbench.kernel.statuses import ValidationMode, ValidationStatus

__all__ = (
    "ContinuationAction",
    "ContinuationDecision",
    "ContinuationFacts",
    "ContinuationPolicy",
    "ContinuationReason",
    "decide_continuation",
)


@unique
class ContinuationAction(StrEnum):
    """Scheduling action selected by the run continuation policy."""

    CONTINUE = "continue"
    SKIP_DEPENDENT = "skip_dependent"
    FINALIZE = "finalize"
    ABORT = "abort"


@unique
class ContinuationReason(StrEnum):
    """Stable reason vocabulary for continuation decisions."""

    READY = "ready"
    ORDINARY_FAILURE_CONTAINED = "ordinary_failure_contained"
    OPTIONAL_FAILURE_CONTAINED = "optional_failure_contained"
    RELEASE_EVIDENCE_COLLECTION = "release_evidence_collection"
    PREREQUISITE_FAILED = "prerequisite_failed"
    FAIL_FAST = "fail_fast"
    CANCELLATION = "cancellation"
    BUDGET_EXHAUSTED = "budget_exhausted"
    UNSAFE_TO_CONTINUE = "unsafe_to_continue"
    EVIDENCE_UNTRUSTWORTHY = "evidence_untrustworthy"
    NO_MEANINGFUL_WORK = "no_meaningful_work"
    FINALIZATION_UNAVAILABLE = "finalization_unavailable"
    CONFIGURATION_INVALID = "configuration_invalid"
    TOOL_UNAVAILABLE = "tool_unavailable"
    SOURCE_ROOT_UNAVAILABLE = "source_root_unavailable"
    OUTPUT_UNUSABLE = "output_unusable"
    CONTAINMENT_VIOLATION = "containment_violation"
    SECURITY_VIOLATION = "security_violation"
    RESULT_CONTRACT_INVALID = "result_contract_invalid"
    INFRASTRUCTURE_UNRELIABLE = "infrastructure_unreliable"


_GLOBAL_BLOCKING_REASONS: Final[frozenset[ContinuationReason]] = frozenset(
    {
        ContinuationReason.CONFIGURATION_INVALID,
        ContinuationReason.TOOL_UNAVAILABLE,
        ContinuationReason.SOURCE_ROOT_UNAVAILABLE,
        ContinuationReason.OUTPUT_UNUSABLE,
        ContinuationReason.CONTAINMENT_VIOLATION,
        ContinuationReason.SECURITY_VIOLATION,
        ContinuationReason.RESULT_CONTRACT_INVALID,
        ContinuationReason.INFRASTRUCTURE_UNRELIABLE,
    }
)

_FAILURE_STATUSES: Final[frozenset[ValidationStatus]] = frozenset(
    {
        ValidationStatus.FAIL,
        ValidationStatus.ERROR,
    }
)

_REASON_MESSAGES: Final[dict[ContinuationReason, str]] = {
    ContinuationReason.READY: (
        "Independent work remains safe, bounded, meaningful, and eligible to run."
    ),
    ContinuationReason.ORDINARY_FAILURE_CONTAINED: (
        "The completed failure is contained and independent evidence remains useful."
    ),
    ContinuationReason.OPTIONAL_FAILURE_CONTAINED: (
        "The optional failure remains visible but does not block independent work."
    ),
    ContinuationReason.RELEASE_EVIDENCE_COLLECTION: (
        "Release success is no longer possible, but safe bounded gating evidence remains useful."
    ),
    ContinuationReason.PREREQUISITE_FAILED: (
        "The work is blocked by one or more failed or unavailable prerequisites."
    ),
    ContinuationReason.FAIL_FAST: (
        "Fail-fast stopped new work after the first gating failure."
    ),
    ContinuationReason.CANCELLATION: (
        "Cancellation stopped scheduling new work."
    ),
    ContinuationReason.BUDGET_EXHAUSTED: (
        "The usable execution budget is exhausted or insufficient."
    ),
    ContinuationReason.UNSAFE_TO_CONTINUE: (
        "Starting additional work would violate execution safety."
    ),
    ContinuationReason.EVIDENCE_UNTRUSTWORTHY: (
        "Additional execution could produce misleading or untrustworthy evidence."
    ),
    ContinuationReason.NO_MEANINGFUL_WORK: (
        "No safe and meaningful validation work remains."
    ),
    ContinuationReason.FINALIZATION_UNAVAILABLE: (
        "A reliable run result cannot be finalized."
    ),
    ContinuationReason.CONFIGURATION_INVALID: (
        "Required project or run configuration is invalid."
    ),
    ContinuationReason.TOOL_UNAVAILABLE: (
        "The required shared tool cannot be launched or used reliably."
    ),
    ContinuationReason.SOURCE_ROOT_UNAVAILABLE: (
        "The required project source root is unavailable."
    ),
    ContinuationReason.OUTPUT_UNUSABLE: (
        "The run output location cannot preserve required evidence."
    ),
    ContinuationReason.CONTAINMENT_VIOLATION: (
        "An output or path containment boundary was violated."
    ),
    ContinuationReason.SECURITY_VIOLATION: (
        "A security boundary violation prevents further scheduling."
    ),
    ContinuationReason.RESULT_CONTRACT_INVALID: (
        "The internal structured-result contract is invalid."
    ),
    ContinuationReason.INFRASTRUCTURE_UNRELIABLE: (
        "Repeated infrastructure failure makes remaining execution unreliable."
    ),
}


def _require_bool(value: object, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a bool")
    return value


def _normalize_blockers(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("blocked_by must be a tuple of stable subject IDs")

    normalized: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"blocked_by[{index}] must be a string")
        if not value or "\x00" in value:
            raise ValueError(
                f"blocked_by[{index}] must be non-empty and contain no NUL"
            )
        if value not in seen:
            seen.add(value)
            normalized.append(value)

    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class ContinuationFacts:
    """Facts available when deciding whether another work item may start."""

    completed_status: ValidationStatus | None = None
    completed_required: bool = False
    completed_gating: bool = False
    cancellation_requested: bool = False
    budget_available: bool = True
    scheduling_safe: bool = True
    evidence_trustworthy: bool = True
    finalization_available: bool = True
    prerequisites_available: bool = True
    remaining_work_meaningful: bool = True
    global_blocker: ContinuationReason | None = None
    blocked_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.completed_status is not None
            and not isinstance(self.completed_status, ValidationStatus)
        ):
            raise TypeError(
                "completed_status must be a ValidationStatus or None"
            )

        for field_name in (
            "completed_required",
            "completed_gating",
            "cancellation_requested",
            "budget_available",
            "scheduling_safe",
            "evidence_trustworthy",
            "finalization_available",
            "prerequisites_available",
            "remaining_work_meaningful",
        ):
            _require_bool(
                getattr(self, field_name),
                field_name=field_name,
            )

        if self.completed_status is None and (
            self.completed_required or self.completed_gating
        ):
            raise ValueError(
                "completed requiredness and gating require completed_status"
            )

        if self.completed_gating and not self.completed_required:
            raise ValueError("a gating completed item must be required")

        if (
            self.global_blocker is not None
            and not isinstance(self.global_blocker, ContinuationReason)
        ):
            raise TypeError(
                "global_blocker must be a ContinuationReason or None"
            )

        if (
            self.global_blocker is not None
            and self.global_blocker not in _GLOBAL_BLOCKING_REASONS
        ):
            raise ValueError(
                "global_blocker must use a global blocking reason"
            )

        blockers = _normalize_blockers(tuple(self.blocked_by))
        object.__setattr__(self, "blocked_by", blockers)

        if self.prerequisites_available and blockers:
            raise ValueError(
                "blocked_by must be empty when prerequisites are available"
            )

        if not self.prerequisites_available and not blockers:
            raise ValueError(
                "unavailable prerequisites require at least one blocker ID"
            )

        if (
            self.global_blocker is not None
            and not self.prerequisites_available
        ):
            raise ValueError(
                "global_blocker and unavailable item prerequisites are distinct"
            )


@dataclass(frozen=True, slots=True)
class ContinuationDecision:
    """Immutable scheduling decision returned to the run orchestrator."""

    action: ContinuationAction
    reason: ContinuationReason
    message: str
    blocked_by: tuple[str, ...] = ()
    trigger_status: ValidationStatus | None = None
    gating_failure_observed: bool = False
    plan_incomplete: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.action, ContinuationAction):
            raise TypeError("action must be a ContinuationAction")
        if not isinstance(self.reason, ContinuationReason):
            raise TypeError("reason must be a ContinuationReason")
        if not isinstance(self.message, str):
            raise TypeError("message must be a string")
        if not self.message or "\x00" in self.message:
            raise ValueError("message must be non-empty and contain no NUL")
        if (
            self.trigger_status is not None
            and not isinstance(self.trigger_status, ValidationStatus)
        ):
            raise TypeError(
                "trigger_status must be a ValidationStatus or None"
            )

        _require_bool(
            self.gating_failure_observed,
            field_name="gating_failure_observed",
        )
        _require_bool(
            self.plan_incomplete,
            field_name="plan_incomplete",
        )

        blockers = _normalize_blockers(tuple(self.blocked_by))
        object.__setattr__(self, "blocked_by", blockers)

        if self.action is ContinuationAction.SKIP_DEPENDENT:
            if self.reason is not ContinuationReason.PREREQUISITE_FAILED:
                raise ValueError(
                    "skip_dependent requires reason prerequisite_failed"
                )
            if not blockers:
                raise ValueError(
                    "skip_dependent requires at least one blocker ID"
                )
        elif blockers:
            raise ValueError(
                "blocked_by is reserved for skip_dependent decisions"
            )

        if self.action is ContinuationAction.CONTINUE and self.plan_incomplete:
            raise ValueError(
                "a continue decision cannot mark the plan incomplete"
            )

        if (
            self.gating_failure_observed
            and self.trigger_status not in _FAILURE_STATUSES
        ):
            raise ValueError(
                "gating_failure_observed requires FAIL or ERROR"
            )

        if (
            self.reason
            is ContinuationReason.RELEASE_EVIDENCE_COLLECTION
            and (
                self.action is not ContinuationAction.CONTINUE
                or not self.gating_failure_observed
            )
        ):
            raise ValueError(
                "release evidence collection requires continued work "
                "after a gating failure"
            )

    @property
    def may_start_new_work(self) -> bool:
        return self.action is ContinuationAction.CONTINUE

    @property
    def skips_current_work(self) -> bool:
        return self.action is ContinuationAction.SKIP_DEPENDENT

    @property
    def should_finalize(self) -> bool:
        return self.action is ContinuationAction.FINALIZE

    @property
    def can_emit_run_result(self) -> bool:
        return self.action is not ContinuationAction.ABORT


@dataclass(frozen=True, slots=True)
class ContinuationPolicy:
    """Mode-aware policy applied by the run orchestrator."""

    mode: ValidationMode
    fail_fast: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        _require_bool(self.fail_fast, field_name="fail_fast")

    def decide(self, facts: ContinuationFacts) -> ContinuationDecision:
        if not isinstance(facts, ContinuationFacts):
            raise TypeError("facts must be ContinuationFacts")

        if facts.global_blocker is not None:
            return _terminal_decision(
                facts=facts,
                reason=facts.global_blocker,
            )

        if facts.cancellation_requested:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.CANCELLATION,
            )

        if not facts.scheduling_safe:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.UNSAFE_TO_CONTINUE,
            )

        if not facts.evidence_trustworthy:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.EVIDENCE_UNTRUSTWORTHY,
            )

        if not facts.budget_available:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.BUDGET_EXHAUSTED,
            )

        if not facts.prerequisites_available:
            return _decision(
                action=ContinuationAction.SKIP_DEPENDENT,
                reason=ContinuationReason.PREREQUISITE_FAILED,
                facts=facts,
                blocked_by=facts.blocked_by,
            )

        trigger_is_failure = facts.completed_status in _FAILURE_STATUSES
        gating_failure = trigger_is_failure and facts.completed_gating

        if self.fail_fast and gating_failure:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.FAIL_FAST,
                gating_failure_observed=True,
            )

        if not facts.remaining_work_meaningful:
            return _terminal_decision(
                facts=facts,
                reason=ContinuationReason.NO_MEANINGFUL_WORK,
                plan_incomplete=False,
                gating_failure_observed=gating_failure,
            )

        if trigger_is_failure:
            if self.mode is ValidationMode.RELEASE and gating_failure:
                return _decision(
                    action=ContinuationAction.CONTINUE,
                    reason=ContinuationReason.RELEASE_EVIDENCE_COLLECTION,
                    facts=facts,
                    gating_failure_observed=True,
                )

            if facts.completed_required:
                return _decision(
                    action=ContinuationAction.CONTINUE,
                    reason=ContinuationReason.ORDINARY_FAILURE_CONTAINED,
                    facts=facts,
                    gating_failure_observed=gating_failure,
                )

            return _decision(
                action=ContinuationAction.CONTINUE,
                reason=ContinuationReason.OPTIONAL_FAILURE_CONTAINED,
                facts=facts,
            )

        return _decision(
            action=ContinuationAction.CONTINUE,
            reason=ContinuationReason.READY,
            facts=facts,
        )


def _decision(
    *,
    action: ContinuationAction,
    reason: ContinuationReason,
    facts: ContinuationFacts,
    blocked_by: tuple[str, ...] = (),
    gating_failure_observed: bool = False,
    plan_incomplete: bool = False,
) -> ContinuationDecision:
    return ContinuationDecision(
        action=action,
        reason=reason,
        message=_REASON_MESSAGES[reason],
        blocked_by=blocked_by,
        trigger_status=facts.completed_status,
        gating_failure_observed=gating_failure_observed,
        plan_incomplete=plan_incomplete,
    )


def _terminal_decision(
    *,
    facts: ContinuationFacts,
    reason: ContinuationReason,
    plan_incomplete: bool = True,
    gating_failure_observed: bool = False,
) -> ContinuationDecision:
    if facts.finalization_available:
        return _decision(
            action=ContinuationAction.FINALIZE,
            reason=reason,
            facts=facts,
            gating_failure_observed=gating_failure_observed,
            plan_incomplete=plan_incomplete,
        )

    return _decision(
        action=ContinuationAction.ABORT,
        reason=ContinuationReason.FINALIZATION_UNAVAILABLE,
        facts=facts,
        gating_failure_observed=gating_failure_observed,
        plan_incomplete=True,
    )


def decide_continuation(
    policy: ContinuationPolicy,
    facts: ContinuationFacts,
) -> ContinuationDecision:
    """Return the canonical continuation decision for the supplied facts."""

    if not isinstance(policy, ContinuationPolicy):
        raise TypeError("policy must be a ContinuationPolicy")
    return policy.decide(facts)
