"""Unit tests for multiline grouping and diagnostic-pattern matching."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticPattern,
    DiagnosticSeverity,
    DiagnosticStream,
    PatternConfidence,
    PatternLifecycle,
    PatternMatch,
    PatternMatcher,
)
from gf_wordbench.diagnostics.parsing.matcher import (
    MatcherWarningCode,
    MatchStrictness,
    PatternContractError,
    PatternExecutionError,
    diagnostic_match_key,
    iter_applicable_patterns,
    match_diagnostic_patterns,
    match_one_pattern,
    pattern_applicability,
    prepare_pattern_order,
    validate_pattern_registry_order,
)
from gf_wordbench.diagnostics.parsing.multiline import (
    ClassifiedLine,
    CloseReason,
    LineRole,
    MultilineLimits,
    MultilineWarningCode,
    group_multiline_diagnostics,
)
from gf_wordbench.kernel.statuses import ErrorKind, ExecutionState


def _line(
    number: int,
    text: str,
    role: LineRole,
    *,
    pattern_id: str | None = None,
    precedence: int | None = None,
    terminates: bool = False,
    max_continuation_lines: int | None = None,
    max_characters: int | None = None,
) -> ClassifiedLine:
    return ClassifiedLine(
        line_number=number,
        text=text,
        role=role,
        pattern_id=pattern_id,
        precedence=precedence,
        terminates=terminates,
        max_continuation_lines=max_continuation_lines,
        max_characters=max_characters,
    )


def _start(
    number: int,
    text: str = "Error: invalid expression",
    *,
    pattern_id: str = "DP-TEST-001",
    precedence: int = 20,
    terminates: bool = False,
    max_continuation_lines: int | None = None,
    max_characters: int | None = None,
) -> ClassifiedLine:
    return _line(
        number,
        text,
        LineRole.DIAGNOSTIC_START,
        pattern_id=pattern_id,
        precedence=precedence,
        terminates=terminates,
        max_continuation_lines=max_continuation_lines,
        max_characters=max_characters,
    )


def _evidence(
    *,
    operation: str = "compile_module",
    stream: DiagnosticStream | str | None = DiagnosticStream.STDERR,
    platform: str | None = "windows",
    gf_version: str | None = "3.12",
) -> DiagnosticEvidence:
    return DiagnosticEvidence(
        operation_kind=operation,
        execution_state=ExecutionState.COMPLETED,
        exit_code=1,
        stdout_path=Path("stdout.txt"),
        stderr_path=Path("stderr.txt"),
        stdout_text="",
        stderr_text="Error: invalid expression",
        stream=stream,
        raw_path=(
            Path("stderr.txt")
            if stream in (DiagnosticStream.STDERR, "stderr")
            else Path("stdout.txt")
            if stream in (DiagnosticStream.STDOUT, "stdout")
            else None
        ),
        text="Error: invalid expression" if stream is not None else None,
        platform=platform,
        gf_version=gf_version,
    )


def _match(
    *,
    pattern_id: str = "DP-TEST-001",
    stream: DiagnosticStream | str = DiagnosticStream.STDERR,
    start_line: int = 4,
    end_line: int = 5,
    signature: str = "syntax|invalid-expression",
    message: str = "Invalid expression.",
) -> PatternMatch:
    return PatternMatch(
        pattern_id=pattern_id,
        operation="compile_module",
        stream=stream,
        start_line=start_line,
        end_line=end_line,
        severity=DiagnosticSeverity.ERROR,
        error_kind=ErrorKind.SYNTAX,
        message=message,
        confidence=PatternConfidence.EXACT,
        raw_excerpt="Error: invalid expression",
        normalized_signature=signature,
    )


def _pattern(
    *,
    pattern_id: str = "DP-TEST-001",
    priority: int = 20,
    matcher: PatternMatcher | None = None,
    operations: frozenset[str] = frozenset({"compile_module"}),
    streams: frozenset[str] = frozenset({"stderr"}),
    lifecycle: PatternLifecycle = PatternLifecycle.ACTIVE,
    platforms: frozenset[str] = frozenset({"windows"}),
    versions: frozenset[str] = frozenset({"3"}),
) -> DiagnosticPattern:
    selected_matcher: PatternMatcher = (
        matcher
        if matcher is not None
        else lambda evidence: _match(pattern_id=pattern_id)
    )
    return DiagnosticPattern(
        pattern_id=pattern_id,
        operations=operations,
        streams=streams,
        priority=priority,
        confidence=PatternConfidence.EXACT,
        error_kind=ErrorKind.SYNTAX,
        severity=DiagnosticSeverity.ERROR,
        matcher=selected_matcher,
        lifecycle_state=lifecycle,
        supported_gf_versions=versions,
        supported_platforms=platforms,
    )


def test_multiline_grouping_builds_one_complete_record() -> None:
    result = group_multiline_diagnostics(
        (
            _start(2),
            _line(
                3,
                "  in expression f x",
                LineRole.DIAGNOSTIC_CONTINUATION,
                pattern_id="DP-TEST-001",
            ),
            _line(4, "  context: Main.gf", LineRole.CONTEXT),
        )
    )

    assert len(result.blocks) == 1
    block = result.blocks[0]
    assert block.pattern_id == "DP-TEST-001"
    assert block.start_line == 2
    assert block.end_line == 4
    assert block.lines == (
        "Error: invalid expression",
        "  in expression f x",
        "  context: Main.gf",
    )
    assert block.continuation_lines == 2
    assert block.character_count == len(block.raw_excerpt)
    assert block.close_reason is CloseReason.STREAM_END
    assert block.truncated is False
    assert block.incomplete is False
    assert result.unclaimed_lines == ()
    assert result.warnings == ()
    assert result.consumed_line_count == 3
    assert (
        result.consumed_character_count
        == sum(
            len(line)
            for line in (
                "Error: invalid expression",
                "  in expression f x",
                "  context: Main.gf",
            )
        )
        + 2
    )
    assert result.stopped_early is False


def test_new_start_closes_open_record_by_relative_precedence() -> None:
    result = group_multiline_diagnostics(
        (
            _start(1, pattern_id="DP-TEST-010", precedence=20),
            _start(2, pattern_id="DP-TEST-020", precedence=30),
            _start(3, pattern_id="DP-TEST-030", precedence=10),
        )
    )

    assert [block.close_reason for block in result.blocks] == [
        CloseReason.NEW_DIAGNOSTIC_START,
        CloseReason.HIGHER_PRECEDENCE_START,
        CloseReason.STREAM_END,
    ]
    assert [block.pattern_id for block in result.blocks] == [
        "DP-TEST-010",
        "DP-TEST-020",
        "DP-TEST-030",
    ]


def test_explicit_termination_closes_start_or_continuation() -> None:
    result = group_multiline_diagnostics(
        (
            _start(1, pattern_id="DP-TEST-010", terminates=True),
            _start(2, pattern_id="DP-TEST-020"),
            _line(
                3,
                "done",
                LineRole.DIAGNOSTIC_CONTINUATION,
                pattern_id="DP-TEST-020",
                terminates=True,
            ),
        )
    )

    assert [block.close_reason for block in result.blocks] == [
        CloseReason.EXPLICIT_TERMINATION,
        CloseReason.EXPLICIT_TERMINATION,
    ]


def test_orphan_continuation_and_context_are_preserved() -> None:
    continuation = _line(
        1,
        "continued",
        LineRole.DIAGNOSTIC_CONTINUATION,
    )
    context = _line(2, "context", LineRole.CONTEXT)

    result = group_multiline_diagnostics((continuation, context))

    assert result.blocks == ()
    assert result.unclaimed_lines == (continuation, context)
    assert [warning.code for warning in result.warnings] == [
        MultilineWarningCode.ORPHAN_CONTINUATION,
        MultilineWarningCode.ORPHAN_CONTEXT,
    ]


def test_pattern_mismatch_closes_record_and_preserves_line() -> None:
    mismatched = _line(
        2,
        "foreign continuation",
        LineRole.DIAGNOSTIC_CONTINUATION,
        pattern_id="DP-TEST-999",
    )

    result = group_multiline_diagnostics((_start(1), mismatched))

    assert result.blocks[0].close_reason is CloseReason.NON_CONTINUATION_BOUNDARY
    assert result.unclaimed_lines == (mismatched,)
    assert result.warnings[0].code is MultilineWarningCode.PATTERN_MISMATCH


def test_continuation_limit_marks_record_truncated() -> None:
    overflow = _line(3, "second continuation", LineRole.CONTEXT)
    result = group_multiline_diagnostics(
        (
            _start(1, max_continuation_lines=1),
            _line(2, "first continuation", LineRole.CONTEXT),
            overflow,
        )
    )

    block = result.blocks[0]
    assert block.lines == (
        "Error: invalid expression",
        "first continuation",
    )
    assert block.close_reason is CloseReason.CONTINUATION_LIMIT
    assert block.truncated is True
    assert block.incomplete is True
    assert result.unclaimed_lines == (overflow,)
    assert result.warnings[0].code is MultilineWarningCode.CONTINUATION_LIMIT_REACHED


def test_character_limits_apply_to_start_and_continuation() -> None:
    start_truncated = group_multiline_diagnostics((_start(1, text="abcdefgh", max_characters=4),))
    assert start_truncated.blocks[0].lines == ("abcd",)
    assert start_truncated.blocks[0].close_reason is CloseReason.CHARACTER_LIMIT
    assert start_truncated.blocks[0].truncated is True

    overflow = _line(2, "def", LineRole.CONTEXT)
    continuation_truncated = group_multiline_diagnostics(
        (
            _start(1, text="abc", max_characters=5),
            overflow,
        )
    )
    assert continuation_truncated.blocks[0].lines == ("abc",)
    assert continuation_truncated.blocks[0].close_reason is CloseReason.CHARACTER_LIMIT
    assert continuation_truncated.unclaimed_lines == (overflow,)
    assert continuation_truncated.warnings[0].code is MultilineWarningCode.CHARACTER_LIMIT_REACHED


def test_record_and_total_character_limits_stop_deterministically() -> None:
    record_limited = group_multiline_diagnostics(
        (
            _start(1, pattern_id="DP-TEST-010"),
            _start(2, pattern_id="DP-TEST-020"),
        ),
        limits=MultilineLimits(max_records=1),
    )
    assert record_limited.stopped_early is True
    assert len(record_limited.blocks) == 1
    assert record_limited.blocks[0].close_reason is CloseReason.RECORD_LIMIT
    assert record_limited.warnings[0].code is MultilineWarningCode.RECORD_LIMIT_REACHED

    total_limited = group_multiline_diagnostics(
        (
            _start(1, text="abc"),
            _line(2, "def", LineRole.CONTEXT),
        ),
        limits=MultilineLimits(max_total_characters=5),
    )
    assert total_limited.stopped_early is True
    assert total_limited.consumed_line_count == 1
    assert total_limited.consumed_character_count == 3
    assert total_limited.blocks[0].close_reason is CloseReason.TOTAL_CHARACTER_LIMIT
    assert total_limited.warnings[0].code is MultilineWarningCode.TOTAL_CHARACTER_LIMIT_REACHED


def test_stream_truncation_marks_open_record_and_emits_warning() -> None:
    result = group_multiline_diagnostics(
        (_start(1),),
        stream_truncated=True,
    )

    assert result.stream_truncated is True
    assert result.blocks[0].close_reason is CloseReason.STREAM_TRUNCATED
    assert result.blocks[0].truncated is True
    assert result.blocks[0].incomplete is True
    assert result.warnings[-1].code is MultilineWarningCode.STREAM_TRUNCATED


def test_multiline_input_contracts_are_enforced() -> None:
    with pytest.raises(TypeError, match="iterable"):
        group_multiline_diagnostics("not-lines")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ClassifiedLine"):
        group_multiline_diagnostics((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="strictly increasing"):
        group_multiline_diagnostics((_start(2), _start(1)))
    with pytest.raises(ValueError, match="diagnostic starts require pattern_id"):
        _line(1, "error", LineRole.DIAGNOSTIC_START, precedence=10)
    with pytest.raises(ValueError, match="valid only on diagnostic starts"):
        _line(1, "context", LineRole.CONTEXT, max_characters=10)


def test_pattern_order_is_stable_and_duplicate_ids_are_rejected() -> None:
    first = _pattern(pattern_id="DP-TEST-010", priority=20)
    second = _pattern(pattern_id="DP-TEST-020", priority=10)
    third = _pattern(pattern_id="DP-TEST-030", priority=20)

    assert prepare_pattern_order((first, second, third)) == (
        second,
        first,
        third,
    )
    assert validate_pattern_registry_order((second, first, third)) == (
        "DP-TEST-020",
        "DP-TEST-010",
        "DP-TEST-030",
    )

    with pytest.raises(PatternContractError, match="canonical precedence order"):
        validate_pattern_registry_order((first, second, third))
    with pytest.raises(PatternContractError, match="duplicate diagnostic pattern ID"):
        prepare_pattern_order((first, replace(first, priority=99)))
    with pytest.raises(TypeError, match="iterable"):
        prepare_pattern_order("DP-TEST-010")


def test_pattern_applicability_checks_every_declared_scope() -> None:
    pattern = _pattern()

    assert pattern_applicability(pattern, _evidence()).applicable is True
    assert (
        pattern_applicability(
            pattern,
            _evidence(operation="build_pgf"),
        ).applicable
        is False
    )
    assert (
        pattern_applicability(
            pattern,
            _evidence(stream=DiagnosticStream.STDOUT),
        ).applicable
        is False
    )
    assert (
        pattern_applicability(
            pattern,
            _evidence(platform="linux"),
        ).applicable
        is False
    )
    assert (
        pattern_applicability(
            pattern,
            _evidence(gf_version="4.0"),
        ).applicable
        is False
    )


def test_unknown_compatibility_data_skips_pattern_with_warning() -> None:
    pattern = _pattern()

    missing_platform = pattern_applicability(
        pattern,
        _evidence(platform=None),
    )
    assert missing_platform.applicable is False
    assert missing_platform.warning is not None
    assert missing_platform.warning.code is MatcherWarningCode.COMPATIBILITY_UNKNOWN

    missing_version = pattern_applicability(
        pattern,
        _evidence(gf_version=None),
    )
    assert missing_version.applicable is False
    assert missing_version.warning is not None
    assert missing_version.warning.code is MatcherWarningCode.COMPATIBILITY_UNKNOWN


def test_lifecycle_controls_matching_and_warning_classification() -> None:
    evidence = _evidence()

    retired = pattern_applicability(
        _pattern(lifecycle=PatternLifecycle.RETIRED),
        evidence,
    )
    assert retired.applicable is False
    assert retired.warning is not None
    assert retired.warning.code is MatcherWarningCode.PATTERN_SKIPPED

    deprecated = pattern_applicability(
        _pattern(lifecycle=PatternLifecycle.DEPRECATED),
        evidence,
    )
    assert deprecated.applicable is True
    assert deprecated.warning is not None
    assert deprecated.warning.code is MatcherWarningCode.PATTERN_DEPRECATED

    experimental = pattern_applicability(
        _pattern(lifecycle=PatternLifecycle.EXPERIMENTAL),
        evidence,
    )
    assert experimental.applicable is True
    assert experimental.warning is not None
    assert experimental.warning.code is MatcherWarningCode.PATTERN_EXPERIMENTAL


def test_match_one_pattern_normalizes_none_single_and_iterable_results() -> None:
    evidence = _evidence()
    match = _match()

    assert match_one_pattern(_pattern(matcher=lambda value: None), evidence) == ()
    assert match_one_pattern(_pattern(matcher=lambda value: match), evidence) == (match,)
    assert match_one_pattern(
        _pattern(matcher=lambda value: [match]),
        evidence,
    ) == (match,)

    with pytest.raises(PatternContractError, match="unsupported match value"):
        match_one_pattern(_pattern(matcher=lambda value: "invalid"), evidence)
    with pytest.raises(PatternContractError, match="returned None inside"):
        match_one_pattern(_pattern(matcher=lambda value: [None]), evidence)


def test_matcher_execution_failures_keep_pattern_context() -> None:
    def fail(_: DiagnosticEvidence) -> PatternMatch:
        raise OSError("parser unavailable\nsecret second line")

    with pytest.raises(PatternExecutionError) as captured:
        match_one_pattern(_pattern(matcher=fail), _evidence())

    message = str(captured.value)
    assert "DP-TEST-001" in message
    assert "OSError" in message
    assert "parser unavailable secret second line" in message


def test_matching_orders_patterns_and_deduplicates_semantic_matches() -> None:
    duplicate = _match(pattern_id="DP-TEST-010")
    stderr_variant = _match(
        pattern_id="DP-TEST-030",
        stream=DiagnosticStream.STDERR,
    )
    stdout_variant = _match(
        pattern_id="DP-TEST-030",
        stream=DiagnosticStream.STDOUT,
    )
    patterns = (
        _pattern(
            pattern_id="DP-TEST-020",
            priority=20,
            matcher=lambda value: _match(pattern_id="DP-TEST-020"),
        ),
        _pattern(
            pattern_id="DP-TEST-010",
            priority=10,
            matcher=lambda value: (duplicate, duplicate),
        ),
        _pattern(
            pattern_id="DP-TEST-030",
            priority=30,
            matcher=lambda value: (stderr_variant, stdout_variant),
            streams=frozenset({"stderr", "stdout"}),
        ),
    )

    batch = match_diagnostic_patterns(patterns, _evidence())

    assert batch.attempted_pattern_ids == (
        "DP-TEST-010",
        "DP-TEST-020",
        "DP-TEST-030",
    )
    assert len(batch.matches) == 4
    assert batch.matches[0] is duplicate
    assert stdout_variant in batch.matches
    assert batch.complete is True
    assert [warning.code for warning in batch.warnings] == [MatcherWarningCode.DUPLICATE_MATCH]


def test_invalid_match_is_warning_in_tolerant_mode_and_error_in_strict_mode() -> None:
    invalid = SimpleNamespace(
        pattern_id="DP-OTHER-001",
        stream="stderr",
        start_line=1,
        end_line=1,
        message="invalid",
        normalized_signature="invalid",
    )
    pattern = _pattern(matcher=lambda value: invalid)

    tolerant = match_diagnostic_patterns(patterns=(pattern,), evidence=_evidence())
    assert tolerant.matches == ()
    assert tolerant.complete is False
    assert tolerant.warnings[0].code is MatcherWarningCode.INVALID_MATCH

    with pytest.raises(PatternExecutionError, match="returned an invalid match"):
        match_diagnostic_patterns(
            patterns=(pattern,),
            evidence=_evidence(),
            strictness=MatchStrictness.STRICT,
        )


def test_match_limit_returns_finite_incomplete_batch() -> None:
    matches = tuple(
        _match(
            start_line=index,
            end_line=index,
            signature=f"signature-{index}",
        )
        for index in range(1, 4)
    )

    batch = match_diagnostic_patterns(
        (_pattern(matcher=lambda value: matches),),
        _evidence(),
        max_matches=2,
    )

    assert batch.matches == matches[:2]
    assert batch.complete is False
    assert batch.warnings[-1].code is MatcherWarningCode.MATCH_LIMIT_REACHED


def test_match_key_prefers_signature_and_preserves_stream_provenance() -> None:
    stderr = _match(stream=DiagnosticStream.STDERR, signature="stable")
    stdout = _match(stream=DiagnosticStream.STDOUT, signature="stable")
    message_only = SimpleNamespace(
        pattern_id="DP-TEST-001",
        stream="stderr",
        start_line=4,
        end_line=5,
        message="Fallback identity",
    )

    assert diagnostic_match_key(stderr) == (
        "stderr",
        4,
        5,
        "DP-TEST-001",
        "stable",
    )
    assert diagnostic_match_key(stderr) != diagnostic_match_key(stdout)
    assert diagnostic_match_key(message_only)[-1] == "Fallback identity"


def test_iter_applicable_patterns_returns_canonical_subset() -> None:
    applicable = _pattern(pattern_id="DP-TEST-020", priority=20)
    skipped = _pattern(
        pattern_id="DP-TEST-010",
        priority=10,
        operations=frozenset({"build_pgf"}),
    )
    later = _pattern(pattern_id="DP-TEST-030", priority=30)

    assert tuple(
        iter_applicable_patterns(
            (later, applicable, skipped),
            _evidence(),
        )
    ) == (applicable, later)


def test_matcher_rejects_causal_classification_from_pattern_output() -> None:
    invalid = SimpleNamespace(
        pattern_id="DP-TEST-001",
        stream="stderr",
        start_line=1,
        end_line=1,
        message="Invalid expression.",
        normalized_signature="syntax|invalid",
        diagnostic_class="direct",
    )

    batch = match_diagnostic_patterns(
        (_pattern(matcher=lambda value: invalid),),
        _evidence(),
    )

    assert batch.matches == ()
    assert batch.complete is False
    assert batch.warnings[0].code is MatcherWarningCode.INVALID_MATCH
    assert "causal field" in batch.warnings[0].message
