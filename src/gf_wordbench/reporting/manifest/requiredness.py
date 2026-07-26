from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Final

from gf_wordbench.kernel.statuses import ValidationMode


@unique
class RequirednessSource(StrEnum):
    PATH_OVERRIDE = "path_override"
    ROLE_OVERRIDE = "role_override"
    DECLARATION = "declaration"
    FRAMEWORK = "framework"
    MODE = "mode"
    EXECUTED_STAGE = "executed_stage"
    SCENARIO = "scenario"
    ARTIFACT_CONTRACT = "artifact_contract"
    CONDITIONAL = "conditional"
    DEFAULT = "default"


@unique
class RequirednessReason(StrEnum):
    EXPLICIT_PATH_REQUIRED = "explicit_path_required"
    EXPLICIT_PATH_OPTIONAL = "explicit_path_optional"
    EXPLICIT_ROLE_REQUIRED = "explicit_role_required"
    EXPLICIT_ROLE_OPTIONAL = "explicit_role_optional"
    DECLARED_REQUIRED = "declared_required"
    DECLARED_OPTIONAL = "declared_optional"
    FRAMEWORK_FINAL_ARTIFACT = "framework_final_artifact"
    CHECKPOINT_AGGREGATE = "checkpoint_aggregate"
    RELEASE_AGGREGATE = "release_aggregate"
    REQUIRED_EXECUTED_STAGE_EVIDENCE = "required_executed_stage_evidence"
    REQUIRED_SCENARIO_STREAM = "required_scenario_stream"
    REQUIRED_SCENARIO_OUTPUT = "required_scenario_output"
    REQUIRED_COMPILE_ARTIFACT = "required_compile_artifact"
    REQUIRED_RELEASE_PGF = "required_release_pgf"
    REQUIRED_ARTIFACT_CONTRACT = "required_artifact_contract"
    CONDITION_ACTIVE = "condition_active"
    CONDITION_INACTIVE = "condition_inactive"
    STAGE_NOT_EXECUTED = "stage_not_executed"
    STAGE_OPTIONAL = "stage_optional"
    SCENARIO_OPTIONAL = "scenario_optional"
    DEFAULT_OPTIONAL = "default_optional"


FRAMEWORK_FINAL_ROLES: Final[frozenset[str]] = frozenset(
    {
        "machine_summary",
        "human_summary",
        "ai_handoff",
        "top_errors",
        "master_log",
    }
)

AGGREGATE_ROLES: Final[frozenset[str]] = frozenset(
    {
        "aggregate_log",
        "aggregate_scan_log",
        "aggregate_operation_log",
    }
)

PROCESS_STREAM_ROLES: Final[frozenset[str]] = frozenset(
    {
        "version_stdout",
        "version_stderr",
        "compile_stdout",
        "compile_stderr",
        "pgf_stdout",
        "pgf_stderr",
        "scenario_stdout",
        "scenario_stderr",
    }
)

SCENARIO_STREAM_ROLES: Final[frozenset[str]] = frozenset(
    {
        "scenario_stdout",
        "scenario_stderr",
    }
)

COMPILE_ARTIFACT_ROLES: Final[frozenset[str]] = frozenset({"gfo"})
PGF_ROLES: Final[frozenset[str]] = frozenset({"pgf"})
SCENARIO_OUTPUT_ROLES: Final[frozenset[str]] = frozenset({"scenario_output"})


@dataclass(frozen=True, slots=True)
class RequirednessContext:
    mode: ValidationMode
    finalized: bool = True
    framework_required_roles: frozenset[str] = FRAMEWORK_FINAL_ROLES
    required_roles: frozenset[str] = frozenset()
    optional_roles: frozenset[str] = frozenset()
    path_overrides: Mapping[str, bool] = field(default_factory=dict)
    role_overrides: Mapping[str, bool] = field(default_factory=dict)
    require_aggregate_logs: bool | None = None
    release_requires_pgf: bool = False
    strict: bool = False

    def __post_init__(self) -> None:
        mode = _coerce_mode(self.mode)
        framework = _normalize_roles(self.framework_required_roles)
        required = _normalize_roles(self.required_roles)
        optional = _normalize_roles(self.optional_roles)
        if required & optional:
            overlap = ", ".join(sorted(required & optional))
            raise ValueError(f"roles cannot be both required and optional: {overlap}")
        path_overrides = _freeze_bool_mapping(
            self.path_overrides,
            normalize_key=_normalize_manifest_path,
            field_name="path_overrides",
        )
        role_overrides = _freeze_bool_mapping(
            self.role_overrides,
            normalize_key=_normalize_role,
            field_name="role_overrides",
        )
        if self.require_aggregate_logs is not None and type(self.require_aggregate_logs) is not bool:
            raise TypeError("require_aggregate_logs must be bool or None")
        if type(self.release_requires_pgf) is not bool:
            raise TypeError("release_requires_pgf must be bool")
        if type(self.finalized) is not bool:
            raise TypeError("finalized must be bool")
        if type(self.strict) is not bool:
            raise TypeError("strict must be bool")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "framework_required_roles", framework)
        object.__setattr__(self, "required_roles", required)
        object.__setattr__(self, "optional_roles", optional)
        object.__setattr__(self, "path_overrides", path_overrides)
        object.__setattr__(self, "role_overrides", role_overrides)


@dataclass(frozen=True, slots=True)
class ArtifactRequirednessRequest:
    role: str
    path: str | Path | PurePosixPath | None = None
    declared_required: bool | None = None
    stage_id: str | None = None
    stage_executed: bool | None = None
    stage_required: bool | None = None
    scenario_id: str | None = None
    scenario_required: bool | None = None
    assertions_enabled: bool = False
    gold_comparison_enabled: bool = False
    artifact_contract_required: bool = False
    activation_condition: bool | None = None

    def __post_init__(self) -> None:
        role = _normalize_role(self.role)
        path = None if self.path is None else _normalize_manifest_path(self.path)
        declared_required = _optional_bool(self.declared_required, "declared_required")
        stage_executed = _optional_bool(self.stage_executed, "stage_executed")
        stage_required = _optional_bool(self.stage_required, "stage_required")
        scenario_required = _optional_bool(self.scenario_required, "scenario_required")
        activation_condition = _optional_bool(
            self.activation_condition,
            "activation_condition",
        )
        if type(self.assertions_enabled) is not bool:
            raise TypeError("assertions_enabled must be bool")
        if type(self.gold_comparison_enabled) is not bool:
            raise TypeError("gold_comparison_enabled must be bool")
        if type(self.artifact_contract_required) is not bool:
            raise TypeError("artifact_contract_required must be bool")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "declared_required", declared_required)
        object.__setattr__(self, "stage_id", _optional_text(self.stage_id, "stage_id"))
        object.__setattr__(self, "stage_executed", stage_executed)
        object.__setattr__(self, "stage_required", stage_required)
        object.__setattr__(self, "scenario_id", _optional_text(self.scenario_id, "scenario_id"))
        object.__setattr__(self, "scenario_required", scenario_required)
        object.__setattr__(self, "activation_condition", activation_condition)


@dataclass(frozen=True, slots=True)
class RequirednessDecision:
    required: bool
    source: RequirednessSource
    reason: RequirednessReason
    role: str
    path: str | None = None

    def __post_init__(self) -> None:
        if type(self.required) is not bool:
            raise TypeError("required must be bool")
        if not isinstance(self.source, RequirednessSource):
            raise TypeError("source must be RequirednessSource")
        if not isinstance(self.reason, RequirednessReason):
            raise TypeError("reason must be RequirednessReason")
        object.__setattr__(self, "role", _normalize_role(self.role))
        if self.path is not None:
            object.__setattr__(self, "path", _normalize_manifest_path(self.path))


class RequirednessPolicy:
    __slots__ = ("_context",)

    def __init__(self, context: RequirednessContext) -> None:
        if not isinstance(context, RequirednessContext):
            raise TypeError("context must be RequirednessContext")
        self._context = context

    @property
    def context(self) -> RequirednessContext:
        return self._context

    def resolve(self, request: ArtifactRequirednessRequest) -> RequirednessDecision:
        if not isinstance(request, ArtifactRequirednessRequest):
            raise TypeError("request must be ArtifactRequirednessRequest")
        return _resolve(request, self._context)

    def is_required(self, request: ArtifactRequirednessRequest) -> bool:
        return self.resolve(request).required

    def resolve_many(
        self,
        requests: Iterable[ArtifactRequirednessRequest],
    ) -> tuple[RequirednessDecision, ...]:
        if isinstance(requests, (str, bytes)):
            raise TypeError("requests must be an iterable of requests")
        return tuple(self.resolve(request) for request in requests)


def resolve_requiredness(
    request: ArtifactRequirednessRequest,
    context: RequirednessContext,
) -> RequirednessDecision:
    return RequirednessPolicy(context).resolve(request)


def resolve_artifact_requiredness(
    role: str,
    *,
    mode: ValidationMode | str,
    path: str | Path | PurePosixPath | None = None,
    declared_required: bool | None = None,
    stage_id: str | None = None,
    stage_executed: bool | None = None,
    stage_required: bool | None = None,
    scenario_id: str | None = None,
    scenario_required: bool | None = None,
    assertions_enabled: bool = False,
    gold_comparison_enabled: bool = False,
    artifact_contract_required: bool = False,
    activation_condition: bool | None = None,
    finalized: bool = True,
    framework_required_roles: Iterable[str] = FRAMEWORK_FINAL_ROLES,
    required_roles: Iterable[str] = (),
    optional_roles: Iterable[str] = (),
    path_overrides: Mapping[str, bool] | None = None,
    role_overrides: Mapping[str, bool] | None = None,
    require_aggregate_logs: bool | None = None,
    release_requires_pgf: bool = False,
    strict: bool = False,
) -> RequirednessDecision:
    context = RequirednessContext(
        mode=_coerce_mode(mode),
        finalized=finalized,
        framework_required_roles=frozenset(framework_required_roles),
        required_roles=frozenset(required_roles),
        optional_roles=frozenset(optional_roles),
        path_overrides={} if path_overrides is None else path_overrides,
        role_overrides={} if role_overrides is None else role_overrides,
        require_aggregate_logs=require_aggregate_logs,
        release_requires_pgf=release_requires_pgf,
        strict=strict,
    )
    request = ArtifactRequirednessRequest(
        role=role,
        path=path,
        declared_required=declared_required,
        stage_id=stage_id,
        stage_executed=stage_executed,
        stage_required=stage_required,
        scenario_id=scenario_id,
        scenario_required=scenario_required,
        assertions_enabled=assertions_enabled,
        gold_comparison_enabled=gold_comparison_enabled,
        artifact_contract_required=artifact_contract_required,
        activation_condition=activation_condition,
    )
    return resolve_requiredness(request, context)


def is_artifact_required(
    role: str,
    *,
    mode: ValidationMode | str,
    **kwargs: Any,
) -> bool:
    return resolve_artifact_requiredness(role, mode=mode, **kwargs).required


def resolve_declaration_requiredness(
    declaration: object,
    context: RequirednessContext,
    *,
    stage_id: str | None = None,
    stage_executed: bool | None = None,
    stage_required: bool | None = None,
    scenario_id: str | None = None,
    scenario_required: bool | None = None,
    assertions_enabled: bool = False,
    gold_comparison_enabled: bool = False,
    artifact_contract_required: bool = False,
    activation_condition: bool | None = None,
) -> RequirednessDecision:
    role = _attribute(declaration, "role")
    path = _attribute(declaration, "path", default=None)
    declared_required = _attribute(declaration, "required", default=None)
    request = ArtifactRequirednessRequest(
        role=role,
        path=path,
        declared_required=declared_required,
        stage_id=stage_id,
        stage_executed=stage_executed,
        stage_required=stage_required,
        scenario_id=scenario_id,
        scenario_required=scenario_required,
        assertions_enabled=assertions_enabled,
        gold_comparison_enabled=gold_comparison_enabled,
        artifact_contract_required=artifact_contract_required,
        activation_condition=activation_condition,
    )
    return resolve_requiredness(request, context)


def required_framework_roles(
    mode: ValidationMode | str,
    *,
    finalized: bool = True,
    framework_required_roles: Iterable[str] = FRAMEWORK_FINAL_ROLES,
    require_aggregate_logs: bool | None = None,
) -> frozenset[str]:
    canonical_mode = _coerce_mode(mode)
    roles = set(_normalize_roles(framework_required_roles)) if finalized else set()
    aggregate_required = require_aggregate_logs
    if aggregate_required is None:
        aggregate_required = canonical_mode in {
            ValidationMode.CHECKPOINT,
            ValidationMode.RELEASE,
        }
    if aggregate_required:
        roles.update(AGGREGATE_ROLES)
    return frozenset(roles)


def validate_requiredness_conflicts(context: RequirednessContext) -> None:
    if not isinstance(context, RequirednessContext):
        raise TypeError("context must be RequirednessContext")
    path_conflicts = {
        path
        for path, value in context.path_overrides.items()
        if type(value) is not bool
    }
    if path_conflicts:
        raise ValueError("path overrides contain non-boolean values")
    role_conflicts = context.required_roles & context.optional_roles
    if role_conflicts:
        overlap = ", ".join(sorted(role_conflicts))
        raise ValueError(f"roles cannot be both required and optional: {overlap}")


def _resolve(
    request: ArtifactRequirednessRequest,
    context: RequirednessContext,
) -> RequirednessDecision:
    role = request.role
    path = request.path

    if path is not None and path in context.path_overrides:
        required = context.path_overrides[path]
        return RequirednessDecision(
            required=required,
            source=RequirednessSource.PATH_OVERRIDE,
            reason=(
                RequirednessReason.EXPLICIT_PATH_REQUIRED
                if required
                else RequirednessReason.EXPLICIT_PATH_OPTIONAL
            ),
            role=role,
            path=path,
        )

    if role in context.role_overrides:
        required = context.role_overrides[role]
        return RequirednessDecision(
            required=required,
            source=RequirednessSource.ROLE_OVERRIDE,
            reason=(
                RequirednessReason.EXPLICIT_ROLE_REQUIRED
                if required
                else RequirednessReason.EXPLICIT_ROLE_OPTIONAL
            ),
            role=role,
            path=path,
        )

    if role in context.required_roles:
        return RequirednessDecision(
            True,
            RequirednessSource.ROLE_OVERRIDE,
            RequirednessReason.EXPLICIT_ROLE_REQUIRED,
            role,
            path,
        )

    if role in context.optional_roles:
        return RequirednessDecision(
            False,
            RequirednessSource.ROLE_OVERRIDE,
            RequirednessReason.EXPLICIT_ROLE_OPTIONAL,
            role,
            path,
        )

    if request.declared_required is not None:
        return RequirednessDecision(
            request.declared_required,
            RequirednessSource.DECLARATION,
            (
                RequirednessReason.DECLARED_REQUIRED
                if request.declared_required
                else RequirednessReason.DECLARED_OPTIONAL
            ),
            role,
            path,
        )

    if request.activation_condition is False:
        return RequirednessDecision(
            False,
            RequirednessSource.CONDITIONAL,
            RequirednessReason.CONDITION_INACTIVE,
            role,
            path,
        )

    if request.artifact_contract_required:
        if role in PGF_ROLES and context.mode is ValidationMode.RELEASE:
            reason = RequirednessReason.REQUIRED_RELEASE_PGF
        elif role in COMPILE_ARTIFACT_ROLES:
            reason = RequirednessReason.REQUIRED_COMPILE_ARTIFACT
        else:
            reason = RequirednessReason.REQUIRED_ARTIFACT_CONTRACT
        return RequirednessDecision(
            True,
            RequirednessSource.ARTIFACT_CONTRACT,
            reason,
            role,
            path,
        )

    if (
        context.finalized
        and role in context.framework_required_roles
    ):
        return RequirednessDecision(
            True,
            RequirednessSource.FRAMEWORK,
            RequirednessReason.FRAMEWORK_FINAL_ARTIFACT,
            role,
            path,
        )

    if role in AGGREGATE_ROLES:
        required = context.require_aggregate_logs
        if required is None:
            required = context.mode in {
                ValidationMode.CHECKPOINT,
                ValidationMode.RELEASE,
            }
        if required:
            reason = (
                RequirednessReason.RELEASE_AGGREGATE
                if context.mode is ValidationMode.RELEASE
                else RequirednessReason.CHECKPOINT_AGGREGATE
            )
            return RequirednessDecision(
                True,
                RequirednessSource.MODE,
                reason,
                role,
                path,
            )

    if role in PGF_ROLES and context.mode is ValidationMode.RELEASE and context.release_requires_pgf:
        return RequirednessDecision(
            True,
            RequirednessSource.MODE,
            RequirednessReason.REQUIRED_RELEASE_PGF,
            role,
            path,
        )

    if role in SCENARIO_OUTPUT_ROLES:
        if request.scenario_required and (
            request.assertions_enabled or request.gold_comparison_enabled
        ):
            return RequirednessDecision(
                True,
                RequirednessSource.SCENARIO,
                RequirednessReason.REQUIRED_SCENARIO_OUTPUT,
                role,
                path,
            )
        if request.scenario_required is False:
            return RequirednessDecision(
                False,
                RequirednessSource.SCENARIO,
                RequirednessReason.SCENARIO_OPTIONAL,
                role,
                path,
            )

    if role in SCENARIO_STREAM_ROLES:
        if request.stage_executed is False:
            return RequirednessDecision(
                False,
                RequirednessSource.EXECUTED_STAGE,
                RequirednessReason.STAGE_NOT_EXECUTED,
                role,
                path,
            )
        if request.scenario_required and request.stage_executed is not False:
            return RequirednessDecision(
                True,
                RequirednessSource.SCENARIO,
                RequirednessReason.REQUIRED_SCENARIO_STREAM,
                role,
                path,
            )
        if request.scenario_required is False:
            return RequirednessDecision(
                False,
                RequirednessSource.SCENARIO,
                RequirednessReason.SCENARIO_OPTIONAL,
                role,
                path,
            )

    if role in PROCESS_STREAM_ROLES:
        if request.stage_executed is False:
            return RequirednessDecision(
                False,
                RequirednessSource.EXECUTED_STAGE,
                RequirednessReason.STAGE_NOT_EXECUTED,
                role,
                path,
            )
        if request.stage_required and request.stage_executed is not False:
            return RequirednessDecision(
                True,
                RequirednessSource.EXECUTED_STAGE,
                RequirednessReason.REQUIRED_EXECUTED_STAGE_EVIDENCE,
                role,
                path,
            )
        if request.stage_required is False:
            return RequirednessDecision(
                False,
                RequirednessSource.EXECUTED_STAGE,
                RequirednessReason.STAGE_OPTIONAL,
                role,
                path,
            )

    if request.activation_condition is True:
        return RequirednessDecision(
            True,
            RequirednessSource.CONDITIONAL,
            RequirednessReason.CONDITION_ACTIVE,
            role,
            path,
        )

    return RequirednessDecision(
        False,
        RequirednessSource.DEFAULT,
        RequirednessReason.DEFAULT_OPTIONAL,
        role,
        path,
    )


def _normalize_role(value: object) -> str:
    if hasattr(value, "value") and isinstance(getattr(value, "value"), str):
        value = getattr(value, "value")
    if not isinstance(value, str):
        raise TypeError("role must be a string or string enum")
    normalized = value.strip().lower().replace("-", "_")
    if not normalized or "\x00" in normalized:
        raise ValueError("role must be non-empty and contain no NUL")
    return normalized


def _normalize_roles(values: Iterable[str]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise TypeError("roles must be an iterable of role strings")
    return frozenset(_normalize_role(value) for value in values)


def _normalize_manifest_path(value: object) -> str:
    if isinstance(value, Path):
        value = value.as_posix()
    elif isinstance(value, PurePosixPath):
        value = value.as_posix()
    if not isinstance(value, str):
        raise TypeError("manifest path must be a string or path")
    text = value.strip().replace("\\", "/")
    if not text or "\x00" in text:
        raise ValueError("manifest path must be non-empty and contain no NUL")
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or ":" in candidate.parts[0]:
        raise ValueError("manifest path must be run-relative")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError("manifest path must be normalized and contain no traversal")
    normalized = candidate.as_posix()
    if normalized == "manifest.json":
        raise ValueError("manifest.json cannot be an artifact declaration")
    return normalized


def _freeze_bool_mapping(
    value: Mapping[object, object],
    *,
    normalize_key: Any,
    field_name: str,
) -> Mapping[str, bool]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    result: dict[str, bool] = {}
    for raw_key, raw_value in value.items():
        key = normalize_key(raw_key)
        if type(raw_value) is not bool:
            raise TypeError(f"{field_name} values must be bool")
        if key in result and result[key] != raw_value:
            raise ValueError(f"conflicting {field_name} entry for {key!r}")
        result[key] = raw_value
    return MappingProxyType(result)


def _coerce_mode(value: ValidationMode | str) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise TypeError("mode must be ValidationMode or string")
    try:
        return ValidationMode(value.strip().lower())
    except ValueError as exc:
        raise ValueError(f"unknown validation mode: {value!r}") from exc


def _optional_bool(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be bool or None")
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be string or None")
    normalized = value.strip()
    if not normalized or "\x00" in normalized:
        raise ValueError(f"{field_name} must be non-empty and contain no NUL")
    return normalized


def _attribute(instance: object, name: str, *, default: object = ...) -> Any:
    if hasattr(instance, name):
        return getattr(instance, name)
    if isinstance(instance, Mapping) and name in instance:
        return instance[name]
    if default is not ...:
        return default
    raise TypeError(f"declaration does not provide {name!r}")


__all__ = (
    "AGGREGATE_ROLES",
    "ArtifactRequirednessRequest",
    "COMPILE_ARTIFACT_ROLES",
    "FRAMEWORK_FINAL_ROLES",
    "PGF_ROLES",
    "PROCESS_STREAM_ROLES",
    "RequirednessContext",
    "RequirednessDecision",
    "RequirednessPolicy",
    "RequirednessReason",
    "RequirednessSource",
    "SCENARIO_OUTPUT_ROLES",
    "SCENARIO_STREAM_ROLES",
    "is_artifact_required",
    "required_framework_roles",
    "resolve_artifact_requiredness",
    "resolve_declaration_requiredness",
    "resolve_requiredness",
    "validate_requiredness_conflicts",
)
