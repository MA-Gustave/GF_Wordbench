"""Unit tests for the canonical active-project loading boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass, field
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.kernel.errors import (
    ProjectConfigurationError,
    SchemaValidationError,
)
from gf_wordbench.projects import loader as loader_module
from gf_wordbench.projects.loader import ProjectLoader, load_project_config
from gf_wordbench.projects.models import (
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
)
from gf_wordbench.projects.validator import ProjectValidator

_EXPECTED_PUBLIC_NAMES = (
    "ProjectLoader",
    "load_project_config",
)


def _validator(value: object) -> ProjectValidator:
    return cast(ProjectValidator, value)


def _valid_document() -> dict[str, object]:
    return {
        "schema_id": str(PROJECT_SCHEMA_ID),
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project": {
            "id": "example-language",
            "name": "Example Language",
            "language_code": "ex",
            "root": ".",
        },
        "sources": {
            "directory": "src",
            "glob": "*.gf",
            "include_regex": "",
            "exclude_regex": "",
        },
        "gf": {
            "path_parts": [".", "src"],
            "minimum_version": "",
        },
        "modules": {
            "entrypoints": ["src/Example.gf"],
            "checkpoints": ["src/ExampleSyntax.gf"],
        },
        "validation": {
            "required_scenarios": ["smoke"],
            "optional_scenarios": ["generation"],
            "release_requires_pgf": True,
        },
    }


@dataclass(slots=True)
class _RecordingReader:
    document: Mapping[str, object]
    calls: list[Path] = field(default_factory=list)
    error: BaseException | None = None

    def read(self, project_file: Path) -> Mapping[str, object]:
        self.calls.append(project_file)
        if self.error is not None:
            raise self.error
        return deepcopy(dict(self.document))


@dataclass(slots=True)
class _RecordingValidator:
    calls: list[ProjectConfig] = field(default_factory=list)
    error: BaseException | None = None

    def validate_for_load(self, project: ProjectConfig) -> None:
        self.calls.append(project)
        if self.error is not None:
            raise self.error


def test_module_exposes_only_the_canonical_loader_contract() -> None:
    assert loader_module.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(loader_module, name) for name in loader_module.__all__)


def test_project_loader_is_frozen_and_slotted() -> None:
    instance = ProjectLoader(
        reader=_RecordingReader(_valid_document()),
        validator=_validator(_RecordingValidator()),
    )

    assert not hasattr(instance, "__dict__")

    with pytest.raises(FrozenInstanceError):
        instance.reader = _RecordingReader(_valid_document())  # type: ignore[misc]


def test_loader_builds_one_typed_project_from_explicit_project_file(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project.toml"
    original_document = _valid_document()
    reader = _RecordingReader(original_document)
    validator = _RecordingValidator()

    project = ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert reader.calls == [project_file]
    assert validator.calls == [project]
    assert original_document == _valid_document()

    assert project.schema_id == PROJECT_SCHEMA_ID
    assert project.schema_version == PROJECT_SCHEMA_VERSION
    assert str(project.identity.id) == "example-language"
    assert project.identity.name == "Example Language"
    assert project.identity.language_code == "ex"
    assert project.identity.root == Path(".")
    assert project.sources.directory == Path("src")
    assert project.sources.glob == "*.gf"
    assert project.gf.path_parts == (".", "src")
    assert project.modules.entrypoints == (Path("src/Example.gf"),)
    assert project.modules.checkpoints == (Path("src/ExampleSyntax.gf"),)
    assert tuple(map(str, project.validation.required_scenarios)) == ("smoke",)
    assert tuple(map(str, project.validation.optional_scenarios)) == ("generation",)
    assert project.validation.release_requires_pgf is True
    assert project.project_file == project_file
    assert project.project_root == tmp_path
    assert project.source_root == tmp_path / "src"


def test_loader_uses_the_normative_pipeline_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project.toml"
    document = _valid_document()
    events: list[str] = []
    expected_project = cast(ProjectConfig, object())

    class Reader:
        def read(self, source: Path) -> Mapping[str, object]:
            assert source == project_file
            events.append("read")
            return document

    class Validator:
        def validate_for_load(self, project: ProjectConfig) -> None:
            assert project is expected_project
            events.append("validate")

    def parse(
        value: Mapping[str, object],
        *,
        source_file: Path,
    ) -> ProjectConfig:
        assert value is document
        assert source_file == project_file
        events.append("parse")
        return expected_project

    def enforce(project: ProjectConfig) -> ProjectConfig:
        assert project is expected_project
        events.append("enforce")
        return project

    monkeypatch.setattr(loader_module, "parse_project_document", parse)
    monkeypatch.setattr(loader_module, "enforce_project_invariants", enforce)

    result = ProjectLoader(reader=Reader(), validator=_validator(Validator())).load(project_file)

    assert result is expected_project
    assert events == ["read", "parse", "enforce", "validate"]


def test_loader_does_not_require_project_file_or_parent_to_exist(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "not-created" / "project.toml"
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator()

    project = ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert project.project_file == project_file
    assert not project_file.exists()
    assert not project_file.parent.exists()
    assert reader.calls == [project_file]
    assert validator.calls == [project]


def test_facade_composes_supplied_reader_and_validator(tmp_path: Path) -> None:
    project_file = tmp_path / "project.toml"
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator()

    project = load_project_config(
        project_file,
        reader=reader,
        validator=_validator(validator),
    )

    assert project.project_file == project_file
    assert reader.calls == [project_file]
    assert validator.calls == [project]


def test_loader_rejects_non_path_before_using_services() -> None:
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator()

    with pytest.raises(TypeError, match="project_file must be pathlib.Path"):
        ProjectLoader(reader=reader, validator=_validator(validator)).load(
            cast(Path, "/workspace/project/project.toml")
        )

    assert reader.calls == []
    assert validator.calls == []


@pytest.mark.parametrize(
    ("project_file_factory", "message"),
    [
        (
            lambda root: Path("project.toml"),
            "explicit absolute path",
        ),
        (
            lambda root: root / "active-project.toml",
            "must name 'project.toml'",
        ),
        (
            lambda root: Path(str(root / "bad\x00name" / "project.toml")),
            "NUL character",
        ),
        (
            lambda root: root / "nested" / ".." / "project.toml",
            "lexically normalized",
        ),
    ],
)
def test_loader_rejects_invalid_project_file_paths_before_reading(
    tmp_path: Path,
    project_file_factory: Callable[[Path], Path],
    message: str,
) -> None:
    project_file = project_file_factory(tmp_path)
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator()

    with pytest.raises(ProjectConfigurationError, match=message) as captured:
        ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert captured.value.subject == str(project_file)
    assert reader.calls == []
    assert validator.calls == []


def test_schema_failure_stops_before_semantic_and_filesystem_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project.toml"
    reader = _RecordingReader({"schema_id": "wrong"})
    validator = _RecordingValidator()
    invariant_calls: list[ProjectConfig] = []

    def record_invariant(project: ProjectConfig) -> ProjectConfig:
        invariant_calls.append(project)
        return project

    monkeypatch.setattr(
        loader_module,
        "enforce_project_invariants",
        record_invariant,
    )

    with pytest.raises(SchemaValidationError):
        ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert reader.calls == [project_file]
    assert invariant_calls == []
    assert validator.calls == []


def test_semantic_failure_stops_before_load_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project.toml"
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator()
    expected = ProjectConfigurationError("semantic project invariant failed")

    def reject(_: ProjectConfig) -> ProjectConfig:
        raise expected

    monkeypatch.setattr(loader_module, "enforce_project_invariants", reject)

    with pytest.raises(ProjectConfigurationError) as captured:
        ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert captured.value is expected
    assert reader.calls == [project_file]
    assert validator.calls == []


def test_reader_failure_is_propagated_without_validation(tmp_path: Path) -> None:
    project_file = tmp_path / "project.toml"
    expected = OSError("project TOML could not be read")
    reader = _RecordingReader(_valid_document(), error=expected)
    validator = _RecordingValidator()

    with pytest.raises(OSError) as captured:
        ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert captured.value is expected
    assert reader.calls == [project_file]
    assert validator.calls == []


def test_load_validation_failure_is_propagated_after_model_construction(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project.toml"
    expected = ProjectConfigurationError("project assets are incomplete")
    reader = _RecordingReader(_valid_document())
    validator = _RecordingValidator(error=expected)

    with pytest.raises(ProjectConfigurationError) as captured:
        ProjectLoader(reader=reader, validator=_validator(validator)).load(project_file)

    assert captured.value is expected
    assert reader.calls == [project_file]
    assert len(validator.calls) == 1
    assert validator.calls[0].project_file == project_file
