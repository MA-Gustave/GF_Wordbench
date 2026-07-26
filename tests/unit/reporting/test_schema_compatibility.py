"""Unit tests for persisted-schema identity and compatibility policy."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from gf_wordbench.kernel.errors import (
    SchemaValidationError,
    UnsupportedVersionError,
)
from gf_wordbench.reporting.schemas.compatibility import (
    CompatibilityReason,
    CompatibilityStatus,
    SchemaCompatibilityPolicy,
    SchemaCompatibilityResult,
    SchemaIdentity,
    SchemaVersion,
    check_schema_compatibility,
    extract_schema_identity,
    is_schema_compatible,
    parse_schema_version,
    require_current_schema,
    require_schema_compatibility,
)

_SCHEMA_ID = "gf-wordbench.run-summary"
_OTHER_SCHEMA_ID = "gf-wordbench.artifact-manifest"


def _identity(
    version: str = "1.0",
    *,
    schema_id: str = _SCHEMA_ID,
) -> SchemaIdentity:
    return SchemaIdentity.from_values(schema_id, version)


def _document(
    version: object = "1.0",
    *,
    schema_id: object = _SCHEMA_ID,
) -> dict[str, object]:
    return {
        "schema_id": schema_id,
        "schema_version": version,
    }


def _policy(**overrides: object) -> SchemaCompatibilityPolicy:
    values: dict[str, object] = {
        "schema_id": _SCHEMA_ID,
        "current_version": SchemaVersion.parse("1.2"),
    }
    values.update(overrides)
    return SchemaCompatibilityPolicy(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected", "components"),
    [
        ("0.0", (0, 0, 0), 2),
        ("1.2", (1, 2, 0), 2),
        ("1.2.0", (1, 2, 0), 3),
        ("12.34.56", (12, 34, 56), 3),
    ],
)
def test_parse_schema_version_preserves_components(
    raw: str,
    expected: tuple[int, int, int],
    components: int,
) -> None:
    version = parse_schema_version(raw)

    assert (version.major, version.minor, version.patch) == expected
    assert version.components == components
    assert str(version) == raw
    assert parse_schema_version(version) is version


@pytest.mark.parametrize(
    "raw",
    [
        "",
        " 1.0",
        "1.0 ",
        "1",
        "1.",
        ".1",
        "1.2.3.4",
        "01.0",
        "1.02",
        "1.2.-1",
        "v1.0",
        "1.0\x00",
    ],
)
def test_parse_schema_version_rejects_noncanonical_text(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_schema_version(raw)


def test_parse_schema_version_rejects_non_text() -> None:
    with pytest.raises(TypeError, match="schema version must be a string"):
        parse_schema_version(1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"major": True, "minor": 0}, TypeError, "major must be an integer"),
        ({"major": 1, "minor": -1}, ValueError, "minor must be non-negative"),
        (
            {"major": 1, "minor": 0, "patch": 1, "components": 2},
            ValueError,
            "two-component version",
        ),
        (
            {"major": 1, "minor": 0, "components": 4},
            ValueError,
            "components must be 2 or 3",
        ),
    ],
)
def test_schema_version_validates_direct_construction(
    kwargs: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        SchemaVersion(**kwargs)  # type: ignore[arg-type]


def test_schema_version_comparison_helpers_use_numeric_components() -> None:
    older = SchemaVersion.parse("1.1.9")
    current = SchemaVersion.parse("1.2")
    newer = SchemaVersion.parse("1.2.1")
    next_major = SchemaVersion.parse("2.0")

    assert older < current < newer < next_major
    assert current.sort_key == (1, 2, 0)
    assert current.same_major(newer) is True
    assert current.same_major(next_major) is False
    assert current.same_minor_line(newer) is True
    assert current.same_minor_line(older) is False


def test_schema_version_is_frozen_and_slotted() -> None:
    version = SchemaVersion.parse("1.0")

    assert not hasattr(version, "__dict__")
    with pytest.raises(FrozenInstanceError):
        version.major = 2  # type: ignore[misc]


@pytest.mark.parametrize(
    "schema_id",
    [
        "gf-wordbench.run-summary",
        "gf-wordbench.scenario-output",
        "wordbench.schema-v1",
        "a.b",
    ],
)
def test_schema_identity_accepts_canonical_ids(schema_id: str) -> None:
    identity = SchemaIdentity.from_values(schema_id, "1.0")

    assert identity.schema_id == schema_id
    assert identity.schema_version == SchemaVersion.parse("1.0")
    assert identity.as_mapping() == {
        "schema_id": schema_id,
        "schema_version": "1.0",
    }


@pytest.mark.parametrize(
    "schema_id",
    [
        "",
        " gf-wordbench.run-summary",
        "gf-wordbench.run-summary ",
        "GF-wordbench.run-summary",
        "gf_wordbench.run_summary",
        "gf-wordbench",
        ".gf-wordbench",
        "gf-wordbench.",
        "gf..wordbench",
        "gf-wordbench.résumé",
        "gf-wordbench.run-summary\x00",
    ],
)
def test_schema_identity_rejects_invalid_ids(schema_id: str) -> None:
    with pytest.raises(ValueError):
        SchemaIdentity.from_values(schema_id, "1.0")


def test_schema_identity_mapping_is_read_only() -> None:
    mapping = _identity().as_mapping()

    assert isinstance(mapping, MappingProxyType)
    with pytest.raises(TypeError):
        mapping["schema_version"] = "2.0"  # type: ignore[index]


def test_exact_policy_owns_one_current_identity() -> None:
    policy = SchemaCompatibilityPolicy.exact(_SCHEMA_ID, "1.2")

    assert policy.current_identity == _identity("1.2")
    assert policy.readable_versions == frozenset()
    assert policy.historical_versions == frozenset()
    assert policy.migration_sources == frozenset()
    assert policy.allow_newer_patch is False
    assert policy.allow_newer_minor is False
    assert policy.allow_unknown_optional_fields is False
    assert policy.all_explicit_versions == {SchemaVersion.parse("1.2")}


def test_additive_minor_policy_normalizes_declared_versions() -> None:
    policy = SchemaCompatibilityPolicy.additive_minor_reader(
        _SCHEMA_ID,
        "1.2",
        readable_versions=("1.1",),
        historical_versions=("0.9",),
        migration_sources=("0.8",),
    )

    assert policy.current_version == SchemaVersion.parse("1.2")
    assert policy.readable_versions == {SchemaVersion.parse("1.1")}
    assert policy.historical_versions == {SchemaVersion.parse("0.9")}
    assert policy.migration_sources == {SchemaVersion.parse("0.8")}
    assert policy.allow_newer_patch is True
    assert policy.allow_newer_minor is True
    assert policy.allow_unknown_optional_fields is True
    assert policy.all_explicit_versions == {
        SchemaVersion.parse("1.2"),
        SchemaVersion.parse("1.1"),
        SchemaVersion.parse("0.9"),
        SchemaVersion.parse("0.8"),
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"historical_versions": frozenset({SchemaVersion.parse("1.2")})},
         "current_version cannot be historical"),
        ({"migration_sources": frozenset({SchemaVersion.parse("1.2")})},
         "current_version cannot be historical"),
        (
            {
                "readable_versions": frozenset({SchemaVersion.parse("1.1")}),
                "historical_versions": frozenset({SchemaVersion.parse("1.1")}),
            },
            "readable_versions and historical_versions",
        ),
        (
            {
                "readable_versions": frozenset({SchemaVersion.parse("1.1")}),
                "migration_sources": frozenset({SchemaVersion.parse("1.1")}),
            },
            "readable_versions and migration_sources",
        ),
        (
            {
                "historical_versions": frozenset({SchemaVersion.parse("1.1")}),
                "migration_sources": frozenset({SchemaVersion.parse("1.1")}),
            },
            "historical_versions and migration_sources",
        ),
        (
            {
                "allow_newer_minor": True,
                "allow_unknown_optional_fields": False,
            },
            "allow_newer_minor requires allow_unknown_optional_fields",
        ),
    ],
)
def test_policy_rejects_ambiguous_support_classes(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _policy(**overrides)


@pytest.mark.parametrize(
    "field",
    [
        "allow_newer_patch",
        "allow_newer_minor",
        "allow_unknown_optional_fields",
    ],
)
def test_policy_boolean_flags_are_strict(field: str) -> None:
    with pytest.raises(TypeError, match=f"{field} must be a bool"):
        _policy(**{field: 1})


def test_policy_rejects_scalar_version_collections() -> None:
    with pytest.raises(TypeError, match="readable_versions must be an iterable"):
        _policy(readable_versions="1.1")


def test_exact_identity_is_classified_for_document_and_identity() -> None:
    policy = _policy()

    from_document = check_schema_compatibility(_document("1.2"), policy)
    from_identity = check_schema_compatibility(_identity("1.2"), policy)

    assert from_document == from_identity
    assert from_document.status is CompatibilityStatus.EXACT
    assert from_document.reason is CompatibilityReason.EXACT_MATCH
    assert from_document.expected == policy.current_identity
    assert from_document.observed == _identity("1.2")
    assert from_document.readable is True
    assert from_document.exact is True
    assert from_document.historical is False
    assert from_document.requires_migration is False
    assert from_document.canonical_write_allowed is True


@pytest.mark.parametrize(
    ("version", "field", "status", "reason"),
    [
        (
            "1.1",
            "readable_versions",
            CompatibilityStatus.COMPATIBLE,
            CompatibilityReason.EXPLICIT_READ_SUPPORT,
        ),
        (
            "0.9",
            "historical_versions",
            CompatibilityStatus.HISTORICAL_READ,
            CompatibilityReason.HISTORICAL_ADAPTER,
        ),
        (
            "0.8",
            "migration_sources",
            CompatibilityStatus.MIGRATION_REQUIRED,
            CompatibilityReason.EXPLICIT_MIGRATION,
        ),
    ],
)
def test_explicit_support_classes_take_precedence(
    version: str,
    field: str,
    status: CompatibilityStatus,
    reason: CompatibilityReason,
) -> None:
    policy = _policy(**{field: frozenset({SchemaVersion.parse(version)})})

    result = check_schema_compatibility(_document(version), policy)

    assert result.status is status
    assert result.reason is reason
    assert result.readable is (status in {
        CompatibilityStatus.COMPATIBLE,
        CompatibilityStatus.HISTORICAL_READ,
    })
    assert result.historical is (status is CompatibilityStatus.HISTORICAL_READ)
    assert result.requires_migration is (
        status is CompatibilityStatus.MIGRATION_REQUIRED
    )
    assert result.canonical_write_allowed is False


def test_wrong_schema_id_is_structured_incompatibility() -> None:
    result = check_schema_compatibility(
        _document("1.2", schema_id=_OTHER_SCHEMA_ID),
        _policy(),
    )

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert result.reason is CompatibilityReason.WRONG_SCHEMA_ID
    assert result.observed == _identity("1.2", schema_id=_OTHER_SCHEMA_ID)
    assert _SCHEMA_ID in result.message
    assert _OTHER_SCHEMA_ID in result.message


@pytest.mark.parametrize(
    ("document", "reason"),
    [
        ({"schema_version": "1.2"}, CompatibilityReason.MISSING_SCHEMA_ID),
        ({"schema_id": _SCHEMA_ID}, CompatibilityReason.MISSING_SCHEMA_VERSION),
        (
            {"schema_id": 4, "schema_version": "1.2"},
            CompatibilityReason.MALFORMED_SCHEMA_ID,
        ),
        (
            {"schema_id": "invalid", "schema_version": "1.2"},
            CompatibilityReason.MALFORMED_SCHEMA_ID,
        ),
        (
            {"schema_id": _SCHEMA_ID, "schema_version": 4},
            CompatibilityReason.MALFORMED_SCHEMA_VERSION,
        ),
        (
            {"schema_id": _SCHEMA_ID, "schema_version": "1"},
            CompatibilityReason.MALFORMED_SCHEMA_VERSION,
        ),
    ],
)
def test_malformed_identity_returns_bounded_result(
    document: dict[str, object],
    reason: CompatibilityReason,
) -> None:
    result = check_schema_compatibility(document, _policy())

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert result.reason is reason
    assert result.observed is None
    assert result.expected == _identity("1.2")
    assert result.readable is False


@pytest.mark.parametrize(
    ("version", "reason"),
    [
        ("0.9", CompatibilityReason.UNSUPPORTED_MAJOR),
        ("2.0", CompatibilityReason.UNSUPPORTED_MAJOR),
        ("1.1", CompatibilityReason.UNSUPPORTED_OLDER_VERSION),
        ("1.2.1", CompatibilityReason.UNSUPPORTED_NEWER_PATCH),
        ("1.3", CompatibilityReason.UNSUPPORTED_NEWER_MINOR),
    ],
)
def test_exact_policy_rejects_undeclared_versions(
    version: str,
    reason: CompatibilityReason,
) -> None:
    result = check_schema_compatibility(_document(version), _policy())

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert result.reason is reason
    assert result.readable is False


def test_patch_compatible_policy_accepts_newer_patch_only() -> None:
    policy = _policy(allow_newer_patch=True)

    patch = check_schema_compatibility(_document("1.2.7"), policy)
    minor = check_schema_compatibility(_document("1.3"), policy)

    assert patch.status is CompatibilityStatus.COMPATIBLE
    assert patch.reason is CompatibilityReason.COMPATIBLE_NEWER_PATCH
    assert minor.status is CompatibilityStatus.INCOMPATIBLE
    assert minor.reason is CompatibilityReason.UNSUPPORTED_NEWER_MINOR


def test_additive_minor_policy_accepts_newer_same_major_versions() -> None:
    policy = SchemaCompatibilityPolicy.additive_minor_reader(
        _SCHEMA_ID,
        "1.2",
    )

    patch = check_schema_compatibility(_document("1.2.1"), policy)
    minor = check_schema_compatibility(_document("1.99"), policy)
    major = check_schema_compatibility(_document("2.0"), policy)

    assert patch.reason is CompatibilityReason.COMPATIBLE_NEWER_PATCH
    assert minor.reason is CompatibilityReason.COMPATIBLE_NEWER_MINOR
    assert patch.readable is True
    assert minor.readable is True
    assert major.reason is CompatibilityReason.UNSUPPORTED_MAJOR
    assert major.readable is False


def test_is_schema_compatible_includes_historical_read_support() -> None:
    policy = _policy(
        historical_versions=frozenset({SchemaVersion.parse("0.9")})
    )

    assert is_schema_compatible(_document("1.2"), policy) is True
    assert is_schema_compatible(_document("0.9"), policy) is True
    assert is_schema_compatible(_document("0.8"), policy) is False


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ({}, "GF-WB-SCHEMA-002"),
        ({"schema_id": _SCHEMA_ID}, "GF-WB-SCHEMA-003"),
        (
            {"schema_id": 1, "schema_version": "1.0"},
            "GF-WB-SCHEMA-004",
        ),
        (
            {"schema_id": _SCHEMA_ID, "schema_version": 1},
            "GF-WB-SCHEMA-005",
        ),
        (
            {"schema_id": "invalid", "schema_version": "1.0"},
            "GF-WB-SCHEMA-006",
        ),
    ],
)
def test_extract_schema_identity_reports_owned_validation_codes(
    document: dict[str, object],
    code: str,
) -> None:
    with pytest.raises(SchemaValidationError) as caught:
        extract_schema_identity(document)

    assert caught.value.code == code
    assert caught.value.stage == "reporting"
    assert caught.value.operation == "extract-schema-identity"


def test_extract_schema_identity_requires_mapping() -> None:
    with pytest.raises(SchemaValidationError) as caught:
        extract_schema_identity([])  # type: ignore[arg-type]

    assert caught.value.code == "GF-WB-SCHEMA-001"


def test_require_schema_compatibility_accepts_exact_compatible_and_historical() -> None:
    policy = _policy(
        readable_versions=frozenset({SchemaVersion.parse("1.1")}),
        historical_versions=frozenset({SchemaVersion.parse("0.9")}),
    )

    assert require_schema_compatibility(_document("1.2"), policy).exact is True
    assert (
        require_schema_compatibility(_document("1.1"), policy).status
        is CompatibilityStatus.COMPATIBLE
    )
    assert (
        require_schema_compatibility(_document("0.9"), policy).historical
        is True
    )


def test_require_schema_compatibility_can_reject_historical_input() -> None:
    policy = _policy(
        historical_versions=frozenset({SchemaVersion.parse("0.9")})
    )

    with pytest.raises(UnsupportedVersionError) as caught:
        require_schema_compatibility(
            _document("0.9"),
            policy,
            allow_historical=False,
        )

    error = caught.value
    assert error.code == "GF-WB-SCHEMA-008"
    assert error.operation == "require-schema-compatibility"
    assert "historical_adapter" in error.detail


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"schema_id": _SCHEMA_ID},
        {"schema_id": "invalid", "schema_version": "1.2"},
        {"schema_id": _OTHER_SCHEMA_ID, "schema_version": "1.2"},
    ],
)
def test_require_schema_compatibility_maps_identity_failures_to_schema_error(
    document: dict[str, object],
) -> None:
    with pytest.raises(SchemaValidationError) as caught:
        require_schema_compatibility(document, _policy())

    error = caught.value
    assert error.code == "GF-WB-SCHEMA-007"
    assert error.stage == "reporting"
    assert error.operation == "require-schema-compatibility"
    assert error.detail.startswith("reason=")


def test_require_schema_compatibility_reports_version_failure() -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        require_schema_compatibility(_document("2.0"), _policy())

    error = caught.value
    assert error.code == "GF-WB-SCHEMA-008"
    assert error.stage == "reporting"
    assert error.operation == "require-schema-compatibility"
    assert error.subject == _SCHEMA_ID
    assert "unsupported_major" in error.detail
    assert "observed_version='2.0'" in error.detail
    assert "current_version=1.2" in error.detail


def test_migration_required_is_not_readable_without_explicit_migration() -> None:
    policy = _policy(
        migration_sources=frozenset({SchemaVersion.parse("0.9")})
    )

    result = check_schema_compatibility(_document("0.9"), policy)

    assert result.requires_migration is True
    assert is_schema_compatible(_document("0.9"), policy) is False
    with pytest.raises(UnsupportedVersionError):
        require_schema_compatibility(_document("0.9"), policy)


def test_require_current_schema_allows_only_exact_current_identity() -> None:
    policy = _policy(
        readable_versions=frozenset({SchemaVersion.parse("1.1")})
    )

    assert require_current_schema(_document("1.2"), policy).exact is True

    with pytest.raises(UnsupportedVersionError) as caught:
        require_current_schema(_document("1.1"), policy)

    error = caught.value
    assert error.code == "GF-WB-SCHEMA-009"
    assert error.operation == "require-current-schema"
    assert "Canonical writing requires schema" in error.message
    assert "explicit_read_support" in error.detail


def test_compatibility_result_normalizes_enums_and_freezes_metadata() -> None:
    source_metadata = {"adapter": "legacy-summary"}
    result = SchemaCompatibilityResult(
        status="historical_read",  # type: ignore[arg-type]
        reason="historical_adapter",  # type: ignore[arg-type]
        expected=_identity("1.2"),
        observed=_identity("0.9"),
        message="Historical reader selected.",
        metadata=source_metadata,
    )
    source_metadata["adapter"] = "changed"

    assert result.status is CompatibilityStatus.HISTORICAL_READ
    assert result.reason is CompatibilityReason.HISTORICAL_ADAPTER
    assert result.metadata == {"adapter": "legacy-summary"}
    assert isinstance(result.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        result.metadata["adapter"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("expected", object(), "expected must be a SchemaIdentity"),
        ("observed", object(), "observed must be a SchemaIdentity or None"),
        ("message", "", "message must not be empty"),
        ("metadata", {"": "value"}, "metadata key must not be empty"),
        ("metadata", {"key": ""}, r"metadata\['key'\] must not be empty"),
    ],
)
def test_compatibility_result_validates_contract_fields(
    field: str,
    value: object,
    message: str,
) -> None:
    values: dict[str, object] = {
        "status": CompatibilityStatus.EXACT,
        "reason": CompatibilityReason.EXACT_MATCH,
        "expected": _identity("1.2"),
        "observed": _identity("1.2"),
        "message": "Exact match.",
    }
    values[field] = value

    with pytest.raises((TypeError, ValueError), match=message):
        SchemaCompatibilityResult(**values)  # type: ignore[arg-type]


def test_public_evaluators_reject_wrong_argument_types() -> None:
    with pytest.raises(TypeError, match="policy must be"):
        check_schema_compatibility(_document(), object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="mapping or SchemaIdentity"):
        check_schema_compatibility([], _policy())  # type: ignore[arg-type]
