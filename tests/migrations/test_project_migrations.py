from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.projects.migrator import (
    ProjectMigrationActionKind,
    ProjectMigrationAsset,
    ProjectMigrationDestinationInspection,
    ProjectMigrationIssue,
    ProjectMigrationPlan,
    ProjectMigrationRequest,
    ProjectMigrationSourceInspection,
    ProjectMigrationStatus,
    ProjectMigrationStrategy,
    ProjectMigrationVerification,
    ProjectMigrationWriteReceipt,
    migrate_project,
    plan_project_migration,
)
from gf_wordbench.projects.models import (
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
)

pytestmark = pytest.mark.migration

_FIXED_TIME: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


@dataclass(slots=True)
class _FixedClock:
    value: datetime = _FIXED_TIME

    def utc_now(self) -> datetime:
        return self.value


@dataclass(slots=True)
class _FakeWorkspace:
    source: ProjectMigrationSourceInspection
    destination: ProjectMigrationDestinationInspection = field(
        default_factory=ProjectMigrationDestinationInspection
    )
    receipt: ProjectMigrationWriteReceipt = field(
        default_factory=lambda: ProjectMigrationWriteReceipt(
            changed=True,
            written=True,
        )
    )
    verification: ProjectMigrationVerification = field(
        default_factory=lambda: ProjectMigrationVerification(valid=True)
    )
    cancelled: bool = False
    apply_error: Exception | None = None
    verification_error: Exception | None = None
    rollback_error: Exception | None = None
    rollback_warning: str | None = None

    inspected_sources: list[Path] = field(default_factory=list)
    destination_requests: list[dict[str, object]] = field(default_factory=list)
    applied_plans: list[ProjectMigrationPlan] = field(default_factory=list)
    verified_plans: list[ProjectMigrationPlan] = field(default_factory=list)
    rollback_receipts: list[ProjectMigrationWriteReceipt] = field(
        default_factory=list
    )

    def inspect_source(
        self,
        source_root: Path,
    ) -> ProjectMigrationSourceInspection:
        self.inspected_sources.append(source_root)
        return self.source

    def inspect_destination(
        self,
        *,
        project_root: Path,
        migration_id: str,
        project_id: str,
        language_code: str,
        source_directory: Path,
        source_root: Path,
        strategy: ProjectMigrationStrategy,
    ) -> ProjectMigrationDestinationInspection:
        self.destination_requests.append(
            {
                "project_root": project_root,
                "migration_id": migration_id,
                "project_id": project_id,
                "language_code": language_code,
                "source_directory": source_directory,
                "source_root": source_root,
                "strategy": strategy,
            }
        )
        return self.destination

    def is_cancelled(self) -> bool:
        return self.cancelled

    def apply(
        self,
        plan: ProjectMigrationPlan,
    ) -> ProjectMigrationWriteReceipt:
        self.applied_plans.append(plan)
        if self.apply_error is not None:
            raise self.apply_error
        return self.receipt

    def verify(
        self,
        plan: ProjectMigrationPlan,
    ) -> ProjectMigrationVerification:
        self.verified_plans.append(plan)
        if self.verification_error is not None:
            raise self.verification_error
        return self.verification

    def rollback(
        self,
        receipt: ProjectMigrationWriteReceipt,
    ) -> str | None:
        self.rollback_receipts.append(receipt)
        if self.rollback_error is not None:
            raise self.rollback_error
        return self.rollback_warning


def _request(
    tmp_path: Path,
    *,
    dry_run: bool = False,
    source_root: Path | None = None,
    project_root: Path | None = None,
) -> ProjectMigrationRequest:
    resolved_source = (
        source_root
        if source_root is not None
        else (tmp_path / "legacy-language").resolve()
    )
    resolved_project = (
        project_root
        if project_root is not None
        else (tmp_path / "project").resolve()
    )

    return ProjectMigrationRequest(
        migration_id="migration-example-001",
        source_root=resolved_source,
        project_root=resolved_project,
        project_id="example",
        project_name="Example Language",
        language_code="ex",
        source_directory=Path("lib/src/example"),
        strategy=ProjectMigrationStrategy.COPY,
        source_glob="*.gf",
        include_regex=r".*\.gf$",
        exclude_regex=r"(?:^|/)attic(?:/|$)",
        gf_path_parts=("lib/src/example", "lib/src/common"),
        minimum_version="3.11",
        entrypoints=(Path("GrammarEx.gf"),),
        checkpoints=(Path("MorphologyEx.gf"),),
        required_scenarios=("smoke",),
        optional_scenarios=("regression",),
        release_requires_pgf=True,
        dry_run=dry_run,
    )


def _workspace(
    *,
    destination_matches: bool = False,
    source_issues: tuple[ProjectMigrationIssue, ...] = (),
) -> _FakeWorkspace:
    return _FakeWorkspace(
        source=ProjectMigrationSourceInspection(
            assets=(
                ProjectMigrationAsset(
                    relative_path=Path("GrammarEx.gf"),
                    size_bytes=128,
                ),
                ProjectMigrationAsset(
                    relative_path=Path("README.md"),
                    copy_to_managed_source=False,
                    size_bytes=64,
                ),
            ),
            issues=source_issues,
        ),
        destination=ProjectMigrationDestinationInspection(
            matches_request=destination_matches
        ),
    )


def test_planning_is_read_only_and_builds_the_canonical_copy_plan(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    workspace = _workspace()

    plan = plan_project_migration(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert plan.migration_id == request.migration_id
    assert plan.created_at == _FIXED_TIME
    assert plan.source_schema == "gf-language-tree"
    assert plan.source_version == "unversioned"
    assert plan.target_schema == str(PROJECT_SCHEMA_ID)
    assert plan.target_version == PROJECT_SCHEMA_VERSION
    assert not plan.already_applied
    assert plan.config.identity.id == request.project_id
    assert plan.config.identity.language_code == request.language_code
    assert plan.config.sources.directory == request.source_directory
    assert plan.config.modules.entrypoints == request.entrypoints
    assert plan.config.validation.required_scenarios == (
        request.required_scenarios
    )

    assert tuple(action.kind for action in plan.actions) == (
        ProjectMigrationActionKind.INITIALIZE_PROJECT,
        ProjectMigrationActionKind.COPY_FILE,
        ProjectMigrationActionKind.WRITE_PROJECT_CONFIG,
        ProjectMigrationActionKind.VERIFY_PROJECT,
    )
    copied = plan.actions[1]
    assert copied.source == request.source_root / "GrammarEx.gf"
    assert copied.destination == (
        request.project_root
        / request.source_directory
        / "GrammarEx.gf"
    )

    assert workspace.inspected_sources == [request.source_root]
    assert len(workspace.destination_requests) == 1
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_successful_migration_applies_then_verifies_and_reports_backup(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    backup = (tmp_path / "backups" / "project-before-migration").resolve()
    workspace = _workspace()
    workspace.receipt = ProjectMigrationWriteReceipt(
        changed=True,
        written=True,
        backup_path=backup,
    )

    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert result.status is ProjectMigrationStatus.MIGRATED_WITH_WARNINGS
    assert result.changed
    assert result.written
    assert result.backup_path == backup.as_posix()
    assert result.source_path == request.source_root.as_posix()
    assert result.destination_path == request.project_root.as_posix()
    assert result.target_schema == str(PROJECT_SCHEMA_ID)
    assert result.target_version == PROJECT_SCHEMA_VERSION
    assert result.manual_actions
    assert len(workspace.applied_plans) == 1
    assert workspace.verified_plans == workspace.applied_plans
    assert workspace.rollback_receipts == []


def test_dry_run_never_applies_or_verifies_the_plan(tmp_path: Path) -> None:
    request = _request(tmp_path, dry_run=True)
    workspace = _workspace()

    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert result.status is ProjectMigrationStatus.NOT_NEEDED
    assert not result.changed
    assert not result.written
    assert any("Dry run completed" in warning for warning in result.warnings)
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_matching_destination_is_idempotent_and_requires_no_write(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    workspace = _workspace(destination_matches=True)

    plan = plan_project_migration(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )
    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert plan.already_applied
    assert plan.actions == ()
    assert plan.manual_actions == ()
    assert result.status is ProjectMigrationStatus.NOT_NEEDED
    assert not result.changed
    assert not result.written
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_blockers_prevent_publication(tmp_path: Path) -> None:
    shared_root = (tmp_path / "same-root").resolve()
    request = _request(
        tmp_path,
        source_root=shared_root,
        project_root=shared_root,
    )
    workspace = _workspace()

    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert result.status is ProjectMigrationStatus.BLOCKED
    assert any(
        "must not be the destination project root" in warning
        for warning in result.warnings
    )
    assert not result.changed
    assert not result.written
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_failed_verification_rolls_back_the_published_destination(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    backup = (tmp_path / "backup" / "active-project").resolve()
    workspace = _workspace()
    workspace.receipt = ProjectMigrationWriteReceipt(
        changed=True,
        written=True,
        backup_path=backup,
    )
    workspace.verification = ProjectMigrationVerification(
        valid=False,
        blockers=("The migrated project failed canonical validation.",),
    )

    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert not result.changed
    assert not result.written
    assert result.backup_path == backup.as_posix()
    assert any(
        "failed canonical validation" in warning
        for warning in result.warnings
    )
    assert len(workspace.applied_plans) == 1
    assert len(workspace.verified_plans) == 1
    assert workspace.rollback_receipts == [workspace.receipt]


def test_failed_rollback_reports_that_published_changes_remain(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    workspace = _workspace()
    workspace.verification = ProjectMigrationVerification(
        valid=False,
        blockers=("Verification failed.",),
    )
    workspace.rollback_warning = "Rollback could not restore the prior project."

    result = migrate_project(
        request,
        workspace=workspace,
        clock=_FixedClock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert result.changed
    assert result.written
    assert "Rollback could not restore" in result.warnings[-1]
    assert workspace.rollback_receipts == [workspace.receipt]
