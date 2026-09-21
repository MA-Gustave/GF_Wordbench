"""Deterministic per-file and per-scenario Markdown detail reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import csv
from dataclasses import dataclass
from enum import Enum
import hashlib
from io import StringIO
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Final
from urllib.parse import quote

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.infrastructure.json_io import JsonObject, JsonValue, write_json
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import FileResult, RunResult
    from gf_wordbench.validation.scenarios.models import ScenarioResult

_MAX_ROWS: Final = 1_000
_MAX_TEXT: Final = 32_000
_UNSAFE_KEY: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9._-]+")
_RESERVED: Final[frozenset[str]] = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


_GLOBAL_SCAN_CSV: Final[str] = "global_scan.csv"
_GLOBAL_SCAN_JSON: Final[str] = "global_scan.json"
_GLOBAL_SIGNATURE_RULES: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("GENERATE_PMCFG", re.compile(r"generate\s*pmcfg|pmcfg", re.IGNORECASE)),
    ("MISSING_LIN", re.compile(r"missing\s+linearization|no\s+linearization", re.IGNORECASE)),
    ("DUPLICATE_DEFINITION", re.compile(r"duplicate|already\s+defined", re.IGNORECASE)),
    ("LOCK_FIELD", re.compile(r"lock\s*field|lock_", re.IGNORECASE)),
    ("MODULE_NOT_FOUND", re.compile(r"module.+not\s+found|unknown\s+module", re.IGNORECASE)),
    (
        "UNKNOWN_SYMBOL",
        re.compile(r"unknown\s+(?:identifier|symbol|constant|function)", re.IGNORECASE),
    ),
    (
        "TYPE_MISMATCH",
        re.compile(r"type\s+mismatch|cannot\s+unify|expected.+found", re.IGNORECASE),
    ),
)


@dataclass(frozen=True, slots=True)
class DetailWritePolicy:
    keep_ok_details: bool = False
    max_rows: int = _MAX_ROWS
    max_text_characters: int = _MAX_TEXT

    def __post_init__(self) -> None:
        if type(self.keep_ok_details) is not bool:
            raise TypeError("keep_ok_details must be a boolean")
        if type(self.max_rows) is not int or self.max_rows < 1:
            raise ValueError("max_rows must be a positive integer")
        if type(self.max_text_characters) is not int or self.max_text_characters < 1:
            raise ValueError("max_text_characters must be a positive integer")


@dataclass(frozen=True, slots=True)
class DetailArtifact:
    subject_kind: str
    subject_id: str
    path: Path


@dataclass(frozen=True, slots=True)
class DetailWriteFailure:
    subject_kind: str
    subject_id: str
    message: str


@dataclass(frozen=True, slots=True)
class DetailWriteResult:
    artifacts: tuple[DetailArtifact, ...]
    skipped_subjects: tuple[str, ...]
    failures: tuple[DetailWriteFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def paths(self) -> tuple[Path, ...]:
        return tuple(item.path for item in self.artifacts)


def write_detail_reports(
    run_result: RunResult,
    *,
    details_root: Path | None = None,
    policy: DetailWritePolicy | None = None,
) -> DetailWriteResult:
    effective = policy or DetailWritePolicy(keep_ok_details=_configured_keep_ok_details(run_result))
    root = _details_root(run_result, details_root)
    run_root = _run_root(run_result)
    artifacts: list[DetailArtifact] = []
    skipped: list[str] = []
    failures: list[DetailWriteFailure] = []
    subjects = (
        ("file", tuple(getattr(run_result, "file_results", ()))),
        ("scenario", tuple(getattr(run_result, "scenario_results", ()))),
    )
    for kind, results in subjects:
        for result in results:
            subject_id = _subject_id(kind, result)
            if not _should_write(result, effective):
                skipped.append(f"{kind}:{subject_id}")
                continue
            try:
                destination = (
                    write_file_detail(
                        result,
                        details_root=root,
                        run_root=run_root,
                        policy=effective,
                    )
                    if kind == "file"
                    else write_scenario_detail(
                        result,
                        details_root=root,
                        run_root=run_root,
                        policy=effective,
                    )
                )
            except Exception as error:
                failures.append(
                    DetailWriteFailure(
                        subject_kind=kind,
                        subject_id=subject_id,
                        message=_bounded(
                            f"{type(error).__name__}: {error}",
                            effective.max_text_characters,
                        ),
                    )
                )
            else:
                artifacts.append(DetailArtifact(kind, subject_id, destination))
    artifacts.sort(key=lambda item: (item.subject_kind, item.subject_id.casefold()))
    skipped.sort(key=str.casefold)
    failures.sort(key=lambda item: (item.subject_kind, item.subject_id.casefold()))
    return DetailWriteResult(tuple(artifacts), tuple(skipped), tuple(failures))


def write_file_detail(
    file_result: FileResult,
    *,
    details_root: Path,
    run_root: Path,
    policy: DetailWritePolicy | None = None,
) -> Path:
    effective = policy or DetailWritePolicy()
    root, owned_root = _validated_roots(details_root, run_root)
    destination = root / "files" / f"{file_detail_key(_file_id(file_result))}.md"
    text = render_file_detail(
        file_result,
        report_path=destination,
        run_root=owned_root,
        policy=effective,
    )
    return atomic_write_text(
        destination,
        text,
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=root,
        role="file detail report",
    )


def write_scenario_detail(
    scenario_result: ScenarioResult,
    *,
    details_root: Path,
    run_root: Path,
    policy: DetailWritePolicy | None = None,
) -> Path:
    effective = policy or DetailWritePolicy()
    root, owned_root = _validated_roots(details_root, run_root)
    destination = root / "scenarios" / f"{scenario_detail_key(_scenario_id(scenario_result))}.md"
    text = render_scenario_detail(
        scenario_result,
        report_path=destination,
        run_root=owned_root,
        policy=effective,
    )
    return atomic_write_text(
        destination,
        text,
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=root,
        role="scenario detail report",
    )


def render_file_detail(
    file_result: FileResult,
    *,
    report_path: Path,
    run_root: Path,
    policy: DetailWritePolicy | None = None,
) -> str:
    effective = policy or DetailWritePolicy()
    report, root = _validated_report_paths(report_path, run_root)
    compile_summary = getattr(file_result, "compile_summary", None)
    lines = [
        "# File Detail",
        "",
        "## Identity",
        "",
        f"- File: {_code(_file_id(file_result))}",
        f"- Module: {_code(_text(getattr(file_result, 'module_name', '')))}",
        "",
        "## Outcome",
        "",
        f"- Status: {_code(_enum(getattr(file_result, 'status', '')))}",
        f"- Diagnostic class: {_code(_enum(getattr(file_result, 'diagnostic_class', '')))}",
        f"- Error kind: {_code(_enum(getattr(file_result, 'error_kind', '')))}",
        f"- Direct: {_yes_no(bool(getattr(file_result, 'is_direct', False)))}",
        "",
    ]
    message = _bounded(
        _text(getattr(file_result, "primary_message", "")),
        effective.max_text_characters,
    )
    if message:
        lines += ["## Primary Diagnostic", "", _paragraph(message), ""]
    lines += _blockers(getattr(file_result, "blocked_by", ()))
    lines += _compile_section(compile_summary, effective)
    lines += _field_table(
        "Static Scan",
        getattr(file_result, "scan_counts", None),
        effective,
    )
    lines += _evidence_section(
        (
            ("scan", getattr(file_result, "scan_log_path", None)),
            ("stdout", getattr(compile_summary, "stdout_path", None)),
            ("stderr", getattr(compile_summary, "stderr_path", None)),
        ),
        report,
        root,
    )
    lines += _artifact_section(getattr(file_result, "artifacts", ()), report, root, effective)
    return _finish(lines)


def render_scenario_detail(
    scenario_result: ScenarioResult,
    *,
    report_path: Path,
    run_root: Path,
    policy: DetailWritePolicy | None = None,
) -> str:
    effective = policy or DetailWritePolicy()
    report, root = _validated_report_paths(report_path, run_root)
    lines = [
        "# Scenario Detail",
        "",
        "## Identity",
        "",
        f"- Scenario: {_code(_scenario_id(scenario_result))}",
        f"- Script: {_code(_portable(getattr(scenario_result, 'script_path', '')))}",
        f"- Required: {_yes_no(bool(getattr(scenario_result, 'required', False)))}",
        "",
        "## Outcome",
        "",
        f"- Status: {_code(_enum(getattr(scenario_result, 'status', '')))}",
        f"- Execution: {_code(_enum(getattr(scenario_result, 'execution_state', '')))}",
        f"- Diagnostic class: {_code(_enum(getattr(scenario_result, 'diagnostic_class', '')))}",
        f"- Error kind: {_code(_enum(getattr(scenario_result, 'error_kind', '')))}",
        f"- Exit code: {_code(_text(getattr(scenario_result, 'exit_code', None)))}",
        f"- Timed out: {_yes_no(bool(getattr(scenario_result, 'timed_out', False)))}",
        f"- Duration: {_duration(getattr(scenario_result, 'duration_ms', 0))}",
        "",
    ]
    message = _bounded(
        _text(getattr(scenario_result, "primary_message", "")),
        effective.max_text_characters,
    )
    if message:
        lines += ["## Primary Diagnostic", "", _paragraph(message), ""]
    command = tuple(getattr(scenario_result, "command", ()))
    if command:
        lines += [
            "## Execution Request",
            "",
            f"- Working directory: {_code(_portable(getattr(scenario_result, 'working_directory', '')))}",
            "- Command:",
            "",
            _block(" ".join(_text(part) for part in command)),
            "",
        ]
    lines += _blockers(getattr(scenario_result, "blocked_by", ()))
    lines += _sections(getattr(scenario_result, "sections", ()), effective)
    lines += _assertions(getattr(scenario_result, "assertions", ()), report, root, effective)
    lines += _gold_section(scenario_result, report, root)
    lines += _evidence_section(
        (
            ("stdout", getattr(scenario_result, "stdout_path", None)),
            ("stderr", getattr(scenario_result, "stderr_path", None)),
            ("normalized output", getattr(scenario_result, "normalized_output_path", None)),
            ("gold", getattr(scenario_result, "gold_path", None)),
            ("diff", getattr(scenario_result, "gold_diff_path", None)),
        ),
        report,
        root,
    )
    lines += _artifact_section(getattr(scenario_result, "artifacts", ()), report, root, effective)
    return _finish(lines)


def file_detail_key(file_identity: str | Path) -> str:
    identity = _required(_portable(file_identity), "file_identity")
    return _safe_key(identity, Path(identity).name)


def scenario_detail_key(scenario_id: str) -> str:
    identity = _required(scenario_id, "scenario_id")
    return _safe_key(identity, identity)


def _compile_section(summary: object, policy: DetailWritePolicy) -> list[str]:
    if summary is None:
        return ["## Compilation", "", "No compilation summary is available.", ""]
    lines = [
        "## Compilation",
        "",
        f"- Execution: {_code(_enum(getattr(summary, 'execution_state', '')))}",
        f"- Exit code: {_code(_text(getattr(summary, 'exit_code', None)))}",
        f"- Timed out: {_yes_no(bool(getattr(summary, 'timed_out', False)))}",
        f"- Duration: {_duration(getattr(summary, 'duration_ms', 0))}",
        f"- Error kind: {_code(_enum(getattr(summary, 'error_kind', '')))}",
        "",
    ]
    detail = _bounded(
        _text(getattr(summary, "error_detail", "")),
        policy.max_text_characters,
    )
    if detail:
        lines += ["### Diagnostic Detail", "", _block(detail), ""]
    return lines


def _field_table(
    title: str,
    value: object,
    policy: DetailWritePolicy,
) -> list[str]:
    fields = _fields(value)
    if not fields:
        return [f"## {title}", "", "None.", ""]
    shown = fields[: policy.max_rows]
    lines = [f"## {title}", "", "| Field | Value |", "|---|---:|"]
    lines += [f"| {_cell(_human(name))} | {_cell(_text(item))} |" for name, item in shown]
    return lines + [""] + _notice(len(shown), len(fields))


def _sections(items: Iterable[object], policy: DetailWritePolicy) -> list[str]:
    values = tuple(items)
    if not values:
        return ["## Marker Sections", "", "None.", ""]
    shown = values[: policy.max_rows]
    lines = [
        "## Marker Sections",
        "",
        "| Section | Completed | Required | Message |",
        "|---|:---:|:---:|---|",
    ]
    for item in shown:
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(_attr(item, "section_id", "id")),
                    _cell(_yes_no(bool(_attr(item, "completed", default=False)))),
                    _cell(_yes_no(bool(_attr(item, "required", default=False)))),
                    _cell(
                        _bounded(
                            _text(_attr(item, "message", default="")), policy.max_text_characters
                        )
                        or "—"
                    ),
                )
            )
            + " |"
        )
    return lines + [""] + _notice(len(shown), len(values))


def _assertions(
    items: Iterable[object],
    report: Path,
    root: Path,
    policy: DetailWritePolicy,
) -> list[str]:
    values = tuple(items)
    if not values:
        return ["## Assertions", "", "None.", ""]
    shown = values[: policy.max_rows]
    lines = [
        "## Assertions",
        "",
        "| Assertion | Kind | Status | Section | Message | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for item in shown:
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(_attr(item, "assertion_id", "id")),
                    _cell(_enum(_attr(item, "assertion_kind", "kind"))),
                    _cell(_enum(_attr(item, "status"))),
                    _cell(_text(_attr(item, "section_id", default="")) or "—"),
                    _cell(
                        _bounded(
                            _text(_attr(item, "message", default="")), policy.max_text_characters
                        )
                        or "—"
                    ),
                    _path_ref("evidence", _attr(item, "evidence_path", default=None), report, root),
                )
            )
            + " |"
        )
    return lines + [""] + _notice(len(shown), len(values))


def _gold_section(result: object, report: Path, root: Path) -> list[str]:
    gold = getattr(result, "gold_path", None)
    matched = getattr(result, "gold_match", None)
    state = (
        "Not applicable"
        if gold is None
        else "Match"
        if matched is True
        else "Mismatch"
        if matched is False
        else "Not evaluated"
    )
    return [
        "## Gold Comparison",
        "",
        f"- State: {_code(state)}",
        f"- Gold: {_path_ref('gold', gold, report, root)}",
        f"- Diff: {_path_ref('diff', getattr(result, 'gold_diff_path', None), report, root)}",
        "",
    ]


def _blockers(items: Iterable[object]) -> list[str]:
    values = sorted({_text(item) for item in items if _text(item)}, key=str.casefold)
    if not values:
        return ["## Blockers", "", "None.", ""]
    return ["## Blockers", "", *(f"- {_code(item)}" for item in values), ""]


def _evidence_section(
    items: Iterable[tuple[str, object]],
    report: Path,
    root: Path,
) -> list[str]:
    return [
        "## Evidence",
        "",
        *(
            f"- {_escape(label.capitalize())}: {_path_ref(label, value, report, root)}"
            for label, value in items
        ),
        "",
    ]


def _artifact_section(
    items: Iterable[object],
    report: Path,
    root: Path,
    policy: DetailWritePolicy,
) -> list[str]:
    values = tuple(items)
    if not values:
        return ["## Produced Artifacts", "", "None.", ""]
    shown = values[: policy.max_rows]
    lines = [
        "## Produced Artifacts",
        "",
        "| Role | Required | Size | Path |",
        "|---|:---:|---:|---|",
    ]
    for item in shown:
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(_enum(_attr(item, "role", "artifact_role", default="artifact"))),
                    _cell(_yes_no(bool(_attr(item, "required", default=False)))),
                    _cell(_text(_attr(item, "size_bytes", "size", default=None)) or "—"),
                    _path_ref("artifact", _attr(item, "path", default=None), report, root),
                )
            )
            + " |"
        )
    return lines + [""] + _notice(len(shown), len(values))


def _path_ref(label: str, value: object, report: Path, root: Path) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, bytes) or not isinstance(value, (str, os.PathLike)):
        raise TypeError("path reference must be path-like text")
    path = Path(value)
    display = _portable(path)
    resolved = (path if path.is_absolute() else root / path).resolve(strict=False)
    if not _contained(resolved, root):
        return _code(display)
    if not resolved.exists():
        return f"Missing: {_code(display)}"
    relative = Path(os.path.relpath(resolved, report.parent)).as_posix()
    href = quote(relative, safe="/._-~")
    return f"[{_escape(label)}]({href}) — {_code(display)}"


def _details_root(run_result: object, explicit: Path | None) -> Path:
    run_paths = getattr(run_result, "run_paths", None)
    candidate = explicit
    if candidate is None:
        candidate = getattr(run_paths, "details_dir", None)
    if candidate is None:
        candidate = getattr(run_paths, "details_root", None)
    if candidate is None:
        raise ValueError("RunPaths must provide details_dir or details_root")
    root = _absolute(candidate, "details_root")
    require_owned = getattr(run_paths, "require_owned_path", None)
    return Path(require_owned(root)) if callable(require_owned) else root


def _run_root(run_result: object) -> Path:
    run_paths = getattr(run_result, "run_paths", None)
    for name in ("run_dir", "run_root"):
        value = getattr(run_paths, name, None)
        if value is not None:
            return _absolute(value, name)
    raise ValueError("RunPaths must provide run_dir or run_root")


def _configured_keep_ok_details(run_result: object) -> bool:
    value = getattr(getattr(run_result, "run_config", None), "keep_ok_details", False)
    if type(value) is not bool:
        raise TypeError("RunConfig.keep_ok_details must be a boolean")
    return value


def _validated_roots(details_root: Path, run_root: Path) -> tuple[Path, Path]:
    root = _absolute(details_root, "details_root")
    owned = _absolute(run_root, "run_root")
    if not _contained(root, owned):
        raise ValueError("details_root escapes run_root")
    return root, owned


def _validated_report_paths(report: Path, run_root: Path) -> tuple[Path, Path]:
    report_path = _absolute(report, "report_path")
    root = _absolute(run_root, "run_root")
    if not _contained(report_path, root):
        raise ValueError("report_path escapes run_root")
    return report_path, root


def _should_write(result: object, policy: DetailWritePolicy) -> bool:
    status = getattr(result, "status", None)
    text = _enum(status)
    return policy.keep_ok_details or text != ValidationStatus.OK.value


def _subject_id(kind: str, result: object) -> str:
    return _file_id(result) if kind == "file" else _scenario_id(result)


def _file_id(result: object) -> str:
    return _required(_portable(_attr(result, "file_path")), "file_path")


def _scenario_id(result: object) -> str:
    return _required(_text(_attr(result, "scenario_id")), "scenario_id")


def _safe_key(identity: str, preferred: str) -> str:
    name = _UNSAFE_KEY.sub("-", preferred.replace("\\", "/")).strip("-._ ")
    name = (name or "subject")[:96].rstrip(". ")
    if name.split(".", 1)[0].upper() in _RESERVED:
        name = f"_{name}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"{name}--{digest}"


def _fields(value: object) -> list[tuple[str, object]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return sorted(((_text(key), item) for key, item in value.items()), key=lambda x: x[0])
    slots = getattr(type(value), "__slots__", ())
    names = (slots,) if isinstance(slots, str) else tuple(slots)
    if not names and hasattr(value, "__dict__"):
        names = tuple(vars(value))
    return [
        (name, getattr(value, name))
        for name in sorted(names)
        if isinstance(name, str)
        and not name.startswith("_")
        and hasattr(value, name)
        and not callable(getattr(value, name))
    ]


def _attr(value: object, *names: str, default: object = "") -> object:
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def _notice(shown: int, total: int) -> list[str]:
    return [] if shown >= total else [f"Showing {shown} of {total}.", ""]


def _finish(lines: Sequence[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"


def _paragraph(value: str) -> str:
    return "  \n".join(_escape(line) for line in value.splitlines())


def _block(value: str) -> str:
    return "\n".join(f"    {line}" for line in value.rstrip().splitlines())


def _code(value: object) -> str:
    text = _text(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(item) for item in re.findall(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _escape(value: object) -> str:
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", _text(value))


def _cell(value: object) -> str:
    return _escape(value).replace("|", r"\|").replace("\r", " ").replace("\n", " / ")


def _portable(value: object) -> str:
    return "" if value is None else str(value).replace("\\", "/")


def _enum(value: object) -> str:
    return _text(value.value) if isinstance(value, Enum) else _text(value)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return _text(value.value)
    return str(value)


def _human(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _duration(value: object) -> str:
    return f"{value / 1000:.3f} s" if type(value) is int and value > 0 else "0 s"


def _bounded(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    marker = " … [truncated; see raw evidence]"
    return value[: max(0, limit - len(marker))].rstrip() + marker[:limit]


def _absolute(value: object, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return value.resolve(strict=False)


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _required(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip() or "\x00" in value:
        raise ValueError(f"{field} must be non-empty and contain no NUL")
    return value


def failure_signature(result: FileResult) -> str:
    """Return a stable coarse failure signature for inventory grouping."""

    if result.status is ValidationStatus.OK:
        return "OK"
    if result.status is ValidationStatus.SKIPPED:
        return "SKIPPED"

    summary = result.compile_summary
    if summary.timed_out or summary.error_kind is ErrorKind.TIMEOUT:
        return "TIMEOUT"
    text = "\n".join((summary.first_error, summary.error_detail))
    for signature, pattern in _GLOBAL_SIGNATURE_RULES:
        if pattern.search(text):
            return signature
    if summary.error_kind is ErrorKind.SYNTAX:
        return "SYNTAX_ERROR"
    if summary.error_kind is ErrorKind.TYPE:
        return "TYPE_ERROR"
    if summary.error_kind is ErrorKind.TOOL:
        return "GF_TOOL_ERROR"
    if summary.error_kind is ErrorKind.IO:
        return "IO_ERROR"
    if summary.error_kind is ErrorKind.INTERNAL:
        return "GF_INTERNAL_ERROR"
    return "OTHER"


def write_global_scan_reports(run_result: RunResult) -> tuple[Path, Path]:
    """Write deterministic JSON and CSV views of one Diagnostic inventory run."""

    if run_result.run_config.mode.value != "diagnostic":
        raise ValueError("global scan reports require diagnostic mode")

    details_root = run_result.run_paths.details_dir
    details_root.mkdir(parents=True, exist_ok=True)
    rows = [
        _global_scan_row(result, run_root=run_result.run_paths.run_dir)
        for result in run_result.file_results
    ]

    json_path = details_root / _GLOBAL_SCAN_JSON
    document: JsonObject = {
        "schema": "gf-wordbench-global-scan-v1",
        "run_id": str(run_result.run_paths.run_id),
        "mode": run_result.run_config.mode.value,
        "gf_version": run_result.gf_version,
        "overall_status": run_result.overall_status.value,
        "totals": {
            "files_seen": run_result.totals.files_seen,
            "files_included": run_result.totals.files_included,
            "files_excluded": run_result.totals.files_excluded,
            "files_ok": run_result.totals.files_ok,
            "files_fail": run_result.totals.files_fail,
            "files_error": run_result.totals.files_error,
            "files_skipped": run_result.totals.files_skipped,
            "direct_fail": run_result.totals.direct_fail,
            "downstream_fail": run_result.totals.downstream_fail,
            "ambiguous_fail": run_result.totals.ambiguous_fail,
        },
        "failure_signatures": _global_signature_counts(run_result.file_results),
        "files": rows,
    }
    write_json(json_path, document)

    csv_path = details_root / _GLOBAL_SCAN_CSV
    stream = StringIO(newline="")
    fieldnames = (
        "status",
        "diagnostic_class",
        "module",
        "source",
        "exit_code",
        "error_kind",
        "failure_signature",
        "duration_ms",
        "gfo_produced",
        "blocked_by",
        "first_error",
        "stdout",
        "stderr",
        "scan_log",
    )
    csv_writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    csv_writer.writeheader()
    for row in rows:
        csv_writer.writerow({key: _global_csv_value(row.get(key)) for key in fieldnames})
    atomic_write_text(
        csv_path,
        stream.getvalue(),
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=details_root,
        role="global scan CSV report",
    )
    return json_path, csv_path


def _global_scan_row(result: FileResult, *, run_root: Path) -> dict[str, JsonValue]:
    summary = result.compile_summary
    return {
        "status": _global_display_status(result),
        "validation_status": result.status.value,
        "diagnostic_class": result.diagnostic_class.value,
        "module": result.module_name,
        "source": result.file_path.as_posix(),
        "exit_code": summary.exit_code,
        "error_kind": summary.error_kind.value,
        "failure_signature": failure_signature(result),
        "duration_ms": summary.duration_ms,
        "gfo_produced": bool(summary.produced_artifacts),
        "blocked_by": list(result.blocked_by),
        "first_error": summary.first_error,
        "stdout": _global_relative(summary.stdout_path, run_root),
        "stderr": _global_relative(summary.stderr_path, run_root),
        "scan_log": _global_relative(result.scan_log_path, run_root),
    }


def _global_display_status(result: FileResult) -> str:
    if result.status is ValidationStatus.OK:
        return "PASS"
    if result.diagnostic_class is DiagnosticClass.DOWNSTREAM:
        return "BLOCKED"
    if result.compile_summary.timed_out:
        return "TIMEOUT"
    if result.status is ValidationStatus.FAIL:
        return "FAIL"
    if result.status is ValidationStatus.SKIPPED:
        return "SKIPPED"
    return "ERROR"


def _global_signature_counts(results: list[FileResult]) -> dict[str, JsonValue]:
    counts: dict[str, int] = {}
    for result in results:
        signature = failure_signature(result)
        if signature in {"OK", "SKIPPED"}:
            continue
        counts[signature] = counts.get(signature, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _global_relative(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _global_csv_value(value: JsonValue | None) -> str | int:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if isinstance(value, dict):
        return ";".join(f"{key}={item}" for key, item in sorted(value.items()))
    return str(value)


__all__ = (
    "DetailArtifact",
    "DetailWriteFailure",
    "DetailWritePolicy",
    "DetailWriteResult",
    "failure_signature",
    "file_detail_key",
    "render_file_detail",
    "render_scenario_detail",
    "scenario_detail_key",
    "write_detail_reports",
    "write_file_detail",
    "write_global_scan_reports",
    "write_scenario_detail",
)
