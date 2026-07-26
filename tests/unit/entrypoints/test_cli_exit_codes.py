"""Unit tests for the canonical GF Wordbench CLI exit-code contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import pytest

from gf_wordbench.entrypoints.cli.exit_codes import (
    EXIT_CANCELLED,
    EXIT_OK,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_FAILED,
    ExitCode,
    determine_exit_code,
    normalize_parser_exit_code,
)
from gf_wordbench.kernel.statuses import OverallStatus


@dataclass(frozen=True, slots=True)
class _CommandResult:
    overall_status: OverallStatus
    cancelled: bool = False
    child_exit_code: int | None = None
    fail_count: int = 0


def test_canonical_exit_code_values_are_stable_and_unique() -> None:
    assert EXIT_OK == 0
    assert EXIT_VALIDATION_FAILED == 1
    assert EXIT_USAGE_ERROR == 2
    assert EXIT_RUNTIME_ERROR == 3
    assert EXIT_CANCELLED == 4

    assert issubclass(ExitCode, IntEnum)
    assert tuple(ExitCode) == (
        ExitCode.OK,
        ExitCode.VALIDATION_FAILED,
        ExitCode.USAGE_ERROR,
        ExitCode.RUNTIME_ERROR,
        ExitCode.CANCELLED,
    )
    assert tuple(int(code) for code in ExitCode) == (0, 1, 2, 3, 4)
    assert len({int(code) for code in ExitCode}) == 5

    assert ExitCode.OK == EXIT_OK
    assert ExitCode.VALIDATION_FAILED == EXIT_VALIDATION_FAILED
    assert ExitCode.USAGE_ERROR == EXIT_USAGE_ERROR
    assert ExitCode.RUNTIME_ERROR == EXIT_RUNTIME_ERROR
    assert ExitCode.CANCELLED == EXIT_CANCELLED


@pytest.mark.parametrize(
    ("status", "cancelled", "expected"),
    [
        (OverallStatus.OK, False, EXIT_OK),
        (OverallStatus.FAIL, False, EXIT_VALIDATION_FAILED),
        (OverallStatus.ERROR, False, EXIT_RUNTIME_ERROR),
        (OverallStatus.OK, True, EXIT_CANCELLED),
        (OverallStatus.FAIL, True, EXIT_CANCELLED),
        (OverallStatus.ERROR, True, EXIT_RUNTIME_ERROR),
    ],
)
def test_complete_command_outcome_maps_to_the_canonical_code(
    status: OverallStatus,
    cancelled: bool,
    expected: int,
) -> None:
    code = determine_exit_code(
        _CommandResult(
            overall_status=status,
            cancelled=cancelled,
        )
    )

    assert type(code) is int
    assert code == expected


def test_runtime_error_outranks_controlled_cancellation_and_prior_failure() -> None:
    result = _CommandResult(
        overall_status=OverallStatus.ERROR,
        cancelled=True,
        child_exit_code=0,
        fail_count=8,
    )

    assert determine_exit_code(result) == EXIT_RUNTIME_ERROR


def test_controlled_cancellation_outranks_completed_validation_failure() -> None:
    result = _CommandResult(
        overall_status=OverallStatus.FAIL,
        cancelled=True,
        child_exit_code=1,
        fail_count=3,
    )

    assert determine_exit_code(result) == EXIT_CANCELLED


@pytest.mark.parametrize("child_exit_code", [0, 1, 2, 3, 4, 42, -9, None])
def test_child_process_exit_codes_are_recorded_but_never_forwarded(
    child_exit_code: int | None,
) -> None:
    successful = _CommandResult(
        overall_status=OverallStatus.OK,
        child_exit_code=child_exit_code,
    )
    failed = _CommandResult(
        overall_status=OverallStatus.FAIL,
        child_exit_code=child_exit_code,
    )

    assert determine_exit_code(successful) == EXIT_OK
    assert determine_exit_code(failed) == EXIT_VALIDATION_FAILED


def test_fail_count_does_not_replace_aggregate_overall_status() -> None:
    successful = _CommandResult(
        overall_status=OverallStatus.OK,
        fail_count=99,
    )
    errored = _CommandResult(
        overall_status=OverallStatus.ERROR,
        fail_count=0,
    )

    assert determine_exit_code(successful) == EXIT_OK
    assert determine_exit_code(errored) == EXIT_RUNTIME_ERROR


@pytest.mark.parametrize(
    ("parser_value", "expected"),
    [
        (None, EXIT_OK),
        (0, EXIT_OK),
        (EXIT_OK, EXIT_OK),
        (EXIT_USAGE_ERROR, EXIT_USAGE_ERROR),
        ("invalid arguments", EXIT_USAGE_ERROR),
        (object(), EXIT_USAGE_ERROR),
    ],
)
def test_parser_termination_values_are_normalized(
    parser_value: object,
    expected: int,
) -> None:
    code = normalize_parser_exit_code(parser_value)

    assert type(code) is int
    assert code == expected


@pytest.mark.parametrize("parser_value", [True, False])
def test_boolean_parser_values_are_not_treated_as_integer_exit_codes(
    parser_value: bool,
) -> None:
    assert normalize_parser_exit_code(parser_value) == EXIT_USAGE_ERROR


@pytest.mark.parametrize("parser_value", [1, 3, 4, 42, -1])
def test_noncanonical_integer_parser_failures_map_to_usage_error(
    parser_value: int,
) -> None:
    assert normalize_parser_exit_code(parser_value) == EXIT_USAGE_ERROR


@pytest.mark.parametrize(
    "invalid_status",
    [
        "OK",
        "FAIL",
        "ERROR",
        None,
        0,
        object(),
    ],
)
def test_exit_code_mapping_rejects_noncanonical_status_values(
    invalid_status: object,
) -> None:
    result = _CommandResult(
        overall_status=invalid_status,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="overall_status"):
        determine_exit_code(result)


def test_exit_code_mapping_rejects_non_boolean_cancellation_state() -> None:
    result = _CommandResult(
        overall_status=OverallStatus.OK,
        cancelled=1,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="cancelled"):
        determine_exit_code(result)


def test_exit_code_mapping_requires_a_structured_command_result() -> None:
    with pytest.raises(TypeError, match="command result"):
        determine_exit_code(object())
