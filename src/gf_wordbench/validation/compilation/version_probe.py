"""GF executable version probing and compatibility interpretation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum, unique
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, cast

from gf_wordbench.infrastructure.process import run_process
from gf_wordbench.infrastructure.process.models import (
    ProcessEventSink,
    ProcessInput,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.infrastructure.process.termination import (
    CancellationToken,
)
from gf_wordbench.kernel.statuses import ExecutionState

DEFAULT_VERSION_PROBE_TIMEOUT_SEC: Final[float] = 10.0
DEFAULT_VERSION_PROBE_OUTPUT_LIMIT_BYTES: Final[int] = 64 * 1024
DEFAULT_VERSION_ARGUMENTS: Final[tuple[str, ...]] = ("--version",)
DEFAULT_VERSION_REQUEST_ID: Final[str] = "gf-version"
DEFAULT_VERSION_OPERATION_ID: Final[str] = "version"
UNKNOWN_VERSION_TEXT: Final[str] = "UNKNOWN"

_VERSION_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?ix)"
    r"(?:\bGF\b|\bGrammatical\s+Framework\b)"
    r"(?:\s*(?:version|[-:]))?"
    r"\s*v?"
    r"(?P<version>[0-9]+(?:\.[0-9]+){1,3})"
    r"(?:[-+][0-9A-Za-z.-]+)?"
)
_FALLBACK_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<![0-9])"
    r"(?P<version>[0-9]+\.[0-9]+(?:\.[0-9]+){0,2})"
    r"(?![0-9])"
)
_EXACT_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^[vV]?"
    r"(?P<version>[0-9]+(?:\.[0-9]+){1,3})"
    r"(?:[-+][0-9A-Za-z.-]+)?$"
)

EnvironmentOverrides: TypeAlias = Mapping[str, str]
EvidenceReader: TypeAlias = Callable[[Path], bytes]


@unique
class GFVersionProbeOutcome(StrEnum):
    RECOGNIZED = "recognized"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    LAUNCH_FAILED = "launch_failed"
    UNSUPPORTED = "unsupported"


@unique
class GFVersionCompatibility(StrEnum):
    SUPPORTED = "supported"
    SUPPORTED_WITH_WARNING = "supported-with-warning"
    UNTESTED = "untested"
    UNSUPPORTED = "unsupported"
    KNOWN_INCOMPATIBLE = "known-incompatible"
    UNKNOWN = "unknown"
    NOT_EVALUATED = "not-evaluated"


@dataclass(frozen=True, slots=True)
class GFVersion:
    components: tuple[int, ...]
    normalized: str

    def __post_init__(self) -> None:
        components = _normalize_components(self.components)
        normalized = ".".join(str(component) for component in components)

        if self.normalized and self.normalized != normalized:
            raise ValueError("normalized must equal the canonical component rendering")

        object.__setattr__(self, "components", components)
        object.__setattr__(self, "normalized", normalized)

    @classmethod
    def parse(cls, value: str) -> GFVersion:
        text = _required_text(value, field_name="version")
        match = _EXACT_VERSION_RE.fullmatch(text)

        if match is None:
            raise ValueError(f"invalid GF version {text!r}; expected a dotted numeric version")

        components = tuple(int(component) for component in match.group("version").split("."))
        normalized_components = _normalize_components(components)
        return cls(
            components=normalized_components,
            normalized=".".join(str(component) for component in normalized_components),
        )

    def comparison_key(self, width: int = 4) -> tuple[int, ...]:
        if isinstance(width, bool) or not isinstance(width, int):
            raise TypeError("width must be an integer")
        if width < len(self.components):
            width = len(self.components)
        return self.components + (0,) * (width - len(self.components))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, GFVersion):
            return NotImplemented
        width = max(len(self.components), len(other.components))
        return self.comparison_key(width) < other.comparison_key(width)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, GFVersion):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, GFVersion):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, GFVersion):
            return NotImplemented
        return not self < other

    def __str__(self) -> str:
        return self.normalized


@dataclass(frozen=True, slots=True)
class GFVersionPolicy:
    minimum_supported_version: GFVersion | str | None = None
    project_minimum_version: GFVersion | str | None = None
    tested_versions: tuple[GFVersion | str, ...] = ()
    known_incompatible_versions: tuple[GFVersion | str, ...] = ()
    allow_untested_versions: bool = False
    strict_unknown: bool = True
    capabilities_by_version: Mapping[
        str,
        frozenset[str],
    ] = field(default_factory=dict)

    def __post_init__(self) -> None:
        minimum_supported_version = _optional_version(
            self.minimum_supported_version,
            field_name="minimum_supported_version",
        )
        project_minimum_version = _optional_version(
            self.project_minimum_version,
            field_name="project_minimum_version",
        )
        tested_versions = _version_tuple(
            self.tested_versions,
            field_name="tested_versions",
        )
        known_incompatible_versions = _version_tuple(
            self.known_incompatible_versions,
            field_name="known_incompatible_versions",
        )

        if not isinstance(self.allow_untested_versions, bool):
            raise TypeError("allow_untested_versions must be a bool")
        if not isinstance(self.strict_unknown, bool):
            raise TypeError("strict_unknown must be a bool")

        overlap = set(tested_versions).intersection(known_incompatible_versions)
        if overlap:
            rendered = ", ".join(sorted(version.normalized for version in overlap))
            raise ValueError(f"tested_versions and known_incompatible_versions overlap: {rendered}")

        capabilities = _normalize_capabilities(self.capabilities_by_version)

        object.__setattr__(
            self,
            "minimum_supported_version",
            minimum_supported_version,
        )
        object.__setattr__(
            self,
            "project_minimum_version",
            project_minimum_version,
        )
        object.__setattr__(
            self,
            "tested_versions",
            tested_versions,
        )
        object.__setattr__(
            self,
            "known_incompatible_versions",
            known_incompatible_versions,
        )
        object.__setattr__(
            self,
            "capabilities_by_version",
            capabilities,
        )

    @property
    def effective_minimum_version(self) -> GFVersion | None:
        minimum_supported = cast(
            GFVersion | None,
            self.minimum_supported_version,
        )
        project_minimum = cast(
            GFVersion | None,
            self.project_minimum_version,
        )
        candidates = tuple(
            version
            for version in (minimum_supported, project_minimum)
            if version is not None
        )
        if not candidates:
            return None
        return max(candidates)

    def capabilities_for(
        self,
        version: GFVersion | str,
    ) -> frozenset[str]:
        parsed = _coerce_version(version, field_name="version")
        return self.capabilities_by_version.get(
            parsed.normalized,
            frozenset(),
        )


@dataclass(frozen=True, slots=True)
class GFVersionText:
    display_text: str
    parsed_version: GFVersion | None
    source_stream: str | None
    recognized: bool

    def __post_init__(self) -> None:
        display_text = _required_text(
            self.display_text,
            field_name="display_text",
        )

        if self.parsed_version is not None and not isinstance(self.parsed_version, GFVersion):
            raise TypeError("parsed_version must be a GFVersion or None")

        source_stream = self.source_stream
        if source_stream not in {None, "stdout", "stderr"}:
            raise ValueError("source_stream must be stdout, stderr, or None")

        if not isinstance(self.recognized, bool):
            raise TypeError("recognized must be a bool")
        if self.recognized != (self.parsed_version is not None):
            raise ValueError("recognized must agree with parsed_version")
        if source_stream is None and display_text != UNKNOWN_VERSION_TEXT:
            raise ValueError("missing source_stream requires UNKNOWN display text")

        object.__setattr__(self, "display_text", display_text)


@dataclass(frozen=True, slots=True)
class GFVersionCompatibilityResult:
    compatibility: GFVersionCompatibility
    accepted: bool
    minimum_required: GFVersion | None
    capabilities: frozenset[str]
    warnings: tuple[str, ...] = ()
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(
            self.compatibility,
            GFVersionCompatibility,
        ):
            raise TypeError("compatibility must be a GFVersionCompatibility")
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be a bool")
        if self.minimum_required is not None and not isinstance(self.minimum_required, GFVersion):
            raise TypeError("minimum_required must be a GFVersion or None")

        capabilities = _string_frozenset(
            self.capabilities,
            field_name="capabilities",
        )
        warnings = _string_tuple(
            self.warnings,
            field_name="warnings",
        )
        message = _required_text(
            self.message,
            field_name="message",
        )

        if (
            self.compatibility
            in {
                GFVersionCompatibility.UNSUPPORTED,
                GFVersionCompatibility.KNOWN_INCOMPATIBLE,
                GFVersionCompatibility.UNKNOWN,
            }
            and self.accepted
        ):
            raise ValueError("unsupported or unknown compatibility cannot be accepted")

        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "message", message)


@dataclass(frozen=True, slots=True)
class GFVersionResult:
    outcome: GFVersionProbeOutcome
    executable: Path
    version_text: GFVersionText
    compatibility: GFVersionCompatibilityResult
    process_result: ProcessResult | None
    stdout_path: Path | None
    stderr_path: Path | None
    warnings: tuple[str, ...] = ()
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, GFVersionProbeOutcome):
            raise TypeError("outcome must be a GFVersionProbeOutcome")

        executable = _absolute_path(
            self.executable,
            field_name="executable",
        )

        if not isinstance(self.version_text, GFVersionText):
            raise TypeError("version_text must be a GFVersionText")
        if not isinstance(
            self.compatibility,
            GFVersionCompatibilityResult,
        ):
            raise TypeError("compatibility must be a GFVersionCompatibilityResult")
        if self.process_result is not None and not isinstance(self.process_result, ProcessResult):
            raise TypeError("process_result must be a ProcessResult or None")

        stdout_path = _optional_absolute_path(
            self.stdout_path,
            field_name="stdout_path",
        )
        stderr_path = _optional_absolute_path(
            self.stderr_path,
            field_name="stderr_path",
        )
        warnings = _string_tuple(
            self.warnings,
            field_name="warnings",
        )
        message = _required_text(
            self.message,
            field_name="message",
        )

        if self.process_result is not None:
            if self.process_result.executable != executable:
                raise ValueError("process_result executable must match executable")
            if stdout_path != self.process_result.stdout_path:
                raise ValueError("stdout_path must match process_result")
            if stderr_path != self.process_result.stderr_path:
                raise ValueError("stderr_path must match process_result")

        if self.outcome is GFVersionProbeOutcome.RECOGNIZED and not self.version_text.recognized:
            raise ValueError("recognized outcome requires a parsed version")
        if self.outcome is GFVersionProbeOutcome.SKIPPED and self.process_result is not None:
            raise ValueError("skipped outcome cannot contain process_result")

        object.__setattr__(self, "executable", executable)
        object.__setattr__(self, "stdout_path", stdout_path)
        object.__setattr__(self, "stderr_path", stderr_path)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "message", message)

    @property
    def parsed_version(self) -> GFVersion | None:
        return self.version_text.parsed_version

    @property
    def normalized_version(self) -> str | None:
        parsed = self.parsed_version
        return parsed.normalized if parsed is not None else None

    @property
    def raw_version_text(self) -> str:
        return self.version_text.display_text

    @property
    def accepted(self) -> bool:
        return self.compatibility.accepted

    @property
    def recognized(self) -> bool:
        return self.version_text.recognized


class ProcessExecutor(Protocol):
    def __call__(
        self,
        request: ProcessRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult: ...


def build_gf_version_probe_request(
    *,
    executable: Path,
    working_directory: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_sec: float = DEFAULT_VERSION_PROBE_TIMEOUT_SEC,
    version_arguments: Sequence[str] = DEFAULT_VERSION_ARGUMENTS,
    request_id: str = DEFAULT_VERSION_REQUEST_ID,
    operation_id: str = DEFAULT_VERSION_OPERATION_ID,
    approved_read_roots: Iterable[Path] = (),
    approved_write_roots: Iterable[Path] = (),
    environment_policy: str = "controlled-inherit-v1",
    env_overrides: EnvironmentOverrides | None = None,
    env_removals: Iterable[str] = (),
    sensitive_env_keys: Iterable[str] = (),
    output_limit_bytes: int = DEFAULT_VERSION_PROBE_OUTPUT_LIMIT_BYTES,
) -> ProcessRequest:
    executable = _absolute_path(
        executable,
        field_name="executable",
    )
    working_directory = _absolute_path(
        working_directory,
        field_name="working_directory",
    )
    stdout_path = _absolute_path(
        stdout_path,
        field_name="stdout_path",
    )
    stderr_path = _absolute_path(
        stderr_path,
        field_name="stderr_path",
    )

    if stdout_path == stderr_path:
        raise ValueError("stdout_path and stderr_path must be distinct")

    arguments = _argument_tuple(version_arguments)
    request_id = _required_text(
        request_id,
        field_name="request_id",
    )
    operation_id = _required_text(
        operation_id,
        field_name="operation_id",
    )
    environment_policy = _required_text(
        environment_policy,
        field_name="environment_policy",
    )
    timeout = _positive_finite_number(
        timeout_sec,
        field_name="timeout_sec",
    )
    output_limit = _positive_integer(
        output_limit_bytes,
        field_name="output_limit_bytes",
    )

    read_roots = _deduplicate_paths(
        (
            executable.parent,
            working_directory,
            *tuple(approved_read_roots),
        ),
        field_name="approved_read_roots",
    )
    write_roots = _deduplicate_paths(
        (
            stdout_path.parent,
            stderr_path.parent,
            *tuple(approved_write_roots),
        ),
        field_name="approved_write_roots",
    )

    return ProcessRequest(
        request_id=request_id,
        tool_id="gf",
        operation_id=operation_id,
        operation_kind=ProcessOperationKind.VERSION_PROBE,
        executable=executable,
        args=arguments,
        cwd=working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=timeout,
        approved_read_roots=read_roots,
        approved_write_roots=write_roots,
        evidence_policy="full-raw-v1",
        stdin=ProcessInput.none(),
        environment_policy=environment_policy,
        env_overrides=dict(env_overrides or {}),
        env_removals=frozenset(
            _string_tuple(
                env_removals,
                field_name="env_removals",
            )
        ),
        sensitive_env_keys=frozenset(
            _string_tuple(
                sensitive_env_keys,
                field_name="sensitive_env_keys",
            )
        ),
        termination_grace_sec=5.0,
        output_limit_bytes=output_limit,
        expected_artifacts=(),
        metadata={
            "probe_kind": "gf_version",
            "version_arguments": "\u001f".join(arguments),
        },
        mutability_class="read_only",
        network_policy="denied",
    )


def select_version_text(
    stdout_text: str,
    stderr_text: str,
) -> GFVersionText:
    stdout_line = _first_non_empty_line(
        stdout_text,
        field_name="stdout_text",
    )
    stderr_line = _first_non_empty_line(
        stderr_text,
        field_name="stderr_text",
    )

    if stdout_line is not None:
        display_text = stdout_line
        source_stream = "stdout"
    elif stderr_line is not None:
        display_text = stderr_line
        source_stream = "stderr"
    else:
        return GFVersionText(
            display_text=UNKNOWN_VERSION_TEXT,
            parsed_version=None,
            source_stream=None,
            recognized=False,
        )

    parsed_version = parse_gf_version_text(display_text)
    return GFVersionText(
        display_text=display_text,
        parsed_version=parsed_version,
        source_stream=source_stream,
        recognized=parsed_version is not None,
    )


def parse_gf_version_text(
    value: str,
) -> GFVersion | None:
    text = _required_text(
        value,
        field_name="version text",
    )

    match = _VERSION_LINE_RE.search(text)
    if match is None:
        match = _FALLBACK_VERSION_RE.search(text)
    if match is None:
        return None

    return GFVersion.parse(match.group("version"))


def evaluate_gf_version_compatibility(
    version: GFVersion | None,
    policy: GFVersionPolicy,
) -> GFVersionCompatibilityResult:
    if not isinstance(policy, GFVersionPolicy):
        raise TypeError("policy must be a GFVersionPolicy")

    minimum = policy.effective_minimum_version

    if version is None:
        accepted = not policy.strict_unknown
        compatibility = GFVersionCompatibility.UNKNOWN
        warning = "GF version output was not recognized."
        return GFVersionCompatibilityResult(
            compatibility=compatibility,
            accepted=accepted,
            minimum_required=minimum,
            capabilities=frozenset(),
            warnings=(warning,),
            message=(
                "GF version is unknown and compatibility is not proven."
                if not accepted
                else "GF version is unknown; non-strict policy permits continuation."
            ),
        )

    if version in policy.known_incompatible_versions:
        return GFVersionCompatibilityResult(
            compatibility=(GFVersionCompatibility.KNOWN_INCOMPATIBLE),
            accepted=False,
            minimum_required=minimum,
            capabilities=policy.capabilities_for(version),
            message=(f"GF {version} is explicitly known to be incompatible."),
        )

    if minimum is not None and version < minimum:
        return GFVersionCompatibilityResult(
            compatibility=GFVersionCompatibility.UNSUPPORTED,
            accepted=False,
            minimum_required=minimum,
            capabilities=policy.capabilities_for(version),
            message=(f"GF {version} is below the required minimum {minimum}."),
        )

    if version in policy.tested_versions:
        return GFVersionCompatibilityResult(
            compatibility=GFVersionCompatibility.SUPPORTED,
            accepted=True,
            minimum_required=minimum,
            capabilities=policy.capabilities_for(version),
            message=(f"GF {version} is a tested supported version."),
        )

    if policy.allow_untested_versions:
        warning = f"GF {version} satisfies the minimum version policy but is not listed as tested."
        return GFVersionCompatibilityResult(
            compatibility=(GFVersionCompatibility.SUPPORTED_WITH_WARNING),
            accepted=True,
            minimum_required=minimum,
            capabilities=policy.capabilities_for(version),
            warnings=(warning,),
            message=warning,
        )

    return GFVersionCompatibilityResult(
        compatibility=GFVersionCompatibility.UNTESTED,
        accepted=False,
        minimum_required=minimum,
        capabilities=policy.capabilities_for(version),
        warnings=(f"GF {version} is not listed in tested_versions.",),
        message=(f"GF {version} is recognized but its compatibility has not been verified."),
    )


def interpret_gf_version_probe(
    process_result: ProcessResult,
    *,
    policy: GFVersionPolicy,
    evidence_reader: EvidenceReader = Path.read_bytes,
) -> GFVersionResult:
    if not isinstance(process_result, ProcessResult):
        raise TypeError("process_result must be a ProcessResult")
    if process_result.operation_kind is not ProcessOperationKind.VERSION_PROBE:
        raise ValueError("process_result must describe a version probe")
    if not isinstance(policy, GFVersionPolicy):
        raise TypeError("policy must be a GFVersionPolicy")
    if not callable(evidence_reader):
        raise TypeError("evidence_reader must be callable")

    warnings: list[str] = []

    stdout_text = _read_evidence_text(
        process_result.stdout_path,
        evidence_reader=evidence_reader,
        stream_name="stdout",
        warnings=warnings,
    )
    stderr_text = _read_evidence_text(
        process_result.stderr_path,
        evidence_reader=evidence_reader,
        stream_name="stderr",
        warnings=warnings,
    )
    version_text = select_version_text(
        stdout_text,
        stderr_text,
    )

    state = process_result.execution_state

    if state is ExecutionState.LAUNCH_FAILED:
        compatibility = _not_evaluated(
            "GF compatibility was not evaluated because the executable did not launch."
        )
        message = process_result.launch_error_message or "Failed to launch the GF executable."
        return GFVersionResult(
            outcome=GFVersionProbeOutcome.LAUNCH_FAILED,
            executable=process_result.executable,
            version_text=version_text,
            compatibility=compatibility,
            process_result=process_result,
            stdout_path=process_result.stdout_path,
            stderr_path=process_result.stderr_path,
            warnings=tuple(warnings),
            message=message,
        )

    if state is ExecutionState.TIMED_OUT:
        compatibility = _not_evaluated(
            "GF compatibility was not evaluated because the version probe timed out."
        )
        return GFVersionResult(
            outcome=GFVersionProbeOutcome.TIMED_OUT,
            executable=process_result.executable,
            version_text=version_text,
            compatibility=compatibility,
            process_result=process_result,
            stdout_path=process_result.stdout_path,
            stderr_path=process_result.stderr_path,
            warnings=tuple(warnings),
            message=(f"GF version probe timed out after {process_result.duration_ms} ms."),
        )

    if state is ExecutionState.CANCELLED:
        warnings.append("GF version probe was cancelled.")
        compatibility = _not_evaluated(
            "GF compatibility was not evaluated because the version probe was cancelled."
        )
        return GFVersionResult(
            outcome=GFVersionProbeOutcome.UNKNOWN,
            executable=process_result.executable,
            version_text=version_text,
            compatibility=compatibility,
            process_result=process_result,
            stdout_path=process_result.stdout_path,
            stderr_path=process_result.stderr_path,
            warnings=tuple(warnings),
            message="GF version probe was cancelled.",
        )

    if state is not ExecutionState.COMPLETED:
        raise ValueError(f"unsupported process execution state: {state!r}")

    if process_result.exit_code != 0:
        warnings.append(
            f"GF version probe completed with non-zero exit code {process_result.exit_code}."
        )

    compatibility = evaluate_gf_version_compatibility(
        version_text.parsed_version,
        policy,
    )
    warnings.extend(compatibility.warnings)

    if not version_text.recognized:
        outcome = GFVersionProbeOutcome.UNKNOWN
    elif compatibility.compatibility in {
        GFVersionCompatibility.UNSUPPORTED,
        GFVersionCompatibility.KNOWN_INCOMPATIBLE,
    } or (
        compatibility.compatibility is GFVersionCompatibility.UNTESTED
        and not compatibility.accepted
    ):
        outcome = GFVersionProbeOutcome.UNSUPPORTED
    else:
        outcome = GFVersionProbeOutcome.RECOGNIZED

    if process_result.exit_code != 0:
        outcome = GFVersionProbeOutcome.UNKNOWN
        compatibility = GFVersionCompatibilityResult(
            compatibility=GFVersionCompatibility.UNKNOWN,
            accepted=False,
            minimum_required=policy.effective_minimum_version,
            capabilities=frozenset(),
            warnings=("A non-zero version-probe exit code prevents compatibility acceptance.",),
            message=("GF version probe did not satisfy the process success contract."),
        )
        warnings.extend(compatibility.warnings)

    return GFVersionResult(
        outcome=outcome,
        executable=process_result.executable,
        version_text=version_text,
        compatibility=compatibility,
        process_result=process_result,
        stdout_path=process_result.stdout_path,
        stderr_path=process_result.stderr_path,
        warnings=_deduplicate_strings(warnings),
        message=compatibility.message,
    )


def probe_gf_version(
    request: ProcessRequest,
    *,
    policy: GFVersionPolicy,
    executor: ProcessExecutor = run_process,
    evidence_reader: EvidenceReader = Path.read_bytes,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
) -> GFVersionResult:
    _validate_probe_request(request)

    if not isinstance(policy, GFVersionPolicy):
        raise TypeError("policy must be a GFVersionPolicy")
    if not callable(executor):
        raise TypeError("executor must be callable")
    if not callable(evidence_reader):
        raise TypeError("evidence_reader must be callable")

    process_result = executor(
        request,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
    )

    if process_result.executable != request.executable:
        raise ValueError("version probe used an executable different from the request")
    if process_result.args != request.args:
        raise ValueError("version probe result arguments differ from the request")
    if process_result.cwd != request.cwd:
        raise ValueError("version probe result working directory differs from the request")

    return interpret_gf_version_probe(
        process_result,
        policy=policy,
        evidence_reader=evidence_reader,
    )


def skipped_gf_version_result(
    *,
    executable: Path,
    reason: str,
) -> GFVersionResult:
    executable = _absolute_path(
        executable,
        field_name="executable",
    )
    reason = _required_text(reason, field_name="reason")

    return GFVersionResult(
        outcome=GFVersionProbeOutcome.SKIPPED,
        executable=executable,
        version_text=GFVersionText(
            display_text=UNKNOWN_VERSION_TEXT,
            parsed_version=None,
            source_stream=None,
            recognized=False,
        ),
        compatibility=_not_evaluated(
            "GF compatibility was not evaluated because version probing was skipped."
        ),
        process_result=None,
        stdout_path=None,
        stderr_path=None,
        warnings=(reason,),
        message=reason,
    )


def _validate_probe_request(
    request: ProcessRequest,
) -> None:
    if not isinstance(request, ProcessRequest):
        raise TypeError("request must be a ProcessRequest")
    if request.operation_kind is not ProcessOperationKind.VERSION_PROBE:
        raise ValueError("request.operation_kind must be VERSION_PROBE")
    if request.tool_id != "gf":
        raise ValueError("version probe tool_id must be 'gf'")
    if request.stdin != ProcessInput.none():
        raise ValueError("version probe stdin must be absent")
    if request.expected_artifacts:
        raise ValueError("version probe must not declare file artifacts")
    if request.mutability_class != "read_only":
        raise ValueError("version probe mutability_class must be read_only")
    if not request.args:
        raise ValueError("version probe must contain a version argument")


def _not_evaluated(
    message: str,
) -> GFVersionCompatibilityResult:
    return GFVersionCompatibilityResult(
        compatibility=GFVersionCompatibility.NOT_EVALUATED,
        accepted=False,
        minimum_required=None,
        capabilities=frozenset(),
        message=message,
    )


def _read_evidence_text(
    path: Path,
    *,
    evidence_reader: EvidenceReader,
    stream_name: str,
    warnings: list[str],
) -> str:
    try:
        payload = evidence_reader(path)
    except OSError as exc:
        warnings.append(f"Unable to read version-probe {stream_name}: {type(exc).__name__}: {exc}")
        return ""

    if not isinstance(payload, bytes):
        raise TypeError("evidence_reader must return bytes")

    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        warnings.append(
            f"Version-probe {stream_name} was not valid UTF-8; replacement decoding was applied."
        )
        return payload.decode("utf-8", errors="replace")


def _first_non_empty_line(
    value: str,
    *,
    field_name: str,
) -> str | None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    for line in value.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return None


def _normalize_components(
    values: Iterable[int],
) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("version components must be an iterable of integers")

    components = tuple(values)
    if len(components) < 2 or len(components) > 4:
        raise ValueError("GF versions must contain between two and four numeric components")

    for component in components:
        if isinstance(component, bool) or not isinstance(component, int):
            raise TypeError("version components must be integers")
        if component < 0:
            raise ValueError("version components must be non-negative")

    mutable = list(components)
    while len(mutable) > 2 and mutable[-1] == 0:
        mutable.pop()
    return tuple(mutable)


def _coerce_version(
    value: GFVersion | str,
    *,
    field_name: str,
) -> GFVersion:
    if isinstance(value, GFVersion):
        return value
    if isinstance(value, str):
        try:
            return GFVersion.parse(value)
        except ValueError as exc:
            raise ValueError(f"invalid {field_name}: {value!r}") from exc
    raise TypeError(f"{field_name} must be a GFVersion or string")


def _optional_version(
    value: GFVersion | str | None,
    *,
    field_name: str,
) -> GFVersion | None:
    if value is None or value == "":
        return None
    return _coerce_version(value, field_name=field_name)


def _version_tuple(
    values: Iterable[GFVersion | str],
    *,
    field_name: str,
) -> tuple[GFVersion, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of versions")

    parsed = tuple(_coerce_version(value, field_name=field_name) for value in values)
    return tuple(
        sorted(
            set(parsed),
            key=lambda version: version.comparison_key(),
        )
    )


def _normalize_capabilities(
    value: Mapping[str, Iterable[str]],
) -> Mapping[str, frozenset[str]]:
    if not isinstance(value, Mapping):
        raise TypeError("capabilities_by_version must be a mapping")

    normalized: dict[str, frozenset[str]] = {}

    for raw_version, raw_capabilities in value.items():
        version = _coerce_version(
            raw_version,
            field_name="capabilities_by_version key",
        )
        if version.normalized in normalized:
            raise ValueError(
                f"capabilities_by_version contains duplicate version {version.normalized}"
            )

        normalized[version.normalized] = _string_frozenset(
            raw_capabilities,
            field_name=(f"capabilities_by_version[{version.normalized!r}]"),
        )

    return MappingProxyType(dict(sorted(normalized.items())))


def _argument_tuple(
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("version_arguments must be a sequence of strings")

    arguments = tuple(values)
    if not arguments:
        raise ValueError("version_arguments must not be empty")

    for index, argument in enumerate(arguments):
        if not isinstance(argument, str):
            raise TypeError(f"version_arguments[{index}] must be a string")
        if not argument or "\x00" in argument:
            raise ValueError(f"version_arguments[{index}] must be non-empty and NUL-free")

    return arguments


def _deduplicate_paths(
    values: Iterable[Path],
    *,
    field_name: str,
) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()

    for value in values:
        path = _absolute_path(
            value,
            field_name=field_name,
        )
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)

    return tuple(result)


def _deduplicate_strings(
    values: Iterable[str],
) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = _required_text(
            value,
            field_name="warning",
        )
        if text in seen:
            continue
        seen.add(text)
        result.append(text)

    return tuple(result)


def _string_tuple(
    values: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")

    result = tuple(values)
    for value in result:
        _required_text(value, field_name=field_name)
    return result


def _string_frozenset(
    values: Iterable[str],
    *,
    field_name: str,
) -> frozenset[str]:
    return frozenset(_string_tuple(values, field_name=field_name))


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
    return value


def _absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return value


def _optional_absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path | None:
    if value is None:
        return None
    return _absolute_path(value, field_name=field_name)


def _positive_finite_number(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")

    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return normalized


def _positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


__all__ = (
    "DEFAULT_VERSION_ARGUMENTS",
    "DEFAULT_VERSION_OPERATION_ID",
    "DEFAULT_VERSION_PROBE_OUTPUT_LIMIT_BYTES",
    "DEFAULT_VERSION_PROBE_TIMEOUT_SEC",
    "DEFAULT_VERSION_REQUEST_ID",
    "UNKNOWN_VERSION_TEXT",
    "GFVersion",
    "GFVersionCompatibility",
    "GFVersionCompatibilityResult",
    "GFVersionPolicy",
    "GFVersionProbeOutcome",
    "GFVersionResult",
    "GFVersionText",
    "build_gf_version_probe_request",
    "evaluate_gf_version_compatibility",
    "interpret_gf_version_probe",
    "parse_gf_version_text",
    "probe_gf_version",
    "select_version_text",
    "skipped_gf_version_result",
)
