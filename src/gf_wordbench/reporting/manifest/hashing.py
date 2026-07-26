from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Final

HASH_ALGORITHM: Final[str] = "sha256"
SHA256_HEX_LENGTH: Final[int] = 64
DEFAULT_HASH_CHUNK_SIZE_BYTES: Final[int] = 1024 * 1024
MAX_HASH_CHUNK_SIZE_BYTES: Final[int] = 64 * 1024 * 1024
DEFAULT_MUTATION_RETRIES: Final[int] = 1


class ManifestHashingError(Exception):
    pass


class UnsupportedHashAlgorithmError(ManifestHashingError):
    pass


class ArtifactNotFoundError(ManifestHashingError):
    pass


class ArtifactNotRegularFileError(ManifestHashingError):
    pass


class ArtifactSymlinkError(ManifestHashingError):
    pass


class ArtifactChangedDuringHashError(ManifestHashingError):
    pass


class ArtifactHashMismatchError(ManifestHashingError):
    pass


@dataclass(frozen=True, slots=True)
class FileIdentity:
    size_bytes: int
    modified_ns: int
    device: int
    inode: int
    mode: int

    def __post_init__(self) -> None:
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if type(self.modified_ns) is not int or self.modified_ns < 0:
            raise ValueError("modified_ns must be a non-negative integer")
        if type(self.device) is not int or self.device < 0:
            raise ValueError("device must be a non-negative integer")
        if type(self.inode) is not int or self.inode < 0:
            raise ValueError("inode must be a non-negative integer")
        if type(self.mode) is not int or self.mode < 0:
            raise ValueError("mode must be a non-negative integer")

    @classmethod
    def from_stat(cls, value: os.stat_result) -> FileIdentity:
        if not isinstance(value, os.stat_result):
            raise TypeError("value must be os.stat_result")
        return cls(
            size_bytes=int(value.st_size),
            modified_ns=int(value.st_mtime_ns),
            device=int(value.st_dev),
            inode=int(value.st_ino),
            mode=int(value.st_mode),
        )

    @property
    def is_regular_file(self) -> bool:
        return stat.S_ISREG(self.mode)

    @property
    def is_symlink(self) -> bool:
        return stat.S_ISLNK(self.mode)

    def same_file(self, other: FileIdentity) -> bool:
        if not isinstance(other, FileIdentity):
            raise TypeError("other must be FileIdentity")
        if self.device and other.device and self.device != other.device:
            return False
        if self.inode and other.inode and self.inode != other.inode:
            return False
        return True

    def same_final_bytes_identity(self, other: FileIdentity) -> bool:
        return (
            self.same_file(other)
            and self.size_bytes == other.size_bytes
            and self.modified_ns == other.modified_ns
            and stat.S_IFMT(self.mode) == stat.S_IFMT(other.mode)
        )


@dataclass(frozen=True, slots=True)
class FileHash:
    path: Path
    hash_algorithm: str
    sha256: str
    size_bytes: int
    modified_ns: int
    identity: FileIdentity
    attempts: int = 1
    reopen_verified: bool = False

    def __post_init__(self) -> None:
        path = _path(self.path)
        algorithm = normalize_hash_algorithm(self.hash_algorithm)
        digest = normalize_sha256(self.sha256)
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if type(self.modified_ns) is not int or self.modified_ns < 0:
            raise ValueError("modified_ns must be a non-negative integer")
        if not isinstance(self.identity, FileIdentity):
            raise TypeError("identity must be FileIdentity")
        if self.size_bytes != self.identity.size_bytes:
            raise ValueError("size_bytes must match identity")
        if self.modified_ns != self.identity.modified_ns:
            raise ValueError("modified_ns must match identity")
        if type(self.attempts) is not int or self.attempts < 1:
            raise ValueError("attempts must be a positive integer")
        if type(self.reopen_verified) is not bool:
            raise TypeError("reopen_verified must be a boolean")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "hash_algorithm", algorithm)
        object.__setattr__(self, "sha256", digest)

    @property
    def digest(self) -> str:
        return self.sha256

    @property
    def algorithm(self) -> str:
        return self.hash_algorithm


@dataclass(frozen=True, slots=True)
class HashVerification:
    path: Path
    expected_size_bytes: int
    actual_size_bytes: int | None
    expected_sha256: str
    actual_sha256: str | None
    exists: bool
    regular_file: bool
    symlink: bool
    size_matches: bool
    hash_matches: bool
    stable: bool
    error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _path(self.path))
        if (
            type(self.expected_size_bytes) is not int
            or self.expected_size_bytes < 0
        ):
            raise ValueError(
                "expected_size_bytes must be a non-negative integer"
            )
        if self.actual_size_bytes is not None and (
            type(self.actual_size_bytes) is not int
            or self.actual_size_bytes < 0
        ):
            raise ValueError(
                "actual_size_bytes must be a non-negative integer or None"
            )
        object.__setattr__(
            self,
            "expected_sha256",
            normalize_sha256(self.expected_sha256),
        )
        if self.actual_sha256 is not None:
            object.__setattr__(
                self,
                "actual_sha256",
                normalize_sha256(self.actual_sha256),
            )
        for name in (
            "exists",
            "regular_file",
            "symlink",
            "size_matches",
            "hash_matches",
            "stable",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")
        if self.error is not None:
            object.__setattr__(
                self,
                "error",
                _bounded_text(self.error, "error"),
            )

    @property
    def ok(self) -> bool:
        return (
            self.exists
            and self.regular_file
            and not self.symlink
            and self.size_matches
            and self.hash_matches
            and self.stable
            and self.error is None
        )

    def require_ok(self) -> None:
        if self.ok:
            return
        detail = self.error or (
            f"size_matches={self.size_matches}, "
            f"hash_matches={self.hash_matches}, stable={self.stable}"
        )
        raise ArtifactHashMismatchError(
            f"Artifact hash verification failed for {self.path}: {detail}"
        )


def normalize_hash_algorithm(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("hash algorithm must be a string")
    normalized = value.strip().lower().replace("-", "")
    if normalized != HASH_ALGORITHM:
        raise UnsupportedHashAlgorithmError(
            f"Unsupported hash algorithm: {value!r}"
        )
    return HASH_ALGORITHM


def is_sha256(value: object) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    return (
        len(candidate) == SHA256_HEX_LENGTH
        and all(character in "0123456789abcdefABCDEF" for character in candidate)
    )


def normalize_sha256(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("SHA-256 digest must be a string")
    candidate = value.strip()
    if not is_sha256(candidate):
        raise ValueError(
            "SHA-256 digest must contain exactly 64 hexadecimal characters"
        )
    return candidate.lower()


def sha256_bytes(value: bytes | bytearray | memoryview) -> str:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError("value must be bytes-like")
    return hashlib.sha256(value).hexdigest()


def sha256_stream(
    stream: BinaryIO,
    *,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
) -> tuple[str, int]:
    if not hasattr(stream, "read"):
        raise TypeError("stream must provide read()")
    chunk_size = _chunk_size(chunk_size_bytes)
    digest = hashlib.sha256()
    size_bytes = 0
    while True:
        chunk = stream.read(chunk_size)
        if chunk in (b"", None):
            break
        if not isinstance(chunk, bytes):
            raise TypeError("binary stream read() must return bytes")
        digest.update(chunk)
        size_bytes += len(chunk)
    return digest.hexdigest(), size_bytes


def sha256_file(
    path: Path,
    *,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> str:
    return hash_file(
        path,
        chunk_size_bytes=chunk_size_bytes,
        reject_symlinks=reject_symlinks,
        mutation_retries=mutation_retries,
        verify_reopen=verify_reopen,
    ).sha256


def hash_file(
    path: Path,
    *,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> FileHash:
    target = _path(path)
    chunk_size = _chunk_size(chunk_size_bytes)
    retries = _non_negative_int(mutation_retries, "mutation_retries")
    if type(reject_symlinks) is not bool:
        raise TypeError("reject_symlinks must be a boolean")
    if type(verify_reopen) is not bool:
        raise TypeError("verify_reopen must be a boolean")

    last_error: ArtifactChangedDuringHashError | None = None
    for attempt in range(1, retries + 2):
        try:
            hashed = _hash_file_once(
                target,
                chunk_size_bytes=chunk_size,
                reject_symlinks=reject_symlinks,
            )
            if verify_reopen:
                second = _hash_file_once(
                    target,
                    chunk_size_bytes=chunk_size,
                    reject_symlinks=reject_symlinks,
                )
                if (
                    hashed.sha256 != second.sha256
                    or hashed.size_bytes != second.size_bytes
                    or not hashed.identity.same_final_bytes_identity(
                        second.identity
                    )
                ):
                    raise ArtifactChangedDuringHashError(
                        f"Artifact changed during strict re-open verification: "
                        f"{target}"
                    )
                hashed = FileHash(
                    path=hashed.path,
                    hash_algorithm=hashed.hash_algorithm,
                    sha256=hashed.sha256,
                    size_bytes=hashed.size_bytes,
                    modified_ns=hashed.modified_ns,
                    identity=hashed.identity,
                    attempts=attempt,
                    reopen_verified=True,
                )
            elif attempt != hashed.attempts:
                hashed = FileHash(
                    path=hashed.path,
                    hash_algorithm=hashed.hash_algorithm,
                    sha256=hashed.sha256,
                    size_bytes=hashed.size_bytes,
                    modified_ns=hashed.modified_ns,
                    identity=hashed.identity,
                    attempts=attempt,
                    reopen_verified=False,
                )
            return hashed
        except ArtifactChangedDuringHashError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise AssertionError("unreachable hashing state")


def hash_artifact(
    path: Path,
    *,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> FileHash:
    return hash_file(
        path,
        chunk_size_bytes=chunk_size_bytes,
        reject_symlinks=reject_symlinks,
        mutation_retries=mutation_retries,
        verify_reopen=verify_reopen,
    )


def verify_file_hash(
    path: Path,
    *,
    expected_size_bytes: int,
    expected_sha256: str,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> HashVerification:
    target = _path(path)
    expected_size = _non_negative_int(
        expected_size_bytes,
        "expected_size_bytes",
    )
    expected_digest = normalize_sha256(expected_sha256)

    try:
        before = target.lstat()
    except FileNotFoundError:
        return HashVerification(
            path=target,
            expected_size_bytes=expected_size,
            actual_size_bytes=None,
            expected_sha256=expected_digest,
            actual_sha256=None,
            exists=False,
            regular_file=False,
            symlink=False,
            size_matches=False,
            hash_matches=False,
            stable=False,
            error="artifact does not exist",
        )
    except OSError as exc:
        return HashVerification(
            path=target,
            expected_size_bytes=expected_size,
            actual_size_bytes=None,
            expected_sha256=expected_digest,
            actual_sha256=None,
            exists=False,
            regular_file=False,
            symlink=False,
            size_matches=False,
            hash_matches=False,
            stable=False,
            error=_exception_text(exc),
        )

    symlink = stat.S_ISLNK(before.st_mode)
    if symlink and reject_symlinks:
        return HashVerification(
            path=target,
            expected_size_bytes=expected_size,
            actual_size_bytes=int(before.st_size),
            expected_sha256=expected_digest,
            actual_sha256=None,
            exists=True,
            regular_file=False,
            symlink=True,
            size_matches=False,
            hash_matches=False,
            stable=False,
            error="artifact is a symbolic link",
        )

    try:
        hashed = hash_file(
            target,
            chunk_size_bytes=chunk_size_bytes,
            reject_symlinks=reject_symlinks,
            mutation_retries=mutation_retries,
            verify_reopen=verify_reopen,
        )
    except (ManifestHashingError, OSError) as exc:
        return HashVerification(
            path=target,
            expected_size_bytes=expected_size,
            actual_size_bytes=int(before.st_size),
            expected_sha256=expected_digest,
            actual_sha256=None,
            exists=True,
            regular_file=stat.S_ISREG(before.st_mode),
            symlink=symlink,
            size_matches=int(before.st_size) == expected_size,
            hash_matches=False,
            stable=False,
            error=_exception_text(exc),
        )

    return HashVerification(
        path=target,
        expected_size_bytes=expected_size,
        actual_size_bytes=hashed.size_bytes,
        expected_sha256=expected_digest,
        actual_sha256=hashed.sha256,
        exists=True,
        regular_file=True,
        symlink=symlink,
        size_matches=hashed.size_bytes == expected_size,
        hash_matches=hashed.sha256 == expected_digest,
        stable=True,
        error=None,
    )


def verify_artifact_hash(
    path: Path,
    *,
    expected_size_bytes: int,
    expected_sha256: str,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> HashVerification:
    return verify_file_hash(
        path,
        expected_size_bytes=expected_size_bytes,
        expected_sha256=expected_sha256,
        chunk_size_bytes=chunk_size_bytes,
        reject_symlinks=reject_symlinks,
        mutation_retries=mutation_retries,
        verify_reopen=verify_reopen,
    )


def matches_file_hash(
    path: Path,
    *,
    expected_size_bytes: int,
    expected_sha256: str,
    chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
    reject_symlinks: bool = True,
    mutation_retries: int = DEFAULT_MUTATION_RETRIES,
    verify_reopen: bool = False,
) -> bool:
    return verify_file_hash(
        path,
        expected_size_bytes=expected_size_bytes,
        expected_sha256=expected_sha256,
        chunk_size_bytes=chunk_size_bytes,
        reject_symlinks=reject_symlinks,
        mutation_retries=mutation_retries,
        verify_reopen=verify_reopen,
    ).ok


class Sha256FileHasher:
    __slots__ = (
        "_chunk_size_bytes",
        "_reject_symlinks",
        "_mutation_retries",
        "_verify_reopen",
    )

    def __init__(
        self,
        *,
        chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE_BYTES,
        reject_symlinks: bool = True,
        mutation_retries: int = DEFAULT_MUTATION_RETRIES,
        verify_reopen: bool = False,
    ) -> None:
        self._chunk_size_bytes = _chunk_size(chunk_size_bytes)
        if type(reject_symlinks) is not bool:
            raise TypeError("reject_symlinks must be a boolean")
        self._reject_symlinks = reject_symlinks
        self._mutation_retries = _non_negative_int(
            mutation_retries,
            "mutation_retries",
        )
        if type(verify_reopen) is not bool:
            raise TypeError("verify_reopen must be a boolean")
        self._verify_reopen = verify_reopen

    @property
    def hash_algorithm(self) -> str:
        return HASH_ALGORITHM

    @property
    def chunk_size_bytes(self) -> int:
        return self._chunk_size_bytes

    def sha256(
        self,
        path: Path,
        *,
        chunk_size_bytes: int | None = None,
    ) -> str:
        return self.hash(
            path,
            chunk_size_bytes=chunk_size_bytes,
        ).sha256

    def hash(
        self,
        path: Path,
        *,
        chunk_size_bytes: int | None = None,
    ) -> FileHash:
        return hash_file(
            path,
            chunk_size_bytes=(
                self._chunk_size_bytes
                if chunk_size_bytes is None
                else chunk_size_bytes
            ),
            reject_symlinks=self._reject_symlinks,
            mutation_retries=self._mutation_retries,
            verify_reopen=self._verify_reopen,
        )

    def verify(
        self,
        path: Path,
        *,
        expected_size_bytes: int,
        expected_sha256: str,
        chunk_size_bytes: int | None = None,
    ) -> HashVerification:
        return verify_file_hash(
            path,
            expected_size_bytes=expected_size_bytes,
            expected_sha256=expected_sha256,
            chunk_size_bytes=(
                self._chunk_size_bytes
                if chunk_size_bytes is None
                else chunk_size_bytes
            ),
            reject_symlinks=self._reject_symlinks,
            mutation_retries=self._mutation_retries,
            verify_reopen=self._verify_reopen,
        )


FileHasher = Sha256FileHasher


def _hash_file_once(
    path: Path,
    *,
    chunk_size_bytes: int,
    reject_symlinks: bool,
) -> FileHash:
    try:
        path_before_stat = path.lstat()
    except FileNotFoundError as exc:
        raise ArtifactNotFoundError(
            f"Artifact does not exist: {path}"
        ) from exc

    path_before = FileIdentity.from_stat(path_before_stat)
    if path_before.is_symlink and reject_symlinks:
        raise ArtifactSymlinkError(
            f"Artifact is a symbolic link: {path}"
        )
    if not path_before.is_symlink and not path_before.is_regular_file:
        raise ArtifactNotRegularFileError(
            f"Artifact is not a regular file: {path}"
        )

    descriptor = _open_read_only(
        path,
        reject_symlinks=reject_symlinks,
    )
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            open_before = FileIdentity.from_stat(os.fstat(stream.fileno()))
            if not open_before.is_regular_file:
                raise ArtifactNotRegularFileError(
                    f"Artifact is not a regular file: {path}"
                )
            if not path_before.same_file(open_before):
                raise ArtifactChangedDuringHashError(
                    f"Artifact identity changed before hashing: {path}"
                )
            digest, bytes_read = sha256_stream(
                stream,
                chunk_size_bytes=chunk_size_bytes,
            )
            open_after = FileIdentity.from_stat(os.fstat(stream.fileno()))
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        path_after_stat = path.lstat()
    except FileNotFoundError as exc:
        raise ArtifactChangedDuringHashError(
            f"Artifact disappeared during hashing: {path}"
        ) from exc

    path_after = FileIdentity.from_stat(path_after_stat)
    if path_after.is_symlink and reject_symlinks:
        raise ArtifactChangedDuringHashError(
            f"Artifact became a symbolic link during hashing: {path}"
        )
    if not open_before.same_final_bytes_identity(open_after):
        raise ArtifactChangedDuringHashError(
            f"Artifact changed while its bytes were read: {path}"
        )
    if not open_after.same_final_bytes_identity(path_after):
        raise ArtifactChangedDuringHashError(
            f"Artifact changed before hashing completed: {path}"
        )
    if bytes_read != open_after.size_bytes:
        raise ArtifactChangedDuringHashError(
            f"Artifact byte count changed during hashing: {path}"
        )

    return FileHash(
        path=path,
        hash_algorithm=HASH_ALGORITHM,
        sha256=digest,
        size_bytes=bytes_read,
        modified_ns=open_after.modified_ns,
        identity=open_after,
    )


def _open_read_only(
    path: Path,
    *,
    reject_symlinks: bool,
) -> int:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    if reject_symlinks:
        flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path, flags)
    except FileNotFoundError as exc:
        raise ArtifactNotFoundError(
            f"Artifact does not exist: {path}"
        ) from exc
    except OSError as exc:
        if reject_symlinks:
            try:
                if path.is_symlink():
                    raise ArtifactSymlinkError(
                        f"Artifact is a symbolic link: {path}"
                    ) from exc
            except OSError:
                pass
        raise


def _path(value: object) -> Path:
    if not isinstance(value, Path):
        raise TypeError("path must be pathlib.Path")
    if "\x00" in os.fspath(value):
        raise ValueError("path must not contain NUL")
    return value


def _chunk_size(value: object) -> int:
    if type(value) is not int:
        raise TypeError("chunk_size_bytes must be an integer")
    if value <= 0:
        raise ValueError("chunk_size_bytes must be positive")
    if value > MAX_HASH_CHUNK_SIZE_BYTES:
        raise ValueError(
            f"chunk_size_bytes must not exceed "
            f"{MAX_HASH_CHUNK_SIZE_BYTES}"
        )
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _bounded_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value[:4000]


def _exception_text(exc: BaseException) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text.replace("\x00", "\\x00")[:4000]


__all__ = (
    "DEFAULT_HASH_CHUNK_SIZE_BYTES",
    "DEFAULT_MUTATION_RETRIES",
    "FileHash",
    "FileHasher",
    "FileIdentity",
    "HASH_ALGORITHM",
    "HashVerification",
    "ManifestHashingError",
    "MAX_HASH_CHUNK_SIZE_BYTES",
    "SHA256_HEX_LENGTH",
    "Sha256FileHasher",
    "ArtifactChangedDuringHashError",
    "ArtifactHashMismatchError",
    "ArtifactNotFoundError",
    "ArtifactNotRegularFileError",
    "ArtifactSymlinkError",
    "UnsupportedHashAlgorithmError",
    "hash_artifact",
    "hash_file",
    "is_sha256",
    "matches_file_hash",
    "normalize_hash_algorithm",
    "normalize_sha256",
    "sha256_bytes",
    "sha256_file",
    "sha256_stream",
    "verify_artifact_hash",
    "verify_file_hash",
)
