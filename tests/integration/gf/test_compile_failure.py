from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.infrastructure.process import ProcessRequest, run_process
from gf_wordbench.infrastructure.process.models import ProcessOperationKind
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.compilation.commands import (
    GfCommandProfile,
    build_module_compile_command,
)

pytestmark = pytest.mark.gf

_GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_TEST_GF_EXE"
_TIMEOUT_SEC: Final[float] = 20.0
_OUTPUT_LIMIT_BYTES: Final[int] = 2 * 1024 * 1024


def _configured_gf_executable() -> Path:
    raw_value = os.environ.get(_GF_EXECUTABLE_ENV)
    if not raw_value:
        pytest.skip(f"{_GF_EXECUTABLE_ENV} is not configured for the real-GF suite")

    candidate = Path(raw_value).expanduser()
    try:
        executable = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(
            f"{_GF_EXECUTABLE_ENV} does not resolve to an existing file: {candidate!s}: {exc}"
        )

    if not executable.is_file():
        pytest.fail(f"{_GF_EXECUTABLE_ENV} must identify a GF executable file: {executable}")
    return executable


def _write_failing_grammar(source_root: Path) -> Path:
    source_path = source_root / "BrokenCompile.gf"
    source_path.write_text(
        "\n".join(
            (
                "abstract BrokenCompile = {",
                "  cat S ;",
                "  fun broken : MissingCategory ;",
                "}",
                "",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    return source_path


def _read_evidence(path: Path) -> str:
    assert path.is_file(), f"missing process evidence: {path}"
    return path.read_text(encoding="utf-8", errors="replace")


def test_real_gf_compile_failure_preserves_authoritative_process_evidence(
    tmp_path: Path,
) -> None:
    executable = _configured_gf_executable()

    workspace = (tmp_path / "compile-failure").resolve()
    source_root = workspace / "source"
    evidence_root = workspace / "evidence"
    source_root.mkdir(parents=True)
    evidence_root.mkdir()

    source_path = _write_failing_grammar(source_root)
    stdout_path = evidence_root / "compile.out.txt"
    stderr_path = evidence_root / "compile.err.txt"

    profile = GfCommandProfile(
        profile_id="real-gf-test",
        path_separator=os.pathsep,
        gf_lib_path_option=None,
        gfo_dir_option=None,
        output_dir_option=None,
        cpu_stats_flag=None,
    )
    command = build_module_compile_command(
        executable=executable,
        working_directory=source_root,
        source_file=source_path.name,
        gf_search_paths=(source_root,),
        profile=profile,
        quiet=False,
    )

    request = ProcessRequest(
        request_id="real-gf-compile-failure",
        tool_id="gf",
        operation_id="real-gf-compile-failure",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=command.executable,
        args=command.arguments,
        cwd=command.working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=_TIMEOUT_SEC,
        approved_read_roots=(workspace,),
        approved_write_roots=(workspace,),
        evidence_policy="raw-streams-required-v1",
        output_limit_bytes=_OUTPUT_LIMIT_BYTES,
        mutability_class="run_artifacts_only",
        network_policy="denied",
        metadata={
            "fixture": "BrokenCompile",
            "expected_outcome": "language_compile_failure",
        },
    )

    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code is not None
    assert result.exit_code != 0
    assert result.capture_complete
    assert not result.output_limit_exceeded
    assert result.command == command.argv
    assert result.working_directory == source_root
    assert result.stdout_path == stdout_path
    assert result.stderr_path == stderr_path

    stdout = _read_evidence(stdout_path)
    stderr = _read_evidence(stderr_path)
    combined_evidence = f"{stdout}\n{stderr}"

    assert combined_evidence.strip(), "GF failure emitted no diagnostic evidence"
    assert (
        source_path.name in combined_evidence
        or "MissingCategory" in combined_evidence
        or "missingcategory" in combined_evidence.casefold()
    ), combined_evidence

    assert not (source_root / "BrokenCompile.gfo").exists()
