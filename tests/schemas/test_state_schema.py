"""Schema tests for the canonical GF Wordbench application state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.state.models import (
    EnvironmentState,
    LastRunState,
    SelectionState,
)
from gf_wordbench.state.schema import (
    APP_STATE_FILENAME,
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
    CANONICAL_MODES,
    LEGACY_APP_STATE_FILENAME,
    MAX_STATE_WARNINGS,
    canonicalize_app_state_document,
    default_app_state,
    default_app_state_document,
    parse_app_state,
    producer_document,
    recover_app_state_document,
    serialize_app_state,
    validate_app_state,
)


def _persisted_document() -> dict[str, object]:
    document: dict[str, object] = deepcopy(default_app_state_document())
    document["producer"] = producer_document("1.2.3")
    return document


def test_schema_identity_and_filenames_are_canonical() -> None:
    assert APP_STATE_SCHEMA_ID == "gf-wordbench.app-state"
    assert APP_STATE_SCHEMA_VERSION == "1.0"
    assert APP_STATE_FILENAME == ".gf_wordbench_state.json"
    assert LEGACY_APP_STATE_FILENAME == ".gf_audit_state.json"
    assert CANONICAL_MODES == {
        "quick",
        "checkpoint",
        "diagnostic",
        "release",
    }
    assert MAX_STATE_WARNINGS == 32


def test_default_document_contains_only_safe_disposable_state() -> None:
    assert default_app_state_document() == {
        "schema_id": "gf-wordbench.app-state",
        "schema_version": "1.0",
        "environment": {
            "project_root": None,
            "rgl_root": None,
            "gf_executable": None,
            "output_root": None,
        },
        "selection": {
            "mode": "diagnostic",
            "target_file": "",
            "timeout_sec": 60,
            "max_files": 0,
            "keep_ok_details": False,
            "diff_previous": True,
            "skip_version_probe": False,
            "no_compile": False,
            "emit_cpu_stats": False,
        },
        "last_run": {
            "run_dir": None,
            "summary_path": None,
            "status_message": "",
        },
    }


@pytest.mark.parametrize("mode", tuple(ValidationMode))
def test_all_canonical_modes_round_trip_in_strict_state(
    mode: ValidationMode,
) -> None:
    document = _persisted_document()
    selection = document["selection"]
    assert isinstance(selection, dict)
    selection["mode"] = mode.value

    state, warnings = parse_app_state(document, strict=True)
    serialized = serialize_app_state(state)

    assert warnings == ()
    assert state.selection.mode is mode
    assert serialized["selection"]["mode"] == mode.value
    assert serialized["producer"] == {
        "name": "gf-wordbench",
        "version": "1.2.3",
    }


def test_tolerant_recovery_normalizes_paths_and_defaults_bad_preferences() -> None:
    document = default_app_state_document()
    document["environment"]["project_root"] = (
        r"C:\work\GF Wordbench"
    )
    document["environment"]["gf_executable"] = (
        r"C:\Program Files\GF\gf.exe"
    )
    document["selection"]["target_file"] = r"src\Grammar.gf"
    document["selection"]["mode"] = "file"
    document["selection"]["timeout_sec"] = True
    document["selection"]["max_files"] = -4
    document["selection"]["keep_ok_details"] = "yes"

    result = recover_app_state_document(document)

    assert result.compatible is True
    assert result.rewrite_safe is True
    assert result.document["environment"]["project_root"] == (
        "C:/work/GF Wordbench"
    )
    assert result.document["environment"]["gf_executable"] == (
        "C:/Program Files/GF/gf.exe"
    )
    assert result.document["selection"]["target_file"] == (
        "src/Grammar.gf"
    )
    assert result.document["selection"]["mode"] == "diagnostic"
    assert result.document["selection"]["timeout_sec"] == 60
    assert result.document["selection"]["max_files"] == 0
    assert result.document["selection"]["keep_ok_details"] is False

    warning_codes = {warning.code for warning in result.warnings}
    assert {
        "normalized_path",
        "invalid_mode",
        "invalid_integer",
        "invalid_boolean",
    } <= warning_codes


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "~",
        "~/workspace",
        r"%USERPROFILE%\workspace",
        "${HOME}/workspace",
        "$HOME/workspace",
        "prefix\x00suffix",
    ),
)
def test_unsafe_environment_paths_default_to_null(
    unsafe_path: str,
) -> None:
    document = default_app_state_document()
    document["environment"]["project_root"] = unsafe_path

    result = recover_app_state_document(document)

    assert result.document["environment"]["project_root"] is None
    assert any(
        warning.code == "invalid_path"
        and warning.field == "$.environment.project_root"
        for warning in result.warnings
    )


def test_future_minor_is_read_compatibly_but_not_rewrite_safe() -> None:
    document = default_app_state_document()
    document["schema_version"] = "1.7"
    document["selection"]["mode"] = "quick"

    result = recover_app_state_document(document)
    state, warnings = parse_app_state(document)

    assert result.compatible is True
    assert result.rewrite_safe is False
    assert result.source_schema_version == "1.7"
    assert result.document["schema_version"] == "1.0"
    assert result.document["selection"]["mode"] == "quick"
    assert state.schema_version == "1.0"
    assert state.selection.mode is ValidationMode.QUICK
    assert warnings == (
        "$.schema_version: known fields were recovered; "
        "automatic rewrite is unsafe",
    )


def test_unsupported_major_is_never_silently_rewritten() -> None:
    document = default_app_state_document()
    document["schema_version"] = "2.0"

    result = recover_app_state_document(document)

    assert result.compatible is False
    assert result.rewrite_safe is False
    assert result.source_schema_version == "2.0"
    assert result.warnings[0].code == "unsupported_schema_major"

    with pytest.raises(
        UnsupportedVersionError,
        match=r"schema major 2 is unsupported",
    ):
        parse_app_state(document)


def test_strict_schema_rejects_unknown_and_missing_fields() -> None:
    unknown = _persisted_document()
    unknown["project_id"] = "forbidden-second-owner"

    with pytest.raises(
        SchemaValidationError,
        match=r"\$: unknown fields: project_id",
    ):
        canonicalize_app_state_document(unknown)

    missing = _persisted_document()
    del missing["last_run"]

    with pytest.raises(
        SchemaValidationError,
        match=r"\$: missing required fields: last_run",
    ):
        canonicalize_app_state_document(missing)


def test_strict_parse_requires_producer_metadata() -> None:
    document = default_app_state_document()

    with pytest.raises(
        SchemaValidationError,
        match=r"\$: missing required fields: producer",
    ):
        parse_app_state(document, strict=True)


def test_serialize_emits_whitelisted_portable_state() -> None:
    base = default_app_state()
    state = replace(
        base,
        producer=ProducerInfo(
            name="gf-wordbench",
            version="9.8.7",
        ),
        environment=EnvironmentState(
            project_root=r"C:\work\GF Wordbench",
            rgl_root=r"C:\work\gf-rgl\src",
            gf_executable=r"C:\tools\gf\gf.exe",
            output_root=r"D:\runs",
        ),
        selection=SelectionState(
            mode=ValidationMode.CHECKPOINT,
            target_file=r"src\Checkpoint.gf",
            timeout_sec=90,
            max_files=25,
            keep_ok_details=True,
            diff_previous=False,
            skip_version_probe=True,
            no_compile=False,
            emit_cpu_stats=True,
        ),
        last_run=LastRunState(
            run_dir=r"D:\runs\run_20260725T120000Z",
            summary_path=(
                r"D:\runs\run_20260725T120000Z\summary.json"
            ),
            status_message="Terminé — 日本語",
        ),
    )

    validate_app_state(state, require_producer=True)
    document = serialize_app_state(state)

    assert tuple(document) == (
        "schema_id",
        "schema_version",
        "environment",
        "selection",
        "last_run",
        "producer",
    )
    assert document["environment"] == {
        "project_root": "C:/work/GF Wordbench",
        "rgl_root": "C:/work/gf-rgl/src",
        "gf_executable": "C:/tools/gf/gf.exe",
        "output_root": "D:/runs",
    }
    assert document["selection"]["target_file"] == (
        "src/Checkpoint.gf"
    )
    assert document["last_run"]["run_dir"] == (
        "D:/runs/run_20260725T120000Z"
    )
    assert document["last_run"]["summary_path"].endswith(
        "/summary.json"
    )
    assert document["last_run"]["status_message"] == "Terminé — 日本語"


def test_serializer_requires_a_canonical_producer() -> None:
    state = default_app_state()

    with pytest.raises(
        SchemaValidationError,
        match="producer_version is required",
    ):
        serialize_app_state(state)

    document = serialize_app_state(
        state,
        producer_version="3.0.0",
    )
    assert document["producer"] == {
        "name": "gf-wordbench",
        "version": "3.0.0",
    }


def test_source_path_is_included_in_strict_validation_errors(
    tmp_path: Path,
) -> None:
    source = tmp_path / ".gf_wordbench_state.json"
    document = _persisted_document()
    document["schema_id"] = "wrong.schema"

    with pytest.raises(SchemaValidationError) as caught:
        canonicalize_app_state_document(
            document,
            source=source,
        )

    assert str(caught.value).startswith(f"{source}: $.schema_id:")
