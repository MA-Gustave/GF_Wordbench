"""Safe publication and observation of GF Wordbench report artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum, unique
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
from typing import Final, TypeAlias

from gf_wordbench.infrastructure.atomic_io import atomic_write_bytes, atomic_write_text
from gf_wordbench.kernel.errors import ReportError

SHA256_ALGORITHM: Final[str] = "sha256"
UTF8: Final[str] = "utf-8"
MAX_ARTIFACT_SIZE_BYTES: Final[int] = 2**63 - 1

_ROLE_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_CREATED_BY_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_MEDIA_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+"
    r"(?:; [A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+-]+)*$"
)
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")


@unique
class ArtifactContentKind(StrEnum):
    TEXT = "text"
    BINARY = "binary"


ArtifactPayload: TypeAlias = str | bytes | bytearray | memoryview


@dataclass(frozen=True, slots=True)
class ArtifactDeclaration:
    destination: Path
    run_root: Path
    role: str
    media_type: str
    required: bool
    created_by: str
    content_kind: ArtifactContentKind

    def __post_init__(self) -> None:
        destination = _absolute_file_path(
            self.destination,
            field_name="destination",
        )
        run_root = _absolute_directory_path(
            self.run_root,
            field_name="run_root",
        )
        _require_contained(destination, run_root)
        role = _validated_token(self.role, field_name="role", pattern=_ROLE_RE)
        media_type = _validated_media_type(self.media_type)
        created_by = _validated_token(
            self.created_by,
            field_name="created_by",
            pattern=_CREATED_BY_RE,
        )
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if not isinstance(self.content_kind, ArtifactContentKind):
            raise TypeError("content_kind must be ArtifactContentKind")
        object.__setattr__(self, "destination", destination)
        object.__setattr__(self, "run_root", run_root)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(self, "created_by", created_by)

    @property
    def run_relative_path(self) -> PurePosixPath:
        return PurePosixPath(self.destination.relative_to(self.run_root).as_posix())


@dataclass(frozen=True, slots=True)
class PublishedArtifact:
    path: Path
    run_relative_path: PurePosixPath
    role: str
    media_type: str
    required: bool
    size_bytes: int
    sha256: str
    created_by: str

    def __post_init__(self) -> None:
        path = _absolute_file_path(self.path, field_name="path")
        relative = _portable_relative_path(
            self.run_relative_path,
            field_name="run_relative_path",
        )
        role = _validated_token(self.role, field_name="role", pattern=_ROLE_RE)
        media_type = _validated_media_type(self.media_type)
        created_by = _validated_token(
            self.created_by,
            field_name="created_by",
            pattern=_CREATED_BY_RE,
        )
        if type(self.required) is not bool:
            raise TypeError("required must be a boolean")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if self.size_bytes > MAX_ARTIFACT_SIZE_BYTES:
            raise ValueError("size_bytes exceeds the supported limit")
        if not isinstance(self.sha256, str) or _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be a lowercase 64-character digest")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "run_relative_path", relative)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(self, "created_by", created_by)


@dataclass(frozen=True, slots=True)
class ArtifactWriteRequest:
    declaration: ArtifactDeclaration
    payload: ArtifactPayload
    canonical_text: bool = True
    create_parents: bool = True
    sync: bool = True
    preserve_existing_mode: bool = True
    file_mode: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.declaration, ArtifactDeclaration):
            raise TypeError("declaration must be ArtifactDeclaration")
        if self.declaration.content_kind is ArtifactContentKind.TEXT:
            if not isinstance(self.payload, str):
                raise TypeError("text artifacts require a string payload")
        elif isinstance(self.payload, str):
            raise TypeError("binary artifacts require a bytes-like payload")
        elif not isinstance(self.payload, (bytes, bytearray, memoryview)):
            raise TypeError("binary payload must be bytes-like")
        for field_name in (
            "canonical_text",
            "create_parents",
            "sync",
            "preserve_existing_mode",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        if self.file_mode is not None:
            if type(self.file_mode) is not int:
                raise TypeError("file_mode must be an integer or None")
            if self.file_mode < 0 or self.file_mode > 0o7777:
                raise ValueError("file_mode must be between 0 and 0o7777")


@dataclass(frozen=True, slots=True)
class ArtifactVerification:
    artifact: PublishedArtifact
    exists: bool
    regular_file: bool
    contained: bool
    size_matches: bool
    hash_matches: bool
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, PublishedArtifact):
            raise TypeError("artifact must be PublishedArtifact")
        for field_name in (
            "exists",
            "regular_file",
            "contained",
            "size_matches",
            "hash_matches",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        issues = _unique_text(self.issues, field_name="issues")
        object.__setattr__(self, "issues", issues)

    @property
    def valid(self) -> bool:
        return (
            self.exists
            and self.regular_file
            and self.contained
            and self.size_matches
            and self.hash_matches
            and not self.issues
        )


def publish_artifact(request: ArtifactWriteRequest) -> PublishedArtifact:
    if not isinstance(request, ArtifactWriteRequest):
        raise TypeError("request must be ArtifactWriteRequest")

    declaration = request.declaration
    destination = declaration.destination
    try:
        if declaration.content_kind is ArtifactContentKind.TEXT:
            text = request.payload
            assert isinstance(text, str)
            if request.canonical_text:
                text = canonical_text(text)
            atomic_write_text(
                destination,
                text,
                encoding=UTF8,
                newline="\n",
                create_parents=request.create_parents,
                root=declaration.run_root,
                role=f"{declaration.role} report artifact",
                sync=request.sync,
                preserve_existing_mode=request.preserve_existing_mode,
                file_mode=request.file_mode,
            )
        else:
            data = request.payload
            assert not isinstance(data, str)
            atomic_write_bytes(
                destination,
                bytes(data),
                create_parents=request.create_parents,
                root=declaration.run_root,
                role=f"{declaration.role} report artifact",
                sync=request.sync,
                preserve_existing_mode=request.preserve_existing_mode,
                file_mode=request.file_mode,
            )
        return observe_artifact(declaration)
    except ReportError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise ReportError(
            "Report artifact publication failed",
            code="GF-WB-REPORT-001",
            detail=_bounded_exception(error),
            stage="reporting",
            operation="publish-artifact",
            subject=str(destination),
            retryable=isinstance(error, OSError),
        ) from error


def publish_text_artifact(
    destination: Path,
    text: str,
    *,
    run_root: Path,
    role: str,
    media_type: str,
    required: bool,
    created_by: str,
    canonical: bool = True,
    create_parents: bool = True,
) -> PublishedArtifact:
    return publish_artifact(
        ArtifactWriteRequest(
            declaration=ArtifactDeclaration(
                destination=destination,
                run_root=run_root,
                role=role,
                media_type=media_type,
                required=required,
                created_by=created_by,
                content_kind=ArtifactContentKind.TEXT,
            ),
            payload=text,
            canonical_text=canonical,
            create_parents=create_parents,
        )
    )


def publish_binary_artifact(
    destination: Path,
    data: bytes | bytearray | memoryview,
    *,
    run_root: Path,
    role: str,
    media_type: str,
    required: bool,
    created_by: str,
    create_parents: bool = True,
) -> PublishedArtifact:
    return publish_artifact(
        ArtifactWriteRequest(
            declaration=ArtifactDeclaration(
                destination=destination,
                run_root=run_root,
                role=role,
                media_type=media_type,
                required=required,
                created_by=created_by,
                content_kind=ArtifactContentKind.BINARY,
            ),
            payload=data,
            canonical_text=False,
            create_parents=create_parents,
        )
    )


def observe_artifact(declaration: ArtifactDeclaration) -> PublishedArtifact:
    if not isinstance(declaration, ArtifactDeclaration):
        raise TypeError("declaration must be ArtifactDeclaration")
    path = declaration.destination
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError(f"artifact is not a regular file: {path}")
        resolved = path.resolve(strict=True)
        _require_contained(resolved, declaration.run_root)
        size_bytes = metadata.st_size
        sha256 = sha256_file(resolved)
    except (OSError, ValueError) as error:
        raise ReportError(
            "Report artifact could not be observed reliably",
            code="GF-WB-REPORT-002",
            detail=_bounded_exception(error),
            stage="reporting",
            operation="observe-artifact",
            subject=str(path),
            retryable=isinstance(error, OSError),
        ) from error
    return PublishedArtifact(
        path=resolved,
        run_relative_path=declaration.run_relative_path,
        role=declaration.role,
        media_type=declaration.media_type,
        required=declaration.required,
        size_bytes=size_bytes,
        sha256=sha256,
        created_by=declaration.created_by,
    )


def verify_published_artifact(
    artifact: PublishedArtifact,
    *,
    run_root: Path,
) -> ArtifactVerification:
    if not isinstance(artifact, PublishedArtifact):
        raise TypeError("artifact must be PublishedArtifact")
    root = _absolute_directory_path(run_root, field_name="run_root")
    issues: list[str] = []
    exists = artifact.path.exists()
    regular_file = False
    contained = _is_contained(artifact.path, root)
    size_matches = False
    hash_matches = False

    if not contained:
        issues.append("artifact path escapes the run root")
    if not exists:
        issues.append("artifact is missing")
    else:
        try:
            metadata = artifact.path.lstat()
            regular_file = stat.S_ISREG(metadata.st_mode)
            if not regular_file:
                issues.append("artifact is not a regular file")
            else:
                size_matches = metadata.st_size == artifact.size_bytes
                if not size_matches:
                    issues.append("artifact size does not match publication metadata")
                observed_hash = sha256_file(artifact.path)
                hash_matches = observed_hash == artifact.sha256
                if not hash_matches:
                    issues.append("artifact hash does not match publication metadata")
        except OSError as error:
            issues.append(_bounded_exception(error))

    return ArtifactVerification(
        artifact=artifact,
        exists=exists,
        regular_file=regular_file,
        contained=contained,
        size_matches=size_matches,
        hash_matches=hash_matches,
        issues=tuple(issues),
    )


def canonical_artifact_order(
    artifacts: Iterable[PublishedArtifact],
) -> tuple[PublishedArtifact, ...]:
    raw_artifacts: object = artifacts
    if isinstance(raw_artifacts, (str, bytes)):
        raise TypeError("artifacts must be an iterable of PublishedArtifact")
    prepared = tuple(artifacts)
    for artifact in prepared:
        if not isinstance(artifact, PublishedArtifact):
            raise TypeError("artifacts must contain PublishedArtifact values")
    paths = tuple(artifact.run_relative_path.as_posix() for artifact in prepared)
    if len(paths) != len(set(paths)):
        raise ValueError("artifact paths must be unique")
    return tuple(
        sorted(
            prepared,
            key=lambda item: (
                item.run_relative_path.as_posix().casefold(),
                item.run_relative_path.as_posix(),
            ),
        )
    )


def canonical_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if "\x00" in text:
        raise ValueError("text must not contain NUL")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.rstrip("\n") + "\n"


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    file_path = _absolute_file_path(path, field_name="path")
    if type(chunk_size) is not int or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")
    digest = hashlib.sha256()
    with file_path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _absolute_file_path(value: object, *, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    raw = os.fspath(value)
    if "\x00" in raw:
        raise ValueError(f"{field_name} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    if not value.name or value.name in {".", ".."}:
        raise ValueError(f"{field_name} must name a file")
    return Path(os.path.abspath(value))


def _absolute_directory_path(value: object, *, field_name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    raw = os.fspath(value)
    if "\x00" in raw:
        raise ValueError(f"{field_name} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return Path(os.path.abspath(value)).resolve(strict=False)


def _portable_relative_path(value: object, *, field_name: str) -> PurePosixPath:
    if isinstance(value, PureWindowsPath):
        raise ValueError(f"{field_name} must use portable '/' separators")
    if isinstance(value, Path) or isinstance(value, PurePosixPath):
        text = value.as_posix()
    elif isinstance(value, str):
        text = value
    else:
        raise TypeError(f"{field_name} must be a portable relative path")
    if not text or "\x00" in text or "\\" in text:
        raise ValueError(f"{field_name} is not a valid portable path")
    path = PurePosixPath(text)
    if path.is_absolute() or text.startswith("//") or ":" in path.parts[0]:
        raise ValueError(f"{field_name} must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field_name} contains an invalid segment")
    return path


def _validated_token(value: object, *, field_name: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if pattern.fullmatch(value) is None:
        raise ValueError(f"{field_name} must use lower_snake_case")
    return value


def _validated_media_type(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("media_type must be a string")
    if _MEDIA_TYPE_RE.fullmatch(value) is None:
        raise ValueError("media_type is invalid")
    return value


def _require_contained(path: Path, root: Path) -> None:
    if not _is_contained(path, root):
        raise ValueError(f"artifact path escapes run root: {path}")


def _is_contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _unique_text(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must contain strings")
        if not value.strip() or "\x00" in value:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _bounded_exception(error: BaseException, limit: int = 4096) -> str:
    text = f"{type(error).__name__}: {error}".replace("\x00", "")
    return text if len(text) <= limit else text[: limit - 16].rstrip() + " … [truncated]"


__all__ = (
    "MAX_ARTIFACT_SIZE_BYTES",
    "SHA256_ALGORITHM",
    "UTF8",
    "ArtifactContentKind",
    "ArtifactDeclaration",
    "ArtifactPayload",
    "ArtifactVerification",
    "ArtifactWriteRequest",
    "PublishedArtifact",
    "canonical_artifact_order",
    "canonical_text",
    "observe_artifact",
    "publish_artifact",
    "publish_binary_artifact",
    "publish_text_artifact",
    "sha256_file",
    "verify_published_artifact",
)
