"""Canonical active-project path derivation.

The projects module owns the active-project boundary. This module translates
portable project declarations into absolute lexical paths without performing
filesystem I/O. Existence, file type, symlink, junction, and reparse-point
checks belong to the concrete filesystem adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING, Final

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    PathInput,
    normalize_environment_path,
    normalize_portable_path,
    relative_portable_path,
    require_lexical_containment,
    validate_portable_segment,
)

if TYPE_CHECKING:
    from .models import ProjectConfig

PROJECT_CONFIG_FILENAME: Final[str] = "project.toml"
PROJECT_README_FILENAME: Final[str] = "README.md"
PROJECT_DOCS_DIRECTORY: Final[str] = "docs"
PROJECT_VALIDATION_DIRECTORY: Final[str] = "validation"
PROJECT_SCENARIOS_DIRECTORY: Final[str] = "scenarios"
PROJECT_GOLD_DIRECTORY: Final[str] = "gold"
PROJECT_INPUTS_DIRECTORY: Final[str] = "inputs"
PROJECT_ROOT_DECLARATION: Final[PurePosixPath] = PurePosixPath(".")


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Absolute lexical paths derived from one immutable active-project root."""

    root: Path
    config_file: Path
    readme_file: Path
    docs_dir: Path
    validation_dir: Path
    scenarios_dir: Path
    gold_dir: Path
    inputs_dir: Path

    @classmethod
    def from_root(cls, project_root: PathInput) -> ProjectPaths:
        """Build the canonical project layout from an absolute project root."""

        root = normalize_environment_path(project_root, role="project root")
        validation_dir = root / PROJECT_VALIDATION_DIRECTORY
        return cls(
            root=root,
            config_file=root / PROJECT_CONFIG_FILENAME,
            readme_file=root / PROJECT_README_FILENAME,
            docs_dir=root / PROJECT_DOCS_DIRECTORY,
            validation_dir=validation_dir,
            scenarios_dir=validation_dir / PROJECT_SCENARIOS_DIRECTORY,
            gold_dir=validation_dir / PROJECT_GOLD_DIRECTORY,
            inputs_dir=validation_dir / PROJECT_INPUTS_DIRECTORY,
        )

    def resolve_project_path(
        self,
        value: PathInput,
        *,
        role: str = "project-relative path",
        allow_root: bool = False,
    ) -> Path:
        """Resolve a portable path beneath the active-project root."""

        return resolve_project_relative_path(
            self.root,
            value,
            role=role,
            allow_root=allow_root,
        )

    def relative_path(
        self,
        candidate: PathInput,
        *,
        role: str = "project path",
        allow_root: bool = True,
    ) -> PurePosixPath:
        """Return a canonical project-relative representation of a path."""

        mode = (
            ContainmentMode.INSIDE_OR_EQUAL
            if allow_root
            else ContainmentMode.STRICTLY_INSIDE
        )
        return relative_portable_path(
            self.root,
            candidate,
            role=role,
            mode=mode,
        )


def resolve_project_paths(config: ProjectConfig) -> ProjectPaths:
    """Derive and verify canonical paths for one loaded project configuration.

    The local import avoids a module-import cycle because ``models`` consumes
    ``PROJECT_CONFIG_FILENAME`` from this module.
    """

    from .models import ProjectConfig

    if not isinstance(config, ProjectConfig):
        raise TypeError("config must be ProjectConfig")

    paths = ProjectPaths.from_root(config.project_root)

    if config.project_file != paths.config_file:
        raise ContractViolationError(
            "config.project_file must equal project_root/project.toml"
        )

    expected_source_root = resolve_source_root(
        paths.root,
        config.sources.directory,
    )
    if config.source_root != expected_source_root:
        raise ContractViolationError(
            "config.source_root must equal "
            "project_root / config.sources.directory"
        )

    return paths


def normalize_project_root_declaration(
    value: PathInput,
    *,
    allow_noncanonical: bool = False,
) -> PurePosixPath:
    """Validate ``[project].root`` for project schema ``1.0``.

    The canonical value is ``.``. A non-dot value is accepted only by an
    explicitly reviewed migration or alternate-layout boundary.
    """

    declaration = normalize_portable_path(
        _portable_declaration_input(value),
        role="project.root",
        allow_root=True,
        accept_backslash=False,
    )
    if declaration != PROJECT_ROOT_DECLARATION and not allow_noncanonical:
        raise ContractViolationError(
            "project.root must be '.' for the canonical "
            "project schema 1.0 layout"
        )
    return declaration


def resolve_project_relative_path(
    project_root: PathInput,
    value: PathInput,
    *,
    role: str = "project-relative path",
    allow_root: bool = False,
) -> Path:
    """Resolve a portable declaration against the active-project root.

    Raw text remains subject to canonical ``/`` separator validation. A
    ``PurePath`` value is already a runtime path object, so its native separator
    spelling is normalized with ``as_posix()`` before portable validation.
    """

    root = normalize_environment_path(project_root, role="project root")
    portable = normalize_portable_path(
        _portable_declaration_input(value),
        role=role,
        allow_root=allow_root,
        accept_backslash=False,
    )
    candidate = (
        root
        if portable == PROJECT_ROOT_DECLARATION
        else root.joinpath(*portable.parts)
    )
    mode = (
        ContainmentMode.INSIDE_OR_EQUAL
        if allow_root
        else ContainmentMode.STRICTLY_INSIDE
    )
    return require_lexical_containment(
        root,
        candidate,
        role=role,
        mode=mode,
    )


def resolve_source_root(
    project_root: PathInput,
    source_directory: PathInput,
) -> Path:
    """Resolve ``[sources].directory`` beneath the active-project root."""

    return resolve_project_relative_path(
        project_root,
        source_directory,
        role="sources.directory",
        allow_root=False,
    )


def resolve_source_relative_path(
    source_root: PathInput,
    value: PathInput,
    *,
    role: str = "source-relative path",
) -> Path:
    """Resolve a portable file or directory path beneath the source root."""

    root = normalize_environment_path(source_root, role="source root")
    portable = normalize_portable_path(
        _portable_declaration_input(value),
        role=role,
        allow_root=False,
        accept_backslash=False,
    )
    candidate = root.joinpath(*portable.parts)
    return require_lexical_containment(
        root,
        candidate,
        role=role,
        mode=ContainmentMode.STRICTLY_INSIDE,
    )


def resolve_module_path(
    source_root: PathInput,
    module_path: PathInput,
) -> Path:
    """Resolve one configured GF entrypoint or checkpoint path."""

    portable = normalize_portable_path(
        _portable_declaration_input(module_path),
        role="module path",
        allow_root=False,
        accept_backslash=False,
    )
    if portable.suffix.casefold() != ".gf":
        raise ContractViolationError(
            f"module path must end in '.gf': {portable.as_posix()!r}"
        )
    return resolve_source_relative_path(
        source_root,
        portable,
        role="module path",
    )


def resolve_scenario_path(
    project_paths: ProjectPaths,
    scenario_id: str,
) -> Path:
    """Derive the canonical native GF scenario path from its registry ID."""

    if not isinstance(project_paths, ProjectPaths):
        raise TypeError("project_paths must be ProjectPaths")

    identifier = validate_portable_segment(
        scenario_id,
        role="scenario ID",
    )
    if identifier.casefold().endswith(".gfs"):
        raise ContractViolationError(
            "scenario ID must not include the '.gfs' suffix"
        )
    return project_paths.scenarios_dir / f"{identifier}.gfs"


def _portable_declaration_input(value: PathInput) -> PathInput:
    """Normalize runtime path objects without relaxing raw-text validation."""

    if isinstance(value, PurePath):
        return value.as_posix()
    return value


__all__ = [
    "PROJECT_CONFIG_FILENAME",
    "PROJECT_DOCS_DIRECTORY",
    "PROJECT_GOLD_DIRECTORY",
    "PROJECT_INPUTS_DIRECTORY",
    "PROJECT_README_FILENAME",
    "PROJECT_ROOT_DECLARATION",
    "PROJECT_SCENARIOS_DIRECTORY",
    "PROJECT_VALIDATION_DIRECTORY",
    "ProjectPaths",
    "normalize_project_root_declaration",
    "resolve_module_path",
    "resolve_project_paths",
    "resolve_project_relative_path",
    "resolve_scenario_path",
    "resolve_source_relative_path",
    "resolve_source_root",
]
