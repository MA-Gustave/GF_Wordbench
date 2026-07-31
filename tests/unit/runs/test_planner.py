"""Unit tests for deterministic run-stage planning."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from gf_wordbench.config.models import (
    ResolvedEnvironment,
    RunConfig,
    ValidationTarget,
)
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.runs.planner import (
    PlannedStage,
    RunPlan,
    StageId,
    StageRequirement,
    resolve_execution_plan,
)


_STAGE_ORDER = (
    StageId.CONFIGURATION,
    StageId.ENVIRONMENT,
    StageId.VERSION_PROBE,
    StageId.SELECTION,
    StageId.STATIC_SCAN,
    StageId.FINGERPRINT,
    StageId.COMPILE_SOURCES,
    StageId.COMPILE_CHECKPOINTS,
    StageId.COMPILE_ENTRYPOINTS,
    StageId.CLASSIFY_FAILURES,
    StageId.RUN_SCENARIOS,
    StageId.NORMALIZE_OUTPUTS,
    StageId.EVALUATE_ASSERTIONS,
    StageId.COMPARE_GOLD,
    StageId.BUILD_PGF,
    StageId.COMPARE_PREVIOUS,
    StageId.EVALUATE_RELEASE_GATES,
    StageId.WRITE_REPORTS,
    StageId.WRITE_MANIFEST,
)

_ALWAYS_REQUIRED = {
    StageId.CONFIGURATION,
    StageId.ENVIRONMENT,
    StageId.SELECTION,
    StageId.STATIC_SCAN,
    StageId.FINGERPRINT,
    StageId.CLASSIFY_FAILURES,
    StageId.WRITE_REPORTS,
    StageId.WRITE_MANIFEST,
}

_EXTERNAL_STAGES = {
    StageId.VERSION_PROBE,
    StageId.COMPILE_SOURCES,
    StageId.COMPILE_CHECKPOINTS,
    StageId.COMPILE_ENTRYPOINTS,
    StageId.RUN_SCENARIOS,
    StageId.BUILD_PGF,
}


def _project_config(tmp_path: Path) -> ProjectConfig:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "src"
    return ProjectConfig(
        schema_id="gf-wordbench.project",
        schema_version="1.0",
        identity=ProjectIdentity(
            id="example-language",
            name="Example Language",
            language_code="eng",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="*.gf",
            include_regex=r"^[A-Z][A-Za-z0-9_]*\.gf$",
            exclude_regex=r"(\.bak\.gf$|\s)",
        ),
        gf=GFProjectConfig(
            path_parts=("src",),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("GrammarEng.gf"),),
            checkpoints=(Path("MorphoEng.gf"),),
        ),
        validation=ValidationPolicy(
            required_scenarios=("load",),
            optional_scenarios=("smoke",),
            release_requires_pgf=True,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )


def _run_config(
    tmp_path: Path,
    *,
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
    target: ValidationTarget | None = None,
    selected_checkpoints: tuple[Path, ...] | None = None,
    selected_entrypoints: tuple[Path, ...] | None = None,
    selected_scenarios: tuple[str, ...] | None = None,
    timeout_sec: int = 73,
    max_files: int = 0,
    diff_previous: bool = True,
    skip_version_probe: bool = False,
    no_compile: bool = False,
    release_requires_pgf: bool = True,
    evidence_level: str = "standard",
    compatibility_warnings: tuple[str, ...] = (),
) -> RunConfig:
    project = _project_config(tmp_path)
    source_root = project.source_root

    if target is None and mode is ValidationMode.QUICK:
        target = ValidationTarget(
            kind=TargetKind.FILE,
            value="LexiconEng.gf",
        )
    if selected_checkpoints is None:
        selected_checkpoints = (
            (source_root / "MorphoEng.gf",)
            if mode is ValidationMode.CHECKPOINT
            else ()
        )
    if selected_entrypoints is None:
        selected_entrypoints = (
            (source_root / "GrammarEng.gf",)
            if mode is ValidationMode.RELEASE
            else ()
        )
    if selected_scenarios is None:
        selected_scenarios = (
            ("load",)
            if mode is ValidationMode.RELEASE
            else ()
        )

    rgl_root = (tmp_path / "rgl").resolve()
    return RunConfig(
        project=project,
        environment=ResolvedEnvironment(
            project_root=project.project_root,
            rgl_root=rgl_root,
            gf_executable=(tmp_path / "bin" / "gf").resolve(),
            output_root=(tmp_path / "runs").resolve(),
            gf_path=(source_root, rgl_root),
        ),
        mode=mode,
        target=target,
        timeout_sec=timeout_sec,
        max_files=max_files,
        keep_ok_details=False,
        diff_previous=diff_previous,
        skip_version_probe=skip_version_probe,
        no_compile=no_compile,
        emit_cpu_stats=False,
        selected_checkpoints=selected_checkpoints,
        selected_entrypoints=selected_entrypoints,
        selected_scenarios=selected_scenarios,
        release_requires_pgf=release_requires_pgf,
        evidence_level=evidence_level,  # type: ignore[arg-type]
        compatibility_warnings=compatibility_warnings,
    )


def _requirements(plan: RunPlan) -> dict[StageId, StageRequirement]:
    return {stage.stage_id: stage.requirement for stage in plan.stages}


def test_planned_stage_exposes_enabled_and_required_flags() -> None:
    required = PlannedStage(
        StageId.CONFIGURATION,
        StageRequirement.REQUIRED,
    )
    optional = PlannedStage(
        StageId.COMPARE_PREVIOUS,
        StageRequirement.OPTIONAL,
    )
    skipped = PlannedStage(
        StageId.BUILD_PGF,
        StageRequirement.SKIPPED,
        reason="not selected",
    )

    assert required.enabled is True
    assert required.required is True
    assert optional.enabled is True
    assert optional.required is False
    assert skipped.enabled is False
    assert skipped.required is False


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        (
            {"stage_id": "configuration"},
            TypeError,
            "stage_id must be a StageId",
        ),
        (
            {"requirement": "required"},
            TypeError,
            "requirement must be a StageRequirement",
        ),
        (
            {"prerequisites": [StageId.CONFIGURATION]},
            TypeError,
            "prerequisites must be a tuple",
        ),
        (
            {
                "prerequisites": (
                    StageId.CONFIGURATION,
                    StageId.CONFIGURATION,
                )
            },
            ValueError,
            "must not contain duplicates",
        ),
        (
            {"prerequisites": (StageId.STATIC_SCAN,)},
            ValueError,
            "cannot depend on itself",
        ),
        (
            {"timeout_sec": 0},
            ValueError,
            "timeout_sec must be positive",
        ),
        (
            {"timeout_sec": True},
            TypeError,
            "timeout_sec must be an integer or None",
        ),
    ],
)
def test_planned_stage_rejects_invalid_contract_values(
    kwargs: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    values: dict[str, object] = {
        "stage_id": StageId.STATIC_SCAN,
        "requirement": StageRequirement.REQUIRED,
    }
    values.update(kwargs)

    with pytest.raises(exception, match=message):
        PlannedStage(**values)  # type: ignore[arg-type]


def test_planned_stage_requires_reason_only_when_skipped() -> None:
    with pytest.raises(ValueError, match="skipped stages require a reason"):
        PlannedStage(
            StageId.BUILD_PGF,
            StageRequirement.SKIPPED,
        )

    with pytest.raises(ValueError, match="enabled stages must not have"):
        PlannedStage(
            StageId.BUILD_PGF,
            StageRequirement.OPTIONAL,
            reason="not allowed",
        )


@pytest.mark.parametrize("reason", ["", "   ", "bad\x00reason"])
def test_planned_stage_rejects_invalid_skip_reason(reason: str) -> None:
    with pytest.raises(ValueError, match="reason"):
        PlannedStage(
            StageId.BUILD_PGF,
            StageRequirement.SKIPPED,
            reason=reason,
        )


def test_run_plan_properties_and_stage_lookup() -> None:
    stages = (
        PlannedStage(
            StageId.CONFIGURATION,
            StageRequirement.REQUIRED,
        ),
        PlannedStage(
            StageId.ENVIRONMENT,
            StageRequirement.OPTIONAL,
            prerequisites=(StageId.CONFIGURATION,),
        ),
        PlannedStage(
            StageId.BUILD_PGF,
            StageRequirement.SKIPPED,
            reason="not selected",
        ),
    )
    plan = RunPlan(
        mode=ValidationMode.DIAGNOSTIC,
        target=None,
        stages=stages,
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        compare_previous=False,
        build_pgf=False,
        evidence_level="expanded",
        release_eligible=False,
    )

    assert plan.selected_stage_ids == (
        StageId.CONFIGURATION,
        StageId.ENVIRONMENT,
    )
    assert plan.required_stage_ids == (StageId.CONFIGURATION,)
    assert plan.skipped_stage_ids == (StageId.BUILD_PGF,)
    assert plan.stage(StageId.ENVIRONMENT) is stages[1]

    with pytest.raises(KeyError, match="write_reports"):
        plan.stage(StageId.WRITE_REPORTS)
    with pytest.raises(TypeError, match="stage_id must be a StageId"):
        plan.stage("environment")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("stages", "message"),
    [
        ((), "stages must not be empty"),
        (
            (
                PlannedStage(
                    StageId.CONFIGURATION,
                    StageRequirement.REQUIRED,
                ),
                PlannedStage(
                    StageId.CONFIGURATION,
                    StageRequirement.OPTIONAL,
                ),
            ),
            "stage IDs must be unique",
        ),
        (
            (
                PlannedStage(
                    StageId.ENVIRONMENT,
                    StageRequirement.REQUIRED,
                    prerequisites=(StageId.CONFIGURATION,),
                ),
            ),
            "references an absent prerequisite",
        ),
        (
            (
                PlannedStage(
                    StageId.ENVIRONMENT,
                    StageRequirement.REQUIRED,
                    prerequisites=(StageId.CONFIGURATION,),
                ),
                PlannedStage(
                    StageId.CONFIGURATION,
                    StageRequirement.REQUIRED,
                ),
            ),
            "configuration must precede environment",
        ),
    ],
)
def test_run_plan_rejects_invalid_stage_graph(
    stages: tuple[PlannedStage, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        RunPlan(
            mode=ValidationMode.DIAGNOSTIC,
            target=None,
            stages=stages,
            selected_checkpoints=(),
            selected_entrypoints=(),
            selected_scenarios=(),
            compare_previous=False,
            build_pgf=False,
            evidence_level="expanded",
            release_eligible=False,
        )


def test_run_plan_enforces_release_eligibility_invariants() -> None:
    stage = PlannedStage(
        StageId.CONFIGURATION,
        StageRequirement.REQUIRED,
    )

    with pytest.raises(ValueError, match="only release mode"):
        RunPlan(
            mode=ValidationMode.DIAGNOSTIC,
            target=None,
            stages=(stage,),
            selected_checkpoints=(),
            selected_entrypoints=(),
            selected_scenarios=(),
            compare_previous=False,
            build_pgf=True,
            evidence_level="expanded",
            release_eligible=True,
        )

    with pytest.raises(ValueError, match="requires a PGF build"):
        RunPlan(
            mode=ValidationMode.RELEASE,
            target=None,
            stages=(stage,),
            selected_checkpoints=(),
            selected_entrypoints=(),
            selected_scenarios=(),
            compare_previous=False,
            build_pgf=False,
            evidence_level="complete",
            release_eligible=True,
        )


def test_resolve_execution_plan_requires_run_config() -> None:
    with pytest.raises(TypeError, match="request must be a RunConfig"):
        resolve_execution_plan(object())  # type: ignore[arg-type]


def test_quick_plan_is_bounded_and_not_release_eligible(
    tmp_path: Path,
) -> None:
    request = _run_config(
        tmp_path,
        mode=ValidationMode.QUICK,
        target=ValidationTarget(TargetKind.FILE, "LexiconEng.gf"),
        diff_previous=False,
        evidence_level="bounded",
    )

    plan = resolve_execution_plan(request)
    requirements = _requirements(plan)

    assert tuple(stage.stage_id for stage in plan.stages) == _STAGE_ORDER
    assert plan.mode is ValidationMode.QUICK
    assert plan.target == request.target
    assert plan.release_eligible is False
    assert plan.build_pgf is False
    assert plan.compare_previous is False
    assert plan.evidence_level == "bounded"
    assert plan.warnings == (
        "quick mode cannot establish release eligibility",
    )
    assert requirements[StageId.VERSION_PROBE] is StageRequirement.REQUIRED
    assert requirements[StageId.COMPILE_SOURCES] is StageRequirement.REQUIRED
    assert requirements[StageId.COMPILE_CHECKPOINTS] is StageRequirement.SKIPPED
    assert requirements[StageId.COMPILE_ENTRYPOINTS] is StageRequirement.SKIPPED
    assert requirements[StageId.RUN_SCENARIOS] is StageRequirement.SKIPPED
    assert requirements[StageId.BUILD_PGF] is StageRequirement.SKIPPED
    assert (
        requirements[StageId.EVALUATE_RELEASE_GATES]
        is StageRequirement.SKIPPED
    )


@pytest.mark.parametrize(
    ("target", "message"),
    [
        (
            ValidationTarget(TargetKind.CHECKPOINT, "morphology"),
            "quick mode requires a file or module target",
        ),
        (
            ValidationTarget(TargetKind.PROJECT, None),
            "quick mode requires a file or module target",
        ),
    ],
)
def test_quick_plan_rejects_unbounded_target_kinds(
    tmp_path: Path,
    target: ValidationTarget,
    message: str,
) -> None:
    request = _run_config(
        tmp_path,
        mode=ValidationMode.QUICK,
        target=target,
    )

    with pytest.raises(ValueError, match=message):
        resolve_execution_plan(request)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {"selected_checkpoints": (Path("MorphoEng.gf"),)},
            "quick mode does not accept checkpoints",
        ),
        ({"max_files": 1}, "quick mode does not accept max_files"),
        ({"no_compile": True}, "quick mode cannot disable compilation"),
    ],
)
def test_quick_plan_rejects_weakening_or_expanding_options(
    tmp_path: Path,
    changes: dict[str, object],
    message: str,
) -> None:
    request = _run_config(tmp_path, mode=ValidationMode.QUICK)
    if "selected_checkpoints" in changes:
        changes = {
            **changes,
            "selected_checkpoints": (
                (tmp_path / "project" / "src" / "MorphoEng.gf").resolve(),
            ),
        }
    request = replace(request, **changes)

    with pytest.raises(ValueError, match=message):
        resolve_execution_plan(request)


def test_checkpoint_plan_requires_checkpoint_compile_and_scenario_evidence(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "project" / "src").resolve()
    request = _run_config(
        tmp_path,
        mode=ValidationMode.CHECKPOINT,
        target=ValidationTarget(TargetKind.CHECKPOINT, "morphology"),
        selected_checkpoints=(source_root / "MorphoEng.gf",),
        selected_scenarios=("morphology",),
        evidence_level="standard",
    )

    plan = resolve_execution_plan(request)
    requirements = _requirements(plan)

    assert requirements[StageId.COMPILE_SOURCES] is StageRequirement.REQUIRED
    assert (
        requirements[StageId.COMPILE_CHECKPOINTS]
        is StageRequirement.REQUIRED
    )
    for stage_id in (
        StageId.RUN_SCENARIOS,
        StageId.NORMALIZE_OUTPUTS,
        StageId.EVALUATE_ASSERTIONS,
        StageId.COMPARE_GOLD,
    ):
        assert requirements[stage_id] is StageRequirement.REQUIRED
    assert requirements[StageId.COMPILE_ENTRYPOINTS] is StageRequirement.SKIPPED
    assert plan.release_eligible is False


def test_checkpoint_plan_rejects_non_checkpoint_target(
    tmp_path: Path,
) -> None:
    request = _run_config(
        tmp_path,
        mode=ValidationMode.CHECKPOINT,
        target=ValidationTarget(TargetKind.MODULE, "MorphoEng"),
    )

    with pytest.raises(ValueError, match="requires a checkpoint target"):
        resolve_execution_plan(request)


def test_release_plan_requires_complete_release_evidence(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "project" / "src").resolve()
    request = _run_config(
        tmp_path,
        mode=ValidationMode.RELEASE,
        target=ValidationTarget(TargetKind.PROJECT, None),
        selected_checkpoints=(
            source_root / "SyntaxEng.gf",
            source_root / "MorphoEng.gf",
        ),
        selected_entrypoints=(
            source_root / "LangEng.gf",
            source_root / "GrammarEng.gf",
        ),
        selected_scenarios=("syntax", "load"),
        evidence_level="complete",
        compatibility_warnings=("newer GF version is untested",),
    )

    plan = resolve_execution_plan(
        request,
        SimpleNamespace(
            gf_available=True,
            version_compatible=True,
            pgf_supported=True,
        ),
    )
    requirements = _requirements(plan)

    expected_required = _ALWAYS_REQUIRED | {
        StageId.VERSION_PROBE,
        StageId.COMPILE_SOURCES,
        StageId.COMPILE_CHECKPOINTS,
        StageId.COMPILE_ENTRYPOINTS,
        StageId.RUN_SCENARIOS,
        StageId.NORMALIZE_OUTPUTS,
        StageId.EVALUATE_ASSERTIONS,
        StageId.COMPARE_GOLD,
        StageId.BUILD_PGF,
        StageId.EVALUATE_RELEASE_GATES,
    }

    assert set(plan.required_stage_ids) == expected_required
    assert plan.release_eligible is True
    assert plan.build_pgf is True
    assert plan.compare_previous is True
    assert plan.evidence_level == "complete"
    assert plan.warnings == ("newer GF version is untested",)
    assert plan.selected_checkpoints == tuple(
        sorted(
            request.selected_checkpoints,
            key=lambda path: path.as_posix().casefold(),
        )
    )
    assert plan.selected_entrypoints == tuple(
        sorted(
            request.selected_entrypoints,
            key=lambda path: path.as_posix().casefold(),
        )
    )
    assert plan.selected_scenarios == ("load", "syntax")
    assert all(
        requirements[stage_id] is StageRequirement.REQUIRED
        for stage_id in expected_required
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {"skip_version_probe": True},
            "release mode cannot skip the version probe",
        ),
        (
            {"no_compile": True},
            "release mode cannot disable compilation",
        ),
        (
            {"max_files": 1},
            "release mode cannot limit selected files",
        ),
        (
            {"selected_scenarios": ()},
            "release mode requires selected scenarios",
        ),
        (
            {"release_requires_pgf": False},
            "release mode requires PGF verification",
        ),
        (
            {
                "target": ValidationTarget(
                    TargetKind.FILE,
                    "LexiconEng.gf",
                )
            },
            "release mode requires a project or entrypoint target",
        ),
    ],
)
def test_release_plan_rejects_weakened_contract(
    tmp_path: Path,
    changes: dict[str, object],
    message: str,
) -> None:
    request = _run_config(tmp_path, mode=ValidationMode.RELEASE)
    request = replace(request, **changes)

    with pytest.raises(ValueError, match=message):
        resolve_execution_plan(request)


def test_diagnostic_plan_supports_explicit_scan_only_policy(
    tmp_path: Path,
) -> None:
    request = _run_config(
        tmp_path,
        mode=ValidationMode.DIAGNOSTIC,
        no_compile=True,
        skip_version_probe=True,
        diff_previous=False,
        evidence_level="expanded",
    )

    plan = resolve_execution_plan(
        request,
        SimpleNamespace(
            gf_available=False,
            version_compatible=False,
            pgf_supported=False,
        ),
    )
    requirements = _requirements(plan)

    assert requirements[StageId.VERSION_PROBE] is StageRequirement.SKIPPED
    assert requirements[StageId.COMPILE_SOURCES] is StageRequirement.SKIPPED
    assert requirements[StageId.COMPILE_CHECKPOINTS] is StageRequirement.SKIPPED
    assert requirements[StageId.COMPILE_ENTRYPOINTS] is StageRequirement.SKIPPED
    assert requirements[StageId.COMPARE_PREVIOUS] is StageRequirement.SKIPPED
    assert plan.stage(StageId.COMPILE_SOURCES).reason == "compilation is disabled"
    assert plan.evidence_level == "expanded"
    assert plan.release_eligible is False


def test_optional_diagnostic_scenario_and_pgf_stages_are_enabled(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "project" / "src").resolve()
    request = _run_config(
        tmp_path,
        mode=ValidationMode.DIAGNOSTIC,
        selected_entrypoints=(source_root / "GrammarEng.gf",),
        selected_scenarios=("smoke",),
        release_requires_pgf=True,
    )

    plan = resolve_execution_plan(request)
    requirements = _requirements(plan)

    for stage_id in (
        StageId.COMPILE_ENTRYPOINTS,
        StageId.RUN_SCENARIOS,
        StageId.NORMALIZE_OUTPUTS,
        StageId.EVALUATE_ASSERTIONS,
        StageId.COMPARE_GOLD,
        StageId.BUILD_PGF,
        StageId.COMPARE_PREVIOUS,
    ):
        assert requirements[stage_id] is StageRequirement.OPTIONAL


@pytest.mark.parametrize(
    ("facts", "message"),
    [
        (
            SimpleNamespace(
                gf_available=False,
                version_compatible=True,
                pgf_supported=True,
            ),
            "GF is unavailable",
        ),
        (
            SimpleNamespace(
                gf_available=True,
                version_compatible=False,
                pgf_supported=True,
            ),
            "requires a compatible GF version",
        ),
        (
            SimpleNamespace(
                gf_available=True,
                version_compatible=True,
                pgf_supported=False,
            ),
            "requires supported PGF construction",
        ),
    ],
)
def test_release_plan_rejects_failed_preflight_facts(
    tmp_path: Path,
    facts: SimpleNamespace,
    message: str,
) -> None:
    request = _run_config(tmp_path, mode=ValidationMode.RELEASE)

    with pytest.raises(ValueError, match=message):
        resolve_execution_plan(request, facts)


@pytest.mark.parametrize(
    "field",
    ["gf_available", "version_compatible", "pgf_supported"],
)
def test_preflight_facts_require_plain_booleans(
    tmp_path: Path,
    field: str,
) -> None:
    values: dict[str, object] = {
        "gf_available": True,
        "version_compatible": True,
        "pgf_supported": True,
    }
    values[field] = 1

    with pytest.raises(TypeError, match=rf"preflight\.{field} must be a bool"):
        resolve_execution_plan(
            _run_config(tmp_path),
            SimpleNamespace(**values),
        )


def test_stage_timeouts_apply_only_to_external_operations(
    tmp_path: Path,
) -> None:
    source_root = (tmp_path / "project" / "src").resolve()
    request = _run_config(
        tmp_path,
        selected_checkpoints=(source_root / "MorphoEng.gf",),
        selected_entrypoints=(source_root / "GrammarEng.gf",),
        selected_scenarios=("smoke",),
        timeout_sec=91,
    )

    plan = resolve_execution_plan(request)

    for stage in plan.stages:
        expected = 91 if stage.stage_id in _EXTERNAL_STAGES else None
        assert stage.timeout_sec == expected


def test_skipped_stage_prerequisites_are_removed_from_plan_graph(
    tmp_path: Path,
) -> None:
    request = _run_config(
        tmp_path,
        no_compile=True,
        selected_scenarios=("smoke",),
    )

    plan = resolve_execution_plan(request)

    assert plan.stage(StageId.BUILD_PGF).prerequisites == ()
    assert plan.stage(StageId.NORMALIZE_OUTPUTS).prerequisites == (
        StageId.RUN_SCENARIOS,
    )
    assert plan.stage(StageId.WRITE_MANIFEST).prerequisites == (
        StageId.WRITE_REPORTS,
    )


def test_compatibility_warnings_keep_order_and_are_deduplicated(
    tmp_path: Path,
) -> None:
    request = _run_config(
        tmp_path,
        compatibility_warnings=("warning-a", "warning-b"),
    )

    plan = resolve_execution_plan(request)

    assert plan.warnings == (
        "warning-a",
        "warning-b",
        "diagnostic mode cannot establish release eligibility",
    )
