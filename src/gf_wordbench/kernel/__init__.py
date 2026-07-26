"""Stable shared contracts for GF Wordbench.

Import public symbols from their owning kernel modules. This package performs no
eager imports so importing it has no side effects and cannot create hidden
cross-module dependencies.
"""

__all__: tuple[str, ...] = ()
