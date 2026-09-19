"""Deterministic execution of GF Wordbench release gates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
import re
from time import perf_counter_ns
from types import MappingProxyType
from typing import Final, Protocol, TypeVar, cast, runtime_checkable

from gf_wordbench.kernel.statuses import ValidationStatus

from .models import (
    ReleaseGateApplicability,
    ReleaseGateResult,
)

GateContextT = TypeVar("GateContextT")
GateContextT_contra = TypeVar("GateContextT_contra", contravariant=True)

_GATE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^RG-[0-9]{2}$")
_MAX_ERROR_TEXT: Final[int] = 500


@runtime_checkable
class ReleaseGate(Protocol[GateContextT_contra]):
    """Executable contract for one registered release gate."""

    gate_id: str
    name: str
    applicability: ReleaseGateApplicability
    dependencies: tuple[str, ...]

    def is_applicable(self, context: GateContextT_contra) -> bool:
        """Return whether a conditional gate is active for this release."""

    def evaluate(
        self,
        context: GateContextT_contra,
    ) -> ReleaseGateResult:
        """Evaluate the gate from already collected structured evidence."""


class ReleaseGateEvaluator:
    """Evaluate release gates in canonical registry order."""

    __slots__ = ()

    def evaluate(
        self,
        gates: Iterable[ReleaseGate[GateContextT]],
        context: GateContextT,
    ) -> tuple[ReleaseGateResult, ...]:
        ordered = _prepare_gates(gates)
        completed: dict[str, ReleaseGateResult] = {}

        for gate in ordered:
            result = self._evaluate_one(
                gate,
                context=context,
                completed=MappingProxyType(completed),
            )
            completed[gate.gate_id] = result

        return tuple(completed[gate.gate_id] for gate in ordered)

    def _evaluate_one(
        self,
        gate: ReleaseGate[GateContextT],
        *,
        context: GateContextT,
        completed: Mapping[str, ReleaseGateResult],
    ) -> ReleaseGateResult:
        started_ns = perf_counter_ns()

        try:
            active = _is_active(gate, context)
        except Exception as exc:
            return _with_duration(
                _error_result(
                    gate,
                    summary=(
                        "Release-gate applicability could not be evaluated: "
                        f"{_safe_exception_text(exc)}"
                    ),
                ),
                started_ns,
            )

        if not active:
            return _with_duration(
                _not_applicable_result(gate),
                started_ns,
            )

        blocked_by = tuple(
            dependency
            for dependency in gate.dependencies
            if completed[dependency].status is not ValidationStatus.OK
        )
        if blocked_by:
            return _with_duration(
                _blocked_result(gate, blocked_by),
                started_ns,
            )

        try:
            result = gate.evaluate(context)
            _validate_gate_result(gate, result)
        except Exception as exc:
            result = _error_result(
                gate,
                summary=(
                    f"Release gate could not be evaluated reliably: {_safe_exception_text(exc)}"
                ),
            )

        return _with_duration(result, started_ns)


def evaluate_release_gates(
    gates: Iterable[ReleaseGate[GateContextT]],
    context: GateContextT,
) -> tuple[ReleaseGateResult, ...]:
    """Evaluate registered release gates in their supplied canonical order."""

    return ReleaseGateEvaluator().evaluate(gates, context)


def _prepare_gates(
    gates: Iterable[object],
) -> tuple[ReleaseGate[GateContextT], ...]:
    if isinstance(gates, (str, bytes)):
        raise TypeError("gates must be an iterable of ReleaseGate objects")

    raw_gates = tuple(gates)
    if not raw_gates:
        raise ValueError("at least one release gate is required")

    ordered: list[ReleaseGate[GateContextT]] = []
    positions: dict[str, int] = {}
    for index, gate in enumerate(raw_gates):
        if not isinstance(gate, ReleaseGate):
            raise TypeError(f"gates[{index}] must satisfy ReleaseGate")
        ordered.append(cast(ReleaseGate[GateContextT], gate))
        _validate_gate_definition(gate)
        if gate.gate_id in positions:
            raise ValueError(f"duplicate release gate ID: {gate.gate_id!r}")
        positions[gate.gate_id] = index

    for index, gate in enumerate(ordered):
        seen_dependencies: set[str] = set()
        for dependency in gate.dependencies:
            if dependency in seen_dependencies:
                raise ValueError(f"release gate {gate.gate_id!r} repeats dependency {dependency!r}")
            seen_dependencies.add(dependency)

            dependency_position = positions.get(dependency)
            if dependency_position is None:
                raise ValueError(
                    f"release gate {gate.gate_id!r} depends on unknown gate {dependency!r}"
                )
            if dependency_position >= index:
                raise ValueError(
                    f"release gate {gate.gate_id!r} depends on {dependency!r}, "
                    "which must appear earlier in canonical gate order"
                )

    return tuple(ordered)


def _validate_gate_definition(gate: object) -> None:
    if not isinstance(gate, ReleaseGate):
        raise TypeError("every gate must satisfy the ReleaseGate protocol")

    _require_text(gate.gate_id, field="gate_id")
    if _GATE_ID_PATTERN.fullmatch(gate.gate_id) is None:
        raise ValueError(f"invalid release gate ID {gate.gate_id!r}; expected RG-NN")

    _require_text(gate.name, field=f"{gate.gate_id}.name")

    if not isinstance(gate.applicability, ReleaseGateApplicability):
        raise TypeError(f"{gate.gate_id}.applicability must be ReleaseGateApplicability")

    if not isinstance(gate.dependencies, tuple):
        raise TypeError(f"{gate.gate_id}.dependencies must be a tuple")
    for dependency in gate.dependencies:
        _require_text(
            dependency,
            field=f"{gate.gate_id}.dependencies item",
        )
        if _GATE_ID_PATTERN.fullmatch(dependency) is None:
            raise ValueError(f"invalid dependency ID {dependency!r} for {gate.gate_id}")
        if dependency == gate.gate_id:
            raise ValueError(f"release gate {gate.gate_id!r} cannot depend on itself")


def _is_active(
    gate: ReleaseGate[GateContextT],
    context: GateContextT,
) -> bool:
    applicability = gate.applicability

    if applicability is ReleaseGateApplicability.REQUIRED:
        return True
    if applicability is ReleaseGateApplicability.NOT_APPLICABLE:
        return False
    if applicability is ReleaseGateApplicability.CONDITIONAL:
        active = gate.is_applicable(context)
        if type(active) is not bool:
            raise TypeError(f"{gate.gate_id}.is_applicable() must return bool")
        return active

    raise ValueError(f"unsupported applicability for release gate {gate.gate_id!r}")


def _validate_gate_result(
    gate: ReleaseGate[GateContextT],
    result: object,
) -> None:
    if not isinstance(result, ReleaseGateResult):
        raise TypeError(f"{gate.gate_id}.evaluate() must return ReleaseGateResult")
    if result.gate_id != gate.gate_id:
        raise ValueError(
            f"gate result ID {result.gate_id!r} does not match registered gate {gate.gate_id!r}"
        )
    if result.name != gate.name:
        raise ValueError(f"gate result name for {gate.gate_id!r} does not match registry")
    if result.applicability is not gate.applicability:
        raise ValueError(
            f"gate result applicability for {gate.gate_id!r} does not match the registered policy"
        )
    if result.blocked_by:
        unknown = tuple(
            dependency for dependency in result.blocked_by if dependency not in gate.dependencies
        )
        if unknown:
            raise ValueError(
                f"gate result {gate.gate_id!r} contains undeclared blockers: {', '.join(unknown)}"
            )


def _not_applicable_result(
    gate: ReleaseGate[GateContextT],
) -> ReleaseGateResult:
    return ReleaseGateResult(
        gate_id=gate.gate_id,
        name=gate.name,
        applicability=ReleaseGateApplicability.NOT_APPLICABLE,
        status=ValidationStatus.SKIPPED,
        summary="Release gate is not applicable to the current release scope.",
        criteria_total=0,
        criteria_passed=0,
        blockers=(),
        warnings=(),
        evidence_paths=(),
        blocked_by=(),
        duration_ms=0,
    )


def _blocked_result(
    gate: ReleaseGate[GateContextT],
    blocked_by: tuple[str, ...],
) -> ReleaseGateResult:
    return ReleaseGateResult(
        gate_id=gate.gate_id,
        name=gate.name,
        applicability=gate.applicability,
        status=ValidationStatus.SKIPPED,
        summary=(
            "Release gate was not executed because prerequisite gates did "
            "not complete successfully."
        ),
        criteria_total=0,
        criteria_passed=0,
        blockers=(),
        warnings=(),
        evidence_paths=(),
        blocked_by=blocked_by,
        duration_ms=0,
    )


def _error_result(
    gate: ReleaseGate[GateContextT],
    *,
    summary: str,
) -> ReleaseGateResult:
    return ReleaseGateResult(
        gate_id=gate.gate_id,
        name=gate.name,
        applicability=gate.applicability,
        status=ValidationStatus.ERROR,
        summary=summary,
        criteria_total=0,
        criteria_passed=0,
        blockers=(summary,),
        warnings=(),
        evidence_paths=(),
        blocked_by=(),
        duration_ms=0,
    )


def _with_duration(
    result: ReleaseGateResult,
    started_ns: int,
) -> ReleaseGateResult:
    elapsed_ns = max(0, perf_counter_ns() - started_ns)
    duration_ms = elapsed_ns // 1_000_000
    return replace(result, duration_ms=duration_ms)


def _safe_exception_text(exc: Exception) -> str:
    message = " ".join(str(exc).replace("\x00", "").split())
    if not message:
        message = "no safe diagnostic message was provided"
    if len(message) > _MAX_ERROR_TEXT:
        message = f"{message[: _MAX_ERROR_TEXT - 3]}..."
    return f"{type(exc).__name__}: {message}"


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL characters")
    return value


__all__ = (
    "ReleaseGate",
    "ReleaseGateEvaluator",
    "evaluate_release_gates",
)
