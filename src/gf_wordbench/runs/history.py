"""Read-only run-history discovery and previous-run selection."""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from typing import Final, TypeAlias

from gf_wordbench.kernel.ids import (
    ProjectId,
    RunId,
    validate_project_id,
    validate_run_id,
)
from gf_wordbench.kernel.statuses import OverallStatus, ValidationMode
SUMMARY_FILENAME: Final = "summary.json"
MANIFEST_FILENAME: Final = "manifest.json"
_RUN_DIR_RE: Final = re.compile(
    r"^run_(?P<id>[0-9]{8}_[0-9]{6}(?:_(?:0[2-9]|[1-9][0-9]+))?)$"
)
_RUN_LIKE_RE: Final = re.compile(r"^run_.+$", re.IGNORECASE)
@unique
class RunHistoryState(StrEnum):
    FINALIZED = "finalized"
    INCOMPLETE = "incomplete"
    CORRUPT = "corrupt"
    LEGACY = "legacy"
    UNKNOWN = "unknown"
@dataclass(frozen=True, slots=True)
class RunHistoryRecord:
    run_id: RunId
    project_id: ProjectId
    mode: ValidationMode
    started_at: datetime
    finished_at: datetime
    overall_status: OverallStatus
    target_file: str | None = None
    schema_id: str | None = None
    schema_version: str | None = None
    manifest_relative_path: PurePosixPath | str | None = MANIFEST_FILENAME
    complete: bool = True
    legacy: bool = False
    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", validate_run_id(self.run_id))
        object.__setattr__(self, "project_id", validate_project_id(self.project_id))
        if not isinstance(self.mode, ValidationMode):
            object.__setattr__(self, "mode", ValidationMode(self.mode))
        if not isinstance(self.overall_status, OverallStatus):
            object.__setattr__(
                self,
                "overall_status",
                OverallStatus(self.overall_status),
            )
        started = _utc(self.started_at, "started_at")
        finished = _utc(self.finished_at, "finished_at")
        if finished < started:
            raise ValueError("finished_at must not precede started_at")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "finished_at", finished)
        if self.target_file is not None:
            object.__setattr__(
                self,
                "target_file",
                _project_relative_path(self.target_file),
            )
        if self.manifest_relative_path is not None:
            object.__setattr__(
                self,
                "manifest_relative_path",
                _run_relative_path(self.manifest_relative_path),
            )
        if type(self.complete) is not bool or type(self.legacy) is not bool:
            raise TypeError("complete and legacy must be bools")

SummaryReader: TypeAlias = Callable[[Path], RunHistoryRecord]
ManifestVerifier: TypeAlias = Callable[[Path, Path, RunId], bool]

@dataclass(frozen=True, slots=True)
class RunHistoryEntry:
    run_dir: Path
    state: RunHistoryState
    run_id: RunId | None = None
    summary_path: Path | None = None
    manifest_path: Path | None = None
    record: RunHistoryRecord | None = None
    manifest_verified: bool | None = None
    previous_run_eligible: bool = False
    issues: tuple[str, ...] = ()

    @property
    def project_id(self) -> ProjectId | None:
        return None if self.record is None else self.record.project_id

    @property
    def mode(self) -> ValidationMode | None:
        return None if self.record is None else self.record.mode

    @property
    def target_file(self) -> str | None:
        return None if self.record is None else self.record.target_file

    @property
    def finished_at(self) -> datetime | None:
        return None if self.record is None else self.record.finished_at

    @property
    def overall_status(self) -> OverallStatus | None:
        return None if self.record is None else self.record.overall_status

    @property
    def is_finalized(self) -> bool:
        return self.state is RunHistoryState.FINALIZED

@dataclass(frozen=True, slots=True)
class RunHistoryQuery:
    output_root: Path
    current_run_dir: Path | None = None
    current_run_id: RunId | str | None = None
    project_id: ProjectId | str | None = None
    mode: ValidationMode | str | None = None
    target_file: str | None = None
    not_after: datetime | None = None
    allow_legacy: bool = False
    require_manifest_verification: bool = True
    include_incomplete: bool = True
    include_corrupt: bool = True
    include_unknown: bool = False
    max_entries: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "output_root",
            _absolute_directory(self.output_root, "output_root"),
        )
        if self.current_run_dir is not None:
            object.__setattr__(
                self,
                "current_run_dir",
                _absolute_path(self.current_run_dir, "current_run_dir"),
            )
        if self.current_run_id is not None:
            object.__setattr__(
                self,
                "current_run_id",
                validate_run_id(self.current_run_id),
            )
        if self.project_id is not None:
            object.__setattr__(
                self,
                "project_id",
                validate_project_id(self.project_id),
            )
        if self.mode is not None and not isinstance(self.mode, ValidationMode):
            object.__setattr__(self, "mode", ValidationMode(self.mode))
        if self.target_file is not None:
            object.__setattr__(
                self,
                "target_file",
                _project_relative_path(self.target_file),
            )
        if self.not_after is not None:
            object.__setattr__(
                self,
                "not_after",
                _utc(self.not_after, "not_after"),
            )
        for name in (
            "allow_legacy",
            "require_manifest_verification",
            "include_incomplete",
            "include_corrupt",
            "include_unknown",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")
        if self.max_entries is not None and (
            type(self.max_entries) is not int or self.max_entries <= 0
        ):
            raise ValueError("max_entries must be a positive integer or None")

@dataclass(frozen=True, slots=True)
class RunHistoryResult:
    entries: tuple[RunHistoryEntry, ...]
    ignored: tuple[str, ...] = ()

    @property
    def eligible_entries(self) -> tuple[RunHistoryEntry, ...]:
        return tuple(entry for entry in self.entries if entry.previous_run_eligible)

    @property
    def previous_run(self) -> RunHistoryEntry | None:
        eligible = self.eligible_entries
        return eligible[0] if eligible else None

def discover_run_history(
    query: RunHistoryQuery,
    *,
    summary_reader: SummaryReader,
    manifest_verifier: ManifestVerifier | None = None,
) -> RunHistoryResult:
    if not isinstance(query, RunHistoryQuery):
        raise TypeError("query must be a RunHistoryQuery")
    if not callable(summary_reader):
        raise TypeError("summary_reader must be callable")
    if manifest_verifier is not None and not callable(manifest_verifier):
        raise TypeError("manifest_verifier must be callable")

    entries: list[RunHistoryEntry] = []
    ignored: list[str] = []
    children = sorted(
        query.output_root.iterdir(),
        key=lambda path: path.name.casefold(),
    )

    for child in children:
        if not _RUN_LIKE_RE.fullmatch(child.name):
            continue
        entry = inspect_run_directory(
            child,
            output_root=query.output_root,
            summary_reader=summary_reader,
            manifest_verifier=manifest_verifier,
        )
        if _is_current(entry, query):
            ignored.append(f"{child}: current run excluded")
            continue
        entry = _with_eligibility(entry, query)
        if _include(entry, query):
            entries.append(entry)
        else:
            ignored.extend(entry.issues)

    entries.sort(key=_sort_key, reverse=True)
    if query.max_entries is not None:
        entries = entries[: query.max_entries]
    return RunHistoryResult(tuple(entries), tuple(ignored))

def select_previous_run(
    query: RunHistoryQuery,
    *,
    summary_reader: SummaryReader,
    manifest_verifier: ManifestVerifier | None = None,
) -> RunHistoryEntry | None:
    return discover_run_history(
        query,
        summary_reader=summary_reader,
        manifest_verifier=manifest_verifier,
    ).previous_run

def inspect_run_directory(
    run_dir: Path,
    *,
    output_root: Path,
    summary_reader: SummaryReader,
    manifest_verifier: ManifestVerifier | None = None,
) -> RunHistoryEntry:
    root = _absolute_directory(output_root, "output_root")
    path = _absolute_path(run_dir, "run_dir")

    if _link(path) or not path.is_dir() or not _immediate_child(path, root):
        return _entry(path, RunHistoryState.UNKNOWN, "unsafe run directory")

    directory_id = _directory_run_id(path)
    legacy_name = directory_id is None
    issues = (
        (f"{path}: non-canonical run directory name",)
        if legacy_name
        else ()
    )
    summary_path = path / SUMMARY_FILENAME
    if _link(summary_path) or not summary_path.is_file():
        return RunHistoryEntry(
            run_dir=path,
            state=RunHistoryState.INCOMPLETE,
            run_id=directory_id,
            summary_path=summary_path,
            issues=(*issues, f"{summary_path}: missing or unsafe summary"),
        )

    try:
        record = summary_reader(summary_path)
        if not isinstance(record, RunHistoryRecord):
            raise TypeError("summary_reader returned an invalid record")
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        manifest = path / MANIFEST_FILENAME
        state = (
            RunHistoryState.CORRUPT
            if manifest.exists()
            else RunHistoryState.INCOMPLETE
        )
        return RunHistoryEntry(
            run_dir=path,
            state=state,
            run_id=directory_id,
            summary_path=summary_path,
            manifest_path=manifest if manifest.exists() else None,
            issues=(
                *issues,
                f"{summary_path}: summary rejected ({type(exc).__name__})",
            ),
        )

    if directory_id is not None and record.run_id != directory_id:
        return RunHistoryEntry(
            run_dir=path,
            state=RunHistoryState.CORRUPT,
            run_id=directory_id,
            summary_path=summary_path,
            record=record,
            issues=(
                *issues,
                f"{summary_path}: directory and summary run IDs disagree",
            ),
        )

    entry = RunHistoryEntry(
        run_dir=path,
        state=RunHistoryState.LEGACY if record.legacy else RunHistoryState.UNKNOWN,
        run_id=record.run_id,
        summary_path=summary_path,
        record=record,
        issues=issues,
    )
    if not record.complete:
        return replace(
            entry,
            state=RunHistoryState.INCOMPLETE,
            issues=(*entry.issues, f"{summary_path}: summary is incomplete"),
        )
    if record.legacy:
        return entry

    manifest_path = _manifest_path(path, record)
    if manifest_path is None or _link(manifest_path) or not manifest_path.is_file():
        return replace(
            entry,
            state=RunHistoryState.INCOMPLETE,
            manifest_path=manifest_path,
            manifest_verified=False,
            issues=(
                *entry.issues,
                f"{manifest_path or path}: missing or unsafe manifest",
            ),
        )
    if manifest_verifier is None:
        return replace(
            entry,
            state=RunHistoryState.UNKNOWN,
            manifest_path=manifest_path,
            issues=(
                *entry.issues,
                f"{manifest_path}: manifest verification not supplied",
            ),
        )

    try:
        verified = bool(manifest_verifier(path, manifest_path, record.run_id))
    except (OSError, UnicodeError, TypeError, ValueError):
        verified = False
    if not verified:
        return replace(
            entry,
            state=RunHistoryState.CORRUPT,
            manifest_path=manifest_path,
            manifest_verified=False,
            issues=(*entry.issues, f"{manifest_path}: verification failed"),
        )
    return replace(
        entry,
        state=RunHistoryState.FINALIZED,
        manifest_path=manifest_path,
        manifest_verified=True,
    )

def is_previous_run_eligible(
    entry: RunHistoryEntry,
    query: RunHistoryQuery,
) -> bool:
    if not isinstance(entry, RunHistoryEntry):
        raise TypeError("entry must be a RunHistoryEntry")
    if not isinstance(query, RunHistoryQuery):
        raise TypeError("query must be a RunHistoryQuery")
    return _with_eligibility(entry, query).previous_run_eligible

def _with_eligibility(
    entry: RunHistoryEntry,
    query: RunHistoryQuery,
) -> RunHistoryEntry:
    issues = list(entry.issues)
    eligible = entry.state is RunHistoryState.FINALIZED

    if entry.state is RunHistoryState.LEGACY:
        eligible = query.allow_legacy and not query.require_manifest_verification
        if not query.allow_legacy:
            issues.append(f"{entry.run_dir}: legacy run excluded")
    if query.require_manifest_verification and entry.manifest_verified is not True:
        eligible = False
    if _is_current(entry, query):
        eligible = False
        issues.append(f"{entry.run_dir}: current run excluded")
    if query.project_id is not None and entry.project_id != query.project_id:
        eligible = False
        issues.append(f"{entry.run_dir}: project mismatch")
    if query.mode is not None and entry.mode is not query.mode:
        eligible = False
        issues.append(f"{entry.run_dir}: mode mismatch")
    if (
        query.mode is ValidationMode.QUICK
        and query.target_file is not None
        and entry.target_file != query.target_file
    ):
        eligible = False
        issues.append(f"{entry.run_dir}: target mismatch")
    if (
        query.not_after is not None
        and entry.finished_at is not None
        and entry.finished_at > query.not_after
    ):
        eligible = False
        issues.append(f"{entry.run_dir}: newer than current run")

    return replace(
        entry,
        previous_run_eligible=eligible,
        issues=tuple(dict.fromkeys(issues)),
    )

def _manifest_path(
    run_dir: Path,
    record: RunHistoryRecord,
) -> Path | None:
    relative = record.manifest_relative_path
    if relative is None:
        return None
    candidate = run_dir.joinpath(*relative.parts)
    return candidate if _within(candidate, run_dir) else None

def _directory_run_id(path: Path) -> RunId | None:
    match = _RUN_DIR_RE.fullmatch(path.name)
    if match is None:
        return None
    try:
        return validate_run_id(match.group("id"))
    except (TypeError, ValueError):
        return None

def _sort_key(entry: RunHistoryEntry) -> tuple[datetime, datetime, int, str]:
    minimum = datetime.min.replace(tzinfo=UTC)
    run_time, collision = _run_order(entry.run_id)
    return (
        entry.finished_at or minimum,
        run_time,
        collision,
        entry.run_dir.name.casefold(),
    )

def _run_order(run_id: RunId | None) -> tuple[datetime, int]:
    minimum = datetime.min.replace(tzinfo=UTC)
    if run_id is None:
        return minimum, 0
    parts = str(run_id).split("_")
    try:
        stamp = datetime.strptime(
            "_".join(parts[:2]),
            "%Y%m%d_%H%M%S",
        ).replace(tzinfo=UTC)
        return stamp, int(parts[2]) if len(parts) > 2 else 1
    except (ValueError, IndexError):
        return minimum, 0

def _include(entry: RunHistoryEntry, query: RunHistoryQuery) -> bool:
    if entry.state in {RunHistoryState.FINALIZED, RunHistoryState.LEGACY}:
        return True
    if entry.state is RunHistoryState.INCOMPLETE:
        return query.include_incomplete
    if entry.state is RunHistoryState.CORRUPT:
        return query.include_corrupt
    return query.include_unknown

def _is_current(entry: RunHistoryEntry, query: RunHistoryQuery) -> bool:
    if query.current_run_id is not None and entry.run_id == query.current_run_id:
        return True
    return (
        query.current_run_dir is not None
        and _same(entry.run_dir, query.current_run_dir)
    )

def _entry(
    run_dir: Path,
    state: RunHistoryState,
    issue: str,
) -> RunHistoryEntry:
    return RunHistoryEntry(
        run_dir=run_dir,
        state=state,
        run_id=_directory_run_id(run_dir),
        issues=(f"{run_dir}: {issue}",),
    )

def _project_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("path must be non-empty and NUL-free")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("path must be project-relative")
    return path.as_posix()

def _run_relative_path(value: PurePosixPath | str) -> PurePosixPath:
    text = value.as_posix() if isinstance(value, PurePosixPath) else value
    if not isinstance(text, str) or not text or "\x00" in text or "\\" in text:
        raise ValueError("manifest path must be portable")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or re.match(r"^[A-Za-z]:", text)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("manifest path must be run-relative")
    return path

def _absolute_path(path: Path, field: str) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if not path.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return path

def _absolute_directory(path: Path, field: str) -> Path:
    checked = _absolute_path(path, field)
    if _link(checked) or not checked.is_dir():
        raise NotADirectoryError(f"{field} is not a safe directory")
    return checked.resolve(strict=True)

def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)

def _immediate_child(path: Path, root: Path) -> bool:
    try:
        return path.resolve(strict=True).parent == root.resolve(strict=True)
    except OSError:
        return False

def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False

def _same(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve(strict=False))) == os.path.normcase(
        str(right.resolve(strict=False))
    )

def _link(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(flag and getattr(metadata, "st_file_attributes", 0) & flag)

__all__ = (
    "MANIFEST_FILENAME",
    "ManifestVerifier",
    "RunHistoryEntry",
    "RunHistoryQuery",
    "RunHistoryRecord",
    "RunHistoryResult",
    "RunHistoryState",
    "SUMMARY_FILENAME",
    "SummaryReader",
    "discover_run_history",
    "inspect_run_directory",
    "is_previous_run_eligible",
    "select_previous_run",
)
