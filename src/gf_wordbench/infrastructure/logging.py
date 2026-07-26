"""Runtime logging primitives for GF Wordbench.

This module configures application diagnostics only. Stage-owned raw evidence and
``raw/master.log`` are written by their owning reporting and orchestration services.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import math
from pathlib import Path
import re
import sys
from threading import RLock
from types import TracebackType
from typing import Final, TextIO

LOGGER_NAMESPACE: Final = "gf_wordbench"
DEFAULT_LOG_LEVEL: Final = logging.INFO
REDACTION_MARKER: Final = '<REDACTED reason="protected_value">'

_LEVEL_ALIASES: Final[dict[str, int]] = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL,
}
_LEVEL_LABELS: Final[dict[int, str]] = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "FATAL",
}
_SAFE_UNQUOTED_RE: Final = re.compile(r"^[A-Za-z0-9._/@:+-]+$")
_FIELD_NAME_RE: Final = re.compile(r"^[a-z][a-z0-9_]*$")
_HANDLER_MARKER: Final = "_gf_wordbench_runtime_handler"
_CONFIGURATION_LOCK: Final = RLock()

_STANDARD_RECORD_FIELDS: Final[frozenset[str]] = frozenset(
    set(logging.makeLogRecord({}).__dict__)
    | {
        "asctime",
        "message",
    }
)

_DEFAULT_PROTECTED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "access_token",
        "api_key",
        "auth_token",
        "authorization",
        "cookie",
        "credentials",
        "password",
        "private_key",
        "secret",
        "secret_key",
        "session_token",
        "token",
    }
)


class LoggingConfigurationError(ValueError):
    """Raised when runtime logging cannot be configured safely."""


@dataclass(frozen=True, slots=True)
class RedactionPolicy:
    """Deterministic redaction rules applied to rendered runtime log text."""

    protected_values: tuple[str, ...] = ()
    protected_keys: frozenset[str] = field(
        default_factory=lambda: _DEFAULT_PROTECTED_KEYS
    )
    marker: str = REDACTION_MARKER

    def __post_init__(self) -> None:
        if not self.marker or "\n" in self.marker or "\r" in self.marker:
            raise LoggingConfigurationError(
                "The redaction marker must be a non-empty single-line string."
            )

        normalized_values: list[str] = []
        seen_values: set[str] = set()
        for value in self.protected_values:
            if not isinstance(value, str):
                raise TypeError("Protected log values must be strings.")
            if not value:
                continue
            if value not in seen_values:
                seen_values.add(value)
                normalized_values.append(value)

        normalized_keys: set[str] = set()
        for key in self.protected_keys:
            if not isinstance(key, str):
                raise TypeError("Protected log keys must be strings.")
            normalized = key.strip().lower().replace("-", "_")
            if not _FIELD_NAME_RE.fullmatch(normalized):
                raise LoggingConfigurationError(
                    f"Invalid protected log key {key!r}; expected lower_snake_case."
                )
            normalized_keys.add(normalized)

        object.__setattr__(
            self,
            "protected_values",
            tuple(sorted(normalized_values, key=lambda item: (-len(item), item))),
        )
        object.__setattr__(self, "protected_keys", frozenset(normalized_keys))

    def redact(self, text: str) -> str:
        """Return ``text`` with protected values and keyed secrets replaced."""

        redacted = text
        for value in self.protected_values:
            redacted = redacted.replace(value, self.marker)

        for key in sorted(self.protected_keys, key=lambda item: (-len(item), item)):
            redacted = _redact_keyed_value(redacted, key=key, marker=self.marker)
        return redacted


@dataclass(frozen=True, slots=True)
class RuntimeLoggingConfig:
    """Configuration for the isolated ``gf_wordbench`` logger hierarchy."""

    level: int | str = DEFAULT_LOG_LEVEL
    stream: TextIO | None = None
    file_path: Path | None = None
    file_level: int | str | None = None
    include_context: bool = True
    propagate: bool = False
    redaction: RedactionPolicy = field(default_factory=RedactionPolicy)

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", normalize_log_level(self.level))
        if self.file_level is not None:
            object.__setattr__(
                self,
                "file_level",
                normalize_log_level(self.file_level),
            )
        if self.file_path is not None:
            object.__setattr__(
                self,
                "file_path",
                Path(self.file_path).expanduser().resolve(strict=False),
            )


class RuntimeLogFormatter(logging.Formatter):
    """UTC formatter with deterministic structured fields and redaction."""

    converter = staticmethod(lambda timestamp: datetime.fromtimestamp(timestamp, timezone.utc).timetuple())

    def __init__(
        self,
        *,
        redaction: RedactionPolicy,
        include_context: bool = True,
    ) -> None:
        super().__init__()
        self._redaction = redaction
        self._include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        timestamp = _format_utc_timestamp(record.created)
        level = _LEVEL_LABELS.get(record.levelno, record.levelname.upper())
        message = record.getMessage().replace("\r", "\\r").replace("\n", "\\n")
        rendered = f"{timestamp} {level} {record.name} {message}"

        if self._include_context:
            context = _record_context(record)
            if context:
                fields = " ".join(
                    f"{key}={_render_field_value(value)}"
                    for key, value in sorted(context.items())
                )
                rendered = f"{rendered} [{fields}]"

        if record.exc_info:
            exception_text = self.formatException(record.exc_info)
            rendered = f"{rendered}\n{exception_text}"
        elif record.exc_text:
            rendered = f"{rendered}\n{record.exc_text}"

        if record.stack_info:
            rendered = f"{rendered}\n{self.formatStack(record.stack_info)}"

        return self._redaction.redact(rendered)


class ContextLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Logger adapter that carries validated structured context fields."""

    def __init__(self, logger: logging.Logger, context: Mapping[str, object]) -> None:
        super().__init__(logger, _validate_context(context))

    def process(
        self,
        msg: object,
        kwargs: dict[str, object],
    ) -> tuple[object, dict[str, object]]:
        extra = dict(self.extra)
        supplied = kwargs.get("extra")
        if supplied is not None:
            if not isinstance(supplied, Mapping):
                raise TypeError("Logging 'extra' must be a mapping.")
            extra.update(_validate_context(supplied))
        kwargs["extra"] = extra
        return msg, kwargs


class _OwnedHandler(logging.Handler):
    """Marker base used only for precise handler replacement."""

    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        setattr(self, _HANDLER_MARKER, True)


class _OwnedStreamHandler(logging.StreamHandler[TextIO], _OwnedHandler):
    def __init__(self, stream: TextIO) -> None:
        logging.StreamHandler.__init__(self, stream)
        setattr(self, _HANDLER_MARKER, True)


class _OwnedFileHandler(logging.FileHandler, _OwnedHandler):
    def __init__(self, path: Path) -> None:
        logging.FileHandler.__init__(
            self,
            filename=path,
            mode="a",
            encoding="utf-8",
            delay=False,
        )
        setattr(self, _HANDLER_MARKER, True)


def normalize_log_level(level: int | str) -> int:
    """Normalize a canonical or stdlib logging level."""

    if isinstance(level, bool):
        raise TypeError("A log level must not be a boolean.")
    if isinstance(level, int):
        if level < logging.NOTSET:
            raise LoggingConfigurationError("A log level cannot be negative.")
        return level
    if not isinstance(level, str):
        raise TypeError("A log level must be an integer or string.")

    normalized = level.strip().upper()
    try:
        return _LEVEL_ALIASES[normalized]
    except KeyError as exc:
        allowed = ", ".join(sorted(_LEVEL_ALIASES))
        raise LoggingConfigurationError(
            f"Unknown log level {level!r}; expected one of: {allowed}."
        ) from exc


def configure_runtime_logging(
    config: RuntimeLoggingConfig | None = None,
) -> logging.Logger:
    """Configure and return the isolated GF Wordbench logger hierarchy.

    Repeated calls replace only handlers previously installed by this function,
    which prevents duplicates without disturbing handlers owned by an embedding
    application.
    """

    effective = config or RuntimeLoggingConfig()
    logger = logging.getLogger(LOGGER_NAMESPACE)
    formatter = RuntimeLogFormatter(
        redaction=effective.redaction,
        include_context=effective.include_context,
    )

    with _CONFIGURATION_LOCK:
        _remove_owned_handlers(logger)

        stream_handler = _OwnedStreamHandler(effective.stream or sys.stderr)
        stream_handler.set_name(f"{LOGGER_NAMESPACE}.runtime.console")
        stream_handler.setLevel(effective.level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if effective.file_path is not None:
            effective.file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = _OwnedFileHandler(effective.file_path)
            file_handler.set_name(f"{LOGGER_NAMESPACE}.runtime.file")
            file_handler.setLevel(
                effective.file_level
                if effective.file_level is not None
                else effective.level
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.setLevel(_minimum_handler_level(logger.handlers, effective.level))
        logger.propagate = effective.propagate
        logger.disabled = False

    return logger


def get_logger(component: str | None = None) -> logging.Logger:
    """Return a logger inside the canonical GF Wordbench namespace."""

    if component is None or not component.strip():
        return logging.getLogger(LOGGER_NAMESPACE)

    normalized = component.strip().strip(".")
    if normalized == LOGGER_NAMESPACE or normalized.startswith(f"{LOGGER_NAMESPACE}."):
        name = normalized
    else:
        name = f"{LOGGER_NAMESPACE}.{normalized}"
    return logging.getLogger(name)


def bind_logger(
    logger: logging.Logger | str,
    **context: object,
) -> ContextLoggerAdapter:
    """Bind deterministic structured context to a runtime logger."""

    resolved = get_logger(logger) if isinstance(logger, str) else logger
    return ContextLoggerAdapter(resolved, context)


def reset_runtime_logging() -> None:
    """Remove and close handlers installed by :func:`configure_runtime_logging`."""

    logger = logging.getLogger(LOGGER_NAMESPACE)
    with _CONFIGURATION_LOCK:
        _remove_owned_handlers(logger)
        logger.setLevel(logging.NOTSET)
        logger.propagate = False


def redact_text(
    text: str,
    *,
    protected_values: Iterable[str] = (),
    protected_keys: Iterable[str] = _DEFAULT_PROTECTED_KEYS,
) -> str:
    """Redact protected content from text without configuring logging."""

    if not isinstance(text, str):
        raise TypeError("Text to redact must be a string.")
    policy = RedactionPolicy(
        protected_values=tuple(protected_values),
        protected_keys=frozenset(protected_keys),
    )
    return policy.redact(text)


def _remove_owned_handlers(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.flush()
            handler.close()


def _minimum_handler_level(
    handlers: Iterable[logging.Handler],
    fallback: int,
) -> int:
    levels = [handler.level for handler in handlers if handler.level != logging.NOTSET]
    return min(levels, default=fallback)


def _validate_context(context: Mapping[str, object]) -> dict[str, object]:
    validated: dict[str, object] = {}
    for key, value in context.items():
        if not isinstance(key, str) or not _FIELD_NAME_RE.fullmatch(key):
            raise LoggingConfigurationError(
                f"Invalid log context key {key!r}; expected lower_snake_case."
            )
        if key in _STANDARD_RECORD_FIELDS:
            raise LoggingConfigurationError(
                f"Log context key {key!r} conflicts with a standard LogRecord field."
            )
        validated[key] = value
    return validated


def _record_context(record: logging.LogRecord) -> dict[str, object]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in _STANDARD_RECORD_FIELDS and not key.startswith("_")
    }


def _render_field_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value) if math.isfinite(value) else "null"
    if isinstance(value, Enum):
        return _render_field_value(value.value)
    if isinstance(value, Path):
        value = value.as_posix()
    if isinstance(value, str):
        if value and _SAFE_UNQUOTED_RE.fullmatch(value):
            return value
        return json.dumps(value, ensure_ascii=False)

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    except (TypeError, ValueError):
        return json.dumps(str(value), ensure_ascii=False)


def _format_utc_timestamp(created: float) -> str:
    value = datetime.fromtimestamp(created, timezone.utc)
    milliseconds = value.microsecond // 1_000
    return value.strftime("%Y-%m-%dT%H:%M:%S") + f".{milliseconds:03d}Z"


def _redact_keyed_value(text: str, *, key: str, marker: str) -> str:
    key_pattern = re.escape(key).replace(r"\_", "[-_]")
    pattern = re.compile(
        rf"(?i)(?P<prefix>(?<![A-Za-z0-9_])(?:[\"']?{key_pattern}[\"']?)\s*(?:=|:)\s*)"
        r"(?P<value>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;\]\}]+)"
    )
    return pattern.sub(lambda match: f"{match.group('prefix')}{marker}", text)


__all__ = [
    "ContextLoggerAdapter",
    "DEFAULT_LOG_LEVEL",
    "LOGGER_NAMESPACE",
    "LoggingConfigurationError",
    "REDACTION_MARKER",
    "RedactionPolicy",
    "RuntimeLogFormatter",
    "RuntimeLoggingConfig",
    "bind_logger",
    "configure_runtime_logging",
    "get_logger",
    "normalize_log_level",
    "redact_text",
    "reset_runtime_logging",
]
