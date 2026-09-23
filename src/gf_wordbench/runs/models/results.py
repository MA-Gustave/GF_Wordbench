"""Canonical structured result models for one GF Wordbench run."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    OverallStatus,
    ValidationStatus,
)

if TYPE_CHECKING:
    from gf_wordbench.diagnostics.models import TopError
    from gf_wordbench.reporting.manifest.models import ArtifactManifestEntry
    from gf_wordbench.validation.compilation.models import (
        CompileSummary,
        SourceFingerprint,
    )
    from gf_wordbench.validation.regression.models import DiffEntry
    from gf_wordbench.validation.scanning.models import ScanCounts
    from gf_wordbench.validation.scenarios.models import ScenarioResult

    from .config import RunConfig
    from .paths import RunPaths

__all__ = (
    "FileResult",
    "RunResult",
    "RunTotals",
)

_CHANGE_ORDER: Final[dict[ChangeKind, int]] = {
    ChangeKind.REGRESSED: 0,
    ChangeKind.NEW: 1,
    ChangeKind.IMPROVED: 2,
    ChangeKind.REMOVED: 3,
    ChangeKind.UNCHANGED: 4,
}

_COUNT_FIELDS: Final[tuple[str, ...]] = (
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
)


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _require_non_negative_int(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _as_utc(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _unique_text_list(
    values: object,
    *,
    field_name: str,
) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence of strings")

    if not isinstance(values, Iterable):
        raise TypeError(f"{field_name} must be an iterable of strings")
    copied = list(values)

    seen: set[str] = set()
    result: list[str] = []
    for index, value in enumerate(copied):
        item = _require_text(
            value,
            field_name=f"{field_name}[{index}]",
            allow_empty=False,
        )
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicate value {item!r}")
        seen.add(item)
        result.append(item)
    return result


def _path_key(value: Path) -> str:
    return value.as_posix()


def _error_kind_text(value: object) -> str:
    if isinstance(value, ErrorKind):
        return value.value
    if isinstance(value, str):
        return value
    raise TypeError("top error error_kind must be ErrorKind or string")


def _coerce_change_kind(value: object) -> ChangeKind:
    if isinstance(value, ChangeKind):
        return value
    if not isinstance(value, str):
        raise TypeError("diff change kind must be ChangeKind or string")
    try:
        return ChangeKind(value)
    except ValueError as exc:
        raise ValueError(f"invalid diff change kind: {value!r}") from exc


def _diff_sort_key(entry: DiffEntry) -> tuple[int, str, str, str, str]:
    change_kind = _coerce_change_kind(entry.change_kind)

    subject_kind = _require_text(
        entry.subject_kind,
        field_name="diff entry subject_kind",
        allow_empty=False,
    )
    if subject_kind not in {"file", "scenario", "run"}:
        raise ValueError(f"unsupported diff subject kind: {subject_kind!r}")

    subject_id = _require_text(
        entry.subject_id,
        field_name="diff entry subject_id",
        allow_empty=False,
    )
    previous_status = _require_text(
        entry.previous_status,
        field_name="diff entry previous_status",
        allow_empty=False,
    )
    current_status = _require_text(
        entry.current_status,
        field_name="diff entry current_status",
        allow_empty=False,
    )

    return (
        _CHANGE_ORDER[change_kind],
        subject_kind,
        subject_id,
        previous_status,
        current_status,
    )


def _top_error_sort_key(
    entry: TopError,
) -> tuple[int, str, str, str]:
    count = entry.count
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("top error count must be an integer")
    if count <= 0:
        raise ValueError("top error count must be positive")

    message = _require_text(
        entry.message,
        field_name="top error message",
        allow_empty=False,
    )
    error_kind = _error_kind_text(entry.error_kind)
    return (-count, error_kind, message.casefold(), message)


@dataclass(slots=True)
class FileResult:
    """Final structured result for one selected GF source file."""

    file_path: Path
    module_name: str
    status: ValidationStatus
    diagnostic_class: DiagnosticClass
    is_direct: bool
    blocked_by: list[str]
    scan_counts: ScanCounts
    fingerprint: SourceFingerprint
    compile_summary: CompileSummary
    scan_log_path: Path | None
    artifacts: list[ArtifactManifestEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.file_path = Path(self.file_path)
        self.module_name = _require_text(
            self.module_name,
            field_name="module_name",
            allow_empty=False,
        )

        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be a ValidationStatus")
        if not isinstance(self.diagnostic_class, DiagnosticClass):
            raise TypeError("diagnostic_class must be a DiagnosticClass")
        if not isinstance(self.is_direct, bool):
            raise TypeError("is_direct must be a bool")
        if self.is_direct != (self.diagnostic_class is DiagnosticClass.DIRECT):
            raise ValueError("is_direct must agree with diagnostic_class")

        self.blocked_by = _unique_text_list(
            self.blocked_by,
            field_name="blocked_by",
        )
        if self.diagnostic_class is DiagnosticClass.DOWNSTREAM and not self.blocked_by:
            raise ValueError("downstream file results require at least one blocker")

        if self.status is ValidationStatus.OK and (self.diagnostic_class is not DiagnosticClass.OK):
            raise ValueError("OK file results require diagnostic_class=ok")
        if self.diagnostic_class is DiagnosticClass.OK and (self.status is not ValidationStatus.OK):
            raise ValueError("diagnostic_class=ok requires status=OK")
        if self.status is ValidationStatus.SKIPPED and (
            self.diagnostic_class is not DiagnosticClass.SKIPPED
        ):
            raise ValueError("SKIPPED file results require diagnostic_class=skipped")
        if self.diagnostic_class is DiagnosticClass.SKIPPED and (
            self.status is not ValidationStatus.SKIPPED
        ):
            raise ValueError("diagnostic_class=skipped requires status=SKIPPED")

        if self.scan_log_path is not None:
            self.scan_log_path = Path(self.scan_log_path)
        self.artifacts = list(self.artifacts)

    @property
    def error_kind(self) -> ErrorKind:
        """Return the compiler-owned technical error category."""

        value = self.compile_summary.error_kind
        if not isinstance(value, ErrorKind):
            raise TypeError("compile_summary.error_kind must be an ErrorKind")
        return value

    @property
    def primary_message(self) -> str:
        """Return the compiler-owned primary normalized diagnostic."""

        return _require_text(
            self.compile_summary.first_error,
            field_name="compile_summary.first_error",
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class RunTotals:
    """Canonical derived totals for one terminal run result."""

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
    overall_status: OverallStatus

    def __post_init__(self) -> None:
        for field_name in _COUNT_FIELDS:
            _require_non_negative_int(
                getattr(self, field_name),
                field_name=field_name,
            )

        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be an OverallStatus")

        if self.files_seen != (self.files_included + self.files_excluded):
            raise ValueError("files_seen must equal files_included + files_excluded")
        if self.files_included != (
            self.files_ok + self.files_fail + self.files_error + self.files_skipped
        ):
            raise ValueError("files_included must equal the sum of file status counts")
        if self.scenarios_seen != (
            self.scenarios_ok + self.scenarios_fail + self.scenarios_error + self.scenarios_skipped
        ):
            raise ValueError("scenarios_seen must equal the sum of scenario status counts")
        if self.required_scenario_fail > self.scenarios_fail:
            raise ValueError("required_scenario_fail cannot exceed scenarios_fail")


@dataclass(slots=True)
class RunResult:
    """Aggregate structured source of truth for one GF Wordbench run."""

    run_config: RunConfig
    run_paths: RunPaths
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    gf_version: str
    overall_status: OverallStatus
    file_results: list[FileResult]
    scenario_results: list[ScenarioResult]
    diff_entries: list[DiffEntry]
    top_errors: list[TopError]
    totals: RunTotals

    def __post_init__(self) -> None:
        if self.run_config is None:
            raise TypeError("run_config must not be None")
        if self.run_paths is None:
            raise TypeError("run_paths must not be None")

        self.started_at = _as_utc(
            self.started_at,
            field_name="started_at",
        )
        self.finished_at = _as_utc(
            self.finished_at,
            field_name="finished_at",
        )
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")

        self.duration_ms = _require_non_negative_int(
            self.duration_ms,
            field_name="duration_ms",
        )
        self.gf_version = _require_text(
            self.gf_version,
            field_name="gf_version",
            allow_empty=True,
        )

        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be an OverallStatus")
        if not isinstance(self.totals, RunTotals):
            raise TypeError("totals must be a RunTotals")

        self.file_results = list(self.file_results)
        self.scenario_results = list(self.scenario_results)
        self.diff_entries = list(self.diff_entries)
        self.top_errors = list(self.top_errors)

        self.validate()

    def validate(self) -> None:
        """Validate terminal aggregate invariants without mutating results."""

        if self.overall_status is not self.totals.overall_status:
            raise ValueError("overall_status must agree with totals.overall_status")

        file_keys = [_path_key(result.file_path) for result in self.file_results]
        if len(file_keys) != len(set(file_keys)):
            raise ValueError("file_results contain duplicate file paths")
        if file_keys != sorted(file_keys, key=lambda value: (value.casefold(), value)):
            raise ValueError("file_results must be ordered by normalized file_path")

        scenario_ids = [
            _require_text(
                result.scenario_id,
                field_name="scenario_id",
                allow_empty=False,
            )
            for result in self.scenario_results
        ]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("scenario_results contain duplicate scenario IDs")

        diff_keys = [_diff_sort_key(entry) for entry in self.diff_entries]
        if diff_keys != sorted(diff_keys):
            raise ValueError("diff_entries must follow canonical deterministic order")

        top_error_keys = [_top_error_sort_key(entry) for entry in self.top_errors]
        if top_error_keys != sorted(top_error_keys):
            raise ValueError("top_errors must follow canonical deterministic order")

        self._validate_totals_against_results()

    def _validate_totals_against_results(self) -> None:
        if self.totals.files_included != len(self.file_results):
            raise ValueError("files_included must equal len(file_results)")
        if self.totals.scenarios_seen != len(self.scenario_results):
            raise ValueError("scenarios_seen must equal len(scenario_results)")

        file_statuses = Counter(result.status for result in self.file_results)
        expected_file_counts = {
            ValidationStatus.OK: self.totals.files_ok,
            ValidationStatus.FAIL: self.totals.files_fail,
            ValidationStatus.ERROR: self.totals.files_error,
            ValidationStatus.SKIPPED: self.totals.files_skipped,
        }
        for status, expected in expected_file_counts.items():
            if file_statuses[status] != expected:
                raise ValueError(f"{status.value} file total does not match file_results")

        scenario_statuses = Counter(result.status for result in self.scenario_results)
        expected_scenario_counts = {
            ValidationStatus.OK: self.totals.scenarios_ok,
            ValidationStatus.FAIL: self.totals.scenarios_fail,
            ValidationStatus.ERROR: self.totals.scenarios_error,
            ValidationStatus.SKIPPED: self.totals.scenarios_skipped,
        }
        for status, expected in expected_scenario_counts.items():
            if scenario_statuses[status] != expected:
                raise ValueError(f"{status.value} scenario total does not match scenario_results")

        required_scenario_fail = sum(
            1
            for result in self.scenario_results
            if result.required and result.status is ValidationStatus.FAIL
        )
        if required_scenario_fail != self.totals.required_scenario_fail:
            raise ValueError("required_scenario_fail does not match scenario_results")
