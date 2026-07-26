"""Deterministic causal-relationship utilities for GF Wordbench diagnostics."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.kernel.statuses import DiagnosticClass, ValidationStatus

BlockerIdentity: TypeAlias = str
BlockerSequence: TypeAlias = tuple[BlockerIdentity, ...]
BlockerMap: TypeAlias = Mapping[BlockerIdentity, BlockerSequence]

_DRIVE_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:[/\\]")
_ENVIRONMENT_REFERENCE_RE: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[^{}]+\}"),
    re.compile(r"(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*"),
)
_MAX_IDENTITIES: Final[int] = 100_000
_MAX_IDENTITY_LENGTH: Final[int] = 2_048


@dataclass(frozen=True, slots=True)
class BlockerGraph:
    """Canonical directed graph whose edges point from subjects to blockers."""

    subjects: BlockerSequence
    edges: BlockerMap
    external_roots: BlockerSequence = ()
    unknown_references: BlockerMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        subjects = normalize_blocker_identities(self.subjects)
        subject_set = frozenset(subjects)

        edges = _freeze_blocker_map(
            self.edges,
            subjects=subject_set,
            allow_external=frozenset(self.external_roots),
            require_all_subjects=True,
        )
        external_roots = normalize_blocker_identities(
            self.external_roots,
            excluded=subject_set,
        )
        unknown_references = _freeze_unknown_map(
            self.unknown_references,
            subjects=subject_set,
            known=frozenset((*subjects, *external_roots)),
        )

        object.__setattr__(self, "subjects", subjects)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "external_roots", external_roots)
        object.__setattr__(self, "unknown_references", unknown_references)

    def blockers_for(self, subject: BlockerIdentity) -> BlockerSequence:
        canonical = normalize_blocker_identity(subject)
        if canonical not in self.edges:
            raise KeyError(f"unknown blocker-graph subject: {canonical!r}")
        return self.edges[canonical]

    def unknown_for(self, subject: BlockerIdentity) -> BlockerSequence:
        canonical = normalize_blocker_identity(subject)
        if canonical not in self.edges:
            raise KeyError(f"unknown blocker-graph subject: {canonical!r}")
        return self.unknown_references.get(canonical, ())

    @property
    def edge_count(self) -> int:
        return sum(len(blockers) for blockers in self.edges.values())


@dataclass(frozen=True, slots=True)
class BlockerGraphResolution:
    """Cycle-safe canonical root blockers derived from one blocker graph."""

    immediate_blockers: BlockerMap
    root_blockers: BlockerMap
    cycles: tuple[BlockerSequence, ...] = ()
    unresolved_subjects: BlockerSequence = ()
    unknown_references: BlockerMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        immediate = _freeze_closed_map(self.immediate_blockers)
        subjects = frozenset(immediate)
        roots = _freeze_result_map(
            self.root_blockers,
            subjects=subjects,
        )
        cycles = _normalize_cycles(self.cycles, subjects=subjects)
        unresolved = normalize_blocker_identities(
            self.unresolved_subjects,
            allowed=subjects,
        )
        unknown = _freeze_unknown_map(
            self.unknown_references,
            subjects=subjects,
            known=subjects,
        )

        object.__setattr__(self, "immediate_blockers", immediate)
        object.__setattr__(self, "root_blockers", roots)
        object.__setattr__(self, "cycles", cycles)
        object.__setattr__(self, "unresolved_subjects", unresolved)
        object.__setattr__(self, "unknown_references", unknown)

    def roots_for(self, subject: BlockerIdentity) -> BlockerSequence:
        canonical = normalize_blocker_identity(subject)
        if canonical not in self.root_blockers:
            raise KeyError(f"unknown blocker-resolution subject: {canonical!r}")
        return self.root_blockers[canonical]

    def is_unresolved(self, subject: BlockerIdentity) -> bool:
        canonical = normalize_blocker_identity(subject)
        return canonical in self.unresolved_subjects


def normalize_blocker_identity(value: object) -> BlockerIdentity:
    """Return a stable project-relative POSIX or namespaced identity."""

    if not isinstance(value, str):
        raise TypeError(
            f"blocker identity must be a string, got {type(value).__name__}"
        )

    candidate = value.strip()
    if not candidate:
        raise ValueError("blocker identity must not be empty")
    if "\x00" in candidate:
        raise ValueError("blocker identity must not contain NUL")
    if len(candidate) > _MAX_IDENTITY_LENGTH:
        raise ValueError("blocker identity exceeds the supported length")
    if not candidate.isascii():
        raise ValueError("blocker identity must use ASCII characters only")
    if candidate.startswith(("~", "/", "\\")):
        raise ValueError("blocker identity must not be an absolute or home path")
    if _DRIVE_PREFIX_RE.match(candidate):
        raise ValueError("blocker identity must not contain an absolute drive path")
    if any(pattern.search(candidate) for pattern in _ENVIRONMENT_REFERENCE_RE):
        raise ValueError("blocker identity must not contain environment references")

    normalized = candidate.replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    parts: list[str] = []
    for part in normalized.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("blocker identity must not contain parent traversal")
        if any(character.isspace() for character in part):
            raise ValueError("blocker identity path segments must not contain whitespace")
        parts.append(part)

    if not parts:
        raise ValueError("blocker identity must contain at least one segment")

    normalized = "/".join(parts)
    if normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    if not normalized:
        raise ValueError("blocker identity must not be empty after normalization")
    return normalized


def blocker_identity_key(
    value: object,
    *,
    case_sensitive: bool = True,
) -> str:
    """Return the deterministic comparison key for one blocker identity."""

    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")
    canonical = normalize_blocker_identity(value)
    return canonical if case_sensitive else canonical.casefold()


def normalize_blocker_identities(
    values: Iterable[object],
    *,
    self_identity: object | None = None,
    excluded: Iterable[object] = (),
    allowed: Iterable[object] | None = None,
    case_sensitive: bool = True,
) -> BlockerSequence:
    """Normalize, deduplicate, filter, and deterministically order identities."""

    if isinstance(values, (str, bytes)):
        raise TypeError("blocker identities must be an iterable, not one string")
    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")

    self_key = (
        None
        if self_identity is None
        else blocker_identity_key(self_identity, case_sensitive=case_sensitive)
    )
    excluded_keys = frozenset(
        blocker_identity_key(value, case_sensitive=case_sensitive)
        for value in excluded
    )
    allowed_keys = (
        None
        if allowed is None
        else frozenset(
            blocker_identity_key(value, case_sensitive=case_sensitive)
            for value in allowed
        )
    )

    canonical_by_key: dict[str, str] = {}
    for raw in values:
        canonical = normalize_blocker_identity(raw)
        key = blocker_identity_key(canonical, case_sensitive=case_sensitive)
        if key == self_key or key in excluded_keys:
            continue
        if allowed_keys is not None and key not in allowed_keys:
            raise ValueError(f"identity is outside the allowed set: {canonical!r}")
        previous = canonical_by_key.get(key)
        if previous is None or canonical < previous:
            canonical_by_key[key] = canonical
        if len(canonical_by_key) > _MAX_IDENTITIES:
            raise ValueError("blocker identity collection exceeds the supported limit")

    return tuple(
        sorted(
            canonical_by_key.values(),
            key=lambda value: _identity_sort_key(
                value,
                case_sensitive=case_sensitive,
            ),
        )
    )


def is_blocker_eligible(status: ValidationStatus | str) -> bool:
    """Return whether a peer status may participate as a causal blocker."""

    canonical = _coerce_validation_status(status)
    return canonical in (ValidationStatus.FAIL, ValidationStatus.ERROR)


def relationship_fields(
    diagnostic_class: DiagnosticClass | str,
    blockers: Iterable[object] = (),
    *,
    self_identity: object | None = None,
) -> tuple[bool, BlockerSequence]:
    """Return coherent ``is_direct`` and ``blocked_by`` relationship fields."""

    canonical_class = _coerce_diagnostic_class(diagnostic_class)
    canonical_blockers = normalize_blocker_identities(
        blockers,
        self_identity=self_identity,
    )

    if canonical_class is DiagnosticClass.DOWNSTREAM:
        if not canonical_blockers:
            raise ValueError("downstream diagnostic class requires blockers")
        return False, canonical_blockers

    if canonical_blockers:
        raise ValueError(
            f"{canonical_class.value!r} diagnostic class requires empty blockers"
        )

    return canonical_class is DiagnosticClass.DIRECT, ()


def validate_relationship_fields(
    diagnostic_class: DiagnosticClass | str,
    *,
    is_direct: bool,
    blocked_by: Iterable[object],
    self_identity: object | None = None,
) -> BlockerSequence:
    """Validate persisted or runtime causal fields and return canonical blockers."""

    if type(is_direct) is not bool:
        raise TypeError("is_direct must be a bool")

    expected_direct, canonical_blockers = relationship_fields(
        diagnostic_class,
        blocked_by,
        self_identity=self_identity,
    )
    if is_direct is not expected_direct:
        raise ValueError(
            "is_direct must equal "
            "(diagnostic_class == DiagnosticClass.DIRECT)"
        )
    return canonical_blockers


def build_blocker_graph(
    immediate_blockers: Mapping[object, Iterable[object]],
    *,
    known_subjects: Iterable[object] | None = None,
    external_roots: Iterable[object] = (),
    case_sensitive: bool = True,
) -> BlockerGraph:
    """Build a closed deterministic graph and retain unknown references separately."""

    if not isinstance(immediate_blockers, Mapping):
        raise TypeError("immediate_blockers must be a mapping")
    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")

    declared_external = normalize_blocker_identities(
        external_roots,
        case_sensitive=case_sensitive,
    )

    raw_subjects = (
        tuple(immediate_blockers.keys())
        if known_subjects is None
        else tuple(known_subjects)
    )
    subjects = normalize_blocker_identities(
        raw_subjects,
        excluded=declared_external,
        case_sensitive=case_sensitive,
    )
    if not subjects:
        if immediate_blockers:
            raise ValueError("blocker graph has edges but no canonical subjects")
        return BlockerGraph(
            subjects=(),
            edges={},
            external_roots=declared_external,
            unknown_references={},
        )

    subject_by_key = _unique_identity_index(
        subjects,
        case_sensitive=case_sensitive,
        field_name="known subjects",
    )
    external_by_key = _unique_identity_index(
        declared_external,
        case_sensitive=case_sensitive,
        field_name="external roots",
    )

    source_by_key: dict[str, Iterable[object]] = {}
    for raw_subject, raw_blockers in immediate_blockers.items():
        subject = normalize_blocker_identity(raw_subject)
        key = blocker_identity_key(subject, case_sensitive=case_sensitive)
        if key not in subject_by_key:
            raise ValueError(
                f"blocker-map subject is not declared: {subject!r}"
            )
        if key in source_by_key:
            raise ValueError(
                f"duplicate blocker-map subject after normalization: {subject!r}"
            )
        source_by_key[key] = raw_blockers

    edges: dict[str, BlockerSequence] = {}
    unknown: dict[str, BlockerSequence] = {}

    for subject in subjects:
        subject_key = blocker_identity_key(
            subject,
            case_sensitive=case_sensitive,
        )
        raw_blockers = source_by_key.get(subject_key, ())
        if isinstance(raw_blockers, (str, bytes)):
            raise TypeError(
                f"blockers for {subject!r} must be an iterable, not one string"
            )

        known_values: list[str] = []
        unknown_values: list[str] = []
        for raw_blocker in raw_blockers:
            blocker = normalize_blocker_identity(raw_blocker)
            blocker_key = blocker_identity_key(
                blocker,
                case_sensitive=case_sensitive,
            )
            if blocker_key == subject_key:
                continue
            canonical = subject_by_key.get(blocker_key)
            if canonical is not None:
                known_values.append(canonical)
                continue
            canonical = external_by_key.get(blocker_key)
            if canonical is not None:
                known_values.append(canonical)
                continue
            unknown_values.append(blocker)

        edges[subject] = normalize_blocker_identities(
            known_values,
            self_identity=subject,
            case_sensitive=case_sensitive,
        )
        if unknown_values:
            unknown[subject] = normalize_blocker_identities(
                unknown_values,
                self_identity=subject,
                case_sensitive=case_sensitive,
            )

    return BlockerGraph(
        subjects=subjects,
        edges=edges,
        external_roots=declared_external,
        unknown_references=unknown,
    )


def find_blocker_cycles(graph: BlockerGraph) -> tuple[BlockerSequence, ...]:
    """Return deterministic strongly connected blocker cycles."""

    _require_graph(graph)

    index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[BlockerSequence] = []
    subject_set = frozenset(graph.subjects)

    def visit(subject: str) -> None:
        nonlocal index
        indexes[subject] = index
        lowlinks[subject] = index
        index += 1
        stack.append(subject)
        on_stack.add(subject)

        for blocker in graph.edges[subject]:
            if blocker not in subject_set:
                continue
            if blocker not in indexes:
                visit(blocker)
                lowlinks[subject] = min(
                    lowlinks[subject],
                    lowlinks[blocker],
                )
            elif blocker in on_stack:
                lowlinks[subject] = min(
                    lowlinks[subject],
                    indexes[blocker],
                )

        if lowlinks[subject] != indexes[subject]:
            return

        component: list[str] = []
        while stack:
            current = stack.pop()
            on_stack.remove(current)
            component.append(current)
            if current == subject:
                break

        if len(component) > 1:
            cycles.append(
                tuple(sorted(component, key=_identity_sort_key))
            )

    for subject in graph.subjects:
        if subject not in indexes:
            visit(subject)

    return tuple(
        sorted(
            cycles,
            key=lambda cycle: tuple(
                _identity_sort_key(value) for value in cycle
            ),
        )
    )


def collapse_blocker_graph(
    graph: BlockerGraph,
    *,
    root_subjects: Iterable[object] = (),
    terminal_subjects_are_roots: bool = True,
) -> BlockerGraphResolution:
    """Collapse blocker chains to deterministic roots without inventing cycle roots."""

    _require_graph(graph)
    if type(terminal_subjects_are_roots) is not bool:
        raise TypeError("terminal_subjects_are_roots must be a bool")

    subject_set = frozenset(graph.subjects)
    external_set = frozenset(graph.external_roots)
    explicit_roots = frozenset(
        normalize_blocker_identities(
            root_subjects,
            allowed=subject_set,
        )
    )
    cycles = find_blocker_cycles(graph)
    cycle_nodes = frozenset(
        subject for cycle in cycles for subject in cycle
    )

    memo: dict[tuple[str, str], frozenset[str]] = {}

    def roots_from(
        node: str,
        *,
        origin: str,
        stack: frozenset[str],
    ) -> frozenset[str]:
        cache_key = (origin, node)
        cached = memo.get(cache_key)
        if cached is not None and node not in stack:
            return cached

        if node == origin:
            return frozenset()
        if node in external_set:
            return frozenset((node,))
        if node in explicit_roots:
            return frozenset((node,))
        if node not in subject_set:
            return frozenset()
        if node in stack:
            return frozenset()

        blockers = graph.edges[node]
        if not blockers:
            result = (
                frozenset((node,))
                if terminal_subjects_are_roots
                else frozenset()
            )
            memo[cache_key] = result
            return result

        roots: set[str] = set()
        next_stack = stack | frozenset((node,))
        for blocker in blockers:
            roots.update(
                roots_from(
                    blocker,
                    origin=origin,
                    stack=next_stack,
                )
            )

        result = frozenset(roots)
        if node not in cycle_nodes or result:
            memo[cache_key] = result
        return result

    root_map: dict[str, BlockerSequence] = {}
    unresolved: list[str] = []

    for subject in graph.subjects:
        if subject in explicit_roots:
            root_map[subject] = ()
            continue

        roots: set[str] = set()
        for blocker in graph.edges[subject]:
            roots.update(
                roots_from(
                    blocker,
                    origin=subject,
                    stack=frozenset((subject,)),
                )
            )

        canonical_roots = normalize_blocker_identities(
            roots,
            self_identity=subject,
        )
        root_map[subject] = canonical_roots

        has_relationship_evidence = bool(
            graph.edges[subject]
            or graph.unknown_references.get(subject)
        )
        if has_relationship_evidence and not canonical_roots:
            unresolved.append(subject)

    return BlockerGraphResolution(
        immediate_blockers=graph.edges,
        root_blockers=root_map,
        cycles=cycles,
        unresolved_subjects=normalize_blocker_identities(unresolved),
        unknown_references=graph.unknown_references,
    )


def resolve_root_blockers(
    subject: object,
    immediate_blockers: Mapping[object, Iterable[object]],
    *,
    known_subjects: Iterable[object] | None = None,
    root_subjects: Iterable[object] = (),
    external_roots: Iterable[object] = (),
    terminal_subjects_are_roots: bool = True,
    case_sensitive: bool = True,
) -> BlockerSequence:
    """Build, collapse, and return canonical root blockers for one subject."""

    graph = build_blocker_graph(
        immediate_blockers,
        known_subjects=known_subjects,
        external_roots=external_roots,
        case_sensitive=case_sensitive,
    )
    resolution = collapse_blocker_graph(
        graph,
        root_subjects=root_subjects,
        terminal_subjects_are_roots=terminal_subjects_are_roots,
    )
    return resolution.roots_for(normalize_blocker_identity(subject))


def has_blocker_path(
    graph: BlockerGraph,
    subject: object,
    blocker: object,
) -> bool:
    """Return whether a bounded directed path exists from subject to blocker."""

    _require_graph(graph)
    source = normalize_blocker_identity(subject)
    target = normalize_blocker_identity(blocker)
    if source not in graph.edges:
        raise KeyError(f"unknown blocker-graph subject: {source!r}")
    if source == target:
        return False

    pending = list(reversed(graph.edges[source]))
    visited: set[str] = {source}
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        if len(visited) > _MAX_IDENTITIES:
            raise ValueError("blocker traversal exceeds the supported limit")
        if current in graph.edges:
            pending.extend(reversed(graph.edges[current]))
    return False


def _freeze_blocker_map(
    values: Mapping[object, Iterable[object]],
    *,
    subjects: frozenset[str],
    allow_external: frozenset[str],
    require_all_subjects: bool,
) -> BlockerMap:
    if not isinstance(values, Mapping):
        raise TypeError("edges must be a mapping")

    copied: dict[str, BlockerSequence] = {}
    for raw_subject, raw_blockers in values.items():
        subject = normalize_blocker_identity(raw_subject)
        if subject not in subjects:
            raise ValueError(f"edge source is not a graph subject: {subject!r}")
        if subject in copied:
            raise ValueError(f"duplicate edge source: {subject!r}")
        copied[subject] = normalize_blocker_identities(
            raw_blockers,
            self_identity=subject,
            allowed=subjects | allow_external,
        )

    if require_all_subjects:
        missing = subjects.difference(copied)
        if missing:
            rendered = ", ".join(sorted(missing, key=_identity_sort_key))
            raise ValueError(f"edges omit graph subjects: {rendered}")

    ordered = {
        subject: copied[subject]
        for subject in sorted(copied, key=_identity_sort_key)
    }
    return MappingProxyType(ordered)


def _freeze_closed_map(
    values: Mapping[object, Iterable[object]],
) -> BlockerMap:
    if not isinstance(values, Mapping):
        raise TypeError("blocker map must be a mapping")
    subjects = normalize_blocker_identities(values.keys())
    return _freeze_blocker_map(
        values,
        subjects=frozenset(subjects),
        allow_external=frozenset(),
        require_all_subjects=True,
    )


def _freeze_result_map(
    values: Mapping[object, Iterable[object]],
    *,
    subjects: frozenset[str],
) -> BlockerMap:
    if not isinstance(values, Mapping):
        raise TypeError("root_blockers must be a mapping")
    copied: dict[str, BlockerSequence] = {}
    for raw_subject, raw_blockers in values.items():
        subject = normalize_blocker_identity(raw_subject)
        if subject not in subjects:
            raise ValueError(
                f"root blocker source is not a subject: {subject!r}"
            )
        if subject in copied:
            raise ValueError(f"duplicate root blocker source: {subject!r}")
        copied[subject] = normalize_blocker_identities(
            raw_blockers,
            self_identity=subject,
        )
    missing = subjects.difference(copied)
    if missing:
        rendered = ", ".join(sorted(missing, key=_identity_sort_key))
        raise ValueError(f"root_blockers omit subjects: {rendered}")
    return MappingProxyType(
        {
            subject: copied[subject]
            for subject in sorted(copied, key=_identity_sort_key)
        }
    )


def _freeze_unknown_map(
    values: Mapping[object, Iterable[object]],
    *,
    subjects: frozenset[str],
    known: frozenset[str],
) -> BlockerMap:
    if not isinstance(values, Mapping):
        raise TypeError("unknown_references must be a mapping")
    copied: dict[str, BlockerSequence] = {}
    for raw_subject, raw_references in values.items():
        subject = normalize_blocker_identity(raw_subject)
        if subject not in subjects:
            raise ValueError(
                f"unknown-reference source is not a subject: {subject!r}"
            )
        references = normalize_blocker_identities(
            raw_references,
            self_identity=subject,
        )
        if any(reference in known for reference in references):
            raise ValueError(
                "unknown_references contains a declared subject or external root"
            )
        if references:
            copied[subject] = references
    return MappingProxyType(
        {
            subject: copied[subject]
            for subject in sorted(copied, key=_identity_sort_key)
        }
    )


def _normalize_cycles(
    values: Iterable[Iterable[object]],
    *,
    subjects: frozenset[str],
) -> tuple[BlockerSequence, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("cycles must be an iterable of identity collections")

    cycles: set[BlockerSequence] = set()
    for raw_cycle in values:
        cycle = normalize_blocker_identities(
            raw_cycle,
            allowed=subjects,
        )
        if len(cycle) < 2:
            raise ValueError("a blocker cycle must contain at least two subjects")
        cycles.add(cycle)

    return tuple(
        sorted(
            cycles,
            key=lambda cycle: tuple(
                _identity_sort_key(identity) for identity in cycle
            ),
        )
    )


def _unique_identity_index(
    values: Sequence[str],
    *,
    case_sensitive: bool,
    field_name: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for identity in values:
        key = blocker_identity_key(
            identity,
            case_sensitive=case_sensitive,
        )
        previous = result.get(key)
        if previous is not None and previous != identity:
            raise ValueError(
                f"{field_name} contains comparison-equivalent identities: "
                f"{previous!r}, {identity!r}"
            )
        result[key] = identity
    return result


def _identity_sort_key(
    value: str,
    *,
    case_sensitive: bool = True,
) -> tuple[str, str]:
    canonical = normalize_blocker_identity(value)
    comparison = canonical if case_sensitive else canonical.casefold()
    return comparison, canonical


def _coerce_validation_status(
    value: ValidationStatus | str,
) -> ValidationStatus:
    if isinstance(value, ValidationStatus):
        return value
    if not isinstance(value, str):
        raise TypeError("status must be ValidationStatus or string")
    try:
        return ValidationStatus(value)
    except ValueError as exc:
        raise ValueError(f"unknown validation status: {value!r}") from exc


def _coerce_diagnostic_class(
    value: DiagnosticClass | str,
) -> DiagnosticClass:
    if isinstance(value, DiagnosticClass):
        return value
    if not isinstance(value, str):
        raise TypeError("diagnostic_class must be DiagnosticClass or string")
    try:
        return DiagnosticClass(value)
    except ValueError as exc:
        raise ValueError(f"unknown diagnostic class: {value!r}") from exc


def _require_graph(value: object) -> BlockerGraph:
    if not isinstance(value, BlockerGraph):
        raise TypeError("graph must be a BlockerGraph")
    return value


__all__ = (
    "BlockerGraph",
    "BlockerGraphResolution",
    "BlockerIdentity",
    "BlockerMap",
    "BlockerSequence",
    "blocker_identity_key",
    "build_blocker_graph",
    "collapse_blocker_graph",
    "find_blocker_cycles",
    "has_blocker_path",
    "is_blocker_eligible",
    "normalize_blocker_identities",
    "normalize_blocker_identity",
    "relationship_fields",
    "resolve_root_blockers",
    "validate_relationship_fields",
)
