"""Unit tests for dependency-aware run continuation policy."""

from __future__ import annotations

from dataclasses import replace

import pytest

from gf_wordbench.kernel.statuses import ValidationMode, ValidationStatus
from gf_wordbench.runs.continuation import (
    ContinuationAction,
    ContinuationDecision,
    ContinuationFacts,
    ContinuationPolicy,
    ContinuationReason,
    decide_continuation,
)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (ValidationMode.QUICK, ContinuationReason.READY),
        (ValidationMode.CHECKPOINT, ContinuationReason.READY),
        (ValidationMode.DIAGNOSTIC, ContinuationReason.READY),
        (ValidationMode.RELEASE, ContinuationReason.READY),
    ],
)
def test_ready_work_continues_in_every_mode(
    mode: ValidationMode,
    expected: ContinuationReason,
) -> None:
    decision = ContinuationPolicy(mode).decide(ContinuationFacts())

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is expected
    assert decision.trigger_status is None
    assert decision.blocked_by == ()
    assert decision.gating_failure_observed is False
    assert decision.plan_incomplete is False
    assert decision.may_start_new_work is True
    assert decision.skips_current_work is False
    assert decision.should_finalize is False
    assert decision.can_emit_run_result is True


@pytest.mark.parametrize(
    "status",
    [ValidationStatus.OK, ValidationStatus.SKIPPED],
)
def test_non_failure_completion_keeps_independent_work_running(
    status: ValidationStatus,
) -> None:
    decision = decide_continuation(
        ContinuationPolicy(ValidationMode.DIAGNOSTIC),
        ContinuationFacts(completed_status=status),
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.READY
    assert decision.trigger_status is status


@pytest.mark.parametrize(
    "status",
    [ValidationStatus.FAIL, ValidationStatus.ERROR],
)
def test_required_failure_is_contained_outside_fail_fast(
    status: ValidationStatus,
) -> None:
    decision = ContinuationPolicy(ValidationMode.DIAGNOSTIC).decide(
        ContinuationFacts(
            completed_status=status,
            completed_required=True,
        )
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.ORDINARY_FAILURE_CONTAINED
    assert decision.trigger_status is status
    assert decision.gating_failure_observed is False


@pytest.mark.parametrize(
    "status",
    [ValidationStatus.FAIL, ValidationStatus.ERROR],
)
def test_optional_failure_remains_visible_but_independent_work_continues(
    status: ValidationStatus,
) -> None:
    decision = ContinuationPolicy(ValidationMode.CHECKPOINT).decide(
        ContinuationFacts(completed_status=status)
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.OPTIONAL_FAILURE_CONTAINED
    assert decision.trigger_status is status
    assert decision.gating_failure_observed is False


def test_release_gating_failure_collects_remaining_safe_evidence() -> None:
    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(
        ContinuationFacts(
            completed_status=ValidationStatus.FAIL,
            completed_required=True,
            completed_gating=True,
        )
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.RELEASE_EVIDENCE_COLLECTION
    assert decision.trigger_status is ValidationStatus.FAIL
    assert decision.gating_failure_observed is True
    assert decision.plan_incomplete is False


@pytest.mark.parametrize(
    "mode",
    [
        ValidationMode.QUICK,
        ValidationMode.CHECKPOINT,
        ValidationMode.DIAGNOSTIC,
    ],
)
def test_non_release_gating_failure_uses_ordinary_containment(
    mode: ValidationMode,
) -> None:
    decision = ContinuationPolicy(mode).decide(
        ContinuationFacts(
            completed_status=ValidationStatus.ERROR,
            completed_required=True,
            completed_gating=True,
        )
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.ORDINARY_FAILURE_CONTAINED
    assert decision.gating_failure_observed is True


@pytest.mark.parametrize(
    "status",
    [ValidationStatus.FAIL, ValidationStatus.ERROR],
)
def test_fail_fast_finalizes_after_gating_failure(
    status: ValidationStatus,
) -> None:
    decision = ContinuationPolicy(
        ValidationMode.DIAGNOSTIC,
        fail_fast=True,
    ).decide(
        ContinuationFacts(
            completed_status=status,
            completed_required=True,
            completed_gating=True,
        )
    )

    assert decision.action is ContinuationAction.FINALIZE
    assert decision.reason is ContinuationReason.FAIL_FAST
    assert decision.trigger_status is status
    assert decision.gating_failure_observed is True
    assert decision.plan_incomplete is True


def test_fail_fast_does_not_stop_after_non_gating_failure() -> None:
    decision = ContinuationPolicy(
        ValidationMode.DIAGNOSTIC,
        fail_fast=True,
    ).decide(
        ContinuationFacts(
            completed_status=ValidationStatus.FAIL,
            completed_required=True,
        )
    )

    assert decision.action is ContinuationAction.CONTINUE
    assert decision.reason is ContinuationReason.ORDINARY_FAILURE_CONTAINED


def test_unavailable_prerequisites_skip_only_dependent_work() -> None:
    facts = ContinuationFacts(
        prerequisites_available=False,
        blocked_by=("compile:Main", "compile:Main", "version-probe"),
    )

    assert facts.blocked_by == ("compile:Main", "version-probe")

    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(facts)

    assert decision.action is ContinuationAction.SKIP_DEPENDENT
    assert decision.reason is ContinuationReason.PREREQUISITE_FAILED
    assert decision.blocked_by == ("compile:Main", "version-probe")
    assert decision.plan_incomplete is False
    assert decision.may_start_new_work is False
    assert decision.skips_current_work is True
    assert decision.should_finalize is False
    assert decision.can_emit_run_result is True


@pytest.mark.parametrize(
    ("facts", "reason", "plan_incomplete"),
    [
        (
            ContinuationFacts(cancellation_requested=True),
            ContinuationReason.CANCELLATION,
            True,
        ),
        (
            ContinuationFacts(scheduling_safe=False),
            ContinuationReason.UNSAFE_TO_CONTINUE,
            True,
        ),
        (
            ContinuationFacts(evidence_trustworthy=False),
            ContinuationReason.EVIDENCE_UNTRUSTWORTHY,
            True,
        ),
        (
            ContinuationFacts(budget_available=False),
            ContinuationReason.BUDGET_EXHAUSTED,
            True,
        ),
        (
            ContinuationFacts(remaining_work_meaningful=False),
            ContinuationReason.NO_MEANINGFUL_WORK,
            False,
        ),
    ],
)
def test_terminal_conditions_enter_finalization(
    facts: ContinuationFacts,
    reason: ContinuationReason,
    plan_incomplete: bool,
) -> None:
    decision = ContinuationPolicy(ValidationMode.DIAGNOSTIC).decide(facts)

    assert decision.action is ContinuationAction.FINALIZE
    assert decision.reason is reason
    assert decision.plan_incomplete is plan_incomplete
    assert decision.should_finalize is True
    assert decision.can_emit_run_result is True


@pytest.mark.parametrize(
    "reason",
    [
        ContinuationReason.CONFIGURATION_INVALID,
        ContinuationReason.TOOL_UNAVAILABLE,
        ContinuationReason.SOURCE_ROOT_UNAVAILABLE,
        ContinuationReason.OUTPUT_UNUSABLE,
        ContinuationReason.CONTAINMENT_VIOLATION,
        ContinuationReason.SECURITY_VIOLATION,
        ContinuationReason.RESULT_CONTRACT_INVALID,
        ContinuationReason.INFRASTRUCTURE_UNRELIABLE,
    ],
)
def test_global_blockers_finalize_with_stable_reason(
    reason: ContinuationReason,
) -> None:
    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(
        ContinuationFacts(global_blocker=reason)
    )

    assert decision.action is ContinuationAction.FINALIZE
    assert decision.reason is reason
    assert decision.plan_incomplete is True
    assert decision.message


def test_finalization_unavailable_aborts_without_fabricating_result() -> None:
    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(
        ContinuationFacts(
            cancellation_requested=True,
            finalization_available=False,
        )
    )

    assert decision.action is ContinuationAction.ABORT
    assert decision.reason is ContinuationReason.FINALIZATION_UNAVAILABLE
    assert decision.plan_incomplete is True
    assert decision.may_start_new_work is False
    assert decision.should_finalize is False
    assert decision.can_emit_run_result is False


def test_global_blocker_has_precedence_over_other_terminal_facts() -> None:
    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(
        ContinuationFacts(
            global_blocker=ContinuationReason.SECURITY_VIOLATION,
            cancellation_requested=True,
            scheduling_safe=False,
            evidence_trustworthy=False,
            budget_available=False,
            remaining_work_meaningful=False,
        )
    )

    assert decision.reason is ContinuationReason.SECURITY_VIOLATION


def test_cancellation_has_precedence_over_safety_and_budget() -> None:
    decision = ContinuationPolicy(ValidationMode.DIAGNOSTIC).decide(
        ContinuationFacts(
            cancellation_requested=True,
            scheduling_safe=False,
            evidence_trustworthy=False,
            budget_available=False,
        )
    )

    assert decision.reason is ContinuationReason.CANCELLATION


def test_safety_has_precedence_over_evidence_and_budget() -> None:
    decision = ContinuationPolicy(ValidationMode.DIAGNOSTIC).decide(
        ContinuationFacts(
            scheduling_safe=False,
            evidence_trustworthy=False,
            budget_available=False,
        )
    )

    assert decision.reason is ContinuationReason.UNSAFE_TO_CONTINUE


def test_evidence_trust_has_precedence_over_budget() -> None:
    decision = ContinuationPolicy(ValidationMode.DIAGNOSTIC).decide(
        ContinuationFacts(
            evidence_trustworthy=False,
            budget_available=False,
        )
    )

    assert decision.reason is ContinuationReason.EVIDENCE_UNTRUSTWORTHY


def test_prerequisite_skip_precedes_completed_failure_policy() -> None:
    decision = ContinuationPolicy(
        ValidationMode.RELEASE,
        fail_fast=True,
    ).decide(
        ContinuationFacts(
            completed_status=ValidationStatus.FAIL,
            completed_required=True,
            completed_gating=True,
            prerequisites_available=False,
            blocked_by=("compile:Main",),
        )
    )

    assert decision.action is ContinuationAction.SKIP_DEPENDENT
    assert decision.reason is ContinuationReason.PREREQUISITE_FAILED
    assert decision.gating_failure_observed is False


def test_no_meaningful_work_preserves_observed_gating_failure() -> None:
    decision = ContinuationPolicy(ValidationMode.RELEASE).decide(
        ContinuationFacts(
            completed_status=ValidationStatus.ERROR,
            completed_required=True,
            completed_gating=True,
            remaining_work_meaningful=False,
        )
    )

    assert decision.action is ContinuationAction.FINALIZE
    assert decision.reason is ContinuationReason.NO_MEANINGFUL_WORK
    assert decision.gating_failure_observed is True
    assert decision.plan_incomplete is False


@pytest.mark.parametrize(
    "field_name",
    [
        "completed_required",
        "completed_gating",
        "cancellation_requested",
        "budget_available",
        "scheduling_safe",
        "evidence_trustworthy",
        "finalization_available",
        "prerequisites_available",
        "remaining_work_meaningful",
    ],
)
def test_facts_reject_non_boolean_flags(field_name: str) -> None:
    with pytest.raises(TypeError, match=field_name):
        ContinuationFacts(**{field_name: 1})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"completed_required": True},
        {"completed_gating": True},
        {
            "completed_status": ValidationStatus.FAIL,
            "completed_gating": True,
        },
    ],
)
def test_completed_requiredness_and_gating_invariants(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ContinuationFacts(**kwargs)  # type: ignore[arg-type]


def test_facts_reject_invalid_status_and_global_blocker_types() -> None:
    with pytest.raises(TypeError, match="completed_status"):
        ContinuationFacts(completed_status="FAIL")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="global_blocker"):
        ContinuationFacts(global_blocker="security_violation")  # type: ignore[arg-type]


def test_facts_accept_only_global_reasons_as_global_blockers() -> None:
    with pytest.raises(ValueError, match="global blocking reason"):
        ContinuationFacts(global_blocker=ContinuationReason.CANCELLATION)


def test_prerequisite_blocker_invariants() -> None:
    with pytest.raises(ValueError, match="must be empty"):
        ContinuationFacts(blocked_by=("compile:Main",))

    with pytest.raises(ValueError, match="at least one blocker"):
        ContinuationFacts(prerequisites_available=False)

    with pytest.raises(ValueError, match="distinct"):
        ContinuationFacts(
            prerequisites_available=False,
            blocked_by=("compile:Main",),
            global_blocker=ContinuationReason.TOOL_UNAVAILABLE,
        )


@pytest.mark.parametrize(
    "blocked_by",
    [
        ("",),
        ("bad\x00id",),
    ],
)
def test_blocker_ids_must_be_nonempty_and_nul_free(
    blocked_by: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="blocked_by"):
        ContinuationFacts(
            prerequisites_available=False,
            blocked_by=blocked_by,
        )


def test_blocker_ids_must_be_strings() -> None:
    with pytest.raises(TypeError, match=r"blocked_by\[0\]"):
        ContinuationFacts(
            prerequisites_available=False,
            blocked_by=(1,),  # type: ignore[arg-type]
        )


def test_policy_and_facade_reject_wrong_types() -> None:
    with pytest.raises(TypeError, match="mode"):
        ContinuationPolicy("release")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="fail_fast"):
        ContinuationPolicy(ValidationMode.RELEASE, fail_fast=1)  # type: ignore[arg-type]

    policy = ContinuationPolicy(ValidationMode.RELEASE)
    with pytest.raises(TypeError, match="facts"):
        policy.decide(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="policy"):
        decide_continuation(object(), ContinuationFacts())  # type: ignore[arg-type]


def test_decision_properties_cover_every_action() -> None:
    continue_decision = ContinuationDecision(
        action=ContinuationAction.CONTINUE,
        reason=ContinuationReason.READY,
        message="ready",
    )
    skip_decision = ContinuationDecision(
        action=ContinuationAction.SKIP_DEPENDENT,
        reason=ContinuationReason.PREREQUISITE_FAILED,
        message="blocked",
        blocked_by=("compile:Main",),
    )
    finalize_decision = ContinuationDecision(
        action=ContinuationAction.FINALIZE,
        reason=ContinuationReason.CANCELLATION,
        message="cancelled",
        plan_incomplete=True,
    )
    abort_decision = ContinuationDecision(
        action=ContinuationAction.ABORT,
        reason=ContinuationReason.FINALIZATION_UNAVAILABLE,
        message="cannot finalize",
        plan_incomplete=True,
    )

    assert continue_decision.may_start_new_work is True
    assert skip_decision.skips_current_work is True
    assert finalize_decision.should_finalize is True
    assert abort_decision.can_emit_run_result is False


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("action", "continue", "action"),
        ("reason", "ready", "reason"),
        ("message", 1, "message"),
        ("trigger_status", "FAIL", "trigger_status"),
        ("gating_failure_observed", 1, "gating_failure_observed"),
        ("plan_incomplete", 1, "plan_incomplete"),
    ],
)
def test_decision_rejects_invalid_field_types(
    field_name: str,
    value: object,
    match: str,
) -> None:
    kwargs: dict[str, object] = {
        "action": ContinuationAction.CONTINUE,
        "reason": ContinuationReason.READY,
        "message": "ready",
    }
    kwargs[field_name] = value

    with pytest.raises(TypeError, match=match):
        ContinuationDecision(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("message", ["", "bad\x00message"])
def test_decision_message_must_be_nonempty_and_nul_free(message: str) -> None:
    with pytest.raises(ValueError, match="message"):
        ContinuationDecision(
            action=ContinuationAction.CONTINUE,
            reason=ContinuationReason.READY,
            message=message,
        )


def test_skip_decision_requires_prerequisite_reason_and_blockers() -> None:
    with pytest.raises(ValueError, match="reason prerequisite_failed"):
        ContinuationDecision(
            action=ContinuationAction.SKIP_DEPENDENT,
            reason=ContinuationReason.READY,
            message="invalid",
            blocked_by=("compile:Main",),
        )

    with pytest.raises(ValueError, match="at least one blocker"):
        ContinuationDecision(
            action=ContinuationAction.SKIP_DEPENDENT,
            reason=ContinuationReason.PREREQUISITE_FAILED,
            message="invalid",
        )


def test_blockers_are_reserved_for_skip_decisions() -> None:
    with pytest.raises(ValueError, match="reserved"):
        ContinuationDecision(
            action=ContinuationAction.CONTINUE,
            reason=ContinuationReason.READY,
            message="invalid",
            blocked_by=("compile:Main",),
        )


def test_continue_decision_cannot_mark_plan_incomplete() -> None:
    with pytest.raises(ValueError, match="continue decision"):
        ContinuationDecision(
            action=ContinuationAction.CONTINUE,
            reason=ContinuationReason.READY,
            message="invalid",
            plan_incomplete=True,
        )


def test_gating_failure_requires_failure_status() -> None:
    with pytest.raises(ValueError, match="FAIL or ERROR"):
        ContinuationDecision(
            action=ContinuationAction.FINALIZE,
            reason=ContinuationReason.FAIL_FAST,
            message="invalid",
            trigger_status=ValidationStatus.OK,
            gating_failure_observed=True,
            plan_incomplete=True,
        )


def test_release_evidence_reason_requires_continue_after_gating_failure() -> None:
    with pytest.raises(ValueError, match="release evidence collection"):
        ContinuationDecision(
            action=ContinuationAction.FINALIZE,
            reason=ContinuationReason.RELEASE_EVIDENCE_COLLECTION,
            message="invalid",
            trigger_status=ValidationStatus.FAIL,
            gating_failure_observed=True,
            plan_incomplete=True,
        )

    with pytest.raises(ValueError, match="release evidence collection"):
        ContinuationDecision(
            action=ContinuationAction.CONTINUE,
            reason=ContinuationReason.RELEASE_EVIDENCE_COLLECTION,
            message="invalid",
            trigger_status=ValidationStatus.FAIL,
        )


def test_fact_and_policy_models_are_immutable() -> None:
    facts = ContinuationFacts()
    policy = ContinuationPolicy(ValidationMode.QUICK)

    with pytest.raises(AttributeError):
        facts.budget_available = False  # type: ignore[misc]

    with pytest.raises(AttributeError):
        policy.fail_fast = True  # type: ignore[misc]

    assert replace(facts, budget_available=False).budget_available is False
