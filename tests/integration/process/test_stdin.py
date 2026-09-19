"""Integration coverage for explicit process standard-input delivery.

These tests exercise the real process runner with a controlled Python child.
They verify that ``none``, Unicode text, encoded text, and file-backed input are
passed without a command shell, are closed at end of input, and preserve raw
stdout/stderr evidence.  Contract failures must occur before process launch or
capture-file creation.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest

from gf_wordbench.infrastructure.process.models import (
    ProcessInput,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.runner import run_process
from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError
from gf_wordbench.kernel.statuses import ExecutionState

_TIMEOUT_SECONDS = 10.0

_ECHO_STDIN = (
    "import sys; "
    "data = sys.stdin.buffer.read(); "
    "sys.stdout.buffer.write(data); "
    "sys.stdout.buffer.flush()"
)
_REPORT_LENGTH = (
    "import sys; "
    "data = sys.stdin.buffer.read(); "
    "sys.stdout.write(str(len(data))); "
    "sys.stdout.flush()"
)
_REPORT_EOF = (
    "import sys; "
    "first = sys.stdin.buffer.read(); "
    "second = sys.stdin.buffer.read(1); "
    "sys.stdout.write(f'{len(first)}:{len(second)}'); "
    "sys.stdout.flush()"
)


def _request(
    tmp_path: Path,
    *,
    stdin: ProcessInput,
    child_program: str = _ECHO_STDIN,
    approved_read_roots: tuple[Path, ...] | None = None,
) -> ProcessRequest:
    root = tmp_path.resolve()
    captures = root / "captures"
    executable = Path(sys.executable).resolve(strict=True)

    return ProcessRequest(
        request_id="integration-process-stdin",
        tool_id="python-test-child",
        operation_id="stdin-delivery",
        operation_kind=ProcessOperationKind.INTROSPECTION,
        executable=executable,
        args=("-c", child_program),
        cwd=root,
        stdout_path=captures / "stdout.bin",
        stderr_path=captures / "stderr.bin",
        timeout_sec=_TIMEOUT_SECONDS,
        approved_read_roots=(
            approved_read_roots if approved_read_roots is not None else (root, executable.parent)
        ),
        approved_write_roots=(root,),
        evidence_policy="retain-raw-streams-v1",
        stdin=stdin,
        environment_policy="controlled-inherit-v1",
        output_limit_bytes=2 * 1024 * 1024,
        metadata={"contract": "stdin-delivery"},
        mutability_class="read_only",
        network_policy="denied",
    )


def _assert_completed(request: ProcessRequest) -> bytes:
    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.pid is not None
    assert result.launch_error_kind is None
    assert result.launch_error_message == ""
    assert result.cancellation_reason is None
    assert result.termination_attempted is False
    assert result.termination_succeeded is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True

    assert result.executable == request.executable
    assert result.args == request.args
    assert result.cwd == request.cwd
    assert result.stdout_path == request.stdout_path
    assert result.stderr_path == request.stderr_path

    assert request.stdout_path.is_file()
    assert request.stderr_path.is_file()
    assert result.stdout_size_bytes == request.stdout_path.stat().st_size
    assert result.stderr_size_bytes == request.stderr_path.stat().st_size
    assert request.stderr_path.read_bytes() == b""

    return request.stdout_path.read_bytes()


def test_none_input_is_closed_and_does_not_inherit_parent_terminal(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        stdin=ProcessInput.none(),
        child_program=_REPORT_LENGTH,
    )

    assert _assert_completed(request) == b"0"


def test_empty_text_input_is_distinct_from_none_but_delivers_eof(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text(""),
        child_program=_REPORT_EOF,
    )

    assert request.stdin.text == ""
    assert _assert_completed(request) == b"0:0"


def test_utf8_text_is_delivered_as_exact_bytes_and_then_closed(
    tmp_path: Path,
) -> None:
    text = "parse -lang=Eng ‘café’\n日本語\n🙂\n"
    request = _request(tmp_path, stdin=ProcessInput.from_text(text))

    assert _assert_completed(request) == text.encode("utf-8")


def test_explicit_text_encoding_controls_delivered_bytes(
    tmp_path: Path,
) -> None:
    text = "café déjà vu\r\n"
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text(text, encoding="latin-1"),
    )

    assert _assert_completed(request) == text.encode("latin-1")


def test_file_input_preserves_exact_binary_content_and_source_file(
    tmp_path: Path,
) -> None:
    source = (tmp_path / "scenario inputs" / "stdin payload.gfs").resolve()
    source.parent.mkdir(parents=True)
    payload = b"\xef\xbb\xbfparse -lang=Eng\r\n\x00raw-byte\xff\n"
    source.write_bytes(payload)
    before_stat = source.stat()

    request = _request(tmp_path, stdin=ProcessInput.from_file(source))

    assert _assert_completed(request) == payload
    assert source.read_bytes() == payload
    after_stat = source.stat()
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_stdin_metacharacters_are_data_not_shell_syntax(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "must-not-exist"
    text = f"; echo injected > {marker}\n$(touch {marker})\n& type nul > {marker}\n"
    request = _request(tmp_path, stdin=ProcessInput.from_text(text))

    assert _assert_completed(request) == text.encode("utf-8")
    assert not marker.exists()


def test_large_text_input_is_delivered_without_pipe_deadlock(
    tmp_path: Path,
) -> None:
    payload = ("0123456789abcdef" * 32_768) + "\n"
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text(payload),
        child_program=_REPORT_EOF,
    )

    assert _assert_completed(request) == f"{len(payload.encode())}:0".encode()


def test_missing_stdin_file_is_rejected_before_capture_creation(
    tmp_path: Path,
) -> None:
    missing = (tmp_path / "missing input.gfs").resolve()
    request = _request(tmp_path, stdin=ProcessInput.from_file(missing))

    with pytest.raises(ContractViolationError, match="stdin file does not resolve"):
        run_process(request)

    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()


def test_stdin_directory_is_rejected_before_launch(tmp_path: Path) -> None:
    directory = (tmp_path / "not a regular file").resolve()
    directory.mkdir()
    request = _request(tmp_path, stdin=ProcessInput.from_file(directory))

    with pytest.raises(ContractViolationError, match="not a regular file"):
        run_process(request)

    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()


def test_stdin_file_must_be_inside_an_approved_read_root(
    tmp_path: Path,
) -> None:
    approved = (tmp_path / "approved").resolve()
    outside = (tmp_path / "outside" / "payload.gfs").resolve()
    approved.mkdir()
    outside.parent.mkdir()
    outside.write_text("q\n", encoding="utf-8")

    request = _request(
        tmp_path,
        stdin=ProcessInput.from_file(outside),
        approved_read_roots=(approved, Path(sys.executable).resolve().parent),
    )

    with pytest.raises(PathSecurityError, match="stdin file"):
        run_process(request)

    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()


def test_unknown_stdin_encoding_is_rejected_before_launch(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text("q\n", encoding="not-a-real-codec"),
    )

    with pytest.raises(ContractViolationError, match="Unknown stdin encoding"):
        run_process(request)

    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()


def test_unencodable_text_is_rejected_before_launch(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text("café", encoding="ascii"),
    )

    with pytest.raises(ContractViolationError, match="cannot be encoded"):
        run_process(request)

    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()


def test_stdin_contract_failure_does_not_modify_existing_capture_files(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        stdin=ProcessInput.from_text("🙂", encoding="ascii"),
    )
    request.stdout_path.parent.mkdir(parents=True)
    request.stdout_path.write_bytes(b"existing stdout")
    request.stderr_path.write_bytes(b"existing stderr")

    with pytest.raises(ContractViolationError, match="cannot be encoded"):
        run_process(request)

    assert request.stdout_path.read_bytes() == b"existing stdout"
    assert request.stderr_path.read_bytes() == b"existing stderr"


def test_reusing_request_replays_immutable_text_input_deterministically(
    tmp_path: Path,
) -> None:
    text = "ps -lang=Eng 'hello world'\n"
    original = _request(tmp_path, stdin=ProcessInput.from_text(text))
    first = _assert_completed(original)

    second = replace(
        original,
        request_id="integration-process-stdin-repeat",
        operation_id="stdin-delivery-repeat",
        stdout_path=tmp_path / "captures-2" / "stdout.bin",
        stderr_path=tmp_path / "captures-2" / "stderr.bin",
    )

    assert _assert_completed(second) == first == text.encode("utf-8")
