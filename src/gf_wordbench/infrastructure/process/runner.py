"""Coordinate one bounded, shell-free external process execution."""

from __future__ import annotations

import logging
import os
import stat
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Final, Literal, cast

from ...kernel.statuses import ExecutionState
from ..environment import PreparedEnvironment, build_child_environment
from .launcher import ProcessHandle, StandardInput, launch_without_shell
from .models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
    CancellationReason,
    ProcessErrorKind,
    ProcessEvent,
    ProcessEventSink,
    ProcessInput,
    ProcessInputKind,
    ProcessRequest,
    ProcessResult,
)
from .requests import render_command_for_display, validate_process_request
from .streams import CaptureSession, open_capture_session
from .termination import (
    CancellationToken,
    ContainmentKind,
    ProcessContainment,
    TerminationOutcome,
    terminate_owned_processes,
)

__all__ = ("run_process",)

_LOGGER = logging.getLogger(__name__)

_POLL_INTERVAL_SEC: Final[float] = 0.05
_MAX_ERROR_MESSAGE_CHARS: Final[int] = 1_000

_TerminalCause = Literal[
    "completed",
    "timed_out",
    "cancelled",
    "output_limit",
]


@dataclass(slots=True)
class _ExecutionFacts:
    """Mutable execution facts assembled before result construction."""

    execution_state: ExecutionState
    exit_code: int | None = None
    pid: int | None = None
    cancellation_reason: CancellationReason | None = None
    launch_error_kind: ProcessErrorKind | None = None
    launch_error_message: str = ""
    soft_termination_attempted: bool = False
    forced_termination_attempted: bool = False
    termination_succeeded: bool = False
    process_tree_contained: bool = False
    termination_error: str | None = None
    output_limit_exceeded: bool = False

    @property
    def termination_attempted(self) -> bool:
        return (
            self.soft_termination_attempted
            or self.forced_termination_attempted
        )


def run_process(
    request: ProcessRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> ProcessResult:
    """Execute one validated request and preserve its raw process evidence.

    The runner owns generic process mechanics only. It does not interpret GF
    diagnostics, assign validation status, or determine stage success.
    """

    validate_process_request(request)

    environment = build_child_environment(
        policy=request.environment_policy,
        overrides=request.env_overrides,
        sensitive_keys=request.sensitive_env_keys,
    )

    _emit_event(event_sink, request, "request_validated")
    _log_start(request)

    with open_capture_session(
        stdout_path=request.stdout_path,
        stderr_path=request.stderr_path,
        output_limit_bytes=request.output_limit_bytes,
    ) as capture:
        _emit_event(event_sink, request, "capture_opened")

        started_at = _utc_now()
        started_clock = time.monotonic()

        if _is_cancelled(cancellation_token):
            facts = _ExecutionFacts(
                execution_state=ExecutionState.CANCELLED,
                cancellation_reason=_cancellation_reason(
                    cancellation_token
                ),
            )
        else:
            facts = _launch_and_monitor(
                request,
                capture,
                environment,
                started_clock=started_clock,
                cancellation_token=cancellation_token,
                event_sink=event_sink,
            )

        capture.flush()
        capture_result = capture.finalize()

    finished_at = _utc_now()
    duration_ms = _duration_ms(
        started_clock,
        time.monotonic(),
    )

    _reconcile_capture_limit(facts, capture_result.output_limit_exceeded)

    observations = tuple(
        _observe_artifact(expectation)
        for expectation in request.expected_artifacts
    )

    result = ProcessResult(
        operation_id=request.operation_id,
        operation_kind=request.operation_kind,
        executable=request.executable,
        args=request.args,
        cwd=request.cwd,
        execution_state=facts.execution_state,
        exit_code=facts.exit_code,
        pid=facts.pid,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        cancellation_reason=facts.cancellation_reason,
        launch_error_kind=facts.launch_error_kind,
        launch_error_message=facts.launch_error_message,
        termination_attempted=facts.termination_attempted,
        termination_succeeded=facts.termination_succeeded,
        stdout_path=request.stdout_path,
        stderr_path=request.stderr_path,
        stdout_size_bytes=capture_result.stdout.size_bytes,
        stderr_size_bytes=capture_result.stderr.size_bytes,
        output_limit_exceeded=facts.output_limit_exceeded,
        capture_complete=capture_result.capture_complete,
        environment_policy=environment.policy,
        recorded_env_overrides=environment.recorded_overrides,
        artifact_observations=observations,
    )

    _emit_event(
        event_sink,
        request,
        "capture_finalized",
        pid=facts.pid,
        execution_state=facts.execution_state,
        details={
            "stdout_size_bytes": capture_result.stdout.size_bytes,
            "stderr_size_bytes": capture_result.stderr.size_bytes,
            "output_limit_exceeded": (
                capture_result.output_limit_exceeded
            ),
            "capture_complete": capture_result.capture_complete,
            "capture_failure_count": len(capture_result.failures),
        },
    )

    _log_finish(request, facts, duration_ms)
    return result


def _launch_and_monitor(
    request: ProcessRequest,
    capture: CaptureSession,
    environment: PreparedEnvironment,
    *,
    started_clock: float,
    cancellation_token: CancellationToken | None,
    event_sink: ProcessEventSink | None,
) -> _ExecutionFacts:
    with _open_standard_input(request.stdin) as stdin:
        try:
            process = launch_without_shell(
                executable=request.executable,
                args=request.args,
                cwd=request.cwd,
                env=environment.values,
                stdin=stdin,
                stdout=capture.stdout,
                stderr=capture.stderr,
            )
        except OSError as exc:
            kind, message = _classify_launch_error(exc)

            _LOGGER.warning(
                "process launch failed "
                "operation_id=%s kind=%s error=%s",
                request.operation_id,
                kind.value,
                message,
            )

            return _ExecutionFacts(
                execution_state=ExecutionState.LAUNCH_FAILED,
                launch_error_kind=kind,
                launch_error_message=message,
            )

        containment = _containment_for(process)

        _emit_event(
            event_sink,
            request,
            "process_started",
            pid=process.pid,
            details={
                "containment_kind": containment.kind.value,
                "process_tree_contained": (
                    containment.process_tree_contained
                ),
            },
        )

        try:
            terminal_cause = _monitor_process(
                process,
                capture,
                timeout_sec=request.timeout_sec,
                started_clock=started_clock,
                cancellation_token=cancellation_token,
            )

            if terminal_cause == "completed":
                facts = _ExecutionFacts(
                    execution_state=ExecutionState.COMPLETED,
                    exit_code=process.wait(),
                    pid=process.pid,
                    process_tree_contained=(
                        containment.process_tree_contained
                    ),
                )
            else:
                facts = _terminate_for_cause(
                    request,
                    process,
                    containment,
                    terminal_cause,
                    cancellation_token=cancellation_token,
                    event_sink=event_sink,
                )

            capture.flush()

            _emit_event(
                event_sink,
                request,
                "process_exited",
                pid=process.pid,
                execution_state=facts.execution_state,
                details={
                    "exit_code": facts.exit_code,
                    "soft_termination_attempted": (
                        facts.soft_termination_attempted
                    ),
                    "forced_termination_attempted": (
                        facts.forced_termination_attempted
                    ),
                    "termination_succeeded": (
                        facts.termination_succeeded
                    ),
                    "process_tree_contained": (
                        facts.process_tree_contained
                    ),
                    "termination_error": facts.termination_error,
                },
            )

            return facts
        except BaseException:
            _contain_after_internal_failure(
                request,
                process,
                containment=containment,
            )
            raise


def _monitor_process(
    process: ProcessHandle,
    capture: CaptureSession,
    *,
    timeout_sec: float,
    started_clock: float,
    cancellation_token: CancellationToken | None,
) -> _TerminalCause:
    deadline = started_clock + timeout_sec

    while True:
        if process.poll() is not None:
            return "completed"

        if _is_cancelled(cancellation_token):
            return "cancelled"

        if capture.output_limit_exceeded:
            return "output_limit"

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "timed_out"

        time.sleep(min(_POLL_INTERVAL_SEC, remaining))


def _terminate_for_cause(
    request: ProcessRequest,
    process: ProcessHandle,
    containment: ProcessContainment,
    cause: _TerminalCause,
    *,
    cancellation_token: CancellationToken | None,
    event_sink: ProcessEventSink | None,
) -> _ExecutionFacts:
    if cause == "timed_out":
        execution_state = ExecutionState.TIMED_OUT
        cancellation_reason = None
        output_limit_exceeded = False
    elif cause == "output_limit":
        execution_state = ExecutionState.CANCELLED
        cancellation_reason = CancellationReason.OUTPUT_LIMIT
        output_limit_exceeded = True
    else:
        execution_state = ExecutionState.CANCELLED
        cancellation_reason = _cancellation_reason(
            cancellation_token
        )
        output_limit_exceeded = False

    _emit_event(
        event_sink,
        request,
        "termination_requested",
        pid=process.pid,
        execution_state=execution_state,
        details={"cause": cause},
    )

    outcome = terminate_owned_processes(
        process,
        containment=containment,
        grace_sec=request.termination_grace_sec,
    )

    facts = _facts_from_termination(
        execution_state,
        cancellation_reason=cancellation_reason,
        output_limit_exceeded=output_limit_exceeded,
        pid=process.pid,
        exit_code=process.poll(),
        outcome=outcome,
    )

    _emit_event(
        event_sink,
        request,
        "termination_completed",
        pid=process.pid,
        execution_state=execution_state,
        details=_termination_details(outcome),
    )

    if outcome.termination_error is not None:
        _LOGGER.warning(
            "process termination reported errors "
            "operation_id=%s pid=%s error=%s",
            request.operation_id,
            process.pid,
            outcome.termination_error,
        )

    return facts


def _facts_from_termination(
    execution_state: ExecutionState,
    *,
    cancellation_reason: CancellationReason | None,
    output_limit_exceeded: bool,
    pid: int,
    exit_code: int | None,
    outcome: TerminationOutcome,
) -> _ExecutionFacts:
    return _ExecutionFacts(
        execution_state=execution_state,
        exit_code=exit_code,
        pid=pid,
        cancellation_reason=cancellation_reason,
        soft_termination_attempted=(
            outcome.soft_termination_attempted
        ),
        forced_termination_attempted=(
            outcome.forced_termination_attempted
        ),
        termination_succeeded=outcome.termination_succeeded,
        process_tree_contained=outcome.process_tree_contained,
        termination_error=outcome.termination_error,
        output_limit_exceeded=output_limit_exceeded,
    )


def _contain_after_internal_failure(
    request: ProcessRequest,
    process: ProcessHandle,
    *,
    containment: ProcessContainment,
) -> None:
    if process.poll() is not None:
        return

    try:
        outcome = terminate_owned_processes(
            process,
            containment=containment,
            grace_sec=request.termination_grace_sec,
        )
    except Exception:
        _LOGGER.exception(
            "process containment failed after internal error "
            "operation_id=%s pid=%s",
            request.operation_id,
            process.pid,
        )
        return

    if (
        not outcome.termination_succeeded
        or outcome.termination_error is not None
    ):
        _LOGGER.error(
            "process containment incomplete after internal error "
            "operation_id=%s pid=%s "
            "tree_contained=%s error=%s",
            request.operation_id,
            process.pid,
            outcome.process_tree_contained,
            outcome.termination_error,
        )


@contextmanager
def _open_standard_input(
    process_input: ProcessInput,
) -> Iterator[StandardInput]:
    if process_input.kind is ProcessInputKind.NONE:
        yield None
        return

    if process_input.kind is ProcessInputKind.TEXT:
        assert process_input.text is not None

        with tempfile.TemporaryFile(mode="w+b") as stream:
            stream.write(
                process_input.text.encode(process_input.encoding)
            )
            stream.seek(0)
            yield stream

        return

    assert process_input.path is not None

    with process_input.path.open("rb") as stream:
        yield stream


def _containment_for(
    process: ProcessHandle,
) -> ProcessContainment:
    if os.name == "posix":
        return ProcessContainment(
            kind=ContainmentKind.POSIX_PROCESS_GROUP,
            identifier=process.pid,
            process_tree_contained=True,
        )

    if os.name == "nt":
        return ProcessContainment(
            kind=ContainmentKind.WINDOWS_PROCESS_GROUP,
            identifier=process.pid,
            process_tree_contained=False,
        )

    return ProcessContainment(
        kind=ContainmentKind.ROOT_PROCESS,
        identifier=process.pid,
        process_tree_contained=False,
    )


def _classify_launch_error(
    error: OSError,
) -> tuple[ProcessErrorKind, str]:
    if isinstance(error, FileNotFoundError):
        message = "executable or launch dependency was not found"
    elif isinstance(error, PermissionError):
        message = (
            "permission was denied while launching the executable"
        )
    else:
        message = str(error).strip() or type(error).__name__

    message = message.replace(
        "\x00",
        "\N{REPLACEMENT CHARACTER}",
    ).strip()

    if len(message) > _MAX_ERROR_MESSAGE_CHARS:
        message = (
            message[: _MAX_ERROR_MESSAGE_CHARS - 1]
            + "…"
        )

    return ProcessErrorKind.LAUNCH, message


def _reconcile_capture_limit(
    facts: _ExecutionFacts,
    output_limit_exceeded: bool,
) -> None:
    if not output_limit_exceeded:
        return

    facts.output_limit_exceeded = True

    if facts.execution_state is ExecutionState.COMPLETED:
        facts.execution_state = ExecutionState.CANCELLED
        facts.cancellation_reason = (
            CancellationReason.OUTPUT_LIMIT
        )


def _observe_artifact(
    expectation: ArtifactExpectation,
) -> ArtifactObservation:
    try:
        metadata = expectation.path.stat()
    except OSError:
        exists = False
        kind_matches = False
        size_bytes = None
    else:
        exists = True

        if expectation.kind is ArtifactKind.FILE:
            kind_matches = stat.S_ISREG(metadata.st_mode)
            size_bytes = (
                metadata.st_size
                if kind_matches
                else None
            )
        else:
            kind_matches = stat.S_ISDIR(metadata.st_mode)
            size_bytes = None

    return ArtifactObservation(
        path=expectation.path,
        role=expectation.role,
        required=expectation.required,
        exists=exists,
        kind_matches=kind_matches,
        size_bytes=size_bytes,
    )


def _is_cancelled(
    token: CancellationToken | None,
) -> bool:
    return token is not None and token.is_cancelled()


def _cancellation_reason(
    token: CancellationToken | None,
) -> CancellationReason:
    reason = None if token is None else token.reason()

    if reason is None or not reason.strip():
        return CancellationReason.CONTROLLER_POLICY

    try:
        return CancellationReason(reason)
    except ValueError:
        _LOGGER.warning(
            "unknown cancellation reason %r; "
            "using controller_policy",
            reason,
        )
        return CancellationReason.CONTROLLER_POLICY


def _termination_details(
    outcome: TerminationOutcome,
) -> Mapping[str, object]:
    return {
        "soft_termination_attempted": (
            outcome.soft_termination_attempted
        ),
        "forced_termination_attempted": (
            outcome.forced_termination_attempted
        ),
        "termination_succeeded": (
            outcome.termination_succeeded
        ),
        "process_tree_contained": (
            outcome.process_tree_contained
        ),
        "termination_error": outcome.termination_error,
    }


def _emit_event(
    sink: ProcessEventSink | None,
    request: ProcessRequest,
    name: str,
    *,
    pid: int | None = None,
    execution_state: ExecutionState | None = None,
    details: Mapping[str, object] | None = None,
) -> None:
    if sink is None:
        return

    event = ProcessEvent(
        name=name,
        operation_id=request.operation_id,
        operation_kind=request.operation_kind,
        occurred_at=_utc_now(),
        pid=pid,
        execution_state=execution_state,
        details=MappingProxyType(dict(details or {})),
    )

    try:
        emitter = getattr(sink, "emit", None)

        if callable(emitter):
            emitter(event)
        else:
            cast(
                Callable[[ProcessEvent], None],
                sink,
            )(event)
    except Exception:
        _LOGGER.exception(
            "process event sink failed "
            "operation_id=%s event=%s",
            request.operation_id,
            name,
        )


def _log_start(request: ProcessRequest) -> None:
    command = render_command_for_display(
        request.executable,
        request.args,
        sensitive_arg_indexes=(
            request.sensitive_arg_indexes
        ),
    )

    _LOGGER.info(
        "starting process "
        "operation_id=%s operation_kind=%s "
        "cwd=%s command=%s",
        request.operation_id,
        request.operation_kind,
        request.cwd,
        command,
    )


def _log_finish(
    request: ProcessRequest,
    facts: _ExecutionFacts,
    duration_ms: int,
) -> None:
    _LOGGER.info(
        "finished process "
        "operation_id=%s state=%s exit_code=%s "
        "duration_ms=%d "
        "soft_termination_attempted=%s "
        "forced_termination_attempted=%s "
        "termination_succeeded=%s "
        "process_tree_contained=%s",
        request.operation_id,
        facts.execution_state.value,
        facts.exit_code,
        duration_ms,
        facts.soft_termination_attempted,
        facts.forced_termination_attempted,
        facts.termination_succeeded,
        facts.process_tree_contained,
    )


def _duration_ms(
    started_clock: float,
    finished_clock: float,
) -> int:
    return max(
        0,
        int((finished_clock - started_clock) * 1_000),
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)