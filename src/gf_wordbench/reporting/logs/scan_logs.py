"""Deterministic aggregation of existing per-source static-scan logs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any, Final, TypeAlias

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.kernel.errors import ContractViolationError

__all__ = (
    "ALL_SCAN_LOGS_FILENAME",
    "ScanLogAggregate",
    "ScanLogAggregateIssue",
    "ScanLogAggregateStatus",
    "ScanLogSection",
    "build_scan_log_sections",
    "render_all_scan_logs",
    "write_all_scan_logs_result",
)

PathLike: TypeAlias = str | os.PathLike[str]
ResultLike: TypeAlias = Mapping[str, Any] | object

ALL_SCAN_LOGS_FILENAME: Final[str] = "ALL_SCAN_LOGS.TXT"
_FORMAT_TITLE: Final[str] = "GF WORDBENCH — ALL SCAN LOGS"
_SECTION_RULE: Final[str] = "=" * 80
_SECTION_INNER_RULE: Final[str] = "-" * 80
_NULL_TEXT: Final[str] = "null"


@unique
class ScanLogAggregateStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class ScanLogAggregateIssue:
    subject: str
    code: str
    message: str
    path: Path | None = None
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", _required_text(self.subject, "subject"))
        object.__setattr__(self, "code", _required_text(self.code, "code"))
        object.__setattr__(self, "message", _required_text(self.message, "message"))
        if self.path is not None:
            object.__setattr__(self, "path", _absolute_path(self.path, "path"))
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")


@dataclass(frozen=True, slots=True)
class ScanLogSection:
    subject: str
    status: str
    required: bool
    log_path: Path | None = None
    display_path: str | None = None
    content: str | None = None
    sha256: str | None = None
    missing_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", _canonical_subject(self.subject))
        object.__setattr__(self, "status", _required_text(self.status, "status"))
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")
        if self.log_path is not None:
            object.__setattr__(self, "log_path", _absolute_path(self.log_path, "log_path"))
        if self.display_path is not None:
            object.__setattr__(
                self,
                "display_path",
                _canonical_display_path(self.display_path),
            )
        if self.content is not None:
            if not isinstance(self.content, str):
                raise TypeError("content must be a string or None")
            if "\x00" in self.content:
                raise ValueError("content must not contain a NUL character")
        if self.sha256 is not None:
            digest = self.sha256.casefold()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("sha256 must be a lowercase hexadecimal SHA-256 digest")
            object.__setattr__(self, "sha256", digest)
        if self.missing_reason is not None:
            object.__setattr__(
                self,
                "missing_reason",
                _single_line(self.missing_reason, "missing_reason"),
            )
        if self.content is None:
            if self.sha256 is not None:
                raise ValueError("a missing scan log cannot have a SHA-256 digest")
            if self.missing_reason is None:
                raise ValueError("a missing scan log requires missing_reason")
        else:
            if self.log_path is None:
                raise ValueError("an included scan log requires log_path")
            if self.sha256 is None:
                raise ValueError("an included scan log requires sha256")
            if self.missing_reason is not None:
                raise ValueError("an included scan log cannot have missing_reason")

    @property
    def included(self) -> bool:
        return self.content is not None


@dataclass(frozen=True, slots=True)
class ScanLogAggregate:
    run_id: str
    project_id: str
    generated_at: datetime
    source_count: int
    sections: tuple[ScanLogSection, ...]
    text: str
    status: ScanLogAggregateStatus
    issues: tuple[ScanLogAggregateIssue, ...] = field(default_factory=tuple)
    path: Path | None = None
    sha256: str | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _single_line(self.run_id, "run_id"))
        object.__setattr__(self, "project_id", _single_line(self.project_id, "project_id"))
        object.__setattr__(self, "generated_at", _utc(self.generated_at, "generated_at"))
        _non_negative_int(self.source_count, "source_count")
        sections = tuple(self.sections)
        if not all(isinstance(item, ScanLogSection) for item in sections):
            raise TypeError("sections must contain ScanLogSection values")
        object.__setattr__(self, "sections", sections)
        if self.source_count != len(sections):
            raise ValueError("source_count must equal the number of sections")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not self.text.endswith("\n"):
            raise ValueError("aggregate text must end with a newline")
        if "\x00" in self.text:
            raise ValueError("aggregate text must not contain a NUL character")
        object.__setattr__(self, "status", _aggregate_status(self.status))
        issues = tuple(self.issues)
        if not all(isinstance(item, ScanLogAggregateIssue) for item in issues):
            raise TypeError("issues must contain ScanLogAggregateIssue values")
        object.__setattr__(self, "issues", tuple(sorted(issues, key=_issue_key)))
        if self.path is not None:
            object.__setattr__(self, "path", _absolute_path(self.path, "path"))
        if self.sha256 is not None:
            digest = self.sha256.casefold()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("sha256 must be a lowercase hexadecimal SHA-256 digest")
            object.__setattr__(self, "sha256", digest)
        if self.size_bytes is not None:
            _non_negative_int(self.size_bytes, "size_bytes")
        if self.path is None and (self.sha256 is not None or self.size_bytes is not None):
            raise ValueError("unwritten aggregate cannot have persisted hash or size")
        if self.path is not None and (self.sha256 is None or self.size_bytes is None):
            raise ValueError("written aggregate requires persisted hash and size")

    @property
    def included_section_count(self) -> int:
        return sum(1 for section in self.sections if section.included)

    @property
    def missing_section_count(self) -> int:
        return self.source_count - self.included_section_count

    @property
    def missing_required_count(self) -> int:
        return sum(1 for section in self.sections if not section.included and section.required)


def build_scan_log_sections(
    file_results: Iterable[ResultLike],
    *,
    run_root: PathLike | None = None,
    project_root: PathLike | None = None,
    strict_paths: bool = True,
    max_log_bytes: int | None = None,
) -> tuple[ScanLogSection, ...]:
    root = _optional_absolute_path(run_root, "run_root")
    project_boundary = _optional_absolute_path(project_root, "project_root")
    if not isinstance(strict_paths, bool):
        raise TypeError("strict_paths must be a bool")
    if max_log_bytes is not None:
        _positive_int(max_log_bytes, "max_log_bytes")

    indexed: list[tuple[str, int, ResultLike]] = []
    for index, result in enumerate(tuple(file_results)):
        subject = _result_subject(result, index, project_boundary)
        indexed.append((_subject_sort_key(subject), index, result))

    sections: list[ScanLogSection] = []
    seen_subjects: set[str] = set()
    seen_paths: dict[str, str] = {}

    for _, index, result in sorted(indexed, key=lambda item: (item[0], item[1])):
        subject = _result_subject(result, index, project_boundary)
        normalized_subject = _subject_sort_key(subject)
        if normalized_subject in seen_subjects:
            raise _contract_error(
                "Duplicate file-result identity while building scan-log aggregate",
                subject=subject,
            )
        seen_subjects.add(normalized_subject)

        required = _result_required(result)
        status = _result_status(result)
        raw_path = _result_scan_log_path(result)
        if raw_path is None:
            sections.append(
                ScanLogSection(
                    subject=subject,
                    status="MISSING",
                    required=required,
                    missing_reason=_missing_reason(result, "scan log path is absent"),
                )
            )
            continue

        try:
            path = _absolute_path(raw_path, "scan_log_path")
        except (TypeError, ValueError) as exc:
            if strict_paths:
                raise _contract_error(str(exc), subject=subject) from exc
            sections.append(
                ScanLogSection(
                    subject=subject,
                    status="MISSING",
                    required=required,
                    missing_reason=_missing_reason(result, str(exc)),
                )
            )
            continue

        if root is not None and not _is_within(path, root):
            message = "scan log path is outside the run root"
            if strict_paths:
                raise _contract_error(message, subject=subject, path=path)
            sections.append(
                ScanLogSection(
                    subject=subject,
                    status="MISSING",
                    required=required,
                    log_path=path,
                    display_path=_display_path(path, root),
                    missing_reason=_missing_reason(result, message),
                )
            )
            continue

        path_key = _path_key(path)
        previous_subject = seen_paths.get(path_key)
        if previous_subject is not None:
            raise _contract_error(
                f"scan log path is shared with {previous_subject!r}",
                subject=subject,
                path=path,
            )
        seen_paths[path_key] = subject

        if not path.is_file():
            sections.append(
                ScanLogSection(
                    subject=subject,
                    status="MISSING",
                    required=required,
                    log_path=path,
                    display_path=_display_path(path, root),
                    missing_reason=_missing_reason(result, "scan log file does not exist"),
                )
            )
            continue

        raw = path.read_bytes()
        if max_log_bytes is not None and len(raw) > max_log_bytes:
            raise _contract_error(
                f"scan log exceeds the configured limit of {max_log_bytes} bytes",
                subject=subject,
                path=path,
            )
        try:
            content = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise _contract_error(
                "scan log is not valid UTF-8",
                subject=subject,
                path=path,
            ) from exc

        sections.append(
            ScanLogSection(
                subject=subject,
                status=status,
                required=required,
                log_path=path,
                display_path=_display_path(path, root),
                content=content,
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )

    return tuple(sections)


def render_all_scan_logs(
    *,
    run_id: str,
    project_id: str,
    generated_at: datetime,
    sections: Sequence[ScanLogSection],
) -> ScanLogAggregate:
    canonical_sections = tuple(sections)
    if not all(isinstance(item, ScanLogSection) for item in canonical_sections):
        raise TypeError("sections must contain ScanLogSection values")

    ordered = tuple(
        sorted(
            canonical_sections,
            key=lambda item: _subject_sort_key(item.subject),
        )
    )
    identities = [_subject_sort_key(item.subject) for item in ordered]
    if len(identities) != len(set(identities)):
        raise _contract_error(
            "scan-log aggregate contains duplicate subjects",
            subject=None,
        )

    generated = _utc(generated_at, "generated_at")
    included = sum(1 for section in ordered if section.included)
    header = "\n".join(
        (
            _FORMAT_TITLE,
            f"Run ID: {_single_line(run_id, 'run_id')}",
            f"Project: {_single_line(project_id, 'project_id')}",
            f"Generated: {_rfc3339_utc(generated)}",
            f"Source count: {len(ordered)}",
            f"Included sections: {included}",
            "Authoritative source: individual files under raw/scan/",
            "",
            "",
        )
    )

    issues: list[ScanLogAggregateIssue] = []
    rendered_sections: list[str] = []
    for section in ordered:
        rendered_sections.append(_render_section(section))
        if not section.included:
            issues.append(
                ScanLogAggregateIssue(
                    subject=section.subject,
                    code="MISSING_SCAN_LOG",
                    message=section.missing_reason or "scan log evidence is missing",
                    path=section.log_path,
                    required=section.required,
                )
            )

    text = header + "".join(rendered_sections)
    if not text.endswith("\n"):
        text += "\n"

    required_missing = any(issue.required for issue in issues)
    status = (
        ScanLogAggregateStatus.ERROR
        if required_missing
        else ScanLogAggregateStatus.PARTIAL
        if issues
        else ScanLogAggregateStatus.COMPLETE
    )
    return ScanLogAggregate(
        run_id=run_id,
        project_id=project_id,
        generated_at=generated,
        source_count=len(ordered),
        sections=ordered,
        text=text,
        status=status,
        issues=tuple(issues),
    )


def write_all_scan_logs_result(
    run_result: ResultLike | None = None,
    *,
    file_results: Iterable[ResultLike] | None = None,
    destination: PathLike | None = None,
    run_root: PathLike | None = None,
    project_root: PathLike | None = None,
    run_id: str | None = None,
    project_id: str | None = None,
    generated_at: datetime | None = None,
    strict_paths: bool = True,
    max_log_bytes: int | None = None,
    replace_retry_delays: Sequence[float] = (),
) -> ScanLogAggregate:
    context = _resolve_context(
        run_result,
        file_results=file_results,
        destination=destination,
        run_root=run_root,
        project_root=project_root,
        run_id=run_id,
        project_id=project_id,
        generated_at=generated_at,
    )
    sections = build_scan_log_sections(
        context.file_results,
        run_root=context.run_root,
        project_root=context.project_root,
        strict_paths=strict_paths,
        max_log_bytes=max_log_bytes,
    )
    aggregate = render_all_scan_logs(
        run_id=context.run_id,
        project_id=context.project_id,
        generated_at=context.generated_at,
        sections=sections,
    )
    written_path = atomic_write_text(
        context.destination,
        aggregate.text,
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=context.run_root,
        role="aggregate scan log",
        replace_retry_delays=tuple(replace_retry_delays),
    )
    payload = written_path.read_bytes()
    return ScanLogAggregate(
        run_id=aggregate.run_id,
        project_id=aggregate.project_id,
        generated_at=aggregate.generated_at,
        source_count=aggregate.source_count,
        sections=aggregate.sections,
        text=aggregate.text,
        status=aggregate.status,
        issues=aggregate.issues,
        path=written_path,
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )


def _write_all_scan_logs_compat(
    run_result: ResultLike | None = None,
    **kwargs: Any,
) -> Path:
    result = write_all_scan_logs_result(run_result, **kwargs)
    if result.path is None:
        raise AssertionError("aggregate writer did not produce a path")
    return result.path


@dataclass(frozen=True, slots=True)
class _WriterContext:
    file_results: tuple[ResultLike, ...]
    destination: Path
    run_root: Path
    project_root: Path | None
    run_id: str
    project_id: str
    generated_at: datetime


def _resolve_context(
    run_result: ResultLike | None,
    *,
    file_results: Iterable[ResultLike] | None,
    destination: PathLike | None,
    run_root: PathLike | None,
    project_root: PathLike | None,
    run_id: str | None,
    project_id: str | None,
    generated_at: datetime | None,
) -> _WriterContext:
    if file_results is None:
        if run_result is None:
            raise TypeError("file_results or run_result is required")
        raw_results = _first_field(
            run_result,
            ("file_results", "files", "results"),
            _MISSING,
        )
        if raw_results is _MISSING:
            raise TypeError("run_result does not expose file_results")
        file_results = raw_results
    if isinstance(file_results, (str, bytes, Mapping)):
        raise TypeError("file_results must be an iterable of result objects")
    results = tuple(file_results)

    resolved_run_root = _optional_absolute_path(run_root, "run_root")
    if resolved_run_root is None and run_result is not None:
        resolved_run_root = _extract_run_root(run_result)

    resolved_destination = _optional_absolute_path(destination, "destination")
    if resolved_destination is None and run_result is not None:
        resolved_destination = _extract_destination(run_result)
    if resolved_destination is None:
        if resolved_run_root is None:
            raise TypeError("destination or run_root is required")
        resolved_destination = resolved_run_root / "raw" / ALL_SCAN_LOGS_FILENAME

    if resolved_run_root is None:
        resolved_run_root = _infer_run_root(resolved_destination)
    if not _is_within(resolved_destination, resolved_run_root):
        raise _contract_error(
            "aggregate destination is outside the run root",
            subject=None,
            path=resolved_destination,
        )

    resolved_run_id = run_id
    if resolved_run_id is None and run_result is not None:
        resolved_run_id = _text_field(run_result, ("run_id", "id"))
    if not resolved_run_id:
        resolved_run_id = resolved_run_root.name.removeprefix("run_")

    resolved_project_id = project_id
    if resolved_project_id is None and run_result is not None:
        resolved_project_id = _text_field(
            run_result,
            ("project_id", "active_project_id"),
        )
        if not resolved_project_id:
            project = _first_field(run_result, ("project", "project_identity"), None)
            if project is not None:
                resolved_project_id = _text_field(project, ("project_id", "id", "name"))
    if not resolved_project_id:
        raise TypeError("project_id is required")

    resolved_generated_at = generated_at
    if resolved_generated_at is None and run_result is not None:
        candidate = _first_field(
            run_result,
            ("finalized_at", "finished_at", "completed_at", "generated_at"),
            None,
        )
        if isinstance(candidate, datetime):
            resolved_generated_at = candidate
    if resolved_generated_at is None:
        resolved_generated_at = datetime.now(UTC)

    resolved_project_root = _optional_absolute_path(project_root, "project_root")
    if resolved_project_root is None and run_result is not None:
        resolved_project_root = _extract_project_root(run_result)

    return _WriterContext(
        file_results=results,
        destination=resolved_destination,
        run_root=resolved_run_root,
        project_root=resolved_project_root,
        run_id=_single_line(resolved_run_id, "run_id"),
        project_id=_single_line(resolved_project_id, "project_id"),
        generated_at=_utc(resolved_generated_at, "generated_at"),
    )


_MISSING: Final = object()


def _extract_run_root(run_result: ResultLike) -> Path | None:
    direct = _first_field(run_result, ("run_root", "run_directory", "output_root"), None)
    if direct is not None:
        return _absolute_path(direct, "run_root")
    paths = _first_field(run_result, ("paths", "run_paths"), None)
    if paths is None:
        return None
    value = _first_field(paths, ("run_root", "root", "run_directory"), None)
    return _absolute_path(value, "run_root") if value is not None else None


def _extract_project_root(run_result: ResultLike) -> Path | None:
    direct = _first_field(run_result, ("project_root", "active_project_root"), None)
    if direct is not None:
        return _absolute_path(direct, "project_root")
    project = _first_field(run_result, ("project", "project_identity", "project_context"), None)
    if project is not None:
        value = _first_field(project, ("root", "project_root", "active_project_root"), None)
        if value is not None:
            return _absolute_path(value, "project_root")
    paths = _first_field(run_result, ("paths", "run_paths"), None)
    if paths is not None:
        value = _first_field(paths, ("project_root", "active_project_root"), None)
        if value is not None:
            return _absolute_path(value, "project_root")
    return None


def _extract_destination(run_result: ResultLike) -> Path | None:
    direct = _first_field(
        run_result,
        ("all_scan_logs_path", "all_scan_logs"),
        None,
    )
    if direct is not None:
        return _absolute_path(direct, "destination")
    paths = _first_field(run_result, ("paths", "run_paths"), None)
    if paths is None:
        return None
    value = _first_field(
        paths,
        ("all_scan_logs_path", "all_scan_logs"),
        None,
    )
    return _absolute_path(value, "destination") if value is not None else None


def _infer_run_root(destination: Path) -> Path:
    parent = destination.parent
    if parent.name.casefold() == "raw":
        return parent.parent
    raise ValueError("run_root cannot be inferred from destination")


def _result_subject(
    result: ResultLike,
    index: int,
    project_root: Path | None,
) -> str:
    relative = _first_field(
        result,
        ("project_relative_path", "relative_path", "subject_id", "subject"),
        None,
    )
    if relative is not None:
        return _canonical_subject(
            os.fspath(relative) if isinstance(relative, os.PathLike) else str(relative)
        )

    value = _first_field(result, ("file_path", "source_path", "path"), None)
    if value is None:
        raise _contract_error(
            f"file result at index {index} has no stable subject identity",
            subject=None,
        )
    text = os.fspath(value) if isinstance(value, os.PathLike) else str(value)
    path = Path(text)
    if path.is_absolute():
        if project_root is None:
            raise _contract_error(
                "absolute file identity requires project_root for canonical projection",
                subject=str(path),
                path=path,
            )
        try:
            text = path.relative_to(project_root).as_posix()
        except ValueError as exc:
            raise _contract_error(
                "file identity is outside the active project root",
                subject=str(path),
                path=path,
            ) from exc
    return _canonical_subject(text)


def _result_required(result: ResultLike) -> bool:
    value = _first_field(result, ("required", "is_required", "gating"), True)
    if not isinstance(value, bool):
        raise TypeError("file-result required flag must be a bool")
    return value


def _result_status(result: ResultLike) -> str:
    value = _first_field(
        result,
        ("scan_status", "status", "validation_status"),
        "UNKNOWN",
    )
    raw = getattr(value, "value", value)
    text = str(raw).strip()
    return _single_line(text or "UNKNOWN", "status")


def _aggregate_status(value: object) -> ScanLogAggregateStatus:
    if isinstance(value, ScanLogAggregateStatus):
        return value
    if not isinstance(value, str):
        raise TypeError("status must be a ScanLogAggregateStatus or string")
    try:
        return ScanLogAggregateStatus(value)
    except ValueError as exc:
        raise ValueError("status must be a canonical ScanLogAggregateStatus") from exc


def _pathlike_or_none(value: object, field_name: str) -> PathLike | None:
    if value is None:
        return None
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError(f"{field_name} must be path-like or None")
    return value


def _result_scan_log_path(result: ResultLike) -> PathLike | None:
    direct = _first_field(
        result,
        ("scan_log_path", "scan_log", "scan_evidence_path"),
        None,
    )
    if direct is not None:
        return _pathlike_or_none(direct, "scan log path")
    scan = _first_field(result, ("scan_result", "scan_summary"), None)
    if scan is None:
        return None
    return _pathlike_or_none(
        _first_field(
            scan,
            ("scan_log_path", "log_path", "evidence_path"),
            None,
        ),
        "scan log path",
    )


def _missing_reason(result: ResultLike, fallback: str) -> str:
    value = _first_field(
        result,
        (
            "scan_error_message",
            "primary_message",
            "message",
            "skip_reason",
        ),
        None,
    )
    text = str(getattr(value, "value", value)).strip() if value is not None else ""
    return _single_line(text or fallback, "missing_reason")


def _render_section(section: ScanLogSection) -> str:
    path_text = section.display_path or (
        str(section.log_path) if section.log_path is not None else _NULL_TEXT
    )
    prefix = (
        "\n".join(
            (
                _SECTION_RULE,
                "BEGIN SCAN LOG",
                f"subject: {section.subject}",
                f"path: {path_text}",
                f"status: {section.status}",
            )
        )
        + "\n"
    )
    if not section.included:
        return (
            prefix
            + f"reason: {section.missing_reason}\n"
            + "END SCAN LOG\n"
            + _SECTION_RULE
            + "\n\n"
        )

    content = section.content or ""
    separator = "" if not content or content.endswith(("\n", "\r")) else "\n"
    return (
        prefix
        + f"sha256: {section.sha256}\n"
        + _SECTION_INNER_RULE
        + "\n"
        + content
        + separator
        + _SECTION_INNER_RULE
        + "\nEND SCAN LOG\n"
        + _SECTION_RULE
        + "\n\n"
    )


def _first_field(
    obj: ResultLike,
    names: Sequence[str],
    default: Any,
) -> Any:
    for name in names:
        if isinstance(obj, Mapping):
            if name in obj:
                return obj[name]
        elif hasattr(obj, name):
            return getattr(obj, name)
    return default


def _text_field(obj: ResultLike, names: Sequence[str]) -> str | None:
    value = _first_field(obj, names, None)
    if value is None:
        return None
    raw = getattr(value, "value", value)
    text = str(raw).strip()
    return text or None


def _canonical_subject(value: str) -> str:
    text = _single_line(value, "subject").replace("\\", "/")
    pure = PurePosixPath(text)
    if pure.is_absolute():
        raise ValueError("subject must be a project-relative path")
    parts = pure.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError("subject must be a normalized project-relative path")
    return pure.as_posix()


def _subject_sort_key(value: str) -> str:
    return _canonical_subject(value).casefold()


def _canonical_display_path(value: str) -> str:
    text = _single_line(value, "display_path").replace("\\", "/")
    pure = PurePosixPath(text)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError("display_path must be a safe relative path")
    return pure.as_posix()


def _display_path(path: Path, run_root: Path | None) -> str:
    if run_root is not None and _is_within(path, run_root):
        return path.relative_to(run_root).as_posix()
    return path.as_posix()


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain a NUL character")
    return value


def _single_line(value: object, field_name: str) -> str:
    text = _required_text(value, field_name).strip()
    if "\n" in text or "\r" in text:
        raise ValueError(f"{field_name} must be a single line")
    return text


def _absolute_path(value: PathLike, field_name: str) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError(f"{field_name} must be path-like")
    text = os.fspath(value)
    if "\x00" in text:
        raise ValueError(f"{field_name} must not contain a NUL character")
    path = Path(os.path.normpath(text))
    if not path.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return path


def _optional_absolute_path(value: PathLike | None, field_name: str) -> Path | None:
    return None if value is None else _absolute_path(value, field_name)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _is_within(path: Path, root: Path) -> bool:
    candidate = _absolute_path(path, "path")
    boundary = _absolute_path(root, "root")
    return candidate == boundary or candidate.is_relative_to(boundary)


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _rfc3339_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _issue_key(issue: ScanLogAggregateIssue) -> tuple[int, str, str, str]:
    return (
        0 if issue.required else 1,
        _subject_sort_key(issue.subject),
        issue.code,
        issue.message,
    )


def _contract_error(
    message: str,
    *,
    subject: str | None,
    path: Path | None = None,
) -> ContractViolationError:
    return ContractViolationError(
        message,
        code="GF-WB-REPORT-LOG-001",
        stage="reporting",
        operation="write-all-scan-logs",
        subject=subject,
        evidence_paths=(() if path is None else (str(path),)),
    )
