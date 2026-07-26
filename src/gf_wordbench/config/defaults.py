"""Language-neutral framework defaults for GF Wordbench.

This module owns primitive default values only. Project identity, language
modules, scenario identifiers, executable paths, and other machine- or
project-specific values must be supplied by their owning configuration source.
"""

from typing import Final

from gf_wordbench.kernel.statuses import ValidationMode

DEFAULT_VALIDATION_MODE: Final[ValidationMode] = ValidationMode.CHECKPOINT
DEFAULT_TIMEOUT_SECONDS: Final[int] = 60
DEFAULT_MAX_FILES: Final[int] = 0

DEFAULT_KEEP_OK_DETAILS: Final[bool] = False
DEFAULT_DIFF_PREVIOUS: Final[bool] = True
DEFAULT_SKIP_VERSION_PROBE: Final[bool] = False
DEFAULT_NO_COMPILE: Final[bool] = False
DEFAULT_EMIT_CPU_STATS: Final[bool] = False

DEFAULT_EVIDENCE_LEVEL: Final[str] = "standard"
DEFAULT_GENERATE_MANIFEST: Final[bool] = True
DEFAULT_GENERATE_AI_READY: Final[bool] = True
DEFAULT_AGGREGATE_LOGS: Final[bool] = True

DEFAULT_STATE_FILENAME: Final[str] = ".gf_wordbench_state.json"
DEFAULT_TEXT_ENCODING: Final[str] = "utf-8"

SUPPORTED_PROJECT_SCHEMA_MAJOR: Final[int] = 1
SUPPORTED_APP_STATE_SCHEMA_MAJOR: Final[int] = 1
SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR: Final[int] = 1
SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR: Final[int] = 1

__all__ = (
    "DEFAULT_AGGREGATE_LOGS",
    "DEFAULT_DIFF_PREVIOUS",
    "DEFAULT_EMIT_CPU_STATS",
    "DEFAULT_EVIDENCE_LEVEL",
    "DEFAULT_GENERATE_AI_READY",
    "DEFAULT_GENERATE_MANIFEST",
    "DEFAULT_KEEP_OK_DETAILS",
    "DEFAULT_MAX_FILES",
    "DEFAULT_NO_COMPILE",
    "DEFAULT_SKIP_VERSION_PROBE",
    "DEFAULT_STATE_FILENAME",
    "DEFAULT_TEXT_ENCODING",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_VALIDATION_MODE",
    "SUPPORTED_APP_STATE_SCHEMA_MAJOR",
    "SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR",
    "SUPPORTED_PROJECT_SCHEMA_MAJOR",
    "SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR",
)