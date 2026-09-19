from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any, cast
from types import MappingProxyType

import pytest

from gf_wordbench.reporting.schemas.migrations import (
    ARTIFACT_MANIFEST_SCHEMA_ID,
    ARTIFACT_MANIFEST_SCHEMA_VERSION,
    RUN_SUMMARY_SCHEMA_ID,
    RUN_SUMMARY_SCHEMA_VERSION,
    MigrationStatus,
    SummaryShape,
    detect_summary_shape,
    migrate_manifest_document,
    migrate_manifest_v0_to_v1,
    migrate_summary_document,
    migrate_summary_v0_to_v1,
)


def _legacy_flat_summary(*, run_root: Path, project_root: Path) -> dict[str, object]:
    return {
        "run_id": "20260725_120000_demo",
        "run_dir": str(run_root),
        "started_at": "2026-07-25T12:00:00Z",
        "finished_at": "2026-07-25T12:00:01Z",
        "duration_ms": 1000,
        "gf_version": "3.12",
        "mode": "all",
        "project_id": "demo",
        "project_name": "Demo",
        "project_root": str(project_root),
        "rgl_root": str(project_root / "rgl"),
        "gf_executable": str(project_root / "bin" / "gf.exe"),
        "output_root": str(project_root / "_gf_wordbench"),
        "source_directory": str(project_root / "lib" / "src"),
        "source_glob": "**/*.gf",
        "ok": 2,
        "fail": 1,
        "error": 0,
        "skipped": 0,
        "file_results": [],
        "scenario_results": [],
        "diff_entries": [],
        "top_errors": [],
    }


def _current_summary() -> dict[str, object]:
    return {
        "schema_id": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "producer": {"name": "gf-wordbench", "version": "1.0.0"},
        "metadata": {},
        "totals": {},
        "artifacts": {},
        "file_results": [],
        "scenario_results": [],
        "diff_entries": [],
        "top_errors": [],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("document", "expected"),
    (
        (_current_summary(), SummaryShape.CURRENT),
        ({"metadata": {}, "totals": {}, "artifacts": {}}, SummaryShape.NESTED_UNVERSIONED),
        ({"started_at": "2026-07-25T12:00:00Z", "ok": 1}, SummaryShape.FLAT_UNVERSIONED),
        (
            {"schema_id": RUN_SUMMARY_SCHEMA_ID, "schema_version": "2.0"},
            SummaryShape.UNSUPPORTED_VERSIONED,
        ),
        ({"unrelated": True}, SummaryShape.UNKNOWN),
    ),
)
def test_detect_summary_shape(
    document: dict[str, object],
    expected: SummaryShape,
) -> None:
    assert detect_summary_shape(document) is expected


def test_flat_summary_migration_maps_legacy_values_without_mutating_source(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "project").resolve()
    run_root = (tmp_path / "run").resolve()
    project_root.mkdir()
    run_root.mkdir()
    source = _legacy_flat_summary(run_root=run_root, project_root=project_root)
    original = copy.deepcopy(source)

    migration = migrate_summary_document(
        source,
        source_path="legacy-summary.json",
        destination_path="summary.json",
        run_root=run_root,
        project_root=project_root,
        producer_version="1.2.3",
    )

    assert source == original
    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.changed is True
    assert migration.result.written is False
    assert migration.result.losses == ()
    assert migration.document is not None
    assert isinstance(migration.document, MappingProxyType)

    document = migration.document
    assert document["schema_id"] == RUN_SUMMARY_SCHEMA_ID
    assert document["schema_version"] == RUN_SUMMARY_SCHEMA_VERSION
    assert document["producer"] == {"name": "gf-wordbench", "version": "1.2.3"}

    metadata = document["metadata"]
    totals = document["totals"]
    assert isinstance(metadata, dict)
    assert isinstance(totals, dict)
    assert metadata["mode"] == "diagnostic"
    assert metadata["source_directory"] == "lib/src"
    assert totals["files_ok"] == 2
    assert totals["files_fail"] == 1
    assert totals["files_included"] == 3
    assert totals["overall_status"] == "FAIL"


def test_summary_migration_is_idempotent_for_current_documents() -> None:
    source = _current_summary()
    original = copy.deepcopy(source)

    migration = migrate_summary_document(source)

    assert source == original
    assert migration.result.status is MigrationStatus.NOT_NEEDED
    assert migration.result.changed is False
    assert migration.result.warnings == ()
    assert migration.result.losses == ()
    assert migration.document == source
    assert migration.document is not source


def test_strict_summary_migration_blocks_unrecoverable_required_fields() -> None:
    source: dict[str, object] = {"metadata": {}, "totals": {}, "artifacts": {}}

    migration = migrate_summary_document(source, strict=True)

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.result.changed is True
    assert migration.result.losses
    assert migration.document is None

    with pytest.raises(ValueError, match="Mandatory metadata field"):
        migrate_summary_v0_to_v1(source, strict=True)


def test_unsupported_versioned_summary_is_blocked_without_reinterpretation() -> None:
    source = {
        "schema_id": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": "2.0",
        "metadata": {},
    }

    migration = migrate_summary_document(source)

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.result.changed is False
    assert migration.document is None
    assert migration.result.losses == ("unsupported versioned run-summary document",)


def test_manifest_migration_hashes_real_artifacts_and_preserves_source(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    summary_path = run_root / "summary.json"
    log_path = run_root / "raw" / "master.log"
    log_path.parent.mkdir()
    summary_path.write_text('{"ok":true}\n', encoding="utf-8")
    log_path.write_text("line one\nline two\n", encoding="utf-8")

    source = {
        "artifacts": [
            {"path": "summary.json", "role": "machine_summary", "required": True},
            {"path": "raw\\master.log", "role": "master_log", "created_by": "runs"},
        ]
    }
    original = copy.deepcopy(source)

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id="20260725_120000_demo",
        generated_at="2026-07-25T12:00:02Z",
        producer_version="1.2.3",
        strict=True,
    )

    assert source == original
    assert migration.result.status is MigrationStatus.MIGRATED
    assert migration.result.losses == ()
    assert migration.document is not None

    document = migration.document
    assert document["schema_id"] == ARTIFACT_MANIFEST_SCHEMA_ID
    assert document["schema_version"] == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert document["run_id"] == "20260725_120000_demo"
    assert document["generated_at"] == "2026-07-25T12:00:02Z"

    entries = document["artifacts"]
    assert isinstance(entries, list)
    assert all(isinstance(entry, dict) for entry in entries)
    typed_entries = cast(list[dict[str, Any]], entries)
    by_path = {str(entry["path"]): entry for entry in typed_entries}
    assert set(by_path) == {"raw/master.log", "summary.json"}
    assert by_path["summary.json"]["required"] is True
    assert by_path["summary.json"]["sha256"] == _sha256(summary_path)
    assert by_path["raw/master.log"]["sha256"] == _sha256(log_path)
    assert by_path["raw/master.log"]["media_type"] == "text/plain; charset=utf-8"


def test_manifest_migration_blocks_losses_in_strict_mode(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    source = {"artifacts": [{"path": "missing.txt", "required": True}]}

    strict = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id="20260725_120000_demo",
        strict=True,
    )
    permissive = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id="20260725_120000_demo",
        strict=False,
    )

    assert strict.result.status is MigrationStatus.BLOCKED
    assert strict.document is None
    assert strict.result.losses == ("Historical artifact is missing: missing.txt.",)
    assert permissive.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert permissive.document is not None
    assert permissive.document["artifacts"] == []

    with pytest.raises(ValueError, match="Historical artifact is missing"):
        migrate_manifest_v0_to_v1(
            source,
            run_root=run_root,
            run_id="20260725_120000_demo",
            strict=True,
        )


def test_current_manifest_migration_is_idempotent(tmp_path: Path) -> None:
    source = {
        "schema_id": ARTIFACT_MANIFEST_SCHEMA_ID,
        "schema_version": ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "producer": {"name": "gf-wordbench", "version": "1.0.0"},
        "run_id": "20260725_120000_demo",
        "generated_at": "2026-07-25T12:00:02Z",
        "hash_algorithm": "sha256",
        "artifacts": [],
    }
    original = copy.deepcopy(source)

    migration = migrate_manifest_document(
        source,
        run_root=tmp_path.resolve(),
        run_id="ignored-for-current-document",
    )

    assert source == original
    assert migration.result.status is MigrationStatus.NOT_NEEDED
    assert migration.result.changed is False
    assert migration.document == source
    assert migration.document is not source
