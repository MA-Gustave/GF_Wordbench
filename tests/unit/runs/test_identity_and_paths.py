"""Unit tests for canonical run identity and run-owned paths."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

import pytest

from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError
from gf_wordbench.runs import paths as paths_module
from gf_wordbench.runs.identity import (
    BASE_COLLISION_INDEX,
    FIRST_SUFFIXED_COLLISION_INDEX,
    RUN_DIRECTORY_PREFIX,
    RUN_ID_TIMESTAMP_FORMAT,
    create_collision_run_id,
    create_run_id,
    is_run_directory_name,
    iter_run_id_candidates,
    parse_run_directory_name,
    run_directory_name,
    run_id_collision_index,
    run_id_timestamp,
)
from gf_wordbench.runs.models.paths import RunPaths
from gf_wordbench.runs.paths import (
    allocate_run_paths,
    build_run_paths,
    create_run_layout,
    owned_run_paths,
    resolve_run_relative_path,
    run_relative_path,
    standard_run_directories,
    validate_run_paths,
)

_RUN_ID = "20260725_163210"
_COLLISION_RUN_ID = "20260725_163210_02"


def _build_paths(tmp_path: Path) -> RunPaths:
    run_dir = tmp_path / f"run_{_RUN_ID}"
    run_dir.mkdir()
    return build_run_paths(_RUN_ID, run_dir)


def test_create_run_id_uses_utc_and_canonical_zero_padding() -> None:
    local_timestamp = datetime(
        2026,
        7,
        25,
        18,
        32,
        10,
        987_654,
        tzinfo=timezone(timedelta(hours=2)),
    )

    assert RUN_ID_TIMESTAMP_FORMAT == "%Y%m%d_%H%M%S"
    assert str(create_run_id(local_timestamp)) == _RUN_ID
    assert str(create_run_id(local_timestamp, collision_index=2)) == _COLLISION_RUN_ID
    assert str(create_run_id(local_timestamp, collision_index=9)) == "20260725_163210_09"
    assert str(create_run_id(local_timestamp, collision_index=12)) == "20260725_163210_12"
    assert str(create_run_id(local_timestamp, collision_index=100)) == "20260725_163210_100"


def test_run_identity_constants_lock_collision_semantics() -> None:
    assert RUN_DIRECTORY_PREFIX == "run_"
    assert BASE_COLLISION_INDEX == 1
    assert FIRST_SUFFIXED_COLLISION_INDEX == 2


def test_create_run_id_rejects_invalid_timestamp_and_collision_index() -> None:
    with pytest.raises(TypeError, match="timestamp must be a datetime"):
        create_run_id("2026-07-25")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        create_run_id(datetime(2026, 7, 25, 16, 32, 10))

    for value in (True, 1.5, "2"):
        with pytest.raises(TypeError, match="collision_index must be an integer"):
            create_run_id(datetime.now(UTC), collision_index=value)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="at least 1"):
        create_run_id(datetime.now(UTC), collision_index=0)


def test_collision_run_id_requires_an_unsuffixed_base() -> None:
    assert str(create_collision_run_id(_RUN_ID, 1)) == _RUN_ID
    assert str(create_collision_run_id(_RUN_ID, 2)) == _COLLISION_RUN_ID
    assert str(create_collision_run_id(_RUN_ID, 25)) == "20260725_163210_25"

    with pytest.raises(ValueError, match="must not already contain"):
        create_collision_run_id(_COLLISION_RUN_ID, 3)


def test_candidate_iterator_is_deterministic_and_unbounded() -> None:
    candidates = iter_run_id_candidates(
        datetime(2026, 7, 25, 12, 32, 10, tzinfo=timezone(timedelta(hours=-4)))
    )

    assert [str(next(candidates)) for _ in range(5)] == [
        _RUN_ID,
        _COLLISION_RUN_ID,
        "20260725_163210_03",
        "20260725_163210_04",
        "20260725_163210_05",
    ]


def test_run_directory_name_round_trip_is_exact() -> None:
    directory_name = run_directory_name(_COLLISION_RUN_ID)

    assert directory_name == "run_20260725_163210_02"
    assert parse_run_directory_name(directory_name) == _COLLISION_RUN_ID
    assert is_run_directory_name(directory_name)
    assert run_id_timestamp(_COLLISION_RUN_ID) == datetime(
        2026,
        7,
        25,
        16,
        32,
        10,
        tzinfo=UTC,
    )
    assert run_id_collision_index(_RUN_ID) == 1
    assert run_id_collision_index(_COLLISION_RUN_ID) == 2


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "run_",
        _RUN_ID,
        "nested/run_20260725_163210",
        r"nested\run_20260725_163210",
        "RUN_20260725_163210",
        "run_20260230_163210",
        "run_20260725_163210_01",
        "run_20260725_163210_2",
    ],
)
def test_noncanonical_run_directory_names_are_rejected(value: object) -> None:
    assert not is_run_directory_name(value)
    with pytest.raises((TypeError, ValueError)):
        parse_run_directory_name(value)


def test_build_run_paths_creates_the_authoritative_registry(tmp_path: Path) -> None:
    run_dir = tmp_path / f"run_{_RUN_ID}"
    run_dir.mkdir()

    paths = build_run_paths(_RUN_ID, run_dir)

    assert isinstance(paths, RunPaths)
    assert paths.run_id == _RUN_ID
    assert paths.run_dir == run_dir
    assert paths.report_files == (
        run_dir / "summary.json",
        run_dir / "summary.md",
        run_dir / "AI_READY.md",
        run_dir / "top_errors.txt",
        run_dir / "manifest.json",
    )
    assert paths.log_files == (
        run_dir / "raw" / "master.log",
        run_dir / "raw" / "ALL_SCAN_LOGS.TXT",
        run_dir / "raw" / "ALL_LOGS.TXT",
    )
    assert paths.standard_directories == (
        run_dir / "details",
        run_dir / "raw",
        run_dir / "raw" / "compile",
        run_dir / "raw" / "scan",
        run_dir / "raw" / "scenarios",
        run_dir / "artifacts",
        run_dir / "artifacts" / "gfo",
        run_dir / "artifacts" / "out",
        run_dir / "artifacts" / "pgf",
    )
    assert len(paths.owned_paths) == 18
    assert len(set(paths.owned_paths)) == len(paths.owned_paths)
    assert all(path.is_absolute() for path in paths.owned_paths)
    assert all(path == run_dir or path.is_relative_to(run_dir) for path in paths.owned_paths)
    assert run_dir.is_dir()
    assert all(not directory.exists() for directory in paths.standard_directories)
    assert validate_run_paths(paths) is paths


def test_run_paths_are_frozen_and_reject_noncanonical_fields(tmp_path: Path) -> None:
    paths = _build_paths(tmp_path)

    with pytest.raises(FrozenInstanceError):
        paths.run_id = "20260725_163211"  # type: ignore[misc]

    with pytest.raises(ContractViolationError, match="canonical run-relative location"):
        replace(paths, summary_json=paths.run_dir / "summary-v2.json")

    with pytest.raises(ContractViolationError, match="directory name"):
        replace(paths, run_id="20260725_163211")


def test_build_run_paths_requires_absolute_matching_run_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run_dir must be absolute"):
        build_run_paths(_RUN_ID, Path(f"run_{_RUN_ID}"))

    with pytest.raises(ValueError, match="must be named"):
        build_run_paths(_RUN_ID, tmp_path / "run_wrong")

    with pytest.raises(TypeError, match="pathlib.Path"):
        build_run_paths(_RUN_ID, str(tmp_path / f"run_{_RUN_ID}"))  # type: ignore[arg-type]


def test_allocate_run_paths_creates_the_complete_layout_exclusively(
    tmp_path: Path,
) -> None:
    paths = allocate_run_paths(tmp_path, _RUN_ID)

    assert paths.run_dir.is_dir()
    assert all(directory.is_dir() for directory in paths.standard_directories)
    assert all(not report.exists() for report in paths.report_files)
    assert all(not log.exists() for log in paths.log_files)
    assert validate_run_paths(paths, require_directories=True) is paths

    with pytest.raises(FileExistsError):
        allocate_run_paths(tmp_path, _RUN_ID)


def test_allocate_run_paths_requires_an_existing_output_directory(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        allocate_run_paths(missing_root, _RUN_ID)

    output_file = tmp_path / "output-file"
    output_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        allocate_run_paths(output_file, _RUN_ID)


def test_create_run_layout_rejects_a_second_initialization(tmp_path: Path) -> None:
    run_dir = tmp_path / f"run_{_RUN_ID}"
    run_dir.mkdir()
    paths = build_run_paths(_RUN_ID, run_dir)

    assert create_run_layout(paths) is paths
    with pytest.raises(FileExistsError):
        create_run_layout(paths)


def test_allocation_rolls_back_empty_directories_after_layout_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    original_create_directory = paths_module.create_directory
    calls = 0

    def fail_during_layout(path: Path, **kwargs: object) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected layout failure")
        return original_create_directory(path, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(paths_module, "create_directory", fail_during_layout)

    with pytest.raises(OSError, match="injected layout failure"):
        allocate_run_paths(tmp_path, _RUN_ID)

    assert not (tmp_path / f"run_{_RUN_ID}").exists()


def test_owned_path_views_have_stable_field_and_creation_order(tmp_path: Path) -> None:
    paths = _build_paths(tmp_path)

    owned = owned_run_paths(paths)
    directories = standard_run_directories(paths)

    assert tuple(name for name, _ in owned) == (
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
    assert tuple(name for name, _ in directories) == (
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


def test_run_relative_path_round_trip_uses_posix_form(tmp_path: Path) -> None:
    paths = _build_paths(tmp_path)

    for absolute, expected in (
        (paths.summary_json, PurePosixPath("summary.json")),
        (paths.master_log, PurePosixPath("raw/master.log")),
        (paths.pgf_dir / "Grammar.pgf", PurePosixPath("artifacts/pgf/Grammar.pgf")),
    ):
        relative = run_relative_path(paths, absolute)
        assert relative == expected
        assert resolve_run_relative_path(paths, relative) == absolute


def test_run_relative_conversion_rejects_root_escape_and_nonportable_input(
    tmp_path: Path,
) -> None:
    paths = _build_paths(tmp_path)

    with pytest.raises(PermissionError):
        run_relative_path(paths, tmp_path / "outside.txt")

    with pytest.raises(PermissionError):
        run_relative_path(paths, paths.run_dir)

    for value in (
        "../outside.txt",
        "/absolute.txt",
        r"raw\master.log",
        ".",
        "",
    ):
        with pytest.raises((TypeError, ValueError, ContractViolationError, PathSecurityError)):
            resolve_run_relative_path(paths, value)


def test_run_paths_model_owned_path_helpers_enforce_containment(
    tmp_path: Path,
) -> None:
    paths = _build_paths(tmp_path)

    assert paths.require_owned_path(paths.master_log) == paths.master_log
    assert paths.require_owned_path(paths.run_dir, allow_run_dir=True) == paths.run_dir
    assert paths.relative_path(paths.master_log) == PurePosixPath("raw/master.log")
    assert paths.relative_path(paths.run_dir, allow_run_dir=True) == PurePosixPath(".")

    with pytest.raises(PathSecurityError):
        paths.require_owned_path(tmp_path / "outside.txt")

    with pytest.raises(PathSecurityError):
        paths.relative_path(paths.run_dir)


def test_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    paths = allocate_run_paths(tmp_path, _RUN_ID)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = paths.raw_dir / "escape"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(PermissionError):
        resolve_run_relative_path(paths, "raw/escape/evidence.txt")


def test_validate_run_paths_rejects_invalid_arguments(tmp_path: Path) -> None:
    paths = _build_paths(tmp_path)

    with pytest.raises(TypeError, match="RunPaths"):
        validate_run_paths(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="bool"):
        validate_run_paths(paths, require_directories=1)  # type: ignore[arg-type]

    with pytest.raises(FileNotFoundError):
        validate_run_paths(paths, require_directories=True)
