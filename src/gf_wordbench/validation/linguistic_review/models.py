"""Immutable models for external linguistic review evidence.

The review workflow is intentionally provider-neutral. GF Wordbench exports
bounded scenario evidence, an external reviewer (human or AI) returns a
structured response, and Wordbench verifies that response against the exact
run/source/output hashes before it can be used as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique
import re
from types import MappingProxyType
from typing import Final, Mapping

from gf_wordbench.kernel.ids import ScenarioId, validate_scenario_id

REQUEST_SCHEMA: Final[str] = "gf-wordbench-linguistic-review-request-v1"
RESPONSE_SCHEMA: Final[str] = "gf-wordbench-linguistic-review-response-v1"
EVALUATION_SCHEMA: Final[str] = "gf-wordbench-linguistic-review-evaluation-v1"

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID_RE: Final[re.Pattern[str]] = re.compile(r"^LR-[0-9a-f]{24}$")
_LEVEL_RE: Final[re.Pattern[str]] = re.compile(r"^T(?:[1-9]|10)$")
_MAX_TEXT: Final[int] = 1_000_000
_MAX_SHORT_TEXT: Final[int] = 8_192
_MAX_ITEMS: Final[int] = 10_000


@unique
class LinguisticVerdict(StrEnum):
    VALID = "valid"
    VALID_VARIANT = "valid_variant"
    QUESTIONABLE = "questionable"
    INVALID = "invalid"


@unique
class ReviewConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@unique
class LinguisticReviewStatus(StrEnum):
    NOT_ASSESSED = "not_assessed"
    PARTIAL = "partial"
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class LinguisticReviewScenario:
    scenario_id: ScenarioId
    script_path: str
    script_sha256: str
    normalized_output_path: str
    output_sha256: str
    output_text: str
    required: bool
    gold_path: str | None = None
    gold_match: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", validate_scenario_id(self.scenario_id))
        for field_name in ("script_path", "normalized_output_path"):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name=field_name),
            )
        for field_name in ("script_sha256", "output_sha256"):
            object.__setattr__(
                self,
                field_name,
                _sha256(getattr(self, field_name), field_name=field_name),
            )
        object.__setattr__(
            self,
            "output_text",
            _required_text(self.output_text, field_name="output_text", maximum=_MAX_TEXT),
        )
        if type(self.required) is not bool:
            raise TypeError("required must be a bool")
        if self.gold_path is not None:
            object.__setattr__(
                self,
                "gold_path",
                _required_text(self.gold_path, field_name="gold_path"),
            )
        if self.gold_match is not None and type(self.gold_match) is not bool:
            raise TypeError("gold_match must be bool or None")


@dataclass(frozen=True, slots=True)
class LinguisticReviewRequest:
    request_id: str
    run_id: str
    source_lock_sha256: str
    gf_version: str
    language_key: str
    language_variety: str
    scenarios: tuple[LinguisticReviewScenario, ...]
    reviewer_instructions: tuple[str, ...]
    schema: str = REQUEST_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != REQUEST_SCHEMA:
            raise ValueError(f"schema must be {REQUEST_SCHEMA!r}")
        if not isinstance(self.request_id, str) or _REQUEST_ID_RE.fullmatch(self.request_id) is None:
            raise ValueError("request_id must use LR- plus 24 lowercase hex characters")
        for field_name in ("run_id", "gf_version", "language_key", "language_variety"):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name=field_name),
            )
        object.__setattr__(
            self,
            "source_lock_sha256",
            _sha256(self.source_lock_sha256, field_name="source_lock_sha256"),
        )
        scenarios = tuple(self.scenarios)
        if len(scenarios) > _MAX_ITEMS:
            raise ValueError("too many linguistic review scenarios")
        if not all(isinstance(item, LinguisticReviewScenario) for item in scenarios):
            raise TypeError("scenarios must contain LinguisticReviewScenario values")
        ids = [str(item.scenario_id) for item in scenarios]
        if len(set(ids)) != len(ids):
            raise ValueError("scenarios must have unique scenario_id values")
        instructions = _text_tuple(
            self.reviewer_instructions,
            field_name="reviewer_instructions",
            allow_empty=False,
        )
        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "reviewer_instructions", instructions)


@dataclass(frozen=True, slots=True)
class ReviewerIdentity:
    reviewer_kind: str
    reviewer_name: str
    model: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("reviewer_kind", "reviewer_name"):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name=field_name),
            )
        if self.model is not None:
            object.__setattr__(self, "model", _required_text(self.model, field_name="model"))

    @property
    def display_name(self) -> str:
        if self.model:
            return f"{self.reviewer_name} ({self.model})"
        return self.reviewer_name


@dataclass(frozen=True, slots=True)
class LinguisticReviewRecord:
    scenario_id: ScenarioId
    output_sha256: str
    verdict: LinguisticVerdict
    confidence: ReviewConfidence
    rationale: str
    issues: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    compendium_levels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", validate_scenario_id(self.scenario_id))
        object.__setattr__(
            self,
            "output_sha256",
            _sha256(self.output_sha256, field_name="output_sha256"),
        )
        if not isinstance(self.verdict, LinguisticVerdict):
            raise TypeError("verdict must be LinguisticVerdict")
        if not isinstance(self.confidence, ReviewConfidence):
            raise TypeError("confidence must be ReviewConfidence")
        object.__setattr__(
            self,
            "rationale",
            _required_text(self.rationale, field_name="rationale", maximum=_MAX_SHORT_TEXT),
        )
        object.__setattr__(self, "issues", _text_tuple(self.issues, field_name="issues"))
        object.__setattr__(
            self,
            "alternatives",
            _text_tuple(self.alternatives, field_name="alternatives"),
        )
        levels = tuple(self.compendium_levels)
        if len(levels) > 10:
            raise ValueError("too many compendium_levels")
        if len(set(levels)) != len(levels):
            raise ValueError("compendium_levels must be unique")
        for level in levels:
            if not isinstance(level, str) or _LEVEL_RE.fullmatch(level) is None:
                raise ValueError(f"unsupported compendium level {level!r}")
        object.__setattr__(self, "compendium_levels", levels)


@dataclass(frozen=True, slots=True)
class LinguisticReviewResponse:
    request_id: str
    source_lock_sha256: str
    reviewer: ReviewerIdentity
    language_variety: str
    reviews: tuple[LinguisticReviewRecord, ...]
    notes: tuple[str, ...] = ()
    schema: str = RESPONSE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != RESPONSE_SCHEMA:
            raise ValueError(f"schema must be {RESPONSE_SCHEMA!r}")
        if not isinstance(self.request_id, str) or _REQUEST_ID_RE.fullmatch(self.request_id) is None:
            raise ValueError("invalid request_id")
        object.__setattr__(
            self,
            "source_lock_sha256",
            _sha256(self.source_lock_sha256, field_name="source_lock_sha256"),
        )
        if not isinstance(self.reviewer, ReviewerIdentity):
            raise TypeError("reviewer must be ReviewerIdentity")
        object.__setattr__(
            self,
            "language_variety",
            _required_text(self.language_variety, field_name="language_variety"),
        )
        reviews = tuple(self.reviews)
        if len(reviews) > _MAX_ITEMS:
            raise ValueError("too many review records")
        if not all(isinstance(item, LinguisticReviewRecord) for item in reviews):
            raise TypeError("reviews must contain LinguisticReviewRecord values")
        ids = [str(item.scenario_id) for item in reviews]
        if len(set(ids)) != len(ids):
            raise ValueError("reviews must have unique scenario_id values")
        object.__setattr__(self, "reviews", reviews)
        object.__setattr__(self, "notes", _text_tuple(self.notes, field_name="notes"))


@dataclass(frozen=True, slots=True)
class LinguisticReviewPolicy:
    require_all_scenarios: bool = True
    allow_valid_variant: bool = True
    minimum_gold_confidence: ReviewConfidence = ReviewConfidence.MEDIUM

    def __post_init__(self) -> None:
        if type(self.require_all_scenarios) is not bool:
            raise TypeError("require_all_scenarios must be a bool")
        if type(self.allow_valid_variant) is not bool:
            raise TypeError("allow_valid_variant must be a bool")
        if not isinstance(self.minimum_gold_confidence, ReviewConfidence):
            raise TypeError("minimum_gold_confidence must be ReviewConfidence")


@dataclass(frozen=True, slots=True)
class LinguisticReviewEvaluation:
    request_id: str
    source_lock_sha256: str
    reviewer: ReviewerIdentity
    status: LinguisticReviewStatus
    requested_count: int
    reviewed_count: int
    verdict_counts: Mapping[str, int]
    confidence_counts: Mapping[str, int]
    missing_scenarios: tuple[ScenarioId, ...]
    gold_eligible_scenarios: tuple[ScenarioId, ...]
    blocking_scenarios: tuple[ScenarioId, ...]
    compendium_evidence: Mapping[str, str]
    notes: tuple[str, ...] = ()
    schema: str = EVALUATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != EVALUATION_SCHEMA:
            raise ValueError(f"schema must be {EVALUATION_SCHEMA!r}")
        if not isinstance(self.status, LinguisticReviewStatus):
            raise TypeError("status must be LinguisticReviewStatus")
        if not isinstance(self.reviewer, ReviewerIdentity):
            raise TypeError("reviewer must be ReviewerIdentity")
        if not isinstance(self.request_id, str) or _REQUEST_ID_RE.fullmatch(self.request_id) is None:
            raise ValueError("invalid request_id")
        object.__setattr__(
            self,
            "source_lock_sha256",
            _sha256(self.source_lock_sha256, field_name="source_lock_sha256"),
        )
        for field_name in ("requested_count", "reviewed_count"):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        object.__setattr__(self, "verdict_counts", _count_mapping(self.verdict_counts))
        object.__setattr__(self, "confidence_counts", _count_mapping(self.confidence_counts))
        for field_name in ("missing_scenarios", "gold_eligible_scenarios", "blocking_scenarios"):
            values = tuple(validate_scenario_id(item) for item in getattr(self, field_name))
            if len(set(map(str, values))) != len(values):
                raise ValueError(f"{field_name} must be unique")
            object.__setattr__(self, field_name, values)
        evidence = dict(self.compendium_evidence)
        for key, value in evidence.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("compendium_evidence must be string/string mapping")
        object.__setattr__(self, "compendium_evidence", MappingProxyType(evidence))
        object.__setattr__(self, "notes", _text_tuple(self.notes, field_name="notes"))


_CONFIDENCE_RANK: Final[Mapping[ReviewConfidence, int]] = MappingProxyType(
    {ReviewConfidence.LOW: 0, ReviewConfidence.MEDIUM: 1, ReviewConfidence.HIGH: 2}
)


def confidence_at_least(value: ReviewConfidence, minimum: ReviewConfidence) -> bool:
    if not isinstance(value, ReviewConfidence) or not isinstance(minimum, ReviewConfidence):
        raise TypeError("confidence values must be ReviewConfidence")
    return _CONFIDENCE_RANK[value] >= _CONFIDENCE_RANK[minimum]


def _required_text(value: object, *, field_name: str, maximum: int = _MAX_SHORT_TEXT) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    if len(text) > maximum:
        raise ValueError(f"{field_name} exceeds supported length")
    return text


def _sha256(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _text_tuple(value: object, *, field_name: str, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence of strings")
    try:
        values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be iterable") from exc
    if len(values) > _MAX_ITEMS:
        raise ValueError(f"{field_name} has too many items")
    normalized = tuple(_required_text(item, field_name=field_name) for item in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _count_mapping(value: Mapping[str, int]) -> Mapping[str, int]:
    result: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("count mapping keys must be non-empty strings")
        if type(count) is not int or count < 0:
            raise ValueError("count mapping values must be non-negative integers")
        result[key] = count
    return MappingProxyType(result)


__all__ = (
    "EVALUATION_SCHEMA",
    "REQUEST_SCHEMA",
    "RESPONSE_SCHEMA",
    "LinguisticReviewEvaluation",
    "LinguisticReviewPolicy",
    "LinguisticReviewRecord",
    "LinguisticReviewRequest",
    "LinguisticReviewResponse",
    "LinguisticReviewScenario",
    "LinguisticReviewStatus",
    "LinguisticVerdict",
    "ReviewConfidence",
    "ReviewerIdentity",
    "confidence_at_least",
)
