"""PGF build orchestration and contract evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from gf_wordbench.infrastructure.process.models import ProcessOperationKind
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.validation.ports import GfToolPort

from .models import (
    PgfArtifactEvidence,
    PgfBuildExecution,
    PgfBuildRequest,
    PgfBuildResult,
)

_LANGUAGE_FAILURE_KINDS: Final[frozenset[ErrorKind]] = frozenset(
    {
        ErrorKind.TYPE,
        ErrorKind.SYNTAX,
        ErrorKind.OTHER,
    }
)


def build_release_pgf(
    request: PgfBuildRequest,
    *,
    gf_tool: GfToolPort,
) -> PgfBuildResult:
    """Execute one semantic PGF request through the GF boundary."""

    if not isinstance(request, PgfBuildRequest):
        raise TypeError("request must be a PgfBuildRequest")
    build_pgf = getattr(gf_tool, "build_pgf", None)
    if not callable(build_pgf):
        raise TypeError("gf_tool must implement GfToolPort.build_pgf")

    execution = build_pgf(request)
    if not isinstance(execution, PgfBuildExecution):
        raise TypeError(
            "GfToolPort.build_pgf must return PgfBuildExecution"
        )

    return evaluate_pgf_build(request, execution)


def evaluate_pgf_build(
    request: PgfBuildRequest,
    execution: PgfBuildExecution,
) -> PgfBuildResult:
    """Convert process-backed GF evidence into one PGF stage result."""

    if not isinstance(request, PgfBuildRequest):
        raise TypeError("request must be a PgfBuildRequest")
    if not isinstance(execution, PgfBuildExecution):
        raise TypeError("execution must be a PgfBuildExecution")

    _validate_execution_identity(request, execution)

    process = execution.process_result
    state = process.execution_state

    if state is ExecutionState.LAUNCH_FAILED:
        return _error_result(
            request,
            execution,
            error_kind=ErrorKind.TOOL,
            first_error=(
                execution.first_error
                or process.launch_error_message
                or "GF could not be launched for PGF construction"
            ),
        )

    if state is ExecutionState.TIMED_OUT:
        return _error_result(
            request,
            execution,
            error_kind=ErrorKind.TIMEOUT,
            first_error=(
                execution.first_error
                or "PGF construction exceeded its execution budget"
            ),
        )

    if state is ExecutionState.CANCELLED:
        return _error_result(
            request,
            execution,
            error_kind=_non_ok_kind(
                execution.error_kind,
                fallback=ErrorKind.OTHER,
            ),
            first_error=(
                execution.first_error
                or "PGF construction was cancelled"
            ),
        )

    if state is not ExecutionState.COMPLETED:
        raise ValueError(
            f"unsupported PGF execution state: {state!r}"
        )

    if not process.capture_complete:
        return _error_result(
            request,
            execution,
            error_kind=ErrorKind.IO,
            first_error="PGF process evidence capture is incomplete",
        )

    if process.exit_code != 0 or execution.fatal_diagnostic:
        error_kind = _non_ok_kind(
            execution.error_kind,
            fallback=ErrorKind.OTHER,
        )
        status = (
            ValidationStatus.FAIL
            if error_kind in _LANGUAGE_FAILURE_KINDS
            else ValidationStatus.ERROR
        )
        return _failed_result(
            request,
            execution,
            status=status,
            error_kind=error_kind,
            first_error=(
                execution.first_error
                or "GF reported a PGF construction failure"
            ),
        )

    if execution.error_kind is not ErrorKind.OK:
        status = (
            ValidationStatus.FAIL
            if execution.error_kind in _LANGUAGE_FAILURE_KINDS
            else ValidationStatus.ERROR
        )
        return _failed_result(
            request,
            execution,
            status=status,
            error_kind=execution.error_kind,
            first_error=(
                execution.first_error
                or "PGF result interpretation returned a non-OK outcome"
            ),
        )

    artifact_error = _artifact_error(
        request,
        execution.artifact,
    )
    if artifact_error is not None:
        return _error_result(
            request,
            execution,
            error_kind=ErrorKind.IO,
            first_error=artifact_error,
        )

    warnings = list(execution.warnings)
    if request.mode is ValidationMode.DIAGNOSTIC:
        warnings.append(
            "diagnostic PGF evidence does not establish release readiness"
        )
        if not request.optimize:
            warnings.append(
                "diagnostic PGF construction used non-release optimization"
            )

    return PgfBuildResult(
        request_id=request.request_id,
        project_id=request.project_id,
        run_id=request.run_id,
        mode=request.mode,
        required=request.required,
        status=ValidationStatus.OK,
        execution_state=state,
        process_result=process,
        artifact=execution.artifact,
        error_kind=ErrorKind.OK,
        first_error="",
        error_detail="",
        gf_version=execution.gf_version,
        release_evidence_eligible=(
            request.mode is ValidationMode.RELEASE
            and request.required
            and request.optimize
        ),
        warnings=_ordered_warnings(warnings),
    )


def skipped_pgf_build(
    request: PgfBuildRequest,
    *,
    reason: str,
) -> PgfBuildResult:
    """Represent one intentionally omitted optional PGF stage."""

    if not isinstance(request, PgfBuildRequest):
        raise TypeError("request must be a PgfBuildRequest")
    if request.required:
        raise ValueError("a required PGF build cannot be skipped")
    reason = _required_text(reason, field="reason")

    return PgfBuildResult(
        request_id=request.request_id,
        project_id=request.project_id,
        run_id=request.run_id,
        mode=request.mode,
        required=False,
        status=ValidationStatus.SKIPPED,
        execution_state=None,
        process_result=None,
        artifact=None,
        error_kind=ErrorKind.OK,
        first_error=reason,
        error_detail="",
        gf_version=None,
        release_evidence_eligible=False,
        warnings=(),
    )


def _validate_execution_identity(
    request: PgfBuildRequest,
    execution: PgfBuildExecution,
) -> None:
    process = execution.process_result

    if (
        process.operation_kind
        is not ProcessOperationKind.PGF_BUILD
    ):
        raise ValueError(
            "PGF execution must use operation kind pgf_build"
        )
    if process.operation_id != request.request_id:
        raise ValueError(
            "process operation_id does not match request_id"
        )
    if process.executable != request.gf_executable:
        raise ValueError(
            "process executable does not match the resolved GF executable"
        )
    if process.cwd != request.project_root:
        raise ValueError(
            "PGF process working directory must equal project_root"
        )
    if process.stdout_path != request.stdout_path:
        raise ValueError(
            "process stdout_path does not match the request"
        )
    if process.stderr_path != request.stderr_path:
        raise ValueError(
            "process stderr_path does not match the request"
        )


def _artifact_error(
    request: PgfBuildRequest,
    artifact: PgfArtifactEvidence,
) -> str | None:
    if artifact.path != request.expected_pgf_path:
        return "PGF build returned an unexpected artifact path"
    if not _is_strictly_within(
        artifact.path,
        request.artifact_root,
    ):
        return "PGF artifact escaped the run-owned artifact root"
    if not artifact.exists:
        return "GF completed without producing the expected PGF artifact"
    if not artifact.is_file:
        return "the expected PGF path is not a regular file"
    if not artifact.readable:
        return "the expected PGF artifact is not readable"
    if artifact.size_bytes is None or artifact.size_bytes == 0:
        return "the expected PGF artifact is empty"
    if artifact.sha256 is None:
        return "the expected PGF artifact has no recorded SHA-256"
    if not artifact.current_request:
        return "the PGF artifact is stale or not attributable to this request"
    if not artifact.identity_matches:
        return "the PGF artifact does not match the configured release identity"
    if (
        request.runtime_verification_required
        and artifact.runtime_verified is not True
    ):
        return "the required PGF runtime verification did not pass"
    if not artifact.catalogued:
        return "the PGF artifact was not registered for manifest publication"
    return None


def _failed_result(
    request: PgfBuildRequest,
    execution: PgfBuildExecution,
    *,
    status: ValidationStatus,
    error_kind: ErrorKind,
    first_error: str,
    error_detail: str | None = None,
) -> PgfBuildResult:
    if status not in {
        ValidationStatus.FAIL,
        ValidationStatus.ERROR,
    }:
        raise ValueError(
            "failed PGF result status must be FAIL or ERROR"
        )
    if error_kind is ErrorKind.OK:
        raise ValueError(
            "failed PGF result requires a non-OK error kind"
        )

    return PgfBuildResult(
        request_id=request.request_id,
        project_id=request.project_id,
        run_id=request.run_id,
        mode=request.mode,
        required=request.required,
        status=status,
        execution_state=execution.process_result.execution_state,
        process_result=execution.process_result,
        artifact=execution.artifact,
        error_kind=error_kind,
        first_error=_required_text(
            first_error,
            field="first_error",
        ),
        error_detail=(
            execution.error_detail
            if error_detail is None
            else _text(error_detail, field="error_detail")
        ),
        gf_version=execution.gf_version,
        release_evidence_eligible=False,
        warnings=_ordered_warnings(execution.warnings),
    )


def _error_result(
    request: PgfBuildRequest,
    execution: PgfBuildExecution,
    *,
    error_kind: ErrorKind,
    first_error: str,
    error_detail: str | None = None,
) -> PgfBuildResult:
    return _failed_result(
        request,
        execution,
        status=ValidationStatus.ERROR,
        error_kind=error_kind,
        first_error=first_error,
        error_detail=error_detail,
    )


def _non_ok_kind(
    value: ErrorKind,
    *,
    fallback: ErrorKind,
) -> ErrorKind:
    if not isinstance(value, ErrorKind):
        raise TypeError("error kind must be ErrorKind")
    if not isinstance(fallback, ErrorKind):
        raise TypeError("fallback must be ErrorKind")
    if fallback is ErrorKind.OK:
        raise ValueError("fallback must not be ErrorKind.OK")
    return fallback if value is ErrorKind.OK else value


def _ordered_warnings(
    values: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        warning = _required_text(
            value,
            field=f"warnings[{index}]",
        )
        if warning not in seen:
            seen.add(warning)
            result.append(warning)
    return tuple(result)


def _required_text(value: object, *, field: str) -> str:
    result = _text(value, field=field)
    if not result:
        raise ValueError(f"{field} must not be empty")
    return result


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _is_strictly_within(path: Path, root: Path) -> bool:
    return path != root and path.is_relative_to(root)


__all__ = (
    "build_release_pgf",
    "evaluate_pgf_build",
    "skipped_pgf_build",
)
