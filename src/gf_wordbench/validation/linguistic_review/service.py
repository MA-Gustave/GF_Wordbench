"""Provider-neutral linguistic-review export, import, verification, and evaluation."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Mapping

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.infrastructure.json_io import write_json
from gf_wordbench.kernel.statuses import ValidationStatus

from .models import (
    LinguisticReviewEvaluation,
    LinguisticReviewPolicy,
    LinguisticReviewRecord,
    LinguisticReviewRequest,
    LinguisticReviewResponse,
    LinguisticReviewScenario,
    LinguisticReviewStatus,
    LinguisticVerdict,
    ReviewConfidence,
    ReviewerIdentity,
    confidence_at_least,
)

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import RunResult

REQUEST_FILENAME: Final[str] = "LINGUISTIC_REVIEW_REQUEST.json"
RESPONSE_FILENAME: Final[str] = "LINGUISTIC_REVIEW_RESPONSE.json"
EVALUATION_JSON_FILENAME: Final[str] = "linguistic_review.json"
EVALUATION_MD_FILENAME: Final[str] = "linguistic_review.md"
_MAX_OUTPUT_BYTES: Final[int] = 2 * 1024 * 1024

_DEFAULT_INSTRUCTIONS: Final[tuple[str, ...]] = (
    "Judge the generated text only as linguistic evidence; do not infer success from GF exit status.",
    "Use verdict valid only when the text is grammatical and natural in the stated language variety.",
    "Use valid_variant for grammatical alternatives that are acceptable but marked, stylistic, or context-dependent.",
    "Use questionable whenever confidence is insufficient; uncertainty must not be promoted to a passing golden.",
    "Use invalid for ungrammatical, morphologically wrong, syntactically wrong, or clearly non-standard output.",
    "Preserve Unicode and quote the exact problematic substring in issues when useful.",
    "Return one review record for every requested scenario and echo each output_sha256 exactly.",
)


def build_linguistic_review_request(
    run_result: RunResult,
    *,
    language_variety: str,
) -> LinguisticReviewRequest:
    """Build a deterministic review request from successful normalized scenarios."""

    run_paths = _required_attr(run_result, "run_paths")
    run_dir = _absolute_path(_required_attr(run_paths, "run_dir"), field="run_dir")
    details_dir = _absolute_path(_required_attr(run_paths, "details_dir"), field="details_dir")
    source_lock_sha256 = _read_source_lock_sha256(details_dir / "source_lock.json")
    run_id = str(_required_attr(run_paths, "run_id"))
    gf_version = _required_text(_required_attr(run_result, "gf_version"), field="gf_version")
    config = _required_attr(run_result, "run_config")
    context = _required_attr(config, "language_context")
    language_key = _required_text(_required_attr(context, "language_key"), field="language_key")

    scenarios: list[LinguisticReviewScenario] = []
    for result in tuple(_required_attr(run_result, "scenario_results")):
        if _enum_value(_required_attr(result, "status")) != ValidationStatus.OK.value.lower():
            continue
        relative_output = _required_attr(result, "normalized_output_path")
        if relative_output is None:
            continue
        output_path = _run_owned_path(run_dir, relative_output)
        data = output_path.read_bytes()
        if len(data) > _MAX_OUTPUT_BYTES:
            raise ValueError(f"normalized scenario output exceeds review limit: {output_path}")
        text = data.decode("utf-8")
        scenarios.append(
            LinguisticReviewScenario(
                scenario_id=_required_attr(result, "scenario_id"),
                script_path=_portable_path(_required_attr(result, "script_path")),
                script_sha256=_required_attr(result, "script_sha256"),
                normalized_output_path=_portable_relative(run_dir, output_path),
                output_sha256=hashlib.sha256(data).hexdigest(),
                output_text=text,
                required=bool(_required_attr(result, "required")),
                gold_path=(
                    None
                    if _required_attr(result, "gold_path") is None
                    else _portable_path(_required_attr(result, "gold_path"))
                ),
                gold_match=_required_attr(result, "gold_match"),
            )
        )

    scenarios.sort(key=lambda item: str(item.scenario_id))
    request_id = _request_id(run_id, source_lock_sha256, scenarios)
    return LinguisticReviewRequest(
        request_id=request_id,
        run_id=run_id,
        source_lock_sha256=source_lock_sha256,
        gf_version=gf_version,
        language_key=language_key,
        language_variety=language_variety,
        scenarios=tuple(scenarios),
        reviewer_instructions=_DEFAULT_INSTRUCTIONS,
    )


def write_linguistic_review_request(
    run_result: RunResult,
    *,
    language_variety: str,
    destination: Path | None = None,
) -> Path:
    request = build_linguistic_review_request(run_result, language_variety=language_variety)
    run_dir = _absolute_path(_required_attr(_required_attr(run_result, "run_paths"), "run_dir"), field="run_dir")
    path = destination or (run_dir / REQUEST_FILENAME)
    path = _absolute_path(path, field="destination")
    _require_contained(path, run_dir)
    write_json(path, request_to_document(request))
    return path


def request_to_document(request: LinguisticReviewRequest) -> dict[str, object]:
    if not isinstance(request, LinguisticReviewRequest):
        raise TypeError("request must be LinguisticReviewRequest")
    return {
        "schema": request.schema,
        "request_id": request.request_id,
        "run_id": request.run_id,
        "source_lock_sha256": request.source_lock_sha256,
        "gf_version": request.gf_version,
        "language_key": request.language_key,
        "language_variety": request.language_variety,
        "reviewer_instructions": list(request.reviewer_instructions),
        "response_contract": {
            "schema": "gf-wordbench-linguistic-review-response-v1",
            "verdicts": [item.value for item in LinguisticVerdict],
            "confidence": [item.value for item in ReviewConfidence],
            "rule": "questionable/invalid/low-confidence outputs are never gold-eligible",
        },
        "scenarios": [
            {
                "scenario_id": str(item.scenario_id),
                "script_path": item.script_path,
                "script_sha256": item.script_sha256,
                "normalized_output_path": item.normalized_output_path,
                "output_sha256": item.output_sha256,
                "output_text": item.output_text,
                "required": item.required,
                "gold_path": item.gold_path,
                "gold_match": item.gold_match,
            }
            for item in request.scenarios
        ],
    }


def load_linguistic_review_response(path: Path) -> LinguisticReviewResponse:
    path = _absolute_path(path, field="path")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read linguistic review response: {exc}") from exc
    return response_from_document(document)


def response_from_document(document: object) -> LinguisticReviewResponse:
    mapping = _mapping(document, field="response")
    reviewer_doc = _mapping(mapping.get("reviewer"), field="reviewer")
    reviewer = ReviewerIdentity(
        reviewer_kind=_required_text(reviewer_doc.get("kind"), field="reviewer.kind"),
        reviewer_name=_required_text(reviewer_doc.get("name"), field="reviewer.name"),
        model=_optional_text(reviewer_doc.get("model"), field="reviewer.model"),
    )
    raw_reviews = mapping.get("reviews")
    if not isinstance(raw_reviews, list):
        raise TypeError("reviews must be a list")
    reviews: list[LinguisticReviewRecord] = []
    for index, raw in enumerate(raw_reviews):
        item = _mapping(raw, field=f"reviews[{index}]")
        reviews.append(
            LinguisticReviewRecord(
                scenario_id=_required_text(item.get("scenario_id"), field="scenario_id"),
                output_sha256=_required_text(item.get("output_sha256"), field="output_sha256"),
                verdict=LinguisticVerdict(_required_text(item.get("verdict"), field="verdict")),
                confidence=ReviewConfidence(
                    _required_text(item.get("confidence"), field="confidence")
                ),
                rationale=_required_text(item.get("rationale"), field="rationale"),
                issues=_string_list(item.get("issues", []), field="issues"),
                alternatives=_string_list(item.get("alternatives", []), field="alternatives"),
                compendium_levels=_string_list(
                    item.get("compendium_levels", []), field="compendium_levels"
                ),
            )
        )
    return LinguisticReviewResponse(
        schema=_required_text(mapping.get("schema"), field="schema"),
        request_id=_required_text(mapping.get("request_id"), field="request_id"),
        source_lock_sha256=_required_text(
            mapping.get("source_lock_sha256"), field="source_lock_sha256"
        ),
        reviewer=reviewer,
        language_variety=_required_text(
            mapping.get("language_variety"), field="language_variety"
        ),
        reviews=tuple(reviews),
        notes=_string_list(mapping.get("notes", []), field="notes"),
    )


def evaluate_linguistic_review(
    request: LinguisticReviewRequest,
    response: LinguisticReviewResponse,
    *,
    policy: LinguisticReviewPolicy | None = None,
) -> LinguisticReviewEvaluation:
    if not isinstance(request, LinguisticReviewRequest):
        raise TypeError("request must be LinguisticReviewRequest")
    if not isinstance(response, LinguisticReviewResponse):
        raise TypeError("response must be LinguisticReviewResponse")
    effective = policy or LinguisticReviewPolicy()
    if not isinstance(effective, LinguisticReviewPolicy):
        raise TypeError("policy must be LinguisticReviewPolicy")
    if response.request_id != request.request_id:
        raise ValueError("linguistic review response request_id does not match request")
    if response.source_lock_sha256 != request.source_lock_sha256:
        raise ValueError("linguistic review response source lock does not match request")
    if response.language_variety != request.language_variety:
        raise ValueError("linguistic review response language_variety does not match request")

    requested = {str(item.scenario_id): item for item in request.scenarios}
    reviewed = {str(item.scenario_id): item for item in response.reviews}
    extras = sorted(set(reviewed).difference(requested))
    if extras:
        raise ValueError(f"response contains scenarios not present in request: {', '.join(extras)}")
    for scenario_id, review in reviewed.items():
        if review.output_sha256 != requested[scenario_id].output_sha256:
            raise ValueError(f"output_sha256 mismatch for scenario {scenario_id}")

    missing = tuple(requested[key].scenario_id for key in sorted(set(requested).difference(reviewed)))
    blocking: list[Any] = []
    eligible: list[Any] = []
    for scenario_id in sorted(reviewed):
        review = reviewed[scenario_id]
        accepted = review.verdict is LinguisticVerdict.VALID or (
            effective.allow_valid_variant and review.verdict is LinguisticVerdict.VALID_VARIANT
        )
        if review.verdict in (LinguisticVerdict.INVALID, LinguisticVerdict.QUESTIONABLE):
            blocking.append(review.scenario_id)
        elif accepted and confidence_at_least(review.confidence, effective.minimum_gold_confidence):
            eligible.append(review.scenario_id)
        else:
            blocking.append(review.scenario_id)

    if blocking:
        status = LinguisticReviewStatus.FAIL
    elif missing and effective.require_all_scenarios:
        status = LinguisticReviewStatus.PARTIAL
    elif not reviewed:
        status = LinguisticReviewStatus.NOT_ASSESSED
    elif missing:
        status = LinguisticReviewStatus.PARTIAL
    else:
        status = LinguisticReviewStatus.PASS

    verdict_counts = Counter(item.verdict.value for item in response.reviews)
    confidence_counts = Counter(item.confidence.value for item in response.reviews)
    t9 = "pass" if status is LinguisticReviewStatus.PASS else (
        "fail" if status is LinguisticReviewStatus.FAIL else "not_assessed"
    )
    all_gold_match = bool(request.scenarios) and all(item.gold_match is True for item in request.scenarios)
    t10 = "pass" if t9 == "pass" and all_gold_match else "not_assessed"
    evidence = {
        "T9_parse_and_generation_behavior": t9,
        "T10_regression_validation": t10,
        "review_kind": response.reviewer.reviewer_kind,
        "reviewer": response.reviewer.display_name,
    }
    return LinguisticReviewEvaluation(
        request_id=request.request_id,
        source_lock_sha256=request.source_lock_sha256,
        reviewer=response.reviewer,
        status=status,
        requested_count=len(request.scenarios),
        reviewed_count=len(response.reviews),
        verdict_counts=dict(verdict_counts),
        confidence_counts=dict(confidence_counts),
        missing_scenarios=missing,
        gold_eligible_scenarios=tuple(eligible),
        blocking_scenarios=tuple(blocking),
        compendium_evidence=evidence,
        notes=response.notes,
    )


def write_linguistic_review_evaluation(
    evaluation: LinguisticReviewEvaluation,
    *,
    run_dir: Path,
) -> tuple[Path, Path]:
    if not isinstance(evaluation, LinguisticReviewEvaluation):
        raise TypeError("evaluation must be LinguisticReviewEvaluation")
    run_dir = _absolute_path(run_dir, field="run_dir")
    details_dir = run_dir / "details"
    json_path = details_dir / EVALUATION_JSON_FILENAME
    md_path = details_dir / EVALUATION_MD_FILENAME
    write_json(json_path, evaluation_to_document(evaluation))
    atomic_write_text(
        md_path,
        render_linguistic_review_evaluation(evaluation),
        encoding="utf-8",
        newline="\n",
        create_parents=True,
        root=run_dir,
        role="linguistic review report",
    )
    return json_path, md_path


def evaluation_to_document(evaluation: LinguisticReviewEvaluation) -> dict[str, object]:
    return {
        "schema": evaluation.schema,
        "request_id": evaluation.request_id,
        "source_lock_sha256": evaluation.source_lock_sha256,
        "reviewer": {
            "kind": evaluation.reviewer.reviewer_kind,
            "name": evaluation.reviewer.reviewer_name,
            "model": evaluation.reviewer.model,
        },
        "status": evaluation.status.value,
        "requested_count": evaluation.requested_count,
        "reviewed_count": evaluation.reviewed_count,
        "verdict_counts": dict(evaluation.verdict_counts),
        "confidence_counts": dict(evaluation.confidence_counts),
        "missing_scenarios": [str(item) for item in evaluation.missing_scenarios],
        "gold_eligible_scenarios": [str(item) for item in evaluation.gold_eligible_scenarios],
        "blocking_scenarios": [str(item) for item in evaluation.blocking_scenarios],
        "compendium_evidence": dict(evaluation.compendium_evidence),
        "notes": list(evaluation.notes),
    }


def render_linguistic_review_evaluation(evaluation: LinguisticReviewEvaluation) -> str:
    rows = (
        ("Status", evaluation.status.value.upper()),
        ("Reviewer", evaluation.reviewer.display_name),
        ("Reviewer kind", evaluation.reviewer.reviewer_kind),
        ("Request ID", evaluation.request_id),
        ("Source lock SHA-256", evaluation.source_lock_sha256),
        ("Scenarios requested", str(evaluation.requested_count)),
        ("Scenarios reviewed", str(evaluation.reviewed_count)),
        ("Gold-eligible", str(len(evaluation.gold_eligible_scenarios))),
        ("Blocking", str(len(evaluation.blocking_scenarios))),
        ("Missing", str(len(evaluation.missing_scenarios))),
        ("T9 review evidence", evaluation.compendium_evidence.get("T9_parse_and_generation_behavior", "not_assessed")),
        ("T10 regression evidence", evaluation.compendium_evidence.get("T10_regression_validation", "not_assessed")),
    )
    lines = ["# Linguistic Review Evidence", "", "| Field | Value |", "|---|---|"]
    lines.extend(f"| {key} | {value} |" for key, value in rows)
    lines.extend(("", "## Verdict counts", ""))
    for key in sorted(evaluation.verdict_counts):
        lines.append(f"- `{key}`: {evaluation.verdict_counts[key]}")
    lines.extend(("", "## Confidence counts", ""))
    for key in sorted(evaluation.confidence_counts):
        lines.append(f"- `{key}`: {evaluation.confidence_counts[key]}")
    lines.extend(("", "## Promotion policy", ""))
    lines.append(
        "Only `valid`/`valid_variant` records meeting the configured confidence floor are gold-eligible. "
        "`questionable`, `invalid`, and low-confidence records remain blocking evidence and are never silently promoted."
    )
    if evaluation.blocking_scenarios:
        lines.extend(("", "## Blocking scenarios", ""))
        lines.extend(f"- `{item}`" for item in evaluation.blocking_scenarios)
    if evaluation.missing_scenarios:
        lines.extend(("", "## Missing reviews", ""))
        lines.extend(f"- `{item}`" for item in evaluation.missing_scenarios)
    if evaluation.notes:
        lines.extend(("", "## Reviewer notes", ""))
        lines.extend(f"- {item}" for item in evaluation.notes)
    return "\n".join(lines).rstrip() + "\n"


def apply_linguistic_review_to_compendium(
    matrix_document: Mapping[str, object],
    evaluation: LinguisticReviewEvaluation,
) -> dict[str, object]:
    """Return a reviewed copy of a TEST_RGL Compendium matrix.

    Only T9/T10 are affected by this evidence type. T1-T7 remain untouched,
    preventing an AI linguistic review from implicitly certifying morphology or
    constructor coverage that the run did not execute.
    """

    if not isinstance(matrix_document, Mapping):
        raise TypeError("matrix_document must be a mapping")
    if not isinstance(evaluation, LinguisticReviewEvaluation):
        raise TypeError("evaluation must be LinguisticReviewEvaluation")
    if matrix_document.get("schema") != "gf-wordbench-compendium-test-matrix-v1":
        raise ValueError("unsupported Compendium matrix schema")
    raw_levels = matrix_document.get("levels")
    if not isinstance(raw_levels, list):
        raise TypeError("Compendium matrix levels must be a list")

    t9 = evaluation.compendium_evidence.get("T9_parse_and_generation_behavior", "not_assessed")
    t10 = evaluation.compendium_evidence.get("T10_regression_validation", "not_assessed")
    updates = {"T9": t9, "T10": t10}
    levels: list[dict[str, object]] = []
    for raw in raw_levels:
        item = dict(_mapping(raw, field="compendium level"))
        level = item.get("level")
        if level in updates and updates[str(level)] != "not_assessed":
            item["status"] = updates[str(level)]
            item["evidence_source"] = "linguistic_review"
            item["review_request_id"] = evaluation.request_id
        levels.append(item)

    document = dict(matrix_document)
    document["levels"] = levels
    document["linguistic_review"] = {
        "schema": evaluation.schema,
        "request_id": evaluation.request_id,
        "source_lock_sha256": evaluation.source_lock_sha256,
        "status": evaluation.status.value,
        "reviewer_kind": evaluation.reviewer.reviewer_kind,
        "reviewer": evaluation.reviewer.display_name,
        "requested_count": evaluation.requested_count,
        "reviewed_count": evaluation.reviewed_count,
        "gold_eligible_count": len(evaluation.gold_eligible_scenarios),
        "blocking_count": len(evaluation.blocking_scenarios),
    }
    document["note"] = (
        "TEST_RGL matrix augmented with hash-bound linguistic-review evidence. "
        "This evidence can assess T9/T10 only; it does not implicitly pass unexecuted T1-T7 levels."
    )
    return document


def write_reviewed_compendium_matrix(
    evaluation: LinguisticReviewEvaluation,
    *,
    canonical_matrix_path: Path,
    destination: Path | None = None,
) -> Path:
    canonical_matrix_path = _absolute_path(canonical_matrix_path, field="canonical_matrix_path")
    try:
        matrix = json.loads(canonical_matrix_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read Compendium matrix: {exc}") from exc
    reviewed = apply_linguistic_review_to_compendium(_mapping(matrix, field="matrix"), evaluation)
    path = destination or canonical_matrix_path.with_name("compendium_matrix.reviewed.json")
    path = _absolute_path(path, field="destination")
    _require_contained(path, canonical_matrix_path.parent.parent)
    write_json(path, reviewed)
    return path


def gold_update_fields_for_review(
    response: LinguisticReviewResponse,
    review: LinguisticReviewRecord,
    *,
    policy: LinguisticReviewPolicy | None = None,
) -> dict[str, object]:
    """Return reviewed fields for the existing ``GoldUpdateRequest`` contract.

    This bridge never writes a gold and never bypasses the existing explicit
    confirmation/diff-review requirements. It only prepares reviewer-owned
    fields after verifying that the linguistic verdict is promotion-eligible.
    """

    if review not in response.reviews:
        raise ValueError("review must belong to response")
    effective = policy or LinguisticReviewPolicy()
    accepted = review.verdict is LinguisticVerdict.VALID or (
        effective.allow_valid_variant and review.verdict is LinguisticVerdict.VALID_VARIANT
    )
    if not accepted:
        raise ValueError("review verdict is not eligible for gold promotion")
    if not confidence_at_least(review.confidence, effective.minimum_gold_confidence):
        raise ValueError("review confidence is below the gold-promotion threshold")
    return {
        "reviewer": response.reviewer.display_name,
        "rationale": review.rationale,
        "decision_reference": (
            f"linguistic-review:{response.request_id}:{review.scenario_id}"
        ),
        "metadata": dict(gold_promotion_metadata(response, review)),
    }


def gold_promotion_metadata(
    response: LinguisticReviewResponse,
    review: LinguisticReviewRecord,
) -> Mapping[str, str]:
    """Return metadata suitable for an existing explicit GoldUpdateRequest."""

    if review not in response.reviews:
        raise ValueError("review must belong to response")
    return {
        "reviewer": response.reviewer.display_name,
        "reviewer_kind": response.reviewer.reviewer_kind,
        "linguistic_verdict": review.verdict.value,
        "linguistic_confidence": review.confidence.value,
        "linguistic_review_request_id": response.request_id,
        "linguistic_review_output_sha256": review.output_sha256,
    }


def _request_id(
    run_id: str,
    source_lock_sha256: str,
    scenarios: list[LinguisticReviewScenario],
) -> str:
    digest = hashlib.sha256()
    digest.update(b"gf-wordbench-linguistic-review-request-v1\0")
    digest.update(run_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(source_lock_sha256.encode("ascii"))
    digest.update(b"\n")
    for item in scenarios:
        digest.update(str(item.scenario_id).encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.output_sha256.encode("ascii"))
        digest.update(b"\n")
    return "LR-" + digest.hexdigest()[:24]


def _read_source_lock_sha256(path: Path) -> str:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"source lock is unavailable or invalid: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("source lock document must be an object")
    value = document.get("aggregate_sha256")
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("source lock document has no valid aggregate_sha256")
    return value


def _run_owned_path(run_dir: Path, value: object) -> Path:
    path = value if isinstance(value, Path) else Path(str(value))
    candidate = path if path.is_absolute() else run_dir / path
    candidate = candidate.resolve(strict=True)
    _require_contained(candidate, run_dir)
    return candidate


def _portable_relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _portable_path(value: object) -> str:
    if isinstance(value, Path):
        return value.as_posix()
    return str(value).replace("\\", "/")


def _absolute_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    path = value.resolve(strict=False)
    if not path.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return path


def _require_contained(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes run directory: {path}") from exc


def _required_attr(value: object, name: str) -> Any:
    if not hasattr(value, name):
        raise TypeError(f"object must expose {name}")
    return getattr(value, name)


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).lower()


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field} must not be empty")
    return text


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be an object")
    return value


def _string_list(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return tuple(_required_text(item, field=field) for item in value)


__all__ = (
    "EVALUATION_JSON_FILENAME",
    "EVALUATION_MD_FILENAME",
    "REQUEST_FILENAME",
    "RESPONSE_FILENAME",
    "apply_linguistic_review_to_compendium",
    "build_linguistic_review_request",
    "evaluate_linguistic_review",
    "evaluation_to_document",
    "gold_promotion_metadata",
    "gold_update_fields_for_review",
    "load_linguistic_review_response",
    "render_linguistic_review_evaluation",
    "request_to_document",
    "response_from_document",
    "write_linguistic_review_evaluation",
    "write_linguistic_review_request",
    "write_reviewed_compendium_matrix",
)
