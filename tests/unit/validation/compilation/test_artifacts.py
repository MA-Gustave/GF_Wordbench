"""Unit tests for compile-artifact expectations and verification."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
)
from gf_wordbench.kernel.errors import PathSecurityError
from gf_wordbench.validation.compilation.artifacts import (
    ArtifactCheck,
    ArtifactFreshness,
    ArtifactIssue,
    ArtifactIssueCode,
    ArtifactIssueSeverity,
    ArtifactProvenance,
    ArtifactSnapshot,
    CompileArtifactExpectation,
    CompileArtifactRole,
    artifact_paths_by_role,
    build_process_artifact_expectations,
    required_gfo_expectation,
    required_pgf_expectation,
    verify_compile_artifacts,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64


def _expectation(
    path: Path,
    *,
    role: CompileArtifactRole = CompileArtifactRole.GFO,
    required: bool = True,
    minimum_size_bytes: int = 1,
    freshness_required: bool = True,
    manifest_required: bool = True,
    request_isolated: bool = True,
    operation_id: str | None = None,
    source_fingerprint: str | None = None,
) -> CompileArtifactExpectation:
    return CompileArtifactExpectation(
        path=path,
        role=role,
        required=required,
        minimum_size_bytes=minimum_size_bytes,
        freshness_required=freshness_required,
        manifest_required=manifest_required,
        request_isolated=request_isolated,
        operation_id=operation_id,
        source_fingerprint=source_fingerprint,
    )


def _observation(
    path: Path,
    *,
    role: str = "gfo",
    required: bool = True,
    exists: bool = True,
    kind_matches: bool = True,
    size_bytes: int | None = 8,
) -> ArtifactObservation:
    return ArtifactObservation(
        path=path,
        role=role,
        required=required,
        exists=exists,
        kind_matches=kind_matches,
        size_bytes=size_bytes,
    )


def _snapshot(
    path: Path,
    *,
    exists: bool = True,
    is_file: bool = True,
    size_bytes: int | None = 8,
    modified_time_ns: int | None = 1,
    sha256: str | None = _SHA_A,
    resolved_path: Path | None = None,
    is_symlink: bool = False,
) -> ArtifactSnapshot:
    return ArtifactSnapshot(
        path=path,
        exists=exists,
        is_file=is_file,
        size_bytes=size_bytes,
        modified_time_ns=modified_time_ns,
        sha256=sha256,
        resolved_path=resolved_path,
        is_symlink=is_symlink,
    )


def _codes(check: ArtifactCheck) -> tuple[ArtifactIssueCode, ...]:
    return tuple(issue.code for issue in check.issues)


def test_required_factories_build_canonical_expectations(
    tmp_path: Path,
) -> None:
    gfo_path = tmp_path / "artifacts" / "gfo" / "Grammar.gfo"
    pgf_path = tmp_path / "artifacts" / "pgf" / "Grammar.pgf"

    gfo = required_gfo_expectation(
        path=gfo_path,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
    )
    pgf = required_pgf_expectation(
        path=pgf_path,
        operation_id="pgf:Grammar",
        source_fingerprint=_SHA_B,
        request_isolated=False,
    )

    assert gfo.path == gfo_path
    assert gfo.role is CompileArtifactRole.GFO
    assert gfo.required is True
    assert gfo.minimum_size_bytes == 1
    assert gfo.freshness_required is True
    assert gfo.manifest_required is True
    assert gfo.request_isolated is True
    assert gfo.operation_id == "compile:Grammar"
    assert gfo.source_fingerprint == _SHA_A
    assert gfo.media_type == "application/octet-stream"

    assert pgf.path == pgf_path
    assert pgf.role is CompileArtifactRole.PGF
    assert pgf.request_isolated is False
    assert pgf.operation_id == "pgf:Grammar"
    assert pgf.source_fingerprint == _SHA_B


@pytest.mark.parametrize(
    ("path_name", "role", "message"),
    [
        ("Grammar.pgf", CompileArtifactRole.GFO, "must end with '.gfo'"),
        ("Grammar.gfo", CompileArtifactRole.PGF, "must end with '.pgf'"),
    ],
)
def test_expectation_rejects_role_suffix_mismatch(
    tmp_path: Path,
    path_name: str,
    role: CompileArtifactRole,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _expectation(tmp_path / path_name, role=role)


def test_expectation_rejects_relative_paths_and_invalid_fields() -> None:
    with pytest.raises(ValueError, match="path must be absolute"):
        _expectation(Path("Grammar.gfo"))

    with pytest.raises(TypeError, match="required must be a bool"):
        CompileArtifactExpectation(
            path=Path.cwd() / "Grammar.gfo",
            role=CompileArtifactRole.GFO,
            required=1,  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="minimum_size_bytes must be an integer"):
        _expectation(
            Path.cwd() / "Grammar.gfo",
            minimum_size_bytes=True,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="operation_id must not have outer whitespace"):
        _expectation(
            Path.cwd() / "Grammar.gfo",
            operation_id=" compile ",
        )

    with pytest.raises(ValueError, match="source_fingerprint must contain exactly"):
        _expectation(
            Path.cwd() / "Grammar.gfo",
            source_fingerprint="abc",
        )



def test_process_expectation_conversion_preserves_generic_contract(
    tmp_path: Path,
) -> None:
    expectation = _expectation(
        tmp_path / "Grammar.gfo",
        minimum_size_bytes=32,
    )

    converted = expectation.to_process_expectation()

    assert converted == ArtifactExpectation(
        path=expectation.path,
        role="gfo",
        required=True,
        kind=ArtifactKind.FILE,
        minimum_size_bytes=32,
    )



def test_build_process_expectations_preserves_order_and_rejects_duplicates(
    tmp_path: Path,
) -> None:
    first = _expectation(tmp_path / "z.gfo")
    second = _expectation(tmp_path / "a.gfo")

    converted = build_process_artifact_expectations((first, second))

    assert [item.path for item in converted] == [first.path, second.path]

    with pytest.raises(ValueError, match="declared more than once"):
        build_process_artifact_expectations((first, first))



def test_artifact_snapshot_missing_and_observation_conversion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    missing = ArtifactSnapshot.missing(path)
    observation = _observation(path, size_bytes=17)

    converted = ArtifactSnapshot.from_observation(observation)

    assert missing == ArtifactSnapshot(
        path=path,
        exists=False,
        is_file=False,
        size_bytes=None,
    )
    assert converted.path == path
    assert converted.exists is True
    assert converted.is_file is True
    assert converted.size_bytes == 17
    assert converted.modified_time_ns is None
    assert converted.sha256 is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"exists": False, "is_file": True, "size_bytes": None, "sha256": None},
        {"exists": False, "is_file": False, "size_bytes": 1, "sha256": None},
        {"exists": True, "is_file": False, "size_bytes": 1, "sha256": None},
        {"exists": True, "is_file": False, "size_bytes": None, "sha256": _SHA_A},
    ],
)
def test_artifact_snapshot_rejects_inconsistent_filesystem_facts(
    tmp_path: Path,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ArtifactSnapshot(path=tmp_path / "artifact", **kwargs)  # type: ignore[arg-type]



def test_provenance_validates_and_normalizes_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    provenance = ArtifactProvenance(
        path=path,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
        artifact_sha256=_SHA_B,
        producer="gf-3.12",
    )

    assert provenance.path == path
    assert provenance.operation_id == "compile:Grammar"
    assert provenance.source_fingerprint == _SHA_A
    assert provenance.artifact_sha256 == _SHA_B
    assert provenance.producer == "gf-3.12"

    with pytest.raises(ValueError, match="lowercase hexadecimal"):
        ArtifactProvenance(
            path=path,
            operation_id="compile:Grammar",
            artifact_sha256="A" * 64,
        )



def test_issue_blocking_depends_only_on_severity(tmp_path: Path) -> None:
    error = ArtifactIssue(
        code=ArtifactIssueCode.MISSING,
        severity=ArtifactIssueSeverity.ERROR,
        message="missing",
        path=tmp_path / "Grammar.gfo",
    )
    warning = ArtifactIssue(
        code=ArtifactIssueCode.UNEXPECTED_ARTIFACT,
        severity=ArtifactIssueSeverity.WARNING,
        message="unexpected",
    )

    assert error.blocking is True
    assert warning.blocking is False



def test_successful_verification_is_manifest_ready(
    tmp_path: Path,
) -> None:
    path = tmp_path / "artifacts" / "gfo" / "Grammar.gfo"
    expectation = _expectation(
        path,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
    )
    observation = _observation(path, size_bytes=21)
    after = _snapshot(
        path,
        size_bytes=21,
        sha256=_SHA_B,
        resolved_path=path,
    )
    provenance = ArtifactProvenance(
        path=path,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
        artifact_sha256=_SHA_B,
    )

    check = verify_compile_artifacts(
        (expectation,),
        (observation,),
        run_root=tmp_path,
        after_snapshots=(after,),
        provenance=(provenance,),
        manifest_paths=(path,),
        require_manifest_registration=True,
    )

    assert check.passed is True
    assert check.required_checks_passed is True
    assert check.manifest_ready is True
    assert check.expected_artifacts == (path,)
    assert check.produced_artifacts == (path,)
    assert check.unexpected_artifacts == ()
    assert check.issues == ()

    verification = check.artifacts[0]
    assert verification.run_relative_path is not None
    assert verification.run_relative_path.as_posix() == (
        "artifacts/gfo/Grammar.gfo"
    )
    assert verification.contained is True
    assert verification.exists is True
    assert verification.kind_matches is True
    assert verification.size_matches is True
    assert verification.freshness is ArtifactFreshness.CURRENT
    assert verification.manifest_registered is True
    assert verification.sha256 == _SHA_B
    assert verification.retained is True
    assert verification.passed is True



def test_identical_before_and_after_snapshot_is_stale(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path, request_isolated=False)
    observation = _observation(path)
    before = _snapshot(path, sha256=_SHA_A, modified_time_ns=10)
    after = _snapshot(path, sha256=_SHA_A, modified_time_ns=10)

    check = verify_compile_artifacts(
        (expectation,),
        (observation,),
        run_root=tmp_path,
        before_snapshots=(before,),
        after_snapshots=(after,),
    )

    assert check.passed is False
    assert check.artifacts[0].freshness is ArtifactFreshness.STALE
    assert ArtifactIssueCode.STALE in _codes(check)



def test_changed_snapshot_is_current(tmp_path: Path) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path, request_isolated=False)

    check = verify_compile_artifacts(
        (expectation,),
        (_observation(path),),
        run_root=tmp_path,
        before_snapshots=(_snapshot(path, sha256=_SHA_A),),
        after_snapshots=(_snapshot(path, sha256=_SHA_B),),
    )

    assert check.artifacts[0].freshness is ArtifactFreshness.CURRENT
    assert ArtifactIssueCode.STALE not in _codes(check)
    assert ArtifactIssueCode.FRESHNESS_UNKNOWN not in _codes(check)



def test_nonisolated_artifact_without_evidence_has_unknown_freshness(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path, request_isolated=False)

    check = verify_compile_artifacts(
        (expectation,),
        (_observation(path),),
        run_root=tmp_path,
    )

    assert check.artifacts[0].freshness is ArtifactFreshness.UNKNOWN
    assert ArtifactIssueCode.FRESHNESS_UNKNOWN in _codes(check)



def test_matching_provenance_proves_current_request(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(
        path,
        request_isolated=False,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
    )
    provenance = ArtifactProvenance(
        path=path,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
        artifact_sha256=_SHA_B,
    )

    check = verify_compile_artifacts(
        (expectation,),
        (_observation(path),),
        run_root=tmp_path,
        after_snapshots=(_snapshot(path, sha256=_SHA_B),),
        provenance=(provenance,),
    )

    assert check.artifacts[0].freshness is ArtifactFreshness.CURRENT
    assert ArtifactIssueCode.PROVENANCE_MISMATCH not in _codes(check)



def test_provenance_mismatch_is_blocking(tmp_path: Path) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(
        path,
        request_isolated=False,
        operation_id="compile:Grammar",
        source_fingerprint=_SHA_A,
    )
    provenance = ArtifactProvenance(
        path=path,
        operation_id="compile:Other",
        source_fingerprint=_SHA_B,
    )

    check = verify_compile_artifacts(
        (expectation,),
        (_observation(path),),
        run_root=tmp_path,
        provenance=(provenance,),
    )

    assert check.passed is False
    assert ArtifactIssueCode.PROVENANCE_MISMATCH in _codes(check)
    assert check.artifacts[0].freshness is ArtifactFreshness.UNKNOWN



def test_required_missing_artifact_is_blocking(tmp_path: Path) -> None:
    path = tmp_path / "Grammar.gfo"

    check = verify_compile_artifacts(
        (_expectation(path),),
        (),
        run_root=tmp_path,
    )

    assert check.passed is False
    assert check.required_checks_passed is False
    assert check.produced_artifacts == ()
    assert ArtifactIssueCode.OBSERVATION_MISSING in _codes(check)
    assert ArtifactIssueCode.MISSING in _codes(check)



def test_optional_missing_artifact_only_emits_warning(
    tmp_path: Path,
) -> None:
    path = tmp_path / "optional.gfo"
    expectation = _expectation(path, required=False)

    check = verify_compile_artifacts(
        (expectation,),
        (),
        run_root=tmp_path,
    )

    assert check.passed is True
    assert check.required_checks_passed is True
    assert _codes(check) == (ArtifactIssueCode.OBSERVATION_MISSING,)
    assert check.issues[0].severity is ArtifactIssueSeverity.WARNING



def test_observation_role_and_required_flag_must_match(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"

    check = verify_compile_artifacts(
        (_expectation(path),),
        (_observation(path, role="pgf", required=False),),
        run_root=tmp_path,
    )

    assert ArtifactIssueCode.ROLE_MISMATCH in _codes(check)
    assert ArtifactIssueCode.REQUIRED_FLAG_MISMATCH in _codes(check)
    assert check.passed is False


@pytest.mark.parametrize(
    ("observation", "expected_code"),
    [
        ({"exists": True, "kind_matches": False, "size_bytes": None}, ArtifactIssueCode.WRONG_KIND),
        ({"exists": True, "kind_matches": True, "size_bytes": 0}, ArtifactIssueCode.EMPTY),
        ({"exists": True, "kind_matches": True, "size_bytes": 3}, ArtifactIssueCode.SIZE_TOO_SMALL),
    ],
)
def test_kind_and_size_failures_are_classified(
    tmp_path: Path,
    observation: dict[str, object],
    expected_code: ArtifactIssueCode,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path, minimum_size_bytes=8)

    check = verify_compile_artifacts(
        (expectation,),
        (_observation(path, **observation),),  # type: ignore[arg-type]
        run_root=tmp_path,
    )

    assert expected_code in _codes(check)
    assert check.passed is False



def test_expectation_outside_run_root_is_unsafe(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    path = tmp_path / "outside.gfo"

    with pytest.raises(PathSecurityError, match="lexical containment"):
        verify_compile_artifacts(
            (_expectation(path),),
            (_observation(path),),
            run_root=run_root,
        )



def test_resolved_path_escape_is_unsafe(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    path = run_root / "Grammar.gfo"
    escaped = tmp_path / "escaped.gfo"

    with pytest.raises(PathSecurityError, match="lexical containment"):
        verify_compile_artifacts(
            (_expectation(path),),
            (_observation(path),),
            run_root=run_root,
            after_snapshots=(
                _snapshot(path, resolved_path=escaped),
            ),
        )



def test_symlink_is_rejected_unless_explicitly_allowed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path)
    observation = _observation(path)
    snapshot = _snapshot(path, is_symlink=True)

    rejected = verify_compile_artifacts(
        (expectation,),
        (observation,),
        run_root=tmp_path,
        after_snapshots=(snapshot,),
    )
    allowed = verify_compile_artifacts(
        (expectation,),
        (observation,),
        run_root=tmp_path,
        after_snapshots=(snapshot,),
        allow_symlinks=True,
    )

    assert ArtifactIssueCode.SYMLINK_PROHIBITED in _codes(rejected)
    assert ArtifactIssueCode.SYMLINK_PROHIBITED not in _codes(allowed)



def test_manifest_ready_requires_registration_and_hash(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path)
    observation = _observation(path)

    check = verify_compile_artifacts(
        (expectation,),
        (observation,),
        run_root=tmp_path,
        require_manifest_registration=True,
    )

    assert check.manifest_ready is False
    assert ArtifactIssueCode.MANIFEST_REGISTRATION_MISSING in _codes(check)
    assert ArtifactIssueCode.HASH_REQUIRED in _codes(check)



def test_unexpected_artifacts_are_retained_and_classified(
    tmp_path: Path,
) -> None:
    expected = tmp_path / "expected.gfo"
    inside = tmp_path / "extra.gfo"
    outside = tmp_path.parent / "outside.gfo"

    inside_check = verify_compile_artifacts(
        (_expectation(expected),),
        (_observation(expected), _observation(inside)),
        run_root=tmp_path,
    )
    assert inside_check.unexpected_artifacts == (_observation(inside),)
    assert ArtifactIssueCode.UNEXPECTED_ARTIFACT in _codes(inside_check)
    assert inside_check.passed is True

    with pytest.raises(PathSecurityError, match="lexical containment"):
        verify_compile_artifacts(
            (_expectation(expected),),
            (_observation(expected), _observation(outside)),
            run_root=tmp_path,
        )



def test_duplicate_inputs_are_reported_without_losing_first_observation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Grammar.gfo"
    expectation = _expectation(path)
    first = _observation(path, size_bytes=8)
    second = _observation(path, size_bytes=20)

    check = verify_compile_artifacts(
        (expectation, expectation),
        (first, second),
        run_root=tmp_path,
    )

    assert ArtifactIssueCode.DUPLICATE_EXPECTATION in _codes(check)
    assert ArtifactIssueCode.DUPLICATE_OBSERVATION in _codes(check)
    assert check.artifacts[0].observation is first
    assert check.artifacts[0].size_bytes == 8
    assert check.passed is False



def test_artifact_paths_by_role_is_sorted_and_immutable(
    tmp_path: Path,
) -> None:
    z_gfo = tmp_path / "z.gfo"
    a_gfo = tmp_path / "a.gfo"
    pgf = tmp_path / "Grammar.pgf"
    expectations = (
        _expectation(z_gfo),
        _expectation(pgf, role=CompileArtifactRole.PGF),
        _expectation(a_gfo),
    )
    observations = (
        _observation(z_gfo),
        _observation(pgf, role="pgf"),
        _observation(a_gfo),
    )

    check = verify_compile_artifacts(
        expectations,
        observations,
        run_root=tmp_path,
    )
    grouped = artifact_paths_by_role(check)

    assert isinstance(grouped, MappingProxyType)
    assert grouped[CompileArtifactRole.GFO] == (a_gfo, z_gfo)
    assert grouped[CompileArtifactRole.PGF] == (pgf,)
    assert grouped[CompileArtifactRole.OTHER] == ()

    with pytest.raises(TypeError):
        grouped[CompileArtifactRole.GFO] = ()  # type: ignore[index]



def test_issues_are_sorted_errors_before_warnings_and_by_path(
    tmp_path: Path,
) -> None:
    missing_b = tmp_path / "b.gfo"
    missing_a = tmp_path / "a.gfo"
    unexpected = tmp_path / "z.gfo"

    check = verify_compile_artifacts(
        (
            _expectation(missing_b),
            _expectation(missing_a),
        ),
        (_observation(unexpected),),
        run_root=tmp_path,
    )

    severities = [issue.severity for issue in check.issues]
    first_warning = severities.index(ArtifactIssueSeverity.WARNING)
    assert all(
        severity is ArtifactIssueSeverity.ERROR
        for severity in severities[:first_warning]
    )
    error_paths = [
        str(issue.path)
        for issue in check.issues[:first_warning]
    ]
    assert error_paths == sorted(error_paths)


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("expectations", "bad", "expectations must be an iterable"),
        ("observations", "bad", "observations must be an iterable"),
        ("before_snapshots", "bad", "snapshots must be an iterable"),
        ("provenance", "bad", "provenance must be an iterable"),
    ],
)
def test_verifier_rejects_scalar_iterables(
    tmp_path: Path,
    argument: str,
    value: object,
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "expectations": (),
        "observations": (),
        "run_root": tmp_path,
    }
    kwargs[argument] = value

    with pytest.raises(TypeError, match=message):
        verify_compile_artifacts(**kwargs)  # type: ignore[arg-type]



def test_artifact_paths_by_role_requires_artifact_check() -> None:
    with pytest.raises(TypeError, match="check must be an ArtifactCheck"):
        artifact_paths_by_role(object())  # type: ignore[arg-type]
