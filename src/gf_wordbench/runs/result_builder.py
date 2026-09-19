"""Typed result assembly and run-level aggregation for GF Wordbench."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, TypeAlias

from gf_wordbench.diagnostics.classification.top_errors import (
    TopErrorCandidate,
    bucket_top_errors as _aggregate_top_errors,
)
from gf_wordbench.diagnostics.models import TopError
from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.paths import normalize_environment_path
from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationStatus,
)
from gf_wordbench.validation.regression.models import DiffEntry
from gf_wordbench.validation.scenarios.models import ScenarioResult

from .models.config import RunConfig
from .models.paths import RunPaths
from .models.results import FileResult, RunResult, RunTotals

ResultSubject: TypeAlias = FileResult | ScenarioResult

_CHANGE_ORDER: Final = {
    ChangeKind.REGRESSED: 0,
    ChangeKind.NEW: 1,
    ChangeKind.IMPROVED: 2,
    ChangeKind.REMOVED: 3,
    ChangeKind.UNCHANGED: 4,
}


def build_file_result(
    *,
    file_path: Path,
    module_name: str,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    scan_counts: Any,
    fingerprint: Any,
    compile_summary: Any,
    blocked_by: Iterable[str] = (),
    scan_log_path: Path | None = None,
    artifacts: Iterable[Any] = (),
) -> FileResult:
    status = _require_enum(status, ValidationStatus, "status")
    diagnostic_class = _require_enum(
        diagnostic_class,
        DiagnosticClass,
        "diagnostic_class",
    )
    blockers = list(_unique_texts(blocked_by, "blocked_by"))
    _validate_diagnostic(
        status,
        diagnostic_class,
        blockers,
        _require_enum(compile_summary.error_kind, ErrorKind, "error_kind"),
        _message(compile_summary.first_error),
    )
    return FileResult(
        file_path=_path(file_path, "file result path"),
        module_name=_text(module_name, "module_name"),
        status=status,
        diagnostic_class=diagnostic_class,
        is_direct=diagnostic_class is DiagnosticClass.DIRECT,
        blocked_by=blockers,
        scan_counts=scan_counts,
        fingerprint=fingerprint,
        compile_summary=compile_summary,
        scan_log_path=_optional_path(scan_log_path, "scan log path"),
        artifacts=list(artifacts),
    )


def build_scenario_result(
    *,
    scenario_id: str,
    script_path: Path,
    script_sha256: str,
    required: bool,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    error_kind: ErrorKind,
    working_directory: Path,
    exit_code: int | None,
    execution_state: ExecutionState | None,
    duration_ms: int,
    primary_message: str,
    blocked_by: Iterable[str] = (),
    command: Iterable[str] = (),
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    normalized_output_path: Path | None = None,
    gold_path: Path | None = None,
    gold_match: bool | None = None,
    gold_diff_path: Path | None = None,
    sections: Iterable[Any] = (),
    assertions: Iterable[Any] = (),
    artifacts: Iterable[Any] = (),
) -> ScenarioResult:
    if not isinstance(required, bool):
        raise TypeError("required must be a boolean")
    status = _require_enum(status, ValidationStatus, "status")
    diagnostic_class = _require_enum(
        diagnostic_class,
        DiagnosticClass,
        "diagnostic_class",
    )
    error_kind = _require_enum(error_kind, ErrorKind, "error_kind")
    if execution_state is not None:
        execution_state = _require_enum(
            execution_state,
            ExecutionState,
            "execution_state",
        )

    return ScenarioResult(
        scenario_id=validate_scenario_id(scenario_id),
        script_path=script_path,
        script_sha256=script_sha256,
        required=required,
        status=status,
        execution_state=execution_state,
        command=tuple(command),
        working_directory=_path(
            working_directory,
            "scenario working directory",
        ),
        exit_code=_exit_code(exit_code),
        timed_out=execution_state is ExecutionState.TIMED_OUT,
        cancelled=execution_state is ExecutionState.CANCELLED,
        duration_ms=_count(duration_ms, "duration_ms"),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        normalized_output_path=normalized_output_path,
        gold_path=gold_path,
        gold_match=gold_match,
        gold_diff_path=gold_diff_path,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
        primary_message=primary_message,
        sections=tuple(sections),
        assertions=tuple(assertions),
        artifacts=tuple(artifacts),
        blocked_by=tuple(blocked_by),
    )


def bucket_top_errors(
    file_results: Iterable[FileResult],
    scenario_results: Iterable[ScenarioResult],
) -> list[TopError]:
    candidates = [
        *(
            _top_error_candidate(
                subject_kind="file",
                subject_id=result.file_path.as_posix(),
                result=result,
            )
            for result in file_results
        ),
        *(
            _top_error_candidate(
                subject_kind="scenario",
                subject_id=str(result.scenario_id),
                result=result,
            )
            for result in scenario_results
        ),
    ]
    return list(_aggregate_top_errors(candidates))


def derive_overall_status(
    file_results: Iterable[FileResult],
    scenario_results: Iterable[ScenarioResult],
    *,
    required_stage_statuses: Iterable[ValidationStatus] = (),
    required_evidence_complete: bool = True,
    framework_error: bool = False,
) -> OverallStatus:
    if not isinstance(required_evidence_complete, bool):
        raise TypeError("required_evidence_complete must be a boolean")
    if not isinstance(framework_error, bool):
        raise TypeError("framework_error must be a boolean")
    if framework_error or not required_evidence_complete:
        return OverallStatus.ERROR

    statuses = [
        *(result.status for result in file_results),
        *(result.status for result in scenario_results if result.required),
        *required_stage_statuses,
    ]
    statuses = [_require_enum(value, ValidationStatus, "status") for value in statuses]
    if any(value in {ValidationStatus.ERROR, ValidationStatus.SKIPPED} for value in statuses):
        return OverallStatus.ERROR
    if any(value is ValidationStatus.FAIL for value in statuses):
        return OverallStatus.FAIL
    return OverallStatus.OK


def update_run_counts(
    file_results: Iterable[FileResult],
    scenario_results: Iterable[ScenarioResult],
    *,
    files_seen: int | None = None,
    files_excluded: int = 0,
    excluded_noise: int = 0,
    required_stage_statuses: Iterable[ValidationStatus] = (),
    required_evidence_complete: bool = True,
    framework_error: bool = False,
) -> RunTotals:
    files = tuple(file_results)
    scenarios = tuple(scenario_results)
    excluded = _count(files_excluded, "files_excluded")
    included = len(files)
    seen = included + excluded if files_seen is None else _count(files_seen, "files_seen")
    if seen != included + excluded:
        raise ValueError("files_seen must equal files_included plus files_excluded")

    totals = RunTotals(
        files_seen=seen,
        files_included=included,
        files_excluded=excluded,
        files_ok=_status_count(files, ValidationStatus.OK),
        files_fail=_status_count(files, ValidationStatus.FAIL),
        files_error=_status_count(files, ValidationStatus.ERROR),
        files_skipped=_status_count(files, ValidationStatus.SKIPPED),
        direct_fail=_diagnostic_count(files, DiagnosticClass.DIRECT),
        downstream_fail=_diagnostic_count(
            files,
            DiagnosticClass.DOWNSTREAM,
        ),
        ambiguous_fail=_diagnostic_count(
            files,
            DiagnosticClass.AMBIGUOUS,
        ),
        excluded_noise=_count(excluded_noise, "excluded_noise"),
        scenarios_seen=len(scenarios),
        scenarios_ok=_status_count(scenarios, ValidationStatus.OK),
        scenarios_fail=_status_count(
            scenarios,
            ValidationStatus.FAIL,
        ),
        scenarios_error=_status_count(
            scenarios,
            ValidationStatus.ERROR,
        ),
        scenarios_skipped=_status_count(
            scenarios,
            ValidationStatus.SKIPPED,
        ),
        required_scenario_fail=sum(
            result.required and result.status is ValidationStatus.FAIL for result in scenarios
        ),
        overall_status=derive_overall_status(
            files,
            scenarios,
            required_stage_statuses=required_stage_statuses,
            required_evidence_complete=required_evidence_complete,
            framework_error=framework_error,
        ),
    )
    _validate_totals(totals)
    return totals


def build_run_result(
    *,
    run_config: RunConfig,
    run_paths: RunPaths,
    started_at: datetime,
    finished_at: datetime,
    duration_ms: int,
    gf_version: str,
    file_results: Iterable[FileResult] = (),
    scenario_results: Iterable[ScenarioResult] = (),
    diff_entries: Iterable[DiffEntry] = (),
    files_seen: int | None = None,
    files_excluded: int = 0,
    excluded_noise: int = 0,
    required_stage_statuses: Iterable[ValidationStatus] = (),
    required_evidence_complete: bool = True,
    framework_error: bool = False,
) -> RunResult:
    started = _timestamp(started_at, "started_at")
    finished = _timestamp(finished_at, "finished_at")
    if finished < started:
        raise ValueError("finished_at must not precede started_at")

    files = sorted(tuple(file_results), key=_file_key)
    scenarios = list(scenario_results)
    diffs = sorted(tuple(diff_entries), key=_diff_key)
    totals = update_run_counts(
        files,
        scenarios,
        files_seen=files_seen,
        files_excluded=files_excluded,
        excluded_noise=excluded_noise,
        required_stage_statuses=required_stage_statuses,
        required_evidence_complete=required_evidence_complete,
        framework_error=framework_error,
    )
    result = RunResult(
        run_config=run_config,
        run_paths=run_paths,
        started_at=started,
        finished_at=finished,
        duration_ms=_count(duration_ms, "duration_ms"),
        gf_version=_text(gf_version, "gf_version"),
        overall_status=totals.overall_status,
        file_results=files,
        scenario_results=scenarios,
        diff_entries=diffs,
        top_errors=bucket_top_errors(files, scenarios),
        totals=totals,
    )
    validate_run_result(result)
    return result


def validate_run_result(result: RunResult) -> None:
    if not isinstance(result, RunResult):
        raise TypeError("result must be a RunResult")
    if _timestamp(result.finished_at, "finished_at") < _timestamp(
        result.started_at,
        "started_at",
    ):
        raise ValueError("finished_at must not precede started_at")
    _count(result.duration_ms, "duration_ms")
    _text(result.gf_version, "gf_version")
    _validate_totals(result.totals)
    if result.overall_status is not result.totals.overall_status:
        raise ValueError("overall_status must equal totals.overall_status")
    if list(result.file_results) != sorted(
        result.file_results,
        key=_file_key,
    ):
        raise ValueError("file_results are not deterministically ordered")
    if list(result.diff_entries) != sorted(
        result.diff_entries,
        key=_diff_key,
    ):
        raise ValueError("diff_entries are not deterministically ordered")
    if list(result.top_errors) != bucket_top_errors(
        result.file_results,
        result.scenario_results,
    ):
        raise ValueError("top_errors must be derived from structured result messages")


def _status_count(
    results: Iterable[ResultSubject],
    status: ValidationStatus,
) -> int:
    return sum(result.status is status for result in results)


def _diagnostic_count(
    results: Iterable[FileResult],
    diagnostic_class: DiagnosticClass,
) -> int:
    return sum(
        result.status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
        and result.diagnostic_class is diagnostic_class
        for result in results
    )


def _validate_totals(totals: RunTotals) -> None:
    for field in (
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
    ):
        _count(getattr(totals, field), f"totals.{field}")
    if totals.files_seen != totals.files_included + totals.files_excluded:
        raise ValueError("files_seen is inconsistent")
    if totals.files_included != (
        totals.files_ok + totals.files_fail + totals.files_error + totals.files_skipped
    ):
        raise ValueError("file totals are inconsistent")
    if totals.scenarios_seen != (
        totals.scenarios_ok
        + totals.scenarios_fail
        + totals.scenarios_error
        + totals.scenarios_skipped
    ):
        raise ValueError("scenario totals are inconsistent")
    if not isinstance(totals.overall_status, OverallStatus):
        raise TypeError("totals.overall_status must be an OverallStatus")


def _validate_diagnostic(
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    blocked_by: list[str],
    error_kind: ErrorKind,
    message: str,
) -> None:
    if diagnostic_class is DiagnosticClass.DIRECT and blocked_by:
        raise ValueError("a direct result must not declare blockers")
    if diagnostic_class is DiagnosticClass.DOWNSTREAM and not blocked_by:
        raise ValueError("a downstream result must declare blockers")
    if status is ValidationStatus.OK:
        if diagnostic_class is not DiagnosticClass.OK:
            raise ValueError("an OK result must use diagnostic class ok")
        if error_kind is not ErrorKind.OK or message:
            raise ValueError("an OK result must not expose an error")
    elif status is ValidationStatus.SKIPPED:
        if diagnostic_class is not DiagnosticClass.SKIPPED:
            raise ValueError("a SKIPPED result must use diagnostic class skipped")
    elif (
        diagnostic_class
        in {
            DiagnosticClass.OK,
            DiagnosticClass.SKIPPED,
        }
        or error_kind is ErrorKind.OK
    ):
        raise ValueError("a failed or errored result needs failure classification")


def _file_key(result: FileResult) -> tuple[str, str]:
    value = result.file_path.as_posix()
    return value.casefold(), value


def _diff_key(entry: DiffEntry) -> tuple[int, str, str, str, str]:
    try:
        rank = _CHANGE_ORDER[entry.change_kind]
    except KeyError as exc:
        raise ValueError(f"unsupported change kind: {entry.change_kind!r}") from exc

    subject_kind = _enum_text(entry.subject_kind, "subject_kind")
    previous_status = _optional_enum_text(
        entry.previous_status,
        "previous_status",
    )
    current_status = _optional_enum_text(
        entry.current_status,
        "current_status",
    )
    return (
        rank,
        subject_kind,
        _text(entry.subject_id, "subject_id"),
        previous_status,
        current_status,
    )


def _top_error_candidate(
    *,
    subject_kind: str,
    subject_id: str,
    result: ResultSubject,
) -> TopErrorCandidate:
    return TopErrorCandidate(
        subject_kind=subject_kind,
        subject_id=subject_id,
        status=_require_enum(result.status, ValidationStatus, "status"),
        diagnostic_class=_require_enum(
            result.diagnostic_class,
            DiagnosticClass,
            "diagnostic_class",
        ),
        error_kind=_require_enum(
            result.error_kind,
            ErrorKind,
            "error_kind",
        ),
        message=_raw_message(result.primary_message),
    )


def _enum_text(value: Any, field: str) -> str:
    rendered = getattr(value, "value", value)
    return _text(rendered, field)


def _optional_enum_text(value: Any | None, field: str) -> str:
    return "" if value is None else _enum_text(value, field)


def _unique_texts(
    values: Iterable[str],
    field: str,
) -> tuple[str, ...]:
    checked = {_text(value, field) for value in values}
    return tuple(sorted(checked, key=lambda item: (item.casefold(), item)))


def _text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _message(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("primary_message must be a string")
    if "\x00" in value:
        raise ValueError("primary_message must not contain NUL")
    return value.strip()


def _raw_message(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("primary_message must be a string")
    if "\x00" in value:
        raise ValueError("primary_message must not contain NUL")
    return value


def _count(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _exit_code(value: int | None) -> int | None:
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise TypeError("exit_code must be an integer or None")
    return value


def _require_enum(value: Any, enum_type: type[Any], field: str) -> Any:
    if not isinstance(value, enum_type):
        raise TypeError(f"{field} must be a {enum_type.__name__}")
    return value


def _timestamp(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _path(value: Path, role: str) -> Path:
    return normalize_environment_path(value, role=role)


def _optional_path(value: Path | None, role: str) -> Path | None:
    return None if value is None else _path(value, role)


__all__ = (
    "ResultSubject",
    "bucket_top_errors",
    "build_file_result",
    "build_run_result",
    "build_scenario_result",
    "derive_overall_status",
    "update_run_counts",
    "validate_run_result",
)
