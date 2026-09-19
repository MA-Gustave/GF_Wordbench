"""Contract tests for the GF Wordbench diagnostics boundary."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass
from importlib import import_module
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Final, Protocol, cast

import pytest

pytestmark = pytest.mark.contract


class _DataclassParamsLike(Protocol):
    frozen: bool


class _PatternMatchView(Protocol):
    pattern_id: str
    raw_excerpt: str
    references: tuple[str, ...]

_DIAGNOSTICS_PACKAGE: Final[str] = "gf_wordbench.diagnostics"
_CANONICAL_PATTERN_ID: Final[str] = (
    r"^DP-(PROC|GFINT|GFTYPE|GFSYN|GFLOAD|GFGEN|GFWARN|SCEN|ART|NORM|GOLD|"
    r"FALLBACK)-[0-9]{3,}$"
)
_PUBLIC_FACADE_OWNERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "DEFAULT_TOP_ERROR_POLICY": ("gf_wordbench.diagnostics.classification.top_errors"),
        "DiagnosticEvidence": "gf_wordbench.diagnostics.models",
        "DiagnosticParseResult": "gf_wordbench.diagnostics.models",
        "DiagnosticRecord": "gf_wordbench.diagnostics.models",
        "TopErrorAggregationPolicy": ("gf_wordbench.diagnostics.classification.top_errors"),
        "TopErrorCandidate": "gf_wordbench.diagnostics.classification.top_errors",
        "bucket_top_errors": "gf_wordbench.diagnostics.classification.top_errors",
        "classify_file_results": ("gf_wordbench.diagnostics.classification.service"),
        "classify_scenario_results": ("gf_wordbench.diagnostics.classification.service"),
        "parse_diagnostics": "gf_wordbench.diagnostics.parsing.service",
    }
)
_EMPTY_INITIALIZERS: Final[tuple[str, ...]] = (
    "gf_wordbench.diagnostics",
    "gf_wordbench.diagnostics.classification",
    "gf_wordbench.diagnostics.patterns",
    "gf_wordbench.diagnostics.tools",
)
_VOCABULARY_OWNED_TYPES: Final[frozenset[str]] = frozenset(
    {
        "DiagnosticCodeFamily",
        "DiagnosticLineKind",
        "DiagnosticOperationKind",
        "DiagnosticOrigin",
        "DiagnosticSeverity",
        "DiagnosticStream",
        "DiagnosticStreamScope",
        "EvidenceConfidence",
        "PatternConfidence",
        "PatternDomain",
        "PatternLifecycle",
        "PresentationConfidence",
    }
)
_FORBIDDEN_DIAGNOSTIC_IMPORTS: Final[tuple[str, ...]] = (
    "gf_portfolio",
    "gf_wordbench.entrypoints",
    "gf_wordbench.reporting",
)


@dataclass(frozen=True, slots=True)
class _Definition:
    pattern_id: str


class _Registry:
    catalog_version = "1.0.0"
    parser_version = "1.0.0"

    def __init__(self, pattern_ids: tuple[str, ...]) -> None:
        self._pattern_ids = pattern_ids
        self._definitions = {pattern_id: _Definition(pattern_id) for pattern_id in pattern_ids}

    def get(self, pattern_id: str) -> _Definition:
        return self._definitions[pattern_id]

    def select(self, selection: object) -> tuple[_Definition, ...]:
        del selection
        return tuple(self._definitions.values())

    def pattern_ids(self) -> tuple[str, ...]:
        return self._pattern_ids


def _repository_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    diagnostics = root / "src" / "gf_wordbench" / "diagnostics"
    if not diagnostics.is_dir():
        raise AssertionError(f"canonical diagnostics source directory is missing: {diagnostics}")
    return root


def _diagnostics_root() -> Path:
    return _repository_root() / "src" / "gf_wordbench" / "diagnostics"


def _module_name(path: Path) -> str:
    relative = path.relative_to(_repository_root() / "src").with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _diagnostic_module_paths() -> tuple[Path, ...]:
    return tuple(sorted(_diagnostics_root().rglob("*.py")))


def _diagnostic_module_names() -> tuple[str, ...]:
    return tuple(_module_name(path) for path in _diagnostic_module_paths())


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _literal_all(tree: ast.Module) -> tuple[str, ...] | None:
    for statement in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
            value = statement.value
        if not isinstance(target, ast.Name) or target.id != "__all__":
            continue
        if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return None
        names: list[str] = []
        for element in value.elts:
            if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                return None
            names.append(element.value)
        return tuple(names)
    return None


def _defined_public_symbols(path: Path) -> frozenset[str]:
    tree = _tree(path)
    exported = _literal_all(tree)
    if exported is None:
        return frozenset()
    definitions = {
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    return frozenset(definitions.intersection(exported))


def _import_targets(path: Path) -> Iterator[str]:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            yield node.module


def _import_all_modules() -> Mapping[str, ModuleType]:
    modules: dict[str, ModuleType] = {}
    failures: list[str] = []
    for module_name in _diagnostic_module_names():
        try:
            modules[module_name] = import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    assert not failures, "diagnostic runtime modules must all import:\n" + "\n".join(failures)
    return MappingProxyType(modules)


def _public_names(module: ModuleType) -> tuple[str, ...]:
    value = getattr(module, "__all__", None)
    assert isinstance(value, (tuple, list)), f"{module.__name__} must define literal __all__"
    assert all(isinstance(name, str) for name in value)
    return tuple(cast("Iterable[str]", value))


def _pattern_id_literals(path: Path) -> Iterator[tuple[str, str]]:
    tree = _tree(path)
    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            value = statement.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in targets:
                if isinstance(target, ast.Name) and "PATTERN_ID" in target.id:
                    yield target.id, value.value
        if isinstance(statement, ast.ClassDef) and statement.name.endswith("PatternId"):
            for member in statement.body:
                if not isinstance(member, ast.Assign) or len(member.targets) != 1:
                    continue
                target = member.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(member.value, ast.Constant) and isinstance(member.value.value, str):
                    yield f"{statement.name}.{target.id}", member.value.value


def _make_match(*, line: int = 7) -> _PatternMatchView:
    models = import_module("gf_wordbench.diagnostics.models")
    return cast(
        "_PatternMatchView",
        models.PatternMatch(
            pattern_id="DP-GFTYPE-001",
            operation="compile_module",
            stream="stderr",
            start_line=line,
            end_line=line,
            severity="error",
            error_kind="TYPE",
            message="Expected type X but inferred Y",
            detail="module=Demo",
            source_path=Path("grammar/Demo.gf"),
            source_module="Demo",
            line=line,
            column=3,
            pattern_version="1.0",
            confidence="high",
            raw_excerpt="grammar/Demo.gf:7:3: Expected type X but inferred Y",
            continuation_lines=("Expected: X", "Inferred: Y"),
            references=("stderr.log#L7", "grammar/Demo.gf#L7"),
            metadata={"origin": "gf", "nested": {"stable": True}},
        ),
    )


def test_all_diagnostic_runtime_modules_import() -> None:
    modules = _import_all_modules()
    assert set(modules) == set(_diagnostic_module_names())


@pytest.mark.parametrize("module_name", _EMPTY_INITIALIZERS)
def test_empty_package_initializers_are_narrow(module_name: str) -> None:
    module = import_module(module_name)
    assert _public_names(module) == ()

    module_path = Path(cast("str", module.__file__))
    imports = tuple(_import_targets(module_path))
    assert imports in ((), ("__future__",))


def test_parsing_initializer_is_a_single_symbol_facade() -> None:
    module = import_module("gf_wordbench.diagnostics.parsing")
    assert _public_names(module) == ("parse_diagnostics",)
    assert module.parse_diagnostics.__module__ == ("gf_wordbench.diagnostics.parsing.service")


def test_public_facade_exports_exact_registered_contracts() -> None:
    module = import_module("gf_wordbench.diagnostics.public")
    assert set(_public_names(module)) == set(_PUBLIC_FACADE_OWNERS)
    for symbol, owner in _PUBLIC_FACADE_OWNERS.items():
        exported = getattr(module, symbol)
        assert getattr(exported, "__module__", owner) == owner


def test_owner_modules_publish_explicit_valid_all() -> None:
    modules = _import_all_modules()
    failures: list[str] = []
    for module_name, module in modules.items():
        names = _public_names(module)
        if len(names) != len(set(names)):
            failures.append(f"{module_name}: duplicate __all__ entries")
        for name in names:
            if name.startswith("_"):
                failures.append(f"{module_name}: private export {name}")
            if not hasattr(module, name):
                failures.append(f"{module_name}: missing export {name}")
    assert not failures, "\n".join(failures)


def test_public_contract_definitions_have_one_owner() -> None:
    owners: defaultdict[str, list[str]] = defaultdict(list)
    for path in _diagnostic_module_paths():
        module_name = _module_name(path)
        for symbol in _defined_public_symbols(path):
            owners[symbol].append(module_name)

    duplicates = {
        symbol: tuple(sorted(modules))
        for symbol, modules in owners.items()
        if len(set(modules)) > 1
    }
    assert duplicates == {}, "public diagnostic symbols have multiple owners: " + repr(duplicates)


def test_vocabulary_types_are_defined_only_by_vocabulary_owner() -> None:
    violations: list[str] = []
    for path in _diagnostic_module_paths():
        if path.name == "vocabulary.py":
            continue
        definitions = {
            statement.name for statement in _tree(path).body if isinstance(statement, ast.ClassDef)
        }
        for name in sorted(definitions.intersection(_VOCABULARY_OWNED_TYPES)):
            violations.append(f"{_module_name(path)} redefines {name}")
    assert violations == []


def test_diagnostics_dependency_direction_is_preserved() -> None:
    violations: list[str] = []
    for path in _diagnostic_module_paths():
        module_name = _module_name(path)
        for target in _import_targets(path):
            for forbidden in _FORBIDDEN_DIAGNOSTIC_IMPORTS:
                if target == forbidden or target.startswith(f"{forbidden}."):
                    violations.append(f"{module_name} imports forbidden boundary {target}")
            if module_name.startswith("gf_wordbench.diagnostics.parsing") and (
                target == "gf_wordbench.diagnostics.classification"
                or target.startswith("gf_wordbench.diagnostics.classification.")
            ):
                violations.append(f"parser imports classifier: {module_name} -> {target}")
            if module_name.startswith("gf_wordbench.diagnostics.classification") and (
                target == "gf_wordbench.diagnostics.parsing"
                or target.startswith("gf_wordbench.diagnostics.parsing.")
            ):
                violations.append(f"classifier imports parser: {module_name} -> {target}")
    assert violations == []


def test_production_diagnostics_use_no_wildcard_imports() -> None:
    violations: list[str] = []
    for path in _diagnostic_module_paths():
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                violations.append(f"{_module_name(path)}:{node.lineno}")
    assert violations == []


def test_all_public_dataclasses_are_frozen_and_slotted() -> None:
    modules = _import_all_modules()
    violations: list[str] = []
    for module_name, module in modules.items():
        for name in _public_names(module):
            value = getattr(module, name)
            if not isinstance(value, type) or not is_dataclass(value):
                continue
            if value.__module__ != module_name:
                continue
            parameters = cast(_DataclassParamsLike, getattr(value, "__dataclass_params__"))
            if not parameters.frozen:
                violations.append(f"{module_name}.{name} is not frozen")
            if "__dict__" in value.__dict__ or "__slots__" not in value.__dict__:
                violations.append(f"{module_name}.{name} is not slotted")
    assert violations == []


def test_canonical_pattern_identifier_contract() -> None:
    vocabulary = import_module("gf_wordbench.diagnostics.vocabulary")
    assert vocabulary.make_pattern_id(vocabulary.PatternDomain.PROCESS, 1) == "DP-PROC-001"
    assert vocabulary.pattern_domain("DP-GFTYPE-017") is vocabulary.PatternDomain.GF_TYPE
    assert vocabulary.validate_pattern_id("DP-FALLBACK-001") == "DP-FALLBACK-001"

    invalid = (
        "GF-DIAG-PROC-001",
        "DIAG-UNKNOWN",
        "DP-PROC-1",
        "DP-UNKNOWN-001",
        " DP-PROC-001",
        "DP-PROC-001 ",
    )
    for value in invalid:
        with pytest.raises(ValueError):
            vocabulary.validate_pattern_id(value)


def test_pattern_identifiers_have_one_literal_owner_and_canonical_shape() -> None:
    import re

    owners: defaultdict[str, list[str]] = defaultdict(list)
    invalid: list[str] = []
    for path in sorted((_diagnostics_root() / "patterns").glob("*.py")):
        module_name = _module_name(path)
        for symbol, pattern_id in _pattern_id_literals(path):
            owners[pattern_id].append(f"{module_name}.{symbol}")
            if re.fullmatch(_CANONICAL_PATTERN_ID, pattern_id) is None:
                invalid.append(f"{module_name}.{symbol}={pattern_id!r}")

    assert invalid == []
    duplicates = {
        pattern_id: tuple(symbols)
        for pattern_id, symbols in owners.items()
        if len(set(symbols)) > 1
    }
    assert duplicates == {}, "pattern IDs have multiple owners: " + repr(duplicates)


def test_pattern_registry_rejects_duplicates_and_priority_drift() -> None:
    models = import_module("gf_wordbench.diagnostics.models")

    def no_match(evidence: object) -> None:
        del evidence
        return None

    first = models.DiagnosticPattern(
        pattern_id="DP-PROC-001",
        operations=frozenset({"all"}),
        streams=frozenset({"process-state"}),
        priority=10,
        confidence="authoritative",
        error_kind="TIMEOUT",
        severity="fatal",
        matcher=no_match,
    )
    second = models.DiagnosticPattern(
        pattern_id="DP-PROC-002",
        operations=frozenset({"all"}),
        streams=frozenset({"process-state"}),
        priority=20,
        confidence="authoritative",
        error_kind="TOOL",
        severity="fatal",
        matcher=no_match,
    )

    registry = models.DiagnosticPatternRegistry(
        parser_version="1.0",
        patterns=(first, second),
    )
    assert registry.get("DP-PROC-001") is first
    assert registry.applicable("compile_module", stream="process-state") == (
        first,
        second,
    )

    with pytest.raises(ValueError, match="duplicate"):
        models.DiagnosticPatternRegistry(
            parser_version="1.0",
            patterns=(first, first),
        )
    with pytest.raises(ValueError, match="priority"):
        models.DiagnosticPatternRegistry(
            parser_version="1.0",
            patterns=(second, first),
        )


def test_port_registry_contract_is_structural_and_deterministic() -> None:
    ports = import_module("gf_wordbench.diagnostics.ports")
    registry = _Registry(("DP-PROC-001", "DP-GFTYPE-001"))

    assert isinstance(registry, ports.DiagnosticPatternRegistry)
    assert ports.validate_pattern_registry(registry) == (
        "1.0.0",
        "1.0.0",
        "DP-PROC-001",
        "DP-GFTYPE-001",
    )

    with pytest.raises(ValueError, match="duplicates"):
        ports.validate_pattern_registry(_Registry(("DP-PROC-001", "DP-PROC-001")))


def test_evidence_is_immutable_and_preserves_separate_stream_identity(
    tmp_path: Path,
) -> None:
    models = import_module("gf_wordbench.diagnostics.models")
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"
    evidence = models.DiagnosticEvidence(
        operation_kind="compile_module",
        execution_state="completed",
        exit_code=1,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_text="compiler banner",
        stderr_text="type error",
        metadata={"run_id": "run-001", "nested": {"stable": True}},
    )

    stderr = evidence.for_stream("stderr")
    assert stderr.source_stream is models.DiagnosticStream.STDERR
    assert stderr.raw_path == stderr_path
    assert stderr.text == "type error"
    assert stderr.stdout_path == stdout_path
    assert stderr.stderr_path == stderr_path
    assert isinstance(evidence.metadata, MappingProxyType)
    assert isinstance(evidence.metadata["nested"], MappingProxyType)

    with pytest.raises(TypeError):
        mutable_metadata = cast(
            MutableMapping[str, object],
            evidence.metadata,
        )
        mutable_metadata["run_id"] = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.exit_code = 0


def test_match_to_record_conversion_is_stable_and_lossless() -> None:
    models = import_module("gf_wordbench.diagnostics.models")
    match = _make_match()

    first = models.DiagnosticRecord.from_match(match)
    second = models.DiagnosticRecord.from_match(match)

    assert first == second
    assert first.record_id.startswith("diag-")
    assert len(first.record_id) == len("diag-") + 16
    assert first.pattern_id == match.pattern_id
    assert first.raw_excerpt == match.raw_excerpt
    assert first.references == match.references
    assert first.location.source_path == Path("grammar/Demo.gf")
    assert first.location.line == 7
    assert isinstance(first.metadata, MappingProxyType)

    records = models.records_from_matches((match, match))
    assert records == (first,)


def test_normalized_signatures_remove_incidental_paths_and_numbers() -> None:
    models = import_module("gf_wordbench.diagnostics.models")
    first = models.normalized_diagnostic_signature(
        "TYPE",
        "/tmp/project/A.gf:12 expected 3 arguments",
    )
    second = models.normalized_diagnostic_signature(
        "TYPE",
        "/different/root/B.gf:99 expected 7 arguments",
    )
    assert first == second == "TYPE|<path>:<n> expected <n> arguments"


def test_parse_result_primary_secondary_and_references_are_deterministic() -> None:
    models = import_module("gf_wordbench.diagnostics.models")
    primary = models.DiagnosticRecord.from_match(_make_match(line=7))
    secondary_match = models.PatternMatch(
        pattern_id="DP-GFWARN-001",
        operation="compile_module",
        stream="stderr",
        start_line=9,
        end_line=9,
        severity="warning",
        error_kind="OTHER",
        message="Unused definition",
        confidence="medium",
        raw_excerpt="Unused definition",
        references=("stderr.log#L9", "grammar/Demo.gf#L7"),
    )
    secondary = models.DiagnosticRecord.from_match(secondary_match)

    result = models.DiagnosticParseResult(
        parser_version="1.0",
        status="FAIL",
        gf_version="3.12",
        operation="compile_module",
        records=(primary, secondary),
        primary_record_id=primary.record_id,
    )

    assert result.primary is primary
    assert result.secondary == (secondary,)
    assert result.references == (
        "stderr.log#L7",
        "grammar/Demo.gf#L7",
        "stderr.log#L9",
    )
    assert result.primary_error_kind == primary.error_kind
    assert result.primary_message == primary.message


def test_public_dataclass_fields_use_immutable_collection_contracts() -> None:
    modules = _import_all_modules()
    mutable_annotations = {"list", "dict", "set"}
    violations: list[str] = []
    for module_name, module in modules.items():
        for name in _public_names(module):
            value = getattr(module, name)
            if not isinstance(value, type) or not is_dataclass(value):
                continue
            if value.__module__ != module_name:
                continue
            for field in fields(value):
                annotation = str(field.type).replace("typing.", "")
                if any(
                    annotation == mutable or annotation.startswith(f"{mutable}[")
                    for mutable in mutable_annotations
                ):
                    violations.append(f"{module_name}.{name}.{field.name}: {annotation}")
    assert violations == []
