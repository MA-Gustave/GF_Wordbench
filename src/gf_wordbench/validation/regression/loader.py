"""Read-only loading and in-memory migration of regression baselines."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Final, TypeAlias, cast

from gf_wordbench.infrastructure.filesystem import (
    PathContainmentError,
    require_directory,
    require_regular_file,
)
from gf_wordbench.infrastructure.json_io import JsonObject, JsonValue, read_json
from gf_wordbench.kernel.errors import (
    EvidenceIOError,
    PathSecurityError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.kernel.ids import validate_project_id, validate_run_id
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode, ValidationStatus

SUMMARY_FILENAME: Final[str] = "summary.json"
RUN_SUMMARY_SCHEMA_ID: Final[str] = "gf-wordbench.run-summary"
SUPPORTED_RUN_SUMMARY_MAJOR: Final[int] = 1
DEFAULT_MAX_SUMMARY_BYTES: Final[int] = 16 * 1024 * 1024

_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)$"
)
_RUN_DIRECTORY_RE: Final[re.Pattern[str]] = re.compile(
    r"^run_(?P<run_id>[0-9]{8}_[0-9]{6}(?:_(?:0[2-9]|[1-9][0-9]+))?)$"
)
_WINDOWS_ABSOLUTE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:[A-Za-z]:[\\/]|\\\\)"
)

_REQUIRED_ROOT_FIELDS: Final[tuple[str, ...]] = (
    "schema_id",
    "schema_version",
    "metadata",
    "totals",
    "artifacts",
    "file_results",
    "scenario_results",
    "diff_entries",
    "top_errors",
)

_REQUIRED_METADATA_FIELDS: Final[tuple[str, ...]] = (
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

_TOTAL_COUNT_FIELDS: Final[tuple[str, ...]] = (
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

_CANONICAL_ARTIFACT_KEYS: Final[tuple[str, ...]] = (
    "summary_json",
    "summary_markdown",
    "ai_ready",
    "top_errors",
    "manifest",
    "details_directory",
    "raw_directory",
    "master_log",
    "all_scan_logs",
    "all_logs",
    "gfo_directory",
    "output_directory",
    "pgf_directory",
)

_ARTIFACT_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "summary_json": ("summary_json", "summary_path"),
    "summary_markdown": (
        "summary_markdown",
        "summary_md",
        "summary_md_path",
    ),
    "ai_ready": (
        "ai_ready",
        "ai_ready_path",
        "ai_brief_path",
    ),
    "top_errors": ("top_errors", "top_errors_path"),
    "manifest": ("manifest", "manifest_path"),
    "details_directory": ("details_directory", "details_dir"),
    "raw_directory": ("raw_directory", "raw_dir"),
    "master_log": ("master_log", "master_log_path"),
    "all_scan_logs": ("all_scan_logs", "all_scan_logs_path"),
    "all_logs": ("all_logs", "all_logs_path"),
    "gfo_directory": ("gfo_directory", "gfo_dir"),
    "output_directory": (
        "output_directory",
        "out_directory",
        "out_dir",
    ),
    "pgf_directory": ("pgf_directory", "pgf_dir"),
}

_MODE_ALIASES: Final[dict[str, str]] = {
    "file": ValidationMode.QUICK.value,
    "all": ValidationMode.DIAGNOSTIC.value,
}

FrozenJsonScalar: TypeAlias = None | bool | int | float | str
FrozenJsonValue: TypeAlias = (
    FrozenJsonScalar
    | tuple["FrozenJsonValue", ...]
    | Mapping[str, "FrozenJsonValue"]
)


@unique
class SummaryForm(StrEnum):
    CANONICAL = "canonical"
    LEGACY_NESTED = "legacy_nested"
    LEGACY_FLAT = "legacy_flat"


@dataclass(frozen=True, slots=True)
class SummaryLoadWarning:
    code: str
    message: str

    def __post_init__(self) -> None:
        _require_non_empty_text(self.code, field="warning code")
        _require_non_empty_text(self.message, field="warning message")


@dataclass(frozen=True, slots=True)
class LoadedRunSummary:
    summary_path: Path
    run_directory: Path
    schema_id: str
    schema_version: str
    schema_major: int
    schema_minor: int
    source_form: SummaryForm
    document: Mapping[str, FrozenJsonValue]
    warnings: tuple[SummaryLoadWarning, ...]

    def __post_init__(self) -> None:
        if not self.summary_path.is_absolute():
            raise ValueError("summary_path must be absolute")
        if not self.run_directory.is_absolute():
            raise ValueError("run_directory must be absolute")
        if self.summary_path.parent != self.run_directory:
            raise ValueError("summary_path must belong to run_directory")
        if self.schema_id != RUN_SUMMARY_SCHEMA_ID:
            raise ValueError("schema_id is not the canonical run-summary ID")
        if self.schema_major != SUPPORTED_RUN_SUMMARY_MAJOR:
            raise ValueError("schema_major is unsupported")
        if self.schema_minor < 0:
            raise ValueError("schema_minor must be non-negative")
        if not isinstance(self.source_form, SummaryForm):
            raise TypeError("source_form must be a SummaryForm")
        if not isinstance(self.document, Mapping):
            raise TypeError("document must be a mapping")
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple")

    @property
    def metadata(self) -> Mapping[str, FrozenJsonValue]:
        return _frozen_object(self.document, "metadata")

    @property
    def totals(self) -> Mapping[str, FrozenJsonValue]:
        return _frozen_object(self.document, "totals")

    @property
    def artifacts(self) -> Mapping[str, FrozenJsonValue]:
        return _frozen_object(self.document, "artifacts")

    @property
    def file_results(self) -> tuple[Mapping[str, FrozenJsonValue], ...]:
        return _frozen_object_array(self.document, "file_results")

    @property
    def scenario_results(self) -> tuple[Mapping[str, FrozenJsonValue], ...]:
        return _frozen_object_array(self.document, "scenario_results")

    @property
    def diff_entries(self) -> tuple[Mapping[str, FrozenJsonValue], ...]:
        return _frozen_object_array(self.document, "diff_entries")

    @property
    def top_errors(self) -> tuple[Mapping[str, FrozenJsonValue], ...]:
        return _frozen_object_array(self.document, "top_errors")

    @property
    def run_id(self) -> str:
        return _frozen_string(self.metadata, "run_id")

    @property
    def project_id(self) -> str:
        return _frozen_string(self.metadata, "project_id")

    @property
    def mode(self) -> ValidationMode:
        return ValidationMode(_frozen_string(self.metadata, "mode"))

    @property
    def target_file(self) -> str | None:
        value = self.metadata.get("target_file")
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("metadata.target_file must be a string or null")
        return value

    @property
    def gf_version(self) -> str:
        value = self.metadata.get("gf_version", "")
        if not isinstance(value, str):
            raise TypeError("metadata.gf_version must be a string")
        return value

    @property
    def overall_status(self) -> OverallStatus:
        return OverallStatus(_frozen_string(self.totals, "overall_status"))

    @property
    def completed(self) -> bool:
        metadata = self.metadata
        for key in ("incomplete", "partial", "recovery_required"):
            value = metadata.get(key)
            if value is True:
                return False
        completion = metadata.get("completed")
        if completion is not None:
            if type(completion) is not bool:
                raise TypeError("metadata.completed must be a bool")
            return completion
        lifecycle = metadata.get("lifecycle_state")
        if lifecycle is not None:
            if not isinstance(lifecycle, str):
                raise TypeError("metadata.lifecycle_state must be a string")
            return lifecycle.casefold() in {"completed", "finalized"}
        return True


@dataclass(frozen=True, slots=True)
class SummaryLoadAttempt:
    summary: LoadedRunSummary | None
    warning: SummaryLoadWarning | None

    def __post_init__(self) -> None:
        if (self.summary is None) == (self.warning is None):
            raise ValueError(
                "exactly one of summary and warning must be present"
            )


def load_previous_summary(
    source: str | os.PathLike[str],
    *,
    approved_root: str | os.PathLike[str] | None = None,
    allow_external_explicit: bool = False,
    max_bytes: int = DEFAULT_MAX_SUMMARY_BYTES,
    strict: bool = False,
) -> LoadedRunSummary:
    """Load, validate, and migrate one baseline summary without rewriting it."""

    maximum = _validate_max_bytes(max_bytes)
    strict_mode = _require_bool(strict, field="strict")
    allow_external = _require_bool(
        allow_external_explicit,
        field="allow_external_explicit",
    )
    summary_path = resolve_summary_path(
        source,
        approved_root=approved_root,
        allow_external_explicit=allow_external,
    )

    try:
        raw = read_json(summary_path, max_bytes=maximum)
    except EvidenceIOError:
        raise
    except OSError as exc:
        raise _evidence_error(
            "Unable to read regression baseline summary",
            summary_path,
            detail=_bounded_exception(exc),
        ) from exc

    source_form = _detect_summary_form(raw)
    warnings: list[SummaryLoadWarning] = []
    canonical = _migrate_to_canonical(
        raw,
        source_form=source_form,
        summary_path=summary_path,
        warnings=warnings,
    )
    schema_major, schema_minor = _validate_canonical_document(
        canonical,
        summary_path=summary_path,
        strict=strict_mode,
        warnings=warnings,
    )

    frozen = cast(
        Mapping[str, FrozenJsonValue],
        _freeze_json(canonical),
    )
    return LoadedRunSummary(
        summary_path=summary_path,
        run_directory=summary_path.parent,
        schema_id=RUN_SUMMARY_SCHEMA_ID,
        schema_version=f"{schema_major}.{schema_minor}",
        schema_major=schema_major,
        schema_minor=schema_minor,
        source_form=source_form,
        document=frozen,
        warnings=tuple(warnings),
    )


def try_load_previous_summary(
    source: str | os.PathLike[str],
    *,
    approved_root: str | os.PathLike[str] | None = None,
    allow_external_explicit: bool = False,
    max_bytes: int = DEFAULT_MAX_SUMMARY_BYTES,
    strict: bool = False,
) -> SummaryLoadAttempt:
    """Attempt baseline loading and convert controlled failures to one warning."""

    try:
        summary = load_previous_summary(
            source,
            approved_root=approved_root,
            allow_external_explicit=allow_external_explicit,
            max_bytes=max_bytes,
            strict=strict,
        )
    except (
        EvidenceIOError,
        PathSecurityError,
        SchemaValidationError,
        UnsupportedVersionError,
    ) as exc:
        subject = getattr(exc, "subject", None)
        context = "" if subject is None else f" ({subject})"
        warning = SummaryLoadWarning(
            code="baseline-unavailable",
            message=f"{exc.message}{context}",
        )
        return SummaryLoadAttempt(summary=None, warning=warning)

    return SummaryLoadAttempt(summary=summary, warning=None)


def resolve_summary_path(
    source: str | os.PathLike[str],
    *,
    approved_root: str | os.PathLike[str] | None = None,
    allow_external_explicit: bool = False,
) -> Path:
    """Resolve a run-directory or summary path under the approved root."""

    allow_external = _require_bool(
        allow_external_explicit,
        field="allow_external_explicit",
    )
    root = _resolve_optional_root(approved_root)
    candidate = _source_path(source, approved_root=root)

    try:
        if candidate.is_dir():
            candidate = candidate / SUMMARY_FILENAME

        if root is not None and not allow_external:
            return require_regular_file(
                candidate,
                root=root,
                role="regression baseline summary",
            )

        return require_regular_file(
            candidate,
            role="regression baseline summary",
        )
    except PathContainmentError as exc:
        raise PathSecurityError(
            "Regression baseline escapes the approved output root",
            code="GF-WB-PATH-001",
            detail=(
                f"candidate={exc.candidate!s}; "
                f"approved_root={exc.root!s}"
            ),
            stage="regression",
            operation="load-baseline",
            subject=os.fspath(candidate),
        ) from exc
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError) as exc:
        raise _evidence_error(
            "Regression baseline summary is not a readable regular file",
            candidate,
            detail=_bounded_exception(exc),
        ) from exc
    except OSError as exc:
        raise _evidence_error(
            "Unable to resolve regression baseline summary",
            candidate,
            detail=_bounded_exception(exc),
        ) from exc


def _detect_summary_form(document: JsonObject) -> SummaryForm:
    schema_id = document.get("schema_id")
    schema_version = document.get("schema_version")

    if schema_id is not None or schema_version is not None:
        if not isinstance(schema_id, str):
            raise _schema_error(
                "Run summary schema_id must be a string",
                field="schema_id",
            )
        if not isinstance(schema_version, str):
            raise _schema_error(
                "Run summary schema_version must be a string",
                field="schema_version",
            )
        return SummaryForm.CANONICAL

    nested_markers = {
        "metadata",
        "totals",
        "artifacts",
        "file_results",
    }
    if nested_markers.issubset(document):
        return SummaryForm.LEGACY_NESTED

    flat_markers = {
        "run_config",
        "run_paths",
        "file_results",
    }
    if flat_markers.issubset(document) or (
        "file_results" in document
        and any(
            key in document
            for key in (
                "started_at",
                "finished_at",
                "duration_ms",
                "gf_version",
                "run_id",
            )
        )
    ):
        return SummaryForm.LEGACY_FLAT

    raise _schema_error(
        "Unrecognized regression baseline summary shape",
        field="$",
    )


def _migrate_to_canonical(
    document: JsonObject,
    *,
    source_form: SummaryForm,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> JsonObject:
    if source_form is SummaryForm.CANONICAL:
        canonical = _copy_json_object(document)
    elif source_form is SummaryForm.LEGACY_NESTED:
        canonical = _migrate_nested_summary(
            document,
            summary_path=summary_path,
            warnings=warnings,
        )
    else:
        canonical = _migrate_flat_summary(
            document,
            summary_path=summary_path,
            warnings=warnings,
        )

    metadata = _require_object(
        canonical.get("metadata"),
        field="metadata",
    )
    project_root = _optional_non_empty_string(
        metadata.get("project_root"),
        field="metadata.project_root",
    )
    run_dir = _optional_non_empty_string(
        metadata.get("run_dir"),
        field="metadata.run_dir",
    )

    metadata["mode"] = _canonical_mode(
        metadata.get("mode"),
        warnings=warnings,
    )
    metadata["run_id"] = _resolve_run_id(
        metadata.get("run_id"),
        summary_path=summary_path,
        warnings=warnings,
    )
    metadata["project_id"] = _resolve_project_id(
        metadata.get("project_id"),
        project_root=project_root,
        warnings=warnings,
    )
    metadata["target_file"] = _normalize_optional_project_path(
        metadata.get("target_file"),
        field="metadata.target_file",
        project_root=project_root,
        warnings=warnings,
    )

    if "source_directory" in metadata:
        metadata["source_directory"] = _normalize_project_path(
            metadata["source_directory"],
            field="metadata.source_directory",
            project_root=project_root,
            warnings=warnings,
        )

    canonical["metadata"] = metadata
    canonical["totals"] = _normalize_totals(
        canonical.get("totals"),
        file_results=canonical.get("file_results"),
        scenario_results=canonical.get("scenario_results"),
        warnings=warnings,
    )
    canonical["artifacts"] = _normalize_artifacts(
        canonical.get("artifacts"),
        run_dir=run_dir,
        summary_path=summary_path,
        warnings=warnings,
    )
    canonical["file_results"] = _normalize_file_results(
        canonical.get("file_results"),
        project_root=project_root,
        warnings=warnings,
    )
    canonical["scenario_results"] = _normalize_scenario_results(
        canonical.get("scenario_results"),
        project_root=project_root,
        warnings=warnings,
    )
    canonical["diff_entries"] = _normalize_diff_entries(
        canonical.get("diff_entries"),
        project_root=project_root,
        warnings=warnings,
    )
    canonical["top_errors"] = _normalize_top_errors(
        canonical.get("top_errors"),
        warnings=warnings,
    )

    return canonical


def _migrate_nested_summary(
    document: JsonObject,
    *,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> JsonObject:
    _warn(
        warnings,
        "legacy-summary",
        "Loaded unversioned nested run summary through in-memory migration",
    )
    metadata = _copy_json_object(
        _require_object(document.get("metadata"), field="metadata")
    )
    metadata.setdefault("run_dir", summary_path.parent.as_posix())

    producer = document.get("producer")
    canonical: JsonObject = {
        "schema_id": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": "1.0",
        "metadata": metadata,
        "totals": _copy_json_object(
            _require_object(document.get("totals"), field="totals")
        ),
        "artifacts": _copy_json_object(
            _require_object(document.get("artifacts"), field="artifacts")
        ),
        "file_results": _copy_json_array(
            document.get("file_results"),
            field="file_results",
        ),
        "scenario_results": _copy_json_array(
            document.get("scenario_results", []),
            field="scenario_results",
        ),
        "diff_entries": _copy_json_array(
            document.get("diff_entries", []),
            field="diff_entries",
        ),
        "top_errors": _legacy_top_errors_value(
            document.get("top_errors", []),
        ),
    }
    if isinstance(producer, dict):
        canonical["producer"] = _copy_json_object(producer)
    else:
        canonical["producer"] = {
            "name": "gf-wordbench",
            "version": "legacy-unknown",
        }
        _warn(
            warnings,
            "legacy-producer",
            "Baseline producer version was unavailable",
        )
    return canonical


def _migrate_flat_summary(
    document: JsonObject,
    *,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> JsonObject:
    _warn(
        warnings,
        "legacy-summary",
        "Loaded flat legacy run summary through in-memory migration",
    )
    run_config = _object_or_empty(document.get("run_config"))
    run_paths = _object_or_empty(document.get("run_paths"))

    metadata: JsonObject = {}
    _copy_first(
        metadata,
        "run_id",
        document,
        run_config,
        run_paths,
    )
    _copy_first(metadata, "mode", run_config, document)
    _copy_first(metadata, "target_file", run_config, document)
    _copy_first(metadata, "project_id", run_config, document)
    _copy_first(metadata, "project_name", run_config, document)
    _copy_first(metadata, "project_root", run_config, document)
    _copy_first(metadata, "rgl_root", run_config, document)
    _copy_first(metadata, "gf_executable", run_config, document)
    _copy_first(metadata, "output_root", run_config, document)
    _copy_first(metadata, "source_directory", run_config, document)
    _copy_first(metadata, "source_glob", run_config, document)
    _copy_first(metadata, "gf_path", run_config, document)
    _copy_first(metadata, "timeout_sec", run_config, document)
    _copy_first(metadata, "max_files", run_config, document)
    _copy_first(metadata, "skip_version_probe", run_config, document)
    _copy_first(metadata, "no_compile", run_config, document)
    _copy_first(metadata, "emit_cpu_stats", run_config, document)
    _copy_first(metadata, "keep_ok_details", run_config, document)
    _copy_first(metadata, "diff_previous", run_config, document)
    _copy_first(metadata, "started_at", document)
    _copy_first(metadata, "finished_at", document)
    _copy_first(metadata, "duration_ms", document)
    _copy_first(metadata, "gf_version", document)
    metadata.setdefault("run_dir", summary_path.parent.as_posix())
    metadata.setdefault("target_file", None)

    totals_source = _object_or_empty(document.get("totals"))
    for field in (*_TOTAL_COUNT_FIELDS, "overall_status"):
        if field in document and field not in totals_source:
            totals_source[field] = document[field]

    artifacts = _copy_json_object(run_paths)
    for key in _CANONICAL_ARTIFACT_KEYS:
        if key in document and key not in artifacts:
            artifacts[key] = document[key]
    for aliases in _ARTIFACT_ALIASES.values():
        for alias in aliases:
            if alias in document and alias not in artifacts:
                artifacts[alias] = document[alias]

    return {
        "schema_id": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": "1.0",
        "producer": {
            "name": "gf-wordbench",
            "version": "legacy-unknown",
        },
        "metadata": metadata,
        "totals": totals_source,
        "artifacts": artifacts,
        "file_results": _copy_json_array(
            document.get("file_results", []),
            field="file_results",
        ),
        "scenario_results": _copy_json_array(
            document.get("scenario_results", []),
            field="scenario_results",
        ),
        "diff_entries": _copy_json_array(
            document.get("diff_entries", []),
            field="diff_entries",
        ),
        "top_errors": _legacy_top_errors_value(
            document.get("top_errors", []),
        ),
    }


def _validate_canonical_document(
    document: JsonObject,
    *,
    summary_path: Path,
    strict: bool,
    warnings: list[SummaryLoadWarning],
) -> tuple[int, int]:
    for field in _REQUIRED_ROOT_FIELDS:
        if field not in document:
            raise _schema_error(
                "Run summary is missing a required root field",
                field=field,
                summary_path=summary_path,
            )

    schema_id = _require_non_empty_string(
        document.get("schema_id"),
        field="schema_id",
    )
    if schema_id != RUN_SUMMARY_SCHEMA_ID:
        raise _schema_error(
            "Run summary uses the wrong schema identity",
            field="schema_id",
            detail=f"expected {RUN_SUMMARY_SCHEMA_ID!r}, got {schema_id!r}",
            summary_path=summary_path,
        )

    version = _require_non_empty_string(
        document.get("schema_version"),
        field="schema_version",
    )
    major, minor = _parse_schema_version(
        version,
        summary_path=summary_path,
    )
    if major != SUPPORTED_RUN_SUMMARY_MAJOR:
        raise UnsupportedVersionError(
            "Unsupported run-summary schema major version",
            code="GF-WB-SCHEMA-001",
            detail=(
                f"supported major={SUPPORTED_RUN_SUMMARY_MAJOR}; "
                f"baseline version={version}"
            ),
            stage="regression",
            operation="load-baseline",
            subject=os.fspath(summary_path),
        )

    metadata = _require_object(
        document.get("metadata"),
        field="metadata",
    )
    totals = _require_object(
        document.get("totals"),
        field="totals",
    )
    _require_object(document.get("artifacts"), field="artifacts")
    _require_array(document.get("file_results"), field="file_results")
    _require_array(
        document.get("scenario_results"),
        field="scenario_results",
    )
    _require_array(document.get("diff_entries"), field="diff_entries")
    _require_array(document.get("top_errors"), field="top_errors")

    _validate_comparison_metadata(
        metadata,
        summary_path=summary_path,
        strict=strict,
        warnings=warnings,
    )
    _validate_totals(
        totals,
        summary_path=summary_path,
        strict=strict,
    )
    _validate_file_result_identities(
        cast(list[JsonValue], document["file_results"]),
        summary_path=summary_path,
        strict=strict,
        warnings=warnings,
    )
    _validate_scenario_result_identities(
        cast(list[JsonValue], document["scenario_results"]),
        summary_path=summary_path,
    )
    _validate_diff_entries(
        cast(list[JsonValue], document["diff_entries"]),
        summary_path=summary_path,
    )

    return major, minor


def _validate_comparison_metadata(
    metadata: JsonObject,
    *,
    summary_path: Path,
    strict: bool,
    warnings: list[SummaryLoadWarning],
) -> None:
    required = _REQUIRED_METADATA_FIELDS if strict else (
        "run_id",
        "mode",
        "target_file",
        "project_id",
    )
    for field in required:
        if field not in metadata:
            raise _schema_error(
                "Run summary metadata is missing a required field",
                field=f"metadata.{field}",
                summary_path=summary_path,
            )

    run_id = _require_non_empty_string(
        metadata.get("run_id"),
        field="metadata.run_id",
    )
    try:
        validate_run_id(run_id)
    except (TypeError, ValueError) as exc:
        raise _schema_error(
            "Run summary contains an invalid run ID",
            field="metadata.run_id",
            detail=str(exc),
            summary_path=summary_path,
        ) from exc

    project_id = _require_non_empty_string(
        metadata.get("project_id"),
        field="metadata.project_id",
    )
    try:
        validate_project_id(project_id)
    except (TypeError, ValueError) as exc:
        raise _schema_error(
            "Run summary contains an invalid project ID",
            field="metadata.project_id",
            detail=str(exc),
            summary_path=summary_path,
        ) from exc

    mode = _require_non_empty_string(
        metadata.get("mode"),
        field="metadata.mode",
    )
    try:
        ValidationMode(mode)
    except ValueError as exc:
        raise _schema_error(
            "Run summary contains an unknown validation mode",
            field="metadata.mode",
            detail=mode,
            summary_path=summary_path,
        ) from exc

    target = metadata.get("target_file")
    if target is not None:
        _require_non_empty_string(
            target,
            field="metadata.target_file",
        )
        _validate_canonical_relative_path(
            cast(str, target),
            field="metadata.target_file",
        )

    if mode == ValidationMode.QUICK.value and target is None:
        _warn(
            warnings,
            "quick-target-missing",
            "Quick baseline has no stable target identity",
        )

    if strict:
        for field in ("duration_ms", "timeout_sec", "max_files"):
            _require_non_negative_integer(
                metadata.get(field),
                field=f"metadata.{field}",
            )
        for field in (
            "skip_version_probe",
            "no_compile",
            "emit_cpu_stats",
            "keep_ok_details",
            "diff_previous",
        ):
            _require_bool(
                metadata.get(field),
                field=f"metadata.{field}",
            )
        gf_path = _require_array(
            metadata.get("gf_path"),
            field="metadata.gf_path",
        )
        for index, value in enumerate(gf_path):
            _require_non_empty_string(
                value,
                field=f"metadata.gf_path[{index}]",
            )


def _normalize_totals(
    value: JsonValue | None,
    *,
    file_results: JsonValue | None,
    scenario_results: JsonValue | None,
    warnings: list[SummaryLoadWarning],
) -> JsonObject:
    totals = _copy_json_object(
        _require_object(value, field="totals")
    )
    aliases = {
        "ok": "files_ok",
        "fail": "files_fail",
        "error": "files_error",
        "skipped": "files_skipped",
    }
    for old, new in aliases.items():
        if new not in totals and old in totals:
            totals[new] = totals[old]
            _warn(
                warnings,
                "legacy-total",
                f"Migrated totals.{old} to totals.{new}",
            )

    files = _array_or_empty(file_results)
    scenarios = _array_or_empty(scenario_results)
    file_counts = _status_counts(files)
    scenario_counts = _status_counts(scenarios)

    defaults: dict[str, int] = {
        "files_seen": len(files),
        "files_included": len(files),
        "files_excluded": 0,
        "files_ok": file_counts[ValidationStatus.OK.value],
        "files_fail": file_counts[ValidationStatus.FAIL.value],
        "files_error": file_counts[ValidationStatus.ERROR.value],
        "files_skipped": file_counts[ValidationStatus.SKIPPED.value],
        "direct_fail": 0,
        "downstream_fail": 0,
        "ambiguous_fail": 0,
        "excluded_noise": 0,
        "scenarios_seen": len(scenarios),
        "scenarios_ok": scenario_counts[ValidationStatus.OK.value],
        "scenarios_fail": scenario_counts[ValidationStatus.FAIL.value],
        "scenarios_error": scenario_counts[ValidationStatus.ERROR.value],
        "scenarios_skipped": scenario_counts[ValidationStatus.SKIPPED.value],
        "required_scenario_fail": _required_scenario_failure_count(
            scenarios
        ),
    }
    for field, default in defaults.items():
        if field not in totals:
            totals[field] = default
            _warn(
                warnings,
                "legacy-total-default",
                f"Derived missing totals.{field}",
            )

    if "overall_status" not in totals:
        totals["overall_status"] = _derive_overall_status(totals)
        _warn(
            warnings,
            "legacy-overall-status",
            "Derived missing totals.overall_status",
        )
    return totals


def _validate_totals(
    totals: JsonObject,
    *,
    summary_path: Path,
    strict: bool,
) -> None:
    for field in _TOTAL_COUNT_FIELDS:
        if field not in totals:
            raise _schema_error(
                "Run summary totals are incomplete",
                field=f"totals.{field}",
                summary_path=summary_path,
            )
        _require_non_negative_integer(
            totals[field],
            field=f"totals.{field}",
        )

    overall = _require_non_empty_string(
        totals.get("overall_status"),
        field="totals.overall_status",
    )
    try:
        OverallStatus(overall)
    except ValueError as exc:
        raise _schema_error(
            "Run summary contains an unknown overall status",
            field="totals.overall_status",
            detail=overall,
            summary_path=summary_path,
        ) from exc

    if not strict:
        return

    files_included = cast(int, totals["files_included"])
    file_sum = sum(
        cast(int, totals[field])
        for field in (
            "files_ok",
            "files_fail",
            "files_error",
            "files_skipped",
        )
    )
    if files_included != file_sum:
        raise _schema_error(
            "Run summary file totals are inconsistent",
            field="totals.files_included",
            detail=f"declared={files_included}; calculated={file_sum}",
            summary_path=summary_path,
        )

    files_seen = cast(int, totals["files_seen"])
    files_excluded = cast(int, totals["files_excluded"])
    if files_seen != files_included + files_excluded:
        raise _schema_error(
            "Run summary file inventory totals are inconsistent",
            field="totals.files_seen",
            detail=(
                f"declared={files_seen}; "
                f"calculated={files_included + files_excluded}"
            ),
            summary_path=summary_path,
        )

    scenarios_seen = cast(int, totals["scenarios_seen"])
    scenario_sum = sum(
        cast(int, totals[field])
        for field in (
            "scenarios_ok",
            "scenarios_fail",
            "scenarios_error",
            "scenarios_skipped",
        )
    )
    if scenarios_seen != scenario_sum:
        raise _schema_error(
            "Run summary scenario totals are inconsistent",
            field="totals.scenarios_seen",
            detail=f"declared={scenarios_seen}; calculated={scenario_sum}",
            summary_path=summary_path,
        )


def _normalize_artifacts(
    value: JsonValue | None,
    *,
    run_dir: str | None,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> JsonObject:
    source = _copy_json_object(
        _require_object(value, field="artifacts")
    )
    normalized: JsonObject = {}

    for canonical, aliases in _ARTIFACT_ALIASES.items():
        found: JsonValue | None = None
        found_alias: str | None = None
        for alias in aliases:
            if alias in source:
                found = source[alias]
                found_alias = alias
                break
        if found is None:
            continue
        if not isinstance(found, str) or not found:
            raise _schema_error(
                "Artifact path must be a non-empty string",
                field=f"artifacts.{found_alias}",
            )
        normalized[canonical] = _normalize_run_artifact_path(
            found,
            field=f"artifacts.{canonical}",
            run_dir=run_dir,
            summary_path=summary_path,
            warnings=warnings,
        )
        if found_alias != canonical:
            _warn(
                warnings,
                "legacy-artifact-alias",
                f"Migrated artifacts.{found_alias} to artifacts.{canonical}",
            )

    if "summary_json" not in normalized:
        normalized["summary_json"] = SUMMARY_FILENAME
    return normalized


def _normalize_file_results(
    value: JsonValue | None,
    *,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> list[JsonValue]:
    items = _copy_json_array(value, field="file_results")
    normalized: list[JsonValue] = []

    for index, item in enumerate(items):
        result = _copy_json_object(
            _require_object(item, field=f"file_results[{index}]")
        )
        result["file_path"] = _normalize_project_path(
            result.get("file_path"),
            field=f"file_results[{index}].file_path",
            project_root=project_root,
            warnings=warnings,
        )
        if "status" not in result:
            result["status"] = _infer_result_status(
                result,
                field=f"file_results[{index}]",
            )
            _warn(
                warnings,
                "legacy-result-status",
                f"Derived file_results[{index}].status",
            )
        _canonical_validation_status(
            result["status"],
            field=f"file_results[{index}].status",
        )
        normalized.append(result)

    normalized.sort(
        key=lambda item: cast(dict[str, JsonValue], item)[
            "file_path"
        ].casefold()
        if isinstance(
            cast(dict[str, JsonValue], item)["file_path"],
            str,
        )
        else "",
    )
    return normalized


def _normalize_scenario_results(
    value: JsonValue | None,
    *,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> list[JsonValue]:
    items = _copy_json_array(value, field="scenario_results")
    normalized: list[JsonValue] = []

    for index, item in enumerate(items):
        result = _copy_json_object(
            _require_object(
                item,
                field=f"scenario_results[{index}]",
            )
        )
        scenario_id = result.get("scenario_id", result.get("id"))
        result["scenario_id"] = _require_non_empty_string(
            scenario_id,
            field=f"scenario_results[{index}].scenario_id",
        )
        for path_field in ("script_path", "gold_path"):
            if path_field in result:
                result[path_field] = _normalize_optional_project_path(
                    result[path_field],
                    field=f"scenario_results[{index}].{path_field}",
                    project_root=project_root,
                    warnings=warnings,
                )
        if "status" not in result:
            result["status"] = _infer_result_status(
                result,
                field=f"scenario_results[{index}]",
            )
            _warn(
                warnings,
                "legacy-result-status",
                f"Derived scenario_results[{index}].status",
            )
        _canonical_validation_status(
            result["status"],
            field=f"scenario_results[{index}].status",
        )
        normalized.append(result)

    return normalized


def _normalize_diff_entries(
    value: JsonValue | None,
    *,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> list[JsonValue]:
    items = _copy_json_array(value, field="diff_entries")
    normalized: list[JsonValue] = []

    for index, item in enumerate(items):
        entry = _copy_json_object(
            _require_object(item, field=f"diff_entries[{index}]")
        )
        if "subject_id" not in entry and "file_path" in entry:
            entry["subject_kind"] = "file"
            entry["subject_id"] = entry["file_path"]
            _warn(
                warnings,
                "legacy-diff-entry",
                f"Migrated diff_entries[{index}].file_path",
            )
        kind = _require_non_empty_string(
            entry.get("subject_kind"),
            field=f"diff_entries[{index}].subject_kind",
        )
        if kind not in {"file", "scenario", "run"}:
            raise _schema_error(
                "Diff entry contains an unknown subject kind",
                field=f"diff_entries[{index}].subject_kind",
                detail=kind,
            )
        subject_id = entry.get("subject_id")
        if kind == "file":
            entry["subject_id"] = _normalize_project_path(
                subject_id,
                field=f"diff_entries[{index}].subject_id",
                project_root=project_root,
                warnings=warnings,
            )
        else:
            entry["subject_id"] = _require_non_empty_string(
                subject_id,
                field=f"diff_entries[{index}].subject_id",
            )
        normalized.append(entry)

    return normalized


def _normalize_top_errors(
    value: JsonValue | None,
    *,
    warnings: list[SummaryLoadWarning],
) -> list[JsonValue]:
    if value is None:
        return []
    if isinstance(value, dict):
        records: list[JsonValue] = []
        for message, count in value.items():
            _require_non_empty_text(message, field="top error message")
            _require_non_negative_integer(
                count,
                field=f"top_errors[{message!r}]",
            )
            records.append({"message": message, "count": count})
        records.sort(
            key=lambda item: (
                -cast(int, cast(dict[str, JsonValue], item)["count"]),
                cast(str, cast(dict[str, JsonValue], item)["message"]).casefold(),
            )
        )
        _warn(
            warnings,
            "legacy-top-errors",
            "Migrated top-errors mapping to canonical records",
        )
        return records
    return _copy_json_array(value, field="top_errors")


def _validate_file_result_identities(
    items: list[JsonValue],
    *,
    summary_path: Path,
    strict: bool,
    warnings: list[SummaryLoadWarning],
) -> None:
    exact: set[str] = set()
    folded: dict[str, str] = {}

    for index, item in enumerate(items):
        result = _require_object(
            item,
            field=f"file_results[{index}]",
        )
        path = _require_non_empty_string(
            result.get("file_path"),
            field=f"file_results[{index}].file_path",
        )
        _validate_canonical_relative_path(
            path,
            field=f"file_results[{index}].file_path",
        )
        if path in exact:
            raise _schema_error(
                "Run summary contains duplicate file identity",
                field=f"file_results[{index}].file_path",
                detail=path,
                summary_path=summary_path,
            )
        exact.add(path)

        folded_key = path.casefold()
        prior = folded.get(folded_key)
        if prior is not None and prior != path:
            message = (
                "File identities differ only by case: "
                f"{prior!r} and {path!r}"
            )
            if strict:
                raise _schema_error(
                    "Run summary contains case-ambiguous file identities",
                    field=f"file_results[{index}].file_path",
                    detail=message,
                    summary_path=summary_path,
                )
            _warn(
                warnings,
                "case-ambiguous-file-identity",
                message,
            )
        folded[folded_key] = path

        _canonical_validation_status(
            result.get("status"),
            field=f"file_results[{index}].status",
        )


def _validate_scenario_result_identities(
    items: list[JsonValue],
    *,
    summary_path: Path,
) -> None:
    identities: set[str] = set()
    for index, item in enumerate(items):
        result = _require_object(
            item,
            field=f"scenario_results[{index}]",
        )
        scenario_id = _require_non_empty_string(
            result.get("scenario_id"),
            field=f"scenario_results[{index}].scenario_id",
        )
        if scenario_id in identities:
            raise _schema_error(
                "Run summary contains duplicate scenario identity",
                field=f"scenario_results[{index}].scenario_id",
                detail=scenario_id,
                summary_path=summary_path,
            )
        identities.add(scenario_id)
        _canonical_validation_status(
            result.get("status"),
            field=f"scenario_results[{index}].status",
        )


def _validate_diff_entries(
    items: list[JsonValue],
    *,
    summary_path: Path,
) -> None:
    identities: set[tuple[str, str]] = set()
    for index, item in enumerate(items):
        entry = _require_object(
            item,
            field=f"diff_entries[{index}]",
        )
        kind = _require_non_empty_string(
            entry.get("subject_kind"),
            field=f"diff_entries[{index}].subject_kind",
        )
        subject_id = _require_non_empty_string(
            entry.get("subject_id"),
            field=f"diff_entries[{index}].subject_id",
        )
        identity = (kind, subject_id)
        if identity in identities:
            raise _schema_error(
                "Run summary contains duplicate diff identity",
                field=f"diff_entries[{index}]",
                detail=f"{kind}:{subject_id}",
                summary_path=summary_path,
            )
        identities.add(identity)


def _canonical_mode(
    value: JsonValue | None,
    *,
    warnings: list[SummaryLoadWarning],
) -> str:
    mode = _require_non_empty_string(value, field="metadata.mode")
    canonical = _MODE_ALIASES.get(mode, mode)
    if canonical != mode:
        _warn(
            warnings,
            "legacy-mode",
            f"Migrated validation mode {mode!r} to {canonical!r}",
        )
    try:
        return ValidationMode(canonical).value
    except ValueError as exc:
        raise _schema_error(
            "Run summary contains an unknown validation mode",
            field="metadata.mode",
            detail=mode,
        ) from exc


def _resolve_run_id(
    value: JsonValue | None,
    *,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> str:
    if value is None or value == "":
        match = _RUN_DIRECTORY_RE.fullmatch(summary_path.parent.name)
        if match is None:
            raise _schema_error(
                "Legacy baseline has no recoverable run ID",
                field="metadata.run_id",
                summary_path=summary_path,
            )
        value = match.group("run_id")
        _warn(
            warnings,
            "legacy-run-id",
            "Inferred run ID from the baseline directory name",
        )

    run_id = _require_non_empty_string(value, field="metadata.run_id")
    try:
        return str(validate_run_id(run_id))
    except (TypeError, ValueError) as exc:
        raise _schema_error(
            "Run summary contains an invalid run ID",
            field="metadata.run_id",
            detail=str(exc),
            summary_path=summary_path,
        ) from exc


def _resolve_project_id(
    value: JsonValue | None,
    *,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> str:
    if value is None or value == "":
        if project_root is None:
            raise _schema_error(
                "Legacy baseline has no recoverable project identity",
                field="metadata.project_id",
            )
        inferred = _path_name(project_root)
        try:
            value = str(validate_project_id(inferred))
        except (TypeError, ValueError) as exc:
            raise _schema_error(
                "Legacy project root cannot provide a canonical project ID",
                field="metadata.project_id",
                detail=str(exc),
            ) from exc
        _warn(
            warnings,
            "legacy-project-id",
            "Inferred project ID from the legacy project root",
        )

    project_id = _require_non_empty_string(
        value,
        field="metadata.project_id",
    )
    try:
        return str(validate_project_id(project_id))
    except (TypeError, ValueError) as exc:
        raise _schema_error(
            "Run summary contains an invalid project ID",
            field="metadata.project_id",
            detail=str(exc),
        ) from exc


def _normalize_project_path(
    value: JsonValue | None,
    *,
    field: str,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> str:
    raw = _require_non_empty_string(value, field=field)
    portable = raw.replace("\\", "/")

    if _is_absolute_portable_path(raw):
        if project_root is None:
            raise _schema_error(
                "Absolute legacy project path cannot be made portable",
                field=field,
                detail=raw,
            )
        relative = _relative_to_legacy_root(raw, project_root)
        if relative is None:
            raise _schema_error(
                "Absolute legacy project path escapes its project root",
                field=field,
                detail=raw,
            )
        portable = relative
        _warn(
            warnings,
            "legacy-absolute-project-path",
            f"Converted absolute {field} to project-relative identity",
        )

    normalized = _canonical_relative_path(portable, field=field)
    return normalized


def _normalize_optional_project_path(
    value: JsonValue | None,
    *,
    field: str,
    project_root: str | None,
    warnings: list[SummaryLoadWarning],
) -> str | None:
    if value is None or value == "":
        return None
    return _normalize_project_path(
        value,
        field=field,
        project_root=project_root,
        warnings=warnings,
    )


def _normalize_run_artifact_path(
    value: str,
    *,
    field: str,
    run_dir: str | None,
    summary_path: Path,
    warnings: list[SummaryLoadWarning],
) -> str:
    raw = value.replace("\\", "/")
    if not _is_absolute_portable_path(value):
        return _canonical_relative_path(raw, field=field)

    baseline_root = run_dir or summary_path.parent.as_posix()
    relative = _relative_to_legacy_root(value, baseline_root)
    if relative is None:
        raise _schema_error(
            "Absolute legacy artifact path escapes the baseline run directory",
            field=field,
            detail=value,
            summary_path=summary_path,
        )
    _warn(
        warnings,
        "legacy-absolute-artifact-path",
        f"Converted absolute {field} to run-relative form",
    )
    return _canonical_relative_path(relative, field=field)


def _relative_to_legacy_root(
    value: str,
    root: str,
) -> str | None:
    if _looks_windows_path(value) or _looks_windows_path(root):
        candidate = PureWindowsPath(value)
        parent = PureWindowsPath(root)
        try:
            relative = candidate.relative_to(parent)
        except ValueError:
            return None
        return PurePosixPath(*relative.parts).as_posix()

    candidate = Path(value)
    parent = Path(root)
    try:
        relative = candidate.relative_to(parent)
    except ValueError:
        return None
    return relative.as_posix()


def _canonical_relative_path(value: str, *, field: str) -> str:
    portable = value.replace("\\", "/")
    path = PurePosixPath(portable)
    if not portable or portable == ".":
        raise _schema_error(
            "Canonical path must not be empty",
            field=field,
        )
    if path.is_absolute() or _WINDOWS_ABSOLUTE_RE.match(portable):
        raise _schema_error(
            "Canonical path must be relative",
            field=field,
            detail=value,
        )
    if any(part in {"", ".", ".."} for part in path.parts):
        raise _schema_error(
            "Canonical path contains a prohibited segment",
            field=field,
            detail=value,
        )
    if "\x00" in portable:
        raise _schema_error(
            "Canonical path contains NUL",
            field=field,
        )
    return path.as_posix()


def _validate_canonical_relative_path(value: str, *, field: str) -> None:
    normalized = _canonical_relative_path(value, field=field)
    if normalized != value:
        raise _schema_error(
            "Canonical path is not normalized",
            field=field,
            detail=f"expected {normalized!r}, got {value!r}",
        )


def _status_counts(items: Sequence[JsonValue]) -> dict[str, int]:
    counts = {
        ValidationStatus.OK.value: 0,
        ValidationStatus.FAIL.value: 0,
        ValidationStatus.ERROR.value: 0,
        ValidationStatus.SKIPPED.value: 0,
    }
    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
    return counts


def _required_scenario_failure_count(
    items: Sequence[JsonValue],
) -> int:
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("required") is not True:
            continue
        if item.get("status") in {
            ValidationStatus.FAIL.value,
            ValidationStatus.ERROR.value,
        }:
            count += 1
    return count


def _derive_overall_status(totals: JsonObject) -> str:
    if cast(int, totals.get("files_error", 0)) > 0:
        return OverallStatus.ERROR.value
    if cast(int, totals.get("scenarios_error", 0)) > 0:
        return OverallStatus.ERROR.value
    if cast(int, totals.get("files_fail", 0)) > 0:
        return OverallStatus.FAIL.value
    if cast(int, totals.get("required_scenario_fail", 0)) > 0:
        return OverallStatus.FAIL.value
    return OverallStatus.OK.value


def _infer_result_status(result: JsonObject, *, field: str) -> str:
    existing = result.get("overall_status")
    if isinstance(existing, str):
        return _canonical_validation_status(
            existing,
            field=f"{field}.overall_status",
        )

    compile_summary = result.get("compile_summary")
    if isinstance(compile_summary, dict):
        if compile_summary.get("timed_out") is True:
            return ValidationStatus.ERROR.value
        exit_code = compile_summary.get("exit_code")
        error_kind = compile_summary.get("error_kind")
        if exit_code == 0 and error_kind in {None, "OK"}:
            return ValidationStatus.OK.value
        if exit_code is None:
            return ValidationStatus.ERROR.value
        return ValidationStatus.FAIL.value

    if result.get("skipped") is True:
        return ValidationStatus.SKIPPED.value
    if result.get("timed_out") is True:
        return ValidationStatus.ERROR.value
    if result.get("ok") is True or result.get("passed") is True:
        return ValidationStatus.OK.value
    if result.get("ok") is False or result.get("passed") is False:
        return ValidationStatus.FAIL.value

    raise _schema_error(
        "Legacy result has no recoverable validation status",
        field=f"{field}.status",
    )


def _canonical_validation_status(
    value: JsonValue | None,
    *,
    field: str,
) -> str:
    status = _require_non_empty_string(value, field=field)
    try:
        return ValidationStatus(status).value
    except ValueError as exc:
        raise _schema_error(
            "Result contains an unknown validation status",
            field=field,
            detail=status,
        ) from exc


def _parse_schema_version(
    value: str,
    *,
    summary_path: Path,
) -> tuple[int, int]:
    match = _VERSION_RE.fullmatch(value)
    if match is None:
        raise _schema_error(
            "Run summary schema version must use MAJOR.MINOR",
            field="schema_version",
            detail=value,
            summary_path=summary_path,
        )
    return int(match.group("major")), int(match.group("minor"))


def _resolve_optional_root(
    root: str | os.PathLike[str] | None,
) -> Path | None:
    if root is None:
        return None
    candidate = _coerce_path(root, field="approved_root")
    if not candidate.is_absolute():
        raise ValueError("approved_root must be absolute")
    try:
        return require_directory(
            candidate,
            role="regression output root",
        )
    except OSError as exc:
        raise _evidence_error(
            "Regression output root is unavailable",
            candidate,
            detail=_bounded_exception(exc),
        ) from exc


def _source_path(
    source: str | os.PathLike[str],
    *,
    approved_root: Path | None,
) -> Path:
    candidate = _coerce_path(source, field="source")
    if candidate.is_absolute():
        return candidate
    if approved_root is None:
        raise ValueError(
            "relative regression baseline paths require approved_root"
        )
    return approved_root / candidate


def _coerce_path(
    value: str | os.PathLike[str],
    *,
    field: str,
) -> Path:
    raw = os.fspath(value)
    if isinstance(raw, bytes):
        raise TypeError(f"{field} must be a text path")
    if "\x00" in raw:
        raise ValueError(f"{field} must not contain NUL")
    return Path(raw).expanduser()


def _copy_first(
    destination: JsonObject,
    field: str,
    *sources: Mapping[str, JsonValue],
) -> None:
    for source in sources:
        if field in source:
            destination[field] = _copy_json_value(source[field])
            return


def _normalize_legacy_total_field(
    value: JsonValue | None,
    *,
    default: int,
    field: str,
) -> int:
    if value is None:
        return default
    return _require_non_negative_integer(value, field=field)


def _legacy_top_errors_value(value: JsonValue | None) -> JsonValue:
    if value is None:
        return []
    return _copy_json_value(value)


def _object_or_empty(value: JsonValue | None) -> JsonObject:
    if value is None:
        return {}
    return _copy_json_object(_require_object(value, field="legacy object"))


def _array_or_empty(value: JsonValue | None) -> list[JsonValue]:
    if value is None:
        return []
    return _require_array(value, field="legacy array")


def _require_object(
    value: JsonValue | FrozenJsonValue | None,
    *,
    field: str,
) -> JsonObject:
    if not isinstance(value, dict):
        raise _schema_error(
            "Run summary field must be an object",
            field=field,
            detail=type(value).__name__,
        )
    return cast(JsonObject, value)


def _require_array(
    value: JsonValue | FrozenJsonValue | None,
    *,
    field: str,
) -> list[JsonValue]:
    if not isinstance(value, list):
        raise _schema_error(
            "Run summary field must be an array",
            field=field,
            detail=type(value).__name__,
        )
    return cast(list[JsonValue], value)


def _require_non_empty_string(
    value: JsonValue | FrozenJsonValue | None,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise _schema_error(
            "Run summary field must be a string",
            field=field,
            detail=type(value).__name__,
        )
    _require_non_empty_text(value, field=field)
    return value


def _optional_non_empty_string(
    value: JsonValue | None,
    *,
    field: str,
) -> str | None:
    if value is None or value == "":
        return None
    return _require_non_empty_string(value, field=field)


def _require_non_empty_text(value: str, *, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")


def _require_non_negative_integer(
    value: JsonValue | FrozenJsonValue | None,
    *,
    field: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _schema_error(
            "Run summary field must be an integer",
            field=field,
            detail=type(value).__name__,
        )
    if value < 0:
        raise _schema_error(
            "Run summary integer must be non-negative",
            field=field,
            detail=str(value),
        )
    return value


def _require_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a bool")
    return cast(bool, value)


def _validate_max_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_bytes must be an integer")
    if value < 1:
        raise ValueError("max_bytes must be positive")
    return value


def _copy_json_object(value: Mapping[str, JsonValue]) -> JsonObject:
    return {
        key: _copy_json_value(item)
        for key, item in value.items()
    }


def _copy_json_array(
    value: JsonValue | None,
    *,
    field: str,
) -> list[JsonValue]:
    return [
        _copy_json_value(item)
        for item in _require_array(value, field=field)
    ]


def _copy_json_value(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return _copy_json_object(value)
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    return value


def _freeze_json(value: JsonValue | JsonObject) -> FrozenJsonValue:
    if isinstance(value, dict):
        return MappingProxyType(
            {
                key: _freeze_json(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return cast(FrozenJsonScalar, value)


def _frozen_object(
    value: Mapping[str, FrozenJsonValue],
    field: str,
) -> Mapping[str, FrozenJsonValue]:
    item = value.get(field)
    if not isinstance(item, Mapping):
        raise TypeError(f"{field} must be an object")
    return cast(Mapping[str, FrozenJsonValue], item)


def _frozen_object_array(
    value: Mapping[str, FrozenJsonValue],
    field: str,
) -> tuple[Mapping[str, FrozenJsonValue], ...]:
    item = value.get(field)
    if not isinstance(item, tuple):
        raise TypeError(f"{field} must be an array")
    result: list[Mapping[str, FrozenJsonValue]] = []
    for index, element in enumerate(item):
        if not isinstance(element, Mapping):
            raise TypeError(f"{field}[{index}] must be an object")
        result.append(cast(Mapping[str, FrozenJsonValue], element))
    return tuple(result)


def _frozen_string(
    value: Mapping[str, FrozenJsonValue],
    field: str,
) -> str:
    item = value.get(field)
    if not isinstance(item, str):
        raise TypeError(f"{field} must be a string")
    return item


def _schema_error(
    message: str,
    *,
    field: str,
    detail: str = "",
    summary_path: Path | None = None,
) -> SchemaValidationError:
    context = field if not detail else f"{field}: {detail}"
    return SchemaValidationError(
        message,
        code="GF-WB-SCHEMA-001",
        detail=context,
        stage="regression",
        operation="load-baseline",
        subject=None if summary_path is None else os.fspath(summary_path),
    )


def _evidence_error(
    message: str,
    path: Path,
    *,
    detail: str,
) -> EvidenceIOError:
    return EvidenceIOError(
        message,
        code="GF-WB-IO-001",
        detail=detail,
        stage="regression",
        operation="load-baseline",
        subject=os.fspath(path),
    )


def _bounded_exception(exc: BaseException, limit: int = 240) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _warn(
    warnings: list[SummaryLoadWarning],
    code: str,
    message: str,
) -> None:
    warning = SummaryLoadWarning(code=code, message=message)
    if warning not in warnings:
        warnings.append(warning)


def _is_absolute_portable_path(value: str) -> bool:
    return value.startswith("/") or bool(_WINDOWS_ABSOLUTE_RE.match(value))


def _looks_windows_path(value: str) -> bool:
    return bool(_WINDOWS_ABSOLUTE_RE.match(value)) or "\\" in value


def _path_name(value: str) -> str:
    if _looks_windows_path(value):
        return PureWindowsPath(value).name
    return Path(value).name


__all__ = (
    "DEFAULT_MAX_SUMMARY_BYTES",
    "LoadedRunSummary",
    "RUN_SUMMARY_SCHEMA_ID",
    "SUMMARY_FILENAME",
    "SUPPORTED_RUN_SUMMARY_MAJOR",
    "SummaryForm",
    "SummaryLoadAttempt",
    "SummaryLoadWarning",
    "load_previous_summary",
    "resolve_summary_path",
    "try_load_previous_summary",
)
