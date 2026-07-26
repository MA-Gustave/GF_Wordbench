"""Canonical active-project path derivation.

The projects module owns the active-project boundary. This module translates
portable project declarations into absolute lexical paths without performing
filesystem I/O. Existence, file type, symlink, junction, and reparse-point
checks belong to the concrete filesystem adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

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
        return cls(
            root=root,
            config_file=root / PROJECT_CONFIG_FILENAME,
            readme_file=root / PROJECT_README_FILENAME,
            docs_dir=root / PROJECT_DOCS_DIRECTORY,
            validation_dir=root / PROJECT_VALIDATION_DIRECTORY,
            scenarios_dir=(
                root / PROJECT_VALIDATION_DIRECTORY / PROJECT_SCENARIOS_DIRECTORY
            ),
            gold_dir=root / PROJECT_VALIDATION_DIRECTORY / PROJECT_GOLD_DIRECTORY,
            inputs_dir=root / PROJECT_VALIDATION_DIRECTORY / PROJECT_INPUTS_DIRECTORY,
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
        return relative_portable_path(self.root, candidate, role=role, mode=mode)



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
        value,
        role="project.root",
        allow_root=True,
        accept_backslash=False,
    )
    if declaration != PROJECT_ROOT_DECLARATION and not allow_noncanonical:
        raise ContractViolationError(
            "project.root must be '.' for the canonical project schema 1.0 layout"
        )
    return declaration



def resolve_project_relative_path(
    project_root: PathInput,
    value: PathInput,
    *,
    role: str = "project-relative path",
    allow_root: bool = False,
) -> Path:
    """Resolve a portable declaration against the active-project root."""

    root = normalize_environment_path(project_root, role="project root")
    portable = normalize_portable_path(
        value,
        role=role,
        allow_root=allow_root,
        accept_backslash=False,
    )
    candidate = root if portable == PROJECT_ROOT_DECLARATION else root.joinpath(*portable.parts)
    mode = (
        ContainmentMode.INSIDE_OR_EQUAL
        if allow_root
        else ContainmentMode.STRICTLY_INSIDE
    )
    return require_lexical_containment(root, candidate, role=role, mode=mode)



def resolve_source_root(project_root: PathInput, source_directory: PathInput) -> Path:
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
        value,
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



def resolve_module_path(source_root: PathInput, module_path: PathInput) -> Path:
    """Resolve one configured GF entrypoint or checkpoint path."""

    portable = normalize_portable_path(
        module_path,
        role="module path",
        allow_root=False,
        accept_backslash=False,
    )
    if portable.suffix.casefold() != ".gf":
        raise ContractViolationError(
            f"module path must end in '.gf': {portable.as_posix()!r}"
        )
    return resolve_source_relative_path(source_root, portable, role="module path")



def resolve_scenario_path(
    project_paths: ProjectPaths,
    scenario_id: str,
) -> Path:
    """Derive the canonical native GF scenario path from its registry ID."""

    identifier = validate_portable_segment(scenario_id, role="scenario ID")
    if identifier.casefold().endswith(".gfs"):
        raise ContractViolationError("scenario ID must not include the '.gfs' suffix")
    return project_paths.scenarios_dir / f"{identifier}.gfs"


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
    "resolve_project_relative_path",
    "resolve_scenario_path",
    "resolve_source_relative_path",
    "resolve_source_root",
]
