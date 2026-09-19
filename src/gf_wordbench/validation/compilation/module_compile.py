"""Coordinate one GF source-module compilation attempt."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.infrastructure.process.requests import validate_process_request
from gf_wordbench.infrastructure.process.runner import run_process
from gf_wordbench.kernel.errors import (
    ConfigurationError,
    ContractViolationError,
    EvidenceIOError,
    GFWordbenchError,
    InfrastructureError,
    PathSecurityError,
    ProcessLaunchError,
)
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

from .models import (
    CompileRequest,
    CompileSummary,
    CompileTargetKind,
)

_MAX_MESSAGE_CHARS = 4_000
_LANGUAGE_FAILURE_KINDS = frozenset(
    {
        ErrorKind.TYPE,
        ErrorKind.SYNTAX,
        ErrorKind.OTHER,
    }
)
_TECHNICAL_ERROR_KINDS = frozenset(
    {
        ErrorKind.INTERNAL,
        ErrorKind.TIMEOUT,
        ErrorKind.SCRIPT,
        ErrorKind.CONFIG,
        ErrorKind.IO,
        ErrorKind.TOOL,
    }
)
_MODULE_TARGET_KINDS = frozenset(
    {
        CompileTargetKind.SOURCE,
        CompileTargetKind.CHECKPOINT,
        CompileTargetKind.ENTRYPOINT,
    }
)


class DiagnosticFacts(Protocol):
    error_kind: ErrorKind
    first_error: str
    error_detail: str
    fatal: bool
    reliable: bool


class ArtifactFacts(Protocol):
    expected_artifacts: tuple[Path, ...]
    produced_artifacts: tuple[Path, ...]
    checks_passed: bool
    reliable: bool
    error_kind: ErrorKind
    message: str
    detail: str


class DiagnosticInterpreter(Protocol):
    def __call__(
        self,
        request: CompileRequest,
        process_result: ProcessResult,
        /,
    ) -> DiagnosticFacts: ...


class ArtifactVerifier(Protocol):
    def __call__(
        self,
        request: CompileRequest,
        process_result: ProcessResult,
        /,
    ) -> ArtifactFacts: ...


ProcessExecutor = Callable[[ProcessRequest], object]


@dataclass(frozen=True, slots=True)
class _DiagnosticSnapshot:
    error_kind: ErrorKind
    first_error: str
    error_detail: str
    fatal: bool
    reliable: bool


@dataclass(frozen=True, slots=True)
class _ArtifactSnapshot:
    expected_artifacts: tuple[Path, ...]
    produced_artifacts: tuple[Path, ...]
    checks_passed: bool
    reliable: bool
    error_kind: ErrorKind
    message: str
    detail: str


def compile_module(
    request: CompileRequest,
    *,
    interpret_diagnostics: DiagnosticInterpreter,
    verify_artifacts: ArtifactVerifier,
    execute_process: ProcessExecutor = run_process,
) -> CompileSummary:
    _require_compile_request(request)
    _require_callable("interpret_diagnostics", interpret_diagnostics)
    _require_callable("verify_artifacts", verify_artifacts)
    _require_callable("execute_process", execute_process)

    process_request = _process_request(request)

    try:
        _validate_module_request(request)
        validate_process_request(process_request)
    except Exception as exc:
        return _summary_without_process(
            request,
            status=ValidationStatus.ERROR,
            error_kind=_exception_error_kind(exc),
            first_error="compile request validation failed",
            error_detail=_exception_detail(exc),
        )

    try:
        process_result = execute_process(process_request)
    except Exception as exc:
        return _summary_without_process(
            request,
            status=ValidationStatus.ERROR,
            error_kind=_exception_error_kind(exc),
            first_error="GF module compilation could not execute",
            error_detail=_exception_detail(exc),
        )

    if not isinstance(process_result, ProcessResult):
        return _summary_without_process(
            request,
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.INTERNAL,
            first_error="process executor returned an invalid result",
            error_detail=(f"expected ProcessResult, received {type(process_result).__name__}"),
        )

    consistency_error = _process_consistency_error(
        process_request,
        process_result,
    )
    if consistency_error:
        return _summary_from_process(
            request,
            process_result,
            status=ValidationStatus.ERROR,
            error_kind=ErrorKind.INTERNAL,
            first_error="process evidence contradicts the compile request",
            error_detail=consistency_error,
            artifact_facts=_artifact_facts_from_process(
                request,
                process_result,
            ),
        )

    diagnostic_facts = _interpret(
        request,
        process_result,
        interpret_diagnostics,
    )
    artifact_facts = _verify(
        request,
        process_result,
        verify_artifacts,
    )

    status, error_kind, first_error, error_detail = _classify(
        process_result,
        diagnostic_facts,
        artifact_facts,
    )

    return _summary_from_process(
        request,
        process_result,
        status=status,
        error_kind=error_kind,
        first_error=first_error,
        error_detail=error_detail,
        artifact_facts=artifact_facts,
    )


def compile_source(
    request: CompileRequest,
    *,
    interpret_diagnostics: DiagnosticInterpreter,
    verify_artifacts: ArtifactVerifier,
    execute_process: ProcessExecutor = run_process,
) -> CompileSummary:
    _require_target_kind(request, CompileTargetKind.SOURCE)
    return compile_module(
        request,
        interpret_diagnostics=interpret_diagnostics,
        verify_artifacts=verify_artifacts,
        execute_process=execute_process,
    )


def compile_checkpoint(
    request: CompileRequest,
    *,
    interpret_diagnostics: DiagnosticInterpreter,
    verify_artifacts: ArtifactVerifier,
    execute_process: ProcessExecutor = run_process,
) -> CompileSummary:
    _require_target_kind(request, CompileTargetKind.CHECKPOINT)
    return compile_module(
        request,
        interpret_diagnostics=interpret_diagnostics,
        verify_artifacts=verify_artifacts,
        execute_process=execute_process,
    )


def compile_entrypoint(
    request: CompileRequest,
    *,
    interpret_diagnostics: DiagnosticInterpreter,
    verify_artifacts: ArtifactVerifier,
    execute_process: ProcessExecutor = run_process,
) -> CompileSummary:
    _require_target_kind(request, CompileTargetKind.ENTRYPOINT)
    return compile_module(
        request,
        interpret_diagnostics=interpret_diagnostics,
        verify_artifacts=verify_artifacts,
        execute_process=execute_process,
    )


def skipped_compile_summary(
    request: CompileRequest,
    *,
    reason: str,
) -> CompileSummary:
    _require_compile_request(request)
    reason = _bounded_required_text("reason", reason)

    process_request = _process_request(request)
    expected = tuple(expectation.path for expectation in process_request.expected_artifacts)

    return CompileSummary(
        target_id=request.target.target_id,
        target_kind=request.target.kind,
        status=ValidationStatus.SKIPPED,
        command=process_request.command,
        working_directory=process_request.cwd,
        exit_code=None,
        launched=False,
        timed_out=False,
        cancelled=False,
        duration_ms=0,
        error_kind=ErrorKind.OK,
        first_error=reason,
        error_detail="",
        stdout_path=None,
        stderr_path=None,
        expected_artifacts=expected,
        produced_artifacts=(),
        artifact_checks_passed=False,
    )


def _process_request(request: CompileRequest) -> ProcessRequest:
    """Return a bound process request or translate the canonical compile request.

    Older callers may provide a read-only ``process_request`` compatibility
    property. New callers use the current ``CompileRequest`` fields and are
    translated here, which keeps process construction inside the compilation
    boundary instead of the domain model.
    """

    bound = getattr(request, "process_request", None)
    if bound is not None:
        if not isinstance(bound, ProcessRequest):
            raise TypeError("request.process_request must be a ProcessRequest")
        return bound

    target = request.target
    source_path = (
        target.source_path
        if target.source_path.is_absolute()
        else request.working_directory / target.source_path
    )
    expected_artifacts = tuple(
        ArtifactExpectation(
            path=path,
            role="gfo",
            required=target.required,
            kind=ArtifactKind.FILE,
            minimum_size_bytes=1,
        )
        for path in request.expected_artifacts
    )

    read_roots = _unique_roots(
        (
            request.working_directory,
            request.executable.parent,
            source_path.parent,
            *request.effective_gf_path,
        )
    )
    write_roots = _unique_roots(
        (
            request.stdout_path.parent,
            request.stderr_path.parent,
            *(path.parent for path in request.expected_artifacts),
        )
    )

    operation_id = f"compile-{target.target_id}"
    return ProcessRequest(
        request_id=operation_id,
        tool_id="gf",
        operation_id=operation_id,
        operation_kind=ProcessOperationKind.COMPILE,
        executable=request.executable,
        args=request.args,
        cwd=request.working_directory,
        stdout_path=request.stdout_path,
        stderr_path=request.stderr_path,
        timeout_sec=request.timeout_sec,
        approved_read_roots=read_roots,
        approved_write_roots=write_roots,
        evidence_policy="retain-raw-streams-v1",
        env_overrides=request.environment,
        expected_artifacts=expected_artifacts,
        metadata={
            "gf_operation_kind": "compile_module",
            "target_module": target.module_name,
        },
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )


def _unique_roots(values: Iterable[Path]) -> tuple[Path, ...]:
    roots: list[Path] = []
    keys: set[str] = set()
    for value in values:
        path = Path(value).resolve(strict=False)
        key = str(path).casefold()
        if key not in keys:
            keys.add(key)
            roots.append(path)
    return tuple(roots)


def _validate_module_request(request: CompileRequest) -> None:
    target = request.target
    process_request = _process_request(request)

    if target.kind not in _MODULE_TARGET_KINDS:
        raise ContractViolationError(
            "module compilation accepts only source, checkpoint, or entrypoint targets",
            code="GF-WB-CONTRACT-001",
            stage="compilation",
            operation="module_compile",
            subject=target.target_id,
        )

    if process_request.operation_kind is not ProcessOperationKind.COMPILE:
        raise ContractViolationError(
            "module compilation requires process operation kind 'compile'",
            code="GF-WB-CONTRACT-002",
            stage="compilation",
            operation="module_compile",
            subject=target.target_id,
        )

    if not process_request.args:
        raise ContractViolationError(
            "module compilation requires a terminal source argument",
            code="GF-WB-CONTRACT-003",
            stage="compilation",
            operation="module_compile",
            subject=target.target_id,
        )

    if not _terminal_source_matches(
        process_request.args[-1],
        process_request.cwd,
        target.source_path,
    ):
        raise ContractViolationError(
            "terminal process argument does not identify the compile target",
            code="GF-WB-CONTRACT-004",
            stage="compilation",
            operation="module_compile",
            subject=target.target_id,
        )

    request_expected = _path_keys(target.expected_artifacts)
    process_expected = _path_keys(
        expectation.path for expectation in process_request.expected_artifacts
    )
    if request_expected != process_expected:
        raise ContractViolationError(
            "compile target and process request disagree on expected artifacts",
            code="GF-WB-CONTRACT-005",
            stage="compilation",
            operation="module_compile",
            subject=target.target_id,
        )


def _process_consistency_error(
    request: ProcessRequest,
    result: ProcessResult,
) -> str:
    contradictions: list[str] = []

    if result.operation_id != request.operation_id:
        contradictions.append("operation_id")
    if result.operation_kind is not request.operation_kind:
        contradictions.append("operation_kind")
    if _path_key(result.executable) != _path_key(request.executable):
        contradictions.append("executable")
    if result.args != request.args:
        contradictions.append("args")
    if _path_key(result.cwd) != _path_key(request.cwd):
        contradictions.append("cwd")
    if _path_key(result.stdout_path) != _path_key(request.stdout_path):
        contradictions.append("stdout_path")
    if _path_key(result.stderr_path) != _path_key(request.stderr_path):
        contradictions.append("stderr_path")

    if not contradictions:
        return ""
    return "mismatched fields: " + ", ".join(contradictions)


def _interpret(
    request: CompileRequest,
    process_result: ProcessResult,
    interpreter: DiagnosticInterpreter,
) -> _DiagnosticSnapshot:
    try:
        facts = interpreter(request, process_result)
        return _snapshot_diagnostics(facts)
    except Exception as exc:
        return _DiagnosticSnapshot(
            error_kind=ErrorKind.SCRIPT,
            first_error="compile diagnostic interpretation failed",
            error_detail=_exception_detail(exc),
            fatal=True,
            reliable=False,
        )


def _verify(
    request: CompileRequest,
    process_result: ProcessResult,
    verifier: ArtifactVerifier,
) -> _ArtifactSnapshot:
    try:
        facts = verifier(request, process_result)
        snapshot = _snapshot_artifacts(facts)
    except Exception as exc:
        return _ArtifactSnapshot(
            expected_artifacts=tuple(
                expectation.path for expectation in _process_request(request).expected_artifacts
            ),
            produced_artifacts=tuple(
                observation.path
                for observation in process_result.artifact_observations
                if observation.exists
            ),
            checks_passed=False,
            reliable=False,
            error_kind=_exception_error_kind(exc),
            message="compile artifact verification failed",
            detail=_exception_detail(exc),
        )

    declared = _path_keys(
        expectation.path for expectation in _process_request(request).expected_artifacts
    )
    reported = _path_keys(snapshot.expected_artifacts)

    if declared != reported:
        return _ArtifactSnapshot(
            expected_artifacts=snapshot.expected_artifacts,
            produced_artifacts=snapshot.produced_artifacts,
            checks_passed=False,
            reliable=False,
            error_kind=ErrorKind.INTERNAL,
            message="artifact verifier changed the declared expectation set",
            detail="expected-artifact identities do not match the request",
        )

    return snapshot


def _classify(
    process_result: ProcessResult,
    diagnostics: _DiagnosticSnapshot,
    artifacts: _ArtifactSnapshot,
) -> tuple[ValidationStatus, ErrorKind, str, str]:
    if process_result.execution_state is ExecutionState.LAUNCH_FAILED:
        return (
            ValidationStatus.ERROR,
            ErrorKind.TOOL,
            process_result.launch_error_message or "GF process launch failed",
            diagnostics.error_detail,
        )

    if process_result.execution_state is ExecutionState.TIMED_OUT:
        return (
            ValidationStatus.ERROR,
            ErrorKind.TIMEOUT,
            "GF module compilation timed out",
            diagnostics.error_detail,
        )

    if process_result.execution_state is ExecutionState.CANCELLED:
        return (
            ValidationStatus.ERROR,
            ErrorKind.TOOL,
            "GF module compilation was cancelled",
            diagnostics.error_detail,
        )

    if not process_result.capture_complete:
        return (
            ValidationStatus.ERROR,
            ErrorKind.IO,
            "compile process evidence capture is incomplete",
            diagnostics.error_detail,
        )

    if not diagnostics.reliable:
        return (
            ValidationStatus.ERROR,
            ErrorKind.SCRIPT,
            diagnostics.first_error,
            diagnostics.error_detail,
        )

    if not artifacts.reliable:
        return (
            ValidationStatus.ERROR,
            _technical_or_default(artifacts.error_kind, ErrorKind.TOOL),
            artifacts.message or "compile artifact verification is unreliable",
            artifacts.detail,
        )

    if not artifacts.checks_passed:
        return (
            ValidationStatus.ERROR,
            _technical_or_default(artifacts.error_kind, ErrorKind.TOOL),
            artifacts.message or "required compile artifact checks failed",
            artifacts.detail,
        )

    if diagnostics.error_kind in _TECHNICAL_ERROR_KINDS:
        if diagnostics.error_kind is ErrorKind.OK:
            raise AssertionError("ErrorKind.OK cannot be technical")
        return (
            ValidationStatus.ERROR,
            diagnostics.error_kind,
            diagnostics.first_error or "compile interpretation reported an error",
            diagnostics.error_detail,
        )

    if diagnostics.fatal:
        return (
            ValidationStatus.FAIL,
            _language_or_default(diagnostics.error_kind),
            diagnostics.first_error or "GF module compilation failed",
            diagnostics.error_detail,
        )

    if process_result.exit_code != 0:
        return (
            ValidationStatus.FAIL,
            _language_or_default(diagnostics.error_kind),
            diagnostics.first_error or f"GF exited with code {process_result.exit_code}",
            diagnostics.error_detail,
        )

    return (
        ValidationStatus.OK,
        ErrorKind.OK,
        "",
        diagnostics.error_detail,
    )


def _summary_without_process(
    request: CompileRequest,
    *,
    status: ValidationStatus,
    error_kind: ErrorKind,
    first_error: str,
    error_detail: str,
) -> CompileSummary:
    process_request = _process_request(request)
    expected = tuple(expectation.path for expectation in process_request.expected_artifacts)

    return CompileSummary(
        target_id=request.target.target_id,
        target_kind=request.target.kind,
        status=status,
        command=process_request.command,
        working_directory=process_request.cwd,
        exit_code=None,
        launched=False,
        timed_out=False,
        cancelled=False,
        duration_ms=0,
        error_kind=error_kind,
        first_error=_bounded_text(first_error),
        error_detail=_bounded_text(error_detail),
        stdout_path=None,
        stderr_path=None,
        expected_artifacts=expected,
        produced_artifacts=(),
        artifact_checks_passed=False,
    )


def _summary_from_process(
    request: CompileRequest,
    process_result: ProcessResult,
    *,
    status: ValidationStatus,
    error_kind: ErrorKind,
    first_error: str,
    error_detail: str,
    artifact_facts: _ArtifactSnapshot,
) -> CompileSummary:
    return CompileSummary(
        target_id=request.target.target_id,
        target_kind=request.target.kind,
        status=status,
        command=process_result.command,
        working_directory=process_result.cwd,
        exit_code=process_result.exit_code,
        launched=process_result.execution_state is not ExecutionState.LAUNCH_FAILED,
        timed_out=process_result.execution_state is ExecutionState.TIMED_OUT,
        cancelled=process_result.execution_state is ExecutionState.CANCELLED,
        duration_ms=process_result.duration_ms,
        error_kind=error_kind,
        first_error=_bounded_text(first_error),
        error_detail=_bounded_text(error_detail),
        stdout_path=process_result.stdout_path,
        stderr_path=process_result.stderr_path,
        expected_artifacts=artifact_facts.expected_artifacts,
        produced_artifacts=artifact_facts.produced_artifacts,
        artifact_checks_passed=artifact_facts.checks_passed,
    )


def _artifact_facts_from_process(
    request: CompileRequest,
    process_result: ProcessResult,
) -> _ArtifactSnapshot:
    expected = tuple(expectation.path for expectation in _process_request(request).expected_artifacts)
    produced = tuple(
        observation.path
        for observation in process_result.artifact_observations
        if observation.exists
    )
    required_passed = all(
        observation.exists and observation.kind_matches
        for observation in process_result.artifact_observations
        if observation.required
    )
    return _ArtifactSnapshot(
        expected_artifacts=expected,
        produced_artifacts=produced,
        checks_passed=required_passed,
        reliable=True,
        error_kind=ErrorKind.OK if required_passed else ErrorKind.TOOL,
        message="" if required_passed else "required artifact checks failed",
        detail="",
    )


def _snapshot_diagnostics(facts: DiagnosticFacts) -> _DiagnosticSnapshot:
    if not isinstance(facts.error_kind, ErrorKind):
        raise TypeError("diagnostic error_kind must be an ErrorKind")
    if type(facts.fatal) is not bool:
        raise TypeError("diagnostic fatal must be a bool")
    if type(facts.reliable) is not bool:
        raise TypeError("diagnostic reliable must be a bool")

    return _DiagnosticSnapshot(
        error_kind=facts.error_kind,
        first_error=_bounded_text(facts.first_error),
        error_detail=_bounded_text(facts.error_detail),
        fatal=facts.fatal,
        reliable=facts.reliable,
    )


def _snapshot_artifacts(facts: ArtifactFacts) -> _ArtifactSnapshot:
    if type(facts.checks_passed) is not bool:
        raise TypeError("artifact checks_passed must be a bool")
    if type(facts.reliable) is not bool:
        raise TypeError("artifact reliable must be a bool")
    if not isinstance(facts.error_kind, ErrorKind):
        raise TypeError("artifact error_kind must be an ErrorKind")

    return _ArtifactSnapshot(
        expected_artifacts=_paths(facts.expected_artifacts),
        produced_artifacts=_paths(facts.produced_artifacts),
        checks_passed=facts.checks_passed,
        reliable=facts.reliable,
        error_kind=facts.error_kind,
        message=_bounded_text(facts.message),
        detail=_bounded_text(facts.detail),
    )


def _require_compile_request(value: object) -> CompileRequest:
    if not isinstance(value, CompileRequest):
        raise TypeError("request must be a CompileRequest")
    return value


def _require_target_kind(
    request: CompileRequest,
    expected: CompileTargetKind,
) -> None:
    _require_compile_request(request)
    if request.target.kind is not expected:
        raise ContractViolationError(
            f"expected {expected.value!r} compile target, received {request.target.kind.value!r}",
            code="GF-WB-CONTRACT-006",
            stage="compilation",
            operation=f"compile_{expected.value}",
            subject=request.target.target_id,
        )


def _terminal_source_matches(
    argument: str,
    cwd: Path,
    source_path: Path,
) -> bool:
    argument_path = Path(argument)
    candidate = argument_path if argument_path.is_absolute() else cwd / argument_path
    source = source_path if source_path.is_absolute() else cwd / source_path
    return _path_key(candidate) == _path_key(source)


def _paths(values: Iterable[Path]) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError("path collection must be an iterable of Path values")
    result = tuple(values)
    if not all(isinstance(path, Path) for path in result):
        raise TypeError("path collection must contain only Path values")
    return result


def _path_keys(values: Iterable[Path]) -> tuple[str, ...]:
    return tuple(sorted(_path_key(path) for path in _paths(values)))


def _path_key(path: Path) -> str:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return str(path.resolve(strict=False)).casefold()


def _require_callable(name: str, value: object) -> None:
    if not callable(value):
        raise TypeError(f"{name} must be callable")


def _bounded_required_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return _bounded_text(value)


def _bounded_text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("text value must be a string")
    value = value.replace("\x00", "")
    if len(value) <= _MAX_MESSAGE_CHARS:
        return value
    return value[: _MAX_MESSAGE_CHARS - 1] + "…"


def _exception_detail(exc: Exception) -> str:
    if isinstance(exc, GFWordbenchError):
        details = [exc.message]
        if exc.detail:
            details.append(exc.detail)
        return _bounded_text(": ".join(details))
    return _bounded_text(f"{type(exc).__name__}: {exc}")


def _exception_error_kind(exc: Exception) -> ErrorKind:
    if isinstance(
        exc,
        (
            ConfigurationError,
            ContractViolationError,
            PathSecurityError,
        ),
    ):
        return ErrorKind.CONFIG
    if isinstance(exc, ProcessLaunchError):
        return ErrorKind.TOOL
    if isinstance(exc, (EvidenceIOError, OSError)):
        return ErrorKind.IO
    if isinstance(exc, InfrastructureError):
        return ErrorKind.TOOL
    return ErrorKind.INTERNAL


def _technical_or_default(
    value: ErrorKind,
    default: ErrorKind,
) -> ErrorKind:
    return value if value in _TECHNICAL_ERROR_KINDS else default


def _language_or_default(value: ErrorKind) -> ErrorKind:
    return value if value in _LANGUAGE_FAILURE_KINDS else ErrorKind.OTHER


__all__ = (
    "ArtifactFacts",
    "ArtifactVerifier",
    "DiagnosticFacts",
    "DiagnosticInterpreter",
    "ProcessExecutor",
    "compile_checkpoint",
    "compile_entrypoint",
    "compile_module",
    "compile_source",
    "skipped_compile_summary",
)
