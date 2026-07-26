"""Unit tests for atomic sibling-file publication."""

from __future__ import annotations

import errno
import os
from pathlib import Path
import stat
from typing import Any, cast

import pytest

from gf_wordbench.infrastructure import atomic_io
from gf_wordbench.infrastructure.atomic_io import (
    atomic_binary_writer,
    atomic_text_writer,
    atomic_write_bytes,
    atomic_write_text,
)
from gf_wordbench.infrastructure.filesystem import PathContainmentError


def _temporary_paths(destination: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            destination.parent.glob(f".{destination.name}.*.tmp"),
            key=lambda path: path.name,
        )
    )


def _supports_symlinks(tmp_path: Path) -> bool:
    target = tmp_path / "symlink-target"
    link = tmp_path / "symlink-probe"
    target.write_text("target", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        return False
    else:
        link.unlink()
        return True


def test_atomic_write_bytes_creates_file_and_returns_absolute_path(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "payload.bin"

    result = atomic_write_bytes(destination, b"\x00\x01wordbench")

    assert result == destination
    assert result.is_absolute()
    assert destination.read_bytes() == b"\x00\x01wordbench"
    assert _temporary_paths(destination) == ()


def test_atomic_write_bytes_accepts_bytearray_and_memoryview(
    tmp_path: Path,
) -> None:
    bytearray_destination = tmp_path / "bytearray.bin"
    memoryview_destination = tmp_path / "memoryview.bin"

    atomic_write_bytes(bytearray_destination, bytearray(b"abc"))
    atomic_write_bytes(memoryview_destination, memoryview(b"def"))

    assert bytearray_destination.read_bytes() == b"abc"
    assert memoryview_destination.read_bytes() == b"def"


def test_atomic_write_text_uses_strict_encoding_and_requested_newlines(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "unicode.txt"

    atomic_write_text(
        destination,
        "élève\nété\n",
        encoding="utf-8",
        newline="\r\n",
    )

    assert destination.read_bytes() == "élève\r\nété\r\n".encode()


def test_atomic_write_text_replaces_existing_file_without_partial_content(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("old-valid-document", encoding="utf-8")

    with atomic_text_writer(destination) as stream:
        stream.write("new-valid-document")
        assert destination.read_text(encoding="utf-8") == "old-valid-document"
        temporary_paths = _temporary_paths(destination)
        assert len(temporary_paths) == 1
        assert temporary_paths[0].parent == destination.parent
        assert temporary_paths[0].name.startswith(f".{destination.name}.")
        assert temporary_paths[0].name.endswith(".tmp")

    assert destination.read_text(encoding="utf-8") == "new-valid-document"
    assert _temporary_paths(destination) == ()


def test_atomic_binary_writer_publishes_only_after_context_exit(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "artifact.bin"

    with atomic_binary_writer(destination) as stream:
        stream.write(b"complete")
        assert not destination.exists()
        assert len(_temporary_paths(destination)) == 1

    assert destination.read_bytes() == b"complete"
    assert _temporary_paths(destination) == ()


def test_last_completed_atomic_writer_wins(tmp_path: Path) -> None:
    destination = tmp_path / "summary.json"
    destination.write_text("initial", encoding="utf-8")

    with atomic_text_writer(destination) as first:
        first.write("first")
        with atomic_text_writer(destination) as second:
            second.write("second")
        assert destination.read_text(encoding="utf-8") == "second"

    assert destination.read_text(encoding="utf-8") == "first"


def test_exception_inside_writer_preserves_previous_file_and_cleans_temporary(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_text("previous", encoding="utf-8")

    with pytest.raises(RuntimeError, match="render failed"):
        with atomic_text_writer(destination) as stream:
            stream.write("incomplete")
            raise RuntimeError("render failed")

    assert destination.read_text(encoding="utf-8") == "previous"
    assert _temporary_paths(destination) == ()


def test_validator_observes_closed_complete_temporary_file(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "summary.json"
    observations: list[tuple[Path, bytes]] = []

    def validator(path: Path) -> None:
        observations.append((path, path.read_bytes()))

    atomic_write_text(destination, '{"status":"OK"}\n', validator=validator)

    assert len(observations) == 1
    temporary_path, payload = observations[0]
    assert temporary_path.parent == destination.parent
    assert temporary_path != destination
    assert payload == b'{"status":"OK"}\n'
    assert not temporary_path.exists()


def test_validator_failure_preserves_previous_file_and_cleans_temporary(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "summary.json"
    destination.write_text("previous", encoding="utf-8")

    def reject(path: Path) -> None:
        assert path.read_text(encoding="utf-8") == "invalid"
        raise ValueError("schema validation failed")

    with pytest.raises(ValueError, match="schema validation failed") as captured:
        atomic_write_text(destination, "invalid", validator=reject)

    assert destination.read_text(encoding="utf-8") == "previous"
    assert _temporary_paths(destination) == ()
    notes = getattr(captured.value, "__notes__", ())
    assert any("atomic destination:" in note for note in notes)
    assert any("atomic temporary file:" in note for note in notes)


def test_failed_write_can_retain_temporary_file_for_explicit_recovery(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "summary.json"
    destination.write_text("previous", encoding="utf-8")

    def reject(_: Path) -> None:
        raise ValueError("validation failed")

    with pytest.raises(ValueError, match="validation failed"):
        atomic_write_text(
            destination,
            "candidate",
            validator=reject,
            keep_temporary_on_failure=True,
        )

    temporary_paths = _temporary_paths(destination)
    assert len(temporary_paths) == 1
    assert temporary_paths[0].read_text(encoding="utf-8") == "candidate"
    assert destination.read_text(encoding="utf-8") == "previous"


def test_disappearing_temporary_file_is_detected_before_replacement(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "summary.json"
    destination.write_text("previous", encoding="utf-8")

    def remove_temporary(path: Path) -> None:
        path.unlink()

    with pytest.raises(FileNotFoundError, match="temporary file disappeared"):
        atomic_write_text(destination, "candidate", validator=remove_temporary)

    assert destination.read_text(encoding="utf-8") == "previous"
    assert _temporary_paths(destination) == ()


def test_caller_closing_stream_is_rejected_without_replacing_destination(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("previous", encoding="utf-8")

    with pytest.raises(ValueError, match="closed by the caller"):
        with atomic_text_writer(destination) as stream:
            stream.write("candidate")
            stream.close()

    assert destination.read_text(encoding="utf-8") == "previous"
    assert _temporary_paths(destination) == ()


def test_create_parents_is_explicit(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "deeper" / "result.txt"

    with pytest.raises(FileNotFoundError):
        atomic_write_text(destination, "value")

    result = atomic_write_text(destination, "value", create_parents=True)

    assert result == destination
    assert destination.read_text(encoding="utf-8") == "value"


def test_root_containment_accepts_inside_and_rejects_outside(
    tmp_path: Path,
) -> None:
    root = tmp_path / "owned"
    root.mkdir()
    inside = root / "summary.json"
    outside = tmp_path / "outside.json"

    atomic_write_text(inside, "inside", root=root)

    with pytest.raises(PathContainmentError, match="escapes its required root"):
        atomic_write_text(outside, "outside", root=root)

    assert inside.read_text(encoding="utf-8") == "inside"
    assert not outside.exists()


def test_symlinked_parent_escape_is_rejected(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("symlink creation is unavailable")

    root = tmp_path / "owned"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "redirect").symlink_to(outside, target_is_directory=True)
    destination = root / "redirect" / "summary.json"

    with pytest.raises(PathContainmentError):
        atomic_write_text(destination, "outside", root=root)

    assert not (outside / "summary.json").exists()


def test_destination_symlink_is_rejected(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("symlink creation is unavailable")

    target = tmp_path / "target.txt"
    destination = tmp_path / "destination.txt"
    target.write_text("target", encoding="utf-8")
    destination.symlink_to(target)

    with pytest.raises(OSError) as captured:
        atomic_write_text(destination, "replacement")

    assert captured.value.errno == errno.ELOOP
    assert target.read_text(encoding="utf-8") == "target"
    assert destination.is_symlink()


def test_destination_directory_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "not-a-file"
    destination.mkdir()

    with pytest.raises(IsADirectoryError):
        atomic_write_text(destination, "value")


@pytest.mark.skipif(os.name == "nt", reason="FIFO contract is POSIX-specific")
def test_non_regular_destination_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "pipe"
    os.mkfifo(destination)

    with pytest.raises(OSError) as captured:
        atomic_write_text(destination, "value")

    assert captured.value.errno == errno.EINVAL


def test_destination_path_must_be_absolute_text_and_nul_free(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="must be absolute"):
        atomic_write_text(Path("relative.txt"), "value")

    with pytest.raises(TypeError, match="must be text"):
        atomic_write_bytes(cast(Any, os.fsencode(tmp_path / "bytes.bin")), b"value")

    with pytest.raises(ValueError, match="contains NUL"):
        atomic_write_text(cast(Any, f"{tmp_path}{os.sep}bad\x00name"), "value")


def test_text_and_common_option_validation(tmp_path: Path) -> None:
    destination = tmp_path / "value.txt"

    with pytest.raises(TypeError, match="text must be a string"):
        atomic_write_text(destination, cast(Any, b"value"))
    with pytest.raises(TypeError, match="encoding must be a string"):
        atomic_write_text(destination, "value", encoding=cast(Any, 1))
    with pytest.raises(ValueError, match="encoding cannot be empty"):
        atomic_write_text(destination, "value", encoding="")
    with pytest.raises(ValueError, match="encoding cannot contain NUL"):
        atomic_write_text(destination, "value", encoding="utf\x00-8")
    with pytest.raises(ValueError, match="newline must be"):
        atomic_write_text(destination, "value", newline="invalid")
    with pytest.raises(TypeError, match="create_parents must be a boolean"):
        atomic_write_text(destination, "value", create_parents=cast(Any, 1))
    with pytest.raises(TypeError, match="role must be a string"):
        atomic_write_text(destination, "value", role=cast(Any, 1))
    with pytest.raises(ValueError, match="role cannot be empty"):
        atomic_write_text(destination, "value", role=" ")
    with pytest.raises(ValueError, match="role cannot contain NUL"):
        atomic_write_text(destination, "value", role="state\x00file")
    with pytest.raises(TypeError, match="validator must be callable"):
        atomic_write_text(destination, "value", validator=cast(Any, object()))


@pytest.mark.parametrize(
    "delays",
    [
        "0.1",
        b"0.1",
        [True],
        [object()],
    ],
)
def test_retry_delays_reject_non_numeric_sequences(
    tmp_path: Path,
    delays: object,
) -> None:
    with pytest.raises(TypeError):
        atomic_write_text(
            tmp_path / "value.txt",
            "value",
            replace_retry_delays=cast(Any, delays),
        )


@pytest.mark.parametrize("delay", [-1, float("inf"), float("-inf"), float("nan")])
def test_retry_delays_must_be_finite_and_non_negative(
    tmp_path: Path,
    delay: float,
) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        atomic_write_text(
            tmp_path / "value.txt",
            "value",
            replace_retry_delays=(delay,),
        )


@pytest.mark.parametrize("mode", [True, -1, 0o10000, 1.5, "644"])
def test_file_mode_validation(tmp_path: Path, mode: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        atomic_write_text(
            tmp_path / "value.txt",
            "value",
            file_mode=cast(Any, mode),
        )


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are required")
def test_existing_mode_is_preserved_by_default(tmp_path: Path) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("old", encoding="utf-8")
    destination.chmod(0o640)

    atomic_write_text(destination, "new")

    assert stat.S_IMODE(destination.stat().st_mode) == 0o640


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are required")
def test_explicit_file_mode_overrides_existing_mode(tmp_path: Path) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("old", encoding="utf-8")
    destination.chmod(0o600)

    atomic_write_text(destination, "new", file_mode=0o644)

    assert stat.S_IMODE(destination.stat().st_mode) == 0o644


def test_sync_true_flushes_with_fsync(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[int] = []
    monkeypatch.setattr(atomic_io.os, "fsync", calls.append)

    atomic_write_text(tmp_path / "state.json", "value", sync=True)

    assert len(calls) == 1
    assert calls[0] >= 0


def test_sync_false_skips_fsync(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def unexpected_fsync(_: int) -> None:
        raise AssertionError("fsync must not be called")

    monkeypatch.setattr(atomic_io.os, "fsync", unexpected_fsync)

    atomic_write_text(tmp_path / "state.json", "value", sync=False)


def test_retryable_replace_failures_are_retried_in_declared_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("old", encoding="utf-8")
    real_replace = atomic_io.os.replace
    replace_calls: list[tuple[Path, Path]] = []
    sleep_calls: list[float] = []

    def flaky_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        source_path = Path(source)
        target_path = Path(target)
        replace_calls.append((source_path, target_path))
        if len(replace_calls) < 3:
            raise PermissionError(errno.EACCES, "temporarily locked")
        real_replace(source_path, target_path)

    monkeypatch.setattr(atomic_io.os, "replace", flaky_replace)
    monkeypatch.setattr(atomic_io.time, "sleep", sleep_calls.append)

    atomic_write_text(
        destination,
        "new",
        replace_retry_delays=(0.01, 0.02),
    )

    assert destination.read_text(encoding="utf-8") == "new"
    assert len(replace_calls) == 3
    assert all(target == destination for _, target in replace_calls)
    assert sleep_calls == [0.01, 0.02]
    assert _temporary_paths(destination) == ()


def test_non_retryable_replace_failure_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "state.json"
    destination.write_text("old", encoding="utf-8")
    replace_calls = 0
    sleep_calls: list[float] = []

    def failing_replace(_: object, __: object) -> None:
        nonlocal replace_calls
        replace_calls += 1
        raise OSError(errno.EXDEV, "cross-device replacement")

    monkeypatch.setattr(atomic_io.os, "replace", failing_replace)
    monkeypatch.setattr(atomic_io.time, "sleep", sleep_calls.append)

    with pytest.raises(OSError) as captured:
        atomic_write_text(
            destination,
            "new",
            replace_retry_delays=(0.01, 0.02),
        )

    assert captured.value.errno == errno.EXDEV
    assert replace_calls == 1
    assert sleep_calls == []
    assert destination.read_text(encoding="utf-8") == "old"
    assert _temporary_paths(destination) == ()
