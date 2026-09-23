"""Language-neutral framework defaults for GF Wordbench.

This module owns primitive default values only. Project identity, language
modules, scenario identifiers, executable paths, and other machine- or
project-specific values must be supplied by their owning configuration source.
"""

from typing import Final, cast

from gf_wordbench.config.models import (
    AppConfig,
    EvidenceLevel,
    OutputDefaults,
    SchemaSupport,
    SelectionDefaults,
)
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.version import __version__

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


def build_framework_defaults() -> AppConfig:
    """Build the language-neutral framework default configuration.

    Keeping this factory in the configuration layer lets GUI runtime composition
    consume defaults without importing the top-level bootstrap composition root.
    ``gf_wordbench.bootstrap.build_framework_defaults`` remains a compatibility
    facade.
    """

    return AppConfig(
        producer=ProducerInfo(name="gf-wordbench", version=__version__),
        selection_defaults=SelectionDefaults(
            mode=DEFAULT_VALIDATION_MODE,
            timeout_sec=DEFAULT_TIMEOUT_SECONDS,
            max_files=DEFAULT_MAX_FILES,
            keep_ok_details=DEFAULT_KEEP_OK_DETAILS,
            diff_previous=DEFAULT_DIFF_PREVIOUS,
            skip_version_probe=DEFAULT_SKIP_VERSION_PROBE,
            no_compile=DEFAULT_NO_COMPILE,
            emit_cpu_stats=DEFAULT_EMIT_CPU_STATS,
        ),
        output_defaults=OutputDefaults(
            evidence_level=cast(EvidenceLevel, DEFAULT_EVIDENCE_LEVEL),
            generate_manifest=DEFAULT_GENERATE_MANIFEST,
            generate_ai_ready=DEFAULT_GENERATE_AI_READY,
            aggregate_logs=DEFAULT_AGGREGATE_LOGS,
        ),
        schema_support=SchemaSupport(
            project_major=SUPPORTED_PROJECT_SCHEMA_MAJOR,
            app_state_major=SUPPORTED_APP_STATE_SCHEMA_MAJOR,
            run_summary_major=SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
            artifact_manifest_major=SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR,
        ),
        state_filename=DEFAULT_STATE_FILENAME,
    )


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
