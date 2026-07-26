"""Schema tests for canonical normalized scenario-output documents."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from gf_wordbench.reporting.schemas.registry import (
    SCENARIO_OUTPUT_SCHEMA_ID,
    SCENARIO_OUTPUT_SCHEMA_VERSION,
    SchemaContractClass,
    SchemaFormat,
    get_schema_definition,
)
from gf_wordbench.validation.scenarios.gold_update import (
    GOLD_SCHEMA_HEADER,
    NORMALIZATION_HEADER_PREFIX,
    OUTPUT_SCHEMA_HEADER,
    SCENARIO_HEADER_PREFIX,
    GoldDocument,
    parse_normalized_output_document,
)

_SCENARIO_ID = "parse-basic"
_NORMALIZATION_VERSION = "1.0.0"
_SECTION_ONE = "load-grammar"
_SECTION_TWO = "parse-unicode"


def _output_document(
    *,
    scenario_id: str = _SCENARIO_ID,
    normalization_version: str = _NORMALIZATION_VERSION,
    sections: tuple[tuple[str, tuple[str, ...]], ...] = (
        (_SECTION_ONE, ("Loaded SmokeEng",)),
        (_SECTION_TWO, ("héllo 世界", "Parse: Greeting")),
    ),
    newline: str = "\n",
    terminate: bool = True,
    bom: bool = False,
) -> str:
    lines = [
        OUTPUT_SCHEMA_HEADER,
        f"{SCENARIO_HEADER_PREFIX}{scenario_id}",
        f"{NORMALIZATION_HEADER_PREFIX}{normalization_version}",
    ]
    for section_id, body in sections:
        lines.append(f"--- BEGIN {section_id} ---")
        lines.extend(body)
        lines.append(f"--- END {section_id} ---")
    text = newline.join(lines)
    if terminate:
        text += newline
    if bom:
        text = "\ufeff" + text
    return text


def _parse(text: str) -> GoldDocument:
    return parse_normalized_output_document(
        text,
        expected_scenario_id=_SCENARIO_ID,
        expected_normalization_version=_NORMALIZATION_VERSION,
    )


def test_registry_declares_scenario_output_as_canonical_text() -> None:
    definition = get_schema_definition(
        SCENARIO_OUTPUT_SCHEMA_ID,
        SCENARIO_OUTPUT_SCHEMA_VERSION,
    )

    assert definition.schema_id == "gf-wordbench.scenario-output"
    assert str(definition.version) == "1.0"
    assert definition.format is SchemaFormat.CANONICAL_TEXT
    assert definition.contract_class is SchemaContractClass.CANONICAL_TEXT
    assert definition.canonical_path_pattern == (
        "run_<run-id>/raw/scenarios/<scenario-id>.out"
    )
    assert definition.encoding == "utf-8"
    assert definition.newline == "lf"
    assert definition.writer_owner == "validation.scenarios.normalization"
    assert definition.matches_path(
        "run_20260725_153043/raw/scenarios/parse-basic.out"
    )
    assert not definition.matches_path(
        "project/validation/gold/parse-basic.gold"
    )


def test_canonical_document_round_trip_preserves_unicode_and_section_order() -> None:
    parsed = _parse(_output_document())

    assert str(parsed.scenario_id) == _SCENARIO_ID
    assert parsed.normalization_version == _NORMALIZATION_VERSION
    assert parsed.sections == (_SECTION_ONE, _SECTION_TWO)
    assert parsed.text == (
        f"{GOLD_SCHEMA_HEADER}\n"
        f"{SCENARIO_HEADER_PREFIX}{_SCENARIO_ID}\n"
        f"{NORMALIZATION_HEADER_PREFIX}{_NORMALIZATION_VERSION}\n"
        f"--- BEGIN {_SECTION_ONE} ---\n"
        "Loaded SmokeEng\n"
        f"--- END {_SECTION_ONE} ---\n"
        f"--- BEGIN {_SECTION_TWO} ---\n"
        "héllo 世界\n"
        "Parse: Greeting\n"
        f"--- END {_SECTION_TWO} ---\n"
    )


def test_crlf_bom_and_missing_final_newline_are_canonicalized() -> None:
    source = _output_document(
        newline="\r\n",
        terminate=False,
        bom=True,
    )

    parsed = _parse(source)

    assert not parsed.text.startswith("\ufeff")
    assert "\r" not in parsed.text
    assert parsed.text.endswith("\n")
    assert "héllo 世界" in parsed.text


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda text: text.replace(
                OUTPUT_SCHEMA_HEADER,
                "# GF_WORDBENCH_OUTPUT 2.0",
                1,
            ),
            "must begin",
        ),
        (
            lambda text: text.replace(
                f"{SCENARIO_HEADER_PREFIX}{_SCENARIO_ID}",
                f"{SCENARIO_HEADER_PREFIX}other-scenario",
                1,
            ),
            "scenario ID does not match",
        ),
        (
            lambda text: text.replace(
                f"{NORMALIZATION_HEADER_PREFIX}{_NORMALIZATION_VERSION}",
                f"{NORMALIZATION_HEADER_PREFIX}2.0.0",
                1,
            ),
            "normalization version does not match",
        ),
        (
            lambda text: text.replace(
                f"{NORMALIZATION_HEADER_PREFIX}{_NORMALIZATION_VERSION}",
                f"{NORMALIZATION_HEADER_PREFIX}current",
                1,
            ),
            "dotted numeric version",
        ),
        (
            lambda text: text.replace(
                f"--- END {_SECTION_TWO} ---\n",
                "",
                1,
            ),
            "no matching END marker",
        ),
        (
            lambda text: text.replace(
                f"--- END {_SECTION_ONE} ---",
                "--- END wrong-section ---",
                1,
            ),
            "does not match BEGIN",
        ),
        (
            lambda text: text.replace(
                f"--- BEGIN {_SECTION_TWO} ---",
                f"--- BEGIN {_SECTION_ONE} ---",
                1,
            ).replace(
                f"--- END {_SECTION_TWO} ---",
                f"--- END {_SECTION_ONE} ---",
                1,
            ),
            "duplicate section ID",
        ),
        (
            lambda text: text.replace(
                "Loaded SmokeEng",
                "--- BEGIN nested-section ---\nLoaded SmokeEng",
                1,
            ),
            "nested scenario sections",
        ),
        (
            lambda text: text.replace(
                f"--- BEGIN {_SECTION_ONE} ---",
                "ordinary output outside a section",
                1,
            ),
            "only canonical BEGIN/END sections",
        ),
    ],
)
def test_invalid_output_contracts_are_rejected(
    mutate: Callable[[str], str],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _parse(mutate(_output_document()))


@pytest.mark.parametrize(
    "text",
    [
        "",
        OUTPUT_SCHEMA_HEADER + "\n",
        (
            f"{OUTPUT_SCHEMA_HEADER}\n"
            f"{SCENARIO_HEADER_PREFIX}{_SCENARIO_ID}\n"
            f"{NORMALIZATION_HEADER_PREFIX}{_NORMALIZATION_VERSION}\n"
        ),
    ],
)
def test_missing_header_or_sections_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        _parse(text)


def test_nul_characters_are_rejected() -> None:
    with pytest.raises(ValueError, match="NUL"):
        _parse(_output_document().replace("héllo", "héllo\x00"))


def test_non_text_input_is_rejected() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        parse_normalized_output_document(
            b"not text",  # type: ignore[arg-type]
            expected_scenario_id=_SCENARIO_ID,
            expected_normalization_version=_NORMALIZATION_VERSION,
        )
