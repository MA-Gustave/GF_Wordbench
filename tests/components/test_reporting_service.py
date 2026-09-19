from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.config.models import ResolvedEnvironment
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from gf_wordbench.reporting.summary.json_writer import write_summary_json
from gf_wordbench.reporting.summary.markdown_writer import write_summary_md
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.models.results import RunResult, RunTotals
from gf_wordbench.runs.paths import build_run_paths
from tests.helpers.builders import make_project_config, make_run_config


@dataclass(frozen=True, slots=True)
class _ReportingRunPaths:
    """Expose canonical paths plus the locked writer compatibility aliases."""

    canonical: RunPaths

    def __getattr__(self, name: str) -> object:
        return getattr(self.canonical, name)

    @property
    def summary_json_path(self) -> Path:
        return self.canonical.summary_json

    @property
    def summary_md_path(self) -> Path:
        return self.canonical.summary_md


@pytest.fixture
def completed_run_result(tmp_path: Path) -> RunResult:
    workspace = tmp_path / "workspace"
    project_root = workspace / "project"
    rgl_root = workspace / "rgl"
    output_root = workspace / "output"
    gf_executable = workspace / "tools" / "gf"
    run_id = "20260725_120000"
    run_dir = output_root / f"run_{run_id}"

    for directory in (
        project_root / "lib" / "src",
        rgl_root,
        output_root,
        gf_executable.parent,
        run_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    gf_executable.write_bytes(b"")

    run_paths = _ReportingRunPaths(build_run_paths(run_id, run_dir))
    project = make_project_config(
        project_root=project_root,
        project_id="demo-project",
        project_name="Demo Project",
        language_code="demo",
        source_directory=Path("lib/src"),
        source_glob="**/*.gf",
        entrypoints=(),
        checkpoints=(),
        required_scenarios=(),
        optional_scenarios=(),
        release_requires_pgf=False,
    )
    environment = ResolvedEnvironment(
        project_root=project_root,
        rgl_root=rgl_root,
        gf_executable=gf_executable,
        output_root=output_root,
        gf_path=(project.source_root, rgl_root),
    )
    run_config = make_run_config(
        project=project,
        environment=environment,
        mode=ValidationMode.DIAGNOSTIC,
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        release_requires_pgf=False,
        evidence_level="standard",
    )

    started_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    finished_at = started_at + timedelta(milliseconds=125)
    totals = RunTotals(
        files_seen=0,
        files_included=0,
        files_excluded=0,
        files_ok=0,
        files_fail=0,
        files_error=0,
        files_skipped=0,
        direct_fail=0,
        downstream_fail=0,
        ambiguous_fail=0,
        excluded_noise=0,
        scenarios_seen=0,
        scenarios_ok=0,
        scenarios_fail=0,
        scenarios_error=0,
        scenarios_skipped=0,
        required_scenario_fail=0,
        overall_status=OverallStatus.OK,
    )
    return RunResult(
        run_config=run_config,
        run_paths=cast(RunPaths, run_paths),
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=125,
        gf_version="3.12",
        overall_status=OverallStatus.OK,
        file_results=[],
        scenario_results=[],
        diff_entries=[],
        top_errors=[],
        totals=totals,
    )


def test_reporting_service_writes_canonical_machine_summary(
    completed_run_result: RunResult,
) -> None:
    destination = write_summary_json(completed_run_result)

    assert destination == completed_run_result.run_paths.summary_json
    assert destination.is_file()
    assert destination.read_bytes().endswith(b"\n")

    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["schema_id"] == "gf-wordbench.run-summary"
    assert document["schema_version"] == "1.0"
    assert document["metadata"]["run_id"] == "20260725_120000"
    assert document["metadata"]["mode"] == "diagnostic"
    assert document["totals"]["overall_status"] == "OK"
    assert document["file_results"] == []
    assert document["scenario_results"] == []


def test_reporting_service_writes_canonical_human_summary(
    completed_run_result: RunResult,
) -> None:
    destination = write_summary_md(completed_run_result)

    assert destination == completed_run_result.run_paths.summary_md
    content = destination.read_text(encoding="utf-8")
    assert content.startswith("# GF Wordbench Audit Summary\n")
    assert "## Run Summary" in content
    assert "## Outcome" in content
    assert "**Overall status: `OK`**" in content
    assert "## Artifacts and Evidence" in content
    assert content.endswith("\n")
    assert "\x00" not in content


def test_reporting_service_is_deterministic_and_does_not_mutate_run_result(
    completed_run_result: RunResult,
) -> None:
    original_lists = (
        tuple(completed_run_result.file_results),
        tuple(completed_run_result.scenario_results),
        tuple(completed_run_result.diff_entries),
        tuple(completed_run_result.top_errors),
    )
    original_status = completed_run_result.overall_status

    summary_path = write_summary_json(completed_run_result)
    first_json = summary_path.read_bytes()
    markdown_path = write_summary_md(completed_run_result)
    first_markdown = markdown_path.read_bytes()

    assert write_summary_json(completed_run_result).read_bytes() == first_json
    assert write_summary_md(completed_run_result).read_bytes() == first_markdown
    assert completed_run_result.overall_status is original_status
    assert (
        tuple(completed_run_result.file_results),
        tuple(completed_run_result.scenario_results),
        tuple(completed_run_result.diff_entries),
        tuple(completed_run_result.top_errors),
    ) == original_lists


def test_reporting_writer_failure_is_explicit_and_independent(
    completed_run_result: RunResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from gf_wordbench.reporting.summary import json_writer

    def fail_write(*args: object, **kwargs: object) -> Path:
        raise OSError("simulated summary persistence failure")

    monkeypatch.setattr(json_writer, "write_json", fail_write)

    with pytest.raises(OSError, match="simulated summary persistence failure"):
        json_writer.write_summary_json(completed_run_result)

    markdown_path = write_summary_md(completed_run_result)
    assert markdown_path.is_file()
    assert not completed_run_result.run_paths.summary_json.exists()


def test_reporting_rejects_inconsistent_terminal_state_without_writing(
    completed_run_result: RunResult,
) -> None:
    completed_run_result.overall_status = OverallStatus.FAIL

    with pytest.raises(ValueError, match="overall_status"):
        write_summary_md(completed_run_result)

    assert not completed_run_result.run_paths.summary_md.exists()


def test_reporting_writes_only_run_owned_summary_paths(
    completed_run_result: RunResult,
) -> None:
    run_dir = completed_run_result.run_paths.run_dir
    before = {path.relative_to(run_dir) for path in run_dir.rglob("*")}

    json_path = write_summary_json(completed_run_result)
    markdown_path = write_summary_md(completed_run_result)

    after = {path.relative_to(run_dir) for path in run_dir.rglob("*")}
    assert after - before == {
        json_path.relative_to(run_dir),
        markdown_path.relative_to(run_dir),
    }
