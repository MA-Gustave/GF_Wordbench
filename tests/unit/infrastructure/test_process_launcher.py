"""Unit tests for shell-free platform process launching."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import BinaryIO, cast

import pytest

import gf_wordbench.infrastructure.process.launcher as process_launcher
from gf_wordbench.infrastructure.process.launcher import ProcessHandle, StandardInput


@dataclass(slots=True)
class _DispatchCall:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]
    stdin: BinaryIO | int
    stdout: BinaryIO
    stderr: BinaryIO


def _handle() -> ProcessHandle:
    return cast("ProcessHandle", object())


def _streams() -> tuple[BytesIO, BytesIO]:
    return BytesIO(), BytesIO()


def test_launch_rejects_shared_capture_stream_before_dispatch() -> None:
    capture = BytesIO()

    with pytest.raises(
        ValueError,
        match="stdout and stderr capture streams must be distinct",
    ):
        process_launcher.launch_without_shell(
            executable=Path("python.exe"),
            args=("--version",),
            cwd=Path("workspace"),
            env={},
            stdin=None,
            stdout=capture,
            stderr=capture,
        )


def test_windows_dispatch_preserves_arguments_and_copies_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_handle = _handle()
    calls: list[_DispatchCall] = []
    stdout, stderr = _streams()
    original_environment = {"TOKEN": "value", "UNICODE": "français"}
    arguments = (
        "",
        "value with spaces",
        "--path=C:/Program Files/GF/rgl",
        "; echo not-a-command",
    )

    def fake_windows_launch(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str],
        stdin: BinaryIO | int,
        stdout: BinaryIO,
        stderr: BinaryIO,
    ) -> ProcessHandle:
        calls.append(_DispatchCall(command, cwd, env, stdin, stdout, stderr))
        env["MUTATED_BY_CHILD"] = "yes"
        return expected_handle

    monkeypatch.setattr(
        process_launcher,
        "os",
        SimpleNamespace(name="nt", fspath=os.fspath),
    )
    monkeypatch.setattr(process_launcher, "_launch_windows", fake_windows_launch)

    result = process_launcher.launch_without_shell(
        executable=Path(r"C:\Program Files\GF Wordbench\gf-wordbench.exe"),
        args=arguments,
        cwd=Path(r"C:\workspace with spaces"),
        env=original_environment,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
    )

    assert result is expected_handle
    assert len(calls) == 1
    call = calls[0]
    assert call.command == (
        r"C:\Program Files\GF Wordbench\gf-wordbench.exe",
        *arguments,
    )
    assert call.cwd == Path(r"C:\workspace with spaces")
    assert call.env["TOKEN"] == "value"
    assert call.env["UNICODE"] == "français"
    assert call.stdin == subprocess.DEVNULL
    assert call.stdout is stdout
    assert call.stderr is stderr
    assert original_environment == {"TOKEN": "value", "UNICODE": "français"}


def test_posix_dispatch_converts_missing_stdin_to_devnull(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_handle = _handle()
    calls: list[_DispatchCall] = []
    stdout, stderr = _streams()

    def fake_posix_launch(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str],
        stdin: BinaryIO | int,
        stdout: BinaryIO,
        stderr: BinaryIO,
    ) -> ProcessHandle:
        calls.append(_DispatchCall(command, cwd, env, stdin, stdout, stderr))
        return expected_handle

    monkeypatch.setattr(
        process_launcher,
        "os",
        SimpleNamespace(name="posix", fspath=os.fspath),
    )
    monkeypatch.setattr(process_launcher, "_launch_posix", fake_posix_launch)

    result = process_launcher.launch_without_shell(
        executable=Path("/opt/gf wordbench/bin/gf-wordbench"),
        args=("validate", "--target", "source with spaces.gf"),
        cwd=Path("/workspace with spaces"),
        env={"LANG": "C.UTF-8"},
        stdin=None,
        stdout=stdout,
        stderr=stderr,
    )

    assert result is expected_handle
    assert len(calls) == 1
    call = calls[0]
    assert call.command == (
        "/opt/gf wordbench/bin/gf-wordbench",
        "validate",
        "--target",
        "source with spaces.gf",
    )
    assert call.stdin == subprocess.DEVNULL
    assert call.stdout is stdout
    assert call.stderr is stderr


def test_explicit_stdin_stream_is_forwarded_without_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_handle = _handle()
    stdin = BytesIO(b"parse -lang=Eng\n")
    stdout, stderr = _streams()
    observed: list[StandardInput] = []

    def fake_posix_launch(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str],
        stdin: BinaryIO | int,
        stdout: BinaryIO,
        stderr: BinaryIO,
    ) -> ProcessHandle:
        del command, cwd, env, stdout, stderr
        observed.append(stdin)
        return expected_handle

    monkeypatch.setattr(
        process_launcher,
        "os",
        SimpleNamespace(name="posix", fspath=os.fspath),
    )
    monkeypatch.setattr(process_launcher, "_launch_posix", fake_posix_launch)

    result = process_launcher.launch_without_shell(
        executable=Path("/usr/bin/gf"),
        args=("-run",),
        cwd=Path("/workspace"),
        env={},
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    assert result is expected_handle
    assert observed == [stdin]


def test_unsupported_platform_fails_without_starting_a_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _streams()
    monkeypatch.setattr(
        process_launcher,
        "os",
        SimpleNamespace(name="unsupported", fspath=os.fspath),
    )

    with pytest.raises(
        RuntimeError,
        match="Unsupported process-launch platform: 'unsupported'",
    ):
        process_launcher.launch_without_shell(
            executable=Path("gf-wordbench"),
            args=("--help",),
            cwd=Path("workspace"),
            env={},
            stdin=None,
            stdout=stdout,
            stderr=stderr,
        )


def test_windows_launch_uses_shell_free_owned_process_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_handle = _handle()
    captured_command: list[Sequence[str]] = []
    captured_options: list[Mapping[str, object]] = []
    stdout, stderr = _streams()
    stdin = BytesIO(b"input")

    def fake_popen(
        command: Sequence[str],
        **options: object,
    ) -> ProcessHandle:
        captured_command.append(command)
        captured_options.append(options)
        return expected_handle

    monkeypatch.setattr(process_launcher, "_WINDOWS_NEW_PROCESS_GROUP", 512)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = process_launcher._launch_windows(
        command=(r"C:\Program Files\GF\gf.exe", "--version"),
        cwd=Path(r"C:\workspace with spaces"),
        env={"PATH": "controlled"},
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    assert result is expected_handle
    assert captured_command == [(r"C:\Program Files\GF\gf.exe", "--version")]
    assert captured_options == [
        {
            "cwd": r"C:\workspace with spaces",
            "env": {"PATH": "controlled"},
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr,
            "shell": False,
            "close_fds": True,
            "bufsize": 0,
            "text": False,
            "creationflags": 512,
        }
    ]


def test_windows_launch_rejects_unavailable_process_group_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _streams()
    monkeypatch.setattr(process_launcher, "_WINDOWS_NEW_PROCESS_GROUP", 0)

    with pytest.raises(
        RuntimeError,
        match="Windows process-group creation is unavailable",
    ):
        process_launcher._launch_windows(
            command=("gf.exe",),
            cwd=Path("workspace"),
            env={},
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
        )


def test_posix_launch_uses_shell_free_new_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_handle = _handle()
    captured_command: list[Sequence[str]] = []
    captured_options: list[Mapping[str, object]] = []
    stdout, stderr = _streams()

    def fake_popen(
        command: Sequence[str],
        **options: object,
    ) -> ProcessHandle:
        captured_command.append(command)
        captured_options.append(options)
        return expected_handle

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = process_launcher._launch_posix(
        command=("/usr/bin/gf", "--version"),
        cwd=Path("/workspace with spaces"),
        env={"LANG": "C.UTF-8"},
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
    )

    assert result is expected_handle
    assert captured_command == [("/usr/bin/gf", "--version")]
    assert captured_options == [
        {
            "cwd": "/workspace with spaces",
            "env": {"LANG": "C.UTF-8"},
            "stdin": subprocess.DEVNULL,
            "stdout": stdout,
            "stderr": stderr,
            "shell": False,
            "close_fds": True,
            "bufsize": 0,
            "text": False,
            "restore_signals": True,
            "start_new_session": True,
        }
    ]


@pytest.mark.parametrize("platform", ["windows", "posix"])
def test_operating_system_launch_errors_propagate_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
) -> None:
    stdout, stderr = _streams()
    expected = FileNotFoundError("executable not found")

    def failing_popen(
        command: Sequence[str],
        **options: object,
    ) -> ProcessHandle:
        del command, options
        raise expected

    monkeypatch.setattr(subprocess, "Popen", failing_popen)
    if platform == "windows":
        monkeypatch.setattr(process_launcher, "_WINDOWS_NEW_PROCESS_GROUP", 512)
        launch = process_launcher._launch_windows
        kwargs: dict[str, object] = {
            "command": ("missing.exe",),
            "cwd": Path("workspace"),
            "env": {},
            "stdin": subprocess.DEVNULL,
            "stdout": stdout,
            "stderr": stderr,
        }
    else:
        launch = process_launcher._launch_posix
        kwargs = {
            "command": ("missing",),
            "cwd": Path("workspace"),
            "env": {},
            "stdin": subprocess.DEVNULL,
            "stdout": stdout,
            "stderr": stderr,
        }

    with pytest.raises(FileNotFoundError) as captured:
        launch(**kwargs)  # type: ignore[arg-type]

    assert captured.value is expected


def test_public_surface_exposes_only_supported_launcher_symbols() -> None:
    assert process_launcher.__all__ == (
        "ProcessHandle",
        "StandardInput",
        "launch_without_shell",
    )
