"""Stable public façade for diagnostic interpretation and classification."""

from __future__ import annotations

from gf_wordbench.diagnostics.classification.service import (
    classify_file_results,
    classify_scenario_results,
)
from gf_wordbench.diagnostics.classification.top_errors import (
    DEFAULT_TOP_ERROR_POLICY,
    TopErrorAggregationPolicy,
    TopErrorCandidate,
    bucket_top_errors,
)
from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticParseResult,
    DiagnosticRecord,
)
from gf_wordbench.diagnostics.parsing.service import parse_diagnostics

__all__ = (
    "DEFAULT_TOP_ERROR_POLICY",
    "DiagnosticEvidence",
    "DiagnosticParseResult",
    "DiagnosticRecord",
    "TopErrorAggregationPolicy",
    "TopErrorCandidate",
    "bucket_top_errors",
    "classify_file_results",
    "classify_scenario_results",
    "parse_diagnostics",
)
