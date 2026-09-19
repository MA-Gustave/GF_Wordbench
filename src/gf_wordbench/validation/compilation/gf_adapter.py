"""GF anti-corruption adapter backed by the shared process boundary."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol

from gf_wordbench.infrastructure.process import CancellationToken, run_process
from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessEventSink,
    ProcessInput,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.validation.ports import (
    GfArtifactKind,
    GfOperationKind,
    GfOperationRequest,
    GfOperationResult,
    GrammarInspectionKind,
    GrammarInspectionPayload,
    ModuleCompilePayload,
    PgfBuildPayload,
    ScenarioRunPayload,
    VersionProbePayload,
    validate_gf_operation_request,
)

from .commands import (
    GfCommand,
    GfCommandProfile,
    build_module_compile_command,
    build_pgf_command,
    build_version_probe_command,
)

__all__ = (
    "GfProcessAdapter",
    "execute_gf_operation",
)


class _ProcessRunner(Protocol):
    def __call__(
        self,
        request: ProcessRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult: ...


_EXPECTED_PROCESS_KIND: Final = MappingProxyType(
    {
        GfOperationKind.PROBE_VERSION: ProcessOperationKind.VERSION_PROBE,
        GfOperationKind.COMPILE_MODULE: ProcessOperationKind.COMPILE,
        GfOperationKind.BUILD_PGF: ProcessOperationKind.PGF_BUILD,
        GfOperationKind.RUN_SCENARIO: ProcessOperationKind.SCENARIO,
        GfOperationKind.INSPECT_GRAMMAR: ProcessOperationKind.INTROSPECTION,
    }
)

_GF_TOOL_ID: Final[str] = "gf"
_DENIED_NETWORK_POLICY: Final[str] = "denied"
_DEFAULT_PROFILE: Final = GfCommandProfile(
    profile_id="canonical",
    path_separator=os.pathsep,
)


@dataclass(frozen=True, slots=True)
class GfProcessAdapter:
    """Translate typed GF operations into generic process requests."""

    process_runner: _ProcessRunner = run_process

    def __post_init__(self) -> None:
        if not callable(self.process_runner):
            raise TypeError("process_runner must be callable")

    def execute(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        """Execute one complete GF operation request through the process runner."""

        process_request = self._validated_process_request(request)
        process_result = self.process_runner(
            process_request,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )
        self._validate_process_result(process_request, process_result)
        return GfOperationResult(
            operation_id=request.operation_id,
            operation_kind=request.operation_kind,
            process=process_result,
        )

    def probe_version(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        return self._execute_expected(
            request,
            GfOperationKind.PROBE_VERSION,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    def compile_module(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        return self._execute_expected(
            request,
            GfOperationKind.COMPILE_MODULE,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    def build_pgf(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        return self._execute_expected(
            request,
            GfOperationKind.BUILD_PGF,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    def run_scenario(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        return self._execute_expected(
            request,
            GfOperationKind.RUN_SCENARIO,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    def inspect_grammar(
        self,
        request: GfOperationRequest,
        *,
        cancellation_token: CancellationToken | None = None,
        event_sink: ProcessEventSink | None = None,
    ) -> GfOperationResult:
        return self._execute_expected(
            request,
            GfOperationKind.INSPECT_GRAMMAR,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    def _execute_expected(
        self,
        request: GfOperationRequest,
        expected_kind: GfOperationKind,
        *,
        cancellation_token: CancellationToken | None,
        event_sink: ProcessEventSink | None,
    ) -> GfOperationResult:
        validate_gf_operation_request(request, expected_kind)
        return self.execute(
            request,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    @staticmethod
    def _validated_process_request(request: GfOperationRequest) -> ProcessRequest:
        validate_gf_operation_request(request)
        try:
            process_kind = _EXPECTED_PROCESS_KIND[request.operation_kind]
        except KeyError as exc:
            raise ContractViolationError(
                f"unsupported GF operation kind: {request.operation_kind!r}"
            ) from exc

        command, stdin, metadata = _translate_operation(request)
        process_request = ProcessRequest(
            request_id=request.operation_id,
            tool_id=_GF_TOOL_ID,
            operation_id=request.operation_id,
            operation_kind=process_kind,
            executable=command.executable,
            args=command.arguments,
            cwd=command.working_directory,
            stdout_path=request.stdout_path,
            stderr_path=request.stderr_path,
            timeout_sec=request.timeout_sec,
            approved_read_roots=_approved_read_roots(request),
            approved_write_roots=_approved_write_roots(request),
            evidence_policy="retain-raw-streams-v1",
            stdin=stdin,
            env_overrides=request.environment_overrides,
            output_limit_bytes=request.output_limit_bytes,
            expected_artifacts=_artifact_expectations(request),
            metadata=metadata,
            mutability_class=(
                "read_only"
                if request.operation_kind
                in {GfOperationKind.PROBE_VERSION, GfOperationKind.INSPECT_GRAMMAR}
                else "run_artifacts_only"
            ),
            network_policy=_DENIED_NETWORK_POLICY,
        )
        return process_request

    @staticmethod
    def _validate_process_result(
        request: ProcessRequest,
        result: ProcessResult,
    ) -> None:
        if not isinstance(result, ProcessResult):
            raise TypeError("process_runner must return a ProcessResult")

        mismatches: list[str] = []
        if result.operation_id != request.operation_id:
            mismatches.append("operation_id")
        if result.operation_kind is not request.operation_kind:
            mismatches.append("operation_kind")
        if result.executable != request.executable:
            mismatches.append("executable")
        if result.args != request.args:
            mismatches.append("args")
        if result.cwd != request.cwd:
            mismatches.append("cwd")
        if result.stdout_path != request.stdout_path:
            mismatches.append("stdout_path")
        if result.stderr_path != request.stderr_path:
            mismatches.append("stderr_path")
        if result.environment_policy != request.environment_policy:
            mismatches.append("environment_policy")

        if mismatches:
            raise ContractViolationError(
                "process result does not correspond to its GF request: "
                + ", ".join(mismatches)
            )


def _translate_operation(
    request: GfOperationRequest,
) -> tuple[GfCommand, ProcessInput, dict[str, str]]:
    payload = request.payload
    metadata = {
        "gf_operation_kind": request.operation_kind.value,
        "project_id": str(request.project_id),
        "run_id": str(request.run_id),
    }

    if isinstance(payload, VersionProbePayload):
        return (
            build_version_probe_command(
                executable=request.executable,
                working_directory=request.working_directory,
            ),
            ProcessInput.none(),
            metadata,
        )

    if isinstance(payload, ModuleCompilePayload):
        command = build_module_compile_command(
            executable=request.executable,
            working_directory=request.working_directory,
            source_file=payload.source_path,
            gf_search_paths=request.gf_path,
            profile=_DEFAULT_PROFILE,
            gfo_dir=payload.output_directory,
            output_dir=payload.output_directory,
            quiet=False,
        )
        # GF_WORDBENCH_VERBOSE_DIAG_BEGIN
        # Diagnostic only: ask GF to print per-function PMCFG progress.
        command = GfCommand(
            operation=command.operation,
            executable=command.executable,
            arguments=("-v", *command.arguments),
            working_directory=command.working_directory,
            gf_search_paths=command.gf_search_paths,
            profile_id=command.profile_id,
        )
        # GF_WORDBENCH_VERBOSE_DIAG_END
        metadata["target_module"] = payload.module_name
        return command, ProcessInput.none(), metadata

    if isinstance(payload, PgfBuildPayload):
        command = build_pgf_command(
            executable=request.executable,
            working_directory=request.working_directory,
            entrypoints=payload.entrypoint_paths,
            gf_search_paths=request.gf_path,
            profile=_DEFAULT_PROFILE,
            output_dir=payload.output_path.parent,
        )
        metadata["grammar_name"] = payload.grammar_name
        return command, ProcessInput.none(), metadata

    if isinstance(payload, ScenarioRunPayload):
        script_text = payload.script_path.read_text(encoding="utf-8")
        if payload.input_path is not None:
            input_text = payload.input_path.read_text(encoding="utf-8")
            script_text = f"{script_text.rstrip()}\n{input_text}\n"
        elif payload.input_text is not None:
            script_text = f"{script_text.rstrip()}\n{payload.input_text}\n"
        metadata["scenario_id"] = str(payload.scenario_id)
        metadata["script_path"] = str(payload.script_path)
        return (
            GfCommand(
                operation="run_scenario",
                executable=request.executable,
                arguments=("-batch",),
                working_directory=request.working_directory,
                gf_search_paths=request.gf_path,
                profile_id=_DEFAULT_PROFILE.profile_id,
            ),
            ProcessInput.from_text(script_text),
            metadata,
        )

    if isinstance(payload, GrammarInspectionPayload):
        inspection_text = _inspection_script(payload)
        metadata["inspection_kind"] = payload.inspection_kind.value
        metadata["grammar_path"] = str(payload.grammar_path)
        return (
            GfCommand(
                operation="inspect_grammar",
                executable=request.executable,
                arguments=("-batch",),
                working_directory=request.working_directory,
                gf_search_paths=request.gf_path,
                profile_id=_DEFAULT_PROFILE.profile_id,
            ),
            ProcessInput.from_text(inspection_text),
            metadata,
        )

    raise ContractViolationError(f"unsupported GF payload: {type(payload).__name__}")


def _inspection_script(payload: GrammarInspectionPayload) -> str:
    subject = "" if payload.subject is None else f" {payload.subject}"
    commands = {
        GrammarInspectionKind.ABSTRACT_INFO: f"i {payload.grammar_path}",
        GrammarInspectionKind.CONCRETE_INFO: f"i {payload.grammar_path}",
        GrammarInspectionKind.MISSING_LINEARIZATIONS: f"ma {payload.grammar_path}",
        GrammarInspectionKind.PARSE: f"p{subject}",
        GrammarInspectionKind.LINEARIZE: f"l{subject}",
        GrammarInspectionKind.GENERATE_RANDOM: f"gr{subject}",
        GrammarInspectionKind.GENERATE_TREES: f"gt{subject}",
        GrammarInspectionKind.MORPHOLOGY: f"ma{subject}",
    }
    command = commands[payload.inspection_kind]
    if payload.input_text:
        command = f"{command} {payload.input_text}"
    if payload.maximum_results is not None:
        command = f"{command} -number={payload.maximum_results}"
    return f"import {payload.grammar_path}\n{command}\nq\n"


def _artifact_expectations(
    request: GfOperationRequest,
) -> tuple[ArtifactExpectation, ...]:
    return tuple(
        ArtifactExpectation(
            path=item.path,
            role=item.role,
            required=item.required,
            kind=(
                ArtifactKind.FILE
                if item.kind is GfArtifactKind.FILE
                else ArtifactKind.DIRECTORY
            ),
            minimum_size_bytes=1 if item.require_non_empty else 0,
        )
        for item in request.expected_artifacts
    )


def _approved_read_roots(request: GfOperationRequest) -> tuple[Path, ...]:
    payload = request.payload
    values: list[Path] = [
        request.working_directory,
        request.executable.parent,
        *request.gf_path,
    ]
    if isinstance(payload, ModuleCompilePayload):
        values.append(payload.source_path.parent)
    elif isinstance(payload, PgfBuildPayload):
        values.extend(path.parent for path in payload.entrypoint_paths)
    elif isinstance(payload, ScenarioRunPayload):
        values.append(payload.script_path.parent)
        if payload.input_path is not None:
            values.append(payload.input_path.parent)
    elif isinstance(payload, GrammarInspectionPayload):
        values.append(payload.grammar_path.parent)
    return _unique_roots(values)


def _approved_write_roots(request: GfOperationRequest) -> tuple[Path, ...]:
    values = [
        request.stdout_path.parent,
        request.stderr_path.parent,
        *(item.path.parent for item in request.expected_artifacts),
    ]
    payload = request.payload
    if isinstance(payload, ModuleCompilePayload):
        values.append(payload.output_directory)
    elif isinstance(payload, PgfBuildPayload):
        values.append(payload.output_path.parent)
    return _unique_roots(values)


def _unique_roots(values: Iterable[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for value in values:
        path = Path(value).resolve(strict=False)
        key = os.path.normcase(os.path.normpath(os.fspath(path)))
        if key not in seen:
            seen.add(key)
            result.append(path)
    return tuple(result)


def execute_gf_operation(
    request: GfOperationRequest,
    *,
    cancellation_token: CancellationToken | None = None,
    event_sink: ProcessEventSink | None = None,
    process_runner: _ProcessRunner = run_process,
) -> GfOperationResult:
    """Execute one GF request through an explicitly supplied process runner."""

    return GfProcessAdapter(process_runner=process_runner).execute(
        request,
        cancellation_token=cancellation_token,
        event_sink=event_sink,
    )
