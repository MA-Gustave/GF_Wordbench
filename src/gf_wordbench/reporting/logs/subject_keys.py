"""Deterministic portable subject keys for GF Wordbench log artifacts."""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.paths import serialize_portable_path, validate_portable_segment

SubjectIdentityInput: TypeAlias = str | os.PathLike[str]

SAFE_KEY_ALGORITHM_VERSION: Final = "1"
MAX_SAFE_KEY_LENGTH: Final = 96
MAX_GENERATED_BASENAME_LENGTH: Final = 120
DEFAULT_HASH_LENGTH: Final = 8
MIN_HASH_LENGTH: Final = 8
MAX_HASH_LENGTH: Final = 64

KNOWN_SUBJECT_EXTENSIONS: Final[tuple[str, ...]] = (
    ".scenario.json",
    ".normalized.txt",
    ".stdout.txt",
    ".stderr.txt",
    ".scan.txt",
    ".out.txt",
    ".err.txt",
    ".gold",
    ".gfs",
    ".gfo",
    ".pgf",
    ".gf",
)

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
_SAFE_KEY_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_HASH_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"--[0-9a-f]{8,64}$"
)
_REPEATED_HYPHEN_RE: Final[re.Pattern[str]] = re.compile(r"-{2,}")
_NAMESPACE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
)


def normalize_subject_identity(
    identity: SubjectIdentityInput,
    *,
    strip_known_extension: bool = True,
    known_extensions: Iterable[str] = KNOWN_SUBJECT_EXTENSIONS,
) -> str:
    """Return the canonical portable identity used to derive a subject key."""

    if type(strip_known_extension) is not bool:
        raise TypeError("strip_known_extension must be a bool")

    canonical = serialize_portable_path(
        identity,
        role="log subject identity",
        allow_root=False,
        accept_backslash=True,
    )
    path = PurePosixPath(canonical)

    if strip_known_extension:
        extensions = _normalize_extensions(known_extensions)
        name = _strip_known_extension(path.name, extensions)
        path = path.with_name(name)

    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ContractViolationError(
            "log subject identity must identify a non-root subject"
        )
    return normalized


def subject_identity_digest(identity: str) -> str:
    """Return the full SHA-256 digest of a canonical subject identity."""

    if not isinstance(identity, str):
        raise TypeError("identity must be a string")
    if identity == "" or "\x00" in identity:
        raise ContractViolationError(
            "identity must be non-empty and contain no NUL characters"
        )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def make_subject_key(
    identity: SubjectIdentityInput,
    *,
    namespace: str | None = None,
    strip_known_extension: bool = True,
    known_extensions: Iterable[str] = KNOWN_SUBJECT_EXTENSIONS,
    force_hash: bool = False,
    hash_length: int = DEFAULT_HASH_LENGTH,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> str:
    """Create one deterministic filename-safe key from a stable identity."""

    if type(force_hash) is not bool:
        raise TypeError("force_hash must be a bool")
    _validate_hash_length(hash_length)
    _validate_max_length(max_length, hash_length=hash_length)

    canonical = normalize_subject_identity(
        identity,
        strip_known_extension=strip_known_extension,
        known_extensions=known_extensions,
    )
    namespace_value = _validate_namespace(namespace)
    hash_identity = (
        canonical
        if namespace_value is None
        else f"{namespace_value}:{canonical}"
    )

    readable, changed = _readable_key(canonical)
    if namespace_value is not None:
        readable = f"{namespace_value}--{readable}"

    needs_hash = (
        force_hash
        or changed
        or "/" in canonical
        or len(readable) > max_length
        or _is_windows_reserved(readable)
    )

    if needs_hash:
        key = _append_hash(
            readable,
            subject_identity_digest(hash_identity),
            hash_length=hash_length,
            max_length=max_length,
        )
    else:
        key = readable

    return validate_subject_key(key, max_length=max_length)


def subject_key_for_path(
    project_relative_path: SubjectIdentityInput,
    *,
    namespace: str | None = None,
    force_hash: bool = False,
    hash_length: int = DEFAULT_HASH_LENGTH,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> str:
    """Create a key from a normalized project-relative path."""

    return make_subject_key(
        project_relative_path,
        namespace=namespace,
        strip_known_extension=True,
        force_hash=force_hash,
        hash_length=hash_length,
        max_length=max_length,
    )


def subject_key_for_id(
    subject_id: str,
    *,
    namespace: str | None = None,
    force_hash: bool = False,
    hash_length: int = DEFAULT_HASH_LENGTH,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> str:
    """Create a key from an already stable logical identifier."""

    return make_subject_key(
        subject_id,
        namespace=namespace,
        strip_known_extension=False,
        force_hash=force_hash,
        hash_length=hash_length,
        max_length=max_length,
    )


def allocate_subject_keys(
    identities: Iterable[SubjectIdentityInput],
    *,
    namespace: str | None = None,
    strip_known_extension: bool = True,
    known_extensions: Iterable[str] = KNOWN_SUBJECT_EXTENSIONS,
    hash_length: int = DEFAULT_HASH_LENGTH,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> Mapping[str, str]:
    """Allocate unique keys for one log namespace in deterministic input order."""

    if isinstance(identities, (str, bytes, os.PathLike)):
        raise TypeError("identities must be an iterable of subject identities")

    _validate_hash_length(hash_length)
    _validate_max_length(max_length, hash_length=hash_length)
    namespace_value = _validate_namespace(namespace)
    extensions = _normalize_extensions(known_extensions)

    canonical_identities: list[str] = []
    seen_identities: set[str] = set()

    for identity in identities:
        canonical = normalize_subject_identity(
            identity,
            strip_known_extension=strip_known_extension,
            known_extensions=extensions,
        )
        if canonical in seen_identities:
            continue
        seen_identities.add(canonical)
        canonical_identities.append(canonical)

    candidates = {
        identity: make_subject_key(
            identity,
            namespace=namespace_value,
            strip_known_extension=False,
            force_hash=False,
            hash_length=hash_length,
            max_length=max_length,
        )
        for identity in canonical_identities
    }

    current_hash_length = hash_length
    while True:
        collisions = _collision_groups(candidates)
        if not collisions:
            break

        if current_hash_length > MAX_HASH_LENGTH:
            raise ContractViolationError(
                "subject-key collisions could not be resolved deterministically"
            )

        for group in collisions:
            for identity in group:
                candidates[identity] = make_subject_key(
                    identity,
                    namespace=namespace_value,
                    strip_known_extension=False,
                    force_hash=True,
                    hash_length=current_hash_length,
                    max_length=max_length,
                )

        if _collision_groups(candidates):
            current_hash_length += 4
            if current_hash_length > MAX_HASH_LENGTH:
                raise ContractViolationError(
                    "subject-key hash space is exhausted"
                )

    return MappingProxyType(
        {identity: candidates[identity] for identity in canonical_identities}
    )


def validate_subject_key(
    key: str,
    *,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> str:
    """Validate and return one generated log-subject key."""

    if not isinstance(key, str):
        raise TypeError("key must be a string")
    if type(max_length) is not int:
        raise TypeError("max_length must be an integer")
    if max_length < 1 or max_length > MAX_GENERATED_BASENAME_LENGTH:
        raise ValueError(
            "max_length must be between 1 and "
            f"{MAX_GENERATED_BASENAME_LENGTH}"
        )
    if key == "":
        raise ContractViolationError("subject key must not be empty")
    if len(key) > max_length:
        raise ContractViolationError(
            f"subject key exceeds the maximum length of {max_length}"
        )
    if not key.isascii():
        raise ContractViolationError(
            "subject key must use portable ASCII characters only"
        )
    if _SAFE_KEY_RE.fullmatch(key) is None:
        raise ContractViolationError(
            "subject key must begin and end with an ASCII letter or digit "
            "and contain only letters, digits, '.', '_', and '-'"
        )
    if key in {".", ".."}:
        raise ContractViolationError(
            "subject key must not be '.' or '..'"
        )
    if _is_windows_reserved(key):
        raise ContractViolationError(
            f"subject key uses a reserved Windows device name: {key!r}"
        )

    validate_portable_segment(key, role="log subject key")
    return key


def is_subject_key(
    value: object,
    *,
    max_length: int = MAX_SAFE_KEY_LENGTH,
) -> bool:
    """Return whether a value satisfies the generated subject-key contract."""

    if not isinstance(value, str):
        return False
    try:
        validate_subject_key(value, max_length=max_length)
    except (ContractViolationError, ValueError, TypeError):
        return False
    return True


def has_hash_suffix(key: str) -> bool:
    """Return whether a key ends with a canonical collision hash suffix."""

    validate_subject_key(key)
    return _HASH_SUFFIX_RE.search(key) is not None


def _normalize_extensions(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("known_extensions must be an iterable of extensions")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("known_extensions must contain strings")
        if (
            len(value) < 2
            or not value.startswith(".")
            or value.endswith(".")
            or "/" in value
            or "\\" in value
            or "\x00" in value
        ):
            raise ValueError(
                f"invalid known subject extension: {value!r}"
            )
        folded = value.casefold()
        if folded not in seen:
            seen.add(folded)
            normalized.append(value)

    normalized.sort(key=lambda item: (-len(item), item.casefold()))
    return tuple(normalized)


def _strip_known_extension(
    name: str,
    extensions: tuple[str, ...],
) -> str:
    folded = name.casefold()
    for extension in extensions:
        if folded.endswith(extension.casefold()):
            stripped = name[: -len(extension)]
            if stripped:
                return stripped
    return name


def _validate_namespace(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("namespace must be a string or None")
    if _NAMESPACE_RE.fullmatch(value) is None:
        raise ContractViolationError(
            "namespace must use lowercase kebab case"
        )
    return value


def _readable_key(identity: str) -> tuple[str, bool]:
    transliterated = unicodedata.normalize("NFKD", identity)
    characters: list[str] = []
    changed = transliterated != identity

    for character in transliterated:
        if character in "/\\":
            characters.append("-")
            changed = True
            continue

        if ord(character) > 127:
            changed = True
            continue

        if character.isalnum() or character in "._-":
            characters.append(character)
            continue

        characters.append("-")
        changed = True

    key = "".join(characters)
    collapsed = _REPEATED_HYPHEN_RE.sub("-", key)
    if collapsed != key:
        changed = True
    key = collapsed.strip("-_.")
    if not key:
        key = "subject"
        changed = True

    if _is_windows_reserved(key):
        key = f"subject-{key}"
        changed = True

    return key, changed


def _append_hash(
    readable: str,
    digest: str,
    *,
    hash_length: int,
    max_length: int,
) -> str:
    suffix = f"--{digest[:hash_length]}"
    prefix_limit = max_length - len(suffix)
    if prefix_limit < 1:
        raise ValueError(
            "max_length leaves no room for a readable subject-key prefix"
        )

    prefix = readable[:prefix_limit].rstrip("-_.")
    if not prefix:
        prefix = "subject"[:prefix_limit].rstrip("-_.")
    if not prefix:
        raise ValueError(
            "max_length is too small for a valid subject key"
        )
    return f"{prefix}{suffix}"


def _collision_groups(
    candidates: Mapping[str, str],
) -> tuple[tuple[str, ...], ...]:
    grouped: dict[str, list[str]] = {}
    for identity, key in candidates.items():
        grouped.setdefault(key.casefold(), []).append(identity)

    groups = [
        tuple(items)
        for items in grouped.values()
        if len(items) > 1
    ]
    groups.sort(key=lambda items: tuple(item.casefold() for item in items))
    return tuple(groups)


def _is_windows_reserved(key: str) -> bool:
    basename = key.split(".", 1)[0].upper()
    return basename in _WINDOWS_RESERVED_BASENAMES


def _validate_hash_length(value: int) -> None:
    if type(value) is not int:
        raise TypeError("hash_length must be an integer")
    if value < MIN_HASH_LENGTH or value > MAX_HASH_LENGTH:
        raise ValueError(
            f"hash_length must be between {MIN_HASH_LENGTH} "
            f"and {MAX_HASH_LENGTH}"
        )


def _validate_max_length(
    value: int,
    *,
    hash_length: int,
) -> None:
    if type(value) is not int:
        raise TypeError("max_length must be an integer")
    minimum = hash_length + 3
    if value < minimum or value > MAX_SAFE_KEY_LENGTH:
        raise ValueError(
            f"max_length must be between {minimum} "
            f"and {MAX_SAFE_KEY_LENGTH}"
        )


safe_subject_key = make_subject_key
build_subject_key_map = allocate_subject_keys


__all__ = (
    "DEFAULT_HASH_LENGTH",
    "KNOWN_SUBJECT_EXTENSIONS",
    "MAX_GENERATED_BASENAME_LENGTH",
    "MAX_HASH_LENGTH",
    "MAX_SAFE_KEY_LENGTH",
    "MIN_HASH_LENGTH",
    "SAFE_KEY_ALGORITHM_VERSION",
    "SubjectIdentityInput",
    "allocate_subject_keys",
    "build_subject_key_map",
    "has_hash_suffix",
    "is_subject_key",
    "make_subject_key",
    "normalize_subject_identity",
    "safe_subject_key",
    "subject_identity_digest",
    "subject_key_for_id",
    "subject_key_for_path",
    "validate_subject_key",
)
