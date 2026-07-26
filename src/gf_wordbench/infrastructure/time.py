"""System clock adapter for GF Wordbench.

Wall-clock timestamps are timezone-aware UTC values. Elapsed time and deadline
measurement use a monotonic clock so civil-clock adjustments cannot affect
runtime behavior.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Final


class SystemClock:
    """Production clock implementation used through injected clock ports."""

    __slots__ = ()

    def utc_now(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""

        return datetime.now(timezone.utc)

    def monotonic_now(self) -> float:
        """Return a monotonic instant expressed in fractional seconds."""

        return time.monotonic()


SYSTEM_CLOCK: Final[SystemClock] = SystemClock()


__all__ = ["SYSTEM_CLOCK", "SystemClock"]
