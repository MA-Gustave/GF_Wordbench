"""Deterministic causal-classification application service."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, cast, runtime_checkable

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import DiagnosticClass, ValidationStatus

from .blockers import BlockerGraphResolution, collapse_blocker_graph
from .causality import CausalityEvidence, classify_causality
from .relationships import (
    ResultIndexes,
    build_result_indexes,
    collect_structured_references,
    normalize_subject_identity,
    resolve_references,
    result_identity,
)

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import FileResult
    from gf_wordbench.validation.scenarios.models import ScenarioResult

__all__ = (
    "ClassificationBatch",
    "ClassificationIssue",
    "ClassificationService",
    "DiagnosticResult",
    "classify_diagnostic_results",
    "classify_file_results",
    "classify_scenario_results",
    "classify_single_result",
    "enforce_classification_coherence",
    "resolve_blocked_by",
)

_ResultT = TypeVar("_ResultT", bound="DiagnosticResult")


@runtime_checkable
class DiagnosticResult(Protocol):
    status: ValidationStatus
    diagnostic_class: DiagnosticClass
    blocked_by: list[str]

    @property
    def error_kind(self) -> object:
        ...

    @property
    def primary_message(self) -> str:
        ...


@dataclass(frozen=True, slots=True)
class ClassificationIssue:
    subject_id: str
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.subject_id.strip():
            raise ValueError("subject_id must not be empty")
        if not self.code.strip():
            raise ValueError("code must not be empty")
        if not self.message.strip():
            raise ValueError("message must not be empty")


@dataclass(frozen=True, slots=True)
class ClassificationBatch(Generic[_ResultT]):
    results: tuple[_ResultT, ...]
    issues: tuple[ClassificationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class ClassificationService:
    strict: bool = True

    def classify(
        self,
        results: Sequence[_ResultT],
        *,
        peer_results: Sequence[DiagnosticResult] = (),
        references_by_subject: Mapping[str, Iterable[str]] | None = None,
        noise_subjects: Collection[str] = (),
    ) -> ClassificationBatch[_ResultT]:
        return classify_diagnostic_results(
            results,
            peer_results=peer_results,
            references_by_subject=references_by_subject,
            noise_subjects=noise_subjects,
            strict=self.strict,
        )

    def classify_files(
        self,
        file_results: Sequence[FileResult],
        *,
        references_by_subject: Mapping[str, Iterable[str]] | None = None,
        noise_subjects: Collection[str] = (),
    ) -> ClassificationBatch[FileResult]:
        return classify_diagnostic_results(
            file_results,
            references_by_subject=references_by_subject,
            noise_subjects=noise_subjects,
            strict=self.strict,
        )

    def classify_scenarios(
        self,
        scenario_results: Sequence[ScenarioResult],
        *,
        prerequisite_results: Sequence[DiagnosticResult] = (),
        references_by_subject: Mapping[str, Iterable[str]] | None = None,
        noise_subjects: Collection[str] = (),
    ) -> ClassificationBatch[ScenarioResult]:
        return classify_diagnostic_results(
            scenario_results,
            peer_results=prerequisite_results,
            references_by_subject=references_by_subject,
            noise_subjects=noise_subjects,
            strict=self.strict,
        )


def classify_file_results(
    file_results: list[FileResult],
    *,
    references_by_subject: Mapping[str, Iterable[str]] | None = None,
    noise_subjects: Collection[str] = (),
    strict: bool = True,
) -> list[FileResult]:
    batch = classify_diagnostic_results(
        file_results,
        references_by_subject=references_by_subject,
        noise_subjects=noise_subjects,
        strict=strict,
    )
    return list(batch.results)


def classify_scenario_results(
    scenario_results: list[ScenarioResult],
    *,
    prerequisite_results: Sequence[DiagnosticResult] = (),
    references_by_subject: Mapping[str, Iterable[str]] | None = None,
    noise_subjects: Collection[str] = (),
    strict: bool = True,
) -> list[ScenarioResult]:
    batch = classify_diagnostic_results(
        scenario_results,
        peer_results=prerequisite_results,
        references_by_subject=references_by_subject,
        noise_subjects=noise_subjects,
        strict=strict,
    )
    return list(batch.results)


def classify_single_result(
    file_result: FileResult,
    file_results: list[FileResult],
    *,
    references_by_subject: Mapping[str, Iterable[str]] | None = None,
    strict: bool = True,
) -> FileResult:
    target_identity = result_identity(file_result)
    matches = [
        index
        for index, candidate in enumerate(file_results)
        if result_identity(candidate) == target_identity
    ]
    if len(matches) != 1:
        raise _contract_error(
            "classify_single_result requires exactly one matching result",
            subject=target_identity,
        )
    classified = classify_file_results(
        file_results,
        references_by_subject=references_by_subject,
        strict=strict,
    )
    return classified[matches[0]]


def resolve_blocked_by(
    file_result: FileResult,
    file_results: list[FileResult],
    *,
    references_by_subject: Mapping[str, Iterable[str]] | None = None,
    strict: bool = True,
) -> list[str]:
    target_identity = result_identity(file_result)
    all_results: tuple[DiagnosticResult, ...] = tuple(file_results)
    indexes = build_result_indexes(all_results, strict=strict)
    references = _references_for(
        file_result,
        references_by_subject=references_by_subject,
    )
    resolution = resolve_references(
        file_result,
        references,
        indexes,
    )
    blockers = _failed_blocker_identities(
        target_identity,
        resolution.resolved_subjects,
        indexes,
    )
    if not blockers:
        return []
    classifications = {
        result_identity(result): _diagnostic_class(result)
        for result in all_results
    }
    initial_edges = {target_identity: blockers}
    graph = collapse_blocker_graph(classifications, initial_edges)
    return list(graph.blockers_by_subject.get(target_identity, ()))


def classify_diagnostic_results(
    results: Sequence[_ResultT],
    *,
    peer_results: Sequence[DiagnosticResult] = (),
    references_by_subject: Mapping[str, Iterable[str]] | None = None,
    noise_subjects: Collection[str] = (),
    strict: bool = True,
) -> ClassificationBatch[_ResultT]:
    owned_results = tuple(results)
    peers = tuple(peer_results)
    combined: tuple[DiagnosticResult, ...] = (*owned_results, *peers)

    if not owned_results:
        return ClassificationBatch(())

    indexes = build_result_indexes(combined, strict=strict)
    normalized_noise = frozenset(
        normalize_subject_identity(value) for value in noise_subjects
    )
    issues: list[ClassificationIssue] = []
    initial_classes: dict[str, DiagnosticClass] = {}
    initial_blockers: dict[str, tuple[str, ...]] = {}

    for result in combined:
        identity = result_identity(result)
        if result not in owned_results:
            initial_classes[identity] = _diagnostic_class(result)
            initial_blockers[identity] = _normalized_existing_blockers(result)
            continue

        try:
            references = _references_for(
                result,
                references_by_subject=references_by_subject,
            )
            resolved = resolve_references(result, references, indexes)
            failed_blockers = _failed_blocker_identities(
                identity,
                resolved.resolved_subjects,
                indexes,
            )
            evidence = CausalityEvidence(
                subject_id=identity,
                failed_blockers=failed_blockers,
                self_referenced=resolved.self_referenced,
                unresolved_references=resolved.unresolved_references,
                has_subject_local_evidence=resolved.has_subject_local_evidence,
            )
            diagnostic_class = classify_causality(
                result,
                evidence,
                retained_noise=(
                    normalize_subject_identity(identity) in normalized_noise
                ),
            )
            initial_classes[identity] = diagnostic_class
            initial_blockers[identity] = (
                failed_blockers
                if diagnostic_class is DiagnosticClass.DOWNSTREAM
                else ()
            )
        except Exception as exc:
            if strict:
                raise
            initial_classes[identity] = DiagnosticClass.AMBIGUOUS
            initial_blockers[identity] = ()
            issues.append(
                ClassificationIssue(
                    subject_id=identity,
                    code="CLASSIFICATION_SUBJECT_ERROR",
                    message=f"{type(exc).__name__}: {exc}",
                )
            )

    graph = collapse_blocker_graph(initial_classes, initial_blockers)
    classified: list[_ResultT] = []

    for result in owned_results:
        identity = result_identity(result)
        diagnostic_class = graph.classifications.get(
            identity,
            DiagnosticClass.AMBIGUOUS,
        )
        blockers = graph.blockers_by_subject.get(identity, ())
        try:
            updated = _with_classification(
                result,
                diagnostic_class=diagnostic_class,
                blocked_by=blockers,
            )
            enforce_classification_coherence(updated)
        except Exception as exc:
            if strict:
                raise
            issues.append(
                ClassificationIssue(
                    subject_id=identity,
                    code="CLASSIFICATION_APPLY_ERROR",
                    message=f"{type(exc).__name__}: {exc}",
                )
            )
            updated = _best_effort_ambiguous(result)
        classified.append(cast(_ResultT, updated))

    return ClassificationBatch(tuple(classified), tuple(issues))


def enforce_classification_coherence(result: DiagnosticResult) -> None:
    status = _validation_status(result)
    diagnostic_class = _diagnostic_class(result)
    blockers = _normalized_existing_blockers(result)
    is_direct = _derived_is_direct(result)

    allowed = {
        ValidationStatus.OK: frozenset({DiagnosticClass.OK}),
        ValidationStatus.FAIL: frozenset(
            {
                DiagnosticClass.DIRECT,
                DiagnosticClass.DOWNSTREAM,
                DiagnosticClass.AMBIGUOUS,
            }
        ),
        ValidationStatus.ERROR: frozenset(
            {
                DiagnosticClass.DIRECT,
                DiagnosticClass.DOWNSTREAM,
                DiagnosticClass.AMBIGUOUS,
            }
        ),
        ValidationStatus.SKIPPED: frozenset(
            {DiagnosticClass.SKIPPED, DiagnosticClass.NOISE}
        ),
    }

    if diagnostic_class not in allowed[status]:
        raise _contract_error(
            f"{status.value} is incompatible with {diagnostic_class.value}",
            subject=result_identity(result),
        )
    if diagnostic_class is DiagnosticClass.DIRECT:
        if not is_direct or blockers:
            raise _contract_error(
                "direct classification requires is_direct=true and no blockers",
                subject=result_identity(result),
            )
    elif is_direct:
        raise _contract_error(
            "is_direct must be derived only from direct classification",
            subject=result_identity(result),
        )
    if diagnostic_class is DiagnosticClass.DOWNSTREAM:
        if not blockers:
            raise _contract_error(
                "downstream classification requires at least one blocker",
                subject=result_identity(result),
            )
    elif blockers:
        raise _contract_error(
            "blocked_by must be empty for non-downstream classifications",
            subject=result_identity(result),
        )


def _references_for(
    result: DiagnosticResult,
    *,
    references_by_subject: Mapping[str, Iterable[str]] | None,
) -> tuple[str, ...]:
    identity = result_identity(result)
    explicit: Iterable[str] = ()
    if references_by_subject is not None:
        explicit = (
            references_by_subject.get(identity)
            or references_by_subject.get(normalize_subject_identity(identity))
            or ()
        )
    collected = collect_structured_references(result)
    return _unique_strings((*collected, *tuple(explicit)))


def _failed_blocker_identities(
    subject_id: str,
    candidates: Iterable[str],
    indexes: ResultIndexes,
) -> tuple[str, ...]:
    normalized_subject = normalize_subject_identity(subject_id)
    blockers: set[str] = set()
    for candidate in candidates:
        normalized = normalize_subject_identity(candidate)
        if normalized == normalized_subject:
            continue
        peer = indexes.by_identity.get(normalized)
        if peer is None:
            continue
        if _validation_status(peer) not in {
            ValidationStatus.FAIL,
            ValidationStatus.ERROR,
        }:
            continue
        blockers.add(result_identity(peer))
    return tuple(sorted(blockers, key=normalize_subject_identity))


def _with_classification(
    result: _ResultT,
    *,
    diagnostic_class: DiagnosticClass,
    blocked_by: Iterable[str],
) -> _ResultT:
    normalized_blockers = tuple(
        sorted(
            {
                normalize_subject_identity(value): value
                for value in blocked_by
                if value and normalize_subject_identity(value)
                != normalize_subject_identity(result_identity(result))
            }.values(),
            key=normalize_subject_identity,
        )
    )
    if diagnostic_class is not DiagnosticClass.DOWNSTREAM:
        normalized_blockers = ()
    elif not normalized_blockers:
        diagnostic_class = DiagnosticClass.AMBIGUOUS

    direct = diagnostic_class is DiagnosticClass.DIRECT
    class_value = _enum_compatible_value(
        getattr(result, "diagnostic_class", diagnostic_class),
        diagnostic_class,
    )
    blocker_value = _collection_compatible_value(
        getattr(result, "blocked_by", []),
        normalized_blockers,
    )

    dataclass_field_names = (
        {item.name for item in fields(result)}
        if is_dataclass(result) and not isinstance(result, type)
        else set()
    )
    replacement_values: dict[str, object] = {}

    if "diagnostic_class" in dataclass_field_names:
        replacement_values["diagnostic_class"] = class_value
    if "blocked_by" in dataclass_field_names:
        replacement_values["blocked_by"] = blocker_value
    if "is_direct" in dataclass_field_names:
        replacement_values["is_direct"] = direct

    dataclass_parameters = getattr(type(result), "__dataclass_params__", None)
    if dataclass_parameters is not None and dataclass_parameters.frozen:
        return cast(_ResultT, replace(result, **replacement_values))

    try:
        setattr(result, "blocked_by", blocker_value)
        setattr(result, "diagnostic_class", class_value)
        if hasattr(result, "is_direct") and not isinstance(
            getattr(type(result), "is_direct", None),
            property,
        ):
            setattr(result, "is_direct", direct)
        return result
    except (AttributeError, TypeError):
        if replacement_values:
            return cast(_ResultT, replace(result, **replacement_values))
        raise _contract_error(
            "result does not expose writable classification-owned fields",
            subject=result_identity(result),
        )


def _best_effort_ambiguous(result: _ResultT) -> _ResultT:
    try:
        return _with_classification(
            result,
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
            blocked_by=(),
        )
    except Exception:
        return result


def _validation_status(result: DiagnosticResult) -> ValidationStatus:
    value = getattr(result, "status", None)
    if isinstance(value, ValidationStatus):
        return value
    raw = value.value if isinstance(value, Enum) else value
    try:
        return ValidationStatus(str(raw))
    except (TypeError, ValueError) as exc:
        raise _contract_error(
            f"unsupported validation status: {raw!r}",
            subject=result_identity(result),
        ) from exc


def _diagnostic_class(result: DiagnosticResult) -> DiagnosticClass:
    value = getattr(result, "diagnostic_class", None)
    if isinstance(value, DiagnosticClass):
        return value
    raw = value.value if isinstance(value, Enum) else value
    try:
        return DiagnosticClass(str(raw))
    except (TypeError, ValueError):
        status = _validation_status(result)
        if status is ValidationStatus.OK:
            return DiagnosticClass.OK
        if status is ValidationStatus.SKIPPED:
            return DiagnosticClass.SKIPPED
        return DiagnosticClass.AMBIGUOUS


def _derived_is_direct(result: DiagnosticResult) -> bool:
    return _diagnostic_class(result) is DiagnosticClass.DIRECT


def _normalized_existing_blockers(
    result: DiagnosticResult,
) -> tuple[str, ...]:
    value = getattr(result, "blocked_by", ())
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise _contract_error(
            "blocked_by must be a collection of stable identities",
            subject=result_identity(result),
        )
    return tuple(
        sorted(
            {
                normalize_subject_identity(str(item)): str(item)
                for item in value
                if str(item).strip()
            }.values(),
            key=normalize_subject_identity,
        )
    )


def _enum_compatible_value(current: object, value: DiagnosticClass) -> object:
    if isinstance(current, str) and not isinstance(current, DiagnosticClass):
        return value.value
    return value


def _collection_compatible_value(
    current: object,
    values: tuple[str, ...],
) -> object:
    if isinstance(current, tuple):
        return values
    if isinstance(current, frozenset):
        return frozenset(values)
    if isinstance(current, set):
        return set(values)
    return list(values)


def _unique_strings(values: Iterable[object]) -> tuple[str, ...]:
    normalized: dict[str, str] = {}
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        normalized.setdefault(normalize_subject_identity(text), text)
    return tuple(
        normalized[key]
        for key in sorted(normalized)
    )


def _contract_error(
    message: str,
    *,
    subject: str | None,
) -> ContractViolationError:
    return ContractViolationError(
        message,
        code="GF-WB-CONTRACT-011",
        stage="classify_failures",
        operation="classify-diagnostic-results",
        subject=subject,
    )
