from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import IntEnum, StrEnum, unique
from pathlib import Path, PurePath, PurePosixPath
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.statuses import DiagnosticClass, ValidationStatus

_EVIDENCE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^EV-(?:PROCESS|CONTRACT|FILE|SCENARIO|GOLD|SCAN|REGRESSION|TOOL|ARTIFACT|WARNING)-[0-9]{3,}$"
)
_SUBJECT_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[^\x00\r\n]{1,512}$")
_METADATA_KEY_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*$")
_MAX_DESCRIPTION_LENGTH: Final[int] = 2_000
_MAX_REASON_LENGTH: Final[int] = 1_000
_MAX_METADATA_ITEMS: Final[int] = 64
_MAX_METADATA_VALUE_LENGTH: Final[int] = 4_096
_MAX_CANDIDATES: Final[int] = 100_000

MetadataValue: TypeAlias = str | int | bool | None
EvidenceMetadata: TypeAlias = Mapping[str, MetadataValue]


@unique
class EvidenceDomain(StrEnum):
    PROCESS = "process"
    CONTRACT = "contract"
    FILE = "file"
    SCENARIO = "scenario"
    GOLD = "gold"
    SCAN = "scan"
    REGRESSION = "regression"
    TOOL = "tool"
    ARTIFACT = "artifact"
    WARNING = "warning"

    @property
    def id_token(self) -> str:
        return self.value.upper()


@unique
class EvidenceRepresentation(StrEnum):
    RAW = "raw"
    NORMALIZED = "normalized"
    DERIVED = "derived"


@unique
class EvidenceSourceType(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    SCAN_LOG = "scan_log"
    SCENARIO_STDOUT = "scenario_stdout"
    SCENARIO_STDERR = "scenario_stderr"
    NORMALIZED_SCENARIO_OUTPUT = "normalized_scenario_output"
    GOLD_DIFF = "gold_diff"
    DIAGNOSTIC_DETAIL = "diagnostic_detail"
    ARTIFACT_DETAIL = "artifact_detail"
    MANIFEST_DETAIL = "manifest_detail"
    CONTRACT_DETAIL = "contract_detail"
    REGRESSION_DETAIL = "regression_detail"
    TOOL_STDOUT = "tool_stdout"
    TOOL_STDERR = "tool_stderr"
    OTHER = "other"


@unique
class EvidenceAvailability(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    OMITTED = "omitted"


@unique
class EvidenceSelectionPriority(IntEnum):
    PROCESS_OR_CONTRACT_ERROR = 10
    DIRECT_FILE_FAILURE = 20
    REQUIRED_SCENARIO_FAILURE = 30
    AMBIGUOUS_FILE_FAILURE = 40
    GOLD_MISMATCH = 50
    DOWNSTREAM_FAILURE = 60
    OPTIONAL_SCENARIO_FAILURE = 70
    SUCCESSFUL_FILE_SCAN_FINDING = 80
    REGRESSION = 90
    NON_BLOCKING_WARNING = 100


_SOURCE_DEFAULT_LINES: Final[Mapping[EvidenceSourceType, int]] = MappingProxyType(
    {
        EvidenceSourceType.STDOUT: 20,
        EvidenceSourceType.STDERR: 20,
        EvidenceSourceType.SCAN_LOG: 20,
        EvidenceSourceType.SCENARIO_STDOUT: 40,
        EvidenceSourceType.SCENARIO_STDERR: 40,
        EvidenceSourceType.NORMALIZED_SCENARIO_OUTPUT: 40,
        EvidenceSourceType.GOLD_DIFF: 60,
        EvidenceSourceType.DIAGNOSTIC_DETAIL: 24,
        EvidenceSourceType.ARTIFACT_DETAIL: 20,
        EvidenceSourceType.MANIFEST_DETAIL: 20,
        EvidenceSourceType.CONTRACT_DETAIL: 24,
        EvidenceSourceType.REGRESSION_DETAIL: 40,
        EvidenceSourceType.TOOL_STDOUT: 20,
        EvidenceSourceType.TOOL_STDERR: 20,
        EvidenceSourceType.OTHER: 20,
    }
)


@dataclass(frozen=True, slots=True)
class EvidenceLimits:
    maximum_failing_file_entries: int = 20
    maximum_failing_scenario_entries: int = 20
    maximum_lines_per_stdout_excerpt: int = 20
    maximum_lines_per_stderr_excerpt: int = 20
    maximum_lines_per_fatal_block: int = 24
    maximum_lines_per_scenario_excerpt: int = 40
    maximum_lines_per_gold_diff_excerpt: int = 60
    maximum_total_inlined_evidence_lines: int = 500
    maximum_packet_size_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        for name in (
            "maximum_failing_file_entries",
            "maximum_failing_scenario_entries",
            "maximum_lines_per_stdout_excerpt",
            "maximum_lines_per_stderr_excerpt",
            "maximum_lines_per_fatal_block",
            "maximum_lines_per_scenario_excerpt",
            "maximum_lines_per_gold_diff_excerpt",
            "maximum_total_inlined_evidence_lines",
            "maximum_packet_size_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")

    def line_limit_for(self, source_type: EvidenceSourceType) -> int:
        if not isinstance(source_type, EvidenceSourceType):
            raise TypeError("source_type must be EvidenceSourceType")
        if source_type in (EvidenceSourceType.STDOUT, EvidenceSourceType.TOOL_STDOUT):
            return self.maximum_lines_per_stdout_excerpt
        if source_type in (EvidenceSourceType.STDERR, EvidenceSourceType.TOOL_STDERR):
            return self.maximum_lines_per_stderr_excerpt
        if source_type in (
            EvidenceSourceType.SCENARIO_STDOUT,
            EvidenceSourceType.SCENARIO_STDERR,
            EvidenceSourceType.NORMALIZED_SCENARIO_OUTPUT,
        ):
            return self.maximum_lines_per_scenario_excerpt
        if source_type is EvidenceSourceType.GOLD_DIFF:
            return self.maximum_lines_per_gold_diff_excerpt
        if source_type in (
            EvidenceSourceType.DIAGNOSTIC_DETAIL,
            EvidenceSourceType.CONTRACT_DETAIL,
        ):
            return self.maximum_lines_per_fatal_block
        return _SOURCE_DEFAULT_LINES[source_type]


DEFAULT_EVIDENCE_LIMITS: Final[EvidenceLimits] = EvidenceLimits()


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    domain: EvidenceDomain
    subject_id: str
    description: str
    source_path: Path
    source_type: EvidenceSourceType
    representation: EvidenceRepresentation
    priority: EvidenceSelectionPriority
    status: ValidationStatus | None = None
    diagnostic_class: DiagnosticClass | None = None
    required: bool = False
    release_significant: bool = False
    configured_order: int = 0
    source_start_line: int | None = None
    source_end_line: int | None = None
    selection_reason: str = ""
    preferred_line_limit: int | None = None
    estimated_total_lines: int | None = None
    availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE
    metadata: EvidenceMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.domain, EvidenceDomain):
            raise TypeError("domain must be EvidenceDomain")
        subject_id = _require_subject_id(self.subject_id)
        description = _require_text(
            self.description,
            field_name="description",
            maximum=_MAX_DESCRIPTION_LENGTH,
            allow_empty=False,
        )
        source_path = _coerce_path(self.source_path, field_name="source_path")
        if not isinstance(self.source_type, EvidenceSourceType):
            raise TypeError("source_type must be EvidenceSourceType")
        if not isinstance(self.representation, EvidenceRepresentation):
            raise TypeError("representation must be EvidenceRepresentation")
        if not isinstance(self.priority, EvidenceSelectionPriority):
            raise TypeError("priority must be EvidenceSelectionPriority")
        if self.status is not None and not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be ValidationStatus or None")
        if self.diagnostic_class is not None and not isinstance(
            self.diagnostic_class, DiagnosticClass
        ):
            raise TypeError("diagnostic_class must be DiagnosticClass or None")
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if type(self.release_significant) is not bool:
            raise TypeError("release_significant must be a boolean")
        if isinstance(self.configured_order, bool) or not isinstance(
            self.configured_order, int
        ):
            raise TypeError("configured_order must be an integer")
        if self.configured_order < 0:
            raise ValueError("configured_order must be non-negative")
        _validate_line_range(self.source_start_line, self.source_end_line)
        selection_reason = _require_text(
            self.selection_reason,
            field_name="selection_reason",
            maximum=_MAX_REASON_LENGTH,
            allow_empty=True,
        )
        _validate_optional_positive_int(
            self.preferred_line_limit,
            field_name="preferred_line_limit",
        )
        _validate_optional_non_negative_int(
            self.estimated_total_lines,
            field_name="estimated_total_lines",
        )
        if not isinstance(self.availability, EvidenceAvailability):
            raise TypeError("availability must be EvidenceAvailability")
        metadata = _freeze_metadata(self.metadata)
        object.__setattr__(self, "subject_id", subject_id)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source_path", source_path)
        object.__setattr__(self, "selection_reason", selection_reason)
        object.__setattr__(self, "metadata", metadata)

    @property
    def identity_key(self) -> tuple[object, ...]:
        return (
            self.domain,
            self.subject_id.casefold(),
            _portable_path_key(self.source_path),
            self.source_type,
            self.representation,
            self.source_start_line,
            self.source_end_line,
        )

    def requested_line_limit(
        self,
        limits: EvidenceLimits = DEFAULT_EVIDENCE_LIMITS,
    ) -> int:
        if self.preferred_line_limit is not None:
            return min(self.preferred_line_limit, limits.line_limit_for(self.source_type))
        return limits.line_limit_for(self.source_type)


@dataclass(frozen=True, slots=True)
class PacketEvidenceItem:
    evidence_id: str
    domain: EvidenceDomain
    subject_id: str
    description: str
    source_path: Path
    source_type: EvidenceSourceType
    representation: EvidenceRepresentation
    priority: EvidenceSelectionPriority
    status: ValidationStatus | None
    diagnostic_class: DiagnosticClass | None
    required: bool
    release_significant: bool
    configured_order: int
    source_start_line: int | None
    source_end_line: int | None
    selection_reason: str
    line_limit: int
    estimated_total_lines: int | None
    availability: EvidenceAvailability
    metadata: EvidenceMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or _EVIDENCE_ID_RE.fullmatch(
            self.evidence_id
        ) is None:
            raise ValueError(f"invalid evidence_id {self.evidence_id!r}")
        candidate = EvidenceCandidate(
            domain=self.domain,
            subject_id=self.subject_id,
            description=self.description,
            source_path=self.source_path,
            source_type=self.source_type,
            representation=self.representation,
            priority=self.priority,
            status=self.status,
            diagnostic_class=self.diagnostic_class,
            required=self.required,
            release_significant=self.release_significant,
            configured_order=self.configured_order,
            source_start_line=self.source_start_line,
            source_end_line=self.source_end_line,
            selection_reason=self.selection_reason,
            preferred_line_limit=self.line_limit,
            estimated_total_lines=self.estimated_total_lines,
            availability=self.availability,
            metadata=self.metadata,
        )
        if not self.evidence_id.startswith(f"EV-{candidate.domain.id_token}-"):
            raise ValueError("evidence_id domain does not match domain")
        if isinstance(self.line_limit, bool) or not isinstance(self.line_limit, int):
            raise TypeError("line_limit must be an integer")
        if self.line_limit < 1:
            raise ValueError("line_limit must be positive")
        object.__setattr__(self, "subject_id", candidate.subject_id)
        object.__setattr__(self, "description", candidate.description)
        object.__setattr__(self, "source_path", candidate.source_path)
        object.__setattr__(self, "selection_reason", candidate.selection_reason)
        object.__setattr__(self, "metadata", candidate.metadata)

    @classmethod
    def from_candidate(
        cls,
        candidate: EvidenceCandidate,
        *,
        evidence_id: str,
        line_limit: int,
    ) -> PacketEvidenceItem:
        if not isinstance(candidate, EvidenceCandidate):
            raise TypeError("candidate must be EvidenceCandidate")
        return cls(
            evidence_id=evidence_id,
            domain=candidate.domain,
            subject_id=candidate.subject_id,
            description=candidate.description,
            source_path=candidate.source_path,
            source_type=candidate.source_type,
            representation=candidate.representation,
            priority=candidate.priority,
            status=candidate.status,
            diagnostic_class=candidate.diagnostic_class,
            required=candidate.required,
            release_significant=candidate.release_significant,
            configured_order=candidate.configured_order,
            source_start_line=candidate.source_start_line,
            source_end_line=candidate.source_end_line,
            selection_reason=candidate.selection_reason,
            line_limit=line_limit,
            estimated_total_lines=candidate.estimated_total_lines,
            availability=candidate.availability,
            metadata=candidate.metadata,
        )

    @property
    def identity_key(self) -> tuple[object, ...]:
        return (
            self.domain,
            self.subject_id.casefold(),
            _portable_path_key(self.source_path),
            self.source_type,
            self.representation,
            self.source_start_line,
            self.source_end_line,
        )

    @property
    def is_truncated_by_plan(self) -> bool:
        return (
            self.estimated_total_lines is not None
            and self.estimated_total_lines > self.line_limit
        )


@dataclass(frozen=True, slots=True)
class OmittedEvidence:
    candidate: EvidenceCandidate
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, EvidenceCandidate):
            raise TypeError("candidate must be EvidenceCandidate")
        reason = _require_text(
            self.reason,
            field_name="reason",
            maximum=_MAX_REASON_LENGTH,
            allow_empty=False,
        )
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class PacketEvidenceCatalog:
    items: tuple[PacketEvidenceItem, ...]
    omitted: tuple[OmittedEvidence, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        items = tuple(self.items)
        omitted = tuple(self.omitted)
        warnings = tuple(self.warnings)
        if any(not isinstance(item, PacketEvidenceItem) for item in items):
            raise TypeError("items must contain PacketEvidenceItem objects")
        if any(not isinstance(item, OmittedEvidence) for item in omitted):
            raise TypeError("omitted must contain OmittedEvidence objects")
        if len({item.evidence_id for item in items}) != len(items):
            raise ValueError("evidence IDs must be unique")
        if len({item.identity_key for item in items}) != len(items):
            raise ValueError("catalog items must not duplicate evidence identity")
        normalized_warnings = tuple(
            _require_text(
                warning,
                field_name="warning",
                maximum=_MAX_DESCRIPTION_LENGTH,
                allow_empty=False,
            )
            for warning in warnings
        )
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "omitted", omitted)
        object.__setattr__(self, "warnings", normalized_warnings)

    def by_id(self) -> Mapping[str, PacketEvidenceItem]:
        return MappingProxyType({item.evidence_id: item for item in self.items})

    def for_subject(self, subject_id: str) -> tuple[PacketEvidenceItem, ...]:
        canonical = _require_subject_id(subject_id)
        return tuple(item for item in self.items if item.subject_id == canonical)

    def for_domain(self, domain: EvidenceDomain) -> tuple[PacketEvidenceItem, ...]:
        if not isinstance(domain, EvidenceDomain):
            raise TypeError("domain must be EvidenceDomain")
        return tuple(item for item in self.items if item.domain is domain)

    @property
    def omitted_count(self) -> int:
        return len(self.omitted)

    @property
    def release_significant_omissions(self) -> tuple[OmittedEvidence, ...]:
        return tuple(item for item in self.omitted if item.candidate.release_significant)


class EvidenceIdAllocator:
    __slots__ = ("_counts",)

    def __init__(self) -> None:
        self._counts: dict[EvidenceDomain, int] = defaultdict(int)

    def next(self, domain: EvidenceDomain) -> str:
        if not isinstance(domain, EvidenceDomain):
            raise TypeError("domain must be EvidenceDomain")
        self._counts[domain] += 1
        return f"EV-{domain.id_token}-{self._counts[domain]:03d}"


def build_evidence_catalog(
    candidates: Iterable[EvidenceCandidate],
    *,
    limits: EvidenceLimits = DEFAULT_EVIDENCE_LIMITS,
    allowed_roots: Sequence[Path] = (),
) -> PacketEvidenceCatalog:
    if not isinstance(limits, EvidenceLimits):
        raise TypeError("limits must be EvidenceLimits")
    prepared = _prepare_candidates(candidates)
    roots = _prepare_roots(allowed_roots)
    validated: list[EvidenceCandidate] = []
    warnings: list[str] = []
    omitted: list[OmittedEvidence] = []

    for candidate in prepared:
        path_error = evidence_path_error(candidate.source_path, allowed_roots=roots)
        if path_error is not None:
            if candidate.release_significant or candidate.required:
                candidate = replace(
                    candidate,
                    availability=EvidenceAvailability.UNREADABLE,
                    metadata={**candidate.metadata, "path_error": path_error},
                )
                warnings.append(
                    f"Required evidence for {candidate.subject_id!r} has an unsafe or invalid path: {path_error}"
                )
            else:
                omitted.append(OmittedEvidence(candidate, path_error))
                continue
        validated.append(candidate)

    deduplicated, duplicates = _deduplicate_candidates(validated)
    omitted.extend(duplicates)
    ordered = sorted(deduplicated, key=evidence_candidate_sort_key)

    selected: list[EvidenceCandidate] = []
    file_subjects: set[str] = set()
    scenario_subjects: set[str] = set()

    for candidate in ordered:
        if candidate.domain is EvidenceDomain.FILE:
            is_new_subject = candidate.subject_id not in file_subjects
            if is_new_subject and len(file_subjects) >= limits.maximum_failing_file_entries:
                omitted.append(
                    OmittedEvidence(candidate, "maximum failing file entry limit reached")
                )
                continue
            file_subjects.add(candidate.subject_id)
        elif candidate.domain in (EvidenceDomain.SCENARIO, EvidenceDomain.GOLD):
            is_new_subject = candidate.subject_id not in scenario_subjects
            if (
                is_new_subject
                and len(scenario_subjects) >= limits.maximum_failing_scenario_entries
            ):
                omitted.append(
                    OmittedEvidence(candidate, "maximum failing scenario entry limit reached")
                )
                continue
            scenario_subjects.add(candidate.subject_id)
        selected.append(candidate)

    allocator = EvidenceIdAllocator()
    items: list[PacketEvidenceItem] = []
    remaining_lines = limits.maximum_total_inlined_evidence_lines

    for candidate in selected:
        requested = candidate.requested_line_limit(limits)
        if remaining_lines < 1:
            omitted.append(
                OmittedEvidence(candidate, "maximum total inlined evidence line limit reached")
            )
            continue
        line_limit = min(requested, remaining_lines)
        remaining_lines -= line_limit
        items.append(
            PacketEvidenceItem.from_candidate(
                candidate,
                evidence_id=allocator.next(candidate.domain),
                line_limit=line_limit,
            )
        )

    if any(item.candidate.release_significant for item in omitted):
        warnings.append(
            "One or more release-significant evidence items were omitted; the packet must disclose the omission and reference the complete structured source."
        )

    return PacketEvidenceCatalog(
        items=tuple(items),
        omitted=tuple(omitted),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def evidence_candidate_sort_key(candidate: EvidenceCandidate) -> tuple[object, ...]:
    if not isinstance(candidate, EvidenceCandidate):
        raise TypeError("candidate must be EvidenceCandidate")
    status_rank = {
        ValidationStatus.ERROR: 0,
        ValidationStatus.FAIL: 1,
        ValidationStatus.SKIPPED: 2,
        ValidationStatus.OK: 3,
        None: 4,
    }[candidate.status]
    class_rank = {
        DiagnosticClass.DIRECT: 0,
        DiagnosticClass.AMBIGUOUS: 1,
        DiagnosticClass.DOWNSTREAM: 2,
        DiagnosticClass.SKIPPED: 3,
        DiagnosticClass.NOISE: 4,
        DiagnosticClass.OK: 5,
        None: 6,
    }[candidate.diagnostic_class]
    return (
        int(candidate.priority),
        status_rank,
        class_rank,
        0 if candidate.required else 1,
        candidate.configured_order,
        candidate.subject_id.casefold(),
        candidate.source_type.value,
        _portable_path_key(candidate.source_path),
        candidate.source_start_line or 0,
        candidate.source_end_line or 0,
        candidate.description.casefold(),
    )


def evidence_path_error(
    path: Path,
    *,
    allowed_roots: Sequence[Path] = (),
) -> str | None:
    candidate = _coerce_path(path, field_name="path")
    if _contains_parent_traversal(candidate):
        return "evidence path contains parent traversal"
    roots = _prepare_roots(allowed_roots)
    if candidate.is_absolute() and roots:
        canonical = _lexical_absolute(candidate)
        if not any(_is_relative_to(canonical, root) for root in roots):
            return "absolute evidence path is outside approved roots"
    if not candidate.is_absolute() and candidate == Path("."):
        return "evidence path must identify a file"
    return None


def ensure_evidence_path(
    path: Path,
    *,
    allowed_roots: Sequence[Path] = (),
) -> Path:
    candidate = _coerce_path(path, field_name="path")
    error = evidence_path_error(candidate, allowed_roots=allowed_roots)
    if error is not None:
        raise ValueError(error)
    return candidate


def portable_evidence_path(path: Path, *, root: Path | None = None) -> PurePosixPath:
    candidate = _coerce_path(path, field_name="path")
    if root is not None:
        canonical_root = _lexical_absolute(_coerce_path(root, field_name="root"))
        canonical_path = _lexical_absolute(candidate)
        if not _is_relative_to(canonical_path, canonical_root):
            raise ValueError("path is outside root")
        candidate = canonical_path.relative_to(canonical_root)
    elif candidate.is_absolute():
        raise ValueError("absolute paths require an explicit root")
    if _contains_parent_traversal(candidate):
        raise ValueError("path contains parent traversal")
    return PurePosixPath(*candidate.parts)


def evidence_ids_for_subject(
    catalog: PacketEvidenceCatalog,
    subject_id: str,
) -> tuple[str, ...]:
    if not isinstance(catalog, PacketEvidenceCatalog):
        raise TypeError("catalog must be PacketEvidenceCatalog")
    return tuple(item.evidence_id for item in catalog.for_subject(subject_id))


def evidence_index_rows(
    catalog: PacketEvidenceCatalog,
    *,
    root: Path | None = None,
) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(catalog, PacketEvidenceCatalog):
        raise TypeError("catalog must be PacketEvidenceCatalog")
    rows: list[tuple[str, str, str]] = []
    for item in catalog.items:
        if item.source_path.is_absolute():
            if root is None:
                path_text = str(item.source_path)
            else:
                path_text = portable_evidence_path(item.source_path, root=root).as_posix()
        else:
            path_text = portable_evidence_path(item.source_path).as_posix()
        rows.append((item.evidence_id, item.description, path_text))
    return tuple(rows)


def _prepare_candidates(
    candidates: Iterable[EvidenceCandidate],
) -> tuple[EvidenceCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise TypeError("candidates must be an iterable of EvidenceCandidate")
    prepared = tuple(candidates)
    if len(prepared) > _MAX_CANDIDATES:
        raise ValueError("candidate count exceeds the supported limit")
    if any(not isinstance(candidate, EvidenceCandidate) for candidate in prepared):
        raise TypeError("candidates must contain EvidenceCandidate objects")
    return prepared


def _deduplicate_candidates(
    candidates: Sequence[EvidenceCandidate],
) -> tuple[tuple[EvidenceCandidate, ...], tuple[OmittedEvidence, ...]]:
    best: dict[tuple[object, ...], EvidenceCandidate] = {}
    omitted: list[OmittedEvidence] = []
    for candidate in candidates:
        current = best.get(candidate.identity_key)
        if current is None:
            best[candidate.identity_key] = candidate
            continue
        if evidence_candidate_sort_key(candidate) < evidence_candidate_sort_key(current):
            best[candidate.identity_key] = candidate
            omitted.append(OmittedEvidence(current, "duplicate evidence identity"))
        else:
            omitted.append(OmittedEvidence(candidate, "duplicate evidence identity"))
    return tuple(best.values()), tuple(omitted)


def _prepare_roots(values: Sequence[Path]) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError("allowed_roots must be a sequence of Path objects")
    roots: list[Path] = []
    for value in values:
        root = _coerce_path(value, field_name="allowed root")
        if not root.is_absolute():
            raise ValueError("allowed roots must be absolute")
        canonical = _lexical_absolute(root)
        if canonical not in roots:
            roots.append(canonical)
    return tuple(roots)


def _lexical_absolute(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    parts: list[str] = []
    anchor = path.anchor
    for part in path.parts:
        if part in (anchor, "", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return Path(anchor, *parts)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _contains_parent_traversal(path: PurePath) -> bool:
    return ".." in path.parts


def _portable_path_key(path: Path) -> str:
    return PurePosixPath(*path.parts).as_posix().casefold()


def _require_subject_id(value: object) -> str:
    text = _require_text(
        value,
        field_name="subject_id",
        maximum=512,
        allow_empty=False,
    )
    if _SUBJECT_ID_RE.fullmatch(text) is None:
        raise ValueError(f"invalid subject_id {text!r}")
    return text


def _require_text(
    value: object,
    *,
    field_name: str,
    maximum: int,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > maximum:
        raise ValueError(f"{field_name} exceeds the supported length")
    return value


def _coerce_path(value: object, *, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _validate_line_range(start: int | None, end: int | None) -> None:
    _validate_optional_positive_int(start, field_name="source_start_line")
    _validate_optional_positive_int(end, field_name="source_end_line")
    if end is not None and start is None:
        raise ValueError("source_end_line requires source_start_line")
    if start is not None and end is not None and end < start:
        raise ValueError("source_end_line must not precede source_start_line")


def _validate_optional_positive_int(value: int | None, *, field_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer or None")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")


def _validate_optional_non_negative_int(
    value: int | None,
    *,
    field_name: str,
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer or None")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _freeze_metadata(values: EvidenceMetadata) -> EvidenceMetadata:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")
    if len(values) > _MAX_METADATA_ITEMS:
        raise ValueError("metadata exceeds the supported item limit")
    copied: dict[str, MetadataValue] = {}
    for key, value in values.items():
        if not isinstance(key, str) or _METADATA_KEY_RE.fullmatch(key) is None:
            raise ValueError(f"invalid metadata key {key!r}")
        if type(value) not in (str, int, bool, type(None)):
            raise TypeError(f"metadata value for {key!r} has unsupported type")
        if isinstance(value, str):
            value = _require_text(
                value,
                field_name=f"metadata[{key!r}]",
                maximum=_MAX_METADATA_VALUE_LENGTH,
                allow_empty=True,
            )
        copied[key] = value
    return MappingProxyType(copied)



__all__ = (
    "DEFAULT_EVIDENCE_LIMITS",
    "EvidenceAvailability",
    "EvidenceCandidate",
    "EvidenceDomain",
    "EvidenceIdAllocator",
    "EvidenceLimits",
    "EvidenceMetadata",
    "EvidenceRepresentation",
    "EvidenceSelectionPriority",
    "EvidenceSourceType",
    "MetadataValue",
    "OmittedEvidence",
    "PacketEvidenceCatalog",
    "PacketEvidenceItem",
    "build_evidence_catalog",
    "ensure_evidence_path",
    "evidence_candidate_sort_key",
    "evidence_ids_for_subject",
    "evidence_index_rows",
    "evidence_path_error",
    "portable_evidence_path",
)
