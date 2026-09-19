"""Transactional active-project reset planning and orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Protocol

from gf_wordbench.kernel.ids import ProjectId, validate_project_id

_PROJECT_DIR = "project"
_TEMPLATE_DIR = Path("templates") / "project"
_STATE_FILE = ".gf_wordbench_state.json"
_OPERATION_ID = re.compile(r"^reset-[0-9a-f]{20}$")
_RUN_NAME = re.compile(r"^run_[A-Za-z0-9][A-Za-z0-9._-]*$")

_INITIALIZATION_ACTIONS = (
    "Provide the new project identity and language metadata explicitly.",
    "Populate and validate project/project.toml.",
    "Populate the active project contract lock and project documentation.",
    "Configure source roots, GF entrypoints, checkpoints, and scenarios.",
    "Run canonical project checks before producing new validation evidence.",
)


class ResetScope(StrEnum):
    NEW_PROJECT = "new-project"
    PROJECT_ONLY = "project-only"


class PreservationMode(StrEnum):
    ARCHIVE = "archive"
    DISCARD = "discard"


class ResetPhase(StrEnum):
    PLAN = "plan"
    PREFLIGHT = "preflight"
    ARCHIVE_OR_AUTHORIZE_DISCARD = "archive-or-authorize-discard"
    STAGE = "stage"
    VALIDATE_STAGE = "validate-stage"
    SWAP = "swap"
    VALIDATE_ACTIVE_PROJECT = "validate-active-project"
    CLEAN_GENERATED_STATE = "clean-generated-state"
    COMPLETE = "complete"
    ROLLBACK = "rollback"


class ResetOutcome(StrEnum):
    SUCCESS = "success"
    DRY_RUN = "dry-run"
    PARTIAL = "partial"
    FAILED = "failed"
    CRITICAL = "critical"


class PhaseStatus(StrEnum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class LifecycleErrorCategory(StrEnum):
    CONFIGURATION = "configuration"
    PATH_SAFETY = "path-safety"
    TEMPLATE = "template"
    ARCHIVE = "archive"
    AUTHORIZATION = "authorization"
    CONCURRENCY = "concurrency"
    STAGING = "staging"
    SWAP = "swap"
    ROLLBACK = "rollback"
    CLEANUP = "cleanup"
    VALIDATION = "validation"


@dataclass(frozen=True, slots=True)
class ResetRequest:
    """Explicit inputs and observations used by pure reset planning."""

    workspace_root: Path
    scope: ResetScope = ResetScope.NEW_PROJECT
    preservation: PreservationMode = PreservationMode.ARCHIVE
    archive_destination: Path | None = None
    discard_authorized: bool = False
    confirmation_token: str | None = None
    expected_project_id: ProjectId | None = None
    dry_run: bool = False
    current_project_id: ProjectId | None = None
    run_paths: tuple[Path, ...] = ()
    external_source_roots: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        root = _absolute_path(self.workspace_root, "workspace_root")
        if root == Path(root.anchor):
            raise ValueError("workspace_root cannot be a filesystem root")
        object.__setattr__(self, "workspace_root", root)
        object.__setattr__(self, "scope", ResetScope(self.scope))
        object.__setattr__(
            self,
            "preservation",
            PreservationMode(self.preservation),
        )

        if not isinstance(self.discard_authorized, bool):
            raise TypeError("discard_authorized must be a boolean")
        if not isinstance(self.dry_run, bool):
            raise TypeError("dry_run must be a boolean")

        archive = self.archive_destination
        if archive is not None:
            archive = _absolute_path(archive, "archive_destination")
            if archive == Path(archive.anchor):
                raise ValueError("archive_destination cannot be a filesystem root")
            object.__setattr__(self, "archive_destination", archive)

        if self.confirmation_token is not None:
            object.__setattr__(
                self,
                "confirmation_token",
                _text(self.confirmation_token, "confirmation_token"),
            )

        expected = _project_id(
            self.expected_project_id,
            "expected_project_id",
        )
        current = _project_id(
            self.current_project_id,
            "current_project_id",
        )
        object.__setattr__(self, "expected_project_id", expected)
        object.__setattr__(self, "current_project_id", current)

        if expected is not None and current is not None and expected != current:
            raise ValueError("current_project_id does not match expected_project_id")

        runs = _paths(self.run_paths, "run_paths")
        for path in runs:
            if path.parent != root or _RUN_NAME.fullmatch(path.name) is None:
                raise ValueError(
                    "run_paths must be canonical run_<run-id> children of workspace_root"
                )
        object.__setattr__(self, "run_paths", runs)

        object.__setattr__(
            self,
            "external_source_roots",
            _paths(
                self.external_source_roots,
                "external_source_roots",
            ),
        )
        object.__setattr__(
            self,
            "warnings",
            _texts(self.warnings, "warnings"),
        )

        if self.preservation is PreservationMode.ARCHIVE:
            if archive is None:
                raise ValueError("archive mode requires archive_destination")
            if self.discard_authorized:
                raise ValueError("archive mode forbids discard_authorized")
        elif archive is not None or not self.discard_authorized:
            raise ValueError(
                "discard mode requires explicit authorization and no archive destination"
            )


@dataclass(frozen=True, slots=True)
class ResetPlan:
    operation_id: str
    request: ResetRequest
    project_path: Path
    template_path: Path
    staging_path: Path
    rollback_path: Path
    state_path: Path
    run_paths: tuple[Path, ...]
    external_source_roots: tuple[Path, ...]
    preserve_paths: tuple[Path, ...]
    replace_paths: tuple[Path, ...]
    removal_paths: tuple[Path, ...]
    current_project_id: ProjectId | None = None
    warnings: tuple[str, ...] = ()
    remaining_initialization_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        operation_id = _text(self.operation_id, "operation_id")
        if _OPERATION_ID.fullmatch(operation_id) is None:
            raise ValueError("operation_id must use reset-<20 lowercase hex>")
        if not isinstance(self.request, ResetRequest):
            raise TypeError("request must be ResetRequest")

        root = self.request.workspace_root
        stage, rollback = _private_paths(root, operation_id)
        expected = {
            "project_path": root / _PROJECT_DIR,
            "template_path": root / _TEMPLATE_DIR,
            "staging_path": stage,
            "rollback_path": rollback,
            "state_path": root / _STATE_FILE,
        }

        for field, value in expected.items():
            if _absolute_path(getattr(self, field), field) != value:
                raise ValueError(f"{field} is not canonical")

        if self.run_paths != self.request.run_paths:
            raise ValueError("run_paths must match request.run_paths")
        if self.external_source_roots != self.request.external_source_roots:
            raise ValueError("external_source_roots must match request.external_source_roots")
        if self.replace_paths != (expected["project_path"],):
            raise ValueError("replace_paths must contain only project_path")
        if self.removal_paths != _removal_paths(
            self.request,
            expected["state_path"],
        ):
            raise ValueError("removal_paths do not match the reset scope")
        if self.preserve_paths != _preserve_paths(
            self.request,
            expected["template_path"],
            expected["state_path"],
        ):
            raise ValueError("preserve_paths do not match the reset scope")
        if self.current_project_id != self.request.current_project_id:
            raise ValueError("current_project_id must match the request")

        object.__setattr__(
            self,
            "warnings",
            _texts(self.warnings, "warnings"),
        )
        object.__setattr__(
            self,
            "remaining_initialization_actions",
            _texts(
                self.remaining_initialization_actions,
                "remaining_initialization_actions",
            ),
        )

        _validate_boundaries(
            self.request,
            expected["project_path"],
            expected["template_path"],
            expected["staging_path"],
            expected["rollback_path"],
            expected["state_path"],
        )


@dataclass(frozen=True, slots=True)
class PhaseRecord:
    phase: ResetPhase
    status: PhaseStatus
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "phase", ResetPhase(self.phase))
        object.__setattr__(self, "status", PhaseStatus(self.status))
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message"),
        )


@dataclass(frozen=True, slots=True)
class ResetFailure:
    category: LifecycleErrorCategory
    phase: ResetPhase
    message: str
    exception_type: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category",
            LifecycleErrorCategory(self.category),
        )
        object.__setattr__(self, "phase", ResetPhase(self.phase))
        object.__setattr__(
            self,
            "message",
            _text(self.message, "message"),
        )
        object.__setattr__(
            self,
            "exception_type",
            _text(self.exception_type, "exception_type"),
        )


@dataclass(frozen=True, slots=True)
class ResetResult:
    outcome: ResetOutcome
    plan: ResetPlan | None
    phases: tuple[PhaseRecord, ...]
    archive_completed: bool | None = None
    project_staged: bool = False
    project_replacement_completed: bool = False
    active_project_validation_completed: bool = False
    rollback_completed: bool | None = None
    run_cleanup_completed: bool | None = None
    state_reset_completed: bool | None = None
    remaining_actions: tuple[str, ...] = ()
    failure: ResetFailure | None = None

    @property
    def plan_created(self) -> bool:
        return self.plan is not None

    @property
    def succeeded(self) -> bool:
        return self.outcome in {
            ResetOutcome.SUCCESS,
            ResetOutcome.DRY_RUN,
        }


class ProjectResetError(RuntimeError):
    def __init__(
        self,
        category: LifecycleErrorCategory,
        message: str,
        *,
        phase: ResetPhase | None = None,
    ) -> None:
        self.category = LifecycleErrorCategory(category)
        self.phase = ResetPhase(phase) if phase is not None else None
        self.public_message = _text(message, "message")
        super().__init__(self.public_message)


def plan_project_reset(request: ResetRequest) -> ResetPlan:
    """Build a deterministic reset plan without filesystem mutation."""

    if not isinstance(request, ResetRequest):
        raise TypeError("request must be ResetRequest")

    operation_id = _operation_id(request)
    root = request.workspace_root
    project = root / _PROJECT_DIR
    template = root / _TEMPLATE_DIR
    staging, rollback = _private_paths(root, operation_id)
    state = root / _STATE_FILE

    _validate_boundaries(
        request,
        project,
        template,
        staging,
        rollback,
        state,
    )

    warnings = list(request.warnings)

    if request.scope is ResetScope.PROJECT_ONLY:
        warnings.append(
            "Project-only reset retains runs and state that may refer to the old project."
        )

    if request.external_source_roots:
        warnings.append(
            "External source roots are preserved and excluded from the project archive."
        )

    if request.archive_destination is not None and _within(request.archive_destination, root):
        warnings.append(
            "The archive destination is inside the workspace and must remain outside reset scope."
        )

    if request.expected_project_id is not None and request.current_project_id is None:
        warnings.append("Preflight must verify expected_project_id before mutation.")

    return ResetPlan(
        operation_id=operation_id,
        request=request,
        project_path=project,
        template_path=template,
        staging_path=staging,
        rollback_path=rollback,
        state_path=state,
        run_paths=request.run_paths,
        external_source_roots=request.external_source_roots,
        preserve_paths=_preserve_paths(
            request,
            template,
            state,
        ),
        replace_paths=(project,),
        removal_paths=_removal_paths(
            request,
            state,
        ),
        current_project_id=request.current_project_id,
        warnings=_texts(warnings, "warnings"),
        remaining_initialization_actions=_INITIALIZATION_ACTIONS,
    )


class ResetPlanner(Protocol):
    def __call__(
        self,
        request: ResetRequest,
        /,
    ) -> ResetPlan: ...


class ResetOperations(Protocol):
    def lifecycle_lock(
        self,
        plan: ResetPlan,
    ) -> AbstractContextManager[None]: ...

    def preflight(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def archive_project(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def authorize_discard(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def stage_template(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def validate_staged_project(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def swap_project(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def validate_active_project(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def cleanup_runs(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def reset_application_state(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def complete(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def discard_stage(
        self,
        plan: ResetPlan,
    ) -> None: ...

    def rollback(
        self,
        plan: ResetPlan,
    ) -> None: ...


@dataclass(slots=True)
class _Progress:
    archive: bool | None = None
    staged: bool = False
    swapped: bool = False
    validated: bool = False
    rollback: bool | None = None
    runs: bool | None = None
    state: bool | None = None


class ProjectResetter:
    """Coordinate a staged, validated, reversible project reset."""

    __slots__ = ("_operations", "_planner")

    def __init__(
        self,
        *,
        operations: ResetOperations,
        planner: ResetPlanner = plan_project_reset,
    ) -> None:
        if not callable(planner):
            raise TypeError("planner must be callable")
        self._planner = planner
        self._operations = operations

    def plan(
        self,
        request: ResetRequest,
    ) -> ResetPlan:
        if not isinstance(request, ResetRequest):
            raise TypeError("request must be ResetRequest")

        plan = self._planner(request)

        if not isinstance(plan, ResetPlan) or plan.request != request:
            raise TypeError("planner must return ResetPlan for the exact request")

        return plan

    def reset(
        self,
        request: ResetRequest,
    ) -> ResetResult:
        records: list[PhaseRecord] = []

        try:
            plan = self.plan(request)
        except Exception as exc:
            failure = _failure(
                exc,
                ResetPhase.PLAN,
                LifecycleErrorCategory.CONFIGURATION,
            )
            records.append(_failed(failure))

            return ResetResult(
                ResetOutcome.FAILED,
                None,
                tuple(records),
                failure=failure,
            )

        records.append(
            _done(
                ResetPhase.PLAN,
                "Plan created.",
            )
        )

        if request.dry_run:
            return self._dry_run(plan, records)

        try:
            with self._operations.lifecycle_lock(plan):
                return self._reset_locked(plan, records)
        except Exception as exc:
            failure = _failure(
                exc,
                ResetPhase.PREFLIGHT,
                LifecycleErrorCategory.CONCURRENCY,
            )
            records.append(_failed(failure))

            return ResetResult(
                ResetOutcome.FAILED,
                plan,
                tuple(records),
                failure=failure,
            )

    def _dry_run(
        self,
        plan: ResetPlan,
        records: list[PhaseRecord],
    ) -> ResetResult:
        try:
            self._operations.preflight(plan)
        except Exception as exc:
            failure = _failure(
                exc,
                ResetPhase.PREFLIGHT,
                LifecycleErrorCategory.PATH_SAFETY,
            )
            records.append(_failed(failure))

            return ResetResult(
                ResetOutcome.FAILED,
                plan,
                tuple(records),
                failure=failure,
            )

        records.append(
            _done(
                ResetPhase.PREFLIGHT,
                "Dry-run preflight passed.",
            )
        )
        records.extend(
            PhaseRecord(
                phase,
                PhaseStatus.SKIPPED,
                "Dry run performs no mutation.",
            )
            for phase in _MUTATING_PHASES
        )

        return ResetResult(
            ResetOutcome.DRY_RUN,
            plan,
            tuple(records),
            remaining_actions=(plan.remaining_initialization_actions),
        )

    def _reset_locked(
        self,
        plan: ResetPlan,
        records: list[PhaseRecord],
    ) -> ResetResult:
        progress = _Progress()
        archive_mode = plan.request.preservation is PreservationMode.ARCHIVE

        steps = (
            (
                ResetPhase.PREFLIGHT,
                self._operations.preflight,
                "Preflight passed.",
            ),
            (
                ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD,
                (
                    self._operations.archive_project
                    if archive_mode
                    else self._operations.authorize_discard
                ),
                (
                    "Project archived and verified."
                    if archive_mode
                    else "Explicit discard authorization verified."
                ),
            ),
            (
                ResetPhase.STAGE,
                self._operations.stage_template,
                "Project staged.",
            ),
            (
                ResetPhase.VALIDATE_STAGE,
                self._operations.validate_staged_project,
                "Staged project validated.",
            ),
            (
                ResetPhase.SWAP,
                self._operations.swap_project,
                "Project swapped.",
            ),
            (
                ResetPhase.VALIDATE_ACTIVE_PROJECT,
                self._operations.validate_active_project,
                "Active reset scaffold validated.",
            ),
        )

        for phase, action, message in steps:
            try:
                action(plan)
            except Exception as exc:
                failure = _failure(
                    exc,
                    phase,
                    _category(
                        phase,
                        plan.request.preservation,
                    ),
                )
                records.append(_failed(failure))

                return self._recover(
                    plan,
                    records,
                    progress,
                    failure,
                )

            records.append(_done(phase, message))

            if phase is ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD:
                progress.archive = True if archive_mode else None
            elif phase is ResetPhase.STAGE:
                progress.staged = True
            elif phase is ResetPhase.SWAP:
                progress.swapped = True
            elif phase is ResetPhase.VALIDATE_ACTIVE_PROJECT:
                progress.validated = True

        cleanup_failure = self._clean(
            plan,
            progress,
        )

        if plan.request.scope is ResetScope.PROJECT_ONLY:
            records.append(
                PhaseRecord(
                    ResetPhase.CLEAN_GENERATED_STATE,
                    PhaseStatus.SKIPPED,
                    "Project-only reset retains runs and application state.",
                )
            )
        elif cleanup_failure is None:
            records.append(
                _done(
                    ResetPhase.CLEAN_GENERATED_STATE,
                    "Generated state cleaned.",
                )
            )
        else:
            records.append(_failed(cleanup_failure))

            return self._result(
                ResetOutcome.PARTIAL,
                plan,
                records,
                progress,
                failure=cleanup_failure,
                remaining_actions=_cleanup_actions(
                    plan,
                    progress,
                ),
            )

        try:
            self._operations.complete(plan)
        except Exception as exc:
            failure = _failure(
                exc,
                ResetPhase.COMPLETE,
                LifecycleErrorCategory.CLEANUP,
            )
            records.append(_failed(failure))

            return self._result(
                ResetOutcome.PARTIAL,
                plan,
                records,
                progress,
                failure=failure,
                remaining_actions=(
                    "Preserve the validated active project.",
                    "Resolve temporary or rollback artifacts before another lifecycle operation.",
                ),
            )

        records.append(
            _done(
                ResetPhase.COMPLETE,
                "Reset completed.",
            )
        )

        return self._result(
            ResetOutcome.SUCCESS,
            plan,
            records,
            progress,
            remaining_actions=(plan.remaining_initialization_actions),
        )

    def _clean(
        self,
        plan: ResetPlan,
        progress: _Progress,
    ) -> ResetFailure | None:
        if plan.request.scope is ResetScope.PROJECT_ONLY:
            return None

        failure: ResetFailure | None = None

        try:
            self._operations.cleanup_runs(plan)
            progress.runs = True
        except Exception as exc:
            progress.runs = False
            failure = _failure(
                exc,
                ResetPhase.CLEAN_GENERATED_STATE,
                LifecycleErrorCategory.CLEANUP,
            )

        try:
            self._operations.reset_application_state(plan)
            progress.state = True
        except Exception as exc:
            progress.state = False
            failure = failure or _failure(
                exc,
                ResetPhase.CLEAN_GENERATED_STATE,
                LifecycleErrorCategory.CLEANUP,
            )

        return failure

    def _recover(
        self,
        plan: ResetPlan,
        records: list[PhaseRecord],
        progress: _Progress,
        failure: ResetFailure,
    ) -> ResetResult:
        must_rollback = failure.phase is ResetPhase.SWAP or (
            progress.swapped and not progress.validated
        )

        if must_rollback:
            try:
                self._operations.rollback(plan)
                progress.rollback = True

                records.append(
                    _done(
                        ResetPhase.ROLLBACK,
                        "Previous project restored.",
                    )
                )
            except Exception as exc:
                rollback_failure = _failure(
                    exc,
                    ResetPhase.ROLLBACK,
                    LifecycleErrorCategory.ROLLBACK,
                )
                progress.rollback = False
                records.append(_failed(rollback_failure))

                return self._result(
                    ResetOutcome.CRITICAL,
                    plan,
                    records,
                    progress,
                    failure=rollback_failure,
                    remaining_actions=(
                        f"Do not delete {plan.project_path!s}.",
                        f"Do not delete {plan.rollback_path!s}.",
                        "Stop lifecycle operations and perform explicit manual recovery.",
                    ),
                )
        elif progress.staged:
            try:
                self._operations.discard_stage(plan)
            except Exception:
                pass

        return self._result(
            ResetOutcome.FAILED,
            plan,
            records,
            progress,
            failure=failure,
            remaining_actions=(
                "Preserve the authoritative project and recovery material.",
                "Resolve the lifecycle failure before retrying reset.",
            ),
        )

    @staticmethod
    def _result(
        outcome: ResetOutcome,
        plan: ResetPlan,
        records: list[PhaseRecord],
        progress: _Progress,
        *,
        failure: ResetFailure | None = None,
        remaining_actions: tuple[str, ...] = (),
    ) -> ResetResult:
        return ResetResult(
            outcome=outcome,
            plan=plan,
            phases=tuple(records),
            archive_completed=progress.archive,
            project_staged=progress.staged,
            project_replacement_completed=progress.swapped,
            active_project_validation_completed=(progress.validated),
            rollback_completed=progress.rollback,
            run_cleanup_completed=progress.runs,
            state_reset_completed=progress.state,
            remaining_actions=remaining_actions,
            failure=failure,
        )


def reset_project(
    request: ResetRequest,
    *,
    operations: ResetOperations,
    planner: ResetPlanner = plan_project_reset,
) -> ResetResult:
    return ProjectResetter(
        operations=operations,
        planner=planner,
    ).reset(request)


_MUTATING_PHASES = (
    ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD,
    ResetPhase.STAGE,
    ResetPhase.VALIDATE_STAGE,
    ResetPhase.SWAP,
    ResetPhase.VALIDATE_ACTIVE_PROJECT,
    ResetPhase.CLEAN_GENERATED_STATE,
    ResetPhase.COMPLETE,
)


def _operation_id(
    request: ResetRequest,
) -> str:
    payload = {
        "workspace_root": os.fspath(request.workspace_root),
        "scope": request.scope.value,
        "preservation": request.preservation.value,
        "archive_destination": (
            os.fspath(request.archive_destination)
            if request.archive_destination is not None
            else None
        ),
        "expected_project_id": (
            str(request.expected_project_id) if request.expected_project_id is not None else None
        ),
        "current_project_id": (
            str(request.current_project_id) if request.current_project_id is not None else None
        ),
        "run_paths": [os.fspath(path) for path in request.run_paths],
        "external_source_roots": [os.fspath(path) for path in request.external_source_roots],
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"reset-{digest}"


def _private_paths(
    root: Path,
    operation_id: str,
) -> tuple[Path, Path]:
    prefix = f".gf-wordbench-{operation_id}"

    return (
        root / f"{prefix}.stage",
        root / f"{prefix}.rollback",
    )


def _preserve_paths(
    request: ResetRequest,
    template: Path,
    state: Path,
) -> tuple[Path, ...]:
    values = [
        template,
        *request.external_source_roots,
    ]

    if request.scope is ResetScope.PROJECT_ONLY:
        values.extend(request.run_paths)
        values.append(state)

    return _unique_paths(values)


def _removal_paths(
    request: ResetRequest,
    state: Path,
) -> tuple[Path, ...]:
    if request.scope is ResetScope.PROJECT_ONLY:
        return ()

    return _unique_paths(
        [
            *request.run_paths,
            state,
        ]
    )


def _validate_boundaries(
    request: ResetRequest,
    project: Path,
    template: Path,
    staging: Path,
    rollback: Path,
    state: Path,
) -> None:
    root = request.workspace_root
    controlled = (
        project,
        template,
        staging,
        rollback,
        state,
        *request.run_paths,
    )

    for path in controlled:
        if path == root or not _within(path, root):
            raise ValueError("reset-controlled paths must remain inside workspace_root")

    if project.parent != root or staging.parent != root or rollback.parent != root:
        raise ValueError("project, staging, and rollback paths must be direct workspace children")

    if state.parent != root:
        raise ValueError("state_path must be a direct workspace child")

    _reject_overlaps(
        controlled,
        "reset-controlled paths",
    )
    _reject_overlaps(
        request.external_source_roots,
        "external_source_roots",
    )

    for source in request.external_source_roots:
        if any(_overlap(source, path) for path in controlled):
            raise ValueError("external source roots must not overlap reset-controlled paths")

    archive = request.archive_destination
    if archive is not None:
        if archive == root:
            raise ValueError("archive_destination cannot be workspace_root")

        if any(
            _overlap(archive, path)
            for path in (
                *controlled,
                *request.external_source_roots,
            )
        ):
            raise ValueError("archive_destination overlaps a protected reset path")


def _absolute_path(
    value: object,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")

    raw = os.fspath(value)

    if "\x00" in raw:
        raise ValueError(f"{field} cannot contain NUL")

    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")

    return Path(os.path.normpath(raw))


def _paths(
    values: object,
    field: str,
) -> tuple[Path, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")

    return _unique_paths(_absolute_path(value, field) for value in values)


def _unique_paths(
    values: Iterable[Path],
) -> tuple[Path, ...]:
    unique: dict[str, Path] = {}

    for path in values:
        key = os.path.normcase(os.fspath(path))

        if key in unique:
            raise ValueError(f"duplicate path: {path!s}")

        unique[key] = path

    return tuple(
        sorted(
            unique.values(),
            key=lambda path: (
                os.path.normcase(os.fspath(path)),
                os.fspath(path),
            ),
        )
    )


def _within(
    candidate: Path,
    parent: Path,
) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False

    return True


def _overlap(
    left: Path,
    right: Path,
) -> bool:
    return _within(left, right) or _within(right, left)


def _reject_overlaps(
    paths: tuple[Path, ...],
    field: str,
) -> None:
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            if _overlap(left, right):
                raise ValueError(f"{field} overlap: {left!s} and {right!s}")


def _project_id(
    value: ProjectId | None,
    field: str,
) -> ProjectId | None:
    if value is None:
        return None

    return validate_project_id(
        value,
        field=field,
    )


def _done(
    phase: ResetPhase,
    message: str,
) -> PhaseRecord:
    return PhaseRecord(
        phase,
        PhaseStatus.COMPLETED,
        message,
    )


def _failed(
    failure: ResetFailure,
) -> PhaseRecord:
    return PhaseRecord(
        failure.phase,
        PhaseStatus.FAILED,
        failure.message,
    )


def _failure(
    exc: Exception,
    phase: ResetPhase,
    fallback: LifecycleErrorCategory,
) -> ResetFailure:
    if isinstance(exc, ProjectResetError):
        return ResetFailure(
            exc.category,
            exc.phase or phase,
            exc.public_message,
            type(exc).__name__,
        )

    return ResetFailure(
        fallback,
        phase,
        f"Reset failed during {phase.value}.",
        type(exc).__name__,
    )


def _category(
    phase: ResetPhase,
    preservation: PreservationMode,
) -> LifecycleErrorCategory:
    if phase is ResetPhase.ARCHIVE_OR_AUTHORIZE_DISCARD:
        return (
            LifecycleErrorCategory.ARCHIVE
            if preservation is PreservationMode.ARCHIVE
            else LifecycleErrorCategory.AUTHORIZATION
        )

    return {
        ResetPhase.PREFLIGHT: (LifecycleErrorCategory.PATH_SAFETY),
        ResetPhase.STAGE: (LifecycleErrorCategory.STAGING),
        ResetPhase.VALIDATE_STAGE: (LifecycleErrorCategory.VALIDATION),
        ResetPhase.SWAP: (LifecycleErrorCategory.SWAP),
        ResetPhase.VALIDATE_ACTIVE_PROJECT: (LifecycleErrorCategory.VALIDATION),
    }[phase]


def _cleanup_actions(
    plan: ResetPlan,
    progress: _Progress,
) -> tuple[str, ...]:
    actions = ["Keep the validated new active project."]

    if progress.runs is False:
        actions.append("Retry cleanup through the run-lifecycle service.")

    if progress.state is False:
        actions.append(f"Retry application-state cleanup for {plan.state_path!s}.")

    actions.append("Resolve retained recovery artifacts before another lifecycle operation.")

    return tuple(actions)


def _text(
    value: object,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")

    if not value or value != value.strip() or any(char in value for char in "\x00\r\n"):
        raise ValueError(f"{field} must be a non-empty single-line string")

    return value


def _texts(
    values: object,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{field} must be a tuple or list")

    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = _text(value, field)

        if text not in seen:
            seen.add(text)
            output.append(text)

    return tuple(output)


__all__ = [
    "LifecycleErrorCategory",
    "PhaseRecord",
    "PhaseStatus",
    "PreservationMode",
    "ProjectResetError",
    "ProjectResetter",
    "ResetFailure",
    "ResetOperations",
    "ResetOutcome",
    "ResetPhase",
    "ResetPlan",
    "ResetPlanner",
    "ResetRequest",
    "ResetResult",
    "ResetScope",
    "plan_project_reset",
    "reset_project",
]
