"""Explicit validation-target resolution for path-resolved language selection.

This module resolves source-backed validation targets inside one validated
language directory. It does not discover the active language, construct the GF
search path, parse GF imports, or load validation profiles.
"""

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
    language_key: str | None = None,
) -> str:
    """Render the canonical explicit identity of a validation target.

    ``TargetKind.PROJECT`` remains a compatibility enum value until the target
    model is migrated. When its value is absent, ``language_key`` supplies the
    resolved portable language identity. The serialized target-kind token stays
    unchanged here so persisted-schema migration remains owned elsewhere.
    """

    if not isinstance(target, ValidationTarget):
        raise TypeError("target must be a ValidationTarget")

    value = target.value
    if target.kind is TargetKind.PROJECT and value is None:
        value = _require_text(language_key, field="language_key")
    elif value is None:
        raise ContractViolationError(
            f"{target.kind.value} target requires an explicit value"
        )

    canonical_value = _canonical_identity_value(target.kind, value)
    return f"{target.kind.value}:{canonical_value}"


def canonical_language_relative_target(
    file_path: Path,
    *,
    language_directory: Path,
) -> PurePosixPath:
    """Return a canonical language-directory-relative target path."""

    language = _resolve_language_directory(language_directory)
    resolved = _resolve_existing_path(file_path, field="file_path")
    _require_contained(
        resolved,
        root=language,
        field="file_path",
        allow_root=False,
    )
    return PurePosixPath(resolved.relative_to(language).as_posix())


# Temporary compatibility aliases.
#
# Both names intentionally refer to the same function object. They do not retain
# the obsolete project-root or source-root contracts; callers must provide the
# canonical ``language_directory`` keyword argument.
canonical_project_relative_target = canonical_language_relative_target
canonical_source_relative_target = canonical_language_relative_target


def resolve_quick_target(
    target: ValidationTarget | str | Path,
    *,
    language_directory: Path,
) -> Path:
    """Resolve one quick-mode file or module inside the active language."""

    language = _resolve_language_directory(language_directory)
    target_kind, raw_value = _coerce_quick_target(target)
    target_path = _target_path_value(target_kind, raw_value)

    for candidate in _quick_direct_candidates(
        target_path,
        language_directory=language,
    ):
        if _path_exists(candidate, field="quick target"):
            return _require_source_file(
                candidate,
                language_directory=language,
                field="quick target",
            )

    if _is_basename_only(target_path):
        return _resolve_unique_basename(
            target_path.name,
            language_directory=language,
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
    language_directory: Path,
    field: str = "configured target",
) -> Path:
    """Resolve one profile target as an exact language-relative path."""

    language = _resolve_language_directory(language_directory)
    raw = _require_path_text(target_path, field=field)
    portable = _require_portable_relative_path(raw, field=field)
    candidate = language.joinpath(*portable.parts)
    return _require_source_file(
        candidate,
        language_directory=language,
        field=field,
    )


def resolve_configured_targets(
    target_paths: Iterable[str | Path],
    *,
    language_directory: Path,
    field: str = "configured targets",
) -> tuple[Path, ...]:
    """Resolve an ordered target list and deduplicate filesystem identity."""

    if isinstance(target_paths, (str, bytes, Path)):
        raise TypeError(f"{field} must be an iterable of paths")

    language = _resolve_language_directory(language_directory)

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
            language_directory=language,
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
    language_directory: Path,
) -> tuple[Path, ...]:
    """Resolve the release ordered union: checkpoints, then new entrypoints."""

    checkpoint_targets = resolve_configured_targets(
        checkpoints,
        language_directory=language_directory,
        field="checkpoints",
    )
    entrypoint_targets = resolve_configured_targets(
        entrypoints,
        language_directory=language_directory,
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
    language_directory: Path,
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
            language_directory=language_directory,
        )

    return resolve_configured_target(
        _target_path_value(target.kind, target.value),
        language_directory=language_directory,
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
    language_directory: Path,
) -> tuple[Path, ...]:
    if target_path.is_absolute():
        return (target_path,)
    return (language_directory / target_path,)


def _resolve_unique_basename(
    filename: str,
    *,
    language_directory: Path,
) -> Path:
    if Path(filename).suffix.casefold() != _GF_SUFFIX:
        raise ProjectConfigurationError(
            f"Quick target must name a '.gf' source file: {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )

    try:
        discovered = tuple(language_directory.rglob(filename))
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to search the language directory for quick target {filename!r}",
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
                language_directory=language_directory,
                field="quick basename match",
            )
        except (ProjectConfigurationError, PathSecurityError, EvidenceIOError):
            continue
        identity = _filesystem_identity(resolved)
        if identity in identities:
            continue
        identities.add(identity)
        valid.append(resolved)

    valid.sort(
        key=lambda path: _portable_sort_key(
            path,
            root=language_directory,
        )
    )
    if not valid:
        raise ProjectConfigurationError(
            f"Quick target was not found: {filename!r}",
            stage="selection",
            operation="resolve_quick_target",
            subject=filename,
        )
    if len(valid) > 1:
        matches = ", ".join(
            path.relative_to(language_directory).as_posix() for path in valid
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
    language_directory: Path,
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
        root=language_directory,
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


def _resolve_language_directory(value: Path) -> Path:
    return _resolve_directory(value, field="language_directory")


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
            f"{field} escapes the approved language directory {root!s}: "
            f"{candidate!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        ) from exc
    if not allow_root and not relative.parts:
        raise PathSecurityError(
            f"{field} must be inside, not equal to, the approved language "
            f"directory {root!s}",
            stage="selection",
            operation="resolve_target",
            subject=str(candidate),
        )


def _require_portable_relative_path(value: str, *, field: str) -> PurePosixPath:
    text = _require_text(value, field=field)
    if "\\" in text:
        raise ProjectConfigurationError(
            f"{field} must use '/' as the portable path separator"
        )
    windows = PureWindowsPath(text)
    portable = PurePosixPath(text)
    if windows.is_absolute() or windows.drive or portable.is_absolute():
        raise ProjectConfigurationError(
            f"{field} must be language-directory-relative"
        )
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
    if kind in {
        TargetKind.FILE,
        TargetKind.MODULE,
        TargetKind.CHECKPOINT,
        TargetKind.ENTRYPOINT,
    }:
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
    return (
        not path.is_absolute()
        and path.parent == Path(".")
        and path.name not in {"", ".", ".."}
    )


def _filesystem_identity(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _portable_sort_key(path: Path, *, root: Path) -> tuple[str, str]:
    relative = path.relative_to(root).as_posix()
    return relative.casefold(), relative


__all__ = (
    "canonical_language_relative_target",
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
