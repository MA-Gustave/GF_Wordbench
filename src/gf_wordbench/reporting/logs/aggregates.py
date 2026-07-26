"""Deterministic aggregate-log rendering and persistence."""

from __future__ import annotations

import codecs
import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from typing import Final

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.kernel.serialization import format_rfc3339_utc

UTF8: Final[str] = "utf-8"
ALL_SCAN_LOGS_RELATIVE_PATH: Final[PurePosixPath] = PurePosixPath(
    "raw/ALL_SCAN_LOGS.TXT"
)
ALL_LOGS_RELATIVE_PATH: Final[PurePosixPath] = PurePosixPath("raw/ALL_LOGS.TXT")
_SECTION_RULE: Final[str] = "=" * 80
_CONTENT_RULE: Final[str] = "-" * 80
_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
_ROLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*$")
_FORBIDDEN_OPERATION_PATHS: Final[frozenset[PurePosixPath]] = frozenset(
    {
        PurePosixPath("summary.json"),
        PurePosixPath("summary.md"),
        PurePosixPath("AI_READY.md"),
        PurePosixPath("top_errors.txt"),
        PurePosixPath("manifest.json"),
    }
)


@unique
class AggregateKind(StrEnum):
    SCAN = "scan"
    OPERATION = "operation"


@unique
class AggregateSourceCategory(StrEnum):
    LIFECYCLE = "lifecycle"
    VERSION = "version"
    COMPILE = "compile"
    PGF = "pgf"
    SCENARIO = "scenario"
    OTHER = "other"
    SCAN = "scan"


@unique
class AggregateStream(StrEnum):
    NONE = "none"
    STDOUT = "stdout"
    STDERR = "stderr"


@dataclass(frozen=True, slots=True)
class AggregateRunMetadata:
    run_id: str
    project_id: str
    generated_at: datetime
    mode: str | None = None

    def __post_init__(self) -> None:
        _require_token(self.run_id, field="run_id")
        _require_token(self.project_id, field="project_id")
        if not isinstance(self.generated_at, datetime):
            raise TypeError("generated_at must be a datetime")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.mode is not None:
            _require_token(self.mode, field="mode")


@dataclass(frozen=True, slots=True)
class AggregateLogSource:
    subject: str
    role: str
    category: AggregateSourceCategory
    sequence: int
    relative_path: PurePosixPath | None
    source_path: Path | None
    stream: AggregateStream = AggregateStream.NONE
    status: str = "OK"
    required: bool = True
    missing_reason: str | None = None
    encoding: str = UTF8

    def __post_init__(self) -> None:
        _require_line(self.subject, field="subject")
        if _ROLE_PATTERN.fullmatch(self.role) is None:
            raise ValueError("role must use lowercase snake_case")
        if not isinstance(self.category, AggregateSourceCategory):
            raise TypeError("category must be AggregateSourceCategory")
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        if not isinstance(self.stream, AggregateStream):
            raise TypeError("stream must be AggregateStream")
        _require_token(self.status, field="status")
        if type(self.required) is not bool:
            raise TypeError("required must be a bool")
        encoding = codecs.lookup(self.encoding).name
        if encoding != UTF8:
            raise ValueError("aggregate sources must use UTF-8")
        object.__setattr__(self, "encoding", UTF8)

        if self.relative_path is None or self.source_path is None:
            if self.relative_path is not None or self.source_path is not None:
                raise ValueError(
                    "relative_path and source_path must both be present or both be absent"
                )
            if self.missing_reason is None:
                raise ValueError("missing sources require missing_reason")
            _require_line(self.missing_reason, field="missing_reason")
            if self.status.upper() != "MISSING":
                raise ValueError("a source without a path must use status MISSING")
        else:
            relative_path = _require_relative_path(
                self.relative_path,
                field="relative_path",
            )
            if not isinstance(self.source_path, Path):
                raise TypeError("source_path must be a pathlib.Path")
            if self.missing_reason is not None:
                raise ValueError("present sources must not define missing_reason")
            object.__setattr__(self, "relative_path", relative_path)

        if self.category is AggregateSourceCategory.SCAN:
            if self.stream is not AggregateStream.NONE:
                raise ValueError("scan sources must not declare a process stream")
        elif self.stream is AggregateStream.NONE and self.category in {
            AggregateSourceCategory.VERSION,
            AggregateSourceCategory.COMPILE,
            AggregateSourceCategory.PGF,
            AggregateSourceCategory.SCENARIO,
        }:
            raise ValueError("process sources must declare stdout or stderr")


@dataclass(frozen=True, slots=True)
class AggregateRenderResult:
    kind: AggregateKind
    text: str
    source_count: int
    included_sections: int
    missing_sections: int
    boundary_escapes: int

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AggregateKind):
            raise TypeError("kind must be AggregateKind")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        for field_name in (
            "source_count",
            "included_sections",
            "missing_sections",
            "boundary_escapes",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class AggregateWriteResult:
    kind: AggregateKind
    path: Path
    source_count: int
    included_sections: int
    missing_sections: int
    boundary_escapes: int
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AggregateKind):
            raise TypeError("kind must be AggregateKind")
        if not isinstance(self.path, Path):
            raise TypeError("path must be a pathlib.Path")
        for field_name in (
            "source_count",
            "included_sections",
            "missing_sections",
            "boundary_escapes",
            "size_bytes",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            raise ValueError("sha256 must be a lowercase SHA-256 digest")


def render_all_scan_logs(
    metadata: AggregateRunMetadata,
    sources: Iterable[AggregateLogSource],
    *,
    run_root: Path,
) -> AggregateRenderResult:
    metadata = _require_metadata(metadata)
    root = _require_run_root(run_root)
    prepared = _prepare_sources(
        sources,
        kind=AggregateKind.SCAN,
        run_root=root,
        destination=None,
    )
    rendered_sections: list[str] = []
    missing_sections = 0
    boundary_escapes = 0

    for source in prepared:
        section, missing, escapes = _render_scan_section(source, root)
        rendered_sections.append(section)
        missing_sections += int(missing)
        boundary_escapes += escapes

    header = "\n".join(
        (
            "GF WORDBENCH — ALL SCAN LOGS",
            f"Run ID: {metadata.run_id}",
            f"Project: {metadata.project_id}",
            f"Generated: {format_rfc3339_utc(metadata.generated_at)}",
            f"Source count: {len(prepared)}",
            f"Included sections: {len(rendered_sections)}",
            "Authoritative source: individual files under raw/scan/",
        )
    )
    text = _join_document(header, rendered_sections)
    return AggregateRenderResult(
        kind=AggregateKind.SCAN,
        text=text,
        source_count=len(prepared),
        included_sections=len(rendered_sections),
        missing_sections=missing_sections,
        boundary_escapes=boundary_escapes,
    )


def render_all_logs(
    metadata: AggregateRunMetadata,
    sources: Iterable[AggregateLogSource],
    *,
    run_root: Path,
    scan_section_count: int = 0,
    scan_aggregate_path: PurePosixPath = ALL_SCAN_LOGS_RELATIVE_PATH,
) -> AggregateRenderResult:
    metadata = _require_metadata(metadata)
    if metadata.mode is None:
        raise ValueError("operation aggregate metadata requires mode")
    if type(scan_section_count) is not int or scan_section_count < 0:
        raise ValueError("scan_section_count must be a non-negative integer")
    scan_path = _require_relative_path(
        scan_aggregate_path,
        field="scan_aggregate_path",
    )
    root = _require_run_root(run_root)
    prepared = _prepare_sources(
        sources,
        kind=AggregateKind.OPERATION,
        run_root=root,
        destination=None,
    )
    rendered_sections: list[str] = []
    missing_sections = 0
    boundary_escapes = 0

    for source in prepared:
        section, missing, escapes = _render_operation_section(source, root)
        rendered_sections.append(section)
        missing_sections += int(missing)
        boundary_escapes += escapes

    rendered_sections.append(
        "\n".join(
            (
                "SCAN LOGS",
                f"Aggregate: {scan_path.as_posix()}",
                "Individual directory: raw/scan/",
                f"Sections: {scan_section_count}",
            )
        )
    )
    header = "\n".join(
        (
            "GF WORDBENCH — ALL OPERATION LOGS",
            f"Run ID: {metadata.run_id}",
            f"Project: {metadata.project_id}",
            f"Mode: {metadata.mode}",
            f"Generated: {format_rfc3339_utc(metadata.generated_at)}",
            "Authoritative source: individual files under raw/",
            "Reports: see ./summary.json, ./summary.md, ./AI_READY.md",
            f"Scan aggregate: {scan_path.name}",
        )
    )
    text = _join_document(header, rendered_sections)
    return AggregateRenderResult(
        kind=AggregateKind.OPERATION,
        text=text,
        source_count=len(prepared),
        included_sections=len(prepared),
        missing_sections=missing_sections,
        boundary_escapes=boundary_escapes,
    )


def write_all_scan_logs(
    destination: Path,
    metadata: AggregateRunMetadata,
    sources: Iterable[AggregateLogSource],
    *,
    run_root: Path,
    allow_replace: bool = False,
) -> AggregateWriteResult:
    root = _require_run_root(run_root)
    target = _require_destination(destination, root, allow_replace=allow_replace)
    rendered = render_all_scan_logs(metadata, sources, run_root=root)
    return _persist_rendered(target, root, rendered)


def write_all_logs(
    destination: Path,
    metadata: AggregateRunMetadata,
    sources: Iterable[AggregateLogSource],
    *,
    run_root: Path,
    scan_section_count: int = 0,
    scan_aggregate_path: PurePosixPath = ALL_SCAN_LOGS_RELATIVE_PATH,
    allow_replace: bool = False,
) -> AggregateWriteResult:
    root = _require_run_root(run_root)
    target = _require_destination(destination, root, allow_replace=allow_replace)
    rendered = render_all_logs(
        metadata,
        sources,
        run_root=root,
        scan_section_count=scan_section_count,
        scan_aggregate_path=scan_aggregate_path,
    )
    return _persist_rendered(target, root, rendered)


def _persist_rendered(
    destination: Path,
    run_root: Path,
    rendered: AggregateRenderResult,
) -> AggregateWriteResult:
    expected = rendered.text.encode(UTF8)
    expected_hash = hashlib.sha256(expected).hexdigest()
    written = atomic_write_text(
        destination,
        rendered.text,
        encoding=UTF8,
        newline="\n",
        create_parents=True,
        root=run_root,
        role=(
            "all scan logs aggregate"
            if rendered.kind is AggregateKind.SCAN
            else "all operation logs aggregate"
        ),
    )
    observed = written.read_bytes()
    observed_hash = hashlib.sha256(observed).hexdigest()
    if observed != expected or observed_hash != expected_hash:
        raise OSError(f"aggregate verification failed: {written}")
    return AggregateWriteResult(
        kind=rendered.kind,
        path=written,
        source_count=rendered.source_count,
        included_sections=rendered.included_sections,
        missing_sections=rendered.missing_sections,
        boundary_escapes=rendered.boundary_escapes,
        size_bytes=len(observed),
        sha256=observed_hash,
    )


def _prepare_sources(
    sources: Iterable[AggregateLogSource],
    *,
    kind: AggregateKind,
    run_root: Path,
    destination: Path | None,
) -> tuple[AggregateLogSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise TypeError("sources must be an iterable of AggregateLogSource")
    prepared = tuple(sources)
    seen_paths: set[PurePosixPath] = set()
    seen_identity: set[tuple[str, str, int, str]] = set()

    for source in prepared:
        if not isinstance(source, AggregateLogSource):
            raise TypeError("sources must contain AggregateLogSource values")
        if kind is AggregateKind.SCAN:
            if source.category is not AggregateSourceCategory.SCAN:
                raise ValueError("scan aggregates accept only scan sources")
        elif source.category is AggregateSourceCategory.SCAN:
            raise ValueError("operation aggregates must reference scans, not embed them")

        identity = (
            source.category.value,
            source.subject,
            source.sequence,
            source.stream.value,
        )
        if identity in seen_identity:
            raise ValueError(f"duplicate aggregate source identity: {identity!r}")
        seen_identity.add(identity)

        if source.relative_path is not None:
            if source.relative_path in seen_paths:
                raise ValueError(
                    f"duplicate aggregate source path: {source.relative_path.as_posix()}"
                )
            seen_paths.add(source.relative_path)
            _validate_source_location(source, run_root, destination)
            if kind is AggregateKind.OPERATION:
                _reject_report_source(source.relative_path)

    if kind is AggregateKind.SCAN:
        return tuple(
            sorted(
                prepared,
                key=lambda item: (
                    item.sequence,
                    item.subject.casefold(),
                    item.subject,
                    "" if item.relative_path is None else item.relative_path.as_posix(),
                ),
            )
        )

    return tuple(sorted(prepared, key=_operation_sort_key))


def _operation_sort_key(source: AggregateLogSource) -> tuple[object, ...]:
    category_rank = {
        AggregateSourceCategory.LIFECYCLE: 0,
        AggregateSourceCategory.VERSION: 1,
        AggregateSourceCategory.COMPILE: 2,
        AggregateSourceCategory.PGF: 2,
        AggregateSourceCategory.SCENARIO: 3,
        AggregateSourceCategory.OTHER: 4,
    }
    stream_rank = {
        AggregateStream.NONE: 0,
        AggregateStream.STDOUT: 0,
        AggregateStream.STDERR: 1,
    }
    path = "" if source.relative_path is None else source.relative_path.as_posix()
    return (
        category_rank[source.category],
        source.sequence,
        stream_rank[source.stream],
        source.subject.casefold(),
        source.subject,
        source.role,
        path,
    )


def _render_scan_section(
    source: AggregateLogSource,
    run_root: Path,
) -> tuple[str, bool, int]:
    if source.source_path is None or source.relative_path is None:
        lines = (
            _SECTION_RULE,
            "BEGIN SCAN LOG",
            f"subject: {source.subject}",
            "path: null",
            "status: MISSING",
            f"reason: {source.missing_reason}",
            "END SCAN LOG",
            _SECTION_RULE,
        )
        return "\n".join(lines), True, 0

    raw, digest = _read_source(source, run_root)
    content, escapes = _aggregate_content(raw)
    lines = (
        _SECTION_RULE,
        "BEGIN SCAN LOG",
        f"subject: {source.subject}",
        f"path: {source.relative_path.as_posix()}",
        f"status: {source.status.upper()}",
        f"sha256: {digest}",
        _CONTENT_RULE,
        content,
        _CONTENT_RULE,
        "END SCAN LOG",
        _SECTION_RULE,
    )
    return "\n".join(lines), False, escapes


def _render_operation_section(
    source: AggregateLogSource,
    run_root: Path,
) -> tuple[str, bool, int]:
    if source.source_path is None or source.relative_path is None:
        missing_path = "null"
        body = f"<MISSING EVIDENCE: {source.subject}>"
        lines = (
            _SECTION_RULE,
            "BEGIN LOG",
            f"role: {source.role}",
            f"subject: {source.subject}",
            f"path: {missing_path}",
            "encoding: UTF-8",
            "size_bytes: 0",
            "sha256: missing",
            f"status: {source.status.upper()}",
            f"reason: {source.missing_reason}",
            _CONTENT_RULE,
            body,
            _CONTENT_RULE,
            "END LOG",
            _SECTION_RULE,
        )
        return "\n".join(lines), True, 0

    raw, digest = _read_source(source, run_root)
    content, escapes = _aggregate_content(raw)
    lines = (
        _SECTION_RULE,
        "BEGIN LOG",
        f"role: {source.role}",
        f"subject: {source.subject}",
        f"path: {source.relative_path.as_posix()}",
        "encoding: UTF-8",
        f"size_bytes: {len(raw)}",
        f"sha256: {digest}",
        _CONTENT_RULE,
        content,
        _CONTENT_RULE,
        "END LOG",
        _SECTION_RULE,
    )
    return "\n".join(lines), False, escapes


def _read_source(
    source: AggregateLogSource,
    run_root: Path,
) -> tuple[bytes, str]:
    if source.source_path is None or source.relative_path is None:
        raise ValueError("source path is missing")
    _validate_source_location(source, run_root, None)
    path = source.source_path.resolve(strict=True)
    if not path.is_file():
        raise OSError(f"aggregate source is not a regular file: {path}")
    raw = path.read_bytes()
    raw.decode(UTF8, errors="strict")
    return raw, hashlib.sha256(raw).hexdigest()


def _aggregate_content(raw: bytes) -> tuple[str, int]:
    text = raw.decode(UTF8, errors="strict")
    if not text:
        return "<EMPTY STREAM>", 0
    normalized = text.rstrip("\r\n")
    if not normalized:
        return "<EMPTY STREAM>", 0
    escaped, count = _escape_boundaries(normalized)
    return escaped, count


def _escape_boundaries(text: str) -> tuple[str, int]:
    collision_lines = {
        _SECTION_RULE,
        _CONTENT_RULE,
        "BEGIN LOG",
        "END LOG",
        "BEGIN SCAN LOG",
        "END SCAN LOG",
        "SCAN LOGS",
    }
    output: list[str] = []
    count = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body) :]
        if body in collision_lines:
            body = "\\" + body
            count += 1
        output.append(body + ending)
    if not output:
        return text, count
    return "".join(output), count


def _join_document(header: str, sections: list[str]) -> str:
    parts = [header, *sections]
    return "\n\n".join(part.rstrip("\r\n") for part in parts) + "\n"


def _validate_source_location(
    source: AggregateLogSource,
    run_root: Path,
    destination: Path | None,
) -> None:
    if source.source_path is None or source.relative_path is None:
        return
    lexical = run_root / Path(source.relative_path.as_posix())
    expected = lexical.resolve(strict=False)
    observed = source.source_path.resolve(strict=False)
    if observed != expected:
        raise ValueError(
            "source_path does not match run_root plus relative_path: "
            f"{source.relative_path.as_posix()}"
        )
    _require_contained(observed, run_root, field="source_path")
    if destination is not None and observed == destination.resolve(strict=False):
        raise ValueError("an aggregate cannot include itself")


def _reject_report_source(relative_path: PurePosixPath) -> None:
    if relative_path in _FORBIDDEN_OPERATION_PATHS:
        raise ValueError(
            f"operation aggregate must not embed report {relative_path.as_posix()}"
        )
    if relative_path.parts and relative_path.parts[0] == "details":
        raise ValueError("operation aggregate must not embed details artifacts")
    if relative_path == ALL_SCAN_LOGS_RELATIVE_PATH:
        raise ValueError("operation aggregate must reference, not embed, ALL_SCAN_LOGS")
    if relative_path == ALL_LOGS_RELATIVE_PATH:
        raise ValueError("operation aggregate must not include itself")


def _require_metadata(value: object) -> AggregateRunMetadata:
    if not isinstance(value, AggregateRunMetadata):
        raise TypeError("metadata must be AggregateRunMetadata")
    return value


def _require_run_root(value: object) -> Path:
    if not isinstance(value, Path):
        raise TypeError("run_root must be a pathlib.Path")
    root = value.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return root


def _require_destination(
    value: object,
    run_root: Path,
    *,
    allow_replace: bool,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError("destination must be a pathlib.Path")
    if type(allow_replace) is not bool:
        raise TypeError("allow_replace must be a bool")
    destination = value.resolve(strict=False)
    _require_contained(destination, run_root, field="destination")
    if destination.exists():
        if destination.is_dir():
            raise IsADirectoryError(destination)
        if not allow_replace:
            raise FileExistsError(destination)
    return destination


def _require_contained(path: Path, root: Path, *, field: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field} escapes the run root: {path}") from exc


def _require_relative_path(value: object, *, field: str) -> PurePosixPath:
    if isinstance(value, PurePosixPath):
        path = value
    elif isinstance(value, str):
        path = PurePosixPath(value)
    else:
        raise TypeError(f"{field} must be PurePosixPath or string")
    rendered = path.as_posix()
    if not rendered or rendered == ".":
        raise ValueError(f"{field} must not be empty")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field} must be a normalized relative POSIX path")
    if "\\" in rendered or "\x00" in rendered:
        raise ValueError(f"{field} must use safe POSIX path syntax")
    return path


def _require_token(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a portable token")
    return value


def _require_line(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise ValueError(f"{field} must be one NUL-free line")
    return value


__all__ = (
    "ALL_LOGS_RELATIVE_PATH",
    "ALL_SCAN_LOGS_RELATIVE_PATH",
    "AggregateKind",
    "AggregateLogSource",
    "AggregateRenderResult",
    "AggregateRunMetadata",
    "AggregateSourceCategory",
    "AggregateStream",
    "AggregateWriteResult",
    "render_all_logs",
    "render_all_scan_logs",
    "write_all_logs",
    "write_all_scan_logs",
)
