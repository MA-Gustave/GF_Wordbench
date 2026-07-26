"""Real-GF integration coverage for expected-artifact observations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.config.environment import GF_EXECUTABLE_ENV
from gf_wordbench.infrastructure.process import (
    ArtifactExpectation,
    ProcessRequest,
    run_process,
)
from gf_wordbench.infrastructure.process.models import (
    ArtifactKind,
    ProcessOperationKind,
)
from gf_wordbench.kernel.statuses import ExecutionState

pytestmark = pytest.mark.gf

_CANONICAL_GF_EXECUTABLE_ENV: Final = "GF_WORDBENCH_GF_EXECUTABLE"
_GF_EXECUTABLE_ENV_NAMES: Final[tuple[str, ...]] = tuple(
    dict.fromkeys((_CANONICAL_GF_EXECUTABLE_ENV, GF_EXECUTABLE_ENV))
)
_FIXTURE_MODULE: Final = "ArtifactObservationProbe"
_FIXTURE_SOURCE: Final = """abstract ArtifactObservationProbe = {
  flags startcat = S ;
  cat S ;
  fun Hello : S ;
}
"""


def _configured_gf_executable() -> Path:
    configured_name: str | None = None
    configured_value: str | None = None

    for name in _GF_EXECUTABLE_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            configured_name = name
            configured_value = value
            break

    if configured_value is None:
        names = ", ".join(_GF_EXECUTABLE_ENV_NAMES)
        pytest.skip(f"real GF is not configured; set one of: {names}")

    candidate = Path(os.path.expandvars(configured_value)).expanduser()
    if not candidate.is_absolute():
        pytest.fail(f"{configured_name} must contain an absolute path")

    try:
        executable = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(f"{configured_name} does not resolve: {candidate}: {exc}")

    if not executable.is_file():
        pytest.fail(f"{configured_name} is not a regular file: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        pytest.fail(f"{configured_name} is not executable: {executable}")

    return executable


def _process_request(
    *,
    executable: Path,
    workspace: Path,
    expectations: tuple[ArtifactExpectation, ...],
) -> ProcessRequest:
    return ProcessRequest(
        request_id="gf-artifact-observation",
        tool_id="gf",
        operation_id="gf-artifact-observation",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=executable,
        args=(
            "-batch",
            "-s",
            f"--path={workspace}",
            f"{_FIXTURE_MODULE}.gf",
        ),
        cwd=workspace,
        stdout_path=workspace / "evidence" / "stdout.bin",
        stderr_path=workspace / "evidence" / "stderr.bin",
        timeout_sec=60.0,
        approved_read_roots=(workspace,),
        approved_write_roots=(workspace,),
        evidence_policy="complete",
        expected_artifacts=expectations,
        mutability_class="run_artifacts_only",
    )


def _captured_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_real_gf_records_present_and_missing_required_artifacts_in_request_order(
    tmp_path: Path,
) -> None:
    executable = _configured_gf_executable()
    source_path = tmp_path / f"{_FIXTURE_MODULE}.gf"
    compiled_path = tmp_path / f"{_FIXTURE_MODULE}.gfo"
    missing_path = tmp_path / "missing-required-artifact.pgf"
    source_path.write_text(_FIXTURE_SOURCE, encoding="utf-8", newline="\n")
    assert not compiled_path.exists()
    assert not missing_path.exists()

    expectations = (
        ArtifactExpectation(
            path=compiled_path,
            role="compiled-module",
            required=True,
            kind=ArtifactKind.FILE,
            minimum_size_bytes=1,
        ),
        ArtifactExpectation(
            path=missing_path,
            role="missing-required-control",
            required=True,
            kind=ArtifactKind.FILE,
            minimum_size_bytes=1,
        ),
    )
    request = _process_request(
        executable=executable,
        workspace=tmp_path,
        expectations=expectations,
    )

    result = run_process(request)
    stdout = _captured_text(result.stdout_path)
    stderr = _captured_text(result.stderr_path)
    evidence = f"stdout:\n{stdout}\n\nstderr:\n{stderr}"

    assert result.execution_state is ExecutionState.COMPLETED, evidence
    assert result.exit_code == 0, evidence
    assert result.capture_complete, evidence
    assert tuple(observation.path for observation in result.artifact_observations) == (
        compiled_path,
        missing_path,
    )

    generated, missing = result.artifact_observations

    assert generated.role == "compiled-module"
    assert generated.required
    assert generated.exists
    assert generated.kind_matches
    assert generated.size_bytes is not None
    assert generated.size_bytes >= expectations[0].minimum_size_bytes
    assert compiled_path.is_file()

    assert missing.role == "missing-required-control"
    assert missing.required
    assert not missing.exists
    assert not missing.kind_matches
    assert missing.size_bytes is None
    assert not missing_path.exists()
