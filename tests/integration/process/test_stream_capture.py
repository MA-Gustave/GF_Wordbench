from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path

from gf_wordbench.infrastructure.process.streams import ProcessStreamCapture


def _capture(
    tmp_path: Path,
    *,
    stdout: bytes,
    stderr: bytes,
    output_limit_bytes: int,
    chunk_size: int,
    on_output_limit: Callable[[], None] | None = None,
) -> tuple[ProcessStreamCapture, Path, Path]:
    stdout_path = (tmp_path / "evidence" / "process.stdout.bin").resolve()
    stderr_path = (tmp_path / "evidence" / "process.stderr.bin").resolve()
    capture = ProcessStreamCapture(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_limit_bytes=output_limit_bytes,
        chunk_size=chunk_size,
        on_output_limit=on_output_limit,
    )
    capture.open()
    capture.start(BytesIO(stdout), BytesIO(stderr))
    return capture, stdout_path, stderr_path


def test_stream_capture_preserves_separate_raw_byte_streams(
    tmp_path: Path,
) -> None:
    stdout = b"stdout-alpha\x00\xff\nstdout-omega\r\n"
    stderr = b"stderr-alpha\xfe\x80\nstderr-omega\n"
    capture, stdout_path, stderr_path = _capture(
        tmp_path,
        stdout=stdout,
        stderr=stderr,
        output_limit_bytes=len(stdout) + len(stderr) + 1,
        chunk_size=3,
    )

    summary = capture.finalize(drain_timeout_sec=2.0)

    assert stdout_path.read_bytes() == stdout
    assert stderr_path.read_bytes() == stderr
    assert summary.stdout.path == stdout_path
    assert summary.stderr.path == stderr_path
    assert summary.stdout.size_bytes == len(stdout)
    assert summary.stderr.size_bytes == len(stderr)
    assert summary.stdout.observed_size_bytes == len(stdout)
    assert summary.stderr.observed_size_bytes == len(stderr)
    assert summary.captured_size_bytes == len(stdout) + len(stderr)
    assert summary.observed_size_bytes == len(stdout) + len(stderr)
    assert summary.stdout.reached_eof
    assert summary.stderr.reached_eof
    assert summary.stdout.source_closed
    assert summary.stderr.source_closed
    assert summary.stdout.sink_closed
    assert summary.stderr.sink_closed
    assert not summary.stdout.truncated
    assert not summary.stderr.truncated
    assert not summary.output_limit_exceeded
    assert summary.capture_complete
    assert summary.failures == ()


def test_stream_capture_drains_large_stdout_and_stderr_without_deadlock(
    tmp_path: Path,
) -> None:
    stdout = b"OUT-" * (256 * 1024)
    stderr = b"ERR-" * (256 * 1024)
    capture, stdout_path, stderr_path = _capture(
        tmp_path,
        stdout=stdout,
        stderr=stderr,
        output_limit_bytes=len(stdout) + len(stderr) + 1,
        chunk_size=4093,
    )

    summary = capture.finalize(drain_timeout_sec=5.0)

    assert stdout_path.read_bytes() == stdout
    assert stderr_path.read_bytes() == stderr
    assert summary.captured_size_bytes == len(stdout) + len(stderr)
    assert summary.observed_size_bytes == len(stdout) + len(stderr)
    assert summary.capture_complete
    assert not summary.output_limit_exceeded
    assert summary.failures == ()


def test_stream_capture_enforces_one_combined_output_budget(
    tmp_path: Path,
) -> None:
    stdout = bytes(range(256)) * 512
    stderr = bytes(reversed(range(256))) * 512
    output_limit_bytes = 96 * 1024
    limit_notifications: list[None] = []

    capture, stdout_path, stderr_path = _capture(
        tmp_path,
        stdout=stdout,
        stderr=stderr,
        output_limit_bytes=output_limit_bytes,
        chunk_size=2048,
        on_output_limit=lambda: limit_notifications.append(None),
    )

    summary = capture.finalize(drain_timeout_sec=5.0)
    captured_stdout = stdout_path.read_bytes()
    captured_stderr = stderr_path.read_bytes()

    assert capture.output_limit_event.is_set()
    assert capture.output_limit_exceeded
    assert limit_notifications == [None]
    assert summary.output_limit_exceeded
    assert summary.output_limit_bytes == output_limit_bytes
    assert summary.captured_size_bytes == output_limit_bytes
    assert summary.observed_size_bytes == len(stdout) + len(stderr)
    assert len(captured_stdout) + len(captured_stderr) == output_limit_bytes
    assert stdout.startswith(captured_stdout)
    assert stderr.startswith(captured_stderr)
    assert summary.stdout.truncated or summary.stderr.truncated
    assert summary.stdout.reached_eof
    assert summary.stderr.reached_eof
    assert summary.stdout.source_closed
    assert summary.stderr.source_closed
    assert summary.stdout.sink_closed
    assert summary.stderr.sink_closed
    assert not summary.capture_complete
    assert summary.failures == ()


def test_stream_capture_finalization_is_idempotent(tmp_path: Path) -> None:
    capture, stdout_path, stderr_path = _capture(
        tmp_path,
        stdout=b"stdout",
        stderr=b"stderr",
        output_limit_bytes=1024,
        chunk_size=2,
    )

    first = capture.finalize(drain_timeout_sec=2.0)
    second = capture.finalize(drain_timeout_sec=0.0)

    assert second is first
    assert stdout_path.read_bytes() == b"stdout"
    assert stderr_path.read_bytes() == b"stderr"
