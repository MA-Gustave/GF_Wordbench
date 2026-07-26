"""Unit tests for canonical scenario-service orchestration and classification."""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest

import gf_wordbench.validation.scenarios.service as service
from gf_wordbench.kernel.errors import ScenarioExecutionError
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)


@dataclass(slots=True)
class _Spec:
    scenario_id: str
    script_path: Path
    required: bool
    working_directory: Path
    timeout_sec: float
    output_limit_bytes: int
    expected_exit_codes: tuple[int, ...] = (0,)
    blocked_by: tuple[str, ...] = ()
    gold_path: Path | None = None
    normalization_profile_id: str = "scenario-default"
    normalization_version: str = "1.0.0"
    script_sha256: str = "a" * 64


@dataclass(slots=True)
class _Execution:
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    execution_state: ExecutionState
    timed_out: bool
    duration_ms: int
    stdout_path: Path | None
    stderr_path: Path | None
    stdout_text: str
    stderr_text: str
    cancelled: bool = False
    script_sha256: str = "a" * 64
    error_kind: ErrorKind = ErrorKind.OK
    primary_message: str = ""


@dataclass(frozen=True, slots=True)
class _MarkerSection:
    section_id: str
    text: str
    source_evidence: str
    begin_line: int = 1
    end_line: int = 3


@dataclass(frozen=True, slots=True)
class _Markers:
    complete: bool
    sections: tuple[_MarkerSection, ...]
    message: str = ""


@dataclass(frozen=True, slots=True)
class _Assertion:
    passed: bool
    evaluated: bool
    message: str
    assertion_id: str = "assertion-basic"
    assertion_kind: str = "text-contains"
    required: bool = True


@dataclass(frozen=True, slots=True)
class _Gold:
    match: bool | None
    gold_path: Path | None
    message: str = ""
    diff_path: Path | None = None


@dataclass(frozen=True, slots=True)
class _Artifacts:
    records: tuple[object, ...] = ()
    missing_required: tuple[object, ...] = ()
    message: str = ""
    error: bool = False


@dataclass(frozen=True, slots=True)
class _ExtractedSection:
    section_id: str
    text: str
    source_evidence: str


@dataclass(frozen=True, slots=True)
class _NormalizedSection:
    section_id: str
    normalized_text: str
    source_sha256: str = "b" * 64
    normalized_sha256: str = "c" * 64
    profile_id: str = "scenario-default"
    profile_version: str = "1.0.0"


class _Record:
    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)


class _ScenarioSectionRecord(_Record):
    pass


class _ScenarioResultRecord(_Record):
    pass


_FAKE_MODELS = SimpleNamespace(
    ScenarioSectionResult=_ScenarioSectionRecord,
    ScenarioResult=_ScenarioResultRecord,
)


class _Registry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.profile = object()

    def require(self, profile_id: str, version: str) -> object:
        self.calls.append((profile_id, version))
        return self.profile


class _Normalization:
    ExtractedScenarioSection = _ExtractedSection

    def __init__(self, registry: _Registry) -> None:
        self.DEFAULT_NORMALIZATION_REGISTRY = registry
        self.calls: list[tuple[tuple[_ExtractedSection, ...], object]] = []
        self.failure: BaseException | None = None

    def normalize_scenario_sections(
        self,
        sections: tuple[_ExtractedSection, ...],
        *,
        profile: object,
    ) -> tuple[_NormalizedSection, ...]:
        self.calls.append((tuple(sections), profile))
        if self.failure is not None:
            raise self.failure
        return tuple(
            _NormalizedSection(
                section_id=section.section_id,
                normalized_text=" ".join(section.text.split()),
            )
            for section in sections
        )


@dataclass(slots=True)
class _RunConfig:
    normalization_registry: object | None = None


class _RunPaths:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir.resolve()
        self.ownership_checks: list[tuple[Path, str, bool]] = []
        self.relative_checks: list[tuple[Path, str, bool]] = []

    def require_owned_path(
        self,
        value: Path,
        *,
        role: str = "run-owned path",
        allow_run_dir: bool = False,
    ) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.run_dir / candidate
        candidate = candidate.resolve()
        self.ownership_checks.append((candidate, role, allow_run_dir))
        try:
            relative = candidate.relative_to(self.run_dir)
        except ValueError as exc:
            raise ValueError(f"{role} must be owned by the run") from exc
        if not allow_run_dir and not relative.parts:
            raise ValueError(f"{role} must be inside the run directory")
        return candidate

    def relative_path(
        self,
        value: Path,
        *,
        role: str = "run-owned path",
        allow_run_dir: bool = False,
    ) -> Path:
        candidate = self.require_owned_path(
            value,
            role=role,
            allow_run_dir=allow_run_dir,
        )
        self.relative_checks.append((candidate, role, allow_run_dir))
        return Path(candidate.relative_to(self.run_dir).as_posix())


class _CancellationToken:
    def is_cancelled(self) -> bool:
        return False


class _StageHarness:
    def __init__(
        self,
        *,
        execution: _Execution,
        markers: _Markers,
        normalized_output_path: Path,
    ) -> None:
        self.execution = execution
        self.markers = markers
        self.assertions: tuple[_Assertion, ...] = (
            _Assertion(True, True, "Assertion passed."),
        )
        self.gold = _Gold(True, None, "Gold comparison passed.")
        self.artifacts = _Artifacts(records=("artifact",))
        self.normalized_output_path = normalized_output_path
        self.calls: list[str] = []
        self.failures: dict[str, BaseException] = {}
        self.cancellation_tokens: list[object | None] = []

    def _record(self, name: str) -> None:
        self.calls.append(name)
        failure = self.failures.get(name)
        if failure is not None:
            raise failure

    def execute(
        self,
        spec: object,
        run_config: object,
        run_paths: object,
        *,
        cancellation_token: object | None = None,
    ) -> _Execution:
        del spec, run_config, run_paths
        self._record("execute")
        self.cancellation_tokens.append(cancellation_token)
        return self.execution

    def evaluate_markers(self, spec: object, stdout_text: str) -> _Markers:
        del spec, stdout_text
        self._record("markers")
        return self.markers

    def evaluate_assertions(
        self,
        spec: object,
        normalized_sections: tuple[object, ...],
        *,
        run_paths: object,
    ) -> tuple[_Assertion, ...]:
        del spec, normalized_sections, run_paths
        self._record("assertions")
        return self.assertions

    def compare_gold(
        self,
        spec: object,
        normalized_sections: tuple[object, ...],
        *,
        run_paths: object,
    ) -> _Gold:
        del spec, normalized_sections, run_paths
        self._record("gold")
        return self.gold

    def verify_artifacts(
        self,
        spec: object,
        execution: object,
        *,
        run_paths: object,
    ) -> _Artifacts:
        del spec, execution, run_paths
        self._record("artifacts")
        return self.artifacts

    def write_normalized_output(
        self,
        spec: object,
        normalized_sections: tuple[object, ...],
        run_paths: object,
    ) -> Path:
        del spec, normalized_sections, run_paths
        self._record("write_normalized")
        return self.normalized_output_path

    def functions(self) -> service.ScenarioStageFunctions:
        return service.ScenarioStageFunctions(
            execute=self.execute,
            evaluate_markers=self.evaluate_markers,
            evaluate_assertions=self.evaluate_assertions,
            compare_gold=self.compare_gold,
            verify_artifacts=self.verify_artifacts,
            write_normalized_output=self.write_normalized_output,
        )


def _spec(tmp_path: Path, **overrides: object) -> _Spec:
    values: dict[str, object] = {
        "scenario_id": "scenario-basic",
        "script_path": Path("scenarios/basic.gfs"),
        "required": True,
        "working_directory": (tmp_path / "project").resolve(),
        "timeout_sec": 30.0,
        "output_limit_bytes": 65_536,
    }
    values.update(overrides)
    return _Spec(**values)  # type: ignore[arg-type]


def _run_paths(tmp_path: Path) -> _RunPaths:
    run_dir = (tmp_path / "run_20260725T190423Z_test").resolve()
    run_dir.mkdir(parents=True)
    return _RunPaths(run_dir)


def _execution(
    spec: _Spec,
    run_paths: _RunPaths,
    **overrides: object,
) -> _Execution:
    values: dict[str, object] = {
        "command": ("gf", "--run", spec.script_path.as_posix()),
        "working_directory": spec.working_directory,
        "exit_code": 0,
        "execution_state": ExecutionState.COMPLETED,
        "timed_out": False,
        "duration_ms": 25,
        "stdout_path": run_paths.run_dir / "raw/scenarios/basic.stdout.txt",
        "stderr_path": run_paths.run_dir / "raw/scenarios/basic.stderr.txt",
        "stdout_text": (
            "GF_WORDBENCH_BEGIN parse-basic\n"
            "parse result\n"
            "GF_WORDBENCH_END parse-basic\n"
        ),
        "stderr_text": "",
    }
    values.update(overrides)
    return _Execution(**values)  # type: ignore[arg-type]


def _markers(*, complete: bool = True, message: str = "") -> _Markers:
    return _Markers(
        complete=complete,
        sections=(
            _MarkerSection(
                section_id="parse-basic",
                text="  parse   result  ",
                source_evidence="stdout:1-3",
            ),
        ),
        message=message,
    )


def _install_harness(
    monkeypatch: pytest.MonkeyPatch,
    harness: _StageHarness,
    normalization: _Normalization,
    *,
    models: object = _FAKE_MODELS,
) -> None:
    monkeypatch.setattr(service, "_load_stage_functions", harness.functions)
    monkeypatch.setattr(service, "_load_models_module", lambda: models)
    monkeypatch.setattr(
        service,
        "_load_normalization_module",
        lambda: normalization,
    )


def _ready_harness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    _Spec,
    _RunConfig,
    _RunPaths,
    _StageHarness,
    _Registry,
    _Normalization,
]:
    spec = _spec(tmp_path)
    run_paths = _run_paths(tmp_path)
    harness = _StageHarness(
        execution=_execution(spec, run_paths),
        markers=_markers(),
        normalized_output_path=(
            run_paths.run_dir / "raw/scenarios/scenario-basic.out"
        ),
    )
    registry = _Registry()
    normalization = _Normalization(registry)
    _install_harness(monkeypatch, harness, normalization)
    return spec, _RunConfig(), run_paths, harness, registry, normalization


def test_public_api_matches_the_canonical_runner_contract() -> None:
    assert service.__all__ == (
        "ScenarioStageFunctions",
        "run_scenario",
        "run_scenarios",
    )

    single = inspect.signature(service.run_scenario).parameters
    assert tuple(single) == (
        "spec",
        "run_config",
        "run_paths",
        "cancellation_token",
    )
    assert single["cancellation_token"].kind is inspect.Parameter.KEYWORD_ONLY
    assert single["cancellation_token"].default is None

    batch = inspect.signature(service.run_scenarios).parameters
    assert tuple(batch) == tuple(single)
    assert batch["cancellation_token"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize(
    "field_name",
    [
        "execute",
        "evaluate_markers",
        "evaluate_assertions",
        "compare_gold",
        "verify_artifacts",
        "write_normalized_output",
    ],
)
def test_stage_bundle_requires_one_callable_owner(field_name: str) -> None:
    callback: Callable[..., object] = lambda *args, **kwargs: None
    values: dict[str, object] = {
        "execute": callback,
        "evaluate_markers": callback,
        "evaluate_assertions": callback,
        "compare_gold": callback,
        "verify_artifacts": callback,
        "write_normalized_output": callback,
    }
    values[field_name] = object()

    with pytest.raises(TypeError, match=rf"{field_name} must be callable"):
        service.ScenarioStageFunctions(**values)  # type: ignore[arg-type]


def test_stage_bundle_is_immutable() -> None:
    callback: Callable[..., object] = lambda *args, **kwargs: None
    stages = service.ScenarioStageFunctions(
        execute=callback,
        evaluate_markers=callback,
        evaluate_assertions=callback,
        compare_gold=callback,
        verify_artifacts=callback,
        write_normalized_output=callback,
    )

    with pytest.raises(FrozenInstanceError):
        stages.execute = callback  # type: ignore[misc]


def test_default_stage_loader_binds_the_canonical_stage_owners() -> None:
    stages = service._load_stage_functions()

    assert stages.execute.__module__.endswith(".scenarios.execution")
    assert stages.evaluate_markers.__module__.endswith(".scenarios.markers")
    assert stages.evaluate_assertions.__module__.endswith(
        ".scenarios.assertions"
    )
    assert stages.compare_gold.__module__.endswith(".scenarios.gold_compare")
    assert stages.verify_artifacts.__module__.endswith(".scenarios.artifacts")
    assert stages.write_normalized_output.__module__.endswith(
        ".scenarios.artifacts"
    )


def test_run_scenarios_preserves_order_and_forwards_cancellation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = tuple(
        _spec(tmp_path, scenario_id=f"scenario-{index}")
        for index in range(3)
    )
    run_config = _RunConfig()
    run_paths = _run_paths(tmp_path)
    token = _CancellationToken()
    calls: list[tuple[str, object, object, object | None]] = []

    def fake_run_scenario(
        spec: _Spec,
        received_config: object,
        received_paths: object,
        *,
        cancellation_token: object | None = None,
    ) -> str:
        calls.append(
            (
                spec.scenario_id,
                received_config,
                received_paths,
                cancellation_token,
            )
        )
        return spec.scenario_id

    monkeypatch.setattr(service, "run_scenario", fake_run_scenario)

    results = service.run_scenarios(
        specs,
        run_config,
        run_paths,
        cancellation_token=token,
    )

    assert results == ["scenario-0", "scenario-1", "scenario-2"]
    assert [item[0] for item in calls] == [
        "scenario-0",
        "scenario-1",
        "scenario-2",
    ]
    assert all(item[1] is run_config for item in calls)
    assert all(item[2] is run_paths for item in calls)
    assert all(item[3] is token for item in calls)


@pytest.mark.parametrize("invalid", ["scenario", b"scenario"])
def test_run_scenarios_rejects_scalar_sequences(invalid: object) -> None:
    with pytest.raises(TypeError, match="specs must be a sequence"):
        service.run_scenarios(  # type: ignore[arg-type]
            invalid,
            object(),
            object(),
        )


def test_run_scenarios_rejects_duplicate_ids_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fail_if_called(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("execution must not start")

    monkeypatch.setattr(service, "run_scenario", fail_if_called)
    specs = (
        _spec(tmp_path, scenario_id="scenario-duplicate"),
        _spec(tmp_path, scenario_id="scenario-duplicate"),
    )

    with pytest.raises(ValueError, match="duplicate scenario ID"):
        service.run_scenarios(specs, object(), object())

    assert calls == 0


def test_run_scenarios_validates_id_type_and_batch_bound() -> None:
    with pytest.raises(TypeError, match=r"specs\[0\].scenario_id"):
        service.run_scenarios(
            (SimpleNamespace(scenario_id=1),),
            object(),
            object(),
        )

    too_many = tuple(
        SimpleNamespace(scenario_id=f"scenario-{index}")
        for index in range(service._MAX_BATCH_SIZE + 1)
    )
    with pytest.raises(ValueError, match="maximum batch size"):
        service.run_scenarios(too_many, object(), object())


def test_input_contract_is_checked_before_stage_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = _spec(tmp_path)
    delattr(spec, "required")
    loaded = False

    def stage_loader() -> object:
        nonlocal loaded
        loaded = True
        raise AssertionError("stage loading must not occur")

    monkeypatch.setattr(service, "_load_stage_functions", stage_loader)

    with pytest.raises(TypeError, match="must expose required"):
        service.run_scenario(spec, _RunConfig(), _run_paths(tmp_path))

    assert loaded is False


def test_input_contract_requires_run_paths_and_cancellation_api(
    tmp_path: Path,
) -> None:
    spec = _spec(tmp_path)

    with pytest.raises(TypeError, match=r"require_owned_path\(\)"):
        service._validate_inputs(
            spec=spec,
            run_config=_RunConfig(),
            run_paths=SimpleNamespace(relative_path=lambda value: value),
            cancellation_token=None,
        )

    with pytest.raises(TypeError, match="cancellation API"):
        service._validate_inputs(
            spec=spec,
            run_config=_RunConfig(),
            run_paths=_run_paths(tmp_path),
            cancellation_token=object(),
        )


def test_successful_scenario_runs_each_owner_in_canonical_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        spec,
        run_config,
        run_paths,
        harness,
        registry,
        normalization,
    ) = _ready_harness(tmp_path, monkeypatch)
    token = _CancellationToken()

    result = service.run_scenario(
        spec,
        run_config,
        run_paths,
        cancellation_token=token,
    )

    assert harness.calls == [
        "execute",
        "markers",
        "write_normalized",
        "assertions",
        "gold",
        "artifacts",
    ]
    assert harness.cancellation_tokens == [token]
    assert registry.calls == [("scenario-default", "1.0.0")]
    assert len(normalization.calls) == 1
    extracted, profile = normalization.calls[0]
    assert profile is registry.profile
    assert extracted == (
        _ExtractedSection(
            section_id="parse-basic",
            text="  parse   result  ",
            source_evidence="stdout:1-3",
        ),
    )

    assert result.scenario_id == "scenario-basic"
    assert result.status is ValidationStatus.OK
    assert result.diagnostic_class is DiagnosticClass.OK
    assert result.error_kind is ErrorKind.OK
    assert result.primary_message == "Scenario completed successfully."
    assert result.command == harness.execution.command
    assert result.stdout_path == harness.execution.stdout_path
    assert result.stderr_path == harness.execution.stderr_path
    assert result.normalized_output_path == harness.normalized_output_path
    assert result.gold_match is True
    assert result.assertions == harness.assertions
    assert result.artifacts == harness.artifacts.records
    assert len(result.sections) == 1

    checked_roles = {role for _, role, _ in run_paths.ownership_checks}
    assert {
        "stdout path",
        "stderr path",
        "normalized scenario output",
    }.issubset(checked_roles)


def test_configured_normalization_registry_overrides_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, _, run_paths, harness, default, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    configured = _Registry()

    service.run_scenario(
        spec,
        _RunConfig(normalization_registry=configured),
        run_paths,
    )

    assert configured.calls == [("scenario-default", "1.0.0")]
    assert default.calls == []
    assert normalization.calls[0][1] is configured.profile
    assert harness.calls[-1] == "artifacts"


def test_missing_completion_marker_is_behavioral_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, run_config, run_paths, harness, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    harness.markers = _markers(
        complete=False,
        message="Required section parse-basic did not complete.",
    )

    result = service.run_scenario(spec, run_config, run_paths)

    assert harness.calls == ["execute", "markers", "artifacts"]
    assert normalization.calls == []
    assert result.status is ValidationStatus.FAIL
    assert result.diagnostic_class is DiagnosticClass.DIRECT
    assert result.error_kind is ErrorKind.SCRIPT
    assert result.primary_message == (
        "Required section parse-basic did not complete."
    )


@pytest.mark.parametrize(
    ("state", "timed_out", "cancelled", "error_kind", "message"),
    [
        (
            ExecutionState.TIMED_OUT,
            True,
            False,
            ErrorKind.TIMEOUT,
            "Process timed out.",
        ),
        (
            ExecutionState.CANCELLED,
            False,
            True,
            ErrorKind.OTHER,
            "Execution was cancelled.",
        ),
        (
            ExecutionState.LAUNCH_FAILED,
            False,
            False,
            ErrorKind.TOOL,
            "Failed to launch GF executable.",
        ),
    ],
)
def test_process_failures_become_structured_error_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: ExecutionState,
    timed_out: bool,
    cancelled: bool,
    error_kind: ErrorKind,
    message: str,
) -> None:
    spec, run_config, run_paths, harness, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    harness.execution = replace(
        harness.execution,
        exit_code=None,
        execution_state=state,
        timed_out=timed_out,
        cancelled=cancelled,
    )

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is ValidationStatus.ERROR
    assert result.diagnostic_class is DiagnosticClass.AMBIGUOUS
    assert result.error_kind is error_kind
    assert result.primary_message == message
    assert result.stdout_path == harness.execution.stdout_path
    assert result.stderr_path == harness.execution.stderr_path
    assert normalization.calls == []
    assert harness.calls == ["execute", "markers", "artifacts"]


@pytest.mark.parametrize(
    ("exit_code", "expected", "status"),
    [
        (0, (0,), ValidationStatus.OK),
        (2, (0, 2), ValidationStatus.OK),
        (2, (0,), ValidationStatus.FAIL),
    ],
)
def test_completed_execution_honors_declared_exit_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_code: int,
    expected: tuple[int, ...],
    status: ValidationStatus,
) -> None:
    spec, run_config, run_paths, harness, _, _ = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    spec.expected_exit_codes = expected
    harness.execution = replace(harness.execution, exit_code=exit_code)

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is status
    if status is ValidationStatus.FAIL:
        assert result.diagnostic_class is DiagnosticClass.DIRECT
        assert result.error_kind is ErrorKind.SCRIPT


@pytest.mark.parametrize(
    ("assertion", "status", "diagnostic_class"),
    [
        (
            _Assertion(False, False, "Assertion could not be evaluated."),
            ValidationStatus.ERROR,
            DiagnosticClass.AMBIGUOUS,
        ),
        (
            _Assertion(False, True, "Expected parse was absent."),
            ValidationStatus.FAIL,
            DiagnosticClass.DIRECT,
        ),
        (
            _Assertion(True, True, "Assertion passed."),
            ValidationStatus.OK,
            DiagnosticClass.OK,
        ),
    ],
)
def test_assertion_aggregation_preserves_error_fail_ok_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    assertion: _Assertion,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
) -> None:
    spec, run_config, run_paths, harness, _, _ = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    harness.assertions = (assertion,)

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is status
    assert result.diagnostic_class is diagnostic_class
    if status is not ValidationStatus.OK:
        assert result.primary_message == assertion.message


def test_gold_mismatch_is_a_direct_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, run_config, run_paths, harness, _, _ = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    harness.gold = _Gold(
        False,
        Path("gold/scenario-basic.gold"),
        "Normalized output differs from gold.",
        run_paths.run_dir / "raw/scenarios/scenario-basic.gold.diff",
    )

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is ValidationStatus.FAIL
    assert result.diagnostic_class is DiagnosticClass.DIRECT
    assert result.error_kind is ErrorKind.SCRIPT
    assert result.gold_match is False
    assert result.primary_message == "Normalized output differs from gold."


@pytest.mark.parametrize(
    ("artifacts", "status", "diagnostic_class"),
    [
        (
            _Artifacts(
                missing_required=("artifacts/output.txt",),
                message="Required artifact was not produced.",
            ),
            ValidationStatus.FAIL,
            DiagnosticClass.DIRECT,
        ),
        (
            _Artifacts(
                message="Artifact evidence is unreadable.",
                error=True,
            ),
            ValidationStatus.ERROR,
            DiagnosticClass.AMBIGUOUS,
        ),
    ],
)
def test_artifact_outcomes_are_not_silently_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifacts: _Artifacts,
    status: ValidationStatus,
    diagnostic_class: DiagnosticClass,
) -> None:
    spec, run_config, run_paths, harness, _, _ = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    harness.artifacts = artifacts

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is status
    assert result.diagnostic_class is diagnostic_class
    assert result.error_kind is ErrorKind.IO
    assert result.primary_message == artifacts.message


@pytest.mark.parametrize(
    ("stage", "expected_kind", "message_fragment"),
    [
        ("normalization", ErrorKind.OTHER, "normalization failed"),
        ("assertions", ErrorKind.OTHER, "could not be evaluated"),
        ("gold", ErrorKind.OTHER, "gold comparison failed"),
        ("artifacts", ErrorKind.IO, "artifact verification failed"),
    ],
)
def test_operational_stage_exceptions_become_structured_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    expected_kind: ErrorKind,
    message_fragment: str,
) -> None:
    spec, run_config, run_paths, harness, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    if stage == "normalization":
        normalization.failure = RuntimeError("normalizer unavailable")
    else:
        harness.failures[stage] = RuntimeError(f"{stage} unavailable")

    result = service.run_scenario(spec, run_config, run_paths)

    assert result.status is ValidationStatus.ERROR
    assert result.diagnostic_class is DiagnosticClass.AMBIGUOUS
    assert result.error_kind is expected_kind
    assert message_fragment in result.primary_message.casefold()
    if stage != "artifacts":
        assert "artifacts" in harness.calls


@pytest.mark.parametrize(
    "failure",
    [
        TypeError("invalid stage contract"),
        ValueError("corrupted invariant"),
        ScenarioExecutionError("safe result construction is impossible"),
    ],
)
def test_contract_exceptions_are_not_reclassified_as_validation_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    spec, run_config, run_paths, _, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    normalization.failure = failure

    with pytest.raises(type(failure), match=str(failure)):
        service.run_scenario(spec, run_config, run_paths)


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        ({"command": ()}, ValueError, "command must not be empty"),
        ({"command": "gf"}, TypeError, "command must be an argument sequence"),
        ({"duration_ms": -1}, ValueError, "non-negative integer"),
        ({"execution_state": "completed"}, TypeError, "ExecutionState"),
        ({"exit_code": True}, TypeError, "integer or None"),
        (
            {
                "execution_state": ExecutionState.TIMED_OUT,
                "timed_out": False,
            },
            ValueError,
            "timed_out must be true",
        ),
    ],
)
def test_execution_evidence_contract_is_strict(
    tmp_path: Path,
    overrides: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    spec = _spec(tmp_path)
    run_paths = _run_paths(tmp_path)
    execution = _execution(spec, run_paths, **overrides)

    with pytest.raises(error, match=message):
        service._validate_execution_evidence(
            execution,
            run_paths=run_paths,
        )


def test_execution_evidence_paths_must_be_run_owned(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    run_paths = _run_paths(tmp_path)
    execution = _execution(
        spec,
        run_paths,
        stdout_path=(tmp_path / "outside.stdout.txt").resolve(),
    )

    with pytest.raises(ValueError, match="owned by the run"):
        service._validate_execution_evidence(
            execution,
            run_paths=run_paths,
        )


def test_marker_evidence_requires_unique_sections_and_string_fields() -> None:
    duplicate = _Markers(
        complete=True,
        sections=(
            _MarkerSection("parse-basic", "one", "stdout:1-2"),
            _MarkerSection("parse-basic", "two", "stdout:3-4"),
        ),
    )
    with pytest.raises(ValueError, match="duplicate marker section ID"):
        service._validate_marker_evaluation(duplicate)

    invalid_text = SimpleNamespace(
        complete=True,
        sections=(
            SimpleNamespace(
                section_id="parse-basic",
                text=b"bytes",
                source_evidence="stdout:1-2",
            ),
        ),
        message="",
    )
    with pytest.raises(TypeError, match="section text must be a string"):
        service._validate_marker_evaluation(invalid_text)


def test_exit_code_contract_accepts_only_non_empty_integer_sets(
    tmp_path: Path,
) -> None:
    spec = _spec(tmp_path)
    assert service._exit_code_accepted(spec, 0) is True
    assert service._exit_code_accepted(spec, 1) is False

    spec.expected_exit_codes = (0, 2)
    assert service._exit_code_accepted(spec, 2) is True

    spec.expected_exit_codes = ()
    with pytest.raises(ValueError, match="must not be empty"):
        service._exit_code_accepted(spec, 0)

    spec.expected_exit_codes = (0, "2")  # type: ignore[assignment]
    with pytest.raises(TypeError, match="must contain integers"):
        service._exit_code_accepted(spec, 0)


def test_section_results_use_the_canonical_model_vocabulary() -> None:
    @dataclass(frozen=True, slots=True)
    class CanonicalSection:
        id: str
        completed: bool
        message: str = ""
        begin_line: int | None = None
        end_line: int | None = None

    marker = _MarkerSection(
        section_id="parse-basic",
        text="parse result",
        source_evidence="stdout:1-3",
        begin_line=1,
        end_line=3,
    )
    normalized = _NormalizedSection(
        section_id="parse-basic",
        normalized_text="parse result",
    )

    results = service._build_section_results(
        models=SimpleNamespace(ScenarioSectionResult=CanonicalSection),
        marker_sections=(marker,),
        normalized_sections=(normalized,),
    )

    assert results == (
        CanonicalSection(
            id="parse-basic",
            completed=True,
            begin_line=1,
            end_line=3,
        ),
    )


def test_result_construction_supplies_canonical_execution_invariants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, run_config, run_paths, harness, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )
    captured: list[dict[str, object]] = []

    def capture_construct(
        model_type: type[object],
        values: dict[str, object],
        *,
        required_fields: tuple[str, ...],
    ) -> _Record:
        del model_type, required_fields
        captured.append(dict(values))
        return _Record(**values)

    monkeypatch.setattr(service, "_construct_model", capture_construct)

    service.run_scenario(spec, run_config, run_paths)

    result_values = captured[-1]
    assert result_values["script_sha256"] == harness.execution.script_sha256
    assert result_values["cancelled"] is False
    assert result_values["timed_out"] is False
    assert result_values["execution_state"] is ExecutionState.COMPLETED
    assert result_values["stdout_path"] == run_paths.relative_path(
        harness.execution.stdout_path,
        role="stdout path",
    )
    assert result_values["stderr_path"] == run_paths.relative_path(
        harness.execution.stderr_path,
        role="stderr path",
    )
    assert normalization.calls


def test_result_construction_failure_preserves_subject_and_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, run_config, run_paths, harness, _, normalization = _ready_harness(
        tmp_path,
        monkeypatch,
    )

    class BrokenResult:
        def __init__(self, **values: object) -> None:
            del values
            raise RuntimeError("model construction failed")

    models = SimpleNamespace(
        ScenarioSectionResult=_ScenarioSectionRecord,
        ScenarioResult=BrokenResult,
    )
    _install_harness(
        monkeypatch,
        harness,
        normalization,
        models=models,
    )

    with pytest.raises(ScenarioExecutionError) as captured:
        service.run_scenario(spec, run_config, run_paths)

    error = captured.value
    assert error.subject == "scenario-basic"
    assert str(harness.execution.stdout_path) in error.evidence_paths
    assert str(harness.execution.stderr_path) in error.evidence_paths
    assert str(harness.normalized_output_path) in error.evidence_paths
    assert isinstance(error.__cause__, RuntimeError)


def test_bounded_messages_are_stable_and_finite() -> None:
    assert service._bounded_message("  one\n  two   three ") == "one two three"
    assert service._bounded_message("  ") == "Scenario validation failed."

    message = service._bounded_message("x" * 2_000, maximum=32)
    assert len(message) == 32
    assert message.endswith("…")

    with pytest.raises(TypeError, match="message must be a string"):
        service._bounded_message(1)  # type: ignore[arg-type]
