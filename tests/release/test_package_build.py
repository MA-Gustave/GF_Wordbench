"""Release verification for source and wheel package construction."""

from __future__ import annotations

import configparser
import csv
from email.parser import Parser
import importlib.util
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
from typing import Final
import zipfile

import pytest

from gf_wordbench.version import __version__

pytestmark = pytest.mark.slow

_BUILD_TIMEOUT_SEC: Final[float] = 240.0
_DISTRIBUTION_NAME: Final[str] = "gf-wordbench"
_IMPORT_PACKAGE: Final[str] = "gf_wordbench"
_REQUIRED_PYTHON: Final[str] = ">=3.11,<3.15"
_CONSOLE_ENTRY_POINT: Final[str] = "gf_wordbench.entrypoints.cli.main:main"
_GUI_ENTRY_POINT: Final[str] = "gf_wordbench.entrypoints.gui.main:main"
_COPY_EXCLUSIONS: Final[frozenset[str]] = frozenset(
    {
        ".coverage",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "htmlcov",
    }
)
_PROHIBITED_PARTS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "htmlcov",
    }
)


class _CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def _repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        pyproject = candidate / "pyproject.toml"
        package = candidate / "src" / _IMPORT_PACKAGE
        if pyproject.is_file() and package.is_dir():
            return candidate
    raise AssertionError("Could not locate the GF Wordbench repository root")


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored = {
        name
        for name in names
        if name in _COPY_EXCLUSIONS
        or name.startswith("run_")
        or name.endswith(".egg-info")
        or name.endswith((".pyc", ".pyo"))
    }
    if Path(directory).name == "_gf_wordbench_backups":
        ignored.update(names)
    return ignored


def _clean_build_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in (
        "PYTHONHOME",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "GF_EXE",
        "GF_EXECUTABLE",
        "GF_RGL",
        "GF_RGL_ROOT",
        "GF_WORDBENCH_GF_EXECUTABLE",
        "GF_WORDBENCH_OUTPUT_ROOT",
        "GF_WORDBENCH_PROJECT",
        "GF_WORDBENCH_RGL_ROOT",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "NO_COLOR": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "SOURCE_DATE_EPOCH": "1704067200",
        }
    )
    return environment


def _build_candidate(source_root: Path, tmp_path: Path) -> Path:
    if importlib.util.find_spec("build") is None:
        raise AssertionError(
            "The release package test requires the declared dev dependency 'build'"
        )
    if importlib.util.find_spec("hatchling") is None:
        raise AssertionError(
            "The release package test requires the declared build backend 'hatchling'"
        )

    candidate = tmp_path / "candidate"
    shutil.copytree(
        source_root,
        candidate,
        ignore=_copy_ignore,
        symlinks=False,
    )
    output_directory = tmp_path / "distributions"
    output_directory.mkdir()

    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--sdist",
            "--wheel",
            "--outdir",
            str(output_directory),
        ),
        cwd=candidate,
        env=_clean_build_environment(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_BUILD_TIMEOUT_SEC,
        check=False,
    )

    assert completed.returncode == 0, (
        "Package construction failed.\n"
        f"command: {sys.executable} -m build --no-isolation --sdist --wheel\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    return output_directory


def _single_artifact(directory: Path, pattern: str) -> Path:
    artifacts = sorted(directory.glob(pattern))
    assert len(artifacts) == 1, (
        f"Expected exactly one artifact matching {pattern!r}; "
        f"found {[path.name for path in artifacts]}"
    )
    artifact = artifacts[0]
    assert artifact.is_file()
    assert artifact.stat().st_size > 0
    return artifact


def _assert_safe_archive_names(names: tuple[str, ...]) -> None:
    assert names
    assert len(names) == len(set(names))
    for name in names:
        assert "\\" not in name
        path = PurePosixPath(name)
        assert not path.is_absolute()
        assert ".." not in path.parts
        assert all(part not in _PROHIBITED_PARTS for part in path.parts)
        assert not any(part.startswith("run_") for part in path.parts)
        assert not name.endswith((".pyc", ".pyo"))
        assert ".gf_wordbench_state.json" not in path.parts


def _dist_info_directory(names: tuple[str, ...]) -> str:
    candidates = {
        path.parts[0]
        for name in names
        if (path := PurePosixPath(name)).parts and path.parts[0].endswith(".dist-info")
    }
    assert len(candidates) == 1
    return candidates.pop()


def _wheel_text(
    archive: zipfile.ZipFile,
    member: str,
) -> str:
    return archive.read(member).decode("utf-8", errors="strict")


def _source_python_members(source_root: Path) -> set[str]:
    package_root = source_root / "src" / _IMPORT_PACKAGE
    return {
        path.relative_to(source_root / "src").as_posix()
        for path in package_root.rglob("*.py")
        if "__pycache__" not in path.parts
    }


def _assert_wheel(
    source_root: Path,
    wheel_path: Path,
) -> None:
    assert wheel_path.name.startswith(f"{_IMPORT_PACKAGE}-{__version__}-")
    assert wheel_path.suffix == ".whl"

    with zipfile.ZipFile(wheel_path) as archive:
        names = tuple(archive.namelist())
        _assert_safe_archive_names(names)

        members = set(names)
        package_prefix = f"{_IMPORT_PACKAGE}/"
        packaged_python = {
            name for name in names if name.startswith(package_prefix) and name.endswith(".py")
        }
        assert packaged_python == _source_python_members(source_root)
        assert f"{_IMPORT_PACKAGE}/py.typed" in members

        assert not any(
            name.startswith(("docs/", "project/", "scripts/", "templates/", "tests/"))
            for name in names
        )

        dist_info = _dist_info_directory(names)
        required_metadata = {
            f"{dist_info}/METADATA",
            f"{dist_info}/WHEEL",
            f"{dist_info}/RECORD",
            f"{dist_info}/entry_points.txt",
        }
        assert required_metadata <= members
        assert any(
            name.startswith(f"{dist_info}/licenses/") and name.endswith("/LICENSE.md")
            for name in names
        )

        metadata = Parser().parsestr(_wheel_text(archive, f"{dist_info}/METADATA"))
        assert metadata["Name"] == _DISTRIBUTION_NAME
        assert metadata["Version"] == __version__
        assert metadata["Requires-Python"] == _REQUIRED_PYTHON
        assert metadata["License-Expression"] == "LicenseRef-Proprietary"
        assert "Private :: Do Not Upload" in metadata.get_all(
            "Classifier",
            [],
        )
        assert any(
            requirement.startswith("PySide6")
            for requirement in metadata.get_all("Requires-Dist", [])
        )

        entry_points = _CaseSensitiveConfigParser(
            interpolation=None,
        )
        entry_points.read_string(_wheel_text(archive, f"{dist_info}/entry_points.txt"))
        assert entry_points["console_scripts"]["gf-wordbench"] == _CONSOLE_ENTRY_POINT
        assert entry_points["gui_scripts"]["gf-wordbench-gui"] == _GUI_ENTRY_POINT

        wheel_metadata = Parser().parsestr(_wheel_text(archive, f"{dist_info}/WHEEL"))
        assert wheel_metadata["Wheel-Version"] == "1.0"
        assert wheel_metadata["Root-Is-Purelib"].lower() == "true"

        record_rows = tuple(csv.reader(io.StringIO(_wheel_text(archive, f"{dist_info}/RECORD"))))
        recorded_names = {row[0] for row in record_rows}
        assert recorded_names == members
        assert all(len(row) == 3 for row in record_rows)


def _strip_sdist_root(names: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    roots = {path.parts[0] for name in names if (path := PurePosixPath(name)).parts}
    assert len(roots) == 1
    root = roots.pop()
    relative = tuple(
        PurePosixPath(name).relative_to(root).as_posix()
        for name in names
        if PurePosixPath(name).parts != (root,)
    )
    return root, relative


def _assert_sdist(
    source_root: Path,
    sdist_path: Path,
) -> None:
    assert sdist_path.name == f"{_IMPORT_PACKAGE}-{__version__}.tar.gz"

    with tarfile.open(sdist_path, mode="r:gz") as archive:
        regular_members = tuple(member.name for member in archive.getmembers() if member.isfile())
        _assert_safe_archive_names(regular_members)
        root, relative_names = _strip_sdist_root(regular_members)

        assert root == f"{_IMPORT_PACKAGE}-{__version__}"
        relative = set(relative_names)
        required = {
            "LICENSE.md",
            "README.md",
            "pyproject.toml",
            f"src/{_IMPORT_PACKAGE}/__init__.py",
            f"src/{_IMPORT_PACKAGE}/py.typed",
            f"src/{_IMPORT_PACKAGE}/version.py",
            "docs/release/RELEASE_PROCESS.md",
            "templates/project/project.toml",
            "tests/release/test_package_build.py",
        }
        assert required <= relative

        expected_python = {
            path.relative_to(source_root).as_posix()
            for path in (source_root / "src" / _IMPORT_PACKAGE).rglob("*.py")
        }
        packaged_python = {
            name
            for name in relative
            if name.startswith(f"src/{_IMPORT_PACKAGE}/") and name.endswith(".py")
        }
        assert packaged_python == expected_python

        prohibited_names = (
            ".coverage",
            ".gf_wordbench_state.json",
        )
        assert not any(PurePosixPath(name).name in prohibited_names for name in relative)
        assert not any(
            PurePosixPath(name).name.startswith(("Index(", "Pasted text(", "Pasted markdown("))
            for name in relative
        )
        assert not any(
            PurePosixPath(name).name.startswith("GF_Wordbench_")
            and PurePosixPath(name).suffix == ".txt"
            for name in relative
        )


def test_package_build_produces_inspectable_wheel_and_sdist(
    tmp_path: Path,
) -> None:
    source_root = _repository_root()
    output_directory = _build_candidate(source_root, tmp_path)

    wheel = _single_artifact(
        output_directory,
        f"{_IMPORT_PACKAGE}-{__version__}-*.whl",
    )
    sdist = _single_artifact(
        output_directory,
        f"{_IMPORT_PACKAGE}-{__version__}.tar.gz",
    )

    _assert_wheel(source_root, wheel)
    _assert_sdist(source_root, sdist)
