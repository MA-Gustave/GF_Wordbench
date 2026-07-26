"""Deterministic stdout and stderr preparation for diagnostic parsing."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias

StreamMetadata: TypeAlias = Mapping[str, str]

_UTF8: Final[str] = "utf-8"
_MAX_STREAM_CHARACTERS: Final[int] = 64 * 1024 * 1024
_MAX_STREAM_BYTES: Final[int] = 64 * 1024 * 1024
_DEFAULT_SEPARATOR: Final[str] = "\n\n--- GF WORDBENCH STREAM: STDERR ---\n\n"
_EMPTY_METADATA: Final[StreamMetadata] = MappingProxyType({})


@unique
class DiagnosticStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


@unique
class StreamSelection(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    EITHER = "either"
    BOTH_STRUCTURE = "both-structure"


@unique
class StreamDecodePolicy(StrEnum):
    STRICT_UTF8 = "strict-utf8"
    REPLACE_INVALID_UTF8 = "replace-invalid-utf8"


@dataclass(frozen=True, slots=True)
class StreamDecodeIssue:
    stream: DiagnosticStream
    start: int
    end: int
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.stream, DiagnosticStream):
            raise TypeError("stream must be DiagnosticStream")
        if type(self.start) is not int or self.start < 0:
            raise ValueError("start must be a non-negative integer")
        if type(self.end) is not int or self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        reason = _require_text(
            self.reason,
            field_name="reason",
            allow_empty=False,
            max_length=1_000,
        )
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class StreamDocument:
    stream: DiagnosticStream
    text: str
    evidence_path: Path | None = None
    encoding: str = _UTF8
    byte_length: int | None = None
    truncated: bool = False
    decode_issues: tuple[StreamDecodeIssue, ...] = ()
    metadata: StreamMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.stream, DiagnosticStream):
            raise TypeError("stream must be DiagnosticStream")

        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            max_length=_MAX_STREAM_CHARACTERS,
        )
        encoding = _require_ascii_token(
            self.encoding,
            field_name="encoding",
            max_length=64,
        )

        evidence_path = self.evidence_path
        if evidence_path is not None:
            if not isinstance(evidence_path, Path):
                raise TypeError("evidence_path must be pathlib.Path or None")
            if "\x00" in str(evidence_path):
                raise ValueError("evidence_path must not contain NUL")

        byte_length = self.byte_length
        if byte_length is not None:
            if type(byte_length) is not int:
                raise TypeError("byte_length must be an integer or None")
            if byte_length < 0:
                raise ValueError("byte_length must be non-negative")

        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a bool")

        decode_issues = tuple(self.decode_issues)
        for issue in decode_issues:
            if not isinstance(issue, StreamDecodeIssue):
                raise TypeError(
                    "decode_issues must contain StreamDecodeIssue values"
                )
            if issue.stream is not self.stream:
                raise ValueError(
                    "decode issue stream must match the document stream"
                )

        metadata = _freeze_metadata(self.metadata)

        object.__setattr__(self, "text", text)
        object.__setattr__(self, "encoding", encoding)
        object.__setattr__(self, "evidence_path", evidence_path)
        object.__setattr__(self, "decode_issues", decode_issues)
        object.__setattr__(self, "metadata", metadata)

    @property
    def is_empty(self) -> bool:
        return self.text == ""

    @property
    def line_count(self) -> int:
        return count_text_lines(self.text)

    def lines(self) -> tuple[StreamLine, ...]:
        return tuple(iter_stream_lines(self))


@dataclass(frozen=True, slots=True)
class StreamLine:
    stream: DiagnosticStream
    line_number: int
    text: str
    start_offset: int
    end_offset: int
    terminated: bool
    evidence_path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stream, DiagnosticStream):
            raise TypeError("stream must be DiagnosticStream")
        if type(self.line_number) is not int or self.line_number < 1:
            raise ValueError("line_number must be a positive integer")

        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            max_length=_MAX_STREAM_CHARACTERS,
        )

        if type(self.start_offset) is not int or self.start_offset < 0:
            raise ValueError("start_offset must be a non-negative integer")
        if type(self.end_offset) is not int or self.end_offset < self.start_offset:
            raise ValueError(
                "end_offset must be greater than or equal to start_offset"
            )
        if type(self.terminated) is not bool:
            raise TypeError("terminated must be a bool")

        evidence_path = self.evidence_path
        if evidence_path is not None and not isinstance(evidence_path, Path):
            raise TypeError("evidence_path must be pathlib.Path or None")

        object.__setattr__(self, "text", text)

    @property
    def source_key(self) -> tuple[str, int]:
        return self.stream.value, self.line_number


@dataclass(frozen=True, slots=True)
class StreamBundle:
    stdout: StreamDocument
    stderr: StreamDocument

    def __post_init__(self) -> None:
        if not isinstance(self.stdout, StreamDocument):
            raise TypeError("stdout must be StreamDocument")
        if not isinstance(self.stderr, StreamDocument):
            raise TypeError("stderr must be StreamDocument")
        if self.stdout.stream is not DiagnosticStream.STDOUT:
            raise ValueError("stdout document must use DiagnosticStream.STDOUT")
        if self.stderr.stream is not DiagnosticStream.STDERR:
            raise ValueError("stderr document must use DiagnosticStream.STDERR")

    @property
    def has_text(self) -> bool:
        return bool(self.stdout.text or self.stderr.text)

    @property
    def truncated(self) -> bool:
        return self.stdout.truncated or self.stderr.truncated

    @property
    def has_decode_issues(self) -> bool:
        return bool(self.stdout.decode_issues or self.stderr.decode_issues)

    def documents(
        self,
        selection: StreamSelection | str = StreamSelection.EITHER,
    ) -> tuple[StreamDocument, ...]:
        canonical = _coerce_selection(selection)
        if canonical is StreamSelection.STDOUT:
            return (self.stdout,)
        if canonical is StreamSelection.STDERR:
            return (self.stderr,)
        return self.stdout, self.stderr

    def lines(
        self,
        selection: StreamSelection | str = StreamSelection.EITHER,
    ) -> tuple[StreamLine, ...]:
        return tuple(
            line
            for document in self.documents(selection)
            for line in iter_stream_lines(document)
        )


@dataclass(frozen=True, slots=True)
class AnalysisSegment:
    stream: DiagnosticStream
    text: str
    combined_start: int
    combined_end: int
    source_start: int
    source_end: int

    def __post_init__(self) -> None:
        if not isinstance(self.stream, DiagnosticStream):
            raise TypeError("stream must be DiagnosticStream")

        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            max_length=_MAX_STREAM_CHARACTERS,
        )

        for name in (
            "combined_start",
            "combined_end",
            "source_start",
            "source_end",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        if self.combined_end < self.combined_start:
            raise ValueError("combined_end must not precede combined_start")
        if self.source_end < self.source_start:
            raise ValueError("source_end must not precede source_start")
        if self.combined_end - self.combined_start != len(text):
            raise ValueError("combined offsets must span the segment text")
        if self.source_end - self.source_start != len(text):
            raise ValueError("source offsets must span the segment text")

        object.__setattr__(self, "text", text)


@dataclass(frozen=True, slots=True)
class CombinedAnalysisView:
    text: str
    segments: tuple[AnalysisSegment, ...]
    separator: str
    stream_order: tuple[DiagnosticStream, ...] = (
        DiagnosticStream.STDOUT,
        DiagnosticStream.STDERR,
    )
    chronology_known: bool = False

    def __post_init__(self) -> None:
        text = _require_text(
            self.text,
            field_name="text",
            allow_empty=True,
            max_length=2 * _MAX_STREAM_CHARACTERS + len(_DEFAULT_SEPARATOR),
        )
        separator = _require_text(
            self.separator,
            field_name="separator",
            allow_empty=False,
            max_length=4_096,
        )

        segments = tuple(self.segments)
        for segment in segments:
            if not isinstance(segment, AnalysisSegment):
                raise TypeError(
                    "segments must contain AnalysisSegment values"
                )

        stream_order = tuple(self.stream_order)
        if stream_order != (
            DiagnosticStream.STDOUT,
            DiagnosticStream.STDERR,
        ):
            raise ValueError(
                "combined analysis stream order must be stdout then stderr"
            )
        if type(self.chronology_known) is not bool:
            raise TypeError("chronology_known must be a bool")
        if self.chronology_known:
            raise ValueError(
                "combined analysis view must not claim cross-stream chronology"
            )

        previous_end = 0
        seen_streams: set[DiagnosticStream] = set()
        for segment in segments:
            if segment.stream in seen_streams:
                raise ValueError(
                    "combined analysis view may contain one segment per stream"
                )
            if segment.combined_start < previous_end:
                raise ValueError("analysis segments must not overlap")
            if text[
                segment.combined_start : segment.combined_end
            ] != segment.text:
                raise ValueError(
                    "analysis segment text must match the combined view"
                )
            previous_end = segment.combined_end
            seen_streams.add(segment.stream)

        object.__setattr__(self, "text", text)
        object.__setattr__(self, "segments", segments)
        object.__setattr__(self, "separator", separator)
        object.__setattr__(self, "stream_order", stream_order)

    def source_at(self, offset: int) -> tuple[DiagnosticStream, int] | None:
        if type(offset) is not int:
            raise TypeError("offset must be an integer")
        if offset < 0 or offset > len(self.text):
            raise ValueError("offset is outside the combined analysis view")

        for segment in self.segments:
            if segment.combined_start <= offset < segment.combined_end:
                source_offset = segment.source_start + (
                    offset - segment.combined_start
                )
                return segment.stream, source_offset
        return None

    def segment_for(
        self,
        stream: DiagnosticStream | str,
    ) -> AnalysisSegment | None:
        canonical = _coerce_stream(stream)
        for segment in self.segments:
            if segment.stream is canonical:
                return segment
        return None


def make_stream_bundle(
    stdout: str,
    stderr: str,
    *,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    stdout_truncated: bool = False,
    stderr_truncated: bool = False,
    metadata: StreamMetadata | None = None,
) -> StreamBundle:
    shared_metadata = _EMPTY_METADATA if metadata is None else metadata
    return StreamBundle(
        stdout=StreamDocument(
            stream=DiagnosticStream.STDOUT,
            text=stdout,
            evidence_path=stdout_path,
            byte_length=len(stdout.encode(_UTF8)),
            truncated=stdout_truncated,
            metadata=shared_metadata,
        ),
        stderr=StreamDocument(
            stream=DiagnosticStream.STDERR,
            text=stderr,
            evidence_path=stderr_path,
            byte_length=len(stderr.encode(_UTF8)),
            truncated=stderr_truncated,
            metadata=shared_metadata,
        ),
    )


def decode_stream_bytes(
    stream: DiagnosticStream | str,
    data: bytes,
    *,
    evidence_path: Path | None = None,
    policy: StreamDecodePolicy | str = StreamDecodePolicy.STRICT_UTF8,
    truncated: bool = False,
    metadata: StreamMetadata | None = None,
) -> StreamDocument:
    canonical_stream = _coerce_stream(stream)
    canonical_policy = _coerce_decode_policy(policy)

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) > _MAX_STREAM_BYTES:
        raise ValueError("stream bytes exceed the supported limit")
    if type(truncated) is not bool:
        raise TypeError("truncated must be a bool")

    issues: tuple[StreamDecodeIssue, ...] = ()
    if canonical_policy is StreamDecodePolicy.STRICT_UTF8:
        text = data.decode(_UTF8, errors="strict")
    else:
        try:
            text = data.decode(_UTF8, errors="strict")
        except UnicodeDecodeError:
            issues = _collect_decode_issues(canonical_stream, data)
            text = data.decode(_UTF8, errors="replace")

    return StreamDocument(
        stream=canonical_stream,
        text=text,
        evidence_path=evidence_path,
        encoding=_UTF8,
        byte_length=len(data),
        truncated=truncated,
        decode_issues=issues,
        metadata=_EMPTY_METADATA if metadata is None else metadata,
    )


def iter_stream_lines(document: StreamDocument) -> Iterator[StreamLine]:
    if not isinstance(document, StreamDocument):
        raise TypeError("document must be StreamDocument")

    text = document.text
    if not text:
        return

    line_number = 1
    offset = 0
    length = len(text)

    while offset < length:
        line_end, content_end, terminated = _locate_line_end(text, offset)
        yield StreamLine(
            stream=document.stream,
            line_number=line_number,
            text=text[offset:content_end],
            start_offset=offset,
            end_offset=content_end,
            terminated=terminated,
            evidence_path=document.evidence_path,
        )
        offset = line_end
        line_number += 1


def count_text_lines(text: str) -> int:
    canonical = _require_text(
        text,
        field_name="text",
        allow_empty=True,
        max_length=_MAX_STREAM_CHARACTERS,
    )
    if not canonical:
        return 0
    return sum(1 for _ in _iter_line_bounds(canonical))


def build_combined_analysis_view(
    bundle: StreamBundle,
    *,
    separator: str = _DEFAULT_SEPARATOR,
    include_empty_streams: bool = True,
) -> CombinedAnalysisView:
    if not isinstance(bundle, StreamBundle):
        raise TypeError("bundle must be StreamBundle")
    if type(include_empty_streams) is not bool:
        raise TypeError("include_empty_streams must be a bool")

    canonical_separator = _require_text(
        separator,
        field_name="separator",
        allow_empty=False,
        max_length=4_096,
    )

    documents = (bundle.stdout, bundle.stderr)
    included = tuple(
        document
        for document in documents
        if include_empty_streams or document.text
    )

    if not included:
        return CombinedAnalysisView(
            text="",
            segments=(),
            separator=canonical_separator,
        )

    pieces: list[str] = []
    segments: list[AnalysisSegment] = []
    combined_offset = 0

    for index, document in enumerate(included):
        if index:
            pieces.append(canonical_separator)
            combined_offset += len(canonical_separator)

        pieces.append(document.text)
        segment_end = combined_offset + len(document.text)
        segments.append(
            AnalysisSegment(
                stream=document.stream,
                text=document.text,
                combined_start=combined_offset,
                combined_end=segment_end,
                source_start=0,
                source_end=len(document.text),
            )
        )
        combined_offset = segment_end

    return CombinedAnalysisView(
        text="".join(pieces),
        segments=tuple(segments),
        separator=canonical_separator,
    )


def select_stream_documents(
    bundle: StreamBundle,
    selection: StreamSelection | str,
) -> tuple[StreamDocument, ...]:
    if not isinstance(bundle, StreamBundle):
        raise TypeError("bundle must be StreamBundle")
    return bundle.documents(selection)


def select_stream_lines(
    bundle: StreamBundle,
    selection: StreamSelection | str,
    *,
    include_empty_lines: bool = True,
) -> tuple[StreamLine, ...]:
    if not isinstance(bundle, StreamBundle):
        raise TypeError("bundle must be StreamBundle")
    if type(include_empty_lines) is not bool:
        raise TypeError("include_empty_lines must be a bool")

    lines = bundle.lines(selection)
    if include_empty_lines:
        return lines
    return tuple(line for line in lines if line.text)


def line_excerpt(
    lines: Iterable[StreamLine],
    anchor_index: int,
    *,
    before: int = 2,
    after: int = 2,
) -> tuple[StreamLine, ...]:
    if isinstance(lines, (str, bytes)):
        raise TypeError("lines must be an iterable of StreamLine values")
    prepared = tuple(lines)
    if any(not isinstance(line, StreamLine) for line in prepared):
        raise TypeError("lines must contain StreamLine values")

    if type(anchor_index) is not int:
        raise TypeError("anchor_index must be an integer")
    if anchor_index < 0 or anchor_index >= len(prepared):
        raise IndexError("anchor_index is outside the line collection")

    for name, value in (("before", before), ("after", after)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    start = max(0, anchor_index - before)
    end = min(len(prepared), anchor_index + after + 1)
    return prepared[start:end]


def find_line_index(
    lines: Iterable[StreamLine],
    *,
    stream: DiagnosticStream | str,
    line_number: int,
) -> int | None:
    canonical_stream = _coerce_stream(stream)
    if type(line_number) is not int or line_number < 1:
        raise ValueError("line_number must be a positive integer")

    for index, line in enumerate(lines):
        if not isinstance(line, StreamLine):
            raise TypeError("lines must contain StreamLine values")
        if line.stream is canonical_stream and line.line_number == line_number:
            return index
    return None


def _collect_decode_issues(
    stream: DiagnosticStream,
    data: bytes,
) -> tuple[StreamDecodeIssue, ...]:
    issues: list[StreamDecodeIssue] = []
    cursor = 0

    while cursor < len(data):
        try:
            data[cursor:].decode(_UTF8, errors="strict")
            break
        except UnicodeDecodeError as exc:
            start = cursor + exc.start
            end = cursor + max(exc.end, exc.start + 1)
            issues.append(
                StreamDecodeIssue(
                    stream=stream,
                    start=start,
                    end=end,
                    reason=exc.reason,
                )
            )
            cursor = end

    return tuple(issues)


def _iter_line_bounds(text: str) -> Iterator[tuple[int, int, int, bool]]:
    offset = 0
    line_number = 1
    while offset < len(text):
        line_end, content_end, terminated = _locate_line_end(text, offset)
        yield line_number, offset, content_end, terminated
        offset = line_end
        line_number += 1


def _locate_line_end(
    text: str,
    start: int,
) -> tuple[int, int, bool]:
    newline = text.find("\n", start)
    carriage = text.find("\r", start)

    candidates = tuple(
        position
        for position in (newline, carriage)
        if position >= 0
    )
    if not candidates:
        return len(text), len(text), False

    content_end = min(candidates)
    if text[content_end] == "\r" and content_end + 1 < len(text):
        if text[content_end + 1] == "\n":
            return content_end + 2, content_end, True
    return content_end + 1, content_end, True


def _freeze_metadata(values: StreamMetadata) -> StreamMetadata:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping")

    copied: dict[str, str] = {}
    for key, value in values.items():
        canonical_key = _require_ascii_token(
            key,
            field_name="metadata key",
            max_length=128,
        )
        canonical_value = _require_text(
            value,
            field_name=f"metadata[{canonical_key!r}]",
            allow_empty=True,
            max_length=4_096,
        )
        copied[canonical_key] = canonical_value

    return MappingProxyType(
        {key: copied[key] for key in sorted(copied)}
    )


def _coerce_stream(
    value: DiagnosticStream | str,
) -> DiagnosticStream:
    if isinstance(value, DiagnosticStream):
        return value
    if not isinstance(value, str):
        raise TypeError("stream must be DiagnosticStream or string")
    try:
        return DiagnosticStream(value)
    except ValueError as exc:
        raise ValueError(f"unknown diagnostic stream: {value!r}") from exc


def _coerce_selection(
    value: StreamSelection | str,
) -> StreamSelection:
    if isinstance(value, StreamSelection):
        return value
    if not isinstance(value, str):
        raise TypeError("selection must be StreamSelection or string")
    try:
        return StreamSelection(value)
    except ValueError as exc:
        raise ValueError(f"unknown stream selection: {value!r}") from exc


def _coerce_decode_policy(
    value: StreamDecodePolicy | str,
) -> StreamDecodePolicy:
    if isinstance(value, StreamDecodePolicy):
        return value
    if not isinstance(value, str):
        raise TypeError("policy must be StreamDecodePolicy or string")
    try:
        return StreamDecodePolicy(value)
    except ValueError as exc:
        raise ValueError(f"unknown stream decode policy: {value!r}") from exc


def _require_ascii_token(
    value: object,
    *,
    field_name: str,
    max_length: int,
) -> str:
    text = _require_text(
        value,
        field_name=field_name,
        allow_empty=False,
        max_length=max_length,
    )
    if not text.isascii():
        raise ValueError(f"{field_name} must use ASCII characters only")
    if any(character.isspace() for character in text):
        raise ValueError(f"{field_name} must not contain whitespace")
    return text


def _require_text(
    value: object,
    *,
    field_name: str,
    allow_empty: bool,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length limit")
    return value


__all__ = (
    "AnalysisSegment",
    "CombinedAnalysisView",
    "DiagnosticStream",
    "StreamBundle",
    "StreamDecodeIssue",
    "StreamDecodePolicy",
    "StreamDocument",
    "StreamLine",
    "StreamMetadata",
    "StreamSelection",
    "build_combined_analysis_view",
    "count_text_lines",
    "decode_stream_bytes",
    "find_line_index",
    "iter_stream_lines",
    "line_excerpt",
    "make_stream_bundle",
    "select_stream_documents",
    "select_stream_lines",
)
