"""Unit tests for read-only run-history discovery and baseline selection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from gf_wordbench.runs.history import (
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
    RunHistoryEntry,
    RunHistoryQuery,
    RunHistoryRecord,
    RunHistoryState,
    discover_run_history,
    inspect_run_directory,
    is_previous_run_eligible,
    select_previous_run,
)


_BASE_TIME = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
_PROJECT_ID = "example-language"


def _record(
    run_id: str,
    *,
    project_id: str = _PROJECT_ID,
    mode: ValidationMode = ValidationMode.RELEASE,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    status: OverallStatus = OverallStatus.OK,
    target_file: str | None = None,
    manifest_relative_path: str | None = MANIFEST_FILENAME,
    complete: bool = True,
    legacy: bool = False,
) -> RunHistoryRecord:
    started = started_at or _BASE_TIME
    return RunHistoryRecord(
        run_id=run_id,
        project_id=project_id,
        mode=mode,
        started_at=started,
        finished_at=finished_at or started + timedelta(minutes=1),
        overall_status=status,
        target_file=target_file,
        schema_id="gf-wordbench.run-summary",
        schema_version="1.0",
        manifest_relative_path=manifest_relative_path,
        complete=complete,
        legacy=legacy,
    )


def _run_directory(
    output_root: Path,
    run_id: str,
    *,
    summary: bool = True,
    manifest: bool = True,
    manifest_relative_path: str = MANIFEST_FILENAME,
) -> Path:
    run_dir = output_root / f"run_{run_id}"
    run_dir.mkdir()
    if summary:
        (run_dir / SUMMARY_FILENAME).write_text("{}\n", encoding="utf-8")
    if manifest:
        manifest_path = run_dir / manifest_relative_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("{}\n", encoding="utf-8")
    return run_dir


def _reader(records: dict[str, RunHistoryRecord]):
    def read(summary_path: Path) -> RunHistoryRecord:
        return records[summary_path.parent.name]

    return read


def _verified(
    run_dir: Path,
    manifest_path: Path,
    run_id: str,
) -> bool:
    return (
        run_dir.name == f"run_{run_id}"
        and manifest_path.is_file()
        and manifest_path.is_relative_to(run_dir)
    )


def test_record_normalizes_enums_timezones_and_portable_paths() -> None:
    eastern = timezone(timedelta(hours=-4))
    record = RunHistoryRecord(
        run_id="20260725_120000",
        project_id=_PROJECT_ID,
        mode="quick",  # type: ignore[arg-type]
        started_at=datetime(2026, 7, 25, 8, 0, tzinfo=eastern),
        finished_at=datetime(2026, 7, 25, 8, 1, tzinfo=eastern),
        overall_status="OK",  # type: ignore[arg-type]
        target_file=r"src\Grammar.gf",
        manifest_relative_path="metadata/manifest.json",
    )

    assert record.mode is ValidationMode.QUICK
    assert record.overall_status is OverallStatus.OK
    assert record.started_at == _BASE_TIME
    assert record.finished_at == _BASE_TIME + timedelta(minutes=1)
    assert record.target_file == "src/Grammar.gf"
    assert record.manifest_relative_path is not None
    assert record.manifest_relative_path.as_posix() == "metadata/manifest.json"


@pytest.mark.parametrize(
    ("changes", "exception", "message"),
    [
        ({"finished_at": _BASE_TIME - timedelta(seconds=1)}, ValueError, "precede"),
        ({"started_at": datetime(2026, 7, 25, 12, 0)}, ValueError, "timezone-aware"),
        ({"target_file": "../outside.gf"}, ValueError, "project-relative"),
        ({"target_file": "C:/outside.gf"}, ValueError, "project-relative"),
        ({"manifest_relative_path": r"raw\manifest.json"}, ValueError, "portable"),
        ({"manifest_relative_path": "../manifest.json"}, ValueError, "run-relative"),
        ({"complete": 1}, TypeError, "bools"),
        ({"legacy": 0}, TypeError, "bools"),
    ],
)
def test_record_rejects_invalid_contract_values(
    changes: dict[str, Any],
    exception: type[Exception],
    message: str,
) -> None:
    values: dict[str, Any] = {
        "run_id": "20260725_120000",
        "project_id": _PROJECT_ID,
        "mode": ValidationMode.RELEASE,
        "started_at": _BASE_TIME,
        "finished_at": _BASE_TIME + timedelta(minutes=1),
        "overall_status": OverallStatus.OK,
    }
    values.update(changes)

    with pytest.raises(exception, match=message):
        RunHistoryRecord(**values)


def test_query_normalizes_filters_and_validates_output_root(
    tmp_path: Path,
) -> None:
    current = tmp_path / "run_20260725_120000"
    query = RunHistoryQuery(
        output_root=tmp_path,
        current_run_dir=current,
        current_run_id="20260725_120000",
        project_id=_PROJECT_ID,
        mode="quick",
        target_file=r"src\Grammar.gf",
        not_after=datetime(
            2026,
            7,
            25,
            8,
            1,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        max_entries=3,
    )

    assert query.output_root == tmp_path.resolve()
    assert query.current_run_dir == current
    assert query.mode is ValidationMode.QUICK
    assert query.target_file == "src/Grammar.gf"
    assert query.not_after == _BASE_TIME + timedelta(minutes=1)
    assert query.max_entries == 3


@pytest.mark.parametrize("max_entries", [0, -1, True, 1.5])
def test_query_rejects_invalid_max_entries(
    tmp_path: Path,
    max_entries: object,
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        RunHistoryQuery(output_root=tmp_path, max_entries=max_entries)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field",
    [
        "allow_legacy",
        "require_manifest_verification",
        "include_incomplete",
        "include_corrupt",
        "include_unknown",
    ],
)
def test_query_requires_real_boolean_flags(
    tmp_path: Path,
    field: str,
) -> None:
    arguments: dict[str, Any] = {"output_root": tmp_path, field: 1}
    with pytest.raises(TypeError, match=field):
        RunHistoryQuery(**arguments)


def test_query_requires_an_existing_safe_absolute_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="absolute"):
        RunHistoryQuery(output_root=Path("relative"))

    with pytest.raises(NotADirectoryError, match="safe directory"):
        RunHistoryQuery(output_root=tmp_path / "missing")


def test_inspect_finalized_run_verifies_manifest(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)
    record = _record(run_id)
    calls: list[tuple[Path, Path, str]] = []

    def verifier(
        observed_run_dir: Path,
        manifest_path: Path,
        observed_run_id: str,
    ) -> bool:
        calls.append((observed_run_dir, manifest_path, observed_run_id))
        return True

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: record,
        manifest_verifier=verifier,
    )

    assert entry.state is RunHistoryState.FINALIZED
    assert entry.is_finalized is True
    assert entry.record == record
    assert entry.run_id == run_id
    assert entry.project_id == _PROJECT_ID
    assert entry.mode is ValidationMode.RELEASE
    assert entry.overall_status is OverallStatus.OK
    assert entry.manifest_verified is True
    assert entry.issues == ()
    assert calls == [(run_dir, run_dir / MANIFEST_FILENAME, run_id)]


def test_inspect_supports_recorded_nested_manifest_path(
    tmp_path: Path,
) -> None:
    run_id = "20260725_120000"
    relative_manifest = "metadata/artifacts.json"
    run_dir = _run_directory(
        tmp_path,
        run_id,
        manifest_relative_path=relative_manifest,
    )

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(
            run_id,
            manifest_relative_path=relative_manifest,
        ),
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.FINALIZED
    assert entry.manifest_path == run_dir / relative_manifest


@pytest.mark.parametrize(
    ("summary", "manifest", "expected_state"),
    [
        (False, False, RunHistoryState.INCOMPLETE),
        (False, True, RunHistoryState.INCOMPLETE),
    ],
)
def test_missing_summary_is_incomplete(
    tmp_path: Path,
    summary: bool,
    manifest: bool,
    expected_state: RunHistoryState,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(
        tmp_path,
        run_id,
        summary=summary,
        manifest=manifest,
    )

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(run_id),
        manifest_verifier=_verified,
    )

    assert entry.state is expected_state
    assert entry.record is None
    assert any("missing or unsafe summary" in issue for issue in entry.issues)


@pytest.mark.parametrize(
    ("manifest", "expected_state"),
    [
        (False, RunHistoryState.INCOMPLETE),
        (True, RunHistoryState.CORRUPT),
    ],
)
def test_rejected_summary_is_classified_by_manifest_presence(
    tmp_path: Path,
    manifest: bool,
    expected_state: RunHistoryState,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id, manifest=manifest)

    def reject(_path: Path) -> RunHistoryRecord:
        raise ValueError("invalid schema")

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=reject,
        manifest_verifier=_verified,
    )

    assert entry.state is expected_state
    assert any("summary rejected (ValueError)" in issue for issue in entry.issues)


def test_summary_reader_must_return_history_record(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: {"run_id": run_id},  # type: ignore[arg-type,return-value]
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.CORRUPT
    assert any("summary rejected (TypeError)" in issue for issue in entry.issues)


def test_directory_and_summary_run_ids_must_agree(tmp_path: Path) -> None:
    run_dir = _run_directory(tmp_path, "20260725_120000")

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record("20260725_115959"),
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.CORRUPT
    assert entry.run_id == "20260725_120000"
    assert entry.record is not None
    assert entry.record.run_id == "20260725_115959"
    assert any("run IDs disagree" in issue for issue in entry.issues)


def test_incomplete_summary_never_reaches_manifest_verifier(
    tmp_path: Path,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)
    called = False

    def verifier(_run_dir: Path, _manifest: Path, _run_id: str) -> bool:
        nonlocal called
        called = True
        return True

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(run_id, complete=False),
        manifest_verifier=verifier,
    )

    assert entry.state is RunHistoryState.INCOMPLETE
    assert entry.manifest_path is None
    assert called is False
    assert any("summary is incomplete" in issue for issue in entry.issues)


def test_legacy_summary_is_visible_but_unverified(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id, manifest=False)

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(
            run_id,
            manifest_relative_path=None,
            legacy=True,
        ),
    )

    assert entry.state is RunHistoryState.LEGACY
    assert entry.manifest_path is None
    assert entry.manifest_verified is None
    assert entry.previous_run_eligible is False


def test_noncanonical_directory_name_is_labelled_legacy_or_unknown(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_old-format"
    run_dir.mkdir()
    (run_dir / SUMMARY_FILENAME).write_text("{}\n", encoding="utf-8")
    record = _record("20260725_120000", legacy=True, manifest_relative_path=None)

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: record,
    )

    assert entry.state is RunHistoryState.LEGACY
    assert entry.run_id == record.run_id
    assert any("non-canonical run directory name" in issue for issue in entry.issues)


def test_missing_manifest_is_incomplete(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id, manifest=False)

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(run_id),
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.INCOMPLETE
    assert entry.manifest_verified is False
    assert any("missing or unsafe manifest" in issue for issue in entry.issues)


def test_missing_manifest_verifier_leaves_run_unknown(
    tmp_path: Path,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(run_id),
    )

    assert entry.state is RunHistoryState.UNKNOWN
    assert entry.manifest_verified is None
    assert any("verification not supplied" in issue for issue in entry.issues)


@pytest.mark.parametrize("behavior", ["false", "raise"])
def test_manifest_verification_failure_marks_run_corrupt(
    tmp_path: Path,
    behavior: str,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)

    def verifier(_run_dir: Path, _manifest: Path, _run_id: str) -> bool:
        if behavior == "raise":
            raise OSError("cannot read manifest")
        return False

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record(run_id),
        manifest_verifier=verifier,
    )

    assert entry.state is RunHistoryState.CORRUPT
    assert entry.manifest_verified is False
    assert any("verification failed" in issue for issue in entry.issues)


def test_nested_or_external_run_directory_is_unknown(tmp_path: Path) -> None:
    nested_root = tmp_path / "nested"
    nested_root.mkdir()
    run_dir = _run_directory(nested_root, "20260725_120000")

    entry = inspect_run_directory(
        run_dir,
        output_root=tmp_path,
        summary_reader=lambda _path: _record("20260725_120000"),
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.UNKNOWN
    assert any("unsafe run directory" in issue for issue in entry.issues)


def test_symlink_run_directory_is_unknown_when_supported(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "targets"
    target_root.mkdir()
    target = _run_directory(target_root, "20260725_120000")
    link = tmp_path / "run_20260725_120000"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    entry = inspect_run_directory(
        link,
        output_root=tmp_path,
        summary_reader=lambda _path: _record("20260725_120000"),
        manifest_verifier=_verified,
    )

    assert entry.state is RunHistoryState.UNKNOWN
    assert any("unsafe run directory" in issue for issue in entry.issues)


def test_discovery_filters_non_run_names_and_excludes_current_run(
    tmp_path: Path,
) -> None:
    old_id = "20260725_115900"
    current_id = "20260725_120000"
    old_dir = _run_directory(tmp_path, old_id)
    current_dir = _run_directory(tmp_path, current_id)
    (tmp_path / "notes").mkdir()
    (tmp_path / "runbook").mkdir()
    records = {
        old_dir.name: _record(old_id),
        current_dir.name: _record(current_id),
    }

    result = discover_run_history(
        RunHistoryQuery(
            output_root=tmp_path,
            current_run_id=current_id,
            project_id=_PROJECT_ID,
            mode=ValidationMode.RELEASE,
        ),
        summary_reader=_reader(records),
        manifest_verifier=_verified,
    )

    assert [entry.run_id for entry in result.entries] == [old_id]
    assert result.previous_run is not None
    assert result.previous_run.run_id == old_id
    assert any("current run excluded" in issue for issue in result.ignored)
    assert not any("notes" in issue or "runbook" in issue for issue in result.ignored)


def test_discovery_orders_newest_compatible_run_first(
    tmp_path: Path,
) -> None:
    first_id = "20260725_115900"
    second_id = "20260725_120000"
    collision_id = "20260725_120000_02"
    first_dir = _run_directory(tmp_path, first_id)
    second_dir = _run_directory(tmp_path, second_id)
    collision_dir = _run_directory(tmp_path, collision_id)
    records = {
        first_dir.name: _record(
            first_id,
            finished_at=_BASE_TIME,
        ),
        second_dir.name: _record(
            second_id,
            finished_at=_BASE_TIME + timedelta(minutes=1),
        ),
        collision_dir.name: _record(
            collision_id,
            finished_at=_BASE_TIME + timedelta(minutes=1),
        ),
    }

    result = discover_run_history(
        RunHistoryQuery(output_root=tmp_path, max_entries=2),
        summary_reader=_reader(records),
        manifest_verifier=_verified,
    )

    assert [entry.run_id for entry in result.entries] == [
        collision_id,
        second_id,
    ]
    assert result.previous_run is not None
    assert result.previous_run.run_id == collision_id


def test_discovery_visibility_flags_control_diagnostic_entries(
    tmp_path: Path,
) -> None:
    incomplete_id = "20260725_115900"
    corrupt_id = "20260725_120000"
    unknown_id = "20260725_120100"
    _run_directory(tmp_path, incomplete_id, summary=False, manifest=False)
    corrupt_dir = _run_directory(tmp_path, corrupt_id)
    unknown_dir = _run_directory(tmp_path, unknown_id)
    records = {
        unknown_dir.name: _record(unknown_id),
    }

    def reader(summary_path: Path) -> RunHistoryRecord:
        if summary_path.parent == corrupt_dir:
            raise ValueError("corrupt summary")
        return records[summary_path.parent.name]

    result = discover_run_history(
        RunHistoryQuery(
            output_root=tmp_path,
            include_incomplete=False,
            include_corrupt=False,
            include_unknown=False,
        ),
        summary_reader=reader,
        manifest_verifier=None,
    )

    assert result.entries == ()
    assert any("missing or unsafe summary" in issue for issue in result.ignored)
    assert any("verification not supplied" in issue for issue in result.ignored)

    corrupt_result = discover_run_history(
        RunHistoryQuery(
            output_root=tmp_path,
            include_incomplete=False,
            include_corrupt=True,
            include_unknown=False,
        ),
        summary_reader=reader,
        manifest_verifier=None,
    )
    assert [entry.state for entry in corrupt_result.entries] == [
        RunHistoryState.CORRUPT
    ]


def test_eligibility_applies_project_mode_target_and_time_filters(
    tmp_path: Path,
) -> None:
    run_id = "20260725_120000"
    record = _record(
        run_id,
        mode=ValidationMode.QUICK,
        target_file="src/Grammar.gf",
        finished_at=_BASE_TIME + timedelta(minutes=2),
    )
    entry = RunHistoryEntry(
        run_dir=tmp_path / f"run_{run_id}",
        state=RunHistoryState.FINALIZED,
        run_id=record.run_id,
        record=record,
        manifest_verified=True,
    )

    matching = RunHistoryQuery(
        output_root=tmp_path,
        project_id=_PROJECT_ID,
        mode=ValidationMode.QUICK,
        target_file="src/Grammar.gf",
        not_after=_BASE_TIME + timedelta(minutes=2),
    )
    assert is_previous_run_eligible(entry, matching) is True

    mismatches = (
        RunHistoryQuery(output_root=tmp_path, project_id="other-project"),
        RunHistoryQuery(output_root=tmp_path, mode=ValidationMode.RELEASE),
        RunHistoryQuery(
            output_root=tmp_path,
            mode=ValidationMode.QUICK,
            target_file="src/Other.gf",
        ),
        RunHistoryQuery(
            output_root=tmp_path,
            not_after=_BASE_TIME + timedelta(minutes=1),
        ),
        RunHistoryQuery(output_root=tmp_path, current_run_id=run_id),
    )
    for query in mismatches:
        assert is_previous_run_eligible(entry, query) is False


def test_target_filter_only_applies_to_quick_mode(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    record = _record(
        run_id,
        mode=ValidationMode.CHECKPOINT,
        target_file="src/Grammar.gf",
    )
    entry = RunHistoryEntry(
        run_dir=tmp_path / f"run_{run_id}",
        state=RunHistoryState.FINALIZED,
        run_id=record.run_id,
        record=record,
        manifest_verified=True,
    )
    query = RunHistoryQuery(
        output_root=tmp_path,
        mode=ValidationMode.CHECKPOINT,
        target_file="src/Other.gf",
    )

    assert is_previous_run_eligible(entry, query) is True


def test_legacy_eligibility_requires_explicit_unverified_policy(
    tmp_path: Path,
) -> None:
    record = _record(
        "20260725_120000",
        legacy=True,
        manifest_relative_path=None,
    )
    entry = RunHistoryEntry(
        run_dir=tmp_path / "run_20260725_120000",
        state=RunHistoryState.LEGACY,
        run_id=record.run_id,
        record=record,
    )

    assert is_previous_run_eligible(
        entry,
        RunHistoryQuery(output_root=tmp_path),
    ) is False
    assert is_previous_run_eligible(
        entry,
        RunHistoryQuery(
            output_root=tmp_path,
            allow_legacy=True,
            require_manifest_verification=True,
        ),
    ) is False
    assert is_previous_run_eligible(
        entry,
        RunHistoryQuery(
            output_root=tmp_path,
            allow_legacy=True,
            require_manifest_verification=False,
        ),
    ) is True


def test_select_previous_run_returns_none_without_eligible_candidate(
    tmp_path: Path,
) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id, manifest=False)

    selected = select_previous_run(
        RunHistoryQuery(output_root=tmp_path),
        summary_reader=lambda _path: _record(run_id),
        manifest_verifier=_verified,
    )

    assert selected is None
    assert run_dir.is_dir()


def test_discovery_is_read_only(tmp_path: Path) -> None:
    run_id = "20260725_120000"
    run_dir = _run_directory(tmp_path, run_id)
    summary = run_dir / SUMMARY_FILENAME
    manifest = run_dir / MANIFEST_FILENAME
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (summary, manifest)
    }

    result = discover_run_history(
        RunHistoryQuery(output_root=tmp_path),
        summary_reader=lambda _path: _record(run_id),
        manifest_verifier=_verified,
    )

    assert result.previous_run is not None
    for path, (content, modified_ns) in before.items():
        assert path.read_bytes() == content
        assert path.stat().st_mtime_ns == modified_ns


def test_public_functions_reject_invalid_collaborators(tmp_path: Path) -> None:
    query = RunHistoryQuery(output_root=tmp_path)

    with pytest.raises(TypeError, match="RunHistoryQuery"):
        discover_run_history(object(), summary_reader=lambda _path: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(TypeError, match="summary_reader"):
        discover_run_history(query, summary_reader=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="manifest_verifier"):
        discover_run_history(
            query,
            summary_reader=lambda _path: _record("20260725_120000"),
            manifest_verifier=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="RunHistoryEntry"):
        is_previous_run_eligible(object(), query)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RunHistoryQuery"):
        is_previous_run_eligible(
            RunHistoryEntry(
                run_dir=tmp_path / "run_20260725_120000",
                state=RunHistoryState.UNKNOWN,
            ),
            object(),  # type: ignore[arg-type]
        )
