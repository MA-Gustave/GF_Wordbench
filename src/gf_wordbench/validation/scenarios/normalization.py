"""Versioned scenario-output normalization for extracted marked sections."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.ids import (
    NormalizationProfileId,
    SectionId,
    validate_normalization_profile_id,
    validate_section_id,
)

_NORMALIZATION_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)
_RULE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^NORM-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}$"
)
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^<[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*>$"
)
_PATH_FIELD_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z][A-Za-z0-9_.-]*$"
)
_MAX_RULES: Final[int] = 128
_MAX_REPLACEMENTS_PER_RULE: Final[int] = 128
_MAX_REMOVABLE_LINES_PER_RULE: Final[int] = 128
_MAX_SECTION_CHARACTERS: Final[int] = 16 * 1024 * 1024
DEFAULT_NORMALIZATION_PROFILE_ID: Final[NormalizationProfileId] = (
    NormalizationProfileId("scenario-default")
)
DEFAULT_NORMALIZATION_PROFILE_VERSION: Final[str] = "1.0.0"


@unique
class NormalizationErrorCode(StrEnum):
    INVALID_PROFILE = "invalid_profile"
    UNKNOWN_PROFILE = "unknown_profile"
    INVALID_RULE = "invalid_rule"
    INVALID_SECTION = "invalid_section"
    LIMIT_EXCEEDED = "limit_exceeded"


class NormalizationError(ValueError):
    def __init__(
        self,
        code: NormalizationErrorCode,
        message: str,
        *,
        profile_id: str | None = None,
        profile_version: str | None = None,
        section_id: str | None = None,
        rule_id: str | None = None,
    ) -> None:
        if not isinstance(code, NormalizationErrorCode):
            raise TypeError("code must be a NormalizationErrorCode")
        _require_text(message, field_name="message")
        self.code = code
        self.profile_id = profile_id
        self.profile_version = profile_version
        self.section_id = section_id
        self.rule_id = rule_id
        super().__init__(message)


@runtime_checkable
class NormalizationRule(Protocol):
    rule_id: str

    def apply(self, text: str) -> str:
        ...


@dataclass(frozen=True, slots=True)
class NormalizeLineEndings:
    rule_id: str = "NORM-LINE-ENDINGS-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        return text.replace("\r\n", "\n").replace("\r", "\n")


@dataclass(frozen=True, slots=True)
class RemoveFinalTrailingBlankLine:
    rule_id: str = "NORM-FINAL-BLANK-LINE-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        match = re.search(r"\n[ \t]*\n\Z", text)
        if match is None:
            return text
        return text[: match.start()] + "\n"


@dataclass(frozen=True, slots=True)
class PathTokenReplacement:
    source: str
    token: str

    def __post_init__(self) -> None:
        _require_text(self.source, field_name="source")
        if "\n" in self.source or "\r" in self.source:
            raise ValueError("source must not contain a line ending")
        if not isinstance(self.token, str):
            raise TypeError("token must be a string")
        if _TOKEN_RE.fullmatch(self.token) is None:
            raise ValueError(
                "token must match <UPPERCASE_TOKEN>"
            )


@dataclass(frozen=True, slots=True)
class ReplaceApprovedPaths:
    replacements: tuple[PathTokenReplacement, ...]
    rule_id: str = "NORM-RUN-PATHS-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)
        normalized = tuple(self.replacements)
        if not normalized:
            raise ValueError("replacements must not be empty")
        if len(normalized) > _MAX_REPLACEMENTS_PER_RULE:
            raise ValueError(
                "replacements exceed the supported rule limit"
            )
        if not all(
            isinstance(item, PathTokenReplacement)
            for item in normalized
        ):
            raise TypeError(
                "replacements must contain PathTokenReplacement values"
            )
        sources = tuple(item.source for item in normalized)
        if len(sources) != len(set(sources)):
            raise ValueError(
                "replacement source values must be unique"
            )
        object.__setattr__(self, "replacements", normalized)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        normalized = text
        for replacement in self.replacements:
            normalized = normalized.replace(
                replacement.source,
                replacement.token,
            )
        return normalized


@dataclass(frozen=True, slots=True)
class NormalizeDesignatedPathFields:
    field_names: tuple[str, ...]
    separators: tuple[str, ...] = (":", "=")
    rule_id: str = "NORM-PATH-SEPARATORS-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)
        fields = tuple(self.field_names)
        separators = tuple(self.separators)
        if not fields:
            raise ValueError("field_names must not be empty")
        if len(fields) != len(set(fields)):
            raise ValueError("field_names must be unique")
        for field_name in fields:
            if (
                not isinstance(field_name, str)
                or _PATH_FIELD_RE.fullmatch(field_name) is None
            ):
                raise ValueError(
                    "field_names must contain stable field identifiers"
                )
        if not separators:
            raise ValueError("separators must not be empty")
        if len(separators) != len(set(separators)):
            raise ValueError("separators must be unique")
        for separator in separators:
            if (
                not isinstance(separator, str)
                or len(separator) != 1
                or separator not in {":", "="}
            ):
                raise ValueError(
                    "separators may contain only ':' and '='"
                )
        object.__setattr__(self, "field_names", fields)
        object.__setattr__(self, "separators", separators)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        output: list[str] = []
        for line in text.splitlines(keepends=True):
            body, ending = _split_line_ending(line)
            output.append(
                self._normalize_line(body) + ending
            )
        if text and not text.endswith(("\n", "\r")) and not output:
            return self._normalize_line(text)
        return "".join(output)

    def _normalize_line(self, line: str) -> str:
        leading_length = len(line) - len(line.lstrip(" \t"))
        leading = line[:leading_length]
        candidate = line[leading_length:]
        for field_name in self.field_names:
            if not candidate.startswith(field_name):
                continue
            remainder = candidate[len(field_name):]
            spacing_length = len(remainder) - len(
                remainder.lstrip(" \t")
            )
            spacing = remainder[:spacing_length]
            remainder = remainder[spacing_length:]
            if not remainder or remainder[0] not in self.separators:
                continue
            separator = remainder[0]
            value = remainder[1:]
            value_spacing_length = len(value) - len(
                value.lstrip(" \t")
            )
            value_spacing = value[:value_spacing_length]
            path_value = value[value_spacing_length:]
            return (
                leading
                + field_name
                + spacing
                + separator
                + value_spacing
                + path_value.replace("\\", "/")
            )
        return line


@dataclass(frozen=True, slots=True)
class RemoveApprovedExactLines:
    line_values: tuple[str, ...]
    rule_id: str = "NORM-GF-PRESENTATION-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)
        values = tuple(self.line_values)
        if not values:
            raise ValueError("line_values must not be empty")
        if len(values) > _MAX_REMOVABLE_LINES_PER_RULE:
            raise ValueError(
                "line_values exceed the supported rule limit"
            )
        if len(values) != len(set(values)):
            raise ValueError("line_values must be unique")
        for value in values:
            _require_text(value, field_name="line value")
            if "\n" in value or "\r" in value:
                raise ValueError(
                    "line values must not contain line endings"
                )
        object.__setattr__(self, "line_values", values)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        removable = frozenset(self.line_values)
        retained: list[str] = []
        for line in text.splitlines(keepends=True):
            body, ending = _split_line_ending(line)
            if body in removable:
                continue
            retained.append(body + ending)
        return "".join(retained)


@dataclass(frozen=True, slots=True)
class RemoveApprovedAnsiSequences:
    sequences: tuple[str, ...]
    rule_id: str = "NORM-ANSI-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)
        values = tuple(self.sequences)
        if not values:
            raise ValueError("sequences must not be empty")
        if len(values) > _MAX_REPLACEMENTS_PER_RULE:
            raise ValueError(
                "sequences exceed the supported rule limit"
            )
        if len(values) != len(set(values)):
            raise ValueError("sequences must be unique")
        for value in values:
            _require_text(value, field_name="ANSI sequence")
            if not value.startswith("\x1b"):
                raise ValueError(
                    "approved ANSI sequences must begin with ESC"
                )
        object.__setattr__(self, "sequences", values)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        normalized = text
        for sequence in self.sequences:
            normalized = normalized.replace(sequence, "")
        return normalized


@dataclass(frozen=True, slots=True)
class RemoveTrailingSpaces:
    rule_id: str = "NORM-TRAILING-SPACES-001"

    def __post_init__(self) -> None:
        _validate_rule_id(self.rule_id)

    def apply(self, text: str) -> str:
        _require_normalizable_text(text)
        output: list[str] = []
        for line in text.splitlines(keepends=True):
            body, ending = _split_line_ending(line)
            output.append(body.rstrip(" \t") + ending)
        return "".join(output)


NormalizationRuleValue: TypeAlias = (
    NormalizeLineEndings
    | RemoveFinalTrailingBlankLine
    | ReplaceApprovedPaths
    | NormalizeDesignatedPathFields
    | RemoveApprovedExactLines
    | RemoveApprovedAnsiSequences
    | RemoveTrailingSpaces
)


@dataclass(frozen=True, slots=True)
class NormalizationProfile:
    profile_id: NormalizationProfileId
    version: str
    rules: tuple[NormalizationRuleValue, ...]

    def __post_init__(self) -> None:
        profile_id = validate_normalization_profile_id(
            self.profile_id,
            field="normalization profile ID",
        )
        version = validate_normalization_version(self.version)
        rules = tuple(self.rules)
        if len(rules) > _MAX_RULES:
            raise NormalizationError(
                NormalizationErrorCode.INVALID_PROFILE,
                "Normalization profile contains too many rules.",
                profile_id=str(profile_id),
                profile_version=version,
            )
        for index, rule in enumerate(rules):
            if not isinstance(rule, NormalizationRule):
                raise TypeError(
                    f"rules[{index}] must implement NormalizationRule"
                )
        rule_ids = tuple(rule.rule_id for rule in rules)
        if len(rule_ids) != len(set(rule_ids)):
            raise NormalizationError(
                NormalizationErrorCode.INVALID_PROFILE,
                "Normalization profile rule IDs must be unique.",
                profile_id=str(profile_id),
                profile_version=version,
            )
        object.__setattr__(self, "profile_id", profile_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "rules", rules)

    @property
    def identity(self) -> tuple[str, str]:
        return str(self.profile_id), self.version


@dataclass(frozen=True, slots=True)
class ExtractedScenarioSection:
    section_id: SectionId
    text: str
    source_evidence: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_id",
            validate_section_id(
                self.section_id,
                field="scenario section ID",
            ),
        )
        _require_normalizable_text(self.text)
        _require_text(
            self.source_evidence,
            field_name="source_evidence",
        )


@dataclass(frozen=True, slots=True)
class NormalizedScenarioSection:
    section_id: SectionId
    normalized_text: str
    source_evidence: str
    profile_id: NormalizationProfileId
    profile_version: str
    source_sha256: str
    normalized_sha256: str
    source_size_bytes: int
    normalized_size_bytes: int
    applied_rule_ids: tuple[str, ...]
    changed: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_id",
            validate_section_id(
                self.section_id,
                field="scenario section ID",
            ),
        )
        _require_normalizable_text(self.normalized_text)
        _require_text(
            self.source_evidence,
            field_name="source_evidence",
        )
        object.__setattr__(
            self,
            "profile_id",
            validate_normalization_profile_id(
                self.profile_id,
                field="normalization profile ID",
            ),
        )
        object.__setattr__(
            self,
            "profile_version",
            validate_normalization_version(
                self.profile_version
            ),
        )
        _validate_sha256(
            self.source_sha256,
            field_name="source_sha256",
        )
        _validate_sha256(
            self.normalized_sha256,
            field_name="normalized_sha256",
        )
        _validate_nonnegative_integer(
            self.source_size_bytes,
            field_name="source_size_bytes",
        )
        _validate_nonnegative_integer(
            self.normalized_size_bytes,
            field_name="normalized_size_bytes",
        )
        rule_ids = tuple(self.applied_rule_ids)
        for rule_id in rule_ids:
            _validate_rule_id(rule_id)
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError(
                "applied_rule_ids must not contain duplicates"
            )
        if not isinstance(self.changed, bool):
            raise TypeError("changed must be a bool")
        object.__setattr__(
            self,
            "applied_rule_ids",
            rule_ids,
        )


class NormalizationProfileRegistry:
    def __init__(
        self,
        profiles: Iterable[NormalizationProfile] = (),
    ) -> None:
        indexed: dict[
            tuple[str, str],
            NormalizationProfile,
        ] = {}
        for position, profile in enumerate(profiles):
            if not isinstance(profile, NormalizationProfile):
                raise TypeError(
                    f"profiles[{position}] must be a "
                    "NormalizationProfile"
                )
            if profile.identity in indexed:
                raise ValueError(
                    "duplicate normalization profile identity "
                    f"{profile.identity!r}"
                )
            indexed[profile.identity] = profile
        self._profiles: Mapping[
            tuple[str, str],
            NormalizationProfile,
        ] = MappingProxyType(indexed)

    def get(
        self,
        profile_id: str | NormalizationProfileId,
        version: str,
    ) -> NormalizationProfile | None:
        normalized_id = validate_normalization_profile_id(
            profile_id,
            field="normalization profile ID",
        )
        normalized_version = validate_normalization_version(
            version
        )
        return self._profiles.get(
            (str(normalized_id), normalized_version)
        )

    def require(
        self,
        profile_id: str | NormalizationProfileId,
        version: str,
    ) -> NormalizationProfile:
        profile = self.get(profile_id, version)
        if profile is None:
            raise NormalizationError(
                NormalizationErrorCode.UNKNOWN_PROFILE,
                (
                    "Unknown normalization profile or unsupported "
                    "normalization version."
                ),
                profile_id=str(profile_id),
                profile_version=version,
            )
        return profile

    def identities(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._profiles))

    def profiles(self) -> tuple[NormalizationProfile, ...]:
        return tuple(
            self._profiles[identity]
            for identity in self.identities()
        )

    def with_profiles(
        self,
        profiles: Iterable[NormalizationProfile],
    ) -> NormalizationProfileRegistry:
        return NormalizationProfileRegistry(
            (*self.profiles(), *tuple(profiles))
        )


DEFAULT_NORMALIZATION_PROFILE: Final[NormalizationProfile] = (
    NormalizationProfile(
        profile_id=DEFAULT_NORMALIZATION_PROFILE_ID,
        version=DEFAULT_NORMALIZATION_PROFILE_VERSION,
        rules=(NormalizeLineEndings(),),
    )
)

DEFAULT_NORMALIZATION_REGISTRY: Final[
    NormalizationProfileRegistry
] = NormalizationProfileRegistry(
    (DEFAULT_NORMALIZATION_PROFILE,)
)


def validate_normalization_version(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "normalization version must be a string"
        )
    if _NORMALIZATION_VERSION_RE.fullmatch(value) is None:
        raise ValueError(
            "normalization version must use MAJOR.MINOR.PATCH"
        )
    return value


def normalize_scenario_section(
    section: ExtractedScenarioSection,
    *,
    profile: NormalizationProfile,
) -> NormalizedScenarioSection:
    if not isinstance(section, ExtractedScenarioSection):
        raise TypeError(
            "section must be an ExtractedScenarioSection"
        )
    if not isinstance(profile, NormalizationProfile):
        raise TypeError(
            "profile must be a NormalizationProfile"
        )

    source_bytes = section.text.encode("utf-8")
    normalized = section.text

    for rule in profile.rules:
        try:
            candidate = rule.apply(normalized)
        except NormalizationError:
            raise
        except Exception as exc:
            raise NormalizationError(
                NormalizationErrorCode.INVALID_RULE,
                (
                    f"Normalization rule {rule.rule_id!r} "
                    "failed."
                ),
                profile_id=str(profile.profile_id),
                profile_version=profile.version,
                section_id=str(section.section_id),
                rule_id=rule.rule_id,
            ) from exc
        if not isinstance(candidate, str):
            raise NormalizationError(
                NormalizationErrorCode.INVALID_RULE,
                (
                    f"Normalization rule {rule.rule_id!r} "
                    "did not return text."
                ),
                profile_id=str(profile.profile_id),
                profile_version=profile.version,
                section_id=str(section.section_id),
                rule_id=rule.rule_id,
            )
        _require_normalizable_text(candidate)
        normalized = candidate

    normalized_bytes = normalized.encode("utf-8")
    return NormalizedScenarioSection(
        section_id=section.section_id,
        normalized_text=normalized,
        source_evidence=section.source_evidence,
        profile_id=profile.profile_id,
        profile_version=profile.version,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        normalized_sha256=hashlib.sha256(
            normalized_bytes
        ).hexdigest(),
        source_size_bytes=len(source_bytes),
        normalized_size_bytes=len(normalized_bytes),
        applied_rule_ids=tuple(
            rule.rule_id for rule in profile.rules
        ),
        changed=normalized != section.text,
    )


def normalize_scenario_section_by_identity(
    section: ExtractedScenarioSection,
    *,
    profile_id: str | NormalizationProfileId,
    profile_version: str,
    registry: NormalizationProfileRegistry = (
        DEFAULT_NORMALIZATION_REGISTRY
    ),
) -> NormalizedScenarioSection:
    if not isinstance(
        registry,
        NormalizationProfileRegistry,
    ):
        raise TypeError(
            "registry must be a NormalizationProfileRegistry"
        )
    profile = registry.require(profile_id, profile_version)
    return normalize_scenario_section(
        section,
        profile=profile,
    )


def normalize_scenario_sections(
    sections: Sequence[ExtractedScenarioSection],
    *,
    profile: NormalizationProfile,
) -> tuple[NormalizedScenarioSection, ...]:
    if isinstance(sections, (str, bytes)):
        raise TypeError(
            "sections must be a sequence of extracted sections"
        )
    if not isinstance(profile, NormalizationProfile):
        raise TypeError(
            "profile must be a NormalizationProfile"
        )

    normalized_sections: list[NormalizedScenarioSection] = []
    seen_ids: set[str] = set()

    for position, section in enumerate(sections):
        if not isinstance(section, ExtractedScenarioSection):
            raise TypeError(
                f"sections[{position}] must be an "
                "ExtractedScenarioSection"
            )
        identity = str(section.section_id)
        if identity in seen_ids:
            raise NormalizationError(
                NormalizationErrorCode.INVALID_SECTION,
                (
                    "Extracted scenario section IDs must be "
                    "unique."
                ),
                profile_id=str(profile.profile_id),
                profile_version=profile.version,
                section_id=identity,
            )
        seen_ids.add(identity)
        normalized_sections.append(
            normalize_scenario_section(
                section,
                profile=profile,
            )
        )

    return tuple(normalized_sections)


def _require_normalizable_text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("normalizable content must be a string")
    if len(value) > _MAX_SECTION_CHARACTERS:
        raise NormalizationError(
            NormalizationErrorCode.LIMIT_EXCEEDED,
            "Extracted scenario section exceeds the normalization limit.",
        )
    if "\x00" in value:
        raise NormalizationError(
            NormalizationErrorCode.INVALID_SECTION,
            "Extracted scenario section must not contain NUL.",
        )
    return value


def _validate_rule_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("rule_id must be a string")
    if _RULE_ID_RE.fullmatch(value) is None:
        raise ValueError(
            "rule_id must match NORM-<DOMAIN>-<NNN>"
        )
    return value


def _validate_sha256(
    value: object,
    *,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
    ):
        raise ValueError(
            f"{field_name} must be a lowercase SHA-256 digest"
        )
    return value


def _validate_nonnegative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise ValueError(
            f"{field_name} must be a non-negative integer"
        )
    return value


def _require_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if "\x00" in value:
        raise ValueError(
            f"{field_name} must not contain NUL"
        )
    return value


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


__all__ = (
    "DEFAULT_NORMALIZATION_PROFILE",
    "DEFAULT_NORMALIZATION_PROFILE_ID",
    "DEFAULT_NORMALIZATION_PROFILE_VERSION",
    "DEFAULT_NORMALIZATION_REGISTRY",
    "ExtractedScenarioSection",
    "NormalizationError",
    "NormalizationErrorCode",
    "NormalizationProfile",
    "NormalizationProfileRegistry",
    "NormalizationRule",
    "NormalizationRuleValue",
    "NormalizeDesignatedPathFields",
    "NormalizeLineEndings",
    "NormalizedScenarioSection",
    "PathTokenReplacement",
    "RemoveApprovedAnsiSequences",
    "RemoveApprovedExactLines",
    "RemoveFinalTrailingBlankLine",
    "RemoveTrailingSpaces",
    "ReplaceApprovedPaths",
    "normalize_scenario_section",
    "normalize_scenario_section_by_identity",
    "normalize_scenario_sections",
    "validate_normalization_version",
)
