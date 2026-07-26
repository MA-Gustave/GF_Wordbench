"""Immutable evidence projection for approved diagnostic-tool executions."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias

from gf_wordbench.infrastructure.process.models import (
    ArtifactObservation,
    ProcessResult,
)
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import ExecutionState

__all__ = (
    "EvidenceIssueCode",
    "EvidenceIssueSeverity",
    "EvidenceOrigin",
    "ToolEvidenceArtifact",
    "ToolEvidenceBundle",
    "ToolEvidenceIssue",
    "ToolEvidencePolicy",
    "build_tool_evidence",
    "ensure_tool_evidence_valid",
    "evidence_by_role",
    "evidence_paths",
    "missing_required_roles",
    "raw_evidence",
    "validate_tool_evidence",
)

StringMap: TypeAlias = Mapping[str, str]
RoleMap: TypeAlias = Mapping[str | Path, str]

_TOOL_STDOUT_ROLE: Final[str] = "tool_stdout"
_TOOL_STDERR_ROLE: Final[str] = "tool_stderr"
_AI_ANNOTATION_ROLE: Final[str] = "ai_annotation"
_ROLE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$"
)
_EMPTY_STRING_MAP: Final[StringMap] = MappingProxyType({})


@unique
class EvidenceOrigin(StrEnum):
    PROCESS_STREAM = "process_stream"
    PROCESS_ARTIFACT = "process_artifact"
    DERIVED = "derived"


@unique
class EvidenceIssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@unique
class EvidenceIssueCode(StrEnum):
    CAPTURE_INCOMPLETE = "capture_incomplete"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    MISSING_REQUIRED_ARTIFACT = "missing_required_artifact"
    ARTIFACT_KIND_MISMATCH = "artifact_kind_mismatch"
    UNDECLARED_ROLE = "undeclared_role"
    REQUIRED_ROLE_MISSING = "required_role_missing"
    PATH_OUTSIDE_ALLOWED_ROOT = "path_outside_allowed_root"
    DUPLICATE_EVIDENCE_PATH = "duplicate_evidence_path"
    DUPLICATE_ROLE_PATH = "duplicate_role_path"
    AI_EVIDENCE_MARKED_NORMATIVE = "ai_evidence_marked_normative"
    AI_ANNOTATION_ROLE_MISSING = "ai_annotation_role_missing"
    STREAM_ROLE_MISSING = "stream_role_missing"
    PROCESS_FACTS_INCOHERENT = "process_facts_incoherent"


@dataclass(frozen=True, slots=True)
class ToolEvidenceIssue:
    code: EvidenceIssueCode
    severity: EvidenceIssueSeverity
    message: str
    role: str | None = None
    path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, EvidenceIssueCode):
            object.__setattr__(self, "code", EvidenceIssueCode(self.code))
        if not isinstance(self.severity, EvidenceIssueSeverity):
            object.__setattr__(
                self,
                "severity",
                EvidenceIssueSeverity(self.severity),
            )
        object.__setattr__(
            self,
            "message",
            _required_text(self.message, "message"),
        )
        if self.role is not None:
            object.__setattr__(
                self,
                "role",
                _role(self.role, "role"),
            )
        if self.path is not None:
            object.__setattr__(
                self,
                "path",
                _normalized_path(self.path, "path"),
            )


@dataclass(frozen=True, slots=True)
class ToolEvidenceArtifact:
    path: Path
    role: str
    origin: EvidenceOrigin
    required: bool
    exists: bool
    kind_matches: bool
    size_bytes: int | None
    raw: bool
    immutable: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "path",
            _normalized_path(self.path, "path"),
        )
        object.__setattr__(
            self,
            "role",
            _role(self.role, "role"),
        )
        if not isinstance(self.origin, EvidenceOrigin):
            object.__setattr__(
                self,
                "origin",
                EvidenceOrigin(self.origin),
            )
        for name in (
            "required",
            "exists",
            "kind_matches",
            "raw",
            "immutable",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool")
        if self.size_bytes is not None:
            _non_negative_int(self.size_bytes, "size_bytes")
        if not self.exists:
            if self.kind_matches:
                raise ValueError(
                    "missing evidence cannot report a matching kind"
                )
            if self.size_bytes is not None:
                raise ValueError(
                    "missing evidence cannot report a size"
                )
        if self.origin is EvidenceOrigin.PROCESS_STREAM and not self.raw:
            raise ValueError("process-stream evidence must be raw")
        if self.raw and not self.immutable:
            raise ValueError("raw evidence must be immutable")


@dataclass(frozen=True, slots=True)
class ToolEvidencePolicy:
    declared_roles: frozenset[str]
    required_roles: frozenset[str] = field(default_factory=frozenset)
    allowed_output_roots: tuple[Path, ...] = ()
    ai_assisted: bool = False
    normative: bool = False

    def __post_init__(self) -> None:
        declared = _roles(self.declared_roles, "declared_roles")
        required = _roles(self.required_roles, "required_roles")
        if not required.issubset(declared):
            missing = sorted(required.difference(declared))
            raise ValueError(
                "required_roles must be declared: "
                + ", ".join(missing)
            )
        roots = _unique_paths(
            self.allowed_output_roots,
            "allowed_output_roots",
        )
        if not isinstance(self.ai_assisted, bool):
            raise TypeError("ai_assisted must be a bool")
        if not isinstance(self.normative, bool):
            raise TypeError("normative must be a bool")
        object.__setattr__(self, "declared_roles", declared)
        object.__setattr__(self, "required_roles", required)
        object.__setattr__(self, "allowed_output_roots", roots)

    @classmethod
    def standard(
        cls,
        *,
        output_roots: Iterable[Path] = (),
        additional_roles: Iterable[str] = (),
        required_roles: Iterable[str] = (),
        ai_assisted: bool = False,
        normative: bool = False,
    ) -> ToolEvidencePolicy:
        declared = {
            _TOOL_STDOUT_ROLE,
            _TOOL_STDERR_ROLE,
            *tuple(additional_roles),
        }
        required = {
            _TOOL_STDOUT_ROLE,
            _TOOL_STDERR_ROLE,
            *tuple(required_roles),
        }
        if ai_assisted:
            declared.add(_AI_ANNOTATION_ROLE)
        return cls(
            declared_roles=frozenset(declared),
            required_roles=frozenset(required),
            allowed_output_roots=tuple(output_roots),
            ai_assisted=ai_assisted,
            normative=normative,
        )


@dataclass(frozen=True, slots=True)
class ToolEvidenceBundle:
    operation_id: str
    operation_kind: str
    resolved_executable: Path
    command: tuple[str, ...]
    working_directory: Path
    execution_state: ExecutionState
    exit_code: int | None
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    termination_attempted: bool
    termination_succeeded: bool
    output_limit_exceeded: bool
    capture_complete: bool
    environment_policy: str
    recorded_environment_overrides: StringMap
    artifacts: tuple[ToolEvidenceArtifact, ...]
    declared_roles: frozenset[str]
    required_roles: frozenset[str]
    ai_assisted: bool
    normative: bool
    issues: tuple[ToolEvidenceIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation_id",
            _required_text(self.operation_id, "operation_id"),
        )
        object.__setattr__(
            self,
            "operation_kind",
            _required_text(self.operation_kind, "operation_kind"),
        )
        object.__setattr__(
            self,
            "resolved_executable",
            _normalized_path(
                self.resolved_executable,
                "resolved_executable",
            ),
        )
        object.__setattr__(
            self,
            "working_directory",
            _normalized_path(
                self.working_directory,
                "working_directory",
            ),
        )
        command = _command(self.command)
        if command[0] != str(self.resolved_executable):
            raise ValueError(
                "command must begin with resolved_executable"
            )
        object.__setattr__(self, "command", command)
        if not isinstance(self.execution_state, ExecutionState):
            object.__setattr__(
                self,
                "execution_state",
                ExecutionState(self.execution_state),
            )
        if self.exit_code is not None:
            _plain_int(self.exit_code, "exit_code")
        object.__setattr__(
            self,
            "started_at",
            _utc(self.started_at, "started_at"),
        )
        object.__setattr__(
            self,
            "finished_at",
            _utc(self.finished_at, "finished_at"),
        )
        if self.finished_at < self.started_at:
            raise ValueError(
                "finished_at must not precede started_at"
            )
        _non_negative_int(self.duration_ms, "duration_ms")
        for name in (
            "termination_attempted",
            "termination_succeeded",
            "output_limit_exceeded",
            "capture_complete",
            "ai_assisted",
            "normative",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool")
        if (
            self.termination_succeeded
            and not self.termination_attempted
        ):
            raise ValueError(
                "termination_succeeded requires termination_attempted"
            )
        object.__setattr__(
            self,
            "environment_policy",
            _required_text(
                self.environment_policy,
                "environment_policy",
            ),
        )
        object.__setattr__(
            self,
            "recorded_environment_overrides",
            _string_map(
                self.recorded_environment_overrides,
                "recorded_environment_overrides",
            ),
        )
        artifacts = tuple(self.artifacts)
        if not all(
            isinstance(item, ToolEvidenceArtifact)
            for item in artifacts
        ):
            raise TypeError(
                "artifacts must contain ToolEvidenceArtifact values"
            )
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(
            self,
            "declared_roles",
            _roles(self.declared_roles, "declared_roles"),
        )
        object.__setattr__(
            self,
            "required_roles",
            _roles(self.required_roles, "required_roles"),
        )
        if not self.required_roles.issubset(self.declared_roles):
            raise ValueError(
                "required_roles must be a subset of declared_roles"
            )
        issues = tuple(self.issues)
        if not all(
            isinstance(item, ToolEvidenceIssue)
            for item in issues
        ):
            raise TypeError(
                "issues must contain ToolEvidenceIssue values"
            )
        object.__setattr__(
            self,
            "issues",
            tuple(sorted(issues, key=_issue_sort_key)),
        )

    @property
    def evidence_roles(self) -> frozenset[str]:
        return frozenset(item.role for item in self.artifacts)

    @property
    def stdout(self) -> ToolEvidenceArtifact:
        return _single_role(self.artifacts, _TOOL_STDOUT_ROLE)

    @property
    def stderr(self) -> ToolEvidenceArtifact:
        return _single_role(self.artifacts, _TOOL_STDERR_ROLE)

    @property
    def output_artifacts(self) -> tuple[ToolEvidenceArtifact, ...]:
        return tuple(
            item
            for item in self.artifacts
            if item.origin is EvidenceOrigin.PROCESS_ARTIFACT
        )

    @property
    def truncated(self) -> bool:
        return self.output_limit_exceeded

    @property
    def valid(self) -> bool:
        return not any(
            issue.severity is EvidenceIssueSeverity.ERROR
            for issue in self.issues
        )

    @property
    def ready_for_interpretation(self) -> bool:
        return (
            self.valid
            and self.capture_complete
            and self.stdout.exists
            and self.stderr.exists
        )


def build_tool_evidence(
    process_result: ProcessResult,
    policy: ToolEvidencePolicy,
    *,
    role_by_artifact_path: RoleMap | None = None,
) -> ToolEvidenceBundle:
    if not isinstance(process_result, ProcessResult):
        raise TypeError("process_result must be a ProcessResult")
    if not isinstance(policy, ToolEvidencePolicy):
        raise TypeError("policy must be a ToolEvidencePolicy")

    role_map = _normalized_role_map(role_by_artifact_path)
    artifacts: list[ToolEvidenceArtifact] = [
        ToolEvidenceArtifact(
            path=process_result.stdout_path,
            role=_TOOL_STDOUT_ROLE,
            origin=EvidenceOrigin.PROCESS_STREAM,
            required=True,
            exists=True,
            kind_matches=True,
            size_bytes=process_result.stdout_size_bytes,
            raw=True,
            immutable=True,
        ),
        ToolEvidenceArtifact(
            path=process_result.stderr_path,
            role=_TOOL_STDERR_ROLE,
            origin=EvidenceOrigin.PROCESS_STREAM,
            required=True,
            exists=True,
            kind_matches=True,
            size_bytes=process_result.stderr_size_bytes,
            raw=True,
            immutable=True,
        ),
    ]

    for observation in process_result.artifact_observations:
        role = role_map.get(
            _path_key(observation.path),
            observation.role,
        )
        artifacts.append(
            _artifact_from_observation(
                observation,
                role=role,
            )
        )

    provisional = ToolEvidenceBundle(
        operation_id=process_result.operation_id,
        operation_kind=process_result.operation_kind.value,
        resolved_executable=process_result.executable,
        command=process_result.command,
        working_directory=process_result.working_directory,
        execution_state=process_result.execution_state,
        exit_code=process_result.exit_code,
        started_at=process_result.started_at,
        finished_at=process_result.finished_at,
        duration_ms=process_result.duration_ms,
        termination_attempted=process_result.termination_attempted,
        termination_succeeded=process_result.termination_succeeded,
        output_limit_exceeded=process_result.output_limit_exceeded,
        capture_complete=process_result.capture_complete,
        environment_policy=process_result.environment_policy,
        recorded_environment_overrides=(
            process_result.recorded_env_overrides
        ),
        artifacts=tuple(artifacts),
        declared_roles=policy.declared_roles,
        required_roles=policy.required_roles,
        ai_assisted=policy.ai_assisted,
        normative=policy.normative,
    )
    issues = validate_tool_evidence(
        provisional,
        allowed_output_roots=policy.allowed_output_roots,
    )
    return ToolEvidenceBundle(
        operation_id=provisional.operation_id,
        operation_kind=provisional.operation_kind,
        resolved_executable=provisional.resolved_executable,
        command=provisional.command,
        working_directory=provisional.working_directory,
        execution_state=provisional.execution_state,
        exit_code=provisional.exit_code,
        started_at=provisional.started_at,
        finished_at=provisional.finished_at,
        duration_ms=provisional.duration_ms,
        termination_attempted=provisional.termination_attempted,
        termination_succeeded=provisional.termination_succeeded,
        output_limit_exceeded=provisional.output_limit_exceeded,
        capture_complete=provisional.capture_complete,
        environment_policy=provisional.environment_policy,
        recorded_environment_overrides=(
            provisional.recorded_environment_overrides
        ),
        artifacts=provisional.artifacts,
        declared_roles=provisional.declared_roles,
        required_roles=provisional.required_roles,
        ai_assisted=provisional.ai_assisted,
        normative=provisional.normative,
        issues=issues,
    )


def validate_tool_evidence(
    bundle: ToolEvidenceBundle,
    *,
    allowed_output_roots: Iterable[Path] = (),
) -> tuple[ToolEvidenceIssue, ...]:
    if not isinstance(bundle, ToolEvidenceBundle):
        raise TypeError("bundle must be a ToolEvidenceBundle")

    roots = _unique_paths(
        allowed_output_roots,
        "allowed_output_roots",
    )
    issues: list[ToolEvidenceIssue] = []

    if not bundle.capture_complete:
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.CAPTURE_INCOMPLETE,
                severity=EvidenceIssueSeverity.ERROR,
                message=(
                    "Raw process evidence capture did not complete."
                ),
            )
        )

    if bundle.output_limit_exceeded:
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.OUTPUT_LIMIT_EXCEEDED,
                severity=EvidenceIssueSeverity.WARNING,
                message=(
                    "Retained process output reached the registered "
                    "output limit."
                ),
            )
        )

    if (
        bundle.execution_state is ExecutionState.COMPLETED
        and bundle.exit_code is None
    ):
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.PROCESS_FACTS_INCOHERENT,
                severity=EvidenceIssueSeverity.ERROR,
                message=(
                    "Completed process evidence requires an exit code."
                ),
            )
        )

    if bundle.ai_assisted and bundle.normative:
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.AI_EVIDENCE_MARKED_NORMATIVE,
                severity=EvidenceIssueSeverity.ERROR,
                message=(
                    "AI-assisted diagnostic evidence cannot be normative."
                ),
            )
        )

    if (
        bundle.ai_assisted
        and _AI_ANNOTATION_ROLE not in bundle.declared_roles
    ):
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.AI_ANNOTATION_ROLE_MISSING,
                severity=EvidenceIssueSeverity.ERROR,
                role=_AI_ANNOTATION_ROLE,
                message=(
                    "AI-assisted tool policy must declare an "
                    "ai_annotation evidence role."
                ),
            )
        )

    for stream_role in (_TOOL_STDOUT_ROLE, _TOOL_STDERR_ROLE):
        if stream_role not in bundle.declared_roles:
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.STREAM_ROLE_MISSING,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=stream_role,
                    message=(
                        f"Diagnostic-tool policy must declare "
                        f"{stream_role}."
                    ),
                )
            )

    actual_roles = bundle.evidence_roles
    for role in sorted(actual_roles.difference(bundle.declared_roles)):
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.UNDECLARED_ROLE,
                severity=EvidenceIssueSeverity.ERROR,
                role=role,
                message=(
                    f"Observed evidence role {role!r} is not declared "
                    "by the tool contract."
                ),
            )
        )

    for role in sorted(bundle.required_roles.difference(actual_roles)):
        issues.append(
            ToolEvidenceIssue(
                code=EvidenceIssueCode.REQUIRED_ROLE_MISSING,
                severity=EvidenceIssueSeverity.ERROR,
                role=role,
                message=(
                    f"Required evidence role {role!r} is absent."
                ),
            )
        )

    path_index: dict[str, ToolEvidenceArtifact] = {}
    role_path_index: set[tuple[str, str]] = set()

    for artifact in bundle.artifacts:
        key = _path_key(artifact.path)
        previous = path_index.get(key)
        if previous is not None:
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.DUPLICATE_EVIDENCE_PATH,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=artifact.role,
                    path=artifact.path,
                    message=(
                        "The same evidence path is registered more "
                        "than once."
                    ),
                )
            )
        else:
            path_index[key] = artifact

        role_path_key = (artifact.role, key)
        if role_path_key in role_path_index:
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.DUPLICATE_ROLE_PATH,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=artifact.role,
                    path=artifact.path,
                    message=(
                        "The same role and path pair is duplicated."
                    ),
                )
            )
        role_path_index.add(role_path_key)

        if roots and not _inside_any(artifact.path, roots):
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.PATH_OUTSIDE_ALLOWED_ROOT,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=artifact.role,
                    path=artifact.path,
                    message=(
                        "Evidence path is outside every registered "
                        "diagnostic-tool output root."
                    ),
                )
            )

        if artifact.required and not artifact.exists:
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.MISSING_REQUIRED_ARTIFACT,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=artifact.role,
                    path=artifact.path,
                    message="Required diagnostic-tool evidence is missing.",
                )
            )

        if artifact.exists and not artifact.kind_matches:
            issues.append(
                ToolEvidenceIssue(
                    code=EvidenceIssueCode.ARTIFACT_KIND_MISMATCH,
                    severity=EvidenceIssueSeverity.ERROR,
                    role=artifact.role,
                    path=artifact.path,
                    message=(
                        "Diagnostic-tool evidence exists but does not "
                        "match the registered artifact kind."
                    ),
                )
            )

    return tuple(sorted(issues, key=_issue_sort_key))


def ensure_tool_evidence_valid(
    bundle: ToolEvidenceBundle,
    *,
    allowed_output_roots: Iterable[Path] = (),
) -> ToolEvidenceBundle:
    issues = validate_tool_evidence(
        bundle,
        allowed_output_roots=allowed_output_roots,
    )
    errors = tuple(
        issue
        for issue in issues
        if issue.severity is EvidenceIssueSeverity.ERROR
    )
    if errors:
        first = errors[0]
        evidence = tuple(
            str(issue.path)
            for issue in errors
            if issue.path is not None
        )
        detail = "; ".join(
            f"{issue.code.value}: {issue.message}"
            for issue in errors[:8]
        )
        if len(errors) > 8:
            detail += f"; and {len(errors) - 8} additional error(s)"
        raise ContractViolationError(
            "Diagnostic-tool evidence contract failed",
            code="GF-WB-DIAG-TOOL-001",
            detail=detail,
            stage="diagnostics",
            operation="validate-tool-evidence",
            subject=bundle.operation_id,
            evidence_paths=evidence,
        )
    return bundle


def evidence_by_role(
    bundle: ToolEvidenceBundle,
) -> Mapping[str, tuple[ToolEvidenceArtifact, ...]]:
    grouped: dict[str, list[ToolEvidenceArtifact]] = {}
    for artifact in bundle.artifacts:
        grouped.setdefault(artifact.role, []).append(artifact)
    return MappingProxyType(
        {
            role: tuple(
                sorted(items, key=lambda item: _path_key(item.path))
            )
            for role, items in sorted(grouped.items())
        }
    )


def evidence_paths(
    bundle: ToolEvidenceBundle,
    *,
    existing_only: bool = True,
) -> tuple[Path, ...]:
    return tuple(
        artifact.path
        for artifact in sorted(
            bundle.artifacts,
            key=lambda item: (
                item.role,
                _path_key(item.path),
            ),
        )
        if artifact.exists or not existing_only
    )


def raw_evidence(
    bundle: ToolEvidenceBundle,
) -> tuple[ToolEvidenceArtifact, ...]:
    return tuple(
        artifact
        for artifact in bundle.artifacts
        if artifact.raw
    )


def missing_required_roles(
    bundle: ToolEvidenceBundle,
) -> tuple[str, ...]:
    present = frozenset(
        artifact.role
        for artifact in bundle.artifacts
        if artifact.exists
    )
    return tuple(sorted(bundle.required_roles.difference(present)))


def _artifact_from_observation(
    observation: ArtifactObservation,
    *,
    role: str,
) -> ToolEvidenceArtifact:
    if not isinstance(observation, ArtifactObservation):
        raise TypeError(
            "observation must be an ArtifactObservation"
        )
    return ToolEvidenceArtifact(
        path=observation.path,
        role=role,
        origin=EvidenceOrigin.PROCESS_ARTIFACT,
        required=observation.required,
        exists=observation.exists,
        kind_matches=observation.kind_matches,
        size_bytes=observation.size_bytes,
        raw=False,
        immutable=observation.exists,
    )


def _normalized_role_map(
    values: RoleMap | None,
) -> Mapping[str, str]:
    if values is None:
        return MappingProxyType({})
    if not isinstance(values, Mapping):
        raise TypeError(
            "role_by_artifact_path must be a mapping"
        )
    normalized: dict[str, str] = {}
    for raw_path, raw_role in values.items():
        path = _normalized_path(
            Path(raw_path),
            "role_by_artifact_path key",
        )
        role = _role(
            raw_role,
            "role_by_artifact_path value",
        )
        key = _path_key(path)
        previous = normalized.get(key)
        if previous is not None and previous != role:
            raise ValueError(
                f"conflicting roles for artifact path {path}"
            )
        normalized[key] = role
    return MappingProxyType(normalized)


def _single_role(
    artifacts: Sequence[ToolEvidenceArtifact],
    role: str,
) -> ToolEvidenceArtifact:
    matches = tuple(
        artifact
        for artifact in artifacts
        if artifact.role == role
    )
    if len(matches) != 1:
        raise ContractViolationError(
            f"Expected exactly one {role} evidence artifact",
            code="GF-WB-DIAG-TOOL-002",
            stage="diagnostics",
            operation="read-tool-evidence",
            subject=role,
            evidence_paths=tuple(
                str(item.path) for item in matches
            ),
        )
    return matches[0]


def _roles(
    values: Iterable[str],
    field_name: str,
) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            f"{field_name} must be an iterable of roles"
        )
    return frozenset(
        _role(value, field_name)
        for value in values
    )


def _role(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if not _ROLE_PATTERN.fullmatch(text):
        raise ValueError(
            f"{field_name} must be lowercase ASCII role text "
            "using letters, digits, underscores, or hyphens"
        )
    return text


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(
            f"{field_name} must not contain surrounding whitespace"
        )
    if "\x00" in value:
        raise ValueError(
            f"{field_name} must not contain a NUL character"
        )
    return value


def _command(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("command must be an argument sequence")
    command = tuple(values)
    if not command:
        raise ValueError("command must not be empty")
    for index, value in enumerate(command):
        _required_text(value, f"command[{index}]")
    return command


def _string_map(
    values: Mapping[str, str] | None,
    field_name: str,
) -> StringMap:
    if not values:
        return _EMPTY_STRING_MAP
    if not isinstance(values, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    copied: dict[str, str] = {}
    for key, value in values.items():
        copied[
            _required_text(key, f"{field_name} key")
        ] = _required_text(
            value,
            f"{field_name}[{key!r}]",
        )
    return MappingProxyType(copied)


def _normalized_path(value: Path, field_name: str) -> Path:
    if not isinstance(value, Path):
        value = Path(value)
    if "\x00" in os.fspath(value):
        raise ValueError(
            f"{field_name} must not contain a NUL character"
        )
    normalized = Path(os.path.normpath(os.fspath(value)))
    if not normalized.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return normalized


def _unique_paths(
    values: Iterable[Path],
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError(
            f"{field_name} must be an iterable of paths"
        )
    normalized: dict[str, Path] = {}
    for value in values:
        path = _normalized_path(Path(value), field_name)
        normalized.setdefault(_path_key(path), path)
    return tuple(
        normalized[key] for key in sorted(normalized)
    )


def _path_key(path: Path) -> str:
    return os.path.normcase(
        os.path.normpath(os.fspath(path))
    )


def _inside_any(
    path: Path,
    roots: Sequence[Path],
) -> bool:
    candidate = _normalized_path(path, "path")
    return any(
        candidate == root or candidate.is_relative_to(root)
        for root in roots
    )


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _plain_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _non_negative_int(value: int, field_name: str) -> int:
    _plain_int(value, field_name)
    if value < 0:
        raise ValueError(
            f"{field_name} must be non-negative"
        )
    return value


def _issue_sort_key(
    issue: ToolEvidenceIssue,
) -> tuple[int, str, str, str, str]:
    severity_rank = {
        EvidenceIssueSeverity.ERROR: 0,
        EvidenceIssueSeverity.WARNING: 1,
    }
    return (
        severity_rank[issue.severity],
        issue.code.value,
        issue.role or "",
        _path_key(issue.path) if issue.path is not None else "",
        issue.message,
    )
