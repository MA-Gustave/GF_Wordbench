from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from gf_wordbench.config.models import ResolvedEnvironment, RunConfig
from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.ids import ProjectId, SchemaId
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.validation.selection.service import SelectionService


def _project(tmp_path: Path) -> ProjectConfig:
    project_root = tmp_path / "project"
    source_root = project_root / "lib" / "src" / "example"
    source_root.mkdir(parents=True)
    (project_root / "project.toml").write_text("", encoding="utf-8")

    for name in (
        "MorphologyCheckpoint.gf",
        "SyntaxCheckpoint.gf",
        "UnrelatedModule.gf",
    ):
        (source_root / name).write_text(
            f"resource {Path(name).stem} = {{}}\n",
            encoding="utf-8",
        )

    return ProjectConfig(
        schema_id=SchemaId("gf-wordbench.project"),
        schema_version="1.0",
        identity=ProjectIdentity(
            id=ProjectId("checkpoint-project"),
            name="Checkpoint Project",
            language_code="xcp",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=Path("lib/src/example"),
            glob="*.gf",
            include_regex=r"^[A-Z][A-Za-z0-9_]*\.gf$",
            exclude_regex=r"(\.bak\.gf$|\.tmp\.gf$)",
        ),
        gf=GFProjectConfig(
            path_parts=("lib/src", "lib/src/example"),
            minimum_version="",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("SyntaxCheckpoint.gf"),),
            checkpoints=(
                Path("MorphologyCheckpoint.gf"),
                Path("SyntaxCheckpoint.gf"),
            ),
        ),
        validation=ValidationPolicy(
            required_scenarios=(),
            optional_scenarios=(),
            release_requires_pgf=False,
        ),
        project_file=project_root / "project.toml",
        project_root=project_root,
        source_root=source_root,
    )


def _run_config(tmp_path: Path, project: ProjectConfig) -> RunConfig:
    rgl_root = tmp_path / "rgl"
    output_root = tmp_path / "runs"
    tool_root = tmp_path / "tools"
    rgl_root.mkdir()
    output_root.mkdir()
    tool_root.mkdir()
    gf_executable = tool_root / "gf"
    gf_executable.write_text("", encoding="utf-8")

    selected_checkpoints = tuple(
        project.source_root / checkpoint for checkpoint in project.modules.checkpoints
    )

    return RunConfig(
        project=project,
        environment=ResolvedEnvironment(
            project_root=project.project_root,
            rgl_root=rgl_root,
            gf_executable=gf_executable,
            output_root=output_root,
            gf_path=(project.project_root / "lib" / "src",),
        ),
        mode=ValidationMode.CHECKPOINT,
        target=None,
        timeout_sec=30,
        max_files=0,
        keep_ok_details=False,
        diff_previous=False,
        skip_version_probe=True,
        no_compile=False,
        emit_cpu_stats=False,
        selected_checkpoints=selected_checkpoints,
        selected_entrypoints=(),
        selected_scenarios=(),
        release_requires_pgf=False,
        evidence_level="standard",
    )


def test_checkpoint_mode_selects_only_declared_checkpoints_in_declared_order(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    run_config = _run_config(tmp_path, project)

    selected, excluded = SelectionService().select(run_config)

    assert selected == [
        project.source_root / "MorphologyCheckpoint.gf",
        project.source_root / "SyntaxCheckpoint.gf",
    ]
    assert excluded == []
    assert project.source_root / "UnrelatedModule.gf" not in selected


def test_checkpoint_mode_rejects_a_missing_required_checkpoint(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    run_config = _run_config(tmp_path, project)
    missing = project.source_root / "MissingCheckpoint.gf"
    run_config = replace(
        run_config,
        selected_checkpoints=(
            run_config.selected_checkpoints[0],
            missing,
        ),
    )

    with pytest.raises(ConfigurationError):
        SelectionService().select(run_config)


def test_checkpoint_mode_rejects_a_checkpoint_excluded_by_project_policy(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    excluded_checkpoint = project.source_root / "Temporary.tmp.gf"
    excluded_checkpoint.write_text(
        "resource Temporary = {}\n",
        encoding="utf-8",
    )
    run_config = replace(
        _run_config(tmp_path, project),
        selected_checkpoints=(excluded_checkpoint,),
    )

    with pytest.raises(ConfigurationError):
        SelectionService().select(run_config)


def test_checkpoint_mode_rejects_max_files_instead_of_truncating(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    run_config = replace(
        _run_config(tmp_path, project),
        max_files=1,
    )

    with pytest.raises(ConfigurationError):
        SelectionService().select(run_config)
