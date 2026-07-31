"""Stable application facade for GF Wordbench run execution."""

from __future__ import annotations

from .models.config import RunConfig
from .models.paths import RunPaths
from .models.results import RunResult
from .orchestrator import run_validation as execute_run

__all__ = (
    "RunConfig",
    "RunPaths",
    "RunResult",
    "execute_run",
)
