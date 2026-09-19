from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum, unique
import re
from types import MappingProxyType
from typing import Final, NewType, TypeVar

from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

DIAGNOSTIC_VOCABULARY_VERSION: Final[str] = "1.0.0"
MAX_DIAGNOSTIC_CODE_LENGTH: Final[int] = 128
MAX_PATTERN_ID_LENGTH: Final[int] = 64

DiagnosticCode = NewType("DiagnosticCode", str)
DiagnosticPatternId = NewType("DiagnosticPatternId", str)

_EnumT = TypeVar("_EnumT", bound=StrEnum)

_DIAGNOSTIC_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_PATTERN_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^DP-(PROC|GFINT|GFTYPE|GFSYN|GFLOAD|GFGEN|GFWARN|SCEN|ART|NORM|GOLD|FALLBACK)-[0-9]{3,}$"
)


@unique
class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"
    UNKNOWN = "unknown"


@unique
class DiagnosticOperationKind(StrEnum):
    PROBE_VERSION = "probe_version"
    COMPILE_MODULE = "compile_module"
    BUILD_PGF = "build_pgf"
    RUN_SCENARIO = "run_scenario"
    INSPECT_GRAMMAR = "inspect_grammar"


@unique
class DiagnosticStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


@unique
class DiagnosticStreamScope(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    EITHER = "either"
    BOTH = "both"


@unique
class DiagnosticLineKind(StrEnum):
    DIAGNOSTIC_START = "diagnostic_start"
    DIAGNOSTIC_CONTINUATION = "diagnostic_continuation"
    CONTEXT = "context"
    KNOWN_NOISE = "known_noise"
    UNKNOWN = "unknown"


@unique
class PatternLifecycle(StrEnum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@unique
class PatternConfidence(StrEnum):
    """Canonical confidence vocabulary shared by pattern definitions and matches.

    The broader set preserves both the framework-evidence confidence levels
    (``authoritative``, ``high``, ``medium``, ``low``) and the parser matching
    levels (``exact``, ``strong``, ``fallback``, ``unknown``).  Keeping one enum
    avoids duplicate owners while remaining compatible with persisted pattern
    catalogs from both generations of the diagnostics API.
    """

    AUTHORITATIVE = "authoritative"
    EXACT = "exact"
    HIGH = "high"
    STRONG = "strong"
    MEDIUM = "medium"
    FALLBACK = "fallback"
    LOW = "low"
    UNKNOWN = "unknown"


@unique
class EvidenceConfidence(StrEnum):
    AUTHORITATIVE = "authoritative"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@unique
class PresentationConfidence(StrEnum):
    CONFIRMED = "confirmed"
    SUPPORTED = "supported"
    UNCERTAIN = "uncertain"


@unique
class DiagnosticOrigin(StrEnum):
    FRAMEWORK = "framework"
    GF = "gf"
    SCENARIO = "scenario"
    NORMALIZER = "normalizer"
    GOLD_COMPARATOR = "gold_comparator"
    ARTIFACT_VERIFIER = "artifact_verifier"
    FILESYSTEM = "filesystem"
    CONFIGURATION = "configuration"
    EXTERNAL_TOOL = "external_tool"


@unique
class PatternDomain(StrEnum):
    PROCESS = "PROC"
    GF_INTERNAL = "GFINT"
    GF_TYPE = "GFTYPE"
    GF_SYNTAX = "GFSYN"
    GF_LOAD = "GFLOAD"
    GF_GENERATION = "GFGEN"
    GF_WARNING = "GFWARN"
    SCENARIO = "SCEN"
    ARTIFACT = "ART"
    NORMALIZATION = "NORM"
    GOLD = "GOLD"
    FALLBACK = "FALLBACK"


@unique
class DiagnosticCodeFamily(StrEnum):
    PROCESS = "process"
    TOOLCHAIN = "toolchain"
    GF_COMPILATION = "gf_compilation"
    SCENARIO = "scenario"
    NORMALIZATION_AND_GOLD = "normalization_and_gold"
    ARTIFACT = "artifact"
    CONFIGURATION_AND_SCHEMA = "configuration_and_schema"
    FILESYSTEM_AND_ENCODING = "filesystem_and_encoding"


_SEVERITY_RANK: Final[Mapping[DiagnosticSeverity, int]] = MappingProxyType(
    {
        DiagnosticSeverity.FATAL: 0,
        DiagnosticSeverity.ERROR: 1,
        DiagnosticSeverity.WARNING: 2,
        DiagnosticSeverity.INFO: 3,
        DiagnosticSeverity.UNKNOWN: 4,
    }
)

_STREAM_RANK: Final[Mapping[DiagnosticStream, int]] = MappingProxyType(
    {
        DiagnosticStream.STDERR: 0,
        DiagnosticStream.STDOUT: 1,
    }
)

_PATTERN_CONFIDENCE_RANK: Final[Mapping[PatternConfidence, int]] = MappingProxyType(
    {
        PatternConfidence.AUTHORITATIVE: 0,
        PatternConfidence.EXACT: 1,
        PatternConfidence.HIGH: 2,
        PatternConfidence.STRONG: 3,
        PatternConfidence.MEDIUM: 4,
        PatternConfidence.FALLBACK: 5,
        PatternConfidence.LOW: 6,
        PatternConfidence.UNKNOWN: 7,
    }
)

_DIAGNOSTIC_CODE_FAMILIES: Final[Mapping[DiagnosticCodeFamily, frozenset[str]]] = MappingProxyType(
    {
        DiagnosticCodeFamily.PROCESS: frozenset(
            {
                "launch_failure",
                "unexpected_exit",
                "timeout",
                "termination_failure",
                "user_cancelled",
                "controller_cancelled",
                "stream_capture_failure",
            }
        ),
        DiagnosticCodeFamily.TOOLCHAIN: frozenset(
            {
                "unknown_version",
                "unsupported_version",
                "capability_missing",
                "version_probe_failure",
                "tool_contract_failure",
            }
        ),
        DiagnosticCodeFamily.GF_COMPILATION: frozenset(
            {
                "gf_parse_error",
                "gf_type_mismatch",
                "gf_unification_failure",
                "gf_internal_error",
                "module_not_found",
                "dependency_load_failure",
            }
        ),
        DiagnosticCodeFamily.SCENARIO: frozenset(
            {
                "script_syntax_error",
                "missing_expected_begin",
                "missing_expected_end",
                "end_without_begin",
                "mismatched_end",
                "nested_begin",
                "duplicate_section",
                "unexpected_section",
                "wrong_scenario",
                "out_of_order",
                "malformed_reserved_line",
                "open_section_at_eof",
                "unknown_assertion_type",
                "invalid_assertion",
                "assertion_failed",
            }
        ),
        DiagnosticCodeFamily.NORMALIZATION_AND_GOLD: frozenset(
            {
                "normalization_failure",
                "unsupported_normalization_version",
                "gold_missing",
                "gold_invalid",
                "gold_version_mismatch",
                "gold_mismatch",
                "gold_write_prohibited",
            }
        ),
        DiagnosticCodeFamily.ARTIFACT: frozenset(
            {
                "artifact_missing",
                "artifact_empty",
                "artifact_invalid",
                "artifact_hash_mismatch",
                "artifact_path_escape",
                "manifest_missing_entry",
            }
        ),
        DiagnosticCodeFamily.CONFIGURATION_AND_SCHEMA: frozenset(
            {
                "config_missing",
                "config_invalid",
                "schema_missing",
                "schema_unsupported",
                "required_field_missing",
                "invalid_field_type",
                "unknown_required_key",
                "multiple_active_projects",
            }
        ),
        DiagnosticCodeFamily.FILESYSTEM_AND_ENCODING: frozenset(
            {
                "file_not_found",
                "permission_denied",
                "read_failure",
                "write_failure",
                "decode_error",
                "encode_error",
                "atomic_replace_failure",
                "disk_full",
            }
        ),
    }
)

DIAGNOSTIC_CODE_FAMILIES: Final[Mapping[DiagnosticCodeFamily, frozenset[str]]] = (
    _DIAGNOSTIC_CODE_FAMILIES
)

KNOWN_DIAGNOSTIC_CODES: Final[frozenset[str]] = frozenset(
    code for codes in DIAGNOSTIC_CODE_FAMILIES.values() for code in codes
)

DiagnosticOperation = DiagnosticOperationKind
DiagnosticPatternLifecycle = PatternLifecycle
DiagnosticPatternConfidence = PatternConfidence
DiagnosticPatternDomain = PatternDomain


def validate_diagnostic_code(value: str) -> DiagnosticCode:
    text = _require_ascii_token(
        value,
        field="diagnostic_code",
        maximum=MAX_DIAGNOSTIC_CODE_LENGTH,
    )
    if _DIAGNOSTIC_CODE_PATTERN.fullmatch(text) is None:
        raise ValueError("diagnostic_code must match [a-z][a-z0-9]*(?:_[a-z0-9]+)*")
    return DiagnosticCode(text)


def is_known_diagnostic_code(value: str) -> bool:
    try:
        code = validate_diagnostic_code(value)
    except (TypeError, ValueError):
        return False
    return str(code) in KNOWN_DIAGNOSTIC_CODES


def diagnostic_code_family(
    value: str,
) -> DiagnosticCodeFamily | None:
    code = str(validate_diagnostic_code(value))
    for family, codes in DIAGNOSTIC_CODE_FAMILIES.items():
        if code in codes:
            return family
    return None


def validate_pattern_id(value: str) -> DiagnosticPatternId:
    text = _require_ascii_token(
        value,
        field="pattern_id",
        maximum=MAX_PATTERN_ID_LENGTH,
    )
    if _PATTERN_ID_PATTERN.fullmatch(text) is None:
        raise ValueError(
            "pattern_id must match DP-<DOMAIN>-<NUMBER> using a canonical diagnostic pattern domain"
        )
    return DiagnosticPatternId(text)


def pattern_domain(value: str) -> PatternDomain:
    pattern_id = str(validate_pattern_id(value))
    domain = pattern_id.split("-", 2)[1]
    return PatternDomain(domain)


def make_pattern_id(
    domain: PatternDomain | str,
    number: int,
) -> DiagnosticPatternId:
    canonical_domain = _coerce_enum(
        domain,
        PatternDomain,
        field="domain",
    )
    if type(number) is not int:
        raise TypeError("number must be an integer")
    if number < 1:
        raise ValueError("number must be positive")
    return validate_pattern_id(f"DP-{canonical_domain.value}-{number:03d}")


def severity_rank(value: DiagnosticSeverity | str) -> int:
    return _SEVERITY_RANK[_coerce_enum(value, DiagnosticSeverity, field="severity")]


def stream_rank(value: DiagnosticStream | str) -> int:
    return _STREAM_RANK[_coerce_enum(value, DiagnosticStream, field="stream")]


def pattern_confidence_rank(
    value: PatternConfidence | str,
) -> int:
    return _PATTERN_CONFIDENCE_RANK[
        _coerce_enum(
            value,
            PatternConfidence,
            field="pattern_confidence",
        )
    ]


def is_failure_severity(value: DiagnosticSeverity | str) -> bool:
    severity = _coerce_enum(
        value,
        DiagnosticSeverity,
        field="severity",
    )
    return severity in {
        DiagnosticSeverity.ERROR,
        DiagnosticSeverity.FATAL,
    }


def is_release_eligible_pattern(
    lifecycle: PatternLifecycle | str,
    confidence: PatternConfidence | str,
) -> bool:
    canonical_lifecycle = _coerce_enum(
        lifecycle,
        PatternLifecycle,
        field="lifecycle",
    )
    canonical_confidence = _coerce_enum(
        confidence,
        PatternConfidence,
        field="confidence",
    )
    return canonical_lifecycle is PatternLifecycle.ACTIVE and canonical_confidence in {
        PatternConfidence.EXACT,
        PatternConfidence.STRONG,
    }


def coerce_diagnostic_severity(
    value: DiagnosticSeverity | str,
) -> DiagnosticSeverity:
    return _coerce_enum(
        value,
        DiagnosticSeverity,
        field="diagnostic_severity",
    )


def coerce_operation_kind(
    value: DiagnosticOperationKind | str,
) -> DiagnosticOperationKind:
    return _coerce_enum(
        value,
        DiagnosticOperationKind,
        field="operation_kind",
    )


def coerce_diagnostic_stream(
    value: DiagnosticStream | str,
) -> DiagnosticStream:
    return _coerce_enum(
        value,
        DiagnosticStream,
        field="stream",
    )


def coerce_pattern_lifecycle(
    value: PatternLifecycle | str,
) -> PatternLifecycle:
    return _coerce_enum(
        value,
        PatternLifecycle,
        field="pattern_lifecycle",
    )


def coerce_pattern_confidence(
    value: PatternConfidence | str,
) -> PatternConfidence:
    return _coerce_enum(
        value,
        PatternConfidence,
        field="pattern_confidence",
    )


def _coerce_enum(
    value: object,
    enum_type: type[_EnumT],
    *,
    field: str,
) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field} must be {enum_type.__name__} or string")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"unknown {field}: {value!r}") from exc


def _require_ascii_token(
    value: object,
    *,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field} must not contain surrounding whitespace")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL characters")
    if not value.isascii():
        raise ValueError(f"{field} must contain ASCII characters only")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds the supported length limit")
    return value


__all__ = (
    "DIAGNOSTIC_CODE_FAMILIES",
    "DIAGNOSTIC_VOCABULARY_VERSION",
    "KNOWN_DIAGNOSTIC_CODES",
    "MAX_DIAGNOSTIC_CODE_LENGTH",
    "MAX_PATTERN_ID_LENGTH",
    "DiagnosticClass",
    "DiagnosticCode",
    "DiagnosticCodeFamily",
    "DiagnosticLineKind",
    "DiagnosticOperation",
    "DiagnosticOperationKind",
    "DiagnosticOrigin",
    "DiagnosticPatternConfidence",
    "DiagnosticPatternDomain",
    "DiagnosticPatternId",
    "DiagnosticPatternLifecycle",
    "DiagnosticSeverity",
    "DiagnosticStream",
    "DiagnosticStreamScope",
    "ErrorKind",
    "EvidenceConfidence",
    "ExecutionState",
    "PatternConfidence",
    "PatternDomain",
    "PatternLifecycle",
    "PresentationConfidence",
    "ValidationStatus",
    "coerce_diagnostic_severity",
    "coerce_diagnostic_stream",
    "coerce_operation_kind",
    "coerce_pattern_confidence",
    "coerce_pattern_lifecycle",
    "diagnostic_code_family",
    "is_failure_severity",
    "is_known_diagnostic_code",
    "is_release_eligible_pattern",
    "make_pattern_id",
    "pattern_confidence_rank",
    "pattern_domain",
    "severity_rank",
    "stream_rank",
    "validate_diagnostic_code",
    "validate_pattern_id",
)
