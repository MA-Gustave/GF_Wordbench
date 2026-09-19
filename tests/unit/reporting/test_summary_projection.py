"""Unit tests for canonical run-summary projection."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from gf_wordbench.kernel.serialization import JsonValue
from gf_wordbench.reporting.schemas.summary_v1 import validate_summary_v1
from gf_wordbench.reporting.summary.projection import (
    SUMMARY_PRODUCER_NAME,
    SUMMARY_SCHEMA_ID,
    SUMMARY_SCHEMA_VERSION,
    SummaryProjectionError,
    build_summary_document,
    project_artifacts,
    project_diff_entry,
    project_file_result,
    project_fingerprint,
    project_metadata,
    project_producer,
    project_scenario_result,
    project_top_error,
    project_totals,
    validate_projection_invariants,
)

_TIMESTAMP = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
_SHA_A = "a" * 64
_SHA_B = "b" * 64


def _json_object(value: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value


def _json_object_array(value: JsonValue) -> list[dict[str, JsonValue]]:
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return cast("list[dict[str, JsonValue]]", value)


def _namespace(**values: Any) -> SimpleNamespace:
    return SimpleNamespace(**values)


def _run_paths(tmp_path: Path) -> SimpleNamespace:
    run_id = "20260725_120000"
    run_dir = (tmp_path / "runs" / f"run_{run_id}").resolve()
    return _namespace(
        run_id=run_id,
        run_dir=run_dir,
        summary_json=run_dir / "summary.json",
        summary_md=run_dir / "summary.md",
        ai_ready_md=run_dir / "AI_READY.md",
        top_errors_txt=run_dir / "top_errors.txt",
        manifest_json=run_dir / "manifest.json",
        details_dir=run_dir / "details",
        raw_dir=run_dir / "raw",
        master_log=run_dir / "raw" / "master.log",
        all_scan_logs=run_dir / "raw" / "ALL_SCAN_LOGS.TXT",
        all_logs=run_dir / "raw" / "ALL_LOGS.TXT",
        raw_compile_dir=run_dir / "raw" / "compile",
        raw_scan_dir=run_dir / "raw" / "scan",
        raw_scenarios_dir=run_dir / "raw" / "scenarios",
        artifacts_dir=run_dir / "artifacts",
        gfo_dir=run_dir / "artifacts" / "gfo",
        out_dir=run_dir / "artifacts" / "out",
        pgf_dir=run_dir / "artifacts" / "pgf",
    )


def _run_config(
    tmp_path: Path,
    *,
    mode: str = "diagnostic",
    target: Path | None = None,
) -> SimpleNamespace:
    project_root = (tmp_path / "project").resolve()
    output_root = (tmp_path / "runs").resolve()
    environment = _namespace(
        project_root=project_root,
        rgl_root=(tmp_path / "rgl").resolve(),
        gf_executable=(tmp_path / "tools" / "gf").resolve(),
        output_root=output_root,
        gf_path=(
            project_root / "src",
            (tmp_path / "rgl").resolve(),
        ),
    )
    project = _namespace(
        identity=_namespace(id="fixture-project", name="Fixture Project"),
        sources=_namespace(directory=Path("src"), glob="*.gf"),
        project_root=project_root,
    )
    return _namespace(
        project=project,
        environment=environment,
        mode=mode,
        target=None if target is None else _namespace(value=target),
        timeout_sec=60,
        max_files=0,
        skip_version_probe=False,
        no_compile=False,
        emit_cpu_stats=False,
        keep_ok_details=False,
        diff_previous=True,
    )


def _scan_counts(**overrides: int) -> SimpleNamespace:
    values = {
        "single_slash_eq": 0,
        "double_slash_dash": 0,
        "runtime_str_match": 0,
        "untyped_case_str_pat": 0,
        "untyped_table_str_pat": 0,
        "trailing_spaces": 0,
    }
    values.update(overrides)
    return _namespace(**values)


def _fingerprint(
    *,
    digest: str = _SHA_A,
    algorithm: str = "sha256",
) -> SimpleNamespace:
    return _namespace(
        size_bytes=17,
        hash_algorithm=algorithm,
        hash=digest,
        last_modified_utc=_TIMESTAMP,
    )


def _compile_summary(
    run_paths: SimpleNamespace,
    *,
    module_name: str,
    ok: bool,
) -> SimpleNamespace:
    return _namespace(
        exit_code=0 if ok else 1,
        timed_out=False,
        duration_ms=25,
        error_kind="OK" if ok else "TYPE",
        first_error="" if ok else "Type mismatch",
        error_detail="",
        stdout_path=run_paths.raw_compile_dir / f"{module_name}.stdout.log",
        stderr_path=run_paths.raw_compile_dir / f"{module_name}.stderr.log",
    )


def _file_result(
    run_config: SimpleNamespace,
    run_paths: SimpleNamespace,
    *,
    relative_path: str,
    ok: bool,
    blocked_by: tuple[str, ...] = (),
    digest: str = _SHA_A,
) -> SimpleNamespace:
    module_name = Path(relative_path).stem
    return _namespace(
        file_path=run_config.project.project_root / relative_path,
        module_name=module_name,
        status="OK" if ok else "FAIL",
        diagnostic_class="ok" if ok else "direct",
        is_direct=not ok,
        blocked_by=list(blocked_by),
        scan_counts=_scan_counts(trailing_spaces=1 if not ok else 0),
        fingerprint=_fingerprint(digest=digest),
        compile_summary=_compile_summary(
            run_paths,
            module_name=module_name,
            ok=ok,
        ),
        scan_log_path=run_paths.raw_scan_dir / f"{module_name}.log",
    )


def _scenario_result(
    run_config: SimpleNamespace,
    run_paths: SimpleNamespace,
    *,
    scenario_id: str = "parse-smoke",
) -> SimpleNamespace:
    return _namespace(
        scenario_id=scenario_id,
        script_path=run_config.project.project_root / "scenarios" / "parse.gfs",
        required=True,
        status="OK",
        command=("gf", "--run", "parse.gfs"),
        working_directory=run_config.project.project_root,
        exit_code=0,
        timed_out=False,
        duration_ms=40,
        stdout_path=run_paths.raw_scenarios_dir / f"{scenario_id}.stdout.log",
        stderr_path=run_paths.raw_scenarios_dir / f"{scenario_id}.stderr.log",
        normalized_output_path=run_paths.out_dir / f"{scenario_id}.out",
        gold_path=run_config.project.project_root / "scenarios" / "parse.gold",
        gold_match=True,
        diagnostic_class="ok",
        error_kind="OK",
        primary_message="",
        sections=(
            _namespace(section_id="load", completed=True),
            _namespace(section_id="parse", completed=True),
        ),
        artifacts=(run_paths.out_dir / f"{scenario_id}.out",),
    )


def _totals() -> SimpleNamespace:
    return _namespace(
        files_seen=2,
        files_included=2,
        files_excluded=0,
        files_ok=1,
        files_fail=1,
        files_error=0,
        files_skipped=0,
        direct_fail=1,
        downstream_fail=0,
        ambiguous_fail=0,
        excluded_noise=0,
        scenarios_seen=1,
        scenarios_ok=1,
        scenarios_fail=0,
        scenarios_error=0,
        scenarios_skipped=0,
        required_scenario_fail=0,
        overall_status="FAIL",
    )


def _completed_run_result(tmp_path: Path) -> SimpleNamespace:
    run_paths = _run_paths(tmp_path)
    project_root = (tmp_path / "project").resolve()
    run_config = _run_config(
        tmp_path,
        target=project_root / "src" / "Main.gf",
    )
    return _namespace(
        run_paths=run_paths,
        run_config=run_config,
        started_at=_TIMESTAMP,
        finished_at=_TIMESTAMP + timedelta(seconds=2),
        duration_ms=2_000,
        gf_version="3.12",
        totals=_totals(),
        overall_status="FAIL",
        file_results=(
            _file_result(
                run_config,
                run_paths,
                relative_path="src/Zeta.gf",
                ok=False,
                blocked_by=("src/Beta.gf", "src/alpha.gf", "src/Beta.gf"),
                digest=_SHA_B,
            ),
            _file_result(
                run_config,
                run_paths,
                relative_path="src/alpha.gf",
                ok=True,
            ),
        ),
        scenario_results=(_scenario_result(run_config, run_paths),),
        diff_entries=(
            _namespace(
                subject_kind="file",
                subject_id="src/alpha.gf",
                previous_status="OK",
                current_status="OK",
                change_kind="unchanged",
                message="No change",
            ),
            _namespace(
                subject_kind="file",
                subject_id=r"src\Zeta.gf",
                previous_status="OK",
                current_status="FAIL",
                change_kind="regressed",
                message="Compilation regressed",
            ),
        ),
        top_errors=(
            _namespace(error_kind="OTHER", message="Unknown constructor", count=1),
            _namespace(error_kind="TYPE", message="Type mismatch", count=3),
        ),
    )


def test_complete_projection_matches_schema_and_canonical_order(tmp_path: Path) -> None:
    document = build_summary_document(
        _completed_run_result(tmp_path),
        producer_version="1.2.3",
    )

    assert validate_summary_v1(document) == ()
    assert document["schema_id"] == SUMMARY_SCHEMA_ID
    assert document["schema_version"] == SUMMARY_SCHEMA_VERSION
    assert document["producer"] == {
        "name": SUMMARY_PRODUCER_NAME,
        "version": "1.2.3",
    }

    metadata = _json_object(document["metadata"])
    assert metadata["run_id"] == "20260725_120000"
    assert metadata["mode"] == "diagnostic"
    assert metadata["target_file"] == "src/Main.gf"
    assert metadata["source_directory"] == "src"
    assert metadata["started_at"] == "2026-07-25T12:00:00Z"
    assert metadata["finished_at"] == "2026-07-25T12:00:02Z"
    assert metadata["gf_path"] == [
        (tmp_path / "project" / "src").resolve().as_posix(),
        (tmp_path / "rgl").resolve().as_posix(),
    ]

    assert document["artifacts"] == {
        "summary_json": "summary.json",
        "summary_markdown": "summary.md",
        "ai_ready": "AI_READY.md",
        "top_errors": "top_errors.txt",
        "manifest": "manifest.json",
        "master_log": "raw/master.log",
        "all_scan_logs": "raw/ALL_SCAN_LOGS.TXT",
        "all_logs": "raw/ALL_LOGS.TXT",
        "details_dir": "details",
        "raw_dir": "raw",
        "compile_logs_dir": "raw/compile",
        "scan_logs_dir": "raw/scan",
        "scenario_logs_dir": "raw/scenarios",
        "artifacts_dir": "artifacts",
        "gfo_dir": "artifacts/gfo",
        "out_dir": "artifacts/out",
        "pgf_dir": "artifacts/pgf",
    }
    file_results = _json_object_array(document["file_results"])
    scenario_results = _json_object_array(document["scenario_results"])
    diff_entries = _json_object_array(document["diff_entries"])
    top_errors = _json_object_array(document["top_errors"])

    assert [item["file_path"] for item in file_results] == [
        "src/alpha.gf",
        "src/Zeta.gf",
    ]
    assert file_results[1]["blocked_by"] == [
        "src/alpha.gf",
        "src/Beta.gf",
    ]
    assert [item["scenario_id"] for item in scenario_results] == ["parse-smoke"]
    assert [item["change_kind"] for item in diff_entries] == [
        "regressed",
        "unchanged",
    ]
    assert [item["count"] for item in top_errors] == [3, 1]


def test_projection_is_deterministic_and_does_not_mutate_input(tmp_path: Path) -> None:
    run_result = _completed_run_result(tmp_path)
    original_file_order = tuple(item.file_path for item in run_result.file_results)
    original_diff_order = tuple(item.change_kind for item in run_result.diff_entries)
    original_top_order = tuple(item.count for item in run_result.top_errors)

    first = build_summary_document(run_result, producer_version="1.0.0")
    second = build_summary_document(run_result, producer_version="1.0.0")

    assert first == second
    assert tuple(item.file_path for item in run_result.file_results) == original_file_order
    assert tuple(item.change_kind for item in run_result.diff_entries) == original_diff_order
    assert tuple(item.count for item in run_result.top_errors) == original_top_order


def test_producer_requires_non_empty_text() -> None:
    assert project_producer(name="gf-wordbench", version="1.0") == {
        "name": "gf-wordbench",
        "version": "1.0",
    }

    with pytest.raises(SummaryProjectionError, match="producer.name"):
        project_producer(name=" ", version="1.0")

    with pytest.raises(TypeError, match="producer.version"):
        project_producer(name="gf-wordbench", version=1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("legacy_mode", "canonical_mode"),
    (("file", "quick"), ("all", "diagnostic")),
)
def test_metadata_normalizes_documented_legacy_modes(
    tmp_path: Path,
    legacy_mode: str,
    canonical_mode: str,
) -> None:
    run_paths = _run_paths(tmp_path)
    run_config = _run_config(tmp_path, mode=legacy_mode)
    run_result = _namespace(
        run_config=run_config,
        run_paths=run_paths,
        started_at=datetime(
            2026,
            7,
            25,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        finished_at=datetime(
            2026,
            7,
            25,
            8,
            0,
            1,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        duration_ms=1_000,
        gf_version="3.12",
    )

    metadata = project_metadata(run_result)

    assert metadata["mode"] == canonical_mode
    assert metadata["started_at"] == "2026-07-25T12:00:00Z"
    assert metadata["finished_at"] == "2026-07-25T12:00:01Z"


def test_metadata_rejects_reversed_timestamps_and_escaping_target(
    tmp_path: Path,
) -> None:
    run_paths = _run_paths(tmp_path)
    run_config = _run_config(
        tmp_path,
        target=(tmp_path / "outside" / "Main.gf").resolve(),
    )
    run_result = _namespace(
        run_config=run_config,
        run_paths=run_paths,
        started_at=_TIMESTAMP,
        finished_at=_TIMESTAMP - timedelta(seconds=1),
        duration_ms=1,
        gf_version="3.12",
    )

    with pytest.raises(SummaryProjectionError, match="escapes the project root"):
        project_metadata(run_result)

    run_result.run_config = _run_config(tmp_path)
    with pytest.raises(SummaryProjectionError, match="must not precede"):
        project_metadata(run_result)


def test_totals_enforce_arithmetic_and_overall_status() -> None:
    totals = _totals()

    assert project_totals(totals, overall_status="FAIL")["files_fail"] == 1

    bad_seen = deepcopy(totals)
    bad_seen.files_seen = 3
    with pytest.raises(SummaryProjectionError, match="files_seen"):
        project_totals(bad_seen)

    bad_scenarios = deepcopy(totals)
    bad_scenarios.scenarios_ok = 0
    with pytest.raises(SummaryProjectionError, match="scenarios_seen"):
        project_totals(bad_scenarios)

    with pytest.raises(SummaryProjectionError, match="overall_status"):
        project_totals(totals, overall_status="OK")


def test_artifacts_are_run_relative_and_cannot_escape(tmp_path: Path) -> None:
    run_paths = _run_paths(tmp_path)

    projected = project_artifacts(run_paths)

    assert projected["summary_json"] == "summary.json"
    assert projected["compile_logs_dir"] == "raw/compile"
    assert projected["pgf_dir"] == "artifacts/pgf"

    run_paths.summary_json = (tmp_path / "outside" / "summary.json").resolve()
    with pytest.raises(SummaryProjectionError, match="escapes the run directory"):
        project_artifacts(run_paths)


def test_file_projection_normalizes_paths_and_digest(tmp_path: Path) -> None:
    run_paths = _run_paths(tmp_path)
    run_config = _run_config(tmp_path)
    result = _file_result(
        run_config,
        run_paths,
        relative_path="src/Zeta.gf",
        ok=False,
        blocked_by=(r"src\beta.gf", "src/Alpha.gf", "src/Alpha.gf"),
        digest=_SHA_B.upper(),
    )

    projected = project_file_result(
        result,
        run_config=run_config,
        run_paths=run_paths,
    )

    fingerprint = _json_object(projected["fingerprint"])
    compile_summary = _json_object(projected["compile_summary"])

    assert projected["file_path"] == "src/Zeta.gf"
    assert projected["blocked_by"] == ["src/Alpha.gf", "src/beta.gf"]
    assert fingerprint["hash"] == _SHA_B
    assert compile_summary["stdout_path"] == "raw/compile/Zeta.stdout.log"
    assert projected["scan_log_path"] == "raw/scan/Zeta.log"


def test_file_projection_requires_direct_flag_to_match_classification(
    tmp_path: Path,
) -> None:
    run_paths = _run_paths(tmp_path)
    run_config = _run_config(tmp_path)
    result = _file_result(
        run_config,
        run_paths,
        relative_path="src/Main.gf",
        ok=False,
    )
    result.is_direct = False

    with pytest.raises(SummaryProjectionError, match="must agree"):
        project_file_result(
            result,
            run_config=run_config,
            run_paths=run_paths,
        )


@pytest.mark.parametrize(
    ("algorithm", "digest", "message"),
    (
        ("sha1", _SHA_A, "use sha256"),
        ("sha256", "f" * 63, "full lowercase SHA-256"),
        ("sha256", "g" * 64, "full lowercase SHA-256"),
    ),
)
def test_fingerprint_rejects_noncanonical_hashes(
    algorithm: str,
    digest: str,
    message: str,
) -> None:
    with pytest.raises(SummaryProjectionError, match=message):
        project_fingerprint(_fingerprint(algorithm=algorithm, digest=digest))


def test_scenario_projection_preserves_order_and_path_bases(tmp_path: Path) -> None:
    run_paths = _run_paths(tmp_path)
    run_config = _run_config(tmp_path)
    scenario = _scenario_result(run_config, run_paths)
    scenario.sections = (
        _namespace(
            id="load",
            completed=True,
            message="loaded",
            begin_line=1,
            end_line=2,
        ),
        _namespace(section_id="parse", completed=False),
    )
    scenario.artifacts = (
        _namespace(path=run_paths.out_dir / "parse-smoke.out"),
        run_paths.raw_scenarios_dir / "parse-smoke.stdout.log",
    )

    projected = project_scenario_result(
        scenario,
        run_config=run_config,
        run_paths=run_paths,
    )

    assert projected["script_path"] == "scenarios/parse.gfs"
    assert projected["gold_path"] == "scenarios/parse.gold"
    assert projected["command"] == ["gf", "--run", "parse.gfs"]
    assert projected["sections"] == [
        {
            "id": "load",
            "completed": True,
            "message": "loaded",
            "begin_line": 1,
            "end_line": 2,
        },
        {"id": "parse", "completed": False},
    ]
    assert projected["artifacts"] == [
        "artifacts/out/parse-smoke.out",
        "raw/scenarios/parse-smoke.stdout.log",
    ]


def test_diff_projection_supports_nullable_statuses_required_by_schema() -> None:
    new_entry = _namespace(
        subject_kind="file",
        subject_id=r"src\New.gf",
        previous_status=None,
        current_status="OK",
        change_kind="new",
        message="New file",
    )
    removed_entry = _namespace(
        subject_kind="scenario",
        subject_id="legacy-scenario",
        previous_status="FAIL",
        current_status=None,
        change_kind="removed",
        message="Scenario removed",
    )

    assert project_diff_entry(new_entry) == {
        "subject_kind": "file",
        "subject_id": "src/New.gf",
        "previous_status": None,
        "current_status": "OK",
        "change_kind": "new",
        "message": "New file",
    }
    assert project_diff_entry(removed_entry)["current_status"] is None


def test_top_errors_use_count_then_case_insensitive_message_order(
    tmp_path: Path,
) -> None:
    run_result = _completed_run_result(tmp_path)
    run_result.top_errors = (
        _namespace(error_kind="TYPE", message="Alpha", count=2),
        _namespace(error_kind="OTHER", message="zeta", count=2),
        _namespace(error_kind="SYNTAX", message="beta", count=3),
    )

    document = build_summary_document(run_result, producer_version="1.0.0")

    top_errors = _json_object_array(document["top_errors"])
    assert [item["message"] for item in top_errors] == [
        "beta",
        "Alpha",
        "zeta",
    ]
    assert validate_summary_v1(document) == ()


def test_top_error_requires_positive_non_boolean_count() -> None:
    assert project_top_error(_namespace(error_kind="TYPE", message="Type mismatch", count=2)) == {
        "error_kind": "TYPE",
        "message": "Type mismatch",
        "count": 2,
    }

    with pytest.raises(SummaryProjectionError, match="positive"):
        project_top_error(_namespace(error_kind="TYPE", message="Type mismatch", count=0))

    with pytest.raises(TypeError, match="must be int"):
        project_top_error(_namespace(error_kind="TYPE", message="Type mismatch", count=True))


def test_projection_invariants_reject_missing_types_and_order() -> None:
    base: dict[str, JsonValue] = {
        "schema_id": SUMMARY_SCHEMA_ID,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "metadata": {},
        "totals": {},
        "artifacts": {},
        "file_results": [],
        "scenario_results": [],
        "diff_entries": [],
        "top_errors": [],
    }
    validate_projection_invariants(base)

    missing: dict[str, JsonValue] = dict(base)
    missing.pop("totals")
    with pytest.raises(SummaryProjectionError, match="missing required fields"):
        validate_projection_invariants(missing)

    wrong_type: dict[str, JsonValue] = {**base, "file_results": {}}
    with pytest.raises(SummaryProjectionError, match="must be an array"):
        validate_projection_invariants(wrong_type)

    unordered_files: dict[str, JsonValue] = {
        **base,
        "file_results": [{"file_path": "z.gf"}, {"file_path": "A.gf"}],
    }
    with pytest.raises(SummaryProjectionError, match="file_results"):
        validate_projection_invariants(unordered_files)

    unordered_errors: dict[str, JsonValue] = {
        **base,
        "top_errors": [
            {"error_kind": "TYPE", "message": "minor", "count": 1},
            {"error_kind": "TYPE", "message": "major", "count": 2},
        ],
    }
    with pytest.raises(SummaryProjectionError, match="top_errors"):
        validate_projection_invariants(unordered_errors)
