"""Immutable configuration models for GF Wordbench."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

from gf_wordbench.kernel.errors import ConfigurationError
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode
from gf_wordbench.projects.models import ProjectConfig

if TYPE_CHECKING:
    from gf_wordbench.config.precedence import ConfigurationSource
    from gf_wordbench.projects.languages.models import ResolvedLanguageContext


EvidenceLevel = Literal["bounded", "standard", "complete", "expanded"]

_EVIDENCE_LEVELS: Final[frozenset[str]] = frozenset(
    {"bounded", "standard", "complete", "expanded"}
)


@unique
class IssueSeverity(StrEnum):
    """Severity of one structured configuration finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@unique
class LanguageCapability(StrEnum):
    """Capability vocabulary shared by startup and run configuration."""

    SOURCE_READY = "source-ready"
    SCAN_READY = "scan-ready"
    COMPILE_READY = "compile-ready"
    SCENARIO_READY = "scenario-ready"
    RELEASE_READY = "release-ready"


def _require_plain_int(
    name: str,
    value: int,
    *,
    minimum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )


def _require_bool(
    name: str,
    value: bool,
) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")


def _require_non_empty_text(
    name: str,
    value: str,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if "\x00" in value:
        raise ValueError(
            f"{name} must not contain a NUL character"
        )


def _require_field_path(
    name: str,
    value: str,
) -> None:
    _require_non_empty_text(name, value)

    if value != value.strip():
        raise ValueError(
            f"{name} must not contain surrounding whitespace"
        )
    if "\r" in value or "\n" in value:
        raise ValueError(
            f"{name} must be a single-line field path"
        )


def _require_tuple(
    name: str,
    value: object,
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple")


def _require_absolute_normalized_path(
    name: str,
    value: Path,
) -> None:
    if not isinstance(value, Path):
        raise TypeError(f"{name} must be a pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{name} must be absolute")

    rendered = os.fspath(value)
    if "\x00" in rendered:
        raise ValueError(
            f"{name} must not contain a NUL character"
        )

    normalized = Path(os.path.normpath(rendered))
    if normalized != value:
        raise ValueError(
            f"{name} must be lexically normalized"
        )


def _path_key(value: Path) -> str:
    return os.path.normcase(
        os.path.normpath(os.fspath(value))
    )


def _require_unique_paths(
    name: str,
    values: tuple[Path, ...],
) -> None:
    _require_tuple(name, values)

    seen: set[str] = set()

    for index, value in enumerate(values):
        _require_absolute_normalized_path(
            f"{name}[{index}]",
            value,
        )

        key = _path_key(value)
        if key in seen:
            raise ValueError(
                f"{name} must not contain duplicate paths"
            )

        seen.add(key)


def _require_unique_non_empty_texts(
    name: str,
    values: tuple[str, ...],
) -> None:
    _require_tuple(name, values)

    seen: set[str] = set()

    for index, value in enumerate(values):
        _require_non_empty_text(
            f"{name}[{index}]",
            value,
        )

        if value in seen:
            raise ValueError(
                f"{name} must not contain duplicate values"
            )

        seen.add(value)


def _require_optional_non_empty_text(
    name: str,
    value: str | None,
) -> None:
    if value is None:
        return
    _require_non_empty_text(name, value)
    if value != value.strip():
        raise ValueError(
            f"{name} must not contain surrounding whitespace"
        )


def _require_contained_path(
    name: str,
    value: Path,
    *,
    parent: Path,
    allow_equal: bool = True,
) -> None:
    _require_absolute_normalized_path(name, value)
    _require_absolute_normalized_path(f"{name} parent", parent)

    try:
        relative = value.relative_to(parent)
    except ValueError as exc:
        raise ValueError(
            f"{name} must remain inside {parent!s}"
        ) from exc

    if not allow_equal and not relative.parts:
        raise ValueError(
            f"{name} must identify a child of {parent!s}"
        )


def _require_paths_contained(
    name: str,
    values: tuple[Path, ...],
    *,
    parent: Path,
) -> None:
    _require_unique_paths(name, values)
    for index, value in enumerate(values):
        _require_contained_path(
            f"{name}[{index}]",
            value,
            parent=parent,
        )


def _require_unique_capabilities(
    name: str,
    values: tuple[LanguageCapability, ...],
) -> None:
    _require_tuple(name, values)
    seen: set[LanguageCapability] = set()
    for index, value in enumerate(values):
        if not isinstance(value, LanguageCapability):
            raise TypeError(
                f"{name}[{index}] must be a LanguageCapability"
            )
        if value in seen:
            raise ValueError(
                f"{name} must not contain duplicate capabilities"
            )
        seen.add(value)


def _require_resolved_language_context(
    name: str,
    value: object,
) -> None:
    """Validate the public surface required from the projects-owned context."""

    required_paths = (
        "selected_path",
        "language_directory",
        "rgl_source_root",
    )
    for attribute in required_paths:
        path = getattr(value, attribute, None)
        if not isinstance(path, Path):
            raise TypeError(
                f"{name}.{attribute} must be a pathlib.Path"
            )
        _require_absolute_normalized_path(
            f"{name}.{attribute}",
            path,
        )

    language_key = getattr(value, "language_key", None)
    if not isinstance(language_key, str):
        raise TypeError(
            f"{name}.language_key must be a string"
        )
    _require_non_empty_text(
        f"{name}.language_key",
        language_key,
    )

    source_inventory = getattr(value, "source_inventory", None)
    if not isinstance(source_inventory, tuple):
        raise TypeError(
            f"{name}.source_inventory must be a tuple"
        )
    _require_paths_contained(
        f"{name}.source_inventory",
        source_inventory,
        parent=getattr(value, "language_directory"),
    )
    if not source_inventory:
        raise ValueError(
            f"{name}.source_inventory must not be empty"
        )

    _require_contained_path(
        f"{name}.language_directory",
        getattr(value, "language_directory"),
        parent=getattr(value, "rgl_source_root"),
    )


def _require_evidence_level(
    value: str,
) -> None:
    if not isinstance(value, str):
        raise TypeError(
            "evidence_level must be a string"
        )

    if value not in _EVIDENCE_LEVELS:
        allowed = ", ".join(
            sorted(_EVIDENCE_LEVELS)
        )
        raise ValueError(
            f"evidence_level must be one of: {allowed}"
        )


def _normalize_optional_raw_text(
    name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string or None"
        )
    if "\x00" in value:
        raise ValueError(
            f"{name} must not contain a NUL character"
        )

    return value or None


def _require_configuration_source(
    name: str,
    value: object,
) -> ConfigurationSource:
    # Lazy import avoids the models/precedence import cycle.
    from gf_wordbench.config.precedence import ConfigurationSource

    if not isinstance(value, ConfigurationSource):
        raise TypeError(
            f"{name} must be a ConfigurationSource"
        )

    return value


def _freeze_source_values(
    value: Mapping[
        ConfigurationSource,
        Mapping[str, object],
    ],
) -> Mapping[
    ConfigurationSource,
    Mapping[str, object],
]:
    if not isinstance(value, Mapping):
        raise TypeError(
            "source_values must be a mapping"
        )

    frozen: dict[
        ConfigurationSource,
        Mapping[str, object],
    ] = {}

    for raw_source, raw_candidates in value.items():
        source = _require_configuration_source(
            "source_values source",
            raw_source,
        )

        if not isinstance(raw_candidates, Mapping):
            raise TypeError(
                f"source_values[{source.value!r}] "
                "must be a mapping"
            )

        candidates: dict[str, object] = {}

        for field_path, candidate in raw_candidates.items():
            _require_field_path(
                "candidate field path",
                field_path,
            )
            candidates[field_path] = candidate

        frozen[source] = MappingProxyType(candidates)

    return MappingProxyType(frozen)


def _validate_issues(
    name: str,
    issues: tuple[ConfigurationIssue, ...],
) -> None:
    _require_tuple(name, issues)

    for index, issue in enumerate(issues):
        if not isinstance(issue, ConfigurationIssue):
            raise TypeError(
                f"{name}[{index}] must be "
                "a ConfigurationIssue"
            )


def _validate_provenance(
    name: str,
    provenance: tuple[
        ConfigurationProvenance,
        ...,
    ],
) -> None:
    _require_tuple(name, provenance)

    seen: set[str] = set()

    for index, record in enumerate(provenance):
        if not isinstance(
            record,
            ConfigurationProvenance,
        ):
            raise TypeError(
                f"{name}[{index}] must be "
                "a ConfigurationProvenance"
            )

        if record.field_path in seen:
            raise ValueError(
                f"{name} must not contain duplicate "
                f"field paths: {record.field_path!r}"
            )

        seen.add(record.field_path)


def _has_error(
    issues: tuple[ConfigurationIssue, ...],
) -> bool:
    return any(
        issue.severity is IssueSeverity.ERROR
        for issue in issues
    )


@dataclass(frozen=True, slots=True)
class EnvironmentOverrides:
    """Raw optional machine-local configuration values.

    ``project_root`` is retained as a legacy validation-profile input. New
    startup flows use ``selected_language_path`` and may supply an explicit
    ``validation_profile_path`` independently.
    """

    project_root: str | None = None
    gf_executable: str | None = None
    rgl_root: str | None = None
    output_root: str | None = None
    state_path: str | None = None
    selected_language_path: str | None = None
    validation_profile_path: str | None = None
    rgl_source_root: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "project_root",
            "gf_executable",
            "rgl_root",
            "output_root",
            "state_path",
            "selected_language_path",
            "validation_profile_path",
            "rgl_source_root",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_optional_raw_text(
                    name,
                    getattr(self, name),
                ),
            )


@dataclass(frozen=True, slots=True)
class SelectionDefaults:
    """Language-neutral defaults for one validation selection."""

    mode: ValidationMode
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.mode,
            ValidationMode,
        ):
            raise TypeError(
                "mode must be a ValidationMode"
            )

        _require_plain_int(
            "timeout_sec",
            self.timeout_sec,
            minimum=1,
        )
        _require_plain_int(
            "max_files",
            self.max_files,
            minimum=0,
        )
        _require_bool(
            "keep_ok_details",
            self.keep_ok_details,
        )
        _require_bool(
            "diff_previous",
            self.diff_previous,
        )
        _require_bool(
            "skip_version_probe",
            self.skip_version_probe,
        )
        _require_bool(
            "no_compile",
            self.no_compile,
        )
        _require_bool(
            "emit_cpu_stats",
            self.emit_cpu_stats,
        )


@dataclass(frozen=True, slots=True)
class OutputDefaults:
    """Language-neutral defaults for evidence and report production."""

    evidence_level: EvidenceLevel
    generate_manifest: bool
    generate_ai_ready: bool
    aggregate_logs: bool

    def __post_init__(self) -> None:
        _require_evidence_level(
            self.evidence_level
        )
        _require_bool(
            "generate_manifest",
            self.generate_manifest,
        )
        _require_bool(
            "generate_ai_ready",
            self.generate_ai_ready,
        )
        _require_bool(
            "aggregate_logs",
            self.aggregate_logs,
        )


@dataclass(frozen=True, slots=True)
class SchemaSupport:
    """Persisted-schema major versions supported by this application."""

    project_major: int
    app_state_major: int
    run_summary_major: int
    artifact_manifest_major: int
    validation_profile_major: int | None = None

    def __post_init__(self) -> None:
        _require_plain_int(
            "project_major",
            self.project_major,
            minimum=1,
        )
        profile_major = self.validation_profile_major
        if profile_major is None:
            profile_major = self.project_major
        _require_plain_int(
            "validation_profile_major",
            profile_major,
            minimum=1,
        )
        object.__setattr__(
            self,
            "validation_profile_major",
            profile_major,
        )
        _require_plain_int(
            "app_state_major",
            self.app_state_major,
            minimum=1,
        )
        _require_plain_int(
            "run_summary_major",
            self.run_summary_major,
            minimum=1,
        )
        _require_plain_int(
            "artifact_manifest_major",
            self.artifact_manifest_major,
            minimum=1,
        )


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Framework defaults and schema-support policy."""

    producer: ProducerInfo
    selection_defaults: SelectionDefaults
    output_defaults: OutputDefaults
    schema_support: SchemaSupport
    state_filename: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.producer,
            ProducerInfo,
        ):
            raise TypeError(
                "producer must be a ProducerInfo"
            )
        if not isinstance(
            self.selection_defaults,
            SelectionDefaults,
        ):
            raise TypeError(
                "selection_defaults must be "
                "SelectionDefaults"
            )
        if not isinstance(
            self.output_defaults,
            OutputDefaults,
        ):
            raise TypeError(
                "output_defaults must be OutputDefaults"
            )
        if not isinstance(
            self.schema_support,
            SchemaSupport,
        ):
            raise TypeError(
                "schema_support must be SchemaSupport"
            )

        _require_non_empty_text(
            "state_filename",
            self.state_filename,
        )

        if self.state_filename in {".", ".."}:
            raise ValueError(
                "state_filename must name a file"
            )
        if (
            "/" in self.state_filename
            or "\\" in self.state_filename
        ):
            raise ValueError(
                "state_filename must not contain "
                "path separators"
            )


@dataclass(frozen=True, slots=True)
class ValidationTarget:
    """Typed identity of a requested validation target."""

    kind: TargetKind
    value: str | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.kind,
            TargetKind,
        ):
            raise TypeError(
                "kind must be a TargetKind"
            )

        if self.value is None:
            if self.kind is not TargetKind.PROJECT:
                raise ValueError(
                    "only a project target may omit value"
                )
            return

        _require_non_empty_text(
            "value",
            self.value,
        )

        if self.value != self.value.strip():
            raise ValueError(
                "value must not contain "
                "surrounding whitespace"
            )


@dataclass(frozen=True, slots=True)
class ResolvedEnvironment:
    """Validated machine-local paths used by one run.

    ``project_root`` is a compatibility field for an optional legacy
    validation profile. ``language_directory`` and ``rgl_source_root`` are the
    canonical source-context paths for path-resolved startup.
    """

    project_root: Path | None
    rgl_root: Path
    gf_executable: Path
    output_root: Path
    gf_path: tuple[Path, ...]
    language_directory: Path | None = None
    rgl_source_root: Path | None = None
    validation_profile_root: Path | None = None

    def __post_init__(self) -> None:
        project_root = self.project_root
        if project_root is not None:
            _require_absolute_normalized_path(
                "project_root",
                project_root,
            )

        _require_absolute_normalized_path(
            "rgl_root",
            self.rgl_root,
        )
        _require_absolute_normalized_path(
            "gf_executable",
            self.gf_executable,
        )
        _require_absolute_normalized_path(
            "output_root",
            self.output_root,
        )
        _require_unique_paths(
            "gf_path",
            self.gf_path,
        )

        language_directory = self.language_directory
        if language_directory is None:
            language_directory = project_root
        if language_directory is None:
            raise ValueError(
                "language_directory is required when project_root is absent"
            )
        _require_absolute_normalized_path(
            "language_directory",
            language_directory,
        )

        rgl_source_root = self.rgl_source_root
        if rgl_source_root is None:
            rgl_source_root = Path(
                os.path.normpath(
                    os.fspath(self.rgl_root / "src")
                )
            )
        _require_absolute_normalized_path(
            "rgl_source_root",
            rgl_source_root,
        )
        _require_contained_path(
            "rgl_source_root",
            rgl_source_root,
            parent=self.rgl_root,
        )
        _require_contained_path(
            "language_directory",
            language_directory,
            parent=rgl_source_root,
        )

        profile_root = self.validation_profile_root
        if profile_root is None:
            profile_root = project_root
        if profile_root is not None:
            _require_absolute_normalized_path(
                "validation_profile_root",
                profile_root,
            )

        object.__setattr__(
            self,
            "language_directory",
            language_directory,
        )
        object.__setattr__(
            self,
            "rgl_source_root",
            rgl_source_root,
        )
        object.__setattr__(
            self,
            "validation_profile_root",
            profile_root,
        )


@dataclass(frozen=True, slots=True)
class ConfigurationIssue:
    """One structured configuration or language-resolution finding."""

    severity: IssueSeverity
    source: ConfigurationSource
    field_path: str
    provided_value: object
    message: str
    remediation: str
    stage: str = "configuration"
    error_kind: str = "configuration"
    technical_detail: str = ""
    relevant_path: Path | None = None
    candidate_choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.severity,
            IssueSeverity,
        ):
            raise TypeError(
                "severity must be an IssueSeverity"
            )

        _require_configuration_source(
            "source",
            self.source,
        )
        _require_field_path(
            "field_path",
            self.field_path,
        )
        _require_non_empty_text(
            "message",
            self.message,
        )
        _require_non_empty_text(
            "remediation",
            self.remediation,
        )
        _require_non_empty_text(
            "stage",
            self.stage,
        )
        _require_non_empty_text(
            "error_kind",
            self.error_kind,
        )
        if not isinstance(self.technical_detail, str):
            raise TypeError(
                "technical_detail must be a string"
            )
        if "\x00" in self.technical_detail:
            raise ValueError(
                "technical_detail must not contain a NUL character"
            )
        if self.relevant_path is not None:
            _require_absolute_normalized_path(
                "relevant_path",
                self.relevant_path,
            )
        _require_unique_non_empty_texts(
            "candidate_choices",
            self.candidate_choices,
        )


@dataclass(frozen=True, slots=True)
class ConfigurationProvenance:
    """Winning source and value transformation for one effective field."""

    field_path: str
    source: ConfigurationSource
    provided_value: object = None
    resolved_value: object = None

    def __post_init__(self) -> None:
        _require_field_path(
            "field_path",
            self.field_path,
        )
        _require_configuration_source(
            "source",
            self.source,
        )


@dataclass(frozen=True, slots=True)
class ConfigurationResolutionRequest:
    """Complete immutable input to run-configuration resolution.

    ``language_context`` is the canonical source authority for path-resolved
    startup. ``project`` is retained as an optional legacy validation profile.
    At least one of them must be supplied during the compatibility period.
    """

    defaults: AppConfig
    project: ProjectConfig | None
    environment: EnvironmentOverrides = field(
        default_factory=EnvironmentOverrides
    )
    source_values: Mapping[
        ConfigurationSource,
        Mapping[str, object],
    ] = field(default_factory=dict)
    language_context: ResolvedLanguageContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.defaults,
            AppConfig,
        ):
            raise TypeError(
                "defaults must be an AppConfig"
            )
        if (
            self.project is not None
            and not isinstance(
                self.project,
                ProjectConfig,
            )
        ):
            raise TypeError(
                "project must be a ProjectConfig or None"
            )
        if self.language_context is not None:
            _require_resolved_language_context(
                "language_context",
                self.language_context,
            )
        if self.project is None and self.language_context is None:
            raise ValueError(
                "language_context is required when no legacy project "
                "profile is supplied"
            )
        if not isinstance(
            self.environment,
            EnvironmentOverrides,
        ):
            raise TypeError(
                "environment must be "
                "an EnvironmentOverrides"
            )

        if self.project is not None and self.language_context is not None:
            if self.project.source_root != self.language_context.language_directory:
                raise ValueError(
                    "the validation profile source_root must equal the "
                    "resolved language_directory"
                )

        object.__setattr__(
            self,
            "source_values",
            _freeze_source_values(
                self.source_values
            ),
        )

    @property
    def validation_profile(self) -> ProjectConfig | None:
        """Return the optional legacy validation profile."""

        return self.project


@dataclass(frozen=True, slots=True)
class EnvironmentResolution:
    """Result of resolving machine-local runtime paths."""

    value: ResolvedEnvironment | None
    issues: tuple[
        ConfigurationIssue,
        ...,
    ] = ()
    provenance: tuple[
        ConfigurationProvenance,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        if (
            self.value is not None
            and not isinstance(
                self.value,
                ResolvedEnvironment,
            )
        ):
            raise TypeError(
                "value must be a "
                "ResolvedEnvironment or None"
            )

        _validate_issues(
            "issues",
            self.issues,
        )
        _validate_provenance(
            "provenance",
            self.provenance,
        )

        if (
            self.value is not None
            and _has_error(self.issues)
        ):
            raise ValueError(
                "an environment with error issues "
                "must not expose a value"
            )

    @property
    def succeeded(self) -> bool:
        """Whether resolution produced a usable environment."""

        return (
            self.value is not None
            and not _has_error(self.issues)
        )


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Fully resolved immutable configuration for one run.

    ``language_context`` owns active-language and source facts. ``project`` is
    an optional validation profile retained for compatibility with the current
    project schema.
    """

    project: ProjectConfig | None
    environment: ResolvedEnvironment
    mode: ValidationMode
    target: ValidationTarget | None
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool
    selected_checkpoints: tuple[Path, ...]
    selected_entrypoints: tuple[Path, ...]
    selected_scenarios: tuple[str, ...]
    release_requires_pgf: bool
    evidence_level: EvidenceLevel
    compatibility_warnings: tuple[str, ...] = ()
    language_context: ResolvedLanguageContext | None = None
    effective_capabilities: tuple[LanguageCapability, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.project is not None
            and not isinstance(
                self.project,
                ProjectConfig,
            )
        ):
            raise TypeError(
                "project must be a ProjectConfig or None"
            )
        if self.language_context is not None:
            _require_resolved_language_context(
                "language_context",
                self.language_context,
            )
        if self.project is None and self.language_context is None:
            raise ValueError(
                "a run requires a resolved language context or a "
                "legacy project profile"
            )
        if not isinstance(
            self.environment,
            ResolvedEnvironment,
        ):
            raise TypeError(
                "environment must be "
                "a ResolvedEnvironment"
            )
        if not isinstance(
            self.mode,
            ValidationMode,
        ):
            raise TypeError(
                "mode must be a ValidationMode"
            )
        if (
            self.target is not None
            and not isinstance(
                self.target,
                ValidationTarget,
            )
        ):
            raise TypeError(
                "target must be "
                "a ValidationTarget or None"
            )

        _require_plain_int(
            "timeout_sec",
            self.timeout_sec,
            minimum=1,
        )
        _require_plain_int(
            "max_files",
            self.max_files,
            minimum=0,
        )
        _require_bool(
            "keep_ok_details",
            self.keep_ok_details,
        )
        _require_bool(
            "diff_previous",
            self.diff_previous,
        )
        _require_bool(
            "skip_version_probe",
            self.skip_version_probe,
        )
        _require_bool(
            "no_compile",
            self.no_compile,
        )
        _require_bool(
            "emit_cpu_stats",
            self.emit_cpu_stats,
        )
        _require_bool(
            "release_requires_pgf",
            self.release_requires_pgf,
        )
        _require_evidence_level(
            self.evidence_level
        )

        _require_unique_paths(
            "selected_checkpoints",
            self.selected_checkpoints,
        )
        _require_unique_paths(
            "selected_entrypoints",
            self.selected_entrypoints,
        )
        _require_unique_non_empty_texts(
            "selected_scenarios",
            self.selected_scenarios,
        )
        _require_unique_non_empty_texts(
            "compatibility_warnings",
            self.compatibility_warnings,
        )
        _require_unique_capabilities(
            "effective_capabilities",
            self.effective_capabilities,
        )

        context = self.language_context
        if context is not None:
            if self.environment.language_directory != context.language_directory:
                raise ValueError(
                    "environment.language_directory must equal the "
                    "resolved language_directory"
                )
            if self.environment.rgl_source_root != context.rgl_source_root:
                raise ValueError(
                    "environment.rgl_source_root must equal the resolved "
                    "rgl_source_root"
                )
            _require_paths_contained(
                "selected_checkpoints",
                self.selected_checkpoints,
                parent=context.language_directory,
            )
            _require_paths_contained(
                "selected_entrypoints",
                self.selected_entrypoints,
                parent=context.language_directory,
            )
            if self.project is not None:
                if self.project.source_root != context.language_directory:
                    raise ValueError(
                        "the validation profile source_root must equal the "
                        "resolved language_directory"
                    )

        if (
            self.mode is ValidationMode.QUICK
            and self.target is None
        ):
            raise ValueError(
                "quick mode requires a resolved target"
            )

        if self.mode is ValidationMode.CHECKPOINT:
            if self.project is None:
                raise ValueError(
                    "checkpoint mode requires an explicit validation profile"
                )
            if not self.selected_checkpoints:
                raise ValueError(
                    "checkpoint mode requires at least one checkpoint"
                )

        if self.mode is ValidationMode.RELEASE:
            if self.project is None:
                raise ValueError(
                    "release mode requires an explicit validation profile"
                )
            if not self.selected_entrypoints:
                raise ValueError(
                    "release mode requires at least one entrypoint"
                )

        if self.release_requires_pgf and self.project is None:
            raise ValueError(
                "release_requires_pgf requires an explicit validation profile"
            )

    @property
    def validation_profile(self) -> ProjectConfig | None:
        """Return the optional validation profile."""

        return self.project

    @property
    def language_key(self) -> str:
        """Return the portable language key used by this run."""

        if self.language_context is not None:
            return self.language_context.language_key
        assert self.project is not None
        return str(self.project.identity.language_code)

    @property
    def source_root(self) -> Path:
        """Return the effective language source directory."""

        if self.language_context is not None:
            return self.language_context.language_directory
        assert self.project is not None
        return self.project.source_root


@dataclass(frozen=True, slots=True)
class ConfigurationResolution:
    """Final configuration result with issues and provenance."""

    configuration: RunConfig | None
    issues: tuple[
        ConfigurationIssue,
        ...,
    ] = ()
    provenance: tuple[
        ConfigurationProvenance,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        if (
            self.configuration is not None
            and not isinstance(
                self.configuration,
                RunConfig,
            )
        ):
            raise TypeError(
                "configuration must be "
                "a RunConfig or None"
            )

        _validate_issues(
            "issues",
            self.issues,
        )
        _validate_provenance(
            "provenance",
            self.provenance,
        )

        if (
            self.configuration is not None
            and _has_error(self.issues)
        ):
            raise ValueError(
                "a resolution with error issues "
                "must not expose a configuration"
            )

    @property
    def succeeded(self) -> bool:
        """Whether resolution produced a usable configuration."""

        return (
            self.configuration is not None
            and not _has_error(self.issues)
        )

    def require(self) -> RunConfig:
        """Return the configuration or raise ConfigurationError."""

        if self.succeeded:
            assert self.configuration is not None
            return self.configuration

        errors = tuple(
            issue
            for issue in self.issues
            if issue.severity is IssueSeverity.ERROR
        )
        relevant = errors or self.issues

        detail = "\n".join(
            (
                f"{issue.field_path}: {issue.message} "
                f"Remediation: {issue.remediation}"
            )
            for issue in relevant
        )
        subject = (
            relevant[0].field_path
            if relevant
            else None
        )

        raise ConfigurationError(
            "Configuration resolution failed.",
            code="GF-WB-CONFIG-001",
            detail=detail,
            stage="configuration",
            operation="resolve",
            subject=subject,
        )


__all__ = (
    "AppConfig",
    "ConfigurationIssue",
    "ConfigurationProvenance",
    "ConfigurationResolution",
    "ConfigurationResolutionRequest",
    "EnvironmentOverrides",
    "EnvironmentResolution",
    "EvidenceLevel",
    "IssueSeverity",
    "LanguageCapability",
    "OutputDefaults",
    "ResolvedEnvironment",
    "RunConfig",
    "SchemaSupport",
    "SelectionDefaults",
    "ValidationTarget",
)
