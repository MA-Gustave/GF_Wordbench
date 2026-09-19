"""Unit tests for canonical run-result assembly and aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from collections.abc import Iterable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationStatus,
)
from gf_wordbench.runs import result_builder
from gf_wordbench.diagnostics.models import TopError
from gf_wordbench.runs.models.results import FileResult, RunResult
from gf_wordbench.validation.scenarios.models import ScenarioResult


@dataclass(frozen=True, slots=True)
class _TopErrorRecord:
    error_kind: ErrorKind
    message: str
    count: int
    subject_kinds: tuple[str, ...]


class _ScenarioResultRecord:
    """Capture the values forwarded by ``build_scenario_result``."""

    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)


def _compile_summary(
    *,
    error_kind: ErrorKind = ErrorKind.OK,
    first_error: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        error_kind=error_kind,
        first_error=first_error,
    )


def _file_result(
    tmp_path: Path,
    name: str,
    *,
    status: ValidationStatus = ValidationStatus.OK,
    diagnostic_class: DiagnosticClass = DiagnosticClass.OK,
    error_kind: ErrorKind = ErrorKind.OK,
    message: str = "",
    blocked_by: tuple[str, ...] = (),
) -> FileResult:
    return result_builder.build_file_result(
        file_path=tmp_path / name,
        module_name=Path(name).stem,
        status=status,
        diagnostic_class=diagnostic_class,
        scan_counts=SimpleNamespace(total=0),
        fingerprint=SimpleNamespace(hash="0" * 64),
        compile_summary=_compile_summary(
            error_kind=error_kind,
            first_error=message,
        ),
        blocked_by=blocked_by,
    )


def _subject(
    *,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass = DiagnosticClass.OK,
    required: bool = True,
    error_kind: ErrorKind = ErrorKind.OK,
    message: str = "",
    scenario_id: str = "scenario",
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        diagnostic_class=diagnostic_class,
        required=required,
        error_kind=error_kind,
        primary_message=message,
        scenario_id=scenario_id,
        file_path=Path(f"{scenario_id}.gf"),
    )


def _diff(
    *,
    change_kind: ChangeKind,
    subject_id: str,
    previous_status: str = "OK",
    current_status: str = "FAIL",
    subject_kind: str = "file",
    message: str = "status changed",
) -> SimpleNamespace:
    return SimpleNamespace(
        change_kind=change_kind,
        subject_kind=subject_kind,
        subject_id=subject_id,
        previous_status=previous_status,
        current_status=current_status,
        message=message,
    )


def _as_file_results(values: Iterable[object]) -> Iterable[FileResult]:
    return cast(Iterable[FileResult], values)


def _as_scenario_results(values: Iterable[object]) -> Iterable[ScenarioResult]:
    return cast(Iterable[ScenarioResult], values)


def _expected_top_errors(values: list[_TopErrorRecord]) -> list[TopError]:
    return cast(list[TopError], values)


@pytest.fixture(autouse=True)
def _use_structural_top_error_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        result_builder,
        "TopError",
        _TopErrorRecord,
    )


def test_build_file_result_normalizes_owned_fields(tmp_path: Path) -> None:
    scan_log = tmp_path / "raw" / "scan" / "demo.scan.txt"

    result = result_builder.build_file_result(
        file_path=tmp_path / "src" / "Demo.gf",
        module_name="  Demo  ",
        status=ValidationStatus.ERROR,
        diagnostic_class=DiagnosticClass.DOWNSTREAM,
        scan_counts=SimpleNamespace(total=3),
        fingerprint=SimpleNamespace(hash="a" * 64),
        compile_summary=_compile_summary(
            error_kind=ErrorKind.TYPE,
            first_error="Unknown category",
        ),
        blocked_by=("Z.gf", "a.gf", "Z.gf"),
        scan_log_path=scan_log,
        artifacts=("compile-log",),
    )

    assert result.file_path == (tmp_path / "src" / "Demo.gf").resolve()
    assert result.module_name == "Demo"
    assert result.status is ValidationStatus.ERROR
    assert result.diagnostic_class is DiagnosticClass.DOWNSTREAM
    assert result.is_direct is False
    assert result.blocked_by == ["a.gf", "Z.gf"]
    assert result.scan_log_path == scan_log.resolve()
    assert result.artifacts == ["compile-log"]
    assert result.error_kind is ErrorKind.TYPE
    assert result.primary_message == "Unknown category"


def test_build_file_result_sets_direct_flag(tmp_path: Path) -> None:
    result = _file_result(
        tmp_path,
        "direct.gf",
        status=ValidationStatus.FAIL,
        diagnostic_class=DiagnosticClass.DIRECT,
        error_kind=ErrorKind.SYNTAX,
        message="Unexpected token",
    )

    assert result.is_direct is True
    assert result.blocked_by == []


@pytest.mark.parametrize(
    ("status", "diagnostic_class", "error_kind", "blocked_by", "message"),
    [
        (
            ValidationStatus.OK,
            DiagnosticClass.DIRECT,
            ErrorKind.OK,
            (),
            "",
        ),
        (
            ValidationStatus.OK,
            DiagnosticClass.OK,
            ErrorKind.SYNTAX,
            (),
            "error",
        ),
        (
            ValidationStatus.FAIL,
            DiagnosticClass.OK,
            ErrorKind.SYNTAX,
            (),
            "error",
        ),
        (
            ValidationStatus.FAIL,
            DiagnosticClass.DIRECT,
            ErrorKind.OK,
            (),
            "error",
        ),
        (
            ValidationStatus.ERROR,
            DiagnosticClass.DOWNSTREAM,
            ErrorKind.TYPE,
            (),
            "blocked",
        ),
        (
            ValidationStatus.FAIL,
            DiagnosticClass.DIRECT,
            ErrorKind.SYNTAX,
            ("provider.gf",),
            "error",
        ),
        (
            ValidationStatus.SKIPPED,
            DiagnosticClass.AMBIGUOUS,
            ErrorKind.OTHER,
            (),
            "skipped",
        ),
    ],
)
def test_build_file_result_rejects_inconsistent_diagnostics(
    tmp_path: Path,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    error_kind: ErrorKind,
    blocked_by: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError):
        _file_result(
            tmp_path,
            "invalid.gf",
            status=status,
            diagnostic_class=diagnostic_class,
            error_kind=error_kind,
            blocked_by=blocked_by,
            message=message,
        )


def test_build_file_result_requires_absolute_paths() -> None:
    with pytest.raises(ValueError, match="explicit resolution base"):
        result_builder.build_file_result(
            file_path=Path("relative.gf"),
            module_name="Relative",
            status=ValidationStatus.OK,
            diagnostic_class=DiagnosticClass.OK,
            scan_counts=SimpleNamespace(total=0),
            fingerprint=SimpleNamespace(hash="0" * 64),
            compile_summary=_compile_summary(),
        )


def test_build_scenario_result_forwards_canonical_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        result_builder,
        "ScenarioResult",
        _ScenarioResultRecord,
    )

    result = result_builder.build_scenario_result(
        scenario_id="smoke",
        script_path=tmp_path / "validation" / "smoke.gfs",
        script_sha256="0" * 64,
        required=True,
        status=ValidationStatus.FAIL,
        diagnostic_class=DiagnosticClass.DOWNSTREAM,
        error_kind=ErrorKind.SCRIPT,
        primary_message="  expected marker missing  ",
        blocked_by=("B", "a", "B"),
        command=("  gf  ", "--run"),
        working_directory=tmp_path,
        exit_code=1,
        execution_state=ExecutionState.COMPLETED,
        duration_ms=15,
        stdout_path=tmp_path / "raw" / "stdout.txt",
        stderr_path=tmp_path / "raw" / "stderr.txt",
        normalized_output_path=tmp_path / "raw" / "normalized.txt",
        gold_path=tmp_path / "gold" / "smoke.gold",
        gold_match=False,
        gold_diff_path=tmp_path / "details" / "smoke.diff",
        sections=("section",),
        assertions=("assertion",),
        artifacts=("artifact",),
    )

    assert result.scenario_id == "smoke"
    assert result.script_path == (tmp_path / "validation" / "smoke.gfs")
    assert result.required is True
    assert result.status is ValidationStatus.FAIL
    assert result.diagnostic_class is DiagnosticClass.DOWNSTREAM
    assert result.error_kind is ErrorKind.SCRIPT
    assert result.primary_message == "expected marker missing"
    assert result.blocked_by == ("a", "B")
    assert result.command == ("gf", "--run")
    assert result.working_directory == tmp_path
    assert result.exit_code == 1
    assert result.execution_state is ExecutionState.COMPLETED
    assert result.timed_out is False
    assert result.duration_ms == 15
    assert result.gold_match is False
    assert result.sections == ("section",)
    assert result.assertions == ("assertion",)
    assert result.artifacts == ("artifact",)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"required": 1}, "required must be a boolean"),
        (
            {
                "execution_state": ExecutionState.COMPLETED,
                "exit_code": None,
            },
            "completed execution requires an exit code",
        ),
        (
            {
                "execution_state": ExecutionState.LAUNCH_FAILED,
                "exit_code": 1,
            },
            "launch failure must not invent an exit code",
        ),
        (
            {
                "execution_state": ExecutionState.TIMED_OUT,
                "status": ValidationStatus.FAIL,
                "error_kind": ErrorKind.TIMEOUT,
            },
            "timed-out scenario must have status ERROR",
        ),
        (
            {
                "execution_state": ExecutionState.TIMED_OUT,
                "status": ValidationStatus.ERROR,
                "error_kind": ErrorKind.TOOL,
            },
            "timed-out scenario must use error kind TIMEOUT",
        ),
        (
            {
                "status": ValidationStatus.OK,
                "diagnostic_class": DiagnosticClass.OK,
                "error_kind": ErrorKind.OK,
                "gold_match": False,
            },
            "gold mismatch cannot have status OK",
        ),
        (
            {
                "status": ValidationStatus.ERROR,
                "diagnostic_class": DiagnosticClass.DOWNSTREAM,
                "error_kind": ErrorKind.SCRIPT,
                "blocked_by": (),
            },
            "downstream result must declare blockers",
        ),
    ],
)
def test_build_scenario_result_rejects_invalid_combinations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    match: str,
) -> None:
    monkeypatch.setattr(
        result_builder,
        "ScenarioResult",
        _ScenarioResultRecord,
    )
    values: dict[str, object] = {
        "scenario_id": "smoke",
        "script_path": tmp_path / "smoke.gfs",
        "script_sha256": "0" * 64,
        "required": True,
        "status": ValidationStatus.FAIL,
        "diagnostic_class": DiagnosticClass.DIRECT,
        "error_kind": ErrorKind.SCRIPT,
        "primary_message": "scenario failed",
        "blocked_by": (),
        "working_directory": tmp_path,
        "exit_code": 1,
        "execution_state": ExecutionState.COMPLETED,
        "duration_ms": 10,
        "gold_match": None,
    }
    values.update(overrides)

    with pytest.raises((TypeError, ValueError), match=match):
        result_builder.build_scenario_result(**values)  # type: ignore[arg-type]


def test_bucket_top_errors_groups_normalized_messages_and_subjects() -> None:
    files = [
        _subject(
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.SYNTAX,
            message="  Missing   semicolon ",
        ),
        _subject(
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.SYNTAX,
            message="missing semicolon",
        ),
        _subject(
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.TYPE,
            message="Unknown category",
        ),
        _subject(
            status=ValidationStatus.OK,
            error_kind=ErrorKind.OK,
            message="",
        ),
    ]
    scenarios = [
        _subject(
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.SYNTAX,
            message="MISSING SEMICOLON",
        )
    ]

    records = result_builder.bucket_top_errors(_as_file_results(files), _as_scenario_results(scenarios))

    assert records == _expected_top_errors([
        _TopErrorRecord(
            error_kind=ErrorKind.SYNTAX,
            message="MISSING SEMICOLON",
            count=3,
            subject_kinds=("file", "scenario"),
        ),
        _TopErrorRecord(
            error_kind=ErrorKind.TYPE,
            message="Unknown category",
            count=1,
            subject_kinds=("file",),
        ),
    ])


def test_bucket_top_errors_uses_deterministic_tie_breakers() -> None:
    records = result_builder.bucket_top_errors(
        _as_file_results((
            _subject(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.TYPE,
                message="zeta",
            ),
            _subject(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.SCRIPT,
                message="beta",
            ),
            _subject(
                status=ValidationStatus.FAIL,
                error_kind=ErrorKind.SCRIPT,
                message="Alpha",
            ),
        )),
        (),
    )

    assert [(record.error_kind, record.message) for record in records] == [
        (ErrorKind.SCRIPT, "Alpha"),
        (ErrorKind.SCRIPT, "beta"),
        (ErrorKind.TYPE, "zeta"),
    ]


@pytest.mark.parametrize(
    ("files", "scenarios", "stage_statuses", "expected"),
    [
        ((), (), (), OverallStatus.OK),
        (
            (_subject(status=ValidationStatus.FAIL),),
            (),
            (),
            OverallStatus.FAIL,
        ),
        (
            (_subject(status=ValidationStatus.ERROR),),
            (),
            (),
            OverallStatus.ERROR,
        ),
        (
            (_subject(status=ValidationStatus.SKIPPED),),
            (),
            (),
            OverallStatus.ERROR,
        ),
        (
            (),
            (
                _subject(
                    status=ValidationStatus.FAIL,
                    required=False,
                ),
            ),
            (),
            OverallStatus.OK,
        ),
        (
            (),
            (
                _subject(
                    status=ValidationStatus.FAIL,
                    required=True,
                ),
            ),
            (),
            OverallStatus.FAIL,
        ),
        (
            (),
            (),
            (ValidationStatus.FAIL,),
            OverallStatus.FAIL,
        ),
        (
            (),
            (),
            (ValidationStatus.ERROR,),
            OverallStatus.ERROR,
        ),
    ],
)
def test_derive_overall_status_applies_required_status_precedence(
    files: tuple[SimpleNamespace, ...],
    scenarios: tuple[SimpleNamespace, ...],
    stage_statuses: tuple[ValidationStatus, ...],
    expected: OverallStatus,
) -> None:
    assert (
        result_builder.derive_overall_status(
            _as_file_results(files),
            _as_scenario_results(scenarios),
            required_stage_statuses=stage_statuses,
        )
        is expected
    )


def test_derive_overall_status_promotes_framework_or_evidence_failure() -> None:
    assert (
        result_builder.derive_overall_status(
            (),
            (),
            required_evidence_complete=False,
        )
        is OverallStatus.ERROR
    )
    assert (
        result_builder.derive_overall_status(
            (),
            (),
            framework_error=True,
        )
        is OverallStatus.ERROR
    )


@pytest.mark.parametrize(
    ("keyword", "value"),
    [
        ("required_evidence_complete", 1),
        ("framework_error", 0),
    ],
)
def test_derive_overall_status_requires_real_booleans(
    keyword: str,
    value: int,
) -> None:
    with pytest.raises(TypeError, match="must be a boolean"):
        if keyword == "required_evidence_complete":
            result_builder.derive_overall_status(
                (), (), required_evidence_complete=cast(bool, value)
            )
        else:
            result_builder.derive_overall_status(
                (), (), framework_error=cast(bool, value)
            )


def test_derive_overall_status_rejects_foreign_status_values() -> None:
    with pytest.raises(TypeError, match="ValidationStatus"):
        result_builder.derive_overall_status(
            (),
            (),
            required_stage_statuses=("FAIL",),  # type: ignore[arg-type]
        )


def test_update_run_counts_derives_all_canonical_totals() -> None:
    files = (
        _subject(
            status=ValidationStatus.OK,
            diagnostic_class=DiagnosticClass.OK,
        ),
        _subject(
            status=ValidationStatus.FAIL,
            diagnostic_class=DiagnosticClass.DIRECT,
        ),
        _subject(
            status=ValidationStatus.ERROR,
            diagnostic_class=DiagnosticClass.DOWNSTREAM,
        ),
        _subject(
            status=ValidationStatus.FAIL,
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
        ),
        _subject(
            status=ValidationStatus.SKIPPED,
            diagnostic_class=DiagnosticClass.SKIPPED,
        ),
    )
    scenarios = (
        _subject(status=ValidationStatus.OK, required=True),
        _subject(status=ValidationStatus.FAIL, required=True),
        _subject(status=ValidationStatus.FAIL, required=False),
        _subject(status=ValidationStatus.ERROR, required=True),
        _subject(status=ValidationStatus.SKIPPED, required=False),
    )

    totals = result_builder.update_run_counts(
        _as_file_results(files),
        _as_scenario_results(scenarios),
        files_seen=7,
        files_excluded=2,
        excluded_noise=3,
    )

    assert totals.files_seen == 7
    assert totals.files_included == 5
    assert totals.files_excluded == 2
    assert totals.files_ok == 1
    assert totals.files_fail == 2
    assert totals.files_error == 1
    assert totals.files_skipped == 1
    assert totals.direct_fail == 1
    assert totals.downstream_fail == 1
    assert totals.ambiguous_fail == 1
    assert totals.excluded_noise == 3
    assert totals.scenarios_seen == 5
    assert totals.scenarios_ok == 1
    assert totals.scenarios_fail == 2
    assert totals.scenarios_error == 1
    assert totals.scenarios_skipped == 1
    assert totals.required_scenario_fail == 1
    assert totals.overall_status is OverallStatus.ERROR


def test_update_run_counts_derives_files_seen_when_omitted() -> None:
    totals = result_builder.update_run_counts(
        _as_file_results((_subject(status=ValidationStatus.OK),)),
        (),
        files_excluded=2,
    )

    assert totals.files_seen == 3
    assert totals.files_included == 1
    assert totals.files_excluded == 2


def test_update_run_counts_rejects_inconsistent_files_seen() -> None:
    with pytest.raises(
        ValueError,
        match="files_seen must equal files_included plus files_excluded",
    ):
        result_builder.update_run_counts(
            _as_file_results((_subject(status=ValidationStatus.OK),)),
            (),
            files_seen=9,
            files_excluded=1,
        )


@pytest.mark.parametrize(
    ("keyword", "value", "exception"),
    [
        ("files_excluded", -1, ValueError),
        ("files_excluded", True, TypeError),
        ("excluded_noise", -1, ValueError),
        ("files_seen", False, TypeError),
    ],
)
def test_update_run_counts_rejects_invalid_counts(
    keyword: str,
    value: object,
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        if keyword == "files_excluded":
            result_builder.update_run_counts((), (), files_excluded=cast(int, value))
        elif keyword == "excluded_noise":
            result_builder.update_run_counts((), (), excluded_noise=cast(int, value))
        else:
            result_builder.update_run_counts((), (), files_seen=cast(int, value))


def test_build_run_result_orders_and_derives_terminal_data(
    tmp_path: Path,
) -> None:
    failed = _file_result(
        tmp_path,
        "b.gf",
        status=ValidationStatus.FAIL,
        diagnostic_class=DiagnosticClass.DIRECT,
        error_kind=ErrorKind.SYNTAX,
        message="Missing semicolon",
    )
    passed = _file_result(tmp_path, "a.gf")
    scenarios = [
        _subject(
            scenario_id="second",
            status=ValidationStatus.FAIL,
            required=False,
            error_kind=ErrorKind.SCRIPT,
            message="Optional mismatch",
        ),
        _subject(
            scenario_id="first",
            status=ValidationStatus.OK,
            required=True,
        ),
    ]
    diffs = [
        _diff(
            change_kind=ChangeKind.IMPROVED,
            subject_id="a.gf",
            previous_status="FAIL",
            current_status="OK",
            message="fixed",
        ),
        _diff(
            change_kind=ChangeKind.REGRESSED,
            subject_id="b.gf",
            previous_status="OK",
            current_status="FAIL",
            message="broken",
        ),
    ]
    local = timezone(timedelta(hours=-4))
    started = datetime(2026, 7, 25, 8, 0, tzinfo=local)
    finished = datetime(2026, 7, 25, 8, 0, 1, tzinfo=local)

    result = result_builder.build_run_result(
        run_config=SimpleNamespace(name="config"),  # type: ignore[arg-type]
        run_paths=SimpleNamespace(run_id="run"),  # type: ignore[arg-type]
        started_at=started,
        finished_at=finished,
        duration_ms=1000,
        gf_version="  GF 3.12  ",
        file_results=(failed, passed),
        scenario_results=_as_scenario_results(scenarios),
        diff_entries=diffs,  # type: ignore[arg-type]
        files_excluded=1,
        excluded_noise=1,
    )

    assert isinstance(result, RunResult)
    assert result.started_at == datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    assert result.finished_at == datetime(
        2026,
        7,
        25,
        12,
        0,
        1,
        tzinfo=UTC,
    )
    assert result.gf_version == "GF 3.12"
    assert [item.file_path.name for item in result.file_results] == [
        "a.gf",
        "b.gf",
    ]
    assert [item.scenario_id for item in result.scenario_results] == [
        "second",
        "first",
    ]
    assert [item.change_kind for item in result.diff_entries] == [
        ChangeKind.REGRESSED,
        ChangeKind.IMPROVED,
    ]
    assert result.overall_status is OverallStatus.FAIL
    assert result.totals.files_seen == 3
    assert result.totals.files_included == 2
    assert result.totals.files_excluded == 1
    assert result.totals.excluded_noise == 1
    assert result.top_errors == _expected_top_errors([
        _TopErrorRecord(
            error_kind=ErrorKind.SCRIPT,
            message="Optional mismatch",
            count=1,
            subject_kinds=("scenario",),
        ),
        _TopErrorRecord(
            error_kind=ErrorKind.SYNTAX,
            message="Missing semicolon",
            count=1,
            subject_kinds=("file",),
        ),
    ])


def test_build_run_result_promotes_missing_required_evidence_to_error(
    tmp_path: Path,
) -> None:
    result = result_builder.build_run_result(
        run_config=SimpleNamespace(),  # type: ignore[arg-type]
        run_paths=SimpleNamespace(),  # type: ignore[arg-type]
        started_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        finished_at=datetime(2026, 7, 25, 12, 0, 1, tzinfo=UTC),
        duration_ms=1000,
        gf_version="GF 3.12",
        file_results=(_file_result(tmp_path, "ok.gf"),),
        required_evidence_complete=False,
    )

    assert result.overall_status is OverallStatus.ERROR
    assert result.totals.overall_status is OverallStatus.ERROR


@pytest.mark.parametrize(
    ("overrides", "exception", "match"),
    [
        (
            {
                "started_at": datetime(2026, 7, 25, 12, 0, 1, tzinfo=UTC),
                "finished_at": datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
            },
            ValueError,
            "finished_at must not precede started_at",
        ),
        (
            {"started_at": datetime(2026, 7, 25, 12, 0)},
            ValueError,
            "started_at must be timezone-aware",
        ),
        (
            {"duration_ms": -1},
            ValueError,
            "duration_ms must be non-negative",
        ),
        (
            {"duration_ms": True},
            TypeError,
            "duration_ms must be an integer",
        ),
        (
            {"gf_version": "   "},
            ValueError,
            "gf_version must not be empty",
        ),
    ],
)
def test_build_run_result_rejects_invalid_terminal_metadata(
    overrides: dict[str, Any],
    exception: type[Exception],
    match: str,
) -> None:
    values: dict[str, Any] = {
        "run_config": SimpleNamespace(),
        "run_paths": SimpleNamespace(),
        "started_at": datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        "finished_at": datetime(2026, 7, 25, 12, 0, 1, tzinfo=UTC),
        "duration_ms": 1000,
        "gf_version": "GF 3.12",
    }
    values.update(overrides)

    with pytest.raises(exception, match=match):
        result_builder.build_run_result(**values)


def _valid_run_result(tmp_path: Path) -> RunResult:
    return result_builder.build_run_result(
        run_config=SimpleNamespace(),  # type: ignore[arg-type]
        run_paths=SimpleNamespace(),  # type: ignore[arg-type]
        started_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        finished_at=datetime(2026, 7, 25, 12, 0, 1, tzinfo=UTC),
        duration_ms=1000,
        gf_version="GF 3.12",
        file_results=(
            _file_result(tmp_path, "a.gf"),
            _file_result(
                tmp_path,
                "b.gf",
                status=ValidationStatus.FAIL,
                diagnostic_class=DiagnosticClass.DIRECT,
                error_kind=ErrorKind.SYNTAX,
                message="failure",
            ),
        ),
        diff_entries=(
            _diff(
                change_kind=ChangeKind.REGRESSED,
                subject_id="a.gf",
            ),
            _diff(
                change_kind=ChangeKind.IMPROVED,
                subject_id="b.gf",
                previous_status="FAIL",
                current_status="OK",
            ),
        ),  # type: ignore[arg-type]
    )


def test_validate_run_result_accepts_canonical_result(tmp_path: Path) -> None:
    result_builder.validate_run_result(_valid_run_result(tmp_path))


def test_validate_run_result_rejects_foreign_object() -> None:
    with pytest.raises(TypeError, match="result must be a RunResult"):
        result_builder.validate_run_result(object())  # type: ignore[arg-type]


def test_validate_run_result_detects_file_order_drift(tmp_path: Path) -> None:
    result = _valid_run_result(tmp_path)
    result.file_results.reverse()

    with pytest.raises(
        ValueError,
        match="file_results are not deterministically ordered",
    ):
        result_builder.validate_run_result(result)


def test_validate_run_result_detects_diff_order_drift(tmp_path: Path) -> None:
    result = _valid_run_result(tmp_path)
    result.diff_entries.reverse()

    with pytest.raises(
        ValueError,
        match="diff_entries are not deterministically ordered",
    ):
        result_builder.validate_run_result(result)


def test_validate_run_result_detects_derived_top_error_drift(
    tmp_path: Path,
) -> None:
    result = _valid_run_result(tmp_path)
    result.top_errors = []

    with pytest.raises(
        ValueError,
        match="top_errors must be derived",
    ):
        result_builder.validate_run_result(result)


def test_validate_run_result_detects_overall_status_drift(
    tmp_path: Path,
) -> None:
    result = _valid_run_result(tmp_path)
    result.overall_status = OverallStatus.OK

    with pytest.raises(
        ValueError,
        match="overall_status must equal totals.overall_status",
    ):
        result_builder.validate_run_result(result)
