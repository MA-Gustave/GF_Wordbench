"""Unit tests for canonical GF Wordbench release-gate contracts.

The release decision is evidence-driven: every applicable required gate must be
represented by one structured result from the same release run.  These tests
lock the policy vocabulary, gate ordering, status invariants, decision
precedence, path portability, registry behavior, and product-boundary rules
specified by ``docs/validation/RELEASE_GATES.md``.
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
import importlib
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Final, cast

import pytest

from gf_wordbench.kernel.ids import ProjectId, RunId
from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.validation.release.models import (
    RELEASE_GATE_POLICY_VERSION,
    ReleaseDecision,
    ReleaseDecisionValue,
    ReleaseGate,
    ReleaseGateApplicability,
    ReleaseGateResult,
    validate_release_gate_id,
)

_EXPECTED_GATE_IDS: Final[tuple[str, ...]] = tuple(f"RG-{index:02d}" for index in range(15))
_CONDITIONAL_GATE_IDS: Final[frozenset[str]] = frozenset({"RG-05", "RG-08", "RG-10"})
_EXPECTED_ACTIVATION_CONDITIONS: Final[dict[str, str]] = {
    "RG-05": "checkpoints_declared",
    "RG-08": "required_gold_backed_scenarios_declared",
    "RG-10": "release_requires_pgf",
}
_FIXED_TIME: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def _gate_result(
    gate_id: str,
    *,
    status: ValidationStatus = ValidationStatus.OK,
    applicability: ReleaseGateApplicability = ReleaseGateApplicability.REQUIRED,
    blockers: tuple[str, ...] | None = None,
    warnings: tuple[str, ...] = (),
    blocked_by: tuple[str, ...] = (),
    evidence_paths: tuple[Path, ...] | None = None,
    criteria_total: int | None = None,
    criteria_passed: int | None = None,
    duration_ms: int = 0,
) -> ReleaseGateResult:
    if criteria_total is None:
        criteria_total = 0 if status is ValidationStatus.SKIPPED else 1
    if criteria_passed is None:
        criteria_passed = 1 if status is ValidationStatus.OK else 0
    if blockers is None:
        blockers = (
            (f"{gate_id} did not satisfy its release criterion.",)
            if status in {ValidationStatus.FAIL, ValidationStatus.ERROR}
            else ()
        )
    if evidence_paths is None:
        evidence_paths = (Path("summary.json"),)

    return ReleaseGateResult(
        gate_id=gate_id,
        name=f"Release gate {gate_id}",
        applicability=applicability,
        status=status,
        summary=f"Structured result for {gate_id}.",
        criteria_total=criteria_total,
        criteria_passed=criteria_passed,
        blockers=blockers,
        warnings=warnings,
        evidence_paths=evidence_paths,
        blocked_by=blocked_by,
        duration_ms=duration_ms,
    )


def _decision(
    gate_results: tuple[ReleaseGateResult, ...],
    *,
    decision: ReleaseDecisionValue,
    failed_gate_ids: tuple[str, ...] = (),
    error_gate_ids: tuple[str, ...] = (),
    skipped_required_gate_ids: tuple[str, ...] = (),
    decided_at: datetime = _FIXED_TIME,
) -> ReleaseDecision:
    blocking_count = len(failed_gate_ids) + len(error_gate_ids) + len(skipped_required_gate_ids)
    required_gate_count = sum(
        result.applicability is not ReleaseGateApplicability.NOT_APPLICABLE
        for result in gate_results
    )
    passed_gate_count = required_gate_count - blocking_count

    return ReleaseDecision(
        decision=decision,
        gate_policy_version=RELEASE_GATE_POLICY_VERSION,
        project_id=ProjectId("fixture-project"),
        run_id=RunId("20260725_120000"),
        gf_wordbench_version="1.0.0",
        gf_version="3.12",
        rgl_identity="fixture-rgl",
        gate_results=gate_results,
        required_gate_count=required_gate_count,
        passed_gate_count=passed_gate_count,
        failed_gate_ids=failed_gate_ids,
        error_gate_ids=error_gate_ids,
        skipped_required_gate_ids=skipped_required_gate_ids,
        warning_count=sum(result.warning_count for result in gate_results),
        release_artifact_paths=(
            Path("summary.json"),
            Path("manifest.json"),
        ),
        decided_at=decided_at,
    )


def _registry() -> ModuleType:
    return importlib.import_module("gf_wordbench.validation.release.registry")


def test_release_gate_policy_and_vocabulary_are_canonical() -> None:
    assert RELEASE_GATE_POLICY_VERSION == "1.1.0"
    assert tuple(member.value for member in ReleaseGateApplicability) == (
        "required",
        "conditional",
        "not_applicable",
    )
    assert tuple(member.value for member in ReleaseDecisionValue) == (
        "READY",
        "NOT_READY",
        "ERROR",
    )


@pytest.mark.parametrize("gate_id", ("RG-00", "RG-07", "RG-14", "RG-99"))
def test_validate_release_gate_id_accepts_canonical_shape(gate_id: str) -> None:
    assert validate_release_gate_id(gate_id) == gate_id


@pytest.mark.parametrize(
    "gate_id",
    (
        "",
        "RG-0",
        "RG-000",
        "rg-01",
        "RC-TEST-001",
        "RG_01",
        "RG-1A",
        " RG-01",
        "RG-01 ",
        "../RG-01",
    ),
)
def test_validate_release_gate_id_rejects_noncanonical_values(
    gate_id: str,
) -> None:
    with pytest.raises(ValueError, match="RG-NN"):
        validate_release_gate_id(gate_id)


def test_validate_release_gate_id_rejects_non_string_values() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        validate_release_gate_id(1)


def test_release_gate_normalizes_text_and_preserves_numeric_order() -> None:
    gate = ReleaseGate(
        gate_id="RG-06",
        name="  Release entrypoint compilation  ",
        applicability="required",  # type: ignore[arg-type]
        owner="  Compiler and release orchestrator  ",
        order=6,
    )

    assert gate.gate_id == "RG-06"
    assert gate.name == "Release entrypoint compilation"
    assert gate.owner == "Compiler and release orchestrator"
    assert gate.applicability is ReleaseGateApplicability.REQUIRED
    assert gate.order == 6

    with pytest.raises(FrozenInstanceError):
        gate.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("order", (5, 7, -1))
def test_release_gate_rejects_an_order_that_disagrees_with_gate_id(
    order: int,
) -> None:
    with pytest.raises(ValueError, match="order"):
        ReleaseGate(
            gate_id="RG-06",
            name="Release entrypoint compilation",
            applicability=ReleaseGateApplicability.REQUIRED,
            owner="Compiler",
            order=order,
        )


def test_release_gate_rejects_boolean_order() -> None:
    with pytest.raises(TypeError, match="order must be an integer"):
        ReleaseGate(
            gate_id="RG-01",
            name="Project identity",
            applicability=ReleaseGateApplicability.REQUIRED,
            owner="Project validator",
            order=True,
        )


def test_ok_gate_result_is_complete_immutable_and_portable() -> None:
    result = _gate_result(
        "RG-13",
        warnings=("Nonblocking documentation note.",),
        evidence_paths=(
            Path("summary.json"),
            Path("details/release-gates/RG-13.json"),
        ),
        duration_ms=25,
    )

    assert result.order == 13
    assert result.warning_count == 1
    assert result.is_required is True
    assert result.is_not_applicable is False
    assert result.status is ValidationStatus.OK
    assert result.criteria_passed == result.criteria_total == 1
    assert result.blockers == ()
    assert result.blocked_by == ()
    assert tuple(path.as_posix() for path in result.evidence_paths) == (
        "summary.json",
        "details/release-gates/RG-13.json",
    )

    with pytest.raises(FrozenInstanceError):
        result.status = ValidationStatus.FAIL  # type: ignore[misc]


@pytest.mark.parametrize(
    ("status", "overrides", "message"),
    (
        (
            ValidationStatus.OK,
            {"criteria_total": 2, "criteria_passed": 1},
            "pass every criterion",
        ),
        (
            ValidationStatus.OK,
            {
                "criteria_total": 1,
                "criteria_passed": 1,
                "blockers": ("unexpected",),
            },
            "must not contain blockers",
        ),
        (
            ValidationStatus.FAIL,
            {"blockers": ()},
            "identify at least one blocker",
        ),
        (
            ValidationStatus.FAIL,
            {"criteria_total": 0, "criteria_passed": 0},
            "evaluate at least one criterion",
        ),
        (
            ValidationStatus.ERROR,
            {"blockers": ()},
            "identify at least one blocker",
        ),
        (
            ValidationStatus.SKIPPED,
            {"criteria_total": 1, "criteria_passed": 1},
            "must not report passed criteria",
        ),
    ),
)
def test_gate_result_enforces_status_specific_invariants(
    status: ValidationStatus,
    overrides: dict[str, object],
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "status": status,
        "criteria_total": 0 if status is ValidationStatus.SKIPPED else 1,
        "criteria_passed": 0,
    }
    kwargs.update(overrides)

    with pytest.raises(ValueError, match=message):
        _gate_result("RG-04", **kwargs)  # type: ignore[arg-type]


def test_not_applicable_gate_is_explicitly_skipped() -> None:
    result = _gate_result(
        "RG-10",
        status=ValidationStatus.SKIPPED,
        applicability=ReleaseGateApplicability.NOT_APPLICABLE,
        evidence_paths=(Path("details/release-gates/RG-10.json"),),
    )

    assert result.status is ValidationStatus.SKIPPED
    assert result.is_not_applicable is True
    assert result.criteria_total == 0
    assert result.criteria_passed == 0

    with pytest.raises(ValueError, match="not_applicable"):
        _gate_result(
            "RG-10",
            status=ValidationStatus.OK,
            applicability=ReleaseGateApplicability.NOT_APPLICABLE,
        )


def test_blocked_gate_records_only_prior_canonical_gate_ids() -> None:
    result = _gate_result(
        "RG-07",
        status=ValidationStatus.SKIPPED,
        blocked_by=("RG-02", "RG-06"),
    )

    assert result.blocked_by == ("RG-02", "RG-06")

    with pytest.raises(ValueError, match="cannot be blocked by itself"):
        _gate_result(
            "RG-07",
            status=ValidationStatus.SKIPPED,
            blocked_by=("RG-07",),
        )

    with pytest.raises(ValueError, match="blocked_by is valid only"):
        _gate_result(
            "RG-07",
            status=ValidationStatus.FAIL,
            blocked_by=("RG-02",),
        )

    with pytest.raises(ValueError, match="canonical gate order"):
        _gate_result(
            "RG-07",
            status=ValidationStatus.SKIPPED,
            blocked_by=("RG-06", "RG-02"),
        )


def test_gate_result_rejects_duplicate_text_and_evidence_identity() -> None:
    with pytest.raises(ValueError, match="duplicate values"):
        _gate_result(
            "RG-03",
            warnings=("same", "same"),
        )

    with pytest.raises(ValueError, match="duplicate paths"):
        _gate_result(
            "RG-03",
            evidence_paths=(Path("summary.json"), Path("summary.json")),
        )


@pytest.mark.parametrize(
    "path",
    (
        Path("../summary.json"),
        Path("details/../summary.json"),
        Path("."),
        Path("C:/release/summary.json"),
    ),
)
def test_gate_evidence_paths_must_be_normalized_and_run_relative(
    path: Path,
) -> None:
    with pytest.raises(ValueError):
        _gate_result("RG-13", evidence_paths=(path,))


def test_release_decision_ready_requires_all_required_evidence_to_pass() -> None:
    results = tuple(
        _gate_result(
            gate_id,
            applicability=(
                ReleaseGateApplicability.CONDITIONAL
                if gate_id in _CONDITIONAL_GATE_IDS
                else ReleaseGateApplicability.REQUIRED
            ),
        )
        for gate_id in _EXPECTED_GATE_IDS
    )
    local_offset = timezone(timedelta(hours=-4))

    decision = _decision(
        results,
        decision=ReleaseDecisionValue.READY,
        decided_at=datetime(2026, 7, 25, 8, 0, tzinfo=local_offset),
    )

    assert decision.decision is ReleaseDecisionValue.READY
    assert decision.is_ready is True
    assert decision.statement == "GF Wordbench release gates passed."
    assert decision.required_gate_count == 15
    assert decision.passed_gate_count == 15
    assert decision.failed_gate_ids == ()
    assert decision.error_gate_ids == ()
    assert decision.skipped_required_gate_ids == ()
    assert decision.decided_at == _FIXED_TIME
    assert decision.release_artifact_paths == (
        Path("summary.json"),
        Path("manifest.json"),
    )


def test_release_decision_uses_not_ready_for_required_failures() -> None:
    results = (
        _gate_result("RG-00"),
        _gate_result("RG-06", status=ValidationStatus.FAIL),
        _gate_result("RG-14"),
    )

    decision = _decision(
        results,
        decision=ReleaseDecisionValue.NOT_READY,
        failed_gate_ids=("RG-06",),
    )

    assert decision.is_ready is False
    assert decision.statement == "GF Wordbench release gates did not pass."
    assert decision.failed_gate_ids == ("RG-06",)


def test_release_decision_uses_error_precedence_for_gate_errors() -> None:
    results = (
        _gate_result("RG-00"),
        _gate_result("RG-02", status=ValidationStatus.ERROR),
        _gate_result("RG-06", status=ValidationStatus.FAIL),
        _gate_result("RG-14"),
    )

    decision = _decision(
        results,
        decision=ReleaseDecisionValue.ERROR,
        failed_gate_ids=("RG-06",),
        error_gate_ids=("RG-02",),
    )

    assert decision.decision is ReleaseDecisionValue.ERROR
    assert decision.statement == ("GF Wordbench could not complete the release decision reliably.")


def test_skipped_required_gate_forces_error_decision() -> None:
    results = (
        _gate_result("RG-00"),
        _gate_result(
            "RG-07",
            status=ValidationStatus.SKIPPED,
            blocked_by=("RG-02",),
        ),
        _gate_result("RG-14"),
    )

    decision = _decision(
        results,
        decision=ReleaseDecisionValue.ERROR,
        skipped_required_gate_ids=("RG-07",),
    )

    assert decision.error_gate_ids == ()
    assert decision.skipped_required_gate_ids == ("RG-07",)
    assert decision.is_ready is False


@pytest.mark.parametrize(
    ("decision", "failed", "errors", "skipped"),
    (
        (ReleaseDecisionValue.READY, ("RG-06",), (), ()),
        (ReleaseDecisionValue.NOT_READY, (), ("RG-02",), ()),
        (ReleaseDecisionValue.NOT_READY, (), (), ("RG-07",)),
        (ReleaseDecisionValue.ERROR, (), (), ()),
    ),
)
def test_release_decision_rejects_noncanonical_precedence(
    decision: ReleaseDecisionValue,
    failed: tuple[str, ...],
    errors: tuple[str, ...],
    skipped: tuple[str, ...],
) -> None:
    results = [
        _gate_result("RG-00"),
        _gate_result("RG-02"),
        _gate_result("RG-06"),
        _gate_result("RG-07"),
        _gate_result("RG-14"),
    ]
    replacements = {
        "RG-02": ValidationStatus.ERROR if "RG-02" in errors else None,
        "RG-06": ValidationStatus.FAIL if "RG-06" in failed else None,
        "RG-07": ValidationStatus.SKIPPED if "RG-07" in skipped else None,
    }
    for index, result in enumerate(results):
        replacement = replacements.get(result.gate_id)
        if replacement is None:
            continue
        results[index] = _gate_result(
            result.gate_id,
            status=replacement,
            blocked_by=("RG-02",) if replacement is ValidationStatus.SKIPPED else (),
        )

    with pytest.raises(ValueError, match="decision"):
        _decision(
            tuple(results),
            decision=decision,
            failed_gate_ids=failed,
            error_gate_ids=errors,
            skipped_required_gate_ids=skipped,
        )


def test_release_decision_requires_ordered_unique_gate_results() -> None:
    rg00 = _gate_result("RG-00")
    rg01 = _gate_result("RG-01")

    with pytest.raises(ValueError, match="strictly increasing"):
        _decision(
            (rg01, rg00),
            decision=ReleaseDecisionValue.READY,
        )

    with pytest.raises(ValueError, match="duplicate gate IDs"):
        _decision(
            (rg00, rg00),
            decision=ReleaseDecisionValue.READY,
        )


def test_release_decision_rejects_inconsistent_warning_count() -> None:
    result = _gate_result("RG-00", warnings=("review note",))

    with pytest.raises(ValueError, match="warning_count"):
        ReleaseDecision(
            decision=ReleaseDecisionValue.READY,
            gate_policy_version=RELEASE_GATE_POLICY_VERSION,
            project_id=ProjectId("fixture-project"),
            run_id=RunId("20260725_120000"),
            gf_wordbench_version="1.0.0",
            gf_version="3.12",
            rgl_identity="fixture-rgl",
            gate_results=(result,),
            required_gate_count=1,
            passed_gate_count=1,
            failed_gate_ids=(),
            error_gate_ids=(),
            skipped_required_gate_ids=(),
            warning_count=0,
            release_artifact_paths=(Path("summary.json"),),
            decided_at=_FIXED_TIME,
        )


def test_release_decision_rejects_absolute_or_traversing_artifact_paths() -> None:
    result = _gate_result("RG-00")

    for invalid in (Path("../manifest.json"), Path("C:/run/manifest.json")):
        with pytest.raises(ValueError):
            ReleaseDecision(
                decision=ReleaseDecisionValue.READY,
                gate_policy_version=RELEASE_GATE_POLICY_VERSION,
                project_id=ProjectId("fixture-project"),
                run_id=RunId("20260725_120000"),
                gf_wordbench_version="1.0.0",
                gf_version="3.12",
                rgl_identity="fixture-rgl",
                gate_results=(result,),
                required_gate_count=1,
                passed_gate_count=1,
                failed_gate_ids=(),
                error_gate_ids=(),
                skipped_required_gate_ids=(),
                warning_count=0,
                release_artifact_paths=(invalid,),
                decided_at=_FIXED_TIME,
            )


def test_release_registry_imports_cleanly_and_is_canonical() -> None:
    registry = _registry()

    assert registry.GATE_POLICY_VERSION == RELEASE_GATE_POLICY_VERSION
    assert registry.CANONICAL_RELEASE_GATE_IDS == _EXPECTED_GATE_IDS
    assert tuple(gate.gate_id for gate in registry.CANONICAL_RELEASE_GATES) == (_EXPECTED_GATE_IDS)
    assert tuple(registry.iter_release_gates()) == (registry.CANONICAL_RELEASE_GATES)
    assert tuple(registry.CANONICAL_RELEASE_GATE_BY_ID) == _EXPECTED_GATE_IDS
    assert isinstance(registry.CANONICAL_RELEASE_GATE_BY_ID, MappingProxyType)

    with pytest.raises(TypeError):
        mutable_registry = cast(
            MutableMapping[str, object],
            registry.CANONICAL_RELEASE_GATE_BY_ID,
        )
        mutable_registry["RG-99"] = object()


def test_release_registry_preserves_conditional_activation_and_decision_phase() -> None:
    registry = _registry()

    conditionals = {
        gate.gate_id: gate
        for gate in registry.CANONICAL_RELEASE_GATES
        if gate.applicability is registry.ReleaseGateApplicability.CONDITIONAL
    }
    assert set(conditionals) == _CONDITIONAL_GATE_IDS
    assert {
        gate_id: gate.activation_condition for gate_id, gate in conditionals.items()
    } == _EXPECTED_ACTIVATION_CONDITIONS

    decision = registry.decision_gate_definition()
    assert decision.gate_id == "RG-14"
    assert decision.phase is registry.ReleaseGatePhase.DECISION
    assert all(
        gate.phase is registry.ReleaseGatePhase.EVALUATION
        for gate in registry.evaluation_gate_definitions()
    )


def test_release_registry_activates_conditional_gates_only_from_typed_conditions() -> None:
    registry = _registry()
    all_active = registry.active_release_gates(
        {
            "checkpoints_declared": True,
            "required_gold_backed_scenarios_declared": True,
            "release_requires_pgf": True,
        },
        include_decision_gate=True,
    )
    none_active = registry.active_release_gates(
        {
            "checkpoints_declared": False,
            "required_gold_backed_scenarios_declared": False,
            "release_requires_pgf": False,
        },
        include_decision_gate=False,
    )

    assert tuple(gate.gate_id for gate in all_active) == _EXPECTED_GATE_IDS
    assert not (_CONDITIONAL_GATE_IDS & {gate.gate_id for gate in none_active})
    assert "RG-14" not in {gate.gate_id for gate in none_active}
    assert tuple(
        gate.gate_id
        for gate in registry.inactive_conditional_gates(
            {
                "checkpoints_declared": False,
                "required_gold_backed_scenarios_declared": False,
                "release_requires_pgf": False,
            }
        )
    ) == ("RG-05", "RG-08", "RG-10")

    with pytest.raises(TypeError, match="bool"):
        registry.active_release_gates(
            {"release_requires_pgf": "yes"},
        )


def test_project_release_gate_extensions_are_explicit_and_append_only() -> None:
    registry = _registry()
    extension = registry.ReleaseGateDefinition(
        gate_id="RC-TEST-001",
        name="Project-specific release criterion",
        applicability=registry.ReleaseGateApplicability.REQUIRED,
        owner="Project release policy",
        purpose="Prove one explicit project-owned release requirement.",
    )

    combined = registry.build_release_gate_registry((extension,))
    indexed = registry.index_release_gate_registry(combined)

    assert combined[:-1] == registry.CANONICAL_RELEASE_GATES
    assert combined[-1] is extension
    assert indexed[extension.gate_id] is extension

    with pytest.raises(ValueError):
        registry.validate_release_gate_registry(
            (*combined, extension),
            require_canonical_prefix=True,
        )

    with pytest.raises(TypeError):
        registry.build_release_gate_registry("RC-TEST-001")


def test_release_submodules_import_as_one_coherent_public_contract() -> None:
    for module_name in (
        "gf_wordbench.validation.release.models",
        "gf_wordbench.validation.release.registry",
        "gf_wordbench.validation.release.evaluator",
        "gf_wordbench.validation.release.decision",
    ):
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_release_package_has_no_portfolio_or_entrypoint_dependency() -> None:
    package = importlib.import_module("gf_wordbench.validation.release")
    package_file = package.__file__
    assert package_file is not None
    package_root = Path(package_file).resolve().parent
    forbidden_prefixes = (
        "gf_portfolio",
        "gf_wordbench.entrypoints",
    )
    violations: list[tuple[str, str]] = []

    for source_path in sorted(package_root.glob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        for node in ast.walk(tree):
            imported: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported = (node.module or "",)

            for module_name in imported:
                if module_name.startswith(forbidden_prefixes):
                    violations.append((source_path.name, module_name))

    assert violations == []
