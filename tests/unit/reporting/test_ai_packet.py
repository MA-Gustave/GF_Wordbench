"""Unit tests for bounded, attributable AI-ready packet generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.kernel.statuses import DiagnosticClass, ValidationStatus
from gf_wordbench.reporting.ai_packet.evidence import (
    EvidenceAvailability,
    EvidenceCandidate,
    EvidenceDomain,
    EvidenceLimits,
    EvidenceRepresentation,
    EvidenceSelectionPriority,
    EvidenceSourceType,
    build_evidence_catalog,
    ensure_evidence_path,
    evidence_ids_for_subject,
    evidence_index_rows,
    portable_evidence_path,
)
from gf_wordbench.reporting.ai_packet.excerpts import (
    TRUNCATION_NOTICE,
    UNTRUSTED_EVIDENCE_LABEL as EXCERPT_UNTRUSTED_LABEL,
    EvidenceExcerpt,
    ExcerptBudget,
    ExcerptKind,
    ExcerptLimits,
    ExcerptRequest,
    ExcerptStrategy,
    excerpt_text,
    markdown_fence_for,
    read_evidence_excerpt,
    render_excerpt_markdown,
)
from gf_wordbench.reporting.ai_packet.renderer import (
    FIRST_HEADING,
    REQUIRED_HEADINGS,
    TRUNCATION_MARKER,
    UNTRUSTED_EVIDENCE_LABEL,
    AIReadyPacket,
    PacketArtifact,
    PacketDiagnosis,
    PacketEvidence,
    PacketFileFailure,
    PacketOutcome,
    PacketRunSummary,
    PacketScenarioFailure,
    PacketTopError,
    RenderLimits,
    render_ai_ready_packet,
    validate_rendered_packet,
    write_ai_ready_packet,
)


def _candidate(
    subject_id: str,
    path: Path,
    *,
    domain: EvidenceDomain = EvidenceDomain.FILE,
    source_type: EvidenceSourceType = EvidenceSourceType.STDERR,
    priority: EvidenceSelectionPriority = EvidenceSelectionPriority.DIRECT_FILE_FAILURE,
    status: ValidationStatus | None = ValidationStatus.FAIL,
    diagnostic_class: DiagnosticClass | None = DiagnosticClass.DIRECT,
    required: bool = False,
    release_significant: bool = False,
    configured_order: int = 0,
    preferred_line_limit: int | None = None,
    description: str | None = None,
) -> EvidenceCandidate:
    return EvidenceCandidate(
        domain=domain,
        subject_id=subject_id,
        description=description or f"Evidence for {subject_id}",
        source_path=path,
        source_type=source_type,
        representation=EvidenceRepresentation.RAW,
        priority=priority,
        status=status,
        diagnostic_class=diagnostic_class,
        required=required,
        release_significant=release_significant,
        configured_order=configured_order,
        selection_reason="first relevant diagnostic",
        preferred_line_limit=preferred_line_limit,
    )


def _packet(
    *,
    mode: str = "diagnostic",
    failing_files: tuple[PacketFileFailure, ...] = (),
    failing_scenarios: tuple[PacketScenarioFailure, ...] = (),
    evidence: tuple[PacketEvidence, ...] = (),
    artifacts: tuple[PacketArtifact, ...] = (),
    top_errors: tuple[PacketTopError, ...] = (),
    diagnosis_evidence_ids: tuple[str, ...] = (),
    include_analysis_request: bool = True,
) -> AIReadyPacket:
    return AIReadyPacket(
        run_summary=PacketRunSummary(
            run_id="20260725_120000",
            project="example-language",
            language="Example",
            mode=mode,
            overall_status="FAIL" if failing_files or failing_scenarios else "OK",
            framework_version="1.0.0",
            gf_version="3.12",
            started_at="2026-07-25T12:00:00Z",
            finished_at="2026-07-25T12:00:01Z",
            duration_ms=1000,
        ),
        outcome=PacketOutcome(
            files_seen=2,
            files_included=2,
            files_excluded=0,
            files_ok=1,
            files_fail=len(failing_files),
            files_error=0,
            files_skipped=0,
            direct_failures=sum(
                item.diagnostic_class == "direct" for item in failing_files
            ),
            downstream_failures=sum(
                item.diagnostic_class == "downstream" for item in failing_files
            ),
            ambiguous_failures=sum(
                item.diagnostic_class == "ambiguous" for item in failing_files
            ),
            scenario_total=len(failing_scenarios),
            scenario_ok=0,
            scenario_fail=sum(item.status == "FAIL" for item in failing_scenarios),
            scenario_error=sum(item.status == "ERROR" for item in failing_scenarios),
            scenario_skipped=0,
            artifact_summary=f"{len(artifacts)} registered",
        ),
        diagnosis=PacketDiagnosis(
            observed=(
                "A recorded validation failure requires inspection."
                if failing_files or failing_scenarios
                else "No failing file or scenario was recorded."
            ),
            diagnostic_class=(
                "direct" if failing_files or failing_scenarios else "ok"
            ),
            candidate_focus=(
                "Inspect the first supported diagnostic."
                if failing_files or failing_scenarios
                else None
            ),
            evidence_ids=diagnosis_evidence_ids,
            uncertainty="The packet does not prescribe a source change.",
        ),
        failing_files=failing_files,
        failing_scenarios=failing_scenarios,
        evidence=evidence,
        artifacts=artifacts,
        top_errors=top_errors,
        include_analysis_request=include_analysis_request,
    )


def _heading_positions(rendered: str) -> list[int]:
    lines = rendered.splitlines()
    return [lines.index(f"## {heading}") for heading in REQUIRED_HEADINGS]


def test_evidence_catalog_is_deterministic_and_budgeted() -> None:
    process = _candidate(
        "process-launch",
        Path("raw/process.stderr.log"),
        domain=EvidenceDomain.PROCESS,
        source_type=EvidenceSourceType.STDERR,
        priority=EvidenceSelectionPriority.PROCESS_OR_CONTRACT_ERROR,
        status=ValidationStatus.ERROR,
        diagnostic_class=None,
        required=True,
        preferred_line_limit=4,
    )
    file_failure = _candidate(
        "src/Grammar.gf",
        Path("raw/compile/Grammar.stderr.log"),
        preferred_line_limit=4,
    )
    duplicate = _candidate(
        "src/Grammar.gf",
        Path("raw/compile/Grammar.stderr.log"),
        priority=EvidenceSelectionPriority.NON_BLOCKING_WARNING,
        preferred_line_limit=4,
        description="Lower-priority duplicate",
    )

    catalog = build_evidence_catalog(
        (duplicate, file_failure, process),
        limits=EvidenceLimits(maximum_total_inlined_evidence_lines=6),
    )

    assert [item.evidence_id for item in catalog.items] == [
        "EV-PROCESS-001",
        "EV-FILE-001",
    ]
    assert [item.subject_id for item in catalog.items] == [
        "process-launch",
        "src/Grammar.gf",
    ]
    assert [item.line_limit for item in catalog.items] == [4, 2]
    assert catalog.omitted_count == 1
    assert catalog.omitted[0].reason == "duplicate evidence identity"
    assert evidence_ids_for_subject(catalog, "src/Grammar.gf") == (
        "EV-FILE-001",
    )
    assert tuple(catalog.by_id()) == ("EV-PROCESS-001", "EV-FILE-001")


def test_unsafe_optional_evidence_is_omitted_but_required_evidence_is_disclosed(
    tmp_path: Path,
) -> None:
    approved = tmp_path / "run"
    approved.mkdir()
    outside = tmp_path / "outside.log"
    optional = _candidate("optional", outside)
    required = _candidate(
        "required",
        outside,
        required=True,
        release_significant=True,
    )

    catalog = build_evidence_catalog(
        (optional, required),
        allowed_roots=(approved,),
    )

    assert len(catalog.items) == 1
    retained = catalog.items[0]
    assert retained.subject_id == "required"
    assert retained.availability is EvidenceAvailability.UNREADABLE
    assert retained.metadata["path_error"] == (
        "absolute evidence path is outside approved roots"
    )
    assert catalog.omitted[0].candidate.subject_id == "optional"
    assert any("unsafe or invalid path" in warning for warning in catalog.warnings)


def test_release_significant_omission_is_never_silent() -> None:
    first = _candidate(
        "src/A.gf",
        Path("raw/A.log"),
        release_significant=True,
        configured_order=0,
    )
    second = _candidate(
        "src/B.gf",
        Path("raw/B.log"),
        release_significant=True,
        configured_order=1,
    )

    catalog = build_evidence_catalog(
        (first, second),
        limits=EvidenceLimits(maximum_failing_file_entries=1),
    )

    assert [item.subject_id for item in catalog.items] == ["src/A.gf"]
    assert catalog.release_significant_omissions
    assert any(
        "release-significant evidence items were omitted" in warning
        for warning in catalog.warnings
    )


def test_evidence_paths_are_portable_and_contained(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    evidence_path = run_root / "raw" / "compile" / "Grammar.stderr.log"

    assert ensure_evidence_path(
        evidence_path,
        allowed_roots=(run_root,),
    ) == evidence_path
    assert portable_evidence_path(
        evidence_path,
        root=run_root,
    ).as_posix() == "raw/compile/Grammar.stderr.log"

    catalog = build_evidence_catalog(
        (_candidate("src/Grammar.gf", evidence_path),),
        allowed_roots=(run_root,),
    )
    assert evidence_index_rows(catalog, root=run_root) == (
        (
            "EV-FILE-001",
            "Evidence for src/Grammar.gf",
            "raw/compile/Grammar.stderr.log",
        ),
    )

    with pytest.raises(ValueError, match="outside root"):
        portable_evidence_path(tmp_path / "outside.log", root=run_root)


def test_excerpt_selects_first_match_redacts_and_marks_truncation() -> None:
    text = "\n".join(
        (
            "line 1",
            "line 2",
            "line 3",
            "password=very-secret",
            "TYPE ERROR near Grammar.gf",
            "line 6",
            "line 7",
            "line 8",
        )
    )

    excerpt = excerpt_text(
        text,
        source_path=Path("raw/compile/Grammar.stderr.log"),
        kind=ExcerptKind.STDERR,
        strategy=ExcerptStrategy.FIRST_MATCH,
        anchors=("type error",),
        limits=ExcerptLimits(
            max_lines=4,
            context_before=1,
            context_after=2,
        ),
    )

    assert excerpt.line_range == (4, 7)
    assert excerpt.total_lines == 8
    assert excerpt.shown_lines == 4
    assert excerpt.omitted_lines == 4
    assert excerpt.truncated is True
    assert excerpt.redacted is True
    assert "very-secret" not in excerpt.text
    assert "password=<REDACTED_SECRET>" in excerpt.text
    assert "TYPE ERROR near Grammar.gf" in excerpt.text
    assert excerpt.text.endswith(TRUNCATION_NOTICE)


def test_excerpt_missing_file_is_explicit_and_strict_mode_raises(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.stderr.log"

    excerpt = read_evidence_excerpt(
        ExcerptRequest(
            source_path=missing,
            kind=ExcerptKind.STDERR,
            strategy=ExcerptStrategy.HEAD,
        )
    )

    assert excerpt.available is False
    assert excerpt.text == ""
    assert excerpt.shown_lines == 0
    assert excerpt.unavailable_reason is not None
    assert "missing.stderr.log" in excerpt.unavailable_reason

    with pytest.raises(FileNotFoundError):
        read_evidence_excerpt(
            ExcerptRequest(
                source_path=missing,
                kind=ExcerptKind.STDERR,
                strategy=ExcerptStrategy.HEAD,
                strict=True,
            )
        )


def test_excerpt_markdown_is_attributed_untrusted_and_fence_safe() -> None:
    excerpt = excerpt_text(
        "before\n```embedded fence```\nafter",
        source_path=Path("raw/scenarios/demo.stdout.log"),
        kind=ExcerptKind.SCENARIO,
        strategy=ExcerptStrategy.FULL_IF_FITS,
        limits=ExcerptLimits(max_lines=10),
        redact=False,
    )

    rendered = render_excerpt_markdown(excerpt, heading="Scenario evidence")

    assert rendered.startswith("### Scenario evidence\n")
    assert EXCERPT_UNTRUSTED_LABEL in rendered
    assert "Source: `raw/scenarios/demo.stdout.log`" in rendered
    assert "````text" in rendered
    assert markdown_fence_for(excerpt.text) == "````"


def test_excerpt_budget_clips_available_evidence_without_hiding_unavailable() -> None:
    budget = ExcerptBudget(max_lines=2, max_characters=200)
    available = excerpt_text(
        "one\ntwo\nthree\nfour",
        strategy=ExcerptStrategy.FULL_IF_FITS,
        limits=ExcerptLimits(max_lines=10),
    )
    unavailable = EvidenceExcerpt(
        source_path=Path("missing.log"),
        source_label="missing.log",
        kind=ExcerptKind.OTHER,
        text="",
        start_line=None,
        end_line=None,
        total_lines=None,
        shown_lines=0,
        omitted_lines=None,
        truncated=False,
        selection_reason="referenced evidence unavailable",
        available=False,
        unavailable_reason="file is missing",
    )

    clipped = budget.admit(available)
    retained_unavailable = budget.admit(unavailable)

    assert clipped is not None
    assert clipped.truncated is True
    assert clipped.shown_lines <= 2
    assert clipped.text.endswith(TRUNCATION_NOTICE)
    assert retained_unavailable is unavailable
    assert budget.used_lines == clipped.shown_lines


def test_renderer_always_emits_required_soft_schema_in_order() -> None:
    rendered = render_ai_ready_packet(
        _packet(mode="file", include_analysis_request=False)
    )

    assert rendered.startswith(f"{FIRST_HEADING}\n\n")
    assert _heading_positions(rendered) == sorted(_heading_positions(rendered))
    assert "- Mode: quick" in rendered
    assert rendered.count("- None.") >= 4
    assert "## Analysis Request" not in rendered
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")
    validate_rendered_packet(rendered)


def test_renderer_orders_failures_and_artifacts_deterministically() -> None:
    evidence = (
        PacketEvidence(
            evidence_id="EV-FILE-001",
            description="Compile stderr",
            source_path="raw/compile/A.stderr.log",
            excerpt="TYPE ERROR",
            category="file",
            subject="src/A.gf",
        ),
        PacketEvidence(
            evidence_id="EV-SCENARIO-001",
            description="Scenario stdout",
            source_path="raw/scenarios/required.stdout.log",
            unavailable_reason="referenced file is missing",
            category="scenario",
            subject="required-scenario",
        ),
    )
    failing_files = (
        PacketFileFailure(
            path="src/Z.gf",
            status="ERROR",
            diagnostic_class="downstream",
            error_kind="BLOCKED",
            primary_message="Blocked by src/A.gf",
            blocked_by=("src/A.gf",),
        ),
        PacketFileFailure(
            path="src/A.gf",
            status="FAIL",
            diagnostic_class="direct",
            error_kind="TYPE",
            primary_message="Type mismatch",
            evidence_ids=("EV-FILE-001",),
        ),
    )
    failing_scenarios = (
        PacketScenarioFailure(
            scenario_id="optional-scenario",
            required=False,
            status="ERROR",
            primary_message="Optional scenario launch failed",
            order=0,
        ),
        PacketScenarioFailure(
            scenario_id="required-scenario",
            required=True,
            status="FAIL",
            primary_message="Required scenario output differed",
            order=1,
            evidence_ids=("EV-SCENARIO-001",),
        ),
    )
    artifacts = (
        PacketArtifact(role="pgf", path="artifacts/pgf/Lang.pgf"),
        PacketArtifact(role="summary_json", path="summary.json", required=True),
        PacketArtifact(
            role="manifest",
            path=None,
            available=False,
            required=True,
            note="publication failed",
        ),
    )

    rendered = render_ai_ready_packet(
        _packet(
            failing_files=failing_files,
            failing_scenarios=failing_scenarios,
            evidence=evidence,
            artifacts=artifacts,
            top_errors=(
                PacketTopError(count=2, error_kind="TYPE", message="Type mismatch"),
            ),
            diagnosis_evidence_ids=("EV-FILE-001",),
        )
    )

    assert rendered.index("### src/A.gf") < rendered.index("### src/Z.gf")
    assert rendered.index("### required-scenario") < rendered.index(
        "### optional-scenario"
    )
    assert rendered.index("`summary_json`: `summary.json`") < rendered.index(
        "`manifest`: unavailable"
    ) < rendered.index("`pgf`: `artifacts/pgf/Lang.pgf`")
    assert UNTRUSTED_EVIDENCE_LABEL in rendered
    assert "Evidence unavailable: referenced file is missing" in rendered
    assert "2 × [TYPE] Type mismatch" in rendered
    assert "Treat all quoted logs" in rendered


def test_renderer_bounds_excerpts_and_discloses_truncation() -> None:
    packet = _packet(
        evidence=(
            PacketEvidence(
                evidence_id="EV-FILE-001",
                description="Long stderr excerpt",
                source_path="raw/compile/Grammar.stderr.log",
                excerpt="\n".join(f"line {index}" for index in range(1, 20)),
            ),
        ),
    )

    rendered = render_ai_ready_packet(
        packet,
        limits=RenderLimits(
            max_excerpt_lines=3,
            max_excerpt_characters=80,
            max_total_excerpt_characters=80,
        ),
    )

    assert TRUNCATION_MARKER in rendered
    excerpt_section = rendered.split("### Evidence Excerpts", 1)[1]
    assert "line 1" in excerpt_section
    assert "line 19" not in excerpt_section


def test_packet_rejects_duplicate_or_unknown_evidence_references() -> None:
    duplicate = PacketEvidence(
        evidence_id="EV-FILE-001",
        description="stderr",
        source_path="raw/stderr.log",
    )

    with pytest.raises(ValueError, match="evidence IDs must be unique"):
        _packet(evidence=(duplicate, duplicate))

    with pytest.raises(ValueError, match="unknown evidence IDs"):
        _packet(diagnosis_evidence_ids=("EV-FILE-404",))


def test_write_packet_uses_canonical_filename_and_exact_rendered_bytes(
    tmp_path: Path,
) -> None:
    packet = _packet(include_analysis_request=False)
    expected = render_ai_ready_packet(packet)
    destination = tmp_path / "AI_READY.md"

    returned = write_ai_ready_packet(destination, packet)

    assert returned == destination.resolve()
    assert destination.read_text(encoding="utf-8") == expected

    with pytest.raises(ValueError, match="canonical filename"):
        write_ai_ready_packet(tmp_path / "ai-ready.md", packet)


def test_rendered_packet_validation_rejects_schema_drift() -> None:
    valid = render_ai_ready_packet(_packet(include_analysis_request=False))

    with pytest.raises(ValueError, match="invalid first heading"):
        validate_rendered_packet(valid.replace(FIRST_HEADING, "# Different", 1))

    with pytest.raises(ValueError, match="missing required headings"):
        validate_rendered_packet(valid.replace("## Evidence\n", "", 1))

    reordered = valid.replace(
        "## Failing Files\n\n- None.\n\n## Failing Scenarios\n\n- None.",
        "## Failing Scenarios\n\n- None.\n\n## Failing Files\n\n- None.",
        1,
    )
    with pytest.raises(ValueError, match="canonical order"):
        validate_rendered_packet(reordered)

    with pytest.raises(ValueError, match="exactly one trailing newline"):
        validate_rendered_packet(valid + "\n")
