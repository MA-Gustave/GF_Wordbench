"""Canonical path helpers for immutable GF Wordbench test fixtures.

The fixed test architecture keeps fixture payloads below ``tests/fixtures`` and
requires tests to address them explicitly rather than depending on the current
working directory.  Repository fixtures are read-only inputs: tests that need
to modify a fixture must first copy it into a temporary directory.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path, PurePath
from typing import Final, TypeAlias

__all__ = (
    "FIXTURES_ROOT",
    "REPOSITORY_ROOT",
    "TESTS_ROOT",
    "FixtureArea",
    "FixtureKind",
    "FixturePathError",
    "FixturePaths",
    "copy_fixture",
    "diagnostic_fixture",
    "discover_repository_root",
    "executable_fixture",
    "fixture_path",
    "fixture_paths",
    "fixture_project",
    "gf_fixture",
    "iter_fixture_files",
    "legacy_fixture",
    "relative_fixture_path",
    "report_fixture",
    "scenario_fixture",
    "schema_fixture",
)

PathInput: TypeAlias = str | os.PathLike[str]


class FixturePathError(ValueError):
    """Raised when a fixture path violates the test-fixture boundary."""


@unique
class FixtureArea(StrEnum):
    """Canonical variable-content zones below ``tests/fixtures``."""

    PROJECTS = "projects"
    GF = "gf"
    DIAGNOSTICS = "diagnostics"
    SCHEMAS = "schemas"
    REPORTS = "reports"
    SCENARIOS = "scenarios"
    LEGACY = "legacy"
    EXECUTABLES = "executables"


@unique
class FixtureKind(StrEnum):
    """Optional filesystem-kind requirement for a resolved fixture."""

    ANY = "any"
    FILE = "file"
    DIRECTORY = "directory"


# These constants are correct once this module is installed at
# tests/helpers/fixture_paths.py.  They perform no filesystem validation at
# import time, which keeps test collection deterministic in partial checkouts.
TESTS_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT: Final[Path] = TESTS_ROOT.parent
FIXTURES_ROOT: Final[Path] = TESTS_ROOT / "fixtures"


def _coerce_area(value: FixtureArea | str) -> FixtureArea:
    if isinstance(value, FixtureArea):
        return value
    if not isinstance(value, str):
        raise TypeError("fixture area must be a FixtureArea or string")
    normalized = value.strip().casefold()
    if not normalized:
        raise FixturePathError("fixture area must not be empty")
    try:
        return FixtureArea(normalized)
    except ValueError as exc:
        allowed = ", ".join(area.value for area in FixtureArea)
        raise FixturePathError(
            f"unknown fixture area {value!r}; expected one of: {allowed}"
        ) from exc


def _coerce_kind(value: FixtureKind | str | None) -> FixtureKind:
    if value is None:
        return FixtureKind.ANY
    if isinstance(value, FixtureKind):
        return value
    if not isinstance(value, str):
        raise TypeError("fixture kind must be a FixtureKind, string, or None")
    normalized = value.strip().casefold()
    try:
        return FixtureKind(normalized)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in FixtureKind)
        raise FixturePathError(
            f"unknown fixture kind {value!r}; expected one of: {allowed}"
        ) from exc


def _validated_relative_parts(parts: Sequence[PathInput]) -> tuple[str, ...]:
    if not parts:
        return ()

    normalized: list[str] = []
    for raw_part in parts:
        if isinstance(raw_part, bytes):
            raise TypeError("fixture path parts must not be bytes")
        try:
            path = PurePath(os.fspath(raw_part))
        except TypeError as exc:
            raise TypeError("fixture path parts must be path-like") from exc

        if path.is_absolute() or path.anchor:
            raise FixturePathError(
                f"fixture path part must be relative: {os.fspath(raw_part)!r}"
            )

        for component in path.parts:
            if component in ("", "."):
                continue
            if component == "..":
                raise FixturePathError("fixture paths must not contain '..'")
            if "\x00" in component:
                raise FixturePathError("fixture paths must not contain NUL bytes")
            normalized.append(component)

    return tuple(normalized)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_beneath(root: Path, parts: Sequence[PathInput]) -> Path:
    relative_parts = _validated_relative_parts(parts)
    candidate = root.joinpath(*relative_parts)

    # ``strict=False`` resolves any existing symlink prefix while still
    # allowing callers to address a not-yet-created destination.  This blocks
    # both lexical ``..`` traversal and escape through fixture symlinks.
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    if not _is_within(resolved_candidate, resolved_root):
        raise FixturePathError(
            f"fixture path escapes {resolved_root}: {candidate}"
        )
    return resolved_candidate


def _require_path(
    path: Path,
    *,
    must_exist: bool,
    kind: FixtureKind,
) -> Path:
    if not must_exist:
        return path

    if not path.exists():
        raise FileNotFoundError(f"fixture does not exist: {path}")
    if kind is FixtureKind.FILE and not path.is_file():
        raise IsADirectoryError(f"fixture is not a regular file: {path}")
    if kind is FixtureKind.DIRECTORY and not path.is_dir():
        raise NotADirectoryError(f"fixture is not a directory: {path}")
    return path


def discover_repository_root(start: PathInput | None = None) -> Path:
    """Locate the repository without consulting the current working directory.

    A valid root contains both ``pyproject.toml`` and ``src/gf_wordbench``.
    When *start* is omitted, discovery begins from this module's installed
    location.  The nearest valid ancestor wins.
    """

    origin = Path(__file__) if start is None else Path(start)
    origin = origin.resolve(strict=False)
    current = origin.parent if origin.suffix or origin.is_file() else origin

    for candidate in (current, *current.parents):
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "gf_wordbench").is_dir()
        ):
            return candidate

    raise FileNotFoundError(
        f"could not locate GF Wordbench repository above {current}"
    )


@dataclass(frozen=True, slots=True)
class FixturePaths:
    """Immutable locator for canonical repository test-fixture zones."""

    repository_root: Path
    tests_root: Path
    root: Path

    def __post_init__(self) -> None:
        repository_root = Path(self.repository_root).resolve(strict=False)
        tests_root = Path(self.tests_root).resolve(strict=False)
        root = Path(self.root).resolve(strict=False)

        if tests_root != repository_root / "tests":
            raise FixturePathError(
                "tests_root must be the repository's canonical 'tests' directory"
            )
        if root != tests_root / "fixtures":
            raise FixturePathError(
                "root must be the canonical 'tests/fixtures' directory"
            )

        object.__setattr__(self, "repository_root", repository_root)
        object.__setattr__(self, "tests_root", tests_root)
        object.__setattr__(self, "root", root)

    @classmethod
    def from_repository_root(cls, root: PathInput) -> "FixturePaths":
        repository_root = Path(root).resolve(strict=False)
        tests_root = repository_root / "tests"
        return cls(
            repository_root=repository_root,
            tests_root=tests_root,
            root=tests_root / "fixtures",
        )

    @classmethod
    def discover(cls, start: PathInput | None = None) -> "FixturePaths":
        return cls.from_repository_root(discover_repository_root(start))

    def area(self, area: FixtureArea | str) -> Path:
        return self.root / _coerce_area(area).value

    @property
    def projects(self) -> Path:
        return self.area(FixtureArea.PROJECTS)

    @property
    def gf(self) -> Path:
        return self.area(FixtureArea.GF)

    @property
    def diagnostics(self) -> Path:
        return self.area(FixtureArea.DIAGNOSTICS)

    @property
    def schemas(self) -> Path:
        return self.area(FixtureArea.SCHEMAS)

    @property
    def reports(self) -> Path:
        return self.area(FixtureArea.REPORTS)

    @property
    def scenarios(self) -> Path:
        return self.area(FixtureArea.SCENARIOS)

    @property
    def legacy(self) -> Path:
        return self.area(FixtureArea.LEGACY)

    @property
    def executables(self) -> Path:
        return self.area(FixtureArea.EXECUTABLES)

    def resolve(
        self,
        *parts: PathInput,
        area: FixtureArea | str | None = None,
        must_exist: bool = True,
        kind: FixtureKind | str | None = None,
    ) -> Path:
        """Resolve an explicit fixture path and enforce the fixture boundary."""

        base = self.root if area is None else self.area(area)
        path = _resolve_beneath(base, parts)
        return _require_path(
            path,
            must_exist=must_exist,
            kind=_coerce_kind(kind),
        )

    def relative(self, path: PathInput) -> Path:
        """Return the canonical path relative to ``tests/fixtures``."""

        candidate = Path(path).resolve(strict=False)
        root = self.root.resolve(strict=False)
        if not _is_within(candidate, root):
            raise FixturePathError(f"path is outside the fixture root: {candidate}")
        return candidate.relative_to(root)

    def iter_files(
        self,
        *,
        area: FixtureArea | str | None = None,
        suffix: str | Sequence[str] | None = None,
        recursive: bool = True,
    ) -> Iterator[Path]:
        """Yield existing fixture files in deterministic portable-path order."""

        base = self.root if area is None else self.area(area)
        if not base.exists():
            return
        if not base.is_dir():
            raise NotADirectoryError(f"fixture area is not a directory: {base}")

        suffixes = _normalize_suffixes(suffix)
        iterator: Iterable[Path] = base.rglob("*") if recursive else base.glob("*")
        files = (
            path
            for path in iterator
            if path.is_file()
            and (not suffixes or path.suffix.casefold() in suffixes)
        )
        yield from sorted(
            files,
            key=lambda item: item.relative_to(base).as_posix().casefold(),
        )


def _normalize_suffixes(
    suffix: str | Sequence[str] | None,
) -> frozenset[str]:
    if suffix is None:
        return frozenset()
    values = (suffix,) if isinstance(suffix, str) else tuple(suffix)
    normalized: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("fixture suffixes must be strings")
        text = value.strip().casefold()
        if not text:
            raise FixturePathError("fixture suffix must not be empty")
        normalized.add(text if text.startswith(".") else f".{text}")
    return frozenset(normalized)


def fixture_paths(
    repository_root: PathInput | None = None,
) -> FixturePaths:
    """Return canonical fixture paths for the installed or supplied repository."""

    if repository_root is None:
        return FixturePaths.from_repository_root(REPOSITORY_ROOT)
    return FixturePaths.from_repository_root(repository_root)


def fixture_path(
    *parts: PathInput,
    area: FixtureArea | str | None = None,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_paths(repository_root).resolve(
        *parts,
        area=area,
        must_exist=must_exist,
        kind=kind,
    )


def fixture_project(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.PROJECTS,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def gf_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.GF,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def diagnostic_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.DIAGNOSTICS,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def schema_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.SCHEMAS,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def report_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.REPORTS,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def scenario_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.SCENARIOS,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def legacy_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = None,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.LEGACY,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def executable_fixture(
    *parts: PathInput,
    must_exist: bool = True,
    kind: FixtureKind | str | None = FixtureKind.FILE,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_path(
        *parts,
        area=FixtureArea.EXECUTABLES,
        must_exist=must_exist,
        kind=kind,
        repository_root=repository_root,
    )


def relative_fixture_path(
    path: PathInput,
    *,
    repository_root: PathInput | None = None,
) -> Path:
    return fixture_paths(repository_root).relative(path)


def iter_fixture_files(
    *,
    area: FixtureArea | str | None = None,
    suffix: str | Sequence[str] | None = None,
    recursive: bool = True,
    repository_root: PathInput | None = None,
) -> Iterator[Path]:
    yield from fixture_paths(repository_root).iter_files(
        area=area,
        suffix=suffix,
        recursive=recursive,
    )


def copy_fixture(
    source: PathInput,
    destination: PathInput,
    *,
    area: FixtureArea | str | None = None,
    overwrite: bool = False,
    repository_root: PathInput | None = None,
) -> Path:
    """Copy an immutable repository fixture into a writable test location.

    ``source`` is interpreted relative to ``tests/fixtures`` or to *area*.
    Existing destinations are rejected unless ``overwrite=True``.  Directory
    copies preserve the source directory name only when the destination itself
    does not yet exist, matching :func:`shutil.copytree` semantics.
    """

    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be a bool")

    source_path = fixture_path(
        source,
        area=area,
        must_exist=True,
        repository_root=repository_root,
    )
    destination_path = Path(destination).resolve(strict=False)

    fixture_root = fixture_paths(repository_root).root.resolve(strict=False)
    if _is_within(destination_path, fixture_root):
        raise FixturePathError(
            "repository fixtures are read-only; copy to tmp_path or another "
            "location outside tests/fixtures"
        )

    if source_path.is_dir():
        if destination_path.exists() and not overwrite:
            raise FileExistsError(f"destination already exists: {destination_path}")
        if destination_path.exists() and not destination_path.is_dir():
            raise NotADirectoryError(
                f"directory fixture destination is not a directory: {destination_path}"
            )
        return Path(
            shutil.copytree(
                source_path,
                destination_path,
                dirs_exist_ok=overwrite,
                copy_function=shutil.copy2,
            )
        )

    if not source_path.is_file():
        raise FixturePathError(f"fixture is neither a file nor directory: {source_path}")

    if destination_path.exists():
        if destination_path.is_dir():
            destination_path = destination_path / source_path.name
        elif not overwrite:
            raise FileExistsError(f"destination already exists: {destination_path}")

    if destination_path.exists() and not overwrite:
        raise FileExistsError(f"destination already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    return Path(shutil.copy2(source_path, destination_path))
