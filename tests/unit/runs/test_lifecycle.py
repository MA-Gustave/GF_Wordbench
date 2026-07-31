"""Unit tests for the runs-owned lifecycle state machine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from gf_wordbench.runs.lifecycle import (
    ALLOWED_LIFECYCLE_TRANSITIONS,
    RunLifecycle,
    RunLifecycleState,
    RunLifecycleTransition,
    allowed_lifecycle_targets,
    can_transition_lifecycle,
    new_run_lifecycle,
    require_lifecycle_transition,
    transition_lifecycle,
)

_RUN_ID = "20260725_120000"
_ALLOCATED_AT = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

_EXPECTED_TRANSITIONS = {
    RunLifecycleState.ALLOCATED: frozenset({RunLifecycleState.INITIALIZED}),
    RunLifecycleState.INITIALIZED: frozenset(
        {
            RunLifecycleState.EXECUTING,
            RunLifecycleState.INCOMPLETE,
        }
    ),
    RunLifecycleState.EXECUTING: frozenset(
        {
            RunLifecycleState.FINALIZING,
            RunLifecycleState.INCOMPLETE,
        }
    ),
    RunLifecycleState.FINALIZING: frozenset(
        {
            RunLifecycleState.FINALIZED,
            RunLifecycleState.INCOMPLETE,
        }
    ),
    RunLifecycleState.FINALIZED: frozenset(
        {
            RunLifecycleState.CORRUPT,
            RunLifecycleState.ARCHIVED,
            RunLifecycleState.DELETED,
        }
    ),
    RunLifecycleState.INCOMPLETE: frozenset(
        {
            RunLifecycleState.ARCHIVED,
            RunLifecycleState.DELETED,
        }
    ),
    RunLifecycleState.CORRUPT: frozenset(
        {
            RunLifecycleState.ARCHIVED,
            RunLifecycleState.DELETED,
        }
    ),
    RunLifecycleState.ARCHIVED: frozenset(),
    RunLifecycleState.DELETED: frozenset(),
}


def _at(seconds: int) -> datetime:
    return _ALLOCATED_AT + timedelta(seconds=seconds)


def _transition_sequence(
    *states: RunLifecycleState,
) -> RunLifecycle:
    lifecycle = new_run_lifecycle(_RUN_ID, allocated_at=_ALLOCATED_AT)
    for revision, state in enumerate(states, start=1):
        lifecycle = lifecycle.transition(
            state,
            occurred_at=_at(revision),
            reason=(
                "controlled incomplete run"
                if state is RunLifecycleState.INCOMPLETE
                else "integrity verification failed"
                if state is RunLifecycleState.CORRUPT
                else None
            ),
        )
    return lifecycle


def _finalized_lifecycle() -> RunLifecycle:
    return _transition_sequence(
        RunLifecycleState.INITIALIZED,
        RunLifecycleState.EXECUTING,
        RunLifecycleState.FINALIZING,
        RunLifecycleState.FINALIZED,
    )


@pytest.mark.parametrize(
    (
        "state",
        "is_complete",
        "is_terminal",
        "is_mutable",
        "allows_stage_execution",
        "allows_finalization_writes",
        "is_previous_run_eligible",
    ),
    (
        (RunLifecycleState.ALLOCATED, False, False, False, False, False, False),
        (RunLifecycleState.INITIALIZED, False, False, True, True, False, False),
        (RunLifecycleState.EXECUTING, False, False, True, True, False, False),
        (RunLifecycleState.FINALIZING, False, False, True, False, True, False),
        (RunLifecycleState.FINALIZED, True, True, False, False, False, True),
        (RunLifecycleState.INCOMPLETE, False, True, False, False, False, False),
        (RunLifecycleState.CORRUPT, False, True, False, False, False, False),
        (RunLifecycleState.ARCHIVED, False, True, False, False, False, False),
        (RunLifecycleState.DELETED, False, True, False, False, False, False),
    ),
)
def test_state_properties_express_the_run_lifecycle_policy(
    state: RunLifecycleState,
    is_complete: bool,
    is_terminal: bool,
    is_mutable: bool,
    allows_stage_execution: bool,
    allows_finalization_writes: bool,
    is_previous_run_eligible: bool,
) -> None:
    assert state.is_complete is is_complete
    assert state.is_terminal is is_terminal
    assert state.is_mutable is is_mutable
    assert state.allows_stage_execution is allows_stage_execution
    assert state.allows_finalization_writes is allows_finalization_writes
    assert state.is_previous_run_eligible is is_previous_run_eligible


def test_transition_graph_is_complete_and_read_only() -> None:
    assert set(ALLOWED_LIFECYCLE_TRANSITIONS) == set(RunLifecycleState)

    for state, expected_targets in _EXPECTED_TRANSITIONS.items():
        assert allowed_lifecycle_targets(state) == expected_targets
        assert ALLOWED_LIFECYCLE_TRANSITIONS[state] == expected_targets
        assert all(can_transition_lifecycle(state, target) for target in expected_targets)

    with pytest.raises(TypeError):
        ALLOWED_LIFECYCLE_TRANSITIONS[
            RunLifecycleState.ALLOCATED
        ] = frozenset()  # type: ignore[index]


def test_new_lifecycle_normalizes_timestamp_and_preserves_identity() -> None:
    local_time = datetime(
        2026,
        7,
        25,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    lifecycle = new_run_lifecycle(_RUN_ID, allocated_at=local_time)

    assert str(lifecycle.run_id) == _RUN_ID
    assert lifecycle.state is RunLifecycleState.ALLOCATED
    assert lifecycle.allocated_at == _ALLOCATED_AT
    assert lifecycle.updated_at == _ALLOCATED_AT
    assert lifecycle.revision == 0
    assert lifecycle.history == ()
    assert not lifecycle.is_complete
    assert not lifecycle.is_terminal
    assert not lifecycle.is_mutable
    assert not lifecycle.is_previous_run_eligible


def test_canonical_completion_records_contiguous_immutable_history() -> None:
    lifecycle = new_run_lifecycle(_RUN_ID, allocated_at=_ALLOCATED_AT)
    original = lifecycle

    for revision, target in enumerate(
        (
            RunLifecycleState.INITIALIZED,
            RunLifecycleState.EXECUTING,
            RunLifecycleState.FINALIZING,
            RunLifecycleState.FINALIZED,
        ),
        start=1,
    ):
        previous = lifecycle
        lifecycle = transition_lifecycle(
            lifecycle,
            target,
            occurred_at=_at(revision),
        )

        transition = lifecycle.history[-1]
        assert transition.run_id == lifecycle.run_id
        assert transition.previous is previous.state
        assert transition.current is target
        assert transition.occurred_at == _at(revision)
        assert transition.revision == revision
        assert transition.reason is None
        assert lifecycle.revision == revision
        assert lifecycle.updated_at == _at(revision)
        assert previous.history == lifecycle.history[:-1]

    assert original.state is RunLifecycleState.ALLOCATED
    assert original.history == ()
    assert lifecycle.state is RunLifecycleState.FINALIZED
    assert lifecycle.is_complete
    assert lifecycle.is_terminal
    assert lifecycle.is_previous_run_eligible

    with pytest.raises(FrozenInstanceError):
        lifecycle.state = RunLifecycleState.EXECUTING  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        lifecycle.history[-1].reason = "changed"  # type: ignore[misc]


def test_same_state_transition_is_an_idempotent_no_op() -> None:
    lifecycle = _transition_sequence(RunLifecycleState.INITIALIZED)

    result = lifecycle.transition(
        RunLifecycleState.INITIALIZED,
        occurred_at=_at(20),
        reason="no new transition",
    )

    assert result is lifecycle
    assert result.revision == 1
    assert len(result.history) == 1


def test_same_state_is_allowed_but_not_listed_as_an_outgoing_target() -> None:
    for state in RunLifecycleState:
        assert can_transition_lifecycle(state, state)
        assert state not in allowed_lifecycle_targets(state)
        assert require_lifecycle_transition(state, state) is None


def test_incomplete_transition_requires_and_normalizes_a_reason() -> None:
    lifecycle = _transition_sequence(RunLifecycleState.INITIALIZED)

    with pytest.raises(ValueError, match="incomplete transitions require a reason"):
        lifecycle.transition(
            RunLifecycleState.INCOMPLETE,
            occurred_at=_at(2),
        )

    incomplete = lifecycle.transition(
        RunLifecycleState.INCOMPLETE,
        occurred_at=_at(2),
        reason="  cancelled before finalization  ",
    )

    assert incomplete.state is RunLifecycleState.INCOMPLETE
    assert incomplete.history[-1].reason == "cancelled before finalization"
    assert incomplete.is_terminal
    assert not incomplete.is_complete
    assert not incomplete.is_previous_run_eligible


def test_corrupt_transition_is_only_available_after_finalization() -> None:
    finalized = _finalized_lifecycle()

    with pytest.raises(ValueError, match="corrupt transitions require a reason"):
        finalized.transition(
            RunLifecycleState.CORRUPT,
            occurred_at=_at(5),
        )

    corrupt = finalized.transition(
        RunLifecycleState.CORRUPT,
        occurred_at=_at(5),
        reason="  manifest digest mismatch  ",
    )

    assert corrupt.state is RunLifecycleState.CORRUPT
    assert corrupt.history[-1].reason == "manifest digest mismatch"
    assert corrupt.is_terminal
    assert not corrupt.is_previous_run_eligible


def test_partial_and_verified_runs_support_explicit_retention_actions() -> None:
    finalized = _finalized_lifecycle()
    incomplete = _transition_sequence(
        RunLifecycleState.INITIALIZED,
        RunLifecycleState.INCOMPLETE,
    )
    corrupt = finalized.transition(
        RunLifecycleState.CORRUPT,
        occurred_at=_at(5),
        reason="verification failed",
    )

    for lifecycle in (finalized, incomplete, corrupt):
        archived = lifecycle.transition(
            RunLifecycleState.ARCHIVED,
            occurred_at=lifecycle.updated_at + timedelta(seconds=1),
        )
        deleted = lifecycle.transition(
            RunLifecycleState.DELETED,
            occurred_at=lifecycle.updated_at + timedelta(seconds=1),
        )

        assert archived.state is RunLifecycleState.ARCHIVED
        assert archived.is_terminal
        assert allowed_lifecycle_targets(archived.state) == frozenset()
        assert deleted.state is RunLifecycleState.DELETED
        assert deleted.is_terminal
        assert allowed_lifecycle_targets(deleted.state) == frozenset()


@pytest.mark.parametrize(
    ("current", "target"),
    (
        (RunLifecycleState.ALLOCATED, RunLifecycleState.EXECUTING),
        (RunLifecycleState.INITIALIZED, RunLifecycleState.FINALIZING),
        (RunLifecycleState.EXECUTING, RunLifecycleState.FINALIZED),
        (RunLifecycleState.FINALIZING, RunLifecycleState.ARCHIVED),
        (RunLifecycleState.INCOMPLETE, RunLifecycleState.EXECUTING),
        (RunLifecycleState.CORRUPT, RunLifecycleState.FINALIZED),
        (RunLifecycleState.ARCHIVED, RunLifecycleState.DELETED),
        (RunLifecycleState.DELETED, RunLifecycleState.ARCHIVED),
    ),
)
def test_prohibited_transitions_fail_closed(
    current: RunLifecycleState,
    target: RunLifecycleState,
) -> None:
    assert not can_transition_lifecycle(current, target)

    with pytest.raises(
        ValueError,
        match=rf"{current.value} -> {target.value}",
    ):
        require_lifecycle_transition(current, target)


def test_transition_rejects_a_timestamp_before_the_current_revision() -> None:
    lifecycle = _transition_sequence(RunLifecycleState.INITIALIZED)

    with pytest.raises(ValueError, match="must not precede"):
        lifecycle.transition(
            RunLifecycleState.EXECUTING,
            occurred_at=_ALLOCATED_AT,
        )


def test_equal_transition_timestamps_are_allowed_and_remain_monotonic() -> None:
    lifecycle = new_run_lifecycle(_RUN_ID, allocated_at=_ALLOCATED_AT)
    initialized = lifecycle.transition(
        RunLifecycleState.INITIALIZED,
        occurred_at=_ALLOCATED_AT,
    )
    executing = initialized.transition(
        RunLifecycleState.EXECUTING,
        occurred_at=_ALLOCATED_AT,
    )

    assert executing.updated_at == _ALLOCATED_AT
    assert [item.occurred_at for item in executing.history] == [
        _ALLOCATED_AT,
        _ALLOCATED_AT,
    ]


@pytest.mark.parametrize(
    ("factory", "expected_exception", "message"),
    (
        (
            lambda: new_run_lifecycle(_RUN_ID, allocated_at="now"),
            TypeError,
            "allocated_at must be a datetime",
        ),
        (
            lambda: new_run_lifecycle(
                _RUN_ID,
                allocated_at=datetime(2026, 7, 25, 12, 0),
            ),
            ValueError,
            "allocated_at must be timezone-aware",
        ),
        (
            lambda: transition_lifecycle(
                new_run_lifecycle(_RUN_ID, allocated_at=_ALLOCATED_AT),
                RunLifecycleState.INITIALIZED,
                occurred_at="later",
            ),
            TypeError,
            "occurred_at must be a datetime",
        ),
        (
            lambda: transition_lifecycle(
                new_run_lifecycle(_RUN_ID, allocated_at=_ALLOCATED_AT),
                RunLifecycleState.INITIALIZED,
                occurred_at=datetime(2026, 7, 25, 12, 0),
            ),
            ValueError,
            "occurred_at must be timezone-aware",
        ),
    ),
)
def test_timestamp_inputs_are_explicit_and_timezone_aware(
    factory: object,
    expected_exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(expected_exception, match=message):
        factory()  # type: ignore[operator]


@pytest.mark.parametrize(
    "reason",
    (
        "",
        "   ",
        "bad\x00reason",
        "x" * 2049,
    ),
)
def test_transition_reason_rejects_noncanonical_text(reason: str) -> None:
    lifecycle = _transition_sequence(RunLifecycleState.INITIALIZED)

    with pytest.raises(ValueError):
        lifecycle.transition(
            RunLifecycleState.INCOMPLETE,
            occurred_at=_at(2),
            reason=reason,
        )


def test_transition_reason_rejects_non_text_values() -> None:
    lifecycle = _transition_sequence(RunLifecycleState.INITIALIZED)

    with pytest.raises(TypeError, match="reason must be a string or None"):
        lifecycle.transition(
            RunLifecycleState.INCOMPLETE,
            occurred_at=_at(2),
            reason=42,  # type: ignore[arg-type]
        )


def test_direct_transition_model_normalizes_values() -> None:
    transition = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=datetime(
            2026,
            7,
            25,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        revision=1,
        reason="  directory tree created  ",
    )

    assert transition.occurred_at == _ALLOCATED_AT
    assert transition.reason == "directory tree created"


@pytest.mark.parametrize("revision", (True, 0, -1, 1.0, "1"))
def test_transition_revision_must_be_a_positive_plain_integer(
    revision: object,
) -> None:
    expected_exception = TypeError if type(revision) is not int else ValueError

    with pytest.raises(expected_exception):
        RunLifecycleTransition(
            run_id=_RUN_ID,
            previous=RunLifecycleState.ALLOCATED,
            current=RunLifecycleState.INITIALIZED,
            occurred_at=_ALLOCATED_AT,
            revision=revision,  # type: ignore[arg-type]
        )


def test_new_lifecycle_rejects_invalid_identity() -> None:
    with pytest.raises(ValueError):
        new_run_lifecycle("not-a-run-id", allocated_at=_ALLOCATED_AT)


def test_public_helpers_require_enum_states_and_lifecycle_models() -> None:
    with pytest.raises(TypeError, match="state must be a RunLifecycleState"):
        allowed_lifecycle_targets("allocated")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="current must be a RunLifecycleState"):
        can_transition_lifecycle(
            "allocated",  # type: ignore[arg-type]
            RunLifecycleState.INITIALIZED,
        )

    with pytest.raises(TypeError, match="target must be a RunLifecycleState"):
        require_lifecycle_transition(
            RunLifecycleState.ALLOCATED,
            "initialized",  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="lifecycle must be a RunLifecycle"):
        transition_lifecycle(
            object(),  # type: ignore[arg-type]
            RunLifecycleState.INITIALIZED,
            occurred_at=_ALLOCATED_AT,
        )


def test_lifecycle_without_history_must_be_newly_allocated() -> None:
    with pytest.raises(ValueError, match="without history must be allocated"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_ALLOCATED_AT,
        )

    with pytest.raises(ValueError, match="matching timestamps"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.ALLOCATED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
        )


def test_lifecycle_requires_revision_to_match_history_length() -> None:
    transition = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(1),
        revision=1,
    )

    with pytest.raises(ValueError, match="number of history entries"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=2,
            history=(transition,),
        )


def test_lifecycle_rejects_noncontiguous_transition_history() -> None:
    first = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(1),
        revision=1,
    )
    wrong_previous = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.EXECUTING,
        current=RunLifecycleState.FINALIZING,
        occurred_at=_at(2),
        revision=2,
    )

    with pytest.raises(ValueError, match="history is not contiguous"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.FINALIZING,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(2),
            revision=2,
            history=(first, wrong_previous),
        )


def test_lifecycle_rejects_noncontiguous_revisions() -> None:
    transition = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(1),
        revision=2,
    )

    with pytest.raises(ValueError, match="revisions must be contiguous"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=1,
            history=(transition,),
        )


def test_lifecycle_rejects_history_from_another_run() -> None:
    transition = RunLifecycleTransition(
        run_id="20260725_120001",
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(1),
        revision=1,
    )

    with pytest.raises(ValueError, match="same run_id"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=1,
            history=(transition,),
        )


def test_lifecycle_rejects_nonmonotonic_history_timestamps() -> None:
    first = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(2),
        revision=1,
    )
    second = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.INITIALIZED,
        current=RunLifecycleState.EXECUTING,
        occurred_at=_at(1),
        revision=2,
    )

    with pytest.raises(ValueError, match="timestamps must be monotonic"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.EXECUTING,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=2,
            history=(first, second),
        )


def test_lifecycle_state_and_updated_at_must_match_final_transition() -> None:
    transition = RunLifecycleTransition(
        run_id=_RUN_ID,
        previous=RunLifecycleState.ALLOCATED,
        current=RunLifecycleState.INITIALIZED,
        occurred_at=_at(1),
        revision=1,
    )

    with pytest.raises(ValueError, match="state must match"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.EXECUTING,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=1,
            history=(transition,),
        )

    with pytest.raises(ValueError, match="updated_at must match"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(2),
            revision=1,
            history=(transition,),
        )


def test_lifecycle_validates_history_container_and_entries() -> None:
    with pytest.raises(TypeError, match="history must be a tuple"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.ALLOCATED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_ALLOCATED_AT,
            history=[],  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="RunLifecycleTransition values"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.INITIALIZED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_at(1),
            revision=1,
            history=(object(),),  # type: ignore[arg-type]
        )


def test_lifecycle_rejects_updated_at_before_allocation() -> None:
    with pytest.raises(ValueError, match="must not precede allocated_at"):
        RunLifecycle(
            run_id=_RUN_ID,
            state=RunLifecycleState.ALLOCATED,
            allocated_at=_ALLOCATED_AT,
            updated_at=_ALLOCATED_AT - timedelta(seconds=1),
        )
