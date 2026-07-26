"""Explicit migration of one active GF language project.

Planning is read-only. Applying a plan is explicit, non-destructive to the
source, atomic at the destination boundary, and followed by verification.
Normal project loading and validation must never invoke this service implicitly.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum, unique
from pathlib import Path, PureWindowsPath
from typing import Final, Literal, TypeAlias

from gf_wordbench.kernel.paths import ContainmentMode, relative_portable_path

from .models import (
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from .paths import ProjectPaths, resolve_source_root
from .policies import (
    deduplicate_declared_path_parts,
    validate_language_code,
    validate_minimum_version,
    validate_module_targets,
    validate_optional_regex,
    validate_portable_project_path,
    validate_project_id,
    validate_project_name,
    validate_release_requires_pgf,
    validate_scenario_policy,
    validate_source_glob,
)
from .ports import ClockPort, ProjectMigrationWorkspacePort
from .schema import PROJECT_SCHEMA_ID, PROJECT_SCHEMA_VERSION

_SOURCE_SCHEMA: Final[str] = "gf-language-tree"
_SOURCE_VERSION: Final[str] = "unversioned"
_MAX_FAILURE_MESSAGE_LENGTH: Final[int] = 500

MigrationIssueSeverity: TypeAlias = Literal["blocker", "warning", "loss"]


@unique
class ProjectMigrationStrategy(StrEnum):
    COPY = "copy"
    EXTERNAL = "external"
    HISTORY_IMPORT = "history-import"


@unique
class ProjectMigrationActionKind(StrEnum):
    INITIALIZE_PROJECT = "initialize-project"
    COPY_FILE = "copy-file"
    REFERENCE_EXISTING_SOURCE = "reference-existing-source"
    IMPORT_WITH_HISTORY = "import-with-history"
    WRITE_PROJECT_CONFIG = "write-project-config"
    VERIFY_PROJECT = "verify-project"


@unique
class ProjectMigrationStatus(StrEnum):
    NOT_NEEDED = "not-needed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    MIGRATED = "migrated"
    MIGRATED_WITH_WARNINGS = "migrated-with-warnings"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProjectMigrationAsset:
    """One inspected source asset relevant to migration."""

    relative_path: Path
    copy_to_managed_source: bool = True
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relative_path",
            _require_relative_path(
                self.relative_path,
                field="relative_path",
            ),
        )

        if type(self.copy_to_managed_source) is not bool:
            raise TypeError("copy_to_managed_source must be a boolean")

        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")


@dataclass(frozen=True, slots=True)
class ProjectMigrationIssue:
    """Structured migration blocker, warning, or expected loss."""

    severity: MigrationIssueSeverity
    code: str
    message: str
    path: Path | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"blocker", "warning", "loss"}:
            raise ValueError(
                f"unsupported migration severity: {self.severity!r}"
            )

        object.__setattr__(
            self,
            "code",
            _single_line(self.code, field="code"),
        )
        object.__setattr__(
            self,
            "message",
            _single_line(self.message, field="message"),
        )

        if self.path is not None:
            object.__setattr__(self, "path", Path(self.path))

    @classmethod
    def blocker(
        cls,
        *,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> ProjectMigrationIssue:
        return cls(
            severity="blocker",
            code=code,
            message=message,
            path=path,
        )

    @classmethod
    def warning(
        cls,
        *,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> ProjectMigrationIssue:
        return cls(
            severity="warning",
            code=code,
            message=message,
            path=path,
        )

    @classmethod
    def loss(
        cls,
        *,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> ProjectMigrationIssue:
        return cls(
            severity="loss",
            code=code,
            message=message,
            path=path,
        )


@dataclass(frozen=True, slots=True)
class ProjectMigrationSourceInspection:
    """Read-only facts discovered from the migration source."""

    assets: tuple[ProjectMigrationAsset, ...] = ()
    issues: tuple[ProjectMigrationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectMigrationDestinationInspection:
    """Read-only facts discovered from the migration destination."""

    matches_request: bool = False
    issues: tuple[ProjectMigrationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectMigrationWriteReceipt:
    """Facts returned after atomic destination publication."""

    changed: bool
    written: bool
    backup_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ProjectMigrationVerification:
    """Result of verifying the published migration destination."""

    valid: bool
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    losses: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectMigrationRequest:
    """Complete explicit request for one active-project migration."""

    migration_id: str
    source_root: Path
    project_root: Path
    project_id: str
    project_name: str
    language_code: str
    source_directory: Path

    strategy: ProjectMigrationStrategy = ProjectMigrationStrategy.COPY

    source_glob: str = "*.gf"
    include_regex: str = ""
    exclude_regex: str = ""

    gf_path_parts: tuple[str, ...] = ()
    minimum_version: str = ""

    entrypoints: tuple[Path, ...] = ()
    checkpoints: tuple[Path, ...] = ()

    required_scenarios: tuple[str, ...] = ()
    optional_scenarios: tuple[str, ...] = ()
    release_requires_pgf: bool = False

    dry_run: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_root",
            Path(self.source_root),
        )
        object.__setattr__(
            self,
            "project_root",
            Path(self.project_root),
        )
        object.__setattr__(
            self,
            "source_directory",
            Path(self.source_directory),
        )
        object.__setattr__(
            self,
            "strategy",
            ProjectMigrationStrategy(self.strategy),
        )
        object.__setattr__(
            self,
            "gf_path_parts",
            _string_tuple(
                self.gf_path_parts,
                field="gf_path_parts",
            ),
        )
        object.__setattr__(
            self,
            "entrypoints",
            _path_tuple(
                self.entrypoints,
                field="entrypoints",
            ),
        )
        object.__setattr__(
            self,
            "checkpoints",
            _path_tuple(
                self.checkpoints,
                field="checkpoints",
            ),
        )
        object.__setattr__(
            self,
            "required_scenarios",
            _string_tuple(
                self.required_scenarios,
                field="required_scenarios",
            ),
        )
        object.__setattr__(
            self,
            "optional_scenarios",
            _string_tuple(
                self.optional_scenarios,
                field="optional_scenarios",
            ),
        )

        if type(self.release_requires_pgf) is not bool:
            raise TypeError("release_requires_pgf must be a boolean")

        if type(self.dry_run) is not bool:
            raise TypeError("dry_run must be a boolean")


@dataclass(frozen=True, slots=True)
class ProjectMigrationAction:
    """One explicit operation in a migration plan."""

    kind: ProjectMigrationActionKind
    source: Path | None
    destination: Path
    asset: ProjectMigrationAsset | None
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "kind",
            ProjectMigrationActionKind(self.kind),
        )

        if self.source is not None:
            object.__setattr__(
                self,
                "source",
                Path(self.source),
            )

        object.__setattr__(
            self,
            "destination",
            Path(self.destination),
        )
        object.__setattr__(
            self,
            "description",
            _single_line(
                self.description,
                field="description",
            ),
        )


@dataclass(frozen=True, slots=True)
class ProjectMigrationPlan:
    """Complete immutable plan for one project migration."""

    migration_id: str
    created_at: datetime
    request: ProjectMigrationRequest

    source_schema: str
    source_version: str
    target_schema: str
    target_version: str

    assets: tuple[ProjectMigrationAsset, ...]
    config: ProjectConfig
    actions: tuple[ProjectMigrationAction, ...]
    issues: tuple[ProjectMigrationIssue, ...]
    manual_actions: tuple[str, ...]

    rollback: str
    already_applied: bool = False

    def __post_init__(self) -> None:
        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("created_at must be timezone-aware")

    @property
    def blocker_messages(self) -> tuple[str, ...]:
        return tuple(
            issue.message
            for issue in self.issues
            if issue.severity == "blocker"
        )

    @property
    def warning_messages(self) -> tuple[str, ...]:
        return tuple(
            issue.message
            for issue in self.issues
            if issue.severity == "warning"
        )

    @property
    def loss_messages(self) -> tuple[str, ...]:
        return tuple(
            issue.message
            for issue in self.issues
            if issue.severity == "loss"
        )


@dataclass(frozen=True, slots=True)
class ProjectMigrationResult:
    """Canonical outcome of an attempted project migration."""

    migration_id: str

    source_schema: str
    source_version: str
    target_schema: str
    target_version: str

    source_path: str
    destination_path: str

    status: ProjectMigrationStatus
    warnings: tuple[str, ...] = ()
    losses: tuple[str, ...] = ()
    manual_actions: tuple[str, ...] = ()

    changed: bool = False
    written: bool = False
    backup_path: str | None = None


class ProjectMigrator:
    """Plan, apply, verify, and roll back an active-project migration."""

    __slots__ = ("_clock", "_workspace")

    def __init__(
        self,
        *,
        workspace: ProjectMigrationWorkspacePort,
        clock: ClockPort,
    ) -> None:
        self._workspace = workspace
        self._clock = clock

    def plan(
        self,
        request: ProjectMigrationRequest,
    ) -> ProjectMigrationPlan:
        """Return a complete migration plan without writing canonical assets."""

        normalized = _normalize_request(request)
        project_paths = ProjectPaths.from_root(
            normalized.project_root
        )
        target_source_root = resolve_source_root(
            project_paths.root,
            normalized.source_directory,
        )

        source = self._workspace.inspect_source(
            normalized.source_root
        )
        destination = self._workspace.inspect_destination(
            project_root=project_paths.root,
            migration_id=normalized.migration_id,
            project_id=normalized.project_id,
            language_code=normalized.language_code,
            source_directory=normalized.source_directory,
            source_root=normalized.source_root,
            strategy=normalized.strategy,
        )

        issues = [
            *source.issues,
            *destination.issues,
        ]
        issues.extend(
            _validate_strategy(
                normalized,
                project_root=project_paths.root,
                target_source_root=target_source_root,
            )
        )
        _validate_external_mapping(
            normalized,
            project_paths=project_paths,
            issues=issues,
        )

        manual_actions: list[str] = []
        config = _build_config_draft(
            normalized,
            issues=issues,
            manual_actions=manual_actions,
        )

        already_applied = destination.matches_request
        actions = (
            ()
            if already_applied
            else tuple(
                _build_actions(
                    normalized,
                    project_paths=project_paths,
                    target_source_root=target_source_root,
                    assets=source.assets,
                )
            )
        )

        if not already_applied:
            manual_actions.extend(
                _required_manual_actions(normalized.strategy)
            )

        return ProjectMigrationPlan(
            migration_id=normalized.migration_id,
            created_at=self._clock.utc_now(),
            request=normalized,
            source_schema=_SOURCE_SCHEMA,
            source_version=_SOURCE_VERSION,
            target_schema=str(PROJECT_SCHEMA_ID),
            target_version=PROJECT_SCHEMA_VERSION,
            assets=tuple(source.assets),
            config=config,
            actions=actions,
            issues=tuple(_deduplicate_issues(issues)),
            manual_actions=tuple(
                _deduplicate_text(manual_actions)
            ),
            rollback=(
                "The source remains untouched. Staged output is discarded "
                "before publication on failure; after publication, restore "
                "the atomic destination backup recorded by the write receipt."
            ),
            already_applied=already_applied,
        )

    def migrate(
        self,
        request: ProjectMigrationRequest,
    ) -> ProjectMigrationResult:
        """Apply an authorized plan and return the migration result."""

        plan = self.plan(request)
        warnings = list(plan.warning_messages)
        losses = list(plan.loss_messages)

        if plan.already_applied:
            return _result(
                plan,
                ProjectMigrationStatus.NOT_NEEDED,
                warnings,
                losses,
            )

        if plan.blocker_messages:
            warnings.extend(plan.blocker_messages)
            return _result(
                plan,
                ProjectMigrationStatus.BLOCKED,
                warnings,
                losses,
            )

        if plan.request.dry_run:
            warnings.append(
                "Dry run completed; no canonical project files were written."
            )
            return _result(
                plan,
                ProjectMigrationStatus.NOT_NEEDED,
                warnings,
                losses,
            )

        if self._workspace.is_cancelled():
            return _result(
                plan,
                ProjectMigrationStatus.CANCELLED,
                warnings,
                losses,
            )

        try:
            receipt = self._workspace.apply(plan)
        except Exception as exc:
            warnings.append(
                _failure_message(
                    exc,
                    operation="write",
                )
            )
            return _result(
                plan,
                ProjectMigrationStatus.FAILED,
                warnings,
                losses,
            )

        try:
            verification = self._workspace.verify(plan)
        except Exception as exc:
            warnings.append(
                _failure_message(
                    exc,
                    operation="verification",
                )
            )
            return self._rollback_failure(
                plan,
                receipt,
                warnings,
                losses,
            )

        warnings.extend(verification.warnings)
        losses.extend(verification.losses)

        if not verification.valid:
            warnings.extend(verification.blockers)
            return self._rollback_failure(
                plan,
                receipt,
                warnings,
                losses,
            )

        if self._workspace.is_cancelled():
            warnings.append(
                "Cancellation was observed after publication; the verified "
                "destination was retained and its backup remains available."
            )

        status = (
            ProjectMigrationStatus.MIGRATED_WITH_WARNINGS
            if warnings or losses or plan.manual_actions
            else ProjectMigrationStatus.MIGRATED
        )

        return _result(
            plan,
            status,
            warnings,
            losses,
            changed=receipt.changed,
            written=receipt.written,
            backup_path=receipt.backup_path,
        )

    def _rollback_failure(
        self,
        plan: ProjectMigrationPlan,
        receipt: ProjectMigrationWriteReceipt,
        warnings: list[str],
        losses: list[str],
    ) -> ProjectMigrationResult:
        try:
            rollback_warning = self._workspace.rollback(receipt)
        except Exception as exc:
            rollback_warning = _failure_message(
                exc,
                operation="rollback",
            )

        rolled_back = rollback_warning is None

        if rollback_warning:
            warnings.append(rollback_warning)

        return _result(
            plan,
            ProjectMigrationStatus.FAILED,
            warnings,
            losses,
            changed=receipt.changed and not rolled_back,
            written=receipt.written and not rolled_back,
            backup_path=receipt.backup_path,
        )


def plan_project_migration(
    request: ProjectMigrationRequest,
    *,
    workspace: ProjectMigrationWorkspacePort,
    clock: ClockPort,
) -> ProjectMigrationPlan:
    """Plan an explicit migration without writing project assets."""

    return ProjectMigrator(
        workspace=workspace,
        clock=clock,
    ).plan(request)


def migrate_project(
    request: ProjectMigrationRequest,
    *,
    workspace: ProjectMigrationWorkspacePort,
    clock: ClockPort,
) -> ProjectMigrationResult:
    """Apply, verify, and report one explicit project migration."""

    return ProjectMigrator(
        workspace=workspace,
        clock=clock,
    ).migrate(request)


def _normalize_request(
    request: ProjectMigrationRequest,
) -> ProjectMigrationRequest:
    if not isinstance(request, ProjectMigrationRequest):
        raise TypeError(
            "request must be ProjectMigrationRequest"
        )

    source_root = _require_absolute_path(
        request.source_root,
        field="source_root",
    )
    project_root = _require_absolute_path(
        request.project_root,
        field="project_root",
    )

    source_directory = validate_portable_project_path(
        request.source_directory.as_posix(),
        field="sources.directory",
        allow_dot=False,
    )

    validate_optional_regex(
        request.include_regex,
        field="sources.include_regex",
    )
    validate_optional_regex(
        request.exclude_regex,
        field="sources.exclude_regex",
    )

    entrypoints, checkpoints = validate_module_targets(
        tuple(
            path.as_posix()
            for path in request.entrypoints
        ),
        tuple(
            path.as_posix()
            for path in request.checkpoints
        ),
        require_entrypoint=False,
    )

    required, optional = validate_scenario_policy(
        request.required_scenarios,
        request.optional_scenarios,
    )

    return replace(
        request,
        migration_id=_single_line(
            request.migration_id,
            field="migration_id",
        ),
        source_root=source_root,
        project_root=project_root,
        project_id=validate_project_id(
            request.project_id
        ),
        project_name=validate_project_name(
            request.project_name
        ),
        language_code=validate_language_code(
            request.language_code
        ),
        source_directory=Path(source_directory),
        source_glob=validate_source_glob(
            request.source_glob
        ),
        gf_path_parts=deduplicate_declared_path_parts(
            request.gf_path_parts
        ),
        minimum_version=validate_minimum_version(
            request.minimum_version
        ),
        entrypoints=tuple(
            Path(value)
            for value in entrypoints
        ),
        checkpoints=tuple(
            Path(value)
            for value in checkpoints
        ),
        required_scenarios=required,
        optional_scenarios=optional,
        release_requires_pgf=validate_release_requires_pgf(
            request.release_requires_pgf
        ),
    )


def _validate_strategy(
    request: ProjectMigrationRequest,
    *,
    project_root: Path,
    target_source_root: Path,
) -> tuple[ProjectMigrationIssue, ...]:
    issues: list[ProjectMigrationIssue] = []

    if request.source_root == project_root:
        issues.append(
            ProjectMigrationIssue.blocker(
                code="migration.source_is_project_root",
                message=(
                    "The migration source must not be the destination "
                    "project root."
                ),
                path=request.source_root,
            )
        )

    if request.strategy in {
        ProjectMigrationStrategy.COPY,
        ProjectMigrationStrategy.HISTORY_IMPORT,
    }:
        if request.source_root == target_source_root:
            issues.append(
                ProjectMigrationIssue.blocker(
                    code="migration.source_equals_target",
                    message=(
                        "The source and managed destination source roots "
                        "must differ."
                    ),
                    path=request.source_root,
                )
            )

        if _is_inside(
            project_root,
            request.source_root,
        ):
            issues.append(
                ProjectMigrationIssue.blocker(
                    code="migration.destination_inside_source",
                    message=(
                        "The destination project root must not be inside "
                        "the source tree; the migration could recursively "
                        "consume its own output."
                    ),
                    path=project_root,
                )
            )

    if request.strategy is ProjectMigrationStrategy.HISTORY_IMPORT:
        issues.append(
            ProjectMigrationIssue.warning(
                code="migration.history_import_requires_adapter",
                message=(
                    "History-preserving import requires a recorded source "
                    "revision, import method, and path mapping."
                ),
                path=request.source_root,
            )
        )

    return tuple(issues)


def _build_config_draft(
    request: ProjectMigrationRequest,
    *,
    issues: list[ProjectMigrationIssue],
    manual_actions: list[str],
) -> ProjectConfig:
    paths = ProjectPaths.from_root(
        request.project_root
    )
    source_root = resolve_source_root(
        paths.root,
        request.source_directory,
    )

    if not request.entrypoints:
        issues.append(
            ProjectMigrationIssue.warning(
                code="migration.entrypoints_pending",
                message=(
                    "No entrypoint is declared in the migration draft."
                ),
                path=paths.config_file,
            )
        )
        manual_actions.append(
            "Declare and review at least one modules.entrypoints target "
            "before release."
        )

    if not request.required_scenarios:
        issues.append(
            ProjectMigrationIssue.warning(
                code="migration.required_scenarios_pending",
                message=(
                    "No required scenario is declared in the migration draft."
                ),
                path=paths.config_file,
            )
        )

    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id=request.project_id,
            name=request.project_name,
            language_code=request.language_code,
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=request.source_directory,
            glob=request.source_glob,
            include_regex=request.include_regex,
            exclude_regex=request.exclude_regex,
        ),
        gf=GFProjectConfig(
            path_parts=request.gf_path_parts,
            minimum_version=request.minimum_version,
        ),
        modules=ModuleTargets(
            entrypoints=request.entrypoints,
            checkpoints=request.checkpoints,
        ),
        validation=ValidationPolicy(
            required_scenarios=request.required_scenarios,
            optional_scenarios=request.optional_scenarios,
            release_requires_pgf=request.release_requires_pgf,
        ),
        project_file=paths.config_file,
        project_root=paths.root,
        source_root=source_root,
    )


def _build_actions(
    request: ProjectMigrationRequest,
    *,
    project_paths: ProjectPaths,
    target_source_root: Path,
    assets: tuple[ProjectMigrationAsset, ...],
) -> list[ProjectMigrationAction]:
    actions = [
        ProjectMigrationAction(
            kind=ProjectMigrationActionKind.INITIALIZE_PROJECT,
            source=None,
            destination=project_paths.root,
            asset=None,
            description=(
                "Materialize the canonical language-neutral project template."
            ),
        )
    ]

    if request.strategy is ProjectMigrationStrategy.COPY:
        actions.extend(
            ProjectMigrationAction(
                kind=ProjectMigrationActionKind.COPY_FILE,
                source=request.source_root.joinpath(
                    *asset.relative_path.parts
                ),
                destination=target_source_root.joinpath(
                    *asset.relative_path.parts
                ),
                asset=asset,
                description=(
                    "Copy original bytes into the managed source tree."
                ),
            )
            for asset in assets
            if asset.copy_to_managed_source
        )

    elif request.strategy is ProjectMigrationStrategy.EXTERNAL:
        actions.append(
            ProjectMigrationAction(
                kind=ProjectMigrationActionKind.REFERENCE_EXISTING_SOURCE,
                source=request.source_root,
                destination=target_source_root,
                asset=None,
                description=(
                    "Reference the existing project-relative source tree."
                ),
            )
        )

    else:
        actions.append(
            ProjectMigrationAction(
                kind=ProjectMigrationActionKind.IMPORT_WITH_HISTORY,
                source=request.source_root,
                destination=target_source_root,
                asset=None,
                description=(
                    "Perform the authorized history-preserving source import."
                ),
            )
        )

    actions.extend(
        (
            ProjectMigrationAction(
                kind=ProjectMigrationActionKind.WRITE_PROJECT_CONFIG,
                source=None,
                destination=project_paths.config_file,
                asset=None,
                description=(
                    "Write the canonical project.toml draft atomically."
                ),
            ),
            ProjectMigrationAction(
                kind=ProjectMigrationActionKind.VERIFY_PROJECT,
                source=None,
                destination=project_paths.root,
                asset=None,
                description=(
                    "Verify project paths, configuration, and migration "
                    "invariants."
                ),
            ),
        )
    )

    return actions


def _validate_external_mapping(
    request: ProjectMigrationRequest,
    *,
    project_paths: ProjectPaths,
    issues: list[ProjectMigrationIssue],
) -> None:
    if request.strategy is not ProjectMigrationStrategy.EXTERNAL:
        return

    try:
        relative = relative_portable_path(
            project_paths.root,
            request.source_root,
            role="external-strategy source root",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
    except Exception:
        issues.append(
            ProjectMigrationIssue.blocker(
                code="migration.external_source_not_project_relative",
                message=(
                    "sources.directory must resolve inside the project root; "
                    "choose a containing project root or use managed copy."
                ),
                path=request.source_root,
            )
        )
        return

    if (
        relative.as_posix()
        != request.source_directory.as_posix()
    ):
        issues.append(
            ProjectMigrationIssue.blocker(
                code="migration.external_source_mismatch",
                message=(
                    "source_directory does not identify the supplied source "
                    f"root; expected {relative.as_posix()!r}."
                ),
                path=request.source_root,
            )
        )


def _required_manual_actions(
    strategy: ProjectMigrationStrategy,
) -> tuple[str, ...]:
    actions = [
        (
            "Review proposed entrypoints and checkpoints before declaring "
            "migration complete."
        ),
        (
            "Create or review scenarios, inputs, and gold files; no gold is "
            "accepted automatically."
        ),
        (
            "Complete project contract documents and retain rollback evidence."
        ),
        (
            "Run the documented baseline and release validations after cutover."
        ),
    ]

    if strategy is ProjectMigrationStrategy.HISTORY_IMPORT:
        actions.insert(
            0,
            (
                "Record the source repository, revision, import method, "
                "and preserved path mapping."
            ),
        )

    return tuple(actions)


def _result(
    plan: ProjectMigrationPlan,
    status: ProjectMigrationStatus,
    warnings: Sequence[str],
    losses: Sequence[str],
    *,
    changed: bool = False,
    written: bool = False,
    backup_path: Path | None = None,
) -> ProjectMigrationResult:
    return ProjectMigrationResult(
        migration_id=plan.migration_id,
        source_schema=plan.source_schema,
        source_version=plan.source_version,
        target_schema=plan.target_schema,
        target_version=plan.target_version,
        source_path=plan.request.source_root.as_posix(),
        destination_path=plan.request.project_root.as_posix(),
        status=status,
        warnings=tuple(
            _deduplicate_text(warnings)
        ),
        losses=tuple(
            _deduplicate_text(losses)
        ),
        manual_actions=plan.manual_actions,
        changed=changed,
        written=written,
        backup_path=(
            backup_path.as_posix()
            if backup_path is not None
            else None
        ),
    )


def _deduplicate_issues(
    issues: Iterable[ProjectMigrationIssue],
) -> list[ProjectMigrationIssue]:
    seen: set[tuple[object, ...]] = set()
    result: list[ProjectMigrationIssue] = []

    for issue in issues:
        key = (
            issue.severity,
            issue.code,
            issue.message,
            issue.path,
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(issue)

    return result


def _deduplicate_text(
    values: Iterable[str],
) -> list[str]:
    return list(
        dict.fromkeys(
            value.strip()
            for value in values
            if value.strip()
        )
    )


def _string_tuple(
    values: Iterable[str],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(
        values,
        (str, bytes, bytearray),
    ):
        raise TypeError(
            f"{field} must be an iterable of strings"
        )

    result = tuple(values)

    if any(
        not isinstance(value, str)
        for value in result
    ):
        raise TypeError(
            f"{field} must contain only strings"
        )

    return result


def _path_tuple(
    values: Iterable[Path],
    *,
    field: str,
) -> tuple[Path, ...]:
    if isinstance(
        values,
        (str, bytes, bytearray),
    ):
        raise TypeError(
            f"{field} must be an iterable of paths"
        )

    return tuple(
        Path(value)
        for value in values
    )


def _single_line(
    value: object,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field} must be a string"
        )

    if (
        not value
        or value != value.strip()
        or any(
            character in value
            for character in "\x00\r\n"
        )
    ):
        raise ValueError(
            f"{field} must be a non-empty single-line string"
        )

    return value


def _require_relative_path(
    value: Path,
    *,
    field: str,
) -> Path:
    path = Path(value)
    text = path.as_posix()
    windows = PureWindowsPath(text)

    if (
        not text
        or path.is_absolute()
        or windows.is_absolute()
        or windows.drive
    ):
        raise ValueError(
            f"{field} must be a relative path"
        )

    if (
        text == "."
        or any(
            part in {"", ".", ".."}
            for part in path.parts
        )
    ):
        raise ValueError(
            f"{field} must identify a contained child path"
        )

    return path


def _require_absolute_path(
    value: Path,
    *,
    field: str,
) -> Path:
    path = Path(value)

    if not path.is_absolute():
        raise ValueError(
            f"{field} must be an absolute path"
        )

    if any(
        part == ".."
        for part in path.parts
    ):
        raise ValueError(
            f"{field} must not contain unresolved parent traversal"
        )

    return Path(*path.parts)


def _is_inside(
    path: Path,
    parent: Path,
) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False

    return path != parent


def _failure_message(
    exc: Exception,
    *,
    operation: str,
) -> str:
    message = (
        str(exc).strip()
        or exc.__class__.__name__
    )
    prefix = f"migration {operation} failed: "
    limit = _MAX_FAILURE_MESSAGE_LENGTH - len(prefix)

    if len(message) > limit:
        message = (
            message[: max(0, limit - 3)]
            + "..."
        )

    return prefix + message


__all__ = [
    "ProjectMigrationAction",
    "ProjectMigrationActionKind",
    "ProjectMigrationAsset",
    "ProjectMigrationDestinationInspection",
    "ProjectMigrationIssue",
    "ProjectMigrationPlan",
    "ProjectMigrationRequest",
    "ProjectMigrationResult",
    "ProjectMigrationSourceInspection",
    "ProjectMigrationStatus",
    "ProjectMigrationStrategy",
    "ProjectMigrationVerification",
    "ProjectMigrationWriteReceipt",
    "ProjectMigrator",
    "migrate_project",
    "plan_project_migration",
]