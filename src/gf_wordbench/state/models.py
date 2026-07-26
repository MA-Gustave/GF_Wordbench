"""Immutable application-state models.

This module defines the validated in-memory shape of private GF Wordbench
application state. Schema identity, defaults, migration, serialization, and
filesystem persistence are owned by the other modules in ``gf_wordbench.state``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path

from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode

__all__ = (
    "AppState",
    "EnvironmentState",
    "LastRunState",
    "SelectionState",
    "StateDiagnostic",
    "StateDiagnosticCode",
    "StateLoadResult",
)


def _require_string(
    value: object,
    *,
    field_name: str,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain a NUL character")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_optional_path_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    path_text = _require_string(
        value,
        field_name=field_name,
        allow_empty=False,
    )
    if path_text != path_text.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    return path_text


def _require_bool(value: object, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _require_int(
    value: object,
    *,
    field_name: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _require_path(value: object, *, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    return value


def _require_tuple(value: object, *, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    return value


@unique
class StateDiagnosticCode(StrEnum):
    """Stable outcomes produced while loading or writing application state."""

    MISSING = "missing"
    LOADED = "loaded"
    MIGRATED = "migrated"
    PARTIALLY_DEFAULTED = "partially_defaulted"
    MALFORMED = "malformed"
    SCHEMA_MISMATCH = "schema_mismatch"
    VERSION_UNSUPPORTED = "version_unsupported"
    QUARANTINED = "quarantined"
    WRITE_FAILED = "write_failed"


@dataclass(frozen=True, slots=True)
class EnvironmentState:
    """Remembered machine-local paths.

    Values remain strings because they may be stale at the next startup. They
    become authoritative runtime paths only after configuration resolution and
    validation.
    """

    project_root: str | None
    rgl_root: str | None
    gf_executable: str | None
    output_root: str | None

    def __post_init__(self) -> None:
        _require_optional_path_text(
            self.project_root,
            field_name="project_root",
        )
        _require_optional_path_text(
            self.rgl_root,
            field_name="rgl_root",
        )
        _require_optional_path_text(
            self.gf_executable,
            field_name="gf_executable",
        )
        _require_optional_path_text(
            self.output_root,
            field_name="output_root",
        )


@dataclass(frozen=True, slots=True)
class SelectionState:
    """Non-authoritative remembered validation preferences."""

    mode: ValidationMode
    target_file: str
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")

        target_file = _require_string(
            self.target_file,
            field_name="target_file",
            allow_empty=True,
        )
        if target_file and target_file != target_file.strip():
            raise ValueError(
                "target_file must not contain surrounding whitespace"
            )

        _require_int(
            self.timeout_sec,
            field_name="timeout_sec",
            minimum=1,
        )
        _require_int(
            self.max_files,
            field_name="max_files",
            minimum=0,
        )
        _require_bool(
            self.keep_ok_details,
            field_name="keep_ok_details",
        )
        _require_bool(
            self.diff_previous,
            field_name="diff_previous",
        )
        _require_bool(
            self.skip_version_probe,
            field_name="skip_version_probe",
        )
        _require_bool(
            self.no_compile,
            field_name="no_compile",
        )
        _require_bool(
            self.emit_cpu_stats,
            field_name="emit_cpu_stats",
        )


@dataclass(frozen=True, slots=True)
class LastRunState:
    """Convenience pointers to the most recently recorded run evidence."""

    run_dir: str | None
    summary_path: str | None
    status_message: str

    def __post_init__(self) -> None:
        _require_optional_path_text(
            self.run_dir,
            field_name="run_dir",
        )
        _require_optional_path_text(
            self.summary_path,
            field_name="summary_path",
        )
        _require_string(
            self.status_message,
            field_name="status_message",
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class AppState:
    """Validated canonical application state.

    Runtime-only values such as active processes, current run objects, loading
    warnings, and GUI state are intentionally absent from this persisted model.
    """

    schema_id: str
    schema_version: str
    producer: ProducerInfo | None
    environment: EnvironmentState
    selection: SelectionState
    last_run: LastRunState

    def __post_init__(self) -> None:
        schema_id = _require_string(
            self.schema_id,
            field_name="schema_id",
            allow_empty=False,
        )
        schema_version = _require_string(
            self.schema_version,
            field_name="schema_version",
            allow_empty=False,
        )

        if schema_id != schema_id.strip():
            raise ValueError("schema_id must not contain surrounding whitespace")
        if schema_version != schema_version.strip():
            raise ValueError(
                "schema_version must not contain surrounding whitespace"
            )

        if self.producer is not None and not isinstance(
            self.producer,
            ProducerInfo,
        ):
            raise TypeError("producer must be a ProducerInfo or None")
        if not isinstance(self.environment, EnvironmentState):
            raise TypeError("environment must be an EnvironmentState")
        if not isinstance(self.selection, SelectionState):
            raise TypeError("selection must be a SelectionState")
        if not isinstance(self.last_run, LastRunState):
            raise TypeError("last_run must be a LastRunState")


@dataclass(frozen=True, slots=True)
class StateDiagnostic:
    """One bounded diagnostic produced by the state repository."""

    code: StateDiagnosticCode
    message: str
    path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.code, StateDiagnosticCode):
            raise TypeError("code must be a StateDiagnosticCode")

        message = _require_string(
            self.message,
            field_name="message",
            allow_empty=False,
        )
        if message != message.strip():
            raise ValueError("message must not contain surrounding whitespace")

        _require_path(self.path, field_name="path")


@dataclass(frozen=True, slots=True)
class StateLoadResult:
    """Validated result of loading canonical or migrated application state."""

    state: AppState
    source_path: Path
    diagnostics: tuple[StateDiagnostic, ...]
    migrated: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, AppState):
            raise TypeError("state must be an AppState")

        _require_path(self.source_path, field_name="source_path")
        diagnostics = _require_tuple(
            self.diagnostics,
            field_name="diagnostics",
        )
        _require_bool(self.migrated, field_name="migrated")

        for index, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, StateDiagnostic):
                raise TypeError(
                    f"diagnostics[{index}] must be a StateDiagnostic"
                )

        if self.migrated and not any(
            diagnostic.code is StateDiagnosticCode.MIGRATED
            for diagnostic in self.diagnostics
        ):
            raise ValueError(
                "migrated results must include a MIGRATED diagnostic"
            )