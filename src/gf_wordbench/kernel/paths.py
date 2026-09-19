"""Canonical path primitives for GF Wordbench.

This module owns path syntax, portable serialization, lexical containment, and
platform-aware comparison keys. It deliberately performs no filesystem I/O.
Symlink-, junction-, and reparse-point-aware containment belongs to the
filesystem infrastructure adapter.
"""

from __future__ import annotations

from enum import Enum
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final, TypeAlias

from .errors import ContractViolationError, PathSecurityError

PathInput: TypeAlias = str | os.PathLike[str]


class PathClass(str, Enum):
    """Ownership class of a path field."""

    FRAMEWORK = "framework"
    PROJECT = "project"
    RUN = "run"
    ENVIRONMENT = "environment"
    TEMPORARY = "temporary"
    EXTERNAL_EVIDENCE = "external_evidence"


class ContainmentMode(str, Enum):
    """Whether a candidate may equal its approved root."""

    INSIDE_OR_EQUAL = "inside_or_equal"
    STRICTLY_INSIDE = "strictly_inside"


_WINDOWS_RESERVED_BASENAMES: Final[frozenset[str]] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)
_WINDOWS_INVALID_PORTABLE_CHARACTERS: Final[frozenset[str]] = frozenset('<>:"|?*')
_ENVIRONMENT_EXPRESSION_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:%[^%\r\n]+%|\$\{[^}\r\n]+\}|\$[A-Za-z_][A-Za-z0-9_]*)"
)
_WINDOWS_DRIVE_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


__all__ = [
    "ContainmentMode",
    "PathClass",
    "PathInput",
    "join_portable_path",
    "lexically_contains",
    "normalize_environment_path",
    "normalize_portable_path",
    "path_identity_key",
    "portable_identity_key",
    "relative_portable_path",
    "require_lexical_containment",
    "serialize_environment_path",
    "serialize_portable_path",
    "validate_portable_segment",
]


def normalize_portable_path(
    value: PathInput,
    *,
    role: str = "portable path",
    allow_root: bool = True,
    accept_backslash: bool = True,
) -> PurePosixPath:
    """Return a canonical project- or run-relative path.

    Canonical portable paths use ``/``, preserve case and Unicode, contain no
    unresolved parent traversal, and have no drive or UNC prefix. ``.`` is
    retained only when root equality is explicitly allowed.
    """

    text = _coerce_path_text(value, role=role, trim=False)

    if text.startswith("~") and (len(text) == 1 or text[1] in "/\\"):
        raise ContractViolationError(f"{role} must not use a user-home alias: {text!r}")

    if _ENVIRONMENT_EXPRESSION_RE.search(text):
        raise ContractViolationError(
            f"{role} must not contain an environment-variable expression: {text!r}"
        )

    windows_path = PureWindowsPath(text)
    if windows_path.drive or windows_path.root or _WINDOWS_DRIVE_PREFIX_RE.match(text):
        raise PathSecurityError(f"{role} must be relative and portable: {text!r}")

    if text.startswith(("/", "\\")):
        raise PathSecurityError(f"{role} must not use an absolute or UNC root: {text!r}")

    if "\\" in text:
        if not accept_backslash:
            raise ContractViolationError(
                f"{role} must use '/' separators in canonical form: {text!r}"
            )
        text = text.replace("\\", "/")

    raw_parts = text.split("/")
    if any(part == "" for part in raw_parts):
        raise ContractViolationError(f"{role} contains an empty path segment: {text!r}")

    normalized_parts: list[str] = []
    for part in raw_parts:
        if part == ".":
            continue

        if part == "..":
            raise PathSecurityError(f"{role} contains prohibited parent traversal: {text!r}")

        validate_portable_segment(part, role=role)
        normalized_parts.append(part)

    if not normalized_parts:
        if allow_root:
            return PurePosixPath(".")

        raise ContractViolationError(f"{role} must identify a child path, not the root")

    return PurePosixPath(*normalized_parts)


def serialize_portable_path(
    value: PathInput,
    *,
    role: str = "portable path",
    allow_root: bool = True,
    accept_backslash: bool = True,
) -> str:
    """Serialize a project- or run-relative path with canonical separators."""

    return normalize_portable_path(
        value,
        role=role,
        allow_root=allow_root,
        accept_backslash=accept_backslash,
    ).as_posix()


def normalize_environment_path(
    value: PathInput,
    *,
    base: PathInput | None = None,
    role: str = "environment path",
    expand_user: bool = False,
) -> Path:
    """Return an absolute, lexical runtime path without touching the filesystem.

    Relative values require an explicit absolute ``base``. Inline environment
    interpolation is rejected. User-home expansion is available only when the
    calling boundary explicitly enables it.
    """

    text = _coerce_path_text(value, role=role, trim=True)

    if _ENVIRONMENT_EXPRESSION_RE.search(text):
        raise ContractViolationError(
            f"{role} must not contain an environment-variable expression: {text!r}"
        )

    if expand_user:
        text = os.path.expanduser(text)
    elif text.startswith("~") and (len(text) == 1 or text[1] in "/\\"):
        raise ContractViolationError(
            f"{role} uses a user-home alias but expansion was not explicitly enabled"
        )

    _reject_drive_relative(text, role=role)
    candidate = Path(text)

    if not candidate.is_absolute():
        if base is None:
            raise ContractViolationError(
                f"relative {role} requires an explicit resolution base: {text!r}"
            )

        base_path = _normalize_absolute_base(
            base,
            role=f"{role} base",
        )
        candidate = base_path / candidate

    return Path(os.path.abspath(os.path.normpath(os.fspath(candidate))))


def serialize_environment_path(
    value: PathInput,
    *,
    role: str = "environment path",
) -> str:
    """Serialize an absolute machine-local path with ``/`` separators."""

    text = _coerce_path_text(
        value,
        role=role,
        trim=False,
    )
    _reject_drive_relative(text, role=role)

    path = Path(text)
    if not path.is_absolute():
        raise ContractViolationError(f"{role} must be absolute before serialization: {text!r}")

    return path.as_posix()


def join_portable_path(
    root: PathInput,
    relative: PathInput,
    *,
    role: str = "portable path",
    allow_root: bool = True,
) -> Path:
    """Join a validated portable relative path to an absolute runtime root."""

    root_path = _normalize_absolute_base(
        root,
        role=f"{role} root",
    )
    portable = normalize_portable_path(
        relative,
        role=role,
        allow_root=allow_root,
    )

    if portable == PurePosixPath("."):
        return root_path

    return root_path.joinpath(*portable.parts)


def path_identity_key(
    value: PathInput,
    *,
    role: str = "path",
) -> str:
    """Return a platform-aware lexical identity key for an absolute path."""

    text = _coerce_path_text(
        value,
        role=role,
        trim=False,
    )
    _reject_drive_relative(text, role=role)

    path = Path(text)
    if not path.is_absolute():
        raise ContractViolationError(f"{role} must be absolute for identity comparison")

    return os.path.normcase(os.path.normpath(os.fspath(path)))


def portable_identity_key(
    value: PathInput,
    *,
    role: str = "portable path",
    case_sensitive: bool = True,
) -> str:
    """Return a canonical comparison key for a portable relative path."""

    canonical = serialize_portable_path(
        value,
        role=role,
    )
    return canonical if case_sensitive else canonical.casefold()


def lexically_contains(
    root: PathInput,
    candidate: PathInput,
    *,
    mode: ContainmentMode = ContainmentMode.INSIDE_OR_EQUAL,
) -> bool:
    """Check lexical containment without following symlinks or junctions."""

    root_path = _normalize_absolute_base(
        root,
        role="containment root",
    )
    candidate_path = normalize_environment_path(
        candidate,
        base=root_path,
        role="containment candidate",
    )

    root_key = path_identity_key(
        root_path,
        role="containment root",
    )
    candidate_key = path_identity_key(
        candidate_path,
        role="containment candidate",
    )

    try:
        common = os.path.commonpath(
            (
                root_key,
                candidate_key,
            )
        )
    except ValueError:
        return False

    if common != root_key:
        return False

    if mode is ContainmentMode.STRICTLY_INSIDE and candidate_key == root_key:
        return False

    return True


def require_lexical_containment(
    root: PathInput,
    candidate: PathInput,
    *,
    role: str,
    mode: ContainmentMode = ContainmentMode.INSIDE_OR_EQUAL,
) -> Path:
    """Return the normalized candidate or raise a path-security exception."""

    root_path = _normalize_absolute_base(
        root,
        role=f"{role} root",
    )
    candidate_path = normalize_environment_path(
        candidate,
        base=root_path,
        role=role,
    )

    if not lexically_contains(
        root_path,
        candidate_path,
        mode=mode,
    ):
        raise PathSecurityError(
            f"{role} violates lexical containment: "
            f"candidate={candidate_path!s}, "
            f"root={root_path!s}, "
            f"mode={mode.value}"
        )

    return candidate_path


def relative_portable_path(
    root: PathInput,
    candidate: PathInput,
    *,
    role: str,
    mode: ContainmentMode = ContainmentMode.INSIDE_OR_EQUAL,
) -> PurePosixPath:
    """Relativize a lexically contained runtime path for canonical persistence."""

    root_path = _normalize_absolute_base(
        root,
        role=f"{role} root",
    )
    candidate_path = require_lexical_containment(
        root_path,
        candidate,
        role=role,
        mode=mode,
    )

    relative_text = os.path.relpath(
        candidate_path,
        root_path,
    )
    return normalize_portable_path(
        relative_text,
        role=role,
        allow_root=(mode is ContainmentMode.INSIDE_OR_EQUAL),
    )


def validate_portable_segment(
    segment: str,
    *,
    role: str = "path segment",
) -> str:
    """Validate one cross-platform project/run path segment."""

    if not isinstance(segment, str):
        raise ContractViolationError(f"{role} must be text")

    if segment in {"", ".", ".."}:
        raise ContractViolationError(f"{role} is prohibited: {segment!r}")

    if segment != segment.strip():
        raise ContractViolationError(f"{role} must not begin or end with whitespace")

    if segment.endswith((".", " ")):
        raise ContractViolationError(f"{role} must not end with a dot or space: {segment!r}")

    if any(
        character in segment
        for character in (
            "/",
            "\\",
        )
    ):
        raise ContractViolationError(f"{role} must not contain a path separator: {segment!r}")

    if any(ord(character) < 32 or ord(character) == 127 for character in segment):
        raise ContractViolationError(f"{role} must not contain control characters")

    if any(character in _WINDOWS_INVALID_PORTABLE_CHARACTERS for character in segment):
        raise ContractViolationError(
            f"{role} contains a character that is not portable to Windows: {segment!r}"
        )

    basename = segment.split(".", 1)[0].upper()
    if basename in _WINDOWS_RESERVED_BASENAMES:
        raise ContractViolationError(f"{role} uses a reserved Windows device name: {segment!r}")

    return segment


def _coerce_path_text(
    value: PathInput,
    *,
    role: str,
    trim: bool,
) -> str:
    if isinstance(value, bytes):
        raise ContractViolationError(f"{role} must be text, not bytes")

    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise ContractViolationError(f"{role} must be a string or os.PathLike value") from exc

    if not isinstance(raw, str):
        raise ContractViolationError(f"{role} must resolve to text, not bytes")

    text = raw.strip() if trim else raw

    if text == "":
        raise ContractViolationError(f"{role} must not be empty")

    if "\x00" in text:
        raise PathSecurityError(f"{role} contains a NUL byte")

    return text


def _normalize_absolute_base(
    value: PathInput,
    *,
    role: str,
) -> Path:
    text = _coerce_path_text(
        value,
        role=role,
        trim=True,
    )
    _reject_drive_relative(text, role=role)

    path = Path(text)
    if not path.is_absolute():
        raise ContractViolationError(f"{role} must be absolute: {text!r}")

    return Path(os.path.abspath(os.path.normpath(os.fspath(path))))


def _reject_drive_relative(
    text: str,
    *,
    role: str,
) -> None:
    windows_path = PureWindowsPath(text)
    if windows_path.drive and not windows_path.root:
        raise PathSecurityError(f"{role} must not be drive-relative: {text!r}")
