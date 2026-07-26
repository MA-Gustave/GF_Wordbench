"""Contract tests for GF Wordbench validation ownership and semantics."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import pytest

import gf_wordbench.validation as validation_package
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.validation.pipeline import (
    PipelineStageResult,
    ValidationPipelinePlan,
    ValidationStageClass,
    ValidationStageId,
    aggregate_pipeline_status,
)
from gf_wordbench.validation.stage_contracts import (
    CANONICAL_STAGE_IDS,
    STAGE_CONTRACTS,
    STAGE_REGISTRY,
    StageEffect,
    StageFailurePolicy,
    StageId,
    StageOwner,
    StageRequirement,
    canonical_stage_ids,
    get_stage_contract,
    get_stage_requirement,
)

pytestmark = pytest.mark.contract

_CANONICAL_MODE_NAMES: Final = (
    "quick",
    "checkpoint",
    "release",
    "diagnostic",
)
_CANONICAL_STAGE_NAMES: Final = (
    "configuration",
    "environment",
    "version_probe",
    "selection",
    "static_scan",
    "fingerprint",
    "compile_files",
    "compile_checkpoints",
    "compile_entrypoints",
    "build_pgf",
    "run_scenarios",
    "normalize_outputs",
    "evaluate_assertions",
    "compare_gold",
    "classify_failures",
    "compare_previous",
    "evaluate_release_gates",
    "write_reports",
    "write_manifest",
    "verify_manifest",
)
_PROCESS_BACKED_STAGES: Final = {
    StageId.VERSION_PROBE,
    StageId.COMPILE_FILES,
    StageId.COMPILE_CHECKPOINTS,
    StageId.COMPILE_ENTRYPOINTS,
    StageId.BUILD_PGF,
    StageId.RUN_SCENARIOS,
}


def _package_dir() -> Path:
    return Path(validation_package.__file__ or "").parent


def _module_tree(relative_path: str) -> ast.Module:
    path = _package_dir() / relative_path
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _assigned_value(tree: ast.Module, name: str) -> ast.expr:
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            return node.value
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    raise AssertionError(f"missing assignment {name}")


def _string_tuple(node: ast.expr) -> tuple[str, ...]:
    assert isinstance(node, (ast.Tuple, ast.List))
    values: list[str] = []
    for element in node.elts:
        assert isinstance(element, ast.Constant)
        assert isinstance(element.value, str)
        values.append(element.value)
    return tuple(values)


def _attribute_tuple(node: ast.expr, owner: str) -> tuple[str, ...]:
    assert isinstance(node, (ast.Tuple, ast.List))
    values: list[str] = []
    for element in node.elts:
        assert isinstance(element, ast.Attribute)
        assert isinstance(element.value, ast.Name)
        assert element.value.id == owner
        values.append(element.attr)
    return tuple(values)


def _policy_keywords(tree: ast.Module, name: str) -> dict[str, ast.expr]:
    value = _assigned_value(tree, name)
    assert isinstance(value, ast.Call)
    assert isinstance(value.func, ast.Name)
    assert value.func.id == "ModePolicy"
    return {keyword.arg: keyword.value for keyword in value.keywords if keyword.arg}


def _keyword_bool(keywords: dict[str, ast.expr], name: str) -> bool:
    value = ast.literal_eval(keywords[name])
    assert isinstance(value, bool)
    return value


def _keyword_string(keywords: dict[str, ast.expr], name: str) -> str:
    value = ast.literal_eval(keywords[name])
    assert isinstance(value, str)
    return value


def _conditional_stages(node: ast.expr) -> tuple[tuple[str, str], ...]:
    assert isinstance(node, (ast.Tuple, ast.List))
    resolved: list[tuple[str, str]] = []
    for element in node.elts:
        assert isinstance(element, ast.Call)
        assert isinstance(element.func, ast.Name)
        assert element.func.id == "ConditionalStage"
        keywords = {item.arg: item.value for item in element.keywords if item.arg}
        stage = ast.literal_eval(keywords["stage"])
        condition = ast.literal_eval(keywords["condition"])
        assert isinstance(stage, str)
        assert isinstance(condition, str)
        resolved.append((stage, condition))
    return tuple(resolved)


def _pipeline_result(
    status: ValidationStatus,
    *,
    required: bool,
    error_kind: ErrorKind | None = None,
) -> PipelineStageResult:
    resolved_error = error_kind
    if resolved_error is None:
        resolved_error = (
            ErrorKind.OK
            if status in {ValidationStatus.OK, ValidationStatus.SKIPPED}
            else ErrorKind.OTHER
        )
    timestamp = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    return PipelineStageResult(
        stage_id=ValidationStageId.SELECT,
        stage_name="Select validation subjects",
        stage_class=ValidationStageClass.INVENTORY,
        required=required,
        started_at=timestamp,
        finished_at=timestamp,
        duration_ms=0,
        validation_status=status,
        execution_state=None,
        error_kind=resolved_error,
        message="contract result",
    )


def test_validation_modes_module_imports_in_a_fresh_interpreter() -> None:
    environment = dict(os.environ)
    source_root = str(_package_dir().parents[1])
    current_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not current_pythonpath
        else os.pathsep.join((source_root, current_pythonpath))
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from gf_wordbench.validation.modes import MODE_POLICIES; "
            "assert len(MODE_POLICIES) == 4",
        ],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_validation_mode_vocabulary_is_exact_and_canonical() -> None:
    tree = _module_tree("modes.py")
    assert tuple(mode.value for mode in ValidationMode) == _CANONICAL_MODE_NAMES
    assert _attribute_tuple(
        _assigned_value(tree, "CANONICAL_VALIDATION_MODES"),
        "ValidationMode",
    ) == ("QUICK", "CHECKPOINT", "RELEASE", "DIAGNOSTIC")
    assert _string_tuple(
        _assigned_value(tree, "CANONICAL_VALIDATION_STAGES")
    ) == _CANONICAL_STAGE_NAMES


def test_legacy_mode_aliases_are_migration_only() -> None:
    tree = _module_tree("modes.py")
    aliases = _assigned_value(tree, "LEGACY_VALIDATION_MODE_ALIASES")
    assert isinstance(aliases, ast.Dict)
    resolved: dict[str, str] = {}
    for key, value in zip(aliases.keys, aliases.values, strict=True):
        assert isinstance(key, ast.Constant)
        assert isinstance(key.value, str)
        assert isinstance(value, ast.Attribute)
        assert isinstance(value.value, ast.Name)
        assert value.value.id == "ValidationMode"
        resolved[key.value] = value.attr
    assert resolved == {"file": "QUICK", "all": "DIAGNOSTIC"}


def test_mode_policies_preserve_distinct_intents() -> None:
    tree = _module_tree("modes.py")
    quick = _policy_keywords(tree, "_QUICK_POLICY")
    checkpoint = _policy_keywords(tree, "_CHECKPOINT_POLICY")
    release = _policy_keywords(tree, "_RELEASE_POLICY")
    diagnostic = _policy_keywords(tree, "_DIAGNOSTIC_POLICY")

    assert _keyword_string(quick, "evidence_policy") == "bounded"
    assert _keyword_bool(quick, "target_required")
    assert not _keyword_bool(quick, "release_eligible")
    assert _string_tuple(quick["allowed_target_kinds"]) == (
        "file",
        "module",
        "entrypoint",
        "scenario",
    )

    assert _keyword_string(checkpoint, "evidence_policy") == "standard"
    assert _keyword_bool(checkpoint, "target_required")
    assert _string_tuple(checkpoint["allowed_target_kinds"]) == ("checkpoint",)

    assert _keyword_string(release, "evidence_policy") == "complete"
    assert _keyword_bool(release, "release_eligible")
    assert _keyword_bool(release, "full_project_scope")
    assert _string_tuple(release["allowed_target_kinds"]) == ("project",)

    assert _keyword_string(diagnostic, "evidence_policy") == "expanded"
    assert _keyword_bool(diagnostic, "continue_after_independent_failure")
    assert not _keyword_bool(diagnostic, "release_eligible")


def test_release_policy_requires_final_decision_and_artifact_verification() -> None:
    tree = _module_tree("modes.py")
    release = _policy_keywords(tree, "_RELEASE_POLICY")
    required = set(_string_tuple(release["required_stages"]))
    assert {
        "evaluate_release_gates",
        "write_reports",
        "write_manifest",
        "verify_manifest",
    }.issubset(required)
    assert _conditional_stages(release["conditional_stages"]) == (
        ("build_pgf", "release_requires_pgf"),
        ("compare_previous", "compatible_history_exists"),
    )
    assert {
        "target",
        "skip_version_probe",
        "no_compile",
        "skip_required_scenarios",
        "skip_required_gold",
        "skip_required_pgf",
        "skip_manifest",
        "ignore_blocking_issues",
    }.issubset(_string_tuple(release["prohibited_overrides"]))


def test_quick_scenario_policy_activates_scenario_evidence_chain() -> None:
    tree = _module_tree("modes.py")
    quick = _policy_keywords(tree, "_QUICK_POLICY")
    assert _conditional_stages(quick["conditional_stages"]) == (
        ("run_scenarios", "target_is_scenario"),
        ("normalize_outputs", "target_is_scenario"),
        ("evaluate_assertions", "target_is_scenario"),
        ("compare_gold", "gold_comparison_required"),
    )


def test_semantic_stage_vocabulary_has_one_canonical_order() -> None:
    assert tuple(stage.value for stage in StageId) == _CANONICAL_STAGE_NAMES
    assert CANONICAL_STAGE_IDS == tuple(StageId)
    assert canonical_stage_ids() == tuple(StageId)


def test_stage_registry_is_complete_unique_and_contiguous() -> None:
    assert len(STAGE_CONTRACTS) == len(StageId) == 20
    assert tuple(STAGE_REGISTRY) == STAGE_CONTRACTS
    assert tuple(contract.order for contract in STAGE_CONTRACTS) == tuple(range(20))
    assert tuple(contract.stage_id for contract in STAGE_CONTRACTS) == tuple(StageId)
    assert all(
        set(contract.mode_requirements) == set(ValidationMode)
        for contract in STAGE_CONTRACTS
    )


def test_stage_dependencies_always_point_backward() -> None:
    positions = {contract.stage_id: contract.order for contract in STAGE_CONTRACTS}
    for contract in STAGE_CONTRACTS:
        predecessors = (
            *contract.required_predecessors,
            *contract.blocking_predecessors,
            *contract.ordered_after,
        )
        assert all(positions[predecessor] < contract.order for predecessor in predecessors)
        assert set(contract.blocking_predecessors).issubset(
            contract.required_predecessors
        )


def test_validation_stages_never_write_project_assets() -> None:
    assert all(not contract.may_write_project_assets() for contract in STAGE_CONTRACTS)
    assert not {
        effect
        for effect in StageEffect
        if effect.value.startswith("write_project")
    }


def test_process_backed_stages_preserve_raw_evidence() -> None:
    process_backed = {
        contract.stage_id
        for contract in STAGE_CONTRACTS
        if contract.process_backed
    }
    assert process_backed == _PROCESS_BACKED_STAGES
    for stage_id in process_backed:
        contract = get_stage_contract(stage_id)
        assert contract.cancellation_aware
        assert contract.preserves_raw_evidence
        assert StageEffect.EXECUTE_GF in contract.effects
        assert StageEffect.WRITE_RAW_EVIDENCE in contract.effects


def test_each_owned_stage_output_has_one_owner() -> None:
    owners: dict[str, StageId] = {}
    for contract in STAGE_CONTRACTS:
        for output in contract.owned_outputs:
            assert output not in owners
            owners[output] = contract.stage_id
    assert owners


def test_release_gate_and_manifest_requirements_are_release_specific() -> None:
    for mode in (
        ValidationMode.QUICK,
        ValidationMode.CHECKPOINT,
        ValidationMode.DIAGNOSTIC,
    ):
        assert (
            get_stage_requirement(StageId.EVALUATE_RELEASE_GATES, mode)
            is StageRequirement.NOT_APPLICABLE
        )
    assert (
        get_stage_requirement(StageId.EVALUATE_RELEASE_GATES, ValidationMode.RELEASE)
        is StageRequirement.REQUIRED
    )
    for stage_id in (StageId.WRITE_MANIFEST, StageId.VERIFY_MANIFEST):
        contract = get_stage_contract(stage_id)
        assert contract.owner is StageOwner.REPORTING
        assert contract.failure_policy is StageFailurePolicy.FINALIZE
        assert contract.is_required(ValidationMode.RELEASE)


def test_validation_package_initializer_is_import_free() -> None:
    tree = _module_tree("__init__.py")
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body)
    assert "__all__" not in vars(validation_package)


def test_validation_public_module_is_a_reexport_only_facade() -> None:
    public_tree = _module_tree("public.py")
    pipeline_tree = _module_tree("pipeline.py")
    selection_tree = _module_tree("selection/service.py")

    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for node in public_tree.body
    )
    imports = {
        (node.level, node.module): tuple(alias.name for alias in node.names)
        for node in public_tree.body
        if isinstance(node, ast.ImportFrom)
    }
    assert imports[(1, "pipeline")] == (
        "preflight_external_tools",
        "run_file_pipeline",
        "run_pgf_stage_if_required",
        "run_selected_scenarios",
    )
    assert imports[(1, "selection.service")] == ("select_files",)

    pipeline_functions = {
        node.name
        for node in pipeline_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    selection_functions = {
        node.name
        for node in selection_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "preflight_external_tools",
        "run_file_pipeline",
        "run_pgf_stage_if_required",
        "run_selected_scenarios",
    }.issubset(pipeline_functions)
    assert "select_files" in selection_functions


def test_validation_and_overall_statuses_remain_distinct_dimensions() -> None:
    assert tuple(item.value for item in ValidationStatus) == (
        "OK",
        "FAIL",
        "ERROR",
        "SKIPPED",
    )
    assert tuple(item.value for item in OverallStatus) == (
        "OK",
        "FAIL",
        "ERROR",
    )
    assert ValidationStatus.OK is not OverallStatus.OK
    assert not hasattr(OverallStatus, "SKIPPED")


def test_pipeline_status_aggregation_uses_required_results() -> None:
    assert aggregate_pipeline_status(
        (_pipeline_result(ValidationStatus.OK, required=True),)
    ) is OverallStatus.OK
    assert aggregate_pipeline_status(
        (_pipeline_result(ValidationStatus.FAIL, required=True),)
    ) is OverallStatus.FAIL
    assert aggregate_pipeline_status(
        (_pipeline_result(ValidationStatus.ERROR, required=True),)
    ) is OverallStatus.ERROR
    assert aggregate_pipeline_status(
        (_pipeline_result(ValidationStatus.FAIL, required=False),)
    ) is OverallStatus.OK


def test_pipeline_results_enforce_status_error_kind_consistency() -> None:
    with pytest.raises(ValueError, match="non-OK error kind"):
        _pipeline_result(
            ValidationStatus.FAIL,
            required=True,
            error_kind=ErrorKind.OK,
        )
    result = _pipeline_result(ValidationStatus.OK, required=True)
    with pytest.raises(FrozenInstanceError):
        setattr(result, "required", False)


def test_pipeline_plan_requires_executors_for_required_stages() -> None:
    with pytest.raises(ValueError, match="required stage"):
        ValidationPipelinePlan(
            mode=ValidationMode.QUICK,
            request=object(),
            executors={},
        )
