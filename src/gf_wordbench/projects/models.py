"""Immutable active-project configuration models for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PureWindowsPath
import re
from typing import Final

from gf_wordbench.kernel.ids import (
    ProjectId,
    ScenarioId,
    SchemaId,
    validate_project_id,
    validate_scenario_id,
    validate_schema_id,
)

PROJECT_SCHEMA_ID: Final[SchemaId] = validate_schema_id("gf-wordbench.project")
PROJECT_SCHEMA_VERSION: Final[str] = "1.0"
PROJECT_CONFIG_FILENAME: Final[str] = "project.toml"


@unique
class ProjectCheckScope(StrEnum):
    """Depth of a read-only active-project validation."""

    CONFIGURATION = "configuration"
    NORMAL = "normal"
    RELEASE = "release"


@unique
class ProjectDiagnosticSeverity(StrEnum):
    """Severity assigned to one project-validation diagnostic."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """Stable identity declared by the active project's ``[project]`` table."""

    id: ProjectId
    name: str
    language_code: str
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", validate_project_id(self.id))
        _require_non_empty_text(
            self.name,
            field="project.name",
            allow_unicode=True,
        )
        _require_language_code(self.language_code)
        object.__setattr__(
            self,
            "root",
            _require_relative_path(
                self.root,
                field="project.root",
                allow_dot=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class SourceConfig:
    """Portable source-discovery policy declared by ``[sources]``."""

    directory: Path
    glob: str
    include_regex: str
    exclude_regex: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "directory",
            _require_relative_path(
                self.directory,
                field="sources.directory",
                allow_dot=False,
            ),
        )
        _require_non_empty_text(self.glob, field="sources.glob")
        _reject_absolute_pattern(self.glob, field="sources.glob")
        _compile_regex(self.include_regex, field="sources.include_regex")
        _compile_regex(self.exclude_regex, field="sources.exclude_regex")


@dataclass(frozen=True, slots=True)
class GFProjectConfig:
    """Project-owned GF search-path requirements and optional version floor."""

    path_parts: tuple[str, ...]
    minimum_version: str

    def __post_init__(self) -> None:
        raw_parts = _require_tuple(self.path_parts, field="gf.path_parts")
        path_parts = tuple(
            _require_path_part(part, field=f"gf.path_parts[{index}]")
            for index, part in enumerate(raw_parts)
        )
        _require_single_line_text(
            self.minimum_version,
            field="gf.minimum_version",
            allow_empty=True,
        )
        object.__setattr__(self, "path_parts", path_parts)


@dataclass(frozen=True, slots=True)
class ModuleTargets:
    """Ordered source-root-relative entrypoints and checkpoints."""

    entrypoints: tuple[Path, ...]
    checkpoints: tuple[Path, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entrypoints",
            _validate_module_paths(
                self.entrypoints,
                field="modules.entrypoints",
            ),
        )
        object.__setattr__(
            self,
            "checkpoints",
            _validate_module_paths(
                self.checkpoints,
                field="modules.checkpoints",
            ),
        )


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    """Project-owned scenario membership and PGF release policy."""

    required_scenarios: tuple[ScenarioId, ...]
    optional_scenarios: tuple[ScenarioId, ...]
    release_requires_pgf: bool

    def __post_init__(self) -> None:
        required = _validate_scenario_ids(
            self.required_scenarios,
            field="validation.required_scenarios",
        )
        optional = _validate_scenario_ids(
            self.optional_scenarios,
            field="validation.optional_scenarios",
        )

        overlap = set(required).intersection(optional)
        if overlap:
            duplicated = ", ".join(sorted(overlap))
            raise ValueError(f"Scenario IDs cannot be both required and optional: {duplicated}.")

        if not isinstance(self.release_requires_pgf, bool):
            raise TypeError("validation.release_requires_pgf must be a boolean.")

        object.__setattr__(self, "required_scenarios", required)
        object.__setattr__(self, "optional_scenarios", optional)

    @property
    def all_scenarios(self) -> tuple[ScenarioId, ...]:
        """Return the ordered required-then-optional scenario registry."""

        return self.required_scenarios + self.optional_scenarios


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Fully loaded configuration for exactly one active project."""

    schema_id: SchemaId
    schema_version: str
    identity: ProjectIdentity
    sources: SourceConfig
    gf: GFProjectConfig
    modules: ModuleTargets
    validation: ValidationPolicy
    project_file: Path
    project_root: Path
    source_root: Path

    def __post_init__(self) -> None:
        schema_id = validate_schema_id(self.schema_id)
        if schema_id != PROJECT_SCHEMA_ID:
            raise ValueError(
                f"Unsupported project schema ID {schema_id!r}; expected {PROJECT_SCHEMA_ID!r}."
            )

        _require_exact_text(
            self.schema_version,
            field="schema_version",
            expected=PROJECT_SCHEMA_VERSION,
        )
        _require_instance(self.identity, ProjectIdentity, field="identity")
        _require_instance(self.sources, SourceConfig, field="sources")
        _require_instance(self.gf, GFProjectConfig, field="gf")
        _require_instance(self.modules, ModuleTargets, field="modules")
        _require_instance(
            self.validation,
            ValidationPolicy,
            field="validation",
        )

        project_file = _require_absolute_path(
            self.project_file,
            field="project_file",
        )
        project_root = _require_absolute_path(
            self.project_root,
            field="project_root",
        )
        source_root = _require_absolute_path(
            self.source_root,
            field="source_root",
        )

        expected_project_file = project_root / PROJECT_CONFIG_FILENAME
        if project_file != expected_project_file:
            raise ValueError(
                f"project_file must be exactly project_root/project.toml; got {project_file!s}."
            )

        expected_source_root = _lexically_normalize(project_root / self.sources.directory)
        if source_root != expected_source_root:
            raise ValueError(
                "source_root must equal project_root / sources.directory; "
                f"expected {expected_source_root!s}, got {source_root!s}."
            )

        _require_contained(
            source_root,
            parent=project_root,
            field="source_root",
        )

        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(self, "project_file", project_file)
        object.__setattr__(self, "project_root", project_root)
        object.__setattr__(self, "source_root", source_root)

    @property
    def project_id(self) -> ProjectId:
        """Return the stable active-project identifier."""

        return self.identity.id


@dataclass(frozen=True, slots=True)
class ProjectDiagnostic:
    """One structured finding produced by active-project validation."""

    code: str
    severity: ProjectDiagnosticSeverity
    field: str
    message: str
    source_file: Path
    suggestion: str
    subject: Path | None = None

    def __post_init__(self) -> None:
        _require_non_empty_text(self.code, field="diagnostic.code")
        _require_instance(
            self.severity,
            ProjectDiagnosticSeverity,
            field="diagnostic.severity",
        )
        _require_non_empty_text(
            self.field,
            field="diagnostic.field",
            allow_unicode=True,
        )
        _require_non_empty_text(
            self.message,
            field="diagnostic.message",
            allow_unicode=True,
        )
        _require_non_empty_text(
            self.suggestion,
            field="diagnostic.suggestion",
            allow_unicode=True,
        )

        source_file = _require_absolute_path(
            self.source_file,
            field="diagnostic.source_file",
        )

        subject = self.subject
        if subject is not None:
            subject = _require_absolute_path(
                subject,
                field="diagnostic.subject",
            )

        object.__setattr__(self, "source_file", source_file)
        object.__setattr__(self, "subject", subject)


@dataclass(frozen=True, slots=True)
class ProjectValidationResult:
    """Aggregate diagnostics from one read-only active-project validation."""

    diagnostics: tuple[ProjectDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        diagnostics = _require_tuple(
            self.diagnostics,
            field="diagnostics",
        )
        for index, diagnostic in enumerate(diagnostics):
            _require_instance(
                diagnostic,
                ProjectDiagnostic,
                field=f"diagnostics[{index}]",
            )

        object.__setattr__(self, "diagnostics", tuple(diagnostics))

    @property
    def errors(self) -> tuple[ProjectDiagnostic, ...]:
        """Return error-severity diagnostics in original order."""

        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.severity is ProjectDiagnosticSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ProjectDiagnostic, ...]:
        """Return warning-severity diagnostics in original order."""

        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.severity is ProjectDiagnosticSeverity.WARNING
        )

    @property
    def ok(self) -> bool:
        """Whether validation produced no error-severity diagnostic."""

        return not any(
            diagnostic.severity is ProjectDiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )


def _require_instance(
    value: object,
    expected: type[object],
    *,
    field: str,
) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be {expected.__name__}, got {type(value).__name__}.")


def _require_tuple(value: object, *, field: str) -> tuple[object, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple, got {type(value).__name__}.")
    return value


def _require_non_empty_text(
    value: object,
    *,
    field: str,
    allow_unicode: bool = False,
) -> str:
    text = _require_single_line_text(
        value,
        field=field,
        allow_empty=False,
    )
    if not allow_unicode and not text.isascii():
        raise ValueError(f"{field} must use ASCII characters only.")
    return text


def _require_single_line_text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string, got {type(value).__name__}.")
    if not allow_empty and not value:
        raise ValueError(f"{field} must not be empty.")
    if value != value.strip():
        raise ValueError(f"{field} must not contain leading or trailing whitespace.")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be a single-line string without NUL bytes.")
    return value


def _require_exact_text(
    value: object,
    *,
    field: str,
    expected: str,
) -> str:
    text = _require_single_line_text(
        value,
        field=field,
        allow_empty=False,
    )
    if text != expected:
        raise ValueError(f"Unsupported {field} {text!r}; expected {expected!r}.")
    return text


def _require_language_code(value: object) -> str:
    code = _require_non_empty_text(
        value,
        field="project.language_code",
        allow_unicode=False,
    )
    if "/" in code or "\\" in code:
        raise ValueError("project.language_code must not contain a path separator.")
    return code


def _require_relative_path(
    value: object,
    *,
    field: str,
    allow_dot: bool,
) -> Path:
    """Validate and normalize one runtime-native relative path.

    Persisted path strings are validated by ``schema.py`` before conversion.
    Once a value is a ``Path``, its original separator spelling is no longer
    portable information: Windows renders native paths with ``\\`` while
    ``Path.as_posix()`` renders the same path with ``/``.

    Parse the runtime value with Windows-aware path semantics to detect drives,
    rooted paths, UNC paths, and traversal consistently on every host. Return
    a native ``Path`` assembled from the validated relative components.
    """

    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path, got {type(value).__name__}.")

    text = value.as_posix()
    if not text or "\x00" in text:
        raise ValueError(f"{field} must not be empty or contain NUL bytes.")

    portable = PureWindowsPath(text)
    if value.is_absolute() or portable.is_absolute() or bool(portable.drive) or bool(portable.root):
        raise ValueError(f"{field} must be project-relative, got {text!r}.")

    parts = portable.parts
    if any(part == ".." for part in parts):
        raise ValueError(f"{field} must not contain parent traversal ('..').")

    normalized = Path(*parts) if parts else Path(".")
    if not allow_dot and normalized == Path("."):
        raise ValueError(f"{field} must identify a non-root relative path.")
    return normalized


def _require_absolute_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path, got {type(value).__name__}.")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL bytes.")
    if not value.is_absolute():
        raise ValueError(f"{field} must be an absolute runtime path.")

    normalized = _lexically_normalize(value)
    if any(part == ".." for part in normalized.parts):
        raise ValueError(f"{field} must not contain unresolved parent traversal.")
    return normalized


def _lexically_normalize(path: Path) -> Path:
    return Path(*path.parts)


def _require_contained(
    path: Path,
    *,
    parent: Path,
    field: str,
) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise ValueError(f"{field} must remain inside project_root.") from exc


def _reject_absolute_pattern(value: str, *, field: str) -> None:
    windows_path = PureWindowsPath(value)
    if value.startswith(("/", "\\")) or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"{field} must not contain an absolute path pattern.")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL bytes.")


def _compile_regex(
    value: object,
    *,
    field: str,
) -> re.Pattern[str] | None:
    text = _require_single_line_text(
        value,
        field=field,
        allow_empty=True,
    )
    if not text:
        return None

    try:
        return re.compile(text)
    except re.error as exc:
        raise ValueError(f"Invalid {field} regular expression: {exc}.") from exc


def _require_path_part(value: object, *, field: str) -> str:
    text = _require_non_empty_text(value, field=field)
    if "\\" in text:
        raise ValueError(f"{field} must use canonical '/' separators.")

    windows_path = PureWindowsPath(text)
    path = Path(text)
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"{field} must not contain a machine-local absolute path.")
    if "$" in text or "%" in text:
        raise ValueError(f"{field} must not embed environment-variable syntax.")
    if any(part == ".." for part in path.parts):
        raise ValueError(f"{field} must not contain parent traversal ('..').")
    return text


def _validate_module_paths(
    values: object,
    *,
    field: str,
) -> tuple[Path, ...]:
    raw = _require_tuple(values, field=field)
    seen: set[str] = set()
    validated: list[Path] = []

    for index, value in enumerate(raw):
        item_field = f"{field}[{index}]"
        path = _require_relative_path(
            value,
            field=item_field,
            allow_dot=False,
        )
        if path.suffix != ".gf":
            raise ValueError(f"{item_field} must end in '.gf'.")

        key = path.as_posix()
        if key in seen:
            raise ValueError(f"{field} contains duplicate path {key!r}.")

        seen.add(key)
        validated.append(path)

    return tuple(validated)


def _validate_scenario_ids(
    values: object,
    *,
    field: str,
) -> tuple[ScenarioId, ...]:
    raw = _require_tuple(values, field=field)
    seen: set[ScenarioId] = set()
    validated: list[ScenarioId] = []

    for index, value in enumerate(raw):
        scenario_id = validate_scenario_id(
            value,
            field=f"{field}[{index}]",
        )
        if scenario_id in seen:
            raise ValueError(f"{field} contains duplicate scenario ID {scenario_id!r}.")

        seen.add(scenario_id)
        validated.append(scenario_id)

    return tuple(validated)


__all__ = (
    "PROJECT_CONFIG_FILENAME",
    "PROJECT_SCHEMA_ID",
    "PROJECT_SCHEMA_VERSION",
    "GFProjectConfig",
    "ModuleTargets",
    "ProjectCheckScope",
    "ProjectConfig",
    "ProjectDiagnostic",
    "ProjectDiagnosticSeverity",
    "ProjectIdentity",
    "ProjectValidationResult",
    "SourceConfig",
    "ValidationPolicy",
)
