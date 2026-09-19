"""Compile-artifact expectations, freshness, and verification."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Final, Protocol, TypeVar

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ArtifactObservation,
)
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    path_identity_key,
    relative_portable_path,
    require_lexical_containment,
)

GFO_SUFFIX: Final[str] = ".gfo"
PGF_SUFFIX: Final[str] = ".pgf"
SHA256_HEX_LENGTH: Final[int] = 64


class _HasPath(Protocol):
    path: Path


_PathValueT = TypeVar("_PathValueT", bound=_HasPath)


@unique
class CompileArtifactRole(StrEnum):
    GFO = "gfo"
    PGF = "pgf"
    OTHER = "other"


@unique
class ArtifactFreshness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"
    MISSING = "missing"
    NOT_REQUIRED = "not_required"


@unique
class ArtifactIssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@unique
class ArtifactIssueCode(StrEnum):
    DUPLICATE_EXPECTATION = "duplicate_expectation"
    DUPLICATE_OBSERVATION = "duplicate_observation"
    OBSERVATION_MISSING = "observation_missing"
    ROLE_MISMATCH = "role_mismatch"
    REQUIRED_FLAG_MISMATCH = "required_flag_mismatch"
    UNSAFE_PATH = "unsafe_path"
    SYMLINK_PROHIBITED = "symlink_prohibited"
    MISSING = "missing"
    WRONG_KIND = "wrong_kind"
    EMPTY = "empty"
    SIZE_TOO_SMALL = "size_too_small"
    SIZE_MISMATCH = "size_mismatch"
    STALE = "stale"
    FRESHNESS_UNKNOWN = "freshness_unknown"
    PROVENANCE_MISMATCH = "provenance_mismatch"
    MANIFEST_REGISTRATION_MISSING = "manifest_registration_missing"
    HASH_REQUIRED = "hash_required"
    UNEXPECTED_ARTIFACT = "unexpected_artifact"
    UNEXPECTED_ARTIFACT_OUTSIDE_ROOT = "unexpected_artifact_outside_root"
    UNEXPECTED_ARTIFACT_CONFLICT = "unexpected_artifact_conflict"


@dataclass(frozen=True, slots=True)
class CompileArtifactExpectation:
    path: Path
    role: CompileArtifactRole
    required: bool = True
    minimum_size_bytes: int = 1
    freshness_required: bool = True
    manifest_required: bool = True
    request_isolated: bool = False
    operation_id: str | None = None
    source_fingerprint: str | None = None
    media_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, field_name="path")

        if not isinstance(self.role, CompileArtifactRole):
            raise TypeError("role must be a CompileArtifactRole")
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")
        if not isinstance(self.freshness_required, bool):
            raise TypeError("freshness_required must be a bool")
        if not isinstance(self.manifest_required, bool):
            raise TypeError("manifest_required must be a bool")
        if not isinstance(self.request_isolated, bool):
            raise TypeError("request_isolated must be a bool")

        _non_negative_integer(
            self.minimum_size_bytes,
            field_name="minimum_size_bytes",
        )

        operation_id = _optional_text(
            self.operation_id,
            field_name="operation_id",
        )
        source_fingerprint = _optional_sha256(
            self.source_fingerprint,
            field_name="source_fingerprint",
        )
        media_type = _required_text(
            self.media_type,
            field_name="media_type",
        )

        _validate_role_suffix(path, self.role)

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(
            self,
            "source_fingerprint",
            source_fingerprint,
        )
        object.__setattr__(self, "media_type", media_type)

    def to_process_expectation(self) -> ArtifactExpectation:
        return ArtifactExpectation(
            path=self.path,
            role=self.role.value,
            required=self.required,
            kind=ArtifactKind.FILE,
            minimum_size_bytes=self.minimum_size_bytes,
        )


@dataclass(frozen=True, slots=True)
class ArtifactSnapshot:
    path: Path
    exists: bool
    is_file: bool
    size_bytes: int | None
    modified_time_ns: int | None = None
    sha256: str | None = None
    resolved_path: Path | None = None
    is_symlink: bool = False

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, field_name="path")

        for field_name in ("exists", "is_file", "is_symlink"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")

        _optional_non_negative_integer(
            self.size_bytes,
            field_name="size_bytes",
        )
        _optional_non_negative_integer(
            self.modified_time_ns,
            field_name="modified_time_ns",
        )

        sha256 = _optional_sha256(
            self.sha256,
            field_name="sha256",
        )

        resolved_path = self.resolved_path
        if resolved_path is not None:
            resolved_path = _absolute_path(
                resolved_path,
                field_name="resolved_path",
            )

        if not self.exists:
            if self.is_file:
                raise ValueError("a missing artifact cannot be a regular file")
            if self.size_bytes is not None:
                raise ValueError("a missing artifact cannot report size_bytes")
            if self.modified_time_ns is not None:
                raise ValueError("a missing artifact cannot report modified_time_ns")
            if sha256 is not None:
                raise ValueError("a missing artifact cannot report sha256")
            if self.is_symlink:
                raise ValueError("a missing artifact cannot be a symlink")

        if self.exists and not self.is_file and self.size_bytes is not None:
            raise ValueError("a non-file artifact cannot report a file size")

        if sha256 is not None and not self.is_file:
            raise ValueError("sha256 is valid only for a regular file")

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "sha256", sha256)
        object.__setattr__(self, "resolved_path", resolved_path)

    @classmethod
    def missing(cls, path: Path) -> ArtifactSnapshot:
        return cls(
            path=path,
            exists=False,
            is_file=False,
            size_bytes=None,
        )

    @classmethod
    def from_observation(
        cls,
        observation: ArtifactObservation,
    ) -> ArtifactSnapshot:
        if not isinstance(observation, ArtifactObservation):
            raise TypeError("observation must be an ArtifactObservation")

        return cls(
            path=observation.path,
            exists=observation.exists,
            is_file=(observation.exists and observation.kind_matches),
            size_bytes=observation.size_bytes,
        )


@dataclass(frozen=True, slots=True)
class ArtifactProvenance:
    path: Path
    operation_id: str
    source_fingerprint: str | None = None
    artifact_sha256: str | None = None
    producer: str = "gf"

    def __post_init__(self) -> None:
        path = _absolute_path(self.path, field_name="path")
        operation_id = _required_text(
            self.operation_id,
            field_name="operation_id",
        )
        source_fingerprint = _optional_sha256(
            self.source_fingerprint,
            field_name="source_fingerprint",
        )
        artifact_sha256 = _optional_sha256(
            self.artifact_sha256,
            field_name="artifact_sha256",
        )
        producer = _required_text(
            self.producer,
            field_name="producer",
        )

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(
            self,
            "source_fingerprint",
            source_fingerprint,
        )
        object.__setattr__(
            self,
            "artifact_sha256",
            artifact_sha256,
        )
        object.__setattr__(self, "producer", producer)


@dataclass(frozen=True, slots=True)
class ArtifactIssue:
    code: ArtifactIssueCode
    severity: ArtifactIssueSeverity
    message: str
    path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ArtifactIssueCode):
            raise TypeError("code must be an ArtifactIssueCode")
        if not isinstance(self.severity, ArtifactIssueSeverity):
            raise TypeError("severity must be an ArtifactIssueSeverity")

        message = _required_text(
            self.message,
            field_name="message",
        )

        path = self.path
        if path is not None:
            path = _absolute_path(path, field_name="path")

        object.__setattr__(self, "message", message)
        object.__setattr__(self, "path", path)

    @property
    def blocking(self) -> bool:
        return self.severity is ArtifactIssueSeverity.ERROR


@dataclass(frozen=True, slots=True)
class ArtifactVerification:
    expectation: CompileArtifactExpectation
    observation: ArtifactObservation | None
    before: ArtifactSnapshot | None
    after: ArtifactSnapshot | None
    provenance: ArtifactProvenance | None
    run_relative_path: PurePosixPath | None
    contained: bool
    kind_matches: bool
    size_matches: bool
    freshness: ArtifactFreshness
    manifest_registered: bool
    issues: tuple[ArtifactIssue, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.expectation,
            CompileArtifactExpectation,
        ):
            raise TypeError("expectation must be a CompileArtifactExpectation")

        if self.observation is not None and not isinstance(
            self.observation,
            ArtifactObservation,
        ):
            raise TypeError("observation must be an ArtifactObservation or None")

        for field_name in ("before", "after"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(
                value,
                ArtifactSnapshot,
            ):
                raise TypeError(f"{field_name} must be an ArtifactSnapshot or None")

        if self.provenance is not None and not isinstance(
            self.provenance,
            ArtifactProvenance,
        ):
            raise TypeError("provenance must be an ArtifactProvenance or None")

        for field_name in (
            "contained",
            "kind_matches",
            "size_matches",
            "manifest_registered",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")

        if not isinstance(self.freshness, ArtifactFreshness):
            raise TypeError("freshness must be an ArtifactFreshness")

        issues = tuple(self.issues)
        if not all(isinstance(issue, ArtifactIssue) for issue in issues):
            raise TypeError("issues must contain ArtifactIssue values")

        object.__setattr__(self, "issues", issues)

    @property
    def exists(self) -> bool:
        if self.after is not None:
            return self.after.exists
        if self.observation is not None:
            return self.observation.exists
        return False

    @property
    def size_bytes(self) -> int | None:
        if self.after is not None:
            return self.after.size_bytes
        if self.observation is not None:
            return self.observation.size_bytes
        return None

    @property
    def sha256(self) -> str | None:
        if self.after is not None and self.after.sha256 is not None:
            return self.after.sha256
        if self.provenance is not None:
            return self.provenance.artifact_sha256
        return None

    @property
    def passed(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def retained(self) -> bool:
        return self.exists and self.kind_matches and self.contained


@dataclass(frozen=True, slots=True)
class ArtifactCheck:
    artifacts: tuple[ArtifactVerification, ...]
    unexpected_artifacts: tuple[ArtifactObservation, ...]
    issues: tuple[ArtifactIssue, ...]

    def __post_init__(self) -> None:
        artifacts = tuple(self.artifacts)
        unexpected_artifacts = tuple(self.unexpected_artifacts)
        issues = tuple(self.issues)

        if not all(isinstance(item, ArtifactVerification) for item in artifacts):
            raise TypeError("artifacts must contain ArtifactVerification values")
        if not all(isinstance(item, ArtifactObservation) for item in unexpected_artifacts):
            raise TypeError("unexpected_artifacts must contain ArtifactObservation values")
        if not all(isinstance(item, ArtifactIssue) for item in issues):
            raise TypeError("issues must contain ArtifactIssue values")

        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(
            self,
            "unexpected_artifacts",
            unexpected_artifacts,
        )
        object.__setattr__(self, "issues", issues)

    @property
    def passed(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def required_checks_passed(self) -> bool:
        return all(
            verification.passed
            for verification in self.artifacts
            if verification.expectation.required
        )

    @property
    def produced_artifacts(self) -> tuple[Path, ...]:
        return tuple(
            verification.expectation.path
            for verification in self.artifacts
            if verification.retained
        )

    @property
    def expected_artifacts(self) -> tuple[Path, ...]:
        return tuple(verification.expectation.path for verification in self.artifacts)

    @property
    def retained_artifacts(
        self,
    ) -> tuple[ArtifactVerification, ...]:
        return tuple(verification for verification in self.artifacts if verification.retained)

    @property
    def manifest_ready(self) -> bool:
        return self.passed and all(
            (not verification.expectation.manifest_required or verification.manifest_registered)
            for verification in self.artifacts
            if verification.retained
        )


def required_gfo_expectation(
    *,
    path: Path,
    operation_id: str | None = None,
    source_fingerprint: str | None = None,
    request_isolated: bool = True,
) -> CompileArtifactExpectation:
    return CompileArtifactExpectation(
        path=path,
        role=CompileArtifactRole.GFO,
        required=True,
        minimum_size_bytes=1,
        freshness_required=True,
        manifest_required=True,
        request_isolated=request_isolated,
        operation_id=operation_id,
        source_fingerprint=source_fingerprint,
        media_type="application/octet-stream",
    )


def required_pgf_expectation(
    *,
    path: Path,
    operation_id: str | None = None,
    source_fingerprint: str | None = None,
    request_isolated: bool = True,
) -> CompileArtifactExpectation:
    return CompileArtifactExpectation(
        path=path,
        role=CompileArtifactRole.PGF,
        required=True,
        minimum_size_bytes=1,
        freshness_required=True,
        manifest_required=True,
        request_isolated=request_isolated,
        operation_id=operation_id,
        source_fingerprint=source_fingerprint,
        media_type="application/octet-stream",
    )


def build_process_artifact_expectations(
    expectations: Iterable[CompileArtifactExpectation],
) -> tuple[ArtifactExpectation, ...]:
    normalized = _expectation_tuple(expectations)
    _ensure_unique_expectations(normalized)

    return tuple(expectation.to_process_expectation() for expectation in normalized)


def verify_compile_artifacts(
    expectations: Iterable[CompileArtifactExpectation],
    observations: Iterable[ArtifactObservation],
    *,
    run_root: Path,
    before_snapshots: Iterable[ArtifactSnapshot] = (),
    after_snapshots: Iterable[ArtifactSnapshot] = (),
    provenance: Iterable[ArtifactProvenance] = (),
    manifest_paths: Iterable[Path] = (),
    require_manifest_registration: bool = False,
    allow_symlinks: bool = False,
) -> ArtifactCheck:
    run_root = _absolute_path(
        run_root,
        field_name="run_root",
    )
    expectations_tuple = _expectation_tuple(expectations)
    observations_tuple = _observation_tuple(observations)
    before_tuple = _snapshot_tuple(before_snapshots)
    after_tuple = _snapshot_tuple(after_snapshots)
    provenance_tuple = _provenance_tuple(provenance)
    manifest_tuple = tuple(
        _absolute_path(path, field_name="manifest path") for path in manifest_paths
    )

    duplicate_expectation_issues = _duplicate_expectation_issues(expectations_tuple)
    duplicate_observation_issues = _duplicate_observation_issues(observations_tuple)

    observation_map = _unique_map_by_path(
        observations_tuple,
        field_name="observations",
    )
    before_map = _unique_map_by_path(
        before_tuple,
        field_name="before_snapshots",
    )
    after_map = _unique_map_by_path(
        after_tuple,
        field_name="after_snapshots",
    )
    provenance_map = _unique_map_by_path(
        provenance_tuple,
        field_name="provenance",
    )
    manifest_keys = frozenset(
        path_identity_key(path, role="manifest artifact path") for path in manifest_tuple
    )

    verifications: list[ArtifactVerification] = []
    issues: list[ArtifactIssue] = [
        *duplicate_expectation_issues,
        *duplicate_observation_issues,
    ]

    expected_keys = {
        path_identity_key(
            expectation.path,
            role="compile artifact expectation path",
        )
        for expectation in expectations_tuple
    }

    for expectation in expectations_tuple:
        key = path_identity_key(
            expectation.path,
            role="compile artifact expectation path",
        )

        observation = observation_map.get(key)
        before = before_map.get(key)
        after = after_map.get(key)
        artifact_provenance = provenance_map.get(key)
        registered = key in manifest_keys

        verification = _verify_one(
            expectation,
            observation=observation,
            before=before,
            after=after,
            provenance=artifact_provenance,
            run_root=run_root,
            manifest_registered=registered,
            require_manifest_registration=(require_manifest_registration),
            allow_symlinks=allow_symlinks,
        )
        verifications.append(verification)
        issues.extend(verification.issues)

    unexpected: list[ArtifactObservation] = []
    for observation in observations_tuple:
        key = path_identity_key(
            observation.path,
            role="observed compile artifact path",
        )
        if key in expected_keys:
            continue

        unexpected.append(observation)
        unexpected_issue = _unexpected_issue(
            observation,
            run_root=run_root,
            expected_keys=expected_keys,
        )
        issues.append(unexpected_issue)

    ordered_verifications = tuple(
        sorted(
            verifications,
            key=lambda item: (
                item.run_relative_path.as_posix()
                if item.run_relative_path is not None
                else str(item.expectation.path)
            ),
        )
    )
    ordered_unexpected = tuple(
        sorted(
            unexpected,
            key=lambda item: path_identity_key(
                item.path,
                role="unexpected artifact path",
            ),
        )
    )
    ordered_issues = tuple(
        sorted(
            issues,
            key=_issue_sort_key,
        )
    )

    return ArtifactCheck(
        artifacts=ordered_verifications,
        unexpected_artifacts=ordered_unexpected,
        issues=ordered_issues,
    )


def artifact_paths_by_role(
    check: ArtifactCheck,
) -> Mapping[CompileArtifactRole, tuple[Path, ...]]:
    if not isinstance(check, ArtifactCheck):
        raise TypeError("check must be an ArtifactCheck")

    grouped: dict[CompileArtifactRole, list[Path]] = {role: [] for role in CompileArtifactRole}

    for verification in check.retained_artifacts:
        grouped[verification.expectation.role].append(verification.expectation.path)

    return MappingProxyType(
        {
            role: tuple(
                sorted(
                    paths,
                    key=lambda path: path_identity_key(
                        path,
                        role=f"{role.value} artifact path",
                    ),
                )
            )
            for role, paths in grouped.items()
        }
    )


def _verify_one(
    expectation: CompileArtifactExpectation,
    *,
    observation: ArtifactObservation | None,
    before: ArtifactSnapshot | None,
    after: ArtifactSnapshot | None,
    provenance: ArtifactProvenance | None,
    run_root: Path,
    manifest_registered: bool,
    require_manifest_registration: bool,
    allow_symlinks: bool,
) -> ArtifactVerification:
    issues: list[ArtifactIssue] = []
    severity = _expectation_severity(expectation)

    run_relative_path: PurePosixPath | None = None
    contained = False

    try:
        require_lexical_containment(
            run_root,
            expectation.path,
            role="compile artifact path",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
        run_relative_path = relative_portable_path(
            run_root,
            expectation.path,
            role="compile artifact path",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
        contained = True
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.UNSAFE_PATH,
                severity=ArtifactIssueSeverity.ERROR,
                message=str(exc),
                path=expectation.path,
            )
        )

    if after is not None and after.resolved_path is not None:
        try:
            require_lexical_containment(
                run_root,
                after.resolved_path,
                role="resolved compile artifact path",
                mode=ContainmentMode.STRICTLY_INSIDE,
            )
        except (TypeError, ValueError, OSError, RuntimeError) as exc:
            contained = False
            issues.append(
                ArtifactIssue(
                    code=ArtifactIssueCode.UNSAFE_PATH,
                    severity=ArtifactIssueSeverity.ERROR,
                    message=str(exc),
                    path=expectation.path,
                )
            )

    if after is not None and after.is_symlink and not allow_symlinks:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.SYMLINK_PROHIBITED,
                severity=ArtifactIssueSeverity.ERROR,
                message=("compile artifacts must not be symbolic links"),
                path=expectation.path,
            )
        )

    if observation is None:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.OBSERVATION_MISSING,
                severity=severity,
                message=(
                    "the process result contains no observation for the expected compile artifact"
                ),
                path=expectation.path,
            )
        )
    else:
        if observation.role != expectation.role.value:
            issues.append(
                ArtifactIssue(
                    code=ArtifactIssueCode.ROLE_MISMATCH,
                    severity=severity,
                    message=(
                        "artifact observation role does not match "
                        f"the expected role {expectation.role.value!r}"
                    ),
                    path=expectation.path,
                )
            )
        if observation.required is not expectation.required:
            issues.append(
                ArtifactIssue(
                    code=ArtifactIssueCode.REQUIRED_FLAG_MISMATCH,
                    severity=severity,
                    message=(
                        "artifact observation required flag does not match the compile expectation"
                    ),
                    path=expectation.path,
                )
            )

    effective_after = after
    if effective_after is None and observation is not None:
        effective_after = ArtifactSnapshot.from_observation(observation)

    exists = effective_after.exists if effective_after is not None else False
    kind_matches = effective_after.is_file if effective_after is not None else False
    size_bytes = effective_after.size_bytes if effective_after is not None else None
    size_matches = size_bytes is not None and size_bytes >= expectation.minimum_size_bytes

    if not exists:
        if expectation.required:
            issues.append(
                ArtifactIssue(
                    code=ArtifactIssueCode.MISSING,
                    severity=ArtifactIssueSeverity.ERROR,
                    message="required compile artifact is missing",
                    path=expectation.path,
                )
            )
    elif not kind_matches:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.WRONG_KIND,
                severity=severity,
                message=("compile artifact is not a regular file"),
                path=expectation.path,
            )
        )
    elif size_bytes is None:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.SIZE_MISMATCH,
                severity=severity,
                message=("compile artifact size was not observed"),
                path=expectation.path,
            )
        )
    elif size_bytes == 0 and expectation.minimum_size_bytes > 0:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.EMPTY,
                severity=severity,
                message="compile artifact is empty",
                path=expectation.path,
            )
        )
    elif size_bytes < expectation.minimum_size_bytes:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.SIZE_TOO_SMALL,
                severity=severity,
                message=(
                    "compile artifact is smaller than the required "
                    f"minimum of {expectation.minimum_size_bytes} bytes"
                ),
                path=expectation.path,
            )
        )

    freshness = _evaluate_freshness(
        expectation,
        before=before,
        after=effective_after,
        provenance=provenance,
    )

    if expectation.freshness_required and exists and freshness is ArtifactFreshness.STALE:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.STALE,
                severity=severity,
                message=("compile artifact is not proven to belong to the current request"),
                path=expectation.path,
            )
        )
    elif expectation.freshness_required and exists and freshness is ArtifactFreshness.UNKNOWN:
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.FRESHNESS_UNKNOWN,
                severity=severity,
                message=("compile artifact freshness could not be proven"),
                path=expectation.path,
            )
        )

    provenance_issue = _provenance_issue(
        expectation,
        provenance=provenance,
    )
    if provenance_issue is not None:
        issues.append(provenance_issue)

    if (
        require_manifest_registration
        and expectation.manifest_required
        and exists
        and not manifest_registered
    ):
        issues.append(
            ArtifactIssue(
                code=(ArtifactIssueCode.MANIFEST_REGISTRATION_MISSING),
                severity=severity,
                message=("retained compile artifact is not registered for manifest publication"),
                path=expectation.path,
            )
        )

    if (
        require_manifest_registration
        and expectation.manifest_required
        and exists
        and effective_after is not None
        and effective_after.sha256 is None
        and (provenance is None or provenance.artifact_sha256 is None)
    ):
        issues.append(
            ArtifactIssue(
                code=ArtifactIssueCode.HASH_REQUIRED,
                severity=severity,
                message=("manifest-ready compile artifact requires a finalized SHA-256 digest"),
                path=expectation.path,
            )
        )

    return ArtifactVerification(
        expectation=expectation,
        observation=observation,
        before=before,
        after=effective_after,
        provenance=provenance,
        run_relative_path=run_relative_path,
        contained=contained,
        kind_matches=kind_matches,
        size_matches=size_matches,
        freshness=freshness,
        manifest_registered=manifest_registered,
        issues=tuple(issues),
    )


def _evaluate_freshness(
    expectation: CompileArtifactExpectation,
    *,
    before: ArtifactSnapshot | None,
    after: ArtifactSnapshot | None,
    provenance: ArtifactProvenance | None,
) -> ArtifactFreshness:
    if not expectation.freshness_required:
        return ArtifactFreshness.NOT_REQUIRED

    if after is None or not after.exists:
        return ArtifactFreshness.MISSING

    if _provenance_matches(expectation, provenance):
        if (
            provenance is not None
            and provenance.artifact_sha256 is not None
            and after.sha256 is not None
            and provenance.artifact_sha256 != after.sha256
        ):
            return ArtifactFreshness.STALE
        return ArtifactFreshness.CURRENT

    if before is not None:
        if not before.exists:
            return ArtifactFreshness.CURRENT

        if before.sha256 is not None and after.sha256 is not None:
            if before.sha256 != after.sha256:
                return ArtifactFreshness.CURRENT
            return ArtifactFreshness.STALE

        if (
            before.modified_time_ns is not None
            and after.modified_time_ns is not None
            and before.modified_time_ns != after.modified_time_ns
        ):
            return ArtifactFreshness.CURRENT

        if (
            before.size_bytes is not None
            and after.size_bytes is not None
            and before.size_bytes != after.size_bytes
        ):
            return ArtifactFreshness.CURRENT

        return ArtifactFreshness.STALE

    if expectation.request_isolated:
        return ArtifactFreshness.CURRENT

    return ArtifactFreshness.UNKNOWN


def _provenance_matches(
    expectation: CompileArtifactExpectation,
    provenance: ArtifactProvenance | None,
) -> bool:
    if provenance is None:
        return False

    if expectation.operation_id is not None and provenance.operation_id != expectation.operation_id:
        return False

    if (
        expectation.source_fingerprint is not None
        and provenance.source_fingerprint != expectation.source_fingerprint
    ):
        return False

    return expectation.operation_id is not None or expectation.source_fingerprint is not None


def _provenance_issue(
    expectation: CompileArtifactExpectation,
    *,
    provenance: ArtifactProvenance | None,
) -> ArtifactIssue | None:
    if provenance is None:
        return None

    if expectation.operation_id is not None and provenance.operation_id != expectation.operation_id:
        return ArtifactIssue(
            code=ArtifactIssueCode.PROVENANCE_MISMATCH,
            severity=_expectation_severity(expectation),
            message=("artifact provenance operation_id does not match the current compile request"),
            path=expectation.path,
        )

    if (
        expectation.source_fingerprint is not None
        and provenance.source_fingerprint != expectation.source_fingerprint
    ):
        return ArtifactIssue(
            code=ArtifactIssueCode.PROVENANCE_MISMATCH,
            severity=_expectation_severity(expectation),
            message=(
                "artifact provenance source fingerprint does not "
                "match the current compile source state"
            ),
            path=expectation.path,
        )

    return None


def _unexpected_issue(
    observation: ArtifactObservation,
    *,
    run_root: Path,
    expected_keys: set[str],
) -> ArtifactIssue:
    try:
        require_lexical_containment(
            run_root,
            observation.path,
            role="unexpected compile artifact path",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        return ArtifactIssue(
            code=(ArtifactIssueCode.UNEXPECTED_ARTIFACT_OUTSIDE_ROOT),
            severity=ArtifactIssueSeverity.ERROR,
            message=str(exc),
            path=observation.path,
        )

    key = path_identity_key(
        observation.path,
        role="unexpected compile artifact path",
    )
    if key in expected_keys:
        return ArtifactIssue(
            code=ArtifactIssueCode.UNEXPECTED_ARTIFACT_CONFLICT,
            severity=ArtifactIssueSeverity.ERROR,
            message=("unexpected artifact conflicts with an expected artifact identity"),
            path=observation.path,
        )

    return ArtifactIssue(
        code=ArtifactIssueCode.UNEXPECTED_ARTIFACT,
        severity=ArtifactIssueSeverity.WARNING,
        message=("compile operation produced an undeclared artifact"),
        path=observation.path,
    )


def _duplicate_expectation_issues(
    expectations: tuple[CompileArtifactExpectation, ...],
) -> tuple[ArtifactIssue, ...]:
    seen: set[str] = set()
    issues: list[ArtifactIssue] = []

    for expectation in expectations:
        key = path_identity_key(
            expectation.path,
            role="compile artifact expectation path",
        )
        if key in seen:
            issues.append(
                ArtifactIssue(
                    code=(ArtifactIssueCode.DUPLICATE_EXPECTATION),
                    severity=ArtifactIssueSeverity.ERROR,
                    message=("compile artifact expectation path is declared more than once"),
                    path=expectation.path,
                )
            )
        seen.add(key)

    return tuple(issues)


def _duplicate_observation_issues(
    observations: tuple[ArtifactObservation, ...],
) -> tuple[ArtifactIssue, ...]:
    seen: set[str] = set()
    issues: list[ArtifactIssue] = []

    for observation in observations:
        key = path_identity_key(
            observation.path,
            role="observed compile artifact path",
        )
        if key in seen:
            issues.append(
                ArtifactIssue(
                    code=(ArtifactIssueCode.DUPLICATE_OBSERVATION),
                    severity=ArtifactIssueSeverity.ERROR,
                    message=("compile artifact was observed more than once"),
                    path=observation.path,
                )
            )
        seen.add(key)

    return tuple(issues)


def _ensure_unique_expectations(
    expectations: tuple[CompileArtifactExpectation, ...],
) -> None:
    issues = _duplicate_expectation_issues(expectations)
    if issues:
        raise ValueError(issues[0].message)


def _unique_map_by_path(
    values: tuple[_PathValueT, ...],
    *,
    field_name: str,
) -> Mapping[str, _PathValueT]:
    result: dict[str, _PathValueT] = {}

    for value in values:
        path = value.path
        if not isinstance(path, Path):
            raise TypeError(f"every {field_name} value must expose a Path")

        key = path_identity_key(
            path,
            role=f"{field_name} path",
        )
        result.setdefault(key, value)

    return MappingProxyType(result)


def _expectation_tuple(
    values: object,
) -> tuple[CompileArtifactExpectation, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("expectations must be an iterable of CompileArtifactExpectation values")

    result = tuple(values)
    if not all(isinstance(item, CompileArtifactExpectation) for item in result):
        raise TypeError("expectations must contain CompileArtifactExpectation values")
    return result


def _observation_tuple(
    values: object,
) -> tuple[ArtifactObservation, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("observations must be an iterable of ArtifactObservation values")

    result = tuple(values)
    if not all(isinstance(item, ArtifactObservation) for item in result):
        raise TypeError("observations must contain ArtifactObservation values")
    return result


def _snapshot_tuple(
    values: object,
) -> tuple[ArtifactSnapshot, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("snapshots must be an iterable of ArtifactSnapshot values")

    result = tuple(values)
    if not all(isinstance(item, ArtifactSnapshot) for item in result):
        raise TypeError("snapshots must contain ArtifactSnapshot values")
    return result


def _provenance_tuple(
    values: object,
) -> tuple[ArtifactProvenance, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("provenance must be an iterable of ArtifactProvenance values")

    result = tuple(values)
    if not all(isinstance(item, ArtifactProvenance) for item in result):
        raise TypeError("provenance must contain ArtifactProvenance values")
    return result


def _expectation_severity(
    expectation: CompileArtifactExpectation,
) -> ArtifactIssueSeverity:
    if expectation.required:
        return ArtifactIssueSeverity.ERROR
    return ArtifactIssueSeverity.WARNING


def _issue_sort_key(
    issue: ArtifactIssue,
) -> tuple[int, str, str, str]:
    severity_order = 0 if issue.severity is ArtifactIssueSeverity.ERROR else 1
    path_text = str(issue.path) if issue.path is not None else ""
    return (
        severity_order,
        path_text,
        issue.code.value,
        issue.message,
    )


def _validate_role_suffix(
    path: Path,
    role: CompileArtifactRole,
) -> None:
    suffix = path.suffix.lower()

    if role is CompileArtifactRole.GFO and suffix != GFO_SUFFIX:
        raise ValueError(f"gfo artifact path must end with {GFO_SUFFIX!r}")
    if role is CompileArtifactRole.PGF and suffix != PGF_SUFFIX:
        raise ValueError(f"pgf artifact path must end with {PGF_SUFFIX!r}")


def _absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return value


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
    return value


def _optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name=field_name)


def _non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    return _non_negative_integer(
        value,
        field_name=field_name,
    )


def _optional_sha256(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(
            f"{field_name} must contain exactly {SHA256_HEX_LENGTH} hexadecimal digits"
        )
    if value.lower() != value:
        raise ValueError(f"{field_name} must use lowercase hexadecimal digits")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must contain only hexadecimal digits")
    return value


__all__ = (
    "GFO_SUFFIX",
    "PGF_SUFFIX",
    "ArtifactCheck",
    "ArtifactFreshness",
    "ArtifactIssue",
    "ArtifactIssueCode",
    "ArtifactIssueSeverity",
    "ArtifactProvenance",
    "ArtifactSnapshot",
    "ArtifactVerification",
    "CompileArtifactExpectation",
    "CompileArtifactRole",
    "artifact_paths_by_role",
    "build_process_artifact_expectations",
    "required_gfo_expectation",
    "required_pgf_expectation",
    "verify_compile_artifacts",
)
