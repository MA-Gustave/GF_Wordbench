"""Stable cross-module reporting facade for GF Wordbench."""

from __future__ import annotations

from gf_wordbench.reporting.ai_packet.renderer import write_ai_ready
from gf_wordbench.reporting.logs.aggregates import (
    write_all_logs,
    write_all_scan_logs,
)
from gf_wordbench.reporting.manifest.builder import build_manifest, write_manifest
from gf_wordbench.reporting.manifest.verifier import verify_manifest
from gf_wordbench.reporting.publisher import publish_reports
from gf_wordbench.reporting.summary.json_writer import write_summary_json
from gf_wordbench.reporting.summary.markdown_writer import write_summary_md

__all__ = (
    "build_manifest",
    "publish_reports",
    "verify_manifest",
    "write_ai_ready",
    "write_all_logs",
    "write_all_scan_logs",
    "write_manifest",
    "write_summary_json",
    "write_summary_md",
)
