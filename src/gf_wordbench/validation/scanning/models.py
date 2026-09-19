"""Static-scanning domain models for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final, TypeVar

from gf_wordbench.kernel.statuses import ErrorKind, ValidationStatus

__all__ = (
    "BUILTIN_SCAN_RULE_SET_ID",
    "SCAN_COUNT_FIELDS",
    "ScanCompletionState",
    "ScanCountUnit",
    "ScanCounts",
    "ScanDiagnostic",
    "ScanEncodingOutcome",
    "ScanEncodingPolicy",
    "ScanFinding",
    "ScanRuleDefinition",
    "ScanRuleDomain",
    "ScanSourceView",
    "StaticScanRequest",
    "StaticScanResult",
    "validate_scan_diagnostic_code",
    "validate_scan_rule_id",
    "validate_scan_rule_set_id",
)

BUILTIN_SCAN_RULE_SET_ID: Final[str] = "gf-wordbench.static-scan/1"

SCAN_COUNT_FIELDS: Final[tuple[str, ...]] = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
)

_SCAN_RULE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^SCAN-(?P<domain>NOTATION|RUNTIME|PATTERN|STYLE)-"
    r"(?P<number>[0-9]{3})$"
)
_SCAN_DIAGNOSTIC_CODE_RE: Final[re.Pattern[str]] = re.compile(r"^GF-WB-SCAN-[0-9]{3}$")
_SCAN_RULE_SET_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*/[1-9][0-9]*$"
)
_SCAN_FIELD_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")

_MAX_FINDINGS: Final[int] = 100_000
_MAX_DIAGNOSTICS: Final[int] = 1_024
_MAX_TEXT_LENGTH: Final[int] = 4_096
_MAX_DETAIL_LENGTH: Final[int] = 32_768
_MAX_EXCERPT_LENGTH: Final[int] = 2_048
_MAX_SOURCE_SIZE: Final[int] = 1 << 30

_EnumT = TypeVar("_EnumT", bound=StrEnum)


@unique
class ScanRuleDomain(StrEnum):
    NOTATION = "NOTATION"
    RUNTIME = "RUNTIME"
    PATTERN = "PATTERN"
    STYLE = "STYLE"


@unique
class ScanSourceView(StrEnum):
    ORIGINAL = "original"
    COMMENT_STRIPPED = "comment_stripped"
    STRING_MASKED = "string_masked"


@unique
class ScanCountUnit(StrEnum):
    SOURCE_LINE = "source_line"
    CASE_BLOCK = "case_block"
    TABLE_BLOCK = "table_block"


@unique
class ScanEncodingPolicy(StrEnum):
    STRICT_UTF8 = "strict_utf8"
    DIAGNOSTIC_REPLACEMENT = "diagnostic_replacement"


@unique
class ScanEncodingOutcome(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    UTF8 = "utf8"
    UTF8_BOM = "utf8_bom"
    UTF8_LOSSY = "utf8_lossy"


@unique
class ScanCompletionState(StrEnum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class ScanCounts:
    single_slash_eq: int = 0
    double_slash_dash: int = 0
    runtime_str_match: int = 0
    untyped_case_str_pat: int = 0
    untyped_table_str_pat: int = 0
    trailing_spaces: int = 0

    def __post_init__(self) -> None:
        for field_name in SCAN_COUNT_FIELDS:
            _require_plain_int(
                getattr(self, field_name),
                field=field_name,
                minimum=0,
            )

    @property
    def total(self) -> int:
        return sum(getattr(self, field_name) for field_name in SCAN_COUNT_FIELDS)

    @property
    def has_findings(self) -> bool:
        return self.total > 0

    def count_for(self, field_name: str) -> int:
        normalized = _validate_count_field_name(field_name)
        counts = {
            "single_slash_eq": self.single_slash_eq,
            "double_slash_dash": self.double_slash_dash,
            "runtime_str_match": self.runtime_str_match,
            "untyped_case_str_pat": self.untyped_case_str_pat,
            "untyped_table_str_pat": self.untyped_table_str_pat,
            "trailing_spaces": self.trailing_spaces,
        }
        return counts[normalized]

    def as_tuple(self) -> tuple[tuple[str, int], ...]:
        return tuple(
            (
                field_name,
                getattr(self, field_name),
            )
            for field_name in SCAN_COUNT_FIELDS
        )

    def incremented(
        self,
        field_name: str,
        amount: int = 1,
    ) -> ScanCounts:
        normalized = _validate_count_field_name(field_name)
        increment = _require_plain_int(
            amount,
            field="amount",
            minimum=0,
        )
        values = {name: getattr(self, name) for name in SCAN_COUNT_FIELDS}
        values[normalized] += increment
        return ScanCounts(**values)

    def merged(
        self,
        other: ScanCounts,
    ) -> ScanCounts:
        if not isinstance(other, ScanCounts):
            raise TypeError("other must be a ScanCounts")
        return ScanCounts(
            **{
                field_name: (getattr(self, field_name) + getattr(other, field_name))
                for field_name in SCAN_COUNT_FIELDS
            }
        )


@dataclass(frozen=True, slots=True)
class ScanRuleDefinition:
    rule_id: str
    count_field: str
    count_unit: ScanCountUnit
    source_view: ScanSourceView
    interpretation: str
    order: int

    def __post_init__(self) -> None:
        rule_id = validate_scan_rule_id(self.rule_id)
        count_field = _validate_count_field_name(self.count_field)
        count_unit = _require_enum(
            self.count_unit,
            ScanCountUnit,
            field="count_unit",
        )
        source_view = _require_enum(
            self.source_view,
            ScanSourceView,
            field="source_view",
        )
        interpretation = _normalize_text(
            self.interpretation,
            field="interpretation",
            maximum=_MAX_TEXT_LENGTH,
        )
        order = _require_plain_int(
            self.order,
            field="order",
            minimum=0,
        )

        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(
            self,
            "count_field",
            count_field,
        )
        object.__setattr__(
            self,
            "count_unit",
            count_unit,
        )
        object.__setattr__(
            self,
            "source_view",
            source_view,
        )
        object.__setattr__(
            self,
            "interpretation",
            interpretation,
        )
        object.__setattr__(self, "order", order)

    @property
    def domain(self) -> ScanRuleDomain:
        match = _SCAN_RULE_ID_RE.fullmatch(self.rule_id)
        if match is None:
            raise AssertionError("validated scan rule ID no longer matches")
        return ScanRuleDomain(match.group("domain"))


@dataclass(frozen=True, slots=True)
class ScanFinding:
    rule_id: str
    count_field: str
    source_path: Path
    start_line: int
    end_line: int
    excerpt: str
    message: str
    start_column: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        rule_id = validate_scan_rule_id(self.rule_id)
        count_field = _validate_count_field_name(self.count_field)
        source_path = _normalize_project_relative_source_path(
            self.source_path,
            field="source_path",
        )
        start_line = _require_plain_int(
            self.start_line,
            field="start_line",
            minimum=1,
        )
        end_line = _require_plain_int(
            self.end_line,
            field="end_line",
            minimum=start_line,
        )
        excerpt = _normalize_evidence_text(
            self.excerpt,
            field="excerpt",
            maximum=_MAX_EXCERPT_LENGTH,
            allow_empty=True,
        )
        message = _normalize_text(
            self.message,
            field="message",
            maximum=_MAX_TEXT_LENGTH,
        )
        start_column = _normalize_optional_positive_int(
            self.start_column,
            field="start_column",
        )
        end_column = _normalize_optional_positive_int(
            self.end_column,
            field="end_column",
        )

        if end_column is not None and start_column is None:
            raise ValueError("end_column requires start_column")
        if (
            start_column is not None
            and end_column is not None
            and start_line == end_line
            and end_column < start_column
        ):
            raise ValueError("end_column must not precede start_column on the same line")

        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(
            self,
            "count_field",
            count_field,
        )
        object.__setattr__(
            self,
            "source_path",
            source_path,
        )
        object.__setattr__(
            self,
            "start_line",
            start_line,
        )
        object.__setattr__(self, "end_line", end_line)
        object.__setattr__(self, "excerpt", excerpt)
        object.__setattr__(self, "message", message)
        object.__setattr__(
            self,
            "start_column",
            start_column,
        )
        object.__setattr__(
            self,
            "end_column",
            end_column,
        )

    @property
    def sort_key(self) -> tuple[str, int, int, str]:
        return (
            self.rule_id,
            self.start_line,
            self.end_line,
            self.excerpt,
        )


@dataclass(frozen=True, slots=True)
class ScanDiagnostic:
    code: str
    error_kind: ErrorKind
    message: str
    detail: str = ""
    fatal: bool = False
    line: int | None = None
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        code = validate_scan_diagnostic_code(self.code)
        error_kind = _require_enum(
            self.error_kind,
            ErrorKind,
            field="error_kind",
        )
        message = _normalize_text(
            self.message,
            field="message",
            maximum=_MAX_TEXT_LENGTH,
        )
        detail = _normalize_evidence_text(
            self.detail,
            field="detail",
            maximum=_MAX_DETAIL_LENGTH,
            allow_empty=True,
        )
        if not isinstance(self.fatal, bool):
            raise TypeError("fatal must be a boolean")
        line = _normalize_optional_positive_int(
            self.line,
            field="line",
        )
        evidence_path = (
            None
            if self.evidence_path is None
            else _normalize_run_relative_path(
                self.evidence_path,
                field="evidence_path",
            )
        )

        if self.fatal and error_kind is ErrorKind.OK:
            raise ValueError("a fatal diagnostic must not use ErrorKind.OK")

        object.__setattr__(self, "code", code)
        object.__setattr__(
            self,
            "error_kind",
            error_kind,
        )
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "detail", detail)
        object.__setattr__(self, "line", line)
        object.__setattr__(
            self,
            "evidence_path",
            evidence_path,
        )


@dataclass(frozen=True, slots=True)
class StaticScanRequest:
    source_identity: str
    source_path: Path
    source_location: Path
    rule_set_id: str
    encoding_policy: ScanEncodingPolicy
    max_source_size: int
    evidence_path: Path
    source_fingerprint_reference: str | None = None

    def __post_init__(self) -> None:
        source_identity = _normalize_text(
            self.source_identity,
            field="source_identity",
            maximum=_MAX_TEXT_LENGTH,
        )
        source_path = _normalize_project_relative_source_path(
            self.source_path,
            field="source_path",
        )
        source_location = _normalize_absolute_path(
            self.source_location,
            field="source_location",
        )
        rule_set_id = validate_scan_rule_set_id(self.rule_set_id)
        encoding_policy = _require_enum(
            self.encoding_policy,
            ScanEncodingPolicy,
            field="encoding_policy",
        )
        max_source_size = _require_plain_int(
            self.max_source_size,
            field="max_source_size",
            minimum=1,
        )
        if max_source_size > _MAX_SOURCE_SIZE:
            raise ValueError(f"max_source_size must not exceed {_MAX_SOURCE_SIZE} bytes")
        evidence_path = _normalize_run_relative_scan_log_path(
            self.evidence_path,
            field="evidence_path",
        )
        source_fingerprint_reference = (
            None
            if self.source_fingerprint_reference is None
            else _normalize_text(
                self.source_fingerprint_reference,
                field="source_fingerprint_reference",
                maximum=_MAX_TEXT_LENGTH,
            )
        )

        object.__setattr__(
            self,
            "source_identity",
            source_identity,
        )
        object.__setattr__(
            self,
            "source_path",
            source_path,
        )
        object.__setattr__(
            self,
            "source_location",
            source_location,
        )
        object.__setattr__(
            self,
            "rule_set_id",
            rule_set_id,
        )
        object.__setattr__(
            self,
            "encoding_policy",
            encoding_policy,
        )
        object.__setattr__(
            self,
            "max_source_size",
            max_source_size,
        )
        object.__setattr__(
            self,
            "evidence_path",
            evidence_path,
        )
        object.__setattr__(
            self,
            "source_fingerprint_reference",
            source_fingerprint_reference,
        )


@dataclass(frozen=True, slots=True)
class StaticScanResult:
    source_identity: str
    source_path: Path
    completion_state: ScanCompletionState
    status: ValidationStatus
    rule_set_id: str
    encoding_outcome: ScanEncodingOutcome
    counts: ScanCounts | None
    findings: tuple[ScanFinding, ...]
    diagnostics: tuple[ScanDiagnostic, ...]
    scan_log_path: Path | None
    source_fingerprint_reference: str | None = None
    bytes_read: int | None = None

    def __post_init__(self) -> None:
        source_identity = _normalize_text(
            self.source_identity,
            field="source_identity",
            maximum=_MAX_TEXT_LENGTH,
        )
        source_path = _normalize_project_relative_source_path(
            self.source_path,
            field="source_path",
        )
        completion_state = _require_enum(
            self.completion_state,
            ScanCompletionState,
            field="completion_state",
        )
        status = _require_enum(
            self.status,
            ValidationStatus,
            field="status",
        )
        rule_set_id = validate_scan_rule_set_id(self.rule_set_id)
        encoding_outcome = _require_enum(
            self.encoding_outcome,
            ScanEncodingOutcome,
            field="encoding_outcome",
        )
        counts = self.counts
        if counts is not None and not isinstance(
            counts,
            ScanCounts,
        ):
            raise TypeError("counts must be a ScanCounts or None")
        findings = _normalize_findings(
            self.findings,
            source_path=source_path,
        )
        diagnostics = _normalize_diagnostics(self.diagnostics)
        scan_log_path = (
            None
            if self.scan_log_path is None
            else _normalize_run_relative_scan_log_path(
                self.scan_log_path,
                field="scan_log_path",
            )
        )
        source_fingerprint_reference = (
            None
            if self.source_fingerprint_reference is None
            else _normalize_text(
                self.source_fingerprint_reference,
                field="source_fingerprint_reference",
                maximum=_MAX_TEXT_LENGTH,
            )
        )
        bytes_read = (
            None
            if self.bytes_read is None
            else _require_plain_int(
                self.bytes_read,
                field="bytes_read",
                minimum=0,
            )
        )

        _validate_result_state(
            completion_state=completion_state,
            status=status,
            encoding_outcome=encoding_outcome,
            counts=counts,
            findings=findings,
            diagnostics=diagnostics,
            scan_log_path=scan_log_path,
            bytes_read=bytes_read,
        )
        _validate_counts_match_findings(
            counts,
            findings,
            completed=(completion_state is ScanCompletionState.COMPLETED),
        )

        object.__setattr__(
            self,
            "source_identity",
            source_identity,
        )
        object.__setattr__(
            self,
            "source_path",
            source_path,
        )
        object.__setattr__(
            self,
            "completion_state",
            completion_state,
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "rule_set_id",
            rule_set_id,
        )
        object.__setattr__(
            self,
            "encoding_outcome",
            encoding_outcome,
        )
        object.__setattr__(self, "findings", findings)
        object.__setattr__(
            self,
            "diagnostics",
            diagnostics,
        )
        object.__setattr__(
            self,
            "scan_log_path",
            scan_log_path,
        )
        object.__setattr__(
            self,
            "source_fingerprint_reference",
            source_fingerprint_reference,
        )
        object.__setattr__(
            self,
            "bytes_read",
            bytes_read,
        )

    @property
    def completed(self) -> bool:
        return self.completion_state is ScanCompletionState.COMPLETED

    @property
    def succeeded(self) -> bool:
        return self.completed and self.status is ValidationStatus.OK

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def fatal_diagnostics(self) -> tuple[ScanDiagnostic, ...]:
        return tuple(diagnostic for diagnostic in self.diagnostics if diagnostic.fatal)


def validate_scan_rule_id(
    value: object,
    *,
    field: str = "rule_id",
) -> str:
    candidate = _normalize_ascii_identifier(
        value,
        field=field,
    )
    if _SCAN_RULE_ID_RE.fullmatch(candidate) is None:
        raise ValueError(f"{field} must match SCAN-(NOTATION|RUNTIME|PATTERN|STYLE)-NNN")
    return candidate


def validate_scan_diagnostic_code(
    value: object,
    *,
    field: str = "code",
) -> str:
    candidate = _normalize_ascii_identifier(
        value,
        field=field,
    )
    if _SCAN_DIAGNOSTIC_CODE_RE.fullmatch(candidate) is None:
        raise ValueError(f"{field} must match GF-WB-SCAN-NNN")
    return candidate


def validate_scan_rule_set_id(
    value: object,
    *,
    field: str = "rule_set_id",
) -> str:
    candidate = _normalize_ascii_identifier(
        value,
        field=field,
    )
    if _SCAN_RULE_SET_ID_RE.fullmatch(candidate) is None:
        raise ValueError(f"{field} must use a lowercase stable-name/version identity")
    return candidate


def _normalize_findings(
    values: tuple[ScanFinding, ...],
    *,
    source_path: Path,
) -> tuple[ScanFinding, ...]:
    if not isinstance(values, tuple):
        raise TypeError("findings must be a tuple")
    if len(values) > _MAX_FINDINGS:
        raise ValueError("findings exceeds the bounded result limit")

    previous_key: tuple[str, int, int, str] | None = None
    normalized: list[ScanFinding] = []

    for index, finding in enumerate(values):
        if not isinstance(finding, ScanFinding):
            raise TypeError(f"findings[{index}] must be a ScanFinding")
        if finding.source_path != source_path:
            raise ValueError("every finding must reference the result source_path")
        if previous_key is not None and finding.sort_key < previous_key:
            raise ValueError("findings must use deterministic rule and source-range order")
        previous_key = finding.sort_key
        normalized.append(finding)

    return tuple(normalized)


def _normalize_diagnostics(
    values: tuple[ScanDiagnostic, ...],
) -> tuple[ScanDiagnostic, ...]:
    if not isinstance(values, tuple):
        raise TypeError("diagnostics must be a tuple")
    if len(values) > _MAX_DIAGNOSTICS:
        raise ValueError("diagnostics exceeds the bounded result limit")
    if any(not isinstance(value, ScanDiagnostic) for value in values):
        raise TypeError("diagnostics must contain ScanDiagnostic values")
    return values


def _validate_result_state(
    *,
    completion_state: ScanCompletionState,
    status: ValidationStatus,
    encoding_outcome: ScanEncodingOutcome,
    counts: ScanCounts | None,
    findings: tuple[ScanFinding, ...],
    diagnostics: tuple[ScanDiagnostic, ...],
    scan_log_path: Path | None,
    bytes_read: int | None,
) -> None:
    if status is ValidationStatus.FAIL:
        raise ValueError("static scan findings must not use FAIL status")

    if completion_state is ScanCompletionState.COMPLETED:
        if status is not ValidationStatus.OK:
            raise ValueError("a completed static scan must use OK status")
        if counts is None:
            raise ValueError("a completed static scan requires ScanCounts")
        if scan_log_path is None:
            raise ValueError("a completed static scan requires scan_log_path")
        if encoding_outcome is ScanEncodingOutcome.NOT_ATTEMPTED:
            raise ValueError("a completed static scan requires an encoding outcome")
        if any(diagnostic.fatal for diagnostic in diagnostics):
            raise ValueError("a completed static scan must not contain a fatal diagnostic")
        if bytes_read is None:
            raise ValueError("a completed static scan requires bytes_read")
        return

    if completion_state is ScanCompletionState.INCOMPLETE:
        if status is not ValidationStatus.ERROR:
            raise ValueError("an incomplete static scan must use ERROR status")
        if not diagnostics:
            raise ValueError("an incomplete static scan requires diagnostics")
        if not any(
            diagnostic.fatal or diagnostic.error_kind is not ErrorKind.OK
            for diagnostic in diagnostics
        ):
            raise ValueError("an incomplete static scan requires an error diagnostic")
        return

    if status is not ValidationStatus.SKIPPED:
        raise ValueError("a skipped static scan must use SKIPPED status")
    if counts is not None:
        raise ValueError("a skipped static scan must not contain counts")
    if findings:
        raise ValueError("a skipped static scan must not contain findings")
    if scan_log_path is not None:
        raise ValueError("a skipped static scan must not claim a scan log")
    if encoding_outcome is not ScanEncodingOutcome.NOT_ATTEMPTED:
        raise ValueError("a skipped static scan must not claim decoding")
    if bytes_read is not None:
        raise ValueError("a skipped static scan must not claim bytes_read")


def _validate_counts_match_findings(
    counts: ScanCounts | None,
    findings: tuple[ScanFinding, ...],
    *,
    completed: bool,
) -> None:
    if counts is None:
        if completed:
            raise ValueError("completed scan requires counts")
        return

    finding_counts = dict.fromkeys(SCAN_COUNT_FIELDS, 0)
    for finding in findings:
        finding_counts[finding.count_field] += 1

    if completed:
        for field_name, finding_count in finding_counts.items():
            if getattr(counts, field_name) != finding_count:
                raise ValueError(
                    f"completed scan counts must agree with structured findings for {field_name}"
                )
    else:
        for field_name, finding_count in finding_counts.items():
            if getattr(counts, field_name) < finding_count:
                raise ValueError(
                    f"partial counts must not be lower than recorded findings for {field_name}"
                )


def _validate_count_field_name(
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError("count field name must be a string")
    if _SCAN_FIELD_RE.fullmatch(value) is None:
        raise ValueError("count field name must use lower_snake_case")
    if value not in SCAN_COUNT_FIELDS:
        allowed = ", ".join(SCAN_COUNT_FIELDS)
        raise ValueError(f"unknown scan count field {value!r}; expected one of {allowed}")
    return value


def _normalize_project_relative_source_path(
    value: object,
    *,
    field: str,
) -> Path:
    path = _normalize_relative_path(
        value,
        field=field,
    )
    if path.suffix.casefold() != ".gf":
        raise ValueError(f"{field} must identify a .gf source file")
    return path


def _normalize_run_relative_scan_log_path(
    value: object,
    *,
    field: str,
) -> Path:
    path = _normalize_run_relative_path(
        value,
        field=field,
    )
    parts = path.as_posix().split("/")
    if len(parts) < 3 or parts[:2] != ["raw", "scan"]:
        raise ValueError(f"{field} must be beneath raw/scan")
    if not path.name.endswith(".scan.txt"):
        raise ValueError(f"{field} must end in .scan.txt")
    return path


def _normalize_run_relative_path(
    value: object,
    *,
    field: str,
) -> Path:
    return _normalize_relative_path(
        value,
        field=field,
    )


def _normalize_relative_path(
    value: object,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")

    rendered = value.as_posix()
    if not rendered or "\x00" in rendered:
        raise ValueError(f"{field} must be a non-empty safe path")
    if _is_absolute_path_text(rendered):
        raise ValueError(f"{field} must be relative")

    portable = PurePosixPath(rendered)
    if portable == PurePosixPath("."):
        raise ValueError(f"{field} must identify a file")
    if any(part in {"", ".", ".."} for part in portable.parts):
        raise ValueError(f"{field} must be normalized without traversal")

    normalized = Path(*portable.parts)
    if normalized.as_posix() != rendered:
        raise ValueError(f"{field} must use canonical forward slashes")
    return normalized


def _normalize_absolute_path(
    value: object,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")

    rendered = str(value)
    if not rendered or "\x00" in rendered:
        raise ValueError(f"{field} must be a non-empty safe path")
    if not _is_absolute_path_text(rendered):
        raise ValueError(f"{field} must be absolute")
    if any(part == ".." for part in PureWindowsPath(rendered).parts) or any(
        part == ".." for part in PurePosixPath(rendered.replace("\\", "/")).parts
    ):
        raise ValueError(f"{field} must not contain traversal")
    return value


def _is_absolute_path_text(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )


def _normalize_ascii_identifier(
    value: object,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not value.isascii():
        raise ValueError(f"{field} must use ASCII characters")
    return value


def _normalize_text(
    value: object,
    *,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return normalized


def _normalize_evidence_text(
    value: object,
    *,
    field: str,
    maximum: int,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    normalized = value.replace("\r\n", "\n").replace(
        "\r",
        "\n",
    )
    if not allow_empty and not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return normalized


def _normalize_optional_positive_int(
    value: object,
    *,
    field: str,
) -> int | None:
    if value is None:
        return None
    return _require_plain_int(
        value,
        field=field,
        minimum=1,
    )


def _require_plain_int(
    value: object,
    *,
    field: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return value


def _require_enum(
    value: object,
    enum_type: type[_EnumT],
    *,
    field: str,
) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    allowed = ", ".join(member.value for member in enum_type)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be one of: {allowed}")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be one of: {allowed}") from exc
