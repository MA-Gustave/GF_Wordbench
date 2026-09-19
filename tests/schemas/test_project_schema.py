"""Contract tests for the canonical ``project.toml`` schema."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.kernel.errors import SchemaValidationError, UnsupportedVersionError
from gf_wordbench.projects.models import (
    PROJECT_CONFIG_FILENAME,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    GFProjectConfig,
    ModuleTargets,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from gf_wordbench.projects.schema import (
    ProjectSchemaCompatibility,
    parse_project_document,
    validate_project_schema,
    validate_project_template_schema,
)

Mutator = Callable[[dict[str, Any]], None]


def canonical_document() -> dict[str, Any]:
    return {
        "schema_id": "gf-wordbench.project",
        "schema_version": "1.0",
        "project": {
            "id": "example-project",
            "name": "Example Language",
            "language_code": "eng",
            "root": ".",
        },
        "sources": {
            "directory": "grammar",
            "glob": "**/*.gf",
            "include_regex": r".*\.gf$",
            "exclude_regex": r"(^|/)(build|dist)(/|$)",
        },
        "gf": {"path_parts": [".", "vendor/rgl"], "minimum_version": "3.12"},
        "modules": {
            "entrypoints": ["Main.gf", "api/Public.gf"],
            "checkpoints": ["Syntax.gf"],
        },
        "validation": {
            "required_scenarios": ["smoke", "syntax-check"],
            "optional_scenarios": ["extended-coverage"],
            "release_requires_pgf": True,
        },
    }


def template_document() -> dict[str, Any]:
    document = canonical_document()
    document["project"] = {
        "id": "<PROJECT_ID>",
        "name": "<PROJECT_NAME>",
        "language_code": "<LANGUAGE_CODE>",
        "root": ".",
    }
    document["sources"] = {
        "directory": "<SOURCE_DIRECTORY>",
        "glob": "<SOURCE_GLOB>",
        "include_regex": "",
        "exclude_regex": "",
    }
    document["gf"] = {"path_parts": [".", "<GF_PATH_PART>"], "minimum_version": ""}
    document["modules"] = {
        "entrypoints": ["<ENTRYPOINT>.gf"],
        "checkpoints": ["<CHECKPOINT>.gf"],
    }
    document["validation"] = {
        "required_scenarios": ["<REQUIRED_SCENARIO>"],
        "optional_scenarios": ["<OPTIONAL_SCENARIO>"],
        "release_requires_pgf": True,
    }
    return document


def set_value(path: str, value: Any) -> Mutator:
    parts = path.split(".")

    def apply(document: dict[str, Any]) -> None:
        target = document
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value

    return apply


def remove_value(path: str) -> Mutator:
    parts = path.split(".")

    def apply(document: dict[str, Any]) -> None:
        target = document
        for part in parts[:-1]:
            target = target[part]
        del target[parts[-1]]

    return apply


def assert_invalid(
    mutator: Mutator,
    message: str,
    error_type: type[Exception] = SchemaValidationError,
) -> None:
    document = canonical_document()
    mutator(document)
    with pytest.raises(error_type, match=message):
        validate_project_schema(document)


def test_schema_identity_constants_are_locked() -> None:
    assert str(PROJECT_SCHEMA_ID) == "gf-wordbench.project"
    assert PROJECT_SCHEMA_VERSION == "1.0"
    assert PROJECT_CONFIG_FILENAME == "project.toml"


def test_validation_returns_a_detached_order_preserving_copy() -> None:
    document = canonical_document()
    document["gf"]["path_parts"] = ["z", ".", "a", "z"]
    validated = validate_project_schema(document)

    assert validated == document
    assert validated is not document
    for table in ("project", "sources", "gf", "modules", "validation"):
        assert validated[table] is not document[table]
    assert validated["gf"]["path_parts"] is not document["gf"]["path_parts"]
    assert validated["gf"]["path_parts"] == ["z", ".", "a", "z"]

    document["project"]["name"] = "Mutated"
    document["gf"]["path_parts"].append("later")
    assert validated["project"]["name"] == "Example Language"
    assert validated["gf"]["path_parts"] == ["z", ".", "a", "z"]


def test_empty_optional_values_are_valid() -> None:
    document = canonical_document()
    document["sources"].update(include_regex="", exclude_regex="")
    document["gf"].update(path_parts=[], minimum_version="")
    document["modules"]["checkpoints"] = []
    document["validation"].update(required_scenarios=[], optional_scenarios=[])
    assert validate_project_schema(document) == document


def test_error_reports_explicit_source() -> None:
    document = canonical_document()
    document["schema_id"] = "wrong"
    source = Path("project/project.toml")
    with pytest.raises(SchemaValidationError) as raised:
        validate_project_schema(document, source=source)
    assert str(raised.value).startswith(f"{source}: $.schema_id:")


def test_document_and_option_types_are_enforced() -> None:
    with pytest.raises(SchemaValidationError, match=r"\$: must be a TOML table"):
        validate_project_schema([])  # type: ignore[arg-type]

    document = canonical_document()
    document[1] = "invalid"  # type: ignore[index]
    with pytest.raises(SchemaValidationError, match="non-string key"):
        validate_project_schema(document)

    with pytest.raises(TypeError, match="compatibility must be"):
        validate_project_schema(canonical_document(), compatibility="strict")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="allow_placeholders must be"):
        validate_project_schema(canonical_document(), allow_placeholders=1)  # type: ignore[arg-type]


@pytest.mark.parametrize("version", ["1", "v1.0", "01.0", "1.00", "1.0.0", ""])
def test_malformed_schema_versions_are_rejected(version: str) -> None:
    assert_invalid(set_value("schema_version", version), "MAJOR.MINOR decimal form")


@pytest.mark.parametrize("version", ["0.9", "2.0", "2.1"])
def test_unsupported_major_versions_are_rejected(version: str) -> None:
    assert_invalid(
        set_value("schema_version", version),
        "unsupported major version",
        UnsupportedVersionError,
    )


def test_strict_and_forward_minor_compatibility() -> None:
    document = canonical_document()
    document["schema_version"] = "1.1"
    with pytest.raises(UnsupportedVersionError, match="unsupported version"):
        validate_project_schema(document)

    document["future_root"] = True
    document["project"]["future_project"] = "value"
    document["validation"]["future_validation"] = False
    validated = validate_project_schema(
        document,
        compatibility=ProjectSchemaCompatibility.FORWARD_MINOR,
    )
    assert validated["schema_version"] == "1.1"
    assert "future_root" not in validated
    assert "future_project" not in validated["project"]
    assert "future_validation" not in validated["validation"]

    document["schema_version"] = "0.9"
    with pytest.raises(UnsupportedVersionError, match="unsupported major"):
        validate_project_schema(
            document,
            compatibility=ProjectSchemaCompatibility.FORWARD_MINOR,
        )


def test_wrong_schema_id_and_unknown_fields_are_rejected() -> None:
    assert_invalid(
        set_value("schema_id", "gf-wordbench.other"),
        r"expected 'gf-wordbench\.project'",
    )

    document = canonical_document()
    document["unknown"] = True
    with pytest.raises(SchemaValidationError, match="unknown fields: unknown"):
        validate_project_schema(document)

    for table in ("project", "sources", "gf", "modules", "validation"):
        document = canonical_document()
        document[table]["unknown"] = True
        with pytest.raises(SchemaValidationError, match="unknown fields: unknown"):
            validate_project_schema(document)


@pytest.mark.parametrize("table", ["project", "sources", "gf", "modules", "validation"])
def test_required_tables_exist_and_are_mappings(table: str) -> None:
    assert_invalid(remove_value(table), rf"missing required fields: {table}")
    assert_invalid(set_value(table, []), rf"\$\.{table}: must be a TOML table")


@pytest.mark.parametrize(
    ("path", "field"),
    [
        ("schema_id", "schema_id"),
        ("schema_version", "schema_version"),
        ("project.id", "id"),
        ("project.name", "name"),
        ("project.language_code", "language_code"),
        ("project.root", "root"),
        ("sources.directory", "directory"),
        ("sources.glob", "glob"),
        ("sources.include_regex", "include_regex"),
        ("sources.exclude_regex", "exclude_regex"),
        ("gf.minimum_version", "minimum_version"),
    ],
)
def test_required_string_fields_exist_and_are_strings(path: str, field: str) -> None:
    assert_invalid(
        remove_value(path),
        rf"missing required field(?:s: | )'?{field}'?",
    )
    assert_invalid(set_value(path, 42), "must be a string")


@pytest.mark.parametrize(
    "path",
    [
        "gf.path_parts",
        "modules.entrypoints",
        "modules.checkpoints",
        "validation.required_scenarios",
        "validation.optional_scenarios",
    ],
)
def test_array_fields_require_string_arrays(path: str) -> None:
    assert_invalid(set_value(path, "not-an-array"), "array of strings")
    assert_invalid(set_value(path, ["valid", 2]), "must be a string")


def test_release_requires_pgf_is_boolean() -> None:
    assert_invalid(set_value("validation.release_requires_pgf", 1), "must be a boolean")


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        ("project.id", "", "must not be empty"),
        ("project.id", " project ", "outer whitespace"),
        ("project.id", "some/path", "not a filesystem path"),
        ("project.id", "some\\path", "not a filesystem path"),
        ("project.id", ".", "stable identifier"),
        ("project.language_code", "../eng", "not a filesystem path"),
        ("project.name", "", "must not be empty"),
        ("project.name", " Example ", "outer whitespace"),
        ("project.name", "Line\nBreak", "control characters"),
        ("project.id", "<PROJECT_ID>", "unresolved template placeholder"),
        ("project.name", "<PROJECT_NAME>", "unresolved template placeholder"),
        ("project.language_code", "<LANGUAGE>", "unresolved template placeholder"),
    ],
)
def test_project_identity_text_rules(path: str, value: str, message: str) -> None:
    assert_invalid(set_value(path, value), message)


@pytest.mark.parametrize("value", ["project", "./", "../project", ""])
def test_project_root_is_fixed_to_dot(value: str) -> None:
    assert_invalid(set_value("project.root", value), "canonical value '.'")


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "must not be empty"),
        (".", "must identify a file or subpath"),
        ("/grammar", "must be relative"),
        ("C:/grammar", "drive letter"),
        ("grammar\\src", "canonical separator"),
        ("../grammar", "parent traversal"),
        ("grammar/./src", "canonical POSIX form"),
        ("$HOME/grammar", "environment-variable reference"),
        ("${SOURCE_ROOT}", "environment-variable reference"),
        ("%SOURCE_ROOT%/grammar", "environment-variable reference"),
        ("<SOURCE_ROOT>", "unresolved template placeholder"),
    ],
)
def test_source_directory_is_portable(value: str, message: str) -> None:
    assert_invalid(set_value("sources.directory", value), message)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "must not be empty"),
        ("/**/*.gf", "project-relative glob"),
        ("../**/*.gf", "parent traversal"),
        ("grammar\\*.gf", "canonical separator"),
        ("C:/*.gf", "drive letter"),
        ("$SOURCE_GLOB", "environment-variable reference"),
        ("<SOURCE_GLOB>", "unresolved template placeholder"),
    ],
)
def test_source_glob_is_portable(value: str, message: str) -> None:
    assert_invalid(set_value("sources.glob", value), message)


@pytest.mark.parametrize("path", ["sources.include_regex", "sources.exclude_regex"])
def test_source_regexes_compile(path: str) -> None:
    assert_invalid(set_value(path, "[unterminated"), "invalid regular expression")


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("/rgl", "must be relative"),
        ("C:/rgl", "drive letter"),
        ("vendor\\rgl", "canonical separator"),
        ("../rgl", "parent traversal"),
        ("vendor/./rgl", "canonical POSIX form"),
        ("$RGL", "environment-variable reference"),
        ("<RGL>", "unresolved template placeholder"),
    ],
)
def test_gf_path_parts_are_portable(value: str, message: str) -> None:
    document = canonical_document()
    document["gf"]["path_parts"] = ["first", value, "last"]
    with pytest.raises(SchemaValidationError, match=message):
        validate_project_schema(document)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (" 3.12", "outer whitespace"),
        ("3.12 ", "outer whitespace"),
        ("3.12\nrelease", "control characters"),
    ],
)
def test_minimum_version_is_single_line_text(value: str, message: str) -> None:
    assert_invalid(set_value("gf.minimum_version", value), message)


def test_entrypoints_are_required_and_module_overlap_is_allowed() -> None:
    assert_invalid(
        set_value("modules.entrypoints", []),
        "must contain at least one module target",
    )
    document = canonical_document()
    document["modules"].update(
        entrypoints=["B.gf", "A.gf"],
        checkpoints=["A.gf", "C.gf"],
    )
    validated = validate_project_schema(document)
    assert validated["modules"]["entrypoints"] == ["B.gf", "A.gf"]
    assert validated["modules"]["checkpoints"] == ["A.gf", "C.gf"]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "must not be empty"),
        ("Main.gfo", "must end in '.gf'"),
        ("/Main.gf", "must be relative"),
        ("C:/Main.gf", "drive letter"),
        ("dir\\Main.gf", "canonical separator"),
        ("../Main.gf", "parent traversal"),
        ("dir/./Main.gf", "canonical POSIX form"),
        ("$MODULE/Main.gf", "environment-variable reference"),
        ("<ENTRYPOINT>.gf", "unresolved template placeholder"),
    ],
)
def test_module_targets_are_portable_gf_paths(value: str, message: str) -> None:
    document = canonical_document()
    document["modules"]["entrypoints"] = [value]
    with pytest.raises(SchemaValidationError, match=message):
        validate_project_schema(document)


def test_module_target_duplicates_are_rejected() -> None:
    for field in ("entrypoints", "checkpoints"):
        document = canonical_document()
        document["modules"][field] = ["Repeated.gf", "Repeated.gf"]
        with pytest.raises(SchemaValidationError, match="duplicates normalized target"):
            validate_project_schema(document)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "must not be empty"),
        ("_hidden", "must use letters"),
        ("scenario/name", "must use letters"),
        ("scenario.gfs", "must use letters"),
        ("white space", "must use letters"),
        ("<SCENARIO>", "unresolved template placeholder"),
    ],
)
def test_scenario_ids_use_canonical_grammar(value: str, message: str) -> None:
    document = canonical_document()
    document["validation"]["required_scenarios"] = [value]
    with pytest.raises(SchemaValidationError, match=message):
        validate_project_schema(document)


def test_scenario_uniqueness_overlap_and_order() -> None:
    for field in ("required_scenarios", "optional_scenarios"):
        document = canonical_document()
        document["validation"][field] = ["same", "same"]
        with pytest.raises(SchemaValidationError, match="duplicates scenario ID"):
            validate_project_schema(document)

    document = canonical_document()
    document["validation"].update(
        required_scenarios=["shared", "required"],
        optional_scenarios=["optional", "shared"],
    )
    with pytest.raises(SchemaValidationError, match="overlap: shared"):
        validate_project_schema(document)

    document["validation"].update(
        required_scenarios=["z", "a", "middle"],
        optional_scenarios=[],
    )
    assert validate_project_schema(document)["validation"]["required_scenarios"] == [
        "z",
        "a",
        "middle",
    ]


def test_template_validator_accepts_only_documented_placeholder_positions() -> None:
    validated = validate_project_template_schema(template_document())
    assert validated["project"]["id"] == "<PROJECT_ID>"
    assert validated["modules"]["entrypoints"] == ["<ENTRYPOINT>.gf"]
    assert validated["validation"]["required_scenarios"] == ["<REQUIRED_SCENARIO>"]

    document = template_document()
    document["project"]["root"] = "<PROJECT_ROOT>"
    with pytest.raises(SchemaValidationError, match="canonical value '.'"):
        validate_project_template_schema(document)

    document = template_document()
    document["modules"]["entrypoints"] = ["<ENTRYPOINT>"]
    with pytest.raises(SchemaValidationError, match="must end in '.gf'"):
        validate_project_template_schema(document)


def test_parse_builds_complete_models_without_filesystem_io(tmp_path: Path) -> None:
    project_root = tmp_path / "does-not-exist"
    source_file = project_root / "project.toml"
    config = parse_project_document(canonical_document(), source_file=source_file)  # type: ignore[arg-type]

    assert isinstance(config, ProjectConfig)
    assert isinstance(config.identity, ProjectIdentity)
    assert isinstance(config.sources, SourceConfig)
    assert isinstance(config.gf, GFProjectConfig)
    assert isinstance(config.modules, ModuleTargets)
    assert isinstance(config.validation, ValidationPolicy)
    assert str(config.schema_id) == "gf-wordbench.project"
    assert config.schema_version == "1.0"
    assert str(config.identity.id) == "example-project"
    assert config.identity.root == Path(".")
    assert config.sources.directory == Path("grammar")
    assert config.gf.path_parts == (".", "vendor/rgl")
    assert config.modules.entrypoints == (Path("Main.gf"), Path("api/Public.gf"))
    assert tuple(map(str, config.validation.all_scenarios)) == (
        "smoke",
        "syntax-check",
        "extended-coverage",
    )
    assert config.project_file == source_file
    assert config.project_root == project_root
    assert config.source_root == project_root / "grammar"
    assert not project_root.exists()


def test_parse_requires_canonical_absolute_project_path(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="source_file must be pathlib.Path"):
        parse_project_document(
            canonical_document(),  # type: ignore[arg-type]
            source_file="/project/project.toml",  # type: ignore[arg-type]
        )
    with pytest.raises(SchemaValidationError, match="explicit absolute"):
        parse_project_document(
            canonical_document(),  # type: ignore[arg-type]
            source_file=Path("project/project.toml"),
        )
    with pytest.raises(SchemaValidationError, match="canonical project.toml path"):
        parse_project_document(
            canonical_document(),  # type: ignore[arg-type]
            source_file=tmp_path / "project" / "other.toml",
        )
    with pytest.raises(SchemaValidationError, match="lexically normalized"):
        parse_project_document(
            canonical_document(),  # type: ignore[arg-type]
            source_file=tmp_path / "project" / ".." / "project" / "project.toml",
        )


def test_parse_revalidates_input_document(tmp_path: Path) -> None:
    document = canonical_document()
    document["validation"]["required_scenarios"] = ["duplicate", "duplicate"]
    with pytest.raises(SchemaValidationError, match="duplicates scenario ID"):
        parse_project_document(
            document,  # type: ignore[arg-type]
            source_file=tmp_path / "project" / "project.toml",
        )
