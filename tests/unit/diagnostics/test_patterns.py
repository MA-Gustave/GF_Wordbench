"""Unit tests for canonical diagnostic-pattern contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from gf_wordbench.diagnostics.models import (
    DiagnosticEvidence,
    DiagnosticPattern,
    DiagnosticPatternRegistry,
    DiagnosticSeverity,
    PatternConfidence,
    PatternLifecycle,
)
from gf_wordbench.diagnostics.patterns.scenarios import (
    REQUIRED_SCENARIO_MISSING_PATTERN,
    REQUIRED_SCENARIO_MISSING_PATTERN_ID,
    REQUIRED_SECTION_INCOMPLETE_PATTERN,
    REQUIRED_SECTION_INCOMPLETE_PATTERN_ID,
    SCENARIO_PATTERNS,
    canonical_scenario_patterns,
    get_scenario_pattern,
    match_required_scenario_missing,
    match_required_section_incomplete,
    scenario_pattern_facts,
)
from gf_wordbench.kernel.statuses import ErrorKind, ExecutionState


def _evidence(
    tmp_path: Path,
    *,
    operation_kind: str = "run_scenario",
    scenario_facts: dict[str, object] | None = None,
    framework_facts: dict[str, object] | None = None,
    contract_facts: dict[str, object] | None = None,
) -> DiagnosticEvidence:
    return DiagnosticEvidence(
        operation_kind=operation_kind,
        execution_state=ExecutionState.COMPLETED,
        exit_code=0,
        stdout_path=tmp_path / "stdout.bin",
        stderr_path=tmp_path / "stderr.bin",
        scenario_facts=scenario_facts or {},
        framework_facts=framework_facts or {},
        contract_facts=contract_facts or {},
    )


def _registry(
    patterns: tuple[DiagnosticPattern, ...] = SCENARIO_PATTERNS,
) -> DiagnosticPatternRegistry:
    return DiagnosticPatternRegistry(
        parser_version="1.0",
        patterns=patterns,
    )


def test_scenario_catalog_is_stable_unique_and_ordered() -> None:
    assert canonical_scenario_patterns() is SCENARIO_PATTERNS
    assert SCENARIO_PATTERNS == (
        REQUIRED_SCENARIO_MISSING_PATTERN,
        REQUIRED_SECTION_INCOMPLETE_PATTERN,
    )
    assert tuple(pattern.pattern_id for pattern in SCENARIO_PATTERNS) == (
        REQUIRED_SCENARIO_MISSING_PATTERN_ID,
        REQUIRED_SECTION_INCOMPLETE_PATTERN_ID,
    )
    assert tuple(pattern.priority for pattern in SCENARIO_PATTERNS) == (
        20,
        21,
    )
    assert len({
        pattern.pattern_id
        for pattern in SCENARIO_PATTERNS
    }) == len(SCENARIO_PATTERNS)

    for pattern in SCENARIO_PATTERNS:
        assert pattern.lifecycle_state is PatternLifecycle.ACTIVE
        assert pattern.confidence is PatternConfidence.AUTHORITATIVE
        assert pattern.severity is DiagnosticSeverity.ERROR
        assert pattern.operations == frozenset({
            "run_scenario",
            "scenario_preflight",
            "scenario_validation",
        })
        assert pattern.streams == frozenset({"framework-state"})


def test_pattern_definitions_and_evidence_metadata_are_immutable(
    tmp_path: Path,
) -> None:
    with pytest.raises(FrozenInstanceError):
        REQUIRED_SCENARIO_MISSING_PATTERN.priority = 999  # type: ignore[misc]

    evidence = _evidence(
        tmp_path,
        scenario_facts={
            "scenario_id": "smoke",
            "required": True,
        },
    )
    assert isinstance(evidence.scenario_facts, MappingProxyType)

    with pytest.raises(TypeError):
        evidence.scenario_facts["required"] = False  # type: ignore[index]


def test_registry_rejects_duplicate_ids() -> None:
    duplicate = replace(
        REQUIRED_SECTION_INCOMPLETE_PATTERN,
        pattern_id=REQUIRED_SCENARIO_MISSING_PATTERN_ID,
        supported_gf_versions=frozenset({"all"}),
        supported_platforms=frozenset({"all"}),
    )

    with pytest.raises(
        ValueError,
        match="duplicate pattern IDs",
    ):
        _registry(
            (
                REQUIRED_SCENARIO_MISSING_PATTERN,
                duplicate,
            )
        )


def test_registry_rejects_noncanonical_priority_order() -> None:
    with pytest.raises(
        ValueError,
        match="priority order",
    ):
        _registry(tuple(reversed(SCENARIO_PATTERNS)))


def test_registry_lookup_and_applicability_are_scope_aware() -> None:
    registry = _registry()

    assert registry.get(REQUIRED_SCENARIO_MISSING_PATTERN_ID) is (
        REQUIRED_SCENARIO_MISSING_PATTERN
    )
    assert registry.applicable(
        "run_scenario",
        stream="framework-state",
    ) == SCENARIO_PATTERNS
    assert registry.applicable(
        "compile_module",
        stream="framework-state",
    ) == ()
    assert registry.applicable(
        "run_scenario",
        stream="stderr",
    ) == ()

    with pytest.raises(KeyError):
        registry.get("DP-SCEN-999")


def test_registry_omits_retired_patterns() -> None:
    retired = replace(
        REQUIRED_SCENARIO_MISSING_PATTERN,
        lifecycle_state=PatternLifecycle.RETIRED,
        supported_gf_versions=frozenset({"all"}),
        supported_platforms=frozenset({"all"}),
    )
    registry = _registry(
        (
            retired,
            REQUIRED_SECTION_INCOMPLETE_PATTERN,
        )
    )

    assert registry.applicable(
        "run_scenario",
        stream="framework-state",
    ) == (REQUIRED_SECTION_INCOMPLETE_PATTERN,)


def test_required_scenario_missing_is_authoritative_framework_evidence(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        scenario_facts={
            "scenario_id": "release-smoke",
            "scenario_path": "validation/scenarios/release-smoke.gfs",
            "scenario_required": True,
            "scenario_script_exists": False,
            "scenario_script_valid": False,
        },
    )

    facts = scenario_pattern_facts(evidence)
    match = match_required_scenario_missing(evidence)

    assert facts.scenario_id == "release-smoke"
    assert facts.required is True
    assert facts.missing is True
    assert facts.existing_script is False
    assert facts.valid_script is False

    assert match is not None
    assert match.pattern_id == REQUIRED_SCENARIO_MISSING_PATTERN_ID
    assert match.operation == "run_scenario"
    assert match.stream is None
    assert match.metadata["evidence_source"] == "framework-state"
    assert match.error_kind is ErrorKind.CONFIG
    assert match.severity is DiagnosticSeverity.ERROR
    assert match.confidence is PatternConfidence.AUTHORITATIVE
    assert match.message == "Required scenario is missing."
    assert match.normalized_signature == (
        "DP-SCEN-001|release-smoke"
    )
    assert match.references == (
        "scenario:release-smoke",
        "validation/scenarios/release-smoke.gfs",
    )
    assert "script_exists=false" in match.detail
    assert "script_valid=false" in match.detail


@pytest.mark.parametrize(
    "scenario_facts",
    (
        {},
        {
            "scenario_id": "optional",
            "scenario_required": False,
            "scenario_script_exists": False,
        },
        {
            "scenario_id": "present",
            "scenario_required": True,
            "scenario_script_exists": True,
            "scenario_script_valid": True,
        },
    ),
)
def test_required_scenario_pattern_has_relevant_negative_cases(
    tmp_path: Path,
    scenario_facts: dict[str, object],
) -> None:
    assert match_required_scenario_missing(
        _evidence(
            tmp_path,
            scenario_facts=scenario_facts,
        )
    ) is None


def test_required_section_incomplete_preserves_section_identity(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        scenario_facts={
            "scenario_id": "syntax",
            "scenario_path": "validation/scenarios/syntax.gfs",
            "required_section_ids": (
                "parse",
                "linearize",
                "generate",
            ),
            "completed_section_ids": ("parse",),
            "marker_error_code": "missing-end-marker",
        },
    )

    facts = scenario_pattern_facts(evidence)
    match = match_required_section_incomplete(evidence)

    assert facts.incomplete_sections == (
        "linearize",
        "generate",
    )
    assert facts.marker_error == "missing-end-marker"

    assert match is not None
    assert match.pattern_id == REQUIRED_SECTION_INCOMPLETE_PATTERN_ID
    assert match.error_kind == "CONTRACT"
    assert match.severity is DiagnosticSeverity.ERROR
    assert match.confidence is PatternConfidence.AUTHORITATIVE
    assert match.message == (
        "Required scenario section did not complete."
    )
    assert match.normalized_signature == (
        "DP-SCEN-002|syntax|linearize"
    )
    assert match.references == (
        "scenario:syntax",
        "section:linearize",
        "validation/scenarios/syntax.gfs",
    )
    assert "section_id=linearize" in match.detail
    assert "additional_sections=generate" in match.detail
    assert "marker_error=missing-end-marker" in match.detail


def test_explicit_incomplete_flag_uses_bounded_unknown_section(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        contract_facts={
            "required_section_incomplete": True,
        },
    )

    facts = scenario_pattern_facts(evidence)
    match = match_required_section_incomplete(evidence)

    assert facts.incomplete_sections == ("unknown-section",)
    assert match is not None
    assert match.normalized_signature == (
        "DP-SCEN-002|unknown-scenario|unknown-section"
    )
    assert match.references == ("section:unknown-section",)


def test_scenario_facts_can_be_supplied_by_nested_metadata(
    tmp_path: Path,
) -> None:
    evidence = DiagnosticEvidence(
        operation_kind="scenario_validation",
        execution_state=ExecutionState.COMPLETED,
        exit_code=0,
        stdout_path=tmp_path / "stdout.bin",
        stderr_path=tmp_path / "stderr.bin",
        metadata={
            "scenario_id": "nested",
            "required": True,
            "scenario_exists": False,
        },
    )

    facts = scenario_pattern_facts(evidence)

    assert facts.scenario_id == "nested"
    assert facts.required is True
    assert facts.missing is True


def test_pattern_lookup_requires_a_canonical_known_id() -> None:
    assert get_scenario_pattern(
        REQUIRED_SECTION_INCOMPLETE_PATTERN_ID
    ) is REQUIRED_SECTION_INCOMPLETE_PATTERN

    with pytest.raises(
        KeyError,
        match="unknown scenario diagnostic pattern",
    ):
        get_scenario_pattern("DP-SCEN-999")

    with pytest.raises(
        ValueError,
        match="pattern_id",
    ):
        get_scenario_pattern(" ")
