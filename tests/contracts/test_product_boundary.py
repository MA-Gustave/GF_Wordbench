from __future__ import annotations

import ast
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import fields
from pathlib import Path
import re
import tomllib
from typing import Any, Final

import pytest

from gf_wordbench.config.models import ConfigurationResolutionRequest, RunConfig
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.state.models import AppState

pytestmark = pytest.mark.contract

_PORTFOLIO_DISTRIBUTIONS: Final[frozenset[str]] = frozenset(
    {
        "gf-portfolio",
        "gfportfolio",
    }
)
_PORTFOLIO_MODULES: Final[frozenset[str]] = frozenset(
    {
        "gf_portfolio",
        "gfportfolio",
    }
)
_RUNTIME_FORBIDDEN_TOP_LEVEL_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "project",
        "templates",
        "tests",
        *_PORTFOLIO_MODULES,
    }
)
_PROJECT_CODE_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".py",
        ".pyc",
        ".pyd",
        ".pyw",
        ".so",
    }
)
_FORBIDDEN_MULTI_PROJECT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "active_projects",
        "identities",
        "languages",
        "portfolio",
        "portfolio_id",
        "portfolio_ids",
        "projects",
        "project_ids",
        "targets",
        "workspace_registry",
        "workspaces",
    }
)
_FORBIDDEN_PROJECT_CONFIGURATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "active_projects",
        "callables",
        "plugins",
        "portfolio",
        "portfolio_registry",
        "python_plugins",
        "workspace_registry",
        "workspaces",
    }
)
_DYNAMIC_IMPORT_CALLS: Final[frozenset[str]] = frozenset(
    {
        "__import__",
        "import_module",
        "importlib.import_module",
    }
)


def _repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "gf_wordbench"
        ).is_dir():
            return candidate
    raise AssertionError("repository root could not be located")


def _python_files(root: Path) -> Iterator[Path]:
    for relative_root in ("src/gf_wordbench", "tests", "scripts"):
        directory = root / relative_root
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def _runtime_python_files(root: Path) -> Iterator[Path]:
    package_root = root / "src" / "gf_wordbench"
    for path in sorted(package_root.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _qualified_call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _qualified_call_name(node.value)
        if owner is None:
            return None
        return f"{owner}.{node.attr}"
    return None


def _imported_modules(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise AssertionError(f"could not parse {path}: {exc}") from exc

    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                modules.append(node.module)
            continue
        if not isinstance(node, ast.Call) or not node.args:
            continue
        call_name = _qualified_call_name(node.func)
        if call_name not in _DYNAMIC_IMPORT_CALLS:
            continue
        first_argument = node.args[0]
        if isinstance(first_argument, ast.Constant) and isinstance(
            first_argument.value,
            str,
        ):
            modules.append(first_argument.value)

    return tuple(modules)


def _top_level_module(module: str) -> str:
    return module.partition(".")[0].strip()


def _requirement_name(requirement: object) -> str:
    if not isinstance(requirement, str) or not requirement.strip():
        raise AssertionError(f"invalid dependency declaration: {requirement!r}")
    name = re.split(r"[\s\[\]();<>=!~@]", requirement.strip(), maxsplit=1)[0]
    return re.sub(r"[-_.]+", "-", name).lower()


def _dependency_requirements(document: Mapping[str, object]) -> tuple[str, ...]:
    requirements: list[str] = []

    build_system = document.get("build-system")
    if isinstance(build_system, Mapping):
        build_requires = build_system.get("requires", ())
        if isinstance(build_requires, list):
            requirements.extend(item for item in build_requires if isinstance(item, str))

    project = document.get("project")
    if not isinstance(project, Mapping):
        raise AssertionError("pyproject.toml must define [project]")

    dependencies = project.get("dependencies", ())
    if isinstance(dependencies, list):
        requirements.extend(item for item in dependencies if isinstance(item, str))

    optional = project.get("optional-dependencies", {})
    if isinstance(optional, Mapping):
        for group in optional.values():
            if isinstance(group, list):
                requirements.extend(item for item in group if isinstance(item, str))

    return tuple(requirements)


def _all_mapping_keys(value: object) -> frozenset[str]:
    keys: set[str] = set()
    pending: list[object] = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, Mapping):
            for key, item in current.items():
                if isinstance(key, str):
                    keys.add(key)
                pending.append(item)
        elif isinstance(current, list):
            pending.extend(current)
    return frozenset(keys)


def _field_names(model: type[Any]) -> frozenset[str]:
    return frozenset(field.name for field in fields(model))


def _relative_paths(root: Path, paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(path.relative_to(root).as_posix() for path in paths)


def _optional_profile_identity(root: Path) -> tuple[str, ...]:
    project_file = root / "project" / "project.toml"
    if not project_file.is_file():
        return ()
    with project_file.open("rb") as handle:
        document = tomllib.load(handle)
    profile = document.get("profile", document.get("project"))
    if not isinstance(profile, Mapping):
        raise AssertionError("an optional project.toml profile must define [profile]")
    values: list[str] = []
    for key in ("id", "name"):
        value = profile.get(key)
        if not isinstance(value, str) or not value.strip():
            raise AssertionError(f"profile.{key} must be a non-empty string")
        values.append(value.casefold())
    return tuple(values)


def _string_constants(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def test_package_metadata_has_no_reverse_portfolio_dependency() -> None:
    root = _repository_root()
    with (root / "pyproject.toml").open("rb") as handle:
        document = tomllib.load(handle)

    dependency_names = {
        _requirement_name(requirement) for requirement in _dependency_requirements(document)
    }
    assert dependency_names.isdisjoint(_PORTFOLIO_DISTRIBUTIONS)

    hatch = document.get("tool", {})
    assert isinstance(hatch, Mapping)
    hatch = hatch.get("hatch", {})
    assert isinstance(hatch, Mapping)
    build = hatch.get("build", {})
    assert isinstance(build, Mapping)
    targets = build.get("targets", {})
    assert isinstance(targets, Mapping)
    wheel = targets.get("wheel", {})
    assert isinstance(wheel, Mapping)
    assert wheel.get("packages") == ["src/gf_wordbench"]

    project = document.get("project")
    assert isinstance(project, Mapping)
    for table_name in ("scripts", "gui-scripts"):
        table = project.get(table_name, {})
        assert isinstance(table, Mapping)
        for entrypoint in table.values():
            assert isinstance(entrypoint, str)
            assert entrypoint.startswith("gf_wordbench.")


def test_runtime_imports_no_repository_project_template_tests_or_portfolio() -> None:
    root = _repository_root()
    violations: list[str] = []

    for path in _runtime_python_files(root):
        for module in _imported_modules(path):
            top_level = _top_level_module(module)
            if top_level in _RUNTIME_FORBIDDEN_TOP_LEVEL_IMPORTS:
                violations.append(f"{path.relative_to(root).as_posix()}: imports {module}")

    assert violations == []


def test_tests_scripts_and_launchers_do_not_require_portfolio() -> None:
    root = _repository_root()
    violations: list[str] = []

    for path in _python_files(root):
        for module in _imported_modules(path):
            if _top_level_module(module) in _PORTFOLIO_MODULES:
                violations.append(f"{path.relative_to(root).as_posix()}: imports {module}")

    forbidden_tokens = ("gf-portfolio", "gf_portfolio", "gfportfolio")
    for path in sorted(root.glob("*.bat")):
        text = path.read_text(encoding="utf-8", errors="strict").casefold()
        for token in forbidden_tokens:
            if token in text:
                violations.append(f"{path.name}: requires {token}")

    assert violations == []


def test_active_project_and_template_are_data_only_extension_boundaries() -> None:
    root = _repository_root()
    violations: list[Path] = []

    boundaries = [root / "templates" / "validation-profile"]
    optional_profile = root / "project"
    if optional_profile.exists():
        boundaries.append(optional_profile)

    assert boundaries[0].is_dir()
    for boundary in boundaries:
        for path in boundary.rglob("*"):
            if path.is_file() and path.suffix.casefold() in _PROJECT_CODE_SUFFIXES:
                violations.append(path)
            if path.is_dir() and path.name == "__pycache__":
                violations.append(path)

    assert _relative_paths(root, violations) == ()


def test_project_configuration_declares_one_project_and_no_portfolio_registry() -> None:
    root = _repository_root()

    paths = [root / "templates" / "validation-profile" / "project.toml"]
    optional_profile = root / "project" / "project.toml"
    if optional_profile.is_file():
        paths.append(optional_profile)

    for path in paths:
        with path.open("rb") as handle:
            document = tomllib.load(handle)

        assert document.get("schema_id") == "gf-wordbench.project"
        assert isinstance(document.get("schema_version"), str)
        profile = document.get("profile", document.get("project"))
        assert isinstance(profile, Mapping)
        assert {"id", "name"}.issubset(profile)
        assert _all_mapping_keys(document).isdisjoint(_FORBIDDEN_PROJECT_CONFIGURATION_KEYS)


def test_models_preserve_one_active_project_and_one_target_per_run() -> None:
    project_fields = _field_names(ProjectConfig)
    request_fields = _field_names(ConfigurationResolutionRequest)
    run_fields = _field_names(RunConfig)
    state_fields = _field_names(AppState)

    assert "identity" in project_fields
    assert {"language_context", "validation_profile"}.issubset(request_fields)
    assert {"language_context", "validation_profile", "target"}.issubset(run_fields)
    assert "project" not in request_fields
    assert "project" not in run_fields

    for model_fields in (
        project_fields,
        request_fields,
        run_fields,
        state_fields,
    ):
        assert model_fields.isdisjoint(_FORBIDDEN_MULTI_PROJECT_FIELDS)


def test_framework_source_does_not_embed_active_language_identity() -> None:
    root = _repository_root()
    active_identity = frozenset(_optional_profile_identity(root))
    violations: list[str] = []

    for path in _runtime_python_files(root):
        for value in _string_constants(path):
            if value.casefold() in active_identity:
                violations.append(f"{path.relative_to(root).as_posix()}: {value!r}")

    assert violations == []
