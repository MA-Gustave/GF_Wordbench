from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.kernel.errors import (
    ContractViolationError,
    PathSecurityError,
)
from gf_wordbench.kernel.ids import validate_run_id
from gf_wordbench.kernel.statuses import OverallStatus
from gf_wordbench.runs.budgets import (
    BudgetDenialReason,
    BudgetPhase,
    RunBudget,
)
from gf_wordbench.runs.identity import (
    create_collision_run_id,
    create_run_id,
    is_run_directory_name,
    iter_run_id_candidates,
    parse_run_directory_name,
    run_directory_name,
    run_id_collision_index,
    run_id_timestamp,
)
from gf_wordbench.runs.lifecycle import (
    RunLifecycleState,
    allowed_lifecycle_targets,
    can_transition_lifecycle,
    new_run_lifecycle,
)
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.models.results import RunTotals
from gf_wordbench.runs.paths import (
    allocate_run_paths,
    build_run_paths,
    owned_run_paths,
    resolve_run_relative_path,
    run_relative_path,
    standard_run_directories,
    validate_run_paths,
)
from gf_wordbench.runs.ports import (
    ArtifactVerificationIssue,
    ArtifactVerificationResult,
    FileDigest,
    RunTreeEntry,
    RunTreeEntryKind,
)

pytestmark = pytest.mark.contract


class _Clock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_run_identity_is_utc_canonical_and_collision_safe() -> None:
    timestamp = datetime(
        2026,
        7,
        24,
        14,
        59,
        45,
        tzinfo=timezone(timedelta(hours=2)),
    )

    base = create_run_id(timestamp)
    collision = create_run_id(timestamp, collision_index=2)

    assert str(base) == "20260724_125945"
    assert str(collision) == "20260724_125945_02"
    assert create_collision_run_id(base, 12) == "20260724_125945_12"
    assert run_id_collision_index(base) == 1
    assert run_id_collision_index(collision) == 2
    assert run_id_timestamp(collision) == datetime(2026, 7, 24, 12, 59, 45, tzinfo=UTC)
    assert run_directory_name(collision) == "run_20260724_125945_02"
    assert parse_run_directory_name("run_20260724_125945_02") == collision
    assert is_run_directory_name("run_20260724_125945_02")
    assert not is_run_directory_name("20260724_125945_02")

    candidates = iter_run_id_candidates(timestamp)
    assert [str(next(candidates)) for _ in range(3)] == [
        "20260724_125945",
        "20260724_125945_02",
        "20260724_125945_03",
    ]


def test_run_identity_rejects_ambiguous_or_reused_inputs() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        create_run_id(datetime(2026, 7, 24, 12, 0, 0))

    with pytest.raises(ValueError, match="must not already contain"):
        create_collision_run_id("20260724_125945_02", 3)

    with pytest.raises(ValueError, match="basename"):
        parse_run_directory_name("nested/run_20260724_125945")

    with pytest.raises(ValueError, match="at least 1"):
        create_run_id(datetime.now(UTC), collision_index=0)


def test_run_paths_are_canonical_absolute_contained_and_immutable(
    tmp_path: Path,
) -> None:
    run_id = "20260724_125945"
    paths = allocate_run_paths(tmp_path, run_id)

    assert isinstance(paths, RunPaths)
    assert paths.run_dir == tmp_path / "run_20260724_125945"
    assert paths.report_files == (
        paths.run_dir / "summary.json",
        paths.run_dir / "summary.md",
        paths.run_dir / "AI_READY.md",
        paths.run_dir / "top_errors.txt",
        paths.run_dir / "manifest.json",
    )
    assert paths.log_files == (
        paths.run_dir / "raw" / "master.log",
        paths.run_dir / "raw" / "ALL_SCAN_LOGS.TXT",
        paths.run_dir / "raw" / "ALL_LOGS.TXT",
    )
    assert all(path.is_absolute() for path in paths.owned_paths)
    assert all(directory.is_dir() for directory in paths.standard_directories)
    assert validate_run_paths(paths, require_directories=True) is paths

    owned = owned_run_paths(paths)
    directories = standard_run_directories(paths)
    assert owned[0] == ("run_dir", paths.run_dir)
    assert directories[0] == ("run_dir", paths.run_dir)
    assert len({path for _, path in owned}) == len(owned)

    relative = run_relative_path(paths, paths.master_log)
    assert relative == PurePosixPath("raw/master.log")
    assert resolve_run_relative_path(paths, relative) == paths.master_log

    with pytest.raises(FrozenInstanceError):
        paths.run_id = "20260724_125946"  # type: ignore[misc]


def test_run_paths_reject_identity_mismatch_and_escape(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_20260724_125945"
    run_dir.mkdir()
    paths = build_run_paths("20260724_125945", run_dir)

    with pytest.raises(ValueError, match="must be named"):
        build_run_paths("20260724_125946", run_dir)

    with pytest.raises((ValueError, ContractViolationError, PathSecurityError)):
        paths.require_owned_path(tmp_path / "outside.txt")

    with pytest.raises((ValueError, ContractViolationError, PathSecurityError)):
        resolve_run_relative_path(paths, "../outside.txt")


def test_run_lifecycle_enforces_the_canonical_transition_graph() -> None:
    run_id = "20260724_125945"
    allocated_at = datetime(2026, 7, 24, 12, 59, 45, tzinfo=UTC)
    lifecycle = new_run_lifecycle(run_id, allocated_at=allocated_at)

    assert lifecycle.state is RunLifecycleState.ALLOCATED
    assert lifecycle.revision == 0
    assert not lifecycle.is_terminal
    assert allowed_lifecycle_targets(RunLifecycleState.ALLOCATED) == frozenset(
        {RunLifecycleState.INITIALIZED}
    )

    sequence = (
        RunLifecycleState.INITIALIZED,
        RunLifecycleState.EXECUTING,
        RunLifecycleState.FINALIZING,
        RunLifecycleState.FINALIZED,
    )
    for offset, state in enumerate(sequence, start=1):
        lifecycle = lifecycle.transition(
            state,
            occurred_at=allocated_at + timedelta(seconds=offset),
        )

    assert lifecycle.state is RunLifecycleState.FINALIZED
    assert lifecycle.revision == 4
    assert len(lifecycle.history) == 4
    assert lifecycle.is_complete
    assert lifecycle.is_terminal
    assert lifecycle.is_previous_run_eligible
    assert not lifecycle.state.allows_stage_execution
    assert not lifecycle.state.allows_finalization_writes
    assert not can_transition_lifecycle(
        RunLifecycleState.FINALIZED,
        RunLifecycleState.EXECUTING,
    )

    with pytest.raises(ValueError, match="prohibited"):
        lifecycle.transition(
            RunLifecycleState.EXECUTING,
            occurred_at=allocated_at + timedelta(seconds=5),
        )


def test_incomplete_and_corrupt_lifecycle_transitions_require_reasons() -> None:
    allocated_at = datetime(2026, 7, 24, 12, 59, 45, tzinfo=UTC)
    lifecycle = new_run_lifecycle(
        "20260724_125945",
        allocated_at=allocated_at,
    ).transition(
        RunLifecycleState.INITIALIZED,
        occurred_at=allocated_at + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="require a reason"):
        lifecycle.transition(
            RunLifecycleState.INCOMPLETE,
            occurred_at=allocated_at + timedelta(seconds=2),
        )

    incomplete = lifecycle.transition(
        RunLifecycleState.INCOMPLETE,
        occurred_at=allocated_at + timedelta(seconds=2),
        reason="cancelled before safe finalization",
    )
    assert incomplete.history[-1].reason == "cancelled before safe finalization"
    assert incomplete.is_terminal
    assert not incomplete.is_previous_run_eligible


def test_run_budget_preserves_finalization_reserve() -> None:
    clock = _Clock()
    budget = RunBudget(
        total_sec=60.0,
        finalization_reserve_sec=10.0,
        clock=clock,
    )

    stage = budget.allocate_stage(
        "compile",
        requested_sec=60.0,
        minimum_sec=1.0,
    )
    assert stage.granted_sec == pytest.approx(50.0)
    assert stage.deadline_monotonic == pytest.approx(150.0)
    assert stage.run_deadline_monotonic == pytest.approx(160.0)

    budget.release(stage)
    snapshot = budget.begin_finalization(reason="execution complete")
    assert snapshot.phase is BudgetPhase.FINALIZATION
    assert snapshot.remaining_finalization_sec == pytest.approx(60.0)

    denied_stage = budget.try_allocate_stage(
        "late-stage",
        requested_sec=1.0,
        minimum_sec=1.0,
    )
    assert not denied_stage.granted
    assert denied_stage.denial_reason is BudgetDenialReason.FINALIZATION_STARTED

    finalization = budget.allocate_finalization(
        "reports",
        requested_sec=20.0,
        minimum_sec=1.0,
    )
    assert finalization.granted_sec == pytest.approx(20.0)
    assert finalization.deadline_monotonic <= budget.run_deadline_monotonic


def test_run_budget_stops_new_work_when_execution_time_is_exhausted() -> None:
    clock = _Clock()
    budget = RunBudget(
        total_sec=20.0,
        finalization_reserve_sec=5.0,
        clock=clock,
    )

    clock.advance(15.0)
    denied = budget.try_allocate_stage(
        "compile",
        requested_sec=1.0,
        minimum_sec=1.0,
    )

    assert denied.denial_reason is BudgetDenialReason.EXECUTION_EXHAUSTED
    assert denied.snapshot.phase is BudgetPhase.FINALIZATION
    assert denied.snapshot.remaining_finalization_sec == pytest.approx(5.0)


def test_run_totals_enforce_conservation_invariants() -> None:
    totals = RunTotals(
        files_seen=6,
        files_included=5,
        files_excluded=1,
        files_ok=2,
        files_fail=1,
        files_error=1,
        files_skipped=1,
        direct_fail=1,
        downstream_fail=0,
        ambiguous_fail=0,
        excluded_noise=1,
        scenarios_seen=4,
        scenarios_ok=2,
        scenarios_fail=1,
        scenarios_error=0,
        scenarios_skipped=1,
        required_scenario_fail=1,
        overall_status=OverallStatus.FAIL,
    )

    assert totals.files_seen == totals.files_included + totals.files_excluded
    assert totals.scenarios_seen == (
        totals.scenarios_ok
        + totals.scenarios_fail
        + totals.scenarios_error
        + totals.scenarios_skipped
    )

    with pytest.raises(ValueError, match="files_seen"):
        RunTotals(
            files_seen=7,
            files_included=5,
            files_excluded=1,
            files_ok=2,
            files_fail=1,
            files_error=1,
            files_skipped=1,
            direct_fail=1,
            downstream_fail=0,
            ambiguous_fail=0,
            excluded_noise=1,
            scenarios_seen=0,
            scenarios_ok=0,
            scenarios_fail=0,
            scenarios_error=0,
            scenarios_skipped=0,
            required_scenario_fail=0,
            overall_status=OverallStatus.ERROR,
        )


def test_run_port_models_reject_unsafe_or_inconsistent_evidence(
    tmp_path: Path,
) -> None:
    run_id = validate_run_id("20260724_125945")
    absolute_file = (tmp_path / "manifest.json").resolve()

    entry = RunTreeEntry(
        relative_path=Path("raw/master.log"),
        kind=RunTreeEntryKind.FILE,
        size_bytes=12,
    )
    assert entry.relative_path == Path("raw/master.log")

    digest = FileDigest(
        path=absolute_file,
        size_bytes=12,
        sha256="a" * 64,
    )
    assert digest.sha256 == "a" * 64

    issue = ArtifactVerificationIssue(
        code="GF-WB-MANIFEST-001",
        message="required artifact is missing",
        path=absolute_file,
        required=True,
    )
    result = ArtifactVerificationResult(
        run_id=run_id,
        manifest_path=absolute_file,
        valid=False,
        checked_files=1,
        checked_bytes=12,
        issues=(issue,),
    )
    assert not result.valid

    with pytest.raises(ValueError, match="required issue"):
        ArtifactVerificationResult(
            run_id=run_id,
            manifest_path=absolute_file,
            valid=True,
            checked_files=1,
            checked_bytes=12,
            issues=(issue,),
        )

    with pytest.raises(ValueError, match="link_target"):
        RunTreeEntry(
            relative_path=Path("raw/master.log"),
            kind=RunTreeEntryKind.SYMLINK,
        )
