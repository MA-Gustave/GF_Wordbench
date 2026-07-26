from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Final, TypeAlias

APPLICATION_JSON: Final[str] = "application/json"
TEXT_MARKDOWN_UTF8: Final[str] = "text/markdown; charset=utf-8"
TEXT_PLAIN_UTF8: Final[str] = "text/plain; charset=utf-8"
APPLICATION_OCTET_STREAM: Final[str] = "application/octet-stream"

MANIFEST_MEDIA_TYPE_INVALID: Final[str] = "MANIFEST_MEDIA_TYPE_INVALID"
MANIFEST_ROLE_UNKNOWN: Final[str] = "MANIFEST_ROLE_UNKNOWN"

_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$"
)
_MEDIA_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<type>[!#$%&'*+.^_`|~0-9A-Za-z-]+)/"
    r"(?P<subtype>[!#$%&'*+.^_`|~0-9A-Za-z-]+)$"
)
_MAX_MEDIA_TYPE_LENGTH: Final[int] = 512
_MAX_PARAMETERS: Final[int] = 16

RoleLike: TypeAlias = str | StrEnum
PathLike: TypeAlias = str | Path | PurePosixPath


@unique
class ArtifactMediaType(StrEnum):
    JSON = APPLICATION_JSON
    MARKDOWN_UTF8 = TEXT_MARKDOWN_UTF8
    PLAIN_TEXT_UTF8 = TEXT_PLAIN_UTF8
    OCTET_STREAM = APPLICATION_OCTET_STREAM


@unique
class MediaTypeFamily(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    BINARY = "binary"
    OTHER = "other"


class MediaTypeContractError(ValueError):
    __slots__ = ("code", "role", "media_type")

    def __init__(
        self,
        message: str,
        *,
        code: str = MANIFEST_MEDIA_TYPE_INVALID,
        role: str | None = None,
        media_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.role = role
        self.media_type = media_type


@dataclass(frozen=True, slots=True)
class ParsedMediaType:
    type: str
    subtype: str
    parameters: Mapping[str, str]

    def __post_init__(self) -> None:
        major = _normalize_token(self.type, field="media type")
        subtype = _normalize_token(self.subtype, field="media subtype")
        parameters = _freeze_parameters(self.parameters)
        object.__setattr__(self, "type", major)
        object.__setattr__(self, "subtype", subtype)
        object.__setattr__(self, "parameters", parameters)

    @property
    def essence(self) -> str:
        return f"{self.type}/{self.subtype}"

    @property
    def charset(self) -> str | None:
        return self.parameters.get("charset")

    def render(self) -> str:
        if not self.parameters:
            return self.essence
        suffix = "; ".join(
            f"{name}={value}" for name, value in self.parameters.items()
        )
        return f"{self.essence}; {suffix}"


@dataclass(frozen=True, slots=True)
class RoleMediaTypePolicy:
    role: str
    canonical_media_type: str | None
    allowed_media_types: frozenset[str]
    allowed_suffixes: frozenset[str]
    require_known_media_type: bool = True

    def __post_init__(self) -> None:
        role = normalize_role(self.role)
        canonical = self.canonical_media_type
        if canonical is not None:
            canonical = normalize_media_type(canonical)
        allowed = frozenset(normalize_media_type(value) for value in self.allowed_media_types)
        suffixes = frozenset(_normalize_suffix(value) for value in self.allowed_suffixes)
        if canonical is not None and canonical not in allowed:
            raise ValueError("canonical_media_type must be allowed")
        if type(self.require_known_media_type) is not bool:
            raise TypeError("require_known_media_type must be bool")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "canonical_media_type", canonical)
        object.__setattr__(self, "allowed_media_types", allowed)
        object.__setattr__(self, "allowed_suffixes", suffixes)

    def accepts(
        self,
        media_type: str | ArtifactMediaType,
        *,
        path: PathLike | None = None,
        check_suffix: bool = True,
    ) -> bool:
        try:
            validate_media_type(
                self.role,
                media_type,
                path=path,
                check_suffix=check_suffix,
            )
        except (TypeError, ValueError):
            return False
        return True


_JSON_SUFFIXES: Final[frozenset[str]] = frozenset({".json"})
_MARKDOWN_SUFFIXES: Final[frozenset[str]] = frozenset({".md", ".markdown"})
_TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".txt", ".log", ".out", ".err", ".diff"}
)
_DETAIL_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".txt", ".log", ".md", ".markdown", ".out", ".err", ".diff"}
)
_GFO_SUFFIXES: Final[frozenset[str]] = frozenset({".gfo"})
_PGF_SUFFIXES: Final[frozenset[str]] = frozenset({".pgf"})


def _policy(
    role: str,
    canonical: str | None,
    allowed: Iterable[str],
    suffixes: Iterable[str],
    *,
    require_known: bool = True,
) -> RoleMediaTypePolicy:
    return RoleMediaTypePolicy(
        role=role,
        canonical_media_type=canonical,
        allowed_media_types=frozenset(allowed),
        allowed_suffixes=frozenset(suffixes),
        require_known_media_type=require_known,
    )


def parse_media_type(value: str | ArtifactMediaType) -> ParsedMediaType:
    raw = _coerce_media_type_text(value)
    parts = _split_parameters(raw)
    match = _MEDIA_TYPE_RE.fullmatch(parts[0].strip())
    if match is None:
        raise MediaTypeContractError(
            f"invalid media type {raw!r}",
            media_type=raw,
        )

    parameters: dict[str, str] = {}
    for part in parts[1:]:
        if not part.strip():
            raise MediaTypeContractError(
                f"invalid empty media-type parameter in {raw!r}",
                media_type=raw,
            )
        if "=" not in part:
            raise MediaTypeContractError(
                f"invalid media-type parameter {part.strip()!r}",
                media_type=raw,
            )
        name, parameter_value = part.split("=", 1)
        name = _normalize_token(name.strip(), field="media-type parameter")
        parameter_value = _normalize_parameter_value(
            parameter_value.strip(),
            field=name,
        )
        if name in parameters:
            raise MediaTypeContractError(
                f"duplicate media-type parameter {name!r}",
                media_type=raw,
            )
        parameters[name] = parameter_value
        if len(parameters) > _MAX_PARAMETERS:
            raise MediaTypeContractError(
                "too many media-type parameters",
                media_type=raw,
            )

    return ParsedMediaType(
        type=match.group("type"),
        subtype=match.group("subtype"),
        parameters=parameters,
    )


def normalize_media_type(value: str | ArtifactMediaType) -> str:
    parsed = parse_media_type(value)
    parameters = dict(parsed.parameters)
    if "charset" in parameters:
        charset = parameters["charset"].replace("_", "-").lower()
        if charset in {"utf8", "utf-8"}:
            parameters["charset"] = "utf-8"
    return ParsedMediaType(
        type=parsed.type,
        subtype=parsed.subtype,
        parameters=parameters,
    ).render()


def normalize_role(role: RoleLike) -> str:
    value = getattr(role, "value", role)
    if not isinstance(value, str):
        raise TypeError("role must be a string or string enum")
    normalized = value.strip().lower().replace("-", "_")
    if not normalized or "\x00" in normalized:
        raise ValueError("role must be non-empty and contain no NUL")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", normalized):
        raise ValueError(f"invalid artifact role {value!r}")
    return normalized


def media_type_policy_for_role(role: RoleLike) -> RoleMediaTypePolicy:
    canonical_role = normalize_role(role)
    try:
        return ROLE_MEDIA_TYPE_POLICIES[canonical_role]
    except KeyError as exc:
        raise MediaTypeContractError(
            f"unknown manifest artifact role {canonical_role!r}",
            code=MANIFEST_ROLE_UNKNOWN,
            role=canonical_role,
        ) from exc


def canonical_media_type_for_role(
    role: RoleLike,
    *,
    path: PathLike | None = None,
) -> str:
    policy = media_type_policy_for_role(role)
    if policy.canonical_media_type is not None:
        if path is not None and policy.role == "detail":
            suffix = artifact_suffix(path)
            if suffix in _MARKDOWN_SUFFIXES:
                return TEXT_MARKDOWN_UTF8
        return policy.canonical_media_type
    if path is None:
        raise MediaTypeContractError(
            "role 'other' requires an explicit media type or a recognized path",
            role=policy.role,
        )
    inferred = media_type_for_path(path)
    if inferred is None:
        raise MediaTypeContractError(
            f"cannot determine a stable media type for {str(path)!r}",
            role=policy.role,
        )
    return inferred


def allowed_media_types_for_role(role: RoleLike) -> frozenset[str]:
    return media_type_policy_for_role(role).allowed_media_types


def media_type_for_path(path: PathLike) -> str | None:
    suffix = artifact_suffix(path)
    if suffix == ".json":
        return APPLICATION_JSON
    if suffix in _MARKDOWN_SUFFIXES:
        return TEXT_MARKDOWN_UTF8
    if suffix in _TEXT_SUFFIXES:
        return TEXT_PLAIN_UTF8
    if suffix in _GFO_SUFFIXES or suffix in _PGF_SUFFIXES:
        return APPLICATION_OCTET_STREAM
    return None


def validate_media_type(
    role: RoleLike,
    media_type: str | ArtifactMediaType,
    *,
    path: PathLike | None = None,
    check_suffix: bool = True,
) -> str:
    canonical_role = normalize_role(role)
    policy = media_type_policy_for_role(canonical_role)
    normalized = normalize_media_type(media_type)
    parsed = parse_media_type(normalized)

    _validate_canonical_parameters(parsed, role=canonical_role)

    if policy.require_known_media_type:
        if normalized not in policy.allowed_media_types:
            allowed = ", ".join(sorted(policy.allowed_media_types))
            raise MediaTypeContractError(
                f"media type {normalized!r} is incompatible with role "
                f"{canonical_role!r}; expected {allowed}",
                role=canonical_role,
                media_type=normalized,
            )
    elif normalized not in policy.allowed_media_types:
        _validate_stable_other_media_type(parsed)

    if path is not None and check_suffix:
        validate_media_type_path_consistency(
            canonical_role,
            normalized,
            path,
        )

    return normalized


def validate_role_media_type(
    role: RoleLike,
    media_type: str | ArtifactMediaType,
    *,
    path: PathLike | None = None,
    check_suffix: bool = True,
) -> str:
    return validate_media_type(
        role,
        media_type,
        path=path,
        check_suffix=check_suffix,
    )


def validate_media_type_path_consistency(
    role: RoleLike,
    media_type: str | ArtifactMediaType,
    path: PathLike,
) -> None:
    canonical_role = normalize_role(role)
    policy = media_type_policy_for_role(canonical_role)
    normalized = normalize_media_type(media_type)
    suffix = artifact_suffix(path)

    if policy.allowed_suffixes and suffix not in policy.allowed_suffixes:
        allowed = ", ".join(sorted(policy.allowed_suffixes))
        raise MediaTypeContractError(
            f"artifact path {str(path)!r} is incompatible with role "
            f"{canonical_role!r}; expected suffix {allowed}",
            role=canonical_role,
            media_type=normalized,
        )

    inferred = media_type_for_path(path)
    if inferred is not None and not _path_media_type_compatible(
        canonical_role,
        normalized,
        inferred,
    ):
        raise MediaTypeContractError(
            f"artifact path {str(path)!r} implies {inferred!r}, not "
            f"{normalized!r}",
            role=canonical_role,
            media_type=normalized,
        )


def is_media_type_compatible(
    role: RoleLike,
    media_type: str | ArtifactMediaType,
    *,
    path: PathLike | None = None,
    check_suffix: bool = True,
) -> bool:
    try:
        validate_media_type(
            role,
            media_type,
            path=path,
            check_suffix=check_suffix,
        )
    except (TypeError, ValueError):
        return False
    return True


def is_supported_media_type(media_type: str | ArtifactMediaType) -> bool:
    try:
        normalized = normalize_media_type(media_type)
    except (TypeError, ValueError):
        return False
    return normalized in CANONICAL_MEDIA_TYPES


def is_text_media_type(media_type: str | ArtifactMediaType) -> bool:
    try:
        parsed = parse_media_type(normalize_media_type(media_type))
    except (TypeError, ValueError):
        return False
    return parsed.type == "text"


def is_binary_media_type(media_type: str | ArtifactMediaType) -> bool:
    try:
        normalized = normalize_media_type(media_type)
    except (TypeError, ValueError):
        return False
    return normalized == APPLICATION_OCTET_STREAM


def media_type_family(
    media_type: str | ArtifactMediaType,
) -> MediaTypeFamily:
    normalized = normalize_media_type(media_type)
    if normalized == APPLICATION_JSON:
        return MediaTypeFamily.JSON
    if normalized == TEXT_MARKDOWN_UTF8:
        return MediaTypeFamily.MARKDOWN
    if normalized == TEXT_PLAIN_UTF8:
        return MediaTypeFamily.PLAIN_TEXT
    if normalized == APPLICATION_OCTET_STREAM:
        return MediaTypeFamily.BINARY
    return MediaTypeFamily.OTHER


def artifact_suffix(path: PathLike) -> str:
    if isinstance(path, Path):
        name = path.name
    elif isinstance(path, PurePosixPath):
        name = path.name
    elif isinstance(path, str):
        if not path or "\x00" in path:
            raise ValueError("path must be non-empty and contain no NUL")
        name = PurePosixPath(path.replace("\\", "/")).name
    else:
        raise TypeError("path must be str or pathlib path")
    return Path(name).suffix.lower()


def _validate_canonical_parameters(
    parsed: ParsedMediaType,
    *,
    role: str,
) -> None:
    if parsed.essence in {"text/plain", "text/markdown"}:
        if parsed.parameters != {"charset": "utf-8"}:
            raise MediaTypeContractError(
                f"UTF-8 text media type for role {role!r} must declare "
                "exactly charset=utf-8",
                role=role,
                media_type=parsed.render(),
            )
        return
    if parsed.essence in {APPLICATION_JSON, APPLICATION_OCTET_STREAM}:
        if parsed.parameters:
            raise MediaTypeContractError(
                f"media type {parsed.essence!r} must not declare parameters",
                role=role,
                media_type=parsed.render(),
            )


def _validate_stable_other_media_type(parsed: ParsedMediaType) -> None:
    if parsed.type == "text" and parsed.charset != "utf-8":
        raise MediaTypeContractError(
            "text artifacts under role 'other' must declare charset=utf-8",
            role="other",
            media_type=parsed.render(),
        )
    if parsed.charset is not None and parsed.type != "text":
        raise MediaTypeContractError(
            "charset is permitted only for text media types",
            role="other",
            media_type=parsed.render(),
        )


def _path_media_type_compatible(
    role: str,
    declared: str,
    inferred: str,
) -> bool:
    if role == "detail":
        return declared in {TEXT_PLAIN_UTF8, TEXT_MARKDOWN_UTF8}
    if role == "other":
        return declared == inferred
    return declared == inferred


def _coerce_media_type_text(value: str | ArtifactMediaType) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise TypeError("media_type must be a string or ArtifactMediaType")
    if not raw.strip():
        raise MediaTypeContractError("media_type must not be empty")
    if "\x00" in raw:
        raise MediaTypeContractError("media_type must not contain NUL")
    if len(raw) > _MAX_MEDIA_TYPE_LENGTH:
        raise MediaTypeContractError("media_type exceeds the supported length")
    return raw.strip()


def _split_parameters(value: str) -> tuple[str, ...]:
    parts: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for character in value:
        if escaped:
            current.append(character)
            escaped = False
            continue
        if character == "\\" and quoted:
            current.append(character)
            escaped = True
            continue
        if character == '"':
            quoted = not quoted
            current.append(character)
            continue
        if character == ";" and not quoted:
            parts.append("".join(current))
            current = []
            continue
        current.append(character)
    if quoted or escaped:
        raise MediaTypeContractError("unterminated quoted media-type parameter")
    parts.append("".join(current))
    return tuple(parts)


def _normalize_token(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if not normalized or _TOKEN_RE.fullmatch(normalized) is None:
        raise MediaTypeContractError(f"invalid {field} {value!r}")
    return normalized


def _normalize_parameter_value(value: str, *, field: str) -> str:
    if value.startswith('"'):
        if len(value) < 2 or not value.endswith('"'):
            raise MediaTypeContractError(
                f"unterminated quoted value for parameter {field!r}"
            )
        value = _unquote(value[1:-1])
    elif _TOKEN_RE.fullmatch(value) is None:
        raise MediaTypeContractError(
            f"invalid value for media-type parameter {field!r}"
        )
    normalized = value.strip().lower()
    if not normalized or "\x00" in normalized:
        raise MediaTypeContractError(
            f"invalid value for media-type parameter {field!r}"
        )
    return normalized


def _unquote(value: str) -> str:
    result: list[str] = []
    escaped = False
    for character in value:
        if escaped:
            result.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        else:
            result.append(character)
    if escaped:
        raise MediaTypeContractError("unterminated quoted escape")
    return "".join(result)


def _freeze_parameters(values: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError("parameters must be a mapping")
    if len(values) > _MAX_PARAMETERS:
        raise ValueError("parameters exceeds the supported item limit")
    copied: dict[str, str] = {}
    for name, value in values.items():
        normalized_name = _normalize_token(name, field="parameter name")
        normalized_value = _normalize_parameter_value(
            value,
            field=normalized_name,
        )
        if normalized_name in copied:
            raise ValueError(f"duplicate parameter {normalized_name!r}")
        copied[normalized_name] = normalized_value
    return MappingProxyType(dict(sorted(copied.items())))


def _normalize_suffix(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("suffix must be a string")
    normalized = value.strip().lower()
    if not normalized.startswith(".") or len(normalized) < 2:
        raise ValueError(f"invalid suffix {value!r}")
    if any(character in normalized for character in ("/", "\\", "\x00")):
        raise ValueError(f"invalid suffix {value!r}")
    return normalized


ROLE_MEDIA_TYPE_POLICIES: Final[Mapping[str, RoleMediaTypePolicy]] = (
    MappingProxyType(
        {
            "machine_summary": _policy(
                "machine_summary",
                APPLICATION_JSON,
                (APPLICATION_JSON,),
                _JSON_SUFFIXES,
            ),
            "human_summary": _policy(
                "human_summary",
                TEXT_MARKDOWN_UTF8,
                (TEXT_MARKDOWN_UTF8,),
                _MARKDOWN_SUFFIXES,
            ),
            "ai_handoff": _policy(
                "ai_handoff",
                TEXT_MARKDOWN_UTF8,
                (TEXT_MARKDOWN_UTF8,),
                _MARKDOWN_SUFFIXES,
            ),
            "top_errors": _policy(
                "top_errors",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "master_log": _policy(
                "master_log",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "aggregate_log": _policy(
                "aggregate_log",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "scan_log": _policy(
                "scan_log",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "compile_stdout": _policy(
                "compile_stdout",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "compile_stderr": _policy(
                "compile_stderr",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "scenario_stdout": _policy(
                "scenario_stdout",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "scenario_stderr": _policy(
                "scenario_stderr",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "scenario_output": _policy(
                "scenario_output",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8,),
                _TEXT_SUFFIXES,
            ),
            "detail": _policy(
                "detail",
                TEXT_PLAIN_UTF8,
                (TEXT_PLAIN_UTF8, TEXT_MARKDOWN_UTF8),
                _DETAIL_SUFFIXES,
            ),
            "gfo": _policy(
                "gfo",
                APPLICATION_OCTET_STREAM,
                (APPLICATION_OCTET_STREAM,),
                _GFO_SUFFIXES,
            ),
            "pgf": _policy(
                "pgf",
                APPLICATION_OCTET_STREAM,
                (APPLICATION_OCTET_STREAM,),
                _PGF_SUFFIXES,
            ),
            "other": _policy(
                "other",
                None,
                (
                    APPLICATION_JSON,
                    TEXT_MARKDOWN_UTF8,
                    TEXT_PLAIN_UTF8,
                    APPLICATION_OCTET_STREAM,
                ),
                (),
                require_known=False,
            ),
        }
    )
)

CANONICAL_MEDIA_TYPES: Final[frozenset[str]] = frozenset(
    media_type.value for media_type in ArtifactMediaType
)

MEDIA_TYPE_BY_ROLE: Final[Mapping[str, str | None]] = MappingProxyType(
    {
        role: policy.canonical_media_type
        for role, policy in ROLE_MEDIA_TYPE_POLICIES.items()
    }
)

ALLOWED_MEDIA_TYPES_BY_ROLE: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        role: policy.allowed_media_types
        for role, policy in ROLE_MEDIA_TYPE_POLICIES.items()
    }
)


__all__ = (
    "ALLOWED_MEDIA_TYPES_BY_ROLE",
    "APPLICATION_JSON",
    "APPLICATION_OCTET_STREAM",
    "ArtifactMediaType",
    "CANONICAL_MEDIA_TYPES",
    "MANIFEST_MEDIA_TYPE_INVALID",
    "MANIFEST_ROLE_UNKNOWN",
    "MEDIA_TYPE_BY_ROLE",
    "MediaTypeContractError",
    "MediaTypeFamily",
    "ParsedMediaType",
    "ROLE_MEDIA_TYPE_POLICIES",
    "RoleMediaTypePolicy",
    "TEXT_MARKDOWN_UTF8",
    "TEXT_PLAIN_UTF8",
    "allowed_media_types_for_role",
    "artifact_suffix",
    "canonical_media_type_for_role",
    "is_binary_media_type",
    "is_media_type_compatible",
    "is_supported_media_type",
    "is_text_media_type",
    "media_type_family",
    "media_type_for_path",
    "media_type_policy_for_role",
    "normalize_media_type",
    "normalize_role",
    "parse_media_type",
    "validate_media_type",
    "validate_media_type_path_consistency",
    "validate_role_media_type",
)
