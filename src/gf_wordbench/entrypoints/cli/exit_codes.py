"""Canonical GF Wordbench process exit codes and command-outcome mapping."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    PathSecurityError,
)
from gf_wordbench.kernel.statuses import OverallStatus

EXIT_OK: Final[int] = 0
EXIT_VALIDATION_FAILED: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_RUNTIME_ERROR: Final[int] = 3
EXIT_CANCELLED: Final[int] = 4


@unique
class ExitCode(IntEnum):
    """Allocated GF Wordbench command-level exit codes."""

    OK = EXIT_OK
    VALIDATION_FAILED = EXIT_VALIDATION_FAILED
    USAGE_ERROR = EXIT_USAGE_ERROR
    RUNTIME_ERROR = EXIT_RUNTIME_ERROR
    CANCELLED = EXIT_CANCELLED


CANONICAL_EXIT_CODES: Final[tuple[int, ...]] = tuple(int(code) for code in ExitCode)
CANONICAL_EXIT_CODE_SET: Final[frozenset[int]] = frozenset(CANONICAL_EXIT_CODES)
RESERVED_EXIT_CODE_RANGE: Final[range] = range(5, 64)
PORTABLE_EXIT_CODE_RANGE: Final[range] = range(256)

_STATUS_TO_EXIT_CODE: Final[dict[OverallStatus, ExitCode]] = {
    OverallStatus.OK: ExitCode.OK,
    OverallStatus.FAIL: ExitCode.VALIDATION_FAILED,
    OverallStatus.ERROR: ExitCode.RUNTIME_ERROR,
}


@runtime_checkable
class HasOverallStatus(Protocol):
    """Minimum structured command-result surface needed by the CLI adapter."""

    overall_status: OverallStatus


def determine_exit_code(
    command_result: HasOverallStatus,
    *,
    cancelled: bool | None = None,
    runtime_error: bool = False,
    cancellation_error: bool = False,
) -> int:
    """Map one complete structured command result to a canonical exit code."""

    if not isinstance(command_result, HasOverallStatus):
        raise TypeError("command result must expose overall_status")
    status = command_result.overall_status
    if not isinstance(status, OverallStatus):
        raise TypeError("overall_status must be an OverallStatus")

    result_cancelled = getattr(command_result, "cancelled", False)
    _require_bool(result_cancelled, field="cancelled")
    if cancelled is not None:
        _require_bool(cancelled, field="cancelled")
        result_cancelled = cancelled
    _require_bool(runtime_error, field="runtime_error")
    _require_bool(cancellation_error, field="cancellation_error")

    if runtime_error or cancellation_error or status is OverallStatus.ERROR:
        return EXIT_RUNTIME_ERROR
    if result_cancelled:
        return EXIT_CANCELLED
    return int(_STATUS_TO_EXIT_CODE[status])


def exit_code_for_overall_status(
    status: OverallStatus | str,
    *,
    cancelled: bool = False,
    runtime_error: bool = False,
    cancellation_error: bool = False,
) -> int:
    """Map an already aggregated overall status to a command exit code."""

    return determine_exit_code(
        _StatusResult(coerce_overall_status(status)),
        cancelled=cancelled,
        runtime_error=runtime_error,
        cancellation_error=cancellation_error,
    )


def exit_code_for_exception(
    error: BaseException,
    *,
    operation_started: bool,
    cancellation_contained: bool = True,
) -> int:
    """Map a controlled CLI-boundary exception without masking its cause.

    Configuration, contract, and path errors map to usage only before the
    requested operation starts. Once execution starts, failure to complete or
    persist safely is a runtime error. Controlled cancellation maps to four
    only when containment and evidence preservation succeeded.
    """

    if not isinstance(error, BaseException):
        raise TypeError("error must be a BaseException")
    _require_bool(operation_started, field="operation_started")
    _require_bool(cancellation_contained, field="cancellation_contained")

    if isinstance(error, CancellationRequested):
        return EXIT_CANCELLED if cancellation_contained else EXIT_RUNTIME_ERROR

    if not operation_started and isinstance(
        error,
        (ConfigurationError, ContractViolationError, PathSecurityError),
    ):
        return EXIT_USAGE_ERROR

    return EXIT_RUNTIME_ERROR


def normalize_parser_exit_code(value: object) -> int:
    """Normalize parser termination to help success or usage failure."""

    if value is None or (type(value) is int and value == EXIT_OK):
        return EXIT_OK
    return EXIT_USAGE_ERROR


def coerce_exit_code(value: ExitCode | int) -> ExitCode:
    """Return a canonical typed exit code and reject unknown observed values."""

    if isinstance(value, ExitCode):
        return value
    if type(value) is not int:
        raise TypeError("exit code must be an integer or ExitCode")
    try:
        return ExitCode(value)
    except ValueError as exc:
        raise ValueError(f"unknown GF Wordbench exit code: {value}") from exc


def coerce_overall_status(value: OverallStatus | str) -> OverallStatus:
    """Return the canonical overall-status enum without accepting other axes."""

    if isinstance(value, OverallStatus):
        return value
    if not isinstance(value, str):
        raise TypeError("overall status must be OverallStatus or string")
    try:
        return OverallStatus(value)
    except ValueError as exc:
        raise ValueError(f"unknown overall status: {value!r}") from exc


def is_canonical_exit_code(value: object) -> bool:
    """Return whether a value is one of the five allocated application codes."""

    return isinstance(value, ExitCode) or (type(value) is int and value in CANONICAL_EXIT_CODE_SET)


def is_reserved_exit_code(value: object) -> bool:
    """Return whether a value is reserved for future GF Wordbench allocation."""

    return type(value) is int and value in RESERVED_EXIT_CODE_RANGE


def is_portable_exit_code(value: object) -> bool:
    """Return whether a value fits the cross-platform process-code range."""

    return isinstance(value, ExitCode) or (type(value) is int and value in PORTABLE_EXIT_CODE_RANGE)


def preserve_observed_exit_code(value: object) -> int:
    """Validate and preserve an observed child or wrapper exit code unchanged."""

    if type(value) is not int:
        raise TypeError("observed exit code must be an integer")
    return value


def exit_code_name(value: ExitCode | int) -> str | None:
    """Return the canonical symbolic name, or ``None`` for an unknown value."""

    if not isinstance(value, ExitCode) and type(value) is not int:
        raise TypeError("exit code must be an integer or ExitCode")
    try:
        return ExitCode(value).name
    except ValueError:
        return None


def _require_bool(value: object, *, field: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a bool")


class _StatusResult:
    __slots__ = ("overall_status",)

    def __init__(self, overall_status: OverallStatus) -> None:
        self.overall_status = overall_status


__all__ = (
    "CANONICAL_EXIT_CODES",
    "CANONICAL_EXIT_CODE_SET",
    "EXIT_CANCELLED",
    "EXIT_OK",
    "EXIT_RUNTIME_ERROR",
    "EXIT_USAGE_ERROR",
    "EXIT_VALIDATION_FAILED",
    "PORTABLE_EXIT_CODE_RANGE",
    "RESERVED_EXIT_CODE_RANGE",
    "ExitCode",
    "HasOverallStatus",
    "coerce_exit_code",
    "coerce_overall_status",
    "determine_exit_code",
    "exit_code_for_exception",
    "exit_code_for_overall_status",
    "exit_code_name",
    "is_canonical_exit_code",
    "is_portable_exit_code",
    "is_reserved_exit_code",
    "normalize_parser_exit_code",
    "preserve_observed_exit_code",
)
