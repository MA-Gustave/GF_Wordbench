"""End-to-end quick-mode acceptance tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.config.models import (
    ResolvedEnvironment,
    RunConfig,
    ValidationTarget,
)
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.runs.planner import (
    StageId,
    StageRequirement,
    resolve_execution_plan,
)
from gf_wordbench.validation.selection.service import select_files


def _quick_run_config(
    tmp_path: Path,
    *,
    target: str = "src/Target.gf",
) -> RunConfig:
    project_root = (tmp_path / "project").resolve()
    source_root = project_root / "src"
    output_root = (tmp_path / "runs").resolve()
    rgl_root = (tmp_path / "rgl").resolve()
    gf_executable = (tmp_path / "bin" / "gf").resolve()

    source_root.mkdir(parents=True)
    output_root.mkdir(parents=True)
    rgl_root.mkdir(parents=True)
    gf_executable.parent.mkdir(parents=True)
    gf_executable.write_text("test executable placeholder\n", encoding="utf-8")

    (project_root / "project.toml").write_text(
        "# Project fixture owned by this test.\n",
        encoding="utf-8",
    )
    (source_root / "Target.gf").write_text(
        "abstract Target = { cat Item ; }\n",
        encoding="utf-8",
    )
    (source_root / "Unrelated.gf").write_text(
        "abstract Unrelated = { cat Other ; }\n",
        encoding="utf-8",
    )

    project = ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="quick-mode-fixture",
            name="Quick mode fixture",
            language_code="en",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("src"),
            glob="**/*.gf",
            include_regex=r".*\.gf$",
            exclude_regex=r"\A\Z",
        ),
        gf=GFProjectConfig(
            path_parts=(),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(),
            checkpoints=(),
        ),
        validation=ValidationPolicy(
            required_scenarios=(),
            optional_scenarios=(),
            release_requires_pgf=True,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )

    environment = ResolvedEnvironment(
        project_root=project_root,
        rgl_root=rgl_root,
        gf_executable=gf_executable,
        output_root=output_root,
        gf_path=(source_root, rgl_root),
    )

    return RunConfig(
        project=project,
        environment=environment,
        mode=ValidationMode.QUICK,
        target=ValidationTarget(
            kind=TargetKind.FILE,
            value=target,
        ),
        timeout_sec=30,
        max_files=0,
        keep_ok_details=False,
        diff_previous=False,
        skip_version_probe=False,
        no_compile=False,
        emit_cpu_stats=False,
        selected_checkpoints=(),
        selected_entrypoints=(),
        selected_scenarios=(),
        release_requires_pgf=True,
        evidence_level="bounded",
    )


def test_quick_mode_selects_one_target_and_builds_a_bounded_plan(
    tmp_path: Path,
) -> None:
    run_config = _quick_run_config(tmp_path)

    included_files, excluded_files = select_files(run_config)
    plan = resolve_execution_plan(run_config)

    expected_target = run_config.project.source_root / "Target.gf"
    assert included_files == [expected_target]
    assert excluded_files == []
    assert len(included_files) == 1

    assert plan.mode is ValidationMode.QUICK
    assert plan.target == run_config.target
    assert plan.release_eligible is False
    assert plan.build_pgf is False
    assert plan.selected_scenarios == ()

    required = set(plan.required_stage_ids)
    assert {
        StageId.CONFIGURATION,
        StageId.ENVIRONMENT,
        StageId.VERSION_PROBE,
        StageId.SELECTION,
        StageId.STATIC_SCAN,
        StageId.FINGERPRINT,
        StageId.COMPILE_SOURCES,
        StageId.CLASSIFY_FAILURES,
        StageId.WRITE_REPORTS,
        StageId.WRITE_MANIFEST,
    } <= required

    for stage_id in (
        StageId.COMPILE_CHECKPOINTS,
        StageId.COMPILE_ENTRYPOINTS,
        StageId.RUN_SCENARIOS,
        StageId.NORMALIZE_OUTPUTS,
        StageId.EVALUATE_ASSERTIONS,
        StageId.COMPARE_GOLD,
        StageId.BUILD_PGF,
        StageId.EVALUATE_RELEASE_GATES,
    ):
        stage = plan.stage(stage_id)
        assert stage.requirement is StageRequirement.SKIPPED
        assert stage.reason

    assert any(
        "cannot establish release eligibility" in warning
        for warning in plan.warnings
    )


def test_quick_mode_missing_target_never_falls_back_to_project_scan(
    tmp_path: Path,
) -> None:
    run_config = _quick_run_config(
        tmp_path,
        target="src/Missing.gf",
    )

    with pytest.raises(
        ConfigurationError,
        match="quick target cannot be selected",
    ):
        select_files(run_config)

    assert (run_config.project.source_root / "Unrelated.gf").is_file()
