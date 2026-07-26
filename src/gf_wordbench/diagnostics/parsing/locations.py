"""Conservative source-location extraction for GF diagnostics."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePath
from typing import Final, TypeAlias

PathText: TypeAlias = str | PurePath

_DEFAULT_SUFFIXES: Final[tuple[str, ...]] = (".gf", ".gfs")
_MAX_INPUT_LENGTH: Final[int] = 1_048_576
_MAX_PATH_LENGTH: Final[int] = 32_768
_COORDINATE_TAIL: Final[str] = (
    r":(?P<line>[1-9][0-9]*)"
    r"(?:"
    r":(?P<column>[1-9][0-9]*)"
    r"(?:-(?:(?P<end_line>[1-9][0-9]*):)?"
    r"(?P<end_column>[1-9][0-9]*))?"
    r"|-(?P<line_range_end>[1-9][0-9]*)"
    r")?"
)
_WINDOWS_ABSOLUTE: Final[str] = (
    r"[A-Za-z]:[\\/][^:\r\n]*?"
)
_UNC_ABSOLUTE: Final[str] = (
    r"\\\\[^\\/\r\n:]+[\\/][^:\r\n]*?"
)
_POSIX_ABSOLUTE: Final[str] = (
    r"/[^:\r\n]*?"
)
_RELATIVE_PATH: Final[str] = (
    r"(?:\.{1,2}[\\/])?"
    r"(?:[^\s:\(\)\[\]\{\}<>'\"]+[\\/])*"
    r"[^\s:\(\)\[\]\{\}<>'\"]+?"
)
_QUOTED_PATH: Final[str] = (
    r"(?P<quote>[\"'])"
    r"(?P<quoted_path>[^\"'\r\n]+?)"
    r"(?P=quote)"
)
_UNQUOTED_PATH: Final[str] = (
    rf"(?P<unquoted_path>"
    rf"(?:{_WINDOWS_ABSOLUTE}|{_UNC_ABSOLUTE}|"
    rf"{_POSIX_ABSOLUTE}|{_RELATIVE_PATH})"
    rf")"
)
_PREFIX_BOUNDARY: Final[str] = r"(?<![A-Za-z0-9_.\\/:-])"


@dataclass(frozen=True, slots=True)
class SourceLocation:
    source_path_raw: str
    source_path_normalized: str | None
    line: int
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        raw = _require_path_text(
            self.source_path_raw,
            field="source_path_raw",
        )
        normalized = self.source_path_normalized
        if normalized is not None:
            normalized = _require_path_text(
                normalized,
                field="source_path_normalized",
            )
        line = _positive_int(self.line, field="line")
        column = _optional_positive_int(self.column, field="column")
        end_line = _optional_positive_int(self.end_line, field="end_line")
        end_column = _optional_positive_int(
            self.end_column,
            field="end_column",
        )

        if end_column is not None and column is None:
            raise ValueError("end_column requires column")
        if end_line is not None and end_line < line:
            raise ValueError("end_line must not precede line")
        if (
            end_line is not None
            and end_line == line
            and end_column is not None
            and column is not None
            and end_column < column
        ):
            raise ValueError(
                "end_column must not precede column on the same line"
            )

        object.__setattr__(self, "source_path_raw", raw)
        object.__setattr__(
            self,
            "source_path_normalized",
            normalized,
        )
        object.__setattr__(self, "line", line)
        object.__setattr__(self, "column", column)
        object.__setattr__(self, "end_line", end_line)
        object.__setattr__(self, "end_column", end_column)

    @property
    def has_range(self) -> bool:
        return self.end_line is not None or self.end_column is not None

    @property
    def effective_end_line(self) -> int | None:
        if self.end_column is not None and self.end_line is None:
            return self.line
        return self.end_line


@dataclass(frozen=True, slots=True)
class LocationMatch:
    location: SourceLocation
    start: int
    end: int
    matched_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.location, SourceLocation):
            raise TypeError("location must be SourceLocation")
        if type(self.start) is not int or self.start < 0:
            raise ValueError("start must be a non-negative integer")
        if type(self.end) is not int or self.end < self.start:
            raise ValueError("end must not precede start")
        if not isinstance(self.matched_text, str):
            raise TypeError("matched_text must be a string")
        if "\x00" in self.matched_text:
            raise ValueError("matched_text must not contain NUL")
        if len(self.matched_text) != self.end - self.start:
            raise ValueError(
                "matched_text length must match the source span"
            )


def parse_source_location(
    value: str,
    *,
    project_root: PathText | None = None,
    allowed_suffixes: Iterable[str] = _DEFAULT_SUFFIXES,
) -> SourceLocation | None:
    text = _require_input(value)
    pattern = _location_pattern(
        allowed_suffixes,
        anchored=True,
        allow_trailing_separator=False,
    )
    match = pattern.fullmatch(text)
    if match is None:
        return None
    return _location_from_match(
        match,
        project_root=project_root,
    )


def match_source_location_prefix(
    text: str,
    *,
    project_root: PathText | None = None,
    allowed_suffixes: Iterable[str] = _DEFAULT_SUFFIXES,
) -> LocationMatch | None:
    value = _require_input(text)
    pattern = _location_pattern(
        allowed_suffixes,
        anchored=True,
        allow_trailing_separator=True,
    )
    match = pattern.match(value)
    if match is None:
        return None
    start, end = match.span("location")
    return LocationMatch(
        location=_location_from_match(
            match,
            project_root=project_root,
        ),
        start=start,
        end=end,
        matched_text=value[start:end],
    )


def extract_source_location(
    text: str,
    *,
    project_root: PathText | None = None,
    allowed_suffixes: Iterable[str] = _DEFAULT_SUFFIXES,
    allow_embedded: bool = False,
) -> LocationMatch | None:
    value = _require_input(text)
    pattern = _location_pattern(
        allowed_suffixes,
        anchored=not allow_embedded,
        allow_trailing_separator=True,
    )
    match = pattern.search(value)
    if match is None:
        return None
    start, end = match.span("location")
    return LocationMatch(
        location=_location_from_match(
            match,
            project_root=project_root,
        ),
        start=start,
        end=end,
        matched_text=value[start:end],
    )


def split_location_prefix(
    text: str,
    *,
    project_root: PathText | None = None,
    allowed_suffixes: Iterable[str] = _DEFAULT_SUFFIXES,
) -> tuple[SourceLocation | None, str]:
    value = _require_input(text)
    matched = match_source_location_prefix(
        value,
        project_root=project_root,
        allowed_suffixes=allowed_suffixes,
    )
    if matched is None:
        return None, value

    remainder = value[matched.end :]
    if remainder.startswith(":"):
        remainder = remainder[1:]
    return matched.location, remainder.lstrip()


def normalize_source_path(
    source_path_raw: PathText,
    *,
    project_root: PathText | None = None,
) -> str:
    raw = _require_path_text(
        str(source_path_raw),
        field="source_path_raw",
    )
    portable = _portable_path(raw)

    if project_root is None:
        return portable

    root = _portable_path(
        _require_path_text(
            str(project_root),
            field="project_root",
        )
    )
    relative = _lexical_relative_to(portable, root)
    return relative if relative is not None else portable


def _location_pattern(
    allowed_suffixes: Iterable[str],
    *,
    anchored: bool,
    allow_trailing_separator: bool,
) -> re.Pattern[str]:
    suffixes = _normalize_suffixes(allowed_suffixes)
    suffix_expression = "(?:" + "|".join(
        re.escape(suffix[1:]) for suffix in suffixes
    ) + ")"
    path_with_suffix = (
        rf"(?:{_QUOTED_PATH}|{_UNQUOTED_PATH})"
        rf"\.{suffix_expression}"
    )
    start = r"^\s*" if anchored else _PREFIX_BOUNDARY
    trailing = r"(?=:\s|\s|$|[\]\)\}>,;])" if allow_trailing_separator else ""
    return re.compile(
        rf"{start}(?P<location>{path_with_suffix}{_COORDINATE_TAIL})"
        rf"{trailing}",
        re.IGNORECASE,
    )


def _location_from_match(
    match: re.Match[str],
    *,
    project_root: PathText | None,
) -> SourceLocation:
    raw_path = match.group("quoted_path") or match.group("unquoted_path")
    if raw_path is None:
        raise AssertionError("location match did not capture a path")

    line = int(match.group("line"))
    column_text = match.group("column")
    end_line_text = match.group("end_line")
    end_column_text = match.group("end_column")
    line_range_end = match.group("line_range_end")

    column = int(column_text) if column_text is not None else None
    end_line = int(end_line_text) if end_line_text is not None else None
    end_column = (
        int(end_column_text)
        if end_column_text is not None
        else None
    )

    if line_range_end is not None:
        end_line = int(line_range_end)
    elif end_column is not None and end_line is None:
        end_line = line

    return SourceLocation(
        source_path_raw=raw_path,
        source_path_normalized=normalize_source_path(
            raw_path,
            project_root=project_root,
        ),
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def _normalize_suffixes(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            "allowed_suffixes must be an iterable of suffix strings"
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("allowed suffixes must be strings")
        suffix = value.casefold()
        if not suffix.startswith("."):
            suffix = "." + suffix
        if re.fullmatch(r"\.[a-z0-9]+", suffix) is None:
            raise ValueError(f"invalid source suffix: {value!r}")
        if suffix not in seen:
            seen.add(suffix)
            normalized.append(suffix)

    if not normalized:
        raise ValueError("at least one source suffix is required")
    return tuple(normalized)


def _portable_path(value: str) -> str:
    text = value.replace("\\", "/")
    prefix = ""

    if text.startswith("//"):
        prefix = "//"
        text = text[2:]
    elif re.match(r"^[A-Za-z]:/", text):
        prefix = text[:3]
        text = text[3:]
    elif text.startswith("/"):
        prefix = "/"
        text = text[1:]

    parts: list[str] = []
    for part in text.split("/"):
        if not part or part == ".":
            continue
        parts.append(part)

    body = "/".join(parts)
    if prefix == "//":
        return "//" + body
    if prefix.endswith(":/"):
        return prefix + body
    if prefix == "/":
        return "/" + body
    return body or "."


def _lexical_relative_to(
    path: str,
    root: str,
) -> str | None:
    path_windows = _is_windows_style(path)
    root_windows = _is_windows_style(root)
    if path_windows != root_windows:
        return None

    path_parts = _comparison_parts(path)
    root_parts = _comparison_parts(root)
    if len(path_parts) <= len(root_parts):
        return None

    if path_windows:
        matches = all(
            left.casefold() == right.casefold()
            for left, right in zip(path_parts, root_parts, strict=False)
        )
    else:
        matches = path_parts[: len(root_parts)] == root_parts

    if not matches:
        return None

    relative_parts = path_parts[len(root_parts) :]
    if not relative_parts or ".." in relative_parts:
        return None
    return "/".join(relative_parts)


def _comparison_parts(value: str) -> tuple[str, ...]:
    text = value
    if text.startswith("//"):
        text = text[2:]
    elif re.match(r"^[A-Za-z]:/", text):
        text = text[:2] + "/" + text[3:]
    elif text.startswith("/"):
        text = text[1:]
    return tuple(part for part in text.split("/") if part)


def _is_windows_style(value: str) -> bool:
    return bool(
        re.match(r"^[A-Za-z]:/", value)
        or value.startswith("//")
    )


def _require_input(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("diagnostic text must be a string")
    if "\x00" in value:
        raise ValueError("diagnostic text must not contain NUL")
    if len(value) > _MAX_INPUT_LENGTH:
        raise ValueError("diagnostic text exceeds the supported limit")
    return value


def _require_path_text(
    value: object,
    *,
    field: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > _MAX_PATH_LENGTH:
        raise ValueError(f"{field} exceeds the supported limit")
    if "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be one line")
    return value


def _positive_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be positive")
    return value


def _optional_positive_int(
    value: object,
    *,
    field: str,
) -> int | None:
    if value is None:
        return None
    return _positive_int(value, field=field)


__all__ = (
    "LocationMatch",
    "PathText",
    "SourceLocation",
    "extract_source_location",
    "match_source_location_prefix",
    "normalize_source_path",
    "parse_source_location",
    "split_location_prefix",
)
