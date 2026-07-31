"""Deterministic GF source selection for runs and language probing.

The run-oriented API remains backward compatible.  ``select_source_tree``
exposes the same bounded enumeration, filtering, containment, deduplication and
ordering behavior to path-resolved language startup without requiring a fake
``RunConfig`` or duplicating selection logic in the language probe.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.config.models import RunConfig
from gf_wordbench.kernel.errors import (
    ConfigurationError,
    EvidenceIOError,
    PathSecurityError,
)
from gf_wordbench.kernel.statuses import TargetKind, ValidationMode

from .models import ExcludedFileEntry
from .targets import extract_module_name as _extract_module_name

__all__ = (
    "SelectionFilesystem",
    "SelectionService",
    "extract_module_name",
    "select_files",
    "select_source_tree",
)

_MISSING_FILE: Final[str] = "missing_file"
_NOT_A_FILE: Final[str] = "not_a_file"
_NOT_GF_FILE: Final[str] = "not_gf_file"
_OUTSIDE_PROJECT_ROOT: Final[str] = "outside_project_root"
_OUTSIDE_SOURCE_ROOT: Final[str] = "outside_source_root"
_UNREADABLE_FILE: Final[str] = "unreadable_file"
_EXCLUDED_BY_REGEX: Final[str] = "excluded_by_regex"
_NOT_MATCHED_BY_INCLUDE_REGEX: Final[str] = (
    "not_matched_by_include_regex"
)
_EXCLUDED_BY_LIMIT: Final[str] = "excluded_by_limit"
_DUPLICATE_CANDIDATE: Final[str] = "duplicate_candidate"

_SOURCE_TARGET_KINDS: Final[frozenset[TargetKind]] = frozenset(
    {
        TargetKind.FILE,
        TargetKind.MODULE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }
)


@runtime_checkable
class SelectionFilesystem(Protocol):
    def resolve(
        self,
        path: Path,
        *,
        strict: bool,
    ) -> Path:
        ...

    def exists(self, path: Path) -> bool:
        ...

    def is_file(self, path: Path) -> bool:
        ...

    def is_directory(self, path: Path) -> bool:
        ...

    def is_readable(self, path: Path) -> bool:
        ...

    def rglob(
        self,
        root: Path,
        pattern: str,
    ) -> Iterable[Path]:
        ...


class _LocalSelectionFilesystem:
    __slots__ = ()

    def resolve(
        self,
        path: Path,
        *,
        strict: bool,
    ) -> Path:
        return path.resolve(strict=strict)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_readable(self, path: Path) -> bool:
        return os.access(path, os.R_OK)

    def rglob(
        self,
        root: Path,
        pattern: str,
    ) -> Iterable[Path]:
        return root.rglob(pattern)


_LOCAL_FILESYSTEM: Final[SelectionFilesystem] = (
    _LocalSelectionFilesystem()
)


@dataclass(frozen=True, slots=True)
class _SelectionRoots:
    project_root: Path
    source_root: Path


@dataclass(frozen=True, slots=True)
class _CompiledFilters:
    include: re.Pattern[str] | None
    exclude: re.Pattern[str] | None


@dataclass(frozen=True, slots=True)
class _CandidateEvaluation:
    path: Path
    exclusion_reason: str | None

    @property
    def selected(self) -> bool:
        return self.exclusion_reason is None


@dataclass(frozen=True, slots=True)
class SelectionService:
    filesystem: SelectionFilesystem = _LOCAL_FILESYSTEM

    def __post_init__(self) -> None:
        if not isinstance(
            self.filesystem,
            SelectionFilesystem,
        ):
            raise TypeError(
                "filesystem must satisfy SelectionFilesystem"
            )

    def select(
        self,
        run_config: RunConfig,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        _require_run_config(run_config)
        roots = self._resolve_roots(run_config)
        filters = _compile_filters(run_config)

        if run_config.mode is ValidationMode.QUICK:
            return self._select_quick(
                run_config,
                roots=roots,
                filters=filters,
            )
        if run_config.mode is ValidationMode.CHECKPOINT:
            return self._select_checkpoint(
                run_config,
                roots=roots,
                filters=filters,
            )
        if run_config.mode is ValidationMode.RELEASE:
            return self._select_release(
                run_config,
                roots=roots,
                filters=filters,
            )
        if run_config.mode is ValidationMode.DIAGNOSTIC:
            return self._select_diagnostic(
                run_config,
                roots=roots,
                filters=filters,
            )

        raise _configuration_error(
            "Unsupported canonical validation mode.",
            detail=f"mode={run_config.mode!r}",
            subject="mode",
            code="GF-WB-CONFIG-220",
        )

    def select_source_tree(
        self,
        source_root: Path,
        *,
        containment_root: Path | None = None,
        glob_pattern: str = "*.gf",
        include_regex: str = "",
        exclude_regex: str = "",
        max_files: int = 0,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        """Select a deterministic GF source inventory without a ``RunConfig``.

        This operation is intended for path-resolved language probing and other
        bounded source-tree inspections.  ``containment_root`` defaults to the
        source root itself; callers may supply the validated RGL source root to
        permit portable ordering while still restricting the scan to one
        language directory.
        """

        if not isinstance(source_root, Path):
            raise TypeError("source_root must be a pathlib.Path")
        if containment_root is not None and not isinstance(
            containment_root,
            Path,
        ):
            raise TypeError("containment_root must be a pathlib.Path or None")
        if type(max_files) is not int:
            raise TypeError("max_files must be an integer")
        if max_files < 0:
            raise _configuration_error(
                "max_files must not be negative.",
                detail=f"max_files={max_files}",
                subject="max_files",
                code="GF-WB-CONFIG-243",
            )

        resolved_source_root = self._resolve_required_directory(
            source_root,
            subject="source_root",
            missing_message="The selected source root does not exist.",
        )
        resolved_containment_root = self._resolve_required_directory(
            containment_root or resolved_source_root,
            subject="containment_root",
            missing_message="The selection containment root does not exist.",
        )

        if not _contains(
            resolved_containment_root,
            resolved_source_root,
            allow_equal=True,
        ):
            raise PathSecurityError(
                "The selected source root escapes its containment root.",
                code="GF-WB-PATH-223",
                detail=(
                    f"containment_root={resolved_containment_root!s}\n"
                    f"source_root={resolved_source_root!s}"
                ),
                stage="selection",
                operation="resolve_source_tree_roots",
                subject=str(resolved_source_root),
            )

        roots = _SelectionRoots(
            project_root=resolved_containment_root,
            source_root=resolved_source_root,
        )
        filters = _compile_filter_values(
            include_regex=include_regex,
            exclude_regex=exclude_regex,
            include_field="include_regex",
            exclude_field="exclude_regex",
        )
        return self._select_discovered(
            roots=roots,
            filters=filters,
            glob_pattern=_validate_glob(
                glob_pattern,
                field="glob_pattern",
            ),
            max_files=max_files,
        )

    def _resolve_roots(
        self,
        run_config: RunConfig,
    ) -> _SelectionRoots:
        project = run_config.project

        project_root = self._resolve_required_directory(
            project.project_root,
            subject="project.project_root",
            missing_message=(
                "The active project root does not exist."
            ),
        )

        expected_source_root = (
            project_root.joinpath(
                *project.sources.directory.parts
            )
        )
        source_root = self._resolve_required_directory(
            expected_source_root,
            subject="project.source_root",
            missing_message=(
                "The configured project source root does not exist."
            ),
        )

        if not _contains(
            project_root,
            source_root,
            allow_equal=True,
        ):
            raise PathSecurityError(
                "The configured source root escapes the active project.",
                code="GF-WB-PATH-220",
                detail=(
                    f"project_root={project_root!s}\n"
                    f"source_root={source_root!s}"
                ),
                stage="selection",
                operation="resolve_source_root",
                subject=str(source_root),
            )

        declared_source_root = self._resolve_path(
            project.source_root,
            strict=False,
            operation="resolve_declared_source_root",
        )
        if _identity_key(
            declared_source_root
        ) != _identity_key(source_root):
            raise _configuration_error(
                "The resolved source root does not match the "
                "loaded project configuration.",
                detail=(
                    f"declared={declared_source_root!s}\n"
                    f"expected={source_root!s}"
                ),
                subject="project.source_root",
                code="GF-WB-CONFIG-221",
            )

        environment_project_root = self._resolve_path(
            run_config.environment.project_root,
            strict=False,
            operation="resolve_environment_project_root",
        )
        if _identity_key(
            environment_project_root
        ) != _identity_key(project_root):
            raise _configuration_error(
                "The environment project root does not match the "
                "active project root.",
                detail=(
                    f"environment={environment_project_root!s}\n"
                    f"project={project_root!s}"
                ),
                subject="environment.project_root",
                code="GF-WB-CONFIG-222",
            )

        return _SelectionRoots(
            project_root=project_root,
            source_root=source_root,
        )

    def _select_quick(
        self,
        run_config: RunConfig,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        target = run_config.target
        if target is None:
            raise _configuration_error(
                "Quick mode requires one explicit source target.",
                subject="target",
                code="GF-WB-CONFIG-223",
            )
        if target.kind not in _SOURCE_TARGET_KINDS:
            raise _configuration_error(
                "Quick file selection requires a source-file target.",
                detail=f"target_kind={target.kind.value}",
                subject="target.kind",
                code="GF-WB-CONFIG-224",
            )
        if target.value is None:
            raise _configuration_error(
                "Quick mode requires a non-empty target path.",
                subject="target.value",
                code="GF-WB-CONFIG-225",
            )

        candidate = self._resolve_quick_target(
            target.value,
            roots=roots,
        )
        evaluation = self._evaluate_candidate(
            candidate,
            roots=roots,
            filters=filters,
        )
        self._require_selected_target(
            evaluation,
            role="quick target",
        )

        return [evaluation.path], []

    def _select_checkpoint(
        self,
        run_config: RunConfig,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        if run_config.max_files != 0:
            raise _configuration_error(
                "Checkpoint mode cannot use max_files.",
                detail=f"max_files={run_config.max_files}",
                subject="max_files",
                code="GF-WB-CONFIG-226",
            )
        if not run_config.selected_checkpoints:
            raise _configuration_error(
                "Checkpoint mode requires configured checkpoints.",
                subject="selected_checkpoints",
                code="GF-WB-CONFIG-227",
            )

        return self._select_required_targets(
            run_config.selected_checkpoints,
            roots=roots,
            filters=filters,
            role="checkpoint",
        )

    def _select_release(
        self,
        run_config: RunConfig,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        if run_config.max_files != 0:
            raise _configuration_error(
                "Release mode cannot use max_files.",
                detail=f"max_files={run_config.max_files}",
                subject="max_files",
                code="GF-WB-CONFIG-228",
            )
        if not run_config.selected_entrypoints:
            raise _configuration_error(
                "Release mode requires configured entrypoints.",
                subject="selected_entrypoints",
                code="GF-WB-CONFIG-229",
            )

        targets = (
            *run_config.selected_checkpoints,
            *run_config.selected_entrypoints,
        )
        return self._select_required_targets(
            targets,
            roots=roots,
            filters=filters,
            role="release target",
        )

    def _select_diagnostic(
        self,
        run_config: RunConfig,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        if run_config.max_files < 0:
            raise _configuration_error(
                "max_files must not be negative.",
                detail=f"max_files={run_config.max_files}",
                subject="max_files",
                code="GF-WB-CONFIG-230",
            )

        return self._select_discovered(
            roots=roots,
            filters=filters,
            glob_pattern=_validate_glob(
                run_config.project.sources.glob,
                field="sources.glob",
            ),
            max_files=run_config.max_files,
        )

    def _select_discovered(
        self,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
        glob_pattern: str,
        max_files: int,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        """Enumerate and evaluate one bounded source tree deterministically."""

        raw_candidates = self._enumerate_candidates(
            roots.source_root,
            glob_pattern,
        )

        accepted: list[Path] = []
        excluded: list[ExcludedFileEntry] = []
        seen: set[str] = set()

        for raw_candidate in raw_candidates:
            normalized_candidate = self._resolve_path(
                raw_candidate,
                strict=False,
                operation="normalize_candidate",
            )
            key = _identity_key(normalized_candidate)

            if key in seen:
                excluded.append(
                    ExcludedFileEntry(
                        file_path=normalized_candidate,
                        excluded_reason=_DUPLICATE_CANDIDATE,
                    )
                )
                continue
            seen.add(key)

            evaluation = self._evaluate_candidate(
                normalized_candidate,
                roots=roots,
                filters=filters,
            )
            if evaluation.selected:
                accepted.append(evaluation.path)
            else:
                excluded.append(
                    ExcludedFileEntry(
                        file_path=evaluation.path,
                        excluded_reason=(
                            evaluation.exclusion_reason
                            or _NOT_A_FILE
                        ),
                    )
                )

        accepted.sort(
            key=lambda path: _diagnostic_sort_key(
                path,
                project_root=roots.project_root,
            )
        )

        if max_files > 0 and len(accepted) > max_files:
            overflow = accepted[max_files:]
            accepted = accepted[:max_files]
            excluded.extend(
                ExcludedFileEntry(
                    file_path=path,
                    excluded_reason=_EXCLUDED_BY_LIMIT,
                )
                for path in overflow
            )

        excluded.sort(
            key=lambda entry: _excluded_sort_key(
                entry,
                project_root=roots.project_root,
            )
        )

        return accepted, excluded

    def _select_required_targets(
        self,
        targets: Sequence[Path],
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
        role: str,
    ) -> tuple[list[Path], list[ExcludedFileEntry]]:
        selected: list[Path] = []
        excluded: list[ExcludedFileEntry] = []
        seen: set[str] = set()

        for index, target in enumerate(targets):
            candidate = self._resolve_configured_target(
                target,
                roots=roots,
                role=f"{role}[{index}]",
            )
            key = _identity_key(candidate)

            if key in seen:
                excluded.append(
                    ExcludedFileEntry(
                        file_path=candidate,
                        excluded_reason=_DUPLICATE_CANDIDATE,
                    )
                )
                continue

            seen.add(key)
            evaluation = self._evaluate_candidate(
                candidate,
                roots=roots,
                filters=filters,
            )
            self._require_selected_target(
                evaluation,
                role=f"{role}[{index}]",
            )
            selected.append(evaluation.path)

        if not selected:
            raise _configuration_error(
                f"No {role} could be selected.",
                subject=role,
                code="GF-WB-CONFIG-231",
            )

        return selected, excluded

    def _resolve_quick_target(
        self,
        raw_target: str,
        *,
        roots: _SelectionRoots,
    ) -> Path:
        target_text = _normalize_target_text(raw_target)
        target_path = Path(target_text)

        if _is_absolute_text(target_text):
            candidate = self._resolve_path(
                target_path,
                strict=False,
                operation="resolve_quick_absolute_target",
            )
            return candidate

        direct_candidates = _ordered_unique_lexical_paths(
            (
                roots.project_root.joinpath(
                    *target_path.parts
                ),
                roots.source_root.joinpath(
                    *target_path.parts
                ),
            )
        )

        for candidate in direct_candidates:
            if self._exists(candidate):
                return self._resolve_path(
                    candidate,
                    strict=False,
                    operation="resolve_quick_direct_target",
                )

        if not _is_basename_only(target_text):
            return self._resolve_path(
                direct_candidates[-1],
                strict=False,
                operation="resolve_missing_quick_target",
            )

        basename = _portable_name(target_text)
        matches: list[Path] = []
        seen: set[str] = set()

        try:
            candidates = self.filesystem.rglob(
                roots.source_root,
                basename,
            )
            for candidate in candidates:
                resolved = self._resolve_path(
                    candidate,
                    strict=False,
                    operation="resolve_quick_basename_candidate",
                )
                key = _identity_key(resolved)
                if key in seen:
                    continue
                seen.add(key)
                matches.append(resolved)
        except OSError as exc:
            raise EvidenceIOError(
                "Quick-target basename resolution failed.",
                code="GF-WB-IO-220",
                detail=str(exc),
                stage="selection",
                operation="resolve_quick_target",
                subject=target_text,
                retryable=True,
            ) from exc

        matches.sort(
            key=lambda path: _diagnostic_sort_key(
                path,
                project_root=roots.project_root,
            )
        )

        if not matches:
            return self._resolve_path(
                roots.source_root / basename,
                strict=False,
                operation="resolve_missing_quick_basename",
            )
        if len(matches) > 1:
            rendered = "\n".join(str(path) for path in matches)
            raise _configuration_error(
                "The quick target basename is ambiguous.",
                detail=rendered,
                subject=target_text,
                code="GF-WB-CONFIG-232",
            )

        return matches[0]

    def _resolve_configured_target(
        self,
        target: Path,
        *,
        roots: _SelectionRoots,
        role: str,
    ) -> Path:
        if not isinstance(target, Path):
            raise TypeError(
                f"{role} must be a pathlib.Path"
            )

        if _is_absolute_text(str(target)):
            candidate = target
        else:
            candidate = roots.source_root.joinpath(
                *target.parts
            )

        return self._resolve_path(
            candidate,
            strict=False,
            operation="resolve_configured_target",
        )

    def _evaluate_candidate(
        self,
        candidate: Path,
        *,
        roots: _SelectionRoots,
        filters: _CompiledFilters,
    ) -> _CandidateEvaluation:
        normalized = self._resolve_path(
            candidate,
            strict=False,
            operation="evaluate_candidate",
        )

        if not self._exists(normalized):
            return _CandidateEvaluation(
                path=normalized,
                exclusion_reason=_MISSING_FILE,
            )
        if not self._is_file(normalized):
            return _CandidateEvaluation(
                path=normalized,
                exclusion_reason=_NOT_A_FILE,
            )
        if normalized.suffix.casefold() != ".gf":
            return _CandidateEvaluation(
                path=normalized,
                exclusion_reason=_NOT_GF_FILE,
            )

        resolved = self._resolve_path(
            normalized,
            strict=True,
            operation="resolve_existing_candidate",
        )

        if not _contains(
            roots.project_root,
            resolved,
            allow_equal=False,
        ):
            return _CandidateEvaluation(
                path=resolved,
                exclusion_reason=_OUTSIDE_PROJECT_ROOT,
            )
        if not _contains(
            roots.source_root,
            resolved,
            allow_equal=False,
        ):
            return _CandidateEvaluation(
                path=resolved,
                exclusion_reason=_OUTSIDE_SOURCE_ROOT,
            )
        if not self._is_readable(resolved):
            return _CandidateEvaluation(
                path=resolved,
                exclusion_reason=_UNREADABLE_FILE,
            )

        file_name = resolved.name
        relative_path = resolved.relative_to(
            roots.project_root
        ).as_posix()

        if _regex_matches(
            filters.exclude,
            file_name=file_name,
            relative_path=relative_path,
        ):
            return _CandidateEvaluation(
                path=resolved,
                exclusion_reason=_EXCLUDED_BY_REGEX,
            )

        if (
            filters.include is not None
            and not _regex_matches(
                filters.include,
                file_name=file_name,
                relative_path=relative_path,
            )
        ):
            return _CandidateEvaluation(
                path=resolved,
                exclusion_reason=(
                    _NOT_MATCHED_BY_INCLUDE_REGEX
                ),
            )

        return _CandidateEvaluation(
            path=resolved,
            exclusion_reason=None,
        )

    def _require_selected_target(
        self,
        evaluation: _CandidateEvaluation,
        *,
        role: str,
    ) -> None:
        if evaluation.selected:
            return

        reason = (
            evaluation.exclusion_reason
            or _NOT_A_FILE
        )
        if reason in {
            _OUTSIDE_PROJECT_ROOT,
            _OUTSIDE_SOURCE_ROOT,
        }:
            raise PathSecurityError(
                f"The required {role} is outside its allowed root.",
                code="GF-WB-PATH-221",
                detail=(
                    f"path={evaluation.path!s}\n"
                    f"reason={reason}"
                ),
                stage="selection",
                operation="select_required_target",
                subject=str(evaluation.path),
            )

        raise _configuration_error(
            f"The required {role} cannot be selected.",
            detail=(
                f"path={evaluation.path!s}\n"
                f"reason={reason}"
            ),
            subject=str(evaluation.path),
            code="GF-WB-CONFIG-233",
        )

    def _resolve_required_directory(
        self,
        path: Path,
        *,
        subject: str,
        missing_message: str,
    ) -> Path:
        normalized = self._resolve_path(
            path,
            strict=False,
            operation="resolve_required_directory",
        )
        if not self._exists(normalized):
            raise _configuration_error(
                missing_message,
                detail=f"path={normalized!s}",
                subject=subject,
                code="GF-WB-CONFIG-234",
            )
        if not self._is_directory(normalized):
            raise _configuration_error(
                "A required selection root is not a directory.",
                detail=f"path={normalized!s}",
                subject=subject,
                code="GF-WB-CONFIG-235",
            )
        if not self._is_readable(normalized):
            raise EvidenceIOError(
                "A required selection root is not readable.",
                code="GF-WB-IO-221",
                detail=f"path={normalized!s}",
                stage="selection",
                operation="resolve_selection_roots",
                subject=subject,
                retryable=True,
            )
        return self._resolve_path(
            normalized,
            strict=True,
            operation="resolve_existing_directory",
        )

    def _enumerate_candidates(
        self,
        source_root: Path,
        glob_pattern: str,
    ) -> Iterator[Path]:
        try:
            yield from self.filesystem.rglob(
                source_root,
                glob_pattern,
            )
        except (OSError, ValueError) as exc:
            raise EvidenceIOError(
                "Source candidate enumeration failed.",
                code="GF-WB-IO-222",
                detail=(
                    f"source_root={source_root!s}\n"
                    f"glob={glob_pattern!r}\n"
                    f"error={exc}"
                ),
                stage="selection",
                operation="enumerate_candidate_files",
                subject=str(source_root),
                retryable=True,
            ) from exc

    def _resolve_path(
        self,
        path: Path,
        *,
        strict: bool,
        operation: str,
    ) -> Path:
        if not isinstance(path, Path):
            raise TypeError("selection paths must be pathlib.Path values")
        if "\x00" in str(path):
            raise ValueError(
                "selection paths must not contain NUL"
            )

        try:
            return self.filesystem.resolve(
                path,
                strict=strict,
            )
        except FileNotFoundError:
            if strict:
                raise
            return path.absolute()
        except OSError as exc:
            raise EvidenceIOError(
                "A selection path could not be resolved.",
                code="GF-WB-IO-223",
                detail=(
                    f"path={path!s}\n"
                    f"error={exc}"
                ),
                stage="selection",
                operation=operation,
                subject=str(path),
                retryable=True,
            ) from exc

    def _exists(self, path: Path) -> bool:
        try:
            return self.filesystem.exists(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A selection path could not be inspected.",
                code="GF-WB-IO-224",
                detail=f"path={path!s}\nerror={exc}",
                stage="selection",
                operation="exists",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_file(self, path: Path) -> bool:
        try:
            return self.filesystem.is_file(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A selection candidate could not be inspected.",
                code="GF-WB-IO-225",
                detail=f"path={path!s}\nerror={exc}",
                stage="selection",
                operation="is_file",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_directory(self, path: Path) -> bool:
        try:
            return self.filesystem.is_directory(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A selection root could not be inspected.",
                code="GF-WB-IO-226",
                detail=f"path={path!s}\nerror={exc}",
                stage="selection",
                operation="is_directory",
                subject=str(path),
                retryable=True,
            ) from exc

    def _is_readable(self, path: Path) -> bool:
        try:
            return self.filesystem.is_readable(path)
        except OSError as exc:
            raise EvidenceIOError(
                "A selection path readability check failed.",
                code="GF-WB-IO-227",
                detail=f"path={path!s}\nerror={exc}",
                stage="selection",
                operation="is_readable",
                subject=str(path),
                retryable=True,
            ) from exc


def select_files(
    run_config: RunConfig,
    *,
    filesystem: SelectionFilesystem | None = None,
) -> tuple[list[Path], list[ExcludedFileEntry]]:
    """Select files for one fully resolved validation run."""

    service = SelectionService(
        filesystem=filesystem or _LOCAL_FILESYSTEM
    )
    return service.select(run_config)


def select_source_tree(
    source_root: Path,
    *,
    containment_root: Path | None = None,
    glob_pattern: str = "*.gf",
    include_regex: str = "",
    exclude_regex: str = "",
    max_files: int = 0,
    filesystem: SelectionFilesystem | None = None,
) -> tuple[list[Path], list[ExcludedFileEntry]]:
    """Select one source inventory for path-resolved language probing."""

    service = SelectionService(
        filesystem=filesystem or _LOCAL_FILESYSTEM
    )
    return service.select_source_tree(
        source_root,
        containment_root=containment_root,
        glob_pattern=glob_pattern,
        include_regex=include_regex,
        exclude_regex=exclude_regex,
        max_files=max_files,
    )


def extract_module_name(
    file_path: Path,
) -> str:
    """Delegate module-name extraction while preserving this API's errors."""

    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a pathlib.Path")
    if not file_path.name:
        raise ValueError("file_path must identify a file")
    return _extract_module_name(file_path)


def _compile_filters(
    run_config: RunConfig,
) -> _CompiledFilters:
    sources = run_config.project.sources
    return _compile_filter_values(
        include_regex=sources.include_regex,
        exclude_regex=sources.exclude_regex,
        include_field="sources.include_regex",
        exclude_field="sources.exclude_regex",
    )


def _compile_filter_values(
    *,
    include_regex: str,
    exclude_regex: str,
    include_field: str,
    exclude_field: str,
) -> _CompiledFilters:
    return _CompiledFilters(
        include=_compile_optional_regex(
            include_regex,
            field=include_field,
        ),
        exclude=_compile_optional_regex(
            exclude_regex,
            field=exclude_field,
        ),
    )


def _compile_optional_regex(
    value: str,
    *,
    field: str,
) -> re.Pattern[str] | None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise _configuration_error(
            "A source-selection regex contains NUL.",
            subject=field,
            code="GF-WB-CONFIG-236",
        )
    if not value.strip():
        return None

    try:
        return re.compile(value)
    except re.error as exc:
        raise _configuration_error(
            "A source-selection regex is invalid.",
            detail=(
                f"field={field}\n"
                f"pattern={value!r}\n"
                f"error={exc}"
            ),
            subject=field,
            code="GF-WB-CONFIG-237",
        ) from exc


def _regex_matches(
    pattern: re.Pattern[str] | None,
    *,
    file_name: str,
    relative_path: str,
) -> bool:
    if pattern is None:
        return False
    return (
        pattern.search(file_name) is not None
        or pattern.search(relative_path) is not None
    )


def _validate_glob(
    value: str,
    *,
    field: str = "sources.glob",
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise _configuration_error(
            f"{field} contains NUL.",
            subject=field,
            code="GF-WB-CONFIG-238",
        )

    normalized = value.strip()
    if not normalized:
        raise _configuration_error(
            f"{field} must not be empty.",
            subject=field,
            code="GF-WB-CONFIG-239",
        )
    if _is_absolute_text(normalized):
        raise _configuration_error(
            f"{field} must be relative.",
            detail=f"glob={normalized!r}",
            subject=field,
            code="GF-WB-CONFIG-240",
        )
    return normalized


def _diagnostic_sort_key(
    path: Path,
    *,
    project_root: Path,
) -> tuple[str, str]:
    relative = _portable_relative_path(
        path,
        project_root=project_root,
    )
    return relative.casefold(), relative


def _excluded_sort_key(
    entry: ExcludedFileEntry,
    *,
    project_root: Path,
) -> tuple[str, str, str]:
    relative = _portable_display_path(
        entry.file_path,
        project_root=project_root,
    )
    return (
        relative.casefold(),
        relative,
        entry.excluded_reason,
    )


def _portable_relative_path(
    path: Path,
    *,
    project_root: Path,
) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError as exc:
        raise PathSecurityError(
            "A selected path is outside the active project root.",
            code="GF-WB-PATH-222",
            detail=(
                f"path={path!s}\n"
                f"project_root={project_root!s}"
            ),
            stage="selection",
            operation="build_relative_identity",
            subject=str(path),
        ) from exc


def _portable_display_path(
    path: Path,
    *,
    project_root: Path,
) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _contains(
    root: Path,
    candidate: Path,
    *,
    allow_equal: bool,
) -> bool:
    try:
        common = Path(
            os.path.commonpath(
                (str(root), str(candidate))
            )
        )
    except ValueError:
        return False

    if _identity_key(common) != _identity_key(root):
        return False
    if not allow_equal and (
        _identity_key(candidate)
        == _identity_key(root)
    ):
        return False
    return True


def _ordered_unique_lexical_paths(
    values: Iterable[Path],
) -> tuple[Path, ...]:
    seen: set[str] = set()
    result: list[Path] = []

    for value in values:
        key = os.path.normcase(
            os.path.normpath(
                os.path.abspath(str(value))
            )
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(value)

    return tuple(result)


def _identity_key(
    path: Path,
) -> str:
    return os.path.normcase(
        os.path.normpath(str(path))
    )


def _normalize_target_text(
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "target.value must be a string"
        )
    if "\x00" in value:
        raise _configuration_error(
            "The target path contains NUL.",
            subject="target.value",
            code="GF-WB-CONFIG-241",
        )

    normalized = value.strip()
    if not normalized:
        raise _configuration_error(
            "The target path must not be empty.",
            subject="target.value",
            code="GF-WB-CONFIG-242",
        )
    return normalized


def _is_absolute_text(
    value: str,
) -> bool:
    return (
        Path(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )


def _is_basename_only(
    value: str,
) -> bool:
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    return (
        posix.name == value
        and windows.name == value
        and value not in {".", ".."}
    )


def _portable_name(
    value: str,
) -> str:
    windows_name = PureWindowsPath(value).name
    posix_name = PurePosixPath(value).name
    if windows_name != value:
        return windows_name
    return posix_name


def _configuration_error(
    message: str,
    *,
    detail: str = "",
    subject: str | None = None,
    code: str,
) -> ConfigurationError:
    return ConfigurationError(
        message,
        code=code,
        detail=detail,
        stage="selection",
        operation="select_files",
        subject=subject,
    )


def _require_run_config(
    value: object,
) -> RunConfig:
    if not isinstance(value, RunConfig):
        raise TypeError(
            "run_config must be a RunConfig"
        )
    if not isinstance(value.mode, ValidationMode):
        raise TypeError(
            "run_config.mode must be a ValidationMode"
        )
    if type(value.max_files) is not int:
        raise TypeError(
            "run_config.max_files must be an integer"
        )
    return value
