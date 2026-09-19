"""Real-GF integration tests for native scenario execution."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

import pytest

from gf_wordbench.infrastructure.process.models import (
    ProcessInputKind,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.scenarios.execution import (
    ScenarioScriptInput,
    build_scenario_process_request,
    execute_scenario_process,
)
from gf_wordbench.validation.scenarios.markers import (
    format_begin_marker,
    format_end_marker,
    validate_scenario_markers,
)

pytestmark = pytest.mark.gf

_SCENARIO_ID = "integration-scenario-execution"
_SECTION_ID = "linearize-smoke"
_TIMEOUT_SEC = 30.0
_OUTPUT_LIMIT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class _ScenarioFixture:
    root: Path
    executable: Path
    script_path: Path
    stdout_path: Path
    stderr_path: Path
    source_paths: tuple[Path, ...]
    source_hashes: tuple[str, ...]


def _find_gf_executable() -> Path:
    configured = os.environ.get("GF_WORDBENCH_GF_EXECUTABLE") or os.environ.get("GF_EXECUTABLE")
    candidate = configured or shutil.which("gf")

    if not candidate:
        pytest.skip(
            "A real GF executable is required; set GF_WORDBENCH_GF_EXECUTABLE or place gf on PATH."
        )

    executable = Path(candidate).expanduser().resolve()
    if not executable.is_file():
        pytest.skip(f"Configured GF executable is not a file: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        pytest.skip(f"Configured GF executable is not executable: {executable}")
    return executable


def _write_fixture(
    tmp_path: Path,
    *,
    script_text: str,
) -> _ScenarioFixture:
    root = (tmp_path / "GF scenario fixture with spaces").resolve()
    evidence = root / "run evidence" / "raw" / "scenarios"
    root.mkdir(parents=True)
    evidence.mkdir(parents=True)

    abstract_path = root / "Smoke.gf"
    concrete_path = root / "SmokeEng.gf"
    script_path = root / f"{_SCENARIO_ID}.gfs"

    abstract_path.write_text(
        """abstract Smoke = {
  flags startcat = S ;
  cat S ;
  fun Greeting : S ;
}
""",
        encoding="utf-8",
        newline="\n",
    )
    concrete_path.write_text(
        """concrete SmokeEng of Smoke = {
  lincat S = Str ;
  lin Greeting = "héllo 世界" ;
}
""",
        encoding="utf-8",
        newline="\n",
    )
    script_path.write_text(
        script_text,
        encoding="utf-8",
        newline="\n",
    )

    source_paths = (abstract_path, concrete_path, script_path)
    source_hashes = tuple(
        __import__("hashlib").sha256(path.read_bytes()).hexdigest() for path in source_paths
    )

    return _ScenarioFixture(
        root=root,
        executable=_find_gf_executable(),
        script_path=script_path,
        stdout_path=evidence / f"{_SCENARIO_ID}.out.txt",
        stderr_path=evidence / f"{_SCENARIO_ID}.err.txt",
        source_paths=source_paths,
        source_hashes=source_hashes,
    )


def _scenario_script(*, include_markers: bool) -> str:
    lines = ["i SmokeEng.gf"]
    if include_markers:
        lines.append(f'ps "{format_begin_marker(_SECTION_ID)}"')
    lines.append("l Greeting")
    if include_markers:
        lines.append(f'ps "{format_end_marker(_SECTION_ID)}"')
    lines.append("q")
    return "\n".join(lines) + "\n"


def _script_input(fixture: _ScenarioFixture) -> ScenarioScriptInput:
    return ScenarioScriptInput.from_bytes(
        scenario_id=_SCENARIO_ID,
        script_path=fixture.script_path,
        content=fixture.script_path.read_bytes(),
    )


def _build_request(fixture: _ScenarioFixture) -> ProcessRequest:
    return build_scenario_process_request(
        _script_input(fixture),
        executable=fixture.executable,
        args=(),
        working_directory=fixture.root,
        stdout_path=fixture.stdout_path,
        stderr_path=fixture.stderr_path,
        timeout_sec=_TIMEOUT_SEC,
        output_limit_bytes=_OUTPUT_LIMIT_BYTES,
        approved_read_roots=(
            fixture.root,
            fixture.executable.parent,
        ),
        approved_write_roots=(fixture.root,),
        request_id="scenario.integration.execution",
        operation_id="scenario.integration.execution",
        metadata={
            "fixture_kind": "real-gf",
            "execution_transport": "direct-stdin",
        },
    )


def _execute(fixture: _ScenarioFixture) -> tuple[ProcessRequest, ProcessResult]:
    request = _build_request(fixture)
    result = execute_scenario_process(request)
    return request, result


def _assert_sources_unchanged(fixture: _ScenarioFixture) -> None:
    import hashlib

    observed = tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in fixture.source_paths)
    assert observed == fixture.source_hashes


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def test_real_gf_executes_native_gfs_over_direct_stdin_and_preserves_evidence(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(
        tmp_path,
        script_text=_scenario_script(include_markers=True),
    )

    request, result = _execute(fixture)

    assert request.operation_kind is ProcessOperationKind.SCENARIO
    assert request.stdin.kind is ProcessInputKind.TEXT
    assert request.stdin.text == fixture.script_path.read_text(encoding="utf-8")
    assert request.stdin.path is None
    assert request.args == ()
    assert request.cwd == fixture.root
    assert request.stdout_path != request.stderr_path
    assert request.metadata["scenario_id"] == _SCENARIO_ID
    assert request.metadata["script_path"] == fixture.script_path.as_posix()
    assert request.metadata["execution_transport"] == "direct-stdin"

    assert result.operation_kind is ProcessOperationKind.SCENARIO
    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.cancelled is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True
    assert result.executable == fixture.executable
    assert result.args == ()
    assert result.cwd == fixture.root
    assert result.stdout_path == fixture.stdout_path
    assert result.stderr_path == fixture.stderr_path

    assert fixture.stdout_path.is_file()
    assert fixture.stderr_path.is_file()
    assert result.stdout_size_bytes == fixture.stdout_path.stat().st_size
    assert result.stderr_size_bytes == fixture.stderr_path.stat().st_size

    stdout = _read_utf8(fixture.stdout_path)
    _read_utf8(fixture.stderr_path)

    assert format_begin_marker(_SECTION_ID) in stdout
    assert format_end_marker(_SECTION_ID) in stdout
    assert "héllo 世界" in stdout

    markers = validate_scenario_markers(
        stdout,
        (_SECTION_ID,),
        raw_output_path=fixture.stdout_path,
    )
    assert markers.valid is True
    assert markers.complete is True
    assert tuple(map(str, markers.completed_section_ids)) == (_SECTION_ID,)
    assert markers.raw_output_path == fixture.stdout_path

    _assert_sources_unchanged(fixture)


def test_zero_exit_without_required_markers_is_not_scenario_success(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(
        tmp_path,
        script_text=_scenario_script(include_markers=False),
    )

    _request, result = _execute(fixture)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.output_limit_exceeded is False

    stdout = _read_utf8(fixture.stdout_path)
    markers = validate_scenario_markers(
        stdout,
        (_SECTION_ID,),
        raw_output_path=fixture.stdout_path,
    )

    assert markers.valid is False
    assert markers.complete is False
    assert markers.failures
    assert tuple(map(str, markers.completed_section_ids)) == ()

    _assert_sources_unchanged(fixture)
