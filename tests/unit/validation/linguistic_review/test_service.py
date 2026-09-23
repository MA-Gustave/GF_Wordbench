from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.validation.linguistic_review import (
    LinguisticReviewPolicy,
    LinguisticReviewStatus,
    LinguisticVerdict,
    ReviewConfidence,
    apply_linguistic_review_to_compendium,
    build_linguistic_review_request,
    evaluate_linguistic_review,
    gold_update_fields_for_review,
    response_from_document,
    write_linguistic_review_evaluation,
    write_linguistic_review_request,
)


def _source_lock(details: Path, digest: str = "a" * 64) -> None:
    details.mkdir(parents=True, exist_ok=True)
    (details / "source_lock.json").write_text(
        json.dumps({"aggregate_sha256": digest}), encoding="utf-8"
    )


def _run(tmp_path: Path, *, gold_match: bool | None = None):
    run_dir = tmp_path / "run_001"
    details = run_dir / "details"
    normalized = run_dir / "raw" / "scenarios" / "basic.normalized.txt"
    normalized.parent.mkdir(parents=True)
    normalized.write_text("E pashë djalin.\n", encoding="utf-8")
    _source_lock(details)
    scenario = SimpleNamespace(
        scenario_id="sq-basic",
        script_path=Path("validation/scenarios/sq-basic.gfs"),
        script_sha256="b" * 64,
        required=True,
        status=ValidationStatus.OK,
        normalized_output_path=normalized.relative_to(run_dir),
        gold_path=Path("validation/gold/sq-basic.gold") if gold_match is not None else None,
        gold_match=gold_match,
    )
    return SimpleNamespace(
        run_paths=SimpleNamespace(run_dir=run_dir, details_dir=details, run_id="20260922_150000"),
        gf_version="3.12",
        run_config=SimpleNamespace(
            language_context=SimpleNamespace(language_key="sqi")
        ),
        scenario_results=(scenario,),
    )


def _response_document(request, *, verdict="valid", confidence="high", digest=None):
    scenario = request.scenarios[0]
    return {
        "schema": "gf-wordbench-linguistic-review-response-v1",
        "request_id": request.request_id,
        "source_lock_sha256": request.source_lock_sha256,
        "reviewer": {"kind": "ai", "name": "ChatGPT", "model": "GPT-5.6 Sol"},
        "language_variety": request.language_variety,
        "reviews": [
            {
                "scenario_id": str(scenario.scenario_id),
                "output_sha256": digest or scenario.output_sha256,
                "verdict": verdict,
                "confidence": confidence,
                "rationale": "The sentence is grammatical Standard Albanian.",
                "issues": [],
                "alternatives": [],
                "compendium_levels": ["T9"],
            }
        ],
        "notes": ["AI-reviewed linguistic evidence; not independent human certification."],
    }


def test_build_request_binds_source_lock_and_output_hash(tmp_path: Path) -> None:
    run = _run(tmp_path)
    request = build_linguistic_review_request(run, language_variety="Standard Albanian")

    assert request.source_lock_sha256 == "a" * 64
    assert request.language_key == "sqi"
    assert request.language_variety == "Standard Albanian"
    assert len(request.scenarios) == 1
    scenario = request.scenarios[0]
    assert scenario.output_sha256 == hashlib.sha256("E pashë djalin.\n".encode()).hexdigest()
    assert request.request_id.startswith("LR-")


def test_write_request_publishes_run_owned_json(tmp_path: Path) -> None:
    run = _run(tmp_path)
    path = write_linguistic_review_request(run, language_variety="Standard Albanian")
    document = json.loads(path.read_text(encoding="utf-8"))

    assert path == run.run_paths.run_dir / "LINGUISTIC_REVIEW_REQUEST.json"
    assert document["schema"] == "gf-wordbench-linguistic-review-request-v1"
    assert document["response_contract"]["rule"].startswith("questionable/invalid")


def test_valid_high_confidence_review_passes_and_is_gold_eligible(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request))

    result = evaluate_linguistic_review(request, response)

    assert result.status is LinguisticReviewStatus.PASS
    assert result.verdict_counts == {"valid": 1}
    assert tuple(map(str, result.gold_eligible_scenarios)) == ("sq-basic",)
    assert not result.blocking_scenarios
    assert result.compendium_evidence["T9_parse_and_generation_behavior"] == "pass"
    assert result.compendium_evidence["T10_regression_validation"] == "not_assessed"


def test_reviewed_matching_gold_can_supply_t10_regression_evidence(tmp_path: Path) -> None:
    request = build_linguistic_review_request(
        _run(tmp_path, gold_match=True), language_variety="Standard Albanian"
    )
    response = response_from_document(_response_document(request))

    result = evaluate_linguistic_review(request, response)

    assert result.status is LinguisticReviewStatus.PASS
    assert result.compendium_evidence["T10_regression_validation"] == "pass"


@pytest.mark.parametrize("verdict", ["questionable", "invalid"])
def test_uncertain_or_invalid_review_is_blocking(tmp_path: Path, verdict: str) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, verdict=verdict))

    result = evaluate_linguistic_review(request, response)

    assert result.status is LinguisticReviewStatus.FAIL
    assert tuple(map(str, result.blocking_scenarios)) == ("sq-basic",)
    assert not result.gold_eligible_scenarios


def test_low_confidence_valid_review_is_not_gold_eligible(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, confidence="low"))

    result = evaluate_linguistic_review(request, response)

    assert result.status is LinguisticReviewStatus.FAIL
    assert not result.gold_eligible_scenarios


def test_output_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, digest="c" * 64))

    with pytest.raises(ValueError, match="output_sha256 mismatch"):
        evaluate_linguistic_review(request, response)


def test_source_lock_mismatch_is_rejected(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    document = _response_document(request)
    document["source_lock_sha256"] = "d" * 64
    response = response_from_document(document)

    with pytest.raises(ValueError, match="source lock"):
        evaluate_linguistic_review(request, response)


def test_evaluation_artifacts_are_deterministic_and_explicit(tmp_path: Path) -> None:
    run = _run(tmp_path)
    request = build_linguistic_review_request(run, language_variety="Standard Albanian")
    response = response_from_document(_response_document(request))
    result = evaluate_linguistic_review(request, response)

    json_path, md_path = write_linguistic_review_evaluation(result, run_dir=run.run_paths.run_dir)
    document = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert document["status"] == "pass"
    assert document["reviewer"]["kind"] == "ai"
    assert "AI-reviewed" not in markdown or "Linguistic Review Evidence" in markdown
    assert "questionable" in markdown
    assert markdown.endswith("\n")


def test_policy_can_require_high_confidence_for_gold(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, confidence="medium"))

    result = evaluate_linguistic_review(
        request,
        response,
        policy=LinguisticReviewPolicy(minimum_gold_confidence=ReviewConfidence.HIGH),
    )

    assert result.status is LinguisticReviewStatus.FAIL
    assert not result.gold_eligible_scenarios
    assert result.blocking_scenarios


def test_valid_variant_is_accepted_by_default_but_can_be_disallowed(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, verdict=LinguisticVerdict.VALID_VARIANT.value))

    assert evaluate_linguistic_review(request, response).status is LinguisticReviewStatus.PASS
    strict = evaluate_linguistic_review(
        request,
        response,
        policy=LinguisticReviewPolicy(allow_valid_variant=False),
    )
    assert strict.status is LinguisticReviewStatus.FAIL


def test_gold_bridge_requires_accepted_review_and_preserves_existing_safety_fields(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request))
    review = response.reviews[0]

    fields = gold_update_fields_for_review(response, review)

    assert fields["reviewer"] == "ChatGPT (GPT-5.6 Sol)"
    assert fields["rationale"].startswith("The sentence is grammatical")
    assert fields["decision_reference"].startswith("linguistic-review:LR-")
    assert fields["metadata"]["linguistic_verdict"] == "valid"
    assert "confirmed" not in fields
    assert "diff_reviewed" not in fields


def test_gold_bridge_rejects_questionable_review(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request, verdict="questionable"))

    with pytest.raises(ValueError, match="not eligible"):
        gold_update_fields_for_review(response, response.reviews[0])


def test_compendium_overlay_updates_only_t9_t10(tmp_path: Path) -> None:
    request = build_linguistic_review_request(_run(tmp_path, gold_match=True), language_variety="Standard Albanian")
    response = response_from_document(_response_document(request))
    evaluation = evaluate_linguistic_review(request, response)
    matrix = {
        "schema": "gf-wordbench-compendium-test-matrix-v1",
        "protocol": "TEST_RGL",
        "levels": [
            {"level": "T2", "name": "morphology_tests", "status": "not_assessed"},
            {"level": "T9", "name": "parse_and_generation_behavior", "status": "not_assessed"},
            {"level": "T10", "name": "regression_validation", "status": "not_assessed"},
        ],
    }

    reviewed = apply_linguistic_review_to_compendium(matrix, evaluation)

    by_level = {item["level"]: item for item in reviewed["levels"]}
    assert by_level["T2"]["status"] == "not_assessed"
    assert by_level["T9"]["status"] == "pass"
    assert by_level["T10"]["status"] == "pass"
    assert reviewed["linguistic_review"]["reviewer_kind"] == "ai"
