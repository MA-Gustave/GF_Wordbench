"""Run planning, orchestration, lifecycle, and finalization package.

Stable cross-module consumers use :mod:`gf_wordbench.runs.public`. This package
initializer intentionally performs no eager imports so importing
``gf_wordbench.runs`` remains side-effect free and cannot create dependency
cycles.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
