from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Protocol, TypeVar, cast

from gf_wordbench.kernel.errors import ScenarioExecutionError
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

if TYPE_CHECKING:
    from gf_wordbench.config.models import RunConfig
    from gf_wordbench.infrastructure.process.termination import (
        CancellationToken,
    )
    from gf_wordbench.runs.models.paths import RunPaths

    from .models import ScenarioResult, ScenarioSpec

_MAX_BATCH_SIZE: Final[int] = 10_000
_T = TypeVar("_T")


class _ExecutionEvidence(Protocol):
    command: Sequence[str]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    timed_out: bool
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    stdout_text: str
    stderr_text: str


class _MarkerSection(Protocol):
    section_id: object
    text: str
    source_evidence: str


class _MarkerEvaluation(Protocol):
    complete: bool
    sections: Sequence[_MarkerSection]
    message: str


class _AssertionEvaluation(Protocol):
    passed: bool
    evaluated: bool
    message: str


class _GoldEvaluation(Protocol):
    match: bool | None
    gold_path: Path | None
    message: str
    diff_path: Path | None


class _ArtifactEvaluation(Protocol):
    records: Sequence[object]
    missing_required: Sequence[object]
    message: str
    error: bool


class _NormalizationRegistry(Protocol):
    def require(self, profile_id: str, profile_version: str) -> object: ...


@dataclass(frozen=True, slots=True)
class ScenarioStageFunctions:
    execute: Callable[..., object]
    evaluate_markers: Callable[..., object]
    evaluate_assertions: Callable[..., object]
    compare_gold: Callable[..., object]
    verify_artifacts: Callable[..., object]
    write_normalized_output: Callable[..., Path | None]

    def __post_init__(self) -> None:
        for field_name in (
            "execute",
            "evaluate_markers",
            "evaluate_assertions",
            "compare_gold",
            "verify_artifacts",
            "write_normalized_output",
        ):
            if not callable(getattr(self, field_name)):
                raise TypeError(f"{field_name} must be callable")


@dataclass(frozen=True, slots=True)
class _ScenarioInterpretation:
    status: ValidationStatus
    diagnostic_class: DiagnosticClass
    error_kind: ErrorKind
    primary_message: str


def run_scenario(
    spec: ScenarioSpec,
    run_config: RunConfig,
    run_paths: RunPaths,
    *,
    cancellation_token: CancellationToken | None = None,
) -> ScenarioResult:
    _validate_inputs(
        spec=spec,
        run_config=run_config,
        run_paths=run_paths,
        cancellation_token=cancellation_token,
    )
    stages = _load_stage_functions()
    models = _load_models_module()
    normalization = _load_normalization_module()

    execution = cast(
        "_ExecutionEvidence",
        stages.execute(
            spec,
            run_config,
            run_paths,
            cancellation_token=cancellation_token,
        ),
    )
    _validate_execution_evidence(execution, run_paths=run_paths)

    marker_evaluation = cast(
        "_MarkerEvaluation",
        stages.evaluate_markers(
            spec,
            execution.stdout_text,
        ),
    )
    _validate_marker_evaluation(marker_evaluation)

    normalized_sections: tuple[object, ...] = ()
    normalized_output_path: Path | None = None
    normalization_error: str | None = None

    if execution.execution_state is ExecutionState.COMPLETED and marker_evaluation.complete:
        try:
            registry = _normalization_registry(
                run_config,
                normalization,
            )
            profile_id = _required_attribute(
                spec,
                "normalization_profile_id",
                fallback="scenario-default",
            )
            profile_version = _required_attribute(
                spec,
                "normalization_version",
                fallback="1.0.0",
            )
            profile = registry.require(
                profile_id,
                profile_version,
            )
            extracted_sections = tuple(
                normalization.ExtractedScenarioSection(
                    section_id=section.section_id,
                    text=section.text,
                    source_evidence=section.source_evidence,
                )
                for section in marker_evaluation.sections
            )
            normalized_sections = tuple(
                normalization.normalize_scenario_sections(
                    extracted_sections,
                    profile=profile,
                )
            )
            normalized_output_path = stages.write_normalized_output(
                spec,
                normalized_sections,
                run_paths,
            )
            if normalized_output_path is not None:
                normalized_output_path = run_paths.require_owned_path(
                    normalized_output_path,
                    role="normalized scenario output",
                )
        except Exception as exc:
            if _is_contract_exception(exc):
                raise
            normalization_error = _bounded_message(f"Scenario output normalization failed: {exc}")

    assertion_evaluations: tuple[_AssertionEvaluation, ...] = ()
    assertion_error: str | None = None

    if (
        execution.execution_state is ExecutionState.COMPLETED
        and marker_evaluation.complete
        and normalization_error is None
    ):
        try:
            produced_assertions = stages.evaluate_assertions(
                spec,
                normalized_sections,
                run_paths=run_paths,
            )
            assertion_evaluations = tuple(cast("Iterable[_AssertionEvaluation]", produced_assertions))
            _validate_assertion_evaluations(assertion_evaluations)
        except Exception as exc:
            if _is_contract_exception(exc):
                raise
            assertion_error = _bounded_message(f"Scenario assertions could not be evaluated: {exc}")

    gold_evaluation: _GoldEvaluation | None = None
    gold_error: str | None = None

    if (
        execution.execution_state is ExecutionState.COMPLETED
        and marker_evaluation.complete
        and normalization_error is None
        and assertion_error is None
    ):
        try:
            gold_evaluation = cast(
                "_GoldEvaluation",
                stages.compare_gold(
                    spec,
                    normalized_sections,
                    run_paths=run_paths,
                ),
            )
            _validate_gold_evaluation(
                gold_evaluation,
                run_paths=run_paths,
            )
        except Exception as exc:
            if _is_contract_exception(exc):
                raise
            gold_error = _bounded_message(f"Scenario gold comparison failed: {exc}")

    artifact_evaluation: _ArtifactEvaluation | None = None
    artifact_error: str | None = None

    try:
        artifact_evaluation = cast(
            "_ArtifactEvaluation",
            stages.verify_artifacts(
                spec,
                execution,
                run_paths=run_paths,
            ),
        )
        _validate_artifact_evaluation(artifact_evaluation)
    except Exception as exc:
        if _is_contract_exception(exc):
            raise
        artifact_error = _bounded_message(f"Scenario artifact verification failed: {exc}")

    interpretation = _interpret_scenario(
        spec=spec,
        execution=execution,
        markers=marker_evaluation,
        assertions=assertion_evaluations,
        gold=gold_evaluation,
        artifacts=artifact_evaluation,
        normalization_error=normalization_error,
        assertion_error=assertion_error,
        gold_error=gold_error,
        artifact_error=artifact_error,
    )

    section_results = _build_section_results(
        models=models,
        marker_sections=marker_evaluation.sections,
        normalized_sections=normalized_sections,
    )
    result_values = {
        "scenario_id": _required_attribute(spec, "scenario_id"),
        "script_path": Path(_required_attribute(spec, "script_path")),
        "script_sha256": _required_attribute(
            execution,
            "script_sha256",
            fallback=_required_attribute(spec, "script_sha256", fallback=""),
        ),
        "required": bool(_required_attribute(spec, "required")),
        "status": interpretation.status,
        "diagnostic_class": interpretation.diagnostic_class,
        "error_kind": interpretation.error_kind,
        "primary_message": interpretation.primary_message,
        "blocked_by": tuple(_optional_sequence(spec, "blocked_by")),
        "command": tuple(execution.command),
        "working_directory": execution.working_directory,
        "exit_code": execution.exit_code,
        "execution_state": execution.execution_state,
        "cancelled": bool(
            getattr(execution, "cancelled", False)
            or execution.execution_state is ExecutionState.CANCELLED
        ),
        "timed_out": execution.timed_out,
        "duration_ms": execution.duration_ms,
        "stdout_path": (
            run_paths.relative_path(execution.stdout_path, role="stdout path")
            if execution.stdout_path is not None
            else None
        ),
        "stderr_path": (
            run_paths.relative_path(execution.stderr_path, role="stderr path")
            if execution.stderr_path is not None
            else None
        ),
        "stdout_relative_path": (
            run_paths.relative_path(execution.stdout_path, role="stdout path")
            if execution.stdout_path is not None
            else None
        ),
        "stderr_relative_path": (
            run_paths.relative_path(execution.stderr_path, role="stderr path")
            if execution.stderr_path is not None
            else None
        ),
        "normalized_output_path": normalized_output_path,
        "gold_path": (
            gold_evaluation.gold_path
            if gold_evaluation is not None
            else _optional_path(spec, "gold_path")
        ),
        "gold_match": (gold_evaluation.match if gold_evaluation is not None else None),
        "sections": section_results,
        "assertions": assertion_evaluations,
        "artifacts": (
            tuple(artifact_evaluation.records) if artifact_evaluation is not None else ()
        ),
        "gold_diff_path": (gold_evaluation.diff_path if gold_evaluation is not None else None),
        "normalization_profile_id": _required_attribute(
            spec,
            "normalization_profile_id",
            fallback="scenario-default",
        ),
        "normalization_version": _required_attribute(
            spec,
            "normalization_version",
            fallback="1.0.0",
        ),
    }

    try:
        result = _construct_model(
            models.ScenarioResult,
            result_values,
            required_fields=(
                "scenario_id",
                "script_path",
                "script_sha256",
                "required",
                "status",
                "diagnostic_class",
                "error_kind",
                "primary_message",
                "blocked_by",
                "command",
                "working_directory",
                "exit_code",
                "execution_state",
                "cancelled",
                "timed_out",
                "duration_ms",
                "stdout_path",
                "stderr_path",
                "normalized_output_path",
                "gold_path",
                "gold_match",
                "sections",
                "artifacts",
            ),
        )
    except Exception as exc:
        raise ScenarioExecutionError(
            "Scenario evidence was preserved but a valid ScenarioResult could not be constructed.",
            subject=str(_required_attribute(spec, "scenario_id")),
            evidence_paths=tuple(
                str(path)
                for path in (
                    execution.stdout_path,
                    execution.stderr_path,
                    normalized_output_path,
                )
                if path is not None
            ),
        ) from exc

    return cast("ScenarioResult", result)


def run_scenarios(
    spec: Sequence[ScenarioSpec],
    run_config: RunConfig,
    run_paths: RunPaths,
    *,
    cancellation_token: CancellationToken | None = None,
) -> list[ScenarioResult]:
    raw_specs: object = spec
    if isinstance(raw_specs, (str, bytes)):
        raise TypeError("specs must be a sequence of ScenarioSpec values")
    if len(spec) > _MAX_BATCH_SIZE:
        raise ValueError(f"specs exceed the maximum batch size of {_MAX_BATCH_SIZE}")

    normalized = tuple(spec)
    scenario_ids: list[str] = []

    for position, scenario_spec in enumerate(normalized):
        scenario_id = _required_attribute(
            scenario_spec,
            "scenario_id",
        )
        if not isinstance(scenario_id, str):
            raise TypeError(f"specs[{position}].scenario_id must be a string")
        if scenario_id in scenario_ids:
            raise ValueError(f"duplicate scenario ID {scenario_id!r}")
        scenario_ids.append(scenario_id)

    results: list[ScenarioResult] = []
    for scenario_spec in normalized:
        results.append(
            run_scenario(
                scenario_spec,
                run_config,
                run_paths,
                cancellation_token=cancellation_token,
            )
        )
    return results


def _interpret_scenario(
    *,
    spec: object,
    execution: _ExecutionEvidence,
    markers: _MarkerEvaluation,
    assertions: Sequence[_AssertionEvaluation],
    gold: _GoldEvaluation | None,
    artifacts: _ArtifactEvaluation | None,
    normalization_error: str | None,
    assertion_error: str | None,
    gold_error: str | None,
    artifact_error: str | None,
) -> _ScenarioInterpretation:
    if execution.execution_state is ExecutionState.TIMED_OUT:
        return _ScenarioInterpretation(
            status=ValidationStatus.ERROR,
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
            error_kind=ErrorKind.TIMEOUT,
            primary_message=_execution_message(
                execution,
                "Process timed out.",
            ),
        )

    if execution.execution_state is ExecutionState.CANCELLED:
        return _ScenarioInterpretation(
            status=ValidationStatus.ERROR,
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
            error_kind=ErrorKind.OTHER,
            primary_message=_execution_message(
                execution,
                "Execution was cancelled.",
            ),
        )

    if execution.execution_state is ExecutionState.LAUNCH_FAILED:
        return _ScenarioInterpretation(
            status=ValidationStatus.ERROR,
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
            error_kind=_execution_error_kind(
                execution,
                fallback=ErrorKind.TOOL,
            ),
            primary_message=_execution_message(
                execution,
                "Failed to launch GF executable.",
            ),
        )

    if not markers.complete:
        return _ScenarioInterpretation(
            status=ValidationStatus.FAIL,
            diagnostic_class=DiagnosticClass.DIRECT,
            error_kind=ErrorKind.SCRIPT,
            primary_message=_bounded_message(
                markers.message or "Required scenario markers are incomplete."
            ),
        )

    for message in (
        normalization_error,
        assertion_error,
        gold_error,
        artifact_error,
    ):
        if message is not None:
            error_kind = ErrorKind.IO if message is artifact_error else ErrorKind.OTHER
            return _ScenarioInterpretation(
                status=ValidationStatus.ERROR,
                diagnostic_class=DiagnosticClass.AMBIGUOUS,
                error_kind=error_kind,
                primary_message=message,
            )

    if not _exit_code_accepted(spec, execution.exit_code):
        return _ScenarioInterpretation(
            status=ValidationStatus.FAIL,
            diagnostic_class=DiagnosticClass.DIRECT,
            error_kind=_execution_error_kind(
                execution,
                fallback=ErrorKind.SCRIPT,
            ),
            primary_message=_execution_message(
                execution,
                ("GF exited with a non-zero status; no accepted scenario outcome was established."),
            ),
        )

    for assertion in assertions:
        if not assertion.evaluated:
            return _ScenarioInterpretation(
                status=ValidationStatus.ERROR,
                diagnostic_class=DiagnosticClass.AMBIGUOUS,
                error_kind=ErrorKind.SCRIPT,
                primary_message=_bounded_message(
                    assertion.message or "A required assertion could not be evaluated."
                ),
            )
        if not assertion.passed:
            return _ScenarioInterpretation(
                status=ValidationStatus.FAIL,
                diagnostic_class=DiagnosticClass.DIRECT,
                error_kind=ErrorKind.SCRIPT,
                primary_message=_bounded_message(
                    assertion.message or "A required scenario assertion failed."
                ),
            )

    if gold is not None and gold.match is False:
        return _ScenarioInterpretation(
            status=ValidationStatus.FAIL,
            diagnostic_class=DiagnosticClass.DIRECT,
            error_kind=ErrorKind.SCRIPT,
            primary_message=_bounded_message(
                gold.message or "Normalized scenario output does not match gold."
            ),
        )

    if artifacts is not None:
        if artifacts.error:
            return _ScenarioInterpretation(
                status=ValidationStatus.ERROR,
                diagnostic_class=DiagnosticClass.AMBIGUOUS,
                error_kind=ErrorKind.IO,
                primary_message=_bounded_message(
                    artifacts.message or "Scenario artifact evidence is unreliable."
                ),
            )
        if artifacts.missing_required:
            return _ScenarioInterpretation(
                status=ValidationStatus.FAIL,
                diagnostic_class=DiagnosticClass.DIRECT,
                error_kind=ErrorKind.IO,
                primary_message=_bounded_message(
                    artifacts.message or "A required scenario artifact was not produced."
                ),
            )

    return _ScenarioInterpretation(
        status=ValidationStatus.OK,
        diagnostic_class=DiagnosticClass.OK,
        error_kind=ErrorKind.OK,
        primary_message="Scenario completed successfully.",
    )


def _load_stage_functions() -> ScenarioStageFunctions:
    from .artifacts import (
        verify_scenario_artifacts,
        write_normalized_scenario_output,
    )
    from .assertions import evaluate_assertions as evaluate_scenario_assertions
    from .execution import prepare_and_execute_scenario as execute_scenario
    from .gold_compare import compare_gold as compare_scenario_gold
    from .markers import validate_scenario_markers as evaluate_scenario_markers

    return ScenarioStageFunctions(
        execute=execute_scenario,
        evaluate_markers=evaluate_scenario_markers,
        evaluate_assertions=evaluate_scenario_assertions,
        compare_gold=compare_scenario_gold,
        verify_artifacts=verify_scenario_artifacts,
        write_normalized_output=write_normalized_scenario_output,
    )


def _load_models_module() -> Any:
    from . import models

    return models


def _load_normalization_module() -> Any:
    from . import normalization

    return normalization


def _normalization_registry(
    run_config: object,
    normalization: Any,
) -> _NormalizationRegistry:
    configured = getattr(
        run_config,
        "normalization_registry",
        None,
    )
    registry = configured if configured is not None else normalization.DEFAULT_NORMALIZATION_REGISTRY
    if not callable(getattr(registry, "require", None)):
        raise TypeError("normalization registry must provide require()")
    return cast("_NormalizationRegistry", registry)


def _build_section_results(
    *,
    models: Any,
    marker_sections: Sequence[_MarkerSection],
    normalized_sections: Sequence[object],
) -> tuple[object, ...]:
    normalized_by_id = {
        str(_required_attribute(section, "section_id")): section for section in normalized_sections
    }
    results: list[object] = []

    for marker_section in marker_sections:
        section_id = str(marker_section.section_id)
        normalized = normalized_by_id.get(section_id)
        values = {
            "id": section_id,
            "completed": True,
            "message": "",
            "begin_line": getattr(marker_section, "begin_line", None),
            "end_line": getattr(marker_section, "end_line", None),
            # Compatibility fields retained for older result models.
            "section_id": marker_section.section_id,
            "complete": True,
            "raw_text": marker_section.text,
            "source_evidence": marker_section.source_evidence,
            "normalized_text": (
                getattr(normalized, "normalized_text", None) if normalized is not None else None
            ),
            "source_sha256": (
                getattr(normalized, "source_sha256", None) if normalized is not None else None
            ),
            "normalized_sha256": (
                getattr(normalized, "normalized_sha256", None) if normalized is not None else None
            ),
            "normalization_profile_id": (
                getattr(normalized, "profile_id", None) if normalized is not None else None
            ),
            "normalization_version": (
                getattr(normalized, "profile_version", None) if normalized is not None else None
            ),
        }
        results.append(
            _construct_model(
                models.ScenarioSectionResult,
                values,
                required_fields=("id", "completed"),
            )
        )

    return tuple(results)


def _construct_model(
    model_type: type[_T],
    values: Mapping[str, object],
    *,
    required_fields: Sequence[str],
) -> _T:
    if not isinstance(model_type, type):
        raise TypeError("model_type must be a type")

    signature = inspect.signature(model_type)
    parameters = signature.parameters
    accepts_keywords = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )

    missing_contract_fields = tuple(
        field_name
        for field_name in required_fields
        if field_name not in parameters and not accepts_keywords
    )
    if missing_contract_fields:
        raise TypeError(
            f"{model_type.__name__} does not expose canonical fields: "
            + ", ".join(missing_contract_fields)
        )

    accepted = (
        dict(values)
        if accepts_keywords
        else {field_name: value for field_name, value in values.items() if field_name in parameters}
    )
    return model_type(**accepted)


def _validate_inputs(
    *,
    spec: object,
    run_config: object,
    run_paths: object,
    cancellation_token: object,
) -> None:
    _required_attribute(spec, "scenario_id")
    _required_attribute(spec, "script_path")
    _required_attribute(spec, "required")
    _required_attribute(spec, "working_directory")
    _required_attribute(spec, "timeout_sec")
    _required_attribute(spec, "output_limit_bytes")

    if run_config is None:
        raise TypeError("run_config must not be None")
    if run_paths is None:
        raise TypeError("run_paths must not be None")
    for method_name in (
        "require_owned_path",
        "relative_path",
    ):
        if not callable(getattr(run_paths, method_name, None)):
            raise TypeError(f"run_paths must provide {method_name}()")

    if cancellation_token is not None:
        cancellation_methods = (
            "is_cancelled",
            "is_cancellation_requested",
            "raise_if_cancelled",
        )
        if not any(
            callable(getattr(cancellation_token, name, None)) for name in cancellation_methods
        ):
            raise TypeError("cancellation_token does not expose a cancellation API")


def _validate_execution_evidence(
    execution: _ExecutionEvidence,
    *,
    run_paths: RunPaths,
) -> None:
    if not isinstance(execution.execution_state, ExecutionState):
        raise TypeError("execution_state must be an ExecutionState")
    if not isinstance(execution.timed_out, bool):
        raise TypeError("timed_out must be a bool")
    if (
        not isinstance(execution.duration_ms, int)
        or isinstance(execution.duration_ms, bool)
        or execution.duration_ms < 0
    ):
        raise ValueError("duration_ms must be a non-negative integer")
    if isinstance(execution.command, (str, bytes)):
        raise TypeError("command must be an argument sequence")
    if not execution.command:
        raise ValueError("command must not be empty")
    if not all(isinstance(argument, str) and argument for argument in execution.command):
        raise ValueError("command must contain non-empty string arguments")
    if not isinstance(execution.working_directory, Path):
        raise TypeError("working_directory must be a Path")
    if execution.exit_code is not None and (
        not isinstance(execution.exit_code, int) or isinstance(execution.exit_code, bool)
    ):
        raise TypeError("exit_code must be an integer or None")
    if not isinstance(execution.stdout_text, str):
        raise TypeError("stdout_text must be a string")
    if not isinstance(execution.stderr_text, str):
        raise TypeError("stderr_text must be a string")

    for field_name in ("stdout_path", "stderr_path"):
        path = getattr(execution, field_name)
        if path is not None:
            run_paths.require_owned_path(
                path,
                role=field_name.replace("_", " "),
            )

    if execution.execution_state is ExecutionState.TIMED_OUT and not execution.timed_out:
        raise ValueError("timed_out must be true for timed_out execution state")


def _validate_marker_evaluation(
    evaluation: _MarkerEvaluation,
) -> None:
    if not isinstance(evaluation.complete, bool):
        raise TypeError("marker complete must be a bool")
    seen: set[str] = set()
    for section in evaluation.sections:
        section_id = str(_required_attribute(section, "section_id"))
        if section_id in seen:
            raise ValueError(f"duplicate marker section ID {section_id!r}")
        seen.add(section_id)
        if not isinstance(section.text, str):
            raise TypeError("marker section text must be a string")
        if not isinstance(section.source_evidence, str):
            raise TypeError("marker section source_evidence must be a string")
    if not isinstance(evaluation.message, str):
        raise TypeError("marker message must be a string")


def _validate_assertion_evaluations(
    evaluations: Sequence[_AssertionEvaluation],
) -> None:
    for evaluation in evaluations:
        if not isinstance(evaluation.passed, bool):
            raise TypeError("assertion passed must be a bool")
        if not isinstance(evaluation.evaluated, bool):
            raise TypeError("assertion evaluated must be a bool")
        if not isinstance(evaluation.message, str):
            raise TypeError("assertion message must be a string")


def _validate_gold_evaluation(
    evaluation: _GoldEvaluation,
    *,
    run_paths: RunPaths,
) -> None:
    if evaluation.match not in (True, False, None):
        raise TypeError("gold match must be bool or None")
    if not isinstance(evaluation.message, str):
        raise TypeError("gold message must be a string")
    if evaluation.diff_path is not None:
        run_paths.require_owned_path(
            evaluation.diff_path,
            role="scenario gold diff",
        )


def _validate_artifact_evaluation(
    evaluation: _ArtifactEvaluation,
) -> None:
    if isinstance(evaluation.records, (str, bytes)):
        raise TypeError("artifact records must be a sequence")
    if isinstance(
        evaluation.missing_required,
        (str, bytes),
    ):
        raise TypeError("missing_required must be a sequence")
    if not isinstance(evaluation.message, str):
        raise TypeError("artifact message must be a string")
    if not isinstance(evaluation.error, bool):
        raise TypeError("artifact error must be a bool")


def _exit_code_accepted(
    spec: object,
    exit_code: int | None,
) -> bool:
    expected = getattr(spec, "expected_exit_codes", (0,))
    if isinstance(expected, int) and not isinstance(
        expected,
        bool,
    ):
        expected_codes = (expected,)
    else:
        if not isinstance(expected, Iterable) or isinstance(expected, (str, bytes)):
            raise TypeError("expected_exit_codes must be an integer sequence")
        expected_codes = tuple(expected)

    if not expected_codes:
        raise ValueError("expected_exit_codes must not be empty")
    if not all(isinstance(code, int) and not isinstance(code, bool) for code in expected_codes):
        raise TypeError("expected_exit_codes must contain integers")
    return exit_code in expected_codes


def _execution_error_kind(
    execution: object,
    *,
    fallback: ErrorKind,
) -> ErrorKind:
    value = getattr(execution, "error_kind", fallback)
    if not isinstance(value, ErrorKind):
        return fallback
    if value is ErrorKind.OK and fallback is not ErrorKind.OK:
        return fallback
    return value


def _execution_message(
    execution: object,
    fallback: str,
) -> str:
    value = getattr(execution, "primary_message", None)
    if isinstance(value, str) and value.strip():
        return _bounded_message(value)
    stderr_text = getattr(execution, "stderr_text", "")
    if isinstance(stderr_text, str):
        first_line = next(
            (line.strip() for line in stderr_text.splitlines() if line.strip()),
            "",
        )
        if first_line:
            return _bounded_message(first_line)
    return fallback


def _required_attribute(
    value: object,
    field_name: str,
    *,
    fallback: object = inspect.Parameter.empty,
) -> Any:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if fallback is not inspect.Parameter.empty:
        return fallback
    raise TypeError(f"{type(value).__name__} must expose {field_name}")


def _optional_sequence(
    value: object,
    field_name: str,
) -> tuple[object, ...]:
    candidate = getattr(value, field_name, ())
    if candidate is None:
        return ()
    if isinstance(candidate, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence")
    return tuple(candidate)


def _optional_path(
    value: object,
    field_name: str,
) -> Path | None:
    candidate = getattr(value, field_name, None)
    if candidate is None:
        return None
    return Path(candidate)


def _bounded_message(
    value: str,
    *,
    maximum: int = 1_024,
) -> str:
    if not isinstance(value, str):
        raise TypeError("message must be a string")
    compact = " ".join(value.split())
    if not compact:
        return "Scenario validation failed."
    if len(compact) <= maximum:
        return compact
    return compact[: maximum - 1] + "…"


def _is_contract_exception(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            TypeError,
            ValueError,
            ScenarioExecutionError,
        ),
    )


__all__ = (
    "ScenarioStageFunctions",
    "run_scenario",
    "run_scenarios",
)
