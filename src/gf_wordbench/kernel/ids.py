"""Canonical identifier types and validation for GF Wordbench.

This module is the single runtime owner of shared identifier types and their
syntax. Public identifiers are accepted exactly or rejected; they are never
silently normalized.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Final, NewType

ProjectId = NewType("ProjectId", str)
RunId = NewType("RunId", str)
ScenarioId = NewType("ScenarioId", str)
SectionId = NewType("SectionId", str)
NormalizationProfileId = NewType("NormalizationProfileId", str)
SchemaId = NewType("SchemaId", str)
ContractId = NewType("ContractId", str)
MigrationId = NewType("MigrationId", str)
ErrorCode = NewType("ErrorCode", str)
DiagnosticPatternId = NewType("DiagnosticPatternId", str)

_KEBAB_ID_PATTERN_TEXT: Final = "[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
_KEBAB_ID_RE: Final[re.Pattern[str]] = re.compile(rf"^{_KEBAB_ID_PATTERN_TEXT}$")

_SCHEMA_COMPONENT: Final = _KEBAB_ID_PATTERN_TEXT
_SCHEMA_ID_RE: Final[re.Pattern[str]] = re.compile(
    rf"^gf-wordbench\.{_SCHEMA_COMPONENT}"
    rf"(?:\.{_SCHEMA_COMPONENT})*$"
)

_RUN_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<timestamp>[0-9]{8}_[0-9]{6})"
    r"(?:_(?P<collision>0[2-9]|[1-9][0-9]+))?$"
)

_CONTRACT_ID_RE: Final[re.Pattern[str]] = re.compile(r"^(?:IFC|PIFC|EXT)-[A-Z][A-Z0-9]*-[0-9]{3}$")
_MIGRATION_ID_RE: Final[re.Pattern[str]] = re.compile(r"^MIG-[A-Z][A-Z0-9]*-[0-9]{3}$")
_ERROR_CODE_RE: Final[re.Pattern[str]] = re.compile(r"^GF-WB-(?P<domain>[A-Z][A-Z0-9]*)-[0-9]{3}$")
_DIAGNOSTIC_PATTERN_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^GF-DIAG-"
    r"(?:SYNTAX|TYPE|INTERNAL|SCRIPT|TOOL|WARNING|LOCATION|CONTEXT)"
    r"-[0-9]{3}$"
)

_ERROR_CODE_DOMAINS: Final[frozenset[str]] = frozenset(
    {
        "CONFIG",
        "PROJECT",
        "PATH",
        "IO",
        "PROCESS",
        "GF",
        "SCAN",
        "SCENARIO",
        "GOLD",
        "SCHEMA",
        "REPORT",
        "MANIFEST",
        "STATE",
        "MIGRATION",
        "CONTRACT",
        "INTERNAL",
    }
)


def _require_string(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"Invalid {field} {value!r}: NUL is prohibited")
    if not value.isascii():
        raise ValueError(f"Invalid {field} {value!r}: identifiers must use ASCII only")
    return value


def _validate_pattern(
    value: object,
    *,
    field: str,
    pattern: re.Pattern[str],
    expected: str,
    example: str,
) -> str:
    candidate = _require_string(value, field=field)

    if pattern.fullmatch(candidate) is None:
        raise ValueError(
            f"Invalid {field} {candidate!r}. Expected {expected}; for example {example!r}"
        )

    return candidate


def _validate_kebab_id(
    value: object,
    *,
    field: str,
    example: str,
) -> str:
    return _validate_pattern(
        value,
        field=field,
        pattern=_KEBAB_ID_RE,
        expected=(f"lowercase kebab case matching {_KEBAB_ID_PATTERN_TEXT}"),
        example=example,
    )


def validate_project_id(
    value: object,
    *,
    field: str = "project ID",
) -> ProjectId:
    """Validate and type a canonical project identifier."""

    return ProjectId(
        _validate_kebab_id(
            value,
            field=field,
            example="example-language",
        )
    )


def validate_scenario_id(
    value: object,
    *,
    field: str = "scenario ID",
) -> ScenarioId:
    """Validate and type a canonical scenario identifier."""

    return ScenarioId(
        _validate_kebab_id(
            value,
            field=field,
            example="parse-basic",
        )
    )


def validate_section_id(
    value: object,
    *,
    field: str = "section ID",
) -> SectionId:
    """Validate and type a canonical scenario-section identifier."""

    return SectionId(
        _validate_kebab_id(
            value,
            field=field,
            example="load-main",
        )
    )


def validate_normalization_profile_id(
    value: object,
    *,
    field: str = "normalization profile ID",
) -> NormalizationProfileId:
    """Validate and type a stable normalization-profile identifier."""

    return NormalizationProfileId(
        _validate_kebab_id(
            value,
            field=field,
            example="scenario-default",
        )
    )


def validate_schema_id(
    value: object,
    *,
    field: str = "schema ID",
) -> SchemaId:
    """Validate and type a canonical persisted-schema identifier."""

    return SchemaId(
        _validate_pattern(
            value,
            field=field,
            pattern=_SCHEMA_ID_RE,
            expected=("a lowercase dotted identifier beginning with 'gf-wordbench.'"),
            example="gf-wordbench.run-summary",
        )
    )


def validate_contract_id(
    value: object,
    *,
    field: str = "contract ID",
) -> ContractId:
    """Validate and type a framework, project, or external contract ID."""

    return ContractId(
        _validate_pattern(
            value,
            field=field,
            pattern=_CONTRACT_ID_RE,
            expected=("IFC-, PIFC-, or EXT-, an uppercase domain, and a three-digit number"),
            example="IFC-WB-001",
        )
    )


def validate_migration_id(
    value: object,
    *,
    field: str = "migration ID",
) -> MigrationId:
    """Validate and type a canonical migration identifier."""

    return MigrationId(
        _validate_pattern(
            value,
            field=field,
            pattern=_MIGRATION_ID_RE,
            expected=("MIG-, an uppercase domain, and a three-digit number"),
            example="MIG-STATE-001",
        )
    )


def validate_error_code(
    value: object,
    *,
    field: str = "error code",
) -> ErrorCode:
    """Validate and type a canonical GF Wordbench error code."""

    candidate = _validate_pattern(
        value,
        field=field,
        pattern=_ERROR_CODE_RE,
        expected=("GF-WB-, a canonical uppercase domain, and a three-digit number"),
        example="GF-WB-PROCESS-001",
    )

    match = _ERROR_CODE_RE.fullmatch(candidate)
    if match is None:
        raise AssertionError("validated error code no longer matches its pattern")

    domain = match.group("domain")
    if domain not in _ERROR_CODE_DOMAINS:
        supported = ", ".join(sorted(_ERROR_CODE_DOMAINS))
        raise ValueError(
            f"Invalid {field} {candidate!r}: unsupported domain "
            f"{domain!r}; expected one of {supported}"
        )

    return ErrorCode(candidate)


def validate_diagnostic_pattern_id(
    value: object,
    *,
    field: str = "diagnostic pattern ID",
) -> DiagnosticPatternId:
    """Validate and type a canonical diagnostic-pattern identifier."""

    return DiagnosticPatternId(
        _validate_pattern(
            value,
            field=field,
            pattern=_DIAGNOSTIC_PATTERN_ID_RE,
            expected=("GF-DIAG-<DOMAIN>-<NNN> using a canonical diagnostic domain"),
            example="GF-DIAG-SYNTAX-001",
        )
    )


def validate_run_id(
    value: object,
    *,
    field: str = "run ID",
) -> RunId:
    """Validate and type a canonical UTC timestamp-based run identifier."""

    candidate = _validate_pattern(
        value,
        field=field,
        pattern=_RUN_ID_RE,
        expected=("YYYYMMDD_HHMMSS with an optional collision suffix beginning at _02"),
        example="20260724_145945_02",
    )

    match = _RUN_ID_RE.fullmatch(candidate)
    if match is None:
        raise AssertionError("validated run ID no longer matches its pattern")

    try:
        datetime.strptime(
            match.group("timestamp"),
            "%Y%m%d_%H%M%S",
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid {field} {candidate!r}: the timestamp component "
            "is not a valid UTC date and time"
        ) from exc

    return RunId(candidate)


__all__ = (
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
