"""Unit tests for deterministic top-error aggregation and ordering."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

import pytest

from gf_wordbench.diagnostics.classification.top_errors import (
    DEFAULT_TOP_ERROR_POLICY,
    TopErrorAggregationPolicy,
    TopErrorCandidate,
    bucket_top_errors,
    normalize_top_error_message,
    sort_top_errors,
    top_error_sort_key,
    validate_top_error_order,
)
from gf_wordbench.diagnostics.models import TopError
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)


def candidate(
    subject_id: str,
    *,
    subject_kind: str = "file",
    status: ValidationStatus = ValidationStatus.FAIL,
    diagnostic_class: DiagnosticClass = DiagnosticClass.DIRECT,
    error_kind: ErrorKind = ErrorKind.TYPE,
    message: str = "type mismatch",
    occurrence_count: int = 1,
    diagnostic_code: str | None = None,
    origin: str | None = None,
    is_warning: bool = False,
) -> TopErrorCandidate:
    return TopErrorCandidate(
        subject_kind=subject_kind,
        subject_id=subject_id,
        status=status,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
        message=message,
        occurrence_count=occurrence_count,
        diagnostic_code=diagnostic_code,
        origin=origin,
        is_warning=is_warning,
    )


def top_error(
    error_kind: ErrorKind,
    message: str,
    count: int,
    subject_kinds: tuple[str, ...] = (),
) -> TopError:
    return TopError(
        error_kind=error_kind,
        message=message,
        count=count,
        subject_kinds=subject_kinds,
    )


def messages(records: Iterable[TopError]) -> tuple[str, ...]:
    return tuple(record.message for record in records)


def test_default_policy_matches_the_normative_root_cause_policy() -> None:
    assert DEFAULT_TOP_ERROR_POLICY == TopErrorAggregationPolicy()
    assert DEFAULT_TOP_ERROR_POLICY.include_ambiguous is True
    assert DEFAULT_TOP_ERROR_POLICY.include_downstream is False
    assert DEFAULT_TOP_ERROR_POLICY.include_warnings is False
    assert DEFAULT_TOP_ERROR_POLICY.count_occurrences is False
    assert DEFAULT_TOP_ERROR_POLICY.include_subject_kinds == (
        "file",
        "scenario",
        "run",
    )


def test_candidate_normalizes_identity_fields_but_preserves_message_evidence() -> None:
    value = candidate(
        "  grammar/Main.gf  ",
        subject_kind="  file  ",
        message="  type\t mismatch  ",
        diagnostic_code="  GF-TYPE-001  ",
        origin="  compile  ",
    )

    assert value.subject_kind == "file"
    assert value.subject_id == "grammar/Main.gf"
    assert value.message == "  type\t mismatch  "
    assert value.diagnostic_code == "GF-TYPE-001"
    assert value.origin == "compile"


@pytest.mark.parametrize("subject_kind", ["", "module", "FILE", "file/scenario"])
def test_candidate_rejects_unsupported_subject_kinds(subject_kind: str) -> None:
    with pytest.raises(ValueError, match="subject_kind|unsupported"):
        candidate("subject", subject_kind=subject_kind)


@pytest.mark.parametrize(
    ("changes", "error_type", "message"),
    [
        ({"subject_id": "   "}, ValueError, "subject_id"),
        ({"status": "FAIL"}, TypeError, "status"),
        ({"diagnostic_class": "direct"}, TypeError, "diagnostic_class"),
        ({"error_kind": "TYPE"}, TypeError, "error_kind"),
        ({"occurrence_count": True}, TypeError, "occurrence_count"),
        ({"occurrence_count": 0}, ValueError, "occurrence_count"),
        ({"is_warning": 1}, TypeError, "is_warning"),
        ({"message": None}, TypeError, "message"),
        ({"message": "bad\x00message"}, ValueError, "NUL"),
    ],
)
def test_candidate_enforces_typed_bounded_contracts(
    changes: dict[str, object],
    error_type: type[Exception],
    message: str,
) -> None:
    values: dict[str, object] = {
        "subject_kind": "file",
        "subject_id": "grammar/Main.gf",
        "status": ValidationStatus.FAIL,
        "diagnostic_class": DiagnosticClass.DIRECT,
        "error_kind": ErrorKind.TYPE,
        "message": "type mismatch",
    }
    values.update(changes)

    with pytest.raises(error_type, match=message):
        TopErrorCandidate(**values)  # type: ignore[arg-type]


def test_policy_rejects_duplicate_unknown_or_scalar_subject_kind_inputs() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        TopErrorAggregationPolicy(include_subject_kinds=("file", "file"))
    with pytest.raises(ValueError, match="unsupported"):
        TopErrorAggregationPolicy(include_subject_kinds=("file", "module"))
    with pytest.raises(TypeError, match="tuple of strings"):
        TopErrorAggregationPolicy(include_subject_kinds="file")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "include_ambiguous",
        "include_downstream",
        "include_warnings",
        "count_occurrences",
    ],
)
def test_policy_requires_plain_booleans(field_name: str) -> None:
    values = {
        "include_ambiguous": True,
        "include_downstream": False,
        "include_warnings": False,
        "count_occurrences": False,
    }
    values[field_name] = 1
    with pytest.raises(TypeError, match=field_name):
        TopErrorAggregationPolicy(**values)  # type: ignore[arg-type]


def test_message_normalization_is_unicode_and_whitespace_deterministic() -> None:
    decomposed = "cafe\u0301\n\t type   mismatch"
    assert normalize_top_error_message(decomposed) == "café type mismatch"
    assert normalize_top_error_message("  one\r\ntwo  ") == "one two"
    assert normalize_top_error_message("") == ""


@pytest.mark.parametrize("value", [None, 42, b"text"])
def test_message_normalization_rejects_non_strings(value: object) -> None:
    with pytest.raises(TypeError, match="message must be a string"):
        normalize_top_error_message(value)  # type: ignore[arg-type]


def test_bucket_uses_error_kind_and_casefolded_normalized_message_as_key() -> None:
    records = bucket_top_errors(
        [
            candidate("a.gf", message=" Type\tMismatch "),
            candidate("b.gf", message="type mismatch"),
            candidate("c.gf", error_kind=ErrorKind.SYNTAX, message="type mismatch"),
        ]
    )

    assert records == (
        top_error(ErrorKind.TYPE, "Type Mismatch", 2, ("file",)),
        top_error(ErrorKind.SYNTAX, "type mismatch", 1, ("file",)),
    )


def test_bucket_chooses_a_stable_presentation_message_independent_of_input_order() -> None:
    left = candidate("a.gf", message="Type mismatch")
    right = candidate("b.gf", message="type mismatch")

    forward = bucket_top_errors([left, right])
    reverse = bucket_top_errors([right, left])

    assert forward == reverse
    assert forward[0].message == "Type mismatch"


def test_default_count_is_once_per_subject_and_group() -> None:
    records = bucket_top_errors(
        [
            candidate("a.gf", message="same", occurrence_count=8),
            candidate("a.gf", message="same", occurrence_count=3),
            candidate("b.gf", message="same", occurrence_count=5),
            candidate("a.gf", message="other", occurrence_count=9),
        ]
    )

    assert records == (
        top_error(ErrorKind.TYPE, "same", 2, ("file",)),
        top_error(ErrorKind.TYPE, "other", 1, ("file",)),
    )


def test_occurrence_policy_preserves_reported_occurrence_counts() -> None:
    policy = replace(DEFAULT_TOP_ERROR_POLICY, count_occurrences=True)
    records = bucket_top_errors(
        [
            candidate("a.gf", occurrence_count=4),
            candidate("a.gf", occurrence_count=2),
            candidate("b.gf", occurrence_count=3),
        ],
        policy=policy,
    )

    assert records == (
        top_error(ErrorKind.TYPE, "type mismatch", 9, ("file",)),
    )


def test_same_subject_id_in_different_subject_namespaces_counts_separately() -> None:
    records = bucket_top_errors(
        [
            candidate("smoke", subject_kind="file", message="failed"),
            candidate("smoke", subject_kind="scenario", message="failed"),
            candidate("smoke", subject_kind="run", message="failed"),
        ]
    )

    assert records == (
        top_error(
            ErrorKind.TYPE,
            "failed",
            3,
            ("file", "run", "scenario"),
        ),
    )


def test_subject_kind_filter_is_applied_before_aggregation() -> None:
    policy = TopErrorAggregationPolicy(include_subject_kinds=("scenario",))
    records = bucket_top_errors(
        [
            candidate("a.gf", subject_kind="file", message="failure"),
            candidate("smoke", subject_kind="scenario", message="failure"),
            candidate("release", subject_kind="run", message="failure"),
        ],
        policy=policy,
    )

    assert records == (
        top_error(ErrorKind.TYPE, "failure", 1, ("scenario",)),
    )


def test_default_policy_includes_direct_and_ambiguous_root_candidates_only() -> None:
    records = bucket_top_errors(
        [
            candidate("direct.gf", message="direct"),
            candidate(
                "ambiguous.gf",
                diagnostic_class=DiagnosticClass.AMBIGUOUS,
                message="ambiguous",
            ),
            candidate(
                "downstream.gf",
                diagnostic_class=DiagnosticClass.DOWNSTREAM,
                message="downstream",
            ),
            candidate(
                "noise.gf",
                diagnostic_class=DiagnosticClass.NOISE,
                message="noise",
            ),
            candidate(
                "skipped.gf",
                status=ValidationStatus.SKIPPED,
                diagnostic_class=DiagnosticClass.SKIPPED,
                message="skipped",
            ),
            candidate(
                "ok.gf",
                status=ValidationStatus.OK,
                diagnostic_class=DiagnosticClass.OK,
                error_kind=ErrorKind.OK,
                message="ok",
            ),
        ]
    )

    assert messages(records) == ("ambiguous", "direct")


def test_policy_can_include_downstream_and_exclude_ambiguous() -> None:
    policy = TopErrorAggregationPolicy(
        include_ambiguous=False,
        include_downstream=True,
    )
    records = bucket_top_errors(
        [
            candidate(
                "ambiguous.gf",
                diagnostic_class=DiagnosticClass.AMBIGUOUS,
                message="ambiguous",
            ),
            candidate(
                "downstream.gf",
                diagnostic_class=DiagnosticClass.DOWNSTREAM,
                message="downstream",
            ),
        ],
        policy=policy,
    )

    assert messages(records) == ("downstream",)


def test_warning_candidates_require_explicit_warning_policy() -> None:
    warning = candidate(
        "warning.gf",
        message="deprecated construct",
        is_warning=True,
    )

    assert bucket_top_errors([warning]) == ()
    records = bucket_top_errors(
        [warning],
        policy=replace(DEFAULT_TOP_ERROR_POLICY, include_warnings=True),
    )
    assert records == (
        top_error(ErrorKind.TYPE, "deprecated construct", 1, ("file",)),
    )


@pytest.mark.parametrize(
    ("status", "diagnostic_class", "error_kind"),
    [
        (ValidationStatus.OK, DiagnosticClass.DIRECT, ErrorKind.TYPE),
        (ValidationStatus.SKIPPED, DiagnosticClass.DIRECT, ErrorKind.TYPE),
        (ValidationStatus.FAIL, DiagnosticClass.OK, ErrorKind.TYPE),
        (ValidationStatus.FAIL, DiagnosticClass.NOISE, ErrorKind.TYPE),
        (ValidationStatus.FAIL, DiagnosticClass.SKIPPED, ErrorKind.TYPE),
        (ValidationStatus.FAIL, DiagnosticClass.DIRECT, ErrorKind.OK),
    ],
)
def test_ineligible_status_class_and_ok_kind_are_never_aggregated(
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
    error_kind: ErrorKind,
) -> None:
    value = candidate(
        "subject",
        status=status,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
    )
    assert bucket_top_errors([value]) == ()


def test_error_status_is_eligible_for_direct_failures() -> None:
    records = bucket_top_errors(
        [candidate("framework", status=ValidationStatus.ERROR, message="launch failed")]
    )
    assert records == (
        top_error(ErrorKind.TYPE, "launch failed", 1, ("file",)),
    )


def test_empty_normalized_messages_are_excluded_without_affecting_other_records() -> None:
    records = bucket_top_errors(
        [
            candidate("empty", message=" \t\n "),
            candidate("real", message="real failure"),
        ]
    )
    assert records == (
        top_error(ErrorKind.TYPE, "real failure", 1, ("file",)),
    )


def test_sort_order_is_count_then_error_kind_then_casefolded_message() -> None:
    unordered = [
        top_error(ErrorKind.TYPE, "zeta", 2),
        top_error(ErrorKind.SYNTAX, "alpha", 3),
        top_error(ErrorKind.CONFIG, "beta", 3),
        top_error(ErrorKind.TYPE, "Alpha", 2),
        top_error(ErrorKind.TYPE, "alpha", 2),
    ]

    assert sort_top_errors(unordered) == (
        top_error(ErrorKind.CONFIG, "beta", 3),
        top_error(ErrorKind.SYNTAX, "alpha", 3),
        top_error(ErrorKind.TYPE, "Alpha", 2),
        top_error(ErrorKind.TYPE, "alpha", 2),
        top_error(ErrorKind.TYPE, "zeta", 2),
    )


def test_sort_key_matches_sort_top_errors() -> None:
    records = [
        top_error(ErrorKind.TYPE, "second", 1),
        top_error(ErrorKind.IO, "first", 2),
        top_error(ErrorKind.SYNTAX, "third", 1),
    ]
    assert tuple(sorted(records, key=top_error_sort_key)) == sort_top_errors(records)


def test_validate_order_accepts_canonical_unique_records_and_returns_tuple() -> None:
    ordered = (
        top_error(ErrorKind.TYPE, "frequent", 4, ("file",)),
        top_error(ErrorKind.SYNTAX, "rare", 1, ("scenario",)),
    )
    assert validate_top_error_order(iter(ordered)) == ordered


def test_validate_order_rejects_unsorted_and_duplicate_canonical_keys() -> None:
    first = top_error(ErrorKind.TYPE, "alpha", 2)
    second = top_error(ErrorKind.TYPE, "beta", 1)

    with pytest.raises(ValueError, match="canonical order"):
        validate_top_error_order((second, first))

    duplicate_a = top_error(ErrorKind.TYPE, "Alpha", 2)
    duplicate_b = top_error(ErrorKind.TYPE, "alpha", 1)
    with pytest.raises(ValueError, match="duplicate canonical aggregation keys"):
        validate_top_error_order((duplicate_a, duplicate_b))


@pytest.mark.parametrize(
    "record",
    [
        top_error(ErrorKind.OK, "not an error", 1),
        top_error(ErrorKind.TYPE, " unnormalized ", 1),
        top_error(ErrorKind.TYPE, "type mismatch", 0),
        top_error(ErrorKind.TYPE, "type mismatch", True),
        top_error(ErrorKind.TYPE, "type mismatch", 1, ("scenario", "file")),
        top_error(ErrorKind.TYPE, "type mismatch", 1, ("file", "file")),
        top_error(ErrorKind.TYPE, "type mismatch", 1, ("module",)),
    ],
)
def test_sort_rejects_invalid_top_error_records(record: TopError) -> None:
    with pytest.raises((TypeError, ValueError)):
        sort_top_errors([record])


def test_public_functions_reject_scalar_or_wrong_element_inputs() -> None:
    with pytest.raises(TypeError, match="iterable of TopErrorCandidate"):
        bucket_top_errors("not candidates")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TopErrorCandidate"):
        bucket_top_errors([object()])  # type: ignore[list-item]
    with pytest.raises(TypeError, match="TopErrorAggregationPolicy"):
        bucket_top_errors([], policy=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="iterable of TopError"):
        sort_top_errors("not records")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TopError objects"):
        sort_top_errors([object()])  # type: ignore[list-item]


def test_optional_code_and_origin_do_not_merge_distinct_error_kinds() -> None:
    records = bucket_top_errors(
        [
            candidate(
                "a.gf",
                error_kind=ErrorKind.TYPE,
                message="same text",
                diagnostic_code="GF-TYPE-001",
                origin="compile",
            ),
            candidate(
                "b.gf",
                error_kind=ErrorKind.SYNTAX,
                message="same text",
                diagnostic_code="GF-SYNTAX-001",
                origin="scenario",
            ),
        ]
    )

    assert records == (
        top_error(ErrorKind.SYNTAX, "same text", 1, ("file",)),
        top_error(ErrorKind.TYPE, "same text", 1, ("file",)),
    )
