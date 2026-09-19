"""Pure policy checks for active-project configuration.

This module validates portable project declarations and cross-field invariants.
It performs no filesystem access, environment resolution, schema migration, or
project mutation.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fnmatch import translate as translate_glob
from pathlib import Path, PureWindowsPath
import re
from typing import Final, TypeAlias

from gf_wordbench.kernel.errors import ProjectConfigurationError

from .models import ProjectConfig, ProjectDiagnostic, ProjectDiagnosticSeverity

PolicyCheck: TypeAlias = tuple[str, str, str, Callable[[], object]]

_PROJECT_ID_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_RECOMMENDED_PROJECT_ID_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_LANGUAGE_CODE_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_RECOMMENDED_SCENARIO_ID_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_TEMPLATE_PLACEHOLDER_PATTERN: Final = re.compile(r"<[^<>\r\n]+>")
_ENVIRONMENT_REFERENCE_PATTERN: Final = re.compile(
    r"(?:\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*|%[^%]+%)"
)
_WINDOWS_RESERVED_NAMES: Final = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)
_WINDOWS_FORBIDDEN_PATH_CHARACTERS: Final = frozenset('<>:"|?*')
_MAX_INVARIANT_ERROR_DETAILS: Final[int] = 8

REQUIRED_PROJECT_ASSETS: Final[tuple[Path, ...]] = tuple(
    Path(value)
    for value in (
        "README.md",
        "docs/00_PROJECT_START_HERE__PROJECT_DOCS.md",
        "docs/CATEGORY_AND_LINCAT_CONTRACT.md",
        "docs/DECISION_LOG.md",
        "docs/INTERFILE_CONTRACT_LOCK.md",
        "docs/KNOWN_ISSUES.md",
        "docs/LANGUAGE_ARCHITECTURE.md",
        "docs/LANGUAGE_OVERVIEW.md",
        "docs/MODULE_DEPENDENCY_MAP.md",
        "docs/MORPHOLOGY_SPEC.md",
        "docs/RELEASE_CRITERIA__PROJECT_DOCS.md",
        "docs/RESEARCH_EVIDENCE.md",
        "docs/STATUS_LEDGER__PROJECT_DOCS.md",
        "docs/SYNTAX_AND_CONSTRUCTOR_RULES.md",
        "docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md",
        "docs/VALIDATION_SPEC__PROJECT_DOCS.md",
        "validation/README.md",
        "validation/gold/README.md",
        "validation/inputs/README.md",
        "validation/scenarios/README.md",
    )
)

__all__ = (
    "REQUIRED_PROJECT_ASSETS",
    "contains_template_placeholder",
    "deduplicate_declared_path_parts",
    "enforce_project_invariants",
    "find_unresolved_placeholder",
    "is_recommended_project_id",
    "is_recommended_scenario_id",
    "normalized_portable_path_key",
    "validate_language_code",
    "validate_minimum_version",
    "validate_module_targets",
    "validate_optional_regex",
    "validate_portable_project_path",
    "validate_project_id",
    "validate_project_name",
    "validate_project_root",
    "validate_project_semantics",
    "validate_release_requires_pgf",
    "validate_scenario_id",
    "validate_scenario_policy",
    "validate_source_glob",
)


def contains_template_placeholder(value: str) -> bool:
    """Return whether *value* contains an unresolved ``<placeholder>``."""

    return find_unresolved_placeholder(value) is not None


def find_unresolved_placeholder(value: str) -> str | None:
    """Return the first unresolved ``<placeholder>`` or ``None``."""

    if not isinstance(value, str):
        raise TypeError("value must be a string")

    match = _TEMPLATE_PLACEHOLDER_PATTERN.search(value)
    return match.group(0) if match else None


def validate_project_semantics(
    project: ProjectConfig,
    *,
    strict: bool = False,
) -> tuple[ProjectDiagnostic, ...]:
    """Return structured diagnostics for pure project invariants."""

    if not isinstance(project, ProjectConfig):
        raise TypeError("project must be a ProjectConfig")
    if type(strict) is not bool:
        raise TypeError("strict must be a bool")

    checks: tuple[PolicyCheck, ...] = (
        (
            "PROJECT_ID_INVALID",
            "project.id",
            "Use a portable ASCII project identifier.",
            lambda: validate_project_id(str(project.identity.id)),
        ),
        (
            "PROJECT_NAME_INVALID",
            "project.name",
            "Provide a non-empty reviewed project name.",
            lambda: validate_project_name(project.identity.name),
        ),
        (
            "PROJECT_LANGUAGE_CODE_INVALID",
            "project.language_code",
            "Use a stable portable language identifier.",
            lambda: validate_language_code(project.identity.language_code),
        ),
        (
            "PROJECT_ROOT_INVALID",
            "project.root",
            "Set project.root to '.' for schema 1.0.",
            lambda: validate_project_root(project.identity.root.as_posix()),
        ),
        (
            "PROJECT_SOURCE_DIRECTORY_INVALID",
            "sources.directory",
            "Use a canonical project-relative source directory.",
            lambda: validate_portable_project_path(
                project.sources.directory.as_posix(),
                field="sources.directory",
            ),
        ),
        (
            "PROJECT_SOURCE_GLOB_INVALID",
            "sources.glob",
            "Use a filename glob without path separators.",
            lambda: validate_source_glob(project.sources.glob),
        ),
        (
            "PROJECT_INCLUDE_REGEX_INVALID",
            "sources.include_regex",
            "Provide a valid regular expression or an empty string.",
            lambda: validate_optional_regex(
                project.sources.include_regex,
                field="sources.include_regex",
            ),
        ),
        (
            "PROJECT_EXCLUDE_REGEX_INVALID",
            "sources.exclude_regex",
            "Provide a valid regular expression or an empty string.",
            lambda: validate_optional_regex(
                project.sources.exclude_regex,
                field="sources.exclude_regex",
            ),
        ),
        (
            "PROJECT_GF_PATH_INVALID",
            "gf.path_parts",
            "Use unique portable GF path parts.",
            lambda: _validate_gf_path_parts(project.gf.path_parts),
        ),
        (
            "PROJECT_GF_MINIMUM_VERSION_INVALID",
            "gf.minimum_version",
            "Use a portable version token or an empty string.",
            lambda: validate_minimum_version(project.gf.minimum_version),
        ),
        (
            "PROJECT_MODULE_TARGETS_INVALID",
            "modules",
            "Declare unique '.gf' targets and at least one entrypoint.",
            lambda: validate_module_targets(
                tuple(path.as_posix() for path in project.modules.entrypoints),
                tuple(path.as_posix() for path in project.modules.checkpoints),
            ),
        ),
        (
            "PROJECT_SCENARIO_POLICY_INVALID",
            "validation",
            "Use unique, disjoint required and optional scenario registries.",
            lambda: validate_scenario_policy(
                tuple(map(str, project.validation.required_scenarios)),
                tuple(map(str, project.validation.optional_scenarios)),
            ),
        ),
        (
            "PROJECT_RELEASE_POLICY_INVALID",
            "validation.release_requires_pgf",
            "Set release_requires_pgf to an explicit boolean.",
            lambda: validate_release_requires_pgf(project.validation.release_requires_pgf),
        ),
        (
            "PROJECT_PATH_RELATION_INVALID",
            "project",
            "Derive project_file and source_root from the project root.",
            lambda: _validate_runtime_path_relations(project),
        ),
    )

    diagnostics: list[ProjectDiagnostic] = []

    for code, field, suggestion, operation in checks:
        try:
            operation()
        except (TypeError, ValueError) as error:
            diagnostics.append(
                _diagnostic(
                    project,
                    code=code,
                    severity=ProjectDiagnosticSeverity.ERROR,
                    field=field,
                    message=str(error),
                    suggestion=suggestion,
                )
            )

    if strict:
        _append_recommendation_diagnostics(diagnostics, project)

    return tuple(diagnostics)


def enforce_project_invariants(
    project: ProjectConfig,
    *,
    strict: bool = False,
) -> ProjectConfig:
    """Return *project* or raise one bounded configuration error."""

    errors = tuple(
        diagnostic
        for diagnostic in validate_project_semantics(project, strict=strict)
        if diagnostic.severity is ProjectDiagnosticSeverity.ERROR
    )

    if not errors:
        return project

    shown = errors[:_MAX_INVARIANT_ERROR_DETAILS]
    detail = "; ".join(f"{item.code} {item.field}: {item.message}" for item in shown)

    remaining = len(errors) - len(shown)
    if remaining:
        detail += f"; and {remaining} additional error(s)"

    project_file = str(project.project_file)

    raise ProjectConfigurationError(
        "Active project invariants are invalid",
        code="GF-WB-PROJECT-002",
        detail=detail,
        stage="projects",
        operation="enforce-project-invariants",
        subject=project_file,
        evidence_paths=(project_file,),
    )


def validate_project_id(value: str) -> str:
    """Validate the stable machine-oriented project identifier."""

    value = _require_non_empty_text(value, field="project.id")
    _reject_placeholder(value, field="project.id")

    if not _PROJECT_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "project.id must begin with an ASCII letter or digit and contain "
            "only ASCII letters, digits, '_' or '-'"
        )

    return value


def is_recommended_project_id(value: str) -> bool:
    """Return whether *value* follows the recommended lowercase format."""

    return bool(_RECOMMENDED_PROJECT_ID_PATTERN.fullmatch(value))


def validate_project_name(value: str) -> str:
    """Validate the human-readable project name."""

    value = _require_non_empty_text(value, field="project.name")
    _reject_placeholder(value, field="project.name")
    return value


def validate_language_code(value: str) -> str:
    """Validate the stable language identifier without imposing a registry."""

    value = _require_non_empty_text(value, field="project.language_code")
    _reject_placeholder(value, field="project.language_code")

    if not _LANGUAGE_CODE_PATTERN.fullmatch(value):
        raise ValueError("project.language_code must use ASCII letters, digits, '.', '_' or '-'")

    return value


def validate_project_root(value: str) -> str:
    """Validate the schema-1.0 logical project root."""

    value = _require_non_empty_text(value, field="project.root")

    if value != ".":
        raise ValueError("project.root must be '.' for project schema 1.0")

    return value


def validate_source_glob(value: str) -> str:
    """Validate the recursive filename-selection glob."""

    value = _require_non_empty_text(value, field="sources.glob")
    _reject_placeholder(value, field="sources.glob")
    _reject_environment_reference(value, field="sources.glob")

    if "/" in value or "\\" in value:
        raise ValueError("sources.glob must be a filename pattern, not a path pattern")

    if value in {".", ".."}:
        raise ValueError("sources.glob must select source candidates")

    try:
        re.compile(translate_glob(value))
    except re.error as error:
        raise ValueError("sources.glob is not a valid selection pattern") from error

    return value


def validate_optional_regex(
    value: str,
    *,
    field: str,
) -> re.Pattern[str] | None:
    """Compile a project regex or return ``None`` for the empty form."""

    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")

    _reject_control_characters(value, field=field)

    if not value:
        return None

    try:
        return re.compile(value)
    except re.error as error:
        raise ValueError(f"{field} is not a valid regular expression: {error}") from error


def validate_portable_project_path(
    value: str,
    *,
    field: str,
    allow_dot: bool = False,
    required_suffix: str | None = None,
) -> str:
    """Validate a canonical project-relative portable path declaration."""

    value = _require_non_empty_text(value, field=field)
    _reject_placeholder(value, field=field)
    _reject_environment_reference(value, field=field)

    if value == ".":
        if allow_dot:
            return value
        raise ValueError(f"{field} must identify a child path")

    if "\\" in value:
        raise ValueError(f"{field} must use '/' as its canonical separator")

    if value.startswith("/") or PureWindowsPath(value).drive:
        raise ValueError(f"{field} must be project-relative")

    if value.startswith("~"):
        raise ValueError(f"{field} must not use user-home expansion")

    parts = value.split("/")

    if any(not part for part in parts):
        raise ValueError(f"{field} contains an empty path component")

    if any(part in {".", ".."} for part in parts):
        raise ValueError(f"{field} contains a prohibited dot component")

    for part in parts:
        _validate_portable_component(part, field=field)

    if required_suffix is not None and not value.endswith(required_suffix):
        raise ValueError(f"{field} must end with {required_suffix!r}")

    return value


def normalized_portable_path_key(
    value: str,
    *,
    case_sensitive: bool = True,
) -> str:
    """Return a comparison key for an already validated portable path."""

    if not isinstance(value, str):
        raise TypeError("value must be a string")

    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")

    return value if case_sensitive else value.casefold()


def deduplicate_declared_path_parts(
    values: Sequence[str],
    *,
    case_sensitive: bool = True,
) -> tuple[str, ...]:
    """Deduplicate declared GF path parts while preserving first order."""

    _require_string_sequence(values, field="gf.path_parts")

    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")

    result: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        validated = validate_portable_project_path(
            value,
            field=f"gf.path_parts[{index}]",
            allow_dot=True,
        )
        key = normalized_portable_path_key(
            validated,
            case_sensitive=case_sensitive,
        )

        if key not in seen:
            seen.add(key)
            result.append(validated)

    return tuple(result)


def validate_minimum_version(value: str) -> str:
    """Validate the portable project minimum-version declaration."""

    if not isinstance(value, str):
        raise TypeError("gf.minimum_version must be a string")

    _reject_control_characters(value, field="gf.minimum_version")

    if not value:
        return value

    if value != value.strip():
        raise ValueError("gf.minimum_version must not contain outer whitespace")

    _reject_placeholder(value, field="gf.minimum_version")

    if any(character.isspace() for character in value):
        raise ValueError("gf.minimum_version must not contain command-output prose")

    if "/" in value or "\\" in value:
        raise ValueError("gf.minimum_version must not identify an executable path")

    return value


def validate_module_targets(
    entrypoints: Sequence[str],
    checkpoints: Sequence[str],
    *,
    require_entrypoint: bool = True,
    case_sensitive_paths: bool = True,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate ordered entrypoint and checkpoint declarations."""

    if type(require_entrypoint) is not bool:
        raise TypeError("require_entrypoint must be a bool")

    if type(case_sensitive_paths) is not bool:
        raise TypeError("case_sensitive_paths must be a bool")

    validated_entrypoints = _validate_unique_module_paths(
        entrypoints,
        field="modules.entrypoints",
        case_sensitive_paths=case_sensitive_paths,
    )
    validated_checkpoints = _validate_unique_module_paths(
        checkpoints,
        field="modules.checkpoints",
        case_sensitive_paths=case_sensitive_paths,
    )

    if require_entrypoint and not validated_entrypoints:
        raise ValueError(
            "modules.entrypoints must contain at least one target for an initialized project"
        )

    return validated_entrypoints, validated_checkpoints


def validate_scenario_id(value: str, *, field: str) -> str:
    """Validate a portable scenario identifier."""

    value = _require_non_empty_text(value, field=field)
    _reject_placeholder(value, field=field)
    _reject_environment_reference(value, field=field)

    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"{field} must be an identifier, not a path")

    _validate_portable_component(value, field=field)
    return value


def is_recommended_scenario_id(value: str) -> bool:
    """Return whether *value* follows the recommended lowercase format."""

    return bool(_RECOMMENDED_SCENARIO_ID_PATTERN.fullmatch(value))


def validate_scenario_policy(
    required: Sequence[str],
    optional: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate required and optional scenario membership."""

    validated_required = _validate_unique_scenario_ids(
        required,
        field="validation.required_scenarios",
    )
    validated_optional = _validate_unique_scenario_ids(
        optional,
        field="validation.optional_scenarios",
    )

    overlap = set(validated_required).intersection(validated_optional)

    if overlap:
        raise ValueError(
            "required and optional scenario lists must not overlap: " + ", ".join(sorted(overlap))
        )

    return validated_required, validated_optional


def validate_release_requires_pgf(value: bool) -> bool:
    """Require the explicit boolean release policy."""

    if type(value) is not bool:
        raise TypeError("validation.release_requires_pgf must be a boolean")

    return value


def _append_recommendation_diagnostics(
    diagnostics: list[ProjectDiagnostic],
    project: ProjectConfig,
) -> None:
    if not is_recommended_project_id(str(project.identity.id)):
        diagnostics.append(
            _diagnostic(
                project,
                code="PROJECT_ID_FORMAT_NOT_RECOMMENDED",
                severity=ProjectDiagnosticSeverity.WARNING,
                field="project.id",
                message=("project.id does not use the recommended lowercase format."),
                suggestion="Use lowercase IDs for new projects.",
            )
        )

    groups = (
        (
            "validation.required_scenarios",
            project.validation.required_scenarios,
        ),
        (
            "validation.optional_scenarios",
            project.validation.optional_scenarios,
        ),
    )

    for field, scenario_ids in groups:
        for index, scenario_id in enumerate(scenario_ids):
            value = str(scenario_id)

            if not is_recommended_scenario_id(value):
                diagnostics.append(
                    _diagnostic(
                        project,
                        code="PROJECT_SCENARIO_ID_FORMAT_NOT_RECOMMENDED",
                        severity=ProjectDiagnosticSeverity.WARNING,
                        field=f"{field}[{index}]",
                        message=(
                            f"Scenario ID {value!r} does not use the recommended lowercase format."
                        ),
                        suggestion="Use lowercase IDs for new scenarios.",
                    )
                )


def _diagnostic(
    project: ProjectConfig,
    *,
    code: str,
    severity: ProjectDiagnosticSeverity,
    field: str,
    message: str,
    suggestion: str,
) -> ProjectDiagnostic:
    return ProjectDiagnostic(
        code=code,
        severity=severity,
        field=field,
        message=message,
        source_file=project.project_file,
        suggestion=suggestion,
        subject=None,
    )


def _validate_gf_path_parts(values: Sequence[str]) -> tuple[str, ...]:
    validated = deduplicate_declared_path_parts(values)

    if len(validated) != len(values):
        raise ValueError("gf.path_parts must not contain duplicate normalized paths")

    return validated


def _validate_runtime_path_relations(project: ProjectConfig) -> None:
    if project.project_file != project.project_root / "project.toml":
        raise ValueError("project_file must equal project_root / 'project.toml'")

    expected_source_root = project.project_root / project.sources.directory

    if project.source_root != expected_source_root:
        raise ValueError("source_root must equal project_root / sources.directory")

    try:
        project.source_root.relative_to(project.project_root)
    except ValueError as error:
        raise ValueError("source_root must remain inside project_root") from error


def _validate_unique_module_paths(
    values: Sequence[str],
    *,
    field: str,
    case_sensitive_paths: bool,
) -> tuple[str, ...]:
    _require_string_sequence(values, field=field)

    result: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        validated = validate_portable_project_path(
            value,
            field=f"{field}[{index}]",
            required_suffix=".gf",
        )
        key = normalized_portable_path_key(
            validated,
            case_sensitive=case_sensitive_paths,
        )

        if key in seen:
            raise ValueError(f"{field} contains duplicate normalized path: {value}")

        seen.add(key)
        result.append(validated)

    return tuple(result)


def _validate_unique_scenario_ids(
    values: Sequence[str],
    *,
    field: str,
) -> tuple[str, ...]:
    _require_string_sequence(values, field=field)

    result: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        validated = validate_scenario_id(
            value,
            field=f"{field}[{index}]",
        )

        if validated in seen:
            raise ValueError(f"{field} contains duplicate scenario ID: {validated}")

        seen.add(validated)
        result.append(validated)

    return tuple(result)


def _require_non_empty_text(value: str, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")

    _reject_control_characters(value, field=field)

    if not value:
        raise ValueError(f"{field} must be non-empty")

    if value != value.strip():
        raise ValueError(f"{field} must not contain outer whitespace")

    return value


def _require_string_sequence(
    values: Sequence[str],
    *,
    field: str,
) -> None:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(
        values,
        Sequence,
    ):
        raise TypeError(f"{field} must be an ordered sequence of strings")

    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"{field}[{index}] must be a string")


def _reject_control_characters(value: str, *, field: str) -> None:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field} must not contain control characters")


def _reject_placeholder(value: str, *, field: str) -> None:
    if find_unresolved_placeholder(value) is not None:
        raise ValueError(f"{field} contains an unresolved template placeholder")


def _reject_environment_reference(value: str, *, field: str) -> None:
    if _ENVIRONMENT_REFERENCE_PATTERN.search(value):
        raise ValueError(f"{field} must not contain an environment-variable reference")


def _validate_portable_component(
    component: str,
    *,
    field: str,
) -> None:
    if any(character in _WINDOWS_FORBIDDEN_PATH_CHARACTERS for character in component):
        raise ValueError(f"{field} contains a non-portable path character")

    if component.endswith((".", " ")):
        raise ValueError(f"{field} contains an ambiguous trailing dot or space")

    reserved_key = component.split(".", 1)[0].upper()

    if reserved_key in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{field} contains reserved Windows name: {component}")
