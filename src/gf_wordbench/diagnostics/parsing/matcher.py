"""Deterministic diagnostic-pattern matching for GF Wordbench."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, Generic, Protocol, TypeVar, runtime_checkable

_MAX_PATTERNS: Final[int] = 4_096
_MAX_MATCHES: Final[int] = 10_000
_MAX_WARNINGS: Final[int] = 256
_MAX_TEXT_FIELD: Final[int] = 8_192
_UNSCOPED_VALUES: Final[frozenset[str]] = frozenset({"*", "all", "any", "either"})
_ACTIVE_LIFECYCLES: Final[frozenset[str]] = frozenset({"active", "deprecated", "experimental"})
_RETIRED_LIFECYCLES: Final[frozenset[str]] = frozenset({"retired"})
_STREAM_VALUES: Final[frozenset[str]] = frozenset(
    {
        "stdout",
        "stderr",
        "either",
        "both-structure",
        "process-state",
        "filesystem",
        "framework-state",
    }
)

_MatchT = TypeVar("_MatchT")


@unique
class MatchStrictness(StrEnum):
    TOLERANT = "tolerant"
    STRICT = "strict"


@unique
class MatcherWarningCode(StrEnum):
    PATTERN_SKIPPED = "pattern_skipped"
    PATTERN_DEPRECATED = "pattern_deprecated"
    PATTERN_EXPERIMENTAL = "pattern_experimental"
    PATTERN_ERROR = "pattern_error"
    INVALID_MATCH = "invalid_match"
    DUPLICATE_MATCH = "duplicate_match"
    MATCH_LIMIT_REACHED = "match_limit_reached"
    WARNING_LIMIT_REACHED = "warning_limit_reached"
    COMPATIBILITY_UNKNOWN = "compatibility_unknown"


@dataclass(frozen=True, slots=True)
class MatcherWarning:
    code: MatcherWarningCode
    pattern_id: str | None
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, MatcherWarningCode):
            raise TypeError("code must be MatcherWarningCode")
        if self.pattern_id is not None:
            _require_text(
                self.pattern_id,
                field="pattern_id",
                max_length=256,
            )
        _require_text(
            self.message,
            field="message",
            max_length=_MAX_TEXT_FIELD,
        )


@dataclass(frozen=True, slots=True)
class PatternMatchBatch(Generic[_MatchT]):
    matches: tuple[_MatchT, ...]
    warnings: tuple[MatcherWarning, ...]
    attempted_pattern_ids: tuple[str, ...]
    skipped_pattern_ids: tuple[str, ...]
    complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.matches, tuple):
            raise TypeError("matches must be a tuple")
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple")
        if not all(isinstance(item, MatcherWarning) for item in self.warnings):
            raise TypeError("warnings must contain MatcherWarning values")
        attempted = _text_tuple(
            self.attempted_pattern_ids,
            field="attempted_pattern_ids",
        )
        skipped = _text_tuple(
            self.skipped_pattern_ids,
            field="skipped_pattern_ids",
        )
        if len(attempted) != len(set(attempted)):
            raise ValueError("attempted_pattern_ids must be unique")
        if len(skipped) != len(set(skipped)):
            raise ValueError("skipped_pattern_ids must be unique")
        if type(self.complete) is not bool:
            raise TypeError("complete must be bool")
        object.__setattr__(self, "attempted_pattern_ids", attempted)
        object.__setattr__(self, "skipped_pattern_ids", skipped)


class PatternContractError(ValueError):
    pass


class PatternExecutionError(RuntimeError):
    pass


@runtime_checkable
class _PatternProtocol(Protocol):
    pattern_id: str
    matcher: object


def match_diagnostic_patterns(
    patterns: Iterable[object],
    evidence: object,
    *,
    strictness: MatchStrictness | str = MatchStrictness.TOLERANT,
    max_matches: int = _MAX_MATCHES,
) -> PatternMatchBatch[object]:
    mode = _coerce_strictness(strictness)
    limit = _positive_int(
        max_matches,
        field="max_matches",
        maximum=_MAX_MATCHES,
    )
    ordered = prepare_pattern_order(patterns)
    matches: list[object] = []
    warnings: list[MatcherWarning] = []
    attempted: list[str] = []
    skipped: list[str] = []
    seen_match_keys: set[tuple[object, ...]] = set()
    complete = True

    for pattern in ordered:
        pattern_id = _pattern_id(pattern)
        applicability = pattern_applicability(pattern, evidence)

        if not applicability.applicable:
            skipped.append(pattern_id)
            if applicability.warning is not None:
                _append_warning(warnings, applicability.warning)
            continue

        if applicability.warning is not None:
            _append_warning(warnings, applicability.warning)

        attempted.append(pattern_id)

        try:
            produced = match_one_pattern(
                pattern,
                evidence,
                strictness=mode,
            )
        except PatternExecutionError:
            raise
        except Exception as exc:
            if mode is MatchStrictness.STRICT:
                raise PatternExecutionError(f"pattern {pattern_id!r} failed") from exc
            complete = False
            _append_warning(
                warnings,
                MatcherWarning(
                    code=MatcherWarningCode.PATTERN_ERROR,
                    pattern_id=pattern_id,
                    message=_exception_message(exc),
                ),
            )
            continue

        for match in produced:
            if len(matches) >= limit:
                complete = False
                _append_warning(
                    warnings,
                    MatcherWarning(
                        code=MatcherWarningCode.MATCH_LIMIT_REACHED,
                        pattern_id=pattern_id,
                        message=(f"diagnostic match limit {limit} was reached"),
                    ),
                )
                return PatternMatchBatch(
                    matches=tuple(matches),
                    warnings=tuple(warnings),
                    attempted_pattern_ids=tuple(attempted),
                    skipped_pattern_ids=tuple(skipped),
                    complete=complete,
                )

            try:
                _validate_match(pattern, match)
            except Exception as exc:
                if mode is MatchStrictness.STRICT:
                    raise PatternExecutionError(
                        f"pattern {pattern_id!r} returned an invalid match"
                    ) from exc
                complete = False
                _append_warning(
                    warnings,
                    MatcherWarning(
                        code=MatcherWarningCode.INVALID_MATCH,
                        pattern_id=pattern_id,
                        message=_exception_message(exc),
                    ),
                )
                continue

            key = diagnostic_match_key(match)
            if key in seen_match_keys:
                _append_warning(
                    warnings,
                    MatcherWarning(
                        code=MatcherWarningCode.DUPLICATE_MATCH,
                        pattern_id=pattern_id,
                        message=(
                            "duplicate semantic match was omitted while "
                            "preserving stream provenance"
                        ),
                    ),
                )
                continue

            seen_match_keys.add(key)
            matches.append(match)

    return PatternMatchBatch(
        matches=tuple(matches),
        warnings=tuple(warnings),
        attempted_pattern_ids=tuple(attempted),
        skipped_pattern_ids=tuple(skipped),
        complete=complete,
    )


def match_one_pattern(
    pattern: object,
    evidence: object,
    *,
    strictness: MatchStrictness | str = MatchStrictness.TOLERANT,
) -> tuple[object, ...]:
    mode = _coerce_strictness(strictness)
    pattern_id = _pattern_id(pattern)
    matcher = getattr(pattern, "matcher", None)
    if not callable(matcher):
        raise PatternContractError(f"pattern {pattern_id!r} matcher must be callable")

    try:
        value = matcher(evidence)
    except Exception as exc:
        raise PatternExecutionError(
            f"pattern {pattern_id!r} matcher raised {type(exc).__name__}: {_safe_text(str(exc))}"
        ) from exc

    if value is None:
        return ()

    if _looks_like_match(value):
        return (value,)

    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise PatternContractError(f"pattern {pattern_id!r} returned an unsupported match value")

    if isinstance(value, Iterable):
        result = tuple(value)
        if len(result) > _MAX_MATCHES:
            raise PatternContractError(f"pattern {pattern_id!r} returned too many matches")
        if any(item is None for item in result):
            raise PatternContractError(
                f"pattern {pattern_id!r} returned None inside a match sequence"
            )
        return result

    if mode is MatchStrictness.STRICT:
        raise PatternContractError(
            f"pattern {pattern_id!r} returned an unsupported type {type(value).__name__}"
        )
    return (value,)


@dataclass(frozen=True, slots=True)
class PatternApplicability:
    applicable: bool
    warning: MatcherWarning | None = None

    def __post_init__(self) -> None:
        if type(self.applicable) is not bool:
            raise TypeError("applicable must be bool")
        if self.warning is not None and not isinstance(
            self.warning,
            MatcherWarning,
        ):
            raise TypeError("warning must be MatcherWarning or None")


def pattern_applicability(
    pattern: object,
    evidence: object,
) -> PatternApplicability:
    pattern_id = _pattern_id(pattern)
    lifecycle = _normalized_optional_text(
        _first_attribute(
            pattern,
            "lifecycle_state",
            "lifecycle",
            default="active",
        )
    )

    if lifecycle in _RETIRED_LIFECYCLES:
        return PatternApplicability(
            applicable=False,
            warning=MatcherWarning(
                code=MatcherWarningCode.PATTERN_SKIPPED,
                pattern_id=pattern_id,
                message="retired diagnostic pattern was skipped",
            ),
        )

    if lifecycle not in _ACTIVE_LIFECYCLES:
        return PatternApplicability(
            applicable=False,
            warning=MatcherWarning(
                code=MatcherWarningCode.PATTERN_SKIPPED,
                pattern_id=pattern_id,
                message=(f"unsupported pattern lifecycle {lifecycle!r} was skipped"),
            ),
        )

    operation = _evidence_operation(evidence)
    operations = _scope_values(
        _first_attribute(
            pattern,
            "supported_operations",
            "operations",
            default=(),
        )
    )
    if operations and not _scope_contains(operations, operation):
        return PatternApplicability(applicable=False)

    platform = _normalized_optional_text(
        _first_attribute(evidence, "platform", "platform_id", default=None)
    )
    platforms = _scope_values(
        _first_attribute(
            pattern,
            "supported_platforms",
            "platforms",
            default=(),
        )
    )
    if platforms:
        if platform is None:
            return PatternApplicability(
                applicable=False,
                warning=MatcherWarning(
                    code=MatcherWarningCode.COMPATIBILITY_UNKNOWN,
                    pattern_id=pattern_id,
                    message=(
                        "pattern platform scope could not be evaluated because "
                        "evidence has no platform"
                    ),
                ),
            )
        if not _scope_contains(platforms, platform):
            return PatternApplicability(applicable=False)

    stream = _evidence_stream(evidence)
    stream_scope = _pattern_stream_scope(pattern)
    if stream is not None and not _stream_scope_accepts(
        stream_scope,
        stream,
    ):
        return PatternApplicability(applicable=False)

    version_check = _version_applicability(pattern, evidence)
    if not version_check.applicable:
        return version_check

    if lifecycle == "deprecated":
        return PatternApplicability(
            applicable=True,
            warning=MatcherWarning(
                code=MatcherWarningCode.PATTERN_DEPRECATED,
                pattern_id=pattern_id,
                message="deprecated diagnostic pattern was evaluated",
            ),
        )

    if lifecycle == "experimental":
        return PatternApplicability(
            applicable=True,
            warning=MatcherWarning(
                code=MatcherWarningCode.PATTERN_EXPERIMENTAL,
                pattern_id=pattern_id,
                message=(
                    "experimental diagnostic pattern matched evidence but must "
                    "not independently determine release success"
                ),
            ),
        )

    return PatternApplicability(applicable=True)


def prepare_pattern_order(
    patterns: Iterable[object],
) -> tuple[object, ...]:
    if isinstance(patterns, (str, bytes, bytearray, Mapping)):
        raise TypeError("patterns must be an iterable of pattern objects")

    prepared = tuple(patterns)
    if not prepared:
        return ()
    if len(prepared) > _MAX_PATTERNS:
        raise PatternContractError(f"pattern registry exceeds {_MAX_PATTERNS} entries")

    seen_ids: set[str] = set()
    indexed: list[tuple[int, int, object]] = []

    for registry_index, pattern in enumerate(prepared):
        pattern_id = _pattern_id(pattern)
        if pattern_id in seen_ids:
            raise PatternContractError(f"duplicate diagnostic pattern ID {pattern_id!r}")
        seen_ids.add(pattern_id)
        priority = _pattern_priority(pattern)
        indexed.append((priority, registry_index, pattern))

    indexed.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in indexed)


def validate_pattern_registry_order(
    patterns: Sequence[object],
) -> tuple[str, ...]:
    prepared = tuple(patterns)
    ordered = prepare_pattern_order(prepared)
    if ordered != prepared:
        expected = tuple(_pattern_id(item) for item in ordered)
        actual = tuple(_pattern_id(item) for item in prepared)
        raise PatternContractError(
            "pattern registry is not in canonical precedence order; "
            f"actual={actual!r}, expected={expected!r}"
        )
    return tuple(_pattern_id(item) for item in prepared)


def iter_applicable_patterns(
    patterns: Iterable[object],
    evidence: object,
) -> Iterator[object]:
    for pattern in prepare_pattern_order(patterns):
        if pattern_applicability(pattern, evidence).applicable:
            yield pattern


def diagnostic_match_key(match: object) -> tuple[object, ...]:
    stream = _normalized_optional_text(
        _first_attribute(
            match,
            "stream",
            "source_stream",
            default=None,
        )
    )
    start_line = _optional_int(
        _first_attribute(match, "start_line", default=None),
        field="start_line",
    )
    end_line = _optional_int(
        _first_attribute(match, "end_line", default=start_line),
        field="end_line",
    )
    pattern_id = _normalized_optional_text(_first_attribute(match, "pattern_id", default=None))
    signature = _normalized_optional_text(
        _first_attribute(
            match,
            "normalized_signature",
            "signature",
            default=None,
        )
    )
    message = _normalized_optional_text(_first_attribute(match, "message", default=None))

    identity = signature if signature is not None else message
    return (
        stream,
        start_line,
        end_line,
        pattern_id,
        identity,
    )


def _validate_match(pattern: object, match: object) -> None:
    pattern_id = _pattern_id(pattern)
    returned_pattern_id = _normalized_optional_text(
        _first_attribute(match, "pattern_id", default=None)
    )
    if returned_pattern_id is not None and returned_pattern_id != pattern_id:
        raise PatternContractError(
            f"match pattern_id {returned_pattern_id!r} does not match "
            f"executed pattern {pattern_id!r}"
        )

    stream = _normalized_optional_text(
        _first_attribute(
            match,
            "stream",
            "source_stream",
            default=None,
        )
    )
    if stream is not None and stream not in {"stdout", "stderr"}:
        raise PatternContractError(f"match stream must be stdout or stderr, got {stream!r}")

    start_line = _optional_int(
        _first_attribute(match, "start_line", default=None),
        field="start_line",
    )
    end_line = _optional_int(
        _first_attribute(match, "end_line", default=start_line),
        field="end_line",
    )
    if start_line is not None and start_line < 1:
        raise PatternContractError("match start_line must be positive")
    if end_line is not None and end_line < 1:
        raise PatternContractError("match end_line must be positive")
    if start_line is not None and end_line is not None and end_line < start_line:
        raise PatternContractError("match end_line must not precede start_line")

    for field in (
        "message",
        "detail",
        "raw_excerpt",
        "normalized_signature",
    ):
        value = _first_attribute(match, field, default=None)
        if value is None:
            continue
        if not isinstance(value, str):
            raise PatternContractError(f"match {field} must be a string")
        if "\x00" in value:
            raise PatternContractError(f"match {field} must not contain NUL")
        if len(value) > _MAX_TEXT_FIELD * 16:
            raise PatternContractError(f"match {field} exceeds the matcher safety bound")

    for forbidden in ("diagnostic_class", "causal_class", "blocked_by"):
        value = _first_attribute(match, forbidden, default=None)
        if value not in (None, "", (), [], {}, frozenset()):
            raise PatternContractError(f"matcher output must not assign causal field {forbidden!r}")


def _version_applicability(
    pattern: object,
    evidence: object,
) -> PatternApplicability:
    pattern_id = _pattern_id(pattern)
    predicate = _first_attribute(
        pattern,
        "supports_gf_version",
        "supports_version",
        default=None,
    )
    gf_version = _normalized_optional_text(
        _first_attribute(
            evidence,
            "gf_version",
            "tool_version",
            default=None,
        )
    )

    if callable(predicate):
        try:
            result = predicate(gf_version)
        except Exception as exc:
            return PatternApplicability(
                applicable=False,
                warning=MatcherWarning(
                    code=MatcherWarningCode.COMPATIBILITY_UNKNOWN,
                    pattern_id=pattern_id,
                    message=(f"pattern version predicate failed: {_exception_message(exc)}"),
                ),
            )
        if type(result) is not bool:
            return PatternApplicability(
                applicable=False,
                warning=MatcherWarning(
                    code=MatcherWarningCode.COMPATIBILITY_UNKNOWN,
                    pattern_id=pattern_id,
                    message="pattern version predicate did not return bool",
                ),
            )
        return PatternApplicability(applicable=result)

    versions = _scope_values(
        _first_attribute(
            pattern,
            "supported_gf_versions",
            "gf_versions",
            default=(),
        )
    )
    if not versions:
        return PatternApplicability(applicable=True)
    if gf_version is None:
        return PatternApplicability(
            applicable=False,
            warning=MatcherWarning(
                code=MatcherWarningCode.COMPATIBILITY_UNKNOWN,
                pattern_id=pattern_id,
                message=(
                    "pattern GF-version scope could not be evaluated because "
                    "evidence has no GF version"
                ),
            ),
        )
    return PatternApplicability(applicable=_scope_contains(versions, gf_version))


def _pattern_stream_scope(pattern: object) -> frozenset[str]:
    raw = _first_attribute(
        pattern,
        "stream_scope",
        "streams",
        default=(),
    )
    values = _scope_values(raw)
    if not values:
        return frozenset({"either"})
    unknown = values.difference(_STREAM_VALUES)
    if unknown:
        raise PatternContractError(
            f"pattern {_pattern_id(pattern)!r} has unsupported stream scope: {sorted(unknown)!r}"
        )
    return values


def _stream_scope_accepts(
    scope: frozenset[str],
    stream: str,
) -> bool:
    if scope.intersection({"either", "both-structure"}):
        return stream in {"stdout", "stderr"}
    if scope.intersection({"process-state", "filesystem", "framework-state"}):
        return False
    return stream in scope


def _pattern_priority(pattern: object) -> int:
    value = _first_attribute(
        pattern,
        "priority",
        "precedence",
        default=None,
    )
    if type(value) is not int:
        raise PatternContractError(f"pattern {_pattern_id(pattern)!r} priority must be an integer")
    if value < 0:
        raise PatternContractError(
            f"pattern {_pattern_id(pattern)!r} priority must be non-negative"
        )
    return value


def _pattern_id(pattern: object) -> str:
    if not isinstance(pattern, _PatternProtocol):
        candidate = getattr(pattern, "pattern_id", None)
    else:
        candidate = pattern.pattern_id
    return _require_text(
        candidate,
        field="pattern_id",
        max_length=256,
    )


def _evidence_operation(evidence: object) -> str | None:
    value = _first_attribute(
        evidence,
        "operation_kind",
        "operation",
        default=None,
    )
    if value is None:
        return None
    return _enum_or_text(value)


def _evidence_stream(evidence: object) -> str | None:
    value = _first_attribute(
        evidence,
        "stream",
        "source_stream",
        default=None,
    )
    if value is None:
        return None
    stream = _enum_or_text(value)
    if stream not in {"stdout", "stderr"}:
        return None
    return stream


def _scope_values(value: object) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({_normalize_scope_value(value)})
    if isinstance(value, Mapping):
        raise TypeError("scope values must not be a mapping")
    if not isinstance(value, Iterable):
        raise TypeError("scope values must be iterable")
    result: set[str] = set()
    for item in value:
        result.add(_normalize_scope_value(_enum_or_text(item)))
    return frozenset(result)


def _scope_contains(
    scope: frozenset[str],
    value: str | None,
) -> bool:
    if scope.intersection(_UNSCOPED_VALUES):
        return True
    if value is None:
        return False
    normalized = _normalize_scope_value(value)
    if normalized in scope:
        return True
    major = normalized.split(".", 1)[0]
    return major in scope


def _normalize_scope_value(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _enum_or_text(value: object) -> str:
    enum_value = getattr(value, "value", value)
    if not isinstance(enum_value, str):
        raise TypeError("scope value must be a string or string enum")
    return _require_text(
        enum_value,
        field="scope value",
        max_length=256,
    )


def _looks_like_match(value: object) -> bool:
    return any(
        hasattr(value, field)
        for field in (
            "pattern_id",
            "message",
            "raw_excerpt",
            "normalized_signature",
        )
    )


def _first_attribute(
    value: object,
    *names: str,
    default: object,
) -> object:
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
        if isinstance(value, Mapping) and name in value:
            return value[name]
    return default


def _append_warning(
    warnings: list[MatcherWarning],
    warning: MatcherWarning,
) -> None:
    if len(warnings) < _MAX_WARNINGS:
        warnings.append(warning)
        return
    if warnings and warnings[-1].code is MatcherWarningCode.WARNING_LIMIT_REACHED:
        return
    replacement = MatcherWarning(
        code=MatcherWarningCode.WARNING_LIMIT_REACHED,
        pattern_id=None,
        message="additional matcher warnings were omitted",
    )
    if warnings:
        warnings[-1] = replacement
    else:
        warnings.append(replacement)


def _coerce_strictness(
    value: MatchStrictness | str,
) -> MatchStrictness:
    if isinstance(value, MatchStrictness):
        return value
    if not isinstance(value, str):
        raise TypeError("strictness must be MatchStrictness or string")
    try:
        return MatchStrictness(value)
    except ValueError as exc:
        raise ValueError(f"unknown matcher strictness {value!r}") from exc


def _normalized_optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _enum_or_text(value)


def _optional_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise PatternContractError(f"{field} must be an integer or None")
    return value


def _positive_int(
    value: object,
    *,
    field: str,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1 or value > maximum:
        raise ValueError(f"{field} must be between 1 and {maximum}")
    return value


def _require_text(
    value: object,
    *,
    field: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds the supported length")
    return value


def _text_tuple(
    values: Iterable[str],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field} must be an iterable of strings")
    result = tuple(values)
    for item in result:
        _require_text(item, field=f"{field} item", max_length=256)
    return result


def _safe_text(value: str) -> str:
    text = " ".join(value.replace("\x00", "\\x00").split())
    if not text:
        return "no safe diagnostic message"
    if len(text) > _MAX_TEXT_FIELD:
        return f"{text[: _MAX_TEXT_FIELD - 3]}..."
    return text


def _exception_message(exc: Exception) -> str:
    return f"{type(exc).__name__}: {_safe_text(str(exc))}"


__all__ = (
    "MatchStrictness",
    "MatcherWarning",
    "MatcherWarningCode",
    "PatternApplicability",
    "PatternContractError",
    "PatternExecutionError",
    "PatternMatchBatch",
    "diagnostic_match_key",
    "iter_applicable_patterns",
    "match_diagnostic_patterns",
    "match_one_pattern",
    "pattern_applicability",
    "prepare_pattern_order",
    "validate_pattern_registry_order",
)
