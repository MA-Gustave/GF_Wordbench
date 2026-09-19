from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest

from gf_wordbench.diagnostics.tools.executor import (
    build_diagnostic_process_request,
    execute_diagnostic_tool,
)
from gf_wordbench.infrastructure.process import (
    ArtifactExpectation,
    CancellationToken,
    ProcessInput,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.infrastructure.process.models import ProcessEvent, ProcessOperationKind
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import ExecutionState


@dataclass(frozen=True, slots=True)
class _ValidatedRequest:
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


@dataclass(frozen=True, slots=True)
class _CancellationToken:
    cancelled: bool = False

    def is_cancelled(self) -> bool:
        return self.cancelled

    def reason(self) -> str | None:
        return "unit-test" if self.cancelled else None


def _request(tmp_path: Path, **overrides: Any) -> _ValidatedRequest:
    run_root = (tmp_path / "run").resolve()
    project_root = (tmp_path / "project").resolve()
    values: dict[str, Any] = {
        "request_id": "request-1",
        "tool_id": "gf-diagnostic-helper",
        "catalog_version": "1.0",
        "operation_id": "operation-1",
        "active_project_id": "example-project",
        "run_id": "20260725T120000Z-example-project-diagnostic-0001",
        "subject_ids": ("Syntax.gf", "Morphology.gf"),
        "executable": (tmp_path / "bin" / "diagnostic-helper").resolve(),
        "args": ("--format", "json"),
        "working_directory": project_root,
        "stdout_path": run_root / "raw" / "tool.stdout.log",
        "stderr_path": run_root / "raw" / "tool.stderr.log",
        "timeout_sec": 30.0,
        "approved_read_roots": (project_root,),
        "approved_write_roots": (run_root,),
        "stdin": ProcessInput.none(),
        "environment_policy": "controlled-inherit-v1",
        "env_overrides": {"GF_TOOL_PROFILE": "diagnostic"},
        "env_removals": frozenset({"PYTHONINSPECT"}),
        "sensitive_env_keys": frozenset({"GF_TOOL_TOKEN"}),
        "sensitive_arg_indexes": frozenset({1}),
        "termination_grace_sec": 2.0,
        "output_limit_bytes": 1024 * 1024,
        "expected_artifacts": (),
        "metadata": {"origin": "unit-test"},
        "mutability_class": "read_only",
        "network_policy": "denied",
        "evidence_policy": "expanded",
    }
    values.update(overrides)
    return _ValidatedRequest(**values)


def _result(
    request: _ValidatedRequest,
    **overrides: Any,
) -> ProcessResult:
    timestamp = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    values: dict[str, Any] = {
        "operation_id": request.operation_id,
        "operation_kind": ProcessOperationKind.OPTIONAL_TOOL,
        "executable": request.executable,
        "args": request.args,
        "cwd": request.working_directory,
        "execution_state": ExecutionState.COMPLETED,
        "exit_code": 0,
        "pid": 4242,
        "started_at": timestamp,
        "finished_at": timestamp,
        "duration_ms": 0,
        "cancellation_reason": None,
        "launch_error_kind": None,
        "launch_error_message": "",
        "termination_attempted": False,
        "termination_succeeded": False,
        "stdout_path": request.stdout_path,
        "stderr_path": request.stderr_path,
        "stdout_size_bytes": 0,
        "stderr_size_bytes": 0,
        "output_limit_exceeded": False,
        "capture_complete": True,
        "environment_policy": request.environment_policy,
        "recorded_env_overrides": {},
        "artifact_observations": (),
    }
    values.update(overrides)
    return ProcessResult(**values)


def test_build_request_maps_the_validated_contract_without_shell_semantics(
    tmp_path: Path,
) -> None:
    source = _request(tmp_path)

    request = build_diagnostic_process_request(source)

    assert request.request_id == source.request_id
    assert request.tool_id == source.tool_id
    assert request.operation_id == source.operation_id
    assert request.operation_kind is ProcessOperationKind.OPTIONAL_TOOL
    assert request.executable == source.executable
    assert request.args == source.args
    assert request.command == (str(source.executable), *source.args)
    assert request.cwd == source.working_directory
    assert request.stdout_path == source.stdout_path
    assert request.stderr_path == source.stderr_path
    assert request.timeout_sec == source.timeout_sec
    assert request.approved_read_roots == source.approved_read_roots
    assert request.approved_write_roots == source.approved_write_roots
    assert request.stdin is source.stdin
    assert request.environment_policy == source.environment_policy
    assert dict(request.env_overrides) == source.env_overrides
    assert request.env_removals == source.env_removals
    assert request.sensitive_env_keys == source.sensitive_env_keys
    assert request.sensitive_arg_indexes == source.sensitive_arg_indexes
    assert request.termination_grace_sec == source.termination_grace_sec
    assert request.output_limit_bytes == source.output_limit_bytes
    assert request.mutability_class == "read_only"
    assert request.network_policy == "denied"
    assert request.evidence_policy == "expanded"


def test_build_request_adds_owned_traceability_metadata_and_freezes_it(
    tmp_path: Path,
) -> None:
    source = _request(tmp_path)

    request = build_diagnostic_process_request(source)

    assert dict(request.metadata) == {
        "origin": "unit-test",
        "diagnostic_tool_id": source.tool_id,
        "diagnostic_catalog_version": source.catalog_version,
        "active_project_id": source.active_project_id,
        "run_id": source.run_id,
        "subject_count": "2",
        "subject_ids": "Syntax.gf,Morphology.gf",
    }
    assert isinstance(request.metadata, MappingProxyType)

    cast(dict[str, str], source.metadata)["origin"] = "changed"
    cast(dict[str, str], source.env_overrides)["GF_TOOL_PROFILE"] = "changed"

    assert request.metadata["origin"] == "unit-test"
    assert request.env_overrides["GF_TOOL_PROFILE"] == "diagnostic"


def test_build_request_omits_subject_list_when_no_subjects_are_selected(
    tmp_path: Path,
) -> None:
    request = build_diagnostic_process_request(_request(tmp_path, subject_ids=()))

    assert request.metadata["subject_count"] == "0"
    assert "subject_ids" not in request.metadata


@pytest.mark.parametrize(
    ("field_name", "value", "exception_type"),
    [
        ("request_id", "", ContractViolationError),
        ("tool_id", "   ", ContractViolationError),
        ("catalog_version", "1.0\x00bad", ContractViolationError),
        ("operation_id", 7, TypeError),
        ("active_project_id", "", ContractViolationError),
        ("run_id", "", ContractViolationError),
        ("evidence_policy", "", ContractViolationError),
    ],
)
def test_build_request_rejects_invalid_identity_fields(
    tmp_path: Path,
    field_name: str,
    value: object,
    exception_type: type[Exception],
) -> None:
    with pytest.raises(exception_type):
        build_diagnostic_process_request(_request(tmp_path, **{field_name: value}))


def test_build_request_rejects_duplicate_or_invalid_subject_ids(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ContractViolationError,
        match="subject_ids must not contain duplicates",
    ):
        build_diagnostic_process_request(_request(tmp_path, subject_ids=("Syntax.gf", "Syntax.gf")))

    with pytest.raises(
        ContractViolationError,
        match=r"subject_ids\[1\]",
    ):
        build_diagnostic_process_request(_request(tmp_path, subject_ids=("Syntax.gf", "")))


def test_build_request_rejects_conflicting_owned_metadata(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ContractViolationError,
        match="diagnostic_tool_id.*conflicts",
    ):
        build_diagnostic_process_request(
            _request(
                tmp_path,
                metadata={"diagnostic_tool_id": "another-tool"},
            )
        )


def test_build_request_accepts_matching_owned_metadata(
    tmp_path: Path,
) -> None:
    source = _request(
        tmp_path,
        metadata={
            "diagnostic_tool_id": "gf-diagnostic-helper",
            "diagnostic_catalog_version": "1.0",
            "active_project_id": "example-project",
            "run_id": "20260725T120000Z-example-project-diagnostic-0001",
            "subject_count": "2",
            "subject_ids": "Syntax.gf,Morphology.gf",
        },
    )

    request = build_diagnostic_process_request(source)

    assert request.metadata["diagnostic_tool_id"] == source.tool_id
    assert request.metadata["subject_count"] == "2"


def test_execute_forwards_only_the_generic_process_boundary(
    tmp_path: Path,
) -> None:
    source = _request(tmp_path)
    cancellation_token: CancellationToken = _CancellationToken()
    events: list[ProcessEvent] = []

    def event_sink(event: ProcessEvent) -> None:
        events.append(event)
    captured: dict[str, object] = {}
    expected = _result(source)

    def runner(
        process_request: ProcessRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: Callable[[ProcessEvent], None] | None = None,
    ) -> ProcessResult:
        captured["request"] = process_request
        captured["cancellation_token"] = cancellation_token
        captured["event_sink"] = event_sink
        return expected

    result = execute_diagnostic_tool(
        source,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
        process_runner=runner,
    )

    assert result is expected
    process_request = captured["request"]
    assert isinstance(process_request, ProcessRequest)
    assert process_request.operation_kind is ProcessOperationKind.OPTIONAL_TOOL
    assert process_request.tool_id == source.tool_id
    assert captured["cancellation_token"] is cancellation_token
    assert captured["event_sink"] is event_sink


def test_execute_requires_a_callable_runner(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="process_runner must be callable"):
        execute_diagnostic_tool(
            _request(tmp_path),
            process_runner=None,  # type: ignore[arg-type]
        )


def test_execute_rejects_non_process_result(tmp_path: Path) -> None:
    with pytest.raises(
        ContractViolationError,
        match="returned an invalid result",
    ):
        def invalid_runner(*args: object, **kwargs: object) -> ProcessResult:
            del args, kwargs
            return cast(ProcessResult, object())

        execute_diagnostic_tool(
            _request(tmp_path),
            process_runner=invalid_runner,
        )


def test_execute_rejects_result_for_another_operation(tmp_path: Path) -> None:
    source = _request(tmp_path)
    wrong_result = replace(
        _result(source),
        operation_id="another-operation",
    )

    with pytest.raises(
        ContractViolationError,
        match="does not match the requested operation",
    ):
        execute_diagnostic_tool(
            source,
            process_runner=lambda *args, **kwargs: wrong_result,
        )


def test_execute_rejects_result_with_non_tool_operation_kind(
    tmp_path: Path,
) -> None:
    source = _request(tmp_path)
    wrong_result = replace(
        _result(source),
        operation_kind=ProcessOperationKind.COMPILE,
    )

    with pytest.raises(
        ContractViolationError,
        match="wrong operation kind",
    ):
        execute_diagnostic_tool(
            source,
            process_runner=lambda *args, **kwargs: wrong_result,
        )
