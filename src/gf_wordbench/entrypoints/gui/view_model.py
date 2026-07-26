"""Qt-neutral presentation state for the GF Wordbench desktop entrypoint."""
from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias
from gf_wordbench.kernel.events import EventLevel, ProgressEvent
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.runs.models.results import RunResult
from gf_wordbench.state.models import AppState, EnvironmentState, LastRunState, SelectionState
__all__ = (
    "ActivityItem",
    "ArtifactAction",
    "ArtifactActionId",
    "FailureCounts",
    "GuiRunRequest",
    "GuiSnapshot",
    "GuiViewModel",
    "ProgressView",
    "ProjectView",
    "ResultView",
    "RunPresentationState",
    "StatusCounts",
    "artifact_actions_from_result",
    "completion_message",
    "project_view_from_config",
    "result_view_from_run",
)
_MAX_ACTIVITY: Final[int] = 500
_MAX_NOTICES: Final[int] = 100
_MAX_TEXT: Final[int] = 4_096
_MAX_ITEMS: Final[int] = 1_024
OverrideScalar: TypeAlias = str | int | float | bool | None
PathProbe: TypeAlias = Callable[[Path], bool]
@unique
class RunPresentationState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
@unique
class ArtifactActionId(StrEnum):
    RUN_DIRECTORY = "run_directory"
    MACHINE_SUMMARY = "machine_summary"
    HUMAN_SUMMARY = "human_summary"
    AI_READY_PACKET = "ai_ready_packet"
    MASTER_LOG = "master_log"
    ALL_OPERATION_LOGS = "all_operation_logs"
    ALL_SCAN_LOGS = "all_scan_logs"
    MANIFEST = "manifest"
    PGF_DIRECTORY = "pgf_directory"
    DETAILS_DIRECTORY = "details_directory"
@dataclass(frozen=True, slots=True)
class GuiRunRequest:
    project_root: Path | None
    gf_executable: Path | None
    rgl_root: Path | None
    output_root: Path | None
    mode: ValidationMode
    target_file: str = ""
    checkpoint_id: str = ""
    scenario_filter: tuple[str, ...] = ()
    timeout_override: int | None = None
    max_files: int = 0
    keep_ok_details: bool = False
    diff_previous: bool = True
    skip_version_probe: bool = False
    no_compile: bool = False
    emit_cpu_stats: bool = False
    strict: bool = False
    advanced_overrides: Mapping[str, OverrideScalar] = field(
        default_factory=lambda: MappingProxyType({})
    )
    def __post_init__(self) -> None:
        for name in ("project_root", "gf_executable", "rgl_root", "output_root"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _path(value, name))
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be ValidationMode")
        _entry(self.target_file, "target_file")
        _entry(self.checkpoint_id, "checkpoint_id")
        object.__setattr__(self, "scenario_filter", _texts(self.scenario_filter, "scenario_filter"))
        if self.timeout_override is not None:
            _integer(self.timeout_override, "timeout_override", 1)
        _integer(self.max_files, "max_files", 0)
        for name in (
            "keep_ok_details", "diff_previous", "skip_version_probe",
            "no_compile", "emit_cpu_stats", "strict",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        object.__setattr__(self, "advanced_overrides", _overrides(self.advanced_overrides))
    @classmethod
    def from_state(cls, state: AppState) -> GuiRunRequest:
        if not isinstance(state, AppState):
            raise TypeError("state must be AppState")
        env, selection = state.environment, state.selection
        return cls(
            project_root=_optional_path(env.project_root),
            gf_executable=_optional_path(env.gf_executable),
            rgl_root=_optional_path(env.rgl_root),
            output_root=_optional_path(env.output_root),
            mode=selection.mode,
            target_file=selection.target_file,
            timeout_override=selection.timeout_sec,
            max_files=selection.max_files,
            keep_ok_details=selection.keep_ok_details,
            diff_previous=selection.diff_previous,
            skip_version_probe=selection.skip_version_probe,
            no_compile=selection.no_compile,
            emit_cpu_stats=selection.emit_cpu_stats,
        )
    def environment_state(self) -> EnvironmentState:
        return EnvironmentState(
            project_root=_path_text(self.project_root),
            rgl_root=_path_text(self.rgl_root),
            gf_executable=_path_text(self.gf_executable),
            output_root=_path_text(self.output_root),
        )
    def selection_state(self) -> SelectionState:
        return SelectionState(
            mode=self.mode,
            target_file=self.target_file,
            timeout_sec=self.timeout_override or 60,
            max_files=self.max_files,
            keep_ok_details=self.keep_ok_details,
            diff_previous=self.diff_previous,
            skip_version_probe=self.skip_version_probe,
            no_compile=self.no_compile,
            emit_cpu_stats=self.emit_cpu_stats,
        )
@dataclass(frozen=True, slots=True)
class ProjectView:
    loaded: bool = False
    valid: bool = False
    name: str = ""
    project_id: str = ""
    language_code: str = ""
    project_root: Path | None = None
    source_root: Path | None = None
    project_file: Path | None = None
    entrypoints: tuple[str, ...] = ()
    checkpoints: tuple[str, ...] = ()
    scenarios: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
@dataclass(frozen=True, slots=True)
class ProgressView:
    message: str = "Ready"
    stage: str | None = None
    subject: str | None = None
    completed: int | None = None
    total: int | None = None
    warnings: int = 0
    failures: int = 0
    started_at: datetime | None = None
    updated_at: datetime | None = None
    @property
    def indeterminate(self) -> bool:
        return self.total is None
    @property
    def fraction(self) -> float | None:
        if self.completed is None or not self.total:
            return None
        return self.completed / self.total
    def elapsed_seconds(self, now: datetime | None = None) -> float:
        if self.started_at is None:
            return 0.0
        endpoint = _utc(now) if now is not None else self.updated_at or datetime.now(UTC)
        return max(0.0, (endpoint - self.started_at).total_seconds())
@dataclass(frozen=True, slots=True)
class StatusCounts:
    ok: int = 0
    fail: int = 0
    error: int = 0
    skipped: int = 0
    def __post_init__(self) -> None:
        for name in ("ok", "fail", "error", "skipped"):
            _integer(getattr(self, name), name, 0)
@dataclass(frozen=True, slots=True)
class FailureCounts:
    direct: int = 0
    downstream: int = 0
    ambiguous: int = 0
    required_scenario: int = 0
    def __post_init__(self) -> None:
        for name in ("direct", "downstream", "ambiguous", "required_scenario"):
            _integer(getattr(self, name), name, 0)
@dataclass(frozen=True, slots=True)
class ResultView:
    headline: str
    overall_status: OverallStatus
    cancelled: bool
    mode: ValidationMode
    project_name: str
    run_id: str
    gf_version: str
    duration_ms: int
    files: StatusCounts
    scenarios: StatusCounts
    failures: FailureCounts
    run_dir: Path | None
@dataclass(frozen=True, slots=True)
class ArtifactAction:
    action_id: ArtifactActionId
    label: str
    path: Path
    enabled: bool
    directory: bool = False
    reason: str = ""
@dataclass(frozen=True, slots=True)
class ActivityItem:
    timestamp: datetime
    level: EventLevel
    message: str
    stage: str | None = None
    subject: str | None = None
@dataclass(frozen=True, slots=True)
class GuiSnapshot:
    request: GuiRunRequest
    project: ProjectView
    run_state: RunPresentationState
    progress: ProgressView
    result: ResultView | None
    artifacts: tuple[ArtifactAction, ...]
    activity: tuple[ActivityItem, ...]
    notices: tuple[str, ...]
    last_run: LastRunState
    can_run: bool
    can_cancel: bool
    can_switch_project: bool
    can_edit_environment: bool
    can_edit_request: bool
    can_open_last_run: bool
class GuiViewModel:
    """Mutable session state exposed through immutable snapshots."""
    __slots__ = (
        "_request", "_project", "_run_state", "_progress", "_result",
        "_artifacts", "_activity", "_notices", "_last_run",
    )
    def __init__(self, state: AppState) -> None:
        if not isinstance(state, AppState):
            raise TypeError("state must be AppState")
        self._request = GuiRunRequest.from_state(state)
        self._project = ProjectView()
        self._run_state = RunPresentationState.IDLE
        self._progress = ProgressView()
        self._result: ResultView | None = None
        self._artifacts: tuple[ArtifactAction, ...] = ()
        self._activity: list[ActivityItem] = []
        self._notices: list[str] = []
        self._last_run = state.last_run
    @property
    def request(self) -> GuiRunRequest:
        return self._request
    def update_request(self, **changes: object) -> GuiRunRequest:
        self._require_idle("run request")
        self._request = replace(self._request, **changes)
        return self._request
    def load_project(self, project: ProjectConfig) -> ProjectView:
        self._require_idle("project")
        self._project = project_view_from_config(project)
        self._request = replace(self._request, project_root=project.project_root)
        return self._project
    def reject_project(self, root: Path | None, issues: Iterable[str]) -> ProjectView:
        self._require_idle("project")
        self._project = ProjectView(
            loaded=True,
            valid=False,
            project_root=None if root is None else _path(root, "project_root"),
            issues=_texts(issues, "issues"),
        )
        self._request = replace(self._request, project_root=root)
        return self._project
    def clear_project(self) -> None:
        self._require_idle("project")
        self._project = ProjectView()
        self._request = replace(self._request, project_root=None, target_file="")
    def begin_run(self, timestamp: datetime | None = None) -> None:
        if not self._project.valid:
            raise RuntimeError("a valid project is required")
        self._require_idle("run")
        started = _utc(timestamp) if timestamp is not None else datetime.now(UTC)
        self._run_state = RunPresentationState.RUNNING
        self._progress = ProgressView(
            message="Starting validation…",
            started_at=started,
            updated_at=started,
        )
        self._append_activity(started, EventLevel.INFO, "Validation started")
    def apply_progress(self, event: ProgressEvent) -> ProgressView:
        if not isinstance(event, ProgressEvent):
            raise TypeError("event must be ProgressEvent")
        fields = {item.key: item.value for item in event.fields}
        warnings = _event_count(fields, "warning_count", self._progress.warnings)
        failures = _event_count(fields, "failure_count", self._progress.failures)
        if event.severity is EventLevel.WARN and "warning_count" not in fields:
            warnings += 1
        if event.severity in {EventLevel.ERROR, EventLevel.FATAL} and "failure_count" not in fields:
            failures += 1
        self._progress = ProgressView(
            message=event.message,
            stage=event.stage,
            subject=event.subject,
            completed=event.completed,
            total=event.total,
            warnings=warnings,
            failures=failures,
            started_at=self._progress.started_at or event.timestamp,
            updated_at=event.timestamp,
        )
        self._append_activity(
            event.timestamp, event.severity, event.message, event.stage, event.subject
        )
        return self._progress
    def request_cancellation(self) -> bool:
        if self._run_state is not RunPresentationState.RUNNING:
            return False
        self._run_state = RunPresentationState.CANCELLING
        now = datetime.now(UTC)
        self._progress = replace(self._progress, message="Cancelling…", updated_at=now)
        self._append_activity(now, EventLevel.WARN, "Cancellation requested")
        return True
    def complete_run(
        self,
        result: RunResult,
        *,
        path_probe: PathProbe | None = None,
    ) -> ResultView:
        if not isinstance(result, RunResult):
            raise TypeError("result must be RunResult")
        cancelled = self._run_state is RunPresentationState.CANCELLING
        self._result = result_view_from_run(result, cancelled=cancelled)
        self._artifacts = artifact_actions_from_result(result, path_probe=path_probe)
        self._run_state = RunPresentationState.COMPLETED
        self._progress = replace(
            self._progress,
            message=self._result.headline,
            updated_at=result.finished_at,
        )
        self._last_run = LastRunState(
            run_dir=str(result.run_paths.run_dir),
            summary_path=str(result.run_paths.summary_json),
            status_message=self._result.headline,
        )
        level = EventLevel.INFO if result.overall_status is OverallStatus.OK else EventLevel.WARN
        if result.overall_status is OverallStatus.ERROR:
            level = EventLevel.ERROR
        self._append_activity(result.finished_at, level, self._result.headline)
        return self._result
    def record_framework_failure(self, message: str) -> None:
        message = _text(message, "message")
        self._run_state = RunPresentationState.FAILED
        now = datetime.now(UTC)
        self._progress = replace(self._progress, message=message, updated_at=now)
        self.add_notice(message)
        self._append_activity(now, EventLevel.ERROR, message)
    def add_notice(self, message: str) -> None:
        self._notices.append(_text(message, "message"))
        del self._notices[:-_MAX_NOTICES]
    def clear_notices(self) -> None:
        self._notices.clear()
    def clear_activity(self) -> None:
        self._activity.clear()
    def persistable_state(self, base: AppState) -> AppState:
        if not isinstance(base, AppState):
            raise TypeError("base must be AppState")
        return replace(
            base,
            environment=self._request.environment_state(),
            selection=self._request.selection_state(),
            last_run=self._last_run,
        )
    def snapshot(self) -> GuiSnapshot:
        active = self._run_state in {
            RunPresentationState.RUNNING,
            RunPresentationState.CANCELLING,
        }
        return GuiSnapshot(
            request=self._request,
            project=self._project,
            run_state=self._run_state,
            progress=self._progress,
            result=self._result,
            artifacts=self._artifacts,
            activity=tuple(self._activity),
            notices=tuple(self._notices),
            last_run=self._last_run,
            can_run=self._project.valid and not active,
            can_cancel=self._run_state is RunPresentationState.RUNNING,
            can_switch_project=not active,
            can_edit_environment=not active,
            can_edit_request=not active,
            can_open_last_run=bool(self._last_run.run_dir or self._last_run.summary_path),
        )
    def _require_idle(self, subject: str) -> None:
        if self._run_state in {
            RunPresentationState.RUNNING,
            RunPresentationState.CANCELLING,
        }:
            raise RuntimeError(f"{subject} cannot change while a run is active")
    def _append_activity(
        self,
        timestamp: datetime,
        level: EventLevel,
        message: str,
        stage: str | None = None,
        subject: str | None = None,
    ) -> None:
        self._activity.append(
            ActivityItem(_utc(timestamp), level, _text(message, "message"), stage, subject)
        )
        del self._activity[:-_MAX_ACTIVITY]
def project_view_from_config(project: ProjectConfig) -> ProjectView:
    if not isinstance(project, ProjectConfig):
        raise TypeError("project must be ProjectConfig")
    identity = project.identity
    return ProjectView(
        loaded=True,
        valid=True,
        name=identity.name,
        project_id=str(identity.id),
        language_code=identity.language_code,
        project_root=project.project_root,
        source_root=project.source_root,
        project_file=project.project_file,
        entrypoints=tuple(path.as_posix() for path in project.modules.entrypoints),
        checkpoints=tuple(path.as_posix() for path in project.modules.checkpoints),
        scenarios=tuple(str(value) for value in project.validation.all_scenarios),
    )
def completion_message(status: OverallStatus, *, cancelled: bool = False) -> str:
    if not isinstance(status, OverallStatus):
        raise TypeError("status must be OverallStatus")
    if cancelled:
        return "Run cancelled"
    return {
        OverallStatus.OK: "Validation passed",
        OverallStatus.FAIL: "Validation completed with failures",
        OverallStatus.ERROR: "Validation error",
    }[status]
def result_view_from_run(result: RunResult, *, cancelled: bool = False) -> ResultView:
    if not isinstance(result, RunResult):
        raise TypeError("result must be RunResult")
    totals = result.totals
    return ResultView(
        headline=completion_message(result.overall_status, cancelled=cancelled),
        overall_status=result.overall_status,
        cancelled=cancelled,
        mode=result.run_config.mode,
        project_name=result.run_config.project.identity.name,
        run_id=result.run_paths.run_id,
        gf_version=result.gf_version,
        duration_ms=result.duration_ms,
        files=StatusCounts(totals.files_ok, totals.files_fail, totals.files_error, totals.files_skipped),
        scenarios=StatusCounts(
            totals.scenarios_ok,
            totals.scenarios_fail,
            totals.scenarios_error,
            totals.scenarios_skipped,
        ),
        failures=FailureCounts(
            totals.direct_fail,
            totals.downstream_fail,
            totals.ambiguous_fail,
            totals.required_scenario_fail,
        ),
        run_dir=result.run_paths.run_dir,
    )
def artifact_actions_from_result(
    result: RunResult,
    *,
    path_probe: PathProbe | None = None,
) -> tuple[ArtifactAction, ...]:
    if not isinstance(result, RunResult):
        raise TypeError("result must be RunResult")
    probe = path_probe or Path.exists
    paths = result.run_paths
    declarations = (
        (ArtifactActionId.RUN_DIRECTORY, "Open Run Directory", paths.run_dir, True),
        (ArtifactActionId.MACHINE_SUMMARY, "Open Machine Summary", paths.summary_json, False),
        (ArtifactActionId.HUMAN_SUMMARY, "Open Human Summary", paths.summary_md, False),
        (ArtifactActionId.AI_READY_PACKET, "Open AI Ready Packet", paths.ai_ready_md, False),
        (ArtifactActionId.MASTER_LOG, "Open Master Log", paths.master_log, False),
        (ArtifactActionId.ALL_OPERATION_LOGS, "Open All Operation Logs", paths.all_logs, False),
        (ArtifactActionId.ALL_SCAN_LOGS, "Open All Scan Logs", paths.all_scan_logs, False),
        (ArtifactActionId.MANIFEST, "Open Manifest", paths.manifest_json, False),
        (ArtifactActionId.PGF_DIRECTORY, "Open PGF Directory", paths.pgf_dir, True),
        (ArtifactActionId.DETAILS_DIRECTORY, "Open Details Directory", paths.details_dir, True),
    )
    actions: list[ArtifactAction] = []
    for action_id, label, path, directory in declarations:
        try:
            enabled = bool(probe(path))
            reason = "" if enabled else "Artifact is not available"
        except OSError as exc:
            enabled = False
            reason = f"Artifact could not be inspected: {type(exc).__name__}"
        actions.append(ArtifactAction(action_id, label, path, enabled, directory, reason))
    return tuple(actions)
def _overrides(values: Mapping[str, OverrideScalar]) -> Mapping[str, OverrideScalar]:
    if not isinstance(values, Mapping) or len(values) > 64:
        raise ValueError("advanced_overrides must be a bounded mapping")
    result: dict[str, OverrideScalar] = {}
    for key, value in values.items():
        key = _text(key, "advanced override key")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError(f"advanced override {key!r} must be scalar")
        result[key] = value
    return MappingProxyType(dict(sorted(result.items())))
def _texts(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if index >= _MAX_ITEMS:
            raise ValueError(f"{field_name} contains too many items")
        value = _text(value, f"{field_name}[{index}]")
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
def _event_count(fields: Mapping[str, object], key: str, fallback: int) -> int:
    value = fields.get(key)
    return value if type(value) is int and value >= 0 else fallback
def _optional_path(value: str | None) -> Path | None:
    return None if value is None else Path(value)
def _path_text(value: Path | None) -> str | None:
    return None if value is None else str(value)
def _path(value: object, field_name: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{field_name} must be str or Path")
    path = Path(value)
    if not str(path) or "\x00" in str(path):
        raise ValueError(f"{field_name} must be a non-empty path")
    return path
def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be a timezone-aware datetime")
    return value.astimezone(UTC)
def _integer(value: object, field_name: str, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field_name} must be an integer >= {minimum}")
    return value
def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{field_name} must be a non-empty string without NUL")
    if len(value) > _MAX_TEXT:
        raise ValueError(f"{field_name} exceeds {_MAX_TEXT} characters")
    return value
def _entry(value: object, field_name: str) -> str:
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError(f"{field_name} must be a string without NUL")
    if value and value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    return value
