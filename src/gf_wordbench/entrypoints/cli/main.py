"""GF Wordbench command-line entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Final, Protocol, TypeAlias

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
    PathSecurityError,
)

from .exit_codes import EXIT_RUNTIME_ERROR, EXIT_USAGE_OR_CONFIG, exit_code_for_result
from .output import present_error, present_result
from .parser import CliUsageError, parse_cli_request

CommandResult: TypeAlias = object
CommandHandler: TypeAlias = Callable[["CliRequest"], CommandResult]

_CANONICAL_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "validate",
        "project",
        "scenarios",
        "gold",
        "schemas",
        "reports",
    }
)
_MAX_FALLBACK_ERROR_LENGTH: Final[int] = 2_000


class CliRequest(Protocol):
    """Minimum parsed-request contract consumed by the dispatcher."""

    command: str | Enum


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical GF Wordbench CLI and return its stable exit code."""

    arguments = _normalize_argv(argv)

    try:
        request = parse_cli_request(arguments)
    except SystemExit as exc:
        return _parser_exit_code(exc)
    except CliUsageError as exc:
        _present_error_safely(exc, category="usage")
        return EXIT_USAGE_OR_CONFIG
    except (ConfigurationError, ContractViolationError, PathSecurityError) as exc:
        _present_error_safely(exc, category="configuration")
        return EXIT_USAGE_OR_CONFIG
    except KeyboardInterrupt:
        _present_error_safely(
            CancellationRequested("command-line parsing was cancelled"),
            category="runtime",
        )
        return EXIT_RUNTIME_ERROR
    except Exception as exc:
        _present_error_safely(exc, category="runtime")
        return EXIT_RUNTIME_ERROR

    try:
        result = dispatch_cli_request(request)
        present_result(result, request=request)
        return exit_code_for_result(result)
    except CliUsageError as exc:
        _present_error_safely(exc, category="usage")
        return EXIT_USAGE_OR_CONFIG
    except (ConfigurationError, ContractViolationError, PathSecurityError) as exc:
        _present_error_safely(exc, category="configuration")
        return EXIT_USAGE_OR_CONFIG
    except CancellationRequested as exc:
        _present_error_safely(exc, category="runtime")
        return EXIT_RUNTIME_ERROR
    except KeyboardInterrupt:
        _present_error_safely(
            CancellationRequested("operation cancelled by user"),
            category="runtime",
        )
        return EXIT_RUNTIME_ERROR
    except GFWordbenchError as exc:
        _present_error_safely(exc, category="runtime")
        return EXIT_RUNTIME_ERROR
    except BrokenPipeError:
        return EXIT_RUNTIME_ERROR
    except Exception as exc:
        _present_error_safely(exc, category="runtime")
        return EXIT_RUNTIME_ERROR


def dispatch_cli_request(request: CliRequest) -> CommandResult:
    """Dispatch one parsed request to its owning application adapter."""

    command = _command_name(request)
    handler = _command_handler(command)
    return handler(request)


def _command_handler(command: str) -> CommandHandler:
    if command == "validate":
        from .audit_commands import execute_validate_command

        return execute_validate_command

    if command == "project":
        from .project_commands import execute_project_check_command

        return execute_project_check_command

    if command == "scenarios":
        from .project_commands import execute_scenarios_check_command

        return execute_scenarios_check_command

    if command == "gold":
        from .maintenance_commands import execute_gold_update_command

        return execute_gold_update_command

    if command == "schemas":
        from .maintenance_commands import execute_schemas_check_command

        return execute_schemas_check_command

    if command == "reports":
        from .maintenance_commands import execute_reports_check_command

        return execute_reports_check_command

    supported = ", ".join(sorted(_CANONICAL_COMMANDS))
    raise CliUsageError(
        f"unsupported command {command!r}; expected one of: {supported}"
    )


def _command_name(request: CliRequest) -> str:
    value = getattr(request, "command", None)
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str):
        raise CliUsageError("parsed request does not define a command")

    command = value.strip().lower()
    if not command or "\x00" in command:
        raise CliUsageError("parsed request contains an invalid command")
    return command


def _normalize_argv(argv: Sequence[str] | None) -> tuple[str, ...]:
    if argv is None:
        return tuple(sys.argv[1:])
    if isinstance(argv, (str, bytes, bytearray)):
        raise TypeError("argv must be a sequence of argument strings")

    arguments = tuple(argv)
    for index, argument in enumerate(arguments):
        if not isinstance(argument, str):
            raise TypeError(f"argv[{index}] must be a string")
        if "\x00" in argument:
            raise ValueError(f"argv[{index}] must not contain NUL")
    return arguments


def _parser_exit_code(exc: SystemExit) -> int:
    code = exc.code
    if code is None:
        return 0
    if type(code) is int:
        return 0 if code == 0 else EXIT_USAGE_OR_CONFIG
    _present_error_safely(CliUsageError(str(code)), category="usage")
    return EXIT_USAGE_OR_CONFIG


def _present_error_safely(error: BaseException, *, category: str) -> None:
    try:
        present_error(error, category=category)
    except Exception:
        _write_fallback_error(error)


def _write_fallback_error(error: BaseException) -> None:
    text = " ".join(str(error).replace("\x00", "\\x00").split())
    if not text:
        text = type(error).__name__
    if len(text) > _MAX_FALLBACK_ERROR_LENGTH:
        text = f"{text[: _MAX_FALLBACK_ERROR_LENGTH - 3]}..."
    try:
        sys.stderr.write(f"ERROR: {text}\n")
        sys.stderr.flush()
    except Exception:
        pass


__all__ = (
    "CliRequest",
    "CommandHandler",
    "CommandResult",
    "dispatch_cli_request",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
