"""Unit tests for PGF build evaluation and release evidence rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest

from gf_wordbench.infrastructure.process.models import (
    CancellationReason,
    ProcessErrorKind,
    ProcessOperationKind,
    ProcessResult,
)
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.validation.compilation.models import (
    PgfArtifactEvidence,
    PgfBuildExecution,
    PgfBuildRequest,
)
from gf_wordbench.validation.compilation.pgf_build import (
    build_release_pgf,
    evaluate_pgf_build,
    skipped_pgf_build,
)
from gf_wordbench.validation.ports import GfToolPort

_SHA256 = "a" * 64
_STARTED_AT = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
_FINISHED_AT = _STARTED_AT + timedelta(milliseconds=25)
_T = TypeVar("_T")


def _unchecked_instance(model: type[_T], /, **values: object) -> _T:
    """Create a contract instance without coupling tests to constructor order."""

    instance = object.__new__(model)
    for name, value in values.items():
        object.__setattr__(instance, name, value)
    return instance


def _request(
    tmp_path: Path,
    **overrides: Any,
) -> PgfBuildRequest:
    project_root = tmp_path / "project"
    artifact_root = tmp_path / "run" / "artifacts"
    values: dict[str, Any] = {
        "request_id": "pgf-build-001",
        "project_id": "project-001",
        "run_id": "run-001",
        "mode": ValidationMode.RELEASE,
        "required": True,
        "optimize": True,
        "runtime_verification_required": True,
        "gf_executable": tmp_path / "tools" / "gf.exe",
        "project_root": project_root,
        "artifact_root": artifact_root,
        "expected_pgf_path": artifact_root / "pgf" / "App.pgf",
        "stdout_path": tmp_path / "run" / "raw" / "pgf.stdout.log",
        "stderr_path": tmp_path / "run" / "raw" / "pgf.stderr.log",
    }
    values.update(overrides)
    return _unchecked_instance(PgfBuildRequest, **values)


def _process(
    request: PgfBuildRequest,
    *,
    state: ExecutionState = ExecutionState.COMPLETED,
    exit_code: int | None = 0,
    capture_complete: bool = True,
    operation_kind: ProcessOperationKind = ProcessOperationKind.PGF_BUILD,
    operation_id: str | None = None,
    executable: Path | None = None,
    cwd: Path | None = None,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> ProcessResult:
    pid: int | None = 41_001
    cancellation_reason: CancellationReason | None = None
    launch_error_kind: ProcessErrorKind | None = None
    launch_error_message = ""
    termination_attempted = False
    termination_succeeded = False

    if state is ExecutionState.LAUNCH_FAILED:
        pid = None
        exit_code = None
        launch_error_kind = ProcessErrorKind.LAUNCH
        launch_error_message = "GF executable could not be launched"
    elif state is ExecutionState.TIMED_OUT:
        exit_code = None
        termination_attempted = True
        termination_succeeded = True
    elif state is ExecutionState.CANCELLED:
        exit_code = None
        cancellation_reason = CancellationReason.USER
        termination_attempted = True
        termination_succeeded = True

    return ProcessResult(
        operation_id=operation_id or request.request_id,
        operation_kind=operation_kind,
        executable=executable or request.gf_executable,
        args=("-make", "App.gf"),
        cwd=cwd or request.project_root,
        execution_state=state,
        exit_code=exit_code,
        pid=pid,
        started_at=_STARTED_AT,
        finished_at=_FINISHED_AT,
        duration_ms=25,
        cancellation_reason=cancellation_reason,
        launch_error_kind=launch_error_kind,
        launch_error_message=launch_error_message,
        termination_attempted=termination_attempted,
        termination_succeeded=termination_succeeded,
        stdout_path=stdout_path or request.stdout_path,
        stderr_path=stderr_path or request.stderr_path,
        stdout_size_bytes=0,
        stderr_size_bytes=0,
        output_limit_exceeded=False,
        capture_complete=capture_complete,
        environment_policy="gf-wordbench-controlled",
    )


def _artifact(
    request: PgfBuildRequest,
    **overrides: Any,
) -> PgfArtifactEvidence:
    values: dict[str, Any] = {
        "path": request.expected_pgf_path,
        "exists": True,
        "is_file": True,
        "readable": True,
        "size_bytes": 128,
        "sha256": _SHA256,
        "current_request": True,
        "identity_matches": True,
        "runtime_verified": True,
        "catalogued": True,
    }
    values.update(overrides)
    return _unchecked_instance(PgfArtifactEvidence, **values)


def _execution(
    request: PgfBuildRequest,
    *,
    process_result: ProcessResult | None = None,
    artifact: PgfArtifactEvidence | None = None,
    error_kind: ErrorKind = ErrorKind.OK,
    first_error: str = "",
    error_detail: str = "",
    fatal_diagnostic: bool = False,
    warnings: tuple[str, ...] = (),
) -> PgfBuildExecution:
    return _unchecked_instance(
        PgfBuildExecution,
        process_result=process_result or _process(request),
        artifact=artifact or _artifact(request),
        error_kind=error_kind,
        first_error=first_error,
        error_detail=error_detail,
        fatal_diagnostic=fatal_diagnostic,
        gf_version="3.12",
        warnings=warnings,
    )


class _GfTool:
    def __init__(self, execution: Any) -> None:
        self.execution = execution
        self.requests: list[PgfBuildRequest] = []

    def build_pgf(self, request: PgfBuildRequest) -> Any:
        self.requests.append(request)
        return self.execution


def test_release_build_is_ok_only_with_complete_current_evidence(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    result = evaluate_pgf_build(request, _execution(request))

    assert result.status is ValidationStatus.OK
    assert result.error_kind is ErrorKind.OK
    assert result.execution_state is ExecutionState.COMPLETED
    assert result.artifact is not None
    assert result.artifact.path == request.expected_pgf_path
    assert result.release_evidence_eligible is True
    assert result.warnings == ()


def test_build_release_pgf_delegates_once_to_gf_boundary(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    execution = _execution(request)
    gf_tool = _GfTool(execution)

    result = build_release_pgf(request, gf_tool=cast(GfToolPort, gf_tool))

    assert gf_tool.requests == [request]
    assert result.status is ValidationStatus.OK


def test_build_release_pgf_rejects_invalid_boundary_result(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    with pytest.raises(
        TypeError,
        match="must return PgfBuildExecution",
    ):
        build_release_pgf(request, gf_tool=cast(GfToolPort, _GfTool(object())))


def test_nonoptimized_diagnostic_build_is_not_release_evidence(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        mode=ValidationMode.DIAGNOSTIC,
        required=False,
        optimize=False,
        runtime_verification_required=False,
    )

    result = evaluate_pgf_build(request, _execution(request))

    assert result.status is ValidationStatus.OK
    assert result.release_evidence_eligible is False
    assert result.warnings == (
        "diagnostic PGF evidence does not establish release readiness",
        "diagnostic PGF construction used non-release optimization",
    )


@pytest.mark.parametrize(
    ("artifact_changes", "expected_error"),
    [
        ({"exists": False}, "without producing"),
        ({"is_file": False}, "not a regular file"),
        ({"readable": False}, "not readable"),
        ({"size_bytes": 0}, "is empty"),
        ({"sha256": None}, "no recorded SHA-256"),
        ({"current_request": False}, "stale"),
        ({"identity_matches": False}, "release identity"),
        ({"runtime_verified": False}, "runtime verification"),
        ({"catalogued": False}, "manifest publication"),
    ],
)
def test_invalid_artifact_evidence_produces_io_error(
    tmp_path: Path,
    artifact_changes: dict[str, Any],
    expected_error: str,
) -> None:
    request = _request(tmp_path)
    execution = _execution(
        request,
        artifact=_artifact(request, **artifact_changes),
    )

    result = evaluate_pgf_build(request, execution)

    assert result.status is ValidationStatus.ERROR
    assert result.error_kind is ErrorKind.IO
    assert expected_error in result.first_error
    assert result.release_evidence_eligible is False


def test_artifact_below_unowned_root_is_rejected(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    artifact = _artifact(
        request,
        path=tmp_path / "outside" / "App.pgf",
    )

    result = evaluate_pgf_build(
        request,
        _execution(request, artifact=artifact),
    )

    assert result.status is ValidationStatus.ERROR
    assert result.error_kind is ErrorKind.IO
    assert "unexpected artifact path" in result.first_error


def test_artifact_root_itself_is_not_a_valid_output_path(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "run" / "artifacts"
    request = _request(
        tmp_path,
        artifact_root=artifact_root,
        expected_pgf_path=artifact_root,
    )

    result = evaluate_pgf_build(request, _execution(request))

    assert result.status is ValidationStatus.ERROR
    assert "escaped the run-owned artifact root" in result.first_error


@pytest.mark.parametrize(
    ("error_kind", "expected_status"),
    [
        (ErrorKind.TYPE, ValidationStatus.FAIL),
        (ErrorKind.SYNTAX, ValidationStatus.FAIL),
        (ErrorKind.OTHER, ValidationStatus.FAIL),
        (ErrorKind.TOOL, ValidationStatus.ERROR),
        (ErrorKind.IO, ValidationStatus.ERROR),
        (ErrorKind.INTERNAL, ValidationStatus.ERROR),
    ],
)
def test_nonzero_exit_uses_language_vs_infrastructure_status_policy(
    tmp_path: Path,
    error_kind: ErrorKind,
    expected_status: ValidationStatus,
) -> None:
    request = _request(tmp_path)
    execution = _execution(
        request,
        process_result=_process(request, exit_code=1),
        error_kind=error_kind,
        first_error="GF reported a failure",
    )

    result = evaluate_pgf_build(request, execution)

    assert result.status is expected_status
    assert result.error_kind is error_kind
    assert result.first_error == "GF reported a failure"
    assert result.release_evidence_eligible is False


def test_fatal_diagnostic_fails_even_with_zero_exit(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    execution = _execution(
        request,
        fatal_diagnostic=True,
        error_kind=ErrorKind.SYNTAX,
        first_error="syntax error in release entrypoint",
    )

    result = evaluate_pgf_build(request, execution)

    assert result.status is ValidationStatus.FAIL
    assert result.error_kind is ErrorKind.SYNTAX


@pytest.mark.parametrize(
    ("state", "expected_kind", "message_fragment"),
    [
        (
            ExecutionState.TIMED_OUT,
            ErrorKind.TIMEOUT,
            "execution budget",
        ),
        (
            ExecutionState.LAUNCH_FAILED,
            ErrorKind.TOOL,
            "could not be launched",
        ),
        (
            ExecutionState.CANCELLED,
            ErrorKind.OTHER,
            "was cancelled",
        ),
    ],
)
def test_abnormal_process_states_are_errors(
    tmp_path: Path,
    state: ExecutionState,
    expected_kind: ErrorKind,
    message_fragment: str,
) -> None:
    request = _request(tmp_path)
    execution = _execution(
        request,
        process_result=_process(request, state=state),
    )

    result = evaluate_pgf_build(request, execution)

    assert result.status is ValidationStatus.ERROR
    assert result.error_kind is expected_kind
    assert message_fragment in result.first_error
    assert result.release_evidence_eligible is False


def test_incomplete_raw_capture_is_an_io_error(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    result = evaluate_pgf_build(
        request,
        _execution(
            request,
            process_result=_process(
                request,
                capture_complete=False,
            ),
        ),
    )

    assert result.status is ValidationStatus.ERROR
    assert result.error_kind is ErrorKind.IO
    assert result.first_error == "PGF process evidence capture is incomplete"


@pytest.mark.parametrize(
    ("process_changes", "expected_error"),
    [
        (
            {"operation_kind": ProcessOperationKind.COMPILE},
            "operation kind pgf_build",
        ),
        ({"operation_id": "other"}, "operation_id"),
        ({"executable": Path("other-gf")}, "resolved GF executable"),
        ({"cwd": Path("other-project")}, "working directory"),
        ({"stdout_path": Path("other.stdout")}, "stdout_path"),
        ({"stderr_path": Path("other.stderr")}, "stderr_path"),
    ],
)
def test_process_identity_must_match_request(
    tmp_path: Path,
    process_changes: dict[str, Any],
    expected_error: str,
) -> None:
    request = _request(tmp_path)

    with pytest.raises(ValueError, match=expected_error):
        evaluate_pgf_build(
            request,
            _execution(
                request,
                process_result=_process(
                    request,
                    **process_changes,
                ),
            ),
        )


def test_runtime_verification_can_be_optional_in_diagnostic_mode(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        mode=ValidationMode.DIAGNOSTIC,
        required=False,
        optimize=False,
        runtime_verification_required=False,
    )
    execution = _execution(
        request,
        artifact=_artifact(request, runtime_verified=None),
    )

    result = evaluate_pgf_build(request, execution)

    assert result.status is ValidationStatus.OK
    assert result.release_evidence_eligible is False


def test_warning_order_is_stable_and_duplicates_are_removed(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    execution = _execution(
        request,
        warnings=("first", "second", "first"),
    )

    result = evaluate_pgf_build(request, execution)

    assert result.warnings == ("first", "second")


def test_optional_pgf_build_can_be_skipped(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        required=False,
        mode=ValidationMode.QUICK,
        optimize=False,
        runtime_verification_required=False,
    )

    result = skipped_pgf_build(
        request,
        reason="PGF is not selected in quick mode",
    )

    assert result.status is ValidationStatus.SKIPPED
    assert result.execution_state is None
    assert result.process_result is None
    assert result.artifact is None
    assert result.error_kind is ErrorKind.OK
    assert result.first_error == "PGF is not selected in quick mode"
    assert result.release_evidence_eligible is False


def test_required_pgf_build_cannot_be_skipped(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, required=True)

    with pytest.raises(
        ValueError,
        match="required PGF build cannot be skipped",
    ):
        skipped_pgf_build(request, reason="not available")


def test_evaluation_does_not_overwrite_sources_or_previous_pgf(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    source = request.project_root / "App.gf"
    previous_pgf = request.project_root / "App.pgf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"abstract App = {}\n")
    previous_pgf.write_bytes(b"previous-pgf")

    result = evaluate_pgf_build(request, _execution(request))

    assert result.status is ValidationStatus.OK
    assert source.read_bytes() == b"abstract App = {}\n"
    assert previous_pgf.read_bytes() == b"previous-pgf"
