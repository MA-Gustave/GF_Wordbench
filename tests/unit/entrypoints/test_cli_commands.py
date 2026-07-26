"""Unit tests for GF Wordbench CLI command adapters."""

from __future__ import annotations

from dataclasses import MISSING, fields
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

import gf_wordbench.entrypoints.cli.main as cli_main
from gf_wordbench.entrypoints.cli.audit_commands import (
    AuditCommandServices,
    CliAuditCommandError,
    ValidateCommandRequest,
    execute_validate_command,
    normalize_validation_mode,
    validate_command_request,
)
from gf_wordbench.entrypoints.cli.exit_codes import (
    EXIT_OK,
    EXIT_USAGE_OR_CONFIG,
)
from gf_wordbench.entrypoints.cli.maintenance_commands import (
    ApplyProjectResetCommand,
    MaintenanceCommandKind,
    PlanProjectResetCommand,
    maintenance_command_is_destructive,
    maintenance_command_is_dry_run,
    maintenance_command_kind,
)
from gf_wordbench.entrypoints.cli.parser import (
    CliUsageError,
    parse_cli_namespace,
    parse_cli_request,
)
from gf_wordbench.entrypoints.cli.project_commands import (
    ProjectCheckRequest,
    execute_project_check,
    project_check_request_from_namespace,
)
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.models import (
    ProjectDiagnostic,
    ProjectDiagnosticSeverity,
    ProjectValidationResult,
)
from gf_wordbench.projects.resetter import ResetPlan, ResetRequest
from gf_wordbench.runs.models.results import RunResult


class _AuditApplication:
    def __init__(self, result: RunResult) -> None:
        self.result = result
        self.calls: list[tuple[ValidateCommandRequest, object | None]] = []

    def run_validation(
        self,
        request: ValidateCommandRequest,
        *,
        event_sink: object | None = None,
    ) -> RunResult:
        self.calls.append((request, event_sink))
        return self.result


class _ProjectApplication:
    def __init__(self, result: ProjectValidationResult) -> None:
        self.result = result
        self.calls: list[ProjectCheckRequest] = []

    def check_project(
        self,
        request: ProjectCheckRequest,
        *args: object,
        **kwargs: object,
    ) -> ProjectValidationResult:
        del args, kwargs
        self.calls.append(request)
        return self.result


def _field_defaults(model: type[Any], values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in fields(model):
        if field.name in values:
            result[field.name] = values[field.name]
            continue
        if field.default is not MISSING or field.default_factory is not MISSING:
            continue
        raise AssertionError(f"No test default for required field {field.name!r}")
    return result


def _validate_request(**overrides: Any) -> ValidateCommandRequest:
    values: dict[str, Any] = {
        "mode": ValidationMode.DIAGNOSTIC,
        "target": None,
        "target_path": None,
        "checkpoint": None,
        "checkpoints": (),
        "checkpoint_ids": (),
        "scenarios": (),
        "scenario_ids": (),
        "selected_scenarios": (),
        "strict": False,
        "no_version_probe": False,
        "skip_version_probe": False,
        "no_compile": False,
        "compile_timeout_sec": 60,
        "compile_timeout": 60,
        "scenario_timeout_sec": 60,
        "scenario_timeout": 60,
        "pgf_timeout_sec": 120,
        "pgf_timeout": 120,
        "max_files": 0,
        "emit_cpu_stats": False,
        "cpu_stats": False,
        "keep_ok_details": False,
        "diff_previous": True,
        "compare_previous": True,
        "baseline": None,
        "baseline_path": None,
        "quiet": False,
        "verbose": False,
        "project_root": None,
        "gf_executable": None,
        "gf_exe": None,
        "rgl_root": None,
        "output_root": None,
        "out_root": None,
        "compatibility_warnings": (),
        "warnings": (),
        "legacy_project_overrides": {},
        "project_overrides": {},
    }
    values.update(overrides)
    return ValidateCommandRequest(**_field_defaults(ValidateCommandRequest, values))


def _project_request(**overrides: Any) -> ProjectCheckRequest:
    values: dict[str, Any] = {
        "project_root": None,
        "strict": False,
        "probe_gf": False,
        "gf_executable": None,
        "gf_exe": None,
        "rgl_root": None,
        "quiet": False,
        "verbose": False,
    }
    values.update(overrides)
    return ProjectCheckRequest(**_field_defaults(ProjectCheckRequest, values))


def _run_result_stub() -> RunResult:
    return object.__new__(RunResult)


def _project_diagnostic(tmp_path: Path) -> ProjectDiagnostic:
    return ProjectDiagnostic(
        code="GF-WB-TEST-001",
        severity=ProjectDiagnosticSeverity.ERROR,
        field="project.id",
        message="Project identity is invalid.",
        source_file=(tmp_path / "project.toml").resolve(),
        suggestion="Use a canonical project identifier.",
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ValidationMode.QUICK, ValidationMode.QUICK),
        ("quick", ValidationMode.QUICK),
        ("checkpoint", ValidationMode.CHECKPOINT),
        ("release", ValidationMode.RELEASE),
        ("diagnostic", ValidationMode.DIAGNOSTIC),
        ("file", ValidationMode.QUICK),
        ("all", ValidationMode.DIAGNOSTIC),
    ],
)
def test_normalize_validation_mode_supports_canonical_and_legacy_values(
    value: ValidationMode | str,
    expected: ValidationMode,
) -> None:
    assert normalize_validation_mode(value) is expected


def test_normalize_validation_mode_rejects_unknown_value() -> None:
    with pytest.raises(CliAuditCommandError):
        normalize_validation_mode("unsupported")


def test_validate_request_from_namespace_preserves_canonical_options(
    tmp_path: Path,
) -> None:
    namespace = parse_cli_namespace(
        [
            "validate",
            "--mode",
            "diagnostic",
            "--scenario",
            "parse-basic",
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
            "9",
            "--cpu-stats",
            "--keep-ok-details",
            "--no-compare-previous",
            "--project-root",
            str(tmp_path),
        ]
    )

    request = ValidateCommandRequest.from_namespace(namespace)

    assert request.mode is ValidationMode.DIAGNOSTIC
    assert request.strict is True
    assert request.no_compile is True
    assert request.max_files == 9
    assert request.keep_ok_details is True
    assert request.diff_previous is False
    assert request.project_root == tmp_path.resolve()
    assert tuple(str(item) for item in request.scenario_ids) == ("parse-basic",)


def test_validate_request_rejects_release_compile_bypass() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            mode=ValidationMode.RELEASE,
            no_compile=True,
        )
        validate_command_request(request)


def test_validate_request_rejects_quick_without_target() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(mode=ValidationMode.QUICK)
        validate_command_request(request)


def test_validate_request_rejects_checkpoint_without_selection() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(mode=ValidationMode.CHECKPOINT)
        validate_command_request(request)


def test_execute_validate_command_delegates_once() -> None:
    result = _run_result_stub()
    application = _AuditApplication(result)
    events: list[object] = []
    services = AuditCommandServices(
        application=application,
        event_sink=events.append,
    )
    namespace = parse_cli_namespace(
        ["validate", "--mode", "diagnostic"]
    )

    returned = execute_validate_command(namespace, services=services)

    assert returned is result
    assert len(application.calls) == 1
    request, event_sink = application.calls[0]
    assert request.mode is ValidationMode.DIAGNOSTIC
    assert callable(event_sink)


def test_audit_services_reject_invalid_dependencies() -> None:
    with pytest.raises(TypeError):
        AuditCommandServices(application=object())

    with pytest.raises(TypeError):
        AuditCommandServices(
            application=_AuditApplication(_run_result_stub()),
            event_sink=object(),
        )


def test_project_check_namespace_builds_typed_request(tmp_path: Path) -> None:
    project_root = tmp_path.resolve()
    gf_executable = (tmp_path / "gf.exe").resolve()
    rgl_root = (tmp_path / "rgl").resolve()
    namespace = parse_cli_namespace(
        [
            "project",
            "check",
            "--strict",
            "--probe-gf",
            "--project-root",
            str(project_root),
            "--gf-exe",
            str(gf_executable),
            "--rgl-root",
            str(rgl_root),
            "--verbose",
        ]
    )

    request = project_check_request_from_namespace(namespace)

    assert request.project_root == project_root
    assert request.gf_executable == gf_executable
    assert request.rgl_root == rgl_root
    assert request.strict is True
    assert request.probe_gf is True
    assert request.verbose is True
    assert request.quiet is False


def test_project_check_request_rejects_conflicting_verbosity() -> None:
    with pytest.raises(ValueError):
        _project_request(quiet=True, verbose=True)


def test_execute_project_check_returns_success_exit_code() -> None:
    request = _project_request()
    application = _ProjectApplication(ProjectValidationResult(()))
    stdout = StringIO()
    stderr = StringIO()

    code = execute_project_check(
        request,
        application=application,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == EXIT_OK
    assert application.calls == [request]
    assert stderr.getvalue() == ""


def test_execute_project_check_reports_contract_failure(tmp_path: Path) -> None:
    request = _project_request()
    result = ProjectValidationResult((_project_diagnostic(tmp_path),))
    application = _ProjectApplication(result)
    stdout = StringIO()
    stderr = StringIO()

    code = execute_project_check(
        request,
        application=application,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == EXIT_USAGE_OR_CONFIG
    assert application.calls == [request]
    assert "GF-WB-TEST-001" in stderr.getvalue()
    assert "Project identity is invalid." in stderr.getvalue()


def test_reset_plan_and_apply_commands_have_distinct_safety_classification() -> None:
    plan_command = PlanProjectResetCommand(object.__new__(ResetRequest))
    apply_command = ApplyProjectResetCommand(object.__new__(ResetPlan))

    assert maintenance_command_kind(plan_command) is MaintenanceCommandKind.PLAN_PROJECT_RESET
    assert maintenance_command_kind(apply_command) is MaintenanceCommandKind.APPLY_PROJECT_RESET
    assert maintenance_command_is_destructive(plan_command) is False
    assert maintenance_command_is_destructive(apply_command) is True
    assert maintenance_command_is_dry_run(plan_command) is True
    assert maintenance_command_is_dry_run(apply_command) is False


def test_maintenance_classification_rejects_unknown_command() -> None:
    with pytest.raises(TypeError):
        maintenance_command_kind(object())

    with pytest.raises(TypeError):
        maintenance_command_is_destructive(object())

    with pytest.raises(TypeError):
        maintenance_command_is_dry_run(object())


@pytest.mark.parametrize(
    "argv",
    [
        ["validate", "--mode", "diagnostic"],
        ["project", "check"],
        ["scenarios", "check"],
        ["gold", "update", "parse-basic", "--yes"],
        ["schemas", "check", "summary.json"],
        ["reports", "check", "run_20260725_120000"],
    ],
)
def test_main_resolves_handler_for_every_public_command(
    argv: list[str],
) -> None:
    request = parse_cli_request(argv)
    handler = cli_main._command_handler(request.command)

    assert callable(handler)


def test_dispatch_cli_request_uses_resolved_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = parse_cli_request(["project", "check"])
    calls: list[object] = []
    sentinel = object()

    def handler(value: object) -> object:
        calls.append(value)
        return sentinel

    monkeypatch.setattr(cli_main, "_command_handler", lambda command: handler)

    assert cli_main.dispatch_cli_request(request) is sentinel
    assert calls == [request]


def test_parser_rejects_command_contract_violations() -> None:
    invalid_argv = [
        ["gold", "update"],
        ["gold", "update", "parse-basic", "--all"],
        ["schemas", "check"],
        ["reports", "check"],
    ]

    for argv in invalid_argv:
        with pytest.raises(CliUsageError):
            parse_cli_request(argv)
