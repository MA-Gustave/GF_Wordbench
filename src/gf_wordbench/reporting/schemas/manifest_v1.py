"""Schema 1.0 for the canonical GF Wordbench artifact manifest."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from enum import Enum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Final, NotRequired, TypedDict, cast
from urllib.parse import urlsplit

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.kernel.ids import validate_run_id
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.reporting.manifest import models as _manifest_models
from gf_wordbench.reporting.manifest.models import (
    ArtifactManifest,
    ArtifactManifestEntry,
)

ARTIFACT_MANIFEST_SCHEMA_ID: Final[str] = "gf-wordbench.artifact-manifest"
ARTIFACT_MANIFEST_SCHEMA_VERSION: Final[str] = "1.0"
ARTIFACT_MANIFEST_FILENAME: Final[str] = "manifest.json"
ARTIFACT_MANIFEST_HASH_ALGORITHM: Final[str] = "sha256"
PRODUCER_NAME: Final[str] = "gf-wordbench"

MANIFEST_SCHEMA_ID: Final[str] = ARTIFACT_MANIFEST_SCHEMA_ID
MANIFEST_SCHEMA_VERSION: Final[str] = ARTIFACT_MANIFEST_SCHEMA_VERSION
MANIFEST_FILENAME: Final[str] = ARTIFACT_MANIFEST_FILENAME
HASH_ALGORITHM: Final[str] = ARTIFACT_MANIFEST_HASH_ALGORITHM

CANONICAL_ARTIFACT_ROLES: Final[frozenset[str]] = frozenset(
    {
        "machine_summary",
        "human_summary",
        "ai_handoff",
        "top_errors",
        "master_log",
        "aggregate_log",
        "scan_log",
        "compile_stdout",
        "compile_stderr",
        "scenario_stdout",
        "scenario_stderr",
        "scenario_output",
        "detail",
        "gfo",
        "pgf",
        "other",
    }
)

CANONICAL_MEDIA_TYPES: Final[frozenset[str]] = frozenset(
    {
        "application/json",
        "text/markdown; charset=utf-8",
        "text/plain; charset=utf-8",
        "application/octet-stream",
    }
)

_ROLE_MEDIA_TYPES: Final[Mapping[str, frozenset[str]]] = {
    "machine_summary": frozenset({"application/json"}),
    "human_summary": frozenset({"text/markdown; charset=utf-8"}),
    "ai_handoff": frozenset({"text/markdown; charset=utf-8"}),
    "top_errors": frozenset({"text/plain; charset=utf-8"}),
    "master_log": frozenset({"text/plain; charset=utf-8"}),
    "aggregate_log": frozenset({"text/plain; charset=utf-8"}),
    "scan_log": frozenset({"text/plain; charset=utf-8"}),
    "compile_stdout": frozenset({"text/plain; charset=utf-8"}),
    "compile_stderr": frozenset({"text/plain; charset=utf-8"}),
    "scenario_stdout": frozenset({"text/plain; charset=utf-8"}),
    "scenario_stderr": frozenset({"text/plain; charset=utf-8"}),
    "scenario_output": frozenset({"text/plain; charset=utf-8"}),
    "detail": frozenset(
        {
            "text/markdown; charset=utf-8",
            "text/plain; charset=utf-8",
            "application/json",
        }
    ),
    "gfo": frozenset({"application/octet-stream"}),
    "pgf": frozenset({"application/octet-stream"}),
    "other": CANONICAL_MEDIA_TYPES,
}

_RECOMMENDED_CREATED_BY: Final[frozenset[str]] = frozenset(
    {
        "reporting_json",
        "reporting_markdown",
        "reporting_ai_ready",
        "reporting_logs",
        "reporting_details",
        "runs",
        "validation_scanner",
        "validation_compiler",
        "validation_scenario",
        "validation_normalizer",
        "validation_pgf",
        "gf",
    }
)

_SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+"
    r"(?:; [A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+-]+)*$"
)
_CREATED_BY_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
)
_RFC3339_UTC_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?P<fraction>\.[0-9]{1,6})?Z$"
)

_ROOT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_id",
        "schema_version",
        "producer",
        "run_id",
        "generated_at",
        "hash_algorithm",
        "artifacts",
    }
)
_PRODUCER_FIELDS: Final[frozenset[str]] = frozenset({"name", "version"})
_ENTRY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "path",
        "role",
        "media_type",
        "required",
        "size_bytes",
        "sha256",
        "created_by",
    }
)

_MAX_ARTIFACTS: Final[int] = 1_000_000
_MAX_TEXT_LENGTH: Final[int] = 4_096
_CURRENT_MAJOR: Final[int] = 1
_CURRENT_MINOR: Final[int] = 0
_NUL: Final[str] = "\x00"


class ProducerDocument(TypedDict):
    name: str
    version: str


class ArtifactManifestEntryDocument(TypedDict):
    path: str
    role: str
    media_type: str
    required: bool
    size_bytes: int
    sha256: str
    created_by: str


class ArtifactManifestDocument(TypedDict):
    schema_id: str
    schema_version: str
    producer: ProducerDocument
    run_id: str
    generated_at: str
    hash_algorithm: str
    artifacts: list[ArtifactManifestEntryDocument]


class CompatibleArtifactManifestDocument(TypedDict):
    schema_id: str
    schema_version: str
    producer: ProducerDocument
    run_id: str
    generated_at: str
    hash_algorithm: str
    artifacts: list[ArtifactManifestEntryDocument]
    extensions: NotRequired[dict[str, object]]


def parse_artifact_manifest(
    document: object,
    *,
    strict: bool = False,
) -> ArtifactManifest:
    """Parse an untrusted decoded JSON value into the canonical typed model."""

    canonical = canonicalize_artifact_manifest_document(
        document,
        strict=strict,
    )
    entries = tuple(
        _entry_model(entry)
        for entry in canonical["artifacts"]
    )
    return ArtifactManifest(
        schema_id=canonical["schema_id"],
        schema_version=canonical["schema_version"],
        producer_name=canonical["producer"]["name"],
        producer_version=canonical["producer"]["version"],
        run_id=canonical["run_id"],
        generated_at=canonical["generated_at"],
        hash_algorithm=canonical["hash_algorithm"],
        artifacts=entries,
    )


def serialize_artifact_manifest(
    manifest: ArtifactManifest,
) -> ArtifactManifestDocument:
    """Return the exact canonical JSON object for a validated manifest model."""

    validate_artifact_manifest(manifest)
    document = ArtifactManifestDocument(
        schema_id=_model_text(manifest, "schema_id"),
        schema_version=_model_text(manifest, "schema_version"),
        producer=ProducerDocument(
            name=_model_text(manifest, "producer_name"),
            version=_model_text(manifest, "producer_version"),
        ),
        run_id=_model_text(manifest, "run_id"),
        generated_at=_canonical_timestamp(
            getattr(manifest, "generated_at"),
            field="$.generated_at",
        ),
        hash_algorithm=_model_text(manifest, "hash_algorithm"),
        artifacts=[
            _entry_to_document(entry)
            for entry in tuple(getattr(manifest, "artifacts"))
        ],
    )
    return canonicalize_artifact_manifest_document(document, strict=True)


def validate_artifact_manifest(manifest: ArtifactManifest) -> None:
    """Validate a typed manifest before persistence or verification."""

    if not isinstance(manifest, ArtifactManifest):
        raise TypeError("manifest must be an ArtifactManifest")
    canonicalize_artifact_manifest_document(
        ArtifactManifestDocument(
            schema_id=_model_text(manifest, "schema_id"),
            schema_version=_model_text(manifest, "schema_version"),
            producer=ProducerDocument(
                name=_model_text(manifest, "producer_name"),
                version=_model_text(manifest, "producer_version"),
            ),
            run_id=_model_text(manifest, "run_id"),
            generated_at=_canonical_timestamp(
                getattr(manifest, "generated_at"),
                field="$.generated_at",
            ),
            hash_algorithm=_model_text(manifest, "hash_algorithm"),
            artifacts=[
                _entry_to_document(entry)
                for entry in tuple(getattr(manifest, "artifacts"))
            ],
        ),
        strict=True,
    )


def canonicalize_artifact_manifest_document(
    document: object,
    *,
    strict: bool = False,
) -> ArtifactManifestDocument:
    """Validate and normalize a decoded schema-1.0 manifest document."""

    root = _mapping(document, "$", strict=strict)
    if strict:
        _require_exact_fields(root, _ROOT_FIELDS, "$", required=_ROOT_FIELDS)
    else:
        _require_fields(root, _ROOT_FIELDS, "$")

    schema_id = _text(root.get("schema_id"), "$.schema_id")
    if schema_id != ARTIFACT_MANIFEST_SCHEMA_ID:
        _fail(
            "$.schema_id",
            f"must be {ARTIFACT_MANIFEST_SCHEMA_ID!r}",
        )

    schema_version = _text(root.get("schema_version"), "$.schema_version")
    _validate_schema_version(schema_version, strict=strict)

    producer_value = _mapping(root.get("producer"), "$.producer", strict=strict)
    if strict:
        _require_exact_fields(
            producer_value,
            _PRODUCER_FIELDS,
            "$.producer",
            required=_PRODUCER_FIELDS,
        )
    else:
        _require_fields(producer_value, _PRODUCER_FIELDS, "$.producer")
    producer_name = _text(producer_value.get("name"), "$.producer.name")
    producer_version = _text(
        producer_value.get("version"),
        "$.producer.version",
    )
    producer = ProducerInfo(name=producer_name, version=producer_version)
    if producer.name != PRODUCER_NAME:
        _fail("$.producer.name", f"must be {PRODUCER_NAME!r}")

    run_id = str(validate_run_id(root.get("run_id"), field="manifest run ID"))
    generated_at = _canonical_timestamp(
        root.get("generated_at"),
        field="$.generated_at",
    )
    hash_algorithm = _text(root.get("hash_algorithm"), "$.hash_algorithm")
    if hash_algorithm != ARTIFACT_MANIFEST_HASH_ALGORITHM:
        _fail(
            "$.hash_algorithm",
            f"must be {ARTIFACT_MANIFEST_HASH_ALGORITHM!r}",
        )

    artifacts_value = root.get("artifacts")
    if not isinstance(artifacts_value, list):
        _fail("$.artifacts", "must be a JSON array")
    if len(artifacts_value) > _MAX_ARTIFACTS:
        _fail("$.artifacts", "exceeds the supported artifact limit")

    entries: list[ArtifactManifestEntryDocument] = []
    comparison_keys: dict[str, str] = {}
    for index, value in enumerate(artifacts_value):
        entry = _canonical_entry(value, index=index, strict=strict)
        comparison_key = artifact_path_comparison_key(entry["path"])
        previous = comparison_keys.get(comparison_key)
        if previous is not None:
            _fail(
                f"$.artifacts[{index}].path",
                f"duplicates artifact path {previous!r}",
            )
        comparison_keys[comparison_key] = entry["path"]
        entries.append(entry)

    entries.sort(key=lambda entry: entry["path"])

    return ArtifactManifestDocument(
        schema_id=ARTIFACT_MANIFEST_SCHEMA_ID,
        schema_version=(
            ARTIFACT_MANIFEST_SCHEMA_VERSION if strict else schema_version
        ),
        producer=ProducerDocument(
            name=producer.name,
            version=producer.version,
        ),
        run_id=run_id,
        generated_at=generated_at,
        hash_algorithm=ARTIFACT_MANIFEST_HASH_ALGORITHM,
        artifacts=entries,
    )


def artifact_manifest_entry_document(
    *,
    path: str,
    role: str | Enum,
    media_type: str,
    required: bool,
    size_bytes: int,
    sha256: str,
    created_by: str,
) -> ArtifactManifestEntryDocument:
    """Construct one validated canonical schema-1.0 artifact entry."""

    return _canonical_entry(
        {
            "path": path,
            "role": _enum_text(role),
            "media_type": media_type,
            "required": required,
            "size_bytes": size_bytes,
            "sha256": sha256,
            "created_by": created_by,
        },
        index=0,
        strict=True,
        field_prefix="$.artifact",
    )


def producer_document(version: str) -> ProducerDocument:
    """Build canonical manifest producer metadata."""

    producer = ProducerInfo(name=PRODUCER_NAME, version=version)
    return ProducerDocument(name=producer.name, version=producer.version)


def normalize_artifact_path(value: object) -> str:
    """Return a safe normalized run-relative artifact path."""

    path = _text(value, "artifact path")
    if "\\" in path:
        _fail("artifact path", "must use forward-slash separators")
    if path.endswith("/"):
        _fail("artifact path", "must identify a file, not a directory")
    if path.startswith("/") or path.startswith("//"):
        _fail("artifact path", "must be relative to the run root")
    if PureWindowsPath(path).is_absolute() or PureWindowsPath(path).drive:
        _fail("artifact path", "must not contain a Windows drive or UNC root")
    split = urlsplit(path)
    if split.scheme or split.netloc:
        _fail("artifact path", "must not be a URI")

    raw_parts = path.split("/")
    normalized_parts: list[str] = []
    for part in raw_parts:
        if part in {"", "."}:
            continue
        if part == "..":
            _fail("artifact path", "must not contain traversal segments")
        if _NUL in part:
            _fail("artifact path", "must not contain NUL")
        normalized_parts.append(part)

    if not normalized_parts:
        _fail("artifact path", "must identify a file")

    normalized = PurePosixPath(*normalized_parts).as_posix()
    if normalized in {".", ""}:
        _fail("artifact path", "must identify a file")
    if normalized == ARTIFACT_MANIFEST_FILENAME:
        _fail("artifact path", "must not list manifest.json itself")
    if normalized.endswith("/"):
        _fail("artifact path", "must identify a file, not a directory")
    return normalized


def artifact_path_comparison_key(value: object) -> str:
    """Return the portable duplicate-detection key used by schema 1.0."""

    return normalize_artifact_path(value).casefold()


def is_supported_artifact_manifest_version(value: object) -> bool:
    """Return whether a schema version belongs to the supported major."""

    if not isinstance(value, str):
        return False
    match = _SCHEMA_VERSION_RE.fullmatch(value)
    return match is not None and int(match.group(1)) == _CURRENT_MAJOR


def _canonical_entry(
    value: object,
    *,
    index: int,
    strict: bool,
    field_prefix: str | None = None,
) -> ArtifactManifestEntryDocument:
    field = field_prefix or f"$.artifacts[{index}]"
    entry = _mapping(value, field, strict=strict)
    if strict:
        _require_exact_fields(entry, _ENTRY_FIELDS, field, required=_ENTRY_FIELDS)
    else:
        _require_fields(entry, _ENTRY_FIELDS, field)

    path = normalize_artifact_path(entry.get("path"))
    role = _enum_text(entry.get("role"))
    if role not in CANONICAL_ARTIFACT_ROLES:
        _fail(f"{field}.role", f"unknown artifact role {role!r}")

    media_type = _text(entry.get("media_type"), f"{field}.media_type")
    if _MEDIA_TYPE_RE.fullmatch(media_type) is None:
        _fail(f"{field}.media_type", "must be a valid canonical media type")
    allowed_media_types = _ROLE_MEDIA_TYPES[role]
    if media_type not in allowed_media_types:
        _fail(
            f"{field}.media_type",
            f"is incompatible with role {role!r}",
        )

    required = entry.get("required")
    if type(required) is not bool:
        _fail(f"{field}.required", "must be a boolean")

    size_bytes = entry.get("size_bytes")
    if type(size_bytes) is not int:
        _fail(f"{field}.size_bytes", "must be an integer")
    if size_bytes < 0:
        _fail(f"{field}.size_bytes", "must be non-negative")

    sha256 = _text(entry.get("sha256"), f"{field}.sha256")
    if _SHA256_RE.fullmatch(sha256) is None:
        _fail(f"{field}.sha256", "must be 64 lowercase hexadecimal characters")

    created_by = _text(entry.get("created_by"), f"{field}.created_by")
    if _CREATED_BY_RE.fullmatch(created_by) is None:
        _fail(f"{field}.created_by", "must be a stable lower_snake_case producer ID")

    return ArtifactManifestEntryDocument(
        path=path,
        role=role,
        media_type=media_type,
        required=required,
        size_bytes=size_bytes,
        sha256=sha256,
        created_by=created_by,
    )


def _entry_to_document(entry: ArtifactManifestEntry) -> ArtifactManifestEntryDocument:
    if not isinstance(entry, ArtifactManifestEntry):
        raise TypeError("manifest artifacts must contain ArtifactManifestEntry")
    return artifact_manifest_entry_document(
        path=_model_text(entry, "path"),
        role=getattr(entry, "role"),
        media_type=_model_text(entry, "media_type"),
        required=getattr(entry, "required"),
        size_bytes=getattr(entry, "size_bytes"),
        sha256=_model_text(entry, "sha256"),
        created_by=_model_text(entry, "created_by"),
    )


def _entry_model(document: ArtifactManifestEntryDocument) -> ArtifactManifestEntry:
    role_value: object = document["role"]
    role_type = getattr(_manifest_models, "ArtifactRole", None)
    if isinstance(role_type, type) and issubclass(role_type, Enum):
        role_value = role_type(document["role"])
    return ArtifactManifestEntry(
        path=document["path"],
        role=role_value,
        media_type=document["media_type"],
        required=document["required"],
        size_bytes=document["size_bytes"],
        sha256=document["sha256"],
        created_by=document["created_by"],
    )


def _validate_schema_version(value: str, *, strict: bool) -> None:
    match = _SCHEMA_VERSION_RE.fullmatch(value)
    if match is None:
        _fail("$.schema_version", "must use MAJOR.MINOR")
    major = int(match.group(1))
    minor = int(match.group(2))
    if major != _CURRENT_MAJOR:
        raise UnsupportedVersionError(
            f"Artifact manifest schema major {major} is unsupported",
            code="GF-WB-SCHEMA-001",
            stage="reporting",
            operation="parse-manifest",
            subject=value,
        )
    if strict and minor > _CURRENT_MINOR:
        raise UnsupportedVersionError(
            f"Artifact manifest schema minor {minor} is newer than supported 1.0",
            code="GF-WB-SCHEMA-002",
            stage="reporting",
            operation="parse-manifest",
            subject=value,
        )
    if strict and value != ARTIFACT_MANIFEST_SCHEMA_VERSION:
        _fail(
            "$.schema_version",
            f"must be {ARTIFACT_MANIFEST_SCHEMA_VERSION!r}",
        )


def _canonical_timestamp(value: object, *, field: str) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            _fail(field, "must be timezone-aware")
        utc = value.astimezone(UTC)
        timespec = "microseconds" if utc.microsecond else "seconds"
        return utc.isoformat(timespec=timespec).removesuffix("+00:00") + "Z"

    text = _text(value, field)
    match = _RFC3339_UTC_RE.fullmatch(text)
    if match is None:
        _fail(field, "must be an RFC 3339 UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(text.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise SchemaValidationError(
            f"{field}: invalid calendar date or time",
            code="GF-WB-SCHEMA-003",
            stage="reporting",
            operation="parse-manifest",
            subject=field,
        ) from exc
    return text


def _mapping(value: object, field: str, *, strict: bool) -> Mapping[str, object]:
    del strict
    if not isinstance(value, Mapping):
        _fail(field, "must be a JSON object")
    for key in value:
        if not isinstance(key, str):
            _fail(field, "must contain string keys only")
    return cast(Mapping[str, object], value)


def _require_fields(
    value: Mapping[str, object],
    fields: frozenset[str],
    field: str,
) -> None:
    missing = fields.difference(value)
    if missing:
        _fail(field, f"missing required fields: {', '.join(sorted(missing))}")


def _require_exact_fields(
    value: Mapping[str, object],
    allowed: frozenset[str],
    field: str,
    *,
    required: frozenset[str],
) -> None:
    _require_fields(value, required, field)
    unexpected = set(value).difference(allowed)
    if unexpected:
        _fail(field, f"contains unknown fields: {', '.join(sorted(unexpected))}")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        _fail(field, "must be a string")
    if _NUL in value:
        _fail(field, "must not contain NUL")
    if not value.strip():
        _fail(field, "must not be empty")
    if len(value) > _MAX_TEXT_LENGTH:
        _fail(field, "exceeds the supported length limit")
    return value


def _model_text(value: object, attribute: str) -> str:
    return _text(getattr(value, attribute), attribute)


def _enum_text(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _text(value, "enum value")


def _fail(field: str, message: str) -> None:
    raise SchemaValidationError(
        f"{field}: {message}",
        code="GF-WB-SCHEMA-004",
        stage="reporting",
        operation="validate-manifest-schema",
        subject=field,
    )


parse_manifest = parse_artifact_manifest
serialize_manifest = serialize_artifact_manifest
validate_manifest = validate_artifact_manifest
canonicalize_manifest_document = canonicalize_artifact_manifest_document


__all__ = (
    "ARTIFACT_MANIFEST_FILENAME",
    "ARTIFACT_MANIFEST_HASH_ALGORITHM",
    "ARTIFACT_MANIFEST_SCHEMA_ID",
    "ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "CANONICAL_ARTIFACT_ROLES",
    "CANONICAL_MEDIA_TYPES",
    "HASH_ALGORITHM",
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_ID",
    "MANIFEST_SCHEMA_VERSION",
    "PRODUCER_NAME",
    "ArtifactManifestDocument",
    "ArtifactManifestEntryDocument",
    "CompatibleArtifactManifestDocument",
    "ProducerDocument",
    "artifact_manifest_entry_document",
    "artifact_path_comparison_key",
    "canonicalize_artifact_manifest_document",
    "canonicalize_manifest_document",
    "is_supported_artifact_manifest_version",
    "normalize_artifact_path",
    "parse_artifact_manifest",
    "parse_manifest",
    "producer_document",
    "serialize_artifact_manifest",
    "serialize_manifest",
    "validate_artifact_manifest",
    "validate_manifest",
)
