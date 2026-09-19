"""Pure, field-specific configuration precedence resolution.

This module owns source authority, equal-tier conflict detection, and provenance
for startup selections and scalar run options. Filesystem validation, language
probing, executable discovery, validation-profile loading, and final ``RunConfig``
construction belong to their dedicated application and composition services.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from functools import lru_cache
from importlib import import_module
import os
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Final, Protocol, cast

from gf_wordbench.kernel.statuses import ValidationMode

__all__ = (
    "PRECEDENCE_POLICIES",
    "ConfigurationDomain",
    "ConfigurationSource",
    "OverrideClass",
    "PrecedencePolicy",
    "PrecedenceResolution",
    "PrecedenceValues",
    "policy_for",
    "resolve_precedence",
)


@unique
class ConfigurationSource(StrEnum):
    """Documented provenance of one configuration value."""

    PACKAGE_METADATA = "package_metadata"
    FRAMEWORK_DEFAULT = "framework_default"
    VALIDATION_PROFILE = "validation_profile"
    PROJECT_TOML = "project_toml"
    APPLICATION_STATE = "application_state"
    ENVIRONMENT_VARIABLE = "environment_variable"
    PATH_DISCOVERY = "path_discovery"
    LANGUAGE_PROBE = "language_probe"
    SELECTION_SERVICE = "selection_service"
    CLI = "cli"
    GUI = "gui"
    AUTOMATION = "automation"
    STARTUP_OPTION = "startup_option"
    RUNTIME_DERIVED = "runtime_derived"
    LEGACY_MIGRATION = "legacy_migration"


@unique
class ConfigurationDomain(StrEnum):
    """Configuration domains with distinct precedence rules."""

    SELECTED_LANGUAGE_PATH = "selected_language_path"
    VALIDATION_PROFILE = "validation_profile"
    GF_EXECUTABLE = "gf_executable"
    RGL_ROOT = "rgl_root"
    OUTPUT_ROOT = "output_root"
    STATE_PATH = "state_path"
    PROFILE_FIELD = "profile_field"
    MODE = "mode"
    PROJECT_ROOT = "project_root"
    PROJECT_FIELD = "project_field"
    TARGET = "target"
    TIMEOUT = "timeout"
    RUN_OPTION = "run_option"


@unique
class OverrideClass(StrEnum):
    """Effect of an override on validation strength and release truth."""

    STRENGTHENING = "strengthening"
    NEUTRAL = "neutral"
    WEAKENING = "weakening"


@dataclass(frozen=True, slots=True)
class PrecedencePolicy:
    """Ordered authority tiers for one configuration domain.

    Earlier tiers have greater authority. Sources in the same tier are
    equivalent; tuple order is not a tie-breaker.
    """

    domain: ConfigurationDomain
    tiers: tuple[tuple[ConfigurationSource, ...], ...]

    def __post_init__(self) -> None:
        if not self.tiers or any(not tier for tier in self.tiers):
            raise ValueError("a precedence policy requires non-empty tiers")

        sources = tuple(source for tier in self.tiers for source in tier)
        if len(sources) != len(set(sources)):
            raise ValueError("a source may appear only once in a precedence policy")

    def rank(self, source: ConfigurationSource) -> int:
        """Return the zero-based authority rank of ``source``."""

        for rank, tier in enumerate(self.tiers):
            if source in tier:
                return rank

        raise ValueError(f"{source.value!r} is not authorized for {self.domain.value!r}")

    def allows(self, source: ConfigurationSource) -> bool:
        """Return whether ``source`` may contribute to this domain."""

        return any(source in tier for tier in self.tiers)

    def outranks(
        self,
        left: ConfigurationSource,
        right: ConfigurationSource,
    ) -> bool:
        """Return whether ``left`` has greater authority than ``right``."""

        return self.rank(left) < self.rank(right)

    def equivalent(
        self,
        left: ConfigurationSource,
        right: ConfigurationSource,
    ) -> bool:
        """Return whether two sources occupy the same authority tier."""

        return self.rank(left) == self.rank(right)


_EXPLICIT_INVOCATION: Final[tuple[ConfigurationSource, ...]] = (
    ConfigurationSource.CLI,
    ConfigurationSource.GUI,
    ConfigurationSource.AUTOMATION,
)

_EXPLICIT_STARTUP: Final[tuple[ConfigurationSource, ...]] = (
    ConfigurationSource.STARTUP_OPTION,
    *_EXPLICIT_INVOCATION,
)

_RUN_OPTION_TIERS: Final[tuple[tuple[ConfigurationSource, ...], ...]] = (
    _EXPLICIT_INVOCATION,
    (ConfigurationSource.APPLICATION_STATE,),
    (ConfigurationSource.FRAMEWORK_DEFAULT,),
)


_PRECEDENCE_POLICIES: Final[dict[ConfigurationDomain, PrecedencePolicy]] = {
    ConfigurationDomain.SELECTED_LANGUAGE_PATH: PrecedencePolicy(
        domain=ConfigurationDomain.SELECTED_LANGUAGE_PATH,
        tiers=(
            _EXPLICIT_STARTUP,
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.LEGACY_MIGRATION,),
        ),
    ),
    ConfigurationDomain.VALIDATION_PROFILE: PrecedencePolicy(
        domain=ConfigurationDomain.VALIDATION_PROFILE,
        tiers=(
            _EXPLICIT_STARTUP,
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.LEGACY_MIGRATION,),
        ),
    ),
    ConfigurationDomain.GF_EXECUTABLE: PrecedencePolicy(
        domain=ConfigurationDomain.GF_EXECUTABLE,
        tiers=(
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.PATH_DISCOVERY,),
        ),
    ),
    ConfigurationDomain.RGL_ROOT: PrecedencePolicy(
        domain=ConfigurationDomain.RGL_ROOT,
        tiers=(
            (ConfigurationSource.LANGUAGE_PROBE,),
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.PATH_DISCOVERY,),
        ),
    ),
    ConfigurationDomain.OUTPUT_ROOT: PrecedencePolicy(
        domain=ConfigurationDomain.OUTPUT_ROOT,
        tiers=(
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.APPLICATION_STATE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
    ),
    ConfigurationDomain.STATE_PATH: PrecedencePolicy(
        domain=ConfigurationDomain.STATE_PATH,
        tiers=(
            _EXPLICIT_STARTUP,
            (ConfigurationSource.ENVIRONMENT_VARIABLE,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
    ),
    ConfigurationDomain.PROFILE_FIELD: PrecedencePolicy(
        domain=ConfigurationDomain.PROFILE_FIELD,
        tiers=(
            (ConfigurationSource.VALIDATION_PROFILE,),
            (ConfigurationSource.PROJECT_TOML,),
        ),
    ),
    ConfigurationDomain.MODE: PrecedencePolicy(
        domain=ConfigurationDomain.MODE,
        tiers=(
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.VALIDATION_PROFILE,),
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
    ),
    ConfigurationDomain.TARGET: PrecedencePolicy(
        domain=ConfigurationDomain.TARGET,
        tiers=(
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.LANGUAGE_PROBE,),
            (ConfigurationSource.VALIDATION_PROFILE,),
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.RUNTIME_DERIVED,),
        ),
    ),
    ConfigurationDomain.TIMEOUT: PrecedencePolicy(
        domain=ConfigurationDomain.TIMEOUT,
        tiers=(
            _EXPLICIT_INVOCATION,
            (ConfigurationSource.VALIDATION_PROFILE,),
            (ConfigurationSource.PROJECT_TOML,),
            (ConfigurationSource.FRAMEWORK_DEFAULT,),
        ),
    ),
    ConfigurationDomain.RUN_OPTION: PrecedencePolicy(
        domain=ConfigurationDomain.RUN_OPTION,
        tiers=_RUN_OPTION_TIERS,
    ),
    # Compatibility-only domains. They must not become normal startup authority.
    ConfigurationDomain.PROJECT_ROOT: PrecedencePolicy(
        domain=ConfigurationDomain.PROJECT_ROOT,
        tiers=((ConfigurationSource.LEGACY_MIGRATION,),),
    ),
    ConfigurationDomain.PROJECT_FIELD: PrecedencePolicy(
        domain=ConfigurationDomain.PROJECT_FIELD,
        tiers=((ConfigurationSource.PROJECT_TOML,),),
    ),
}

PRECEDENCE_POLICIES: Final[Mapping[ConfigurationDomain, PrecedencePolicy]] = MappingProxyType(
    _PRECEDENCE_POLICIES
)


def policy_for(domain: ConfigurationDomain) -> PrecedencePolicy:
    """Return the canonical precedence policy for ``domain``."""

    return PRECEDENCE_POLICIES[domain]


class _IssueSeverityMembers(Protocol):
    ERROR: object
    WARNING: object
    INFO: object


class _ConfigurationIssueView(Protocol):
    severity: object
    source: ConfigurationSource
    field_path: str
    message: str


class _ConfigurationProvenanceView(Protocol):
    field_path: str
    source: ConfigurationSource


class _ConfigurationIssueFactory(Protocol):
    def __call__(
        self,
        *,
        severity: object,
        source: ConfigurationSource,
        field_path: str,
        provided_value: object,
        message: str,
        remediation: str,
    ) -> _ConfigurationIssueView: ...


class _ConfigurationProvenanceFactory(Protocol):
    def __call__(
        self,
        *,
        field_path: str,
        source: ConfigurationSource,
        provided_value: object,
        resolved_value: object,
    ) -> _ConfigurationProvenanceView: ...


class _SelectionDefaultsView(Protocol):
    mode: ValidationMode
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool


class _OutputDefaultsView(Protocol):
    evidence_level: str


class _DefaultsView(Protocol):
    selection_defaults: _SelectionDefaultsView
    output_defaults: _OutputDefaultsView


class _EnvironmentView(Protocol):
    gf_executable: str | None
    rgl_root: str | None
    output_root: str | None
    state_path: str | None
    project_root: str | None


class _ResolutionRequestView(Protocol):
    defaults: _DefaultsView
    environment: _EnvironmentView
    project: object | None
    source_values: Mapping[
        ConfigurationSource,
        Mapping[str, object],
    ]

    @property
    def validation_profile(self) -> object | None: ...


@dataclass(frozen=True, slots=True)
class _ModelContracts:
    request_type: type[object]
    validation_target_type: type[object]
    issue_factory: _ConfigurationIssueFactory
    provenance_factory: _ConfigurationProvenanceFactory
    severity: _IssueSeverityMembers


@lru_cache(maxsize=1)
def _model_contracts() -> _ModelContracts:
    """Load model-owned contracts after ``config.models`` finished importing.

    ``config.models`` owns the request, issue, provenance and target models.
    Precedence owns only the source enum, policies and pure selection logic.
    Delaying this lookup until resolution removes the import-time and static
    module cycle without duplicating any public model.
    """

    module = import_module("gf_wordbench.config.models")
    return _contracts_from_module(module)


def _contracts_from_module(module: ModuleType) -> _ModelContracts:
    request_type = _require_model_type(
        module,
        "ConfigurationResolutionRequest",
    )
    validation_target_type = _require_model_type(
        module,
        "ValidationTarget",
    )
    issue_factory = cast(
        "_ConfigurationIssueFactory",
        _require_model_type(module, "ConfigurationIssue"),
    )
    provenance_factory = cast(
        "_ConfigurationProvenanceFactory",
        _require_model_type(module, "ConfigurationProvenance"),
    )
    severity = cast(
        "_IssueSeverityMembers",
        _require_model_type(module, "IssueSeverity"),
    )
    for member in ("ERROR", "WARNING", "INFO"):
        if not hasattr(severity, member):
            raise RuntimeError(f"config.models.IssueSeverity is missing {member}")

    return _ModelContracts(
        request_type=request_type,
        validation_target_type=validation_target_type,
        issue_factory=issue_factory,
        provenance_factory=provenance_factory,
        severity=severity,
    )


def _require_model_type(
    module: ModuleType,
    name: str,
) -> type[object]:
    value = getattr(module, name, None)
    if not isinstance(value, type):
        raise RuntimeError(f"config.models.{name} must be a runtime type")
    return value


@dataclass(frozen=True, slots=True)
class PrecedenceValues:
    """Effective values selected without filesystem access or discovery.

    ``project_root`` is retained only as a legacy migration value. New startup
    code uses ``selected_language_path`` and an optional ``validation_profile``.
    """

    selected_language_path: str | os.PathLike[str] | None
    validation_profile: str | os.PathLike[str] | None
    project_root: str | os.PathLike[str] | None
    gf_executable: str | os.PathLike[str] | None
    rgl_root: str | os.PathLike[str] | None
    output_root: str | os.PathLike[str] | None
    state_path: str | os.PathLike[str] | None
    mode: ValidationMode
    target: object | None
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool
    evidence_level: str
    selected_checkpoints: tuple[Path, ...]
    selected_entrypoints: tuple[Path, ...]
    selected_scenarios: tuple[str, ...]
    release_requires_pgf: bool

    def __post_init__(self) -> None:
        for name, specification in _FIELD_SPECIFICATIONS.items():
            error = specification.validator(getattr(self, name))
            if error is not None:
                raise ValueError(f"{name}: {error}")

        _require_unique_tuple(
            "selected_checkpoints",
            self.selected_checkpoints,
            Path,
        )
        _require_unique_tuple(
            "selected_entrypoints",
            self.selected_entrypoints,
            Path,
        )
        _require_unique_tuple(
            "selected_scenarios",
            self.selected_scenarios,
            str,
            non_empty=True,
        )
        if type(self.release_requires_pgf) is not bool:
            raise TypeError("release_requires_pgf must be a boolean")


@dataclass(frozen=True, slots=True)
class PrecedenceResolution:
    """Selected values plus structured issues and winning-source provenance."""

    values: PrecedenceValues | None
    issues: tuple[_ConfigurationIssueView, ...] = ()
    provenance: tuple[_ConfigurationProvenanceView, ...] = ()


@dataclass(frozen=True, slots=True)
class _FieldSpecification:
    domain: ConfigurationDomain
    validator: Callable[[object], str | None]
    required: bool = True


def _optional_path(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (str, os.PathLike)):
        return "must be a path-like value or None"

    rendered = os.fspath(value)
    if isinstance(rendered, bytes):
        return "must resolve to text, not bytes"
    if "\x00" in rendered:
        return "must not contain NUL"
    return None


def _instance(
    expected: type[object],
    description: str,
    *,
    optional: bool = False,
) -> Callable[[object], str | None]:
    def validate(value: object) -> str | None:
        if optional and value is None:
            return None
        if isinstance(value, expected):
            return None
        suffix = " or None" if optional else ""
        return f"must be {description}{suffix}"

    return validate


def _validation_target(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, _model_contracts().validation_target_type):
        return None
    return "must be a ValidationTarget or None"


def _integer(minimum: int) -> Callable[[object], str | None]:
    def validate(value: object) -> str | None:
        if type(value) is not int:
            return "must be an integer"
        if value < minimum:
            return f"must be greater than or equal to {minimum}"
        return None

    return validate


def _boolean(value: object) -> str | None:
    return None if type(value) is bool else "must be a boolean"


_EVIDENCE_LEVELS: Final = frozenset({"bounded", "standard", "complete", "expanded"})


def _evidence_level(value: object) -> str | None:
    if not isinstance(value, str):
        return "must be a string"
    if value not in _EVIDENCE_LEVELS:
        return "must be one of: " + ", ".join(sorted(_EVIDENCE_LEVELS))
    return None


def _require_unique_tuple(
    name: str,
    values: tuple[object, ...],
    item_type: type[object],
    *,
    non_empty: bool = False,
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    if any(not isinstance(value, item_type) for value in values):
        raise TypeError(f"{name} must contain {item_type.__name__} values")
    if non_empty:
        for value in values:
            if not isinstance(value, str):
                raise TypeError(f"{name} must contain string values")
            if not value or value != value.strip() or "\x00" in value:
                raise ValueError(
                    f"{name} must contain non-empty, trimmed, NUL-free strings"
                )
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")


_FIELD_SPECIFICATIONS: Final[Mapping[str, _FieldSpecification]] = MappingProxyType(
    {
        "selected_language_path": _FieldSpecification(
            ConfigurationDomain.SELECTED_LANGUAGE_PATH,
            _optional_path,
            required=False,
        ),
        "validation_profile": _FieldSpecification(
            ConfigurationDomain.VALIDATION_PROFILE,
            _optional_path,
            required=False,
        ),
        "project_root": _FieldSpecification(
            ConfigurationDomain.PROJECT_ROOT,
            _optional_path,
            required=False,
        ),
        "gf_executable": _FieldSpecification(
            ConfigurationDomain.GF_EXECUTABLE,
            _optional_path,
            required=False,
        ),
        "rgl_root": _FieldSpecification(
            ConfigurationDomain.RGL_ROOT,
            _optional_path,
            required=False,
        ),
        "output_root": _FieldSpecification(
            ConfigurationDomain.OUTPUT_ROOT,
            _optional_path,
            required=False,
        ),
        "state_path": _FieldSpecification(
            ConfigurationDomain.STATE_PATH,
            _optional_path,
            required=False,
        ),
        "mode": _FieldSpecification(
            ConfigurationDomain.MODE,
            _instance(ValidationMode, "a ValidationMode"),
        ),
        "target": _FieldSpecification(
            ConfigurationDomain.TARGET,
            _validation_target,
            required=False,
        ),
        "timeout_sec": _FieldSpecification(
            ConfigurationDomain.TIMEOUT,
            _integer(1),
        ),
        "max_files": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _integer(0),
        ),
        "keep_ok_details": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _boolean,
        ),
        "diff_previous": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _boolean,
        ),
        "skip_version_probe": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _boolean,
        ),
        "no_compile": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _boolean,
        ),
        "emit_cpu_stats": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _boolean,
        ),
        "evidence_level": _FieldSpecification(
            ConfigurationDomain.RUN_OPTION,
            _evidence_level,
        ),
    }
)

_MISSING: Final = object()


def resolve_precedence(
    request: object,
) -> PrecedenceResolution:
    """Resolve supplied immutable values without filesystem access.

    A validation profile is optional. ``request.project`` is accepted only as a
    compatibility representation of a profile until the request model migration
    is complete.
    """

    contracts = _model_contracts()
    if not isinstance(request, contracts.request_type):
        raise TypeError("request must be a ConfigurationResolutionRequest")
    typed_request = cast("_ResolutionRequestView", request)

    candidates, issues = _collect_candidates(typed_request)
    resolved: dict[str, object] = {}
    provenance: list[_ConfigurationProvenanceView] = []

    for name, specification in _FIELD_SPECIFICATIONS.items():
        value, source, field_issues = _resolve_field(
            name,
            specification,
            candidates,
        )
        issues.extend(field_issues)
        if value is _MISSING:
            continue

        resolved[name] = value
        if source is not None:
            provenance.append(
                _provenance(
                    field_path=name,
                    source=source,
                    provided_value=value,
                    resolved_value=value,
                )
            )

    (
        selected_checkpoints,
        selected_entrypoints,
        selected_scenarios,
        release_requires_pgf,
        profile_source,
    ) = _profile_policy(typed_request)

    if profile_source is not None:
        profile_values = {
            "selected_checkpoints": selected_checkpoints,
            "selected_entrypoints": selected_entrypoints,
            "selected_scenarios": selected_scenarios,
            "release_requires_pgf": release_requires_pgf,
        }
        provenance.extend(
            _provenance(
                field_path=name,
                source=profile_source,
                provided_value=value,
                resolved_value=value,
            )
            for name, value in profile_values.items()
        )

    ordered_issues = _ordered_issues(issues)
    ordered_provenance = tuple(sorted(provenance, key=lambda item: item.field_path))
    if any(issue.severity is contracts.severity.ERROR for issue in ordered_issues):
        return PrecedenceResolution(
            values=None,
            issues=ordered_issues,
            provenance=ordered_provenance,
        )

    return PrecedenceResolution(
        values=PrecedenceValues(
            selected_language_path=cast(
                "str | os.PathLike[str] | None", resolved.get("selected_language_path")
            ),
            validation_profile=cast(
                "str | os.PathLike[str] | None", resolved.get("validation_profile")
            ),
            project_root=cast(
                "str | os.PathLike[str] | None", resolved.get("project_root")
            ),
            gf_executable=cast(
                "str | os.PathLike[str] | None", resolved.get("gf_executable")
            ),
            rgl_root=cast("str | os.PathLike[str] | None", resolved.get("rgl_root")),
            output_root=cast(
                "str | os.PathLike[str] | None", resolved.get("output_root")
            ),
            state_path=cast(
                "str | os.PathLike[str] | None", resolved.get("state_path")
            ),
            mode=cast("ValidationMode", resolved["mode"]),
            target=resolved.get("target"),
            timeout_sec=cast("int", resolved["timeout_sec"]),
            max_files=cast("int", resolved["max_files"]),
            keep_ok_details=cast("bool", resolved["keep_ok_details"]),
            diff_previous=cast("bool", resolved["diff_previous"]),
            skip_version_probe=cast("bool", resolved["skip_version_probe"]),
            no_compile=cast("bool", resolved["no_compile"]),
            emit_cpu_stats=cast("bool", resolved["emit_cpu_stats"]),
            evidence_level=cast("str", resolved["evidence_level"]),
            selected_checkpoints=selected_checkpoints,
            selected_entrypoints=selected_entrypoints,
            selected_scenarios=selected_scenarios,
            release_requires_pgf=release_requires_pgf,
        ),
        issues=ordered_issues,
        provenance=ordered_provenance,
    )


def _profile_policy(
    request: _ResolutionRequestView,
) -> tuple[
    tuple[Path, ...],
    tuple[Path, ...],
    tuple[str, ...],
    bool,
    ConfigurationSource | None,
]:
    """Return optional profile-owned policy without making it startup authority."""

    profile = getattr(request, "validation_profile", None)
    source: ConfigurationSource | None = None

    if profile is not None:
        source = ConfigurationSource.VALIDATION_PROFILE
    else:
        profile = getattr(request, "project", None)
        if profile is not None:
            source = ConfigurationSource.PROJECT_TOML

    if profile is None:
        return (), (), (), False, None

    modules = getattr(profile, "modules", None)
    validation = getattr(profile, "validation", None)
    checkpoints = tuple(getattr(modules, "checkpoints", ()))
    entrypoints = tuple(getattr(modules, "entrypoints", ()))
    scenarios = tuple(getattr(validation, "all_scenarios", ()))
    release_requires_pgf = getattr(
        validation,
        "release_requires_pgf",
        False,
    )
    return (
        checkpoints,
        entrypoints,
        scenarios,
        release_requires_pgf,
        source,
    )


def _collect_candidates(
    request: _ResolutionRequestView,
) -> tuple[
    dict[ConfigurationSource, dict[str, object]],
    list[_ConfigurationIssueView],
]:
    candidates: dict[ConfigurationSource, dict[str, object]] = {}
    issues: list[_ConfigurationIssueView] = []

    source_values = getattr(
        request,
        "source_values",
        getattr(request, "candidates_by_source", {}),
    )
    for source, values in source_values.items():
        if not isinstance(source, ConfigurationSource):
            raise TypeError("candidates_by_source keys must be ConfigurationSource values")
        if not isinstance(values, Mapping):
            raise TypeError("candidates_by_source entries must be mappings")
        _merge_candidates(
            candidates,
            source,
            values,
            issues,
            owner="candidates_by_source",
        )

    environment = request.environment
    _merge_candidates(
        candidates,
        ConfigurationSource.ENVIRONMENT_VARIABLE,
        {
            name: value
            for name, value in {
                "gf_executable": getattr(environment, "gf_executable", None),
                "rgl_root": getattr(environment, "rgl_root", None),
                "output_root": getattr(environment, "output_root", None),
                "state_path": getattr(environment, "state_path", None),
            }.items()
            if value is not None
        },
        issues,
        owner="request.environment",
    )

    legacy_project_root = getattr(environment, "project_root", None)
    if legacy_project_root is not None:
        _merge_candidates(
            candidates,
            ConfigurationSource.LEGACY_MIGRATION,
            {"project_root": legacy_project_root},
            issues,
            owner="request.environment.project_root",
        )

    selection = request.defaults.selection_defaults
    output = request.defaults.output_defaults
    _merge_candidates(
        candidates,
        ConfigurationSource.FRAMEWORK_DEFAULT,
        {
            "mode": selection.mode,
            "timeout_sec": selection.timeout_sec,
            "max_files": selection.max_files,
            "keep_ok_details": selection.keep_ok_details,
            "diff_previous": selection.diff_previous,
            "skip_version_probe": selection.skip_version_probe,
            "no_compile": selection.no_compile,
            "emit_cpu_stats": selection.emit_cpu_stats,
            "evidence_level": output.evidence_level,
        },
        issues,
        owner="request.defaults",
    )
    return candidates, issues


def _merge_candidates(
    candidates: dict[ConfigurationSource, dict[str, object]],
    source: ConfigurationSource,
    values: Mapping[str, object],
    issues: list[_ConfigurationIssueView],
    *,
    owner: str,
) -> None:
    destination = candidates.setdefault(source, {})

    for name, value in values.items():
        if not isinstance(name, str):
            raise TypeError(f"{owner} field names must be strings")
        if name not in _FIELD_SPECIFICATIONS:
            issues.append(
                _error(
                    source,
                    name,
                    value,
                    f"Unknown precedence-controlled field {name!r}.",
                    "Remove it or define an owned precedence policy.",
                )
            )
            continue
        if name in destination and destination[name] != value:
            issues.append(
                _error(
                    source,
                    name,
                    (destination[name], value),
                    f"{source.value!r} supplied conflicting values for {name!r}.",
                    "Provide one value per source or make them agree.",
                )
            )
            continue
        destination.setdefault(name, value)


def _resolve_field(
    name: str,
    specification: _FieldSpecification,
    candidates: Mapping[
        ConfigurationSource,
        Mapping[str, object],
    ],
) -> tuple[
    object,
    ConfigurationSource | None,
    list[_ConfigurationIssueView],
]:
    policy = policy_for(specification.domain)
    issues = [
        _error(
            source,
            name,
            values[name],
            f"{source.value!r} is not authorized to set {name!r}.",
            f"Use a source authorized by the {specification.domain.value!r} policy.",
        )
        for source, values in candidates.items()
        if name in values and not policy.allows(source)
    ]

    for tier in policy.tiers:
        present = tuple(
            (source, candidates[source][name])
            for source in tier
            if source in candidates and name in candidates[source]
        )
        if not present:
            continue

        invalid = [
            _error(
                source,
                name,
                value,
                f"Invalid value for {name!r}: {message}.",
                "Correct or remove the value at this authority tier.",
            )
            for source, value in present
            if (message := specification.validator(value)) is not None
        ]
        if invalid:
            return _MISSING, None, [*issues, *invalid]

        reference = present[0][1]
        if any(value != reference for _, value in present[1:]):
            sources = ", ".join(sorted(source.value for source, _ in present))
            issues.append(
                _error(
                    ConfigurationSource.RUNTIME_DERIVED,
                    name,
                    tuple(value for _, value in present),
                    (f"Equivalent sources supplied conflicting values for {name!r}: {sources}."),
                    "Use one source at this tier or make all values agree.",
                )
            )
            return _MISSING, None, issues

        winner = min(
            (source for source, _ in present),
            key=lambda source: source.value,
        )
        return reference, winner, issues

    if not specification.required:
        return None, None, issues

    issues.append(
        _error(
            ConfigurationSource.RUNTIME_DERIVED,
            name,
            None,
            f"No authorized source supplied {name!r}.",
            "Provide the value or configure a framework default.",
        )
    )
    return _MISSING, None, issues


def _provenance(
    *,
    field_path: str,
    source: ConfigurationSource,
    provided_value: object,
    resolved_value: object,
) -> _ConfigurationProvenanceView:
    return _model_contracts().provenance_factory(
        field_path=field_path,
        source=source,
        provided_value=provided_value,
        resolved_value=resolved_value,
    )


def _error(
    source: ConfigurationSource,
    field_path: str,
    provided_value: object,
    message: str,
    remediation: str,
) -> _ConfigurationIssueView:
    contracts = _model_contracts()
    return contracts.issue_factory(
        severity=contracts.severity.ERROR,
        source=source,
        field_path=field_path,
        provided_value=provided_value,
        message=message,
        remediation=remediation,
    )


def _ordered_issues(
    issues: list[_ConfigurationIssueView],
) -> tuple[_ConfigurationIssueView, ...]:
    severity = _model_contracts().severity
    rank = {
        severity.ERROR: 0,
        severity.WARNING: 1,
        severity.INFO: 2,
    }
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                rank[issue.severity],
                issue.field_path,
                issue.source.value,
                issue.message,
            ),
        )
    )
