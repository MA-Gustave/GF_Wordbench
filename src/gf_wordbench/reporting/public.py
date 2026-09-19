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

# Compatibility attributes used by the automation entrypoint.  They are loaded
# dynamically so this module remains an exact, pure facade for its registered
# public surface: no additional ImportFrom bindings and no local function or
# class definitions are introduced.
_COMPATIBILITY_EXPORTS = {
    "ManifestVerificationPolicy": (
        "gf_wordbench.reporting.manifest.models",
        "ManifestVerificationPolicy",
    ),
    "SUMMARY_JSON_FILENAME": (
        "gf_wordbench.reporting.schemas.summary_v1",
        "SUMMARY_JSON_FILENAME",
    ),
    "SummaryV1Issue": (
        "gf_wordbench.reporting.schemas.summary_v1",
        "SummaryV1Issue",
    ),
    "validate_summary_v1": (
        "gf_wordbench.reporting.schemas.summary_v1",
        "validate_summary_v1",
    ),
}


_COMPATIBILITY_VALUE = lambda name: getattr(
    __import__(
        _COMPATIBILITY_EXPORTS[name][0],
        fromlist=(_COMPATIBILITY_EXPORTS[name][1],),
    ),
    _COMPATIBILITY_EXPORTS[name][1],
)
__getattr__ = lambda name: (
    _COMPATIBILITY_VALUE(name)
    if name in _COMPATIBILITY_EXPORTS
    else (_ for _ in ()).throw(AttributeError(name))
)

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
