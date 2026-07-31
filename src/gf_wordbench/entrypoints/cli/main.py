"""GF Wordbench command-line entrypoint.

This module owns process-level concerns only:

- argument normalization and parsing;
- canonical command dispatch;
- result presentation;
- exit-code mapping;
- bounded fallback error reporting.

Command-specific CLI wrappers remain in their owning adapter modules.
Concrete dependency composition belongs to ``gf_wordbench.bootstrap``.
Every public CLI wrapper accepts one :class:`CliRequest` and returns a
structured result exposing ``overall_status``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Final, Literal, TypeAlias

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
    PathSecurityError,
)

from .exit_codes import (
    EXIT_CANCELLED,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    HasOverallStatus,
    determine_exit_code,
    normalize_parser_exit_code,
)
from .output import present_error, present_result
from .parser import (
    CliCommand,
    CliRequest,
    CliUsageError,
    parse_cli_request,
)

CommandResult: TypeAlias = HasOverallStatus
CommandHandler: TypeAlias = Callable[[CliRequest], CommandResult]
ErrorCategory: TypeAlias = Literal[
    "usage",
    "configuration",
    "runtime",
]

_CANONICAL_COMMANDS: Final[tuple[str, ...]] = tuple(
    command.value for command in CliCommand
)
_MAX_FALLBACK_ERROR_LENGTH: Final[int] = 2_000


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical GF Wordbench CLI and return its stable exit code."""

    try:
        request = parse_cli_request(_normalize_argv(argv))
    except SystemExit as exc:
        return _parser_exit_code(exc)
    except CliUsageError as exc:
        return _report_error(
            exc,
            category="usage",
            exit_code=EXIT_USAGE_ERROR,
        )
    except (
        ConfigurationError,
        ContractViolationError,
        PathSecurityError,
    ) as exc:
        return _report_error(
            exc,
            category="configuration",
            exit_code=EXIT_USAGE_ERROR,
        )
    except (TypeError, ValueError) as exc:
        return _report_error(
            exc,
            category="usage",
            exit_code=EXIT_USAGE_ERROR,
        )
    except KeyboardInterrupt:
        return _report_error(
            CancellationRequested("command-line parsing was cancelled"),
            category="runtime",
            exit_code=EXIT_CANCELLED,
        )
    except Exception as exc:
        return _report_error(
            exc,
            category="runtime",
            exit_code=EXIT_RUNTIME_ERROR,
        )

    return _execute_request(request)


def _execute_request(request: CliRequest) -> int:
    """Dispatch, present, and map one canonical request to an exit code."""

    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")

    try:
        result = dispatch_cli_request(request)

        if not isinstance(result, HasOverallStatus):
            raise TypeError(
                "command handler must return a structured result "
                "exposing overall_status"
            )

        present_result(result, request=request)
        return determine_exit_code(result)

    except CliUsageError as exc:
        return _report_error(
            exc,
            category="usage",
            exit_code=EXIT_USAGE_ERROR,
        )
    except (
        ConfigurationError,
        ContractViolationError,
        PathSecurityError,
    ) as exc:
        return _report_error(
            exc,
            category="configuration",
            exit_code=EXIT_USAGE_ERROR,
        )
    except CancellationRequested as exc:
        return _report_error(
            exc,
            category="runtime",
            exit_code=EXIT_CANCELLED,
        )
    except KeyboardInterrupt:
        return _report_error(
            CancellationRequested("operation cancelled by user"),
            category="runtime",
            exit_code=EXIT_CANCELLED,
        )
    except BrokenPipeError:
        return EXIT_RUNTIME_ERROR
    except GFWordbenchError as exc:
        return _report_error(
            exc,
            category="runtime",
            exit_code=EXIT_RUNTIME_ERROR,
        )
    except (TypeError, ValueError) as exc:
        return _report_error(
            exc,
            category="runtime",
            exit_code=EXIT_RUNTIME_ERROR,
        )
    except Exception as exc:
        return _report_error(
            exc,
            category="runtime",
            exit_code=EXIT_RUNTIME_ERROR,
        )


def dispatch_cli_request(request: CliRequest) -> CommandResult:
    """Dispatch one parsed request to its owning CLI adapter."""

    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")

    return _command_handler(request.command)(request)


def _command_handler(command: object) -> CommandHandler:
    """Resolve one canonical command handler without eager adapter imports."""

    command_name = _normalize_command(command)

    match command_name:
        case CliCommand.LANGUAGE_PROBE:
            from .language_commands import execute_language_probe_command

            return execute_language_probe_command

        case CliCommand.VALIDATE:
            from .audit_commands import execute_validate_cli_command

            return execute_validate_cli_command

        case CliCommand.PROJECT_CHECK:
            from .project_commands import execute_project_check_command

            return execute_project_check_command

        case CliCommand.SCENARIOS_CHECK:
            from .project_commands import execute_scenarios_check_command

            return execute_scenarios_check_command

        case CliCommand.GOLD_UPDATE:
            from .maintenance_commands import execute_gold_update_command

            return execute_gold_update_command

        case CliCommand.SCHEMAS_CHECK:
            from .maintenance_commands import execute_schemas_check_command

            return execute_schemas_check_command

        case CliCommand.REPORTS_CHECK:
            from .maintenance_commands import execute_reports_check_command

            return execute_reports_check_command

    raise AssertionError(
        f"unhandled canonical command: {command_name.value}"
    )


def _normalize_command(value: object) -> CliCommand:
    """Normalize a command value to the canonical typed command enum."""

    if isinstance(value, CliCommand):
        return value

    if isinstance(value, Enum):
        value = value.value

    if not isinstance(value, str):
        raise CliUsageError(
            "parsed request does not define a command"
        )

    candidate = value.strip().lower()
    if not candidate or "\x00" in candidate:
        raise CliUsageError(
            "parsed request contains an invalid command"
        )

    try:
        return CliCommand(candidate)
    except ValueError as exc:
        supported = ", ".join(_CANONICAL_COMMANDS)
        raise CliUsageError(
            f"unsupported command {candidate!r}; "
            f"expected one of: {supported}"
        ) from exc


def _normalize_argv(
    argv: Sequence[str] | None,
) -> tuple[str, ...]:
    """Return a validated immutable argument sequence."""

    if argv is None:
        return tuple(sys.argv[1:])

    if isinstance(argv, (str, bytes, bytearray)):
        raise TypeError(
            "argv must be a sequence of argument strings"
        )

    arguments = tuple(argv)

    for index, argument in enumerate(arguments):
        if not isinstance(argument, str):
            raise TypeError(
                f"argv[{index}] must be a string"
            )
        if "\x00" in argument:
            raise ValueError(
                f"argv[{index}] must not contain NUL"
            )

    return arguments


def _parser_exit_code(exc: SystemExit) -> int:
    """Normalize argparse help, version, and usage termination."""

    code = exc.code

    if code is not None and type(code) is not int:
        _present_error_safely(
            CliUsageError(str(code)),
            category="usage",
        )

    return normalize_parser_exit_code(code)


def _report_error(
    error: BaseException,
    *,
    category: ErrorCategory,
    exit_code: int,
) -> int:
    """Present an error without allowing presentation failure to escape."""

    _present_error_safely(
        error,
        category=category,
    )
    return exit_code


def _present_error_safely(
    error: BaseException,
    *,
    category: ErrorCategory,
) -> None:
    """Present one error, falling back to bounded stderr output."""

    try:
        present_error(
            error,
            category=category,
        )
    except Exception:
        _write_fallback_error(error)


def _write_fallback_error(error: BaseException) -> None:
    """Write a bounded fallback message when presentation itself fails."""

    text = " ".join(
        str(error)
        .replace("\x00", "\\x00")
        .split()
    )

    if not text:
        text = type(error).__name__

    if len(text) > _MAX_FALLBACK_ERROR_LENGTH:
        text = (
            f"{text[: _MAX_FALLBACK_ERROR_LENGTH - 3]}..."
        )

    try:
        sys.stderr.write(f"ERROR: {text}\n")
        sys.stderr.flush()
    except Exception:
        pass


__all__ = (
    "CommandHandler",
    "CommandResult",
    "dispatch_cli_request",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
