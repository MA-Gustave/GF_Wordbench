"""Unit tests for the canonical shared status vocabularies."""

from __future__ import annotations

from enum import StrEnum
import json
from typing import Final

import pytest

import gf_wordbench.kernel.statuses as statuses
from gf_wordbench.kernel.statuses import (
    ChangeKind,
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    OverallStatus,
    TargetKind,
    ValidationMode,
    ValidationStatus,
)

_STATUS_CONTRACTS: Final[
    tuple[type[StrEnum], tuple[tuple[str, str], ...]], ...
] = (
    (
        ValidationStatus,
        (
            ("OK", "OK"),
            ("FAIL", "FAIL"),
            ("ERROR", "ERROR"),
            ("SKIPPED", "SKIPPED"),
        ),
    ),
    (
        OverallStatus,
        (
            ("OK", "OK"),
            ("FAIL", "FAIL"),
            ("ERROR", "ERROR"),
        ),
    ),
    (
        ExecutionState,
        (
            ("COMPLETED", "completed"),
            ("TIMED_OUT", "timed_out"),
            ("CANCELLED", "cancelled"),
            ("LAUNCH_FAILED", "launch_failed"),
        ),
    ),
    (
        DiagnosticClass,
        (
            ("OK", "ok"),
            ("DIRECT", "direct"),
            ("DOWNSTREAM", "downstream"),
            ("AMBIGUOUS", "ambiguous"),
            ("NOISE", "noise"),
            ("SKIPPED", "skipped"),
        ),
    ),
    (
        ErrorKind,
        (
            ("OK", "OK"),
            ("OTHER", "OTHER"),
            ("TYPE", "TYPE"),
            ("SYNTAX", "SYNTAX"),
            ("INTERNAL", "INTERNAL"),
            ("TIMEOUT", "TIMEOUT"),
            ("SCRIPT", "SCRIPT"),
            ("CONFIG", "CONFIG"),
            ("IO", "IO"),
            ("TOOL", "TOOL"),
        ),
    ),
    (
        ChangeKind,
        (
            ("UNCHANGED", "unchanged"),
            ("IMPROVED", "improved"),
            ("REGRESSED", "regressed"),
            ("NEW", "new"),
            ("REMOVED", "removed"),
        ),
    ),
    (
        ValidationMode,
        (
            ("QUICK", "quick"),
            ("CHECKPOINT", "checkpoint"),
            ("RELEASE", "release"),
            ("DIAGNOSTIC", "diagnostic"),
        ),
    ),
    (
        TargetKind,
        (
            ("FILE", "file"),
            ("MODULE", "module"),
            ("CHECKPOINT", "checkpoint"),
            ("ENTRYPOINT", "entrypoint"),
            ("SCENARIO", "scenario"),
            ("PROJECT", "project"),
            ("REGRESSION", "regression"),
        ),
    ),
)


@pytest.mark.parametrize(("enum_type", "expected"), _STATUS_CONTRACTS)
def test_status_enum_members_and_values_are_exact(
    enum_type: type[StrEnum],
    expected: tuple[tuple[str, str], ...],
) -> None:
    assert tuple((member.name, member.value) for member in enum_type) == expected
    assert tuple(enum_type.__members__) == tuple(name for name, _ in expected)


@pytest.mark.parametrize(("enum_type", "expected"), _STATUS_CONTRACTS)
def test_status_values_round_trip_through_canonical_boundaries(
    enum_type: type[StrEnum],
    expected: tuple[tuple[str, str], ...],
) -> None:
    for name, value in expected:
        member = enum_type[name]
        assert enum_type(value) is member
        assert str(member) == value
        assert f"{member}" == value
        assert json.loads(json.dumps(member)) == value


@pytest.mark.parametrize(("enum_type", "expected"), _STATUS_CONTRACTS)
def test_status_enums_are_string_enums_without_aliases(
    enum_type: type[StrEnum],
    expected: tuple[tuple[str, str], ...],
) -> None:
    assert issubclass(enum_type, StrEnum)
    assert len(enum_type.__members__) == len(enum_type) == len(expected)
    assert len({member.value for member in enum_type}) == len(expected)
    assert all(isinstance(member, str) for member in enum_type)


@pytest.mark.parametrize(("enum_type", "expected"), _STATUS_CONTRACTS)
def test_unknown_status_values_are_rejected(
    enum_type: type[StrEnum],
    expected: tuple[tuple[str, str], ...],
) -> None:
    existing_values = {value for _, value in expected}
    invalid_values = {"", "unknown", " UNKNOWN ", "Ok", "failed"} - existing_values

    for value in invalid_values:
        with pytest.raises(ValueError):
            enum_type(value)


@pytest.mark.parametrize(("enum_type", "expected"), _STATUS_CONTRACTS)
def test_member_names_are_case_sensitive(
    enum_type: type[StrEnum],
    expected: tuple[tuple[str, str], ...],
) -> None:
    for name, _ in expected:
        assert enum_type[name].name == name
        with pytest.raises(KeyError):
            enum_type[name.lower()]


def test_module_exports_only_the_canonical_status_owners() -> None:
    assert statuses.__all__ == (
        "ChangeKind",
        "DiagnosticClass",
        "ErrorKind",
        "ExecutionState",
        "OverallStatus",
        "TargetKind",
        "ValidationMode",
        "ValidationStatus",
    )

    for exported_name in statuses.__all__:
        enum_type = getattr(statuses, exported_name)
        assert issubclass(enum_type, StrEnum)
        assert enum_type.__module__ == "gf_wordbench.kernel.statuses"


def test_equal_text_does_not_merge_distinct_contract_dimensions() -> None:
    same_text_members = (
        ValidationStatus.OK,
        OverallStatus.OK,
        ErrorKind.OK,
    )

    assert {type(member) for member in same_text_members} == {
        ValidationStatus,
        OverallStatus,
        ErrorKind,
    }
    assert ValidationStatus.OK is not OverallStatus.OK
    assert ValidationStatus.OK is not ErrorKind.OK
    assert OverallStatus.OK is not ErrorKind.OK
    assert ValidationStatus.SKIPPED is not DiagnosticClass.SKIPPED


def test_validation_and_overall_status_have_different_terminal_domains() -> None:
    assert ValidationStatus.SKIPPED.value == "SKIPPED"
    assert "SKIPPED" not in OverallStatus.__members__
    assert tuple(member.value for member in OverallStatus) == (
        "OK",
        "FAIL",
        "ERROR",
    )


def test_execution_state_does_not_encode_not_started() -> None:
    assert tuple(member.value for member in ExecutionState) == (
        "completed",
        "timed_out",
        "cancelled",
        "launch_failed",
    )
    assert "not_started" not in {member.value for member in ExecutionState}


def test_mode_and_target_dimensions_remain_independent() -> None:
    assert ValidationMode.CHECKPOINT.value == TargetKind.CHECKPOINT.value
    assert ValidationMode.CHECKPOINT is not TargetKind.CHECKPOINT
    assert type(ValidationMode.CHECKPOINT) is ValidationMode
    assert type(TargetKind.CHECKPOINT) is TargetKind
