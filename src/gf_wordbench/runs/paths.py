"""Canonical allocation and validation of GF Wordbench run paths."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Final

from gf_wordbench.infrastructure.filesystem import (
    create_directory,
    create_directory_exclusive,
    remove_empty_directory,
    require_directory,
    require_within,
    resolve_for_output,
)
from gf_wordbench.kernel.ids import RunId, validate_run_id
from gf_wordbench.kernel.paths import normalize_portable_path

from .models.paths import RunPaths

__all__ = (
    "allocate_run_paths",
    "build_run_paths",
    "create_run_layout",
    "owned_run_paths",
    "resolve_run_relative_path",
    "run_relative_path",
    "standard_run_directories",
    "validate_run_paths",
)

_RUN_PREFIX: Final[str] = "run_"

_SUMMARY_JSON: Final[str] = "summary.json"
_SUMMARY_MARKDOWN: Final[str] = "summary.md"
_AI_READY: Final[str] = "AI_READY.md"
_TOP_ERRORS: Final[str] = "top_errors.txt"
_MANIFEST: Final[str] = "manifest.json"

_DETAILS_DIR: Final[str] = "details"
_RAW_DIR: Final[str] = "raw"
_MASTER_LOG: Final[tuple[str, str]] = (_RAW_DIR, "master.log")
_ALL_SCAN_LOGS: Final[tuple[str, str]] = (_RAW_DIR, "ALL_SCAN_LOGS.TXT")
_ALL_LOGS: Final[tuple[str, str]] = (_RAW_DIR, "ALL_LOGS.TXT")
_RAW_COMPILE_DIR: Final[tuple[str, str]] = (_RAW_DIR, "compile")
_RAW_SCAN_DIR: Final[tuple[str, str]] = (_RAW_DIR, "scan")
_RAW_SCENARIOS_DIR: Final[tuple[str, str]] = (_RAW_DIR, "scenarios")

_ARTIFACTS_DIR: Final[str] = "artifacts"
_GFO_DIR: Final[tuple[str, str]] = (_ARTIFACTS_DIR, "gfo")
_OUT_DIR: Final[tuple[str, str]] = (_ARTIFACTS_DIR, "out")
_PGF_DIR: Final[tuple[str, str]] = (_ARTIFACTS_DIR, "pgf")

_PATH_FIELD_NAMES: Final[tuple[str, ...]] = (
    "run_dir",
    "summary_json",
    "summary_md",
    "ai_ready_md",
    "top_errors_txt",
    "manifest_json",
    "details_dir",
    "raw_dir",
    "master_log",
    "all_scan_logs",
    "all_logs",
    "raw_compile_dir",
    "raw_scan_dir",
    "raw_scenarios_dir",
    "artifacts_dir",
    "gfo_dir",
    "out_dir",
    "pgf_dir",
)

_DIRECTORY_FIELD_NAMES: Final[tuple[str, ...]] = (
    "run_dir",
    "details_dir",
    "raw_dir",
    "raw_compile_dir",
    "raw_scan_dir",
    "raw_scenarios_dir",
    "artifacts_dir",
    "gfo_dir",
    "out_dir",
    "pgf_dir",
)


def build_run_paths(
    run_id: RunId | str,
    run_dir: Path,
) -> RunPaths:
    """Build the immutable canonical path registry for one run."""

    validated_id = validate_run_id(run_id)
    resolved_run_dir = _require_absolute_output_path(
        run_dir,
        field_name="run_dir",
    )
    expected_name = f"{_RUN_PREFIX}{validated_id}"
    if resolved_run_dir.name != expected_name:
        raise ValueError(f"run_dir must be named {expected_name!r}, got {resolved_run_dir.name!r}")

    paths = RunPaths(
        run_id=validated_id,
        run_dir=resolved_run_dir,
        summary_json=resolved_run_dir / _SUMMARY_JSON,
        summary_md=resolved_run_dir / _SUMMARY_MARKDOWN,
        ai_ready_md=resolved_run_dir / _AI_READY,
        top_errors_txt=resolved_run_dir / _TOP_ERRORS,
        manifest_json=resolved_run_dir / _MANIFEST,
        details_dir=resolved_run_dir / _DETAILS_DIR,
        raw_dir=resolved_run_dir / _RAW_DIR,
        master_log=resolved_run_dir.joinpath(*_MASTER_LOG),
        all_scan_logs=resolved_run_dir.joinpath(*_ALL_SCAN_LOGS),
        all_logs=resolved_run_dir.joinpath(*_ALL_LOGS),
        raw_compile_dir=resolved_run_dir.joinpath(*_RAW_COMPILE_DIR),
        raw_scan_dir=resolved_run_dir.joinpath(*_RAW_SCAN_DIR),
        raw_scenarios_dir=resolved_run_dir.joinpath(*_RAW_SCENARIOS_DIR),
        artifacts_dir=resolved_run_dir / _ARTIFACTS_DIR,
        gfo_dir=resolved_run_dir.joinpath(*_GFO_DIR),
        out_dir=resolved_run_dir.joinpath(*_OUT_DIR),
        pgf_dir=resolved_run_dir.joinpath(*_PGF_DIR),
    )
    return validate_run_paths(paths)


def allocate_run_paths(
    output_root: Path,
    run_id: RunId | str,
) -> RunPaths:
    """Create one exclusive canonical run directory and its standard layout."""

    root = require_directory(output_root, role="run output root")
    validated_id = validate_run_id(run_id)
    run_dir = root / f"{_RUN_PREFIX}{validated_id}"
    created_root = create_directory_exclusive(
        run_dir,
        root=root,
        role="run directory",
    )
    paths = build_run_paths(validated_id, created_root)

    try:
        create_run_layout(paths)
    except BaseException:
        _remove_empty_layout(paths)
        raise

    return validate_run_paths(paths, require_directories=True)


def create_run_layout(paths: RunPaths) -> RunPaths:
    """Create and validate every canonical run-owned directory."""

    validated = validate_run_paths(paths)
    run_dir = require_directory(
        validated.run_dir,
        role="run directory",
    )

    for field_name, directory in standard_run_directories(validated):
        if field_name == "run_dir":
            continue
        create_directory(
            directory,
            parents=False,
            exist_ok=False,
            root=run_dir,
            role=field_name,
        )

    return validate_run_paths(validated, require_directories=True)


def validate_run_paths(
    paths: RunPaths,
    *,
    require_directories: bool = False,
) -> RunPaths:
    """Validate canonical names, uniqueness, absolute paths and containment."""

    if not isinstance(paths, RunPaths):
        raise TypeError("paths must be a RunPaths instance")
    if type(require_directories) is not bool:
        raise TypeError("require_directories must be a bool")

    run_id = validate_run_id(paths.run_id)
    run_dir = _require_absolute_output_path(
        paths.run_dir,
        field_name="run_dir",
    )
    expected_name = f"{_RUN_PREFIX}{run_id}"
    if run_dir.name != expected_name:
        raise ValueError(f"run_dir must be named {expected_name!r}, got {run_dir.name!r}")

    expected = build_expected_path_map(run_dir)
    identities: set[str] = set()

    for field_name in _PATH_FIELD_NAMES:
        actual = _require_absolute_output_path(
            getattr(paths, field_name),
            field_name=field_name,
        )
        if actual != expected[field_name]:
            raise ValueError(f"{field_name} must be {expected[field_name]!s}, got {actual!s}")

        identity = _path_identity(actual)
        if identity in identities:
            raise ValueError(f"duplicate run-owned path: {actual!s}")
        identities.add(identity)

        if field_name != "run_dir":
            require_within(
                actual,
                run_dir,
                role=field_name,
                stage="run-path validation",
                allow_equal=False,
                for_output=True,
            )

    if require_directories:
        for field_name, directory in standard_run_directories(paths):
            require_directory(
                directory,
                root=None if field_name == "run_dir" else run_dir,
                role=field_name,
            )

    return paths


def owned_run_paths(paths: RunPaths) -> tuple[tuple[str, Path], ...]:
    """Return every canonical run-owned path in stable field order."""

    validate_run_paths(paths)
    return tuple((field_name, Path(getattr(paths, field_name))) for field_name in _PATH_FIELD_NAMES)


def standard_run_directories(
    paths: RunPaths,
) -> tuple[tuple[str, Path], ...]:
    """Return every canonical directory in safe creation order."""

    validate_run_paths(paths)
    return tuple(
        (field_name, Path(getattr(paths, field_name))) for field_name in _DIRECTORY_FIELD_NAMES
    )


def run_relative_path(
    paths: RunPaths,
    path: Path,
) -> PurePosixPath:
    """Return a canonical run-relative reference for one owned path."""

    validate_run_paths(paths)
    absolute = _require_absolute_output_path(path, field_name="path")
    contained = require_within(
        absolute,
        paths.run_dir,
        role="run-owned path",
        stage="run-relative serialization",
        allow_equal=False,
        for_output=True,
    )
    relative = contained.relative_to(paths.run_dir)
    return normalize_portable_path(
        relative.as_posix(),
        role="run-relative path",
        allow_root=False,
        accept_backslash=False,
    )


def resolve_run_relative_path(
    paths: RunPaths,
    relative_path: str | PurePosixPath,
) -> Path:
    """Resolve one canonical run-relative path without permitting escape."""

    validate_run_paths(paths)
    portable = normalize_portable_path(
        relative_path,
        role="run-relative path",
        allow_root=False,
        accept_backslash=False,
    )
    candidate = paths.run_dir.joinpath(*portable.parts)
    return require_within(
        candidate,
        paths.run_dir,
        role="run-relative path",
        stage="run-relative resolution",
        allow_equal=False,
        for_output=True,
    )


def build_expected_path_map(run_dir: Path) -> dict[str, Path]:
    """Return the canonical field-to-path mapping for one run root."""

    root = _require_absolute_output_path(run_dir, field_name="run_dir")
    return {
        "run_dir": root,
        "summary_json": root / _SUMMARY_JSON,
        "summary_md": root / _SUMMARY_MARKDOWN,
        "ai_ready_md": root / _AI_READY,
        "top_errors_txt": root / _TOP_ERRORS,
        "manifest_json": root / _MANIFEST,
        "details_dir": root / _DETAILS_DIR,
        "raw_dir": root / _RAW_DIR,
        "master_log": root.joinpath(*_MASTER_LOG),
        "all_scan_logs": root.joinpath(*_ALL_SCAN_LOGS),
        "all_logs": root.joinpath(*_ALL_LOGS),
        "raw_compile_dir": root.joinpath(*_RAW_COMPILE_DIR),
        "raw_scan_dir": root.joinpath(*_RAW_SCAN_DIR),
        "raw_scenarios_dir": root.joinpath(*_RAW_SCENARIOS_DIR),
        "artifacts_dir": root / _ARTIFACTS_DIR,
        "gfo_dir": root.joinpath(*_GFO_DIR),
        "out_dir": root.joinpath(*_OUT_DIR),
        "pgf_dir": root.joinpath(*_PGF_DIR),
    }


def _remove_empty_layout(paths: RunPaths) -> None:
    directories = tuple(
        directory
        for field_name, directory in standard_run_directories(paths)
        if field_name != "run_dir"
    )
    for directory in reversed(directories):
        try:
            remove_empty_directory(
                directory,
                root=paths.run_dir,
                role="partially initialized run directory",
            )
        except FileNotFoundError:
            continue
        except OSError:
            return

    try:
        remove_empty_directory(
            paths.run_dir,
            role="partially initialized run root",
        )
    except OSError:
        return


def _require_absolute_output_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL")
    return resolve_for_output(value)


def _path_identity(path: Path) -> str:
    return str(path).casefold() if _is_case_insensitive_platform() else str(path)


def _is_case_insensitive_platform() -> bool:
    return Path("A") == Path("a") or __import__("os").name == "nt"
