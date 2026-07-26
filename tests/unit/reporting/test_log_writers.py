"""Unit tests for GF Wordbench log writers and log-support contracts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest

from gf_wordbench.kernel.errors import ContractViolationError, ReportError
from gf_wordbench.kernel.events import EventLevel, LifecycleEvent, event_fields
from gf_wordbench.reporting.logs.aggregates import (
    ALL_LOGS_RELATIVE_PATH,
    ALL_SCAN_LOGS_RELATIVE_PATH,
    AggregateKind,
    AggregateLogSource,
    AggregateRunMetadata,
    AggregateSourceCategory,
    AggregateStream,
    render_all_logs,
    render_all_scan_logs as render_scan_sources,
    write_all_logs,
    write_all_scan_logs as write_scan_sources,
)
from gf_wordbench.reporting.logs.lifecycle import (
    LifecycleLogPolicy,
    LifecycleLogWriter,
    MASTER_LOG_ENCODING,
    MASTER_LOG_NEWLINE,
    MASTER_LOG_RELATIVE_PATH,
    REDACTED_VALUE,
    append_lifecycle_event,
    create_lifecycle_log,
    format_lifecycle_event,
)
from gf_wordbench.reporting.logs.process_streams import (
    ProcessStreamName,
    ProcessStreamState,
    ProcessStreamWriter,
    StreamPaths,
    inspect_process_stream,
    inspect_process_streams,
    stream_paths_from_capture,
    validate_stream_paths,
    write_process_streams,
)
from gf_wordbench.reporting.logs.redaction import (
    ConfiguredRedactionRule,
    LogRedactionPolicy,
    RedactionReason,
    RedactionRuleMode,
    contains_redaction_marker,
    parse_redaction_markers,
    redact_log_text,
)
from gf_wordbench.reporting.logs.scan_logs import (
    ScanLogAggregateStatus,
    ScanLogSection,
    build_scan_log_sections,
    render_all_scan_logs,
    write_all_scan_logs_result,
)
from gf_wordbench.reporting.logs.subject_keys import (
    allocate_subject_keys,
    is_subject_key,
    make_subject_key,
    normalize_subject_identity,
    validate_subject_key,
)
from gf_wordbench.reporting.logs.truncation import (
    RetentionStrategy,
    TruncationReason,
    append_truncation_marker,
    excerpt_around_line,
    truncate_bytes,
    truncate_lines,
    truncate_text,
)


_GENERATED_AT = datetime(2026, 7, 25, 12, 34, 56, 789000, tzinfo=UTC)
_SECTION_RULE = "=" * 80


@dataclass(slots=True)
class _Capture:
    stdout_path: Path
    stderr_path: Path
    stdout_size_bytes: int
    stderr_size_bytes: int



def _event(
    *,
    name: str = "stage_completed",
    level: EventLevel = EventLevel.INFO,
    message: str = "",
    fields: dict[str, object] | None = None,
) -> LifecycleEvent:
    return LifecycleEvent(
        timestamp=datetime(
            2026,
            7,
            25,
            8,
            34,
            56,
            789999,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        event=name,
        level=level,
        run_id="20260725_123456",
        stage="VAL-120",
        operation="compile",
        subject="lib/src/french/GrammaireÉté.gf",
        status="OK",
        message=message,
        evidence_path="raw/compile/grammaire-ete.err.txt",
        fields=event_fields(fields or {}),
    )



def _metadata(*, mode: str | None = "diagnostic") -> AggregateRunMetadata:
    return AggregateRunMetadata(
        run_id="run-20260725-123456",
        project_id="francais-demo",
        generated_at=_GENERATED_AT,
        mode=mode,
    )



def _write(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path



def _source(
    run_root: Path,
    relative_path: str,
    *,
    subject: str,
    role: str,
    category: AggregateSourceCategory,
    sequence: int,
    stream: AggregateStream = AggregateStream.NONE,
    status: str = "OK",
) -> AggregateLogSource:
    relative = PurePosixPath(relative_path)
    return AggregateLogSource(
        subject=subject,
        role=role,
        category=category,
        sequence=sequence,
        relative_path=relative,
        source_path=run_root / Path(relative.as_posix()),
        stream=stream,
        status=status,
    )



def test_lifecycle_format_is_utf8_lf_utc_and_deterministic() -> None:
    line = format_lifecycle_event(
        _event(
            message="compilation terminée avec succès",
            fields={
                "note": "valeur avec espaces",
                "duration_ms": 17,
                "cached": False,
            },
        )
    )

    assert line == (
        "2026-07-25T12:34:56.789Z INFO stage_completed "
        "run_id=20260725_123456 stage=VAL-120 operation=compile "
        "subject=lib/src/french/GrammaireÉté.gf status=OK "
        "evidence_path=raw/compile/grammaire-ete.err.txt "
        'message="compilation terminée avec succès" cached=false '
        "duration_ms=17 note=\"valeur avec espaces\"\n"
    )
    assert line.encode(MASTER_LOG_ENCODING).decode("utf-8") == line
    assert line.endswith(MASTER_LOG_NEWLINE)
    assert "\r" not in line



def test_lifecycle_format_redacts_sensitive_fields_and_custom_values() -> None:
    event = _event(
        fields={
            "api_key": "top-secret",
            "workspace": "C:/Users/Alice/private/project",
        }
    )

    line = format_lifecycle_event(
        event,
        redactor=lambda key, value: (
            "<HOME>" if key == "workspace" else value
        ),
    )

    assert f'api_key="{REDACTED_VALUE}"' in line
    assert "top-secret" not in line
    assert "workspace=<HOME>" in line
    assert "Alice" not in line



def test_lifecycle_line_limit_is_measured_after_utf8_encoding() -> None:
    event = _event(message="é" * 20)

    with pytest.raises(ValueError, match="line limit"):
        format_lifecycle_event(event, maximum_line_bytes=64)



def test_lifecycle_writer_suppresses_debug_and_finalizes_once(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    writer = LifecycleLogWriter(
        run_root,
        policy=LifecycleLogPolicy(emit_debug=False, sync_every_event=False),
    )

    suppressed = writer.append(_event(name="trace", level=EventLevel.DEBUG))
    emitted = writer.append(_event(name="run_completed"), synchronize=False)

    assert suppressed.emitted is False
    assert suppressed.bytes_written == 0
    assert emitted.emitted is True
    assert emitted.synchronized is False
    assert writer.path == run_root / MASTER_LOG_RELATIVE_PATH

    first = writer.finalize()
    second = writer.finalize()

    assert first == second
    assert writer.finalized is True
    payload = first.read_bytes()
    assert payload.startswith(b"2026-07-25T12:34:56.789Z INFO run_completed")
    assert payload.endswith(b"\n")
    assert not payload.endswith(b"\n\n")

    with pytest.raises(RuntimeError, match="finalized"):
        writer.append(_event())



def test_lifecycle_create_and_append_preserve_existing_content(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    path = create_lifecycle_log(run_root)
    path.write_text("existing\r\n\r\n", encoding="utf-8", newline="")

    receipt = append_lifecycle_event(
        path,
        _event(name="warning", level=EventLevel.WARN),
        run_root=run_root,
    )

    assert receipt.emitted is True
    assert path.read_text(encoding="utf-8").startswith("existing\n\n")
    assert " WARN warning " in path.read_text(encoding="utf-8")

    writer = LifecycleLogWriter(run_root, path=path, initialize=False)
    writer.finalize()
    assert path.read_bytes().endswith(b"\n")
    assert not path.read_bytes().endswith(b"\n\n")



def test_lifecycle_writer_rejects_destination_outside_run_root(
    tmp_path: Path,
) -> None:
    run_root = (tmp_path / "run").resolve()
    run_root.mkdir()

    with pytest.raises(OSError, match="escapes"):
        LifecycleLogWriter(run_root, path=(tmp_path / "outside.log").resolve())



def test_process_stream_inspection_distinguishes_present_empty_and_missing(
    tmp_path: Path,
) -> None:
    stdout = _write((tmp_path / "stdout.txt").resolve(), "été\n".encode())
    stderr = _write((tmp_path / "stderr.txt").resolve(), b"")
    missing = (tmp_path / "missing.txt").resolve()

    stdout_artifact = inspect_process_stream(ProcessStreamName.STDOUT, stdout)
    stderr_artifact = inspect_process_stream("stderr", stderr)
    missing_artifact = inspect_process_stream("stderr", missing)

    assert stdout_artifact.state is ProcessStreamState.PRESENT
    assert stdout_artifact.size_bytes == len("été\n".encode())
    assert stdout_artifact.sha256 == hashlib.sha256(stdout.read_bytes()).hexdigest()
    assert stderr_artifact.state is ProcessStreamState.EMPTY
    assert stderr_artifact.size_bytes == 0
    assert missing_artifact.state is ProcessStreamState.MISSING
    assert missing_artifact.size_bytes is None
    assert missing_artifact.sha256 is None



def test_process_stream_writer_copies_exact_bytes_and_preserves_empty_stream(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    source_paths = StreamPaths(
        _write(run_root / "capture" / "stdout.tmp", "café\r\n".encode()),
        _write(run_root / "capture" / "stderr.tmp", b""),
    )
    destinations = StreamPaths(
        run_root / "raw" / "compile" / "module.out.txt",
        run_root / "raw" / "compile" / "module.err.txt",
    )
    capture = _Capture(
        stdout_path=source_paths.stdout,
        stderr_path=source_paths.stderr,
        stdout_size_bytes=source_paths.stdout.stat().st_size,
        stderr_size_bytes=0,
    )

    result = write_process_streams(
        capture,
        destinations,
        run_root=run_root,
        sync=False,
    )

    assert result.copied is True
    assert result.complete is True
    assert result.total_size_bytes == source_paths.stdout.stat().st_size
    assert destinations.stdout.read_bytes() == source_paths.stdout.read_bytes()
    assert destinations.stderr.read_bytes() == b""
    assert result.stdout.state is ProcessStreamState.PRESENT
    assert result.stderr.state is ProcessStreamState.EMPTY



def test_process_stream_writer_detects_declared_size_mismatch(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    stdout = _write(run_root / "raw" / "stdout.txt", b"abc")
    stderr = _write(run_root / "raw" / "stderr.txt", b"")
    capture = _Capture(stdout, stderr, stdout_size_bytes=999, stderr_size_bytes=0)

    with pytest.raises(ReportError, match="size mismatch"):
        ProcessStreamWriter(run_root, sync=False).inspect(capture)



def test_process_stream_contract_rejects_aliasing_missing_and_escape(
    tmp_path: Path,
) -> None:
    run_root = (tmp_path / "run").resolve()
    run_root.mkdir()
    same = (run_root / "same.txt").resolve()

    with pytest.raises(ContractViolationError, match="distinct"):
        StreamPaths(same, same)

    missing_paths = StreamPaths(
        run_root / "stdout.txt",
        run_root / "stderr.txt",
    )
    with pytest.raises(ReportError, match="missing"):
        inspect_process_streams(missing_paths)

    escaped = StreamPaths(
        (tmp_path / "outside.out").resolve(),
        run_root / "stderr.txt",
    )
    with pytest.raises(ContractViolationError, match="escapes"):
        validate_stream_paths(escaped, run_root=run_root)



def test_stream_paths_are_extracted_from_direct_or_nested_capture(
    tmp_path: Path,
) -> None:
    stdout = (tmp_path / "stdout.txt").resolve()
    stderr = (tmp_path / "stderr.txt").resolve()

    direct = stream_paths_from_capture(
        {"stdout_path": stdout, "stderr_path": stderr}
    )
    nested = stream_paths_from_capture(
        SimpleNamespace(
            stdout=SimpleNamespace(path=stdout),
            stderr=SimpleNamespace(path=stderr),
        )
    )

    assert direct == nested == StreamPaths(stdout, stderr)

    with pytest.raises(ContractViolationError, match="both"):
        stream_paths_from_capture({"stdout_path": stdout})




def test_scan_source_aggregate_preserves_unicode_and_escapes_boundaries(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    scan_path = _write(
        run_root / "raw" / "scan" / "grammar.scan.txt",
        (
            "GF_WORDBENCH_SCAN_LOG 1.0\r\n"
            "subject: GrammaireÉté.gf\r\n"
            f"{_SECTION_RULE}\r\n"
            "message: élève détecté\r\n"
        ).encode(),
    )
    source = _source(
        run_root,
        "raw/scan/grammar.scan.txt",
        subject="lib/src/french/GrammaireÉté.gf",
        role="scan_log",
        category=AggregateSourceCategory.SCAN,
        sequence=0,
    )

    rendered = render_scan_sources(_metadata(mode=None), [source], run_root=run_root)

    assert rendered.kind is AggregateKind.SCAN
    assert rendered.source_count == 1
    assert rendered.included_sections == 1
    assert rendered.missing_sections == 0
    assert rendered.boundary_escapes == 1
    assert "message: élève détecté" in rendered.text
    assert f"\\{_SECTION_RULE}" in rendered.text
    assert scan_path.read_bytes().decode("utf-8").count(_SECTION_RULE) == 1
    assert rendered.text.endswith("\n")
    assert "\r" not in rendered.text.split("message: élève détecté", 1)[1]



def test_operation_aggregate_orders_sources_and_references_scan_logs(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "raw" / "master.log", b"master\n")
    _write(run_root / "raw" / "gf_version.out.txt", b"GF 3.12\n")
    _write(run_root / "raw" / "gf_version.err.txt", b"")
    _write(run_root / "raw" / "compile" / "a.out.txt", b"stdout\n")
    _write(run_root / "raw" / "compile" / "a.err.txt", b"stderr\n")

    sources = [
        _source(
            run_root,
            "raw/compile/a.err.txt",
            subject="A.gf",
            role="compile_stderr",
            category=AggregateSourceCategory.COMPILE,
            sequence=0,
            stream=AggregateStream.STDERR,
        ),
        _source(
            run_root,
            "raw/gf_version.err.txt",
            subject="gf-version",
            role="gf_version_stderr",
            category=AggregateSourceCategory.VERSION,
            sequence=0,
            stream=AggregateStream.STDERR,
        ),
        _source(
            run_root,
            "raw/master.log",
            subject="run-lifecycle",
            role="master_log",
            category=AggregateSourceCategory.LIFECYCLE,
            sequence=0,
        ),
        _source(
            run_root,
            "raw/compile/a.out.txt",
            subject="A.gf",
            role="compile_stdout",
            category=AggregateSourceCategory.COMPILE,
            sequence=0,
            stream=AggregateStream.STDOUT,
        ),
        _source(
            run_root,
            "raw/gf_version.out.txt",
            subject="gf-version",
            role="gf_version_stdout",
            category=AggregateSourceCategory.VERSION,
            sequence=0,
            stream=AggregateStream.STDOUT,
        ),
    ]

    rendered = render_all_logs(
        _metadata(),
        reversed(sources),
        run_root=run_root,
        scan_section_count=7,
    )

    text = rendered.text
    positions = [
        text.index("role: master_log"),
        text.index("role: gf_version_stdout"),
        text.index("role: gf_version_stderr"),
        text.index("role: compile_stdout"),
        text.index("role: compile_stderr"),
        text.index("SCAN LOGS"),
    ]
    assert positions == sorted(positions)
    assert "<EMPTY STREAM>" in text
    assert "Aggregate: raw/ALL_SCAN_LOGS.TXT" in text
    assert "Sections: 7" in text
    assert "summary.json" in text.splitlines()[6]
    assert rendered.included_sections == 5



def test_operation_aggregate_represents_missing_evidence_without_creating_it(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    missing = AggregateLogSource(
        subject="scenario:unicode",
        role="scenario_stderr",
        category=AggregateSourceCategory.SCENARIO,
        sequence=3,
        relative_path=None,
        source_path=None,
        stream=AggregateStream.STDERR,
        status="MISSING",
        required=False,
        missing_reason="scenario was skipped",
    )

    rendered = render_all_logs(_metadata(), [missing], run_root=run_root)

    assert rendered.missing_sections == 1
    assert "path: null" in rendered.text
    assert "status: MISSING" in rendered.text
    assert "reason: scenario was skipped" in rendered.text
    assert "<MISSING EVIDENCE: scenario:unicode>" in rendered.text
    assert list(run_root.rglob("*.txt")) == []



def test_operation_aggregate_rejects_reports_and_invalid_utf8(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    report = _write(run_root / "summary.json", b"{}\n")
    report_source = AggregateLogSource(
        subject="summary",
        role="summary",
        category=AggregateSourceCategory.OTHER,
        sequence=0,
        relative_path=PurePosixPath("summary.json"),
        source_path=report,
    )

    with pytest.raises(ValueError, match="must not embed report"):
        render_all_logs(_metadata(), [report_source], run_root=run_root)

    invalid = _write(run_root / "raw" / "compile" / "bad.err.txt", b"\xff")
    invalid_source = AggregateLogSource(
        subject="Bad.gf",
        role="compile_stderr",
        category=AggregateSourceCategory.COMPILE,
        sequence=0,
        relative_path=PurePosixPath("raw/compile/bad.err.txt"),
        source_path=invalid,
        stream=AggregateStream.STDERR,
    )

    with pytest.raises(UnicodeDecodeError):
        render_all_logs(_metadata(), [invalid_source], run_root=run_root)



def test_aggregate_writer_is_utf8_lf_verified_and_replace_is_explicit(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "raw" / "master.log", "début\r\nfin\r\n".encode())
    source = _source(
        run_root,
        "raw/master.log",
        subject="run-lifecycle",
        role="master_log",
        category=AggregateSourceCategory.LIFECYCLE,
        sequence=0,
    )
    destination = run_root / Path(ALL_LOGS_RELATIVE_PATH.as_posix())

    result = write_all_logs(
        destination,
        _metadata(),
        [source],
        run_root=run_root,
    )

    payload = destination.read_bytes()
    assert result.path == destination
    assert result.size_bytes == len(payload)
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert payload.endswith(b"\n")

    with pytest.raises(FileExistsError):
        write_all_logs(destination, _metadata(), [source], run_root=run_root)

    replacement = write_all_logs(
        destination,
        _metadata(),
        [source],
        run_root=run_root,
        allow_replace=True,
    )
    assert replacement.sha256 == result.sha256



def test_scan_source_writer_uses_canonical_destination_and_digest(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    _write(run_root / "raw" / "scan" / "a.scan.txt", b"status: OK\n")
    source = _source(
        run_root,
        "raw/scan/a.scan.txt",
        subject="A.gf",
        role="scan_log",
        category=AggregateSourceCategory.SCAN,
        sequence=0,
    )
    destination = run_root / Path(ALL_SCAN_LOGS_RELATIVE_PATH.as_posix())

    result = write_scan_sources(
        destination,
        _metadata(mode=None),
        [source],
        run_root=run_root,
    )

    assert result.kind is AggregateKind.SCAN
    assert result.path == destination
    assert result.sha256 == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert destination.read_text(encoding="utf-8").startswith(
        "GF WORDBENCH — ALL SCAN LOGS\n"
    )



def test_scan_log_sections_sort_and_distinguish_missing_required_evidence(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    a_path = _write(
        run_root / "raw" / "scan" / "a.scan.txt",
        "status: OK\nmessage: élève\n".encode(),
    )
    results = [
        {
            "project_relative_path": "z/Z.gf",
            "status": "SKIPPED",
            "required": False,
            "scan_log_path": None,
            "message": "optional scan disabled",
        },
        {
            "project_relative_path": "a/A.gf",
            "status": "OK",
            "required": True,
            "scan_log_path": a_path,
        },
        {
            "project_relative_path": "m/M.gf",
            "status": "ERROR",
            "required": True,
            "scan_log_path": run_root / "raw" / "scan" / "missing.scan.txt",
            "message": "writer failed",
        },
    ]

    sections = build_scan_log_sections(results, run_root=run_root)
    aggregate = render_all_scan_logs(
        run_id="20260725_123456",
        project_id="francais-demo",
        generated_at=_GENERATED_AT,
        sections=sections,
    )

    assert [section.subject for section in sections] == [
        "a/A.gf",
        "m/M.gf",
        "z/Z.gf",
    ]
    assert sections[0].included is True
    assert sections[0].sha256 == hashlib.sha256(a_path.read_bytes()).hexdigest()
    assert sections[1].included is False
    assert sections[1].missing_reason == "writer failed"
    assert sections[2].required is False
    assert aggregate.status is ScanLogAggregateStatus.ERROR
    assert aggregate.included_section_count == 1
    assert aggregate.missing_section_count == 2
    assert aggregate.missing_required_count == 1
    assert "message: élève" in aggregate.text



def test_scan_log_render_is_partial_when_only_optional_evidence_is_missing() -> None:
    sections = (
        ScanLogSection(
            subject="optional.gf",
            status="MISSING",
            required=False,
            missing_reason="not selected",
        ),
    )

    aggregate = render_all_scan_logs(
        run_id="20260725_123456",
        project_id="francais-demo",
        generated_at=_GENERATED_AT,
        sections=sections,
    )

    assert aggregate.status is ScanLogAggregateStatus.PARTIAL
    assert aggregate.missing_required_count == 0
    assert "path: null" in aggregate.text
    assert "reason: not selected" in aggregate.text



def test_scan_log_writer_persists_hash_size_utf8_and_lf(
    tmp_path: Path,
) -> None:
    run_root = tmp_path.resolve()
    source = _write(
        run_root / "raw" / "scan" / "unicode.scan.txt",
        "status: OK\r\nmessage: français\r\n".encode(),
    )
    destination = run_root / "raw" / "ALL_SCAN_LOGS.TXT"

    aggregate = write_all_scan_logs_result(
        file_results=(
            {
                "project_relative_path": "src/Unicode.gf",
                "status": "OK",
                "required": True,
                "scan_log_path": source,
            },
        ),
        destination=destination,
        run_root=run_root,
        run_id="20260725_123456",
        project_id="francais-demo",
        generated_at=_GENERATED_AT,
    )

    payload = destination.read_bytes()
    assert aggregate.status is ScanLogAggregateStatus.COMPLETE
    assert aggregate.path == destination
    assert aggregate.size_bytes == len(payload)
    assert aggregate.sha256 == hashlib.sha256(payload).hexdigest()
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert payload.endswith(b"\n")
    assert payload.decode("utf-8") == aggregate.text



def test_scan_log_builder_rejects_escape_duplicate_path_and_invalid_utf8(
    tmp_path: Path,
) -> None:
    run_root = (tmp_path / "run").resolve()
    run_root.mkdir()
    outside = _write((tmp_path / "outside.scan.txt").resolve(), b"status: OK\n")

    with pytest.raises((ContractViolationError, ValueError)):
        build_scan_log_sections(
            (
                {
                    "subject": "outside.gf",
                    "scan_log_path": outside,
                },
            ),
            run_root=run_root,
        )

    shared = _write(run_root / "raw" / "shared.scan.txt", b"status: OK\n")
    with pytest.raises((ContractViolationError, ValueError)):
        build_scan_log_sections(
            (
                {"subject": "A.gf", "scan_log_path": shared},
                {"subject": "B.gf", "scan_log_path": shared},
            ),
            run_root=run_root,
        )

    invalid = _write(run_root / "raw" / "invalid.scan.txt", b"\xff")
    with pytest.raises((ContractViolationError, ValueError)):
        build_scan_log_sections(
            ({"subject": "invalid.gf", "scan_log_path": invalid},),
            run_root=run_root,
        )



def test_log_redaction_records_explicit_reasons_without_mutating_unicode() -> None:
    policy = LogRedactionPolicy(
        protected_values=("été-secret",),
        sensitive_path_prefixes=(r"C:\Users\Alice",),
        configured_rules=(
            ConfiguredRedactionRule(
                rule_id="ticket-number",
                reason=RedactionReason.CONFIGURED_PATTERN,
                pattern=r"TICKET-[0-9]+",
                mode=RedactionRuleMode.REGEX,
            ),
        ),
    )
    original = (
        "message=élève validé\n"
        "password=bonjour\n"
        "token: abc123\n"
        "secret=été-secret\n"
        r"path=C:\Users\Alice\project" "\n"
        "reference=TICKET-4831\n"
    )

    redacted = redact_log_text(
        original,
        artifact_path=r"raw\compile\unicode.err.txt",
        policy=policy,
        local_unredacted_evidence_exists=True,
    )

    assert redacted.changed is True
    assert redacted.record is not None
    assert redacted.record.artifact_path == "raw/compile/unicode.err.txt"
    assert redacted.record.local_unredacted_evidence_exists is True
    assert redacted.replacement_count >= 5
    assert "message=élève validé" in redacted.text
    assert "bonjour" not in redacted.text
    assert "abc123" not in redacted.text
    assert "été-secret" not in redacted.text
    assert "Alice" not in redacted.text
    assert "TICKET-4831" not in redacted.text
    assert contains_redaction_marker(redacted.text)
    reasons = set(parse_redaction_markers(redacted.text))
    assert {
        "password",
        "token",
        "protected_value",
        "sensitive_path",
        "configured_pattern",
    } <= reasons



def test_subject_keys_are_portable_deterministic_and_collision_safe() -> None:
    identity = "lib/src/french/Grammaire française.gf"

    first = make_subject_key(identity)
    second = make_subject_key(Path(identity))
    allocated = allocate_subject_keys(("A.gf", "a.gf"))

    assert first == second
    assert is_subject_key(first)
    assert validate_subject_key(first) == first
    assert "/" not in first
    assert "\\" not in first
    assert normalize_subject_identity(identity) == identity.removesuffix(".gf")
    assert allocated["A"] != allocated["a"]
    assert all(is_subject_key(value) for value in allocated.values())

    with pytest.raises(ContractViolationError, match="reserved Windows"):
        make_subject_key("CON.gf")



def test_truncation_helpers_preserve_bounds_and_emit_auditable_metadata() -> None:
    byte_result = truncate_bytes(
        b"0123456789",
        6,
        strategy=RetentionStrategy.HEAD_TAIL,
        reason=TruncationReason.OUTPUT_LIMIT,
    )
    text_result = truncate_text(
        "école-été",
        8,
        strategy=RetentionStrategy.HEAD_TAIL,
    )
    line_result = truncate_lines(
        "one\ntwo\nthree\nfour\nfive\n",
        3,
        strategy=RetentionStrategy.HEAD_TAIL,
    )

    assert byte_result.data == b"012789"
    assert byte_result.metadata.truncated is True
    assert byte_result.metadata.observed_bytes == 10
    assert byte_result.metadata.retained_bytes == 6
    assert len(text_result.text.encode("utf-8")) <= 8
    assert text_result.metadata.truncated is True
    assert line_result.metadata.retained_lines == 3
    assert line_result.text.splitlines() == ["one", "two", "five"]

    rendered = append_truncation_marker("evidence", byte_result.metadata)
    assert rendered.startswith("evidence\n")
    assert "<TRUNCATED:" in rendered
    assert "reason=output_limit" in rendered



def test_excerpt_around_line_preserves_requested_context_and_line_identity() -> None:
    text = "\n".join(f"line-{index}" for index in range(1, 11)) + "\n"

    excerpt = excerpt_around_line(
        text,
        6,
        before_lines=2,
        after_lines=1,
    )

    assert excerpt.text.splitlines() == [
        "line-4",
        "line-5",
        "line-6",
        "line-7",
    ]
    assert excerpt.metadata.start_line == 4
    assert excerpt.metadata.end_line == 7
    assert excerpt.metadata.observed_lines == 10
    assert excerpt.metadata.retained_lines == 4
