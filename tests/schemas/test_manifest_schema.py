from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
import pytest

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.reporting.manifest.models import (
    ArtifactManifest,
    ArtifactManifestEntry,
)
from gf_wordbench.reporting.schemas import manifest_v1
from gf_wordbench.reporting.schemas.manifest_v1 import (
    ARTIFACT_MANIFEST_FILENAME,
    ARTIFACT_MANIFEST_HASH_ALGORITHM,
    ARTIFACT_MANIFEST_SCHEMA_ID,
    ARTIFACT_MANIFEST_SCHEMA_VERSION,
    CANONICAL_ARTIFACT_ROLES,
    CANONICAL_MEDIA_TYPES,
    PRODUCER_NAME,
    artifact_manifest_entry_document,
    artifact_path_comparison_key,
    canonicalize_artifact_manifest_document,
    is_supported_artifact_manifest_version,
    normalize_artifact_path,
    parse_artifact_manifest,
    producer_document,
    serialize_artifact_manifest,
    validate_artifact_manifest,
)

_RUN_ID = "20260725_153043"
_GENERATED_AT = "2026-07-25T19:30:43Z"
_SHA_A = "a" * 64
_SHA_B = "b" * 64


def _entry(
    path: str = "summary.json",
    *,
    role: str = "machine_summary",
    media_type: str = "application/json",
    required: bool = True,
    size_bytes: int = 128,
    sha256: str = _SHA_A,
    created_by: str = "reporting_json",
) -> dict[str, object]:
    return {
        "path": path,
        "role": role,
        "media_type": media_type,
        "required": required,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "created_by": created_by,
    }


def _document(
    *,
    artifacts: list[dict[str, object]] | None = None,
    schema_version: str = ARTIFACT_MANIFEST_SCHEMA_VERSION,
) -> dict[str, object]:
    return {
        "schema_id": ARTIFACT_MANIFEST_SCHEMA_ID,
        "schema_version": schema_version,
        "producer": {
            "name": PRODUCER_NAME,
            "version": "1.0.0",
        },
        "run_id": _RUN_ID,
        "generated_at": _GENERATED_AT,
        "hash_algorithm": ARTIFACT_MANIFEST_HASH_ALGORITHM,
        "artifacts": list(artifacts or []),
    }


def test_manifest_schema_constants_are_locked() -> None:
    assert ARTIFACT_MANIFEST_SCHEMA_ID == "gf-wordbench.artifact-manifest"
    assert ARTIFACT_MANIFEST_SCHEMA_VERSION == "1.0"
    assert ARTIFACT_MANIFEST_FILENAME == "manifest.json"
    assert ARTIFACT_MANIFEST_HASH_ALGORITHM == "sha256"
    assert PRODUCER_NAME == "gf-wordbench"
    assert manifest_v1.MANIFEST_SCHEMA_ID == ARTIFACT_MANIFEST_SCHEMA_ID
    assert manifest_v1.MANIFEST_SCHEMA_VERSION == ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert manifest_v1.MANIFEST_FILENAME == ARTIFACT_MANIFEST_FILENAME
    assert manifest_v1.HASH_ALGORITHM == ARTIFACT_MANIFEST_HASH_ALGORITHM


def test_manifest_schema_has_exact_canonical_vocabularies() -> None:
    assert CANONICAL_ARTIFACT_ROLES == frozenset(
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
    assert CANONICAL_MEDIA_TYPES == frozenset(
        {
            "application/json",
            "text/markdown; charset=utf-8",
            "text/plain; charset=utf-8",
            "application/octet-stream",
        }
    )


def test_canonicalization_sorts_entries_and_normalizes_paths() -> None:
    document = _document(
        artifacts=[
            _entry(
                "raw//compile/./stderr.log",
                role="compile_stderr",
                media_type="text/plain; charset=utf-8",
                required=False,
                sha256=_SHA_B,
                created_by="validation_compiler",
            ),
            _entry("summary.json"),
        ]
    )

    canonical = canonicalize_artifact_manifest_document(document, strict=True)

    assert [entry["path"] for entry in canonical["artifacts"]] == [
        "raw/compile/stderr.log",
        "summary.json",
    ]
    assert canonical["producer"] == {
        "name": "gf-wordbench",
        "version": "1.0.0",
    }
    assert canonical["generated_at"] == _GENERATED_AT


def test_parse_and_serialize_round_trip_through_immutable_models() -> None:
    document = canonicalize_artifact_manifest_document(
        _document(
            artifacts=[
                _entry("summary.json"),
                _entry(
                    "summary.md",
                    role="human_summary",
                    media_type="text/markdown; charset=utf-8",
                    required=True,
                    size_bytes=256,
                    sha256=_SHA_B,
                    created_by="reporting_markdown",
                ),
            ]
        ),
        strict=True,
    )

    model = parse_artifact_manifest(document, strict=True)

    assert isinstance(model, ArtifactManifest)
    assert model.run_id == _RUN_ID
    assert model.entry_count == 2
    assert model.required_entry_count == 2
    assert model.total_size_bytes == 384
    assert model.required_artifacts == model.artifacts
    assert model.get_entry("summary.json") is model.artifacts[0]
    assert model.get_entry("details/missing.json") is None
    assert all(isinstance(entry, ArtifactManifestEntry) for entry in model.artifacts)
    assert serialize_artifact_manifest(model) == document
    validate_artifact_manifest(model)

    with pytest.raises(FrozenInstanceError):
        model.run_id = "20260725_153044"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        model.artifacts[0].path = "other.json"  # type: ignore[misc]


def test_constructors_return_canonical_typed_documents() -> None:
    producer = producer_document("2.4.1")
    entry = artifact_manifest_entry_document(
        path="details/result.json",
        role="detail",
        media_type="application/json",
        required=False,
        size_bytes=0,
        sha256="0" * 64,
        created_by="reporting_details",
    )

    assert producer == {"name": "gf-wordbench", "version": "2.4.1"}
    assert entry == {
        "path": "details/result.json",
        "role": "detail",
        "media_type": "application/json",
        "required": False,
        "size_bytes": 0,
        "sha256": "0" * 64,
        "created_by": "reporting_details",
    }


def test_compatibility_mode_discards_unknown_fields_but_strict_mode_rejects_them() -> None:
    document = _document(artifacts=[_entry()])
    document["extensions"] = {"consumer": "example"}
    artifact = document["artifacts"][0]  # type: ignore[index]
    assert isinstance(artifact, dict)
    artifact["extension_field"] = "ignored"

    compatible = canonicalize_artifact_manifest_document(document, strict=False)

    assert "extensions" not in compatible
    assert "extension_field" not in compatible["artifacts"][0]
    with pytest.raises(SchemaValidationError, match="unknown fields"):
        canonicalize_artifact_manifest_document(document, strict=True)


def test_supported_version_rules_are_major_version_aware() -> None:
    assert is_supported_artifact_manifest_version("1.0") is True
    assert is_supported_artifact_manifest_version("1.99") is True
    assert is_supported_artifact_manifest_version("2.0") is False
    assert is_supported_artifact_manifest_version("1") is False
    assert is_supported_artifact_manifest_version(1.0) is False

    compatible = canonicalize_artifact_manifest_document(
        _document(schema_version="1.7"),
        strict=False,
    )
    assert compatible["schema_version"] == "1.7"

    with pytest.raises(UnsupportedVersionError):
        canonicalize_artifact_manifest_document(
            _document(schema_version="1.7"),
            strict=True,
        )
    with pytest.raises(UnsupportedVersionError):
        canonicalize_artifact_manifest_document(
            _document(schema_version="2.0"),
            strict=False,
        )


@pytest.mark.parametrize(
    "path",
    [
        "manifest.json",
        "/absolute.json",
        "C:/absolute.json",
        "C:\\absolute.json",
        "//server/share.json",
        "../escape.json",
        "nested/../../escape.json",
        "https://example.invalid/artifact.json",
        "folder/",
        "",
        ".",
        "nul\x00name.json",
    ],
)
def test_artifact_paths_reject_self_reference_and_unsafe_values(path: str) -> None:
    with pytest.raises(SchemaValidationError):
        normalize_artifact_path(path)


def test_artifact_path_comparison_is_portable_and_case_insensitive() -> None:
    assert normalize_artifact_path("raw//compile/./stdout.log") == (
        "raw/compile/stdout.log"
    )
    assert artifact_path_comparison_key("Logs/Result.JSON") == (
        "logs/result.json"
    )

    duplicate = _document(
        artifacts=[
            _entry("Logs/Result.JSON", role="other"),
            _entry(
                "logs/result.json",
                role="other",
                sha256=_SHA_B,
            ),
        ]
    )
    with pytest.raises(SchemaValidationError, match="duplicates artifact path"):
        canonicalize_artifact_manifest_document(duplicate, strict=True)


@pytest.mark.parametrize(
    ("role", "media_type"),
    [
        ("machine_summary", "text/plain; charset=utf-8"),
        ("human_summary", "application/json"),
        ("compile_stderr", "application/octet-stream"),
        ("gfo", "text/plain; charset=utf-8"),
        ("pgf", "application/json"),
    ],
)
def test_role_media_type_pairs_are_enforced(role: str, media_type: str) -> None:
    document = _document(
        artifacts=[_entry(role=role, media_type=media_type)]
    )
    with pytest.raises(SchemaValidationError, match="incompatible with role"):
        canonicalize_artifact_manifest_document(document, strict=True)


def test_unknown_roles_and_noncanonical_producer_ids_are_rejected() -> None:
    unknown_role = _document(artifacts=[_entry(role="custom_role")])
    with pytest.raises(SchemaValidationError, match="unknown artifact role"):
        canonicalize_artifact_manifest_document(unknown_role, strict=True)

    bad_creator = _document(
        artifacts=[_entry(created_by="Reporting JSON")]
    )
    with pytest.raises(SchemaValidationError, match="lower_snake_case"):
        canonicalize_artifact_manifest_document(bad_creator, strict=True)


def test_entry_scalar_types_and_hash_format_are_exact() -> None:
    invalid_documents = [
        _document(artifacts=[_entry(required=1)]),  # type: ignore[arg-type]
        _document(artifacts=[_entry(size_bytes=True)]),
        _document(artifacts=[_entry(size_bytes=-1)]),
        _document(artifacts=[_entry(sha256="A" * 64)]),
        _document(artifacts=[_entry(sha256="a" * 63)]),
    ]

    for document in invalid_documents:
        with pytest.raises(SchemaValidationError):
            canonicalize_artifact_manifest_document(document, strict=True)


def test_root_identity_and_algorithm_are_enforced() -> None:
    mutations = (
        ("schema_id", "example.manifest"),
        ("run_id", "not-a-run-id"),
        ("hash_algorithm", "sha512"),
    )
    for field, value in mutations:
        document = _document()
        document[field] = value
        with pytest.raises((SchemaValidationError, ValueError)):
            canonicalize_artifact_manifest_document(document, strict=True)

    document = _document()
    producer = document["producer"]
    assert isinstance(producer, dict)
    producer["name"] = "other-producer"
    with pytest.raises(SchemaValidationError, match="producer.name"):
        canonicalize_artifact_manifest_document(document, strict=True)


def test_generated_at_is_canonical_rfc3339_utc() -> None:
    document = _document()
    document["generated_at"] = datetime(
        2026,
        7,
        25,
        15,
        30,
        43,
        125000,
        tzinfo=timezone(-timedelta(hours=4)),
    )

    canonical = canonicalize_artifact_manifest_document(document, strict=True)
    assert canonical["generated_at"] == "2026-07-25T19:30:43.125000Z"

    for invalid in (
        "2026-07-25T19:30:43+00:00",
        "2026-07-25 19:30:43Z",
        "2026-02-30T19:30:43Z",
        datetime(2026, 7, 25, 19, 30, 43),
    ):
        bad = _document()
        bad["generated_at"] = invalid
        with pytest.raises(SchemaValidationError):
            canonicalize_artifact_manifest_document(bad, strict=True)


def test_manifest_aliases_reference_the_canonical_implementations() -> None:
    assert manifest_v1.parse_manifest is parse_artifact_manifest
    assert manifest_v1.serialize_manifest is serialize_artifact_manifest
    assert manifest_v1.validate_manifest is validate_artifact_manifest
    assert (
        manifest_v1.canonicalize_manifest_document
        is canonicalize_artifact_manifest_document
    )


def test_canonicalization_does_not_mutate_untrusted_input() -> None:
    document = _document(
        artifacts=[
            _entry(
                "raw//stdout.log",
                role="compile_stdout",
                media_type="text/plain; charset=utf-8",
                required=False,
            )
        ]
    )
    original = deepcopy(document)

    canonicalize_artifact_manifest_document(document, strict=True)

    assert document == original
