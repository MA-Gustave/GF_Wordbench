"""Clean-wheel installation smoke tests for the GF Wordbench distribution."""

from __future__ import annotations

from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING, TypedDict
import venv

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_CLI_NAME = "gf-wordbench"
_GUI_NAME = "gf-wordbench-gui"
_EXPECTED_ENTRY_POINTS = {
    "console_scripts:gf-wordbench": "gf_wordbench.entrypoints.cli.main:main",
    "gui_scripts:gf-wordbench-gui": "gf_wordbench.entrypoints.gui.main:main",
}
_BUILD_TIMEOUT_SECONDS = 300
_INSTALL_TIMEOUT_SECONDS = 180
_COMMAND_TIMEOUT_SECONDS = 60


class _InstalledMetadata(TypedDict):
    distribution_version: str
    package_version: str
    package_file: str
    entry_points: dict[str, str]


def _repository_root() -> Path:
    """Return the checkout root that owns this test module."""
    for candidate in Path(__file__).resolve().parents:
        pyproject = candidate / "pyproject.toml"
        package = candidate / "src" / "gf_wordbench" / "__init__.py"
        if pyproject.is_file() and package.is_file():
            return candidate
    raise AssertionError("could not locate the GF Wordbench repository root")


def _clean_environment(home: Path) -> dict[str, str]:
    """Build a deterministic subprocess environment without import-path leakage."""
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.update(
        {
            "APPDATA": str(home / "appdata"),
            "HOME": str(home),
            "LOCALAPPDATA": str(home / "localappdata"),
            "NO_COLOR": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "USERPROFILE": str(home),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
        }
    )
    return environment


def _run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run a command and expose complete evidence when it fails."""
    result = subprocess.run(
        tuple(command),
        cwd=cwd,
        env=dict(environment),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        rendered = subprocess.list2cmdline(list(command))
        pytest.fail(
            f"command failed with exit code {result.returncode}: {rendered}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
    return result


def _build_wheel(
    repository_root: Path,
    output_directory: Path,
    environment: Mapping[str, str],
) -> Path:
    """Build exactly one wheel from the checkout under test."""
    output_directory.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "build",
        "--wheel",
        "--outdir",
        str(output_directory),
    ]
    if find_spec("hatchling") is not None:
        command.append("--no-isolation")

    _run_checked(
        command,
        cwd=repository_root,
        environment=environment,
        timeout=_BUILD_TIMEOUT_SECONDS,
    )

    wheels = tuple(sorted(output_directory.glob("gf_wordbench-*.whl")))
    assert len(wheels) == 1, (
        "wheel build must create exactly one gf_wordbench wheel; "
        f"observed: {[path.name for path in wheels]}"
    )
    return wheels[0]


def _venv_python(environment_root: Path) -> Path:
    if os.name == "nt":
        return environment_root / "Scripts" / "python.exe"
    return environment_root / "bin" / "python"


def _venv_script(environment_root: Path, name: str) -> Path:
    if os.name == "nt":
        return environment_root / "Scripts" / f"{name}.exe"
    return environment_root / "bin" / name


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _inspect_installed_distribution(
    python_executable: Path,
    *,
    cwd: Path,
    environment: Mapping[str, str],
) -> _InstalledMetadata:
    script = """
import json
from importlib.metadata import distribution
from pathlib import Path
import gf_wordbench

dist = distribution("gf-wordbench")
entry_points = {
    f"{entry.group}:{entry.name}": entry.value
    for entry in dist.entry_points
    if entry.group in {"console_scripts", "gui_scripts"}
}
print(json.dumps({
    "distribution_version": dist.version,
    "package_version": gf_wordbench.__version__,
    "package_file": str(Path(gf_wordbench.__file__).resolve()),
    "entry_points": entry_points,
}, sort_keys=True))
"""
    result = _run_checked(
        [str(python_executable), "-I", "-c", script],
        cwd=cwd,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    raw_payload = json.loads(result.stdout)
    assert isinstance(raw_payload, dict)

    distribution_version = raw_payload.get("distribution_version")
    package_version = raw_payload.get("package_version")
    package_file = raw_payload.get("package_file")
    raw_entry_points = raw_payload.get("entry_points")

    assert isinstance(distribution_version, str)
    assert distribution_version
    assert isinstance(package_version, str)
    assert isinstance(package_file, str)
    assert isinstance(raw_entry_points, dict)

    entry_points: dict[str, str] = {}
    for key, value in raw_entry_points.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
        entry_points[key] = value

    return {
        "distribution_version": distribution_version,
        "package_version": package_version,
        "package_file": package_file,
        "entry_points": entry_points,
    }


@pytest.mark.slow
def test_wheel_installs_and_exposes_supported_entrypoints(tmp_path: Path) -> None:
    """A wheel must work outside the checkout through installed entrypoints."""
    repository_root = _repository_root()
    clean_home = tmp_path / "home"
    clean_home.mkdir()
    environment = _clean_environment(clean_home)

    wheel = _build_wheel(repository_root, tmp_path / "dist", environment)

    environment_root = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(environment_root)
    python_executable = _venv_python(environment_root)
    assert python_executable.is_file()

    _run_checked(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-index",
            str(wheel),
        ],
        cwd=tmp_path,
        environment=environment,
        timeout=_INSTALL_TIMEOUT_SECONDS,
    )

    metadata = _inspect_installed_distribution(
        python_executable,
        cwd=tmp_path,
        environment=environment,
    )
    distribution_version = metadata["distribution_version"]
    package_version = metadata["package_version"]
    package_file = Path(metadata["package_file"])
    entry_points = metadata["entry_points"]

    assert distribution_version
    assert package_version == distribution_version
    assert _is_within(package_file, environment_root)
    assert not _is_within(package_file, repository_root)
    for key, expected_value in _EXPECTED_ENTRY_POINTS.items():
        assert entry_points.get(key) == expected_value

    cli = _venv_script(environment_root, _CLI_NAME)
    gui = _venv_script(environment_root, _GUI_NAME)
    assert cli.is_file(), "the installed wheel must provide the gf-wordbench command"
    assert gui.is_file(), "the installed wheel must provide the gf-wordbench-gui command"

    version_result = _run_checked(
        [str(cli), "--version"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    assert version_result.stdout.strip() == f"GF Wordbench {distribution_version}"

    help_result = _run_checked(
        [str(cli), "--help"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    help_text = help_result.stdout
    assert "usage:" in help_text.casefold()
    for command_name in (
        "validate",
        "project",
        "scenarios",
        "gold",
        "schemas",
        "reports",
    ):
        assert command_name in help_text

    command_help = _run_checked(
        [str(cli), "project", "check", "--help"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    assert "usage:" in command_help.stdout.casefold()
