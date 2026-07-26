"""Schema tests for the canonical GF Wordbench run summary document."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import cast

import pytest

from gf_wordbench.reporting.schemas.summary_v1 import (
    ArtifactsV1,
    DiffEntryV1,
    FileResultV1,
    MetadataV1,
    ProducerV1,
    SUMMARY_JSON_FILENAME,
    SUMMARY_PRODUCER_NAME,
    SUMMARY_SCHEMA_ID,
    SUMMARY_SCHEMA_VERSION,
    SummaryV1,
    SummaryV1ValidationError,
    TopErrorV1,
    TotalsV1,
    assert_summary_v1_json_safe,
    canonicalize_summary_v1,
    is_summary_v1,
    is_supported_schema_version,
    new_summary_v1,
    parse_schema_version,
    require_summary_v1,
    schema_identity,
    validate_summary_v1,
)

pytestmark = pytest.mark.schema

_TIMESTAMP = "2026-07-25T12:00:00Z"
_SHA_A = "a" * 64
_SHA_B = "b" * 64


def _metadata() -> MetadataV1:
    return {
        "run_id": "20260725_120000",
        "run_dir": "C:/work/gf-wordbench/runs/20260725_120000",
        "started_at": _TIMESTAMP,
        "finished_at": _TIMESTAMP,
        "duration_ms": 0,
        "gf_version": "3.12",
        "mode": "diagnostic",
        "target_file": None,
        "project_id": "test-language",
        "project_name": "Test Language",
        "project_root": "C:/work/gf-wordbench/project",
        "rgl_root": "C:/tools/gf-rgl",
        "gf_executable": "C:/tools/gf/bin/gf.exe",
        "output_root": "C:/work/gf-wordbench/runs",
        "source_directory": "src",
        "source_glob": "*.gf",
        "gf_path": [
            "C:/work/gf-wordbench/project/src",
            "C:/tools/gf-rgl",
        ],
        "timeout_sec": 60,
        "max_files": 0,
        "skip_version_probe": False,
        "no_compile": False,
        "emit_cpu_stats": False,
        "keep_ok_details": False,
        "diff_previous": True,
    }


def _totals(
    *,
    files_seen: int = 0,
    files_ok: int = 0,
    files_fail: int = 0,
    direct_fail: int = 0,
) -> TotalsV1:
    files_included = files_ok + files_fail
    return {
        "files_seen": files_seen,
        "files_included": files_included,
        "files_excluded": files_seen - files_included,
        "files_ok": files_ok,
        "files_fail": files_fail,
        "files_error": 0,
        "files_skipped": 0,
        "direct_fail": direct_fail,
        "downstream_fail": 0,
        "ambiguous_fail": 0,
        "excluded_noise": 0,
        "scenarios_seen": 0,
        "scenarios_ok": 0,
        "scenarios_fail": 0,
        "scenarios_error": 0,
        "scenarios_skipped": 0,
        "required_scenario_fail": 0,
        "overall_status": "FAIL" if files_fail else "OK",
    }


def _artifacts() -> ArtifactsV1:
    return {
        "summary_json": SUMMARY_JSON_FILENAME,
        "summary_markdown": "summary.md",
        "ai_ready": "AI_READY.md",
        "top_errors": "top_errors.txt",
        "manifest": "manifest.json",
        "master_log": "raw/master.log",
        "all_scan_logs": "raw/all_scan_logs.log",
        "all_logs": "raw/all_logs.log",
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


def _producer() -> ProducerV1:
    return {
        "name": SUMMARY_PRODUCER_NAME,
        "version": "1.0.0",
    }


def _file_result(
    file_path: str,
    *,
    status: str,
    diagnostic_class: str,
    is_direct: bool,
    digest: str,
) -> FileResultV1:
    return cast(
        FileResultV1,
        {
            "file_path": file_path,
            "module_name": Path(file_path).stem,
            "status": status,
            "diagnostic_class": diagnostic_class,
            "is_direct": is_direct,
            "blocked_by": [],
            "scan_counts": {
                "single_slash_eq": 0,
                "double_slash_dash": 0,
                "runtime_str_match": 0,
                "untyped_case_str_pat": 0,
                "untyped_table_str_pat": 0,
                "trailing_spaces": 0,
            },
            "fingerprint": {
                "size_bytes": 1,
                "hash_algorithm": "sha256",
                "hash": digest,
                "last_modified_utc": _TIMESTAMP,
            },
            "compile_summary": {
                "exit_code": 0 if status == "OK" else 1,
                "timed_out": False,
                "duration_ms": 1,
                "error_kind": "OK" if status == "OK" else "TYPE",
                "first_error": "" if status == "OK" else "Type mismatch",
                "error_detail": "",
                "stdout_path": f"raw/compile/{Path(file_path).stem}.stdout.log",
                "stderr_path": f"raw/compile/{Path(file_path).stem}.stderr.log",
            },
            "scan_log_path": f"raw/scan/{Path(file_path).stem}.log",
        },
    )


def _valid_summary() -> SummaryV1:
    return new_summary_v1(
        metadata=_metadata(),
        totals=_totals(),
        artifacts=_artifacts(),
        producer=_producer(),
    )


def _issue_codes(document: object, *, strict: bool = True) -> set[str]:
    return {
        issue.code
        for issue in validate_summary_v1(
            document,
            strict=strict,
        )
    }


def test_schema_identity_and_version_support_are_stable() -> None:
    assert schema_identity() == (SUMMARY_SCHEMA_ID, SUMMARY_SCHEMA_VERSION)
    assert parse_schema_version(SUMMARY_SCHEMA_VERSION) == (1, 0)
    assert is_supported_schema_version("1.0") is True
    assert is_supported_schema_version("1.99") is True
    assert is_supported_schema_version("2.0") is False
    assert is_supported_schema_version("1") is False
    assert is_supported_schema_version(1) is False

    with pytest.raises(ValueError, match="MAJOR.MINOR"):
        parse_schema_version("v1")


def test_minimal_summary_is_valid_json_safe_and_round_trippable() -> None:
    document = _valid_summary()

    assert validate_summary_v1(document) == ()
    assert require_summary_v1(document) is document
    assert is_summary_v1(document) is True
    assert_summary_v1_json_safe(document)

    encoded = json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
    )
    decoded = json.loads(encoded)

    assert decoded == document
    assert decoded["schema_id"] == SUMMARY_SCHEMA_ID
    assert decoded["schema_version"] == SUMMARY_SCHEMA_VERSION
    assert decoded["producer"] == {
        "name": SUMMARY_PRODUCER_NAME,
        "version": "1.0.0",
    }


def test_constructor_deep_copies_all_caller_owned_values() -> None:
    metadata = _metadata()
    totals = _totals()
    artifacts = _artifacts()
    producer = _producer()

    document = new_summary_v1(
        metadata=metadata,
        totals=totals,
        artifacts=artifacts,
        producer=producer,
    )

    metadata["project_name"] = "Mutated"
    metadata["gf_path"].append("C:/unexpected")
    totals["files_seen"] = 99
    artifacts["summary_json"] = "changed.json"
    producer["version"] = "999"

    assert document["metadata"]["project_name"] == "Test Language"
    assert document["metadata"]["gf_path"] == [
        "C:/work/gf-wordbench/project/src",
        "C:/tools/gf-rgl",
    ]
    assert document["totals"]["files_seen"] == 0
    assert document["artifacts"]["summary_json"] == SUMMARY_JSON_FILENAME
    assert document["producer"]["version"] == "1.0.0"


def test_strict_validation_rejects_unknown_fields() -> None:
    document = deepcopy(_valid_summary())
    document["future_extension"] = {"enabled": True}  # type: ignore[typeddict-unknown-key]

    assert "unknown_field" in _issue_codes(document)
    assert validate_summary_v1(document, strict=False) == ()

    with pytest.raises(SummaryV1ValidationError) as captured:
        require_summary_v1(document)

    assert any(
        issue.path == "$.future_extension" and issue.code == "unknown_field"
        for issue in captured.value.issues
    )


@pytest.mark.parametrize(
    ("version", "expected_code"),
    [
        ("2.0", "unsupported_major"),
        ("1.1", "noncanonical_minor"),
        ("1", "invalid_version"),
    ],
)
def test_schema_version_failures_are_reported(
    version: str,
    expected_code: str,
) -> None:
    document = deepcopy(_valid_summary())
    document["schema_version"] = version

    assert expected_code in _issue_codes(document)
    assert is_summary_v1(document) is False


def test_canonicalization_orders_collections_without_mutating_input() -> None:
    failed = _file_result(
        "src/Zeta.gf",
        status="FAIL",
        diagnostic_class="direct",
        is_direct=True,
        digest=_SHA_B,
    )
    passed = _file_result(
        "src/alpha.gf",
        status="OK",
        diagnostic_class="ok",
        is_direct=False,
        digest=_SHA_A,
    )
    diff_entries = cast(
        list[DiffEntryV1],
        [
            {
                "subject_kind": "file",
                "subject_id": "src/alpha.gf",
                "previous_status": "OK",
                "current_status": "OK",
                "change_kind": "unchanged",
                "message": "",
            },
            {
                "subject_kind": "file",
                "subject_id": "src/Zeta.gf",
                "previous_status": "OK",
                "current_status": "FAIL",
                "change_kind": "regressed",
                "message": "Compilation regressed.",
            },
        ],
    )
    top_errors = cast(
        list[TopErrorV1],
        [
            {
                "error_kind": "TYPE",
                "message": "Secondary issue",
                "count": 1,
            },
            {
                "error_kind": "TYPE",
                "message": "Primary issue",
                "count": 3,
            },
        ],
    )

    document = new_summary_v1(
        metadata=_metadata(),
        totals=_totals(
            files_seen=2,
            files_ok=1,
            files_fail=1,
            direct_fail=1,
        ),
        artifacts=_artifacts(),
        file_results=[failed, passed],
        diff_entries=diff_entries,
        top_errors=top_errors,
        producer=_producer(),
        canonicalize=False,
        validate=False,
    )
    original = deepcopy(document)

    assert "noncanonical_order" in _issue_codes(document)

    canonical = canonicalize_summary_v1(document)

    assert document == original
    assert [item["file_path"] for item in canonical["file_results"]] == [
        "src/alpha.gf",
        "src/Zeta.gf",
    ]
    assert [item["change_kind"] for item in canonical["diff_entries"]] == [
        "regressed",
        "unchanged",
    ]
    assert [item["count"] for item in canonical["top_errors"]] == [3, 1]
    assert validate_summary_v1(canonical) == ()


def test_cross_result_counts_are_enforced() -> None:
    document = new_summary_v1(
        metadata=_metadata(),
        totals=_totals(
            files_seen=1,
            files_ok=1,
        ),
        artifacts=_artifacts(),
        file_results=[
            _file_result(
                "src/Main.gf",
                status="OK",
                diagnostic_class="ok",
                is_direct=False,
                digest=_SHA_A,
            )
        ],
        producer=_producer(),
    )
    broken = deepcopy(document)
    broken["totals"]["files_ok"] = 0
    broken["totals"]["files_fail"] = 1
    broken["totals"]["overall_status"] = "FAIL"

    codes = _issue_codes(broken)

    assert "result_count_mismatch" in codes
    with pytest.raises(SummaryV1ValidationError):
        require_summary_v1(broken)


def test_paths_and_timestamps_use_canonical_persisted_forms() -> None:
    document = deepcopy(_valid_summary())
    document["metadata"]["finished_at"] = "2026-07-25T07:59:59-04:00"
    document["metadata"]["target_file"] = "../outside.gf"
    document["artifacts"]["summary_json"] = r"raw\summary.json"

    issues = validate_summary_v1(document)
    findings = {(issue.path, issue.code) for issue in issues}

    assert ("$.metadata.finished_at", "timestamp_utc") in findings
    assert ("$.metadata.target_file", "path_segment") in findings
    assert ("$.artifacts.summary_json", "separator") in findings
    assert (
        "$.artifacts.summary_json",
        "noncanonical_summary_path",
    ) in findings


def test_json_safety_rejects_non_json_values_and_non_finite_numbers() -> None:
    with pytest.raises(TypeError, match="non-JSON value"):
        assert_summary_v1_json_safe({"path": Path("summary.json")})

    with pytest.raises(ValueError, match="non-finite"):
        assert_summary_v1_json_safe({"duration": float("nan")})

    with pytest.raises(TypeError, match="non-string key"):
        assert_summary_v1_json_safe({1: "invalid"})
