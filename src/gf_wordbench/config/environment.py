"""Read and resolve GF Wordbench process-environment configuration."""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Final

from .models import (
    ConfigurationIssue,
    ConfigurationProvenance,
    ConfigurationResolutionRequest,
    EnvironmentOverrides,
    EnvironmentResolution,
    IssueSeverity,
    ResolvedEnvironment,
)
from .precedence import (
    ConfigurationSource,
    PrecedenceResolution,
    resolve_precedence,
)

ENVIRONMENT_PREFIX: Final[str] = "GF_WORDBENCH_"

PROJECT_ROOT_ENV: Final[str] = "GF_WORDBENCH_PROJECT_ROOT"
GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_GF_EXE"
RGL_ROOT_ENV: Final[str] = "GF_WORDBENCH_RGL_ROOT"
OUTPUT_ROOT_ENV: Final[str] = "GF_WORDBENCH_OUTPUT_ROOT"
STATE_PATH_ENV: Final[str] = "GF_WORDBENCH_STATE_PATH"

CANONICAL_ENVIRONMENT_VARIABLES: Final[tuple[str, ...]] = (
    PROJECT_ROOT_ENV,
    GF_EXECUTABLE_ENV,
    RGL_ROOT_ENV,
    OUTPUT_ROOT_ENV,
    STATE_PATH_ENV,
)

_GF_EXECUTABLE_NAMES: Final = frozenset({"gf", "gf.exe"})
_ENV_REFERENCE_PATTERNS: Final = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[^{}]+\}"),
    re.compile(r"(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*"),
)

_PathValidator = Callable[[Path], bool]


def read_environment(
    environ: Mapping[str, str] | None = None,
) -> EnvironmentOverrides:
    """Return documented raw overrides without resolving their values."""

    source = os.environ if environ is None else _require_mapping(environ)
    return EnvironmentOverrides(
        project_root=_optional_value(source, PROJECT_ROOT_ENV),
        gf_executable=_optional_value(source, GF_EXECUTABLE_ENV),
        rgl_root=_optional_value(source, RGL_ROOT_ENV),
        output_root=_optional_value(source, OUTPUT_ROOT_ENV),
        state_path=_optional_value(source, STATE_PATH_ENV),
    )


def find_unknown_environment_variables(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Return unknown non-empty names in the reserved environment namespace."""

    source = os.environ if environ is None else _require_mapping(environ)
    known = frozenset(CANONICAL_ENVIRONMENT_VARIABLES)
    unknown: list[str] = []

    for name, value in source.items():
        if not isinstance(name, str):
            raise TypeError("environment variable names must be strings")
        if not name.startswith(ENVIRONMENT_PREFIX):
            continue

        checked = _require_string(name, value)
        if name not in known and checked:
            unknown.append(name)

    return tuple(sorted(unknown))


def resolve_environment(
    request: ConfigurationResolutionRequest,
) -> EnvironmentResolution:
    """Resolve and validate the machine-local environment for one run."""

    if not isinstance(request, ConfigurationResolutionRequest):
        raise TypeError("request must be a ConfigurationResolutionRequest")

    precedence = resolve_precedence(request)
    if precedence.values is None:
        return EnvironmentResolution(
            value=None,
            issues=precedence.issues,
            provenance=precedence.provenance,
        )

    if _has_errors(precedence.issues):
        return EnvironmentResolution(
            value=None,
            issues=_ordered_issues(precedence.issues),
            provenance=precedence.provenance,
        )

    values = precedence.values
    issues = list(precedence.issues)

    project_root = _resolve_required_path(
        field_path="project_root",
        raw_value=values.project_root,
        precedence=precedence,
        issues=issues,
        expected="an existing project directory containing project.toml",
        remediation=(
            "Select the directory containing the active project.toml file."
        ),
        validator=_is_project_root,
    )
    rgl_root = _resolve_required_path(
        field_path="rgl_root",
        raw_value=values.rgl_root,
        precedence=precedence,
        issues=issues,
        expected="an existing RGL source directory",
        remediation=(
            "Select the existing RGL source root used by the active project."
        ),
        validator=Path.is_dir,
    )
    output_root = _resolve_required_path(
        field_path="output_root",
        raw_value=values.output_root,
        precedence=precedence,
        issues=issues,
        expected="an existing writable output directory",
        remediation=(
            "Select or create a writable directory for GF Wordbench runs."
        ),
        validator=_is_writable_directory,
    )
    gf_executable, gf_source = _resolve_gf_executable(
        raw_value=values.gf_executable,
        precedence=precedence,
        issues=issues,
    )

    if project_root is not None:
        loaded_root = _normalize_machine_path(
            request.project.project_root
        )
        if not _same_path(project_root, loaded_root):
            issues.append(
                _error(
                    source=_source_for(
                        precedence,
                        "project_root",
                    ),
                    field_path="project_root",
                    provided_value=values.project_root,
                    message=(
                        "The selected project root does not match the root of "
                        "the loaded project configuration."
                    ),
                    remediation=(
                        "Load project.toml from the same project root selected "
                        "for this run."
                    ),
                )
            )

    gf_path = (
        None
        if rgl_root is None
        else _resolve_gf_path(
            rgl_root=rgl_root,
            path_parts=request.project.gf.path_parts,
            issues=issues,
        )
    )

    if output_root is not None and rgl_root is not None:
        _validate_output_separation(
            output_root=output_root,
            source_root=_normalize_machine_path(
                request.project.source_root
            ),
            rgl_root=rgl_root,
            source=_source_for(
                precedence,
                "output_root",
            ),
            provided_value=values.output_root,
            issues=issues,
        )

    if _has_errors(issues):
        return EnvironmentResolution(
            value=None,
            issues=_ordered_issues(issues),
            provenance=precedence.provenance,
        )

    assert project_root is not None
    assert rgl_root is not None
    assert gf_executable is not None
    assert output_root is not None
    assert gf_path is not None

    resolved_provenance = (
        ConfigurationProvenance(
            field_path="environment.project_root",
            source=_source_for(
                precedence,
                "project_root",
            ),
        ),
        ConfigurationProvenance(
            field_path="environment.rgl_root",
            source=_source_for(
                precedence,
                "rgl_root",
            ),
        ),
        ConfigurationProvenance(
            field_path="environment.gf_executable",
            source=gf_source,
        ),
        ConfigurationProvenance(
            field_path="environment.output_root",
            source=_source_for(
                precedence,
                "output_root",
            ),
        ),
        ConfigurationProvenance(
            field_path="environment.gf_path",
            source=ConfigurationSource.PROJECT_TOML,
        ),
    )

    return EnvironmentResolution(
        value=ResolvedEnvironment(
            project_root=project_root,
            rgl_root=rgl_root,
            gf_executable=gf_executable,
            output_root=output_root,
            gf_path=gf_path,
        ),
        issues=_ordered_issues(issues),
        provenance=_merge_provenance(
            precedence.provenance,
            resolved_provenance,
        ),
    )


def _resolve_required_path(
    *,
    field_path: str,
    raw_value: str | os.PathLike[str] | None,
    precedence: PrecedenceResolution,
    issues: list[ConfigurationIssue],
    expected: str,
    remediation: str,
    validator: _PathValidator,
) -> Path | None:
    source = _source_for(
        precedence,
        field_path,
    )

    if raw_value is None:
        issues.append(
            _error(
                source=source,
                field_path=field_path,
                provided_value=None,
                message=f"No value was resolved for {field_path!r}.",
                remediation=remediation,
            )
        )
        return None

    try:
        path = _normalize_machine_path(raw_value)
        valid = validator(path)
    except (OSError, TypeError, ValueError) as exc:
        issues.append(
            _error(
                source=source,
                field_path=field_path,
                provided_value=raw_value,
                message=(
                    f"The selected {field_path!r} path is invalid: {exc}."
                ),
                remediation=remediation,
            )
        )
        return None

    if not valid:
        issues.append(
            _error(
                source=source,
                field_path=field_path,
                provided_value=raw_value,
                message=(
                    f"The selected {field_path!r} is not "
                    f"{expected}: {path}."
                ),
                remediation=remediation,
            )
        )
        return None

    return path


def _resolve_gf_executable(
    *,
    raw_value: str | os.PathLike[str] | None,
    precedence: PrecedenceResolution,
    issues: list[ConfigurationIssue],
) -> tuple[Path | None, ConfigurationSource]:
    if raw_value is None:
        source = ConfigurationSource.PATH_DISCOVERY
        candidate: str | os.PathLike[str] | None = shutil.which("gf")

        if candidate is None:
            issues.append(
                _error(
                    source=source,
                    field_path="gf_executable",
                    provided_value=None,
                    message=(
                        "No GF executable was selected and bounded PATH "
                        "discovery did not find 'gf'."
                    ),
                    remediation=(
                        f"Set {GF_EXECUTABLE_ENV} or provide an explicit "
                        "path to gf or gf.exe."
                    ),
                )
            )
            return None, source
    else:
        source = _source_for(
            precedence,
            "gf_executable",
        )
        candidate = raw_value

    try:
        executable = _normalize_machine_path(candidate)
    except (OSError, TypeError, ValueError) as exc:
        issues.append(
            _error(
                source=source,
                field_path="gf_executable",
                provided_value=candidate,
                message=(
                    f"The selected GF executable path is invalid: {exc}."
                ),
                remediation=(
                    "Provide an existing executable file named gf or gf.exe."
                ),
            )
        )
        return None, source

    if not _is_gf_executable(executable):
        issues.append(
            _error(
                source=source,
                field_path="gf_executable",
                provided_value=candidate,
                message=(
                    f"The selected GF executable is not usable: "
                    f"{executable}."
                ),
                remediation=(
                    "Provide an existing executable file named gf or gf.exe."
                ),
            )
        )
        return None, source

    return executable, source


def _resolve_gf_path(
    *,
    rgl_root: Path,
    path_parts: Sequence[str],
    issues: list[ConfigurationIssue],
) -> tuple[Path, ...] | None:
    if isinstance(path_parts, (str, bytes)):
        raise TypeError(
            "project.gf.path_parts must be a sequence of strings"
        )

    resolved: list[Path] = []
    seen: set[str] = set()
    initial_error_count = _error_count(issues)

    for index, path_part in enumerate(path_parts):
        field = f"project.gf.path_parts[{index}]"

        try:
            candidate = _resolve_project_path(
                rgl_root,
                path_part,
            )
        except (OSError, TypeError, ValueError) as exc:
            issues.append(
                _error(
                    source=ConfigurationSource.PROJECT_TOML,
                    field_path=field,
                    provided_value=path_part,
                    message=(
                        f"The GF path part cannot be resolved: {exc}."
                    ),
                    remediation=(
                        "Use a valid RGL-root-relative path "
                        "in gf.path_parts."
                    ),
                )
            )
            continue

        if not candidate.is_dir():
            issues.append(
                _error(
                    source=ConfigurationSource.PROJECT_TOML,
                    field_path=field,
                    provided_value=path_part,
                    message=(
                        "The resolved GF path directory does not exist: "
                        f"{candidate}."
                    ),
                    remediation=(
                        "Correct gf.path_parts or select the matching RGL root."
                    ),
                )
            )
            continue

        key = _path_key(candidate)
        if key not in seen:
            seen.add(key)
            resolved.append(candidate)

    return (
        None
        if _error_count(issues) > initial_error_count
        else tuple(resolved)
    )


def _validate_output_separation(
    *,
    output_root: Path,
    source_root: Path,
    rgl_root: Path,
    source: ConfigurationSource,
    provided_value: object,
    issues: list[ConfigurationIssue],
) -> None:
    overlaps: list[str] = []

    if _paths_overlap(output_root, source_root):
        overlaps.append("the project source root")
    if _paths_overlap(output_root, rgl_root):
        overlaps.append("the RGL root")
    if not overlaps:
        return

    issues.append(
        _error(
            source=source,
            field_path="output_root",
            provided_value=provided_value,
            message=(
                "The selected output root overlaps "
                + " and ".join(overlaps)
                + f": {output_root}."
            ),
            remediation=(
                "Select a writable output directory outside project sources "
                "and the RGL tree."
            ),
        )
    )


def _normalize_machine_path(
    value: str | os.PathLike[str],
) -> Path:
    text = _path_text(value)

    if any(
        pattern.search(text)
        for pattern in _ENV_REFERENCE_PATTERNS
    ):
        raise ValueError(
            "inline environment-variable references are not permitted"
        )

    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(
            "machine-local paths must be absolute"
        )

    return path.resolve(strict=False)


def _resolve_project_path(
    root: Path,
    value: str,
) -> Path:
    if not isinstance(value, str):
        raise TypeError("path part must be a string")
    if not value or "\x00" in value:
        raise ValueError(
            "path part must be non-empty and contain no NUL"
        )
    if value == "~" or value.startswith(("~/", "~\\")):
        raise ValueError(
            "project paths must not use home expansion"
        )
    if any(
        pattern.search(value)
        for pattern in _ENV_REFERENCE_PATTERNS
    ):
        raise ValueError(
            "project paths must not contain environment references"
        )

    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(
            "path part must be relative to the RGL root"
        )

    candidate = (root / relative).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError(
            "path part escapes the selected RGL root"
        )

    return candidate


def _path_text(
    value: str | os.PathLike[str],
) -> str:
    if isinstance(value, str):
        text = value
    elif isinstance(value, os.PathLike):
        text = os.fspath(value)
    else:
        raise TypeError(
            "path must be a string or os.PathLike object"
        )

    if not isinstance(text, str):
        raise TypeError("path must resolve to text")
    if not text:
        raise ValueError("path must not be empty")
    if "\x00" in text:
        raise ValueError(
            "path must not contain a NUL character"
        )

    return text


def _is_project_root(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "project.toml").is_file()
    )


def _is_writable_directory(path: Path) -> bool:
    return (
        path.is_dir()
        and os.access(path, os.W_OK)
    )


def _is_gf_executable(path: Path) -> bool:
    return (
        path.is_file()
        and path.name.casefold() in _GF_EXECUTABLE_NAMES
        and os.access(path, os.X_OK)
    )


def _same_path(
    left: Path,
    right: Path,
) -> bool:
    return _path_key(left) == _path_key(right)


def _paths_overlap(
    left: Path,
    right: Path,
) -> bool:
    return (
        _same_path(left, right)
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def _path_key(path: Path) -> str:
    return os.path.normcase(
        os.path.normpath(
            os.fspath(path)
        )
    )


def _source_for(
    resolution: PrecedenceResolution,
    field_path: str,
) -> ConfigurationSource:
    accepted = {
        field_path,
        f"environment.{field_path}",
    }

    for record in resolution.provenance:
        if record.field_path in accepted:
            return record.source

    return ConfigurationSource.RUNTIME_DERIVED


def _merge_provenance(
    *groups: Sequence[ConfigurationProvenance],
) -> tuple[ConfigurationProvenance, ...]:
    merged: dict[str, ConfigurationProvenance] = {}

    for group in groups:
        for record in group:
            merged[record.field_path] = record

    return tuple(
        sorted(
            merged.values(),
            key=lambda record: record.field_path,
        )
    )


def _error(
    *,
    source: ConfigurationSource,
    field_path: str,
    provided_value: object,
    message: str,
    remediation: str,
) -> ConfigurationIssue:
    return ConfigurationIssue(
        severity=IssueSeverity.ERROR,
        source=source,
        field_path=field_path,
        provided_value=provided_value,
        message=message,
        remediation=remediation,
    )


def _error_count(
    issues: Sequence[ConfigurationIssue],
) -> int:
    return sum(
        issue.severity is IssueSeverity.ERROR
        for issue in issues
    )


def _has_errors(
    issues: Sequence[ConfigurationIssue],
) -> bool:
    return _error_count(issues) > 0


def _ordered_issues(
    issues: Sequence[ConfigurationIssue],
) -> tuple[ConfigurationIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.field_path,
                issue.severity.value,
                issue.message,
            ),
        )
    )


def _require_mapping(
    environ: Mapping[str, str],
) -> Mapping[str, str]:
    if not isinstance(environ, Mapping):
        raise TypeError("environ must be a mapping")
    return environ


def _optional_value(
    environ: Mapping[str, str],
    name: str,
) -> str | None:
    value = environ.get(name)
    if value is None:
        return None

    checked = _require_string(name, value)
    return checked or None


def _require_string(
    name: str,
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"environment variable {name!r} must contain a string"
        )
    if "\x00" in value:
        raise ValueError(
            f"environment variable {name!r} "
            "must not contain a NUL character"
        )

    return value


__all__ = (
    "CANONICAL_ENVIRONMENT_VARIABLES",
    "ENVIRONMENT_PREFIX",
    "GF_EXECUTABLE_ENV",
    "OUTPUT_ROOT_ENV",
    "PROJECT_ROOT_ENV",
    "RGL_ROOT_ENV",
    "STATE_PATH_ENV",
    "find_unknown_environment_variables",
    "read_environment",
    "resolve_environment",
)