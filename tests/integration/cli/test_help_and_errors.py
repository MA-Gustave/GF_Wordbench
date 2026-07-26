from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Final

import pytest

pytestmark = pytest.mark.integration

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
_SOURCE_ROOT: Final[Path] = _REPOSITORY_ROOT / "src"
_CLI_MODULE: Final[str] = "gf_wordbench"

_COMMAND_HELP_CASES: Final[tuple[tuple[str, ...], ...]] = (
    ("validate", "--help"),
    ("project", "check", "--help"),
    ("scenarios", "check", "--help"),
    ("gold", "update", "--help"),
    ("schemas", "check", "--help"),
    ("reports", "check", "--help"),
)

_TOP_LEVEL_COMMANDS: Final[tuple[str, ...]] = (
    "validate",
    "project",
    "scenarios",
    "gold",
    "schemas",
    "reports",
)


def _cli_environment() -> dict[str, str]:
    environment = os.environ.copy()
    current_pythonpath = environment.get("PYTHONPATH")
    entries = [str(_SOURCE_ROOT)]
    if current_pythonpath:
        entries.append(current_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    environment.pop("NO_COLOR", None)
    return environment


def _run_cli(
    *arguments: str,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", _CLI_MODULE, *arguments],
        cwd=cwd,
        env=_cli_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=20,
        check=False,
    )


def _assert_help_result(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
    assert result.stderr == ""
    assert "usage:" in result.stdout.lower()
    assert "gf-wordbench" in result.stdout.lower()


def test_global_help_is_read_only_and_lists_the_canonical_commands(
    tmp_path: Path,
) -> None:
    before = tuple(tmp_path.iterdir())

    result = _run_cli("--help", cwd=tmp_path)

    _assert_help_result(result)
    for command in _TOP_LEVEL_COMMANDS:
        assert command in result.stdout
    assert tuple(tmp_path.iterdir()) == before


@pytest.mark.parametrize("arguments", _COMMAND_HELP_CASES)
def test_each_canonical_command_help_succeeds_without_side_effects(
    arguments: tuple[str, ...],
    tmp_path: Path,
) -> None:
    before = tuple(tmp_path.iterdir())

    result = _run_cli(*arguments, cwd=tmp_path)

    _assert_help_result(result)
    assert tuple(tmp_path.iterdir()) == before


@pytest.mark.parametrize(
    "arguments",
    (
        ("unknown-command",),
        ("validate", "--unknown-option"),
        ("project",),
        ("project", "unknown-command"),
    ),
)
def test_invalid_invocations_use_stderr_and_exit_two(
    arguments: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result = _run_cli(*arguments, cwd=tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip()
    assert "ERROR:" in result.stderr
    assert "usage:" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


def test_missing_command_is_reported_as_a_usage_error(tmp_path: Path) -> None:
    result = _run_cli(cwd=tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("ERROR:")
    assert "usage:" in result.stderr.lower()
    assert "command" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


def test_help_takes_precedence_over_project_loading(tmp_path: Path) -> None:
    invalid_project = tmp_path / "project"
    invalid_project.mkdir()
    (invalid_project / "project.toml").write_text(
        "this is not valid TOML = [",
        encoding="utf-8",
    )

    result = _run_cli("--help", cwd=tmp_path)

    _assert_help_result(result)
    assert "project configuration" not in result.stderr.lower()


def test_command_help_takes_precedence_over_required_arguments(
    tmp_path: Path,
) -> None:
    result = _run_cli("gold", "update", "--help", cwd=tmp_path)

    _assert_help_result(result)
    assert "required" not in result.stderr.lower()
