"""Deterministic human-readable Markdown summary reporting.

The builder projects an already-finalized run result.  It does not execute
validation work, parse raw logs, recompute causal classification, or mutate
its input models.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import quote

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.version import __version__

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import RunResult

__all__ = (
    "SUMMARY_MARKDOWN_FILENAME",
    "SUMMARY_MARKDOWN_SOFT_SCHEMA_VERSION",
    "build_summary_md",
    "write_summary_md",
)

SUMMARY_MARKDOWN_FILENAME: Final[str] = "summary.md"
SUMMARY_MARKDOWN_SOFT_SCHEMA_VERSION: Final[str] = "1.0"
MAX_PRIMARY_MESSAGE_CHARS: Final[int] = 320
MAX_WARNING_CHARS: Final[int] = 500
MAX_MAIN_BLOCKERS: Final[int] = 10
MAX_TOP_ERRORS: Final[int] = 20
MAX_SUCCESSFUL_FILES: Final[int] = 100
MAX_REGRESSION_ENTRIES_PER_GROUP: Final[int] = 100

_ANSI_RE: Final[re.Pattern[str]] = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))"
)
_CONTROL_RE: Final[re.Pattern[str]] = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)
_BACKTICK_RUN_RE: Final[re.Pattern[str]] = re.compile(r"`+")

_STATUS_OK: Final[str] = "OK"
_STATUS_FAIL: Final[str] = "FAIL"
_STATUS_ERROR: Final[str] = "ERROR"
_STATUS_SKIPPED: Final[str] = "SKIPPED"

_CLASS_OK: Final[str] = "ok"
_CLASS_DIRECT: Final[str] = "direct"
_CLASS_DOWNSTREAM: Final[str] = "downstream"
_CLASS_AMBIGUOUS: Final[str] = "ambiguous"
_CLASS_NOISE: Final[str] = "noise"
_CLASS_SKIPPED: Final[str] = "skipped"

_CHANGE_ORDER: Final[tuple[str, ...]] = (
    "regressed",
    "new",
    "improved",
    "removed",
    "unchanged",
)

_ARTIFACT_PATH_FIELDS: Final[tuple[tuple[str, tuple[str, ...], bool], ...]] = (
    ("Machine summary", ("summary_json", "summary_json_path"), False),
    ("Human summary", ("summary_md", "summary_md_path"), True),
    ("AI packet", ("ai_ready_md", "ai_ready_path", "ai_ready_md_path"), False),
    ("Manifest", ("manifest_json", "manifest_path", "manifest_json_path"), False),
    ("Top errors", ("top_errors_txt", "top_errors_path"), False),
    ("Master log", ("master_log", "master_log_path"), False),
    ("Aggregate scan log", ("all_scan_logs", "all_scan_logs_path"), False),
    ("Aggregate execution log", ("all_logs", "all_logs_path"), False),
    ("Details", ("details_dir",), False),
    ("Raw evidence", ("raw_dir",), False),
    ("Compile logs", ("raw_compile_dir", "compile_logs_dir"), False),
    ("Scan logs", ("raw_scan_dir", "scan_logs_dir"), False),
    ("Scenario logs", ("raw_scenarios_dir", "scenario_logs_dir"), False),
    ("GFO artifacts", ("gfo_dir",), False),
    ("Output artifacts", ("out_dir",), False),
    ("PGF artifacts", ("pgf_dir",), False),
)

_SCAN_FIELD_LABELS: Final[tuple[tuple[str, str], ...]] = (
    ("single_slash_eq", "single_slash_eq"),
    ("double_slash_dash", "double_slash_dash"),
    ("runtime_str_match", "runtime_str_match"),
    ("untyped_case_str_pat", "untyped_case_str_pat"),
    ("untyped_table_str_pat", "untyped_table_str_pat"),
    ("trailing_spaces", "trailing_spaces"),
)


class SummaryMarkdownModelError(ValueError):
    """Raised when a run result would produce misleading Markdown."""


def build_summary_md(run_result: "RunResult") -> str:
    """Build canonical ``summary.md`` content from a structured run result."""

    _validate_summary_report_input(run_result)

    sections: list[str] = [
        "# GF Wordbench Audit Summary",
        _build_run_summary(run_result),
        _build_outcome(run_result),
    ]

    gate_section = _build_release_gates(run_result)
    if gate_section is not None:
        sections.append(gate_section)

    sections.extend(
        (
            _build_file_results(run_result),
            _build_scenario_results(run_result),
        )
    )

    top_errors = _sequence(_get(run_result, "top_errors", default=()))
    if top_errors:
        sections.append(_build_top_errors(top_errors))

    scan_section = _build_static_scan_notes(run_result)
    if scan_section is not None:
        sections.append(scan_section)

    sections.extend(
        (
            _build_regression_comparison(run_result),
            _build_artifacts(run_result),
        )
    )

    warnings = _collect_warnings(run_result)
    if warnings:
        sections.append(_build_warnings(warnings))

    report_generation = _build_report_generation(run_result)
    if report_generation is not None:
        sections.append(report_generation)

    normalized = "\n\n".join(section.strip() for section in sections if section.strip())
    return normalized.rstrip("\n") + "\n"


def write_summary_md(run_result: "RunResult") -> Path:
    """Atomically write the run-owned Markdown summary and return its path."""

    run_paths = _required_attr(run_result, "run_paths")
    run_dir = _as_path(_required_attr(run_paths, "run_dir"), "run_paths.run_dir")
    destination_value = _first_present(
        run_paths,
        ("summary_md", "summary_md_path"),
    )
    if destination_value is None:
        raise SummaryMarkdownModelError(
            "run_paths must define summary_md or summary_md_path"
        )
    destination = _as_path(destination_value, "run_paths.summary_md")

    return atomic_write_text(
        destination,
        build_summary_md(run_result),
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=run_dir,
        role="summary Markdown report",
    )


def _validate_summary_report_input(run_result: Any) -> None:
    if run_result is None:
        raise TypeError("run_result must not be None")

    duration_ms = _integer(_required_attr(run_result, "duration_ms"), "duration_ms")
    if duration_ms < 0:
        raise SummaryMarkdownModelError("duration_ms must be non-negative")

    started_at = _required_attr(run_result, "started_at")
    finished_at = _required_attr(run_result, "finished_at")
    if not isinstance(started_at, datetime) or not isinstance(finished_at, datetime):
        raise SummaryMarkdownModelError("run timestamps must be datetime values")
    if started_at.tzinfo is None or started_at.utcoffset() is None:
        raise SummaryMarkdownModelError("started_at must be timezone-aware")
    if finished_at.tzinfo is None or finished_at.utcoffset() is None:
        raise SummaryMarkdownModelError("finished_at must be timezone-aware")
    if finished_at < started_at:
        raise SummaryMarkdownModelError("finished_at must not precede started_at")

    overall_status = _enum_text(_required_attr(run_result, "overall_status"))
    if overall_status not in {_STATUS_OK, _STATUS_FAIL, _STATUS_ERROR}:
        raise SummaryMarkdownModelError(
            f"unsupported overall status: {overall_status!r}"
        )

    totals = _required_attr(run_result, "totals")
    totals_status = _enum_text(_required_attr(totals, "overall_status"))
    if totals_status != overall_status:
        raise SummaryMarkdownModelError(
            "overall_status must equal totals.overall_status"
        )

    file_results = _sequence(_required_attr(run_result, "file_results"))
    scenario_results = _sequence(_required_attr(run_result, "scenario_results"))

    for result in file_results:
        _validate_subject_classification(result, subject_kind="file")
    for result in scenario_results:
        _validate_subject_classification(result, subject_kind="scenario")

    _validate_count_equations(totals)
    _validate_required_release_gates(run_result, overall_status)


def _validate_subject_classification(result: Any, *, subject_kind: str) -> None:
    status = _enum_text(_required_attr(result, "status"))
    diagnostic_class = _enum_text(_required_attr(result, "diagnostic_class")).lower()
    blockers = _unique_texts(_sequence(_get(result, "blocked_by", default=())))

    allowed: dict[str, set[str]] = {
        _STATUS_OK: {_CLASS_OK},
        _STATUS_FAIL: {_CLASS_DIRECT, _CLASS_DOWNSTREAM, _CLASS_AMBIGUOUS},
        _STATUS_ERROR: {_CLASS_DIRECT, _CLASS_DOWNSTREAM, _CLASS_AMBIGUOUS},
        _STATUS_SKIPPED: {_CLASS_SKIPPED, _CLASS_NOISE},
    }
    if status not in allowed:
        raise SummaryMarkdownModelError(
            f"unsupported {subject_kind} status: {status!r}"
        )
    if diagnostic_class not in allowed[status]:
        raise SummaryMarkdownModelError(
            f"invalid {subject_kind} status/class combination: "
            f"{status}/{diagnostic_class}"
        )

    if diagnostic_class == _CLASS_DOWNSTREAM and not blockers:
        raise SummaryMarkdownModelError(
            f"downstream {subject_kind} result must identify blocked_by"
        )
    if diagnostic_class != _CLASS_DOWNSTREAM and blockers:
        raise SummaryMarkdownModelError(
            f"{diagnostic_class} {subject_kind} result must have empty blocked_by"
        )

    if hasattr(result, "is_direct"):
        is_direct = _required_attr(result, "is_direct")
        if not isinstance(is_direct, bool):
            raise SummaryMarkdownModelError("is_direct must be a bool")
        if is_direct != (diagnostic_class == _CLASS_DIRECT):
            raise SummaryMarkdownModelError(
                "is_direct must be derived from diagnostic_class"
            )


def _validate_count_equations(totals: Any) -> None:
    files_included = _non_negative_count(totals, "files_included")
    file_sum = sum(
        _non_negative_count(totals, field)
        for field in ("files_ok", "files_fail", "files_error", "files_skipped")
    )
    if files_included != file_sum:
        raise SummaryMarkdownModelError(
            "files_included must equal files_ok + files_fail + "
            "files_error + files_skipped"
        )

    scenarios_seen = _non_negative_count(totals, "scenarios_seen")
    scenario_sum = sum(
        _non_negative_count(totals, field)
        for field in (
            "scenarios_ok",
            "scenarios_fail",
            "scenarios_error",
            "scenarios_skipped",
        )
    )
    if scenarios_seen != scenario_sum:
        raise SummaryMarkdownModelError(
            "scenarios_seen must equal scenarios_ok + scenarios_fail + "
            "scenarios_error + scenarios_skipped"
        )

    for field in (
        "files_seen",
        "files_excluded",
        "direct_fail",
        "downstream_fail",
        "ambiguous_fail",
        "excluded_noise",
        "required_scenario_fail",
    ):
        if hasattr(totals, field):
            _non_negative_count(totals, field)


def _validate_required_release_gates(run_result: Any, overall_status: str) -> None:
    if overall_status != _STATUS_OK:
        return
    for gate in _release_gate_results(run_result):
        if not _bool(_get(gate, "required", default=False)):
            continue
        status = _enum_text(_get(gate, "status", default=""))
        if status != _STATUS_OK:
            raise SummaryMarkdownModelError(
                "overall status cannot be OK while a required release gate "
                f"is {status or 'unknown'}"
            )


def _build_run_summary(run_result: Any) -> str:
    config = _required_attr(run_result, "run_config")
    paths = _required_attr(run_result, "run_paths")
    project = _required_attr(config, "project")
    identity = _get(project, "identity", default=project)
    environment = _get(config, "environment", default=None)

    project_id = _text(_get(identity, "id", "project_id", default="Unknown"))
    project_name = _text(_get(identity, "name", "project_name", default="Unknown"))
    language_code = _text(
        _get(identity, "language_code", "language", default="Unknown")
    )
    mode = _enum_text(_required_attr(config, "mode")).lower()

    rows: list[tuple[str, str]] = [
        ("Run ID", _inline_code(_text(_required_attr(paths, "run_id")))),
        ("GF Wordbench", _inline_code(__version__)),
        ("Project", f"{_inline_code(project_id)} — {_plain_cell(project_name)}"),
        ("Language code", _inline_code(language_code)),
        ("Mode", _inline_code(mode)),
    ]

    target_label, target_value = _render_target(config, mode)
    if target_label is not None:
        rows.append((target_label, target_value))

    rows.extend(
        (
            ("Started", _inline_code(_format_timestamp(_required_attr(run_result, "started_at")))),
            ("Finished", _inline_code(_format_timestamp(_required_attr(run_result, "finished_at")))),
            ("Duration", _format_duration(_required_attr(run_result, "duration_ms"))),
            ("GF version", _inline_code(_optional_text(_get(run_result, "gf_version", default=None)))),
            (
                "Run directory",
                _inline_code(_display_path(_required_attr(paths, "run_dir"))),
            ),
        )
    )

    strict_mode = _get(config, "strict", "strict_mode", default=None)
    if strict_mode is not None:
        rows.append(("Strict mode", _yes_no(_bool(strict_mode))))

    if environment is not None:
        for label, aliases in (
            ("GF executable", ("gf_executable",)),
            ("RGL root", ("rgl_root",)),
            ("Output root", ("output_root",)),
        ):
            value = _first_present(environment, aliases)
            if value is not None:
                rows.append((label, _inline_code(_display_path(value))))

    schema_version = _get(project, "schema_version", default=None)
    if schema_version:
        rows.append(("Project schema", _inline_code(_text(schema_version))))
    rows.append(
        (
            "Summary soft schema",
            _inline_code(SUMMARY_MARKDOWN_SOFT_SCHEMA_VERSION),
        )
    )

    return "## Run Summary\n\n" + _table(("Field", "Value"), rows)


def _render_target(config: Any, mode: str) -> tuple[str | None, str]:
    target = _get(config, "target", default=None)
    if target is not None:
        value = _get(target, "path", "value", "subject_id", default=target)
        kind = _enum_text(_get(target, "kind", default="")).lower()
        label = "Checkpoint" if "checkpoint" in kind else "Target"
        return label, _inline_code(_display_path(value))

    if mode == "checkpoint":
        checkpoints = _sequence(_get(config, "selected_checkpoints", default=()))
        if checkpoints:
            return "Checkpoint", ", ".join(
                _inline_code(_display_path(item)) for item in checkpoints
            )
        return "Checkpoint", "—"
    if mode == "quick":
        return "Target", "—"
    return None, "—"


def _build_outcome(run_result: Any) -> str:
    status = _enum_text(_required_attr(run_result, "overall_status"))
    totals = _required_attr(run_result, "totals")

    explanations = {
        _STATUS_OK: "All required validation checks passed.",
        _STATUS_FAIL: (
            "Required validation completed, but one or more checks failed."
        ),
        _STATUS_ERROR: (
            "The run could not complete reliably because a required execution "
            "stage errored."
        ),
    }

    lines = [
        "## Outcome",
        "",
        f"**Overall status: {_inline_code(status)}**",
        "",
        explanations[status],
        "",
    ]

    count_rows = [
        ("Files included", str(_count_alias(totals, "files_included"))),
        ("Files OK", str(_count_alias(totals, "files_ok"))),
        ("Files failed", str(_count_alias(totals, "files_fail"))),
        ("Files errored", str(_count_alias(totals, "files_error"))),
        ("Files skipped", str(_count_alias(totals, "files_skipped"))),
        (
            "Direct failures",
            str(_count_alias(totals, "direct_fail", "direct_count")),
        ),
        (
            "Downstream failures",
            str(_count_alias(totals, "downstream_fail", "downstream_count")),
        ),
        (
            "Ambiguous failures",
            str(_count_alias(totals, "ambiguous_fail", "ambiguous_count")),
        ),
        ("Scenarios seen", str(_count_alias(totals, "scenarios_seen"))),
        ("Scenarios OK", str(_count_alias(totals, "scenarios_ok"))),
        ("Scenarios failed", str(_count_alias(totals, "scenarios_fail"))),
        ("Scenarios errored", str(_count_alias(totals, "scenarios_error"))),
        ("Scenarios skipped", str(_count_alias(totals, "scenarios_skipped"))),
    ]
    lines.append(_table(("Measure", "Count"), count_rows, right_align=(1,)))

    blockers = _main_blockers(run_result)
    if blockers:
        lines.extend(("", "### Main Blockers", ""))
        lines.extend(f"- {item}" for item in blockers[:MAX_MAIN_BLOCKERS])
        if len(blockers) > MAX_MAIN_BLOCKERS:
            lines.append(
                f"- Showing {MAX_MAIN_BLOCKERS} of {len(blockers)} blockers."
            )

    return "\n".join(lines)


def _main_blockers(run_result: Any) -> list[str]:
    items: list[str] = []
    for result in _sorted_file_results(run_result):
        status = _enum_text(_get(result, "status", default=""))
        diagnostic_class = _enum_text(
            _get(result, "diagnostic_class", default="")
        ).lower()
        if status not in {_STATUS_FAIL, _STATUS_ERROR}:
            continue
        if diagnostic_class not in {_CLASS_DIRECT, _CLASS_AMBIGUOUS}:
            continue
        path = _project_relative_file_path(run_result, result)
        kind = _enum_text(_get(result, "error_kind", default="OTHER"))
        message = _primary_message(result)
        items.append(
            f"{_inline_code(path)} — {_inline_code(kind)}: "
            f"{_inline_code(message)}"
        )

    for result in _sequence(_get(run_result, "scenario_results", default=())):
        status = _enum_text(_get(result, "status", default=""))
        required = _bool(_get(result, "required", default=False))
        diagnostic_class = _enum_text(
            _get(result, "diagnostic_class", default="")
        ).lower()
        if not required or status not in {_STATUS_FAIL, _STATUS_ERROR}:
            continue
        if diagnostic_class not in {_CLASS_DIRECT, _CLASS_AMBIGUOUS}:
            continue
        scenario_id = _text(_get(result, "scenario_id", default="Unknown"))
        items.append(
            f"{_inline_code(scenario_id)} — "
            f"{_inline_code(_primary_message(result))}"
        )
    return items


def _build_release_gates(run_result: Any) -> str | None:
    gates = _release_gate_results(run_result)
    mode = _enum_text(
        _get(_get(run_result, "run_config", default=None), "mode", default="")
    ).lower()
    if not gates and mode != "release":
        return None

    lines = ["## Release Gates", ""]
    if not gates:
        lines.append("None.")
        return "\n".join(lines)

    rows: list[tuple[str, str, str, str]] = []
    for gate in gates:
        gate_id = _text(
            _get(gate, "gate_id", "id", "name", default="Unknown")
        )
        required = _yes_no(_bool(_get(gate, "required", default=False)))
        status = _enum_text(_get(gate, "status", default="Unknown"))
        evidence = _gate_evidence(gate)
        rows.append(
            (
                _inline_code(gate_id),
                required,
                _inline_code(status),
                evidence,
            )
        )
    lines.append(
        _table(("Gate", "Required", "Status", "Evidence"), rows, center=(1,))
    )
    return "\n".join(lines)


def _gate_evidence(gate: Any) -> str:
    for name in ("evidence", "message", "criterion", "detail"):
        value = _get(gate, name, default=None)
        if value:
            if isinstance(value, (list, tuple)):
                return "; ".join(_plain_cell(item) for item in value)
            return _plain_cell(value)
    blockers = _unique_texts(_sequence(_get(gate, "blocked_by", default=())))
    if blockers:
        return ", ".join(_inline_code(item) for item in blockers)
    return "—"


def _build_file_results(run_result: Any) -> str:
    results = _sorted_file_results(run_result)
    lines = ["## File Results", ""]
    if not results:
        lines.append("None.")
        return "\n".join(lines)

    groups: dict[str, list[Any]] = {
        _CLASS_DIRECT: [],
        _CLASS_AMBIGUOUS: [],
        _CLASS_DOWNSTREAM: [],
        _CLASS_SKIPPED: [],
        _CLASS_OK: [],
        _CLASS_NOISE: [],
    }
    for result in results:
        diagnostic_class = _enum_text(
            _get(result, "diagnostic_class", default="")
        ).lower()
        groups.setdefault(diagnostic_class, []).append(result)

    if groups[_CLASS_DIRECT]:
        lines.extend(("### Direct Failures", ""))
        lines.extend(_render_file_failure(run_result, item) for item in groups[_CLASS_DIRECT])

    if groups[_CLASS_AMBIGUOUS]:
        lines.extend(("### Ambiguous Failures", ""))
        lines.extend(
            _render_file_failure(run_result, item, ambiguous=True)
            for item in groups[_CLASS_AMBIGUOUS]
        )

    if groups[_CLASS_DOWNSTREAM]:
        lines.extend(("### Downstream Failures", ""))
        lines.extend(
            _render_downstream_file(run_result, item)
            for item in groups[_CLASS_DOWNSTREAM]
        )

    if groups[_CLASS_SKIPPED]:
        lines.extend(("### Skipped Files", ""))
        for item in groups[_CLASS_SKIPPED]:
            path = _project_relative_file_path(run_result, item)
            reason = _primary_message(item)
            lines.append(f"- {_inline_code(path)} — {_plain_cell(reason)}")
        lines.append("")

    if groups[_CLASS_OK]:
        lines.extend(("### Successful Files", ""))
        successful = groups[_CLASS_OK]
        displayed = successful[:MAX_SUCCESSFUL_FILES]
        rows: list[tuple[str, str, str, str]] = []
        for item in displayed:
            compile_summary = _get(item, "compile_summary", default=None)
            rows.append(
                (
                    _inline_code(_project_relative_file_path(run_result, item)),
                    _inline_code(_text(_get(item, "module_name", default="Unknown"))),
                    _format_duration(_get(compile_summary, "duration_ms", default=0)),
                    str(_scan_total(_get(item, "scan_counts", default=None))),
                )
            )
        lines.append(
            _table(
                ("File", "Module", "Duration", "Scan hits"),
                rows,
                right_align=(2, 3),
            )
        )
        if len(successful) > len(displayed):
            lines.extend(
                (
                    "",
                    f"Showing {len(displayed)} of {len(successful)} successful files.",
                    "",
                    "[See complete structured results](summary.json).",
                )
            )
        lines.append("")

    if groups[_CLASS_NOISE]:
        lines.extend(("### Excluded or Noise Files", ""))
        for item in groups[_CLASS_NOISE]:
            path = _project_relative_file_path(run_result, item)
            reason = _primary_message(item)
            lines.append(f"- {_inline_code(path)} — {_plain_cell(reason)}")
        lines.append("")

    if len(lines) == 2:
        lines.append("None.")
    return "\n".join(lines).rstrip()


def _render_file_failure(
    run_result: Any,
    result: Any,
    *,
    ambiguous: bool = False,
) -> str:
    path = _project_relative_file_path(run_result, result)
    compile_summary = _get(result, "compile_summary", default=None)
    lines = [
        f"#### {_inline_code(path)}",
        "",
        f"- Module: {_inline_code(_text(_get(result, 'module_name', default='Unknown')))}",
        f"- Status: {_inline_code(_enum_text(_get(result, 'status', default='Unknown')))}",
        f"- Error kind: {_inline_code(_enum_text(_get(result, 'error_kind', default='OTHER')))}",
        f"- First error: {_inline_code(_primary_message(result))}",
        f"- Duration: {_format_duration(_get(compile_summary, 'duration_ms', default=0))}",
        f"- Timed out: {_yes_no(_bool(_get(compile_summary, 'timed_out', default=False)))}",
    ]
    if ambiguous:
        detail = _text(_get(compile_summary, "error_detail", default=""))
        reason = _first_line(detail) if detail else (
            "The available evidence does not reliably distinguish a local "
            "failure from a dependency failure."
        )
        lines.append(f"- Ambiguity: {_plain_cell(reason)}")
    lines.extend(_render_evidence_list(_file_evidence_paths(result), run_result))
    lines.append("")
    return "\n".join(lines)


def _render_downstream_file(run_result: Any, result: Any) -> str:
    path = _project_relative_file_path(run_result, result)
    blockers = _unique_texts(_sequence(_get(result, "blocked_by", default=())))
    lines = [
        f"#### {_inline_code(path)}",
        "",
        f"- Status: {_inline_code(_enum_text(_get(result, 'status', default='Unknown')))}",
        "- Blocked by:",
    ]
    lines.extend(f"  - {_inline_code(item)}" for item in blockers)
    lines.append(f"- First error: {_inline_code(_primary_message(result))}")
    lines.extend(_render_evidence_list(_file_evidence_paths(result), run_result))
    lines.append("")
    return "\n".join(lines)


def _file_evidence_paths(result: Any) -> list[tuple[str, Any]]:
    compile_summary = _get(result, "compile_summary", default=None)
    paths: list[tuple[str, Any]] = []
    for label, name in (
        ("stdout", "stdout_path"),
        ("stderr", "stderr_path"),
    ):
        value = _get(compile_summary, name, default=None)
        if value is not None:
            paths.append((label, value))
    scan_log = _get(result, "scan_log_path", default=None)
    if scan_log is not None:
        paths.append(("scan", scan_log))
    for artifact in _sequence(_get(result, "artifacts", default=())):
        role = _text(_get(artifact, "role", default="artifact"))
        value = _get(artifact, "path", default=None)
        if value is not None:
            paths.append((_artifact_label(role), value))
    return _deduplicate_paths(paths)


def _build_scenario_results(run_result: Any) -> str:
    scenarios = _sequence(_get(run_result, "scenario_results", default=()))
    lines = ["## Scenario Results", ""]
    if not scenarios:
        lines.append("None.")
        return "\n".join(lines)

    rows: list[tuple[str, str, str, str, str, str]] = []
    for result in scenarios:
        execution_state = _get(result, "execution_state", default=None)
        rows.append(
            (
                _inline_code(_text(_get(result, "scenario_id", default="Unknown"))),
                _yes_no(_bool(_get(result, "required", default=False))),
                _inline_code(_enum_text(_get(result, "status", default="Unknown"))),
                (
                    _inline_code(_enum_text(execution_state))
                    if execution_state is not None
                    else "—"
                ),
                _gold_label(result),
                _format_duration(_get(result, "duration_ms", default=0)),
            )
        )
    lines.append(
        _table(
            ("Scenario", "Required", "Status", "Execution", "Gold", "Duration"),
            rows,
            center=(1,),
            right_align=(5,),
        )
    )

    failed = [
        result
        for result in scenarios
        if _enum_text(_get(result, "status", default=""))
        in {_STATUS_FAIL, _STATUS_ERROR}
    ]
    if failed:
        lines.extend(("", "### Failed Scenarios", ""))
        for result in failed:
            lines.append(_render_failed_scenario(run_result, result))

    return "\n".join(lines).rstrip()


def _render_failed_scenario(run_result: Any, result: Any) -> str:
    scenario_id = _text(_get(result, "scenario_id", default="Unknown"))
    lines = [
        f"#### {_inline_code(scenario_id)}",
        "",
        f"- Required: {_yes_no(_bool(_get(result, 'required', default=False)))}",
        f"- Status: {_inline_code(_enum_text(_get(result, 'status', default='Unknown')))}",
        f"- Diagnostic class: {_inline_code(_enum_text(_get(result, 'diagnostic_class', default='Unknown')))}",
        f"- Error kind: {_inline_code(_enum_text(_get(result, 'error_kind', default='OTHER')))}",
        f"- Message: {_plain_cell(_primary_message(result))}",
        f"- Gold: {_gold_label(result)}",
        f"- Script: {_inline_code(_project_relative_path(run_result, _get(result, 'script_path', default='Unknown')))}",
    ]

    blockers = _unique_texts(_sequence(_get(result, "blocked_by", default=())))
    if blockers:
        lines.append("- Blocked by:")
        lines.extend(f"  - {_inline_code(item)}" for item in blockers)

    incomplete_sections = [
        section
        for section in _sequence(_get(result, "sections", default=()))
        if not _bool(_get(section, "completed", default=False))
    ]
    if incomplete_sections:
        lines.append("- Incomplete sections:")
        for section in incomplete_sections:
            section_id = _text(_get(section, "id", "section_id", default="Unknown"))
            message = _text(_get(section, "message", default="required marker incomplete"))
            lines.append(f"  - {_inline_code(section_id)} — {_plain_cell(message)}")

    failed_assertions = [
        assertion
        for assertion in _sequence(_get(result, "assertions", default=()))
        if _enum_text(_get(assertion, "status", default="")).lower()
        in {"failed", "error"}
    ]
    if failed_assertions:
        lines.append("- Failed assertions:")
        for assertion in failed_assertions:
            assertion_id = _text(
                _get(assertion, "assertion_id", "id", default="Unknown")
            )
            message = _text(_get(assertion, "message", default="assertion failed"))
            lines.append(f"  - {_inline_code(assertion_id)} — {_plain_cell(message)}")

    for label, name, path_class in (
        ("Normalized output", "normalized_output_path", "run"),
        ("Gold file", "gold_path", "project"),
        ("Gold diff", "gold_diff_path", "run"),
    ):
        value = _get(result, name, default=None)
        if value is not None:
            if path_class == "run":
                rendered = _run_relative_path(run_result, value)
            else:
                rendered = _project_relative_path(run_result, value)
            lines.append(f"- {label}: {_inline_code(rendered)}")

    lines.extend(_render_evidence_list(_scenario_evidence_paths(result), run_result))

    if (
        not _bool(_get(result, "required", default=False))
        and _enum_text(_get(result, "status", default=""))
        in {_STATUS_FAIL, _STATUS_ERROR}
    ):
        lines.append(
            "- Optional diagnostic failure; does not affect overall required "
            "validation unless project policy says otherwise."
        )
    lines.append("")
    return "\n".join(lines)


def _scenario_evidence_paths(result: Any) -> list[tuple[str, Any]]:
    paths: list[tuple[str, Any]] = []
    for label, name in (
        ("stdout", "stdout_path"),
        ("stderr", "stderr_path"),
        ("normalized", "normalized_output_path"),
        ("gold diff", "gold_diff_path"),
    ):
        value = _get(result, name, default=None)
        if value is not None:
            paths.append((label, value))
    for artifact in _sequence(_get(result, "artifacts", default=())):
        role = _text(_get(artifact, "role", default="artifact"))
        value = _get(artifact, "path", default=None)
        if value is not None:
            paths.append((_artifact_label(role), value))
    return _deduplicate_paths(paths)


def _gold_label(result: Any) -> str:
    gold_path = _get(result, "gold_path", default=None)
    gold_match = _get(result, "gold_match", default=None)
    if gold_path is None and gold_match is None:
        return "—"
    if gold_path is None:
        return "Missing"
    if gold_match is True:
        return "Match"
    if gold_match is False:
        return "Mismatch"
    return "Not compared"


def _build_top_errors(top_errors: Sequence[Any]) -> str:
    ordered = sorted(
        top_errors,
        key=lambda item: (
            -_integer(_get(item, "count", default=0), "top error count"),
            _text(_get(item, "message", default="")).casefold(),
            _enum_text(_get(item, "error_kind", default="OTHER")),
        ),
    )
    displayed = ordered[:MAX_TOP_ERRORS]
    rows = [
        (
            str(_integer(_get(item, "count", default=0), "top error count")),
            _inline_code(_enum_text(_get(item, "error_kind", default="OTHER"))),
            _inline_code(_text(_get(item, "message", default="Unknown"))),
        )
        for item in displayed
        if _text(_get(item, "message", default="")).strip()
    ]
    lines = ["## Top Errors", ""]
    if not rows:
        lines.append("None.")
    else:
        lines.append(_table(("Count", "Kind", "Message"), rows, right_align=(0,)))
        if len(ordered) > len(displayed):
            lines.extend(
                (
                    "",
                    f"Showing {len(displayed)} of {len(ordered)} grouped errors.",
                )
            )
    return "\n".join(lines)


def _build_static_scan_notes(run_result: Any) -> str | None:
    rows: list[tuple[str, str, str, str]] = []
    for result in _sorted_file_results(run_result):
        scan_counts = _get(result, "scan_counts", default=None)
        if scan_counts is None:
            continue
        for field, label in _SCAN_FIELD_LABELS:
            count = _integer(_get(scan_counts, field, default=0), field)
            if count <= 0:
                continue
            rows.append(
                (
                    _inline_code(_project_relative_file_path(run_result, result)),
                    _inline_code(_enum_text(_get(result, "status", default="Unknown"))),
                    _inline_code(label),
                    str(count),
                )
            )
    if not rows:
        return None
    return "\n".join(
        (
            "## Static Scan Notes",
            "",
            "Heuristic scan findings are shown separately from GF validation outcomes.",
            "",
            _table(
                ("File", "File status", "Finding", "Count"),
                rows,
                right_align=(3,),
            ),
        )
    )


def _build_regression_comparison(run_result: Any) -> str:
    config = _get(run_result, "run_config", default=None)
    enabled = _bool(_get(config, "diff_previous", default=True))
    entries = _sequence(_get(run_result, "diff_entries", default=()))
    baseline_id = _comparison_value(
        run_result,
        "baseline_run_id",
        "previous_run_id",
        "baseline_id",
    )

    lines = ["## Regression Comparison", ""]
    if not enabled:
        lines.append("Comparison was disabled for this run.")
        return "\n".join(lines)
    if not entries and baseline_id is None:
        lines.append("No compatible baseline was available.")
        return "\n".join(lines)

    if baseline_id is not None:
        lines.extend((f"Baseline: {_inline_code(_text(baseline_id))}", ""))

    grouped: dict[str, list[Any]] = {kind: [] for kind in _CHANGE_ORDER}
    for entry in entries:
        kind = _enum_text(_get(entry, "change_kind", default="unchanged")).lower()
        grouped.setdefault(kind, []).append(entry)

    count_rows = [
        ("Regressed", str(len(grouped.get("regressed", ())))),
        ("New", str(len(grouped.get("new", ())))),
        ("Improved", str(len(grouped.get("improved", ())))),
        ("Removed", str(len(grouped.get("removed", ())))),
        ("Unchanged", str(len(grouped.get("unchanged", ())))),
    ]
    lines.append(_table(("Change", "Count"), count_rows, right_align=(1,)))

    headings = {
        "regressed": "Regressions",
        "new": "New Subjects",
        "improved": "Improvements",
        "removed": "Removed Subjects",
        "unchanged": "Unchanged Details",
    }
    for kind in _CHANGE_ORDER:
        group = grouped.get(kind, [])
        if not group:
            continue
        if kind == "unchanged":
            group = [
                item
                for item in group
                if _text(_get(item, "message", default="")).strip()
            ]
            if not group:
                continue
        lines.extend(("", f"### {headings[kind]}", ""))
        for entry in group[:MAX_REGRESSION_ENTRIES_PER_GROUP]:
            lines.append(_render_diff_entry(entry, kind))
        if len(group) > MAX_REGRESSION_ENTRIES_PER_GROUP:
            lines.append(
                f"- Showing {MAX_REGRESSION_ENTRIES_PER_GROUP} of "
                f"{len(group)} {kind} entries."
            )

    comparison_warnings = _comparison_warnings(run_result)
    if comparison_warnings:
        lines.extend(("", "### Comparison Warnings", ""))
        lines.extend(f"- {_plain_cell(item)}" for item in comparison_warnings)

    return "\n".join(lines)


def _render_diff_entry(entry: Any, kind: str) -> str:
    subject_kind = _text(_get(entry, "subject_kind", default="file"))
    subject_id = _text(
        _get(entry, "subject_id", "file_path", default="Unknown")
    )
    previous = _enum_text(_get(entry, "previous_status", default="—")) or "—"
    current = _enum_text(_get(entry, "current_status", default="—")) or "—"
    message = _text(_get(entry, "message", default="")).strip()
    rendered = (
        f"- {_inline_code(subject_kind)} {_inline_code(subject_id)}: "
        f"{_inline_code(previous)} → {_inline_code(current)} — **{_plain_cell(kind)}**"
    )
    if message:
        rendered += f"\n  - {_plain_cell(message)}"
    return rendered


def _build_artifacts(run_result: Any) -> str:
    paths = _required_attr(run_result, "run_paths")
    run_dir = _as_path(_required_attr(paths, "run_dir"), "run_paths.run_dir")
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()

    for label, aliases, self_link in _ARTIFACT_PATH_FIELDS:
        value = _first_present(paths, aliases)
        if value is None:
            continue
        path = _as_path(value, f"run_paths.{aliases[0]}")
        display = _display_path(path, root=run_dir)
        key = display.casefold()
        if key in seen:
            continue
        seen.add(key)
        if self_link:
            rendered = _inline_code(display)
        else:
            rendered = _markdown_link(display, display)
        rows.append((label, rendered))

    for artifact in _sequence(_get(run_result, "artifacts", default=())):
        value = _get(artifact, "path", default=None)
        if value is None:
            continue
        display = _display_path(value, root=run_dir)
        key = display.casefold()
        if key in seen:
            continue
        seen.add(key)
        role = _artifact_label(_text(_get(artifact, "role", default="artifact")))
        rows.append((role.title(), _markdown_link(display, display)))

    lines = ["## Artifacts", ""]
    if rows:
        lines.append(_table(("Role", "Path"), rows))
    else:
        lines.append("None.")
    return "\n".join(lines)


def _build_warnings(warnings: Sequence[str]) -> str:
    lines = ["## Warnings", ""]
    lines.extend(f"- {_plain_cell(item, limit=MAX_WARNING_CHARS)}" for item in warnings)
    return "\n".join(lines)


def _build_report_generation(run_result: Any) -> str | None:
    values = _sequence(
        _get(
            run_result,
            "report_generation_results",
            "report_results",
            default=(),
        )
    )
    if not values:
        return None
    lines = ["## Report Generation", ""]
    for value in values:
        name = _text(_get(value, "name", "artifact", "writer", default="report"))
        status = _enum_text(_get(value, "status", default="Unknown"))
        message = _text(_get(value, "message", "detail", default="")).strip()
        line = f"- {_inline_code(name)}: {_inline_code(status)}"
        if message:
            line += f" — {_plain_cell(message)}"
        lines.append(line)
    return "\n".join(lines)


def _collect_warnings(run_result: Any) -> list[str]:
    warnings: list[str] = []
    config = _get(run_result, "run_config", default=None)
    for source in (
        _get(config, "compatibility_warnings", default=()),
        _get(run_result, "compatibility_warnings", default=()),
        _get(run_result, "warnings", default=()),
    ):
        for item in _sequence(source):
            value = _warning_text(item)
            if value:
                warnings.append(value)

    for error in _sequence(_get(run_result, "errors", default=())):
        severity = _enum_text(_get(error, "severity", default="")).lower()
        if severity in {"error", "fatal"}:
            continue
        value = _warning_text(error)
        if value:
            warnings.append(value)

    return _unique_texts(warnings)


def _warning_text(value: Any) -> str:
    if isinstance(value, str):
        return _first_line(value, limit=MAX_WARNING_CHARS)
    code = _text(_get(value, "code", default="")).strip()
    message = _text(_get(value, "message", "detail", default="")).strip()
    if code and message:
        return f"{code}: {message}"
    return message or code


def _comparison_warnings(run_result: Any) -> list[str]:
    context = _get(run_result, "comparison", "comparison_context", default=None)
    values: list[Any] = []
    values.extend(_sequence(_get(context, "warnings", default=())))
    values.extend(_sequence(_get(run_result, "comparison_warnings", default=())))
    return _unique_texts(_warning_text(item) for item in values if item is not None)


def _comparison_value(run_result: Any, *names: str) -> Any:
    direct = _get(run_result, *names, default=None)
    if direct is not None:
        return direct
    context = _get(run_result, "comparison", "comparison_context", default=None)
    return _get(context, *names, default=None)


def _release_gate_results(run_result: Any) -> list[Any]:
    return list(
        _sequence(
            _get(
                run_result,
                "release_gate_results",
                "release_gates",
                default=(),
            )
        )
    )


def _sorted_file_results(run_result: Any) -> list[Any]:
    return sorted(
        _sequence(_get(run_result, "file_results", default=())),
        key=lambda item: _project_relative_file_path(run_result, item).casefold(),
    )


def _project_relative_file_path(run_result: Any, result: Any) -> str:
    return _project_relative_path(
        run_result,
        _get(result, "file_path", default="Unknown"),
    )


def _project_relative_path(run_result: Any, value: Any) -> str:
    config = _get(run_result, "run_config", default=None)
    project = _get(config, "project", default=None)
    identity = _get(project, "identity", default=project)
    root = _get(identity, "root", default=None)
    return _display_path(value, root=root)


def _run_relative_path(run_result: Any, value: Any) -> str:
    paths = _get(run_result, "run_paths", default=None)
    root = _get(paths, "run_dir", default=None)
    return _display_path(value, root=root)


def _render_evidence_list(
    paths: Sequence[tuple[str, Any]],
    run_result: Any,
) -> list[str]:
    if not paths:
        return []
    lines = ["- Evidence:"]
    for label, value in paths:
        display = _run_relative_path(run_result, value)
        lines.append(f"  - {_markdown_link(label, display)}")
    return lines


def _deduplicate_paths(paths: Iterable[tuple[str, Any]]) -> list[tuple[str, Any]]:
    output: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for label, value in paths:
        key = _display_path(value).casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append((label, value))
    return output


def _artifact_label(role: str) -> str:
    return role.replace("_", " ").strip() or "artifact"


def _primary_message(result: Any) -> str:
    value = _get(result, "primary_message", default=None)
    if value is None:
        compile_summary = _get(result, "compile_summary", default=None)
        value = _get(compile_summary, "first_error", default=None)
    if value is None or not _text(value).strip():
        status = _enum_text(_get(result, "status", default="Unknown"))
        return f"No primary diagnostic was recorded for status {status}."
    return _first_line(value, limit=MAX_PRIMARY_MESSAGE_CHARS)


def _scan_total(scan_counts: Any) -> int:
    if scan_counts is None:
        return 0
    total = 0
    for field, _ in _SCAN_FIELD_LABELS:
        total += _integer(_get(scan_counts, field, default=0), field)
    return total


def _count_alias(owner: Any, *names: str) -> int:
    for name in names:
        if hasattr(owner, name) or (isinstance(owner, Mapping) and name in owner):
            return _non_negative_count(owner, name)
    raise SummaryMarkdownModelError(
        "missing required count field: " + " or ".join(names)
    )


def _non_negative_count(owner: Any, name: str) -> int:
    value = _integer(_required_attr(owner, name), name)
    if value < 0:
        raise SummaryMarkdownModelError(f"{name} must be non-negative")
    return value


def _format_timestamp(value: Any) -> str:
    if not isinstance(value, datetime):
        return "Unknown"
    if value.tzinfo is None or value.utcoffset() is None:
        return "Unknown"
    utc = value.astimezone(timezone.utc)
    timespec = "microseconds" if utc.microsecond else "seconds"
    return utc.isoformat(timespec=timespec).replace("+00:00", "Z")


def _format_duration(value: Any) -> str:
    milliseconds = _integer(value, "duration_ms")
    if milliseconds < 0:
        raise SummaryMarkdownModelError("duration_ms must be non-negative")
    return f"{milliseconds / 1000:.3f} s"


def _display_path(value: Any, *, root: Any = None) -> str:
    if value is None:
        return "Unknown"
    try:
        path = Path(value)
    except (TypeError, ValueError):
        return _text(value).replace("\\", "/")

    if root is not None:
        try:
            root_path = Path(root)
            path = path.relative_to(root_path)
        except (TypeError, ValueError):
            try:
                path = path.resolve(strict=False).relative_to(
                    Path(root).resolve(strict=False)
                )
            except (OSError, RuntimeError, ValueError):
                pass
    rendered = path.as_posix()
    return rendered or "."


def _markdown_link(label: Any, destination: str) -> str:
    safe_label = _escape_link_label(_text(label))
    safe_destination = quote(
        _sanitize_text(destination, multiline=False),
        safe="/._~-:@",
    )
    return f"[{safe_label}]({safe_destination})"


def _escape_link_label(value: str) -> str:
    return (
        _sanitize_text(value, multiline=False)
        .replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _inline_code(value: Any) -> str:
    text = _sanitize_text(_text(value), multiline=False)
    if not text:
        text = "Unknown"
    longest = max((len(match.group(0)) for match in _BACKTICK_RUN_RE.finditer(text)), default=0)
    delimiter = "`" * (longest + 1)
    if text.startswith(("`", " ")) or text.endswith(("`", " ")):
        text = f" {text} "
    return f"{delimiter}{text}{delimiter}"


def _plain_cell(value: Any, *, limit: int = MAX_PRIMARY_MESSAGE_CHARS) -> str:
    text = _first_line(value, limit=limit)
    text = (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return text or "Unknown"


def _table(
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    center: Sequence[int] = (),
    right_align: Sequence[int] = (),
) -> str:
    header_cells = [f" {_plain_cell(value)} " for value in headers]
    separators: list[str] = []
    center_set = set(center)
    right_set = set(right_align)
    for index in range(len(headers)):
        if index in center_set:
            separators.append(":---:")
        elif index in right_set:
            separators.append("---:")
        else:
            separators.append("---")

    lines = [
        "|" + "|".join(header_cells) + "|",
        "|" + "|".join(separators) + "|",
    ]
    for row in rows:
        cells = list(row)
        if len(cells) != len(headers):
            raise SummaryMarkdownModelError("table row width does not match headers")
        lines.append(
            "|" + "|".join(f" {_table_cell(value)} " for value in cells) + "|"
        )
    return "\n".join(lines)


def _table_cell(value: Any) -> str:
    text = _sanitize_text(_text(value), multiline=False)
    return text.replace("|", "\\|") or "—"


def _sanitize_text(value: str, *, multiline: bool) -> str:
    text = _ANSI_RE.sub("", value)
    text = _CONTROL_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not multiline:
        text = " ".join(part.strip() for part in text.split("\n") if part.strip())
    return text.strip()


def _first_line(value: Any, *, limit: int = MAX_PRIMARY_MESSAGE_CHARS) -> str:
    text = _sanitize_text(_text(value), multiline=True)
    first = next((line.strip() for line in text.split("\n") if line.strip()), "")
    if len(first) <= limit:
        return first
    return first[: max(0, limit - 1)].rstrip() + "…"


def _optional_text(value: Any) -> str:
    text = _text(value).strip() if value is not None else ""
    return text or "Unknown"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _enum_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return _text(value.value)
    raw = getattr(value, "value", value)
    return _text(raw)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _unique_texts(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _sanitize_text(_text(value), multiline=False)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def _sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Sequence):
        return list(value)
    if isinstance(value, Iterable):
        return list(value)
    raise TypeError(f"expected an iterable collection, got {type(value).__name__}")


def _get(owner: Any, *names: str, default: Any = None) -> Any:
    if owner is None:
        return default
    for name in names:
        if isinstance(owner, Mapping) and name in owner:
            return owner[name]
        if hasattr(owner, name):
            return getattr(owner, name)
    return default


def _required_attr(owner: Any, name: str) -> Any:
    sentinel = object()
    value = _get(owner, name, default=sentinel)
    if value is sentinel:
        raise SummaryMarkdownModelError(f"missing required field: {name}")
    return value


def _first_present(owner: Any, names: Sequence[str]) -> Any:
    for name in names:
        value = _get(owner, name, default=None)
        if value is not None:
            return value
    return None


def _integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SummaryMarkdownModelError(f"{field_name} must be an integer")
    return value


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0", ""}:
            return False
    return bool(value)


def _as_path(value: Any, field_name: str) -> Path:
    if isinstance(value, Path):
        return value
    try:
        return Path(value)
    except (TypeError, ValueError) as exc:
        raise SummaryMarkdownModelError(f"{field_name} must be path-like") from exc
