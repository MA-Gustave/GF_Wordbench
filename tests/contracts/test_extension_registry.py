from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT: Final[Path] = _REPOSITORY_ROOT / "src" / "gf_wordbench"

_REGISTRY_MODULES: Final[tuple[str, ...]] = (
    "gf_wordbench.diagnostics.tools.registry",
    "gf_wordbench.reporting.schemas.registry",
    "gf_wordbench.validation.release.registry",
    "gf_wordbench.validation.scanning.registry",
    "gf_wordbench.validation.scenarios.assertion_registry",
)

_FORBIDDEN_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "entrypoints",
    "gf_portfolio",
    "importlib.metadata",
    "pkg_resources",
    "pkgutil",
    "pluggy",
    "setuptools",
)

_FORBIDDEN_DYNAMIC_CALLS: Final[frozenset[str]] = frozenset(
    {
        "__import__",
        "entry_points",
        "eval",
        "exec",
        "exec_module",
        "find_distributions",
        "iter_modules",
        "load_module",
        "walk_packages",
    }
)

_EXPECTED_SCHEMA_IDS: Final[tuple[str, ...]] = (
    "gf-wordbench.app-state",
    "gf-wordbench.artifact-manifest",
    "gf-wordbench.project",
    "gf-wordbench.run-summary",
    "gf-wordbench.scenario-gold",
    "gf-wordbench.scenario-output",
)

_EXPECTED_RELEASE_GATE_IDS: Final[tuple[str, ...]] = tuple(
    f"RG-{index:02d}" for index in range(15)
)

_EXPECTED_SCAN_RULE_IDS: Final[tuple[str, ...]] = (
    "SCAN-NOTATION-001",
    "SCAN-NOTATION-002",
    "SCAN-RUNTIME-001",
    "SCAN-PATTERN-001",
    "SCAN-PATTERN-002",
    "SCAN-STYLE-001",
)

_EXPECTED_SCAN_COUNT_FIELDS: Final[tuple[str, ...]] = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
)

_EXPECTED_ASSERTION_TYPE_IDS: Final[tuple[str, ...]] = (
    "process.completed",
    "process.exit-code",
    "process.not-timed-out",
    "process.not-cancelled",
    "process.output-within-limit",
    "process.capture-complete",
    "section.exists",
    "section.completed",
    "section.ordered",
    "section.no-unexpected",
    "section.non-empty",
    "diagnostic.no-fatal",
    "diagnostic.expected",
    "diagnostic.absent",
    "text.contains",
    "text.excludes",
    "text.equals",
    "text.matches",
    "text.one-of",
    "count.equals",
    "count.minimum",
    "count.maximum",
    "count.range",
    "artifact.exists",
    "artifact.non-empty",
    "artifact.current",
    "artifact.contained",
    "gold.matches",
)


@pytest.mark.parametrize("module_name", _REGISTRY_MODULES)
def test_extension_registry_module_imports_cleanly(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module.__name__ == module_name


@pytest.mark.parametrize("module_name", _REGISTRY_MODULES)
def test_extension_registry_uses_explicit_static_registration(
    module_name: str,
) -> None:
    source_path = _module_source_path(module_name)
    tree = ast.parse(source_path.read_text(encoding="utf-8"), source_path.name)

    forbidden_imports: list[str] = []
    forbidden_calls: list[str] = []
    environment_reads: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _matches_forbidden_import(alias.name):
                    forbidden_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if _matches_forbidden_import(imported):
                forbidden_imports.append(imported)
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in _FORBIDDEN_DYNAMIC_CALLS:
                forbidden_calls.append(name)
            if name in {"getenv", "os.getenv"}:
                environment_reads.append(name)
        elif isinstance(node, ast.Attribute):
            if node.attr == "environ":
                environment_reads.append("environ")

    assert forbidden_imports == []
    assert forbidden_calls == []
    assert environment_reads == []


def test_diagnostic_tool_registry_is_static_immutable_and_empty_by_default() -> None:
    registry = importlib.import_module(
        "gf_wordbench.diagnostics.tools.registry"
    )

    assert registry.DEFAULT_TOOL_SPECS == ()
    assert registry.DEFAULT_TOOL_REGISTRY.catalog_version == (
        registry.CATALOG_VERSION
    )
    assert tuple(registry.DEFAULT_TOOL_REGISTRY) == ()
    assert registry.DEFAULT_TOOL_REGISTRY.tool_ids == ()
    assert registry.registered_tool_ids() == ()

    snapshot = registry.DEFAULT_TOOL_REGISTRY.snapshot()
    assert snapshot.catalog_version == registry.CATALOG_VERSION
    assert snapshot.tool_ids == ()
    assert snapshot.required_tool_ids == ()
    assert snapshot.optional_tool_ids == ()
    assert snapshot.diagnostic_only_tool_ids == ()
    assert snapshot.normative_tool_ids == ()
    assert snapshot.ai_assisted_tool_ids == ()

    assert isinstance(registry.DEFAULT_TOOL_REGISTRY.mapping, MappingProxyType)
    with pytest.raises(TypeError):
        registry.DEFAULT_TOOL_REGISTRY.mapping["unreviewed-tool"] = object()

    assert registry.normalize_tool_id("tool-1") == "tool-1"
    for invalid in ("", "Tool", "tool_name", "tool name", "../tool"):
        with pytest.raises((TypeError, ValueError)):
            registry.normalize_tool_id(invalid)

    with pytest.raises(registry.UnknownDiagnosticToolError):
        registry.require_registered_tool("unregistered-tool")


def test_schema_registry_is_versioned_deterministic_and_immutable() -> None:
    registry = importlib.import_module(
        "gf_wordbench.reporting.schemas.registry"
    )

    definitions = registry.CANONICAL_SCHEMA_DEFINITIONS
    assert tuple(registry.SCHEMA_REGISTRY) == definitions
    assert registry.CANONICAL_SCHEMA_IDS == _EXPECTED_SCHEMA_IDS
    assert len(registry.CANONICAL_SCHEMA_KEYS) == len(definitions)
    assert len(set(registry.CANONICAL_SCHEMA_KEYS)) == len(definitions)

    paths = tuple(
        definition.canonical_path_pattern
        for definition in definitions
    )
    assert len(paths) == len(set(path.casefold() for path in paths))

    for definition in definitions:
        assert registry.current_schema(definition.schema_id) is definition
        assert definition.writer_owner
        assert definition.readers
        assert definition.version.major == 1
        assert definition.version.minor == 0

    snapshot = registry.schema_registry_snapshot()
    assert isinstance(snapshot, MappingProxyType)
    assert tuple(snapshot) == tuple(sorted(snapshot))
    assert set(snapshot.values()) == set(definitions)

    with pytest.raises(TypeError):
        snapshot["gf-wordbench.unreviewed/1.0"] = definitions[0]


def test_release_gate_registry_preserves_canonical_prefix_and_decision_owner() -> None:
    registry = importlib.import_module(
        "gf_wordbench.validation.release.registry"
    )

    assert registry.CANONICAL_RELEASE_GATE_IDS == (
        _EXPECTED_RELEASE_GATE_IDS
    )
    assert tuple(registry.iter_release_gates()) == (
        registry.CANONICAL_RELEASE_GATES
    )
    assert tuple(registry.CANONICAL_RELEASE_GATE_BY_ID) == (
        _EXPECTED_RELEASE_GATE_IDS
    )

    decision = registry.decision_gate_definition()
    assert decision.gate_id == "RG-14"
    assert decision.phase is registry.ReleaseGatePhase.DECISION
    assert all(
        gate.phase is registry.ReleaseGatePhase.EVALUATION
        for gate in registry.evaluation_gate_definitions()
    )

    extension = registry.ReleaseGateDefinition(
        gate_id="RC-TEST-001",
        name="Contract-test project gate",
        applicability=registry.ReleaseGateApplicability.REQUIRED,
        owner="Project release policy",
        purpose=(
            "Prove that project extensions are explicit, typed, and "
            "append-only."
        ),
    )
    combined = registry.build_release_gate_registry((extension,))

    assert combined[:-1] == registry.CANONICAL_RELEASE_GATES
    assert combined[-1] is extension
    assert registry.index_release_gate_registry(combined)[
        extension.gate_id
    ] is extension

    with pytest.raises(ValueError):
        registry.validate_release_gate_registry(
            (*registry.CANONICAL_RELEASE_GATES, extension, extension),
            require_canonical_prefix=True,
        )

    with pytest.raises(TypeError):
        registry.build_release_gate_registry("RC-TEST-001")


def test_scan_rule_registry_is_explicit_ordered_and_total() -> None:
    registry = importlib.import_module(
        "gf_wordbench.validation.scanning.registry"
    )

    registry.validate_builtin_registry()

    rule_set = registry.BUILTIN_RULE_REGISTRY
    assert rule_set.rule_set_id == registry.BUILTIN_RULE_SET_ID
    assert rule_set.version == registry.BUILTIN_RULE_SET_VERSION
    assert rule_set.rule_ids == _EXPECTED_SCAN_RULE_IDS
    assert rule_set.count_fields == _EXPECTED_SCAN_COUNT_FIELDS
    assert tuple(registry.iter_builtin_rules()) == registry.BUILTIN_RULES
    assert tuple(rule_set) == registry.BUILTIN_RULES

    orders = tuple(rule.order for rule in rule_set)
    assert orders == tuple(sorted(orders))
    assert len(orders) == len(set(orders))
    assert len(rule_set.rule_ids) == len(set(rule_set.rule_ids))
    assert len(rule_set.count_fields) == len(set(rule_set.count_fields))

    for rule in rule_set:
        assert registry.require_builtin_rule(rule.rule_id) is rule
        assert (
            registry.require_builtin_rule_by_count_field(rule.count_field)
            is rule
        )
        assert rule.source_views
        assert rule.interpretation


def test_assertion_registry_requires_complete_explicit_evaluator_binding() -> None:
    registry = importlib.import_module(
        "gf_wordbench.validation.scenarios.assertion_registry"
    )

    descriptors = registry.CANONICAL_ASSERTION_TYPES
    assert tuple(descriptor.type_id for descriptor in descriptors) == (
        _EXPECTED_ASSERTION_TYPE_IDS
    )
    assert tuple(registry.CANONICAL_ASSERTION_TYPE_BY_ID) == (
        _EXPECTED_ASSERTION_TYPE_IDS
    )

    orders = tuple(descriptor.order for descriptor in descriptors)
    assert orders == tuple(sorted(orders))
    assert len(orders) == len(set(orders))
    assert len(_EXPECTED_ASSERTION_TYPE_IDS) == len(
        set(_EXPECTED_ASSERTION_TYPE_IDS)
    )

    for descriptor in descriptors:
        assert (
            registry.canonical_assertion_descriptor(descriptor.type_id)
            is descriptor
        )
        assert descriptor.input_sources
        assert descriptor.serialization_name
        assert descriptor.report_label

    def evaluator(spec: object, context: object) -> object:
        return (spec, context)

    evaluators = {
        type_id: evaluator
        for type_id in reversed(_EXPECTED_ASSERTION_TYPE_IDS)
    }
    bound = registry.bind_canonical_assertion_registry(evaluators)

    assert bound.type_ids == _EXPECTED_ASSERTION_TYPE_IDS
    assert bound.descriptors == descriptors
    assert len(bound.fingerprint) == 64
    assert bound.fingerprint == registry.bind_canonical_assertion_registry(
        dict(evaluators)
    ).fingerprint

    with pytest.raises(registry.AssertionEvaluatorBindingError):
        registry.bind_canonical_assertion_registry({})

    with pytest.raises(registry.AssertionEvaluatorBindingError):
        registry.bind_canonical_assertion_registry(
            {**evaluators, "unreviewed.assertion": evaluator}
        )

    invalid = dict(evaluators)
    invalid[_EXPECTED_ASSERTION_TYPE_IDS[0]] = object()
    with pytest.raises(registry.AssertionEvaluatorBindingError):
        registry.bind_canonical_assertion_registry(invalid)


def test_registry_contracts_expose_no_runtime_mutator_api() -> None:
    registry_classes = (
        (
            "gf_wordbench.diagnostics.tools.registry",
            "DiagnosticToolRegistry",
        ),
        (
            "gf_wordbench.reporting.schemas.registry",
            "SchemaRegistry",
        ),
        (
            "gf_wordbench.validation.scanning.registry",
            "ScanRuleSet",
        ),
        (
            "gf_wordbench.validation.scenarios.assertion_registry",
            "AssertionRegistry",
        ),
    )

    forbidden = {
        "add",
        "append",
        "clear",
        "discover",
        "install",
        "load_plugins",
        "register",
        "remove",
        "unregister",
        "update",
    }

    for module_name, class_name in registry_classes:
        module = importlib.import_module(module_name)
        registry_class = getattr(module, class_name)
        public_names = {
            name
            for name in vars(registry_class)
            if not name.startswith("_")
        }
        assert public_names.isdisjoint(forbidden)


def _module_source_path(module_name: str) -> Path:
    prefix = "gf_wordbench."
    if not module_name.startswith(prefix):
        raise ValueError(f"not a GF Wordbench module: {module_name!r}")
    relative = module_name.removeprefix(prefix).replace(".", "/")
    path = _PACKAGE_ROOT / f"{relative}.py"
    assert path.is_file(), f"missing registry source: {path}"
    return path


def _matches_forbidden_import(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in _FORBIDDEN_IMPORT_PREFIXES
    )


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""
