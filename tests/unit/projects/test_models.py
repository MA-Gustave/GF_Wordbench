"""Unit tests for immutable active-project configuration models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.projects.models import (
    PROJECT_CONFIG_FILENAME,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectCheckScope,
    ProjectConfig,
    ProjectDiagnostic,
    ProjectDiagnosticSeverity,
    ProjectIdentity,
    ProjectValidationResult,
    SourceConfig,
    ValidationPolicy,
)


def _identity(**overrides: object) -> ProjectIdentity:
    values: dict[str, object] = {
        "id": "example-language",
        "name": "Langue d’exemple",
        "language_code": "Exa",
        "root": Path("."),
    }
    values.update(overrides)
    return ProjectIdentity(**cast("Any", values))


def _sources(**overrides: object) -> SourceConfig:
    values: dict[str, object] = {
        "directory": Path("src"),
        "glob": "**/*.gf",
        "include_regex": r"(?:^|/)Example.*\.gf$",
        "exclude_regex": r"(?:^|/)(?:build|vendor)/",
    }
    values.update(overrides)
    return SourceConfig(**cast("Any", values))


def _gf(**overrides: object) -> GFProjectConfig:
    values: dict[str, object] = {
        "path_parts": ("src", "../forbidden-not-used"),
        "minimum_version": "3.12",
    }
    values.update(overrides)
    if values["path_parts"] == ("src", "../forbidden-not-used"):
        values["path_parts"] = ("src", "rgl")
    return GFProjectConfig(**cast("Any", values))


def _modules(**overrides: object) -> ModuleTargets:
    values: dict[str, object] = {
        "entrypoints": (Path("Example.gf"),),
        "checkpoints": (
            Path("Lexicon.gf"),
            Path("Syntax/Grammar.gf"),
        ),
    }
    values.update(overrides)
    return ModuleTargets(**cast("Any", values))


def _validation(**overrides: object) -> ValidationPolicy:
    values: dict[str, object] = {
        "required_scenarios": ("parse-basic", "generate-basic"),
        "optional_scenarios": ("unicode-smoke",),
        "release_requires_pgf": True,
    }
    values.update(overrides)
    return ValidationPolicy(**cast("Any", values))


def _project_config(tmp_path: Path, **overrides: object) -> ProjectConfig:
    project_root = tmp_path / "active-project"
    default_sources = _sources()
    values: dict[str, object] = {
        "schema_id": PROJECT_SCHEMA_ID,
        "schema_version": PROJECT_SCHEMA_VERSION,
        "identity": _identity(),
        "sources": default_sources,
        "gf": _gf(),
        "modules": _modules(),
        "validation": _validation(),
        "project_file": project_root / PROJECT_CONFIG_FILENAME,
        "project_root": project_root,
        "source_root": project_root / default_sources.directory,
    }
    values.update(overrides)
    return ProjectConfig(**cast("Any", values))


def _diagnostic(tmp_path: Path, **overrides: object) -> ProjectDiagnostic:
    values: dict[str, object] = {
        "code": "PROJECT_SOURCE_MISSING",
        "severity": ProjectDiagnosticSeverity.ERROR,
        "field": "modules.entrypoints[0]",
        "message": "Le module déclaré est introuvable.",
        "source_file": tmp_path / "project.toml",
        "suggestion": "Créer le module ou corriger le chemin déclaré.",
        "subject": tmp_path / "src" / "Example.gf",
    }
    values.update(overrides)
    return ProjectDiagnostic(**cast("Any", values))


def test_project_model_constants_are_canonical() -> None:
    assert str(PROJECT_SCHEMA_ID) == "gf-wordbench.project"
    assert PROJECT_SCHEMA_VERSION == "1.0"
    assert PROJECT_CONFIG_FILENAME == "project.toml"


@pytest.mark.parametrize(
    ("enum_type", "members"),
    [
        (
            ProjectCheckScope,
            {
                "CONFIGURATION": "configuration",
                "NORMAL": "normal",
                "RELEASE": "release",
            },
        ),
        (
            ProjectDiagnosticSeverity,
            {
                "ERROR": "error",
                "WARNING": "warning",
                "INFO": "info",
            },
        ),
    ],
)
def test_project_enums_have_closed_canonical_values(
    enum_type: type[ProjectCheckScope] | type[ProjectDiagnosticSeverity],
    members: dict[str, str],
) -> None:
    assert {member.name: member.value for member in enum_type} == members


@pytest.mark.parametrize(
    "model_type",
    [
        ProjectIdentity,
        SourceConfig,
        GFProjectConfig,
        ModuleTargets,
        ValidationPolicy,
        ProjectConfig,
        ProjectDiagnostic,
        ProjectValidationResult,
    ],
)
def test_project_models_are_frozen_slotted_dataclasses(model_type: type[Any]) -> None:
    assert is_dataclass(model_type)
    assert model_type.__dataclass_params__.frozen
    assert "__slots__" in model_type.__dict__


def test_project_identity_accepts_unicode_display_name_and_portable_root() -> None:
    identity = _identity(root=Path("active-language"))

    assert identity.id == "example-language"
    assert identity.name == "Langue d’exemple"
    assert identity.language_code == "Exa"
    assert identity.root == Path("active-language")
    assert tuple(field.name for field in fields(identity)) == (
        "id",
        "name",
        "language_code",
        "root",
    )


def test_path_models_accept_native_nested_relative_paths() -> None:
    """Runtime Path values use the host separator after schema validation."""

    root = Path("nested") / "project"
    source_directory = Path("source") / "gf"
    checkpoint = Path("Syntax") / "Main.gf"

    identity = _identity(root=root)
    sources = _sources(directory=source_directory)
    modules = _modules(checkpoints=(checkpoint,))

    assert identity.root == root
    assert sources.directory == source_directory
    assert modules.checkpoints == (checkpoint,)
    assert identity.root.as_posix() == "nested/project"
    assert sources.directory.as_posix() == "source/gf"
    assert modules.checkpoints[0].as_posix() == "Syntax/Main.gf"


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"id": "Example-Language"}, ValueError, "project ID"),
        ({"id": ""}, ValueError, "project ID"),
        ({"id": 7}, TypeError, "project ID"),
        ({"name": ""}, ValueError, "project.name"),
        ({"name": " padded "}, ValueError, "project.name"),
        ({"name": "two\nlines"}, ValueError, "project.name"),
        ({"language_code": ""}, ValueError, "project.language_code"),
        ({"language_code": "Français"}, ValueError, "ASCII"),
        ({"language_code": "fr/CA"}, ValueError, "path separator"),
        ({"language_code": r"fr\CA"}, ValueError, "path separator"),
        ({"root": Path("..")}, ValueError, "parent traversal"),
        ({"root": Path("C:/project")}, ValueError, "project-relative"),
        ({"root": "project"}, TypeError, "pathlib.Path"),
    ],
)
def test_project_identity_rejects_invalid_values(
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _identity(**overrides)


def test_source_config_preserves_valid_selection_policy() -> None:
    sources = _sources()

    assert sources.directory == Path("src")
    assert sources.glob == "**/*.gf"
    assert sources.include_regex == r"(?:^|/)Example.*\.gf$"
    assert sources.exclude_regex == r"(?:^|/)(?:build|vendor)/"


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"directory": Path(".")}, ValueError, "non-root relative path"),
        ({"directory": Path("../src")}, ValueError, "parent traversal"),
        ({"directory": Path("/src")}, ValueError, "project-relative"),
        ({"directory": Path("C:/src")}, ValueError, "project-relative"),
        ({"directory": "src"}, TypeError, "pathlib.Path"),
        ({"glob": ""}, ValueError, "sources.glob"),
        ({"glob": "/absolute/*.gf"}, ValueError, "absolute path pattern"),
        ({"glob": "C:/absolute/*.gf"}, ValueError, "absolute path pattern"),
        ({"glob": "é/*.gf"}, ValueError, "ASCII"),
        ({"include_regex": "["}, ValueError, "include_regex"),
        ({"exclude_regex": "("}, ValueError, "exclude_regex"),
        ({"include_regex": 1}, TypeError, "must be a string"),
    ],
)
def test_source_config_rejects_nonportable_or_invalid_policy(
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _sources(**overrides)


def test_source_config_allows_empty_optional_regexes() -> None:
    sources = _sources(include_regex="", exclude_regex="")

    assert sources.include_regex == ""
    assert sources.exclude_regex == ""


def test_gf_project_config_preserves_declared_order_and_duplicates() -> None:
    config = _gf(path_parts=("src", "rgl", "src"), minimum_version="")

    assert config.path_parts == ("src", "rgl", "src")
    assert config.minimum_version == ""


@pytest.mark.parametrize(
    ("path_parts", "exception", "message"),
    [
        (["src"], TypeError, "must be a tuple"),
        (("",), ValueError, "must not be empty"),
        (("réseau",), ValueError, "ASCII"),
        ((r"rgl\lib",), ValueError, "canonical '/'"),
        (("../rgl",), ValueError, "parent traversal"),
        (("/opt/rgl",), ValueError, "absolute path"),
        (("C:/rgl",), ValueError, "absolute path"),
        (("$RGL",), ValueError, "environment-variable"),
        (("%RGL%",), ValueError, "environment-variable"),
        ((1,), TypeError, "must be a string"),
    ],
)
def test_gf_project_config_rejects_invalid_path_parts(
    path_parts: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _gf(path_parts=path_parts)


@pytest.mark.parametrize(
    ("minimum_version", "exception", "message"),
    [
        (" 3.12", ValueError, "leading or trailing whitespace"),
        ("3.12\n3.13", ValueError, "single-line"),
        (None, TypeError, "must be a string"),
    ],
)
def test_gf_project_config_rejects_invalid_minimum_version(
    minimum_version: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _gf(minimum_version=minimum_version)


def test_module_targets_preserve_project_owned_order() -> None:
    targets = _modules()

    assert targets.entrypoints == (Path("Example.gf"),)
    assert targets.checkpoints == (
        Path("Lexicon.gf"),
        Path("Syntax/Grammar.gf"),
    )


def test_module_targets_allow_empty_collections_at_model_boundary() -> None:
    targets = _modules(entrypoints=(), checkpoints=())

    assert targets.entrypoints == ()
    assert targets.checkpoints == ()


@pytest.mark.parametrize(
    ("field", "value", "exception", "message"),
    [
        ("entrypoints", [Path("Main.gf")], TypeError, "must be a tuple"),
        ("entrypoints", ("Main.gf",), TypeError, "pathlib.Path"),
        ("entrypoints", (Path("Main.txt"),), ValueError, "end in '.gf'"),
        ("entrypoints", (Path("../Main.gf"),), ValueError, "parent traversal"),
        ("entrypoints", (Path("/Main.gf"),), ValueError, "project-relative"),
        ("entrypoints", (Path("Main.gf"), Path("Main.gf")), ValueError, "duplicate"),
        ("checkpoints", (Path("C:/Main.gf"),), ValueError, "project-relative"),
    ],
)
def test_module_targets_reject_invalid_declarations(
    field: str,
    value: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _modules(**{field: value})


def test_validation_policy_exposes_required_then_optional_registry() -> None:
    policy = _validation()

    assert policy.required_scenarios == ("parse-basic", "generate-basic")
    assert policy.optional_scenarios == ("unicode-smoke",)
    assert policy.all_scenarios == (
        "parse-basic",
        "generate-basic",
        "unicode-smoke",
    )
    assert policy.release_requires_pgf is True


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"required_scenarios": ["parse-basic"]}, TypeError, "must be a tuple"),
        ({"required_scenarios": ("Parse-Basic",)}, ValueError, "scenario"),
        (
            {"required_scenarios": ("parse-basic", "parse-basic")},
            ValueError,
            "duplicate scenario ID",
        ),
        (
            {
                "required_scenarios": ("parse-basic",),
                "optional_scenarios": ("parse-basic",),
            },
            ValueError,
            "both required and optional",
        ),
        ({"release_requires_pgf": 1}, TypeError, "must be a boolean"),
    ],
)
def test_validation_policy_rejects_invalid_registry(
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _validation(**overrides)


def test_project_config_binds_persisted_and_resolved_paths(tmp_path: Path) -> None:
    config = _project_config(tmp_path)

    assert config.schema_id == PROJECT_SCHEMA_ID
    assert config.schema_version == PROJECT_SCHEMA_VERSION
    assert config.project_file == config.project_root / PROJECT_CONFIG_FILENAME
    assert config.source_root == config.project_root / config.sources.directory
    assert config.project_id == config.identity.id


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"schema_id": "gf-wordbench.other"}, ValueError, "Unsupported project schema ID"),
        ({"schema_id": "project"}, ValueError, "schema ID"),
        ({"schema_version": "2.0"}, ValueError, "Unsupported schema_version"),
        ({"schema_version": 1}, TypeError, "must be a string"),
        ({"identity": object()}, TypeError, "identity must be ProjectIdentity"),
        ({"sources": object()}, TypeError, "sources must be SourceConfig"),
        ({"gf": object()}, TypeError, "gf must be GFProjectConfig"),
        ({"modules": object()}, TypeError, "modules must be ModuleTargets"),
        ({"validation": object()}, TypeError, "validation must be ValidationPolicy"),
        ({"project_file": Path("project.toml")}, ValueError, "absolute runtime path"),
        ({"project_root": Path("project")}, ValueError, "absolute runtime path"),
        ({"source_root": Path("project/src")}, ValueError, "absolute runtime path"),
    ],
)
def test_project_config_rejects_invalid_schema_types_and_runtime_paths(
    tmp_path: Path,
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _project_config(tmp_path, **overrides)


def test_project_config_requires_exact_project_file_location(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="project_root/project.toml"):
        _project_config(
            tmp_path,
            project_file=tmp_path / "active-project" / "other.toml",
        )


def test_project_config_requires_source_root_from_source_declaration(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source_root must equal"):
        _project_config(
            tmp_path,
            source_root=tmp_path / "active-project" / "grammar",
        )


def test_project_config_rejects_unresolved_parent_traversal(tmp_path: Path) -> None:
    project_root = tmp_path / "active-project"

    with pytest.raises(ValueError, match="unresolved parent traversal"):
        _project_config(
            tmp_path,
            project_file=project_root / "nested" / ".." / "project.toml",
        )


def test_project_diagnostic_preserves_unicode_and_optional_subject(tmp_path: Path) -> None:
    diagnostic = _diagnostic(tmp_path)
    without_subject = _diagnostic(tmp_path, subject=None)

    assert diagnostic.code == "PROJECT_SOURCE_MISSING"
    assert diagnostic.severity is ProjectDiagnosticSeverity.ERROR
    assert diagnostic.field == "modules.entrypoints[0]"
    assert diagnostic.message == "Le module déclaré est introuvable."
    assert diagnostic.source_file == tmp_path / "project.toml"
    assert diagnostic.subject == tmp_path / "src" / "Example.gf"
    assert without_subject.subject is None


@pytest.mark.parametrize(
    ("overrides", "exception", "message"),
    [
        ({"code": ""}, ValueError, "diagnostic.code"),
        ({"code": "ÉCHEC"}, ValueError, "ASCII"),
        ({"severity": "error"}, TypeError, "ProjectDiagnosticSeverity"),
        ({"field": ""}, ValueError, "diagnostic.field"),
        ({"message": ""}, ValueError, "diagnostic.message"),
        ({"suggestion": ""}, ValueError, "diagnostic.suggestion"),
        ({"source_file": Path("project.toml")}, ValueError, "absolute runtime path"),
        ({"source_file": "project.toml"}, TypeError, "pathlib.Path"),
        ({"subject": Path("src/Main.gf")}, ValueError, "absolute runtime path"),
    ],
)
def test_project_diagnostic_rejects_invalid_values(
    tmp_path: Path,
    overrides: dict[str, object],
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        _diagnostic(tmp_path, **overrides)


def test_project_validation_result_filters_diagnostics_in_original_order(
    tmp_path: Path,
) -> None:
    warning = _diagnostic(
        tmp_path,
        code="PROJECT_WARNING",
        severity=ProjectDiagnosticSeverity.WARNING,
        message="Avertissement.",
    )
    error = _diagnostic(tmp_path)
    info = _diagnostic(
        tmp_path,
        code="PROJECT_INFO",
        severity=ProjectDiagnosticSeverity.INFO,
        message="Information.",
    )

    result = ProjectValidationResult((warning, error, info))

    assert result.diagnostics == (warning, error, info)
    assert result.errors == (error,)
    assert result.warnings == (warning,)
    assert result.ok is False


def test_project_validation_result_is_ok_without_errors(tmp_path: Path) -> None:
    warning = _diagnostic(
        tmp_path,
        code="PROJECT_WARNING",
        severity=ProjectDiagnosticSeverity.WARNING,
    )

    assert ProjectValidationResult().ok is True
    assert ProjectValidationResult((warning,)).ok is True


@pytest.mark.parametrize(
    ("diagnostics", "exception", "message"),
    [
        ([], TypeError, "must be a tuple"),
        ((object(),), TypeError, r"diagnostics\[0\] must be ProjectDiagnostic"),
    ],
)
def test_project_validation_result_rejects_invalid_diagnostics(
    diagnostics: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        ProjectValidationResult(cast("Any", diagnostics))


def test_project_models_are_immutable_at_runtime(tmp_path: Path) -> None:
    values: tuple[tuple[object, str], ...] = (
        (_identity(), "name"),
        (_sources(), "glob"),
        (_gf(), "minimum_version"),
        (_modules(), "entrypoints"),
        (_validation(), "release_requires_pgf"),
        (_project_config(tmp_path), "schema_version"),
        (_diagnostic(tmp_path), "message"),
        (ProjectValidationResult(), "diagnostics"),
    )

    for value, attribute in values:
        with pytest.raises(FrozenInstanceError):
            setattr(value, attribute, None)
        assert not hasattr(value, "__dict__")
