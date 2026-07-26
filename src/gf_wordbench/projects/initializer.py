"""Initialize the single active project from the canonical project template."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.errors import (
    ContractViolationError,
    ProjectConfigurationError,
)

from .models import (
    ProjectCheckScope,
    ProjectConfig,
    ProjectValidationResult,
)
from .ports import (
    ProjectConfigWriter,
    ProjectFilesystem,
    ProjectTemplateSource,
    TreeEntry,
    TreeEntryKind,
)
from .validator import check_project

__all__ = (
    "ProjectInitializationRequest",
    "ProjectInitializationResult",
    "ProjectInitializer",
    "initialize_project",
)

_ACTIVE_PROJECT_DIRECTORY: Final[str] = "project"
_PROJECT_FILENAME: Final[str] = "project.toml"
_STAGING_DIRECTORY: Final[str] = ".gf-wordbench-project-init-stage"
_ROLLBACK_DIRECTORY: Final[str] = ".gf-wordbench-project-init-rollback"

_PLACEHOLDER_TOKEN: Final[re.Pattern[str]] = re.compile(
    r"^<[A-Z][A-Z0-9_-]*>$"
)
_PLACEHOLDER_REFERENCE: Final[re.Pattern[str]] = re.compile(
    r"<[A-Z][A-Z0-9_-]*>"
)

_TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".gf",
        ".gfs",
        ".json",
        ".md",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)
_MAX_VALIDATION_ERRORS: Final[int] = 8


@dataclass(frozen=True, slots=True)
class ProjectInitializationRequest:
    """Explicit inputs for one template-to-project initialization."""

    workspace_root: Path
    config: ProjectConfig
    template_values: Mapping[str, str] = field(default_factory=dict)
    require_resolved_placeholders: bool = False
    allow_existing_empty_project: bool = True

    def __post_init__(self) -> None:
        workspace_root = _validated_absolute_path(
            self.workspace_root,
            field_name="workspace_root",
        )
        if not isinstance(self.config, ProjectConfig):
            raise TypeError("config must be a ProjectConfig")

        _require_bool(
            "require_resolved_placeholders",
            self.require_resolved_placeholders,
        )
        _require_bool(
            "allow_existing_empty_project",
            self.allow_existing_empty_project,
        )

        object.__setattr__(self, "workspace_root", workspace_root)
        object.__setattr__(
            self,
            "template_values",
            MappingProxyType(
                _normalized_template_values(self.template_values)
            ),
        )


@dataclass(frozen=True, slots=True)
class ProjectInitializationResult:
    """Published project paths and validation evidence."""

    workspace_root: Path
    template_root: Path
    project_root: Path
    project_file: Path
    created_files: tuple[PurePosixPath, ...]
    unresolved_placeholders: tuple[str, ...]
    validation: ProjectValidationResult

    @property
    def is_active(self) -> bool:
        """Whether the published project is valid and fully resolved."""

        return self.validation.ok and not self.unresolved_placeholders


@dataclass(frozen=True, slots=True)
class _ProjectTemplateStage:
    """Private materialized-template staging record."""

    root: Path
    project_file: Path
    created_files: tuple[PurePosixPath, ...]


class ProjectInitializer:
    """Coordinate staged, validated, atomic project initialization."""

    def __init__(
        self,
        *,
        template_source: ProjectTemplateSource,
        filesystem: ProjectFilesystem,
        config_writer: ProjectConfigWriter,
    ) -> None:
        self._template_source = template_source
        self._filesystem = filesystem
        self._config_writer = config_writer

    def initialize(
        self,
        request: ProjectInitializationRequest,
    ) -> ProjectInitializationResult:
        """Materialize, validate, and atomically publish the active project."""

        if not isinstance(request, ProjectInitializationRequest):
            raise TypeError(
                "request must be a ProjectInitializationRequest"
            )

        workspace_root = self._filesystem.resolve(request.workspace_root)
        self._require_workspace(workspace_root)

        project_root = self._contained(
            workspace_root / _ACTIVE_PROJECT_DIRECTORY,
            workspace_root=workspace_root,
        )
        stage_root = self._contained(
            workspace_root / _STAGING_DIRECTORY,
            workspace_root=workspace_root,
        )
        rollback_root = self._contained(
            workspace_root / _ROLLBACK_DIRECTORY,
            workspace_root=workspace_root,
        )

        template_root = self._filesystem.resolve(
            self._template_source.root
        )
        self._require_template_root(
            template_root,
            workspace_root=workspace_root,
        )
        self._require_matching_configuration(
            request.config,
            project_root=project_root,
        )
        self._require_available_lifecycle_paths(
            project_root=project_root,
            stage_root=stage_root,
            rollback_root=rollback_root,
            allow_existing_empty=request.allow_existing_empty_project,
        )

        expected_layout = _inventory_layout(
            self._template_source.inventory(),
            owner="project template",
        )
        _require_canonical_template(expected_layout)

        published = False

        try:
            self._template_source.materialize(
                stage_root,
                replacements=request.template_values,
            )

            staged_config = _staged_configuration(
                request.config,
                stage_root=stage_root,
            )
            staged_project_file = stage_root / _PROJECT_FILENAME

            self._config_writer.write(
                staged_project_file,
                staged_config,
                overwrite=True,
            )

            observed_layout = _inventory_layout(
                self._filesystem.inspect_tree(stage_root),
                owner="materialized project stage",
            )
            _require_matching_layout(
                expected=expected_layout,
                observed=observed_layout,
                subject=stage_root,
            )

            created_files = _created_files(observed_layout)
            stage = _ProjectTemplateStage(
                root=stage_root,
                project_file=staged_project_file,
                created_files=created_files,
            )
            _assert_stage(stage)

            unresolved = _find_unresolved_placeholders(
                stage,
                filesystem=self._filesystem,
            )

            staged_validation = check_project(
                staged_config,
                self._filesystem,
                scope=ProjectCheckScope.NORMAL,
                strict=request.require_resolved_placeholders,
            )
            _raise_for_validation(
                staged_validation,
                subject=stage.project_file,
            )
            _raise_for_placeholders(
                unresolved,
                required=request.require_resolved_placeholders,
                subject=stage.root,
            )

            self._filesystem.atomic_replace_directory(
                staged=stage.root,
                active=project_root,
                rollback=rollback_root,
            )
            published = True

            active_validation = check_project(
                request.config,
                self._filesystem,
                scope=ProjectCheckScope.NORMAL,
                strict=request.require_resolved_placeholders,
            )
            _raise_for_validation(
                active_validation,
                subject=request.config.project_file,
            )

            result = ProjectInitializationResult(
                workspace_root=workspace_root,
                template_root=template_root,
                project_root=project_root,
                project_file=project_root / _PROJECT_FILENAME,
                created_files=created_files,
                unresolved_placeholders=unresolved,
                validation=active_validation,
            )

            if self._filesystem.exists(rollback_root):
                self._filesystem.remove_tree(rollback_root)

            return result

        except BaseException as error:
            if published:
                self._rollback_publication(
                    project_root=project_root,
                    rollback_root=rollback_root,
                    original_error=error,
                )
            else:
                _discard_if_present(
                    stage_root,
                    filesystem=self._filesystem,
                )
            raise

    def _require_workspace(self, workspace_root: Path) -> None:
        if (
            not self._filesystem.exists(workspace_root)
            or not self._filesystem.is_directory(workspace_root)
        ):
            raise ProjectConfigurationError(
                "Project initialization requires an existing workspace directory",
                code="GF-WB-PROJECT-INIT-001",
                stage="projects",
                operation="initialize-project",
                subject=str(workspace_root),
            )

    def _require_template_root(
        self,
        template_root: Path,
        *,
        workspace_root: Path,
    ) -> None:
        expected = self._filesystem.resolve(
            workspace_root / "templates" / "project"
        )
        if template_root != expected:
            raise ContractViolationError(
                "The project template source does not identify the canonical template",
                code="GF-WB-PROJECT-INIT-002",
                detail=f"Expected {expected!s}, received {template_root!s}.",
                stage="projects",
                operation="initialize-project",
                subject=str(template_root),
            )

        if (
            not self._filesystem.exists(template_root)
            or not self._filesystem.is_directory(template_root)
        ):
            raise ProjectConfigurationError(
                "The canonical project template directory is unavailable",
                code="GF-WB-PROJECT-INIT-003",
                stage="projects",
                operation="initialize-project",
                subject=str(template_root),
            )

    def _contained(
        self,
        path: Path,
        *,
        workspace_root: Path,
    ) -> Path:
        return self._filesystem.require_contained(
            path,
            root=workspace_root,
            allow_root=False,
        )

    def _require_available_lifecycle_paths(
        self,
        *,
        project_root: Path,
        stage_root: Path,
        rollback_root: Path,
        allow_existing_empty: bool,
    ) -> None:
        for path, role in (
            (stage_root, "staging"),
            (rollback_root, "rollback"),
        ):
            if self._filesystem.exists(path):
                raise ProjectConfigurationError(
                    f"A stale project-initialization {role} path already exists",
                    code="GF-WB-PROJECT-INIT-004",
                    detail=(
                        "Inspect and remove the stale lifecycle-owned path "
                        "before retrying initialization."
                    ),
                    stage="projects",
                    operation="initialize-project",
                    subject=str(path),
                )

        if not self._filesystem.exists(project_root):
            return

        if not allow_existing_empty:
            raise ProjectConfigurationError(
                "An active project path already exists",
                code="GF-WB-PROJECT-INIT-005",
                stage="projects",
                operation="initialize-project",
                subject=str(project_root),
            )

        if not self._filesystem.is_directory(project_root):
            raise ProjectConfigurationError(
                "The active project path is not a regular directory",
                code="GF-WB-PROJECT-INIT-006",
                stage="projects",
                operation="initialize-project",
                subject=str(project_root),
            )

        if self._filesystem.inspect_tree(project_root):
            raise ProjectConfigurationError(
                "The active project directory is not empty",
                code="GF-WB-PROJECT-INIT-007",
                detail="Initialization never overwrites existing project work.",
                stage="projects",
                operation="initialize-project",
                subject=str(project_root),
            )

    def _rollback_publication(
        self,
        *,
        project_root: Path,
        rollback_root: Path,
        original_error: BaseException,
    ) -> None:
        try:
            if self._filesystem.exists(rollback_root):
                self._filesystem.restore_directory(
                    rollback=rollback_root,
                    active=project_root,
                )
            elif self._filesystem.exists(project_root):
                self._filesystem.remove_tree(project_root)
        except Exception as rollback_error:
            raise ContractViolationError(
                "Project initialization failed and automatic rollback also failed",
                code="GF-WB-PROJECT-INIT-008",
                detail=(
                    f"Original failure: {type(original_error).__name__}: "
                    f"{original_error}"
                ),
                stage="projects",
                operation="initialize-project",
                subject=str(project_root),
                evidence_paths=(str(rollback_root),),
            ) from rollback_error


def initialize_project(
    request: ProjectInitializationRequest,
    *,
    template_source: ProjectTemplateSource,
    filesystem: ProjectFilesystem,
    config_writer: ProjectConfigWriter,
) -> ProjectInitializationResult:
    """Initialize the canonical active project through explicit ports."""

    return ProjectInitializer(
        template_source=template_source,
        filesystem=filesystem,
        config_writer=config_writer,
    ).initialize(request)


def _staged_configuration(
    config: ProjectConfig,
    *,
    stage_root: Path,
) -> ProjectConfig:
    return replace(
        config,
        project_file=stage_root / _PROJECT_FILENAME,
        project_root=stage_root,
        source_root=stage_root / config.sources.directory,
    )


def _require_matching_configuration(
    config: ProjectConfig,
    *,
    project_root: Path,
) -> None:
    expected_project_file = project_root / _PROJECT_FILENAME
    expected_source_root = project_root / config.sources.directory

    mismatches: list[str] = []
    if config.project_root != project_root:
        mismatches.append(
            f"project_root={config.project_root!s}"
        )
    if config.project_file != expected_project_file:
        mismatches.append(
            f"project_file={config.project_file!s}"
        )
    if config.source_root != expected_source_root:
        mismatches.append(
            f"source_root={config.source_root!s}"
        )

    if mismatches:
        raise ProjectConfigurationError(
            "The supplied project configuration belongs to another project root",
            code="GF-WB-PROJECT-INIT-009",
            detail="; ".join(mismatches),
            stage="projects",
            operation="initialize-project",
            subject=str(expected_project_file),
        )


def _inventory_layout(
    inventory: tuple[TreeEntry, ...],
    *,
    owner: str,
) -> dict[PurePosixPath, TreeEntryKind]:
    if not isinstance(inventory, tuple):
        raise TypeError(f"{owner} inventory must be a tuple")

    layout: dict[PurePosixPath, TreeEntryKind] = {}

    for entry in inventory:
        if not isinstance(entry, TreeEntry):
            raise ContractViolationError(
                f"{owner} returned a non-TreeEntry inventory value"
            )

        relative_path = _validated_relative_path(entry.relative_path)
        if entry.kind not in {
            TreeEntryKind.FILE,
            TreeEntryKind.DIRECTORY,
        }:
            raise ContractViolationError(
                f"{owner} contains an unsupported filesystem node",
                subject=relative_path.as_posix(),
            )

        if relative_path in layout:
            raise ContractViolationError(
                f"{owner} contains a duplicate relative path",
                subject=relative_path.as_posix(),
            )

        layout[relative_path] = entry.kind

    return dict(
        sorted(
            layout.items(),
            key=lambda item: item[0].as_posix(),
        )
    )


def _require_canonical_template(
    layout: Mapping[PurePosixPath, TreeEntryKind],
) -> None:
    if not layout:
        raise ProjectConfigurationError(
            "The canonical project template is empty",
            code="GF-WB-PROJECT-INIT-010",
            stage="projects",
            operation="initialize-project",
        )

    project_file = PurePosixPath(_PROJECT_FILENAME)
    if layout.get(project_file) is not TreeEntryKind.FILE:
        raise ProjectConfigurationError(
            "The canonical project template does not contain project.toml",
            code="GF-WB-PROJECT-INIT-011",
            stage="projects",
            operation="initialize-project",
            subject=_PROJECT_FILENAME,
        )


def _require_matching_layout(
    *,
    expected: Mapping[PurePosixPath, TreeEntryKind],
    observed: Mapping[PurePosixPath, TreeEntryKind],
    subject: Path,
) -> None:
    if expected == observed:
        return

    expected_paths = set(expected)
    observed_paths = set(observed)

    missing = sorted(
        (path.as_posix() for path in expected_paths - observed_paths)
    )
    unexpected = sorted(
        (path.as_posix() for path in observed_paths - expected_paths)
    )
    changed = sorted(
        path.as_posix()
        for path in expected_paths & observed_paths
        if expected[path] is not observed[path]
    )

    details: list[str] = []
    if missing:
        details.append("missing=" + ", ".join(missing))
    if unexpected:
        details.append("unexpected=" + ", ".join(unexpected))
    if changed:
        details.append("kind-changed=" + ", ".join(changed))

    raise ContractViolationError(
        "The materialized project does not match the canonical template layout",
        code="GF-WB-PROJECT-INIT-012",
        detail="; ".join(details),
        stage="projects",
        operation="initialize-project",
        subject=str(subject),
    )


def _created_files(
    layout: Mapping[PurePosixPath, TreeEntryKind],
) -> tuple[PurePosixPath, ...]:
    return tuple(
        path
        for path, kind in layout.items()
        if kind is TreeEntryKind.FILE
    )


def _assert_stage(stage: _ProjectTemplateStage) -> None:
    if stage.project_file != stage.root / _PROJECT_FILENAME:
        raise ContractViolationError(
            "The project stage has a noncanonical project.toml path",
            subject=str(stage.project_file),
        )

    if PurePosixPath(_PROJECT_FILENAME) not in stage.created_files:
        raise ContractViolationError(
            "The project stage does not contain project.toml",
            subject=str(stage.root),
        )


def _find_unresolved_placeholders(
    stage: _ProjectTemplateStage,
    *,
    filesystem: ProjectFilesystem,
) -> tuple[str, ...]:
    unresolved: set[str] = set()

    for relative_path in stage.created_files:
        if relative_path.suffix.lower() not in _TEXT_SUFFIXES:
            continue

        path = stage.root.joinpath(*relative_path.parts)
        try:
            content = filesystem.read_text(path, encoding="utf-8")
        except UnicodeError as error:
            raise ProjectConfigurationError(
                "A textual project-template asset is not valid UTF-8",
                code="GF-WB-PROJECT-INIT-013",
                detail=f"{type(error).__name__}: {error}",
                stage="projects",
                operation="initialize-project",
                subject=str(path),
            ) from error

        unresolved.update(_PLACEHOLDER_REFERENCE.findall(content))

    return tuple(sorted(unresolved))


def _raise_for_validation(
    validation: ProjectValidationResult,
    *,
    subject: Path,
) -> None:
    if validation.ok:
        return

    errors = validation.errors
    detail = "; ".join(
        f"{item.code} {item.field}: {item.message}"
        for item in errors[:_MAX_VALIDATION_ERRORS]
    )

    if len(errors) > _MAX_VALIDATION_ERRORS:
        detail += (
            f"; and {len(errors) - _MAX_VALIDATION_ERRORS} "
            "additional error(s)"
        )

    raise ProjectConfigurationError(
        "Project initialization validation failed",
        code="GF-WB-PROJECT-INIT-014",
        detail=detail,
        stage="projects",
        operation="initialize-project",
        subject=str(subject),
    )


def _raise_for_placeholders(
    unresolved: tuple[str, ...],
    *,
    required: bool,
    subject: Path,
) -> None:
    if not required or not unresolved:
        return

    raise ContractViolationError(
        "Project initialization left unresolved placeholders",
        code="GF-WB-PROJECT-INIT-015",
        detail=", ".join(unresolved),
        stage="projects",
        operation="initialize-project",
        subject=str(subject),
    )


def _discard_if_present(
    path: Path,
    *,
    filesystem: ProjectFilesystem,
) -> None:
    try:
        if filesystem.exists(path):
            filesystem.remove_tree(path)
    except Exception:
        # Cleanup must not hide the original initialization failure.
        pass


def _validated_absolute_path(
    value: Path,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in os.fspath(value):
        raise ValueError(f"{field_name} cannot contain NUL characters")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")

    normalized = Path(os.path.normpath(os.fspath(value)))
    if normalized != value:
        raise ValueError(f"{field_name} must be lexically normalized")

    return value


def _normalized_template_values(
    values: Mapping[str, str],
) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError("template_values must be a mapping")

    normalized: dict[str, str] = {}

    for token, replacement in values.items():
        if (
            not isinstance(token, str)
            or _PLACEHOLDER_TOKEN.fullmatch(token) is None
        ):
            raise ValueError(
                "template replacement keys must use "
                "the form <UPPER_SNAKE_CASE>"
            )
        if not isinstance(replacement, str):
            raise TypeError(
                f"replacement for {token} must be a string"
            )
        if not replacement.strip():
            raise ValueError(
                f"replacement for {token} cannot be empty"
            )
        if "\x00" in replacement:
            raise ValueError(
                f"replacement for {token} cannot contain NUL characters"
            )

        normalized[token] = replacement

    return dict(sorted(normalized.items()))


def _validated_relative_path(value: Path) -> PurePosixPath:
    if not isinstance(value, Path):
        raise TypeError(
            "project inventory paths must be pathlib.Path values"
        )

    rendered = value.as_posix()
    relative_path = PurePosixPath(rendered)

    if (
        value.is_absolute()
        or relative_path.is_absolute()
        or not relative_path.parts
        or rendered in {"", "."}
        or "\\" in rendered
        or "\x00" in rendered
        or any(part in {"", ".", ".."} for part in relative_path.parts)
    ):
        raise ContractViolationError(
            "Project inventory contains an unsafe relative path",
            subject=rendered,
        )

    return relative_path


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a boolean")