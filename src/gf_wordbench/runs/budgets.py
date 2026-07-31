"""Monotonic run-budget allocation for GF Wordbench."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum, unique
from threading import RLock
from typing import Final

Clock = Callable[[], float]

_EPSILON_SEC: Final[float] = 1e-9


@unique
class BudgetPhase(StrEnum):
    """Runtime phase controlled by a run budget."""

    EXECUTION = "execution"
    FINALIZATION = "finalization"
    CLOSED = "closed"


@unique
class BudgetKind(StrEnum):
    """Kinds of bounded work issued by a run budget."""

    STAGE = "stage"
    FINALIZATION = "finalization"


@unique
class BudgetDenialReason(StrEnum):
    """Canonical reasons why bounded work cannot start."""

    FINALIZATION_STARTED = "finalization_started"
    FINALIZATION_NOT_STARTED = "finalization_not_started"
    RUN_CLOSED = "run_closed"
    CANCELLED = "cancelled"
    EXECUTION_EXHAUSTED = "execution_exhausted"
    FINALIZATION_EXHAUSTED = "finalization_exhausted"
    BELOW_MINIMUM = "below_minimum"
    ALREADY_ACTIVE = "already_active"


@dataclass(frozen=True, slots=True)
class BudgetAllocation:
    """One finite runtime-only budget allocation."""

    token: int
    kind: BudgetKind
    name: str
    requested_sec: float
    minimum_sec: float
    granted_sec: float
    allocated_at_monotonic: float
    deadline_monotonic: float
    run_deadline_monotonic: float

    def __post_init__(self) -> None:
        if isinstance(self.token, bool) or not isinstance(self.token, int):
            raise TypeError("token must be an integer")
        if self.token <= 0:
            raise ValueError("token must be positive")
        if not isinstance(self.kind, BudgetKind):
            raise TypeError("kind must be a BudgetKind")
        _require_name(self.name, field="name")
        _require_positive_duration(self.requested_sec, field="requested_sec")
        _require_positive_duration(self.minimum_sec, field="minimum_sec")
        _require_positive_duration(self.granted_sec, field="granted_sec")
        _require_finite_number(
            self.allocated_at_monotonic,
            field="allocated_at_monotonic",
        )
        _require_finite_number(
            self.deadline_monotonic,
            field="deadline_monotonic",
        )
        _require_finite_number(
            self.run_deadline_monotonic,
            field="run_deadline_monotonic",
        )
        if self.minimum_sec - self.granted_sec > _EPSILON_SEC:
            raise ValueError("granted_sec must satisfy minimum_sec")
        if self.granted_sec - self.requested_sec > _EPSILON_SEC:
            raise ValueError("granted_sec must not exceed requested_sec")
        if self.deadline_monotonic < self.allocated_at_monotonic:
            raise ValueError("deadline must not precede allocation")
        if self.deadline_monotonic - self.run_deadline_monotonic > _EPSILON_SEC:
            raise ValueError("allocation deadline must not exceed run deadline")

    @property
    def timeout_sec(self) -> float:
        """Return the initially granted timeout."""

        return self.granted_sec

    def remaining_sec(self, now_monotonic: float) -> float:
        """Return allocation time remaining at a monotonic instant."""

        now = _require_finite_number(now_monotonic, field="now_monotonic")
        return max(0.0, self.deadline_monotonic - now)

    def expired(self, now_monotonic: float) -> bool:
        """Return whether the allocation deadline has been reached."""

        return self.remaining_sec(now_monotonic) <= _EPSILON_SEC


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    """Immutable view of current run-budget state."""

    phase: BudgetPhase
    total_sec: float
    finalization_reserve_sec: float
    elapsed_sec: float
    remaining_total_sec: float
    remaining_execution_sec: float
    remaining_finalization_sec: float
    execution_deadline_monotonic: float
    run_deadline_monotonic: float
    cancellation_reason: str | None
    stop_reason: str | None
    active_stage_names: tuple[str, ...]
    active_finalization_names: tuple[str, ...]

    @property
    def execution_available(self) -> bool:
        """Return whether normal stage execution may still begin."""

        return (
            self.phase is BudgetPhase.EXECUTION
            and self.cancellation_reason is None
            and self.remaining_execution_sec > _EPSILON_SEC
        )

    @property
    def finalization_available(self) -> bool:
        """Return whether finalization work may still begin."""

        return (
            self.phase is BudgetPhase.FINALIZATION
            and self.remaining_finalization_sec > _EPSILON_SEC
        )


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    """Result of a non-raising budget-allocation attempt."""

    allocation: BudgetAllocation | None
    denial_reason: BudgetDenialReason | None
    available_sec: float
    snapshot: BudgetSnapshot

    def __post_init__(self) -> None:
        _require_non_negative_duration(self.available_sec, field="available_sec")
        if (self.allocation is None) == (self.denial_reason is None):
            raise ValueError(
                "exactly one of allocation and denial_reason must be present"
            )

    @property
    def granted(self) -> bool:
        """Return whether an allocation was granted."""

        return self.allocation is not None

    def require(self) -> BudgetAllocation:
        """Return the allocation or raise ``BudgetUnavailableError``."""

        if self.allocation is not None:
            return self.allocation
        assert self.denial_reason is not None
        raise BudgetUnavailableError(
            reason=self.denial_reason,
            available_sec=self.available_sec,
            snapshot=self.snapshot,
        )


class BudgetUnavailableError(RuntimeError):
    """Raised when a required stage or finalization budget is unavailable."""

    def __init__(
        self,
        *,
        reason: BudgetDenialReason,
        available_sec: float,
        snapshot: BudgetSnapshot,
    ) -> None:
        if not isinstance(reason, BudgetDenialReason):
            raise TypeError("reason must be a BudgetDenialReason")
        _require_non_negative_duration(available_sec, field="available_sec")
        if not isinstance(snapshot, BudgetSnapshot):
            raise TypeError("snapshot must be a BudgetSnapshot")
        self.reason = reason
        self.available_sec = available_sec
        self.snapshot = snapshot
        super().__init__(
            f"budget unavailable: {reason.value}; "
            f"available={available_sec:.6f}s"
        )


class RunBudget:
    """Thread-safe monotonic controller for one run lifecycle.

    Normal stages may consume only the execution interval ending before the
    protected finalization reserve. Once finalization begins, no new stage is
    admitted and finalization tasks receive bounded allocations ending no later
    than the global run deadline.
    """

    __slots__ = (
        "_active",
        "_cancellation_reason",
        "_clock",
        "_execution_deadline",
        "_finalization_reserve_sec",
        "_last_observed",
        "_lock",
        "_next_token",
        "_phase",
        "_run_deadline",
        "_started_at",
        "_stop_reason",
        "_total_sec",
    )

    def __init__(
        self,
        *,
        total_sec: float,
        finalization_reserve_sec: float,
        clock: Clock = time.monotonic,
    ) -> None:
        total = _require_positive_duration(total_sec, field="total_sec")
        reserve = _require_positive_duration(
            finalization_reserve_sec,
            field="finalization_reserve_sec",
        )
        if reserve >= total:
            raise ValueError(
                "finalization_reserve_sec must be smaller than total_sec"
            )
        if not callable(clock):
            raise TypeError("clock must be callable")

        started_at = _read_clock(clock)
        self._clock = clock
        self._total_sec = total
        self._finalization_reserve_sec = reserve
        self._started_at = started_at
        self._execution_deadline = started_at + total - reserve
        self._run_deadline = started_at + total
        self._last_observed = started_at
        self._phase = BudgetPhase.EXECUTION
        self._cancellation_reason: str | None = None
        self._stop_reason: str | None = None
        self._next_token = 1
        self._active: dict[int, BudgetAllocation] = {}
        self._lock = RLock()

    @property
    def total_sec(self) -> float:
        """Return the configured global run duration."""

        return self._total_sec

    @property
    def finalization_reserve_sec(self) -> float:
        """Return the protected finalization reserve."""

        return self._finalization_reserve_sec

    @property
    def started_at_monotonic(self) -> float:
        """Return the monotonic run start instant."""

        return self._started_at

    @property
    def execution_deadline_monotonic(self) -> float:
        """Return the deadline after which no normal stage may run."""

        return self._execution_deadline

    @property
    def run_deadline_monotonic(self) -> float:
        """Return the absolute global run deadline."""

        return self._run_deadline

    @property
    def phase(self) -> BudgetPhase:
        """Return the current budget phase."""

        with self._lock:
            self._refresh_locked(self._now_locked())
            return self._phase

    @property
    def cancellation_reason(self) -> str | None:
        """Return the accepted cancellation reason, when present."""

        with self._lock:
            return self._cancellation_reason

    @property
    def stop_reason(self) -> str | None:
        """Return the reason normal execution stopped, when known."""

        with self._lock:
            return self._stop_reason

    def snapshot(self) -> BudgetSnapshot:
        """Return an immutable budget snapshot."""

        with self._lock:
            now = self._now_locked()
            self._refresh_locked(now)
            return self._snapshot_locked(now)

    def remaining_total_sec(self) -> float:
        """Return time remaining before the global deadline."""

        return self.snapshot().remaining_total_sec

    def remaining_execution_sec(self) -> float:
        """Return time available to normal stages."""

        return self.snapshot().remaining_execution_sec

    def remaining_finalization_sec(self) -> float:
        """Return time available to finalization work."""

        return self.snapshot().remaining_finalization_sec

    def try_allocate_stage(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> BudgetDecision:
        """Attempt to allocate a bounded normal-stage budget."""

        return self._try_allocate(
            kind=BudgetKind.STAGE,
            name=name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        )

    def allocate_stage(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> BudgetAllocation:
        """Allocate a normal-stage budget or raise when unavailable."""

        return self.try_allocate_stage(
            name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        ).require()

    def try_allocate_finalization(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> BudgetDecision:
        """Attempt to allocate a bounded finalization sub-budget."""

        return self._try_allocate(
            kind=BudgetKind.FINALIZATION,
            name=name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        )

    def allocate_finalization(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> BudgetAllocation:
        """Allocate a finalization sub-budget or raise when unavailable."""

        return self.try_allocate_finalization(
            name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        ).require()

    def remaining_for(self, allocation: BudgetAllocation) -> float:
        """Return usable time remaining for an active allocation."""

        with self._lock:
            current = self._require_active_locked(allocation)
            now = self._now_locked()
            self._refresh_locked(now)
            deadline = min(current.deadline_monotonic, self._run_deadline)
            if current.kind is BudgetKind.STAGE:
                deadline = min(deadline, self._execution_deadline)
            return max(0.0, deadline - now)

    def bounded_timeout(
        self,
        allocation: BudgetAllocation,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> float:
        """Return a launch-safe timeout bounded by an active allocation."""

        requested = _require_positive_duration(
            requested_sec,
            field="requested_sec",
        )
        minimum = _require_positive_duration(
            minimum_sec,
            field="minimum_sec",
        )
        available = self.remaining_for(allocation)
        granted = min(requested, available)
        if granted + _EPSILON_SEC < minimum:
            snapshot = self.snapshot()
            reason = (
                BudgetDenialReason.EXECUTION_EXHAUSTED
                if allocation.kind is BudgetKind.STAGE
                and available <= _EPSILON_SEC
                else BudgetDenialReason.FINALIZATION_EXHAUSTED
                if allocation.kind is BudgetKind.FINALIZATION
                and available <= _EPSILON_SEC
                else BudgetDenialReason.BELOW_MINIMUM
            )
            raise BudgetUnavailableError(
                reason=reason,
                available_sec=available,
                snapshot=snapshot,
            )
        return granted

    def release(self, allocation: BudgetAllocation) -> None:
        """Release one active allocation idempotently."""

        if not isinstance(allocation, BudgetAllocation):
            raise TypeError("allocation must be a BudgetAllocation")
        with self._lock:
            current = self._active.get(allocation.token)
            if current is None:
                return
            if current is not allocation:
                raise ValueError("allocation token belongs to another allocation")
            del self._active[allocation.token]

    @contextmanager
    def stage(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> Iterator[BudgetAllocation]:
        """Acquire and automatically release a normal-stage allocation."""

        allocation = self.allocate_stage(
            name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        )
        try:
            yield allocation
        finally:
            self.release(allocation)

    @contextmanager
    def finalization_task(
        self,
        name: str,
        *,
        requested_sec: float,
        minimum_sec: float,
    ) -> Iterator[BudgetAllocation]:
        """Acquire and automatically release a finalization allocation."""

        allocation = self.allocate_finalization(
            name,
            requested_sec=requested_sec,
            minimum_sec=minimum_sec,
        )
        try:
            yield allocation
        finally:
            self.release(allocation)

    def begin_finalization(self, *, reason: str) -> BudgetSnapshot:
        """Enter finalization idempotently and prevent new normal stages."""

        stop_reason = _require_name(reason, field="reason")
        with self._lock:
            now = self._now_locked()
            self._refresh_locked(now)
            if self._phase is BudgetPhase.CLOSED:
                return self._snapshot_locked(now)
            if self._phase is BudgetPhase.EXECUTION:
                self._phase = BudgetPhase.FINALIZATION
                self._stop_reason = stop_reason
            elif self._stop_reason is None:
                self._stop_reason = stop_reason
            return self._snapshot_locked(now)

    def cancel(self, *, reason: str) -> BudgetSnapshot:
        """Accept cancellation and enter protected finalization."""

        cancellation_reason = _require_name(reason, field="reason")
        with self._lock:
            now = self._now_locked()
            self._refresh_locked(now)
            if self._phase is BudgetPhase.CLOSED:
                return self._snapshot_locked(now)
            if self._cancellation_reason is None:
                self._cancellation_reason = cancellation_reason
            if self._phase is BudgetPhase.EXECUTION:
                self._phase = BudgetPhase.FINALIZATION
            if self._stop_reason is None:
                self._stop_reason = "cancelled"
            return self._snapshot_locked(now)

    def close(self, *, reason: str = "completed") -> BudgetSnapshot:
        """Close the budget and reject all future allocations."""

        close_reason = _require_name(reason, field="reason")
        with self._lock:
            now = self._now_locked()
            self._refresh_locked(now)
            self._phase = BudgetPhase.CLOSED
            if self._stop_reason is None:
                self._stop_reason = close_reason
            self._active.clear()
            return self._snapshot_locked(now)

    def active_allocations(self) -> tuple[BudgetAllocation, ...]:
        """Return active allocations in deterministic token order."""

        with self._lock:
            return tuple(self._active[token] for token in sorted(self._active))

    def _try_allocate(
        self,
        *,
        kind: BudgetKind,
        name: str,
        requested_sec: float,
        minimum_sec: float,
    ) -> BudgetDecision:
        allocation_name = _require_name(name, field="name")
        requested = _require_positive_duration(
            requested_sec,
            field="requested_sec",
        )
        minimum = _require_positive_duration(
            minimum_sec,
            field="minimum_sec",
        )
        if minimum - requested > _EPSILON_SEC:
            raise ValueError("minimum_sec must not exceed requested_sec")

        with self._lock:
            now = self._now_locked()
            self._refresh_locked(now)
            denial = self._phase_denial_locked(kind)
            available = self._available_locked(kind, now)

            if denial is None and self._name_is_active_locked(kind, allocation_name):
                denial = BudgetDenialReason.ALREADY_ACTIVE
            if denial is None and available <= _EPSILON_SEC:
                denial = (
                    BudgetDenialReason.EXECUTION_EXHAUSTED
                    if kind is BudgetKind.STAGE
                    else BudgetDenialReason.FINALIZATION_EXHAUSTED
                )

            granted = min(requested, available)
            if denial is None and granted + _EPSILON_SEC < minimum:
                denial = BudgetDenialReason.BELOW_MINIMUM

            if denial is not None:
                snapshot = self._snapshot_locked(now)
                return BudgetDecision(
                    allocation=None,
                    denial_reason=denial,
                    available_sec=available,
                    snapshot=snapshot,
                )

            deadline_cap = (
                self._execution_deadline
                if kind is BudgetKind.STAGE
                else self._run_deadline
            )
            token = self._next_token
            self._next_token += 1
            allocation = BudgetAllocation(
                token=token,
                kind=kind,
                name=allocation_name,
                requested_sec=requested,
                minimum_sec=minimum,
                granted_sec=granted,
                allocated_at_monotonic=now,
                deadline_monotonic=min(now + granted, deadline_cap),
                run_deadline_monotonic=self._run_deadline,
            )
            self._active[token] = allocation
            snapshot = self._snapshot_locked(now)
            return BudgetDecision(
                allocation=allocation,
                denial_reason=None,
                available_sec=available,
                snapshot=snapshot,
            )

    def _phase_denial_locked(
        self,
        kind: BudgetKind,
    ) -> BudgetDenialReason | None:
        if self._phase is BudgetPhase.CLOSED:
            if self._stop_reason == "global_budget_exhausted":
                return (
                    BudgetDenialReason.EXECUTION_EXHAUSTED
                    if kind is BudgetKind.STAGE
                    else BudgetDenialReason.FINALIZATION_EXHAUSTED
                )
            return BudgetDenialReason.RUN_CLOSED
        if self._cancellation_reason is not None and kind is BudgetKind.STAGE:
            return BudgetDenialReason.CANCELLED
        if kind is BudgetKind.STAGE:
            if self._phase is BudgetPhase.FINALIZATION:
                if self._stop_reason == "execution_budget_exhausted":
                    return BudgetDenialReason.EXECUTION_EXHAUSTED
                return BudgetDenialReason.FINALIZATION_STARTED
            return None
        if self._phase is BudgetPhase.EXECUTION:
            return BudgetDenialReason.FINALIZATION_NOT_STARTED
        return None

    def _available_locked(
        self,
        kind: BudgetKind,
        now: float,
    ) -> float:
        if kind is BudgetKind.STAGE:
            if self._phase is not BudgetPhase.EXECUTION:
                return 0.0
            return max(0.0, self._execution_deadline - now)
        if self._phase is not BudgetPhase.FINALIZATION:
            return 0.0
        return max(0.0, self._run_deadline - now)

    def _name_is_active_locked(
        self,
        kind: BudgetKind,
        name: str,
    ) -> bool:
        return any(
            allocation.kind is kind and allocation.name == name
            for allocation in self._active.values()
        )

    def _require_active_locked(
        self,
        allocation: BudgetAllocation,
    ) -> BudgetAllocation:
        if not isinstance(allocation, BudgetAllocation):
            raise TypeError("allocation must be a BudgetAllocation")
        current = self._active.get(allocation.token)
        if current is None:
            raise ValueError("allocation is not active")
        if current is not allocation:
            raise ValueError("allocation token belongs to another allocation")
        return current

    def _now_locked(self) -> float:
        now = _read_clock(self._clock)
        if now + _EPSILON_SEC < self._last_observed:
            raise RuntimeError("monotonic clock moved backwards")
        self._last_observed = max(self._last_observed, now)
        return self._last_observed

    def _refresh_locked(self, now: float) -> None:
        if self._phase is BudgetPhase.CLOSED:
            return
        if now + _EPSILON_SEC >= self._run_deadline:
            self._phase = BudgetPhase.CLOSED
            self._stop_reason = "global_budget_exhausted"
            return
        if (
            self._phase is BudgetPhase.EXECUTION
            and now + _EPSILON_SEC >= self._execution_deadline
        ):
            self._phase = BudgetPhase.FINALIZATION
            if self._stop_reason is None:
                self._stop_reason = "execution_budget_exhausted"

    def _snapshot_locked(self, now: float) -> BudgetSnapshot:
        elapsed = min(self._total_sec, max(0.0, now - self._started_at))
        remaining_total = max(0.0, self._run_deadline - now)
        remaining_execution = (
            max(0.0, self._execution_deadline - now)
            if self._phase is BudgetPhase.EXECUTION
            else 0.0
        )
        remaining_finalization = (
            remaining_total
            if self._phase is BudgetPhase.FINALIZATION
            else 0.0
        )
        active_stages = tuple(
            sorted(
                allocation.name
                for allocation in self._active.values()
                if allocation.kind is BudgetKind.STAGE
            )
        )
        active_finalization = tuple(
            sorted(
                allocation.name
                for allocation in self._active.values()
                if allocation.kind is BudgetKind.FINALIZATION
            )
        )
        return BudgetSnapshot(
            phase=self._phase,
            total_sec=self._total_sec,
            finalization_reserve_sec=self._finalization_reserve_sec,
            elapsed_sec=elapsed,
            remaining_total_sec=remaining_total,
            remaining_execution_sec=remaining_execution,
            remaining_finalization_sec=remaining_finalization,
            execution_deadline_monotonic=self._execution_deadline,
            run_deadline_monotonic=self._run_deadline,
            cancellation_reason=self._cancellation_reason,
            stop_reason=self._stop_reason,
            active_stage_names=active_stages,
            active_finalization_names=active_finalization,
        )


def create_run_budget(
    *,
    total_sec: float,
    finalization_reserve_sec: float,
    clock: Clock = time.monotonic,
) -> RunBudget:
    """Create one validated run budget."""

    return RunBudget(
        total_sec=total_sec,
        finalization_reserve_sec=finalization_reserve_sec,
        clock=clock,
    )


def _read_clock(clock: Clock) -> float:
    value = clock()
    return _require_finite_number(value, field="clock value")


def _require_name(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or value.isspace():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _require_finite_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _require_positive_duration(value: object, *, field: str) -> float:
    result = _require_finite_number(value, field=field)
    if result <= 0.0:
        raise ValueError(f"{field} must be positive")
    return result


def _require_non_negative_duration(value: object, *, field: str) -> float:
    result = _require_finite_number(value, field=field)
    if result < 0.0:
        raise ValueError(f"{field} must be non-negative")
    return result


__all__ = (
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
