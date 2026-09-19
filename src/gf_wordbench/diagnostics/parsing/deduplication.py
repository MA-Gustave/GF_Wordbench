"""Deterministic diagnostic deduplication without raw-evidence loss."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
import re
from types import MappingProxyType
from typing import Final, Generic, TypeVar

RecordT = TypeVar("RecordT")

_MAX_RECORDS: Final[int] = 1_000_000
_MAX_TEXT_LENGTH: Final[int] = 8 * 1024 * 1024
_STREAM_ORDER: Final[Mapping[str, int]] = MappingProxyType({"stderr": 0, "stdout": 1})
_HORIZONTAL_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"[\t\f\v ]+")
_WINDOWS_ABSOLUTE_RE: Final[re.Pattern[str]] = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
_SEMANTIC_FIELDS: Final[tuple[str, ...]] = (
    "severity",
    "origin",
    "detail",
    "source_module",
    "symbol",
    "expected",
    "actual",
    "expected_type",
    "actual_type",
    "assertion_id",
    "artifact_role",
    "blocker",
    "blocked_by",
    "execution_state",
    "is_fatal",
    "is_warning",
    "is_unknown",
)


@dataclass(frozen=True, slots=True, order=True)
class DiagnosticDuplicateKey:
    """Stable semantic identity used only for a deduplicated parse view."""

    pattern_id: str
    error_kind: str
    normalized_signature: str
    source_path_normalized: str | None
    line: int | None
    column: int | None
    origin: str | None
    severity: str | None
    semantic_discriminator: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "pattern_id",
            _required_text(self.pattern_id, field="pattern_id", max_length=256),
        )
        object.__setattr__(
            self,
            "error_kind",
            _required_text(self.error_kind, field="error_kind", max_length=128),
        )
        object.__setattr__(
            self,
            "normalized_signature",
            _required_text(
                self.normalized_signature,
                field="normalized_signature",
                max_length=_MAX_TEXT_LENGTH,
            ),
        )
        if self.source_path_normalized is not None:
            object.__setattr__(
                self,
                "source_path_normalized",
                _required_text(
                    self.source_path_normalized,
                    field="source_path_normalized",
                    max_length=32_768,
                ),
            )
        _optional_non_negative_int(self.line, field="line", allow_zero=False)
        _optional_non_negative_int(self.column, field="column", allow_zero=False)
        if self.origin is not None:
            object.__setattr__(
                self,
                "origin",
                _required_text(self.origin, field="origin", max_length=128),
            )
        if self.severity is not None:
            object.__setattr__(
                self,
                "severity",
                _required_text(self.severity, field="severity", max_length=128),
            )
        object.__setattr__(
            self,
            "semantic_discriminator",
            _required_text(
                self.semantic_discriminator,
                field="semantic_discriminator",
                max_length=128,
            ),
        )


@dataclass(frozen=True, slots=True)
class DiagnosticOccurrence:
    """Provenance for one preserved diagnostic occurrence."""

    record_id: str
    stream: str
    start_line: int
    end_line: int
    raw_artifact_path: Path | None
    raw_excerpt: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "record_id",
            _required_text(self.record_id, field="record_id", max_length=512),
        )
        object.__setattr__(
            self,
            "stream",
            _required_text(self.stream, field="stream", max_length=64),
        )
        _positive_int(self.start_line, field="start_line")
        _positive_int(self.end_line, field="end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        if self.raw_artifact_path is not None:
            object.__setattr__(
                self,
                "raw_artifact_path",
                _path(self.raw_artifact_path, field="raw_artifact_path"),
            )
        object.__setattr__(
            self,
            "raw_excerpt",
            _text(
                self.raw_excerpt,
                field="raw_excerpt",
                allow_empty=True,
                max_length=_MAX_TEXT_LENGTH,
            ),
        )


@dataclass(frozen=True, slots=True)
class DeduplicatedDiagnostic(Generic[RecordT]):
    """One representative record plus every preserved occurrence."""

    key: DiagnosticDuplicateKey
    representative: RecordT
    occurrences: tuple[RecordT, ...]
    provenance: tuple[DiagnosticOccurrence, ...]
    streams: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.key, DiagnosticDuplicateKey):
            raise TypeError("key must be DiagnosticDuplicateKey")
        if not self.occurrences:
            raise ValueError("occurrences must not be empty")
        if self.representative is not self.occurrences[0]:
            raise ValueError("representative must be the first occurrence")
        if len(self.occurrences) != len(self.provenance):
            raise ValueError("occurrences and provenance must have identical lengths")
        if not self.streams:
            raise ValueError("streams must not be empty")
        if len(self.streams) != len(set(self.streams)):
            raise ValueError("streams must not contain duplicates")
        provenance_streams = {item.stream for item in self.provenance}
        if set(self.streams) != provenance_streams:
            raise ValueError("streams must exactly describe provenance streams")

    @property
    def occurrence_count(self) -> int:
        return len(self.occurrences)

    @property
    def record_ids(self) -> tuple[str, ...]:
        return tuple(item.record_id for item in self.provenance)

    @property
    def is_duplicate(self) -> bool:
        return len(self.occurrences) > 1


@dataclass(frozen=True, slots=True)
class DiagnosticDeduplicationResult(Generic[RecordT]):
    """Original records and their non-destructive deduplicated view."""

    records: tuple[RecordT, ...]
    groups: tuple[DeduplicatedDiagnostic[RecordT], ...]

    def __post_init__(self) -> None:
        if len(self.records) > _MAX_RECORDS:
            raise ValueError("records exceeds the supported limit")
        positions_by_identity: dict[int, list[int]] = {}
        for index, record in enumerate(self.records):
            positions_by_identity.setdefault(id(record), []).append(index)

        consumed_by_identity: dict[int, int] = {}
        consumed_indexes: set[int] = set()
        first_indexes: list[int] = []
        for group in self.groups:
            indexes: list[int] = []
            for occurrence in group.occurrences:
                identity = id(occurrence)
                positions = positions_by_identity.get(identity, [])
                offset = consumed_by_identity.get(identity, 0)
                if offset >= len(positions):
                    raise ValueError("groups must preserve every original record exactly once")
                original_index = positions[offset]
                if self.records[original_index] is not occurrence:
                    raise ValueError("groups must preserve records by object identity")
                consumed_by_identity[identity] = offset + 1
                consumed_indexes.add(original_index)
                indexes.append(original_index)

            if indexes != sorted(indexes):
                raise ValueError("group occurrences must preserve original order")
            if indexes:
                first_indexes.append(indexes[0])

        if consumed_indexes != set(range(len(self.records))):
            raise ValueError("groups must preserve every original record exactly once")
        if first_indexes != sorted(first_indexes):
            raise ValueError("groups must preserve first-occurrence order")

    @property
    def representatives(self) -> tuple[RecordT, ...]:
        return tuple(group.representative for group in self.groups)

    @property
    def duplicate_occurrence_count(self) -> int:
        return sum(group.occurrence_count - 1 for group in self.groups)

    @property
    def has_duplicates(self) -> bool:
        return any(group.is_duplicate for group in self.groups)


@dataclass(slots=True)
class _MutableGroup(Generic[RecordT]):
    key: DiagnosticDuplicateKey
    records: list[RecordT]
    provenance: list[DiagnosticOccurrence]


def deduplicate_diagnostics(
    records: Iterable[RecordT],
    *,
    known_roots: Iterable[PurePath | str] = (),
    windows_case_insensitive: bool = True,
) -> DiagnosticDeduplicationResult[RecordT]:
    """Build a stable aggregation view while preserving every occurrence."""

    original = _record_tuple(records)
    roots = _normalize_roots(
        known_roots,
        windows_case_insensitive=windows_case_insensitive,
    )
    groups_by_key: dict[DiagnosticDuplicateKey, _MutableGroup[RecordT]] = {}
    ordered_groups: list[_MutableGroup[RecordT]] = []

    for record in original:
        key = diagnostic_duplicate_key(
            record,
            known_roots=roots,
            windows_case_insensitive=windows_case_insensitive,
            roots_are_normalized=True,
        )
        occurrence = diagnostic_occurrence(record)
        group = groups_by_key.get(key)
        if group is None:
            group = _MutableGroup(
                key=key,
                records=[record],
                provenance=[occurrence],
            )
            groups_by_key[key] = group
            ordered_groups.append(group)
        else:
            group.records.append(record)
            group.provenance.append(occurrence)

    groups = tuple(
        DeduplicatedDiagnostic(
            key=group.key,
            representative=group.records[0],
            occurrences=tuple(group.records),
            provenance=tuple(group.provenance),
            streams=_ordered_streams(item.stream for item in group.provenance),
        )
        for group in ordered_groups
    )
    return DiagnosticDeduplicationResult(records=original, groups=groups)


def diagnostic_duplicate_key(
    record: object,
    *,
    known_roots: Iterable[PurePath | str] = (),
    windows_case_insensitive: bool = True,
    roots_are_normalized: bool = False,
) -> DiagnosticDuplicateKey:
    """Return the conservative semantic key for one diagnostic record."""

    pattern_id = _enum_text(
        _attribute(record, "pattern_id"),
        field="pattern_id",
        max_length=256,
    )
    error_kind = _enum_text(
        _attribute(record, "error_kind"),
        field="error_kind",
        max_length=128,
    )
    source_path = _optional_attribute(record, "source_path")
    roots = (
        tuple(str(item) for item in known_roots)
        if roots_are_normalized
        else _normalize_roots(
            known_roots,
            windows_case_insensitive=windows_case_insensitive,
        )
    )
    normalized_source = normalize_source_path(
        source_path,
        known_roots=roots,
        windows_case_insensitive=windows_case_insensitive,
        roots_are_normalized=True,
    )
    normalized_signature = _normalized_signature(record, normalized_source)
    origin = _optional_enum_text(record, "origin", max_length=128)
    severity = _optional_enum_text(record, "severity", max_length=128)
    line = _optional_int_attribute(record, "line", allow_zero=False)
    column = _optional_int_attribute(record, "column", allow_zero=False)
    semantic_discriminator = _semantic_discriminator(record)
    return DiagnosticDuplicateKey(
        pattern_id=pattern_id,
        error_kind=error_kind,
        normalized_signature=normalized_signature,
        source_path_normalized=normalized_source,
        line=line,
        column=column,
        origin=origin,
        severity=severity,
        semantic_discriminator=semantic_discriminator,
    )


def diagnostic_occurrence(record: object) -> DiagnosticOccurrence:
    """Extract immutable provenance from one diagnostic record."""

    record_id = _enum_text(
        _attribute(record, "record_id"),
        field="record_id",
        max_length=512,
    )
    stream = _enum_text(
        _attribute(record, "stream"),
        field="stream",
        max_length=64,
    )
    start_line = _int_attribute(record, "start_line", allow_zero=False)
    end_line = _int_attribute(record, "end_line", allow_zero=False)
    raw_artifact_value = _first_present_attribute(
        record,
        ("raw_artifact_path", "evidence_path", "stream_path"),
    )
    raw_artifact_path = (
        None if raw_artifact_value is None else _path(raw_artifact_value, field="raw_artifact_path")
    )
    raw_excerpt_value = _optional_attribute(record, "raw_excerpt")
    raw_excerpt = (
        ""
        if raw_excerpt_value is None
        else _text(
            raw_excerpt_value,
            field="raw_excerpt",
            allow_empty=True,
            max_length=_MAX_TEXT_LENGTH,
        )
    )
    return DiagnosticOccurrence(
        record_id=record_id,
        stream=stream,
        start_line=start_line,
        end_line=end_line,
        raw_artifact_path=raw_artifact_path,
        raw_excerpt=raw_excerpt,
    )


def normalize_source_path(
    value: object,
    *,
    known_roots: Iterable[PurePath | str] = (),
    windows_case_insensitive: bool = True,
    roots_are_normalized: bool = False,
) -> str | None:
    """Normalize separators and explicit root prefixes without filesystem I/O."""

    if value is None:
        return None
    if isinstance(value, PurePath):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise TypeError("source_path must be a string, PurePath, or None")
    text = _required_text(text, field="source_path", max_length=32_768)
    normalized = _lexical_path(text)
    roots = (
        tuple(str(item) for item in known_roots)
        if roots_are_normalized
        else _normalize_roots(
            known_roots,
            windows_case_insensitive=windows_case_insensitive,
        )
    )
    for root in roots:
        relative = _relative_under_root(
            normalized,
            root,
            windows_case_insensitive=windows_case_insensitive,
        )
        if relative is not None:
            return relative or "."
    return normalized


def deduplicated_records(
    records: Iterable[RecordT],
    *,
    known_roots: Iterable[PurePath | str] = (),
    windows_case_insensitive: bool = True,
) -> tuple[RecordT, ...]:
    """Return first occurrences in stable input order."""

    return deduplicate_diagnostics(
        records,
        known_roots=known_roots,
        windows_case_insensitive=windows_case_insensitive,
    ).representatives


def duplicate_groups(
    records: Iterable[RecordT],
    *,
    known_roots: Iterable[PurePath | str] = (),
    windows_case_insensitive: bool = True,
) -> tuple[DeduplicatedDiagnostic[RecordT], ...]:
    """Return only groups containing more than one occurrence."""

    result = deduplicate_diagnostics(
        records,
        known_roots=known_roots,
        windows_case_insensitive=windows_case_insensitive,
    )
    return tuple(group for group in result.groups if group.is_duplicate)


def _normalized_signature(record: object, normalized_source: str | None) -> str:
    explicit = _optional_attribute(record, "normalized_signature")
    if explicit is not None:
        return _required_text(
            explicit,
            field="normalized_signature",
            max_length=_MAX_TEXT_LENGTH,
        )

    message_value = _attribute(record, "message")
    message = _stable_message(message_value)
    symbol = _optional_enum_text(record, "symbol", max_length=512)
    source_module = _optional_enum_text(record, "source_module", max_length=512)
    components = [message]
    if normalized_source is not None:
        components.append(f"source={normalized_source}")
    if source_module is not None:
        components.append(f"module={source_module}")
    if symbol is not None:
        components.append(f"symbol={symbol}")
    return "\n".join(components)


def _stable_message(value: object) -> str:
    text = (
        _required_text(
            value,
            field="message",
            max_length=_MAX_TEXT_LENGTH,
        )
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    lines = []
    for line in text.split("\n"):
        line = _HORIZONTAL_WHITESPACE_RE.sub(" ", line.strip())
        lines.append(line)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    stable = "\n".join(lines)
    if not stable:
        raise ValueError("message must contain non-whitespace diagnostic text")
    return stable


def _semantic_discriminator(record: object) -> str:
    pieces: list[str] = []
    for field_name in _SEMANTIC_FIELDS:
        value = _optional_attribute(record, field_name)
        if value is None:
            continue
        pieces.append(f"{field_name}={_stable_value(value)}")
    payload = "\x1f".join(pieces).encode("utf-8", errors="strict")
    return hashlib.sha256(payload).hexdigest()


def _stable_value(value: object) -> str:
    if isinstance(value, Enum):
        return _stable_value(value.value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("semantic diagnostic values must be finite")
        return repr(value)
    if isinstance(value, PurePath):
        return _lexical_path(str(value))
    if isinstance(value, str):
        return (
            _text(
                value,
                field="semantic diagnostic value",
                allow_empty=True,
                max_length=_MAX_TEXT_LENGTH,
            )
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
    if isinstance(value, Mapping):
        parts = []
        for key in sorted(value, key=lambda item: _stable_value(item)):
            parts.append(f"{_stable_value(key)}:{_stable_value(value[key])}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, (tuple, list)):
        return "[" + ",".join(_stable_value(item) for item in value) + "]"
    if isinstance(value, (set, frozenset)):
        return "[" + ",".join(sorted(_stable_value(item) for item in value)) + "]"
    raise TypeError("semantic diagnostic values must be scalar, path, mapping, or sequence")


def _normalize_roots(
    values: Iterable[PurePath | str],
    *,
    windows_case_insensitive: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, PurePath)):
        raise TypeError("known_roots must be an iterable of paths")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, PurePath):
            text = str(value)
        elif isinstance(value, str):
            text = value
        else:
            raise TypeError("known_roots must contain strings or PurePath values")
        root = _lexical_path(_required_text(text, field="known root", max_length=32_768)).rstrip(
            "/"
        )
        comparison = (
            root.casefold() if windows_case_insensitive and _looks_windows_path(root) else root
        )
        if comparison not in seen:
            seen.add(comparison)
            normalized.append(root)
    normalized.sort(key=lambda item: (-len(item), item.casefold(), item))
    return tuple(normalized)


def _lexical_path(text: str) -> str:
    text = text.strip().strip('"').replace("\\", "/")
    if not text:
        raise ValueError("path text must not be empty")
    is_windows = _looks_windows_path(text)
    path: PurePath = PureWindowsPath(text) if is_windows else PurePosixPath(text)
    normalized = path.as_posix()
    if is_windows and len(normalized) >= 2 and normalized[1] == ":":
        normalized = normalized[0].upper() + normalized[1:]
    return normalized.rstrip("/") or "/"


def _looks_windows_path(value: str) -> bool:
    return bool(_WINDOWS_ABSOLUTE_RE.match(value)) or "\\" in value


def _relative_under_root(
    path: str,
    root: str,
    *,
    windows_case_insensitive: bool,
) -> str | None:
    windows = _looks_windows_path(path) or _looks_windows_path(root)
    candidate = path.casefold() if windows and windows_case_insensitive else path
    base = root.casefold() if windows and windows_case_insensitive else root
    if candidate == base:
        return ""
    prefix = base.rstrip("/") + "/"
    if not candidate.startswith(prefix):
        return None
    return path[len(root.rstrip("/")) + 1 :]


def _ordered_streams(values: Iterable[str]) -> tuple[str, ...]:
    unique = set(values)
    return tuple(
        sorted(
            unique,
            key=lambda value: (
                _STREAM_ORDER.get(value.casefold(), 2),
                value.casefold(),
                value,
            ),
        )
    )


def _record_tuple(values: Iterable[RecordT]) -> tuple[RecordT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("records must be an iterable of diagnostic records")
    records = tuple(values)
    if len(records) > _MAX_RECORDS:
        raise ValueError("records exceeds the supported limit")
    return records


def _attribute(record: object, name: str) -> object:
    try:
        return getattr(record, name)
    except AttributeError as exc:
        raise TypeError(f"diagnostic record is missing required field {name!r}") from exc


def _optional_attribute(record: object, name: str) -> object | None:
    return getattr(record, name, None)


def _first_present_attribute(
    record: object,
    names: Sequence[str],
) -> object | None:
    for name in names:
        value: object | None = getattr(record, name, None)
        if value is not None:
            return value
    return None


def _int_attribute(record: object, name: str, *, allow_zero: bool) -> int:
    value = _attribute(record, name)
    if type(value) is not int:
        raise TypeError(f"diagnostic field {name!r} must be an integer")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"diagnostic field {name!r} must be {qualifier}")
    return value


def _optional_int_attribute(
    record: object,
    name: str,
    *,
    allow_zero: bool,
) -> int | None:
    value = _optional_attribute(record, name)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"diagnostic field {name!r} must be an integer or None")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"diagnostic field {name!r} must be {qualifier}")
    return value


def _optional_enum_text(
    record: object,
    name: str,
    *,
    max_length: int,
) -> str | None:
    value = _optional_attribute(record, name)
    if value is None:
        return None
    return _enum_text(value, field=name, max_length=max_length)


def _enum_text(value: object, *, field: str, max_length: int) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _required_text(value, field=field, max_length=max_length)


def _path(value: object, *, field: str) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, PurePath):
        path = Path(str(value))
    elif isinstance(value, str):
        path = Path(value)
    else:
        raise TypeError(f"{field} must be a path or string")
    if "\x00" in str(path):
        raise ValueError(f"{field} must not contain NUL")
    return path


def _positive_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be positive")
    return value


def _optional_non_negative_int(
    value: object,
    *,
    field: str,
    allow_zero: bool,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer or None")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be {qualifier}")
    return value


def _required_text(value: object, *, field: str, max_length: int) -> str:
    return _text(
        value,
        field=field,
        allow_empty=False,
        max_length=max_length,
    )


def _text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds the supported length limit")
    return value


__all__ = (
    "DeduplicatedDiagnostic",
    "DiagnosticDeduplicationResult",
    "DiagnosticDuplicateKey",
    "DiagnosticOccurrence",
    "deduplicate_diagnostics",
    "deduplicated_records",
    "diagnostic_duplicate_key",
    "diagnostic_occurrence",
    "duplicate_groups",
)
