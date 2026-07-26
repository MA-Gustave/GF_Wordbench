"""Deterministic construction and aggregation of diagnostic findings."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from enum import Enum
from types import MappingProxyType
from typing import Final

from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import DiagnosticClass, ErrorKind

from .models import EvidenceRef, Finding

_FINDING_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^finding-[a-f0-9]{24}$"
)
_RULE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$"
)
_KIND_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$"
)
_SEVERITIES: Final[tuple[str, ...]] = (
    "fatal",
    "error",
    "warning",
    "info",
)
_SEVERITY_RANK: Final[Mapping[str, int]] = MappingProxyType(
    {value: index for index, value in enumerate(_SEVERITIES)}
)
_MAX_TEXT: Final[int] = 4_096
_MAX_EXCERPT: Final[int] = 16_384
_MAX_METADATA_ITEMS: Final[int] = 64
_MAX_FINDINGS: Final[int] = 100_000


def build_finding(
    *,
    severity: str,
    kind: str,
    message: str,
    target: str,
    evidence_refs: Iterable[EvidenceRef],
    producer: ProducerInfo,
    diagnostic_class: DiagnosticClass | None = None,
    error_kind: ErrorKind | None = None,
    rule_id: str | None = None,
    blocking: bool = False,
    metadata: Mapping[str, str] | None = None,
    finding_id: str | None = None,
) -> Finding:
    """Build one immutable finding with a stable content-derived identity."""

    normalized_severity = _normalize_severity(severity)
    normalized_kind = _normalize_kind(kind)
    normalized_message = _require_text(
        message,
        field="message",
        max_length=_MAX_TEXT,
    )
    normalized_target = _require_text(
        target,
        field="target",
        max_length=_MAX_TEXT,
    )
    normalized_evidence = _normalize_evidence_refs(evidence_refs)
    normalized_rule_id = _normalize_rule_id(rule_id)
    normalized_metadata = _normalize_metadata(metadata)

    if not isinstance(producer, ProducerInfo):
        raise TypeError("producer must be ProducerInfo")
    if diagnostic_class is not None and not isinstance(
        diagnostic_class,
        DiagnosticClass,
    ):
        raise TypeError("diagnostic_class must be DiagnosticClass or None")
    if error_kind is not None and not isinstance(error_kind, ErrorKind):
        raise TypeError("error_kind must be ErrorKind or None")
    if type(blocking) is not bool:
        raise TypeError("blocking must be a boolean")

    if normalized_kind == "static_scan":
        if error_kind not in (None, ErrorKind.OK):
            raise ValueError(
                "static scan findings must not claim a GF error kind"
            )
        if diagnostic_class not in (None, DiagnosticClass.OK, DiagnosticClass.NOISE):
            raise ValueError(
                "static scan findings must not claim direct or downstream causality"
            )

    canonical_id = (
        _normalize_finding_id(finding_id)
        if finding_id is not None
        else _derive_finding_id(
            severity=normalized_severity,
            kind=normalized_kind,
            message=normalized_message,
            target=normalized_target,
            evidence_refs=normalized_evidence,
            producer=producer,
            diagnostic_class=diagnostic_class,
            error_kind=error_kind,
            rule_id=normalized_rule_id,
            blocking=blocking,
            metadata=normalized_metadata,
        )
    )

    return Finding(
        finding_id=canonical_id,
        severity=normalized_severity,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
        kind=normalized_kind,
        message=normalized_message,
        target=normalized_target,
        evidence_refs=normalized_evidence,
        producer=producer,
        rule_id=normalized_rule_id,
        blocking=blocking,
        metadata=normalized_metadata,
    )


def rebuild_finding(
    finding: Finding,
    *,
    severity: str | None = None,
    message: str | None = None,
    blocking: bool | None = None,
    metadata: Mapping[str, str] | None = None,
) -> Finding:
    """Return a validated replacement with a newly derived identity."""

    _require_finding(finding)
    return build_finding(
        severity=finding.severity if severity is None else severity,
        kind=finding.kind,
        message=finding.message if message is None else message,
        target=finding.target,
        evidence_refs=finding.evidence_refs,
        producer=finding.producer,
        diagnostic_class=finding.diagnostic_class,
        error_kind=finding.error_kind,
        rule_id=finding.rule_id,
        blocking=finding.blocking if blocking is None else blocking,
        metadata=finding.metadata if metadata is None else metadata,
    )


def finding_signature(finding: Finding) -> str:
    """Return the stable semantic signature used for deduplication."""

    _require_finding(finding)
    digest = hashlib.sha256()
    for part in _signature_parts(finding):
        encoded = part.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def validate_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Validate finding identities and return the original deterministic order."""

    prepared = _prepare_findings(findings)
    seen_ids: set[str] = set()
    for finding in prepared:
        _normalize_finding_id(finding.finding_id)
        if finding.finding_id in seen_ids:
            raise ValueError(f"duplicate finding ID {finding.finding_id!r}")
        seen_ids.add(finding.finding_id)
    return prepared


def sort_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Sort findings by severity, target, location, kind, and identity."""

    prepared = _prepare_findings(findings)
    return tuple(sorted(prepared, key=_finding_sort_key))


def deduplicate_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Remove semantic duplicates while preserving the strongest evidence."""

    prepared = _prepare_findings(findings)
    selected: dict[str, Finding] = {}
    order: list[str] = []

    for finding in prepared:
        signature = finding_signature(finding)
        existing = selected.get(signature)
        if existing is None:
            selected[signature] = finding
            order.append(signature)
            continue
        selected[signature] = _merge_duplicate_pair(existing, finding)

    return tuple(selected[signature] for signature in order)


def merge_findings(*groups: Iterable[Finding]) -> tuple[Finding, ...]:
    """Merge, deduplicate, and canonically order several finding groups."""

    flattened: list[Finding] = []
    for group in groups:
        flattened.extend(_prepare_findings(group))
        if len(flattened) > _MAX_FINDINGS:
            raise ValueError("finding count exceeds the supported limit")
    return sort_findings(deduplicate_findings(flattened))


def blocking_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Return canonically ordered findings that are explicitly blocking."""

    return tuple(
        finding
        for finding in sort_findings(findings)
        if finding.blocking
    )


def findings_by_target(
    findings: Iterable[Finding],
) -> Mapping[str, tuple[Finding, ...]]:
    """Group findings by stable target identity in canonical target order."""

    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in sort_findings(findings):
        grouped[finding.target].append(finding)
    return MappingProxyType(
        {
            target: tuple(grouped[target])
            for target in sorted(grouped, key=lambda value: (value.casefold(), value))
        }
    )


def finding_counts(
    findings: Iterable[Finding],
) -> Mapping[str, int]:
    """Return deterministic counts by severity and blocking policy."""

    prepared = _prepare_findings(findings)
    values = {severity: 0 for severity in _SEVERITIES}
    values["blocking"] = 0
    values["total"] = len(prepared)
    for finding in prepared:
        severity = _normalize_severity(finding.severity)
        values[severity] += 1
        if finding.blocking:
            values["blocking"] += 1
    return MappingProxyType(values)


def has_blocking_findings(findings: Iterable[Finding]) -> bool:
    """Return whether at least one finding is explicitly release-blocking."""

    return any(finding.blocking for finding in _prepare_findings(findings))


def _derive_finding_id(
    *,
    severity: str,
    kind: str,
    message: str,
    target: str,
    evidence_refs: tuple[EvidenceRef, ...],
    producer: ProducerInfo,
    diagnostic_class: DiagnosticClass | None,
    error_kind: ErrorKind | None,
    rule_id: str | None,
    blocking: bool,
    metadata: Mapping[str, str],
) -> str:
    temporary = Finding(
        finding_id="finding-" + ("0" * 24),
        severity=severity,
        diagnostic_class=diagnostic_class,
        error_kind=error_kind,
        kind=kind,
        message=message,
        target=target,
        evidence_refs=evidence_refs,
        producer=producer,
        rule_id=rule_id,
        blocking=blocking,
        metadata=metadata,
    )
    return f"finding-{finding_signature(temporary)[:24]}"


def _signature_parts(finding: Finding) -> tuple[str, ...]:
    evidence_parts: list[str] = []
    for reference in finding.evidence_refs:
        evidence_parts.extend(_evidence_signature_parts(reference))
    metadata_parts = [
        f"{key}={value}"
        for key, value in sorted(
            finding.metadata.items(),
            key=lambda item: (item[0].casefold(), item[0]),
        )
    ]
    return (
        finding.severity,
        finding.kind,
        finding.message,
        finding.target,
        _enum_value(finding.diagnostic_class),
        _enum_value(finding.error_kind),
        finding.rule_id or "",
        "1" if finding.blocking else "0",
        finding.producer.name,
        finding.producer.version,
        *evidence_parts,
        *metadata_parts,
    )


def _evidence_signature_parts(reference: EvidenceRef) -> tuple[str, ...]:
    return (
        _string_attribute(reference, "role"),
        _string_attribute(reference, "path"),
        _optional_string_attribute(reference, "stream"),
        _optional_int_attribute(reference, "line"),
        _optional_int_attribute(reference, "column"),
        _optional_string_attribute(reference, "excerpt"),
    )


def _merge_duplicate_pair(left: Finding, right: Finding) -> Finding:
    evidence = _normalize_evidence_refs(
        (*left.evidence_refs, *right.evidence_refs)
    )
    metadata = dict(left.metadata)
    for key, value in right.metadata.items():
        metadata.setdefault(key, value)

    strongest = min(
        (left, right),
        key=lambda finding: (
            _SEVERITY_RANK[_normalize_severity(finding.severity)],
            0 if finding.blocking else 1,
            finding.finding_id,
        ),
    )
    return replace(
        strongest,
        evidence_refs=evidence,
        metadata=MappingProxyType(metadata),
    )


def _finding_sort_key(finding: Finding) -> tuple[object, ...]:
    evidence_key = tuple(
        _evidence_sort_key(reference)
        for reference in finding.evidence_refs
    )
    return (
        _SEVERITY_RANK[_normalize_severity(finding.severity)],
        0 if finding.blocking else 1,
        finding.target.casefold(),
        finding.target,
        evidence_key,
        finding.kind,
        finding.rule_id or "",
        finding.message.casefold(),
        finding.message,
        finding.finding_id,
    )


def _evidence_sort_key(reference: EvidenceRef) -> tuple[object, ...]:
    return (
        _string_attribute(reference, "path").casefold(),
        _string_attribute(reference, "path"),
        _optional_int_raw(reference, "line"),
        _optional_int_raw(reference, "column"),
        _string_attribute(reference, "role"),
        _optional_string_attribute(reference, "stream"),
    )


def _normalize_evidence_refs(
    references: Iterable[EvidenceRef],
) -> tuple[EvidenceRef, ...]:
    if isinstance(references, (str, bytes)):
        raise TypeError("evidence_refs must be an iterable of EvidenceRef")
    prepared = tuple(references)
    unique: dict[tuple[str, ...], EvidenceRef] = {}
    for reference in prepared:
        if not isinstance(reference, EvidenceRef):
            raise TypeError("evidence_refs must contain EvidenceRef objects")
        key = _evidence_signature_parts(reference)
        unique.setdefault(key, reference)
    return tuple(sorted(unique.values(), key=_evidence_sort_key))


def _normalize_metadata(
    metadata: Mapping[str, str] | None,
) -> Mapping[str, str]:
    if metadata is None:
        return MappingProxyType({})
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")
    if len(metadata) > _MAX_METADATA_ITEMS:
        raise ValueError("metadata exceeds the supported item limit")
    normalized: dict[str, str] = {}
    for key, value in metadata.items():
        normalized_key = _normalize_kind(key)
        normalized_value = _require_text(
            value,
            field=f"metadata[{key!r}]",
            max_length=_MAX_TEXT,
        )
        normalized[normalized_key] = normalized_value
    return MappingProxyType(
        dict(
            sorted(
                normalized.items(),
                key=lambda item: (item[0].casefold(), item[0]),
            )
        )
    )


def _prepare_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    if isinstance(findings, (str, bytes)):
        raise TypeError("findings must be an iterable of Finding objects")
    prepared = tuple(findings)
    if len(prepared) > _MAX_FINDINGS:
        raise ValueError("finding count exceeds the supported limit")
    for finding in prepared:
        _require_finding(finding)
    return prepared


def _require_finding(value: object) -> Finding:
    if not isinstance(value, Finding):
        raise TypeError("value must be a Finding")
    _normalize_severity(value.severity)
    _normalize_kind(value.kind)
    _normalize_finding_id(value.finding_id)
    return value


def _normalize_severity(value: object) -> str:
    text = _require_text(value, field="severity", max_length=16).lower()
    if text not in _SEVERITY_RANK:
        expected = ", ".join(_SEVERITIES)
        raise ValueError(f"unsupported finding severity {text!r}; expected {expected}")
    return text


def _normalize_kind(value: object) -> str:
    text = _require_text(value, field="kind", max_length=128)
    if not text.isascii() or _KIND_RE.fullmatch(text) is None:
        raise ValueError(f"invalid finding kind {text!r}")
    return text


def _normalize_rule_id(value: str | None) -> str | None:
    if value is None:
        return None
    text = _require_text(value, field="rule_id", max_length=128)
    if not text.isascii() or _RULE_ID_RE.fullmatch(text) is None:
        raise ValueError(f"invalid rule_id {text!r}")
    return text


def _normalize_finding_id(value: object) -> str:
    text = _require_text(value, field="finding_id", max_length=32)
    if _FINDING_ID_RE.fullmatch(text) is None:
        raise ValueError(
            f"invalid finding_id {text!r}; expected finding- plus 24 lowercase hex digits"
        )
    return text


def _require_text(
    value: object,
    *,
    field: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL characters")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds the supported length limit")
    return value


def _enum_value(value: Enum | None) -> str:
    if value is None:
        return ""
    raw = value.value
    if not isinstance(raw, str):
        raise TypeError("canonical enum values must be strings")
    return raw


def _string_attribute(value: object, name: str) -> str:
    attribute = getattr(value, name)
    return _require_text(
        attribute,
        field=f"EvidenceRef.{name}",
        max_length=_MAX_EXCERPT if name == "excerpt" else _MAX_TEXT,
    )


def _optional_string_attribute(value: object, name: str) -> str:
    attribute = getattr(value, name)
    if attribute is None:
        return ""
    if not isinstance(attribute, str):
        raise TypeError(f"EvidenceRef.{name} must be a string or None")
    if "\x00" in attribute:
        raise ValueError(f"EvidenceRef.{name} must not contain NUL characters")
    maximum = _MAX_EXCERPT if name == "excerpt" else _MAX_TEXT
    if len(attribute) > maximum:
        raise ValueError(f"EvidenceRef.{name} exceeds the supported length limit")
    return attribute


def _optional_int_attribute(value: object, name: str) -> str:
    attribute = _optional_int_raw(value, name)
    return "" if attribute is None else str(attribute)


def _optional_int_raw(value: object, name: str) -> int | None:
    attribute = getattr(value, name)
    if attribute is None:
        return None
    if type(attribute) is not int:
        raise TypeError(f"EvidenceRef.{name} must be an integer or None")
    if attribute < 1:
        raise ValueError(f"EvidenceRef.{name} must be positive")
    return attribute


__all__ = (
    "blocking_findings",
    "build_finding",
    "deduplicate_findings",
    "finding_counts",
    "finding_signature",
    "findings_by_target",
    "has_blocking_findings",
    "merge_findings",
    "rebuild_finding",
    "sort_findings",
    "validate_findings",
)
