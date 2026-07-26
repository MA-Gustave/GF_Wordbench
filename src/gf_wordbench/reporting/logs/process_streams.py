from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.infrastructure.atomic_io import atomic_binary_writer
from gf_wordbench.kernel.errors import ContractViolationError, ReportError

_COPY_CHUNK_SIZE: Final[int] = 1024 * 1024
_MAX_ROLE_LENGTH: Final[int] = 128
_MAX_SUBJECT_LENGTH: Final[int] = 2048
_MAX_OPERATION_ID_LENGTH: Final[int] = 256


@unique
class ProcessStreamName(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


@unique
class ProcessStreamState(StrEnum):
    PRESENT = "present"
    EMPTY = "empty"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class StreamPaths:
    stdout: Path
    stderr: Path

    def __post_init__(self) -> None:
        stdout = _coerce_absolute_path(self.stdout, "stdout")
        stderr = _coerce_absolute_path(self.stderr, "stderr")
        if _path_key(stdout) == _path_key(stderr):
            raise ContractViolationError("stdout and stderr paths must be distinct")
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)

    def for_stream(self, stream: ProcessStreamName | str) -> Path:
        canonical = _coerce_stream(stream)
        return self.stdout if canonical is ProcessStreamName.STDOUT else self.stderr

    def as_tuple(self) -> tuple[Path, Path]:
        return self.stdout, self.stderr


@dataclass(frozen=True, slots=True)
class ProcessStreamArtifact:
    stream: ProcessStreamName
    path: Path
    state: ProcessStreamState
    size_bytes: int | None
    sha256: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.stream, ProcessStreamName):
            raise TypeError("stream must be ProcessStreamName")
        path = _coerce_absolute_path(self.path, "path")
        if not isinstance(self.state, ProcessStreamState):
            raise TypeError("state must be ProcessStreamState")
        if self.size_bytes is not None:
            if type(self.size_bytes) is not int or self.size_bytes < 0:
                raise ValueError("size_bytes must be a non-negative integer or None")
        if self.sha256 is not None:
            if not isinstance(self.sha256, str) or len(self.sha256) != 64:
                raise ValueError("sha256 must be a 64-character hexadecimal digest")
            try:
                int(self.sha256, 16)
            except ValueError as exc:
                raise ValueError("sha256 must be hexadecimal") from exc
        if self.state is ProcessStreamState.MISSING:
            if self.size_bytes is not None or self.sha256 is not None:
                raise ValueError("missing stream evidence cannot have size or digest")
        elif self.size_bytes is None or self.sha256 is None:
            raise ValueError("present stream evidence requires size and digest")
        if self.state is ProcessStreamState.EMPTY and self.size_bytes != 0:
            raise ValueError("empty stream evidence must have zero size")
        if self.state is ProcessStreamState.PRESENT and self.size_bytes == 0:
            raise ValueError("zero-byte stream evidence must use state EMPTY")
        object.__setattr__(self, "path", path)
        if self.sha256 is not None:
            object.__setattr__(self, "sha256", self.sha256.lower())


@dataclass(frozen=True, slots=True)
class ProcessStreamWriteResult:
    paths: StreamPaths
    stdout: ProcessStreamArtifact
    stderr: ProcessStreamArtifact
    copied: bool

    def __post_init__(self) -> None:
        if self.stdout.stream is not ProcessStreamName.STDOUT:
            raise ValueError("stdout artifact must identify stdout")
        if self.stderr.stream is not ProcessStreamName.STDERR:
            raise ValueError("stderr artifact must identify stderr")
        if self.stdout.path != self.paths.stdout:
            raise ValueError("stdout artifact path does not match StreamPaths")
        if self.stderr.path != self.paths.stderr:
            raise ValueError("stderr artifact path does not match StreamPaths")
        if type(self.copied) is not bool:
            raise TypeError("copied must be bool")

    @property
    def complete(self) -> bool:
        return (
            self.stdout.state is not ProcessStreamState.MISSING
            and self.stderr.state is not ProcessStreamState.MISSING
        )

    @property
    def total_size_bytes(self) -> int | None:
        if not self.complete:
            return None
        assert self.stdout.size_bytes is not None
        assert self.stderr.size_bytes is not None
        return self.stdout.size_bytes + self.stderr.size_bytes


@runtime_checkable
class ProcessStreamCaptureLike(Protocol):
    stdout: object
    stderr: object


class ProcessStreamWriter:
    __slots__ = ("_run_root", "_sync")

    def __init__(self, run_root: Path, *, sync: bool = True) -> None:
        self._run_root = _coerce_absolute_path(run_root, "run_root")
        if type(sync) is not bool:
            raise TypeError("sync must be bool")
        self._sync = sync

    @property
    def run_root(self) -> Path:
        return self._run_root

    def inspect(
        self,
        capture: object,
        *,
        require_both: bool = True,
        verify_declared_sizes: bool = True,
    ) -> ProcessStreamWriteResult:
        source_paths = stream_paths_from_capture(capture)
        _require_contained_pair(source_paths, self._run_root)
        result = inspect_process_streams(
            source_paths,
            require_both=require_both,
        )
        if verify_declared_sizes:
            _verify_declared_sizes(capture, result)
        return result

    def write(
        self,
        capture: object,
        destinations: StreamPaths | None = None,
        *,
        require_both: bool = True,
        verify_declared_sizes: bool = True,
    ) -> ProcessStreamWriteResult:
        source_paths = stream_paths_from_capture(capture)
        target_paths = source_paths if destinations is None else destinations
        _require_contained_pair(target_paths, self._run_root)
        copied = _path_key(source_paths.stdout) != _path_key(target_paths.stdout) or _path_key(
            source_paths.stderr
        ) != _path_key(target_paths.stderr)
        if copied:
            _copy_pair_atomic(
                source_paths,
                target_paths,
                sync=self._sync,
                require_both=require_both,
            )
        result = inspect_process_streams(target_paths, require_both=require_both)
        if verify_declared_sizes:
            _verify_declared_sizes(capture, result)
        return ProcessStreamWriteResult(
            paths=result.paths,
            stdout=result.stdout,
            stderr=result.stderr,
            copied=copied,
        )


def write_stream_capture(
    result: object,
    destinations: StreamPaths | None = None,
    *,
    run_root: Path | None = None,
    require_both: bool = True,
    verify_declared_sizes: bool = True,
    sync: bool = True,
) -> StreamPaths:
    effective_root = _resolve_run_root(result, destinations, run_root)
    written = ProcessStreamWriter(effective_root, sync=sync).write(
        result,
        destinations,
        require_both=require_both,
        verify_declared_sizes=verify_declared_sizes,
    )
    return written.paths


def write_process_streams(
    result: object,
    destinations: StreamPaths | None = None,
    *,
    run_root: Path | None = None,
    require_both: bool = True,
    verify_declared_sizes: bool = True,
    sync: bool = True,
) -> ProcessStreamWriteResult:
    effective_root = _resolve_run_root(result, destinations, run_root)
    return ProcessStreamWriter(effective_root, sync=sync).write(
        result,
        destinations,
        require_both=require_both,
        verify_declared_sizes=verify_declared_sizes,
    )


def inspect_process_streams(
    paths: StreamPaths,
    *,
    require_both: bool = True,
) -> ProcessStreamWriteResult:
    if not isinstance(paths, StreamPaths):
        raise TypeError("paths must be StreamPaths")
    if type(require_both) is not bool:
        raise TypeError("require_both must be bool")
    stdout = inspect_process_stream(ProcessStreamName.STDOUT, paths.stdout)
    stderr = inspect_process_stream(ProcessStreamName.STDERR, paths.stderr)
    if require_both:
        missing = tuple(
            artifact.stream.value
            for artifact in (stdout, stderr)
            if artifact.state is ProcessStreamState.MISSING
        )
        if missing:
            raise ReportError(
                "required process stream evidence is missing: " + ", ".join(missing)
            )
    return ProcessStreamWriteResult(
        paths=paths,
        stdout=stdout,
        stderr=stderr,
        copied=False,
    )


def inspect_process_stream(
    stream: ProcessStreamName | str,
    path: Path,
) -> ProcessStreamArtifact:
    canonical_stream = _coerce_stream(stream)
    canonical_path = _coerce_absolute_path(path, "path")
    if not canonical_path.exists():
        return ProcessStreamArtifact(
            stream=canonical_stream,
            path=canonical_path,
            state=ProcessStreamState.MISSING,
            size_bytes=None,
            sha256=None,
        )
    if not canonical_path.is_file() or canonical_path.is_symlink():
        raise ReportError(f"process stream path is not a regular file: {canonical_path}")
    size = canonical_path.stat().st_size
    digest = _sha256_file(canonical_path)
    return ProcessStreamArtifact(
        stream=canonical_stream,
        path=canonical_path,
        state=ProcessStreamState.EMPTY if size == 0 else ProcessStreamState.PRESENT,
        size_bytes=size,
        sha256=digest,
    )


def stream_paths_from_capture(capture: object) -> StreamPaths:
    direct_stdout = _member(capture, "stdout_path")
    direct_stderr = _member(capture, "stderr_path")
    if direct_stdout is not None or direct_stderr is not None:
        if direct_stdout is None or direct_stderr is None:
            raise ContractViolationError(
                "capture must provide both stdout_path and stderr_path"
            )
        return StreamPaths(Path(direct_stdout), Path(direct_stderr))
    stdout = _member(capture, "stdout")
    stderr = _member(capture, "stderr")
    if stdout is None or stderr is None:
        raise ContractViolationError(
            "capture must provide stdout/stderr summaries or direct stream paths"
        )
    stdout_path = _member(stdout, "path")
    stderr_path = _member(stderr, "path")
    if stdout_path is None or stderr_path is None:
        raise ContractViolationError("stream summaries must provide paths")
    return StreamPaths(Path(stdout_path), Path(stderr_path))


def validate_stream_paths(
    paths: StreamPaths,
    *,
    run_root: Path,
) -> StreamPaths:
    if not isinstance(paths, StreamPaths):
        raise TypeError("paths must be StreamPaths")
    root = _coerce_absolute_path(run_root, "run_root")
    _require_contained_pair(paths, root)
    return paths


def _copy_pair_atomic(
    sources: StreamPaths,
    destinations: StreamPaths,
    *,
    sync: bool,
    require_both: bool,
) -> None:
    source_states = (
        inspect_process_stream(ProcessStreamName.STDOUT, sources.stdout),
        inspect_process_stream(ProcessStreamName.STDERR, sources.stderr),
    )
    if require_both and any(
        item.state is ProcessStreamState.MISSING for item in source_states
    ):
        raise ReportError("cannot publish missing required process stream evidence")
    for source, destination in zip(source_states, destinations.as_tuple(), strict=True):
        if source.state is ProcessStreamState.MISSING:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        _copy_file_atomic(source.path, destination, sync=sync)
        published = inspect_process_stream(source.stream, destination)
        if published.size_bytes != source.size_bytes or published.sha256 != source.sha256:
            raise ReportError(f"published process stream verification failed: {destination}")


def _copy_file_atomic(source: Path, destination: Path, *, sync: bool) -> None:
    if _path_key(source) == _path_key(destination):
        return
    try:
        with source.open("rb") as input_stream:
            with atomic_binary_writer(
                destination,
                sync=sync,
                preserve_existing_mode=True,
            ) as output_stream:
                while block := input_stream.read(_COPY_CHUNK_SIZE):
                    output_stream.write(block)
    except OSError as exc:
        raise ReportError(
            f"could not publish process stream {source} to {destination}"
        ) from exc


def _verify_declared_sizes(
    capture: object,
    result: ProcessStreamWriteResult,
) -> None:
    expected_stdout = _declared_size(capture, ProcessStreamName.STDOUT)
    expected_stderr = _declared_size(capture, ProcessStreamName.STDERR)
    for expected, artifact in (
        (expected_stdout, result.stdout),
        (expected_stderr, result.stderr),
    ):
        if expected is None:
            continue
        if artifact.size_bytes != expected:
            raise ReportError(
                f"{artifact.stream.value} size mismatch: declared={expected}, "
                f"observed={artifact.size_bytes}"
            )


def _declared_size(
    capture: object,
    stream: ProcessStreamName,
) -> int | None:
    direct = _member(capture, f"{stream.value}_size_bytes")
    if direct is None:
        summary = _member(capture, stream.value)
        direct = None if summary is None else _member(summary, "size_bytes")
    if direct is None:
        return None
    if type(direct) is not int or direct < 0:
        raise ContractViolationError(
            f"declared {stream.value} size must be a non-negative integer"
        )
    return direct


def _resolve_run_root(
    result: object,
    destinations: StreamPaths | None,
    explicit: Path | None,
) -> Path:
    if explicit is not None:
        return _coerce_absolute_path(explicit, "run_root")
    candidate = _member(result, "run_root")
    if candidate is not None:
        return _coerce_absolute_path(Path(candidate), "run_root")
    paths = destinations if destinations is not None else stream_paths_from_capture(result)
    return Path(os.path.commonpath((paths.stdout.parent, paths.stderr.parent))).resolve()


def _require_contained_pair(paths: StreamPaths, run_root: Path) -> None:
    for path in paths.as_tuple():
        try:
            path.relative_to(run_root)
        except ValueError as exc:
            raise ContractViolationError(
                f"process stream path escapes run root: {path}"
            ) from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while block := stream.read(_COPY_CHUNK_SIZE):
                digest.update(block)
    except OSError as exc:
        raise ReportError(f"could not read process stream: {path}") from exc
    return digest.hexdigest()


def _member(value: object, name: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _coerce_stream(value: ProcessStreamName | str) -> ProcessStreamName:
    if isinstance(value, ProcessStreamName):
        return value
    if not isinstance(value, str):
        raise TypeError("stream must be ProcessStreamName or string")
    try:
        return ProcessStreamName(value)
    except ValueError as exc:
        raise ValueError(f"unknown process stream {value!r}") from exc


def _coerce_absolute_path(value: Path, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return value.resolve(strict=False)


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


__all__ = (
    "ProcessStreamArtifact",
    "ProcessStreamCaptureLike",
    "ProcessStreamName",
    "ProcessStreamState",
    "ProcessStreamWriteResult",
    "ProcessStreamWriter",
    "StreamPaths",
    "inspect_process_stream",
    "inspect_process_streams",
    "stream_paths_from_capture",
    "validate_stream_paths",
    "write_process_streams",
    "write_stream_capture",
)
