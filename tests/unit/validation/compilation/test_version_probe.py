from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.infrastructure.process.models import (
    CancellationReason,
    ProcessErrorKind,
    ProcessInputKind,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.compilation.version_probe import (
    DEFAULT_VERSION_ARGUMENTS,
    DEFAULT_VERSION_OPERATION_ID,
    DEFAULT_VERSION_PROBE_OUTPUT_LIMIT_BYTES,
    DEFAULT_VERSION_PROBE_TIMEOUT_SEC,
    DEFAULT_VERSION_REQUEST_ID,
    UNKNOWN_VERSION_TEXT,
    GFVersion,
    GFVersionCompatibility,
    GFVersionCompatibilityResult,
    GFVersionPolicy,
    GFVersionProbeOutcome,
    build_gf_version_probe_request,
    evaluate_gf_version_compatibility,
    interpret_gf_version_probe,
    parse_gf_version_text,
    probe_gf_version,
    select_version_text,
    skipped_gf_version_result,
)


def _absolute(tmp_path: Path, name: str) -> Path:
    return (tmp_path / name).resolve()


def _process_result(
    tmp_path: Path,
    *,
    stdout: bytes = b"GF 3.12\n",
    stderr: bytes = b"",
    execution_state: ExecutionState = ExecutionState.COMPLETED,
    exit_code: int | None = 0,
    executable: Path | None = None,
    args: tuple[str, ...] = DEFAULT_VERSION_ARGUMENTS,
    cwd: Path | None = None,
    launch_error_message: str = "",
    duration_ms: int = 25,
) -> ProcessResult:
    stdout_path = _absolute(tmp_path, "version.stdout.txt")
    stderr_path = _absolute(tmp_path, "version.stderr.txt")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)

    started_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    launched = execution_state is not ExecutionState.LAUNCH_FAILED
    terminated = execution_state in {
        ExecutionState.TIMED_OUT,
        ExecutionState.CANCELLED,
    }
    cancellation_reason = (
        CancellationReason.USER if execution_state is ExecutionState.CANCELLED else None
    )
    launch_error_kind = (
        ProcessErrorKind.LAUNCH if execution_state is ExecutionState.LAUNCH_FAILED else None
    )

    return ProcessResult(
        operation_id=DEFAULT_VERSION_OPERATION_ID,
        operation_kind=ProcessOperationKind.VERSION_PROBE,
        executable=executable or _absolute(tmp_path, "gf"),
        args=args,
        cwd=cwd or tmp_path.resolve(),
        execution_state=execution_state,
        exit_code=exit_code if execution_state is ExecutionState.COMPLETED else None,
        pid=4312 if launched else None,
        started_at=started_at,
        finished_at=started_at + timedelta(milliseconds=duration_ms),
        duration_ms=duration_ms,
        cancellation_reason=cancellation_reason,
        launch_error_kind=launch_error_kind,
        launch_error_message=launch_error_message,
        termination_attempted=terminated,
        termination_succeeded=terminated,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_size_bytes=len(stdout),
        stderr_size_bytes=len(stderr),
        output_limit_exceeded=False,
        capture_complete=True,
        environment_policy="controlled-inherit-v1",
    )


def _tested_policy() -> GFVersionPolicy:
    return GFVersionPolicy(
        minimum_supported_version="3.10",
        project_minimum_version="3.11",
        tested_versions=("3.11", "3.12"),
        known_incompatible_versions=("3.10",),
        capabilities_by_version={
            "3.12": frozenset({"pgf-build", "unicode-paths"}),
        },
    )


@pytest.mark.parametrize(
    ("raw", "normalized", "components"),
    [
        ("3.12", "3.12", (3, 12)),
        ("v3.12.0", "3.12", (3, 12)),
        ("3.12.1.0", "3.12.1", (3, 12, 1)),
        ("3.12.1-beta.2", "3.12.1", (3, 12, 1)),
    ],
)
def test_gf_version_parse_normalizes_numeric_components(
    raw: str,
    normalized: str,
    components: tuple[int, ...],
) -> None:
    version = GFVersion.parse(raw)

    assert version.normalized == normalized
    assert version.components == components
    assert str(version) == normalized


@pytest.mark.parametrize(
    "value",
    ["", "3", "3.x", "GF 3.12", " 3.12", "3.12 ", "3.12.1.2.3"],
)
def test_gf_version_parse_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(ValueError):
        GFVersion.parse(value)


def test_gf_version_comparison_pads_components() -> None:
    assert GFVersion.parse("3.12") == GFVersion.parse("3.12.0")
    assert GFVersion.parse("3.12") < GFVersion.parse("3.12.1")
    assert GFVersion.parse("3.12.1") > GFVersion.parse("3.12")
    assert GFVersion.parse("4.0") >= GFVersion.parse("3.99.99")
    assert GFVersion.parse("3.12").comparison_key() == (3, 12, 0, 0)


def test_gf_version_policy_uses_highest_minimum_and_freezes_capabilities() -> None:
    source_capabilities = {"3.12.0": {"pgf-build", "unicode-paths"}}
    policy = GFVersionPolicy(
        minimum_supported_version="3.10",
        project_minimum_version="3.12",
        tested_versions=("3.12.0", "3.12"),
        capabilities_by_version=cast("dict[str, frozenset[str]]", source_capabilities),
    )
    source_capabilities["3.12.0"].add("mutated-later")

    assert policy.effective_minimum_version == GFVersion.parse("3.12")
    assert policy.tested_versions == (GFVersion.parse("3.12"),)
    assert policy.capabilities_for("3.12") == frozenset({"pgf-build", "unicode-paths"})

    with pytest.raises(TypeError):
        policy.capabilities_by_version["3.12"] = frozenset()  # type: ignore[index]


def test_gf_version_policy_rejects_tested_incompatible_overlap() -> None:
    with pytest.raises(ValueError, match="overlap: 3.12"):
        GFVersionPolicy(
            tested_versions=("3.12",),
            known_incompatible_versions=("3.12.0",),
        )


@pytest.mark.parametrize(
    ("value", "normalized"),
    [
        ("GF 3.12", "3.12"),
        ("GF version 3.12.1", "3.12.1"),
        ("Grammatical Framework: v3.11.0", "3.11"),
        ("build information: 3.12.2+local", "3.12.2"),
    ],
)
def test_parse_gf_version_text_recognizes_documented_formats(
    value: str,
    normalized: str,
) -> None:
    assert parse_gf_version_text(value) == GFVersion.parse(normalized)


def test_parse_gf_version_text_returns_none_without_dotted_version() -> None:
    assert parse_gf_version_text("Grammatical Framework development build") is None


def test_select_version_text_prefers_first_non_empty_stdout_line() -> None:
    selected = select_version_text(
        "\n  GF 3.12.1  \nignored\n",
        "GF 3.11\n",
    )

    assert selected.display_text == "GF 3.12.1"
    assert selected.parsed_version == GFVersion.parse("3.12.1")
    assert selected.source_stream == "stdout"
    assert selected.recognized is True


def test_select_version_text_falls_back_to_stderr() -> None:
    selected = select_version_text("\n", "GF 3.12\n")

    assert selected.source_stream == "stderr"
    assert selected.parsed_version == GFVersion.parse("3.12")


def test_select_version_text_returns_unknown_for_empty_streams() -> None:
    selected = select_version_text("\n", "\r\n")

    assert selected.display_text == UNKNOWN_VERSION_TEXT
    assert selected.parsed_version is None
    assert selected.source_stream is None
    assert selected.recognized is False


def test_compatibility_accepts_tested_version_and_exposes_capabilities() -> None:
    result = evaluate_gf_version_compatibility(
        GFVersion.parse("3.12"),
        _tested_policy(),
    )

    assert result.compatibility is GFVersionCompatibility.SUPPORTED
    assert result.accepted is True
    assert result.minimum_required == GFVersion.parse("3.11")
    assert result.capabilities == frozenset({"pgf-build", "unicode-paths"})
    assert result.warnings == ()


@pytest.mark.parametrize(
    ("version", "compatibility", "message_fragment"),
    [
        ("3.9", GFVersionCompatibility.UNSUPPORTED, "below the required minimum"),
        (
            "3.10",
            GFVersionCompatibility.KNOWN_INCOMPATIBLE,
            "explicitly known to be incompatible",
        ),
        ("3.13", GFVersionCompatibility.UNTESTED, "has not been verified"),
    ],
)
def test_compatibility_rejects_unaccepted_versions(
    version: str,
    compatibility: GFVersionCompatibility,
    message_fragment: str,
) -> None:
    result = evaluate_gf_version_compatibility(
        GFVersion.parse(version),
        _tested_policy(),
    )

    assert result.compatibility is compatibility
    assert result.accepted is False
    assert message_fragment in result.message


def test_compatibility_can_accept_untested_version_with_warning() -> None:
    policy = GFVersionPolicy(
        minimum_supported_version="3.10",
        tested_versions=("3.12",),
        allow_untested_versions=True,
    )

    result = evaluate_gf_version_compatibility(
        GFVersion.parse("3.13"),
        policy,
    )

    assert result.compatibility is GFVersionCompatibility.SUPPORTED_WITH_WARNING
    assert result.accepted is True
    assert result.warnings == (
        "GF 3.13 satisfies the minimum version policy but is not listed as tested.",
    )


def test_compatibility_rejects_unknown_version_under_strict_policy() -> None:
    result = evaluate_gf_version_compatibility(
        None,
        GFVersionPolicy(strict_unknown=True),
    )

    assert result.compatibility is GFVersionCompatibility.UNKNOWN
    assert result.accepted is False
    assert result.capabilities == frozenset()
    assert result.warnings == ("GF version output was not recognized.",)


def test_compatibility_result_rejects_accepted_unknown_state() -> None:
    with pytest.raises(ValueError, match="cannot be accepted"):
        GFVersionCompatibilityResult(
            compatibility=GFVersionCompatibility.UNKNOWN,
            accepted=True,
            minimum_required=None,
            capabilities=frozenset(),
            message="Unknown.",
        )


def test_build_probe_request_applies_read_only_process_contract(tmp_path: Path) -> None:
    executable = _absolute(tmp_path, "bin/gf")
    working_directory = _absolute(tmp_path, "project")
    stdout_path = _absolute(tmp_path, "logs/version.stdout.txt")
    stderr_path = _absolute(tmp_path, "logs/version.stderr.txt")
    extra_read_root = _absolute(tmp_path, "rgl")
    extra_write_root = _absolute(tmp_path, "evidence")

    request = build_gf_version_probe_request(
        executable=executable,
        working_directory=working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        approved_read_roots=(working_directory, extra_read_root),
        approved_write_roots=(stdout_path.parent, extra_write_root),
        env_overrides={"GF_LIB_PATH": str(extra_read_root)},
        env_removals=("PYTHONPATH",),
        sensitive_env_keys=("GF_TOKEN",),
    )

    assert request.request_id == DEFAULT_VERSION_REQUEST_ID
    assert request.tool_id == "gf"
    assert request.operation_id == DEFAULT_VERSION_OPERATION_ID
    assert request.operation_kind is ProcessOperationKind.VERSION_PROBE
    assert request.args == DEFAULT_VERSION_ARGUMENTS
    assert request.cwd == working_directory
    assert request.timeout_sec == DEFAULT_VERSION_PROBE_TIMEOUT_SEC
    assert request.output_limit_bytes == DEFAULT_VERSION_PROBE_OUTPUT_LIMIT_BYTES
    assert request.stdin.kind is ProcessInputKind.NONE
    assert request.evidence_policy == "full-raw-v1"
    assert request.mutability_class == "read_only"
    assert request.network_policy == "denied"
    assert request.approved_read_roots == (
        executable.parent,
        working_directory,
        extra_read_root,
    )
    assert request.approved_write_roots == (
        stdout_path.parent,
        extra_write_root,
    )
    assert dict(request.env_overrides) == {"GF_LIB_PATH": str(extra_read_root)}
    assert request.env_removals == frozenset({"PYTHONPATH"})
    assert request.sensitive_env_keys == frozenset({"GF_TOKEN"})
    assert dict(request.metadata) == {
        "probe_kind": "gf_version",
        "version_arguments": "--version",
    }


@pytest.mark.parametrize(
    ("changes", "error_type", "message"),
    [
        ({"timeout_sec": 0}, ValueError, "timeout_sec must be finite and positive"),
        ({"output_limit_bytes": 0}, ValueError, "output_limit_bytes must be positive"),
        ({"version_arguments": ()}, ValueError, "version_arguments must not be empty"),
        (
            {"version_arguments": "--version"},
            TypeError,
            "version_arguments must be a sequence",
        ),
    ],
)
def test_build_probe_request_rejects_invalid_policy_values(
    tmp_path: Path,
    changes: dict[str, Any],
    error_type: type[Exception],
    message: str,
) -> None:
    kwargs: dict[str, Any] = {
        "executable": _absolute(tmp_path, "gf"),
        "working_directory": tmp_path.resolve(),
        "stdout_path": _absolute(tmp_path, "stdout.txt"),
        "stderr_path": _absolute(tmp_path, "stderr.txt"),
    }
    kwargs.update(changes)

    with pytest.raises(error_type, match=message):
        build_gf_version_probe_request(**kwargs)


def test_build_probe_request_rejects_shared_capture_path(tmp_path: Path) -> None:
    output = _absolute(tmp_path, "version.txt")

    with pytest.raises(ValueError, match="must be distinct"):
        build_gf_version_probe_request(
            executable=_absolute(tmp_path, "gf"),
            working_directory=tmp_path.resolve(),
            stdout_path=output,
            stderr_path=output,
        )


def test_interpret_completed_probe_recognizes_tested_version(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"Grammatical Framework 3.12.0\n",
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.outcome is GFVersionProbeOutcome.RECOGNIZED
    assert result.normalized_version == "3.12"
    assert result.raw_version_text == "Grammatical Framework 3.12.0"
    assert result.recognized is True
    assert result.accepted is True
    assert result.compatibility.compatibility is GFVersionCompatibility.SUPPORTED
    assert result.stdout_path == process_result.stdout_path
    assert result.stderr_path == process_result.stderr_path
    assert result.process_result is process_result


def test_interpret_probe_uses_stderr_when_stdout_is_empty(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"\n",
        stderr=b"GF version 3.12\n",
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.version_text.source_stream == "stderr"
    assert result.normalized_version == "3.12"
    assert result.accepted is True


def test_interpret_nonzero_exit_code_never_accepts_version(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"GF 3.12\n",
        exit_code=2,
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.outcome is GFVersionProbeOutcome.UNKNOWN
    assert result.recognized is True
    assert result.accepted is False
    assert result.compatibility.compatibility is GFVersionCompatibility.UNKNOWN
    assert result.warnings == (
        "GF version probe completed with non-zero exit code 2.",
        "A non-zero version-probe exit code prevents compatibility acceptance.",
    )


def test_interpret_timed_out_probe_does_not_evaluate_compatibility(
    tmp_path: Path,
) -> None:
    process_result = _process_result(
        tmp_path,
        execution_state=ExecutionState.TIMED_OUT,
        exit_code=None,
        duration_ms=10_500,
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.outcome is GFVersionProbeOutcome.TIMED_OUT
    assert result.compatibility.compatibility is GFVersionCompatibility.NOT_EVALUATED
    assert result.accepted is False
    assert result.message == "GF version probe timed out after 10500 ms."


def test_interpret_launch_failure_preserves_sanitized_message(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"",
        execution_state=ExecutionState.LAUNCH_FAILED,
        exit_code=None,
        launch_error_message="Executable not found.",
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.outcome is GFVersionProbeOutcome.LAUNCH_FAILED
    assert result.compatibility.compatibility is GFVersionCompatibility.NOT_EVALUATED
    assert result.message == "Executable not found."


def test_interpret_cancelled_probe_records_warning(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        execution_state=ExecutionState.CANCELLED,
        exit_code=None,
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.outcome is GFVersionProbeOutcome.UNKNOWN
    assert result.compatibility.compatibility is GFVersionCompatibility.NOT_EVALUATED
    assert result.warnings == ("GF version probe was cancelled.",)


def test_interpret_probe_warns_and_recovers_from_invalid_utf8(tmp_path: Path) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"GF 3.12\xff\n",
    )

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
    )

    assert result.normalized_version == "3.12"
    assert result.accepted is True
    assert result.warnings == (
        "Version-probe stdout was not valid UTF-8; replacement decoding was applied.",
    )


def test_interpret_probe_can_recover_version_when_stdout_read_fails(
    tmp_path: Path,
) -> None:
    process_result = _process_result(
        tmp_path,
        stdout=b"GF 3.11\n",
        stderr=b"GF 3.12\n",
    )

    def reader(path: Path) -> bytes:
        if path == process_result.stdout_path:
            raise OSError("simulated read failure")
        return path.read_bytes()

    result = interpret_gf_version_probe(
        process_result,
        policy=_tested_policy(),
        evidence_reader=reader,
    )

    assert result.normalized_version == "3.12"
    assert result.version_text.source_stream == "stderr"
    assert result.warnings == (
        "Unable to read version-probe stdout: OSError: simulated read failure",
    )


def test_interpret_probe_requires_byte_evidence(tmp_path: Path) -> None:
    process_result = _process_result(tmp_path)

    def invalid_reader(_path: Path) -> bytes:
        return "GF 3.12"  # type: ignore[return-value]

    with pytest.raises(TypeError, match="evidence_reader must return bytes"):
        interpret_gf_version_probe(
            process_result,
            policy=_tested_policy(),
            evidence_reader=invalid_reader,
        )


def test_probe_gf_version_delegates_exact_request_to_executor(tmp_path: Path) -> None:
    request = build_gf_version_probe_request(
        executable=_absolute(tmp_path, "gf"),
        working_directory=tmp_path.resolve(),
        stdout_path=_absolute(tmp_path, "stdout.txt"),
        stderr_path=_absolute(tmp_path, "stderr.txt"),
    )
    process_result = _process_result(
        tmp_path,
        executable=request.executable,
        args=request.args,
        cwd=request.cwd,
    )
    calls: list[ProcessRequest] = []

    def executor(
        received: ProcessRequest,
        *,
        cancellation_token: object | None = None,
        event_sink: object | None = None,
    ) -> ProcessResult:
        assert cancellation_token is None
        assert event_sink is None
        calls.append(received)
        return process_result

    result = probe_gf_version(
        request,
        policy=_tested_policy(),
        executor=executor,  # type: ignore[arg-type]
    )

    assert calls == [request]
    assert result.outcome is GFVersionProbeOutcome.RECOGNIZED
    assert result.normalized_version == "3.12"


def test_probe_gf_version_rejects_executor_contract_drift(tmp_path: Path) -> None:
    request = build_gf_version_probe_request(
        executable=_absolute(tmp_path, "gf"),
        working_directory=tmp_path.resolve(),
        stdout_path=_absolute(tmp_path, "stdout.txt"),
        stderr_path=_absolute(tmp_path, "stderr.txt"),
    )
    process_result = _process_result(
        tmp_path,
        executable=_absolute(tmp_path, "different-gf"),
        args=request.args,
        cwd=request.cwd,
    )

    def executor(
        _request: ProcessRequest,
        *,
        cancellation_token: object | None = None,
        event_sink: object | None = None,
    ) -> ProcessResult:
        return process_result

    with pytest.raises(ValueError, match="executable different"):
        probe_gf_version(
            request,
            policy=_tested_policy(),
            executor=executor,  # type: ignore[arg-type]
        )


def test_probe_gf_version_rejects_non_version_request(tmp_path: Path) -> None:
    request = build_gf_version_probe_request(
        executable=_absolute(tmp_path, "gf"),
        working_directory=tmp_path.resolve(),
        stdout_path=_absolute(tmp_path, "stdout.txt"),
        stderr_path=_absolute(tmp_path, "stderr.txt"),
    )
    invalid = replace(
        request,
        operation_kind=ProcessOperationKind.COMPILE,
    )

    with pytest.raises(ValueError, match="VERSION_PROBE"):
        probe_gf_version(
            invalid,
            policy=_tested_policy(),
        )


def test_skipped_version_result_is_explicit_and_has_no_process(tmp_path: Path) -> None:
    executable = _absolute(tmp_path, "gf")

    result = skipped_gf_version_result(
        executable=executable,
        reason="Version probing disabled by configuration.",
    )

    assert result.outcome is GFVersionProbeOutcome.SKIPPED
    assert result.executable == executable
    assert result.normalized_version is None
    assert result.raw_version_text == UNKNOWN_VERSION_TEXT
    assert result.compatibility.compatibility is GFVersionCompatibility.NOT_EVALUATED
    assert result.process_result is None
    assert result.stdout_path is None
    assert result.stderr_path is None
    assert result.warnings == ("Version probing disabled by configuration.",)
    assert result.message == "Version probing disabled by configuration."
