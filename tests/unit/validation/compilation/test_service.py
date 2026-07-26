"""Unit tests for compilation orchestration and continuation policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.infrastructure.process.models import (
    ProcessOperationKind,
    ProcessResult,
)
from gf_wordbench.kernel.errors import CancellationRequested
from gf_wordbench.kernel.statuses import ErrorKind, ExecutionState, ValidationStatus
from gf_wordbench.validation.compilation.models import (
    CompilePlan,
    CompileRequest,
    CompileSummary,
    CompileTarget,
    CompileTargetKind,
)
from gf_wordbench.validation.compilation.service import (
    CompilationExecutor,
    CompilationObserver,
    CompilationPreflight,
    CompilationPreflightValidator,
    CompilationRequestBuilder,
    CompilationService,
    CompilationSummaryFactory,
)


@dataclass(slots=True)
class _PreflightValidator:
    result: CompilationPreflight = field(default_factory=CompilationPreflight.ok)
    calls: list[CompilePlan] = field(default_factory=list)

    def validate(self, plan: CompilePlan) -> CompilationPreflight:
        self.calls.append(plan)
        return self.result


@dataclass(slots=True)
class _RequestBuilder:
    root: Path
    calls: list[tuple[CompileTarget, bool]] = field(default_factory=list)
    error: Exception | None = None
    target_override: CompileTarget | None = None

    def build(
        self,
        target: CompileTarget,
        *,
        clean_build: bool,
    ) -> CompileRequest:
        self.calls.append((target, clean_build))
        if self.error is not None:
            raise self.error
        request_target = self.target_override or target
        return _request(request_target, self.root)


@dataclass(slots=True)
class _Executor:
    result: ProcessResult
    calls: list[tuple[CompileRequest, object | None]] = field(default_factory=list)
    error: Exception | None = None
    return_value: object | None = None

    def execute(
        self,
        request: CompileRequest,
        *,
        cancellation_token: object | None = None,
    ) -> ProcessResult:
        self.calls.append((request, cancellation_token))
        if self.error is not None:
            raise self.error
        if self.return_value is not None:
            return self.return_value  # type: ignore[return-value]
        return self.result


@dataclass(slots=True)
class _SummaryFactory:
    status_by_target: dict[str, ValidationStatus] = field(default_factory=dict)
    calls: list[tuple[str, str, object]] = field(default_factory=list)
    target_id_override: str | None = None
    skipped_status: ValidationStatus = ValidationStatus.SKIPPED

    def from_process(
        self,
        target: CompileTarget,
        request: CompileRequest,
        process_result: ProcessResult,
    ) -> CompileSummary:
        self.calls.append(("from_process", target.target_id, process_result))
        return _summary(
            target,
            status=self.status_by_target.get(target.target_id, ValidationStatus.OK),
            target_id=self.target_id_override,
            request=request,
            process_result=process_result,
        )

    def from_exception(
        self,
        target: CompileTarget,
        error: Exception,
        *,
        request: CompileRequest | None,
    ) -> CompileSummary:
        self.calls.append(("from_exception", target.target_id, error))
        return _summary(
            target,
            status=ValidationStatus.ERROR,
            target_id=self.target_id_override,
            request=request,
            error_kind=ErrorKind.SCRIPT,
            first_error=str(error),
        )

    def preflight_error(
        self,
        target: CompileTarget,
        *,
        error_kind: ErrorKind,
        message: str,
        detail: str,
    ) -> CompileSummary:
        self.calls.append(("preflight_error", target.target_id, error_kind))
        return _summary(
            target,
            status=ValidationStatus.ERROR,
            target_id=self.target_id_override,
            error_kind=error_kind,
            first_error=message,
            error_detail=detail,
        )

    def skipped(
        self,
        target: CompileTarget,
        *,
        reason: str,
    ) -> CompileSummary:
        self.calls.append(("skipped", target.target_id, reason))
        return _summary(
            target,
            status=self.skipped_status,
            target_id=self.target_id_override,
            skipped_reason=reason,
        )


@dataclass(slots=True)
class _Observer:
    events: list[tuple[Any, ...]] = field(default_factory=list)

    def plan_started(self, plan: CompilePlan) -> None:
        self.events.append(("plan_started", plan))

    def preflight_completed(
        self,
        plan: CompilePlan,
        result: CompilationPreflight,
    ) -> None:
        self.events.append(("preflight_completed", plan, result))

    def target_started(
        self,
        target: CompileTarget,
        index: int,
        total: int,
    ) -> None:
        self.events.append(("target_started", target.target_id, index, total))

    def target_completed(
        self,
        target: CompileTarget,
        summary: CompileSummary,
        index: int,
        total: int,
    ) -> None:
        self.events.append(
            ("target_completed", target.target_id, summary.status, index, total)
        )

    def plan_completed(
        self,
        plan: CompilePlan,
        summaries: tuple[CompileSummary, ...],
    ) -> None:
        self.events.append(("plan_completed", plan, summaries))


@dataclass(slots=True)
class _CancellationToken:
    cancelled: bool = False
    cancellation_reason: str = "user"

    def is_cancelled(self) -> bool:
        return self.cancelled

    def reason(self) -> str:
        return self.cancellation_reason


@dataclass(slots=True)
class _CancelAfterBuildBuilder(_RequestBuilder):
    token: _CancellationToken = field(default_factory=_CancellationToken)

    def build(
        self,
        target: CompileTarget,
        *,
        clean_build: bool,
    ) -> CompileRequest:
        request = super().build(target, clean_build=clean_build)
        self.token.cancelled = True
        return request


def _target(
    target_id: str,
    *,
    kind: CompileTargetKind = CompileTargetKind.SOURCE,
    required: bool = True,
    order: int = 0,
) -> CompileTarget:
    module_name = target_id.replace("-", "_").title().replace("_", "")
    return CompileTarget(
        target_id=target_id,
        kind=kind,
        source_path=Path("src") / f"{module_name}.gf",
        module_name=module_name,
        required=required,
        expected_artifacts=(Path("artifacts") / f"{module_name}.gfo",),
        declared_order=order,
        entrypoint_modules=(module_name,) if kind is CompileTargetKind.PGF else (),
    )


def _plan(
    *targets: CompileTarget,
    clean_build: bool = True,
    fail_fast: bool = False,
) -> CompilePlan:
    return CompilePlan(
        mode="diagnostic",
        targets=tuple(targets),
        clean_build=clean_build,
        fail_fast=fail_fast,
        gf_version_required=True,
    )


def _request(target: CompileTarget, root: Path) -> CompileRequest:
    return CompileRequest(
        target=target,
        executable=root / "bin" / "gf",
        args=("-batch", target.source_path.as_posix()),
        working_directory=root,
        environment={},
        timeout_sec=30.0,
        stdout_path=root / "logs" / f"{target.target_id}.out.txt",
        stderr_path=root / "logs" / f"{target.target_id}.err.txt",
        expected_artifacts=tuple(root / path for path in target.expected_artifacts),
        effective_gf_path=(root / "src",),
    )


def _process_result(root: Path) -> ProcessResult:
    started_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    return ProcessResult(
        operation_id="compile",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=root / "bin" / "gf",
        args=("-batch", "src/Grammar.gf"),
        cwd=root,
        execution_state=ExecutionState.COMPLETED,
        exit_code=0,
        pid=1234,
        started_at=started_at,
        finished_at=started_at + timedelta(milliseconds=25),
        duration_ms=25,
        cancellation_reason=None,
        launch_error_kind=None,
        launch_error_message="",
        termination_attempted=False,
        termination_succeeded=False,
        stdout_path=root / "logs" / "compile.out.txt",
        stderr_path=root / "logs" / "compile.err.txt",
        stdout_size_bytes=0,
        stderr_size_bytes=0,
        output_limit_exceeded=False,
        capture_complete=True,
        environment_policy="controlled-inherit-v1",
    )


def _summary(
    target: CompileTarget,
    *,
    status: ValidationStatus,
    target_id: str | None = None,
    request: CompileRequest | None = None,
    process_result: ProcessResult | None = None,
    error_kind: ErrorKind = ErrorKind.OK,
    first_error: str = "",
    error_detail: str = "",
    skipped_reason: str = "",
) -> CompileSummary:
    command = request.command if request is not None else ()
    working_directory = (
        request.working_directory.as_posix() if request is not None else ""
    )
    expected_artifacts = (
        tuple(path.as_posix() for path in request.expected_artifacts)
        if request is not None
        else tuple(path.as_posix() for path in target.expected_artifacts)
    )
    return CompileSummary(
        target_id=target_id or target.target_id,
        target_kind=target.kind.value,
        status=status,
        command=command,
        working_directory=working_directory,
        exit_code=process_result.exit_code if process_result is not None else None,
        launched=process_result is not None,
        timed_out=(
            process_result is not None
            and process_result.execution_state is ExecutionState.TIMED_OUT
        ),
        cancelled=(
            process_result is not None
            and process_result.execution_state is ExecutionState.CANCELLED
        ),
        duration_ms=process_result.duration_ms if process_result is not None else 0,
        error_kind=error_kind,
        first_error=first_error,
        error_detail=error_detail,
        stdout_path=(
            process_result.stdout_path.as_posix() if process_result is not None else None
        ),
        stderr_path=(
            process_result.stderr_path.as_posix() if process_result is not None else None
        ),
        expected_artifacts=expected_artifacts,
        produced_artifacts=(),
        artifact_checks_passed=status is ValidationStatus.OK,
        skipped_reason=skipped_reason,
    )


def _service(
    tmp_path: Path,
    *,
    preflight: CompilationPreflight | None = None,
    statuses: dict[str, ValidationStatus] | None = None,
    observer: _Observer | None = None,
) -> tuple[
    CompilationService,
    _PreflightValidator,
    _RequestBuilder,
    _Executor,
    _SummaryFactory,
]:
    validator = _PreflightValidator(preflight or CompilationPreflight.ok())
    builder = _RequestBuilder(tmp_path)
    executor = _Executor(_process_result(tmp_path))
    factory = _SummaryFactory(statuses or {})
    return (
        CompilationService(validator, builder, executor, factory, observer),
        validator,
        builder,
        executor,
        factory,
    )


def test_protocol_fakes_satisfy_public_service_ports(tmp_path: Path) -> None:
    validator = _PreflightValidator()
    builder = _RequestBuilder(tmp_path)
    executor = _Executor(_process_result(tmp_path))
    factory = _SummaryFactory()
    observer = _Observer()

    assert isinstance(validator, CompilationPreflightValidator)
    assert isinstance(builder, CompilationRequestBuilder)
    assert isinstance(executor, CompilationExecutor)
    assert isinstance(factory, CompilationSummaryFactory)
    assert isinstance(observer, CompilationObserver)


def test_preflight_value_object_enforces_success_and_failure_coherence() -> None:
    assert CompilationPreflight.ok().succeeded is True
    failed = CompilationPreflight.failed(
        error_kind=ErrorKind.CONFIG,
        message=" invalid project ",
        detail=" missing source root ",
        warnings=("warning",),
    )
    assert failed.succeeded is False
    assert failed.message == "invalid project"
    assert failed.detail == "missing source root"
    assert failed.warnings == ("warning",)

    with pytest.raises(ValueError, match="successful preflight"):
        CompilationPreflight(succeeded=True, error_kind=ErrorKind.CONFIG)
    with pytest.raises(ValueError, match="failed preflight"):
        CompilationPreflight(succeeded=False, error_kind=ErrorKind.OK, message="bad")
    with pytest.raises(ValueError, match="requires a message"):
        CompilationPreflight(succeeded=False, error_kind=ErrorKind.CONFIG)
    with pytest.raises(ValueError, match="duplicate"):
        CompilationPreflight.ok(warnings=("same", "same"))


def test_validate_plan_delegates_once_and_notifies_observer(tmp_path: Path) -> None:
    target = _target("source")
    plan = _plan(target)
    observer = _Observer()
    service, validator, builder, executor, factory = _service(
        tmp_path,
        observer=observer,
    )

    result = service.validate_plan(plan)

    assert result == CompilationPreflight.ok()
    assert validator.calls == [plan]
    assert builder.calls == []
    assert executor.calls == []
    assert factory.calls == []
    assert observer.events == [("preflight_completed", plan, result)]


def test_failed_preflight_creates_one_error_summary_per_target_without_launch(
    tmp_path: Path,
) -> None:
    targets = (_target("first", order=0), _target("second", order=1))
    plan = _plan(*targets)
    preflight = CompilationPreflight.failed(
        error_kind=ErrorKind.TOOL,
        message="GF executable unavailable",
        detail="configured path does not exist",
    )
    observer = _Observer()
    service, validator, builder, executor, factory = _service(
        tmp_path,
        preflight=preflight,
        observer=observer,
    )

    summaries = service.execute_plan(plan)

    assert validator.calls == [plan]
    assert builder.calls == []
    assert executor.calls == []
    assert [summary.status for summary in summaries] == [
        ValidationStatus.ERROR,
        ValidationStatus.ERROR,
    ]
    assert [call[0] for call in factory.calls] == [
        "preflight_error",
        "preflight_error",
    ]
    assert observer.events[0] == ("plan_started", plan)
    assert observer.events[1] == ("preflight_completed", plan, preflight)
    assert observer.events[-1] == ("plan_completed", plan, summaries)
    assert not any(event[0] == "target_started" for event in observer.events)


def test_no_compile_returns_explicit_skips_without_building_requests(
    tmp_path: Path,
) -> None:
    targets = (_target("first", order=0), _target("second", order=1))
    plan = _plan(*targets)
    service, _, builder, executor, factory = _service(tmp_path)

    summaries = service.execute_plan(plan, no_compile=True)

    assert builder.calls == []
    assert executor.calls == []
    assert [summary.status for summary in summaries] == [
        ValidationStatus.SKIPPED,
        ValidationStatus.SKIPPED,
    ]
    assert factory.calls == [
        ("skipped", "first", "no_compile"),
        ("skipped", "second", "no_compile"),
    ]


def test_successful_plan_preserves_declared_order_and_clean_build_flag(
    tmp_path: Path,
) -> None:
    targets = (_target("first", order=0), _target("second", order=1))
    plan = _plan(*targets, clean_build=False)
    observer = _Observer()
    service, _, builder, executor, factory = _service(tmp_path, observer=observer)

    summaries = service.execute_plan(plan)

    assert [summary.target_id for summary in summaries] == ["first", "second"]
    assert builder.calls == [(targets[0], False), (targets[1], False)]
    assert [call[0].target.target_id for call in executor.calls] == ["first", "second"]
    assert [call[0] for call in factory.calls] == ["from_process", "from_process"]
    assert [event[0] for event in observer.events] == [
        "plan_started",
        "preflight_completed",
        "target_started",
        "target_completed",
        "target_started",
        "target_completed",
        "plan_completed",
    ]
    assert observer.events[2] == ("target_started", "first", 1, 2)
    assert observer.events[4] == ("target_started", "second", 2, 2)


def test_fail_fast_skips_remaining_targets_after_required_failure(
    tmp_path: Path,
) -> None:
    targets = (
        _target("required-failure", required=True, order=0),
        _target("later", required=True, order=1),
    )
    service, _, builder, executor, factory = _service(
        tmp_path,
        statuses={"required-failure": ValidationStatus.FAIL},
    )

    summaries = service.execute_plan(_plan(*targets, fail_fast=True))

    assert [summary.status for summary in summaries] == [
        ValidationStatus.FAIL,
        ValidationStatus.SKIPPED,
    ]
    assert [target.target_id for target, _ in builder.calls] == ["required-failure"]
    assert len(executor.calls) == 1
    assert factory.calls[-1] == ("skipped", "later", "fail_fast")


def test_fail_fast_does_not_stop_after_optional_failure(tmp_path: Path) -> None:
    targets = (
        _target("optional-failure", required=False, order=0),
        _target("later", required=True, order=1),
    )
    service, _, builder, executor, _ = _service(
        tmp_path,
        statuses={"optional-failure": ValidationStatus.FAIL},
    )

    summaries = service.execute_plan(_plan(*targets, fail_fast=True))

    assert [summary.status for summary in summaries] == [
        ValidationStatus.FAIL,
        ValidationStatus.OK,
    ]
    assert [target.target_id for target, _ in builder.calls] == [
        "optional-failure",
        "later",
    ]
    assert len(executor.calls) == 2


def test_pre_cancelled_plan_skips_every_target_without_building_requests(
    tmp_path: Path,
) -> None:
    targets = (_target("first", order=0), _target("second", order=1))
    token = _CancellationToken(cancelled=True)
    service, _, builder, executor, factory = _service(tmp_path)

    summaries = service.execute_plan(_plan(*targets), cancellation_token=token)

    assert [summary.status for summary in summaries] == [
        ValidationStatus.SKIPPED,
        ValidationStatus.SKIPPED,
    ]
    assert builder.calls == []
    assert executor.calls == []
    assert factory.calls == [
        ("skipped", "first", "cancelled"),
        ("skipped", "second", "cancelled"),
    ]


def test_cancellation_after_request_build_prevents_process_launch(tmp_path: Path) -> None:
    target = _target("source")
    token = _CancellationToken()
    validator = _PreflightValidator()
    builder = _CancelAfterBuildBuilder(tmp_path, token=token)
    executor = _Executor(_process_result(tmp_path))
    factory = _SummaryFactory()
    service = CompilationService(validator, builder, executor, factory)

    summary = service.compile_target(target, cancellation_token=token)

    assert summary.status is ValidationStatus.SKIPPED
    assert builder.calls == [(target, True)]
    assert executor.calls == []
    assert factory.calls == [("skipped", "source", "cancelled")]


def test_cancellation_exception_is_converted_to_skip(tmp_path: Path) -> None:
    target = _target("source")
    service, _, _, executor, factory = _service(tmp_path)
    executor.error = CancellationRequested("cancelled by caller")

    summary = service.compile_target(target)

    assert summary.status is ValidationStatus.SKIPPED
    assert factory.calls == [("skipped", "source", "cancelled")]


@pytest.mark.parametrize(
    "error",
    [
        OSError("capture unavailable"),
        ValueError("invalid request"),
        RuntimeError("unexpected adapter failure"),
    ],
)
def test_execution_exceptions_are_converted_by_summary_factory(
    tmp_path: Path,
    error: Exception,
) -> None:
    target = _target("source")
    service, _, _, executor, factory = _service(tmp_path)
    executor.error = error

    summary = service.compile_target(target)

    assert summary.status is ValidationStatus.ERROR
    assert summary.first_error == str(error)
    assert factory.calls[0][0:2] == ("from_exception", "source")
    assert factory.calls[0][2] is error


def test_builder_exception_is_converted_without_a_request(tmp_path: Path) -> None:
    target = _target("source")
    service, _, builder, executor, factory = _service(tmp_path)
    error = ValueError("source escaped approved roots")
    builder.error = error

    summary = service.compile_target(target)

    assert summary.status is ValidationStatus.ERROR
    assert executor.calls == []
    assert factory.calls == [("from_exception", "source", error)]


def test_non_process_executor_result_is_converted_to_error(tmp_path: Path) -> None:
    target = _target("source")
    service, _, _, executor, factory = _service(tmp_path)
    executor.return_value = object()

    summary = service.compile_target(target)

    assert summary.status is ValidationStatus.ERROR
    call = factory.calls[0]
    assert call[0:2] == ("from_exception", "source")
    assert isinstance(call[2], TypeError)
    assert "ProcessResult" in str(call[2])


def test_request_target_identity_mismatch_is_converted_to_error(tmp_path: Path) -> None:
    target = _target("source")
    different = _target("different")
    service, _, builder, executor, factory = _service(tmp_path)
    builder.target_override = different

    summary = service.compile_target(target)

    assert summary.status is ValidationStatus.ERROR
    assert executor.calls == []
    call = factory.calls[0]
    assert call[0:2] == ("from_exception", "source")
    assert isinstance(call[2], ValueError)
    assert "identity" in str(call[2])


def test_summary_target_identity_mismatch_is_rejected(tmp_path: Path) -> None:
    target = _target("source")
    service, _, _, _, factory = _service(tmp_path)
    factory.target_id_override = "different"

    with pytest.raises(ValueError, match="summary target_id"):
        service.compile_target(target)


def test_skipped_factory_must_return_skipped_status(tmp_path: Path) -> None:
    target = _target("source")
    service, _, _, _, factory = _service(tmp_path)
    factory.skipped_status = ValidationStatus.OK

    with pytest.raises(ValueError, match="must return ValidationStatus.SKIPPED"):
        service.execute_plan(_plan(target), no_compile=True)


@pytest.mark.parametrize(
    ("method_name", "kind"),
    [
        ("compile_source", CompileTargetKind.SOURCE),
        ("compile_checkpoint", CompileTargetKind.CHECKPOINT),
        ("compile_entrypoint", CompileTargetKind.ENTRYPOINT),
        ("build_release_pgf", CompileTargetKind.PGF),
    ],
)
def test_specialized_operations_accept_only_their_target_kind(
    tmp_path: Path,
    method_name: str,
    kind: CompileTargetKind,
) -> None:
    service, _, _, _, _ = _service(tmp_path)
    target = _target("subject", kind=kind)

    summary = getattr(service, method_name)(target)

    assert summary.status is ValidationStatus.OK
    wrong_kind = (
        CompileTargetKind.CHECKPOINT
        if kind is CompileTargetKind.SOURCE
        else CompileTargetKind.SOURCE
    )
    with pytest.raises(ValueError, match="target kind"):
        getattr(service, method_name)(_target("wrong", kind=wrong_kind))


def test_duplicate_target_ids_are_rejected_before_preflight(tmp_path: Path) -> None:
    first = _target("duplicate", order=0)
    second = _target("duplicate", order=1)
    service, validator, _, _, _ = _service(tmp_path)

    with pytest.raises(ValueError, match="duplicate compile target ID"):
        service.execute_plan(_plan(first, second))

    assert validator.calls == []


def test_targets_must_preserve_declared_order(tmp_path: Path) -> None:
    first = _target("first", order=2)
    second = _target("second", order=1)
    service, validator, _, _, _ = _service(tmp_path)

    with pytest.raises(ValueError, match="declared order"):
        service.execute_plan(_plan(first, second))

    assert validator.calls == []


def test_invalid_boolean_and_cancellation_token_inputs_are_rejected(
    tmp_path: Path,
) -> None:
    target = _target("source")
    service, _, _, _, _ = _service(tmp_path)

    with pytest.raises(TypeError, match="no_compile"):
        service.execute_plan(_plan(target), no_compile=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="clean_build"):
        service.compile_target(target, clean_build=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="is_cancelled"):
        service.compile_target(target, cancellation_token=object())  # type: ignore[arg-type]


def test_observer_must_expose_every_emitted_callback(tmp_path: Path) -> None:
    class IncompleteObserver:
        def plan_started(self, plan: CompilePlan) -> None:
            del plan

    validator = _PreflightValidator()
    builder = _RequestBuilder(tmp_path)
    executor = _Executor(_process_result(tmp_path))
    factory = _SummaryFactory()
    service = CompilationService(
        validator,
        builder,
        executor,
        factory,
        IncompleteObserver(),  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="preflight_completed"):
        service.execute_plan(_plan(_target("source")))
