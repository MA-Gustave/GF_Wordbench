"""Unit tests for native GF scenario request preparation and execution."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import Final, cast

import pytest
from tests.helpers.fake_processes import make_process_result

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessInput,
    ProcessEvent,
    ProcessEventSink,
    ProcessInputKind,
    ProcessOperationKind,
    ProcessRequest,
    ProcessResult,
)
from gf_wordbench.kernel.ids import ScenarioId
from gf_wordbench.validation.scenarios import execution as scenario_execution
from gf_wordbench.validation.scenarios.execution import (
    ScenarioScriptInput,
    build_scenario_process_request,
    execute_scenario_process,
    prepare_and_execute_scenario,
)

_SCENARIO_ID: Final[ScenarioId] = ScenarioId("linearize-smoke")
_SCRIPT_TEXT: Final[str] = 'ps "GF_WORDBENCH_BEGIN:linearize"\nl Greeting\nq\n'


class _CancellationToken:
    def is_cancelled(self) -> bool:
        return False

    def reason(self) -> str | None:
        return None


class _EventSink:
    def __init__(self, events: list[ProcessEvent]) -> None:
        self.events = events

    def emit(self, event: ProcessEvent, /) -> None:
        self.events.append(event)


def _script(
    tmp_path: Path,
    *,
    content: bytes | None = None,
) -> ScenarioScriptInput:
    script_path = tmp_path / "project" / "validation" / "scenarios" / "linearize-smoke.gfs"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _SCRIPT_TEXT.encode("utf-8") if content is None else content
    script_path.write_bytes(payload)
    return ScenarioScriptInput.from_bytes(
        scenario_id=_SCENARIO_ID,
        script_path=script_path,
        content=payload,
    )


def _request(
    tmp_path: Path,
    *,
    script: ScenarioScriptInput | None = None,
    expected_artifacts: tuple[ArtifactExpectation, ...] = (),
    metadata: dict[str, str] | None = None,
) -> ProcessRequest:
    root = tmp_path.resolve()
    project_root = root / "project"
    run_root = root / "run_20260725_120000"
    evidence_root = run_root / "raw" / "scenarios"
    evidence_root.mkdir(parents=True, exist_ok=True)
    project_root.mkdir(parents=True, exist_ok=True)

    return build_scenario_process_request(
        script or _script(tmp_path),
        executable=root / "tools" / "gf",
        args=("--retain", "DemoEng"),
        working_directory=project_root,
        stdout_path=evidence_root / "linearize-smoke.stdout.txt",
        stderr_path=evidence_root / "linearize-smoke.stderr.txt",
        timeout_sec=30,
        output_limit_bytes=2 * 1024 * 1024,
        approved_read_roots=(project_root, root / "tools", project_root),
        approved_write_roots=(run_root, run_root),
        expected_artifacts=expected_artifacts,
        env_overrides={"GF_LIB_PATH": str(project_root / "lib")},
        env_removals=("HOME", "HOME"),
        sensitive_env_keys=("TOKEN", "TOKEN"),
        sensitive_arg_indexes=(1, 1),
        metadata=metadata,
    )


def test_script_input_records_exact_utf8_source_identity(tmp_path: Path) -> None:
    script = _script(tmp_path)
    payload = _SCRIPT_TEXT.encode("utf-8")

    assert str(script.scenario_id) == _SCENARIO_ID
    assert script.script_path.suffix == ".gfs"
    assert script.text == _SCRIPT_TEXT
    assert script.size_bytes == len(payload)
    assert script.sha256 == hashlib.sha256(payload).hexdigest()
    assert script.has_utf8_bom is False
    script.verify_bytes(payload)


def test_script_input_preserves_utf8_bom_as_executed_bytes(tmp_path: Path) -> None:
    payload = b"\xef\xbb\xbf" + _SCRIPT_TEXT.encode("utf-8")
    script = _script(tmp_path, content=payload)

    assert script.has_utf8_bom is True
    assert script.text.startswith("\ufeff")
    assert script.text.encode("utf-8") == payload
    assert script.sha256 == hashlib.sha256(payload).hexdigest()


def test_script_input_rejects_invalid_utf8_and_non_bytes(tmp_path: Path) -> None:
    path = tmp_path / "invalid.gfs"

    with pytest.raises(UnicodeDecodeError):
        ScenarioScriptInput.from_bytes(
            scenario_id=_SCENARIO_ID,
            script_path=path,
            content=b"\xff",
        )

    with pytest.raises(TypeError, match="content must be bytes"):
        ScenarioScriptInput.from_bytes(
            scenario_id=_SCENARIO_ID,
            script_path=path,
            content=bytearray(b"q\n"),  # type: ignore[arg-type]
        )


def test_script_input_rejects_wrong_extension_and_inconsistent_facts(
    tmp_path: Path,
) -> None:
    payload = b"q\n"
    digest = hashlib.sha256(payload).hexdigest()

    with pytest.raises(ValueError, match=r"\.gfs"):
        ScenarioScriptInput(
            scenario_id=_SCENARIO_ID,
            script_path=tmp_path / "scenario.txt",
            text="q\n",
            size_bytes=len(payload),
            sha256=digest,
            has_utf8_bom=False,
        )

    with pytest.raises(ValueError, match="size_bytes does not match"):
        ScenarioScriptInput(
            scenario_id=_SCENARIO_ID,
            script_path=tmp_path / "scenario.gfs",
            text="q\n",
            size_bytes=len(payload) + 1,
            sha256=digest,
            has_utf8_bom=False,
        )

    with pytest.raises(ValueError, match="sha256 does not match"):
        ScenarioScriptInput(
            scenario_id=_SCENARIO_ID,
            script_path=tmp_path / "scenario.gfs",
            text="q\n",
            size_bytes=len(payload),
            sha256="0" * 64,
            has_utf8_bom=False,
        )


def test_script_input_detects_mutation_after_preparation(tmp_path: Path) -> None:
    script = _script(tmp_path)

    with pytest.raises(ValueError, match="changed after preparation"):
        script.verify_bytes((_SCRIPT_TEXT + "-- changed\n").encode("utf-8"))


def test_request_uses_shell_free_direct_utf8_stdin_and_canonical_defaults(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        metadata={
            "fixture_kind": "unit",
            "execution_transport": "direct-stdin",
        },
    )

    assert request.request_id == f"scenario:{_SCENARIO_ID}"
    assert request.operation_id == f"scenario:{_SCENARIO_ID}"
    assert request.tool_id == "gf"
    assert request.operation_kind is ProcessOperationKind.SCENARIO
    assert request.args == ("--retain", "DemoEng")
    assert request.stdin.kind is ProcessInputKind.TEXT
    assert request.stdin.text == _SCRIPT_TEXT
    assert request.stdin.path is None
    assert request.stdin.encoding == "utf-8"
    assert request.timeout_sec == 30.0
    assert request.output_limit_bytes == 2 * 1024 * 1024
    assert request.termination_grace_sec == 5.0
    assert request.environment_policy == "controlled-inherit-v1"
    assert request.evidence_policy == "scenario-raw-v1"
    assert request.mutability_class == "read_only"
    assert request.network_policy == "denied"
    assert request.approved_read_roots == (
        tmp_path.resolve() / "project",
        tmp_path.resolve() / "tools",
    )
    assert request.approved_write_roots == (tmp_path.resolve() / "run_20260725_120000",)
    assert request.env_removals == frozenset({"HOME"})
    assert request.sensitive_env_keys == frozenset({"TOKEN"})
    assert request.sensitive_arg_indexes == frozenset({1})
    assert request.metadata["scenario_id"] == _SCENARIO_ID
    assert request.metadata["script_path"].endswith("linearize-smoke.gfs")
    assert (
        request.metadata["script_sha256"]
        == hashlib.sha256(_SCRIPT_TEXT.encode("utf-8")).hexdigest()
    )
    assert request.metadata["script_size_bytes"] == str(len(_SCRIPT_TEXT.encode("utf-8")))
    assert request.metadata["script_encoding"] == "utf-8"
    assert request.metadata["script_has_utf8_bom"] == "false"
    assert request.metadata["execution_transport"] == "direct-stdin"


def test_request_metadata_and_environment_are_immutable_snapshots(
    tmp_path: Path,
) -> None:
    metadata = {"fixture_kind": "unit"}
    environment = {"GF_LIB_PATH": "project/lib"}
    script = _script(tmp_path)
    root = tmp_path.resolve()

    request = build_scenario_process_request(
        script,
        executable=root / "gf",
        args=(),
        working_directory=root / "project",
        stdout_path=root / "run" / "stdout.txt",
        stderr_path=root / "run" / "stderr.txt",
        timeout_sec=10,
        output_limit_bytes=1024,
        approved_read_roots=(root,),
        approved_write_roots=(root / "run",),
        metadata=metadata,
        env_overrides=environment,
    )
    metadata["fixture_kind"] = "changed"
    environment["GF_LIB_PATH"] = "changed"

    assert request.metadata["fixture_kind"] == "unit"
    assert request.env_overrides["GF_LIB_PATH"] == "project/lib"
    with pytest.raises(TypeError):
        request.metadata["new"] = "value"  # type: ignore[index]


def test_request_preserves_explicit_artifact_expectations(tmp_path: Path) -> None:
    artifact = ArtifactExpectation(
        path=tmp_path / "run" / "artifacts" / "scenario.json",
        role="scenario-detail",
        required=True,
        kind=ArtifactKind.FILE,
        minimum_size_bytes=1,
    )

    request = _request(tmp_path, expected_artifacts=(artifact,))

    assert request.expected_artifacts == (artifact,)


def test_request_rejects_reserved_metadata_overrides(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not override scenario_id"):
        _request(tmp_path, metadata={"scenario_id": "different"})

    with pytest.raises(ValueError, match="must not override script_sha256"):
        _request(tmp_path, metadata={"script_sha256": "0" * 64})


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("timeout_sec", 0, "timeout_sec must be finite and positive"),
        ("timeout_sec", float("inf"), "timeout_sec must be finite and positive"),
        ("output_limit_bytes", 0, "output_limit_bytes must be positive"),
        ("termination_grace_sec", -1, "termination_grace_sec must be finite and non-negative"),
    ),
)
def test_request_rejects_unbounded_execution_limits(
    tmp_path: Path,
    field: str,
    value: object,
    error: str,
) -> None:
    script = _script(tmp_path)
    arguments: dict[str, object] = {
        "executable": tmp_path / "gf",
        "args": (),
        "working_directory": tmp_path,
        "stdout_path": tmp_path / "stdout.txt",
        "stderr_path": tmp_path / "stderr.txt",
        "timeout_sec": 10,
        "output_limit_bytes": 1024,
        "approved_read_roots": (tmp_path,),
        "approved_write_roots": (tmp_path,),
        "termination_grace_sec": 5,
    }
    arguments[field] = value

    with pytest.raises(ValueError, match=error):
        build_scenario_process_request(script, **arguments)  # type: ignore[arg-type]


def test_request_rejects_shell_like_scalar_args_and_empty_roots(tmp_path: Path) -> None:
    script = _script(tmp_path)
    with pytest.raises(TypeError, match="args must be a sequence"):
        build_scenario_process_request(
            script,
            executable=tmp_path / "gf",
            args=cast(Sequence[str], "< scenario.gfs"),
            working_directory=tmp_path,
            stdout_path=tmp_path / "stdout.txt",
            stderr_path=tmp_path / "stderr.txt",
            timeout_sec=10,
            output_limit_bytes=1024,
            approved_read_roots=(tmp_path,),
            approved_write_roots=(tmp_path,),
        )

    with pytest.raises(ValueError, match="approved_read_roots must not be empty"):
        build_scenario_process_request(
            script,
            executable=tmp_path / "gf",
            args=(),
            working_directory=tmp_path,
            stdout_path=tmp_path / "stdout.txt",
            stderr_path=tmp_path / "stderr.txt",
            timeout_sec=10,
            output_limit_bytes=1024,
            approved_read_roots=(),
            approved_write_roots=(tmp_path,),
        )


def test_request_rejects_duplicate_artifact_identity(tmp_path: Path) -> None:
    artifact = ArtifactExpectation(
        path=tmp_path / "artifact.txt",
        role="evidence",
        required=True,
        kind=ArtifactKind.FILE,
    )

    with pytest.raises(ValueError, match="duplicate path and role"):
        _request(tmp_path, expected_artifacts=(artifact, artifact))


def test_execute_validates_then_delegates_with_cancellation_and_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(tmp_path)
    expected = make_process_result(request)
    token = _CancellationToken()
    events: list[ProcessEvent] = []
    sink = _EventSink(events)
    calls: list[tuple[ProcessRequest, object, object]] = []

    def fake_run_process(
        received: ProcessRequest,
        *,
        cancellation_token: object = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult:
        calls.append((received, cancellation_token, event_sink))
        return expected

    monkeypatch.setattr(scenario_execution, "run_process", fake_run_process)

    result = execute_scenario_process(
        request,
        cancellation_token=token,
        event_sink=sink,
    )

    assert result is expected
    assert calls == [(request, token, sink)]


def _corrupt_stdout_path(request: ProcessRequest) -> ProcessRequest:
    object.__setattr__(request, "stdout_path", request.stderr_path)
    return request


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda request: replace(
                request,
                operation_kind=ProcessOperationKind.COMPILE,
            ),
            "operation_kind must be scenario",
        ),
        (
            lambda request: replace(
                request,
                stdin=ProcessInput.from_file(Path("scenario.gfs")),
            ),
            "direct text stdin",
        ),
        (
            lambda request: replace(
                request,
                stdin=ProcessInput.from_text(
                    request.stdin.text or "",
                    encoding="latin-1",
                ),
            ),
            "encoding must be UTF-8",
        ),
        (
            _corrupt_stdout_path,
            "stdout and stderr paths must be distinct",
        ),
    ),
)
def test_execute_rejects_invalid_scenario_process_contracts_before_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: object,
    message: str,
) -> None:
    request = _request(tmp_path)
    calls: list[ProcessRequest] = []
    monkeypatch.setattr(
        scenario_execution,
        "run_process",
        lambda received, **_kwargs: calls.append(received),
    )

    mutate = mutation
    assert callable(mutate)
    invalid = mutate(request)

    with pytest.raises(ValueError, match=message):
        execute_scenario_process(invalid)

    assert calls == []


@pytest.mark.parametrize(
    ("metadata", "message"),
    (
        ({}, "must include script_path"),
        ({"script_path": "scenario.txt"}, r"script_path must identify a \.gfs file"),
        ({"script_sha256": "not-a-digest"}, "lowercase SHA-256 digest"),
        ({"script_size_bytes": "not-an-integer"}, "must be an integer"),
    ),
)
def test_execute_rejects_missing_or_malformed_integrity_metadata(
    tmp_path: Path,
    metadata: dict[str, str],
    message: str,
) -> None:
    request = _request(tmp_path)
    changed = dict(request.metadata)
    changed.update(metadata)
    if metadata == {}:
        changed.pop("script_path")
    invalid = replace(request, metadata=changed)

    with pytest.raises(ValueError, match=message):
        execute_scenario_process(invalid)


def test_execute_rejects_stdin_changed_after_request_preparation(tmp_path: Path) -> None:
    request = _request(tmp_path)
    invalid = replace(
        request,
        stdin=ProcessInput.from_text((request.stdin.text or "") + "q\n"),
    )

    with pytest.raises(ValueError, match="no longer matches the recorded script SHA-256"):
        execute_scenario_process(invalid)


def test_prepare_and_execute_builds_one_request_and_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = _script(tmp_path)
    token = _CancellationToken()
    events: list[ProcessEvent] = []
    sink = _EventSink(events)
    captured: list[tuple[ProcessRequest, object, object]] = []

    def fake_execute(
        request: ProcessRequest,
        *,
        cancellation_token: object = None,
        event_sink: ProcessEventSink | None = None,
    ) -> ProcessResult:
        captured.append((request, cancellation_token, event_sink))
        return make_process_result(request)

    monkeypatch.setattr(scenario_execution, "execute_scenario_process", fake_execute)

    result = prepare_and_execute_scenario(
        script,
        executable=tmp_path / "gf",
        args=(),
        working_directory=tmp_path / "project",
        stdout_path=tmp_path / "run" / "stdout.txt",
        stderr_path=tmp_path / "run" / "stderr.txt",
        timeout_sec=15,
        output_limit_bytes=4096,
        approved_read_roots=(tmp_path,),
        approved_write_roots=(tmp_path / "run",),
        request_id="scenario.unit",
        operation_id="scenario.unit",
        cancellation_token=token,
        event_sink=sink,
    )

    request, observed_token, observed_sink = captured[0]
    assert result.operation_kind is ProcessOperationKind.SCENARIO
    assert request.request_id == "scenario.unit"
    assert request.operation_id == "scenario.unit"
    assert request.stdin.text == script.text
    assert observed_token is token
    assert observed_sink is sink
    assert len(captured) == 1
