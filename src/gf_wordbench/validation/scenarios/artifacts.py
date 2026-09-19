"""Scenario-owned artifact paths, publication, and integrity verification."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.infrastructure.atomic_io import (
    atomic_write_bytes,
    atomic_write_text,
)
from gf_wordbench.infrastructure.filesystem import (
    PathContainmentError,
    require_directory,
    require_regular_file,
    require_within,
    resolve_for_output,
)
from gf_wordbench.kernel.errors import (
    ArtifactError,
    EvidenceIOError,
    PathSecurityError,
)
from gf_wordbench.kernel.ids import ScenarioId, validate_scenario_id

PathInput: TypeAlias = str | os.PathLike[str]


@runtime_checkable
class _ScenarioSpecLike(Protocol):
    scenario_id: object


@runtime_checkable
class _RunPathsLike(Protocol):
    run_dir: PathInput


MAX_SAFE_KEY_LENGTH: Final[int] = 96
MAX_GENERATED_BASENAME_LENGTH: Final[int] = 120
HASH_SUFFIX_LENGTH: Final[int] = 8
HASH_CHUNK_SIZE: Final[int] = 1024 * 1024

STDOUT_SUFFIX: Final[str] = ".stdout.txt"
STDERR_SUFFIX: Final[str] = ".stderr.txt"
NORMALIZED_OUTPUT_SUFFIX: Final[str] = ".out"
GOLD_DIFF_SUFFIX: Final[str] = ".gold.diff"

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]*$")
_PORTABLE_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._-]+$")
_WINDOWS_RESERVED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{number}" for number in range(1, 10)),
        *(f"lpt{number}" for number in range(1, 10)),
    }
)


@unique
class ScenarioArtifactKind(StrEnum):
    STDOUT = "scenario_stdout"
    STDERR = "scenario_stderr"
    NORMALIZED_OUTPUT = "scenario_normalized_output"
    GOLD_DIFF = "scenario_gold_diff"
    GENERATED_OUTPUT = "scenario_generated_output"


@dataclass(frozen=True, slots=True)
class ScenarioArtifactPaths:
    scenario_id: ScenarioId
    safe_key: str
    run_directory: Path
    raw_scenarios_directory: Path
    generated_output_directory: Path
    stdout_path: Path
    stderr_path: Path
    normalized_output_path: Path
    gold_diff_path: Path

    def __post_init__(self) -> None:
        validate_scenario_id(self.scenario_id)
        _validate_safe_key(self.safe_key)

        for field_name in (
            "run_directory",
            "raw_scenarios_directory",
            "generated_output_directory",
            "stdout_path",
            "stderr_path",
            "normalized_output_path",
            "gold_diff_path",
        ):
            path = getattr(self, field_name)
            if not isinstance(path, Path):
                raise TypeError(f"{field_name} must be a Path")
            if not path.is_absolute():
                raise ValueError(f"{field_name} must be absolute")

        if self.raw_scenarios_directory == self.run_directory:
            raise ValueError("raw_scenarios_directory must be below run_directory")
        if self.generated_output_directory == self.run_directory:
            raise ValueError("generated_output_directory must be below run_directory")

        expected = {
            "stdout_path": (self.raw_scenarios_directory / f"{self.safe_key}{STDOUT_SUFFIX}"),
            "stderr_path": (self.raw_scenarios_directory / f"{self.safe_key}{STDERR_SUFFIX}"),
            "normalized_output_path": (
                self.raw_scenarios_directory / f"{self.safe_key}{NORMALIZED_OUTPUT_SUFFIX}"
            ),
            "gold_diff_path": (self.raw_scenarios_directory / f"{self.safe_key}{GOLD_DIFF_SUFFIX}"),
        }
        for field_name, expected_path in expected.items():
            if getattr(self, field_name) != expected_path:
                raise ValueError(
                    f"{field_name} does not match the canonical scenario artifact name"
                )

        for path in (
            self.raw_scenarios_directory,
            self.generated_output_directory,
            self.stdout_path,
            self.stderr_path,
            self.normalized_output_path,
            self.gold_diff_path,
        ):
            try:
                path.relative_to(self.run_directory)
            except ValueError as exc:
                raise ValueError("scenario artifact paths must remain below run_directory") from exc

    def path_for(self, kind: ScenarioArtifactKind) -> Path:
        if not isinstance(kind, ScenarioArtifactKind):
            raise TypeError("kind must be a ScenarioArtifactKind")
        if kind is ScenarioArtifactKind.STDOUT:
            return self.stdout_path
        if kind is ScenarioArtifactKind.STDERR:
            return self.stderr_path
        if kind is ScenarioArtifactKind.NORMALIZED_OUTPUT:
            return self.normalized_output_path
        if kind is ScenarioArtifactKind.GOLD_DIFF:
            return self.gold_diff_path
        raise ValueError("generated output artifacts require an explicit existing path")

    def run_relative(self, path: PathInput) -> str:
        return run_relative_artifact_path(
            path,
            run_directory=self.run_directory,
        )


@dataclass(frozen=True, slots=True)
class GoldDiffMetadata:
    scenario_id: ScenarioId
    gold_path: str
    actual_normalized_output_path: str
    comparison_result: str
    normalization_version: str

    def __post_init__(self) -> None:
        validate_scenario_id(self.scenario_id)
        _validate_portable_relative_path(
            self.gold_path,
            field="gold_path",
        )
        _validate_portable_relative_path(
            self.actual_normalized_output_path,
            field="actual_normalized_output_path",
        )
        _validate_token(
            self.comparison_result,
            field="comparison_result",
        )
        _validate_metadata_text(
            self.normalization_version,
            field="normalization_version",
        )


@dataclass(frozen=True, slots=True)
class ScenarioArtifactRecord:
    scenario_id: ScenarioId
    kind: ScenarioArtifactKind
    path: Path
    run_relative_path: str
    size_bytes: int
    sha256: str
    media_type: str
    source_run_relative_path: str | None = None
    normalization_version: str | None = None

    def __post_init__(self) -> None:
        validate_scenario_id(self.scenario_id)
        if not isinstance(self.kind, ScenarioArtifactKind):
            raise TypeError("kind must be a ScenarioArtifactKind")
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")
        if not self.path.is_absolute():
            raise ValueError("path must be absolute")
        _validate_portable_relative_path(
            self.run_relative_path,
            field="run_relative_path",
        )
        if isinstance(self.size_bytes, bool) or not isinstance(
            self.size_bytes,
            int,
        ):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if not isinstance(self.sha256, str) or _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be a full lowercase SHA-256")
        _validate_metadata_text(self.media_type, field="media_type")
        if self.source_run_relative_path is not None:
            _validate_portable_relative_path(
                self.source_run_relative_path,
                field="source_run_relative_path",
            )
        if self.normalization_version is not None:
            _validate_metadata_text(
                self.normalization_version,
                field="normalization_version",
            )


def scenario_safe_key(scenario_id: object) -> str:
    canonical = str(validate_scenario_id(scenario_id))
    reserved = _is_windows_reserved(canonical)

    if (
        len(canonical) <= MAX_SAFE_KEY_LENGTH
        and not reserved
        and _PORTABLE_SEGMENT_RE.fullmatch(canonical) is not None
    ):
        return canonical

    digest = hashlib.sha256(canonical.encode("ascii")).hexdigest()[:HASH_SUFFIX_LENGTH]
    suffix = f"--{digest}"
    readable = canonical

    if reserved:
        readable = f"scenario-{canonical}"

    maximum_prefix = MAX_SAFE_KEY_LENGTH - len(suffix)
    readable = readable[:maximum_prefix].rstrip(" .-_")
    if not readable:
        readable = "scenario"

    key = f"{readable}{suffix}"
    _validate_safe_key(key)
    return key


def resolve_scenario_artifact_paths(
    scenario_id: object,
    *,
    run_directory: PathInput,
    raw_scenarios_directory: PathInput,
    generated_output_directory: PathInput,
) -> ScenarioArtifactPaths:
    canonical_id = validate_scenario_id(scenario_id)
    safe_key = scenario_safe_key(canonical_id)

    run_root = _require_owned_directory(
        run_directory,
        role="scenario run directory",
    )
    raw_root = _require_owned_directory(
        raw_scenarios_directory,
        root=run_root,
        role="raw scenario artifact directory",
    )
    generated_root = _require_owned_directory(
        generated_output_directory,
        root=run_root,
        role="scenario generated-output directory",
    )

    paths = ScenarioArtifactPaths(
        scenario_id=canonical_id,
        safe_key=safe_key,
        run_directory=run_root,
        raw_scenarios_directory=raw_root,
        generated_output_directory=generated_root,
        stdout_path=_resolve_owned_output(
            raw_root / f"{safe_key}{STDOUT_SUFFIX}",
            root=run_root,
            role="scenario stdout artifact",
        ),
        stderr_path=_resolve_owned_output(
            raw_root / f"{safe_key}{STDERR_SUFFIX}",
            root=run_root,
            role="scenario stderr artifact",
        ),
        normalized_output_path=_resolve_owned_output(
            raw_root / f"{safe_key}{NORMALIZED_OUTPUT_SUFFIX}",
            root=run_root,
            role="scenario normalized-output artifact",
        ),
        gold_diff_path=_resolve_owned_output(
            raw_root / f"{safe_key}{GOLD_DIFF_SUFFIX}",
            root=run_root,
            role="scenario gold-diff artifact",
        ),
    )
    _validate_generated_basenames(paths)
    return paths


def write_scenario_stdout(
    paths: ScenarioArtifactPaths,
    data: bytes | bytearray | memoryview,
) -> ScenarioArtifactRecord:
    return _write_raw_stream(
        paths,
        kind=ScenarioArtifactKind.STDOUT,
        data=data,
    )


def write_scenario_stderr(
    paths: ScenarioArtifactPaths,
    data: bytes | bytearray | memoryview,
) -> ScenarioArtifactRecord:
    return _write_raw_stream(
        paths,
        kind=ScenarioArtifactKind.STDERR,
        data=data,
    )


def write_normalized_output(
    paths: ScenarioArtifactPaths,
    text: str,
    *,
    normalization_version: str,
    source_kind: ScenarioArtifactKind = ScenarioArtifactKind.STDOUT,
) -> ScenarioArtifactRecord:
    _require_paths(paths)
    _validate_metadata_text(
        normalization_version,
        field="normalization_version",
    )
    if source_kind not in {
        ScenarioArtifactKind.STDOUT,
        ScenarioArtifactKind.STDERR,
    }:
        raise ValueError("source_kind must identify raw stdout or raw stderr")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if "\x00" in text:
        raise ValueError("normalized output must not contain NUL")
    if "\r" in text:
        raise ValueError("normalized output must use canonical LF line endings")

    destination = paths.normalized_output_path
    _require_new_artifact(destination, role="normalized scenario output")
    try:
        atomic_write_text(
            destination,
            text,
            encoding="utf-8",
            newline="\n",
            create_parents=False,
            root=paths.run_directory,
            role="normalized scenario output",
        )
    except OSError as exc:
        raise _evidence_io_error(
            "Unable to publish normalized scenario output",
            destination,
            paths.scenario_id,
            exc,
        ) from exc

    source_path = paths.path_for(source_kind)
    source_relative = paths.run_relative(source_path) if source_path.exists() else None
    return verify_scenario_artifact(
        paths,
        kind=ScenarioArtifactKind.NORMALIZED_OUTPUT,
        source_run_relative_path=source_relative,
        normalization_version=normalization_version,
    )


def write_normalized_scenario_output(
    spec: object,
    normalized_sections: Iterable[object],
    run_paths: object,
) -> Path:
    """Publish normalized scenario text through the canonical artifact owner.

    This stage-level adapter keeps the service independent from the lower-level
    ``ScenarioArtifactPaths`` value object while preserving the same run-owned
    destination and LF-normalized UTF-8 output.
    """

    if not isinstance(spec, _ScenarioSpecLike):
        raise TypeError("spec must expose scenario_id")
    if not isinstance(run_paths, _RunPathsLike):
        raise TypeError("run_paths must expose run_dir")
    scenario_id = validate_scenario_id(spec.scenario_id)
    run_directory = Path(run_paths.run_dir).resolve()
    raw_directory = Path(
        getattr(
            run_paths,
            "raw_scenarios_dir",
            run_directory / "raw" / "scenarios",
        )
    ).resolve()
    raw_directory.mkdir(parents=True, exist_ok=True)
    destination = resolve_for_output(
        raw_directory / f"{scenario_safe_key(scenario_id)}{NORMALIZED_OUTPUT_SUFFIX}"
    )
    require_within(destination, run_directory, role="normalized scenario output")

    lines: list[str] = []
    for index, section in enumerate(normalized_sections):
        text = getattr(
            section,
            "normalized_text",
            getattr(section, "text", None),
        )
        if not isinstance(text, str):
            raise TypeError(f"normalized_sections[{index}] must expose normalized_text or text")
        if "\x00" in text:
            raise ValueError("normalized scenario output must not contain NUL")
        lines.append(text.replace("\r\n", "\n").replace("\r", "\n"))

    payload = "\n".join(lines)
    if payload and not payload.endswith("\n"):
        payload += "\n"
    atomic_write_text(
        destination,
        payload,
        encoding="utf-8",
        newline="\n",
        create_parents=False,
        root=run_directory,
        role="normalized scenario output",
    )
    return destination


def write_gold_diff(
    paths: ScenarioArtifactPaths,
    metadata: GoldDiffMetadata,
    diff_text: str,
) -> ScenarioArtifactRecord:
    _require_paths(paths)
    if not isinstance(metadata, GoldDiffMetadata):
        raise TypeError("metadata must be GoldDiffMetadata")
    if metadata.scenario_id != paths.scenario_id:
        raise ValueError("gold diff metadata scenario_id does not match artifact paths")
    expected_actual = paths.run_relative(paths.normalized_output_path)
    if metadata.actual_normalized_output_path != expected_actual:
        raise ValueError("gold diff metadata must reference the owned normalized output")
    if not isinstance(diff_text, str):
        raise TypeError("diff_text must be a string")
    if "\x00" in diff_text:
        raise ValueError("diff_text must not contain NUL")

    canonical_diff = _canonical_lf(diff_text)
    body = _render_gold_diff(metadata, canonical_diff)
    destination = paths.gold_diff_path
    _require_new_artifact(destination, role="scenario gold diff")

    try:
        atomic_write_text(
            destination,
            body,
            encoding="utf-8",
            newline="\n",
            create_parents=False,
            root=paths.run_directory,
            role="scenario gold diff",
        )
    except OSError as exc:
        raise _evidence_io_error(
            "Unable to publish scenario gold diff",
            destination,
            paths.scenario_id,
            exc,
        ) from exc

    return verify_scenario_artifact(
        paths,
        kind=ScenarioArtifactKind.GOLD_DIFF,
        source_run_relative_path=metadata.actual_normalized_output_path,
        normalization_version=metadata.normalization_version,
        require_non_empty=True,
    )


def verify_scenario_artifact(
    paths: ScenarioArtifactPaths,
    *,
    kind: ScenarioArtifactKind,
    source_run_relative_path: str | None = None,
    normalization_version: str | None = None,
    require_non_empty: bool | None = None,
) -> ScenarioArtifactRecord:
    _require_paths(paths)
    if not isinstance(kind, ScenarioArtifactKind):
        raise TypeError("kind must be a ScenarioArtifactKind")
    if kind is ScenarioArtifactKind.GENERATED_OUTPUT:
        raise ValueError("use verify_generated_scenario_artifact for generated output")

    path = paths.path_for(kind)
    non_empty = (
        kind is ScenarioArtifactKind.GOLD_DIFF
        if require_non_empty is None
        else _require_bool(require_non_empty, field="require_non_empty")
    )
    return _verify_artifact(
        scenario_id=paths.scenario_id,
        kind=kind,
        path=path,
        run_directory=paths.run_directory,
        allowed_root=paths.raw_scenarios_directory,
        source_run_relative_path=source_run_relative_path,
        normalization_version=normalization_version,
        require_non_empty=non_empty,
    )


def verify_generated_scenario_artifact(
    paths: ScenarioArtifactPaths,
    artifact_path: PathInput,
    *,
    source_run_relative_path: str | None = None,
    media_type: str = "application/octet-stream",
    require_non_empty: bool = True,
) -> ScenarioArtifactRecord:
    _require_paths(paths)
    non_empty = _require_bool(
        require_non_empty,
        field="require_non_empty",
    )
    resolved = _require_owned_file(
        artifact_path,
        root=paths.generated_output_directory,
        role="scenario-generated artifact",
        scenario_id=paths.scenario_id,
    )
    if len(resolved.name) > MAX_GENERATED_BASENAME_LENGTH:
        raise ArtifactError(
            "Scenario-generated artifact basename is too long",
            code="GF-WB-SCENARIO-001",
            detail=(f"maximum={MAX_GENERATED_BASENAME_LENGTH}; actual={len(resolved.name)}"),
            stage="scenarios",
            operation="verify-artifact",
            subject=str(paths.scenario_id),
            evidence_paths=(paths.run_relative(resolved),),
        )
    _validate_metadata_text(media_type, field="media_type")
    return _verify_artifact(
        scenario_id=paths.scenario_id,
        kind=ScenarioArtifactKind.GENERATED_OUTPUT,
        path=resolved,
        run_directory=paths.run_directory,
        allowed_root=paths.generated_output_directory,
        source_run_relative_path=source_run_relative_path,
        normalization_version=None,
        require_non_empty=non_empty,
        media_type=media_type,
    )


def collect_existing_scenario_artifacts(
    paths: ScenarioArtifactPaths,
    *,
    required_kinds: Iterable[ScenarioArtifactKind] = (),
    generated_artifacts: Iterable[PathInput] = (),
) -> tuple[ScenarioArtifactRecord, ...]:
    _require_paths(paths)
    required = _normalize_required_kinds(required_kinds)
    records: list[ScenarioArtifactRecord] = []

    for kind in (
        ScenarioArtifactKind.STDOUT,
        ScenarioArtifactKind.STDERR,
        ScenarioArtifactKind.NORMALIZED_OUTPUT,
        ScenarioArtifactKind.GOLD_DIFF,
    ):
        path = paths.path_for(kind)
        if path.exists():
            records.append(
                verify_scenario_artifact(
                    paths,
                    kind=kind,
                )
            )
        elif kind in required:
            raise ArtifactError(
                "Required scenario artifact is missing",
                code="GF-WB-SCENARIO-001",
                detail=f"kind={kind.value}",
                stage="scenarios",
                operation="collect-artifacts",
                subject=str(paths.scenario_id),
                evidence_paths=(paths.run_relative(path),),
            )

    generated_paths = tuple(Path(value) for value in generated_artifacts)
    for generated_path in sorted(
        generated_paths,
        key=lambda value: os.fspath(value).casefold(),
    ):
        records.append(verify_generated_scenario_artifact(paths, generated_path))

    records.sort(
        key=lambda record: (
            _artifact_kind_order(record.kind),
            record.run_relative_path.casefold(),
            record.run_relative_path,
        )
    )
    return tuple(records)


def run_relative_artifact_path(
    path: PathInput,
    *,
    run_directory: PathInput,
) -> str:
    run_root = _require_owned_directory(
        run_directory,
        role="scenario run directory",
    )
    try:
        resolved = require_within(
            path,
            run_root,
            role="scenario artifact",
            stage="serialize run-relative artifact path",
            allow_equal=False,
            for_output=not Path(os.fspath(path)).exists(),
        )
    except PathContainmentError as exc:
        raise _path_security_error(
            "Scenario artifact escapes the run directory",
            candidate=exc.candidate,
            root=exc.root,
            scenario_id=None,
        ) from exc
    except OSError as exc:
        raise EvidenceIOError(
            "Unable to resolve scenario artifact path",
            code="GF-WB-IO-001",
            detail=_bounded_exception(exc),
            stage="scenarios",
            operation="serialize-artifact-path",
            subject=os.fspath(path),
        ) from exc

    relative = resolved.relative_to(run_root)
    portable = PurePosixPath(*relative.parts).as_posix()
    _validate_portable_relative_path(
        portable,
        field="run-relative artifact path",
    )
    return portable


def _write_raw_stream(
    paths: ScenarioArtifactPaths,
    *,
    kind: ScenarioArtifactKind,
    data: bytes | bytearray | memoryview,
) -> ScenarioArtifactRecord:
    _require_paths(paths)
    if kind not in {
        ScenarioArtifactKind.STDOUT,
        ScenarioArtifactKind.STDERR,
    }:
        raise ValueError("kind must identify stdout or stderr")
    try:
        payload = bytes(data)
    except (TypeError, ValueError) as exc:
        raise TypeError("data must be bytes-like") from exc

    destination = paths.path_for(kind)
    _require_new_artifact(
        destination,
        role=kind.value.replace("_", " "),
    )
    try:
        atomic_write_bytes(
            destination,
            payload,
            create_parents=False,
            root=paths.run_directory,
            role=kind.value.replace("_", " "),
        )
    except OSError as exc:
        raise _evidence_io_error(
            f"Unable to publish {kind.value.replace('_', ' ')}",
            destination,
            paths.scenario_id,
            exc,
        ) from exc

    return verify_scenario_artifact(
        paths,
        kind=kind,
        require_non_empty=False,
    )


def _verify_artifact(
    *,
    scenario_id: ScenarioId,
    kind: ScenarioArtifactKind,
    path: Path,
    run_directory: Path,
    allowed_root: Path,
    source_run_relative_path: str | None,
    normalization_version: str | None,
    require_non_empty: bool,
    media_type: str | None = None,
) -> ScenarioArtifactRecord:
    resolved = _require_owned_file(
        path,
        root=allowed_root,
        role=kind.value.replace("_", " "),
        scenario_id=scenario_id,
    )
    run_relative = run_relative_artifact_path(
        resolved,
        run_directory=run_directory,
    )

    try:
        size_bytes = resolved.stat().st_size
        digest = _sha256_file(resolved)
    except OSError as exc:
        raise _evidence_io_error(
            "Unable to verify scenario artifact",
            resolved,
            scenario_id,
            exc,
        ) from exc

    if require_non_empty and size_bytes == 0:
        raise ArtifactError(
            "Required scenario artifact is empty",
            code="GF-WB-SCENARIO-001",
            detail=f"kind={kind.value}",
            stage="scenarios",
            operation="verify-artifact",
            subject=str(scenario_id),
            evidence_paths=(run_relative,),
        )

    if source_run_relative_path is not None:
        _validate_portable_relative_path(
            source_run_relative_path,
            field="source_run_relative_path",
        )
    if normalization_version is not None:
        _validate_metadata_text(
            normalization_version,
            field="normalization_version",
        )

    return ScenarioArtifactRecord(
        scenario_id=scenario_id,
        kind=kind,
        path=resolved,
        run_relative_path=run_relative,
        size_bytes=size_bytes,
        sha256=digest,
        media_type=media_type or _media_type_for(kind),
        source_run_relative_path=source_run_relative_path,
        normalization_version=normalization_version,
    )


def _render_gold_diff(
    metadata: GoldDiffMetadata,
    diff_text: str,
) -> str:
    header = (
        f"scenario_id: {metadata.scenario_id}\n"
        f"gold_path: {metadata.gold_path}\n"
        "actual_normalized_output_path: "
        f"{metadata.actual_normalized_output_path}\n"
        f"comparison_result: {metadata.comparison_result}\n"
        f"normalization_version: {metadata.normalization_version}\n"
        "---\n"
    )
    if not diff_text:
        return header
    return header + diff_text.rstrip("\n") + "\n"


def _normalize_required_kinds(
    values: Iterable[ScenarioArtifactKind],
) -> frozenset[ScenarioArtifactKind]:
    if isinstance(values, (str, bytes)):
        raise TypeError("required_kinds must be an iterable of ScenarioArtifactKind")
    try:
        normalized = frozenset(values)
    except TypeError as exc:
        raise TypeError("required_kinds must be an iterable of ScenarioArtifactKind") from exc
    for value in normalized:
        if not isinstance(value, ScenarioArtifactKind):
            raise TypeError("required_kinds must contain ScenarioArtifactKind values")
        if value is ScenarioArtifactKind.GENERATED_OUTPUT:
            raise ValueError("generated outputs must be supplied explicitly")
    return normalized


def _require_new_artifact(path: Path, *, role: str) -> None:
    if path.exists() or path.is_symlink():
        raise ArtifactError(
            "Scenario artifact already exists and is immutable",
            code="GF-WB-SCENARIO-001",
            detail=f"role={role}",
            stage="scenarios",
            operation="publish-artifact",
            subject=os.fspath(path),
        )


def _require_owned_directory(
    path: PathInput,
    *,
    root: Path | None = None,
    role: str,
) -> Path:
    try:
        return require_directory(path, root=root, role=role)
    except PathContainmentError as exc:
        raise _path_security_error(
            f"{role.capitalize()} escapes its required root",
            candidate=exc.candidate,
            root=exc.root,
            scenario_id=None,
        ) from exc
    except OSError as exc:
        raise EvidenceIOError(
            f"{role.capitalize()} is unavailable",
            code="GF-WB-IO-001",
            detail=_bounded_exception(exc),
            stage="scenarios",
            operation="resolve-artifact-directory",
            subject=os.fspath(path),
        ) from exc


def _require_owned_file(
    path: PathInput,
    *,
    root: Path,
    role: str,
    scenario_id: ScenarioId,
) -> Path:
    try:
        return require_regular_file(path, root=root, role=role)
    except PathContainmentError as exc:
        raise _path_security_error(
            f"{role.capitalize()} escapes its required root",
            candidate=exc.candidate,
            root=exc.root,
            scenario_id=scenario_id,
        ) from exc
    except OSError as exc:
        raise ArtifactError(
            f"{role.capitalize()} is missing or unreadable",
            code="GF-WB-SCENARIO-001",
            detail=_bounded_exception(exc),
            stage="scenarios",
            operation="verify-artifact",
            subject=str(scenario_id),
            evidence_paths=(os.fspath(path),),
        ) from exc


def _resolve_owned_output(
    path: Path,
    *,
    root: Path,
    role: str,
) -> Path:
    try:
        return require_within(
            resolve_for_output(path),
            root,
            role=role,
            stage="resolve scenario artifact output",
            allow_equal=False,
            for_output=True,
        )
    except PathContainmentError as exc:
        raise _path_security_error(
            f"{role.capitalize()} escapes the run directory",
            candidate=exc.candidate,
            root=exc.root,
            scenario_id=None,
        ) from exc
    except OSError as exc:
        raise EvidenceIOError(
            f"Unable to resolve {role}",
            code="GF-WB-IO-001",
            detail=_bounded_exception(exc),
            stage="scenarios",
            operation="resolve-artifact-path",
            subject=os.fspath(path),
        ) from exc


def _path_security_error(
    message: str,
    *,
    candidate: Path,
    root: Path,
    scenario_id: ScenarioId | None,
) -> PathSecurityError:
    return PathSecurityError(
        message,
        code="GF-WB-PATH-001",
        detail=f"candidate={candidate!s}; root={root!s}",
        stage="scenarios",
        operation="resolve-artifact-path",
        subject=(os.fspath(candidate) if scenario_id is None else str(scenario_id)),
    )


def _evidence_io_error(
    message: str,
    path: Path,
    scenario_id: ScenarioId,
    exc: BaseException,
) -> EvidenceIOError:
    return EvidenceIOError(
        message,
        code="GF-WB-IO-001",
        detail=_bounded_exception(exc),
        stage="scenarios",
        operation="publish-artifact",
        subject=str(scenario_id),
        evidence_paths=(os.fspath(path),),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_lf(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _media_type_for(kind: ScenarioArtifactKind) -> str:
    if kind in {
        ScenarioArtifactKind.STDOUT,
        ScenarioArtifactKind.STDERR,
        ScenarioArtifactKind.NORMALIZED_OUTPUT,
        ScenarioArtifactKind.GOLD_DIFF,
    }:
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


def _artifact_kind_order(kind: ScenarioArtifactKind) -> int:
    return {
        ScenarioArtifactKind.STDOUT: 0,
        ScenarioArtifactKind.STDERR: 1,
        ScenarioArtifactKind.NORMALIZED_OUTPUT: 2,
        ScenarioArtifactKind.GOLD_DIFF: 3,
        ScenarioArtifactKind.GENERATED_OUTPUT: 4,
    }[kind]


def _validate_generated_basenames(
    paths: ScenarioArtifactPaths,
) -> None:
    for path in (
        paths.stdout_path,
        paths.stderr_path,
        paths.normalized_output_path,
        paths.gold_diff_path,
    ):
        if len(path.name) > MAX_GENERATED_BASENAME_LENGTH:
            raise ValueError(
                "generated scenario artifact basename exceeds "
                f"{MAX_GENERATED_BASENAME_LENGTH} characters"
            )


def _validate_safe_key(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("safe_key must be a string")
    if not value or len(value) > MAX_SAFE_KEY_LENGTH:
        raise ValueError(f"safe_key must contain 1 to {MAX_SAFE_KEY_LENGTH} characters")
    if _PORTABLE_SEGMENT_RE.fullmatch(value) is None:
        raise ValueError("safe_key contains non-portable characters")
    if value in {".", ".."}:
        raise ValueError("safe_key must not be a traversal segment")
    if value.endswith((" ", ".")):
        raise ValueError("safe_key must not end with a space or dot")
    if _is_windows_reserved(value):
        raise ValueError("safe_key must not use a Windows reserved name")


def _is_windows_reserved(value: str) -> bool:
    stem = value.split(".", 1)[0].casefold()
    return stem in _WINDOWS_RESERVED_NAMES


def verify_scenario_artifacts(
    spec: object,
    execution: object,
    *,
    run_paths: object,
) -> object:
    """Verify process-level artifacts declared by a scenario specification.

    This compatibility stage intentionally returns a small structural result so
    the scenario service does not depend on infrastructure result classes.
    """
    from types import SimpleNamespace

    declared = tuple(
        getattr(
            spec,
            "expected_artifacts",
            getattr(spec, "artifacts", ()),
        )
        or ()
    )
    records: list[object] = []
    missing: list[object] = []

    owner = getattr(execution, "working_directory", None)
    if not isinstance(owner, Path):
        owner = getattr(run_paths, "run_dir", None)
    if owner is not None and not isinstance(owner, Path):
        return SimpleNamespace(
            records=(),
            missing_required=(),
            message="Scenario artifact owner is not a path.",
            error=True,
        )

    for declaration in declared:
        raw_path = getattr(declaration, "path", declaration)
        try:
            path = raw_path if isinstance(raw_path, Path) else Path(raw_path)
        except (TypeError, ValueError):
            return SimpleNamespace(
                records=tuple(records),
                missing_required=tuple(missing),
                message="Scenario artifact declaration contains an invalid path.",
                error=True,
            )

        if not path.is_absolute():
            if owner is None:
                return SimpleNamespace(
                    records=tuple(records),
                    missing_required=tuple(missing),
                    message=("Relative scenario artifact path has no approved owner."),
                    error=True,
                )
            path = owner / path
        path = path.resolve(strict=False)

        required = bool(getattr(declaration, "required", True))
        kind = getattr(declaration, "kind", None)
        kind_value = str(getattr(kind, "value", kind or "file")).casefold()
        exists = path.is_dir() if "directory" in kind_value else path.is_file()
        minimum_size = getattr(declaration, "minimum_size_bytes", 0)
        if exists and isinstance(minimum_size, int) and minimum_size > 0:
            try:
                exists = path.stat().st_size >= minimum_size
            except OSError:
                exists = False

        record = SimpleNamespace(
            path=path,
            exists=exists,
            required=required,
            role=getattr(declaration, "role", "scenario-artifact"),
            declaration=declaration,
        )
        records.append(record)
        if required and not exists:
            missing.append(record)

    return SimpleNamespace(
        records=tuple(records),
        missing_required=tuple(missing),
        message=("Required scenario artifacts are missing." if missing else ""),
        error=False,
    )


def _validate_portable_relative_path(
    value: str,
    *,
    field: str,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or "\x00" in value or "\\" in value:
        raise ValueError(f"{field} must be a non-empty portable relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix():
        raise ValueError(f"{field} must use canonical '/' separators")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field} contains a prohibited path segment")


def _validate_token(value: str, *, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if _TOKEN_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase machine token")


def _validate_metadata_text(value: str, *, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be a single NUL-free line")


def _require_paths(value: ScenarioArtifactPaths) -> None:
    if not isinstance(value, ScenarioArtifactPaths):
        raise TypeError("paths must be ScenarioArtifactPaths")


def _require_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a bool")
    return value


def _bounded_exception(
    exc: BaseException,
    *,
    maximum: int = 320,
) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= maximum:
        return text
    return text[: maximum - 1] + "…"


__all__ = (
    "GOLD_DIFF_SUFFIX",
    "HASH_SUFFIX_LENGTH",
    "MAX_GENERATED_BASENAME_LENGTH",
    "MAX_SAFE_KEY_LENGTH",
    "NORMALIZED_OUTPUT_SUFFIX",
    "STDERR_SUFFIX",
    "STDOUT_SUFFIX",
    "GoldDiffMetadata",
    "ScenarioArtifactKind",
    "ScenarioArtifactPaths",
    "ScenarioArtifactRecord",
    "collect_existing_scenario_artifacts",
    "resolve_scenario_artifact_paths",
    "run_relative_artifact_path",
    "scenario_safe_key",
    "verify_generated_scenario_artifact",
    "verify_scenario_artifact",
    "verify_scenario_artifacts",
    "write_gold_diff",
    "write_normalized_output",
    "write_normalized_scenario_output",
    "write_scenario_stderr",
    "write_scenario_stdout",
)
