"""Unit tests for bounded deterministic scenario-assertion evaluation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.validation.scenarios.assertions import (
    ArtifactAssertionEvidence,
    AssertionBatchResult,
    AssertionCategory,
    AssertionEvaluationContext,
    AssertionInputSource,
    AssertionKind,
    AssertionStatus,
    CountComparison,
    DiagnosticAssertionEvidence,
    GoldAssertionEvidence,
    ProcessAssertionEvidence,
    ScenarioAssertionResult,
    ScenarioAssertionSpec,
    SectionAssertionEvidence,
    aggregate_assertion_results,
    evaluate_assertion,
    evaluate_assertion_results,
    evaluate_assertions,
)

_FAILURE_MESSAGE: Final = "The reviewed scenario assertion failed."


def _spec(
    assertion_id: str,
    kind: AssertionKind,
    source: AssertionInputSource,
    *,
    section_id: str | None = None,
    parameters: dict[str, str | int | bool | tuple[str, ...] | None] | None = None,
    required: bool = True,
    release_significant: bool = False,
) -> ScenarioAssertionSpec:
    return ScenarioAssertionSpec(
        assertion_id=assertion_id,
        kind=kind,
        source=source,
        failure_message=_FAILURE_MESSAGE,
        required=required,
        release_significant=release_significant,
        section_id=section_id,
        parameters={} if parameters is None else parameters,
    )


def _context(tmp_path: Path) -> AssertionEvaluationContext:
    run_root = tmp_path.resolve()
    evidence_path = run_root / "raw" / "scenarios" / "scenario.out.txt"
    return AssertionEvaluationContext(
        process=ProcessAssertionEvidence(
            completed=True,
            exit_code=0,
            timed_out=False,
            cancelled=False,
            output_limit_exceeded=False,
            capture_completed=True,
            evidence_path=evidence_path,
        ),
        sections={
            "trees": SectionAssertionEvidence(
                section_id="trees",
                completed=True,
                text="TreeOne\nTreeTwo\n",
                begin_line=1,
                end_line=4,
                evidence_path=evidence_path,
            )
        },
        raw_stdout="GF banner\nTREE: TreeOne\n",
        raw_stderr="warning: recoverable\n",
        normalized_output="TREE: TreeOne\nTREE: TreeTwo\n",
        normalized_sections={"trees": "TreeOne\nTreeTwo\n"},
        diagnostics=(
            DiagnosticAssertionEvidence(
                diagnostic_id="GF-TYPE-001",
                kind="type",
                message="Expected Cat but inferred NP.",
                fatal=True,
                section_id="trees",
                evidence_path=evidence_path,
            ),
            DiagnosticAssertionEvidence(
                diagnostic_id="GF-WARN-001",
                kind="warning",
                message="Recoverable warning.",
                fatal=False,
                evidence_path=evidence_path,
            ),
        ),
        counts={"parse.count": 2, "missing-linearizations": 0},
        artifacts={
            "release-pgf": ArtifactAssertionEvidence(
                artifact_id="release-pgf",
                path=run_root / "artifacts" / "pgf" / "Grammar.pgf",
                exists=True,
                size_bytes=128,
                contained=True,
                current=True,
                evidence_path=evidence_path,
            )
        },
        gold=GoldAssertionEvidence(
            evaluated=True,
            matched=True,
            evidence_path=run_root / "details" / "gold-diff.txt",
        ),
        run_root=run_root,
    )


def _result(
    spec: ScenarioAssertionSpec,
    status: AssertionStatus,
) -> ScenarioAssertionResult:
    return ScenarioAssertionResult(
        assertion_id=spec.assertion_id,
        assertion_kind=spec.kind.value,
        status=status,
        message="Evaluated assertion.",
        evidence_path=None,
        section_id=spec.section_id,
    )


def test_canonical_vocabularies_and_kind_categories_are_stable() -> None:
    assert tuple(status.value for status in AssertionStatus) == (
        "passed",
        "failed",
        "error",
        "skipped",
    )
    assert tuple(category.value for category in AssertionCategory) == (
        "process",
        "section",
        "diagnostic",
        "text",
        "count",
        "artifact",
        "gold",
    )
    assert tuple(comparison.value for comparison in CountComparison) == (
        "eq",
        "ne",
        "lt",
        "le",
        "gt",
        "ge",
    )

    expected_categories = {
        AssertionKind.PROCESS_COMPLETED: AssertionCategory.PROCESS,
        AssertionKind.EXIT_CODE_EQUALS: AssertionCategory.PROCESS,
        AssertionKind.NOT_TIMED_OUT: AssertionCategory.PROCESS,
        AssertionKind.NOT_CANCELLED: AssertionCategory.PROCESS,
        AssertionKind.OUTPUT_LIMIT_NOT_EXCEEDED: AssertionCategory.PROCESS,
        AssertionKind.CAPTURE_COMPLETED: AssertionCategory.PROCESS,
        AssertionKind.SECTION_EXISTS: AssertionCategory.SECTION,
        AssertionKind.SECTION_COMPLETED: AssertionCategory.SECTION,
        AssertionKind.SECTION_NON_EMPTY: AssertionCategory.SECTION,
        AssertionKind.DIAGNOSTIC_PRESENT: AssertionCategory.DIAGNOSTIC,
        AssertionKind.DIAGNOSTIC_ABSENT: AssertionCategory.DIAGNOSTIC,
        AssertionKind.TEXT_CONTAINS: AssertionCategory.TEXT,
        AssertionKind.TEXT_EXCLUDES: AssertionCategory.TEXT,
        AssertionKind.TEXT_EQUALS: AssertionCategory.TEXT,
        AssertionKind.TEXT_MATCHES: AssertionCategory.TEXT,
        AssertionKind.COUNT_COMPARE: AssertionCategory.COUNT,
        AssertionKind.ARTIFACT_EXISTS: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_NON_EMPTY: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_CONTAINED: AssertionCategory.ARTIFACT,
        AssertionKind.ARTIFACT_CURRENT: AssertionCategory.ARTIFACT,
        AssertionKind.GOLD_MATCHES: AssertionCategory.GOLD,
    }
    assert {kind: kind.category for kind in AssertionKind} == expected_categories


def test_assertion_spec_is_immutable_and_defensively_copies_parameters() -> None:
    parameters: dict[str, str | int | bool | tuple[str, ...] | None] = {
        "expected": "TreeOne",
        "ignore_case": False,
    }
    spec = _spec(
        "contains-tree",
        AssertionKind.TEXT_CONTAINS,
        AssertionInputSource.NORMALIZED_OUTPUT,
        parameters=parameters,
        release_significant=True,
    )

    parameters["expected"] = "mutated"

    assert spec.parameters == {"expected": "TreeOne", "ignore_case": False}
    assert isinstance(spec.parameters, MappingProxyType)
    assert spec.release_significant is True
    with pytest.raises(TypeError):
        spec.parameters["expected"] = "forbidden"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        spec.required = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "error_type", "message"),
    [
        (
            {
                "assertion_id": "Invalid ID",
                "kind": AssertionKind.PROCESS_COMPLETED,
                "source": AssertionInputSource.PROCESS,
            },
            ValueError,
            "assertion_id",
        ),
        (
            {
                "assertion_id": "bad-source",
                "kind": AssertionKind.PROCESS_COMPLETED,
                "source": AssertionInputSource.RAW_STDOUT,
            },
            ValueError,
            "invalid for assertion kind",
        ),
        (
            {
                "assertion_id": "missing-parameter",
                "kind": AssertionKind.EXIT_CODE_EQUALS,
                "source": AssertionInputSource.PROCESS,
            },
            ValueError,
            "missing parameters: expected",
        ),
        (
            {
                "assertion_id": "missing-section",
                "kind": AssertionKind.SECTION_COMPLETED,
                "source": AssertionInputSource.SECTIONS,
            },
            ValueError,
            "requires section_id",
        ),
        (
            {
                "assertion_id": "missing-filter",
                "kind": AssertionKind.DIAGNOSTIC_PRESENT,
                "source": AssertionInputSource.DIAGNOSTICS,
            },
            ValueError,
            "diagnostic filter",
        ),
        (
            {
                "assertion_id": "unknown-parameter",
                "kind": AssertionKind.TEXT_EQUALS,
                "source": AssertionInputSource.NORMALIZED_OUTPUT,
                "parameters": {"expected": "x", "unknown": True},
            },
            ValueError,
            "unsupported parameters",
        ),
        (
            {
                "assertion_id": "unsafe-regex",
                "kind": AssertionKind.TEXT_MATCHES,
                "source": AssertionInputSource.NORMALIZED_OUTPUT,
                "parameters": {"expected": "(?=Tree)"},
            },
            ValueError,
            "regex extensions",
        ),
    ],
)
def test_assertion_spec_rejects_invalid_or_unbounded_contracts(
    kwargs: dict[str, object],
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        ScenarioAssertionSpec(
            failure_message=_FAILURE_MESSAGE,
            **kwargs,  # type: ignore[arg-type]
        )


def test_evidence_models_reject_contradictory_states(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="completed cannot be true"):
        ProcessAssertionEvidence(
            completed=True,
            exit_code=None,
            timed_out=True,
            cancelled=False,
            output_limit_exceeded=False,
            capture_completed=False,
        )
    with pytest.raises(ValueError, match="completed section must have an end_line"):
        SectionAssertionEvidence(
            section_id="trees",
            completed=True,
            begin_line=1,
        )
    with pytest.raises(ValueError, match="missing artifact cannot have a positive size"):
        ArtifactAssertionEvidence(
            artifact_id="pgf",
            path=tmp_path / "Grammar.pgf",
            exists=False,
            size_bytes=1,
            contained=True,
        )
    with pytest.raises(ValueError, match="matched must be None"):
        GoldAssertionEvidence(evaluated=False, matched=True)
    with pytest.raises(ValueError, match="missing required gold"):
        GoldAssertionEvidence(
            evaluated=True,
            matched=False,
            missing_required_gold=True,
        )


def test_context_freezes_evidence_and_enforces_identity_and_containment(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)

    assert isinstance(context.sections, MappingProxyType)
    assert isinstance(context.normalized_sections, MappingProxyType)
    assert isinstance(context.counts, MappingProxyType)
    assert isinstance(context.artifacts, MappingProxyType)
    assert isinstance(context.diagnostics, tuple)
    with pytest.raises(TypeError):
        context.counts["parse.count"] = 99  # type: ignore[index]

    with pytest.raises(ValueError, match="does not match value identity"):
        replace(
            context,
            sections={"wrong": context.sections["trees"]},
        )
    with pytest.raises(ValueError, match="must be non-negative"):
        replace(context, counts={"parse.count": -1})
    with pytest.raises(ValueError, match="escapes run_root"):
        replace(
            context,
            process=replace(
                context.process,
                evidence_path=tmp_path.parent / "outside.txt",
            ),
        )
    with pytest.raises(ValueError, match="evidence path must be absolute"):
        replace(
            context,
            process=replace(context.process, evidence_path=Path("relative.txt")),
        )


def test_process_assertions_cover_success_failure_and_unavailable_exit_code(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    specs = (
        _spec(
            "process-completed",
            AssertionKind.PROCESS_COMPLETED,
            AssertionInputSource.PROCESS,
        ),
        _spec(
            "exit-zero",
            AssertionKind.EXIT_CODE_EQUALS,
            AssertionInputSource.PROCESS,
            parameters={"expected": 0},
        ),
        _spec(
            "not-timed-out",
            AssertionKind.NOT_TIMED_OUT,
            AssertionInputSource.PROCESS,
        ),
        _spec(
            "not-cancelled",
            AssertionKind.NOT_CANCELLED,
            AssertionInputSource.PROCESS,
        ),
        _spec(
            "capture-within-limit",
            AssertionKind.OUTPUT_LIMIT_NOT_EXCEEDED,
            AssertionInputSource.PROCESS,
        ),
        _spec(
            "capture-completed",
            AssertionKind.CAPTURE_COMPLETED,
            AssertionInputSource.PROCESS,
        ),
    )

    results = evaluate_assertion_results(specs, context)

    assert tuple(result.status for result in results) == (
        AssertionStatus.PASSED,
    ) * len(specs)
    assert all(result.evidence_path == context.process.evidence_path for result in results)

    nonzero = replace(context, process=replace(context.process, exit_code=2))
    failed = evaluate_assertion(specs[1], nonzero)
    assert failed.status is AssertionStatus.FAILED
    assert failed.message == _FAILURE_MESSAGE

    unavailable = replace(context, process=replace(context.process, exit_code=None))
    error = evaluate_assertion(specs[1], unavailable)
    assert error.status is AssertionStatus.ERROR
    assert error.message == "Process exit code is unavailable."


def test_section_assertions_require_parsed_completion_and_nonempty_output(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    exists = _spec(
        "section-exists",
        AssertionKind.SECTION_EXISTS,
        AssertionInputSource.SECTIONS,
        section_id="trees",
    )
    completed = _spec(
        "section-completed",
        AssertionKind.SECTION_COMPLETED,
        AssertionInputSource.SECTIONS,
        section_id="trees",
    )
    nonempty = _spec(
        "section-nonempty",
        AssertionKind.SECTION_NON_EMPTY,
        AssertionInputSource.NORMALIZED_SECTION,
        section_id="trees",
    )

    assert evaluate_assertion(exists, context).status is AssertionStatus.PASSED
    assert evaluate_assertion(completed, context).status is AssertionStatus.PASSED
    assert evaluate_assertion(nonempty, context).status is AssertionStatus.PASSED

    missing = replace(context, sections={}, normalized_sections={})
    missing_result = evaluate_assertion(exists, missing)
    assert missing_result.status is AssertionStatus.ERROR
    assert "is absent" in missing_result.message

    incomplete_section = replace(
        context.sections["trees"],
        completed=False,
        end_line=None,
    )
    incomplete = replace(context, sections={"trees": incomplete_section})
    incomplete_result = evaluate_assertion(completed, incomplete)
    assert incomplete_result.status is AssertionStatus.ERROR
    assert "marker contract" in incomplete_result.message

    empty = replace(context, normalized_sections={"trees": "  \n"})
    empty_result = evaluate_assertion(nonempty, empty)
    assert empty_result.status is AssertionStatus.FAILED
    assert empty_result.message == _FAILURE_MESSAGE


def test_diagnostic_assertions_use_structured_filters_and_explicit_sources(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    present = _spec(
        "type-diagnostic-present",
        AssertionKind.DIAGNOSTIC_PRESENT,
        AssertionInputSource.DIAGNOSTICS,
        section_id="trees",
        parameters={
            "diagnostic_id": "GF-TYPE-001",
            "kind": "type",
            "message_pattern": "expected cat",
            "fatal": True,
            "ignore_case": True,
        },
    )
    absent = _spec(
        "syntax-diagnostic-absent",
        AssertionKind.DIAGNOSTIC_ABSENT,
        AssertionInputSource.DIAGNOSTICS,
        parameters={"kind": "syntax"},
    )

    present_result = evaluate_assertion(present, context)
    absent_result = evaluate_assertion(absent, context)

    assert present_result.status is AssertionStatus.PASSED
    assert present_result.evidence_path == context.diagnostics[0].evidence_path
    assert absent_result.status is AssertionStatus.PASSED

    prohibited = _spec(
        "fatal-diagnostic-absent",
        AssertionKind.DIAGNOSTIC_ABSENT,
        AssertionInputSource.DIAGNOSTICS,
        parameters={"fatal": True},
    )
    prohibited_result = evaluate_assertion(prohibited, context)
    assert prohibited_result.status is AssertionStatus.FAILED
    assert prohibited_result.message == _FAILURE_MESSAGE


@pytest.mark.parametrize(
    ("kind", "source", "section_id", "parameters"),
    [
        (
            AssertionKind.TEXT_CONTAINS,
            AssertionInputSource.RAW_STDOUT,
            None,
            {"expected": "tree: treeone", "ignore_case": True},
        ),
        (
            AssertionKind.TEXT_EXCLUDES,
            AssertionInputSource.RAW_STDERR,
            None,
            {"expected": "fatal"},
        ),
        (
            AssertionKind.TEXT_EQUALS,
            AssertionInputSource.NORMALIZED_SECTION,
            "trees",
            {"expected": "TreeOne\nTreeTwo\n"},
        ),
        (
            AssertionKind.TEXT_MATCHES,
            AssertionInputSource.NORMALIZED_OUTPUT,
            None,
            {"expected": r"TREE: TreeOne\nTREE: TreeTwo\n", "full_match": True},
        ),
    ],
)
def test_text_assertions_are_deterministic_over_declared_evidence(
    tmp_path: Path,
    kind: AssertionKind,
    source: AssertionInputSource,
    section_id: str | None,
    parameters: dict[str, str | bool],
) -> None:
    result = evaluate_assertion(
        _spec(
            f"text-{kind.value}",
            kind,
            source,
            section_id=section_id,
            parameters=parameters,
        ),
        _context(tmp_path),
    )

    assert result.status is AssertionStatus.PASSED


def test_text_assertion_unavailable_evidence_becomes_structured_error(
    tmp_path: Path,
) -> None:
    context = replace(_context(tmp_path), normalized_output=None)
    spec = _spec(
        "normalized-output-present",
        AssertionKind.TEXT_CONTAINS,
        AssertionInputSource.NORMALIZED_OUTPUT,
        parameters={"expected": "TreeOne"},
    )

    result = evaluate_assertion(spec, context)

    assert result.status is AssertionStatus.ERROR
    assert "normalized output is unavailable" in result.message
    assert result.evidence_path == context.process.evidence_path


@pytest.mark.parametrize(
    ("operator", "expected", "status"),
    [
        (CountComparison.EQUAL, 2, AssertionStatus.PASSED),
        (CountComparison.NOT_EQUAL, 3, AssertionStatus.PASSED),
        (CountComparison.LESS_THAN, 3, AssertionStatus.PASSED),
        (CountComparison.LESS_THAN_OR_EQUAL, 2, AssertionStatus.PASSED),
        (CountComparison.GREATER_THAN, 1, AssertionStatus.PASSED),
        (CountComparison.GREATER_THAN_OR_EQUAL, 2, AssertionStatus.PASSED),
        (CountComparison.EQUAL, 1, AssertionStatus.FAILED),
    ],
)
def test_count_assertions_support_the_bounded_operator_vocabulary(
    tmp_path: Path,
    operator: CountComparison,
    expected: int,
    status: AssertionStatus,
) -> None:
    spec = _spec(
        f"count-{operator.value}-{expected}",
        AssertionKind.COUNT_COMPARE,
        AssertionInputSource.COUNTS,
        parameters={
            "name": "parse.count",
            "operator": operator.value,
            "expected": expected,
        },
    )

    result = evaluate_assertion(spec, _context(tmp_path))

    assert result.status is status


def test_missing_count_is_error_not_assertion_failure(tmp_path: Path) -> None:
    spec = _spec(
        "missing-count",
        AssertionKind.COUNT_COMPARE,
        AssertionInputSource.COUNTS,
        parameters={"name": "unknown.count", "operator": "eq", "expected": 0},
    )

    result = evaluate_assertion(spec, _context(tmp_path))

    assert result.status is AssertionStatus.ERROR
    assert result.message == "Count 'unknown.count' is unavailable."


@pytest.mark.parametrize(
    "kind",
    [
        AssertionKind.ARTIFACT_EXISTS,
        AssertionKind.ARTIFACT_NON_EMPTY,
        AssertionKind.ARTIFACT_CONTAINED,
        AssertionKind.ARTIFACT_CURRENT,
    ],
)
def test_artifact_assertions_use_declared_observations(
    tmp_path: Path,
    kind: AssertionKind,
) -> None:
    spec = _spec(
        f"artifact-{kind.value}",
        kind,
        AssertionInputSource.ARTIFACTS,
        parameters={"artifact_id": "release-pgf"},
    )

    result = evaluate_assertion(spec, _context(tmp_path))

    assert result.status is AssertionStatus.PASSED
    assert result.evidence_path == _context(tmp_path).artifacts["release-pgf"].evidence_path


def test_artifact_assertions_distinguish_absence_from_unavailable_metadata(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    missing_exists = _spec(
        "missing-artifact",
        AssertionKind.ARTIFACT_EXISTS,
        AssertionInputSource.ARTIFACTS,
        parameters={"artifact_id": "missing"},
    )
    missing_nonempty = _spec(
        "missing-artifact-size",
        AssertionKind.ARTIFACT_NON_EMPTY,
        AssertionInputSource.ARTIFACTS,
        parameters={"artifact_id": "missing"},
    )

    assert evaluate_assertion(missing_exists, context).status is AssertionStatus.FAILED
    assert evaluate_assertion(missing_nonempty, context).status is AssertionStatus.ERROR

    unknown_freshness = replace(
        context.artifacts["release-pgf"],
        current=None,
    )
    unavailable = replace(context, artifacts={"release-pgf": unknown_freshness})
    current_spec = _spec(
        "artifact-current",
        AssertionKind.ARTIFACT_CURRENT,
        AssertionInputSource.ARTIFACTS,
        parameters={"artifact_id": "release-pgf"},
    )
    result = evaluate_assertion(current_spec, unavailable)
    assert result.status is AssertionStatus.ERROR
    assert "freshness" in result.message


def test_gold_assertion_maps_match_mismatch_and_missing_evidence(
    tmp_path: Path,
) -> None:
    spec = _spec(
        "gold-matches",
        AssertionKind.GOLD_MATCHES,
        AssertionInputSource.GOLD,
    )
    context = _context(tmp_path)

    assert evaluate_assertion(spec, context).status is AssertionStatus.PASSED
    assert (
        evaluate_assertion(
            spec,
            replace(context, gold=replace(context.gold, matched=False)),
        ).status
        is AssertionStatus.FAILED
    )

    missing_gold = replace(
        context,
        gold=GoldAssertionEvidence(
            evaluated=False,
            matched=None,
            missing_required_gold=True,
            evidence_path=context.gold.evidence_path,
        ),
    )
    missing_result = evaluate_assertion(spec, missing_gold)
    assert missing_result.status is AssertionStatus.ERROR
    assert missing_result.message == "Required gold input is missing."

    unavailable_result = evaluate_assertion(spec, replace(context, gold=None))
    assert unavailable_result.status is AssertionStatus.ERROR
    assert unavailable_result.message == "Gold comparison evidence is unavailable."


def test_evaluate_assertions_preserves_spec_order_and_optional_failures_as_warnings(
    tmp_path: Path,
) -> None:
    specs = (
        _spec(
            "required-process",
            AssertionKind.PROCESS_COMPLETED,
            AssertionInputSource.PROCESS,
        ),
        _spec(
            "optional-prohibition",
            AssertionKind.TEXT_EXCLUDES,
            AssertionInputSource.RAW_STDOUT,
            parameters={"expected": "TREE"},
            required=False,
        ),
        _spec(
            "required-gold",
            AssertionKind.GOLD_MATCHES,
            AssertionInputSource.GOLD,
        ),
    )

    batch = evaluate_assertions(specs, _context(tmp_path))

    assert isinstance(batch, AssertionBatchResult)
    assert tuple(result.assertion_id for result in batch.results) == tuple(
        spec.assertion_id for spec in specs
    )
    assert batch.scenario_status is ValidationStatus.OK
    assert batch.warning_assertion_ids == ("optional-prohibition",)


def test_required_assertion_aggregation_uses_error_then_fail_then_ok_precedence() -> None:
    first = _spec(
        "first",
        AssertionKind.PROCESS_COMPLETED,
        AssertionInputSource.PROCESS,
    )
    second = _spec(
        "second",
        AssertionKind.NOT_TIMED_OUT,
        AssertionInputSource.PROCESS,
    )

    status, warnings = aggregate_assertion_results(
        (first, second),
        (_result(first, AssertionStatus.PASSED), _result(second, AssertionStatus.FAILED)),
    )
    assert status is ValidationStatus.FAIL
    assert warnings == ()

    status, _ = aggregate_assertion_results(
        (first, second),
        (_result(first, AssertionStatus.ERROR), _result(second, AssertionStatus.FAILED)),
    )
    assert status is ValidationStatus.ERROR

    status, _ = aggregate_assertion_results(
        (first, second),
        (_result(first, AssertionStatus.SKIPPED), _result(second, AssertionStatus.PASSED)),
    )
    assert status is ValidationStatus.ERROR

    status, _ = aggregate_assertion_results(
        (first, second),
        (_result(first, AssertionStatus.PASSED), _result(second, AssertionStatus.PASSED)),
    )
    assert status is ValidationStatus.OK


def test_batch_validation_rejects_duplicate_missing_unknown_and_mismatched_results(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    duplicate = _spec(
        "duplicate",
        AssertionKind.PROCESS_COMPLETED,
        AssertionInputSource.PROCESS,
    )
    with pytest.raises(ValueError, match="duplicate assertion ID"):
        evaluate_assertions((duplicate, duplicate), context)

    other = _spec(
        "other",
        AssertionKind.NOT_TIMED_OUT,
        AssertionInputSource.PROCESS,
    )
    with pytest.raises(ValueError, match="identical lengths"):
        aggregate_assertion_results((duplicate, other), (_result(duplicate, AssertionStatus.PASSED),))

    unknown_result = ScenarioAssertionResult(
        assertion_id="unknown",
        assertion_kind=duplicate.kind.value,
        status=AssertionStatus.PASSED,
        message="Evaluated assertion.",
        evidence_path=None,
        section_id=None,
    )
    with pytest.raises(ValueError, match="missing result"):
        aggregate_assertion_results(
            (duplicate,),
            (unknown_result,),
        )

    mismatched_kind = replace(
        _result(duplicate, AssertionStatus.PASSED),
        assertion_kind=AssertionKind.NOT_TIMED_OUT.value,
    )
    with pytest.raises(ValueError, match="does not match its specification"):
        aggregate_assertion_results((duplicate,), (mismatched_kind,))
