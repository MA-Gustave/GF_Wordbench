"""Contract tests for read-only artifact-manifest migrations."""

from __future__ import annotations

import copy
import hashlib
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from gf_wordbench.reporting.schemas.migrations import (
    ARTIFACT_MANIFEST_SCHEMA_ID,
    ARTIFACT_MANIFEST_SCHEMA_VERSION,
    MANIFEST_MIGRATION_ID,
    MigrationStatus,
    migrate_artifact_manifest,
    migrate_manifest_document,
    migrate_manifest_v0_to_v1,
)

_RUN_ID = "20260725_190423"
_TIMESTAMP = "2026-07-25T19:04:23Z"


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entry(document: Any, path: str) -> dict[str, Any]:
    artifacts = document["artifacts"]
    assert isinstance(artifacts, list)
    return next(item for item in artifacts if item["path"] == path)


def _current_manifest() -> dict[str, object]:
    return {
        "schema_id": ARTIFACT_MANIFEST_SCHEMA_ID,
        "schema_version": ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "producer": {"name": "gf-wordbench", "version": "1.0.0"},
        "run_id": _RUN_ID,
        "generated_at": _TIMESTAMP,
        "hash_algorithm": "sha256",
        "artifacts": [],
    }


def test_current_manifest_is_returned_as_not_needed_without_mutation(
    tmp_path: Path,
) -> None:
    source = _current_manifest()
    original = copy.deepcopy(source)

    migration = migrate_manifest_document(
        source,
        run_root=tmp_path.resolve(),
        run_id="ignored-for-current-document",
        source_path="legacy/manifest.json",
        destination_path="manifest.json",
    )

    assert source == original
    assert migration.result.migration_id == MANIFEST_MIGRATION_ID
    assert migration.result.source_schema == ARTIFACT_MANIFEST_SCHEMA_ID
    assert migration.result.source_version == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert migration.result.target_schema == ARTIFACT_MANIFEST_SCHEMA_ID
    assert migration.result.target_version == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert migration.result.source_path == "legacy/manifest.json"
    assert migration.result.destination_path == "manifest.json"
    assert migration.result.status is MigrationStatus.NOT_NEEDED
    assert migration.result.warnings == ()
    assert migration.result.losses == ()
    assert migration.result.changed is False
    assert migration.result.written is False
    assert migration.result.backup_path is None
    assert migration.document == source
    assert migration.document is not source
    assert isinstance(migration.document, MappingProxyType)


def test_same_major_future_minor_is_treated_as_current(tmp_path: Path) -> None:
    source = _current_manifest()
    source["schema_version"] = "1.9"

    migration = migrate_manifest_document(
        source,
        run_root=tmp_path.resolve(),
        run_id="ignored",
    )

    assert migration.result.status is MigrationStatus.NOT_NEEDED
    assert migration.result.source_version == "1.9"
    assert migration.document == source


def test_manifest_migration_hashes_actual_bytes_and_preserves_legacy_metadata(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    summary = _write(run_root / "summary.json", b'{"status":"OK"}\n')
    log = _write(run_root / "raw" / "master.log", "résultat\n".encode())
    source = {
        "schema_id": "gf-audit.manifest",
        "schema_version": "0",
        "artifacts": [
            {
                "path": "summary.json",
                "role": "machine_summary",
                "required": True,
                "created_by": "reporting_json",
                "size_bytes": 1,
                "sha256": "0" * 64,
            },
            {
                "path": r"raw\master.log",
                "role": "master_log",
                "created_by": "runs",
            },
        ],
    }
    original = copy.deepcopy(source)

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id=_RUN_ID,
        source_path="legacy-manifest.json",
        destination_path="manifest.json",
        generated_at=_TIMESTAMP,
        producer_version="1.4.2",
        strict=True,
    )

    assert source == original
    assert migration.result.status is MigrationStatus.MIGRATED
    assert migration.result.changed is True
    assert migration.result.written is False
    assert migration.result.warnings == ()
    assert migration.result.losses == ()
    assert migration.document is not None
    assert isinstance(migration.document, MappingProxyType)

    document = migration.document
    assert document["schema_id"] == ARTIFACT_MANIFEST_SCHEMA_ID
    assert document["schema_version"] == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert document["producer"] == {"name": "gf-wordbench", "version": "1.4.2"}
    assert document["run_id"] == _RUN_ID
    assert document["generated_at"] == _TIMESTAMP
    assert document["hash_algorithm"] == "sha256"
    assert [item["path"] for item in document["artifacts"]] == [
        "raw/master.log",
        "summary.json",
    ]

    summary_entry = _entry(document, "summary.json")
    assert summary_entry == {
        "path": "summary.json",
        "role": "machine_summary",
        "media_type": "application/json",
        "required": True,
        "size_bytes": summary.stat().st_size,
        "sha256": _sha256(summary),
        "created_by": "reporting_json",
    }

    log_entry = _entry(document, "raw/master.log")
    assert log_entry == {
        "path": "raw/master.log",
        "role": "master_log",
        "media_type": "text/plain; charset=utf-8",
        "required": False,
        "size_bytes": log.stat().st_size,
        "sha256": _sha256(log),
        "created_by": "runs",
    }


def test_explicit_inventory_and_metadata_maps_build_manifest_without_legacy_document(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    summary = _write(run_root / "summary.md", b"# Summary\n")
    pgf = _write(run_root / "artifacts" / "pgf" / "Demo.pgf", b"PGF\x00data")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=("artifacts/pgf/Demo.pgf", "summary.md"),
        required_paths=("summary.md", r"artifacts\pgf\Demo.pgf"),
        role_by_path={
            "summary.md": "human_summary",
            "artifacts/pgf/Demo.pgf": "pgf",
        },
        created_by_by_path={
            "summary.md": "reporting_markdown",
            "artifacts/pgf/Demo.pgf": "validation_pgf",
        },
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.MIGRATED
    assert migration.document is not None

    summary_entry = _entry(migration.document, "summary.md")
    assert summary_entry["role"] == "human_summary"
    assert summary_entry["media_type"] == "text/markdown; charset=utf-8"
    assert summary_entry["required"] is True
    assert summary_entry["created_by"] == "reporting_markdown"
    assert summary_entry["sha256"] == _sha256(summary)

    pgf_entry = _entry(migration.document, "artifacts/pgf/Demo.pgf")
    assert pgf_entry["role"] == "pgf"
    assert pgf_entry["media_type"] == "application/octet-stream"
    assert pgf_entry["required"] is True
    assert pgf_entry["created_by"] == "validation_pgf"
    assert pgf_entry["sha256"] == _sha256(pgf)


def test_explicit_maps_override_legacy_role_and_creator(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "summary.md", b"# Summary\n")
    source = {
        "artifacts": [
            {
                "path": "summary.md",
                "role": "other",
                "created_by": "migration",
            }
        ]
    }

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id=_RUN_ID,
        role_by_path={"summary.md": "human_summary"},
        created_by_by_path={"summary.md": "reporting_markdown"},
        generated_at=_TIMESTAMP,
    )

    assert migration.document is not None
    entry = _entry(migration.document, "summary.md")
    assert entry["role"] == "human_summary"
    assert entry["created_by"] == "reporting_markdown"


def test_legacy_required_flag_overrides_required_paths(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "summary.json", b"{}\n")
    source = {
        "artifacts": [
            {
                "path": "summary.json",
                "required": False,
            }
        ]
    }

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id=_RUN_ID,
        required_paths=("summary.json",),
        generated_at=_TIMESTAMP,
    )

    assert migration.document is not None
    assert _entry(migration.document, "summary.json")["required"] is False


def test_legacy_artifact_mapping_is_converted_and_sorted(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "z.txt", b"z")
    _write(run_root / "a.txt", b"a")
    source = {
        "files": {
            "z.txt": {"role": "other"},
            "a.txt": {"role": "other"},
        }
    }

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id=_RUN_ID,
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.losses == ()
    assert migration.result.warnings == (
        "Converted legacy manifest artifact mapping to an ordered path list.",
    )
    assert migration.document is not None
    assert [item["path"] for item in migration.document["artifacts"]] == [
        "a.txt",
        "z.txt",
    ]


@pytest.mark.parametrize(
    ("path", "expected_role", "expected_media_type"),
    (
        ("summary.json", "machine_summary", "application/json"),
        ("summary.md", "human_summary", "text/markdown; charset=utf-8"),
        ("AI_READY.md", "ai_handoff", "text/markdown; charset=utf-8"),
        ("top_errors.txt", "top_errors", "text/plain; charset=utf-8"),
        ("raw/master.log", "master_log", "text/plain; charset=utf-8"),
        ("raw/ALL_LOGS.TXT", "aggregate_log", "text/plain; charset=utf-8"),
        ("raw/file.scan.txt", "scan_log", "text/plain; charset=utf-8"),
        ("raw/compile/Main.stdout.txt", "compile_stdout", "text/plain; charset=utf-8"),
        ("raw/compile/Main.stderr.txt", "compile_stderr", "text/plain; charset=utf-8"),
        (
            "raw/scenarios/demo.stdout.txt",
            "scenario_stdout",
            "text/plain; charset=utf-8",
        ),
        (
            "raw/scenarios/demo.stderr.txt",
            "scenario_stderr",
            "text/plain; charset=utf-8",
        ),
        ("raw/scenarios/demo.out", "scenario_output", "text/plain; charset=utf-8"),
        ("details/result.json", "detail", "application/json"),
        ("artifacts/gfo/Main.gfo", "gfo", "application/octet-stream"),
        ("artifacts/pgf/Demo.pgf", "pgf", "application/octet-stream"),
        ("artifact.bin", "other", "application/octet-stream"),
    ),
)
def test_role_and_media_type_are_inferred_from_canonical_paths(
    tmp_path: Path,
    path: str,
    expected_role: str,
    expected_media_type: str,
) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / Path(path), b"content")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=(path,),
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.MIGRATED
    assert migration.document is not None
    entry = _entry(migration.document, path)
    assert entry["role"] == expected_role
    assert entry["media_type"] == expected_media_type
    assert entry["created_by"] == "migration"


def test_unknown_legacy_role_is_mapped_to_other_with_warning(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "artifact.bin", b"payload")
    source = {
        "artifacts": [
            {
                "path": "artifact.bin",
                "role": "legacy_unknown_role",
            }
        ]
    }

    migration = migrate_manifest_document(
        source,
        run_root=run_root,
        run_id=_RUN_ID,
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.warnings == (
        "Unknown legacy role for 'artifact.bin' was mapped to 'other'.",
    )
    assert migration.document is not None
    assert _entry(migration.document, "artifact.bin")["role"] == "other"


def test_absolute_path_inside_run_root_is_relativized(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    artifact = _write(run_root / "raw" / "stdout.txt", b"ok\n")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=(str(artifact),),
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.warnings == (
        "Converted absolute artifact path to a run-relative path.",
    )
    assert migration.result.losses == ()
    assert migration.document is not None
    assert migration.document["artifacts"][0]["path"] == "raw/stdout.txt"


def test_absolute_path_outside_run_root_blocks_strict_migration(tmp_path: Path) -> None:
    run_root = (tmp_path / "run").resolve()
    run_root.mkdir()
    outside = _write(tmp_path / "outside.txt", b"outside")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=(str(outside),),
        generated_at=_TIMESTAMP,
        strict=True,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.document is None
    assert migration.result.losses == (
        f"Absolute artifact path is outside run_root: {str(outside)!r}.",
    )


@pytest.mark.parametrize(
    ("artifact_paths", "expected_loss"),
    (
        (("manifest.json",), "The manifest cannot contain itself as an artifact entry."),
        (("missing.txt",), "Historical artifact is missing: missing.txt."),
        (("../outside.txt",), "Invalid portable relative artifact path: '../outside.txt'."),
        (("summary.json", "summary.json"), "Duplicate artifact path after normalization"),
    ),
)
def test_strict_migration_blocks_each_integrity_loss(
    tmp_path: Path,
    artifact_paths: tuple[str, ...],
    expected_loss: str,
) -> None:
    run_root = tmp_path.resolve()
    if "summary.json" in artifact_paths:
        _write(run_root / "summary.json", b"{}\n")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=artifact_paths,
        generated_at=_TIMESTAMP,
        strict=True,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.result.changed is True
    assert migration.document is None
    assert any(expected_loss in loss for loss in migration.result.losses)


def test_permissive_migration_records_losses_and_keeps_recoverable_entries(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    summary = _write(run_root / "summary.json", b"{}\n")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=("missing.txt", "summary.json", "manifest.json"),
        generated_at=_TIMESTAMP,
        strict=False,
    )

    assert migration.result.status is MigrationStatus.MIGRATED_WITH_WARNINGS
    assert migration.result.losses == (
        "Historical artifact is missing: missing.txt.",
        "The manifest cannot contain itself as an artifact entry.",
    )
    assert migration.document is not None
    assert [item["path"] for item in migration.document["artifacts"]] == [
        "summary.json"
    ]
    assert _entry(migration.document, "summary.json")["sha256"] == _sha256(summary)


def test_directory_artifact_is_rejected(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    (run_root / "details").mkdir()

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=("details",),
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.document is None
    assert migration.result.losses == (
        "Manifest migration accepts regular non-symlink files only: details.",
    )


def test_symlink_artifact_is_rejected_when_supported(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    target = _write(run_root / "target.txt", b"target")
    link = run_root / "link.txt"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("Symlink creation is unavailable in this environment.")

    migration = migrate_manifest_document(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=("link.txt",),
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.document is None
    assert migration.result.losses == (
        "Manifest migration accepts regular non-symlink files only: link.txt.",
    )


def test_missing_inventory_blocks_strict_migration(tmp_path: Path) -> None:
    migration = migrate_manifest_document(
        {"files": None},
        run_root=tmp_path.resolve(),
        run_id=_RUN_ID,
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.document is None
    assert migration.result.losses == (
        "No recoverable artifact path inventory was supplied for manifest migration.",
    )


def test_malformed_legacy_inventory_item_is_lossy(tmp_path: Path) -> None:
    source = {"artifacts": [{"role": "other"}]}

    migration = migrate_manifest_document(
        source,
        run_root=tmp_path.resolve(),
        run_id=_RUN_ID,
        generated_at=_TIMESTAMP,
    )

    assert migration.result.status is MigrationStatus.BLOCKED
    assert migration.document is None
    assert migration.result.losses == (
        "Legacy manifest contains an artifact without a usable path.",
    )


def test_generated_at_is_canonicalized_to_utc_seconds(tmp_path: Path) -> None:
    generated_at = datetime(
        2026,
        7,
        25,
        15,
        4,
        23,
        987654,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    migration = migrate_manifest_document(
        None,
        run_root=tmp_path.resolve(),
        run_id=_RUN_ID,
        artifact_paths=(),
        generated_at=generated_at,
    )

    assert migration.result.status is MigrationStatus.MIGRATED
    assert migration.document is not None
    assert migration.document["generated_at"] == _TIMESTAMP


def test_utc_datetime_is_accepted(tmp_path: Path) -> None:
    migration = migrate_manifest_document(
        None,
        run_root=tmp_path.resolve(),
        run_id=_RUN_ID,
        artifact_paths=(),
        generated_at=datetime(2026, 7, 25, 19, 4, 23, tzinfo=UTC),
    )

    assert migration.document is not None
    assert migration.document["generated_at"] == _TIMESTAMP


@pytest.mark.parametrize(
    "generated_at",
    (
        datetime(2026, 7, 25, 19, 4, 23),
        "not-a-timestamp",
        123,
    ),
)
def test_invalid_generated_at_is_rejected(
    tmp_path: Path,
    generated_at: object,
) -> None:
    expected = (TypeError, ValueError)
    with pytest.raises(expected):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
            generated_at=generated_at,
        )


@pytest.mark.parametrize("strict", (None, 0, 1, "true"))
def test_strict_must_be_a_real_bool(tmp_path: Path, strict: object) -> None:
    with pytest.raises(TypeError, match="strict must be a bool"):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
            strict=strict,  # type: ignore[arg-type]
        )


def test_run_root_must_be_an_existing_absolute_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run_root must be absolute"):
        migrate_manifest_document(
            None,
            run_root=Path("relative-run"),
            run_id=_RUN_ID,
            artifact_paths=(),
        )

    with pytest.raises(ValueError, match="run_root must identify an existing directory"):
        migrate_manifest_document(
            None,
            run_root=(tmp_path / "missing").resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
        )

    file_root = _write(tmp_path / "file-root", b"not a directory").resolve()
    with pytest.raises(ValueError, match="run_root must identify an existing directory"):
        migrate_manifest_document(
            None,
            run_root=file_root,
            run_id=_RUN_ID,
            artifact_paths=(),
        )


@pytest.mark.parametrize("run_id", ("", "   ", "bad\x00id", 123))
def test_run_id_must_be_nonempty_text_without_nul(
    tmp_path: Path,
    run_id: object,
) -> None:
    with pytest.raises(ValueError, match="run_id must be a non-empty string"):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=run_id,  # type: ignore[arg-type]
            artifact_paths=(),
        )


def test_artifact_paths_rejects_scalar_text(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="artifact_paths must be an iterable of paths"):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths="summary.json",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "invalid_map",
    (
        {"summary.md": ""},
        {1: "human_summary"},
        {"summary.md": 1},
    ),
)
def test_metadata_maps_require_nonempty_path_and_text_strings(
    tmp_path: Path,
    invalid_map: dict[Any, Any],
) -> None:
    with pytest.raises(TypeError, match="must map non-empty path strings"):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
            role_by_path=invalid_map,
        )


def test_document_must_be_a_mapping_or_none(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="document must be a mapping"):
        migrate_manifest_document(
            [],  # type: ignore[arg-type]
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
        )


def test_document_values_must_be_json_compatible(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="contains a non-JSON value"):
        migrate_manifest_document(
            {"artifacts": [], "invalid": object()},
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
        )


def test_producer_version_must_be_nonempty_text(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="producer_version must be a non-empty string"):
        migrate_manifest_document(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=(),
            producer_version=" ",
        )


def test_wrapper_returns_migrated_document(tmp_path: Path) -> None:
    run_root = tmp_path.resolve()
    artifact = _write(run_root / "summary.json", b"{}\n")

    document = migrate_manifest_v0_to_v1(
        None,
        run_root=run_root,
        run_id=_RUN_ID,
        artifact_paths=("summary.json",),
        generated_at=_TIMESTAMP,
    )

    assert isinstance(document, MappingProxyType)
    assert document["run_id"] == _RUN_ID
    assert _entry(document, "summary.json")["sha256"] == _sha256(artifact)


def test_wrapper_raises_with_recorded_losses_when_migration_is_blocked(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Historical artifact is missing: missing.txt"):
        migrate_manifest_v0_to_v1(
            None,
            run_root=tmp_path.resolve(),
            run_id=_RUN_ID,
            artifact_paths=("missing.txt",),
            generated_at=_TIMESTAMP,
            strict=True,
        )


def test_public_manifest_alias_points_to_canonical_migrator() -> None:
    assert migrate_artifact_manifest is migrate_manifest_document
