"""Launch the existing practical multilingual Tk UI from the Qt desktop shell.

This adapter is presentation-only. Practical campaign rules live in
``gf_wordbench.practical.batch`` and the existing .pyw entrypoint.
"""
from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys


def wordbench_root() -> Path:
    return Path(__file__).resolve().parents[4]


def qualifier_script(root: Path | None = None) -> Path:
    repository = (root or wordbench_root()).resolve()
    script = repository / "Qualification_Langues_Utiles.pyw"
    if not script.is_file() or not (repository / "src/gf_wordbench/practical/batch.py").is_file():
        raise FileNotFoundError(
            "Practical qualification tool not installed in the GF WordBench repository: "
            + str(script)
        )
    return script


def python_for_qualifier(
    root: Path | None = None, *, running_python: str | None = None
) -> str:
    """Choose a real Python interpreter, never an entrypoint .exe as Python."""
    repository = (root or wordbench_root()).resolve()
    current = Path(running_python or sys.executable)
    names = ("pythonw.exe", "python.exe") if os.name == "nt" else ("python3", "python")
    if current.name.lower() in names and current.is_file():
        # A python.exe starting Qt can use an adjacent pythonw.exe to avoid CMD.
        if os.name == "nt" and current.name.lower() == "python.exe":
            hidden = current.with_name("pythonw.exe")
            if hidden.is_file():
                return str(hidden)
        return str(current)
    if os.name == "nt":
        candidates = (
            current.with_name("pythonw.exe"),
            current.with_name("python.exe"),
            repository / ".venv/Scripts/pythonw.exe",
            repository / ".venv/Scripts/python.exe",
        )
    else:
        candidates = (repository / ".venv/bin/python3", repository / ".venv/bin/python")
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    for executable in names:
        resolved = shutil.which(executable)
        if resolved:
            return str(Path(resolved).resolve())
    raise FileNotFoundError(
        "Python 3.11+ was not found. Configure the GF WordBench virtual environment."
    )


def launch_qualification(root: Path | None = None) -> int:
    """Start the separate candidate-only UI; never block the Qt event loop."""
    repository = (root or wordbench_root()).resolve()
    script = qualifier_script(repository)
    interpreter = python_for_qualifier(repository)
    from PySide6.QtCore import QProcess

    started, pid = QProcess.startDetached(
        interpreter, [str(script)], str(repository)
    )
    if not started:
        raise OSError("Could not start the practical qualification window")
    return pid
