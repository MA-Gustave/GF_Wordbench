"""Run finalization coordination for GF Wordbench."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from typing import Generic, Protocol, TypeVar

from gf_wordbench.kernel.errors import ErrorInfo, GFWordbenchError
from gf_wordbench.kernel.statuses import ErrorKind

RunResultT = TypeVar("RunResultT")


@unique
class FinalizationDisposition(StrEnum):
    FINALIZED = "finalized"
    INCOMPLETE = "incomplete"


@unique
class FinalizationStep(StrEnum):
    MARK_FINALIZING = "mark_finalizing"
    STOP_OWNED_PROCESSES = "stop_owned_processes"
    CLOSE_STAGE_WRITERS = "close_stage_writers"
    PREPARE_RESULT = "prepare_result"
    PUBLISH_ARTIFACTS = "publish_artifacts"
    CLOSE_NON_MANIFEST_WRITERS = "close_non_manifest_writers"
    PUBLISH_MANIFEST = "publish_manifest"
    VERIFY_MANIFEST = "verify_manifest"
    MARK_FINALIZED = "mark_finalized"
    MARK_INCOMPLETE = "mark_incomplete"
    UPDATE_LAST_RUN = "update_last_run"


_STEP_CODES = {
    FinalizationStep.MARK_FINALIZING: "GF-WB-INTERNAL-001",
    FinalizationStep.STOP_OWNED_PROCESSES: "GF-WB-PROCESS-001",
    FinalizationStep.CLOSE_STAGE_WRITERS: "GF-WB-IO-001",
    FinalizationStep.PREPARE_RESULT: "GF-WB-INTERNAL-002",
    FinalizationStep.PUBLISH_ARTIFACTS: "GF-WB-REPORT-001",
    FinalizationStep.CLOSE_NON_MANIFEST_WRITERS: "GF-WB-IO-002",
    FinalizationStep.PUBLISH_MANIFEST: "GF-WB-MANIFEST-001",
    FinalizationStep.VERIFY_MANIFEST: "GF-WB-MANIFEST-002",
    FinalizationStep.MARK_FINALIZED: "GF-WB-INTERNAL-003",
    FinalizationStep.MARK_INCOMPLETE: "GF-WB-INTERNAL-004",
    FinalizationStep.UPDATE_LAST_RUN: "GF-WB-STATE-001",
}

_STEP_KINDS = {
    FinalizationStep.MARK_FINALIZING: ErrorKind.INTERNAL,
    FinalizationStep.STOP_OWNED_PROCESSES: ErrorKind.TOOL,
    FinalizationStep.CLOSE_STAGE_WRITERS: ErrorKind.IO,
    FinalizationStep.PREPARE_RESULT: ErrorKind.INTERNAL,
    FinalizationStep.PUBLISH_ARTIFACTS: ErrorKind.IO,
    FinalizationStep.CLOSE_NON_MANIFEST_WRITERS: ErrorKind.IO,
    FinalizationStep.PUBLISH_MANIFEST: ErrorKind.IO,
    FinalizationStep.VERIFY_MANIFEST: ErrorKind.INTERNAL,
    FinalizationStep.MARK_FINALIZED: ErrorKind.INTERNAL,
    FinalizationStep.MARK_INCOMPLETE: ErrorKind.INTERNAL,
    FinalizationStep.UPDATE_LAST_RUN: ErrorKind.IO,
}


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a bool")
    return value


def _require_path(name: str, value: object) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{name} must be pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{name} must be absolute")
    if "\x00" in str(value):
        raise ValueError(f"{name} must not contain NUL")
    return value


def _require_aware_utc(name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _path_key(value: Path) -> str:
    return str(value.resolve(strict=False)).casefold()


def _is_within(path: Path, root: Path) -> bool:
    candidate = path.resolve(strict=False)
    container = root.resolve(strict=False)
    return candidate == container or candidate.is_relative_to(container)


def _bounded_detail(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


@dataclass(frozen=True, slots=True)
class FinalizationFailure:
    step: FinalizationStep
    required: bool
    error: ErrorInfo
    artifact_path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.step, FinalizationStep):
            raise TypeError("step must be a FinalizationStep")
        _require_bool("required", self.required)
        if not isinstance(self.error, ErrorInfo):
            raise TypeError("error must be an ErrorInfo")
        if self.artifact_path is not None:
            object.__setattr__(
                self,
                "artifact_path",
                _require_path("artifact_path", self.artifact_path),
            )

    @property
    def key(self) -> tuple[str, str, str, str | None]:
        return (
            self.step.value,
            self.error.code,
            self.error.message,
            None if self.artifact_path is None else _path_key(self.artifact_path),
        )


@dataclass(frozen=True, slots=True)
class ArtifactPublicationOutcome:
    artifact_id: str
    path: Path
    role: str
    required: bool
    created_by: str
    success: bool
    error: ErrorInfo | None = None

    def __post_init__(self) -> None:
        _require_text("artifact_id", self.artifact_id)
        object.__setattr__(self, "path", _require_path("path", self.path))
        _require_text("role", self.role)
        _require_bool("required", self.required)
        _require_text("created_by", self.created_by)
        _require_bool("success", self.success)

        if self.success and self.error is not None:
            raise ValueError("successful publication cannot contain an error")
        if not self.success and self.error is None:
            raise ValueError("failed publication requires an error")
        if self.error is not None and not isinstance(self.error, ErrorInfo):
            raise TypeError("error must be an ErrorInfo or None")


@dataclass(frozen=True, slots=True)
class PublicationBatch:
    outcomes: tuple[ArtifactPublicationOutcome, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.outcomes, tuple):
            raise TypeError("outcomes must be a tuple")

        ids: set[str] = set()
        paths: set[str] = set()

        for index, outcome in enumerate(self.outcomes):
            if not isinstance(outcome, ArtifactPublicationOutcome):
                raise TypeError(
                    f"outcomes[{index}] must be an ArtifactPublicationOutcome"
                )
            if outcome.artifact_id in ids:
                raise ValueError(
                    f"duplicate artifact_id: {outcome.artifact_id!r}"
                )

            path_key = _path_key(outcome.path)
            if path_key in paths:
                raise ValueError(
                    f"duplicate artifact path: {outcome.path}"
                )

            ids.add(outcome.artifact_id)
            paths.add(path_key)

    @property
    def successful(self) -> tuple[ArtifactPublicationOutcome, ...]:
        return tuple(outcome for outcome in self.outcomes if outcome.success)

    @property
    def failed(self) -> tuple[ArtifactPublicationOutcome, ...]:
        return tuple(outcome for outcome in self.outcomes if not outcome.success)

    @property
    def required_failed(self) -> tuple[ArtifactPublicationOutcome, ...]:
        return tuple(
            outcome
            for outcome in self.outcomes
            if outcome.required and not outcome.success
        )

    @property
    def published_paths(self) -> tuple[Path, ...]:
        return tuple(outcome.path for outcome in self.successful)


@dataclass(frozen=True, slots=True)
class PreparedResult(Generic[RunResultT]):
    result: RunResultT
    changed: bool

    def __post_init__(self) -> None:
        _require_bool("changed", self.changed)


@dataclass(frozen=True, slots=True)
class FinalizationRequest(Generic[RunResultT]):
    run_id: str
    run_root: Path
    result: RunResultT
    terminal_error: ErrorInfo | None = None
    cancellation_requested: bool = False
    deadline_monotonic: float | None = None
    max_consistency_passes: int = 2

    def __post_init__(self) -> None:
        _require_text("run_id", self.run_id)
        object.__setattr__(self, "run_root", _require_path("run_root", self.run_root))

        if self.terminal_error is not None and not isinstance(
            self.terminal_error,
            ErrorInfo,
        ):
            raise TypeError("terminal_error must be an ErrorInfo or None")

        _require_bool("cancellation_requested", self.cancellation_requested)

        if self.deadline_monotonic is not None:
            if isinstance(self.deadline_monotonic, bool) or not isinstance(
                self.deadline_monotonic,
                (int, float),
            ):
                raise TypeError("deadline_monotonic must be a number or None")
            deadline = float(self.deadline_monotonic)
            if not math.isfinite(deadline):
                raise ValueError("deadline_monotonic must be finite")
            object.__setattr__(self, "deadline_monotonic", deadline)

        if (
            isinstance(self.max_consistency_passes, bool)
            or not isinstance(self.max_consistency_passes, int)
            or self.max_consistency_passes < 1
            or self.max_consistency_passes > 4
        ):
            raise ValueError(
                "max_consistency_passes must be an integer from 1 through 4"
            )


@dataclass(frozen=True, slots=True)
class FinalizationOutcome(Generic[RunResultT]):
    result: RunResultT
    disposition: FinalizationDisposition
    finalized_at: datetime
    publications: PublicationBatch
    manifest_path: Path | None
    manifest_verified: bool
    failures: tuple[FinalizationFailure, ...]
    consistency_passes: int
    state_updated: bool

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, FinalizationDisposition):
            raise TypeError("disposition must be a FinalizationDisposition")

        object.__setattr__(
            self,
            "finalized_at",
            _require_aware_utc("finalized_at", self.finalized_at),
        )

        if not isinstance(self.publications, PublicationBatch):
            raise TypeError("publications must be a PublicationBatch")

        if self.manifest_path is not None:
            object.__setattr__(
                self,
                "manifest_path",
                _require_path("manifest_path", self.manifest_path),
            )

        _require_bool("manifest_verified", self.manifest_verified)

        if not isinstance(self.failures, tuple):
            raise TypeError("failures must be a tuple")
        for index, failure in enumerate(self.failures):
            if not isinstance(failure, FinalizationFailure):
                raise TypeError(
                    f"failures[{index}] must be a FinalizationFailure"
                )

        if (
            isinstance(self.consistency_passes, bool)
            or not isinstance(self.consistency_passes, int)
            or self.consistency_passes < 0
        ):
            raise ValueError("consistency_passes must be non-negative")

        _require_bool("state_updated", self.state_updated)

        if self.disposition is FinalizationDisposition.FINALIZED:
            if self.manifest_path is None or not self.manifest_verified:
                raise ValueError(
                    "finalized disposition requires a verified manifest"
                )
            if any(failure.required for failure in self.failures):
                raise ValueError(
                    "finalized disposition cannot contain required failures"
                )

    @property
    def finalized(self) -> bool:
        return self.disposition is FinalizationDisposition.FINALIZED

    @property
    def incomplete(self) -> bool:
        return self.disposition is FinalizationDisposition.INCOMPLETE

    @property
    def required_failures(self) -> tuple[FinalizationFailure, ...]:
        return tuple(failure for failure in self.failures if failure.required)


class FinalizationOperations(Protocol[RunResultT]):
    def utc_now(self) -> datetime: ...

    def monotonic_now(self) -> float: ...

    def mark_finalizing(
        self,
        request: FinalizationRequest[RunResultT],
    ) -> None: ...

    def stop_owned_processes(
        self,
        request: FinalizationRequest[RunResultT],
    ) -> None: ...

    def close_stage_writers(
        self,
        request: FinalizationRequest[RunResultT],
    ) -> None: ...

    def prepare_result(
        self,
        request: FinalizationRequest[RunResultT],
        *,
        current: RunResultT,
        failures: tuple[FinalizationFailure, ...],
        finished_at: datetime,
    ) -> PreparedResult[RunResultT]: ...

    def publish_artifacts(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
    ) -> PublicationBatch: ...

    def close_non_manifest_writers(
        self,
        request: FinalizationRequest[RunResultT],
    ) -> None: ...

    def publish_manifest(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
        publications: PublicationBatch,
    ) -> Path: ...

    def verify_manifest(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
        manifest_path: Path,
        publications: PublicationBatch,
    ) -> None: ...

    def mark_finalized(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
        manifest_path: Path,
    ) -> None: ...

    def mark_incomplete(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
        failures: tuple[FinalizationFailure, ...],
    ) -> None: ...

    def update_last_run(
        self,
        request: FinalizationRequest[RunResultT],
        result: RunResultT,
        *,
        disposition: FinalizationDisposition,
        manifest_path: Path | None,
    ) -> None: ...


def finalize_run(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
) -> FinalizationOutcome[RunResultT]:
    if not isinstance(request, FinalizationRequest):
        raise TypeError("request must be a FinalizationRequest")

    failures: list[FinalizationFailure] = []
    publications = PublicationBatch()
    manifest_path: Path | None = None
    manifest_verified = False
    consistency_passes = 0
    state_updated = False

    finished_at = _safe_utc_now(operations)

    _attempt_required(
        request,
        operations,
        FinalizationStep.MARK_FINALIZING,
        failures,
        lambda: operations.mark_finalizing(request),
    )
    _attempt_required(
        request,
        operations,
        FinalizationStep.STOP_OWNED_PROCESSES,
        failures,
        lambda: operations.stop_owned_processes(request),
    )
    _attempt_required(
        request,
        operations,
        FinalizationStep.CLOSE_STAGE_WRITERS,
        failures,
        lambda: operations.close_stage_writers(request),
    )

    current = request.result
    current = _prepare_result(
        request,
        operations,
        current=current,
        failures=failures,
        finished_at=finished_at,
    ).result

    for pass_index in range(request.max_consistency_passes):
        consistency_passes = pass_index + 1

        if _deadline_exceeded(request, operations):
            _append_failure(
                failures,
                _deadline_failure(FinalizationStep.PUBLISH_ARTIFACTS),
            )
            break

        publications = _publish_artifacts(
            request,
            operations,
            current,
            failures,
        )
        _validate_publication_batch(
            request,
            publications,
            failures,
        )
        _record_publication_failures(publications, failures)

        _attempt_required(
            request,
            operations,
            FinalizationStep.CLOSE_NON_MANIFEST_WRITERS,
            failures,
            lambda: operations.close_non_manifest_writers(request),
        )

        prepared = _prepare_result(
            request,
            operations,
            current=current,
            failures=failures,
            finished_at=finished_at,
        )
        current = prepared.result

        if prepared.changed:
            if pass_index + 1 < request.max_consistency_passes:
                continue
            _append_failure(
                failures,
                _convergence_failure(
                    "structured result remained unstable after artifact publication"
                ),
            )
            break

        if _deadline_exceeded(request, operations):
            _append_failure(
                failures,
                _deadline_failure(FinalizationStep.PUBLISH_MANIFEST),
            )
            break

        manifest_path = _publish_manifest(
            request,
            operations,
            current,
            publications,
            failures,
        )

        if manifest_path is None:
            current = _prepare_result(
                request,
                operations,
                current=current,
                failures=failures,
                finished_at=finished_at,
            ).result
            break

        if not _validate_manifest_path(
            request,
            manifest_path,
            publications,
            failures,
        ):
            current = _prepare_result(
                request,
                operations,
                current=current,
                failures=failures,
                finished_at=finished_at,
            ).result
            break

        verified = _verify_manifest(
            request,
            operations,
            current,
            manifest_path,
            publications,
            failures,
        )

        if verified:
            manifest_verified = True
            break

        prepared = _prepare_result(
            request,
            operations,
            current=current,
            failures=failures,
            finished_at=finished_at,
        )
        current = prepared.result

        if prepared.changed and pass_index + 1 < request.max_consistency_passes:
            manifest_path = None
            continue

        break

    current = _prepare_result(
        request,
        operations,
        current=current,
        failures=failures,
        finished_at=finished_at,
    ).result

    required_failures = tuple(failure for failure in failures if failure.required)

    if manifest_verified and manifest_path is not None and not required_failures:
        marked = _attempt_required(
            request,
            operations,
            FinalizationStep.MARK_FINALIZED,
            failures,
            lambda: operations.mark_finalized(
                request,
                current,
                manifest_path,
            ),
        )

        if marked:
            disposition = FinalizationDisposition.FINALIZED
        else:
            disposition = FinalizationDisposition.INCOMPLETE
            manifest_verified = False
    else:
        disposition = FinalizationDisposition.INCOMPLETE

    if disposition is FinalizationDisposition.INCOMPLETE:
        current = _prepare_result(
            request,
            operations,
            current=current,
            failures=failures,
            finished_at=finished_at,
        ).result
        _attempt_optional(
            request,
            operations,
            FinalizationStep.MARK_INCOMPLETE,
            failures,
            lambda: operations.mark_incomplete(
                request,
                current,
                tuple(failures),
            ),
        )

    state_updated = _attempt_optional(
        request,
        operations,
        FinalizationStep.UPDATE_LAST_RUN,
        failures,
        lambda: operations.update_last_run(
            request,
            current,
            disposition=disposition,
            manifest_path=manifest_path if manifest_verified else None,
        ),
    )

    finalized_at = _safe_utc_now(operations)

    return FinalizationOutcome(
        result=current,
        disposition=disposition,
        finalized_at=finalized_at,
        publications=publications,
        manifest_path=manifest_path,
        manifest_verified=manifest_verified,
        failures=tuple(failures),
        consistency_passes=consistency_passes,
        state_updated=state_updated,
    )


def _publish_artifacts(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    result: RunResultT,
    failures: list[FinalizationFailure],
) -> PublicationBatch:
    try:
        batch = operations.publish_artifacts(request, result)
    except Exception as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                FinalizationStep.PUBLISH_ARTIFACTS,
                exc,
                required=True,
            ),
        )
        return PublicationBatch()

    if not isinstance(batch, PublicationBatch):
        _append_failure(
            failures,
            _contract_failure(
                FinalizationStep.PUBLISH_ARTIFACTS,
                "publish_artifacts must return PublicationBatch",
            ),
        )
        return PublicationBatch()

    return batch


def _publish_manifest(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    result: RunResultT,
    publications: PublicationBatch,
    failures: list[FinalizationFailure],
) -> Path | None:
    try:
        path = operations.publish_manifest(
            request,
            result,
            publications,
        )
    except Exception as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                FinalizationStep.PUBLISH_MANIFEST,
                exc,
                required=True,
            ),
        )
        return None

    try:
        return _require_path("manifest_path", path)
    except (TypeError, ValueError) as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                FinalizationStep.PUBLISH_MANIFEST,
                exc,
                required=True,
            ),
        )
        return None


def _verify_manifest(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    result: RunResultT,
    manifest_path: Path,
    publications: PublicationBatch,
    failures: list[FinalizationFailure],
) -> bool:
    try:
        operations.verify_manifest(
            request,
            result,
            manifest_path,
            publications,
        )
    except Exception as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                FinalizationStep.VERIFY_MANIFEST,
                exc,
                required=True,
                artifact_path=manifest_path,
            ),
        )
        return False

    return True


def _prepare_result(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    *,
    current: RunResultT,
    failures: list[FinalizationFailure],
    finished_at: datetime,
) -> PreparedResult[RunResultT]:
    try:
        prepared = operations.prepare_result(
            request,
            current=current,
            failures=tuple(failures),
            finished_at=finished_at,
        )
    except Exception as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                FinalizationStep.PREPARE_RESULT,
                exc,
                required=True,
            ),
        )
        return PreparedResult(result=current, changed=False)

    if not isinstance(prepared, PreparedResult):
        _append_failure(
            failures,
            _contract_failure(
                FinalizationStep.PREPARE_RESULT,
                "prepare_result must return PreparedResult",
            ),
        )
        return PreparedResult(result=current, changed=False)

    return prepared


def _attempt_required(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    step: FinalizationStep,
    failures: list[FinalizationFailure],
    operation: object,
) -> bool:
    return _attempt(
        request,
        operations,
        step,
        failures,
        operation,
        required=True,
    )


def _attempt_optional(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    step: FinalizationStep,
    failures: list[FinalizationFailure],
    operation: object,
) -> bool:
    return _attempt(
        request,
        operations,
        step,
        failures,
        operation,
        required=False,
    )


def _attempt(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
    step: FinalizationStep,
    failures: list[FinalizationFailure],
    operation: object,
    *,
    required: bool,
) -> bool:
    if _deadline_exceeded(request, operations):
        _append_failure(
            failures,
            _deadline_failure(step, required=required),
        )
        return False

    if not callable(operation):
        _append_failure(
            failures,
            _contract_failure(
                step,
                "finalization operation is not callable",
                required=required,
            ),
        )
        return False

    try:
        operation()
    except Exception as exc:
        _append_failure(
            failures,
            _failure_from_exception(
                step,
                exc,
                required=required,
            ),
        )
        return False

    return True


def _safe_utc_now(
    operations: FinalizationOperations[RunResultT],
) -> datetime:
    value = operations.utc_now()
    return _require_aware_utc("utc_now result", value)


def _deadline_exceeded(
    request: FinalizationRequest[RunResultT],
    operations: FinalizationOperations[RunResultT],
) -> bool:
    deadline = request.deadline_monotonic
    if deadline is None:
        return False

    value = operations.monotonic_now()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("monotonic_now must return a number")

    instant = float(value)
    if not math.isfinite(instant):
        raise ValueError("monotonic_now must return a finite number")

    return instant >= deadline


def _validate_publication_batch(
    request: FinalizationRequest[RunResultT],
    publications: PublicationBatch,
    failures: list[FinalizationFailure],
) -> None:
    for outcome in publications.outcomes:
        if not _is_within(outcome.path, request.run_root):
            _append_failure(
                failures,
                _contract_failure(
                    FinalizationStep.PUBLISH_ARTIFACTS,
                    f"artifact path escapes run root: {outcome.path}",
                    artifact_path=outcome.path,
                ),
            )

        lowered = outcome.path.name.casefold()
        if lowered.endswith(".tmp") or lowered.endswith(".partial"):
            _append_failure(
                failures,
                _contract_failure(
                    FinalizationStep.PUBLISH_ARTIFACTS,
                    f"temporary artifact cannot be published: {outcome.path}",
                    artifact_path=outcome.path,
                ),
            )


def _validate_manifest_path(
    request: FinalizationRequest[RunResultT],
    manifest_path: Path,
    publications: PublicationBatch,
    failures: list[FinalizationFailure],
) -> bool:
    valid = True

    if not _is_within(manifest_path, request.run_root):
        _append_failure(
            failures,
            _contract_failure(
                FinalizationStep.PUBLISH_MANIFEST,
                f"manifest path escapes run root: {manifest_path}",
                artifact_path=manifest_path,
            ),
        )
        valid = False

    manifest_key = _path_key(manifest_path)
    if any(
        _path_key(outcome.path) == manifest_key
        for outcome in publications.outcomes
    ):
        _append_failure(
            failures,
            _contract_failure(
                FinalizationStep.PUBLISH_MANIFEST,
                "manifest must exclude itself from the artifact catalog",
                artifact_path=manifest_path,
            ),
        )
        valid = False

    lowered = manifest_path.name.casefold()
    if lowered.endswith(".tmp") or lowered.endswith(".partial"):
        _append_failure(
            failures,
            _contract_failure(
                FinalizationStep.PUBLISH_MANIFEST,
                "canonical manifest path cannot use a temporary suffix",
                artifact_path=manifest_path,
            ),
        )
        valid = False

    return valid


def _record_publication_failures(
    publications: PublicationBatch,
    failures: list[FinalizationFailure],
) -> None:
    for outcome in publications.failed:
        assert outcome.error is not None
        _append_failure(
            failures,
            FinalizationFailure(
                step=FinalizationStep.PUBLISH_ARTIFACTS,
                required=outcome.required,
                error=outcome.error,
                artifact_path=outcome.path,
            ),
        )


def _append_failure(
    failures: list[FinalizationFailure],
    failure: FinalizationFailure,
) -> None:
    if any(existing.key == failure.key for existing in failures):
        return
    failures.append(failure)


def _deadline_failure(
    step: FinalizationStep,
    *,
    required: bool = True,
) -> FinalizationFailure:
    error = ErrorInfo(
        code="GF-WB-INTERNAL-005",
        error_kind=ErrorKind.TIMEOUT,
        message="finalization reserve was exhausted",
        detail=f"deadline reached before step {step.value}",
        stage="finalization",
        operation=step.value,
        subject=None,
        retryable=False,
        evidence_paths=(),
        cause_type=None,
    )
    return FinalizationFailure(
        step=step,
        required=required,
        error=error,
    )


def _convergence_failure(message: str) -> FinalizationFailure:
    error = ErrorInfo(
        code="GF-WB-INTERNAL-006",
        error_kind=ErrorKind.INTERNAL,
        message=message,
        detail="bounded finalization passes did not reach a stable result",
        stage="finalization",
        operation=FinalizationStep.PREPARE_RESULT.value,
        subject=None,
        retryable=False,
        evidence_paths=(),
        cause_type=None,
    )
    return FinalizationFailure(
        step=FinalizationStep.PREPARE_RESULT,
        required=True,
        error=error,
    )


def _contract_failure(
    step: FinalizationStep,
    message: str,
    *,
    required: bool = True,
    artifact_path: Path | None = None,
) -> FinalizationFailure:
    evidence = () if artifact_path is None else (str(artifact_path),)
    error = ErrorInfo(
        code="GF-WB-CONTRACT-001",
        error_kind=ErrorKind.INTERNAL,
        message=message,
        detail="finalization contract violation",
        stage="finalization",
        operation=step.value,
        subject=None if artifact_path is None else str(artifact_path),
        retryable=False,
        evidence_paths=evidence,
        cause_type=None,
    )
    return FinalizationFailure(
        step=step,
        required=required,
        error=error,
        artifact_path=artifact_path,
    )


def _failure_from_exception(
    step: FinalizationStep,
    exc: Exception,
    *,
    required: bool,
    artifact_path: Path | None = None,
) -> FinalizationFailure:
    code = _STEP_CODES[step]
    error_kind = _STEP_KINDS[step]
    message = f"{step.value.replace('_', ' ')} failed"
    detail = _bounded_detail(str(exc))

    if isinstance(exc, GFWordbenchError):
        code = exc.code or code
        message = exc.message
        detail = exc.detail or detail

    evidence_paths = list(
        exc.evidence_paths
        if isinstance(exc, GFWordbenchError)
        else ()
    )
    if artifact_path is not None:
        rendered = str(artifact_path)
        if rendered not in evidence_paths:
            evidence_paths.append(rendered)

    error = ErrorInfo(
        code=code,
        error_kind=error_kind,
        message=message,
        detail=detail,
        stage="finalization",
        operation=step.value,
        subject=None if artifact_path is None else str(artifact_path),
        retryable=(
            exc.retryable
            if isinstance(exc, GFWordbenchError)
            else False
        ),
        evidence_paths=tuple(evidence_paths),
        cause_type=type(exc).__name__,
    )

    return FinalizationFailure(
        step=step,
        required=required,
        error=error,
        artifact_path=artifact_path,
    )


__all__ = (
    "ArtifactPublicationOutcome",
    "FinalizationDisposition",
    "FinalizationFailure",
    "FinalizationOperations",
    "FinalizationOutcome",
    "FinalizationRequest",
    "FinalizationStep",
    "PreparedResult",
    "PublicationBatch",
    "finalize_run",
)
