"""Immutable models for deterministic GF source-file selection."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Final, TypeAlias, cast

from gf_wordbench.kernel.statuses import ValidationMode

PathInput: TypeAlias = str | os.PathLike[str]

_GF_SUFFIX: Final[str] = ".gf"


@unique
class SelectionReason(StrEnum):
    MISSING_FILE = "missing_file"
    NOT_A_FILE = "not_a_file"
    NOT_GF_FILE = "not_gf_file"
    OUTSIDE_PROJECT_ROOT = "outside_project_root"
    OUTSIDE_SOURCE_ROOT = "outside_source_root"
    UNREADABLE_FILE = "unreadable_file"
    EXCLUDED_BY_REGEX = "excluded_by_regex"
    NOT_MATCHED_BY_INCLUDE_REGEX = "not_matched_by_include_regex"
    EXCLUDED_BY_LIMIT = "excluded_by_limit"
    DUPLICATE_CANDIDATE = "duplicate_candidate"


@unique
class SelectionOrigin(StrEnum):
    DISCOVERED = "discovered"
    QUICK_TARGET = "quick_target"
    CHECKPOINT = "checkpoint"
    ENTRYPOINT = "entrypoint"


@dataclass(frozen=True, slots=True)
class SelectionTarget:
    file_path: Path
    origin: SelectionOrigin
    required: bool
    declared_order: int

    def __post_init__(self) -> None:
        file_path = _require_absolute_normalized_path(
            self.file_path,
            field="file_path",
        )
        if not isinstance(self.origin, SelectionOrigin):
            raise TypeError("origin must be a SelectionOrigin")
        if type(self.required) is not bool:
            raise TypeError("required must be a bool")
        declared_order = _require_non_negative_integer(
            self.declared_order,
            field="declared_order",
        )
        object.__setattr__(self, "file_path", file_path)
        object.__setattr__(self, "declared_order", declared_order)

    @property
    def module_name(self) -> str:
        return self.file_path.stem


@dataclass(frozen=True, slots=True)
class SelectionCandidate:
    file_path: Path
    project_relative_path: str
    source_relative_path: str
    origin: SelectionOrigin
    required: bool = False
    declared_order: int | None = None

    def __post_init__(self) -> None:
        file_path = _require_absolute_normalized_path(
            self.file_path,
            field="file_path",
        )
        project_relative_path = _require_portable_relative_path(
            self.project_relative_path,
            field="project_relative_path",
        )
        source_relative_path = _require_portable_relative_path(
            self.source_relative_path,
            field="source_relative_path",
        )
        if not isinstance(self.origin, SelectionOrigin):
            raise TypeError("origin must be a SelectionOrigin")
        if type(self.required) is not bool:
            raise TypeError("required must be a bool")
        if self.declared_order is not None:
            declared_order = _require_non_negative_integer(
                self.declared_order,
                field="declared_order",
            )
        else:
            declared_order = None
        if self.origin is SelectionOrigin.DISCOVERED:
            if self.required:
                raise ValueError(
                    "discovered candidates cannot be required targets"
                )
            if declared_order is not None:
                raise ValueError(
                    "discovered candidates cannot have declared_order"
                )
        elif declared_order is None:
            raise ValueError(
                "explicit selection candidates require declared_order"
            )
        object.__setattr__(self, "file_path", file_path)
        object.__setattr__(
            self,
            "project_relative_path",
            project_relative_path,
        )
        object.__setattr__(
            self,
            "source_relative_path",
            source_relative_path,
        )
        object.__setattr__(self, "declared_order", declared_order)

    @property
    def module_name(self) -> str:
        return self.file_path.stem


@dataclass(frozen=True, slots=True)
class ExcludedFileEntry:
    file_path: Path
    excluded_reason: str

    def __post_init__(self) -> None:
        file_path = _require_absolute_normalized_path(
            self.file_path,
            field="file_path",
            require_gf_suffix=False,
        )
        reason = _require_selection_reason(self.excluded_reason)
        object.__setattr__(self, "file_path", file_path)
        object.__setattr__(self, "excluded_reason", reason.value)

    @property
    def reason(self) -> SelectionReason:
        return SelectionReason(self.excluded_reason)


@dataclass(frozen=True, slots=True)
class SelectionCounts:
    files_seen: int
    files_included: int
    files_excluded: int

    def __post_init__(self) -> None:
        files_seen = _require_non_negative_integer(
            self.files_seen,
            field="files_seen",
        )
        files_included = _require_non_negative_integer(
            self.files_included,
            field="files_included",
        )
        files_excluded = _require_non_negative_integer(
            self.files_excluded,
            field="files_excluded",
        )
        if files_seen != files_included + files_excluded:
            raise ValueError(
                "files_seen must equal files_included + files_excluded"
            )
        object.__setattr__(self, "files_seen", files_seen)
        object.__setattr__(self, "files_included", files_included)
        object.__setattr__(self, "files_excluded", files_excluded)


@dataclass(frozen=True, slots=True)
class FileSelection:
    mode: ValidationMode
    included_files: tuple[Path, ...]
    excluded_files: tuple[ExcludedFileEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be a ValidationMode")
        included_files = _require_path_tuple(
            self.included_files,
            field="included_files",
            require_gf_suffix=True,
        )
        excluded_files = _require_excluded_tuple(
            self.excluded_files,
            field="excluded_files",
        )

        included_keys = {
            _path_identity(path)
            for path in included_files
        }
        excluded_keys: set[str] = set()
        for index, entry in enumerate(excluded_files):
            key = _path_identity(entry.file_path)
            if key in included_keys:
                raise ValueError(
                    "included and excluded file identities must not overlap"
                )
            if key in excluded_keys:
                raise ValueError(
                    "excluded_files must not contain duplicate identities: "
                    f"index {index}"
                )
            excluded_keys.add(key)

        if self.mode is ValidationMode.QUICK and len(included_files) != 1:
            raise ValueError(
                "quick mode requires exactly one included file"
            )
        if self.mode in {
            ValidationMode.CHECKPOINT,
            ValidationMode.RELEASE,
        }:
            if any(
                entry.reason is SelectionReason.EXCLUDED_BY_LIMIT
                for entry in excluded_files
            ):
                raise ValueError(
                    "checkpoint and release selections cannot be truncated"
                )

        object.__setattr__(self, "included_files", included_files)
        object.__setattr__(self, "excluded_files", excluded_files)

    @property
    def selected_files(self) -> tuple[Path, ...]:
        return self.included_files

    @property
    def excluded_entries(self) -> tuple[ExcludedFileEntry, ...]:
        return self.excluded_files

    @property
    def counts(self) -> SelectionCounts:
        return SelectionCounts(
            files_seen=len(self.included_files) + len(self.excluded_files),
            files_included=len(self.included_files),
            files_excluded=len(self.excluded_files),
        )

    @property
    def files_seen(self) -> int:
        return self.counts.files_seen

    @property
    def files_included(self) -> int:
        return self.counts.files_included

    @property
    def files_excluded(self) -> int:
        return self.counts.files_excluded

    def as_public_result(
        self,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        return list(self.included_files), list(self.excluded_files)


def extract_module_name(file_path: PathInput) -> str:
    path = _coerce_path(file_path, field="file_path")
    if path.name in {"", ".", ".."}:
        raise ValueError("file_path must identify a file")
    if path.suffix.casefold() != _GF_SUFFIX:
        raise ValueError("file_path must end in '.gf'")
    if not path.stem:
        raise ValueError("file_path must have a non-empty stem")
    return path.stem


def make_excluded_file_entry(
    file_path: PathInput,
    reason: SelectionReason | str,
) -> ExcludedFileEntry:
    return ExcludedFileEntry(
        file_path=_coerce_path(file_path, field="file_path"),
        excluded_reason=_require_selection_reason(reason).value,
    )


def _require_selection_reason(
    value: SelectionReason | str,
) -> SelectionReason:
    if not isinstance(value, str):
        raise TypeError(
            "excluded_reason must be a SelectionReason or string"
        )
    try:
        return SelectionReason(value)
    except ValueError as exc:
        allowed = ", ".join(reason.value for reason in SelectionReason)
        raise ValueError(
            f"excluded_reason must be one of: {allowed}"
        ) from exc


def _require_path_tuple(
    value: object,
    *,
    field: str,
    require_gf_suffix: bool,
) -> tuple[Path, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    paths: list[Path] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        path = _require_absolute_normalized_path(
            item,
            field=f"{field}[{index}]",
            require_gf_suffix=require_gf_suffix,
        )
        identity = _path_identity(path)
        if identity in seen:
            raise ValueError(
                f"{field} must not contain duplicate file identities"
            )
        seen.add(identity)
        paths.append(path)
    return tuple(paths)


def _require_excluded_tuple(
    value: object,
    *,
    field: str,
) -> tuple[ExcludedFileEntry, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    entries: list[ExcludedFileEntry] = []
    for index, item in enumerate(value):
        if not isinstance(item, ExcludedFileEntry):
            raise TypeError(
                f"{field}[{index}] must be an ExcludedFileEntry"
            )
        entries.append(item)
    return tuple(entries)


def _require_absolute_normalized_path(
    value: object,
    *,
    field: str,
    require_gf_suffix: bool = True,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    rendered = os.fspath(value)
    if "\x00" in rendered:
        raise ValueError(f"{field} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")

    normalized = Path(os.path.normpath(rendered))
    if normalized != value:
        raise ValueError(f"{field} must be lexically normalized")
    if any(part == ".." for part in value.parts):
        raise ValueError(
            f"{field} must not contain unresolved parent traversal"
        )
    if require_gf_suffix and value.suffix.casefold() != _GF_SUFFIX:
        raise ValueError(f"{field} must end in '.gf'")
    if require_gf_suffix and not value.stem:
        raise ValueError(f"{field} must have a non-empty stem")
    return value


def _require_portable_relative_path(
    value: object,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or value != value.strip():
        raise ValueError(
            f"{field} must be a non-empty path without surrounding whitespace"
        )
    if "\x00" in value or "\\" in value:
        raise ValueError(
            f"{field} must use canonical '/' separators and contain no NUL"
        )

    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
    ):
        raise ValueError(f"{field} must be relative")
    if value != path.as_posix():
        raise ValueError(f"{field} must be canonically normalized")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(
            f"{field} must not contain empty, current, or parent segments"
        )
    return value


def _require_non_negative_integer(
    value: object,
    *,
    field: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _path_identity(path: Path) -> str:
    return os.path.normcase(
        os.path.normpath(os.fspath(path))
    )


def _coerce_path(
    value: PathInput,
    *,
    field: str,
) -> Path:
    raw = os.fspath(value)
    if isinstance(raw, bytes):
        raise TypeError(f"{field} must be a text path")
    if "\x00" in raw:
        raise ValueError(f"{field} must not contain NUL")
    return Path(raw)


ExclusionReason = SelectionReason

__all__ = (
    "ExcludedFileEntry",
    "ExclusionReason",
    "FileSelection",
    "PathInput",
    "SelectionCandidate",
    "SelectionCounts",
    "SelectionOrigin",
    "SelectionReason",
    "SelectionTarget",
    "extract_module_name",
    "make_excluded_file_entry",
)
