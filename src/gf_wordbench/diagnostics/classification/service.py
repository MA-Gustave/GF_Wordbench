"""Deterministic causal-classification application service."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Collection as TypingCollection, Generic, Protocol, TypeVar, cast, runtime_checkable

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ValidationStatus,
)

from .causality import CausalityFacts, classify_causality
from .relationships import (
    build_blocker_graph,
    collapse_blocker_graph,
    normalize_blocker_identity,
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
    @property
    def status(self) -> ValidationStatus: ...

    @property
    def diagnostic_class(self) -> DiagnosticClass: ...

    @property
    def blocked_by(self) -> TypingCollection[str]: ...

    @property
    def error_kind(self) -> object: ...

    @property
    def primary_message(self) -> str: ...


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
class _ResultIndexes:
    by_identity: Mapping[str, DiagnosticResult]
    canonical_identity: Mapping[str, str]
    aliases: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class _ReferenceResolution:
    resolved_subjects: tuple[str, ...]
    unresolved_references: tuple[str, ...]
    self_referenced: bool
    has_subject_local_evidence: bool


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
    target_identity = _result_identity(file_result)
    matches = [
        index
        for index, candidate in enumerate(file_results)
        if _result_identity(candidate) == target_identity
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
    target_identity = _result_identity(file_result)
    all_results: tuple[DiagnosticResult, ...] = tuple(file_results)
    indexes = _build_result_indexes(all_results, strict=strict)
    references = _references_for(
        file_result,
        references_by_subject=references_by_subject,
    )
    reference_resolution = _resolve_references(
        file_result,
        references,
        indexes,
    )
    blockers = _failed_blocker_identities(
        target_identity,
        reference_resolution.resolved_subjects,
        indexes,
    )
    if not blockers:
        return []
    classifications = {
        _result_identity(result): _diagnostic_class(result) for result in all_results
    }
    initial_edges: dict[object, Iterable[object]] = {target_identity: blockers}
    graph = build_blocker_graph(
        initial_edges,
        known_subjects=classifications,
    )
    resolution = collapse_blocker_graph(
        graph,
        root_subjects=(
            identity
            for identity, diagnostic_class in classifications.items()
            if diagnostic_class is DiagnosticClass.DIRECT
        ),
        terminal_subjects_are_roots=False,
    )
    return list(resolution.root_blockers.get(target_identity, ()))


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
    owned_object_ids = frozenset(id(result) for result in owned_results)

    if not owned_results:
        return ClassificationBatch(())

    indexes = _build_result_indexes(combined, strict=strict)
    normalized_noise = frozenset(_normalize_subject_identity(value) for value in noise_subjects)
    issues: list[ClassificationIssue] = []
    initial_classes: dict[str, DiagnosticClass] = {}
    initial_blockers: dict[object, Iterable[object]] = {}

    for result in combined:
        identity = _result_identity(result)
        if id(result) not in owned_object_ids:
            initial_classes[identity] = _diagnostic_class(result)
            initial_blockers[identity] = _normalized_existing_blockers(result)
            continue

        try:
            references = _references_for(
                result,
                references_by_subject=references_by_subject,
            )
            resolved = _resolve_references(result, references, indexes)
            failed_blockers = _failed_blocker_identities(
                identity,
                resolved.resolved_subjects,
                indexes,
            )
            status = _validation_status(result)
            error_kind = _error_kind(result)
            retained_noise = _normalize_subject_identity(identity) in normalized_noise
            decision = classify_causality(
                subject_id=identity,
                status=status,
                error_kind=error_kind,
                facts=_causality_facts(
                    result,
                    status=status,
                    error_kind=error_kind,
                    failed_blockers=failed_blockers,
                    resolved=resolved,
                    indexes=indexes,
                    retained_noise=retained_noise,
                ),
            )
            initial_classes[identity] = decision.diagnostic_class
            initial_blockers[identity] = decision.blocked_by
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

    graph = build_blocker_graph(
        initial_blockers,
        known_subjects=initial_classes,
    )
    resolution = collapse_blocker_graph(
        graph,
        root_subjects=(
            identity
            for identity, diagnostic_class in initial_classes.items()
            if diagnostic_class is DiagnosticClass.DIRECT
        ),
        terminal_subjects_are_roots=False,
    )
    classified: list[_ResultT] = []

    for result in owned_results:
        identity = _result_identity(result)
        diagnostic_class = initial_classes.get(
            identity,
            DiagnosticClass.AMBIGUOUS,
        )
        blockers = (
            resolution.root_blockers.get(identity, ())
            if diagnostic_class is DiagnosticClass.DOWNSTREAM
            else ()
        )
        if diagnostic_class is DiagnosticClass.DOWNSTREAM and not blockers:
            diagnostic_class = DiagnosticClass.AMBIGUOUS
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
        classified.append(updated)

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
        ValidationStatus.SKIPPED: frozenset({DiagnosticClass.SKIPPED, DiagnosticClass.NOISE}),
    }

    if diagnostic_class not in allowed[status]:
        raise _contract_error(
            f"{status.value} is incompatible with {diagnostic_class.value}",
            subject=_result_identity(result),
        )
    if diagnostic_class is DiagnosticClass.DIRECT:
        if not is_direct or blockers:
            raise _contract_error(
                "direct classification requires is_direct=true and no blockers",
                subject=_result_identity(result),
            )
    elif is_direct:
        raise _contract_error(
            "is_direct must be derived only from direct classification",
            subject=_result_identity(result),
        )
    if diagnostic_class is DiagnosticClass.DOWNSTREAM:
        if not blockers:
            raise _contract_error(
                "downstream classification requires at least one blocker",
                subject=_result_identity(result),
            )
    elif blockers:
        raise _contract_error(
            "blocked_by must be empty for non-downstream classifications",
            subject=_result_identity(result),
        )


def _build_result_indexes(
    results: Sequence[DiagnosticResult],
    *,
    strict: bool,
) -> _ResultIndexes:
    by_identity: dict[str, DiagnosticResult] = {}
    canonical_identity: dict[str, str] = {}
    aliases: dict[str, str] = {}

    for result in results:
        identity = _result_identity(result)
        normalized = _normalize_subject_identity(identity)
        previous = by_identity.get(normalized)
        if previous is not None and previous is not result:
            if strict:
                raise _contract_error(
                    "duplicate diagnostic result identity",
                    subject=identity,
                )
            continue

        by_identity[normalized] = result
        canonical_identity[normalized] = identity
        for alias in _result_aliases(result, identity):
            alias_key = _normalize_subject_identity(alias)
            previous_identity = aliases.get(alias_key)
            if previous_identity is not None and previous_identity != normalized:
                if strict:
                    raise _contract_error(
                        "diagnostic result alias resolves to multiple subjects",
                        subject=alias,
                    )
                continue
            aliases[alias_key] = normalized

    return _ResultIndexes(
        by_identity=by_identity,
        canonical_identity=canonical_identity,
        aliases=aliases,
    )


def _resolve_references(
    result: DiagnosticResult,
    references: Iterable[str],
    indexes: _ResultIndexes,
) -> _ReferenceResolution:
    identity = _result_identity(result)
    subject_key = _normalize_subject_identity(identity)
    resolved: dict[str, str] = {}
    unresolved: dict[str, str] = {}
    self_referenced = False

    for reference in references:
        reference_key = _normalize_subject_identity(reference)
        if reference_key == subject_key:
            self_referenced = True
            continue

        canonical_key = indexes.aliases.get(reference_key)
        if canonical_key is None:
            unresolved.setdefault(reference_key, reference_key)
            continue

        canonical = indexes.canonical_identity[canonical_key]
        resolved.setdefault(canonical_key, canonical)

    return _ReferenceResolution(
        resolved_subjects=tuple(resolved[key] for key in sorted(resolved)),
        unresolved_references=tuple(unresolved[key] for key in sorted(unresolved)),
        self_referenced=self_referenced,
        has_subject_local_evidence=_has_subject_local_evidence(result),
    )


def _causality_facts(
    result: DiagnosticResult,
    *,
    status: ValidationStatus,
    error_kind: ErrorKind,
    failed_blockers: tuple[str, ...],
    resolved: _ReferenceResolution,
    indexes: _ResultIndexes,
    retained_noise: bool,
) -> CausalityFacts:
    successful_reference = any(
        _validation_status(indexes.by_identity[_normalize_subject_identity(value)])
        in {ValidationStatus.OK, ValidationStatus.SKIPPED}
        for value in resolved.resolved_subjects
        if _normalize_subject_identity(value) in indexes.by_identity
    )

    return CausalityFacts(
        confirmed_blockers=failed_blockers,
        self_reference=resolved.self_referenced,
        local_location=resolved.has_subject_local_evidence,
        local_artifact_failure=_local_artifact_failure(result),
        unknown_external_reference=bool(resolved.unresolved_references),
        successful_external_reference=successful_reference,
        timeout=(error_kind is ErrorKind.TIMEOUT or _bool_attribute(result, "timed_out")),
        parser_failure=_bool_attribute(result, "parser_failure"),
        output_truncated=any(
            _bool_attribute(result, name)
            for name in ("output_truncated", "stdout_truncated", "stderr_truncated")
        ),
        combined_inputs=_bool_attribute(result, "combined_inputs"),
        policy_skip=(status is ValidationStatus.SKIPPED and not retained_noise),
        excluded_noise=(retained_noise and status is ValidationStatus.SKIPPED),
    )


def _result_identity(result: DiagnosticResult) -> str:
    for field_name in (
        "subject_id",
        "file_path",
        "scenario_id",
        "target_id",
        "script_path",
        "module_name",
        "name",
    ):
        value = getattr(result, field_name, None)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return _normalize_subject_identity(text)
    raise _contract_error(
        "result does not expose a stable subject identity",
        subject=None,
    )


def _result_aliases(
    result: DiagnosticResult,
    identity: str,
) -> tuple[str, ...]:
    aliases: list[str] = [identity]
    for field_name in (
        "subject_id",
        "file_path",
        "scenario_id",
        "target_id",
        "script_path",
        "module_name",
    ):
        value = getattr(result, field_name, None)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        try:
            aliases.append(_normalize_subject_identity(text))
        except (TypeError, ValueError):
            continue
    return _unique_strings(aliases)


def _collect_structured_references(
    result: DiagnosticResult,
) -> tuple[str, ...]:
    collected: list[object] = []
    for field_name in (
        "references",
        "dependencies",
        "dependency_ids",
        "imports",
        "prerequisites",
        "required_subjects",
        "referenced_subjects",
    ):
        value = getattr(result, field_name, None)
        if value is None:
            continue
        if isinstance(value, (str, bytes, Path)):
            collected.append(value)
            continue
        try:
            collected.extend(value)
        except TypeError:
            continue
    return _unique_strings(collected)


def _normalize_subject_identity(value: object) -> str:
    if isinstance(value, Path):
        value = value.as_posix()
    return normalize_blocker_identity(str(value).strip())


def _has_subject_local_evidence(result: DiagnosticResult) -> bool:
    for field_name in (
        "source_path",
        "diagnostic_path",
        "location_path",
        "evidence_path",
    ):
        if getattr(result, field_name, None) is not None:
            return True
    return False


def _local_artifact_failure(result: DiagnosticResult) -> bool:
    value = getattr(result, "artifact_checks_passed", None)
    if value is None:
        summary = getattr(result, "compile_summary", None)
        value = getattr(summary, "artifact_checks_passed", None)
    return value is False


def _bool_attribute(result: DiagnosticResult, field_name: str) -> bool:
    value = getattr(result, field_name, False)
    return value if type(value) is bool else False


def _references_for(
    result: DiagnosticResult,
    *,
    references_by_subject: Mapping[str, Iterable[str]] | None,
) -> tuple[str, ...]:
    identity = _result_identity(result)
    explicit: Iterable[str] = ()
    if references_by_subject is not None:
        explicit = (
            references_by_subject.get(identity)
            or references_by_subject.get(_normalize_subject_identity(identity))
            or ()
        )
    collected = _collect_structured_references(result)
    return _unique_strings((*collected, *tuple(explicit)))


def _failed_blocker_identities(
    subject_id: str,
    candidates: Iterable[str],
    indexes: _ResultIndexes,
) -> tuple[str, ...]:
    normalized_subject = _normalize_subject_identity(subject_id)
    blockers: set[str] = set()
    for candidate in candidates:
        normalized = _normalize_subject_identity(candidate)
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
        blockers.add(_result_identity(peer))
    return tuple(sorted(blockers, key=_normalize_subject_identity))


def _with_classification(
    result: _ResultT,
    *,
    diagnostic_class: DiagnosticClass,
    blocked_by: Iterable[str],
) -> _ResultT:
    normalized_blockers = tuple(
        sorted(
            {
                _normalize_subject_identity(value): value
                for value in blocked_by
                if value
                and _normalize_subject_identity(value)
                != _normalize_subject_identity(_result_identity(result))
            }.values(),
            key=_normalize_subject_identity,
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

    dataclass_field_names: set[str] = (
        {item.name for item in fields(result)} if is_dataclass(result) else set()
    )
    replacement_values: dict[str, object] = {}

    if "diagnostic_class" in dataclass_field_names:
        replacement_values["diagnostic_class"] = class_value
    if "blocked_by" in dataclass_field_names:
        replacement_values["blocked_by"] = blocker_value
    if "is_direct" in dataclass_field_names:
        replacement_values["is_direct"] = direct

    dataclass_parameters = getattr(type(result), "__dataclass_params__", None)
    replace_result = cast("Callable[..., _ResultT]", replace)
    if dataclass_parameters is not None and dataclass_parameters.frozen:
        return replace_result(result, **replacement_values)

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
            return replace_result(result, **replacement_values)
        raise _contract_error(
            "result does not expose writable classification-owned fields",
            subject=_result_identity(result),
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
            subject=_result_identity(result),
        ) from exc


def _error_kind(result: DiagnosticResult) -> ErrorKind:
    value = getattr(result, "error_kind", None)
    if value is None:
        compile_summary = getattr(result, "compile_summary", None)
        value = getattr(compile_summary, "error_kind", None)

    if isinstance(value, ErrorKind):
        return value

    status = _validation_status(result)
    if value is None and status in {
        ValidationStatus.OK,
        ValidationStatus.SKIPPED,
    }:
        return ErrorKind.OK
    if value is None:
        return ErrorKind.OTHER

    raw = value.value if isinstance(value, Enum) else value
    try:
        return ErrorKind(str(raw))
    except (TypeError, ValueError) as exc:
        raise _contract_error(
            f"unsupported error kind: {raw!r}",
            subject=_result_identity(result),
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
            subject=_result_identity(result),
        )
    return tuple(
        sorted(
            {
                _normalize_subject_identity(str(item)): str(item)
                for item in value
                if str(item).strip()
            }.values(),
            key=_normalize_subject_identity,
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
        normalized.setdefault(_normalize_subject_identity(text), text)
    return tuple(normalized[key] for key in sorted(normalized))


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
