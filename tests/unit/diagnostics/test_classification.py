from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.diagnostics.classification.causality import (
    CausalityDecision,
    CausalityFacts,
    CausalityReason,
    classify_causality,
    normalize_blocker_ids,
    normalize_subject_id,
    validate_causality_decision,
)
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)


def test_success_is_classified_as_ok_and_preserves_evidence() -> None:
    evidence = (Path("logs/compile.jsonl"),)

    decision = classify_causality(
        subject_id="lib/src/Test.gf",
        status=ValidationStatus.OK,
        error_kind=ErrorKind.OK,
        facts=CausalityFacts(evidence_paths=evidence),
    )

    assert decision == CausalityDecision(
        diagnostic_class=DiagnosticClass.OK,
        blocked_by=(),
        is_direct=False,
        reason=CausalityReason.SUCCESS,
        explanation="The requested validation criterion passed.",
        evidence_paths=evidence,
    )
    validate_causality_decision(
        status=ValidationStatus.OK,
        error_kind=ErrorKind.OK,
        decision=decision,
    )


@pytest.mark.parametrize(
    ("facts", "expected_class", "expected_reason"),
    (
        (
            CausalityFacts(policy_skip=True),
            DiagnosticClass.SKIPPED,
            CausalityReason.POLICY_SKIP,
        ),
        (
            CausalityFacts(excluded_noise=True),
            DiagnosticClass.NOISE,
            CausalityReason.EXCLUDED_NOISE,
        ),
    ),
)
def test_skipped_results_are_distinguished_from_noise(
    facts: CausalityFacts,
    expected_class: DiagnosticClass,
    expected_reason: CausalityReason,
) -> None:
    decision = classify_causality(
        subject_id="lib/src/Optional.gf",
        status=ValidationStatus.SKIPPED,
        error_kind=ErrorKind.OK,
        facts=facts,
    )

    assert decision.diagnostic_class is expected_class
    assert decision.reason is expected_reason
    assert decision.blocked_by == ()
    assert decision.is_direct is False
    validate_causality_decision(
        status=ValidationStatus.SKIPPED,
        error_kind=ErrorKind.OK,
        decision=decision,
    )


@pytest.mark.parametrize(
    ("facts", "expected_reason"),
    (
        (CausalityFacts(local_location=True), CausalityReason.LOCAL_LOCATION),
        (CausalityFacts(self_reference=True), CausalityReason.SELF_REFERENCE),
        (
            CausalityFacts(local_stage_failure=True),
            CausalityReason.LOCAL_STAGE_FAILURE,
        ),
        (
            CausalityFacts(local_contract_failure=True),
            CausalityReason.LOCAL_CONTRACT_FAILURE,
        ),
        (
            CausalityFacts(local_artifact_failure=True),
            CausalityReason.LOCAL_ARTIFACT_FAILURE,
        ),
    ),
)
def test_structured_local_evidence_is_direct(
    facts: CausalityFacts,
    expected_reason: CausalityReason,
) -> None:
    decision = classify_causality(
        subject_id="lib/src/Local.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.OTHER,
        facts=facts,
    )

    assert decision.diagnostic_class is DiagnosticClass.DIRECT
    assert decision.reason is expected_reason
    assert decision.is_direct is True
    assert decision.blocked_by == ()


@pytest.mark.parametrize("error_kind", (ErrorKind.TYPE, ErrorKind.SYNTAX))
def test_local_type_or_syntax_is_direct_without_external_uncertainty(
    error_kind: ErrorKind,
) -> None:
    decision = classify_causality(
        subject_id="lib/src/Grammar.gf",
        status=ValidationStatus.FAIL,
        error_kind=error_kind,
        facts=CausalityFacts(),
    )

    assert decision.diagnostic_class is DiagnosticClass.DIRECT
    assert decision.reason is CausalityReason.LOCAL_TYPE_OR_SYNTAX
    assert decision.is_direct is True


def test_confirmed_failed_blockers_take_precedence_over_local_evidence() -> None:
    decision = classify_causality(
        subject_id="lib/src/Concrete.gf",
        status=ValidationStatus.ERROR,
        error_kind=ErrorKind.TYPE,
        facts=CausalityFacts(
            confirmed_blockers=(
                "lib/src/Abstract.gf",
                "lib\\src\\Abstract.gf",
                "lib/src/Concrete.gf",
            ),
            local_location=True,
            conflicting_evidence=True,
        ),
    )

    assert decision.diagnostic_class is DiagnosticClass.DOWNSTREAM
    assert decision.reason is CausalityReason.CONFIRMED_BLOCKER
    assert decision.blocked_by == ("lib/src/Abstract.gf",)
    assert decision.is_direct is False


@pytest.mark.parametrize(
    ("error_kind", "facts", "expected_reason"),
    (
        (
            ErrorKind.OTHER,
            CausalityFacts(unresolved_cycle=True),
            CausalityReason.UNRESOLVED_CYCLE,
        ),
        (
            ErrorKind.OTHER,
            CausalityFacts(candidate_blockers=("lib/src/Candidate.gf",)),
            CausalityReason.CONFLICTING_EVIDENCE,
        ),
        (
            ErrorKind.TIMEOUT,
            CausalityFacts(),
            CausalityReason.TIMEOUT_WITHOUT_BLOCKER,
        ),
        (
            ErrorKind.TOOL,
            CausalityFacts(),
            CausalityReason.GLOBAL_OR_LAUNCH_FAILURE,
        ),
        (
            ErrorKind.TYPE,
            CausalityFacts(parser_failure=True),
            CausalityReason.PARSER_FAILURE,
        ),
        (
            ErrorKind.TYPE,
            CausalityFacts(output_truncated=True),
            CausalityReason.OUTPUT_TRUNCATED,
        ),
        (
            ErrorKind.TYPE,
            CausalityFacts(combined_inputs=True),
            CausalityReason.COMBINED_INPUTS,
        ),
        (
            ErrorKind.TYPE,
            CausalityFacts(unknown_external_reference=True),
            CausalityReason.UNKNOWN_EXTERNAL_REFERENCE,
        ),
        (
            ErrorKind.TYPE,
            CausalityFacts(successful_external_reference=True),
            CausalityReason.SUCCESSFUL_EXTERNAL_REFERENCE,
        ),
        (
            ErrorKind.INTERNAL,
            CausalityFacts(),
            CausalityReason.INSUFFICIENT_EVIDENCE,
        ),
    ),
)
def test_uncertain_failures_remain_ambiguous(
    error_kind: ErrorKind,
    facts: CausalityFacts,
    expected_reason: CausalityReason,
) -> None:
    decision = classify_causality(
        subject_id="lib/src/Uncertain.gf",
        status=ValidationStatus.ERROR,
        error_kind=error_kind,
        facts=facts,
    )

    assert decision.diagnostic_class is DiagnosticClass.AMBIGUOUS
    assert decision.reason is expected_reason
    assert decision.blocked_by == ()
    assert decision.is_direct is False


@pytest.mark.parametrize(
    ("subject_id", "expected"),
    (
        (" lib\\src\\Test.gf ", "lib/src/Test.gf"),
        ("project//scenarios///smoke.gfs", "project/scenarios/smoke.gfs"),
        ("module.gf", "module.gf"),
    ),
)
def test_subject_identity_is_normalized(
    subject_id: str,
    expected: str,
) -> None:
    assert normalize_subject_id(subject_id) == expected


@pytest.mark.parametrize(
    "subject_id",
    ("", "   ", "/absolute.gf", "C:/absolute.gf", "../escape.gf", "a/../b.gf"),
)
def test_subject_identity_rejects_unstable_or_absolute_values(
    subject_id: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_subject_id(subject_id)


def test_blocker_ids_are_normalized_deduplicated_and_sorted() -> None:
    assert normalize_blocker_ids(
        (
            "z/Last.gf",
            "a\\First.gf",
            "A/Second.gf",
            "a/First.gf",
        )
    ) == (
        "a/First.gf",
        "A/Second.gf",
        "z/Last.gf",
    )


@pytest.mark.parametrize(
    ("status", "error_kind", "facts", "message"),
    (
        (
            ValidationStatus.OK,
            ErrorKind.TYPE,
            CausalityFacts(),
            "status OK requires error_kind OK",
        ),
        (
            ValidationStatus.FAIL,
            ErrorKind.OK,
            CausalityFacts(),
            "FAIL or ERROR requires a non-OK error_kind",
        ),
        (
            ValidationStatus.ERROR,
            ErrorKind.INTERNAL,
            CausalityFacts(policy_skip=True),
            "failing results cannot be classified",
        ),
        (
            ValidationStatus.SKIPPED,
            ErrorKind.OK,
            CausalityFacts(confirmed_blockers=("lib/src/Blocker.gf",)),
            "canonical skipped results cannot carry confirmed blockers",
        ),
    ),
)
def test_incoherent_inputs_are_rejected(
    status: ValidationStatus,
    error_kind: ErrorKind,
    facts: CausalityFacts,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        classify_causality(
            subject_id="lib/src/Test.gf",
            status=status,
            error_kind=error_kind,
            facts=facts,
        )


def test_decision_model_rejects_downstream_without_blockers() -> None:
    with pytest.raises(ValueError, match="downstream decisions require blocked_by"):
        CausalityDecision(
            diagnostic_class=DiagnosticClass.DOWNSTREAM,
            blocked_by=(),
            is_direct=False,
            reason=CausalityReason.CONFIRMED_BLOCKER,
            explanation="Blocked.",
        )


def test_facts_are_immutable_and_metadata_is_defensively_copied() -> None:
    metadata = {"stage": "compile"}
    facts = CausalityFacts(
        confirmed_blockers=("lib/src/Base.gf",),
        evidence_paths=(Path("logs/raw.log"),),
        metadata=metadata,
    )
    metadata["stage"] = "changed"

    assert facts.confirmed_blockers == ("lib/src/Base.gf",)
    assert facts.evidence_paths == (Path("logs/raw.log"),)
    assert dict(facts.metadata) == {"stage": "compile"}
    with pytest.raises(TypeError):
        facts.metadata["stage"] = "changed"  # type: ignore[index]
