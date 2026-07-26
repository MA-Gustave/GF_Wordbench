"""Unit tests for verified artifact publication."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType

import pytest

import gf_wordbench.reporting.publisher as publisher
from gf_wordbench.reporting.publisher import (
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
    FilesystemArtifactPublisher,
    PublicationConflictPolicy,
    PublicationContractError,
    PublicationEntry,
    PublicationEntryStatus,
    PublicationKind,
    PublicationRequest,
    PublicationResult,
    PublicationSourceError,
    PublicationStatus,
    PublicationVerificationError,
    discover_publication_entries,
    publish_artifacts,
    publish_run,
)


class _Clock:
    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def utc_now(self) -> datetime:
        return next(self._values)


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_finalized_source(root: Path) -> dict[str, Path]:
    files = {
        SUMMARY_FILENAME: _write(root / SUMMARY_FILENAME, b'{"overall_status":"OK"}\n'),
        MANIFEST_FILENAME: _write(root / MANIFEST_FILENAME, b'{"artifacts":[]}\n'),
        "summary.md": _write(root / "summary.md", b"# Summary\n"),
        "raw/scenarios/unicode.out": _write(
            root / "raw" / "scenarios" / "unicode.out",
            "élève — 日本語\n".encode(),
        ),
    }
    return files


def _entries_for(files: dict[str, Path]) -> tuple[PublicationEntry, ...]:
    return tuple(
        PublicationEntry(
            source_path=relative,
            required=relative in {SUMMARY_FILENAME, MANIFEST_FILENAME},
            expected_size_bytes=path.stat().st_size,
            expected_sha256=_sha256(path),
        )
        for relative, path in files.items()
    )


def _request(
    source_root: Path,
    destination: Path,
    entries: tuple[PublicationEntry, ...],
    **overrides: object,
) -> PublicationRequest:
    values: dict[str, object] = {
        "source_root": source_root.resolve(),
        "destination": destination.resolve(),
        "entries": entries,
        "kind": PublicationKind.COMPLETE_RUN,
        "conflict_policy": PublicationConflictPolicy.FAIL,
        "require_finalized_run": True,
        "require_summary": True,
        "require_manifest": True,
        "verify_source_stability": True,
        "verify_destination": True,
        "preserve_timestamps": True,
        "metadata": {"channel": "test"},
    }
    values.update(overrides)
    return PublicationRequest(**values)  # type: ignore[arg-type]


def test_publication_entry_normalizes_defaults_and_freezes_metadata() -> None:
    metadata = {"source": "release", "attempt": 1}

    entry = PublicationEntry(
        source_path="details/report.json",
        media_type="APPLICATION/JSON",
        metadata=metadata,
    )
    metadata["source"] = "mutated"

    assert entry.published_path == "details/report.json"
    assert entry.media_type == "application/json"
    assert entry.metadata == {"source": "release", "attempt": 1}
    assert isinstance(entry.metadata, MappingProxyType)

    with pytest.raises(TypeError):
        entry.metadata["new"] = "value"  # type: ignore[index]


@pytest.mark.parametrize(
    ("kwargs", "error_type"),
    [
        ({"source_path": "../escape.txt"}, ValueError),
        ({"source_path": r"raw\stdout.txt"}, ValueError),
        ({"source_path": "/absolute.txt"}, ValueError),
        ({"source_path": "raw/./stdout.txt"}, ValueError),
        ({"source_path": "ok.txt", "published_path": "../escape.txt"}, ValueError),
        ({"source_path": "ok.txt", "media_type": "text"}, ValueError),
        ({"source_path": "ok.txt", "required": 1}, TypeError),
        ({"source_path": "ok.txt", "expected_size_bytes": -1}, ValueError),
        ({"source_path": "ok.txt", "expected_sha256": "invalid"}, ValueError),
    ],
)
def test_publication_entry_rejects_invalid_contract_values(
    kwargs: dict[str, object],
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        PublicationEntry(**kwargs)  # type: ignore[arg-type]


def test_publication_request_sorts_entries_and_freezes_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "published"
    source.mkdir()
    metadata = {"release": "1.0.0"}
    entries = (
        PublicationEntry(source_path=SUMMARY_FILENAME),
        PublicationEntry(source_path="z.txt"),
        PublicationEntry(source_path=MANIFEST_FILENAME),
        PublicationEntry(source_path="A.txt"),
    )

    request = _request(source, destination, entries, metadata=metadata)
    metadata["release"] = "changed"

    assert [entry.published_path for entry in request.entries] == [
        "A.txt",
        MANIFEST_FILENAME,
        SUMMARY_FILENAME,
        "z.txt",
    ]
    assert request.metadata == {"release": "1.0.0"}
    assert isinstance(request.metadata, MappingProxyType)


@pytest.mark.parametrize(
    "entries",
    [
        (
            PublicationEntry(source_path=SUMMARY_FILENAME),
            PublicationEntry(source_path=MANIFEST_FILENAME),
            PublicationEntry(source_path="same.txt"),
            PublicationEntry(source_path="SAME.TXT"),
        ),
        (
            PublicationEntry(source_path=SUMMARY_FILENAME),
            PublicationEntry(source_path=MANIFEST_FILENAME),
            PublicationEntry(source_path="one.txt", published_path="same.txt"),
            PublicationEntry(source_path="two.txt", published_path="SAME.TXT"),
        ),
    ],
)
def test_publication_request_rejects_case_insensitive_duplicate_paths(
    tmp_path: Path,
    entries: tuple[PublicationEntry, ...],
) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(ValueError, match="duplicate"):
        _request(source, tmp_path / "destination", entries)


def test_publication_request_requires_final_outputs_and_non_overlapping_roots(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(PublicationContractError, match="summary.json"):
        PublicationRequest(
            source_root=source.resolve(),
            destination=(tmp_path / "published").resolve(),
            entries=(PublicationEntry(source_path=MANIFEST_FILENAME),),
        )

    with pytest.raises(PublicationContractError, match="manifest.json"):
        PublicationRequest(
            source_root=source.resolve(),
            destination=(tmp_path / "published").resolve(),
            entries=(PublicationEntry(source_path=SUMMARY_FILENAME),),
        )

    with pytest.raises(PublicationContractError, match="must not overlap"):
        PublicationRequest(
            source_root=source.resolve(),
            destination=(source / "published").resolve(),
            entries=(
                PublicationEntry(source_path=SUMMARY_FILENAME),
                PublicationEntry(source_path=MANIFEST_FILENAME),
            ),
        )


def test_discovery_is_deterministic_and_assigns_canonical_metadata(
    tmp_path: Path,
) -> None:
    source = tmp_path / "run"
    _make_finalized_source(source)
    _write(source / "details" / "module.json", b"{}\n")
    _write(source / "artifacts" / "pgf" / "Grammar.pgf", b"pgf")
    _write(source / "logs" / "master.log", b"log\n")
    _write(source / "ignored.tmp", b"ignored")

    entries = discover_publication_entries(
        source.resolve(),
        exclude_paths=("ignored.tmp",),
    )

    assert [entry.published_path for entry in entries] == sorted(
        [entry.published_path for entry in entries],
        key=lambda value: (value.casefold(), value),
    )
    by_path = {entry.published_path: entry for entry in entries}
    assert by_path[SUMMARY_FILENAME].role == "machine_summary"
    assert by_path[SUMMARY_FILENAME].media_type == "application/json"
    assert by_path[SUMMARY_FILENAME].required is True
    assert by_path[MANIFEST_FILENAME].role == "artifact_manifest"
    assert by_path["summary.md"].role == "human_summary"
    assert by_path["raw/scenarios/unicode.out"].role == "raw_evidence"
    assert by_path["details/module.json"].role == "detail_report"
    assert by_path["artifacts/pgf/Grammar.pgf"].role == "pgf"
    assert by_path["logs/master.log"].role == "log"
    assert "ignored.tmp" not in by_path


def test_discovery_rejects_symbolic_links_when_supported(tmp_path: Path) -> None:
    source = tmp_path / "run"
    source.mkdir()
    target = _write(source / "target.txt", b"target")
    link = source / "link.txt"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(PublicationSourceError, match="symbolic-link"):
        discover_publication_entries(source.resolve())


def test_publish_artifacts_copies_exact_bytes_and_records_hashes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    started = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    finished = started + timedelta(milliseconds=125)
    request = _request(source, destination, _entries_for(files))

    result = publish_artifacts(request, clock=_Clock(started, finished))

    assert result.status is PublicationStatus.PUBLISHED
    assert result.successful is True
    assert result.duration_ms == 125
    assert result.required_failures == ()
    assert result.metadata == {"channel": "test"}
    assert result.source_manifest_sha256 == _sha256(files[MANIFEST_FILENAME])
    assert destination.is_dir()
    assert not source.samefile(destination)
    published_paths = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    assert published_paths == set(files)

    by_path = {outcome.published_path: outcome for outcome in result.outcomes}
    for relative, source_path in files.items():
        published = destination / Path(relative)
        assert published.read_bytes() == source_path.read_bytes()
        assert by_path[relative].status is PublicationEntryStatus.PUBLISHED
        assert by_path[relative].size_bytes == source_path.stat().st_size
        assert by_path[relative].sha256 == _sha256(source_path)

    assert not list(tmp_path.glob(".published.publish-*.tmp"))
    assert not list(tmp_path.glob(".published.publish-*.bak"))


def test_missing_optional_entry_is_omitted_without_failing_publication(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    entries = _entries_for(files) + (
        PublicationEntry(source_path="optional.txt", required=False),
    )
    destination = tmp_path / "published"

    result = publish_artifacts(_request(source, destination, entries))

    assert result.status is PublicationStatus.PUBLISHED
    assert "optional.txt" not in {outcome.source_path for outcome in result.outcomes}
    assert not (destination / "optional.txt").exists()


def test_source_integrity_mismatch_fails_without_creating_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    entries = list(_entries_for(files))
    summary_index = next(
        index for index, entry in enumerate(entries) if entry.source_path == SUMMARY_FILENAME
    )
    entries[summary_index] = PublicationEntry(
        source_path=SUMMARY_FILENAME,
        required=True,
        expected_size_bytes=files[SUMMARY_FILENAME].stat().st_size,
        expected_sha256="0" * 64,
    )
    destination = tmp_path / "published"

    result = publish_artifacts(_request(source, destination, tuple(entries)))

    assert result.status is PublicationStatus.FAILED
    assert result.successful is False
    assert result.error is not None
    assert "source hash mismatch" in result.error
    assert not destination.exists()
    assert any(
        outcome.status is PublicationEntryStatus.FAILED
        for outcome in result.outcomes
    )


def test_approved_manifest_digest_is_verified_and_recorded(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    digest = _sha256(files[MANIFEST_FILENAME])

    success = publish_artifacts(
        _request(
            source,
            tmp_path / "published",
            _entries_for(files),
            source_manifest_sha256=digest,
        )
    )
    failure = publish_artifacts(
        _request(
            source,
            tmp_path / "rejected",
            _entries_for(files),
            source_manifest_sha256="f" * 64,
        )
    )

    assert success.status is PublicationStatus.PUBLISHED
    assert success.source_manifest_sha256 == digest
    assert failure.status is PublicationStatus.FAILED
    assert failure.error is not None
    assert "approved digest" in failure.error
    assert not (tmp_path / "rejected").exists()


def test_conflict_fail_policy_preserves_existing_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    marker = _write(destination / "keep.txt", b"existing")

    result = publish_artifacts(
        _request(
            source,
            destination,
            _entries_for(files),
            conflict_policy=PublicationConflictPolicy.FAIL,
        )
    )

    assert result.status is PublicationStatus.FAILED
    assert result.error is not None
    assert "already exists" in result.error
    assert marker.read_bytes() == b"existing"
    assert set(path.name for path in destination.iterdir()) == {"keep.txt"}


def test_reuse_identical_returns_already_present_without_rewriting(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    entries = _entries_for(files)

    first = publish_artifacts(_request(source, destination, entries))
    before = {
        relative: (destination / Path(relative)).stat().st_mtime_ns
        for relative in files
    }
    second = publish_artifacts(
        _request(
            source,
            destination,
            entries,
            conflict_policy=PublicationConflictPolicy.REUSE_IDENTICAL,
        )
    )

    assert first.status is PublicationStatus.PUBLISHED
    assert second.status is PublicationStatus.ALREADY_PRESENT
    assert second.successful is True
    assert all(
        outcome.status is PublicationEntryStatus.ALREADY_PRESENT
        for outcome in second.outcomes
    )
    assert {
        relative: (destination / Path(relative)).stat().st_mtime_ns
        for relative in files
    } == before


def test_reuse_identical_rejects_extra_or_changed_destination_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    entries = _entries_for(files)
    assert publish_artifacts(_request(source, destination, entries)).successful
    _write(destination / "unexpected.txt", b"extra")

    result = publish_artifacts(
        _request(
            source,
            destination,
            entries,
            conflict_policy=PublicationConflictPolicy.REUSE_IDENTICAL,
        )
    )

    assert result.status is PublicationStatus.FAILED
    assert result.error is not None
    assert "differs from requested set" in result.error
    assert (destination / "unexpected.txt").read_bytes() == b"extra"


def test_replace_policy_replaces_the_entire_destination_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    _write(destination / "obsolete.txt", b"obsolete")
    _write(destination / SUMMARY_FILENAME, b"old")

    result = publish_artifacts(
        _request(
            source,
            destination,
            _entries_for(files),
            conflict_policy=PublicationConflictPolicy.REPLACE,
        )
    )

    assert result.status is PublicationStatus.PUBLISHED
    assert not (destination / "obsolete.txt").exists()
    assert (destination / SUMMARY_FILENAME).read_bytes() == files[SUMMARY_FILENAME].read_bytes()
    assert not list(tmp_path.glob(".published.publish-*.bak"))


def test_replace_policy_rolls_back_when_post_commit_verification_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)
    destination = tmp_path / "published"
    old = _write(destination / "old.txt", b"old publication")

    def fail_verification(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise PublicationVerificationError("forced post-commit failure")

    monkeypatch.setattr(publisher, "_verify_existing_destination", fail_verification)

    result = publish_artifacts(
        _request(
            source,
            destination,
            _entries_for(files),
            conflict_policy=PublicationConflictPolicy.REPLACE,
        )
    )

    assert result.status is PublicationStatus.FAILED
    assert result.error == "forced post-commit failure"
    assert old.read_bytes() == b"old publication"
    assert set(path.name for path in destination.iterdir()) == {"old.txt"}
    assert not list(tmp_path.glob(".published.publish-*.tmp"))
    assert not list(tmp_path.glob(".published.publish-*.bak"))


def test_publish_run_promotes_the_exact_discovered_tree(tmp_path: Path) -> None:
    source = tmp_path / "run"
    files = _make_finalized_source(source)
    _write(source / "logs" / "all.log", b"complete log\n")
    destination = tmp_path / "archive" / "run-001"

    result = publish_run(
        source.resolve(),
        destination.resolve(),
        metadata={"revision": "abc123"},
    )

    expected_paths = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file()
    }
    actual_paths = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }

    assert result.kind is PublicationKind.COMPLETE_RUN
    assert result.status is PublicationStatus.PUBLISHED
    assert result.metadata == {"revision": "abc123"}
    assert actual_paths == expected_paths
    for relative in expected_paths:
        assert (destination / relative).read_bytes() == (source / relative).read_bytes()
    assert result.source_manifest_sha256 == _sha256(files[MANIFEST_FILENAME])


def test_publish_run_rejects_incomplete_finalized_source(tmp_path: Path) -> None:
    source = tmp_path / "run"
    source.mkdir()
    _write(source / SUMMARY_FILENAME, b"{}\n")

    with pytest.raises(PublicationContractError, match="manifest.json"):
        publish_run(source.resolve(), (tmp_path / "published").resolve())


def test_filesystem_publisher_requires_protocol_clock() -> None:
    with pytest.raises(TypeError, match="PublicationClock"):
        FilesystemArtifactPublisher(clock=object())  # type: ignore[arg-type]


def test_naive_clock_result_is_rejected_before_publication(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _make_finalized_source(source)

    with pytest.raises(ValueError, match="timezone-aware"):
        publish_artifacts(
            _request(source, tmp_path / "published", _entries_for(files)),
            clock=_Clock(datetime(2026, 7, 25, 12, 0)),
        )


def test_publication_result_contract_and_derived_properties(tmp_path: Path) -> None:
    started = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    failed = publisher.PublicationEntryOutcome(
        source_path="summary.json",
        published_path="summary.json",
        role="machine_summary",
        required=True,
        status=PublicationEntryStatus.FAILED,
        error="failed",
    )
    result = PublicationResult(
        source_root=(tmp_path / "source").resolve(),
        destination=(tmp_path / "published").resolve(),
        kind=PublicationKind.COMPLETE_RUN,
        status=PublicationStatus.FAILED,
        started_at=started,
        finished_at=started + timedelta(milliseconds=10),
        outcomes=(failed,),
        source_manifest_sha256=None,
        publication_id="publication-1",
        error="publication failed",
    )

    assert result.successful is False
    assert result.duration_ms == 10
    assert result.required_failures == (failed,)

    with pytest.raises(ValueError, match="requires error"):
        PublicationResult(
            source_root=(tmp_path / "source").resolve(),
            destination=(tmp_path / "published").resolve(),
            kind=PublicationKind.COMPLETE_RUN,
            status=PublicationStatus.FAILED,
            started_at=started,
            finished_at=started,
            outcomes=(),
            source_manifest_sha256=None,
            publication_id="publication-2",
        )
