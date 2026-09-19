from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import PurePosixPath, PureWindowsPath
import re
from types import MappingProxyType
from typing import Final, TypeAlias


@unique
class SchemaFormat(StrEnum):
    JSON = "json"
    TOML = "toml"
    CANONICAL_TEXT = "canonical_text"


@unique
class SchemaContractClass(StrEnum):
    CANONICAL_ROOT = "canonical_root"
    CANONICAL_TEXT = "canonical_text"


@unique
class SchemaSupportClass(StrEnum):
    CANONICAL = "canonical"
    DEPRECATED = "deprecated"
    LEGACY_READABLE = "legacy_readable"
    RETIRED = "retired"


@unique
class SchemaCompatibility(StrEnum):
    EXACT = "exact"
    SAME_MAJOR = "same_major"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    UNSUPPORTED_MAJOR = "unsupported_major"
    UNSUPPORTED_MINOR = "unsupported_minor"
    NOT_WRITABLE = "not_writable"
    LEGACY_READABLE = "legacy_readable"
    RETIRED = "retired"


_SCHEMA_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*)+$"
)
_SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_OWNER_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[._/-][a-z0-9]+)*$")
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"<([a-z][a-z0-9_-]*)>")


@dataclass(frozen=True, slots=True, order=True)
class SchemaVersion:
    major: int
    minor: int

    def __post_init__(self) -> None:
        if type(self.major) is not int or type(self.minor) is not int:
            raise TypeError("schema version components must be integers")
        if self.major < 0 or self.minor < 0:
            raise ValueError("schema version components must be non-negative")

    @classmethod
    def parse(cls, value: SchemaVersionLike) -> SchemaVersion:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("schema version must be SchemaVersion or string")
        if value != value.strip():
            raise ValueError("schema version must not contain surrounding whitespace")
        match = _SCHEMA_VERSION_RE.fullmatch(value)
        if match is None:
            raise ValueError("schema version must use MAJOR.MINOR")
        return cls(int(match.group(1)), int(match.group(2)))

    def same_major(self, other: SchemaVersionLike) -> bool:
        return self.major == SchemaVersion.parse(other).major

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


SchemaVersionLike: TypeAlias = SchemaVersion | str


@dataclass(frozen=True, slots=True)
class SchemaKey:
    schema_id: str
    version: SchemaVersion

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", normalize_schema_id(self.schema_id))
        object.__setattr__(self, "version", SchemaVersion.parse(self.version))

    @classmethod
    def parse(cls, value: SchemaKeyLike) -> SchemaKey:
        if isinstance(value, cls):
            return value
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError("schema key tuple must contain schema ID and version")
            return cls(value[0], SchemaVersion.parse(value[1]))
        if not isinstance(value, str):
            raise TypeError("schema key must be SchemaKey, tuple, or string")
        schema_id, separator, version = value.rpartition("/")
        if not separator or not schema_id or not version:
            raise ValueError("schema key must use '<schema-id>/<major>.<minor>'")
        return cls(schema_id, SchemaVersion.parse(version))

    def __str__(self) -> str:
        return f"{self.schema_id}/{self.version}"


SchemaKeyLike: TypeAlias = SchemaKey | tuple[str, SchemaVersionLike] | str


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    schema_id: str
    version: SchemaVersion
    format: SchemaFormat
    canonical_path_pattern: str
    contract_class: SchemaContractClass
    support: SchemaSupportClass
    writer_owner: str
    readers: tuple[str, ...]
    allow_same_major_read: bool
    migration_policy: str
    encoding: str = "utf-8"
    newline: str | None = None

    def __post_init__(self) -> None:
        schema_id = normalize_schema_id(self.schema_id)
        version = SchemaVersion.parse(self.version)
        if not isinstance(self.format, SchemaFormat):
            raise TypeError("format must be SchemaFormat")
        if not isinstance(self.contract_class, SchemaContractClass):
            raise TypeError("contract_class must be SchemaContractClass")
        if not isinstance(self.support, SchemaSupportClass):
            raise TypeError("support must be SchemaSupportClass")
        path_pattern = normalize_schema_path_pattern(self.canonical_path_pattern)
        writer_owner = _normalize_owner(self.writer_owner, field="writer_owner")
        readers = _normalize_owners(self.readers, field="readers")
        if type(self.allow_same_major_read) is not bool:
            raise TypeError("allow_same_major_read must be a boolean")
        migration_policy = _normalize_text(self.migration_policy, field="migration_policy")
        encoding = _normalize_encoding(self.encoding)
        newline = _normalize_newline(self.newline)
        if self.contract_class is SchemaContractClass.CANONICAL_ROOT:
            if self.format not in (SchemaFormat.JSON, SchemaFormat.TOML):
                raise ValueError("canonical root schemas must use JSON or TOML")
            if newline is not None:
                raise ValueError("root schema definitions do not own a text newline contract")
        else:
            if self.format is not SchemaFormat.CANONICAL_TEXT:
                raise ValueError("canonical text contracts must use canonical_text format")
            if newline != "lf":
                raise ValueError("canonical text schemas must use LF newlines")
        if self.support is not SchemaSupportClass.CANONICAL:
            raise ValueError("SchemaDefinition entries in the canonical registry must be canonical")
        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "canonical_path_pattern", path_pattern)
        object.__setattr__(self, "writer_owner", writer_owner)
        object.__setattr__(self, "readers", readers)
        object.__setattr__(self, "migration_policy", migration_policy)
        object.__setattr__(self, "encoding", encoding)
        object.__setattr__(self, "newline", newline)

    @property
    def key(self) -> SchemaKey:
        return SchemaKey(self.schema_id, self.version)

    @property
    def qualified_id(self) -> str:
        return str(self.key)

    @property
    def machine_readable_root(self) -> bool:
        return self.contract_class is SchemaContractClass.CANONICAL_ROOT

    def matches_path(self, path: str) -> bool:
        return schema_path_matches(self.canonical_path_pattern, path)


SchemaDescriptor = SchemaDefinition


@dataclass(frozen=True, slots=True)
class LegacySchemaDefinition:
    legacy_id: str
    source_path_pattern: str
    replacement: SchemaKey
    reader_policy: str
    writer_policy: str = "never_write"
    support: SchemaSupportClass = SchemaSupportClass.LEGACY_READABLE

    def __post_init__(self) -> None:
        legacy_id = normalize_schema_id(self.legacy_id, require_wordbench_prefix=False)
        source = normalize_schema_path_pattern(self.source_path_pattern)
        replacement = SchemaKey.parse(self.replacement)
        reader_policy = _normalize_text(self.reader_policy, field="reader_policy")
        writer_policy = _normalize_text(self.writer_policy, field="writer_policy")
        if self.support not in (
            SchemaSupportClass.DEPRECATED,
            SchemaSupportClass.LEGACY_READABLE,
            SchemaSupportClass.RETIRED,
        ):
            raise ValueError("legacy entries must be deprecated, legacy-readable, or retired")
        object.__setattr__(self, "legacy_id", legacy_id)
        object.__setattr__(self, "source_path_pattern", source)
        object.__setattr__(self, "replacement", replacement)
        object.__setattr__(self, "reader_policy", reader_policy)
        object.__setattr__(self, "writer_policy", writer_policy)

    def matches_path(self, path: str) -> bool:
        return schema_path_matches(self.source_path_pattern, path)


@dataclass(frozen=True, slots=True)
class SchemaResolution:
    requested_id: str
    requested_version: SchemaVersion | None
    compatibility: SchemaCompatibility
    definition: SchemaDefinition | None = None
    legacy: LegacySchemaDefinition | None = None
    message: str = ""

    def __post_init__(self) -> None:
        requested_id = normalize_schema_id(self.requested_id, require_wordbench_prefix=False)
        requested_version = (
            None if self.requested_version is None else SchemaVersion.parse(self.requested_version)
        )
        if not isinstance(self.compatibility, SchemaCompatibility):
            raise TypeError("compatibility must be SchemaCompatibility")
        if self.definition is not None and not isinstance(self.definition, SchemaDefinition):
            raise TypeError("definition must be SchemaDefinition or None")
        if self.legacy is not None and not isinstance(self.legacy, LegacySchemaDefinition):
            raise TypeError("legacy must be LegacySchemaDefinition or None")
        if self.definition is not None and self.legacy is not None:
            raise ValueError("resolution cannot contain both canonical and legacy definitions")
        message = self.message
        if message:
            message = _normalize_text(message, field="message")
        object.__setattr__(self, "requested_id", requested_id)
        object.__setattr__(self, "requested_version", requested_version)
        object.__setattr__(self, "message", message)

    @property
    def readable(self) -> bool:
        return self.compatibility in (
            SchemaCompatibility.EXACT,
            SchemaCompatibility.SAME_MAJOR,
            SchemaCompatibility.LEGACY_READABLE,
        )

    @property
    def writable(self) -> bool:
        return self.compatibility is SchemaCompatibility.EXACT and self.definition is not None


class SchemaRegistry:
    __slots__ = (
        "_by_key",
        "_current_by_id",
        "_definitions",
        "_legacy",
        "_legacy_by_id",
        "_versions_by_id",
    )

    def __init__(
        self,
        definitions: Iterable[SchemaDefinition],
        legacy: Iterable[LegacySchemaDefinition] = (),
    ) -> None:
        definitions_tuple = tuple(definitions)
        legacy_tuple = tuple(legacy)
        _validate_definitions(definitions_tuple)
        _validate_legacy(legacy_tuple, definitions_tuple)

        by_key = {definition.key: definition for definition in definitions_tuple}
        versions: dict[str, list[SchemaDefinition]] = {}
        for definition in definitions_tuple:
            versions.setdefault(definition.schema_id, []).append(definition)
        versions_by_id = {
            schema_id: tuple(sorted(items, key=lambda item: item.version))
            for schema_id, items in versions.items()
        }
        current_by_id = {schema_id: items[-1] for schema_id, items in versions_by_id.items()}
        legacy_by_id = {entry.legacy_id: entry for entry in legacy_tuple}

        self._definitions = tuple(
            sorted(definitions_tuple, key=lambda item: (item.schema_id, item.version))
        )
        self._legacy = tuple(sorted(legacy_tuple, key=lambda item: item.legacy_id))
        self._by_key = MappingProxyType(by_key)
        self._versions_by_id = MappingProxyType(versions_by_id)
        self._current_by_id = MappingProxyType(current_by_id)
        self._legacy_by_id = MappingProxyType(legacy_by_id)

    def __iter__(self) -> Iterator[SchemaDefinition]:
        return iter(self._definitions)

    def __len__(self) -> int:
        return len(self._definitions)

    @property
    def definitions(self) -> tuple[SchemaDefinition, ...]:
        return self._definitions

    @property
    def legacy_definitions(self) -> tuple[LegacySchemaDefinition, ...]:
        return self._legacy

    @property
    def schema_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._current_by_id))

    @property
    def qualified_ids(self) -> tuple[str, ...]:
        return tuple(definition.qualified_id for definition in self._definitions)

    def contains(self, schema_id: str, version: SchemaVersionLike | None = None) -> bool:
        try:
            if version is None:
                return normalize_schema_id(schema_id) in self._current_by_id
            key = SchemaKey(schema_id, SchemaVersion.parse(version))
        except (TypeError, ValueError):
            return False
        return key in self._by_key

    def get(
        self,
        schema_id: str,
        version: SchemaVersionLike | None = None,
    ) -> SchemaDefinition:
        canonical_id = normalize_schema_id(schema_id)
        if version is None:
            try:
                return self._current_by_id[canonical_id]
            except KeyError as exc:
                raise KeyError(f"unknown schema ID: {canonical_id}") from exc
        key = SchemaKey(canonical_id, SchemaVersion.parse(version))
        try:
            return self._by_key[key]
        except KeyError as exc:
            raise KeyError(f"unknown schema version: {key}") from exc

    def get_key(self, key: SchemaKeyLike) -> SchemaDefinition:
        parsed = SchemaKey.parse(key)
        return self.get(parsed.schema_id, parsed.version)

    def current(self, schema_id: str) -> SchemaDefinition:
        return self.get(schema_id)

    def versions(self, schema_id: str) -> tuple[SchemaVersion, ...]:
        canonical_id = normalize_schema_id(schema_id)
        try:
            return tuple(item.version for item in self._versions_by_id[canonical_id])
        except KeyError as exc:
            raise KeyError(f"unknown schema ID: {canonical_id}") from exc

    def legacy(self, legacy_id: str) -> LegacySchemaDefinition:
        canonical_id = normalize_schema_id(legacy_id, require_wordbench_prefix=False)
        try:
            return self._legacy_by_id[canonical_id]
        except KeyError as exc:
            raise KeyError(f"unknown legacy schema ID: {canonical_id}") from exc

    def resolve(
        self,
        schema_id: str,
        version: SchemaVersionLike | None,
        *,
        for_write: bool = False,
    ) -> SchemaResolution:
        normalized_id = normalize_schema_id(schema_id, require_wordbench_prefix=False)
        requested_version = None if version is None else SchemaVersion.parse(version)

        legacy = self._legacy_by_id.get(normalized_id)
        if legacy is not None:
            compatibility = (
                SchemaCompatibility.RETIRED
                if legacy.support is SchemaSupportClass.RETIRED
                else SchemaCompatibility.LEGACY_READABLE
            )
            if for_write:
                compatibility = SchemaCompatibility.NOT_WRITABLE
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=compatibility,
                legacy=legacy,
                message=(
                    f"legacy schema {legacy.legacy_id!r} is read-only; "
                    f"canonical replacement is {legacy.replacement}"
                ),
            )

        definition = self._current_by_id.get(normalized_id)
        if definition is None:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=SchemaCompatibility.UNSUPPORTED_SCHEMA,
                message=f"unsupported schema ID: {normalized_id}",
            )

        if requested_version is None:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=None,
                compatibility=SchemaCompatibility.UNSUPPORTED_MINOR,
                definition=definition,
                message="schema_version is required",
            )

        exact = self._by_key.get(SchemaKey(normalized_id, requested_version))
        if exact is not None:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=SchemaCompatibility.EXACT,
                definition=exact,
            )

        if for_write:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=SchemaCompatibility.NOT_WRITABLE,
                definition=definition,
                message=(
                    f"canonical writer emits only {definition.qualified_id}; "
                    f"requested {normalized_id}/{requested_version}"
                ),
            )

        if requested_version.major != definition.version.major:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=SchemaCompatibility.UNSUPPORTED_MAJOR,
                definition=definition,
                message=(
                    f"unsupported major version {requested_version.major} for "
                    f"{normalized_id}; supported major is {definition.version.major}"
                ),
            )

        if definition.allow_same_major_read:
            return SchemaResolution(
                requested_id=normalized_id,
                requested_version=requested_version,
                compatibility=SchemaCompatibility.SAME_MAJOR,
                definition=definition,
                message=(
                    f"same-major schema {normalized_id}/{requested_version} requires "
                    "field-level compatibility validation"
                ),
            )

        return SchemaResolution(
            requested_id=normalized_id,
            requested_version=requested_version,
            compatibility=SchemaCompatibility.UNSUPPORTED_MINOR,
            definition=definition,
            message=(
                f"unsupported minor version {requested_version} for {normalized_id}; "
                f"supported version is {definition.version}"
            ),
        )

    def require_readable(
        self,
        schema_id: str,
        version: SchemaVersionLike | None,
    ) -> SchemaResolution:
        resolution = self.resolve(schema_id, version, for_write=False)
        if not resolution.readable:
            raise ValueError(resolution.message or "schema is not readable")
        return resolution

    def require_writable(
        self,
        schema_id: str,
        version: SchemaVersionLike | None,
    ) -> SchemaDefinition:
        resolution = self.resolve(schema_id, version, for_write=True)
        if not resolution.writable or resolution.definition is None:
            raise ValueError(resolution.message or "schema is not writable")
        return resolution.definition

    def find_by_path(self, path: str) -> tuple[SchemaDefinition, ...]:
        normalized = normalize_schema_path(path)
        return tuple(
            definition for definition in self._definitions if definition.matches_path(normalized)
        )

    def find_legacy_by_path(self, path: str) -> tuple[LegacySchemaDefinition, ...]:
        normalized = normalize_schema_path(path)
        return tuple(entry for entry in self._legacy if entry.matches_path(normalized))

    def as_mapping(self) -> Mapping[str, SchemaDefinition]:
        return MappingProxyType(
            {definition.qualified_id: definition for definition in self._definitions}
        )


def normalize_schema_id(value: str, *, require_wordbench_prefix: bool = True) -> str:
    if not isinstance(value, str):
        raise TypeError("schema ID must be a string")
    if value != value.strip() or not value:
        raise ValueError("schema ID must be non-empty without surrounding whitespace")
    if not value.isascii() or _SCHEMA_ID_RE.fullmatch(value) is None:
        raise ValueError(f"invalid schema ID: {value!r}")
    if require_wordbench_prefix and not value.startswith("gf-wordbench."):
        raise ValueError("canonical schema ID must use the 'gf-wordbench.' prefix")
    return value


def parse_schema_version(value: SchemaVersionLike) -> SchemaVersion:
    return SchemaVersion.parse(value)


def format_schema_key(schema_id: str, version: SchemaVersionLike) -> str:
    return str(SchemaKey(schema_id, SchemaVersion.parse(version)))


def parse_schema_key(value: SchemaKeyLike) -> SchemaKey:
    return SchemaKey.parse(value)


def normalize_schema_path(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("schema path must be a string")
    if value != value.strip() or not value:
        raise ValueError("schema path must be non-empty without surrounding whitespace")
    if "\x00" in value:
        raise ValueError("schema path must not contain NUL characters")
    if PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive:
        raise ValueError("schema path must be portable and relative")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("schema path must be portable and traversal-free")
    return path.as_posix()


def normalize_schema_path_pattern(value: str) -> str:
    normalized = normalize_schema_path(value)
    for part in PurePosixPath(normalized).parts:
        scrubbed = _TOKEN_RE.sub("token", part)
        if "<" in scrubbed or ">" in scrubbed:
            raise ValueError(f"invalid schema path token in {value!r}")
    return normalized


def schema_path_matches(pattern: str, path: str) -> bool:
    canonical_pattern = normalize_schema_path_pattern(pattern)
    canonical_path = normalize_schema_path(path)
    expression_parts: list[str] = []
    position = 0
    for match in _TOKEN_RE.finditer(canonical_pattern):
        expression_parts.append(re.escape(canonical_pattern[position : match.start()]))
        expression_parts.append(r"[^/]+")
        position = match.end()
    expression_parts.append(re.escape(canonical_pattern[position:]))
    expression = "".join(expression_parts)
    return re.fullmatch(expression, canonical_path) is not None


def get_schema_definition(
    schema_id: str,
    version: SchemaVersionLike | None = None,
) -> SchemaDefinition:
    return SCHEMA_REGISTRY.get(schema_id, version)


def get_schema(schema_id: str, version: SchemaVersionLike | None = None) -> SchemaDefinition:
    return get_schema_definition(schema_id, version)


def current_schema(schema_id: str) -> SchemaDefinition:
    return SCHEMA_REGISTRY.current(schema_id)


def supported_schema_versions(schema_id: str) -> tuple[SchemaVersion, ...]:
    return SCHEMA_REGISTRY.versions(schema_id)


def resolve_schema(
    schema_id: str,
    version: SchemaVersionLike | None,
    *,
    for_write: bool = False,
) -> SchemaResolution:
    return SCHEMA_REGISTRY.resolve(schema_id, version, for_write=for_write)


def is_supported_schema(
    schema_id: str,
    version: SchemaVersionLike | None,
    *,
    for_write: bool = False,
) -> bool:
    resolution = resolve_schema(schema_id, version, for_write=for_write)
    return resolution.writable if for_write else resolution.readable


def require_readable_schema(
    schema_id: str,
    version: SchemaVersionLike | None,
) -> SchemaResolution:
    return SCHEMA_REGISTRY.require_readable(schema_id, version)


def require_writable_schema(
    schema_id: str,
    version: SchemaVersionLike | None,
) -> SchemaDefinition:
    return SCHEMA_REGISTRY.require_writable(schema_id, version)


def schema_identity_from_mapping(document: Mapping[str, object]) -> SchemaKey:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    if "schema_id" not in document:
        raise ValueError("document is missing schema_id")
    if "schema_version" not in document:
        raise ValueError("document is missing schema_version")
    schema_id = document["schema_id"]
    schema_version = document["schema_version"]
    if not isinstance(schema_id, str):
        raise TypeError("schema_id must be a string")
    if not isinstance(schema_version, str):
        raise TypeError("schema_version must be a string")
    return SchemaKey(schema_id, SchemaVersion.parse(schema_version))


def validate_schema_identity(
    document: Mapping[str, object],
    *,
    expected_schema_id: str | None = None,
    for_write: bool = False,
) -> SchemaResolution:
    key = schema_identity_from_mapping(document)
    if expected_schema_id is not None:
        expected = normalize_schema_id(expected_schema_id)
        if key.schema_id != expected:
            raise ValueError(f"wrong schema_id: expected {expected!r}, received {key.schema_id!r}")
    resolution = resolve_schema(key.schema_id, key.version, for_write=for_write)
    if for_write:
        if not resolution.writable:
            raise ValueError(resolution.message or "schema is not writable")
    elif not resolution.readable:
        raise ValueError(resolution.message or "schema is not readable")
    return resolution


def schema_registry_snapshot() -> Mapping[str, SchemaDefinition]:
    return SCHEMA_REGISTRY.as_mapping()


def _validate_definitions(definitions: tuple[SchemaDefinition, ...]) -> None:
    if not definitions:
        raise ValueError("schema registry requires at least one canonical definition")
    seen_keys: set[SchemaKey] = set()
    seen_paths: dict[str, SchemaKey] = {}
    for definition in definitions:
        if not isinstance(definition, SchemaDefinition):
            raise TypeError("definitions must contain SchemaDefinition values")
        if definition.key in seen_keys:
            raise ValueError(f"duplicate schema definition: {definition.qualified_id}")
        seen_keys.add(definition.key)
        path_identity = definition.canonical_path_pattern.casefold()
        previous = seen_paths.get(path_identity)
        if previous is not None and previous.schema_id != definition.schema_id:
            raise ValueError(
                f"canonical schema path {definition.canonical_path_pattern!r} is shared by "
                f"{previous} and {definition.qualified_id}"
            )
        seen_paths[path_identity] = definition.key

    by_id: dict[str, list[SchemaDefinition]] = {}
    for definition in definitions:
        by_id.setdefault(definition.schema_id, []).append(definition)
    for schema_id, versions in by_id.items():
        majors = {definition.version.major for definition in versions}
        if len(majors) > 1:
            raise ValueError(f"registry contains multiple active major versions for {schema_id!r}")


def _validate_legacy(
    legacy: tuple[LegacySchemaDefinition, ...],
    definitions: tuple[SchemaDefinition, ...],
) -> None:
    canonical_keys = {definition.key for definition in definitions}
    canonical_ids = {definition.schema_id for definition in definitions}
    seen: set[str] = set()
    for entry in legacy:
        if not isinstance(entry, LegacySchemaDefinition):
            raise TypeError("legacy entries must contain LegacySchemaDefinition values")
        if entry.legacy_id in seen:
            raise ValueError(f"duplicate legacy schema ID: {entry.legacy_id}")
        if entry.legacy_id in canonical_ids:
            raise ValueError("legacy schema ID must not collide with a canonical schema ID")
        if entry.replacement not in canonical_keys:
            raise ValueError(
                f"legacy replacement is not present in the canonical registry: {entry.replacement}"
            )
        seen.add(entry.legacy_id)


def _normalize_owner(value: str, *, field: str) -> str:
    text = _normalize_text(value, field=field)
    if not text.isascii() or _OWNER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a portable owner identifier")
    return text


def _normalize_owners(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of owner identifiers")
    normalized = tuple(_normalize_owner(value, field=f"{field} item") for value in values)
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} must not contain duplicates")
    return normalized


def _normalize_text(value: str, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field} must be non-empty without surrounding whitespace")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be one NUL-free line")
    return value


def _normalize_encoding(value: str) -> str:
    text = _normalize_text(value, field="encoding").lower().replace("_", "-")
    if text not in ("utf-8",):
        raise ValueError("canonical schemas use UTF-8")
    return text


def _normalize_newline(value: str | None) -> str | None:
    if value is None:
        return None
    text = _normalize_text(value, field="newline").lower()
    if text != "lf":
        raise ValueError("canonical text schemas use LF newlines")
    return text


PROJECT_SCHEMA_ID: Final[str] = "gf-wordbench.project"
APP_STATE_SCHEMA_ID: Final[str] = "gf-wordbench.app-state"
RUN_SUMMARY_SCHEMA_ID: Final[str] = "gf-wordbench.run-summary"
ARTIFACT_MANIFEST_SCHEMA_ID: Final[str] = "gf-wordbench.artifact-manifest"
SCENARIO_OUTPUT_SCHEMA_ID: Final[str] = "gf-wordbench.scenario-output"
SCENARIO_GOLD_SCHEMA_ID: Final[str] = "gf-wordbench.scenario-gold"

PROJECT_SCHEMA_VERSION: Final[str] = "1.0"
APP_STATE_SCHEMA_VERSION: Final[str] = "1.0"
RUN_SUMMARY_SCHEMA_VERSION: Final[str] = "1.0"
ARTIFACT_MANIFEST_SCHEMA_VERSION: Final[str] = "1.0"
SCENARIO_OUTPUT_SCHEMA_VERSION: Final[str] = "1.0"
SCENARIO_GOLD_SCHEMA_VERSION: Final[str] = "1.0"

MANIFEST_SCHEMA_ID: Final[str] = ARTIFACT_MANIFEST_SCHEMA_ID
MANIFEST_SCHEMA_VERSION: Final[str] = ARTIFACT_MANIFEST_SCHEMA_VERSION
SUMMARY_SCHEMA_ID: Final[str] = RUN_SUMMARY_SCHEMA_ID
SUMMARY_SCHEMA_VERSION: Final[str] = RUN_SUMMARY_SCHEMA_VERSION

PROJECT_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    PROJECT_SCHEMA_ID,
    SchemaVersion.parse(PROJECT_SCHEMA_VERSION),
)
APP_STATE_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    APP_STATE_SCHEMA_ID,
    SchemaVersion.parse(APP_STATE_SCHEMA_VERSION),
)
RUN_SUMMARY_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    RUN_SUMMARY_SCHEMA_ID,
    SchemaVersion.parse(RUN_SUMMARY_SCHEMA_VERSION),
)
ARTIFACT_MANIFEST_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    ARTIFACT_MANIFEST_SCHEMA_ID,
    SchemaVersion.parse(ARTIFACT_MANIFEST_SCHEMA_VERSION),
)
SCENARIO_OUTPUT_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    SCENARIO_OUTPUT_SCHEMA_ID,
    SchemaVersion.parse(SCENARIO_OUTPUT_SCHEMA_VERSION),
)
SCENARIO_GOLD_SCHEMA_KEY: Final[SchemaKey] = SchemaKey(
    SCENARIO_GOLD_SCHEMA_ID,
    SchemaVersion.parse(SCENARIO_GOLD_SCHEMA_VERSION),
)


_DECLARED_CANONICAL_SCHEMA_DEFINITIONS: Final[tuple[SchemaDefinition, ...]] = (
    SchemaDefinition(
        schema_id=PROJECT_SCHEMA_ID,
        version=SchemaVersion.parse(PROJECT_SCHEMA_VERSION),
        format=SchemaFormat.TOML,
        canonical_path_pattern="project/project.toml",
        contract_class=SchemaContractClass.CANONICAL_ROOT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="projects.toml_adapter",
        readers=(
            "projects.loader",
            "projects.validator",
            "config.resolver",
            "entrypoints",
            "schema_validator",
        ),
        allow_same_major_read=True,
        migration_policy="explicit",
    ),
    SchemaDefinition(
        schema_id=APP_STATE_SCHEMA_ID,
        version=SchemaVersion.parse(APP_STATE_SCHEMA_VERSION),
        format=SchemaFormat.JSON,
        canonical_path_pattern=".gf_wordbench_state.json",
        contract_class=SchemaContractClass.CANONICAL_ROOT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="state.repository",
        readers=(
            "state.repository",
            "entrypoints.cli",
            "entrypoints.gui",
            "schema_validator",
        ),
        allow_same_major_read=True,
        migration_policy="required_when_imported",
    ),
    SchemaDefinition(
        schema_id=RUN_SUMMARY_SCHEMA_ID,
        version=SchemaVersion.parse(RUN_SUMMARY_SCHEMA_VERSION),
        format=SchemaFormat.JSON,
        canonical_path_pattern="run_<run-id>/summary.json",
        contract_class=SchemaContractClass.CANONICAL_ROOT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="reporting.summary.json_writer",
        readers=(
            "validation.regression.loader",
            "entrypoints.cli",
            "entrypoints.gui",
            "validation.release",
            "reporting.publisher",
            "schema_validator",
            "external_read_only_consumers",
        ),
        allow_same_major_read=True,
        migration_policy="required_when_imported",
    ),
    SchemaDefinition(
        schema_id=ARTIFACT_MANIFEST_SCHEMA_ID,
        version=SchemaVersion.parse(ARTIFACT_MANIFEST_SCHEMA_VERSION),
        format=SchemaFormat.JSON,
        canonical_path_pattern="run_<run-id>/manifest.json",
        contract_class=SchemaContractClass.CANONICAL_ROOT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="reporting.manifest.builder",
        readers=(
            "reporting.manifest.verifier",
            "entrypoints.gui",
            "runs.cleanup",
            "runs.archive",
            "reporting.publisher",
            "validation.release",
            "schema_validator",
        ),
        allow_same_major_read=True,
        migration_policy="not_applicable",
    ),
    SchemaDefinition(
        schema_id=SCENARIO_OUTPUT_SCHEMA_ID,
        version=SchemaVersion.parse(SCENARIO_OUTPUT_SCHEMA_VERSION),
        format=SchemaFormat.CANONICAL_TEXT,
        canonical_path_pattern="run_<run-id>/raw/scenarios/<scenario-id>.out",
        contract_class=SchemaContractClass.CANONICAL_TEXT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="validation.scenarios.normalization",
        readers=(
            "validation.scenarios.markers",
            "validation.scenarios.gold_compare",
            "reporting.details",
            "reporting.ai_packet",
            "schema_validator",
        ),
        allow_same_major_read=True,
        migration_policy="regenerate_or_explicit_import",
        newline="lf",
    ),
    SchemaDefinition(
        schema_id=SCENARIO_GOLD_SCHEMA_ID,
        version=SchemaVersion.parse(SCENARIO_GOLD_SCHEMA_VERSION),
        format=SchemaFormat.CANONICAL_TEXT,
        canonical_path_pattern="project/validation/gold/<scenario-id>.gold",
        contract_class=SchemaContractClass.CANONICAL_TEXT,
        support=SchemaSupportClass.CANONICAL,
        writer_owner="validation.scenarios.gold_update",
        readers=(
            "validation.scenarios.gold_compare",
            "validation.release",
            "project_review_tooling",
            "schema_validator",
        ),
        allow_same_major_read=True,
        migration_policy="explicit_review",
        newline="lf",
    ),
)

CANONICAL_SCHEMA_DEFINITIONS: Final[tuple[SchemaDefinition, ...]] = tuple(
    sorted(
        _DECLARED_CANONICAL_SCHEMA_DEFINITIONS,
        key=lambda definition: (definition.schema_id, definition.version),
    )
)


LEGACY_SCHEMA_DEFINITIONS: Final[tuple[LegacySchemaDefinition, ...]] = (
    LegacySchemaDefinition(
        legacy_id="gf-audit.state-legacy",
        source_path_pattern=".gf_audit_state.json",
        replacement=APP_STATE_SCHEMA_KEY,
        reader_policy="import_and_migrate",
    ),
    LegacySchemaDefinition(
        legacy_id="gf-audit.state-unversioned",
        source_path_pattern=".gf_audit_state.json",
        replacement=APP_STATE_SCHEMA_KEY,
        reader_policy="read_legacy_fields_with_warnings",
    ),
    LegacySchemaDefinition(
        legacy_id="gf-audit.run-summary-current",
        source_path_pattern="run_<run-id>/summary.json",
        replacement=RUN_SUMMARY_SCHEMA_KEY,
        reader_policy="read_and_migrate_nested_summary",
    ),
    LegacySchemaDefinition(
        legacy_id="gf-audit.run-summary-legacy",
        source_path_pattern="run_<run-id>/summary.json",
        replacement=RUN_SUMMARY_SCHEMA_KEY,
        reader_policy="read_and_migrate_flat_summary",
    ),
)


SCHEMA_REGISTRY: Final[SchemaRegistry] = SchemaRegistry(
    CANONICAL_SCHEMA_DEFINITIONS,
    LEGACY_SCHEMA_DEFINITIONS,
)
CANONICAL_SCHEMA_IDS: Final[tuple[str, ...]] = SCHEMA_REGISTRY.schema_ids
CANONICAL_SCHEMA_KEYS: Final[tuple[SchemaKey, ...]] = tuple(
    definition.key for definition in SCHEMA_REGISTRY
)


SchemaKind = SchemaContractClass
SchemaSupport = SchemaSupportClass


__all__ = (
    "APP_STATE_SCHEMA_ID",
    "APP_STATE_SCHEMA_KEY",
    "APP_STATE_SCHEMA_VERSION",
    "ARTIFACT_MANIFEST_SCHEMA_ID",
    "ARTIFACT_MANIFEST_SCHEMA_KEY",
    "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "CANONICAL_SCHEMA_DEFINITIONS",
    "CANONICAL_SCHEMA_IDS",
    "CANONICAL_SCHEMA_KEYS",
    "LEGACY_SCHEMA_DEFINITIONS",
    "MANIFEST_SCHEMA_ID",
    "MANIFEST_SCHEMA_VERSION",
    "PROJECT_SCHEMA_ID",
    "PROJECT_SCHEMA_KEY",
    "PROJECT_SCHEMA_VERSION",
    "RUN_SUMMARY_SCHEMA_ID",
    "RUN_SUMMARY_SCHEMA_KEY",
    "RUN_SUMMARY_SCHEMA_VERSION",
    "SCENARIO_GOLD_SCHEMA_ID",
    "SCENARIO_GOLD_SCHEMA_KEY",
    "SCENARIO_GOLD_SCHEMA_VERSION",
    "SCENARIO_OUTPUT_SCHEMA_ID",
    "SCENARIO_OUTPUT_SCHEMA_KEY",
    "SCENARIO_OUTPUT_SCHEMA_VERSION",
    "SCHEMA_REGISTRY",
    "SUMMARY_SCHEMA_ID",
    "SUMMARY_SCHEMA_VERSION",
    "LegacySchemaDefinition",
    "SchemaCompatibility",
    "SchemaContractClass",
    "SchemaDefinition",
    "SchemaDescriptor",
    "SchemaFormat",
    "SchemaKey",
    "SchemaKeyLike",
    "SchemaKind",
    "SchemaRegistry",
    "SchemaResolution",
    "SchemaSupport",
    "SchemaSupportClass",
    "SchemaVersion",
    "SchemaVersionLike",
    "current_schema",
    "format_schema_key",
    "get_schema",
    "get_schema_definition",
    "is_supported_schema",
    "normalize_schema_id",
    "normalize_schema_path",
    "normalize_schema_path_pattern",
    "parse_schema_key",
    "parse_schema_version",
    "require_readable_schema",
    "require_writable_schema",
    "resolve_schema",
    "schema_identity_from_mapping",
    "schema_path_matches",
    "schema_registry_snapshot",
    "supported_schema_versions",
    "validate_schema_identity",
)
