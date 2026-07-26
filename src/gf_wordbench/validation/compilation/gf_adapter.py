"""GF anti-corruption adapter backed by the shared process boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Protocol

from gf_wordbench.infrastructure.process import CancellationToken, run_process
from gf_wordbench.infrastructure.process.models import (
    ProcessEventSink,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.errors import ContractViolationError

from .models import GfOperationKind, GfOperationRequest, GfOperationResult

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

_ALLOWED_MUTABILITY: Final[frozenset[str]] = frozenset(
    {
        "read_only",
        "run_artifacts_only",
    }
)

_GF_TOOL_ID: Final[str] = "gf"
_DENIED_NETWORK_POLICY: Final[str] = "denied"


@dataclass(frozen=True, slots=True)
class GfProcessAdapter:
    """Execute validated GF operations without rebuilding their commands."""

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
            request=request,
            process_result=process_result,
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
        if not isinstance(request, GfOperationRequest):
            raise TypeError("request must be a GfOperationRequest")
        if request.operation_kind is not expected_kind:
            raise ContractViolationError(
                f"GF operation method {expected_kind.value!r} received "
                f"request kind {request.operation_kind.value!r}"
            )
        return self.execute(
            request,
            cancellation_token=cancellation_token,
            event_sink=event_sink,
        )

    @staticmethod
    def _validated_process_request(
        request: GfOperationRequest,
    ) -> ProcessRequest:
        if not isinstance(request, GfOperationRequest):
            raise TypeError("request must be a GfOperationRequest")
        if not isinstance(request.operation_kind, GfOperationKind):
            raise TypeError("request.operation_kind must be a GfOperationKind")

        try:
            expected_process_kind = _EXPECTED_PROCESS_KIND[request.operation_kind]
        except KeyError as exc:
            raise ContractViolationError(
                f"unsupported GF operation kind: {request.operation_kind!r}"
            ) from exc

        process_request = request.process_request
        if not isinstance(process_request, ProcessRequest):
            raise TypeError("request.process_request must be a ProcessRequest")
        if process_request.request_id != request.request_id:
            raise ContractViolationError(
                "GF and process request identifiers must match"
            )
        if process_request.tool_id != _GF_TOOL_ID:
            raise ContractViolationError(
                f"GF process request tool_id must be {_GF_TOOL_ID!r}"
            )
        if process_request.operation_kind is not expected_process_kind:
            raise ContractViolationError(
                "GF operation kind does not match the process operation kind"
            )
        if process_request.network_policy != _DENIED_NETWORK_POLICY:
            raise ContractViolationError(
                "GF process requests must use the denied network policy"
            )
        if process_request.mutability_class not in _ALLOWED_MUTABILITY:
            raise ContractViolationError(
                "GF process mutability must be read_only or run_artifacts_only"
            )

        metadata_kind = process_request.metadata.get("gf_operation_kind")
        if metadata_kind is not None and metadata_kind != request.operation_kind.value:
            raise ContractViolationError(
                "GF operation metadata disagrees with the typed operation kind"
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
            joined = ", ".join(mismatches)
            raise ContractViolationError(
                "process result does not correspond to its GF request: " + joined
            )


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
