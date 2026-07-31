"""Authoritative process-state diagnostic patterns."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
import math
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.infrastructure.process.models import (
    CancellationReason,
    ProcessErrorKind,
    ProcessResult,
)
from gf_wordbench.kernel.statuses import ErrorKind, ExecutionState

ProcessMetadataValue: TypeAlias = str | int | bool | float | None
ProcessMetadata: TypeAlias = Mapping[str, ProcessMetadataValue]

_EMPTY_METADATA: Final[ProcessMetadata] = MappingProxyType({})
_MAX_DETAIL_LENGTH: Final[int] = 4_000

def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _optional_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _bounded_optional_text(
    value: object,
    field_name: str,
) -> str:
    text = _optional_text(value, field_name)
    if len(text) > _MAX_DETAIL_LENGTH:
        return text[: _MAX_DETAIL_LENGTH - 1] + "…"
    return text


def _optional_positive_number(
    value: object,
    field_name: str,
) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number or None")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return result


def _optional_positive_int(
    value: object,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer or None")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _boolean(value: bool) -> str:
    return "true" if value else "false"


@unique
class ProcessPatternId(StrEnum):
    TIMEOUT = "DP-PROC-001"
    LAUNCH_FAILURE = "DP-PROC-002"
    CANCELLATION = "DP-PROC-003"
    OUTPUT_LIMIT = "DP-PROC-004"
    DECODING_FAILURE = "DP-PROC-005"


@unique
class ProcessPatternSeverity(StrEnum):
    ERROR = "error"
    FATAL = "fatal"


@unique
class ProcessPatternConfidence(StrEnum):
    AUTHORITATIVE = "authoritative"


@unique
class LaunchFailureKind(StrEnum):
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    INVALID_EXECUTABLE = "invalid_executable"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    PLATFORM_ERROR = "platform_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProcessPatternSpec:
    pattern_id: ProcessPatternId
    title: str
    error_kind: ErrorKind
    severity: ProcessPatternSeverity
    message: str
    precedence: int

    def __post_init__(self) -> None:
        if not isinstance(self.pattern_id, ProcessPatternId):
            raise TypeError("pattern_id must be ProcessPatternId")
        object.__setattr__(self, "title", _text(self.title, "title"))
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be ErrorKind")
        if not isinstance(self.severity, ProcessPatternSeverity):
            raise TypeError("severity must be ProcessPatternSeverity")
        object.__setattr__(self, "message", _text(self.message, "message"))
        if type(self.precedence) is not int or self.precedence < 0:
            raise ValueError("precedence must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ProcessPatternContext:
    result: ProcessResult
    timeout_seconds: float | None = None
    output_limit_bytes: int | None = None
    launch_failure_kind: LaunchFailureKind = LaunchFailureKind.UNKNOWN
    decoding_failed: bool = False
    decoding_lossy: bool = False
    decoding_error: str = ""
    raw_byte_paths: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.result, ProcessResult):
            raise TypeError("result must be ProcessResult")
        timeout_seconds = _optional_positive_number(
            self.timeout_seconds,
            "timeout_seconds",
        )
        output_limit_bytes = _optional_positive_int(
            self.output_limit_bytes,
            "output_limit_bytes",
        )
        if not isinstance(self.launch_failure_kind, LaunchFailureKind):
            raise TypeError(
                "launch_failure_kind must be LaunchFailureKind"
            )
        if type(self.decoding_failed) is not bool:
            raise TypeError("decoding_failed must be a boolean")
        if type(self.decoding_lossy) is not bool:
            raise TypeError("decoding_lossy must be a boolean")
        decoding_error = _optional_text(
            self.decoding_error,
            "decoding_error",
        )
        raw_byte_paths = _paths(self.raw_byte_paths, "raw_byte_paths")

        if (
            self.result.execution_state is ExecutionState.TIMED_OUT
            and timeout_seconds is None
        ):
            raise ValueError(
                "timeout_seconds is required for timed-out process evidence"
            )
        if self.result.output_limit_exceeded and output_limit_bytes is None:
            raise ValueError(
                "output_limit_bytes is required when the limit was exceeded"
            )
        if self.decoding_failed and not decoding_error:
            raise ValueError(
                "decoding_error is required when decoding_failed is true"
            )
        if not self.decoding_failed and decoding_error:
            raise ValueError(
                "decoding_error is reserved for decoding failure"
            )

        object.__setattr__(self, "timeout_seconds", timeout_seconds)
        object.__setattr__(self, "output_limit_bytes", output_limit_bytes)
        object.__setattr__(self, "decoding_error", decoding_error)
        object.__setattr__(self, "raw_byte_paths", raw_byte_paths)


@dataclass(frozen=True, slots=True)
class ProcessPatternMatch:
    pattern_id: ProcessPatternId
    error_kind: ErrorKind
    severity: ProcessPatternSeverity
    confidence: ProcessPatternConfidence
    message: str
    detail: str
    operation_id: str
    evidence_paths: tuple[Path, ...]
    metadata: ProcessMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.pattern_id, ProcessPatternId):
            raise TypeError("pattern_id must be ProcessPatternId")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be ErrorKind")
        if not isinstance(self.severity, ProcessPatternSeverity):
            raise TypeError("severity must be ProcessPatternSeverity")
        if not isinstance(self.confidence, ProcessPatternConfidence):
            raise TypeError(
                "confidence must be ProcessPatternConfidence"
            )
        object.__setattr__(self, "message", _text(self.message, "message"))
        object.__setattr__(
            self,
            "detail",
            _bounded_optional_text(self.detail, "detail"),
        )
        object.__setattr__(
            self,
            "operation_id",
            _text(self.operation_id, "operation_id"),
        )
        object.__setattr__(
            self,
            "evidence_paths",
            _paths(self.evidence_paths, "evidence_paths"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_metadata(self.metadata),
        )

# ``ErrorKind`` is the canonical coarse technical category. Process-specific
# meanings such as cancellation and output-limit exhaustion remain represented
# by ``ProcessPatternId`` and structured metadata rather than duplicate enum
# members.


TIMEOUT_PATTERN: Final = ProcessPatternSpec(
    pattern_id=ProcessPatternId.TIMEOUT,
    title="Process timeout",
    error_kind=ErrorKind.TIMEOUT,
    severity=ProcessPatternSeverity.FATAL,
    message="External process timed out.",
    precedence=10,
)

LAUNCH_FAILURE_PATTERN: Final = ProcessPatternSpec(
    pattern_id=ProcessPatternId.LAUNCH_FAILURE,
    title="Process launch failure",
    error_kind=ErrorKind.TOOL,
    severity=ProcessPatternSeverity.FATAL,
    message="External process could not be started.",
    precedence=20,
)

OUTPUT_LIMIT_PATTERN: Final = ProcessPatternSpec(
    pattern_id=ProcessPatternId.OUTPUT_LIMIT,
    title="Output limit exceeded",
    error_kind=ErrorKind.IO,
    severity=ProcessPatternSeverity.ERROR,
    message="External process exceeded its output limit.",
    precedence=30,
)

CANCELLATION_PATTERN: Final = ProcessPatternSpec(
    pattern_id=ProcessPatternId.CANCELLATION,
    title="Process cancellation",
    error_kind=ErrorKind.OTHER,
    severity=ProcessPatternSeverity.ERROR,
    message="External process was cancelled.",
    precedence=40,
)

DECODING_FAILURE_PATTERN: Final = ProcessPatternSpec(
    pattern_id=ProcessPatternId.DECODING_FAILURE,
    title="Output decoding failure",
    error_kind=ErrorKind.IO,
    severity=ProcessPatternSeverity.ERROR,
    message="External process output could not be decoded reliably.",
    precedence=50,
)

PROCESS_PATTERNS: Final[tuple[ProcessPatternSpec, ...]] = (
    TIMEOUT_PATTERN,
    LAUNCH_FAILURE_PATTERN,
    OUTPUT_LIMIT_PATTERN,
    CANCELLATION_PATTERN,
    DECODING_FAILURE_PATTERN,
)


def match_process_patterns(
    context: ProcessPatternContext,
) -> tuple[ProcessPatternMatch, ...]:
    if not isinstance(context, ProcessPatternContext):
        raise TypeError("context must be ProcessPatternContext")

    matches: list[ProcessPatternMatch] = []
    result = context.result

    if result.execution_state is ExecutionState.TIMED_OUT:
        matches.append(_timeout_match(context))

    if result.execution_state is ExecutionState.LAUNCH_FAILED:
        matches.append(_launch_failure_match(context))

    if result.output_limit_exceeded:
        matches.append(_output_limit_match(context))

    if result.execution_state is ExecutionState.CANCELLED:
        matches.append(_cancellation_match(context))

    if context.decoding_failed:
        matches.append(_decoding_failure_match(context))

    order = {
        spec.pattern_id: spec.precedence
        for spec in PROCESS_PATTERNS
    }
    return tuple(
        sorted(
            matches,
            key=lambda item: (
                order[item.pattern_id],
                item.pattern_id.value,
            ),
        )
    )


def primary_process_pattern(
    context: ProcessPatternContext,
) -> ProcessPatternMatch | None:
    matches = match_process_patterns(context)
    return matches[0] if matches else None


def process_pattern_by_id(
    pattern_id: ProcessPatternId | str,
) -> ProcessPatternSpec:
    canonical = ProcessPatternId(pattern_id)
    for spec in PROCESS_PATTERNS:
        if spec.pattern_id is canonical:
            return spec
    raise KeyError(canonical.value)


def _timeout_match(
    context: ProcessPatternContext,
) -> ProcessPatternMatch:
    result = context.result
    detail = (
        f"Timeout: {context.timeout_seconds:g} seconds; "
        f"duration: {result.duration_ms} ms; "
        f"termination attempted: {_boolean(result.termination_attempted)}; "
        f"termination succeeded: {_boolean(result.termination_succeeded)}."
    )
    return _match(
        TIMEOUT_PATTERN,
        context,
        detail=detail,
        metadata={
            "timeout_seconds": context.timeout_seconds,
            "duration_ms": result.duration_ms,
            "termination_attempted": result.termination_attempted,
            "termination_succeeded": result.termination_succeeded,
            "capture_complete": result.capture_complete,
        },
    )


def _launch_failure_match(
    context: ProcessPatternContext,
) -> ProcessPatternMatch:
    result = context.result
    launch_kind = (
        result.launch_error_kind.value
        if isinstance(result.launch_error_kind, ProcessErrorKind)
        else None
    )
    detail_parts = [
        f"Executable: {result.executable}",
        f"working directory: {result.cwd}",
        f"subkind: {context.launch_failure_kind.value}",
    ]
    if result.launch_error_message:
        detail_parts.append(
            f"runner detail: {result.launch_error_message}"
        )
    return _match(
        LAUNCH_FAILURE_PATTERN,
        context,
        detail="; ".join(detail_parts) + ".",
        metadata={
            "launch_failure_kind": context.launch_failure_kind.value,
            "process_error_kind": launch_kind,
            "exit_code": result.exit_code,
            "pid": result.pid,
        },
    )


def _output_limit_match(
    context: ProcessPatternContext,
) -> ProcessPatternMatch:
    result = context.result
    detail = (
        f"Configured limit: {context.output_limit_bytes} bytes; "
        f"captured stdout: {result.stdout_size_bytes} bytes; "
        f"captured stderr: {result.stderr_size_bytes} bytes; "
        f"capture complete: {_boolean(result.capture_complete)}."
    )
    return _match(
        OUTPUT_LIMIT_PATTERN,
        context,
        detail=detail,
        metadata={
            "output_limit_bytes": context.output_limit_bytes,
            "stdout_size_bytes": result.stdout_size_bytes,
            "stderr_size_bytes": result.stderr_size_bytes,
            "captured_size_bytes": (
                result.stdout_size_bytes + result.stderr_size_bytes
            ),
            "capture_complete": result.capture_complete,
            "cancelled": (
                result.execution_state is ExecutionState.CANCELLED
            ),
        },
    )


def _cancellation_match(
    context: ProcessPatternContext,
) -> ProcessPatternMatch:
    result = context.result
    reason = result.cancellation_reason
    if not isinstance(reason, CancellationReason):
        raise ValueError(
            "cancelled process evidence requires a cancellation reason"
        )
    detail = (
        f"Reason: {reason.value}; "
        f"duration: {result.duration_ms} ms; "
        f"termination attempted: {_boolean(result.termination_attempted)}; "
        f"termination succeeded: {_boolean(result.termination_succeeded)}."
    )
    return _match(
        CANCELLATION_PATTERN,
        context,
        detail=detail,
        metadata={
            "cancellation_reason": reason.value,
            "duration_ms": result.duration_ms,
            "termination_attempted": result.termination_attempted,
            "termination_succeeded": result.termination_succeeded,
            "output_limit_exceeded": result.output_limit_exceeded,
            "capture_complete": result.capture_complete,
        },
    )


def _decoding_failure_match(
    context: ProcessPatternContext,
) -> ProcessPatternMatch:
    result = context.result
    detail = context.decoding_error
    return _match(
        DECODING_FAILURE_PATTERN,
        context,
        detail=detail,
        evidence_paths=(
            context.raw_byte_paths
            if context.raw_byte_paths
            else _result_evidence_paths(result)
        ),
        metadata={
            "decoding_failed": True,
            "decoding_lossy": context.decoding_lossy,
            "capture_complete": result.capture_complete,
        },
    )


def _match(
    spec: ProcessPatternSpec,
    context: ProcessPatternContext,
    *,
    detail: str,
    metadata: ProcessMetadata,
    evidence_paths: tuple[Path, ...] | None = None,
) -> ProcessPatternMatch:
    return ProcessPatternMatch(
        pattern_id=spec.pattern_id,
        error_kind=spec.error_kind,
        severity=spec.severity,
        confidence=ProcessPatternConfidence.AUTHORITATIVE,
        message=spec.message,
        detail=detail,
        operation_id=context.result.operation_id,
        evidence_paths=(
            evidence_paths
            if evidence_paths is not None
            else _result_evidence_paths(context.result)
        ),
        metadata=metadata,
    )


def _result_evidence_paths(
    result: ProcessResult,
) -> tuple[Path, ...]:
    paths = (result.stdout_path, result.stderr_path)
    unique: dict[str, Path] = {}
    for path in paths:
        key = str(path)
        if key not in unique:
            unique[key] = path
    return tuple(unique.values())


def _freeze_metadata(
    values: ProcessMetadata,
) -> ProcessMetadata:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")
    copied: dict[str, ProcessMetadataValue] = {}
    for key, value in values.items():
        key = _text(key, "metadata key")
        if value is not None and type(value) not in (
            str,
            int,
            bool,
            float,
        ):
            raise TypeError(
                f"unsupported metadata value for {key!r}"
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(
                f"metadata value for {key!r} must be finite"
            )
        if isinstance(value, str):
            value = _optional_text(value, f"metadata[{key!r}]")
        copied[key] = value
    return MappingProxyType(copied) if copied else _EMPTY_METADATA


def _paths(
    values: Iterable[Path],
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError(f"{field_name} must be an iterable of Path")
    unique: dict[str, Path] = {}
    for value in values:
        if not isinstance(value, Path):
            raise TypeError(
                f"{field_name} must contain pathlib.Path values"
            )
        if "\x00" in str(value):
            raise ValueError(
                f"{field_name} must not contain NUL paths"
            )
        key = str(value)
        if key not in unique:
            unique[key] = value
    return tuple(unique.values())



__all__ = (
    "CANCELLATION_PATTERN",
    "DECODING_FAILURE_PATTERN",
    "LAUNCH_FAILURE_PATTERN",
    "OUTPUT_LIMIT_PATTERN",
    "PROCESS_PATTERNS",
    "TIMEOUT_PATTERN",
    "LaunchFailureKind",
    "ProcessMetadata",
    "ProcessMetadataValue",
    "ProcessPatternConfidence",
    "ProcessPatternContext",
    "ProcessPatternId",
    "ProcessPatternMatch",
    "ProcessPatternSeverity",
    "ProcessPatternSpec",
    "match_process_patterns",
    "primary_process_pattern",
    "process_pattern_by_id",
)
