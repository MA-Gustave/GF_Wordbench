"""Deterministic primary-diagnostic selection."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import IntEnum, unique
from pathlib import PurePath
from typing import Final, Generic, Protocol, TypeVar, runtime_checkable

_MAX_PRIMARY_MESSAGE: Final[int] = 1_000
_MAX_ERROR_DETAIL: Final[int] = 4_000
_MAX_LINE_NUMBER: Final[int] = 2**63 - 1


@runtime_checkable
class DiagnosticRecordLike(Protocol):
    pattern_id: object
    error_kind: object
    severity: object
    confidence: object
    message: object


DiagnosticRecordT = TypeVar("DiagnosticRecordT", bound=DiagnosticRecordLike)


@unique
class PrimaryDiagnosticTier(IntEnum):
    AUTHORITATIVE_PROCESS = 0
    AUTHORITATIVE_CONTRACT = 10
    FATAL_INTERNAL_LOCATED = 20
    FATAL_INTERNAL = 30
    LOCATED_SYNTAX_OR_TYPE = 40
    SYNTAX_OR_TYPE = 50
    OPERATION_SPECIFIC = 60
    OTHER_ERROR = 70
    UNKNOWN_NONZERO_FAILURE = 80
    FALLBACK_ERROR = 90
    WARNING = 100
    INFORMATIONAL = 110


@dataclass(frozen=True, slots=True)
class PrimarySelection(Generic[DiagnosticRecordT]):
    primary: DiagnosticRecordT | None
    secondary: tuple[DiagnosticRecordT, ...]

    def __post_init__(self) -> None:
        secondary = tuple(self.secondary)
        if self.primary is not None and any(
            item is self.primary for item in secondary
        ):
            raise ValueError("primary must not also appear in secondary")
        object.__setattr__(self, "secondary", secondary)


_PROCESS_PATTERN_PREFIXES: Final[tuple[str, ...]] = (
    "DP-PROC-",
    "GF-DIAG-PROC-",
)
_CONTRACT_PATTERN_PREFIXES: Final[tuple[str, ...]] = (
    "DP-SCEN-",
    "DP-ART-",
    "DP-NORM-",
    "DP-GOLD-",
    "GF-DIAG-CONTRACT-",
    "GF-DIAG-ARTIFACT-",
)
_FALLBACK_PATTERN_PREFIXES: Final[tuple[str, ...]] = (
    "DP-FALLBACK-",
    "GF-DIAG-FALLBACK-",
)
_AUTHORITATIVE_ERROR_KINDS: Final[frozenset[str]] = frozenset(
    {
        "TIMEOUT",
        "CANCELLED",
        "OUTPUT_LIMIT",
    }
)
_CONTRACT_ERROR_KINDS: Final[frozenset[str]] = frozenset(
    {
        "CONFIG",
        "IO",
        "TOOL",
        "CONTRACT",
        "ARTIFACT",
        "NORMALIZATION",
        "GOLD",
    }
)
_OPERATION_ERROR_KINDS: Final[frozenset[str]] = frozenset(
    {
        "SCRIPT",
        "TOOL",
        "CONFIG",
        "IO",
        "ARTIFACT",
        "NORMALIZATION",
        "GOLD",
        "CONTRACT",
    }
)
_FAILURE_SEVERITIES: Final[frozenset[str]] = frozenset({"fatal", "error"})
_WARNING_SEVERITIES: Final[frozenset[str]] = frozenset({"warning"})

_CONFIDENCE_RANK: Final[dict[str, int]] = {
    "authoritative": 0,
    "exact": 10,
    "high": 10,
    "strong": 20,
    "medium": 30,
    "fallback": 40,
    "low": 50,
    "unknown": 60,
}
_STREAM_RANK: Final[dict[str, int]] = {
    "stderr": 0,
    "stdout": 1,
}


def select_primary_diagnostic(
    records: Iterable[DiagnosticRecordT],
    *,
    exit_code: int | None = None,
    allow_warning_primary: bool = False,
) -> DiagnosticRecordT | None:
    ordered = order_diagnostics(
        records,
        exit_code=exit_code,
        allow_warning_primary=allow_warning_primary,
    )
    return ordered[0] if ordered else None


def select_primary(
    records: Iterable[DiagnosticRecordT],
    *,
    exit_code: int | None = None,
    allow_warning_primary: bool = False,
) -> PrimarySelection[DiagnosticRecordT]:
    prepared = _prepare_records(records)
    primary = select_primary_diagnostic(
        prepared,
        exit_code=exit_code,
        allow_warning_primary=allow_warning_primary,
    )
    if primary is None:
        return PrimarySelection(primary=None, secondary=prepared)
    secondary = tuple(item for item in prepared if item is not primary)
    return PrimarySelection(primary=primary, secondary=secondary)


def order_diagnostics(
    records: Iterable[DiagnosticRecordT],
    *,
    exit_code: int | None = None,
    allow_warning_primary: bool = True,
) -> tuple[DiagnosticRecordT, ...]:
    prepared = _prepare_records(records)
    eligible = tuple(
        record
        for record in prepared
        if _is_primary_eligible(
            record,
            exit_code=exit_code,
            allow_warning_primary=allow_warning_primary,
        )
    )
    return tuple(
        sorted(
            eligible,
            key=lambda record: primary_sort_key(record, exit_code=exit_code),
        )
    )


def primary_sort_key(
    record: DiagnosticRecordLike,
    *,
    exit_code: int | None = None,
) -> tuple[int, int, int, int, int, str, str, str]:
    _validate_record(record)
    tier = primary_tier(record, exit_code=exit_code)
    confidence_rank = _CONFIDENCE_RANK.get(
        _enum_value(record.confidence).casefold(),
        _CONFIDENCE_RANK["unknown"],
    )
    pattern_precedence = _non_negative_int(
        _first_attribute(
            record,
            "pattern_precedence",
            "pattern_priority",
            "priority",
            "precedence",
        ),
        default=_MAX_LINE_NUMBER,
    )
    stream_rank = _STREAM_RANK.get(
        _stream_value(record),
        len(_STREAM_RANK),
    )
    start_line = _positive_int(
        _first_attribute(record, "start_line", "line_number", "line"),
        default=_MAX_LINE_NUMBER,
    )
    pattern_id = _safe_text(record.pattern_id)
    message = _safe_text(record.message)
    record_id = _safe_text(_first_attribute(record, "record_id"))
    return (
        int(tier),
        confidence_rank,
        pattern_precedence,
        stream_rank,
        start_line,
        pattern_id,
        message.casefold(),
        record_id,
    )


def primary_tier(
    record: DiagnosticRecordLike,
    *,
    exit_code: int | None = None,
) -> PrimaryDiagnosticTier:
    _validate_record(record)
    pattern_id = _safe_text(record.pattern_id).upper()
    error_kind = _enum_value(record.error_kind).upper()
    severity = _enum_value(record.severity).casefold()
    confidence = _enum_value(record.confidence).casefold()
    located = _has_source_location(record)
    unknown = _is_unknown(record)

    if confidence == "authoritative" and (
        error_kind in _AUTHORITATIVE_ERROR_KINDS
        or pattern_id.startswith(_PROCESS_PATTERN_PREFIXES)
    ):
        return PrimaryDiagnosticTier.AUTHORITATIVE_PROCESS

    if confidence == "authoritative" and (
        error_kind in _CONTRACT_ERROR_KINDS
        or pattern_id.startswith(_CONTRACT_PATTERN_PREFIXES)
    ):
        return PrimaryDiagnosticTier.AUTHORITATIVE_CONTRACT

    if severity == "fatal" and error_kind == "INTERNAL" and located:
        return PrimaryDiagnosticTier.FATAL_INTERNAL_LOCATED

    if severity == "fatal" and error_kind == "INTERNAL":
        return PrimaryDiagnosticTier.FATAL_INTERNAL

    if error_kind in {"SYNTAX", "TYPE"} and located:
        return PrimaryDiagnosticTier.LOCATED_SYNTAX_OR_TYPE

    if error_kind in {"SYNTAX", "TYPE"}:
        return PrimaryDiagnosticTier.SYNTAX_OR_TYPE

    if error_kind in _OPERATION_ERROR_KINDS and severity in _FAILURE_SEVERITIES:
        return PrimaryDiagnosticTier.OPERATION_SPECIFIC

    if severity in _FAILURE_SEVERITIES and not unknown:
        return PrimaryDiagnosticTier.OTHER_ERROR

    if unknown and exit_code not in (None, 0):
        return PrimaryDiagnosticTier.UNKNOWN_NONZERO_FAILURE

    if (
        pattern_id.startswith(_FALLBACK_PATTERN_PREFIXES)
        or confidence in {"fallback", "low", "unknown"}
        or error_kind == "OTHER"
    ):
        return PrimaryDiagnosticTier.FALLBACK_ERROR

    if severity in _WARNING_SEVERITIES:
        return PrimaryDiagnosticTier.WARNING

    return PrimaryDiagnosticTier.INFORMATIONAL


def primary_message(
    record: DiagnosticRecordLike | None,
    *,
    max_length: int = _MAX_PRIMARY_MESSAGE,
) -> str | None:
    if record is None:
        return None
    _validate_record(record)
    limit = _positive_limit(max_length, field="max_length")
    message = _bounded_text(_safe_text(record.message), limit)
    if not message:
        return None
    location = _render_location(record)
    if not location or _message_already_has_location(message, location):
        return message
    return _bounded_text(f"{location}: {message}", limit)


def error_detail(
    record: DiagnosticRecordLike | None,
    *,
    max_length: int = _MAX_ERROR_DETAIL,
) -> str | None:
    if record is None:
        return None
    _validate_record(record)
    limit = _positive_limit(max_length, field="max_length")
    detail = _safe_text(_first_attribute(record, "detail", "error_detail"))
    if not detail:
        detail = _safe_text(_first_attribute(record, "raw_excerpt"))
    detail = _bounded_text(detail, limit)
    return detail or None


def compact_primary_fields(
    record: DiagnosticRecordLike | None,
    *,
    message_limit: int = _MAX_PRIMARY_MESSAGE,
    detail_limit: int = _MAX_ERROR_DETAIL,
) -> tuple[str | None, str | None, str | None]:
    if record is None:
        return None, None, None
    return (
        _enum_value(record.error_kind) or None,
        primary_message(record, max_length=message_limit),
        error_detail(record, max_length=detail_limit),
    )


def _prepare_records(
    records: Iterable[DiagnosticRecordT],
) -> tuple[DiagnosticRecordT, ...]:
    if isinstance(records, (str, bytes, bytearray)):
        raise TypeError("records must be an iterable of diagnostic records")
    prepared = tuple(records)
    for record in prepared:
        _validate_record(record)
    return prepared


def _is_primary_eligible(
    record: DiagnosticRecordLike,
    *,
    exit_code: int | None,
    allow_warning_primary: bool,
) -> bool:
    severity = _enum_value(record.severity).casefold()
    error_kind = _enum_value(record.error_kind).upper()
    message = _safe_text(record.message)
    if not message:
        return False
    if severity in _FAILURE_SEVERITIES:
        return True
    if error_kind not in {"", "OK"}:
        return True
    if _is_unknown(record) and exit_code not in (None, 0):
        return True
    return allow_warning_primary and severity == "warning"


def _validate_record(record: object) -> None:
    if record is None:
        raise TypeError("diagnostic record must not be None")
    for field in ("pattern_id", "error_kind", "severity", "confidence", "message"):
        if not hasattr(record, field):
            raise TypeError(f"diagnostic record is missing required field {field!r}")
    if not _safe_text(getattr(record, "pattern_id")):
        raise ValueError("diagnostic pattern_id must not be empty")
    if not _enum_value(getattr(record, "severity")):
        raise ValueError("diagnostic severity must not be empty")
    if not _enum_value(getattr(record, "confidence")):
        raise ValueError("diagnostic confidence must not be empty")


def _has_source_location(record: object) -> bool:
    source_path = _first_attribute(record, "source_path", "file_path")
    source_module = _first_attribute(record, "source_module", "module_name")
    line = _first_attribute(record, "line", "source_line", "line_number")
    return bool(_safe_text(source_path) or _safe_text(source_module) or _positive_int(line))


def _is_unknown(record: object) -> bool:
    flag = _first_attribute(record, "is_unknown")
    if isinstance(flag, bool):
        return flag
    pattern_id = _safe_text(_first_attribute(record, "pattern_id")).upper()
    confidence = _enum_value(_first_attribute(record, "confidence")).casefold()
    return pattern_id in {"DIAG-UNKNOWN", "DP-FALLBACK-002"} or confidence == "unknown"


def _stream_value(record: object) -> str:
    return _enum_value(
        _first_attribute(record, "stream", "source_stream")
    ).casefold()


def _render_location(record: object) -> str:
    source = _safe_text(_first_attribute(record, "source_path", "file_path"))
    if not source:
        source = _safe_text(_first_attribute(record, "source_module", "module_name"))
    if source:
        source = PurePath(source.replace("\\", "/")).as_posix()
    line = _positive_int(
        _first_attribute(record, "line", "source_line", "line_number")
    )
    column = _positive_int(
        _first_attribute(record, "column", "source_column")
    )
    if not source:
        return ""
    if line is None:
        return source
    if column is None:
        return f"{source}:{line}"
    return f"{source}:{line}:{column}"


def _message_already_has_location(message: str, location: str) -> bool:
    normalized_message = message.replace("\\", "/").casefold()
    normalized_location = location.replace("\\", "/").casefold()
    return normalized_message.startswith(normalized_location)


def _first_attribute(record: object, *names: str) -> object | None:
    for name in names:
        if hasattr(record, name):
            value = getattr(record, name)
            if value is not None:
                return value
    return None


def _enum_value(value: object) -> str:
    if value is None:
        return ""
    raw = getattr(value, "value", value)
    return _safe_text(raw)


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, PurePath):
        text = value.as_posix()
    elif isinstance(value, str):
        text = value
    else:
        text = str(value)
    text = text.replace("\x00", "")
    return " ".join(text.split())


def _bounded_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    if limit == 1:
        return "…"
    return f"{value[: limit - 1].rstrip()}…"


def _positive_int(value: object, default: int | None = None) -> int | None:
    if type(value) is int and value > 0:
        return value
    return default


def _non_negative_int(value: object, default: int) -> int:
    if type(value) is int and value >= 0:
        return value
    return default


def _positive_limit(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be positive")
    return value


__all__ = (
    "DiagnosticRecordLike",
    "PrimaryDiagnosticTier",
    "PrimarySelection",
    "compact_primary_fields",
    "error_detail",
    "order_diagnostics",
    "primary_message",
    "primary_sort_key",
    "primary_tier",
    "select_primary",
    "select_primary_diagnostic",
)
