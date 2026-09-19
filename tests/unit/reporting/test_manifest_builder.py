"""Unit tests for canonical artifact-manifest construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

import gf_wordbench.reporting.manifest.builder as builder_module
from gf_wordbench.reporting.manifest.builder import (
    MANIFEST_FILENAME,
    MANIFEST_HASH_ALGORITHM,
    MANIFEST_PRODUCER_NAME,
    MANIFEST_SCHEMA_ID,
    MANIFEST_SCHEMA_VERSION,
    ArtifactMutationError,
    DuplicateManifestPathError,
    ManifestBuildError,
    ManifestBuildPolicy,
    MissingRequiredArtifactError,
    UnsafeManifestPathError,
    build_manifest,
    build_manifest_from_result,
    build_manifest_result,
    canonical_manifest_path,
    manifest_path_comparison_key,
)
from gf_wordbench.reporting.manifest.declarations import (
    APPLICATION_JSON,
    TEXT_MARKDOWN_UTF8,
    TEXT_PLAIN_UTF8,
    ArtifactDeclaration,
    ArtifactProducer,
    ArtifactRole,
    artifact_declaration,
)
from gf_wordbench.reporting.manifest.hashing import (
    DEFAULT_HASH_CHUNK_SIZE_BYTES,
    DEFAULT_MUTATION_RETRIES,
    FileHash,
    FileIdentity,
    hash_file,
)


@dataclass(frozen=True, slots=True)
class _RunPaths:
    run_id: str
    run_dir: Path
    manifest_json: Path


class _RunResult:
    def __init__(self, run_paths: _RunPaths) -> None:
        self._run_paths = run_paths

    @property
    def run_paths(self) -> builder_module.RunPathsLike:
        return self._run_paths


class _BuilderFileHash(FileHash):
    """Hashing-port result expected by the manifest builder contract."""

    @property
    def changed_during_read(self) -> bool:
        return False


class _MutatedFileHash(FileHash):
    @property
    def changed_during_read(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def _stable_hashing_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep builder tests focused on construction rather than hash internals."""

    def stable_hash_file(
        path: Path,
        *,
        chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
        reject_symlinks: bool = True,
        mutation_retries: int = DEFAULT_MUTATION_RETRIES,
        verify_reopen: bool = False,
    ) -> _BuilderFileHash:
        result = hash_file(
            path,
            chunk_size_bytes=chunk_size_bytes,
            reject_symlinks=reject_symlinks,
            mutation_retries=mutation_retries,
            verify_reopen=verify_reopen,
        )
        return _BuilderFileHash(
            path=result.path,
            hash_algorithm=result.hash_algorithm,
            sha256=result.sha256,
            size_bytes=result.size_bytes,
            modified_ns=result.modified_ns,
            identity=result.identity,
            attempts=result.attempts,
            reopen_verified=result.reopen_verified,
        )

    monkeypatch.setattr(builder_module, "hash_file", stable_hash_file)


def _run_context(
    tmp_path: Path, *, run_id: str = "20260725_190423"
) -> tuple[_RunResult, _RunPaths]:
    run_dir = (tmp_path / "run").resolve()
    run_dir.mkdir()
    paths = _RunPaths(
        run_id=run_id,
        run_dir=run_dir,
        manifest_json=run_dir / MANIFEST_FILENAME,
    )
    return _RunResult(run_paths=paths), paths


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _text_declaration(
    path: Path,
    *,
    required: bool = False,
    created_by: str = ArtifactProducer.RUNS.value,
) -> ArtifactDeclaration:
    return ArtifactDeclaration(
        path=path,
        role=ArtifactRole.OTHER.value,
        media_type=TEXT_PLAIN_UTF8,
        required=required,
        created_by=created_by,
    )


def test_build_manifest_uses_final_bytes_and_canonical_order(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    summary = _write(run_paths.run_dir / "summary.json", b'{"status":"OK"}\n')
    human = _write(run_paths.run_dir / "summary.md", "# Résumé\n".encode())
    master_log = _write(run_paths.run_dir / "raw" / "master.log", b"compile ok\n")

    declarations = (
        artifact_declaration(
            Path("raw/master.log"),
            ArtifactRole.MASTER_LOG,
            required=True,
            created_by=ArtifactProducer.REPORTING_LOGS,
        ),
        artifact_declaration(
            Path("summary.md"),
            ArtifactRole.HUMAN_SUMMARY,
            required=True,
            created_by=ArtifactProducer.REPORTING_MARKDOWN,
        ),
        artifact_declaration(
            Path("summary.json"),
            ArtifactRole.MACHINE_SUMMARY,
            required=True,
            created_by=ArtifactProducer.REPORTING_JSON,
        ),
    )

    result = build_manifest_result(
        run_result,
        run_paths,
        declarations,
        generated_at=datetime(
            2026,
            7,
            25,
            15,
            4,
            23,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        producer_version="1.2.3",
    )

    manifest = result.manifest
    assert manifest.schema_id == MANIFEST_SCHEMA_ID
    assert manifest.schema_version == MANIFEST_SCHEMA_VERSION
    assert manifest.producer_name == MANIFEST_PRODUCER_NAME
    assert manifest.producer_version == "1.2.3"
    assert manifest.run_id == run_paths.run_id
    assert manifest.generated_at == "2026-07-25T19:04:23Z"
    assert manifest.hash_algorithm == MANIFEST_HASH_ALGORITHM
    assert [entry.path for entry in manifest.artifacts] == [
        "raw/master.log",
        "summary.json",
        "summary.md",
    ]

    entries = {entry.path: entry for entry in manifest.artifacts}
    assert entries["summary.json"].media_type == APPLICATION_JSON
    assert entries["summary.md"].media_type == TEXT_MARKDOWN_UTF8
    assert entries["raw/master.log"].media_type == TEXT_PLAIN_UTF8
    assert entries["summary.json"].size_bytes == summary.stat().st_size
    assert entries["summary.md"].size_bytes == human.stat().st_size
    assert entries["raw/master.log"].size_bytes == master_log.stat().st_size
    assert entries["summary.json"].sha256 == hashlib.sha256(summary.read_bytes()).hexdigest()
    assert entries["summary.md"].sha256 == hashlib.sha256(human.read_bytes()).hexdigest()
    assert entries["raw/master.log"].sha256 == hashlib.sha256(master_log.read_bytes()).hexdigest()
    assert result.warnings == ()
    assert result.entry_count == 3
    assert result.required_entry_count == 3
    assert result.total_size_bytes == sum(
        path.stat().st_size for path in (summary, human, master_log)
    )


def test_build_manifest_facades_return_the_same_manifest(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    _write(run_paths.run_dir / "summary.json", b"{}\n")
    declarations = (
        artifact_declaration(
            Path("summary.json"),
            ArtifactRole.MACHINE_SUMMARY,
            required=True,
            created_by=ArtifactProducer.REPORTING_JSON,
        ),
    )
    generated_at = datetime(2026, 7, 25, 19, 4, 23, tzinfo=UTC)

    explicit = build_manifest(
        run_result,
        run_paths,
        declarations,
        generated_at=generated_at,
        producer_version="1.0.0",
    )
    from_result = build_manifest_from_result(
        run_result,
        declarations,
        generated_at=generated_at,
        producer_version="1.0.0",
    )

    assert from_result == explicit


def test_optional_missing_artifact_is_omitted_with_bounded_warning(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)

    result = build_manifest_result(
        run_result,
        run_paths,
        (_text_declaration(Path("details/optional.txt")),),
        generated_at=datetime(2026, 7, 25, 19, 4, 23, tzinfo=UTC),
    )

    assert result.manifest.artifacts == ()
    assert result.entry_count == 0
    assert len(result.warnings) == 1
    warning = result.warnings[0]
    assert warning.code == "optional_artifact_missing"
    assert warning.path == "details/optional.txt"
    assert "omitted" in warning.message


def test_missing_required_artifact_is_fatal(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)

    with pytest.raises(MissingRequiredArtifactError, match="required artifact is missing"):
        build_manifest(
            run_result,
            run_paths,
            (_text_declaration(Path("required.txt"), required=True),),
        )


def test_required_semantic_artifact_must_not_be_empty(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    _write(run_paths.run_dir / "summary.json", b"")

    declaration = artifact_declaration(
        Path("summary.json"),
        ArtifactRole.MACHINE_SUMMARY,
        required=True,
        created_by=ArtifactProducer.REPORTING_JSON,
    )

    with pytest.raises(MissingRequiredArtifactError, match="must be non-empty"):
        build_manifest(run_result, run_paths, (declaration,))


def test_empty_text_artifact_is_allowed_when_role_contract_allows_it(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    _write(run_paths.run_dir / "top_errors.txt", b"")

    declaration = artifact_declaration(
        Path("top_errors.txt"),
        ArtifactRole.TOP_ERRORS,
        required=True,
        created_by=ArtifactProducer.REPORTING_LOGS,
    )

    manifest = build_manifest(run_result, run_paths, (declaration,))

    assert manifest.artifacts[0].size_bytes == 0
    assert manifest.artifacts[0].sha256 == hashlib.sha256(b"").hexdigest()


def test_manifest_cannot_include_itself(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    declaration = _text_declaration(run_paths.manifest_json)

    with pytest.raises(UnsafeManifestPathError, match="must not include itself"):
        build_manifest(run_result, run_paths, (declaration,))


def test_artifact_must_remain_beneath_run_root(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    outside = _write((tmp_path / "outside.txt").resolve(), b"outside")

    with pytest.raises(UnsafeManifestPathError, match="escapes the run root"):
        build_manifest(
            run_result,
            run_paths,
            (_text_declaration(outside),),
        )


def test_directory_cannot_be_a_manifest_entry(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    directory = run_paths.run_dir / "details"
    directory.mkdir()

    with pytest.raises(UnsafeManifestPathError, match="directories cannot"):
        build_manifest(
            run_result,
            run_paths,
            (_text_declaration(directory),),
        )


def test_symlink_is_rejected_by_default(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    target = _write(run_paths.run_dir / "target.txt", b"target")
    link = run_paths.run_dir / "link.txt"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(UnsafeManifestPathError, match="symlink artifacts are prohibited"):
        build_manifest(
            run_result,
            run_paths,
            (_text_declaration(link),),
        )


def test_duplicate_paths_use_configured_case_identity(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    upper = _write(run_paths.run_dir / "Detail.txt", b"upper")
    lower = _write(run_paths.run_dir / "detail.txt", b"lower")

    with pytest.raises(DuplicateManifestPathError, match="duplicate artifact path"):
        build_manifest(
            run_result,
            run_paths,
            (
                _text_declaration(upper),
                _text_declaration(lower),
            ),
            policy=ManifestBuildPolicy(case_sensitive_paths=False),
        )


def test_case_sensitive_policy_preserves_distinct_display_paths(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    upper = _write(run_paths.run_dir / "Detail.txt", b"upper")
    lower = _write(run_paths.run_dir / "detail.txt", b"lower")

    manifest = build_manifest(
        run_result,
        run_paths,
        (
            _text_declaration(upper),
            _text_declaration(lower),
        ),
        policy=ManifestBuildPolicy(case_sensitive_paths=True),
    )

    assert [entry.path for entry in manifest.artifacts] == ["Detail.txt", "detail.txt"]


def test_manifest_path_helpers_preserve_portable_identity(tmp_path: Path) -> None:
    run_root = (tmp_path / "run").resolve()
    run_root.mkdir()
    artifact = _write(run_root / "détails" / "résultat final.txt", b"ok")

    assert canonical_manifest_path(artifact, run_root=run_root) == "détails/résultat final.txt"
    assert manifest_path_comparison_key("Raw/Log.txt", case_sensitive=True) == "Raw/Log.txt"
    assert manifest_path_comparison_key("Raw/Log.txt", case_sensitive=False) == "raw/log.txt"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "../outside.txt",
        "raw\\master.log",
        "/absolute.txt",
        "C:/absolute.txt",
        "file://artifact.txt",
        "raw//master.log",
        "raw/./master.log",
    ],
)
def test_manifest_path_comparison_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(UnsafeManifestPathError):
        manifest_path_comparison_key(value)


def test_run_result_and_explicit_paths_must_describe_same_run(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    conflicting = _RunPaths(
        run_id="different-run",
        run_dir=run_paths.run_dir,
        manifest_json=run_paths.manifest_json,
    )

    with pytest.raises(ManifestBuildError, match="different run identifiers"):
        build_manifest(run_result, conflicting, ())


def test_manifest_target_must_be_direct_canonical_child(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    nested = _RunPaths(
        run_id=run_paths.run_id,
        run_dir=run_paths.run_dir,
        manifest_json=run_paths.run_dir / "reports" / MANIFEST_FILENAME,
    )
    nested_result = _RunResult(run_paths=nested)

    with pytest.raises(UnsafeManifestPathError, match="direct child"):
        build_manifest(nested_result, nested, ())


def test_hash_mutation_is_reported_as_artifact_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_result, run_paths = _run_context(tmp_path)
    artifact = _write(run_paths.run_dir / "evidence.txt", b"evidence")
    metadata = artifact.stat()
    identity = FileIdentity.from_stat(metadata)

    def mutated_hash_file(*args: object, **kwargs: object) -> _MutatedFileHash:
        del args, kwargs
        return _MutatedFileHash(
            path=artifact,
            hash_algorithm="sha256",
            sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
            size_bytes=metadata.st_size,
            modified_ns=metadata.st_mtime_ns,
            identity=identity,
        )

    monkeypatch.setattr(builder_module, "hash_file", mutated_hash_file)

    with pytest.raises(ArtifactMutationError, match="changed while hashing"):
        build_manifest(
            run_result,
            run_paths,
            (_text_declaration(artifact, required=True),),
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reject_symlinks": 1},
        {"reject_undeclared_directories": 0},
        {"verify_hash_stability": "yes"},
        {"case_sensitive_paths": 1},
        {"hash_chunk_size": 0},
        {"max_artifacts": 0},
        {"non_empty_required_roles": {""}},
    ],
)
def test_manifest_build_policy_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        cast("Any", ManifestBuildPolicy)(**kwargs)


def test_artifact_count_limit_is_enforced_before_filesystem_reads(tmp_path: Path) -> None:
    run_result, run_paths = _run_context(tmp_path)
    declarations = (
        _text_declaration(Path("one.txt")),
        _text_declaration(Path("two.txt")),
    )

    with pytest.raises(ManifestBuildError, match="configured maximum"):
        build_manifest(
            run_result,
            run_paths,
            declarations,
            policy=ManifestBuildPolicy(max_artifacts=1),
        )
