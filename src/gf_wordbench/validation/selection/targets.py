"""Explicit validation-target resolution for GF Wordbench file selection."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Final

from gf_wordbench.config.models import ValidationTarget
from gf_wordbench.kernel.errors import (
    ContractViolationError,
    EvidenceIOError,
    PathSecurityError,
    ProjectConfigurationError,
)
from gf_wordbench.kernel.statuses import TargetKind

_GF_SUFFIX: Final[str] = ".gf"
_SOURCE_TARGET_KINDS: Final[frozenset[TargetKind]] = frozenset(
    {
        TargetKind.FILE,
        TargetKind.MODULE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }
)


def extract_module_name(file_path: Path) -> str:
    """Return the expected GF module name derived from a source filename."""

    path = _require_path_value(file_path, field="file_path")
    if path.name in {"", ".", ".."}:
        raise ValueError("file_path must name a source file")
    if path.suffix.casefold() != _GF_SUFFIX:
        raise ValueError("file_path must end in '.gf'")

    module_name = path.stem
    if not module_name:
        raise ValueError("file_path must have a non-empty module name")
    if "\x00" in module_name:
        raise ValueError("module name must not contain a NUL character")
    return module_name


def is_source_target_kind(kind: TargetKind) -> bool:
    """Return whether a target kind resolves to a GF source file."""

    if not isinstance(kind, TargetKind):
        raise TypeError("kind must be a TargetKind")
    return kind in _SOURCE_TARGET_KINDS


def format_target_identity(
    target: ValidationTarget,
    *,
    project_id: str | None = None,
) -> str:
    """Render the canonical explicit identity of a validation target."""

    if not isinstance(target, ValidationTarget):
        raise TypeError("target must be a ValidationTarget")

    value = target.value
    if target.kind is TargetKind.PROJECT and value is None:
        value = _require_text(project_id, field="project_id")
    elif value is None:
        raise ContractViolationError(
            f"{target.kind.value} target requires an explicit value"
        )

    canonical_value = _canonical_identity_value(target.kind, value)
    return f"{target.kind.value}:{canonical_value}"


def canonical_project_relative_target(
    file_path: Path,
    *,
    project_root: Path,
) -> PurePosixPath:
    """Return a canonical project-relative path for a resolved target."""

    root = _resolve_directory(project_root, field="project_root")
    resolved = _resolve_existing_path(file_path, field="file_path")
    _require_contained(
        resolved,
        root=root,
        field="file_path",
        allow_root=False,
    )
    return PurePosixPath(resolved.relative_to(root).as_posix())


def canonical_source_relative_target(
    file_path: Path,
    *,
    source_root: Path,
) -> PurePosixPath:
    """Return a canonical source-root-relative path for a resolved target."""

    root = _resolve_directory(source_root, field="source_root")
    resolved = _resolve_existing_path(file_path, field="file_path")
    _require_contained(
        resolved,
        root=root,
        field="file_path",
        allow_root=False,
    )
    return PurePosixPath(resolved.relative_to(root).as_posix())


def resolve_quick_target(
    target: ValidationTarget | str | Path,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    """Resolve one quick-mode file or module target through canonical precedence."""

    project, source = _resolve_roots(
        project_root=project_root,
        source_root=source_root,
    )
    target_kind, raw_value = _coerce_quick_target(target)
    target_path = _target_path_value(target_kind, raw_value)

    direct_candidates = _quick_direct_candidates(
        target_path,
        project_root=project,
        source_root=source,
    )
    for candidate in direct_candidates:
        if _path_exists(candidate, field="quick target"):
            return _require_source_file(
                candidate,
                project_root=project,
                source_root=source,
                field="quick target",
            )

    if _is_basename_only(target_path):
        return _resolve_unique_basename(
            target_path.name,
            project_root=project,
            source_root=source,
        )

    raise ProjectConfigurationError(
        f"Quick target was not found: {raw_value!r}",
        stage="selection",
        operation="resolve_quick_target",
        subject=raw_value,
    )


def resolve_configured_target(
    target_path: str | Path,
    *,
    project_root: Path,
    source_root: Path,
    field: str = "configured target",
) -> Path:
    """Resolve one checkpoint or entrypoint as an exact source-relative path."""

    project, source = _resolve_roots(
        project_root=project_root,
        source_root=source_root,
    )
    raw = _require_path_text(target_path, field=field)
    portable = _require_portable_relative_path(raw, field=field)
    candidate = source.joinpath(*portable.parts)
    return _require_source_file(
        candidate,
        project_root=project,
        source_root=source,
        field=field,
    )


def resolve_configured_targets(
    target_paths: Iterable[str | Path],
    *,
    project_root: Path,
    source_root: Path,
    field: str = "configured targets",
) -> tuple[Path, ...]:
    """Resolve an ordered configured target list and deduplicate filesystem identity."""

    if isinstance(target_paths, (str, bytes, Path)):
        raise TypeError(f"{field} must be an iterable of paths")

    project, source = _resolve_roots(
        project_root=project_root,
        source_root=source_root,
    )

    resolved: list[Path] = []
    identities: set[str] = set()
    try:
        iterator = iter(target_paths)
    except TypeError as exc:
        raise TypeError(f"{field} must be an iterable of paths") from exc

    for index, target_path in enumerate(iterator):
        item_field = f"{field}[{index}]"
        candidate = resolve_configured_target(
            target_path,
            project_root=project,
            source_root=source,
            field=item_field,
        )
        identity = _filesystem_identity(candidate)
        if identity in identities:
            continue
        identities.add(identity)
        resolved.append(candidate)

    return tuple(resolved)


def resolve_release_targets(
    checkpoints: Iterable[str | Path],
    entrypoints: Iterable[str | Path],
    *,
    project_root: Path,
    source_root: Path,
) -> tuple[Path, ...]:
    """Resolve the release ordered union: checkpoints, then new entrypoints."""

    checkpoint_targets = resolve_configured_targets(
        checkpoints,
        project_root=project_root,
        source_root=source_root,
        field="checkpoints",
    )
    entrypoint_targets = resolve_configured_targets(
        entrypoints,
        project_root=project_root,
        source_root=source_root,
        field="entrypoints",
    )

    combined: list[Path] = list(checkpoint_targets)
    identities = {_filesystem_identity(path) for path in checkpoint_targets}
    for path in entrypoint_targets:
        identity = _filesystem_identity(path)
        if identity in identities:
            continue
        identities.add(identity)
        combined.append(path)
    return tuple(combined)


def resolve_source_target(
    target: ValidationTarget,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    """Resolve one source-backed typed target without mode inference."""

    if not isinstance(target, ValidationTarget):
        raise TypeError("target must be a ValidationTarget")
    if target.kind not in _SOURCE_TARGET_KINDS:
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
        _target_path_value(target.kind, target.value),
        project_root=project_root,
        source_root=source_root,
        field=f"{target.kind.value} target",
    )


def _coerce_quick_target(
    target: ValidationTarget | str | Path,
) -> tuple[TargetKind, str]:
    if isinstance(target, ValidationTarget):
        if target.kind not in {TargetKind.FILE, TargetKind.MODULE}:
            raise ContractViolationError(
                "quick target must use target kind 'file' or 'module'"
            )
        if target.value is None:
            raise ContractViolationError("quick target requires an explicit value")
        return target.kind, _require_text(target.value, field="quick target")

    return TargetKind.FILE, _require_path_text(target, field="quick target")


def _target_path_value(kind: TargetKind, value: str) -> Path:
    text = _require_text(value, field=f"{kind.value} target")
    path = Path(text)
    if kind is TargetKind.MODULE and path.suffix == "":
        path = path.with_suffix(_GF_SUFFIX)
    return path


def _quick_direct_candidates(
    target_path: Path,
    *,
    project_root: Path,
    source_root: Path,
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if target_path.is_absolute():
        candidates.append(target_path)
    else:
        candidates.append(project_root / target_path)
        candidates.append(source_root / target_path)

    unique: list[Path] = []
    identities: set[str] = set()
    for candidate in candidates:
        identity = _lexical_identity(candidate)
        if identity in identities:
            continue
        identities.add(identity)
        unique.append(candidate)
    return tuple(unique)


def _resolve_unique_basename(
    filename: str,
    *,
    project_root: Path,
    source_root: Path,
) -> Path:
    if Path(filename).suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(
            f"Quick target must name a '.gf' source file: {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )

    try:
        discovered = tuple(source_root.rglob(filename))
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to search the source root for quick target {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        ) from exc

    valid: list[Path] = []
    identities: set[str] = set()
    for candidate in discovered:
        try:
            resolved = _require_source_file(
                candidate,
                project_root=project_root,
                source_root=source_root,
                field="quick basename match",
            )
        except (ProjectConfigurationError, PathSecurityError, EvidenceIOError):
            continue
        identity = _filesystem_identity(resolved)
        if identity in identities:
            continue
        identities.add(identity)
        valid.append(resolved)

    valid.sort(key=lambda path: _portable_sort_key(path, root=source_root))
    if not valid:
        raise ProjectConfigurationError(
            f"Quick target was not found: {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    if len(valid) > 1:
        matches = ", ".join(
            path.relative_to(source_root).as_posix() for path in valid
        )
        raise ProjectConfigurationError(
            f"Quick target {filename!r} is ambiguous; matches: {matches}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    return valid[0]


def _require_source_file(
    candidate: Path,
    *,
    project_root: Path,
    source_root: Path,
    field: str,
) -> Path:
    path = _require_path_value(candidate, field=field)

    if not _path_exists(path, field=field):
        raise ProjectConfigurationError(
            f"{field} does not exist: {path!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(path),
        )
    try:
        is_file = path.is_file()
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to inspect {field}: {path!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(path),
        ) from exc
    if not is_file:
        raise ProjectConfigurationError(
            f"{field} is not a regular file: {path!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(path),
        )
    if path.suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(
            f"{field} must end in '.gf': {path!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(path),
        )

    resolved = _resolve_existing_path(path, field=field)
    _require_contained(
        resolved,
        root=project_root,
        field=field,
        allow_root=False,
    )
    _require_contained(
        resolved,
        root=source_root,
        field=field,
        allow_root=False,
    )

    if not os.access(resolved, os.R_OK):
        raise EvidenceIOError(
            f"{field} is not readable: {resolved!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(resolved),
        )
    return resolved


def _resolve_roots(
    *,
    project_root: Path,
    source_root: Path,
) -> tuple[Path, Path]:
    project = _resolve_directory(project_root, field="project_root")
    source = _resolve_directory(source_root, field="source_root")
    _require_contained(
        source,
        root=project,
        field="source_root",
        allow_root=False,
    )
    return project, source


def _resolve_directory(value: Path, *, field: str) -> Path:
    path = _require_path_value(value, field=field)
    if not path.is_absolute():
        raise ContractViolationError(f"{field} must be absolute")
    if not _path_exists(path, field=field):
        raise ProjectConfigurationError(f"{field} does not exist: {path!s}")
    try:
        if not path.is_dir():
            raise ProjectConfigurationError(f"{field} is not a directory: {path!s}")
    except OSError as exc:
        raise EvidenceIOError(f"Unable to inspect {field}: {path!s}") from exc
    return _resolve_existing_path(path, field=field)


def _resolve_existing_path(value: Path, *, field: str) -> Path:
    path = _require_path_value(value, field=field)
    try:
        return path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ProjectConfigurationError(f"{field} does not exist: {path!s}") from exc
    except (OSError, RuntimeError) as exc:
        raise EvidenceIOError(f"Unable to resolve {field}: {path!s}") from exc


def _require_contained(
    candidate: Path,
    *,
    root: Path,
    field: str,
    allow_root: bool,
) -> None:
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise PathSecurityError(
            f"{field} escapes the approved root {root!s}: {candidate!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        ) from exc
    if not allow_root and not relative.parts:
        raise PathSecurityError(
            f"{field} must be inside, not equal to, the approved root {root!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        )


def _require_portable_relative_path(value: str, *, field: str) -> PurePosixPath:
    text = _require_text(value, field=field)
    if "\\" in text:
        raise ProjectConfigurationError(
            f"{field} must use '/' as the project path separator"
        )
    windows = PureWindowsPath(text)
    portable = PurePosixPath(text)
    if windows.is_absolute() or windows.drive or portable.is_absolute():
        raise ProjectConfigurationError(f"{field} must be source-root-relative")
    if portable in {PurePosixPath("."), PurePosixPath("..")}:
        raise ProjectConfigurationError(f"{field} must name a source file")
    if any(part in {"", ".", ".."} for part in portable.parts):
        raise ProjectConfigurationError(
            f"{field} contains an invalid path segment: {text!r}"
        )
    if portable.suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(f"{field} must end in '.gf': {text!r}")
    return portable


def _canonical_identity_value(kind: TargetKind, value: str) -> str:
    text = _require_text(value, field=f"{kind.value} target value")
    if kind in {TargetKind.FILE, TargetKind.MODULE, TargetKind.CHECKPOINT, TargetKind.ENTRYPOINT}:
        path = PurePath(text)
        if isinstance(path, PureWindowsPath):
            return path.as_posix()
        return text.replace("\\", "/")
    return text


def _require_path_text(value: str | Path, *, field: str) -> str:
    if isinstance(value, Path):
        text = os.fspath(value)
    elif isinstance(value, str):
        text = value
    else:
        raise TypeError(f"{field} must be a string or Path")
    return _require_text(text, field=field)


def _require_path_value(value: Path, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a Path")
    if "\x00" in os.fspath(value):
        raise ValueError(f"{field} must not contain a NUL character")
    return value


def _require_text(value: str | None, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field} must not contain surrounding whitespace")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain a NUL character")
    if "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be a single-line value")
    return value


def _path_exists(path: Path, *, field: str) -> bool:
    try:
        return path.exists()
    except OSError as exc:
        raise EvidenceIOError(f"Unable to inspect {field}: {path!s}") from exc


def _is_basename_only(path: Path) -> bool:
    return not path.is_absolute() and path.parent == Path(".") and path.name not in {"", ".", ".."}


def _filesystem_identity(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _lexical_identity(path: Path) -> str:
    try:
        normalized = path.absolute()
    except OSError:
        normalized = path
    return _filesystem_identity(normalized)


def _portable_sort_key(path: Path, *, root: Path) -> tuple[str, str]:
    relative = path.relative_to(root).as_posix()
    return relative.casefold(), relative


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
