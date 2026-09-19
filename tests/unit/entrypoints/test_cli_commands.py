"""Unit tests for GF Wordbench CLI command adapters."""

from __future__ import annotations

from dataclasses import MISSING, fields
from io import StringIO
from pathlib import Path
from collections.abc import Callable
from typing import Any

import pytest

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
    EXIT_VALIDATION_FAILED,
)
from gf_wordbench.entrypoints.cli.language_commands import (
    LanguageCommandServices,
    LanguageProbeCommandRequest,
    execute_language_probe_command,
    language_probe_request_from_namespace,
)
import gf_wordbench.entrypoints.cli.main as cli_main
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
from gf_wordbench.kernel.events import EventSink, LifecycleEvent
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.languages.models import LanguageProbeResult
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
        cancellation_check: Callable[[], None] | None = None,
        event_sink: EventSink[LifecycleEvent] | None = None,
    ) -> RunResult:
        del cancellation_check
        self.calls.append((request, event_sink))
        return self.result


class _LanguageApplication:
    def __init__(self, result: LanguageProbeResult) -> None:
        self.result = result
        self.calls: list[LanguageProbeCommandRequest] = []

    def probe_language(
        self,
        request: LanguageProbeCommandRequest,
        *args: object,
        **kwargs: object,
    ) -> LanguageProbeResult:
        del args, kwargs
        self.calls.append(request)
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
        "language_path": Path("language"),
        "selected_language_path": Path("language"),
        "validation_profile": None,
        "profile_path": None,
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


def _language_probe_request(**overrides: Any) -> LanguageProbeCommandRequest:
    values: dict[str, Any] = {
        "language_path": Path("language"),
        "selected_path": Path("language"),
        "rgl_root": None,
        "validation_profile": None,
        "profile_path": None,
        "gf_executable": None,
        "gf_exe": None,
        "verify_with_gf": False,
        "quiet": False,
        "verbose": False,
    }
    values.update(overrides)
    return LanguageProbeCommandRequest(**_field_defaults(LanguageProbeCommandRequest, values))


def _project_request(**overrides: Any) -> ProjectCheckRequest:
    values: dict[str, Any] = {
        "language_path": Path("language"),
        "selected_language_path": Path("language"),
        "validation_profile": Path("project/project.toml"),
        "profile_path": Path("project/project.toml"),
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


def _language_probe_result_stub() -> LanguageProbeResult:
    return object.__new__(LanguageProbeResult)


def _profile_diagnostic(tmp_path: Path) -> ProjectDiagnostic:
    return ProjectDiagnostic(
        code="GF-WB-TEST-001",
        severity=ProjectDiagnosticSeverity.ERROR,
        field="profile.id",
        message="Validation profile identity is invalid.",
        source_file=(tmp_path / "project" / "project.toml").resolve(),
        suggestion="Use a profile compatible with the resolved language context.",
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


def test_validate_request_from_namespace_preserves_path_resolved_options(
    tmp_path: Path,
) -> None:
    language_path = (tmp_path / "gf-rgl" / "src" / "english").resolve()
    profile_path = (tmp_path / "profile" / "project.toml").resolve()
    gf_executable = (tmp_path / "gf.exe").resolve()
    rgl_root = (tmp_path / "gf-rgl").resolve()

    namespace = parse_cli_namespace(
        [
            "validate",
            "--language-path",
            str(language_path),
            "--validation-profile",
            str(profile_path),
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
            "--gf-exe",
            str(gf_executable),
            "--rgl-root",
            str(rgl_root),
        ]
    )

    request = ValidateCommandRequest.from_namespace(namespace)

    assert request.language_path == language_path
    assert request.validation_profile == profile_path
    assert request.mode is ValidationMode.DIAGNOSTIC
    assert request.strict is True
    assert request.no_compile is True
    assert request.max_files == 9
    assert request.keep_ok_details is True
    assert request.diff_previous is False
    assert request.gf_executable == gf_executable
    assert request.rgl_root == rgl_root
    assert tuple(str(item) for item in request.scenario_ids) == ("parse-basic",)


def test_validate_request_rejects_missing_language_path() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            language_path=None,
            selected_language_path=None,
        )
        validate_command_request(request)


def test_validate_request_rejects_release_compile_bypass() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            mode=ValidationMode.RELEASE,
            validation_profile=Path("project/project.toml"),
            no_compile=True,
        )
        validate_command_request(request)


def test_validate_request_rejects_release_without_validation_profile() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            mode=ValidationMode.RELEASE,
            validation_profile=None,
            profile_path=None,
        )
        validate_command_request(request)


def test_validate_request_rejects_quick_directory_without_target() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            language_path=Path("english"),
            mode=ValidationMode.QUICK,
            target=None,
            target_path=None,
        )
        validate_command_request(request)


def test_validate_request_accepts_quick_selected_gf_file_as_focused_target() -> None:
    request = _validate_request(
        language_path=Path("english/LangEng.gf"),
        selected_language_path=Path("english/LangEng.gf"),
        mode=ValidationMode.QUICK,
        target=None,
        target_path=None,
    )

    validate_command_request(request)


def test_validate_request_rejects_checkpoint_without_profile_selection() -> None:
    with pytest.raises(CliAuditCommandError):
        request = _validate_request(
            mode=ValidationMode.CHECKPOINT,
            validation_profile=None,
            checkpoint=None,
        )
        validate_command_request(request)


def test_execute_validate_command_delegates_once(tmp_path: Path) -> None:
    result = _run_result_stub()
    application = _AuditApplication(result)
    events: list[object] = []
    services = AuditCommandServices(
        application=application,
        event_sink=events.append,
    )
    language_path = (tmp_path / "gf-rgl" / "src" / "english").resolve()
    namespace = parse_cli_namespace(
        [
            "validate",
            "--language-path",
            str(language_path),
            "--mode",
            "diagnostic",
        ]
    )

    returned = execute_validate_command(namespace, services=services)

    assert returned is result
    assert len(application.calls) == 1
    request, event_sink = application.calls[0]
    assert request.language_path == language_path
    assert request.mode is ValidationMode.DIAGNOSTIC
    assert callable(event_sink)


def test_audit_services_reject_invalid_dependencies() -> None:
    with pytest.raises(TypeError):
        AuditCommandServices(application=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        AuditCommandServices(
            application=_AuditApplication(_run_result_stub()),
            event_sink=object(),  # type: ignore[arg-type]
        )


def test_language_probe_namespace_builds_typed_request(tmp_path: Path) -> None:
    language_path = (tmp_path / "gf-rgl" / "src" / "english" / "LangEng.gf").resolve()
    rgl_root = (tmp_path / "gf-rgl").resolve()
    gf_executable = (tmp_path / "gf.exe").resolve()

    namespace = parse_cli_namespace(
        [
            "language",
            "probe",
            str(language_path),
            "--rgl-root",
            str(rgl_root),
            "--gf-exe",
            str(gf_executable),
            "--verify-with-gf",
            "--verbose",
        ]
    )

    request = language_probe_request_from_namespace(namespace)

    assert request.language_path == language_path
    assert request.rgl_root == rgl_root
    assert request.gf_executable == gf_executable
    assert request.verify_with_gf is True
    assert request.verbose is True
    assert request.quiet is False


def test_language_probe_request_rejects_conflicting_verbosity() -> None:
    with pytest.raises(ValueError):
        _language_probe_request(quiet=True, verbose=True)


def test_execute_language_probe_delegates_once(tmp_path: Path) -> None:
    result = _language_probe_result_stub()
    application = _LanguageApplication(result)
    services = LanguageCommandServices(application=application)
    language_path = (tmp_path / "gf-rgl" / "src" / "english").resolve()
    namespace = parse_cli_namespace(["language", "probe", str(language_path)])

    returned = execute_language_probe_command(namespace, services=services)

    assert returned is result
    assert len(application.calls) == 1
    assert application.calls[0].language_path == language_path


def test_language_services_reject_invalid_dependencies() -> None:
    with pytest.raises(TypeError):
        LanguageCommandServices(application=object())  # type: ignore[arg-type]


def test_project_check_namespace_builds_explicit_profile_request(
    tmp_path: Path,
) -> None:
    language_path = (tmp_path / "gf-rgl" / "src" / "english").resolve()
    validation_profile = (tmp_path / "profile" / "project.toml").resolve()
    gf_executable = (tmp_path / "gf.exe").resolve()
    rgl_root = (tmp_path / "gf-rgl").resolve()
    namespace = parse_cli_namespace(
        [
            "project",
            "check",
            "--language-path",
            str(language_path),
            "--validation-profile",
            str(validation_profile),
            "--strict",
            "--probe-gf",
            "--gf-exe",
            str(gf_executable),
            "--rgl-root",
            str(rgl_root),
            "--verbose",
        ]
    )

    request = project_check_request_from_namespace(namespace)

    assert request.language_path == language_path
    assert request.validation_profile == validation_profile
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


def test_execute_project_check_reports_profile_contract_failure(
    tmp_path: Path,
) -> None:
    request = _project_request()
    result = ProjectValidationResult((_profile_diagnostic(tmp_path),))
    application = _ProjectApplication(result)
    stdout = StringIO()
    stderr = StringIO()

    code = execute_project_check(
        request,
        application=application,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == EXIT_VALIDATION_FAILED
    assert application.calls == [request]
    assert "GF-WB-TEST-001" in stderr.getvalue()
    assert "Validation profile identity is invalid." in stderr.getvalue()


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
        maintenance_command_kind(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        maintenance_command_is_destructive(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        maintenance_command_is_dry_run(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "argv",
    [
        ["language", "probe", "src/english"],
        ["validate", "--language-path", "src/english", "--mode", "diagnostic"],
        [
            "project",
            "check",
            "--language-path",
            "src/english",
            "--validation-profile",
            "project/project.toml",
        ],
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


def test_dispatch_cli_request_uses_resolved_language_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = parse_cli_request(["language", "probe", "src/english"])
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
        ["language", "probe"],
        ["project", "check", "--language-path", "src/english"],
        ["gold", "update"],
        ["gold", "update", "parse-basic", "--all"],
        ["schemas", "check"],
        ["reports", "check"],
    ]

    for argv in invalid_argv:
        with pytest.raises(CliUsageError):
            parse_cli_request(argv)
