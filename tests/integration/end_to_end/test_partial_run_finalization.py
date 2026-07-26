"""End-to-end coverage for recoverable partial-run finalization."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from gf_wordbench.kernel.errors import ErrorInfo
from gf_wordbench.kernel.statuses import ErrorKind
from gf_wordbench.runs.finalizer import (
    ArtifactPublicationOutcome,
    FinalizationDisposition,
    FinalizationFailure,
    FinalizationOutcome,
    FinalizationRequest,
    FinalizationStep,
    PreparedResult,
    PublicationBatch,
    finalize_run,
)


@dataclass(frozen=True, slots=True)
class _RunSnapshot:
    terminal_error_code: str | None = None
    finalization_error_codes: tuple[str, ...] = ()
    finished_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class _StateUpdate:
    disposition: FinalizationDisposition
    manifest_path: Path | None


class _PartialRunOperations:
    def __init__(
        self,
        run_root: Path,
        *,
        fail_manifest_verification: bool = False,
        fail_state_update: bool = False,
    ) -> None:
        self.run_root = run_root
        self.fail_manifest_verification = fail_manifest_verification
        self.fail_state_update = fail_state_update
        self.calls: list[str] = []
        self.state_update: _StateUpdate | None = None
        self.incomplete_failures: tuple[FinalizationFailure, ...] = ()
        self._clock = datetime(2026, 7, 25, 18, 0, tzinfo=UTC)
        self._monotonic = 100.0

    def utc_now(self) -> datetime:
        value = self._clock
        self._clock += timedelta(milliseconds=1)
        return value

    def monotonic_now(self) -> float:
        return self._monotonic

    def mark_finalizing(self, request: FinalizationRequest[_RunSnapshot]) -> None:
        self.calls.append("mark_finalizing")
        (request.run_root / ".finalizing").write_text("finalizing\n", encoding="utf-8")

    def stop_owned_processes(
        self,
        request: FinalizationRequest[_RunSnapshot],
    ) -> None:
        self.calls.append("stop_owned_processes")
        assert request.cancellation_requested

    def close_stage_writers(
        self,
        request: FinalizationRequest[_RunSnapshot],
    ) -> None:
        self.calls.append("close_stage_writers")
        assert request.run_root == self.run_root

    def prepare_result(
        self,
        request: FinalizationRequest[_RunSnapshot],
        *,
        current: _RunSnapshot,
        failures: tuple[FinalizationFailure, ...],
        finished_at: datetime,
    ) -> PreparedResult[_RunSnapshot]:
        self.calls.append("prepare_result")
        terminal_code = (
            None if request.terminal_error is None else request.terminal_error.code
        )
        failure_codes = tuple(failure.error.code for failure in failures)
        prepared = replace(
            current,
            terminal_error_code=terminal_code,
            finalization_error_codes=failure_codes,
            finished_at=finished_at,
        )
        return PreparedResult(result=prepared, changed=prepared != current)

    def publish_artifacts(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
    ) -> PublicationBatch:
        self.calls.append("publish_artifacts")
        summary_path = request.run_root / "summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "completion_state": "partial",
                    "terminal_error_code": result.terminal_error_code,
                    "finalization_error_codes": list(
                        result.finalization_error_codes
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        required_report = request.run_root / "summary.md"
        report_error = ErrorInfo(
            code="GF-WB-REPORT-001",
            error_kind=ErrorKind.IO,
            message="required human summary could not be published",
            detail="simulated writer failure",
            stage="finalization",
            operation="publish_artifacts",
            subject=str(required_report),
            retryable=False,
            evidence_paths=(str(required_report),),
            cause_type="OSError",
        )

        return PublicationBatch(
            outcomes=(
                ArtifactPublicationOutcome(
                    artifact_id="summary-json",
                    path=summary_path,
                    role="machine_summary",
                    required=True,
                    created_by="test-partial-finalizer",
                    success=True,
                ),
                ArtifactPublicationOutcome(
                    artifact_id="summary-markdown",
                    path=required_report,
                    role="human_summary",
                    required=True,
                    created_by="test-partial-finalizer",
                    success=False,
                    error=report_error,
                ),
            )
        )

    def close_non_manifest_writers(
        self,
        request: FinalizationRequest[_RunSnapshot],
    ) -> None:
        self.calls.append("close_non_manifest_writers")
        assert (request.run_root / "summary.json").is_file()

    def publish_manifest(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
        publications: PublicationBatch,
    ) -> Path:
        self.calls.append("publish_manifest")
        manifest_path = request.run_root / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "completion_state": "partial",
                    "run_id": request.run_id,
                    "artifacts": [
                        outcome.path.relative_to(request.run_root).as_posix()
                        for outcome in publications.successful
                    ],
                    "finalization_error_codes": list(
                        result.finalization_error_codes
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def verify_manifest(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
        manifest_path: Path,
        publications: PublicationBatch,
    ) -> None:
        self.calls.append("verify_manifest")
        if self.fail_manifest_verification:
            raise ValueError("simulated manifest verification failure")

        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert document["completion_state"] == "partial"
        assert document["run_id"] == request.run_id
        assert document["artifacts"] == ["summary.json"]
        assert result.terminal_error_code == "GF-WB-PROCESS-001"
        assert publications.required_failed

    def mark_finalized(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
        manifest_path: Path,
    ) -> None:
        self.calls.append("mark_finalized")
        raise AssertionError("a partial run must never be marked finalized")

    def mark_incomplete(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
        failures: tuple[FinalizationFailure, ...],
    ) -> None:
        self.calls.append("mark_incomplete")
        self.incomplete_failures = failures
        (request.run_root / ".incomplete").write_text(
            "\n".join(failure.error.code for failure in failures) + "\n",
            encoding="utf-8",
        )
        assert result.finished_at is not None

    def update_last_run(
        self,
        request: FinalizationRequest[_RunSnapshot],
        result: _RunSnapshot,
        *,
        disposition: FinalizationDisposition,
        manifest_path: Path | None,
    ) -> None:
        self.calls.append("update_last_run")
        if self.fail_state_update:
            raise OSError("simulated state update failure")
        assert request.run_root == self.run_root
        assert result.terminal_error_code == "GF-WB-PROCESS-001"
        self.state_update = _StateUpdate(disposition, manifest_path)


def _terminal_cancellation_error(run_root: Path) -> ErrorInfo:
    return ErrorInfo(
        code="GF-WB-PROCESS-001",
        error_kind=ErrorKind.OTHER,
        message="run execution was cancelled",
        detail="controlled cancellation before all stages completed",
        stage="run",
        operation="execute",
        subject=None,
        retryable=False,
        evidence_paths=(str(run_root),),
        cause_type="CancellationRequested",
    )


def _finalize_partial_run(
    run_root: Path,
    operations: _PartialRunOperations,
) -> FinalizationOutcome[_RunSnapshot]:
    request = FinalizationRequest(
        run_id="run-20260725T180000Z-partial",
        run_root=run_root,
        result=_RunSnapshot(),
        terminal_error=_terminal_cancellation_error(run_root),
        cancellation_requested=True,
        deadline_monotonic=200.0,
        max_consistency_passes=2,
    )
    return finalize_run(request, operations)


@pytest.mark.e2e
def test_partial_run_preserves_evidence_and_is_never_complete(tmp_path: Path) -> None:
    run_root = (tmp_path / "run-partial").resolve()
    run_root.mkdir()
    operations = _PartialRunOperations(run_root)

    outcome = _finalize_partial_run(run_root, operations)

    assert outcome.disposition is FinalizationDisposition.INCOMPLETE
    assert outcome.incomplete
    assert not outcome.finalized
    assert outcome.manifest_verified
    assert outcome.manifest_path == run_root / "manifest.json"
    assert outcome.consistency_passes == 2
    assert outcome.state_updated
    assert (run_root / "summary.json").is_file()
    assert not (run_root / "summary.md").exists()
    assert (run_root / ".incomplete").is_file()
    assert "GF-WB-REPORT-001" in outcome.result.finalization_error_codes
    assert any(
        failure.step is FinalizationStep.PUBLISH_ARTIFACTS
        and failure.required
        and failure.error.code == "GF-WB-REPORT-001"
        for failure in outcome.failures
    )
    assert operations.state_update == _StateUpdate(
        FinalizationDisposition.INCOMPLETE,
        run_root / "manifest.json",
    )
    assert "mark_finalized" not in operations.calls
    assert operations.calls.index("stop_owned_processes") < operations.calls.index(
        "publish_artifacts"
    )
    assert operations.calls.index("close_non_manifest_writers") < operations.calls.index(
        "publish_manifest"
    )


@pytest.mark.e2e
def test_manifest_verification_failure_keeps_partial_run_incomplete(
    tmp_path: Path,
) -> None:
    run_root = (tmp_path / "run-unverified").resolve()
    run_root.mkdir()
    operations = _PartialRunOperations(
        run_root,
        fail_manifest_verification=True,
    )

    outcome = _finalize_partial_run(run_root, operations)

    assert outcome.disposition is FinalizationDisposition.INCOMPLETE
    assert not outcome.manifest_verified
    assert outcome.manifest_path == run_root / "manifest.json"
    assert (run_root / "summary.json").is_file()
    assert (run_root / ".incomplete").is_file()
    assert any(
        failure.step is FinalizationStep.VERIFY_MANIFEST
        and failure.required
        for failure in outcome.failures
    )
    assert operations.state_update == _StateUpdate(
        FinalizationDisposition.INCOMPLETE,
        None,
    )
    assert "mark_finalized" not in operations.calls


@pytest.mark.e2e
def test_state_update_failure_does_not_discard_partial_evidence(
    tmp_path: Path,
) -> None:
    run_root = (tmp_path / "run-state-failure").resolve()
    run_root.mkdir()
    operations = _PartialRunOperations(run_root, fail_state_update=True)

    outcome = _finalize_partial_run(run_root, operations)

    assert outcome.disposition is FinalizationDisposition.INCOMPLETE
    assert not outcome.state_updated
    assert (run_root / "summary.json").is_file()
    assert (run_root / "manifest.json").is_file()
    assert (run_root / ".incomplete").is_file()
    state_failures = [
        failure
        for failure in outcome.failures
        if failure.step is FinalizationStep.UPDATE_LAST_RUN
    ]
    assert len(state_failures) == 1
    assert not state_failures[0].required
    assert state_failures[0].error.code == "GF-WB-STATE-001"
