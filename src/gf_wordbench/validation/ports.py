"""Ports and typed boundary contracts for GF-backed validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import math
import os
from pathlib import Path
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from gf_wordbench.kernel.ids import (
    NormalizationProfileId,
    ProjectId,
    RunId,
    ScenarioId,
    validate_project_id,
    validate_run_id,
    validate_scenario_id,
)
from gf_wordbench.kernel.paths import normalize_environment_path
from gf_wordbench.kernel.statuses import ExecutionState

if TYPE_CHECKING:
    from gf_wordbench.infrastructure.process.termination import CancellationToken


class GfOperationKind(StrEnum):
    PROBE_VERSION = "probe_version"
    COMPILE_MODULE = "compile_module"
    BUILD_PGF = "build_pgf"
    RUN_SCENARIO = "run_scenario"
    INSPECT_GRAMMAR = "inspect_grammar"


class GfArtifactKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


class GfDiagnosticStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


class GrammarInspectionKind(StrEnum):
    ABSTRACT_INFO = "abstract_info"
    CONCRETE_INFO = "concrete_info"
    MISSING_LINEARIZATIONS = "missing_linearizations"
    PARSE = "parse"
    LINEARIZE = "linearize"
    GENERATE_RANDOM = "generate_random"
    GENERATE_TREES = "generate_trees"
    MORPHOLOGY = "morphology"


@dataclass(frozen=True, slots=True)
class GfArtifactExpectation:
    path: Path
    role: str
    kind: GfArtifactKind = GfArtifactKind.FILE
    required: bool = True
    require_non_empty: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _path(self.path, "artifact path"))
        object.__setattr__(self, "role", _line(self.role, "artifact role"))
        _enum(self.kind, GfArtifactKind, "artifact kind")
        _bool(self.required, "required")
        _bool(self.require_non_empty, "require_non_empty")
        if self.require_non_empty and self.kind is not GfArtifactKind.FILE:
            raise ValueError("require_non_empty applies only to file artifacts")


@dataclass(frozen=True, slots=True)
class VersionProbePayload:
    operation_kind: GfOperationKind = field(
        default=GfOperationKind.PROBE_VERSION,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class ModuleCompilePayload:
    source_path: Path
    module_name: str
    output_directory: Path
    expected_object_path: Path | None = None
    operation_kind: GfOperationKind = field(
        default=GfOperationKind.COMPILE_MODULE,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class PgfBuildPayload:
    entrypoint_paths: tuple[Path, ...]
    output_path: Path
    grammar_name: str
    operation_kind: GfOperationKind = field(
        default=GfOperationKind.BUILD_PGF,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class ScenarioRunPayload:
    scenario_id: ScenarioId
    script_path: Path
    input_path: Path | None = None
    input_text: str | None = None
    operation_kind: GfOperationKind = field(
        default=GfOperationKind.RUN_SCENARIO,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class GrammarInspectionPayload:
    grammar_path: Path
    inspection_kind: GrammarInspectionKind
    subject: str | None = None
    input_text: str | None = None
    maximum_results: int | None = None
    operation_kind: GfOperationKind = field(
        default=GfOperationKind.INSPECT_GRAMMAR,
        init=False,
    )


GfOperationPayload = (
    VersionProbePayload
    | ModuleCompilePayload
    | PgfBuildPayload
    | ScenarioRunPayload
    | GrammarInspectionPayload
)


@dataclass(frozen=True, slots=True)
class GfOperationRequest:
    operation_id: str
    project_id: ProjectId
    run_id: RunId
    executable: Path
    working_directory: Path
    gf_path: tuple[Path, ...]
    stdout_path: Path
    stderr_path: Path
    timeout_sec: float
    output_limit_bytes: int
    payload: GfOperationPayload
    environment_overrides: Mapping[str, str] = field(default_factory=dict)
    expected_artifacts: tuple[GfArtifactExpectation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", _line(self.operation_id, "operation ID"))
        object.__setattr__(self, "project_id", validate_project_id(self.project_id))
        object.__setattr__(self, "run_id", validate_run_id(self.run_id))
        object.__setattr__(self, "executable", _path(self.executable, "GF executable"))
        object.__setattr__(
            self,
            "working_directory",
            _path(self.working_directory, "working directory"),
        )
        object.__setattr__(self, "gf_path", _paths(self.gf_path, "GF path"))
        object.__setattr__(self, "stdout_path", _path(self.stdout_path, "stdout path"))
        object.__setattr__(self, "stderr_path", _path(self.stderr_path, "stderr path"))
        if _key(self.stdout_path) == _key(self.stderr_path):
            raise ValueError("stdout_path and stderr_path must be distinct")
        _positive_number(self.timeout_sec, "timeout_sec")
        _positive_int(self.output_limit_bytes, "output_limit_bytes")
        object.__setattr__(self, "payload", _payload(self.payload))
        object.__setattr__(
            self,
            "environment_overrides",
            _environment(self.environment_overrides),
        )
        artifacts = tuple(self.expected_artifacts)
        if any(not isinstance(item, GfArtifactExpectation) for item in artifacts):
            raise TypeError("expected_artifacts must contain GfArtifactExpectation values")
        _unique_artifacts(artifacts)
        object.__setattr__(self, "expected_artifacts", artifacts)
        _operation_contract(self)

    @property
    def operation_kind(self) -> GfOperationKind:
        return self.payload.operation_kind


@dataclass(frozen=True, slots=True)
class GfArtifactObservation:
    path: Path
    role: str
    kind: GfArtifactKind
    required: bool
    exists: bool
    kind_matches: bool
    fresh: bool
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _path(self.path, "artifact path"))
        object.__setattr__(self, "role", _line(self.role, "artifact role"))
        _enum(self.kind, GfArtifactKind, "artifact kind")
        for name in ("required", "exists", "kind_matches", "fresh"):
            _bool(getattr(self, name), name)
        if self.size_bytes is not None:
            _non_negative_int(self.size_bytes, "size_bytes")
        if not self.exists and (self.kind_matches or self.fresh):
            raise ValueError("a missing artifact cannot match its kind or be fresh")


@dataclass(frozen=True, slots=True)
class GfDiagnosticEvidence:
    stream: GfDiagnosticStream
    message: str
    raw_text: str
    source_path: Path | None = None
    line: int | None = None
    column: int | None = None

    def __post_init__(self) -> None:
        _enum(self.stream, GfDiagnosticStream, "diagnostic stream")
        object.__setattr__(self, "message", _line(self.message, "diagnostic message"))
        object.__setattr__(self, "raw_text", _text(self.raw_text, "raw diagnostic text"))
        if self.source_path is not None:
            object.__setattr__(
                self,
                "source_path",
                _path(self.source_path, "diagnostic source path"),
            )
        if self.line is not None:
            _positive_int(self.line, "diagnostic line")
        if self.column is not None:
            _positive_int(self.column, "diagnostic column")
        if self.column is not None and self.line is None:
            raise ValueError("diagnostic column requires a line number")


@runtime_checkable
class ProcessEvidence(Protocol):
    @property
    def operation_id(self) -> str: ...

    @property
    def command(self) -> tuple[str, ...]: ...

    @property
    def working_directory(self) -> Path: ...

    @property
    def execution_state(self) -> ExecutionState: ...

    @property
    def exit_code(self) -> int | None: ...

    @property
    def duration_ms(self) -> int: ...

    @property
    def stdout_path(self) -> Path: ...

    @property
    def stderr_path(self) -> Path: ...


@dataclass(frozen=True, slots=True)
class GfOperationResult:
    operation_id: str
    operation_kind: GfOperationKind
    process: ProcessEvidence
    gf_version: str | None = None
    diagnostics: tuple[GfDiagnosticEvidence, ...] = ()
    artifacts: tuple[GfArtifactObservation, ...] = ()
    contract_complete: bool = True
    primary_message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", _line(self.operation_id, "operation ID"))
        _enum(self.operation_kind, GfOperationKind, "operation kind")
        _process(self.process)
        if self.process.operation_id != self.operation_id:
            raise ValueError("process operation_id must match the GF operation_id")
        if self.gf_version is not None:
            object.__setattr__(self, "gf_version", _line(self.gf_version, "GF version"))
        diagnostics = tuple(self.diagnostics)
        artifacts = tuple(self.artifacts)
        if any(not isinstance(item, GfDiagnosticEvidence) for item in diagnostics):
            raise TypeError("diagnostics must contain GfDiagnosticEvidence values")
        if any(not isinstance(item, GfArtifactObservation) for item in artifacts):
            raise TypeError("artifacts must contain GfArtifactObservation values")
        if len({_key(item.path) for item in artifacts}) != len(artifacts):
            raise ValueError("observed artifact paths must be unique")
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "artifacts", artifacts)
        _bool(self.contract_complete, "contract_complete")
        if self.primary_message:
            object.__setattr__(
                self,
                "primary_message",
                _line(self.primary_message, "primary message"),
            )

    @property
    def required_artifacts_valid(self) -> bool:
        return all(
            item.exists and item.kind_matches and item.fresh
            for item in self.artifacts
            if item.required
        )

    @property
    def process_completed_successfully(self) -> bool:
        return (
            self.process.execution_state is ExecutionState.COMPLETED and self.process.exit_code == 0
        )


@runtime_checkable
class GfToolPort(Protocol):
    def probe_version(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> GfOperationResult: ...

    def compile_module(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> GfOperationResult: ...

    def build_pgf(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> GfOperationResult: ...

    def run_scenario(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> GfOperationResult: ...

    def inspect_grammar(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> GfOperationResult: ...


@runtime_checkable
class SourceReader(Protocol):
    def read_bytes(self, path: Path, *, maximum_bytes: int | None = None) -> bytes: ...

    def read_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
        maximum_bytes: int | None = None,
    ) -> str: ...


@runtime_checkable
class ValidationEvidenceWriter(Protocol):
    def write_bytes_atomic(self, path: Path, data: bytes) -> None: ...

    def write_text_atomic(
        self,
        path: Path,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> None: ...


@runtime_checkable
class GoldReader(Protocol):
    def read_gold(self, path: Path, *, encoding: str = "utf-8") -> str: ...


@runtime_checkable
class GoldWriter(Protocol):
    def write_gold_atomic(
        self,
        path: Path,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> None: ...


@runtime_checkable
class SourceFingerprintView(Protocol):
    @property
    def size_bytes(self) -> int: ...

    @property
    def hash_algorithm(self) -> str: ...

    @property
    def hash(self) -> str: ...

    @property
    def last_modified_utc(self) -> datetime: ...


@runtime_checkable
class FingerprintService(Protocol):
    def fingerprint_file(self, path: Path) -> SourceFingerprintView: ...


@runtime_checkable
class NormalizationProfileView(Protocol):
    @property
    def profile_id(self) -> NormalizationProfileId: ...

    @property
    def version(self) -> str: ...


@runtime_checkable
class NormalizationProfileReader(Protocol):
    def read_profile(
        self,
        profile_id: NormalizationProfileId,
    ) -> NormalizationProfileView: ...


def validate_gf_operation_request(
    request: GfOperationRequest,
    expected_kind: GfOperationKind | None = None,
) -> GfOperationRequest:
    if not isinstance(request, GfOperationRequest):
        raise TypeError("request must be a GfOperationRequest")
    if expected_kind is not None:
        _enum(expected_kind, GfOperationKind, "expected kind")
        if request.operation_kind is not expected_kind:
            raise ValueError(
                f"expected {expected_kind.value!r}, got {request.operation_kind.value!r}"
            )
    return request


def _payload(value: object) -> GfOperationPayload:
    if isinstance(value, VersionProbePayload):
        return value
    if isinstance(value, ModuleCompilePayload):
        source = _path(value.source_path, "module source path")
        module = _line(value.module_name, "module name")
        if re.fullmatch(r"[A-Z][A-Za-z0-9_']*", module) is None:
            raise ValueError(f"invalid GF module name: {module!r}")
        expected = (
            None
            if value.expected_object_path is None
            else _path(
                value.expected_object_path,
                "expected object path",
            )
        )
        return ModuleCompilePayload(
            source,
            module,
            _path(value.output_directory, "compile output directory"),
            expected,
        )
    if isinstance(value, PgfBuildPayload):
        entrypoints = _paths(value.entrypoint_paths, "PGF entrypoint paths")
        if not entrypoints:
            raise ValueError("PGF construction requires at least one entrypoint")
        return PgfBuildPayload(
            entrypoints,
            _path(value.output_path, "PGF output path"),
            _line(value.grammar_name, "grammar name"),
        )
    if isinstance(value, ScenarioRunPayload):
        if value.input_path is not None and value.input_text is not None:
            raise ValueError("scenario input must use either a path or text, not both")
        return ScenarioRunPayload(
            validate_scenario_id(value.scenario_id),
            _path(value.script_path, "scenario script path"),
            None if value.input_path is None else _path(value.input_path, "scenario input path"),
            None if value.input_text is None else _text(value.input_text, "scenario input text"),
        )
    if isinstance(value, GrammarInspectionPayload):
        _enum(value.inspection_kind, GrammarInspectionKind, "inspection kind")
        if value.maximum_results is not None:
            _positive_int(value.maximum_results, "maximum_results")
        return GrammarInspectionPayload(
            _path(value.grammar_path, "grammar inspection path"),
            value.inspection_kind,
            None if value.subject is None else _line(value.subject, "inspection subject"),
            None if value.input_text is None else _text(value.input_text, "inspection input text"),
            value.maximum_results,
        )
    raise TypeError("payload must be a supported GF operation payload")


def _operation_contract(request: GfOperationRequest) -> None:
    if request.operation_kind is GfOperationKind.PROBE_VERSION:
        if request.expected_artifacts:
            raise ValueError("version probing cannot require generated artifacts")
        return
    required = {_key(item.path) for item in request.expected_artifacts if item.required}
    payload = request.payload
    if isinstance(payload, ModuleCompilePayload) and payload.expected_object_path is not None:
        if _key(payload.expected_object_path) not in required:
            raise ValueError("expected object path must be a required artifact")
    if isinstance(payload, PgfBuildPayload) and _key(payload.output_path) not in required:
        raise ValueError("PGF output path must be a required artifact")


def _path(value: object, name: str) -> Path:
    if isinstance(value, str):
        return normalize_environment_path(value, role=name)
    if isinstance(value, os.PathLike):
        raw = os.fspath(value)
        if isinstance(raw, bytes):
            raise TypeError(f"{name} must be a text path")
        return normalize_environment_path(raw, role=name)
    raise TypeError(f"{name} must be a string or path-like value")


def _paths(values: Sequence[Path], name: str) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, os.PathLike)):
        raise TypeError(f"{name} must be a sequence of paths")
    result = tuple(_path(value, f"{name}[{index}]") for index, value in enumerate(values))
    if len({_key(value) for value in result}) != len(result):
        raise ValueError(f"{name} must contain unique paths")
    return result


def _key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _line(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip() or any(char in value for char in "\x00\r\n"):
        raise ValueError(f"{name} must be a non-empty trimmed single line")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _environment(values: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError("environment_overrides must be a mapping")
    result: dict[str, str] = {}
    for name, value in values.items():
        key = _line(name, "environment variable name")
        if "=" in key:
            raise ValueError("environment variable names must not contain '='")
        result[key] = _text(value, f"environment variable {key}")
    return MappingProxyType(dict(sorted(result.items())))


def _process(value: object) -> None:
    required = (
        "operation_id",
        "command",
        "working_directory",
        "execution_state",
        "exit_code",
        "duration_ms",
        "stdout_path",
        "stderr_path",
    )
    if any(not hasattr(value, name) for name in required):
        raise TypeError("process must satisfy the ProcessEvidence protocol")


def _unique_artifacts(values: Sequence[GfArtifactExpectation]) -> None:
    if len({_key(item.path) for item in values}) != len(values):
        raise ValueError("expected artifact paths must be unique")


def _positive_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    if not math.isfinite(float(value)) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def _positive_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _non_negative_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")


def _enum(value: object, enum_type: type[StrEnum], name: str) -> None:
    if not isinstance(value, enum_type):
        raise TypeError(f"{name} must be a {enum_type.__name__}")


__all__ = (
    "FingerprintService",
    "GfArtifactExpectation",
    "GfArtifactKind",
    "GfArtifactObservation",
    "GfDiagnosticEvidence",
    "GfDiagnosticStream",
    "GfOperationKind",
    "GfOperationPayload",
    "GfOperationRequest",
    "GfOperationResult",
    "GfToolPort",
    "GoldReader",
    "GoldWriter",
    "GrammarInspectionKind",
    "GrammarInspectionPayload",
    "ModuleCompilePayload",
    "NormalizationProfileReader",
    "NormalizationProfileView",
    "PgfBuildPayload",
    "ProcessEvidence",
    "ScenarioRunPayload",
    "SourceFingerprintView",
    "SourceReader",
    "ValidationEvidenceWriter",
    "VersionProbePayload",
    "validate_gf_operation_request",
)
