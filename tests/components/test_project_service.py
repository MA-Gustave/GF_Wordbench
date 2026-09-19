from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.kernel.errors import ProjectConfigurationError
from gf_wordbench.projects.filesystem_adapter import ProjectFilesystemAdapter
from gf_wordbench.projects.models import (
    ProjectCheckScope,
    ProjectConfig,
    ProjectValidationResult,
)
from gf_wordbench.projects.policies import REQUIRED_PROJECT_ASSETS
from gf_wordbench.projects.public import check_project, load_project_config
from gf_wordbench.projects.schema import ProjectDocument, parse_project_document
from gf_wordbench.projects.validator import ProjectValidator, ensure_project_valid


@dataclass(slots=True)
class _RecordingReader:
    document: Mapping[str, object]
    calls: list[Path] = field(default_factory=list)

    def read(self, project_file: Path) -> Mapping[str, object]:
        self.calls.append(project_file)
        return deepcopy(self.document)


@dataclass(slots=True)
class _RecordingValidator:
    calls: list[ProjectConfig] = field(default_factory=list)

    def validate_for_load(
        self,
        project: ProjectConfig,
    ) -> ProjectValidationResult:
        self.calls.append(project)
        return ProjectValidationResult()


def _project_document() -> ProjectDocument:
    return {
        "schema_id": "gf-wordbench.project",
        "schema_version": "1.0",
        "project": {
            "id": "fixture",
            "name": "Fixture Language",
            "language_code": "fx",
            "root": ".",
        },
        "sources": {
            "directory": "src",
            "glob": "*.gf",
            "include_regex": r"^[A-Z][A-Za-z0-9_]*\.gf$",
            "exclude_regex": r"(\.bak\.gf$|\.tmp\.gf$|\s)",
        },
        "gf": {
            "path_parts": ["src"],
            "minimum_version": "",
        },
        "modules": {
            "entrypoints": ["GrammarFixture.gf"],
            "checkpoints": ["CoreFixture.gf"],
        },
        "validation": {
            "required_scenarios": ["smoke"],
            "optional_scenarios": ["optional"],
            "release_requires_pgf": False,
        },
    }


def _write_file(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _materialize_project(root: Path) -> ProjectConfig:
    root.mkdir(parents=True)
    project_file = root / "project.toml"
    _write_file(project_file)

    for module_name in ("GrammarFixture.gf", "CoreFixture.gf"):
        _write_file(root / "src" / module_name)

    for scenario_id in ("smoke", "optional"):
        _write_file(
            root / "validation" / "scenarios" / f"{scenario_id}.gfs",
            f'ps "GF_WORDBENCH_SCENARIO_BEGIN:{scenario_id}"\n'
            f'ps "GF_WORDBENCH_SCENARIO_END:{scenario_id}"\n'
            "q\n",
        )

    for relative_path in REQUIRED_PROJECT_ASSETS:
        _write_file(root / relative_path, "Fixture project asset.\n")

    return parse_project_document(
        _project_document(),
        source_file=project_file,
    )


def _snapshot(root: Path) -> tuple[tuple[str, str, bytes], ...]:
    entries: list[tuple[str, str, bytes]] = []
    for entry in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = entry.relative_to(root).as_posix()
        if entry.is_dir():
            entries.append((relative, "directory", b""))
        elif entry.is_file():
            entries.append((relative, "file", entry.read_bytes()))
    return tuple(entries)


def test_load_project_config_coordinates_reader_schema_and_validator(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project" / "project.toml"
    reader = _RecordingReader(_project_document())
    recording_validator = _RecordingValidator()
    validator = cast("ProjectValidator", recording_validator)

    project = load_project_config(
        project_file,
        reader=reader,
        validator=validator,
    )

    assert reader.calls == [project_file]
    assert recording_validator.calls == [project]
    assert project.project_file == project_file
    assert project.project_root == project_file.parent
    assert project.source_root == project_file.parent / "src"
    assert project.project_id == "fixture"
    assert project.modules.entrypoints == (Path("GrammarFixture.gf"),)
    assert project.validation.required_scenarios == ("smoke",)


def test_load_project_config_rejects_relative_path_before_reading() -> None:
    reader = _RecordingReader(_project_document())
    recording_validator = _RecordingValidator()
    validator = cast("ProjectValidator", recording_validator)

    with pytest.raises(
        ProjectConfigurationError,
        match="explicit absolute path",
    ):
        load_project_config(
            Path("project/project.toml"),
            reader=reader,
            validator=validator,
        )

    assert reader.calls == []
    assert recording_validator.calls == []


def test_check_project_accepts_complete_project_without_mutation(
    tmp_path: Path,
) -> None:
    project = _materialize_project(tmp_path / "project")
    filesystem = ProjectFilesystemAdapter()
    before = _snapshot(project.project_root)

    result = check_project(
        project,
        filesystem,
        scope=ProjectCheckScope.NORMAL,
        strict=True,
    )

    assert result.ok
    assert result.diagnostics == ()
    assert _snapshot(project.project_root) == before


def test_configuration_scope_is_pure_and_needs_no_filesystem_state(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "absent-project" / "project.toml"
    project = parse_project_document(
        _project_document(),
        source_file=project_file,
    )

    result = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.CONFIGURATION,
        strict=True,
    )

    assert result.ok
    assert result.diagnostics == ()
    assert not project.project_root.exists()


def test_missing_optional_scenario_is_warning_not_failure(
    tmp_path: Path,
) -> None:
    project = _materialize_project(tmp_path / "project")
    optional_scenario = project.project_root / "validation" / "scenarios" / "optional.gfs"
    optional_scenario.unlink()

    result = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.NORMAL,
    )

    assert result.ok
    assert result.errors == ()
    assert tuple(item.code for item in result.warnings) == ("PROJECT_SCENARIO_MISSING",)
    assert result.warnings[0].subject == optional_scenario


def test_missing_required_scenario_is_error(
    tmp_path: Path,
) -> None:
    project = _materialize_project(tmp_path / "project")
    required_scenario = project.project_root / "validation" / "scenarios" / "smoke.gfs"
    required_scenario.unlink()

    result = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.NORMAL,
    )

    assert not result.ok
    assert tuple(item.code for item in result.errors) == ("PROJECT_SCENARIO_MISSING",)
    assert result.errors[0].subject == required_scenario


def test_strict_check_reports_unresolved_project_placeholder(
    tmp_path: Path,
) -> None:
    project = _materialize_project(tmp_path / "project")
    contract = project.project_root / "docs" / "INTERFILE_CONTRACT_LOCK.md"
    _write_file(contract, "Owner: <OWNER>\n")

    normal = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.NORMAL,
        strict=False,
    )
    strict = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.NORMAL,
        strict=True,
    )

    assert normal.ok
    assert not strict.ok
    assert any(
        item.code == "PROJECT_PLACEHOLDER_UNRESOLVED" and item.subject == contract
        for item in strict.errors
    )


def test_ensure_project_valid_raises_bounded_configuration_error(
    tmp_path: Path,
) -> None:
    project = _materialize_project(tmp_path / "project")
    (project.source_root / "GrammarFixture.gf").unlink()

    with pytest.raises(
        ProjectConfigurationError,
        match="Active project validation failed",
    ) as captured:
        ensure_project_valid(
            project,
            ProjectFilesystemAdapter(),
            scope=ProjectCheckScope.NORMAL,
        )

    error = captured.value
    assert error.code == "GF-WB-PROJECT-001"
    assert error.stage == "projects"
    assert error.operation == "validate-project"
    assert "PROJECT_ENTRYPOINT_MISSING" in error.detail
