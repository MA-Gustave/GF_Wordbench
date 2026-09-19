"""Validation for registered diagnostic-tool catalogs, requests, and results."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Final, TypeAlias

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.ids import validate_project_id, validate_run_id

__all__ = (
    "ToolValidationCode",
    "ToolValidationIssue",
    "ToolValidationReport",
    "ToolValidationSeverity",
    "require_valid_catalog",
    "require_valid_catalog_entry",
    "require_valid_tool_request",
    "require_valid_tool_result",
    "validate_catalog",
    "validate_catalog_entry",
    "validate_tool_request",
    "validate_tool_result",
)

ToolObject: TypeAlias = Mapping[str, Any] | object

_MISSING: Final = object()
_TOOL_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z.-]+)?$"
)
_ROLE_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")
_FLAG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")
_PROFILE_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ALLOWED_RESOLUTION_TYPES: Final = frozenset(
    {
        "bundled",
        "configured_absolute_path",
        "approved_path_lookup",
        "platform_registered_location",
    }
)
_ALLOWED_WORKING_DIRECTORY_POLICIES: Final = frozenset(
    {
        "run_directory",
        "active_project_root",
        "source_root",
        "tool_owned_temporary_directory",
    }
)
_ALLOWED_MUTABILITY: Final = frozenset(
    {
        "read_only",
        "run_artifacts_only",
        "project_mutating",
        "external_mutating",
    }
)
_ALLOWED_CONFIRMATION: Final = frozenset(
    {
        "none",
        "explicit_user_confirmation",
        "reviewed_batch_operation",
    }
)
_ALLOWED_NETWORK: Final = frozenset(
    {
        "denied",
        "loopback_only",
        "approved_endpoints",
    }
)
_ALLOWED_AVAILABILITY: Final = frozenset(
    {
        "required",
        "optional",
        "diagnostic_only",
    }
)
_ALLOWED_PLATFORMS: Final = frozenset({"windows", "linux", "macos"})
_ALLOWED_FLAG_TYPES: Final = frozenset({"boolean", "integer", "number", "string", "enum", "path"})
_ALLOWED_RESULT_STATUSES: Final = frozenset({"completed", "failed", "error", "skipped"})
_ALLOWED_EXECUTION_STATES: Final = frozenset(
    {"completed", "timed_out", "cancelled", "launch_failed"}
)
_REQUIRED_STREAM_ROLES: Final = frozenset({"tool_stdout", "tool_stderr"})


@unique
class ToolValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@unique
class ToolValidationCode(StrEnum):
    REQUIRED_FIELD = "required_field"
    INVALID_TOOL_ID = "invalid_tool_id"
    DUPLICATE_TOOL_ID = "duplicate_tool_id"
    INVALID_VERSION = "invalid_version"
    VERSION_POLICY = "version_policy"
    EXECUTABLE_POLICY = "executable_policy"
    INPUT_POLICY = "input_policy"
    FLAG_POLICY = "flag_policy"
    WORKING_DIRECTORY_POLICY = "working_directory_policy"
    ENVIRONMENT_POLICY = "environment_policy"
    MUTABILITY_POLICY = "mutability_policy"
    CONFIRMATION_POLICY = "confirmation_policy"
    PATH_POLICY = "path_policy"
    NETWORK_POLICY = "network_policy"
    TIMEOUT_POLICY = "timeout_policy"
    OUTPUT_LIMIT_POLICY = "output_limit_policy"
    EVIDENCE_ROLE_POLICY = "evidence_role_policy"
    NORMALIZATION_POLICY = "normalization_policy"
    PARSER_POLICY = "parser_policy"
    AI_POLICY = "ai_policy"
    AVAILABILITY_POLICY = "availability_policy"
    PLATFORM_POLICY = "platform_policy"
    PRODUCT_BOUNDARY = "product_boundary"
    TOOL_MISMATCH = "tool_mismatch"
    PROJECT_ID = "project_id"
    RUN_ID = "run_id"
    SUBJECT_POLICY = "subject_policy"
    REQUEST_FLAG = "request_flag"
    REQUEST_INPUT = "request_input"
    REQUEST_PATH = "request_path"
    REQUEST_TIMEOUT = "request_timeout"
    REQUEST_OUTPUT_LIMIT = "request_output_limit"
    REQUEST_CONFIRMATION = "request_confirmation"
    REQUEST_PLATFORM = "request_platform"
    RESULT_STATUS = "result_status"
    RESULT_EXECUTION = "result_execution"
    RESULT_COMMAND = "result_command"
    RESULT_PATH = "result_path"
    RESULT_EVIDENCE = "result_evidence"
    RESULT_VERSION = "result_version"


@dataclass(frozen=True, slots=True)
class ToolValidationIssue:
    code: ToolValidationCode
    severity: ToolValidationSeverity
    field: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _validation_code(self.code))
        object.__setattr__(
            self,
            "severity",
            _validation_severity(self.severity),
        )
        for name in ("field", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
            if "\x00" in value:
                raise ValueError(f"{name} must not contain NUL characters")


@dataclass(frozen=True, slots=True)
class ToolValidationReport:
    issues: tuple[ToolValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(self.issues)
        if not all(isinstance(item, ToolValidationIssue) for item in values):
            raise TypeError("issues must contain ToolValidationIssue values")
        object.__setattr__(
            self,
            "issues",
            tuple(sorted(values, key=_issue_key)),
        )

    @property
    def valid(self) -> bool:
        return not any(issue.severity is ToolValidationSeverity.ERROR for issue in self.issues)

    @property
    def errors(self) -> tuple[ToolValidationIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity is ToolValidationSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ToolValidationIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity is ToolValidationSeverity.WARNING
        )

    def merge(self, *others: ToolValidationReport) -> ToolValidationReport:
        merged = list(self.issues)
        for other in others:
            if not isinstance(other, ToolValidationReport):
                raise TypeError("merge accepts ToolValidationReport values")
            merged.extend(other.issues)
        return ToolValidationReport(tuple(merged))


def validate_catalog(
    entries: Iterable[ToolObject],
) -> ToolValidationReport:
    values = tuple(entries)
    issues: list[ToolValidationIssue] = []
    seen: dict[str, int] = {}
    for index, entry in enumerate(values):
        issues.extend(validate_catalog_entry(entry).issues)
        tool_id = _text(_field(entry, "tool_id", ""))
        if tool_id:
            if tool_id in seen:
                issues.append(
                    _error(
                        ToolValidationCode.DUPLICATE_TOOL_ID,
                        f"entries[{index}].tool_id",
                        f"tool_id {tool_id!r} duplicates entries[{seen[tool_id]}]",
                    )
                )
            else:
                seen[tool_id] = index
    return ToolValidationReport(tuple(issues))


def validate_catalog_entry(
    entry: ToolObject,
) -> ToolValidationReport:
    issues: list[ToolValidationIssue] = []
    tool_id = _text(_field(entry, "tool_id", ""))
    if not tool_id:
        issues.append(_required("tool_id"))
    elif _TOOL_ID_RE.fullmatch(tool_id) is None:
        issues.append(
            _error(
                ToolValidationCode.INVALID_TOOL_ID,
                "tool_id",
                "tool_id must be lowercase ASCII kebab case",
            )
        )

    catalog_version = _text(_field(entry, "catalog_version", ""))
    if not catalog_version:
        issues.append(_required("catalog_version"))
    elif _VERSION_RE.fullmatch(catalog_version) is None:
        issues.append(
            _error(
                ToolValidationCode.INVALID_VERSION,
                "catalog_version",
                "catalog_version must be a dotted numeric version",
            )
        )

    for name in ("description", "purpose"):
        if not _text(_field(entry, name, "")):
            issues.append(_required(name))

    issues.extend(_validate_version_policy(entry))
    issues.extend(_validate_executable_resolution(entry))
    issues.extend(_validate_input_contract(entry))
    issues.extend(_validate_flag_contract(entry))
    issues.extend(
        _validate_enum_field(
            entry,
            "working_directory_policy",
            _ALLOWED_WORKING_DIRECTORY_POLICIES,
            ToolValidationCode.WORKING_DIRECTORY_POLICY,
        )
    )
    issues.extend(_validate_environment_policy(entry))
    issues.extend(
        _validate_enum_field(
            entry,
            "mutability",
            _ALLOWED_MUTABILITY,
            ToolValidationCode.MUTABILITY_POLICY,
        )
    )
    issues.extend(
        _validate_enum_field(
            entry,
            "confirmation_policy",
            _ALLOWED_CONFIRMATION,
            ToolValidationCode.CONFIRMATION_POLICY,
        )
    )
    issues.extend(_validate_allowed_paths(entry))
    issues.extend(_validate_network_policy(entry))
    issues.extend(_validate_timeout(entry))
    issues.extend(_validate_output_limits(entry))
    issues.extend(_validate_evidence_roles(entry))
    issues.extend(
        _validate_profile_field(
            entry,
            "normalization_profile",
            ToolValidationCode.NORMALIZATION_POLICY,
        )
    )
    issues.extend(
        _validate_profile_field(
            entry,
            "parser_id",
            ToolValidationCode.PARSER_POLICY,
        )
    )
    issues.extend(
        _validate_enum_field(
            entry,
            "availability_policy",
            _ALLOWED_AVAILABILITY,
            ToolValidationCode.AVAILABILITY_POLICY,
        )
    )
    issues.extend(_validate_platforms(entry))
    issues.extend(_validate_cross_field_policies(entry))
    issues.extend(_validate_product_boundary(entry))
    return ToolValidationReport(tuple(issues))


def validate_tool_request(
    request: ToolObject,
    entry: ToolObject,
    *,
    platform: str | None = None,
    active_project_root: Path | None = None,
    run_root: Path | None = None,
    source_root: Path | None = None,
    temporary_root: Path | None = None,
) -> ToolValidationReport:
    issues = list(validate_catalog_entry(entry).errors)
    entry_tool_id = _text(_field(entry, "tool_id", ""))
    request_tool_id = _text(_field(request, "tool_id", ""))
    if request_tool_id != entry_tool_id:
        issues.append(
            _error(
                ToolValidationCode.TOOL_MISMATCH,
                "tool_id",
                f"request tool_id {request_tool_id!r} does not match {entry_tool_id!r}",
            )
        )

    project_id = _field(request, "active_project_id", _MISSING)
    if project_id is _MISSING:
        issues.append(_required("active_project_id"))
    else:
        try:
            validate_project_id(project_id)
        except (TypeError, ValueError) as exc:
            issues.append(
                _error(
                    ToolValidationCode.PROJECT_ID,
                    "active_project_id",
                    str(exc),
                )
            )

    run_id = _field(request, "run_id", _MISSING)
    if run_id is _MISSING:
        issues.append(_required("run_id"))
    else:
        try:
            validate_run_id(run_id)
        except (TypeError, ValueError) as exc:
            issues.append(
                _error(
                    ToolValidationCode.RUN_ID,
                    "run_id",
                    str(exc),
                )
            )

    subject_ids = _sequence(
        _field(request, "subject_ids", ()),
        "subject_ids",
        issues,
        ToolValidationCode.SUBJECT_POLICY,
    )
    input_contract = _field(entry, "input_contract", {})
    max_subjects = _positive_int_or_none(_field(input_contract, "maximum_input_count", None))
    if max_subjects is not None and len(subject_ids) > max_subjects:
        issues.append(
            _error(
                ToolValidationCode.SUBJECT_POLICY,
                "subject_ids",
                f"request has {len(subject_ids)} subjects; maximum is {max_subjects}",
            )
        )

    issues.extend(_validate_request_inputs(request, input_contract))
    issues.extend(_validate_request_flags(request, entry))
    issues.extend(
        _validate_request_working_directory(
            request,
            entry,
            active_project_root=active_project_root,
            run_root=run_root,
            source_root=source_root,
            temporary_root=temporary_root,
        )
    )
    issues.extend(_validate_request_timeout(request, entry))
    issues.extend(_validate_request_output_limits(request, entry))
    issues.extend(_validate_request_confirmation(request, entry))
    issues.extend(_validate_request_platform(entry, platform))
    return ToolValidationReport(tuple(issues))


def validate_tool_result(
    result: ToolObject,
    entry: ToolObject,
    *,
    run_root: Path | None = None,
) -> ToolValidationReport:
    issues = list(validate_catalog_entry(entry).errors)
    entry_tool_id = _text(_field(entry, "tool_id", ""))
    result_tool_id = _text(_field(result, "tool_id", ""))
    if result_tool_id != entry_tool_id:
        issues.append(
            _error(
                ToolValidationCode.TOOL_MISMATCH,
                "tool_id",
                f"result tool_id {result_tool_id!r} does not match {entry_tool_id!r}",
            )
        )

    entry_catalog_version = _text(_field(entry, "catalog_version", ""))
    result_catalog_version = _text(_field(result, "catalog_version", ""))
    if result_catalog_version != entry_catalog_version:
        issues.append(
            _error(
                ToolValidationCode.RESULT_VERSION,
                "catalog_version",
                "result catalog_version does not match the catalog entry",
            )
        )

    resolved_version = _text(_field(result, "resolved_tool_version", ""))
    if not resolved_version:
        issues.append(_required("resolved_tool_version"))
    else:
        issues.extend(
            _validate_resolved_version(
                resolved_version,
                _field(entry, "tool_version_policy", {}),
            )
        )

    status = _text(_field(result, "status", ""))
    if status not in _ALLOWED_RESULT_STATUSES:
        issues.append(
            _error(
                ToolValidationCode.RESULT_STATUS,
                "status",
                f"status must be one of {sorted(_ALLOWED_RESULT_STATUSES)}",
            )
        )

    execution_state = _text(_field(result, "execution_state", ""))
    if execution_state not in _ALLOWED_EXECUTION_STATES:
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "execution_state",
                f"execution_state must be one of {sorted(_ALLOWED_EXECUTION_STATES)}",
            )
        )
    elif status in {"completed", "failed"} and execution_state != "completed":
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "execution_state",
                f"status {status!r} requires completed execution",
            )
        )
    elif status == "skipped" and execution_state == "completed":
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "execution_state",
                "skipped status cannot represent a completed process",
            )
        )

    exit_code = _field(result, "exit_code", None)
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "exit_code",
                "exit_code must be an integer or None",
            )
        )
    if execution_state == "completed" and exit_code is None:
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "exit_code",
                "completed execution requires an exit code",
            )
        )

    duration_ms = _field(result, "duration_ms", _MISSING)
    if (
        duration_ms is _MISSING
        or isinstance(duration_ms, bool)
        or not isinstance(duration_ms, int)
        or duration_ms < 0
    ):
        issues.append(
            _error(
                ToolValidationCode.RESULT_EXECUTION,
                "duration_ms",
                "duration_ms must be a non-negative integer",
            )
        )

    issues.extend(_validate_result_command(result))
    issues.extend(_validate_result_paths(result, run_root))
    issues.extend(_validate_result_evidence(result, entry, run_root))

    ai_assisted = _strict_bool(_field(result, "ai_assisted", False))
    normative = _strict_bool(_field(result, "normative", False))
    entry_ai = _strict_bool(_field(entry, "ai_assisted", False))
    entry_normative = _strict_bool(_field(entry, "normative", False))
    if ai_assisted is None or normative is None:
        issues.append(
            _error(
                ToolValidationCode.AI_POLICY,
                "ai_assisted/normative",
                "ai_assisted and normative must be bools",
            )
        )
    else:
        if ai_assisted != entry_ai or normative != entry_normative:
            issues.append(
                _error(
                    ToolValidationCode.AI_POLICY,
                    "ai_assisted/normative",
                    "result AI and normative flags must match the catalog entry",
                )
            )
        if ai_assisted and normative:
            issues.append(
                _error(
                    ToolValidationCode.AI_POLICY,
                    "normative",
                    "AI-assisted diagnostic output cannot be normative",
                )
            )

    truncated = _field(result, "truncated", False)
    if not isinstance(truncated, bool):
        issues.append(
            _error(
                ToolValidationCode.RESULT_EVIDENCE,
                "truncated",
                "truncated must be a bool",
            )
        )
    return ToolValidationReport(tuple(issues))


def require_valid_catalog(
    entries: Iterable[ToolObject],
) -> tuple[ToolObject, ...]:
    values = tuple(entries)
    _raise_if_invalid(validate_catalog(values), "catalog", None)
    return values


def require_valid_catalog_entry(entry: ToolObject) -> ToolObject:
    _raise_if_invalid(
        validate_catalog_entry(entry),
        "catalog-entry",
        _text(_field(entry, "tool_id", "")) or None,
    )
    return entry


def require_valid_tool_request(
    request: ToolObject,
    entry: ToolObject,
    **kwargs: Any,
) -> ToolObject:
    _raise_if_invalid(
        validate_tool_request(request, entry, **kwargs),
        "tool-request",
        _text(_field(request, "tool_id", "")) or None,
    )
    return request


def require_valid_tool_result(
    result: ToolObject,
    entry: ToolObject,
    **kwargs: Any,
) -> ToolObject:
    _raise_if_invalid(
        validate_tool_result(result, entry, **kwargs),
        "tool-result",
        _text(_field(result, "tool_id", "")) or None,
    )
    return result


def _validate_version_policy(entry: ToolObject) -> list[ToolValidationIssue]:
    policy = _field(entry, "tool_version_policy", _MISSING)
    if policy is _MISSING:
        return [_required("tool_version_policy")]
    issues: list[ToolValidationIssue] = []
    fields = (
        "minimum_version",
        "maximum_version",
        "tested_versions",
        "blocked_versions",
        "version_probe",
        "unparseable_version_policy",
    )
    if not any(_field(policy, name, None) not in (None, "", (), []) for name in fields):
        issues.append(
            _error(
                ToolValidationCode.VERSION_POLICY,
                "tool_version_policy",
                "version policy must define at least one explicit constraint",
            )
        )
    for name in ("minimum_version", "maximum_version"):
        value = _text(_field(policy, name, ""))
        if value and _VERSION_RE.fullmatch(value) is None:
            issues.append(
                _error(
                    ToolValidationCode.INVALID_VERSION,
                    f"tool_version_policy.{name}",
                    f"{name} must be a dotted numeric version",
                )
            )
    minimum = _text(_field(policy, "minimum_version", ""))
    maximum = _text(_field(policy, "maximum_version", ""))
    if minimum and maximum and _version_key(minimum) > _version_key(maximum):
        issues.append(
            _error(
                ToolValidationCode.VERSION_POLICY,
                "tool_version_policy",
                "minimum_version must not exceed maximum_version",
            )
        )
    return issues


def _validate_executable_resolution(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    resolution = _field(entry, "executable_resolution", _MISSING)
    if resolution is _MISSING:
        return [_required("executable_resolution")]
    kind = _text(_field(resolution, "type", resolution if isinstance(resolution, str) else ""))
    issues: list[ToolValidationIssue] = []
    if kind not in _ALLOWED_RESOLUTION_TYPES:
        issues.append(
            _error(
                ToolValidationCode.EXECUTABLE_POLICY,
                "executable_resolution.type",
                f"resolution type must be one of {sorted(_ALLOWED_RESOLUTION_TYPES)}",
            )
        )
    if _field(resolution, "shell", False) is True:
        issues.append(
            _error(
                ToolValidationCode.EXECUTABLE_POLICY,
                "executable_resolution.shell",
                "diagnostic tools must use a structured argument vector",
            )
        )
    return issues


def _validate_input_contract(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    contract = _field(entry, "input_contract", _MISSING)
    if contract is _MISSING:
        return [_required("input_contract")]
    issues: list[ToolValidationIssue] = []
    count = _field(contract, "maximum_input_count", _MISSING)
    size = _field(contract, "maximum_input_size_bytes", _MISSING)
    if count is _MISSING or _positive_int_or_none(count) is None:
        issues.append(
            _error(
                ToolValidationCode.INPUT_POLICY,
                "input_contract.maximum_input_count",
                "maximum_input_count must be a positive integer",
            )
        )
    if size is _MISSING or _positive_int_or_none(size) is None:
        issues.append(
            _error(
                ToolValidationCode.INPUT_POLICY,
                "input_contract.maximum_input_size_bytes",
                "maximum_input_size_bytes must be a positive integer",
            )
        )
    return issues


def _validate_flag_contract(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    flags = _field(entry, "allowed_flags", _MISSING)
    if flags is _MISSING:
        return [_required("allowed_flags")]
    if not isinstance(flags, Mapping):
        return [
            _error(
                ToolValidationCode.FLAG_POLICY,
                "allowed_flags",
                "allowed_flags must be a mapping",
            )
        ]
    issues: list[ToolValidationIssue] = []
    for name, specification in flags.items():
        if not isinstance(name, str) or _FLAG_RE.fullmatch(name) is None:
            issues.append(
                _error(
                    ToolValidationCode.FLAG_POLICY,
                    f"allowed_flags.{name}",
                    "flag names must be lowercase ASCII identifiers",
                )
            )
            continue
        flag_type = _text(_field(specification, "type", ""))
        if flag_type not in _ALLOWED_FLAG_TYPES:
            issues.append(
                _error(
                    ToolValidationCode.FLAG_POLICY,
                    f"allowed_flags.{name}.type",
                    f"flag type must be one of {sorted(_ALLOWED_FLAG_TYPES)}",
                )
            )
    return issues


def _validate_environment_policy(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    policy = _field(entry, "environment_policy", _MISSING)
    if policy is _MISSING:
        return [_required("environment_policy")]
    if isinstance(policy, str):
        if not policy.strip():
            return [_required("environment_policy")]
        return []
    if not isinstance(policy, Mapping) and not hasattr(policy, "__dict__"):
        return [
            _error(
                ToolValidationCode.ENVIRONMENT_POLICY,
                "environment_policy",
                "environment_policy must be structured or a named policy",
            )
        ]
    if _field(policy, "inherit_all", False) is True:
        return [
            _error(
                ToolValidationCode.ENVIRONMENT_POLICY,
                "environment_policy.inherit_all",
                "complete environment inheritance is prohibited",
            )
        ]
    return []


def _validate_allowed_paths(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    allowed = _field(entry, "allowed_paths", _MISSING)
    if allowed is _MISSING:
        return [_required("allowed_paths")]
    read = set(_text_values(_field(allowed, "read", ())))
    write = set(_text_values(_field(allowed, "write", ())))
    issues: list[ToolValidationIssue] = []
    if read.intersection(write):
        issues.append(
            _error(
                ToolValidationCode.PATH_POLICY,
                "allowed_paths",
                "readable and writable path classes must be distinct",
            )
        )
    mutability = _text(_field(entry, "mutability", ""))
    if mutability == "read_only" and write:
        issues.append(
            _error(
                ToolValidationCode.PATH_POLICY,
                "allowed_paths.write",
                "read_only tools cannot declare writable project or external paths",
            )
        )
    if mutability == "run_artifacts_only" and any("run" not in item for item in write):
        issues.append(
            _error(
                ToolValidationCode.PATH_POLICY,
                "allowed_paths.write",
                "run_artifacts_only tools may write only run-owned path classes",
            )
        )
    return issues


def _validate_network_policy(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    issues = _validate_enum_field(
        entry,
        "network_policy",
        _ALLOWED_NETWORK,
        ToolValidationCode.NETWORK_POLICY,
    )
    if _text(_field(entry, "network_policy", "")) == "approved_endpoints":
        endpoints = _text_values(_field(entry, "approved_endpoints", ()))
        if not endpoints:
            issues.append(
                _error(
                    ToolValidationCode.NETWORK_POLICY,
                    "approved_endpoints",
                    "approved_endpoints policy requires explicit endpoints",
                )
            )
    return issues


def _validate_timeout(entry: ToolObject) -> list[ToolValidationIssue]:
    value = _field(entry, "timeout_sec", _MISSING)
    if not _positive_finite(value):
        return [
            _error(
                ToolValidationCode.TIMEOUT_POLICY,
                "timeout_sec",
                "timeout_sec must be a finite positive number",
            )
        ]
    return []


def _validate_output_limits(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    limits = _field(entry, "output_limit_bytes", _MISSING)
    if limits is _MISSING:
        return [_required("output_limit_bytes")]
    issues: list[ToolValidationIssue] = []
    for name in ("stdout", "stderr"):
        if _positive_int_or_none(_field(limits, name, None)) is None:
            issues.append(
                _error(
                    ToolValidationCode.OUTPUT_LIMIT_POLICY,
                    f"output_limit_bytes.{name}",
                    f"{name} output limit must be a positive integer",
                )
            )
    optional_names = ("generated_files", "total_files", "total_retained")
    if not any(
        _positive_int_or_none(_field(limits, name, None)) is not None for name in optional_names
    ):
        issues.append(
            _error(
                ToolValidationCode.OUTPUT_LIMIT_POLICY,
                "output_limit_bytes",
                "a generated or total retained output limit is required",
            )
        )
    return issues


def _validate_evidence_roles(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    roles = frozenset(_text_values(_field(entry, "evidence_roles", ())))
    issues: list[ToolValidationIssue] = []
    if not roles:
        issues.append(_required("evidence_roles"))
        return issues
    for role in roles:
        if _ROLE_RE.fullmatch(role) is None:
            issues.append(
                _error(
                    ToolValidationCode.EVIDENCE_ROLE_POLICY,
                    "evidence_roles",
                    f"invalid evidence role {role!r}",
                )
            )
    missing = _REQUIRED_STREAM_ROLES.difference(roles)
    if missing:
        issues.append(
            _error(
                ToolValidationCode.EVIDENCE_ROLE_POLICY,
                "evidence_roles",
                f"missing required stream roles: {sorted(missing)}",
            )
        )
    if _field(entry, "ai_assisted", False) is True and "ai_annotation" not in roles:
        issues.append(
            _error(
                ToolValidationCode.AI_POLICY,
                "evidence_roles",
                "AI-assisted tools must declare ai_annotation",
            )
        )
    return issues


def _validate_profile_field(
    entry: ToolObject,
    name: str,
    code: ToolValidationCode,
) -> list[ToolValidationIssue]:
    value = _text(_field(entry, name, ""))
    if not value:
        return [_required(name)]
    if _PROFILE_RE.fullmatch(value) is None:
        return [
            _error(
                code,
                name,
                f"{name} must be lowercase ASCII kebab case",
            )
        ]
    return []


def _validate_platforms(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    platforms = frozenset(_text_values(_field(entry, "platforms", ())))
    if not platforms:
        return [_required("platforms")]
    unsupported = platforms.difference(_ALLOWED_PLATFORMS)
    if unsupported:
        return [
            _error(
                ToolValidationCode.PLATFORM_POLICY,
                "platforms",
                f"unsupported platform values: {sorted(unsupported)}",
            )
        ]
    return []


def _validate_cross_field_policies(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    issues: list[ToolValidationIssue] = []
    mutability = _text(_field(entry, "mutability", ""))
    confirmation = _text(_field(entry, "confirmation_policy", ""))
    ai_assisted = _field(entry, "ai_assisted", _MISSING)
    normative = _field(entry, "normative", _MISSING)
    availability = _text(_field(entry, "availability_policy", ""))

    if ai_assisted is _MISSING or not isinstance(ai_assisted, bool):
        issues.append(
            _error(
                ToolValidationCode.AI_POLICY,
                "ai_assisted",
                "ai_assisted must be a bool",
            )
        )
    if normative is _MISSING or not isinstance(normative, bool):
        issues.append(
            _error(
                ToolValidationCode.AI_POLICY,
                "normative",
                "normative must be a bool",
            )
        )
    if ai_assisted is True:
        if normative is True:
            issues.append(
                _error(
                    ToolValidationCode.AI_POLICY,
                    "normative",
                    "AI-assisted tools must be non-normative",
                )
            )
        if availability == "required":
            issues.append(
                _error(
                    ToolValidationCode.AI_POLICY,
                    "availability_policy",
                    "AI-assisted tools cannot be required for core validation",
                )
            )
    if mutability in {"project_mutating", "external_mutating"} and confirmation == "none":
        issues.append(
            _error(
                ToolValidationCode.CONFIRMATION_POLICY,
                "confirmation_policy",
                "mutating tools require explicit confirmation",
            )
        )
    if mutability == "external_mutating" and not _text(_field(entry, "security_contract_id", "")):
        issues.append(
            _error(
                ToolValidationCode.MUTABILITY_POLICY,
                "security_contract_id",
                "external_mutating tools require an accepted security contract",
            )
        )
    return issues


def _validate_product_boundary(
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    haystack = repr(entry).casefold()
    if "gf-portfolio" in haystack or "gf_portfolio" in haystack:
        return [
            _error(
                ToolValidationCode.PRODUCT_BOUNDARY,
                "entry",
                "diagnostic-tool entries cannot depend on gf-portfolio",
            )
        ]
    return []


def _validate_request_inputs(
    request: ToolObject,
    contract: ToolObject,
) -> list[ToolValidationIssue]:
    issues: list[ToolValidationIssue] = []
    inputs = _sequence(
        _field(request, "resolved_inputs", ()),
        "resolved_inputs",
        issues,
        ToolValidationCode.REQUEST_INPUT,
    )
    max_count = _positive_int_or_none(_field(contract, "maximum_input_count", None))
    max_size = _positive_int_or_none(_field(contract, "maximum_input_size_bytes", None))
    if max_count is not None and len(inputs) > max_count:
        issues.append(
            _error(
                ToolValidationCode.REQUEST_INPUT,
                "resolved_inputs",
                f"input count {len(inputs)} exceeds maximum {max_count}",
            )
        )
    allowed_types = frozenset(_text_values(_field(contract, "file_types", ())))
    for index, item in enumerate(inputs):
        path_value = _field(item, "path", item if isinstance(item, (str, os.PathLike)) else None)
        if path_value is not None and allowed_types:
            suffix = Path(path_value).suffix
            if suffix not in allowed_types:
                issues.append(
                    _error(
                        ToolValidationCode.REQUEST_INPUT,
                        f"resolved_inputs[{index}].path",
                        f"file type {suffix!r} is not allowed",
                    )
                )
        size = _field(item, "size_bytes", None)
        if size is not None and max_size is not None:
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                issues.append(
                    _error(
                        ToolValidationCode.REQUEST_INPUT,
                        f"resolved_inputs[{index}].size_bytes",
                        "size_bytes must be a non-negative integer",
                    )
                )
            elif size > max_size:
                issues.append(
                    _error(
                        ToolValidationCode.REQUEST_INPUT,
                        f"resolved_inputs[{index}].size_bytes",
                        f"input size exceeds maximum {max_size}",
                    )
                )
    return issues


def _validate_request_flags(
    request: ToolObject,
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    selected = _field(request, "selected_registered_flags", {})
    allowed = _field(entry, "allowed_flags", {})
    if not isinstance(selected, Mapping):
        return [
            _error(
                ToolValidationCode.REQUEST_FLAG,
                "selected_registered_flags",
                "selected_registered_flags must be a mapping",
            )
        ]
    issues: list[ToolValidationIssue] = []
    for name, value in selected.items():
        specification = allowed.get(name) if isinstance(allowed, Mapping) else None
        if specification is None:
            issues.append(
                _error(
                    ToolValidationCode.REQUEST_FLAG,
                    f"selected_registered_flags.{name}",
                    "flag is not registered",
                )
            )
            continue
        expected = _text(_field(specification, "type", ""))
        if not _value_matches_flag_type(value, expected, specification):
            issues.append(
                _error(
                    ToolValidationCode.REQUEST_FLAG,
                    f"selected_registered_flags.{name}",
                    f"flag value does not match registered type {expected!r}",
                )
            )
    return issues


def _validate_request_working_directory(
    request: ToolObject,
    entry: ToolObject,
    *,
    active_project_root: Path | None,
    run_root: Path | None,
    source_root: Path | None,
    temporary_root: Path | None,
) -> list[ToolValidationIssue]:
    raw = _field(request, "working_directory", _MISSING)
    if raw is _MISSING:
        return [_required("working_directory")]
    try:
        path = _absolute_path(raw)
    except (TypeError, ValueError) as exc:
        return [
            _error(
                ToolValidationCode.REQUEST_PATH,
                "working_directory",
                str(exc),
            )
        ]
    policy = _text(_field(entry, "working_directory_policy", ""))
    roots = {
        "active_project_root": active_project_root,
        "run_directory": run_root,
        "source_root": source_root,
        "tool_owned_temporary_directory": temporary_root,
    }
    expected_root = roots.get(policy)
    if expected_root is not None and not _is_within(path, expected_root):
        return [
            _error(
                ToolValidationCode.REQUEST_PATH,
                "working_directory",
                f"working directory violates {policy}",
            )
        ]
    return []


def _validate_request_timeout(
    request: ToolObject,
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    requested = _field(request, "timeout_sec", _MISSING)
    maximum = _field(entry, "timeout_sec", _MISSING)
    if not _positive_finite(requested):
        return [
            _error(
                ToolValidationCode.REQUEST_TIMEOUT,
                "timeout_sec",
                "request timeout must be finite and positive",
            )
        ]
    if _positive_finite(maximum) and float(requested) > float(maximum):
        return [
            _error(
                ToolValidationCode.REQUEST_TIMEOUT,
                "timeout_sec",
                "request timeout exceeds the registered limit",
            )
        ]
    return []


def _validate_request_output_limits(
    request: ToolObject,
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    requested = _field(request, "output_limits", {})
    registered = _field(entry, "output_limit_bytes", {})
    if not isinstance(requested, Mapping):
        return [
            _error(
                ToolValidationCode.REQUEST_OUTPUT_LIMIT,
                "output_limits",
                "output_limits must be a mapping",
            )
        ]
    issues: list[ToolValidationIssue] = []
    for name, value in requested.items():
        maximum = _field(registered, name, None)
        if _positive_int_or_none(value) is None:
            issues.append(
                _error(
                    ToolValidationCode.REQUEST_OUTPUT_LIMIT,
                    f"output_limits.{name}",
                    "requested output limit must be a positive integer",
                )
            )
        elif _positive_int_or_none(maximum) is None:
            issues.append(
                _error(
                    ToolValidationCode.REQUEST_OUTPUT_LIMIT,
                    f"output_limits.{name}",
                    "requested output limit is not registered",
                )
            )
        elif value > maximum:
            issues.append(
                _error(
                    ToolValidationCode.REQUEST_OUTPUT_LIMIT,
                    f"output_limits.{name}",
                    "requested output limit exceeds the registered limit",
                )
            )
    return issues


def _validate_request_confirmation(
    request: ToolObject,
    entry: ToolObject,
) -> list[ToolValidationIssue]:
    policy = _text(_field(entry, "confirmation_policy", ""))
    record = _field(request, "confirmation_record", None)
    if policy == "none":
        return []
    if (
        record is None
        or record is False
        or not _text(_field(record, "confirmation_id", record if isinstance(record, str) else ""))
    ):
        return [
            _error(
                ToolValidationCode.REQUEST_CONFIRMATION,
                "confirmation_record",
                f"{policy} requires a fresh confirmation record",
            )
        ]
    return []


def _validate_request_platform(
    entry: ToolObject,
    platform: str | None,
) -> list[ToolValidationIssue]:
    actual = _normalize_platform(platform)
    supported = frozenset(_text_values(_field(entry, "platforms", ())))
    if actual not in supported:
        return [
            _error(
                ToolValidationCode.REQUEST_PLATFORM,
                "platform",
                f"platform {actual!r} is not supported by this tool",
            )
        ]
    return []


def _validate_result_command(
    result: ToolObject,
) -> list[ToolValidationIssue]:
    command = _field(result, "command", _MISSING)
    if command is _MISSING:
        return [_required("command")]
    if isinstance(command, (str, bytes)) or not isinstance(command, Sequence):
        return [
            _error(
                ToolValidationCode.RESULT_COMMAND,
                "command",
                "command must be an ordered argument sequence",
            )
        ]
    if not command:
        return [
            _error(
                ToolValidationCode.RESULT_COMMAND,
                "command",
                "command must not be empty",
            )
        ]
    for index, value in enumerate(command):
        if not isinstance(value, str) or "\x00" in value:
            return [
                _error(
                    ToolValidationCode.RESULT_COMMAND,
                    f"command[{index}]",
                    "command arguments must be NUL-free strings",
                )
            ]
    return []


def _validate_result_paths(
    result: ToolObject,
    run_root: Path | None,
) -> list[ToolValidationIssue]:
    issues: list[ToolValidationIssue] = []
    paths: dict[str, Path] = {}
    for name in ("working_directory", "stdout_path", "stderr_path"):
        raw = _field(result, name, _MISSING)
        if raw is _MISSING:
            issues.append(_required(name))
            continue
        try:
            paths[name] = _absolute_path(raw)
        except (TypeError, ValueError) as exc:
            issues.append(
                _error(
                    ToolValidationCode.RESULT_PATH,
                    name,
                    str(exc),
                )
            )
    if (
        "stdout_path" in paths
        and "stderr_path" in paths
        and _path_key(paths["stdout_path"]) == _path_key(paths["stderr_path"])
    ):
        issues.append(
            _error(
                ToolValidationCode.RESULT_PATH,
                "stdout_path/stderr_path",
                "stdout and stderr evidence paths must be distinct",
            )
        )
    if run_root is not None:
        for name in ("stdout_path", "stderr_path"):
            if name in paths and not _is_within(paths[name], run_root):
                issues.append(
                    _error(
                        ToolValidationCode.RESULT_PATH,
                        name,
                        "raw stream evidence must remain inside the run root",
                    )
                )
    return issues


def _validate_result_evidence(
    result: ToolObject,
    entry: ToolObject,
    run_root: Path | None,
) -> list[ToolValidationIssue]:
    issues: list[ToolValidationIssue] = []
    declared = frozenset(_text_values(_field(entry, "evidence_roles", ())))
    roles = frozenset(_text_values(_field(result, "evidence_roles", ())))
    missing_streams = _REQUIRED_STREAM_ROLES.difference(roles)
    if missing_streams:
        issues.append(
            _error(
                ToolValidationCode.RESULT_EVIDENCE,
                "evidence_roles",
                f"result is missing stream roles {sorted(missing_streams)}",
            )
        )
    undeclared = roles.difference(declared)
    if undeclared:
        issues.append(
            _error(
                ToolValidationCode.RESULT_EVIDENCE,
                "evidence_roles",
                f"result contains undeclared evidence roles {sorted(undeclared)}",
            )
        )
    artifacts = _field(result, "output_artifacts", ())
    if isinstance(artifacts, (str, bytes)) or not isinstance(artifacts, Sequence):
        issues.append(
            _error(
                ToolValidationCode.RESULT_EVIDENCE,
                "output_artifacts",
                "output_artifacts must be a sequence",
            )
        )
        return issues
    seen: set[str] = set()
    for index, artifact in enumerate(artifacts):
        role = _text(_field(artifact, "role", ""))
        if role not in declared:
            issues.append(
                _error(
                    ToolValidationCode.RESULT_EVIDENCE,
                    f"output_artifacts[{index}].role",
                    f"artifact role {role!r} is not declared",
                )
            )
        raw_path = _field(
            artifact, "path", artifact if isinstance(artifact, (str, os.PathLike)) else _MISSING
        )
        if raw_path is _MISSING:
            issues.append(_required(f"output_artifacts[{index}].path"))
            continue
        try:
            path = _absolute_path(raw_path)
        except (TypeError, ValueError) as exc:
            issues.append(
                _error(
                    ToolValidationCode.RESULT_EVIDENCE,
                    f"output_artifacts[{index}].path",
                    str(exc),
                )
            )
            continue
        key = _path_key(path)
        if key in seen:
            issues.append(
                _error(
                    ToolValidationCode.RESULT_EVIDENCE,
                    f"output_artifacts[{index}].path",
                    "artifact path is duplicated",
                )
            )
        seen.add(key)
        if run_root is not None and not _is_within(path, run_root):
            issues.append(
                _error(
                    ToolValidationCode.RESULT_EVIDENCE,
                    f"output_artifacts[{index}].path",
                    "tool output artifact escapes the run root",
                )
            )
    return issues


def _validate_resolved_version(
    version: str,
    policy: ToolObject,
) -> list[ToolValidationIssue]:
    issues: list[ToolValidationIssue] = []
    if _VERSION_RE.fullmatch(version) is None:
        issues.append(
            _error(
                ToolValidationCode.RESULT_VERSION,
                "resolved_tool_version",
                "resolved tool version is not parseable",
            )
        )
        return issues
    key = _version_key(version)
    minimum = _text(_field(policy, "minimum_version", ""))
    maximum = _text(_field(policy, "maximum_version", ""))
    blocked = frozenset(_text_values(_field(policy, "blocked_versions", ())))
    if minimum and key < _version_key(minimum):
        issues.append(
            _error(
                ToolValidationCode.RESULT_VERSION,
                "resolved_tool_version",
                "resolved version is below the registered minimum",
            )
        )
    if maximum and key > _version_key(maximum):
        issues.append(
            _error(
                ToolValidationCode.RESULT_VERSION,
                "resolved_tool_version",
                "resolved version exceeds the registered maximum",
            )
        )
    if version in blocked:
        issues.append(
            _error(
                ToolValidationCode.RESULT_VERSION,
                "resolved_tool_version",
                "resolved version is explicitly blocked",
            )
        )
    return issues


def _validate_enum_field(
    obj: ToolObject,
    name: str,
    allowed: frozenset[str],
    code: ToolValidationCode,
) -> list[ToolValidationIssue]:
    value = _text(_field(obj, name, ""))
    if not value:
        return [_required(name)]
    if value not in allowed:
        return [
            _error(
                code,
                name,
                f"{name} must be one of {sorted(allowed)}",
            )
        ]
    return []


def _value_matches_flag_type(
    value: object,
    expected: str,
    specification: ToolObject,
) -> bool:
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    if expected == "string":
        return isinstance(value, str) and "\x00" not in value
    if expected == "path":
        return isinstance(value, (str, os.PathLike))
    if expected == "enum":
        allowed = set(_text_values(_field(specification, "values", ())))
        return value in allowed
    return False


def _raise_if_invalid(
    report: ToolValidationReport,
    operation: str,
    subject: str | None,
) -> None:
    if report.valid:
        return
    errors = report.errors
    detail = "; ".join(f"{issue.field}: {issue.message}" for issue in errors[:12])
    if len(errors) > 12:
        detail += f"; and {len(errors) - 12} additional error(s)"
    raise ContractViolationError(
        "Diagnostic-tool contract validation failed",
        code="GF-WB-CONTRACT-013",
        detail=detail,
        stage="diagnostics",
        operation=operation,
        subject=subject,
    )


def _validation_code(value: object) -> ToolValidationCode:
    if isinstance(value, ToolValidationCode):
        return value
    if not isinstance(value, str):
        raise TypeError("code must be a ToolValidationCode or string")
    try:
        return ToolValidationCode(value)
    except ValueError as exc:
        raise ValueError("code must be a canonical ToolValidationCode") from exc


def _validation_severity(value: object) -> ToolValidationSeverity:
    if isinstance(value, ToolValidationSeverity):
        return value
    if not isinstance(value, str):
        raise TypeError("severity must be a ToolValidationSeverity or string")
    try:
        return ToolValidationSeverity(value)
    except ValueError as exc:
        raise ValueError("severity must be a canonical ToolValidationSeverity") from exc


def _field(
    obj: ToolObject,
    name: str,
    default: object = _MISSING,
) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _text(value: object) -> str:
    if isinstance(value, StrEnum):
        return value.value
    return value if isinstance(value, str) else ""


def _text_values(values: object) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        return (values,) if values else ()
    if isinstance(values, Mapping):
        values = values.keys()
    if not isinstance(values, Iterable):
        return ()
    iterable: tuple[object, ...] = tuple(values)
    return tuple(text for item in iterable if (text := _text(item)))


def _sequence(
    value: object,
    field: str,
    issues: list[ToolValidationIssue],
    code: ToolValidationCode,
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        issues.append(_error(code, field, f"{field} must be a sequence"))
        return ()
    return tuple(value)


def _strict_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _positive_int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _absolute_path(value: object) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError("path must be a string or path-like value")
    text = os.fspath(value)
    if "\x00" in text:
        raise ValueError("path must not contain NUL characters")
    path = Path(os.path.normpath(text))
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    return path


def _is_within(path: Path, root: Path) -> bool:
    candidate = _absolute_path(path)
    boundary = _absolute_path(root)
    return candidate == boundary or candidate.is_relative_to(boundary)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _version_key(value: str) -> tuple[int, ...]:
    numeric = re.split(r"[-+]", value, maxsplit=1)[0]
    return tuple(int(part) for part in numeric.split("."))


def _normalize_platform(value: str | None) -> str:
    if value is not None:
        normalized = value.casefold()
    elif sys.platform.startswith("win"):
        normalized = "windows"
    elif sys.platform == "darwin":
        normalized = "macos"
    else:
        normalized = "linux"
    aliases = {
        "win32": "windows",
        "windows": "windows",
        "linux": "linux",
        "darwin": "macos",
        "macos": "macos",
    }
    return aliases.get(normalized, normalized)


def _required(field: str) -> ToolValidationIssue:
    return _error(
        ToolValidationCode.REQUIRED_FIELD,
        field,
        f"{field} is required",
    )


def _error(
    code: ToolValidationCode,
    field: str,
    message: str,
) -> ToolValidationIssue:
    return ToolValidationIssue(
        code=code,
        severity=ToolValidationSeverity.ERROR,
        field=field,
        message=message,
    )


def _issue_key(
    issue: ToolValidationIssue,
) -> tuple[int, str, str, str]:
    return (
        0 if issue.severity is ToolValidationSeverity.ERROR else 1,
        issue.field,
        issue.code.value,
        issue.message,
    )
