"""Canonical production-model builders for GF Wordbench tests."""

from __future__ import annotations

import hashlib
import inspect
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeVar, cast

from gf_wordbench.config.defaults import (
    DEFAULT_AGGREGATE_LOGS,
    DEFAULT_DIFF_PREVIOUS,
    DEFAULT_EMIT_CPU_STATS,
    DEFAULT_EVIDENCE_LEVEL,
    DEFAULT_GENERATE_AI_READY,
    DEFAULT_GENERATE_MANIFEST,
    DEFAULT_KEEP_OK_DETAILS,
    DEFAULT_MAX_FILES,
    DEFAULT_NO_COMPILE,
    DEFAULT_SKIP_VERSION_PROBE,
    DEFAULT_STATE_FILENAME,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VALIDATION_MODE,
    SUPPORTED_APP_STATE_SCHEMA_MAJOR,
    SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR,
    SUPPORTED_PROJECT_SCHEMA_MAJOR,
    SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
)
from gf_wordbench.config.models import (
    AppConfig,
    OutputDefaults,
    ResolvedEnvironment,
    RunConfig,
    SchemaSupport,
    SelectionDefaults,
    ValidationTarget,
)
from gf_wordbench.kernel.ids import (
    validate_project_id,
    validate_scenario_id,
    validate_schema_id,
)
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    TargetKind,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.projects.models import (
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.models.results import FileResult, RunResult, RunTotals
from gf_wordbench.validation.scanning.models import ScanCounts
from gf_wordbench.version import __version__

if TYPE_CHECKING:
    from gf_wordbench.infrastructure.process.models import (
        ArtifactObservation,
        ProcessRequest,
        ProcessResult,
    )
    from gf_wordbench.validation.compilation.models import (
        CompileSummary,
        SourceFingerprint,
    )
    from gf_wordbench.validation.scenarios.models import (
        ScenarioAssertionResult,
        ScenarioResult,
        ScenarioSectionResult,
    )

__all__ = (
    "DEFAULT_DURATION_MS",
    "DEFAULT_FINISHED_AT",
    "DEFAULT_RUN_ID",
    "DEFAULT_STARTED_AT",
    "make_app_config",
    "make_compile_summary",
    "make_file_result",
    "make_process_result",
    "make_project_config",
    "make_run_config",
    "make_run_paths",
    "make_run_result",
    "make_scenario_result",
)

DEFAULT_RUN_ID: Final[str] = "20260101_120000"
DEFAULT_STARTED_AT: Final[datetime] = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
DEFAULT_DURATION_MS: Final[int] = 25
DEFAULT_FINISHED_AT: Final[datetime] = DEFAULT_STARTED_AT + timedelta(
    milliseconds=DEFAULT_DURATION_MS
)
_DEFAULT_SOURCE_BYTES: Final[bytes] = b"abstract Example = { cat Item ; }\n"
_DEFAULT_SCENARIO_BYTES: Final[bytes] = b"-- GF Wordbench scenario\n"
_UNSET: Final[object] = object()
_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class _SourceFingerprintFallback:
    size_bytes: int
    hash_algorithm: str
    hash: str
    last_modified_utc: datetime

    def __post_init__(self) -> None:
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if self.hash_algorithm != "sha256":
            raise ValueError("hash_algorithm must be 'sha256'")
        if len(self.hash) != 64 or any(
            character not in "0123456789abcdef" for character in self.hash
        ):
            raise ValueError("hash must be a lowercase SHA-256 digest")
        value = _aware_utc(self.last_modified_utc, field="last_modified_utc")
        object.__setattr__(self, "last_modified_utc", value)


@dataclass(frozen=True, slots=True)
class _CompileSummaryFallback:
    target_id: str
    target_kind: str
    status: ValidationStatus
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    launched: bool
    timed_out: bool
    cancelled: bool
    duration_ms: int
    error_kind: ErrorKind
    first_error: str
    error_detail: str
    stdout_path: Path | None
    stderr_path: Path | None
    expected_artifacts: tuple[Path, ...]
    produced_artifacts: tuple[Path, ...]
    artifact_checks_passed: bool

    def __post_init__(self) -> None:
        _required_text(self.target_id, field="target_id")
        _required_text(self.target_kind, field="target_kind")
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be a ValidationStatus")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be an ErrorKind")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int):
            raise TypeError("duration_ms must be an integer")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        for name in (
            "launched",
            "timed_out",
            "cancelled",
            "artifact_checks_passed",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")
        if self.timed_out and self.error_kind is not ErrorKind.TIMEOUT:
            raise ValueError("timed_out requires error_kind TIMEOUT")
        if self.status is ValidationStatus.OK:
            if self.exit_code != 0 or self.error_kind is not ErrorKind.OK:
                raise ValueError("OK compile requires exit_code zero and error_kind OK")
            if not self.artifact_checks_passed:
                raise ValueError("OK compile requires passing artifact checks")
        if self.exit_code not in (None, 0) and self.error_kind is ErrorKind.OK:
            raise ValueError("a non-zero exit code cannot use error_kind OK")
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "working_directory", Path(self.working_directory))
        object.__setattr__(
            self,
            "stdout_path",
            None if self.stdout_path is None else Path(self.stdout_path),
        )
        object.__setattr__(
            self,
            "stderr_path",
            None if self.stderr_path is None else Path(self.stderr_path),
        )
        object.__setattr__(
            self,
            "expected_artifacts",
            tuple(Path(path) for path in self.expected_artifacts),
        )
        object.__setattr__(
            self,
            "produced_artifacts",
            tuple(Path(path) for path in self.produced_artifacts),
        )


def make_app_config(
    *,
    producer_name: str = "gf-wordbench",
    producer_version: str = __version__,
    mode: ValidationMode = DEFAULT_VALIDATION_MODE,
    timeout_sec: int = DEFAULT_TIMEOUT_SECONDS,
    max_files: int = DEFAULT_MAX_FILES,
    keep_ok_details: bool = DEFAULT_KEEP_OK_DETAILS,
    diff_previous: bool = DEFAULT_DIFF_PREVIOUS,
    skip_version_probe: bool = DEFAULT_SKIP_VERSION_PROBE,
    no_compile: bool = DEFAULT_NO_COMPILE,
    emit_cpu_stats: bool = DEFAULT_EMIT_CPU_STATS,
    evidence_level: str = DEFAULT_EVIDENCE_LEVEL,
    generate_manifest: bool = DEFAULT_GENERATE_MANIFEST,
    generate_ai_ready: bool = DEFAULT_GENERATE_AI_READY,
    aggregate_logs: bool = DEFAULT_AGGREGATE_LOGS,
    project_schema_major: int = SUPPORTED_PROJECT_SCHEMA_MAJOR,
    app_state_schema_major: int = SUPPORTED_APP_STATE_SCHEMA_MAJOR,
    run_summary_schema_major: int = SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
    artifact_manifest_schema_major: int = SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR,
    state_filename: str = DEFAULT_STATE_FILENAME,
) -> AppConfig:
    """Build canonical language-neutral framework defaults."""

    return AppConfig(
        producer=ProducerInfo(
            name=producer_name,
            version=producer_version,
        ),
        selection_defaults=SelectionDefaults(
            mode=mode,
            timeout_sec=timeout_sec,
            max_files=max_files,
            keep_ok_details=keep_ok_details,
            diff_previous=diff_previous,
            skip_version_probe=skip_version_probe,
            no_compile=no_compile,
            emit_cpu_stats=emit_cpu_stats,
        ),
        output_defaults=OutputDefaults(
            evidence_level=cast(Any, evidence_level),
            generate_manifest=generate_manifest,
            generate_ai_ready=generate_ai_ready,
            aggregate_logs=aggregate_logs,
        ),
        schema_support=SchemaSupport(
            project_major=project_schema_major,
            app_state_major=app_state_schema_major,
            run_summary_major=run_summary_schema_major,
            artifact_manifest_major=artifact_manifest_schema_major,
        ),
        state_filename=state_filename,
    )


def make_project_config(
    *,
    project_root: Path | str | None = None,
    project_id: str = "example-language",
    project_name: str = "Example Language",
    language_code: str = "eng",
    identity_root: Path | str = Path("."),
    source_directory: Path | str = Path("src"),
    source_glob: str = "*.gf",
    include_regex: str = r"^[A-Z][A-Za-z0-9_]*\.gf$",
    exclude_regex: str = r"(\.bak\.gf$|\.tmp\.gf$|\s)",
    gf_path_parts: Sequence[str] = ("src",),
    minimum_gf_version: str = "",
    entrypoints: Iterable[Path | str] = (Path("GrammarEng.gf"),),
    checkpoints: Iterable[Path | str] = (Path("MorphoEng.gf"),),
    required_scenarios: Iterable[str] = ("load",),
    optional_scenarios: Iterable[str] = (),
    release_requires_pgf: bool = True,
    schema_id: str = str(PROJECT_SCHEMA_ID),
    schema_version: str = PROJECT_SCHEMA_VERSION,
) -> ProjectConfig:
    """Build one valid active-project configuration without touching disk."""

    root = _absolute_path(
        project_root if project_root is not None else _default_root() / "project"
    )
    source_directory_path = Path(source_directory)
    source_root = _absolute_path(root / source_directory_path)

    return ProjectConfig(
        schema_id=validate_schema_id(schema_id),
        schema_version=schema_version,
        identity=ProjectIdentity(
            id=validate_project_id(project_id),
            name=project_name,
            language_code=language_code,
            root=Path(identity_root),
        ),
        sources=SourceConfig(
            directory=source_directory_path,
            glob=source_glob,
            include_regex=include_regex,
            exclude_regex=exclude_regex,
        ),
        gf=GFProjectConfig(
            path_parts=tuple(gf_path_parts),
            minimum_version=minimum_gf_version,
        ),
        modules=ModuleTargets(
            entrypoints=tuple(Path(path) for path in entrypoints),
            checkpoints=tuple(Path(path) for path in checkpoints),
        ),
        validation=ValidationPolicy(
            required_scenarios=tuple(
                validate_scenario_id(value) for value in required_scenarios
            ),
            optional_scenarios=tuple(
                validate_scenario_id(value) for value in optional_scenarios
            ),
            release_requires_pgf=release_requires_pgf,
        ),
        project_file=root / "project.toml",
        project_root=root,
        source_root=source_root,
    )


def make_run_config(
    *,
    project: ProjectConfig | None = None,
    project_root: Path | str | None = None,
    environment: ResolvedEnvironment | None = None,
    mode: ValidationMode = DEFAULT_VALIDATION_MODE,
    target: ValidationTarget | None = None,
    timeout_sec: int = DEFAULT_TIMEOUT_SECONDS,
    max_files: int = DEFAULT_MAX_FILES,
    keep_ok_details: bool = DEFAULT_KEEP_OK_DETAILS,
    diff_previous: bool = DEFAULT_DIFF_PREVIOUS,
    skip_version_probe: bool = DEFAULT_SKIP_VERSION_PROBE,
    no_compile: bool = DEFAULT_NO_COMPILE,
    emit_cpu_stats: bool = DEFAULT_EMIT_CPU_STATS,
    selected_checkpoints: Iterable[Path | str] | None = None,
    selected_entrypoints: Iterable[Path | str] | None = None,
    selected_scenarios: Iterable[str] | None = None,
    release_requires_pgf: bool | None = None,
    evidence_level: str = DEFAULT_EVIDENCE_LEVEL,
    compatibility_warnings: Iterable[str] = (),
    rgl_root: Path | str | None = None,
    gf_executable: Path | str | None = None,
    output_root: Path | str | None = None,
    gf_path: Iterable[Path | str] | None = None,
) -> RunConfig:
    """Build one fully resolved non-interactive run configuration."""

    active_project = project or make_project_config(project_root=project_root)
    base = active_project.project_root.parent
    resolved_rgl = _absolute_path(rgl_root or base / "rgl")
    resolved_executable = _absolute_path(gf_executable or base / "bin" / "gf")
    resolved_output = _absolute_path(output_root or base / "runs")

    resolved_environment = environment or ResolvedEnvironment(
        project_root=active_project.project_root,
        rgl_root=resolved_rgl,
        gf_executable=resolved_executable,
        output_root=resolved_output,
        gf_path=tuple(
            _absolute_path(path)
            for path in (
                gf_path
                if gf_path is not None
                else (active_project.source_root, resolved_rgl)
            )
        ),
    )

    checkpoint_paths = (
        tuple(_absolute_path(path) for path in selected_checkpoints)
        if selected_checkpoints is not None
        else tuple(
            _absolute_path(active_project.source_root / path)
            for path in active_project.modules.checkpoints
        )
        if mode is ValidationMode.CHECKPOINT
        else ()
    )
    entrypoint_paths = (
        tuple(_absolute_path(path) for path in selected_entrypoints)
        if selected_entrypoints is not None
        else tuple(
            _absolute_path(active_project.source_root / path)
            for path in active_project.modules.entrypoints
        )
        if mode is ValidationMode.RELEASE
        else ()
    )
    scenario_ids = (
        tuple(selected_scenarios)
        if selected_scenarios is not None
        else tuple(str(value) for value in active_project.validation.all_scenarios)
        if mode is ValidationMode.RELEASE
        else ()
    )

    resolved_target = target
    if mode is ValidationMode.QUICK and resolved_target is None:
        candidates = (
            *active_project.modules.checkpoints,
            *active_project.modules.entrypoints,
        )
        value = str(candidates[0]) if candidates else "Example.gf"
        resolved_target = ValidationTarget(
            kind=TargetKind.FILE,
            value=value,
        )

    return RunConfig(
        project=active_project,
        environment=resolved_environment,
        mode=mode,
        target=resolved_target,
        timeout_sec=timeout_sec,
        max_files=max_files,
        keep_ok_details=keep_ok_details,
        diff_previous=diff_previous,
        skip_version_probe=skip_version_probe,
        no_compile=no_compile,
        emit_cpu_stats=emit_cpu_stats,
        selected_checkpoints=checkpoint_paths,
        selected_entrypoints=entrypoint_paths,
        selected_scenarios=scenario_ids,
        release_requires_pgf=(
            active_project.validation.release_requires_pgf
            if release_requires_pgf is None
            else release_requires_pgf
        ),
        evidence_level=cast(Any, evidence_level),
        compatibility_warnings=tuple(compatibility_warnings),
    )


def make_run_paths(
    *,
    output_root: Path | str | None = None,
    run_id: str = DEFAULT_RUN_ID,
    run_dir: Path | str | None = None,
) -> RunPaths:
    """Build canonical run-owned paths without creating directories."""

    directory = (
        _absolute_path(run_dir)
        if run_dir is not None
        else _absolute_path(output_root or _default_root() / "runs")
        / f"run_{run_id}"
    )
    return RunPaths(
        run_id=run_id,
        run_dir=directory,
        summary_json=directory / "summary.json",
        summary_md=directory / "summary.md",
        ai_ready_md=directory / "AI_READY.md",
        top_errors_txt=directory / "top_errors.txt",
        manifest_json=directory / "manifest.json",
        details_dir=directory / "details",
        raw_dir=directory / "raw",
        master_log=directory / "raw" / "master.log",
        all_scan_logs=directory / "raw" / "ALL_SCAN_LOGS.TXT",
        all_logs=directory / "raw" / "ALL_LOGS.TXT",
        raw_compile_dir=directory / "raw" / "compile",
        raw_scan_dir=directory / "raw" / "scan",
        raw_scenarios_dir=directory / "raw" / "scenarios",
        artifacts_dir=directory / "artifacts",
        gfo_dir=directory / "artifacts" / "gfo",
        out_dir=directory / "artifacts" / "out",
        pgf_dir=directory / "artifacts" / "pgf",
    )


def make_process_result(
    request: ProcessRequest | None = None,
    **overrides: object,
) -> ProcessResult:
    """Delegate to the canonical deterministic process-result factory."""

    from tests.helpers.fake_processes import make_process_result as factory

    return factory(request, **overrides)


def make_compile_summary(
    *,
    target_id: str = "example-module",
    target_kind: str = "source",
    status: ValidationStatus = ValidationStatus.OK,
    command: Iterable[str] | None = None,
    working_directory: Path | str | None = None,
    exit_code: int | None | object = _UNSET,
    launched: bool | object = _UNSET,
    timed_out: bool = False,
    cancelled: bool = False,
    duration_ms: int = DEFAULT_DURATION_MS,
    error_kind: ErrorKind | object = _UNSET,
    first_error: str | object = _UNSET,
    error_detail: str = "",
    stdout_path: Path | str | None | object = _UNSET,
    stderr_path: Path | str | None | object = _UNSET,
    expected_artifacts: Iterable[Path | str] | None = None,
    produced_artifacts: Iterable[Path | str] | None = None,
    artifact_checks_passed: bool | object = _UNSET,
) -> CompileSummary:
    """Build the production compile-summary model with coherent defaults."""

    normalized_status = _enum(status, ValidationStatus, field="status")
    stem = _safe_stem(target_id)
    root = _absolute_path(working_directory or _default_root() / "project")
    expected = tuple(
        Path(path)
        for path in (
            expected_artifacts
            if expected_artifacts is not None
            else (Path("artifacts") / "gfo" / f"{stem}.gfo",)
        )
    )

    defaults = _compile_defaults(
        normalized_status,
        timed_out=timed_out,
        cancelled=cancelled,
    )
    normalized_exit_code = defaults["exit_code"] if exit_code is _UNSET else exit_code
    normalized_launched = defaults["launched"] if launched is _UNSET else launched
    normalized_error_kind = (
        defaults["error_kind"]
        if error_kind is _UNSET
        else error_kind
    )
    normalized_first_error = (
        defaults["first_error"]
        if first_error is _UNSET
        else first_error
    )
    normalized_artifact_check = (
        defaults["artifact_checks_passed"]
        if artifact_checks_passed is _UNSET
        else artifact_checks_passed
    )
    normalized_stdout = (
        defaults["stdout_path"]
        if stdout_path is _UNSET
        else stdout_path
    )
    normalized_stderr = (
        defaults["stderr_path"]
        if stderr_path is _UNSET
        else stderr_path
    )
    produced = tuple(
        Path(path)
        for path in (
            produced_artifacts
            if produced_artifacts is not None
            else expected
            if normalized_status is ValidationStatus.OK
            else ()
        )
    )

    model = _optional_model(
        "gf_wordbench.validation.compilation.models",
        "CompileSummary",
        _CompileSummaryFallback,
    )
    candidates: dict[str, object] = {
        "target_id": target_id,
        "target_kind": target_kind,
        "status": normalized_status,
        "command": tuple(command or ("gf", "-make", f"{stem}.gf")),
        "working_directory": root,
        "exit_code": normalized_exit_code,
        "launched": normalized_launched,
        "timed_out": timed_out,
        "cancelled": cancelled,
        "duration_ms": duration_ms,
        "error_kind": _enum(normalized_error_kind, ErrorKind, field="error_kind"),
        "first_error": cast(str, normalized_first_error),
        "error_detail": error_detail,
        "stdout_path": (
            None if normalized_stdout is None else Path(cast(Any, normalized_stdout))
        ),
        "stderr_path": (
            None if normalized_stderr is None else Path(cast(Any, normalized_stderr))
        ),
        "expected_artifacts": expected,
        "produced_artifacts": produced,
        "artifact_checks_passed": normalized_artifact_check,
    }
    return cast("CompileSummary", _construct_supported(model, candidates))


def make_file_result(
    *,
    file_path: Path | str = Path("src/Example.gf"),
    module_name: str | None = None,
    status: ValidationStatus = ValidationStatus.OK,
    diagnostic_class: DiagnosticClass | None = None,
    is_direct: bool | None = None,
    blocked_by: Iterable[str] = (),
    scan_counts: ScanCounts | None = None,
    fingerprint: SourceFingerprint | None = None,
    compile_summary: CompileSummary | None = None,
    scan_log_path: Path | str | None | object = _UNSET,
    artifacts: Iterable[object] = (),
    source_bytes: bytes = _DEFAULT_SOURCE_BYTES,
    last_modified_utc: datetime = DEFAULT_STARTED_AT,
) -> FileResult:
    """Build one valid structured file result."""

    path = Path(file_path)
    name = module_name or path.stem
    normalized_status = _enum(status, ValidationStatus, field="status")
    classification = diagnostic_class or _default_diagnostic_class(normalized_status)
    blockers = tuple(blocked_by)
    if classification is DiagnosticClass.DOWNSTREAM and not blockers:
        blockers = ("upstream-subject",)
    direct = (
        classification is DiagnosticClass.DIRECT
        if is_direct is None
        else is_direct
    )
    summary = compile_summary or make_compile_summary(
        target_id=name,
        status=normalized_status,
    )
    fingerprint_value = fingerprint or _make_source_fingerprint(
        source_bytes,
        last_modified_utc=last_modified_utc,
    )
    log_path = (
        Path("raw") / "scan" / f"{name}.log"
        if scan_log_path is _UNSET
        else None
        if scan_log_path is None
        else Path(scan_log_path)
    )

    return FileResult(
        file_path=path,
        module_name=name,
        status=normalized_status,
        diagnostic_class=classification,
        is_direct=direct,
        blocked_by=list(blockers),
        scan_counts=scan_counts or ScanCounts(),
        fingerprint=fingerprint_value,
        compile_summary=summary,
        scan_log_path=log_path,
        artifacts=list(artifacts),
    )


def make_scenario_result(
    *,
    scenario_id: str = "load",
    script_path: Path | str | None = None,
    script_bytes: bytes = _DEFAULT_SCENARIO_BYTES,
    script_sha256: str | None = None,
    required: bool = True,
    status: ValidationStatus = ValidationStatus.OK,
    execution_state: ExecutionState | None | object = _UNSET,
    command: Iterable[str] | None = None,
    working_directory: Path | str | None = None,
    exit_code: int | None | object = _UNSET,
    timed_out: bool = False,
    cancelled: bool = False,
    duration_ms: int = DEFAULT_DURATION_MS,
    stdout_path: Path | str | None | object = _UNSET,
    stderr_path: Path | str | None | object = _UNSET,
    normalized_output_path: Path | str | None | object = _UNSET,
    gold_path: Path | str | None = None,
    gold_match: bool | None = None,
    gold_diff_path: Path | str | None = None,
    diagnostic_class: DiagnosticClass | None = None,
    error_kind: ErrorKind | None = None,
    primary_message: str | None = None,
    sections: Iterable[ScenarioSectionResult] = (),
    assertions: Iterable[ScenarioAssertionResult] = (),
    artifacts: Iterable[ArtifactObservation] = (),
    blocked_by: Iterable[str] = (),
) -> ScenarioResult:
    """Build one valid production scenario result."""

    normalized_status = _enum(status, ValidationStatus, field="status")
    defaults = _scenario_defaults(
        normalized_status,
        timed_out=timed_out,
        cancelled=cancelled,
    )
    state = (
        defaults["execution_state"]
        if execution_state is _UNSET
        else execution_state
    )
    normalized_exit_code = defaults["exit_code"] if exit_code is _UNSET else exit_code
    classification = diagnostic_class or _default_diagnostic_class(normalized_status)
    blockers = tuple(blocked_by)
    if classification is DiagnosticClass.DOWNSTREAM and not blockers:
        blockers = ("upstream-scenario",)
    kind = error_kind or cast(ErrorKind, defaults["error_kind"])
    message = primary_message or cast(str, defaults["primary_message"])
    script = Path(script_path or Path("scenarios") / f"{scenario_id}.gfs")
    stdout = defaults["stdout_path"] if stdout_path is _UNSET else stdout_path
    stderr = defaults["stderr_path"] if stderr_path is _UNSET else stderr_path
    normalized = (
        defaults["normalized_output_path"]
        if normalized_output_path is _UNSET
        else normalized_output_path
    )

    model = _required_model(
        "gf_wordbench.validation.scenarios.models",
        "ScenarioResult",
    )
    candidates: dict[str, object] = {
        "scenario_id": validate_scenario_id(scenario_id),
        "script_path": script,
        "script_sha256": script_sha256 or hashlib.sha256(script_bytes).hexdigest(),
        "required": required,
        "status": normalized_status,
        "execution_state": state,
        "command": tuple(
            command
            or (() if state is None else ("gf", "-run", scenario_id))
        ),
        "working_directory": _absolute_path(
            working_directory or _default_root() / "project"
        ),
        "exit_code": normalized_exit_code,
        "timed_out": timed_out,
        "cancelled": cancelled,
        "duration_ms": duration_ms,
        "stdout_path": None if stdout is None else Path(cast(Any, stdout)),
        "stderr_path": None if stderr is None else Path(cast(Any, stderr)),
        "normalized_output_path": (
            None if normalized is None else Path(cast(Any, normalized))
        ),
        "gold_path": None if gold_path is None else Path(gold_path),
        "gold_match": gold_match,
        "gold_diff_path": None if gold_diff_path is None else Path(gold_diff_path),
        "diagnostic_class": classification,
        "error_kind": kind,
        "primary_message": message,
        "sections": tuple(sections),
        "assertions": tuple(assertions),
        "artifacts": tuple(artifacts),
        "blocked_by": blockers,
    }
    return cast("ScenarioResult", _construct_supported(model, candidates))


def make_run_result(
    *,
    run_config: RunConfig | None = None,
    run_paths: RunPaths | None = None,
    started_at: datetime = DEFAULT_STARTED_AT,
    finished_at: datetime | None = None,
    duration_ms: int = DEFAULT_DURATION_MS,
    gf_version: str = "3.12",
    file_results: Iterable[FileResult] | None = None,
    scenario_results: Iterable[ScenarioResult] = (),
    diff_entries: Iterable[object] = (),
    top_errors: Iterable[object] = (),
    totals: RunTotals | None = None,
    overall_status: OverallStatus | None = None,
    files_seen: int | None = None,
    files_excluded: int = 0,
    excluded_noise: int = 0,
) -> RunResult:
    """Build a deterministic aggregate run result and derived totals."""

    config = run_config or make_run_config()
    paths = run_paths or make_run_paths(
        output_root=config.environment.output_root,
    )
    files = sorted(
        tuple(file_results) if file_results is not None else (make_file_result(),),
        key=lambda result: result.file_path.as_posix(),
    )
    scenarios = tuple(scenario_results)
    diffs = sorted(tuple(diff_entries), key=_diff_sort_key)
    errors = sorted(tuple(top_errors), key=_top_error_sort_key)
    computed_totals = totals or _run_totals(
        files,
        scenarios,
        files_seen=files_seen,
        files_excluded=files_excluded,
        excluded_noise=excluded_noise,
        overall_status=overall_status,
    )
    terminal_status = overall_status or computed_totals.overall_status
    if terminal_status is not computed_totals.overall_status:
        raise ValueError("overall_status must agree with totals.overall_status")
    started = _aware_utc(started_at, field="started_at")
    finished = _aware_utc(
        finished_at or started + timedelta(milliseconds=duration_ms),
        field="finished_at",
    )

    return RunResult(
        run_config=config,
        run_paths=paths,
        started_at=started,
        finished_at=finished,
        duration_ms=duration_ms,
        gf_version=gf_version,
        overall_status=terminal_status,
        file_results=list(files),
        scenario_results=list(scenarios),
        diff_entries=list(diffs),
        top_errors=list(errors),
        totals=computed_totals,
    )


def _default_root() -> Path:
    return (Path.cwd().resolve() / ".gf-wordbench-test-data").resolve()


def _absolute_path(value: Path | str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve(strict=False)


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or "\x00" in value:
        raise ValueError(f"{field} must be non-empty and NUL-free")
    return value


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _enum(value: object, enum_type: type[_T], *, field: str) -> _T:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)  # type: ignore[call-arg,return-value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc


def _safe_stem(value: str) -> str:
    text = _required_text(value, field="identifier")
    return "".join(character if character.isalnum() else "_" for character in text)


def _optional_model(module_name: str, name: str, fallback: type[_T]) -> type[_T]:
    try:
        module = import_module(module_name)
    except ImportError:
        return fallback
    value = getattr(module, name, fallback)
    if not isinstance(value, type):
        raise TypeError(f"{module_name}.{name} must be a class")
    return cast(type[_T], value)


def _required_model(module_name: str, name: str) -> type[Any]:
    module = import_module(module_name)
    value = getattr(module, name)
    if not isinstance(value, type):
        raise TypeError(f"{module_name}.{name} must be a class")
    return value


def _construct_supported(model: type[_T], candidates: Mapping[str, object]) -> _T:
    parameters = inspect.signature(model).parameters
    accepts_keywords = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    values = (
        dict(candidates)
        if accepts_keywords
        else {
            name: candidates[name]
            for name in parameters
            if name in candidates and name not in {"self", "cls"}
        }
    )
    missing = tuple(
        name
        for name, parameter in parameters.items()
        if name not in {"self", "cls"}
        and parameter.kind
        not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        and parameter.default is inspect.Parameter.empty
        and name not in values
    )
    if missing:
        raise TypeError(
            f"{model.__module__}.{model.__name__} requires unsupported fields: "
            + ", ".join(missing)
        )
    return model(**values)


def _make_source_fingerprint(
    content: bytes,
    *,
    last_modified_utc: datetime,
) -> SourceFingerprint:
    if not isinstance(content, bytes):
        raise TypeError("source_bytes must be bytes")
    model = _optional_model(
        "gf_wordbench.validation.compilation.models",
        "SourceFingerprint",
        _SourceFingerprintFallback,
    )
    return cast(
        "SourceFingerprint",
        _construct_supported(
            model,
            {
                "size_bytes": len(content),
                "hash_algorithm": "sha256",
                "hash": hashlib.sha256(content).hexdigest(),
                "last_modified_utc": _aware_utc(
                    last_modified_utc,
                    field="last_modified_utc",
                ),
            },
        ),
    )


def _default_diagnostic_class(status: ValidationStatus) -> DiagnosticClass:
    if status is ValidationStatus.OK:
        return DiagnosticClass.OK
    if status is ValidationStatus.SKIPPED:
        return DiagnosticClass.SKIPPED
    return DiagnosticClass.DIRECT


def _compile_defaults(
    status: ValidationStatus,
    *,
    timed_out: bool,
    cancelled: bool,
) -> dict[str, object]:
    if timed_out:
        if status is not ValidationStatus.ERROR:
            raise ValueError("timed_out compile requires ERROR status")
        return {
            "exit_code": None,
            "launched": True,
            "error_kind": ErrorKind.TIMEOUT,
            "first_error": "GF compilation timed out.",
            "artifact_checks_passed": False,
            "stdout_path": Path("raw/compile/example.stdout.log"),
            "stderr_path": Path("raw/compile/example.stderr.log"),
        }
    if cancelled:
        if status is not ValidationStatus.ERROR:
            raise ValueError("cancelled compile requires ERROR status")
        return {
            "exit_code": None,
            "launched": True,
            "error_kind": ErrorKind.TOOL,
            "first_error": "GF compilation was cancelled.",
            "artifact_checks_passed": False,
            "stdout_path": Path("raw/compile/example.stdout.log"),
            "stderr_path": Path("raw/compile/example.stderr.log"),
        }
    if status is ValidationStatus.OK:
        return {
            "exit_code": 0,
            "launched": True,
            "error_kind": ErrorKind.OK,
            "first_error": "",
            "artifact_checks_passed": True,
            "stdout_path": Path("raw/compile/example.stdout.log"),
            "stderr_path": Path("raw/compile/example.stderr.log"),
        }
    if status is ValidationStatus.FAIL:
        return {
            "exit_code": 1,
            "launched": True,
            "error_kind": ErrorKind.OTHER,
            "first_error": "GF validation failed.",
            "artifact_checks_passed": False,
            "stdout_path": Path("raw/compile/example.stdout.log"),
            "stderr_path": Path("raw/compile/example.stderr.log"),
        }
    if status is ValidationStatus.SKIPPED:
        return {
            "exit_code": None,
            "launched": False,
            "error_kind": ErrorKind.OK,
            "first_error": "Compilation intentionally skipped.",
            "artifact_checks_passed": False,
            "stdout_path": None,
            "stderr_path": None,
        }
    return {
        "exit_code": None,
        "launched": False,
        "error_kind": ErrorKind.TOOL,
        "first_error": "GF compilation could not be completed.",
        "artifact_checks_passed": False,
        "stdout_path": None,
        "stderr_path": None,
    }


def _scenario_defaults(
    status: ValidationStatus,
    *,
    timed_out: bool,
    cancelled: bool,
) -> dict[str, object]:
    if timed_out:
        if status is not ValidationStatus.ERROR:
            raise ValueError("timed_out scenario requires ERROR status")
        return {
            "execution_state": ExecutionState.TIMED_OUT,
            "exit_code": None,
            "error_kind": ErrorKind.TIMEOUT,
            "primary_message": "Scenario execution timed out.",
            "stdout_path": Path("raw/scenarios/scenario.stdout.log"),
            "stderr_path": Path("raw/scenarios/scenario.stderr.log"),
            "normalized_output_path": None,
        }
    if cancelled:
        if status is not ValidationStatus.ERROR:
            raise ValueError("cancelled scenario requires ERROR status")
        return {
            "execution_state": ExecutionState.CANCELLED,
            "exit_code": None,
            "error_kind": ErrorKind.TOOL,
            "primary_message": "Scenario execution was cancelled.",
            "stdout_path": Path("raw/scenarios/scenario.stdout.log"),
            "stderr_path": Path("raw/scenarios/scenario.stderr.log"),
            "normalized_output_path": None,
        }
    if status is ValidationStatus.OK:
        return {
            "execution_state": ExecutionState.COMPLETED,
            "exit_code": 0,
            "error_kind": ErrorKind.OK,
            "primary_message": "Scenario completed successfully.",
            "stdout_path": Path("raw/scenarios/scenario.stdout.log"),
            "stderr_path": Path("raw/scenarios/scenario.stderr.log"),
            "normalized_output_path": Path("raw/scenarios/scenario.normalized.txt"),
        }
    if status is ValidationStatus.FAIL:
        return {
            "execution_state": ExecutionState.COMPLETED,
            "exit_code": 1,
            "error_kind": ErrorKind.OTHER,
            "primary_message": "Scenario validation failed.",
            "stdout_path": Path("raw/scenarios/scenario.stdout.log"),
            "stderr_path": Path("raw/scenarios/scenario.stderr.log"),
            "normalized_output_path": Path("raw/scenarios/scenario.normalized.txt"),
        }
    if status is ValidationStatus.SKIPPED:
        return {
            "execution_state": None,
            "exit_code": None,
            "error_kind": ErrorKind.OK,
            "primary_message": "Scenario intentionally skipped.",
            "stdout_path": None,
            "stderr_path": None,
            "normalized_output_path": None,
        }
    return {
        "execution_state": ExecutionState.LAUNCH_FAILED,
        "exit_code": None,
        "error_kind": ErrorKind.TOOL,
        "primary_message": "Scenario execution could not be started.",
        "stdout_path": Path("raw/scenarios/scenario.stdout.log"),
        "stderr_path": Path("raw/scenarios/scenario.stderr.log"),
        "normalized_output_path": None,
    }


def _derive_overall_status(
    files: Sequence[FileResult],
    scenarios: Sequence[ScenarioResult],
) -> OverallStatus:
    statuses = [
        *(result.status for result in files),
        *(result.status for result in scenarios if result.required),
    ]
    if any(
        status in {ValidationStatus.ERROR, ValidationStatus.SKIPPED}
        for status in statuses
    ):
        return OverallStatus.ERROR
    if any(status is ValidationStatus.FAIL for status in statuses):
        return OverallStatus.FAIL
    return OverallStatus.OK


def _run_totals(
    files: Sequence[FileResult],
    scenarios: Sequence[ScenarioResult],
    *,
    files_seen: int | None,
    files_excluded: int,
    excluded_noise: int,
    overall_status: OverallStatus | None,
) -> RunTotals:
    file_statuses = Counter(result.status for result in files)
    scenario_statuses = Counter(result.status for result in scenarios)
    included = len(files)
    seen = included + files_excluded if files_seen is None else files_seen
    terminal = overall_status or _derive_overall_status(files, scenarios)
    return RunTotals(
        files_seen=seen,
        files_included=included,
        files_excluded=files_excluded,
        files_ok=file_statuses[ValidationStatus.OK],
        files_fail=file_statuses[ValidationStatus.FAIL],
        files_error=file_statuses[ValidationStatus.ERROR],
        files_skipped=file_statuses[ValidationStatus.SKIPPED],
        direct_fail=sum(
            result.status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
            and result.diagnostic_class is DiagnosticClass.DIRECT
            for result in files
        ),
        downstream_fail=sum(
            result.status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
            and result.diagnostic_class is DiagnosticClass.DOWNSTREAM
            for result in files
        ),
        ambiguous_fail=sum(
            result.status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
            and result.diagnostic_class is DiagnosticClass.AMBIGUOUS
            for result in files
        ),
        excluded_noise=excluded_noise,
        scenarios_seen=len(scenarios),
        scenarios_ok=scenario_statuses[ValidationStatus.OK],
        scenarios_fail=scenario_statuses[ValidationStatus.FAIL],
        scenarios_error=scenario_statuses[ValidationStatus.ERROR],
        scenarios_skipped=scenario_statuses[ValidationStatus.SKIPPED],
        required_scenario_fail=sum(
            result.required and result.status is ValidationStatus.FAIL
            for result in scenarios
        ),
        overall_status=terminal,
    )


def _diff_sort_key(entry: object) -> tuple[int, str, str, str, str]:
    order = {
        ChangeKind.REGRESSED: 0,
        ChangeKind.NEW: 1,
        ChangeKind.IMPROVED: 2,
        ChangeKind.REMOVED: 3,
        ChangeKind.UNCHANGED: 4,
    }
    kind = _enum(getattr(entry, "change_kind"), ChangeKind, field="change_kind")
    return (
        order[kind],
        str(getattr(entry, "subject_kind")),
        str(getattr(entry, "subject_id")),
        str(getattr(entry, "previous_status")),
        str(getattr(entry, "current_status")),
    )


def _top_error_sort_key(entry: object) -> tuple[int, str, str, str]:
    count = getattr(entry, "count")
    message = str(getattr(entry, "message"))
    kind = getattr(entry, "error_kind")
    kind_text = kind.value if isinstance(kind, ErrorKind) else str(kind)
    return (-int(count), kind_text, message.casefold(), message)
