"""Unit tests for GF source-module compilation coordination."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
import inspect
import os
from pathlib import Path
from typing import Any, cast

import pytest
from tests.helpers.fake_processes import (
    make_cancelled_process_result,
    make_launch_failed_process_result,
    make_process_result,
    make_timed_out_process_result,
)

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ValidationStatus,
)
from gf_wordbench.validation.compilation.models import (
    CompileRequest,
    CompileSummary,
    CompileTarget,
    CompileTargetKind,
)
from gf_wordbench.validation.compilation.module_compile import (
    ArtifactVerifier,
    DiagnosticInterpreter,
    compile_checkpoint,
    compile_entrypoint,
    compile_module,
    compile_source,
    skipped_compile_summary,
)


@dataclass(frozen=True, slots=True)
class _DiagnosticFacts:
    error_kind: ErrorKind = ErrorKind.OK
    first_error: str = ""
    error_detail: str = ""
    fatal: bool = False
    reliable: bool = True


@dataclass(frozen=True, slots=True)
class _ArtifactFacts:
    expected_artifacts: tuple[Path, ...]
    produced_artifacts: tuple[Path, ...]
    checks_passed: bool = True
    reliable: bool = True
    error_kind: ErrorKind = ErrorKind.OK
    message: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class _CompileCase:
    request: CompileRequest
    process_request: ProcessRequest
    target: CompileTarget
    artifact_path: Path


class _Services:
    def __init__(self) -> None:
        self.execute_calls: list[ProcessRequest] = []
        self.interpret_calls: list[tuple[CompileRequest, ProcessResult]] = []
        self.verify_calls: list[tuple[CompileRequest, ProcessResult]] = []
        self.result_factory: Callable[[ProcessRequest], object] = self._completed_result
        self.diagnostics = _DiagnosticFacts()
        self.artifacts: _ArtifactFacts | None = None
        self.execute_error: Exception | None = None
        self.interpret_error: Exception | None = None
        self.verify_error: Exception | None = None

    def execute(self, request: ProcessRequest) -> ProcessResult:
        self.execute_calls.append(request)
        if self.execute_error is not None:
            raise self.execute_error
        return cast(ProcessResult, self.result_factory(request))

    def interpret(
        self,
        request: CompileRequest,
        result: ProcessResult,
    ) -> _DiagnosticFacts:
        self.interpret_calls.append((request, result))
        if self.interpret_error is not None:
            raise self.interpret_error
        return self.diagnostics

    def verify(
        self,
        request: CompileRequest,
        result: ProcessResult,
    ) -> _ArtifactFacts:
        self.verify_calls.append((request, result))
        if self.verify_error is not None:
            raise self.verify_error
        if self.artifacts is not None:
            return self.artifacts
        expected = tuple(item.path for item in request.process_request.expected_artifacts)
        return _ArtifactFacts(
            expected_artifacts=expected,
            produced_artifacts=expected,
        )

    @staticmethod
    def _completed_result(request: ProcessRequest) -> ProcessResult:
        observations = tuple(
            ArtifactObservation(
                path=item.path,
                role=item.role,
                required=item.required,
                exists=True,
                kind_matches=True,
                size_bytes=max(1, item.minimum_size_bytes),
            )
            for item in request.expected_artifacts
        )
        return make_process_result(
            request,
            artifact_observations=observations,
        )


def _make_executable(root: Path) -> Path:
    executable = root / "bin" / "gf"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_bytes(b"test executable")
    if os.name != "nt":
        executable.chmod(0o755)
    return executable.resolve()


def _bind_process_request(
    *,
    target: CompileTarget,
    process_request: ProcessRequest,
) -> CompileRequest:
    parameters = inspect.signature(CompileRequest).parameters
    if "process_request" in parameters:
        return CompileRequest(  # type: ignore[call-arg]
            target=target,
            process_request=process_request,
        )

    class _ProcessBackedCompileRequest(CompileRequest):
        __slots__ = ("_bound_process_request",)
        _bound_process_request: ProcessRequest

        def __init__(self) -> None:
            super().__init__(
                target=target,
                executable=process_request.executable,
                args=process_request.args,
                working_directory=process_request.cwd,
                environment=process_request.env_overrides,
                timeout_sec=process_request.timeout_sec,
                stdout_path=process_request.stdout_path,
                stderr_path=process_request.stderr_path,
                expected_artifacts=tuple(item.path for item in process_request.expected_artifacts),
            )
            object.__setattr__(
                self,
                "_bound_process_request",
                process_request,
            )

        @property
        def process_request(self) -> ProcessRequest:
            return self._bound_process_request

    return _ProcessBackedCompileRequest()


def _case(
    tmp_path: Path,
    *,
    kind: CompileTargetKind = CompileTargetKind.SOURCE,
    operation_kind: ProcessOperationKind = ProcessOperationKind.COMPILE,
    terminal_argument: str | None = None,
    target_artifacts: tuple[Path, ...] | None = None,
    process_artifacts: tuple[Path, ...] | None = None,
) -> _CompileCase:
    root = tmp_path.resolve()
    working_directory = root / "project"
    source_path = Path("src") / "Example.gf"
    absolute_source = working_directory / source_path
    absolute_source.parent.mkdir(parents=True, exist_ok=True)
    absolute_source.write_text(
        "abstract Example = { cat S ; }\n",
        encoding="utf-8",
    )

    artifact_root = root / "run" / "artifacts" / "gfo"
    artifact_root.mkdir(parents=True, exist_ok=True)
    default_artifact = artifact_root / "Example.gfo"
    target_expected = target_artifacts or (default_artifact,)
    process_expected = process_artifacts or target_expected

    target = CompileTarget(
        target_id="example",
        kind=kind,
        source_path=source_path,
        module_name="Example",
        required=True,
        expected_artifacts=target_expected,
        declared_order=0,
    )

    evidence_root = root / "run" / "raw" / "compile"
    evidence_root.mkdir(parents=True, exist_ok=True)
    process_request = ProcessRequest(
        request_id="compile-example",
        tool_id="gf",
        operation_id="compile-example",
        operation_kind=operation_kind,
        executable=_make_executable(root),
        args=(
            "-batch",
            terminal_argument if terminal_argument is not None else source_path.as_posix(),
        ),
        cwd=working_directory,
        stdout_path=evidence_root / "example.stdout.txt",
        stderr_path=evidence_root / "example.stderr.txt",
        timeout_sec=30.0,
        approved_read_roots=(root,),
        approved_write_roots=(root / "run",),
        evidence_policy="retain-raw-streams-v1",
        environment_policy="controlled-inherit-v1",
        env_removals=frozenset({"GF_LIB_PATH"}),
        expected_artifacts=tuple(
            ArtifactExpectation(
                path=path,
                role="gfo",
                required=True,
                kind=ArtifactKind.FILE,
                minimum_size_bytes=1,
            )
            for path in process_expected
        ),
        metadata={
            "gf_operation_kind": "compile_module",
            "target_module": "Example",
        },
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )
    request = _bind_process_request(
        target=target,
        process_request=process_request,
    )
    return _CompileCase(
        request=request,
        process_request=process_request,
        target=target,
        artifact_path=default_artifact,
    )


def _compile(
    case: _CompileCase,
    services: _Services,
) -> CompileSummary:
    return compile_module(
        case.request,
        interpret_diagnostics=cast(DiagnosticInterpreter, services.interpret),
        verify_artifacts=cast(ArtifactVerifier, services.verify),
        execute_process=services.execute,
    )


def test_success_preserves_process_and_artifact_evidence(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()

    summary = _compile(case, services)

    assert summary.target_id == "example"
    assert summary.target_kind is CompileTargetKind.SOURCE
    assert summary.status is ValidationStatus.OK
    assert summary.command == case.process_request.command
    assert summary.working_directory == case.process_request.cwd
    assert summary.exit_code == 0
    assert summary.launched is True
    assert summary.timed_out is False
    assert summary.cancelled is False
    assert summary.error_kind is ErrorKind.OK
    assert summary.first_error == ""
    assert summary.error_detail == ""
    assert summary.stdout_path == case.process_request.stdout_path
    assert summary.stderr_path == case.process_request.stderr_path
    assert summary.expected_artifacts == (case.artifact_path,)
    assert summary.produced_artifacts == (case.artifact_path,)
    assert summary.artifact_checks_passed is True
    assert services.execute_calls == [case.process_request]
    assert services.interpret_calls[0][0] is case.request
    assert services.verify_calls[0][0] is case.request


@pytest.mark.parametrize(
    "error_kind",
    (ErrorKind.TYPE, ErrorKind.SYNTAX, ErrorKind.OTHER),
)
def test_fatal_language_diagnostic_is_fail(
    tmp_path: Path,
    error_kind: ErrorKind,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.diagnostics = _DiagnosticFacts(
        error_kind=error_kind,
        first_error="GF rejected the module",
        error_detail="Example.gf:1",
        fatal=True,
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.FAIL
    assert summary.error_kind is error_kind
    assert summary.first_error == "GF rejected the module"
    assert summary.error_detail == "Example.gf:1"
    assert summary.exit_code == 0


def test_zero_exit_with_unclassified_fatal_diagnostic_is_other_failure(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.diagnostics = _DiagnosticFacts(
        error_kind=ErrorKind.OK,
        fatal=True,
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.FAIL
    assert summary.error_kind is ErrorKind.OTHER
    assert summary.first_error == "GF module compilation failed"


def test_nonzero_exit_without_recognized_diagnostic_remains_failure(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = lambda request: make_process_result(
        request,
        exit_code=9,
        artifact_observations=tuple(
            ArtifactObservation(
                path=item.path,
                role=item.role,
                required=item.required,
                exists=True,
                kind_matches=True,
                size_bytes=1,
            )
            for item in request.expected_artifacts
        ),
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.FAIL
    assert summary.error_kind is ErrorKind.OTHER
    assert summary.first_error == "GF exited with code 9"
    assert summary.exit_code == 9


@pytest.mark.parametrize(
    "error_kind",
    (
        ErrorKind.INTERNAL,
        ErrorKind.TIMEOUT,
        ErrorKind.SCRIPT,
        ErrorKind.CONFIG,
        ErrorKind.IO,
        ErrorKind.TOOL,
    ),
)
def test_technical_diagnostic_is_error(
    tmp_path: Path,
    error_kind: ErrorKind,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.diagnostics = _DiagnosticFacts(
        error_kind=error_kind,
        first_error="technical compilation failure",
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is error_kind
    assert summary.first_error == "technical compilation failure"


def test_launch_failure_is_tool_error_without_fabricated_exit_code(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = lambda request: make_launch_failed_process_result(
        request,
        message="GF executable could not start",
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.TOOL
    assert summary.first_error == "GF executable could not start"
    assert summary.exit_code is None
    assert summary.launched is False
    assert summary.timed_out is False
    assert summary.cancelled is False


def test_timeout_is_error_and_preserves_partial_evidence_paths(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = make_timed_out_process_result

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.TIMEOUT
    assert summary.first_error == "GF module compilation timed out"
    assert summary.exit_code is None
    assert summary.launched is True
    assert summary.timed_out is True
    assert summary.cancelled is False
    assert summary.stdout_path == case.process_request.stdout_path
    assert summary.stderr_path == case.process_request.stderr_path


def test_cancellation_is_error_without_language_failure_semantics(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = make_cancelled_process_result

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.TOOL
    assert summary.first_error == "GF module compilation was cancelled"
    assert summary.cancelled is True
    assert summary.timed_out is False


def test_incomplete_stream_capture_is_io_error(tmp_path: Path) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = lambda request: make_process_result(
        request,
        capture_complete=False,
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.IO
    assert summary.first_error == "compile process evidence capture is incomplete"


def test_unreliable_diagnostic_interpretation_is_script_error(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.diagnostics = _DiagnosticFacts(
        error_kind=ErrorKind.TYPE,
        first_error="diagnostic evidence is incomplete",
        reliable=False,
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.SCRIPT
    assert summary.first_error == "diagnostic evidence is incomplete"


def test_interpreter_exception_cannot_convert_failure_to_success(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.interpret_error = ValueError("parser exploded")

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.SCRIPT
    assert summary.first_error == "compile diagnostic interpretation failed"
    assert "ValueError: parser exploded" in summary.error_detail


def test_unreliable_artifact_verification_preserves_technical_kind(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.artifacts = _ArtifactFacts(
        expected_artifacts=(case.artifact_path,),
        produced_artifacts=(),
        checks_passed=False,
        reliable=False,
        error_kind=ErrorKind.IO,
        message="artifact evidence unreadable",
        detail="stat failed",
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.IO
    assert summary.first_error == "artifact evidence unreadable"
    assert summary.error_detail == "stat failed"
    assert summary.artifact_checks_passed is False


def test_missing_required_artifact_is_tool_error(tmp_path: Path) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.artifacts = _ArtifactFacts(
        expected_artifacts=(case.artifact_path,),
        produced_artifacts=(),
        checks_passed=False,
        error_kind=ErrorKind.TOOL,
        message="required .gfo is missing",
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.TOOL
    assert summary.first_error == "required .gfo is missing"
    assert summary.expected_artifacts == (case.artifact_path,)
    assert summary.produced_artifacts == ()


def test_language_kind_from_artifact_verifier_is_normalized_to_tool_error(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.artifacts = _ArtifactFacts(
        expected_artifacts=(case.artifact_path,),
        produced_artifacts=(),
        checks_passed=False,
        error_kind=ErrorKind.TYPE,
        message="artifact contract failed",
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.TOOL


def test_verifier_exception_is_structured_as_artifact_error(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.verify_error = OSError("artifact directory unavailable")

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.IO
    assert summary.first_error == "compile artifact verification failed"
    assert "OSError: artifact directory unavailable" in summary.error_detail
    assert summary.expected_artifacts == (case.artifact_path,)


def test_verifier_cannot_change_declared_expectation_identity(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    other = tmp_path / "run" / "artifacts" / "gfo" / "Other.gfo"
    services = _Services()
    services.artifacts = _ArtifactFacts(
        expected_artifacts=(other,),
        produced_artifacts=(other,),
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.INTERNAL
    assert summary.first_error == "artifact verifier changed the declared expectation set"
    assert "identities do not match" in summary.error_detail


def test_expected_artifact_identity_comparison_is_order_independent(
    tmp_path: Path,
) -> None:
    first = tmp_path / "run" / "artifacts" / "gfo" / "A.gfo"
    second = tmp_path / "run" / "artifacts" / "gfo" / "B.gfo"
    case = _case(
        tmp_path,
        target_artifacts=(first, second),
        process_artifacts=(second, first),
    )
    services = _Services()
    services.artifacts = _ArtifactFacts(
        expected_artifacts=(first, second),
        produced_artifacts=(first, second),
    )

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.OK
    assert summary.expected_artifacts == (first, second)


def test_executor_exception_returns_error_without_process_evidence(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.execute_error = OSError("process boundary unavailable")

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.IO
    assert summary.first_error == "GF module compilation could not execute"
    assert "OSError: process boundary unavailable" in summary.error_detail
    assert summary.exit_code is None
    assert summary.launched is False
    assert summary.stdout_path is None
    assert summary.stderr_path is None
    assert services.interpret_calls == []
    assert services.verify_calls == []


def test_executor_must_return_process_result(tmp_path: Path) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.result_factory = lambda request: object()

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.INTERNAL
    assert summary.first_error == "process executor returned an invalid result"
    assert "received object" in summary.error_detail
    assert services.interpret_calls == []
    assert services.verify_calls == []


def _replace_process_result_field(
    result: ProcessResult,
    field: str,
    replacement: object,
) -> ProcessResult:
    if field == "operation_id":
        return replace(result, operation_id=cast(str, replacement))
    if field == "args":
        return replace(result, args=cast(tuple[str, ...], replacement))
    if field == "cwd":
        return replace(result, cwd=cast(Path, replacement))
    if field == "stdout_path":
        return replace(result, stdout_path=cast(Path, replacement))
    if field == "stderr_path":
        return replace(result, stderr_path=cast(Path, replacement))
    raise AssertionError(f"unsupported test field: {field}")


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("operation_id", "different-operation"),
        ("args", ("-batch", "src/Other.gf")),
        ("cwd", Path("/different-working-directory")),
        ("stdout_path", Path("/different-stdout.txt")),
        ("stderr_path", Path("/different-stderr.txt")),
    ),
)
def test_contradictory_process_result_is_internal_error(
    tmp_path: Path,
    field: str,
    replacement: object,
) -> None:
    case = _case(tmp_path)
    services = _Services()

    def inconsistent(request: ProcessRequest) -> ProcessResult:
        result = make_process_result(request)
        return _replace_process_result_field(result, field, replacement)

    services.result_factory = inconsistent

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.INTERNAL
    assert summary.first_error == "process evidence contradicts the compile request"
    assert field in summary.error_detail
    assert services.interpret_calls == []
    assert services.verify_calls == []


@pytest.mark.parametrize(
    ("operation_kind", "terminal_argument", "process_artifacts"),
    (
        (ProcessOperationKind.VERSION_PROBE, None, None),
        (ProcessOperationKind.COMPILE, "src/Other.gf", None),
    ),
)
def test_invalid_module_request_is_configuration_error_before_launch(
    tmp_path: Path,
    operation_kind: ProcessOperationKind,
    terminal_argument: str | None,
    process_artifacts: tuple[Path, ...] | None,
) -> None:
    case = _case(
        tmp_path,
        operation_kind=operation_kind,
        terminal_argument=terminal_argument,
        process_artifacts=process_artifacts,
    )
    services = _Services()

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.CONFIG
    assert summary.first_error == "compile request validation failed"
    assert services.execute_calls == []


def test_target_and_process_artifact_sets_must_agree(tmp_path: Path) -> None:
    target_artifact = tmp_path / "run" / "artifacts" / "gfo" / "Example.gfo"
    process_artifact = tmp_path / "run" / "artifacts" / "gfo" / "Other.gfo"
    case = _case(
        tmp_path,
        target_artifacts=(target_artifact,),
        process_artifacts=(process_artifact,),
    )
    services = _Services()

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.CONFIG
    assert "disagree on expected artifacts" in summary.error_detail
    assert services.execute_calls == []


def test_process_request_validation_failure_is_configuration_error(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)
    case.process_request.executable.unlink()
    services = _Services()

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.CONFIG
    assert summary.first_error == "compile request validation failed"
    assert "Executable does not resolve" in summary.error_detail
    assert services.execute_calls == []


@pytest.mark.parametrize(
    ("compiler", "kind"),
    (
        (compile_source, CompileTargetKind.SOURCE),
        (compile_checkpoint, CompileTargetKind.CHECKPOINT),
        (compile_entrypoint, CompileTargetKind.ENTRYPOINT),
    ),
)
def test_kind_specific_compilers_delegate_for_matching_target(
    tmp_path: Path,
    compiler: Callable[..., Any],
    kind: CompileTargetKind,
) -> None:
    case = _case(tmp_path, kind=kind)
    services = _Services()

    summary = compiler(
        case.request,
        interpret_diagnostics=cast(DiagnosticInterpreter, services.interpret),
        verify_artifacts=cast(ArtifactVerifier, services.verify),
        execute_process=services.execute,
    )

    assert summary.status is ValidationStatus.OK
    assert summary.target_kind is kind
    assert services.execute_calls == [case.process_request]


@pytest.mark.parametrize(
    ("compiler", "actual_kind"),
    (
        (compile_source, CompileTargetKind.CHECKPOINT),
        (compile_checkpoint, CompileTargetKind.ENTRYPOINT),
        (compile_entrypoint, CompileTargetKind.SOURCE),
    ),
)
def test_kind_specific_compilers_reject_wrong_target(
    tmp_path: Path,
    compiler: Callable[..., Any],
    actual_kind: CompileTargetKind,
) -> None:
    case = _case(tmp_path, kind=actual_kind)
    services = _Services()

    with pytest.raises(ContractViolationError, match="expected"):
        compiler(
            case.request,
            interpret_diagnostics=cast(DiagnosticInterpreter, services.interpret),
            verify_artifacts=cast(ArtifactVerifier, services.verify),
            execute_process=services.execute,
        )

    assert services.execute_calls == []


def test_pgf_target_is_not_accepted_by_module_compiler(tmp_path: Path) -> None:
    case = _case(tmp_path, kind=CompileTargetKind.PGF)
    services = _Services()

    summary = _compile(case, services)

    assert summary.status is ValidationStatus.ERROR
    assert summary.error_kind is ErrorKind.CONFIG
    assert "accepts only source, checkpoint, or entrypoint" in summary.error_detail
    assert services.execute_calls == []


def test_skipped_summary_has_no_fabricated_process_evidence(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path)

    summary = skipped_compile_summary(
        case.request,
        reason="compilation disabled by explicit mode policy",
    )

    assert summary.status is ValidationStatus.SKIPPED
    assert summary.error_kind is ErrorKind.OK
    assert summary.first_error == "compilation disabled by explicit mode policy"
    assert summary.exit_code is None
    assert summary.launched is False
    assert summary.timed_out is False
    assert summary.cancelled is False
    assert summary.duration_ms == 0
    assert summary.stdout_path is None
    assert summary.stderr_path is None
    assert summary.expected_artifacts == (case.artifact_path,)
    assert summary.produced_artifacts == ()
    assert summary.artifact_checks_passed is False


@pytest.mark.parametrize("reason", ("", "   ", "bad\x00reason"))
def test_skipped_summary_requires_valid_reason(
    tmp_path: Path,
    reason: str,
) -> None:
    case = _case(tmp_path)

    with pytest.raises((TypeError, ValueError)):
        skipped_compile_summary(case.request, reason=reason)


def test_compile_messages_are_bounded(tmp_path: Path) -> None:
    case = _case(tmp_path)
    services = _Services()
    services.diagnostics = _DiagnosticFacts(
        error_kind=ErrorKind.TYPE,
        first_error="x" * 5_000,
        error_detail="y" * 5_000,
        fatal=True,
    )

    summary = _compile(case, services)

    assert len(summary.first_error) == 4_000
    assert len(summary.error_detail) == 4_000
    assert summary.first_error.endswith("…")
    assert summary.error_detail.endswith("…")


@pytest.mark.parametrize(
    "invalid_name",
    ("interpret_diagnostics", "verify_artifacts", "execute_process"),
)
def test_compile_dependencies_must_be_callable(
    tmp_path: Path,
    invalid_name: str,
) -> None:
    case = _case(tmp_path)
    services = _Services()
    arguments: dict[str, object] = {
        "interpret_diagnostics": services.interpret,
        "verify_artifacts": services.verify,
        "execute_process": services.execute,
    }
    arguments[invalid_name] = None

    with pytest.raises(TypeError, match=invalid_name):
        compile_module(case.request, **arguments)  # type: ignore[arg-type]

    assert services.execute_calls == []


def test_compile_request_type_is_enforced() -> None:
    services = _Services()

    with pytest.raises(TypeError, match="request must be a CompileRequest"):
        compile_module(
            object(),  # type: ignore[arg-type]
            interpret_diagnostics=cast(DiagnosticInterpreter, services.interpret),
            verify_artifacts=cast(ArtifactVerifier, services.verify),
            execute_process=services.execute,
        )
