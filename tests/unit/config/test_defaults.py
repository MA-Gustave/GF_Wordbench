"""Unit tests for language-neutral framework configuration defaults."""

from __future__ import annotations

from pathlib import Path

from gf_wordbench.config import defaults
from gf_wordbench.config.models import (
    OutputDefaults,
    SchemaSupport,
    SelectionDefaults,
)
from gf_wordbench.kernel.statuses import ValidationMode

_EXPECTED_PUBLIC_NAMES = (
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


def test_defaults_module_exposes_only_the_canonical_public_constants() -> None:
    assert defaults.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(defaults, name) for name in defaults.__all__)


def test_selection_defaults_match_the_canonical_checkpoint_policy() -> None:
    selection = SelectionDefaults(
        mode=defaults.DEFAULT_VALIDATION_MODE,
        timeout_sec=defaults.DEFAULT_TIMEOUT_SECONDS,
        max_files=defaults.DEFAULT_MAX_FILES,
        keep_ok_details=defaults.DEFAULT_KEEP_OK_DETAILS,
        diff_previous=defaults.DEFAULT_DIFF_PREVIOUS,
        skip_version_probe=defaults.DEFAULT_SKIP_VERSION_PROBE,
        no_compile=defaults.DEFAULT_NO_COMPILE,
        emit_cpu_stats=defaults.DEFAULT_EMIT_CPU_STATS,
    )

    assert selection == SelectionDefaults(
        mode=ValidationMode.CHECKPOINT,
        timeout_sec=60,
        max_files=0,
        keep_ok_details=False,
        diff_previous=True,
        skip_version_probe=False,
        no_compile=False,
        emit_cpu_stats=False,
    )


def test_output_defaults_preserve_required_evidence_products() -> None:
    output = OutputDefaults(
        evidence_level=defaults.DEFAULT_EVIDENCE_LEVEL,
        generate_manifest=defaults.DEFAULT_GENERATE_MANIFEST,
        generate_ai_ready=defaults.DEFAULT_GENERATE_AI_READY,
        aggregate_logs=defaults.DEFAULT_AGGREGATE_LOGS,
    )

    assert output == OutputDefaults(
        evidence_level="standard",
        generate_manifest=True,
        generate_ai_ready=True,
        aggregate_logs=True,
    )


def test_supported_schema_majors_form_a_valid_schema_support_policy() -> None:
    support = SchemaSupport(
        project_major=defaults.SUPPORTED_PROJECT_SCHEMA_MAJOR,
        app_state_major=defaults.SUPPORTED_APP_STATE_SCHEMA_MAJOR,
        run_summary_major=defaults.SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
        artifact_manifest_major=(
            defaults.SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR
        ),
    )

    assert support == SchemaSupport(
        project_major=1,
        app_state_major=1,
        run_summary_major=1,
        artifact_manifest_major=1,
    )


def test_local_state_and_text_defaults_are_portable_leaf_values() -> None:
    assert defaults.DEFAULT_STATE_FILENAME == ".gf_wordbench_state.json"
    assert defaults.DEFAULT_TEXT_ENCODING == "utf-8"

    state_path = Path(defaults.DEFAULT_STATE_FILENAME)
    assert state_path.name == defaults.DEFAULT_STATE_FILENAME
    assert state_path.parent == Path(".")
    assert not state_path.is_absolute()


def test_framework_defaults_do_not_embed_machine_specific_paths() -> None:
    public_values = (
        getattr(defaults, name)
        for name in defaults.__all__
    )

    assert all(not isinstance(value, Path) for value in public_values)
