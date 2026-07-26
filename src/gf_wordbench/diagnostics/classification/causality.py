"""Deterministic causal classification for structured GF Wordbench results."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)

_MAX_REASON_LENGTH: Final[int] = 1_000
_MAX_EVIDENCE_PATHS: Final[int] = 256
_MAX_BLOCKERS: Final[int] = 10_000
_WINDOWS_DRIVE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


@unique
class CausalityReason(StrEnum):
    SUCCESS = "success"
    POLICY_SKIP = "policy_skip"
    EXCLUDED_NOISE = "excluded_noise"
    CONFIRMED_BLOCKER = "confirmed_blocker"
    SELF_REFERENCE = "self_reference"
    LOCAL_LOCATION = "local_location"
    LOCAL_STAGE_FAILURE = "local_stage_failure"
    LOCAL_CONTRACT_FAILURE = "local_contract_failure"
    LOCAL_ARTIFACT_FAILURE = "local_artifact_failure"
    LOCAL_TYPE_OR_SYNTAX = "local_type_or_syntax"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    UNRESOLVED_CYCLE = "unresolved_cycle"
    UNKNOWN_EXTERNAL_REFERENCE = "unknown_external_reference"
    SUCCESSFUL_EXTERNAL_REFERENCE = "successful_external_reference"
    TIMEOUT_WITHOUT_BLOCKER = "timeout_without_blocker"
    GLOBAL_OR_LAUNCH_FAILURE = "global_or_launch_failure"
    PARSER_FAILURE = "parser_failure"
    OUTPUT_TRUNCATED = "output_truncated"
    COMBINED_INPUTS = "combined_inputs"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class CausalityFacts:
    confirmed_blockers: tuple[str, ...] = ()
    candidate_blockers: tuple[str, ...] = ()
    self_reference: bool = False
    local_location: bool = False
    local_stage_failure: bool = False
    local_contract_failure: bool = False
    local_artifact_failure: bool = False
    conflicting_evidence: bool = False
    unresolved_cycle: bool = False
    unknown_external_reference: bool = False
    successful_external_reference: bool = False
    timeout: bool = False
    global_or_launch_failure: bool = False
    parser_failure: bool = False
    output_truncated: bool = False
    combined_inputs: bool = False
    policy_skip: bool = False
    excluded_noise: bool = False
    evidence_paths: tuple[Path, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "self_reference",
            "local_location",
            "local_stage_failure",
            "local_contract_failure",
            "local_artifact_failure",
            "conflicting_evidence",
            "unresolved_cycle",
            "unknown_external_reference",
            "successful_external_reference",
            "timeout",
            "global_or_launch_failure",
            "parser_failure",
            "output_truncated",
            "combined_inputs",
            "policy_skip",
            "excluded_noise",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a bool")

        confirmed = normalize_blocker_ids(self.confirmed_blockers)
        candidates = normalize_blocker_ids(self.candidate_blockers)
        evidence_paths = _freeze_paths(self.evidence_paths)
        metadata = _freeze_metadata(self.metadata)

        if self.policy_skip and self.excluded_noise:
            raise ValueError("policy_skip and excluded_noise are mutually exclusive")
        if self.unresolved_cycle and confirmed:
            raise ValueError(
                "unresolved_cycle cannot be combined with confirmed root blockers"
            )

        object.__setattr__(self, "confirmed_blockers", confirmed)
        object.__setattr__(self, "candidate_blockers", candidates)
        object.__setattr__(self, "evidence_paths", evidence_paths)
        object.__setattr__(self, "metadata", metadata)

    @property
    def has_local_evidence(self) -> bool:
        return any(
            (
                self.self_reference,
                self.local_location,
                self.local_stage_failure,
                self.local_contract_failure,
                self.local_artifact_failure,
            )
        )


@dataclass(frozen=True, slots=True)
class CausalityDecision:
    diagnostic_class: DiagnosticClass
    blocked_by: tuple[str, ...]
    is_direct: bool
    reason: CausalityReason
    explanation: str
    evidence_paths: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.diagnostic_class, DiagnosticClass):
            raise TypeError("diagnostic_class must be DiagnosticClass")
        if not isinstance(self.reason, CausalityReason):
            raise TypeError("reason must be CausalityReason")
        if type(self.is_direct) is not bool:
            raise TypeError("is_direct must be a bool")

        blocked_by = normalize_blocker_ids(self.blocked_by)
        explanation = _require_text(
            self.explanation,
            field_name="explanation",
            max_length=_MAX_REASON_LENGTH,
        )
        evidence_paths = _freeze_paths(self.evidence_paths)

        if self.is_direct is not (
            self.diagnostic_class is DiagnosticClass.DIRECT
        ):
            raise ValueError(
                "is_direct must equal diagnostic_class == DiagnosticClass.DIRECT"
            )
        if self.diagnostic_class is DiagnosticClass.DOWNSTREAM:
            if not blocked_by:
                raise ValueError("downstream decisions require blocked_by")
        elif blocked_by:
            raise ValueError(
                "blocked_by must be empty unless diagnostic_class is downstream"
            )

        object.__setattr__(self, "blocked_by", blocked_by)
        object.__setattr__(self, "explanation", explanation)
        object.__setattr__(self, "evidence_paths", evidence_paths)


def classify_causality(
    *,
    subject_id: str,
    status: ValidationStatus,
    error_kind: ErrorKind,
    facts: CausalityFacts,
) -> CausalityDecision:
    subject = normalize_subject_id(subject_id)
    if not isinstance(status, ValidationStatus):
        raise TypeError("status must be ValidationStatus")
    if not isinstance(error_kind, ErrorKind):
        raise TypeError("error_kind must be ErrorKind")
    if not isinstance(facts, CausalityFacts):
        raise TypeError("facts must be CausalityFacts")

    blockers = tuple(
        blocker
        for blocker in facts.confirmed_blockers
        if blocker != subject
    )

    if status is ValidationStatus.OK:
        if error_kind is not ErrorKind.OK:
            raise ValueError("status OK requires error_kind OK")
        return _decision(
            DiagnosticClass.OK,
            reason=CausalityReason.SUCCESS,
            explanation="The requested validation criterion passed.",
            evidence_paths=facts.evidence_paths,
        )

    if status is ValidationStatus.SKIPPED:
        if error_kind is not ErrorKind.OK:
            raise ValueError("status SKIPPED requires error_kind OK")
        if blockers:
            raise ValueError(
                "canonical skipped results cannot carry confirmed blockers; "
                "represent a required blocked operation as ERROR/downstream"
            )
        if facts.excluded_noise:
            return _decision(
                DiagnosticClass.NOISE,
                reason=CausalityReason.EXCLUDED_NOISE,
                explanation=(
                    "The retained subject is explicitly excluded or "
                    "non-actionable under selection policy."
                ),
                evidence_paths=facts.evidence_paths,
            )
        return _decision(
            DiagnosticClass.SKIPPED,
            reason=CausalityReason.POLICY_SKIP,
            explanation=(
                "The operation was intentionally omitted by the resolved plan."
            ),
            evidence_paths=facts.evidence_paths,
        )

    if status not in (ValidationStatus.FAIL, ValidationStatus.ERROR):
        raise ValueError(f"unsupported validation status: {status!r}")
    if error_kind is ErrorKind.OK:
        raise ValueError("FAIL or ERROR requires a non-OK error_kind")
    if facts.policy_skip or facts.excluded_noise:
        raise ValueError(
            "failing results cannot be classified as policy skips or noise"
        )

    if blockers:
        return _decision(
            DiagnosticClass.DOWNSTREAM,
            blocked_by=blockers,
            reason=CausalityReason.CONFIRMED_BLOCKER,
            explanation=(
                "One or more confirmed failed subjects block the current subject."
            ),
            evidence_paths=facts.evidence_paths,
        )

    if facts.unresolved_cycle:
        return _decision(
            DiagnosticClass.AMBIGUOUS,
            reason=CausalityReason.UNRESOLVED_CYCLE,
            explanation=(
                "A dependency cycle exists and no supported root blocker can be "
                "resolved."
            ),
            evidence_paths=facts.evidence_paths,
        )

    if facts.conflicting_evidence or facts.candidate_blockers:
        return _decision(
            DiagnosticClass.AMBIGUOUS,
            reason=CausalityReason.CONFLICTING_EVIDENCE,
            explanation=(
                "The available evidence supports multiple plausible causal "
                "origins."
            ),
            evidence_paths=facts.evidence_paths,
        )

    local_reason = _local_reason(facts)
    if local_reason is not None:
        return _decision(
            DiagnosticClass.DIRECT,
            reason=local_reason,
            explanation=_LOCAL_EXPLANATIONS[local_reason],
            evidence_paths=facts.evidence_paths,
        )

    if error_kind in (ErrorKind.TYPE, ErrorKind.SYNTAX):
        if not (
            facts.unknown_external_reference
            or facts.successful_external_reference
            or facts.combined_inputs
            or facts.parser_failure
            or facts.output_truncated
        ):
            return _decision(
                DiagnosticClass.DIRECT,
                reason=CausalityReason.LOCAL_TYPE_OR_SYNTAX,
                explanation=(
                    "A local type or syntax failure is attached to the current "
                    "subject and no failed external blocker is resolved."
                ),
                evidence_paths=facts.evidence_paths,
            )

    reason, explanation = _ambiguous_reason(error_kind, facts)
    return _decision(
        DiagnosticClass.AMBIGUOUS,
        reason=reason,
        explanation=explanation,
        evidence_paths=facts.evidence_paths,
    )


def validate_causality_decision(
    *,
    status: ValidationStatus,
    error_kind: ErrorKind,
    decision: CausalityDecision,
) -> None:
    if not isinstance(status, ValidationStatus):
        raise TypeError("status must be ValidationStatus")
    if not isinstance(error_kind, ErrorKind):
        raise TypeError("error_kind must be ErrorKind")
    if not isinstance(decision, CausalityDecision):
        raise TypeError("decision must be CausalityDecision")

    diagnostic_class = decision.diagnostic_class
    if status is ValidationStatus.OK:
        if diagnostic_class is not DiagnosticClass.OK:
            raise ValueError("status OK requires diagnostic_class ok")
        if error_kind is not ErrorKind.OK:
            raise ValueError("status OK requires error_kind OK")
        return

    if status is ValidationStatus.SKIPPED:
        if diagnostic_class not in (
            DiagnosticClass.SKIPPED,
            DiagnosticClass.NOISE,
        ):
            raise ValueError(
                "status SKIPPED requires diagnostic_class skipped or noise"
            )
        if error_kind is not ErrorKind.OK:
            raise ValueError("status SKIPPED requires error_kind OK")
        return

    if status in (ValidationStatus.FAIL, ValidationStatus.ERROR):
        if diagnostic_class not in (
            DiagnosticClass.DIRECT,
            DiagnosticClass.DOWNSTREAM,
            DiagnosticClass.AMBIGUOUS,
        ):
            raise ValueError(
                "FAIL and ERROR require direct, downstream, or ambiguous causality"
            )
        if error_kind is ErrorKind.OK:
            raise ValueError("FAIL and ERROR require a non-OK error_kind")
        return

    raise ValueError(f"unsupported validation status: {status!r}")


def normalize_subject_id(value: str) -> str:
    text = _require_text(value, field_name="subject_id", max_length=1_024)
    normalized = text.strip().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    if normalized.startswith("/") or _WINDOWS_DRIVE_RE.match(normalized):
        raise ValueError("subject_id must not be an absolute path")

    path = PurePosixPath(normalized)
    if not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("subject_id must be a stable relative identity")

    return path.as_posix()


def normalize_blocker_ids(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("blocker IDs must be an iterable of strings")

    normalized = {normalize_subject_id(value) for value in values}
    if len(normalized) > _MAX_BLOCKERS:
        raise ValueError("blocker count exceeds the supported limit")

    return tuple(sorted(normalized, key=lambda item: (item.casefold(), item)))


def _decision(
    diagnostic_class: DiagnosticClass,
    *,
    reason: CausalityReason,
    explanation: str,
    blocked_by: tuple[str, ...] = (),
    evidence_paths: tuple[Path, ...] = (),
) -> CausalityDecision:
    return CausalityDecision(
        diagnostic_class=diagnostic_class,
        blocked_by=blocked_by,
        is_direct=diagnostic_class is DiagnosticClass.DIRECT,
        reason=reason,
        explanation=explanation,
        evidence_paths=evidence_paths,
    )


def _local_reason(facts: CausalityFacts) -> CausalityReason | None:
    if facts.local_location:
        return CausalityReason.LOCAL_LOCATION
    if facts.self_reference:
        return CausalityReason.SELF_REFERENCE
    if facts.local_stage_failure:
        return CausalityReason.LOCAL_STAGE_FAILURE
    if facts.local_contract_failure:
        return CausalityReason.LOCAL_CONTRACT_FAILURE
    if facts.local_artifact_failure:
        return CausalityReason.LOCAL_ARTIFACT_FAILURE
    return None


def _ambiguous_reason(
    error_kind: ErrorKind,
    facts: CausalityFacts,
) -> tuple[CausalityReason, str]:
    if facts.timeout or error_kind is ErrorKind.TIMEOUT:
        return (
            CausalityReason.TIMEOUT_WITHOUT_BLOCKER,
            "The operation timed out and no confirmed causal blocker is known.",
        )
    if facts.global_or_launch_failure or error_kind in (
        ErrorKind.CONFIG,
        ErrorKind.IO,
        ErrorKind.TOOL,
    ):
        return (
            CausalityReason.GLOBAL_OR_LAUNCH_FAILURE,
            "The failure is operational or framework-wide and cannot be "
            "attributed safely to the current subject.",
        )
    if facts.parser_failure:
        return (
            CausalityReason.PARSER_FAILURE,
            "Diagnostic interpretation was not reliable enough to establish "
            "causality.",
        )
    if facts.output_truncated:
        return (
            CausalityReason.OUTPUT_TRUNCATED,
            "Captured evidence ended before a reliable causal conclusion could "
            "be established.",
        )
    if facts.combined_inputs:
        return (
            CausalityReason.COMBINED_INPUTS,
            "The operation combines multiple inputs and does not identify one "
            "supported causal subject.",
        )
    if facts.unknown_external_reference:
        return (
            CausalityReason.UNKNOWN_EXTERNAL_REFERENCE,
            "The diagnostic references an external subject that cannot be "
            "resolved to a selected result.",
        )
    if facts.successful_external_reference:
        return (
            CausalityReason.SUCCESSFUL_EXTERNAL_REFERENCE,
            "The diagnostic references an external selected subject that did "
            "not fail in this run.",
        )
    return (
        CausalityReason.INSUFFICIENT_EVIDENCE,
        "The available evidence does not reliably distinguish a local failure "
        "from a dependency failure.",
    )


def _freeze_paths(values: Iterable[Path]) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError("evidence_paths must be an iterable of pathlib.Path")
    result = tuple(values)
    if len(result) > _MAX_EVIDENCE_PATHS:
        raise ValueError("evidence_paths exceeds the supported limit")
    for path in result:
        if not isinstance(path, Path):
            raise TypeError("evidence_paths must contain pathlib.Path values")
        if "\x00" in str(path):
            raise ValueError("evidence paths must not contain NUL characters")
    return result


def _freeze_metadata(values: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")
    copied: dict[str, str] = {}
    for key, value in values.items():
        normalized_key = _require_text(
            key,
            field_name="metadata key",
            max_length=256,
        )
        normalized_value = _require_text(
            value,
            field_name=f"metadata[{normalized_key!r}]",
            max_length=4_096,
            allow_empty=True,
        )
        copied[normalized_key] = normalized_value
    return MappingProxyType(copied)


def _require_text(
    value: object,
    *,
    field_name: str,
    max_length: int,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length limit")
    return value


_LOCAL_EXPLANATIONS: Final[Mapping[CausalityReason, str]] = MappingProxyType(
    {
        CausalityReason.LOCAL_LOCATION: (
            "A structured diagnostic location identifies the current subject."
        ),
        CausalityReason.SELF_REFERENCE: (
            "Structured diagnostic evidence explicitly references the current "
            "subject."
        ),
        CausalityReason.LOCAL_STAGE_FAILURE: (
            "Stage-owned structured evidence identifies a failure local to the "
            "current subject."
        ),
        CausalityReason.LOCAL_CONTRACT_FAILURE: (
            "The current subject violates a contract it directly owns."
        ),
        CausalityReason.LOCAL_ARTIFACT_FAILURE: (
            "The current subject's producer operation violates its artifact "
            "contract."
        ),
    }
)


__all__ = (
    "CausalityDecision",
    "CausalityFacts",
    "CausalityReason",
    "classify_causality",
    "normalize_blocker_ids",
    "normalize_subject_id",
    "validate_causality_decision",
)
