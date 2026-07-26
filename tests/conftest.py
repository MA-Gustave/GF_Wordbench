"""Shared pytest configuration for the GF Wordbench verification suite."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
import os
from pathlib import Path
import shutil
from typing import Final

import pytest

from tests.helpers.fixture_paths import FixturePaths, discover_repository_root

_GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_TEST_GF_EXE"
_RGL_ROOT_ENV: Final[str] = "GF_WORDBENCH_TEST_RGL_ROOT"
_TEST_HARNESS_PREFIX: Final[str] = "GF_WORDBENCH_TEST_"
_RUNTIME_ENVIRONMENT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "GF_LIB_PATH",
        "GF_WORDBENCH_GF_EXE",
        "GF_WORDBENCH_OUTPUT_ROOT",
        "GF_WORDBENCH_PROJECT_ROOT",
        "GF_WORDBENCH_RGL_ROOT",
        "GF_WORDBENCH_STATE_PATH",
    }
)
_FIXED_UTC_NOW: Final[datetime] = datetime(2026, 7, 25, 12, tzinfo=UTC)

Clock = Callable[[], datetime]


def _configured_environment_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _resolve_executable(value: str, *, variable: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        discovered = shutil.which(value)
        if discovered is None:
            pytest.fail(
                f"{variable}={value!r} does not resolve to an executable",
                pytrace=False,
            )
        candidate = Path(discovered)

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(
            f"{variable} cannot be resolved: {candidate}: {exc}",
            pytrace=False,
        )

    if not resolved.is_file():
        pytest.fail(
            f"{variable} must identify a regular executable file: {resolved}",
            pytrace=False,
        )
    if os.name != "nt" and not os.access(resolved, os.X_OK):
        pytest.fail(
            f"{variable} is not executable: {resolved}",
            pytrace=False,
        )
    return resolved


def _resolve_directory(value: str, *, variable: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        pytest.fail(
            f"{variable} must be an absolute path: {candidate}",
            pytrace=False,
        )

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(
            f"{variable} cannot be resolved: {candidate}: {exc}",
            pytrace=False,
        )

    if not resolved.is_dir():
        pytest.fail(
            f"{variable} must identify an existing directory: {resolved}",
            pytrace=False,
        )
    return resolved


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    windows_only = pytest.mark.skip(reason="Windows-specific test")
    posix_only = pytest.mark.skip(reason="POSIX-specific test")

    for item in items:
        if "windows" in item.keywords and os.name != "nt":
            item.add_marker(windows_only)
        if "posix" in item.keywords and os.name == "nt":
            item.add_marker(posix_only)


def pytest_report_header() -> list[str]:
    gf_executable = _configured_environment_value(_GF_EXECUTABLE_ENV)
    rgl_root = _configured_environment_value(_RGL_ROOT_ENV)
    return [
        f"GF test executable: {gf_executable or '<not configured>'}",
        f"GF test RGL root: {rgl_root or '<not configured>'}",
    ]


@pytest.fixture(scope="session")
def repository_root() -> Path:
    root = discover_repository_root(Path(__file__))
    if not (root / "pyproject.toml").is_file():
        pytest.fail(f"repository root is missing pyproject.toml: {root}", pytrace=False)
    if not (root / "src" / "gf_wordbench").is_dir():
        pytest.fail(f"repository root is missing src/gf_wordbench: {root}", pytrace=False)
    return root


@pytest.fixture(scope="session")
def tests_root(repository_root: Path) -> Path:
    root = repository_root / "tests"
    if not root.is_dir():
        pytest.fail(f"canonical tests directory is missing: {root}", pytrace=False)
    return root


@pytest.fixture(scope="session")
def fixture_paths(repository_root: Path) -> FixturePaths:
    return FixturePaths.from_repository_root(repository_root)


@pytest.fixture(scope="session")
def fixtures_root(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.root


@pytest.fixture(scope="session")
def project_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.projects


@pytest.fixture(scope="session")
def gf_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.gf


@pytest.fixture(scope="session")
def diagnostic_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.diagnostics


@pytest.fixture(scope="session")
def schema_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.schemas


@pytest.fixture(scope="session")
def report_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.reports


@pytest.fixture(scope="session")
def scenario_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.scenarios


@pytest.fixture(scope="session")
def legacy_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.legacy


@pytest.fixture(scope="session")
def executable_fixtures(fixture_paths: FixturePaths) -> Path:
    return fixture_paths.executables


@pytest.fixture(scope="session")
def fixed_utc_now() -> datetime:
    return _FIXED_UTC_NOW


@pytest.fixture(scope="session")
def deterministic_clock(fixed_utc_now: datetime) -> Clock:
    return lambda: fixed_utc_now


@pytest.fixture(autouse=True)
def clean_test_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in tuple(os.environ):
        normalized = name.upper()
        if normalized in _RUNTIME_ENVIRONMENT_NAMES:
            monkeypatch.delenv(name, raising=False)
            continue
        if normalized.startswith("GF_WORDBENCH_") and not normalized.startswith(
            _TEST_HARNESS_PREFIX
        ):
            monkeypatch.delenv(name, raising=False)
    yield


@pytest.fixture
def isolated_test_environment(clean_test_environment: None) -> None:
    return clean_test_environment


@pytest.fixture(scope="session")
def real_gf_executable() -> Path:
    configured = _configured_environment_value(_GF_EXECUTABLE_ENV)
    if configured is None:
        pytest.skip(
            f"real-GF test requires {_GF_EXECUTABLE_ENV} to be configured"
        )
    return _resolve_executable(configured, variable=_GF_EXECUTABLE_ENV)


@pytest.fixture(scope="session")
def real_gf_rgl_root() -> Path:
    configured = _configured_environment_value(_RGL_ROOT_ENV)
    if configured is None:
        pytest.skip(f"real-GF test requires {_RGL_ROOT_ENV} to be configured")
    return _resolve_directory(configured, variable=_RGL_ROOT_ENV)
