"""Read-only validation of a loaded active-project configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from gf_wordbench.kernel.errors import GFWordbenchError, ProjectConfigurationError

from .models import (
    ProjectCheckScope,
    ProjectConfig,
    ProjectDiagnostic,
    ProjectDiagnosticSeverity,
    ProjectValidationResult,
)
from .paths import (
    ProjectPaths,
    resolve_module_path,
    resolve_project_paths,
    resolve_scenario_path,
)
from .policies import (
    REQUIRED_PROJECT_ASSETS,
    find_unresolved_placeholder,
    validate_project_semantics,
)
from .ports import ProjectFilesystem

__all__ = (
    "ProjectValidator",
    "check_project",
    "ensure_project_valid",
    "validate_project",
)

_MAX_ERROR_DETAIL_ITEMS: Final[int] = 8


@dataclass(frozen=True, slots=True)
class ProjectValidator:
    """Filesystem-backed validator used by the canonical project loader."""

    filesystem: ProjectFilesystem

    def validate_for_load(
        self,
        project: ProjectConfig,
    ) -> ProjectValidationResult:
        """Require one fully valid project before returning it from the loader."""

        return ensure_project_valid(
            project,
            self.filesystem,
            scope=ProjectCheckScope.NORMAL,
            strict=True,
        )


def _diagnostic(
    project: ProjectConfig,
    *,
    code: str,
    field: str,
    message: str,
    suggestion: str,
    severity: ProjectDiagnosticSeverity = ProjectDiagnosticSeverity.ERROR,
    subject: Path | None = None,
) -> ProjectDiagnostic:
    return ProjectDiagnostic(
        code=code,
        severity=severity,
        field=field,
        message=message,
        source_file=project.project_file,
        suggestion=suggestion,
        subject=subject,
    )


def _filesystem_error(
    project: ProjectConfig,
    *,
    field: str,
    path: Path,
    error: BaseException,
) -> ProjectDiagnostic:
    return _diagnostic(
        project,
        code="PROJECT_FILESYSTEM_ERROR",
        field=field,
        message=(f"Filesystem validation could not be completed ({type(error).__name__})."),
        suggestion=("Correct permissions or filesystem state, then repeat the check."),
        subject=path,
    )


def _outside_diagnostic(
    project: ProjectConfig,
    *,
    field: str,
    path: Path,
    kind: str,
    root_name: str,
) -> ProjectDiagnostic:
    return _diagnostic(
        project,
        code="PROJECT_SOURCE_ROOT_OUTSIDE",
        field=field,
        message=f"Configured {kind} resolves outside the {root_name}.",
        suggestion=(f"Use a project-relative path contained beneath the {root_name}."),
        subject=path,
    )


def _check_project_paths(
    project: ProjectConfig,
    project_paths: ProjectPaths,
    filesystem: ProjectFilesystem,
) -> list[ProjectDiagnostic]:
    diagnostics: list[ProjectDiagnostic] = []

    try:
        config_file = filesystem.resolve(project_paths.config_file)
        config_parent = filesystem.resolve(project_paths.config_file.parent)
        project_root = filesystem.resolve(project_paths.root)
        source_root = filesystem.resolve(project.source_root)
    except (OSError, GFWordbenchError) as error:
        return [
            _filesystem_error(
                project,
                field="project",
                path=project.project_file,
                error=error,
            )
        ]

    try:
        config_exists = filesystem.exists(config_file) and filesystem.is_file(config_file)
    except (OSError, GFWordbenchError) as error:
        diagnostics.append(
            _filesystem_error(
                project,
                field="project_file",
                path=config_file,
                error=error,
            )
        )
    else:
        if not config_exists:
            diagnostics.append(
                _diagnostic(
                    project,
                    code="PROJECT_CONFIG_MISSING",
                    field="project_file",
                    message=("Canonical project.toml does not exist as a regular file."),
                    suggestion=("Restore project/project.toml at the configured location."),
                    subject=config_file,
                )
            )

    if project_root != config_parent:
        diagnostics.append(
            _diagnostic(
                project,
                code="PROJECT_ROOT_INVALID",
                field="project.root",
                message=(
                    "Schema 1.0 requires the project root to equal the directory "
                    "containing project.toml."
                ),
                suggestion=("Keep project.root = '.' and resolve it from project.toml."),
                subject=project_root,
            )
        )

    try:
        filesystem.require_contained(
            source_root,
            root=project_root,
            allow_root=False,
        )
    except (ProjectConfigurationError, ValueError):
        diagnostics.append(
            _outside_diagnostic(
                project,
                field="sources.directory",
                path=source_root,
                kind="source root",
                root_name="active project root",
            )
        )
        return diagnostics
    except (OSError, GFWordbenchError) as error:
        diagnostics.append(
            _filesystem_error(
                project,
                field="sources.directory",
                path=source_root,
                error=error,
            )
        )
        return diagnostics

    try:
        source_exists = filesystem.exists(source_root) and filesystem.is_directory(source_root)
    except (OSError, GFWordbenchError) as error:
        diagnostics.append(
            _filesystem_error(
                project,
                field="sources.directory",
                path=source_root,
                error=error,
            )
        )
    else:
        if not source_exists:
            diagnostics.append(
                _diagnostic(
                    project,
                    code="PROJECT_SOURCE_ROOT_MISSING",
                    field="sources.directory",
                    message=("Configured source root does not exist as a directory."),
                    suggestion=("Create the source directory or correct project.toml."),
                    subject=source_root,
                )
            )

    return diagnostics


def _check_modules(
    project: ProjectConfig,
    filesystem: ProjectFilesystem,
) -> list[ProjectDiagnostic]:
    diagnostics: list[ProjectDiagnostic] = []

    try:
        source_root = filesystem.resolve(project.source_root)
    except (OSError, GFWordbenchError) as error:
        return [
            _filesystem_error(
                project,
                field="sources.directory",
                path=project.source_root,
                error=error,
            )
        ]

    groups = (
        ("entrypoint", "modules.entrypoints", project.modules.entrypoints),
        ("checkpoint", "modules.checkpoints", project.modules.checkpoints),
    )

    for kind, field, targets in groups:
        missing_code = (
            "PROJECT_ENTRYPOINT_MISSING" if kind == "entrypoint" else "PROJECT_CHECKPOINT_MISSING"
        )

        for index, target in enumerate(targets):
            item_field = f"{field}[{index}]"
            path = resolve_module_path(project.source_root, target)

            try:
                resolved = filesystem.resolve(path)
                filesystem.require_contained(
                    resolved,
                    root=source_root,
                    allow_root=False,
                )
            except (ProjectConfigurationError, ValueError):
                diagnostics.append(
                    _outside_diagnostic(
                        project,
                        field=item_field,
                        path=path,
                        kind=kind,
                        root_name="source root",
                    )
                )
                continue
            except (OSError, GFWordbenchError) as error:
                diagnostics.append(
                    _filesystem_error(
                        project,
                        field=item_field,
                        path=path,
                        error=error,
                    )
                )
                continue

            try:
                present = filesystem.exists(path) and filesystem.is_file(path)
            except (OSError, GFWordbenchError) as error:
                diagnostics.append(
                    _filesystem_error(
                        project,
                        field=item_field,
                        path=path,
                        error=error,
                    )
                )
                continue

            if not present:
                diagnostics.append(
                    _diagnostic(
                        project,
                        code=missing_code,
                        field=item_field,
                        message=f"Configured {kind} file does not exist.",
                        suggestion=("Create the declared module or correct project.toml."),
                        subject=path,
                    )
                )

    return diagnostics


def _check_scenarios(
    project: ProjectConfig,
    project_paths: ProjectPaths,
    filesystem: ProjectFilesystem,
) -> list[ProjectDiagnostic]:
    diagnostics: list[ProjectDiagnostic] = []
    groups = (
        (
            True,
            "validation.required_scenarios",
            project.validation.required_scenarios,
        ),
        (
            False,
            "validation.optional_scenarios",
            project.validation.optional_scenarios,
        ),
    )

    for required, field, scenario_ids in groups:
        for index, scenario_id in enumerate(scenario_ids):
            path = resolve_scenario_path(project_paths, str(scenario_id))

            try:
                present = filesystem.exists(path) and filesystem.is_file(path)
            except (OSError, GFWordbenchError) as error:
                diagnostics.append(
                    _filesystem_error(
                        project,
                        field=f"{field}[{index}]",
                        path=path,
                        error=error,
                    )
                )
                continue

            if not present:
                diagnostics.append(
                    _diagnostic(
                        project,
                        code="PROJECT_SCENARIO_MISSING",
                        field=f"{field}[{index}]",
                        message=(
                            f"Registered {'required' if required else 'optional'} "
                            "scenario is missing."
                        ),
                        suggestion=("Create the canonical .gfs asset or correct the registry."),
                        severity=(
                            ProjectDiagnosticSeverity.ERROR
                            if required
                            else ProjectDiagnosticSeverity.WARNING
                        ),
                        subject=path,
                    )
                )

    return diagnostics


def _check_required_assets(
    project: ProjectConfig,
    project_paths: ProjectPaths,
    filesystem: ProjectFilesystem,
    *,
    inspect_placeholders: bool,
) -> list[ProjectDiagnostic]:
    diagnostics: list[ProjectDiagnostic] = []

    for relative_path in REQUIRED_PROJECT_ASSETS:
        path = project_paths.root / relative_path

        try:
            present = filesystem.exists(path) and filesystem.is_file(path)
            if not present:
                diagnostics.append(
                    _diagnostic(
                        project,
                        code="PROJECT_DOCUMENT_MISSING",
                        field=relative_path.as_posix(),
                        message=(
                            "Required active-project authority or validation guide is missing."
                        ),
                        suggestion=(
                            "Restore the canonical project asset and synchronize it "
                            "with project.toml."
                        ),
                        subject=path,
                    )
                )
                continue

            if not inspect_placeholders or path.suffix.lower() != ".md":
                continue

            text = filesystem.read_text(path, encoding="utf-8")
        except (OSError, UnicodeError, GFWordbenchError) as error:
            diagnostics.append(
                _filesystem_error(
                    project,
                    field=relative_path.as_posix(),
                    path=path,
                    error=error,
                )
            )
            continue

        placeholder = find_unresolved_placeholder(text)
        if placeholder is not None:
            diagnostics.append(
                _diagnostic(
                    project,
                    code="PROJECT_PLACEHOLDER_UNRESOLVED",
                    field=relative_path.as_posix(),
                    message=(
                        "Required project document contains unresolved placeholder "
                        f"'{placeholder}'."
                    ),
                    suggestion=(
                        "Replace the placeholder with reviewed active-project information."
                    ),
                    subject=path,
                )
            )

    return diagnostics


def validate_project(
    project: ProjectConfig,
    filesystem: ProjectFilesystem,
    *,
    scope: ProjectCheckScope = ProjectCheckScope.NORMAL,
    strict: bool = False,
) -> ProjectValidationResult:
    """Validate one immutable project without executing GF or changing assets."""

    if not isinstance(project, ProjectConfig):
        raise TypeError("project must be ProjectConfig")
    if not isinstance(scope, ProjectCheckScope):
        raise TypeError("scope must be a ProjectCheckScope")
    if type(strict) is not bool:
        raise TypeError("strict must be a bool")

    diagnostics = list(validate_project_semantics(project, strict=strict))

    if scope is ProjectCheckScope.CONFIGURATION:
        return ProjectValidationResult(tuple(diagnostics))

    project_paths = resolve_project_paths(project)
    diagnostics.extend(_check_project_paths(project, project_paths, filesystem))
    diagnostics.extend(_check_modules(project, filesystem))
    diagnostics.extend(
        _check_scenarios(
            project,
            project_paths,
            filesystem,
        )
    )
    diagnostics.extend(
        _check_required_assets(
            project,
            project_paths,
            filesystem,
            inspect_placeholders=(strict or scope is ProjectCheckScope.RELEASE),
        )
    )

    return ProjectValidationResult(tuple(diagnostics))


def check_project(
    project: ProjectConfig,
    filesystem: ProjectFilesystem,
    *,
    scope: ProjectCheckScope = ProjectCheckScope.NORMAL,
    strict: bool = False,
) -> ProjectValidationResult:
    """Run the canonical read-only project check."""

    return validate_project(
        project,
        filesystem,
        scope=scope,
        strict=strict,
    )


def ensure_project_valid(
    project: ProjectConfig,
    filesystem: ProjectFilesystem,
    *,
    scope: ProjectCheckScope = ProjectCheckScope.NORMAL,
    strict: bool = False,
) -> ProjectValidationResult:
    """Return a valid result or raise one bounded project-configuration error."""

    result = validate_project(
        project,
        filesystem,
        scope=scope,
        strict=strict,
    )
    if result.ok:
        return result

    errors = result.errors
    detail = "; ".join(
        f"{item.code} {item.field}: {item.message}" for item in errors[:_MAX_ERROR_DETAIL_ITEMS]
    )
    if len(errors) > _MAX_ERROR_DETAIL_ITEMS:
        detail += f"; and {len(errors) - _MAX_ERROR_DETAIL_ITEMS} additional error(s)"

    raise ProjectConfigurationError(
        "Active project validation failed",
        code="GF-WB-PROJECT-001",
        detail=detail,
        stage="projects",
        operation="validate-project",
        subject=str(project.project_file),
    )
