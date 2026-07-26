"""Unit tests for the canonical process-stream capture boundary."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

from gf_wordbench.infrastructure.process.streams import (
    CaptureSession,
    ProcessCapture,
    StreamCaptureSummary,
    open_capture_session,
)
from gf_wordbench.kernel.errors import ContractViolationError, EvidenceIOError


def _paths(tmp_path: Path, stem: str = "process") -> tuple[Path, Path]:
    evidence_root = (tmp_path / "raw" / "process").resolve()
    return (
        evidence_root / f"{stem}.stdout.bin",
        evidence_root / f"{stem}.stderr.bin",
    )


def _open(
    tmp_path: Path,
    *,
    stem: str = "process",
    output_limit_bytes: int = 4096,
) -> tuple[AbstractContextManager[CaptureSession], Path, Path]:
    stdout_path, stderr_path = _paths(tmp_path, stem)
    return (
        open_capture_session(
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_limit_bytes=output_limit_bytes,
        ),
        stdout_path,
        stderr_path,
    )


def _enter_capture_session(
    *,
    stdout_path: object,
    stderr_path: object,
    output_limit_bytes: object,
) -> CaptureSession:
    manager = open_capture_session(
        stdout_path=stdout_path,  # type: ignore[arg-type]
        stderr_path=stderr_path,  # type: ignore[arg-type]
        output_limit_bytes=output_limit_bytes,  # type: ignore[arg-type]
    )
    return manager.__enter__()


def test_stream_module_exposes_the_canonical_capture_vocabulary() -> None:
    assert is_dataclass(ProcessCapture)
    assert is_dataclass(StreamCaptureSummary)
    assert isinstance(CaptureSession, type)
    assert callable(open_capture_session)


def test_open_capture_session_creates_parent_directories_and_distinct_files(
    tmp_path: Path,
) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        assert stdout_path.parent.is_dir()
        assert stdout_path.is_file()
        assert stderr_path.is_file()
        assert stdout_path != stderr_path
        assert not capture.stdout.closed
        assert not capture.stderr.closed

    assert capture.stdout.closed
    assert capture.stderr.closed


def test_capture_preserves_stdout_and_stderr_as_separate_raw_bytes(
    tmp_path: Path,
) -> None:
    stdout = b"stdout-alpha\x00\xff\r\nstdout-omega\n"
    stderr = b"stderr-alpha\xfe\x80\nstderr-omega\r\n"
    manager, stdout_path, stderr_path = _open(
        tmp_path,
        output_limit_bytes=len(stdout) + len(stderr) + 1,
    )

    with manager as capture:
        capture.stdout.write(stdout)
        capture.stderr.write(stderr)
        capture.flush()
        result = capture.finalize()

    assert stdout_path.read_bytes() == stdout
    assert stderr_path.read_bytes() == stderr
    assert result.stdout.path == stdout_path
    assert result.stderr.path == stderr_path
    assert result.stdout.size_bytes == len(stdout)
    assert result.stderr.size_bytes == len(stderr)
    assert result.stdout.observed_size_bytes == len(stdout)
    assert result.stderr.observed_size_bytes == len(stderr)
    assert result.captured_size_bytes == len(stdout) + len(stderr)
    assert result.observed_size_bytes == len(stdout) + len(stderr)
    assert not result.output_limit_exceeded
    assert result.capture_complete
    assert result.failures == ()


def test_flush_makes_partial_evidence_visible_before_finalization(
    tmp_path: Path,
) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        capture.stdout.write(b"partial stdout")
        capture.stderr.write(b"partial stderr")
        capture.flush()

        assert stdout_path.read_bytes() == b"partial stdout"
        assert stderr_path.read_bytes() == b"partial stderr"
        assert not capture.output_limit_exceeded


def test_empty_streams_finalize_as_complete_evidence(tmp_path: Path) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        result = capture.finalize()

    assert stdout_path.read_bytes() == b""
    assert stderr_path.read_bytes() == b""
    assert result.stdout.size_bytes == 0
    assert result.stderr.size_bytes == 0
    assert result.stdout.source_closed
    assert result.stderr.source_closed
    assert result.stdout.sink_closed
    assert result.stderr.sink_closed
    assert result.stdout.reached_eof
    assert result.stderr.reached_eof
    assert result.capture_complete
    assert result.failures == ()


def test_one_empty_stream_does_not_merge_or_relabel_the_other(
    tmp_path: Path,
) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        capture.stderr.write(b"stderr only")
        result = capture.finalize()

    assert stdout_path.read_bytes() == b""
    assert stderr_path.read_bytes() == b"stderr only"
    assert result.stdout.stream == "stdout"
    assert result.stderr.stream == "stderr"
    assert result.stdout.size_bytes == 0
    assert result.stderr.size_bytes == len(b"stderr only")
    assert result.capture_complete


def test_output_limit_is_combined_across_stdout_and_stderr(
    tmp_path: Path,
) -> None:
    limit = 32
    stdout = b"o" * 24
    stderr = b"e" * 24
    manager, stdout_path, stderr_path = _open(
        tmp_path,
        output_limit_bytes=limit,
    )

    with manager as capture:
        capture.stdout.write(stdout)
        capture.stderr.write(stderr)
        capture.flush()

        assert capture.output_limit_exceeded
        result = capture.finalize()

    assert result.output_limit_bytes == limit
    assert result.output_limit_exceeded
    assert result.observed_size_bytes >= limit
    assert result.captured_size_bytes > 0
    assert stdout_path.exists()
    assert stderr_path.exists()
    captured_stdout = stdout_path.read_bytes()
    captured_stderr = stderr_path.read_bytes()
    assert stdout.startswith(captured_stdout)
    assert stderr.startswith(captured_stderr)
    assert not result.capture_complete


def test_limit_is_not_reported_when_combined_size_equals_limit(
    tmp_path: Path,
) -> None:
    limit = 16
    manager, _, _ = _open(tmp_path, output_limit_bytes=limit)

    with manager as capture:
        capture.stdout.write(b"a" * 7)
        capture.stderr.write(b"b" * 9)
        capture.flush()
        result = capture.finalize()

    assert result.captured_size_bytes == limit
    assert result.observed_size_bytes == limit
    assert not result.output_limit_exceeded
    assert result.capture_complete


def test_finalize_is_idempotent_and_returns_one_immutable_summary(
    tmp_path: Path,
) -> None:
    manager, _, _ = _open(tmp_path)

    with manager as capture:
        capture.stdout.write(b"stdout")
        first = capture.finalize()
        second = capture.finalize()

    assert second is first

    with pytest.raises(FrozenInstanceError):
        first.capture_complete = False  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        first.stdout.size_bytes = 0  # type: ignore[misc]


def test_context_manager_finalizes_partial_evidence_when_body_raises(
    tmp_path: Path,
) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)
    capture: CaptureSession | None = None

    with pytest.raises(RuntimeError, match="operation failed"):
        with manager as capture:
            capture.stdout.write(b"partial stdout")
            capture.stderr.write(b"partial stderr")
            raise RuntimeError("operation failed")

    assert capture is not None
    result = capture.finalize()
    assert stdout_path.read_bytes() == b"partial stdout"
    assert stderr_path.read_bytes() == b"partial stderr"
    assert capture.stdout.closed
    assert capture.stderr.closed
    assert result.stdout.size_bytes == len(b"partial stdout")
    assert result.stderr.size_bytes == len(b"partial stderr")


def test_finalized_capture_rejects_additional_writes(tmp_path: Path) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        capture.stdout.write(b"fixed")
        capture.stderr.write(b"evidence")
        capture.finalize()

    with pytest.raises((OSError, ValueError), match="closed|I/O operation"):
        capture.stdout.write(b"mutation")

    with pytest.raises((OSError, ValueError), match="closed|I/O operation"):
        capture.stderr.write(b"mutation")

    assert stdout_path.read_bytes() == b"fixed"
    assert stderr_path.read_bytes() == b"evidence"


@pytest.mark.parametrize(
    "output_limit_bytes",
    [0, -1, True, 1.5, float("inf"), float("nan"), "1024"],
)
def test_output_limit_must_be_a_finite_positive_integer(
    tmp_path: Path,
    output_limit_bytes: object,
) -> None:
    stdout_path, stderr_path = _paths(tmp_path)

    with pytest.raises(ContractViolationError, match="output_limit_bytes"):
        _enter_capture_session(
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_limit_bytes=output_limit_bytes,
        )


def test_capture_paths_must_be_path_instances(tmp_path: Path) -> None:
    stdout_path, stderr_path = _paths(tmp_path)

    with pytest.raises(ContractViolationError, match="stdout_path"):
        _enter_capture_session(
            stdout_path=str(stdout_path),
            stderr_path=stderr_path,
            output_limit_bytes=1,
        )


def test_capture_paths_must_be_absolute(tmp_path: Path) -> None:
    _, stderr_path = _paths(tmp_path)

    with pytest.raises(ContractViolationError, match="stdout_path"):
        _enter_capture_session(
            stdout_path=Path("relative.stdout.bin"),
            stderr_path=stderr_path,
            output_limit_bytes=1,
        )


def test_stdout_and_stderr_paths_must_be_distinct(tmp_path: Path) -> None:
    stdout_path, _ = _paths(tmp_path)

    with pytest.raises(ContractViolationError, match="distinct"):
        _enter_capture_session(
            stdout_path=stdout_path,
            stderr_path=stdout_path,
            output_limit_bytes=1,
        )


def test_existing_capture_file_is_not_overwritten_or_deleted(
    tmp_path: Path,
) -> None:
    stdout_path, stderr_path = _paths(tmp_path)
    stdout_path.parent.mkdir(parents=True)
    stdout_path.write_bytes(b"existing evidence")

    with pytest.raises(EvidenceIOError):
        _enter_capture_session(
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_limit_bytes=128,
        )

    assert stdout_path.read_bytes() == b"existing evidence"
    assert not stderr_path.exists()


def test_active_capture_paths_cannot_be_reused_concurrently(
    tmp_path: Path,
) -> None:
    first_stdout, first_stderr = _paths(tmp_path, "first")
    second_stderr = first_stderr.with_name("second.stderr.bin")

    with (
        open_capture_session(
            stdout_path=first_stdout,
            stderr_path=first_stderr,
            output_limit_bytes=128,
        ),
        pytest.raises(ContractViolationError, match="reserved"),
    ):
        _enter_capture_session(
            stdout_path=first_stdout,
            stderr_path=second_stderr,
            output_limit_bytes=128,
        )


def test_path_reservations_are_released_after_finalization(
    tmp_path: Path,
) -> None:
    stdout_path, stderr_path = _paths(tmp_path)

    with open_capture_session(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_limit_bytes=128,
    ) as capture:
        capture.finalize()

    stdout_path.unlink()
    stderr_path.unlink()

    with open_capture_session(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_limit_bytes=128,
    ) as capture:
        result = capture.finalize()

    assert result.capture_complete


def test_summary_paths_and_sizes_reflect_final_files(tmp_path: Path) -> None:
    manager, stdout_path, stderr_path = _open(tmp_path)

    with manager as capture:
        capture.stdout.write(b"abc")
        capture.stderr.write(b"12345")
        result = capture.finalize()

    assert result.stdout.path.resolve() == stdout_path.resolve()
    assert result.stderr.path.resolve() == stderr_path.resolve()
    assert result.stdout.size_bytes == stdout_path.stat().st_size == 3
    assert result.stderr.size_bytes == stderr_path.stat().st_size == 5
    assert result.captured_size_bytes == 8
