from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any, Final, cast

import pytest

from gf_wordbench.infrastructure import process as process_api
from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
    CancellationReason,
    ProcessErrorKind,
    ProcessEvent,
    ProcessInput,
    ProcessInputKind,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.infrastructure.process.requests import (
    render_command_for_display,
    validate_process_request,
)
from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError
from gf_wordbench.kernel.statuses import ExecutionState

pytestmark = pytest.mark.contract

_PROCESS_PACKAGE: Final[Path] = (
    Path(__file__).resolve().parents[2] / "src" / "gf_wordbench" / "infrastructure" / "process"
)


def _request(tmp_path: Path, **changes: object) -> ProcessRequest:
    root = tmp_path.resolve()
    stdin_path = root / "scenario.gfs"
    stdin_path.write_text("-- controlled input\n", encoding="utf-8")

    request = ProcessRequest(
        request_id="request-001",
        tool_id="gf",
        operation_id="compile-001",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=Path(sys.executable).resolve(strict=True),
        args=("--make", "SecretModule", "argument with spaces", ";echo-not-a-shell"),
        cwd=root,
        stdout_path=root / "captures" / "stdout.bin",
        stderr_path=root / "captures" / "stderr.bin",
        timeout_sec=30.0,
        approved_read_roots=(root,),
        approved_write_roots=(root,),
        evidence_policy="raw-bytes-v1",
        stdin=ProcessInput.from_file(stdin_path),
        environment_policy="controlled-inherit-v1",
        env_overrides={"GF_TEST_MODE": "1", "GF_TEST_TOKEN": "secret-value"},
        env_removals=frozenset({"GF_REMOVE_ME"}),
        sensitive_env_keys=frozenset({"GF_TEST_TOKEN"}),
        sensitive_arg_indexes=frozenset({1}),
        termination_grace_sec=2.0,
        output_limit_bytes=1024 * 1024,
        expected_artifacts=(
            ArtifactExpectation(
                path=root / "artifacts" / "Grammar.pgf",
                role="pgf",
                required=True,
                kind=ArtifactKind.FILE,
                minimum_size_bytes=1,
            ),
        ),
        metadata={"project_id": "example", "entrypoint": "Grammar"},
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )
    return cast(ProcessRequest, cast(Any, replace)(request, **changes))


def _result(
    tmp_path: Path,
    *,
    state: ExecutionState,
    exit_code: int | None,
    pid: int | None,
    cancellation_reason: CancellationReason | None = None,
    launch_error_kind: ProcessErrorKind | None = None,
    launch_error_message: str = "",
    termination_attempted: bool = False,
    termination_succeeded: bool = False,
    output_limit_exceeded: bool = False,
) -> ProcessResult:
    started = datetime(2026, 7, 25, 14, 0, tzinfo=UTC)
    return ProcessResult(
        operation_id="compile-001",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=Path(sys.executable),
        args=("--make", "Grammar"),
        cwd=tmp_path,
        execution_state=state,
        exit_code=exit_code,
        pid=pid,
        started_at=started,
        finished_at=started + timedelta(milliseconds=250),
        duration_ms=250,
        cancellation_reason=cancellation_reason,
        launch_error_kind=launch_error_kind,
        launch_error_message=launch_error_message,
        termination_attempted=termination_attempted,
        termination_succeeded=termination_succeeded,
        stdout_path=tmp_path / "stdout.bin",
        stderr_path=tmp_path / "stderr.bin",
        stdout_size_bytes=7,
        stderr_size_bytes=5,
        output_limit_exceeded=output_limit_exceeded,
        capture_complete=True,
        environment_policy="controlled-inherit-v1",
        recorded_env_overrides={"GF_TEST_TOKEN": "<redacted>"},
        artifact_observations=(
            ArtifactObservation(
                path=tmp_path / "Grammar.pgf",
                role="pgf",
                required=True,
                exists=False,
                kind_matches=False,
                size_bytes=None,
            ),
        ),
    )


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _qualified_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return None


def test_locked_process_vocabularies_are_exact() -> None:
    assert tuple(ProcessOperationKind) == (
        ProcessOperationKind.VERSION_PROBE,
        ProcessOperationKind.COMPILE,
        ProcessOperationKind.PGF_BUILD,
        ProcessOperationKind.SCENARIO,
        ProcessOperationKind.GENERATION,
        ProcessOperationKind.INTROSPECTION,
        ProcessOperationKind.OPTIONAL_TOOL,
    )
    assert {value.value for value in ProcessInputKind} == {"none", "text", "file"}
    assert {value.value for value in ArtifactKind} == {"file", "directory"}
    assert {value.value for value in CancellationReason} == {
        "user",
        "application_shutdown",
        "output_limit",
        "controller_policy",
    }
    assert {value.value for value in ProcessErrorKind} == {
        "OK",
        "LAUNCH",
        "TIMEOUT",
        "CANCELLED",
        "OUTPUT_LIMIT",
        "IO",
        "ENCODING",
        "CONTAINMENT",
        "CONTRACT",
        "OTHER",
    }
    assert {value.value for value in ExecutionState} == {
        "completed",
        "timed_out",
        "cancelled",
        "launch_failed",
    }


def test_public_process_boundary_reexports_owner_types_without_redefinition() -> None:
    assert process_api.ProcessInput is ProcessInput
    assert process_api.ArtifactExpectation is ArtifactExpectation
    assert process_api.ArtifactObservation is ArtifactObservation
    assert process_api.ProcessRequest is ProcessRequest
    assert process_api.ProcessResult is ProcessResult
    assert process_api.validate_process_request is validate_process_request
    assert process_api.render_command_for_display is render_command_for_display

    for owned_type in (
        ProcessInput,
        ArtifactExpectation,
        ArtifactObservation,
        ProcessRequest,
        ProcessEvent,
        ProcessResult,
    ):
        assert owned_type.__module__ == "gf_wordbench.infrastructure.process.models"


def test_process_models_do_not_own_validation_or_diagnostic_interpretation() -> None:
    forbidden = {
        "validation_status",
        "overall_status",
        "diagnostic_class",
        "error_kind",
        "top_errors",
        "normalized_output",
    }
    assert forbidden.isdisjoint(field.name for field in fields(ProcessRequest))
    assert forbidden.isdisjoint(field.name for field in fields(ProcessResult))


def test_process_input_modes_are_explicit_and_mutually_exclusive(tmp_path: Path) -> None:
    source = tmp_path / "input.gfs"
    source.write_text("q\n", encoding="utf-8")

    assert ProcessInput.none() == ProcessInput()
    assert ProcessInput.from_text("q\n").kind is ProcessInputKind.TEXT
    assert ProcessInput.from_file(source).path == source

    with pytest.raises(ValueError, match="none input"):
        ProcessInput(kind=ProcessInputKind.NONE, text="unexpected")
    with pytest.raises(ValueError, match="text input"):
        ProcessInput(kind=ProcessInputKind.TEXT, text="x", path=source)
    with pytest.raises(ValueError, match="file input"):
        ProcessInput(kind=ProcessInputKind.FILE)


def test_artifact_facts_preserve_missing_and_present_states(tmp_path: Path) -> None:
    expectation = ArtifactExpectation(
        path=tmp_path / "Grammar.pgf",
        role="pgf",
        required=True,
        kind=ArtifactKind.FILE,
        minimum_size_bytes=1,
    )
    assert expectation.required is True
    assert expectation.minimum_size_bytes == 1

    missing = ArtifactObservation(
        path=expectation.path,
        role=expectation.role,
        required=True,
        exists=False,
        kind_matches=False,
        size_bytes=None,
    )
    assert missing.exists is False

    with pytest.raises(ValueError, match="missing artifact"):
        ArtifactObservation(
            path=expectation.path,
            role=expectation.role,
            required=True,
            exists=False,
            kind_matches=True,
            size_bytes=1,
        )


def test_process_request_is_immutable_and_defensively_copies_inputs(tmp_path: Path) -> None:
    overrides = {"GF_TEST": "before"}
    metadata = {"project_id": "one"}
    request = _request(tmp_path, env_overrides=overrides, metadata=metadata)

    overrides["GF_TEST"] = "after"
    metadata["project_id"] = "two"

    assert request.env_overrides["GF_TEST"] == "before"
    assert request.metadata["project_id"] == "one"
    assert request.command == (str(request.executable), *request.args)
    assert request.working_directory == request.cwd
    assert isinstance(request.args, tuple)
    assert isinstance(request.env_removals, frozenset)
    assert isinstance(request.sensitive_arg_indexes, frozenset)

    with pytest.raises(TypeError):
        request.env_overrides["GF_TEST"] = "mutated"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        request.timeout_sec = 1.0  # type: ignore[misc]


def test_canonical_request_passes_contract_validation(tmp_path: Path) -> None:
    validate_process_request(_request(tmp_path))


@pytest.mark.parametrize(
    ("change", "error_type", "message"),
    (
        (
            {"stdout_path": Path("relative.out")},
            ContractViolationError,
            "absolute path",
        ),
        (
            {"sensitive_arg_indexes": frozenset({99})},
            ContractViolationError,
            "outside the argument vector",
        ),
        (
            {
                "env_overrides": {"GF_CONFLICT": "1"},
                "env_removals": frozenset({"GF_CONFLICT"}),
            },
            ContractViolationError,
            "both overridden and removed",
        ),
    ),
)
def test_request_validation_rejects_contract_violations(
    tmp_path: Path,
    change: dict[str, object],
    error_type: type[Exception],
    message: str,
) -> None:
    request = _request(tmp_path, **change)
    with pytest.raises(error_type, match=message):
        validate_process_request(request)


def test_request_validation_rejects_path_escape_and_capture_reuse(tmp_path: Path) -> None:
    request = _request(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside" / "stdout.bin"

    with pytest.raises(PathSecurityError, match="escapes approved roots"):
        validate_process_request(replace(request, stdout_path=outside))

    with pytest.raises(ValueError, match="must be distinct"):
        replace(request, stderr_path=request.stdout_path)

    request.stdout_path.parent.mkdir(parents=True)
    request.stdout_path.write_bytes(b"already reserved")
    with pytest.raises(ContractViolationError, match="already exists"):
        validate_process_request(request)


def test_request_validation_blocks_gold_writes_and_batch_launchers(tmp_path: Path) -> None:
    request = _request(tmp_path)
    gold_expectation = ArtifactExpectation(
        path=tmp_path / "expected.gold",
        role="gold",
        required=True,
        kind=ArtifactKind.FILE,
    )
    with pytest.raises(PathSecurityError, match=r"\.gold"):
        validate_process_request(replace(request, expected_artifacts=(gold_expectation,)))

    batch_file = tmp_path / "tool.bat"
    batch_file.write_text("@echo off\n", encoding="utf-8")
    with pytest.raises(ContractViolationError, match="Batch executable"):
        validate_process_request(replace(request, executable=batch_file))


def test_display_rendering_redacts_secrets_and_preserves_literal_arguments(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    rendered = render_command_for_display(
        request.executable,
        request.args,
        sensitive_arg_indexes=request.sensitive_arg_indexes,
    )

    assert "SecretModule" not in rendered
    assert "<redacted>" in rendered
    assert "argument with spaces" in rendered
    assert ";echo-not-a-shell" in rendered
    assert request.args[1] == "SecretModule"


def test_process_package_has_one_shell_free_launch_primitive() -> None:
    assert _PROCESS_PACKAGE.is_dir()
    popen_locations: list[tuple[str, int]] = []
    prohibited_calls: list[tuple[str, int, str]] = []

    prohibited = {
        "os.system",
        "os.popen",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.getoutput",
        "subprocess.getstatusoutput",
        "subprocess.run",
        "asyncio.create_subprocess_shell",
    }

    for source_path in sorted(_PROCESS_PACKAGE.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _qualified_name(node.func)
            if name == "subprocess.Popen":
                popen_locations.append((source_path.name, node.lineno))
                shell = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "shell"),
                    None,
                )
                assert isinstance(shell, ast.Constant)
                assert shell.value is False
            elif name in prohibited:
                prohibited_calls.append((source_path.name, node.lineno, name))

    assert popen_locations
    assert {filename for filename, _ in popen_locations} == {"launcher.py"}
    assert prohibited_calls == []


def test_completed_timeout_cancellation_and_launch_failure_remain_distinct(
    tmp_path: Path,
) -> None:
    completed = _result(
        tmp_path,
        state=ExecutionState.COMPLETED,
        exit_code=7,
        pid=123,
    )
    timed_out = _result(
        tmp_path,
        state=ExecutionState.TIMED_OUT,
        exit_code=None,
        pid=124,
        termination_attempted=True,
        termination_succeeded=True,
    )
    cancelled = _result(
        tmp_path,
        state=ExecutionState.CANCELLED,
        exit_code=None,
        pid=None,
        cancellation_reason=CancellationReason.USER,
    )
    output_limited = _result(
        tmp_path,
        state=ExecutionState.CANCELLED,
        exit_code=None,
        pid=125,
        cancellation_reason=CancellationReason.OUTPUT_LIMIT,
        termination_attempted=True,
        termination_succeeded=True,
        output_limit_exceeded=True,
    )
    launch_failed = _result(
        tmp_path,
        state=ExecutionState.LAUNCH_FAILED,
        exit_code=None,
        pid=None,
        launch_error_kind=ProcessErrorKind.LAUNCH,
        launch_error_message="executable not found",
    )

    assert completed.exit_code == 7
    assert completed.timed_out is False
    assert timed_out.timed_out is True
    assert timed_out.exit_code is None
    assert cancelled.cancelled is True
    assert output_limited.output_limit_exceeded is True
    assert launch_failed.launch_error == "executable not found"
    assert launch_failed.exit_code is None
    assert completed.total_output_size_bytes == 12


def test_result_terminal_state_invariants_reject_collapsed_states(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="completed requires"):
        _result(
            tmp_path,
            state=ExecutionState.COMPLETED,
            exit_code=None,
            pid=123,
        )
    with pytest.raises(ValueError, match="timed_out requires"):
        _result(
            tmp_path,
            state=ExecutionState.TIMED_OUT,
            exit_code=None,
            pid=123,
        )
    with pytest.raises(ValueError, match="cancelled requires"):
        _result(
            tmp_path,
            state=ExecutionState.CANCELLED,
            exit_code=None,
            pid=None,
        )
    with pytest.raises(ValueError, match="launch_failed requires"):
        _result(
            tmp_path,
            state=ExecutionState.LAUNCH_FAILED,
            exit_code=None,
            pid=None,
            launch_error_kind=ProcessErrorKind.LAUNCH,
        )
    with pytest.raises(ValueError, match="must agree"):
        _result(
            tmp_path,
            state=ExecutionState.CANCELLED,
            exit_code=None,
            pid=123,
            cancellation_reason=CancellationReason.USER,
            termination_attempted=True,
            output_limit_exceeded=True,
        )


def test_results_and_events_normalize_timestamps_and_freeze_evidence(
    tmp_path: Path,
) -> None:
    offset = timezone(timedelta(hours=-4))
    started = datetime(2026, 7, 25, 10, 0, tzinfo=offset)
    result = replace(
        _result(
            tmp_path,
            state=ExecutionState.COMPLETED,
            exit_code=0,
            pid=321,
        ),
        started_at=started,
        finished_at=started + timedelta(seconds=1),
    )
    event_details = {"phase": "launched"}
    event = ProcessEvent(
        name="process_started",
        operation_id="compile-001",
        operation_kind=ProcessOperationKind.COMPILE,
        occurred_at=started,
        pid=321,
        details=event_details,
    )
    event_details["phase"] = "mutated"

    assert result.started_at.tzinfo is UTC
    assert result.finished_at.tzinfo is UTC
    assert event.occurred_at.tzinfo is UTC
    assert event.details["phase"] == "launched"
    assert result.recorded_env_overrides["GF_TEST_TOKEN"] == "<redacted>"

    with pytest.raises(TypeError):
        event.details["phase"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        result.recorded_env_overrides["GF_TEST_TOKEN"] = "secret"  # type: ignore[index]
