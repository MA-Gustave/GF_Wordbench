"""Unit tests for exact, read-only scenario gold comparison."""

from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.kernel.statuses import ErrorKind
from gf_wordbench.validation.scenarios.gold_compare import (
    GoldComparisonPolicy,
    GoldComparisonState,
    ScenarioTextKind,
    ScenarioTextValidationError,
    build_unified_gold_diff,
    compare_gold,
    compare_gold_text,
    parse_scenario_text,
)

_SCENARIO_ID = "parse"
_NORMALIZATION_VERSION = "1.0"


def _scenario_text(
    *,
    kind: ScenarioTextKind,
    sections: tuple[tuple[str, str], ...] = (("parse-basic", "hello world\n"),),
    scenario_id: str = _SCENARIO_ID,
    normalization_version: str = _NORMALIZATION_VERSION,
    newline: str = "\n",
) -> str:
    header = (
        "# GF_WORDBENCH_OUTPUT 1.0"
        if kind is ScenarioTextKind.OUTPUT
        else "# GF_WORDBENCH_GOLD 1.0"
    )
    lines = [
        header,
        f"# scenario_id: {scenario_id}",
        f"# normalization_version: {normalization_version}",
    ]
    for section_id, content in sections:
        lines.append(f"--- BEGIN {section_id} ---")
        lines.extend(content.removesuffix("\n").split("\n") if content else [])
        lines.append(f"--- END {section_id} ---")
    return newline.join(lines) + newline


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_none_policy_is_not_applicable_and_requires_no_files() -> None:
    result = compare_gold(
        policy=GoldComparisonPolicy.NONE,
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=None,
        gold_path=None,
    )

    assert result.policy is GoldComparisonPolicy.NONE
    assert result.state is GoldComparisonState.NOT_APPLICABLE
    assert result.gold_match is None
    assert result.error_kind is ErrorKind.OK
    assert result.gold_diff_path is None
    assert result.applied is False
    assert result.succeeded is True


def test_exact_match_returns_hashes_and_never_writes_a_diff(tmp_path: Path) -> None:
    output = _write(
        tmp_path / "raw/scenarios/parse.out",
        _scenario_text(kind=ScenarioTextKind.OUTPUT),
    )
    gold = _write(
        tmp_path / "project/validation/gold/parse.gold",
        _scenario_text(kind=ScenarioTextKind.GOLD),
    )
    diff = tmp_path / "raw/scenarios/parse.gold.diff"
    original_gold = gold.read_bytes()

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=diff,
        diff_root=tmp_path,
    )

    assert result.policy is GoldComparisonPolicy.EXACT
    assert result.state is GoldComparisonState.MATCH
    assert result.gold_match is True
    assert result.error_kind is ErrorKind.OK
    assert result.gold_diff_path is None
    assert result.section_ids == ("parse-basic",)
    assert result.expected_sha256 is not None
    assert result.actual_sha256 is not None
    assert result.expected_sha256 != result.actual_sha256
    assert len(result.expected_sha256) == 64
    assert len(result.actual_sha256) == 64
    assert result.applied is True
    assert result.succeeded is True
    assert not diff.exists()
    assert gold.read_bytes() == original_gold


def test_exact_comparison_accepts_crlf_as_permitted_newline_handling() -> None:
    output = _scenario_text(kind=ScenarioTextKind.OUTPUT, newline="\n")
    gold = _scenario_text(kind=ScenarioTextKind.GOLD, newline="\r\n")

    matched, diff, expected, actual = compare_gold_text(
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_text=output,
        gold_text=gold,
    )

    assert matched is True
    assert diff == ""
    assert expected.canonical_text.endswith("\n")
    assert "\r" not in expected.canonical_text
    assert expected.comparison_projection() == actual.comparison_projection()
    assert expected.sha256 == parse_scenario_text(
        _scenario_text(kind=ScenarioTextKind.GOLD),
        kind=ScenarioTextKind.GOLD,
    ).sha256
    assert expected.sha256 != actual.sha256


def test_mismatch_writes_a_bounded_unified_diff_and_preserves_gold(tmp_path: Path) -> None:
    output = _write(
        tmp_path / "raw/scenarios/parse.out",
        _scenario_text(
            kind=ScenarioTextKind.OUTPUT,
            sections=(("parse-basic", "actual value\n"),),
        ),
    )
    gold = _write(
        tmp_path / "project/validation/gold/parse.gold",
        _scenario_text(
            kind=ScenarioTextKind.GOLD,
            sections=(("parse-basic", "expected value\n"),),
        ),
    )
    diff = tmp_path / "raw/scenarios/parse.gold.diff"
    original_gold = gold.read_bytes()

    result = compare_gold(
        policy=GoldComparisonPolicy.EXACT,
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=diff,
        gold_label="project/validation/gold/parse.gold",
        actual_label="raw/scenarios/parse.out",
        diff_root=tmp_path,
    )

    assert result.state is GoldComparisonState.MISMATCH
    assert result.gold_match is False
    assert result.error_kind is ErrorKind.OTHER
    assert result.message == "Normalized output differs from gold."
    assert result.gold_diff_path == diff.resolve()
    assert result.succeeded is False
    assert gold.read_bytes() == original_gold

    diff_text = diff.read_text(encoding="utf-8")
    assert diff_text.startswith(
        "--- project/validation/gold/parse.gold\n"
        "+++ raw/scenarios/parse.out\n"
    )
    assert "-expected value\n" in diff_text
    assert "+actual value\n" in diff_text
    assert str(tmp_path) not in diff_text
    assert "\r" not in diff_text
    assert diff_text.endswith("\n")


def test_section_order_is_semantic_for_exact_comparison() -> None:
    gold = _scenario_text(
        kind=ScenarioTextKind.GOLD,
        sections=(("first", "one\n"), ("second", "two\n")),
    )
    output = _scenario_text(
        kind=ScenarioTextKind.OUTPUT,
        sections=(("second", "two\n"), ("first", "one\n")),
    )

    matched, diff, expected, actual = compare_gold_text(
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_text=output,
        gold_text=gold,
    )

    assert matched is False
    assert diff
    assert expected.section_ids == ("first", "second")
    assert actual.section_ids == ("second", "first")


@pytest.mark.parametrize(
    ("missing_role", "expected_kind", "message"),
    (
        ("output", ErrorKind.IO, "Normalized scenario output is missing."),
        ("gold", ErrorKind.CONFIG, "Required gold file is missing."),
    ),
)
def test_missing_exact_comparison_inputs_fail_closed(
    tmp_path: Path,
    missing_role: str,
    expected_kind: ErrorKind,
    message: str,
) -> None:
    output = tmp_path / "raw/scenarios/parse.out"
    gold = tmp_path / "project/validation/gold/parse.gold"
    if missing_role != "output":
        _write(output, _scenario_text(kind=ScenarioTextKind.OUTPUT))
    if missing_role != "gold":
        _write(gold, _scenario_text(kind=ScenarioTextKind.GOLD))

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "raw/scenarios/parse.gold.diff",
    )

    assert result.state is GoldComparisonState.ERROR
    assert result.gold_match is None
    assert result.error_kind is expected_kind
    assert result.message == message
    assert result.gold_diff_path is None


def test_unreadable_utf8_input_is_an_io_error(tmp_path: Path) -> None:
    output = tmp_path / "raw/scenarios/parse.out"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"\xff\xfe\x00")
    gold = _write(
        tmp_path / "project/validation/gold/parse.gold",
        _scenario_text(kind=ScenarioTextKind.GOLD),
    )

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "raw/scenarios/parse.gold.diff",
    )

    assert result.state is GoldComparisonState.ERROR
    assert result.error_kind is ErrorKind.IO
    assert result.gold_match is None
    assert result.message.startswith("Gold comparison input is unreadable:")


@pytest.mark.parametrize(
    ("kind", "expected_error_kind"),
    (
        (ScenarioTextKind.GOLD, ErrorKind.CONFIG),
        (ScenarioTextKind.OUTPUT, ErrorKind.INTERNAL),
    ),
)
def test_malformed_documents_map_to_their_owning_error_category(
    tmp_path: Path,
    kind: ScenarioTextKind,
    expected_error_kind: ErrorKind,
) -> None:
    output_text = _scenario_text(kind=ScenarioTextKind.OUTPUT)
    gold_text = _scenario_text(kind=ScenarioTextKind.GOLD)
    if kind is ScenarioTextKind.GOLD:
        gold_text = gold_text.replace("# GF_WORDBENCH_GOLD 1.0", "bad header")
    else:
        output_text = output_text.replace("# GF_WORDBENCH_OUTPUT 1.0", "bad header")

    output = _write(tmp_path / "parse.out", output_text)
    gold = _write(tmp_path / "parse.gold", gold_text)

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "parse.gold.diff",
    )

    assert result.state is GoldComparisonState.ERROR
    assert result.error_kind is expected_error_kind
    assert result.gold_match is None
    assert "unsupported" in result.message


@pytest.mark.parametrize(
    ("kind", "expected_error_kind"),
    (
        (ScenarioTextKind.GOLD, ErrorKind.CONFIG),
        (ScenarioTextKind.OUTPUT, ErrorKind.INTERNAL),
    ),
)
def test_identity_mismatch_is_not_reported_as_a_content_mismatch(
    tmp_path: Path,
    kind: ScenarioTextKind,
    expected_error_kind: ErrorKind,
) -> None:
    output_text = _scenario_text(kind=ScenarioTextKind.OUTPUT)
    gold_text = _scenario_text(kind=ScenarioTextKind.GOLD)
    if kind is ScenarioTextKind.GOLD:
        gold_text = _scenario_text(kind=kind, scenario_id="different")
    else:
        output_text = _scenario_text(kind=kind, normalization_version="2.0")

    output = _write(tmp_path / "parse.out", output_text)
    gold = _write(tmp_path / "parse.gold", gold_text)

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "parse.gold.diff",
    )

    assert result.state is GoldComparisonState.ERROR
    assert result.error_kind is expected_error_kind
    assert result.gold_match is None
    assert "does not match" in result.message
    assert not (tmp_path / "parse.gold.diff").exists()


def test_empty_gold_requires_explicit_intent(tmp_path: Path) -> None:
    empty_sections = (("parse-basic", ""), ("parse-secondary", ""))
    output = _write(
        tmp_path / "parse.out",
        _scenario_text(kind=ScenarioTextKind.OUTPUT, sections=empty_sections),
    )
    gold = _write(
        tmp_path / "parse.gold",
        _scenario_text(kind=ScenarioTextKind.GOLD, sections=empty_sections),
    )

    rejected = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "parse.gold.diff",
    )
    accepted = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=tmp_path / "parse.gold.diff",
        allow_empty_gold=True,
    )

    assert rejected.state is GoldComparisonState.ERROR
    assert rejected.error_kind is ErrorKind.CONFIG
    assert "empty gold requires explicit" in rejected.message
    assert accepted.state is GoldComparisonState.MATCH
    assert accepted.gold_match is True


def test_diff_write_is_contained_by_the_configured_root(tmp_path: Path) -> None:
    output = _write(
        tmp_path / "parse.out",
        _scenario_text(
            kind=ScenarioTextKind.OUTPUT,
            sections=(("parse-basic", "actual\n"),),
        ),
    )
    gold = _write(
        tmp_path / "parse.gold",
        _scenario_text(
            kind=ScenarioTextKind.GOLD,
            sections=(("parse-basic", "expected\n"),),
        ),
    )
    allowed_root = tmp_path / "allowed"
    outside_diff = tmp_path / "outside/parse.gold.diff"

    result = compare_gold(
        policy="exact",
        scenario_id=_SCENARIO_ID,
        normalization_version=_NORMALIZATION_VERSION,
        normalized_output_path=output,
        gold_path=gold,
        gold_diff_path=outside_diff,
        diff_root=allowed_root,
    )

    assert result.state is GoldComparisonState.ERROR
    assert result.gold_match is False
    assert result.error_kind is ErrorKind.IO
    assert "diff writing failed" in result.message
    assert result.gold_diff_path is None
    assert not outside_diff.exists()


def test_build_unified_diff_is_deterministic_and_terminates_with_lf() -> None:
    first = build_unified_gold_diff(
        expected_projection="expected\n",
        actual_projection="actual\n",
        expected_label="project/validation/gold/parse.gold",
        actual_label="raw/scenarios/parse.out",
    )
    second = build_unified_gold_diff(
        expected_projection="expected\n",
        actual_projection="actual\n",
        expected_label="project\\validation\\gold\\parse.gold",
        actual_label="raw\\scenarios\\parse.out",
    )

    assert first == second
    assert first.startswith(
        "--- project/validation/gold/parse.gold\n"
        "+++ raw/scenarios/parse.out\n"
    )
    assert first.endswith("\n")
    assert "\r" not in first


def test_parser_rejects_bom_and_missing_terminating_newline() -> None:
    gold = _scenario_text(kind=ScenarioTextKind.GOLD)

    with pytest.raises(ScenarioTextValidationError, match="without BOM") as bom:
        parse_scenario_text("\ufeff" + gold, kind=ScenarioTextKind.GOLD)
    with pytest.raises(ScenarioTextValidationError, match="end with a newline") as newline:
        parse_scenario_text(gold.removesuffix("\n"), kind=ScenarioTextKind.GOLD)

    assert bom.value.kind is ScenarioTextKind.GOLD
    assert newline.value.kind is ScenarioTextKind.GOLD


@pytest.mark.parametrize(
    ("kwargs", "error_type", "message"),
    (
        ({"policy": "unordered"}, ValueError, "unsupported gold comparison policy"),
        ({"policy": 1}, TypeError, "policy must be"),
        ({"normalization_version": "1"}, ValueError, "major.minor"),
        ({"normalized_output_path": None}, ValueError, "normalized_output_path is required"),
        ({"gold_path": None}, ValueError, "gold_path is required"),
    ),
)
def test_public_entrypoint_rejects_noncanonical_configuration(
    tmp_path: Path,
    kwargs: dict[str, object],
    error_type: type[Exception],
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "policy": "exact",
        "scenario_id": _SCENARIO_ID,
        "normalization_version": _NORMALIZATION_VERSION,
        "normalized_output_path": tmp_path / "parse.out",
        "gold_path": tmp_path / "parse.gold",
        "gold_diff_path": tmp_path / "parse.gold.diff",
    }
    arguments.update(kwargs)

    with pytest.raises(error_type, match=message):
        compare_gold(**arguments)  # type: ignore[arg-type]
