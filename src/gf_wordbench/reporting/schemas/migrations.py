"""Read-only migrations for persisted reporting schemas."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.version import __version__

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

RUN_SUMMARY_SCHEMA_ID: Final = "gf-wordbench.run-summary"
RUN_SUMMARY_SCHEMA_VERSION: Final = "1.0"
ARTIFACT_MANIFEST_SCHEMA_ID: Final = "gf-wordbench.artifact-manifest"
ARTIFACT_MANIFEST_SCHEMA_VERSION: Final = "1.0"
PRODUCER_NAME: Final = "gf-wordbench"
SUMMARY_MIGRATION_ID: Final = "gf-audit-summary-v0-to-gf-wordbench-run-summary-v1"
MANIFEST_MIGRATION_ID: Final = "legacy-run-to-gf-wordbench-artifact-manifest-v1"

_SUMMARY_ROOT_FIELDS: Final = frozenset(
    {
        "schema_id",
        "schema_version",
        "producer",
        "metadata",
        "totals",
        "artifacts",
        "file_results",
        "scenario_results",
        "diff_entries",
        "top_errors",
    }
)
_METADATA_FIELDS: Final[tuple[str, ...]] = (
    "run_id",
    "run_dir",
    "started_at",
    "finished_at",
    "duration_ms",
    "gf_version",
    "mode",
    "target_file",
    "project_id",
    "project_name",
    "project_root",
    "rgl_root",
    "gf_executable",
    "output_root",
    "source_directory",
    "source_glob",
    "gf_path",
    "timeout_sec",
    "max_files",
    "skip_version_probe",
    "no_compile",
    "emit_cpu_stats",
    "keep_ok_details",
    "diff_previous",
)
_TOTAL_FIELDS: Final[tuple[str, ...]] = (
    "files_seen",
    "files_included",
    "files_excluded",
    "files_ok",
    "files_fail",
    "files_error",
    "files_skipped",
    "direct_fail",
    "downstream_fail",
    "ambiguous_fail",
    "excluded_noise",
    "scenarios_seen",
    "scenarios_ok",
    "scenarios_fail",
    "scenarios_error",
    "scenarios_skipped",
    "required_scenario_fail",
)
_ARTIFACT_FIELDS: Final[tuple[str, ...]] = (
    "summary_json",
    "summary_markdown",
    "ai_ready",
    "top_errors",
    "manifest",
    "master_log",
    "all_scan_logs",
    "all_logs",
    "details_dir",
    "raw_dir",
    "compile_logs_dir",
    "scan_logs_dir",
    "scenario_logs_dir",
    "artifacts_dir",
    "gfo_dir",
    "out_dir",
    "pgf_dir",
)
_DEFAULT_ARTIFACTS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "summary_json": "summary.json",
        "summary_markdown": "summary.md",
        "ai_ready": "AI_READY.md",
        "top_errors": "top_errors.txt",
        "manifest": "manifest.json",
        "master_log": "raw/master.log",
        "all_scan_logs": "raw/ALL_SCAN_LOGS.TXT",
        "all_logs": "raw/ALL_LOGS.TXT",
        "details_dir": "details",
        "raw_dir": "raw",
        "compile_logs_dir": "raw/compile",
        "scan_logs_dir": "raw/scan",
        "scenario_logs_dir": "raw/scenarios",
        "artifacts_dir": "artifacts",
        "gfo_dir": "artifacts/gfo",
        "out_dir": "artifacts/out",
        "pgf_dir": "artifacts/pgf",
    }
)
_MODE_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {"file": "quick", "all": "diagnostic"}
)
_CANONICAL_MODES: Final = frozenset({"quick", "checkpoint", "release", "diagnostic"})
_CANONICAL_STATUSES: Final = frozenset({"OK", "FAIL", "ERROR", "SKIPPED"})
_CANONICAL_OVERALL_STATUSES: Final = frozenset({"OK", "FAIL", "ERROR"})
_CANONICAL_DIAGNOSTIC_CLASSES: Final = frozenset(
    {"ok", "direct", "downstream", "ambiguous", "noise", "skipped", "framework_error"}
)
_CANONICAL_ERROR_KINDS: Final = frozenset(
    {
        "OK",
        "OTHER",
        "TYPE",
        "SYNTAX",
        "INTERNAL",
        "TIMEOUT",
        "SCRIPT",
        "CONFIG",
        "IO",
        "TOOL",
        "CONTRACT",
        "ARTIFACT",
        "NORMALIZATION",
        "GOLD",
        "CANCELLED",
        "OUTPUT_LIMIT",
    }
)
_MANIFEST_ROLES: Final = frozenset(
    {
        "machine_summary",
        "human_summary",
        "ai_handoff",
        "top_errors",
        "master_log",
        "aggregate_log",
        "scan_log",
        "compile_stdout",
        "compile_stderr",
        "scenario_stdout",
        "scenario_stderr",
        "scenario_output",
        "detail",
        "gfo",
        "pgf",
        "other",
    }
)
_ROLE_BY_ARTIFACT_FIELD: Final[Mapping[str, str]] = MappingProxyType(
    {
        "summary_json": "machine_summary",
        "summary_markdown": "human_summary",
        "ai_ready": "ai_handoff",
        "top_errors": "top_errors",
        "master_log": "master_log",
        "all_scan_logs": "aggregate_log",
        "all_logs": "aggregate_log",
    }
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE: Final = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_DRIVE_RE: Final = re.compile(r"^[A-Za-z]:")


@unique
class MigrationStatus(StrEnum):
    NOT_NEEDED = "not_needed"
    MIGRATED = "migrated"
    MIGRATED_WITH_WARNINGS = "migrated_with_warnings"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


@unique
class SummaryShape(StrEnum):
    CURRENT = "current"
    NESTED_UNVERSIONED = "nested_unversioned"
    FLAT_UNVERSIONED = "flat_unversioned"
    UNSUPPORTED_VERSIONED = "unsupported_versioned"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MigrationResult:
    migration_id: str
    source_schema: str
    source_version: str
    target_schema: str
    target_version: str
    source_path: str
    destination_path: str | None
    status: MigrationStatus
    warnings: tuple[str, ...]
    losses: tuple[str, ...]
    changed: bool
    written: bool
    backup_path: str | None


@dataclass(frozen=True, slots=True)
class DocumentMigration:
    result: MigrationResult
    document: Mapping[str, JsonValue] | None

    def __post_init__(self) -> None:
        if self.document is not None and not isinstance(self.document, Mapping):
            raise TypeError("document must be a mapping or None")


class _Recorder:
    __slots__ = ("warnings", "losses")

    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.losses: list[str] = []

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def lose(self, message: str) -> None:
        if message not in self.losses:
            self.losses.append(message)


def detect_summary_shape(document: Mapping[str, object]) -> SummaryShape:
    _require_mapping(document, "document")
    schema_id = document.get("schema_id")
    schema_version = document.get("schema_version")
    if schema_id is not None or schema_version is not None:
        if schema_id == RUN_SUMMARY_SCHEMA_ID and _supported_v1(schema_version):
            return SummaryShape.CURRENT
        return SummaryShape.UNSUPPORTED_VERSIONED
    if any(key in document for key in ("metadata", "totals", "artifacts")):
        return SummaryShape.NESTED_UNVERSIONED
    flat_markers = {
        "run_config",
        "run_paths",
        "started_at",
        "finished_at",
        "duration_ms",
        "gf_version",
        "file_results",
        "top_errors",
        "ok",
        "fail",
    }
    if flat_markers.intersection(document):
        return SummaryShape.FLAT_UNVERSIONED
    return SummaryShape.UNKNOWN


def migrate_summary_document(
    document: Mapping[str, object],
    *,
    source_path: str = "",
    destination_path: str | None = None,
    run_root: Path | None = None,
    project_root: Path | None = None,
    producer_version: str = __version__,
    strict: bool = False,
) -> DocumentMigration:
    _require_mapping(document, "document")
    if type(strict) is not bool:
        raise TypeError("strict must be a bool")
    run_root = _optional_absolute_path(run_root, "run_root")
    project_root = _optional_absolute_path(project_root, "project_root")
    shape = detect_summary_shape(document)

    if shape is SummaryShape.CURRENT:
        copied = _json_object(document, "document")
        return DocumentMigration(
            result=_result(
                migration_id=SUMMARY_MIGRATION_ID,
                source_schema=RUN_SUMMARY_SCHEMA_ID,
                source_version=str(document.get("schema_version", "1.0")),
                target_schema=RUN_SUMMARY_SCHEMA_ID,
                target_version=RUN_SUMMARY_SCHEMA_VERSION,
                source_path=source_path,
                destination_path=destination_path,
                status=MigrationStatus.NOT_NEEDED,
                changed=False,
            ),
            document=MappingProxyType(copied),
        )

    if shape in {SummaryShape.UNSUPPORTED_VERSIONED, SummaryShape.UNKNOWN}:
        reason = (
            "unsupported versioned run-summary document"
            if shape is SummaryShape.UNSUPPORTED_VERSIONED
            else "unrecognized legacy run-summary shape"
        )
        return DocumentMigration(
            result=_result(
                migration_id=SUMMARY_MIGRATION_ID,
                source_schema=str(document.get("schema_id", "unversioned")),
                source_version=str(document.get("schema_version", "0")),
                target_schema=RUN_SUMMARY_SCHEMA_ID,
                target_version=RUN_SUMMARY_SCHEMA_VERSION,
                source_path=source_path,
                destination_path=destination_path,
                status=MigrationStatus.BLOCKED,
                changed=False,
                losses=(reason,),
            ),
            document=None,
        )

    recorder = _Recorder()
    recorder.warn(f"Migrated {shape.value} run summary to {RUN_SUMMARY_SCHEMA_ID}/1.0.")
    source = _json_object(document, "document")

    if shape is SummaryShape.NESTED_UNVERSIONED:
        metadata_source = _mapping_or_empty(source.get("metadata"), "metadata", recorder)
        totals_source = _mapping_or_empty(source.get("totals"), "totals", recorder)
        artifacts_source = _mapping_or_empty(source.get("artifacts"), "artifacts", recorder)
    else:
        metadata_source = _merge_flat_metadata(source, recorder)
        totals_source = _merge_flat_totals(source)
        artifacts_source = _merge_flat_artifacts(source)

    metadata = _migrate_metadata(
        metadata_source,
        source,
        run_root=run_root,
        project_root=project_root,
        recorder=recorder,
        strict=strict,
    )
    totals = _migrate_totals(totals_source, recorder=recorder, strict=strict)
    artifacts = _migrate_artifact_map(
        artifacts_source,
        run_root=run_root,
        recorder=recorder,
    )
    file_results = _migrate_file_results(
        source.get("file_results", []),
        run_root=run_root,
        project_root=project_root,
        recorder=recorder,
        strict=strict,
    )
    scenario_results = _migrate_scenario_results(
        source.get("scenario_results"),
        run_root=run_root,
        project_root=project_root,
        recorder=recorder,
        strict=strict,
    )
    diff_entries = _migrate_diff_entries(
        source.get("diff_entries", []),
        recorder=recorder,
        strict=strict,
    )
    top_errors = _migrate_top_errors(
        source.get("top_errors", []),
        recorder=recorder,
        strict=strict,
    )

    canonical: JsonObject = {
        "schema_id": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "producer": {"name": PRODUCER_NAME, "version": _nonempty_text(producer_version, "producer_version")},
        "metadata": metadata,
        "totals": totals,
        "artifacts": artifacts,
        "file_results": file_results,
        "scenario_results": scenario_results,
        "diff_entries": diff_entries,
        "top_errors": top_errors,
    }

    unknown = sorted(set(source).difference(_SUMMARY_ROOT_FIELDS).difference(_legacy_summary_root_fields()))
    if unknown:
        recorder.warn("Ignored undocumented legacy root fields: " + ", ".join(unknown) + ".")

    if strict and recorder.losses:
        status = MigrationStatus.BLOCKED
        migrated_document: Mapping[str, JsonValue] | None = None
    else:
        status = (
            MigrationStatus.MIGRATED_WITH_WARNINGS
            if recorder.warnings or recorder.losses
            else MigrationStatus.MIGRATED
        )
        migrated_document = MappingProxyType(canonical)

    return DocumentMigration(
        result=_result(
            migration_id=SUMMARY_MIGRATION_ID,
            source_schema="gf-audit.run-summary" if shape is SummaryShape.FLAT_UNVERSIONED else "unversioned.run-summary",
            source_version="0",
            target_schema=RUN_SUMMARY_SCHEMA_ID,
            target_version=RUN_SUMMARY_SCHEMA_VERSION,
            source_path=source_path,
            destination_path=destination_path,
            status=status,
            warnings=tuple(recorder.warnings),
            losses=tuple(recorder.losses),
            changed=True,
        ),
        document=migrated_document,
    )


def migrate_summary_v0_to_v1(
    document: Mapping[str, object],
    **kwargs: object,
) -> Mapping[str, JsonValue]:
    migrated = migrate_summary_document(document, **kwargs)
    if migrated.document is None:
        detail = "; ".join(migrated.result.losses) or "summary migration was blocked"
        raise ValueError(detail)
    return migrated.document


def migrate_manifest_document(
    document: Mapping[str, object] | None,
    *,
    run_root: Path,
    run_id: str,
    source_path: str = "",
    destination_path: str | None = None,
    generated_at: datetime | str | None = None,
    producer_version: str = __version__,
    artifact_paths: Iterable[str] | None = None,
    required_paths: Iterable[str] = (),
    role_by_path: Mapping[str, str] | None = None,
    created_by_by_path: Mapping[str, str] | None = None,
    strict: bool = True,
) -> DocumentMigration:
    if document is not None:
        _require_mapping(document, "document")
        if (
            document.get("schema_id") == ARTIFACT_MANIFEST_SCHEMA_ID
            and _supported_v1(document.get("schema_version"))
        ):
            copied = _json_object(document, "document")
            return DocumentMigration(
                result=_result(
                    migration_id=MANIFEST_MIGRATION_ID,
                    source_schema=ARTIFACT_MANIFEST_SCHEMA_ID,
                    source_version=str(document.get("schema_version", "1.0")),
                    target_schema=ARTIFACT_MANIFEST_SCHEMA_ID,
                    target_version=ARTIFACT_MANIFEST_SCHEMA_VERSION,
                    source_path=source_path,
                    destination_path=destination_path,
                    status=MigrationStatus.NOT_NEEDED,
                    changed=False,
                ),
                document=MappingProxyType(copied),
            )

    if type(strict) is not bool:
        raise TypeError("strict must be a bool")
    root = _required_absolute_directory(run_root, "run_root")
    canonical_run_id = _nonempty_text(run_id, "run_id")
    recorder = _Recorder()
    source = {} if document is None else _json_object(document, "document")

    paths = _manifest_candidate_paths(source, artifact_paths, recorder)
    required = frozenset(_portable_run_path(value, run_root=root, recorder=recorder, field="required path") for value in required_paths)
    roles = _normalized_string_map(role_by_path or {}, root, recorder, "role_by_path")
    producers = _normalized_string_map(created_by_by_path or {}, root, recorder, "created_by_by_path")

    entries: list[JsonValue] = []
    seen: set[str] = set()
    for raw_path in paths:
        relative = _portable_run_path(raw_path, run_root=root, recorder=recorder, field="artifact path")
        if not relative:
            continue
        if relative == "manifest.json":
            recorder.lose("The manifest cannot contain itself as an artifact entry.")
            continue
        folded = relative.casefold()
        if folded in seen:
            recorder.lose(f"Duplicate artifact path after normalization: {relative}.")
            continue
        seen.add(folded)
        resolved = (root / PurePosixPath(relative)).resolve(strict=False)
        if not _is_relative_to(resolved, root):
            recorder.lose(f"Artifact path escapes the run root: {relative}.")
            continue
        if not resolved.exists():
            recorder.lose(f"Historical artifact is missing: {relative}.")
            continue
        if not resolved.is_file() or resolved.is_symlink():
            recorder.lose(f"Manifest migration accepts regular non-symlink files only: {relative}.")
            continue

        legacy_entry = _legacy_manifest_entry(source, raw_path, relative)
        role = roles.get(relative) or _entry_text(legacy_entry, "role") or _infer_role(relative)
        if role not in _MANIFEST_ROLES:
            recorder.warn(f"Unknown legacy role for {relative!r} was mapped to 'other'.")
            role = "other"
        required_value = relative in required
        if legacy_entry is not None and isinstance(legacy_entry.get("required"), bool):
            required_value = bool(legacy_entry["required"])
        created_by = producers.get(relative) or _entry_text(legacy_entry, "created_by") or "migration"

        entries.append(
            {
                "path": relative,
                "role": role,
                "media_type": _media_type(relative),
                "required": required_value,
                "size_bytes": resolved.stat().st_size,
                "sha256": _sha256_file(resolved),
                "created_by": created_by,
            }
        )

    entries.sort(key=lambda item: str(item["path"]) if isinstance(item, dict) else "")
    timestamp = _canonical_timestamp(generated_at)
    canonical: JsonObject = {
        "schema_id": ARTIFACT_MANIFEST_SCHEMA_ID,
        "schema_version": ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "producer": {"name": PRODUCER_NAME, "version": _nonempty_text(producer_version, "producer_version")},
        "run_id": canonical_run_id,
        "generated_at": timestamp,
        "hash_algorithm": "sha256",
        "artifacts": entries,
    }

    if strict and recorder.losses:
        status = MigrationStatus.BLOCKED
        migrated_document: Mapping[str, JsonValue] | None = None
    else:
        status = (
            MigrationStatus.MIGRATED_WITH_WARNINGS
            if recorder.warnings or recorder.losses
            else MigrationStatus.MIGRATED
        )
        migrated_document = MappingProxyType(canonical)

    return DocumentMigration(
        result=_result(
            migration_id=MANIFEST_MIGRATION_ID,
            source_schema=str(source.get("schema_id", "absent_or_legacy_manifest")),
            source_version=str(source.get("schema_version", "0")),
            target_schema=ARTIFACT_MANIFEST_SCHEMA_ID,
            target_version=ARTIFACT_MANIFEST_SCHEMA_VERSION,
            source_path=source_path,
            destination_path=destination_path,
            status=status,
            warnings=tuple(recorder.warnings),
            losses=tuple(recorder.losses),
            changed=True,
        ),
        document=migrated_document,
    )


def migrate_manifest_v0_to_v1(
    document: Mapping[str, object] | None,
    **kwargs: object,
) -> Mapping[str, JsonValue]:
    migrated = migrate_manifest_document(document, **kwargs)
    if migrated.document is None:
        detail = "; ".join(migrated.result.losses) or "manifest migration was blocked"
        raise ValueError(detail)
    return migrated.document


def _migrate_metadata(
    nested: Mapping[str, object],
    root: Mapping[str, object],
    *,
    run_root: Path | None,
    project_root: Path | None,
    recorder: _Recorder,
    strict: bool,
) -> JsonObject:
    metadata: JsonObject = {}
    for field in _METADATA_FIELDS:
        value = nested.get(field, root.get(field))
        metadata[field] = _metadata_value(field, value, run_root, project_root, recorder, strict)

    if not metadata["run_id"] and isinstance(metadata["run_dir"], str):
        name = PureWindowsPath(metadata["run_dir"]).name
        if name.startswith("run_") and len(name) > 4:
            metadata["run_id"] = name[4:]
            recorder.warn("Recovered run_id from the legacy run directory name.")

    for required_text in (
        "run_id",
        "run_dir",
        "started_at",
        "finished_at",
        "gf_version",
        "project_id",
        "project_name",
        "project_root",
        "rgl_root",
        "gf_executable",
        "output_root",
        "source_directory",
        "source_glob",
    ):
        if not metadata[required_text]:
            recorder.lose(f"Mandatory metadata field {required_text!r} could not be recovered.")

    return metadata


def _metadata_value(
    field: str,
    value: object,
    run_root: Path | None,
    project_root: Path | None,
    recorder: _Recorder,
    strict: bool,
) -> JsonValue:
    if field == "mode":
        if value is None:
            recorder.lose("Mandatory metadata field 'mode' could not be recovered.")
            return "diagnostic"
        mode = str(value).strip().lower()
        if mode in _MODE_ALIASES:
            recorder.warn(f"Mapped legacy mode {mode!r} to {_MODE_ALIASES[mode]!r}.")
            return _MODE_ALIASES[mode]
        if mode not in _CANONICAL_MODES:
            recorder.lose(f"Unknown legacy validation mode: {value!r}.")
            return "diagnostic"
        return mode
    if field == "target_file":
        if value in (None, ""):
            return None
        return _portable_project_path(value, project_root, recorder, field)
    if field == "source_directory":
        if value is None:
            return ""
        return _portable_project_path(value, project_root, recorder, field)
    if field == "gf_path":
        if value is None:
            return []
        if isinstance(value, str):
            recorder.warn("Converted scalar legacy gf_path to an ordered array.")
            values = [value]
        elif isinstance(value, Iterable) and not isinstance(value, (bytes, Mapping)):
            values = list(value)
        else:
            recorder.lose("Legacy gf_path has an invalid type.")
            return []
        result: list[JsonValue] = []
        seen: set[str] = set()
        for item in values:
            text = _path_text(item)
            if text is None:
                recorder.lose("Legacy gf_path contains a non-path value.")
                continue
            normalized = text.replace("\\", "/")
            if normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result
    if field in {"duration_ms", "timeout_sec", "max_files"}:
        default = 0
        integer = _coerce_nonnegative_int(value, field, recorder, default=default)
        if field == "duration_ms" and value is None:
            started = None
            finished = None
            if started is not None and finished is not None:
                return max(0, int((finished - started).total_seconds() * 1000))
        return integer
    if field in {
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
        "keep_ok_details",
        "diff_previous",
    }:
        return _coerce_bool(value, field, recorder, default=False)
    if field in {"started_at", "finished_at"}:
        if value is None:
            return ""
        try:
            return _canonical_timestamp(value)
        except (TypeError, ValueError):
            recorder.lose(f"Legacy timestamp {field!r} is invalid or timezone-naive.")
            return ""
    if field == "run_dir":
        if value is None and run_root is not None:
            return run_root.as_posix()
        return "" if value is None else _path_text(value).replace("\\", "/") if _path_text(value) else ""
    if field == "project_root":
        if value is None and project_root is not None:
            return project_root.as_posix()
        return "" if value is None else _path_text(value).replace("\\", "/") if _path_text(value) else ""
    if field in {"rgl_root", "gf_executable", "output_root"}:
        text = _path_text(value)
        return "" if text is None else text.replace("\\", "/")
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value) if not isinstance(value, str) else value
    recorder.lose(f"Legacy metadata field {field!r} has an invalid type.")
    return ""


def _migrate_totals(
    source: Mapping[str, object],
    *,
    recorder: _Recorder,
    strict: bool,
) -> JsonObject:
    aliases = {"ok": "files_ok", "fail": "files_fail", "error": "files_error", "skipped": "files_skipped"}
    values: dict[str, int] = {}
    for field in _TOTAL_FIELDS:
        raw = source.get(field)
        if raw is None:
            legacy = next((key for key, target in aliases.items() if target == field), None)
            raw = source.get(legacy) if legacy else None
            if raw is not None:
                recorder.warn(f"Renamed legacy total {legacy!r} to {field!r}.")
        values[field] = _coerce_nonnegative_int(raw, field, recorder, default=0)

    if values["files_included"] == 0:
        values["files_included"] = sum(values[name] for name in ("files_ok", "files_fail", "files_error", "files_skipped"))
    if values["files_seen"] == 0:
        values["files_seen"] = values["files_included"] + values["files_excluded"]
    if values["scenarios_seen"] == 0:
        values["scenarios_seen"] = sum(values[name] for name in ("scenarios_ok", "scenarios_fail", "scenarios_error", "scenarios_skipped"))

    overall_raw = source.get("overall_status", source.get("status"))
    if overall_raw is None:
        overall = "ERROR" if values["files_error"] or values["scenarios_error"] else "FAIL" if values["files_fail"] or values["scenarios_fail"] or values["required_scenario_fail"] else "OK"
        recorder.warn("Derived overall_status from migrated status counts.")
    else:
        overall = str(overall_raw).upper()
        if overall not in _CANONICAL_OVERALL_STATUSES:
            recorder.lose(f"Unknown legacy overall status: {overall_raw!r}.")
            overall = "ERROR"

    return {**values, "overall_status": overall}


def _migrate_artifact_map(
    source: Mapping[str, object],
    *,
    run_root: Path | None,
    recorder: _Recorder,
) -> JsonObject:
    aliases = {
        "ai_brief_path": "ai_ready",
        "ai_ready_path": "ai_ready",
        "summary_path": "summary_json",
        "summary_md_path": "summary_markdown",
        "top_errors_path": "top_errors",
        "manifest_path": "manifest",
        "master_log_path": "master_log",
    }
    result: JsonObject = {}
    for field in _ARTIFACT_FIELDS:
        value = source.get(field)
        if value is None:
            alias = next((old for old, new in aliases.items() if new == field and old in source), None)
            if alias is not None:
                value = source[alias]
                recorder.warn(f"Mapped legacy artifact field {alias!r} to {field!r}.")
        if value is None:
            result[field] = _DEFAULT_ARTIFACTS[field]
            continue
        result[field] = _portable_run_path(value, run_root=run_root, recorder=recorder, field=f"artifacts.{field}") or None
    return result


def _migrate_file_results(
    value: object,
    *,
    run_root: Path | None,
    project_root: Path | None,
    recorder: _Recorder,
    strict: bool,
) -> list[JsonValue]:
    items = _list_or_empty(value, "file_results", recorder)
    result: list[JsonValue] = []
    for index, raw in enumerate(items):
        if not isinstance(raw, Mapping):
            recorder.lose(f"file_results[{index}] is not an object.")
            continue
        item = dict(raw)
        file_path = _portable_project_path(item.get("file_path", item.get("path", "")), project_root, recorder, f"file_results[{index}].file_path")
        status = _canonical_status(item.get("status"), recorder, f"file_results[{index}].status")
        diagnostic_class = _diagnostic_class(item.get("diagnostic_class"), status, bool(item.get("is_direct")), recorder)
        blocked_by_raw = item.get("blocked_by", [])
        blocked_by = []
        for blocker in _list_or_empty(blocked_by_raw, f"file_results[{index}].blocked_by", recorder):
            normalized = _portable_project_path(blocker, project_root, recorder, "blocked_by")
            if normalized and normalized not in blocked_by:
                blocked_by.append(normalized)
        scan_counts_source = item.get("scan_counts", {})
        scan_counts_map = scan_counts_source if isinstance(scan_counts_source, Mapping) else {}
        scan_counts = {
            name: _coerce_nonnegative_int(scan_counts_map.get(name), name, recorder, default=0)
            for name in (
                "single_slash_eq",
                "double_slash_dash",
                "runtime_str_match",
                "untyped_case_str_pat",
                "untyped_table_str_pat",
                "trailing_spaces",
            )
        }
        fingerprint = _migrate_fingerprint(item.get("fingerprint", item), recorder, index)
        compile_summary = _migrate_compile_summary(item.get("compile_summary", item.get("compile", {})), run_root, recorder, index)
        scan_log_path = _portable_run_path(item.get("scan_log_path", ""), run_root=run_root, recorder=recorder, field="scan_log_path")
        result.append(
            {
                "file_path": file_path,
                "module_name": str(item.get("module_name", PurePosixPath(file_path).stem if file_path else "")),
                "status": status,
                "diagnostic_class": diagnostic_class,
                "is_direct": diagnostic_class == "direct",
                "blocked_by": blocked_by,
                "scan_counts": scan_counts,
                "fingerprint": fingerprint,
                "compile_summary": compile_summary,
                "scan_log_path": scan_log_path,
            }
        )
    result.sort(key=lambda entry: str(entry["file_path"]) if isinstance(entry, dict) else "")
    return result


def _migrate_fingerprint(value: object, recorder: _Recorder, index: int) -> JsonValue:
    source = value if isinstance(value, Mapping) else {}
    algorithm = source.get("hash_algorithm")
    digest = source.get("hash")
    if algorithm == "sha256" and isinstance(digest, str) and _SHA256_RE.fullmatch(digest.lower()):
        return {
            "size_bytes": _coerce_nonnegative_int(source.get("size_bytes"), "size_bytes", recorder, default=0),
            "hash_algorithm": "sha256",
            "hash": digest.lower(),
            "last_modified_utc": _optional_timestamp(source.get("last_modified_utc"), recorder),
        }
    legacy = source.get("sha1_short")
    if legacy is not None:
        recorder.lose(f"file_results[{index}] contains sha1_short, which cannot be converted to SHA-256.")
    elif source:
        recorder.lose(f"file_results[{index}] has no recoverable SHA-256 fingerprint.")
    return {
        "size_bytes": _coerce_nonnegative_int(source.get("size_bytes"), "size_bytes", recorder, default=0),
        "hash_algorithm": None,
        "hash": None,
        "last_modified_utc": _optional_timestamp(source.get("last_modified_utc"), recorder),
    }


def _migrate_compile_summary(value: object, run_root: Path | None, recorder: _Recorder, index: int) -> JsonObject:
    source = value if isinstance(value, Mapping) else {}
    error_kind = str(source.get("error_kind", "OK")).upper()
    if error_kind not in _CANONICAL_ERROR_KINDS:
        recorder.warn(f"Unknown compile error kind in file_results[{index}] was mapped to OTHER.")
        error_kind = "OTHER"
    exit_code = source.get("exit_code")
    if exit_code is not None and type(exit_code) is not int:
        recorder.lose(f"file_results[{index}].compile_summary.exit_code is invalid.")
        exit_code = None
    return {
        "exit_code": exit_code,
        "timed_out": _coerce_bool(source.get("timed_out"), "timed_out", recorder, default=False),
        "duration_ms": _coerce_nonnegative_int(source.get("duration_ms"), "duration_ms", recorder, default=0),
        "error_kind": error_kind,
        "first_error": str(source.get("first_error", "")),
        "error_detail": str(source.get("error_detail", "")),
        "stdout_path": _portable_run_path(source.get("stdout_path", ""), run_root=run_root, recorder=recorder, field="stdout_path"),
        "stderr_path": _portable_run_path(source.get("stderr_path", ""), run_root=run_root, recorder=recorder, field="stderr_path"),
    }


def _migrate_scenario_results(
    value: object,
    *,
    run_root: Path | None,
    project_root: Path | None,
    recorder: _Recorder,
    strict: bool,
) -> list[JsonValue]:
    if value is None:
        recorder.warn("Legacy summary predates scenario results; scenario_results was set to an empty array.")
        recorder.lose("Historical run contains no scenario evidence.")
        return []
    items = _list_or_empty(value, "scenario_results", recorder)
    result: list[JsonValue] = []
    for index, raw in enumerate(items):
        if not isinstance(raw, Mapping):
            recorder.lose(f"scenario_results[{index}] is not an object.")
            continue
        item = dict(raw)
        status = _canonical_status(item.get("status"), recorder, f"scenario_results[{index}].status")
        diagnostic_class = _diagnostic_class(item.get("diagnostic_class"), status, False, recorder)
        error_kind = str(item.get("error_kind", "OK")).upper()
        if error_kind not in _CANONICAL_ERROR_KINDS:
            error_kind = "OTHER"
            recorder.warn(f"Unknown scenario error kind in scenario_results[{index}] was mapped to OTHER.")
        command_raw = item.get("command", [])
        command = [str(part) for part in command_raw] if isinstance(command_raw, (list, tuple)) else []
        exit_code = item.get("exit_code")
        if exit_code is not None and type(exit_code) is not int:
            exit_code = None
            recorder.lose(f"scenario_results[{index}].exit_code is invalid.")
        result.append(
            {
                "scenario_id": str(item.get("scenario_id", item.get("id", ""))),
                "script_path": _portable_project_path(item.get("script_path", ""), project_root, recorder, "script_path"),
                "required": _coerce_bool(item.get("required"), "required", recorder, default=False),
                "status": status,
                "command": command,
                "working_directory": (_path_text(item.get("working_directory")) or "").replace("\\", "/"),
                "exit_code": exit_code,
                "timed_out": _coerce_bool(item.get("timed_out"), "timed_out", recorder, default=False),
                "duration_ms": _coerce_nonnegative_int(item.get("duration_ms"), "duration_ms", recorder, default=0),
                "stdout_path": _portable_run_path(item.get("stdout_path", ""), run_root=run_root, recorder=recorder, field="stdout_path"),
                "stderr_path": _portable_run_path(item.get("stderr_path", ""), run_root=run_root, recorder=recorder, field="stderr_path"),
                "normalized_output_path": _portable_run_path(item.get("normalized_output_path", ""), run_root=run_root, recorder=recorder, field="normalized_output_path"),
                "gold_path": None if item.get("gold_path") in (None, "") else _portable_project_path(item.get("gold_path"), project_root, recorder, "gold_path"),
                "gold_match": item.get("gold_match") if isinstance(item.get("gold_match"), bool) else None,
                "diagnostic_class": diagnostic_class,
                "error_kind": error_kind,
                "primary_message": str(item.get("primary_message", "")),
                "sections": _copy_object_list(item.get("sections", []), "sections", recorder),
                "artifacts": _copy_json_list(item.get("artifacts", []), "artifacts", recorder),
            }
        )
    return result


def _migrate_diff_entries(value: object, *, recorder: _Recorder, strict: bool) -> list[JsonValue]:
    items = _list_or_empty(value, "diff_entries", recorder)
    result: list[JsonValue] = []
    for index, raw in enumerate(items):
        if not isinstance(raw, Mapping):
            recorder.lose(f"diff_entries[{index}] is not an object.")
            continue
        item = dict(raw)
        subject_kind = str(item.get("subject_kind", "file" if "file_path" in item else "run"))
        subject_id = str(item.get("subject_id", item.get("file_path", "")))
        if "file_path" in item and "subject_id" not in item:
            recorder.warn("Mapped legacy diff file_path to subject_kind='file' and subject_id.")
        result.append(
            {
                "subject_kind": subject_kind,
                "subject_id": subject_id,
                "previous_status": str(item.get("previous_status", "SKIPPED")).upper(),
                "current_status": str(item.get("current_status", "SKIPPED")).upper(),
                "change_kind": str(item.get("change_kind", "unchanged")),
                "message": str(item.get("message", "")),
            }
        )
    return result


def _migrate_top_errors(value: object, *, recorder: _Recorder, strict: bool) -> list[JsonValue]:
    result: list[JsonValue] = []
    if isinstance(value, Mapping):
        recorder.warn("Normalized legacy top-error mapping to the canonical array form.")
        for message, count in value.items():
            if not isinstance(message, str) or not message.strip():
                recorder.lose("Legacy top-error mapping contains an empty or non-string message.")
                continue
            numeric = _coerce_nonnegative_int(count, "top error count", recorder, default=0)
            if numeric <= 0:
                recorder.lose(f"Legacy top-error count for {message!r} is not positive.")
                continue
            result.append({"error_kind": "OTHER", "message": message, "count": numeric})
    else:
        for index, raw in enumerate(_list_or_empty(value, "top_errors", recorder)):
            if not isinstance(raw, Mapping):
                recorder.lose(f"top_errors[{index}] is not an object.")
                continue
            message = raw.get("message")
            count = _coerce_nonnegative_int(raw.get("count"), "top error count", recorder, default=0)
            if not isinstance(message, str) or not message.strip() or count <= 0:
                recorder.lose(f"top_errors[{index}] is invalid.")
                continue
            error_kind = str(raw.get("error_kind", "OTHER")).upper()
            if error_kind not in _CANONICAL_ERROR_KINDS:
                error_kind = "OTHER"
                recorder.warn(f"Unknown top-error kind at index {index} was mapped to OTHER.")
            result.append({"error_kind": error_kind, "message": message, "count": count})
    result.sort(key=lambda item: (-int(item["count"]), str(item["message"]).casefold()) if isinstance(item, dict) else (0, ""))
    return result


def _merge_flat_metadata(source: Mapping[str, object], recorder: _Recorder) -> Mapping[str, object]:
    merged: dict[str, object] = {}
    for key in ("run_config", "config"):
        value = source.get(key)
        if isinstance(value, Mapping):
            merged.update(value)
    run_paths = source.get("run_paths")
    if isinstance(run_paths, Mapping):
        aliases = {
            "run_dir": "run_dir",
            "summary_json": "summary_json",
            "summary_markdown": "summary_markdown",
        }
        for old, new in aliases.items():
            if old in run_paths:
                merged[new] = run_paths[old]
    for field in _METADATA_FIELDS:
        if field in source:
            merged[field] = source[field]
    return merged


def _merge_flat_totals(source: Mapping[str, object]) -> Mapping[str, object]:
    totals: dict[str, object] = {}
    for field in (*_TOTAL_FIELDS, "ok", "fail", "error", "skipped", "overall_status", "status"):
        if field in source:
            totals[field] = source[field]
    return totals


def _merge_flat_artifacts(source: Mapping[str, object]) -> Mapping[str, object]:
    artifacts: dict[str, object] = {}
    run_paths = source.get("run_paths")
    if isinstance(run_paths, Mapping):
        artifacts.update(run_paths)
    for field in (*_ARTIFACT_FIELDS, "ai_brief_path", "ai_ready_path", "summary_path", "summary_md_path", "top_errors_path", "manifest_path", "master_log_path"):
        if field in source:
            artifacts[field] = source[field]
    return artifacts


def _manifest_candidate_paths(source: Mapping[str, object], explicit: Iterable[str] | None, recorder: _Recorder) -> tuple[str, ...]:
    if explicit is not None:
        if isinstance(explicit, (str, bytes)):
            raise TypeError("artifact_paths must be an iterable of paths")
        return tuple(str(item) for item in explicit)
    raw = source.get("artifacts", source.get("files", []))
    if isinstance(raw, Mapping):
        recorder.warn("Converted legacy manifest artifact mapping to an ordered path list.")
        return tuple(str(key) for key in raw)
    if isinstance(raw, list):
        values: list[str] = []
        for item in raw:
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, Mapping) and isinstance(item.get("path"), str):
                values.append(str(item["path"]))
            else:
                recorder.lose("Legacy manifest contains an artifact without a usable path.")
        return tuple(values)
    recorder.lose("No recoverable artifact path inventory was supplied for manifest migration.")
    return ()


def _legacy_manifest_entry(source: Mapping[str, object], raw_path: str, relative: str) -> Mapping[str, object] | None:
    raw = source.get("artifacts", source.get("files", []))
    if isinstance(raw, Mapping):
        value = raw.get(raw_path, raw.get(relative))
        return value if isinstance(value, Mapping) else None
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping) and item.get("path") in {raw_path, relative}:
                return item
    return None


def _normalized_string_map(values: Mapping[str, str], root: Path, recorder: _Recorder, field: str) -> Mapping[str, str]:
    result: dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value.strip():
            raise TypeError(f"{field} must map non-empty path strings to non-empty strings")
        normalized = _portable_run_path(key, run_root=root, recorder=recorder, field=field)
        if normalized:
            result[normalized] = value
    return result


def _portable_run_path(value: object, *, run_root: Path | None, recorder: _Recorder, field: str) -> str:
    text = _path_text(value)
    if text is None or text == "":
        return ""
    normalized = text.replace("\\", "/")
    if _is_absolute_text(normalized):
        if run_root is None:
            recorder.lose(f"Absolute {field} cannot be made run-relative without run_root: {text!r}.")
            return ""
        candidate = Path(text).resolve(strict=False)
        if not _is_relative_to(candidate, run_root):
            recorder.lose(f"Absolute {field} is outside run_root: {text!r}.")
            return ""
        normalized = candidate.relative_to(run_root).as_posix()
        recorder.warn(f"Converted absolute {field} to a run-relative path.")
    return _validate_relative_path(normalized, recorder, field)


def _portable_project_path(value: object, project_root: Path | None, recorder: _Recorder, field: str) -> str:
    text = _path_text(value)
    if text is None or text == "":
        return ""
    normalized = text.replace("\\", "/")
    if _is_absolute_text(normalized):
        if project_root is None:
            recorder.lose(f"Absolute {field} cannot be made project-relative without project_root: {text!r}.")
            return ""
        candidate = Path(text).resolve(strict=False)
        if not _is_relative_to(candidate, project_root):
            recorder.lose(f"Absolute {field} is outside project_root: {text!r}.")
            return ""
        normalized = candidate.relative_to(project_root).as_posix()
        recorder.warn(f"Converted absolute {field} to a project-relative path.")
    return _validate_relative_path(normalized, recorder, field)


def _validate_relative_path(value: str, recorder: _Recorder, field: str) -> str:
    path = PurePosixPath(value)
    if value in {"", "."} or value.startswith("/") or _DRIVE_RE.match(value) or any(part == ".." for part in path.parts):
        recorder.lose(f"Invalid portable relative {field}: {value!r}.")
        return ""
    return path.as_posix()


def _canonical_status(value: object, recorder: _Recorder, field: str) -> str:
    status = "SKIPPED" if value is None else str(value).upper()
    aliases = {"PASS": "OK", "PASSED": "OK", "FAILED": "FAIL"}
    status = aliases.get(status, status)
    if status not in _CANONICAL_STATUSES:
        recorder.lose(f"Unknown legacy status in {field}: {value!r}.")
        return "ERROR"
    return status


def _diagnostic_class(value: object, status: str, is_direct: bool, recorder: _Recorder) -> str:
    if isinstance(value, str):
        candidate = value.lower()
        aliases = {"script_error": "direct", "clean": "ok"}
        candidate = aliases.get(candidate, candidate)
        if candidate in _CANONICAL_DIAGNOSTIC_CLASSES:
            return candidate
        recorder.warn(f"Unknown legacy diagnostic class {value!r} was mapped conservatively.")
    if status == "OK":
        return "ok"
    if status == "SKIPPED":
        return "skipped"
    return "direct" if is_direct else "ambiguous"


def _media_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".json"):
        return "application/json"
    if lower.endswith(".md"):
        return "text/markdown; charset=utf-8"
    if lower.endswith((".txt", ".log", ".out", ".gold", ".gfs", ".gf")):
        return "text/plain; charset=utf-8"
    guessed, _ = mimetypes.guess_type(path, strict=False)
    return guessed or "application/octet-stream"


def _infer_role(path: str) -> str:
    lower = path.lower()
    name = PurePosixPath(lower).name
    if lower == "summary.json":
        return "machine_summary"
    if lower == "summary.md":
        return "human_summary"
    if name == "ai_ready.md":
        return "ai_handoff"
    if name == "top_errors.txt":
        return "top_errors"
    if name == "master.log":
        return "master_log"
    if name in {"all_logs.txt", "all_scan_logs.txt"}:
        return "aggregate_log"
    if lower.endswith(".scan.txt"):
        return "scan_log"
    if lower.endswith(".stdout.txt"):
        return "scenario_stdout" if "/scenarios/" in f"/{lower}" else "compile_stdout"
    if lower.endswith(".stderr.txt"):
        return "scenario_stderr" if "/scenarios/" in f"/{lower}" else "compile_stderr"
    if lower.endswith(".out") or lower.endswith(".out.txt"):
        return "scenario_output"
    if lower.endswith(".gfo"):
        return "gfo"
    if lower.endswith(".pgf"):
        return "pgf"
    if lower.startswith("details/"):
        return "detail"
    return "other"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_timestamp(value: datetime | str | object | None) -> str:
    if value is None:
        instant = datetime.now(UTC)
    elif isinstance(value, datetime):
        instant = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        instant = datetime.fromisoformat(text)
    else:
        raise TypeError("timestamp must be datetime, RFC 3339 string, or None")
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return instant.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _optional_timestamp(value: object, recorder: _Recorder) -> JsonValue:
    if value in (None, ""):
        return None
    try:
        return _canonical_timestamp(value)
    except (TypeError, ValueError):
        recorder.warn(f"Ignored invalid optional timestamp: {value!r}.")
        return None


def _supported_v1(value: object) -> bool:
    if not isinstance(value, str) or _VERSION_RE.fullmatch(value) is None:
        return False
    return value.split(".", 1)[0] == "1"


def _result(
    *,
    migration_id: str,
    source_schema: str,
    source_version: str,
    target_schema: str,
    target_version: str,
    source_path: str,
    destination_path: str | None,
    status: MigrationStatus,
    changed: bool,
    warnings: tuple[str, ...] = (),
    losses: tuple[str, ...] = (),
) -> MigrationResult:
    return MigrationResult(
        migration_id=migration_id,
        source_schema=source_schema,
        source_version=source_version,
        target_schema=target_schema,
        target_version=target_version,
        source_path=source_path,
        destination_path=destination_path,
        status=status,
        warnings=warnings,
        losses=losses,
        changed=changed,
        written=False,
        backup_path=None,
    )


def _json_object(value: Mapping[str, object], field: str) -> JsonObject:
    result: JsonObject = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(f"{field} keys must be strings")
        result[key] = _json_value(item, f"{field}.{key}")
    return result


def _json_value(value: object, field: str) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return _json_object(value, field)
    if isinstance(value, (list, tuple)):
        return [_json_value(item, field) for item in value]
    raise TypeError(f"{field} contains a non-JSON value of type {type(value).__name__}")


def _mapping_or_empty(value: object, field: str, recorder: _Recorder) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        recorder.lose(f"Legacy {field} is not an object.")
        return {}
    return value


def _list_or_empty(value: object, field: str, recorder: _Recorder) -> list[object]:
    if value is None:
        return []
    if not isinstance(value, list):
        recorder.lose(f"Legacy {field} is not an array.")
        return []
    return value


def _copy_object_list(value: object, field: str, recorder: _Recorder) -> list[JsonValue]:
    result: list[JsonValue] = []
    for index, item in enumerate(_list_or_empty(value, field, recorder)):
        if not isinstance(item, Mapping):
            recorder.lose(f"{field}[{index}] is not an object.")
            continue
        result.append(_json_object(item, f"{field}[{index}]"))
    return result


def _copy_json_list(value: object, field: str, recorder: _Recorder) -> list[JsonValue]:
    return [_json_value(item, field) for item in _list_or_empty(value, field, recorder)]


def _coerce_nonnegative_int(value: object, field: str, recorder: _Recorder, *, default: int) -> int:
    if value is None:
        return default
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isdecimal():
        recorder.warn(f"Converted textual integer in {field!r} to a JSON integer.")
        return int(value)
    recorder.lose(f"Legacy field {field!r} is not a non-negative integer.")
    return default


def _coerce_bool(value: object, field: str, recorder: _Recorder, *, default: bool) -> bool:
    if value is None:
        return default
    if type(value) is bool:
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        recorder.warn(f"Converted textual boolean in {field!r} to a JSON boolean.")
        return value.lower() == "true"
    recorder.lose(f"Legacy field {field!r} is not a boolean.")
    return default


def _path_text(value: object) -> str | None:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return None


def _entry_text(entry: Mapping[str, object] | None, field: str) -> str | None:
    if entry is None:
        return None
    value = entry.get(field)
    return value if isinstance(value, str) and value.strip() else None


def _is_absolute_text(value: str) -> bool:
    return value.startswith("/") or bool(_DRIVE_RE.match(value)) or value.startswith("//")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _optional_absolute_path(value: Path | None, field: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path or None")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return value.resolve(strict=False)


def _required_absolute_directory(value: Path, field: str) -> Path:
    path = _optional_absolute_path(value, field)
    assert path is not None
    if not path.is_dir():
        raise ValueError(f"{field} must identify an existing directory")
    return path


def _nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{field} must be a non-empty string without NUL characters")
    return value


def _require_mapping(value: object, field: str) -> None:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")


def _legacy_summary_root_fields() -> frozenset[str]:
    return frozenset(
        {
            "run_config",
            "config",
            "run_paths",
            "started_at",
            "finished_at",
            "duration_ms",
            "gf_version",
            "mode",
            "target_file",
            "file_results",
            "scenario_results",
            "diff_entries",
            "top_errors",
            "ok",
            "fail",
            "error",
            "skipped",
            "overall_status",
            "status",
            "ai_brief_path",
            "ai_ready_path",
            "summary_path",
            "summary_md_path",
            "top_errors_path",
            "manifest_path",
            "master_log_path",
            *_METADATA_FIELDS,
            *_TOTAL_FIELDS,
            *_ARTIFACT_FIELDS,
        }
    )


migrate_run_summary = migrate_summary_document
migrate_artifact_manifest = migrate_manifest_document


__all__ = (
    "ARTIFACT_MANIFEST_SCHEMA_ID",
    "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "DocumentMigration",
    "MANIFEST_MIGRATION_ID",
    "MigrationResult",
    "MigrationStatus",
    "RUN_SUMMARY_SCHEMA_ID",
    "RUN_SUMMARY_SCHEMA_VERSION",
    "SUMMARY_MIGRATION_ID",
    "SummaryShape",
    "detect_summary_shape",
    "migrate_artifact_manifest",
    "migrate_manifest_document",
    "migrate_manifest_v0_to_v1",
    "migrate_run_summary",
    "migrate_summary_document",
    "migrate_summary_v0_to_v1",
)
