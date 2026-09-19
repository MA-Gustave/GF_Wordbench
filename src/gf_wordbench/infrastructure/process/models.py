"""Immutable process-boundary models for GF Wordbench.

The process layer records generic execution facts only. Validation status,
diagnostic classification, GF command semantics, and report serialization
remain owned by their dedicated modules.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
import math
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, TypeVar

from gf_wordbench.kernel.statuses import ExecutionState

__all__ = (
    "ArtifactExpectation",
    "ArtifactKind",
    "ArtifactObservation",
    "CancellationReason",
    "ProcessErrorKind",
    "ProcessEvent",
    "ProcessEventSink",
    "ProcessInput",
    "ProcessInputKind",
    "ProcessOperationKind",
    "ProcessRequest",
    "ProcessResult",
    "StringMap",
)

StringMap: TypeAlias = Mapping[str, str]
_EventDetails: TypeAlias = Mapping[str, object]

_EnumT = TypeVar("_EnumT", bound=StrEnum)

_EMPTY_STRING_MAP: Final[StringMap] = MappingProxyType({})
_EMPTY_EVENT_DETAILS: Final[_EventDetails] = MappingProxyType({})


@unique
class ProcessOperationKind(StrEnum):
    """Canonical categories of external-process operations."""

    VERSION_PROBE = "version_probe"
    COMPILE = "compile"
    PGF_BUILD = "pgf_build"
    SCENARIO = "scenario"
    GENERATION = "generation"
    INTROSPECTION = "introspection"
    OPTIONAL_TOOL = "optional_tool"


@unique
class ProcessInputKind(StrEnum):
    """Supported standard-input modes."""

    NONE = "none"
    TEXT = "text"
    FILE = "file"


@unique
class ArtifactKind(StrEnum):
    """Filesystem kinds that a process request may expect."""

    FILE = "file"
    DIRECTORY = "directory"


@unique
class CancellationReason(StrEnum):
    """Canonical controller reasons for cancelling a process request."""

    USER = "user"
    APPLICATION_SHUTDOWN = "application_shutdown"
    OUTPUT_LIMIT = "output_limit"
    CONTROLLER_POLICY = "controller_policy"


@unique
class ProcessErrorKind(StrEnum):
    """Technical process-layer error vocabulary."""

    OK = "OK"
    LAUNCH = "LAUNCH"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    OUTPUT_LIMIT = "OUTPUT_LIMIT"
    IO = "IO"
    ENCODING = "ENCODING"
    CONTAINMENT = "CONTAINMENT"
    CONTRACT = "CONTRACT"
    OTHER = "OTHER"


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or "\x00" in value:
        raise ValueError(f"{field_name} must be non-empty and contain no NUL")
    return value


def _frozen_string_map(
    values: Mapping[str, str] | None,
    *,
    field_name: str,
) -> StringMap:
    if not values:
        return _EMPTY_STRING_MAP
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    copied = dict(values)
    for key, value in copied.items():
        _non_empty(key, f"{field_name} key")
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError(f"{field_name}[{key!r}] must be a NUL-free string")
    return MappingProxyType(copied)


def _frozen_details(
    values: Mapping[str, object] | None,
) -> _EventDetails:
    if not values:
        return _EMPTY_EVENT_DETAILS
    if not isinstance(values, Mapping):
        raise TypeError("details must be a mapping")

    copied = dict(values)
    for key in copied:
        _non_empty(key, "details key")
    return MappingProxyType(copied)


def _frozen_strings(
    values: Collection[str],
    field_name: str,
) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be a collection of strings")

    result = frozenset(values)
    for value in result:
        _non_empty(value, field_name)
    return result


def _frozen_indexes(
    values: Collection[int],
) -> frozenset[int]:
    if isinstance(values, (str, bytes)):
        raise TypeError("sensitive_arg_indexes must be a collection of integers")

    result = frozenset(values)
    if any(isinstance(index, bool) or not isinstance(index, int) or index < 0 for index in result):
        raise ValueError("sensitive_arg_indexes must contain non-negative integers")
    return result


def _string_tuple(values: object, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"{field_name}[{index}] must be a string")
        if "\x00" in value:
            raise ValueError(f"{field_name}[{index}] must not contain NUL")
        result.append(value)
    return tuple(result)


def _optional_enum(
    value: object,
    enum_type: type[_EnumT],
    field_name: str,
) -> _EnumT | None:
    if value is None:
        return None
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be {enum_type.__name__}, string, or None")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc


def _paths(
    values: Iterable[Path],
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError(f"{field_name} must be an iterable of paths")
    return tuple(Path(value) for value in values)


def _finite(
    value: float,
    field_name: str,
    *,
    allow_zero: bool,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{field_name} must be a number")

    result = float(value)
    if not math.isfinite(result) or result < 0 or (result == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field_name} must be finite and {qualifier}")
    return result


def _utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ProcessInput:
    """Explicit standard input for one process request."""

    kind: ProcessInputKind = ProcessInputKind.NONE
    text: str | None = None
    path: Path | None = None
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProcessInputKind):
            raise TypeError("kind must be a ProcessInputKind")
        _non_empty(self.encoding, "encoding")

        if self.kind is ProcessInputKind.NONE:
            if self.text is not None or self.path is not None:
                raise ValueError("none input cannot contain text or a path")

        elif self.kind is ProcessInputKind.TEXT:
            if not isinstance(self.text, str) or self.path is not None:
                raise ValueError("text input requires text and forbids a path")

        else:
            if self.text is not None or self.path is None:
                raise ValueError("file input requires a path and forbids text")
            object.__setattr__(
                self,
                "path",
                Path(self.path),
            )

    @classmethod
    def none(cls) -> ProcessInput:
        return cls()

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> ProcessInput:
        return cls(
            kind=ProcessInputKind.TEXT,
            text=text,
            encoding=encoding,
        )

    @classmethod
    def from_file(
        cls,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> ProcessInput:
        return cls(
            kind=ProcessInputKind.FILE,
            path=path,
            encoding=encoding,
        )


@dataclass(frozen=True, slots=True)
class ArtifactExpectation:
    """Generic filesystem artifact expected after process execution."""

    path: Path
    role: str
    required: bool
    kind: ArtifactKind
    minimum_size_bytes: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "path",
            Path(self.path),
        )
        _non_empty(self.role, "role")

        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")
        if not isinstance(self.kind, ArtifactKind):
            raise TypeError("kind must be an ArtifactKind")
        if (
            isinstance(self.minimum_size_bytes, bool)
            or not isinstance(self.minimum_size_bytes, int)
            or self.minimum_size_bytes < 0
        ):
            raise ValueError("minimum_size_bytes must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ArtifactObservation:
    """Generic filesystem facts observed after process execution."""

    path: Path
    role: str
    required: bool
    exists: bool
    kind_matches: bool
    size_bytes: int | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "path",
            Path(self.path),
        )
        _non_empty(self.role, "role")

        if not all(
            isinstance(value, bool)
            for value in (
                self.required,
                self.exists,
                self.kind_matches,
            )
        ):
            raise TypeError("required, exists, and kind_matches must be bools")

        if self.size_bytes is not None and (
            isinstance(self.size_bytes, bool)
            or not isinstance(self.size_bytes, int)
            or self.size_bytes < 0
        ):
            raise ValueError("size_bytes must be a non-negative integer or None")

        if not self.exists and (self.kind_matches or self.size_bytes is not None):
            raise ValueError("a missing artifact cannot match its kind or report a size")


@dataclass(frozen=True, slots=True)
class ProcessRequest:
    """Structured, shell-free request for one external-process attempt.

    The model owns immutable request data only. Filesystem containment,
    executable availability, capture-path safety, and registered policy
    validation remain owned by :mod:`process.requests`.
    """

    request_id: str
    tool_id: str
    operation_id: str
    operation_kind: ProcessOperationKind
    executable: Path
    args: tuple[str, ...]
    cwd: Path
    stdout_path: Path
    stderr_path: Path
    timeout_sec: float
    approved_read_roots: tuple[Path, ...]
    approved_write_roots: tuple[Path, ...]
    evidence_policy: str
    stdin: ProcessInput = field(default_factory=ProcessInput.none)
    environment_policy: str = "controlled-inherit-v1"
    env_overrides: StringMap = field(default_factory=dict)
    env_removals: frozenset[str] = field(default_factory=frozenset)
    sensitive_env_keys: frozenset[str] = field(default_factory=frozenset)
    sensitive_arg_indexes: frozenset[int] = field(default_factory=frozenset)
    termination_grace_sec: float = 5.0
    output_limit_bytes: int = 8 * 1024 * 1024
    expected_artifacts: tuple[
        ArtifactExpectation,
        ...,
    ] = ()
    metadata: StringMap = field(default_factory=dict)
    mutability_class: str = "read_only"
    network_policy: str = "denied"

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "tool_id",
            "operation_id",
            "environment_policy",
            "evidence_policy",
            "mutability_class",
            "network_policy",
        ):
            _non_empty(
                getattr(self, name),
                name,
            )

        if not isinstance(
            self.operation_kind,
            ProcessOperationKind,
        ):
            raise TypeError("operation_kind must be a ProcessOperationKind")
        if not isinstance(self.stdin, ProcessInput):
            raise TypeError("stdin must be a ProcessInput")
        args = _string_tuple(self.args, "args")

        object.__setattr__(
            self,
            "executable",
            Path(self.executable),
        )
        object.__setattr__(
            self,
            "args",
            args,
        )
        object.__setattr__(
            self,
            "cwd",
            Path(self.cwd),
        )
        object.__setattr__(
            self,
            "stdout_path",
            Path(self.stdout_path),
        )
        object.__setattr__(
            self,
            "stderr_path",
            Path(self.stderr_path),
        )
        object.__setattr__(
            self,
            "approved_read_roots",
            _paths(
                self.approved_read_roots,
                "approved_read_roots",
            ),
        )
        object.__setattr__(
            self,
            "approved_write_roots",
            _paths(
                self.approved_write_roots,
                "approved_write_roots",
            ),
        )
        object.__setattr__(
            self,
            "timeout_sec",
            _finite(
                self.timeout_sec,
                "timeout_sec",
                allow_zero=False,
            ),
        )
        object.__setattr__(
            self,
            "termination_grace_sec",
            _finite(
                self.termination_grace_sec,
                "termination_grace_sec",
                allow_zero=True,
            ),
        )

        for index, argument in enumerate(self.args):
            if not isinstance(argument, str) or "\x00" in argument:
                raise ValueError(f"args[{index}] must be a NUL-free string")

        if self.stdout_path == self.stderr_path:
            raise ValueError("stdout_path and stderr_path must be distinct")

        if (
            isinstance(self.output_limit_bytes, bool)
            or not isinstance(self.output_limit_bytes, int)
            or self.output_limit_bytes <= 0
        ):
            raise ValueError("output_limit_bytes must be a positive integer")

        object.__setattr__(
            self,
            "env_overrides",
            _frozen_string_map(
                self.env_overrides,
                field_name="env_overrides",
            ),
        )
        object.__setattr__(
            self,
            "env_removals",
            _frozen_strings(
                self.env_removals,
                "env_removals",
            ),
        )
        object.__setattr__(
            self,
            "sensitive_env_keys",
            _frozen_strings(
                self.sensitive_env_keys,
                "sensitive_env_keys",
            ),
        )
        object.__setattr__(
            self,
            "sensitive_arg_indexes",
            _frozen_indexes(self.sensitive_arg_indexes),
        )

        artifacts = tuple(self.expected_artifacts)
        if not all(isinstance(item, ArtifactExpectation) for item in artifacts):
            raise TypeError("expected_artifacts must contain ArtifactExpectation values")
        object.__setattr__(
            self,
            "expected_artifacts",
            artifacts,
        )
        object.__setattr__(
            self,
            "metadata",
            _frozen_string_map(
                self.metadata,
                field_name="metadata",
            ),
        )

    @property
    def command(self) -> tuple[str, ...]:
        """Return the executable-and-argument vector."""

        return (
            str(self.executable),
            *self.args,
        )

    @property
    def working_directory(self) -> Path:
        """Return the explicit process working directory."""

        return self.cwd


@dataclass(frozen=True, slots=True)
class ProcessEvent:
    """Immutable generic event emitted by the process runner."""

    name: str
    operation_id: str
    operation_kind: ProcessOperationKind
    occurred_at: datetime
    pid: int | None = None
    execution_state: ExecutionState | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty(self.name, "name")
        _non_empty(
            self.operation_id,
            "operation_id",
        )

        if not isinstance(
            self.operation_kind,
            ProcessOperationKind,
        ):
            raise TypeError("operation_kind must be a ProcessOperationKind")

        if self.pid is not None and (
            isinstance(self.pid, bool) or not isinstance(self.pid, int) or self.pid <= 0
        ):
            raise ValueError("pid must be a positive integer or None")

        if self.execution_state is not None and not isinstance(
            self.execution_state,
            ExecutionState,
        ):
            raise TypeError("execution_state must be an ExecutionState or None")

        object.__setattr__(
            self,
            "occurred_at",
            _utc(
                self.occurred_at,
                "occurred_at",
            ),
        )
        object.__setattr__(
            self,
            "details",
            _frozen_details(self.details),
        )


class ProcessEventSink(Protocol):
    """Generic, UI-independent consumer of process events."""

    def emit(
        self,
        event: ProcessEvent,
        /,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """Immutable facts from one finalized external-process attempt."""

    operation_id: str
    operation_kind: ProcessOperationKind
    executable: Path
    args: tuple[str, ...]
    cwd: Path
    execution_state: ExecutionState
    exit_code: int | None
    pid: int | None
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    cancellation_reason: CancellationReason | None
    launch_error_kind: ProcessErrorKind | None
    launch_error_message: str
    termination_attempted: bool
    termination_succeeded: bool
    stdout_path: Path
    stderr_path: Path
    stdout_size_bytes: int
    stderr_size_bytes: int
    output_limit_exceeded: bool
    capture_complete: bool
    environment_policy: str
    recorded_env_overrides: StringMap = field(default_factory=dict)
    artifact_observations: tuple[
        ArtifactObservation,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        _non_empty(
            self.operation_id,
            "operation_id",
        )
        _non_empty(
            self.environment_policy,
            "environment_policy",
        )

        if not isinstance(self.launch_error_message, str) or "\x00" in self.launch_error_message:
            raise ValueError("launch_error_message must be a NUL-free string")

        if not isinstance(
            self.operation_kind,
            ProcessOperationKind,
        ):
            raise TypeError("operation_kind must be a ProcessOperationKind")
        if not isinstance(
            self.execution_state,
            ExecutionState,
        ):
            raise TypeError("execution_state must be an ExecutionState")
        args = _string_tuple(self.args, "args")

        object.__setattr__(
            self,
            "executable",
            Path(self.executable),
        )
        object.__setattr__(
            self,
            "args",
            args,
        )
        object.__setattr__(
            self,
            "cwd",
            Path(self.cwd),
        )
        object.__setattr__(
            self,
            "stdout_path",
            Path(self.stdout_path),
        )
        object.__setattr__(
            self,
            "stderr_path",
            Path(self.stderr_path),
        )
        object.__setattr__(
            self,
            "started_at",
            _utc(
                self.started_at,
                "started_at",
            ),
        )
        object.__setattr__(
            self,
            "finished_at",
            _utc(
                self.finished_at,
                "finished_at",
            ),
        )

        for index, argument in enumerate(self.args):
            if not isinstance(argument, str) or "\x00" in argument:
                raise ValueError(f"args[{index}] must be a NUL-free string")

        object.__setattr__(
            self,
            "cancellation_reason",
            _optional_enum(
                self.cancellation_reason,
                CancellationReason,
                "cancellation_reason",
            ),
        )
        object.__setattr__(
            self,
            "launch_error_kind",
            _optional_enum(
                self.launch_error_kind,
                ProcessErrorKind,
                "launch_error_kind",
            ),
        )

        object.__setattr__(
            self,
            "recorded_env_overrides",
            _frozen_string_map(
                self.recorded_env_overrides,
                field_name="recorded_env_overrides",
            ),
        )

        observations = tuple(self.artifact_observations)
        if not all(isinstance(item, ArtifactObservation) for item in observations):
            raise TypeError("artifact_observations must contain ArtifactObservation values")
        object.__setattr__(
            self,
            "artifact_observations",
            observations,
        )

        self._validate_common_facts()
        self._validate_terminal_state()

    def _validate_common_facts(self) -> None:
        if self.exit_code is not None and (
            isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)
        ):
            raise TypeError("exit_code must be an integer or None")

        if self.pid is not None and (
            isinstance(self.pid, bool) or not isinstance(self.pid, int) or self.pid <= 0
        ):
            raise ValueError("pid must be a positive integer or None")

        for name in (
            "duration_ms",
            "stdout_size_bytes",
            "stderr_size_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        for name in (
            "termination_attempted",
            "termination_succeeded",
            "output_limit_exceeded",
            "capture_complete",
        ):
            if not isinstance(
                getattr(self, name),
                bool,
            ):
                raise TypeError(f"{name} must be a bool")

        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")

        if self.stdout_path == self.stderr_path:
            raise ValueError("stdout_path and stderr_path must be distinct")

        if self.termination_succeeded and not self.termination_attempted:
            raise ValueError("termination_succeeded requires termination_attempted")

        if self.termination_attempted and self.pid is None:
            raise ValueError("termination_attempted requires a launched process")

    def _validate_terminal_state(self) -> None:
        state = self.execution_state

        if state is ExecutionState.LAUNCH_FAILED:
            if self.pid is not None or self.exit_code is not None:
                raise ValueError("launch_failed cannot have a pid or an exit code")

            if self.launch_error_kind in (
                None,
                ProcessErrorKind.OK,
            ):
                raise ValueError("launch_failed requires a non-OK launch_error_kind")

            if not self.launch_error_message:
                raise ValueError("launch_failed requires a launch_error_message")

            if self.cancellation_reason is not None:
                raise ValueError("launch_failed cannot have a cancellation reason")
            return

        if self.launch_error_kind is not None or self.launch_error_message:
            raise ValueError("launch error fields are reserved for launch_failed")

        if state is ExecutionState.COMPLETED:
            if self.pid is None or self.exit_code is None:
                raise ValueError("completed requires a pid and exit_code")

            if self.cancellation_reason is not None:
                raise ValueError("completed cannot have a cancellation reason")

            if self.termination_attempted or self.output_limit_exceeded:
                raise ValueError("completed cannot report termination or output exhaustion")
            return

        if state is ExecutionState.TIMED_OUT:
            if self.pid is None or not self.termination_attempted:
                raise ValueError("timed_out requires a pid and termination attempt")

            if self.cancellation_reason is not None:
                raise ValueError("timed_out is distinct from cancellation")

            if self.output_limit_exceeded:
                raise ValueError("timed_out cannot also be output-limit cancellation")
            return

        if state is ExecutionState.CANCELLED:
            if self.cancellation_reason is None:
                raise ValueError("cancelled requires a cancellation reason")

            if self.pid is not None and not self.termination_attempted:
                raise ValueError("a launched cancelled process requires termination")

            if self.output_limit_exceeded != (
                self.cancellation_reason is CancellationReason.OUTPUT_LIMIT
            ):
                raise ValueError("output_limit_exceeded and reason output_limit must agree")
            return

        raise ValueError(f"unsupported execution state: {state!r}")

    @property
    def command(self) -> tuple[str, ...]:
        """Return the executable-and-argument vector."""

        return (
            str(self.executable),
            *self.args,
        )

    @property
    def working_directory(self) -> Path:
        """Return the explicit process working directory."""

        return self.cwd

    @property
    def timed_out(self) -> bool:
        """Whether execution timed out."""

        return self.execution_state is ExecutionState.TIMED_OUT

    @property
    def cancelled(self) -> bool:
        """Whether execution was cancelled."""

        return self.execution_state is ExecutionState.CANCELLED

    @property
    def launch_error(self) -> str:
        """Return the sanitized launch-error message."""

        return self.launch_error_message

    @property
    def total_output_size_bytes(self) -> int:
        """Return combined retained output size."""

        return self.stdout_size_bytes + self.stderr_size_bytes
