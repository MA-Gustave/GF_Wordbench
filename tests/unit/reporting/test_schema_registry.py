"""Unit tests for the canonical persisted-schema registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError, replace
from types import MappingProxyType

import pytest

from gf_wordbench.reporting.schemas.registry import (
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_KEY,
    APP_STATE_SCHEMA_VERSION,
    ARTIFACT_MANIFEST_SCHEMA_ID,
    ARTIFACT_MANIFEST_SCHEMA_KEY,
    ARTIFACT_MANIFEST_SCHEMA_VERSION,
    CANONICAL_SCHEMA_DEFINITIONS,
    CANONICAL_SCHEMA_IDS,
    CANONICAL_SCHEMA_KEYS,
    LEGACY_SCHEMA_DEFINITIONS,
    MANIFEST_SCHEMA_ID,
    MANIFEST_SCHEMA_VERSION,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_KEY,
    PROJECT_SCHEMA_VERSION,
    RUN_SUMMARY_SCHEMA_ID,
    RUN_SUMMARY_SCHEMA_KEY,
    RUN_SUMMARY_SCHEMA_VERSION,
    SCENARIO_GOLD_SCHEMA_ID,
    SCENARIO_GOLD_SCHEMA_KEY,
    SCENARIO_GOLD_SCHEMA_VERSION,
    SCENARIO_OUTPUT_SCHEMA_ID,
    SCENARIO_OUTPUT_SCHEMA_KEY,
    SCENARIO_OUTPUT_SCHEMA_VERSION,
    SCHEMA_REGISTRY,
    SUMMARY_SCHEMA_ID,
    SUMMARY_SCHEMA_VERSION,
    LegacySchemaDefinition,
    SchemaCompatibility,
    SchemaContractClass,
    SchemaDefinition,
    SchemaFormat,
    SchemaKey,
    SchemaRegistry,
    SchemaResolution,
    SchemaSupportClass,
    SchemaVersion,
    current_schema,
    format_schema_key,
    get_schema,
    get_schema_definition,
    is_supported_schema,
    normalize_schema_id,
    normalize_schema_path,
    normalize_schema_path_pattern,
    parse_schema_key,
    parse_schema_version,
    require_readable_schema,
    require_writable_schema,
    resolve_schema,
    schema_identity_from_mapping,
    schema_path_matches,
    schema_registry_snapshot,
    supported_schema_versions,
    validate_schema_identity,
)

pytestmark = pytest.mark.schema

_EXPECTED_DEFINITIONS: dict[str, dict[str, object]] = {
    PROJECT_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.TOML,
        "path": "project/project.toml",
        "contract": SchemaContractClass.CANONICAL_ROOT,
        "writer": "projects.toml_adapter",
        "readers": (
            "projects.loader",
            "projects.validator",
            "config.resolver",
            "entrypoints",
            "schema_validator",
        ),
        "migration": "explicit",
        "newline": None,
    },
    APP_STATE_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.JSON,
        "path": ".gf_wordbench_state.json",
        "contract": SchemaContractClass.CANONICAL_ROOT,
        "writer": "state.repository",
        "readers": (
            "state.repository",
            "entrypoints.cli",
            "entrypoints.gui",
            "schema_validator",
        ),
        "migration": "required_when_imported",
        "newline": None,
    },
    RUN_SUMMARY_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.JSON,
        "path": "run_<run-id>/summary.json",
        "contract": SchemaContractClass.CANONICAL_ROOT,
        "writer": "reporting.summary.json_writer",
        "readers": (
            "validation.regression.loader",
            "entrypoints.cli",
            "entrypoints.gui",
            "validation.release",
            "reporting.publisher",
            "schema_validator",
            "external_read_only_consumers",
        ),
        "migration": "required_when_imported",
        "newline": None,
    },
    ARTIFACT_MANIFEST_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.JSON,
        "path": "run_<run-id>/manifest.json",
        "contract": SchemaContractClass.CANONICAL_ROOT,
        "writer": "reporting.manifest.builder",
        "readers": (
            "reporting.manifest.verifier",
            "entrypoints.gui",
            "runs.cleanup",
            "runs.archive",
            "reporting.publisher",
            "validation.release",
            "schema_validator",
        ),
        "migration": "not_applicable",
        "newline": None,
    },
    SCENARIO_OUTPUT_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.CANONICAL_TEXT,
        "path": "run_<run-id>/raw/scenarios/<scenario-id>.out",
        "contract": SchemaContractClass.CANONICAL_TEXT,
        "writer": "validation.scenarios.normalization",
        "readers": (
            "validation.scenarios.markers",
            "validation.scenarios.gold_compare",
            "reporting.details",
            "reporting.ai_packet",
            "schema_validator",
        ),
        "migration": "regenerate_or_explicit_import",
        "newline": "lf",
    },
    SCENARIO_GOLD_SCHEMA_ID: {
        "version": "1.0",
        "format": SchemaFormat.CANONICAL_TEXT,
        "path": "project/validation/gold/<scenario-id>.gold",
        "contract": SchemaContractClass.CANONICAL_TEXT,
        "writer": "validation.scenarios.gold_update",
        "readers": (
            "validation.scenarios.gold_compare",
            "validation.release",
            "project_review_tooling",
            "schema_validator",
        ),
        "migration": "explicit_review",
        "newline": "lf",
    },
}

_EXPECTED_LEGACY: dict[str, tuple[str, SchemaKey, str]] = {
    "gf-audit.state-legacy": (
        ".gf_audit_state.json",
        APP_STATE_SCHEMA_KEY,
        "import_and_migrate",
    ),
    "gf-audit.state-unversioned": (
        ".gf_audit_state.json",
        APP_STATE_SCHEMA_KEY,
        "read_legacy_fields_with_warnings",
    ),
    "gf-audit.run-summary-current": (
        "run_<run-id>/summary.json",
        RUN_SUMMARY_SCHEMA_KEY,
        "read_and_migrate_nested_summary",
    ),
    "gf-audit.run-summary-legacy": (
        "run_<run-id>/summary.json",
        RUN_SUMMARY_SCHEMA_KEY,
        "read_and_migrate_flat_summary",
    ),
}


def _definition(
    *,
    schema_id: str = "gf-wordbench.example",
    version: str = "1.0",
    path: str = "example/document.json",
    format_: SchemaFormat = SchemaFormat.JSON,
    contract: SchemaContractClass = SchemaContractClass.CANONICAL_ROOT,
    support: SchemaSupportClass = SchemaSupportClass.CANONICAL,
    newline: str | None = None,
    allow_same_major_read: bool = True,
) -> SchemaDefinition:
    return SchemaDefinition(
        schema_id=schema_id,
        version=SchemaVersion.parse(version),
        format=format_,
        canonical_path_pattern=path,
        contract_class=contract,
        support=support,
        writer_owner="reporting.example.writer",
        readers=("reporting.example.reader", "schema_validator"),
        allow_same_major_read=allow_same_major_read,
        migration_policy="explicit",
        newline=newline,
    )


def test_registry_contains_exact_canonical_schema_set() -> None:
    assert len(SCHEMA_REGISTRY) == 6
    assert set(SCHEMA_REGISTRY.schema_ids) == set(_EXPECTED_DEFINITIONS)
    assert SCHEMA_REGISTRY.definitions == tuple(SCHEMA_REGISTRY)
    assert tuple(
        sorted(
            CANONICAL_SCHEMA_DEFINITIONS,
            key=lambda definition: (definition.schema_id, definition.version),
        )
    ) == SCHEMA_REGISTRY.definitions
    assert CANONICAL_SCHEMA_IDS == SCHEMA_REGISTRY.schema_ids
    assert CANONICAL_SCHEMA_KEYS == tuple(
        definition.key for definition in SCHEMA_REGISTRY
    )
    assert SCHEMA_REGISTRY.qualified_ids == tuple(
        f"{schema_id}/1.0" for schema_id in sorted(_EXPECTED_DEFINITIONS)
    )


def test_canonical_schema_constants_and_aliases_are_locked() -> None:
    assert PROJECT_SCHEMA_ID == "gf-wordbench.project"
    assert APP_STATE_SCHEMA_ID == "gf-wordbench.app-state"
    assert RUN_SUMMARY_SCHEMA_ID == "gf-wordbench.run-summary"
    assert ARTIFACT_MANIFEST_SCHEMA_ID == "gf-wordbench.artifact-manifest"
    assert SCENARIO_OUTPUT_SCHEMA_ID == "gf-wordbench.scenario-output"
    assert SCENARIO_GOLD_SCHEMA_ID == "gf-wordbench.scenario-gold"

    assert {
        PROJECT_SCHEMA_VERSION,
        APP_STATE_SCHEMA_VERSION,
        RUN_SUMMARY_SCHEMA_VERSION,
        ARTIFACT_MANIFEST_SCHEMA_VERSION,
        SCENARIO_OUTPUT_SCHEMA_VERSION,
        SCENARIO_GOLD_SCHEMA_VERSION,
    } == {"1.0"}

    assert MANIFEST_SCHEMA_ID == ARTIFACT_MANIFEST_SCHEMA_ID
    assert MANIFEST_SCHEMA_VERSION == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert SUMMARY_SCHEMA_ID == RUN_SUMMARY_SCHEMA_ID
    assert SUMMARY_SCHEMA_VERSION == RUN_SUMMARY_SCHEMA_VERSION

    assert PROJECT_SCHEMA_KEY == SchemaKey(PROJECT_SCHEMA_ID, SchemaVersion(1, 0))
    assert APP_STATE_SCHEMA_KEY == SchemaKey(APP_STATE_SCHEMA_ID, SchemaVersion(1, 0))
    assert RUN_SUMMARY_SCHEMA_KEY == SchemaKey(
        RUN_SUMMARY_SCHEMA_ID,
        SchemaVersion(1, 0),
    )
    assert ARTIFACT_MANIFEST_SCHEMA_KEY == SchemaKey(
        ARTIFACT_MANIFEST_SCHEMA_ID,
        SchemaVersion(1, 0),
    )
    assert SCENARIO_OUTPUT_SCHEMA_KEY == SchemaKey(
        SCENARIO_OUTPUT_SCHEMA_ID,
        SchemaVersion(1, 0),
    )
    assert SCENARIO_GOLD_SCHEMA_KEY == SchemaKey(
        SCENARIO_GOLD_SCHEMA_ID,
        SchemaVersion(1, 0),
    )


@pytest.mark.parametrize("schema_id", sorted(_EXPECTED_DEFINITIONS))
def test_canonical_definition_matches_documented_contract(schema_id: str) -> None:
    expected = _EXPECTED_DEFINITIONS[schema_id]
    definition = SCHEMA_REGISTRY.get(schema_id)

    assert str(definition.version) == expected["version"]
    assert definition.format is expected["format"]
    assert definition.canonical_path_pattern == expected["path"]
    assert definition.contract_class is expected["contract"]
    assert definition.support is SchemaSupportClass.CANONICAL
    assert definition.writer_owner == expected["writer"]
    assert definition.readers == expected["readers"]
    assert definition.allow_same_major_read is True
    assert definition.migration_policy == expected["migration"]
    assert definition.encoding == "utf-8"
    assert definition.newline == expected["newline"]
    assert definition.key.schema_id == schema_id
    assert definition.qualified_id == f"{schema_id}/1.0"
    assert definition.machine_readable_root is (
        definition.contract_class is SchemaContractClass.CANONICAL_ROOT
    )


@pytest.mark.parametrize(
    ("schema_id", "path"),
    [
        (PROJECT_SCHEMA_ID, "project/project.toml"),
        (APP_STATE_SCHEMA_ID, ".gf_wordbench_state.json"),
        (RUN_SUMMARY_SCHEMA_ID, "run_20260725_120000/summary.json"),
        (ARTIFACT_MANIFEST_SCHEMA_ID, "run_20260725_120000/manifest.json"),
        (
            SCENARIO_OUTPUT_SCHEMA_ID,
            "run_20260725_120000/raw/scenarios/linearize-basic.out",
        ),
        (
            SCENARIO_GOLD_SCHEMA_ID,
            "project/validation/gold/linearize-basic.gold",
        ),
    ],
)
def test_registry_resolves_canonical_paths(schema_id: str, path: str) -> None:
    matches = SCHEMA_REGISTRY.find_by_path(path)

    assert tuple(definition.schema_id for definition in matches) == (schema_id,)
    assert matches[0].matches_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "run_20260725_120000/raw/scenarios/nested/name.out",
        "project/validation/gold/nested/name.gold",
        "run_20260725_120000/summary.md",
        "project/project.json",
    ],
)
def test_registry_does_not_overmatch_paths(path: str) -> None:
    assert SCHEMA_REGISTRY.find_by_path(path) == ()


def test_legacy_registry_is_exact_and_read_only() -> None:
    assert len(LEGACY_SCHEMA_DEFINITIONS) == 4
    assert SCHEMA_REGISTRY.legacy_definitions == tuple(
        sorted(LEGACY_SCHEMA_DEFINITIONS, key=lambda entry: entry.legacy_id)
    )

    observed = {
        entry.legacy_id: (
            entry.source_path_pattern,
            entry.replacement,
            entry.reader_policy,
        )
        for entry in LEGACY_SCHEMA_DEFINITIONS
    }
    assert observed == _EXPECTED_LEGACY
    assert all(
        entry.writer_policy == "never_write"
        and entry.support is SchemaSupportClass.LEGACY_READABLE
        for entry in LEGACY_SCHEMA_DEFINITIONS
    )


@pytest.mark.parametrize("legacy_id", sorted(_EXPECTED_LEGACY))
def test_legacy_resolution_is_readable_but_never_writable(legacy_id: str) -> None:
    read_resolution = SCHEMA_REGISTRY.resolve(legacy_id, None)
    write_resolution = SCHEMA_REGISTRY.resolve(legacy_id, None, for_write=True)

    assert read_resolution.compatibility is SchemaCompatibility.LEGACY_READABLE
    assert read_resolution.readable is True
    assert read_resolution.writable is False
    assert read_resolution.legacy is SCHEMA_REGISTRY.legacy(legacy_id)
    assert read_resolution.definition is None
    assert "read-only" in read_resolution.message
    assert str(read_resolution.legacy.replacement) in read_resolution.message

    assert write_resolution.compatibility is SchemaCompatibility.NOT_WRITABLE
    assert write_resolution.readable is False
    assert write_resolution.writable is False

    with pytest.raises(ValueError, match="read-only"):
        SCHEMA_REGISTRY.require_writable(legacy_id, None)


def test_legacy_path_lookup_can_return_multiple_historical_shapes() -> None:
    state_matches = SCHEMA_REGISTRY.find_legacy_by_path(".gf_audit_state.json")
    summary_matches = SCHEMA_REGISTRY.find_legacy_by_path(
        "run_20260725_120000/summary.json"
    )

    assert {entry.legacy_id for entry in state_matches} == {
        "gf-audit.state-legacy",
        "gf-audit.state-unversioned",
    }
    assert {entry.legacy_id for entry in summary_matches} == {
        "gf-audit.run-summary-current",
        "gf-audit.run-summary-legacy",
    }


def test_schema_version_is_strict_orderable_and_canonical() -> None:
    assert SchemaVersion.parse("0.0") == SchemaVersion(0, 0)
    assert SchemaVersion.parse("1.12") == SchemaVersion(1, 12)
    version = SchemaVersion(2, 3)
    assert SchemaVersion.parse(version) is version
    assert parse_schema_version("3.4") == SchemaVersion(3, 4)
    assert str(SchemaVersion(10, 2)) == "10.2"
    assert SchemaVersion(1, 9) < SchemaVersion(2, 0)
    assert SchemaVersion(1, 2).same_major("1.99") is True
    assert SchemaVersion(1, 2).same_major("2.0") is False


@pytest.mark.parametrize(
    "value",
    ["", " 1.0", "1.0 ", "1", "1.0.0", "01.0", "1.01", "v1.0", "-1.0"],
)
def test_schema_version_rejects_noncanonical_text(value: str) -> None:
    with pytest.raises(ValueError):
        SchemaVersion.parse(value)


@pytest.mark.parametrize("value", [1, 1.0, None, object()])
def test_schema_version_rejects_nontext_values(value: object) -> None:
    with pytest.raises(TypeError):
        SchemaVersion.parse(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("major", "minor", "error"),
    [
        (-1, 0, ValueError),
        (0, -1, ValueError),
        (True, 0, TypeError),
        (1, False, TypeError),
        (1.0, 0, TypeError),
    ],
)
def test_schema_version_components_are_nonnegative_integers(
    major: object,
    minor: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        SchemaVersion(major, minor)  # type: ignore[arg-type]


def test_schema_key_round_trips_all_supported_input_forms() -> None:
    expected = SchemaKey(PROJECT_SCHEMA_ID, SchemaVersion(1, 0))

    assert SchemaKey.parse(expected) is expected
    assert SchemaKey.parse((PROJECT_SCHEMA_ID, "1.0")) == expected
    assert SchemaKey.parse(f"{PROJECT_SCHEMA_ID}/1.0") == expected
    assert parse_schema_key(expected) is expected
    assert format_schema_key(PROJECT_SCHEMA_ID, "1.0") == str(expected)
    assert str(expected) == "gf-wordbench.project/1.0"


@pytest.mark.parametrize(
    "value",
    [
        "gf-wordbench.project",
        "/1.0",
        "gf-wordbench.project/",
        "gf-wordbench.project/v1",
        (PROJECT_SCHEMA_ID,),
        (PROJECT_SCHEMA_ID, "1.0", "extra"),
    ],
)
def test_schema_key_rejects_invalid_shapes(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        SchemaKey.parse(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        "gf-wordbench.project",
        "gf-wordbench.app-state",
        "gf-wordbench.run-summary",
        "gf-audit.state-legacy",
    ],
)
def test_schema_id_normalization_accepts_portable_ids(value: str) -> None:
    require_prefix = value.startswith("gf-wordbench.")
    assert normalize_schema_id(value, require_wordbench_prefix=require_prefix) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " gf-wordbench.project",
        "gf-wordbench.project ",
        "GF-Wordbench.project",
        "gf_wordbench.project",
        "gf-wordbench",
        "gf-wordbench..project",
        "gf-wordbench.projét",
        "gf-wordbench.project\x00",
    ],
)
def test_schema_id_normalization_rejects_invalid_ids(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_schema_id(value, require_wordbench_prefix=False)


def test_canonical_schema_id_requires_wordbench_prefix() -> None:
    with pytest.raises(ValueError, match="gf-wordbench"):
        normalize_schema_id("gf-audit.project")


def test_schema_path_normalization_is_portable_and_relative() -> None:
    assert normalize_schema_path(r"run_1\raw\scenarios\basic.out") == (
        "run_1/raw/scenarios/basic.out"
    )
    assert normalize_schema_path("project//validation/gold/basic.gold") == (
        "project/validation/gold/basic.gold"
    )
    assert normalize_schema_path_pattern(
        r"run_<run-id>\raw\scenarios\<scenario-id>.out"
    ) == "run_<run-id>/raw/scenarios/<scenario-id>.out"


@pytest.mark.parametrize(
    "value",
    [
        "",
        " project/project.toml",
        "project/project.toml ",
        "/project/project.toml",
        "../project/project.toml",
        "project/../project.toml",
        "C:/project/project.toml",
        r"C:\project\project.toml",
        r"\\server\share\project.toml",
        "project/project.toml\x00",
    ],
)
def test_schema_path_normalization_rejects_unsafe_paths(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_schema_path(value)


@pytest.mark.parametrize(
    "pattern",
    [
        "run_<Run-ID>/summary.json",
        "run_<run id>/summary.json",
        "run_<run-id/summary.json",
        "run_run-id>/summary.json",
        "run_<>/summary.json",
    ],
)
def test_schema_path_pattern_rejects_invalid_tokens(pattern: str) -> None:
    with pytest.raises(ValueError):
        normalize_schema_path_pattern(pattern)


def test_schema_path_matching_substitutes_one_segment_per_token() -> None:
    pattern = "run_<run-id>/raw/scenarios/<scenario-id>.out"

    assert schema_path_matches(
        pattern,
        "run_20260725_120000/raw/scenarios/linearize-basic.out",
    )
    assert schema_path_matches(
        pattern,
        r"run_20260725_120000\raw\scenarios\linearize-basic.out",
    )
    assert not schema_path_matches(
        pattern,
        "run_20260725_120000/raw/scenarios/nested/linearize-basic.out",
    )
    assert not schema_path_matches(
        pattern,
        "run_20260725_120000/raw/scenarios/.out",
    )


def test_exact_and_same_major_resolution_follow_read_write_policy() -> None:
    definition = SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID)
    exact = resolve_schema(PROJECT_SCHEMA_ID, "1.0")
    same_major = resolve_schema(PROJECT_SCHEMA_ID, "1.7")
    same_major_write = resolve_schema(PROJECT_SCHEMA_ID, "1.7", for_write=True)

    assert exact.compatibility is SchemaCompatibility.EXACT
    assert exact.readable is True
    assert exact.writable is True
    assert exact.definition is definition

    assert same_major.compatibility is SchemaCompatibility.SAME_MAJOR
    assert same_major.readable is True
    assert same_major.writable is False
    assert same_major.definition is definition
    assert "field-level compatibility" in same_major.message

    assert same_major_write.compatibility is SchemaCompatibility.NOT_WRITABLE
    assert same_major_write.readable is False
    assert same_major_write.writable is False
    assert "emits only" in same_major_write.message


def test_missing_unknown_and_incompatible_versions_are_classified() -> None:
    missing = resolve_schema(PROJECT_SCHEMA_ID, None)
    unknown = resolve_schema("gf-wordbench.unknown", "1.0")
    wrong_major = resolve_schema(PROJECT_SCHEMA_ID, "2.0")

    assert missing.compatibility is SchemaCompatibility.UNSUPPORTED_MINOR
    assert missing.readable is False
    assert missing.message == "schema_version is required"

    assert unknown.compatibility is SchemaCompatibility.UNSUPPORTED_SCHEMA
    assert unknown.definition is None
    assert "unsupported schema ID" in unknown.message

    assert wrong_major.compatibility is SchemaCompatibility.UNSUPPORTED_MAJOR
    assert wrong_major.definition is SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID)
    assert "supported major is 1" in wrong_major.message


def test_registry_can_disable_same_major_reading() -> None:
    definition = _definition(allow_same_major_read=False)
    registry = SchemaRegistry((definition,))

    resolution = registry.resolve(definition.schema_id, "1.1")

    assert resolution.compatibility is SchemaCompatibility.UNSUPPORTED_MINOR
    assert resolution.readable is False
    assert resolution.writable is False


def test_readable_and_writable_guards_return_typed_results() -> None:
    readable = require_readable_schema(RUN_SUMMARY_SCHEMA_ID, "1.9")
    writable = require_writable_schema(RUN_SUMMARY_SCHEMA_ID, "1.0")

    assert readable.compatibility is SchemaCompatibility.SAME_MAJOR
    assert readable.definition is SCHEMA_REGISTRY.get(RUN_SUMMARY_SCHEMA_ID)
    assert writable is SCHEMA_REGISTRY.get(RUN_SUMMARY_SCHEMA_ID)

    with pytest.raises(ValueError, match="unsupported major"):
        require_readable_schema(RUN_SUMMARY_SCHEMA_ID, "2.0")
    with pytest.raises(ValueError, match="emits only"):
        require_writable_schema(RUN_SUMMARY_SCHEMA_ID, "1.1")


def test_supported_schema_query_distinguishes_read_from_write() -> None:
    assert is_supported_schema(PROJECT_SCHEMA_ID, "1.0") is True
    assert is_supported_schema(PROJECT_SCHEMA_ID, "1.9") is True
    assert is_supported_schema(PROJECT_SCHEMA_ID, "1.9", for_write=True) is False
    assert is_supported_schema(PROJECT_SCHEMA_ID, "2.0") is False
    assert is_supported_schema("gf-wordbench.unknown", "1.0") is False


def test_public_lookup_helpers_delegate_to_single_registry() -> None:
    definition = SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID)

    assert get_schema_definition(PROJECT_SCHEMA_ID) is definition
    assert get_schema(PROJECT_SCHEMA_ID, "1.0") is definition
    assert current_schema(PROJECT_SCHEMA_ID) is definition
    assert supported_schema_versions(PROJECT_SCHEMA_ID) == (SchemaVersion(1, 0),)
    assert SCHEMA_REGISTRY.get_key(PROJECT_SCHEMA_KEY) is definition
    assert SCHEMA_REGISTRY.contains(PROJECT_SCHEMA_ID) is True
    assert SCHEMA_REGISTRY.contains(PROJECT_SCHEMA_ID, "1.0") is True
    assert SCHEMA_REGISTRY.contains(PROJECT_SCHEMA_ID, "2.0") is False
    assert SCHEMA_REGISTRY.contains("bad id", "1.0") is False


def test_unknown_registry_lookups_raise_precise_key_errors() -> None:
    with pytest.raises(KeyError, match="unknown schema ID"):
        SCHEMA_REGISTRY.get("gf-wordbench.unknown")
    with pytest.raises(KeyError, match="unknown schema version"):
        SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID, "1.1")
    with pytest.raises(KeyError, match="unknown legacy schema ID"):
        SCHEMA_REGISTRY.legacy("gf-audit.unknown")


def test_schema_identity_from_mapping_requires_string_identity_fields() -> None:
    document = {
        "schema_id": PROJECT_SCHEMA_ID,
        "schema_version": PROJECT_SCHEMA_VERSION,
    }

    assert schema_identity_from_mapping(document) == PROJECT_SCHEMA_KEY

    with pytest.raises(TypeError, match="mapping"):
        schema_identity_from_mapping([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing schema_id"):
        schema_identity_from_mapping({"schema_version": "1.0"})
    with pytest.raises(ValueError, match="missing schema_version"):
        schema_identity_from_mapping({"schema_id": PROJECT_SCHEMA_ID})
    with pytest.raises(TypeError, match="schema_id"):
        schema_identity_from_mapping({"schema_id": 1, "schema_version": "1.0"})
    with pytest.raises(TypeError, match="schema_version"):
        schema_identity_from_mapping({"schema_id": PROJECT_SCHEMA_ID, "schema_version": 1})


def test_validate_schema_identity_enforces_expected_id_and_access_mode() -> None:
    exact_document: Mapping[str, object] = {
        "schema_id": PROJECT_SCHEMA_ID,
        "schema_version": "1.0",
    }
    same_major_document: Mapping[str, object] = {
        "schema_id": PROJECT_SCHEMA_ID,
        "schema_version": "1.8",
    }

    exact = validate_schema_identity(
        exact_document,
        expected_schema_id=PROJECT_SCHEMA_ID,
        for_write=True,
    )
    same_major = validate_schema_identity(same_major_document)

    assert exact.compatibility is SchemaCompatibility.EXACT
    assert exact.writable is True
    assert same_major.compatibility is SchemaCompatibility.SAME_MAJOR
    assert same_major.readable is True

    with pytest.raises(ValueError, match="wrong schema_id"):
        validate_schema_identity(
            exact_document,
            expected_schema_id=RUN_SUMMARY_SCHEMA_ID,
        )
    with pytest.raises(ValueError, match="emits only"):
        validate_schema_identity(same_major_document, for_write=True)


def test_registry_snapshot_is_read_only_and_stable() -> None:
    snapshot = schema_registry_snapshot()

    assert isinstance(snapshot, MappingProxyType)
    assert tuple(snapshot) == SCHEMA_REGISTRY.qualified_ids
    assert snapshot[str(PROJECT_SCHEMA_KEY)] is SCHEMA_REGISTRY.get(
        PROJECT_SCHEMA_ID
    )

    with pytest.raises(TypeError):
        snapshot["gf-wordbench.extra/1.0"] = _definition()  # type: ignore[index]


def test_definitions_keys_and_resolutions_are_immutable() -> None:
    definition = SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID)
    key = definition.key
    resolution = resolve_schema(PROJECT_SCHEMA_ID, "1.0")

    with pytest.raises(FrozenInstanceError):
        definition.schema_id = RUN_SUMMARY_SCHEMA_ID  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        key.schema_id = RUN_SUMMARY_SCHEMA_ID  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        resolution.message = "changed"  # type: ignore[misc]


def test_schema_definition_normalizes_supported_values() -> None:
    definition = SchemaDefinition(
        schema_id="gf-wordbench.example",
        version="1.0",  # type: ignore[arg-type]
        format=SchemaFormat.JSON,
        canonical_path_pattern=r"example\document.json",
        contract_class=SchemaContractClass.CANONICAL_ROOT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="reporting.example_writer",
        readers=("reporting.reader", "schema_validator"),
        allow_same_major_read=True,
        migration_policy="explicit",
        encoding="UTF_8",
    )

    assert definition.version == SchemaVersion(1, 0)
    assert definition.canonical_path_pattern == "example/document.json"
    assert definition.encoding == "utf-8"
    assert definition.newline is None


def test_schema_definition_enforces_contract_format_and_newline() -> None:
    with pytest.raises(ValueError, match="root schemas"):
        _definition(format_=SchemaFormat.CANONICAL_TEXT)
    with pytest.raises(ValueError, match="newline"):
        _definition(newline="lf")
    with pytest.raises(ValueError, match="canonical_text"):
        _definition(
            format_=SchemaFormat.JSON,
            contract=SchemaContractClass.CANONICAL_TEXT,
            newline="lf",
        )
    with pytest.raises(ValueError, match="LF"):
        _definition(
            format_=SchemaFormat.CANONICAL_TEXT,
            contract=SchemaContractClass.CANONICAL_TEXT,
        )


def test_schema_definition_rejects_noncanonical_support() -> None:
    with pytest.raises(ValueError, match="must be canonical"):
        _definition(support=SchemaSupportClass.DEPRECATED)


def test_schema_definition_rejects_invalid_owner_reader_and_policy_values() -> None:
    base = _definition()

    with pytest.raises(ValueError, match="writer_owner"):
        replace(base, writer_owner="Invalid Owner")
    with pytest.raises(TypeError, match="readers"):
        replace(base, readers="reporting.reader")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not be empty"):
        replace(base, readers=())
    with pytest.raises(ValueError, match="duplicates"):
        replace(base, readers=("schema_validator", "schema_validator"))
    with pytest.raises(ValueError, match="migration_policy"):
        replace(base, migration_policy=" explicit ")
    with pytest.raises(TypeError, match="boolean"):
        replace(base, allow_same_major_read=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="UTF-8"):
        replace(base, encoding="utf-16")


def test_legacy_definition_requires_valid_support_and_policy() -> None:
    entry = LegacySchemaDefinition(
        legacy_id="gf-audit.example",
        source_path_pattern="legacy/example.json",
        replacement=PROJECT_SCHEMA_KEY,
        reader_policy="import_and_migrate",
    )

    assert entry.writer_policy == "never_write"
    assert entry.support is SchemaSupportClass.LEGACY_READABLE
    assert entry.matches_path("legacy/example.json") is True

    with pytest.raises(ValueError, match="legacy entries"):
        replace(entry, support=SchemaSupportClass.CANONICAL)
    with pytest.raises(ValueError, match="reader_policy"):
        replace(entry, reader_policy="")


def test_registry_rejects_empty_duplicate_or_conflicting_definitions() -> None:
    first = _definition()
    duplicate = replace(first)
    same_path_other_id = _definition(schema_id="gf-wordbench.other")
    other_major = _definition(version="2.0")

    with pytest.raises(ValueError, match="at least one"):
        SchemaRegistry(())
    with pytest.raises(ValueError, match="duplicate schema definition"):
        SchemaRegistry((first, duplicate))
    with pytest.raises(ValueError, match="canonical schema path"):
        SchemaRegistry((first, same_path_other_id))
    with pytest.raises(ValueError, match="multiple active major"):
        SchemaRegistry((first, other_major))


def test_registry_allows_ordered_minor_versions_and_selects_current() -> None:
    version_10 = _definition(version="1.0")
    version_12 = _definition(version="1.2")
    registry = SchemaRegistry((version_12, version_10))

    assert registry.definitions == (version_10, version_12)
    assert registry.current(version_10.schema_id) is version_12
    assert registry.versions(version_10.schema_id) == (
        SchemaVersion(1, 0),
        SchemaVersion(1, 2),
    )
    assert registry.get(version_10.schema_id, "1.0") is version_10


def test_registry_rejects_invalid_legacy_entries() -> None:
    definition = _definition()
    valid = LegacySchemaDefinition(
        legacy_id="gf-audit.example",
        source_path_pattern="legacy/example.json",
        replacement=definition.key,
        reader_policy="import_and_migrate",
    )

    with pytest.raises(ValueError, match="duplicate legacy schema ID"):
        SchemaRegistry((definition,), (valid, valid))
    with pytest.raises(ValueError, match="must not collide"):
        SchemaRegistry(
            (definition,),
            (
                replace(valid, legacy_id=definition.schema_id),
            ),
        )
    with pytest.raises(ValueError, match="replacement is not present"):
        SchemaRegistry(
            (definition,),
            (
                replace(valid, replacement=PROJECT_SCHEMA_KEY),
            ),
        )


def test_schema_resolution_rejects_inconsistent_payloads() -> None:
    definition = SCHEMA_REGISTRY.get(PROJECT_SCHEMA_ID)
    legacy = SCHEMA_REGISTRY.legacy("gf-audit.state-legacy")

    with pytest.raises(ValueError, match="both canonical and legacy"):
        SchemaResolution(
            requested_id=PROJECT_SCHEMA_ID,
            requested_version=SchemaVersion(1, 0),
            compatibility=SchemaCompatibility.EXACT,
            definition=definition,
            legacy=legacy,
        )
    with pytest.raises(TypeError, match="compatibility"):
        SchemaResolution(
            requested_id=PROJECT_SCHEMA_ID,
            requested_version=SchemaVersion(1, 0),
            compatibility="exact",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="message"):
        SchemaResolution(
            requested_id=PROJECT_SCHEMA_ID,
            requested_version=SchemaVersion(1, 0),
            compatibility=SchemaCompatibility.EXACT,
            message=" invalid ",
        )
