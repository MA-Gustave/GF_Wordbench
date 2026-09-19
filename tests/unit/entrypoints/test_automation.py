from __future__ import annotations

from dataclasses import replace
import inspect
import io
import json
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.entrypoints import automation
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode

_RUN_ID = "20260725_123456"
_PROJECT_ID = "demo-project"


def _construct(
    factory: Any,
    candidates: dict[str, object],
) -> Any:
    parameters = inspect.signature(factory).parameters
    arguments: dict[str, object] = {}
    missing: list[str] = []

    for name, parameter in parameters.items():
        if parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            continue
        if name in candidates:
            arguments[name] = candidates[name]
            continue
        if parameter.default is not inspect.Parameter.empty:
            continue
        missing.append(name)

    if missing:
        raise AssertionError(
            f"Missing fixture values for {factory.__name__}: " + ", ".join(missing)
        )
    return factory(**arguments)


def _issue(
    *,
    severity: object | None = None,
    code: str = "AUTOMATION_TEST",
    message: str = "Automation verification failed.",
    path: Path | None = None,
) -> automation.AutomationIssue:
    return cast(
        automation.AutomationIssue,
        _construct(
            automation.AutomationIssue,
            {
                "severity": (
                    severity
                    if severity is not None
                    else automation.AutomationIssueSeverity.ERROR
                ),
                "code": code,
                "message": message,
                "path": path,
            },
        ),
    )

def _summary_document(
    run_dir: Path,
    *,
    project_id: str = _PROJECT_ID,
    mode: ValidationMode = ValidationMode.DIAGNOSTIC,
    overall_status: OverallStatus = OverallStatus.OK,
    manifest: str | None = None,
) -> dict[str, object]:
    root = run_dir.resolve()
    output_root = root.parent
    timestamp = "2026-07-25T12:34:56Z"

    counts = {
        "files_seen": 0,
        "files_included": 0,
        "files_excluded": 0,
        "files_ok": 0,
        "files_fail": 0,
        "files_error": 0,
        "files_skipped": 0,
        "direct_fail": 0,
        "downstream_fail": 0,
        "ambiguous_fail": 0,
        "excluded_noise": 0,
        "scenarios_seen": 0,
        "scenarios_ok": 0,
        "scenarios_fail": 0,
        "scenarios_error": 0,
        "scenarios_skipped": 0,
        "required_scenario_fail": 0,
        "overall_status": overall_status.value,
    }

    artifacts = {
        "summary_json": "summary.json",
        "summary_markdown": None,
        "ai_ready": None,
        "top_errors": None,
        "manifest": manifest,
        "master_log": None,
        "all_scan_logs": None,
        "all_logs": None,
        "details_dir": "details",
        "raw_dir": "raw",
        "compile_logs_dir": "raw/compile",
        "scan_logs_dir": "raw/scan",
        "scenario_logs_dir": "raw/scenarios",
        "artifacts_dir": "artifacts",
        "gfo_dir": "artifacts/gfo",
        "out_dir": "artifacts/out",
        "pgf_dir": "artifacts/pgf",
    }

    return {
        "schema_id": "gf-wordbench.run-summary",
        "schema_version": "1.0",
        "producer": {
            "name": "gf-wordbench",
            "version": "1.0.0",
        },
        "metadata": {
            "run_id": _RUN_ID,
            "run_dir": root.as_posix(),
            "started_at": timestamp,
            "finished_at": timestamp,
            "duration_ms": 0,
            "gf_version": "3.12",
            "mode": mode.value,
            "target_file": None,
            "project_id": project_id,
            "project_name": "Demo Project",
            "project_root": (root / "project").as_posix(),
            "rgl_root": (root / "rgl").as_posix(),
            "gf_executable": (root / "bin" / "gf").as_posix(),
            "output_root": output_root.as_posix(),
            "source_directory": "src",
            "source_glob": "*.gf",
            "gf_path": [
                (root / "project" / "src").as_posix(),
                (root / "rgl").as_posix(),
            ],
            "timeout_sec": 30,
            "max_files": 100,
            "skip_version_probe": False,
            "no_compile": False,
            "emit_cpu_stats": False,
            "keep_ok_details": False,
            "diff_previous": False,
        },
        "totals": counts,
        "artifacts": artifacts,
        "file_results": [],
        "scenario_results": [],
        "diff_entries": [],
        "top_errors": [],
    }


def _write_summary(
    run_dir: Path,
    document: dict[str, object],
) -> Path:
    destination = run_dir / "summary.json"
    destination.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def _verification_request(
    run_dir: Path,
    *,
    summary_path: Path | None = None,
    manifest_path: Path | None = None,
    expected_project_id: str | None = _PROJECT_ID,
    expected_mode: ValidationMode | None = ValidationMode.DIAGNOSTIC,
    require_manifest: bool = False,
) -> automation.AutomationVerificationRequest:
    root = run_dir.resolve()
    return cast(
        automation.AutomationVerificationRequest,
        _construct(
            automation.AutomationVerificationRequest,
            {
                "run_dir": root,
                "summary_path": summary_path or root / "summary.json",
                "manifest_path": manifest_path,
                "expected_project_id": expected_project_id,
                "expected_mode": expected_mode,
                "require_manifest": require_manifest,
                "strict_manifest": True,
                "strict": True,
                "allow_legacy_summary": False,
                "allow_legacy": False,
            },
        ),
    )

def _verification_result(
    run_dir: Path,
    *,
    status: OverallStatus = OverallStatus.ERROR,
    issues: tuple[automation.AutomationIssue, ...] = (),
) -> automation.AutomationVerificationResult:
    root = run_dir.resolve()
    return cast(
        automation.AutomationVerificationResult,
        _construct(
            automation.AutomationVerificationResult,
            {
                "run_dir": root,
                "summary_path": root / "summary.json",
                "manifest_path": None,
                "run_id": _RUN_ID,
                "project_id": _PROJECT_ID,
                "mode": ValidationMode.DIAGNOSTIC,
                "overall_status": status,
                "manifest_verified": None,
                "summary_valid": not issues,
                "summary_document": {},
                "summary": {},
                "issues": issues,
            },
        ),
    )

def _execution_result(
    verification: automation.AutomationVerificationResult,
) -> automation.AutomationExecutionResult:
    return cast(
        automation.AutomationExecutionResult,
        _construct(
            automation.AutomationExecutionResult,
            {
                "run_result": None,
                "verification": verification,
                "verification_result": verification,
                "error": None,
                "failure": None,
                "issue": None,
            },
        ),
    )

def test_issue_severity_values_are_stable() -> None:
    assert {severity.value for severity in automation.AutomationIssueSeverity} == {
        "warning",
        "error",
    }


def test_issue_normalizes_path_and_rejects_empty_contract_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "summary.json"
    issue = _issue(path=path)

    assert issue.severity is automation.AutomationIssueSeverity.ERROR
    assert issue.code == "AUTOMATION_TEST"
    assert issue.message == "Automation verification failed."
    assert issue.path == path.resolve()

    with pytest.raises((TypeError, ValueError)):
        replace(issue, code="")
    with pytest.raises((TypeError, ValueError)):
        replace(issue, message=" ")
    with pytest.raises((TypeError, ValueError)):
        replace(issue, severity="fatal")


def test_verification_request_normalizes_paths_and_mode(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    summary_path = run_dir / "summary.json"

    request = _verification_request(
        run_dir,
        summary_path=summary_path,
        expected_mode=ValidationMode.RELEASE,
        require_manifest=True,
    )

    assert request.run_dir == run_dir.resolve()
    assert request.summary_path == summary_path.resolve()
    assert request.expected_project_id == _PROJECT_ID
    assert request.expected_mode is ValidationMode.RELEASE
    assert request.require_manifest is True


def test_verification_request_rejects_paths_outside_run_directory(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    outside = tmp_path / "outside.json"

    with pytest.raises((TypeError, ValueError)):
        _verification_request(
            run_dir,
            summary_path=outside,
        )

    with pytest.raises((TypeError, ValueError)):
        _verification_request(
            run_dir,
            manifest_path=outside,
            require_manifest=True,
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (OverallStatus.OK, 0),
        (OverallStatus.FAIL, 1),
        (OverallStatus.ERROR, 3),
    ],
)
def test_exit_code_mapping_uses_overall_status(
    status: OverallStatus,
    expected: int,
) -> None:
    assert automation.exit_code_for_overall_status(status) == expected


def test_valid_summary_is_verified_without_parsing_human_reports(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    document = _summary_document(run_dir)
    summary_path = _write_summary(run_dir, document)
    (run_dir / "summary.md").write_text(
        "This text deliberately claims failure.",
        encoding="utf-8",
    )

    result = automation.verify_completed_run(
        _verification_request(
            run_dir,
            summary_path=summary_path,
        )
    )

    assert result.succeeded is True
    assert result.has_errors is False
    assert result.run_id == _RUN_ID
    assert result.project_id == _PROJECT_ID
    assert result.mode is ValidationMode.DIAGNOSTIC
    assert result.overall_status is OverallStatus.OK
    assert result.summary_path == summary_path.resolve()
    assert result.issues == ()


def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    summary_path = run_dir / "summary.json"
    summary_path.write_text(
        '{"schema_id":"gf-wordbench.run-summary","schema_id":"duplicate","value":NaN}\n',
        encoding="utf-8",
    )

    result = automation.verify_completed_run(
        _verification_request(
            run_dir,
            summary_path=summary_path,
            expected_project_id=None,
            expected_mode=None,
        )
    )

    assert result.succeeded is False
    assert result.has_errors is True
    assert result.overall_status is OverallStatus.ERROR
    assert any(
        issue.severity is automation.AutomationIssueSeverity.ERROR for issue in result.issues
    )
    assert any(
        "json" in issue.message.casefold() or "duplicate" in issue.message.casefold()
        for issue in result.issues
    )


@pytest.mark.parametrize(
    ("expected_project_id", "expected_mode", "needle"),
    [
        ("other-project", ValidationMode.DIAGNOSTIC, "project"),
        (_PROJECT_ID, ValidationMode.RELEASE, "mode"),
    ],
)
def test_expected_identity_mismatch_is_an_error(
    tmp_path: Path,
    expected_project_id: str,
    expected_mode: ValidationMode,
    needle: str,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    summary_path = _write_summary(
        run_dir,
        _summary_document(run_dir),
    )

    result = automation.verify_completed_run(
        _verification_request(
            run_dir,
            summary_path=summary_path,
            expected_project_id=expected_project_id,
            expected_mode=expected_mode,
        )
    )

    assert result.succeeded is False
    assert result.has_errors is True
    assert any(needle in (issue.code + " " + issue.message).casefold() for issue in result.issues)


def test_required_manifest_cannot_be_silently_omitted(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run_20260725_123456"
    run_dir.mkdir()
    summary_path = _write_summary(
        run_dir,
        _summary_document(
            run_dir,
            manifest="manifest.json",
        ),
    )

    result = automation.verify_completed_run(
        _verification_request(
            run_dir,
            summary_path=summary_path,
            manifest_path=run_dir / "manifest.json",
            require_manifest=True,
        )
    )

    assert result.succeeded is False
    assert result.has_errors is True
    assert result.manifest_verified is False
    assert any(
        "manifest" in (issue.code + " " + issue.message).casefold() for issue in result.issues
    )


def test_result_document_and_json_are_deterministic(
    tmp_path: Path,
) -> None:
    verification = _verification_result(
        tmp_path,
        issues=(
            _issue(
                code="AUTOMATION_TEST_ERROR",
                message="Synthetic verification failure.",
                path=tmp_path / "summary.json",
            ),
        ),
    )
    result = _execution_result(verification)

    document = automation.automation_result_document(result)
    encoded = automation.dumps_automation_result(result)

    assert json.loads(encoded) == document
    assert encoded.endswith("\n")
    assert "\r" not in encoded
    assert "Synthetic verification failure." in encoded
    assert document["exit_code"] == result.exit_code
    assert document["succeeded"] is False


def test_write_automation_result_emits_exact_canonical_document(
    tmp_path: Path,
) -> None:
    verification = _verification_result(
        tmp_path,
        issues=(
            _issue(
                code="AUTOMATION_TEST_ERROR",
                message="Synthetic verification failure.",
            ),
        ),
    )
    result = _execution_result(verification)
    stream = io.StringIO()

    automation.write_automation_result(result, stream)

    assert stream.getvalue() == automation.dumps_automation_result(result)


def test_automation_application_protocol_accepts_callable_adapter() -> None:
    class Application:
        def __call__(self, configuration: object) -> object:
            return configuration

    assert isinstance(
        Application(),
        automation.AutomationRunApplication,
    )
