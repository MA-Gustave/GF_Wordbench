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
    startup_runtime_builder: bool
    gui_main_callable: bool
    qt_eagerly_imported: bool


class _InstalledCliContract(TypedDict):
    probe_command: str
    probe_language_path: str
    probe_profile: str
    validate_command: str
    validate_language_path: str
    validate_profile: str
    validate_target: str


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
    """Inspect installed metadata and the lazy GUI startup composition boundary."""
    script = """
import importlib
import json
from importlib.metadata import distribution
from pathlib import Path
import sys

import gf_wordbench

bootstrap = importlib.import_module("gf_wordbench.bootstrap")
gui_main = importlib.import_module("gf_wordbench.entrypoints.gui.main")
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
    "startup_runtime_builder": callable(
        getattr(bootstrap, "build_startup_gui_runtime", None)
    ),
    "gui_main_callable": callable(getattr(gui_main, "main", None)),
    "qt_eagerly_imported": any(
        name == "PySide6" or name.startswith("PySide6.")
        for name in sys.modules
    ),
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
    startup_runtime_builder = raw_payload.get("startup_runtime_builder")
    gui_main_callable = raw_payload.get("gui_main_callable")
    qt_eagerly_imported = raw_payload.get("qt_eagerly_imported")

    assert isinstance(distribution_version, str)
    assert distribution_version
    assert isinstance(package_version, str)
    assert isinstance(package_file, str)
    assert isinstance(raw_entry_points, dict)
    assert type(startup_runtime_builder) is bool
    assert type(gui_main_callable) is bool
    assert type(qt_eagerly_imported) is bool

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
        "startup_runtime_builder": startup_runtime_builder,
        "gui_main_callable": gui_main_callable,
        "qt_eagerly_imported": qt_eagerly_imported,
    }


def _inspect_installed_cli_contract(
    python_executable: Path,
    *,
    cwd: Path,
    environment: Mapping[str, str],
    language_path: Path,
    validation_profile: Path,
) -> _InstalledCliContract:
    """Parse canonical ADR-0015 requests from the installed wheel."""
    script = """
import json
import os
from pathlib import Path
import sys

from gf_wordbench.entrypoints.cli.parser import parse_cli_request

language_path = Path(sys.argv[1])
validation_profile = Path(sys.argv[2])
probe = parse_cli_request([
    "language",
    "probe",
    os.fspath(language_path),
    "--profile",
    os.fspath(validation_profile),
])
validate = parse_cli_request([
    "validate",
    "--language-path",
    os.fspath(language_path),
    "--profile",
    os.fspath(validation_profile),
    "--mode",
    "quick",
])
print(json.dumps({
    "probe_command": probe.command.value,
    "probe_language_path": os.fspath(probe.require("language_path")),
    "probe_profile": os.fspath(probe.require("validation_profile")),
    "validate_command": validate.command.value,
    "validate_language_path": os.fspath(validate.require("language_path")),
    "validate_profile": os.fspath(validate.require("validation_profile")),
    "validate_target": os.fspath(validate.require("target")),
}, sort_keys=True))
"""
    result = _run_checked(
        [
            str(python_executable),
            "-I",
            "-c",
            script,
            str(language_path),
            str(validation_profile),
        ],
        cwd=cwd,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    raw_payload = json.loads(result.stdout)
    assert isinstance(raw_payload, dict)

    expected_fields = (
        "probe_command",
        "probe_language_path",
        "probe_profile",
        "validate_command",
        "validate_language_path",
        "validate_profile",
        "validate_target",
    )
    payload: dict[str, str] = {}
    for field_name in expected_fields:
        value = raw_payload.get(field_name)
        assert isinstance(value, str)
        payload[field_name] = value
    return _InstalledCliContract(**payload)


@pytest.mark.slow
def test_wheel_installs_and_exposes_path_resolved_entrypoints(tmp_path: Path) -> None:
    """A wheel must expose the installed ADR-0015 startup and CLI contracts."""
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
    assert metadata["startup_runtime_builder"] is True
    assert metadata["gui_main_callable"] is True
    assert metadata["qt_eagerly_imported"] is False
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
        "language",
        "validate",
        "project",
        "scenarios",
        "gold",
        "schemas",
        "reports",
    ):
        assert command_name in help_text

    language_help = _run_checked(
        [str(cli), "language", "probe", "--help"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    assert "usage:" in language_help.casefold()
    assert "LANGUAGE-PATH" in language_help
    assert "--profile" in language_help
    assert "--gf-exe" in language_help
    assert "--rgl-root" in language_help
    assert "--project-root" not in language_help

    validate_help = _run_checked(
        [str(cli), "validate", "--help"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    assert "usage:" in validate_help.casefold()
    assert "--language-path" in validate_help
    assert "--last-language" in validate_help
    assert "--profile" in validate_help
    assert "--project-root" not in validate_help

    project_help = _run_checked(
        [str(cli), "project", "check", "--help"],
        cwd=tmp_path,
        environment=environment,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    assert "usage:" in project_help.casefold()
    assert "--language-path" in project_help
    assert "--profile" in project_help
    assert "--project-root" not in project_help

    language_path = tmp_path / "gf-rgl" / "src" / "english" / "LangEng.gf"
    validation_profile = tmp_path / "profiles" / "english-release.toml"
    cli_contract = _inspect_installed_cli_contract(
        python_executable,
        cwd=tmp_path,
        environment=environment,
        language_path=language_path,
        validation_profile=validation_profile,
    )
    assert cli_contract == {
        "probe_command": "language.probe",
        "probe_language_path": str(language_path),
        "probe_profile": str(validation_profile),
        "validate_command": "validate",
        "validate_language_path": str(language_path),
        "validate_profile": str(validation_profile),
        "validate_target": str(language_path),
    }
