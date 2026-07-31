"""Composition boundary for path-resolved GF Wordbench run configuration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
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

# These fallbacks keep the resolver importable during the staged ADR-0015
# migration. The enum should ultimately define both canonical members.
_LANGUAGE_CONTEXT_SOURCE: Final[ConfigurationSource] = getattr(
    ConfigurationSource,
    "LANGUAGE_CONTEXT",
    ConfigurationSource.RUNTIME_DERIVED,
)
_VALIDATION_PROFILE_SOURCE: Final[ConfigurationSource] = getattr(
    ConfigurationSource,
    "VALIDATION_PROFILE",
    getattr(
        ConfigurationSource,
        "PROJECT_TOML",
        ConfigurationSource.RUNTIME_DERIVED,
    ),
)


def resolve_configuration(
    request: ConfigurationResolutionRequest,
) -> ConfigurationResolution:
    """Compose one immutable run configuration under ADR-0015.

    Precedence resolution owns scalar run-option selection. Environment
    resolution owns machine-local executable and output paths. The immutable
    ``ResolvedLanguageContext`` owns active-language and source facts. An
    explicitly loaded validation profile owns only advanced validation policy,
    including checkpoints, entrypoints, scenarios, and release requirements.

    This function performs no language discovery, source enumeration, profile
    loading, filesystem mutation, or GF execution.
    """

    if not isinstance(request, ConfigurationResolutionRequest):
        raise TypeError(
            "request must be a ConfigurationResolutionRequest"
        )

    language_context = getattr(request, "language_context", None)
    validation_profile = getattr(request, "validation_profile", None)

    if language_context is None:
        return ConfigurationResolution(
            configuration=None,
            issues=(_missing_language_context_issue(),),
            provenance=(),
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
            _language_context_provenance(),
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

    try:
        language_directory = _language_directory(language_context)
        profile_values = _resolve_profile_values(
            validation_profile,
            language_directory=language_directory,
        )

        configuration = RunConfig(
            language_context=language_context,
            validation_profile=validation_profile,
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
            selected_checkpoints=profile_values.checkpoints,
            selected_entrypoints=profile_values.entrypoints,
            selected_scenarios=profile_values.scenarios,
            release_requires_pgf=profile_values.release_requires_pgf,
            evidence_level=values.evidence_level,
            compatibility_warnings=_warning_messages(issues),
        )

        provenance_groups: list[
            Iterable[ConfigurationProvenance]
        ] = [base_provenance]
        if validation_profile is not None:
            provenance_groups.append(_validation_profile_provenance())

        provenance = _merge_provenance(*provenance_groups)
    except (AttributeError, TypeError, ValueError) as exc:
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


@dataclass(frozen=True, slots=True)
class _ResolvedProfileValues:
    """Small internal carrier for optional profile-owned policy."""

    checkpoints: tuple[Path, ...]
    entrypoints: tuple[Path, ...]
    scenarios: tuple[str, ...]
    release_requires_pgf: bool


def _resolve_profile_values(
    validation_profile: object | None,
    *,
    language_directory: Path,
) -> _ResolvedProfileValues:
    """Resolve optional profile policy against the active language directory.

    Profile module paths remain relative policy. The resolved language context,
    not the profile, owns the absolute language source directory.
    """

    if validation_profile is None:
        return _ResolvedProfileValues(
            checkpoints=(),
            entrypoints=(),
            scenarios=(),
            release_requires_pgf=False,
        )

    modules = getattr(validation_profile, "modules")
    validation = getattr(validation_profile, "validation")

    return _ResolvedProfileValues(
        checkpoints=_absolute_profile_module_paths(
            language_directory,
            tuple(getattr(modules, "checkpoints")),
        ),
        entrypoints=_absolute_profile_module_paths(
            language_directory,
            tuple(getattr(modules, "entrypoints")),
        ),
        scenarios=tuple(
            str(scenario)
            for scenario in getattr(validation, "all_scenarios")
        ),
        release_requires_pgf=_profile_release_requires_pgf(
            validation
        ),
    )


def _profile_release_requires_pgf(validation: object) -> bool:
    """Return the profile release flag without truthiness coercion."""

    value = getattr(validation, "release_requires_pgf")
    if type(value) is not bool:
        raise TypeError(
            "validation_profile.validation.release_requires_pgf "
            "must be a boolean"
        )
    return value


def _language_directory(language_context: object) -> Path:
    """Return the normalized language directory from the resolved context."""

    value = getattr(language_context, "language_directory", None)
    if not isinstance(value, Path):
        raise TypeError(
            "language_context.language_directory must be a Path"
        )
    if not value.is_absolute():
        raise ValueError(
            "language_context.language_directory must be absolute"
        )
    return value


def _absolute_profile_module_paths(
    language_directory: Path,
    relative_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Compose profile module paths under the resolved language directory.

    This is lexical composition only. Existence, readability, symlink identity,
    and containment remain owned by preflight and the existing path services.
    """

    resolved: list[Path] = []
    for relative_path in relative_paths:
        if not isinstance(relative_path, Path):
            raise TypeError(
                "validation-profile module paths must be Path values"
            )
        if relative_path.is_absolute():
            raise ValueError(
                "validation-profile module paths must be relative"
            )
        if ".." in relative_path.parts:
            raise ValueError(
                "validation-profile module paths must not traverse parents"
            )

        resolved.append(
            language_directory.joinpath(*relative_path.parts)
        )

    return tuple(resolved)


def _language_context_provenance(
) -> tuple[ConfigurationProvenance, ...]:
    """Return provenance for facts owned by ResolvedLanguageContext."""

    return tuple(
        ConfigurationProvenance(
            field_path=field_path,
            source=_LANGUAGE_CONTEXT_SOURCE,
        )
        for field_path in (
            "language_context",
            "language_key",
            "selected_path",
            "language_directory",
            "rgl_source_root",
            "gf_path_requirements",
        )
    )


def _validation_profile_provenance(
) -> tuple[ConfigurationProvenance, ...]:
    """Return provenance for explicitly loaded profile-owned policy."""

    return tuple(
        ConfigurationProvenance(
            field_path=field_path,
            source=_VALIDATION_PROFILE_SOURCE,
        )
        for field_path in (
            "validation_profile",
            "selected_checkpoints",
            "selected_entrypoints",
            "selected_scenarios",
            "release_requires_pgf",
        )
    )


def _missing_language_context_issue() -> ConfigurationIssue:
    """Return the canonical error for run resolution before language startup."""

    return ConfigurationIssue(
        severity=IssueSeverity.ERROR,
        source=ConfigurationSource.STARTUP_OPTION,
        field_path="language_context",
        provided_value=None,
        message=(
            "A resolved language context is required before run "
            "configuration can be composed."
        ),
        remediation=(
            "Select a GF language directory or .gf file and complete "
            "path-resolved language startup first."
        ),
    )


def _composition_issue(
    error: AttributeError | TypeError | ValueError,
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
            "Correct the resolved language context, optional validation "
            "profile, environment, or run options and resolve again."
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
