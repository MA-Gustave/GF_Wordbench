"""Unit tests for canonical GF Wordbench identifier contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

import pytest

from gf_wordbench.kernel import ids
from gf_wordbench.kernel.ids import (
    ContractId,
    DiagnosticPatternId,
    ErrorCode,
    MigrationId,
    NormalizationProfileId,
    ProjectId,
    RunId,
    ScenarioId,
    SchemaId,
    SectionId,
    validate_contract_id,
    validate_diagnostic_pattern_id,
    validate_error_code,
    validate_migration_id,
    validate_normalization_profile_id,
    validate_project_id,
    validate_run_id,
    validate_scenario_id,
    validate_schema_id,
    validate_section_id,
)

IdentifierValidator = Callable[..., str]

_EXPECTED_EXPORTS: Final = (
    "ContractId",
    "DiagnosticPatternId",
    "ErrorCode",
    "MigrationId",
    "NormalizationProfileId",
    "ProjectId",
    "RunId",
    "ScenarioId",
    "SchemaId",
    "SectionId",
    "validate_contract_id",
    "validate_diagnostic_pattern_id",
    "validate_error_code",
    "validate_migration_id",
    "validate_normalization_profile_id",
    "validate_project_id",
    "validate_run_id",
    "validate_scenario_id",
    "validate_schema_id",
    "validate_section_id",
)

_KEBAB_VALIDATORS: Final[tuple[tuple[IdentifierValidator, str], ...]] = (
    (validate_project_id, "project ID"),
    (validate_scenario_id, "scenario ID"),
    (validate_section_id, "section ID"),
    (validate_normalization_profile_id, "normalization profile ID"),
)

_ALL_VALIDATORS: Final[tuple[IdentifierValidator, ...]] = (
    validate_project_id,
    validate_run_id,
    validate_scenario_id,
    validate_section_id,
    validate_normalization_profile_id,
    validate_schema_id,
    validate_contract_id,
    validate_migration_id,
    validate_error_code,
    validate_diagnostic_pattern_id,
)

_ERROR_DOMAINS: Final = (
    "CONFIG",
    "CONTRACT",
    "GF",
    "GOLD",
    "INTERNAL",
    "IO",
    "MANIFEST",
    "MIGRATION",
    "PATH",
    "PROCESS",
    "PROJECT",
    "REPORT",
    "SCAN",
    "SCENARIO",
    "SCHEMA",
    "STATE",
)

_DIAGNOSTIC_DOMAINS: Final = (
    "SYNTAX",
    "TYPE",
    "INTERNAL",
    "SCRIPT",
    "TOOL",
    "WARNING",
    "LOCATION",
    "CONTEXT",
)


def test_public_api_is_exact_and_owner_module_is_explicit() -> None:
    assert ids.__all__ == _EXPECTED_EXPORTS
    assert set(vars(ids)).issuperset(_EXPECTED_EXPORTS)


@pytest.mark.parametrize(
    ("alias", "expected_name"),
    [
        (ProjectId, "ProjectId"),
        (RunId, "RunId"),
        (ScenarioId, "ScenarioId"),
        (SectionId, "SectionId"),
        (NormalizationProfileId, "NormalizationProfileId"),
        (SchemaId, "SchemaId"),
        (ContractId, "ContractId"),
        (MigrationId, "MigrationId"),
        (ErrorCode, "ErrorCode"),
        (DiagnosticPatternId, "DiagnosticPatternId"),
    ],
)
def test_identifier_aliases_are_string_newtypes(
    alias: Any,
    expected_name: str,
) -> None:
    assert alias.__name__ == expected_name
    assert alias.__supertype__ is str
    assert alias("canonical-id") == "canonical-id"
    assert type(alias("canonical-id")) is str


@pytest.mark.parametrize(
    "value",
    [
        "a",
        "a0",
        "alpha",
        "alpha-0",
        "alpha-beta",
        "a1-b2-c3",
    ],
)
@pytest.mark.parametrize(("validator", "field"), _KEBAB_VALIDATORS)
def test_kebab_identifiers_accept_only_canonical_values(
    validator: IdentifierValidator,
    field: str,
    value: str,
) -> None:
    result = validator(value)

    assert result == value
    assert result is value
    assert type(result) is str
    assert field not in result


@pytest.mark.parametrize(
    "value",
    [
        "0alpha",
        "Alpha",
        "alpha_Beta",
        "alpha_beta",
        "alpha.beta",
        "alpha/beta",
        r"alpha\beta",
        "alpha--beta",
        "-alpha",
        "alpha-",
        " alpha",
        "alpha ",
        "alpha beta",
    ],
)
@pytest.mark.parametrize(("validator", "field"), _KEBAB_VALIDATORS)
def test_kebab_identifiers_reject_noncanonical_values(
    validator: IdentifierValidator,
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValueError) as captured:
        validator(value)

    message = str(captured.value)
    assert field in message
    assert repr(value) in message
    assert "Expected" in message
    assert "for example" in message


@pytest.mark.parametrize(
    "value",
    [
        "gf-wordbench.run-summary",
        "gf-wordbench.artifact-manifest",
        "gf-wordbench.validation.scenario-output",
        "gf-wordbench.a0.b1-c2",
    ],
)
def test_schema_ids_accept_canonical_dotted_names(value: str) -> None:
    result = validate_schema_id(value)

    assert result == value
    assert result is value


@pytest.mark.parametrize(
    "value",
    [
        "gf-wordbench",
        "gf-wordbench.",
        "gf-wordbench..run-summary",
        "gf-wordbench.Run-summary",
        "gf-wordbench.run_summary",
        "gf-wordbench.0summary",
        "GF-WORDBENCH.run-summary",
        "gf-audit.run-summary",
        "run-summary",
    ],
)
def test_schema_ids_reject_noncanonical_names(value: str) -> None:
    with pytest.raises(ValueError, match="schema ID"):
        validate_schema_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "IFC-WB-001",
        "PIFC-PROJECT-999",
        "EXT-GF2-123",
    ],
)
def test_contract_ids_accept_supported_prefixes(value: str) -> None:
    assert validate_contract_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "IFC-WB-01",
        "IFC-WB-0001",
        "IFC-WB2-A01",
        "IFC-WB-ABC",
        "IFC-WB-001-extra",
        "IFC-WORD-BENCH-001",
        "MIG-WB-001",
        "ifc-WB-001",
        "IFC-wb-001",
    ],
)
def test_contract_ids_reject_invalid_shape(value: str) -> None:
    with pytest.raises(ValueError, match="contract ID"):
        validate_contract_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "MIG-STATE-001",
        "MIG-PROJECT2-999",
        "MIG-A-123",
    ],
)
def test_migration_ids_accept_canonical_shape(value: str) -> None:
    assert validate_migration_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "MIG-STATE-01",
        "MIG-STATE-0001",
        "MIG-STATE-V2-001",
        "MIG-state-001",
        "MIG-1STATE-001",
        "IFC-STATE-001",
    ],
)
def test_migration_ids_reject_invalid_shape(value: str) -> None:
    with pytest.raises(ValueError, match="migration ID"):
        validate_migration_id(value)


@pytest.mark.parametrize("domain", _ERROR_DOMAINS)
def test_error_codes_accept_every_canonical_domain(domain: str) -> None:
    value = f"GF-WB-{domain}-001"

    assert validate_error_code(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "GF-WB-UNKNOWN-001",
        "GF-WB-PROCESS-01",
        "GF-WB-PROCESS-0001",
        "GF-WB-PROCESS-V2-001",
        "GF-WB-process-001",
        "GF-PROCESS-001",
        "GF-WB-1PROCESS-001",
    ],
)
def test_error_codes_reject_unknown_domains_and_invalid_shape(value: str) -> None:
    with pytest.raises(ValueError, match="error code"):
        validate_error_code(value)


def test_unknown_error_domain_reports_the_closed_domain_set() -> None:
    with pytest.raises(ValueError) as captured:
        validate_error_code("GF-WB-UNKNOWN-001")

    message = str(captured.value)
    assert "unsupported domain 'UNKNOWN'" in message
    for domain in _ERROR_DOMAINS:
        assert domain in message


@pytest.mark.parametrize("domain", _DIAGNOSTIC_DOMAINS)
def test_diagnostic_pattern_ids_accept_every_canonical_domain(
    domain: str,
) -> None:
    value = f"GF-DIAG-{domain}-001"

    assert validate_diagnostic_pattern_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "GF-DIAG-UNKNOWN-001",
        "GF-DIAG-SYNTAX-01",
        "GF-DIAG-SYNTAX-0001",
        "GF-DIAG-SYNTAX-V2-001",
        "GF-DIAG-syntax-001",
        "GF-WB-SYNTAX-001",
    ],
)
def test_diagnostic_pattern_ids_reject_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="diagnostic pattern ID"):
        validate_diagnostic_pattern_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "20260101_000000",
        "20260228_235959",
        "20260228_235959_02",
        "20260228_235959_09",
        "20260228_235959_10",
        "20260228_235959_99",
        "20260228_235959_100",
        "20240229_120000",
    ],
)
def test_run_ids_accept_valid_utc_timestamps_and_collision_suffixes(
    value: str,
) -> None:
    result = validate_run_id(value)

    assert result == value
    assert result is value


@pytest.mark.parametrize(
    "value",
    [
        "20260229_120000",
        "20261301_000000",
        "20260001_000000",
        "20260132_000000",
        "20260101_240000",
        "20260101_236000",
        "20260101_235960",
    ],
)
def test_run_ids_reject_impossible_dates_and_times(value: str) -> None:
    with pytest.raises(ValueError) as captured:
        validate_run_id(value)

    assert "timestamp component is not a valid UTC date and time" in str(captured.value)


@pytest.mark.parametrize(
    "value",
    [
        "20260101",
        "20260101-000000",
        "2026-01-01_000000",
        "20260101_00000",
        "20260101_000000_00",
        "20260101_000000_01",
        "20260101_000000_2",
        "20260101_000000_002",
        "20260101_000000_extra",
    ],
)
def test_run_ids_reject_noncanonical_shape(value: str) -> None:
    with pytest.raises(ValueError) as captured:
        validate_run_id(value)

    message = str(captured.value)
    assert "run ID" in message
    assert "YYYYMMDD_HHMMSS" in message
    assert "_02" in message


@pytest.mark.parametrize("validator", _ALL_VALIDATORS)
@pytest.mark.parametrize("value", [None, 1, 1.5, True, b"identifier", object()])
def test_all_validators_reject_non_strings(
    validator: IdentifierValidator,
    value: object,
) -> None:
    with pytest.raises(TypeError) as captured:
        validator(value)

    message = str(captured.value)
    assert "must be a string" in message
    assert type(value).__name__ in message


@pytest.mark.parametrize("validator", _ALL_VALIDATORS)
def test_all_validators_reject_empty_values(
    validator: IdentifierValidator,
) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validator("")


@pytest.mark.parametrize("validator", _ALL_VALIDATORS)
def test_all_validators_reject_nul(
    validator: IdentifierValidator,
) -> None:
    with pytest.raises(ValueError, match="NUL is prohibited"):
        validator("valid\x00identifier")


@pytest.mark.parametrize("validator", _ALL_VALIDATORS)
def test_all_validators_reject_non_ascii_input(
    validator: IdentifierValidator,
) -> None:
    with pytest.raises(ValueError, match="ASCII only"):
        validator("café")


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_project_id, " Example-Language "),
        (validate_scenario_id, "Parse-Basic"),
        (validate_section_id, "load_main"),
        (validate_normalization_profile_id, "scenario.default"),
        (validate_schema_id, " GF-WORDBENCH.RUN-SUMMARY "),
        (validate_contract_id, "ifc-wb-001"),
        (validate_migration_id, "mig-state-001"),
        (validate_error_code, "gf-wb-process-001"),
        (validate_diagnostic_pattern_id, "gf-diag-syntax-001"),
        (validate_run_id, "20260101_000000_01"),
    ],
)
def test_public_identifiers_are_rejected_not_sanitized(
    validator: IdentifierValidator,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        validator(value)


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_project_id, "example-language"),
        (validate_scenario_id, "parse-basic"),
        (validate_section_id, "load-main"),
        (validate_normalization_profile_id, "scenario-default"),
        (validate_schema_id, "gf-wordbench.run-summary"),
        (validate_contract_id, "IFC-WB-001"),
        (validate_migration_id, "MIG-STATE-001"),
        (validate_error_code, "GF-WB-PROCESS-001"),
        (validate_diagnostic_pattern_id, "GF-DIAG-SYNTAX-001"),
        (validate_run_id, "20260725_190423"),
    ],
)
def test_custom_field_name_is_used_in_validation_errors(
    validator: IdentifierValidator,
    value: str,
) -> None:
    custom_field = "document.identifier"

    assert validator(value, field=custom_field) == value

    with pytest.raises(TypeError) as type_error:
        validator(7, field=custom_field)
    assert custom_field in str(type_error.value)

    with pytest.raises(ValueError) as nul_error:
        validator("valid\x00identifier", field=custom_field)
    assert custom_field in str(nul_error.value)
