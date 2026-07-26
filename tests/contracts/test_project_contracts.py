from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
from collections.abc import Mapping
from dataclasses import is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

PROJECT_PACKAGE: Final = "gf_wordbench.projects"

OWNER_EXPORTS: Final[Mapping[str, frozenset[str]]] = {
    "models": frozenset(
        {
            "PROJECT_CONFIG_FILENAME",
            "PROJECT_SCHEMA_ID",
            "PROJECT_SCHEMA_VERSION",
            "GFProjectConfig",
            "ModuleTargets",
            "ProjectCheckScope",
            "ProjectConfig",
            "ProjectDiagnostic",
            "ProjectDiagnosticSeverity",
            "ProjectIdentity",
            "ProjectValidationResult",
            "SourceConfig",
            "ValidationPolicy",
        }
    ),
    "paths": frozenset(
        {
            "PROJECT_CONFIG_FILENAME",
            "PROJECT_DOCS_DIRECTORY",
            "PROJECT_GOLD_DIRECTORY",
            "PROJECT_INPUTS_DIRECTORY",
            "PROJECT_README_FILENAME",
            "PROJECT_ROOT_DECLARATION",
            "PROJECT_SCENARIOS_DIRECTORY",
            "PROJECT_VALIDATION_DIRECTORY",
            "ProjectPaths",
            "normalize_project_root_declaration",
            "resolve_module_path",
            "resolve_project_paths",
            "resolve_project_relative_path",
            "resolve_scenario_path",
            "resolve_source_relative_path",
            "resolve_source_root",
        }
    ),
    "policies": frozenset(
        {
            "REQUIRED_PROJECT_ASSETS",
            "contains_template_placeholder",
            "deduplicate_declared_path_parts",
            "enforce_project_invariants",
            "find_unresolved_placeholder",
            "is_recommended_project_id",
            "is_recommended_scenario_id",
            "normalized_portable_path_key",
            "validate_language_code",
            "validate_minimum_version",
            "validate_module_targets",
            "validate_optional_regex",
            "validate_portable_project_path",
            "validate_project_id",
            "validate_project_name",
            "validate_project_root",
            "validate_project_semantics",
            "validate_release_requires_pgf",
            "validate_scenario_id",
            "validate_scenario_policy",
            "validate_source_glob",
        }
    ),
    "ports": frozenset(
        {
            "ArchiveFormat",
            "ArchiveReceipt",
            "ClockPort",
            "LifecycleLease",
            "LifecycleLockRequest",
            "ProjectArchiveWriter",
            "ProjectConfigReader",
            "ProjectConfigWriter",
            "ProjectFilesystem",
            "ProjectLifecycleLock",
            "ProjectMigrationWorkspacePort",
            "ProjectTemplateSource",
            "TreeEntry",
            "TreeEntryKind",
        }
    ),
    "schema": frozenset(
        {
            "GFTable",
            "ModulesTable",
            "ProjectDocument",
            "ProjectSchemaCompatibility",
            "ProjectTable",
            "SourcesTable",
            "ValidationTable",
            "parse_project_document",
            "validate_project_schema",
            "validate_project_template_schema",
        }
    ),
    "toml_adapter": frozenset(
        {
            "ProjectTomlDecodeError",
            "ProjectTomlEncodeError",
            "ProjectTomlError",
            "TomlDocument",
            "TomlScalar",
            "TomlValue",
            "parse_project_toml",
            "read_project_toml",
            "render_project_toml",
            "write_project_toml",
        }
    ),
    "loader": frozenset({"ProjectLoader", "load_project_config"}),
    "validator": frozenset(
        {
            "ProjectValidator",
            "check_project",
            "ensure_project_valid",
            "validate_project",
        }
    ),
    "initializer": frozenset(
        {
            "ProjectInitializationRequest",
            "ProjectInitializationResult",
            "ProjectInitializer",
            "initialize_project",
        }
    ),
    "resetter": frozenset(
        {
            "LifecycleErrorCategory",
            "PhaseRecord",
            "PhaseStatus",
            "PreservationMode",
            "ProjectResetError",
            "ProjectResetter",
            "ResetFailure",
            "ResetOperations",
            "ResetOutcome",
            "ResetPhase",
            "ResetPlan",
            "ResetPlanner",
            "ResetRequest",
            "ResetResult",
            "ResetScope",
            "plan_project_reset",
            "reset_project",
        }
    ),
    "migrator": frozenset(
        {
            "ProjectMigrationAction",
            "ProjectMigrationActionKind",
            "ProjectMigrationAsset",
            "ProjectMigrationDestinationInspection",
            "ProjectMigrationIssue",
            "ProjectMigrationPlan",
            "ProjectMigrationRequest",
            "ProjectMigrationResult",
            "ProjectMigrationSourceInspection",
            "ProjectMigrationStatus",
            "ProjectMigrationStrategy",
            "ProjectMigrationVerification",
            "ProjectMigrationWriteReceipt",
            "ProjectMigrator",
            "migrate_project",
            "plan_project_migration",
        }
    ),
    "public": frozenset(
        {
            "ProjectConfig",
            "check_project",
            "initialize_project",
            "load_project_config",
            "migrate_project",
            "plan_project_migration",
            "plan_project_reset",
            "reset_project",
            "resolve_project_paths",
        }
    ),
}

PUBLIC_OWNER: Final[Mapping[str, str]] = {
    "ProjectConfig": "models",
    "check_project": "validator",
    "initialize_project": "initializer",
    "load_project_config": "loader",
    "migrate_project": "migrator",
    "plan_project_migration": "migrator",
    "plan_project_reset": "resetter",
    "reset_project": "resetter",
    "resolve_project_paths": "paths",
}

MODEL_TYPES: Final = (
    "ProjectIdentity",
    "SourceConfig",
    "GFProjectConfig",
    "ModuleTargets",
    "ValidationPolicy",
    "ProjectConfig",
    "ProjectDiagnostic",
    "ProjectValidationResult",
)

FORBIDDEN_SHARED_MODEL_NAMES: Final = frozenset(
    {
        "ProjectInitializationRequest",
        "ProjectInitializationResult",
        "ProjectMigrationAction",
        "ProjectMigrationIssue",
        "ProjectMigrationPlan",
        "ProjectMigrationRequest",
        "ProjectMigrationResult",
        "ProjectMigrationStatus",
        "ProjectMigrationStrategy",
        "ProjectResetError",
        "ProjectTemplateStage",
        "ProjectValidationReport",
        "ProjectWorkspace",
        "ResetPlan",
        "ResetRequest",
        "ResetResult",
    }
)

FORBIDDEN_PATH_NAMES: Final = frozenset(
    {"is_within", "module_path", "resolve_project_config", "scenario_path"}
)

FORBIDDEN_PORT_NAMES: Final = frozenset(
    {"ProjectFileSystem", "ProjectWorkspace"}
)

DOMAIN_MODULES: Final = (
    "models",
    "paths",
    "policies",
    "ports",
    "schema",
)

FORBIDDEN_DOMAIN_PREFIXES: Final = (
    "gf_wordbench.config",
    "gf_wordbench.diagnostics",
    "gf_wordbench.entrypoints",
    "gf_wordbench.infrastructure",
    "gf_wordbench.reporting",
    "gf_wordbench.runs",
    "gf_wordbench.state",
    "gf_wordbench.validation",
)


def _module_name(short_name: str) -> str:
    return f"{PROJECT_PACKAGE}.{short_name}"


def _import(short_name: str) -> ModuleType:
    return importlib.import_module(_module_name(short_name))


def _source_path(short_name: str) -> Path:
    spec = importlib.util.find_spec(_module_name(short_name))
    assert spec is not None, f"missing module spec for {_module_name(short_name)}"
    assert spec.origin is not None, f"missing source path for {_module_name(short_name)}"
    path = Path(spec.origin)
    assert path.is_file(), f"missing source file for {_module_name(short_name)}"
    return path


def _tree(short_name: str) -> ast.Module:
    return ast.parse(_source_path(short_name).read_text(encoding="utf-8"))


def _top_level_definitions(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return frozenset(names)


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                modules.append(node.module)
    return tuple(modules)


def _imports_from(tree: ast.Module, module: str) -> frozenset[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            imported.update(alias.name for alias in node.names)
    return frozenset(imported)


def _parameter_names(value: object) -> tuple[str, ...]:
    return tuple(inspect.signature(value).parameters)


@pytest.mark.contract
@pytest.mark.parametrize("short_name", tuple(OWNER_EXPORTS))
def test_project_owner_exports_are_exact(short_name: str) -> None:
    module = _import(short_name)
    exported = getattr(module, "__all__", None)
    assert isinstance(exported, (list, tuple))
    assert frozenset(exported) == OWNER_EXPORTS[short_name]
    assert len(exported) == len(set(exported))
    for name in exported:
        assert hasattr(module, name), f"{_module_name(short_name)} exports missing {name}"


@pytest.mark.contract
def test_project_domain_models_are_immutable_and_slotted() -> None:
    models = _import("models")
    for name in MODEL_TYPES:
        value = getattr(models, name)
        assert is_dataclass(value), name
        assert value.__dataclass_params__.frozen, name
        assert "__slots__" in value.__dict__, name


@pytest.mark.contract
def test_projects_models_owns_only_shared_project_models() -> None:
    definitions = _top_level_definitions(_tree("models"))
    assert definitions.isdisjoint(FORBIDDEN_SHARED_MODEL_NAMES)
    models = _import("models")
    assert not hasattr(models, "ProjectValidationReport")
    assert models.PROJECT_CONFIG_FILENAME == "project.toml"
    assert str(models.PROJECT_SCHEMA_ID) == "gf-wordbench.project"
    assert models.PROJECT_SCHEMA_VERSION == "1.0"


@pytest.mark.contract
def test_project_paths_exposes_only_canonical_path_operations() -> None:
    paths = _import("paths")
    definitions = _top_level_definitions(_tree("paths"))
    assert definitions.isdisjoint(FORBIDDEN_PATH_NAMES)
    assert _parameter_names(paths.resolve_project_paths) == ("config",)
    assert _parameter_names(paths.resolve_module_path) == (
        "source_root",
        "module_path",
    )
    assert _parameter_names(paths.resolve_scenario_path) == (
        "project_paths",
        "scenario_id",
    )


@pytest.mark.contract
def test_project_ports_are_canonical_and_mechanism_neutral() -> None:
    tree = _tree("ports")
    definitions = _top_level_definitions(tree)
    assert definitions.isdisjoint(FORBIDDEN_PORT_NAMES)
    assert "ProjectMigrationWorkspacePort" in definitions
    assert "AbstractContextManager" in _imports_from(tree, "contextlib")
    assert "AbstractContextManager" not in _imports_from(tree, "collections.abc")
    ports = _import("ports")
    for name in (
        "ProjectFilesystem",
        "ProjectConfigReader",
        "ProjectConfigWriter",
        "ProjectTemplateSource",
        "ProjectArchiveWriter",
        "ProjectLifecycleLock",
        "ProjectMigrationWorkspacePort",
    ):
        assert getattr(ports, name)._is_protocol


@pytest.mark.contract
def test_filesystem_adapter_reuses_port_owned_tree_models() -> None:
    tree = _tree("filesystem_adapter")
    definitions = _top_level_definitions(tree)
    assert "TreeEntry" not in definitions
    assert "TreeEntryKind" not in definitions
    imported = _imports_from(tree, "ports") | _imports_from(tree, "gf_wordbench.projects.ports")
    assert {"TreeEntry", "TreeEntryKind", "ProjectFilesystem"}.issubset(imported)
    adapter = _import("filesystem_adapter")
    ports = _import("ports")
    assert isinstance(adapter.ProjectFilesystemAdapter(), ports.ProjectFilesystem)


@pytest.mark.contract
def test_project_schema_has_the_canonical_parser_contract() -> None:
    schema = _import("schema")
    signature = inspect.signature(schema.parse_project_document)
    assert tuple(signature.parameters) == ("document", "source_file")
    assert signature.parameters["source_file"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "resolve_project_config" not in _top_level_definitions(_tree("schema"))


@pytest.mark.contract
def test_project_loader_uses_registered_project_owners_only() -> None:
    tree = _tree("loader")
    assert "ProjectConfigReader" in _imports_from(tree, "ports")
    assert "parse_project_document" in _imports_from(tree, "schema")
    assert "enforce_project_invariants" in _imports_from(tree, "policies")
    assert "ProjectValidator" in _imports_from(tree, "validator")
    imports = _imported_modules(tree)
    prohibited = (
        "subprocess",
        "gf_wordbench.state",
        "gf_wordbench.runs",
        "gf_wordbench.entrypoints",
    )
    assert not any(
        name == prefix or name.startswith(f"{prefix}.")
        for name in imports
        for prefix in prohibited
    )
    loader = _import("loader")
    assert _parameter_names(loader.load_project_config) == (
        "project_file",
        "reader",
        "validator",
    )


@pytest.mark.contract
def test_project_validator_uses_canonical_paths_and_result_type() -> None:
    tree = _tree("validator")
    imported_paths = _imports_from(tree, "paths")
    assert {
        "resolve_module_path",
        "resolve_project_paths",
        "resolve_scenario_path",
    }.issubset(imported_paths)
    assert imported_paths.isdisjoint(FORBIDDEN_PATH_NAMES)
    definitions = _top_level_definitions(tree)
    assert {"ProjectValidator", "check_project"}.issubset(definitions)
    assert "ProjectValidationReport" not in definitions
    validator = _import("validator")
    models = _import("models")
    assert inspect.signature(validator.check_project).return_annotation in {
        models.ProjectValidationResult,
        "ProjectValidationResult",
    }


@pytest.mark.contract
def test_initializer_reset_and_migration_models_stay_with_their_use_cases() -> None:
    models_tree = _tree("models")
    assert _top_level_definitions(models_tree).isdisjoint(FORBIDDEN_SHARED_MODEL_NAMES)
    initializer = _top_level_definitions(_tree("initializer"))
    resetter = _top_level_definitions(_tree("resetter"))
    migrator = _top_level_definitions(_tree("migrator"))
    assert {
        "ProjectInitializationRequest",
        "ProjectInitializationResult",
    }.issubset(initializer)
    assert {"ResetRequest", "ResetPlan", "ResetResult"}.issubset(resetter)
    assert {
        "ProjectMigrationAction",
        "ProjectMigrationIssue",
        "ProjectMigrationPlan",
        "ProjectMigrationRequest",
        "ProjectMigrationResult",
        "ProjectMigrationStatus",
        "ProjectMigrationStrategy",
    }.issubset(migrator)


@pytest.mark.contract
def test_migrator_consumes_the_registered_migration_workspace_port() -> None:
    tree = _tree("migrator")
    port_imports = _imports_from(tree, "ports")
    assert {"ClockPort", "ProjectMigrationWorkspacePort"}.issubset(port_imports)
    model_imports = _imports_from(tree, "models")
    migration_models = {
        name for name in OWNER_EXPORTS["migrator"] if name.startswith("ProjectMigration")
    }
    assert model_imports.isdisjoint(migration_models)


@pytest.mark.contract
def test_project_public_facade_reexports_owner_objects_without_wrapping() -> None:
    facade = _import("public")
    tree = _tree("public")
    assert not any(
        isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for node in tree.body
    )
    for name, owner_name in PUBLIC_OWNER.items():
        owner = _import(owner_name)
        assert getattr(facade, name) is getattr(owner, name)


@pytest.mark.contract
def test_projects_package_initializer_is_inert() -> None:
    module = importlib.import_module(PROJECT_PACKAGE)
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    assert tuple(getattr(module, "__all__", ())) == ()
    assert not any(
        isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for node in tree.body
    )
    assert not any(isinstance(node, ast.Call) for node in ast.walk(tree))


@pytest.mark.contract
@pytest.mark.parametrize("short_name", DOMAIN_MODULES)
def test_project_domain_modules_do_not_reverse_dependency_direction(
    short_name: str,
) -> None:
    imports = _imported_modules(_tree(short_name))
    violations = sorted(
        module
        for module in imports
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_DOMAIN_PREFIXES
        )
    )
    assert violations == []


@pytest.mark.contract
def test_project_validation_has_one_aggregate_type() -> None:
    for short_name in OWNER_EXPORTS:
        tree = _tree(short_name)
        assert "ProjectValidationReport" not in _top_level_definitions(tree)
        assert "ProjectValidationReport" not in _imports_from(tree, "models")
        assert "ProjectValidationReport" not in _imports_from(
            tree,
            "gf_wordbench.projects.models",
        )
