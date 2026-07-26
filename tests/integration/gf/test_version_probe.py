from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.infrastructure.process.models import ProcessOperationKind
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.compilation.version_probe import (
    DEFAULT_VERSION_ARGUMENTS,
    GFVersionCompatibility,
    GFVersionPolicy,
    GFVersionProbeOutcome,
    build_gf_version_probe_request,
    probe_gf_version,
)

pytestmark = pytest.mark.gf

_GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_TEST_GF_EXE"
_TIMEOUT_SEC: Final[float] = 20.0
_OUTPUT_LIMIT_BYTES: Final[int] = 64 * 1024


def _configured_gf_executable() -> Path:
    raw_value = os.environ.get(_GF_EXECUTABLE_ENV)
    if not raw_value:
        pytest.skip(
            f"{_GF_EXECUTABLE_ENV} is not configured for the real-GF suite"
        )

    candidate = Path(raw_value).expanduser()
    try:
        executable = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(
            f"{_GF_EXECUTABLE_ENV} does not resolve to an existing file: "
            f"{candidate!s}: {exc}"
        )

    if not executable.is_file():
        pytest.fail(
            f"{_GF_EXECUTABLE_ENV} must identify a GF executable file: "
            f"{executable}"
        )
    return executable


def _read_evidence(path: Path) -> str:
    assert path.is_file(), f"missing process evidence: {path}"
    return path.read_text(encoding="utf-8", errors="replace")


def test_real_gf_version_probe_recognizes_and_preserves_version_evidence(
    tmp_path: Path,
) -> None:
    executable = _configured_gf_executable()

    workspace = (tmp_path / "version-probe").resolve()
    evidence_root = workspace / "evidence"
    evidence_root.mkdir(parents=True)

    stdout_path = evidence_root / "gf-version.out.txt"
    stderr_path = evidence_root / "gf-version.err.txt"

    request = build_gf_version_probe_request(
        executable=executable,
        working_directory=workspace,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=_TIMEOUT_SEC,
        version_arguments=DEFAULT_VERSION_ARGUMENTS,
        request_id="real-gf-version-probe",
        operation_id="version",
        approved_read_roots=(workspace,),
        approved_write_roots=(workspace,),
        output_limit_bytes=_OUTPUT_LIMIT_BYTES,
    )
    policy = GFVersionPolicy(
        allow_untested_versions=True,
        strict_unknown=True,
    )

    result = probe_gf_version(
        request,
        policy=policy,
    )

    assert request.operation_kind is ProcessOperationKind.VERSION_PROBE
    assert request.args == DEFAULT_VERSION_ARGUMENTS
    assert request.mutability_class == "read_only"
    assert request.network_policy == "denied"

    assert result.outcome is GFVersionProbeOutcome.RECOGNIZED
    assert result.recognized
    assert result.accepted
    assert result.parsed_version is not None
    assert result.normalized_version == str(result.parsed_version)
    assert result.raw_version_text.strip()
    assert result.version_text.source_stream in {"stdout", "stderr"}

    process_result = result.process_result
    assert process_result is not None
    assert process_result.execution_state is ExecutionState.COMPLETED
    assert process_result.exit_code == 0
    assert process_result.operation_kind is ProcessOperationKind.VERSION_PROBE
    assert process_result.executable == executable
    assert process_result.args == DEFAULT_VERSION_ARGUMENTS
    assert process_result.cwd == workspace
    assert process_result.capture_complete
    assert not process_result.output_limit_exceeded

    assert result.stdout_path == stdout_path
    assert result.stderr_path == stderr_path
    stdout = _read_evidence(stdout_path)
    stderr = _read_evidence(stderr_path)
    combined_evidence = f"{stdout}\n{stderr}"

    assert combined_evidence.strip()
    assert result.raw_version_text in combined_evidence

    assert result.compatibility.compatibility in {
        GFVersionCompatibility.SUPPORTED,
        GFVersionCompatibility.SUPPORTED_WITH_WARNING,
    }


def test_real_gf_version_probe_is_repeatable_and_read_only(
    tmp_path: Path,
) -> None:
    executable = _configured_gf_executable()

    workspace = (tmp_path / "repeatable-version-probe").resolve()
    workspace.mkdir(parents=True)
    before = tuple(sorted(path.relative_to(workspace) for path in workspace.rglob("*")))

    versions: list[str] = []
    for attempt in (1, 2):
        evidence_root = workspace / f"attempt-{attempt}"
        evidence_root.mkdir()

        request = build_gf_version_probe_request(
            executable=executable,
            working_directory=workspace,
            stdout_path=evidence_root / "stdout.txt",
            stderr_path=evidence_root / "stderr.txt",
            timeout_sec=_TIMEOUT_SEC,
            approved_read_roots=(workspace,),
            approved_write_roots=(workspace,),
            output_limit_bytes=_OUTPUT_LIMIT_BYTES,
        )
        result = probe_gf_version(
            request,
            policy=GFVersionPolicy(
                allow_untested_versions=True,
                strict_unknown=True,
            ),
        )

        assert result.outcome is GFVersionProbeOutcome.RECOGNIZED
        assert result.normalized_version is not None
        versions.append(result.normalized_version)

    assert versions[0] == versions[1]

    generated = {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert generated == {
        "attempt-1/stderr.txt",
        "attempt-1/stdout.txt",
        "attempt-2/stderr.txt",
        "attempt-2/stdout.txt",
    }
    assert before == ()
