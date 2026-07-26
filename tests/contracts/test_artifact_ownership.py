from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest


@dataclass(frozen=True, slots=True)
class OwnedWriter:
    artifact: str
    owner_module: str
    symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModuleFacts:
    module: str
    path: Path
    tree: ast.Module
    definitions: frozenset[str]
    exports: frozenset[str]
    imports: Mapping[str, tuple[str, str]]


OWNED_WRITERS: Final[tuple[OwnedWriter, ...]] = (
    OwnedWriter(
        artifact=".gf_wordbench_state.json",
        owner_module="gf_wordbench.state.repository",
        symbols=("save_app_state",),
    ),
    OwnedWriter(
        artifact="raw/master.log",
        owner_module="gf_wordbench.reporting.logs.lifecycle",
        symbols=(
            "create_lifecycle_log",
            "append_lifecycle_event",
            "write_master_event",
            "finalize_lifecycle_log",
        ),
    ),
    OwnedWriter(
        artifact="raw/ALL_SCAN_LOGS.TXT",
        owner_module="gf_wordbench.reporting.logs.aggregates",
        symbols=("write_all_scan_logs",),
    ),
    OwnedWriter(
        artifact="raw/ALL_LOGS.TXT",
        owner_module="gf_wordbench.reporting.logs.aggregates",
        symbols=("write_all_logs",),
    ),
    OwnedWriter(
        artifact="summary.json",
        owner_module="gf_wordbench.reporting.summary.json_writer",
        symbols=("write_summary_json",),
    ),
    OwnedWriter(
        artifact="summary.md",
        owner_module="gf_wordbench.reporting.summary.markdown_writer",
        symbols=("write_summary_md",),
    ),
    OwnedWriter(
        artifact="AI_READY.md",
        owner_module="gf_wordbench.reporting.ai_packet.renderer",
        symbols=("write_ai_ready",),
    ),
    OwnedWriter(
        artifact="manifest.json",
        owner_module="gf_wordbench.reporting.manifest.builder",
        symbols=("write_manifest",),
    ),
)

REPORTING_FACADE: Final[str] = "gf_wordbench.reporting.public"
REPORTING_FACADE_EXPORTS: Final[Mapping[str, tuple[str, str]]] = {
    "build_manifest": (
        "gf_wordbench.reporting.manifest.builder",
        "build_manifest",
    ),
    "publish_reports": (
        "gf_wordbench.reporting.publisher",
        "publish_reports",
    ),
    "verify_manifest": (
        "gf_wordbench.reporting.manifest.verifier",
        "verify_manifest",
    ),
    "write_ai_ready": (
        "gf_wordbench.reporting.ai_packet.renderer",
        "write_ai_ready",
    ),
    "write_all_logs": (
        "gf_wordbench.reporting.logs.aggregates",
        "write_all_logs",
    ),
    "write_all_scan_logs": (
        "gf_wordbench.reporting.logs.aggregates",
        "write_all_scan_logs",
    ),
    "write_manifest": (
        "gf_wordbench.reporting.manifest.builder",
        "write_manifest",
    ),
    "write_summary_json": (
        "gf_wordbench.reporting.summary.json_writer",
        "write_summary_json",
    ),
    "write_summary_md": (
        "gf_wordbench.reporting.summary.markdown_writer",
        "write_summary_md",
    ),
}

ANTI_DUPLICATION_OWNERS: Final[Mapping[str, str]] = {
    "ProducerInfo": "gf_wordbench.kernel.serialization",
    "ValidationMode": "gf_wordbench.kernel.statuses",
    "TargetKind": "gf_wordbench.kernel.statuses",
    "CancellationToken": "gf_wordbench.infrastructure.process.termination",
    "ProcessCapture": "gf_wordbench.infrastructure.process.streams",
    "TreeEntry": "gf_wordbench.projects.ports",
    "TreeEntryKind": "gf_wordbench.projects.ports",
    "ProjectValidationResult": "gf_wordbench.projects.models",
    "RunPaths": "gf_wordbench.runs.models.paths",
}

FORBIDDEN_COMPETING_SYMBOLS: Final[Mapping[str, frozenset[str]]] = {
    "ProducerInfo": frozenset(
        {
            "gf_wordbench.config.models",
            "gf_wordbench.state.models",
        }
    ),
    "ValidationMode": frozenset(
        {
            "gf_wordbench.config.models",
        }
    ),
    "CancellationToken": frozenset(
        {
            "gf_wordbench.infrastructure.process.models",
        }
    ),
    "ProcessCapture": frozenset(
        {
            "gf_wordbench.infrastructure.process.models",
        }
    ),
    "TreeEntry": frozenset(
        {
            "gf_wordbench.projects.filesystem_adapter",
        }
    ),
    "TreeEntryKind": frozenset(
        {
            "gf_wordbench.projects.filesystem_adapter",
        }
    ),
}

WRITE_PRIMITIVES: Final[frozenset[str]] = frozenset(
    {
        "atomic_write_bytes",
        "atomic_write_json",
        "atomic_write_text",
        "open",
        "write_bytes",
        "write_json",
        "write_text",
    }
)

FIXED_ARTIFACT_WRITER_MODULES: Final[Mapping[str, frozenset[str]]] = {
    ".gf_wordbench_state.json": frozenset(
        {
            "gf_wordbench.state.repository",
            "gf_wordbench.projects.initializer",
            "gf_wordbench.projects.migrator",
            "gf_wordbench.projects.resetter",
        }
    ),
    "raw/master.log": frozenset(
        {
            "gf_wordbench.reporting.logs.lifecycle",
        }
    ),
    "master.log": frozenset(
        {
            "gf_wordbench.reporting.logs.lifecycle",
        }
    ),
    "ALL_SCAN_LOGS.TXT": frozenset(
        {
            "gf_wordbench.reporting.logs.aggregates",
        }
    ),
    "ALL_LOGS.TXT": frozenset(
        {
            "gf_wordbench.reporting.logs.aggregates",
        }
    ),
    "summary.json": frozenset(
        {
            "gf_wordbench.reporting.summary.json_writer",
        }
    ),
    "summary.md": frozenset(
        {
            "gf_wordbench.reporting.summary.markdown_writer",
        }
    ),
    "AI_READY.md": frozenset(
        {
            "gf_wordbench.reporting.ai_packet.renderer",
        }
    ),
    "top_errors.txt": frozenset(
        {
            "gf_wordbench.reporting.publisher",
        }
    ),
    "manifest.json": frozenset(
        {
            "gf_wordbench.reporting.manifest.builder",
        }
    ),
}


def _repository_root() -> Path:
    candidate = Path(__file__).resolve()
    for parent in candidate.parents:
        if (parent / "pyproject.toml").is_file() and (
            parent / "src" / "gf_wordbench"
        ).is_dir():
            return parent
    raise AssertionError("cannot locate GF Wordbench repository root")


def _module_name(source_root: Path, path: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _literal_string_sequence(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values: list[str] = []
    for element in node.elts:
        if not isinstance(element, ast.Constant) or not isinstance(
            element.value,
            str,
        ):
            return None
        values.append(element.value)
    return tuple(values)


def _extract_exports(tree: ast.Module) -> frozenset[str]:
    exports: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if not any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in statement.targets
            ):
                continue
            values = _literal_string_sequence(statement.value)
            if values is not None:
                exports = list(values)
        elif isinstance(statement, ast.AnnAssign):
            if not (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "__all__"
            ):
                continue
            if statement.value is None:
                continue
            values = _literal_string_sequence(statement.value)
            if values is not None:
                exports = list(values)
        elif isinstance(statement, ast.AugAssign):
            if not (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "__all__"
                and isinstance(statement.op, ast.Add)
            ):
                continue
            values = _literal_string_sequence(statement.value)
            if values is not None:
                exports.extend(values)
    return frozenset(exports)


def _extract_imports(tree: ast.Module) -> Mapping[str, tuple[str, str]]:
    imports: dict[str, tuple[str, str]] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.ImportFrom):
            continue
        if statement.level != 0 or statement.module is None:
            continue
        for alias in statement.names:
            if alias.name == "*":
                continue
            local_name = alias.asname or alias.name
            imports[local_name] = (statement.module, alias.name)
    return imports


def _extract_definitions(tree: ast.Module) -> frozenset[str]:
    return frozenset(
        statement.name
        for statement in tree.body
        if isinstance(
            statement,
            (
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.FunctionDef,
            ),
        )
    )


def _load_module_facts() -> Mapping[str, ModuleFacts]:
    repository_root = _repository_root()
    source_root = repository_root / "src"
    package_root = source_root / "gf_wordbench"
    facts: dict[str, ModuleFacts] = {}

    for path in sorted(package_root.rglob("*.py")):
        module = _module_name(source_root, path)
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as error:
            pytest.fail(f"cannot parse {path}: {error}")

        facts[module] = ModuleFacts(
            module=module,
            path=path,
            tree=tree,
            definitions=_extract_definitions(tree),
            exports=_extract_exports(tree),
            imports=_extract_imports(tree),
        )

    assert facts, "no GF Wordbench source modules were discovered"
    return facts


@pytest.fixture(scope="module")
def module_facts() -> Mapping[str, ModuleFacts]:
    return _load_module_facts()


def _definitions_by_symbol(
    facts: Mapping[str, ModuleFacts],
) -> Mapping[str, tuple[str, ...]]:
    owners: defaultdict[str, list[str]] = defaultdict(list)
    for module, module_fact in facts.items():
        for symbol in module_fact.definitions:
            owners[symbol].append(module)
    return {
        symbol: tuple(sorted(modules))
        for symbol, modules in owners.items()
    }


def _called_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _string_literals(node: ast.AST) -> frozenset[str]:
    return frozenset(
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
    )


def _write_calls(tree: ast.Module) -> Iterator[ast.Call]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node)
        if name not in WRITE_PRIMITIVES:
            continue
        if name == "open":
            mode: str | None = None
            if len(node.args) >= 2:
                candidate = node.args[1]
                if isinstance(candidate, ast.Constant) and isinstance(
                    candidate.value,
                    str,
                ):
                    mode = candidate.value
            for keyword in node.keywords:
                if (
                    keyword.arg == "mode"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    mode = keyword.value.value
            if mode is None or not any(flag in mode for flag in "wax+"):
                continue
        yield node


def test_owned_writer_modules_exist_and_export_their_contracts(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    failures: list[str] = []

    for contract in OWNED_WRITERS:
        owner = module_facts.get(contract.owner_module)
        if owner is None:
            failures.append(
                f"{contract.artifact}: missing owner module "
                f"{contract.owner_module}"
            )
            continue

        if not owner.exports:
            failures.append(
                f"{contract.owner_module}: owner module has no explicit __all__"
            )

        for symbol in contract.symbols:
            if symbol not in owner.definitions:
                failures.append(
                    f"{contract.artifact}: {contract.owner_module} does not "
                    f"define {symbol}"
                )
            if symbol not in owner.exports:
                failures.append(
                    f"{contract.artifact}: {contract.owner_module} does not "
                    f"export {symbol} through __all__"
                )

    assert not failures, "\n".join(failures)


def test_owned_writer_symbols_have_one_definition(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    definitions = _definitions_by_symbol(module_facts)
    failures: list[str] = []

    for contract in OWNED_WRITERS:
        for symbol in contract.symbols:
            actual = definitions.get(symbol, ())
            expected = (contract.owner_module,)
            if actual != expected:
                failures.append(
                    f"{contract.artifact}: {symbol} definitions are "
                    f"{actual!r}; expected {expected!r}"
                )

    assert not failures, "\n".join(failures)


def test_reporting_public_is_a_pure_registered_facade(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    facade = module_facts.get(REPORTING_FACADE)
    assert facade is not None, f"missing facade module {REPORTING_FACADE}"

    forbidden_definitions = sorted(
        facade.definitions.intersection(REPORTING_FACADE_EXPORTS)
    )
    assert not forbidden_definitions, (
        f"{REPORTING_FACADE} redefines owned symbols: "
        + ", ".join(forbidden_definitions)
    )

    assert facade.exports == frozenset(REPORTING_FACADE_EXPORTS), (
        f"{REPORTING_FACADE} __all__ drifted: "
        f"actual={sorted(facade.exports)!r}, "
        f"expected={sorted(REPORTING_FACADE_EXPORTS)!r}"
    )

    failures: list[str] = []
    for local_name, expected_import in REPORTING_FACADE_EXPORTS.items():
        actual = facade.imports.get(local_name)
        if actual != expected_import:
            failures.append(
                f"{local_name}: imported from {actual!r}; "
                f"expected {expected_import!r}"
            )

    assert not failures, "\n".join(failures)


def test_registered_cross_file_models_have_one_owner(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    definitions = _definitions_by_symbol(module_facts)
    failures: list[str] = []

    for symbol, expected_owner in ANTI_DUPLICATION_OWNERS.items():
        actual = definitions.get(symbol, ())
        if actual != (expected_owner,):
            failures.append(
                f"{symbol}: definitions are {actual!r}; "
                f"expected only {(expected_owner,)!r}"
            )

    assert not failures, "\n".join(failures)


def test_forbidden_competing_modules_do_not_define_owned_models(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    failures: list[str] = []

    for symbol, forbidden_modules in FORBIDDEN_COMPETING_SYMBOLS.items():
        for module in sorted(forbidden_modules):
            facts = module_facts.get(module)
            if facts is not None and symbol in facts.definitions:
                failures.append(
                    f"{module} illegally defines owner symbol {symbol}"
                )

    assert not failures, "\n".join(failures)


def test_fixed_artifact_literals_are_not_written_by_observers(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    failures: list[str] = []

    for module, facts in module_facts.items():
        for call in _write_calls(facts.tree):
            literals = _string_literals(call)
            for artifact, allowed_modules in FIXED_ARTIFACT_WRITER_MODULES.items():
                if artifact not in literals:
                    continue
                if module in allowed_modules:
                    continue
                failures.append(
                    f"{facts.path}:{call.lineno}: {module} writes owned "
                    f"artifact literal {artifact!r}; allowed writers are "
                    f"{sorted(allowed_modules)!r}"
                )

    assert not failures, "\n".join(failures)


def test_manifest_is_not_registered_as_its_own_payload(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    declarations = module_facts.get(
        "gf_wordbench.reporting.manifest.declarations"
    )
    builder = module_facts.get("gf_wordbench.reporting.manifest.builder")

    assert declarations is not None, "missing manifest declarations module"
    assert builder is not None, "missing manifest builder module"

    declaration_source = declarations.path.read_text(encoding="utf-8")
    builder_source = builder.path.read_text(encoding="utf-8")

    declaration_guard = (
        "manifest.json must not be declared" in declaration_source
        or "manifest.json cannot be an artifact declaration"
        in declaration_source
    )
    builder_guard = (
        "manifest.json must not include itself" in builder_source
        or "manifest must not include itself" in builder_source
    )

    assert declaration_guard, (
        "manifest declarations must explicitly reject manifest.json as a "
        "catalogued artifact"
    )
    assert builder_guard, (
        "manifest builder must explicitly reject manifest self-inclusion"
    )


def test_path_model_owns_canonical_run_artifact_locations(
    module_facts: Mapping[str, ModuleFacts],
) -> None:
    model_module = module_facts.get("gf_wordbench.runs.models.paths")
    factory_module = module_facts.get("gf_wordbench.runs.paths")

    assert model_module is not None, "missing RunPaths owner module"
    assert factory_module is not None, "missing run-path construction module"
    assert "RunPaths" in model_module.definitions
    assert "RunPaths" not in factory_module.definitions

    required_literals = {
        "summary.json",
        "summary.md",
        "AI_READY.md",
        "top_errors.txt",
        "manifest.json",
        "master.log",
        "ALL_SCAN_LOGS.TXT",
        "ALL_LOGS.TXT",
    }
    actual_literals = _string_literals(factory_module.tree)
    missing = sorted(required_literals.difference(actual_literals))
    assert not missing, (
        "run-path construction does not own every canonical artifact path: "
        + ", ".join(missing)
    )
