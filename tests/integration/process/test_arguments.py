"""Integration tests for structured external-process arguments."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from gf_wordbench.infrastructure.process.models import (
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.requests import (
    render_command_for_display,
)
from gf_wordbench.infrastructure.process.runner import run_process
from gf_wordbench.kernel.statuses import ExecutionState


def _request(
    tmp_path: Path,
    *,
    args: tuple[str, ...],
    sensitive_arg_indexes: frozenset[int] = frozenset(),
) -> ProcessRequest:
    capture_root = tmp_path / "capture"
    capture_root.mkdir()

    return ProcessRequest(
        request_id="arguments-integration",
        tool_id="python",
        operation_id="arguments-integration",
        operation_kind=ProcessOperationKind.INTROSPECTION,
        executable=Path(sys.executable).resolve(),
        args=args,
        cwd=tmp_path.resolve(),
        stdout_path=(capture_root / "stdout.bin").resolve(),
        stderr_path=(capture_root / "stderr.bin").resolve(),
        timeout_sec=15.0,
        approved_read_roots=(tmp_path.resolve(),),
        approved_write_roots=(capture_root.resolve(),),
        evidence_policy="bounded",
        sensitive_arg_indexes=sensitive_arg_indexes,
    )


def test_process_preserves_order_and_argument_boundaries(
    tmp_path: Path,
) -> None:
    expected = [
        "",
        "value with spaces",
        "Unicode: français 日本語",
        "--path=C:/Program Files/GF/rgl",
        ";",
        "&&",
        "|",
        ">",
        "$(not-a-command)",
        "%NOT_EXPANDED%",
    ]
    probe = (
        "import json, sys; "
        "print(json.dumps(sys.argv[1:], ensure_ascii=False))"
    )
    request = _request(
        tmp_path,
        args=("-c", probe, *expected),
    )

    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.args == request.args
    assert result.executable == request.executable
    assert result.cwd == request.cwd
    assert result.stderr_path.read_bytes() == b""

    observed = json.loads(
        result.stdout_path.read_text(encoding="utf-8")
    )
    assert observed == expected


def test_shell_metacharacters_are_literal_and_cannot_inject_a_command(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "injected.txt"
    attempted_injection = f"; echo injected > {marker}"
    probe = (
        "import json, sys; "
        "print(json.dumps(sys.argv[1:], ensure_ascii=False))"
    )
    request = _request(
        tmp_path,
        args=("-c", probe, attempted_injection),
    )

    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert json.loads(
        result.stdout_path.read_text(encoding="utf-8")
    ) == [attempted_injection]
    assert not marker.exists()


def test_display_redaction_does_not_change_executed_arguments(
    tmp_path: Path,
) -> None:
    secret = "token with spaces & metacharacters"
    probe = (
        "import json, sys; "
        "print(json.dumps(sys.argv[1:], ensure_ascii=False))"
    )
    request = _request(
        tmp_path,
        args=("-c", probe, "--token", secret),
        sensitive_arg_indexes=frozenset({3}),
    )

    display = render_command_for_display(
        request.executable,
        request.args,
        sensitive_arg_indexes=request.sensitive_arg_indexes,
    )
    result = run_process(request)

    assert "<redacted>" in display
    assert secret not in display
    assert request.args[3] == secret
    assert result.args[3] == secret
    assert json.loads(
        result.stdout_path.read_text(encoding="utf-8")
    ) == ["--token", secret]


@pytest.mark.parametrize(
    "argument",
    (
        "prefix\x00suffix",
        "\x00",
    ),
)
def test_process_request_rejects_nul_arguments(
    tmp_path: Path,
    argument: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"args\[0\] must be a NUL-free string",
    ):
        _request(tmp_path, args=(argument,))
