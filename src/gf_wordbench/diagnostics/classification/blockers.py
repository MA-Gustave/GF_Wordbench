"""Deterministic blocker normalization and root resolution."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import PurePath, PureWindowsPath
from types import MappingProxyType
from typing import Final, TypeAlias

BlockerIdentity: TypeAlias = str
BlockerIdentityLike: TypeAlias = str | PurePath
BlockerGraphInput: TypeAlias = Mapping[
    BlockerIdentityLike,
    Iterable[BlockerIdentityLike],
]

_DEFAULT_MAX_NODES: Final = 100_000
_DEFAULT_MAX_EDGES: Final = 1_000_000


class BlockerGraphError(ValueError):
    """Invalid blocker identity or graph structure."""


class DuplicateBlockerIdentityError(BlockerGraphError):
    """Two supplied identities normalize to the same comparison key."""


class UnknownBlockerSubjectError(BlockerGraphError):
    """A requested subject is absent from a resolved graph."""


@dataclass(frozen=True, slots=True)
class BlockerCycle:
    members: tuple[BlockerIdentity, ...]
    root_blockers: tuple[BlockerIdentity, ...] = ()

    def __post_init__(self) -> None:
        members = _identity_tuple(self.members, field="members")
        roots = _identity_tuple(self.root_blockers, field="root_blockers")
        if len(members) < 2:
            raise ValueError("a blocker cycle requires at least two members")
        object.__setattr__(self, "members", members)
        object.__setattr__(self, "root_blockers", roots)

    @property
    def resolved(self) -> bool:
        return bool(self.root_blockers)


@dataclass(frozen=True, slots=True)
class BlockerResolution:
    subject_id: BlockerIdentity
    immediate_blockers: tuple[BlockerIdentity, ...]
    root_blockers: tuple[BlockerIdentity, ...]
    unknown_references: tuple[BlockerIdentity, ...] = ()
    cycle_members: tuple[BlockerIdentity, ...] = ()

    def __post_init__(self) -> None:
        subject = normalize_blocker_identity(self.subject_id)
        immediate = _identity_tuple(
            self.immediate_blockers,
            field="immediate_blockers",
        )
        roots = _identity_tuple(self.root_blockers, field="root_blockers")
        unknown = _identity_tuple(
            self.unknown_references,
            field="unknown_references",
        )
        cycle = _identity_tuple(self.cycle_members, field="cycle_members")
        if subject in immediate or subject in roots:
            raise ValueError("a subject cannot block itself")
        object.__setattr__(self, "subject_id", subject)
        object.__setattr__(self, "immediate_blockers", immediate)
        object.__setattr__(self, "root_blockers", roots)
        object.__setattr__(self, "unknown_references", unknown)
        object.__setattr__(self, "cycle_members", cycle)

    @property
    def is_downstream_candidate(self) -> bool:
        return bool(self.root_blockers)

    @property
    def has_unresolved_cycle(self) -> bool:
        return bool(self.cycle_members) and not self.root_blockers


@dataclass(frozen=True, slots=True)
class BlockerGraphResolution:
    immediate_blockers: Mapping[str, tuple[str, ...]]
    root_blockers: Mapping[str, tuple[str, ...]]
    unknown_references: Mapping[str, tuple[str, ...]]
    cycles: tuple[BlockerCycle, ...]
    external_blockers: tuple[str, ...]
    case_sensitive: bool = True

    def __post_init__(self) -> None:
        if type(self.case_sensitive) is not bool:
            raise TypeError("case_sensitive must be a bool")
        immediate = _freeze_map(self.immediate_blockers, "immediate_blockers")
        roots = _freeze_map(self.root_blockers, "root_blockers")
        unknown = _freeze_map(self.unknown_references, "unknown_references")
        if tuple(immediate) != tuple(roots) or tuple(immediate) != tuple(unknown):
            raise ValueError("blocker mappings must contain identical subjects")
        cycles = tuple(self.cycles)
        if not all(isinstance(value, BlockerCycle) for value in cycles):
            raise TypeError("cycles must contain BlockerCycle values")
        external = _identity_tuple(
            self.external_blockers,
            field="external_blockers",
        )
        object.__setattr__(self, "immediate_blockers", immediate)
        object.__setattr__(self, "root_blockers", roots)
        object.__setattr__(self, "unknown_references", unknown)
        object.__setattr__(self, "cycles", cycles)
        object.__setattr__(self, "external_blockers", external)

    @property
    def subjects(self) -> tuple[str, ...]:
        return tuple(self.immediate_blockers)

    def resolution_for(self, subject_id: BlockerIdentityLike) -> BlockerResolution:
        subject = _lookup(
            subject_id,
            self.subjects,
            case_sensitive=self.case_sensitive,
        )
        if subject is None:
            raise UnknownBlockerSubjectError(f"unknown blocker subject: {subject_id!r}")
        cycle_members: tuple[str, ...] = ()
        for cycle in self.cycles:
            if subject in cycle.members:
                cycle_members = cycle.members
                break
        return BlockerResolution(
            subject_id=subject,
            immediate_blockers=self.immediate_blockers[subject],
            root_blockers=self.root_blockers[subject],
            unknown_references=self.unknown_references[subject],
            cycle_members=cycle_members,
        )

    def roots_for(self, subject_id: BlockerIdentityLike) -> tuple[str, ...]:
        return self.resolution_for(subject_id).root_blockers

    @property
    def has_unresolved_cycles(self) -> bool:
        return any(not cycle.resolved for cycle in self.cycles)


def normalize_blocker_identity(value: BlockerIdentityLike) -> str:
    """Return a canonical project-relative POSIX blocker identity."""

    if isinstance(value, PurePath):
        raw = str(value)
    elif isinstance(value, str):
        raw = value
    else:
        raise TypeError("blocker identity must be a string or PurePath")
    if not raw or not raw.strip():
        raise BlockerGraphError("blocker identity must not be empty")
    if raw != raw.strip():
        raise BlockerGraphError("blocker identity must not have outer whitespace")
    if "\x00" in raw:
        raise BlockerGraphError("blocker identity must not contain NUL")
    windows = PureWindowsPath(raw)
    if windows.drive or windows.root:
        raise BlockerGraphError("blocker identity must be project-relative")
    portable = raw.replace("\\", "/")
    if portable.startswith(("/", "~", "$")) or "%" in portable or "${" in portable:
        raise BlockerGraphError("blocker identity must not be absolute or environment-dependent")
    parts: list[str] = []
    for part in portable.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise BlockerGraphError("blocker identity must not traverse parents")
        parts.append(part)
    if not parts:
        raise BlockerGraphError("blocker identity must contain a component")
    return "/".join(parts)


def normalize_blocker_identities(
    values: Iterable[BlockerIdentityLike],
    *,
    subject_id: BlockerIdentityLike | None = None,
    case_sensitive: bool = True,
) -> tuple[str, ...]:
    """Normalize, de-duplicate, self-filter, and sort identities."""

    if isinstance(values, (str, bytes, PurePath)):
        raise TypeError("blocker identities must be an iterable")
    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")
    subject_key = None
    if subject_id is not None:
        subject_key = _key(
            normalize_blocker_identity(subject_id),
            case_sensitive=case_sensitive,
        )
    indexed: dict[str, str] = {}
    for value in values:
        identity = normalize_blocker_identity(value)
        key = _key(identity, case_sensitive=case_sensitive)
        if key == subject_key:
            continue
        previous = indexed.get(key)
        if previous is not None and previous != identity:
            raise DuplicateBlockerIdentityError(
                f"identity collision: {previous!r} and {identity!r}"
            )
        indexed[key] = identity
    return tuple(value for _, value in sorted(indexed.items()))


def validate_blocked_by(
    subject_id: BlockerIdentityLike,
    blocked_by: Iterable[BlockerIdentityLike],
    *,
    require_non_empty: bool = False,
    case_sensitive: bool = True,
) -> tuple[str, ...]:
    """Validate a canonical persisted ``blocked_by`` array."""

    if type(require_non_empty) is not bool:
        raise TypeError("require_non_empty must be a bool")
    result = normalize_blocker_identities(
        blocked_by,
        subject_id=subject_id,
        case_sensitive=case_sensitive,
    )
    if require_non_empty and not result:
        raise BlockerGraphError("downstream classification requires blockers")
    return result


def resolve_blocker_graph(
    immediate_blockers: BlockerGraphInput,
    *,
    known_subjects: Iterable[BlockerIdentityLike] | None = None,
    external_blockers: Iterable[BlockerIdentityLike] = (),
    case_sensitive: bool = True,
    max_nodes: int = _DEFAULT_MAX_NODES,
    max_edges: int = _DEFAULT_MAX_EDGES,
) -> BlockerGraphResolution:
    """Normalize blockers, remove unknown references, and collapse roots."""

    if not isinstance(immediate_blockers, Mapping):
        raise TypeError("immediate_blockers must be a mapping")
    _positive_int(max_nodes, "max_nodes")
    _positive_int(max_edges, "max_edges")
    if type(case_sensitive) is not bool:
        raise TypeError("case_sensitive must be a bool")

    supplied = tuple(immediate_blockers)
    subjects = _index_identities(
        supplied if known_subjects is None else (*tuple(known_subjects), *supplied),
        case_sensitive=case_sensitive,
        field="subject",
    )
    if len(subjects) > max_nodes:
        raise BlockerGraphError(f"blocker graph exceeds max_nodes={max_nodes}")
    external = _index_identities(
        external_blockers,
        case_sensitive=case_sensitive,
        field="external blocker",
    )
    for key in tuple(external):
        if key in subjects:
            del external[key]

    raw_by_subject: dict[str, Iterable[BlockerIdentityLike]] = {}
    for raw_subject, raw_blockers in immediate_blockers.items():
        normalized = normalize_blocker_identity(raw_subject)
        subject = subjects[_key(normalized, case_sensitive=case_sensitive)]
        if subject in raw_by_subject:
            raise DuplicateBlockerIdentityError(f"duplicate subject {subject!r}")
        if isinstance(raw_blockers, (str, bytes, PurePath)):
            raise TypeError(f"blockers for {subject!r} must be an iterable")
        raw_by_subject[subject] = raw_blockers

    ordered_subjects = tuple(value for _, value in sorted(subjects.items()))
    graph: dict[str, tuple[str, ...]] = {}
    unknown: dict[str, tuple[str, ...]] = {}
    edges = 0
    for subject in ordered_subjects:
        confirmed: list[str] = []
        rejected: list[str] = []
        for raw in raw_by_subject.get(subject, ()):
            identity = normalize_blocker_identity(raw)
            key = _key(identity, case_sensitive=case_sensitive)
            if key == _key(subject, case_sensitive=case_sensitive):
                continue
            if key in subjects:
                confirmed.append(subjects[key])
            elif key in external:
                confirmed.append(external[key])
            else:
                rejected.append(identity)
        graph[subject] = normalize_blocker_identities(
            confirmed,
            subject_id=subject,
            case_sensitive=case_sensitive,
        )
        unknown[subject] = normalize_blocker_identities(
            rejected,
            subject_id=subject,
            case_sensitive=case_sensitive,
        )
        edges += len(graph[subject])
        if edges > max_edges:
            raise BlockerGraphError(f"blocker graph exceeds max_edges={max_edges}")

    components, component_for = _components(graph, case_sensitive=case_sensitive)
    component_edges = _component_edges(
        graph,
        components,
        component_for,
        frozenset(external.values()),
    )
    roots_by_component = _component_roots(
        components,
        component_edges,
        case_sensitive=case_sensitive,
    )

    roots: dict[str, tuple[str, ...]] = {}
    for subject in ordered_subjects:
        values: list[str] = []
        for blocker in graph[subject]:
            component = component_for.get(blocker)
            values.extend((blocker,) if component is None else roots_by_component[component])
        roots[subject] = normalize_blocker_identities(
            values,
            subject_id=subject,
            case_sensitive=case_sensitive,
        )

    cycles = tuple(
        BlockerCycle(
            members=component,
            root_blockers=tuple(
                root for root in roots_by_component[index] if root not in component
            ),
        )
        for index, component in enumerate(components)
        if len(component) > 1
    )
    return BlockerGraphResolution(
        immediate_blockers=MappingProxyType(graph),
        root_blockers=MappingProxyType(roots),
        unknown_references=MappingProxyType(unknown),
        cycles=cycles,
        external_blockers=tuple(value for _, value in sorted(external.items())),
        case_sensitive=case_sensitive,
    )


def collapse_blocker_roots(
    subject_id: BlockerIdentityLike,
    immediate_blockers: BlockerGraphInput,
    *,
    known_subjects: Iterable[BlockerIdentityLike] | None = None,
    external_blockers: Iterable[BlockerIdentityLike] = (),
    case_sensitive: bool = True,
) -> tuple[str, ...]:
    return resolve_blocker_graph(
        immediate_blockers,
        known_subjects=known_subjects,
        external_blockers=external_blockers,
        case_sensitive=case_sensitive,
    ).roots_for(subject_id)


def _components(
    graph: Mapping[str, tuple[str, ...]],
    *,
    case_sensitive: bool,
) -> tuple[tuple[tuple[str, ...], ...], Mapping[str, int]]:
    counter = 0
    stack: list[str] = []
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    active: set[str] = set()
    found: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal counter
        index[node] = counter
        low[node] = counter
        counter += 1
        stack.append(node)
        active.add(node)
        for target in graph[node]:
            if target not in graph:
                continue
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in active:
                low[node] = min(low[node], index[target])
        if low[node] != index[node]:
            return
        members: list[str] = []
        while True:
            member = stack.pop()
            active.remove(member)
            members.append(member)
            if member == node:
                break
        members.sort(key=lambda value: _key(value, case_sensitive=case_sensitive))
        found.append(tuple(members))

    for node in graph:
        if node not in index:
            visit(node)
    found.sort(
        key=lambda values: tuple(_key(value, case_sensitive=case_sensitive) for value in values)
    )
    component_for = {
        member: component_index
        for component_index, members in enumerate(found)
        for member in members
    }
    return tuple(found), MappingProxyType(component_for)


def _component_edges(
    graph: Mapping[str, tuple[str, ...]],
    components: tuple[tuple[str, ...], ...],
    component_for: Mapping[str, int],
    external: frozenset[str],
) -> tuple[tuple[tuple[int, ...], tuple[str, ...]], ...]:
    result: list[tuple[tuple[int, ...], tuple[str, ...]]] = []
    for current, members in enumerate(components):
        downstream: set[int] = set()
        terminals: set[str] = set()
        for member in members:
            for blocker in graph[member]:
                target = component_for.get(blocker)
                if target is not None and target != current:
                    downstream.add(target)
                elif blocker in external:
                    terminals.add(blocker)
        result.append((tuple(sorted(downstream)), tuple(sorted(terminals))))
    return tuple(result)


def _component_roots(
    components: tuple[tuple[str, ...], ...],
    edges: tuple[tuple[tuple[int, ...], tuple[str, ...]], ...],
    *,
    case_sensitive: bool,
) -> tuple[tuple[str, ...], ...]:
    cache: dict[int, tuple[str, ...]] = {}
    active: set[int] = set()

    def resolve(component: int) -> tuple[str, ...]:
        if component in cache:
            return cache[component]
        if component in active:
            return ()
        active.add(component)
        targets, external = edges[component]
        values: list[str] = list(external)
        for target in targets:
            values.extend(resolve(target))
        if not targets and not external and len(components[component]) == 1:
            values.append(components[component][0])
        active.remove(component)
        result = normalize_blocker_identities(
            values,
            case_sensitive=case_sensitive,
        )
        cache[component] = result
        return result

    return tuple(resolve(index) for index in range(len(components)))


def _index_identities(
    values: Iterable[BlockerIdentityLike],
    *,
    case_sensitive: bool,
    field: str,
) -> dict[str, str]:
    if isinstance(values, (str, bytes, PurePath)):
        raise TypeError(f"{field} values must be an iterable")
    result: dict[str, str] = {}
    for value in values:
        identity = normalize_blocker_identity(value)
        key = _key(identity, case_sensitive=case_sensitive)
        previous = result.get(key)
        if previous is not None and previous != identity:
            raise DuplicateBlockerIdentityError(f"{field} collision: {previous!r} and {identity!r}")
        result[key] = identity
    return result


def _freeze_map(
    values: Mapping[str, Iterable[BlockerIdentityLike]],
    field: str,
) -> Mapping[str, tuple[str, ...]]:
    if not isinstance(values, Mapping):
        raise TypeError(f"{field} must be a mapping")
    result: dict[str, tuple[str, ...]] = {}
    for key, items in values.items():
        identity = normalize_blocker_identity(key)
        if identity in result:
            raise ValueError(f"duplicate {field} subject {identity!r}")
        result[identity] = _identity_tuple(items, field=f"{field}[{identity!r}]")
    return MappingProxyType(result)


def _identity_tuple(
    values: Iterable[BlockerIdentityLike],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, PurePath)):
        raise TypeError(f"{field} must be an iterable")
    result = tuple(normalize_blocker_identity(value) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    return result


def _lookup(
    value: BlockerIdentityLike,
    candidates: Iterable[str],
    *,
    case_sensitive: bool,
) -> str | None:
    key = _key(normalize_blocker_identity(value), case_sensitive=case_sensitive)
    return next(
        (
            candidate
            for candidate in candidates
            if _key(candidate, case_sensitive=case_sensitive) == key
        ),
        None,
    )


def _key(value: str, *, case_sensitive: bool) -> str:
    return value if case_sensitive else value.casefold()


def _positive_int(value: int, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be positive")


__all__ = (
    "BlockerCycle",
    "BlockerGraphError",
    "BlockerGraphInput",
    "BlockerIdentity",
    "BlockerIdentityLike",
    "BlockerResolution",
    "DuplicateBlockerIdentityError",
    "UnknownBlockerSubjectError",
    "collapse_blocker_roots",
    "resolve_blocker_graph",
    "validate_blocked_by",
)
