"""Pure migration of legacy ``gf-audit`` application state.

The canonical state schema owns identity, defaults, validation, serialization,
and version support. This module only converts the supported unversioned flat
legacy representation into the current path-resolved canonical payload supplied
by that schema.

No filesystem operation is performed here. Publication, atomic replacement,
verification, and preservation of the legacy source belong to the state
repository.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

_CANONICAL_GROUPS: Final[tuple[str, ...]] = (
    "environment",
    "selection",
    "last_run",
)

_LEGACY_PATH_FIELDS: Final[dict[str, tuple[str, str, bool]]] = {
    "selected_scan_dir": (
        "environment",
        "last_selected_language_path",
        True,
    ),
    "selected_rgl_root": ("environment", "last_rgl_root", True),
    "selected_gf_exe": ("environment", "gf_executable", True),
    "selected_out_root": ("environment", "output_root", True),
    "selected_target_file": ("selection", "target_file", False),
    "last_run_dir": ("last_run", "run_dir", True),
    "last_summary_path": ("last_run", "summary_path", True),
}

_LEGACY_PROJECT_ROOT_FIELD: Final[str] = "selected_project_root"

_LEGACY_PATH_NOTICES: Final[dict[str, tuple[str, str]]] = {
    "selected_scan_dir": (
        "legacy_scan_dir_mapped_to_language_candidate",
        "Legacy scan directory was retained as a selected-language-path candidate "
        "and must be revalidated before use.",
    ),
    "selected_rgl_root": (
        "legacy_rgl_root_mapped_to_hint",
        "Legacy RGL root was retained as a path-resolution hint and must be "
        "revalidated against the selected language path.",
    ),
}

_LEGACY_BOOLEAN_FIELDS: Final[dict[str, tuple[str, str]]] = {
    "selected_keep_ok_details": ("selection", "keep_ok_details"),
    "selected_diff_previous": ("selection", "diff_previous"),
    "selected_skip_version_probe": ("selection", "skip_version_probe"),
    "selected_no_compile": ("selection", "no_compile"),
    "selected_emit_cpu_stats": ("selection", "emit_cpu_stats"),
}

_LEGACY_INTEGER_FIELDS: Final[dict[str, tuple[str, str, int]]] = {
    "selected_timeout_sec": ("selection", "timeout_sec", 1),
    "selected_max_files": ("selection", "max_files", 0),
}

_DISCARDED_LEGACY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "selected_scan_glob",
        "selected_gf_path",
        "selected_include_regex",
        "selected_exclude_regex",
        "is_running",
        "current_run_config",
        "current_run_result",
        "language",
        "language_name",
        "language_code",
        "project_id",
        "project_name",
        "project_registry",
        "last_language_id",
        "selected_language_id",
        "catalog_path",
        "last_catalog_entry",
        "resolved_language_context",
        "audit_results",
        "file_results",
        "scenario_results",
    }
)

_RECOGNIZED_LEGACY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        *_LEGACY_PATH_FIELDS,
        _LEGACY_PROJECT_ROOT_FIELD,
        *_LEGACY_BOOLEAN_FIELDS,
        *_LEGACY_INTEGER_FIELDS,
        "selected_mode",
        "status_message",
        *_DISCARDED_LEGACY_FIELDS,
    }
)

_CANONICAL_MODES: Final[frozenset[str]] = frozenset(
    {"quick", "checkpoint", "diagnostic", "release"}
)
_LEGACY_MODE_ALIASES: Final[dict[str, str]] = {
    "file": "quick",
    "all": "diagnostic",
}
_LEGACY_TRUE_STRINGS: Final[frozenset[str]] = frozenset(
    {"1", "true", "yes", "on"}
)
_LEGACY_FALSE_STRINGS: Final[frozenset[str]] = frozenset(
    {"0", "false", "no", "off"}
)
_INTEGER_TEXT: Final[re.Pattern[str]] = re.compile(r"^[+-]?\d+$")
_DEFAULT_STATUS_MESSAGE_LIMIT: Final[int] = 512


class StateMigrationError(ValueError):
    """Raised when a legacy state cannot be migrated safely."""


@dataclass(frozen=True, slots=True)
class StateMigrationWarning:
    """One bounded, machine-readable warning produced during migration."""

    code: str
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class LegacyStateMigration:
    """Deterministic result of converting one legacy flat state object."""

    payload: JsonObject
    warnings: tuple[StateMigrationWarning, ...]
    consumed_fields: tuple[str, ...]
    discarded_fields: tuple[str, ...]
    unknown_fields: tuple[str, ...]


@dataclass(slots=True)
class _MigrationBuilder:
    payload: JsonObject
    warnings: list[StateMigrationWarning]
    consumed: set[str]
    discarded: set[str]

    def set_value(self, group: str, field: str, value: JsonValue) -> None:
        group_value = self.payload.get(group)
        if not isinstance(group_value, dict):
            raise StateMigrationError(
                f"Canonical defaults group {group!r} must be a JSON object"
            )
        if field not in group_value:
            raise StateMigrationError(
                f"Canonical defaults group {group!r} is missing field {field!r}"
            )
        group_value[field] = value

    def warn(self, code: str, field: str, message: str) -> None:
        self.warnings.append(
            StateMigrationWarning(code=code, field=field, message=message)
        )


def migrate_legacy_state(
    legacy_state: Mapping[str, object],
    *,
    canonical_defaults: Mapping[str, object],
    status_message_limit: int = _DEFAULT_STATUS_MESSAGE_LIMIT,
) -> LegacyStateMigration:
    """Convert a supported flat legacy state into a canonical state payload.

    ``canonical_defaults`` must be produced by the canonical state schema. The
    mapping is deep-copied before legacy values are applied, so neither input is
    mutated. Invalid legacy convenience values retain their canonical default
    and produce a bounded warning. Unknown fields are ignored. Fields whose
    authority belongs to the resolved language context, validation-profile
    policy, runtime execution, or run evidence are discarded and never copied into
    the canonical payload. Migrated paths remain untrusted convenience candidates.
    """

    if not isinstance(legacy_state, Mapping):
        raise StateMigrationError("Legacy application state must be a JSON object")
    if "schema_id" in legacy_state or "schema_version" in legacy_state:
        raise StateMigrationError(
            "Versioned state must be handled by the canonical state reader"
        )
    if isinstance(status_message_limit, bool) or not isinstance(
        status_message_limit, int
    ):
        raise TypeError("status_message_limit must be an integer")
    if status_message_limit < 1:
        raise ValueError("status_message_limit must be greater than zero")

    payload = _copy_canonical_defaults(canonical_defaults)
    builder = _MigrationBuilder(
        payload=payload,
        warnings=[],
        consumed=set(),
        discarded=set(),
    )

    _migrate_paths(legacy_state, builder)
    _migrate_project_root_candidate(legacy_state, builder)
    _migrate_mode(legacy_state, builder)
    _migrate_integers(legacy_state, builder)
    _migrate_booleans(legacy_state, builder)
    _migrate_status_message(
        legacy_state,
        builder,
        limit=status_message_limit,
    )
    _record_discarded_fields(legacy_state, builder)

    source_fields = {key for key in legacy_state if isinstance(key, str)}
    unknown_fields = tuple(
        sorted(source_fields.difference(_RECOGNIZED_LEGACY_FIELDS))
    )

    return LegacyStateMigration(
        payload=payload,
        warnings=tuple(builder.warnings),
        consumed_fields=tuple(sorted(builder.consumed)),
        discarded_fields=tuple(sorted(builder.discarded)),
        unknown_fields=unknown_fields,
    )


def _copy_canonical_defaults(defaults: Mapping[str, object]) -> JsonObject:
    if not isinstance(defaults, Mapping):
        raise StateMigrationError("Canonical state defaults must be a JSON object")

    copied = _copy_json_mapping(defaults, path=())
    for group in _CANONICAL_GROUPS:
        if not isinstance(copied.get(group), dict):
            raise StateMigrationError(
                f"Canonical state defaults are missing object group {group!r}"
            )
    return copied


def _copy_json_mapping(
    value: Mapping[object, object],
    *,
    path: tuple[str, ...],
) -> JsonObject:
    copied: JsonObject = {}
    for key, child in value.items():
        if not isinstance(key, str) or not key:
            raise StateMigrationError(
                f"Canonical default key at {_display_path(path)} must be a "
                "non-empty string"
            )
        copied[key] = _copy_json_value(child, path=(*path, key))
    return copied


def _copy_json_value(value: object, *, path: tuple[str, ...]) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise StateMigrationError(
                f"Canonical default at {_display_path(path)} is not finite"
            )
        return value

    if isinstance(value, Mapping):
        return _copy_json_mapping(value, path=path)

    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray, memoryview)
    ):
        return [
            _copy_json_value(child, path=(*path, f"[{index}]"))
            for index, child in enumerate(value)
        ]

    raise StateMigrationError(
        f"Canonical default at {_display_path(path)} is not JSON-compatible: "
        f"{type(value).__name__}"
    )


def _migrate_paths(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    for legacy_key, (group, field, nullable) in _LEGACY_PATH_FIELDS.items():
        if legacy_key not in legacy_state:
            continue

        builder.consumed.add(legacy_key)
        value = legacy_state[legacy_key]
        normalized = _coerce_legacy_path(value, nullable=nullable)
        if normalized is _INVALID:
            builder.warn(
                "invalid_legacy_path",
                legacy_key,
                "Legacy path was ignored and the canonical default was retained.",
            )
            continue
        builder.set_value(group, field, normalized)
        notice = _LEGACY_PATH_NOTICES.get(legacy_key)
        if notice is not None and normalized is not None:
            code, message = notice
            builder.warn(code, legacy_key, message)


def _migrate_project_root_candidate(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    key = _LEGACY_PROJECT_ROOT_FIELD
    if key not in legacy_state:
        return

    builder.consumed.add(key)
    normalized = _coerce_legacy_path(legacy_state[key], nullable=True)
    if normalized is _INVALID:
        builder.warn(
            "invalid_legacy_project_root",
            key,
            "Legacy project root was ignored and the canonical default was retained.",
        )
        return
    if normalized is None:
        return

    candidate = _legacy_project_profile_candidate(normalized)
    builder.set_value(
        "environment",
        "last_selected_validation_profile",
        candidate,
    )
    builder.warn(
        "legacy_project_root_mapped_to_profile_candidate",
        key,
        "Legacy project root was converted to a validation-profile candidate and "
        "must be resolved explicitly and checked against the selected language.",
    )


def _migrate_mode(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    key = "selected_mode"
    if key not in legacy_state:
        return

    builder.consumed.add(key)
    raw = legacy_state[key]
    if not isinstance(raw, str):
        builder.set_value("selection", "mode", "diagnostic")
        builder.warn(
            "invalid_legacy_mode",
            key,
            "Legacy mode was not text and was replaced with 'diagnostic'.",
        )
        return

    normalized = raw.strip().casefold()
    if normalized in _LEGACY_MODE_ALIASES:
        builder.set_value("selection", "mode", _LEGACY_MODE_ALIASES[normalized])
        return
    if normalized in _CANONICAL_MODES:
        builder.set_value("selection", "mode", normalized)
        return

    builder.set_value("selection", "mode", "diagnostic")
    builder.warn(
        "unknown_legacy_mode",
        key,
        "Unknown legacy mode was replaced with 'diagnostic'.",
    )


def _migrate_integers(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    for legacy_key, (group, field, minimum) in _LEGACY_INTEGER_FIELDS.items():
        if legacy_key not in legacy_state:
            continue

        builder.consumed.add(legacy_key)
        raw = legacy_state[legacy_key]
        coerced = _coerce_legacy_integer(raw)
        if coerced is None or coerced < minimum:
            builder.warn(
                "invalid_legacy_integer",
                legacy_key,
                "Legacy integer was ignored and the canonical default was retained.",
            )
            continue

        if not isinstance(raw, int) or isinstance(raw, bool):
            builder.warn(
                "coerced_legacy_integer",
                legacy_key,
                "Legacy integer text was converted to a canonical integer.",
            )
        builder.set_value(group, field, coerced)


def _migrate_booleans(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    for legacy_key, (group, field) in _LEGACY_BOOLEAN_FIELDS.items():
        if legacy_key not in legacy_state:
            continue

        builder.consumed.add(legacy_key)
        raw = legacy_state[legacy_key]
        coerced = _coerce_legacy_boolean(raw)
        if coerced is None:
            builder.warn(
                "invalid_legacy_boolean",
                legacy_key,
                "Legacy boolean was ignored and the canonical default was retained.",
            )
            continue

        if not isinstance(raw, bool):
            builder.warn(
                "coerced_legacy_boolean",
                legacy_key,
                "Legacy boolean alias was converted to a canonical boolean.",
            )
        builder.set_value(group, field, coerced)


def _migrate_status_message(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
    *,
    limit: int,
) -> None:
    key = "status_message"
    if key not in legacy_state:
        return

    builder.consumed.add(key)
    raw = legacy_state[key]
    if not isinstance(raw, str):
        builder.warn(
            "invalid_legacy_status_message",
            key,
            "Legacy status message was ignored because it was not text.",
        )
        return

    normalized = " ".join(raw.split())
    if len(normalized) > limit:
        normalized = normalized[:limit].rstrip()
        builder.warn(
            "truncated_legacy_status_message",
            key,
            "Legacy status message was truncated to the configured safe limit.",
        )
    builder.set_value("last_run", "status_message", normalized)


def _record_discarded_fields(
    legacy_state: Mapping[str, object],
    builder: _MigrationBuilder,
) -> None:
    for key in sorted(_DISCARDED_LEGACY_FIELDS):
        if key not in legacy_state:
            continue
        builder.discarded.add(key)
        builder.warn(
            "discarded_legacy_field",
            key,
            "Legacy field is runtime-only or owned by the resolved language "
            "context, validation-profile policy, or run evidence.",
        )


def _coerce_legacy_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if _INTEGER_TEXT.fullmatch(text) is not None:
            try:
                return int(text, 10)
            except ValueError:
                return None
    return None


def _coerce_legacy_boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in _LEGACY_TRUE_STRINGS:
            return True
        if normalized in _LEGACY_FALSE_STRINGS:
            return False
    return None


class _InvalidValue:
    __slots__ = ()


_INVALID: Final[_InvalidValue] = _InvalidValue()


def _legacy_project_profile_candidate(project_root: str) -> str:
    normalized = project_root.rstrip("/")
    suffix = "/project/project.toml"
    if normalized.casefold().endswith(suffix.casefold()):
        return normalized
    if normalized == "":
        return suffix.removeprefix("/")
    return f"{normalized}{suffix}"


def _coerce_legacy_path(
    value: object,
    *,
    nullable: bool,
) -> str | None | _InvalidValue:
    if value is None:
        return None if nullable else ""
    if not isinstance(value, str):
        return _INVALID
    if any(ord(character) < 32 for character in value):
        return _INVALID
    if value == "":
        return None if nullable else ""
    return value.replace("\\", "/")


def _display_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"


__all__ = (
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "LegacyStateMigration",
    "StateMigrationError",
    "StateMigrationWarning",
    "migrate_legacy_state",
)
