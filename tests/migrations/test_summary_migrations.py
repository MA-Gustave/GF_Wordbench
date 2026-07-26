"""Contract tests for read-only run-summary migrations."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from gf_wordbench.reporting.schemas.migrations import (
    RUN_SUMMARY_SCHEMA_ID,
    RUN_SUMMARY_SCHEMA_VERSION,
    SUMMARY_MIGRATION_ID,
    MigrationStatus,
    SummaryShape,
    detect_summary_shape,
    migrate_run_summary,
    migrate_summary_document,
    migrate_summary_v0_to_v1,
)
from gf_wordbench.reporting.schemas.summary_v1 import validate_summary_v1


def _legacy_flat_summary(
    *,
    run_root: Path,
    project_root: Path,
    mode: str = "file",
    include_scenarios: bool = True,
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "run_id": "20260725_120000",
        "run_dir": str(run_root),
        "started_at": "2026-07-25T12:00:00+00:00",
        "finished_at": "2026-07-25T12:00:01Z",
        "duration_ms": 1_000,
        "gf_version": "3.12",
        "mode": mode,
        "target_file": str(project_root / "src" / "Main.gf"),
        "project_id": "demo",
        "project_name": "Demo Grammar",
        "project_root": str(project_root),
        "rgl_root": str(project_root.parent / "rgl"),
        "gf_executable": str(project_root.parent / "bin" / "gf.exe"),
        "output_root": str(run_root.parent),
        "source_directory": str(project_root / "src"),
        "source_glob": "*.gf",
        "gf_path": [
            str(project_root.parent / "rgl"),
            str(project_root.parent / "rgl"),
        ],
        "timeout_sec": 60,
        "max_files": 25,
        "skip_version_probe": False,
        "no_compile": False,
        "emit_cpu_stats": False,
        "keep_ok_details": False,
        "diff_previous": True,
        "ok": 0,
        "fail": 0,
        "error": 0,
        "skipped": 0,
        "overall_status": "OK",
        "ai_brief_path": str(run_root / "AI_READY.md"),
        "summary_md_path": str(run_root / "summary.md"),
        "file_results": [],
        "diff_entries": [],
        "top_errors": {
            "Type mismatch": 3,
            "Unknown constructor": 1,
        },
    }
    if include_scenarios:
        document["scenario_results"] = []
    return document


@pytest.fixture
def migration_roots(tmp_path: Path) -> tuple[Path, Path]:
    project_root = (tmp_path / "project").resolve()
    run_root = (tmp_path / "runs" / "run_20260725_120000").resolve()
    (project_root / "src").mkdir(parents=True)
    run_root.mkdir(parents=True)
    return run_root, project_root


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        (
            {
                "schema_id": RUN_SUMMARY_SCHEMA_ID,
                "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
            },
            SummaryShape.CURRENT,
        ),
        ({"metadata": {}, "totals": {}, "artifacts": {}}, SummaryShape.NESTED_UNVERSIONED),
        ({"run_config": {}, "file_results": []}, SummaryShape.FLAT_UNVERSIONED),
        (
            {
                "schema_id": RUN_SUMMARY_SCHEMA_ID,
                "schema_version": "2.0",
            },
            SummaryShape.UNSUPPORTED_VERSIONED,
        ),
        ({"unrelated": True}, SummaryShape.UNKNOWN),
    ],
)
def test_detect_summary_shape(document: dict[str, object], expected: SummaryShape) -> None:
    assert detect_summary_shape(document) is expected


def test_detect_summary_shape_requires_a_mapping() -> None:
    with pytest.raises(TypeError, match="document must be a mapping"):
        detect_summary_shape([])  # type: ignore[arg-type]


def test_flat_summary_migration_emits_valid_canonical_v1(
    migration_roots: tuple[Path, Path],
) -> None:
    run_root, project_root = migration_roots
    legacy = _legacy_flat_summary(run_root=run_root, project_root=project_root)
    original = deepcopy(legacy)

    migration = migrate_summary_document(
        legacy,
        source_path="legacy/summary.json",
        destination_path="runs/run_20260725_120000/summary.json",
        run_root=run_root,
        project_root=project_root,
        producer_version="1.4.2",
    )

    assert legacy == original
    assert migration.result.migration_id == SUMMARY_MIGRATION_ID
    assert migration.result.source_schema == "gf-audit.run-summary"
    assert migration.result.source_version == "0"
    assert migration.result.target_schema == RUN_SUMMARY_SCHEMA_ID
    assert migration.result.target_version == RUN_SUMMARY_SCHEMA_VERSION
    assert migration.result.source_path == "legacy/summary.json"
    assert migration.result.destination_path == "runs/run_20260725_120000/summary.json"
    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.changed is True
    assert migration.result.written is False
    assert migration.result.backup_path is None
    assert migration.result.losses == ()

    document = migration.document
    assert isinstance(document, MappingProxyType)
    assert document is not None
    assert validate_summary_v1(document) == ()
    assert document["schema_id"] == RUN_SUMMARY_SCHEMA_ID
    assert document["schema_version"] == RUN_SUMMARY_SCHEMA_VERSION
    assert document["producer"] == {"name": "gf-wordbench", "version": "1.4.2"}

    metadata = document["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["mode"] == "quick"
    assert metadata["target_file"] == "src/Main.gf"
    assert metadata["source_directory"] == "src"
    assert metadata["gf_path"] == [str(project_root.parent / "rgl").replace("\\", "/")]

    totals = document["totals"]
    assert isinstance(totals, dict)
    assert totals["files_ok"] == 0
    assert totals["files_fail"] == 0
    assert totals["overall_status"] == "OK"

    artifacts = document["artifacts"]
    assert isinstance(artifacts, dict)
    assert artifacts["ai_ready"] == "AI_READY.md"
    assert artifacts["summary_markdown"] == "summary.md"
    assert artifacts["summary_json"] == "summary.json"

    assert document["scenario_results"] == []
    assert document["top_errors"] == [
        {"error_kind": "OTHER", "message": "Type mismatch", "count": 3},
        {"error_kind": "OTHER", "message": "Unknown constructor", "count": 1},
    ]
    assert any("Mapped legacy mode 'file' to 'quick'" in item for item in migration.result.warnings)
    assert any("Normalized legacy top-error mapping" in item for item in migration.result.warnings)


def test_nested_summary_maps_all_mode_to_diagnostic(
    migration_roots: tuple[Path, Path],
) -> None:
    run_root, project_root = migration_roots
    flat = _legacy_flat_summary(
        run_root=run_root,
        project_root=project_root,
        mode="all",
    )
    metadata_keys = {
        "run_id",
        "run_dir",
        "started_at",
        "finished_at",
        "duration_ms",
        "gf_version",
        "mode",
        "target_file",
        "project_id",
        "project_name",
        "project_root",
        "rgl_root",
        "gf_executable",
        "output_root",
        "source_directory",
        "source_glob",
        "gf_path",
        "timeout_sec",
        "max_files",
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
        "keep_ok_details",
        "diff_previous",
    }
    nested = {
        "metadata": {key: flat[key] for key in metadata_keys},
        "totals": {
            "ok": flat["ok"],
            "fail": flat["fail"],
            "error": flat["error"],
            "skipped": flat["skipped"],
            "overall_status": flat["overall_status"],
        },
        "artifacts": {
            "ai_brief_path": flat["ai_brief_path"],
            "summary_md_path": flat["summary_md_path"],
        },
        "file_results": [],
        "scenario_results": [],
        "diff_entries": [],
        "top_errors": [],
    }

    migration = migrate_run_summary(
        nested,
        run_root=run_root,
        project_root=project_root,
        producer_version="1.4.2",
    )

    assert migration.result.source_schema == "unversioned.run-summary"
    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.document is not None
    assert migration.document["metadata"]["mode"] == "diagnostic"  # type: ignore[index]
    assert validate_summary_v1(migration.document) == ()


def test_pre_scenario_summary_records_historical_limitation(
    migration_roots: tuple[Path, Path],
) -> None:
    run_root, project_root = migration_roots
    legacy = _legacy_flat_summary(
        run_root=run_root,
        project_root=project_root,
        include_scenarios=False,
    )

    migration = migrate_summary_document(
        legacy,
        run_root=run_root,
        project_root=project_root,
        strict=False,
    )

    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.document is not None
    assert migration.document["scenario_results"] == []
    assert "Historical run contains no scenario evidence." in migration.result.losses
    assert any(
        "predates scenario results" in warning
        for warning in migration.result.warnings
    )


def test_strict_migration_blocks_lossy_pre_scenario_summary(
    migration_roots: tuple[Path, Path],
) -> None:
    run_root, project_root = migration_roots
    legacy = _legacy_flat_summary(
        run_root=run_root,
        project_root=project_root,
        include_scenarios=False,
    )

    migration = migrate_summary_document(
        legacy,
        run_root=run_root,
        project_root=project_root,
        strict=True,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.result.changed is True
    assert migration.document is None
    assert "Historical run contains no scenario evidence." in migration.result.losses


def test_current_summary_is_returned_as_not_needed(
    migration_roots: tuple[Path, Path],
) -> None:
    run_root, project_root = migration_roots
    canonical = migrate_summary_v0_to_v1(
        _legacy_flat_summary(run_root=run_root, project_root=project_root),
        run_root=run_root,
        project_root=project_root,
        producer_version="1.4.2",
    )

    second = migrate_summary_document(
        canonical,
        source_path="runs/run_20260725_120000/summary.json",
        run_root=run_root,
        project_root=project_root,
    )

    assert second.result.status is MigrationStatus.NOT_NEEDED
    assert second.result.changed is False
    assert second.result.warnings == ()
    assert second.result.losses == ()
    assert second.document == canonical
    assert isinstance(second.document, MappingProxyType)

    with pytest.raises(TypeError):
        second.document["schema_version"] = "9.9"  # type: ignore[index]


@pytest.mark.parametrize(
    ("document", "loss"),
    [
        (
            {
                "schema_id": RUN_SUMMARY_SCHEMA_ID,
                "schema_version": "2.0",
            },
            "unsupported versioned run-summary document",
        ),
        ({"unexpected": "shape"}, "unrecognized legacy run-summary shape"),
    ],
)
def test_unsupported_or_unknown_summaries_are_blocked(
    document: dict[str, object],
    loss: str,
) -> None:
    migration = migrate_summary_document(document)

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.result.changed is False
    assert migration.result.losses == (loss,)
    assert migration.document is None


def test_convenience_wrapper_raises_when_migration_is_blocked() -> None:
    with pytest.raises(ValueError, match="unsupported versioned run-summary document"):
        migrate_summary_v0_to_v1(
            {
                "schema_id": RUN_SUMMARY_SCHEMA_ID,
                "schema_version": "2.0",
            }
        )


def test_migration_is_read_only_even_when_destination_is_declared(
    migration_roots: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    run_root, project_root = migration_roots
    destination = tmp_path / "published" / "summary.json"
    backup = tmp_path / "published" / "summary.json.bak"

    migration = migrate_summary_document(
        _legacy_flat_summary(run_root=run_root, project_root=project_root),
        source_path="legacy/summary.json",
        destination_path=destination.as_posix(),
        run_root=run_root,
        project_root=project_root,
    )

    assert migration.document is not None
    assert migration.result.written is False
    assert migration.result.backup_path is None
    assert not destination.exists()
    assert not backup.exists()
