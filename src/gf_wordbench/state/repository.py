"""Load, migrate, save, and reset GF Wordbench application state.

Application state is disposable, machine-local convenience data. This repository
never treats it as project identity, project configuration, or release evidence.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Never, TypeAlias, cast

from gf_wordbench.infrastructure.atomic_io import atomic_write_bytes
from gf_wordbench.infrastructure.filesystem import (
    copy_file,
    read_bytes,
    require_directory,
    resolve_for_output,
    unlink_file,
)
from gf_wordbench.kernel.errors import (
    InfrastructureError,
    SchemaValidationError,
    StateWriteError,
    UnsupportedVersionError,
)
from gf_wordbench.kernel.serialization import dumps_canonical_json
from gf_wordbench.version import __version__

from .migrations import LegacyStateMigration, migrate_legacy_state
from .models import (
    AppState,
    StateDiagnostic,
    StateDiagnosticCode,
    StateLoadResult,
)
from .schema import (
    APP_STATE_FILENAME as CANONICAL_STATE_FILENAME,
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
    LEGACY_APP_STATE_FILENAME as LEGACY_STATE_FILENAME,
    default_app_state,
    default_app_state_document,
    parse_app_state,
    serialize_app_state,
    validate_app_state,
)

JsonObject: TypeAlias = dict[str, object]

UTF8: Final = "utf-8"
_SUPPORTED_SCHEMA_MAJOR: Final = int(APP_STATE_SCHEMA_VERSION.partition(".")[0])
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StateRepository:
    """Filesystem repository for disposable application state.

    ``workspace_root`` identifies the GF Wordbench workspace that owns the
    canonical state file. An explicit ``state_path`` is reserved for tests and
    documented portable or diagnostic invocations.
    """

    workspace_root: Path
    state_path: Path | None = None
    create_alternate_parent: bool = False
    quarantine_invalid: bool = False

    def __post_init__(self) -> None:
        if type(self.create_alternate_parent) is not bool:
            raise TypeError("create_alternate_parent must be a bool")
        if type(self.quarantine_invalid) is not bool:
            raise TypeError("quarantine_invalid must be a bool")

        workspace = _require_absolute_path(
            self.workspace_root,
            role="workspace_root",
        )
        workspace = require_directory(
            workspace,
            role="GF Wordbench workspace",
        )
        object.__setattr__(self, "workspace_root", workspace)

        if self.state_path is not None:
            explicit = _require_absolute_path(
                self.state_path,
                role="state_path",
            )
            if explicit.name != CANONICAL_STATE_FILENAME:
                raise ValueError(
                    "an alternate state path must retain the canonical filename "
                    f"{CANONICAL_STATE_FILENAME!r}"
                )
            object.__setattr__(self, "state_path", explicit)

        _reject_run_owned_path(self.resolved_state_path, workspace)

    @property
    def resolved_state_path(self) -> Path:
        """Return the explicit or workspace-owned state destination."""

        if self.state_path is not None:
            return resolve_for_output(self.state_path)

        return resolve_for_output(
            self.workspace_root / CANONICAL_STATE_FILENAME
        )

    @property
    def legacy_state_path(self) -> Path:
        """Return the read-only legacy state path beside the active state."""

        return self.resolved_state_path.with_name(LEGACY_STATE_FILENAME)

    def load(self) -> AppState:
        """Load validated state or return safe canonical defaults."""

        return self.load_with_diagnostics().state

    def load_with_diagnostics(self) -> StateLoadResult:
        """Load state and expose bounded diagnostics for bootstrap or UI use."""

        state_path = self.resolved_state_path
        if state_path.exists():
            return self._load_canonical(state_path)

        legacy_path = self.legacy_state_path
        if legacy_path.exists():
            return self._migrate_legacy(legacy_path)

        diagnostics = (
            StateDiagnostic(
                StateDiagnosticCode.MISSING,
                "application state is absent; canonical defaults were used",
                state_path,
            ),
        )
        _log_diagnostics(
            diagnostics,
            operation="load",
            state_path=state_path,
        )
        return StateLoadResult(
            state=default_app_state(),
            source_path=state_path,
            diagnostics=diagnostics,
            migrated=False,
        )

    def save(self, state: AppState) -> Path:
        """Validate and atomically replace the canonical state document."""

        state_path = self.resolved_state_path

        # Invalid typed state is a caller/schema error, not an I/O failure.
        validate_app_state(state)
        document = serialize_app_state(
            state,
            producer_version=__version__,
        )
        payload = _canonical_json_bytes(document)

        try:
            destination = atomic_write_bytes(
                state_path,
                payload,
                root=self._write_root(state_path),
                create_parents=self._may_create_parent(state_path),
                validator=self._validate_candidate,
                role="application state",
            )
        except StateWriteError:
            raise
        except Exception as exc:
            diagnostic = StateDiagnostic(
                StateDiagnosticCode.WRITE_FAILED,
                f"application state could not be written: {type(exc).__name__}",
                state_path,
            )
            _log_diagnostics(
                (diagnostic,),
                operation="save",
                state_path=state_path,
            )
            raise _state_write_error(
                "application state could not be written atomically",
                state_path,
            ) from exc

        _LOG.info(
            "application state saved",
            extra={
                "state_path": str(destination),
                "schema_id": APP_STATE_SCHEMA_ID,
                "schema_version": APP_STATE_SCHEMA_VERSION,
                "operation": "save",
            },
        )
        return destination

    def reset(
        self,
        *,
        replace_with_defaults: bool = False,
    ) -> Path | None:
        """Clear convenience state without touching projects, runs, or templates."""

        if type(replace_with_defaults) is not bool:
            raise TypeError("replace_with_defaults must be a bool")

        if replace_with_defaults:
            return self.save(default_app_state())

        state_path = self.resolved_state_path
        existed = state_path.exists()

        try:
            unlink_file(
                state_path,
                missing_ok=True,
                root=self._write_root(state_path),
                role="application state",
            )
        except StateWriteError:
            raise
        except Exception as exc:
            raise _state_write_error(
                "application state could not be reset",
                state_path,
            ) from exc

        return state_path if existed else None

    def _load_canonical(
        self,
        state_path: Path,
    ) -> StateLoadResult:
        try:
            document = _read_json_object(state_path)
        except (
            InfrastructureError,
            OSError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.MALFORMED,
                "application state is unreadable or malformed: "
                f"{type(exc).__name__}",
                quarantine=True,
            )

        if document.get("schema_id") != APP_STATE_SCHEMA_ID:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.SCHEMA_MISMATCH,
                "state schema identifier is not gf-wordbench.app-state",
                quarantine=False,
            )

        source_major = _schema_major(document.get("schema_version"))
        if source_major is None:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.MALFORMED,
                "state schema version must use MAJOR.MINOR",
                quarantine=True,
            )

        if source_major != _SUPPORTED_SCHEMA_MAJOR:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.VERSION_UNSUPPORTED,
                f"state schema major version {source_major} is unsupported",
                quarantine=False,
            )

        try:
            state, warnings = parse_app_state(
                document,
                strict=False,
                source=state_path,
            )
        except UnsupportedVersionError as exc:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.VERSION_UNSUPPORTED,
                str(exc),
                quarantine=False,
            )
        except (
            SchemaValidationError,
            TypeError,
            ValueError,
        ) as exc:
            return self._fallback_from_invalid_file(
                state_path,
                StateDiagnosticCode.MALFORMED,
                f"state schema validation failed: {type(exc).__name__}",
                quarantine=True,
            )

        diagnostics = _loaded_diagnostics(
            warnings,
            state_path=state_path,
        )
        _log_diagnostics(
            diagnostics,
            operation="load",
            state_path=state_path,
        )
        return StateLoadResult(
            state=state,
            source_path=state_path,
            diagnostics=diagnostics,
            migrated=False,
        )

    def _migrate_legacy(
        self,
        legacy_path: Path,
    ) -> StateLoadResult:
        state_path = self.resolved_state_path

        try:
            legacy_document = _read_json_object(legacy_path)
            migration = migrate_legacy_state(
                legacy_document,
                canonical_defaults=default_app_state_document(),
            )
            state, schema_warnings = parse_app_state(
                migration.payload,
                strict=False,
                source=legacy_path,
            )
            validate_app_state(state)
            self.save(state)

            verified = self._load_canonical(state_path)
            if not _is_successful_load(verified):
                raise ValueError(
                    "migrated canonical state failed verification"
                )
        except Exception as exc:
            diagnostics = (
                StateDiagnostic(
                    StateDiagnosticCode.MALFORMED,
                    "legacy state migration failed; defaults were used: "
                    f"{type(exc).__name__}",
                    legacy_path,
                ),
            )
            _log_diagnostics(
                diagnostics,
                operation="migrate",
                state_path=legacy_path,
            )
            return StateLoadResult(
                state=default_app_state(),
                source_path=state_path,
                diagnostics=diagnostics,
                migrated=False,
            )

        warning_messages = (
            *_migration_warning_messages(migration),
            *schema_warnings,
        )
        diagnostics = (
            StateDiagnostic(
                StateDiagnosticCode.MIGRATED,
                "legacy application state was migrated to the canonical schema",
                legacy_path,
            ),
            *_partial_diagnostics(
                warning_messages,
                source_path=legacy_path,
            ),
        )
        _log_diagnostics(
            diagnostics,
            operation="migrate",
            state_path=state_path,
        )
        return StateLoadResult(
            state=verified.state,
            source_path=state_path,
            diagnostics=diagnostics,
            migrated=True,
        )

    def _fallback_from_invalid_file(
        self,
        state_path: Path,
        code: StateDiagnosticCode,
        message: str,
        *,
        quarantine: bool,
    ) -> StateLoadResult:
        diagnostics: list[StateDiagnostic] = [
            StateDiagnostic(code, message, state_path)
        ]

        if quarantine and self.quarantine_invalid:
            quarantined = self._quarantine(state_path)
            if quarantined is not None:
                diagnostics.append(
                    StateDiagnostic(
                        StateDiagnosticCode.QUARANTINED,
                        "invalid state bytes were copied to a quarantine artifact",
                        quarantined,
                    )
                )

        result = tuple(diagnostics)
        _log_diagnostics(
            result,
            operation="load",
            state_path=state_path,
        )
        return StateLoadResult(
            state=default_app_state(),
            source_path=state_path,
            diagnostics=result,
            migrated=False,
        )

    def _quarantine(
        self,
        state_path: Path,
    ) -> Path | None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        quarantine_path = state_path.with_name(
            f".gf_wordbench_state.invalid-{stamp}.json"
        )

        try:
            return copy_file(
                state_path,
                quarantine_path,
                overwrite=False,
                create_parents=False,
                source_root=state_path.parent,
                destination_root=state_path.parent,
                role="invalid application state quarantine",
            )
        except Exception:
            _LOG.warning(
                "application state quarantine failed",
                extra={
                    "state_path": str(state_path),
                    "operation": "quarantine",
                },
                exc_info=True,
            )
            return None

    def _validate_candidate(
        self,
        candidate: Path,
    ) -> None:
        document = _read_json_object(candidate)
        state, warnings = parse_app_state(
            document,
            strict=True,
            source=candidate,
        )
        if warnings:
            rendered = str(candidate)
            raise SchemaValidationError(
                "candidate canonical state required field recovery",
                subject=rendered,
                evidence_paths=(rendered,),
            )

        validate_app_state(state)

    def _write_root(
        self,
        state_path: Path,
    ) -> Path:
        if self.state_path is None:
            return self.workspace_root

        if state_path.parent.exists():
            return require_directory(
                state_path.parent,
                role="alternate application-state parent",
            )

        if not self.create_alternate_parent:
            raise FileNotFoundError(
                "alternate application-state parent does not exist: "
                f"{state_path.parent}"
            )

        return _nearest_existing_directory(state_path.parent)

    def _may_create_parent(
        self,
        state_path: Path,
    ) -> bool:
        return (
            self.state_path is not None
            and self.create_alternate_parent
            and not state_path.parent.exists()
        )


def load_app_state(
    workspace_root: Path,
    *,
    state_path: Path | None = None,
    quarantine_invalid: bool = False,
) -> AppState:
    """Load application state from a canonical or explicit path."""

    return StateRepository(
        workspace_root=workspace_root,
        state_path=state_path,
        quarantine_invalid=quarantine_invalid,
    ).load()


def save_app_state(
    state: AppState,
    workspace_root: Path,
    *,
    state_path: Path | None = None,
    create_alternate_parent: bool = False,
) -> Path:
    """Atomically save validated application state."""

    return StateRepository(
        workspace_root=workspace_root,
        state_path=state_path,
        create_alternate_parent=create_alternate_parent,
    ).save(state)


def _read_json_object(path: Path) -> JsonObject:
    raw = read_bytes(
        path,
        root=path.parent,
        role="application state",
    )
    text = raw.decode(UTF8)
    if not text.strip():
        raise ValueError("application state is empty")

    value = json.loads(
        text,
        parse_constant=_reject_non_json_number,
        object_pairs_hook=_object_without_duplicates,
    )
    if not isinstance(value, dict):
        raise TypeError(
            "application state root must be a JSON object"
        )
    if not all(isinstance(key, str) for key in value):
        raise TypeError(
            "application state object keys must be strings"
        )

    return cast(JsonObject, value)


def _canonical_json_bytes(
    document: Mapping[str, object],
) -> bytes:
    return dumps_canonical_json(document).encode(UTF8)


def _object_without_duplicates(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(
                f"duplicate JSON object key is prohibited: {key!r}"
            )
        result[key] = value

    return result


def _reject_non_json_number(value: str) -> Never:
    raise ValueError(
        f"non-JSON numeric constant is prohibited: {value}"
    )


def _schema_major(value: object) -> int | None:
    if not isinstance(value, str):
        return None

    major, separator, minor = value.partition(".")
    if (
        separator != "."
        or not major
        or not minor
        or not major.isascii()
        or not minor.isascii()
        or not major.isdecimal()
        or not minor.isdecimal()
    ):
        return None

    return int(major)


def _require_absolute_path(
    path: Path,
    *,
    role: str,
) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{role} must be pathlib.Path")
    if not path.is_absolute():
        raise ValueError(f"{role} must be absolute")

    return path


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            raise FileNotFoundError(
                f"no existing ancestor for alternate state path: {path}"
            )
        candidate = parent

    return require_directory(
        candidate,
        role="alternate application-state containment root",
    )


def _reject_run_owned_path(
    state_path: Path,
    workspace_root: Path,
) -> None:
    runs_root = resolve_for_output(workspace_root / "runs")
    candidate = resolve_for_output(state_path)
    if candidate == runs_root or candidate.is_relative_to(runs_root):
        raise ValueError(
            "application state must not be stored inside runs/"
        )


def _loaded_diagnostics(
    warnings: tuple[str, ...],
    *,
    state_path: Path,
) -> tuple[StateDiagnostic, ...]:
    if not warnings:
        return (
            StateDiagnostic(
                StateDiagnosticCode.LOADED,
                "application state loaded",
                state_path,
            ),
        )

    return _partial_diagnostics(
        warnings,
        source_path=state_path,
    )


def _partial_diagnostics(
    warnings: tuple[str, ...],
    *,
    source_path: Path,
) -> tuple[StateDiagnostic, ...]:
    return tuple(
        StateDiagnostic(
            StateDiagnosticCode.PARTIALLY_DEFAULTED,
            warning,
            source_path,
        )
        for warning in warnings
    )


def _migration_warning_messages(
    migration: LegacyStateMigration,
) -> tuple[str, ...]:
    return tuple(
        f"{warning.field}: {warning.message}"
        for warning in migration.warnings
    )


def _is_successful_load(result: StateLoadResult) -> bool:
    successful_codes = {
        StateDiagnosticCode.LOADED,
        StateDiagnosticCode.PARTIALLY_DEFAULTED,
    }
    return any(
        diagnostic.code in successful_codes
        for diagnostic in result.diagnostics
    )


def _state_write_error(
    message: str,
    path: Path,
) -> StateWriteError:
    rendered = str(path)
    return StateWriteError(
        message,
        subject=rendered,
        evidence_paths=(rendered,),
    )


def _log_diagnostics(
    diagnostics: tuple[StateDiagnostic, ...],
    *,
    operation: str,
    state_path: Path,
) -> None:
    for diagnostic in diagnostics:
        level = (
            logging.INFO
            if diagnostic.code
            in {
                StateDiagnosticCode.LOADED,
                StateDiagnosticCode.MIGRATED,
            }
            else logging.WARNING
        )
        _LOG.log(
            level,
            diagnostic.message,
            extra={
                "state_path": str(state_path),
                "schema_id": APP_STATE_SCHEMA_ID,
                "schema_version": APP_STATE_SCHEMA_VERSION,
                "operation": operation,
                "state_diagnostic": diagnostic.code.value,
            },
        )


__all__ = (
    "CANONICAL_STATE_FILENAME",
    "LEGACY_STATE_FILENAME",
    "StateRepository",
    "load_app_state",
    "save_app_state",
)