"""Unit tests for versioned scenario-output normalization."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
from typing import Any, Final, cast

import pytest

from gf_wordbench.kernel.ids import NormalizationProfileId, SectionId
from gf_wordbench.validation.scenarios import normalization
from gf_wordbench.validation.scenarios.normalization import (
    DEFAULT_NORMALIZATION_PROFILE,
    DEFAULT_NORMALIZATION_PROFILE_ID,
    DEFAULT_NORMALIZATION_PROFILE_VERSION,
    DEFAULT_NORMALIZATION_REGISTRY,
    ExtractedScenarioSection,
    NormalizationError,
    NormalizationErrorCode,
    NormalizationProfile,
    NormalizationProfileRegistry,
    NormalizeDesignatedPathFields,
    NormalizedScenarioSection,
    NormalizeLineEndings,
    PathTokenReplacement,
    RemoveApprovedAnsiSequences,
    RemoveApprovedExactLines,
    RemoveFinalTrailingBlankLine,
    RemoveTrailingSpaces,
    ReplaceApprovedPaths,
    normalize_scenario_section,
    normalize_scenario_section_by_identity,
    normalize_scenario_sections,
    validate_normalization_version,
)

_EXPECTED_PUBLIC_NAMES: Final = (
    "DEFAULT_NORMALIZATION_PROFILE",
    "DEFAULT_NORMALIZATION_PROFILE_ID",
    "DEFAULT_NORMALIZATION_PROFILE_VERSION",
    "DEFAULT_NORMALIZATION_REGISTRY",
    "ExtractedScenarioSection",
    "NormalizationError",
    "NormalizationErrorCode",
    "NormalizationProfile",
    "NormalizationProfileRegistry",
    "NormalizationRule",
    "NormalizationRuleValue",
    "NormalizeDesignatedPathFields",
    "NormalizeLineEndings",
    "NormalizedScenarioSection",
    "PathTokenReplacement",
    "RemoveApprovedAnsiSequences",
    "RemoveApprovedExactLines",
    "RemoveFinalTrailingBlankLine",
    "RemoveTrailingSpaces",
    "ReplaceApprovedPaths",
    "normalize_scenario_section",
    "normalize_scenario_section_by_identity",
    "normalize_scenario_sections",
    "validate_normalization_version",
)


def _section(
    text: str,
    *,
    section_id: str = "parse-output",
    source_evidence: str = "stdout:12-18",
) -> ExtractedScenarioSection:
    return ExtractedScenarioSection(
        section_id=SectionId(section_id),
        text=text,
        source_evidence=source_evidence,
    )


def _profile(
    *rules: object,
    profile_id: str = "test-profile",
    version: str = "1.2.3",
) -> NormalizationProfile:
    return NormalizationProfile(
        profile_id=NormalizationProfileId(profile_id),
        version=version,
        rules=rules,  # type: ignore[arg-type]
    )


class _ExplodingRule:
    rule_id = "NORM-TEST-FAILURE-001"

    def apply(self, text: str) -> str:
        del text
        raise RuntimeError("boom")


class _NonTextRule:
    rule_id = "NORM-TEST-NONTEXT-001"

    def apply(self, text: str) -> str:
        del text
        return 42  # type: ignore[return-value]


class _IdentityRule:
    rule_id = "NORM-TEST-IDENTITY-001"

    def apply(self, text: str) -> str:
        return text


def test_module_exposes_the_canonical_public_contract() -> None:
    assert normalization.__all__ == _EXPECTED_PUBLIC_NAMES
    assert all(hasattr(normalization, name) for name in normalization.__all__)


def test_default_profile_identity_and_rule_are_stable() -> None:
    assert DEFAULT_NORMALIZATION_PROFILE_ID == "scenario-default"
    assert DEFAULT_NORMALIZATION_PROFILE_VERSION == "1.0.0"
    assert DEFAULT_NORMALIZATION_PROFILE.identity == (
        "scenario-default",
        "1.0.0",
    )
    assert DEFAULT_NORMALIZATION_PROFILE.rules == (NormalizeLineEndings(),)
    assert (
        DEFAULT_NORMALIZATION_REGISTRY.require(
            "scenario-default",
            "1.0.0",
        )
        is DEFAULT_NORMALIZATION_PROFILE
    )


@pytest.mark.parametrize(
    "value",
    ["0.0.0", "1.0.0", "10.24.300"],
)
def test_normalization_version_accepts_strict_semantic_versions(
    value: str,
) -> None:
    assert validate_normalization_version(value) == value


@pytest.mark.parametrize(
    "value",
    ["", "1", "1.0", "v1.0.0", "01.0.0", "1.01.0", "1.0.00", "1.0.0-rc1"],
)
def test_normalization_version_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        validate_normalization_version(value)


def test_normalization_version_rejects_non_text() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        validate_normalization_version(1)


def test_line_endings_are_normalized_without_changing_unicode() -> None:
    text = "Shqipëri\r\nçështje\rëmbël\n"

    assert NormalizeLineEndings().apply(text) == "Shqipëri\nçështje\nëmbël\n"


def test_final_trailing_blank_line_removal_is_narrow_and_single_step() -> None:
    rule = RemoveFinalTrailingBlankLine()

    assert rule.apply("one\n\n") == "one\n"
    assert rule.apply("one\n  \t\n") == "one\n"
    assert rule.apply("one\n\n\n") == "one\n\n"
    assert rule.apply("one\n") == "one\n"
    assert rule.apply("one") == "one"


def test_approved_path_replacement_is_literal_ordered_and_declared() -> None:
    rule = ReplaceApprovedPaths(
        (
            PathTokenReplacement("C:\\runs\\42", "<RUN_ROOT>"),
            PathTokenReplacement("C:\\project", "<PROJECT_ROOT>"),
        )
    )
    text = "run=C:\\runs\\42\\out\nproject=C:\\project\nother=C:\\temp\n"

    assert rule.apply(text) == ("run=<RUN_ROOT>\\out\nproject=<PROJECT_ROOT>\nother=C:\\temp\n")


def test_path_token_replacement_rejects_unsafe_declarations() -> None:
    with pytest.raises(ValueError, match="line ending"):
        PathTokenReplacement("C:\\run\nnext", "<RUN_ROOT>")
    with pytest.raises(ValueError, match="UPPERCASE_TOKEN"):
        PathTokenReplacement("C:\\run", "<run_root>")
    with pytest.raises(ValueError, match="UPPERCASE_TOKEN"):
        PathTokenReplacement("C:\\run", "RUN_ROOT")
    with pytest.raises(ValueError, match="unique"):
        ReplaceApprovedPaths(
            (
                PathTokenReplacement("C:\\run", "<RUN_ROOT>"),
                PathTokenReplacement("C:\\run", "<OTHER_ROOT>"),
            )
        )


def test_only_designated_path_fields_receive_portable_separators() -> None:
    rule = NormalizeDesignatedPathFields(("path", "artifact_path"))
    text = (
        "path: C:\\work\\Main.gf\r\n"
        "  artifact_path = D:\\runs\\artifact.json\n"
        "message: C:\\must\\remain\\native\n"
        "pathology: C:\\not-a-path-field\n"
    )

    assert rule.apply(text) == (
        "path: C:/work/Main.gf\r\n"
        "  artifact_path = D:/runs/artifact.json\n"
        "message: C:\\must\\remain\\native\n"
        "pathology: C:\\not-a-path-field\n"
    )


def test_designated_path_field_configuration_is_strict() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        NormalizeDesignatedPathFields(())
    with pytest.raises(ValueError, match="unique"):
        NormalizeDesignatedPathFields(("path", "path"))
    with pytest.raises(ValueError, match="stable field identifiers"):
        NormalizeDesignatedPathFields(("bad field",))
    with pytest.raises(ValueError, match="only ':' and '='"):
        NormalizeDesignatedPathFields(("path",), separators=("-",))


def test_exact_line_removal_preserves_order_duplicates_and_near_matches() -> None:
    rule = RemoveApprovedExactLines(("gf> ", "GF 3.12"))
    text = "GF 3.12\ngf> \nanswer\nanswer\n gf> \ngf> x\n"

    assert rule.apply(text) == "answer\nanswer\n gf> \ngf> x\n"


def test_exact_line_removal_rejects_ambiguous_declarations() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        RemoveApprovedExactLines(())
    with pytest.raises(ValueError, match="unique"):
        RemoveApprovedExactLines(("banner", "banner"))
    with pytest.raises(ValueError, match="line endings"):
        RemoveApprovedExactLines(("banner\n",))


def test_only_explicitly_approved_ansi_sequences_are_removed() -> None:
    red = "\x1b[31m"
    reset = "\x1b[0m"
    green = "\x1b[32m"
    rule = RemoveApprovedAnsiSequences((red, reset))

    assert rule.apply(f"{red}error{reset} {green}kept") == f"error {green}kept"


def test_ansi_sequence_configuration_requires_escape_prefixed_values() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        RemoveApprovedAnsiSequences(())
    with pytest.raises(ValueError, match="unique"):
        RemoveApprovedAnsiSequences(("\x1b[0m", "\x1b[0m"))
    with pytest.raises(ValueError, match="begin with ESC"):
        RemoveApprovedAnsiSequences(("[0m",))


def test_trailing_space_removal_preserves_line_endings_and_meaningful_space() -> None:
    text = "  first  \r\nsecond\t\nthird  "

    assert RemoveTrailingSpaces().apply(text) == "  first\r\nsecond\nthird"


def test_rule_ids_are_validated_at_construction() -> None:
    with pytest.raises(ValueError, match="NORM-<DOMAIN>-<NNN>"):
        NormalizeLineEndings(rule_id="line-endings")
    with pytest.raises(TypeError, match="rule_id must be a string"):
        NormalizeLineEndings(rule_id=1)  # type: ignore[arg-type]


def test_profile_freezes_rules_and_rejects_duplicate_rule_ids() -> None:
    rules = [NormalizeLineEndings(), RemoveTrailingSpaces()]
    profile = NormalizationProfile(
        profile_id=NormalizationProfileId("stable-profile"),
        version="2.0.0",
        rules=rules,  # type: ignore[arg-type]
    )
    rules.clear()

    assert profile.rules == (NormalizeLineEndings(), RemoveTrailingSpaces())
    assert not hasattr(profile, "__dict__")
    with pytest.raises(FrozenInstanceError):
        profile.version = "3.0.0"  # type: ignore[misc]

    with pytest.raises(NormalizationError) as captured:
        _profile(NormalizeLineEndings(), NormalizeLineEndings())
    assert captured.value.code is NormalizationErrorCode.INVALID_PROFILE
    assert captured.value.profile_id == "test-profile"
    assert captured.value.profile_version == "1.2.3"


def test_profile_rejects_values_that_do_not_implement_rule_protocol() -> None:
    with pytest.raises(TypeError, match=r"rules\[0\]"):
        _profile(object())


def test_extracted_section_validates_identity_evidence_and_raw_content() -> None:
    section = _section("dy\n", source_evidence="stdout:1-1")

    assert section.section_id == "parse-output"
    assert section.text == "dy\n"
    assert section.source_evidence == "stdout:1-1"
    assert not hasattr(section, "__dict__")

    with pytest.raises(ValueError, match="scenario section ID"):
        _section("text", section_id="Bad_ID")
    with pytest.raises(ValueError, match="source_evidence"):
        _section("text", source_evidence="   ")
    with pytest.raises(NormalizationError) as captured:
        _section("bad\x00text")
    assert captured.value.code is NormalizationErrorCode.INVALID_SECTION


def test_normalize_section_applies_rules_in_declared_order() -> None:
    profile = _profile(
        NormalizeLineEndings(),
        RemoveTrailingSpaces(),
        RemoveFinalTrailingBlankLine(),
    )

    result = normalize_scenario_section(
        _section("një  \r\n\r\n"),
        profile=profile,
    )

    assert result.normalized_text == "një\n"
    assert result.applied_rule_ids == (
        "NORM-LINE-ENDINGS-001",
        "NORM-TRAILING-SPACES-001",
        "NORM-FINAL-BLANK-LINE-001",
    )
    assert result.changed is True


def test_normalized_section_records_reproducible_evidence_and_utf8_sizes() -> None:
    source = "Shqipëri\r\n"
    expected = "Shqipëri\n"
    profile = _profile(NormalizeLineEndings())

    result = normalize_scenario_section(_section(source), profile=profile)

    assert result.section_id == "parse-output"
    assert result.source_evidence == "stdout:12-18"
    assert result.profile_id == "test-profile"
    assert result.profile_version == "1.2.3"
    assert result.source_sha256 == hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert result.normalized_sha256 == hashlib.sha256(expected.encode("utf-8")).hexdigest()
    assert result.source_size_bytes == len(source.encode("utf-8"))
    assert result.normalized_size_bytes == len(expected.encode("utf-8"))
    assert result.normalized_text == expected


def test_identity_rule_records_unchanged_output_without_losing_evidence() -> None:
    result = normalize_scenario_section(
        _section("a\na\n"),
        profile=_profile(_IdentityRule()),
    )

    assert result.normalized_text == "a\na\n"
    assert result.changed is False
    assert result.source_sha256 == result.normalized_sha256
    assert result.source_size_bytes == result.normalized_size_bytes


def test_normalization_does_not_sort_deduplicate_or_rewrite_unicode() -> None:
    raw = "z\nç\na\na\në\n"

    result = normalize_scenario_section(
        _section(raw),
        profile=_profile(NormalizeLineEndings()),
    )

    assert result.normalized_text == raw


def test_rule_failures_are_wrapped_with_full_context() -> None:
    with pytest.raises(NormalizationError) as captured:
        normalize_scenario_section(
            _section("text", section_id="load-main"),
            profile=_profile(_ExplodingRule()),
        )

    error = captured.value
    assert error.code is NormalizationErrorCode.INVALID_RULE
    assert error.profile_id == "test-profile"
    assert error.profile_version == "1.2.3"
    assert error.section_id == "load-main"
    assert error.rule_id == "NORM-TEST-FAILURE-001"
    assert isinstance(error.__cause__, RuntimeError)


def test_rule_returning_non_text_is_an_explicit_invalid_rule_error() -> None:
    with pytest.raises(NormalizationError) as captured:
        normalize_scenario_section(
            _section("text"),
            profile=_profile(_NonTextRule()),
        )

    assert captured.value.code is NormalizationErrorCode.INVALID_RULE
    assert captured.value.rule_id == "NORM-TEST-NONTEXT-001"


def test_registry_orders_profiles_and_requires_exact_identity() -> None:
    first = _profile(profile_id="z-profile", version="2.0.0")
    second = _profile(profile_id="a-profile", version="1.0.0")
    registry = NormalizationProfileRegistry((first, second))

    assert registry.identities() == (
        ("a-profile", "1.0.0"),
        ("z-profile", "2.0.0"),
    )
    assert registry.profiles() == (second, first)
    assert registry.get("a-profile", "1.0.0") is second
    assert registry.get("a-profile", "2.0.0") is None

    with pytest.raises(NormalizationError) as captured:
        registry.require("a-profile", "2.0.0")
    assert captured.value.code is NormalizationErrorCode.UNKNOWN_PROFILE
    assert captured.value.profile_id == "a-profile"
    assert captured.value.profile_version == "2.0.0"


def test_registry_rejects_duplicate_id_and_version_and_extends_immutably() -> None:
    original = _profile(profile_id="original", version="1.0.0")
    duplicate = _profile(profile_id="original", version="1.0.0")

    with pytest.raises(ValueError, match="duplicate normalization profile"):
        NormalizationProfileRegistry((original, duplicate))

    registry = NormalizationProfileRegistry((original,))
    extension = _profile(profile_id="extension", version="1.0.0")
    extended = registry.with_profiles((extension,))

    assert registry.identities() == (("original", "1.0.0"),)
    assert extended.identities() == (
        ("extension", "1.0.0"),
        ("original", "1.0.0"),
    )


def test_normalize_by_identity_uses_registry_profile() -> None:
    profile = _profile(NormalizeLineEndings(), profile_id="portable")
    registry = NormalizationProfileRegistry((profile,))

    result = normalize_scenario_section_by_identity(
        _section("one\r\ntwo\r"),
        profile_id="portable",
        profile_version="1.2.3",
        registry=registry,
    )

    assert result.normalized_text == "one\ntwo\n"
    assert result.profile_id == "portable"


def test_multiple_sections_preserve_input_order_and_require_unique_ids() -> None:
    profile = _profile(NormalizeLineEndings())
    sections = (
        _section("first\r\n", section_id="first"),
        _section("second\r", section_id="second"),
    )

    results = normalize_scenario_sections(sections, profile=profile)

    assert tuple(result.section_id for result in results) == ("first", "second")
    assert tuple(result.normalized_text for result in results) == (
        "first\n",
        "second\n",
    )

    with pytest.raises(NormalizationError) as captured:
        normalize_scenario_sections(
            (sections[0], _section("again", section_id="first")),
            profile=profile,
        )
    assert captured.value.code is NormalizationErrorCode.INVALID_SECTION
    assert captured.value.section_id == "first"


def test_public_entry_points_reject_wrong_boundary_types() -> None:
    profile = _profile()

    with pytest.raises(TypeError, match="ExtractedScenarioSection"):
        normalize_scenario_section("text", profile=profile)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="NormalizationProfile"):
        normalize_scenario_section(_section("text"), profile=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="sequence of extracted sections"):
        normalize_scenario_sections("text", profile=profile)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"sections\[0\]"):
        normalize_scenario_sections((object(),), profile=profile)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="NormalizationProfileRegistry"):
        normalize_scenario_section_by_identity(
            _section("text"),
            profile_id="test-profile",
            profile_version="1.2.3",
            registry=object(),  # type: ignore[arg-type]
        )



def _construct_normalized_section(
    values: dict[str, object],
) -> NormalizedScenarioSection:
    """Construct from deliberately dynamic test data at one narrow boundary."""
    return cast(Any, NormalizedScenarioSection)(**values)


def test_normalized_section_model_rejects_inconsistent_field_shapes() -> None:
    valid = {
        "section_id": SectionId("parse-output"),
        "normalized_text": "text",
        "source_evidence": "stdout:1-1",
        "profile_id": NormalizationProfileId("test-profile"),
        "profile_version": "1.0.0",
        "source_sha256": "a" * 64,
        "normalized_sha256": "b" * 64,
        "source_size_bytes": 4,
        "normalized_size_bytes": 4,
        "applied_rule_ids": ("NORM-TEST-001",),
        "changed": True,
    }

    assert _construct_normalized_section(valid).applied_rule_ids == ("NORM-TEST-001",)

    bad_digest = dict(valid, source_sha256="A" * 64)
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        _construct_normalized_section(bad_digest)

    duplicate_rules = dict(
        valid,
        applied_rule_ids=("NORM-TEST-001", "NORM-TEST-001"),
    )
    with pytest.raises(ValueError, match="duplicates"):
        _construct_normalized_section(duplicate_rules)

    boolean_size = dict(valid, source_size_bytes=True)
    with pytest.raises(ValueError, match="non-negative integer"):
        _construct_normalized_section(boolean_size)

    non_boolean_changed = dict(valid, changed=1)
    with pytest.raises(TypeError, match="changed must be a bool"):
        _construct_normalized_section(non_boolean_changed)
