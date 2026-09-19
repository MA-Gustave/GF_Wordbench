"""Canonical shared status vocabularies for GF Wordbench.

Each enum is a distinct contract dimension. Persisted writers must serialize the
exact string values defined here and must not substitute values from another
dimension.
"""

from enum import StrEnum, unique

__all__ = (
    "ChangeKind",
    "DiagnosticClass",
    "ErrorKind",
    "ExecutionState",
    "OverallStatus",
    "TargetKind",
    "ValidationMode",
    "ValidationStatus",
)


@unique
class ValidationStatus(StrEnum):
    """Outcome of one requested validation operation or subject."""

    OK = "OK"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@unique
class OverallStatus(StrEnum):
    """Terminal outcome of a complete required run."""

    OK = "OK"
    FAIL = "FAIL"
    ERROR = "ERROR"


@unique
class ExecutionState(StrEnum):
    """Outcome of an attempted external-process execution.

    Models use ``None`` when no external process request was made.
    """

    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    LAUNCH_FAILED = "launch_failed"


@unique
class DiagnosticClass(StrEnum):
    """Causal relationship of a subject to the observed failure set."""

    OK = "ok"
    DIRECT = "direct"
    DOWNSTREAM = "downstream"
    AMBIGUOUS = "ambiguous"
    NOISE = "noise"
    SKIPPED = "skipped"


@unique
class ErrorKind(StrEnum):
    """Immediate technical category of a validation result."""

    OK = "OK"
    OTHER = "OTHER"
    TYPE = "TYPE"
    SYNTAX = "SYNTAX"
    INTERNAL = "INTERNAL"
    TIMEOUT = "TIMEOUT"
    SCRIPT = "SCRIPT"
    CONFIG = "CONFIG"
    IO = "IO"
    TOOL = "TOOL"


@unique
class ChangeKind(StrEnum):
    """Regression relationship between a subject and its baseline."""

    UNCHANGED = "unchanged"
    IMPROVED = "improved"
    REGRESSED = "regressed"
    NEW = "new"
    REMOVED = "removed"


@unique
class ValidationMode(StrEnum):
    """Canonical validation-policy mode selected for a run."""

    QUICK = "quick"
    CHECKPOINT = "checkpoint"
    RELEASE = "release"
    DIAGNOSTIC = "diagnostic"


@unique
class TargetKind(StrEnum):
    """Canonical kind of validation target."""

    FILE = "file"
    MODULE = "module"
    CHECKPOINT = "checkpoint"
    ENTRYPOINT = "entrypoint"
    SCENARIO = "scenario"
    PROJECT = "project"
    REGRESSION = "regression"
