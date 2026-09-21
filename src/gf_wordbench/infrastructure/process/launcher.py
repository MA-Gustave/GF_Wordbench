"""Platform-contained, shell-free child-process launch primitives.

Requests are validated and capture files are opened by the process runner before
this module is called. Launch errors intentionally propagate as ``OSError`` so
the runner can normalize them into the canonical process result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import os
from pathlib import Path
import subprocess
from typing import BinaryIO, Final, TypeAlias

ProcessHandle: TypeAlias = subprocess.Popen[bytes]
StandardInput: TypeAlias = BinaryIO | int | None

_WINDOWS_NEW_PROCESS_GROUP: Final[int] = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
_WINDOWS_NO_WINDOW: Final[int] = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def launch_without_shell(
    *,
    executable: Path,
    args: Sequence[str],
    cwd: Path,
    env: Mapping[str, str],
    stdin: StandardInput,
    stdout: BinaryIO,
    stderr: BinaryIO,
) -> ProcessHandle:
    """Launch a validated process in an owned containment group.

    ``args`` contains only arguments following the executable. No quoting or
    shell interpretation is applied. ``None`` standard input is converted to a
    null device so a child cannot wait on the parent application's terminal.
    Standard output and standard error must be distinct binary capture streams.
    """

    if stdout is stderr:
        raise ValueError("stdout and stderr capture streams must be distinct")

    command = (os.fspath(executable), *args)
    child_environment = dict(env)
    stdin_target = subprocess.DEVNULL if stdin is None else stdin

    if os.name == "nt":
        return _launch_windows(
            command=command,
            cwd=cwd,
            env=child_environment,
            stdin=stdin_target,
            stdout=stdout,
            stderr=stderr,
        )

    if os.name == "posix":
        return _launch_posix(
            command=command,
            cwd=cwd,
            env=child_environment,
            stdin=stdin_target,
            stdout=stdout,
            stderr=stderr,
        )

    raise RuntimeError(f"Unsupported process-launch platform: {os.name!r}")


def _launch_windows(
    *,
    command: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    stdin: BinaryIO | int,
    stdout: BinaryIO,
    stderr: BinaryIO,
) -> ProcessHandle:
    if _WINDOWS_NEW_PROCESS_GROUP == 0:
        raise RuntimeError("Windows process-group creation is unavailable")

    # ``CREATE_NEW_PROCESS_GROUP`` preserves Wordbench's owned-process
    # cancellation semantics. ``CREATE_NO_WINDOW`` suppresses transient
    # console windows for GF and diagnostic child processes when Wordbench is
    # running as a desktop GUI.  The latter is optional only for interpreter
    # compatibility; supported Windows Python builds expose it.
    creation_flags = _WINDOWS_NEW_PROCESS_GROUP | _WINDOWS_NO_WINDOW

    return subprocess.Popen(
        command,
        cwd=os.fspath(cwd),
        env=env,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        shell=False,
        close_fds=True,
        bufsize=0,
        text=False,
        creationflags=creation_flags,
    )


def _launch_posix(
    *,
    command: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    stdin: BinaryIO | int,
    stdout: BinaryIO,
    stderr: BinaryIO,
) -> ProcessHandle:
    return subprocess.Popen(
        command,
        cwd=os.fspath(cwd),
        env=env,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        shell=False,
        close_fds=True,
        bufsize=0,
        text=False,
        restore_signals=True,
        start_new_session=True,
    )


__all__ = ("ProcessHandle", "StandardInput", "launch_without_shell")
