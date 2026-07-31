"""Unit tests for monotonic run-budget allocation and finalization reserve."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import pytest

import gf_wordbench.runs.budgets as budgets
from gf_wordbench.runs.budgets import (
    BudgetAllocation,
    BudgetDecision,
    BudgetDenialReason,
    BudgetKind,
    BudgetPhase,
    BudgetSnapshot,
    BudgetUnavailableError,
    RunBudget,
    create_run_budget,
)


@dataclass(slots=True)
class _Clock:
    value: float = 100.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _budget(
    clock: _Clock,
    *,
    total_sec: float = 60.0,
    reserve_sec: float = 10.0,
) -> RunBudget:
    return RunBudget(
        total_sec=total_sec,
        finalization_reserve_sec=reserve_sec,
        clock=clock,
    )


def test_public_api_and_enum_values_are_canonical() -> None:
    assert budgets.__all__ == (
        "BudgetAllocation",
        "BudgetDecision",
        "BudgetDenialReason",
        "BudgetKind",
        "BudgetPhase",
        "BudgetSnapshot",
        "BudgetUnavailableError",
        "Clock",
        "RunBudget",
        "create_run_budget",
    )
    assert tuple(member.value for member in BudgetPhase) == (
        "execution",
        "finalization",
        "closed",
    )
    assert tuple(member.value for member in BudgetKind) == (
        "stage",
        "finalization",
    )
    assert tuple(member.value for member in BudgetDenialReason) == (
        "finalization_started",
        "finalization_not_started",
        "run_closed",
        "cancelled",
        "execution_exhausted",
        "finalization_exhausted",
        "below_minimum",
        "already_active",
    )


def test_factory_creates_valid_budget_with_protected_reserve() -> None:
    clock = _Clock()

    budget = create_run_budget(
        total_sec=60,
        finalization_reserve_sec=10,
        clock=clock,
    )

    assert isinstance(budget, RunBudget)
    assert budget.total_sec == 60.0
    assert budget.finalization_reserve_sec == 10.0
    assert budget.started_at_monotonic == 100.0
    assert budget.execution_deadline_monotonic == 150.0
    assert budget.run_deadline_monotonic == 160.0

    snapshot = budget.snapshot()
    assert snapshot.phase is BudgetPhase.EXECUTION
    assert snapshot.elapsed_sec == 0.0
    assert snapshot.remaining_total_sec == 60.0
    assert snapshot.remaining_execution_sec == 50.0
    assert snapshot.remaining_finalization_sec == 0.0
    assert snapshot.execution_available is True
    assert snapshot.finalization_available is False
    assert snapshot.cancellation_reason is None
    assert snapshot.stop_reason is None
    assert snapshot.active_stage_names == ()
    assert snapshot.active_finalization_names == ()


@pytest.mark.parametrize(
    ("total_sec", "reserve_sec", "error", "message"),
    [
        (0, 1, ValueError, "total_sec must be positive"),
        (-1, 1, ValueError, "total_sec must be positive"),
        (math.inf, 1, ValueError, "total_sec must be finite"),
        (True, 1, TypeError, "total_sec must be a number"),
        (10, 0, ValueError, "finalization_reserve_sec must be positive"),
        (10, 10, ValueError, "must be smaller"),
        (10, 11, ValueError, "must be smaller"),
    ],
)
def test_budget_configuration_is_strictly_validated(
    total_sec: object,
    reserve_sec: object,
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        RunBudget(
            total_sec=total_sec,  # type: ignore[arg-type]
            finalization_reserve_sec=reserve_sec,  # type: ignore[arg-type]
        )


def test_clock_must_be_callable_and_return_a_finite_number() -> None:
    with pytest.raises(TypeError, match="clock must be callable"):
        RunBudget(
            total_sec=10,
            finalization_reserve_sec=1,
            clock=object(),  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="clock value must be a number"):
        RunBudget(
            total_sec=10,
            finalization_reserve_sec=1,
            clock=lambda: "now",  # type: ignore[return-value]
        )

    with pytest.raises(ValueError, match="clock value must be finite"):
        RunBudget(
            total_sec=10,
            finalization_reserve_sec=1,
            clock=lambda: math.nan,
        )


def test_stage_allocation_is_capped_before_finalization_reserve() -> None:
    clock = _Clock()
    budget = _budget(clock)

    allocation = budget.allocate_stage(
        "compile",
        requested_sec=60.0,
        minimum_sec=1.0,
    )

    assert allocation.token == 1
    assert allocation.kind is BudgetKind.STAGE
    assert allocation.name == "compile"
    assert allocation.requested_sec == 60.0
    assert allocation.minimum_sec == 1.0
    assert allocation.granted_sec == 50.0
    assert allocation.timeout_sec == 50.0
    assert allocation.allocated_at_monotonic == 100.0
    assert allocation.deadline_monotonic == 150.0
    assert allocation.run_deadline_monotonic == 160.0
    assert allocation.remaining_sec(125.0) == 25.0
    assert allocation.expired(149.0) is False
    assert allocation.expired(150.0) is True

    snapshot = budget.snapshot()
    assert snapshot.active_stage_names == ("compile",)
    assert budget.active_allocations() == (allocation,)


def test_stage_budget_uses_time_remaining_at_allocation() -> None:
    clock = _Clock()
    budget = _budget(clock)
    clock.advance(17.5)

    allocation = budget.allocate_stage(
        "scan",
        requested_sec=100.0,
        minimum_sec=1.0,
    )

    assert allocation.allocated_at_monotonic == 117.5
    assert allocation.granted_sec == 32.5
    assert allocation.deadline_monotonic == 150.0
    assert budget.remaining_total_sec() == 42.5
    assert budget.remaining_execution_sec() == 32.5
    assert budget.remaining_finalization_sec() == 0.0


def test_stage_request_below_minimum_returns_structured_denial() -> None:
    clock = _Clock()
    budget = _budget(clock, total_sec=20.0, reserve_sec=5.0)
    clock.advance(14.5)

    decision = budget.try_allocate_stage(
        "compile",
        requested_sec=2.0,
        minimum_sec=1.0,
    )

    assert decision.granted is False
    assert decision.allocation is None
    assert decision.denial_reason is BudgetDenialReason.BELOW_MINIMUM
    assert decision.available_sec == pytest.approx(0.5)
    assert decision.snapshot.phase is BudgetPhase.EXECUTION

    with pytest.raises(BudgetUnavailableError) as captured:
        decision.require()

    error = captured.value
    assert error.reason is BudgetDenialReason.BELOW_MINIMUM
    assert error.available_sec == pytest.approx(0.5)
    assert error.snapshot is decision.snapshot
    assert "below_minimum" in str(error)


def test_allocation_rejects_invalid_names_and_durations() -> None:
    budget = _budget(_Clock())

    for name in ("", "   ", "bad\x00name"):
        with pytest.raises(ValueError, match="name"):
            budget.try_allocate_stage(
                name,
                requested_sec=1,
                minimum_sec=1,
            )

    with pytest.raises(TypeError, match="name must be a string"):
        budget.try_allocate_stage(  # type: ignore[arg-type]
            1,
            requested_sec=1,
            minimum_sec=1,
        )

    with pytest.raises(ValueError, match="requested_sec must be positive"):
        budget.try_allocate_stage(
            "compile",
            requested_sec=0,
            minimum_sec=1,
        )

    with pytest.raises(ValueError, match="minimum_sec must be positive"):
        budget.try_allocate_stage(
            "compile",
            requested_sec=1,
            minimum_sec=0,
        )

    with pytest.raises(ValueError, match="must not exceed"):
        budget.try_allocate_stage(
            "compile",
            requested_sec=1,
            minimum_sec=2,
        )


def test_duplicate_active_name_is_denied_until_release() -> None:
    budget = _budget(_Clock())
    first = budget.allocate_stage(
        "compile",
        requested_sec=10,
        minimum_sec=1,
    )

    duplicate = budget.try_allocate_stage(
        "compile",
        requested_sec=10,
        minimum_sec=1,
    )

    assert duplicate.denial_reason is BudgetDenialReason.ALREADY_ACTIVE
    assert duplicate.available_sec == 50.0

    budget.release(first)
    second = budget.allocate_stage(
        "compile",
        requested_sec=10,
        minimum_sec=1,
    )
    assert second.token == 2


def test_active_allocations_are_returned_in_token_order() -> None:
    budget = _budget(_Clock())
    third_name_first = budget.allocate_stage(
        "zeta",
        requested_sec=5,
        minimum_sec=1,
    )
    first_name_second = budget.allocate_stage(
        "alpha",
        requested_sec=5,
        minimum_sec=1,
    )

    assert budget.active_allocations() == (third_name_first, first_name_second)
    assert budget.snapshot().active_stage_names == ("alpha", "zeta")


def test_context_manager_releases_stage_after_success_and_failure() -> None:
    budget = _budget(_Clock())

    with budget.stage(
        "scan",
        requested_sec=5,
        minimum_sec=1,
    ) as allocation:
        assert budget.active_allocations() == (allocation,)

    assert budget.active_allocations() == ()

    with pytest.raises(RuntimeError, match="stage failed"):
        with budget.stage(
            "compile",
            requested_sec=5,
            minimum_sec=1,
        ):
            raise RuntimeError("stage failed")

    assert budget.active_allocations() == ()


def test_release_is_idempotent_but_rejects_token_substitution() -> None:
    budget = _budget(_Clock())
    allocation = budget.allocate_stage(
        "compile",
        requested_sec=5,
        minimum_sec=1,
    )
    forged = replace(allocation, name="forged")

    with pytest.raises(ValueError, match="another allocation"):
        budget.release(forged)

    budget.release(allocation)
    budget.release(allocation)
    assert budget.active_allocations() == ()

    with pytest.raises(TypeError, match="BudgetAllocation"):
        budget.release(object())  # type: ignore[arg-type]


def test_remaining_for_tracks_active_deadline_and_requires_active_identity() -> None:
    clock = _Clock()
    budget = _budget(clock)
    allocation = budget.allocate_stage(
        "compile",
        requested_sec=20,
        minimum_sec=1,
    )

    clock.advance(7.5)
    assert budget.remaining_for(allocation) == pytest.approx(12.5)

    budget.release(allocation)
    with pytest.raises(ValueError, match="not active"):
        budget.remaining_for(allocation)


def test_bounded_timeout_never_exceeds_active_allocation() -> None:
    clock = _Clock()
    budget = _budget(clock)
    allocation = budget.allocate_stage(
        "compile",
        requested_sec=20,
        minimum_sec=1,
    )
    clock.advance(7.5)

    assert budget.bounded_timeout(
        allocation,
        requested_sec=30,
        minimum_sec=1,
    ) == pytest.approx(12.5)
    assert budget.bounded_timeout(
        allocation,
        requested_sec=3,
        minimum_sec=1,
    ) == 3.0

    with pytest.raises(BudgetUnavailableError) as captured:
        budget.bounded_timeout(
            allocation,
            requested_sec=20,
            minimum_sec=13,
        )
    assert captured.value.reason is BudgetDenialReason.BELOW_MINIMUM


def test_execution_deadline_automatically_enters_finalization() -> None:
    clock = _Clock()
    budget = _budget(clock, total_sec=20, reserve_sec=5)
    clock.advance(15)

    snapshot = budget.snapshot()

    assert snapshot.phase is BudgetPhase.FINALIZATION
    assert snapshot.stop_reason == "execution_budget_exhausted"
    assert snapshot.remaining_execution_sec == 0.0
    assert snapshot.remaining_finalization_sec == 5.0
    assert snapshot.execution_available is False
    assert snapshot.finalization_available is True

    denied = budget.try_allocate_stage(
        "late-stage",
        requested_sec=1,
        minimum_sec=1,
    )
    assert denied.denial_reason is BudgetDenialReason.EXECUTION_EXHAUSTED


def test_finalization_must_begin_before_finalization_allocation() -> None:
    budget = _budget(_Clock())

    decision = budget.try_allocate_finalization(
        "reports",
        requested_sec=5,
        minimum_sec=1,
    )

    assert decision.denial_reason is BudgetDenialReason.FINALIZATION_NOT_STARTED
    assert decision.available_sec == 0.0


def test_begin_finalization_is_idempotent_and_first_reason_wins() -> None:
    budget = _budget(_Clock())

    first = budget.begin_finalization(reason="execution complete")
    second = budget.begin_finalization(reason="ignored later reason")

    assert first.phase is BudgetPhase.FINALIZATION
    assert first.stop_reason == "execution complete"
    assert second.stop_reason == "execution complete"
    assert budget.stop_reason == "execution complete"

    denied = budget.try_allocate_stage(
        "late-stage",
        requested_sec=1,
        minimum_sec=1,
    )
    assert denied.denial_reason is BudgetDenialReason.FINALIZATION_STARTED


def test_finalization_uses_remaining_global_budget_not_only_nominal_reserve() -> None:
    clock = _Clock()
    budget = _budget(clock, total_sec=60, reserve_sec=10)
    clock.advance(20)
    snapshot = budget.begin_finalization(reason="fail-fast")

    assert snapshot.remaining_finalization_sec == 40.0

    allocation = budget.allocate_finalization(
        "publish",
        requested_sec=100,
        minimum_sec=1,
    )
    assert allocation.kind is BudgetKind.FINALIZATION
    assert allocation.granted_sec == 40.0
    assert allocation.deadline_monotonic == budget.run_deadline_monotonic


def test_finalization_context_manager_releases_on_failure() -> None:
    budget = _budget(_Clock())
    budget.begin_finalization(reason="execution complete")

    with pytest.raises(RuntimeError, match="publication failed"):
        with budget.finalization_task(
            "publisher",
            requested_sec=5,
            minimum_sec=1,
        ) as allocation:
            assert allocation.kind is BudgetKind.FINALIZATION
            raise RuntimeError("publication failed")

    assert budget.active_allocations() == ()


def test_cancellation_enters_finalization_and_preserves_first_reason() -> None:
    budget = _budget(_Clock())

    first = budget.cancel(reason="user requested cancellation")
    second = budget.cancel(reason="second request")

    assert first.phase is BudgetPhase.FINALIZATION
    assert first.cancellation_reason == "user requested cancellation"
    assert first.stop_reason == "cancelled"
    assert second.cancellation_reason == "user requested cancellation"
    assert budget.cancellation_reason == "user requested cancellation"

    denied = budget.try_allocate_stage(
        "compile",
        requested_sec=1,
        minimum_sec=1,
    )
    assert denied.denial_reason is BudgetDenialReason.CANCELLED

    finalization = budget.allocate_finalization(
        "cleanup",
        requested_sec=5,
        minimum_sec=1,
    )
    assert finalization.kind is BudgetKind.FINALIZATION


def test_close_clears_allocations_and_rejects_future_work() -> None:
    budget = _budget(_Clock())
    budget.allocate_stage(
        "compile",
        requested_sec=5,
        minimum_sec=1,
    )

    snapshot = budget.close(reason="completed")

    assert snapshot.phase is BudgetPhase.CLOSED
    assert snapshot.stop_reason == "completed"
    assert snapshot.active_stage_names == ()
    assert budget.active_allocations() == ()

    denied_stage = budget.try_allocate_stage(
        "scan",
        requested_sec=1,
        minimum_sec=1,
    )
    denied_finalization = budget.try_allocate_finalization(
        "reports",
        requested_sec=1,
        minimum_sec=1,
    )
    assert denied_stage.denial_reason is BudgetDenialReason.RUN_CLOSED
    assert denied_finalization.denial_reason is BudgetDenialReason.RUN_CLOSED


def test_global_deadline_closes_budget_with_exhaustion_reason() -> None:
    clock = _Clock()
    budget = _budget(clock, total_sec=20, reserve_sec=5)
    clock.advance(20)

    snapshot = budget.snapshot()

    assert snapshot.phase is BudgetPhase.CLOSED
    assert snapshot.stop_reason == "global_budget_exhausted"
    assert snapshot.elapsed_sec == 20.0
    assert snapshot.remaining_total_sec == 0.0
    assert snapshot.remaining_execution_sec == 0.0
    assert snapshot.remaining_finalization_sec == 0.0

    stage = budget.try_allocate_stage(
        "compile",
        requested_sec=1,
        minimum_sec=1,
    )
    finalization = budget.try_allocate_finalization(
        "publish",
        requested_sec=1,
        minimum_sec=1,
    )
    assert stage.denial_reason is BudgetDenialReason.EXECUTION_EXHAUSTED
    assert finalization.denial_reason is BudgetDenialReason.FINALIZATION_EXHAUSTED


def test_clock_moving_backwards_is_rejected() -> None:
    clock = _Clock()
    budget = _budget(clock)
    clock.advance(1)
    budget.snapshot()
    clock.value = 100.0

    with pytest.raises(RuntimeError, match="moved backwards"):
        budget.snapshot()


def test_budget_allocation_model_enforces_deadline_invariants() -> None:
    valid = BudgetAllocation(
        token=1,
        kind=BudgetKind.STAGE,
        name="compile",
        requested_sec=5,
        minimum_sec=1,
        granted_sec=5,
        allocated_at_monotonic=100,
        deadline_monotonic=105,
        run_deadline_monotonic=110,
    )
    assert valid.timeout_sec == 5.0

    with pytest.raises(ValueError, match="satisfy minimum"):
        replace(valid, minimum_sec=6)
    with pytest.raises(ValueError, match="not exceed requested"):
        replace(valid, granted_sec=6)
    with pytest.raises(ValueError, match="precede allocation"):
        replace(valid, deadline_monotonic=99)
    with pytest.raises(ValueError, match="not exceed run deadline"):
        replace(valid, deadline_monotonic=111)


def test_budget_decision_requires_exactly_one_outcome() -> None:
    snapshot = BudgetSnapshot(
        phase=BudgetPhase.EXECUTION,
        total_sec=10,
        finalization_reserve_sec=2,
        elapsed_sec=0,
        remaining_total_sec=10,
        remaining_execution_sec=8,
        remaining_finalization_sec=0,
        execution_deadline_monotonic=108,
        run_deadline_monotonic=110,
        cancellation_reason=None,
        stop_reason=None,
        active_stage_names=(),
        active_finalization_names=(),
    )

    with pytest.raises(ValueError, match="exactly one"):
        BudgetDecision(
            allocation=None,
            denial_reason=None,
            available_sec=8,
            snapshot=snapshot,
        )

    allocation = BudgetAllocation(
        token=1,
        kind=BudgetKind.STAGE,
        name="scan",
        requested_sec=1,
        minimum_sec=1,
        granted_sec=1,
        allocated_at_monotonic=100,
        deadline_monotonic=101,
        run_deadline_monotonic=110,
    )
    with pytest.raises(ValueError, match="exactly one"):
        BudgetDecision(
            allocation=allocation,
            denial_reason=BudgetDenialReason.BELOW_MINIMUM,
            available_sec=8,
            snapshot=snapshot,
        )
