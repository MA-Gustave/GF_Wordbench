"""Static allowlist registry for executable diagnostic tools."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypeAlias

from .models import DiagnosticToolSpec

ToolId: TypeAlias = str

CATALOG_VERSION: Final[str] = "1.0"

_TOOL_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
)
_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+(?:\.[0-9]+){1,2}$"
)
_MAX_TOOL_COUNT: Final[int] = 1_000
_MAX_TOOL_ID_LENGTH: Final[int] = 128
_MAX_VERSION_LENGTH: Final[int] = 32


class DiagnosticToolRegistryError(ValueError):
    """Base error for invalid diagnostic-tool registry contracts."""


class DuplicateDiagnosticToolError(DiagnosticToolRegistryError):
    """Raised when two entries use the same canonical tool identity."""


class UnknownDiagnosticToolError(LookupError):
    """Raised when execution requests an unregistered diagnostic tool."""


class CatalogVersionMismatchError(DiagnosticToolRegistryError):
    """Raised when an entry belongs to a different catalog contract version."""


@dataclass(frozen=True, slots=True)
class DiagnosticToolRegistrySnapshot:
    """Stable, serializable registry identity without executable details."""

    catalog_version: str
    tool_ids: tuple[ToolId, ...]
    required_tool_ids: tuple[ToolId, ...]
    optional_tool_ids: tuple[ToolId, ...]
    diagnostic_only_tool_ids: tuple[ToolId, ...]
    normative_tool_ids: tuple[ToolId, ...]
    ai_assisted_tool_ids: tuple[ToolId, ...]

    def __post_init__(self) -> None:
        catalog_version = _normalize_catalog_version(self.catalog_version)
        tool_ids = _normalize_tool_id_sequence(self.tool_ids)

        categories = {
            "required_tool_ids": _normalize_tool_id_sequence(
                self.required_tool_ids
            ),
            "optional_tool_ids": _normalize_tool_id_sequence(
                self.optional_tool_ids
            ),
            "diagnostic_only_tool_ids": _normalize_tool_id_sequence(
                self.diagnostic_only_tool_ids
            ),
            "normative_tool_ids": _normalize_tool_id_sequence(
                self.normative_tool_ids
            ),
            "ai_assisted_tool_ids": _normalize_tool_id_sequence(
                self.ai_assisted_tool_ids
            ),
        }

        known = frozenset(tool_ids)
        for field_name, values in categories.items():
            unknown = frozenset(values).difference(known)
            if unknown:
                rendered = ", ".join(sorted(unknown))
                raise ValueError(
                    f"{field_name} contains unknown tool IDs: {rendered}"
                )

        availability_groups = (
            frozenset(categories["required_tool_ids"]),
            frozenset(categories["optional_tool_ids"]),
            frozenset(categories["diagnostic_only_tool_ids"]),
        )
        if any(
            left.intersection(right)
            for index, left in enumerate(availability_groups)
            for right in availability_groups[index + 1 :]
        ):
            raise ValueError(
                "availability tool-ID groups must not overlap"
            )
        if frozenset().union(*availability_groups) != known:
            raise ValueError(
                "availability tool-ID groups must cover every tool"
            )

        ai_assisted = frozenset(categories["ai_assisted_tool_ids"])
        normative = frozenset(categories["normative_tool_ids"])
        if ai_assisted.intersection(normative):
            raise ValueError(
                "AI-assisted tools must not be normative"
            )

        object.__setattr__(self, "catalog_version", catalog_version)
        object.__setattr__(self, "tool_ids", tool_ids)
        for field_name, values in categories.items():
            object.__setattr__(self, field_name, values)


class DiagnosticToolRegistry:
    """Immutable static registry of reviewed diagnostic-tool specifications."""

    __slots__ = ("_catalog_version", "_specs", "_by_id")

    def __init__(
        self,
        specs: Iterable[DiagnosticToolSpec] = (),
        *,
        catalog_version: str = CATALOG_VERSION,
    ) -> None:
        canonical_version = _normalize_catalog_version(catalog_version)
        prepared = _prepare_specs(
            specs,
            catalog_version=canonical_version,
        )

        self._catalog_version = canonical_version
        self._specs = prepared
        self._by_id = MappingProxyType(
            {spec.tool_id: spec for spec in prepared}
        )

    @property
    def catalog_version(self) -> str:
        return self._catalog_version

    @property
    def specs(self) -> tuple[DiagnosticToolSpec, ...]:
        return self._specs

    @property
    def tool_ids(self) -> tuple[ToolId, ...]:
        return tuple(spec.tool_id for spec in self._specs)

    @property
    def mapping(self) -> Mapping[ToolId, DiagnosticToolSpec]:
        return self._by_id

    def __iter__(self) -> Iterator[DiagnosticToolSpec]:
        return iter(self._specs)

    def __len__(self) -> int:
        return len(self._specs)

    def __bool__(self) -> bool:
        return bool(self._specs)

    def __contains__(self, tool_id: object) -> bool:
        if not isinstance(tool_id, str):
            return False
        try:
            canonical = normalize_tool_id(tool_id)
        except (TypeError, ValueError):
            return False
        return canonical in self._by_id

    def get(
        self,
        tool_id: str,
        default: DiagnosticToolSpec | None = None,
    ) -> DiagnosticToolSpec | None:
        canonical = normalize_tool_id(tool_id)
        return self._by_id.get(canonical, default)

    def require(self, tool_id: str) -> DiagnosticToolSpec:
        canonical = normalize_tool_id(tool_id)
        try:
            return self._by_id[canonical]
        except KeyError as exc:
            raise UnknownDiagnosticToolError(
                f"diagnostic tool is not registered: {canonical!r}"
            ) from exc

    def select(
        self,
        tool_ids: Iterable[str],
    ) -> tuple[DiagnosticToolSpec, ...]:
        canonical_ids = _normalize_tool_id_sequence(tool_ids)
        return tuple(self.require(tool_id) for tool_id in canonical_ids)

    def for_platform(
        self,
        platform: str,
    ) -> tuple[DiagnosticToolSpec, ...]:
        canonical_platform = _normalize_policy_value(
            platform,
            field_name="platform",
        )
        return tuple(
            spec
            for spec in self._specs
            if canonical_platform in _string_values(spec.platforms)
        )

    def by_availability(
        self,
        availability_policy: object,
    ) -> tuple[DiagnosticToolSpec, ...]:
        canonical = _normalize_policy_value(
            availability_policy,
            field_name="availability_policy",
        )
        return tuple(
            spec
            for spec in self._specs
            if _policy_value(spec.availability_policy) == canonical
        )

    def by_mutability(
        self,
        mutability: object,
    ) -> tuple[DiagnosticToolSpec, ...]:
        canonical = _normalize_policy_value(
            mutability,
            field_name="mutability",
        )
        return tuple(
            spec
            for spec in self._specs
            if _policy_value(spec.mutability) == canonical
        )

    def normative(self) -> tuple[DiagnosticToolSpec, ...]:
        return tuple(spec for spec in self._specs if spec.normative)

    def ai_assisted(self) -> tuple[DiagnosticToolSpec, ...]:
        return tuple(spec for spec in self._specs if spec.ai_assisted)

    def read_only(self) -> tuple[DiagnosticToolSpec, ...]:
        return self.by_mutability("read_only")

    def snapshot(self) -> DiagnosticToolRegistrySnapshot:
        return DiagnosticToolRegistrySnapshot(
            catalog_version=self._catalog_version,
            tool_ids=self.tool_ids,
            required_tool_ids=tuple(
                spec.tool_id
                for spec in self.by_availability("required")
            ),
            optional_tool_ids=tuple(
                spec.tool_id
                for spec in self.by_availability("optional")
            ),
            diagnostic_only_tool_ids=tuple(
                spec.tool_id
                for spec in self.by_availability("diagnostic_only")
            ),
            normative_tool_ids=tuple(
                spec.tool_id for spec in self.normative()
            ),
            ai_assisted_tool_ids=tuple(
                spec.tool_id for spec in self.ai_assisted()
            ),
        )


def normalize_tool_id(value: object) -> ToolId:
    if not isinstance(value, str):
        raise TypeError("tool_id must be a string")

    canonical = value.strip()
    if not canonical:
        raise ValueError("tool_id must not be empty")
    if len(canonical) > _MAX_TOOL_ID_LENGTH:
        raise ValueError("tool_id exceeds the supported length")
    if not canonical.isascii():
        raise ValueError("tool_id must use ASCII characters only")
    if _TOOL_ID_PATTERN.fullmatch(canonical) is None:
        raise ValueError(
            "tool_id must be lowercase ASCII letters, digits, and hyphens"
        )
    return canonical


def build_tool_registry(
    specs: Iterable[DiagnosticToolSpec],
    *,
    catalog_version: str = CATALOG_VERSION,
) -> DiagnosticToolRegistry:
    return DiagnosticToolRegistry(
        specs,
        catalog_version=catalog_version,
    )


def is_registered_tool(
    tool_id: str,
    *,
    registry: DiagnosticToolRegistry | None = None,
) -> bool:
    selected = DEFAULT_TOOL_REGISTRY if registry is None else registry
    _require_registry(selected)
    return tool_id in selected


def get_registered_tool(
    tool_id: str,
    *,
    registry: DiagnosticToolRegistry | None = None,
) -> DiagnosticToolSpec | None:
    selected = DEFAULT_TOOL_REGISTRY if registry is None else registry
    _require_registry(selected)
    return selected.get(tool_id)


def require_registered_tool(
    tool_id: str,
    *,
    registry: DiagnosticToolRegistry | None = None,
) -> DiagnosticToolSpec:
    selected = DEFAULT_TOOL_REGISTRY if registry is None else registry
    _require_registry(selected)
    return selected.require(tool_id)


def registered_tool_ids(
    *,
    registry: DiagnosticToolRegistry | None = None,
) -> tuple[ToolId, ...]:
    selected = DEFAULT_TOOL_REGISTRY if registry is None else registry
    _require_registry(selected)
    return selected.tool_ids


def _prepare_specs(
    specs: Iterable[DiagnosticToolSpec],
    *,
    catalog_version: str,
) -> tuple[DiagnosticToolSpec, ...]:
    if isinstance(specs, (str, bytes)):
        raise TypeError(
            "specs must be an iterable of DiagnosticToolSpec values"
        )

    prepared = tuple(specs)
    if len(prepared) > _MAX_TOOL_COUNT:
        raise ValueError("diagnostic-tool count exceeds the supported limit")

    by_id: dict[str, DiagnosticToolSpec] = {}
    for spec in prepared:
        if not isinstance(spec, DiagnosticToolSpec):
            raise TypeError(
                "specs must contain DiagnosticToolSpec values"
            )

        tool_id = normalize_tool_id(spec.tool_id)
        entry_version = _normalize_catalog_version(
            spec.catalog_version
        )
        if entry_version != catalog_version:
            raise CatalogVersionMismatchError(
                f"tool {tool_id!r} uses catalog version "
                f"{entry_version!r}; registry requires "
                f"{catalog_version!r}"
            )

        _validate_registry_coherence(spec)

        if tool_id in by_id:
            raise DuplicateDiagnosticToolError(
                f"duplicate diagnostic tool ID: {tool_id!r}"
            )
        by_id[tool_id] = spec

    return tuple(by_id[tool_id] for tool_id in sorted(by_id))


def _validate_registry_coherence(
    spec: DiagnosticToolSpec,
) -> None:
    if type(spec.ai_assisted) is not bool:
        raise TypeError("ai_assisted must be a bool")
    if type(spec.normative) is not bool:
        raise TypeError("normative must be a bool")
    if spec.ai_assisted and spec.normative:
        raise DiagnosticToolRegistryError(
            f"AI-assisted tool {spec.tool_id!r} must not be normative"
        )

    timeout = spec.timeout_sec
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise TypeError("timeout_sec must be a positive number")
    if timeout <= 0:
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} must have a positive timeout"
        )

    if not tuple(spec.platforms):
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} must declare supported platforms"
        )

    availability = _policy_value(spec.availability_policy)
    if availability not in {
        "required",
        "optional",
        "diagnostic_only",
    }:
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} has unsupported availability policy "
            f"{availability!r}"
        )

    mutability = _policy_value(spec.mutability)
    if mutability not in {
        "read_only",
        "run_artifacts_only",
        "project_mutating",
        "external_mutating",
    }:
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} has unsupported mutability "
            f"{mutability!r}"
        )

    confirmation = _policy_value(spec.confirmation_policy)
    if confirmation not in {
        "none",
        "explicit_user_confirmation",
        "reviewed_batch_operation",
    }:
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} has unsupported confirmation policy "
            f"{confirmation!r}"
        )

    if mutability == "read_only" and confirmation != "none":
        raise DiagnosticToolRegistryError(
            f"read-only tool {spec.tool_id!r} must not require mutation "
            "confirmation"
        )
    if mutability in {"project_mutating", "external_mutating"}:
        if confirmation == "none":
            raise DiagnosticToolRegistryError(
                f"mutating tool {spec.tool_id!r} requires explicit "
                "confirmation policy"
            )

    network = _policy_value(spec.network_policy)
    if network not in {
        "denied",
        "loopback_only",
        "approved_endpoints",
    }:
        raise DiagnosticToolRegistryError(
            f"tool {spec.tool_id!r} has unsupported network policy "
            f"{network!r}"
        )


def _normalize_catalog_version(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("catalog_version must be a string")

    canonical = value.strip()
    if not canonical:
        raise ValueError("catalog_version must not be empty")
    if len(canonical) > _MAX_VERSION_LENGTH:
        raise ValueError("catalog_version exceeds the supported length")
    if not canonical.isascii():
        raise ValueError(
            "catalog_version must use ASCII characters only"
        )
    if _VERSION_PATTERN.fullmatch(canonical) is None:
        raise ValueError(
            "catalog_version must use numeric dotted-version syntax"
        )
    return canonical


def _normalize_tool_id_sequence(
    values: Iterable[object],
) -> tuple[ToolId, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("tool IDs must be an iterable, not one string")

    canonical = tuple(normalize_tool_id(value) for value in values)
    if len(canonical) > _MAX_TOOL_COUNT:
        raise ValueError("tool-ID count exceeds the supported limit")
    if len(canonical) != len(set(canonical)):
        raise ValueError("tool IDs must not contain duplicates")
    return tuple(sorted(canonical))


def _normalize_policy_value(
    value: object,
    *,
    field_name: str,
) -> str:
    canonical = _policy_value(value)
    if not canonical:
        raise ValueError(f"{field_name} must not be empty")
    if len(canonical) > 128:
        raise ValueError(f"{field_name} exceeds the supported length")
    if not canonical.isascii():
        raise ValueError(
            f"{field_name} must use ASCII characters only"
        )
    return canonical


def _policy_value(value: object) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise TypeError("policy values must be strings or string enums")
    return raw.strip()


def _string_values(values: Iterable[object]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        return frozenset(
            (_normalize_policy_value(values, field_name="value"),)
        )
    return frozenset(
        _normalize_policy_value(value, field_name="value")
        for value in values
    )


def _require_registry(
    value: object,
) -> DiagnosticToolRegistry:
    if not isinstance(value, DiagnosticToolRegistry):
        raise TypeError("registry must be DiagnosticToolRegistry")
    return value


DEFAULT_TOOL_SPECS: Final[tuple[DiagnosticToolSpec, ...]] = ()
DEFAULT_TOOL_REGISTRY: Final[DiagnosticToolRegistry] = (
    DiagnosticToolRegistry(DEFAULT_TOOL_SPECS)
)


__all__ = (
    "CATALOG_VERSION",
    "CatalogVersionMismatchError",
    "DEFAULT_TOOL_REGISTRY",
    "DEFAULT_TOOL_SPECS",
    "DiagnosticToolRegistry",
    "DiagnosticToolRegistryError",
    "DiagnosticToolRegistrySnapshot",
    "DuplicateDiagnosticToolError",
    "ToolId",
    "UnknownDiagnosticToolError",
    "build_tool_registry",
    "get_registered_tool",
    "is_registered_tool",
    "normalize_tool_id",
    "registered_tool_ids",
    "require_registered_tool",
)
