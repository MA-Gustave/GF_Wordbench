"""Deterministic diagnostic-pattern catalog for GF Wordbench.

Pattern definitions remain in their owning modules and are registered explicitly
by the diagnostics registry. Importing this package performs no registration,
eager implementation imports, filesystem access, or process execution.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
