"""Deterministic release-decision aggregation for GF Wordbench."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from gf_wordbench.kernel.ids import (
    ProjectId,
    RunId,
    validate_project_id,
    validate_run_id,
)
from gf_wordbench.kernel.statuses import ValidationStatus

from .models import (
    ReleaseDecision,
    ReleaseDecisionStatus,
    ReleaseGateApplicability,
    ReleaseGateResult,
)

_GATE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^RG-(?P<number>[0-9]{2,})$"
)
_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+"
    r"(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"
    r"(?:\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$"
)


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _require_version(name: str, value: object) -> str:
    candidate = _require_text(name, value)
    if _VERSION_RE.fullmatch(candidate) is None:
        raise ValueError(
            f"{name} must be a semantic version without a leading prefix"
        )
    return candidate


def _require_aware_datetime(name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_artifact_paths(
    paths: Iterable[Path],
) -> tuple[Path, ...]:
    if isinstance(paths, (str, bytes, Path)):
        raise TypeError(
            "release_artifact_paths must be an iterable of Path values"
        )

    try:
        normalized = tuple(paths)
    except TypeError as exc:
        raise TypeError(
            "release_artifact_paths must be an iterable of Path values"
        ) from exc

    seen: set[str] = set()

    for index, path in enumerate(normalized):
        if not isinstance(path, Path):
            raise TypeError(
                f"release_artifact_paths[{index}] must be pathlib.Path"
            )

        rendered = str(path)
        if not rendered:
            raise ValueError(
                f"release_artifact_paths[{index}] must not be empty"
            )
        if "\x00" in rendered:
            raise ValueError(
                f"release_artifact_paths[{index}] must not contain NUL"
            )

        key = path.as_posix().casefold()
        if key in seen:
            raise ValueError(f"duplicate release artifact path: {path}")
        seen.add(key)

    return normalized


def _gate_sort_key(
    result: ReleaseGateResult,
) -> tuple[int, int, str]:
    match = _GATE_ID_RE.fullmatch(result.gate_id)
    if match is None:
        return (1, 0, result.gate_id)

    return (
        0,
        int(match.group("number")),
        result.gate_id,
    )


def _normalize_gate_results(
    gate_results: Iterable[ReleaseGateResult],
) -> tuple[ReleaseGateResult, ...]:
    if isinstance(gate_results, (str, bytes)):
        raise TypeError(
            "gate_results must be an iterable of ReleaseGateResult values"
        )

    try:
        normalized = tuple(gate_results)
    except TypeError as exc:
        raise TypeError(
            "gate_results must be an iterable of ReleaseGateResult values"
        ) from exc

    if not normalized:
        raise ValueError("release decision requires gate results")

    seen: set[str] = set()

    for index, result in enumerate(normalized):
        if not isinstance(result, ReleaseGateResult):
            raise TypeError(
                f"gate_results[{index}] must be a ReleaseGateResult"
            )

        gate_id = _require_text(
            f"gate_results[{index}].gate_id",
            result.gate_id,
        )

        if gate_id in seen:
            raise ValueError(f"duplicate release gate ID: {gate_id}")

        seen.add(gate_id)
        _validate_gate_result(result)

    return tuple(sorted(normalized, key=_gate_sort_key))


def _validate_gate_result(
    result: ReleaseGateResult,
) -> None:
    applicability = result.applicability
    status = result.status

    if not isinstance(
        applicability,
        ReleaseGateApplicability,
    ):
        raise TypeError(
            f"{result.gate_id} applicability must be "
            "a ReleaseGateApplicability"
        )

    if not isinstance(status, ValidationStatus):
        raise TypeError(
            f"{result.gate_id} status must be a ValidationStatus"
        )

    if (
        applicability
        is ReleaseGateApplicability.NOT_APPLICABLE
        and status is not ValidationStatus.SKIPPED
    ):
        raise ValueError(
            f"{result.gate_id} is not applicable and must be SKIPPED"
        )

    if (
        applicability
        in {
            ReleaseGateApplicability.REQUIRED,
            ReleaseGateApplicability.CONDITIONAL,
        }
        and status is ValidationStatus.SKIPPED
        and not result.blocked_by
        and not result.blockers
    ):
        raise ValueError(
            f"{result.gate_id} is a skipped applicable gate "
            "without a reason or blocker"
        )


def _is_required(
    result: ReleaseGateResult,
) -> bool:
    return result.applicability in {
        ReleaseGateApplicability.REQUIRED,
        ReleaseGateApplicability.CONDITIONAL,
    }


@dataclass(frozen=True, slots=True)
class ReleaseDecisionContext:
    gate_policy_version: str
    project_id: ProjectId
    run_id: RunId
    gf_wordbench_version: str
    gf_version: str
    rgl_identity: str
    release_artifact_paths: tuple[Path, ...]
    decided_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "gate_policy_version",
            _require_version(
                "gate_policy_version",
                self.gate_policy_version,
            ),
        )
        object.__setattr__(
            self,
            "project_id",
            validate_project_id(
                self.project_id,
                field="project_id",
            ),
        )
        object.__setattr__(
            self,
            "run_id",
            validate_run_id(
                self.run_id,
                field="run_id",
            ),
        )
        object.__setattr__(
            self,
            "gf_wordbench_version",
            _require_version(
                "gf_wordbench_version",
                self.gf_wordbench_version,
            ),
        )
        object.__setattr__(
            self,
            "gf_version",
            _require_text(
                "gf_version",
                self.gf_version,
            ),
        )
        object.__setattr__(
            self,
            "rgl_identity",
            _require_text(
                "rgl_identity",
                self.rgl_identity,
            ),
        )
        object.__setattr__(
            self,
            "release_artifact_paths",
            _normalize_artifact_paths(
                self.release_artifact_paths,
            ),
        )
        object.__setattr__(
            self,
            "decided_at",
            _require_aware_datetime(
                "decided_at",
                self.decided_at,
            ),
        )


def evaluate_release_decision(
    context: ReleaseDecisionContext,
    gate_results: Iterable[ReleaseGateResult],
) -> ReleaseDecision:
    if not isinstance(context, ReleaseDecisionContext):
        raise TypeError(
            "context must be a ReleaseDecisionContext"
        )

    ordered_results = _normalize_gate_results(
        gate_results,
    )
    required_results = tuple(
        result
        for result in ordered_results
        if _is_required(result)
    )

    if not required_results:
        raise ValueError(
            "release decision requires at least one "
            "applicable required gate"
        )

    failed_gate_ids = tuple(
        result.gate_id
        for result in required_results
        if result.status is ValidationStatus.FAIL
    )
    error_gate_ids = tuple(
        result.gate_id
        for result in required_results
        if result.status is ValidationStatus.ERROR
    )
    skipped_required_gate_ids = tuple(
        result.gate_id
        for result in required_results
        if result.status is ValidationStatus.SKIPPED
    )

    if error_gate_ids or skipped_required_gate_ids:
        decision = ReleaseDecisionStatus.ERROR
    elif failed_gate_ids:
        decision = ReleaseDecisionStatus.NOT_READY
    else:
        decision = ReleaseDecisionStatus.READY

    passed_gate_count = sum(
        result.status is ValidationStatus.OK
        for result in required_results
    )
    warning_count = sum(
        len(result.warnings)
        for result in ordered_results
    )

    return ReleaseDecision(
        decision=decision,
        gate_policy_version=context.gate_policy_version,
        project_id=context.project_id,
        run_id=context.run_id,
        gf_wordbench_version=context.gf_wordbench_version,
        gf_version=context.gf_version,
        rgl_identity=context.rgl_identity,
        gate_results=ordered_results,
        required_gate_count=len(required_results),
        passed_gate_count=passed_gate_count,
        failed_gate_ids=failed_gate_ids,
        error_gate_ids=error_gate_ids,
        skipped_required_gate_ids=skipped_required_gate_ids,
        warning_count=warning_count,
        release_artifact_paths=context.release_artifact_paths,
        decided_at=context.decided_at,
    )


__all__ = (
    "ReleaseDecisionContext",
    "evaluate_release_decision",
)
