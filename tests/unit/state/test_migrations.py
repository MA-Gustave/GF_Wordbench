"""Unit tests for pure legacy application-state migration."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.state.migrations import (
    LegacyStateMigration,
    StateMigrationError,
    StateMigrationWarning,
    migrate_legacy_state,
)
from gf_wordbench.state.schema import (
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
    default_app_state_document,
    parse_app_state,
    validate_app_state,
)


def _defaults() -> dict[str, object]:
    return deepcopy(default_app_state_document())


def _group(
    migration: LegacyStateMigration,
    name: str,
) -> dict[str, Any]:
    value = migration.payload[name]
    assert isinstance(value, dict)
    return cast(dict[str, Any], value)


def _warning_pairs(
    migration: LegacyStateMigration,
) -> set[tuple[str, str]]:
    return {
        (warning.code, warning.field)
        for warning in migration.warnings
    }


def test_complete_legacy_document_maps_to_canonical_state() -> None:
    legacy = {
        "selected_project_root": r"C:\work\GF Wordbench",
        "selected_rgl_root": r"C:\gf\rgl",
        "selected_gf_exe": r"C:\gf\bin\gf.exe",
        "selected_out_root": r"C:\work\runs",
        "selected_target_file": r"grammar\Main.gf",
        "selected_mode": "release",
        "selected_timeout_sec": 180,
        "selected_max_files": 25,
        "selected_keep_ok_details": True,
        "selected_diff_previous": False,
        "selected_skip_version_probe": True,
        "selected_no_compile": False,
        "selected_emit_cpu_stats": True,
        "last_run_dir": r"C:\work\runs\run_001",
        "last_summary_path": r"C:\work\runs\run_001\summary.json",
        "status_message": "  release   validation\ncompleted  ",
    }

    migration = migrate_legacy_state(
        legacy,
        canonical_defaults=_defaults(),
    )

    assert migration.payload["schema_id"] == APP_STATE_SCHEMA_ID
    assert (
        migration.payload["schema_version"]
        == APP_STATE_SCHEMA_VERSION
    )
    assert _group(migration, "environment") == {
        "project_root": "C:/work/GF Wordbench",
        "rgl_root": "C:/gf/rgl",
        "gf_executable": "C:/gf/bin/gf.exe",
        "output_root": "C:/work/runs",
    }
    assert _group(migration, "selection") == {
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
    assert _group(migration, "last_run") == {
        "run_dir": "C:/work/runs/run_001",
        "summary_path": "C:/work/runs/run_001/summary.json",
        "status_message": "release validation completed",
    }
    assert migration.warnings == ()
    assert migration.consumed_fields == tuple(sorted(legacy))
    assert migration.discarded_fields == ()
    assert migration.unknown_fields == ()

    state, warnings = parse_app_state(migration.payload, strict=False)
    assert warnings == ()
    validate_app_state(state)
    assert state.selection.mode is ValidationMode.RELEASE


@pytest.mark.parametrize(
    ("legacy_mode", "expected"),
    [
        ("file", "quick"),
        (" FILE ", "quick"),
        ("all", "diagnostic"),
        ("ALL", "diagnostic"),
        ("quick", "quick"),
        ("checkpoint", "checkpoint"),
        ("Diagnostic", "diagnostic"),
        ("release", "release"),
    ],
)
def test_mode_aliases_and_canonical_modes_are_supported(
    legacy_mode: str,
    expected: str,
) -> None:
    migration = migrate_legacy_state(
        {"selected_mode": legacy_mode},
        canonical_defaults=_defaults(),
    )

    assert _group(migration, "selection")["mode"] == expected
    assert migration.warnings == ()


@pytest.mark.parametrize(
    ("legacy_mode", "warning_code"),
    [
        (None, "invalid_legacy_mode"),
        (42, "invalid_legacy_mode"),
        ([], "invalid_legacy_mode"),
        ("", "unknown_legacy_mode"),
        ("portfolio", "unknown_legacy_mode"),
    ],
)
def test_invalid_mode_falls_back_to_diagnostic(
    legacy_mode: object,
    warning_code: str,
) -> None:
    migration = migrate_legacy_state(
        {"selected_mode": legacy_mode},
        canonical_defaults=_defaults(),
    )

    assert _group(migration, "selection")["mode"] == "diagnostic"
    assert _warning_pairs(migration) == {
        (warning_code, "selected_mode")
    }


def test_integer_and_boolean_aliases_are_coerced() -> None:
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

    selection = _group(migration, "selection")
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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_timeout_sec", 0),
        ("selected_timeout_sec", True),
        ("selected_timeout_sec", "1.5"),
        ("selected_max_files", -1),
        ("selected_max_files", False),
        ("selected_max_files", "many"),
    ],
)
def test_invalid_integer_retains_default(
    field: str,
    value: object,
) -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {field: value},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {
        ("invalid_legacy_integer", field)
    }
    assert migration.consumed_fields == (field,)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_keep_ok_details", 2),
        ("selected_diff_previous", -1),
        ("selected_skip_version_probe", "sometimes"),
        ("selected_no_compile", None),
        ("selected_emit_cpu_stats", []),
    ],
)
def test_invalid_boolean_retains_default(
    field: str,
    value: object,
) -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {field: value},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {
        ("invalid_legacy_boolean", field)
    }


def test_paths_are_normalized_without_filesystem_resolution() -> None:
    migration = migrate_legacy_state(
        {
            "selected_project_root": "",
            "selected_rgl_root": None,
            "selected_gf_exe": r"relative\gf.exe",
            "selected_out_root": r"out\runs",
            "selected_target_file": None,
            "last_run_dir": "run_001",
            "last_summary_path": r"run_001\summary.json",
        },
        canonical_defaults=_defaults(),
    )

    assert _group(migration, "environment") == {
        "project_root": None,
        "rgl_root": None,
        "gf_executable": "relative/gf.exe",
        "output_root": "out/runs",
    }
    assert _group(migration, "selection")["target_file"] == ""
    assert _group(migration, "last_run") == {
        "run_dir": "run_001",
        "summary_path": "run_001/summary.json",
        "status_message": "",
    }
    assert migration.warnings == ()


@pytest.mark.parametrize(
    "field",
    [
        "selected_project_root",
        "selected_rgl_root",
        "selected_gf_exe",
        "selected_out_root",
        "selected_target_file",
        "last_run_dir",
        "last_summary_path",
    ],
)
def test_control_characters_make_legacy_paths_invalid(
    field: str,
) -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {field: "bad\x00path"},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {
        ("invalid_legacy_path", field)
    }


def test_status_message_is_whitespace_normalized_and_bounded() -> None:
    migration = migrate_legacy_state(
        {"status_message": "  alpha\n beta\t gamma delta  "},
        canonical_defaults=_defaults(),
        status_message_limit=16,
    )

    assert (
        _group(migration, "last_run")["status_message"]
        == "alpha beta gamma"
    )
    assert _warning_pairs(migration) == {
        ("truncated_legacy_status_message", "status_message")
    }


def test_non_text_status_message_is_ignored() -> None:
    defaults = _defaults()
    migration = migrate_legacy_state(
        {"status_message": ["not", "text"]},
        canonical_defaults=defaults,
    )

    assert migration.payload == defaults
    assert _warning_pairs(migration) == {
        ("invalid_legacy_status_message", "status_message")
    }


def test_runtime_project_and_evidence_fields_are_discarded() -> None:
    discarded = {
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
        "selected_mode": "quick",
        "future_extension": {"enabled": True},
    }

    migration = migrate_legacy_state(
        legacy,
        canonical_defaults=_defaults(),
    )

    assert migration.consumed_fields == ("selected_mode",)
    assert migration.discarded_fields == tuple(sorted(discarded))
    assert migration.unknown_fields == ("future_extension",)
    assert {
        warning.field
        for warning in migration.warnings
        if warning.code == "discarded_legacy_field"
    } == set(discarded)

    serialized = json.dumps(migration.payload, sort_keys=True)
    for field in (*discarded, "future_extension"):
        assert field not in serialized


def test_field_summaries_are_sorted_and_deterministic() -> None:
    legacy = {
        "z_future": 1,
        "selected_mode": "quick",
        "a_future": 2,
        "scenario_results": [],
        "audit_results": [],
    }

    first = migrate_legacy_state(
        legacy,
        canonical_defaults=_defaults(),
    )
    second = migrate_legacy_state(
        dict(reversed(tuple(legacy.items()))),
        canonical_defaults=_defaults(),
    )

    assert first.payload == second.payload
    assert first.consumed_fields == ("selected_mode",)
    assert first.discarded_fields == (
        "audit_results",
        "scenario_results",
    )
    assert first.unknown_fields == ("a_future", "z_future")


def test_inputs_are_not_mutated_or_shared() -> None:
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


def test_result_and_warning_records_are_frozen() -> None:
    migration = migrate_legacy_state(
        {"selected_mode": "unknown"},
        canonical_defaults=_defaults(),
    )

    assert isinstance(migration, LegacyStateMigration)
    assert isinstance(migration.warnings[0], StateMigrationWarning)
    with pytest.raises(FrozenInstanceError):
        migration.consumed_fields = ()
    with pytest.raises(FrozenInstanceError):
        migration.warnings[0].code = "changed"


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
def test_versioned_documents_are_not_legacy_input(
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


@pytest.mark.parametrize("legacy", [None, [], "state", 42])
def test_legacy_state_must_be_a_mapping(legacy: object) -> None:
    with pytest.raises(
        StateMigrationError,
        match="must be a JSON object",
    ):
        migrate_legacy_state(
            cast(Any, legacy),
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


def test_canonical_defaults_must_be_a_mapping() -> None:
    with pytest.raises(
        StateMigrationError,
        match="must be a JSON object",
    ):
        migrate_legacy_state(
            {},
            canonical_defaults=cast(Any, []),
        )


@pytest.mark.parametrize("limit", [True, False, 1.5, "32", None])
def test_status_message_limit_requires_integer(limit: object) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        migrate_legacy_state(
            {},
            canonical_defaults=_defaults(),
            status_message_limit=cast(int, limit),
        )


@pytest.mark.parametrize("limit", [0, -1, -100])
def test_status_message_limit_must_be_positive(limit: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        migrate_legacy_state(
            {},
            canonical_defaults=_defaults(),
            status_message_limit=limit,
        )
