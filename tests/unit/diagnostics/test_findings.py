"""Unit tests for deterministic diagnostic finding construction and aggregation."""

from __future__ import annotations

from collections.abc import Mapping
import re
from types import MappingProxyType

import pytest

from gf_wordbench.diagnostics.findings import (
    blocking_findings,
    build_finding,
    deduplicate_findings,
    finding_counts,
    finding_signature,
    findings_by_target,
    has_blocking_findings,
    merge_findings,
    rebuild_finding,
    sort_findings,
    validate_findings,
)
from gf_wordbench.diagnostics.models import EvidenceRef, Finding
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import DiagnosticClass, ErrorKind

_PRODUCER = ProducerInfo(name="gf-wordbench", version="1.0.0")
_FINDING_ID_RE = re.compile(r"^finding-[a-f0-9]{24}$")


def _evidence(
    *,
    path: str = "raw/compile/Main.stderr.log",
    role: str = "compile_stderr",
    stream: str | None = "stderr",
    line: int | None = 3,
    column: int | None = 7,
    excerpt: str | None = "Type mismatch",
) -> EvidenceRef:
    return EvidenceRef(
        role=role,
        path=path,
        stream=stream,
        line=line,
        column=column,
        excerpt=excerpt,
    )


def _finding(
    *,
    severity: str = "error",
    kind: str = "gf_diagnostic",
    message: str = "Type mismatch",
    target: str = "src/Main.gf",
    evidence_refs: tuple[EvidenceRef, ...] | None = None,
    diagnostic_class: DiagnosticClass | None = DiagnosticClass.DIRECT,
    error_kind: ErrorKind | None = ErrorKind.TYPE,
    rule_id: str | None = "GF-DIAG-TYPE",
    blocking: bool = True,
    metadata: Mapping[str, str] | None = None,
    finding_id: str | None = None,
) -> Finding:
    return build_finding(
        severity=severity,
        kind=kind,
        message=message,
        target=target,
        evidence_refs=((_evidence(),) if evidence_refs is None else evidence_refs),
        producer=_PRODUCER,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
        rule_id=rule_id,
        blocking=blocking,
        metadata=metadata,
        finding_id=finding_id,
    )


def test_build_finding_normalizes_inputs_and_derives_stable_identity() -> None:
    later = _evidence(
        path="raw/compile/Main.stderr.log",
        line=8,
        column=2,
        excerpt="continued context",
    )
    earlier = _evidence(line=2, column=1, excerpt="primary diagnostic")

    first = _finding(
        severity="ERROR",
        evidence_refs=(later, earlier, later),
        metadata={
            "tool_version": "3.12",
            "phase": "compile",
        },
    )
    second = _finding(
        severity="error",
        evidence_refs=(earlier, later),
        metadata={
            "phase": "compile",
            "tool_version": "3.12",
        },
    )

    assert first.severity == "error"
    assert _FINDING_ID_RE.fullmatch(first.finding_id)
    assert first.finding_id == second.finding_id
    assert finding_signature(first) == finding_signature(second)

    assert first.evidence_refs == (earlier, later)
    assert tuple(first.metadata) == ("phase", "tool_version")
    assert isinstance(first.metadata, MappingProxyType)

    with pytest.raises(TypeError):
        first.metadata["phase"] = "changed"  # type: ignore[index]


def test_content_changes_produce_distinct_finding_identities() -> None:
    original = _finding()
    changed_message = _finding(message="Unknown identifier")
    changed_target = _finding(target="src/Other.gf")
    changed_evidence = _finding(
        evidence_refs=(
            _evidence(
                path="raw/compile/Other.stderr.log",
                line=1,
            ),
        )
    )

    identities = {
        original.finding_id,
        changed_message.finding_id,
        changed_target.finding_id,
        changed_evidence.finding_id,
    }

    assert len(identities) == 4


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("severity", "critical", ValueError),
        ("kind", "GF Diagnostic", ValueError),
        ("rule_id", "invalid-rule", ValueError),
        ("blocking", 1, TypeError),
    ],
)
def test_build_finding_rejects_noncanonical_fields(
    field: str,
    value: object,
    error_type: type[Exception],
) -> None:
    arguments: dict[str, object] = {
        "severity": "error",
        "kind": "gf_diagnostic",
        "message": "Type mismatch",
        "target": "src/Main.gf",
        "evidence_refs": (_evidence(),),
        "producer": _PRODUCER,
        "diagnostic_class": DiagnosticClass.DIRECT,
        "error_kind": ErrorKind.TYPE,
        "rule_id": "GF-DIAG-TYPE",
        "blocking": True,
    }
    arguments[field] = value

    with pytest.raises(error_type):
        build_finding(**arguments)  # type: ignore[arg-type]


def test_static_scan_findings_cannot_claim_authoritative_gf_causality() -> None:
    with pytest.raises(ValueError, match="GF error kind"):
        _finding(
            kind="static_scan",
            diagnostic_class=DiagnosticClass.NOISE,
            error_kind=ErrorKind.TYPE,
            rule_id="SCAN-STYLE-001",
        )

    with pytest.raises(ValueError, match="direct or downstream causality"):
        _finding(
            kind="static_scan",
            diagnostic_class=DiagnosticClass.DIRECT,
            error_kind=None,
            rule_id="SCAN-STYLE-001",
        )

    finding = _finding(
        severity="warning",
        kind="static_scan",
        diagnostic_class=DiagnosticClass.NOISE,
        error_kind=None,
        rule_id="SCAN-STYLE-001",
        blocking=False,
    )

    assert finding.diagnostic_class is DiagnosticClass.NOISE
    assert finding.error_kind is None
    assert finding.blocking is False


def test_rebuild_finding_preserves_semantics_and_rederives_identity() -> None:
    original = _finding(metadata={"phase": "compile"})
    rebuilt = rebuild_finding(
        original,
        severity="warning",
        message="Type mismatch accepted by policy",
        blocking=False,
        metadata={
            "phase": "review",
            "disposition": "accepted",
        },
    )

    assert rebuilt is not original
    assert rebuilt.finding_id != original.finding_id
    assert rebuilt.severity == "warning"
    assert rebuilt.message == "Type mismatch accepted by policy"
    assert rebuilt.blocking is False
    assert dict(rebuilt.metadata) == {
        "disposition": "accepted",
        "phase": "review",
    }

    assert rebuilt.kind == original.kind
    assert rebuilt.target == original.target
    assert rebuilt.evidence_refs == original.evidence_refs
    assert rebuilt.producer == original.producer
    assert rebuilt.diagnostic_class is original.diagnostic_class
    assert rebuilt.error_kind is original.error_kind
    assert rebuilt.rule_id == original.rule_id


def test_validate_findings_preserves_order_and_rejects_duplicate_ids() -> None:
    first = _finding(target="src/B.gf")
    second = _finding(target="src/A.gf")

    assert validate_findings((first, second)) == (first, second)

    duplicate_id = _finding(
        target="src/Other.gf",
        finding_id=first.finding_id,
    )
    with pytest.raises(ValueError, match="duplicate finding ID"):
        validate_findings((first, duplicate_id))

    with pytest.raises(TypeError, match="Finding"):
        validate_findings((first, object()))  # type: ignore[arg-type]


def test_sort_findings_uses_canonical_severity_blocking_target_and_location_order() -> None:
    warning = _finding(
        severity="warning",
        target="src/Zeta.gf",
        blocking=False,
    )
    nonblocking_error = _finding(
        target="src/alpha.gf",
        blocking=False,
        evidence_refs=(_evidence(line=9),),
    )
    blocking_late = _finding(
        target="src/alpha.gf",
        blocking=True,
        evidence_refs=(_evidence(line=8),),
    )
    blocking_early = _finding(
        target="src/alpha.gf",
        blocking=True,
        evidence_refs=(_evidence(line=2),),
    )
    fatal = _finding(
        severity="fatal",
        target="src/Omega.gf",
        blocking=True,
    )

    ordered = sort_findings(
        (
            warning,
            nonblocking_error,
            blocking_late,
            fatal,
            blocking_early,
        )
    )

    assert ordered == (
        fatal,
        blocking_early,
        blocking_late,
        nonblocking_error,
        warning,
    )


def test_deduplication_uses_semantic_signature_and_stable_identity_choice() -> None:
    first = _finding(
        finding_id="finding-bbbbbbbbbbbbbbbbbbbbbbbb",
    )
    equivalent = _finding(
        finding_id="finding-aaaaaaaaaaaaaaaaaaaaaaaa",
    )
    different = _finding(message="Different diagnostic")

    deduplicated = deduplicate_findings((first, equivalent, different))

    assert len(deduplicated) == 2
    assert deduplicated[0].finding_id == "finding-aaaaaaaaaaaaaaaaaaaaaaaa"
    assert deduplicated[1] is different


def test_merge_findings_deduplicates_groups_and_restores_canonical_order() -> None:
    duplicate_a = _finding(
        target="src/B.gf",
        finding_id="finding-bbbbbbbbbbbbbbbbbbbbbbbb",
    )
    duplicate_b = _finding(
        target="src/B.gf",
        finding_id="finding-aaaaaaaaaaaaaaaaaaaaaaaa",
    )
    fatal = _finding(
        severity="fatal",
        target="src/A.gf",
        message="Internal failure",
        error_kind=ErrorKind.INTERNAL,
        rule_id="GF-DIAG-INTERNAL",
    )

    merged = merge_findings(
        (duplicate_a,),
        (fatal, duplicate_b),
    )

    assert merged == (
        fatal,
        duplicate_b,
    )


def test_grouping_counts_and_blocking_projection_are_immutable_and_deterministic() -> None:
    fatal = _finding(
        severity="fatal",
        target="src/B.gf",
        message="Internal failure",
        error_kind=ErrorKind.INTERNAL,
        rule_id="GF-DIAG-INTERNAL",
    )
    warning = _finding(
        severity="warning",
        target="src/A.gf",
        blocking=False,
    )
    error = _finding(
        target="src/A.gf",
        message="Unknown identifier",
        rule_id="GF-DIAG-UNKNOWN",
    )
    findings = (warning, fatal, error)

    grouped = findings_by_target(findings)
    counts = finding_counts(findings)

    assert isinstance(grouped, MappingProxyType)
    assert tuple(grouped) == ("src/A.gf", "src/B.gf")
    assert grouped["src/A.gf"] == (error, warning)
    assert grouped["src/B.gf"] == (fatal,)

    assert dict(counts) == {
        "fatal": 1,
        "error": 1,
        "warning": 1,
        "info": 0,
        "blocking": 2,
        "total": 3,
    }
    assert blocking_findings(findings) == (fatal, error)
    assert has_blocking_findings(findings) is True
    assert has_blocking_findings((warning,)) is False

    with pytest.raises(TypeError):
        counts["total"] = 0  # type: ignore[index]
