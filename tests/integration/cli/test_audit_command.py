"""Integration contracts for the canonical ``validate`` CLI command."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.entrypoints.cli.audit_commands import (
    AuditCommandServices,
    CliAuditCommandError,
    ValidateCommandRequest,
    execute_validate_command,
)
from gf_wordbench.entrypoints.cli.parser import (
    CliCommand,
    CliRequest,
    CliUsageError,
    parse_cli_namespace,
    parse_cli_request,
)
from gf_wordbench.kernel.events import LifecycleEvent
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
from gf_wordbench.runs.models.results import RunResult, RunTotals

_FIXED_TIME = datetime(2026, 7, 25, 19, 0, tzinfo=UTC)


@dataclass(slots=True)
class _RecordingApplication:
    result: RunResult
    calls: list[
        tuple[
            ValidateCommandRequest,
            Callable[[], None] | None,
            Callable[[LifecycleEvent], None] | None,
        ]
    ] = field(default_factory=list)

    def run_validation(
        self,
        request: ValidateCommandRequest,
        *,
        cancellation_check: Callable[[], None] | None = None,
        event_sink: Callable[[LifecycleEvent], None] | None = None,
    ) -> RunResult:
        self.calls.append((request, cancellation_check, event_sink))
        return self.result


def _run_result(status: OverallStatus = OverallStatus.OK) -> RunResult:
    totals = RunTotals(
        files_seen=0,
        files_included=0,
        files_excluded=0,
        files_ok=0,
        files_fail=0,
        files_error=0,
        files_skipped=0,
        direct_fail=0,
        downstream_fail=0,
        ambiguous_fail=0,
        excluded_noise=0,
        scenarios_seen=0,
        scenarios_ok=0,
        scenarios_fail=0,
        scenarios_error=0,
        scenarios_skipped=0,
        required_scenario_fail=0,
        overall_status=status,
    )
    return RunResult(
        run_config=cast(Any, object()),
        run_paths=cast(Any, object()),
        started_at=_FIXED_TIME,
        finished_at=_FIXED_TIME,
        duration_ms=0,
        gf_version="3.12",
        overall_status=status,
        file_results=[],
        scenario_results=[],
        diff_entries=[],
        top_errors=[],
        totals=totals,
    )


def _canonical_arguments(tmp_path: Path) -> list[str]:
    return [
        "validate",
        "--mode",
        "diagnostic",
        "--scenario",
        "parse-negation",
        "--scenario",
        "generation-smoke",
        "--strict",
        "--no-version-probe",
        "--no-compile",
        "--compile-timeout",
        "17",
        "--scenario-timeout",
        "23",
        "--pgf-timeout",
        "31",
        "--max-files",
        "12",
        "--cpu-stats",
        "--keep-ok-details",
        "--baseline",
        str(tmp_path / "baseline" / "summary.json"),
        "--quiet",
        "--project-root",
        str(tmp_path / "workspace"),
        "--gf-exe",
        str(tmp_path / "toolchain" / "gf.exe"),
        "--rgl-root",
        str(tmp_path / "rgl"),
        "--out-root",
        str(tmp_path / "runs"),
    ]


def test_canonical_parser_and_adapter_preserve_all_validate_semantics(
    tmp_path: Path,
) -> None:
    namespace = parse_cli_namespace(_canonical_arguments(tmp_path))
    request = ValidateCommandRequest.from_namespace(namespace)

    assert request.mode is ValidationMode.DIAGNOSTIC
    assert tuple(map(str, request.scenarios)) == (
        "parse-negation",
        "generation-smoke",
    )
    assert request.strict is True
    assert request.no_version_probe is True
    assert request.no_compile is True
    assert request.compile_timeout_seconds == 17
    assert request.scenario_timeout_seconds == 23
    assert request.pgf_timeout_seconds == 31
    assert request.max_files == 12
    assert request.cpu_stats is True
    assert request.keep_ok_details is True
    assert request.compare_previous is True
    assert request.baseline == tmp_path / "baseline" / "summary.json"
    assert request.quiet is True
    assert request.verbose is False
    assert request.project_root == tmp_path / "workspace"
    assert request.gf_executable == tmp_path / "toolchain" / "gf.exe"
    assert request.rgl_root == tmp_path / "rgl"
    assert request.output_root == tmp_path / "runs"
    assert request.compatibility_warnings == ()


def test_parse_cli_request_is_canonical_immutable_and_typed() -> None:
    request = parse_cli_request(
        [
            "validate",
            "--mode",
            "diagnostic",
            "--scenario",
            "parse-basic",
        ]
    )

    assert request.command is CliCommand.VALIDATE
    assert request.require("mode") is ValidationMode.DIAGNOSTIC
    assert request.require("scenario_ids") == ("parse-basic",)
    assert request.compatibility_warnings == ()

    with pytest.raises(TypeError):
        request.arguments["mode"] = ValidationMode.RELEASE  # type: ignore[index]


def test_legacy_aliases_emit_one_warning_and_build_only_canonical_values(
    tmp_path: Path,
) -> None:
    namespace = parse_cli_namespace(
        [
            "validate",
            "--mode",
            "file",
            "--target-file",
            str(tmp_path / "project" / "src" / "Main.gf"),
            "--timeout-sec",
            "19",
            "--skip-version-probe",
            "--emit-cpu-stats",
            "--diff-previous",
        ]
    )

    assert namespace.mode is ValidationMode.QUICK
    assert namespace.target == tmp_path / "project" / "src" / "Main.gf"
    assert namespace.compile_timeout == 19
    assert namespace.no_version_probe is True
    assert namespace.cpu_stats is True
    assert namespace.compare_previous is True
    assert len(namespace._compatibility_warnings) == 1

    request = ValidateCommandRequest.from_namespace(namespace)

    assert request.mode is ValidationMode.QUICK
    assert request.target == tmp_path / "project" / "src" / "Main.gf"
    assert request.compile_timeout_seconds == 19
    assert request.no_version_probe is True
    assert request.cpu_stats is True
    assert request.compare_previous is True
    assert request.compatibility_warnings == namespace._compatibility_warnings


def test_parsed_cli_request_is_accepted_by_the_validation_adapter() -> None:
    parsed = parse_cli_request(["validate", "--mode", "diagnostic"])
    application = _RecordingApplication(_run_result())

    result = execute_validate_command(cast(Any, parsed), application)

    assert result is application.result
    assert len(application.calls) == 1
    assert application.calls[0][0].mode is ValidationMode.DIAGNOSTIC


def test_execute_validate_command_delegates_once_with_shared_callbacks() -> None:
    result = _run_result()
    application = _RecordingApplication(result)
    services = AuditCommandServices(run_validation=application.run_validation)
    events: list[LifecycleEvent] = []
    cancellation_checks = 0

    def cancellation_check() -> None:
        nonlocal cancellation_checks
        cancellation_checks += 1

    request = ValidateCommandRequest(
        mode=ValidationMode.DIAGNOSTIC,
        scenarios=("parse-basic",),
        max_files=5,
    )

    returned = execute_validate_command(
        request,
        services,
        cancellation_check=cancellation_check,
        event_sink=events.append,
    )

    assert returned is result
    assert len(application.calls) == 1
    captured_request, captured_cancellation, captured_sink = application.calls[0]
    assert captured_request is request
    assert captured_cancellation is cancellation_check
    assert captured_sink is not None
    captured_cancellation()
    assert cancellation_checks == 1


def test_execute_validate_command_rejects_non_run_result() -> None:
    def invalid_runner(
        request: ValidateCommandRequest,
        *,
        cancellation_check: Callable[[], None] | None = None,
        event_sink: Callable[[LifecycleEvent], None] | None = None,
    ) -> RunResult:
        del request, cancellation_check, event_sink
        return cast(RunResult, object())

    services = AuditCommandServices(run_validation=invalid_runner)

    with pytest.raises(TypeError, match="must return RunResult"):
        execute_validate_command(
            ValidateCommandRequest(mode=ValidationMode.DIAGNOSTIC),
            services,
        )


@pytest.mark.parametrize(
    ("arguments", "message"),
    (
        (["validate", "--mode", "quick"], "--target is required"),
        (
            [
                "validate",
                "--mode",
                "checkpoint",
                "--target",
                "project/src/Main.gf",
            ],
            "--target is valid only",
        ),
        (
            ["validate", "--mode", "release", "--no-compile"],
            "does not permit --no-compile",
        ),
        (
            [
                "validate",
                "--mode",
                "release",
                "--strict",
                "--no-version-probe",
            ],
            "does not permit --no-version-probe",
        ),
        (
            [
                "validate",
                "--mode",
                "quick",
                "--target",
                "project/src/Main.gf",
                "--max-files",
                "1",
            ],
            "--max-files greater than zero",
        ),
        (
            ["validate", "--mode", "diagnostic", "--quiet", "--verbose"],
            "not allowed with argument",
        ),
    ),
)
def test_invalid_mode_option_combinations_fail_before_dispatch(
    arguments: Sequence[str],
    message: str,
) -> None:
    with pytest.raises(CliUsageError, match=message):
        parse_cli_namespace(arguments)


def test_duplicate_scenario_ids_are_rejected_at_cli_boundary() -> None:
    with pytest.raises(CliUsageError, match="duplicate ID"):
        parse_cli_namespace(
            [
                "validate",
                "--mode",
                "diagnostic",
                "--scenario",
                "parse-basic",
                "--scenario",
                "parse-basic",
            ]
        )


@pytest.mark.parametrize(
    "values",
    (
        {
            "mode": ValidationMode.DIAGNOSTIC,
            "quiet": True,
            "verbose": True,
        },
        {
            "mode": ValidationMode.RELEASE,
            "no_compile": True,
        },
        {
            "mode": ValidationMode.QUICK,
            "target": Path("Main.gf"),
            "max_files": 1,
        },
        {
            "mode": ValidationMode.DIAGNOSTIC,
            "baseline": Path("summary.json"),
            "compare_previous": False,
        },
    ),
)
def test_adapter_revalidates_untrusted_namespace_values(
    values: Mapping[str, object],
) -> None:
    with pytest.raises(CliAuditCommandError):
        ValidateCommandRequest.from_namespace(values)
