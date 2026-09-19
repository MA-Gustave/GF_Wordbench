"""Prepare and execute one native GF scenario through the shared process boundary."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from types import MappingProxyType
from typing import Final

from gf_wordbench.infrastructure.process import (
    CancellationToken,
    ProcessInput,
    ProcessRequest,
    ProcessResult,
    run_process,
)
from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ProcessEventSink,
    ProcessOperationKind,
)
from gf_wordbench.kernel.ids import ScenarioId, validate_scenario_id

_DEFAULT_TOOL_ID: Final[str] = "gf"
_DEFAULT_ENVIRONMENT_POLICY: Final[str] = "controlled-inherit-v1"
_DEFAULT_EVIDENCE_POLICY: Final[str] = "scenario-raw-v1"
_DEFAULT_MUTABILITY_CLASS: Final[str] = "read_only"
_DEFAULT_NETWORK_POLICY: Final[str] = "denied"
_DEFAULT_TERMINATION_GRACE_SEC: Final[float] = 5.0
_UTF8_BOM: Final[bytes] = b"\xef\xbb\xbf"


@dataclass(frozen=True, slots=True)
class ScenarioScriptInput:
    scenario_id: ScenarioId
    script_path: Path
    text: str
    size_bytes: int
    sha256: str
    has_utf8_bom: bool

    def __post_init__(self) -> None:
        scenario_id = validate_scenario_id(self.scenario_id)
        script_path = Path(self.script_path)

        if script_path.suffix.casefold() != ".gfs":
            raise ValueError("script_path must identify a .gfs file")
        if "\x00" in str(script_path):
            raise ValueError("script_path must not contain NUL")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if "\x00" in self.text:
            raise ValueError("scenario text must not contain NUL")
        if isinstance(self.size_bytes, bool) or not isinstance(
            self.size_bytes,
            int,
        ):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if not isinstance(self.sha256, str):
            raise TypeError("sha256 must be a string")
        if len(self.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256
        ):
            raise ValueError("sha256 must contain 64 lowercase hexadecimal characters")
        if type(self.has_utf8_bom) is not bool:
            raise TypeError("has_utf8_bom must be a bool")

        encoded = self.text.encode("utf-8")
        if len(encoded) != self.size_bytes:
            raise ValueError("size_bytes does not match the encoded scenario text")
        if hashlib.sha256(encoded).hexdigest() != self.sha256:
            raise ValueError("sha256 does not match the encoded scenario text")
        if encoded.startswith(_UTF8_BOM) != self.has_utf8_bom:
            raise ValueError("has_utf8_bom does not match the scenario bytes")

        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "script_path", script_path)

    @classmethod
    def from_bytes(
        cls,
        *,
        scenario_id: object,
        script_path: Path,
        content: bytes,
    ) -> ScenarioScriptInput:
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")

        text = content.decode("utf-8", errors="strict")
        return cls(
            scenario_id=validate_scenario_id(scenario_id),
            script_path=Path(script_path),
            text=text,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            has_utf8_bom=content.startswith(_UTF8_BOM),
        )

    def verify_bytes(self, content: bytes) -> None:
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if len(content) != self.size_bytes:
            raise ValueError("scenario bytes changed after preparation")
        if hashlib.sha256(content).hexdigest() != self.sha256:
            raise ValueError("scenario bytes changed after preparation")


def build_scenario_process_request(
    script: ScenarioScriptInput,
    *,
    executable: Path,
    args: Sequence[str],
    working_directory: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_sec: float,
    output_limit_bytes: int,
    approved_read_roots: Sequence[Path],
    approved_write_roots: Sequence[Path],
    expected_artifacts: Sequence[ArtifactExpectation] = (),
    request_id: str | None = None,
    operation_id: str | None = None,
    tool_id: str = _DEFAULT_TOOL_ID,
    environment_policy: str = _DEFAULT_ENVIRONMENT_POLICY,
    env_overrides: Mapping[str, str] | None = None,
    env_removals: Collection[str] = (),
    sensitive_env_keys: Collection[str] = (),
    sensitive_arg_indexes: Collection[int] = (),
    termination_grace_sec: float = _DEFAULT_TERMINATION_GRACE_SEC,
    evidence_policy: str = _DEFAULT_EVIDENCE_POLICY,
    metadata: Mapping[str, str] | None = None,
) -> ProcessRequest:
    if not isinstance(script, ScenarioScriptInput):
        raise TypeError("script must be a ScenarioScriptInput")

    normalized_args = _normalize_args(args)
    normalized_timeout = _positive_number(
        timeout_sec,
        field_name="timeout_sec",
    )
    normalized_limit = _positive_integer(
        output_limit_bytes,
        field_name="output_limit_bytes",
    )
    normalized_grace = _non_negative_number(
        termination_grace_sec,
        field_name="termination_grace_sec",
    )

    scenario_id = str(script.scenario_id)
    resolved_request_id = _optional_identifier(
        request_id,
        default=f"scenario:{scenario_id}",
        field_name="request_id",
    )
    resolved_operation_id = _optional_identifier(
        operation_id,
        default=f"scenario:{scenario_id}",
        field_name="operation_id",
    )

    request_metadata = {
        "scenario_id": scenario_id,
        "script_path": script.script_path.as_posix(),
        "script_sha256": script.sha256,
        "script_size_bytes": str(script.size_bytes),
        "script_encoding": "utf-8",
        "script_has_utf8_bom": "true" if script.has_utf8_bom else "false",
    }
    if metadata is not None:
        request_metadata.update(
            _normalize_string_mapping(
                metadata,
                field_name="metadata",
            )
        )

    if request_metadata["scenario_id"] != scenario_id:
        raise ValueError("metadata must not override scenario_id")
    if request_metadata["script_sha256"] != script.sha256:
        raise ValueError("metadata must not override script_sha256")

    return ProcessRequest(
        request_id=resolved_request_id,
        tool_id=_non_empty_text(tool_id, field_name="tool_id"),
        operation_id=resolved_operation_id,
        operation_kind=ProcessOperationKind.SCENARIO,
        executable=Path(executable),
        args=normalized_args,
        cwd=Path(working_directory),
        stdout_path=Path(stdout_path),
        stderr_path=Path(stderr_path),
        timeout_sec=normalized_timeout,
        approved_read_roots=_normalize_paths(
            approved_read_roots,
            field_name="approved_read_roots",
        ),
        approved_write_roots=_normalize_paths(
            approved_write_roots,
            field_name="approved_write_roots",
        ),
        evidence_policy=_non_empty_text(
            evidence_policy,
            field_name="evidence_policy",
        ),
        stdin=ProcessInput.from_text(script.text, encoding="utf-8"),
        environment_policy=_non_empty_text(
            environment_policy,
            field_name="environment_policy",
        ),
        env_overrides=_normalize_string_mapping(
            env_overrides or {},
            field_name="env_overrides",
        ),
        env_removals=frozenset(
            _normalize_strings(
                env_removals,
                field_name="env_removals",
            )
        ),
        sensitive_env_keys=frozenset(
            _normalize_strings(
                sensitive_env_keys,
                field_name="sensitive_env_keys",
            )
        ),
        sensitive_arg_indexes=frozenset(_normalize_indexes(sensitive_arg_indexes)),
        termination_grace_sec=normalized_grace,
        output_limit_bytes=normalized_limit,
        expected_artifacts=_normalize_artifacts(expected_artifacts),
        metadata=MappingProxyType(request_metadata),
        mutability_class=_DEFAULT_MUTABILITY_CLASS,
        network_policy=_DEFAULT_NETWORK_POLICY,
    )


def execute_scenario_process(
    request: ProcessRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> ProcessResult:
    _validate_scenario_process_request(request)
    return run_process(
        request,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
    )


def prepare_and_execute_scenario(
    script: ScenarioScriptInput,
    *,
    executable: Path,
    args: Sequence[str],
    working_directory: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_sec: float,
    output_limit_bytes: int,
    approved_read_roots: Sequence[Path],
    approved_write_roots: Sequence[Path],
    expected_artifacts: Sequence[ArtifactExpectation] = (),
    request_id: str | None = None,
    operation_id: str | None = None,
    tool_id: str = _DEFAULT_TOOL_ID,
    environment_policy: str = _DEFAULT_ENVIRONMENT_POLICY,
    env_overrides: Mapping[str, str] | None = None,
    env_removals: Collection[str] = (),
    sensitive_env_keys: Collection[str] = (),
    sensitive_arg_indexes: Collection[int] = (),
    termination_grace_sec: float = _DEFAULT_TERMINATION_GRACE_SEC,
    evidence_policy: str = _DEFAULT_EVIDENCE_POLICY,
    metadata: Mapping[str, str] | None = None,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> ProcessResult:
    request = build_scenario_process_request(
        script,
        executable=executable,
        args=args,
        working_directory=working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=timeout_sec,
        output_limit_bytes=output_limit_bytes,
        approved_read_roots=approved_read_roots,
        approved_write_roots=approved_write_roots,
        expected_artifacts=expected_artifacts,
        request_id=request_id,
        operation_id=operation_id,
        tool_id=tool_id,
        environment_policy=environment_policy,
        env_overrides=env_overrides,
        env_removals=env_removals,
        sensitive_env_keys=sensitive_env_keys,
        sensitive_arg_indexes=sensitive_arg_indexes,
        termination_grace_sec=termination_grace_sec,
        evidence_policy=evidence_policy,
        metadata=metadata,
    )
    return execute_scenario_process(
        request,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
    )


def _validate_scenario_process_request(request: ProcessRequest) -> None:
    if not isinstance(request, ProcessRequest):
        raise TypeError("request must be a ProcessRequest")
    if request.operation_kind is not ProcessOperationKind.SCENARIO:
        raise ValueError("request operation_kind must be scenario")
    if request.stdin.text is None or request.stdin.path is not None:
        raise ValueError("scenario execution requires direct text stdin")
    if request.stdin.encoding.casefold().replace("_", "-") != "utf-8":
        raise ValueError("scenario stdin encoding must be UTF-8")

    scenario_id = request.metadata.get("scenario_id")
    validate_scenario_id(scenario_id, field="request metadata scenario ID")

    script_path = request.metadata.get("script_path")
    if script_path is None:
        raise ValueError("request metadata must include script_path")
    if Path(script_path).suffix.casefold() != ".gfs":
        raise ValueError("request metadata script_path must identify a .gfs file")

    script_sha256 = request.metadata.get("script_sha256")
    if (
        script_sha256 is None
        or len(script_sha256) != 64
        or any(character not in "0123456789abcdef" for character in script_sha256)
    ):
        raise ValueError("request metadata must include a lowercase SHA-256 digest")

    encoded = request.stdin.text.encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != script_sha256:
        raise ValueError("scenario stdin no longer matches the recorded script SHA-256")

    recorded_size = request.metadata.get("script_size_bytes")
    if recorded_size is None:
        raise ValueError("request metadata must include script_size_bytes")
    try:
        expected_size = int(recorded_size, 10)
    except ValueError as exc:
        raise ValueError("request metadata script_size_bytes must be an integer") from exc
    if expected_size < 0 or expected_size != len(encoded):
        raise ValueError("scenario stdin no longer matches the recorded script size")

    if request.stdout_path == request.stderr_path:
        raise ValueError("scenario stdout and stderr paths must be distinct")


def _normalize_args(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("args must be a sequence of strings")
    normalized = tuple(values)
    for index, value in enumerate(normalized):
        if not isinstance(value, str):
            raise TypeError(f"args[{index}] must be a string")
        if "\x00" in value:
            raise ValueError(f"args[{index}] must not contain NUL")
    return normalized


def _normalize_paths(
    values: Sequence[Path],
    *,
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError(f"{field_name} must be a sequence of paths")

    normalized: list[Path] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        path = Path(value)
        if "\x00" in str(path):
            raise ValueError(f"{field_name}[{index}] must not contain NUL")
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(path)

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _normalize_artifacts(
    values: Sequence[ArtifactExpectation],
) -> tuple[ArtifactExpectation, ...]:
    raw_values: object = values
    if isinstance(raw_values, (str, bytes)):
        raise TypeError("expected_artifacts must be a sequence of ArtifactExpectation values")
    normalized = tuple(values)
    if not all(isinstance(value, ArtifactExpectation) for value in normalized):
        raise TypeError("expected_artifacts must contain ArtifactExpectation values")

    seen: set[tuple[str, str]] = set()
    for value in normalized:
        key = (str(value.path).casefold(), value.role)
        if key in seen:
            raise ValueError("expected_artifacts contains a duplicate path and role")
        seen.add(key)
    return normalized


def _normalize_strings(
    values: Collection[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be a collection of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _non_empty_text(value, field_name=field_name)
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(normalized)


def _normalize_indexes(values: Collection[int]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("sensitive_arg_indexes must be a collection of integers")

    normalized: set[int] = set()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("sensitive_arg_indexes must contain integers")
        if value < 0:
            raise ValueError("sensitive_arg_indexes must contain non-negative integers")
        normalized.add(value)
    return tuple(sorted(normalized))


def _normalize_string_mapping(
    values: Mapping[str, str],
    *,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, str] = {}
    for key, value in values.items():
        normalized_key = _non_empty_text(
            key,
            field_name=f"{field_name} key",
        )
        if not isinstance(value, str):
            raise TypeError(f"{field_name}[{normalized_key!r}] must be a string")
        if "\x00" in value:
            raise ValueError(f"{field_name}[{normalized_key!r}] must not contain NUL")
        normalized[normalized_key] = value
    return normalized


def _optional_identifier(
    value: str | None,
    *,
    default: str,
    field_name: str,
) -> str:
    if value is None:
        return default
    return _non_empty_text(value, field_name=field_name)


def _non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or "\x00" in value:
        raise ValueError(f"{field_name} must be non-empty and contain no NUL")
    return value


def _positive_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _positive_number(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return normalized


def _non_negative_number(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


__all__ = (
    "ScenarioScriptInput",
    "build_scenario_process_request",
    "execute_scenario_process",
    "prepare_and_execute_scenario",
)
