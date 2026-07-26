"""Immutable compilation-domain models for GF Wordbench."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

StringMap: TypeAlias = Mapping[str, str]

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_EMPTY_STRING_MAP: Final[StringMap] = MappingProxyType({})


@unique
class CompileTargetKind(StrEnum):
    SOURCE = "source"
    CHECKPOINT = "checkpoint"
    ENTRYPOINT = "entrypoint"
    PGF = "pgf"


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_bool(value: object, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a bool")
    return value


def _require_non_negative_int(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_positive_number(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return normalized


def _normalize_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if isinstance(value, bytes):
        raise TypeError(f"{field_name} must be path-like text")
    try:
        path = Path(value)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be path-like") from exc
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    return path


def _normalize_optional_path(
    value: object | None,
    *,
    field_name: str,
) -> Path | None:
    if value is None:
        return None
    return _normalize_path(value, field_name=field_name)


def _normalize_paths(
    values: Iterable[object],
    *,
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of paths")
    normalized: list[Path] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        path = _normalize_path(
            value,
            field_name=f"{field_name}[{index}]",
        )
        key = path.as_posix()
        if key in seen:
            raise ValueError(
                f"{field_name} contains duplicate path {key!r}"
            )
        seen.add(key)
        normalized.append(path)
    return tuple(normalized)


def _normalize_strings(
    values: Iterable[object],
    *,
    field_name: str,
    allow_empty_items: bool = False,
    unique: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        item = _require_text(
            value,
            field_name=f"{field_name}[{index}]",
            allow_empty=allow_empty_items,
        )
        if unique and item in seen:
            raise ValueError(
                f"{field_name} contains duplicate value {item!r}"
            )
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _freeze_string_map(
    values: Mapping[object, object],
    *,
    field_name: str,
) -> StringMap:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    normalized: dict[str, str] = {}
    for raw_key, raw_value in values.items():
        key = _require_text(
            raw_key,
            field_name=f"{field_name} key",
        )
        value = _require_text(
            raw_value,
            field_name=f"{field_name}[{key!r}]",
            allow_empty=True,
        )
        normalized[key] = value
    if not normalized:
        return _EMPTY_STRING_MAP
    return MappingProxyType(normalized)


def _is_project_relative(path: Path) -> bool:
    text = path.as_posix()
    if not text or text.startswith("/") or text.startswith("//"):
        return False
    if re.match(r"^[A-Za-z]:", text):
        return False
    return all(part not in {"", ".", ".."} for part in path.parts)


@dataclass(frozen=True, slots=True)
class CompileTarget:
    target_id: str
    kind: CompileTargetKind
    source_path: Path
    module_name: str
    required: bool
    expected_artifacts: tuple[Path, ...]
    declared_order: int
    entrypoint_modules: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.target_id, field_name="target_id")
        _require_text(self.module_name, field_name="module_name")
        _require_bool(self.required, field_name="required")
        _require_non_negative_int(
            self.declared_order,
            field_name="declared_order",
        )

        kind = self.kind
        if not isinstance(kind, CompileTargetKind):
            try:
                kind = CompileTargetKind(kind)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "kind must be source, checkpoint, entrypoint, or pgf"
                ) from exc
            object.__setattr__(self, "kind", kind)

        source_path = _normalize_path(
            self.source_path,
            field_name="source_path",
        )
        if not _is_project_relative(source_path):
            raise ValueError(
                "source_path must be a contained project-relative path"
            )
        if source_path.suffix.casefold() != ".gf":
            raise ValueError("source_path must identify a .gf source")
        object.__setattr__(self, "source_path", source_path)

        expected_artifacts = _normalize_paths(
            self.expected_artifacts,
            field_name="expected_artifacts",
        )
        object.__setattr__(
            self,
            "expected_artifacts",
            expected_artifacts,
        )

        entrypoints = _normalize_strings(
            self.entrypoint_modules,
            field_name="entrypoint_modules",
            unique=True,
        )
        object.__setattr__(
            self,
            "entrypoint_modules",
            entrypoints,
        )

        if kind is CompileTargetKind.PGF:
            if not entrypoints:
                object.__setattr__(
                    self,
                    "entrypoint_modules",
                    (self.module_name,),
                )
        elif entrypoints:
            raise ValueError(
                "entrypoint_modules is reserved for pgf targets"
            )

    @property
    def sort_key(self) -> tuple[int, str, str]:
        return (
            self.declared_order,
            self.source_path.as_posix(),
            self.target_id,
        )

    @property
    def is_pgf(self) -> bool:
        return self.kind is CompileTargetKind.PGF


@dataclass(frozen=True, slots=True)
class CompileRequest:
    target: CompileTarget
    executable: Path
    args: tuple[str, ...]
    working_directory: Path
    environment: StringMap
    timeout_sec: float
    stdout_path: Path
    stderr_path: Path
    expected_artifacts: tuple[Path, ...]
    effective_gf_path: tuple[Path, ...] = ()
    source_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.target, CompileTarget):
            raise TypeError("target must be a CompileTarget")

        executable = _normalize_path(
            self.executable,
            field_name="executable",
        )
        working_directory = _normalize_path(
            self.working_directory,
            field_name="working_directory",
        )
        stdout_path = _normalize_path(
            self.stdout_path,
            field_name="stdout_path",
        )
        stderr_path = _normalize_path(
            self.stderr_path,
            field_name="stderr_path",
        )

        if stdout_path == stderr_path:
            raise ValueError(
                "stdout_path and stderr_path must be distinct"
            )

        args = _normalize_strings(
            self.args,
            field_name="args",
            allow_empty_items=True,
        )
        if not args:
            raise ValueError("args must not be empty")

        environment = _freeze_string_map(
            self.environment,
            field_name="environment",
        )
        expected_artifacts = _normalize_paths(
            self.expected_artifacts,
            field_name="expected_artifacts",
        )
        effective_gf_path = _normalize_paths(
            self.effective_gf_path,
            field_name="effective_gf_path",
        )
        timeout_sec = _require_positive_number(
            self.timeout_sec,
            field_name="timeout_sec",
        )

        fingerprint = self.source_fingerprint
        if fingerprint is not None:
            fingerprint = _require_text(
                fingerprint,
                field_name="source_fingerprint",
            )

        object.__setattr__(self, "executable", executable)
        object.__setattr__(self, "args", args)
        object.__setattr__(
            self,
            "working_directory",
            working_directory,
        )
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "timeout_sec", timeout_sec)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(
            self,
            "expected_artifacts",
            expected_artifacts,
        )
        object.__setattr__(
            self,
            "effective_gf_path",
            effective_gf_path,
        )
        object.__setattr__(
            self,
            "source_fingerprint",
            fingerprint,
        )

    @property
    def command(self) -> tuple[str, ...]:
        return (str(self.executable), *self.args)


@dataclass(frozen=True, slots=True)
class ArtifactCheckItem:
    path: Path
    required: bool
    contained: bool
    exists: bool
    regular_file: bool
    non_empty: bool
    fresh: bool
    associated_with_request: bool
    trusted: bool
    manifest_required: bool = False
    manifest_registered: bool = False
    size_bytes: int | None = None
    sha256: str | None = None
    message: str = ""

    def __post_init__(self) -> None:
        path = _normalize_path(self.path, field_name="path")
        object.__setattr__(self, "path", path)

        for field_name in (
            "required",
            "contained",
            "exists",
            "regular_file",
            "non_empty",
            "fresh",
            "associated_with_request",
            "trusted",
            "manifest_required",
            "manifest_registered",
        ):
            _require_bool(
                getattr(self, field_name),
                field_name=field_name,
            )

        _require_text(
            self.message,
            field_name="message",
            allow_empty=True,
        )

        if self.size_bytes is not None:
            _require_non_negative_int(
                self.size_bytes,
                field_name="size_bytes",
            )

        digest = self.sha256
        if digest is not None:
            digest = _require_text(
                digest,
                field_name="sha256",
            ).casefold()
            if _SHA256_RE.fullmatch(digest) is None:
                raise ValueError(
                    "sha256 must contain exactly 64 lowercase hexadecimal characters"
                )
            object.__setattr__(self, "sha256", digest)

        if not self.exists:
            if (
                self.regular_file
                or self.non_empty
                or self.fresh
                or self.associated_with_request
                or self.trusted
                or self.manifest_registered
                or self.size_bytes is not None
                or self.sha256 is not None
            ):
                raise ValueError(
                    "a missing artifact cannot have positive file, freshness, "
                    "trust, manifest, size, or hash evidence"
                )

        if self.regular_file and not self.exists:
            raise ValueError("regular_file requires exists")
        if self.non_empty and not self.regular_file:
            raise ValueError("non_empty requires regular_file")
        if self.fresh and not self.exists:
            raise ValueError("fresh requires exists")
        if self.associated_with_request and not self.fresh:
            raise ValueError(
                "associated_with_request requires fresh evidence"
            )
        if self.sha256 is not None and not self.regular_file:
            raise ValueError("sha256 requires a regular file")
        if self.manifest_registered and not self.exists:
            raise ValueError("manifest registration requires exists")

        trustworthy = (
            self.contained
            and self.exists
            and self.regular_file
            and self.non_empty
            and self.fresh
            and self.associated_with_request
        )
        if self.trusted and not trustworthy:
            raise ValueError(
                "trusted requires containment, existence, regular-file, "
                "non-empty, freshness, and request-association evidence"
            )

    @property
    def satisfies_contract(self) -> bool:
        if not self.trusted:
            return False
        if self.manifest_required and not self.manifest_registered:
            return False
        return True


@dataclass(frozen=True, slots=True)
class ArtifactCheck:
    items: tuple[ArtifactCheckItem, ...] = ()
    unexpected_artifacts: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        items = tuple(self.items)
        if not all(
            isinstance(item, ArtifactCheckItem)
            for item in items
        ):
            raise TypeError(
                "items must contain ArtifactCheckItem values"
            )

        seen: set[str] = set()
        for item in items:
            key = item.path.as_posix()
            if key in seen:
                raise ValueError(
                    f"items contains duplicate artifact path {key!r}"
                )
            seen.add(key)

        unexpected_artifacts = _normalize_paths(
            self.unexpected_artifacts,
            field_name="unexpected_artifacts",
        )
        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
            allow_empty_items=False,
        )

        object.__setattr__(self, "items", items)
        object.__setattr__(
            self,
            "unexpected_artifacts",
            unexpected_artifacts,
        )
        object.__setattr__(self, "warnings", warnings)

    @classmethod
    def empty(cls) -> ArtifactCheck:
        return cls()

    @property
    def required_items(self) -> tuple[ArtifactCheckItem, ...]:
        return tuple(item for item in self.items if item.required)

    @property
    def failed_required_items(
        self,
    ) -> tuple[ArtifactCheckItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.required and not item.satisfies_contract
        )

    @property
    def passed(self) -> bool:
        return not self.failed_required_items

    @property
    def produced_artifacts(self) -> tuple[Path, ...]:
        return tuple(item.path for item in self.items if item.exists)


@dataclass(frozen=True, slots=True)
class GFVersionResult:
    status: ValidationStatus
    executable: Path
    command: tuple[str, ...]
    execution_state: ExecutionState | None
    exit_code: int | None
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    version: str | None
    compatibility: str
    message: str = ""
    warnings: tuple[str, ...] = ()
    skipped_reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be a ValidationStatus")

        executable = _normalize_path(
            self.executable,
            field_name="executable",
        )
        command = _normalize_strings(
            self.command,
            field_name="command",
            allow_empty_items=True,
        )
        if command and command[0] != str(executable):
            raise ValueError(
                "command must begin with the recorded executable"
            )

        if (
            self.execution_state is not None
            and not isinstance(self.execution_state, ExecutionState)
        ):
            raise TypeError(
                "execution_state must be an ExecutionState or None"
            )

        if self.exit_code is not None and (
            isinstance(self.exit_code, bool)
            or not isinstance(self.exit_code, int)
        ):
            raise TypeError("exit_code must be an integer or None")

        _require_non_negative_int(
            self.duration_ms,
            field_name="duration_ms",
        )
        stdout_path = _normalize_optional_path(
            self.stdout_path,
            field_name="stdout_path",
        )
        stderr_path = _normalize_optional_path(
            self.stderr_path,
            field_name="stderr_path",
        )
        if (
            stdout_path is not None
            and stderr_path is not None
            and stdout_path == stderr_path
        ):
            raise ValueError(
                "stdout_path and stderr_path must be distinct"
            )

        version = self.version
        if version is not None:
            version = _require_text(
                version,
                field_name="version",
            )

        compatibility = _require_text(
            self.compatibility,
            field_name="compatibility",
        )
        _require_text(
            self.message,
            field_name="message",
            allow_empty=True,
        )
        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
        )
        _require_text(
            self.skipped_reason,
            field_name="skipped_reason",
            allow_empty=True,
        )

        object.__setattr__(self, "executable", executable)
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "compatibility", compatibility)
        object.__setattr__(self, "warnings", warnings)

        if self.status is ValidationStatus.SKIPPED:
            if self.execution_state is not None:
                raise ValueError(
                    "a skipped version probe has no execution_state"
                )
            if self.exit_code is not None:
                raise ValueError(
                    "a skipped version probe has no exit_code"
                )
            if self.duration_ms != 0:
                raise ValueError(
                    "a skipped version probe has zero duration"
                )
            if command:
                raise ValueError(
                    "a skipped version probe has no executed command"
                )
            if version is not None:
                raise ValueError(
                    "a skipped version probe has no parsed version"
                )
            if not self.skipped_reason:
                raise ValueError(
                    "a skipped version probe requires skipped_reason"
                )
            return

        if self.execution_state is None:
            raise ValueError(
                "an attempted version probe requires execution_state"
            )
        if not command:
            raise ValueError(
                "an attempted version probe requires command"
            )
        if self.skipped_reason:
            raise ValueError(
                "skipped_reason is reserved for skipped probes"
            )

        if self.status is ValidationStatus.OK:
            if self.execution_state is not ExecutionState.COMPLETED:
                raise ValueError(
                    "an OK version probe must complete normally"
                )
            if self.exit_code != 0:
                raise ValueError(
                    "an OK version probe requires exit_code zero"
                )
            if version is None:
                raise ValueError(
                    "an OK version probe requires a parsed version"
                )

        if self.execution_state is ExecutionState.LAUNCH_FAILED:
            if self.exit_code is not None:
                raise ValueError(
                    "a launch failure must not fabricate an exit code"
                )
            if self.status is not ValidationStatus.ERROR:
                raise ValueError(
                    "a launch failure must produce ERROR"
                )

        if self.execution_state in {
            ExecutionState.TIMED_OUT,
            ExecutionState.CANCELLED,
        } and self.status is not ValidationStatus.ERROR:
            raise ValueError(
                "timeout or cancellation must produce ERROR"
            )


@dataclass(frozen=True, slots=True)
class CompileResult:
    target: CompileTarget
    status: ValidationStatus
    execution_state: ExecutionState | None
    exit_code: int | None
    duration_ms: int
    error_kind: ErrorKind | None
    first_error: str
    error_detail: str
    stdout_path: Path | None
    stderr_path: Path | None
    artifact_check: ArtifactCheck
    executable: Path | None = None
    command: tuple[str, ...] = ()
    working_directory: Path | None = None
    gf_version: str | None = None
    warnings: tuple[str, ...] = ()
    skipped_reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.target, CompileTarget):
            raise TypeError("target must be a CompileTarget")
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be a ValidationStatus")
        if (
            self.execution_state is not None
            and not isinstance(self.execution_state, ExecutionState)
        ):
            raise TypeError(
                "execution_state must be an ExecutionState or None"
            )
        if self.exit_code is not None and (
            isinstance(self.exit_code, bool)
            or not isinstance(self.exit_code, int)
        ):
            raise TypeError("exit_code must be an integer or None")
        _require_non_negative_int(
            self.duration_ms,
            field_name="duration_ms",
        )

        error_kind = self.error_kind
        if error_kind is not None and not isinstance(
            error_kind,
            ErrorKind,
        ):
            try:
                error_kind = ErrorKind(error_kind)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "error_kind must be a canonical ErrorKind or None"
                ) from exc
            object.__setattr__(
                self,
                "error_kind",
                error_kind,
            )

        _require_text(
            self.first_error,
            field_name="first_error",
            allow_empty=True,
        )
        _require_text(
            self.error_detail,
            field_name="error_detail",
            allow_empty=True,
        )

        stdout_path = _normalize_optional_path(
            self.stdout_path,
            field_name="stdout_path",
        )
        stderr_path = _normalize_optional_path(
            self.stderr_path,
            field_name="stderr_path",
        )
        if (
            stdout_path is not None
            and stderr_path is not None
            and stdout_path == stderr_path
        ):
            raise ValueError(
                "stdout_path and stderr_path must be distinct"
            )

        if not isinstance(self.artifact_check, ArtifactCheck):
            raise TypeError(
                "artifact_check must be an ArtifactCheck"
            )

        executable = _normalize_optional_path(
            self.executable,
            field_name="executable",
        )
        command = _normalize_strings(
            self.command,
            field_name="command",
            allow_empty_items=True,
        )
        working_directory = _normalize_optional_path(
            self.working_directory,
            field_name="working_directory",
        )

        if executable is not None and command:
            if command[0] != str(executable):
                raise ValueError(
                    "command must begin with the recorded executable"
                )

        gf_version = self.gf_version
        if gf_version is not None:
            gf_version = _require_text(
                gf_version,
                field_name="gf_version",
            )

        warnings = _normalize_strings(
            self.warnings,
            field_name="warnings",
        )
        _require_text(
            self.skipped_reason,
            field_name="skipped_reason",
            allow_empty=True,
        )

        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "executable", executable)
        object.__setattr__(self, "command", command)
        object.__setattr__(
            self,
            "working_directory",
            working_directory,
        )
        object.__setattr__(self, "gf_version", gf_version)
        object.__setattr__(self, "warnings", warnings)

        self._validate_status_coherence()

    def _validate_status_coherence(self) -> None:
        if self.status is ValidationStatus.SKIPPED:
            if self.execution_state is not None:
                raise ValueError(
                    "a skipped compile has no execution_state"
                )
            if self.exit_code is not None:
                raise ValueError(
                    "a skipped compile has no exit_code"
                )
            if self.duration_ms != 0:
                raise ValueError(
                    "a skipped compile has zero duration"
                )
            if self.error_kind is not None:
                raise ValueError(
                    "a skipped compile has no error_kind"
                )
            if self.command:
                raise ValueError(
                    "a skipped compile has no executed command"
                )
            if not self.skipped_reason:
                raise ValueError(
                    "a skipped compile requires skipped_reason"
                )
            if self.artifact_check.items:
                raise ValueError(
                    "a skipped compile cannot claim artifact checks"
                )
            return

        if self.execution_state is None:
            raise ValueError(
                "an attempted compile requires execution_state"
            )
        if self.error_kind is None:
            raise ValueError(
                "an attempted compile requires error_kind"
            )
        if self.skipped_reason:
            raise ValueError(
                "skipped_reason is reserved for skipped results"
            )
        if not self.command:
            raise ValueError(
                "an attempted compile requires command evidence"
            )
        if self.executable is None:
            raise ValueError(
                "an attempted compile requires executable evidence"
            )
        if self.working_directory is None:
            raise ValueError(
                "an attempted compile requires working_directory"
            )

        if self.execution_state is ExecutionState.LAUNCH_FAILED:
            if self.exit_code is not None:
                raise ValueError(
                    "a launch failure must not fabricate an exit code"
                )
            if self.status is not ValidationStatus.ERROR:
                raise ValueError(
                    "a launch failure must produce ERROR"
                )

        if self.execution_state in {
            ExecutionState.TIMED_OUT,
            ExecutionState.CANCELLED,
        } and self.status is not ValidationStatus.ERROR:
            raise ValueError(
                "timeout or cancellation must produce ERROR"
            )

        if self.status is ValidationStatus.OK:
            if self.execution_state is not ExecutionState.COMPLETED:
                raise ValueError(
                    "an OK compile must complete normally"
                )
            if self.exit_code != 0:
                raise ValueError(
                    "an OK compile requires exit_code zero"
                )
            if self.error_kind is not ErrorKind.OK:
                raise ValueError(
                    "an OK compile requires error_kind OK"
                )
            if self.first_error or self.error_detail:
                raise ValueError(
                    "an OK compile cannot contain error text"
                )
            if not self.artifact_check.passed:
                raise ValueError(
                    "an OK compile requires all required artifacts"
                )
            return

        if self.error_kind is ErrorKind.OK:
            raise ValueError(
                "FAIL or ERROR cannot use error_kind OK"
            )

        if self.status is ValidationStatus.FAIL:
            if self.execution_state is not ExecutionState.COMPLETED:
                raise ValueError(
                    "FAIL requires a completed interpretable GF execution"
                )

    @property
    def timed_out(self) -> bool:
        return self.execution_state is ExecutionState.TIMED_OUT

    @property
    def cancelled(self) -> bool:
        return self.execution_state is ExecutionState.CANCELLED

    @property
    def launched(self) -> bool:
        return self.execution_state not in {
            None,
            ExecutionState.LAUNCH_FAILED,
        }

    @property
    def produced_artifacts(self) -> tuple[Path, ...]:
        return self.artifact_check.produced_artifacts


__all__ = (
    "ArtifactCheck",
    "ArtifactCheckItem",
    "CompileRequest",
    "CompileResult",
    "CompileTarget",
    "CompileTargetKind",
    "GFVersionResult",
    "StringMap",
)
