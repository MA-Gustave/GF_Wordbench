from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import math
from pathlib import PurePosixPath, PureWindowsPath
import re
from typing import Any, Final, Literal, NotRequired, TypeAlias, TypedDict, cast

SUMMARY_SCHEMA_ID: Final[str] = "gf-wordbench.run-summary"
SUMMARY_SCHEMA_VERSION: Final[str] = "1.0"
RUN_SUMMARY_SCHEMA_ID: Final[str] = SUMMARY_SCHEMA_ID
RUN_SUMMARY_SCHEMA_VERSION: Final[str] = SUMMARY_SCHEMA_VERSION
SUMMARY_SCHEMA_MAJOR: Final[int] = 1
SUMMARY_SCHEMA_MINOR: Final[int] = 0
SUMMARY_PRODUCER_NAME: Final[str] = "gf-wordbench"
SUMMARY_JSON_FILENAME: Final[str] = "summary.json"

ValidationModeValue: TypeAlias = Literal[
    "quick",
    "checkpoint",
    "release",
    "diagnostic",
]
ValidationStatusValue: TypeAlias = Literal[
    "OK",
    "FAIL",
    "ERROR",
    "SKIPPED",
]
OverallStatusValue: TypeAlias = Literal[
    "OK",
    "FAIL",
    "ERROR",
]
DiagnosticClassValue: TypeAlias = Literal[
    "ok",
    "direct",
    "downstream",
    "ambiguous",
    "noise",
    "skipped",
    "framework_error",
]
ErrorKindValue: TypeAlias = Literal[
    "OK",
    "OTHER",
    "TYPE",
    "SYNTAX",
    "INTERNAL",
    "TIMEOUT",
    "SCRIPT",
    "CONFIG",
    "IO",
    "TOOL",
]
ChangeKindValue: TypeAlias = Literal[
    "unchanged",
    "improved",
    "regressed",
    "new",
    "removed",
]
DiffSubjectKindValue: TypeAlias = Literal[
    "file",
    "scenario",
    "run",
]


class ProducerV1(TypedDict):
    name: str
    version: str


class MetadataV1(TypedDict):
    run_id: str
    run_dir: str
    started_at: str
    finished_at: str
    duration_ms: int
    gf_version: str
    mode: ValidationModeValue
    target_file: str | None
    project_id: str
    project_name: str
    project_root: str
    rgl_root: str
    gf_executable: str
    output_root: str
    source_directory: str
    source_glob: str
    gf_path: list[str]
    timeout_sec: int
    max_files: int
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool
    keep_ok_details: bool
    diff_previous: bool


class TotalsV1(TypedDict):
    files_seen: int
    files_included: int
    files_excluded: int
    files_ok: int
    files_fail: int
    files_error: int
    files_skipped: int
    direct_fail: int
    downstream_fail: int
    ambiguous_fail: int
    excluded_noise: int
    scenarios_seen: int
    scenarios_ok: int
    scenarios_fail: int
    scenarios_error: int
    scenarios_skipped: int
    required_scenario_fail: int
    overall_status: OverallStatusValue


class ArtifactsV1(TypedDict):
    summary_json: str
    summary_markdown: str | None
    ai_ready: str | None
    top_errors: str | None
    manifest: str | None
    master_log: str | None
    all_scan_logs: str | None
    all_logs: str | None
    details_dir: str
    raw_dir: str
    compile_logs_dir: str
    scan_logs_dir: str
    scenario_logs_dir: str
    artifacts_dir: str
    gfo_dir: str
    out_dir: str
    pgf_dir: str


class ScanCountsV1(TypedDict):
    single_slash_eq: int
    double_slash_dash: int
    runtime_str_match: int
    untyped_case_str_pat: int
    untyped_table_str_pat: int
    trailing_spaces: int


class FingerprintV1(TypedDict):
    size_bytes: int
    hash_algorithm: str
    hash: str
    last_modified_utc: str


class CompileSummaryV1(TypedDict):
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    error_kind: ErrorKindValue
    first_error: str
    error_detail: str
    stdout_path: str | None
    stderr_path: str | None


class FileResultV1(TypedDict):
    file_path: str
    module_name: str
    status: ValidationStatusValue
    diagnostic_class: DiagnosticClassValue
    is_direct: bool
    blocked_by: list[str]
    scan_counts: ScanCountsV1
    fingerprint: FingerprintV1
    compile_summary: CompileSummaryV1
    scan_log_path: str


class ScenarioSectionV1(TypedDict):
    id: str
    completed: bool


class ScenarioResultV1(TypedDict):
    scenario_id: str
    script_path: str
    required: bool
    status: ValidationStatusValue
    command: list[str]
    working_directory: str
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    stdout_path: str
    stderr_path: str
    normalized_output_path: str | None
    gold_path: str | None
    gold_match: bool | None
    diagnostic_class: DiagnosticClassValue
    error_kind: ErrorKindValue
    primary_message: str
    sections: list[ScenarioSectionV1]
    artifacts: list[str]


class DiffEntryV1(TypedDict):
    subject_kind: DiffSubjectKindValue
    subject_id: str
    previous_status: ValidationStatusValue | OverallStatusValue | None
    current_status: ValidationStatusValue | OverallStatusValue | None
    change_kind: ChangeKindValue
    message: str


class TopErrorV1(TypedDict):
    error_kind: ErrorKindValue
    message: str
    count: int


class SummaryV1(TypedDict):
    schema_id: str
    schema_version: str
    producer: NotRequired[ProducerV1]
    metadata: MetadataV1
    totals: TotalsV1
    artifacts: ArtifactsV1
    file_results: list[FileResultV1]
    scenario_results: list[ScenarioResultV1]
    diff_entries: list[DiffEntryV1]
    top_errors: list[TopErrorV1]


SummaryDocument: TypeAlias = SummaryV1
RunSummaryDocument: TypeAlias = SummaryV1
ProducerDocument: TypeAlias = ProducerV1
MetadataDocument: TypeAlias = MetadataV1
TotalsDocument: TypeAlias = TotalsV1
ArtifactsDocument: TypeAlias = ArtifactsV1
FileResultDocument: TypeAlias = FileResultV1
ScenarioResultDocument: TypeAlias = ScenarioResultV1
DiffEntryDocument: TypeAlias = DiffEntryV1
TopErrorDocument: TypeAlias = TopErrorV1

ROOT_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "schema_id",
    "schema_version",
    "metadata",
    "totals",
    "artifacts",
    "file_results",
    "scenario_results",
    "diff_entries",
    "top_errors",
)
ROOT_OPTIONAL_FIELDS: Final[tuple[str, ...]] = ("producer",)
METADATA_FIELDS: Final[tuple[str, ...]] = (
    "run_id",
    "run_dir",
    "started_at",
    "finished_at",
    "duration_ms",
    "gf_version",
    "mode",
    "target_file",
    "project_id",
    "project_name",
    "project_root",
    "rgl_root",
    "gf_executable",
    "output_root",
    "source_directory",
    "source_glob",
    "gf_path",
    "timeout_sec",
    "max_files",
    "skip_version_probe",
    "no_compile",
    "emit_cpu_stats",
    "keep_ok_details",
    "diff_previous",
)
TOTALS_FIELDS: Final[tuple[str, ...]] = (
    "files_seen",
    "files_included",
    "files_excluded",
    "files_ok",
    "files_fail",
    "files_error",
    "files_skipped",
    "direct_fail",
    "downstream_fail",
    "ambiguous_fail",
    "excluded_noise",
    "scenarios_seen",
    "scenarios_ok",
    "scenarios_fail",
    "scenarios_error",
    "scenarios_skipped",
    "required_scenario_fail",
    "overall_status",
)
ARTIFACT_FIELDS: Final[tuple[str, ...]] = (
    "summary_json",
    "summary_markdown",
    "ai_ready",
    "top_errors",
    "manifest",
    "master_log",
    "all_scan_logs",
    "all_logs",
    "details_dir",
    "raw_dir",
    "compile_logs_dir",
    "scan_logs_dir",
    "scenario_logs_dir",
    "artifacts_dir",
    "gfo_dir",
    "out_dir",
    "pgf_dir",
)
FILE_RESULT_FIELDS: Final[tuple[str, ...]] = (
    "file_path",
    "module_name",
    "status",
    "diagnostic_class",
    "is_direct",
    "blocked_by",
    "scan_counts",
    "fingerprint",
    "compile_summary",
    "scan_log_path",
)
SCAN_COUNT_FIELDS: Final[tuple[str, ...]] = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
)
FINGERPRINT_FIELDS: Final[tuple[str, ...]] = (
    "size_bytes",
    "hash_algorithm",
    "hash",
    "last_modified_utc",
)
COMPILE_SUMMARY_FIELDS: Final[tuple[str, ...]] = (
    "exit_code",
    "timed_out",
    "duration_ms",
    "error_kind",
    "first_error",
    "error_detail",
    "stdout_path",
    "stderr_path",
)
SCENARIO_RESULT_FIELDS: Final[tuple[str, ...]] = (
    "scenario_id",
    "script_path",
    "required",
    "status",
    "command",
    "working_directory",
    "exit_code",
    "timed_out",
    "duration_ms",
    "stdout_path",
    "stderr_path",
    "normalized_output_path",
    "gold_path",
    "gold_match",
    "diagnostic_class",
    "error_kind",
    "primary_message",
    "sections",
    "artifacts",
)
SCENARIO_SECTION_FIELDS: Final[tuple[str, ...]] = (
    "id",
    "completed",
)
DIFF_ENTRY_FIELDS: Final[tuple[str, ...]] = (
    "subject_kind",
    "subject_id",
    "previous_status",
    "current_status",
    "change_kind",
    "message",
)
TOP_ERROR_FIELDS: Final[tuple[str, ...]] = (
    "error_kind",
    "message",
    "count",
)

VALIDATION_MODES: Final[frozenset[str]] = frozenset(
    {"quick", "checkpoint", "release", "diagnostic"}
)
VALIDATION_STATUSES: Final[frozenset[str]] = frozenset({"OK", "FAIL", "ERROR", "SKIPPED"})
OVERALL_STATUSES: Final[frozenset[str]] = frozenset({"OK", "FAIL", "ERROR"})
DIAGNOSTIC_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "ok",
        "direct",
        "downstream",
        "ambiguous",
        "noise",
        "skipped",
        "framework_error",
    }
)
ERROR_KINDS: Final[frozenset[str]] = frozenset(
    {
        "OK",
        "OTHER",
        "TYPE",
        "SYNTAX",
        "INTERNAL",
        "TIMEOUT",
        "SCRIPT",
        "CONFIG",
        "IO",
        "TOOL",
    }
)
CHANGE_KINDS: Final[frozenset[str]] = frozenset(
    {"unchanged", "improved", "regressed", "new", "removed"}
)
DIFF_SUBJECT_KINDS: Final[frozenset[str]] = frozenset({"file", "scenario", "run"})
DIFF_CHANGE_ORDER: Final[Mapping[str, int]] = {
    "regressed": 0,
    "new": 1,
    "improved": 2,
    "removed": 3,
    "unchanged": 4,
}
_RUN_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9]{8}_[0-9]{6}(?:_[0-9]{2,})?$")
_SCHEMA_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_PROJECT_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


@dataclass(frozen=True, slots=True, order=True)
class SummaryV1Issue:
    path: str
    code: str
    message: str

    def __post_init__(self) -> None:
        for name in ("path", "code", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value:
                raise ValueError(f"{name} must not be empty")
            if "\x00" in value:
                raise ValueError(f"{name} must not contain NUL")


class SummaryV1ValidationError(ValueError):
    def __init__(self, issues: Sequence[SummaryV1Issue]) -> None:
        prepared = tuple(issues)
        if not prepared:
            raise ValueError("issues must not be empty")
        self.issues = prepared
        preview = "; ".join(f"{issue.path}: {issue.message}" for issue in prepared[:8])
        if len(prepared) > 8:
            preview += f"; and {len(prepared) - 8} more"
        super().__init__(preview)


def new_summary_v1(
    *,
    metadata: MetadataV1,
    totals: TotalsV1,
    artifacts: ArtifactsV1,
    file_results: Sequence[FileResultV1] = (),
    scenario_results: Sequence[ScenarioResultV1] = (),
    diff_entries: Sequence[DiffEntryV1] = (),
    top_errors: Sequence[TopErrorV1] = (),
    producer: ProducerV1 | None = None,
    canonicalize: bool = True,
    validate: bool = True,
) -> SummaryV1:
    document: dict[str, Any] = {
        "schema_id": SUMMARY_SCHEMA_ID,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "metadata": deepcopy(dict(metadata)),
        "totals": deepcopy(dict(totals)),
        "artifacts": deepcopy(dict(artifacts)),
        "file_results": deepcopy(list(file_results)),
        "scenario_results": deepcopy(list(scenario_results)),
        "diff_entries": deepcopy(list(diff_entries)),
        "top_errors": deepcopy(list(top_errors)),
    }
    if producer is not None:
        document["producer"] = deepcopy(dict(producer))
    result = cast("SummaryV1", document)
    if canonicalize:
        result = canonicalize_summary_v1(result, validate=False)
    if validate:
        return require_summary_v1(result)
    return result


def schema_identity() -> tuple[str, str]:
    return SUMMARY_SCHEMA_ID, SUMMARY_SCHEMA_VERSION


def parse_schema_version(value: str) -> tuple[int, int]:
    if not isinstance(value, str):
        raise TypeError("schema version must be a string")
    match = _SCHEMA_VERSION_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("schema version must use MAJOR.MINOR")
    return int(match.group(1)), int(match.group(2))


def is_supported_schema_version(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        major, _ = parse_schema_version(value)
    except ValueError:
        return False
    return major == SUMMARY_SCHEMA_MAJOR


def validate_summary_v1(
    document: object,
    *,
    strict: bool = True,
    check_ordering: bool = True,
) -> tuple[SummaryV1Issue, ...]:
    if type(strict) is not bool:
        raise TypeError("strict must be a boolean")
    if type(check_ordering) is not bool:
        raise TypeError("check_ordering must be a boolean")

    issues: list[SummaryV1Issue] = []
    root = _mapping(document, "$", issues)
    if root is None:
        return tuple(issues)

    _fields(
        root,
        "$",
        ROOT_REQUIRED_FIELDS,
        ROOT_OPTIONAL_FIELDS,
        strict,
        issues,
    )
    _literal(
        root.get("schema_id"),
        "$.schema_id",
        frozenset({SUMMARY_SCHEMA_ID}),
        issues,
    )
    version = _string(root.get("schema_version"), "$.schema_version", issues)
    if version is not None:
        try:
            major, minor = parse_schema_version(version)
        except ValueError as exc:
            _issue(issues, "$.schema_version", "invalid_version", str(exc))
        else:
            if major != SUMMARY_SCHEMA_MAJOR:
                _issue(
                    issues,
                    "$.schema_version",
                    "unsupported_major",
                    f"unsupported summary schema major version {major}",
                )
            elif minor != SUMMARY_SCHEMA_MINOR:
                _issue(
                    issues,
                    "$.schema_version",
                    "noncanonical_minor",
                    f"canonical writer version is {SUMMARY_SCHEMA_VERSION}",
                )

    if "producer" in root:
        _validate_producer(root.get("producer"), "$.producer", strict, issues)
    _validate_metadata(root.get("metadata"), "$.metadata", strict, issues)
    _validate_totals(root.get("totals"), "$.totals", strict, issues)
    _validate_artifacts(root.get("artifacts"), "$.artifacts", strict, issues)
    _validate_file_results(
        root.get("file_results"),
        "$.file_results",
        strict,
        check_ordering,
        issues,
    )
    _validate_scenario_results(
        root.get("scenario_results"),
        "$.scenario_results",
        strict,
        issues,
    )
    _validate_diff_entries(
        root.get("diff_entries"),
        "$.diff_entries",
        strict,
        check_ordering,
        issues,
    )
    _validate_top_errors(
        root.get("top_errors"),
        "$.top_errors",
        strict,
        check_ordering,
        issues,
    )
    _validate_cross_invariants(root, issues)
    return tuple(sorted(set(issues)))


def validate_summary_document(document: object) -> None:
    """Strictly validate one canonical persisted summary document.

    This writer-facing entry point rejects schema issues, non-canonical
    collection ordering, unknown fields, and values that cannot be represented
    safely as JSON.  Use :func:`validate_summary_v1` when callers need the
    issue-producing validation result instead of an exception.
    """
    require_summary_v1(
        document,
        strict=True,
        check_ordering=True,
    )
    assert_summary_v1_json_safe(document)


def require_summary_v1(
    document: object,
    *,
    strict: bool = True,
    check_ordering: bool = True,
) -> SummaryV1:
    issues = validate_summary_v1(
        document,
        strict=strict,
        check_ordering=check_ordering,
    )
    if issues:
        raise SummaryV1ValidationError(issues)
    return cast("SummaryV1", document)


def is_summary_v1(
    document: object,
    *,
    strict: bool = True,
    check_ordering: bool = True,
) -> bool:
    return not validate_summary_v1(
        document,
        strict=strict,
        check_ordering=check_ordering,
    )


def canonicalize_summary_v1(
    document: Mapping[str, Any],
    *,
    validate: bool = True,
) -> SummaryV1:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    copied = deepcopy(dict(document))

    file_results = copied.get("file_results")
    if isinstance(file_results, list):
        file_results.sort(
            key=lambda item: (
                (
                    str(item.get("file_path", "")).casefold(),
                    str(item.get("file_path", "")),
                )
                if isinstance(item, Mapping)
                else ("", "")
            )
        )

    diff_entries = copied.get("diff_entries")
    if isinstance(diff_entries, list):
        diff_entries.sort(
            key=lambda item: (
                (
                    DIFF_CHANGE_ORDER.get(
                        str(item.get("change_kind", "")),
                        len(DIFF_CHANGE_ORDER),
                    ),
                    str(item.get("subject_kind", "")).casefold(),
                    str(item.get("subject_id", "")).casefold(),
                    str(item.get("subject_id", "")),
                )
                if isinstance(item, Mapping)
                else (len(DIFF_CHANGE_ORDER), "", "", "")
            )
        )

    top_errors = copied.get("top_errors")
    if isinstance(top_errors, list):
        top_errors.sort(
            key=lambda item: (
                -int(item.get("count", 0))
                if isinstance(item, Mapping) and type(item.get("count")) is int
                else 0,
                str(item.get("message", "")).casefold() if isinstance(item, Mapping) else "",
                str(item.get("message", "")) if isinstance(item, Mapping) else "",
            )
        )

    result = cast("SummaryV1", copied)
    if validate:
        return require_summary_v1(result)
    return result


def _validate_producer(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, ("name", "version"), (), strict, issues)
    name = _nonempty_string(item.get("name"), f"{path}.name", issues)
    if name is not None and name != SUMMARY_PRODUCER_NAME:
        _issue(
            issues,
            f"{path}.name",
            "unexpected_producer",
            f"canonical producer name is {SUMMARY_PRODUCER_NAME!r}",
        )
    _nonempty_string(item.get("version"), f"{path}.version", issues)


def _validate_metadata(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, METADATA_FIELDS, (), strict, issues)

    run_id = _nonempty_string(item.get("run_id"), f"{path}.run_id", issues)
    if run_id is not None and _RUN_ID_PATTERN.fullmatch(run_id) is None:
        _issue(
            issues,
            f"{path}.run_id",
            "invalid_run_id",
            "run_id must use YYYYMMDD_HHMMSS with an optional numeric suffix",
        )

    run_dir = _nonempty_string(item.get("run_dir"), f"{path}.run_dir", issues)
    if run_dir is not None:
        _canonical_separators(run_dir, f"{path}.run_dir", issues)

    started = _utc_timestamp(
        item.get("started_at"),
        f"{path}.started_at",
        issues,
    )
    finished = _utc_timestamp(
        item.get("finished_at"),
        f"{path}.finished_at",
        issues,
    )
    if started is not None and finished is not None and finished < started:
        _issue(
            issues,
            f"{path}.finished_at",
            "time_order",
            "finished_at must not precede started_at",
        )

    _non_negative_integer(
        item.get("duration_ms"),
        f"{path}.duration_ms",
        issues,
    )
    _string(item.get("gf_version"), f"{path}.gf_version", issues)
    _literal(
        item.get("mode"),
        f"{path}.mode",
        VALIDATION_MODES,
        issues,
    )

    target = item.get("target_file")
    if target is not None:
        target_text = _nonempty_string(
            target,
            f"{path}.target_file",
            issues,
        )
        if target_text is not None:
            _portable_relative_path(
                target_text,
                f"{path}.target_file",
                issues,
            )

    project_id = _nonempty_string(
        item.get("project_id"),
        f"{path}.project_id",
        issues,
    )
    if project_id is not None and _PROJECT_ID_PATTERN.fullmatch(project_id) is None:
        _issue(
            issues,
            f"{path}.project_id",
            "invalid_project_id",
            "project_id must be portable lowercase ASCII with hyphens",
        )

    _nonempty_string(
        item.get("project_name"),
        f"{path}.project_name",
        issues,
    )

    for field_name in (
        "project_root",
        "rgl_root",
        "gf_executable",
        "output_root",
    ):
        text = _nonempty_string(
            item.get(field_name),
            f"{path}.{field_name}",
            issues,
        )
        if text is not None:
            _canonical_separators(
                text,
                f"{path}.{field_name}",
                issues,
            )

    source_directory = _nonempty_string(
        item.get("source_directory"),
        f"{path}.source_directory",
        issues,
    )
    if source_directory is not None:
        _portable_relative_path(
            source_directory,
            f"{path}.source_directory",
            issues,
        )

    source_glob = _nonempty_string(
        item.get("source_glob"),
        f"{path}.source_glob",
        issues,
    )
    if source_glob is not None and ("/" in source_glob or "\\" in source_glob):
        _issue(
            issues,
            f"{path}.source_glob",
            "invalid_glob",
            "source_glob must not contain path separators",
        )

    gf_path = _list(item.get("gf_path"), f"{path}.gf_path", issues)
    if gf_path is not None:
        seen: set[str] = set()
        for index, entry in enumerate(gf_path):
            entry_path = f"{path}.gf_path[{index}]"
            text = _nonempty_string(entry, entry_path, issues)
            if text is None:
                continue
            _canonical_separators(text, entry_path, issues)
            key = text.casefold()
            if key in seen:
                _issue(
                    issues,
                    entry_path,
                    "duplicate_path",
                    "gf_path entries must be unique",
                )
            seen.add(key)

    _positive_integer(
        item.get("timeout_sec"),
        f"{path}.timeout_sec",
        issues,
    )
    _non_negative_integer(
        item.get("max_files"),
        f"{path}.max_files",
        issues,
    )
    for field_name in (
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
        "keep_ok_details",
        "diff_previous",
    ):
        _boolean(item.get(field_name), f"{path}.{field_name}", issues)


def _validate_totals(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, TOTALS_FIELDS, (), strict, issues)
    count_fields = tuple(
        field_name for field_name in TOTALS_FIELDS if field_name != "overall_status"
    )
    for field_name in count_fields:
        _non_negative_integer(
            item.get(field_name),
            f"{path}.{field_name}",
            issues,
        )
    _literal(
        item.get("overall_status"),
        f"{path}.overall_status",
        OVERALL_STATUSES,
        issues,
    )

    _count_invariant(
        item,
        "files_seen",
        ("files_included", "files_excluded"),
        path,
        issues,
    )
    _count_invariant(
        item,
        "files_included",
        (
            "files_ok",
            "files_fail",
            "files_error",
            "files_skipped",
        ),
        path,
        issues,
    )
    _count_invariant(
        item,
        "scenarios_seen",
        (
            "scenarios_ok",
            "scenarios_fail",
            "scenarios_error",
            "scenarios_skipped",
        ),
        path,
        issues,
    )


def _validate_artifacts(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, ARTIFACT_FIELDS, (), strict, issues)
    for field_name in ARTIFACT_FIELDS:
        value = item.get(field_name)
        field_path = f"{path}.{field_name}"
        if value is None:
            if field_name in {
                "summary_json",
                "details_dir",
                "raw_dir",
                "compile_logs_dir",
                "scan_logs_dir",
                "scenario_logs_dir",
                "artifacts_dir",
                "gfo_dir",
                "out_dir",
                "pgf_dir",
            }:
                _issue(
                    issues,
                    field_path,
                    "null_required_path",
                    "required artifact path must not be null",
                )
            continue
        text = _nonempty_string(value, field_path, issues)
        if text is not None:
            _run_relative_path(text, field_path, issues)
    if item.get("summary_json") != SUMMARY_JSON_FILENAME:
        _issue(
            issues,
            f"{path}.summary_json",
            "noncanonical_summary_path",
            f"summary_json must be {SUMMARY_JSON_FILENAME!r}",
        )


def _validate_file_results(
    value: object,
    path: str,
    strict: bool,
    check_ordering: bool,
    issues: list[SummaryV1Issue],
) -> None:
    items = _list(value, path, issues)
    if items is None:
        return
    paths: list[str] = []
    identities: set[str] = set()
    for index, value_item in enumerate(items):
        item_path = f"{path}[{index}]"
        item = _mapping(value_item, item_path, issues)
        if item is None:
            continue
        _fields(item, item_path, FILE_RESULT_FIELDS, (), strict, issues)

        file_path = _nonempty_string(
            item.get("file_path"),
            f"{item_path}.file_path",
            issues,
        )
        if file_path is not None:
            _portable_relative_path(
                file_path,
                f"{item_path}.file_path",
                issues,
            )
            paths.append(file_path)
            key = file_path.casefold()
            if key in identities:
                _issue(
                    issues,
                    f"{item_path}.file_path",
                    "duplicate_identity",
                    "file_results must have unique file_path values",
                )
            identities.add(key)

        _nonempty_string(
            item.get("module_name"),
            f"{item_path}.module_name",
            issues,
        )
        _literal(
            item.get("status"),
            f"{item_path}.status",
            VALIDATION_STATUSES,
            issues,
        )
        diagnostic_class = _literal(
            item.get("diagnostic_class"),
            f"{item_path}.diagnostic_class",
            DIAGNOSTIC_CLASSES,
            issues,
        )
        is_direct = _boolean(
            item.get("is_direct"),
            f"{item_path}.is_direct",
            issues,
        )
        if diagnostic_class == "direct" and is_direct is not True:
            _issue(
                issues,
                f"{item_path}.is_direct",
                "direct_compatibility",
                "diagnostic_class direct requires is_direct true",
            )
        if diagnostic_class is not None and diagnostic_class != "direct" and is_direct is True:
            _issue(
                issues,
                f"{item_path}.is_direct",
                "direct_compatibility",
                "is_direct true is reserved for diagnostic_class direct",
            )

        blockers = _list(
            item.get("blocked_by"),
            f"{item_path}.blocked_by",
            issues,
        )
        if blockers is not None:
            seen: set[str] = set()
            for blocker_index, blocker in enumerate(blockers):
                blocker_path = f"{item_path}.blocked_by[{blocker_index}]"
                text = _nonempty_string(blocker, blocker_path, issues)
                if text is None:
                    continue
                _portable_relative_path(text, blocker_path, issues)
                key = text.casefold()
                if key in seen:
                    _issue(
                        issues,
                        blocker_path,
                        "duplicate_blocker",
                        "blocked_by values must be unique",
                    )
                seen.add(key)

        _validate_scan_counts(
            item.get("scan_counts"),
            f"{item_path}.scan_counts",
            strict,
            issues,
        )
        _validate_fingerprint(
            item.get("fingerprint"),
            f"{item_path}.fingerprint",
            strict,
            issues,
        )
        _validate_compile_summary(
            item.get("compile_summary"),
            f"{item_path}.compile_summary",
            strict,
            issues,
        )
        scan_log = _nonempty_string(
            item.get("scan_log_path"),
            f"{item_path}.scan_log_path",
            issues,
        )
        if scan_log is not None:
            _run_relative_path(
                scan_log,
                f"{item_path}.scan_log_path",
                issues,
            )

    if check_ordering and paths != sorted(
        paths,
        key=lambda item: (item.casefold(), item),
    ):
        _issue(
            issues,
            path,
            "noncanonical_order",
            "file_results must be ordered by normalized file_path",
        )


def _validate_scan_counts(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, SCAN_COUNT_FIELDS, (), strict, issues)
    for field_name in SCAN_COUNT_FIELDS:
        _non_negative_integer(
            item.get(field_name),
            f"{path}.{field_name}",
            issues,
        )


def _validate_fingerprint(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, FINGERPRINT_FIELDS, (), strict, issues)
    _non_negative_integer(
        item.get("size_bytes"),
        f"{path}.size_bytes",
        issues,
    )
    algorithm = _literal(
        item.get("hash_algorithm"),
        f"{path}.hash_algorithm",
        frozenset({"sha256"}),
        issues,
    )
    digest = _string(item.get("hash"), f"{path}.hash", issues)
    if algorithm == "sha256" and digest is not None and _SHA256_PATTERN.fullmatch(digest) is None:
        _issue(
            issues,
            f"{path}.hash",
            "invalid_sha256",
            "hash must be a full lowercase SHA-256 hexadecimal digest",
        )
    _utc_timestamp(
        item.get("last_modified_utc"),
        f"{path}.last_modified_utc",
        issues,
    )


def _validate_compile_summary(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    item = _mapping(value, path, issues)
    if item is None:
        return
    _fields(item, path, COMPILE_SUMMARY_FIELDS, (), strict, issues)
    _optional_integer(item.get("exit_code"), f"{path}.exit_code", issues)
    timed_out = _boolean(
        item.get("timed_out"),
        f"{path}.timed_out",
        issues,
    )
    _non_negative_integer(
        item.get("duration_ms"),
        f"{path}.duration_ms",
        issues,
    )
    error_kind = _literal(
        item.get("error_kind"),
        f"{path}.error_kind",
        ERROR_KINDS,
        issues,
    )
    _string(item.get("first_error"), f"{path}.first_error", issues)
    _string(item.get("error_detail"), f"{path}.error_detail", issues)
    for field_name in ("stdout_path", "stderr_path"):
        field_value = item.get(field_name)
        if field_value is None:
            continue
        text = _nonempty_string(
            field_value,
            f"{path}.{field_name}",
            issues,
        )
        if text is not None:
            _run_relative_path(
                text,
                f"{path}.{field_name}",
                issues,
            )
    if timed_out is True and error_kind != "TIMEOUT":
        _issue(
            issues,
            f"{path}.error_kind",
            "timeout_kind",
            "timed_out compile evidence requires error_kind TIMEOUT",
        )


def _validate_scenario_results(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    items = _list(value, path, issues)
    if items is None:
        return
    identities: set[str] = set()
    for index, value_item in enumerate(items):
        item_path = f"{path}[{index}]"
        item = _mapping(value_item, item_path, issues)
        if item is None:
            continue
        _fields(
            item,
            item_path,
            SCENARIO_RESULT_FIELDS,
            (),
            strict,
            issues,
        )

        scenario_id = _nonempty_string(
            item.get("scenario_id"),
            f"{item_path}.scenario_id",
            issues,
        )
        if scenario_id is not None:
            key = scenario_id.casefold()
            if key in identities:
                _issue(
                    issues,
                    f"{item_path}.scenario_id",
                    "duplicate_identity",
                    "scenario_results must have unique scenario_id values",
                )
            identities.add(key)

        script_path = _nonempty_string(
            item.get("script_path"),
            f"{item_path}.script_path",
            issues,
        )
        if script_path is not None:
            _portable_relative_path(
                script_path,
                f"{item_path}.script_path",
                issues,
            )

        required = _boolean(
            item.get("required"),
            f"{item_path}.required",
            issues,
        )
        status = _literal(
            item.get("status"),
            f"{item_path}.status",
            VALIDATION_STATUSES,
            issues,
        )

        command = _list(
            item.get("command"),
            f"{item_path}.command",
            issues,
        )
        if command is not None:
            if not command and status != "SKIPPED":
                _issue(
                    issues,
                    f"{item_path}.command",
                    "empty_command",
                    "executed scenario command must not be empty",
                )
            for command_index, argument in enumerate(command):
                _string(
                    argument,
                    f"{item_path}.command[{command_index}]",
                    issues,
                )

        working_directory = _nonempty_string(
            item.get("working_directory"),
            f"{item_path}.working_directory",
            issues,
        )
        if working_directory is not None:
            _canonical_separators(
                working_directory,
                f"{item_path}.working_directory",
                issues,
            )

        _optional_integer(
            item.get("exit_code"),
            f"{item_path}.exit_code",
            issues,
        )
        timed_out = _boolean(
            item.get("timed_out"),
            f"{item_path}.timed_out",
            issues,
        )
        _non_negative_integer(
            item.get("duration_ms"),
            f"{item_path}.duration_ms",
            issues,
        )

        for field_name in ("stdout_path", "stderr_path"):
            text = _nonempty_string(
                item.get(field_name),
                f"{item_path}.{field_name}",
                issues,
            )
            if text is not None:
                _run_relative_path(
                    text,
                    f"{item_path}.{field_name}",
                    issues,
                )

        normalized = item.get("normalized_output_path")
        if normalized is not None:
            text = _nonempty_string(
                normalized,
                f"{item_path}.normalized_output_path",
                issues,
            )
            if text is not None:
                _run_relative_path(
                    text,
                    f"{item_path}.normalized_output_path",
                    issues,
                )

        gold_path = item.get("gold_path")
        if gold_path is not None:
            text = _nonempty_string(
                gold_path,
                f"{item_path}.gold_path",
                issues,
            )
            if text is not None:
                _portable_relative_path(
                    text,
                    f"{item_path}.gold_path",
                    issues,
                )

        gold_match = _optional_boolean(
            item.get("gold_match"),
            f"{item_path}.gold_match",
            issues,
        )
        diagnostic_class = _literal(
            item.get("diagnostic_class"),
            f"{item_path}.diagnostic_class",
            DIAGNOSTIC_CLASSES,
            issues,
        )
        error_kind = _literal(
            item.get("error_kind"),
            f"{item_path}.error_kind",
            ERROR_KINDS,
            issues,
        )
        _string(
            item.get("primary_message"),
            f"{item_path}.primary_message",
            issues,
        )
        _validate_sections(
            item.get("sections"),
            f"{item_path}.sections",
            strict,
            issues,
        )
        artifacts = _list(
            item.get("artifacts"),
            f"{item_path}.artifacts",
            issues,
        )
        if artifacts is not None:
            seen_artifacts: set[str] = set()
            for artifact_index, artifact in enumerate(artifacts):
                artifact_path = f"{item_path}.artifacts[{artifact_index}]"
                text = _nonempty_string(
                    artifact,
                    artifact_path,
                    issues,
                )
                if text is None:
                    continue
                _run_relative_path(text, artifact_path, issues)
                key = text.casefold()
                if key in seen_artifacts:
                    _issue(
                        issues,
                        artifact_path,
                        "duplicate_artifact",
                        "scenario artifacts must be unique",
                    )
                seen_artifacts.add(key)

        if timed_out is True:
            if status != "ERROR":
                _issue(
                    issues,
                    f"{item_path}.status",
                    "timeout_status",
                    "timed-out scenario requires status ERROR",
                )
            if error_kind != "TIMEOUT":
                _issue(
                    issues,
                    f"{item_path}.error_kind",
                    "timeout_kind",
                    "timed-out scenario requires error_kind TIMEOUT",
                )

        if status == "OK":
            if error_kind != "OK":
                _issue(
                    issues,
                    f"{item_path}.error_kind",
                    "success_kind",
                    "scenario status OK requires error_kind OK",
                )
            if diagnostic_class != "ok":
                _issue(
                    issues,
                    f"{item_path}.diagnostic_class",
                    "success_class",
                    "scenario status OK requires diagnostic_class ok",
                )

        if required is True and gold_path is None and gold_match is True:
            _issue(
                issues,
                f"{item_path}.gold_match",
                "gold_without_path",
                "gold_match true requires a gold_path",
            )


def _validate_sections(
    value: object,
    path: str,
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    items = _list(value, path, issues)
    if items is None:
        return
    identities: set[str] = set()
    for index, value_item in enumerate(items):
        item_path = f"{path}[{index}]"
        item = _mapping(value_item, item_path, issues)
        if item is None:
            continue
        _fields(
            item,
            item_path,
            SCENARIO_SECTION_FIELDS,
            (),
            strict,
            issues,
        )
        section_id = _nonempty_string(
            item.get("id"),
            f"{item_path}.id",
            issues,
        )
        if section_id is not None:
            if section_id in identities:
                _issue(
                    issues,
                    f"{item_path}.id",
                    "duplicate_section",
                    "section IDs must be unique",
                )
            identities.add(section_id)
        _boolean(
            item.get("completed"),
            f"{item_path}.completed",
            issues,
        )


def _validate_diff_entries(
    value: object,
    path: str,
    strict: bool,
    check_ordering: bool,
    issues: list[SummaryV1Issue],
) -> None:
    items = _list(value, path, issues)
    if items is None:
        return
    identities: set[tuple[str, str]] = set()
    sortable: list[tuple[int, str, str, str]] = []
    for index, value_item in enumerate(items):
        item_path = f"{path}[{index}]"
        item = _mapping(value_item, item_path, issues)
        if item is None:
            continue
        _fields(item, item_path, DIFF_ENTRY_FIELDS, (), strict, issues)
        subject_kind = _literal(
            item.get("subject_kind"),
            f"{item_path}.subject_kind",
            DIFF_SUBJECT_KINDS,
            issues,
        )
        subject_id = _nonempty_string(
            item.get("subject_id"),
            f"{item_path}.subject_id",
            issues,
        )
        if subject_kind == "file" and subject_id is not None:
            _portable_relative_path(
                subject_id,
                f"{item_path}.subject_id",
                issues,
            )
        if subject_kind is not None and subject_id is not None:
            identity = (subject_kind, subject_id.casefold())
            if identity in identities:
                _issue(
                    issues,
                    item_path,
                    "duplicate_identity",
                    "diff entries must have unique subject identities",
                )
            identities.add(identity)

        _nullable_status(
            item.get("previous_status"),
            f"{item_path}.previous_status",
            issues,
        )
        _nullable_status(
            item.get("current_status"),
            f"{item_path}.current_status",
            issues,
        )
        change_kind = _literal(
            item.get("change_kind"),
            f"{item_path}.change_kind",
            CHANGE_KINDS,
            issues,
        )
        _string(item.get("message"), f"{item_path}.message", issues)

        if subject_kind is not None and subject_id is not None and change_kind is not None:
            sortable.append(
                (
                    DIFF_CHANGE_ORDER[change_kind],
                    subject_kind.casefold(),
                    subject_id.casefold(),
                    subject_id,
                )
            )

    if check_ordering and sortable != sorted(sortable):
        _issue(
            issues,
            path,
            "noncanonical_order",
            "diff_entries must use change severity rank then identity",
        )


def _validate_top_errors(
    value: object,
    path: str,
    strict: bool,
    check_ordering: bool,
    issues: list[SummaryV1Issue],
) -> None:
    items = _list(value, path, issues)
    if items is None:
        return
    sortable: list[tuple[int, str, str]] = []
    identities: set[tuple[str, str]] = set()
    for index, value_item in enumerate(items):
        item_path = f"{path}[{index}]"
        item = _mapping(value_item, item_path, issues)
        if item is None:
            continue
        _fields(item, item_path, TOP_ERROR_FIELDS, (), strict, issues)
        error_kind = _literal(
            item.get("error_kind"),
            f"{item_path}.error_kind",
            ERROR_KINDS,
            issues,
        )
        message = _nonempty_string(
            item.get("message"),
            f"{item_path}.message",
            issues,
        )
        count = _positive_integer(
            item.get("count"),
            f"{item_path}.count",
            issues,
        )
        if error_kind is not None and message is not None:
            identity = (error_kind, message.casefold())
            if identity in identities:
                _issue(
                    issues,
                    item_path,
                    "duplicate_top_error",
                    "top-error identities must be unique",
                )
            identities.add(identity)
        if count is not None and message is not None:
            sortable.append((-count, message.casefold(), message))

    if check_ordering and sortable != sorted(sortable):
        _issue(
            issues,
            path,
            "noncanonical_order",
            "top_errors must be ordered by descending count then message",
        )


def _validate_cross_invariants(
    root: Mapping[str, Any],
    issues: list[SummaryV1Issue],
) -> None:
    totals = root.get("totals")
    file_results = root.get("file_results")
    scenario_results = root.get("scenario_results")

    if isinstance(totals, Mapping) and isinstance(file_results, list):
        counts = {
            "OK": 0,
            "FAIL": 0,
            "ERROR": 0,
            "SKIPPED": 0,
        }
        direct = 0
        downstream = 0
        ambiguous = 0
        noise = 0
        valid = True
        for item in file_results:
            if not isinstance(item, Mapping):
                valid = False
                continue
            status = item.get("status")
            diagnostic_class = item.get("diagnostic_class")
            if status not in counts:
                valid = False
            else:
                counts[cast("str", status)] += 1
            if diagnostic_class == "direct":
                direct += 1
            elif diagnostic_class == "downstream":
                downstream += 1
            elif diagnostic_class in {"ambiguous", "framework_error"}:
                ambiguous += 1
            elif diagnostic_class == "noise":
                noise += 1
        if valid:
            expected = {
                "files_ok": counts["OK"],
                "files_fail": counts["FAIL"],
                "files_error": counts["ERROR"],
                "files_skipped": counts["SKIPPED"],
                "direct_fail": direct,
                "downstream_fail": downstream,
                "ambiguous_fail": ambiguous,
                "excluded_noise": noise,
            }
            for field_name, expected_value in expected.items():
                actual = totals.get(field_name)
                if type(actual) is int and actual != expected_value:
                    _issue(
                        issues,
                        f"$.totals.{field_name}",
                        "result_count_mismatch",
                        f"expected {expected_value} from file_results",
                    )

    if isinstance(totals, Mapping) and isinstance(
        scenario_results,
        list,
    ):
        counts = {
            "OK": 0,
            "FAIL": 0,
            "ERROR": 0,
            "SKIPPED": 0,
        }
        required_fail = 0
        valid = True
        for item in scenario_results:
            if not isinstance(item, Mapping):
                valid = False
                continue
            status = item.get("status")
            if status not in counts:
                valid = False
                continue
            counts[cast("str", status)] += 1
            if item.get("required") is True and status in {
                "FAIL",
                "ERROR",
            }:
                required_fail += 1
        if valid:
            expected = {
                "scenarios_seen": len(scenario_results),
                "scenarios_ok": counts["OK"],
                "scenarios_fail": counts["FAIL"],
                "scenarios_error": counts["ERROR"],
                "scenarios_skipped": counts["SKIPPED"],
                "required_scenario_fail": required_fail,
            }
            for field_name, expected_value in expected.items():
                actual = totals.get(field_name)
                if type(actual) is int and actual != expected_value:
                    _issue(
                        issues,
                        f"$.totals.{field_name}",
                        "result_count_mismatch",
                        f"expected {expected_value} from scenario_results",
                    )


def _fields(
    mapping: Mapping[str, Any],
    path: str,
    required: Sequence[str],
    optional: Sequence[str],
    strict: bool,
    issues: list[SummaryV1Issue],
) -> None:
    for field_name in required:
        if field_name not in mapping:
            _issue(
                issues,
                f"{path}.{field_name}",
                "missing_field",
                "required field is missing",
            )
    if strict:
        allowed = set(required) | set(optional)
        for field_name in mapping:
            if field_name not in allowed:
                _issue(
                    issues,
                    f"{path}.{field_name}",
                    "unknown_field",
                    "field is not part of summary schema 1.0",
                )


def _mapping(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        _issue(issues, path, "type", "expected an object")
        return None
    for key in value:
        if not isinstance(key, str):
            _issue(
                issues,
                path,
                "key_type",
                "object keys must be strings",
            )
            return None
    return cast("Mapping[str, Any]", value)


def _list(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> list[Any] | None:
    if not isinstance(value, list):
        _issue(issues, path, "type", "expected an array")
        return None
    return value


def _string(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> str | None:
    if not isinstance(value, str):
        _issue(issues, path, "type", "expected a string")
        return None
    if "\x00" in value:
        _issue(issues, path, "nul", "string must not contain NUL")
        return None
    return value


def _nonempty_string(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> str | None:
    text = _string(value, path, issues)
    if text is not None and not text:
        _issue(issues, path, "empty", "string must not be empty")
        return None
    return text


def _literal(
    value: object,
    path: str,
    allowed: frozenset[str],
    issues: list[SummaryV1Issue],
) -> str | None:
    text = _string(value, path, issues)
    if text is not None and text not in allowed:
        _issue(
            issues,
            path,
            "enum",
            "expected one of: " + ", ".join(sorted(allowed)),
        )
        return None
    return text


def _boolean(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> bool | None:
    if type(value) is not bool:
        _issue(issues, path, "type", "expected a boolean")
        return None
    return value


def _optional_boolean(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> bool | None:
    if value is None:
        return None
    return _boolean(value, path, issues)


def _non_negative_integer(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> int | None:
    if type(value) is not int:
        _issue(issues, path, "type", "expected an integer")
        return None
    integer = value
    if integer < 0:
        _issue(
            issues,
            path,
            "range",
            "integer must be non-negative",
        )
        return None
    return integer


def _positive_integer(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> int | None:
    integer = _non_negative_integer(value, path, issues)
    if integer is not None and integer < 1:
        _issue(
            issues,
            path,
            "range",
            "integer must be positive",
        )
        return None
    return integer


def _optional_integer(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        _issue(
            issues,
            path,
            "type",
            "expected an integer or null",
        )
        return None
    return value


def _nullable_status(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> str | None:
    if value is None:
        return None
    return _literal(
        value,
        path,
        VALIDATION_STATUSES | OVERALL_STATUSES,
        issues,
    )


def _utc_timestamp(
    value: object,
    path: str,
    issues: list[SummaryV1Issue],
) -> datetime | None:
    text = _nonempty_string(value, path, issues)
    if text is None:
        return None
    parsed_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(parsed_text)
    except ValueError:
        _issue(
            issues,
            path,
            "timestamp",
            "expected an RFC 3339 timestamp",
        )
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _issue(
            issues,
            path,
            "timestamp_timezone",
            "timestamp must include an explicit timezone",
        )
        return None
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        _issue(
            issues,
            path,
            "timestamp_utc",
            "canonical summary timestamps must be UTC",
        )
    return parsed.astimezone(UTC)


def _portable_relative_path(
    value: str,
    path: str,
    issues: list[SummaryV1Issue],
) -> None:
    _canonical_separators(value, path, issues)
    if "\\" in value:
        return
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        _issue(
            issues,
            path,
            "absolute_path",
            "expected a portable relative path",
        )
    if not value or value == ".":
        _issue(
            issues,
            path,
            "empty_path",
            "relative path must identify a child",
        )
    if any(part in {"", ".", ".."} for part in posix.parts):
        _issue(
            issues,
            path,
            "path_segment",
            "path must not contain empty, dot, or parent segments",
        )


def _run_relative_path(
    value: str,
    path: str,
    issues: list[SummaryV1Issue],
) -> None:
    _portable_relative_path(value, path, issues)


def _canonical_separators(
    value: str,
    path: str,
    issues: list[SummaryV1Issue],
) -> None:
    if "\\" in value:
        _issue(
            issues,
            path,
            "separator",
            "canonical paths must use forward slashes",
        )


def _count_invariant(
    mapping: Mapping[str, Any],
    total_field: str,
    parts: Sequence[str],
    path: str,
    issues: list[SummaryV1Issue],
) -> None:
    total = mapping.get(total_field)
    values = tuple(mapping.get(field_name) for field_name in parts)
    if type(total) is int and all(type(value) is int for value in values):
        expected = sum(cast("int", value) for value in values)
        if total != expected:
            _issue(
                issues,
                f"{path}.{total_field}",
                "count_invariant",
                f"must equal {' + '.join(parts)} ({expected})",
            )


def _issue(
    issues: list[SummaryV1Issue],
    path: str,
    code: str,
    message: str,
) -> None:
    issues.append(
        SummaryV1Issue(
            path=path,
            code=code,
            message=message,
        )
    )


def _assert_json_safe(value: object, path: str = "$") -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_json_safe(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} contains a non-string key")
            _assert_json_safe(item, f"{path}.{key}")
        return
    raise TypeError(f"{path} contains a non-JSON value of type {type(value).__name__}")


def assert_summary_v1_json_safe(document: object) -> None:
    _assert_json_safe(document)


__all__ = (
    "ARTIFACT_FIELDS",
    "CHANGE_KINDS",
    "COMPILE_SUMMARY_FIELDS",
    "DIAGNOSTIC_CLASSES",
    "DIFF_CHANGE_ORDER",
    "DIFF_ENTRY_FIELDS",
    "DIFF_SUBJECT_KINDS",
    "ERROR_KINDS",
    "FILE_RESULT_FIELDS",
    "FINGERPRINT_FIELDS",
    "METADATA_FIELDS",
    "OVERALL_STATUSES",
    "ROOT_OPTIONAL_FIELDS",
    "ROOT_REQUIRED_FIELDS",
    "RUN_SUMMARY_SCHEMA_ID",
    "RUN_SUMMARY_SCHEMA_VERSION",
    "SCAN_COUNT_FIELDS",
    "SCENARIO_RESULT_FIELDS",
    "SCENARIO_SECTION_FIELDS",
    "SUMMARY_JSON_FILENAME",
    "SUMMARY_PRODUCER_NAME",
    "SUMMARY_SCHEMA_ID",
    "SUMMARY_SCHEMA_MAJOR",
    "SUMMARY_SCHEMA_MINOR",
    "SUMMARY_SCHEMA_VERSION",
    "TOP_ERROR_FIELDS",
    "TOTALS_FIELDS",
    "VALIDATION_MODES",
    "VALIDATION_STATUSES",
    "ArtifactsDocument",
    "ArtifactsV1",
    "ChangeKindValue",
    "CompileSummaryV1",
    "DiagnosticClassValue",
    "DiffEntryDocument",
    "DiffEntryV1",
    "DiffSubjectKindValue",
    "ErrorKindValue",
    "FileResultDocument",
    "FileResultV1",
    "FingerprintV1",
    "MetadataDocument",
    "MetadataV1",
    "OverallStatusValue",
    "ProducerDocument",
    "ProducerV1",
    "RunSummaryDocument",
    "ScanCountsV1",
    "ScenarioResultDocument",
    "ScenarioResultV1",
    "ScenarioSectionV1",
    "SummaryDocument",
    "SummaryV1",
    "SummaryV1Issue",
    "SummaryV1ValidationError",
    "TopErrorDocument",
    "TopErrorV1",
    "TotalsDocument",
    "TotalsV1",
    "ValidationModeValue",
    "ValidationStatusValue",
    "assert_summary_v1_json_safe",
    "canonicalize_summary_v1",
    "is_summary_v1",
    "is_supported_schema_version",
    "new_summary_v1",
    "parse_schema_version",
    "require_summary_v1",
    "schema_identity",
    "validate_summary_document",
    "validate_summary_v1",
)
