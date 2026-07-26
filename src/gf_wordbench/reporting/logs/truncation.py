from __future__ import annotations

import codecs
import os
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, TypeAlias

_DEFAULT_ENCODING: Final[str] = "utf-8"
_DEFAULT_MARKER_TEMPLATE: Final[str] = (
    "<TRUNCATED: retained {retained_bytes} of {size_qualifier}"
    "{observed_bytes} bytes; strategy={strategy}; reason={reason}>"
)
_SUPPORTED_DECODE_ERRORS: Final[frozenset[str]] = frozenset(
    {"strict", "replace", "ignore", "surrogateescape"}
)
PathLike: TypeAlias = str | os.PathLike[str]


@unique
class RetentionStrategy(StrEnum):
    FULL = "full"
    HEAD = "head"
    TAIL = "tail"
    HEAD_TAIL = "head_tail"
    AROUND_LINE = "around_line"


TruncationStrategy = RetentionStrategy


@unique
class TruncationReason(StrEnum):
    OUTPUT_LIMIT = "output_limit"
    REPORT_LIMIT = "report_limit"
    AGGREGATE_LIMIT = "aggregate_limit"
    AI_EXCERPT_LIMIT = "ai_excerpt_limit"
    DETAIL_EXCERPT_LIMIT = "detail_excerpt_limit"
    DIAGNOSTIC_EXCERPT_LIMIT = "diagnostic_excerpt_limit"
    EXPLICIT_POLICY = "explicit_policy"


@dataclass(frozen=True, slots=True)
class TruncationPolicy:
    maximum_bytes: int
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY
    head_bytes: int | None = None
    tail_bytes: int | None = None

    def __post_init__(self) -> None:
        _require_non_negative_int(self.maximum_bytes, "maximum_bytes")
        if not isinstance(self.strategy, RetentionStrategy):
            raise TypeError("strategy must be RetentionStrategy")
        reason = _coerce_reason(self.reason)
        object.__setattr__(self, "reason", reason)
        if self.strategy is RetentionStrategy.AROUND_LINE:
            raise ValueError("AROUND_LINE is valid only for line excerpts")
        if self.head_bytes is not None:
            _require_non_negative_int(self.head_bytes, "head_bytes")
        if self.tail_bytes is not None:
            _require_non_negative_int(self.tail_bytes, "tail_bytes")
        if self.strategy is not RetentionStrategy.HEAD_TAIL and (
            self.head_bytes is not None or self.tail_bytes is not None
        ):
            raise ValueError("head_bytes and tail_bytes require HEAD_TAIL strategy")
        if self.strategy is RetentionStrategy.HEAD_TAIL:
            head, tail = self.partition()
            if head + tail != self.maximum_bytes:
                raise ValueError("head and tail allocation must equal maximum_bytes")

    def partition(self) -> tuple[int, int]:
        if self.strategy is not RetentionStrategy.HEAD_TAIL:
            raise ValueError("partition is available only for HEAD_TAIL strategy")
        if self.head_bytes is None and self.tail_bytes is None:
            head = (self.maximum_bytes + 1) // 2
            return head, self.maximum_bytes - head
        if self.head_bytes is None:
            assert self.tail_bytes is not None
            if self.tail_bytes > self.maximum_bytes:
                raise ValueError("tail_bytes exceeds maximum_bytes")
            return self.maximum_bytes - self.tail_bytes, self.tail_bytes
        if self.tail_bytes is None:
            if self.head_bytes > self.maximum_bytes:
                raise ValueError("head_bytes exceeds maximum_bytes")
            return self.head_bytes, self.maximum_bytes - self.head_bytes
        if self.head_bytes + self.tail_bytes != self.maximum_bytes:
            raise ValueError("head_bytes plus tail_bytes must equal maximum_bytes")
        return self.head_bytes, self.tail_bytes


@dataclass(frozen=True, slots=True)
class TruncationMetadata:
    truncated: bool
    observed_bytes: int
    retained_bytes: int
    retention_strategy: RetentionStrategy
    reason: str
    original_size_known: bool = True

    def __post_init__(self) -> None:
        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a boolean")
        _require_non_negative_int(self.observed_bytes, "observed_bytes")
        _require_non_negative_int(self.retained_bytes, "retained_bytes")
        if self.retained_bytes > self.observed_bytes:
            raise ValueError("retained_bytes cannot exceed observed_bytes")
        if not isinstance(self.retention_strategy, RetentionStrategy):
            raise TypeError("retention_strategy must be RetentionStrategy")
        reason = _require_text(self.reason, "reason")
        if type(self.original_size_known) is not bool:
            raise TypeError("original_size_known must be a boolean")
        if self.truncated != (self.retained_bytes < self.observed_bytes):
            raise ValueError("truncated must reflect retained and observed byte counts")
        if not self.truncated and self.retention_strategy is not RetentionStrategy.FULL:
            object.__setattr__(self, "retention_strategy", RetentionStrategy.FULL)
        object.__setattr__(self, "reason", reason)

    @property
    def omitted_bytes(self) -> int:
        return self.observed_bytes - self.retained_bytes

    @property
    def original_or_observed_bytes(self) -> int:
        return self.observed_bytes

    @property
    def size_qualifier(self) -> str:
        return "" if self.original_size_known else "at least "


@dataclass(frozen=True, slots=True)
class ByteTruncationResult:
    data: bytes
    metadata: TruncationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes):
            raise TypeError("data must be bytes")
        if not isinstance(self.metadata, TruncationMetadata):
            raise TypeError("metadata must be TruncationMetadata")
        if len(self.data) != self.metadata.retained_bytes:
            raise ValueError("data length must equal retained_bytes")


@dataclass(frozen=True, slots=True)
class TextTruncationResult:
    text: str
    metadata: TruncationMetadata
    encoding: str = _DEFAULT_ENCODING
    decode_lossy: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not isinstance(self.metadata, TruncationMetadata):
            raise TypeError("metadata must be TruncationMetadata")
        encoding = _normalize_encoding(self.encoding)
        if type(self.decode_lossy) is not bool:
            raise TypeError("decode_lossy must be a boolean")
        object.__setattr__(self, "encoding", encoding)

    @property
    def marker(self) -> str | None:
        if not self.metadata.truncated:
            return None
        return render_truncation_marker(self.metadata)


@dataclass(frozen=True, slots=True)
class LineTruncationMetadata:
    truncated: bool
    observed_lines: int
    retained_lines: int
    start_line: int | None
    end_line: int | None
    retention_strategy: RetentionStrategy
    reason: str
    retained_ranges: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a boolean")
        _require_non_negative_int(self.observed_lines, "observed_lines")
        _require_non_negative_int(self.retained_lines, "retained_lines")
        if self.retained_lines > self.observed_lines:
            raise ValueError("retained_lines cannot exceed observed_lines")
        if not isinstance(self.retention_strategy, RetentionStrategy):
            raise TypeError("retention_strategy must be RetentionStrategy")
        reason = _require_text(self.reason, "reason")
        ranges = _normalize_line_ranges(
            self.retained_ranges,
            start_line=self.start_line,
            end_line=self.end_line,
            retained_lines=self.retained_lines,
            observed_lines=self.observed_lines,
        )
        if self.truncated != (self.retained_lines < self.observed_lines):
            raise ValueError("truncated must reflect retained and observed line counts")
        if not self.truncated and self.retention_strategy is not RetentionStrategy.FULL:
            object.__setattr__(self, "retention_strategy", RetentionStrategy.FULL)
        object.__setattr__(self, "start_line", ranges[0][0] if ranges else None)
        object.__setattr__(self, "end_line", ranges[-1][1] if ranges else None)
        object.__setattr__(self, "retained_ranges", ranges)
        object.__setattr__(self, "reason", reason)

    @property
    def omitted_lines(self) -> int:
        return self.observed_lines - self.retained_lines

    @property
    def contiguous(self) -> bool:
        return len(self.retained_ranges) <= 1


@dataclass(frozen=True, slots=True)
class LineTruncationResult:
    text: str
    metadata: LineTruncationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not isinstance(self.metadata, LineTruncationMetadata):
            raise TypeError("metadata must be LineTruncationMetadata")


def truncate_bytes(
    data: bytes | bytearray | memoryview,
    maximum_bytes: int,
    *,
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL,
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY,
    head_bytes: int | None = None,
    tail_bytes: int | None = None,
) -> ByteTruncationResult:
    payload = bytes(data)
    policy = TruncationPolicy(
        maximum_bytes=maximum_bytes,
        strategy=strategy,
        reason=reason,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    observed = len(payload)
    if observed <= maximum_bytes:
        return ByteTruncationResult(
            data=payload,
            metadata=_metadata(
                observed=observed,
                retained=observed,
                strategy=RetentionStrategy.FULL,
                reason=policy.reason,
            ),
        )
    retained = _retain_from_bytes(payload, policy)
    return ByteTruncationResult(
        data=retained,
        metadata=_metadata(
            observed=observed,
            retained=len(retained),
            strategy=policy.strategy,
            reason=policy.reason,
        ),
    )


def truncate_text(
    text: str,
    maximum_bytes: int,
    *,
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL,
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY,
    encoding: str = _DEFAULT_ENCODING,
    encode_errors: str = "strict",
    decode_errors: str = "replace",
    head_bytes: int | None = None,
    tail_bytes: int | None = None,
) -> TextTruncationResult:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    encoding = _normalize_encoding(encoding)
    _validate_codec_errors(encode_errors, "encode_errors")
    _validate_codec_errors(decode_errors, "decode_errors")
    encoded = text.encode(encoding, errors=encode_errors)
    result = truncate_bytes(
        encoded,
        maximum_bytes,
        strategy=strategy,
        reason=reason,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    decoded, lossy = _decode_retained(
        result.data,
        encoding=encoding,
        errors=decode_errors,
        strategy=result.metadata.retention_strategy,
        truncated=result.metadata.truncated,
        maximum_bytes=maximum_bytes,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    return TextTruncationResult(
        text=decoded,
        metadata=result.metadata,
        encoding=encoding,
        decode_lossy=lossy,
    )


def read_truncated_bytes(
    path: PathLike,
    maximum_bytes: int,
    *,
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL,
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY,
    head_bytes: int | None = None,
    tail_bytes: int | None = None,
) -> ByteTruncationResult:
    source = _coerce_file_path(path)
    policy = TruncationPolicy(
        maximum_bytes=maximum_bytes,
        strategy=strategy,
        reason=reason,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    observed = source.stat().st_size
    if observed <= maximum_bytes:
        data = source.read_bytes()
        observed = len(data)
        return ByteTruncationResult(
            data=data,
            metadata=_metadata(
                observed=observed,
                retained=observed,
                strategy=RetentionStrategy.FULL,
                reason=policy.reason,
            ),
        )
    with source.open("rb") as handle:
        if policy.strategy is RetentionStrategy.HEAD:
            data = handle.read(maximum_bytes)
        elif policy.strategy is RetentionStrategy.TAIL:
            handle.seek(max(0, observed - maximum_bytes))
            data = handle.read(maximum_bytes)
        elif policy.strategy is RetentionStrategy.HEAD_TAIL:
            head, tail = policy.partition()
            first = handle.read(head)
            handle.seek(max(0, observed - tail))
            last = handle.read(tail)
            data = first + last
        else:
            raise ValueError(f"unsupported byte retention strategy: {policy.strategy}")
    return ByteTruncationResult(
        data=data,
        metadata=_metadata(
            observed=observed,
            retained=len(data),
            strategy=policy.strategy,
            reason=policy.reason,
        ),
    )


def read_truncated_text(
    path: PathLike,
    maximum_bytes: int,
    *,
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL,
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY,
    encoding: str = _DEFAULT_ENCODING,
    errors: str = "replace",
    head_bytes: int | None = None,
    tail_bytes: int | None = None,
) -> TextTruncationResult:
    encoding = _normalize_encoding(encoding)
    _validate_codec_errors(errors, "errors")
    result = read_truncated_bytes(
        path,
        maximum_bytes,
        strategy=strategy,
        reason=reason,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    text, lossy = _decode_retained(
        result.data,
        encoding=encoding,
        errors=errors,
        strategy=result.metadata.retention_strategy,
        truncated=result.metadata.truncated,
        maximum_bytes=maximum_bytes,
        head_bytes=head_bytes,
        tail_bytes=tail_bytes,
    )
    return TextTruncationResult(
        text=text,
        metadata=result.metadata,
        encoding=encoding,
        decode_lossy=lossy,
    )


def truncate_lines(
    text: str,
    maximum_lines: int,
    *,
    strategy: RetentionStrategy = RetentionStrategy.HEAD_TAIL,
    reason: TruncationReason | str = TruncationReason.EXPLICIT_POLICY,
    head_lines: int | None = None,
    tail_lines: int | None = None,
) -> LineTruncationResult:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    _require_non_negative_int(maximum_lines, "maximum_lines")
    if strategy not in (
        RetentionStrategy.HEAD,
        RetentionStrategy.TAIL,
        RetentionStrategy.HEAD_TAIL,
    ):
        raise ValueError("line truncation supports HEAD, TAIL, and HEAD_TAIL")
    reason_text = _coerce_reason(reason)
    lines = text.splitlines(keepends=True)
    observed = len(lines)
    if observed <= maximum_lines:
        ranges = ((1, observed),) if observed else ()
        return LineTruncationResult(
            text=text,
            metadata=LineTruncationMetadata(
                truncated=False,
                observed_lines=observed,
                retained_lines=observed,
                start_line=1 if observed else None,
                end_line=observed if observed else None,
                retention_strategy=RetentionStrategy.FULL,
                reason=reason_text,
                retained_ranges=ranges,
            ),
        )
    if strategy is RetentionStrategy.HEAD:
        retained = lines[:maximum_lines]
        ranges = ((1, len(retained)),) if retained else ()
    elif strategy is RetentionStrategy.TAIL:
        retained = lines[-maximum_lines:] if maximum_lines else []
        ranges = (
            ((observed - len(retained) + 1, observed),) if retained else ()
        )
    else:
        head, tail = _line_partition(maximum_lines, head_lines, tail_lines)
        retained = lines[:head] + (lines[-tail:] if tail else [])
        range_parts: list[tuple[int, int]] = []
        if head:
            range_parts.append((1, head))
        if tail:
            range_parts.append((observed - tail + 1, observed))
        ranges = tuple(range_parts)
    return LineTruncationResult(
        text="".join(retained),
        metadata=LineTruncationMetadata(
            truncated=True,
            observed_lines=observed,
            retained_lines=len(retained),
            start_line=ranges[0][0] if ranges else None,
            end_line=ranges[-1][1] if ranges else None,
            retention_strategy=strategy,
            reason=reason_text,
            retained_ranges=ranges,
        ),
    )


def excerpt_around_line(
    text: str,
    line_number: int,
    *,
    before_lines: int = 3,
    after_lines: int = 3,
    reason: TruncationReason | str = TruncationReason.DIAGNOSTIC_EXCERPT_LIMIT,
) -> LineTruncationResult:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    _require_positive_int(line_number, "line_number")
    _require_non_negative_int(before_lines, "before_lines")
    _require_non_negative_int(after_lines, "after_lines")
    reason_text = _coerce_reason(reason)
    lines = text.splitlines(keepends=True)
    observed = len(lines)
    if observed == 0:
        return LineTruncationResult(
            text="",
            metadata=LineTruncationMetadata(
                truncated=False,
                observed_lines=0,
                retained_lines=0,
                start_line=None,
                end_line=None,
                retention_strategy=RetentionStrategy.FULL,
                reason=reason_text,
                retained_ranges=(),
            ),
        )
    if line_number > observed:
        raise ValueError("line_number exceeds available lines")
    start = max(1, line_number - before_lines)
    end = min(observed, line_number + after_lines)
    retained = lines[start - 1 : end]
    truncated = start > 1 or end < observed
    return LineTruncationResult(
        text="".join(retained),
        metadata=LineTruncationMetadata(
            truncated=truncated,
            observed_lines=observed,
            retained_lines=len(retained),
            start_line=start,
            end_line=end,
            retention_strategy=(
                RetentionStrategy.AROUND_LINE if truncated else RetentionStrategy.FULL
            ),
            reason=reason_text,
            retained_ranges=((start, end),),
        ),
    )


def render_truncation_marker(
    metadata: TruncationMetadata,
    *,
    template: str = _DEFAULT_MARKER_TEMPLATE,
) -> str:
    if not isinstance(metadata, TruncationMetadata):
        raise TypeError("metadata must be TruncationMetadata")
    if not metadata.truncated:
        return ""
    if not isinstance(template, str) or not template:
        raise ValueError("template must be a non-empty string")
    try:
        return template.format(
            retained_bytes=metadata.retained_bytes,
            observed_bytes=metadata.observed_bytes,
            original_or_observed_bytes=metadata.original_or_observed_bytes,
            omitted_bytes=metadata.omitted_bytes,
            strategy=metadata.retention_strategy.value,
            reason=metadata.reason,
            size_qualifier=metadata.size_qualifier,
        )
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError("invalid truncation marker template") from exc


def format_truncation_marker(metadata: TruncationMetadata) -> str:
    return render_truncation_marker(metadata)


def append_truncation_marker(
    text: str,
    metadata: TruncationMetadata,
    *,
    newline: str = "\n",
) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if newline not in ("\n", "\r\n"):
        raise ValueError("newline must be LF or CRLF")
    marker = render_truncation_marker(metadata)
    if not marker:
        return text
    if text and not text.endswith(("\n", "\r")):
        text += newline
    return f"{text}{marker}{newline}"


def _retain_from_bytes(data: bytes, policy: TruncationPolicy) -> bytes:
    limit = policy.maximum_bytes
    if policy.strategy is RetentionStrategy.HEAD:
        return data[:limit]
    if policy.strategy is RetentionStrategy.TAIL:
        return data[-limit:] if limit else b""
    if policy.strategy is RetentionStrategy.HEAD_TAIL:
        head, tail = policy.partition()
        return data[:head] + (data[-tail:] if tail else b"")
    raise ValueError(f"unsupported byte retention strategy: {policy.strategy}")


def _decode_retained(
    data: bytes,
    *,
    encoding: str,
    errors: str,
    strategy: RetentionStrategy,
    truncated: bool,
    maximum_bytes: int,
    head_bytes: int | None,
    tail_bytes: int | None,
) -> tuple[str, bool]:
    if not truncated or strategy in (RetentionStrategy.FULL, RetentionStrategy.HEAD):
        return _decode(data, encoding, errors, trim_leading=False, trim_trailing=truncated)
    if strategy is RetentionStrategy.TAIL:
        return _decode(data, encoding, errors, trim_leading=True, trim_trailing=False)
    if strategy is RetentionStrategy.HEAD_TAIL:
        head, tail = TruncationPolicy(
            maximum_bytes=maximum_bytes,
            strategy=strategy,
            head_bytes=head_bytes,
            tail_bytes=tail_bytes,
        ).partition()
        first = data[:head]
        last = data[head : head + tail]
        first_text, first_lossy = _decode(
            first,
            encoding,
            errors,
            trim_leading=False,
            trim_trailing=True,
        )
        last_text, last_lossy = _decode(
            last,
            encoding,
            errors,
            trim_leading=True,
            trim_trailing=False,
        )
        return first_text + last_text, first_lossy or last_lossy
    return _decode(data, encoding, errors, trim_leading=False, trim_trailing=False)


def _decode(
    data: bytes,
    encoding: str,
    errors: str,
    *,
    trim_leading: bool,
    trim_trailing: bool,
) -> tuple[str, bool]:
    candidate = data
    lossy = False
    if trim_leading:
        candidate, changed = _trim_incomplete_prefix(candidate, encoding)
        lossy = lossy or changed
    if trim_trailing:
        candidate, changed = _trim_incomplete_suffix(candidate, encoding)
        lossy = lossy or changed
    try:
        return candidate.decode(encoding, errors="strict"), lossy
    except UnicodeDecodeError:
        if errors == "strict":
            raise
        return candidate.decode(encoding, errors=errors), True


def _trim_incomplete_prefix(data: bytes, encoding: str) -> tuple[bytes, bool]:
    if not data:
        return data, False
    maximum = min(8, len(data))
    for offset in range(maximum + 1):
        candidate = data[offset:]
        try:
            candidate.decode(encoding, errors="strict")
            return candidate, offset > 0
        except UnicodeDecodeError as exc:
            if exc.start > 0:
                return data, False
    return data, False


def _trim_incomplete_suffix(data: bytes, encoding: str) -> tuple[bytes, bool]:
    if not data:
        return data, False
    maximum = min(8, len(data))
    for removed in range(maximum + 1):
        candidate = data[: len(data) - removed] if removed else data
        try:
            candidate.decode(encoding, errors="strict")
            return candidate, removed > 0
        except UnicodeDecodeError as exc:
            if exc.end < len(candidate):
                return data, False
    return data, False


def _normalize_line_ranges(
    values: tuple[tuple[int, int], ...],
    *,
    start_line: int | None,
    end_line: int | None,
    retained_lines: int,
    observed_lines: int,
) -> tuple[tuple[int, int], ...]:
    if not isinstance(values, tuple):
        raise TypeError("retained_ranges must be a tuple")
    if values:
        ranges = values
    elif retained_lines:
        _require_positive_int(start_line, "start_line")
        _require_positive_int(end_line, "end_line")
        assert start_line is not None
        assert end_line is not None
        ranges = ((start_line, end_line),)
    else:
        if start_line is not None or end_line is not None:
            raise ValueError("empty excerpts cannot declare line ranges")
        return ()
    previous_end = 0
    total = 0
    normalized: list[tuple[int, int]] = []
    for item in ranges:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("retained_ranges items must be two-integer tuples")
        first, last = item
        _require_positive_int(first, "retained range start")
        _require_positive_int(last, "retained range end")
        if last < first:
            raise ValueError("retained range end cannot precede start")
        if last > observed_lines:
            raise ValueError("retained range exceeds observed_lines")
        if first <= previous_end:
            raise ValueError("retained ranges must be ordered and non-overlapping")
        normalized.append((first, last))
        total += last - first + 1
        previous_end = last
    if total != retained_lines:
        raise ValueError("retained ranges must account for retained_lines")
    return tuple(normalized)


def _line_partition(
    maximum_lines: int,
    head_lines: int | None,
    tail_lines: int | None,
) -> tuple[int, int]:
    if head_lines is not None:
        _require_non_negative_int(head_lines, "head_lines")
    if tail_lines is not None:
        _require_non_negative_int(tail_lines, "tail_lines")
    if head_lines is None and tail_lines is None:
        head = (maximum_lines + 1) // 2
        return head, maximum_lines - head
    if head_lines is None:
        assert tail_lines is not None
        if tail_lines > maximum_lines:
            raise ValueError("tail_lines exceeds maximum_lines")
        return maximum_lines - tail_lines, tail_lines
    if tail_lines is None:
        if head_lines > maximum_lines:
            raise ValueError("head_lines exceeds maximum_lines")
        return head_lines, maximum_lines - head_lines
    if head_lines + tail_lines != maximum_lines:
        raise ValueError("head_lines plus tail_lines must equal maximum_lines")
    return head_lines, tail_lines


def _metadata(
    *,
    observed: int,
    retained: int,
    strategy: RetentionStrategy,
    reason: str,
) -> TruncationMetadata:
    return TruncationMetadata(
        truncated=retained < observed,
        observed_bytes=observed,
        retained_bytes=retained,
        retention_strategy=strategy,
        reason=reason,
        original_size_known=True,
    )


def _coerce_file_path(path: PathLike) -> Path:
    source = Path(path)
    if "\x00" in str(source):
        raise ValueError("path must not contain NUL")
    if not source.exists():
        raise FileNotFoundError(source)
    if not source.is_file():
        raise IsADirectoryError(source)
    return source


def _coerce_reason(value: TruncationReason | str) -> str:
    if isinstance(value, TruncationReason):
        return value.value
    return _require_text(value, "reason")


def _normalize_encoding(value: str) -> str:
    value = _require_text(value, "encoding")
    try:
        return codecs.lookup(value).name
    except LookupError as exc:
        raise ValueError(f"unknown encoding {value!r}") from exc


def _validate_codec_errors(value: str, field: str) -> None:
    if value not in _SUPPORTED_DECODE_ERRORS:
        allowed = ", ".join(sorted(_SUPPORTED_DECODE_ERRORS))
        raise ValueError(f"{field} must be one of: {allowed}")


def _require_non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _require_positive_int(value: object, field: str) -> int:
    result = _require_non_negative_int(value, field)
    if result == 0:
        raise ValueError(f"{field} must be positive")
    return result


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip() or "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be non-empty single-line text without NUL")
    return value


__all__ = (
    "ByteTruncationResult",
    "LineTruncationMetadata",
    "LineTruncationResult",
    "RetentionStrategy",
    "TextTruncationResult",
    "TruncationMetadata",
    "TruncationPolicy",
    "TruncationReason",
    "TruncationStrategy",
    "append_truncation_marker",
    "excerpt_around_line",
    "format_truncation_marker",
    "read_truncated_bytes",
    "read_truncated_text",
    "render_truncation_marker",
    "truncate_bytes",
    "truncate_lines",
    "truncate_text",
)
