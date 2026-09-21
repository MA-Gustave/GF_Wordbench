"""One-file static-scanning application service."""

from __future__ import annotations

import codecs
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
import inspect
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from typing import Final, Protocol, cast

from gf_wordbench.kernel.statuses import ErrorKind, ValidationStatus

from .masking import build_source_views
from .models import (
    ScanCompletionState,
    ScanCounts,
    ScanDiagnostic,
    ScanEncodingOutcome,
    ScanEncodingPolicy,
    ScanFinding,
    StaticScanRequest,
    StaticScanResult,
)
from .registry import (
    CANONICAL_SCAN_RULE_REGISTRY,
    ScanRule,
    ScanRuleRegistry,
)
from .rules.suspicious import (
    find_double_slash_dash,
    find_runtime_string_matches,
    find_single_slash_eq,
    find_trailing_spaces,
    find_untyped_case_string_patterns,
    find_untyped_table_string_patterns,
)

_MAX_EXCERPT_CHARACTERS: Final[int] = 240
_MAX_DIAGNOSTIC_CHARACTERS: Final[int] = 1_024
_LOG_ENCODING: Final[str] = "utf-8"
_RULE_SET_VERSION: Final[str] = "2.0.0"
_COUNT_FIELDS: Final[tuple[str, ...]] = tuple(field.name for field in fields(ScanCounts))


class _ScanRequestView(Protocol):
    @property
    def rule_set_id(self) -> str: ...

    @property
    def evidence_path(self) -> Path: ...


@dataclass(frozen=True, slots=True)
class _TextScanRequest:
    source_path: Path
    project_relative_path: PurePosixPath
    evidence_path: Path
    rule_set_id: str
    max_source_bytes: int
    allow_lossy_decode: bool = False
    fingerprint_reference: str | None = None


class StaticScanError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        source_path: Path | None = None,
        evidence_path: Path | None = None,
        cause: BaseException | None = None,
    ) -> None:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.source_path = source_path
        self.evidence_path = evidence_path
        self.cause = cause
        super().__init__(message)


def scan_file(
    request: StaticScanRequest,
    *,
    registry: ScanRuleRegistry = CANONICAL_SCAN_RULE_REGISTRY,
) -> StaticScanResult:
    _validate_request(request)
    _validate_registry(registry, expected_rule_set_id=request.rule_set_id)

    source_location = _request_source_location(request)
    source_bytes = _read_source_bytes(request)
    source_text, encoding_outcome, decode_diagnostics = _decode_source(
        source_bytes,
        allow_lossy=_request_allow_lossy(request),
        source_path=source_location,
    )

    try:
        views = build_source_views(source_text)
    except Exception as exc:
        raise StaticScanError(
            "GF-WB-SCAN-004",
            "Static-scanning lexical view construction failed.",
            source_path=source_location,
            evidence_path=request.evidence_path,
            cause=exc,
        ) from exc

    masking_diagnostics = tuple(
        _coerce_diagnostic(diagnostic)
        for diagnostic in _view_diagnostics(views)
    )
    findings = _evaluate_rules(request=request, registry=registry, views=views)
    counts = _build_counts(findings)
    diagnostics = _sort_diagnostics((*decode_diagnostics, *masking_diagnostics))
    result = _build_scan_result(
        request=request,
        registry=registry,
        counts=counts,
        findings=findings,
        diagnostics=diagnostics,
        encoding_outcome=encoding_outcome,
        source_size_bytes=len(source_bytes),
    )

    log_text = render_scan_log(request, result, registry=registry)
    _write_scan_log(request.evidence_path, log_text, source_path=source_location)
    return result

def scan_text(
    source_text: str,
    *,
    project_relative_path: str | PurePosixPath,
    rule_set_id: str | None = None,
    registry: ScanRuleRegistry = CANONICAL_SCAN_RULE_REGISTRY,
) -> tuple[ScanCounts, tuple[ScanFinding, ...], tuple[ScanDiagnostic, ...]]:
    if not isinstance(source_text, str):
        raise TypeError("source_text must be a string")
    _validate_registry(
        registry,
        expected_rule_set_id=(registry.rule_set_id if rule_set_id is None else rule_set_id),
    )
    relative_path = _normalize_project_relative_path(project_relative_path)

    try:
        views = build_source_views(source_text)
    except Exception as exc:
        raise StaticScanError(
            "GF-WB-SCAN-004",
            "Static-scanning lexical view construction failed.",
            cause=exc,
        ) from exc

    request = _build_text_scan_request(
        relative_path=relative_path,
        rule_set_id=registry.rule_set_id,
        source_size=max(1, len(source_text.encode("utf-8"))),
    )
    findings = _evaluate_rules(
        request=request,
        registry=registry,
        views=views,
    )
    diagnostics = _sort_diagnostics(
        tuple(_coerce_diagnostic(diagnostic) for diagnostic in _view_diagnostics(views))
    )
    return _build_counts(findings), findings, diagnostics


def render_scan_log(
    request: StaticScanRequest,
    result: StaticScanResult,
    *,
    registry: ScanRuleRegistry = CANONICAL_SCAN_RULE_REGISTRY,
) -> str:
    _validate_request(request)
    if not isinstance(result, StaticScanResult):
        raise TypeError("result must be a StaticScanResult")
    _validate_registry(registry, expected_rule_set_id=result.rule_set_id)

    source_location = _request_source_location(request)
    relative_path = _request_project_relative_path(request)
    counts = _result_counts(result)
    lines: list[str] = [
        "GF Wordbench Static Scan",
        "",
        f"source_path: {source_location}",
        f"project_relative_path: {relative_path.as_posix()}",
        f"rule_set_id: {result.rule_set_id}",
        f"rule_set_version: {_registry_version(registry)}",
        f"completion_state: {result.completion_state.value}",
        f"encoding_outcome: {result.encoding_outcome.value}",
        f"source_size_bytes: {_result_source_size(result)}",
        "",
        "Counts",
    ]

    count_values = _counts_mapping(counts)
    for field_name in _COUNT_FIELDS:
        lines.append(f"{field_name}: {count_values[field_name]}")

    findings_by_rule = _group_findings(result.findings)
    lines.extend(("", "Findings"))
    for rule in registry.rules:
        lines.extend(("", f"[{rule.rule_id}] {rule.count_field}"))
        rule_findings = findings_by_rule.get(str(rule.rule_id), ())
        if not rule_findings:
            lines.append("none")
            continue
        for finding in rule_findings:
            location = (
                str(finding.start_line)
                if finding.start_line == finding.end_line
                else f"{finding.start_line}-{finding.end_line}"
            )
            lines.append(f"line: {location}")
            lines.append(f"message: {finding.message}")
            lines.append(f"excerpt: {_bounded_excerpt(finding.excerpt)}")

    lines.extend(("", "Diagnostics"))
    if not result.diagnostics:
        lines.append("none")
    else:
        for diagnostic in result.diagnostics:
            location = "" if diagnostic.line is None else f" line={diagnostic.line}"
            lines.append(f"{diagnostic.code}{location}: {_bounded_diagnostic(diagnostic.message)}")
    return "\n".join(lines) + "\n"

def _read_source_bytes(request: StaticScanRequest) -> bytes:
    path = _request_source_location(request)
    maximum = _request_max_source_size(request)
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise StaticScanError(
            "GF-WB-SCAN-001",
            "Selected source file does not exist.",
            source_path=path,
            evidence_path=request.evidence_path,
            cause=exc,
        ) from exc
    except OSError as exc:
        raise StaticScanError(
            "GF-WB-SCAN-001",
            "Selected source metadata could not be read.",
            source_path=path,
            evidence_path=request.evidence_path,
            cause=exc,
        ) from exc

    if stat.S_ISLNK(metadata.st_mode):
        raise StaticScanError(
            "GF-WB-SCAN-002",
            "Selected source must not be a symbolic link.",
            source_path=path,
            evidence_path=request.evidence_path,
        )
    if not stat.S_ISREG(metadata.st_mode):
        raise StaticScanError(
            "GF-WB-SCAN-002",
            "Selected source is not a regular file.",
            source_path=path,
            evidence_path=request.evidence_path,
        )
    if metadata.st_size > maximum:
        raise StaticScanError(
            "GF-WB-SCAN-003",
            ("Selected source exceeds the configured static-scan size limit."),
            source_path=path,
            evidence_path=request.evidence_path,
        )

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise StaticScanError(
            "GF-WB-SCAN-001",
            "Selected source could not be read.",
            source_path=path,
            evidence_path=request.evidence_path,
            cause=exc,
        ) from exc

    if len(data) > maximum:
        raise StaticScanError(
            "GF-WB-SCAN-003",
            ("Selected source exceeds the configured static-scan size limit."),
            source_path=path,
            evidence_path=request.evidence_path,
        )
    return data


def _decode_source(
    data: bytes,
    *,
    allow_lossy: bool,
    source_path: Path,
) -> tuple[
    str,
    ScanEncodingOutcome,
    tuple[ScanDiagnostic, ...],
]:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not isinstance(allow_lossy, bool):
        raise TypeError("allow_lossy must be a bool")

    has_bom = data.startswith(codecs.BOM_UTF8)
    try:
        text = data.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as exc:
        if not allow_lossy:
            raise StaticScanError(
                "GF-WB-SCAN-005",
                "Selected source is not valid UTF-8.",
                source_path=source_path,
                cause=exc,
            ) from exc
        text = data.decode("utf-8", errors="replace")
        diagnostic = _make_scan_diagnostic(
            code="GF-WB-SCAN-ENCODING-001",
            message=(
                "Source was decoded with replacement characters; scan interpretation is lossy."
            ),
            line=None,
        )
        return (
            text,
            _lossy_encoding_outcome(),
            (diagnostic,),
        )

    outcome = ScanEncodingOutcome.UTF8_BOM if has_bom else ScanEncodingOutcome.UTF8
    return text, outcome, ()


def _evaluate_rules(
    *,
    request: _ScanRequestView,
    registry: ScanRuleRegistry,
    views: object,
) -> tuple[ScanFinding, ...]:
    source_location = _request_source_location(request)
    relative_path = _request_project_relative_path(request)
    findings: list[ScanFinding] = []

    for rule in registry.rules:
        scanner = getattr(rule, "scan", None)
        try:
            if callable(scanner):
                produced = scanner(
                    views,
                    source_path=source_location,
                    project_relative_path=relative_path,
                )
            else:
                produced = _evaluate_canonical_rule(
                    rule,
                    views=views,
                    relative_path=relative_path,
                )
        except Exception as exc:
            raise StaticScanError(
                "GF-WB-SCAN-006",
                f"Static scan rule {rule.rule_id} failed.",
                source_path=source_location,
                evidence_path=request.evidence_path,
                cause=exc,
            ) from exc

        if not isinstance(produced, Iterable):
            raise StaticScanError(
                "GF-WB-SCAN-006",
                f"Static scan rule {rule.rule_id} returned a non-iterable result.",
                source_path=source_location,
                evidence_path=request.evidence_path,
            )
        for finding_index, finding in enumerate(produced):
            if not isinstance(finding, ScanFinding):
                raise StaticScanError(
                    "GF-WB-SCAN-006",
                    f"Static scan rule {rule.rule_id} returned an invalid finding at index {finding_index}.",
                    source_path=source_location,
                    evidence_path=request.evidence_path,
                )
            if str(finding.rule_id) != str(rule.rule_id):
                raise StaticScanError(
                    "GF-WB-SCAN-006",
                    f"Static scan rule {rule.rule_id} returned a finding with a different rule ID.",
                    source_path=source_location,
                    evidence_path=request.evidence_path,
                )
            if finding.count_field != rule.count_field:
                raise StaticScanError(
                    "GF-WB-SCAN-006",
                    f"Static scan rule {rule.rule_id} returned a finding with a different count field.",
                    source_path=source_location,
                    evidence_path=request.evidence_path,
                )
            findings.append(finding)

    rule_order = {str(rule.rule_id): index for index, rule in enumerate(registry.rules)}
    return tuple(
        sorted(
            findings,
            key=lambda finding: (
                rule_order[str(finding.rule_id)],
                finding.start_line,
                finding.end_line,
                finding.excerpt,
            ),
        )
    )


def _evaluate_canonical_rule(
    rule: ScanRule,
    *,
    views: object,
    relative_path: PurePosixPath,
) -> tuple[ScanFinding, ...]:
    original_lines = _view_lines(views, "original_lines")
    comment_lines = _view_lines(views, "comment_stripped_lines")
    masked_lines = _view_lines(views, "string_masked_lines")
    detectors: Mapping[str, Callable[[], tuple[tuple[int, int], ...]]] = {
        "single_slash_eq": lambda: find_single_slash_eq(masked_lines),
        "double_slash_dash": lambda: find_double_slash_dash(masked_lines),
        "runtime_str_match": lambda: find_runtime_string_matches(masked_lines, comment_lines),
        "untyped_case_str_pat": lambda: find_untyped_case_string_patterns(masked_lines, comment_lines),
        "untyped_table_str_pat": lambda: find_untyped_table_string_patterns(masked_lines, comment_lines),
        "trailing_spaces": lambda: find_trailing_spaces(original_lines),
    }
    detector = detectors.get(rule.count_field)
    if detector is None:
        raise ValueError(f"unsupported canonical count field {rule.count_field!r}")
    message = getattr(rule, "interpretation", f"Matched {rule.rule_id}")
    finding_factory = cast("Callable[..., ScanFinding]", ScanFinding)
    return tuple(
        finding_factory(
            rule_id=rule.rule_id,
            count_field=rule.count_field,
            source_path=Path(relative_path.as_posix()),
            start_line=start_line,
            end_line=end_line,
            excerpt=_source_excerpt(original_lines, start_line, end_line),
            message=str(message),
        )
        for start_line, end_line in detector()
    )

def _build_counts(
    findings: Iterable[ScanFinding],
) -> ScanCounts:
    values: dict[str, int] = dict.fromkeys(_COUNT_FIELDS, 0)
    for finding in findings:
        if not isinstance(finding, ScanFinding):
            raise TypeError("findings must contain only ScanFinding values")
        if finding.count_field not in values:
            raise StaticScanError(
                "GF-WB-SCAN-006",
                (f"Static scan finding refers to unsupported count field {finding.count_field!r}."),
            )
        values[finding.count_field] += 1
    return ScanCounts(**values)


def _write_scan_log(
    path: Path,
    text: str,
    *,
    source_path: Path,
) -> None:
    if not isinstance(path, Path):
        raise TypeError("path must be a Path")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if "\r" in text:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding=_LOG_ENCODING,
                newline="\n",
            ) as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    except OSError as exc:
        raise StaticScanError(
            "GF-WB-SCAN-007",
            "Static-scan evidence could not be written.",
            source_path=source_path,
            evidence_path=path,
            cause=exc,
        ) from exc


def _validate_request(request: StaticScanRequest) -> None:
    if not isinstance(request, StaticScanRequest):
        raise TypeError("request must be a StaticScanRequest")
    _request_project_relative_path(request)
    source_location = _request_source_location(request)
    if not isinstance(request.evidence_path, Path):
        raise TypeError("request.evidence_path must be a Path")
    if source_location == request.evidence_path:
        raise ValueError("source_path and evidence_path must be different")
    _request_max_source_size(request)
    _request_allow_lossy(request)
    if not isinstance(request.rule_set_id, str) or not request.rule_set_id.strip():
        raise ValueError("request.rule_set_id must not be empty")

def _validate_registry(
    registry: ScanRuleRegistry,
    *,
    expected_rule_set_id: str,
) -> None:
    if not isinstance(registry, ScanRuleRegistry):
        raise TypeError("registry must be a ScanRuleRegistry")
    if registry.rule_set_id != expected_rule_set_id:
        raise ValueError("request rule_set_id does not match the supplied registry")
    if not registry.rules:
        raise ValueError("registry must contain at least one rule")

    seen_rule_ids: set[str] = set()
    seen_count_fields: set[str] = set()
    for rule in registry.rules:
        if not isinstance(rule, ScanRule):
            raise TypeError("registry rules must be ScanRule instances")
        if rule.rule_id in seen_rule_ids:
            raise ValueError(f"duplicate static scan rule ID {rule.rule_id!r}")
        if rule.count_field in seen_count_fields:
            raise ValueError("each canonical static scan count field must have one rule owner")
        if rule.count_field not in _COUNT_FIELDS:
            raise ValueError(f"unsupported static scan count field {rule.count_field!r}")
        seen_rule_ids.add(rule.rule_id)
        seen_count_fields.add(rule.count_field)

    if tuple(rule.count_field for rule in registry.rules) != _COUNT_FIELDS:
        raise ValueError("registry count-field order must match ScanCounts")


def _request_source_location(request: _ScanRequestView) -> Path:
    value = getattr(request, "source_location", None)
    if value is None:
        value = getattr(request, "source_path", None)
    if not isinstance(value, Path):
        raise TypeError("request source location must be a Path")
    return value


def _request_project_relative_path(request: _ScanRequestView) -> PurePosixPath:
    value = getattr(request, "project_relative_path", None)
    if value is None:
        source_path = getattr(request, "source_path", None)
        if not isinstance(source_path, Path):
            raise TypeError("request.source_path must be a Path")
        value = PurePosixPath(source_path.as_posix())
    if not isinstance(value, (str, PurePosixPath)):
        raise TypeError("request project-relative path must be text or PurePosixPath")
    return _normalize_project_relative_path(value)


def _request_allow_lossy(request: _ScanRequestView) -> bool:
    policy = getattr(request, "encoding_policy", None)
    if policy is not None:
        if not isinstance(policy, ScanEncodingPolicy):
            raise TypeError("request.encoding_policy must be a ScanEncodingPolicy")
        return policy is ScanEncodingPolicy.DIAGNOSTIC_REPLACEMENT
    value = getattr(request, "allow_lossy_decode", False)
    if not isinstance(value, bool):
        raise TypeError("request.allow_lossy_decode must be a bool")
    return value


def _request_max_source_size(request: _ScanRequestView) -> int:
    value = getattr(request, "max_source_size", None)
    if value is None:
        value = getattr(request, "max_source_bytes", None)
    if type(value) is not int or value <= 0:
        raise ValueError("request source-size limit must be a positive integer")
    return value


def _request_fingerprint_reference(request: _ScanRequestView) -> str | None:
    value = getattr(request, "source_fingerprint_reference", None)
    if value is None:
        value = getattr(request, "fingerprint_reference", None)
    if value is not None and not isinstance(value, str):
        raise TypeError("source fingerprint reference must be a string or None")
    return value


def _registry_version(registry: ScanRuleRegistry) -> str:
    value = getattr(registry, "version", None)
    if value is None:
        value = getattr(registry, "rule_set_version", _RULE_SET_VERSION)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("registry version must be a non-empty string")
    return value


def _build_text_scan_request(
    *,
    relative_path: PurePosixPath,
    rule_set_id: str,
    source_size: int,
) -> _TextScanRequest:
    return _TextScanRequest(
        source_path=Path(relative_path.as_posix()),
        project_relative_path=relative_path,
        evidence_path=Path("scan.txt"),
        rule_set_id=rule_set_id,
        max_source_bytes=source_size,
    )

def _build_scan_result(
    *,
    request: StaticScanRequest,
    registry: ScanRuleRegistry,
    counts: ScanCounts,
    findings: tuple[ScanFinding, ...],
    diagnostics: tuple[ScanDiagnostic, ...],
    encoding_outcome: ScanEncodingOutcome,
    source_size_bytes: int,
) -> StaticScanResult:
    constructor = cast("Callable[..., StaticScanResult]", StaticScanResult)
    parameters = inspect.signature(StaticScanResult).parameters
    if "source_identity" in parameters:
        relative_path = _request_project_relative_path(request)
        return constructor(
            source_identity=getattr(request, "source_identity", relative_path.as_posix()),
            source_path=Path(relative_path.as_posix()),
            completion_state=ScanCompletionState.COMPLETED,
            status=ValidationStatus.FAIL if findings else ValidationStatus.OK,
            rule_set_id=registry.rule_set_id,
            encoding_outcome=encoding_outcome,
            counts=counts,
            findings=findings,
            diagnostics=diagnostics,
            scan_log_path=request.evidence_path,
            source_fingerprint_reference=_request_fingerprint_reference(request),
            bytes_read=source_size_bytes,
        )
    return constructor(
        completion_state=ScanCompletionState.COMPLETED,
        counts=counts,
        findings=findings,
        diagnostics=diagnostics,
        fingerprint_reference=_request_fingerprint_reference(request),
        evidence_path=request.evidence_path,
        rule_set_id=registry.rule_set_id,
        rule_set_version=_registry_version(registry),
        encoding_outcome=encoding_outcome,
        source_size_bytes=source_size_bytes,
    )


def _result_counts(result: StaticScanResult) -> ScanCounts:
    counts = result.counts
    if not isinstance(counts, ScanCounts):
        raise ValueError("completed scan result must contain ScanCounts")
    return counts


def _result_source_size(result: StaticScanResult) -> int:
    value = getattr(result, "bytes_read", None)
    if value is None:
        value = getattr(result, "source_size_bytes", None)
    if type(value) is not int or value < 0:
        raise ValueError("scan result source size must be a non-negative integer")
    return value


def _lossy_encoding_outcome() -> ScanEncodingOutcome:
    value = getattr(ScanEncodingOutcome, "UTF8_LOSSY", None)
    if value is None:
        value = getattr(ScanEncodingOutcome, "UTF8_REPLACEMENT", None)
    if not isinstance(value, ScanEncodingOutcome):
        raise RuntimeError("No lossy UTF-8 encoding outcome is available")
    return value


def _make_scan_diagnostic(
    *,
    code: str,
    message: str,
    line: int | None,
) -> ScanDiagnostic:
    constructor = cast("Callable[..., ScanDiagnostic]", ScanDiagnostic)
    if "error_kind" in inspect.signature(ScanDiagnostic).parameters:
        return constructor(
            code=code if code.startswith("GF-WB-SCAN-") and code[-3:].isdigit() else "GF-WB-SCAN-005",
            error_kind=ErrorKind.OTHER,
            message=message,
            line=line,
        )
    return constructor(code=code, message=message, line=line)


def _view_diagnostics(views: object) -> tuple[object, ...]:
    raw = getattr(views, "diagnostics", None)
    if raw is None:
        raw = getattr(views, "issues", ())
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes, Mapping)):
        raise TypeError("source-view diagnostics must be iterable")
    return tuple(raw)


def _view_lines(views: object, name: str) -> tuple[str, ...]:
    raw = getattr(views, name, None)
    if raw is None:
        text_name = name.removesuffix("_lines")
        raw_text = getattr(views, text_name, None)
        if not isinstance(raw_text, str):
            raise TypeError(f"source views must expose {name}")
        raw = raw_text.splitlines(keepends=True)
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes, Mapping)):
        raise TypeError(f"{name} must be iterable")
    lines = tuple(raw)
    if not all(isinstance(line, str) for line in lines):
        raise TypeError(f"{name} must contain strings")
    return cast("tuple[str, ...]", lines)


def _source_excerpt(lines: tuple[str, ...], start_line: int, end_line: int) -> str:
    """Return bounded source evidence suitable for ``ScanFinding``.

    Pattern detectors may legitimately span very large ``case``/``table``
    blocks.  ``ScanFinding`` intentionally bounds inline evidence, so the
    service must truncate before constructing the domain model rather than
    turning an otherwise valid finding into a fatal static-scan error.
    """

    excerpt = "".join(lines[start_line - 1 : end_line]).rstrip("\r\n")
    if len(excerpt) <= _MAX_EXCERPT_CHARACTERS:
        return excerpt
    return excerpt[: _MAX_EXCERPT_CHARACTERS - 1] + "…"


def _normalize_project_relative_path(
    value: str | PurePosixPath,
) -> PurePosixPath:
    if isinstance(value, PurePosixPath):
        path = value
    elif isinstance(value, str):
        path = PurePosixPath(value.replace("\\", "/"))
    else:
        raise TypeError("project_relative_path must be a string or PurePosixPath")

    if path.is_absolute():
        raise ValueError("project_relative_path must be project-relative")
    if not path.parts or path.as_posix() in {"", "."}:
        raise ValueError("project_relative_path must identify a source file")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("project_relative_path must not contain empty, '.' or '..' segments")
    if path.suffix.casefold() != ".gf":
        raise ValueError("project_relative_path must identify a .gf source file")
    return path


def _coerce_diagnostic(value: object) -> ScanDiagnostic:
    if isinstance(value, ScanDiagnostic):
        return value
    code = getattr(value, "code", "GF-WB-SCAN-LEXICAL-001")
    message = getattr(value, "message", str(value))
    line = getattr(value, "line", None)
    return _make_scan_diagnostic(
        code=str(code),
        message=_bounded_diagnostic(str(message)),
        line=line if isinstance(line, int) and line > 0 else None,
    )

def _sort_diagnostics(
    diagnostics: Iterable[ScanDiagnostic],
) -> tuple[ScanDiagnostic, ...]:
    normalized = tuple(diagnostics)
    if not all(isinstance(diagnostic, ScanDiagnostic) for diagnostic in normalized):
        raise TypeError("diagnostics must contain only ScanDiagnostic values")
    return tuple(
        sorted(
            normalized,
            key=lambda diagnostic: (
                diagnostic.line is None,
                diagnostic.line or 0,
                diagnostic.code,
                diagnostic.message,
            ),
        )
    )


def _counts_mapping(counts: ScanCounts) -> Mapping[str, int]:
    if not isinstance(counts, ScanCounts):
        raise TypeError("counts must be a ScanCounts")
    return {field_name: getattr(counts, field_name) for field_name in _COUNT_FIELDS}


def _group_findings(
    findings: Iterable[ScanFinding],
) -> dict[str, tuple[ScanFinding, ...]]:
    groups: dict[str, list[ScanFinding]] = {}
    for finding in findings:
        if not isinstance(finding, ScanFinding):
            raise TypeError("findings must contain only ScanFinding values")
        groups.setdefault(finding.rule_id, []).append(finding)
    return {rule_id: tuple(values) for rule_id, values in groups.items()}


def _bounded_excerpt(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("excerpt must be a string")
    compact = value.replace("\r", "").replace("\n", "\\n")
    if len(compact) <= _MAX_EXCERPT_CHARACTERS:
        return compact
    return compact[: _MAX_EXCERPT_CHARACTERS - 1] + "…"


def _bounded_diagnostic(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("diagnostic must be a string")
    compact = " ".join(value.split())
    if len(compact) <= _MAX_DIAGNOSTIC_CHARACTERS:
        return compact
    return compact[: _MAX_DIAGNOSTIC_CHARACTERS - 1] + "…"


__all__ = (
    "StaticScanError",
    "render_scan_log",
    "scan_file",
    "scan_text",
)
