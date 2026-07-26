from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from typing import Final, cast

import pytest

from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    TargetKind,
    ValidationMode,
    ValidationStatus,
)

pytestmark = pytest.mark.contract

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT: Final[Path] = _REPOSITORY_ROOT / "src" / "gf_wordbench"

_MUTABLE_PUBLIC_DATACLASSES: Final[frozenset[str]] = frozenset(
    {
        "gf_wordbench.reporting.ai_packet.excerpts.ExcerptBudget",
        "gf_wordbench.runs.models.results.FileResult",
        "gf_wordbench.runs.models.results.RunResult",
    }
)

_REQUIRED_PUBLIC_SYMBOLS: Final[Mapping[str, frozenset[str]]] = {
    "gf_wordbench.kernel.serialization": frozenset({"ProducerInfo"}),
    "gf_wordbench.kernel.events": frozenset(
        {"EventField", "ProgressEvent", "LifecycleEvent"}
    ),
    "gf_wordbench.kernel.errors": frozenset({"ErrorInfo"}),
    "gf_wordbench.config.models": frozenset(
        {
            "EnvironmentOverrides",
            "SelectionDefaults",
            "OutputDefaults",
            "SchemaSupport",
            "AppConfig",
            "ValidationTarget",
            "ResolvedEnvironment",
            "ConfigurationIssue",
            "ConfigurationProvenance",
            "ConfigurationResolutionRequest",
            "EnvironmentResolution",
            "ConfigurationResolution",
            "RunConfig",
        }
    ),
    "gf_wordbench.infrastructure.process.models": frozenset(
        {
            "ProcessInput",
            "ArtifactExpectation",
            "ArtifactObservation",
            "ProcessRequest",
            "ProcessEvent",
            "ProcessResult",
        }
    ),
    "gf_wordbench.infrastructure.process.streams": frozenset(
        {
            "CaptureFailure",
            "StreamCaptureSummary",
            "ProcessCapture",
            "CaptureSession",
        }
    ),
    "gf_wordbench.projects.models": frozenset(
        {
            "ProjectIdentity",
            "SourceConfig",
            "GFProjectConfig",
            "ModuleTargets",
            "ValidationPolicy",
            "ProjectConfig",
            "ProjectDiagnostic",
            "ProjectValidationResult",
        }
    ),
    "gf_wordbench.projects.paths": frozenset({"ProjectPaths"}),
    "gf_wordbench.projects.ports": frozenset(
        {"TreeEntry", "ArchiveReceipt", "LifecycleLockRequest"}
    ),
    "gf_wordbench.projects.initializer": frozenset(
        {"ProjectInitializationRequest", "ProjectInitializationResult"}
    ),
    "gf_wordbench.projects.resetter": frozenset(
        {"ResetRequest", "ResetPlan", "PhaseRecord", "ResetFailure", "ResetResult"}
    ),
    "gf_wordbench.projects.migrator": frozenset(
        {
            "ProjectMigrationRequest",
            "ProjectMigrationIssue",
            "ProjectMigrationAction",
            "ProjectMigrationPlan",
            "ProjectMigrationResult",
        }
    ),
    "gf_wordbench.state.models": frozenset(
        {
            "EnvironmentState",
            "SelectionState",
            "LastRunState",
            "AppState",
            "StateDiagnostic",
            "StateLoadResult",
        }
    ),
    "gf_wordbench.runs.models.config": frozenset({"RunConfig"}),
    "gf_wordbench.runs.models.paths": frozenset({"RunPaths"}),
    "gf_wordbench.runs.models.results": frozenset(
        {"FileResult", "RunTotals", "RunResult"}
    ),
    "gf_wordbench.validation.compilation.models": frozenset(
        {
            "CompileTarget",
            "CompileRequest",
            "ArtifactCheckItem",
            "ArtifactCheck",
            "GFVersionResult",
            "CompileResult",
        }
    ),
    "gf_wordbench.validation.scanning.models": frozenset(
        {
            "ScanCounts",
            "ScanRuleDefinition",
            "ScanFinding",
            "ScanDiagnostic",
            "StaticScanRequest",
            "StaticScanResult",
        }
    ),
    "gf_wordbench.validation.selection.models": frozenset(
        {
            "SelectionTarget",
            "SelectionCandidate",
            "ExcludedFileEntry",
            "SelectionCounts",
            "FileSelection",
        }
    ),
    "gf_wordbench.validation.scenarios.models": frozenset(
        {
            "ScenarioSpec",
            "ScenarioSectionResult",
            "ScenarioAssertionResult",
            "ScenarioResult",
        }
    ),
    "gf_wordbench.validation.regression.models": frozenset(
        {
            "SubjectDetails",
            "RegressionSubject",
            "DiffEntry",
            "RunSnapshotMetadata",
            "RegressionSnapshot",
            "CompatibilityDecision",
            "RegressionComparison",
        }
    ),
    "gf_wordbench.validation.release.models": frozenset(
        {"ReleaseGate", "ReleaseGateResult", "ReleaseDecision"}
    ),
    "gf_wordbench.diagnostics.models": frozenset(
        {
            "ArtifactObservation",
            "DiagnosticLocation",
            "DiagnosticLine",
            "DiagnosticStreamEvidence",
            "DiagnosticEvidence",
            "PatternMatch",
            "DiagnosticRecord",
            "DiagnosticPattern",
            "DiagnosticParseWarning",
            "DiagnosticParseResult",
            "DiagnosticPatternRegistry",
        }
    ),
    "gf_wordbench.diagnostics.tools.models": frozenset(
        {
            "ToolVersionPolicy",
            "ToolExecutableResolution",
            "ToolInputContract",
            "ToolFlagSpec",
            "ToolEnvironmentPolicy",
            "ToolPathPolicy",
            "ToolOutputLimits",
            "DiagnosticToolSpec",
            "ToolConfirmationRecord",
            "DiagnosticToolRequest",
            "ToolOutputArtifact",
            "DiagnosticToolResult",
        }
    ),
    "gf_wordbench.reporting.artifacts": frozenset(
        {
            "ArtifactDeclaration",
            "PublishedArtifact",
            "ArtifactWriteRequest",
            "ArtifactVerification",
        }
    ),
    "gf_wordbench.reporting.manifest.models": frozenset(
        {
            "ArtifactManifestEntry",
            "ArtifactManifest",
            "ManifestWriteResult",
            "ManifestVerificationResult",
        }
    ),
}

_FORBIDDEN_OWNER_DEFINITIONS: Final[Mapping[str, frozenset[str]]] = {
    "gf_wordbench.config.models": frozenset(
        {"ProducerInfo", "ValidationMode", "TargetKind"}
    ),
    "gf_wordbench.state.models": frozenset({"ProducerInfo", "ValidationMode"}),
    "gf_wordbench.infrastructure.process.models": frozenset(
        {"CancellationToken", "ProcessCapture"}
    ),
    "gf_wordbench.projects.filesystem_adapter": frozenset(
        {"TreeEntry", "TreeEntryKind"}
    ),
    "gf_wordbench.projects.models": frozenset(
        {
            "ProjectValidationReport",
            "ResetRequest",
            "ResetPlan",
            "ResetResult",
            "ProjectMigrationRequest",
            "ProjectMigrationPlan",
            "ProjectMigrationResult",
        }
    ),
}

_MUTABLE_ANNOTATION_NAMES: Final[frozenset[str]] = frozenset(
    {
        "list",
        "dict",
        "set",
        "List",
        "Dict",
        "Set",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
    }
)


@dataclass(frozen=True, slots=True)
class _DataclassDeclaration:
    module_name: str
    path: Path
    class_name: str
    frozen: bool
    slots: bool
    annotations: tuple[ast.expr, ...]
    defaults: tuple[ast.expr, ...]

    @property
    def qualified_name(self) -> str:
        return f"{self.module_name}.{self.class_name}"


def _module_path(module_name: str) -> Path:
    relative = module_name.removeprefix("gf_wordbench.").replace(".", "/")
    candidate = _PACKAGE_ROOT / f"{relative}.py"
    if candidate.is_file():
        return candidate
    package_candidate = _PACKAGE_ROOT / relative / "__init__.py"
    if package_candidate.is_file():
        return package_candidate
    raise AssertionError(f"runtime module is missing: {module_name}")


def _module_name(path: Path) -> str:
    relative = path.relative_to(_PACKAGE_ROOT).with_suffix("")
    parts = relative.parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(("gf_wordbench", *parts))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _public_names(tree: ast.Module) -> tuple[str, ...] | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if not isinstance(target, ast.Name) or target.id != "__all__":
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, tuple | list):
            raise AssertionError("__all__ must be a literal tuple or list")
        if not all(isinstance(item, str) for item in value):
            raise AssertionError("__all__ must contain only strings")
        return tuple(cast(list[str] | tuple[str, ...], value))
    return None


def _bound_names(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.partition(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
    return frozenset(names)


def _defined_names(tree: ast.Module) -> frozenset[str]:
    return frozenset(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    )


def _dataclass_options(node: ast.ClassDef) -> tuple[bool, bool] | None:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return False, False
        if not isinstance(decorator, ast.Call):
            continue
        if isinstance(decorator.func, ast.Name):
            is_dataclass_decorator = decorator.func.id == "dataclass"
        else:
            is_dataclass_decorator = (
                isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "dataclass"
            )
        if not is_dataclass_decorator:
            continue
        values: dict[str, bool] = {}
        for keyword in decorator.keywords:
            if keyword.arg not in {"frozen", "slots"}:
                continue
            if not isinstance(keyword.value, ast.Constant) or not isinstance(
                keyword.value.value, bool
            ):
                raise AssertionError(
                    f"{node.name} must declare literal dataclass options"
                )
            values[keyword.arg] = keyword.value.value
        return values.get("frozen", False), values.get("slots", False)
    return None


def _public_dataclass_declarations() -> tuple[_DataclassDeclaration, ...]:
    declarations: list[_DataclassDeclaration] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        tree = _parse(path)
        public_names = _public_names(tree)
        if public_names is None:
            continue
        public_set = frozenset(public_names)
        module_name = _module_name(path)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name not in public_set:
                continue
            options = _dataclass_options(node)
            if options is None:
                continue
            annotations: list[ast.expr] = []
            defaults: list[ast.expr] = []
            for statement in node.body:
                if not isinstance(statement, ast.AnnAssign):
                    continue
                annotations.append(statement.annotation)
                if statement.value is not None:
                    defaults.append(statement.value)
            frozen, slots = options
            declarations.append(
                _DataclassDeclaration(
                    module_name=module_name,
                    path=path,
                    class_name=node.name,
                    frozen=frozen,
                    slots=slots,
                    annotations=tuple(annotations),
                    defaults=tuple(defaults),
                )
            )
    return tuple(declarations)


def _annotation_uses_mutable_collection(annotation: ast.expr) -> bool:
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name) and node.id in _MUTABLE_ANNOTATION_NAMES:
            return True
        if isinstance(node, ast.Attribute) and node.attr in _MUTABLE_ANNOTATION_NAMES:
            return True
    return False


def _is_direct_mutable_default(value: ast.expr) -> bool:
    if isinstance(value, ast.List | ast.Dict | ast.Set):
        return True
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in {"list", "dict", "set"}
    )


def _enum_values(enum_type: type[StrEnum]) -> tuple[str, ...]:
    return tuple(item.value for item in enum_type)


def test_required_model_owners_declare_explicit_public_symbols() -> None:
    failures: list[str] = []
    for module_name, required_names in _REQUIRED_PUBLIC_SYMBOLS.items():
        path = _module_path(module_name)
        public_names = _public_names(_parse(path))
        if public_names is None:
            failures.append(f"{module_name} has no explicit __all__")
            continue
        missing = required_names.difference(public_names)
        if missing:
            failures.append(f"{module_name} is missing: {', '.join(sorted(missing))}")
    assert not failures, "\n".join(failures)


def test_every_literal_public_api_resolves_to_a_module_binding() -> None:
    failures: list[str] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        tree = _parse(path)
        public_names = _public_names(tree)
        if public_names is None:
            continue
        duplicates = sorted(
            name for name in frozenset(public_names) if public_names.count(name) > 1
        )
        missing = sorted(set(public_names).difference(_bound_names(tree)))
        module_name = _module_name(path)
        if duplicates:
            failures.append(
                f"{module_name} duplicates public names: {', '.join(duplicates)}"
            )
        if missing:
            failures.append(
                f"{module_name} exports unbound names: {', '.join(missing)}"
            )
    assert not failures, "\n".join(failures)


def test_public_dataclasses_are_slotted_and_frozen_by_default() -> None:
    declarations = _public_dataclass_declarations()
    assert declarations
    failures: list[str] = []
    observed_mutable: set[str] = set()
    for declaration in declarations:
        if not declaration.slots:
            failures.append(f"{declaration.qualified_name} is not slotted")
        if declaration.qualified_name in _MUTABLE_PUBLIC_DATACLASSES:
            observed_mutable.add(declaration.qualified_name)
            if declaration.frozen:
                failures.append(
                    f"{declaration.qualified_name} must remain an explicit mutable model"
                )
        elif not declaration.frozen:
            failures.append(f"{declaration.qualified_name} is not frozen")
    missing_exceptions = _MUTABLE_PUBLIC_DATACLASSES.difference(observed_mutable)
    if missing_exceptions:
        failures.append(
            "mutable-model exception declarations are missing: "
            + ", ".join(sorted(missing_exceptions))
        )
    assert not failures, "\n".join(failures)


def test_frozen_public_dataclasses_use_immutable_collection_annotations() -> None:
    failures: list[str] = []
    for declaration in _public_dataclass_declarations():
        if not declaration.frozen:
            continue
        for annotation in declaration.annotations:
            if _annotation_uses_mutable_collection(annotation):
                failures.append(
                    f"{declaration.qualified_name} exposes mutable annotation "
                    f"{ast.unparse(annotation)}"
                )
    assert not failures, "\n".join(failures)


def test_public_dataclasses_do_not_share_mutable_default_values() -> None:
    failures: list[str] = []
    for declaration in _public_dataclass_declarations():
        for value in declaration.defaults:
            if _is_direct_mutable_default(value):
                failures.append(
                    f"{declaration.qualified_name} has mutable default {ast.unparse(value)}"
                )
    assert not failures, "\n".join(failures)


def test_registered_contract_symbols_have_only_their_documented_owner() -> None:
    failures: list[str] = []
    for module_name, forbidden_names in _FORBIDDEN_OWNER_DEFINITIONS.items():
        defined = _defined_names(_parse(_module_path(module_name)))
        duplicates = sorted(defined.intersection(forbidden_names))
        if duplicates:
            failures.append(
                f"{module_name} redefines owned symbols: {', '.join(duplicates)}"
            )
    assert not failures, "\n".join(failures)


def test_shared_kernel_model_identity_is_preserved_by_consumers() -> None:
    config_models = import_module("gf_wordbench.config.models")
    state_models = import_module("gf_wordbench.state.models")

    assert config_models.ProducerInfo is ProducerInfo
    assert state_models.ProducerInfo is ProducerInfo
    assert config_models.ValidationMode is ValidationMode
    assert state_models.ValidationMode is ValidationMode
    assert config_models.TargetKind is TargetKind

    assert "ProducerInfo" not in config_models.__all__
    assert "ProducerInfo" not in state_models.__all__
    assert "ValidationMode" not in config_models.__all__
    assert "ValidationMode" not in state_models.__all__
    assert "TargetKind" not in config_models.__all__


def test_shared_status_dimensions_have_exact_locked_values() -> None:
    expected: Mapping[type[StrEnum], tuple[str, ...]] = {
        ValidationStatus: ("OK", "FAIL", "ERROR", "SKIPPED"),
        OverallStatus: ("OK", "FAIL", "ERROR"),
        ExecutionState: ("completed", "timed_out", "cancelled", "launch_failed"),
        DiagnosticClass: (
            "ok",
            "direct",
            "downstream",
            "ambiguous",
            "noise",
            "skipped",
        ),
        ErrorKind: (
            "OK",
            "OTHER",
            "TYPE",
            "SYNTAX",
            "INTERNAL",
            "TIMEOUT",
            "SCRIPT",
            "CONFIG",
            "IO",
            "TOOL",
        ),
        ChangeKind: ("unchanged", "improved", "regressed", "new", "removed"),
        ValidationMode: ("quick", "checkpoint", "release", "diagnostic"),
        TargetKind: (
            "file",
            "module",
            "checkpoint",
            "entrypoint",
            "scenario",
            "project",
            "regression",
        ),
    }

    for enum_type, values in expected.items():
        assert _enum_values(enum_type) == values
        assert enum_type.__module__ == "gf_wordbench.kernel.statuses"

    assert len(set(expected)) == len(expected)


def test_producer_info_is_an_immutable_slotted_owner_model() -> None:
    producer = ProducerInfo(name="gf-wordbench", version="1.0.0")

    assert is_dataclass(producer)
    assert tuple(field.name for field in fields(producer)) == ("name", "version")
    assert not hasattr(producer, "__dict__")
    assert type(producer).__module__ == "gf_wordbench.kernel.serialization"

    with pytest.raises(FrozenInstanceError):
        setattr(producer, "name", "other")


def test_run_result_mutability_is_limited_to_the_accepted_adr_models() -> None:
    module = import_module("gf_wordbench.runs.models.results")
    file_result = module.FileResult
    run_totals = module.RunTotals
    run_result = module.RunResult

    assert is_dataclass(file_result)
    assert is_dataclass(run_totals)
    assert is_dataclass(run_result)
    assert getattr(file_result, "__dataclass_params__").frozen is False
    assert getattr(run_result, "__dataclass_params__").frozen is False
    assert getattr(run_totals, "__dataclass_params__").frozen is True
    assert "__dict__" not in vars(file_result)
    assert "__dict__" not in vars(run_result)
    assert "__dict__" not in vars(run_totals)


def test_project_lifecycle_models_remain_with_their_use_case_owners() -> None:
    project_models = import_module("gf_wordbench.projects.models")
    project_model_names = frozenset(vars(project_models))

    assert "ProjectValidationResult" in project_models.__all__
    assert "ProjectValidationReport" not in project_model_names
    assert not project_model_names.intersection(
        {
            "ResetRequest",
            "ResetPlan",
            "ResetResult",
            "ProjectMigrationRequest",
            "ProjectMigrationPlan",
            "ProjectMigrationResult",
        }
    )


def test_model_owner_modules_do_not_depend_on_portfolio() -> None:
    failures: list[str] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            imported: str | None = None
            if isinstance(node, ast.ImportFrom):
                imported = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "gf_portfolio" or alias.name.startswith(
                        "gf_portfolio."
                    ):
                        failures.append(
                            f"{_module_name(path)} imports {alias.name}"
                        )
            if imported == "gf_portfolio" or (
                imported is not None and imported.startswith("gf_portfolio.")
            ):
                failures.append(f"{_module_name(path)} imports {imported}")
    assert not failures, "\n".join(failures)
