from __future__ import annotations

import pytest

from gf_wordbench.reporting.schemas.registry import (
    SCENARIO_GOLD_SCHEMA_ID,
    SCENARIO_GOLD_SCHEMA_KEY,
    SCENARIO_GOLD_SCHEMA_VERSION,
    SchemaContractClass,
    SchemaFormat,
    SchemaSupportClass,
    get_schema_definition,
)
from gf_wordbench.validation.scenarios.gold_compare import (
    ScenarioTextKind,
    ScenarioTextValidationError,
    compare_gold_text,
    parse_scenario_text,
)
from gf_wordbench.validation.scenarios.gold_update import (
    GOLD_SCHEMA_HEADER,
    GoldDocument,
    parse_gold_document,
    parse_normalized_output_document,
)

pytestmark = pytest.mark.schema

_SCENARIO_ID = "parse"
_NORMALIZATION_VERSION = "1.0"
_SECTION_ID = "parse-basic"

_GOLD_TEXT = (
    "# GF_WORDBENCH_GOLD 1.0\n"
    "# scenario_id: parse\n"
    "# normalization_version: 1.0\n"
    "--- BEGIN parse-basic ---\n"
    "hello world\n"
    "--- END parse-basic ---\n"
)

_OUTPUT_TEXT = (
    "# GF_WORDBENCH_OUTPUT 1.0\n"
    "# scenario_id: parse\n"
    "# normalization_version: 1.0\n"
    "--- BEGIN parse-basic ---\n"
    "hello world\n"
    "--- END parse-basic ---\n"
)


def test_gold_schema_registry_entry_is_canonical_and_owned() -> None:
    definition = get_schema_definition(
        SCENARIO_GOLD_SCHEMA_ID,
        SCENARIO_GOLD_SCHEMA_VERSION,
    )

    assert definition.key == SCENARIO_GOLD_SCHEMA_KEY
    assert definition.schema_id == "gf-wordbench.scenario-gold"
    assert str(definition.version) == "1.0"
    assert definition.format is SchemaFormat.CANONICAL_TEXT
    assert definition.contract_class is SchemaContractClass.CANONICAL_TEXT
    assert definition.support is SchemaSupportClass.CANONICAL
    assert definition.canonical_path_pattern == ("project/validation/gold/<scenario-id>.gold")
    assert definition.writer_owner == "validation.scenarios.gold_update"
    assert "validation.scenarios.gold_compare" in definition.readers
    assert "validation.release" in definition.readers
    assert "schema_validator" in definition.readers
    assert definition.encoding == "utf-8"
    assert definition.newline == "lf"
    assert definition.migration_policy == "explicit_review"


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        ("project/validation/gold/parse.gold", True),
        ("project/validation/gold/smoke-test.gold", True),
        ("project/validation/gold/parse.txt", False),
        ("project/validation/parse.gold", False),
        ("validation/gold/parse.gold", False),
    ),
)
def test_gold_schema_path_pattern_matches_only_canonical_locations(
    path: str,
    expected: bool,
) -> None:
    definition = get_schema_definition(SCENARIO_GOLD_SCHEMA_ID)

    assert definition.matches_path(path) is expected


def test_canonical_gold_document_round_trips_without_loss() -> None:
    document = parse_gold_document(
        _GOLD_TEXT,
        expected_scenario_id=_SCENARIO_ID,
        expected_normalization_version=_NORMALIZATION_VERSION,
    )

    assert isinstance(document, GoldDocument)
    assert document.scenario_id == _SCENARIO_ID
    assert document.normalization_version == _NORMALIZATION_VERSION
    assert document.sections == (_SECTION_ID,)
    assert document.text == _GOLD_TEXT

    strict = parse_scenario_text(
        document.text,
        kind=ScenarioTextKind.GOLD,
    )
    assert strict.scenario_id == _SCENARIO_ID
    assert strict.normalization_version == _NORMALIZATION_VERSION
    assert tuple(str(section_id) for section_id in strict.section_ids) == (_SECTION_ID,)
    assert strict.sections[0].content == "hello world\n"
    assert strict.canonical_text == _GOLD_TEXT
    assert len(strict.sha256) == 64


def test_normalized_output_converts_to_the_canonical_gold_schema() -> None:
    candidate = parse_normalized_output_document(
        _OUTPUT_TEXT,
        expected_scenario_id=_SCENARIO_ID,
        expected_normalization_version=_NORMALIZATION_VERSION,
    )

    assert candidate.text == _GOLD_TEXT
    assert candidate.sections == (_SECTION_ID,)
    assert candidate.text.startswith(f"{GOLD_SCHEMA_HEADER}\n")
    assert candidate.text.endswith("\n")


def test_output_and_gold_compare_by_canonical_projection() -> None:
    matched, diff, expected, actual = compare_gold_text(
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_text=_OUTPUT_TEXT,
        gold_text=_GOLD_TEXT,
    )

    assert matched
    assert diff == ""
    assert expected.kind is ScenarioTextKind.GOLD
    assert actual.kind is ScenarioTextKind.OUTPUT
    assert expected.comparison_projection() == actual.comparison_projection()


@pytest.mark.parametrize(
    ("gold_text", "message"),
    (
        (
            _GOLD_TEXT.replace(
                "# GF_WORDBENCH_GOLD 1.0",
                "# GF_WORDBENCH_GOLD 2.0",
            ),
            "unsupported gold header",
        ),
        (
            _GOLD_TEXT.replace(
                "--- END parse-basic ---",
                "--- END another-section ---",
            ),
            "closes as",
        ),
        (
            _GOLD_TEXT + "--- BEGIN parse-basic ---\nagain\n--- END parse-basic ---\n",
            "duplicate section ID",
        ),
        (
            _GOLD_TEXT.removesuffix("\n"),
            "must end with a newline",
        ),
        (
            "\ufeff" + _GOLD_TEXT,
            "without BOM",
        ),
    ),
)
def test_malformed_gold_documents_fail_closed(
    gold_text: str,
    message: str,
) -> None:
    with pytest.raises(ScenarioTextValidationError, match=message) as captured:
        parse_scenario_text(gold_text, kind=ScenarioTextKind.GOLD)

    assert captured.value.kind is ScenarioTextKind.GOLD


def test_gold_identity_must_match_the_selected_scenario() -> None:
    with pytest.raises(ValueError, match="does not match the expected scenario"):
        parse_gold_document(
            _GOLD_TEXT,
            expected_scenario_id="linearize",
            expected_normalization_version=_NORMALIZATION_VERSION,
        )

    with pytest.raises(
        ValueError,
        match="does not match the expected version",
    ):
        parse_gold_document(
            _GOLD_TEXT,
            expected_scenario_id=_SCENARIO_ID,
            expected_normalization_version="2.0",
        )


def test_empty_gold_requires_explicit_policy() -> None:
    empty_gold = (
        "# GF_WORDBENCH_GOLD 1.0\n"
        "# scenario_id: parse\n"
        "# normalization_version: 1.0\n"
        "--- BEGIN parse-basic ---\n"
        "--- END parse-basic ---\n"
        "--- BEGIN parse-secondary ---\n"
        "--- END parse-secondary ---\n"
    )
    empty_output = empty_gold.replace(
        "# GF_WORDBENCH_GOLD 1.0",
        "# GF_WORDBENCH_OUTPUT 1.0",
    )

    with pytest.raises(
        ScenarioTextValidationError,
        match="empty gold requires explicit",
    ):
        compare_gold_text(
            scenario_id=_SCENARIO_ID,
            normalization_version=_NORMALIZATION_VERSION,
            normalized_output_text=empty_output,
            gold_text=empty_gold,
        )

    matched, diff, expected, actual = compare_gold_text(
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_text=empty_output,
        gold_text=empty_gold,
        allow_empty_gold=True,
    )

    assert matched
    assert diff == ""
    assert expected.is_content_empty
    assert actual.is_content_empty


def test_gold_document_preserves_unicode_linguistic_content() -> None:
    gold_text = _GOLD_TEXT.replace(
        "hello world",
        "élève — κόσμος — 日本語",
    )

    document = parse_scenario_text(
        gold_text,
        kind=ScenarioTextKind.GOLD,
    )

    assert document.sections[0].content == "élève — κόσμος — 日本語\n"
    assert document.canonical_text.encode("utf-8").decode("utf-8") == gold_text
