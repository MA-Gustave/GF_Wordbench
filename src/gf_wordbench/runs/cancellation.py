"""Thread-safe cooperative cancellation for GF Wordbench runs."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from threading import Condition, RLock
from typing import Final, TypeAlias

from gf_wordbench.kernel.errors import CancellationRequested

Clock: TypeAlias = Callable[[], float]
UtcClock: TypeAlias = Callable[[], datetime]
CancellationCheck: TypeAlias = Callable[[], None]

_DEFAULT_MESSAGE: Final[str] = "Cancellation requested."
_MAX_REASON_LENGTH: Final[int] = 512
_MAX_DETAIL_LENGTH: Final[int] = 4_096


@unique
class CancellationReason(StrEnum):
    """Canonical controller reasons defined by the execution contract."""

    USER = "user"
    APPLICATION_SHUTDOWN = "application_shutdown"
    OUTPUT_LIMIT = "output_limit"
    CONTROLLER_POLICY = "controller_policy"


@dataclass(frozen=True, slots=True)
class CancellationSnapshot:
    """Immutable observation of one run's cancellation state."""

    requested: bool
    reason: str | None
    requested_at: datetime | None
    requested_at_monotonic: float | None

    def __post_init__(self) -> None:
        if type(self.requested) is not bool:
            raise TypeError("requested must be a bool")

        reason = self.reason
        requested_at = self.requested_at
        requested_at_monotonic = self.requested_at_monotonic

        if self.requested:
            if reason is None:
                raise ValueError("requested cancellation requires a reason")
            _normalize_reason(reason)
            if requested_at is None:
                raise ValueError(
                    "requested cancellation requires requested_at"
                )
            if requested_at_monotonic is None:
                raise ValueError(
                    "requested cancellation requires requested_at_monotonic"
                )
        elif any(
            value is not None
            for value in (reason, requested_at, requested_at_monotonic)
        ):
            raise ValueError(
                "unrequested cancellation cannot contain request metadata"
            )

        if requested_at is not None:
            object.__setattr__(
                self,
                "requested_at",
                _normalize_utc_datetime(requested_at),
            )

        if requested_at_monotonic is not None:
            _validate_monotonic_value(requested_at_monotonic)


class CancellationController:
    """Accept and expose the first cancellation request for one active run.

    The controller satisfies both the application-level ``CancellationSource``
    shape and the process-layer ``CancellationToken`` shape without redefining
    either owner contract.
    """

    __slots__ = (
        "_condition",
        "_monotonic_clock",
        "_reason",
        "_requested_at",
        "_requested_at_monotonic",
        "_utc_clock",
    )

    def __init__(
        self,
        *,
        monotonic_clock: Clock = time.monotonic,
        utc_clock: UtcClock = lambda: datetime.now(UTC),
    ) -> None:
        if not callable(monotonic_clock):
            raise TypeError("monotonic_clock must be callable")
        if not callable(utc_clock):
            raise TypeError("utc_clock must be callable")

        self._condition = Condition(RLock())
        self._monotonic_clock = monotonic_clock
        self._utc_clock = utc_clock
        self._reason: str | None = None
        self._requested_at: datetime | None = None
        self._requested_at_monotonic: float | None = None

    def request(
        self,
        reason: CancellationReason | str = CancellationReason.USER,
    ) -> bool:
        """Accept cancellation once and return whether this call won."""

        normalized_reason = _normalize_reason(reason)

        with self._condition:
            if self._reason is not None:
                return False

            requested_at_monotonic = _read_monotonic_clock(
                self._monotonic_clock
            )
            requested_at = _read_utc_clock(self._utc_clock)

            self._reason = normalized_reason
            self._requested_at = requested_at
            self._requested_at_monotonic = requested_at_monotonic
            self._condition.notify_all()
            return True

    def cancel(
        self,
        reason: CancellationReason | str = CancellationReason.USER,
    ) -> bool:
        """Alias for ``request`` used by GUI and controller code."""

        return self.request(reason)

    def is_cancellation_requested(self) -> bool:
        """Return whether cancellation has been accepted."""

        with self._condition:
            return self._reason is not None

    def is_cancelled(self) -> bool:
        """Return the process-token view of cancellation state."""

        return self.is_cancellation_requested()

    def cancellation_reason(self) -> str | None:
        """Return the accepted reason for application orchestration."""

        with self._condition:
            return self._reason

    def reason(self) -> str | None:
        """Return the accepted reason for process execution."""

        return self.cancellation_reason()

    @property
    def requested_at(self) -> datetime | None:
        """Return the accepted UTC request timestamp."""

        with self._condition:
            return self._requested_at

    @property
    def requested_at_monotonic(self) -> float | None:
        """Return the monotonic instant used for terminal-race ordering."""

        with self._condition:
            return self._requested_at_monotonic

    def snapshot(self) -> CancellationSnapshot:
        """Return an atomic immutable cancellation observation."""

        with self._condition:
            requested = self._reason is not None
            return CancellationSnapshot(
                requested=requested,
                reason=self._reason,
                requested_at=self._requested_at,
                requested_at_monotonic=self._requested_at_monotonic,
            )

    def wait(self, timeout_sec: float | None = None) -> bool:
        """Wait until cancellation or timeout and report cancellation."""

        timeout = _normalize_timeout(timeout_sec)
        with self._condition:
            if self._reason is not None:
                return True
            if timeout == 0.0:
                return False
            return self._condition.wait_for(
                lambda: self._reason is not None,
                timeout=timeout,
            )

    def raise_if_cancelled(
        self,
        *,
        message: str = _DEFAULT_MESSAGE,
        stage: str | None = None,
        operation: str | None = None,
        subject: str | None = None,
        evidence_paths: Iterable[str] = (),
    ) -> None:
        """Raise the canonical controlled exception when cancelled."""

        snapshot = self.snapshot()
        if not snapshot.requested:
            return

        raise CancellationRequested(
            _normalize_message(message),
            detail=_cancellation_detail(snapshot.reason),
            stage=_normalize_optional_context(stage, field="stage"),
            operation=_normalize_optional_context(
                operation,
                field="operation",
            ),
            subject=_normalize_optional_context(subject, field="subject"),
            retryable=False,
            evidence_paths=evidence_paths,
        )

    def check(self) -> None:
        """Zero-argument cancellation check for run orchestration."""

        self.raise_if_cancelled()

    def as_check(self) -> CancellationCheck:
        """Return the stable zero-argument orchestration callback."""

        return self.check


def create_cancellation_controller(
    *,
    monotonic_clock: Clock = time.monotonic,
    utc_clock: UtcClock = lambda: datetime.now(UTC),
) -> CancellationController:
    """Construct a fresh controller for one run."""

    return CancellationController(
        monotonic_clock=monotonic_clock,
        utc_clock=utc_clock,
    )


def cancellation_requested(source: object | None) -> bool:
    """Read either canonical cancellation interface structurally."""

    if source is None:
        return False

    method = getattr(source, "is_cancellation_requested", None)
    if not callable(method):
        method = getattr(source, "is_cancelled", None)
    if not callable(method):
        raise TypeError(
            "cancellation source must expose "
            "is_cancellation_requested() or is_cancelled()"
        )

    value = method()
    if type(value) is not bool:
        raise TypeError("cancellation state method must return bool")
    return value


def cancellation_reason(source: object | None) -> str | None:
    """Read an accepted reason from either canonical interface."""

    if source is None:
        return None

    member = getattr(source, "cancellation_reason", None)
    if member is None:
        member = getattr(source, "reason", None)

    value = member() if callable(member) else member
    if value is None:
        return None
    return _normalize_reason(value)


def raise_if_cancellation_requested(
    source: object | None,
    *,
    message: str = _DEFAULT_MESSAGE,
    stage: str | None = None,
    operation: str | None = None,
    subject: str | None = None,
    evidence_paths: Iterable[str] = (),
) -> None:
    """Raise ``CancellationRequested`` for any compatible source."""

    if not cancellation_requested(source):
        return

    raise CancellationRequested(
        _normalize_message(message),
        detail=_cancellation_detail(cancellation_reason(source)),
        stage=_normalize_optional_context(stage, field="stage"),
        operation=_normalize_optional_context(
            operation,
            field="operation",
        ),
        subject=_normalize_optional_context(subject, field="subject"),
        retryable=False,
        evidence_paths=evidence_paths,
    )


def _normalize_reason(value: CancellationReason | str) -> str:
    raw = value.value if isinstance(value, CancellationReason) else value
    if not isinstance(raw, str):
        raise TypeError("cancellation reason must be a string")
    if not raw.strip():
        raise ValueError("cancellation reason must not be empty")
    if "\x00" in raw:
        raise ValueError("cancellation reason must not contain NUL")
    if len(raw) > _MAX_REASON_LENGTH:
        raise ValueError(
            f"cancellation reason exceeds {_MAX_REASON_LENGTH} characters"
        )
    return raw


def _normalize_message(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("message must be a string")
    if not value.strip():
        raise ValueError("message must not be empty")
    if "\x00" in value:
        raise ValueError("message must not contain NUL")
    return value


def _normalize_optional_context(
    value: str | None,
    *,
    field: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or None")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _cancellation_detail(reason: str | None) -> str:
    if reason is None:
        return "Cancellation was accepted without a supplied reason."
    detail = f"Cancellation reason: {reason}."
    if len(detail) <= _MAX_DETAIL_LENGTH:
        return detail
    return f"{detail[: _MAX_DETAIL_LENGTH - 3]}..."


def _normalize_timeout(value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("timeout_sec must be a number or None")
    timeout = float(value)
    if not math.isfinite(timeout):
        raise ValueError("timeout_sec must be finite")
    if timeout < 0:
        raise ValueError("timeout_sec must be non-negative")
    return timeout


def _read_monotonic_clock(clock: Clock) -> float:
    value = clock()
    return _validate_monotonic_value(value)


def _validate_monotonic_value(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("monotonic clock must return a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("monotonic clock must return a finite value")
    return result


def _read_utc_clock(clock: UtcClock) -> datetime:
    return _normalize_utc_datetime(clock())


def _normalize_utc_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("UTC clock must return a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


__all__ = (
    "CancellationCheck",
    "CancellationController",
    "CancellationReason",
    "CancellationSnapshot",
    "Clock",
    "UtcClock",
    "cancellation_reason",
    "cancellation_requested",
    "create_cancellation_controller",
    "raise_if_cancellation_requested",
)
