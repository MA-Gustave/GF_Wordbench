"""Stable cross-module API for GF Wordbench validation."""

from __future__ import annotations

from .pipeline import (
    preflight_external_tools,
    run_file_pipeline,
    run_pgf_stage_if_required,
    run_selected_scenarios,
)
from .selection.service import select_files

__all__ = (
    "preflight_external_tools",
    "run_file_pipeline",
    "run_pgf_stage_if_required",
    "run_selected_scenarios",
    "select_files",
)
