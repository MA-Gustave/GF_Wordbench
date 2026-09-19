"""End-to-end release-mode validation with a deterministic fake execution boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from gf_wordbench.kernel.serialization import dumps_canonical_json, format_rfc3339_utc
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ExecutionState,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.paths import allocate_run_paths, validate_run_paths
from gf_wordbench.validation.pipeline import (
    CANONICAL_STAGE_ORDER,
    PipelineStageContext,
    PipelineStageResult,
    StageParticipation,
    ValidationPipelinePlan,
    ValidationStageClass,
    ValidationStageId,
    execute_validation_pipeline,
)

pytestmark = pytest.mark.e2e

_RUN_ID = "20260725_120000"
_FIXED_TIME = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

_STAGE_CLASSES = MappingProxyType(
    {
        ValidationStageId.SELECT: ValidationStageClass.INVENTORY,
        ValidationStageId.INVENTORY: ValidationStageClass.INVENTORY,
        ValidationStageId.STATIC_SCAN: ValidationStageClass.ANALYSIS,
        ValidationStageId.COMPILE: ValidationStageClass.ANALYSIS,
        ValidationStageId.NORMALIZE_DIAGNOSTICS: ValidationStageClass.ANALYSIS,
        ValidationStageId.CLASSIFY_FAILURES: ValidationStageClass.ANALYSIS,
        ValidationStageId.EXECUTE_SCENARIOS: ValidationStageClass.SCENARIO,
        ValidationStageId.NORMALIZE_SCENARIOS: ValidationStageClass.SCENARIO,
        ValidationStageId.COMPARE_GOLD: ValidationStageClass.SCENARIO,
        ValidationStageId.BUILD_RELEASE_ARTIFACTS: ValidationStageClass.RELEASE,
        ValidationStageId.EVALUATE_RELEASE: ValidationStageClass.RELEASE,
        ValidationStageId.COMPARE_PREVIOUS: ValidationStageClass.FINALIZATION,
    }
)


@dataclass(frozen=True, slots=True)
class _ReleaseRequest:
    run_id: str
    project_id: str = "test-language"
    release_requires_pgf: bool = True
    required_scenarios: tuple[str, ...] = ("release-smoke",)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def _ok_stage_result(
    context: PipelineStageContext,
    *,
    artifact_paths: tuple[Path, ...] = (),
    payload: object | None = None,
) -> PipelineStageResult:
    return PipelineStageResult(
        stage_id=context.stage_id,
        stage_name=context.stage_id.value,
        stage_class=_STAGE_CLASSES[context.stage_id],
        required=context.participation is StageParticipation.REQUIRED,
        started_at=_FIXED_TIME,
        finished_at=_FIXED_TIME,
        duration_ms=0,
        validation_status=ValidationStatus.OK,
        execution_state=ExecutionState.COMPLETED,
        error_kind=ErrorKind.OK,
        message=f"{context.stage_id.value} completed.",
        artifact_paths=artifact_paths,
        payload=payload,
    )


def _release_executors(
    paths: RunPaths,
) -> dict[ValidationStageId, Callable[[PipelineStageContext], PipelineStageResult]]:
    def execute(context: PipelineStageContext) -> PipelineStageResult:
        if context.stage_id is ValidationStageId.BUILD_RELEASE_ARTIFACTS:
            pgf_path = paths.pgf_dir / "TestLanguage.pgf"
            pgf_path.write_bytes(b"GF-WORDBENCH-TEST-PGF\n")
            return _ok_stage_result(
                context,
                artifact_paths=(pgf_path,),
                payload={"pgf_verified": True},
            )

        if context.stage_id is ValidationStageId.EVALUATE_RELEASE:
            return _ok_stage_result(
                context,
                payload={
                    "decision": "READY",
                    "all_required_gates_passed": True,
                },
            )

        return _ok_stage_result(context)

    return dict.fromkeys(CANONICAL_STAGE_ORDER, execute)


@dataclass(frozen=True, slots=True)
class _ArtifactSpec:
    path: Path
    role: str
    media_type: str
    created_by: str


def _required_artifact_specs(paths: RunPaths) -> tuple[_ArtifactSpec, ...]:
    return (
        _ArtifactSpec(
            paths.summary_json,
            "machine_summary",
            "application/json",
            "reporting_json",
        ),
        _ArtifactSpec(
            paths.summary_md,
            "human_summary",
            "text/markdown; charset=utf-8",
            "reporting_markdown",
        ),
        _ArtifactSpec(
            paths.ai_ready_md,
            "ai_handoff",
            "text/markdown; charset=utf-8",
            "reporting_ai_ready",
        ),
        _ArtifactSpec(
            paths.top_errors_txt,
            "top_errors",
            "text/plain; charset=utf-8",
            "reporting_logs",
        ),
        _ArtifactSpec(
            paths.master_log,
            "master_log",
            "text/plain; charset=utf-8",
            "reporting_logs",
        ),
        _ArtifactSpec(
            paths.pgf_dir / "TestLanguage.pgf",
            "pgf",
            "application/octet-stream",
            "validation_pgf",
        ),
    )


def _manifest_entry(paths: RunPaths, spec: _ArtifactSpec) -> dict[str, object]:
    relative = spec.path.relative_to(paths.run_dir).as_posix()
    data = spec.path.read_bytes()
    return {
        "path": relative,
        "role": spec.role,
        "media_type": spec.media_type,
        "required": True,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "created_by": spec.created_by,
    }


def _finalize_release_directory(paths: RunPaths) -> None:
    _write_text(
        paths.summary_json,
        json.dumps(
            {
                "schema_id": "gf-wordbench.run-summary",
                "schema_version": "1.0",
                "run": {
                    "run_id": paths.run_id,
                    "mode": "release",
                    "overall_status": "OK",
                    "execution_state": "completed",
                    "partial": False,
                },
                "release": {
                    "decision": "READY",
                    "release_gates_passed": True,
                    "manifest_verified": True,
                },
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
    )
    _write_text(paths.summary_md, "# GF Wordbench Release Summary\n\nStatus: READY")
    _write_text(paths.ai_ready_md, "# AI Ready\n\nRelease decision: READY")
    _write_text(paths.top_errors_txt, "No release-blocking errors.")
    _write_text(paths.master_log, "release run completed")

    entries = tuple(
        sorted(
            (_manifest_entry(paths, spec) for spec in _required_artifact_specs(paths)),
            key=lambda entry: str(entry["path"]),
        )
    )
    document = {
        "schema_id": "gf-wordbench.artifact-manifest",
        "schema_version": "1.0",
        "producer": {"name": "gf-wordbench", "version": "1.0.0"},
        "run_id": paths.run_id,
        "generated_at": format_rfc3339_utc(_FIXED_TIME),
        "hash_algorithm": "sha256",
        "artifacts": list(entries),
    }
    paths.manifest_json.write_text(
        dumps_canonical_json(document),
        encoding="utf-8",
        newline="\n",
    )


def _verify_manifest_bytes(paths: RunPaths) -> tuple[str, ...]:
    raw_document = json.loads(paths.manifest_json.read_text(encoding="utf-8"))
    assert raw_document["schema_id"] == "gf-wordbench.artifact-manifest"
    assert raw_document["schema_version"] == "1.0"
    assert raw_document["hash_algorithm"] == "sha256"
    assert raw_document["run_id"] == paths.run_id

    entries = raw_document["artifacts"]
    assert isinstance(entries, list)
    verified_paths: list[str] = []
    for entry in entries:
        assert isinstance(entry, dict)
        relative_path = entry["path"]
        assert isinstance(relative_path, str)
        assert not Path(relative_path).is_absolute()
        assert ".." not in Path(relative_path).parts
        artifact_path = paths.run_dir / relative_path
        assert artifact_path.is_file()
        data = artifact_path.read_bytes()
        assert len(data) == entry["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert entry["required"] is True
        verified_paths.append(relative_path)

    assert verified_paths == sorted(verified_paths)
    assert len(verified_paths) == len(set(verified_paths))
    return tuple(verified_paths)


def test_release_mode_completes_required_pipeline_and_validates_run_directory(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    output_root.mkdir()
    paths = allocate_run_paths(output_root, _RUN_ID)

    request = _ReleaseRequest(run_id=paths.run_id)
    plan = ValidationPipelinePlan(
        mode=ValidationMode.RELEASE,
        request=request,
        executors=_release_executors(paths),
        enabled_conditional_stages=frozenset(
            {
                ValidationStageId.COMPARE_GOLD,
                ValidationStageId.BUILD_RELEASE_ARTIFACTS,
            }
        ),
        metadata={
            "project_id": request.project_id,
            "run_id": request.run_id,
        },
    )

    result = execute_validation_pipeline(
        plan,
        utc_now=lambda: _FIXED_TIME,
        monotonic_now=lambda: 0.0,
    )

    assert result.mode is ValidationMode.RELEASE
    assert result.overall_status is OverallStatus.OK
    assert result.cancelled is False
    assert tuple(item.stage_id for item in result.stage_results) == CANONICAL_STAGE_ORDER
    assert all(
        item.validation_status is ValidationStatus.OK
        for item in result.stage_results
        if item.required
    )
    assert (
        result.result_for(ValidationStageId.BUILD_RELEASE_ARTIFACTS).validation_status
        is ValidationStatus.OK
    )
    assert result.result_for(ValidationStageId.EVALUATE_RELEASE).payload == {
        "decision": "READY",
        "all_required_gates_passed": True,
    }

    _finalize_release_directory(paths)
    validate_run_paths(paths, require_directories=True)
    manifest_paths = _verify_manifest_bytes(paths)

    assert paths.manifest_json.is_file()
    assert "manifest.json" not in manifest_paths
    assert {
        "summary.json",
        "summary.md",
        "AI_READY.md",
        "top_errors.txt",
        "raw/master.log",
        "artifacts/pgf/TestLanguage.pgf",
    }.issubset(manifest_paths)

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert summary["run"] == {
        "run_id": paths.run_id,
        "mode": "release",
        "overall_status": "OK",
        "execution_state": "completed",
        "partial": False,
    }
    assert summary["release"] == {
        "decision": "READY",
        "release_gates_passed": True,
        "manifest_verified": True,
    }


def test_release_mode_cannot_pass_when_a_required_stage_is_skipped(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    output_root.mkdir()
    paths = allocate_run_paths(output_root, "20260725_120001")

    executors = _release_executors(paths)
    executors.pop(ValidationStageId.EVALUATE_RELEASE)

    with pytest.raises(
        ValueError,
        match=r"required stage .* has no executor",
    ):
        ValidationPipelinePlan(
            mode=ValidationMode.RELEASE,
            request=_ReleaseRequest(run_id=paths.run_id),
            executors=executors,
            enabled_conditional_stages=frozenset(
                {
                    ValidationStageId.COMPARE_GOLD,
                    ValidationStageId.BUILD_RELEASE_ARTIFACTS,
                }
            ),
        )


def test_release_mode_requires_explicit_activation_of_conditional_release_work(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    output_root.mkdir()
    paths = allocate_run_paths(output_root, "20260725_120002")

    result = execute_validation_pipeline(
        ValidationPipelinePlan(
            mode=ValidationMode.RELEASE,
            request=_ReleaseRequest(run_id=paths.run_id),
            executors=_release_executors(paths),
        ),
        utc_now=lambda: _FIXED_TIME,
        monotonic_now=lambda: 0.0,
    )

    assert (
        result.result_for(ValidationStageId.COMPARE_GOLD).validation_status
        is ValidationStatus.SKIPPED
    )
    assert (
        result.result_for(ValidationStageId.BUILD_RELEASE_ARTIFACTS).validation_status
        is ValidationStatus.SKIPPED
    )
    assert result.overall_status is OverallStatus.OK
    assert not (paths.pgf_dir / "TestLanguage.pgf").exists()
