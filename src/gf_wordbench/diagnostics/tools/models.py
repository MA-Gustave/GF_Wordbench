"""Immutable contracts for registered diagnostic-tool execution."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final, NewType, Protocol, TypeAlias, TypeVar, runtime_checkable

from gf_wordbench.kernel.ids import (
    ProjectId,
    RunId,
    validate_project_id,
    validate_run_id,
)
from gf_wordbench.kernel.statuses import ExecutionState

ToolId = NewType("ToolId", str)
ToolFlagValue: TypeAlias = str | int | float | bool | Path | tuple[str, ...]
ToolFlagValues: TypeAlias = Mapping[str, ToolFlagValue]
StringMap: TypeAlias = Mapping[str, str]

_EnumT = TypeVar("_EnumT", bound=StrEnum)
_ItemT = TypeVar("_ItemT")

_TOOL_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_PORTABLE_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")
_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z.-]+)?$"
)
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_MAX_TEXT: Final[int] = 16_384
_MAX_ITEMS: Final[int] = 100_000
_EMPTY_STRING_MAP: Final[StringMap] = MappingProxyType({})
_EMPTY_FLAG_VALUES: Final[ToolFlagValues] = MappingProxyType({})


@unique
class ToolExecutableResolutionKind(StrEnum):
    BUNDLED = "bundled"
    CONFIGURED_ABSOLUTE_PATH = "configured_absolute_path"
    APPROVED_PATH_LOOKUP = "approved_path_lookup"
    PLATFORM_REGISTERED_LOCATION = "platform_registered_location"


@unique
class ToolWorkingDirectoryPolicy(StrEnum):
    RUN_DIRECTORY = "run_directory"
    ACTIVE_PROJECT_ROOT = "active_project_root"
    SOURCE_ROOT = "source_root"
    TOOL_TEMPORARY_DIRECTORY = "tool_temporary_directory"


@unique
class ToolMutability(StrEnum):
    READ_ONLY = "read_only"
    RUN_ARTIFACTS_ONLY = "run_artifacts_only"
    PROJECT_MUTATING = "project_mutating"
    EXTERNAL_MUTATING = "external_mutating"


@unique
class ToolConfirmationPolicy(StrEnum):
    NONE = "none"
    EXPLICIT_USER_CONFIRMATION = "explicit_user_confirmation"
    REVIEWED_BATCH_OPERATION = "reviewed_batch_operation"


@unique
class ToolNetworkPolicy(StrEnum):
    DENIED = "denied"
    LOOPBACK_ONLY = "loopback_only"
    APPROVED_ENDPOINTS = "approved_endpoints"


@unique
class ToolAvailabilityPolicy(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DIAGNOSTIC_ONLY = "diagnostic_only"


@unique
class ToolPlatform(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


@unique
class ToolFlagType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    CHOICE = "choice"
    PATH = "path"
    STRING_LIST = "string_list"


@unique
class ToolStdinPolicy(StrEnum):
    NONE = "none"
    TEXT = "text"
    FILE = "file"


@unique
class ToolTemporaryFilePolicy(StrEnum):
    PROHIBITED = "prohibited"
    TOOL_OWNED_RUN_DIRECTORY = "tool_owned_run_directory"


@unique
class ToolEvidenceRole(StrEnum):
    TOOL_STDOUT = "tool_stdout"
    TOOL_STDERR = "tool_stderr"
    TOOL_REPORT = "tool_report"
    TOOL_METADATA = "tool_metadata"
    TOOL_DIFF = "tool_diff"
    TOOL_RECOVERY_RECORD = "tool_recovery_record"
    AI_ANNOTATION = "ai_annotation"


@unique
class ToolExecutionStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@unique
class ToolResultKind(StrEnum):
    SUCCESS_WITH_FINDINGS = "success_with_findings"
    SUCCESS_WITHOUT_FINDINGS = "success_without_findings"
    TOOL_FAILURE = "tool_failure"
    LAUNCH_FAILURE = "launch_failure"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    PARSER_FAILURE = "parser_failure"
    INVALID_REQUEST = "invalid_request"
    UNAVAILABLE_OPTIONAL_TOOL = "unavailable_optional_tool"


@unique
class UnparseableVersionPolicy(StrEnum):
    ERROR = "error"
    WARN = "warn"
    SKIP = "skip"


@dataclass(frozen=True, slots=True)
class ToolVersionPolicy:
    minimum_version: str | None = None
    maximum_version: str | None = None
    tested_versions: tuple[str, ...] = ()
    blocked_versions: tuple[str, ...] = ()
    version_probe: tuple[str, ...] = ()
    unparseable_version_policy: UnparseableVersionPolicy = UnparseableVersionPolicy.ERROR

    def __post_init__(self) -> None:
        minimum = _optional_version(self.minimum_version, "minimum_version")
        maximum = _optional_version(self.maximum_version, "maximum_version")
        tested = _version_tuple(self.tested_versions, "tested_versions")
        blocked = _version_tuple(self.blocked_versions, "blocked_versions")
        probe = _argument_tuple(self.version_probe, "version_probe")
        if not isinstance(
            self.unparseable_version_policy,
            UnparseableVersionPolicy,
        ):
            raise TypeError("unparseable_version_policy must be UnparseableVersionPolicy")
        if set(tested).intersection(blocked):
            raise ValueError("tested_versions and blocked_versions must be disjoint")
        object.__setattr__(self, "minimum_version", minimum)
        object.__setattr__(self, "maximum_version", maximum)
        object.__setattr__(self, "tested_versions", tested)
        object.__setattr__(self, "blocked_versions", blocked)
        object.__setattr__(self, "version_probe", probe)


@dataclass(frozen=True, slots=True)
class ToolExecutableResolution:
    kind: ToolExecutableResolutionKind
    executable_name: str
    configuration_key: str | None = None
    approved_path_names: tuple[str, ...] = ()
    platform_locations: Mapping[ToolPlatform, tuple[Path, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ToolExecutableResolutionKind):
            raise TypeError("kind must be ToolExecutableResolutionKind")
        executable_name = _require_text(
            self.executable_name,
            "executable_name",
            max_length=512,
        )
        configuration_key = _optional_portable_id(
            self.configuration_key,
            "configuration_key",
        )
        approved_names = _text_tuple(
            self.approved_path_names,
            "approved_path_names",
            max_length=512,
        )
        locations = _freeze_platform_paths(self.platform_locations)
        if self.kind is ToolExecutableResolutionKind.CONFIGURED_ABSOLUTE_PATH:
            if configuration_key is None:
                raise ValueError("configured absolute-path resolution requires configuration_key")
        elif configuration_key is not None:
            raise ValueError(
                "configuration_key is permitted only for configured absolute-path resolution"
            )
        if self.kind is ToolExecutableResolutionKind.APPROVED_PATH_LOOKUP:
            if not approved_names:
                raise ValueError("approved PATH lookup requires approved_path_names")
        elif approved_names:
            raise ValueError("approved_path_names are permitted only for approved PATH lookup")
        if self.kind is ToolExecutableResolutionKind.PLATFORM_REGISTERED_LOCATION:
            if not locations:
                raise ValueError(
                    "platform registered-location resolution requires platform_locations"
                )
        elif locations:
            raise ValueError(
                "platform_locations are permitted only for platform registered-location resolution"
            )
        object.__setattr__(self, "executable_name", executable_name)
        object.__setattr__(self, "configuration_key", configuration_key)
        object.__setattr__(self, "approved_path_names", approved_names)
        object.__setattr__(self, "platform_locations", locations)


@dataclass(frozen=True, slots=True)
class ToolInputContract:
    subject_kinds: tuple[str, ...]
    file_types: tuple[str, ...] = ()
    encodings: tuple[str, ...] = ("utf-8",)
    maximum_input_count: int = 1
    maximum_input_size_bytes: int = 8 * 1024 * 1024
    stdin_policy: ToolStdinPolicy = ToolStdinPolicy.NONE
    temporary_file_policy: ToolTemporaryFilePolicy = ToolTemporaryFilePolicy.PROHIBITED

    def __post_init__(self) -> None:
        subject_kinds = _id_tuple(self.subject_kinds, "subject_kinds")
        if not subject_kinds:
            raise ValueError("subject_kinds must not be empty")
        file_types = _file_type_tuple(self.file_types)
        encodings = _text_tuple(
            self.encodings,
            "encodings",
            max_length=128,
        )
        if not encodings:
            raise ValueError("encodings must not be empty")
        _positive_int(self.maximum_input_count, "maximum_input_count")
        _positive_int(
            self.maximum_input_size_bytes,
            "maximum_input_size_bytes",
        )
        if not isinstance(self.stdin_policy, ToolStdinPolicy):
            raise TypeError("stdin_policy must be ToolStdinPolicy")
        if not isinstance(
            self.temporary_file_policy,
            ToolTemporaryFilePolicy,
        ):
            raise TypeError("temporary_file_policy must be ToolTemporaryFilePolicy")
        object.__setattr__(self, "subject_kinds", subject_kinds)
        object.__setattr__(self, "file_types", file_types)
        object.__setattr__(self, "encodings", encodings)


@dataclass(frozen=True, slots=True)
class ToolFlagSpec:
    name: str
    argument: str
    value_type: ToolFlagType
    required: bool = False
    repeatable: bool = False
    sensitive: bool = False
    default: ToolFlagValue | None = None
    choices: tuple[str, ...] = ()
    mutually_exclusive_with: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = _portable_id(self.name, "name")
        argument = _require_text(self.argument, "argument", max_length=256)
        if not argument.startswith("-") or any(
            marker in argument for marker in (" ", "\t", "\n", "\r")
        ):
            raise ValueError(
                "argument must be one shell-free command-line token beginning with '-'"
            )
        if not isinstance(self.value_type, ToolFlagType):
            raise TypeError("value_type must be ToolFlagType")
        for field_name in ("required", "repeatable", "sensitive"):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        choices = _text_tuple(self.choices, "choices", max_length=512)
        exclusions = _id_tuple(
            self.mutually_exclusive_with,
            "mutually_exclusive_with",
        )
        if name in exclusions:
            raise ValueError("a flag cannot exclude itself")
        if self.value_type is ToolFlagType.CHOICE and not choices:
            raise ValueError("choice flags require choices")
        if self.value_type is not ToolFlagType.CHOICE and choices:
            raise ValueError("choices are permitted only for choice flags")
        if self.required and self.default is not None:
            raise ValueError("required flags must not define a default")
        if self.default is not None:
            _validate_flag_value(self.default, self.value_type, choices)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "argument", argument)
        object.__setattr__(self, "choices", choices)
        object.__setattr__(self, "mutually_exclusive_with", exclusions)


@dataclass(frozen=True, slots=True)
class ToolEnvironmentPolicy:
    policy_id: str
    allowed_variables: tuple[str, ...] = ()
    removed_variables: tuple[str, ...] = ()
    inherited_variables: tuple[str, ...] = ()
    sensitive_variables: tuple[str, ...] = ()
    locale: str = "C"
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        policy_id = _portable_id(self.policy_id, "policy_id")
        allowed = _environment_names(
            self.allowed_variables,
            "allowed_variables",
        )
        removed = _environment_names(
            self.removed_variables,
            "removed_variables",
        )
        inherited = _environment_names(
            self.inherited_variables,
            "inherited_variables",
        )
        sensitive = _environment_names(
            self.sensitive_variables,
            "sensitive_variables",
        )
        if set(removed).intersection(inherited):
            raise ValueError("removed_variables and inherited_variables must be disjoint")
        if not set(sensitive).issubset(set(allowed) | set(inherited)):
            raise ValueError("sensitive_variables must be allowed or inherited")
        locale = _require_text(self.locale, "locale", max_length=128)
        encoding = _require_text(self.encoding, "encoding", max_length=128)
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "allowed_variables", allowed)
        object.__setattr__(self, "removed_variables", removed)
        object.__setattr__(self, "inherited_variables", inherited)
        object.__setattr__(self, "sensitive_variables", sensitive)
        object.__setattr__(self, "locale", locale)
        object.__setattr__(self, "encoding", encoding)


@dataclass(frozen=True, slots=True)
class ToolPathPolicy:
    readable_path_classes: tuple[str, ...]
    writable_path_classes: tuple[str, ...]
    reject_parent_traversal: bool = True
    reject_symlink_escape: bool = True

    def __post_init__(self) -> None:
        readable = _id_tuple(
            self.readable_path_classes,
            "readable_path_classes",
        )
        writable = _id_tuple(
            self.writable_path_classes,
            "writable_path_classes",
        )
        if not readable:
            raise ValueError("readable_path_classes must not be empty")
        for field_name in (
            "reject_parent_traversal",
            "reject_symlink_escape",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        object.__setattr__(self, "readable_path_classes", readable)
        object.__setattr__(self, "writable_path_classes", writable)


@dataclass(frozen=True, slots=True)
class ToolOutputLimits:
    stdout_bytes: int
    stderr_bytes: int
    generated_files_bytes: int
    total_retained_bytes: int
    maximum_generated_files: int = 128

    def __post_init__(self) -> None:
        for field_name in (
            "stdout_bytes",
            "stderr_bytes",
            "generated_files_bytes",
            "total_retained_bytes",
            "maximum_generated_files",
        ):
            _positive_int(getattr(self, field_name), field_name)
        if self.total_retained_bytes < max(
            self.stdout_bytes,
            self.stderr_bytes,
            self.generated_files_bytes,
        ):
            raise ValueError(
                "total_retained_bytes must not be less than an individual output limit"
            )

    @property
    def process_capture_limit_bytes(self) -> int:
        return self.stdout_bytes + self.stderr_bytes


@dataclass(frozen=True, slots=True)
class DiagnosticToolSpec:
    tool_id: ToolId | str
    catalog_version: str
    tool_version_policy: ToolVersionPolicy
    description: str
    purpose: str
    executable_resolution: ToolExecutableResolution
    input_contract: ToolInputContract
    allowed_flags: tuple[ToolFlagSpec, ...]
    working_directory_policy: ToolWorkingDirectoryPolicy
    environment_policy: ToolEnvironmentPolicy
    mutability: ToolMutability
    confirmation_policy: ToolConfirmationPolicy
    allowed_paths: ToolPathPolicy
    network_policy: ToolNetworkPolicy
    timeout_sec: float
    output_limits: ToolOutputLimits
    evidence_roles: tuple[ToolEvidenceRole, ...]
    normalization_profile: str
    parser_id: str
    ai_assisted: bool
    normative: bool
    availability_policy: ToolAvailabilityPolicy
    platforms: tuple[ToolPlatform, ...]
    approved_network_endpoints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        tool_id = validate_tool_id(self.tool_id)
        catalog_version = _version(self.catalog_version, "catalog_version")
        if not isinstance(self.tool_version_policy, ToolVersionPolicy):
            raise TypeError("tool_version_policy must be ToolVersionPolicy")
        description = _require_text(
            self.description,
            "description",
            max_length=2_000,
        )
        purpose = _require_text(self.purpose, "purpose", max_length=2_000)
        if not isinstance(
            self.executable_resolution,
            ToolExecutableResolution,
        ):
            raise TypeError("executable_resolution must be ToolExecutableResolution")
        if not isinstance(self.input_contract, ToolInputContract):
            raise TypeError("input_contract must be ToolInputContract")
        flags = _flag_specs(self.allowed_flags)
        if not isinstance(
            self.working_directory_policy,
            ToolWorkingDirectoryPolicy,
        ):
            raise TypeError("working_directory_policy must be ToolWorkingDirectoryPolicy")
        if not isinstance(self.environment_policy, ToolEnvironmentPolicy):
            raise TypeError("environment_policy must be ToolEnvironmentPolicy")
        if not isinstance(self.mutability, ToolMutability):
            raise TypeError("mutability must be ToolMutability")
        if not isinstance(
            self.confirmation_policy,
            ToolConfirmationPolicy,
        ):
            raise TypeError("confirmation_policy must be ToolConfirmationPolicy")
        if not isinstance(self.allowed_paths, ToolPathPolicy):
            raise TypeError("allowed_paths must be ToolPathPolicy")
        if not isinstance(self.network_policy, ToolNetworkPolicy):
            raise TypeError("network_policy must be ToolNetworkPolicy")
        timeout_sec = _positive_finite(self.timeout_sec, "timeout_sec")
        if not isinstance(self.output_limits, ToolOutputLimits):
            raise TypeError("output_limits must be ToolOutputLimits")
        roles = _enum_tuple(
            self.evidence_roles,
            ToolEvidenceRole,
            "evidence_roles",
        )
        if not roles:
            raise ValueError("evidence_roles must not be empty")
        normalization_profile = _portable_id(
            self.normalization_profile,
            "normalization_profile",
        )
        parser_id = _portable_id(self.parser_id, "parser_id")
        if type(self.ai_assisted) is not bool:
            raise TypeError("ai_assisted must be a boolean")
        if type(self.normative) is not bool:
            raise TypeError("normative must be a boolean")
        if not isinstance(
            self.availability_policy,
            ToolAvailabilityPolicy,
        ):
            raise TypeError("availability_policy must be ToolAvailabilityPolicy")
        platforms = _enum_tuple(
            self.platforms,
            ToolPlatform,
            "platforms",
        )
        if not platforms:
            raise ValueError("platforms must not be empty")
        endpoints = _text_tuple(
            self.approved_network_endpoints,
            "approved_network_endpoints",
            max_length=2_048,
        )
        _validate_tool_spec_policy(
            mutability=self.mutability,
            confirmation_policy=self.confirmation_policy,
            network_policy=self.network_policy,
            endpoints=endpoints,
            ai_assisted=self.ai_assisted,
            normative=self.normative,
            availability_policy=self.availability_policy,
            evidence_roles=roles,
        )
        object.__setattr__(self, "tool_id", tool_id)
        object.__setattr__(self, "catalog_version", catalog_version)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "purpose", purpose)
        object.__setattr__(self, "allowed_flags", flags)
        object.__setattr__(self, "timeout_sec", timeout_sec)
        object.__setattr__(self, "evidence_roles", roles)
        object.__setattr__(
            self,
            "normalization_profile",
            normalization_profile,
        )
        object.__setattr__(self, "parser_id", parser_id)
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(
            self,
            "approved_network_endpoints",
            endpoints,
        )

    @property
    def flag_specs_by_name(self) -> Mapping[str, ToolFlagSpec]:
        return MappingProxyType({flag.name: flag for flag in self.allowed_flags})

    @property
    def is_mutating(self) -> bool:
        return self.mutability in {
            ToolMutability.PROJECT_MUTATING,
            ToolMutability.EXTERNAL_MUTATING,
        }

    @property
    def is_executable_in_normal_validation(self) -> bool:
        return not self.is_mutating


@dataclass(frozen=True, slots=True)
class ToolConfirmationRecord:
    confirmation_id: str
    policy: ToolConfirmationPolicy
    confirmed_at: datetime
    confirmed_by: str
    operation_id: str
    accepted: bool = True

    def __post_init__(self) -> None:
        confirmation_id = _portable_id(
            self.confirmation_id,
            "confirmation_id",
        )
        if not isinstance(self.policy, ToolConfirmationPolicy):
            raise TypeError("policy must be ToolConfirmationPolicy")
        confirmed_at = _utc(self.confirmed_at, "confirmed_at")
        confirmed_by = _require_text(
            self.confirmed_by,
            "confirmed_by",
            max_length=512,
        )
        operation_id = _portable_id(self.operation_id, "operation_id")
        if type(self.accepted) is not bool:
            raise TypeError("accepted must be a boolean")
        if self.policy is ToolConfirmationPolicy.NONE:
            raise ValueError("confirmation records cannot use the none policy")
        object.__setattr__(self, "confirmation_id", confirmation_id)
        object.__setattr__(self, "confirmed_at", confirmed_at)
        object.__setattr__(self, "confirmed_by", confirmed_by)
        object.__setattr__(self, "operation_id", operation_id)


@dataclass(frozen=True, slots=True)
class DiagnosticToolRequest:
    tool_id: ToolId | str
    active_project_id: ProjectId | str
    run_id: RunId | str
    operation_id: str
    subject_ids: tuple[str, ...]
    resolved_inputs: tuple[Path, ...]
    selected_registered_flags: ToolFlagValues
    working_directory: Path
    timeout_sec: float
    output_limits: ToolOutputLimits
    stdout_path: Path
    stderr_path: Path
    output_directory: Path
    confirmation_record: ToolConfirmationRecord | None = None

    def __post_init__(self) -> None:
        tool_id = validate_tool_id(self.tool_id)
        project_id = validate_project_id(
            self.active_project_id,
            field="active_project_id",
        )
        run_id = validate_run_id(self.run_id, field="run_id")
        operation_id = _portable_id(self.operation_id, "operation_id")
        subjects = _text_tuple(
            self.subject_ids,
            "subject_ids",
            max_length=1_024,
        )
        inputs = _absolute_path_tuple(
            self.resolved_inputs,
            "resolved_inputs",
        )
        flags = _freeze_flag_values(self.selected_registered_flags)
        working_directory = _absolute_path(
            self.working_directory,
            "working_directory",
        )
        timeout_sec = _positive_finite(self.timeout_sec, "timeout_sec")
        if not isinstance(self.output_limits, ToolOutputLimits):
            raise TypeError("output_limits must be ToolOutputLimits")
        stdout_path = _absolute_path(self.stdout_path, "stdout_path")
        stderr_path = _absolute_path(self.stderr_path, "stderr_path")
        output_directory = _absolute_path(
            self.output_directory,
            "output_directory",
        )
        if stdout_path == stderr_path:
            raise ValueError("stdout_path and stderr_path must be distinct")
        if not _is_relative_to(stdout_path, output_directory):
            raise ValueError("stdout_path must be inside output_directory")
        if not _is_relative_to(stderr_path, output_directory):
            raise ValueError("stderr_path must be inside output_directory")
        if self.confirmation_record is not None and not isinstance(
            self.confirmation_record,
            ToolConfirmationRecord,
        ):
            raise TypeError("confirmation_record must be ToolConfirmationRecord or None")
        if (
            self.confirmation_record is not None
            and self.confirmation_record.operation_id != operation_id
        ):
            raise ValueError("confirmation_record operation_id does not match request")
        object.__setattr__(self, "tool_id", tool_id)
        object.__setattr__(self, "active_project_id", project_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(self, "subject_ids", subjects)
        object.__setattr__(self, "resolved_inputs", inputs)
        object.__setattr__(self, "selected_registered_flags", flags)
        object.__setattr__(self, "working_directory", working_directory)
        object.__setattr__(self, "timeout_sec", timeout_sec)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "output_directory", output_directory)


@dataclass(frozen=True, slots=True)
class ToolOutputArtifact:
    path: Path
    role: ToolEvidenceRole
    size_bytes: int
    media_type: str
    sha256: str | None = None
    current: bool = True

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, "path")
        if not isinstance(self.role, ToolEvidenceRole):
            raise TypeError("role must be ToolEvidenceRole")
        _non_negative_int(self.size_bytes, "size_bytes")
        media_type = _require_text(
            self.media_type,
            "media_type",
            max_length=256,
        )
        sha256 = self.sha256
        if sha256 is not None:
            sha256 = _require_text(sha256, "sha256", max_length=64)
            if _SHA256_RE.fullmatch(sha256) is None:
                raise ValueError("sha256 must be 64 lowercase hexadecimal digits")
        if type(self.current) is not bool:
            raise TypeError("current must be a boolean")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(self, "sha256", sha256)


@runtime_checkable
class ToolDiagnosticRecord(Protocol):
    message: str


@dataclass(frozen=True, slots=True)
class DiagnosticToolResult:
    tool_id: ToolId | str
    catalog_version: str
    resolved_tool_version: str | None
    status: ToolExecutionStatus
    result_kind: ToolResultKind
    execution_state: ExecutionState | None
    exit_code: int | None
    duration_ms: int
    command: tuple[str, ...]
    working_directory: Path
    stdout_path: Path | None
    stderr_path: Path | None
    output_artifacts: tuple[ToolOutputArtifact, ...]
    truncated: bool
    diagnostics: tuple[ToolDiagnosticRecord, ...]
    evidence_roles: tuple[ToolEvidenceRole, ...]
    ai_assisted: bool
    normative: bool
    warnings: tuple[str, ...] = ()
    error_message: str = ""

    def __post_init__(self) -> None:
        tool_id = validate_tool_id(self.tool_id)
        catalog_version = _version(self.catalog_version, "catalog_version")
        resolved_version = _optional_version(
            self.resolved_tool_version,
            "resolved_tool_version",
        )
        if not isinstance(self.status, ToolExecutionStatus):
            raise TypeError("status must be ToolExecutionStatus")
        if not isinstance(self.result_kind, ToolResultKind):
            raise TypeError("result_kind must be ToolResultKind")
        if self.execution_state is not None and not isinstance(
            self.execution_state,
            ExecutionState,
        ):
            raise TypeError("execution_state must be ExecutionState or None")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise TypeError("exit_code must be an integer or None")
        _non_negative_int(self.duration_ms, "duration_ms")
        command = _argument_tuple(self.command, "command")
        working_directory = _absolute_path(
            self.working_directory,
            "working_directory",
        )
        stdout_path = _optional_absolute_path(self.stdout_path, "stdout_path")
        stderr_path = _optional_absolute_path(self.stderr_path, "stderr_path")
        if stdout_path is not None and stdout_path == stderr_path:
            raise ValueError("stdout_path and stderr_path must be distinct")
        artifacts = _typed_tuple(
            self.output_artifacts,
            ToolOutputArtifact,
            "output_artifacts",
        )
        if type(self.truncated) is not bool:
            raise TypeError("truncated must be a boolean")
        diagnostics = tuple(self.diagnostics)
        if len(diagnostics) > _MAX_ITEMS:
            raise ValueError("diagnostics exceeds the supported item limit")
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, ToolDiagnosticRecord):
                raise TypeError("diagnostics must contain records exposing a string message field")
            _require_text(
                diagnostic.message,
                "diagnostic message",
                max_length=_MAX_TEXT,
            )
        roles = _enum_tuple(
            self.evidence_roles,
            ToolEvidenceRole,
            "evidence_roles",
        )
        if type(self.ai_assisted) is not bool:
            raise TypeError("ai_assisted must be a boolean")
        if type(self.normative) is not bool:
            raise TypeError("normative must be a boolean")
        warnings = _text_tuple(self.warnings, "warnings", max_length=_MAX_TEXT)
        if not isinstance(self.error_message, str) or "\x00" in self.error_message:
            raise ValueError("error_message must be a NUL-free string")
        if len(self.error_message) > _MAX_TEXT:
            raise ValueError("error_message exceeds the supported length")
        _validate_result_coherence(
            status=self.status,
            result_kind=self.result_kind,
            execution_state=self.execution_state,
            exit_code=self.exit_code,
            command=command,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            ai_assisted=self.ai_assisted,
            normative=self.normative,
            error_message=self.error_message,
        )
        object.__setattr__(self, "tool_id", tool_id)
        object.__setattr__(self, "catalog_version", catalog_version)
        object.__setattr__(self, "resolved_tool_version", resolved_version)
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "working_directory", working_directory)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "output_artifacts", artifacts)
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "evidence_roles", roles)
        object.__setattr__(self, "warnings", warnings)

    @property
    def completed_normally(self) -> bool:
        return self.execution_state is ExecutionState.COMPLETED

    @property
    def has_findings(self) -> bool:
        return bool(self.diagnostics)

    @property
    def may_affect_normative_validation(self) -> bool:
        return self.normative and not self.ai_assisted


ToolCatalogEntry = DiagnosticToolSpec
ToolRequest = DiagnosticToolRequest
ToolResult = DiagnosticToolResult


def validate_tool_id(value: object, *, field: str = "tool_id") -> ToolId:
    text = _require_text(value, field, max_length=128)
    if not text.isascii() or _TOOL_ID_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must use lowercase ASCII letters, digits, and hyphens")
    return ToolId(text)


def _validate_tool_spec_policy(
    *,
    mutability: ToolMutability,
    confirmation_policy: ToolConfirmationPolicy,
    network_policy: ToolNetworkPolicy,
    endpoints: tuple[str, ...],
    ai_assisted: bool,
    normative: bool,
    availability_policy: ToolAvailabilityPolicy,
    evidence_roles: tuple[ToolEvidenceRole, ...],
) -> None:
    if (
        mutability
        in {
            ToolMutability.PROJECT_MUTATING,
            ToolMutability.EXTERNAL_MUTATING,
        }
        and confirmation_policy is ToolConfirmationPolicy.NONE
    ):
        raise ValueError("mutating tools require an explicit confirmation policy")
    if (
        mutability in {ToolMutability.READ_ONLY, ToolMutability.RUN_ARTIFACTS_ONLY}
        and confirmation_policy is not ToolConfirmationPolicy.NONE
    ):
        raise ValueError("non-mutating tools must use the none confirmation policy")
    if network_policy is ToolNetworkPolicy.APPROVED_ENDPOINTS:
        if not endpoints:
            raise ValueError("approved_endpoints network policy requires endpoint entries")
    elif endpoints:
        raise ValueError(
            "approved_network_endpoints are permitted only with the "
            "approved_endpoints network policy"
        )
    if ai_assisted:
        if normative:
            raise ValueError("AI-assisted tools must be non-normative")
        if availability_policy is ToolAvailabilityPolicy.REQUIRED:
            raise ValueError("AI-assisted tools cannot be required")
        if ToolEvidenceRole.AI_ANNOTATION not in evidence_roles:
            raise ValueError("AI-assisted tools must declare the ai_annotation evidence role")


def _validate_result_coherence(
    *,
    status: ToolExecutionStatus,
    result_kind: ToolResultKind,
    execution_state: ExecutionState | None,
    exit_code: int | None,
    command: tuple[str, ...],
    stdout_path: Path | None,
    stderr_path: Path | None,
    ai_assisted: bool,
    normative: bool,
    error_message: str,
) -> None:
    if ai_assisted and normative:
        raise ValueError("AI-assisted results must be non-normative")
    if result_kind is ToolResultKind.UNAVAILABLE_OPTIONAL_TOOL:
        if status is not ToolExecutionStatus.SKIPPED or execution_state is not None:
            raise ValueError("unavailable optional tools must be skipped without execution")
    if result_kind is ToolResultKind.INVALID_REQUEST:
        if status is not ToolExecutionStatus.ERROR or execution_state is not None:
            raise ValueError("invalid requests must be errors without execution")
    if result_kind is ToolResultKind.LAUNCH_FAILURE:
        if execution_state is not ExecutionState.LAUNCH_FAILED:
            raise ValueError("launch failures require launch_failed execution state")
    if result_kind is ToolResultKind.TIMEOUT:
        if execution_state is not ExecutionState.TIMED_OUT:
            raise ValueError("timeouts require timed_out execution state")
    if result_kind is ToolResultKind.CANCELLATION:
        if execution_state is not ExecutionState.CANCELLED:
            raise ValueError("cancellations require cancelled execution state")
    if (
        execution_state
        in {
            ExecutionState.LAUNCH_FAILED,
            ExecutionState.TIMED_OUT,
            ExecutionState.CANCELLED,
        }
        and status is not ToolExecutionStatus.ERROR
    ):
        raise ValueError("launch failure, timeout, and cancellation require error status")
    if (
        status
        in {
            ToolExecutionStatus.COMPLETED,
            ToolExecutionStatus.FAILED,
        }
        and execution_state is not ExecutionState.COMPLETED
    ):
        raise ValueError("completed and failed tool statuses require completed execution")
    if status is ToolExecutionStatus.SKIPPED and execution_state is not None:
        raise ValueError("skipped tool status must not have execution state")
    if execution_state is ExecutionState.LAUNCH_FAILED and exit_code is not None:
        raise ValueError("launch failure must not have an exit code")
    if execution_state is not None and not command:
        raise ValueError("executed results require a command")
    if execution_state is not None and (stdout_path is None or stderr_path is None):
        raise ValueError("executed results require stdout and stderr paths")
    if status is ToolExecutionStatus.ERROR and not error_message:
        raise ValueError("error results require error_message")


def _flag_specs(values: Iterable[ToolFlagSpec]) -> tuple[ToolFlagSpec, ...]:
    result = _typed_tuple(values, ToolFlagSpec, "allowed_flags")
    names = [item.name for item in result]
    arguments = [item.argument for item in result]
    if len(names) != len(set(names)):
        raise ValueError("allowed_flags contains duplicate names")
    if len(arguments) != len(set(arguments)):
        raise ValueError("allowed_flags contains duplicate arguments")
    known = set(names)
    for spec in result:
        unknown = set(spec.mutually_exclusive_with).difference(known)
        if unknown:
            raise ValueError(
                f"flag {spec.name!r} references unknown exclusions: {', '.join(sorted(unknown))}"
            )
    return result


def _freeze_flag_values(values: ToolFlagValues) -> ToolFlagValues:
    if not values:
        return _EMPTY_FLAG_VALUES
    if not isinstance(values, Mapping):
        raise TypeError("selected_registered_flags must be a mapping")
    if len(values) > _MAX_ITEMS:
        raise ValueError("selected_registered_flags exceeds the item limit")
    copied: dict[str, ToolFlagValue] = {}
    for key, value in values.items():
        key = _portable_id(key, "selected_registered_flags key")
        if type(value) not in (str, int, float, bool, Path, tuple):
            raise TypeError(f"unsupported flag value type for {key!r}: {type(value).__name__}")
        if isinstance(value, str):
            value = _require_text(
                value,
                f"selected_registered_flags[{key!r}]",
                max_length=_MAX_TEXT,
                allow_empty=True,
            )
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"flag {key!r} must be finite")
        elif isinstance(value, Path):
            value = Path(value)
        elif isinstance(value, tuple):
            value = _text_tuple(
                value,
                f"selected_registered_flags[{key!r}]",
                max_length=_MAX_TEXT,
            )
        copied[key] = value
    return MappingProxyType(copied)


def _validate_flag_value(
    value: ToolFlagValue,
    value_type: ToolFlagType,
    choices: tuple[str, ...],
) -> None:
    valid = False
    if value_type is ToolFlagType.BOOLEAN:
        valid = type(value) is bool
    elif value_type is ToolFlagType.INTEGER:
        valid = type(value) is int
    elif value_type is ToolFlagType.NUMBER:
        valid = (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    elif value_type is ToolFlagType.STRING:
        valid = isinstance(value, str)
    elif value_type is ToolFlagType.CHOICE:
        valid = isinstance(value, str) and value in choices
    elif value_type is ToolFlagType.PATH:
        valid = isinstance(value, Path)
    elif value_type is ToolFlagType.STRING_LIST:
        valid = isinstance(value, tuple) and all(isinstance(item, str) for item in value)
    if not valid:
        raise TypeError(f"default value does not match flag type {value_type.value!r}")


def _freeze_platform_paths(
    values: Mapping[ToolPlatform, Iterable[Path]],
) -> Mapping[ToolPlatform, tuple[Path, ...]]:
    if not values:
        return MappingProxyType({})
    if not isinstance(values, Mapping):
        raise TypeError("platform_locations must be a mapping")
    copied: dict[ToolPlatform, tuple[Path, ...]] = {}
    for platform, paths in values.items():
        if not isinstance(platform, ToolPlatform):
            raise TypeError("platform_locations keys must be ToolPlatform")
        normalized = _absolute_path_tuple(
            paths,
            f"platform_locations[{platform.value!r}]",
        )
        if not normalized:
            raise ValueError(f"platform_locations[{platform.value!r}] must not be empty")
        copied[platform] = normalized
    return MappingProxyType(copied)


def _enum_tuple(
    values: Iterable[object],
    enum_type: type[_EnumT],
    field_name: str,
) -> tuple[_EnumT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable")
    result: list[_EnumT] = []
    for item in values:
        if not isinstance(item, enum_type):
            raise TypeError(f"{field_name} must contain {enum_type.__name__} values")
        result.append(item)
        if len(result) > _MAX_ITEMS:
            raise ValueError(f"{field_name} exceeds the supported item limit")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(result)


def _typed_tuple(
    values: Iterable[object],
    item_type: type[_ItemT],
    field_name: str,
) -> tuple[_ItemT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable")
    result: list[_ItemT] = []
    for item in values:
        if not isinstance(item, item_type):
            raise TypeError(f"{field_name} must contain {item_type.__name__} values")
        result.append(item)
        if len(result) > _MAX_ITEMS:
            raise ValueError(f"{field_name} exceeds the supported item limit")
    return tuple(result)


def _text_tuple(
    values: Iterable[str],
    field_name: str,
    *,
    max_length: int,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(
        _require_text(item, f"{field_name} item", max_length=max_length) for item in values
    )
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported item limit")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _id_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of identifiers")
    result = tuple(_portable_id(item, f"{field_name} item") for item in values)
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported item limit")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _file_type_tuple(values: Iterable[str]) -> tuple[str, ...]:
    result = _text_tuple(values, "file_types", max_length=128)
    for item in result:
        if not item.startswith(".") or "/" in item or "\\" in item:
            raise ValueError("file_types entries must be simple suffixes beginning with '.'")
    return result


def _environment_names(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = _text_tuple(values, field_name, max_length=256)
    for item in result:
        if "=" in item or not item.isascii():
            raise ValueError(f"{field_name} entries must be ASCII variable names")
    return result


def _version_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of versions")
    result = tuple(_version(item, f"{field_name} item") for item in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _argument_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = _text_tuple(
        values,
        field_name,
        max_length=_MAX_TEXT,
    )
    for item in result:
        if "\x00" in item:
            raise ValueError(f"{field_name} must not contain NUL")
    return result


def _absolute_path_tuple(
    values: Iterable[Path],
    field_name: str,
) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError(f"{field_name} must be an iterable of paths")
    result = tuple(_absolute_path(item, f"{field_name} item") for item in values)
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"{field_name} exceeds the supported item limit")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _absolute_path(value: object, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    path = Path(value)
    if "\x00" in str(path):
        raise ValueError(f"{field_name} must not contain NUL")
    if not path.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return path


def _optional_absolute_path(value: object, field_name: str) -> Path | None:
    if value is None:
        return None
    return _absolute_path(value, field_name)


def _portable_id(value: object, field_name: str) -> str:
    text = _require_text(value, field_name, max_length=256)
    if not text.isascii() or _PORTABLE_ID_RE.fullmatch(text) is None:
        raise ValueError(f"invalid {field_name}: {text!r}")
    return text


def _optional_portable_id(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _portable_id(value, field_name)


def _version(value: object, field_name: str) -> str:
    text = _require_text(value, field_name, max_length=128)
    if not text.isascii() or _VERSION_RE.fullmatch(text) is None:
        raise ValueError(f"invalid {field_name}: {text!r}")
    return text


def _optional_version(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _version(value, field_name)


def _require_text(
    value: object,
    field_name: str,
    *,
    max_length: int,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the supported length")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _positive_finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return result


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


__all__ = (
    "DiagnosticToolRequest",
    "DiagnosticToolResult",
    "DiagnosticToolSpec",
    "StringMap",
    "ToolAvailabilityPolicy",
    "ToolCatalogEntry",
    "ToolConfirmationPolicy",
    "ToolConfirmationRecord",
    "ToolDiagnosticRecord",
    "ToolEnvironmentPolicy",
    "ToolEvidenceRole",
    "ToolExecutableResolution",
    "ToolExecutableResolutionKind",
    "ToolExecutionStatus",
    "ToolFlagSpec",
    "ToolFlagType",
    "ToolFlagValue",
    "ToolFlagValues",
    "ToolId",
    "ToolInputContract",
    "ToolMutability",
    "ToolNetworkPolicy",
    "ToolOutputArtifact",
    "ToolOutputLimits",
    "ToolPathPolicy",
    "ToolPlatform",
    "ToolRequest",
    "ToolResult",
    "ToolResultKind",
    "ToolStdinPolicy",
    "ToolTemporaryFilePolicy",
    "ToolVersionPolicy",
    "ToolWorkingDirectoryPolicy",
    "UnparseableVersionPolicy",
    "validate_tool_id",
)
