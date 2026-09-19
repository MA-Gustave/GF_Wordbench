"""Controlled child-process environment construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from types import MappingProxyType
from typing import Final, TypeAlias

EnvironmentMapping: TypeAlias = Mapping[str, str]

CONTROLLED_INHERIT_V1: Final = "controlled-inherit-v1"
REDACTED_VALUE: Final = "<redacted>"

_AMBIENT_GF_VARIABLES: Final[frozenset[str]] = frozenset({"GF_LIB_PATH"})


@dataclass(frozen=True, slots=True)
class PreparedEnvironment:
    """Immutable child environment and its persistable override evidence."""

    policy: str
    values: EnvironmentMapping
    recorded_overrides: EnvironmentMapping

    def __post_init__(self) -> None:
        if self.policy != CONTROLLED_INHERIT_V1:
            raise ValueError(f"unsupported environment policy: {self.policy!r}")
        if not isinstance(self.values, MappingProxyType):
            raise TypeError("values must be an immutable mapping snapshot")
        if not isinstance(self.recorded_overrides, MappingProxyType):
            raise TypeError("recorded_overrides must be an immutable mapping snapshot")


def build_child_environment(
    *,
    policy: str = CONTROLLED_INHERIT_V1,
    parent: EnvironmentMapping | None = None,
    overrides: EnvironmentMapping | None = None,
    sensitive_keys: frozenset[str] = frozenset(),
) -> PreparedEnvironment:
    """Build one child-only environment without mutating ``os.environ``."""

    if policy != CONTROLLED_INHERIT_V1:
        raise ValueError(f"unsupported environment policy: {policy!r}")

    source = os.environ if parent is None else parent
    inherited = _validated_environment(source, field_name="parent")
    explicit = _validated_environment(overrides or {}, field_name="overrides")
    sensitive = _validated_sensitive_keys(sensitive_keys)

    child = dict(inherited)
    _remove_ambient_gf_variables(child)
    _apply_overrides(child, explicit)

    recorded = {
        key: REDACTED_VALUE if _contains_key(sensitive, key) else value
        for key, value in explicit.items()
    }

    return PreparedEnvironment(
        policy=policy,
        values=MappingProxyType(child),
        recorded_overrides=MappingProxyType(recorded),
    )


def _validated_environment(
    environment: EnvironmentMapping,
    *,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(environment, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    validated: dict[str, str] = {}
    seen: set[str] = set()

    for key, value in environment.items():
        _validate_environment_entry(key, value, field_name=field_name)
        identity = _key_identity(key)
        if identity in seen:
            raise ValueError(f"{field_name} contains duplicate environment key {key!r}")
        seen.add(identity)
        validated[key] = value

    return validated


def _validated_sensitive_keys(keys: frozenset[str]) -> frozenset[str]:
    if not isinstance(keys, frozenset):
        raise TypeError("sensitive_keys must be a frozenset")

    identities: set[str] = set()
    for key in keys:
        _validate_environment_key(key, field_name="sensitive_keys")
        identity = _key_identity(key)
        if identity in identities:
            raise ValueError("sensitive_keys contains duplicate environment keys")
        identities.add(identity)

    return frozenset(identities)


def _validate_environment_entry(
    key: object,
    value: object,
    *,
    field_name: str,
) -> None:
    _validate_environment_key(key, field_name=field_name)
    if not isinstance(value, str):
        raise TypeError(f"{field_name}[{key!r}] must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name}[{key!r}] must not contain a NUL character")


def _validate_environment_key(key: object, *, field_name: str) -> None:
    if not isinstance(key, str):
        raise TypeError(f"{field_name} environment keys must be strings")
    if not key:
        raise ValueError(f"{field_name} environment keys must not be empty")
    if "\x00" in key:
        raise ValueError(f"{field_name} environment keys must not contain a NUL character")
    if "=" in key:
        raise ValueError(f"{field_name} environment keys must not contain '='")


def _remove_ambient_gf_variables(environment: dict[str, str]) -> None:
    ambient = {_key_identity(key) for key in _AMBIENT_GF_VARIABLES}
    for key in tuple(environment):
        if _key_identity(key) in ambient:
            del environment[key]


def _apply_overrides(
    environment: dict[str, str],
    overrides: Mapping[str, str],
) -> None:
    for key, value in overrides.items():
        existing = _matching_key(environment, key)
        if existing is not None and existing != key:
            del environment[existing]
        environment[key] = value


def _matching_key(environment: Mapping[str, str], key: str) -> str | None:
    identity = _key_identity(key)
    for candidate in environment:
        if _key_identity(candidate) == identity:
            return candidate
    return None


def _contains_key(identities: frozenset[str], key: str) -> bool:
    return _key_identity(key) in identities


def _key_identity(key: str) -> str:
    return key.upper() if os.name == "nt" else key


__all__ = (
    "CONTROLLED_INHERIT_V1",
    "REDACTED_VALUE",
    "EnvironmentMapping",
    "PreparedEnvironment",
    "build_child_environment",
)
