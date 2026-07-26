"""Composition boundary for GF Wordbench runtime configuration."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Final

from .environment import resolve_environment
from .models import (
    ConfigurationIssue,
    ConfigurationProvenance,
    ConfigurationResolution,
    ConfigurationResolutionRequest,
    IssueSeverity,
    RunConfig,
)
from .precedence import ConfigurationSource, resolve_precedence

_SEVERITY_RANK: Final[dict[IssueSeverity, int]] = {
    IssueSeverity.ERROR: 0,
    IssueSeverity.WARNING: 1,
    IssueSeverity.INFO: 2,
}


def resolve_configuration(
    request: ConfigurationResolutionRequest,
) -> ConfigurationResolution:
    """Resolve and compose the immutable configuration for one execution.

    Precedence resolution owns scalar run-option selection. Environment
    resolution owns machine-local paths and executable discovery. The loaded
    project remains authoritative for module targets, scenarios, and release
    requirements.
    """

    if not isinstance(request, ConfigurationResolutionRequest):
        raise TypeError(
            "request must be a ConfigurationResolutionRequest"
        )

    precedence = resolve_precedence(request)
    environment = resolve_environment(request)

    issues = _ordered_issues(
        (*precedence.issues, *environment.issues)
    )

    try:
        base_provenance = _merge_provenance(
            precedence.provenance,
            environment.provenance,
        )
    except ValueError as exc:
        return ConfigurationResolution(
            configuration=None,
            issues=_ordered_issues(
                (*issues, _composition_issue(exc))
            ),
            provenance=(),
        )

    if (
        precedence.values is None
        or environment.value is None
        or _contains_errors(issues)
    ):
        return ConfigurationResolution(
            configuration=None,
            issues=issues,
            provenance=base_provenance,
        )

    values = precedence.values
    project = request.project

    try:
        configuration = RunConfig(
            project=project,
            environment=environment.value,
            mode=values.mode,
            target=values.target,
            timeout_sec=values.timeout_sec,
            max_files=values.max_files,
            keep_ok_details=values.keep_ok_details,
            diff_previous=values.diff_previous,
            skip_version_probe=values.skip_version_probe,
            no_compile=values.no_compile,
            emit_cpu_stats=values.emit_cpu_stats,
            selected_checkpoints=_absolute_module_paths(
                project.source_root,
                project.modules.checkpoints,
            ),
            selected_entrypoints=_absolute_module_paths(
                project.source_root,
                project.modules.entrypoints,
            ),
            selected_scenarios=tuple(
                str(scenario)
                for scenario in project.validation.all_scenarios
            ),
            release_requires_pgf=(
                project.validation.release_requires_pgf
            ),
            evidence_level=values.evidence_level,
            compatibility_warnings=_warning_messages(issues),
        )

        provenance = _merge_provenance(
            base_provenance,
            _project_provenance(),
        )
    except (TypeError, ValueError) as exc:
        return ConfigurationResolution(
            configuration=None,
            issues=_ordered_issues(
                (*issues, _composition_issue(exc))
            ),
            provenance=base_provenance,
        )

    return ConfigurationResolution(
        configuration=configuration,
        issues=issues,
        provenance=provenance,
    )


def require_configuration(
    request: ConfigurationResolutionRequest,
) -> RunConfig:
    """Resolve configuration or raise the canonical configuration error."""

    return resolve_configuration(request).require()


def _absolute_module_paths(
    source_root: Path,
    relative_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Compose absolute module paths without filesystem access."""

    return tuple(
        source_root.joinpath(*relative_path.parts)
        for relative_path in relative_paths
    )


def _project_provenance() -> tuple[ConfigurationProvenance, ...]:
    """Return provenance for fields owned by project.toml."""

    return (
        ConfigurationProvenance(
            field_path="project",
            source=ConfigurationSource.PROJECT_TOML,
        ),
        ConfigurationProvenance(
            field_path="selected_checkpoints",
            source=ConfigurationSource.PROJECT_TOML,
        ),
        ConfigurationProvenance(
            field_path="selected_entrypoints",
            source=ConfigurationSource.PROJECT_TOML,
        ),
        ConfigurationProvenance(
            field_path="selected_scenarios",
            source=ConfigurationSource.PROJECT_TOML,
        ),
        ConfigurationProvenance(
            field_path="release_requires_pgf",
            source=ConfigurationSource.PROJECT_TOML,
        ),
    )


def _composition_issue(
    error: TypeError | ValueError,
) -> ConfigurationIssue:
    """Convert a composition failure into a structured issue."""

    return ConfigurationIssue(
        severity=IssueSeverity.ERROR,
        source=ConfigurationSource.RUNTIME_DERIVED,
        field_path="configuration",
        provided_value=None,
        message=(
            "The resolved values cannot form a valid RunConfig: "
            f"{error}"
        ),
        remediation=(
            "Correct the reported configuration sources and resolve "
            "the configuration again."
        ),
    )


def _contains_errors(
    issues: Iterable[ConfigurationIssue],
) -> bool:
    return any(
        issue.severity is IssueSeverity.ERROR
        for issue in issues
    )


def _warning_messages(
    issues: Iterable[ConfigurationIssue],
) -> tuple[str, ...]:
    """Return unique warning messages in encounter order."""

    return tuple(
        dict.fromkeys(
            issue.message
            for issue in issues
            if issue.severity is IssueSeverity.WARNING
        )
    )


def _merge_provenance(
    *groups: Iterable[ConfigurationProvenance],
) -> tuple[ConfigurationProvenance, ...]:
    """Merge provenance records and reject conflicting field owners."""

    merged: dict[str, ConfigurationProvenance] = {}

    for group in groups:
        for record in group:
            existing = merged.get(record.field_path)

            if (
                existing is not None
                and existing.source is not record.source
            ):
                raise ValueError(
                    "conflicting provenance for "
                    f"{record.field_path!r}: "
                    f"{existing.source.value!r} and "
                    f"{record.source.value!r}"
                )

            merged[record.field_path] = record

    return tuple(
        merged[field_path]
        for field_path in sorted(merged)
    )


def _ordered_issues(
    issues: Iterable[ConfigurationIssue],
) -> tuple[ConfigurationIssue, ...]:
    """Return deterministic severity-first issue ordering."""

    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                _SEVERITY_RANK[issue.severity],
                issue.field_path,
                issue.source.value,
                issue.message,
            ),
        )
    )


__all__ = (
    "require_configuration",
    "resolve_configuration",
)