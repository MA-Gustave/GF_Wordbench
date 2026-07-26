from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from gf_wordbench.diagnostics.patterns.common import (
        DiagnosticPatternDefinition,
    )
    from gf_wordbench.diagnostics.tools.models import (
        DiagnosticToolRequest,
        DiagnosticToolResult,
    )
    from gf_wordbench.infrastructure.process.models import ProcessEventSink
    from gf_wordbench.infrastructure.process.termination import (
        CancellationToken,
    )


@dataclass(frozen=True, slots=True)
class EvidenceMetadata:
    path: Path
    size_bytes: int
    modified_ns: int | None
    is_file: bool
    sha256: str | None = None

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        size_bytes = _non_negative_int(self.size_bytes, "size_bytes")
        modified_ns = _optional_non_negative_int(
            self.modified_ns,
            "modified_ns",
        )
        if type(self.is_file) is not bool:
            raise TypeError("is_file must be a boolean")
        sha256 = _optional_sha256(self.sha256)
        if sha256 is not None and not self.is_file:
            raise ValueError("sha256 is valid only for files")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "size_bytes", size_bytes)
        object.__setattr__(self, "modified_ns", modified_ns)
        object.__setattr__(self, "sha256", sha256)


@dataclass(frozen=True, slots=True)
class EvidenceReadRequest:
    path: Path
    root: Path
    max_bytes: int
    offset: int = 0

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        root = _absolute_path(self.root, "root")
        max_bytes = _positive_int(self.max_bytes, "max_bytes")
        offset = _non_negative_int(self.offset, "offset")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "max_bytes", max_bytes)
        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True, slots=True)
class EvidenceTextRequest:
    path: Path
    root: Path
    max_bytes: int
    encoding: str = "utf-8"
    errors: str = "strict"
    offset: int = 0

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        root = _absolute_path(self.root, "root")
        max_bytes = _positive_int(self.max_bytes, "max_bytes")
        encoding = _required_text(self.encoding, "encoding")
        errors = _required_text(self.errors, "errors")
        if errors not in {
            "strict",
            "replace",
            "surrogateescape",
        }:
            raise ValueError(
                "errors must be strict, replace, or surrogateescape"
            )
        offset = _non_negative_int(self.offset, "offset")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "max_bytes", max_bytes)
        object.__setattr__(self, "encoding", encoding)
        object.__setattr__(self, "errors", errors)
        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True, slots=True)
class EvidenceBytes:
    path: Path
    data: bytes
    offset: int
    total_size_bytes: int
    truncated: bool

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        if not isinstance(self.data, bytes):
            raise TypeError("data must be bytes")
        offset = _non_negative_int(self.offset, "offset")
        total_size_bytes = _non_negative_int(
            self.total_size_bytes,
            "total_size_bytes",
        )
        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a boolean")
        if offset > total_size_bytes:
            raise ValueError("offset must not exceed total_size_bytes")
        if len(self.data) > total_size_bytes - offset:
            raise ValueError("data exceeds the declared evidence size")
        expected_truncated = (
            offset + len(self.data) < total_size_bytes
        )
        if self.truncated is not expected_truncated:
            raise ValueError(
                "truncated must reflect unread evidence bytes"
            )
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "offset", offset)
        object.__setattr__(
            self,
            "total_size_bytes",
            total_size_bytes,
        )


@dataclass(frozen=True, slots=True)
class EvidenceText:
    path: Path
    text: str
    encoding: str
    decoding_lossy: bool
    offset: int
    consumed_bytes: int
    total_size_bytes: int
    truncated: bool

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        text = _text(self.text, "text")
        encoding = _required_text(self.encoding, "encoding")
        if type(self.decoding_lossy) is not bool:
            raise TypeError("decoding_lossy must be a boolean")
        offset = _non_negative_int(self.offset, "offset")
        consumed_bytes = _non_negative_int(
            self.consumed_bytes,
            "consumed_bytes",
        )
        total_size_bytes = _non_negative_int(
            self.total_size_bytes,
            "total_size_bytes",
        )
        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a boolean")
        if offset > total_size_bytes:
            raise ValueError("offset must not exceed total_size_bytes")
        if consumed_bytes > total_size_bytes - offset:
            raise ValueError(
                "consumed_bytes exceeds the declared evidence size"
            )
        expected_truncated = (
            offset + consumed_bytes < total_size_bytes
        )
        if self.truncated is not expected_truncated:
            raise ValueError(
                "truncated must reflect unread evidence bytes"
            )
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "encoding", encoding)
        object.__setattr__(self, "offset", offset)
        object.__setattr__(self, "consumed_bytes", consumed_bytes)
        object.__setattr__(
            self,
            "total_size_bytes",
            total_size_bytes,
        )


@dataclass(frozen=True, slots=True)
class PatternSelection:
    operation_kind: str
    source_streams: tuple[str, ...]
    gf_version: str | None = None
    include_fallbacks: bool = True

    def __post_init__(self) -> None:
        operation_kind = _required_text(
            self.operation_kind,
            "operation_kind",
        )
        source_streams = _unique_text_tuple(
            self.source_streams,
            "source_streams",
        )
        if not source_streams:
            raise ValueError("source_streams must not be empty")
        invalid_streams = tuple(
            stream
            for stream in source_streams
            if stream not in {"stdout", "stderr", "process", "derived"}
        )
        if invalid_streams:
            raise ValueError(
                "unsupported source streams: "
                + ", ".join(invalid_streams)
            )
        gf_version = (
            None
            if self.gf_version is None
            else _required_text(self.gf_version, "gf_version")
        )
        if type(self.include_fallbacks) is not bool:
            raise TypeError("include_fallbacks must be a boolean")
        object.__setattr__(
            self,
            "operation_kind",
            operation_kind,
        )
        object.__setattr__(
            self,
            "source_streams",
            source_streams,
        )
        object.__setattr__(self, "gf_version", gf_version)


@runtime_checkable
class EvidenceReader(Protocol):
    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
    ) -> Path:
        ...

    def metadata(
        self,
        path: Path,
        *,
        root: Path,
        include_sha256: bool = False,
    ) -> EvidenceMetadata:
        ...

    def read_bytes(
        self,
        request: EvidenceReadRequest,
    ) -> EvidenceBytes:
        ...

    def read_text(
        self,
        request: EvidenceTextRequest,
    ) -> EvidenceText:
        ...


@runtime_checkable
class DiagnosticPatternRegistry(Protocol):
    @property
    def catalog_version(self) -> str:
        ...

    @property
    def parser_version(self) -> str:
        ...

    def get(
        self,
        pattern_id: str,
    ) -> DiagnosticPatternDefinition:
        ...

    def select(
        self,
        selection: PatternSelection,
    ) -> tuple[DiagnosticPatternDefinition, ...]:
        ...

    def pattern_ids(self) -> tuple[str, ...]:
        ...


@runtime_checkable
class DiagnosticToolPort(Protocol):
    def execute(
        self,
        request: DiagnosticToolRequest,
        *,
        cancellation: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> DiagnosticToolResult:
        ...


def validate_pattern_registry(
    registry: DiagnosticPatternRegistry,
) -> tuple[str, ...]:
    if not isinstance(registry, DiagnosticPatternRegistry):
        raise TypeError(
            "registry must satisfy DiagnosticPatternRegistry"
        )
    catalog_version = _required_text(
        registry.catalog_version,
        "catalog_version",
    )
    parser_version = _required_text(
        registry.parser_version,
        "parser_version",
    )
    pattern_ids = _unique_text_tuple(
        registry.pattern_ids(),
        "pattern_ids",
    )
    if not pattern_ids:
        raise ValueError("pattern registry must not be empty")
    for pattern_id in pattern_ids:
        definition = registry.get(pattern_id)
        actual = getattr(definition, "pattern_id", None)
        if actual != pattern_id:
            raise ValueError(
                f"registry identity mismatch for {pattern_id!r}"
            )
    return (catalog_version, parser_version, *pattern_ids)


def _absolute_path(value: object, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return value


def _required_text(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if not text.strip():
        raise ValueError(f"{field_name} must not be empty")
    if text != text.strip():
        raise ValueError(
            f"{field_name} must not have outer whitespace"
        )
    return text


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(
            f"{field_name} must be non-negative"
        )
    return value


def _optional_non_negative_int(
    value: object,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    return _non_negative_int(value, field_name)


def _optional_sha256(value: object) -> str | None:
    if value is None:
        return None
    text = _required_text(value, "sha256").lower()
    if len(text) != 64 or any(
        character not in "0123456789abcdef"
        for character in text
    ):
        raise ValueError(
            "sha256 must contain 64 lowercase hexadecimal characters"
        )
    return text


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            f"{field_name} must be an iterable of strings"
        )
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _required_text(value, f"{field_name} item")
        if text in seen:
            raise ValueError(
                f"{field_name} must not contain duplicates"
            )
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


__all__ = (
    "DiagnosticPatternRegistry",
    "DiagnosticToolPort",
    "EvidenceBytes",
    "EvidenceMetadata",
    "EvidenceReadRequest",
    "EvidenceReader",
    "EvidenceText",
    "EvidenceTextRequest",
    "PatternSelection",
    "validate_pattern_registry",
)
