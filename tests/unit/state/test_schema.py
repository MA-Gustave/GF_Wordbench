"""Unit tests for the canonical GF Wordbench application-state schema."""

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
from gf_wordbench.state import schema
from gf_wordbench.state.models import (
    AppState,
    EnvironmentState,
    LastRunState,
    SelectionState,
)
from gf_wordbench.state.schema import (
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
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

_EXPECTED_PUBLIC_NAMES = (
    "APP_STATE_FILENAME",
    "APP_STATE_SCHEMA_ID",
    "APP_STATE_SCHEMA_VERSION",
    "AppStateDocument",
    "CANONICAL_MODES",
    "EnvironmentDocument",
    "LEGACY_APP_STATE_FILENAME",
    "LastRunDocument",
    "MAX_STATE_WARNINGS",
    "ProducerDocument",
    "SelectionDocument",
    "StateSchemaResult",
    "StateSchemaWarning",
    "canonicalize_app_state_document",
    "default_app_state",
    "default_app_state_document",
    "parse_app_state",
    "producer_document",
    "recover_app_state_document",
    "serialize_app_state",
    "validate_app_state",
)

_BOOLEAN_FIELDS = (
    "keep_ok_details",
    "diff_previous",
    "skip_version_probe",
    "no_compile",
    "emit_cpu_stats",
)


def _persisted_document() -> dict[str, object]:
    document: dict[str, object] = deepcopy(default_app_state_document())
    document["producer"] = producer_document("1.2.3")
    return document


def _selection(document: dict[str, object]) -> dict[str, object]:
    selection = document["selection"]
    assert isinstance(selection, dict)
    return selection


def _environment(document: dict[str, object]) -> dict[str, object]:
    environment = document["environment"]
    assert isinstance(environment, dict)
    return environment


def test_schema_module_exposes_only_the_canonical_public_surface() -> None:
    assert schema.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(schema, name) for name in schema.__all__)


def test_schema_identity_defaults_and_warning_bound_are_stable() -> None:
    assert APP_STATE_SCHEMA_ID == "gf-wordbench.app-state"
    assert APP_STATE_SCHEMA_VERSION == "1.0"
    assert MAX_STATE_WARNINGS == 32
    assert schema.CANONICAL_MODES == frozenset(
        mode.value for mode in ValidationMode
    )


def test_default_state_is_fresh_immutable_and_disposable() -> None:
    first = default_app_state()
    second = default_app_state()

    assert first == second
    assert first is not second
    assert first.environment is not second.environment
    assert first.selection is not second.selection
    assert first.last_run is not second.last_run
    assert first.producer is None
    assert first.selection.mode is ValidationMode.DIAGNOSTIC
    assert first.selection.timeout_sec == 60
    assert first.selection.max_files == 0
    assert first.environment == EnvironmentState(None, None, None, None)
    assert first.last_run == LastRunState(None, None, "")

    with pytest.raises(AttributeError):
        first.schema_id = "changed"  # type: ignore[misc]


def test_default_document_is_fresh_and_contains_no_producer_metadata() -> None:
    first = default_app_state_document()
    second = default_app_state_document()

    assert first == second
    assert first is not second
    assert first["environment"] is not second["environment"]
    assert first["selection"] is not second["selection"]
    assert first["last_run"] is not second["last_run"]
    assert "producer" not in first

    first["selection"]["mode"] = "quick"
    assert second["selection"]["mode"] == "diagnostic"


@pytest.mark.parametrize(
    ("document", "exception_type", "message"),
    (
        ([], SchemaValidationError, r"\$: expected a JSON object"),
        (
            {"schema_id": "wrong", "schema_version": "1.0"},
            SchemaValidationError,
            r"\$\.schema_id: state identity is unsupported",
        ),
        (
            {"schema_id": APP_STATE_SCHEMA_ID},
            SchemaValidationError,
            r"\$\.schema_version: expected MAJOR.MINOR",
        ),
        (
            {
                "schema_id": APP_STATE_SCHEMA_ID,
                "schema_version": "01.0",
            },
            SchemaValidationError,
            r"\$\.schema_version: expected MAJOR.MINOR",
        ),
        (
            {
                "schema_id": APP_STATE_SCHEMA_ID,
                "schema_version": "2.0",
            },
            UnsupportedVersionError,
            r"schema major 2 is unsupported",
        ),
    ),
)
def test_tolerant_parse_reports_incompatible_documents(
    document: object,
    exception_type: type[Exception],
    message: str,
    tmp_path: Path,
) -> None:
    source = tmp_path / ".gf_wordbench_state.json"

    with pytest.raises(exception_type, match=message) as caught:
        parse_app_state(document, source=source)

    assert str(caught.value).startswith(f"{source}: ")


def test_tolerant_parse_ignores_unknown_fields_and_does_not_reemit_them() -> None:
    document = _persisted_document()
    document["project_id"] = "forbidden-owner"
    _environment(document)["machine_note"] = "ignored"
    _selection(document)["legacy_mode"] = "file"

    state, warnings = parse_app_state(document)
    serialized = serialize_app_state(state)

    assert warnings == ()
    assert "project_id" not in serialized
    assert "machine_note" not in serialized["environment"]
    assert "legacy_mode" not in serialized["selection"]


@pytest.mark.parametrize(
    "producer",
    (
        None,
        [],
        {"name": "other", "version": "1.0"},
        {"name": "gf-wordbench", "version": ""},
        {"name": "gf-wordbench", "version": "1.0\x00bad"},
    ),
)
def test_invalid_optional_producer_is_ignored_during_recovery(
    producer: object,
) -> None:
    document = default_app_state_document()
    document["producer"] = producer  # type: ignore[typeddict-item]

    result = recover_app_state_document(document)
    state, warnings = parse_app_state(document)

    assert result.compatible is True
    assert result.rewrite_safe is True
    assert "producer" not in result.document
    assert state.producer is None
    assert warnings
    assert any("producer" in warning for warning in warnings)


@pytest.mark.parametrize(
    ("value", "expected", "warning_code"),
    (
        (None, None, None),
        ("", None, None),
        (r"C:\work\GF Wordbench", "C:/work/GF Wordbench", "normalized_path"),
        ("~/workspace", None, "invalid_path"),
        ("${HOME}/workspace", None, "invalid_path"),
        (r"%USERPROFILE%\workspace", None, "invalid_path"),
        ("prefix\x00suffix", None, "invalid_path"),
        (42, None, "invalid_path"),
    ),
)
def test_environment_path_recovery_is_safe_and_portable(
    value: object,
    expected: str | None,
    warning_code: str | None,
) -> None:
    document = default_app_state_document()
    _environment(document)["project_root"] = value

    result = recover_app_state_document(document)

    assert result.document["environment"]["project_root"] == expected
    codes = {warning.code for warning in result.warnings}
    if warning_code is None:
        assert not codes
    else:
        assert warning_code in codes


@pytest.mark.parametrize(
    ("value", "expected", "warning_code"),
    (
        ("", "", None),
        (r"src\Grammar.gf", "src/Grammar.gf", "normalized_path"),
        ("~/Grammar.gf", "", "invalid_path"),
        ("$HOME/Grammar.gf", "", "invalid_path"),
        (False, "", "invalid_path"),
    ),
)
def test_target_path_recovery_is_safe_and_portable(
    value: object,
    expected: str,
    warning_code: str | None,
) -> None:
    document = default_app_state_document()
    _selection(document)["target_file"] = value

    result = recover_app_state_document(document)

    assert result.document["selection"]["target_file"] == expected
    codes = {warning.code for warning in result.warnings}
    if warning_code is None:
        assert not codes
    else:
        assert warning_code in codes


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    (
        ("timeout_sec", 1, 1),
        ("timeout_sec", 0, 60),
        ("timeout_sec", -1, 60),
        ("timeout_sec", "30", 60),
        ("timeout_sec", True, 60),
        ("max_files", 0, 0),
        ("max_files", 5, 5),
        ("max_files", -1, 0),
        ("max_files", "5", 0),
        ("max_files", False, 0),
    ),
)
def test_integer_preferences_require_exact_integer_types_and_bounds(
    field: str,
    value: object,
    expected: int,
) -> None:
    document = default_app_state_document()
    _selection(document)[field] = value

    result = recover_app_state_document(document)

    assert result.document["selection"][field] == expected
    invalid = not (
        type(value) is int
        and (
            value > 0
            if field == "timeout_sec"
            else value >= 0
        )
    )
    assert any(
        warning.code == "invalid_integer" and warning.field.endswith(field)
        for warning in result.warnings
    ) is invalid


@pytest.mark.parametrize("field", _BOOLEAN_FIELDS)
@pytest.mark.parametrize(
    ("value", "is_valid"),
    ((True, True), (False, True), (1, False), (0, False), ("true", False)),
)
def test_boolean_preferences_accept_only_json_booleans(
    field: str,
    value: object,
    is_valid: bool,
) -> None:
    document = default_app_state_document()
    selection = _selection(document)
    default = selection[field]
    selection[field] = value

    result = recover_app_state_document(document)

    assert result.document["selection"][field] == (
        value if is_valid else default
    )
    assert any(
        warning.code == "invalid_boolean" and warning.field.endswith(field)
        for warning in result.warnings
    ) is (not is_valid)


def test_missing_or_malformed_groups_default_every_known_field() -> None:
    document: dict[str, object] = {
        "schema_id": APP_STATE_SCHEMA_ID,
        "schema_version": APP_STATE_SCHEMA_VERSION,
        "environment": [],
        "selection": "invalid",
    }

    result = recover_app_state_document(document)

    assert result.compatible is True
    assert result.rewrite_safe is True
    assert result.document == default_app_state_document()
    fields = {warning.field for warning in result.warnings}
    assert "$.environment" in fields
    assert "$.selection" in fields
    assert "$.last_run" in fields
    assert len(result.warnings) <= MAX_STATE_WARNINGS


def test_future_minor_recovers_known_fields_but_blocks_automatic_rewrite() -> None:
    document = default_app_state_document()
    document["schema_version"] = "1.999"
    _selection(document)["mode"] = "release"

    result = recover_app_state_document(document)
    state, warnings = parse_app_state(document)

    assert result.compatible is True
    assert result.rewrite_safe is False
    assert result.source_schema_version == "1.999"
    assert result.document["schema_version"] == APP_STATE_SCHEMA_VERSION
    assert state.selection.mode is ValidationMode.RELEASE
    assert warnings == (
        "$.schema_version: known fields were recovered; automatic rewrite is unsafe",
    )


def test_strict_parser_requires_exact_nested_shapes() -> None:
    unknown = _persisted_document()
    _selection(unknown)["extra"] = True
    with pytest.raises(
        SchemaValidationError,
        match=r"\$\.selection: unknown fields: extra",
    ):
        parse_app_state(unknown, strict=True)

    missing = _persisted_document()
    del _environment(missing)["rgl_root"]
    with pytest.raises(
        SchemaValidationError,
        match=r"\$\.environment: missing required fields: rgl_root",
    ):
        canonicalize_app_state_document(missing)

    wrong_type = _persisted_document()
    wrong_type["last_run"] = []
    with pytest.raises(
        SchemaValidationError,
        match=r"\$\.last_run: must be an object with string keys",
    ):
        canonicalize_app_state_document(wrong_type)


def test_strict_schema_distinguishes_future_minor_and_major_versions() -> None:
    future_minor = _persisted_document()
    future_minor["schema_version"] = "1.1"
    with pytest.raises(
        SchemaValidationError,
        match=r"\$\.schema_version: must be '1.0'",
    ):
        canonicalize_app_state_document(future_minor)

    future_major = _persisted_document()
    future_major["schema_version"] = "2.0"
    with pytest.raises(
        UnsupportedVersionError,
        match=r"\$\.schema_version: schema major 2 is unsupported",
    ):
        canonicalize_app_state_document(future_major)


def test_producer_document_uses_the_shared_producer_model() -> None:
    assert producer_document("4.5.6") == {
        "name": "gf-wordbench",
        "version": "4.5.6",
    }

    with pytest.raises(ValueError, match="version must not be empty"):
        producer_document(" ")
    with pytest.raises(ValueError, match="version must not contain NUL"):
        producer_document("1.0\x00bad")
    with pytest.raises(TypeError, match="version must be a string"):
        producer_document(1)  # type: ignore[arg-type]


def test_serialization_normalizes_paths_and_producer_override_wins() -> None:
    state = replace(
        default_app_state(),
        producer=ProducerInfo(name="gf-wordbench", version="old"),
        environment=EnvironmentState(
            project_root=r"C:\workspace\GF Wordbench",
            rgl_root=None,
            gf_executable=r"C:\Program Files\GF\gf.exe",
            output_root=r"D:\runs",
        ),
        selection=replace(
            default_app_state().selection,
            mode=ValidationMode.QUICK,
            target_file=r"src\Grammar.gf",
        ),
        last_run=LastRunState(
            run_dir=r"D:\runs\run_20260725_120000",
            summary_path=r"D:\runs\run_20260725_120000\summary.json",
            status_message="Terminé — 日本語",
        ),
    )

    document = serialize_app_state(state, producer_version="new")

    assert document["producer"] == {
        "name": "gf-wordbench",
        "version": "new",
    }
    assert document["environment"] == {
        "project_root": "C:/workspace/GF Wordbench",
        "rgl_root": None,
        "gf_executable": "C:/Program Files/GF/gf.exe",
        "output_root": "D:/runs",
    }
    assert document["selection"]["target_file"] == "src/Grammar.gf"
    assert document["last_run"]["summary_path"] == (
        "D:/runs/run_20260725_120000/summary.json"
    )
    assert document["last_run"]["status_message"] == "Terminé — 日本語"


def test_serialization_rejects_wrong_producer_and_unsafe_paths() -> None:
    wrong_producer = replace(
        default_app_state(),
        producer=ProducerInfo(name="other", version="1.0"),
    )
    with pytest.raises(
        SchemaValidationError,
        match=r"\$\.producer: producer was ignored",
    ):
        serialize_app_state(wrong_producer)

    unsafe_path = replace(
        default_app_state(),
        environment=EnvironmentState(
            project_root="${HOME}/workspace",
            rgl_root=None,
            gf_executable=None,
            output_root=None,
        ),
    )
    with pytest.raises(
        SchemaValidationError,
        match="state contains an unsafe path value",
    ):
        serialize_app_state(unsafe_path, producer_version="1.0")


def test_validate_app_state_checks_type_and_persisted_producer_requirement() -> None:
    with pytest.raises(TypeError, match="state must be an AppState"):
        validate_app_state(object())  # type: ignore[arg-type]

    state = default_app_state()
    validate_app_state(state)

    with pytest.raises(
        SchemaValidationError,
        match=r"\$: missing required fields: producer",
    ):
        validate_app_state(state, require_producer=True)

    persisted = replace(
        state,
        producer=ProducerInfo(name="gf-wordbench", version="1.0"),
    )
    validate_app_state(persisted, require_producer=True)


def test_strict_error_messages_include_the_declared_source_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "state with spaces.json"
    document = _persisted_document()
    _selection(document)["timeout_sec"] = 0

    with pytest.raises(SchemaValidationError) as caught:
        canonicalize_app_state_document(document, source=source)

    assert str(caught.value) == (
        f"{source}: $.selection.timeout_sec: defaulted to 60"
    )
