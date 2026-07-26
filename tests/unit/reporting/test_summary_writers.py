"""Unit tests for canonical machine and human summary writers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest

from gf_wordbench.infrastructure.filesystem import PathContainmentError
from gf_wordbench.infrastructure.json_io import read_json
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from gf_wordbench.reporting.schemas.summary_v1 import SummaryV1ValidationError
from gf_wordbench.reporting.summary import json_writer
from gf_wordbench.reporting.summary.json_writer import (
    SUMMARY_FILENAME,
    SummaryJsonWriter,
    write_summary_document,
    write_summary_json,
)
from gf_wordbench.reporting.summary.markdown_writer import (
    SUMMARY_MARKDOWN_FILENAME,
    SUMMARY_MARKDOWN_SOFT_SCHEMA_VERSION,
    SummaryMarkdownModelError,
    build_summary_md,
    write_summary_md,
)
from gf_wordbench.reporting.summary.projection import build_summary_document
from gf_wordbench.runs.models.results import RunResult, RunTotals
from gf_wordbench.runs.paths import build_run_paths


_REQUIRED_MARKDOWN_HEADINGS = (
    "# GF Wordbench Audit Summary",
    "## Run Summary",
    "## Outcome",
    "## File Results",
    "## Scenario Results",
    "## Regression Comparison",
    "## Artifacts",
)


@dataclass(frozen=True, slots=True)
class _WriterRunPaths:
    """Expose canonical paths plus the locked writer compatibility names."""

    canonical: object

    def __getattr__(self, name: str) -> object:
        return getattr(self.canonical, name)

    @property
    def summary_json_path(self) -> Path:
        return Path(getattr(self.canonical, "summary_json"))

    @property
    def summary_md_path(self) -> Path:
        return Path(getattr(self.canonical, "summary_md"))


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

    run_paths = _WriterRunPaths(build_run_paths(run_id, run_dir))
    identity = SimpleNamespace(
        id="demo-project",
        name="Démonstration – 日本語",
        language_code="Demo",
    )
    project = SimpleNamespace(
        identity=identity,
        sources=SimpleNamespace(
            directory=Path("lib/src"),
            glob="*.gf",
        ),
        project_root=project_root,
        schema_version="1.0",
    )
    environment = SimpleNamespace(
        project_root=project_root,
        rgl_root=rgl_root,
        gf_executable=gf_executable,
        output_root=output_root,
        gf_path=(project_root / "lib" / "src", rgl_root),
    )
    run_config = SimpleNamespace(
        project=project,
        environment=environment,
        mode=ValidationMode.DIAGNOSTIC,
        target=None,
        timeout_sec=60,
        max_files=0,
        keep_ok_details=False,
        diff_previous=True,
        skip_version_probe=False,
        no_compile=False,
        emit_cpu_stats=False,
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        compatibility_warnings=(),
    )

    started_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
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
        run_paths=run_paths,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=1),
        duration_ms=1_000,
        gf_version="3.12",
        overall_status=OverallStatus.OK,
        file_results=[],
        scenario_results=[],
        diff_entries=[],
        top_errors=[],
        totals=totals,
    )


def test_write_summary_document_round_trips_canonical_document(
    completed_run_result: RunResult,
) -> None:
    destination = completed_run_result.run_paths.summary_json_path
    document = build_summary_document(completed_run_result)
    readonly_document = MappingProxyType(document)

    written = write_summary_document(destination, readonly_document)

    assert written == destination
    assert written.name == SUMMARY_FILENAME
    assert written.read_bytes().endswith(b"\n")
    assert b"D\xc3\xa9monstration" in written.read_bytes()
    assert read_json(written) == document

    decoded = json.loads(written.read_text(encoding="utf-8"))
    assert decoded["schema_id"] == "gf-wordbench.run-summary"
    assert decoded["schema_version"] == "1.0"
    assert decoded["metadata"]["run_id"] == "20260725_120000"
    assert decoded["metadata"]["mode"] == "diagnostic"
    assert decoded["totals"]["overall_status"] == "OK"


def test_write_summary_document_rejects_noncanonical_filename_before_write(
    completed_run_result: RunResult,
) -> None:
    destination = completed_run_result.run_paths.run_dir / "result.json"
    document = build_summary_document(completed_run_result)

    with pytest.raises(ValueError, match=SUMMARY_FILENAME):
        write_summary_document(destination, document)

    assert not destination.exists()


def test_write_summary_document_rejects_invalid_schema_before_write(
    completed_run_result: RunResult,
) -> None:
    destination = completed_run_result.run_paths.summary_json_path
    document = dict(build_summary_document(completed_run_result))
    document["schema_id"] = "not-gf-wordbench"

    with pytest.raises(SummaryV1ValidationError):
        write_summary_document(destination, document)

    assert not destination.exists()


def test_write_summary_document_detects_persisted_semantic_drift(
    completed_run_result: RunResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = completed_run_result.run_paths.summary_json_path
    document = build_summary_document(completed_run_result)
    altered = dict(document)
    altered["metadata"] = dict(document["metadata"])
    altered["metadata"]["project_name"] = "Altered after persistence"

    monkeypatch.setattr(json_writer, "read_json", lambda path: altered)

    with pytest.raises(RuntimeError, match="persisted summary differs"):
        write_summary_document(destination, document)

    assert destination.is_file()


def test_write_summary_json_projects_to_the_run_owned_path(
    completed_run_result: RunResult,
) -> None:
    destination = write_summary_json(completed_run_result)

    assert destination == completed_run_result.run_paths.summary_json_path
    assert read_json(destination) == build_summary_document(completed_run_result)


def test_summary_json_writer_adapter_delegates_write_and_call(
    completed_run_result: RunResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = completed_run_result.run_paths.summary_json_path
    calls: list[RunResult] = []

    def fake_write(run_result: RunResult) -> Path:
        calls.append(run_result)
        return destination

    monkeypatch.setattr(json_writer, "write_summary_json", fake_write)
    writer = SummaryJsonWriter()

    assert writer.write(completed_run_result) == destination
    assert writer(completed_run_result) == destination
    assert calls == [completed_run_result, completed_run_result]


@pytest.mark.parametrize(
    "run_result",
    [
        SimpleNamespace(),
        SimpleNamespace(run_paths=SimpleNamespace()),
        SimpleNamespace(
            run_paths=SimpleNamespace(summary_json_path=Path("other.json"))
        ),
    ],
)
def test_write_summary_json_requires_the_canonical_writer_path(
    run_result: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        write_summary_json(run_result)


def test_build_summary_md_emits_required_soft_schema_in_order(
    completed_run_result: RunResult,
) -> None:
    content = build_summary_md(completed_run_result)

    positions = [content.index(heading) for heading in _REQUIRED_MARKDOWN_HEADINGS]
    assert positions == sorted(positions)
    assert content.startswith("# GF Wordbench Audit Summary\n")
    assert f"`{SUMMARY_MARKDOWN_SOFT_SCHEMA_VERSION}`" in content
    assert "**Overall status: `OK`**" in content
    assert "None." in content
    assert content.endswith("\n")
    assert not content.endswith("\n\n")


def test_build_summary_md_is_deterministic_and_read_only(
    completed_run_result: RunResult,
) -> None:
    before = (
        completed_run_result.overall_status,
        tuple(completed_run_result.file_results),
        tuple(completed_run_result.scenario_results),
        tuple(completed_run_result.diff_entries),
        tuple(completed_run_result.top_errors),
        completed_run_result.run_config.compatibility_warnings,
    )

    first = build_summary_md(completed_run_result)
    second = build_summary_md(completed_run_result)

    assert second == first
    assert (
        completed_run_result.overall_status,
        tuple(completed_run_result.file_results),
        tuple(completed_run_result.scenario_results),
        tuple(completed_run_result.diff_entries),
        tuple(completed_run_result.top_errors),
        completed_run_result.run_config.compatibility_warnings,
    ) == before


def test_build_summary_md_sanitizes_untrusted_warning_text(
    completed_run_result: RunResult,
) -> None:
    completed_run_result.run_config.compatibility_warnings = (
        "\x1b[31munsafe|<tag>\x00\nignored second line",
    )

    content = build_summary_md(completed_run_result)

    assert "## Warnings" in content
    assert "unsafe\\|&lt;tag&gt;" in content
    assert "ignored second line" not in content
    assert "\x1b" not in content
    assert "\x00" not in content
    assert "<tag>" not in content


def test_write_summary_md_writes_utf8_lf_and_returns_owned_path(
    completed_run_result: RunResult,
) -> None:
    destination = write_summary_md(completed_run_result)

    assert destination == completed_run_result.run_paths.summary_md_path
    assert destination.name == SUMMARY_MARKDOWN_FILENAME
    payload = destination.read_bytes()
    assert b"\r\n" not in payload
    assert payload.endswith(b"\n")
    assert "Démonstration – 日本語" in payload.decode("utf-8")


def test_write_summary_md_replaces_an_existing_report_atomically(
    completed_run_result: RunResult,
) -> None:
    destination = completed_run_result.run_paths.summary_md_path
    destination.write_text("obsolete\n", encoding="utf-8")

    written = write_summary_md(completed_run_result)

    assert written == destination
    assert destination.read_text(encoding="utf-8").startswith(
        "# GF Wordbench Audit Summary\n"
    )
    assert not any(destination.parent.glob(f".{destination.name}.*.tmp"))


def test_build_failure_preserves_an_existing_markdown_report(
    completed_run_result: RunResult,
) -> None:
    destination = completed_run_result.run_paths.summary_md_path
    destination.write_text("previous valid report\n", encoding="utf-8")
    completed_run_result.overall_status = OverallStatus.FAIL

    with pytest.raises(SummaryMarkdownModelError, match="overall_status"):
        write_summary_md(completed_run_result)

    assert destination.read_text(encoding="utf-8") == "previous valid report\n"


def test_write_summary_md_rejects_a_destination_outside_the_run_directory(
    completed_run_result: RunResult,
    tmp_path: Path,
) -> None:
    canonical = completed_run_result.run_paths.canonical
    outside = tmp_path / SUMMARY_MARKDOWN_FILENAME
    completed_run_result.run_paths = SimpleNamespace(
        run_id=canonical.run_id,
        run_dir=canonical.run_dir,
        summary_json=canonical.summary_json,
        summary_md=outside,
        ai_ready_md=canonical.ai_ready_md,
        top_errors_txt=canonical.top_errors_txt,
        manifest_json=canonical.manifest_json,
        details_dir=canonical.details_dir,
        raw_dir=canonical.raw_dir,
        master_log=canonical.master_log,
        all_scan_logs=canonical.all_scan_logs,
        all_logs=canonical.all_logs,
        raw_compile_dir=canonical.raw_compile_dir,
        raw_scan_dir=canonical.raw_scan_dir,
        raw_scenarios_dir=canonical.raw_scenarios_dir,
        artifacts_dir=canonical.artifacts_dir,
        gfo_dir=canonical.gfo_dir,
        out_dir=canonical.out_dir,
        pgf_dir=canonical.pgf_dir,
    )

    with pytest.raises(PathContainmentError):
        write_summary_md(completed_run_result)

    assert not outside.exists()
