"""Architectural contracts for GF Wordbench reporting."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping, Sequence
import importlib
from pathlib import Path
import sys
from types import ModuleType
from typing import Final, TypeAlias, cast

import pytest

pytestmark = pytest.mark.contract

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_SOURCE_ROOT: Final[Path] = _REPOSITORY_ROOT / "src"
_PACKAGE_ROOT: Final[Path] = _SOURCE_ROOT / "gf_wordbench"
_REPORTING_ROOT: Final[Path] = _PACKAGE_ROOT / "reporting"
_REPORTING_PACKAGE: Final[str] = "gf_wordbench.reporting"

if str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))

_REPORTING_FILES: Final[tuple[str, ...]] = (
    "__init__.py",
    "artifacts.py",
    "ports.py",
    "public.py",
    "publisher.py",
    "ai_packet/__init__.py",
    "ai_packet/evidence.py",
    "ai_packet/excerpts.py",
    "ai_packet/renderer.py",
    "details/__init__.py",
    "details/writer.py",
    "logs/__init__.py",
    "logs/aggregates.py",
    "logs/lifecycle.py",
    "logs/process_streams.py",
    "logs/redaction.py",
    "logs/scan_logs.py",
    "logs/subject_keys.py",
    "logs/truncation.py",
    "manifest/__init__.py",
    "manifest/builder.py",
    "manifest/declarations.py",
    "manifest/hashing.py",
    "manifest/media_types.py",
    "manifest/models.py",
    "manifest/requiredness.py",
    "manifest/verifier.py",
    "schemas/__init__.py",
    "schemas/compatibility.py",
    "schemas/manifest_v1.py",
    "schemas/migrations.py",
    "schemas/registry.py",
    "schemas/summary_v1.py",
    "schemas/validation.py",
    "summary/__init__.py",
    "summary/json_writer.py",
    "summary/markdown_writer.py",
    "summary/projection.py",
)

_PACKAGE_INITIALIZERS: Final[tuple[str, ...]] = tuple(
    path for path in _REPORTING_FILES if path.endswith("__init__.py")
)
_EMPTY_INITIALIZERS: Final[frozenset[str]] = frozenset(
    path for path in _PACKAGE_INITIALIZERS if path != "manifest/__init__.py"
)
_OWNER_FILES: Final[tuple[str, ...]] = tuple(
    path for path in _REPORTING_FILES if not path.endswith("__init__.py")
)

_PUBLIC_EXPORT_OWNERS: Final[tuple[tuple[str, str], ...]] = (
    ("build_manifest", "gf_wordbench.reporting.manifest.builder"),
    ("publish_reports", "gf_wordbench.reporting.publisher"),
    ("verify_manifest", "gf_wordbench.reporting.manifest.verifier"),
    ("write_ai_ready", "gf_wordbench.reporting.ai_packet.renderer"),
    ("write_all_logs", "gf_wordbench.reporting.logs.aggregates"),
    ("write_all_scan_logs", "gf_wordbench.reporting.logs.aggregates"),
    ("write_manifest", "gf_wordbench.reporting.manifest.builder"),
    ("write_summary_json", "gf_wordbench.reporting.summary.json_writer"),
    ("write_summary_md", "gf_wordbench.reporting.summary.markdown_writer"),
)

_CANONICAL_RUN_PATHS: Final[Mapping[str, str]] = {
    "summary_json": "summary.json",
    "summary_md": "summary.md",
    "ai_ready_md": "AI_READY.md",
    "top_errors_txt": "top_errors.txt",
    "manifest_json": "manifest.json",
    "details_dir": "details",
    "raw_dir": "raw",
    "master_log": "raw/master.log",
    "all_scan_logs": "raw/ALL_SCAN_LOGS.TXT",
    "all_logs": "raw/ALL_LOGS.TXT",
    "raw_compile_dir": "raw/compile",
    "raw_scan_dir": "raw/scan",
    "raw_scenarios_dir": "raw/scenarios",
    "artifacts_dir": "artifacts",
    "gfo_dir": "artifacts/gfo",
    "out_dir": "artifacts/out",
    "pgf_dir": "artifacts/pgf",
}

_FORBIDDEN_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "gf_portfolio",
    "gf_wordbench.bootstrap",
    "gf_wordbench.config",
    "gf_wordbench.entrypoints",
    "gf_wordbench.infrastructure.process",
    "gf_wordbench.projects",
    "gf_wordbench.state",
    "gf_wordbench.validation.compilation",
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.validation.scanning",
    "subprocess",
)
_FORBIDDEN_SCENARIO_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "gf_wordbench.validation.scenarios.artifacts",
        "gf_wordbench.validation.scenarios.assertion_registry",
        "gf_wordbench.validation.scenarios.assertions",
        "gf_wordbench.validation.scenarios.discovery",
        "gf_wordbench.validation.scenarios.execution",
        "gf_wordbench.validation.scenarios.gold_compare",
        "gf_wordbench.validation.scenarios.gold_update",
        "gf_wordbench.validation.scenarios.markers",
        "gf_wordbench.validation.scenarios.normalization",
        "gf_wordbench.validation.scenarios.parser",
        "gf_wordbench.validation.scenarios.service",
    }
)
_FORBIDDEN_PROCESS_CALLS: Final[frozenset[str]] = frozenset(
    {
        "asyncio.create_subprocess_exec",
        "asyncio.create_subprocess_shell",
        "os.popen",
        "os.spawnl",
        "os.spawnle",
        "os.spawnlp",
        "os.spawnlpe",
        "os.spawnv",
        "os.spawnve",
        "os.spawnvp",
        "os.spawnvpe",
        "os.system",
        "subprocess.Popen",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.run",
    }
)
_FORBIDDEN_LOCAL_ATOMIC_CALLS: Final[frozenset[str]] = frozenset(
    {
        "os.replace",
        "tempfile.mkstemp",
        "tempfile.NamedTemporaryFile",
    }
)

ImportBinding: TypeAlias = tuple[str, str]
AtomicWriterPolicy: TypeAlias = tuple[str, str, frozenset[ImportBinding]]

_STABLE_WRITER_POLICIES: Final[tuple[AtomicWriterPolicy, ...]] = (
    (
        "summary/json_writer.py",
        "write_summary_json",
        frozenset(
            {
                ("gf_wordbench.infrastructure.json_io", "write_json"),
                ("gf_wordbench.infrastructure.atomic_io", "atomic_write_bytes"),
                ("gf_wordbench.reporting.artifacts", "publish_text_artifact"),
                ("gf_wordbench.reporting.ports", "ArtifactWriter"),
            }
        ),
    ),
    (
        "summary/markdown_writer.py",
        "write_summary_md",
        frozenset(
            {
                ("gf_wordbench.infrastructure.atomic_io", "atomic_write_text"),
                ("gf_wordbench.reporting.artifacts", "publish_text_artifact"),
                ("gf_wordbench.reporting.ports", "ArtifactWriter"),
            }
        ),
    ),
    (
        "ai_packet/renderer.py",
        "write_ai_ready",
        frozenset(
            {
                ("gf_wordbench.infrastructure.atomic_io", "atomic_write_text"),
                ("gf_wordbench.reporting.artifacts", "publish_text_artifact"),
                ("gf_wordbench.reporting.ports", "ArtifactWriter"),
            }
        ),
    ),
    (
        "manifest/builder.py",
        "write_manifest",
        frozenset(
            {
                ("gf_wordbench.infrastructure.json_io", "write_json"),
                ("gf_wordbench.infrastructure.atomic_io", "atomic_write_bytes"),
                ("gf_wordbench.infrastructure.atomic_io", "atomic_write_text"),
                ("gf_wordbench.reporting.artifacts", "publish_text_artifact"),
                ("gf_wordbench.reporting.ports", "ArtifactWriter"),
            }
        ),
    ),
)


def _source_path(relative_path: str) -> Path:
    return _REPORTING_ROOT / Path(relative_path)


def _module_name(relative_path: str) -> str:
    without_suffix = relative_path.removesuffix(".py")
    parts = without_suffix.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join((_REPORTING_PACKAGE, *parts)) if parts else _REPORTING_PACKAGE


def _parse(relative_path: str) -> ast.Module:
    path = _source_path(relative_path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        pytest.fail(f"cannot read reporting module {path}: {exc}")
    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        pytest.fail(f"cannot parse reporting module {path}: {exc}")


def _assignment_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.List, ast.Tuple)):
        result: set[str] = set()
        for element in target.elts:
            result.update(_assignment_names(element))
        return result
    return set()


def _defined_names(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.partition(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_assignment_names(target))
        elif isinstance(node, ast.AnnAssign):
            names.update(_assignment_names(node.target))
    return frozenset(names)


def _literal_all(tree: ast.Module) -> tuple[str, ...] | None:
    values: list[ast.expr] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                values.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and node.value is not None
        ):
            values.append(node.value)
    if not values:
        return None
    if len(values) != 1:
        pytest.fail("module must assign __all__ exactly once")
    try:
        raw = ast.literal_eval(values[0])
    except (ValueError, TypeError) as exc:
        pytest.fail(f"__all__ must be a literal tuple or list: {exc}")
    if not isinstance(raw, (tuple, list)) or not all(isinstance(value, str) for value in raw):
        pytest.fail("__all__ must contain strings only")
    return tuple(cast("Sequence[str]", raw))


def _from_import_map(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or node.module is None:
            continue
        if node.module == "__future__":
            continue
        for alias in node.names:
            if alias.name == "*":
                pytest.fail("star imports are prohibited in reporting facades")
            bound_name = alias.asname or alias.name
            if bound_name in result:
                pytest.fail(f"duplicate imported facade name {bound_name!r}")
            result[bound_name] = node.module
    return result


def _import_bindings(tree: ast.Module) -> frozenset[ImportBinding]:
    result: set[ImportBinding] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or node.module is None:
            continue
        for alias in node.names:
            if alias.name != "*":
                result.add((node.module, alias.name))
    return frozenset(result)


def _absolute_imports(tree: ast.Module) -> frozenset[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            result.add(node.module)
    return frozenset(result)


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _call_names(tree: ast.Module) -> frozenset[str]:
    return frozenset(
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        if (name := _call_name(node.func)) is not None
    )


def _is_forbidden_import(module_name: str) -> bool:
    if module_name in _FORBIDDEN_SCENARIO_IMPORTS:
        return True
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in _FORBIDDEN_IMPORT_PREFIXES
    )


def _import_module(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        pytest.fail(
            f"failed to import {module_name}: {type(exc).__name__}: {exc}",
            pytrace=True,
        )


def _constant(module: ModuleType, name: str) -> object:
    if not hasattr(module, name):
        pytest.fail(f"{module.__name__} does not define {name}")
    return getattr(module, name)


@pytest.mark.parametrize("relative_path", _REPORTING_FILES)
def test_reporting_fixed_runtime_files_exist(relative_path: str) -> None:
    path = _source_path(relative_path)
    assert path.is_file(), f"missing canonical reporting file: {path.relative_to(_REPOSITORY_ROOT)}"


@pytest.mark.parametrize("relative_path", _PACKAGE_INITIALIZERS)
def test_reporting_package_initializers_are_side_effect_free(relative_path: str) -> None:
    tree = _parse(relative_path)
    violations: list[str] = []
    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__" and node.level == 0:
                continue
            if (
                node.level == 1
                and node.module is not None
                and all(alias.name != "*" for alias in node.names)
            ):
                continue
        if isinstance(node, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            continue
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
        ):
            continue
        violations.append(f"line {getattr(node, 'lineno', '?')}: {type(node).__name__}")
    assert not violations, f"{relative_path} performs package-initializer work: " + ", ".join(
        violations
    )
    exports = _literal_all(tree)
    if relative_path in _EMPTY_INITIALIZERS:
        assert exports in (None, ()), f"{relative_path} must expose an empty package API"
        return

    imported_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
    }
    assert exports is not None, f"{relative_path} must declare its narrow facade API"
    assert set(exports) == imported_names, (
        f"{relative_path} must only re-export symbols imported from owner modules"
    )


@pytest.mark.parametrize("relative_path", _OWNER_FILES)
def test_reporting_owner_modules_have_explicit_valid_all(relative_path: str) -> None:
    tree = _parse(relative_path)
    exports = _literal_all(tree)
    assert exports is not None, f"{relative_path} must declare an explicit __all__"
    assert len(exports) == len(set(exports)), f"{relative_path} has duplicate __all__ names"
    assert all(not name.startswith("_") for name in exports), (
        f"{relative_path} exports a private symbol"
    )
    missing = set(exports).difference(_defined_names(tree))
    assert not missing, f"{relative_path} exports undefined names: {sorted(missing)!r}"


@pytest.mark.parametrize("relative_path", _REPORTING_FILES)
def test_every_reporting_module_imports_and_exports_resolve(relative_path: str) -> None:
    module = _import_module(_module_name(relative_path))
    exports = getattr(module, "__all__", ())
    assert isinstance(exports, (tuple, list)), f"{module.__name__}.__all__ is not ordered"
    assert all(isinstance(name, str) for name in exports)
    missing = [name for name in exports if not hasattr(module, name)]
    assert not missing, f"{module.__name__} exports missing symbols: {missing!r}"


def test_reporting_public_facade_is_an_exact_owner_reexport() -> None:
    tree = _parse("public.py")
    assert not any(
        isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for node in tree.body
    ), "reporting.public must not wrap or redefine owner symbols"

    expected = dict(_PUBLIC_EXPORT_OWNERS)
    assert _from_import_map(tree) == expected
    assert _literal_all(tree) == tuple(expected)

    facade = _import_module("gf_wordbench.reporting.public")
    for name, owner_name in _PUBLIC_EXPORT_OWNERS:
        owner = _import_module(owner_name)
        assert hasattr(owner, name), f"{owner_name} does not own {name}"
        owner_symbol = getattr(owner, name)
        assert getattr(facade, name) is owner_symbol
        assert getattr(owner_symbol, "__module__", owner_name) == owner_name
        owner_exports = getattr(owner, "__all__", ())
        assert name in owner_exports, f"{owner_name} does not publish {name} in __all__"


@pytest.mark.parametrize("relative_path", _REPORTING_FILES)
def test_reporting_does_not_import_execution_or_project_authority(
    relative_path: str,
) -> None:
    tree = _parse(relative_path)
    forbidden = sorted(
        module_name for module_name in _absolute_imports(tree) if _is_forbidden_import(module_name)
    )
    assert not forbidden, (
        f"{relative_path} crosses the reporting boundary through imports: {forbidden!r}"
    )


@pytest.mark.parametrize("relative_path", _REPORTING_FILES)
def test_reporting_never_launches_external_processes(relative_path: str) -> None:
    calls = _call_names(_parse(relative_path))
    forbidden = sorted(calls.intersection(_FORBIDDEN_PROCESS_CALLS))
    assert not forbidden, f"{relative_path} launches a process: {forbidden!r}"


@pytest.mark.parametrize(
    ("relative_path", "writer_name", "approved_bindings"),
    _STABLE_WRITER_POLICIES,
)
def test_stable_report_writers_use_owned_atomic_publication(
    relative_path: str,
    writer_name: str,
    approved_bindings: frozenset[ImportBinding],
) -> None:
    tree = _parse(relative_path)
    assert writer_name in _defined_names(tree), (
        f"{relative_path} must own canonical writer {writer_name}"
    )
    bindings = _import_bindings(tree)
    assert bindings.intersection(approved_bindings), (
        f"{relative_path} must publish through atomic_io, json_io, "
        "reporting.artifacts, or the ArtifactWriter port"
    )
    locally_owned = sorted(
        name
        for name in _defined_names(tree)
        if name.startswith("_atomic_write") or name.startswith("_atomic_replace")
    )
    assert not locally_owned, (
        f"{relative_path} duplicates atomic publication helpers: {locally_owned!r}"
    )
    direct_atomic_calls = sorted(_call_names(tree).intersection(_FORBIDDEN_LOCAL_ATOMIC_CALLS))
    assert not direct_atomic_calls, (
        f"{relative_path} bypasses the atomic publication owner: {direct_atomic_calls!r}"
    )


def test_canonical_report_paths_are_owned_by_the_run_registry(tmp_path: Path) -> None:
    runs_paths = _import_module("gf_wordbench.runs.paths")
    build_run_paths = runs_paths.build_run_paths
    run_id = "20260725_153043"
    run_dir = (tmp_path / f"run_{run_id}").resolve()
    run_dir.mkdir()
    paths = build_run_paths(run_id, run_dir)

    actual = {
        field: cast("Path", getattr(paths, field)).relative_to(run_dir).as_posix()
        for field in _CANONICAL_RUN_PATHS
    }
    assert actual == dict(_CANONICAL_RUN_PATHS)


@pytest.mark.parametrize(
    ("module_name", "name", "expected"),
    (
        (
            "gf_wordbench.reporting.schemas.summary_v1",
            "SUMMARY_SCHEMA_ID",
            "gf-wordbench.run-summary",
        ),
        ("gf_wordbench.reporting.schemas.summary_v1", "SUMMARY_SCHEMA_VERSION", "1.0"),
        ("gf_wordbench.reporting.schemas.summary_v1", "SUMMARY_JSON_FILENAME", "summary.json"),
        (
            "gf_wordbench.reporting.schemas.manifest_v1",
            "ARTIFACT_MANIFEST_SCHEMA_ID",
            "gf-wordbench.artifact-manifest",
        ),
        (
            "gf_wordbench.reporting.schemas.manifest_v1",
            "ARTIFACT_MANIFEST_SCHEMA_VERSION",
            "1.0",
        ),
        (
            "gf_wordbench.reporting.schemas.manifest_v1",
            "ARTIFACT_MANIFEST_FILENAME",
            "manifest.json",
        ),
        (
            "gf_wordbench.reporting.schemas.manifest_v1",
            "ARTIFACT_MANIFEST_HASH_ALGORITHM",
            "sha256",
        ),
        ("gf_wordbench.reporting.summary.json_writer", "SUMMARY_FILENAME", "summary.json"),
        (
            "gf_wordbench.reporting.summary.markdown_writer",
            "SUMMARY_MARKDOWN_FILENAME",
            "summary.md",
        ),
        ("gf_wordbench.reporting.ai_packet.renderer", "FIRST_HEADING", "# AI Ready Packet"),
    ),
)
def test_reporting_schema_and_format_constants_are_canonical(
    module_name: str,
    name: str,
    expected: object,
) -> None:
    module = _import_module(module_name)
    assert _constant(module, name) == expected


def test_summary_schema_identity_is_consistent_across_reporting_owners() -> None:
    summary_schema = _import_module("gf_wordbench.reporting.schemas.summary_v1")
    projection = _import_module("gf_wordbench.reporting.summary.projection")
    assert _constant(projection, "SUMMARY_SCHEMA_ID") == _constant(
        summary_schema,
        "SUMMARY_SCHEMA_ID",
    )
    assert _constant(projection, "SUMMARY_SCHEMA_VERSION") == _constant(
        summary_schema,
        "SUMMARY_SCHEMA_VERSION",
    )


def test_manifest_schema_identity_is_consistent_across_reporting_owners() -> None:
    schema = _import_module("gf_wordbench.reporting.schemas.manifest_v1")
    models = _import_module("gf_wordbench.reporting.manifest.models")
    builder = _import_module("gf_wordbench.reporting.manifest.builder")

    assert _constant(models, "ARTIFACT_MANIFEST_SCHEMA_ID") == _constant(
        schema,
        "ARTIFACT_MANIFEST_SCHEMA_ID",
    )
    assert _constant(builder, "MANIFEST_SCHEMA_ID") == _constant(
        schema,
        "ARTIFACT_MANIFEST_SCHEMA_ID",
    )
    assert _constant(models, "ARTIFACT_MANIFEST_SCHEMA_VERSION") == _constant(
        schema,
        "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    )
    assert _constant(builder, "MANIFEST_SCHEMA_VERSION") == _constant(
        schema,
        "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    )
    assert _constant(models, "ARTIFACT_MANIFEST_FILENAME") == _constant(
        schema,
        "ARTIFACT_MANIFEST_FILENAME",
    )
    assert _constant(builder, "MANIFEST_FILENAME") == _constant(
        schema,
        "ARTIFACT_MANIFEST_FILENAME",
    )
    assert _constant(models, "ARTIFACT_MANIFEST_HASH_ALGORITHM") == _constant(
        schema,
        "ARTIFACT_MANIFEST_HASH_ALGORITHM",
    )
    assert _constant(builder, "MANIFEST_HASH_ALGORITHM") == _constant(
        schema,
        "ARTIFACT_MANIFEST_HASH_ALGORITHM",
    )


def test_human_reports_are_not_machine_schema_dependencies() -> None:
    prohibited_edges: Mapping[str, frozenset[str]] = {
        "summary/json_writer.py": frozenset(
            {
                "gf_wordbench.reporting.summary.markdown_writer",
                "gf_wordbench.reporting.ai_packet.renderer",
            }
        ),
        "summary/markdown_writer.py": frozenset({"gf_wordbench.reporting.ai_packet.renderer"}),
        "ai_packet/renderer.py": frozenset({"gf_wordbench.reporting.summary.markdown_writer"}),
    }
    for relative_path, prohibited in prohibited_edges.items():
        imports = _absolute_imports(_parse(relative_path))
        offending = sorted(imports.intersection(prohibited))
        assert not offending, (
            f"{relative_path} reconstructs facts through another human report: {offending!r}"
        )


def test_aggregate_logs_explicitly_exclude_canonical_reports() -> None:
    module = _import_module("gf_wordbench.reporting.logs.aggregates")
    forbidden = _constant(module, "_FORBIDDEN_OPERATION_PATHS")
    actual = {str(path).replace("\\", "/") for path in cast("Iterable[object]", forbidden)}
    assert actual == {
        "summary.json",
        "summary.md",
        "AI_READY.md",
        "top_errors.txt",
        "manifest.json",
    }
