"""Canonical typed schema for ``.gf_wordbench_state.json``.

This module owns state defaults, tolerant parsing, strict validation, and
conversion between immutable state models and their canonical JSON document.
Filesystem persistence remains owned by :mod:`gf_wordbench.state.repository`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Never, NotRequired, TypedDict, cast

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode

from .models import AppState, EnvironmentState, LastRunState, SelectionState

APP_STATE_SCHEMA_ID: Final = "gf-wordbench.app-state"
APP_STATE_SCHEMA_VERSION: Final = "1.0"
APP_STATE_FILENAME: Final = ".gf_wordbench_state.json"
LEGACY_APP_STATE_FILENAME: Final = ".gf_audit_state.json"
PRODUCER_NAME: Final = "gf-wordbench"

DEFAULT_MODE: Final = ValidationMode.DIAGNOSTIC
DEFAULT_TIMEOUT_SEC: Final = 60
DEFAULT_MAX_FILES: Final = 0
DEFAULT_KEEP_OK_DETAILS: Final = False
DEFAULT_DIFF_PREVIOUS: Final = True
DEFAULT_SKIP_VERSION_PROBE: Final = False
DEFAULT_NO_COMPILE: Final = False
DEFAULT_EMIT_CPU_STATS: Final = False

MAX_STATE_WARNINGS: Final = 32
CANONICAL_MODES: Final = frozenset(mode.value for mode in ValidationMode)

_SCHEMA_VERSION_PATTERN: Final = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
_CURRENT_SCHEMA_MAJOR: Final = 1
_CURRENT_SCHEMA_MINOR: Final = 0
_NUL: Final = "\x00"
_MISSING: Final = object()

_ENVIRONMENT_REFERENCE_PATTERNS: Final = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[^{}]+\}"),
    re.compile(r"(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*"),
)

_ROOT_FIELDS: Final = frozenset(
    {
        "schema_id",
        "schema_version",
        "producer",
        "environment",
        "selection",
        "last_run",
    }
)
_REQUIRED_ROOT_FIELDS: Final = frozenset(
    {
        "schema_id",
        "schema_version",
        "environment",
        "selection",
        "last_run",
    }
)
_PRODUCER_FIELDS: Final = frozenset({"name", "version"})
_ENVIRONMENT_FIELDS: Final = frozenset(
    {
        "project_root",
        "rgl_root",
        "gf_executable",
        "output_root",
    }
)
_SELECTION_FIELDS: Final = frozenset(
    {
        "mode",
        "target_file",
        "timeout_sec",
        "max_files",
        "keep_ok_details",
        "diff_previous",
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
    }
)
_LAST_RUN_FIELDS: Final = frozenset(
    {
        "run_dir",
        "summary_path",
        "status_message",
    }
)


class ProducerDocument(TypedDict):
    name: str
    version: str


class EnvironmentDocument(TypedDict):
    project_root: str | None
    rgl_root: str | None
    gf_executable: str | None
    output_root: str | None


class SelectionDocument(TypedDict):
    mode: str
    target_file: str
    timeout_sec: int
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool


class LastRunDocument(TypedDict):
    run_dir: str | None
    summary_path: str | None
    status_message: str


class AppStateDocument(TypedDict):
    schema_id: str
    schema_version: str
    producer: NotRequired[ProducerDocument]
    environment: EnvironmentDocument
    selection: SelectionDocument
    last_run: LastRunDocument


@dataclass(frozen=True, slots=True)
class StateSchemaWarning:
    """One non-fatal field recovery or compatibility decision."""

    code: str
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class StateSchemaResult:
    """Recovered document and compatibility metadata for its source."""

    document: AppStateDocument
    warnings: tuple[StateSchemaWarning, ...]
    source_schema_version: str | None
    compatible: bool
    rewrite_safe: bool


def default_app_state() -> AppState:
    """Return a fresh immutable application-state default."""

    return AppState(
        schema_id=APP_STATE_SCHEMA_ID,
        schema_version=APP_STATE_SCHEMA_VERSION,
        producer=None,
        environment=EnvironmentState(
            project_root=None,
            rgl_root=None,
            gf_executable=None,
            output_root=None,
        ),
        selection=SelectionState(
            mode=DEFAULT_MODE,
            target_file="",
            timeout_sec=DEFAULT_TIMEOUT_SEC,
            max_files=DEFAULT_MAX_FILES,
            keep_ok_details=DEFAULT_KEEP_OK_DETAILS,
            diff_previous=DEFAULT_DIFF_PREVIOUS,
            skip_version_probe=DEFAULT_SKIP_VERSION_PROBE,
            no_compile=DEFAULT_NO_COMPILE,
            emit_cpu_stats=DEFAULT_EMIT_CPU_STATS,
        ),
        last_run=LastRunState(
            run_dir=None,
            summary_path=None,
            status_message="",
        ),
    )


def parse_app_state(
    document: object,
    *,
    strict: bool = False,
    source: Path | None = None,
) -> tuple[AppState, tuple[str, ...]]:
    """Parse untrusted JSON into typed state and bounded recovery warnings.

    Strict parsing requires the exact current schema, all canonical fields, and
    producer metadata. Tolerant parsing recovers known fields from compatible
    schema versions and defaults malformed values.
    """

    if strict:
        if not isinstance(document, Mapping):
            _StrictContext(source).fail("$", "must be a JSON object")

        canonical = canonicalize_app_state_document(
            cast(Mapping[str, object], document),
            source=source,
            require_producer=True,
        )
        state = _document_to_state(canonical)
        validate_app_state(state, require_producer=True)
        return state, ()

    result = recover_app_state_document(document, source=source)
    if not result.compatible:
        _raise_incompatible(result, source=source)

    state = _document_to_state(result.document)
    validate_app_state(state)

    warnings = tuple(
        f"{warning.field}: {warning.message}"
        for warning in result.warnings
    )
    return state, warnings


def serialize_app_state(
    state: AppState,
    *,
    producer_version: str | None = None,
) -> AppStateDocument:
    """Return the canonical JSON document for a validated typed state."""

    validate_app_state(state)

    producer = (
        state.producer
        if producer_version is None
        else ProducerInfo(
            name=PRODUCER_NAME,
            version=producer_version,
        )
    )
    if producer is None:
        raise SchemaValidationError(
            "producer_version is required when state.producer is absent"
        )
    if producer.name != PRODUCER_NAME:
        raise SchemaValidationError(
            f"producer name must be {PRODUCER_NAME!r}"
        )

    return canonicalize_app_state_document(
        _state_to_document(state, producer=producer),
        require_producer=True,
    )


def validate_app_state(
    state: AppState,
    *,
    require_producer: bool = False,
) -> None:
    """Validate an ``AppState`` before canonical persistence."""

    if not isinstance(state, AppState):
        raise TypeError("state must be an AppState")

    canonicalize_app_state_document(
        _state_to_document(state),
        require_producer=require_producer,
    )


def default_app_state_document() -> AppStateDocument:
    """Return the canonical default document without producer metadata."""

    return _state_to_document(default_app_state())


def recover_app_state_document(
    document: object,
    *,
    source: Path | None = None,
) -> StateSchemaResult:
    """Recover supported canonical values from untrusted parsed JSON."""

    del source

    warnings: list[StateSchemaWarning] = []
    root = _recover_mapping(document, "$", warnings)
    if root is None:
        return _failure(warnings)

    schema_id = root.get("schema_id")
    if schema_id != APP_STATE_SCHEMA_ID:
        _warn(
            warnings,
            "schema_id_mismatch",
            "$.schema_id",
            "state identity is unsupported",
        )
        return _failure(warnings)

    schema_version = root.get("schema_version")
    if not isinstance(schema_version, str):
        _warn(
            warnings,
            "invalid_schema_version",
            "$.schema_version",
            "expected MAJOR.MINOR",
        )
        return _failure(warnings)

    parsed = _parse_version(schema_version)
    if parsed is None:
        _warn(
            warnings,
            "invalid_schema_version",
            "$.schema_version",
            "expected MAJOR.MINOR",
        )
        return _failure(warnings, schema_version)

    major, minor = parsed
    if major != _CURRENT_SCHEMA_MAJOR:
        _warn(
            warnings,
            "unsupported_schema_major",
            "$.schema_version",
            f"schema major {major} is unsupported",
        )
        return _failure(warnings, schema_version)

    future_minor = minor > _CURRENT_SCHEMA_MINOR
    if future_minor:
        _warn(
            warnings,
            "future_schema_minor",
            "$.schema_version",
            "known fields were recovered; automatic rewrite is unsafe",
        )

    state = default_app_state_document()

    producer = _recover_producer(root, warnings)
    if producer is not None:
        state["producer"] = producer

    state["environment"] = _recover_environment(root, warnings)
    state["selection"] = _recover_selection(root, warnings)
    state["last_run"] = _recover_last_run(root, warnings)

    return StateSchemaResult(
        document=state,
        warnings=tuple(warnings),
        source_schema_version=schema_version,
        compatible=True,
        rewrite_safe=not future_minor,
    )


def canonicalize_app_state_document(
    document: Mapping[str, object],
    *,
    source: Path | None = None,
    require_producer: bool = True,
) -> AppStateDocument:
    """Validate and normalize a document before canonical persistence."""

    context = _StrictContext(source)
    root = _strict_mapping(document, "$", context)

    required_root = _REQUIRED_ROOT_FIELDS | (
        frozenset({"producer"})
        if require_producer
        else frozenset()
    )

    _strict_shape(
        root,
        _ROOT_FIELDS,
        required_root,
        "$",
        context,
    )
    _strict_shape_group(
        root,
        "environment",
        _ENVIRONMENT_FIELDS,
        context,
    )
    _strict_shape_group(
        root,
        "selection",
        _SELECTION_FIELDS,
        context,
    )
    _strict_shape_group(
        root,
        "last_run",
        _LAST_RUN_FIELDS,
        context,
    )

    if "producer" in root:
        _strict_shape_group(
            root,
            "producer",
            _PRODUCER_FIELDS,
            context,
        )

    schema_id = root["schema_id"]
    if schema_id != APP_STATE_SCHEMA_ID:
        context.fail(
            "$.schema_id",
            f"must be {APP_STATE_SCHEMA_ID!r}",
        )

    schema_version = root["schema_version"]
    if schema_version != APP_STATE_SCHEMA_VERSION:
        parsed = (
            _parse_version(schema_version)
            if isinstance(schema_version, str)
            else None
        )
        if parsed is not None and parsed[0] != _CURRENT_SCHEMA_MAJOR:
            context.unsupported(
                "$.schema_version",
                f"schema major {parsed[0]} is unsupported",
            )
        context.fail(
            "$.schema_version",
            f"must be {APP_STATE_SCHEMA_VERSION!r}",
        )

    result = recover_app_state_document(root, source=source)
    if not result.compatible:
        context.fail(
            "$",
            "document is not compatible application state",
        )

    if result.warnings:
        warning = result.warnings[0]
        context.fail(warning.field, warning.message)

    if require_producer and "producer" not in result.document:
        context.fail(
            "$.producer",
            "is required for persisted output",
        )

    return result.document


def producer_document(version: str) -> ProducerDocument:
    """Build producer metadata through the canonical owning model."""

    producer = ProducerInfo(
        name=PRODUCER_NAME,
        version=version,
    )
    return ProducerDocument(
        name=producer.name,
        version=producer.version,
    )


def _state_to_document(
    state: AppState,
    *,
    producer: ProducerInfo | None = None,
) -> AppStateDocument:
    selected_producer = (
        state.producer
        if producer is None
        else producer
    )

    document = AppStateDocument(
        schema_id=state.schema_id,
        schema_version=state.schema_version,
        environment=EnvironmentDocument(
            project_root=_portable_optional_path(
                state.environment.project_root
            ),
            rgl_root=_portable_optional_path(
                state.environment.rgl_root
            ),
            gf_executable=_portable_optional_path(
                state.environment.gf_executable
            ),
            output_root=_portable_optional_path(
                state.environment.output_root
            ),
        ),
        selection=SelectionDocument(
            mode=state.selection.mode.value,
            target_file=_portable_path(
                state.selection.target_file
            ),
            timeout_sec=state.selection.timeout_sec,
            max_files=state.selection.max_files,
            keep_ok_details=state.selection.keep_ok_details,
            diff_previous=state.selection.diff_previous,
            skip_version_probe=state.selection.skip_version_probe,
            no_compile=state.selection.no_compile,
            emit_cpu_stats=state.selection.emit_cpu_stats,
        ),
        last_run=LastRunDocument(
            run_dir=_portable_optional_path(
                state.last_run.run_dir
            ),
            summary_path=_portable_optional_path(
                state.last_run.summary_path
            ),
            status_message=state.last_run.status_message,
        ),
    )

    if selected_producer is not None:
        document["producer"] = ProducerDocument(
            name=selected_producer.name,
            version=selected_producer.version,
        )

    return document


def _document_to_state(
    document: AppStateDocument,
) -> AppState:
    producer_value = document.get("producer")
    producer = (
        None
        if producer_value is None
        else ProducerInfo(
            name=producer_value["name"],
            version=producer_value["version"],
        )
    )

    environment = document["environment"]
    selection = document["selection"]
    last_run = document["last_run"]

    return AppState(
        schema_id=document["schema_id"],
        schema_version=document["schema_version"],
        producer=producer,
        environment=EnvironmentState(
            project_root=environment["project_root"],
            rgl_root=environment["rgl_root"],
            gf_executable=environment["gf_executable"],
            output_root=environment["output_root"],
        ),
        selection=SelectionState(
            mode=ValidationMode(selection["mode"]),
            target_file=selection["target_file"],
            timeout_sec=selection["timeout_sec"],
            max_files=selection["max_files"],
            keep_ok_details=selection["keep_ok_details"],
            diff_previous=selection["diff_previous"],
            skip_version_probe=selection["skip_version_probe"],
            no_compile=selection["no_compile"],
            emit_cpu_stats=selection["emit_cpu_stats"],
        ),
        last_run=LastRunState(
            run_dir=last_run["run_dir"],
            summary_path=last_run["summary_path"],
            status_message=last_run["status_message"],
        ),
    )


def _recover_producer(
    root: Mapping[str, object],
    warnings: list[StateSchemaWarning],
) -> ProducerDocument | None:
    value = root.get("producer", _MISSING)
    if value is _MISSING:
        return None

    group = _recover_mapping(
        value,
        "$.producer",
        warnings,
    )
    if group is None:
        return None

    name = _field(
        group,
        "name",
        "$.producer.name",
        warnings,
    )
    version = _field(
        group,
        "version",
        "$.producer.version",
        warnings,
    )

    if (
        name != PRODUCER_NAME
        or not isinstance(version, str)
        or not version
        or _NUL in version
    ):
        _warn(
            warnings,
            "invalid_producer",
            "$.producer",
            "producer was ignored",
        )
        return None

    producer = ProducerInfo(
        name=PRODUCER_NAME,
        version=version,
    )
    return ProducerDocument(
        name=producer.name,
        version=producer.version,
    )


def _recover_environment(
    root: Mapping[str, object],
    warnings: list[StateSchemaWarning],
) -> EnvironmentDocument:
    group = _group(
        root,
        "environment",
        warnings,
    )
    return EnvironmentDocument(
        project_root=_optional_path(
            group,
            "project_root",
            "$.environment",
            warnings,
        ),
        rgl_root=_optional_path(
            group,
            "rgl_root",
            "$.environment",
            warnings,
        ),
        gf_executable=_optional_path(
            group,
            "gf_executable",
            "$.environment",
            warnings,
        ),
        output_root=_optional_path(
            group,
            "output_root",
            "$.environment",
            warnings,
        ),
    )


def _recover_selection(
    root: Mapping[str, object],
    warnings: list[StateSchemaWarning],
) -> SelectionDocument:
    group = _group(
        root,
        "selection",
        warnings,
    )

    mode = _field(
        group,
        "mode",
        "$.selection.mode",
        warnings,
    )
    if mode not in CANONICAL_MODES:
        if mode is not _MISSING:
            _warn(
                warnings,
                "invalid_mode",
                "$.selection.mode",
                f"defaulted to {DEFAULT_MODE.value}",
            )
        mode = DEFAULT_MODE.value

    return SelectionDocument(
        mode=cast(str, mode),
        target_file=_target_path(
            group,
            "target_file",
            "$.selection",
            warnings,
        ),
        timeout_sec=_integer(
            group,
            "timeout_sec",
            "$.selection",
            DEFAULT_TIMEOUT_SEC,
            positive=True,
            warnings=warnings,
        ),
        max_files=_integer(
            group,
            "max_files",
            "$.selection",
            DEFAULT_MAX_FILES,
            positive=False,
            warnings=warnings,
        ),
        keep_ok_details=_boolean(
            group,
            "keep_ok_details",
            "$.selection",
            DEFAULT_KEEP_OK_DETAILS,
            warnings,
        ),
        diff_previous=_boolean(
            group,
            "diff_previous",
            "$.selection",
            DEFAULT_DIFF_PREVIOUS,
            warnings,
        ),
        skip_version_probe=_boolean(
            group,
            "skip_version_probe",
            "$.selection",
            DEFAULT_SKIP_VERSION_PROBE,
            warnings,
        ),
        no_compile=_boolean(
            group,
            "no_compile",
            "$.selection",
            DEFAULT_NO_COMPILE,
            warnings,
        ),
        emit_cpu_stats=_boolean(
            group,
            "emit_cpu_stats",
            "$.selection",
            DEFAULT_EMIT_CPU_STATS,
            warnings,
        ),
    )


def _recover_last_run(
    root: Mapping[str, object],
    warnings: list[StateSchemaWarning],
) -> LastRunDocument:
    group = _group(
        root,
        "last_run",
        warnings,
    )

    message = _field(
        group,
        "status_message",
        "$.last_run.status_message",
        warnings,
    )
    if not isinstance(message, str) or _NUL in message:
        if message is not _MISSING:
            _warn(
                warnings,
                "invalid_string",
                "$.last_run.status_message",
                "defaulted",
            )
        message = ""

    return LastRunDocument(
        run_dir=_optional_path(
            group,
            "run_dir",
            "$.last_run",
            warnings,
        ),
        summary_path=_optional_path(
            group,
            "summary_path",
            "$.last_run",
            warnings,
        ),
        status_message=message,
    )


def _group(
    root: Mapping[str, object],
    key: str,
    warnings: list[StateSchemaWarning],
) -> Mapping[str, object]:
    field = f"$.{key}"
    value = _field(
        root,
        key,
        field,
        warnings,
    )
    group = _recover_mapping(
        value,
        field,
        warnings,
        warn=False,
    )
    if group is None:
        if value is not _MISSING:
            _warn(
                warnings,
                "invalid_group",
                field,
                "group defaulted",
            )
        return {}

    return group


def _field(
    group: Mapping[str, object],
    key: str,
    field: str,
    warnings: list[StateSchemaWarning],
) -> object:
    if key in group:
        return group[key]

    _warn(
        warnings,
        "missing_field",
        field,
        "field defaulted",
    )
    return _MISSING


def _optional_path(
    group: Mapping[str, object],
    key: str,
    parent: str,
    warnings: list[StateSchemaWarning],
) -> str | None:
    field = f"{parent}.{key}"
    value = _field(
        group,
        key,
        field,
        warnings,
    )

    if value is _MISSING or value is None or value == "":
        return None

    if not isinstance(value, str) or not _valid_path_text(value):
        _warn(
            warnings,
            "invalid_path",
            field,
            "defaulted to null",
        )
        return None

    normalized = _normalize_path(value)
    if normalized != value:
        _warn(
            warnings,
            "normalized_path",
            field,
            "path separators were normalized",
        )

    return normalized


def _target_path(
    group: Mapping[str, object],
    key: str,
    parent: str,
    warnings: list[StateSchemaWarning],
) -> str:
    field = f"{parent}.{key}"
    value = _field(
        group,
        key,
        field,
        warnings,
    )

    if value is _MISSING or value == "":
        return ""

    if not isinstance(value, str) or not _valid_path_text(value):
        _warn(
            warnings,
            "invalid_path",
            field,
            "defaulted to empty",
        )
        return ""

    normalized = _normalize_path(value)
    if normalized != value:
        _warn(
            warnings,
            "normalized_path",
            field,
            "path separators were normalized",
        )

    return normalized


def _integer(
    group: Mapping[str, object],
    key: str,
    parent: str,
    default: int,
    *,
    positive: bool,
    warnings: list[StateSchemaWarning],
) -> int:
    field = f"{parent}.{key}"
    value = _field(
        group,
        key,
        field,
        warnings,
    )

    valid = (
        type(value) is int
        and (
            value > 0
            if positive
            else value >= 0
        )
    )
    if valid:
        return cast(int, value)

    if value is not _MISSING:
        _warn(
            warnings,
            "invalid_integer",
            field,
            f"defaulted to {default}",
        )

    return default


def _boolean(
    group: Mapping[str, object],
    key: str,
    parent: str,
    default: bool,
    warnings: list[StateSchemaWarning],
) -> bool:
    field = f"{parent}.{key}"
    value = _field(
        group,
        key,
        field,
        warnings,
    )

    if type(value) is bool:
        return cast(bool, value)

    if value is not _MISSING:
        _warn(
            warnings,
            "invalid_boolean",
            field,
            f"defaulted to {default!r}",
        )

    return default


def _recover_mapping(
    value: object,
    field: str,
    warnings: list[StateSchemaWarning],
    *,
    warn: bool = True,
) -> Mapping[str, object] | None:
    if (
        isinstance(value, Mapping)
        and all(isinstance(key, str) for key in value)
    ):
        return cast(Mapping[str, object], value)

    if warn:
        _warn(
            warnings,
            "invalid_object",
            field,
            "expected a JSON object",
        )

    return None


def _strict_shape_group(
    root: Mapping[str, object],
    key: str,
    fields: frozenset[str],
    context: _StrictContext,
) -> None:
    group = _strict_mapping(
        root[key],
        f"$.{key}",
        context,
    )
    _strict_shape(
        group,
        fields,
        fields,
        f"$.{key}",
        context,
    )


def _strict_mapping(
    value: object,
    field: str,
    context: _StrictContext,
) -> Mapping[str, object]:
    if (
        not isinstance(value, Mapping)
        or not all(isinstance(key, str) for key in value)
    ):
        context.fail(
            field,
            "must be an object with string keys",
        )

    return cast(Mapping[str, object], value)


def _strict_shape(
    group: Mapping[str, object],
    allowed: frozenset[str],
    required: frozenset[str],
    field: str,
    context: _StrictContext,
) -> None:
    missing = required.difference(group)
    if missing:
        context.fail(
            field,
            "missing required fields: "
            + ", ".join(sorted(missing)),
        )

    unknown = set(group).difference(allowed)
    if unknown:
        context.fail(
            field,
            "unknown fields: "
            + ", ".join(sorted(unknown)),
        )


def _valid_path_text(value: str) -> bool:
    if (
        not value
        or _NUL in value
        or value == "~"
        or value.startswith(("~/", "~\\"))
    ):
        return False

    return not any(
        pattern.search(value)
        for pattern in _ENVIRONMENT_REFERENCE_PATTERNS
    )


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def _portable_optional_path(
    value: str | None,
) -> str | None:
    return (
        None
        if value is None
        else _portable_path(value)
    )


def _portable_path(value: str) -> str:
    if value == "":
        return ""

    if not _valid_path_text(value):
        raise SchemaValidationError(
            "state contains an unsafe path value"
        )

    return _normalize_path(value)


def _raise_incompatible(
    result: StateSchemaResult,
    *,
    source: Path | None,
) -> Never:
    warning = (
        result.warnings[0]
        if result.warnings
        else None
    )
    message = (
        "application state is incompatible"
        if warning is None
        else f"{warning.field}: {warning.message}"
    )
    location = (
        f"{source}: "
        if source is not None
        else ""
    )

    if (
        warning is not None
        and warning.code == "unsupported_schema_major"
    ):
        raise UnsupportedVersionError(location + message)

    raise SchemaValidationError(location + message)


def _parse_version(
    value: str,
) -> tuple[int, int] | None:
    match = _SCHEMA_VERSION_PATTERN.fullmatch(value)
    if match is None:
        return None

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def _warn(
    warnings: list[StateSchemaWarning],
    code: str,
    field: str,
    message: str,
) -> None:
    if len(warnings) < MAX_STATE_WARNINGS:
        warnings.append(
            StateSchemaWarning(
                code=code,
                field=field,
                message=message,
            )
        )
    elif warnings[-1].code != "warnings_truncated":
        warnings[-1] = StateSchemaWarning(
            code="warnings_truncated",
            field="$",
            message="additional recovery warnings were omitted",
        )


def _failure(
    warnings: list[StateSchemaWarning],
    source_schema_version: str | None = None,
) -> StateSchemaResult:
    return StateSchemaResult(
        document=default_app_state_document(),
        warnings=tuple(warnings),
        source_schema_version=source_schema_version,
        compatible=False,
        rewrite_safe=False,
    )


@dataclass(frozen=True, slots=True)
class _StrictContext:
    source: Path | None

    def fail(
        self,
        field: str,
        message: str,
    ) -> Never:
        location = (
            f"{self.source}: "
            if self.source is not None
            else ""
        )
        raise SchemaValidationError(
            f"{location}{field}: {message}"
        )

    def unsupported(
        self,
        field: str,
        message: str,
    ) -> Never:
        location = (
            f"{self.source}: "
            if self.source is not None
            else ""
        )
        raise UnsupportedVersionError(
            f"{location}{field}: {message}"
        )


__all__ = (
    "APP_STATE_FILENAME",
    "APP_STATE_SCHEMA_ID",
    "APP_STATE_SCHEMA_VERSION",
    "AppStateDocument",
    "CANONICAL_MODES",
    "EnvironmentDocument",
    "LEGACY_APP_STATE_FILENAME",
    "LastRunDocument",
    "MAX_STATE_WARNINGS",
    "ProducerDocument",
    "SelectionDocument",
    "StateSchemaResult",
    "StateSchemaWarning",
    "canonicalize_app_state_document",
    "default_app_state",
    "default_app_state_document",
    "parse_app_state",
    "producer_document",
    "recover_app_state_document",
    "serialize_app_state",
    "validate_app_state",
)