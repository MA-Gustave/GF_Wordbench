"""Integration coverage for GF execution across paths containing spaces.

The process contract requires executable, arguments, working directory, and
capture paths to remain structured values.  Human-facing quoting must never be
inserted into the execution argument vector.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

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
    GfCommand,
    GfCommandProfile,
    ValueOptionStyle,
    build_module_compile_command,
)

_TEST_GF_ENV = "GF_WORDBENCH_TEST_GF_EXE"
_TIMEOUT_SECONDS = 30.0
_MODULE_NAME = "PathSpacesTst"
_CONCRETE_MODULE_NAME = f"{_MODULE_NAME}Eng"


def _command_profile() -> GfCommandProfile:
    return GfCommandProfile(
        profile_id="integration-paths-with-spaces",
        path_separator=os.pathsep,
        value_option_style=ValueOptionStyle.EQUALS,
        gfo_dir_option="--gfo-dir",
        output_dir_option="--output-dir",
    )


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
    abstract_source = source_root / f"{_MODULE_NAME}.gf"
    concrete_source = source_root / f"{_CONCRETE_MODULE_NAME}.gf"

    abstract_source.write_text(
        f"abstract {_MODULE_NAME} = {{\n"
        "  flags startcat = Utt ;\n"
        "  cat Utt ;\n"
        "  fun Greeting : Utt ;\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    concrete_source.write_text(
        f"concrete {_CONCRETE_MODULE_NAME} of {_MODULE_NAME} = {{\n"
        "  lincat Utt = Str ;\n"
        '  lin Greeting = "hello" ;\n'
        "}\n",
        encoding="utf-8",
        newline="\n",
    )

    return concrete_source


def _build_command(
    *,
    executable: Path,
    source_root: Path,
    source_file: Path,
    gfo_root: Path,
    output_root: Path,
) -> GfCommand:
    return build_module_compile_command(
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


def _assert_structured_space_arguments(
    command: GfCommand,
    *,
    source_root: Path,
    source_file: Path,
    gfo_root: Path,
    output_root: Path,
) -> None:
    expected_path_option = f"--path={source_root}"
    expected_gfo_option = f"--gfo-dir={gfo_root}"
    expected_output_option = f"--output-dir={output_root}"
    expected_source_argument = os.fspath(source_file)

    assert " " in os.fspath(source_root)
    assert " " in os.fspath(gfo_root)
    assert " " in os.fspath(output_root)

    assert expected_path_option in command.arguments
    assert expected_gfo_option in command.arguments
    assert expected_output_option in command.arguments
    assert expected_source_argument in command.arguments

    assert command.arguments.count(expected_path_option) == 1
    assert command.arguments.count(expected_gfo_option) == 1
    assert command.arguments.count(expected_output_option) == 1
    assert command.arguments.count(expected_source_argument) == 1

    assert command.argv == (os.fspath(command.executable), *command.arguments)
    assert all("\x00" not in argument for argument in command.arguments)
    assert all(
        not (
            len(argument) >= 2
            and argument[0] == argument[-1]
            and argument[0] in {'"', "'"}
        )
        for argument in command.arguments
    )


def test_command_preserves_space_bearing_paths_as_atomic_arguments(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "project source with spaces").resolve()
    gfo_root = (tmp_path / "run artifacts with spaces" / "gfo output").resolve()
    output_root = (tmp_path / "run artifacts with spaces" / "other output").resolve()
    source_file = source_root / f"{_CONCRETE_MODULE_NAME}.gf"

    command = _build_command(
        executable=Path(sys.executable).resolve(),
        source_root=source_root,
        source_file=source_file,
        gfo_root=gfo_root,
        output_root=output_root,
    )

    _assert_structured_space_arguments(
        command,
        source_root=source_root,
        source_file=source_file,
        gfo_root=gfo_root,
        output_root=output_root,
    )
    assert command.working_directory == source_root
    assert command.gf_search_paths == (source_root,)


@pytest.mark.gf
def test_real_gf_compiles_with_space_bearing_project_and_run_paths(
    tmp_path: Path,
) -> None:
    executable = _resolve_test_gf_executable()

    source_root = (tmp_path / "GF project source with spaces").resolve()
    run_root = (tmp_path / "GF run evidence with spaces").resolve()
    gfo_root = run_root / "compiled gfo artifacts"
    output_root = run_root / "compiler output artifacts"
    log_root = run_root / "raw process logs"

    for directory in (source_root, gfo_root, output_root, log_root):
        directory.mkdir(parents=True, exist_ok=True)

    source_file = _write_valid_fixture(source_root)
    expected_gfo = gfo_root / f"{_CONCRETE_MODULE_NAME}.gfo"
    stdout_path = log_root / "compile standard output.log"
    stderr_path = log_root / "compile standard error.log"

    command = _build_command(
        executable=executable,
        source_root=source_root,
        source_file=source_file,
        gfo_root=gfo_root,
        output_root=output_root,
    )
    _assert_structured_space_arguments(
        command,
        source_root=source_root,
        source_file=source_file,
        gfo_root=gfo_root,
        output_root=output_root,
    )

    request = ProcessRequest(
        request_id="integration-gf-paths-with-spaces",
        tool_id="gf",
        operation_id="compile-paths-with-spaces",
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
            "target_module": _CONCRETE_MODULE_NAME,
            "path_contract": "spaces-preserved-as-argument-values",
        },
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )

    source_before = {
        path.name: path.read_bytes()
        for path in sorted(source_root.glob("*.gf"))
    }
    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.launch_error_kind is None
    assert result.launch_error_message == ""
    assert result.capture_complete is True
    assert result.output_limit_exceeded is False
    assert result.cancellation_reason is None

    assert result.executable == executable
    assert result.args == command.arguments
    assert result.cwd == source_root
    assert result.stdout_path == stdout_path
    assert result.stderr_path == stderr_path
    assert stdout_path.is_file()
    assert stderr_path.is_file()
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
    assert {
        path.name: path.read_bytes()
        for path in sorted(source_root.glob("*.gf"))
    } == source_before
    assert not (source_root / expected_gfo.name).exists()
