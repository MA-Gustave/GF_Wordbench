from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import PurePosixPath
from typing import Final

REDACTION_MARKER_TEMPLATE: Final = '<REDACTED reason="{reason}">' 
DEFAULT_REDACTION_POLICY_ID: Final = "gf-wordbench.log-redaction-v1"
DEFAULT_MAX_INPUT_CHARS: Final = 64 * 1024 * 1024

_IDENTIFIER_RE: Final = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")
_REASON_RE: Final = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")
_MARKER_RE: Final = re.compile(
    r'<REDACTED reason="(?P<reason>[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*)">'
)
_PRIVATE_KEY_BLOCK_RE: Final = re.compile(
    r"-----BEGIN (?P<label>[A-Z0-9][A-Z0-9 -]*PRIVATE KEY)-----"
    r".*?"
    r"-----END (?P=label)-----",
    re.DOTALL,
)
_DEFAULT_PROTECTED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth_cookie",
        "auth_token",
        "authorization",
        "client_secret",
        "cookie",
        "credentials",
        "id_token",
        "passphrase",
        "passwd",
        "password",
        "private_key",
        "proxy_authorization",
        "refresh_token",
        "secret",
        "secret_key",
        "session_token",
        "set_cookie",
        "token",
        "x_api_key",
    }
)


@unique
class RedactionReason(StrEnum):
    PROTECTED_VALUE = "protected_value"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    AUTHENTICATION_COOKIE = "authentication_cookie"
    SECRET_ENVIRONMENT = "secret_environment"
    SENSITIVE_PATH = "sensitive_path"
    CONFIGURED_PATTERN = "configured_pattern"


@unique
class RedactionRuleMode(StrEnum):
    LITERAL = "literal"
    REGEX = "regex"


@dataclass(frozen=True, slots=True)
class ConfiguredRedactionRule:
    rule_id: str
    reason: RedactionReason
    pattern: str
    mode: RedactionRuleMode = RedactionRuleMode.REGEX
    ignore_case: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", _identifier(self.rule_id, "rule_id"))
        if not isinstance(self.reason, RedactionReason):
            raise TypeError("reason must be RedactionReason")
        if not isinstance(self.mode, RedactionRuleMode):
            raise TypeError("mode must be RedactionRuleMode")
        pattern = _text(self.pattern, "pattern", empty=False)
        if len(pattern) > 512:
            raise ValueError("pattern exceeds 512 characters")
        if type(self.ignore_case) is not bool:
            raise TypeError("ignore_case must be a boolean")
        if self.mode is RedactionRuleMode.REGEX:
            _compile_regex(pattern, self.ignore_case)
        object.__setattr__(self, "pattern", pattern)


@dataclass(frozen=True, slots=True)
class LogRedactionPolicy:
    policy_id: str = DEFAULT_REDACTION_POLICY_ID
    protected_values: tuple[str, ...] = ()
    protected_keys: frozenset[str] = field(
        default_factory=lambda: _DEFAULT_PROTECTED_KEYS
    )
    sensitive_path_prefixes: tuple[str, ...] = ()
    configured_rules: tuple[ConfiguredRedactionRule, ...] = ()
    redact_private_key_blocks: bool = True
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", _identifier(self.policy_id, "policy_id"))
        object.__setattr__(
            self,
            "protected_values",
            _unique_texts(self.protected_values, "protected_values", longest_first=True),
        )
        keys = frozenset(_key_identity(key) for key in self.protected_keys)
        if any(_IDENTIFIER_RE.fullmatch(key) is None for key in keys):
            raise ValueError("protected_keys contains an invalid key")
        object.__setattr__(self, "protected_keys", keys)
        object.__setattr__(
            self,
            "sensitive_path_prefixes",
            _unique_texts(
                self.sensitive_path_prefixes,
                "sensitive_path_prefixes",
                longest_first=True,
            ),
        )
        rules = tuple(self.configured_rules)
        if any(not isinstance(rule, ConfiguredRedactionRule) for rule in rules):
            raise TypeError("configured_rules must contain ConfiguredRedactionRule values")
        if len({rule.rule_id for rule in rules}) != len(rules):
            raise ValueError("configured_rules contains duplicate rule IDs")
        object.__setattr__(self, "configured_rules", rules)
        if type(self.redact_private_key_blocks) is not bool:
            raise TypeError("redact_private_key_blocks must be a boolean")
        if type(self.max_input_chars) is not int or self.max_input_chars < 1:
            raise ValueError("max_input_chars must be a positive integer")


@dataclass(frozen=True, slots=True)
class RedactionEffect:
    rule_id: str
    reason: RedactionReason
    replacements: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", _identifier(self.rule_id, "rule_id"))
        if not isinstance(self.reason, RedactionReason):
            raise TypeError("reason must be RedactionReason")
        if type(self.replacements) is not int or self.replacements < 1:
            raise ValueError("replacements must be a positive integer")


@dataclass(frozen=True, slots=True)
class LogRedactionRecord:
    artifact_path: str
    policy_id: str
    affected_fields_or_patterns: tuple[str, ...]
    local_unredacted_evidence_exists: bool
    replacement_count: int
    effects: tuple[RedactionEffect, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_path", normalize_artifact_path(self.artifact_path))
        object.__setattr__(self, "policy_id", _identifier(self.policy_id, "policy_id"))
        labels = _unique_texts(
            self.affected_fields_or_patterns,
            "affected_fields_or_patterns",
        )
        effects = tuple(self.effects)
        if any(not isinstance(effect, RedactionEffect) for effect in effects):
            raise TypeError("effects must contain RedactionEffect values")
        if len({effect.rule_id for effect in effects}) != len(effects):
            raise ValueError("effects contains duplicate rule IDs")
        if type(self.local_unredacted_evidence_exists) is not bool:
            raise TypeError("local_unredacted_evidence_exists must be a boolean")
        expected = sum(effect.replacements for effect in effects)
        if type(self.replacement_count) is not int or self.replacement_count != expected:
            raise ValueError("replacement_count must equal the sum of effect counts")
        if expected < 1:
            raise ValueError("a redaction record must contain at least one replacement")
        object.__setattr__(self, "affected_fields_or_patterns", labels)
        object.__setattr__(self, "effects", effects)


@dataclass(frozen=True, slots=True)
class LogRedactionResult:
    text: str
    record: LogRedactionRecord | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _text(self.text, "text", empty=True))
        if self.record is not None and not isinstance(self.record, LogRedactionRecord):
            raise TypeError("record must be LogRedactionRecord or None")

    @property
    def changed(self) -> bool:
        return self.record is not None

    @property
    def replacement_count(self) -> int:
        return 0 if self.record is None else self.record.replacement_count


def make_redaction_marker(reason: RedactionReason | str) -> str:
    value = reason.value if isinstance(reason, RedactionReason) else reason
    value = _text(value, "reason", empty=False)
    if len(value) > 64 or _REASON_RE.fullmatch(value) is None:
        raise ValueError(f"invalid redaction reason: {value!r}")
    return REDACTION_MARKER_TEMPLATE.format(reason=value)


def parse_redaction_markers(text: str) -> tuple[str, ...]:
    value = _text(text, "text", empty=True)
    return tuple(match.group("reason") for match in _MARKER_RE.finditer(value))


def contains_redaction_marker(text: str) -> bool:
    return _MARKER_RE.search(_text(text, "text", empty=True)) is not None


def normalize_artifact_path(path: str | PurePosixPath) -> str:
    if isinstance(path, str):
        candidate = PurePosixPath(_text(path, "artifact_path", empty=False).replace("\\", "/"))
    elif isinstance(path, PurePosixPath):
        candidate = path
    else:
        raise TypeError("artifact_path must be a string or PurePosixPath")
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise ValueError("artifact_path must be a normalized contained relative path")
    rendered = candidate.as_posix()
    if rendered == ".":
        raise ValueError("artifact_path must identify a file")
    return rendered


def redact_log_text(
    text: str,
    *,
    artifact_path: str | PurePosixPath,
    policy: LogRedactionPolicy | None = None,
    local_unredacted_evidence_exists: bool,
) -> LogRedactionResult:
    rendered = _text(text, "text", empty=True)
    effective = policy or LogRedactionPolicy()
    if not isinstance(effective, LogRedactionPolicy):
        raise TypeError("policy must be LogRedactionPolicy or None")
    if type(local_unredacted_evidence_exists) is not bool:
        raise TypeError("local_unredacted_evidence_exists must be a boolean")
    if len(rendered) > effective.max_input_chars:
        raise ValueError("text exceeds the redaction policy input limit")

    effects: list[RedactionEffect] = []
    labels: list[str] = []

    if effective.redact_private_key_blocks:
        rendered, count = _PRIVATE_KEY_BLOCK_RE.subn(
            make_redaction_marker(RedactionReason.PRIVATE_KEY),
            rendered,
        )
        _effect(effects, labels, "private-key-block", RedactionReason.PRIVATE_KEY, count, "pattern:private-key-block")

    for index, secret in enumerate(effective.protected_values, 1):
        count = rendered.count(secret)
        if count:
            rendered = rendered.replace(secret, make_redaction_marker(RedactionReason.PROTECTED_VALUE))
        _effect(effects, labels, f"protected-value-{index}", RedactionReason.PROTECTED_VALUE, count, f"pattern:protected-value-{index}")

    for key in sorted(effective.protected_keys):
        reason = _key_reason(key)
        rendered, count = _redact_keyed(rendered, key, make_redaction_marker(reason))
        _effect(effects, labels, f"key-{key.replace('_', '-')}", reason, count, f"field:{key}")

    for index, prefix in enumerate(effective.sensitive_path_prefixes, 1):
        rendered, count = _redact_path(rendered, prefix)
        _effect(effects, labels, f"sensitive-path-{index}", RedactionReason.SENSITIVE_PATH, count, f"pattern:sensitive-path-{index}")

    for rule in effective.configured_rules:
        marker = make_redaction_marker(rule.reason)
        if rule.mode is RedactionRuleMode.LITERAL:
            pattern = re.compile(re.escape(rule.pattern), re.IGNORECASE if rule.ignore_case else 0)
        else:
            pattern = _compile_regex(rule.pattern, rule.ignore_case)
        rendered, count = pattern.subn(lambda _: marker, rendered)
        _effect(effects, labels, rule.rule_id, rule.reason, count, f"pattern:{rule.rule_id}")

    if not effects:
        return LogRedactionResult(rendered, None)

    record = LogRedactionRecord(
        artifact_path=normalize_artifact_path(artifact_path),
        policy_id=effective.policy_id,
        affected_fields_or_patterns=tuple(labels),
        local_unredacted_evidence_exists=local_unredacted_evidence_exists,
        replacement_count=sum(effect.replacements for effect in effects),
        effects=tuple(effects),
    )
    return LogRedactionResult(rendered, record)


def redact_log_lines(
    lines: Iterable[str],
    *,
    artifact_path: str | PurePosixPath,
    policy: LogRedactionPolicy | None = None,
    local_unredacted_evidence_exists: bool,
    newline: str = "\n",
) -> LogRedactionResult:
    if isinstance(lines, (str, bytes)):
        raise TypeError("lines must be an iterable of strings")
    if newline not in ("\n", "\r\n"):
        raise ValueError("newline must be '\\n' or '\\r\\n'")
    text = newline.join(_text(line, "line", empty=True).rstrip("\r\n") for line in lines)
    return redact_log_text(
        text,
        artifact_path=artifact_path,
        policy=policy,
        local_unredacted_evidence_exists=local_unredacted_evidence_exists,
    )


def merge_redaction_records(
    records: Iterable[LogRedactionRecord],
    *,
    artifact_path: str | PurePosixPath,
    policy_id: str = DEFAULT_REDACTION_POLICY_ID,
    local_unredacted_evidence_exists: bool,
) -> LogRedactionRecord | None:
    if isinstance(records, (str, bytes)):
        raise TypeError("records must be an iterable of LogRedactionRecord")
    prepared = tuple(records)
    if not prepared:
        return None
    if any(not isinstance(record, LogRedactionRecord) for record in prepared):
        raise TypeError("records must contain LogRedactionRecord values")
    counts: dict[tuple[str, RedactionReason], int] = {}
    labels: list[str] = []
    for record in prepared:
        labels.extend(record.affected_fields_or_patterns)
        for effect in record.effects:
            key = (effect.rule_id, effect.reason)
            counts[key] = counts.get(key, 0) + effect.replacements
    effects = tuple(
        RedactionEffect(rule_id, reason, count)
        for (rule_id, reason), count in sorted(counts.items(), key=lambda item: (item[0][0], item[0][1].value))
    )
    return LogRedactionRecord(
        artifact_path=artifact_path,
        policy_id=policy_id,
        affected_fields_or_patterns=tuple(labels),
        local_unredacted_evidence_exists=local_unredacted_evidence_exists,
        replacement_count=sum(effect.replacements for effect in effects),
        effects=effects,
    )


def _redact_keyed(text: str, key: str, marker: str) -> tuple[str, int]:
    escaped = re.escape(key).replace(r"\_", "[-_]")
    patterns = (
        re.compile(
            rf"(?i)(?P<prefix>(?<![A-Za-z0-9_])(?:[\"']?{escaped}[\"']?)\s*(?:=|:)\s*)"
            r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;\]\}]+)"
        ),
        re.compile(
            rf"(?i)(?P<prefix>(?<![A-Za-z0-9_-])--?{escaped}\s+)"
            r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|\S+)"
        ),
    )
    total = 0
    for pattern in patterns:
        text, count = pattern.subn(lambda match: f"{match.group('prefix')}{marker}", text)
        total += count
    return text, total


def _redact_path(text: str, prefix: str) -> tuple[str, int]:
    marker = make_redaction_marker(RedactionReason.SENSITIVE_PATH)
    variants = {prefix, prefix.replace("\\", "/"), prefix.replace("/", "\\")}
    total = 0
    for variant in sorted(filter(None, variants), key=lambda item: (-len(item), item)):
        count = text.count(variant)
        if count:
            text = text.replace(variant, marker)
            total += count
    return text, total


def _compile_regex(pattern: str, ignore_case: bool) -> re.Pattern[str]:
    if "(?" in pattern or re.search(r"\\[1-9]", pattern):
        raise ValueError("regex extensions, lookarounds and backreferences are unsupported")
    if re.search(r"(?:\*|\+|\?|\{[^}]+\})\s*(?:\*|\+|\?|\{)", pattern):
        raise ValueError("nested or repeated quantifiers are unsupported")
    try:
        return re.compile(pattern, re.MULTILINE | (re.IGNORECASE if ignore_case else 0))
    except re.error as exc:
        raise ValueError(f"invalid redaction regex: {exc}") from exc


def _effect(
    effects: list[RedactionEffect],
    labels: list[str],
    rule_id: str,
    reason: RedactionReason,
    count: int,
    label: str,
) -> None:
    if count:
        effects.append(RedactionEffect(rule_id, reason, count))
        labels.append(label)


def _key_reason(key: str) -> RedactionReason:
    if "password" in key or key in {"passwd", "passphrase"}:
        return RedactionReason.PASSWORD
    if "cookie" in key:
        return RedactionReason.AUTHENTICATION_COOKIE
    if "private_key" in key:
        return RedactionReason.PRIVATE_KEY
    if "token" in key or "api_key" in key or key == "apikey":
        return RedactionReason.TOKEN
    return RedactionReason.PROTECTED_VALUE


def _key_identity(value: object) -> str:
    return _text(value, "protected key", empty=False).strip().lower().replace("-", "_")


def _unique_texts(
    values: Iterable[str],
    field_name: str,
    *,
    longest_first: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _text(value, f"{field_name} item", empty=False)
        if item not in seen:
            seen.add(item)
            output.append(item)
    if longest_first:
        output.sort(key=lambda item: (-len(item), item))
    return tuple(output)


def _identifier(value: object, field_name: str) -> str:
    item = _text(value, field_name, empty=False)
    if len(item) > 128 or _IDENTIFIER_RE.fullmatch(item) is None:
        raise ValueError(f"invalid {field_name}: {item!r}")
    return item


def _text(value: object, field_name: str, *, empty: bool) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


__all__ = (
    "ConfiguredRedactionRule",
    "DEFAULT_MAX_INPUT_CHARS",
    "DEFAULT_REDACTION_POLICY_ID",
    "LogRedactionPolicy",
    "LogRedactionRecord",
    "LogRedactionResult",
    "REDACTION_MARKER_TEMPLATE",
    "RedactionEffect",
    "RedactionReason",
    "RedactionRuleMode",
    "contains_redaction_marker",
    "make_redaction_marker",
    "merge_redaction_records",
    "normalize_artifact_path",
    "parse_redaction_markers",
    "redact_log_lines",
    "redact_log_text",
)
