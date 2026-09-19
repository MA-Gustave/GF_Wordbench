"""Unit tests for the canonical regression-comparison contracts.

This module restores the fixed architecture path
``tests/unit/validation/test_regression.py``.  It exercises the stable value
models, baseline compatibility policy, subject identity rules, and safe summary
path resolution without launching GF or mutating previous run artifacts.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.kernel.statuses import (
    ChangeKind,
    ExecutionState,
    OverallStatus,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.validation import regression as regression_package
from gf_wordbench.validation.regression.compatibility import (
    CompatibilityCode,
    CompatibilitySeverity,
    IncompatibleBaselineError,
    RunCompatibilityDescriptor,
    check_run_compatibility,
    normalize_validation_mode,
    require_explicit_baseline_compatibility,
    runs_are_comparable,
)
from gf_wordbench.validation.regression.loader import (
    SUMMARY_FILENAME,
    SummaryLoadAttempt,
    SummaryLoadWarning,
    resolve_summary_path,
)
from gf_wordbench.validation.regression.matcher import (
    RunComparableSubject,
    SubjectIdentity,
    canonical_file_subject_id,
    run_subject_identity,
)
from gf_wordbench.validation.regression.models import (
    ComparisonState,
    CompatibilityDecision,
    DiffEntry,
    RegressionComparison,
    RegressionSnapshot,
    RegressionSubject,
    RegressionSubjectKind,
    RunSnapshotMetadata,
    SubjectDetails,
)

pytestmark = pytest.mark.unit

_EXPECTED_MODEL_NAMES = {
    "SubjectDetails",
    "RegressionSubject",
    "DiffEntry",
    "RunSnapshotMetadata",
    "RegressionSnapshot",
    "CompatibilityDecision",
    "RegressionComparison",
}


def _metadata(
    *,
    run_id: str = "run_20260803_120000",
    project_id: str = "demo-project",
    mode: ValidationMode = ValidationMode.CHECKPOINT,
) -> RunSnapshotMetadata:
    return RunSnapshotMetadata(
        run_id=run_id,
        project_id=project_id,
        mode=mode,
        schema_id="gf-wordbench.run-summary",
        schema_version="1.0",
        gf_version="3.12",
        manifest_available=True,
    )


def _descriptor(
    *,
    project_id: str = "demo-project",
    mode: ValidationMode | str = ValidationMode.CHECKPOINT,
    gf_version: str = "3.12",
) -> RunCompatibilityDescriptor:
    return RunCompatibilityDescriptor(
        project_id=project_id,
        mode=mode,
        gf_version=gf_version,
        selected_subject_ids=("src/Main.gf", "scenario:smoke"),
        normalization_versions=(("scenario", "1"),),
    )


def test_regression_package_initializer_is_side_effect_free() -> None:
    assert regression_package.__all__ == ()


def test_regression_models_have_the_canonical_owned_dataclasses() -> None:
    module = pytest.importorskip("gf_wordbench.validation.regression.models")
    discovered = {name for name in _EXPECTED_MODEL_NAMES if hasattr(module, name)}

    assert discovered == _EXPECTED_MODEL_NAMES
    assert tuple(field.name for field in fields(RegressionSubject)) == (
        "subject_kind",
        "subject_id",
        "status",
        "message",
        "details",
    )


def test_subject_models_enforce_kind_specific_identity_and_status() -> None:
    file_subject = RegressionSubject(
        subject_kind=RegressionSubjectKind.FILE,
        subject_id="src/Main.gf",
        status=ValidationStatus.OK,
    )
    scenario_subject = RegressionSubject(
        subject_kind=RegressionSubjectKind.SCENARIO,
        subject_id="linearize-smoke",
        status=ValidationStatus.FAIL,
        details=SubjectDetails(required=True, gold_match=False),
    )
    run_subject = RegressionSubject(
        subject_kind=RegressionSubjectKind.RUN,
        subject_id="overall-status",
        status=OverallStatus.OK,
    )

    assert file_subject.identity == (
        RegressionSubjectKind.FILE,
        "src/Main.gf",
    )
    assert scenario_subject.details.required is True
    assert run_subject.status is OverallStatus.OK

    with pytest.raises(ValueError, match="forward-slash"):
        RegressionSubject(
            subject_kind=RegressionSubjectKind.FILE,
            subject_id=r"src\Main.gf",
            status=ValidationStatus.OK,
        )
    coerced_run_subject = RegressionSubject(
        subject_kind=RegressionSubjectKind.RUN,
        subject_id="overall-status",
        status=ValidationStatus.OK,
    )
    assert coerced_run_subject.status is OverallStatus.OK


def test_subject_details_are_frozen_and_validate_timeout_consistency() -> None:
    details = SubjectDetails(
        required=True,
        scan_counts={"errors": 1},
        produced_artifacts=("raw/main.stderr.txt",),
    )

    assert dict(details.scan_counts) == {"errors": 1}
    with pytest.raises(FrozenInstanceError):
        details.required = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="conflicts"):
        SubjectDetails(
            execution_state=cast("ExecutionState", "completed"),
            timed_out=True,
        )


def test_snapshot_rejects_duplicate_identity_and_exposes_canonical_order() -> None:
    run_subject = RegressionSubject(
        RegressionSubjectKind.RUN,
        "overall-status",
        OverallStatus.OK,
    )
    file_subject = RegressionSubject(
        RegressionSubjectKind.FILE,
        "src/Main.gf",
        ValidationStatus.OK,
    )
    scenario_subject = RegressionSubject(
        RegressionSubjectKind.SCENARIO,
        "smoke",
        ValidationStatus.OK,
    )
    snapshot = RegressionSnapshot(
        metadata=_metadata(),
        subjects=(scenario_subject, file_subject, run_subject),
    )

    assert snapshot.ordered_subjects == (
        run_subject,
        file_subject,
        scenario_subject,
    )
    assert snapshot.index()[file_subject.identity] is file_subject

    with pytest.raises(ValueError, match="duplicate"):
        RegressionSnapshot(
            metadata=_metadata(),
            subjects=(file_subject, file_subject),
        )


def test_comparison_state_counts_and_regression_projection() -> None:
    entry = DiffEntry(
        subject_kind=RegressionSubjectKind.FILE,
        subject_id="src/Main.gf",
        previous_status=ValidationStatus.OK,
        current_status=ValidationStatus.FAIL,
        change_kind=ChangeKind.REGRESSED,
        message="Status changed: OK -> FAIL.",
    )
    comparison = RegressionComparison(
        state=ComparisonState.COMPLETED,
        entries=(entry,),
        baseline=_metadata(run_id="run_20260802_120000"),
    )

    assert comparison.counts[ChangeKind.REGRESSED] == 1
    assert comparison.regressions == (entry,)

    with pytest.raises(ValueError, match="requires baseline"):
        RegressionComparison(
            state=ComparisonState.COMPLETED,
            entries=(entry,),
        )
    with pytest.raises(ValueError, match="only a completed"):
        RegressionComparison(
            state=ComparisonState.NO_BASELINE,
            entries=(entry,),
        )


def test_compatibility_decision_requires_reasons_only_for_rejection() -> None:
    accepted = CompatibilityDecision(compatible=True)
    rejected = CompatibilityDecision(
        compatible=False,
        reasons=("project identity changed",),
    )

    assert accepted.compatible is True
    assert rejected.reasons == ("project identity changed",)

    with pytest.raises(ValueError, match="must not contain"):
        CompatibilityDecision(compatible=True, reasons=("unexpected",))
    with pytest.raises(ValueError, match="requires at least one"):
        CompatibilityDecision(compatible=False)


def test_identical_run_descriptors_are_compatible() -> None:
    previous = _descriptor()
    current = _descriptor()

    result = check_run_compatibility(previous, current)

    assert result.compatible is True
    assert result.errors == ()
    assert runs_are_comparable(previous, current) is True
    explicit = require_explicit_baseline_compatibility(previous, current)
    assert explicit.compatible is True


def test_project_mismatch_is_an_explicit_incompatibility() -> None:
    previous = _descriptor(project_id="alpha")
    current = _descriptor(project_id="beta")

    result = check_run_compatibility(previous, current)

    assert result.compatible is False
    assert tuple(issue.code for issue in result.errors) == (CompatibilityCode.PROJECT_MISMATCH,)
    assert all(issue.severity is CompatibilitySeverity.ERROR for issue in result.errors)
    with pytest.raises(IncompatibleBaselineError, match="incompatible"):
        require_explicit_baseline_compatibility(previous, current)


def test_legacy_mode_alias_is_normalized_with_a_warning() -> None:
    canonical, consumed_alias = normalize_validation_mode("all")
    result = check_run_compatibility(
        _descriptor(mode="all"),
        _descriptor(mode=ValidationMode.DIAGNOSTIC),
    )

    assert canonical is ValidationMode.DIAGNOSTIC
    assert consumed_alias is True
    assert result.compatible is True
    assert CompatibilityCode.LEGACY_MODE_ALIAS in {issue.code for issue in result.warnings}


def test_subject_identity_helpers_are_stable_and_portable(tmp_path: Path) -> None:
    source_root = (tmp_path / "project" / "src").resolve()
    source_root.mkdir(parents=True)

    assert (
        canonical_file_subject_id(
            Path("nested/Main.gf"),
            source_root=source_root,
        )
        == "nested/Main.gf"
    )

    run_subject = RunComparableSubject(
        subject_id="overall-status",
        status=OverallStatus.OK,
    )
    identity = run_subject_identity(run_subject)

    assert identity == SubjectIdentity("run", "overall-status")
    assert identity.display == "run:overall-status"


def test_summary_path_resolution_accepts_run_directory_and_direct_file(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "runs").resolve()
    run_directory = output_root / "run_20260802_120000"
    run_directory.mkdir(parents=True)
    summary_path = run_directory / SUMMARY_FILENAME
    summary_path.write_text("{}\n", encoding="utf-8")

    assert (
        resolve_summary_path(
            run_directory,
            approved_root=output_root,
        )
        == summary_path.resolve()
    )
    assert (
        resolve_summary_path(
            summary_path,
            approved_root=output_root,
        )
        == summary_path.resolve()
    )


def test_summary_load_attempt_has_exactly_one_outcome() -> None:
    warning = SummaryLoadWarning(
        code="baseline-unavailable",
        message="No compatible baseline was available.",
    )
    attempt = SummaryLoadAttempt(summary=None, warning=warning)

    assert attempt.warning is warning
    assert attempt.summary is None

    with pytest.raises(ValueError, match="exactly one"):
        SummaryLoadAttempt(summary=None, warning=None)
