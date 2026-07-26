"""Execution boundary for validated allowlisted diagnostic tools."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import Protocol, TypeAlias

from gf_wordbench.infrastructure.process import (
    ArtifactExpectation,
    CancellationToken,
    ProcessInput,
    ProcessRequest,
    ProcessResult,
    run_process,
)
from gf_wordbench.infrastructure.process.models import (
    ProcessEvent,
    ProcessOperationKind,
)
from gf_wordbench.kernel.errors import ContractViolationError

ProcessEventSink: TypeAlias = Callable[[ProcessEvent], None]
ProcessRunner: TypeAlias = Callable[..., ProcessResult]


class ValidatedDiagnosticToolRequest(Protocol):
    request_id: str
    tool_id: str
    catalog_version: str
    operation_id: str
    active_project_id: str
    run_id: str
    subject_ids: tuple[str, ...]
    executable: Path
    args: tuple[str, ...]
    working_directory: Path
    stdout_path: Path
    stderr_path: Path
    timeout_sec: float
    approved_read_roots: tuple[Path, ...]
    approved_write_roots: tuple[Path, ...]
    stdin: ProcessInput
    environment_policy: str
    env_overrides: Mapping[str, str]
    env_removals: Collection[str]
    sensitive_env_keys: Collection[str]
    sensitive_arg_indexes: Collection[int]
    termination_grace_sec: float
    output_limit_bytes: int
    expected_artifacts: tuple[ArtifactExpectation, ...]
    metadata: Mapping[str, str]
    mutability_class: str
    network_policy: str
    evidence_policy: str


def build_diagnostic_process_request(
    request: ValidatedDiagnosticToolRequest,
) -> ProcessRequest:
    _validate_identity(request)
    metadata = _execution_metadata(request)
    return ProcessRequest(
        request_id=request.request_id,
        tool_id=request.tool_id,
        operation_id=request.operation_id,
        operation_kind=ProcessOperationKind.OPTIONAL_TOOL,
        executable=Path(request.executable),
        args=tuple(request.args),
        cwd=Path(request.working_directory),
        stdout_path=Path(request.stdout_path),
        stderr_path=Path(request.stderr_path),
        timeout_sec=request.timeout_sec,
        approved_read_roots=tuple(Path(path) for path in request.approved_read_roots),
        approved_write_roots=tuple(Path(path) for path in request.approved_write_roots),
        evidence_policy=request.evidence_policy,
        stdin=request.stdin,
        environment_policy=request.environment_policy,
        env_overrides=dict(request.env_overrides),
        env_removals=frozenset(request.env_removals),
        sensitive_env_keys=frozenset(request.sensitive_env_keys),
        sensitive_arg_indexes=frozenset(request.sensitive_arg_indexes),
        termination_grace_sec=request.termination_grace_sec,
        output_limit_bytes=request.output_limit_bytes,
        expected_artifacts=tuple(request.expected_artifacts),
        metadata=metadata,
        mutability_class=request.mutability_class,
        network_policy=request.network_policy,
    )


def execute_diagnostic_tool(
    request: ValidatedDiagnosticToolRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
    process_runner: ProcessRunner = run_process,
) -> ProcessResult:
    if not callable(process_runner):
        raise TypeError("process_runner must be callable")

    process_request = build_diagnostic_process_request(request)
    result = process_runner(
        process_request,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
    )
    if not isinstance(result, ProcessResult):
        raise ContractViolationError(
            "The diagnostic-tool process runner returned an invalid result."
        )
    if result.operation_id != request.operation_id:
        raise ContractViolationError(
            "The diagnostic-tool process result does not match the requested operation."
        )
    if result.operation_kind is not ProcessOperationKind.OPTIONAL_TOOL:
        raise ContractViolationError(
            "The diagnostic-tool process result has the wrong operation kind."
        )
    return result


def _validate_identity(request: ValidatedDiagnosticToolRequest) -> None:
    for field_name in (
        "request_id",
        "tool_id",
        "catalog_version",
        "operation_id",
        "active_project_id",
        "run_id",
        "evidence_policy",
    ):
        _require_text(getattr(request, field_name), field_name)

    subject_ids = tuple(request.subject_ids)
    if len(subject_ids) != len(set(subject_ids)):
        raise ContractViolationError("subject_ids must not contain duplicates.")
    for index, subject_id in enumerate(subject_ids):
        _require_text(subject_id, f"subject_ids[{index}]")


def _execution_metadata(
    request: ValidatedDiagnosticToolRequest,
) -> Mapping[str, str]:
    metadata = dict(request.metadata)
    required = {
        "diagnostic_tool_id": request.tool_id,
        "diagnostic_catalog_version": request.catalog_version,
        "active_project_id": request.active_project_id,
        "run_id": request.run_id,
        "subject_count": str(len(request.subject_ids)),
    }
    if request.subject_ids:
        required["subject_ids"] = ",".join(request.subject_ids)

    for key, value in required.items():
        existing = metadata.get(key)
        if existing is not None and existing != value:
            raise ContractViolationError(
                f"metadata field {key!r} conflicts with the validated request."
            )
        metadata[key] = value

    for key, value in metadata.items():
        _require_text(key, "metadata key")
        if not isinstance(value, str) or "\x00" in value:
            raise ContractViolationError(
                f"metadata value for {key!r} must be a NUL-free string."
            )
    return metadata


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip() or "\x00" in value:
        raise ContractViolationError(
            f"{field_name} must be non-empty and contain no NUL characters."
        )
    return value


__all__ = (
    "ProcessEventSink",
    "ProcessRunner",
    "ValidatedDiagnosticToolRequest",
    "build_diagnostic_process_request",
    "execute_diagnostic_tool",
)
