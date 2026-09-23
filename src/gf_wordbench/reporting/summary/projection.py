"""Canonical projection of completed run results into summary schema 1.0."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from enum import Enum
from pathlib import Path, PurePath
from typing import Final, TypeAlias

from gf_wordbench.kernel.serialization import (
    JsonValue,
    format_rfc3339_utc,
    path_to_portable_string,
)
from gf_wordbench.version import __version__

SUMMARY_SCHEMA_ID: Final[str] = "gf-wordbench.run-summary"
SUMMARY_SCHEMA_VERSION: Final[str] = "1.0"
SUMMARY_PRODUCER_NAME: Final[str] = "gf-wordbench"

_SCAN_COUNT_FIELDS: Final[tuple[str, ...]] = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
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
_ARTIFACT_FIELDS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("summary_json", ("summary_json", "summary_json_path")),
    ("summary_markdown", ("summary_md", "summary_markdown", "summary_md_path")),
    ("ai_ready", ("ai_ready_md", "ai_ready", "ai_ready_path")),
    ("top_errors", ("top_errors_txt", "top_errors_path")),
    ("manifest", ("manifest_json", "manifest_path")),
    ("master_log", ("master_log",)),
    ("all_scan_logs", ("all_scan_logs",)),
    ("all_logs", ("all_logs",)),
    ("details_dir", ("details_dir",)),
    ("raw_dir", ("raw_dir",)),
    ("compile_logs_dir", ("raw_compile_dir", "compile_logs_dir")),
    ("scan_logs_dir", ("raw_scan_dir", "scan_logs_dir")),
    ("scenario_logs_dir", ("raw_scenarios_dir", "scenario_logs_dir")),
    ("artifacts_dir", ("artifacts_dir",)),
    ("gfo_dir", ("gfo_dir",)),
    ("out_dir", ("out_dir",)),
    ("pgf_dir", ("pgf_dir",)),
)
_CHANGE_ORDER: Final[Mapping[str, int]] = {
    "regressed": 0,
    "new": 1,
    "improved": 2,
    "removed": 3,
    "unchanged": 4,
}
_CANONICAL_MODES: Final[frozenset[str]] = frozenset(
    {"quick", "checkpoint", "release", "diagnostic"}
)
_MODE_ALIASES: Final[Mapping[str, str]] = {
    "file": "quick",
    "all": "diagnostic",
}
_MAX_ITEMS: Final[int] = 100_000

SummaryDocument: TypeAlias = dict[str, JsonValue]


class SummaryProjectionError(ValueError):
    pass


def build_summary_document(
    run_result: object,
    *,
    producer_name: str = SUMMARY_PRODUCER_NAME,
    producer_version: str = __version__,
) -> SummaryDocument:
    run_paths = _required_attr(run_result, "run_paths")
    run_config = _required_attr(run_result, "run_config")
    file_results = _sequence_attr(run_result, "file_results")
    scenario_results = _sequence_attr(run_result, "scenario_results")
    diff_entries = _sequence_attr(run_result, "diff_entries")
    top_errors = _sequence_attr(run_result, "top_errors")

    document: SummaryDocument = {
        "schema_id": SUMMARY_SCHEMA_ID,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "producer": project_producer(
            name=producer_name,
            version=producer_version,
        ),
        "metadata": project_metadata(
            run_result,
            run_config=run_config,
            run_paths=run_paths,
        ),
        "totals": project_totals(
            _required_attr(run_result, "totals"),
            overall_status=_required_attr(run_result, "overall_status"),
        ),
        "artifacts": project_artifacts(run_paths),
        "file_results": [
            project_file_result(
                result,
                run_config=run_config,
                run_paths=run_paths,
            )
            for result in _ordered_file_results(
                file_results,
                run_config=run_config,
            )
        ],
        "scenario_results": [
            project_scenario_result(
                result,
                run_config=run_config,
                run_paths=run_paths,
            )
            for result in scenario_results
        ],
        "diff_entries": [
            project_diff_entry(entry) for entry in _ordered_diff_entries(diff_entries)
        ],
        "top_errors": [project_top_error(item) for item in _ordered_top_errors(top_errors)],
    }
    validate_projection_invariants(document)
    return document


def project_producer(
    *,
    name: str = SUMMARY_PRODUCER_NAME,
    version: str = __version__,
) -> dict[str, JsonValue]:
    return {
        "name": _non_empty_text(name, "producer.name"),
        "version": _non_empty_text(version, "producer.version"),
    }


def project_metadata(
    run_result: object,
    *,
    run_config: object | None = None,
    run_paths: object | None = None,
) -> dict[str, JsonValue]:
    config = _required_attr(run_result, "run_config") if run_config is None else run_config
    paths = _required_attr(run_result, "run_paths") if run_paths is None else run_paths
    project = _required_attr(config, "project")
    identity = _required_attr(project, "identity")
    sources = _required_attr(project, "sources")
    environment = _required_attr(config, "environment")

    run_dir = _path_attr(paths, "run_dir")
    target = _optional_attr(config, "target")
    target_value = None if target is None else _optional_attr(target, "value")
    target_file = (
        None
        if target_value is None
        else _project_relative_path(
            target_value,
            project_root=_path_attr(project, "project_root"),
            field_name="metadata.target_file",
        )
    )

    started_at = _timestamp(
        _required_attr(run_result, "started_at"),
        "metadata.started_at",
    )
    finished_at = _timestamp(
        _required_attr(run_result, "finished_at"),
        "metadata.finished_at",
    )
    metadata: dict[str, JsonValue] = {
        "run_id": _identifier(_required_attr(paths, "run_id"), "metadata.run_id"),
        "run_dir": _environment_path(run_dir, "metadata.run_dir"),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": _non_negative_int(
            _required_attr(run_result, "duration_ms"),
            "metadata.duration_ms",
        ),
        "gf_version": _text(
            _required_attr(run_result, "gf_version"),
            "metadata.gf_version",
            allow_empty=True,
        ),
        "mode": _mode(_required_attr(config, "mode")),
        "target_file": target_file,
        "project_id": _identifier(
            _first_attr(identity, ("id", "project_id")),
            "metadata.project_id",
        ),
        "project_name": _text(
            _first_attr(identity, ("name", "project_name")),
            "metadata.project_name",
        ),
        "project_root": _environment_path(
            _path_attr(environment, "project_root"),
            "metadata.project_root",
        ),
        "rgl_root": _environment_path(
            _path_attr(environment, "rgl_root"),
            "metadata.rgl_root",
        ),
        "gf_executable": _environment_path(
            _path_attr(environment, "gf_executable"),
            "metadata.gf_executable",
        ),
        "output_root": _environment_path(
            _path_attr(environment, "output_root"),
            "metadata.output_root",
        ),
        "source_directory": _project_path_value(
            _required_attr(sources, "directory"),
            "metadata.source_directory",
        ),
        "source_glob": _non_empty_text(
            _required_attr(sources, "glob"),
            "metadata.source_glob",
        ),
        "gf_path": [
            _environment_path(item, "metadata.gf_path[]")
            for item in _iterable_attr(environment, "gf_path")
        ],
        "timeout_sec": _non_negative_int(
            _required_attr(config, "timeout_sec"),
            "metadata.timeout_sec",
        ),
        "max_files": _non_negative_int(
            _required_attr(config, "max_files"),
            "metadata.max_files",
        ),
        "skip_version_probe": _boolean(
            _required_attr(config, "skip_version_probe"),
            "metadata.skip_version_probe",
        ),
        "no_compile": _boolean(
            _required_attr(config, "no_compile"),
            "metadata.no_compile",
        ),
        "emit_cpu_stats": _boolean(
            _required_attr(config, "emit_cpu_stats"),
            "metadata.emit_cpu_stats",
        ),
        "keep_ok_details": _boolean(
            _required_attr(config, "keep_ok_details"),
            "metadata.keep_ok_details",
        ),
        "diff_previous": _boolean(
            _required_attr(config, "diff_previous"),
            "metadata.diff_previous",
        ),
    }

    if finished_at < started_at:
        raise SummaryProjectionError("metadata.finished_at must not precede metadata.started_at")
    return metadata


def project_totals(
    totals: object,
    *,
    overall_status: object | None = None,
) -> dict[str, JsonValue]:
    counts: dict[str, int] = {
        field: _non_negative_int(
            _required_attr(totals, field),
            f"totals.{field}",
        )
        for field in _TOTAL_FIELDS
    }
    totals_status = _enum_text(
        _required_attr(totals, "overall_status"),
        "totals.overall_status",
    )
    if overall_status is not None:
        result_status = _enum_text(
            overall_status,
            "run_result.overall_status",
        )
        if result_status != totals_status:
            raise SummaryProjectionError(
                "run_result.overall_status must equal totals.overall_status"
            )

    if counts["files_seen"] != counts["files_included"] + counts["files_excluded"]:
        raise SummaryProjectionError("totals.files_seen must equal files_included + files_excluded")
    if counts["files_included"] != (
        counts["files_ok"]
        + counts["files_fail"]
        + counts["files_error"]
        + counts["files_skipped"]
    ):
        raise SummaryProjectionError("totals.files_included must equal file status counts")
    if counts["scenarios_seen"] != (
        counts["scenarios_ok"]
        + counts["scenarios_fail"]
        + counts["scenarios_error"]
        + counts["scenarios_skipped"]
    ):
        raise SummaryProjectionError("totals.scenarios_seen must equal scenario status counts")

    projected: dict[str, JsonValue] = dict(counts)
    projected["overall_status"] = totals_status
    return projected


def project_artifacts(run_paths: object) -> dict[str, JsonValue]:
    run_root = _path_attr(run_paths, "run_dir")
    projected: dict[str, JsonValue] = {}
    for field_name, aliases in _ARTIFACT_FIELDS:
        value = _first_attr(run_paths, aliases, required=False)
        projected[field_name] = (
            None
            if value is None
            else _run_relative_path(
                value,
                run_root=run_root,
                field_name=f"artifacts.{field_name}",
            )
        )
    return projected


def project_file_result(
    file_result: object,
    *,
    run_config: object,
    run_paths: object,
) -> dict[str, JsonValue]:
    project = _required_attr(run_config, "project")
    project_root = _path_attr(project, "project_root")
    run_root = _path_attr(run_paths, "run_dir")
    diagnostic_class = _enum_text(
        _required_attr(file_result, "diagnostic_class"),
        "file_result.diagnostic_class",
    )
    is_direct_value = _boolean(
        _required_attr(file_result, "is_direct"),
        "file_result.is_direct",
    )
    if is_direct_value != (diagnostic_class == "direct"):
        raise SummaryProjectionError("file_result.is_direct must agree with diagnostic_class")

    blocked_by = sorted(
        {
            _project_relative_path(
                item,
                project_root=project_root,
                field_name="file_result.blocked_by[]",
            )
            for item in _iterable_attr(file_result, "blocked_by")
        },
        key=lambda value: (value.casefold(), value),
    )

    return {
        "file_path": _project_relative_path(
            _required_attr(file_result, "file_path"),
            project_root=project_root,
            field_name="file_result.file_path",
        ),
        "module_name": _non_empty_text(
            _required_attr(file_result, "module_name"),
            "file_result.module_name",
        ),
        "status": _enum_text(
            _required_attr(file_result, "status"),
            "file_result.status",
        ),
        "diagnostic_class": diagnostic_class,
        "is_direct": is_direct_value,
        "blocked_by": [item for item in blocked_by],
        "scan_counts": project_scan_counts(_required_attr(file_result, "scan_counts")),
        "fingerprint": project_fingerprint(_required_attr(file_result, "fingerprint")),
        "compile_summary": project_compile_summary(
            _required_attr(file_result, "compile_summary"),
            run_root=run_root,
        ),
        "scan_log_path": _optional_run_path(
            _optional_attr(file_result, "scan_log_path"),
            run_root=run_root,
            field_name="file_result.scan_log_path",
        ),
    }


def project_scan_counts(scan_counts: object) -> dict[str, JsonValue]:
    return {
        field: _non_negative_int(
            _required_attr(scan_counts, field),
            f"scan_counts.{field}",
        )
        for field in _SCAN_COUNT_FIELDS
    }


def project_fingerprint(fingerprint: object) -> dict[str, JsonValue]:
    algorithm = _non_empty_text(
        _required_attr(fingerprint, "hash_algorithm"),
        "fingerprint.hash_algorithm",
    ).lower()
    digest = _non_empty_text(
        _required_attr(fingerprint, "hash"),
        "fingerprint.hash",
    ).lower()
    if algorithm != "sha256":
        raise SummaryProjectionError("canonical fingerprints must use sha256")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise SummaryProjectionError("fingerprint.hash must be a full lowercase SHA-256 digest")
    return {
        "size_bytes": _non_negative_int(
            _required_attr(fingerprint, "size_bytes"),
            "fingerprint.size_bytes",
        ),
        "hash_algorithm": algorithm,
        "hash": digest,
        "last_modified_utc": _timestamp(
            _required_attr(fingerprint, "last_modified_utc"),
            "fingerprint.last_modified_utc",
        ),
    }


def project_compile_summary(
    compile_summary: object,
    *,
    run_root: Path,
) -> dict[str, JsonValue]:
    return {
        "exit_code": _optional_int(
            _optional_attr(compile_summary, "exit_code"),
            "compile_summary.exit_code",
        ),
        "timed_out": _boolean(
            _required_attr(compile_summary, "timed_out"),
            "compile_summary.timed_out",
        ),
        "duration_ms": _non_negative_int(
            _required_attr(compile_summary, "duration_ms"),
            "compile_summary.duration_ms",
        ),
        "error_kind": _enum_text(
            _required_attr(compile_summary, "error_kind"),
            "compile_summary.error_kind",
        ),
        "first_error": _text(
            _required_attr(compile_summary, "first_error"),
            "compile_summary.first_error",
            allow_empty=True,
        ),
        "error_detail": _text(
            _required_attr(compile_summary, "error_detail"),
            "compile_summary.error_detail",
            allow_empty=True,
        ),
        "stdout_path": _optional_run_path(
            _optional_attr(compile_summary, "stdout_path"),
            run_root=run_root,
            field_name="compile_summary.stdout_path",
        ),
        "stderr_path": _optional_run_path(
            _optional_attr(compile_summary, "stderr_path"),
            run_root=run_root,
            field_name="compile_summary.stderr_path",
        ),
    }


def project_scenario_result(
    scenario_result: object,
    *,
    run_config: object,
    run_paths: object,
) -> dict[str, JsonValue]:
    project = _required_attr(run_config, "project")
    project_root = _path_attr(project, "project_root")
    run_root = _path_attr(run_paths, "run_dir")

    return {
        "scenario_id": _identifier(
            _required_attr(scenario_result, "scenario_id"),
            "scenario_result.scenario_id",
        ),
        "script_path": _project_relative_path(
            _required_attr(scenario_result, "script_path"),
            project_root=project_root,
            field_name="scenario_result.script_path",
        ),
        "required": _boolean(
            _required_attr(scenario_result, "required"),
            "scenario_result.required",
        ),
        "status": _enum_text(
            _required_attr(scenario_result, "status"),
            "scenario_result.status",
        ),
        "command": [
            _text(item, "scenario_result.command[]", allow_empty=False)
            for item in _iterable_attr(scenario_result, "command")
        ],
        "working_directory": _environment_path(
            _required_attr(scenario_result, "working_directory"),
            "scenario_result.working_directory",
        ),
        "exit_code": _optional_int(
            _optional_attr(scenario_result, "exit_code"),
            "scenario_result.exit_code",
        ),
        "timed_out": _boolean(
            _required_attr(scenario_result, "timed_out"),
            "scenario_result.timed_out",
        ),
        "duration_ms": _non_negative_int(
            _required_attr(scenario_result, "duration_ms"),
            "scenario_result.duration_ms",
        ),
        "stdout_path": _optional_run_path(
            _optional_attr(scenario_result, "stdout_path"),
            run_root=run_root,
            field_name="scenario_result.stdout_path",
        ),
        "stderr_path": _optional_run_path(
            _optional_attr(scenario_result, "stderr_path"),
            run_root=run_root,
            field_name="scenario_result.stderr_path",
        ),
        "normalized_output_path": _optional_run_path(
            _optional_attr(scenario_result, "normalized_output_path"),
            run_root=run_root,
            field_name="scenario_result.normalized_output_path",
        ),
        "gold_path": _optional_project_path(
            _optional_attr(scenario_result, "gold_path"),
            project_root=project_root,
            field_name="scenario_result.gold_path",
        ),
        "gold_match": _optional_boolean(
            _optional_attr(scenario_result, "gold_match"),
            "scenario_result.gold_match",
        ),
        "diagnostic_class": _enum_text(
            _required_attr(scenario_result, "diagnostic_class"),
            "scenario_result.diagnostic_class",
        ),
        "error_kind": _enum_text(
            _required_attr(scenario_result, "error_kind"),
            "scenario_result.error_kind",
        ),
        "primary_message": _text(
            _required_attr(scenario_result, "primary_message"),
            "scenario_result.primary_message",
            allow_empty=True,
        ),
        "sections": [
            project_scenario_section(section)
            for section in _sequence_attr(scenario_result, "sections")
        ],
        "artifacts": [
            _artifact_reference(
                artifact,
                run_root=run_root,
            )
            for artifact in _sequence_attr(scenario_result, "artifacts")
        ],
    }


def project_scenario_section(section: object) -> dict[str, JsonValue]:
    projected: dict[str, JsonValue] = {
        "id": _identifier(
            _first_attr(section, ("id", "section_id")),
            "scenario_section.id",
        ),
        "completed": _boolean(
            _required_attr(section, "completed"),
            "scenario_section.completed",
        ),
    }
    for field_name in ("message", "begin_line", "end_line"):
        value = _optional_attr(section, field_name)
        if value is None:
            continue
        if field_name in {"begin_line", "end_line"}:
            projected[field_name] = _non_negative_int(
                value,
                f"scenario_section.{field_name}",
            )
        else:
            projected[field_name] = _text(
                value,
                f"scenario_section.{field_name}",
                allow_empty=True,
            )
    return projected


def project_diff_entry(entry: object) -> dict[str, JsonValue]:
    return {
        "subject_kind": _non_empty_text(
            _required_attr(entry, "subject_kind"),
            "diff_entry.subject_kind",
        ),
        "subject_id": _non_empty_text(
            _first_attr(entry, ("subject_id", "file_path")),
            "diff_entry.subject_id",
        ).replace("\\", "/"),
        "previous_status": _optional_enum_text(
            _optional_attr(entry, "previous_status"),
            "diff_entry.previous_status",
        ),
        "current_status": _optional_enum_text(
            _optional_attr(entry, "current_status"),
            "diff_entry.current_status",
        ),
        "change_kind": _enum_text(
            _required_attr(entry, "change_kind"),
            "diff_entry.change_kind",
        ),
        "message": _text(
            _required_attr(entry, "message"),
            "diff_entry.message",
            allow_empty=True,
        ),
    }


def project_top_error(item: object) -> dict[str, JsonValue]:
    return {
        "error_kind": _enum_text(
            _required_attr(item, "error_kind"),
            "top_error.error_kind",
        ),
        "message": _non_empty_text(
            _required_attr(item, "message"),
            "top_error.message",
        ),
        "count": _positive_int(
            _required_attr(item, "count"),
            "top_error.count",
        ),
    }


def validate_projection_invariants(document: Mapping[str, JsonValue]) -> None:
    required = (
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
    missing = [field for field in required if field not in document]
    if missing:
        raise SummaryProjectionError(
            "summary document is missing required fields: " + ", ".join(missing)
        )
    if document["schema_id"] != SUMMARY_SCHEMA_ID:
        raise SummaryProjectionError("invalid summary schema_id")
    if document["schema_version"] != SUMMARY_SCHEMA_VERSION:
        raise SummaryProjectionError("invalid summary schema_version")

    for field in ("metadata", "totals", "artifacts"):
        if not isinstance(document[field], Mapping):
            raise SummaryProjectionError(f"summary field {field!r} must be an object")
    for field in (
        "file_results",
        "scenario_results",
        "diff_entries",
        "top_errors",
    ):
        if not isinstance(document[field], list):
            raise SummaryProjectionError(f"summary field {field!r} must be an array")

    file_results = document["file_results"]
    if not isinstance(file_results, list):
        raise SummaryProjectionError("summary field 'file_results' must be an array")
    file_paths: list[str] = []
    for index, item in enumerate(file_results):
        if not isinstance(item, Mapping):
            raise SummaryProjectionError(f"file_results[{index}] must be an object")
        file_paths.append(
            _non_empty_text(item.get("file_path"), f"file_results[{index}].file_path")
        )
    if file_paths != sorted(
        file_paths,
        key=lambda value: (value.casefold(), value),
    ):
        raise SummaryProjectionError("file_results must be ordered by normalized file_path")

    top_errors = document["top_errors"]
    if not isinstance(top_errors, list):
        raise SummaryProjectionError("summary field 'top_errors' must be an array")
    top_error_keys: list[tuple[int, str, str]] = []
    for index, item in enumerate(top_errors):
        if not isinstance(item, Mapping):
            raise SummaryProjectionError(f"top_errors[{index}] must be an object")
        count = _positive_int(item.get("count"), f"top_errors[{index}].count")
        _non_empty_text(
            item.get("error_kind"), f"top_errors[{index}].error_kind"
        )
        message = _non_empty_text(item.get("message"), f"top_errors[{index}].message")
        top_error_keys.append((-count, message.casefold(), message))
    if top_error_keys != sorted(top_error_keys):
        raise SummaryProjectionError("top_errors must use canonical deterministic ordering")


def _ordered_file_results(
    values: Sequence[object],
    *,
    run_config: object,
) -> tuple[object, ...]:
    project = _required_attr(run_config, "project")
    project_root = _path_attr(project, "project_root")
    return tuple(
        sorted(
            values,
            key=lambda item: (
                _project_relative_path(
                    _required_attr(item, "file_path"),
                    project_root=project_root,
                    field_name="file_result.file_path",
                ).casefold(),
                _project_relative_path(
                    _required_attr(item, "file_path"),
                    project_root=project_root,
                    field_name="file_result.file_path",
                ),
            ),
        )
    )


def _ordered_diff_entries(
    values: Sequence[object],
) -> tuple[object, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                _CHANGE_ORDER.get(
                    _enum_text(
                        _required_attr(item, "change_kind"),
                        "diff_entry.change_kind",
                    ),
                    99,
                ),
                _non_empty_text(
                    _required_attr(item, "subject_kind"),
                    "diff_entry.subject_kind",
                ),
                _non_empty_text(
                    _first_attr(item, ("subject_id", "file_path")),
                    "diff_entry.subject_id",
                ).casefold(),
                _non_empty_text(
                    _first_attr(item, ("subject_id", "file_path")),
                    "diff_entry.subject_id",
                ),
            ),
        )
    )


def _ordered_top_errors(
    values: Sequence[object],
) -> tuple[object, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -_positive_int(
                    _required_attr(item, "count"),
                    "top_error.count",
                ),
                _non_empty_text(
                    _required_attr(item, "message"),
                    "top_error.message",
                ).casefold(),
                _non_empty_text(
                    _required_attr(item, "message"),
                    "top_error.message",
                ),
            ),
        )
    )


def _artifact_reference(
    artifact: object,
    *,
    run_root: Path,
) -> JsonValue:
    if isinstance(artifact, (str, PurePath)):
        return _run_relative_path(
            artifact,
            run_root=run_root,
            field_name="scenario_result.artifacts[]",
        )
    path_value = _optional_attr(artifact, "path")
    if path_value is None:
        raise SummaryProjectionError("scenario artifact references must expose a path")
    return _run_relative_path(
        path_value,
        run_root=run_root,
        field_name="scenario_result.artifacts[].path",
    )


def _mode(value: object) -> str:
    canonical = _enum_text(value, "metadata.mode").strip().lower()
    canonical = _MODE_ALIASES.get(canonical, canonical)
    if canonical not in _CANONICAL_MODES:
        raise SummaryProjectionError(f"unsupported canonical validation mode: {canonical!r}")
    return canonical


def _timestamp(value: object, field_name: str) -> str:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")
    return format_rfc3339_utc(value)


def _enum_text(value: object, field_name: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _non_empty_text(value, field_name)


def _optional_enum_text(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _enum_text(value, field_name)


def _identifier(value: object, field_name: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _non_empty_text(value, field_name)


def _environment_path(value: object, field_name: str) -> str:
    path = _coerce_path(value, field_name)
    return path_to_portable_string(path)


def _project_path_value(value: object, field_name: str) -> str:
    path = _coerce_path(value, field_name)
    if path.is_absolute():
        raise SummaryProjectionError(f"{field_name} must be project-relative")
    normalized = path_to_portable_string(path)
    _validate_relative_path(normalized, field_name)
    return normalized


def _project_relative_path(
    value: object,
    *,
    project_root: Path,
    field_name: str,
) -> str:
    path = _coerce_path(value, field_name)
    if path.is_absolute():
        try:
            path = path.relative_to(project_root)
        except ValueError as exc:
            raise SummaryProjectionError(f"{field_name} escapes the project root") from exc
    normalized = path_to_portable_string(path)
    _validate_relative_path(normalized, field_name)
    return normalized


def _run_relative_path(
    value: object,
    *,
    run_root: Path,
    field_name: str,
) -> str:
    path = _coerce_path(value, field_name)
    if path.is_absolute():
        try:
            path = path.relative_to(run_root)
        except ValueError as exc:
            raise SummaryProjectionError(f"{field_name} escapes the run directory") from exc
    normalized = path_to_portable_string(path)
    _validate_relative_path(normalized, field_name)
    return normalized


def _optional_run_path(
    value: object | None,
    *,
    run_root: Path,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _run_relative_path(
        value,
        run_root=run_root,
        field_name=field_name,
    )


def _optional_project_path(
    value: object | None,
    *,
    project_root: Path,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _project_relative_path(
        value,
        project_root=project_root,
        field_name=field_name,
    )


def _validate_relative_path(value: str, field_name: str) -> None:
    if not value or value.startswith("/"):
        raise SummaryProjectionError(f"{field_name} must be a non-empty relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SummaryProjectionError(f"{field_name} contains an unresolved path segment")
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise SummaryProjectionError(f"{field_name} must not contain a drive prefix")


def _coerce_path(value: object, field_name: str) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, PurePath):
        path = Path(value)
    elif isinstance(value, str):
        if not value:
            raise SummaryProjectionError(f"{field_name} must not be empty")
        path = Path(value.replace("\\", "/"))
    else:
        raise TypeError(f"{field_name} must be a path or string")
    if "\x00" in str(path):
        raise SummaryProjectionError(f"{field_name} must not contain NUL")
    return path


def _path_attr(value: object, name: str) -> Path:
    return _coerce_path(
        _required_attr(value, name),
        name,
    )


def _required_attr(value: object, name: str) -> object:
    if value is None or not hasattr(value, name):
        raise SummaryProjectionError(f"required projection field is missing: {name}")
    return getattr(value, name)


def _optional_attr(value: object, name: str) -> object | None:
    if value is None:
        return None
    return getattr(value, name, None)


def _first_attr(
    value: object,
    names: Sequence[str],
    *,
    required: bool = True,
) -> object | None:
    for name in names:
        try:
            return getattr(value, name)
        except AttributeError:
            continue
    if required:
        raise SummaryProjectionError("required projection field is missing: " + " or ".join(names))
    return None


def _sequence_attr(value: object, name: str) -> tuple[object, ...]:
    raw = _required_attr(value, name)
    if isinstance(raw, (str, bytes, Mapping)):
        raise TypeError(f"{name} must be a sequence")
    if not isinstance(raw, Iterable):
        raise TypeError(f"{name} must be a sequence")
    prepared = tuple(raw)
    if len(prepared) > _MAX_ITEMS:
        raise SummaryProjectionError(f"{name} exceeds the supported item limit")
    return prepared


def _iterable_attr(value: object, name: str) -> tuple[object, ...]:
    raw = _required_attr(value, name)
    if isinstance(raw, (str, bytes, Mapping)):
        raise TypeError(f"{name} must be an iterable collection")
    if not isinstance(raw, Iterable):
        raise TypeError(f"{name} must be iterable")
    prepared = tuple(raw)
    if len(prepared) > _MAX_ITEMS:
        raise SummaryProjectionError(f"{name} exceeds the supported item limit")
    return prepared


def _boolean(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be bool")
    return value


def _optional_boolean(
    value: object | None,
    field_name: str,
) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field_name)


def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int")
    if value < 0:
        raise SummaryProjectionError(f"{field_name} must be non-negative")
    return value


def _positive_int(value: object, field_name: str) -> int:
    result = _non_negative_int(value, field_name)
    if result == 0:
        raise SummaryProjectionError(f"{field_name} must be positive")
    return result


def _optional_int(
    value: object | None,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int or None")
    return value


def _non_empty_text(value: object, field_name: str) -> str:
    return _text(value, field_name, allow_empty=False)


def _text(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if "\x00" in value:
        raise SummaryProjectionError(f"{field_name} must not contain NUL")
    if not allow_empty and not value.strip():
        raise SummaryProjectionError(f"{field_name} must not be empty")
    return value


__all__ = (
    "SUMMARY_PRODUCER_NAME",
    "SUMMARY_SCHEMA_ID",
    "SUMMARY_SCHEMA_VERSION",
    "SummaryDocument",
    "SummaryProjectionError",
    "build_summary_document",
    "project_artifacts",
    "project_compile_summary",
    "project_diff_entry",
    "project_file_result",
    "project_fingerprint",
    "project_metadata",
    "project_producer",
    "project_scan_counts",
    "project_scenario_result",
    "project_scenario_section",
    "project_top_error",
    "project_totals",
    "validate_projection_invariants",
)
