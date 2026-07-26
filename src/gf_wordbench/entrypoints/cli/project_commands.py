"""CLI adapter for the canonical ``project check`` command."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO, runtime_checkable

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
)
from gf_wordbench.projects.models import (
    ProjectDiagnostic,
    ProjectDiagnosticSeverity,
    ProjectValidationResult,
)

from .exit_codes import EXIT_OK, EXIT_RUNTIME_ERROR, EXIT_USAGE_OR_CONFIG

_PROJECT_COMMAND = "project"
_PROJECT_CHECK_COMMAND = "check"


@runtime_checkable
class ProjectCheckApplication(Protocol):
    def check_project(
        self,
        *,
        project_root: Path | None,
        strict: bool,
        probe_gf: bool,
        gf_executable: Path | None,
        rgl_root: Path | None,
    ) -> ProjectValidationResult:
        ...


class SubparserCollection(Protocol):
    def add_parser(
        self,
        name: str,
        **kwargs: object,
    ) -> argparse.ArgumentParser:
        ...


@dataclass(frozen=True, slots=True)
class ProjectCheckRequest:
    project_root: Path | None = None
    strict: bool = False
    probe_gf: bool = False
    gf_executable: Path | None = None
    rgl_root: Path | None = None
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "strict",
            "probe_gf",
            "quiet",
            "verbose",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be bool")

        if self.quiet and self.verbose:
            raise ValueError("--quiet and --verbose cannot be used together")

        for field_name in (
            "project_root",
            "gf_executable",
            "rgl_root",
        ):
            value = getattr(self, field_name)
            if value is not None:
                if not isinstance(value, Path):
                    raise TypeError(f"{field_name} must be pathlib.Path or None")
                if "\x00" in str(value):
                    raise ValueError(f"{field_name} must not contain NUL")


def register_project_commands(
    subparsers: SubparserCollection,
) -> argparse.ArgumentParser:
    project_parser = subparsers.add_parser(
        _PROJECT_COMMAND,
        help="Inspect or validate the active project.",
        description="Active-project contract operations.",
    )
    project_subparsers = project_parser.add_subparsers(
        dest="project_command",
        metavar="COMMAND",
        required=True,
    )

    check_parser = project_subparsers.add_parser(
        _PROJECT_CHECK_COMMAND,
        help="Validate the active project contract.",
        description=(
            "Validate project configuration, semantics, paths, registries, "
            "required assets, and contract consistency without running full "
            "validation."
        ),
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict project and environment checks.",
    )
    check_parser.add_argument(
        "--probe-gf",
        action="store_true",
        help="Resolve GF, run gf --version, and validate the RGL path.",
    )
    check_parser.add_argument(
        "--project-root",
        type=Path,
        metavar="PATH",
        help="GF Wordbench workspace root containing project/project.toml.",
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
        help="Explicit root of the Resource Grammar Library.",
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
        command_name="project.check",
    )
    return project_parser


def project_check_request_from_namespace(
    namespace: argparse.Namespace,
) -> ProjectCheckRequest:
    if not isinstance(namespace, argparse.Namespace):
        raise TypeError("namespace must be argparse.Namespace")

    command_group = getattr(namespace, "command_group", _PROJECT_COMMAND)
    project_command = getattr(namespace, "project_command", None)
    command_name = getattr(namespace, "command_name", None)

    if command_group != _PROJECT_COMMAND:
        raise ValueError("namespace does not identify a project command")
    if (
        project_command != _PROJECT_CHECK_COMMAND
        and command_name != "project.check"
    ):
        raise ValueError("namespace does not identify project check")

    return ProjectCheckRequest(
        project_root=_optional_path(
            getattr(namespace, "project_root", None),
            field="project_root",
        ),
        strict=_namespace_bool(namespace, "strict"),
        probe_gf=_namespace_bool(namespace, "probe_gf"),
        gf_executable=_optional_path(
            getattr(namespace, "gf_exe", None),
            field="gf_exe",
        ),
        rgl_root=_optional_path(
            getattr(namespace, "rgl_root", None),
            field="rgl_root",
        ),
        quiet=_namespace_bool(namespace, "quiet"),
        verbose=_namespace_bool(namespace, "verbose"),
    )


def execute_project_command(
    namespace: argparse.Namespace,
    application: ProjectCheckApplication,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    try:
        request = project_check_request_from_namespace(namespace)
    except (TypeError, ValueError) as exc:
        _write_error(stderr, str(exc))
        return EXIT_USAGE_OR_CONFIG

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
    if not isinstance(request, ProjectCheckRequest):
        raise TypeError("request must be ProjectCheckRequest")
    if not isinstance(application, ProjectCheckApplication):
        raise TypeError(
            "application must satisfy ProjectCheckApplication"
        )

    try:
        result = application.check_project(
            project_root=request.project_root,
            strict=request.strict,
            probe_gf=request.probe_gf,
            gf_executable=request.gf_executable,
            rgl_root=request.rgl_root,
        )
        if not isinstance(result, ProjectValidationResult):
            raise TypeError(
                "check_project() must return ProjectValidationResult"
            )
    except (ConfigurationError, ContractViolationError, ValueError) as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_USAGE_OR_CONFIG
    except (CancellationRequested, GFWordbenchError, OSError) as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_RUNTIME_ERROR
    except Exception as exc:
        _write_error(stderr, _safe_exception_message(exc))
        return EXIT_RUNTIME_ERROR

    present_project_check(
        result,
        quiet=request.quiet,
        verbose=request.verbose,
        stdout=stdout,
        stderr=stderr,
    )
    return EXIT_OK if result.ok else EXIT_USAGE_OR_CONFIG


def present_project_check(
    result: ProjectValidationResult,
    *,
    quiet: bool = False,
    verbose: bool = False,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> None:
    if not isinstance(result, ProjectValidationResult):
        raise TypeError("result must be ProjectValidationResult")
    if type(quiet) is not bool:
        raise TypeError("quiet must be bool")
    if type(verbose) is not bool:
        raise TypeError("verbose must be bool")
    if quiet and verbose:
        raise ValueError("quiet and verbose cannot both be enabled")

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
                f"Project check: {status} "
                f"({error_count} errors, {warning_count} warnings)"
            ),
        )
        return

    _write_line(stdout, f"Project check: {status}")
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
        raise TypeError("diagnostic must be ProjectDiagnostic")

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
        _write_line(stream, f"  Suggestion: {diagnostic.suggestion}")

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


def _namespace_bool(
    namespace: argparse.Namespace,
    name: str,
) -> bool:
    value = getattr(namespace, name, False)
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")
    return value


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
            raise ValueError(f"{field} must not be empty")
        path = Path(value)
    else:
        raise TypeError(f"{field} must be a path or None")

    if "\x00" in str(path):
        raise ValueError(f"{field} must not contain NUL")
    return path


def _write_error(stream: TextIO, message: str) -> None:
    _write_line(stream, f"ERROR: {message}")


def _write_line(stream: TextIO, text: str) -> None:
    if not hasattr(stream, "write"):
        raise TypeError("output stream must provide write()")
    stream.write(f"{text}\n")


def _safe_exception_message(exc: BaseException) -> str:
    message = " ".join(str(exc).replace("\x00", "\\x00").split())
    if not message:
        message = type(exc).__name__
    if len(message) > 2_000:
        message = f"{message[:1997]}..."
    return message


__all__ = (
    "ProjectCheckApplication",
    "ProjectCheckRequest",
    "SubparserCollection",
    "execute_project_check",
    "execute_project_command",
    "present_project_check",
    "project_check_request_from_namespace",
    "register_project_commands",
)
