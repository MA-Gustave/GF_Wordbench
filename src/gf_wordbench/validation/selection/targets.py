"""Canonical validation-target resolution."""

from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path, PurePosixPath
import re

from gf_wordbench.config.models import ValidationTarget
from gf_wordbench.kernel.errors import (
    ContractViolationError,
    EvidenceIOError,
    PathSecurityError,
    ProjectConfigurationError,
)
from gf_wordbench.kernel.statuses import TargetKind

_GF_SUFFIX = ".gf"
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_SOURCE_TARGET_KINDS = frozenset(
    {TargetKind.FILE, TargetKind.MODULE, TargetKind.CHECKPOINT, TargetKind.ENTRYPOINT}
)


def extract_module_name(file_path: Path) -> str:
    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a Path")
    rendered = str(file_path)
    if "\x00" in rendered:
        raise ValueError("file_path must not contain NUL")
    if file_path.name in {"", ".", ".."} or file_path.suffix.casefold() != _GF_SUFFIX:
        raise ValueError("file_path must name a .gf source file")
    if not file_path.stem:
        raise ValueError("file_path must have a module name")
    return file_path.stem


def is_source_target_kind(kind: TargetKind) -> bool:
    if not isinstance(kind, TargetKind):
        raise TypeError("kind must be a TargetKind")
    return kind in _SOURCE_TARGET_KINDS


def format_target_identity(
    target: ValidationTarget,
    *,
    project_id: str | None = None,
) -> str:
    if not isinstance(target, ValidationTarget):
        raise TypeError("target must be a ValidationTarget")
    value = target.value
    if target.kind is TargetKind.PROJECT and value is None:
        if not isinstance(project_id, str):
            raise TypeError("project_id must be a string")
        if not project_id.strip():
            raise ValueError("project_id must not be empty")
        value = project_id
    elif value is None:
        raise ContractViolationError(f"{target.kind.value} target requires an explicit value")
    if not isinstance(value, str):
        raise TypeError("target value must be a string")
    if "\x00" in value:
        raise ValueError("target value must not contain NUL")
    if target.kind in {
        TargetKind.FILE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }:
        value = value.replace("\\", "/")
    return f"{target.kind.value}:{value}"


def canonical_project_relative_target(
    file_path: Path,
    *,
    project_root: Path,
) -> PurePosixPath:
    return _canonical_relative(file_path, root=project_root, role="project_root")


def canonical_source_relative_target(
    file_path: Path,
    *,
    source_root: Path,
) -> PurePosixPath:
    return _canonical_relative(file_path, root=source_root, role="source_root")


def resolve_quick_target(
    target: ValidationTarget | str | Path,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    project, source = _validated_roots(project_root, source_root)
    kind, raw = _coerce_quick_target(target)
    candidate_text = raw
    if kind is TargetKind.MODULE and Path(candidate_text).suffix == "":
        candidate_text += _GF_SUFFIX
    candidate = Path(candidate_text)

    direct_candidates: tuple[Path, ...]
    if candidate.is_absolute() or _WINDOWS_ABSOLUTE_RE.match(candidate_text):
        direct_candidates = (candidate,)
    else:
        direct_candidates = (project / candidate, source / candidate)

    seen: set[str] = set()
    for direct in direct_candidates:
        key = os.path.normcase(os.path.normpath(os.fspath(direct)))
        if key in seen:
            continue
        seen.add(key)
        if _safe_exists(direct):
            return _require_source_file(direct, source_root=source, field="quick target")

    if len(candidate.parts) == 1:
        return _resolve_unique_basename(candidate.name, source_root=source)

    raise ProjectConfigurationError(
        f"Quick target {raw!r} was not found",
        stage="selection",
        operation="resolve_quick_target",
        subject=raw,
    )


def resolve_configured_target(
    target_path: str | Path,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    _project, source = _validated_roots(project_root, source_root)
    raw = _path_text(target_path, field="configured target")
    portable = _portable_source_relative(raw, field="configured target")
    return _require_source_file(
        source.joinpath(*portable.parts),
        source_root=source,
        field="configured target",
    )


def resolve_configured_targets(
    targets: Iterable[str | Path],
    *,
    project_root: Path,
    source_root: Path,
) -> tuple[Path, ...]:
    if isinstance(targets, (str, bytes, Path)):
        raise TypeError("targets must be an iterable of paths")
    result: list[Path] = []
    seen: set[str] = set()
    for target in targets:
        resolved = resolve_configured_target(
            target,
            project_root=project_root,
            source_root=source_root,
        )
        identity = os.path.normcase(os.path.normpath(os.fspath(resolved)))
        if identity not in seen:
            seen.add(identity)
            result.append(resolved)
    return tuple(result)


def resolve_release_targets(
    checkpoints: Iterable[str | Path],
    entrypoints: Iterable[str | Path],
    *,
    project_root: Path,
    source_root: Path,
) -> tuple[Path, ...]:
    combined: list[Path] = []
    seen: set[str] = set()
    for group in (checkpoints, entrypoints):
        for path in resolve_configured_targets(
            group,
            project_root=project_root,
            source_root=source_root,
        ):
            identity = os.path.normcase(os.path.normpath(os.fspath(path)))
            if identity not in seen:
                seen.add(identity)
                combined.append(path)
    return tuple(combined)


def resolve_source_target(
    target: ValidationTarget,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    if not isinstance(target, ValidationTarget):
        raise TypeError("target must be a ValidationTarget")
    if not is_source_target_kind(target.kind):
        raise ContractViolationError(
            f"Target kind {target.kind.value!r} does not resolve to a source file"
        )
    if target.value is None:
        raise ContractViolationError(
            f"Target kind {target.kind.value!r} requires an explicit value"
        )
    if target.kind in {TargetKind.FILE, TargetKind.MODULE}:
        return resolve_quick_target(
            target,
            project_root=project_root,
            source_root=source_root,
        )
    return resolve_configured_target(
        target.value,
        project_root=project_root,
        source_root=source_root,
    )


def _validated_roots(project_root: Path, source_root: Path) -> tuple[Path, Path]:
    project = _absolute_directory(project_root, field="project_root")
    source = _absolute_directory(source_root, field="source_root")
    _contained(source, root=project, field="source_root", allow_root=False)
    return project, source


def _absolute_directory(value: Path, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    if not value.is_absolute():
        raise PathSecurityError(f"{field} must be absolute")
    try:
        resolved = value.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ProjectConfigurationError(f"{field} does not exist: {value}") from exc
    except OSError as exc:
        raise EvidenceIOError(f"Unable to resolve {field}: {value}") from exc
    if not resolved.is_dir():
        raise ProjectConfigurationError(f"{field} is not a directory: {resolved}")
    return resolved


def _canonical_relative(file_path: Path, *, root: Path, role: str) -> PurePosixPath:
    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a Path")
    approved = _absolute_directory(root, field=role)
    if not file_path.is_absolute():
        raise PathSecurityError("file_path must be absolute")
    try:
        resolved = file_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ProjectConfigurationError(f"file_path does not exist: {file_path}") from exc
    except OSError as exc:
        raise EvidenceIOError(f"Unable to resolve file_path: {file_path}") from exc
    _contained(resolved, root=approved, field="file_path", allow_root=False)
    return PurePosixPath(resolved.relative_to(approved).as_posix())


def _contained(path: Path, *, root: Path, field: str, allow_root: bool) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise PathSecurityError(f"{field} escapes the approved root: {path}") from exc
    if not allow_root and not relative.parts:
        raise PathSecurityError(f"{field} must be inside, not equal to, the approved root")


def _coerce_quick_target(target: ValidationTarget | str | Path) -> tuple[TargetKind, str]:
    if isinstance(target, ValidationTarget):
        if target.kind not in {TargetKind.FILE, TargetKind.MODULE}:
            raise ContractViolationError("quick target must use file or module kind")
        if target.value is None:
            raise ContractViolationError("quick target requires an explicit value")
        return target.kind, _path_text(target.value, field="quick target")
    return TargetKind.FILE, _path_text(target, field="quick target")


def _path_text(value: str | Path, *, field: str) -> str:
    if isinstance(value, Path):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise TypeError(f"{field} must be path-like text")
    if not text or "\x00" in text:
        raise ProjectConfigurationError(f"{field} must be a non-empty NUL-free path")
    return text


def _portable_source_relative(value: str, *, field: str) -> PurePosixPath:
    if "\\" in value or _WINDOWS_ABSOLUTE_RE.match(value):
        raise ProjectConfigurationError(f"{field} must use a portable relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ProjectConfigurationError(f"{field} must be a contained relative path")
    if path.suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(f"{field} must end in '.gf'")
    return path


def _require_source_file(candidate: Path, *, source_root: Path, field: str) -> Path:
    if candidate.suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(
            f"{field} must end in '.gf': {candidate}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        )
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ProjectConfigurationError(
            f"{field} does not exist: {candidate}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        ) from exc
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to inspect {field}: {candidate}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        ) from exc
    _contained(resolved, root=source_root, field=field, allow_root=False)
    if not resolved.is_file():
        raise ProjectConfigurationError(
            f"{field} is not a regular file: {resolved}",
            stage="selection",
            operation="resolve_target",
            subject=str(resolved),
        )
    if not os.access(resolved, os.R_OK):
        raise EvidenceIOError(
            f"{field} is not readable: {resolved}",
            stage="selection",
            operation="resolve_target",
            subject=str(resolved),
        )
    return resolved


def _resolve_unique_basename(filename: str, *, source_root: Path) -> Path:
    if Path(filename).suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(
            f"Quick target must end in '.gf': {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    try:
        candidates = sorted(
            (path.resolve() for path in source_root.rglob(filename) if path.is_file()),
            key=lambda path: (
                path.relative_to(source_root).as_posix().casefold(),
                path.relative_to(source_root).as_posix(),
            ),
        )
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to search source_root for {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        ) from exc
    if not candidates:
        raise ProjectConfigurationError(
            f"Quick target {filename!r} was not found",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    if len(candidates) > 1:
        matches = ", ".join(path.relative_to(source_root).as_posix() for path in candidates)
        raise ProjectConfigurationError(
            f"Quick target {filename!r} is ambiguous; matches: {matches}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    return _require_source_file(candidates[0], source_root=source_root, field="quick target")


def _safe_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError as exc:
        raise EvidenceIOError(f"Unable to inspect target path: {path}") from exc


__all__ = (
    "canonical_project_relative_target",
    "canonical_source_relative_target",
    "extract_module_name",
    "format_target_identity",
    "is_source_target_kind",
    "resolve_configured_target",
    "resolve_configured_targets",
    "resolve_quick_target",
    "resolve_release_targets",
    "resolve_source_target",
)
