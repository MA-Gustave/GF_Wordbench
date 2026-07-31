from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from typing import Final

import pytest

pytestmark = pytest.mark.contract

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_CLI_LAUNCHER: Final[Path] = _REPOSITORY_ROOT / "launch_cli.bat"
_GUI_LAUNCHER: Final[Path] = _REPOSITORY_ROOT / "launch_gui.bat"
_PYPROJECT: Final[Path] = _REPOSITORY_ROOT / "pyproject.toml"

_DRIVE_PATH_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)(?<![%~])[a-z]:[\\/]"
)
_UNC_PATH_RE: Final[re.Pattern[str]] = re.compile(r"(?m)(?<!%)\\\\[^\\\r\n]+\\")
_DIRECT_GF_RE: Final[re.Pattern[str]] = re.compile(
    r"(?ix)(?:^|[\s\"'])gf(?:\.exe)?(?:[\s\"']|$)"
)
_TEMP_FILE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?ix)(?:%temp%|%tmp%|\\temp\\|mktemp|temporary)"
)
_EXIT_LITERAL_RE: Final[re.Pattern[str]] = re.compile(
    r"(?im)^\s*exit\s+/b\s+(-?\d+)\s*$"
)


@dataclass(frozen=True, slots=True)
class LauncherContract:
    path: Path
    executable_name: str
    console_script: str
    module_fallbacks: tuple[str, ...]


_LAUNCHERS: Final[tuple[LauncherContract, ...]] = (
    LauncherContract(
        path=_CLI_LAUNCHER,
        executable_name="gf-wordbench.exe",
        console_script="gf-wordbench",
        module_fallbacks=("gf_wordbench", "gf_wordbench.entrypoints.cli.main"),
    ),
    LauncherContract(
        path=_GUI_LAUNCHER,
        executable_name="gf-wordbench-gui.exe",
        console_script="gf-wordbench-gui",
        module_fallbacks=("gf_wordbench.entrypoints.gui.main",),
    ),
)


def _read_launcher(path: Path) -> str:
    raw = path.read_bytes()
    assert b"\x00" not in raw, f"{path.name} must be a text batch file"
    assert not raw.startswith((b"\xff\xfe", b"\xfe\xff")), (
        f"{path.name} must not use UTF-16 because cmd.exe parsing becomes ambiguous"
    )
    return raw.decode("utf-8-sig")


def _normalized(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _active_lines(text: str) -> tuple[str, ...]:
    active: list[str] = []
    for raw_line in _normalized(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.casefold()
        if lowered.startswith(("rem ", "::")):
            continue
        active.append(line)
    return tuple(active)


def _without_echo_commands(text: str) -> str:
    lines = []
    for line in _normalized(text).splitlines():
        stripped = line.lstrip(" @")
        if stripped.casefold().startswith("echo "):
            continue
        lines.append(line)
    return "\n".join(lines)


def _has_repository_anchor(text: str) -> bool:
    lowered = text.casefold()
    return "%~dp0" in lowered or "%~dpnx0" in lowered


def _has_argument_forwarding(text: str) -> bool:
    return bool(re.search(r"(?<!%)%\*(?!%)", text))


def _has_exit_code_propagation(text: str) -> bool:
    lowered = text.casefold()
    direct = bool(
        re.search(r"(?im)^\s*exit\s+/b\s+%errorlevel%\s*$", lowered)
    )
    captured = bool(
        re.search(
            r'(?im)^\s*set\s+"?([a-z_][a-z0-9_]*)\s*=\s*%errorlevel%"?\s*$',
            lowered,
        )
    )
    if direct:
        return True
    if not captured:
        return False
    variable_names = {
        match.group(1)
        for match in re.finditer(
            r'(?im)^\s*set\s+"?([a-z_][a-z0-9_]*)\s*=\s*%errorlevel%"?\s*$',
            lowered,
        )
    }
    return any(
        re.search(
            rf"(?im)^\s*exit\s+/b\s+%{re.escape(name)}%\s*$",
            lowered,
        )
        for name in variable_names
    )


def _has_actionable_missing_environment_branch(text: str) -> bool:
    lowered = text.casefold()
    detects_missing = bool(
        re.search(r"(?im)^\s*if\s+not\s+exist\s+", lowered)
        or re.search(r"(?im)^\s*where(?:\.exe)?\s+", lowered)
        or re.search(r"(?im)^\s*if\s+errorlevel\s+1\b", lowered)
    )
    reports_error = bool(
        re.search(r"(?im)^\s*(?:1?>&2|>&2)\s*echo\s+\S", lowered)
        or re.search(r"(?im)^\s*echo\s+\S.*(?:error|missing|not found|unavailable)", lowered)
    )
    nonzero_literals = {
        int(value)
        for value in _EXIT_LITERAL_RE.findall(lowered)
        if int(value) != 0
    }
    exits_nonzero = bool(nonzero_literals) or bool(
        re.search(r"(?im)^\s*exit\s+/b\s+%[a-z_][a-z0-9_]*%\s*$", lowered)
    )
    return detects_missing and reports_error and exits_nonzero


def _invokes_documented_entrypoint(contract: LauncherContract, text: str) -> bool:
    lowered = text.casefold()
    installed = contract.executable_name.casefold() in lowered
    console_command = bool(
        re.search(
            rf"(?im)(?:^|[\s\"']){re.escape(contract.console_script.casefold())}"
            r"(?:\.exe)?(?:[\s\"']|$)",
            lowered,
        )
    )
    module = any(
        re.search(
            rf"(?im)(?:python(?:\.exe)?|py(?:\.exe)?)\s+(?:-[^\s]+\s+)*-m\s+"
            rf"{re.escape(module.casefold())}(?:[\s\"']|$)",
            lowered,
        )
        for module in contract.module_fallbacks
    )
    return installed or console_command or module


def _assert_no_hidden_policy(text: str, launcher_name: str) -> None:
    """Reject application policy embedded in a Windows wrapper.

    ADR-0015 makes language selection and path resolution application concerns.
    The batch launchers may forward caller arguments, but they must not invent,
    select, remember, validate, or rewrite language and run configuration.
    """

    non_echo_text = _without_echo_commands(text)
    prohibited_fragments = {
        "--language-path": "selected-language-path policy",
        "--language-dir": "language-directory policy",
        "--language-file": "focused-language-file policy",
        "--validation-profile": "validation-profile policy",
        "--project": "legacy project-startup policy",
        "--catalog": "legacy catalog-startup policy",
        "--mode": "validation mode",
        "--gf-exe": "GF executable override",
        "--rgl-root": "RGL override",
        "--out-root": "output-root override",
        "--strict": "strict-validation policy",
        "--no-compile": "compilation policy",
        "--scan-only": "scan policy",
        "project.toml": "project loading policy",
        "language.toml": "mandatory language-bundle policy",
        "rgl-language-catalog": "catalog-driven startup policy",
        ".gf_wordbench_state.json": "persistent state ownership",
    }
    lowered = non_echo_text.casefold()
    violations = [
        description
        for fragment, description in prohibited_fragments.items()
        if fragment in lowered
    ]
    assert violations == [], (
        f"{launcher_name} duplicates application policy: {', '.join(violations)}"
    )


def test_windows_launchers_are_fixed_repository_files() -> None:
    for contract in _LAUNCHERS:
        assert contract.path.is_file(), f"Missing canonical launcher: {contract.path.name}"
        assert contract.path.parent == _REPOSITORY_ROOT
        assert contract.path.suffix.casefold() == ".bat"


def test_launcher_console_scripts_match_package_metadata() -> None:
    metadata = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["scripts"]["gf-wordbench"] == (
        "gf_wordbench.entrypoints.cli.main:main"
    )
    assert project["gui-scripts"]["gf-wordbench-gui"] == (
        "gf_wordbench.entrypoints.gui.main:main"
    )


def test_gui_launcher_defers_language_selection_to_the_application() -> None:
    """The Windows wrapper must not bypass the ADR-0015 startup surface."""

    text = _read_launcher(_GUI_LAUNCHER)
    non_echo_text = _without_echo_commands(text).casefold()

    prohibited_language_literals = {
        "src/english": "hard-coded English source directory",
        r"src\english": "hard-coded English source directory",
        "langeng.gf": "hard-coded English entrypoint",
        "grammareng.gf": "hard-coded English entrypoint",
        "alleng.gf": "hard-coded English entrypoint",
    }
    violations = [
        description
        for fragment, description in prohibited_language_literals.items()
        if fragment in non_echo_text
    ]

    assert violations == [], (
        "launch_gui.bat embeds a language-specific startup default: "
        f"{', '.join(violations)}"
    )
    assert _has_argument_forwarding(text), (
        "launch_gui.bat must forward explicit caller intent unchanged; the GUI "
        "application remains responsible for presenting and resolving language "
        "selection"
    )


@pytest.mark.parametrize("contract", _LAUNCHERS, ids=lambda item: item.path.name)
def test_launcher_has_a_minimal_safe_batch_preamble(
    contract: LauncherContract,
) -> None:
    text = _read_launcher(contract.path)
    active = _active_lines(text)

    assert active, f"{contract.path.name} is empty"
    assert active[0].casefold() == "@echo off"
    assert any(line.casefold().startswith("setlocal") for line in active[:5])
    assert "enabledelayedexpansion" not in text.casefold(), (
        f"{contract.path.name} must not enable delayed expansion because user arguments "
        "may contain exclamation marks"
    )


@pytest.mark.parametrize("contract", _LAUNCHERS, ids=lambda item: item.path.name)
def test_launcher_resolves_and_quotes_its_own_repository_path(
    contract: LauncherContract,
) -> None:
    text = _read_launcher(contract.path)
    lowered = text.casefold()

    assert _has_repository_anchor(text), (
        f"{contract.path.name} must resolve paths from %~dp0, not the caller cwd"
    )
    assert re.search(r'"[^"\r\n]*%~dp0[^"\r\n]*"', lowered), (
        f"{contract.path.name} must quote paths derived from %~dp0"
    )
    assert not _DRIVE_PATH_RE.search(_without_echo_commands(text)), (
        f"{contract.path.name} embeds a machine-local drive path"
    )
    assert not _UNC_PATH_RE.search(_without_echo_commands(text)), (
        f"{contract.path.name} embeds a machine-local UNC path"
    )


@pytest.mark.parametrize("contract", _LAUNCHERS, ids=lambda item: item.path.name)
def test_launcher_invokes_only_its_documented_application_entrypoint(
    contract: LauncherContract,
) -> None:
    text = _read_launcher(contract.path)
    lowered = text.casefold()

    assert _invokes_documented_entrypoint(contract, text), (
        f"{contract.path.name} does not invoke {contract.console_script} or its documented "
        "Python module"
    )
    other = _LAUNCHERS[1] if contract is _LAUNCHERS[0] else _LAUNCHERS[0]
    assert other.executable_name.casefold() not in lowered
    assert not _DIRECT_GF_RE.search(_without_echo_commands(text)), (
        f"{contract.path.name} must not invoke gf.exe directly"
    )
    _assert_no_hidden_policy(text, contract.path.name)


@pytest.mark.parametrize("contract", _LAUNCHERS, ids=lambda item: item.path.name)
def test_launcher_forwards_arguments_and_preserves_child_exit_code(
    contract: LauncherContract,
) -> None:
    text = _read_launcher(contract.path)

    assert _has_argument_forwarding(text), (
        f"{contract.path.name} must forward the original argument vector with %*"
    )
    assert _has_exit_code_propagation(text), (
        f"{contract.path.name} must return the child process exit code"
    )
    assert not re.search(r"(?im)^\s*start(?:\s|$)", text), (
        f"{contract.path.name} must not use START because it detaches and loses the child "
        "exit code"
    )


@pytest.mark.parametrize("contract", _LAUNCHERS, ids=lambda item: item.path.name)
def test_launcher_reports_missing_environment_without_unsafe_temporary_files(
    contract: LauncherContract,
) -> None:
    text = _read_launcher(contract.path)

    assert _has_actionable_missing_environment_branch(text), (
        f"{contract.path.name} must detect a missing interpreter or installed entrypoint, "
        "print an actionable error, and fail non-zero"
    )
    assert not _TEMP_FILE_RE.search(_without_echo_commands(text)), (
        f"{contract.path.name} must not write user arguments to temporary shell files"
    )
    assert not re.search(r"(?im)^\s*setx(?:\.exe)?\s+", text)
    assert not re.search(r"(?im)^\s*(?:copy|move|del|erase|mkdir|md)\s+", text)


@pytest.mark.windows
def test_launchers_work_from_a_repository_path_with_spaces_and_preserve_exit_code(
    tmp_path: Path,
) -> None:
    if os.name != "nt":
        pytest.skip("cmd.exe launcher execution is Windows-specific")

    repository = tmp_path / "GF Wordbench repository with spaces"
    scripts_dir = repository / ".venv" / "Scripts"
    scripts_dir.mkdir(parents=True)

    for contract in _LAUNCHERS:
        launcher = repository / contract.path.name
        shutil.copy2(contract.path, launcher)
        shim = scripts_dir / contract.executable_name
        shutil.copy2(sys.executable, shim)

        completed = subprocess.run(
            [
                os.environ.get("COMSPEC", "cmd.exe"),
                "/d",
                "/s",
                "/c",
                f'"{launcher}" -c "import sys;sys.exit(37)"',
            ],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        assert completed.returncode == 37, (
            f"{contract.path.name} did not forward arguments or preserve exit code; "
            f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
        )


@pytest.mark.windows
def test_launchers_fail_actionably_when_the_local_environment_is_missing(
    tmp_path: Path,
) -> None:
    if os.name != "nt":
        pytest.skip("cmd.exe launcher execution is Windows-specific")

    repository = tmp_path / "GF Wordbench missing environment"
    repository.mkdir()

    for contract in _LAUNCHERS:
        launcher = repository / contract.path.name
        shutil.copy2(contract.path, launcher)
        completed = subprocess.run(
            [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", str(launcher)],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        output = f"{completed.stdout}\n{completed.stderr}".casefold()
        assert completed.returncode != 0
        assert any(
            word in output
            for word in ("error", "missing", "not found", "unavailable", "install", "venv")
        ), f"{contract.path.name} did not print an actionable error: {output!r}"
