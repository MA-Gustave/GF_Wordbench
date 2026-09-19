"""Exact, read-only scenario gold comparison for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from enum import StrEnum, unique
import hashlib
from pathlib import Path
import re
from typing import Final

from gf_wordbench.infrastructure.atomic_io import atomic_write_text
from gf_wordbench.kernel.ids import (
    ScenarioId,
    SectionId,
    validate_scenario_id,
    validate_section_id,
)
from gf_wordbench.kernel.paths import serialize_portable_path
from gf_wordbench.kernel.statuses import ErrorKind

_OUTPUT_HEADER: Final = "# GF_WORDBENCH_OUTPUT 1.0"
_GOLD_HEADER: Final = "# GF_WORDBENCH_GOLD 1.0"
_SCENARIO_PREFIX: Final = "# scenario_id: "
_NORMALIZATION_PREFIX: Final = "# normalization_version: "
_VERSION_RE: Final = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
_BEGIN_RE: Final = re.compile(r"^--- BEGIN (?P<id>[a-z][a-z0-9]*(?:-[a-z0-9]+)*) ---$")
_END_RE: Final = re.compile(r"^--- END (?P<id>[a-z][a-z0-9]*(?:-[a-z0-9]+)*) ---$")


@unique
class GoldComparisonPolicy(StrEnum):
    NONE = "none"
    EXACT = "exact"


@unique
class GoldComparisonState(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    MATCH = "match"
    MISMATCH = "mismatch"
    ERROR = "error"


@unique
class ScenarioTextKind(StrEnum):
    OUTPUT = "output"
    GOLD = "gold"


@dataclass(frozen=True, slots=True)
class ScenarioTextSection:
    section_id: SectionId
    content: str


@dataclass(frozen=True, slots=True)
class ScenarioTextDocument:
    kind: ScenarioTextKind
    scenario_id: ScenarioId
    normalization_version: str
    sections: tuple[ScenarioTextSection, ...]
    canonical_text: str
    sha256: str

    @property
    def section_ids(self) -> tuple[SectionId, ...]:
        return tuple(section.section_id for section in self.sections)

    @property
    def is_content_empty(self) -> bool:
        return all(not section.content for section in self.sections)

    def comparison_projection(self) -> str:
        parts = [
            f"{_SCENARIO_PREFIX}{self.scenario_id}\n",
            f"{_NORMALIZATION_PREFIX}{self.normalization_version}\n",
        ]
        for section in self.sections:
            parts.extend(
                (
                    f"--- BEGIN {section.section_id} ---\n",
                    section.content,
                    f"--- END {section.section_id} ---\n",
                )
            )
        return "".join(parts)


@dataclass(frozen=True, slots=True)
class GoldComparisonResult:
    policy: GoldComparisonPolicy
    state: GoldComparisonState
    gold_match: bool | None
    error_kind: ErrorKind
    message: str
    scenario_id: ScenarioId
    normalization_version: str
    normalized_output_path: Path | None
    gold_path: Path | None
    gold_diff_path: Path | None
    expected_sha256: str | None = None
    actual_sha256: str | None = None
    section_ids: tuple[SectionId, ...] = ()

    @property
    def applied(self) -> bool:
        return self.policy is GoldComparisonPolicy.EXACT

    @property
    def succeeded(self) -> bool:
        return self.state in {
            GoldComparisonState.NOT_APPLICABLE,
            GoldComparisonState.MATCH,
        }


class ScenarioTextValidationError(ValueError):
    def __init__(self, message: str, *, kind: ScenarioTextKind) -> None:
        super().__init__(message)
        self.kind = kind


def parse_scenario_text(
    text: str,
    *,
    kind: ScenarioTextKind,
) -> ScenarioTextDocument:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(kind, ScenarioTextKind):
        raise TypeError("kind must be a ScenarioTextKind")
    if text.startswith("\ufeff"):
        raise ScenarioTextValidationError(
            f"{kind.value} text must be UTF-8 without BOM",
            kind=kind,
        )

    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    if not canonical.endswith("\n"):
        raise ScenarioTextValidationError(
            f"{kind.value} text must end with a newline",
            kind=kind,
        )

    lines = canonical.splitlines(keepends=True)
    if len(lines) < 6:
        raise ScenarioTextValidationError(
            f"{kind.value} text is incomplete",
            kind=kind,
        )

    header = _OUTPUT_HEADER if kind is ScenarioTextKind.OUTPUT else _GOLD_HEADER
    if _line(lines[0]) != header:
        raise ScenarioTextValidationError(
            f"unsupported {kind.value} header; expected {header!r}",
            kind=kind,
        )

    scenario_text = _header_value(lines[1], _SCENARIO_PREFIX, "scenario_id", kind)
    version = _header_value(lines[2], _NORMALIZATION_PREFIX, "normalization_version", kind)
    try:
        scenario_id = validate_scenario_id(scenario_text, field="scenario_id")
        _require_version(version)
    except (TypeError, ValueError) as exc:
        raise ScenarioTextValidationError(str(exc), kind=kind) from exc

    sections: list[ScenarioTextSection] = []
    seen: set[SectionId] = set()
    index = 3
    while index < len(lines):
        begin = _BEGIN_RE.fullmatch(_line(lines[index]))
        if begin is None:
            raise ScenarioTextValidationError(
                f"unexpected text outside a section at line {index + 1}",
                kind=kind,
            )
        section_id = validate_section_id(begin.group("id"), field=f"section ID at line {index + 1}")
        if section_id in seen:
            raise ScenarioTextValidationError(f"duplicate section ID {section_id!r}", kind=kind)

        index += 1
        content: list[str] = []
        while index < len(lines):
            current = _line(lines[index])
            end = _END_RE.fullmatch(current)
            if end is not None:
                if end.group("id") != section_id:
                    raise ScenarioTextValidationError(
                        f"section {section_id!r} closes as {end.group('id')!r}",
                        kind=kind,
                    )
                break
            if _BEGIN_RE.fullmatch(current) is not None:
                raise ScenarioTextValidationError(
                    f"nested section marker at line {index + 1}", kind=kind
                )
            content.append(lines[index])
            index += 1

        if index >= len(lines):
            raise ScenarioTextValidationError(
                f"section {section_id!r} has no end marker", kind=kind
            )
        sections.append(ScenarioTextSection(section_id, "".join(content)))
        seen.add(section_id)
        index += 1

    if not sections:
        raise ScenarioTextValidationError(f"{kind.value} text contains no sections", kind=kind)

    return ScenarioTextDocument(
        kind=kind,
        scenario_id=scenario_id,
        normalization_version=version,
        sections=tuple(sections),
        canonical_text=canonical,
        sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def compare_gold_text(
    *,
    scenario_id: ScenarioId | str,
    normalization_version: str,
    normalized_output_text: str,
    gold_text: str,
    allow_empty_gold: bool = False,
    expected_label: str = "expected.gold",
    actual_label: str = "actual.out",
) -> tuple[bool, str, ScenarioTextDocument, ScenarioTextDocument]:
    resolved_id = validate_scenario_id(scenario_id, field="scenario_id")
    _require_version(normalization_version)
    if not isinstance(allow_empty_gold, bool):
        raise TypeError("allow_empty_gold must be a boolean")

    actual = parse_scenario_text(normalized_output_text, kind=ScenarioTextKind.OUTPUT)
    expected = parse_scenario_text(gold_text, kind=ScenarioTextKind.GOLD)
    _require_identity(actual, resolved_id, normalization_version)
    _require_identity(expected, resolved_id, normalization_version)

    if expected.is_content_empty and not allow_empty_gold:
        raise ScenarioTextValidationError(
            "empty gold requires explicit allow_empty_gold=True",
            kind=ScenarioTextKind.GOLD,
        )

    expected_projection = expected.comparison_projection()
    actual_projection = actual.comparison_projection()
    matched = expected_projection == actual_projection
    diff = (
        ""
        if matched
        else build_unified_gold_diff(
            expected_projection=expected_projection,
            actual_projection=actual_projection,
            expected_label=expected_label,
            actual_label=actual_label,
        )
    )
    return matched, diff, expected, actual


def build_unified_gold_diff(
    *,
    expected_projection: str,
    actual_projection: str,
    expected_label: str,
    actual_label: str,
) -> str:
    expected_name = _diff_label(expected_label, "expected_label")
    actual_name = _diff_label(actual_label, "actual_label")
    diff = "".join(
        unified_diff(
            expected_projection.splitlines(keepends=True),
            actual_projection.splitlines(keepends=True),
            fromfile=expected_name,
            tofile=actual_name,
            lineterm="\n",
        )
    )
    return diff if not diff or diff.endswith("\n") else diff + "\n"


def compare_gold(
    *,
    policy: GoldComparisonPolicy | str,
    scenario_id: ScenarioId | str,
    normalization_version: str,
    normalized_output_path: Path | None,
    gold_path: Path | None,
    gold_diff_path: Path | None = None,
    gold_label: str | None = None,
    actual_label: str | None = None,
    diff_root: Path | None = None,
    allow_empty_gold: bool = False,
) -> GoldComparisonResult:
    resolved_policy = _policy(policy)
    resolved_id = validate_scenario_id(scenario_id, field="scenario_id")
    _require_version(normalization_version)

    if resolved_policy is GoldComparisonPolicy.NONE:
        return GoldComparisonResult(
            resolved_policy,
            GoldComparisonState.NOT_APPLICABLE,
            None,
            ErrorKind.OK,
            "No gold comparison applies.",
            resolved_id,
            normalization_version,
            normalized_output_path,
            gold_path,
            None,
        )

    actual_path = _required_path(normalized_output_path, "normalized_output_path")
    expected_path = _required_path(gold_path, "gold_path")
    if not actual_path.is_file():
        return _error(
            resolved_id,
            normalization_version,
            actual_path,
            expected_path,
            "Normalized scenario output is missing.",
            ErrorKind.IO,
        )
    if not expected_path.is_file():
        return _error(
            resolved_id,
            normalization_version,
            actual_path,
            expected_path,
            "Required gold file is missing.",
            ErrorKind.CONFIG,
        )

    try:
        actual_text = _read_utf8(actual_path, "normalized scenario output")
        expected_text = _read_utf8(expected_path, "gold file")
    except (OSError, UnicodeError) as exc:
        return _error(
            resolved_id,
            normalization_version,
            actual_path,
            expected_path,
            f"Gold comparison input is unreadable: {_bounded(exc)}",
            ErrorKind.IO,
        )

    try:
        matched, diff, expected, actual = compare_gold_text(
            scenario_id=resolved_id,
            normalization_version=normalization_version,
            normalized_output_text=actual_text,
            gold_text=expected_text,
            allow_empty_gold=allow_empty_gold,
            expected_label=gold_label or expected_path.name,
            actual_label=actual_label or actual_path.name,
        )
    except ScenarioTextValidationError as exc:
        kind = ErrorKind.CONFIG if exc.kind is ScenarioTextKind.GOLD else ErrorKind.INTERNAL
        return _error(
            resolved_id,
            normalization_version,
            actual_path,
            expected_path,
            str(exc),
            kind,
        )

    if matched:
        return GoldComparisonResult(
            state=GoldComparisonState.MATCH,
            gold_match=True,
            error_kind=ErrorKind.OK,
            message="Normalized output matches gold.",
            gold_diff_path=None,
            policy=GoldComparisonPolicy.EXACT,
            scenario_id=resolved_id,
            normalization_version=normalization_version,
            normalized_output_path=actual_path,
            gold_path=expected_path,
            expected_sha256=expected.sha256,
            actual_sha256=actual.sha256,
            section_ids=actual.section_ids,
        )

    destination = _required_path(gold_diff_path, "gold_diff_path")
    try:
        written = atomic_write_text(
            destination,
            diff,
            encoding="utf-8",
            newline="\n",
            create_parents=True,
            root=diff_root,
            role="scenario gold diff",
        )
    except (OSError, ValueError) as exc:
        return GoldComparisonResult(
            state=GoldComparisonState.ERROR,
            gold_match=False,
            error_kind=ErrorKind.IO,
            message=f"Gold mismatch detected, but diff writing failed: {_bounded(exc)}",
            gold_diff_path=None,
            policy=GoldComparisonPolicy.EXACT,
            scenario_id=resolved_id,
            normalization_version=normalization_version,
            normalized_output_path=actual_path,
            gold_path=expected_path,
            expected_sha256=expected.sha256,
            actual_sha256=actual.sha256,
            section_ids=actual.section_ids,
        )

    return GoldComparisonResult(
        state=GoldComparisonState.MISMATCH,
        gold_match=False,
        error_kind=ErrorKind.OTHER,
        message="Normalized output differs from gold.",
        gold_diff_path=written,
        policy=GoldComparisonPolicy.EXACT,
        scenario_id=resolved_id,
        normalization_version=normalization_version,
        normalized_output_path=actual_path,
        gold_path=expected_path,
        expected_sha256=expected.sha256,
        actual_sha256=actual.sha256,
        section_ids=actual.section_ids,
    )


def _line(value: str) -> str:
    return value[:-1] if value.endswith("\n") else value


def _header_value(
    line: str,
    prefix: str,
    name: str,
    kind: ScenarioTextKind,
) -> str:
    value = _line(line)
    if not value.startswith(prefix):
        raise ScenarioTextValidationError(f"missing canonical {name} header", kind=kind)
    result = value[len(prefix) :]
    if not result or result != result.strip() or "\x00" in result:
        raise ScenarioTextValidationError(f"invalid canonical {name} header", kind=kind)
    return result


def _require_identity(
    document: ScenarioTextDocument,
    scenario_id: ScenarioId,
    normalization_version: str,
) -> None:
    if document.scenario_id != scenario_id:
        raise ScenarioTextValidationError(
            f"{document.kind.value} scenario ID {document.scenario_id!r} does not match {scenario_id!r}",
            kind=document.kind,
        )
    if document.normalization_version != normalization_version:
        raise ScenarioTextValidationError(
            f"{document.kind.value} normalization version {document.normalization_version!r} does not match {normalization_version!r}",
            kind=document.kind,
        )


def _require_version(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("normalization_version must be a string")
    if _VERSION_RE.fullmatch(value) is None:
        raise ValueError("normalization_version must use canonical major.minor form")


def _policy(value: GoldComparisonPolicy | str) -> GoldComparisonPolicy:
    if isinstance(value, GoldComparisonPolicy):
        return value
    if not isinstance(value, str):
        raise TypeError("policy must be a GoldComparisonPolicy or string")
    try:
        return GoldComparisonPolicy(value)
    except ValueError as exc:
        raise ValueError(f"unsupported gold comparison policy {value!r}") from exc


def _required_path(value: Path | None, name: str) -> Path:
    if value is None:
        raise ValueError(f"{name} is required for exact gold comparison")
    if not isinstance(value, Path):
        raise TypeError(f"{name} must be a Path")
    if "\x00" in str(value):
        raise ValueError(f"{name} must not contain NUL")
    return value


def _read_utf8(path: Path, role: str) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise UnicodeError(f"{role} must be UTF-8 without BOM")
    return data.decode("utf-8", errors="strict")


def _diff_label(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip() or any(c in value for c in "\x00\r\n"):
        raise ValueError(f"{name} must be a non-empty single-line label")
    return serialize_portable_path(
        value,
        role=name,
        allow_root=False,
        accept_backslash=True,
    )


def _error(
    scenario_id: ScenarioId,
    normalization_version: str,
    actual_path: Path | None,
    gold_path: Path | None,
    message: str,
    error_kind: ErrorKind,
) -> GoldComparisonResult:
    return GoldComparisonResult(
        GoldComparisonPolicy.EXACT,
        GoldComparisonState.ERROR,
        None,
        error_kind,
        message,
        scenario_id,
        normalization_version,
        actual_path,
        gold_path,
        None,
    )


def _bounded(exc: BaseException, limit: int = 240) -> str:
    text = " ".join(str(exc).split()) or type(exc).__name__
    return text if len(text) <= limit else text[: limit - 1] + "…"


__all__ = (
    "GoldComparisonPolicy",
    "GoldComparisonResult",
    "GoldComparisonState",
    "ScenarioTextDocument",
    "ScenarioTextKind",
    "ScenarioTextSection",
    "ScenarioTextValidationError",
    "build_unified_gold_diff",
    "compare_gold",
    "compare_gold_text",
    "parse_scenario_text",
)
