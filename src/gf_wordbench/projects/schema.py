"""Canonical persisted schema for ``project/project.toml``."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Final, Never, TypedDict, cast

from gf_wordbench.kernel.errors import SchemaValidationError, UnsupportedVersionError

from .models import (
    GFProjectConfig,
    ModuleTargets,
    PROJECT_CONFIG_FILENAME,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
)
from .paths import ProjectPaths, resolve_source_root

_SCHEMA_VERSION_PATTERN: Final = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
_CURRENT_SCHEMA_MAJOR: Final = 1
_CURRENT_SCHEMA_MINOR: Final = 0

_PLACEHOLDER_PATTERN: Final = re.compile(r"<[^<>]+>")
_ENVIRONMENT_REFERENCE_PATTERNS: Final = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[^{}]+\}"),
    re.compile(r"(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*"),
)
_WINDOWS_DRIVE_PATTERN: Final = re.compile(r"^[A-Za-z]:")
_SCENARIO_ID_PATTERN: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_-]*$"
)

_ROOT_FIELDS: Final = frozenset(
    {
        "schema_id",
        "schema_version",
        "project",
        "sources",
        "gf",
        "modules",
        "validation",
    }
)
_PROJECT_FIELDS: Final = frozenset(
    {"id", "name", "language_code", "root"}
)
_SOURCE_FIELDS: Final = frozenset(
    {"directory", "glob", "include_regex", "exclude_regex"}
)
_GF_FIELDS: Final = frozenset(
    {"path_parts", "minimum_version"}
)
_MODULE_FIELDS: Final = frozenset(
    {"entrypoints", "checkpoints"}
)
_VALIDATION_FIELDS: Final = frozenset(
    {
        "required_scenarios",
        "optional_scenarios",
        "release_requires_pgf",
    }
)


class ProjectTable(TypedDict):
    id: str
    name: str
    language_code: str
    root: str


class SourcesTable(TypedDict):
    directory: str
    glob: str
    include_regex: str
    exclude_regex: str


class GFTable(TypedDict):
    path_parts: list[str]
    minimum_version: str


class ModulesTable(TypedDict):
    entrypoints: list[str]
    checkpoints: list[str]


class ValidationTable(TypedDict):
    required_scenarios: list[str]
    optional_scenarios: list[str]
    release_requires_pgf: bool


class ProjectDocument(TypedDict):
    schema_id: str
    schema_version: str
    project: ProjectTable
    sources: SourcesTable
    gf: GFTable
    modules: ModulesTable
    validation: ValidationTable


class ProjectSchemaCompatibility(str, Enum):
    """Compatibility policy for persisted project documents."""

    STRICT = "strict"
    FORWARD_MINOR = "forward_minor"


@dataclass(frozen=True, slots=True)
class _ValidationContext:
    source: Path | None

    def fail(self, field: str, message: str) -> Never:
        location = f"{self.source}: " if self.source is not None else ""
        raise SchemaValidationError(
            f"{location}{field}: {message}"
        )

    def unsupported(self, field: str, message: str) -> Never:
        location = f"{self.source}: " if self.source is not None else ""
        raise UnsupportedVersionError(
            f"{location}{field}: {message}"
        )


def validate_project_schema(
    document: Mapping[str, object],
    *,
    source: Path | None = None,
    compatibility: ProjectSchemaCompatibility = (
        ProjectSchemaCompatibility.STRICT
    ),
    allow_placeholders: bool = False,
) -> ProjectDocument:
    """Validate and copy one canonical project document.

    The returned document contains only supported schema fields and preserves
    the declared ordering of arrays.
    """

    if not isinstance(compatibility, ProjectSchemaCompatibility):
        raise TypeError(
            "compatibility must be a ProjectSchemaCompatibility"
        )
    if not isinstance(allow_placeholders, bool):
        raise TypeError("allow_placeholders must be a boolean")

    context = _ValidationContext(source)
    root = _require_mapping(document, "$", context)

    schema_id = _require_string(
        root,
        "schema_id",
        "$",
        context,
    )
    if schema_id != PROJECT_SCHEMA_ID:
        context.fail(
            "$.schema_id",
            f"expected {PROJECT_SCHEMA_ID!r}, received {schema_id!r}",
        )

    schema_version = _require_string(
        root,
        "schema_version",
        "$",
        context,
    )
    major, minor = _validate_schema_version(
        schema_version,
        compatibility,
        context,
    )
    allow_unknown = (
        compatibility is ProjectSchemaCompatibility.FORWARD_MINOR
        and major == _CURRENT_SCHEMA_MAJOR
        and minor > _CURRENT_SCHEMA_MINOR
    )

    _validate_fields(
        root,
        _ROOT_FIELDS,
        "$",
        context,
        allow_unknown=allow_unknown,
    )

    project = _require_table(root, "project", context)
    sources = _require_table(root, "sources", context)
    gf = _require_table(root, "gf", context)
    modules = _require_table(root, "modules", context)
    validation = _require_table(root, "validation", context)

    _validate_fields(
        project,
        _PROJECT_FIELDS,
        "$.project",
        context,
        allow_unknown=allow_unknown,
    )
    _validate_fields(
        sources,
        _SOURCE_FIELDS,
        "$.sources",
        context,
        allow_unknown=allow_unknown,
    )
    _validate_fields(
        gf,
        _GF_FIELDS,
        "$.gf",
        context,
        allow_unknown=allow_unknown,
    )
    _validate_fields(
        modules,
        _MODULE_FIELDS,
        "$.modules",
        context,
        allow_unknown=allow_unknown,
    )
    _validate_fields(
        validation,
        _VALIDATION_FIELDS,
        "$.validation",
        context,
        allow_unknown=allow_unknown,
    )

    project_id = _require_string(
        project,
        "id",
        "$.project",
        context,
    )
    project_name = _require_string(
        project,
        "name",
        "$.project",
        context,
    )
    language_code = _require_string(
        project,
        "language_code",
        "$.project",
        context,
    )
    project_root = _require_string(
        project,
        "root",
        "$.project",
        context,
    )

    _validate_identifier(
        project_id,
        "$.project.id",
        context,
        allow_placeholders,
    )
    _validate_display_name(
        project_name,
        "$.project.name",
        context,
        allow_placeholders,
    )
    _validate_identifier(
        language_code,
        "$.project.language_code",
        context,
        allow_placeholders,
    )
    _validate_project_root(project_root, context)

    source_directory = _require_string(
        sources,
        "directory",
        "$.sources",
        context,
    )
    source_glob = _require_string(
        sources,
        "glob",
        "$.sources",
        context,
    )
    include_regex = _require_string(
        sources,
        "include_regex",
        "$.sources",
        context,
    )
    exclude_regex = _require_string(
        sources,
        "exclude_regex",
        "$.sources",
        context,
    )

    _validate_portable_relative_path(
        source_directory,
        "$.sources.directory",
        context,
        allow_dot=False,
        allow_placeholders=allow_placeholders,
    )
    _validate_glob(
        source_glob,
        "$.sources.glob",
        context,
        allow_placeholders,
    )
    _validate_regex(
        include_regex,
        "$.sources.include_regex",
        context,
    )
    _validate_regex(
        exclude_regex,
        "$.sources.exclude_regex",
        context,
    )

    path_parts = _require_string_list(
        gf,
        "path_parts",
        "$.gf",
        context,
    )
    minimum_version = _require_string(
        gf,
        "minimum_version",
        "$.gf",
        context,
    )

    for index, path_part in enumerate(path_parts):
        _validate_portable_relative_path(
            path_part,
            f"$.gf.path_parts[{index}]",
            context,
            allow_dot=True,
            allow_placeholders=allow_placeholders,
        )

    _validate_optional_version_text(
        minimum_version,
        "$.gf.minimum_version",
        context,
    )

    entrypoints = _require_string_list(
        modules,
        "entrypoints",
        "$.modules",
        context,
    )
    checkpoints = _require_string_list(
        modules,
        "checkpoints",
        "$.modules",
        context,
    )

    if not entrypoints:
        context.fail(
            "$.modules.entrypoints",
            "must contain at least one module target",
        )

    _validate_module_targets(
        entrypoints,
        "$.modules.entrypoints",
        context,
        allow_placeholders,
    )
    _validate_module_targets(
        checkpoints,
        "$.modules.checkpoints",
        context,
        allow_placeholders,
    )

    required_scenarios = _require_string_list(
        validation,
        "required_scenarios",
        "$.validation",
        context,
    )
    optional_scenarios = _require_string_list(
        validation,
        "optional_scenarios",
        "$.validation",
        context,
    )
    release_requires_pgf = _require_bool(
        validation,
        "release_requires_pgf",
        "$.validation",
        context,
    )

    _validate_scenario_ids(
        required_scenarios,
        "$.validation.required_scenarios",
        context,
        allow_placeholders,
    )
    _validate_scenario_ids(
        optional_scenarios,
        "$.validation.optional_scenarios",
        context,
        allow_placeholders,
    )

    overlap = set(required_scenarios).intersection(
        optional_scenarios
    )
    if overlap:
        context.fail(
            "$.validation",
            "required_scenarios and optional_scenarios overlap: "
            + ", ".join(sorted(overlap)),
        )

    return ProjectDocument(
        schema_id=schema_id,
        schema_version=schema_version,
        project=ProjectTable(
            id=project_id,
            name=project_name,
            language_code=language_code,
            root=project_root,
        ),
        sources=SourcesTable(
            directory=source_directory,
            glob=source_glob,
            include_regex=include_regex,
            exclude_regex=exclude_regex,
        ),
        gf=GFTable(
            path_parts=list(path_parts),
            minimum_version=minimum_version,
        ),
        modules=ModulesTable(
            entrypoints=list(entrypoints),
            checkpoints=list(checkpoints),
        ),
        validation=ValidationTable(
            required_scenarios=list(required_scenarios),
            optional_scenarios=list(optional_scenarios),
            release_requires_pgf=release_requires_pgf,
        ),
    )


def parse_project_document(
    document: ProjectDocument,
    *,
    source_file: Path,
) -> ProjectConfig:
    """Validate a document and construct its complete project model.

    ``source_file`` must be the explicit absolute and lexically normalized
    canonical ``project.toml`` path. This operation performs no filesystem I/O.
    """

    project_file, project_root = _resolve_project_file(
        source_file
    )
    validated = validate_project_schema(
        document,
        source=project_file,
    )

    project_table = validated["project"]
    sources_table = validated["sources"]
    gf_table = validated["gf"]
    modules_table = validated["modules"]
    validation_table = validated["validation"]

    identity = ProjectIdentity(
        id=project_table["id"],
        name=project_table["name"],
        language_code=project_table["language_code"],
        root=Path(project_table["root"]),
    )
    sources = SourceConfig(
        directory=Path(sources_table["directory"]),
        glob=sources_table["glob"],
        include_regex=sources_table["include_regex"],
        exclude_regex=sources_table["exclude_regex"],
    )
    gf = GFProjectConfig(
        path_parts=tuple(gf_table["path_parts"]),
        minimum_version=gf_table["minimum_version"],
    )
    modules = ModuleTargets(
        entrypoints=tuple(
            Path(value)
            for value in modules_table["entrypoints"]
        ),
        checkpoints=tuple(
            Path(value)
            for value in modules_table["checkpoints"]
        ),
    )
    validation = ValidationPolicy(
        required_scenarios=tuple(
            validation_table["required_scenarios"]
        ),
        optional_scenarios=tuple(
            validation_table["optional_scenarios"]
        ),
        release_requires_pgf=(
            validation_table["release_requires_pgf"]
        ),
    )

    return ProjectConfig(
        schema_id=validated["schema_id"],
        schema_version=validated["schema_version"],
        identity=identity,
        sources=sources,
        gf=gf,
        modules=modules,
        validation=validation,
        project_file=project_file,
        project_root=project_root,
        source_root=resolve_source_root(
            project_root,
            sources.directory,
        ),
    )


def _resolve_project_file(
    source_file: Path,
) -> tuple[Path, Path]:
    if not isinstance(source_file, Path):
        raise TypeError("source_file must be pathlib.Path")
    if not source_file.is_absolute():
        raise SchemaValidationError(
            "source_file must be an explicit absolute "
            "project.toml path"
        )

    project_paths = ProjectPaths.from_root(
        source_file.parent
    )
    project_file = (
        project_paths.root / PROJECT_CONFIG_FILENAME
    )

    if source_file != project_file:
        raise SchemaValidationError(
            "source_file must be the lexically normalized "
            "canonical project.toml path; "
            f"expected {project_file}, received {source_file}"
        )

    return project_file, project_paths.root


def validate_project_template_schema(
    document: Mapping[str, object],
    *,
    source: Path | None = None,
) -> ProjectDocument:
    """Validate a canonical template with placeholders enabled."""

    return validate_project_schema(
        document,
        source=source,
        allow_placeholders=True,
    )


def _validate_schema_version(
    value: str,
    compatibility: ProjectSchemaCompatibility,
    context: _ValidationContext,
) -> tuple[int, int]:
    match = _SCHEMA_VERSION_PATTERN.fullmatch(value)
    if match is None:
        context.fail(
            "$.schema_version",
            "must use MAJOR.MINOR decimal form",
        )

    major = int(match.group(1))
    minor = int(match.group(2))

    if major != _CURRENT_SCHEMA_MAJOR:
        context.unsupported(
            "$.schema_version",
            f"unsupported major version {major}; supported "
            f"major is {_CURRENT_SCHEMA_MAJOR}",
        )

    if minor != _CURRENT_SCHEMA_MINOR:
        forward_compatible = (
            compatibility
            is ProjectSchemaCompatibility.FORWARD_MINOR
            and minor > _CURRENT_SCHEMA_MINOR
        )
        if not forward_compatible:
            context.unsupported(
                "$.schema_version",
                f"unsupported version {value!r}; current "
                f"version is {PROJECT_SCHEMA_VERSION!r}",
            )

    return major, minor


def _require_mapping(
    value: object,
    field: str,
    context: _ValidationContext,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        context.fail(field, "must be a TOML table")

    for key in value:
        if not isinstance(key, str):
            context.fail(
                field,
                "contains a non-string key",
            )

    return cast(Mapping[str, object], value)


def _require_table(
    parent: Mapping[str, object],
    key: str,
    context: _ValidationContext,
) -> Mapping[str, object]:
    if key not in parent:
        context.fail(
            "$",
            f"missing required table [{key}]",
        )

    return _require_mapping(
        parent[key],
        f"$.{key}",
        context,
    )


def _validate_fields(
    table: Mapping[str, object],
    required: frozenset[str],
    field: str,
    context: _ValidationContext,
    *,
    allow_unknown: bool,
) -> None:
    keys = set(table)

    missing = required - keys
    if missing:
        context.fail(
            field,
            "missing required fields: "
            + ", ".join(sorted(missing)),
        )

    unknown = keys - required
    if unknown and not allow_unknown:
        context.fail(
            field,
            "contains unknown fields: "
            + ", ".join(sorted(unknown)),
        )


def _require_string(
    table: Mapping[str, object],
    key: str,
    table_path: str,
    context: _ValidationContext,
) -> str:
    if key not in table:
        context.fail(
            table_path,
            f"missing required field {key!r}",
        )

    value = table[key]
    if not isinstance(value, str):
        context.fail(
            f"{table_path}.{key}",
            "must be a string",
        )

    return value


def _require_string_list(
    table: Mapping[str, object],
    key: str,
    table_path: str,
    context: _ValidationContext,
) -> list[str]:
    if key not in table:
        context.fail(
            table_path,
            f"missing required field {key!r}",
        )

    value = table[key]
    if not isinstance(value, list):
        context.fail(
            f"{table_path}.{key}",
            "must be an array of strings",
        )

    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            context.fail(
                f"{table_path}.{key}[{index}]",
                "must be a string",
            )
        result.append(item)

    return result


def _require_bool(
    table: Mapping[str, object],
    key: str,
    table_path: str,
    context: _ValidationContext,
) -> bool:
    if key not in table:
        context.fail(
            table_path,
            f"missing required field {key!r}",
        )

    value = table[key]
    if not isinstance(value, bool):
        context.fail(
            f"{table_path}.{key}",
            "must be a boolean",
        )

    return value


def _validate_identifier(
    value: str,
    field: str,
    context: _ValidationContext,
    allow_placeholders: bool,
) -> None:
    _validate_nonempty_text(value, field, context)

    if not allow_placeholders:
        _reject_placeholder(value, field, context)

    if value in {".", ".."} or "/" in value or "\\" in value:
        context.fail(
            field,
            "must be a stable identifier, not a filesystem path",
        )


def _validate_display_name(
    value: str,
    field: str,
    context: _ValidationContext,
    allow_placeholders: bool,
) -> None:
    _validate_nonempty_text(value, field, context)

    if not allow_placeholders:
        _reject_placeholder(value, field, context)


def _validate_project_root(
    value: str,
    context: _ValidationContext,
) -> None:
    if value != ".":
        context.fail(
            "$.project.root",
            "schema 1.x requires the canonical value '.'",
        )


def _validate_glob(
    value: str,
    field: str,
    context: _ValidationContext,
    allow_placeholders: bool,
) -> None:
    _validate_nonempty_text(value, field, context)

    if not allow_placeholders:
        _reject_placeholder(value, field, context)

    _reject_nonportable_path_text(
        value,
        field,
        context,
    )

    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        context.fail(
            field,
            "must be a project-relative glob without "
            "parent traversal",
        )


def _validate_regex(
    value: str,
    field: str,
    context: _ValidationContext,
) -> None:
    _validate_text(
        value,
        field,
        context,
        allow_empty=True,
    )

    try:
        re.compile(value)
    except re.error as exc:
        context.fail(
            field,
            f"invalid regular expression: {exc.msg}",
        )


def _validate_optional_version_text(
    value: str,
    field: str,
    context: _ValidationContext,
) -> None:
    _validate_text(
        value,
        field,
        context,
        allow_empty=True,
    )

    if value and value != value.strip():
        context.fail(
            field,
            "must not have outer whitespace",
        )


def _validate_module_targets(
    values: list[str],
    field: str,
    context: _ValidationContext,
    allow_placeholders: bool,
) -> None:
    seen: set[str] = set()

    for index, value in enumerate(values):
        item_field = f"{field}[{index}]"

        _validate_portable_relative_path(
            value,
            item_field,
            context,
            allow_dot=False,
            allow_placeholders=allow_placeholders,
        )

        if not value.endswith(".gf"):
            context.fail(
                item_field,
                "must end in '.gf'",
            )

        normalized = str(PurePosixPath(value))
        if normalized in seen:
            context.fail(
                item_field,
                f"duplicates normalized target {normalized!r}",
            )

        seen.add(normalized)


def _validate_scenario_ids(
    values: list[str],
    field: str,
    context: _ValidationContext,
    allow_placeholders: bool,
) -> None:
    seen: set[str] = set()

    for index, value in enumerate(values):
        item_field = f"{field}[{index}]"
        _validate_nonempty_text(
            value,
            item_field,
            context,
        )

        if (
            allow_placeholders
            and _contains_placeholder(value)
        ):
            continue

        _reject_placeholder(
            value,
            item_field,
            context,
        )

        if _SCENARIO_ID_PATTERN.fullmatch(value) is None:
            context.fail(
                item_field,
                "must use letters, digits, '_' or '-', "
                "beginning with a letter or digit",
            )

        if value in seen:
            context.fail(
                item_field,
                f"duplicates scenario ID {value!r}",
            )

        seen.add(value)


def _validate_portable_relative_path(
    value: str,
    field: str,
    context: _ValidationContext,
    *,
    allow_dot: bool,
    allow_placeholders: bool,
) -> None:
    _validate_nonempty_text(
        value,
        field,
        context,
    )

    if not allow_placeholders:
        _reject_placeholder(
            value,
            field,
            context,
        )

    _reject_nonportable_path_text(
        value,
        field,
        context,
    )

    path = PurePosixPath(value)

    if path.is_absolute():
        context.fail(field, "must be relative")

    if ".." in path.parts:
        context.fail(
            field,
            "must not contain parent traversal",
        )

    if not allow_dot and value == ".":
        context.fail(
            field,
            "must identify a file or subpath",
        )

    normalized = str(path)
    if value != normalized:
        context.fail(
            field,
            f"must use canonical POSIX form {normalized!r}",
        )


def _reject_nonportable_path_text(
    value: str,
    field: str,
    context: _ValidationContext,
) -> None:
    if "\\" in value:
        context.fail(
            field,
            "must use '/' as the canonical separator",
        )

    if _WINDOWS_DRIVE_PATTERN.match(value):
        context.fail(
            field,
            "must not contain a drive letter",
        )

    if any(
        pattern.search(value)
        for pattern in _ENVIRONMENT_REFERENCE_PATTERNS
    ):
        context.fail(
            field,
            "must not contain an environment-variable reference",
        )


def _validate_nonempty_text(
    value: str,
    field: str,
    context: _ValidationContext,
) -> None:
    _validate_text(
        value,
        field,
        context,
        allow_empty=False,
    )

    if value != value.strip():
        context.fail(
            field,
            "must not have outer whitespace",
        )


def _validate_text(
    value: str,
    field: str,
    context: _ValidationContext,
    *,
    allow_empty: bool,
) -> None:
    if not allow_empty and not value:
        context.fail(field, "must not be empty")

    if any(
        ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        context.fail(
            field,
            "must not contain control characters",
        )


def _reject_placeholder(
    value: str,
    field: str,
    context: _ValidationContext,
) -> None:
    if _contains_placeholder(value):
        context.fail(
            field,
            "contains an unresolved template placeholder",
        )


def _contains_placeholder(value: str) -> bool:
    return _PLACEHOLDER_PATTERN.search(value) is not None


__all__ = [
    "GFTable",
    "ModulesTable",
    "ProjectDocument",
    "ProjectSchemaCompatibility",
    "ProjectTable",
    "SourcesTable",
    "ValidationTable",
    "parse_project_document",
    "validate_project_schema",
    "validate_project_template_schema",
]