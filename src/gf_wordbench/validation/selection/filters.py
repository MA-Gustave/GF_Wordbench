"""Canonical file-selection filters for GF Wordbench."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Literal, TypeAlias

from gf_wordbench.kernel.errors import ConfigurationError

SelectionExclusionReason: TypeAlias = Literal[
    "missing_file",
    "not_a_file",
    "not_gf_file",
    "outside_project_root",
    "outside_source_root",
    "unreadable_file",
    "excluded_by_regex",
    "not_matched_by_include_regex",
    "excluded_by_limit",
    "duplicate_candidate",
]

MISSING_FILE: Final[SelectionExclusionReason] = "missing_file"
NOT_A_FILE: Final[SelectionExclusionReason] = "not_a_file"
NOT_GF_FILE: Final[SelectionExclusionReason] = "not_gf_file"
OUTSIDE_PROJECT_ROOT: Final[SelectionExclusionReason] = "outside_project_root"
OUTSIDE_SOURCE_ROOT: Final[SelectionExclusionReason] = "outside_source_root"
UNREADABLE_FILE: Final[SelectionExclusionReason] = "unreadable_file"
EXCLUDED_BY_REGEX: Final[SelectionExclusionReason] = "excluded_by_regex"
NOT_MATCHED_BY_INCLUDE_REGEX: Final[SelectionExclusionReason] = (
    "not_matched_by_include_regex"
)
EXCLUDED_BY_LIMIT: Final[SelectionExclusionReason] = "excluded_by_limit"
DUPLICATE_CANDIDATE: Final[SelectionExclusionReason] = "duplicate_candidate"

_DEFAULT_SOURCE_GLOB: Final[str] = "*.gf"


@dataclass(frozen=True, slots=True)
class CompiledSourceFilters:
    include_pattern: re.Pattern[str] | None
    exclude_pattern: re.Pattern[str] | None

    def exclusion_reason(
        self,
        *,
        file_name: str,
        project_relative_path: str,
    ) -> SelectionExclusionReason | None:
        _require_match_text(file_name, field_name="file_name")
        _require_match_text(
            project_relative_path,
            field_name="project_relative_path",
        )

        if _matches_either(
            self.exclude_pattern,
            file_name=file_name,
            project_relative_path=project_relative_path,
        ):
            return EXCLUDED_BY_REGEX

        if (
            self.include_pattern is not None
            and not _matches_either(
                self.include_pattern,
                file_name=file_name,
                project_relative_path=project_relative_path,
            )
        ):
            return NOT_MATCHED_BY_INCLUDE_REGEX

        return None


@dataclass(frozen=True, slots=True)
class CandidateFilterDecision:
    candidate_path: Path
    resolved_path: Path
    project_relative_path: str | None
    excluded_reason: SelectionExclusionReason | None

    def __post_init__(self) -> None:
        candidate_path = Path(self.candidate_path)
        resolved_path = Path(self.resolved_path)

        if "\x00" in str(candidate_path):
            raise ValueError("candidate_path must not contain NUL")
        if "\x00" in str(resolved_path):
            raise ValueError("resolved_path must not contain NUL")
        if not resolved_path.is_absolute():
            raise ValueError("resolved_path must be absolute")

        relative_path = self.project_relative_path
        if relative_path is not None:
            _require_match_text(
                relative_path,
                field_name="project_relative_path",
            )
            if "\\" in relative_path:
                raise ValueError(
                    "project_relative_path must use POSIX separators"
                )
            portable = PurePosixPath(relative_path)
            if portable.is_absolute() or ".." in portable.parts:
                raise ValueError(
                    "project_relative_path must be contained and relative"
                )

        reason = self.excluded_reason
        if reason is not None and reason not in _EXCLUSION_REASONS:
            raise ValueError(f"unsupported exclusion reason: {reason!r}")

        if reason is None and relative_path is None:
            raise ValueError(
                "a selected candidate requires project_relative_path"
            )

        object.__setattr__(self, "candidate_path", candidate_path)
        object.__setattr__(self, "resolved_path", resolved_path)

    @property
    def selected(self) -> bool:
        return self.excluded_reason is None


_EXCLUSION_REASONS: Final[frozenset[str]] = frozenset(
    {
        MISSING_FILE,
        NOT_A_FILE,
        NOT_GF_FILE,
        OUTSIDE_PROJECT_ROOT,
        OUTSIDE_SOURCE_ROOT,
        UNREADABLE_FILE,
        EXCLUDED_BY_REGEX,
        NOT_MATCHED_BY_INCLUDE_REGEX,
        EXCLUDED_BY_LIMIT,
        DUPLICATE_CANDIDATE,
    }
)


def compile_optional_regex(
    pattern: str | None,
    *,
    field_name: str,
) -> re.Pattern[str] | None:
    normalized = _normalize_optional_regex(
        pattern,
        field_name=field_name,
    )
    if normalized is None:
        return None

    try:
        return re.compile(normalized)
    except re.error as exc:
        raise ConfigurationError(
            f"{field_name} is not a valid regular expression",
            detail=str(exc),
            stage="selection",
            operation="compile_regex",
            subject=field_name,
        ) from exc


def compile_source_filters(
    *,
    include_regex: str | None,
    exclude_regex: str | None,
) -> CompiledSourceFilters:
    return CompiledSourceFilters(
        include_pattern=compile_optional_regex(
            include_regex,
            field_name="sources.include_regex",
        ),
        exclude_pattern=compile_optional_regex(
            exclude_regex,
            field_name="sources.exclude_regex",
        ),
    )


def normalize_source_glob(source_glob: str) -> str:
    if not isinstance(source_glob, str):
        raise TypeError("sources.glob must be a string")
    if "\x00" in source_glob:
        raise ValueError("sources.glob must not contain NUL")
    if not source_glob.strip():
        raise ConfigurationError(
            "sources.glob must not be empty",
            stage="selection",
            operation="validate_glob",
            subject="sources.glob",
        )
    return source_glob


def matches_source_glob(
    project_relative_path: str | PurePosixPath,
    source_glob: str = _DEFAULT_SOURCE_GLOB,
) -> bool:
    pattern = normalize_source_glob(source_glob)
    relative_path = PurePosixPath(project_relative_path)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(
            "project_relative_path must be a contained relative path"
        )

    return relative_path.match(pattern)


def candidate_exclusion_reason(
    candidate: Path,
    *,
    project_root: Path,
    source_root: Path,
    filters: CompiledSourceFilters,
) -> CandidateFilterDecision:
    if not isinstance(filters, CompiledSourceFilters):
        raise TypeError("filters must be CompiledSourceFilters")

    candidate_path = _coerce_path(candidate, field_name="candidate")
    resolved_project_root = _resolve_root(
        project_root,
        field_name="project_root",
    )
    resolved_source_root = _resolve_root(
        source_root,
        field_name="source_root",
    )

    if not _is_relative_to(resolved_source_root, resolved_project_root):
        raise ConfigurationError(
            "source_root must remain inside project_root",
            stage="selection",
            operation="validate_roots",
            subject=str(resolved_source_root),
        )

    resolved_candidate = candidate_path.resolve(strict=False)

    if not candidate_path.exists():
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=None,
            excluded_reason=MISSING_FILE,
        )

    if not candidate_path.is_file():
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=None,
            excluded_reason=NOT_A_FILE,
        )

    if candidate_path.suffix.casefold() != ".gf":
        relative_path = _relative_path_or_none(
            resolved_candidate,
            resolved_project_root,
        )
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=relative_path,
            excluded_reason=NOT_GF_FILE,
        )

    if not _is_relative_to(resolved_candidate, resolved_project_root):
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=None,
            excluded_reason=OUTSIDE_PROJECT_ROOT,
        )

    project_relative_path = resolved_candidate.relative_to(
        resolved_project_root
    ).as_posix()

    if not _is_relative_to(resolved_candidate, resolved_source_root):
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=project_relative_path,
            excluded_reason=OUTSIDE_SOURCE_ROOT,
        )

    if not os.access(resolved_candidate, os.R_OK):
        return CandidateFilterDecision(
            candidate_path=candidate_path,
            resolved_path=resolved_candidate,
            project_relative_path=project_relative_path,
            excluded_reason=UNREADABLE_FILE,
        )

    regex_reason = filters.exclusion_reason(
        file_name=resolved_candidate.name,
        project_relative_path=project_relative_path,
    )
    return CandidateFilterDecision(
        candidate_path=candidate_path,
        resolved_path=resolved_candidate,
        project_relative_path=project_relative_path,
        excluded_reason=regex_reason,
    )


def is_included_file(
    candidate: Path,
    *,
    project_root: Path,
    source_root: Path,
    include_regex: str | None = None,
    exclude_regex: str | None = None,
) -> bool:
    filters = compile_source_filters(
        include_regex=include_regex,
        exclude_regex=exclude_regex,
    )
    return candidate_exclusion_reason(
        candidate,
        project_root=project_root,
        source_root=source_root,
        filters=filters,
    ).selected


def filter_candidate_files(
    candidates: Iterable[Path],
    *,
    project_root: Path,
    source_root: Path,
    include_regex: str | None = None,
    exclude_regex: str | None = None,
    required: bool = False,
) -> tuple[
    tuple[Path, ...],
    tuple[CandidateFilterDecision, ...],
]:
    if isinstance(candidates, (str, bytes, Path)):
        raise TypeError("candidates must be an iterable of paths")
    if type(required) is not bool:
        raise TypeError("required must be a bool")

    filters = compile_source_filters(
        include_regex=include_regex,
        exclude_regex=exclude_regex,
    )
    selected: list[Path] = []
    decisions: list[CandidateFilterDecision] = []

    for candidate in candidates:
        decision = candidate_exclusion_reason(
            Path(candidate),
            project_root=project_root,
            source_root=source_root,
            filters=filters,
        )
        decisions.append(decision)

        if decision.selected:
            selected.append(decision.resolved_path)
            continue

        if required:
            raise _required_candidate_error(decision)

    return tuple(selected), tuple(decisions)


def apply_diagnostic_limit(
    accepted_paths: Sequence[Path],
    *,
    max_files: int,
    project_root: Path,
) -> tuple[
    tuple[Path, ...],
    tuple[CandidateFilterDecision, ...],
]:
    if isinstance(accepted_paths, (str, bytes, Path)):
        raise TypeError("accepted_paths must be a sequence of paths")
    if isinstance(max_files, bool) or not isinstance(max_files, int):
        raise TypeError("max_files must be an integer")
    if max_files < 0:
        raise ConfigurationError(
            "max_files must be non-negative",
            stage="selection",
            operation="apply_limit",
            subject="max_files",
        )

    paths = tuple(Path(path).resolve(strict=False) for path in accepted_paths)
    if max_files == 0 or len(paths) <= max_files:
        return paths, ()

    root = _resolve_root(project_root, field_name="project_root")
    selected = paths[:max_files]
    overflow: list[CandidateFilterDecision] = []

    for path in paths[max_files:]:
        if not _is_relative_to(path, root):
            raise ConfigurationError(
                "accepted diagnostic path escaped project_root",
                stage="selection",
                operation="apply_limit",
                subject=str(path),
            )
        overflow.append(
            CandidateFilterDecision(
                candidate_path=path,
                resolved_path=path,
                project_relative_path=path.relative_to(root).as_posix(),
                excluded_reason=EXCLUDED_BY_LIMIT,
            )
        )

    return selected, tuple(overflow)


def _required_candidate_error(
    decision: CandidateFilterDecision,
) -> ConfigurationError:
    reason = decision.excluded_reason
    assert reason is not None

    return ConfigurationError(
        f"required target is not selectable: {reason}",
        stage="selection",
        operation="filter_required_target",
        subject=str(decision.candidate_path),
    )


def _normalize_optional_regex(
    pattern: str | None,
    *,
    field_name: str,
) -> str | None:
    if pattern is None:
        return None
    if not isinstance(pattern, str):
        raise TypeError(f"{field_name} must be a string or None")
    if "\x00" in pattern:
        raise ValueError(f"{field_name} must not contain NUL")
    if not pattern.strip():
        return None
    return pattern


def _matches_either(
    pattern: re.Pattern[str] | None,
    *,
    file_name: str,
    project_relative_path: str,
) -> bool:
    if pattern is None:
        return False
    return (
        pattern.search(file_name) is not None
        or pattern.search(project_relative_path) is not None
    )


def _require_match_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or "\x00" in value:
        raise ValueError(
            f"{field_name} must be non-empty and contain no NUL"
        )
    return value


def _coerce_path(value: Path, *, field_name: str) -> Path:
    if isinstance(value, bytes):
        raise TypeError(f"{field_name} must be path-like text")
    try:
        path = Path(value)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be path-like") from exc
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    return path


def _resolve_root(value: Path, *, field_name: str) -> Path:
    root = _coerce_path(value, field_name=field_name).resolve(strict=False)
    if not root.is_absolute():
        raise ValueError(f"{field_name} must resolve to an absolute path")
    return root


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _relative_path_or_none(
    candidate: Path,
    root: Path,
) -> str | None:
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return None


__all__ = (
    "CandidateFilterDecision",
    "CompiledSourceFilters",
    "DUPLICATE_CANDIDATE",
    "EXCLUDED_BY_LIMIT",
    "EXCLUDED_BY_REGEX",
    "MISSING_FILE",
    "NOT_A_FILE",
    "NOT_GF_FILE",
    "NOT_MATCHED_BY_INCLUDE_REGEX",
    "OUTSIDE_PROJECT_ROOT",
    "OUTSIDE_SOURCE_ROOT",
    "SelectionExclusionReason",
    "UNREADABLE_FILE",
    "apply_diagnostic_limit",
    "candidate_exclusion_reason",
    "compile_optional_regex",
    "compile_source_filters",
    "filter_candidate_files",
    "is_included_file",
    "matches_source_glob",
    "normalize_source_glob",
)
