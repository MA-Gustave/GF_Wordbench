"""Canonical scenario-contract diagnostic patterns."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from inspect import Parameter, signature
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeVar

from ..models import DiagnosticEvidence, DiagnosticPattern, PatternMatch

PATTERN_VERSION: Final[str] = "1.0"

REQUIRED_SCENARIO_MISSING_PATTERN_ID: Final[str] = "DP-SCEN-001"
REQUIRED_SECTION_INCOMPLETE_PATTERN_ID: Final[str] = "DP-SCEN-002"

_REQUIRED_SCENARIO_MISSING_PRIORITY: Final[int] = 20
_REQUIRED_SECTION_INCOMPLETE_PRIORITY: Final[int] = 21

_SCENARIO_OPERATIONS: Final[frozenset[str]] = frozenset(
    {
        "run_scenario",
        "scenario_preflight",
        "scenario_validation",
    }
)
_FRAMEWORK_STATE_STREAMS: Final[frozenset[str]] = frozenset(
    {"framework-state"}
)

_MAX_IDENTIFIER_LENGTH: Final[int] = 256
_MAX_DETAIL_LENGTH: Final[int] = 2_000
_MAX_REFERENCES: Final[int] = 128
_MAX_COLLECTION_ITEMS: Final[int] = 10_000

_MISSING_FLAG_KEYS: Final[tuple[str, ...]] = (
    "required_scenario_missing",
    "scenario_script_missing",
    "scenario_asset_missing",
)
_REQUIRED_FLAG_KEYS: Final[tuple[str, ...]] = (
    "scenario_required",
    "required",
)
_VALID_SCRIPT_KEYS: Final[tuple[str, ...]] = (
    "scenario_script_valid",
    "valid_script_asset",
    "script_asset_valid",
)
_EXISTS_KEYS: Final[tuple[str, ...]] = (
    "scenario_exists",
    "scenario_script_exists",
    "script_asset_exists",
)
_SCENARIO_ID_KEYS: Final[tuple[str, ...]] = (
    "scenario_id",
    "subject_id",
)
_SCENARIO_PATH_KEYS: Final[tuple[str, ...]] = (
    "scenario_path",
    "script_path",
    "asset_path",
)

_INCOMPLETE_FLAG_KEYS: Final[tuple[str, ...]] = (
    "required_section_incomplete",
    "scenario_section_incomplete",
    "marker_contract_failed",
)
_INCOMPLETE_SECTION_KEYS: Final[tuple[str, ...]] = (
    "incomplete_required_sections",
    "incomplete_sections",
    "failed_section_ids",
)
_REQUIRED_SECTION_KEYS: Final[tuple[str, ...]] = (
    "required_section_ids",
    "required_sections",
)
_COMPLETED_SECTION_KEYS: Final[tuple[str, ...]] = (
    "completed_section_ids",
    "completed_sections",
)
_SECTION_ID_KEYS: Final[tuple[str, ...]] = (
    "section_id",
    "failed_section_id",
)
_MARKER_ERROR_KEYS: Final[tuple[str, ...]] = (
    "marker_error_code",
    "marker_error",
    "transition_error",
)

_EVIDENCE_CONTAINER_KEYS: Final[tuple[str, ...]] = (
    "metadata",
    "framework_facts",
    "scenario_facts",
    "contract_facts",
)

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class ScenarioPatternFacts:
    scenario_id: str | None
    scenario_path: str | None
    required: bool
    missing: bool
    valid_script: bool | None
    existing_script: bool | None
    incomplete_sections: tuple[str, ...]
    marker_error: str | None

    def __post_init__(self) -> None:
        _validate_optional_identifier(
            self.scenario_id,
            field="scenario_id",
        )
        _validate_optional_text(
            self.scenario_path,
            field="scenario_path",
        )
        if type(self.required) is not bool:
            raise TypeError("required must be bool")
        if type(self.missing) is not bool:
            raise TypeError("missing must be bool")
        if self.valid_script is not None and type(self.valid_script) is not bool:
            raise TypeError("valid_script must be bool or None")
        if self.existing_script is not None and type(
            self.existing_script
        ) is not bool:
            raise TypeError("existing_script must be bool or None")
        for section_id in self.incomplete_sections:
            _validate_identifier(section_id, field="incomplete section")
        _validate_optional_text(
            self.marker_error,
            field="marker_error",
        )


def scenario_pattern_facts(
    evidence: DiagnosticEvidence,
) -> ScenarioPatternFacts:
    sources = _evidence_sources(evidence)
    scenario_id = _first_text(sources, _SCENARIO_ID_KEYS)
    scenario_path = _first_path_text(sources, _SCENARIO_PATH_KEYS)

    explicit_missing = _first_optional_bool(
        sources,
        _MISSING_FLAG_KEYS,
    )
    required = _first_optional_bool(
        sources,
        _REQUIRED_FLAG_KEYS,
    )
    valid_script = _first_optional_bool(
        sources,
        _VALID_SCRIPT_KEYS,
    )
    existing_script = _first_optional_bool(
        sources,
        _EXISTS_KEYS,
    )

    missing = explicit_missing is True
    if explicit_missing is None and required is True:
        missing = existing_script is False or valid_script is False

    incomplete_sections = _resolve_incomplete_sections(sources)
    incomplete_flag = _first_optional_bool(
        sources,
        _INCOMPLETE_FLAG_KEYS,
    )
    explicit_section = _first_text(sources, _SECTION_ID_KEYS)
    if incomplete_flag is True and not incomplete_sections:
        incomplete_sections = (
            explicit_section
            if explicit_section is not None
            else "unknown-section",
        )

    marker_error = _first_text(sources, _MARKER_ERROR_KEYS)

    return ScenarioPatternFacts(
        scenario_id=scenario_id,
        scenario_path=scenario_path,
        required=(
            required is True
            or _canonical_required_missing_flag(sources)
        ),
        missing=missing,
        valid_script=valid_script,
        existing_script=existing_script,
        incomplete_sections=incomplete_sections,
        marker_error=marker_error,
    )


def match_required_scenario_missing(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    facts = scenario_pattern_facts(evidence)
    if not facts.required or not facts.missing:
        return None

    detail_parts: list[str] = []
    references: list[str] = []

    if facts.scenario_id is not None:
        detail_parts.append(f"scenario_id={facts.scenario_id}")
        references.append(f"scenario:{facts.scenario_id}")

    if facts.scenario_path is not None:
        detail_parts.append(f"scenario_path={facts.scenario_path}")
        references.append(facts.scenario_path)

    if facts.existing_script is False:
        detail_parts.append("script_exists=false")
    if facts.valid_script is False:
        detail_parts.append("script_valid=false")

    detail = _bounded_detail(detail_parts)
    identity = facts.scenario_id or facts.scenario_path or "required-scenario"

    return _new_match(
        evidence=evidence,
        pattern_id=REQUIRED_SCENARIO_MISSING_PATTERN_ID,
        error_kind="CONFIG",
        severity="error",
        confidence="authoritative",
        message="Required scenario is missing.",
        detail=detail,
        normalized_signature=(
            f"{REQUIRED_SCENARIO_MISSING_PATTERN_ID}|{identity}"
        ),
        references=_bounded_references(references),
    )


def match_required_section_incomplete(
    evidence: DiagnosticEvidence,
) -> PatternMatch | None:
    facts = scenario_pattern_facts(evidence)
    if not facts.incomplete_sections:
        return None

    section_id = facts.incomplete_sections[0]
    detail_parts: list[str] = [f"section_id={section_id}"]
    references: list[str] = [f"section:{section_id}"]

    if facts.scenario_id is not None:
        detail_parts.insert(0, f"scenario_id={facts.scenario_id}")
        references.insert(0, f"scenario:{facts.scenario_id}")

    if facts.scenario_path is not None:
        detail_parts.append(f"scenario_path={facts.scenario_path}")
        references.append(facts.scenario_path)

    if facts.marker_error is not None:
        detail_parts.append(f"marker_error={facts.marker_error}")

    if len(facts.incomplete_sections) > 1:
        remaining = ",".join(facts.incomplete_sections[1:])
        detail_parts.append(f"additional_sections={remaining}")

    detail = _bounded_detail(detail_parts)
    scenario_identity = facts.scenario_id or "unknown-scenario"

    return _new_match(
        evidence=evidence,
        pattern_id=REQUIRED_SECTION_INCOMPLETE_PATTERN_ID,
        error_kind="CONTRACT",
        severity="error",
        confidence="authoritative",
        message="Required scenario section did not complete.",
        detail=detail,
        normalized_signature=(
            f"{REQUIRED_SECTION_INCOMPLETE_PATTERN_ID}|"
            f"{scenario_identity}|{section_id}"
        ),
        references=_bounded_references(references),
    )


def canonical_scenario_patterns() -> tuple[DiagnosticPattern, ...]:
    return SCENARIO_PATTERNS


def get_scenario_pattern(
    pattern_id: str,
) -> DiagnosticPattern:
    _validate_identifier(pattern_id, field="pattern_id")
    try:
        return SCENARIO_PATTERN_BY_ID[pattern_id]
    except KeyError as exc:
        raise KeyError(
            f"unknown scenario diagnostic pattern {pattern_id!r}"
        ) from exc


def _new_pattern(
    *,
    pattern_id: str,
    priority: int,
    error_kind: str,
    matcher: object,
) -> DiagnosticPattern:
    candidates: dict[str, object] = {
        "pattern_id": pattern_id,
        "operations": _SCENARIO_OPERATIONS,
        "supported_operations": _SCENARIO_OPERATIONS,
        "streams": _FRAMEWORK_STATE_STREAMS,
        "stream_scope": "framework-state",
        "priority": priority,
        "precedence": priority,
        "confidence": "authoritative",
        "error_kind": error_kind,
        "severity": "error",
        "matcher": matcher,
        "lifecycle": "active",
        "lifecycle_state": "active",
        "pattern_version": PATTERN_VERSION,
        "supported_gf_versions": frozenset({"all"}),
        "supported_platforms": frozenset({"all"}),
        "fixtures": (),
        "notes": (
            "Authoritative Wordbench framework-state pattern; "
            "no GF text matching."
        ),
    }
    return _construct_supported(
        DiagnosticPattern,
        candidates,
        object_name="DiagnosticPattern",
    )


def _new_match(
    *,
    evidence: DiagnosticEvidence,
    pattern_id: str,
    error_kind: str,
    severity: str,
    confidence: str,
    message: str,
    detail: str,
    normalized_signature: str,
    references: tuple[str, ...],
) -> PatternMatch:
    operation = _operation_text(evidence)
    evidence_path = _evidence_path(evidence)

    candidates: dict[str, object] = {
        "pattern_id": pattern_id,
        "operation": operation,
        "operation_kind": operation,
        "stream": None,
        "source_stream": None,
        "start_line": None,
        "end_line": None,
        "severity": severity,
        "error_kind": error_kind,
        "message": message,
        "detail": detail,
        "source_path": evidence_path,
        "file_path": evidence_path,
        "source_module": None,
        "module_name": None,
        "line": None,
        "column": None,
        "end_line_number": None,
        "end_column": None,
        "symbol": None,
        "pattern_version": PATTERN_VERSION,
        "confidence": confidence,
        "raw_excerpt": "",
        "normalized_signature": normalized_signature,
        "continuation_lines": (),
        "is_fatal": False,
        "is_warning": False,
        "is_unknown": False,
        "references": references,
        "metadata": MappingProxyType(
            {
                "evidence_source": "framework-state",
                "pattern_version": PATTERN_VERSION,
            }
        ),
    }
    return _construct_supported(
        PatternMatch,
        candidates,
        object_name="PatternMatch",
    )


def _construct_supported(
    constructor: type[_T],
    candidates: Mapping[str, object],
    *,
    object_name: str,
) -> _T:
    try:
        parameters = signature(constructor).parameters
    except (TypeError, ValueError):
        return constructor(**dict(candidates))

    accepts_kwargs = any(
        parameter.kind is Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    if accepts_kwargs:
        kwargs = dict(candidates)
    else:
        kwargs = {
            name: candidates[name]
            for name in parameters
            if name in candidates
            and name not in {"self", "cls"}
        }

    missing: list[str] = []
    for name, parameter in parameters.items():
        if name in {"self", "cls"}:
            continue
        if parameter.kind in (
            Parameter.VAR_POSITIONAL,
            Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is not Parameter.empty:
            continue
        if name not in kwargs:
            missing.append(name)

    if missing:
        rendered = ", ".join(missing)
        raise TypeError(
            f"{object_name} requires unsupported fields: {rendered}"
        )

    return constructor(**kwargs)


def _evidence_sources(
    evidence: DiagnosticEvidence,
) -> tuple[object, ...]:
    sources: list[object] = [evidence]
    for key in _EVIDENCE_CONTAINER_KEYS:
        value = _read_member(evidence, key)
        if isinstance(value, Mapping):
            sources.append(value)
    return tuple(sources)


def _resolve_incomplete_sections(
    sources: Sequence[object],
) -> tuple[str, ...]:
    explicit = _first_text_collection(
        sources,
        _INCOMPLETE_SECTION_KEYS,
    )
    if explicit:
        return explicit

    required = _first_text_collection(
        sources,
        _REQUIRED_SECTION_KEYS,
    )
    completed = frozenset(
        _first_text_collection(
            sources,
            _COMPLETED_SECTION_KEYS,
        )
    )
    if not required:
        return ()

    return tuple(
        section_id
        for section_id in required
        if section_id not in completed
    )


def _canonical_required_missing_flag(
    sources: Sequence[object],
) -> bool:
    value = _first_optional_bool(
        sources,
        ("required_scenario_missing",),
    )
    return value is True


def _first_optional_bool(
    sources: Sequence[object],
    keys: Sequence[str],
) -> bool | None:
    for source in sources:
        for key in keys:
            value = _read_member(source, key)
            if value is None:
                continue
            if type(value) is not bool:
                raise TypeError(f"{key} must be bool")
            return value
    return None


def _first_text(
    sources: Sequence[object],
    keys: Sequence[str],
) -> str | None:
    for source in sources:
        for key in keys:
            value = _read_member(source, key)
            if value is None:
                continue
            return _coerce_text(value, field=key)
    return None


def _first_path_text(
    sources: Sequence[object],
    keys: Sequence[str],
) -> str | None:
    for source in sources:
        for key in keys:
            value = _read_member(source, key)
            if value is None:
                continue
            if not isinstance(value, (str, Path)):
                raise TypeError(f"{key} must be str or Path")
            text = str(value)
            _validate_text(text, field=key)
            return text
    return None


def _first_text_collection(
    sources: Sequence[object],
    keys: Sequence[str],
) -> tuple[str, ...]:
    for source in sources:
        for key in keys:
            value = _read_member(source, key)
            if value is None:
                continue
            return _coerce_text_collection(value, field=key)
    return ()


def _coerce_text_collection(
    value: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(value, str):
        item = _coerce_text(value, field=field)
        return (item,)
    if isinstance(value, Mapping):
        iterable: Iterable[object] = (
            key
            for key, included in value.items()
            if included is True
        )
    elif isinstance(value, Iterable):
        iterable = value
    else:
        raise TypeError(f"{field} must be an iterable of strings")

    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(iterable):
        if index >= _MAX_COLLECTION_ITEMS:
            raise ValueError(
                f"{field} exceeds {_MAX_COLLECTION_ITEMS} items"
            )
        text = _coerce_text(item, field=f"{field} item")
        _validate_identifier(text, field=f"{field} item")
        if text not in seen:
            result.append(text)
            seen.add(text)
    return tuple(result)


def _read_member(
    value: object,
    name: str,
) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _operation_text(
    evidence: DiagnosticEvidence,
) -> str:
    value = _read_member(evidence, "operation_kind")
    if value is None:
        value = _read_member(evidence, "operation")
    if value is None:
        return "run_scenario"
    enum_value = getattr(value, "value", value)
    return _coerce_text(enum_value, field="operation")


def _evidence_path(
    evidence: DiagnosticEvidence,
) -> Path | None:
    for name in (
        "evidence_path",
        "metadata_path",
        "scenario_path",
        "stdout_path",
        "stderr_path",
    ):
        value = _read_member(evidence, name)
        if value is None:
            continue
        if isinstance(value, Path):
            return value
        if isinstance(value, str):
            _validate_text(value, field=name)
            return Path(value)
    return None


def _bounded_detail(parts: Sequence[str]) -> str:
    filtered = [
        part
        for part in parts
        if part
    ]
    value = "; ".join(filtered)
    if len(value) <= _MAX_DETAIL_LENGTH:
        return value
    return f"{value[: _MAX_DETAIL_LENGTH - 3]}..."


def _bounded_references(
    references: Iterable[str],
) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in references:
        _validate_text(value, field="reference")
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
        if len(result) >= _MAX_REFERENCES:
            break
    return tuple(result)


def _coerce_text(
    value: object,
    *,
    field: str,
) -> str:
    enum_value = getattr(value, "value", value)
    if not isinstance(enum_value, str):
        raise TypeError(f"{field} must be a string")
    _validate_text(enum_value, field=field)
    return enum_value


def _validate_identifier(
    value: str,
    *,
    field: str,
) -> None:
    _validate_text(value, field=field)
    if len(value) > _MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"{field} exceeds {_MAX_IDENTIFIER_LENGTH} characters"
        )
    if any(character.isspace() for character in value):
        raise ValueError(f"{field} must not contain whitespace")


def _validate_optional_identifier(
    value: str | None,
    *,
    field: str,
) -> None:
    if value is not None:
        _validate_identifier(value, field=field)


def _validate_text(
    value: str,
    *,
    field: str,
) -> None:
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")


def _validate_optional_text(
    value: str | None,
    *,
    field: str,
) -> None:
    if value is not None:
        _validate_text(value, field=field)


REQUIRED_SCENARIO_MISSING_PATTERN: Final[DiagnosticPattern] = (
    _new_pattern(
        pattern_id=REQUIRED_SCENARIO_MISSING_PATTERN_ID,
        priority=_REQUIRED_SCENARIO_MISSING_PRIORITY,
        error_kind="CONFIG",
        matcher=match_required_scenario_missing,
    )
)

REQUIRED_SECTION_INCOMPLETE_PATTERN: Final[DiagnosticPattern] = (
    _new_pattern(
        pattern_id=REQUIRED_SECTION_INCOMPLETE_PATTERN_ID,
        priority=_REQUIRED_SECTION_INCOMPLETE_PRIORITY,
        error_kind="CONTRACT",
        matcher=match_required_section_incomplete,
    )
)

SCENARIO_PATTERNS: Final[tuple[DiagnosticPattern, ...]] = (
    REQUIRED_SCENARIO_MISSING_PATTERN,
    REQUIRED_SECTION_INCOMPLETE_PATTERN,
)

SCENARIO_PATTERN_BY_ID: Final[Mapping[str, DiagnosticPattern]] = (
    MappingProxyType(
        {
            REQUIRED_SCENARIO_MISSING_PATTERN_ID: (
                REQUIRED_SCENARIO_MISSING_PATTERN
            ),
            REQUIRED_SECTION_INCOMPLETE_PATTERN_ID: (
                REQUIRED_SECTION_INCOMPLETE_PATTERN
            ),
        }
    )
)

__all__ = (
    "PATTERN_VERSION",
    "REQUIRED_SCENARIO_MISSING_PATTERN",
    "REQUIRED_SCENARIO_MISSING_PATTERN_ID",
    "REQUIRED_SECTION_INCOMPLETE_PATTERN",
    "REQUIRED_SECTION_INCOMPLETE_PATTERN_ID",
    "SCENARIO_PATTERNS",
    "SCENARIO_PATTERN_BY_ID",
    "ScenarioPatternFacts",
    "canonical_scenario_patterns",
    "get_scenario_pattern",
    "match_required_scenario_missing",
    "match_required_section_incomplete",
    "scenario_pattern_facts",
)
