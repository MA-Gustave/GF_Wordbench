"""Structured errors and the canonical GF Wordbench exception hierarchy.

This module is deliberately independent of entrypoints, adapters, persistence,
and report rendering. Expected tool outcomes are represented by stage results;
these exceptions are reserved for invalid requests, contract violations, and
conditions that prevent construction of a reliable result.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
from typing import Final

from .statuses import ErrorKind

__all__ = (
    "ArtifactError",
    "CancellationRequested",
    "CompileExecutionError",
    "ConfigurationError",
    "ContractViolationError",
    "ErrorInfo",
    "EvidenceIOError",
    "GFWordbenchError",
    "InfrastructureError",
    "MigrationError",
    "NormalizationError",
    "PathSecurityError",
    "ProcessLaunchError",
    "ProjectConfigurationError",
    "ReportError",
    "ScanExecutionError",
    "ScenarioExecutionError",
    "SchemaValidationError",
    "StageExecutionError",
    "StateWriteError",
    "UnsupportedVersionError",
)

_ERROR_CODE_DOMAINS: Final[frozenset[str]] = frozenset(
    {
        "CONFIG",
        "PROJECT",
        "PATH",
        "IO",
        "PROCESS",
        "GF",
        "SCAN",
        "SCENARIO",
        "GOLD",
        "SCHEMA",
        "REPORT",
        "MANIFEST",
        "STATE",
        "MIGRATION",
        "CONTRACT",
        "INTERNAL",
    }
)

_ERROR_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"GF-WB-(?P<domain>[A-Z]+)-(?P<number>[0-9]{3})"
)


def _validate_text(name: str, value: str, *, required: bool) -> str:
    """Validate a textual field without modifying its supplied value."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL characters")
    if required and not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _validate_optional_text(name: str, value: str | None) -> str | None:
    """Validate an optional non-empty textual field."""

    if value is None:
        return None
    return _validate_text(name, value, required=True)


def _validate_error_code(code: str) -> str:
    """Validate and return a canonical GF Wordbench error code."""

    code = _validate_text("code", code, required=True)
    match = _ERROR_CODE_PATTERN.fullmatch(code)

    if match is None:
        raise ValueError("code must use the canonical form GF-WB-<DOMAIN>-<NNN>")

    domain = match.group("domain")
    if domain not in _ERROR_CODE_DOMAINS:
        raise ValueError(f"unsupported GF Wordbench error-code domain: {domain}")

    return code


def _validate_retryable(value: bool) -> bool:
    """Validate the retryability flag without accepting integer substitutes."""

    if type(value) is not bool:
        raise TypeError("retryable must be a bool")
    return value


def _normalize_evidence_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Validate evidence paths and return their stable immutable form."""

    if isinstance(paths, (str, bytes)):
        raise TypeError("evidence_paths must be an iterable of path strings")

    try:
        normalized = tuple(paths)
    except TypeError as exc:
        raise TypeError("evidence_paths must be an iterable of path strings") from exc

    for index, path in enumerate(normalized):
        _validate_text(f"evidence_paths[{index}]", path, required=True)

    return normalized


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """Stable structured error envelope for stage and run results."""

    code: str
    error_kind: ErrorKind
    message: str
    detail: str
    stage: str
    operation: str
    subject: str | None
    retryable: bool
    evidence_paths: tuple[str, ...]
    cause_type: str | None

    def __post_init__(self) -> None:
        _validate_error_code(self.code)

        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be an ErrorKind")

        _validate_text("message", self.message, required=True)
        _validate_text("detail", self.detail, required=False)
        _validate_text("stage", self.stage, required=True)
        _validate_text("operation", self.operation, required=True)
        _validate_optional_text("subject", self.subject)
        _validate_retryable(self.retryable)
        _validate_optional_text("cause_type", self.cause_type)

        object.__setattr__(
            self,
            "evidence_paths",
            _normalize_evidence_paths(self.evidence_paths),
        )


class GFWordbenchError(Exception):
    """Base class for controlled GF Wordbench exceptions.

    The original exception should be preserved with ``raise ... from exc``.
    Stage owners convert expected operational exceptions into structured
    results; this class only carries bounded context needed for that conversion.
    """

    message: str
    code: str | None
    detail: str
    stage: str | None
    operation: str | None
    subject: str | None
    retryable: bool
    evidence_paths: tuple[str, ...]

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        detail: str = "",
        stage: str | None = None,
        operation: str | None = None,
        subject: str | None = None,
        retryable: bool = False,
        evidence_paths: Iterable[str] = (),
    ) -> None:
        self.message = _validate_text("message", message, required=True)
        self.code = None if code is None else _validate_error_code(code)
        self.detail = _validate_text("detail", detail, required=False)
        self.stage = _validate_optional_text("stage", stage)
        self.operation = _validate_optional_text("operation", operation)
        self.subject = _validate_optional_text("subject", subject)
        self.retryable = _validate_retryable(retryable)
        self.evidence_paths = _normalize_evidence_paths(evidence_paths)

        super().__init__(self.message)


class ConfigurationError(GFWordbenchError):
    """Resolved application configuration is invalid or unusable."""


class ProjectConfigurationError(ConfigurationError):
    """The active project's configuration is invalid or inconsistent."""


class UnsupportedVersionError(ConfigurationError):
    """A required schema, application, or external-tool version is unsupported."""


class SchemaValidationError(ConfigurationError):
    """Structured input does not satisfy its owned schema contract."""


class ContractViolationError(GFWordbenchError):
    """A caller or component violated a documented boundary contract."""


class InfrastructureError(GFWordbenchError):
    """A required infrastructure mechanism could not perform its operation."""


class PathSecurityError(InfrastructureError):
    """A path violates containment, ownership, or write-root policy."""


class EvidenceIOError(InfrastructureError):
    """Required evidence could not be read, decoded, preserved, or written."""


class ProcessLaunchError(InfrastructureError):
    """An external process could not be started reliably."""


class StateWriteError(InfrastructureError):
    """A reliable application-state file could not be published or removed."""


class StageExecutionError(GFWordbenchError):
    """A validation stage could not construct a reliable structured result."""


class ScanExecutionError(StageExecutionError):
    """Static scanning could not complete or preserve required evidence."""


class CompileExecutionError(StageExecutionError):
    """Compilation could not complete or preserve required evidence."""


class ScenarioExecutionError(StageExecutionError):
    """Scenario execution could not complete or preserve required evidence."""


class NormalizationError(StageExecutionError):
    """Scenario or diagnostic evidence could not be normalized reliably."""


class ArtifactError(GFWordbenchError):
    """A required artifact is missing, invalid, unsafe, or unverifiable."""


class ReportError(GFWordbenchError):
    """A required report could not be rendered, validated, or published."""


class MigrationError(GFWordbenchError):
    """A versioned migration could not preserve required meaning or integrity."""


class CancellationRequested(GFWordbenchError):
    """Controlled cancellation was observed before normal completion."""
