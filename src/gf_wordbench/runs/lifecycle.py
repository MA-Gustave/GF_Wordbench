"""Run-directory lifecycle policy for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.ids import RunId, validate_run_id

__all__ = (
    "ALLOWED_LIFECYCLE_TRANSITIONS",
    "RunLifecycle",
    "RunLifecycleState",
    "RunLifecycleTransition",
    "allowed_lifecycle_targets",
    "can_transition_lifecycle",
    "new_run_lifecycle",
    "require_lifecycle_transition",
    "transition_lifecycle",
)


@unique
class RunLifecycleState(StrEnum):
    ALLOCATED = "allocated"
    INITIALIZED = "initialized"
    EXECUTING = "executing"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"
    INCOMPLETE = "incomplete"
    CORRUPT = "corrupt"
    ARCHIVED = "archived"
    DELETED = "deleted"

    @property
    def is_complete(self) -> bool:
        return self is RunLifecycleState.FINALIZED

    @property
    def is_terminal(self) -> bool:
        return self in _TERMINAL_STATES

    @property
    def is_mutable(self) -> bool:
        return self in _MUTABLE_STATES

    @property
    def allows_stage_execution(self) -> bool:
        return self in {
            RunLifecycleState.INITIALIZED,
            RunLifecycleState.EXECUTING,
        }

    @property
    def allows_finalization_writes(self) -> bool:
        return self is RunLifecycleState.FINALIZING

    @property
    def is_previous_run_eligible(self) -> bool:
        return self is RunLifecycleState.FINALIZED


_TERMINAL_STATES: Final[frozenset[RunLifecycleState]] = frozenset(
    {
        RunLifecycleState.FINALIZED,
        RunLifecycleState.INCOMPLETE,
        RunLifecycleState.CORRUPT,
        RunLifecycleState.ARCHIVED,
        RunLifecycleState.DELETED,
    }
)

_MUTABLE_STATES: Final[frozenset[RunLifecycleState]] = frozenset(
    {
        RunLifecycleState.INITIALIZED,
        RunLifecycleState.EXECUTING,
        RunLifecycleState.FINALIZING,
    }
)

_ALLOWED_TRANSITIONS: Final[
    dict[RunLifecycleState, frozenset[RunLifecycleState]]
] = {
    RunLifecycleState.ALLOCATED: frozenset(
        {RunLifecycleState.INITIALIZED}
    ),
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

ALLOWED_LIFECYCLE_TRANSITIONS: Final = MappingProxyType(
    _ALLOWED_TRANSITIONS
)


@dataclass(frozen=True, slots=True)
class RunLifecycleTransition:
    run_id: RunId
    previous: RunLifecycleState
    current: RunLifecycleState
    occurred_at: datetime
    revision: int
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "run_id",
            validate_run_id(self.run_id),
        )
        _require_state("previous", self.previous)
        _require_state("current", self.current)
        object.__setattr__(
            self,
            "occurred_at",
            _normalize_utc_timestamp(
                self.occurred_at,
                field="occurred_at",
            ),
        )
        _require_plain_int(
            "revision",
            self.revision,
            minimum=1,
        )
        object.__setattr__(
            self,
            "reason",
            _normalize_reason(self.reason),
        )
        require_lifecycle_transition(
            self.previous,
            self.current,
        )


@dataclass(frozen=True, slots=True)
class RunLifecycle:
    run_id: RunId
    state: RunLifecycleState
    allocated_at: datetime
    updated_at: datetime
    revision: int = 0
    history: tuple[RunLifecycleTransition, ...] = ()

    def __post_init__(self) -> None:
        run_id = validate_run_id(self.run_id)
        object.__setattr__(self, "run_id", run_id)
        _require_state("state", self.state)

        allocated_at = _normalize_utc_timestamp(
            self.allocated_at,
            field="allocated_at",
        )
        updated_at = _normalize_utc_timestamp(
            self.updated_at,
            field="updated_at",
        )
        if updated_at < allocated_at:
            raise ValueError(
                "updated_at must not precede allocated_at"
            )

        object.__setattr__(self, "allocated_at", allocated_at)
        object.__setattr__(self, "updated_at", updated_at)

        _require_plain_int(
            "revision",
            self.revision,
            minimum=0,
        )

        if not isinstance(self.history, tuple):
            raise TypeError("history must be a tuple")
        if any(
            not isinstance(item, RunLifecycleTransition)
            for item in self.history
        ):
            raise TypeError(
                "history must contain RunLifecycleTransition values"
            )

        self._validate_history()

    @property
    def is_complete(self) -> bool:
        return self.state.is_complete

    @property
    def is_terminal(self) -> bool:
        return self.state.is_terminal

    @property
    def is_mutable(self) -> bool:
        return self.state.is_mutable

    @property
    def is_previous_run_eligible(self) -> bool:
        return self.state.is_previous_run_eligible

    def can_transition(
        self,
        target: RunLifecycleState,
    ) -> bool:
        return can_transition_lifecycle(
            self.state,
            target,
        )

    def transition(
        self,
        target: RunLifecycleState,
        *,
        occurred_at: datetime,
        reason: str | None = None,
    ) -> RunLifecycle:
        return transition_lifecycle(
            self,
            target,
            occurred_at=occurred_at,
            reason=reason,
        )

    def _validate_history(self) -> None:
        if self.revision != len(self.history):
            raise ValueError(
                "revision must equal the number of history entries"
            )

        if not self.history:
            if self.revision != 0:
                raise ValueError(
                    "a lifecycle without history must have revision zero"
                )
            if self.state is not RunLifecycleState.ALLOCATED:
                raise ValueError(
                    "a lifecycle without history must be allocated"
                )
            if self.updated_at != self.allocated_at:
                raise ValueError(
                    "a newly allocated lifecycle must have matching timestamps"
                )
            return

        expected_previous = RunLifecycleState.ALLOCATED
        previous_time = self.allocated_at

        for expected_revision, transition in enumerate(
            self.history,
            start=1,
        ):
            if transition.run_id != self.run_id:
                raise ValueError(
                    "every lifecycle transition must use the same run_id"
                )
            if transition.revision != expected_revision:
                raise ValueError(
                    "lifecycle transition revisions must be contiguous"
                )
            if transition.previous is not expected_previous:
                raise ValueError(
                    "lifecycle transition history is not contiguous"
                )
            if transition.occurred_at < previous_time:
                raise ValueError(
                    "lifecycle transition timestamps must be monotonic"
                )

            expected_previous = transition.current
            previous_time = transition.occurred_at

        if self.state is not expected_previous:
            raise ValueError(
                "state must match the final lifecycle transition"
            )
        if self.updated_at != previous_time:
            raise ValueError(
                "updated_at must match the final transition timestamp"
            )


def new_run_lifecycle(
    run_id: RunId | str,
    *,
    allocated_at: datetime,
) -> RunLifecycle:
    timestamp = _normalize_utc_timestamp(
        allocated_at,
        field="allocated_at",
    )
    return RunLifecycle(
        run_id=validate_run_id(run_id),
        state=RunLifecycleState.ALLOCATED,
        allocated_at=timestamp,
        updated_at=timestamp,
    )


def allowed_lifecycle_targets(
    state: RunLifecycleState,
) -> frozenset[RunLifecycleState]:
    _require_state("state", state)
    return ALLOWED_LIFECYCLE_TRANSITIONS[state]


def can_transition_lifecycle(
    current: RunLifecycleState,
    target: RunLifecycleState,
) -> bool:
    _require_state("current", current)
    _require_state("target", target)
    return (
        target is current
        or target in ALLOWED_LIFECYCLE_TRANSITIONS[current]
    )


def require_lifecycle_transition(
    current: RunLifecycleState,
    target: RunLifecycleState,
) -> None:
    _require_state("current", current)
    _require_state("target", target)

    if target is current:
        return

    if target not in ALLOWED_LIFECYCLE_TRANSITIONS[current]:
        raise ValueError(
            "prohibited run lifecycle transition: "
            f"{current.value} -> {target.value}"
        )


def transition_lifecycle(
    lifecycle: RunLifecycle,
    target: RunLifecycleState,
    *,
    occurred_at: datetime,
    reason: str | None = None,
) -> RunLifecycle:
    if not isinstance(lifecycle, RunLifecycle):
        raise TypeError("lifecycle must be a RunLifecycle")
    _require_state("target", target)

    timestamp = _normalize_utc_timestamp(
        occurred_at,
        field="occurred_at",
    )
    if timestamp < lifecycle.updated_at:
        raise ValueError(
            "occurred_at must not precede the current lifecycle timestamp"
        )

    if target is lifecycle.state:
        return lifecycle

    require_lifecycle_transition(
        lifecycle.state,
        target,
    )

    normalized_reason = _normalize_reason(reason)
    if target in {
        RunLifecycleState.INCOMPLETE,
        RunLifecycleState.CORRUPT,
    } and normalized_reason is None:
        raise ValueError(
            f"{target.value} transitions require a reason"
        )

    transition = RunLifecycleTransition(
        run_id=lifecycle.run_id,
        previous=lifecycle.state,
        current=target,
        occurred_at=timestamp,
        revision=lifecycle.revision + 1,
        reason=normalized_reason,
    )

    return RunLifecycle(
        run_id=lifecycle.run_id,
        state=target,
        allocated_at=lifecycle.allocated_at,
        updated_at=timestamp,
        revision=transition.revision,
        history=(*lifecycle.history, transition),
    )


def _require_state(
    field: str,
    value: object,
) -> RunLifecycleState:
    if not isinstance(value, RunLifecycleState):
        raise TypeError(
            f"{field} must be a RunLifecycleState"
        )
    return value


def _normalize_utc_timestamp(
    value: datetime,
    *,
    field: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(UTC)


def _normalize_reason(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("reason must be a string or None")
    if "\x00" in value:
        raise ValueError("reason must not contain NUL")
    normalized = value.strip()
    if not normalized:
        raise ValueError("reason must not be empty")
    if len(normalized) > 2048:
        raise ValueError(
            "reason must not exceed 2048 characters"
        )
    return normalized


def _require_plain_int(
    field: str,
    value: object,
    *,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an int")
    if value < minimum:
        raise ValueError(
            f"{field} must be at least {minimum}"
        )
    return value
