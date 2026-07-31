"""Supported non-interactive adapter for GF Wordbench automation."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Protocol, TextIO, runtime_checkable

from gf_wordbench.kernel.errors import (
    CancellationRequested,
    ConfigurationError,
    ContractViolationError,
    GFWordbenchError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.entrypoints.cli.exit_codes import (
    EXIT_CANCELLED,
    EXIT_OK,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_FAILED,
    exit_code_for_overall_status,
    is_canonical_exit_code,
)
from gf_wordbench.kernel.serialization import dumps_canonical_json
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode, ValidationStatus
from gf_wordbench.reporting.schemas.summary_v1 import (
    SUMMARY_JSON_FILENAME,
    SummaryV1Issue,
    validate_summary_v1,
)
from gf_wordbench.runs.public import RunConfig, RunPaths, RunResult

AUTOMATION_RESULT_SCHEMA_ID: Final[str] = "gf-wordbench.automation-result"
AUTOMATION_RESULT_SCHEMA_VERSION: Final[str] = "1.0"

_MANIFEST_FILENAME: Final[str] = "manifest.json"
_MAX_MESSAGE_LENGTH: Final[int] = 2_000
_MAX_ISSUES: Final[int] = 256


@unique
class AutomationIssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True, order=True)
class AutomationIssue:
    code: str
    message: str
    path: Path | str | None = None
    severity: AutomationIssueSeverity = AutomationIssueSeverity.ERROR

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "code",
            _require_text(self.code, field="code", max_length=128),
        )
        object.__setattr__(
            self,
            "message",
            _require_text(
                self.message,
                field="message",
                max_length=_MAX_MESSAGE_LENGTH,
            ),
        )
        if self.path is not None:
            object.__setattr__(
                self,
                "path",
                _normalize_issue_path(self.path),
            )
        if not isinstance(self.severity, AutomationIssueSeverity):
            raise TypeError("severity must be AutomationIssueSeverity")


@dataclass(frozen=True, slots=True)
class AutomationVerificationRequest:
    summary_path: Path
    run_dir: Path | None = None
    expected_mode: ValidationMode | str | None = None
    expected_project_id: str | None = None
    expected_run_id: str | None = None
    manifest_path: Path | None = None
    verify_manifest_integrity: bool = False
    require_manifest: bool = False
    require_success: bool = False

    def __post_init__(self) -> None:
        summary_path = _coerce_path(
            self.summary_path,
            field="summary_path",
        )
        if summary_path.name != SUMMARY_JSON_FILENAME:
            raise ValueError(
                f"summary_path must end with {SUMMARY_JSON_FILENAME!r}"
            )

        run_dir = _coerce_path(
            self.run_dir if self.run_dir is not None else summary_path.parent,
            field="run_dir",
        )
        _require_contained_path(
            summary_path,
            run_dir,
            field="summary_path",
        )

        object.__setattr__(self, "summary_path", summary_path)
        object.__setattr__(self, "run_dir", run_dir)

        if self.expected_mode is not None:
            object.__setattr__(
                self,
                "expected_mode",
                _coerce_mode(self.expected_mode),
            )

        for field_name in ("expected_project_id", "expected_run_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_text(
                        value,
                        field=field_name,
                        max_length=256,
                    ),
                )

        manifest_path = self.manifest_path
        if manifest_path is not None:
            manifest_path = _coerce_path(
                manifest_path,
                field="manifest_path",
            )
            if manifest_path.name != _MANIFEST_FILENAME:
                raise ValueError(
                    f"manifest_path must end with {_MANIFEST_FILENAME!r}"
                )
            _require_contained_path(
                manifest_path,
                run_dir,
                field="manifest_path",
            )
            object.__setattr__(self, "manifest_path", manifest_path)

        for field_name in (
            "verify_manifest_integrity",
            "require_manifest",
            "require_success",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be bool")

        if self.require_manifest and not self.verify_manifest_integrity:
            object.__setattr__(self, "verify_manifest_integrity", True)

@dataclass(frozen=True, slots=True)
class AutomationVerificationResult:
    summary_path: Path
    manifest_path: Path | None
    run_id: str | None
    project_id: str | None
    mode: ValidationMode | None
    overall_status: OverallStatus | None
    summary_valid: bool
    manifest_verified: bool | None
    issues: tuple[AutomationIssue, ...]
    exit_code: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "summary_path",
            _coerce_path(self.summary_path, field="summary_path"),
        )
        if self.manifest_path is not None:
            object.__setattr__(
                self,
                "manifest_path",
                _coerce_path(self.manifest_path, field="manifest_path"),
            )

        for field_name in ("run_id", "project_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_text(
                        value,
                        field=field_name,
                        max_length=256,
                    ),
                )

        if self.mode is not None and not isinstance(
            self.mode,
            ValidationMode,
        ):
            raise TypeError("mode must be ValidationMode or None")
        if self.overall_status is not None and not isinstance(
            self.overall_status,
            OverallStatus,
        ):
            raise TypeError("overall_status must be OverallStatus or None")
        if type(self.summary_valid) is not bool:
            raise TypeError("summary_valid must be bool")
        if (
            self.manifest_verified is not None
            and type(self.manifest_verified) is not bool
        ):
            raise TypeError("manifest_verified must be bool or None")

        prepared = tuple(self.issues)
        if any(not isinstance(item, AutomationIssue) for item in prepared):
            raise TypeError("issues must contain AutomationIssue values")
        object.__setattr__(self, "issues", prepared)

        exit_code = self.exit_code
        if exit_code is None:
            has_errors = any(
                issue.severity is AutomationIssueSeverity.ERROR
                for issue in prepared
            )
            if (
                has_errors
                or not self.summary_valid
                or self.overall_status is None
                or self.overall_status is OverallStatus.ERROR
            ):
                exit_code = EXIT_RUNTIME_ERROR
            else:
                exit_code = exit_code_for_overall_status(
                    self.overall_status
                )
            object.__setattr__(self, "exit_code", exit_code)
        elif not is_canonical_exit_code(exit_code):
            raise ValueError("exit_code is not canonical")

        if exit_code == EXIT_OK:
            if self.overall_status is not OverallStatus.OK:
                raise ValueError("exit 0 requires overall_status=OK")
            if not self.summary_valid:
                raise ValueError("exit 0 requires a valid summary")
            if any(
                issue.severity is AutomationIssueSeverity.ERROR
                for issue in prepared
            ):
                raise ValueError("exit 0 cannot contain error issues")

    @property
    def succeeded(self) -> bool:
        return self.exit_code == EXIT_OK

    @property
    def has_errors(self) -> bool:
        return any(
            issue.severity is AutomationIssueSeverity.ERROR
            for issue in self.issues
        )


@dataclass(frozen=True, slots=True)
class AutomationExecutionResult:
    verification: AutomationVerificationResult
    run_result: RunResult | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.verification,
            AutomationVerificationResult,
        ):
            raise TypeError(
                "verification must be AutomationVerificationResult"
            )
        if self.run_result is not None and not isinstance(
            self.run_result,
            RunResult,
        ):
            raise TypeError("run_result must be RunResult or None")

    @property
    def exit_code(self) -> int:
        return self.verification.exit_code

    @property
    def succeeded(self) -> bool:
        return self.verification.succeeded

    @property
    def has_errors(self) -> bool:
        return self.verification.has_errors


@runtime_checkable
class AutomationRunApplication(Protocol):
    def __call__(
        self,
        run_config: RunConfig,
        run_paths: RunPaths,
        *,
        cancellation_check: Callable[[], None] | None = None,
        event_sink: Callable[[object], None] | None = None,
    ) -> RunResult:
        ...


@dataclass(frozen=True, slots=True)
class _ManifestPolicy:
    mode: str
    expected_run_id: str | None
    verify_summary: bool = True
    require_pgf: bool = False
    reject_unlisted_files: bool = False
    allow_symlinks: bool = False
    required_paths: tuple[str, ...] = ()
    owned_directories: tuple[str, ...] = ()
    allowed_roles: tuple[str, ...] = ()
    allowed_creators: tuple[str, ...] = ()


def execute_automation(
    run_config: RunConfig,
    run_paths: RunPaths,
    application: AutomationRunApplication,
    *,
    cancellation_check: Callable[[], None] | None = None,
    event_sink: Callable[[object], None] | None = None,
    verify_manifest_integrity: bool | None = None,
) -> AutomationExecutionResult:
    if not isinstance(run_config, RunConfig):
        raise TypeError("run_config must be RunConfig")
    if not isinstance(run_paths, RunPaths):
        raise TypeError("run_paths must be RunPaths")
    if not callable(application):
        raise TypeError("application must be callable")
    if cancellation_check is not None and not callable(cancellation_check):
        raise TypeError("cancellation_check must be callable or None")
    if event_sink is not None and not callable(event_sink):
        raise TypeError("event_sink must be callable or None")

    if verify_manifest_integrity is None:
        verify_manifest_integrity = (
            run_config.mode is ValidationMode.RELEASE
        )
    if type(verify_manifest_integrity) is not bool:
        raise TypeError("verify_manifest_integrity must be bool or None")

    try:
        run_result = application(
            run_config,
            run_paths,
            cancellation_check=cancellation_check,
            event_sink=event_sink,
        )
        if not isinstance(run_result, RunResult):
            raise TypeError(
                "automation application must return RunResult"
            )
        run_result.validate()
    except (
        ConfigurationError,
        SchemaValidationError,
        UnsupportedVersionError,
    ) as exc:
        return AutomationExecutionResult(
            verification=_failure_result(
                run_paths.summary_json,
                run_paths.manifest_json,
                EXIT_USAGE_ERROR,
                "AUTOMATION_CONFIGURATION_INVALID",
                exc,
            )
        )
    except CancellationRequested as exc:
        return AutomationExecutionResult(
            verification=_failure_result(
                run_paths.summary_json,
                run_paths.manifest_json,
                EXIT_CANCELLED,
                "AUTOMATION_CANCELLED",
                exc,
            )
        )
    except (
        ContractViolationError,
        GFWordbenchError,
        OSError,
    ) as exc:
        return AutomationExecutionResult(
            verification=_failure_result(
                run_paths.summary_json,
                run_paths.manifest_json,
                EXIT_RUNTIME_ERROR,
                "AUTOMATION_EXECUTION_ERROR",
                exc,
            )
        )
    except Exception as exc:
        return AutomationExecutionResult(
            verification=_failure_result(
                run_paths.summary_json,
                run_paths.manifest_json,
                EXIT_RUNTIME_ERROR,
                "AUTOMATION_UNEXPECTED_ERROR",
                exc,
            )
        )

    project_id = _project_id(run_config)
    request = AutomationVerificationRequest(
        summary_path=run_paths.summary_json,
        run_dir=run_paths.run_dir,
        expected_mode=run_config.mode,
        expected_project_id=project_id,
        expected_run_id=run_paths.run_id,
        manifest_path=run_paths.manifest_json,
        verify_manifest_integrity=verify_manifest_integrity,
        require_manifest=(
            run_config.mode is ValidationMode.RELEASE
            or verify_manifest_integrity
        ),
        require_success=False,
    )
    verification = verify_completed_run(request)

    run_status_exit = exit_code_for_overall_status(
        run_result.overall_status
    )
    issues = list(verification.issues)

    if verification.overall_status is not run_result.overall_status:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_RESULT_STATUS_MISMATCH",
                path="$.totals.overall_status",
                message=(
                    "persisted summary status does not match RunResult"
                ),
            ),
        )

    if verification.exit_code == EXIT_CANCELLED:
        final_exit = EXIT_CANCELLED
    elif verification.exit_code in {
        EXIT_USAGE_ERROR,
        EXIT_RUNTIME_ERROR,
    } or any(
        issue.severity is AutomationIssueSeverity.ERROR
        for issue in issues
    ):
        final_exit = EXIT_RUNTIME_ERROR
    else:
        final_exit = run_status_exit

    verification = AutomationVerificationResult(
        summary_path=verification.summary_path,
        manifest_path=verification.manifest_path,
        run_id=verification.run_id,
        project_id=verification.project_id,
        mode=verification.mode,
        overall_status=verification.overall_status,
        exit_code=final_exit,
        summary_valid=verification.summary_valid,
        manifest_verified=verification.manifest_verified,
        issues=tuple(issues),
    )
    return AutomationExecutionResult(
        verification=verification,
        run_result=run_result,
    )


def verify_completed_run(
    request: AutomationVerificationRequest,
) -> AutomationVerificationResult:
    if not isinstance(request, AutomationVerificationRequest):
        raise TypeError(
            "request must be AutomationVerificationRequest"
        )

    issues: list[AutomationIssue] = []
    summary_document = _read_summary(request.summary_path, issues)
    summary_valid = False
    run_id: str | None = None
    project_id: str | None = None
    mode: ValidationMode | None = None
    overall_status: OverallStatus | None = None
    manifest_path = request.manifest_path
    manifest_verified = False

    if summary_document is not None:
        summary_issues = validate_summary_v1(
            summary_document,
            strict=True,
            check_ordering=True,
        )
        for issue in summary_issues:
            _append_issue(
                issues,
                _summary_issue(issue),
            )

        summary_valid = not summary_issues
        metadata = summary_document.get("metadata")
        totals = summary_document.get("totals")
        artifacts = summary_document.get("artifacts")

        if isinstance(metadata, Mapping):
            run_id = _optional_text(metadata.get("run_id"))
            project_id = _optional_text(metadata.get("project_id"))
            mode = _optional_mode(metadata.get("mode"), issues)

        if isinstance(totals, Mapping):
            overall_status = _optional_overall_status(
                totals.get("overall_status"),
                issues,
            )

        if isinstance(artifacts, Mapping):
            declared_summary = artifacts.get("summary_json")
            if declared_summary != SUMMARY_JSON_FILENAME:
                _append_issue(
                    issues,
                    AutomationIssue(
                        code="AUTOMATION_SUMMARY_PATH_INVALID",
                        path="$.artifacts.summary_json",
                        message=(
                            "summary must declare canonical summary.json"
                        ),
                    ),
                )

            declared_manifest = artifacts.get("manifest")
            if manifest_path is None and isinstance(
                declared_manifest,
                str,
            ):
                manifest_path = _resolve_run_relative_file(
                    request.run_dir,
                    declared_manifest,
                    issues,
                    code="AUTOMATION_MANIFEST_PATH_INVALID",
                )

        _validate_expected_identity(
            request,
            run_id=run_id,
            project_id=project_id,
            mode=mode,
            issues=issues,
        )

        if request.require_success and (
            overall_status is not OverallStatus.OK
        ):
            _append_issue(
                issues,
                AutomationIssue(
                    code="AUTOMATION_REQUIRED_SUCCESS_MISSING",
                    path="$.totals.overall_status",
                    message=(
                        "automation requires overall_status=OK"
                    ),
                ),
            )

    if request.require_manifest and manifest_path is None:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_MISSING",
                path="$.artifacts.manifest",
                message="manifest verification is required",
            ),
        )

    if request.verify_manifest_integrity and manifest_path is not None:
        manifest_verified = _verify_manifest(
            request,
            manifest_path,
            run_id,
            mode,
            issues,
        )

    error_present = any(
        issue.severity is AutomationIssueSeverity.ERROR
        for issue in issues
    )

    if error_present or not summary_valid:
        if overall_status is None:
            overall_status = OverallStatus.ERROR
        exit_code = EXIT_RUNTIME_ERROR
    elif overall_status is None:
        overall_status = OverallStatus.ERROR
        exit_code = EXIT_RUNTIME_ERROR
    else:
        exit_code = exit_code_for_overall_status(overall_status)

    return AutomationVerificationResult(
        summary_path=request.summary_path,
        manifest_path=manifest_path,
        run_id=run_id,
        project_id=project_id,
        mode=mode,
        overall_status=overall_status,
        exit_code=exit_code,
        summary_valid=summary_valid,
        manifest_verified=manifest_verified,
        issues=tuple(issues),
    )


def automation_result_document(
    result: AutomationExecutionResult | AutomationVerificationResult,
) -> dict[str, object]:
    verification = _coerce_verification_result(result)

    return {
        "schema_id": AUTOMATION_RESULT_SCHEMA_ID,
        "schema_version": AUTOMATION_RESULT_SCHEMA_VERSION,
        "exit_code": verification.exit_code,
        "succeeded": verification.succeeded,
        "summary_valid": verification.summary_valid,
        "manifest_verified": verification.manifest_verified,
        "run_id": verification.run_id,
        "project_id": verification.project_id,
        "mode": (
            verification.mode.value
            if verification.mode is not None
            else None
        ),
        "overall_status": (
            verification.overall_status.value
            if verification.overall_status is not None
            else None
        ),
        "paths": {
            "summary": verification.summary_path.as_posix(),
            "manifest": (
                verification.manifest_path.as_posix()
                if verification.manifest_path is not None
                else None
            ),
        },
        "issues": [
            {
                "severity": issue.severity.value,
                "code": issue.code,
                "path": _render_issue_path(issue.path),
                "message": issue.message,
            }
            for issue in verification.issues
        ],
    }


def dumps_automation_result(
    result: AutomationExecutionResult | AutomationVerificationResult,
) -> str:
    return dumps_canonical_json(
        automation_result_document(result)
    )


def write_automation_result(
    result: AutomationExecutionResult | AutomationVerificationResult,
    stream: TextIO,
) -> None:
    if not callable(getattr(stream, "write", None)):
        raise TypeError("stream must provide write()")
    stream.write(dumps_automation_result(result))


def _coerce_verification_result(
    result: AutomationExecutionResult | AutomationVerificationResult,
) -> AutomationVerificationResult:
    if isinstance(result, AutomationExecutionResult):
        return result.verification
    if isinstance(result, AutomationVerificationResult):
        return result
    raise TypeError(
        "result must be AutomationExecutionResult or "
        "AutomationVerificationResult"
    )

def _read_summary(
    summary_path: Path,
    issues: list[AutomationIssue],
) -> dict[str, object] | None:
    try:
        raw = summary_path.read_bytes()
    except OSError as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_SUMMARY_MISSING",
                path=str(summary_path),
                message=_exception_message(exc),
            ),
        )
        return None

    if raw.startswith(b"\xef\xbb\xbf"):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_SUMMARY_ENCODING_INVALID",
                path=str(summary_path),
                message="UTF-8 BOM is prohibited",
            ),
        )
        return None

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_SUMMARY_ENCODING_INVALID",
                path=str(summary_path),
                message=_exception_message(exc),
            ),
        )
        return None

    try:
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_SUMMARY_JSON_INVALID",
                path=str(summary_path),
                message=_exception_message(exc),
            ),
        )
        return None

    if not isinstance(document, dict):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_SUMMARY_ROOT_INVALID",
                path="$",
                message="summary root must be a JSON object",
            ),
        )
        return None
    return document


def _verify_manifest(
    request: AutomationVerificationRequest,
    manifest_path: Path,
    run_id: str | None,
    mode: ValidationMode | None,
    issues: list[AutomationIssue],
) -> bool:
    run_root = request.run_dir
    try:
        resolved_manifest = manifest_path.resolve(strict=False)
        resolved_root = run_root.resolve(strict=False)
        resolved_manifest.relative_to(resolved_root)
    except (OSError, ValueError):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_PATH_INVALID",
                path=manifest_path,
                message="manifest must remain inside the run directory",
            ),
        )
        return False

    try:
        from gf_wordbench.reporting.manifest.verifier import verify_manifest
    except Exception as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_VERIFIER_UNAVAILABLE",
                path=manifest_path,
                message=_exception_message(exc),
            ),
        )
        return False

    policy_mode = (
        "release"
        if mode is ValidationMode.RELEASE
        else "strict"
    )
    policy = _ManifestPolicy(
        mode=policy_mode,
        expected_run_id=request.expected_run_id or run_id,
        require_pgf=mode is ValidationMode.RELEASE,
    )
    try:
        verification = verify_manifest(
            manifest_path,
            run_root,
            policy,
        )
    except Exception as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_VERIFICATION_ERROR",
                path=manifest_path,
                message=_exception_message(exc),
            ),
        )
        return False
    if not isinstance(verification.status, ValidationStatus):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_RESULT_INVALID",
                path=str(manifest_path),
                message="manifest verifier returned an invalid status",
            ),
        )
        return False

    if verification.status is ValidationStatus.OK:
        for warning in verification.warnings:
            _append_issue(
                issues,
                AutomationIssue(
                    code="AUTOMATION_MANIFEST_WARNING",
                    path=str(manifest_path),
                    message=warning,
                    severity=AutomationIssueSeverity.WARNING,
                ),
            )
        return True

    _append_issue(
        issues,
        AutomationIssue(
            code="AUTOMATION_MANIFEST_VERIFICATION_FAILED",
            path=str(manifest_path),
            message=verification.message,
        ),
    )
    for path in verification.failure_paths:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_ARTIFACT_INVALID",
                path=path,
                message="manifest artifact verification failed",
            ),
        )
    for warning in verification.warnings:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MANIFEST_DETAIL",
                path=str(manifest_path),
                message=warning,
                severity=AutomationIssueSeverity.WARNING,
            ),
        )
    return False


def _validate_expected_identity(
    request: AutomationVerificationRequest,
    *,
    run_id: str | None,
    project_id: str | None,
    mode: ValidationMode | None,
    issues: list[AutomationIssue],
) -> None:
    if (
        request.expected_run_id is not None
        and run_id != request.expected_run_id
    ):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_RUN_ID_MISMATCH",
                path="$.metadata.run_id",
                message=(
                    f"expected {request.expected_run_id!r}, "
                    f"received {run_id!r}"
                ),
            ),
        )

    if (
        request.expected_project_id is not None
        and project_id != request.expected_project_id
    ):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_PROJECT_ID_MISMATCH",
                path="$.metadata.project_id",
                message=(
                    f"expected {request.expected_project_id!r}, "
                    f"received {project_id!r}"
                ),
            ),
        )

    if (
        request.expected_mode is not None
        and mode is not request.expected_mode
    ):
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MODE_MISMATCH",
                path="$.metadata.mode",
                message=(
                    f"expected {request.expected_mode.value!r}, "
                    f"received {mode.value if mode is not None else None!r}"
                ),
            ),
        )


def _resolve_run_relative_file(
    run_root: Path,
    value: str,
    issues: list[AutomationIssue],
    *,
    code: str,
) -> Path | None:
    try:
        text = _require_text(
            value,
            field="artifact path",
            max_length=2_048,
        )
        if "\\" in text or text.startswith("/"):
            raise ValueError(
                "artifact path must be run-relative and use forward slashes"
            )
        candidate = run_root.joinpath(*Path(text).parts)
        candidate.resolve(strict=False).relative_to(
            run_root.resolve(strict=False)
        )
        return candidate
    except (OSError, TypeError, ValueError) as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code=code,
                path=value,
                message=_exception_message(exc),
            ),
        )
        return None


def _summary_issue(issue: SummaryV1Issue) -> AutomationIssue:
    return AutomationIssue(
        code=f"AUTOMATION_SUMMARY_{issue.code.upper()}",
        path=issue.path,
        message=issue.message,
    )


def _optional_mode(
    value: object,
    issues: list[AutomationIssue],
) -> ValidationMode | None:
    try:
        return _coerce_mode(value)
    except (TypeError, ValueError) as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_MODE_INVALID",
                path="$.metadata.mode",
                message=_exception_message(exc),
            ),
        )
        return None


def _optional_overall_status(
    value: object,
    issues: list[AutomationIssue],
) -> OverallStatus | None:
    try:
        if isinstance(value, OverallStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("overall_status must be a string")
        return OverallStatus(value)
    except (TypeError, ValueError) as exc:
        _append_issue(
            issues,
            AutomationIssue(
                code="AUTOMATION_OVERALL_STATUS_INVALID",
                path="$.totals.overall_status",
                message=_exception_message(exc),
            ),
        )
        return None


def _coerce_mode(value: object) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise TypeError("mode must be ValidationMode or string")
    try:
        return ValidationMode(value)
    except ValueError as exc:
        raise ValueError(f"unsupported validation mode {value!r}") from exc


def _project_id(run_config: RunConfig) -> str:
    value = getattr(run_config.project, "project_id", None)
    return _require_text(
        value,
        field="run_config.project.project_id",
        max_length=256,
    )


def _failure_result(
    summary_path: Path,
    manifest_path: Path | None,
    exit_code: int,
    code: str,
    exception: BaseException,
) -> AutomationVerificationResult:
    return AutomationVerificationResult(
        summary_path=summary_path,
        manifest_path=manifest_path,
        run_id=None,
        project_id=None,
        mode=None,
        overall_status=(
            None
            if exit_code == EXIT_CANCELLED
            else OverallStatus.ERROR
        ),
        exit_code=exit_code,
        summary_valid=False,
        manifest_verified=False,
        issues=(
            AutomationIssue(
                code=code,
                message=_exception_message(exception),
            ),
        ),
    )


def _reject_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(
        f"non-finite JSON number is prohibited: {value}"
    )


def _append_issue(
    issues: list[AutomationIssue],
    issue: AutomationIssue,
) -> None:
    if len(issues) >= _MAX_ISSUES:
        if issues and issues[-1].code == "AUTOMATION_ISSUE_LIMIT":
            return
        replacement = AutomationIssue(
            code="AUTOMATION_ISSUE_LIMIT",
            message="additional automation issues were omitted",
        )
        if issues:
            issues[-1] = replacement
        else:
            issues.append(replacement)
        return
    if issue not in issues:
        issues.append(issue)


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if not value.strip() or "\x00" in value:
        return None
    return value


def _coerce_path(value: object, *, field: str) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        if not value.strip():
            raise ValueError(f"{field} must not be empty")
        path = Path(value)
    else:
        raise TypeError(f"{field} must be a path")
    if "\x00" in str(path):
        raise ValueError(f"{field} must not contain NUL")
    return path.expanduser().resolve(strict=False)


def _require_contained_path(
    path: Path,
    root: Path,
    *,
    field: str,
) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"{field} must remain inside run_dir"
        ) from exc


def _normalize_issue_path(value: object) -> Path | str:
    if isinstance(value, Path):
        return value.expanduser().resolve(strict=False)
    if isinstance(value, str):
        return _require_text(
            value,
            field="path",
            max_length=2_048,
        )
    raise TypeError("path must be pathlib.Path, string, or None")


def _render_issue_path(value: Path | str | None) -> str | None:
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _require_text(
    value: object,
    *,
    field: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds {max_length} characters")
    return value


def _exception_message(exception: BaseException) -> str:
    message = " ".join(
        str(exception).replace("\x00", "\\x00").split()
    )
    if not message:
        message = type(exception).__name__
    if len(message) > _MAX_MESSAGE_LENGTH:
        message = f"{message[: _MAX_MESSAGE_LENGTH - 3]}..."
    return f"{type(exception).__name__}: {message}"


__all__ = (
    "AUTOMATION_RESULT_SCHEMA_ID",
    "AUTOMATION_RESULT_SCHEMA_VERSION",
    "AutomationExecutionResult",
    "AutomationIssue",
    "AutomationIssueSeverity",
    "AutomationRunApplication",
    "AutomationVerificationRequest",
    "AutomationVerificationResult",
    "EXIT_CANCELLED",
    "EXIT_OK",
    "EXIT_RUNTIME_ERROR",
    "EXIT_USAGE_ERROR",
    "EXIT_VALIDATION_FAILED",
    "automation_result_document",
    "dumps_automation_result",
    "execute_automation",
    "exit_code_for_overall_status",
    "verify_completed_run",
    "write_automation_result",
)
