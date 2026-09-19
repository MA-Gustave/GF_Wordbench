"""Unit tests for bounded, evidence-preserving run finalization."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.kernel.errors import ErrorInfo, GFWordbenchError
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
class _Result:
    status: str = "OK"
    revision: int = 0
    failure_count: int = 0


class _Operations:
    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root
        self.events: list[str] = []
        self.exceptions: dict[str, Exception] = {}
        self.prepare_changes: list[bool] = []
        self.prepare_return: object | None = None
        self.publication_return: object = PublicationBatch(
            (
                _publication(
                    run_root / "summary.json",
                    artifact_id="summary",
                    role="machine_summary",
                ),
            )
        )
        self.manifest_return: object = run_root / "manifest.json"
        self.monotonic_values: list[float] = [0.0]
        self.utc_values: list[datetime] = [
            datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
            datetime(2026, 7, 25, 12, 0, 1, tzinfo=UTC),
        ]
        self.last_run_update: (
            tuple[
                FinalizationDisposition,
                Path | None,
            ]
            | None
        ) = None
        self.finalized_request: FinalizationRequest[_Result] | None = None

    def _event(self, name: str) -> None:
        self.events.append(name)
        error = self.exceptions.get(name)
        if error is not None:
            raise error

    def utc_now(self) -> datetime:
        self.events.append("utc_now")
        if len(self.utc_values) > 1:
            return self.utc_values.pop(0)
        return self.utc_values[0]

    def monotonic_now(self) -> float:
        self.events.append("monotonic_now")
        if len(self.monotonic_values) > 1:
            return self.monotonic_values.pop(0)
        return self.monotonic_values[0]

    def mark_finalizing(self, request: FinalizationRequest[_Result]) -> None:
        self._event("mark_finalizing")

    def stop_owned_processes(
        self,
        request: FinalizationRequest[_Result],
    ) -> None:
        self._event("stop_owned_processes")

    def close_stage_writers(
        self,
        request: FinalizationRequest[_Result],
    ) -> None:
        self._event("close_stage_writers")

    def prepare_result(
        self,
        request: FinalizationRequest[_Result],
        *,
        current: _Result,
        failures: tuple[FinalizationFailure, ...],
        finished_at: datetime,
    ) -> PreparedResult[_Result]:
        self._event("prepare_result")
        if self.prepare_return is not None:
            return self.prepare_return  # type: ignore[return-value]
        changed = self.prepare_changes.pop(0) if self.prepare_changes else False
        result = replace(
            current,
            revision=current.revision + int(changed),
            failure_count=len(failures),
        )
        return PreparedResult(result=result, changed=changed)

    def publish_artifacts(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
    ) -> PublicationBatch:
        self._event("publish_artifacts")
        return self.publication_return  # type: ignore[return-value]

    def close_non_manifest_writers(
        self,
        request: FinalizationRequest[_Result],
    ) -> None:
        self._event("close_non_manifest_writers")

    def publish_manifest(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
        publications: PublicationBatch,
    ) -> Path:
        self._event("publish_manifest")
        return self.manifest_return  # type: ignore[return-value]

    def verify_manifest(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
        manifest_path: Path,
        publications: PublicationBatch,
    ) -> None:
        self._event("verify_manifest")

    def mark_finalized(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
        manifest_path: Path,
    ) -> None:
        self.finalized_request = request
        self._event("mark_finalized")

    def mark_incomplete(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
        failures: tuple[FinalizationFailure, ...],
    ) -> None:
        self._event("mark_incomplete")

    def update_last_run(
        self,
        request: FinalizationRequest[_Result],
        result: _Result,
        *,
        disposition: FinalizationDisposition,
        manifest_path: Path | None,
    ) -> None:
        self.last_run_update = (disposition, manifest_path)
        self._event("update_last_run")


def _error(
    *,
    code: str = "GF-WB-IO-001",
    kind: ErrorKind = ErrorKind.IO,
    message: str = "artifact publication failed",
) -> ErrorInfo:
    return ErrorInfo(
        code=code,
        error_kind=kind,
        message=message,
        detail="test failure detail",
        stage="finalization",
        operation="publish_artifacts",
        subject=None,
        retryable=False,
        evidence_paths=(),
        cause_type=None,
    )


def _publication(
    path: Path,
    *,
    artifact_id: str = "artifact",
    role: str = "other",
    required: bool = True,
    success: bool = True,
    error: ErrorInfo | None = None,
) -> ArtifactPublicationOutcome:
    return ArtifactPublicationOutcome(
        artifact_id=artifact_id,
        path=path,
        role=role,
        required=required,
        created_by="tests.unit.runs.test_finalizer",
        success=success,
        error=error,
    )


def _request(
    base_run_root: Path,
    **changes: Any,
) -> FinalizationRequest[_Result]:
    values: dict[str, Any] = {
        "run_id": "20260725_120000",
        "run_root": base_run_root,
        "result": _Result(),
    }
    values.update(changes)
    return FinalizationRequest(**values)


def _failure_steps(outcome: FinalizationOutcome[_Result]) -> tuple[str, ...]:
    return tuple(failure.step.value for failure in outcome.failures)


def test_successful_finalization_follows_the_canonical_order(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.finalized is True
    assert outcome.incomplete is False
    assert outcome.disposition is FinalizationDisposition.FINALIZED
    assert outcome.manifest_path == tmp_path / "manifest.json"
    assert outcome.manifest_verified is True
    assert outcome.failures == ()
    assert outcome.consistency_passes == 1
    assert outcome.state_updated is True
    assert outcome.finalized_at == datetime(
        2026,
        7,
        25,
        12,
        0,
        1,
        tzinfo=UTC,
    )
    assert operations.events == [
        "utc_now",
        "mark_finalizing",
        "stop_owned_processes",
        "close_stage_writers",
        "prepare_result",
        "publish_artifacts",
        "close_non_manifest_writers",
        "prepare_result",
        "publish_manifest",
        "verify_manifest",
        "prepare_result",
        "mark_finalized",
        "update_last_run",
        "utc_now",
    ]
    assert operations.last_run_update == (
        FinalizationDisposition.FINALIZED,
        tmp_path / "manifest.json",
    )


def test_validation_status_does_not_determine_structural_finalization(
    tmp_path: Path,
) -> None:
    for status in ("OK", "FAIL", "ERROR"):
        operations = _Operations(tmp_path)
        request = _request(tmp_path, result=_Result(status=status))

        outcome = finalize_run(request, operations)

        assert outcome.finalized is True
        assert outcome.result.status == status


def test_cancelled_run_can_finalize_when_evidence_is_safe(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    request = _request(tmp_path, cancellation_requested=True)

    outcome = finalize_run(request, operations)

    assert outcome.finalized is True
    assert operations.finalized_request is request
    assert operations.finalized_request.cancellation_requested is True


def test_result_change_republishes_before_manifest_creation(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.prepare_changes = [False, True, False, False]

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.finalized is True
    assert outcome.consistency_passes == 2
    assert outcome.result.revision == 1
    assert operations.events.count("publish_artifacts") == 2
    assert operations.events.count("publish_manifest") == 1
    assert operations.events.index("publish_manifest") > max(
        index for index, event in enumerate(operations.events) if event == "publish_artifacts"
    )


def test_unstable_result_is_bounded_and_left_incomplete(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.prepare_changes = [False, True, True, False, False]

    outcome = finalize_run(
        _request(tmp_path, max_consistency_passes=2),
        operations,
    )

    assert outcome.incomplete is True
    assert outcome.consistency_passes == 2
    assert "GF-WB-INTERNAL-006" in {failure.error.code for failure in outcome.required_failures}
    assert "publish_manifest" not in operations.events
    assert "mark_incomplete" in operations.events


def test_optional_artifact_failure_is_recorded_without_blocking_finalization(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.publication_return = PublicationBatch(
        (
            _publication(
                tmp_path / "summary.json",
                artifact_id="summary",
                role="machine_summary",
            ),
            _publication(
                tmp_path / "optional.txt",
                artifact_id="optional",
                required=False,
                success=False,
                error=_error(message="optional report failed"),
            ),
        )
    )

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.finalized is True
    assert len(outcome.failures) == 1
    assert outcome.failures[0].required is False
    assert outcome.failures[0].artifact_path == tmp_path / "optional.txt"


def test_required_artifact_failure_prevents_finalized_disposition(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.publication_return = PublicationBatch(
        (
            _publication(
                tmp_path / "summary.json",
                artifact_id="summary",
                role="machine_summary",
                success=False,
                error=_error(),
            ),
        )
    )

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert outcome.manifest_verified is True
    assert outcome.required_failures
    assert "mark_finalized" not in operations.events
    assert "mark_incomplete" in operations.events
    assert operations.last_run_update == (
        FinalizationDisposition.INCOMPLETE,
        tmp_path / "manifest.json",
    )


@pytest.mark.parametrize(
    ("event", "expected_step"),
    [
        ("publish_artifacts", FinalizationStep.PUBLISH_ARTIFACTS),
        ("publish_manifest", FinalizationStep.PUBLISH_MANIFEST),
        ("verify_manifest", FinalizationStep.VERIFY_MANIFEST),
    ],
)
def test_required_publication_failures_leave_the_run_incomplete(
    tmp_path: Path,
    event: str,
    expected_step: FinalizationStep,
) -> None:
    operations = _Operations(tmp_path)
    operations.exceptions[event] = OSError("disk unavailable")

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert expected_step.value in _failure_steps(outcome)
    assert any(
        failure.required and failure.error.cause_type == "OSError"
        for failure in outcome.failures
        if failure.step is expected_step
    )
    assert "mark_incomplete" in operations.events


def test_mark_finalized_failure_reclassifies_the_run_as_incomplete(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.exceptions["mark_finalized"] = RuntimeError("freeze failed")

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert outcome.manifest_verified is False
    assert FinalizationStep.MARK_FINALIZED.value in _failure_steps(outcome)
    assert "mark_incomplete" in operations.events
    assert operations.last_run_update == (
        FinalizationDisposition.INCOMPLETE,
        None,
    )


def test_last_run_update_is_optional_after_successful_finalization(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.exceptions["update_last_run"] = OSError("state is read-only")

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.finalized is True
    assert outcome.state_updated is False
    state_failures = [
        failure for failure in outcome.failures if failure.step is FinalizationStep.UPDATE_LAST_RUN
    ]
    assert len(state_failures) == 1
    assert state_failures[0].required is False


def test_artifact_paths_must_remain_beneath_the_run_root(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    operations = _Operations(run_root)
    operations.publication_return = PublicationBatch((_publication(tmp_path / "escaped.txt"),))

    outcome = finalize_run(_request(run_root), operations)

    assert outcome.incomplete is True
    assert any(
        failure.error.code == "GF-WB-CONTRACT-001" and "escapes run root" in failure.error.message
        for failure in outcome.required_failures
    )


@pytest.mark.parametrize("suffix", [".tmp", ".partial"])
def test_temporary_artifacts_cannot_be_published(
    tmp_path: Path,
    suffix: str,
) -> None:
    operations = _Operations(tmp_path)
    operations.publication_return = PublicationBatch(
        (_publication(tmp_path / f"summary.json{suffix}"),)
    )

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert any(
        "temporary artifact cannot be published" in failure.error.message
        for failure in outcome.required_failures
    )


def test_manifest_must_exclude_itself_from_publications(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.publication_return = PublicationBatch(
        (
            _publication(
                tmp_path / "manifest.json",
                artifact_id="manifest",
                role="manifest",
            ),
        )
    )

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert outcome.manifest_verified is False
    assert "verify_manifest" not in operations.events
    assert any(
        "manifest must exclude itself" in failure.error.message
        for failure in outcome.required_failures
    )


@pytest.mark.parametrize(
    "manifest_path",
    [
        Path("relative-manifest.json"),
        Path("/tmp/external-manifest.json"),
    ],
)
def test_manifest_path_must_be_absolute_and_contained(
    tmp_path: Path,
    manifest_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.manifest_return = manifest_path

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    assert outcome.manifest_verified is False
    assert FinalizationStep.PUBLISH_MANIFEST.value in _failure_steps(outcome)


def test_deadline_exhaustion_stops_publication_and_records_timeout(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.monotonic_values = [10.0]

    outcome = finalize_run(
        _request(tmp_path, deadline_monotonic=10.0),
        operations,
    )

    assert outcome.incomplete is True
    assert "publish_artifacts" not in operations.events
    assert any(
        failure.error.error_kind is ErrorKind.TIMEOUT and failure.error.code == "GF-WB-INTERNAL-005"
        for failure in outcome.required_failures
    )
    assert outcome.state_updated is False


def test_controlled_exception_metadata_is_preserved(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.exceptions["mark_finalizing"] = GFWordbenchError(
        "controlled finalization failure",
        code="GF-WB-STATE-001",
        detail="state transition rejected",
        retryable=True,
        evidence_paths=(str(tmp_path / "lifecycle.json"),),
    )

    outcome = finalize_run(_request(tmp_path), operations)

    failure = next(
        item for item in outcome.failures if item.step is FinalizationStep.MARK_FINALIZING
    )
    assert failure.error.code == "GF-WB-STATE-001"
    assert failure.error.message == "controlled finalization failure"
    assert failure.error.detail == "state transition rejected"
    assert failure.error.retryable is True
    assert failure.error.evidence_paths == (str(tmp_path / "lifecycle.json"),)
    assert failure.error.cause_type == "GFWordbenchError"


def test_invalid_operation_return_types_become_contract_failures(
    tmp_path: Path,
) -> None:
    operations = _Operations(tmp_path)
    operations.prepare_return = "not prepared"
    operations.publication_return = "not a batch"

    outcome = finalize_run(_request(tmp_path), operations)

    assert outcome.incomplete is True
    messages = {failure.error.message for failure in outcome.required_failures}
    assert "prepare_result must return PreparedResult" in messages
    assert "publish_artifacts must return PublicationBatch" in messages


def test_publication_batch_rejects_duplicate_ids_and_paths(
    tmp_path: Path,
) -> None:
    first = _publication(tmp_path / "a.txt", artifact_id="same")
    duplicate_id = _publication(tmp_path / "b.txt", artifact_id="same")
    duplicate_path = _publication(tmp_path / "a.txt", artifact_id="other")

    with pytest.raises(ValueError, match="duplicate artifact_id"):
        PublicationBatch((first, duplicate_id))

    with pytest.raises(ValueError, match="duplicate artifact path"):
        PublicationBatch((first, duplicate_path))


def test_publication_outcome_requires_consistent_success_and_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="successful publication"):
        _publication(tmp_path / "a.txt", success=True, error=_error())

    with pytest.raises(ValueError, match="failed publication requires"):
        _publication(tmp_path / "a.txt", success=False, error=None)


@pytest.mark.parametrize(
    ("changes", "expected_exception"),
    [
        ({"run_id": ""}, ValueError),
        ({"run_root": Path("relative")}, ValueError),
        ({"cancellation_requested": 1}, TypeError),
        ({"deadline_monotonic": float("inf")}, ValueError),
        ({"max_consistency_passes": 0}, ValueError),
        ({"max_consistency_passes": 5}, ValueError),
    ],
)
def test_finalization_request_rejects_invalid_contract_values(
    tmp_path: Path,
    changes: dict[str, Any],
    expected_exception: type[Exception],
) -> None:
    with pytest.raises(expected_exception):
        _request(tmp_path, **changes)


def test_finalization_outcome_normalizes_timestamp_to_utc(
    tmp_path: Path,
) -> None:
    local_time = datetime(
        2026,
        7,
        25,
        8,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    outcome = FinalizationOutcome(
        result=_Result(),
        disposition=FinalizationDisposition.FINALIZED,
        finalized_at=local_time,
        publications=PublicationBatch(),
        manifest_path=tmp_path / "manifest.json",
        manifest_verified=True,
        failures=(),
        consistency_passes=1,
        state_updated=True,
    )

    assert outcome.finalized_at == datetime(
        2026,
        7,
        25,
        12,
        tzinfo=UTC,
    )
