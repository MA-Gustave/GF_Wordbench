"""CLI adapters for validation-profile and scenario contract checks.

This module owns CLI-facing request translation, result projection, legacy
terminal presentation, and compatibility helpers. It does not construct
concrete adapters, load validation profiles, resolve language contexts, probe
GF, parse scenario sources, or execute validation algorithms.

Canonical requests use ADR-0015 inputs:

- one explicit ``language_path`` when language context is required;
- one explicit ``validation_profile`` for project and scenario policy;
- optional environment paths such as the GF executable and RGL root.

The temporary ``project_root`` compatibility surface is derived from the
explicit profile path. It is not a startup authority and must disappear after
the bootstrap migration is complete.

The canonical one-argument handlers obtain their application boundaries from
the bootstrap composition root:

- ``build_project_check_application()``
- ``build_scenario_check_application()``

Both bootstrap factories must be import-side-effect free until called.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final, Protocol, TextIO, runtime_checkable

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
)
from gf_wordbench.kernel.ids import validate_scenario_id
from gf_wordbench.kernel.statuses import OverallStatus
from gf_wordbench.projects.models import (
    ProjectDiagnostic,
    ProjectDiagnosticSeverity,
    ProjectValidationResult,
)

from .exit_codes import (
    EXIT_CANCELLED,
    EXIT_OK,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_FAILED,
)
from .parser import CliCommand, CliRequest, CliUsageError

_PROJECT_COMMAND: Final[str] = "project"
_PROJECT_CHECK_COMMAND: Final[str] = "check"
_PROJECT_CHECK_CANONICAL_COMMAND: Final[str] = "project.check"
_SCENARIOS_CHECK_CANONICAL_COMMAND: Final[str] = "scenarios.check"
_MAX_ERROR_MESSAGE_LENGTH: Final[int] = 2_000


@runtime_checkable
class ProjectCheckApplication(Protocol):
    """Application boundary consumed by the profile-check CLI adapter."""

    def check_project(
        self,
        request: ProjectCheckRequest,
    ) -> ProjectValidationResult:
        ...


@runtime_checkable
class ScenarioCheckApplication(Protocol):
    """Application boundary consumed by the scenario-check CLI adapter."""

    def check_scenarios(
        self,
        request: ScenarioCheckRequest,
    ) -> ScenarioCheckCommandResult | ProjectValidationResult:
        ...


class SubparserCollection(Protocol):
    """Minimal argparse subparser collection used by the legacy registrar."""

    def add_parser(
        self,
        name: str,
        **kwargs: object,
    ) -> argparse.ArgumentParser:
        ...


@dataclass(frozen=True, slots=True)
class ProjectCheckRequest:
    """Typed request for one explicit validation-profile contract check."""

    validation_profile: Path
    language_path: Path | None = None
    strict: bool = False
    probe_gf: bool = False
    gf_executable: Path | None = None
    rgl_root: Path | None = None
    legacy_project_root: Path | None = None
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        _require_path(
            self.validation_profile,
            field="validation_profile",
        )
        for field_name in (
            "language_path",
            "gf_executable",
            "rgl_root",
            "legacy_project_root",
        ):
            _require_optional_path(
                getattr(self, field_name),
                field=field_name,
            )

        for field_name in (
            "strict",
            "probe_gf",
            "quiet",
            "verbose",
        ):
            _require_bool(
                getattr(self, field_name),
                field=field_name,
            )

        if self.quiet and self.verbose:
            raise ValueError(
                "--quiet and --verbose cannot be used together"
            )

        if self.legacy_project_root is not None:
            expected = _legacy_profile_path(self.legacy_project_root)
            if (
                _normalized_path(self.validation_profile)
                != _normalized_path(expected)
            ):
                raise ValueError(
                    "legacy project root conflicts with validation profile"
                )

    @property
    def selected_language_path(self) -> Path | None:
        """Compatibility alias for the canonical selected language path."""

        return self.language_path

    @property
    def profile_path(self) -> Path:
        """Compatibility alias for the explicit validation profile."""

        return self.validation_profile

    @property
    def gf_exe(self) -> Path | None:
        """Compatibility alias for the configured GF executable."""

        return self.gf_executable

    @property
    def project_root(self) -> Path:
        """Temporary bootstrap bridge derived from ``validation_profile``.

        This property exists only while the bootstrap checker still consumes a
        legacy project-root-shaped request. It never overrides the explicit
        profile path.
        """

        if self.legacy_project_root is not None:
            return self.legacy_project_root
        return _profile_workspace_root(self.validation_profile)

@dataclass(frozen=True, slots=True)
class ProjectCheckCommandResult:
    """Structured result returned by the validation-profile checker."""

    overall_status: OverallStatus
    validation_profile: Path
    language_path: Path | None = None
    diagnostics: tuple[ProjectDiagnostic, ...] = ()
    message: str = "Validation profile contract is valid."

    def __post_init__(self) -> None:
        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be OverallStatus")

        _require_path(
            self.validation_profile,
            field="validation_profile",
        )
        _require_optional_path(
            self.language_path,
            field="language_path",
        )

        diagnostics = tuple(self.diagnostics)
        for index, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, ProjectDiagnostic):
                raise TypeError(
                    "diagnostics must contain ProjectDiagnostic values; "
                    f"item {index} is {type(diagnostic).__name__}"
                )
        object.__setattr__(self, "diagnostics", diagnostics)

        _require_message(self.message, field="message")

        expected = OverallStatus.FAIL if self.errors else OverallStatus.OK
        if self.overall_status is not expected:
            raise ValueError(
                "overall_status must agree with profile diagnostics"
            )

    @classmethod
    def from_validation(
        cls,
        validation: ProjectValidationResult,
        *,
        validation_profile: Path,
        language_path: Path | None,
    ) -> "ProjectCheckCommandResult":
        """Project one application result into the canonical CLI result."""

        if not isinstance(validation, ProjectValidationResult):
            raise TypeError(
                "validation must be ProjectValidationResult"
            )

        errors = len(validation.errors)
        warnings = len(validation.warnings)
        status = OverallStatus.FAIL if errors else OverallStatus.OK

        if errors:
            message = (
                "Validation profile contract is invalid: "
                f"{errors} error(s), {warnings} warning(s)."
            )
        elif warnings:
            message = (
                "Validation profile contract is valid with "
                f"{warnings} warning(s)."
            )
        else:
            message = "Validation profile contract is valid."

        return cls(
            overall_status=status,
            validation_profile=validation_profile,
            language_path=language_path,
            diagnostics=validation.diagnostics,
            message=message,
        )

    @property
    def project_file(self) -> Path:
        """Compatibility alias for the explicit validation profile."""

        return self.validation_profile

    @property
    def project_root(self) -> Path:
        """Compatibility projection of the profile-owning workspace root."""

        return _profile_workspace_root(self.validation_profile)

    @property
    def errors(self) -> tuple[ProjectDiagnostic, ...]:
        return tuple(
            item
            for item in self.diagnostics
            if item.severity is ProjectDiagnosticSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ProjectDiagnostic, ...]:
        return tuple(
            item
            for item in self.diagnostics
            if item.severity is ProjectDiagnosticSeverity.WARNING
        )

    @property
    def ok(self) -> bool:
        return self.overall_status is OverallStatus.OK

@dataclass(frozen=True, slots=True)
class ScenarioCheckRequest:
    """Typed request for registered scenario-contract validation."""

    validation_profile: Path
    language_path: Path | None = None
    use_last_language: bool = False
    strict: bool = False
    scenario_ids: tuple[str, ...] = ()
    legacy_project_root: Path | None = None
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        _require_path(
            self.validation_profile,
            field="validation_profile",
        )
        for field_name in (
            "language_path",
            "legacy_project_root",
        ):
            _require_optional_path(
                getattr(self, field_name),
                field=field_name,
            )

        for field_name in (
            "use_last_language",
            "strict",
            "quiet",
            "verbose",
        ):
            _require_bool(
                getattr(self, field_name),
                field=field_name,
            )

        if self.language_path is None and not self.use_last_language:
            raise ValueError(
                "scenario check requires language_path or use_last_language"
            )
        if self.language_path is not None and self.use_last_language:
            raise ValueError(
                "language_path and use_last_language are mutually exclusive"
            )
        if self.quiet and self.verbose:
            raise ValueError(
                "--quiet and --verbose cannot be used together"
            )

        if self.legacy_project_root is not None:
            expected = _legacy_profile_path(self.legacy_project_root)
            if (
                _normalized_path(self.validation_profile)
                != _normalized_path(expected)
            ):
                raise ValueError(
                    "legacy project root conflicts with validation profile"
                )

        identifiers = _normalize_scenario_ids(
            self.scenario_ids,
            field="scenario_ids",
        )
        object.__setattr__(self, "scenario_ids", identifiers)

    @property
    def selected_language_path(self) -> Path | None:
        return self.language_path

    @property
    def profile_path(self) -> Path:
        return self.validation_profile

    @property
    def project_root(self) -> Path:
        if self.legacy_project_root is not None:
            return self.legacy_project_root
        return _profile_workspace_root(self.validation_profile)

@dataclass(frozen=True, slots=True)
class ScenarioCheckIssue:
    """One bounded issue discovered by the scenario-check application."""

    severity: str
    code: str
    message: str
    path: Path | None = None
    scenario_id: str | None = None
    line: int | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning"}:
            raise ValueError(
                "severity must be 'error' or 'warning'"
            )

        _require_message(self.code, field="code")
        _require_message(self.message, field="message")
        _require_optional_path(self.path, field="path")

        if self.scenario_id is not None:
            object.__setattr__(
                self,
                "scenario_id",
                str(validate_scenario_id(self.scenario_id)),
            )

        if self.line is not None:
            if type(self.line) is not int:
                raise TypeError(
                    "line must be an integer or None"
                )
            if self.line <= 0:
                raise ValueError(
                    "line must be positive when provided"
                )


@dataclass(frozen=True, slots=True)
class ScenarioCheckCommandResult:
    """Structured result returned by the scenario-contract checker."""

    overall_status: OverallStatus
    validation_profile: Path
    language_path: Path | None
    checked_scenarios: tuple[str, ...]
    issues: tuple[ScenarioCheckIssue, ...] = ()
    message: str = "Scenario contracts are valid."

    def __post_init__(self) -> None:
        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be OverallStatus")

        _require_path(
            self.validation_profile,
            field="validation_profile",
        )
        _require_optional_path(
            self.language_path,
            field="language_path",
        )

        checked = _normalize_scenario_ids(
            self.checked_scenarios,
            field="checked_scenarios",
        )
        object.__setattr__(self, "checked_scenarios", checked)

        issues = tuple(self.issues)
        for index, issue in enumerate(issues):
            if not isinstance(issue, ScenarioCheckIssue):
                raise TypeError(
                    "issues must contain ScenarioCheckIssue values; "
                    f"item {index} is {type(issue).__name__}"
                )
        object.__setattr__(self, "issues", issues)

        _require_message(self.message, field="message")

        expected = OverallStatus.FAIL if self.errors else OverallStatus.OK
        if self.overall_status is not expected:
            raise ValueError(
                "overall_status must agree with scenario issues"
            )

    @classmethod
    def from_validation(
        cls,
        validation: ProjectValidationResult,
        *,
        request: ScenarioCheckRequest,
    ) -> "ScenarioCheckCommandResult":
        """Adapt the bootstrap's transitional project-validation result."""

        if not isinstance(validation, ProjectValidationResult):
            raise TypeError(
                "validation must be ProjectValidationResult"
            )

        issues = tuple(
            ScenarioCheckIssue(
                severity=(
                    "error"
                    if diagnostic.severity is ProjectDiagnosticSeverity.ERROR
                    else "warning"
                ),
                code=diagnostic.code,
                message=diagnostic.message,
                path=diagnostic.source_file,
            )
            for diagnostic in validation.diagnostics
            if diagnostic.severity
            in {
                ProjectDiagnosticSeverity.ERROR,
                ProjectDiagnosticSeverity.WARNING,
            }
        )
        errors = sum(1 for issue in issues if issue.severity == "error")
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        if errors:
            message = (
                "Scenario contracts are invalid: "
                f"{errors} error(s), {warnings} warning(s)."
            )
        elif warnings:
            message = (
                "Scenario contracts are valid with "
                f"{warnings} warning(s)."
            )
        else:
            message = "Scenario contracts are valid."

        return cls(
            overall_status=(
                OverallStatus.FAIL if errors else OverallStatus.OK
            ),
            validation_profile=request.validation_profile,
            language_path=request.language_path,
            checked_scenarios=request.scenario_ids,
            issues=issues,
            message=message,
        )

    @property
    def project_root(self) -> Path:
        """Compatibility projection of the profile-owning workspace root."""

        return _profile_workspace_root(self.validation_profile)

    @property
    def errors(self) -> tuple[ScenarioCheckIssue, ...]:
        return tuple(
            item
            for item in self.issues
            if item.severity == "error"
        )

    @property
    def warnings(self) -> tuple[ScenarioCheckIssue, ...]:
        return tuple(
            item
            for item in self.issues
            if item.severity == "warning"
        )

    @property
    def ok(self) -> bool:
        return self.overall_status is OverallStatus.OK


def register_project_commands(
    subparsers: SubparserCollection,
) -> argparse.ArgumentParser:
    """Register the compatibility ``project check`` parser surface."""

    project_parser = subparsers.add_parser(
        _PROJECT_COMMAND,
        help="Inspect an explicit validation profile.",
        description="Validation-profile contract operations.",
    )
    project_subparsers = project_parser.add_subparsers(
        dest="project_command",
        metavar="COMMAND",
        required=True,
    )

    check_parser = project_subparsers.add_parser(
        _PROJECT_CHECK_COMMAND,
        help="Validate one explicit validation profile.",
        description=(
            "Validate profile configuration, semantics, paths, registries, "
            "required assets, and compatibility with an optional explicit "
            "language path without running full validation."
        ),
    )
    check_parser.add_argument(
        "--language-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="GF language directory or .gf file used for compatibility checks.",
    )
    check_parser.add_argument(
        "--profile",
        "--validation-profile",
        dest="validation_profile",
        type=Path,
        required=False,
        metavar="PATH",
        help="Explicit validation profile to check.",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict profile and environment checks.",
    )
    check_parser.add_argument(
        "--probe-gf",
        action="store_true",
        help="Probe the configured GF executable and RGL environment.",
    )
    check_parser.add_argument(
        "--project-root",
        dest="legacy_project_root",
        type=Path,
        metavar="PATH",
        help=(
            "Deprecated compatibility alias for "
            "--profile <root>/project/project.toml."
        ),
    )
    check_parser.add_argument(
        "--gf-exe",
        type=Path,
        metavar="PATH",
        help="Explicit path to gf or gf.exe.",
    )
    check_parser.add_argument(
        "--rgl-root",
        type=Path,
        metavar="PATH",
        help="Explicit Resource Grammar Library root.",
    )

    verbosity = check_parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the compact final result.",
    )
    verbosity.add_argument(
        "--verbose",
        action="store_true",
        help="Print expanded diagnostic evidence.",
    )

    check_parser.set_defaults(
        command_group=_PROJECT_COMMAND,
        command_name=_PROJECT_CHECK_CANONICAL_COMMAND,
    )
    return project_parser


def project_check_request_from_namespace(
    namespace: argparse.Namespace,
) -> ProjectCheckRequest:
    """Build a typed request from a canonical or compatibility namespace."""

    if not isinstance(namespace, argparse.Namespace):
        raise TypeError("namespace must be argparse.Namespace")

    canonical_command = _command_value(
        getattr(namespace, "_command", None)
    )
    if canonical_command is not None:
        if canonical_command != _PROJECT_CHECK_CANONICAL_COMMAND:
            raise ValueError(
                "namespace does not identify project check"
            )
    else:
        command_group = getattr(
            namespace,
            "command_group",
            _PROJECT_COMMAND,
        )
        project_command = getattr(
            namespace,
            "project_command",
            None,
        )
        command_name = getattr(
            namespace,
            "command_name",
            None,
        )
        if command_group != _PROJECT_COMMAND:
            raise ValueError(
                "namespace does not identify a project command"
            )
        if (
            project_command != _PROJECT_CHECK_COMMAND
            and command_name != _PROJECT_CHECK_CANONICAL_COMMAND
        ):
            raise ValueError(
                "namespace does not identify project check"
            )

    legacy_root = _optional_path(
        _namespace_first(
            namespace,
            "legacy_project_root",
            "project_root",
        ),
        field="legacy_project_root",
    )
    profile = _resolve_validation_profile(
        _namespace_first(
            namespace,
            "validation_profile",
            "profile",
            "profile_path",
        ),
        legacy_project_root=legacy_root,
    )

    return ProjectCheckRequest(
        validation_profile=profile,
        language_path=_optional_path(
            _namespace_first(
                namespace,
                "language_path",
                "selected_language_path",
            ),
            field="language_path",
        ),
        strict=_namespace_bool(namespace, "strict"),
        probe_gf=_namespace_bool(namespace, "probe_gf"),
        gf_executable=_optional_path(
            _namespace_first(
                namespace,
                "gf_exe",
                "gf_executable",
            ),
            field="gf_executable",
        ),
        rgl_root=_optional_path(
            getattr(namespace, "rgl_root", None),
            field="rgl_root",
        ),
        legacy_project_root=legacy_root,
        quiet=_namespace_bool(namespace, "quiet"),
        verbose=_namespace_bool(namespace, "verbose"),
    )


def project_check_request_from_cli_request(
    request: CliRequest,
) -> ProjectCheckRequest:
    """Translate one canonical CLI request into the application request."""

    _require_cli_command(request, CliCommand.PROJECT_CHECK)

    legacy_root = _optional_path(
        _request_first(
            request,
            "legacy_project_root",
            "project_root",
        ),
        field="legacy_project_root",
    )
    profile = _resolve_validation_profile(
        _request_first(
            request,
            "validation_profile",
            "profile",
            "profile_path",
        ),
        legacy_project_root=legacy_root,
    )

    return ProjectCheckRequest(
        validation_profile=profile,
        language_path=_optional_path(
            _request_first(
                request,
                "language_path",
                "selected_language_path",
            ),
            field="language_path",
        ),
        strict=_request_bool(request, "strict"),
        probe_gf=_request_bool(request, "probe_gf"),
        gf_executable=_optional_path(
            _request_first(
                request,
                "gf_exe",
                "gf_executable",
            ),
            field="gf_executable",
        ),
        rgl_root=_optional_path(
            request.get("rgl_root"),
            field="rgl_root",
        ),
        legacy_project_root=legacy_root,
        quiet=_request_bool(request, "quiet"),
        verbose=_request_bool(request, "verbose"),
    )


def scenario_check_request_from_cli_request(
    request: CliRequest,
) -> ScenarioCheckRequest:
    """Translate one canonical CLI request into the application request."""

    _require_cli_command(request, CliCommand.SCENARIOS_CHECK)

    raw_ids = request.get("scenario_ids", ())
    if raw_ids is None:
        scenario_ids: tuple[str, ...] = ()
    elif isinstance(raw_ids, tuple):
        scenario_ids = raw_ids
    elif isinstance(raw_ids, list):
        scenario_ids = tuple(raw_ids)
    else:
        raise CliUsageError(
            "scenario_ids must be a sequence of scenario IDs"
        )

    legacy_root = _optional_path(
        _request_first(
            request,
            "legacy_project_root",
            "project_root",
        ),
        field="legacy_project_root",
    )
    profile = _resolve_validation_profile(
        _request_first(
            request,
            "validation_profile",
            "profile",
            "profile_path",
        ),
        legacy_project_root=legacy_root,
    )

    return ScenarioCheckRequest(
        validation_profile=profile,
        language_path=_optional_path(
            _request_first(
                request,
                "language_path",
                "selected_language_path",
            ),
            field="language_path",
        ),
        use_last_language=_request_bool(
            request,
            "use_last_language",
        ),
        strict=_request_bool(request, "strict"),
        scenario_ids=scenario_ids,
        legacy_project_root=legacy_root,
        quiet=_request_bool(request, "quiet"),
        verbose=_request_bool(request, "verbose"),
    )


def execute_project_check_command(
    request: CliRequest,
) -> ProjectCheckCommandResult:
    """Execute the canonical one-argument ``project check`` handler."""

    typed_request = project_check_request_from_cli_request(request)
    return run_project_check(
        typed_request,
        _build_project_check_application(),
    )


def execute_scenarios_check_command(
    request: CliRequest,
) -> ScenarioCheckCommandResult:
    """Execute the canonical one-argument ``scenarios check`` handler."""

    typed_request = scenario_check_request_from_cli_request(request)
    return run_scenarios_check(
        typed_request,
        _build_scenario_check_application(),
    )


def run_project_check(
    request: ProjectCheckRequest,
    application: ProjectCheckApplication,
) -> ProjectCheckCommandResult:
    """Invoke the injected profile-check application and project its result."""

    if not isinstance(request, ProjectCheckRequest):
        raise TypeError("request must be ProjectCheckRequest")
    _require_project_application(application)

    validation = application.check_project(request)
    if not isinstance(validation, ProjectValidationResult):
        raise TypeError(
            "check_project() must return ProjectValidationResult"
        )

    return ProjectCheckCommandResult.from_validation(
        validation,
        validation_profile=request.validation_profile,
        language_path=request.language_path,
    )


def run_scenarios_check(
    request: ScenarioCheckRequest,
    application: ScenarioCheckApplication,
) -> ScenarioCheckCommandResult:
    """Invoke the injected scenario-check application."""

    if not isinstance(request, ScenarioCheckRequest):
        raise TypeError("request must be ScenarioCheckRequest")
    _require_scenario_application(application)

    result = application.check_scenarios(request)
    if isinstance(result, ScenarioCheckCommandResult):
        return result
    if isinstance(result, ProjectValidationResult):
        return ScenarioCheckCommandResult.from_validation(
            result,
            request=request,
        )
    raise TypeError(
        "check_scenarios() must return ScenarioCheckCommandResult "
        "or transitional ProjectValidationResult"
    )


def execute_project_command(
    namespace: argparse.Namespace,
    application: ProjectCheckApplication,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Execute a compatibility argparse namespace."""

    try:
        request = project_check_request_from_namespace(namespace)
    except (TypeError, ValueError) as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_USAGE_ERROR

    return execute_project_check(
        request,
        application,
        stdout=stdout,
        stderr=stderr,
    )


def execute_project_check(
    request: ProjectCheckRequest,
    application: ProjectCheckApplication,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Execute the injectable compatibility adapter and return an exit code."""

    if not isinstance(request, ProjectCheckRequest):
        raise TypeError("request must be ProjectCheckRequest")
    _require_project_application(application)

    try:
        command_result = run_project_check(
            request,
            application,
        )
    except CancellationRequested as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_CANCELLED
    except (
        CliUsageError,
        ConfigurationError,
        ContractViolationError,
        ValueError,
    ) as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_USAGE_ERROR
    except (GFWordbenchError, OSError) as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_RUNTIME_ERROR
    except Exception as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_RUNTIME_ERROR

    validation = ProjectValidationResult(
        command_result.diagnostics
    )
    present_project_check(
        validation,
        quiet=request.quiet,
        verbose=request.verbose,
        stdout=stdout,
        stderr=stderr,
    )
    return (
        EXIT_OK
        if command_result.ok
        else EXIT_VALIDATION_FAILED
    )


def present_project_check(
    result: ProjectValidationResult,
    *,
    quiet: bool = False,
    verbose: bool = False,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> None:
    """Render one project-validation result without changing its verdict."""

    if not isinstance(result, ProjectValidationResult):
        raise TypeError("result must be ProjectValidationResult")
    _require_bool(quiet, field="quiet")
    _require_bool(verbose, field="verbose")
    if quiet and verbose:
        raise ValueError(
            "quiet and verbose cannot both be enabled"
        )

    error_count = len(result.errors)
    warning_count = len(result.warnings)
    info_count = sum(
        diagnostic.severity is ProjectDiagnosticSeverity.INFO
        for diagnostic in result.diagnostics
    )
    status = "OK" if result.ok else "INVALID"

    if quiet:
        _write_line(
            stdout if result.ok else stderr,
            (
                f"Validation profile check: {status} "
                f"({error_count} errors, "
                f"{warning_count} warnings)"
            ),
        )
        return

    _write_line(stdout, f"Validation profile check: {status}")
    _write_line(
        stdout,
        (
            f"Diagnostics: {error_count} errors, "
            f"{warning_count} warnings, {info_count} info"
        ),
    )

    for diagnostic in result.diagnostics:
        _present_diagnostic(
            diagnostic,
            verbose=verbose,
            stdout=stdout,
            stderr=stderr,
        )


def _present_diagnostic(
    diagnostic: ProjectDiagnostic,
    *,
    verbose: bool,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    if not isinstance(diagnostic, ProjectDiagnostic):
        raise TypeError(
            "diagnostic must be ProjectDiagnostic"
        )

    if diagnostic.severity is ProjectDiagnosticSeverity.ERROR:
        prefix = "ERROR"
        stream = stderr
    elif diagnostic.severity is ProjectDiagnosticSeverity.WARNING:
        prefix = "WARNING"
        stream = stderr
    else:
        prefix = "INFO"
        stream = stdout

    _write_line(
        stream,
        (
            f"{prefix}: [{diagnostic.code}] "
            f"{diagnostic.field}: {diagnostic.message}"
        ),
    )

    if diagnostic.suggestion:
        _write_line(
            stream,
            f"  Suggestion: {diagnostic.suggestion}",
        )

    if verbose:
        _write_line(
            stream,
            f"  Source: {diagnostic.source_file}",
        )
        if diagnostic.subject is not None:
            _write_line(
                stream,
                f"  Subject: {diagnostic.subject}",
            )


def _build_project_check_application() -> ProjectCheckApplication:
    """Obtain the composed project-check application from bootstrap."""

    from gf_wordbench.bootstrap import (
        build_project_check_application,
    )

    application = build_project_check_application()
    _require_project_application(application)
    return application


def _build_scenario_check_application() -> ScenarioCheckApplication:
    """Obtain the composed scenario-check application from bootstrap."""

    from gf_wordbench.bootstrap import (
        build_scenario_check_application,
    )

    application = build_scenario_check_application()
    _require_scenario_application(application)
    return application


def _require_project_application(
    application: object,
) -> ProjectCheckApplication:
    if not isinstance(application, ProjectCheckApplication):
        raise TypeError(
            "application must satisfy ProjectCheckApplication"
        )
    return application


def _require_scenario_application(
    application: object,
) -> ScenarioCheckApplication:
    if not isinstance(application, ScenarioCheckApplication):
        raise TypeError(
            "application must satisfy ScenarioCheckApplication"
        )
    return application


def _resolve_validation_profile(
    value: object,
    *,
    legacy_project_root: Path | None,
) -> Path:
    profile = _optional_path(
        value,
        field="validation_profile",
    )
    if profile is None:
        if legacy_project_root is None:
            raise CliUsageError(
                "an explicit --profile is required"
            )
        return _legacy_profile_path(legacy_project_root)

    if legacy_project_root is not None:
        expected = _legacy_profile_path(legacy_project_root)
        if _normalized_path(profile) != _normalized_path(expected):
            raise CliUsageError(
                "--project-root conflicts with --profile"
            )
    return profile


def _legacy_profile_path(project_root: Path) -> Path:
    _require_path(project_root, field="legacy_project_root")
    return project_root / "project" / "project.toml"


def _profile_workspace_root(validation_profile: Path) -> Path:
    _require_path(
        validation_profile,
        field="validation_profile",
    )
    profile = validation_profile.expanduser().resolve(strict=False)
    if profile.name.casefold() != "project.toml":
        return profile.parent
    if profile.parent.name.casefold() == "project":
        return profile.parent.parent
    return profile.parent


def _normalized_path(value: Path) -> Path:
    _require_path(value, field="path")
    return value.expanduser().resolve(strict=False)


def _require_cli_command(
    request: CliRequest,
    expected: CliCommand,
) -> None:
    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")
    if not isinstance(expected, CliCommand):
        raise TypeError("expected must be CliCommand")
    if request.command is not expected:
        raise CliUsageError(
            f"CLI request must identify {expected.value}"
        )


def _normalize_scenario_ids(
    values: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field} must be a tuple")

    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(
                f"{field}[{index}] must be a string"
            )
        identifier = str(
            validate_scenario_id(
                value,
                field=f"{field}[{index}]",
            )
        )
        if identifier in seen:
            raise ValueError(
                f"duplicate scenario ID {identifier!r}"
            )
        seen.add(identifier)
        normalized.append(identifier)
    return tuple(normalized)


def _request_bool(
    request: CliRequest,
    name: str,
) -> bool:
    value = request.get(name, False)
    if value is None:
        return False
    return _require_bool(value, field=name)


def _request_first(
    request: CliRequest,
    *names: str,
) -> object:
    for name in names:
        value = request.get(name)
        if value is not None:
            return value
    return None


def _namespace_first(
    namespace: argparse.Namespace,
    *names: str,
) -> object:
    for name in names:
        value = getattr(namespace, name, None)
        if value is not None:
            return value
    return None


def _command_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str):
        raise TypeError(
            "command identifier must be a string or enum"
        )

    normalized = value.strip()
    if not normalized or "\x00" in normalized:
        raise ValueError("command identifier is invalid")
    return normalized


def _namespace_bool(
    namespace: argparse.Namespace,
    name: str,
) -> bool:
    return _require_bool(
        getattr(namespace, name, False),
        field=name,
    )


def _optional_path(
    value: object,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        if not value.strip():
            raise ValueError(
                f"{field} must not be empty"
            )
        path = Path(value)
    else:
        raise TypeError(
            f"{field} must be a path or None"
        )

    _require_path(path, field=field)
    return path


def _require_optional_path(
    value: object,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    return _require_path(value, field=field)


def _require_path(
    value: object,
    *,
    field: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(
            f"{field} must be pathlib.Path"
        )
    if "\x00" in str(value):
        raise ValueError(
            f"{field} must not contain NUL"
        )
    return value


def _require_bool(
    value: object,
    *,
    field: str,
) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be bool")
    return value


def _require_message(
    value: object,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(
            f"{field} must be a non-empty string"
        )
    if value != value.strip():
        raise ValueError(
            f"{field} must not have outer whitespace"
        )
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(
            f"{field} must be a single-line string without NUL"
        )
    if len(value) > _MAX_ERROR_MESSAGE_LENGTH:
        raise ValueError(
            f"{field} exceeds "
            f"{_MAX_ERROR_MESSAGE_LENGTH} characters"
        )
    return value


def _write_error(stream: TextIO, message: str) -> None:
    _write_line(stream, f"ERROR: {message}")


def _write_line(stream: TextIO, text: str) -> None:
    writer = getattr(stream, "write", None)
    if not callable(writer):
        raise TypeError(
            "output stream must provide write()"
        )
    writer(f"{text}\n")


def _safe_exception_message(exc: BaseException) -> str:
    message = " ".join(
        str(exc).replace("\x00", "\\x00").split()
    )
    if not message:
        message = type(exc).__name__
    if len(message) > _MAX_ERROR_MESSAGE_LENGTH:
        message = (
            f"{message[: _MAX_ERROR_MESSAGE_LENGTH - 3]}..."
        )
    return message


__all__ = (
    "ProjectCheckApplication",
    "ProjectCheckCommandResult",
    "ProjectCheckRequest",
    "ScenarioCheckApplication",
    "ScenarioCheckCommandResult",
    "ScenarioCheckIssue",
    "ScenarioCheckRequest",
    "SubparserCollection",
    "execute_project_check",
    "execute_project_check_command",
    "execute_project_command",
    "execute_scenarios_check_command",
    "present_project_check",
    "project_check_request_from_cli_request",
    "project_check_request_from_namespace",
    "register_project_commands",
    "run_project_check",
    "run_scenarios_check",
    "scenario_check_request_from_cli_request",
)
