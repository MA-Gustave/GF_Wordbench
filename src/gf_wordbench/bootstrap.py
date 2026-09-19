"""GF Wordbench composition root and bootstrap boundaries.

This module owns two deliberately separate composition paths:

* desktop startup delegates path-resolved language selection to the GUI startup
  application service defined by ADR-0015;
* language, profile, and scenario checks accept explicit path-resolved language
  input and an optional or required validation profile according to their CLI
  contract;
* run bootstrap preserves the existing explicit ``project.toml`` profile path
  during the compatibility period while consuming a resolved language context
  whenever one is supplied.

The composition root wires public services only.  It does not enumerate GF
files, infer language identity, construct GF command lines, show dialogs, or
execute validation while being imported.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
import importlib
import inspect
import os
from pathlib import Path
import shutil
from types import MappingProxyType
from typing import (
    Final,
    Protocol,
    TypeAlias,
    cast,
    runtime_checkable,
)

from gf_wordbench.config.defaults import (
    DEFAULT_AGGREGATE_LOGS,
    DEFAULT_DIFF_PREVIOUS,
    DEFAULT_EMIT_CPU_STATS,
    DEFAULT_EVIDENCE_LEVEL,
    DEFAULT_GENERATE_AI_READY,
    DEFAULT_GENERATE_MANIFEST,
    DEFAULT_KEEP_OK_DETAILS,
    DEFAULT_MAX_FILES,
    DEFAULT_NO_COMPILE,
    DEFAULT_SKIP_VERSION_PROBE,
    DEFAULT_STATE_FILENAME,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VALIDATION_MODE,
    SUPPORTED_APP_STATE_SCHEMA_MAJOR,
    SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR,
    SUPPORTED_PROJECT_SCHEMA_MAJOR,
    SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
)
from gf_wordbench.config.environment import read_environment
from gf_wordbench.config.models import (
    AppConfig,
    ConfigurationIssue,
    ConfigurationProvenance,
    ConfigurationResolution,
    ConfigurationResolutionRequest,
    EnvironmentOverrides,
    EvidenceLevel,
    IssueSeverity,
    OutputDefaults,
    ResolvedEnvironment,
    RunConfig,
    SchemaSupport,
    SelectionDefaults,
    ValidationTarget,
)
from gf_wordbench.config.precedence import ConfigurationSource
from gf_wordbench.config.resolver import resolve_configuration
from gf_wordbench.kernel.errors import (
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
    ProjectConfigurationError,
)
from gf_wordbench.kernel.ids import RunId, validate_run_id
from gf_wordbench.kernel.paths import normalize_environment_path
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.projects.paths import PROJECT_CONFIG_FILENAME
from gf_wordbench.projects.policies import enforce_project_invariants
from gf_wordbench.projects.schema import parse_project_document
from gf_wordbench.projects.toml_adapter import read_project_toml
from gf_wordbench.runs.identity import (
    iter_run_id_candidates,
    run_directory_name,
)
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.paths import (
    allocate_run_paths,
    build_expected_path_map,
)
from gf_wordbench.runs.planner import RunPlan, resolve_execution_plan
from gf_wordbench.runs.preflight import PreflightResult, preflight_run
from gf_wordbench.state.models import AppState, StateLoadResult
from gf_wordbench.state.repository import StateRepository
from gf_wordbench.state.schema import default_app_state
from gf_wordbench.version import __version__

PathInput: TypeAlias = str | os.PathLike[str] | Path
ProjectDocument: TypeAlias = Mapping[str, object]
SourceValues: TypeAlias = Mapping[ConfigurationSource, Mapping[str, object]]
Clock: TypeAlias = Callable[[], datetime]
AuditWorkflow: TypeAlias = Callable[..., object]
GoldUpdateWorkflow: TypeAlias = Callable[[object], object]
_LanguageProbeWorkflow: TypeAlias = Callable[[object], object]
_ProjectCheckWorkflow: TypeAlias = Callable[[object], object]
_ProjectProbeWorkflow: TypeAlias = Callable[[object, ProjectConfig], None]
_ScenarioCheckWorkflow: TypeAlias = Callable[[object], object]


@runtime_checkable
class GoldUpdateApplication(Protocol):
    """Bootstrap-owned application boundary for reviewed gold updates.

    CLI adapters may pass their immutable command request objects through this
    structural boundary. Bootstrap deliberately does not import entrypoint
    request or application types, which would reverse the dependency direction
    and create a composition cycle.
    """

    def execute_gold_update(self, request: object) -> object:
        """Execute one injected, reviewed gold-update workflow."""


@runtime_checkable
class GuiRuntime(Protocol):
    """Bootstrap-owned desktop startup runtime returned to the GUI entrypoint.

    The entrypoint depends only on this structural contract.  The concrete
    introduction window, language probe, state repository and language runtime
    remain owned by their functional modules.
    """

    @property
    def window(self) -> object:
        """Return the top-level introduction window."""

    def start(self) -> None:
        """Connect startup actions without selecting or probing a language."""

    def shutdown(self) -> None:
        """Release runtime resources without starting new work."""


GuiRuntimeFactory: TypeAlias = Callable[[object, tuple[str, ...]], GuiRuntime]

_APPLICATION_NAME: Final[str] = "gf-wordbench"
_LEGACY_MODE_ALIASES: Final[Mapping[str, ValidationMode]] = MappingProxyType(
    {
        "file": ValidationMode.QUICK,
        "all": ValidationMode.DIAGNOSTIC,
    }
)
_INVOCATION_SOURCES: Final[frozenset[ConfigurationSource]] = frozenset(
    {
        ConfigurationSource.CLI,
        ConfigurationSource.GUI,
        ConfigurationSource.AUTOMATION,
    }
)
_MAX_SCENARIO_FILTERS: Final[int] = 4096
_MAX_BOOTSTRAP_WARNINGS: Final[int] = 256
_MAX_COLLISION_ATTEMPTS: Final[int] = 10_000
_AUDIT_PROVIDER_CANDIDATES: Final[tuple[tuple[str, str], ...]] = (
    ("gf_wordbench.runs.application", "run_validation"),
    ("gf_wordbench.audit_core", "run_validation"),
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class InvocationRequest:
    """Interface-neutral explicit input accepted by shared bootstrap code."""

    source: ConfigurationSource
    workspace_root: PathInput | None = None
    language_path: PathInput | None = None
    validation_profile: PathInput | None = None
    project_root: PathInput | None = None
    project_file: PathInput | None = None
    gf_executable: PathInput | None = None
    rgl_root: PathInput | None = None
    output_root: PathInput | None = None
    state_path: PathInput | None = None
    mode: ValidationMode | str | None = None
    target: ValidationTarget | None = None
    target_file: str | None = None
    checkpoint_id: str | None = None
    scenario_filter: tuple[str, ...] = ()
    timeout_sec: int | None = None
    max_files: int | None = None
    keep_ok_details: bool | None = None
    diff_previous: bool | None = None
    skip_version_probe: bool | None = None
    no_compile: bool | None = None
    emit_cpu_stats: bool | None = None
    evidence_level: str | None = None
    strict: bool = False
    load_state: bool = True
    run_id: RunId | str | None = None
    compatibility_warnings: tuple[str, ...] = field(
        default=(),
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.source not in _INVOCATION_SOURCES:
            allowed = ", ".join(sorted(item.value for item in _INVOCATION_SOURCES))
            raise ValueError(f"source must be one of: {allowed}")

        for name in (
            "workspace_root",
            "language_path",
            "validation_profile",
            "project_root",
            "project_file",
            "gf_executable",
            "rgl_root",
            "output_root",
            "state_path",
        ):
            value = getattr(self, name)
            if value is not None:
                _validate_path_input(value, field_name=name)

        raw_mode = self.mode
        normalized_mode = _coerce_mode(raw_mode)
        object.__setattr__(self, "mode", normalized_mode)
        if isinstance(raw_mode, str) and raw_mode.strip().lower() in _LEGACY_MODE_ALIASES:
            alias = raw_mode.strip().lower()
            canonical_mode = _require_validation_mode(normalized_mode, field_name="mode")
            object.__setattr__(
                self,
                "compatibility_warnings",
                (f"mode={alias} is deprecated; use mode={canonical_mode.value}",),
            )

        if self.target is not None and not isinstance(self.target, ValidationTarget):
            raise TypeError("target must be a ValidationTarget or None")

        target_file = _optional_trimmed_text(self.target_file, "target_file")
        checkpoint_id = _optional_trimmed_text(
            self.checkpoint_id,
            "checkpoint_id",
        )
        object.__setattr__(self, "target_file", target_file)
        object.__setattr__(self, "checkpoint_id", checkpoint_id)

        supplied_targets = sum(
            item is not None for item in (self.target, target_file, checkpoint_id)
        )
        if supplied_targets > 1:
            raise ValueError("target, target_file, and checkpoint_id are mutually exclusive")

        scenarios = _unique_text_tuple(
            self.scenario_filter,
            field_name="scenario_filter",
            maximum=_MAX_SCENARIO_FILTERS,
        )
        object.__setattr__(self, "scenario_filter", scenarios)

        for name, minimum in (("timeout_sec", 1), ("max_files", 0)):
            value = getattr(self, name)
            if value is not None:
                _require_plain_int(value, field_name=name, minimum=minimum)

        for name in (
            "keep_ok_details",
            "diff_previous",
            "skip_version_probe",
            "no_compile",
            "emit_cpu_stats",
            "strict",
            "load_state",
        ):
            value = getattr(self, name)
            if type(value) is not bool and value is not None:
                raise TypeError(f"{name} must be a bool or None")

        if self.evidence_level is not None:
            _require_text(self.evidence_level, field_name="evidence_level")

        if self.run_id is not None:
            object.__setattr__(self, "run_id", validate_run_id(self.run_id))

    @property
    def resolved_target(self) -> ValidationTarget | None:
        if self.target is not None:
            return self.target
        if self.target_file is not None:
            return ValidationTarget(TargetKind.FILE, self.target_file)
        if self.checkpoint_id is not None:
            return ValidationTarget(TargetKind.CHECKPOINT, self.checkpoint_id)
        return None


@dataclass(frozen=True, slots=True)
class BootstrapServices:
    """Replaceable adapters used by the composition root."""

    environment_reader: Callable[[], EnvironmentOverrides] = read_environment
    project_reader: Callable[[Path], ProjectDocument] = read_project_toml
    project_parser: Callable[[ProjectDocument, Path], ProjectConfig] = lambda document, source: (
        parse_project_document(
            document,
            source_file=source,
        )
    )
    project_policy: Callable[[ProjectConfig, bool], ProjectConfig] = lambda project, strict: (
        enforce_project_invariants(
            project,
            strict=strict,
        )
    )
    state_loader: Callable[[Path, Path | None], StateLoadResult] = lambda workspace, state_path: (
        StateRepository(
            workspace_root=workspace,
            state_path=state_path,
        ).load_with_diagnostics()
    )
    configuration_resolver: Callable[
        [ConfigurationResolutionRequest],
        ConfigurationResolution,
    ] = lambda request: _resolve_configuration_compat(request)
    preflight: Callable[[RunConfig], PreflightResult] = preflight_run
    planner: Callable[[RunConfig, object | None], RunPlan] = resolve_execution_plan
    run_path_allocator: Callable[[Path, RunId | str], RunPaths] = allocate_run_paths
    clock: Clock = _utc_now

    def __post_init__(self) -> None:
        for name in (
            "environment_reader",
            "project_reader",
            "project_parser",
            "project_policy",
            "state_loader",
            "configuration_resolver",
            "preflight",
            "planner",
            "run_path_allocator",
            "clock",
        ):
            if not callable(getattr(self, name)):
                raise TypeError(f"{name} must be callable")


@dataclass(frozen=True, slots=True)
class BootstrapContext:
    """Fully resolved, preflighted context returned before stage execution."""

    request: InvocationRequest
    defaults: AppConfig
    project: ProjectConfig
    state: StateLoadResult
    environment_overrides: EnvironmentOverrides
    resolution: ConfigurationResolution
    run_config: RunConfig
    preflight: PreflightResult
    plan: RunPlan
    run_paths: RunPaths
    created_run_directory: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, InvocationRequest):
            raise TypeError("request must be an InvocationRequest")
        if not isinstance(self.defaults, AppConfig):
            raise TypeError("defaults must be an AppConfig")
        if not isinstance(self.project, ProjectConfig):
            raise TypeError("project must be a ProjectConfig")
        if not isinstance(self.state, StateLoadResult):
            raise TypeError("state must be a StateLoadResult")
        if not isinstance(self.environment_overrides, EnvironmentOverrides):
            raise TypeError("environment_overrides must be EnvironmentOverrides")
        if not isinstance(self.resolution, ConfigurationResolution):
            raise TypeError("resolution must be a ConfigurationResolution")
        if not isinstance(self.run_config, RunConfig):
            raise TypeError("run_config must be a RunConfig")
        if not isinstance(self.preflight, PreflightResult):
            raise TypeError("preflight must be a PreflightResult")
        if not isinstance(self.plan, RunPlan):
            raise TypeError("plan must be a RunPlan")
        if not isinstance(self.run_paths, RunPaths):
            raise TypeError("run_paths must be RunPaths")
        if type(self.created_run_directory) is not bool:
            raise TypeError("created_run_directory must be a bool")
        object.__setattr__(
            self,
            "warnings",
            _unique_text_tuple(
                self.warnings,
                field_name="warnings",
                maximum=_MAX_BOOTSTRAP_WARNINGS,
            ),
        )

    @property
    def provenance(self) -> tuple[ConfigurationProvenance, ...]:
        return self.resolution.provenance

    @property
    def run_id(self) -> str:
        return str(self.run_paths.run_id)


@dataclass(frozen=True, slots=True)
class _PreparedBootstrap:
    request: InvocationRequest
    defaults: AppConfig
    project: ProjectConfig
    state: StateLoadResult
    environment: EnvironmentOverrides
    resolution: ConfigurationResolution
    run_config: RunConfig
    preflight: PreflightResult
    plan: RunPlan
    timestamp: datetime
    warnings: tuple[str, ...]


class _SourceValuesResolutionRequest(ConfigurationResolutionRequest):
    """Compatibility shim for snapshots using the earlier accessor name."""

    __slots__ = ()

    @property
    def candidates_by_source(self) -> SourceValues:
        return cast("SourceValues", self.source_values)


def _resolve_configuration_compat(
    request: ConfigurationResolutionRequest,
) -> ConfigurationResolution:
    """Use the owned resolver, with a narrow inter-snapshot contract fallback."""

    try:
        return resolve_configuration(request)
    except (AttributeError, TypeError) as exc:
        message = str(exc)
        known_drift = (
            "candidates_by_source" in message
            or "ConfigurationProvenance.__init__" in message
            or ("ConfigurationProvenance" in message and "required positional arguments" in message)
        )
        if not known_drift:
            raise
        return _compose_configuration_fallback(request)


def _compose_configuration_fallback(
    request: ConfigurationResolutionRequest,
) -> ConfigurationResolution:
    """Compose the documented precedence model for compatible code snapshots."""

    project = _require_project_config(request.project, field_name="request.project")
    defaults = request.defaults
    source_values = _request_source_values(request)
    issues: list[ConfigurationIssue] = []
    provenance: list[ConfigurationProvenance] = []

    def choose(
        field_name: str,
        tiers: Sequence[Sequence[ConfigurationSource]],
        *,
        default: object = None,
        required: bool = False,
    ) -> object:
        for tier in tiers:
            present = [
                (source, source_values[source][field_name])
                for source in tier
                if source in source_values and field_name in source_values[source]
            ]
            if not present:
                continue
            reference = present[0][1]
            if any(value != reference for _, value in present[1:]):
                issues.append(
                    _configuration_issue(
                        field_name,
                        ConfigurationSource.RUNTIME_DERIVED,
                        tuple(value for _, value in present),
                        "Equivalent configuration sources supplied conflicting values.",
                        "Remove the conflict or make the values identical.",
                    )
                )
                return None
            source = min((item[0] for item in present), key=lambda item: item.value)
            provenance.append(
                ConfigurationProvenance(
                    field_path=field_name,
                    source=source,
                    provided_value=reference,
                    resolved_value=reference,
                )
            )
            return reference
        if required and default is None:
            issues.append(
                _configuration_issue(
                    field_name,
                    ConfigurationSource.RUNTIME_DERIVED,
                    None,
                    "No authorized configuration source supplied a value.",
                    f"Provide {field_name} through an explicit, environment, or state source.",
                )
            )
        return default

    explicit = (
        ConfigurationSource.CLI,
        ConfigurationSource.GUI,
        ConfigurationSource.AUTOMATION,
    )
    env_tier = (ConfigurationSource.ENVIRONMENT_VARIABLE,)
    state_tier = (ConfigurationSource.APPLICATION_STATE,)
    runtime_tier = (ConfigurationSource.RUNTIME_DERIVED,)

    project_root_value = choose(
        "project_root",
        (explicit, env_tier, state_tier),
        default=project.project_root,
    )
    gf_value = choose(
        "gf_executable",
        (explicit, env_tier, state_tier),
        default=shutil.which("gf") or shutil.which("gf.exe"),
        required=True,
    )
    rgl_value = choose(
        "rgl_root",
        (explicit, env_tier, state_tier),
        required=True,
    )
    output_value = choose(
        "output_root",
        (explicit, env_tier, state_tier),
        required=True,
    )

    selection = defaults.selection_defaults
    output_defaults = defaults.output_defaults
    mode = choose(
        "mode",
        (explicit, state_tier),
        default=selection.mode,
    )
    target = choose(
        "target",
        (explicit, state_tier, runtime_tier),
        default=None,
    )
    timeout_sec = choose(
        "timeout_sec",
        (explicit, state_tier),
        default=selection.timeout_sec,
    )
    max_files = choose(
        "max_files",
        (explicit, state_tier),
        default=selection.max_files,
    )
    keep_ok_details = choose(
        "keep_ok_details",
        (explicit, state_tier),
        default=selection.keep_ok_details,
    )
    diff_previous = choose(
        "diff_previous",
        (explicit, state_tier),
        default=selection.diff_previous,
    )
    skip_version_probe = choose(
        "skip_version_probe",
        (explicit, state_tier),
        default=selection.skip_version_probe,
    )
    no_compile = choose(
        "no_compile",
        (explicit, state_tier),
        default=selection.no_compile,
    )
    emit_cpu_stats = choose(
        "emit_cpu_stats",
        (explicit, state_tier),
        default=selection.emit_cpu_stats,
    )
    evidence_level = choose(
        "evidence_level",
        (explicit, state_tier),
        default=output_defaults.evidence_level,
    )

    environment_values = {
        "project_root": project_root_value,
        "gf_executable": gf_value,
        "rgl_root": rgl_value,
        "output_root": output_value,
    }
    resolved_paths: dict[str, Path] = {}
    for field_name, value in environment_values.items():
        if value is None:
            continue
        try:
            resolved_paths[field_name] = normalize_environment_path(
                cast("PathInput", value),
                role=field_name,
            )
        except Exception as exc:
            issues.append(
                _configuration_issue(
                    field_name,
                    _winning_source(provenance, field_name),
                    value,
                    f"The path could not be normalized: {_bounded_message(exc)}",
                    "Provide an absolute, lexically valid machine-local path.",
                )
            )

    expected_project_root = project.project_root
    actual_project_root = resolved_paths.get("project_root")
    if actual_project_root is not None and actual_project_root != expected_project_root:
        issues.append(
            _configuration_issue(
                "project_root",
                _winning_source(provenance, "project_root"),
                actual_project_root,
                "The selected project root does not own the loaded project.toml.",
                f"Use the active project root {expected_project_root}.",
            )
        )

    for field_name in ("gf_executable", "rgl_root", "output_root"):
        path = resolved_paths.get(field_name)
        if path is None:
            continue
        valid = path.is_file() if field_name == "gf_executable" else path.is_dir()
        if not valid:
            expected = "regular file" if field_name == "gf_executable" else "directory"
            issues.append(
                _configuration_issue(
                    field_name,
                    _winning_source(provenance, field_name),
                    path,
                    f"The resolved path is not an existing {expected}.",
                    "Correct the machine-local path and retry.",
                )
            )

    gf_path: list[Path] = []
    rgl_root = resolved_paths.get("rgl_root")
    if rgl_root is not None:
        seen: set[str] = set()
        for index, part in enumerate(project.gf.path_parts):
            try:
                candidate = normalize_environment_path(
                    part,
                    base=rgl_root,
                    role=f"project.gf.path_parts[{index}]",
                )
            except Exception as exc:
                issues.append(
                    _configuration_issue(
                        f"project.gf.path_parts[{index}]",
                        ConfigurationSource.PROJECT_TOML,
                        part,
                        f"The GF path part is invalid: {_bounded_message(exc)}",
                        "Use an RGL-root-relative directory path.",
                    )
                )
                continue
            if not candidate.is_dir():
                issues.append(
                    _configuration_issue(
                        f"project.gf.path_parts[{index}]",
                        ConfigurationSource.PROJECT_TOML,
                        part,
                        "The resolved GF path directory does not exist.",
                        f"Create or correct {candidate}.",
                    )
                )
                continue
            key = os.path.normcase(os.path.normpath(os.fspath(candidate)))
            if key not in seen:
                seen.add(key)
                gf_path.append(candidate)

    output_root = resolved_paths.get("output_root")
    if output_root is not None:
        overlaps = _paths_overlap(output_root, project.source_root) or (
            rgl_root is not None and _paths_overlap(output_root, rgl_root)
        )
        if overlaps:
            issues.append(
                _configuration_issue(
                    "output_root",
                    _winning_source(provenance, "output_root"),
                    output_root,
                    "The output root overlaps project sources or the RGL tree.",
                    "Select a separate writable output directory.",
                )
            )

    if issues:
        return ConfigurationResolution(
            configuration=None,
            issues=tuple(issues),
            provenance=tuple(sorted(provenance, key=lambda item: item.field_path)),
        )

    try:
        environment = ResolvedEnvironment(
            project_root=expected_project_root,
            rgl_root=resolved_paths["rgl_root"],
            gf_executable=resolved_paths["gf_executable"],
            output_root=resolved_paths["output_root"],
            gf_path=tuple(gf_path),
        )
        configuration = RunConfig(
            project=project,
            environment=environment,
            mode=cast("ValidationMode", mode),
            target=cast("ValidationTarget | None", target),
            timeout_sec=cast("int", timeout_sec),
            max_files=cast("int", max_files),
            keep_ok_details=cast("bool", keep_ok_details),
            diff_previous=cast("bool", diff_previous),
            skip_version_probe=cast("bool", skip_version_probe),
            no_compile=cast("bool", no_compile),
            emit_cpu_stats=cast("bool", emit_cpu_stats),
            selected_checkpoints=tuple(
                project.source_root.joinpath(*path.parts) for path in project.modules.checkpoints
            ),
            selected_entrypoints=tuple(
                project.source_root.joinpath(*path.parts) for path in project.modules.entrypoints
            ),
            selected_scenarios=tuple(str(item) for item in project.validation.all_scenarios),
            release_requires_pgf=project.validation.release_requires_pgf,
            evidence_level=_coerce_evidence_level(
                evidence_level,
                field_name="evidence_level",
            ),
            compatibility_warnings=(),
        )
    except (TypeError, ValueError, KeyError) as exc:
        issue = _configuration_issue(
            "configuration",
            ConfigurationSource.RUNTIME_DERIVED,
            None,
            f"Resolved values cannot form RunConfig: {_bounded_message(exc)}",
            "Correct the reported configuration values.",
        )
        return ConfigurationResolution(
            configuration=None,
            issues=(issue,),
            provenance=tuple(sorted(provenance, key=lambda item: item.field_path)),
        )

    for field_name in (
        "selected_checkpoints",
        "selected_entrypoints",
        "selected_scenarios",
        "release_requires_pgf",
    ):
        provenance.append(
            ConfigurationProvenance(
                field_path=field_name,
                source=ConfigurationSource.PROJECT_TOML,
                provided_value=getattr(project, "validation", project),
                resolved_value=getattr(configuration, field_name),
            )
        )

    return ConfigurationResolution(
        configuration=configuration,
        issues=(),
        provenance=tuple(sorted(provenance, key=lambda item: item.field_path)),
    )


def _request_source_values(
    request: ConfigurationResolutionRequest,
) -> SourceValues:
    if hasattr(request, "source_values"):
        return cast("SourceValues", request.source_values)
    return cast("SourceValues", request.candidates_by_source)


def _configuration_issue(
    field_path: str,
    source: ConfigurationSource,
    provided_value: object,
    message: str,
    remediation: str,
) -> ConfigurationIssue:
    return ConfigurationIssue(
        severity=IssueSeverity.ERROR,
        source=source,
        field_path=field_path,
        provided_value=provided_value,
        message=message,
        remediation=remediation,
    )


def _winning_source(
    provenance: Sequence[ConfigurationProvenance],
    field_path: str,
) -> ConfigurationSource:
    for item in reversed(provenance):
        if item.field_path == field_path:
            source = item.source
            if not isinstance(source, ConfigurationSource):
                raise ContractViolationError(
                    "Configuration provenance contains an invalid source.",
                    code="GF-WB-CONTRACT-008",
                    stage="bootstrap",
                    operation="resolve-configuration-provenance",
                    subject=field_path,
                )
            return source
    return ConfigurationSource.RUNTIME_DERIVED


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class _ComposedAuditApplication:
    """Application adapter composed for canonical validation execution."""

    workflow: AuditWorkflow

    def __post_init__(self) -> None:
        if not callable(self.workflow):
            raise TypeError("workflow must be callable")

    def run_validation(
        self,
        request: object,
        *,
        cancellation_check: Callable[[], None] | None = None,
        event_sink: Callable[[object], None] | None = None,
    ) -> object:
        if cancellation_check is not None and not callable(cancellation_check):
            raise TypeError("cancellation_check must be callable or None")
        if event_sink is not None and not callable(event_sink):
            raise TypeError("event_sink must be callable or None")

        return self.workflow(
            request,
            cancellation_check=cancellation_check,
            event_sink=event_sink,
        )


def build_audit_application(
    *,
    workflow: AuditWorkflow | None = None,
) -> object:
    """Compose the shared CLI and GUI validation application boundary.

    ``workflow`` is the explicit test and embedding seam.  The default path
    resolves the canonical run-application service lazily, so importing this
    composition root never imports execution stages or starts validation.
    """

    active_workflow = workflow or _default_audit_workflow
    if not callable(active_workflow):
        raise TypeError("workflow must be callable or None")
    return _ComposedAuditApplication(active_workflow)


def _default_audit_workflow(
    request: object,
    *,
    cancellation_check: Callable[[], None] | None = None,
    event_sink: Callable[[object], None] | None = None,
) -> object:
    """Delegate one validation request to the canonical application service."""

    workflow = _load_audit_workflow()
    return workflow(
        request,
        cancellation_check=cancellation_check,
        event_sink=event_sink,
    )


def _load_audit_workflow() -> AuditWorkflow:
    """Load the reviewed validation application without eager imports."""

    unavailable: list[str] = []

    for module_name, symbol_name in _AUDIT_PROVIDER_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name or (
                exc.name is not None and module_name.startswith(f"{exc.name}.")
            ):
                unavailable.append(module_name)
                continue
            raise ConfigurationError(
                "The audit application service could not be imported.",
                code="GF-WB-CONFIG-912",
                detail=(f"{module_name}: {type(exc).__name__}: {_bounded_message(exc)}"),
                stage="bootstrap",
                operation="load-audit-application",
                subject=module_name,
            ) from exc
        except ImportError as exc:
            raise ConfigurationError(
                "The audit application service could not be imported.",
                code="GF-WB-CONFIG-912",
                detail=(f"{module_name}: {type(exc).__name__}: {_bounded_message(exc)}"),
                stage="bootstrap",
                operation="load-audit-application",
                subject=module_name,
            ) from exc

        workflow = getattr(module, symbol_name, None)
        if not callable(workflow):
            raise ContractViolationError(
                f"Audit application provider must expose callable {symbol_name}().",
                code="GF-WB-CONTRACT-006",
                stage="bootstrap",
                operation="load-audit-application",
                subject=f"{module_name}.{symbol_name}",
            )
        return cast("AuditWorkflow", workflow)

    expected = ", ".join(
        f"{module_name}.{symbol_name}" for module_name, symbol_name in _AUDIT_PROVIDER_CANDIDATES
    )
    detail = f"No canonical audit application provider is installed. Expected one of: {expected}."
    if unavailable:
        detail += " Missing modules: " + ", ".join(unavailable) + "."

    raise ConfigurationError(
        "The audit application service is not configured.",
        code="GF-WB-CONFIG-913",
        detail=detail,
        stage="bootstrap",
        operation="load-audit-application",
        subject="validate",
    )


@dataclass(frozen=True, slots=True)
class _ComposedLanguageProbeApplication:
    """Application adapter composed for path-resolved language probing."""

    workflow: _LanguageProbeWorkflow

    def __post_init__(self) -> None:
        if not callable(self.workflow):
            raise TypeError("workflow must be callable")

    def probe_language(self, request: object) -> object:
        return self.workflow(request)


@dataclass(frozen=True, slots=True)
class _ComposedProjectCheckApplication:
    """Application adapter composed for the read-only project checker."""

    workflow: _ProjectCheckWorkflow

    def __post_init__(self) -> None:
        if not callable(self.workflow):
            raise TypeError("workflow must be callable")

    def check_project(self, request: object) -> object:
        return self.workflow(request)


@dataclass(frozen=True, slots=True)
class _ComposedScenarioCheckApplication:
    """Application adapter composed for the read-only scenario checker."""

    workflow: _ScenarioCheckWorkflow

    def __post_init__(self) -> None:
        if not callable(self.workflow):
            raise TypeError("workflow must be callable")

    def check_scenarios(self, request: object) -> object:
        return self.workflow(request)

    def check_scenario_contracts(self, request: object) -> object:
        """Expose the alternate protocol spelling used by older adapters."""

        return self.workflow(request)


def build_gui_startup_runtime(
    application: object,
    argv: tuple[str, ...] = (),
    *,
    runtime_factory: GuiRuntimeFactory | None = None,
) -> GuiRuntime:
    """Compose the desktop pre-launch runtime used by ``entrypoints.gui.main``.

    The default factory is imported lazily so importing :mod:`bootstrap` never
    imports Qt.  ``entrypoints.gui.startup`` owns the introduction window and
    explicit path-resolved language-selection workflow; this composition root
    only validates and returns its startup runtime.

    ``runtime_factory`` is an explicit test and embedding seam.  It receives
    the application and immutable argument tuple and must return an object with
    ``window``, ``start()`` and ``shutdown()``.  This function never selects,
    probes or opens a language automatically.
    """

    if application is None:
        raise TypeError("application must not be None")
    if not isinstance(argv, tuple):
        raise TypeError("argv must be a tuple of strings")
    for index, value in enumerate(argv):
        if not isinstance(value, str):
            raise TypeError(f"argv[{index}] must be a string")
        if "\x00" in value:
            raise ValueError(f"argv[{index}] must be NUL-free")
    if runtime_factory is not None and not callable(runtime_factory):
        raise TypeError("runtime_factory must be callable or None")

    factory = runtime_factory or _default_gui_startup_runtime_factory
    try:
        runtime = factory(application, argv)
    except (ConfigurationError, ContractViolationError):
        raise
    except Exception as exc:
        raise ConfigurationError(
            "GF Wordbench GUI startup runtime could not be composed.",
            code="GF-WB-CONFIG-910",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="build-gui-startup-runtime",
        ) from exc

    return _require_gui_startup_runtime(runtime)


def _default_gui_startup_runtime_factory(
    application: object,
    argv: tuple[str, ...],
) -> GuiRuntime:
    """Load the path-resolved GUI startup factory without eager Qt imports."""

    try:
        from gf_wordbench.entrypoints.gui.startup import build_startup_runtime
    except ImportError as exc:
        raise ConfigurationError(
            "The path-resolved GUI startup module is not installed.",
            code="GF-WB-CONFIG-911",
            detail=(
                "Expected gf_wordbench.entrypoints.gui.startup.build_startup_runtime. "
                f"Import failed: {_bounded_message(exc)}. "
                "Install or implement the ADR-0015 startup module before "
                "launching the desktop application."
            ),
            stage="bootstrap",
            operation="load-gui-startup-factory",
            subject="gf_wordbench.entrypoints.gui.startup",
        ) from exc

    if not callable(build_startup_runtime):
        raise ContractViolationError(
            "GUI startup factory must be callable.",
            code="GF-WB-CONTRACT-002",
            stage="bootstrap",
            operation="load-gui-startup-factory",
            subject="build_startup_runtime",
        )

    _require_canonical_gui_startup_factory(build_startup_runtime)
    return cast(
        "GuiRuntime",
        build_startup_runtime(application, argv),
    )


def _require_canonical_gui_startup_factory(factory: Callable[..., object]) -> None:
    """Require the canonical startup signature without extra required inputs.

    ``entrypoints.gui.startup`` owns composition of its concrete services.  The
    bootstrap boundary supplies only the Qt application and immutable argument
    tuple.  Requiring another input here would split startup ownership across
    modules and make the desktop entrypoint dependent on implementation details.
    """

    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        # Some extension or generated callables do not expose an inspectable
        # signature.  Their runtime contract is still checked by the call below
        # and by ``_require_gui_startup_runtime``.
        return

    try:
        signature.bind(object(), ())
    except TypeError as exc:
        raise ContractViolationError(
            "GUI startup factory has a non-canonical signature.",
            code="GF-WB-CONTRACT-008",
            detail=(
                "build_startup_runtime must accept application and argv without "
                "additional required arguments. Concrete startup services must "
                "be composed inside entrypoints.gui.startup. "
                f"Detected signature: {signature}."
            ),
            stage="bootstrap",
            operation="load-gui-startup-factory",
            subject="build_startup_runtime",
        ) from exc


def _require_gui_startup_runtime(runtime: object) -> GuiRuntime:
    """Validate the startup runtime contract at the composition edge."""

    if not isinstance(runtime, GuiRuntime):
        raise ContractViolationError(
            "GUI startup factory returned an invalid runtime.",
            code="GF-WB-CONTRACT-003",
            detail=(
                "The runtime must expose a window property and callable "
                "start() and shutdown() methods."
            ),
            stage="bootstrap",
            operation="validate-gui-startup-runtime",
        )

    window = runtime.window
    show = getattr(window, "show", None)
    if not callable(show):
        raise ContractViolationError(
            "GUI runtime window must expose show().",
            code="GF-WB-CONTRACT-004",
            stage="bootstrap",
            operation="validate-gui-startup-runtime",
            subject=type(window).__name__,
        )
    if not callable(runtime.start):
        raise ContractViolationError(
            "GUI startup runtime must expose start().",
            code="GF-WB-CONTRACT-007",
            stage="bootstrap",
            operation="validate-gui-startup-runtime",
            subject=type(runtime).__name__,
        )
    if not callable(runtime.shutdown):
        raise ContractViolationError(
            "GUI startup runtime must expose shutdown().",
            code="GF-WB-CONTRACT-005",
            stage="bootstrap",
            operation="validate-gui-startup-runtime",
            subject=type(runtime).__name__,
        )
    return runtime


def build_language_probe_application(
    *,
    workflow: _LanguageProbeWorkflow | None = None,
) -> object:
    """Compose the public application boundary for ``language probe``.

    The default workflow delegates bounded source discovery to the existing
    path-resolved language probe.  It may validate one explicitly supplied
    ``project.toml`` profile against the resolved language directory, but it
    does not execute GF, allocate a run, persist state, or write reports.
    """

    active_workflow = workflow or _run_language_probe
    if not callable(active_workflow):
        raise TypeError("workflow must be callable or None")
    return _ComposedLanguageProbeApplication(active_workflow)


def build_project_check_application(
    *,
    services: BootstrapServices | None = None,
    workflow: _ProjectCheckWorkflow | None = None,
    probe_workflow: _ProjectProbeWorkflow | None = None,
) -> object:
    """Compose the public application boundary for ``project check``.

    Bootstrap loads one explicit ``project.toml`` validation profile and, when
    ``language_path`` is supplied, verifies that the profile source root matches
    the resolved language directory. The optional GF probe remains separately
    injected behind the approved process boundary.
    """

    active_services = services or BootstrapServices()
    if not isinstance(active_services, BootstrapServices):
        raise TypeError("services must be BootstrapServices or None")
    if workflow is not None:
        if not callable(workflow):
            raise TypeError("workflow must be callable or None")
        if probe_workflow is not None:
            raise ValueError("probe_workflow cannot be combined with a custom workflow")
        return _ComposedProjectCheckApplication(workflow)
    if probe_workflow is not None and not callable(probe_workflow):
        raise TypeError("probe_workflow must be callable or None")

    def execute(request: object) -> object:
        return _run_project_check(
            request,
            services=active_services,
            probe_workflow=probe_workflow,
        )

    return _ComposedProjectCheckApplication(execute)


def build_scenario_check_application(
    *,
    services: BootstrapServices | None = None,
    workflow: _ScenarioCheckWorkflow | None = None,
) -> object:
    """Compose the public application boundary for ``scenarios check``.

    The default workflow requires one explicit language path and one explicit
    ``project.toml`` validation profile, verifies their compatibility, selects
    registered scenario IDs, and delegates static ``.gfs`` validation to the
    scenario parser. It never launches GF, updates gold, or allocates a run.
    """

    active_services = services or BootstrapServices()
    if not isinstance(active_services, BootstrapServices):
        raise TypeError("services must be BootstrapServices or None")
    if workflow is not None:
        if not callable(workflow):
            raise TypeError("workflow must be callable or None")
        return _ComposedScenarioCheckApplication(workflow)

    def execute(request: object) -> object:
        return _run_scenario_check(
            request,
            services=active_services,
        )

    return _ComposedScenarioCheckApplication(execute)


def _run_language_probe(request: object) -> object:
    from gf_wordbench.projects.languages.public import probe_language_path

    selected_path = _check_required_path_value(
        request,
        names=("language_path", "selected_path", "path"),
        role="language_path",
        message="language probe requires an explicit language path",
    )
    explicit_rgl_root = _check_optional_path_value(
        request,
        names=("rgl_root", "explicit_rgl_root"),
        role="rgl_root",
    )
    strict = _check_request_bool(request, "strict", default=False)
    max_ancestor_depth = _check_request_int(
        request,
        "max_ancestor_depth",
        default=16,
        minimum=1,
        maximum=256,
    )

    result = probe_language_path(
        selected_path,
        explicit_rgl_root=explicit_rgl_root,
        max_ancestor_depth=max_ancestor_depth,
        require_unambiguous_suffix=strict,
    )

    context = _require_resolved_probe_context(
        result,
        selected_path=selected_path,
    )
    profile_file = _check_validation_profile_file(request, required=False)
    if profile_file is not None:
        project = load_active_project(
            profile_file,
            strict=strict,
        )
        _require_profile_language_compatibility(project, context)

    return result


def _run_project_check(
    request: object,
    *,
    services: BootstrapServices,
    probe_workflow: _ProjectProbeWorkflow | None,
) -> object:
    from gf_wordbench.projects.filesystem_adapter import (
        ProjectFilesystemAdapter,
    )
    from gf_wordbench.projects.models import (
        ProjectCheckScope,
        ProjectValidationResult,
    )
    from gf_wordbench.projects.public import check_project

    strict = _check_request_bool(request, "strict", default=False)
    language_context = _check_resolved_language_context(
        request,
        required=False,
        strict=strict,
    )
    project_file = _check_validation_profile_file(request, required=True)
    assert project_file is not None
    project = load_active_project(
        project_file,
        strict=strict,
        services=services,
    )
    if language_context is not None:
        _require_profile_language_compatibility(project, language_context)

    result = check_project(
        project,
        ProjectFilesystemAdapter(),
        scope=ProjectCheckScope.NORMAL,
        strict=strict,
    )
    if not isinstance(result, ProjectValidationResult):
        raise TypeError("check_project must return ProjectValidationResult")

    if _check_request_bool(request, "probe_gf", default=False):
        if probe_workflow is None:
            raise ConfigurationError(
                "GF probing is not configured for project check.",
                code="GF-WB-CONFIG-902",
                detail=(
                    "Provide a reviewed probe_workflow that resolves GF, "
                    "runs the version probe through the process boundary, "
                    "checks compatibility, and validates the RGL root."
                ),
                stage="bootstrap",
                operation="project-check-probe",
                subject=str(project.project_file),
            )
        probe_workflow(request, project)

    return result


def _run_scenario_check(
    request: object,
    *,
    services: BootstrapServices,
) -> object:
    from gf_wordbench.kernel.ids import validate_scenario_id
    from gf_wordbench.projects.models import (
        ProjectDiagnostic,
        ProjectDiagnosticSeverity,
        ProjectValidationResult,
    )
    from gf_wordbench.projects.paths import (
        resolve_project_paths,
        resolve_scenario_path,
    )
    from gf_wordbench.validation.scenarios.parser import (
        validate_scenario_file,
    )

    strict = _check_request_bool(request, "strict", default=False)
    language_context = _check_resolved_language_context(
        request,
        required=True,
        strict=strict,
    )
    assert language_context is not None
    profile_file = _check_validation_profile_file(request, required=True)
    assert profile_file is not None
    project = load_active_project(
        profile_file,
        strict=strict,
        services=services,
    )
    _require_profile_language_compatibility(project, language_context)

    project_paths = resolve_project_paths(project)
    registered = tuple(project.validation.all_scenarios)
    registered_set = set(registered)
    selected_ids = _check_scenario_ids(request, registered)
    diagnostics: list[ProjectDiagnostic] = []

    for scenario_id in selected_ids:
        validated_id = validate_scenario_id(scenario_id)
        if validated_id not in registered_set:
            raise ConfigurationError(
                "Scenario selection contains an unregistered ID.",
                code="GF-WB-CONFIG-903",
                detail=f"scenario_id={validated_id}",
                stage="bootstrap",
                operation="scenarios-check",
                subject=str(validated_id),
            )

        scenario_path = resolve_scenario_path(project_paths, validated_id)
        try:
            validate_scenario_file(
                scenario_path,
                scenario_id=validated_id,
            )
        except (GFWordbenchError, OSError, ValueError) as exc:
            line = _positive_optional_int(getattr(exc, "line", None))
            message = _bounded_message(exc)
            if line is not None:
                message = f"{message} (line {line})"
            diagnostics.append(
                ProjectDiagnostic(
                    code=str(getattr(exc, "code", None) or "GF-WB-SCENARIO-001"),
                    severity=ProjectDiagnosticSeverity.ERROR,
                    field=f"scenarios.{validated_id}",
                    message=message,
                    source_file=scenario_path,
                    suggestion=("Correct the scenario contract before retrying the check."),
                    subject=scenario_path,
                )
            )

    return ProjectValidationResult(tuple(diagnostics))


def _check_validation_profile_file(
    request: object,
    *,
    required: bool,
) -> Path | None:
    raw_profile = _first_check_request_value(
        request,
        ("validation_profile", "profile", "project_file"),
        None,
    )
    if raw_profile is not None:
        return _require_regular_file(
            _project_file_path(cast("PathInput", raw_profile)),
            role="validation profile",
        )

    raw_root = _first_check_request_value(
        request,
        ("legacy_project_root", "project_root"),
        None,
    )
    if raw_root is not None:
        return _legacy_profile_from_root(cast("PathInput", raw_root))

    if not required:
        return None
    raise ConfigurationError(
        "An explicit validation profile is required.",
        code="GF-WB-CONFIG-904",
        detail=(
            "Supply --profile <project.toml>. The legacy --project-root "
            "mapping is accepted only during the migration period."
        ),
        stage="bootstrap",
        operation="select-validation-profile",
        subject="validation_profile",
    )


def _legacy_profile_from_root(value: PathInput) -> Path:
    root = _absolute_path(value, role="legacy_project_root")
    _require_directory(root, role="legacy project root")

    direct = root / PROJECT_CONFIG_FILENAME
    nested = root / "project" / PROJECT_CONFIG_FILENAME
    if direct.is_file():
        return direct
    if nested.is_file():
        return nested

    expected = direct if root.name.casefold() == "project" else nested
    return _require_regular_file(
        expected,
        role="validation profile",
    )


def _check_project_file(request: object) -> Path:
    """Compatibility wrapper for callers still using the former helper."""

    profile = _check_validation_profile_file(request, required=True)
    assert profile is not None
    return profile


def _check_resolved_language_context(
    request: object,
    *,
    required: bool,
    strict: bool,
) -> object | None:
    raw_selected = _first_check_request_value(
        request,
        ("language_path", "selected_path"),
        None,
    )
    if raw_selected is None:
        if not required:
            return None
        raise ConfigurationError(
            "An explicit language path is required.",
            code="GF-WB-CONFIG-905",
            detail="Supply --language-path <directory-or-gf-file>.",
            stage="bootstrap",
            operation="resolve-language-context",
            subject="language_path",
        )

    selected_path = _absolute_path(
        cast("PathInput", raw_selected),
        role="language_path",
    )
    explicit_rgl_root = _check_optional_path_value(
        request,
        names=("rgl_root", "explicit_rgl_root"),
        role="rgl_root",
    )
    max_ancestor_depth = _check_request_int(
        request,
        "max_ancestor_depth",
        default=16,
        minimum=1,
        maximum=256,
    )

    from gf_wordbench.projects.languages.public import probe_language_path

    result = probe_language_path(
        selected_path,
        explicit_rgl_root=explicit_rgl_root,
        max_ancestor_depth=max_ancestor_depth,
        require_unambiguous_suffix=strict,
    )
    return _require_resolved_probe_context(
        result,
        selected_path=selected_path,
    )


def _require_resolved_probe_context(
    result: object,
    *,
    selected_path: Path,
) -> object:
    context = getattr(result, "context", None)
    resolved = bool(getattr(result, "resolved", False))
    status = getattr(result, "status", None)
    status_value = getattr(status, "value", status)
    if context is not None and (resolved or status_value == "resolved"):
        return context

    diagnostics = getattr(result, "diagnostics", ())
    first = diagnostics[0] if isinstance(diagnostics, Sequence) and diagnostics else None
    detail = _bounded_message(first) if first is not None else f"status={status_value}"
    raise ConfigurationError(
        "The selected language path could not be resolved.",
        code="GF-WB-CONFIG-906",
        detail=detail,
        stage="bootstrap",
        operation="resolve-language-context",
        subject=str(selected_path),
    )


def _require_profile_language_compatibility(
    project: ProjectConfig,
    language_context: object,
) -> None:
    language_directory = getattr(language_context, "language_directory", None)
    if not isinstance(language_directory, Path):
        raise ContractViolationError(
            "Resolved language context does not expose language_directory.",
            code="GF-WB-CONTRACT-006",
            stage="bootstrap",
            operation="validate-profile-language-compatibility",
        )

    profile_source = project.source_root.resolve(strict=False)
    resolved_language = language_directory.resolve(strict=False)
    if profile_source != resolved_language:
        raise ProjectConfigurationError(
            "Validation profile does not belong to the selected language.",
            code="GF-WB-PROJECT-006",
            detail=(
                f"profile source_root={profile_source}; "
                f"resolved language_directory={resolved_language}"
            ),
            stage="bootstrap",
            operation="validate-profile-language-compatibility",
            subject=str(project.project_file),
        )


def _check_scenario_ids(
    request: object,
    registered: tuple[str, ...],
) -> tuple[str, ...]:
    raw = _check_request_value(request, "scenario_ids", None)
    if raw is None:
        raw = _check_request_value(request, "scenarios", None)
    if raw is None:
        return registered
    if isinstance(raw, (str, bytes, bytearray)):
        raise TypeError("scenario_ids must be a sequence of strings")

    if not isinstance(raw, Iterable):
        raise TypeError("scenario_ids must be a sequence of strings")
    values: tuple[object, ...] = tuple(raw)

    if not values:
        return registered
    return _unique_text_tuple(
        values,
        field_name="scenario_ids",
        maximum=_MAX_SCENARIO_FILTERS,
    )


def _check_request_bool(
    request: object,
    name: str,
    *,
    default: bool,
) -> bool:
    value = _check_request_value(request, name, default)
    if type(value) is not bool:
        raise TypeError(f"{name} must be a bool")
    return value


def _check_request_value(
    request: object,
    name: str,
    default: object,
) -> object:
    if request is None:
        raise TypeError("request must not be None")

    if hasattr(request, name):
        return getattr(request, name)

    getter = getattr(request, "get", None)
    if callable(getter):
        return getter(name, default)

    arguments = getattr(request, "arguments", None)
    if isinstance(arguments, Mapping):
        return arguments.get(name, default)

    return default


def _first_check_request_value(
    request: object,
    names: Sequence[str],
    default: object,
) -> object:
    for name in names:
        value = _check_request_value(request, name, None)
        if value is not None:
            return value
    return default


def _check_required_path_value(
    request: object,
    *,
    names: Sequence[str],
    role: str,
    message: str,
) -> Path:
    value = _first_check_request_value(request, names, None)
    if value is None:
        raise ConfigurationError(
            message,
            code="GF-WB-CONFIG-907",
            stage="bootstrap",
            operation="resolve-request-path",
            subject=role,
        )
    return _absolute_path(cast("PathInput", value), role=role)


def _check_optional_path_value(
    request: object,
    *,
    names: Sequence[str],
    role: str,
) -> Path | None:
    value = _first_check_request_value(request, names, None)
    if value is None:
        return None
    return _absolute_path(cast("PathInput", value), role=role)


def _check_request_int(
    request: object,
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    value = _check_request_value(request, name, default)
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    checked = value
    if checked < minimum or checked > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return checked


def _positive_optional_int(value: object) -> int | None:
    if type(value) is int and value > 0:
        return value
    return None


@dataclass(frozen=True, slots=True)
class _ComposedGoldUpdateApplication:
    """Small adapter that keeps the CLI boundary outside bootstrap internals."""

    workflow: GoldUpdateWorkflow

    def __post_init__(self) -> None:
        if not callable(self.workflow):
            raise TypeError("workflow must be callable")

    def execute_gold_update(
        self,
        request: object,
    ) -> object:
        return self.workflow(request)


def build_gold_update_application(
    *,
    workflow: GoldUpdateWorkflow | None = None,
) -> GoldUpdateApplication:
    """Compose the CLI gold-update application boundary.

    The current repository snapshot exposes the low-level, atomic gold-update
    primitives but does not yet expose the higher-level application use case
    that executes scenarios and gathers review evidence. Callers and tests may
    inject that application workflow explicitly. Without one, execution fails
    closed with a structured configuration error rather than bypassing review.
    """

    active_workflow = workflow or _unconfigured_gold_update_workflow
    if not callable(active_workflow):
        raise TypeError("workflow must be callable or None")

    return _ComposedGoldUpdateApplication(active_workflow)


def _unconfigured_gold_update_workflow(
    request: object,
) -> object:
    """Reject gold mutation until the reviewed application use case is wired."""

    if request is None:
        raise TypeError("request must not be None")

    raise ConfigurationError(
        "Gold update application workflow is not configured.",
        code="GF-WB-CONFIG-901",
        detail=(
            "The current source snapshot provides atomic gold-update "
            "primitives, but no application use case that validates selected "
            "registrations, executes scenarios, preserves raw and normalized "
            "evidence, presents the diff, records maintainer review metadata, "
            "and invokes the atomic writer. Inject that workflow through "
            "build_gold_update_application(workflow=...)."
        ),
        stage="bootstrap",
        operation="execute-gold-update",
        subject="gold.update",
    )


def build_framework_defaults() -> AppConfig:
    """Build the language-neutral framework default configuration."""

    return AppConfig(
        producer=ProducerInfo(
            name=_APPLICATION_NAME,
            version=__version__,
        ),
        selection_defaults=SelectionDefaults(
            mode=DEFAULT_VALIDATION_MODE,
            timeout_sec=DEFAULT_TIMEOUT_SECONDS,
            max_files=DEFAULT_MAX_FILES,
            keep_ok_details=DEFAULT_KEEP_OK_DETAILS,
            diff_previous=DEFAULT_DIFF_PREVIOUS,
            skip_version_probe=DEFAULT_SKIP_VERSION_PROBE,
            no_compile=DEFAULT_NO_COMPILE,
            emit_cpu_stats=DEFAULT_EMIT_CPU_STATS,
        ),
        output_defaults=OutputDefaults(
            evidence_level=_coerce_evidence_level(
                DEFAULT_EVIDENCE_LEVEL,
                field_name="DEFAULT_EVIDENCE_LEVEL",
            ),
            generate_manifest=DEFAULT_GENERATE_MANIFEST,
            generate_ai_ready=DEFAULT_GENERATE_AI_READY,
            aggregate_logs=DEFAULT_AGGREGATE_LOGS,
        ),
        schema_support=SchemaSupport(
            project_major=SUPPORTED_PROJECT_SCHEMA_MAJOR,
            app_state_major=SUPPORTED_APP_STATE_SCHEMA_MAJOR,
            run_summary_major=SUPPORTED_RUN_SUMMARY_SCHEMA_MAJOR,
            artifact_manifest_major=(SUPPORTED_ARTIFACT_MANIFEST_SCHEMA_MAJOR),
        ),
        state_filename=DEFAULT_STATE_FILENAME,
    )


def preview_run(
    request: InvocationRequest,
    *,
    services: BootstrapServices | None = None,
) -> BootstrapContext:
    """Resolve and validate a run without creating its run directory."""

    prepared = _prepare(request, services or BootstrapServices())
    paths = _preview_paths(
        prepared.run_config.environment.output_root,
        prepared.timestamp,
        prepared.request.run_id,
    )
    return _context(prepared, paths, created=False)


def bootstrap_run(
    request: InvocationRequest,
    *,
    services: BootstrapServices | None = None,
) -> BootstrapContext:
    """Resolve a run and atomically allocate its canonical run directory."""

    active_services = services or BootstrapServices()
    prepared = _prepare(request, active_services)
    paths = _allocate_paths(
        prepared.run_config.environment.output_root,
        prepared.timestamp,
        prepared.request.run_id,
        active_services.run_path_allocator,
    )
    return _context(prepared, paths, created=True)


def resolve_run_configuration(
    request: InvocationRequest,
    *,
    services: BootstrapServices | None = None,
) -> RunConfig:
    """Return the authoritative immutable RunConfig without allocating paths."""

    return _prepare(request, services or BootstrapServices()).run_config


def load_active_project(
    project_file: PathInput,
    *,
    strict: bool = False,
    services: BootstrapServices | None = None,
) -> ProjectConfig:
    """Load and validate one explicit absolute project.toml."""

    if type(strict) is not bool:
        raise TypeError("strict must be a bool")
    active_services = services or BootstrapServices()
    source = _project_file_path(project_file)
    _require_regular_file(source, role="active project configuration")

    try:
        document = active_services.project_reader(source)
        project = active_services.project_parser(document, source)
        return active_services.project_policy(project, strict)
    except ProjectConfigurationError:
        raise
    except Exception as exc:
        raise ProjectConfigurationError(
            "Active project configuration could not be loaded.",
            code="GF-WB-PROJECT-001",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="load-project",
            subject=str(source),
        ) from exc


def _prepare(
    request: InvocationRequest,
    services: BootstrapServices,
) -> _PreparedBootstrap:
    if not isinstance(request, InvocationRequest):
        raise TypeError("request must be an InvocationRequest")
    if not isinstance(services, BootstrapServices):
        raise TypeError("services must be BootstrapServices")

    timestamp = _require_utc_timestamp(services.clock())
    defaults = build_framework_defaults()
    environment = services.environment_reader()
    if not isinstance(environment, EnvironmentOverrides):
        raise TypeError("environment_reader must return EnvironmentOverrides")

    workspace_hint = _workspace_hint(request, environment)
    state = _load_state(
        request,
        environment,
        workspace_hint,
        defaults,
        services,
    )
    project_file = _select_project_file(request, environment, state.state)
    project = load_active_project(
        project_file,
        strict=request.strict,
        services=services,
    )

    if workspace_hint is None and request.load_state:
        state = _load_state(
            request,
            environment,
            project.project_root,
            defaults,
            services,
        )

    source_values = _configuration_source_values(
        request,
        project,
        state.state,
    )
    resolution_request = _make_resolution_request(
        defaults=defaults,
        project=project,
        environment=environment,
        source_values=source_values,
    )

    try:
        resolution = services.configuration_resolver(resolution_request)
    except (ConfigurationError, ContractViolationError):
        raise
    except Exception as exc:
        raise ConfigurationError(
            "Runtime configuration resolution failed.",
            code="GF-WB-CONFIG-001",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="resolve-configuration",
        ) from exc

    if not isinstance(resolution, ConfigurationResolution):
        raise TypeError("configuration_resolver must return ConfigurationResolution")
    run_config = resolution.require()
    run_config = _apply_effective_selection(run_config, request)

    try:
        preflight = services.preflight(run_config)
        if not isinstance(preflight, PreflightResult):
            raise TypeError("preflight must return PreflightResult")
        preflight.require()
        plan = services.planner(run_config, preflight)
    except (ConfigurationError, ContractViolationError):
        raise
    except Exception as exc:
        raise ConfigurationError(
            "Run planning failed.",
            code="GF-WB-CONFIG-002",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="plan-run",
            subject=project.project_id,
        ) from exc

    if not isinstance(plan, RunPlan):
        raise TypeError("planner must return RunPlan")

    warnings = _collect_warnings(state, resolution, preflight, request)
    return _PreparedBootstrap(
        request=request,
        defaults=defaults,
        project=project,
        state=state,
        environment=environment,
        resolution=resolution,
        run_config=run_config,
        preflight=preflight,
        plan=plan,
        timestamp=timestamp,
        warnings=warnings,
    )


def _make_resolution_request(
    *,
    defaults: AppConfig,
    project: ProjectConfig,
    environment: EnvironmentOverrides,
    source_values: SourceValues,
) -> ConfigurationResolutionRequest:
    parameters = inspect.signature(ConfigurationResolutionRequest).parameters

    if "source_values" in parameters:
        return _SourceValuesResolutionRequest(
            defaults=defaults,
            project=project,
            environment=environment,
            source_values=source_values,
        )
    if "candidates_by_source" in parameters:
        return ConfigurationResolutionRequest(
            defaults=defaults,
            project=project,
            environment=environment,
            candidates_by_source=source_values,
        )

    raise ContractViolationError(
        "ConfigurationResolutionRequest exposes no supported source-values field",
        code="GF-WB-CONTRACT-001",
        stage="bootstrap",
        operation="compose-configuration-request",
    )


def _configuration_source_values(
    request: InvocationRequest,
    project: ProjectConfig,
    state: AppState,
) -> SourceValues:
    invocation: dict[str, object] = {}

    explicit_project_root = _explicit_project_root(request)
    if explicit_project_root is not None:
        invocation["project_root"] = explicit_project_root

    for name in (
        "gf_executable",
        "rgl_root",
        "output_root",
        "state_path",
    ):
        value = getattr(request, name)
        if value is not None:
            invocation[name] = os.fspath(value)

    if request.mode is not None:
        invocation["mode"] = request.mode
    target = request.resolved_target
    if target is not None:
        invocation["target"] = target

    for name in (
        "timeout_sec",
        "max_files",
        "keep_ok_details",
        "diff_previous",
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
        "evidence_level",
    ):
        value = getattr(request, name)
        if value is not None:
            invocation[name] = value

    state_values = _state_source_values(state)
    runtime_values: dict[str, object] = {}
    if target is None:
        derived = _derived_target(_coerce_mode(request.mode), project)
        if derived is not None:
            runtime_values["target"] = derived

    grouped: dict[ConfigurationSource, Mapping[str, object]] = {}
    if invocation:
        grouped[request.source] = MappingProxyType(invocation)
    if state_values:
        grouped[ConfigurationSource.APPLICATION_STATE] = MappingProxyType(state_values)
    if runtime_values:
        grouped[ConfigurationSource.RUNTIME_DERIVED] = MappingProxyType(runtime_values)

    return MappingProxyType(grouped)


def _state_source_values(state: AppState) -> dict[str, object]:
    values: dict[str, object] = {}
    environment = state.environment
    selection = state.selection

    for name in (
        "project_root",
        "gf_executable",
        "rgl_root",
        "output_root",
    ):
        value = getattr(environment, name)
        if value:
            values[name] = value

    values.update(
        {
            "mode": selection.mode,
            "timeout_sec": selection.timeout_sec,
            "max_files": selection.max_files,
            "keep_ok_details": selection.keep_ok_details,
            "diff_previous": selection.diff_previous,
            "skip_version_probe": selection.skip_version_probe,
            "no_compile": selection.no_compile,
            "emit_cpu_stats": selection.emit_cpu_stats,
        }
    )
    if selection.target_file:
        values["target"] = ValidationTarget(
            TargetKind.FILE,
            selection.target_file,
        )
    return values


def _apply_effective_selection(
    configuration: RunConfig,
    request: InvocationRequest,
) -> RunConfig:
    mode = configuration.mode
    target = configuration.target
    project = _require_project_config(
        configuration.project,
        field_name="configuration.project",
    )
    checkpoints = configuration.selected_checkpoints
    entrypoints = configuration.selected_entrypoints
    scenarios = configuration.selected_scenarios

    if request.scenario_filter:
        unknown = tuple(item for item in request.scenario_filter if item not in scenarios)
        if unknown:
            raise ConfigurationError(
                "Unknown scenario filter.",
                code="GF-WB-CONFIG-003",
                detail=", ".join(unknown),
                stage="bootstrap",
                operation="select-scenarios",
                subject=project.project_id,
            )
        scenarios = request.scenario_filter

    if mode is ValidationMode.QUICK:
        checkpoints = ()
        entrypoints = ()
        scenarios = ()
    elif mode is ValidationMode.CHECKPOINT:
        entrypoints = ()
        if target is not None:
            checkpoints = _select_checkpoint(checkpoints, target)
    elif mode is ValidationMode.RELEASE:
        if request.scenario_filter:
            required = tuple(
                str(item) for item in project.validation.required_scenarios
            )
            omitted = tuple(item for item in required if item not in scenarios)
            if omitted:
                raise ConfigurationError(
                    "Release mode cannot omit required scenarios.",
                    code="GF-WB-CONFIG-004",
                    detail=", ".join(omitted),
                    stage="bootstrap",
                    operation="select-scenarios",
                    subject=project.project_id,
                )

    return replace(
        configuration,
        selected_checkpoints=checkpoints,
        selected_entrypoints=entrypoints,
        selected_scenarios=scenarios,
    )


def _select_checkpoint(
    checkpoints: tuple[Path, ...],
    target: ValidationTarget,
) -> tuple[Path, ...]:
    if target.kind is not TargetKind.CHECKPOINT:
        return checkpoints
    if target.value is None:
        raise ConfigurationError(
            "Checkpoint target is missing its identifier.",
            code="GF-WB-CONFIG-005",
            stage="bootstrap",
            operation="select-checkpoint",
        )

    requested = target.value.replace("\\", "/").casefold()
    matches = tuple(
        path
        for path in checkpoints
        if requested
        in {
            path.name.casefold(),
            path.stem.casefold(),
            path.as_posix().casefold(),
        }
    )
    if len(matches) == 1:
        return matches
    if not matches:
        raise ConfigurationError(
            "Unknown checkpoint target.",
            code="GF-WB-CONFIG-006",
            detail=target.value,
            stage="bootstrap",
            operation="select-checkpoint",
            subject=target.value,
        )
    raise ConfigurationError(
        "Checkpoint target is ambiguous.",
        code="GF-WB-CONFIG-007",
        detail=", ".join(path.as_posix() for path in matches),
        stage="bootstrap",
        operation="select-checkpoint",
        subject=target.value,
    )


def _derived_target(
    mode: ValidationMode | None,
    project: ProjectConfig,
) -> ValidationTarget | None:
    if mode is ValidationMode.RELEASE:
        return ValidationTarget(TargetKind.PROJECT, None)
    if mode is ValidationMode.CHECKPOINT and len(project.modules.checkpoints) == 1:
        checkpoint = project.modules.checkpoints[0]
        return ValidationTarget(TargetKind.CHECKPOINT, checkpoint.as_posix())
    return None


def _select_project_file(
    request: InvocationRequest,
    environment: EnvironmentOverrides,
    state: AppState,
) -> Path:
    if request.project_file is not None:
        return _project_file_path(request.project_file)

    candidates: Sequence[tuple[str, object | None]] = (
        ("invocation", request.project_root),
        ("environment", environment.project_root),
        ("application state", state.environment.project_root),
    )
    for source, value in candidates:
        if value is None or value == "":
            continue
        if not isinstance(value, (str, os.PathLike, Path)):
            raise TypeError(f"{source} project root must be path-like")
        root = _absolute_path(value, role=f"{source} project root")
        return root / PROJECT_CONFIG_FILENAME

    raise ProjectConfigurationError(
        "No active project was selected.",
        code="GF-WB-PROJECT-002",
        detail=(
            "Supply an explicit project_file or project_root, set "
            "GF_WORDBENCH_PROJECT_ROOT, or select a project in application state."
        ),
        stage="bootstrap",
        operation="select-project",
    )


def _workspace_hint(
    request: InvocationRequest,
    environment: EnvironmentOverrides,
) -> Path | None:
    if request.workspace_root is not None:
        return _absolute_path(request.workspace_root, role="workspace_root")
    if request.project_file is not None:
        return _project_file_path(request.project_file).parent
    if request.project_root is not None:
        return _absolute_path(request.project_root, role="project_root")
    if environment.project_root:
        return _absolute_path(
            environment.project_root,
            role="environment project_root",
        )
    return None


def _load_state(
    request: InvocationRequest,
    environment: EnvironmentOverrides,
    workspace_root: Path | None,
    defaults: AppConfig,
    services: BootstrapServices,
) -> StateLoadResult:
    if workspace_root is None or not request.load_state:
        source_root = workspace_root or Path(__file__).resolve().parent
        source_path = source_root / defaults.state_filename
        return StateLoadResult(
            state=default_app_state(),
            source_path=source_path,
            diagnostics=(),
            migrated=False,
        )

    _require_directory(workspace_root, role="workspace root")
    state_path_value = request.state_path or environment.state_path
    state_path = (
        None if state_path_value is None else _absolute_path(state_path_value, role="state_path")
    )
    try:
        result = services.state_loader(workspace_root, state_path)
    except Exception as exc:
        raise ConfigurationError(
            "Application state could not be loaded safely.",
            code="GF-WB-STATE-001",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="load-state",
            subject=str(state_path or workspace_root),
        ) from exc
    if not isinstance(result, StateLoadResult):
        raise TypeError("state_loader must return StateLoadResult")
    return result


def _preview_paths(
    output_root: Path,
    timestamp: datetime,
    requested_run_id: RunId | str | None,
) -> RunPaths:
    root = _require_directory(output_root, role="run output root")
    if requested_run_id is not None:
        run_id = validate_run_id(requested_run_id)
        run_dir = root / run_directory_name(run_id)
        if run_dir.exists():
            raise ConfigurationError(
                "Requested run ID already exists.",
                code="GF-WB-PATH-001",
                stage="bootstrap",
                operation="preview-run-paths",
                subject=str(run_dir),
            )
        return _build_preview_run_paths(run_id, run_dir)

    for index, run_id in enumerate(iter_run_id_candidates(timestamp), start=1):
        if index > _MAX_COLLISION_ATTEMPTS:
            break
        run_dir = root / run_directory_name(run_id)
        if not run_dir.exists():
            return _build_preview_run_paths(run_id, run_dir)

    raise ConfigurationError(
        "No collision-free run identifier could be selected.",
        code="GF-WB-PATH-002",
        stage="bootstrap",
        operation="preview-run-paths",
        subject=str(root),
    )


def _build_preview_run_paths(
    run_id: RunId | str,
    run_dir: Path,
) -> RunPaths:
    validated = validate_run_id(run_id)
    expected = build_expected_path_map(run_dir)
    return RunPaths(
        run_id=str(validated),
        run_dir=expected["run_dir"],
        summary_json=expected["summary_json"],
        summary_md=expected["summary_md"],
        ai_ready_md=expected["ai_ready_md"],
        top_errors_txt=expected["top_errors_txt"],
        manifest_json=expected["manifest_json"],
        details_dir=expected["details_dir"],
        raw_dir=expected["raw_dir"],
        master_log=expected["master_log"],
        all_scan_logs=expected["all_scan_logs"],
        all_logs=expected["all_logs"],
        raw_compile_dir=expected["raw_compile_dir"],
        raw_scan_dir=expected["raw_scan_dir"],
        raw_scenarios_dir=expected["raw_scenarios_dir"],
        artifacts_dir=expected["artifacts_dir"],
        gfo_dir=expected["gfo_dir"],
        out_dir=expected["out_dir"],
        pgf_dir=expected["pgf_dir"],
    )


def _allocate_paths(
    output_root: Path,
    timestamp: datetime,
    requested_run_id: RunId | str | None,
    allocator: Callable[[Path, RunId | str], RunPaths],
) -> RunPaths:
    root = _require_directory(output_root, role="run output root")
    if requested_run_id is not None:
        run_id = validate_run_id(requested_run_id)
        try:
            return allocator(root, run_id)
        except FileExistsError as exc:
            raise ConfigurationError(
                "Requested run ID already exists.",
                code="GF-WB-PATH-001",
                stage="bootstrap",
                operation="allocate-run-paths",
                subject=str(root / run_directory_name(run_id)),
            ) from exc

    for index, run_id in enumerate(iter_run_id_candidates(timestamp), start=1):
        if index > _MAX_COLLISION_ATTEMPTS:
            break
        try:
            return allocator(root, run_id)
        except FileExistsError:
            continue

    raise ConfigurationError(
        "No collision-free run directory could be allocated.",
        code="GF-WB-PATH-002",
        stage="bootstrap",
        operation="allocate-run-paths",
        subject=str(root),
    )


def _context(
    prepared: _PreparedBootstrap,
    paths: RunPaths,
    *,
    created: bool,
) -> BootstrapContext:
    return BootstrapContext(
        request=prepared.request,
        defaults=prepared.defaults,
        project=prepared.project,
        state=prepared.state,
        environment_overrides=prepared.environment,
        resolution=prepared.resolution,
        run_config=prepared.run_config,
        preflight=prepared.preflight,
        plan=prepared.plan,
        run_paths=paths,
        created_run_directory=created,
        warnings=prepared.warnings,
    )


def _collect_warnings(
    state: StateLoadResult,
    resolution: ConfigurationResolution,
    preflight: PreflightResult,
    request: InvocationRequest,
) -> tuple[str, ...]:
    values: list[str] = []
    values.extend(request.compatibility_warnings)
    for diagnostic in state.diagnostics:
        values.append(diagnostic.message)
    for issue in resolution.issues:
        severity = getattr(issue.severity, "value", str(issue.severity))
        if severity == "warning":
            values.append(issue.message)
    for warning in preflight.warnings:
        values.append(warning.message)
    return _unique_text_tuple(
        values,
        field_name="bootstrap warnings",
        maximum=_MAX_BOOTSTRAP_WARNINGS,
    )


def _explicit_project_root(request: InvocationRequest) -> str | None:
    if request.project_file is not None:
        return os.fspath(_project_file_path(request.project_file).parent)
    if request.project_root is not None:
        return os.fspath(request.project_root)
    return None


def _project_file_path(value: PathInput) -> Path:
    path = _absolute_path(value, role="project_file")
    if path.name != PROJECT_CONFIG_FILENAME:
        raise ProjectConfigurationError(
            f"Active project file must be named {PROJECT_CONFIG_FILENAME!r}.",
            code="GF-WB-PROJECT-003",
            stage="bootstrap",
            operation="select-project",
            subject=str(path),
        )
    return path


def _absolute_path(value: PathInput, *, role: str) -> Path:
    try:
        return normalize_environment_path(value, role=role)
    except Exception as exc:
        raise ConfigurationError(
            f"Invalid {role}.",
            code="GF-WB-PATH-003",
            detail=f"{type(exc).__name__}: {_bounded_message(exc)}",
            stage="bootstrap",
            operation="normalize-path",
            subject=os.fspath(value),
        ) from exc


def _require_regular_file(path: Path, *, role: str) -> Path:
    if not path.exists():
        raise ProjectConfigurationError(
            f"{role.capitalize()} does not exist.",
            code="GF-WB-PROJECT-004",
            stage="bootstrap",
            operation="load-project",
            subject=str(path),
        )
    if not path.is_file():
        raise ProjectConfigurationError(
            f"{role.capitalize()} is not a regular file.",
            code="GF-WB-PROJECT-005",
            stage="bootstrap",
            operation="load-project",
            subject=str(path),
        )
    return path


def _require_directory(path: Path, *, role: str) -> Path:
    if not path.exists():
        raise ConfigurationError(
            f"{role.capitalize()} does not exist.",
            code="GF-WB-PATH-004",
            stage="bootstrap",
            operation="validate-path",
            subject=str(path),
        )
    if not path.is_dir():
        raise ConfigurationError(
            f"{role.capitalize()} is not a directory.",
            code="GF-WB-PATH-005",
            stage="bootstrap",
            operation="validate-path",
            subject=str(path),
        )
    return path


def _require_project_config(
    value: object | None,
    *,
    field_name: str,
) -> ProjectConfig:
    if not isinstance(value, ProjectConfig):
        raise ContractViolationError(
            f"{field_name} must be a ProjectConfig.",
            code="GF-WB-CONTRACT-009",
            stage="bootstrap",
            operation="validate-project-configuration",
            subject=field_name,
        )
    return value


def _require_validation_mode(
    value: ValidationMode | None,
    *,
    field_name: str,
) -> ValidationMode:
    if value is None:
        raise ValueError(f"{field_name} must resolve to a validation mode")
    return value


def _coerce_evidence_level(
    value: object,
    *,
    field_name: str,
) -> EvidenceLevel:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    allowed: tuple[EvidenceLevel, ...] = (
        "bounded",
        "standard",
        "complete",
        "expanded",
    )
    if value not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {choices}")
    return cast("EvidenceLevel", value)


def _coerce_mode(value: ValidationMode | str | None) -> ValidationMode | None:
    if value is None or isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise TypeError("mode must be a ValidationMode, string, or None")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("mode must not be blank")
    alias = _LEGACY_MODE_ALIASES.get(normalized)
    if alias is not None:
        return alias
    try:
        return ValidationMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ValidationMode)
        raise ValueError(f"mode must be one of: {allowed}") from exc


def _require_utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("clock must return datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def _validate_path_input(value: PathInput, *, field_name: str) -> None:
    rendered = os.fspath(value)
    if not rendered or "\x00" in rendered:
        raise ValueError(f"{field_name} must be non-empty and NUL-free")


def _optional_trimmed_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    _require_text(value, field_name=field_name)
    normalized = value.strip()
    if normalized != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    return normalized


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip() or "\x00" in value:
        raise ValueError(f"{field_name} must be non-empty and NUL-free")
    return value


def _unique_text_tuple(
    values: Sequence[str],
    *,
    field_name: str,
    maximum: int,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field_name} must be a sequence of strings")
    if len(values) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} entries")
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        text = _require_text(value, field_name=f"{field_name}[{index}]")
        if text != text.strip():
            raise ValueError(f"{field_name}[{index}] must not contain surrounding whitespace")
        if text not in seen:
            result.append(text)
            seen.add(text)
    return tuple(result)


def _require_plain_int(
    value: object,
    *,
    field_name: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    checked = value
    if checked < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return checked


def _bounded_message(error: BaseException) -> str:
    message = " ".join(str(error).replace("\x00", "\\x00").split())
    if not message:
        return "no diagnostic detail"
    return message[:2000]


__all__ = (
    "BootstrapContext",
    "BootstrapServices",
    "GoldUpdateApplication",
    "GoldUpdateWorkflow",
    "GuiRuntime",
    "GuiRuntimeFactory",
    "InvocationRequest",
    "bootstrap_run",
    "build_audit_application",
    "build_framework_defaults",
    "build_gold_update_application",
    "build_gui_startup_runtime",
    "build_language_probe_application",
    "build_project_check_application",
    "build_scenario_check_application",
    "load_active_project",
    "preview_run",
    "resolve_run_configuration",
)
