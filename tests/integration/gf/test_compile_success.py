"""Real-GF integration coverage for a successful module compilation."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.runner import run_process
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.compilation.commands import (
    GfCommandProfile,
    ValueOptionStyle,
    build_module_compile_command,
)

pytestmark = pytest.mark.gf

_TEST_GF_ENV = "GF_WORDBENCH_TEST_GF_EXE"
_TIMEOUT_SECONDS = 30.0


def _resolve_test_gf_executable() -> Path:
    configured = os.environ.get(_TEST_GF_ENV, "").strip()
    if not configured:
        pytest.skip(
            f"real GF integration requires {_TEST_GF_ENV} to name the GF executable"
        )

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        discovered = shutil.which(configured)
        if discovered is None:
            pytest.skip(
                f"{_TEST_GF_ENV}={configured!r} does not resolve to an executable"
            )
        candidate = Path(discovered)

    try:
        executable = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.skip(f"configured GF executable cannot be resolved: {exc}")

    if not executable.is_file():
        pytest.skip(f"configured GF executable is not a regular file: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        pytest.skip(f"configured GF executable is not executable: {executable}")

    return executable


def _write_valid_fixture(source_root: Path) -> Path:
    abstract_source = source_root / "CompileSuccess.gf"
    concrete_source = source_root / "CompileSuccessEng.gf"

    abstract_source.write_text(
        """abstract CompileSuccess = {\n"
        "  flags startcat = Utt ;\n"
        "  cat Utt ;\n"
        "  fun Greeting : Utt ;\n"
        "}\n""",
        encoding="utf-8",
        newline="\n",
    )
    concrete_source.write_text(
        """concrete CompileSuccessEng of CompileSuccess = {\n"
        "  lincat Utt = Str ;\n"
        "  lin Greeting = \"hello\" ;\n"
        "}\n""",
        encoding="utf-8",
        newline="\n",
    )

    return concrete_source


def _command_profile() -> GfCommandProfile:
    return GfCommandProfile(
        profile_id="integration-real-gf",
        path_separator=os.pathsep,
        value_option_style=ValueOptionStyle.EQUALS,
        gfo_dir_option="--gfo-dir",
        output_dir_option="--output-dir",
    )


def test_real_gf_compiles_valid_module_and_records_fresh_artifact(
    tmp_path: Path,
) -> None:
    executable = _resolve_test_gf_executable()

    source_root = (tmp_path / "source with spaces").resolve()
    run_root = (tmp_path / "run evidence").resolve()
    gfo_root = run_root / "artifacts" / "gfo"
    output_root = run_root / "artifacts" / "out"
    log_root = run_root / "logs"

    for directory in (source_root, gfo_root, output_root, log_root):
        directory.mkdir(parents=True, exist_ok=True)

    source_file = _write_valid_fixture(source_root)
    expected_gfo = gfo_root / "CompileSuccessEng.gfo"
    stdout_path = log_root / "compile.stdout.log"
    stderr_path = log_root / "compile.stderr.log"

    command = build_module_compile_command(
        executable=executable,
        working_directory=source_root,
        source_file=source_file,
        gf_search_paths=(source_root,),
        profile=_command_profile(),
        gfo_dir=gfo_root,
        output_dir=output_root,
        quiet=True,
        emit_cpu_stats=False,
    )

    assert command.arguments[0] == "-batch"
    assert command.arguments[-1] == os.fspath(source_file)
    assert any(argument.startswith("--path=") for argument in command.arguments)
    assert any(argument == f"--gfo-dir={gfo_root}" for argument in command.arguments)

    request = ProcessRequest(
        request_id="integration-gf-compile-success",
        tool_id="gf",
        operation_id="compile-success",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=command.executable,
        args=command.arguments,
        cwd=command.working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=_TIMEOUT_SECONDS,
        approved_read_roots=(source_root, executable.parent),
        approved_write_roots=(run_root,),
        evidence_policy="retain-raw-streams-v1",
        environment_policy="controlled-inherit-v1",
        env_removals=frozenset({"GF_LIB_PATH"}),
        expected_artifacts=(
            ArtifactExpectation(
                path=expected_gfo,
                role="gfo",
                required=True,
                kind=ArtifactKind.FILE,
                minimum_size_bytes=1,
            ),
        ),
        metadata={
            "gf_operation_kind": "compile_module",
            "target_module": "CompileSuccessEng",
        },
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )

    before_source = source_file.read_bytes()
    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.pid is not None
    assert result.capture_complete is True
    assert result.output_limit_exceeded is False
    assert result.launch_error_kind is None
    assert result.launch_error_message == ""
    assert result.cancellation_reason is None
    assert result.termination_attempted is False
    assert result.termination_succeeded is False

    assert result.executable == executable
    assert result.args == command.arguments
    assert result.cwd == source_root
    assert result.stdout_path == stdout_path
    assert result.stderr_path == stderr_path
    assert stdout_path.is_file()
    assert stderr_path.is_file()
    assert stdout_path != stderr_path
    assert result.stdout_size_bytes == stdout_path.stat().st_size
    assert result.stderr_size_bytes == stderr_path.stat().st_size

    assert len(result.artifact_observations) == 1
    observation = result.artifact_observations[0]
    assert observation.path == expected_gfo
    assert observation.role == "gfo"
    assert observation.required is True
    assert observation.exists is True
    assert observation.kind_matches is True
    assert observation.size_bytes is not None
    assert observation.size_bytes > 0

    assert expected_gfo.is_file()
    assert expected_gfo.stat().st_size == observation.size_bytes
    assert source_file.read_bytes() == before_source
    assert not (source_root / expected_gfo.name).exists()
