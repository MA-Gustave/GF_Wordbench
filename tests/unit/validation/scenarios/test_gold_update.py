"""Tests for explicit, reviewed, and atomic scenario-gold updates."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.validation.scenarios.gold_update import (
    GOLD_SCHEMA_HEADER,
    NORMALIZATION_HEADER_PREFIX,
    OUTPUT_SCHEMA_HEADER,
    SCENARIO_HEADER_PREFIX,
    GoldUpdateConcurrentChangeError,
    GoldUpdateError,
    GoldUpdateIntegrityError,
    GoldUpdateRefusalCode,
    GoldUpdateRequest,
    GoldUpdateStatus,
    apply_gold_update,
    build_gold_diff,
    parse_gold_document,
    parse_normalized_output_document,
    prepare_gold_update,
    update_gold,
)

SCENARIO_ID = "parse-basic"
RUN_ID = "20260725_190423"
NORMALIZATION_VERSION = "1.0"
SECTION_ID = "linearizations"
FIXED_TIME = datetime(2026, 7, 25, 19, 4, 23, tzinfo=UTC)


def _normalized_output(
    body: str = "chat → bisedë\nélève → nxënës",
    *,
    scenario_id: str = SCENARIO_ID,
    normalization_version: str = NORMALIZATION_VERSION,
    line_ending: str = "\n",
) -> str:
    lines = (
        OUTPUT_SCHEMA_HEADER,
        f"{SCENARIO_HEADER_PREFIX}{scenario_id}",
        f"{NORMALIZATION_HEADER_PREFIX}{normalization_version}",
        f"--- BEGIN {SECTION_ID} ---",
        *body.split("\n"),
        f"--- END {SECTION_ID} ---",
        "",
    )
    return line_ending.join(lines)


def _gold_text(body: str = "chat → bisedë\nélève → nxënës") -> str:
    return _normalized_output(body).replace(
        OUTPUT_SCHEMA_HEADER,
        GOLD_SCHEMA_HEADER,
        1,
    )


def _request(
    tmp_path: Path,
    **overrides: Any,
) -> GoldUpdateRequest:
    values: dict[str, Any] = {
        "project_root": tmp_path,
        "scenario_id": SCENARIO_ID,
        "source_run_id": RUN_ID,
        "normalized_output_text": _normalized_output(),
        "normalization_version": NORMALIZATION_VERSION,
        "reviewer": "maintainer@example.test",
        "rationale": "Reviewed intentional linguistic correction.",
        "decision_reference": "ADR-0007 review 2026-07-25",
        "raw_stdout_path": tmp_path / "run" / "raw" / "scenario.stdout.txt",
        "raw_stderr_path": tmp_path / "run" / "raw" / "scenario.stderr.txt",
        "normalized_output_path": tmp_path / "run" / "raw" / "scenario.out",
        "diff_evidence_path": tmp_path / "run" / "raw" / "scenario.gold.diff",
        "confirmed": True,
        "diff_reviewed": True,
        "metadata": {
            "gf_version": "3.12",
            "normalization_profile": "scenario-default",
        },
    }
    values.update(overrides)
    return GoldUpdateRequest(**values)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_candidate(
    captured: dict[str, Any],
) -> Callable[..., Path]:
    def writer(
        destination: Path,
        text: str,
        **options: Any,
    ) -> Path:
        captured["destination"] = destination
        captured["text"] = text
        captured["options"] = options
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            text,
            encoding=options["encoding"],
            newline=options["newline"],
        )
        return destination

    return writer


def test_parse_normalized_output_builds_canonical_gold_without_linguistic_changes() -> None:
    source = "\ufeff" + _normalized_output(line_ending="\r\n")

    document = parse_normalized_output_document(
        source,
        expected_scenario_id=SCENARIO_ID,
        expected_normalization_version=NORMALIZATION_VERSION,
    )

    assert document.scenario_id == SCENARIO_ID
    assert document.normalization_version == NORMALIZATION_VERSION
    assert document.sections == (SECTION_ID,)
    assert document.text == _gold_text()
    assert "chat → bisedë" in document.text
    assert "élève → nxënës" in document.text
    assert "\r" not in document.text
    assert document.text.endswith("\n")


def test_parse_gold_document_requires_exact_identity_and_version() -> None:
    document = parse_gold_document(
        _gold_text(),
        expected_scenario_id=SCENARIO_ID,
        expected_normalization_version=NORMALIZATION_VERSION,
    )

    assert document.sections == (SECTION_ID,)

    with pytest.raises(ValueError, match="scenario ID does not match"):
        parse_gold_document(
            _gold_text(),
            expected_scenario_id="another-scenario",
        )

    with pytest.raises(ValueError, match="normalization version does not match"):
        parse_gold_document(
            _gold_text(),
            expected_normalization_version="2.0",
        )


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            _normalized_output().replace(
                OUTPUT_SCHEMA_HEADER,
                "# GF_WORDBENCH_OUTPUT 9.9",
                1,
            ),
            "must begin",
        ),
        (
            _normalized_output(scenario_id="another-scenario"),
            "scenario ID does not match",
        ),
        (
            _normalized_output(normalization_version="2.0"),
            "normalization version does not match",
        ),
        (
            _normalized_output().replace(
                f"--- END {SECTION_ID} ---",
                "--- END wrong-section ---",
            ),
            "does not match BEGIN",
        ),
        (
            _normalized_output().replace(
                f"--- END {SECTION_ID} ---",
                "",
            ),
            "no matching END",
        ),
    ],
)
def test_normalized_output_schema_rejects_unreviewable_documents(
    text: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_normalized_output_document(
            text,
            expected_scenario_id=SCENARIO_ID,
            expected_normalization_version=NORMALIZATION_VERSION,
        )


def test_prepare_missing_gold_is_read_only_and_produces_visible_diff(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    plan = prepare_gold_update(request)

    assert plan.status is GoldUpdateStatus.READY
    assert plan.changed is True
    assert plan.writable is True
    assert plan.previous_exists is False
    assert plan.previous_sha256 is None
    assert plan.candidate is not None
    assert plan.candidate.text == _gold_text()
    assert plan.candidate_sha256 == _sha256(_gold_text().encode())
    assert plan.gold_path == (tmp_path / "validation" / "gold" / f"{SCENARIO_ID}.gold")
    assert not plan.gold_path.exists()
    assert "# scenario_id: parse-basic" in plan.diff_text
    assert "--- /dev/null" in plan.diff_text
    assert "+++ " in plan.diff_text
    assert "+chat → bisedë" in plan.diff_text


def test_prepare_existing_identical_gold_is_unchanged(tmp_path: Path) -> None:
    request = _request(tmp_path)
    request.gold_path.parent.mkdir(parents=True)
    request.gold_path.write_text(_gold_text(), encoding="utf-8", newline="")

    plan = prepare_gold_update(request)

    assert plan.status is GoldUpdateStatus.UNCHANGED
    assert plan.changed is False
    assert plan.previous_exists is True
    assert plan.previous_sha256 == _sha256(_gold_text().encode())
    assert plan.candidate_sha256 == plan.previous_sha256


@pytest.mark.parametrize(
    ("override", "code"),
    [
        ({"markers_valid": False}, GoldUpdateRefusalCode.MARKERS_INVALID),
        (
            {"normalization_succeeded": False},
            GoldUpdateRefusalCode.NORMALIZATION_FAILED,
        ),
        ({"output_truncated": True}, GoldUpdateRefusalCode.OUTPUT_TRUNCATED),
        ({"output_complete": False}, GoldUpdateRefusalCode.OUTPUT_INCOMPLETE),
        (
            {"compatibility_verified": False},
            GoldUpdateRefusalCode.COMPATIBILITY_UNKNOWN,
        ),
        ({"deterministic": False}, GoldUpdateRefusalCode.NONDETERMINISTIC),
        ({"diff_reviewed": False}, GoldUpdateRefusalCode.DIFF_NOT_REVIEWED),
    ],
)
def test_prepare_refuses_each_documented_safety_failure(
    tmp_path: Path,
    override: dict[str, bool],
    code: GoldUpdateRefusalCode,
) -> None:
    plan = prepare_gold_update(_request(tmp_path, **override))

    assert plan.status is GoldUpdateStatus.REFUSED
    assert code in {refusal.code for refusal in plan.refusals}
    assert not plan.gold_path.exists()


def test_prepare_refuses_empty_output_unless_explicitly_allowed(
    tmp_path: Path,
) -> None:
    empty_output = _normalized_output(body="")

    refused = prepare_gold_update(_request(tmp_path, normalized_output_text=empty_output))
    allowed = prepare_gold_update(
        _request(
            tmp_path,
            normalized_output_text=empty_output,
            allow_empty=True,
        )
    )

    assert refused.status is GoldUpdateStatus.REFUSED
    assert GoldUpdateRefusalCode.OUTPUT_NOT_MEANINGFUL in {
        refusal.code for refusal in refused.refusals
    }
    assert allowed.status is GoldUpdateStatus.READY


def test_prepare_refuses_invalid_schema_and_preserves_all_other_refusals(
    tmp_path: Path,
) -> None:
    plan = prepare_gold_update(
        _request(
            tmp_path,
            normalized_output_text="not a normalized document",
            markers_valid=False,
            normalization_succeeded=False,
        )
    )

    codes = {refusal.code for refusal in plan.refusals}
    assert plan.status is GoldUpdateStatus.REFUSED
    assert plan.candidate is None
    assert GoldUpdateRefusalCode.INVALID_OUTPUT_SCHEMA in codes
    assert GoldUpdateRefusalCode.MARKERS_INVALID in codes
    assert GoldUpdateRefusalCode.NORMALIZATION_FAILED in codes
    assert GoldUpdateRefusalCode.OUTPUT_NOT_MEANINGFUL in codes


def test_prepare_refuses_when_reviewed_previous_hash_is_stale(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        expected_previous_sha256="0" * 64,
    )
    request.gold_path.parent.mkdir(parents=True)
    request.gold_path.write_text(
        _gold_text("old reviewed output"),
        encoding="utf-8",
    )

    plan = prepare_gold_update(request)

    assert plan.status is GoldUpdateStatus.REFUSED
    assert GoldUpdateRefusalCode.PREVIOUS_HASH_MISMATCH in {
        refusal.code for refusal in plan.refusals
    }


def test_apply_without_explicit_confirmation_declines_without_writing(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, confirmed=False)
    plan = prepare_gold_update(request)
    writes: list[Path] = []

    def forbidden_writer(destination: Path, text: str, **options: Any) -> Path:
        writes.append(destination)
        return destination

    result = apply_gold_update(plan, write_text=forbidden_writer)

    assert plan.status is GoldUpdateStatus.READY
    assert result.status is GoldUpdateStatus.DECLINED
    assert result.record is None
    assert writes == []
    assert not request.gold_path.exists()


def test_successful_update_writes_exact_gold_and_attributable_record(
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}
    request = _request(tmp_path)

    result = update_gold(
        request,
        write_text=_write_candidate(captured),
        clock=lambda: FIXED_TIME,
    )

    assert result.status is GoldUpdateStatus.UPDATED
    assert result.record is not None
    assert request.gold_path.read_bytes() == _gold_text().encode("utf-8")
    assert captured["destination"] == request.gold_path
    assert captured["text"] == _gold_text()
    assert captured["options"] == {
        "encoding": "utf-8",
        "newline": "\n",
        "create_parents": True,
        "root": request.gold_root,
        "role": "scenario gold file",
        "sync": True,
        "preserve_existing_mode": True,
    }

    record = result.record
    assert record.scenario_id == SCENARIO_ID
    assert record.source_run_id == RUN_ID
    assert record.previous_sha256 is None
    assert record.new_sha256 == _sha256(_gold_text().encode())
    assert record.updated_at == FIXED_TIME
    assert record.raw_stdout_path == request.raw_stdout_path
    assert record.raw_stderr_path == request.raw_stderr_path
    assert record.normalized_output_path == request.normalized_output_path
    assert record.diff_evidence_path == request.diff_evidence_path
    assert dict(record.metadata) == {
        "gf_version": "3.12",
        "normalization_profile": "scenario-default",
    }


def test_update_record_mapping_is_immutable_and_complete(
    tmp_path: Path,
) -> None:
    result = update_gold(
        _request(
            tmp_path,
            rationale="Correction revue pour élève et bisedë.",
        ),
        write_text=_write_candidate({}),
        clock=lambda: FIXED_TIME,
    )
    assert result.record is not None

    payload = result.record.to_mapping()

    assert payload["scenario_id"] == SCENARIO_ID
    assert payload["source_run_id"] == RUN_ID
    assert payload["updated_at"] == "2026-07-25T19:04:23Z"
    assert payload["new_sha256"] == result.record.new_sha256
    assert payload["rationale"] == "Correction revue pour élève et bisedë."
    assert payload["metadata"] == {
        "gf_version": "3.12",
        "normalization_profile": "scenario-default",
    }

    with pytest.raises(TypeError):
        payload["scenario_id"] = "changed"  # type: ignore[index]


def test_apply_detects_change_after_diff_review_and_never_calls_writer(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.gold_path.parent.mkdir(parents=True)
    request.gold_path.write_text(
        _gold_text("reviewed previous value"),
        encoding="utf-8",
    )
    plan = prepare_gold_update(request)
    request.gold_path.write_text(
        _gold_text("concurrent unreviewed value"),
        encoding="utf-8",
    )
    writes: list[Path] = []

    def forbidden_writer(destination: Path, text: str, **options: Any) -> Path:
        writes.append(destination)
        return destination

    with pytest.raises(
        GoldUpdateConcurrentChangeError,
        match="changed after diff preparation",
    ):
        apply_gold_update(plan, write_text=forbidden_writer)

    assert writes == []
    assert request.gold_path.read_text(encoding="utf-8") == _gold_text(
        "concurrent unreviewed value"
    )


def test_integrity_failure_restores_previous_gold(tmp_path: Path) -> None:
    request = _request(tmp_path)
    previous = _gold_text("previous accepted value").encode()
    request.gold_path.parent.mkdir(parents=True)
    request.gold_path.write_bytes(previous)
    plan = prepare_gold_update(request)

    def corrupting_writer(
        destination: Path,
        text: str,
        **options: Any,
    ) -> Path:
        destination.write_bytes(b"corrupted after write")
        return destination

    with pytest.raises(
        GoldUpdateIntegrityError,
        match="SHA-256 does not match",
    ):
        apply_gold_update(plan, write_text=corrupting_writer)

    assert request.gold_path.read_bytes() == previous


def test_integrity_failure_removes_new_unverified_gold(tmp_path: Path) -> None:
    request = _request(tmp_path)
    plan = prepare_gold_update(request)

    def corrupting_writer(
        destination: Path,
        text: str,
        **options: Any,
    ) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"corrupt")
        return destination

    with pytest.raises(GoldUpdateIntegrityError):
        apply_gold_update(plan, write_text=corrupting_writer)

    assert not request.gold_path.exists()


def test_existing_non_utf8_gold_is_refused(tmp_path: Path) -> None:
    request = _request(tmp_path)
    request.gold_path.parent.mkdir(parents=True)
    request.gold_path.write_bytes(b"\xff\xfe\x00")

    plan = prepare_gold_update(request)

    assert plan.status is GoldUpdateStatus.REFUSED
    assert GoldUpdateRefusalCode.INVALID_OUTPUT_SCHEMA in {
        refusal.code for refusal in plan.refusals
    }


def test_symlink_gold_destination_is_rejected_when_supported(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    target = tmp_path / "outside.gold"
    target.write_text("outside", encoding="utf-8")
    request.gold_path.parent.mkdir(parents=True)
    try:
        request.gold_path.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(GoldUpdateError, match="symbolic link"):
        prepare_gold_update(request)

    assert target.read_text(encoding="utf-8") == "outside"


def test_build_gold_diff_is_stable_and_names_previous_and_candidate(
    tmp_path: Path,
) -> None:
    gold_path = tmp_path / "validation" / "gold" / "parse-basic.gold"

    diff = build_gold_diff(
        previous_text=_gold_text("old"),
        candidate_text=_gold_text("new"),
        gold_path=gold_path,
        scenario_id=SCENARIO_ID,
    )

    assert diff.startswith(f"# scenario_id: parse-basic\n# gold_path: {gold_path.as_posix()}\n")
    assert f"--- {gold_path.as_posix()}@previous" in diff
    assert f"+++ {gold_path.as_posix()}@candidate" in diff
    assert "-old" in diff
    assert "+new" in diff
