"""Read and resolve GF Wordbench process-environment configuration.

The environment resolver is intentionally downstream from language probing.
It does not discover or select a language. It receives one already resolved
language context, resolves machine-local execution values, and constructs the
effective GF path through one bounded implementation.

During the ADR-0015 migration the resolver accepts the legacy project-backed
request shape as a compatibility input. That compatibility path never makes
``project.toml`` a startup authority and should be removed after the request and
model migrations are complete.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
import inspect
import os
from pathlib import Path
import re
import shutil
from typing import Final, TypeVar, cast

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

GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_GF_EXE"
RGL_ROOT_ENV: Final[str] = "GF_WORDBENCH_RGL_ROOT"
OUTPUT_ROOT_ENV: Final[str] = "GF_WORDBENCH_OUTPUT_ROOT"
STATE_PATH_ENV: Final[str] = "GF_WORDBENCH_STATE_PATH"

# Retained only so older installations do not turn the former variable into an
# unknown reserved-name error during the migration. It is never required and it
# no longer identifies the startup language.
LEGACY_PROJECT_ROOT_ENV: Final[str] = "GF_WORDBENCH_PROJECT_ROOT"
PROJECT_ROOT_ENV: Final[str] = LEGACY_PROJECT_ROOT_ENV

CANONICAL_ENVIRONMENT_VARIABLES: Final[tuple[str, ...]] = (
    GF_EXECUTABLE_ENV,
    RGL_ROOT_ENV,
    OUTPUT_ROOT_ENV,
    STATE_PATH_ENV,
)
LEGACY_ENVIRONMENT_VARIABLES: Final[tuple[str, ...]] = (LEGACY_PROJECT_ROOT_ENV,)
KNOWN_ENVIRONMENT_VARIABLES: Final[tuple[str, ...]] = (
    *CANONICAL_ENVIRONMENT_VARIABLES,
    *LEGACY_ENVIRONMENT_VARIABLES,
)

_GF_EXECUTABLE_NAMES: Final = frozenset({"gf", "gf.exe"})
_ENV_REFERENCE_PATTERNS: Final = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[^{}]+\}"),
    re.compile(r"(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*"),
)
_STANDARD_SOURCE_ROOT_NAME: Final[str] = "src"
_STANDARD_SOURCE_MARKERS: Final[tuple[str, ...]] = ("abstract", "api", "common", "prelude")
_MAX_ANCESTOR_DEPTH: Final[int] = 16
_MAX_GF_PATH_PARTS: Final[int] = 256

_PathValidator = Callable[[Path], bool]
_DataclassT = TypeVar("_DataclassT")


@dataclass(frozen=True, slots=True)
class _LanguagePaths:
    language_directory: Path
    rgl_source_root: Path
    rgl_root: Path
    profile_root: Path | None


@dataclass(frozen=True, slots=True)
class _PathRequirement:
    value: str | os.PathLike[str]
    required: bool
    source: ConfigurationSource


def read_environment(
    environ: Mapping[str, str] | None = None,
) -> EnvironmentOverrides:
    """Return documented raw overrides without resolving their values.

    ``GF_WORDBENCH_PROJECT_ROOT`` is read only when the installed legacy model
    still exposes ``EnvironmentOverrides.project_root``. New models omit that
    field entirely.
    """

    source = os.environ if environ is None else _require_mapping(environ)
    values: dict[str, str | None] = {
        "gf_executable": _optional_value(source, GF_EXECUTABLE_ENV),
        "rgl_root": _optional_value(source, RGL_ROOT_ENV),
        "output_root": _optional_value(source, OUTPUT_ROOT_ENV),
        "state_path": _optional_value(source, STATE_PATH_ENV),
        "project_root": _optional_value(source, LEGACY_PROJECT_ROOT_ENV),
    }
    return _construct_dataclass(EnvironmentOverrides, values)


def find_unknown_environment_variables(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Return unknown non-empty names in the reserved environment namespace."""

    source = os.environ if environ is None else _require_mapping(environ)
    known = frozenset(KNOWN_ENVIRONMENT_VARIABLES)
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
    """Resolve machine-local execution values for one language-aware run.

    Language identity and source-root discovery belong to the language probe.
    This function validates those resolved facts, applies compatible explicit
    machine-local overrides, resolves optional GF capability, constructs one
    effective GF path, and validates source/output separation.
    """

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

    language_paths = _resolve_language_paths(
        request=request,
        raw_rgl_root=getattr(values, "rgl_root", None),
        precedence=precedence,
        issues=issues,
    )

    output_root = _resolve_required_path(
        field_path="output_root",
        raw_value=getattr(values, "output_root", None),
        precedence=precedence,
        issues=issues,
        expected="an existing writable directory or a creatable directory",
        remediation=(
            "Select a writable directory outside the resolved language and "
            "RGL source trees for GF Wordbench runs."
        ),
        validator=_is_usable_output_root,
    )

    gf_required = _requires_gf(request, values)
    gf_executable, gf_source = _resolve_gf_executable(
        raw_value=getattr(values, "gf_executable", None),
        precedence=precedence,
        issues=issues,
        required=gf_required,
    )

    gf_path: tuple[Path, ...] | None = None
    if language_paths is not None:
        gf_path = _resolve_gf_path(
            request=request,
            language_paths=language_paths,
            required_for_run=gf_required,
            issues=issues,
        )

    if output_root is not None and language_paths is not None:
        _validate_output_separation(
            output_root=output_root,
            protected_roots=_protected_roots(language_paths),
            source=_source_for(precedence, "output_root"),
            provided_value=getattr(values, "output_root", None),
            issues=issues,
        )

    if _has_errors(issues):
        return EnvironmentResolution(
            value=None,
            issues=_ordered_issues(issues),
            provenance=precedence.provenance,
        )

    assert language_paths is not None
    assert output_root is not None
    assert gf_path is not None
    if gf_required:
        assert gf_executable is not None

    resolved_value = _construct_resolved_environment(
        language_paths=language_paths,
        gf_executable=gf_executable,
        output_root=output_root,
        gf_path=gf_path,
    )

    resolved_provenance = (
        _provenance(
            field_path="environment.language_directory",
            source=_configuration_source(
                "LANGUAGE_PROBE",
                ConfigurationSource.RUNTIME_DERIVED,
            ),
            provided_value=_context_value(
                request,
                "language_directory",
            ),
            resolved_value=language_paths.language_directory,
        ),
        _provenance(
            field_path="environment.rgl_source_root",
            source=_rgl_source(precedence, request),
            provided_value=getattr(values, "rgl_root", None),
            resolved_value=language_paths.rgl_source_root,
        ),
        _provenance(
            field_path="environment.rgl_root",
            source=_rgl_source(precedence, request),
            provided_value=getattr(values, "rgl_root", None),
            resolved_value=language_paths.rgl_root,
        ),
        _provenance(
            field_path="environment.gf_executable",
            source=gf_source,
            provided_value=getattr(values, "gf_executable", None),
            resolved_value=gf_executable,
        ),
        _provenance(
            field_path="environment.output_root",
            source=_source_for(precedence, "output_root"),
            provided_value=getattr(values, "output_root", None),
            resolved_value=output_root,
        ),
        _provenance(
            field_path="environment.gf_path",
            source=_configuration_source(
                "LANGUAGE_PROBE",
                ConfigurationSource.RUNTIME_DERIVED,
            ),
            provided_value=_raw_gf_requirements(request),
            resolved_value=gf_path,
        ),
    )

    return EnvironmentResolution(
        value=resolved_value,
        issues=_ordered_issues(issues),
        provenance=_merge_provenance(
            precedence.provenance,
            resolved_provenance,
        ),
    )


def _resolve_language_paths(
    *,
    request: ConfigurationResolutionRequest,
    raw_rgl_root: str | os.PathLike[str] | None,
    precedence: PrecedenceResolution,
    issues: list[ConfigurationIssue],
) -> _LanguagePaths | None:
    context = getattr(request, "language_context", None)
    legacy_project = getattr(request, "project", None)

    language_raw = (
        getattr(context, "language_directory", None)
        if context is not None
        else getattr(legacy_project, "source_root", None)
    )
    if language_raw is None:
        issues.append(
            _error(
                source=_configuration_source(
                    "LANGUAGE_PROBE",
                    ConfigurationSource.RUNTIME_DERIVED,
                ),
                field_path="language_directory",
                provided_value=None,
                message="No resolved language directory was supplied.",
                remediation=(
                    "Resolve one selected language directory or .gf file "
                    "through LanguageProbeService before environment resolution."
                ),
            )
        )
        return None

    try:
        language_directory = _normalize_machine_path(language_raw)
    except (OSError, TypeError, ValueError) as exc:
        issues.append(
            _error(
                source=_configuration_source(
                    "LANGUAGE_PROBE",
                    ConfigurationSource.RUNTIME_DERIVED,
                ),
                field_path="language_directory",
                provided_value=language_raw,
                message=f"The resolved language directory is invalid: {exc}.",
                remediation="Select a readable GF language directory or .gf file.",
            )
        )
        return None

    if not language_directory.is_dir():
        issues.append(
            _error(
                source=_configuration_source(
                    "LANGUAGE_PROBE",
                    ConfigurationSource.RUNTIME_DERIVED,
                ),
                field_path="language_directory",
                provided_value=language_raw,
                message=(
                    "The resolved language directory does not exist or is not "
                    f"a directory: {language_directory}."
                ),
                remediation="Select an existing readable GF language directory.",
            )
        )
        return None

    context_source_raw = getattr(context, "rgl_source_root", None) if context is not None else None
    context_root_raw = getattr(context, "rgl_root", None) if context is not None else None

    explicit_root: Path | None = None
    if raw_rgl_root is not None:
        explicit_root = _resolve_required_path(
            field_path="rgl_root",
            raw_value=raw_rgl_root,
            precedence=precedence,
            issues=issues,
            expected="an existing RGL repository root or RGL source root",
            remediation=(
                "Select the RGL repository root containing src/, or select "
                "the src/ directory that contains the resolved language."
            ),
            validator=Path.is_dir,
        )
        if explicit_root is None:
            return None

    try:
        rgl_source_root, rgl_root = _choose_rgl_layout(
            language_directory=language_directory,
            explicit_root=explicit_root,
            context_source_root=context_source_raw,
            context_root=context_root_raw,
        )
    except (OSError, TypeError, ValueError) as exc:
        issues.append(
            _error(
                source=_rgl_source(precedence, request),
                field_path="rgl_root",
                provided_value=(
                    raw_rgl_root
                    if raw_rgl_root is not None
                    else context_root_raw or context_source_raw
                ),
                message=f"The RGL layout cannot be resolved safely: {exc}.",
                remediation=(
                    "Select a standard RGL language directory beneath src/, "
                    "or provide a compatible explicit RGL root."
                ),
            )
        )
        return None

    try:
        profile_root = _optional_profile_root(request)
    except (OSError, TypeError, ValueError) as exc:
        issues.append(
            _error(
                source=_configuration_source(
                    "VALIDATION_PROFILE",
                    _configuration_source(
                        "PROJECT_TOML",
                        ConfigurationSource.LEGACY_MIGRATION,
                    ),
                ),
                field_path="validation_profile_root",
                provided_value=_profile_root_value(request),
                message=f"The validation-profile root is invalid: {exc}.",
                remediation=(
                    "Select an existing validation profile whose assets remain "
                    "inside its approved profile root."
                ),
            )
        )
        return None

    return _LanguagePaths(
        language_directory=language_directory,
        rgl_source_root=rgl_source_root,
        rgl_root=rgl_root,
        profile_root=profile_root,
    )


def _choose_rgl_layout(
    *,
    language_directory: Path,
    explicit_root: Path | None,
    context_source_root: object,
    context_root: object,
) -> tuple[Path, Path]:
    if explicit_root is not None:
        return _layout_from_explicit_root(language_directory, explicit_root)

    source_root = _optional_machine_path(context_source_root, "language context source_root")
    root = _optional_machine_path(context_root, "language context root")

    if source_root is not None:
        if not source_root.is_dir():
            raise ValueError(f"RGL source root does not exist: {source_root}")
        if not _is_supported_rgl_source_root(source_root):
            raise ValueError(f"RGL source root has an unsupported layout: {source_root}")
        effective_root = root or source_root.parent
        if root is not None and source_root.parent != root:
            expected_source = root / _STANDARD_SOURCE_ROOT_NAME
            if source_root != expected_source:
                raise ValueError(
                    f"resolved RGL root and source root disagree: {root} versus {source_root}"
                )
        # The language directory may be an external GF project.  The resolved
        # RGL source root is then a dependency provider rather than a source
        # containment parent.
        return source_root, effective_root

    if root is not None:
        return _layout_from_explicit_root(language_directory, root)

    return _discover_standard_rgl_layout(language_directory)


def _layout_from_explicit_root(
    language_directory: Path,
    explicit_root: Path,
) -> tuple[Path, Path]:
    del language_directory  # source ownership is independent from dependency ownership

    repository_source = explicit_root / _STANDARD_SOURCE_ROOT_NAME
    if repository_source.is_dir() and _is_supported_rgl_source_root(repository_source):
        return repository_source, explicit_root

    if (
        explicit_root.name.casefold() == _STANDARD_SOURCE_ROOT_NAME
        and explicit_root.is_dir()
        and _is_supported_rgl_source_root(explicit_root)
    ):
        return explicit_root, explicit_root.parent

    raise ValueError(
        "explicit RGL root is not a supported repository root or src/ directory"
    )


def _is_supported_rgl_source_root(path: Path) -> bool:
    if (path / "languages.csv").is_file():
        return True
    markers = sum((path / name).is_dir() for name in _STANDARD_SOURCE_MARKERS)
    return markers >= 2


def _discover_standard_rgl_layout(
    language_directory: Path,
) -> tuple[Path, Path]:
    current = language_directory
    for _ in range(_MAX_ANCESTOR_DEPTH + 1):
        if current.name.casefold() == _STANDARD_SOURCE_ROOT_NAME:
            return current, current.parent
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise ValueError(
        f"no ancestor named {_STANDARD_SOURCE_ROOT_NAME!r} was found within "
        f"the {_MAX_ANCESTOR_DEPTH}-level discovery bound"
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
    source = _source_for(precedence, field_path)

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
                message=f"The selected {field_path!r} path is invalid: {exc}.",
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
                message=(f"The selected {field_path!r} is not {expected}: {path}."),
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
    required: bool,
) -> tuple[Path | None, ConfigurationSource]:
    if raw_value is None:
        source = ConfigurationSource.PATH_DISCOVERY
        candidate: str | os.PathLike[str] | None = shutil.which("gf")

        if candidate is None:
            if required:
                issues.append(
                    _error(
                        source=source,
                        field_path="gf_executable",
                        provided_value=None,
                        message=(
                            "The requested capability requires GF, but no GF "
                            "executable was selected and bounded PATH discovery "
                            "did not find 'gf'."
                        ),
                        remediation=(
                            f"Set {GF_EXECUTABLE_ENV} or provide an explicit path to gf or gf.exe."
                        ),
                    )
                )
            else:
                issues.append(
                    _issue(
                        severity=IssueSeverity.INFO,
                        source=source,
                        field_path="gf_executable",
                        provided_value=None,
                        message=(
                            "GF is unavailable; source browsing and static scan "
                            "may continue, but GF-backed capabilities are disabled."
                        ),
                        remediation=(
                            f"Set {GF_EXECUTABLE_ENV} when compilation, scenarios "
                            "or release validation are required."
                        ),
                    )
                )
            return None, source
    else:
        source = _source_for(precedence, "gf_executable")
        candidate = raw_value

    try:
        executable = _normalize_machine_path(candidate)
    except (OSError, TypeError, ValueError) as exc:
        severity = (
            IssueSeverity.ERROR if required or raw_value is not None else IssueSeverity.WARNING
        )
        issues.append(
            _issue(
                severity=severity,
                source=source,
                field_path="gf_executable",
                provided_value=candidate,
                message=f"The selected GF executable path is invalid: {exc}.",
                remediation="Provide an existing executable file named gf or gf.exe.",
            )
        )
        return None, source

    if not _is_gf_executable(executable):
        severity = (
            IssueSeverity.ERROR if required or raw_value is not None else IssueSeverity.WARNING
        )
        issues.append(
            _issue(
                severity=severity,
                source=source,
                field_path="gf_executable",
                provided_value=candidate,
                message=f"The selected GF executable is not usable: {executable}.",
                remediation="Provide an existing executable file named gf or gf.exe.",
            )
        )
        return None, source

    return executable, source


def _requires_gf(
    request: ConfigurationResolutionRequest,
    values: object,
) -> bool:
    explicit = getattr(request, "requires_gf", None)
    if explicit is not None:
        if type(explicit) is not bool:
            raise TypeError("request.requires_gf must be bool when supplied")
        return explicit

    capability = getattr(request, "requested_capability", None)
    if capability is not None:
        rendered = getattr(capability, "value", capability)
        if not isinstance(rendered, str):
            raise TypeError("requested_capability must be string-like")
        return rendered.casefold() in {
            "compile",
            "compile-ready",
            "scenario",
            "scenario-ready",
            "release",
            "release-ready",
        }

    no_compile = getattr(values, "no_compile", False)
    scenarios = getattr(values, "selected_scenarios", ())
    release_requires_pgf = getattr(values, "release_requires_pgf", False)
    return (not bool(no_compile)) or bool(scenarios) or bool(release_requires_pgf)


def _resolve_gf_path(
    *,
    request: ConfigurationResolutionRequest,
    language_paths: _LanguagePaths,
    required_for_run: bool,
    issues: list[ConfigurationIssue],
) -> tuple[Path, ...] | None:
    requirements = (
        _PathRequirement(
            value=language_paths.language_directory,
            required=True,
            source=_configuration_source(
                "LANGUAGE_PROBE",
                ConfigurationSource.RUNTIME_DERIVED,
            ),
        ),
        *_collect_gf_path_requirements(request),
    )

    if len(requirements) > _MAX_GF_PATH_PARTS:
        issues.append(
            _error(
                source=ConfigurationSource.RUNTIME_DERIVED,
                field_path="gf_path",
                provided_value=len(requirements),
                message=(
                    "The GF path requirement count exceeds the bounded limit "
                    f"of {_MAX_GF_PATH_PARTS}."
                ),
                remediation="Reduce duplicate or unnecessary GF path requirements.",
            )
        )
        return None

    resolved: list[Path] = []
    seen: set[str] = set()
    initial_error_count = _error_count(issues)

    for index, requirement in enumerate(requirements):
        field = f"gf_path_requirements[{index}]"
        try:
            candidate = _resolve_gf_path_part(
                language_paths=language_paths,
                value=requirement.value,
            )
        except (OSError, TypeError, ValueError) as exc:
            severity = (
                IssueSeverity.ERROR
                if requirement.required and required_for_run
                else IssueSeverity.WARNING
            )
            issues.append(
                _issue(
                    severity=severity,
                    source=requirement.source,
                    field_path=field,
                    provided_value=requirement.value,
                    message=f"The GF path part cannot be resolved: {exc}.",
                    remediation=(
                        "Use an existing path inside the approved RGL source tree "
                        "or remove the incompatible optional requirement."
                    ),
                )
            )
            continue

        if not candidate.is_dir():
            severity = (
                IssueSeverity.ERROR
                if requirement.required and required_for_run
                else IssueSeverity.WARNING
            )
            issues.append(
                _issue(
                    severity=severity,
                    source=requirement.source,
                    field_path=field,
                    provided_value=requirement.value,
                    message=(f"The resolved GF path directory does not exist: {candidate}."),
                    remediation=("Correct the path requirement or select the matching RGL root."),
                )
            )
            continue

        key = _path_key(candidate)
        if key not in seen:
            seen.add(key)
            resolved.append(candidate)

    if required_for_run and _error_count(issues) > initial_error_count:
        return None
    return tuple(resolved)


def _collect_gf_path_requirements(
    request: ConfigurationResolutionRequest,
) -> tuple[_PathRequirement, ...]:
    context = getattr(request, "language_context", None)
    profile = getattr(request, "validation_profile", None)
    legacy_project = getattr(request, "project", None)

    raw_groups: list[tuple[object, ConfigurationSource]] = []
    if context is not None:
        raw_groups.append(
            (
                getattr(context, "gf_path_requirements", ()),
                _configuration_source(
                    "LANGUAGE_PROBE",
                    ConfigurationSource.RUNTIME_DERIVED,
                ),
            )
        )
    if profile is not None:
        raw_groups.append(
            (
                _nested_attr(profile, "gf.path_parts", default=()),
                _configuration_source(
                    "VALIDATION_PROFILE",
                    _configuration_source(
                        "PROJECT_TOML",
                        ConfigurationSource.LEGACY_MIGRATION,
                    ),
                ),
            )
        )
    elif legacy_project is not None:
        raw_groups.append(
            (
                _nested_attr(legacy_project, "gf.path_parts", default=()),
                _configuration_source(
                    "PROJECT_TOML",
                    ConfigurationSource.LEGACY_MIGRATION,
                ),
            )
        )

    collected: list[_PathRequirement] = []
    for raw_values, default_source in raw_groups:
        if raw_values is None:
            continue
        if isinstance(raw_values, (str, bytes, os.PathLike)):
            raw_values = (raw_values,)
        if not isinstance(raw_values, Sequence):
            raise TypeError("GF path requirements must be a sequence")

        for value in raw_values:
            if hasattr(value, "path") or hasattr(value, "value"):
                raw_value = getattr(value, "path", getattr(value, "value", None))
                required = getattr(value, "required", True)
                source = getattr(value, "source", default_source)
                if type(required) is not bool:
                    raise TypeError("GF path requirement.required must be bool")
                if not isinstance(source, ConfigurationSource):
                    source = default_source
            else:
                raw_value = value
                required = True
                source = default_source

            if raw_value is None:
                raise ValueError("GF path requirement must contain a path value")
            collected.append(
                _PathRequirement(
                    value=raw_value,
                    required=required,
                    source=source,
                )
            )

    return tuple(collected)


def _resolve_gf_path_part(
    *,
    language_paths: _LanguagePaths,
    value: str | os.PathLike[str],
) -> Path:
    text = _path_text(value)
    candidate = Path(text)

    if candidate.is_absolute():
        resolved = candidate.resolve(strict=False)
    else:
        if text == "language":
            resolved = language_paths.language_directory
        elif text in {"rgl_source_root", "src"}:
            resolved = language_paths.rgl_source_root
        elif text == "rgl_root":
            resolved = language_paths.rgl_root
        elif candidate.parts and candidate.parts[0].casefold() == _STANDARD_SOURCE_ROOT_NAME:
            resolved = (language_paths.rgl_root / candidate).resolve(strict=False)
        else:
            resolved = (language_paths.rgl_source_root / candidate).resolve(strict=False)

    approved_roots = [language_paths.rgl_root]
    if not language_paths.language_directory.is_relative_to(
        language_paths.rgl_source_root
    ):
        # External project source root.  The probe deliberately adds only this
        # bounded project source directory to GF-path requirements.
        approved_roots.append(language_paths.language_directory.parent)

    if not any(
        resolved == root or resolved.is_relative_to(root)
        for root in approved_roots
    ):
        raise ValueError(
            "path escapes the approved RGL dependency root and external "
            f"project source root: {resolved}"
        )
    return resolved


def _validate_output_separation(
    *,
    output_root: Path,
    protected_roots: Iterable[tuple[str, Path]],
    source: ConfigurationSource,
    provided_value: object,
    issues: list[ConfigurationIssue],
) -> None:
    overlaps = [label for label, root in protected_roots if _paths_overlap(output_root, root)]
    if not overlaps:
        return

    issues.append(
        _error(
            source=source,
            field_path="output_root",
            provided_value=provided_value,
            message=(
                "The selected output root overlaps " + " and ".join(overlaps) + f": {output_root}."
            ),
            remediation=(
                "Select a writable output directory outside the resolved "
                "language, RGL and validation-profile source trees."
            ),
        )
    )


def _protected_roots(
    paths: _LanguagePaths,
) -> tuple[tuple[str, Path], ...]:
    values: list[tuple[str, Path]] = [
        ("the language directory", paths.language_directory),
        ("the RGL source root", paths.rgl_source_root),
        ("the RGL repository root", paths.rgl_root),
    ]
    if paths.profile_root is not None:
        values.append(("the validation-profile root", paths.profile_root))
    return tuple(values)


def _profile_root_value(
    request: ConfigurationResolutionRequest,
) -> object:
    profile = getattr(request, "validation_profile", None)
    candidate = getattr(profile, "profile_root", None) if profile is not None else None
    if candidate is None:
        legacy_project = getattr(request, "project", None)
        candidate = getattr(legacy_project, "project_root", None)
    return candidate


def _optional_profile_root(
    request: ConfigurationResolutionRequest,
) -> Path | None:
    candidate = _profile_root_value(request)
    if candidate is None:
        return None

    root = _normalize_machine_path(cast("str | os.PathLike[str]", candidate))
    if not root.is_dir():
        raise ValueError(f"profile root does not exist: {root}")
    return root


def _construct_resolved_environment(
    *,
    language_paths: _LanguagePaths,
    gf_executable: Path | None,
    output_root: Path,
    gf_path: tuple[Path, ...],
) -> ResolvedEnvironment:
    values: dict[str, object] = {
        "language_directory": language_paths.language_directory,
        "rgl_source_root": language_paths.rgl_source_root,
        "rgl_root": language_paths.rgl_root,
        "gf_executable": gf_executable,
        "output_root": output_root,
        "gf_path": gf_path,
        "validation_profile_root": language_paths.profile_root,
        # Legacy model compatibility. The value is only a structural adapter;
        # it is not treated as startup or language authority.
        "project_root": (language_paths.profile_root or language_paths.language_directory),
    }
    return _construct_dataclass(ResolvedEnvironment, values)


def _construct_dataclass(
    cls: type[_DataclassT],
    values: Mapping[str, object],
) -> _DataclassT:
    if is_dataclass(cls):
        accepted = {field.name for field in fields(cls)}
    else:
        accepted = set(inspect.signature(cls).parameters)
    return cls(**{name: value for name, value in values.items() if name in accepted})


def _provenance(
    *,
    field_path: str,
    source: ConfigurationSource,
    provided_value: object,
    resolved_value: object,
) -> ConfigurationProvenance:
    return _construct_dataclass(
        ConfigurationProvenance,
        {
            "field_path": field_path,
            "source": source,
            "provided_value": provided_value,
            "resolved_value": resolved_value,
        },
    )


def _context_value(
    request: ConfigurationResolutionRequest,
    name: str,
) -> object:
    context = getattr(request, "language_context", None)
    if context is not None:
        return getattr(context, name, None)
    project = getattr(request, "project", None)
    if name == "language_directory" and project is not None:
        return getattr(project, "source_root", None)
    return None


def _raw_gf_requirements(request: ConfigurationResolutionRequest) -> object:
    context = getattr(request, "language_context", None)
    if context is not None:
        return getattr(context, "gf_path_requirements", ())
    project = getattr(request, "project", None)
    return _nested_attr(project, "gf.path_parts", default=())


def _nested_attr(obj: object, path: str, *, default: object) -> object:
    current = obj
    for part in path.split("."):
        if current is None or not hasattr(current, part):
            return default
        current = getattr(current, part)
    return current


def _optional_machine_path(value: object, field_name: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError(f"{field_name} must be path-like")
    return _normalize_machine_path(value)


def _normalize_machine_path(
    value: str | os.PathLike[str],
) -> Path:
    text = _path_text(value)

    if any(pattern.search(text) for pattern in _ENV_REFERENCE_PATTERNS):
        raise ValueError("inline environment-variable references are not permitted")

    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError("machine-local paths must be absolute")

    return path.resolve(strict=False)


def _path_text(value: str | os.PathLike[str]) -> str:
    if isinstance(value, str):
        text = value
    elif isinstance(value, os.PathLike):
        text = os.fspath(value)
    else:
        raise TypeError("path must be a string or os.PathLike object")

    if not isinstance(text, str):
        raise TypeError("path must resolve to text")
    if not text:
        raise ValueError("path must not be empty")
    if "\x00" in text:
        raise ValueError("path must not contain a NUL character")
    return text


def _is_usable_output_root(path: Path) -> bool:
    if path.exists():
        return path.is_dir() and os.access(path, os.W_OK)

    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return parent.is_dir() and os.access(parent, os.W_OK)


def _is_gf_executable(path: Path) -> bool:
    return (
        path.is_file() and path.name.casefold() in _GF_EXECUTABLE_NAMES and os.access(path, os.X_OK)
    )


def _paths_overlap(left: Path, right: Path) -> bool:
    return _same_path(left, right) or left.is_relative_to(right) or right.is_relative_to(left)


def _same_path(left: Path, right: Path) -> bool:
    return _path_key(left) == _path_key(right)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _rgl_source(
    resolution: PrecedenceResolution,
    request: ConfigurationResolutionRequest,
) -> ConfigurationSource:
    values = getattr(resolution, "values", None)
    if values is not None and getattr(values, "rgl_root", None) is not None:
        return _source_for(resolution, "rgl_root")
    if getattr(request, "language_context", None) is not None:
        return _configuration_source(
            "LANGUAGE_PROBE",
            ConfigurationSource.RUNTIME_DERIVED,
        )
    return ConfigurationSource.LEGACY_MIGRATION


def _source_for(
    resolution: PrecedenceResolution,
    field_path: str,
) -> ConfigurationSource:
    accepted = {field_path, f"environment.{field_path}"}

    for record in resolution.provenance:
        if record.field_path in accepted:
            return record.source

    return ConfigurationSource.RUNTIME_DERIVED


def _configuration_source(
    name: str,
    fallback: ConfigurationSource,
) -> ConfigurationSource:
    return getattr(ConfigurationSource, name, fallback)


def _merge_provenance(
    *groups: Sequence[ConfigurationProvenance],
) -> tuple[ConfigurationProvenance, ...]:
    merged: dict[str, ConfigurationProvenance] = {}

    for group in groups:
        for record in group:
            merged[record.field_path] = record

    return tuple(sorted(merged.values(), key=lambda record: record.field_path))


def _issue(
    *,
    severity: IssueSeverity,
    source: ConfigurationSource,
    field_path: str,
    provided_value: object,
    message: str,
    remediation: str,
) -> ConfigurationIssue:
    return ConfigurationIssue(
        severity=severity,
        source=source,
        field_path=field_path,
        provided_value=provided_value,
        message=message,
        remediation=remediation,
    )


def _error(
    *,
    source: ConfigurationSource,
    field_path: str,
    provided_value: object,
    message: str,
    remediation: str,
) -> ConfigurationIssue:
    return _issue(
        severity=IssueSeverity.ERROR,
        source=source,
        field_path=field_path,
        provided_value=provided_value,
        message=message,
        remediation=remediation,
    )


def _error_count(issues: Sequence[ConfigurationIssue]) -> int:
    return sum(issue.severity is IssueSeverity.ERROR for issue in issues)


def _has_errors(issues: Sequence[ConfigurationIssue]) -> bool:
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


def _require_string(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"environment variable {name!r} must contain a string")
    if "\x00" in value:
        raise ValueError(f"environment variable {name!r} must not contain a NUL character")
    return value


__all__ = (
    "CANONICAL_ENVIRONMENT_VARIABLES",
    "ENVIRONMENT_PREFIX",
    "GF_EXECUTABLE_ENV",
    "KNOWN_ENVIRONMENT_VARIABLES",
    "LEGACY_ENVIRONMENT_VARIABLES",
    "LEGACY_PROJECT_ROOT_ENV",
    "OUTPUT_ROOT_ENV",
    "PROJECT_ROOT_ENV",
    "RGL_ROOT_ENV",
    "STATE_PATH_ENV",
    "find_unknown_environment_variables",
    "read_environment",
    "resolve_environment",
)
