"""Unit tests for explicit active-project migration planning and execution."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    ProjectMigrator,
    migrate_project,
    plan_project_migration,
)
from gf_wordbench.projects.schema import PROJECT_SCHEMA_ID, PROJECT_SCHEMA_VERSION

_FIXED_TIME: Final = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


@dataclass(slots=True)
class _Clock:
    value: datetime = _FIXED_TIME

    def utc_now(self) -> datetime:
        return self.value


@dataclass(slots=True)
class _Workspace:
    source: ProjectMigrationSourceInspection = field(
        default_factory=ProjectMigrationSourceInspection
    )
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
    cancelled_values: list[bool] = field(default_factory=lambda: [False])
    apply_error: Exception | None = None
    verification_error: Exception | None = None
    rollback_error: Exception | None = None
    rollback_warning: str | None = None

    calls: list[str] = field(default_factory=list)
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
        self.calls.append("inspect_source")
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
        self.calls.append("inspect_destination")
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
        self.calls.append("is_cancelled")
        if len(self.cancelled_values) > 1:
            return self.cancelled_values.pop(0)
        return self.cancelled_values[0]

    def apply(
        self,
        plan: ProjectMigrationPlan,
    ) -> ProjectMigrationWriteReceipt:
        self.calls.append("apply")
        self.applied_plans.append(plan)
        if self.apply_error is not None:
            raise self.apply_error
        return self.receipt

    def verify(
        self,
        plan: ProjectMigrationPlan,
    ) -> ProjectMigrationVerification:
        self.calls.append("verify")
        self.verified_plans.append(plan)
        if self.verification_error is not None:
            raise self.verification_error
        return self.verification

    def rollback(
        self,
        receipt: ProjectMigrationWriteReceipt,
    ) -> str | None:
        self.calls.append("rollback")
        self.rollback_receipts.append(receipt)
        if self.rollback_error is not None:
            raise self.rollback_error
        return self.rollback_warning


def _request(
    tmp_path: Path,
    **overrides: object,
) -> ProjectMigrationRequest:
    request = ProjectMigrationRequest(
        migration_id="migration-example-001",
        source_root=(tmp_path / "legacy language").resolve(),
        project_root=(tmp_path / "active project").resolve(),
        project_id="example-language",
        project_name="Example Language",
        language_code="ex",
        source_directory=Path("lib/src/example"),
        strategy=ProjectMigrationStrategy.COPY,
        source_glob="*.gf",
        include_regex=r".*\.gf$",
        exclude_regex=r"(?:^|/)attic(?:/|$)",
        gf_path_parts=(
            "lib/src/example",
            "lib/src/common",
        ),
        minimum_version="3.11",
        entrypoints=(Path("GrammarEx.gf"),),
        checkpoints=(Path("MorphologyEx.gf"),),
        required_scenarios=("smoke",),
        optional_scenarios=("regression",),
        release_requires_pgf=True,
    )
    return replace(request, **overrides)


def _source_inspection(
    *,
    issues: tuple[ProjectMigrationIssue, ...] = (),
) -> ProjectMigrationSourceInspection:
    return ProjectMigrationSourceInspection(
        assets=(
            ProjectMigrationAsset(
                relative_path=Path("GrammarEx.gf"),
                size_bytes=128,
            ),
            ProjectMigrationAsset(
                relative_path=Path("sub/ConcreteEx.gf"),
                size_bytes=256,
            ),
            ProjectMigrationAsset(
                relative_path=Path("README.md"),
                copy_to_managed_source=False,
                size_bytes=64,
            ),
        ),
        issues=issues,
    )


def _workspace(
    *,
    source_issues: tuple[ProjectMigrationIssue, ...] = (),
    destination_issues: tuple[ProjectMigrationIssue, ...] = (),
    destination_matches: bool = False,
) -> _Workspace:
    return _Workspace(
        source=_source_inspection(issues=source_issues),
        destination=ProjectMigrationDestinationInspection(
            matches_request=destination_matches,
            issues=destination_issues,
        ),
    )


def _kinds(plan: ProjectMigrationPlan) -> tuple[ProjectMigrationActionKind, ...]:
    return tuple(action.kind for action in plan.actions)


def test_public_enums_use_documented_wire_values() -> None:
    assert tuple(ProjectMigrationStrategy) == (
        ProjectMigrationStrategy.COPY,
        ProjectMigrationStrategy.EXTERNAL,
        ProjectMigrationStrategy.HISTORY_IMPORT,
    )
    assert [item.value for item in ProjectMigrationStrategy] == [
        "copy",
        "external",
        "history-import",
    ]
    assert [item.value for item in ProjectMigrationStatus] == [
        "not-needed",
        "blocked",
        "cancelled",
        "migrated",
        "migrated-with-warnings",
        "failed",
    ]


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("."),
        Path("../Grammar.gf"),
        Path("folder/../Grammar.gf"),
        Path("/absolute/Grammar.gf"),
        Path("C:/absolute/Grammar.gf"),
    ],
)
def test_migration_asset_rejects_noncontained_paths(
    relative_path: Path,
) -> None:
    with pytest.raises(ValueError, match="relative path|contained child"):
        ProjectMigrationAsset(relative_path=relative_path)


def test_migration_asset_validates_flags_and_size() -> None:
    with pytest.raises(TypeError, match="copy_to_managed_source"):
        ProjectMigrationAsset(
            relative_path=Path("Grammar.gf"),
            copy_to_managed_source=1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="non-negative"):
        ProjectMigrationAsset(
            relative_path=Path("Grammar.gf"),
            size_bytes=-1,
        )


def test_issue_factories_and_plan_projections_preserve_classification(
    tmp_path: Path,
) -> None:
    issues = (
        ProjectMigrationIssue.blocker(
            code="migration.blocked",
            message="Unsafe source layout.",
        ),
        ProjectMigrationIssue.warning(
            code="migration.review",
            message="Review the entrypoints.",
        ),
        ProjectMigrationIssue.loss(
            code="migration.loss",
            message="One legacy fact could not be preserved.",
        ),
    )
    workspace = _workspace(source_issues=issues)

    plan = plan_project_migration(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert plan.blocker_messages == ("Unsafe source layout.",)
    assert plan.warning_messages == ("Review the entrypoints.",)
    assert plan.loss_messages == (
        "One legacy fact could not be preserved.",
    )


@pytest.mark.parametrize(
    ("field_name", "value", "expected"),
    [
        ("gf_path_parts", "lib/src", "iterable of strings"),
        ("entrypoints", "Grammar.gf", "iterable of paths"),
        ("checkpoints", b"Grammar.gf", "iterable of paths"),
        ("required_scenarios", "smoke", "iterable of strings"),
        ("optional_scenarios", bytearray(b"smoke"), "iterable of strings"),
    ],
)
def test_request_rejects_scalar_collection_values(
    tmp_path: Path,
    field_name: str,
    value: object,
    expected: str,
) -> None:
    with pytest.raises(TypeError, match=expected):
        _request(tmp_path, **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("release_requires_pgf", 1),
        ("dry_run", 0),
    ],
)
def test_request_requires_real_boolean_flags(
    tmp_path: Path,
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(TypeError, match="boolean"):
        _request(tmp_path, **{field_name: value})


def test_copy_plan_is_read_only_complete_and_deterministic(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    workspace = _workspace()

    plan = ProjectMigrator(
        workspace=workspace,
        clock=_Clock(),
    ).plan(request)

    assert plan.migration_id == request.migration_id
    assert plan.created_at == _FIXED_TIME
    assert plan.source_schema == "gf-language-tree"
    assert plan.source_version == "unversioned"
    assert plan.target_schema == str(PROJECT_SCHEMA_ID)
    assert plan.target_version == PROJECT_SCHEMA_VERSION
    assert plan.request == request
    assert plan.config.identity.id == request.project_id
    assert plan.config.identity.name == request.project_name
    assert plan.config.identity.language_code == request.language_code
    assert plan.config.sources.directory == request.source_directory
    assert plan.config.sources.glob == request.source_glob
    assert plan.config.modules.entrypoints == request.entrypoints
    assert plan.config.modules.checkpoints == request.checkpoints
    assert plan.config.validation.required_scenarios == request.required_scenarios
    assert plan.config.validation.optional_scenarios == request.optional_scenarios
    assert plan.config.validation.release_requires_pgf is True

    assert _kinds(plan) == (
        ProjectMigrationActionKind.INITIALIZE_PROJECT,
        ProjectMigrationActionKind.COPY_FILE,
        ProjectMigrationActionKind.COPY_FILE,
        ProjectMigrationActionKind.WRITE_PROJECT_CONFIG,
        ProjectMigrationActionKind.VERIFY_PROJECT,
    )
    assert [
        action.asset.relative_path
        for action in plan.actions
        if action.asset is not None
    ] == [
        Path("GrammarEx.gf"),
        Path("sub/ConcreteEx.gf"),
    ]
    assert plan.actions[1].source == request.source_root / "GrammarEx.gf"
    assert plan.actions[1].destination == (
        request.project_root
        / request.source_directory
        / "GrammarEx.gf"
    )
    assert workspace.calls == ["inspect_source", "inspect_destination"]
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_plan_normalizes_and_deduplicates_declared_gf_paths(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        gf_path_parts=(
            "lib/src/example",
            "lib/src/common",
            "lib/src/example",
        ),
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    assert plan.request.gf_path_parts == (
        "lib/src/example",
        "lib/src/common",
    )
    assert plan.config.gf.path_parts == plan.request.gf_path_parts


def test_valid_external_strategy_references_project_relative_source(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "active project").resolve()
    source_directory = Path("vendor/external-language")
    source_root = project_root / source_directory
    request = _request(
        tmp_path,
        project_root=project_root,
        source_root=source_root,
        source_directory=source_directory,
        strategy=ProjectMigrationStrategy.EXTERNAL,
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    assert plan.blocker_messages == ()
    assert _kinds(plan) == (
        ProjectMigrationActionKind.INITIALIZE_PROJECT,
        ProjectMigrationActionKind.REFERENCE_EXISTING_SOURCE,
        ProjectMigrationActionKind.WRITE_PROJECT_CONFIG,
        ProjectMigrationActionKind.VERIFY_PROJECT,
    )
    reference = plan.actions[1]
    assert reference.source == source_root
    assert reference.destination == source_root


def test_external_strategy_rejects_source_outside_project_root(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        strategy=ProjectMigrationStrategy.EXTERNAL,
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    assert any(
        issue.code == "migration.external_source_not_project_relative"
        for issue in plan.issues
    )
    assert plan.blocker_messages


def test_external_strategy_rejects_mismatched_source_directory(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "active project").resolve()
    request = _request(
        tmp_path,
        project_root=project_root,
        source_root=project_root / "actual/source",
        source_directory=Path("declared/source"),
        strategy=ProjectMigrationStrategy.EXTERNAL,
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    mismatch = next(
        issue
        for issue in plan.issues
        if issue.code == "migration.external_source_mismatch"
    )
    assert mismatch.severity == "blocker"
    assert "expected 'actual/source'" in mismatch.message


def test_history_import_has_explicit_action_warning_and_manual_evidence(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        strategy=ProjectMigrationStrategy.HISTORY_IMPORT,
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    assert ProjectMigrationActionKind.IMPORT_WITH_HISTORY in _kinds(plan)
    assert any(
        issue.code == "migration.history_import_requires_adapter"
        and issue.severity == "warning"
        for issue in plan.issues
    )
    assert plan.manual_actions[0].startswith("Record the source repository")


def test_copy_strategy_blocks_destination_nested_inside_source(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "legacy").resolve()
    project_root = source_root / "generated-project"
    request = _request(
        tmp_path,
        source_root=source_root,
        project_root=project_root,
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    assert any(
        issue.code == "migration.destination_inside_source"
        for issue in plan.issues
    )


def test_missing_entrypoints_and_required_scenarios_are_visible_tasks(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        entrypoints=(),
        required_scenarios=(),
    )

    plan = plan_project_migration(
        request,
        workspace=_workspace(),
        clock=_Clock(),
    )

    codes = {issue.code for issue in plan.issues}
    assert "migration.entrypoints_pending" in codes
    assert "migration.required_scenarios_pending" in codes
    assert any("Declare and review" in item for item in plan.manual_actions)


def test_duplicate_issues_are_deduplicated_without_reordering(
    tmp_path: Path,
) -> None:
    duplicate = ProjectMigrationIssue.warning(
        code="migration.review",
        message="Review the source inventory.",
        path=Path("GrammarEx.gf"),
    )
    other = ProjectMigrationIssue.loss(
        code="migration.loss",
        message="Legacy ownership is unknown.",
    )
    workspace = _workspace(
        source_issues=(duplicate, other),
        destination_issues=(duplicate,),
    )

    plan = plan_project_migration(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert plan.issues[:2] == (duplicate, other)
    assert plan.issues.count(duplicate) == 1


def test_matching_destination_is_idempotent(
    tmp_path: Path,
) -> None:
    workspace = _workspace(destination_matches=True)

    plan = plan_project_migration(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )
    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert plan.already_applied is True
    assert plan.actions == ()
    assert plan.manual_actions == ()
    assert result.status is ProjectMigrationStatus.NOT_NEEDED
    assert result.changed is False
    assert result.written is False
    assert "apply" not in workspace.calls
    assert "verify" not in workspace.calls


def test_blocker_prevents_apply_verify_and_rollback(
    tmp_path: Path,
) -> None:
    blocker = ProjectMigrationIssue.blocker(
        code="migration.unsafe_source",
        message="The source inventory contains an unsafe path.",
    )
    workspace = _workspace(source_issues=(blocker,))

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.BLOCKED
    assert result.warnings == (blocker.message,)
    assert result.changed is False
    assert result.written is False
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_dry_run_returns_plan_outcome_without_publication(
    tmp_path: Path,
) -> None:
    workspace = _workspace()

    result = migrate_project(
        _request(tmp_path, dry_run=True),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.NOT_NEEDED
    assert result.changed is False
    assert result.written is False
    assert result.manual_actions
    assert any("Dry run completed" in warning for warning in result.warnings)
    assert "is_cancelled" not in workspace.calls
    assert "apply" not in workspace.calls
    assert "verify" not in workspace.calls


def test_cancellation_before_publication_returns_cancelled(
    tmp_path: Path,
) -> None:
    workspace = _workspace()
    workspace.cancelled_values = [True]

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.CANCELLED
    assert result.changed is False
    assert result.written is False
    assert workspace.calls[-1] == "is_cancelled"
    assert workspace.applied_plans == []
    assert workspace.verified_plans == []


def test_apply_failure_is_bounded_and_does_not_attempt_rollback(
    tmp_path: Path,
) -> None:
    workspace = _workspace()
    workspace.apply_error = OSError("publication failed")

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert result.warnings[-1] == "migration write failed: publication failed"
    assert result.changed is False
    assert result.written is False
    assert len(workspace.applied_plans) == 1
    assert workspace.verified_plans == []
    assert workspace.rollback_receipts == []


def test_verification_exception_rolls_back_publication(
    tmp_path: Path,
) -> None:
    backup = (tmp_path / "backup" / "active-project").resolve()
    workspace = _workspace()
    workspace.receipt = ProjectMigrationWriteReceipt(
        changed=True,
        written=True,
        backup_path=backup,
    )
    workspace.verification_error = RuntimeError("verification crashed")

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert result.changed is False
    assert result.written is False
    assert result.backup_path == backup.as_posix()
    assert "migration verification failed: verification crashed" in result.warnings
    assert workspace.rollback_receipts == [workspace.receipt]


def test_invalid_verification_preserves_losses_and_rolls_back(
    tmp_path: Path,
) -> None:
    workspace = _workspace()
    workspace.verification = ProjectMigrationVerification(
        valid=False,
        blockers=("Canonical project validation failed.",),
        warnings=("A generated document needs review.",),
        losses=("One legacy ownership fact was not recoverable.",),
    )

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert result.changed is False
    assert result.written is False
    assert result.losses == (
        "One legacy ownership fact was not recoverable.",
    )
    assert "Canonical project validation failed." in result.warnings
    assert workspace.rollback_receipts == [workspace.receipt]


@pytest.mark.parametrize(
    ("rollback_warning", "rollback_error", "expected_warning"),
    [
        (
            "Rollback could not restore the prior project.",
            None,
            "Rollback could not restore the prior project.",
        ),
        (
            None,
            OSError("backup unavailable"),
            "migration rollback failed: backup unavailable",
        ),
    ],
)
def test_rollback_failure_reports_published_changes_as_remaining(
    tmp_path: Path,
    rollback_warning: str | None,
    rollback_error: Exception | None,
    expected_warning: str,
) -> None:
    workspace = _workspace()
    workspace.verification = ProjectMigrationVerification(
        valid=False,
        blockers=("Verification failed.",),
    )
    workspace.rollback_warning = rollback_warning
    workspace.rollback_error = rollback_error

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.FAILED
    assert result.changed is True
    assert result.written is True
    assert expected_warning in result.warnings


def test_cancellation_after_successful_verification_retains_destination(
    tmp_path: Path,
) -> None:
    workspace = _workspace()
    workspace.cancelled_values = [False, True]

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.MIGRATED_WITH_WARNINGS
    assert result.changed is True
    assert result.written is True
    assert any(
        "Cancellation was observed after publication" in warning
        for warning in result.warnings
    )
    assert workspace.rollback_receipts == []


def test_successful_migration_reports_canonical_contract_and_backup(
    tmp_path: Path,
) -> None:
    backup = (tmp_path / "backup" / "before-migration").resolve()
    workspace = _workspace()
    workspace.receipt = ProjectMigrationWriteReceipt(
        changed=True,
        written=True,
        backup_path=backup,
    )

    result = migrate_project(
        _request(tmp_path),
        workspace=workspace,
        clock=_Clock(),
    )

    assert result.status is ProjectMigrationStatus.MIGRATED_WITH_WARNINGS
    assert result.source_schema == "gf-language-tree"
    assert result.source_version == "unversioned"
    assert result.target_schema == str(PROJECT_SCHEMA_ID)
    assert result.target_version == PROJECT_SCHEMA_VERSION
    assert result.source_path.endswith("legacy language")
    assert result.destination_path.endswith("active project")
    assert result.backup_path == backup.as_posix()
    assert result.manual_actions
    assert workspace.calls == [
        "inspect_source",
        "inspect_destination",
        "is_cancelled",
        "apply",
        "verify",
        "is_cancelled",
    ]


def test_naive_clock_is_rejected_by_plan_contract(
    tmp_path: Path,
) -> None:
    clock = _Clock(datetime(2026, 7, 25, 12, 0))

    with pytest.raises(ValueError, match="timezone-aware"):
        plan_project_migration(
            _request(tmp_path),
            workspace=_workspace(),
            clock=clock,
        )


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"source_root": Path("relative-source")}, "source_root must be an absolute"),
        ({"project_root": Path("relative-project")}, "project_root must be an absolute"),
        (
            {
                "required_scenarios": ("smoke",),
                "optional_scenarios": ("smoke",),
            },
            "must not overlap",
        ),
        (
            {"source_directory": Path("../outside")},
            "sources.directory",
        ),
        (
            {"migration_id": " migration "},
            "single-line",
        ),
    ],
)
def test_invalid_request_contract_is_rejected_before_workspace_use(
    tmp_path: Path,
    overrides: dict[str, object],
    expected: str,
) -> None:
    workspace = _workspace()

    with pytest.raises((TypeError, ValueError), match=expected):
        plan_project_migration(
            _request(tmp_path, **overrides),
            workspace=workspace,
            clock=_Clock(),
        )

    assert workspace.calls == []
