"""Architecture tests for GF Wordbench dependency directions.

The ADR-0015 checks keep path-resolved language startup inside reviewed
application boundaries: entrypoints collect intent, bootstrap composes concrete
adapters, the projects language probe coordinates passive ports, and existing
selection/GF services retain ownership of their mechanisms.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.contract

_PACKAGE_NAME: Final[str] = "gf_wordbench"
_FUNCTIONAL_MODULES: Final[frozenset[str]] = frozenset(
    {"projects", "runs", "validation", "diagnostics", "reporting"}
)
_ALLOWED_FUNCTIONAL_DEPENDENCIES: Final[Mapping[str, frozenset[str]]] = {
    "projects": frozenset(),
    "runs": frozenset({"projects", "validation", "diagnostics", "reporting"}),
    "validation": frozenset({"projects", "runs", "diagnostics"}),
    "diagnostics": frozenset({"runs", "validation"}),
    "reporting": frozenset({"projects", "runs", "validation", "diagnostics"}),
}
_APPROVED_PROCESS_CREATION_MODULE: Final[str] = "gf_wordbench.infrastructure.process.launcher"
_LANGUAGE_PROBE_PREFIX: Final[str] = "gf_wordbench.projects.languages.probe"
_RUNTIME_STARTUP_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.bootstrap",
    "gf_wordbench.config.environment",
    "gf_wordbench.config.precedence",
    "gf_wordbench.config.resolver",
    "gf_wordbench.entrypoints.cli",
    "gf_wordbench.entrypoints.gui",
    "gf_wordbench.state.repository",
)
_REQUIRED_PATH_RESOLVED_MODULES: Final[frozenset[str]] = frozenset(
    {
        "gf_wordbench.entrypoints.gui.startup",
        "gf_wordbench.projects.languages.models",
        "gf_wordbench.projects.languages.ports",
        "gf_wordbench.projects.languages.probe",
    }
)
_FORBIDDEN_LANGUAGE_PROBE_PREFIXES: Final[tuple[str, ...]] = (
    "PySide6",
    "tkinter",
    "subprocess",
    "gf_wordbench.bootstrap",
    "gf_wordbench.config.environment",
    "gf_wordbench.config.resolver",
    "gf_wordbench.diagnostics",
    "gf_wordbench.entrypoints",
    "gf_wordbench.infrastructure",
    "gf_wordbench.reporting",
    "gf_wordbench.runs",
    "gf_wordbench.state",
    "gf_wordbench.validation",
)
_RUNTIME_CATALOG_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "catalog",
        "rgl_language_catalog",
        "rgl-language-catalog",
    }
)
_FORBIDDEN_STARTUP_LITERALS: Final[frozenset[str]] = frozenset(
    {
        "rgl-language-catalog.json",
        "wordbench/languages/",
        "wordbench\\languages\\",
    }
)
_LANGUAGE_SPECIFIC_LITERALS: Final[frozenset[str]] = frozenset(
    {
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
        "src/english",
        "src\\english",
    }
)
_FORBIDDEN_KERNEL_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.bootstrap",
    "gf_wordbench.config",
    "gf_wordbench.diagnostics",
    "gf_wordbench.entrypoints",
    "gf_wordbench.infrastructure",
    "gf_wordbench.projects",
    "gf_wordbench.reporting",
    "gf_wordbench.runs",
    "gf_wordbench.state",
    "gf_wordbench.validation",
)
_FORBIDDEN_REPORTING_EXECUTION_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.infrastructure.process",
    "gf_wordbench.validation.compilation.commands",
    "gf_wordbench.validation.compilation.gf_adapter",
    "gf_wordbench.validation.compilation.module_compile",
    "gf_wordbench.validation.compilation.pgf_build",
    "gf_wordbench.validation.compilation.service",
    "gf_wordbench.validation.compilation.version_probe",
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.validation.selection.service",
    "gf_wordbench.validation.selection.targets",
    "gf_wordbench.validation.scanning.service",
    "gf_wordbench.validation.scenarios.execution",
    "gf_wordbench.validation.scenarios.service",
)
_FORBIDDEN_ENTRYPOINT_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.config.environment",
    "gf_wordbench.config.resolver",
    "gf_wordbench.infrastructure.atomic_io",
    "gf_wordbench.infrastructure.filesystem",
    "gf_wordbench.infrastructure.process",
    "gf_wordbench.projects.filesystem_adapter",
    "gf_wordbench.projects.languages.probe",
    "gf_wordbench.projects.toml_adapter",
    "gf_wordbench.state.repository",
    "gf_wordbench.validation.compilation.gf_adapter",
    "gf_wordbench.validation.compilation.module_compile",
    "gf_wordbench.validation.compilation.pgf_build",
    "gf_wordbench.validation.compilation.service",
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.validation.selection.service",
    "gf_wordbench.validation.selection.targets",
    "gf_wordbench.validation.scanning.service",
    "gf_wordbench.validation.scenarios.execution",
    "gf_wordbench.validation.scenarios.service",
)
_PASSIVE_MODULE_FILENAMES: Final[frozenset[str]] = frozenset(
    {"models.py", "policies.py", "ports.py", "stage_contracts.py"}
)
_FORBIDDEN_PASSIVE_PREFIXES: Final[tuple[str, ...]] = (
    "PySide6",
    "tkinter",
    "subprocess",
    "gf_wordbench.bootstrap",
    "gf_wordbench.config.environment",
    "gf_wordbench.config.resolver",
    "gf_wordbench.entrypoints",
    "gf_wordbench.infrastructure.process.launcher",
    "gf_wordbench.infrastructure.process.runner",
    "gf_wordbench.state.repository",
    "gf_wordbench.validation.selection.service",
)
_PROCESS_CALLS: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("subprocess", "Popen"),
        ("subprocess", "call"),
        ("subprocess", "check_call"),
        ("subprocess", "check_output"),
        ("subprocess", "run"),
        ("asyncio", "create_subprocess_exec"),
        ("asyncio", "create_subprocess_shell"),
        ("os", "popen"),
        ("os", "system"),
    }
)


@dataclass(frozen=True, slots=True)
class SourceModule:
    name: str
    path: Path
    is_package: bool
    tree: ast.Module


@dataclass(frozen=True, slots=True)
class ImportEdge:
    importer: str
    imported: str
    path: Path
    line: int
    imported_names: tuple[str, ...]

    def render(self) -> str:
        names = f" ({', '.join(self.imported_names)})" if self.imported_names else ""
        return f"{self.path}:{self.line}: {self.importer} -> {self.imported}{names}"


def _package_root() -> Path:
    specification = importlib.util.find_spec(_PACKAGE_NAME)
    assert specification is not None, "gf_wordbench is not importable"
    locations = specification.submodule_search_locations
    assert locations is not None, "gf_wordbench must be a package"
    roots = tuple(Path(location).resolve() for location in locations)
    assert len(roots) == 1, "tests require one unambiguous gf_wordbench package root"
    root = roots[0]
    assert root.is_dir()
    return root


def _module_name(root: Path, source_path: Path) -> tuple[str, bool]:
    relative = source_path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    suffix = ".".join(parts)
    return (
        _PACKAGE_NAME if not suffix else f"{_PACKAGE_NAME}.{suffix}",
        is_package,
    )


def _source_modules() -> tuple[SourceModule, ...]:
    root = _package_root()
    modules: list[SourceModule] = []
    for source_path in sorted(root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        name, is_package = _module_name(root, source_path)
        text = source_path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(source_path))
        modules.append(
            SourceModule(
                name=name,
                path=source_path,
                is_package=is_package,
                tree=tree,
            )
        )
    assert modules, "no GF Wordbench production modules were found"
    return tuple(modules)


def _resolve_from_import(
    module: SourceModule,
    node: ast.ImportFrom,
) -> str:
    if node.level == 0:
        return node.module or ""

    current_parts = module.name.split(".")
    package_parts = current_parts if module.is_package else current_parts[:-1]
    ascents = node.level - 1
    if ascents > len(package_parts):
        return ""

    base = package_parts[: len(package_parts) - ascents]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _import_edges(
    modules: Iterable[SourceModule],
) -> tuple[ImportEdge, ...]:
    prepared = tuple(modules)
    known_modules = {module.name for module in prepared}
    edges: list[ImportEdge] = []

    for module in prepared:
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    edges.append(
                        ImportEdge(
                            importer=module.name,
                            imported=alias.name,
                            path=module.path,
                            line=node.lineno,
                            imported_names=(),
                        )
                    )
                continue

            if not isinstance(node, ast.ImportFrom):
                continue

            imported = _resolve_from_import(module, node)
            if not imported:
                continue

            names = tuple(alias.name for alias in node.names)
            edges.append(
                ImportEdge(
                    importer=module.name,
                    imported=imported,
                    path=module.path,
                    line=node.lineno,
                    imported_names=names,
                )
            )

            for alias in node.names:
                candidate = f"{imported}.{alias.name}"
                if candidate in known_modules:
                    edges.append(
                        ImportEdge(
                            importer=module.name,
                            imported=candidate,
                            path=module.path,
                            line=node.lineno,
                            imported_names=(),
                        )
                    )

    return tuple(edges)


def _internal_edges(
    edges: Iterable[ImportEdge],
) -> Iterator[ImportEdge]:
    prefix = f"{_PACKAGE_NAME}."
    for edge in edges:
        if edge.imported == _PACKAGE_NAME or edge.imported.startswith(prefix):
            yield edge


def _functional_owner(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) < 2 or parts[0] != _PACKAGE_NAME:
        return None
    candidate = parts[1]
    return candidate if candidate in _FUNCTIONAL_MODULES else None


def _starts_with_any(value: str, prefixes: tuple[str, ...]) -> bool:
    return any(value == prefix or value.startswith(f"{prefix}.") for prefix in prefixes)


def _format_edges(edges: Iterable[ImportEdge]) -> str:
    rendered = sorted({edge.render() for edge in edges})
    return "\n".join(rendered)


def _module_matches(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _is_runtime_startup_module(module_name: str) -> bool:
    return any(_module_matches(module_name, prefix) for prefix in _RUNTIME_STARTUP_PREFIXES)


def _contains_catalog_token(value: str) -> bool:
    normalized = value.replace("-", "_").casefold()
    return any(token.replace("-", "_") in normalized for token in _RUNTIME_CATALOG_TOKENS)


def _string_constants(module: SourceModule) -> Iterator[tuple[int, str]]:
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def _recursive_inventory_call(node: ast.Call) -> str | None:
    function = node.func
    if not isinstance(function, ast.Attribute):
        return None

    if function.attr == "rglob":
        return "rglob"

    if function.attr == "glob" and node.args:
        pattern = node.args[0]
        if (
            isinstance(pattern, ast.Constant)
            and isinstance(pattern.value, str)
            and "**" in pattern.value
        ):
            return f"glob({pattern.value!r})"

    if (
        function.attr == "walk"
        and isinstance(function.value, ast.Name)
        and function.value.id == "os"
    ):
        return "os.walk"

    return None


def _strongly_connected_components(
    graph: Mapping[str, frozenset[str]],
) -> tuple[frozenset[str], ...]:
    index = 0
    indexes: dict[str, int] = {}
    low_links: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[frozenset[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbour in sorted(graph.get(node, frozenset())):
            if neighbour not in indexes:
                visit(neighbour)
                low_links[node] = min(
                    low_links[node],
                    low_links[neighbour],
                )
            elif neighbour in on_stack:
                low_links[node] = min(
                    low_links[node],
                    indexes[neighbour],
                )

        if low_links[node] != indexes[node]:
            return

        component: set[str] = set()
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node:
                break
        components.append(frozenset(component))

    all_nodes = set(graph)
    for neighbours in graph.values():
        all_nodes.update(neighbours)
    for node in sorted(all_nodes):
        if node not in indexes:
            visit(node)

    return tuple(components)


def _call_name(node: ast.Call) -> tuple[str, str] | None:
    function = node.func
    if not isinstance(function, ast.Attribute):
        return None
    if not isinstance(function.value, ast.Name):
        return None
    return function.value.id, function.attr


def test_path_resolved_startup_contract_modules_exist() -> None:
    available = {module.name for module in _source_modules()}
    missing = sorted(_REQUIRED_PATH_RESOLVED_MODULES - available)
    assert not missing, (
        "ADR-0015 path-resolved startup requires these production modules: " + ", ".join(missing)
    )


def test_functional_module_dependencies_follow_the_normative_matrix() -> None:
    edges = tuple(_internal_edges(_import_edges(_source_modules())))
    violations: list[ImportEdge] = []

    for edge in edges:
        caller = _functional_owner(edge.importer)
        provider = _functional_owner(edge.imported)
        if caller is None or provider is None or caller == provider:
            continue
        if provider not in _ALLOWED_FUNCTIONAL_DEPENDENCIES[caller]:
            violations.append(edge)

    assert not violations, f"Forbidden functional-module dependencies:\n{_format_edges(violations)}"


def test_functional_module_import_graph_is_acyclic() -> None:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in _internal_edges(_import_edges(_source_modules())):
        caller = _functional_owner(edge.importer)
        provider = _functional_owner(edge.imported)
        if caller is None or provider is None or caller == provider:
            continue
        graph[caller].add(provider)

    frozen_graph = {node: frozenset(neighbours) for node, neighbours in graph.items()}
    cycles = tuple(
        component
        for component in _strongly_connected_components(frozen_graph)
        if len(component) > 1
    )

    assert not cycles, "Functional-module import cycles are prohibited: " + "; ".join(
        " -> ".join(sorted(component)) for component in cycles
    )


def test_kernel_remains_independent_of_outer_modules() -> None:
    violations = [
        edge
        for edge in _internal_edges(_import_edges(_source_modules()))
        if (
            edge.importer == "gf_wordbench.kernel"
            or edge.importer.startswith("gf_wordbench.kernel.")
        )
        and _starts_with_any(
            edge.imported,
            _FORBIDDEN_KERNEL_PREFIXES,
        )
    ]
    assert not violations, (
        f"Kernel dependencies must remain inward and mechanism-free:\n{_format_edges(violations)}"
    )


def test_reporting_does_not_import_execution_behavior() -> None:
    violations = [
        edge
        for edge in _internal_edges(_import_edges(_source_modules()))
        if (
            edge.importer == "gf_wordbench.reporting"
            or edge.importer.startswith("gf_wordbench.reporting.")
        )
        and _starts_with_any(
            edge.imported,
            _FORBIDDEN_REPORTING_EXECUTION_PREFIXES,
        )
    ]
    assert not violations, (
        "Reporting may observe results but must not import execution "
        "behavior:\n"
        f"{_format_edges(violations)}"
    )


def test_entrypoints_do_not_import_concrete_mechanisms_or_stages() -> None:
    violations = [
        edge
        for edge in _internal_edges(_import_edges(_source_modules()))
        if (
            edge.importer == "gf_wordbench.entrypoints"
            or edge.importer.startswith("gf_wordbench.entrypoints.")
        )
        and _starts_with_any(
            edge.imported,
            _FORBIDDEN_ENTRYPOINT_PREFIXES,
        )
    ]
    assert not violations, (
        "Entrypoints must use bootstrap or public application contracts:\n"
        f"{_format_edges(violations)}"
    )


def test_language_probe_uses_ports_instead_of_concrete_outer_services() -> None:
    violations = [
        edge
        for edge in _import_edges(_source_modules())
        if _module_matches(edge.importer, _LANGUAGE_PROBE_PREFIX)
        and _starts_with_any(
            edge.imported,
            _FORBIDDEN_LANGUAGE_PROBE_PREFIXES,
        )
    ]
    assert not violations, (
        "ADR-0015 language probing must depend on passive local contracts "
        "and injected ports, not GUI, configuration, state, validation, "
        "diagnostic, reporting, process, or run implementations:\n"
        f"{_format_edges(violations)}"
    )


def test_language_probe_does_not_reimplement_recursive_source_inventory() -> None:
    violations: list[str] = []

    for module in _source_modules():
        if not _module_matches(module.name, _LANGUAGE_PROBE_PREFIX):
            continue
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Call):
                continue
            operation = _recursive_inventory_call(node)
            if operation is not None:
                violations.append(
                    f"{module.path}:{node.lineno}: language probe performs {operation}"
                )

    assert not violations, (
        "The language probe must delegate recursive source inventory to "
        "the existing selection service through an injected port:\n" + "\n".join(sorted(violations))
    )


def test_runtime_startup_does_not_import_catalog_authority() -> None:
    violations: list[str] = []

    for edge in _import_edges(_source_modules()):
        if not _is_runtime_startup_module(edge.importer):
            continue
        imported_values = (edge.imported, *edge.imported_names)
        if any(_contains_catalog_token(value) for value in imported_values):
            violations.append(edge.render())

    for module in _source_modules():
        if not _is_runtime_startup_module(module.name):
            continue
        for line, value in _string_constants(module):
            if any(literal in value for literal in _FORBIDDEN_STARTUP_LITERALS):
                violations.append(
                    f"{module.path}:{line}: runtime startup references "
                    f"catalog/bundle authority {value!r}"
                )

    assert not violations, (
        "ADR-0015 normal startup must not import or reference the retired "
        "catalog/bundle authority:\n" + "\n".join(sorted(set(violations)))
    )


def test_generic_production_code_has_no_hard_coded_language_defaults() -> None:
    violations: list[str] = []

    for module in _source_modules():
        for line, value in _string_constants(module):
            for literal in _LANGUAGE_SPECIFIC_LITERALS:
                if literal in value:
                    violations.append(f"{module.path}:{line}: {literal!r} in {value!r}")

    assert not violations, (
        "Generic production code must derive language identity, directories, "
        "suffixes, and entrypoint candidates from the selected source "
        "context rather than English defaults:\n" + "\n".join(sorted(set(violations)))
    )


def test_scanning_and_compilation_do_not_invoke_each_other() -> None:
    edges = tuple(_internal_edges(_import_edges(_source_modules())))
    violations = [
        edge
        for edge in edges
        if (
            edge.importer.startswith("gf_wordbench.validation.scanning.")
            and edge.imported.startswith("gf_wordbench.validation.compilation.")
        )
        or (
            edge.importer.startswith("gf_wordbench.validation.compilation.")
            and edge.imported.startswith("gf_wordbench.validation.scanning.")
        )
    ]
    assert not violations, (
        f"Static scanning and GF compilation are separate stages:\n{_format_edges(violations)}"
    )


def test_process_creation_is_confined_to_launcher() -> None:
    violations: list[str] = []

    for module in _source_modules():
        for node in ast.walk(module.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported_names: tuple[str, ...]
                if isinstance(node, ast.Import):
                    imported_names = tuple(alias.name for alias in node.names)
                else:
                    imported_names = (node.module,) if node.module else ()
                if (
                    any(
                        name == "subprocess" or name.startswith("subprocess.")
                        for name in imported_names
                    )
                    and module.name != _APPROVED_PROCESS_CREATION_MODULE
                ):
                    violations.append(
                        f"{module.path}:{node.lineno}: {module.name} imports subprocess"
                    )

            if not isinstance(node, ast.Call):
                continue
            call_name = _call_name(node)
            if call_name not in _PROCESS_CALLS:
                continue

            if module.name != _APPROVED_PROCESS_CREATION_MODULE:
                violations.append(
                    f"{module.path}:{node.lineno}: "
                    f"{module.name} calls "
                    f"{call_name[0]}.{call_name[1]}"
                )

            for keyword in node.keywords:
                if (
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    violations.append(f"{module.path}:{node.lineno}: shell=True is prohibited")

    assert not violations, (
        "Process creation must be shell-free and owned only by "
        "infrastructure.process.launcher:\n" + "\n".join(sorted(set(violations)))
    )


def test_passive_contract_modules_do_not_depend_on_delivery_or_launchers() -> None:
    modules = _source_modules()
    passive_names = {
        module.name
        for module in modules
        if module.path.name in _PASSIVE_MODULE_FILENAMES
        or "models" in module.path.relative_to(_package_root()).parts
    }
    violations = [
        edge
        for edge in _import_edges(modules)
        if edge.importer in passive_names
        and _starts_with_any(
            edge.imported,
            _FORBIDDEN_PASSIVE_PREFIXES,
        )
    ]
    assert not violations, (
        "Models, policies, ports, and stage contracts must remain "
        "passive:\n"
        f"{_format_edges(violations)}"
    )


def test_production_code_does_not_import_tests_or_portfolio() -> None:
    violations = [
        edge
        for edge in _import_edges(_source_modules())
        if (
            edge.imported == "tests"
            or edge.imported.startswith("tests.")
            or edge.imported == "gf_portfolio"
            or edge.imported.startswith("gf_portfolio.")
        )
    ]
    assert not violations, (
        f"Production code must not depend on tests or gf-portfolio:\n{_format_edges(violations)}"
    )


def test_cross_module_private_and_wildcard_imports_are_prohibited() -> None:
    violations: list[str] = []

    for edge in _internal_edges(_import_edges(_source_modules())):
        if "*" in edge.imported_names:
            violations.append(f"{edge.path}:{edge.line}: wildcard import from {edge.imported}")

        importer_owner = ".".join(edge.importer.split(".")[:2])
        imported_owner = ".".join(edge.imported.split(".")[:2])
        if importer_owner == imported_owner:
            continue

        for name in edge.imported_names:
            if name.startswith("_") and name != "__version__":
                violations.append(f"{edge.path}:{edge.line}: private symbol {edge.imported}.{name}")

    assert not violations, (
        "Cross-module consumers must use explicit public contracts:\n"
        + "\n".join(sorted(set(violations)))
    )
