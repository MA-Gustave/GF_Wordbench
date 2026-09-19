from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.state.migrations import (
    LegacyStateMigration,
    StateMigrationError,
    StateMigrationWarning,
    migrate_legacy_state,
)
from gf_wordbench.state.models import StateDiagnosticCode
from gf_wordbench.state.repository import StateRepository
from gf_wordbench.state.schema import (
    APP_STATE_FILENAME,
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
    LEGACY_APP_STATE_FILENAME,
    default_app_state,
    default_app_state_document,
    parse_app_state,
    validate_app_state,
)


def _defaults() -> dict[str, object]:
    return cast("dict[str, object]", deepcopy(default_app_state_document()))


def _warning_pairs(
    migration: LegacyStateMigration,
) -> set[tuple[str, str]]:
    return {(warning.code, warning.field) for warning in migration.warnings}


def _write_json(path: Path, document: object) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_default_state_uses_path_resolved_environment_fields() -> None:
    document = _defaults()

    assert document["environment"] == {
        "last_selected_language_path": None,
        "last_selected_validation_profile": None,
        "last_rgl_root": None,
        "gf_executable": None,
        "output_root": None,
    }


def test_complete_supported_legacy_state_maps_to_path_resolved_shape() -> None:
    defaults = _defaults()
    legacy = {
        # A former project root cannot be converted safely into a selected
        # language path without loading project configuration and inspecting the
        # filesystem. Pure state migration therefore discards it.
        "selected_project_root": r"C:\work\GF Wordbench",
        "selected_rgl_root": r"C:\gf\rgl",
        "selected_gf_exe": r"C:\gf\bin\gf.exe",
        "selected_out_root": r"C:\work\runs",
        "selected_target_file": r"grammar\Main.gf",
        "last_run_dir": r"C:\work\runs\run_001",
        "last_summary_path": r"C:\work\runs\run_001\summary.json",
        "selected_mode": "release",
        "selected_timeout_sec": 180,
        "selected_max_files": 25,
        "selected_keep_ok_details": True,
        "selected_diff_previous": False,
        "selected_skip_version_probe": True,
        "selected_no_compile": False,
        "selected_emit_cpu_stats": True,
        "status_message": "  release   validation\ncompleted  ",
    }

    migration = migrate_legacy_state(
        legacy,
        canonical_defaults=defaults,
    )

    assert migration.payload["schema_id"] == APP_STATE_SCHEMA_ID
    assert migration.payload["schema_version"] == APP_STATE_SCHEMA_VERSION
    assert migration.payload["environment"] == {
        "last_selected_language_path": None,
        "last_selected_validation_profile": None,
        "last_rgl_root": "C:/gf/rgl",
        "gf_executable": "C:/gf/bin/gf.exe",
        "output_root": "C:/work/runs",
    }
    assert migration.payload["selection"] == {
        "mode": "release",
        "target_file": "grammar/Main.gf",
        "timeout_sec": 180,
        "max_files": 25,
        "keep_ok_details": True,
        "diff_previous": False,
        "skip_version_probe": True,
        "no_compile": False,
        "emit_cpu_stats": True,
    }
    assert migration.payload["last_run"] == {
        "run_dir": "C:/work/runs/run_001",
        "summary_path": "C:/work/runs/run_001/summary.json",
        "status_message": "release validation completed",
    }
    assert _warning_pairs(migration) == {("discarded_legacy_field", "selected_project_root")}
    assert migration.discarded_fields == ("selected_project_root",)
    assert migration.unknown_fields == ()
    assert migration.consumed_fields == tuple(
        sorted(set(legacy).difference({"selected_project_root"}))
    )

    state, warnings = parse_app_state(migration.payload, strict=False)
    validate_app_state(state)
    assert warnings == ()
    assert state.environment.last_selected_language_path is None
    assert state.environment.last_selected_validation_profile is None
    assert state.environment.last_rgl_root == "C:/gf/rgl"
    assert state.selection.mode is ValidationMode.RELEASE


def test_canonical_state_remembers_paths_without_restoring_language_truth() -> None:
    document = _defaults()
    environment = document["environment"]
    assert isinstance(environment, dict)
    environment.update(
        {
            "last_selected_language_path": ("C:/gf/rgl/src/english/LangEng.gf"),
            "last_selected_validation_profile": ("C:/work/profiles/english/project.toml"),
            "last_rgl_root": "C:/gf/rgl",
        }
    )

    state, warnings = parse_app_state(document, strict=False)

    assert warnings == ()
    assert state.environment.last_selected_language_path == "C:/gf/rgl/src/english/LangEng.gf"
    assert (
        state.environment.last_selected_validation_profile
        == "C:/work/profiles/english/project.toml"
    )
    assert state.environment.last_rgl_root == "C:/gf/rgl"

    serialized = json.dumps(document, sort_keys=True)
    for forbidden in (
        "language_key",
        "language_directory",
        "rgl_source_root",
        "module_suffix",
        "source_inventory",
        "resolved_language_context",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    ("legacy_mode", "expected"),
    [
        ("file", "quick"),
        (" FILE ", "quick"),
        ("all", "diagnostic"),
        ("ALL", "diagnostic"),
        ("checkpoint", "checkpoint"),
        ("Diagnostic", "diagnostic"),
        ("release", "release"),
    ],
)
def test_supported_mode_aliases_are_deterministic(
    legacy_mode: str,
    expected: str,
) -> None:
    migration = migrate_legacy_state(
        {"selected_mode": legacy_mode},
        canonical_defaults=_defaults(),
    )

    selection = migration.payload["selection"]
    assert isinstance(selection, dict)
    assert selection["mode"] == expected
    assert migration.warnings == ()


@pytest.mark.parametrize(
    ("legacy_mode", "warning_code"),
    [
        (None, "invalid_legacy_mode"),
        (42, "invalid_legacy_mode"),
        ("portfolio", "unknown_legacy_mode"),
        ("", "unknown_legacy_mode"),
    ],
)
def test_invalid_modes_fail_safe_to_diagnostic(
    legacy_mode: object,
    warning_code: str,
) -> None:
    migration = migrate_legacy_state(
        {"selected_mode": legacy_mode},
        canonical_defaults=_defaults(),
    )

    selection = migration.payload["selection"]
    assert isinstance(selection, dict)
    assert selection["mode"] == "diagnostic"
    assert _warning_pairs(migration) == {(warning_code, "selected_mode")}


def test_integer_and_boolean_aliases_are_coerced_with_warnings() -> None:
    migration = migrate_legacy_state(
        {
            "selected_timeout_sec": " 90 ",
            "selected_max_files": "+12",
            "selected_keep_ok_details": "YES",
            "selected_diff_previous": "off",
            "selected_skip_version_probe": 1,
            "selected_no_compile": 0,
            "selected_emit_cpu_stats": "true",
        },
        canonical_defaults=_defaults(),
    )

    selection = migration.payload["selection"]
    assert isinstance(selection, dict)
    assert selection["timeout_sec"] == 90
    assert selection["max_files"] == 12
    assert selection["keep_ok_details"] is True
    assert selection["diff_previous"] is False
    assert selection["skip_version_probe"] is True
    assert selection["no_compile"] is False
    assert selection["emit_cpu_stats"] is True
    assert _warning_pairs(migration) == {
        ("coerced_legacy_integer", "selected_timeout_sec"),
        ("coerced_legacy_integer", "selected_max_files"),
        ("coerced_legacy_boolean", "selected_keep_ok_details"),
        ("coerced_legacy_boolean", "selected_diff_previous"),
        ("coerced_legacy_boolean", "selected_skip_version_probe"),
        ("coerced_legacy_boolean", "selected_no_compile"),
        ("coerced_legacy_boolean", "selected_emit_cpu_stats"),
    }


def test_invalid_scalar_values_retain_canonical_defaults() -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {
            "selected_timeout_sec": 0,
            "selected_max_files": -1,
            "selected_keep_ok_details": 2,
            "selected_diff_previous": "sometimes",
            "selected_skip_version_probe": [],
            "selected_no_compile": None,
            "selected_emit_cpu_stats": object(),
        },
        canonical_defaults=defaults,
    )

    selection = migration.payload["selection"]
    default_selection = defaults["selection"]
    assert isinstance(selection, dict)
    assert isinstance(default_selection, dict)
    assert selection == default_selection
    assert _warning_pairs(migration) == {
        ("invalid_legacy_integer", "selected_timeout_sec"),
        ("invalid_legacy_integer", "selected_max_files"),
        ("invalid_legacy_boolean", "selected_keep_ok_details"),
        ("invalid_legacy_boolean", "selected_diff_previous"),
        ("invalid_legacy_boolean", "selected_skip_version_probe"),
        ("invalid_legacy_boolean", "selected_no_compile"),
        ("invalid_legacy_boolean", "selected_emit_cpu_stats"),
    }


def test_path_migration_preserves_local_paths_without_resolving_filesystem() -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {
            "selected_project_root": "",
            "selected_rgl_root": None,
            "selected_gf_exe": "relative\\gf.exe",
            "selected_out_root": "out\\runs",
            "selected_target_file": None,
            "last_run_dir": "run_001",
            "last_summary_path": "run_001\\summary.json",
        },
        canonical_defaults=defaults,
    )

    environment = migration.payload["environment"]
    selection = migration.payload["selection"]
    last_run = migration.payload["last_run"]
    assert isinstance(environment, dict)
    assert isinstance(selection, dict)
    assert isinstance(last_run, dict)
    assert environment == {
        "last_selected_language_path": None,
        "last_selected_validation_profile": None,
        "last_rgl_root": None,
        "gf_executable": "relative/gf.exe",
        "output_root": "out/runs",
    }
    assert selection["target_file"] == ""
    assert last_run["run_dir"] == "run_001"
    assert last_run["summary_path"] == "run_001/summary.json"
    assert _warning_pairs(migration) == {("discarded_legacy_field", "selected_project_root")}
    assert migration.discarded_fields == ("selected_project_root",)


@pytest.mark.parametrize(
    "field",
    [
        "selected_rgl_root",
        "selected_gf_exe",
        "selected_out_root",
        "selected_target_file",
        "last_run_dir",
        "last_summary_path",
    ],
)
def test_invalid_legacy_paths_are_ignored(field: str) -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {field: "bad\x00path"},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {("invalid_legacy_path", field)}
    assert migration.consumed_fields == (field,)


@pytest.mark.parametrize(
    "field",
    [
        "last_selected_language_path",
        "last_selected_validation_profile",
        "last_rgl_root",
        "gf_executable",
        "output_root",
    ],
)
def test_invalid_canonical_environment_paths_are_defaulted(field: str) -> None:
    document = _defaults()
    environment = document["environment"]
    assert isinstance(environment, dict)
    environment[field] = "bad\x00path"

    state, warnings = parse_app_state(document, strict=False)

    assert getattr(state.environment, field) is None
    assert any(f"$.environment.{field}" in warning for warning in warnings)


def test_status_message_is_normalized_and_bounded() -> None:
    migration = migrate_legacy_state(
        {"status_message": "  alpha\n beta\t gamma delta  "},
        canonical_defaults=_defaults(),
        status_message_limit=16,
    )

    last_run = migration.payload["last_run"]
    assert isinstance(last_run, dict)
    assert last_run["status_message"] == "alpha beta gamma"
    assert _warning_pairs(migration) == {("truncated_legacy_status_message", "status_message")}


def test_invalid_status_message_retains_default() -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {"status_message": ["not", "text"]},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {("invalid_legacy_status_message", "status_message")}


def test_language_identity_runtime_and_evidence_fields_are_discarded() -> None:
    discarded = {
        "selected_project_root": r"C:\workspace\project",
        "last_language_id": "Eng",
        "catalog_path": r"C:\workspace\rgl-language-catalog.json",
        "last_catalog_entry": "Eng",
        "selected_scan_dir": "src",
        "selected_scan_glob": "*.gf",
        "selected_gf_path": ["src"],
        "selected_include_regex": ".*",
        "selected_exclude_regex": "generated",
        "is_running": True,
        "current_run_config": {"mode": "release"},
        "current_run_result": {"status": "OK"},
        "language": "Example",
        "language_name": "Example Language",
        "language_code": "ex",
        "project_id": "example",
        "project_name": "Example",
        "project_registry": ["one", "two"],
        "audit_results": [1],
        "file_results": [2],
        "scenario_results": [3],
    }
    legacy = {
        **discarded,
        "future_extension": {"enabled": True},
        "selected_mode": "quick",
    }

    migration = migrate_legacy_state(
        legacy,
        canonical_defaults=_defaults(),
    )

    assert migration.discarded_fields == tuple(sorted(discarded))
    assert migration.unknown_fields == ("future_extension",)
    assert migration.consumed_fields == ("selected_mode",)
    assert {
        warning.field for warning in migration.warnings if warning.code == "discarded_legacy_field"
    } == set(discarded)

    serialized = json.dumps(migration.payload, sort_keys=True)
    for field in (*discarded, "future_extension"):
        assert field not in serialized


def test_migration_does_not_mutate_inputs_or_share_nested_values() -> None:
    defaults = _defaults()
    defaults["extension"] = {
        "nested": [
            {"value": 1},
            ["alpha", "beta"],
        ]
    }
    legacy = {"selected_mode": "quick"}
    defaults_before = deepcopy(defaults)
    legacy_before = deepcopy(legacy)

    migration = migrate_legacy_state(
        legacy,
        canonical_defaults=defaults,
    )

    assert defaults == defaults_before
    assert legacy == legacy_before
    assert migration.payload is not defaults
    assert migration.payload["extension"] is not defaults["extension"]

    extension = migration.payload["extension"]
    assert isinstance(extension, dict)
    nested = extension["nested"]
    assert isinstance(nested, list)
    nested.append("changed")
    assert defaults == defaults_before


def test_migration_result_and_warnings_are_immutable() -> None:
    migration = migrate_legacy_state(
        {"selected_mode": "unknown"},
        canonical_defaults=_defaults(),
    )

    assert isinstance(migration, LegacyStateMigration)
    assert isinstance(migration.warnings[0], StateMigrationWarning)
    with pytest.raises(FrozenInstanceError):
        migration.consumed_fields = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        migration.warnings[0].code = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "legacy",
    [
        {"schema_id": APP_STATE_SCHEMA_ID},
        {"schema_version": APP_STATE_SCHEMA_VERSION},
        {
            "schema_id": APP_STATE_SCHEMA_ID,
            "schema_version": APP_STATE_SCHEMA_VERSION,
        },
    ],
)
def test_versioned_documents_are_not_treated_as_legacy(
    legacy: dict[str, object],
) -> None:
    with pytest.raises(
        StateMigrationError,
        match="Versioned state must be handled",
    ):
        migrate_legacy_state(
            legacy,
            canonical_defaults=_defaults(),
        )


@pytest.mark.parametrize(
    ("defaults", "message"),
    [
        ({}, "missing object group"),
        (
            {
                "environment": {},
                "selection": {},
                "last_run": [],
            },
            "missing object group",
        ),
        (
            {
                "environment": {},
                "selection": {},
                "last_run": {},
                "": "invalid",
            },
            "non-empty string",
        ),
        (
            {
                "environment": {},
                "selection": {},
                "last_run": {},
                "invalid": float("inf"),
            },
            "not finite",
        ),
        (
            {
                "environment": {},
                "selection": {},
                "last_run": {},
                "invalid": object(),
            },
            "not JSON-compatible",
        ),
    ],
)
def test_invalid_canonical_defaults_fail_closed(
    defaults: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(StateMigrationError, match=message):
        migrate_legacy_state(
            {},
            canonical_defaults=defaults,
        )


@pytest.mark.parametrize("limit", [True, False, 1.5, "32", None])
def test_status_message_limit_requires_an_integer(limit: object) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        migrate_legacy_state(
            {},
            canonical_defaults=_defaults(),
            status_message_limit=cast("int", limit),
        )


@pytest.mark.parametrize("limit", [0, -1, -100])
def test_status_message_limit_must_be_positive(limit: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        migrate_legacy_state(
            {},
            canonical_defaults=_defaults(),
            status_message_limit=limit,
        )


def test_repository_migrates_once_publishes_canonical_and_preserves_source(
    tmp_path: Path,
) -> None:
    repository = StateRepository(workspace_root=tmp_path.resolve())
    legacy_path = tmp_path / LEGACY_APP_STATE_FILENAME
    canonical_path = tmp_path / APP_STATE_FILENAME
    legacy_document = {
        "selected_project_root": r"C:\workspace\project",
        "selected_rgl_root": r"C:\gf\rgl",
        "selected_mode": "file",
        "selected_timeout_sec": "75",
        "selected_no_compile": "yes",
        "language_name": "must not become application state",
        "unknown_future_field": 7,
        "status_message": " migrated from legacy ",
    }
    _write_json(legacy_path, legacy_document)
    original_legacy_bytes = legacy_path.read_bytes()

    result = repository.load_with_diagnostics()

    assert result.migrated is True
    assert result.source_path == canonical_path.resolve()
    assert result.state.selection.mode is ValidationMode.QUICK
    assert result.state.selection.timeout_sec == 75
    assert result.state.selection.no_compile is True
    assert result.state.environment.last_selected_language_path is None
    assert result.state.environment.last_selected_validation_profile is None
    assert result.state.environment.last_rgl_root == "C:/gf/rgl"
    assert result.state.last_run.status_message == "migrated from legacy"
    assert any(diagnostic.code is StateDiagnosticCode.MIGRATED for diagnostic in result.diagnostics)
    assert any(
        diagnostic.code is StateDiagnosticCode.PARTIALLY_DEFAULTED
        for diagnostic in result.diagnostics
    )
    assert canonical_path.is_file()
    assert legacy_path.read_bytes() == original_legacy_bytes

    canonical_document = json.loads(canonical_path.read_text(encoding="utf-8"))
    assert canonical_document["schema_id"] == APP_STATE_SCHEMA_ID
    assert canonical_document["schema_version"] == APP_STATE_SCHEMA_VERSION
    assert "producer" in canonical_document
    assert "project_root" not in canonical_document["environment"]
    assert "language_name" not in canonical_document
    assert "unknown_future_field" not in canonical_document

    _write_json(
        legacy_path,
        {
            "selected_mode": "release",
            "status_message": "must not be imported twice",
        },
    )
    second = repository.load_with_diagnostics()

    assert second.migrated is False
    assert second.state.selection.mode is ValidationMode.QUICK
    assert second.state.last_run.status_message == "migrated from legacy"
    assert any(diagnostic.code is StateDiagnosticCode.LOADED for diagnostic in second.diagnostics)


def test_existing_canonical_state_has_precedence_over_legacy_state(
    tmp_path: Path,
) -> None:
    repository = StateRepository(workspace_root=tmp_path.resolve())
    repository.save(default_app_state())
    legacy_path = tmp_path / LEGACY_APP_STATE_FILENAME
    _write_json(
        legacy_path,
        {
            "selected_mode": "release",
            "selected_timeout_sec": 999,
        },
    )

    result = repository.load_with_diagnostics()

    assert result.migrated is False
    assert result.state.selection.mode is ValidationMode.DIAGNOSTIC
    assert result.state.selection.timeout_sec == 60
    assert any(diagnostic.code is StateDiagnosticCode.LOADED for diagnostic in result.diagnostics)
    assert not any(
        diagnostic.code is StateDiagnosticCode.MIGRATED for diagnostic in result.diagnostics
    )


def test_invalid_legacy_state_falls_back_without_rewriting_source(
    tmp_path: Path,
) -> None:
    repository = StateRepository(workspace_root=tmp_path.resolve())
    legacy_path = tmp_path / LEGACY_APP_STATE_FILENAME
    canonical_path = tmp_path / APP_STATE_FILENAME
    legacy_document = {
        "schema_id": APP_STATE_SCHEMA_ID,
        "schema_version": APP_STATE_SCHEMA_VERSION,
    }
    _write_json(legacy_path, legacy_document)
    original = legacy_path.read_bytes()

    result = repository.load_with_diagnostics()

    assert result.migrated is False
    assert result.state == default_app_state()
    assert result.source_path == canonical_path.resolve()
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code is StateDiagnosticCode.MALFORMED
    assert result.diagnostics[0].path == legacy_path.resolve()
    assert canonical_path.exists() is False
    assert legacy_path.read_bytes() == original
