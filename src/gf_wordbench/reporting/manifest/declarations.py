"""Structured artifact declarations for GF Wordbench manifests."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from types import MappingProxyType
from typing import Final, TypeAlias


@unique
class ArtifactRole(StrEnum):
    MACHINE_SUMMARY = "machine_summary"
    HUMAN_SUMMARY = "human_summary"
    AI_HANDOFF = "ai_handoff"
    TOP_ERRORS = "top_errors"
    MASTER_LOG = "master_log"
    AGGREGATE_LOG = "aggregate_log"
    SCAN_LOG = "scan_log"
    COMPILE_STDOUT = "compile_stdout"
    COMPILE_STDERR = "compile_stderr"
    SCENARIO_STDOUT = "scenario_stdout"
    SCENARIO_STDERR = "scenario_stderr"
    SCENARIO_OUTPUT = "scenario_output"
    DETAIL = "detail"
    GFO = "gfo"
    PGF = "pgf"
    OTHER = "other"


@unique
class ArtifactProducer(StrEnum):
    REPORTING_JSON = "reporting_json"
    REPORTING_MARKDOWN = "reporting_markdown"
    REPORTING_AI_READY = "reporting_ai_ready"
    REPORTING_LOGS = "reporting_logs"
    REPORTING_DETAILS = "reporting_details"
    RUNS = "runs"
    VALIDATION_SCANNER = "validation_scanner"
    VALIDATION_COMPILER = "validation_compiler"
    VALIDATION_SCENARIO = "validation_scenario"
    VALIDATION_NORMALIZER = "validation_normalizer"
    VALIDATION_PGF = "validation_pgf"
    GF = "gf"


APPLICATION_JSON: Final[str] = "application/json"
TEXT_MARKDOWN_UTF8: Final[str] = "text/markdown; charset=utf-8"
TEXT_PLAIN_UTF8: Final[str] = "text/plain; charset=utf-8"
APPLICATION_OCTET_STREAM: Final[str] = "application/octet-stream"

MANIFEST_FILENAME: Final[str] = "manifest.json"

_ROLE_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_PRODUCER_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_MEDIA_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+"
    r"(?:\s*;\s*[A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+\-\"]+)*$"
)

_ALLOWED_MEDIA_TYPES: Final[Mapping[ArtifactRole, frozenset[str]]] = MappingProxyType(
    {
        ArtifactRole.MACHINE_SUMMARY: frozenset({APPLICATION_JSON}),
        ArtifactRole.HUMAN_SUMMARY: frozenset({TEXT_MARKDOWN_UTF8}),
        ArtifactRole.AI_HANDOFF: frozenset({TEXT_MARKDOWN_UTF8}),
        ArtifactRole.TOP_ERRORS: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.MASTER_LOG: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.AGGREGATE_LOG: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.SCAN_LOG: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.COMPILE_STDOUT: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.COMPILE_STDERR: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.SCENARIO_STDOUT: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.SCENARIO_STDERR: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.SCENARIO_OUTPUT: frozenset({TEXT_PLAIN_UTF8}),
        ArtifactRole.DETAIL: frozenset({TEXT_MARKDOWN_UTF8, TEXT_PLAIN_UTF8}),
        ArtifactRole.GFO: frozenset({APPLICATION_OCTET_STREAM}),
        ArtifactRole.PGF: frozenset({APPLICATION_OCTET_STREAM}),
        ArtifactRole.OTHER: frozenset(
            {
                APPLICATION_JSON,
                TEXT_MARKDOWN_UTF8,
                TEXT_PLAIN_UTF8,
                APPLICATION_OCTET_STREAM,
            }
        ),
    }
)

_CANONICAL_PATHS: Final[Mapping[ArtifactRole, tuple[str, ...]]] = MappingProxyType(
    {
        ArtifactRole.MACHINE_SUMMARY: ("summary.json",),
        ArtifactRole.HUMAN_SUMMARY: ("summary.md",),
        ArtifactRole.AI_HANDOFF: ("AI_READY.md",),
        ArtifactRole.TOP_ERRORS: ("top_errors.txt",),
        ArtifactRole.MASTER_LOG: ("raw/master.log",),
        ArtifactRole.AGGREGATE_LOG: (
            "raw/ALL_LOGS.TXT",
            "raw/ALL_SCAN_LOGS.TXT",
        ),
    }
)

_DEFAULT_MEDIA_TYPES: Final[Mapping[ArtifactRole, str]] = MappingProxyType(
    {
        role: next(iter(media_types))
        for role, media_types in _ALLOWED_MEDIA_TYPES.items()
        if len(media_types) == 1
    }
)

ArtifactRoleLike: TypeAlias = ArtifactRole | str
ArtifactProducerLike: TypeAlias = ArtifactProducer | str


@dataclass(frozen=True, slots=True)
class ArtifactDeclaration:
    path: Path
    role: str
    media_type: str
    required: bool
    created_by: str

    def __post_init__(self) -> None:
        path = _require_path(self.path)
        role = normalize_artifact_role(self.role)
        media_type = normalize_media_type(self.media_type)
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        created_by = normalize_artifact_producer(self.created_by)
        _validate_role_media_type(role, media_type)
        _validate_fixed_path(role, path)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "role", role.value)
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(self, "created_by", created_by)

    @property
    def role_id(self) -> ArtifactRole:
        return ArtifactRole(self.role)

    @property
    def producer_id(self) -> ArtifactProducer | None:
        try:
            return ArtifactProducer(self.created_by)
        except ValueError:
            return None

    def with_required(self, required: bool) -> ArtifactDeclaration:
        if type(required) is not bool:
            raise TypeError("required must be a boolean")
        if required is self.required:
            return self
        return ArtifactDeclaration(
            path=self.path,
            role=self.role,
            media_type=self.media_type,
            required=required,
            created_by=self.created_by,
        )


@dataclass(frozen=True, slots=True)
class ArtifactDeclarationSet:
    declarations: tuple[ArtifactDeclaration, ...]

    def __post_init__(self) -> None:
        prepared = validate_artifact_declarations(self.declarations)
        object.__setattr__(self, "declarations", prepared)

    def __iter__(self) -> Iterator[ArtifactDeclaration]:
        return iter(self.declarations)

    def __len__(self) -> int:
        return len(self.declarations)

    def by_path(self) -> Mapping[str, ArtifactDeclaration]:
        return MappingProxyType(
            {portable_artifact_path(item.path): item for item in self.declarations}
        )

    def by_role(self) -> Mapping[str, tuple[ArtifactDeclaration, ...]]:
        return group_artifact_declarations(self.declarations)

    def required(self) -> tuple[ArtifactDeclaration, ...]:
        return tuple(item for item in self.declarations if item.required)

    def optional(self) -> tuple[ArtifactDeclaration, ...]:
        return tuple(item for item in self.declarations if not item.required)


def artifact_declaration(
    path: Path,
    role: ArtifactRoleLike,
    *,
    required: bool,
    created_by: ArtifactProducerLike,
    media_type: str | None = None,
) -> ArtifactDeclaration:
    canonical_role = normalize_artifact_role(role)
    resolved_media_type = (
        default_media_type_for(canonical_role)
        if media_type is None
        else normalize_media_type(media_type)
    )
    return ArtifactDeclaration(
        path=path,
        role=canonical_role.value,
        media_type=resolved_media_type,
        required=required,
        created_by=normalize_artifact_producer(created_by),
    )


def normalize_artifact_role(value: ArtifactRoleLike) -> ArtifactRole:
    if isinstance(value, ArtifactRole):
        return value
    if not isinstance(value, str):
        raise TypeError("artifact role must be ArtifactRole or string")
    if value != value.strip() or not value:
        raise ValueError("artifact role must be non-empty without surrounding whitespace")
    if not value.isascii() or _ROLE_RE.fullmatch(value) is None:
        raise ValueError(f"invalid artifact role: {value!r}")
    try:
        return ArtifactRole(value)
    except ValueError as exc:
        raise ValueError(f"unknown artifact role for manifest schema 1.0: {value!r}") from exc


def normalize_artifact_producer(value: ArtifactProducerLike) -> str:
    if isinstance(value, ArtifactProducer):
        return value.value
    if not isinstance(value, str):
        raise TypeError("created_by must be ArtifactProducer or string")
    if value != value.strip() or not value:
        raise ValueError("created_by must be non-empty without surrounding whitespace")
    if not value.isascii() or _PRODUCER_RE.fullmatch(value) is None:
        raise ValueError(f"invalid created_by producer ID: {value!r}")
    return value


def normalize_media_type(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("media_type must be a string")
    if value != value.strip() or not value:
        raise ValueError("media_type must be non-empty without surrounding whitespace")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError("media_type must be a single NUL-free line")
    if not value.isascii() or _MEDIA_TYPE_RE.fullmatch(value) is None:
        raise ValueError(f"invalid media_type: {value!r}")
    primary, *parameters = value.split(";")
    normalized = primary.lower()
    if parameters:
        normalized += "; " + "; ".join(part.strip().lower() for part in parameters)
    return normalized


def default_media_type_for(role: ArtifactRoleLike) -> str:
    canonical_role = normalize_artifact_role(role)
    try:
        return _DEFAULT_MEDIA_TYPES[canonical_role]
    except KeyError as exc:
        raise ValueError(
            f"artifact role {canonical_role.value!r} requires an explicit media_type"
        ) from exc


def allowed_media_types_for(role: ArtifactRoleLike) -> frozenset[str]:
    return _ALLOWED_MEDIA_TYPES[normalize_artifact_role(role)]


def canonical_paths_for(role: ArtifactRoleLike) -> tuple[str, ...]:
    return _CANONICAL_PATHS.get(normalize_artifact_role(role), ())


def portable_artifact_path(path: Path) -> str:
    candidate = _require_path(path)
    if candidate.is_absolute() or PureWindowsPath(str(candidate)).is_absolute():
        return candidate.as_posix()
    return _validate_relative_artifact_path(candidate)


def validate_artifact_declaration(
    declaration: ArtifactDeclaration,
) -> ArtifactDeclaration:
    if not isinstance(declaration, ArtifactDeclaration):
        raise TypeError("declaration must be ArtifactDeclaration")
    return declaration


def _materialize_artifact_declarations(
    declarations: object,
) -> tuple[ArtifactDeclaration, ...]:
    if isinstance(declarations, (str, bytes)) or not isinstance(declarations, Iterable):
        raise TypeError("declarations must be an iterable of ArtifactDeclaration")
    prepared: list[ArtifactDeclaration] = []
    for declaration in declarations:
        if not isinstance(declaration, ArtifactDeclaration):
            raise TypeError("declarations must contain ArtifactDeclaration values")
        prepared.append(declaration)
    return tuple(prepared)


def validate_artifact_declarations(
    declarations: Iterable[ArtifactDeclaration],
) -> tuple[ArtifactDeclaration, ...]:
    prepared = _materialize_artifact_declarations(declarations)
    seen_paths: dict[str, ArtifactDeclaration] = {}
    for declaration in prepared:
        identity = artifact_path_identity(declaration.path)
        previous = seen_paths.get(identity)
        if previous is not None:
            raise ValueError(
                f"duplicate artifact declaration path: {previous.path!s} and {declaration.path!s}"
            )
        seen_paths[identity] = declaration
    return tuple(sorted(prepared, key=artifact_declaration_sort_key))


def merge_artifact_declarations(
    *groups: Iterable[ArtifactDeclaration],
) -> tuple[ArtifactDeclaration, ...]:
    merged: list[ArtifactDeclaration] = []
    for group in groups:
        merged.extend(_materialize_artifact_declarations(group))
    return validate_artifact_declarations(merged)


def group_artifact_declarations(
    declarations: Iterable[ArtifactDeclaration],
) -> Mapping[str, tuple[ArtifactDeclaration, ...]]:
    prepared = validate_artifact_declarations(declarations)
    grouped: dict[str, list[ArtifactDeclaration]] = {}
    for declaration in prepared:
        grouped.setdefault(declaration.role, []).append(declaration)
    return MappingProxyType(
        {role: tuple(items) for role, items in sorted(grouped.items(), key=lambda item: item[0])}
    )


def artifact_declaration_sort_key(
    declaration: ArtifactDeclaration,
) -> tuple[str, str, str]:
    validate_artifact_declaration(declaration)
    path = portable_artifact_path(declaration.path)
    return (path.casefold(), path, declaration.role)


def artifact_path_identity(path: Path) -> str:
    candidate = _require_path(path)
    raw = str(candidate)
    normalized = os.path.normcase(os.path.normpath(raw))
    return normalized.casefold() if os.name == "nt" else normalized


def _validate_role_media_type(role: ArtifactRole, media_type: str) -> None:
    allowed = _ALLOWED_MEDIA_TYPES[role]
    if media_type not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(
            f"media_type {media_type!r} is incompatible with role "
            f"{role.value!r}; expected one of: {expected}"
        )


def _validate_fixed_path(role: ArtifactRole, path: Path) -> None:
    expected = _CANONICAL_PATHS.get(role)
    if expected is None or path.is_absolute() or PureWindowsPath(str(path)).is_absolute():
        return
    actual = _validate_relative_artifact_path(path)
    if actual not in expected:
        rendered = ", ".join(repr(item) for item in expected)
        raise ValueError(
            f"artifact role {role.value!r} requires canonical path {rendered}; received {actual!r}"
        )


def _validate_relative_artifact_path(path: Path) -> str:
    raw = str(path)
    if "\x00" in raw:
        raise ValueError("artifact path must not contain NUL characters")
    if not raw or raw == ".":
        raise ValueError("artifact path must identify a file")
    windows = PureWindowsPath(raw)
    if path.is_absolute() or windows.is_absolute() or windows.drive or raw.startswith(("/", "\\")):
        raise ValueError("artifact path must be run-relative")
    normalized = raw.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError("artifact path must not contain empty, dot, or parent segments")
    if pure.as_posix() == MANIFEST_FILENAME:
        raise ValueError("manifest.json must not be declared as a manifested artifact")
    return pure.as_posix()


def _require_path(value: object) -> Path:
    if not isinstance(value, Path):
        raise TypeError("path must be pathlib.Path")
    raw = str(value)
    if "\x00" in raw:
        raise ValueError("artifact path must not contain NUL characters")
    if not raw:
        raise ValueError("artifact path must not be empty")
    if not value.is_absolute() and not PureWindowsPath(raw).is_absolute():
        _validate_relative_artifact_path(value)
    return value


__all__ = (
    "APPLICATION_JSON",
    "APPLICATION_OCTET_STREAM",
    "MANIFEST_FILENAME",
    "TEXT_MARKDOWN_UTF8",
    "TEXT_PLAIN_UTF8",
    "ArtifactDeclaration",
    "ArtifactDeclarationSet",
    "ArtifactProducer",
    "ArtifactProducerLike",
    "ArtifactRole",
    "ArtifactRoleLike",
    "allowed_media_types_for",
    "artifact_declaration",
    "artifact_declaration_sort_key",
    "artifact_path_identity",
    "canonical_paths_for",
    "default_media_type_for",
    "group_artifact_declarations",
    "merge_artifact_declarations",
    "normalize_artifact_producer",
    "normalize_artifact_role",
    "normalize_media_type",
    "portable_artifact_path",
    "validate_artifact_declaration",
    "validate_artifact_declarations",
)
