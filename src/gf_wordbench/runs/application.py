"""Production application service for path-resolved Quick and Diagnostic runs.

The service consumes an already-resolved :class:`RunConfig`. It never
rediscovers language or RGL facts. Quick validates one explicit target;
Diagnostic can inventory every resolved GF source while continuing after
independent failures and preserving per-file evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
import time
from typing import Final, Protocol

from gf_wordbench.diagnostics.models import ArtifactObservation as DiagnosticArtifactObservation
from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticRecord,
)
from gf_wordbench.diagnostics.parsing.service import parse_diagnostics
from gf_wordbench.infrastructure.process.termination import CancellationToken
from gf_wordbench.kernel.errors import CancellationRequested, ConfigurationError
from gf_wordbench.kernel.events import EventLevel, ProgressEvent
from gf_wordbench.kernel.ids import validate_project_id
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    TargetKind,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.reporting.details.writer import write_global_scan_reports
from gf_wordbench.reporting.summary.markdown_writer import write_summary_md
from gf_wordbench.runs.identity import iter_run_id_candidates
from gf_wordbench.runs.paths import allocate_run_paths
from gf_wordbench.runs.public import RunConfig, RunResult
from gf_wordbench.runs.result_builder import build_file_result, build_run_result
from gf_wordbench.validation.compilation.gf_adapter import GfProcessAdapter
from gf_wordbench.validation.compilation.models import (
    CompileSummary,
    CompileTargetKind,
    SourceFingerprint,
)
from gf_wordbench.validation.compilation.version_probe import (
    GFVersionPolicy,
    GFVersionProbeOutcome,
    build_gf_version_probe_request,
    probe_gf_version,
    skipped_gf_version_result,
)
from gf_wordbench.validation.ports import (
    GfArtifactExpectation,
    GfArtifactKind,
    GfOperationRequest,
    ModuleCompilePayload,
)
from gf_wordbench.validation.scanning.models import ScanCounts
from gf_wordbench.validation.scanning.service import scan_text

__all__ = ("execute_diagnostic_run", "execute_quick_run", "run_validation")

_OUTPUT_LIMIT_BYTES: Final[int] = 16 * 1024 * 1024
_MAX_SCAN_LOG_CHARS: Final[int] = 512 * 1024


class _EventSink(Protocol):
    def __call__(self, event: object, /) -> None: ...


class _CancellationCheck(Protocol):
    def __call__(self) -> None: ...


@dataclass(frozen=True, slots=True)
class _CompileEvidence:
    summary: CompileSummary
    primary_record: DiagnosticRecord | None


@dataclass(frozen=True, slots=True)
class _DiagnosticWorkItem:
    source_path: Path
    relative: Path
    scan_counts: ScanCounts
    scan_log: Path
    fingerprint: SourceFingerprint
    compile_evidence: _CompileEvidence


class _CheckCancellationToken:
    """Adapt the worker's raising cancellation check to the process token port."""

    __slots__ = ("_check", "_cancelled")

    def __init__(self, check: _CancellationCheck) -> None:
        self._check = check
        self._cancelled = False

    def is_cancelled(self) -> bool:
        try:
            self._check()
        except CancellationRequested:
            self._cancelled = True
        return self._cancelled

    def reason(self) -> str | None:
        return "user" if self._cancelled else None


def execute_quick_run(
    run_config: RunConfig,
    event_sink: _EventSink,
    cancellation_check: _CancellationCheck,
    *,
    run_id: str | None = None,
) -> RunResult:
    """Execute one real Quick validation using the resolved GF environment."""

    if not isinstance(run_config, RunConfig):
        raise TypeError("run_config must be RunConfig")
    if not callable(event_sink):
        raise TypeError("event_sink must be callable")
    if not callable(cancellation_check):
        raise TypeError("cancellation_check must be callable")
    if run_config.mode is not ValidationMode.QUICK:
        raise ConfigurationError(
            "The path-resolved runtime currently executes Quick validation only.",
            code="GF-WB-CONFIG-907",
            stage="run",
            operation="quick-validation",
            subject=run_config.mode.value,
        )
    target = run_config.target
    if target is None or target.kind is not TargetKind.FILE or target.value is None:
        raise ConfigurationError(
            "Quick validation requires one explicit GF source file target.",
            code="GF-WB-CONFIG-908",
            stage="run",
            operation="quick-validation",
            subject="target",
        )

    context = run_config.language_context
    if context is None:
        raise ConfigurationError(
            "Quick validation requires a resolved language context.",
            code="GF-WB-CONFIG-909",
            stage="run",
            operation="quick-validation",
            subject="language_context",
        )

    source_root = context.language_directory.resolve(strict=True)
    source_path = (source_root / target.value).resolve(strict=True)
    try:
        source_path.relative_to(source_root)
    except ValueError as exc:
        raise ConfigurationError(
            "The Quick target escapes the resolved language directory.",
            code="GF-WB-PATH-270",
            stage="run",
            operation="quick-validation",
            subject=str(source_path),
        ) from exc
    if source_path.suffix.casefold() != ".gf" or not source_path.is_file():
        raise ConfigurationError(
            "The Quick target must be an existing .gf source file.",
            code="GF-WB-PATH-271",
            stage="run",
            operation="quick-validation",
            subject=str(source_path),
        )

    cancellation_check()
    started_at = datetime.now(UTC)
    started_clock = time.monotonic()
    output_root = run_config.environment.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    run_paths = _allocate_paths(output_root, started_at, requested_run_id=run_id)
    run_id = str(run_paths.run_id)
    token: CancellationToken = _CheckCancellationToken(cancellation_check)

    _progress(
        event_sink,
        run_id=run_id,
        message="Quick validation started",
        stage="prepare",
        subject=target.value,
        completed=0,
        total=3,
    )

    gf_version = _probe_version(
        run_config,
        run_paths=run_paths,
        run_id=run_id,
        token=token,
        event_sink=event_sink,
    )
    cancellation_check()

    _progress(
        event_sink,
        run_id=run_id,
        message="Static scan",
        stage="scan",
        subject=target.value,
        completed=1,
        total=3,
    )
    source_text = source_path.read_text(encoding="utf-8")
    relative = source_path.relative_to(source_root)
    scan_counts, scan_findings, scan_diagnostics = scan_text(
        source_text,
        project_relative_path=relative.as_posix(),
    )
    scan_log = run_paths.raw_scan_dir / f"{_safe_stem(relative)}.scan.txt"
    _write_scan_log(
        scan_log,
        source_path=source_path,
        counts=scan_counts,
        findings=scan_findings,
        diagnostics=scan_diagnostics,
    )
    cancellation_check()

    _progress(
        event_sink,
        run_id=run_id,
        message="GF compilation",
        stage="compile",
        subject=target.value,
        completed=2,
        total=3,
    )
    compile_summary = _compile_target(
        run_config,
        source_path=source_path,
        relative=relative,
        run_paths=run_paths,
        run_id=run_id,
        gf_version=gf_version,
        token=token,
    )
    cancellation_check()

    status = compile_summary.status
    diagnostic_class = (
        DiagnosticClass.OK
        if status is ValidationStatus.OK
        else DiagnosticClass.DIRECT
    )
    fingerprint = _fingerprint(source_path)
    file_result = build_file_result(
        file_path=source_path,
        module_name=source_path.stem,
        status=status,
        diagnostic_class=diagnostic_class,
        scan_counts=scan_counts,
        fingerprint=fingerprint,
        compile_summary=compile_summary,
        scan_log_path=scan_log,
        artifacts=compile_summary.produced_artifacts,
    )

    finished_at = datetime.now(UTC)
    duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
    result = build_run_result(
        run_config=run_config,
        run_paths=run_paths,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        gf_version=gf_version,
        file_results=(file_result,),
    )

    # The Markdown writer already supports the canonical RunPaths model and is
    # useful immediately. JSON/AI packet publication remains a later full-run
    # finalization concern rather than being reimplemented here.
    try:
        write_summary_md(result)
    except Exception as exc:  # reporting must not erase successful raw evidence
        _progress(
            event_sink,
            run_id=run_id,
            message=f"Summary report was not written: {type(exc).__name__}: {exc}",
            severity=EventLevel.WARN,
            stage="report",
            subject=target.value,
            completed=3,
            total=3,
        )
    else:
        _progress(
            event_sink,
            run_id=run_id,
            message="Quick validation completed",
            stage="complete",
            subject=target.value,
            completed=3,
            total=3,
        )
    return result



def execute_diagnostic_run(
    run_config: RunConfig,
    event_sink: _EventSink,
    cancellation_check: _CancellationCheck,
    *,
    run_id: str | None = None,
) -> RunResult:
    """Inventory one or all resolved GF sources without fail-fast behavior."""

    if not isinstance(run_config, RunConfig):
        raise TypeError("run_config must be RunConfig")
    if run_config.mode is not ValidationMode.DIAGNOSTIC:
        raise ConfigurationError(
            "Diagnostic inventory requires mode=diagnostic.",
            code="GF-WB-CONFIG-916",
            stage="run",
            operation="diagnostic-validation",
            subject=run_config.mode.value,
        )
    context = run_config.language_context
    if context is None:
        raise ConfigurationError(
            "Diagnostic inventory requires a resolved language context.",
            code="GF-WB-CONFIG-917",
            stage="run",
            operation="diagnostic-validation",
            subject="language_context",
        )

    source_root = context.language_directory.resolve(strict=True)
    inventory = tuple(
        sorted(
            (path.resolve(strict=True) for path in context.source_inventory),
            key=str,
        )
    )
    selected = _diagnostic_sources(run_config, inventory=inventory, source_root=source_root)
    is_global = run_config.target is None or run_config.target.kind is TargetKind.PROJECT
    files_seen = len(selected)
    if run_config.max_files > 0:
        selected = selected[: run_config.max_files]
    files_excluded = files_seen - len(selected)
    if not selected:
        raise ConfigurationError(
            "Diagnostic inventory has no GF source files to validate.",
            code="GF-WB-CONFIG-918",
            stage="selection",
            operation="diagnostic-validation",
            subject=str(source_root),
        )

    cancellation_check()
    started_at = datetime.now(UTC)
    started_clock = time.monotonic()
    output_root = run_config.environment.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    run_paths = _allocate_paths(output_root, started_at, requested_run_id=run_id)
    resolved_run_id = str(run_paths.run_id)
    token: CancellationToken = _CheckCancellationToken(cancellation_check)
    total_steps = 2 + (2 * len(selected))

    _progress(
        event_sink,
        run_id=resolved_run_id,
        message=f"Diagnostic {'global scan' if is_global else 'validation'} started ({len(selected)} files)",
        stage="prepare",
        subject=(
            "all GF sources" if is_global else str(run_config.target.value)
        ),
        completed=0,
        total=total_steps,
    )
    gf_version = _probe_version(
        run_config,
        run_paths=run_paths,
        run_id=resolved_run_id,
        token=token,
        event_sink=event_sink,
        progress_total=total_steps,
    )
    work_items: list[_DiagnosticWorkItem] = []
    completed = 1

    for source_path in selected:
        cancellation_check()
        relative = source_path.relative_to(source_root)
        _progress(
            event_sink,
            run_id=resolved_run_id,
            message="Static scan",
            stage="scan",
            subject=relative.as_posix(),
            completed=completed,
            total=total_steps,
        )
        source_text = source_path.read_text(encoding="utf-8")
        scan_counts, scan_findings, scan_diagnostics = scan_text(
            source_text,
            project_relative_path=relative.as_posix(),
        )
        scan_log = run_paths.raw_scan_dir / f"{_safe_stem(relative)}.scan.txt"
        _write_scan_log(
            scan_log,
            source_path=source_path,
            counts=scan_counts,
            findings=scan_findings,
            diagnostics=scan_diagnostics,
        )
        completed += 1
        cancellation_check()

        if run_config.no_compile:
            compile_evidence = _CompileEvidence(
                summary=_skipped_compile_summary(
                    source_path=source_path,
                    relative=relative,
                    working_directory=source_root,
                    reason="Diagnostic scan-only run",
                ),
                primary_record=None,
            )
        else:
            _progress(
                event_sink,
                run_id=resolved_run_id,
                message="GF compilation",
                stage="compile",
                subject=relative.as_posix(),
                completed=completed,
                total=total_steps,
            )
            module_output = run_paths.gfo_dir / _safe_stem(relative)
            try:
                compile_evidence = _compile_target_evidence(
                    run_config,
                    source_path=source_path,
                    relative=relative,
                    run_paths=run_paths,
                    run_id=resolved_run_id,
                    gf_version=gf_version,
                    token=token,
                    output_directory=module_output,
                )
            except CancellationRequested:
                raise
            except Exception as exc:
                compile_evidence = _compile_exception_evidence(
                    source_path=source_path,
                    relative=relative,
                    run_paths=run_paths,
                    working_directory=source_root,
                    output_directory=module_output,
                    error=exc,
                )
                _progress(
                    event_sink,
                    run_id=resolved_run_id,
                    message=(
                        "Compilation raised an internal file-level exception; "
                        "continuing Global Scan"
                    ),
                    severity=EventLevel.WARN,
                    stage="compile",
                    subject=relative.as_posix(),
                    completed=completed,
                    total=total_steps,
                )
        completed += 1
        work_items.append(
            _DiagnosticWorkItem(
                source_path=source_path,
                relative=relative,
                scan_counts=scan_counts,
                scan_log=scan_log,
                fingerprint=_fingerprint(source_path),
                compile_evidence=compile_evidence,
            )
        )

    file_results = _diagnostic_file_results(work_items)
    finished_at = datetime.now(UTC)
    duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
    result = build_run_result(
        run_config=run_config,
        run_paths=run_paths,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        gf_version=gf_version,
        file_results=file_results,
        files_seen=files_seen,
        files_excluded=files_excluded,
    )

    report_errors: list[str] = []
    for writer in (write_summary_md, write_global_scan_reports):
        try:
            writer(result)
        except Exception as exc:
            report_errors.append(f"{getattr(writer, '__name__', type(writer).__name__)}: {exc}")
    if report_errors:
        _progress(
            event_sink,
            run_id=resolved_run_id,
            message="Some diagnostic reports were not written: " + " | ".join(report_errors),
            severity=EventLevel.WARN,
            stage="report",
            subject="diagnostic inventory",
            completed=total_steps,
            total=total_steps,
        )
    else:
        _progress(
            event_sink,
            run_id=resolved_run_id,
            message="Diagnostic global scan completed" if is_global else "Diagnostic validation completed",
            stage="complete",
            subject="diagnostic inventory",
            completed=total_steps,
            total=total_steps,
        )
    return result


def _diagnostic_sources(
    run_config: RunConfig,
    *,
    inventory: tuple[Path, ...],
    source_root: Path,
) -> tuple[Path, ...]:
    target = run_config.target
    if target is None or target.kind is TargetKind.PROJECT:
        return inventory
    if target.kind not in {TargetKind.FILE, TargetKind.MODULE}:
        raise ConfigurationError(
            "Path-resolved Diagnostic supports project, file, or module source scope.",
            code="GF-WB-CONFIG-919",
            stage="selection",
            operation="diagnostic-validation",
            subject=target.kind.value,
        )
    assert target.value is not None
    value = target.value
    by_relative = {path.relative_to(source_root).as_posix(): path for path in inventory}
    by_module = {path.stem: path for path in inventory}
    selected = by_relative.get(value) or by_module.get(value) or by_module.get(Path(value).stem)
    if selected is None:
        raise ConfigurationError(
            "Diagnostic target is not present in the resolved source inventory.",
            code="GF-WB-PATH-272",
            stage="selection",
            operation="diagnostic-validation",
            subject=value,
        )
    return (selected,)


def _diagnostic_file_results(items: list[_DiagnosticWorkItem]):
    failed_modules = {
        item.source_path.stem
        for item in items
        if item.compile_evidence.summary.status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
    }
    results = []
    for item in items:
        summary = item.compile_evidence.summary
        diagnostic_class, blocked_by = _classify_diagnostic_item(
            item,
            failed_modules=failed_modules,
        )
        results.append(
            build_file_result(
                file_path=item.source_path,
                module_name=item.source_path.stem,
                status=summary.status,
                diagnostic_class=diagnostic_class,
                blocked_by=blocked_by,
                scan_counts=item.scan_counts,
                fingerprint=item.fingerprint,
                compile_summary=summary,
                scan_log_path=item.scan_log,
                artifacts=summary.produced_artifacts,
            )
        )
    return tuple(results)


def _classify_diagnostic_item(
    item: _DiagnosticWorkItem,
    *,
    failed_modules: set[str],
) -> tuple[DiagnosticClass, tuple[str, ...]]:
    summary = item.compile_evidence.summary
    if summary.status is ValidationStatus.OK:
        return DiagnosticClass.OK, ()
    if summary.status is ValidationStatus.SKIPPED:
        return DiagnosticClass.SKIPPED, ()
    if summary.error_kind in {ErrorKind.TIMEOUT, ErrorKind.TOOL, ErrorKind.IO, ErrorKind.INTERNAL}:
        return DiagnosticClass.DIRECT, ()

    target_module = item.source_path.stem
    record = item.compile_evidence.primary_record
    if record is not None:
        if record.source_module == target_module:
            return DiagnosticClass.DIRECT, ()
        if record.source_path is not None and record.source_path.stem == target_module:
            return DiagnosticClass.DIRECT, ()
        candidates = {reference for reference in record.references if reference in failed_modules}
        if record.source_module in failed_modules:
            candidates.add(record.source_module)
        if record.source_path is not None and record.source_path.stem in failed_modules:
            candidates.add(record.source_path.stem)
        candidates.discard(target_module)
        if candidates:
            return DiagnosticClass.DOWNSTREAM, tuple(sorted(candidates))

    text = f"{summary.first_error}\n{summary.error_detail}"
    candidates = tuple(
        sorted(
            module
            for module in failed_modules
            if module != target_module and module in text
        )
    )
    if candidates:
        return DiagnosticClass.DOWNSTREAM, candidates
    return DiagnosticClass.AMBIGUOUS, ()


def _skipped_compile_summary(
    *,
    source_path: Path,
    relative: Path,
    working_directory: Path,
    reason: str,
) -> CompileSummary:
    return CompileSummary(
        target_id=relative.as_posix(),
        target_kind=CompileTargetKind.SOURCE,
        status=ValidationStatus.SKIPPED,
        command=(),
        working_directory=working_directory,
        exit_code=None,
        launched=False,
        timed_out=False,
        cancelled=False,
        duration_ms=0,
        error_kind=ErrorKind.OTHER,
        first_error=reason,
        error_detail="",
        stdout_path=None,
        stderr_path=None,
        expected_artifacts=(),
        produced_artifacts=(),
        artifact_checks_passed=False,
        skipped_reason=reason,
    )


def _compile_exception_evidence(
    *,
    source_path: Path,
    relative: Path,
    run_paths,
    working_directory: Path,
    output_directory: Path,
    error: Exception,
) -> _CompileEvidence:
    """Preserve a file-level framework exception without aborting the inventory."""

    key = _safe_stem(relative)
    stdout_path = run_paths.raw_compile_dir / f"{key}.out.txt"
    stderr_path = run_paths.raw_compile_dir / f"{key}.err.txt"
    if not stdout_path.exists():
        stdout_path.write_text("", encoding="utf-8", newline="\n")
    existing = _read_text(stderr_path).rstrip()
    message = f"{type(error).__name__}: {error}"
    detail = "GF Wordbench file-level compile exception: " + message
    stderr_text = f"{existing}\n{detail}\n" if existing else f"{detail}\n"
    stderr_path.write_text(stderr_text, encoding="utf-8", newline="\n")

    output_directory.mkdir(parents=True, exist_ok=True)
    expected_object = output_directory / f"{source_path.stem}.gfo"
    produced = (expected_object,) if expected_object.is_file() else ()
    error_kind = ErrorKind.IO if isinstance(error, OSError) else ErrorKind.INTERNAL
    summary = CompileSummary(
        target_id=relative.as_posix(),
        target_kind=CompileTargetKind.SOURCE,
        status=ValidationStatus.ERROR,
        command=(),
        working_directory=working_directory,
        exit_code=None,
        launched=False,
        timed_out=False,
        cancelled=False,
        duration_ms=0,
        error_kind=error_kind,
        first_error=detail,
        error_detail=message,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        expected_artifacts=(expected_object,),
        produced_artifacts=produced,
        artifact_checks_passed=False,
    )
    return _CompileEvidence(summary=summary, primary_record=None)


def run_validation(
    request: object,
    *,
    cancellation_check: _CancellationCheck | None = None,
    event_sink: _EventSink | None = None,
) -> RunResult:
    """Canonical application-provider name used by bootstrap discovery.

    The first executable ADR-0015 slice consumes a resolved ``RunConfig``.
    CLI request-to-RunConfig translation remains bootstrap-owned; callers must
    not bypass that resolution boundary by passing ad-hoc dictionaries here.
    """

    if not isinstance(request, RunConfig):
        raise ConfigurationError(
            "The validation application requires a resolved RunConfig.",
            code="GF-WB-CONFIG-914",
            stage="run",
            operation="run-validation",
            subject=type(request).__name__,
        )
    sink = event_sink or (lambda _event: None)
    check = cancellation_check or (lambda: None)
    if request.mode is ValidationMode.QUICK:
        return execute_quick_run(request, sink, check)
    if request.mode is ValidationMode.DIAGNOSTIC:
        return execute_diagnostic_run(request, sink, check)
    raise ConfigurationError(
        "The path-resolved runtime executes Quick and Diagnostic validation.",
        code="GF-WB-CONFIG-915",
        stage="run",
        operation="run-validation",
        subject=request.mode.value,
    )


def _allocate_paths(
    output_root: Path,
    timestamp: datetime,
    *,
    requested_run_id: str | None = None,
):
    if requested_run_id is not None:
        return allocate_run_paths(output_root, requested_run_id)
    for run_id in iter_run_id_candidates(timestamp):
        if (output_root / f"run_{run_id}").exists():
            continue
        try:
            return allocate_run_paths(output_root, run_id)
        except FileExistsError:
            continue
    raise RuntimeError("unable to allocate a unique run directory")


def _probe_version(
    run_config: RunConfig,
    *,
    run_paths,
    run_id: str,
    token: CancellationToken,
    event_sink: _EventSink,
    progress_total: int = 3,
) -> str:
    executable = run_config.environment.gf_executable
    if run_config.skip_version_probe:
        result = skipped_gf_version_result(
            executable=executable,
            reason="GF version probing was skipped by the selected validation profile.",
        )
        return result.normalized_version or "UNKNOWN"

    stdout_path = run_paths.raw_compile_dir / "gf_version.out.txt"
    stderr_path = run_paths.raw_compile_dir / "gf_version.err.txt"
    request = build_gf_version_probe_request(
        executable=executable,
        working_directory=run_config.source_root,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=min(10.0, float(run_config.timeout_sec)),
        approved_read_roots=(
            run_config.source_root,
            run_config.environment.rgl_root,
            *run_config.environment.gf_path,
        ),
        approved_write_roots=(run_paths.run_dir,),
        request_id=f"{run_id}-gf-version",
        operation_id="version",
        output_limit_bytes=256 * 1024,
    )
    result = probe_gf_version(
        request,
        policy=GFVersionPolicy(allow_untested_versions=True, strict_unknown=True),
        cancellation_token=token,
    )
    if result.outcome is not GFVersionProbeOutcome.RECOGNIZED or not result.accepted:
        raise ConfigurationError(
            "GF version verification failed.",
            code="GF-WB-TOOL-910",
            detail=result.message,
            stage="version_probe",
            operation="gf-version",
            subject=str(executable),
            evidence_paths=(str(stdout_path), str(stderr_path)),
        )
    version = result.normalized_version or result.raw_version_text.strip()
    _progress(
        event_sink,
        run_id=run_id,
        message=f"GF {version} verified",
        stage="version_probe",
        subject=str(executable),
        completed=1,
        total=progress_total,
    )
    return version


def _compile_target(
    run_config: RunConfig,
    *,
    source_path: Path,
    relative: Path,
    run_paths,
    run_id: str,
    gf_version: str,
    token: CancellationToken,
    output_directory: Path | None = None,
) -> CompileSummary:
    return _compile_target_evidence(
        run_config,
        source_path=source_path,
        relative=relative,
        run_paths=run_paths,
        run_id=run_id,
        gf_version=gf_version,
        token=token,
        output_directory=output_directory,
    ).summary


def _compile_target_evidence(
    run_config: RunConfig,
    *,
    source_path: Path,
    relative: Path,
    run_paths,
    run_id: str,
    gf_version: str,
    token: CancellationToken,
    output_directory: Path | None = None,
) -> _CompileEvidence:
    module_name = source_path.stem
    key = _safe_stem(relative)
    stdout_path = run_paths.raw_compile_dir / f"{key}.out.txt"
    stderr_path = run_paths.raw_compile_dir / f"{key}.err.txt"
    artifact_root = output_directory or run_paths.gfo_dir
    artifact_root.mkdir(parents=True, exist_ok=True)
    expected_object = artifact_root / f"{module_name}.gfo"
    request = GfOperationRequest(
        operation_id=f"compile-{key}",
        project_id=validate_project_id(run_config.language_key),
        run_id=run_paths.run_id,
        executable=run_config.environment.gf_executable,
        working_directory=run_config.source_root,
        gf_path=run_config.environment.gf_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=float(run_config.timeout_sec),
        output_limit_bytes=_OUTPUT_LIMIT_BYTES,
        payload=ModuleCompilePayload(
            source_path=source_path,
            module_name=module_name,
            output_directory=artifact_root,
            expected_object_path=expected_object,
        ),
        expected_artifacts=(
            GfArtifactExpectation(
                path=expected_object,
                role="gfo",
                kind=GfArtifactKind.FILE,
                required=True,
                require_non_empty=True,
            ),
        ),
    )
    operation = GfProcessAdapter().compile_module(
        request,
        cancellation_token=token,
    )
    process = operation.process
    stdout_text = _read_text(stdout_path)
    stderr_text = _read_text(stderr_path)
    parse = parse_diagnostics(
        DiagnosticEvidence(
            operation_kind="compile",
            execution_state=process.execution_state,
            exit_code=process.exit_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            artifact_observations=tuple(
                DiagnosticArtifactObservation(
                    path=item.path,
                    role=item.role,
                    required=item.required,
                    exists=item.exists,
                    kind_matches=item.kind_matches,
                    size_bytes=item.size_bytes,
                )
                for item in getattr(process, "artifact_observations", ())
            ),
            gf_version=gf_version,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            stdout_truncated=bool(getattr(process, "output_limit_exceeded", False)),
            stderr_truncated=bool(getattr(process, "output_limit_exceeded", False)),
            capture_complete=bool(getattr(process, "capture_complete", True)),
        )
    )

    produced = (expected_object,) if expected_object.is_file() else ()
    artifacts_ok = bool(produced and expected_object.stat().st_size > 0)
    state = process.execution_state
    exit_code = process.exit_code
    if state is ExecutionState.COMPLETED and exit_code == 0 and artifacts_ok:
        status = ValidationStatus.OK
        error_kind = ErrorKind.OK
        first_error = ""
        error_detail = ""
    elif state is ExecutionState.COMPLETED:
        status = ValidationStatus.FAIL if exit_code not in (None, 0) else ValidationStatus.ERROR
        error_kind = parse.primary_error_kind or (
            ErrorKind.IO if exit_code == 0 else ErrorKind.OTHER
        )
        first_error = parse.primary_message or _first_message(stderr_text, stdout_text) or (
            "GF completed without the required GFO artifact"
        )
        error_detail = parse.primary_detail
    elif state is ExecutionState.TIMED_OUT:
        status = ValidationStatus.ERROR
        error_kind = ErrorKind.TIMEOUT
        first_error = "GF compilation timed out"
        error_detail = ""
    elif state is ExecutionState.LAUNCH_FAILED:
        status = ValidationStatus.ERROR
        error_kind = ErrorKind.TOOL
        first_error = "GF could not be launched"
        error_detail = str(getattr(process, "launch_error_message", ""))
    elif state is ExecutionState.CANCELLED:
        raise CancellationRequested("GF compilation cancelled", detail="reason=user")
    else:
        status = ValidationStatus.ERROR
        error_kind = ErrorKind.INTERNAL
        first_error = "GF compilation ended in an unknown execution state"
        error_detail = str(state)

    summary = CompileSummary(
        target_id=relative.as_posix(),
        target_kind=CompileTargetKind.SOURCE,
        status=status,
        command=tuple(process.command),
        working_directory=process.cwd,
        exit_code=exit_code,
        launched=state is not ExecutionState.LAUNCH_FAILED,
        timed_out=state is ExecutionState.TIMED_OUT,
        cancelled=state is ExecutionState.CANCELLED,
        duration_ms=process.duration_ms,
        error_kind=error_kind,
        first_error=first_error,
        error_detail=error_detail,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        expected_artifacts=(expected_object,),
        produced_artifacts=produced,
        artifact_checks_passed=artifacts_ok,
    )
    primary_record = next(
        (record for record in parse.records if record.record_id == parse.primary_record_id),
        None,
    )
    return _CompileEvidence(summary=summary, primary_record=primary_record)


def _fingerprint(path: Path) -> SourceFingerprint:
    data = path.read_bytes()
    stat = path.stat()
    return SourceFingerprint(
        size_bytes=len(data),
        hash_algorithm="sha256",
        hash=hashlib.sha256(data).hexdigest(),
        last_modified_utc=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
    )


def _write_scan_log(path: Path, *, source_path: Path, counts, findings, diagnostics) -> None:
    lines = [
        "GF Wordbench Static Scan",
        f"source_path: {source_path}",
        "",
        "Counts",
        *(f"{name}: {value}" for name, value in counts.as_tuple()),
        "",
        "Findings",
    ]
    if findings:
        for finding in findings:
            lines.append(
                f"{finding.rule_id} line {finding.start_line}: {finding.message}"
            )
    else:
        lines.append("none")
    lines.extend(("", "Diagnostics"))
    if diagnostics:
        for diagnostic in diagnostics:
            lines.append(f"{diagnostic.code}: {diagnostic.message}")
    else:
        lines.append("none")
    text = "\n".join(lines) + "\n"
    path.write_text(text[:_MAX_SCAN_LOG_CHARS], encoding="utf-8")


def _safe_stem(relative: Path) -> str:
    text = "_".join(relative.with_suffix("").parts)
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in text)


def _first_message(*streams: str) -> str:
    for stream in streams:
        for line in stream.splitlines():
            text = line.strip()
            if text and not text.casefold().startswith(("- compiling", "linking", "writing")):
                return text[:4000]
    return ""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _progress(
    sink: _EventSink,
    *,
    run_id: str,
    message: str,
    stage: str,
    subject: str,
    completed: int,
    total: int,
    severity: EventLevel = EventLevel.INFO,
) -> None:
    sink(
        ProgressEvent(
            timestamp=datetime.now(UTC),
            message=message,
            severity=severity,
            run_id=run_id,
            stage=stage,
            subject=subject,
            completed=completed,
            total=total,
        )
    )
