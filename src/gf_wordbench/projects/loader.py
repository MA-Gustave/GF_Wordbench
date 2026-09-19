"""Load one active GF Wordbench project from its authoritative TOML file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from gf_wordbench.kernel.errors import ProjectConfigurationError

from .models import ProjectConfig
from .paths import PROJECT_CONFIG_FILENAME
from .policies import enforce_project_invariants
from .ports import ProjectConfigReader
from .schema import ProjectDocument, parse_project_document
from .validator import ProjectValidator

__all__ = (
    "ProjectLoader",
    "load_project_config",
)


@dataclass(frozen=True, slots=True)
class ProjectLoader:
    """Construct a fully validated immutable active-project configuration.

    The loader coordinates read-only project loading. It does not execute GF,
    create directories, rewrite ``project.toml``, consult application state, or
    infer project facts from historical runs.

    ``ProjectConfigReader`` owns transport and TOML decoding.
    ``parse_project_document`` owns schema validation and model construction.
    ``ProjectValidator`` owns filesystem-backed load validation.
    """

    reader: ProjectConfigReader
    validator: ProjectValidator

    def load(self, project_file: Path) -> ProjectConfig:
        """Load one project from an explicit absolute ``project.toml`` path."""

        source = _require_explicit_project_file(project_file)

        document = self.reader.read(source)
        # The schema parser owns runtime validation of the decoded mapping.
        # The cast only reconciles its narrower TypedDict annotation with the
        # transport port while preserving the original document identity.
        project = parse_project_document(
            cast(ProjectDocument, document),
            source_file=source,
        )

        enforce_project_invariants(project)
        self.validator.validate_for_load(project)

        return project


def load_project_config(
    project_file: Path,
    *,
    reader: ProjectConfigReader,
    validator: ProjectValidator,
) -> ProjectConfig:
    """Load and validate one active project through composed services."""

    return ProjectLoader(
        reader=reader,
        validator=validator,
    ).load(project_file)


def _require_explicit_project_file(project_file: Path) -> Path:
    """Validate the explicit active-project configuration path."""

    if not isinstance(project_file, Path):
        raise TypeError("project_file must be pathlib.Path")

    rendered = str(project_file)
    if "\x00" in rendered:
        raise ProjectConfigurationError(
            "project_file must not contain a NUL character",
            subject="<invalid project path>",
        )

    if not project_file.is_absolute():
        raise ProjectConfigurationError(
            "project.toml must be supplied as an explicit absolute path; "
            "relative paths must not be resolved from the process working directory",
            subject=rendered,
        )

    if ".." in project_file.parts:
        raise ProjectConfigurationError(
            "project_file must be lexically normalized and must not contain '..'",
            subject=rendered,
        )

    if project_file.name != PROJECT_CONFIG_FILENAME:
        raise ProjectConfigurationError(
            f"project_file must name {PROJECT_CONFIG_FILENAME!r}",
            subject=rendered,
        )

    return project_file
