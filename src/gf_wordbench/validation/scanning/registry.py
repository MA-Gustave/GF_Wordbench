"""Canonical built-in static-scan rule registry for GF Wordbench."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, Literal, Mapping, NewType

ScanRuleId = NewType("ScanRuleId", str)
ScanCountField = Literal[
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
]

BUILTIN_RULE_SET_ID: Final[str] = "gf-wordbench.static-scanning"
BUILTIN_RULE_SET_VERSION: Final[str] = "2.0.0"

_RULE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^SCAN-(?P<domain>NOTATION|RUNTIME|PATTERN|STYLE)-(?P<number>[0-9]{3})$"
)
_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)$"
)
_RULE_SET_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$"
)

_CANONICAL_COUNT_FIELDS: Final[tuple[ScanCountField, ...]] = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
)


@unique
class ScanRuleDomain(StrEnum):
    NOTATION = "NOTATION"
    RUNTIME = "RUNTIME"
    PATTERN = "PATTERN"
    STYLE = "STYLE"


@unique
class ScanTextView(StrEnum):
    ORIGINAL = "original"
    COMMENT_STRIPPED = "comment_stripped"
    STRING_MASKED = "string_masked"


@unique
class ScanCountUnit(StrEnum):
    SOURCE_LINE = "source_line"
    CASE_BLOCK = "case_block"
    TABLE_BLOCK = "table_block"


@unique
class ScanRuleSeverity(StrEnum):
    WARNING = "warning"
    ADVISORY = "advisory"


def validate_scan_rule_id(value: object) -> ScanRuleId:
    if not isinstance(value, str):
        raise TypeError("scan rule ID must be a string")
    if _RULE_ID_RE.fullmatch(value) is None:
        raise ValueError(
            "scan rule ID must match "
            "SCAN-(NOTATION|RUNTIME|PATTERN|STYLE)-NNN"
        )
    return ScanRuleId(value)


def _validate_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    return value


def _validate_count_field(value: object) -> ScanCountField:
    if not isinstance(value, str):
        raise TypeError("count_field must be a string")
    if value not in _CANONICAL_COUNT_FIELDS:
        expected = ", ".join(_CANONICAL_COUNT_FIELDS)
        raise ValueError(
            f"unsupported ScanCounts field {value!r}; expected one of {expected}"
        )
    return value  # type: ignore[return-value]


def _normalize_views(
    values: tuple[ScanTextView, ...],
) -> tuple[ScanTextView, ...]:
    if not isinstance(values, tuple):
        raise TypeError("source_views must be a tuple")
    if not values:
        raise ValueError("source_views must not be empty")
    if not all(isinstance(value, ScanTextView) for value in values):
        raise TypeError("source_views must contain only ScanTextView values")
    if len(values) != len(set(values)):
        raise ValueError("source_views must not contain duplicates")
    return values


@dataclass(frozen=True, slots=True)
class ScanRuleDefinition:
    rule_id: ScanRuleId
    domain: ScanRuleDomain
    count_field: ScanCountField
    count_unit: ScanCountUnit
    source_views: tuple[ScanTextView, ...]
    default_severity: ScanRuleSeverity
    interpretation: str
    order: int

    def __post_init__(self) -> None:
        rule_id = validate_scan_rule_id(self.rule_id)
        match = _RULE_ID_RE.fullmatch(rule_id)
        if match is None:
            raise AssertionError("validated rule ID no longer matches its pattern")
        if not isinstance(self.domain, ScanRuleDomain):
            raise TypeError("domain must be a ScanRuleDomain")
        if match.group("domain") != self.domain.value:
            raise ValueError("rule ID domain must agree with domain")
        count_field = _validate_count_field(self.count_field)
        if not isinstance(self.count_unit, ScanCountUnit):
            raise TypeError("count_unit must be a ScanCountUnit")
        source_views = _normalize_views(self.source_views)
        if not isinstance(self.default_severity, ScanRuleSeverity):
            raise TypeError("default_severity must be a ScanRuleSeverity")
        interpretation = _validate_text(
            self.interpretation,
            field_name="interpretation",
        )
        if type(self.order) is not int:
            raise TypeError("order must be an integer")
        if self.order < 0:
            raise ValueError("order must be non-negative")
        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "count_field", count_field)
        object.__setattr__(self, "source_views", source_views)
        object.__setattr__(self, "interpretation", interpretation)

    @property
    def is_line_rule(self) -> bool:
        return self.count_unit is ScanCountUnit.SOURCE_LINE

    @property
    def is_block_rule(self) -> bool:
        return self.count_unit in {
            ScanCountUnit.CASE_BLOCK,
            ScanCountUnit.TABLE_BLOCK,
        }


@dataclass(frozen=True, slots=True)
class ScanRuleSet:
    rule_set_id: str
    version: str
    rules: tuple[ScanRuleDefinition, ...]
    _by_id: Mapping[ScanRuleId, ScanRuleDefinition] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _by_count_field: Mapping[ScanCountField, ScanRuleDefinition] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        rule_set_id = _validate_text(
            self.rule_set_id,
            field_name="rule_set_id",
        )
        if _RULE_SET_ID_RE.fullmatch(rule_set_id) is None:
            raise ValueError(
                "rule_set_id must use lowercase dot- or hyphen-separated tokens"
            )
        version = _validate_text(self.version, field_name="version")
        if _VERSION_RE.fullmatch(version) is None:
            raise ValueError("version must use MAJOR.MINOR.PATCH")
        if not isinstance(self.rules, tuple):
            raise TypeError("rules must be a tuple")
        if not self.rules:
            raise ValueError("rules must not be empty")
        if not all(isinstance(rule, ScanRuleDefinition) for rule in self.rules):
            raise TypeError("rules must contain only ScanRuleDefinition values")

        ordered = tuple(sorted(self.rules, key=lambda rule: rule.order))
        orders = tuple(rule.order for rule in ordered)
        if len(orders) != len(set(orders)):
            raise ValueError("rule order values must be unique")

        ids = tuple(rule.rule_id for rule in ordered)
        if len(ids) != len(set(ids)):
            raise ValueError("rule IDs must be unique")

        fields = tuple(rule.count_field for rule in ordered)
        if len(fields) != len(set(fields)):
            raise ValueError("ScanCounts fields must be unique")

        object.__setattr__(self, "rule_set_id", rule_set_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "rules", ordered)
        object.__setattr__(
            self,
            "_by_id",
            MappingProxyType({rule.rule_id: rule for rule in ordered}),
        )
        object.__setattr__(
            self,
            "_by_count_field",
            MappingProxyType({rule.count_field: rule for rule in ordered}),
        )

    @property
    def identity(self) -> str:
        return f"{self.rule_set_id}@{self.version}"

    @property
    def rule_ids(self) -> tuple[ScanRuleId, ...]:
        return tuple(rule.rule_id for rule in self.rules)

    @property
    def count_fields(self) -> tuple[ScanCountField, ...]:
        return tuple(rule.count_field for rule in self.rules)

    def get(self, rule_id: object) -> ScanRuleDefinition | None:
        try:
            canonical = validate_scan_rule_id(rule_id)
        except (TypeError, ValueError):
            return None
        return self._by_id.get(canonical)

    def require(self, rule_id: object) -> ScanRuleDefinition:
        canonical = validate_scan_rule_id(rule_id)
        try:
            return self._by_id[canonical]
        except KeyError as exc:
            raise KeyError(f"unknown scan rule ID: {canonical}") from exc

    def get_by_count_field(
        self,
        count_field: object,
    ) -> ScanRuleDefinition | None:
        try:
            canonical = _validate_count_field(count_field)
        except (TypeError, ValueError):
            return None
        return self._by_count_field.get(canonical)

    def require_by_count_field(
        self,
        count_field: object,
    ) -> ScanRuleDefinition:
        canonical = _validate_count_field(count_field)
        try:
            return self._by_count_field[canonical]
        except KeyError as exc:
            raise KeyError(
                f"unregistered ScanCounts field: {canonical}"
            ) from exc

    def __iter__(self) -> Iterator[ScanRuleDefinition]:
        return iter(self.rules)

    def __len__(self) -> int:
        return len(self.rules)


BUILTIN_RULES: Final[tuple[ScanRuleDefinition, ...]] = (
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-NOTATION-001"),
        domain=ScanRuleDomain.NOTATION,
        count_field="single_slash_eq",
        count_unit=ScanCountUnit.SOURCE_LINE,
        source_views=(ScanTextView.STRING_MASKED,),
        default_severity=ScanRuleSeverity.WARNING,
        interpretation="suspicious single-backslash before =>",
        order=0,
    ),
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-NOTATION-002"),
        domain=ScanRuleDomain.NOTATION,
        count_field="double_slash_dash",
        count_unit=ScanCountUnit.SOURCE_LINE,
        source_views=(ScanTextView.STRING_MASKED,),
        default_severity=ScanRuleSeverity.WARNING,
        interpretation="suspicious double-backslash before ->",
        order=1,
    ),
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-RUNTIME-001"),
        domain=ScanRuleDomain.RUNTIME,
        count_field="runtime_str_match",
        count_unit=ScanCountUnit.CASE_BLOCK,
        source_views=(
            ScanTextView.STRING_MASKED,
            ScanTextView.COMMENT_STRIPPED,
        ),
        default_severity=ScanRuleSeverity.WARNING,
        interpretation="runtime string-literal matching on a .s expression",
        order=2,
    ),
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-PATTERN-001"),
        domain=ScanRuleDomain.PATTERN,
        count_field="untyped_case_str_pat",
        count_unit=ScanCountUnit.CASE_BLOCK,
        source_views=(
            ScanTextView.STRING_MASKED,
            ScanTextView.COMMENT_STRIPPED,
        ),
        default_severity=ScanRuleSeverity.WARNING,
        interpretation=(
            "case string-concatenation pattern without explicit : Str > form"
        ),
        order=3,
    ),
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-PATTERN-002"),
        domain=ScanRuleDomain.PATTERN,
        count_field="untyped_table_str_pat",
        count_unit=ScanCountUnit.TABLE_BLOCK,
        source_views=(
            ScanTextView.STRING_MASKED,
            ScanTextView.COMMENT_STRIPPED,
        ),
        default_severity=ScanRuleSeverity.WARNING,
        interpretation=(
            "table string-concatenation pattern without explicit : Str > form"
        ),
        order=4,
    ),
    ScanRuleDefinition(
        rule_id=ScanRuleId("SCAN-STYLE-001"),
        domain=ScanRuleDomain.STYLE,
        count_field="trailing_spaces",
        count_unit=ScanCountUnit.SOURCE_LINE,
        source_views=(ScanTextView.ORIGINAL,),
        default_severity=ScanRuleSeverity.ADVISORY,
        interpretation="source line ending in space or tab",
        order=5,
    ),
)

BUILTIN_RULE_REGISTRY: Final[ScanRuleSet] = ScanRuleSet(
    rule_set_id=BUILTIN_RULE_SET_ID,
    version=BUILTIN_RULE_SET_VERSION,
    rules=BUILTIN_RULES,
)


def iter_builtin_rules() -> Iterator[ScanRuleDefinition]:
    return iter(BUILTIN_RULE_REGISTRY)


def get_builtin_rule(rule_id: object) -> ScanRuleDefinition | None:
    return BUILTIN_RULE_REGISTRY.get(rule_id)


def require_builtin_rule(rule_id: object) -> ScanRuleDefinition:
    return BUILTIN_RULE_REGISTRY.require(rule_id)


def get_builtin_rule_by_count_field(
    count_field: object,
) -> ScanRuleDefinition | None:
    return BUILTIN_RULE_REGISTRY.get_by_count_field(count_field)


def require_builtin_rule_by_count_field(
    count_field: object,
) -> ScanRuleDefinition:
    return BUILTIN_RULE_REGISTRY.require_by_count_field(count_field)


def validate_builtin_registry() -> None:
    if BUILTIN_RULE_REGISTRY.count_fields != _CANONICAL_COUNT_FIELDS:
        raise RuntimeError(
            "built-in rule order must match the canonical ScanCounts field order"
        )
    if len(BUILTIN_RULE_REGISTRY) != 6:
        raise RuntimeError("the canonical built-in scanner nucleus has six rules")


validate_builtin_registry()

__all__ = (
    "BUILTIN_RULE_REGISTRY",
    "BUILTIN_RULE_SET_ID",
    "BUILTIN_RULE_SET_VERSION",
    "BUILTIN_RULES",
    "ScanCountField",
    "ScanCountUnit",
    "ScanRuleDefinition",
    "ScanRuleDomain",
    "ScanRuleId",
    "ScanRuleSet",
    "ScanRuleSeverity",
    "ScanTextView",
    "get_builtin_rule",
    "get_builtin_rule_by_count_field",
    "iter_builtin_rules",
    "require_builtin_rule",
    "require_builtin_rule_by_count_field",
    "validate_builtin_registry",
    "validate_scan_rule_id",
)
