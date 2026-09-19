"""Unit tests for scenario-owned artifact paths and integrity records."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from gf_wordbench.kernel.errors import (
    ArtifactError,
    EvidenceIOError,
    PathSecurityError,
)
from gf_wordbench.kernel.ids import ScenarioId
from gf_wordbench.validation.scenarios.artifacts import (
    GOLD_DIFF_SUFFIX,
    HASH_SUFFIX_LENGTH,
    MAX_GENERATED_BASENAME_LENGTH,
    MAX_SAFE_KEY_LENGTH,
    NORMALIZED_OUTPUT_SUFFIX,
    STDERR_SUFFIX,
    STDOUT_SUFFIX,
    GoldDiffMetadata,
    ScenarioArtifactKind,
    ScenarioArtifactPaths,
    ScenarioArtifactRecord,
    collect_existing_scenario_artifacts,
    resolve_scenario_artifact_paths,
    run_relative_artifact_path,
    scenario_safe_key,
    verify_generated_scenario_artifact,
    verify_scenario_artifact,
    write_gold_diff,
    write_normalized_output,
    write_scenario_stderr,
    write_scenario_stdout,
)


def _artifact_paths(
    tmp_path: Path,
    scenario_id: str = "parse-basic",
) -> ScenarioArtifactPaths:
    run_directory = tmp_path / "run_20260725_120000"
    raw_directory = run_directory / "raw" / "scenarios"
    generated_directory = run_directory / "artifacts" / "out"
    raw_directory.mkdir(parents=True)
    generated_directory.mkdir(parents=True)
    return resolve_scenario_artifact_paths(
        ScenarioId(scenario_id),
        run_directory=run_directory,
        raw_scenarios_directory=raw_directory,
        generated_output_directory=generated_directory,
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_artifact_kind_values_are_stable_machine_tokens() -> None:
    assert tuple(kind.value for kind in ScenarioArtifactKind) == (
        "scenario_stdout",
        "scenario_stderr",
        "scenario_normalized_output",
        "scenario_gold_diff",
        "scenario_generated_output",
    )


def test_safe_key_preserves_normal_scenario_id() -> None:
    assert scenario_safe_key("parse-basic") == "parse-basic"


def test_safe_key_hashes_windows_reserved_name_deterministically() -> None:
    first = scenario_safe_key("con")
    second = scenario_safe_key(ScenarioId("con"))

    assert first == second
    assert first.startswith("scenario-con--")
    assert len(first.rsplit("--", 1)[1]) == HASH_SUFFIX_LENGTH
    assert len(first) <= MAX_SAFE_KEY_LENGTH


def test_safe_key_bounds_long_scenario_id_and_keeps_hash_suffix() -> None:
    scenario_id = "scenario-" + ("segment" * 40)
    expected_hash = hashlib.sha256(scenario_id.encode("ascii")).hexdigest()[:HASH_SUFFIX_LENGTH]

    key = scenario_safe_key(scenario_id)

    assert len(key) == MAX_SAFE_KEY_LENGTH
    assert key.endswith(f"--{expected_hash}")
    assert "/" not in key
    assert "\\" not in key


def test_safe_key_rejects_noncanonical_scenario_id() -> None:
    with pytest.raises(ValueError, match="lowercase kebab case"):
        scenario_safe_key("Parse Basic")


def test_resolve_paths_uses_canonical_owned_names(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)

    assert paths.scenario_id == "parse-basic"
    assert paths.safe_key == "parse-basic"
    assert paths.stdout_path == (paths.raw_scenarios_directory / f"parse-basic{STDOUT_SUFFIX}")
    assert paths.stderr_path == (paths.raw_scenarios_directory / f"parse-basic{STDERR_SUFFIX}")
    assert paths.normalized_output_path == (
        paths.raw_scenarios_directory / f"parse-basic{NORMALIZED_OUTPUT_SUFFIX}"
    )
    assert paths.gold_diff_path == (
        paths.raw_scenarios_directory / f"parse-basic{GOLD_DIFF_SUFFIX}"
    )
    assert paths.run_relative(paths.stdout_path) == ("raw/scenarios/parse-basic.stdout.txt")


def test_resolve_paths_requires_existing_owned_directories(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    run_directory.mkdir()

    with pytest.raises(EvidenceIOError, match="unavailable"):
        resolve_scenario_artifact_paths(
            "parse-basic",
            run_directory=run_directory,
            raw_scenarios_directory=run_directory / "raw" / "scenarios",
            generated_output_directory=run_directory / "artifacts" / "out",
        )


def test_resolve_paths_rejects_directory_outside_run(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    raw_directory = tmp_path / "outside" / "raw"
    generated_directory = run_directory / "artifacts" / "out"
    run_directory.mkdir()
    raw_directory.mkdir(parents=True)
    generated_directory.mkdir(parents=True)

    with pytest.raises(PathSecurityError, match="escapes") as captured:
        resolve_scenario_artifact_paths(
            "parse-basic",
            run_directory=run_directory,
            raw_scenarios_directory=raw_directory,
            generated_output_directory=generated_directory,
        )

    assert captured.value.code == "GF-WB-PATH-001"
    assert captured.value.stage == "scenarios"


def test_paths_model_rejects_noncanonical_file_name(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(ValueError, match="canonical scenario artifact name"):
        ScenarioArtifactPaths(
            scenario_id=paths.scenario_id,
            safe_key=paths.safe_key,
            run_directory=paths.run_directory,
            raw_scenarios_directory=paths.raw_scenarios_directory,
            generated_output_directory=paths.generated_output_directory,
            stdout_path=paths.raw_scenarios_directory / "wrong.stdout.txt",
            stderr_path=paths.stderr_path,
            normalized_output_path=paths.normalized_output_path,
            gold_diff_path=paths.gold_diff_path,
        )


def test_path_for_rejects_generated_output_without_explicit_path(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(ValueError, match="explicit existing path"):
        paths.path_for(ScenarioArtifactKind.GENERATED_OUTPUT)


def test_write_raw_streams_preserves_exact_bytes_and_integrity(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    stdout = b"line one\r\nline two\x00\xff"
    stderr = b"warning\n"

    stdout_record = write_scenario_stdout(paths, stdout)
    stderr_record = write_scenario_stderr(paths, memoryview(stderr))

    assert paths.stdout_path.read_bytes() == stdout
    assert paths.stderr_path.read_bytes() == stderr
    assert stdout_record == ScenarioArtifactRecord(
        scenario_id=ScenarioId("parse-basic"),
        kind=ScenarioArtifactKind.STDOUT,
        path=paths.stdout_path,
        run_relative_path="raw/scenarios/parse-basic.stdout.txt",
        size_bytes=len(stdout),
        sha256=_sha256(stdout),
        media_type="text/plain; charset=utf-8",
    )
    assert stderr_record.size_bytes == len(stderr)
    assert stderr_record.sha256 == _sha256(stderr)


def test_raw_stream_may_be_empty_but_is_immutable(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)

    record = write_scenario_stdout(paths, b"")

    assert record.size_bytes == 0
    with pytest.raises(ArtifactError, match="immutable") as captured:
        write_scenario_stdout(paths, b"replacement")
    assert captured.value.operation == "publish-artifact"


def test_raw_stream_requires_bytes_like_data(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(TypeError, match="bytes-like"):
        write_scenario_stderr(paths, "not bytes")  # type: ignore[arg-type]


def test_write_normalized_output_uses_lf_and_links_raw_source(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    write_scenario_stdout(paths, b"RAW\r\n")

    record = write_normalized_output(
        paths,
        "normalized\noutput\n",
        normalization_version="scenario-default-v1",
    )

    assert paths.normalized_output_path.read_bytes() == (b"normalized\noutput\n")
    assert record.kind is ScenarioArtifactKind.NORMALIZED_OUTPUT
    assert record.source_run_relative_path == ("raw/scenarios/parse-basic.stdout.txt")
    assert record.normalization_version == "scenario-default-v1"


def test_normalized_output_rejects_cr_nul_and_invalid_source_kind(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(ValueError, match="canonical LF"):
        write_normalized_output(
            paths,
            "line\r\n",
            normalization_version="v1",
        )
    with pytest.raises(ValueError, match="NUL"):
        write_normalized_output(
            paths,
            "line\x00",
            normalization_version="v1",
        )
    with pytest.raises(ValueError, match="stdout or raw stderr"):
        write_normalized_output(
            paths,
            "line\n",
            normalization_version="v1",
            source_kind=ScenarioArtifactKind.GOLD_DIFF,
        )


def test_write_gold_diff_publishes_required_metadata_and_canonical_lf(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    write_normalized_output(
        paths,
        "actual\n",
        normalization_version="scenario-default-v1",
    )
    metadata = GoldDiffMetadata(
        scenario_id=ScenarioId("parse-basic"),
        gold_path="scenarios/gold/parse-basic.gold",
        actual_normalized_output_path=paths.run_relative(paths.normalized_output_path),
        comparison_result="mismatch",
        normalization_version="scenario-default-v1",
    )

    record = write_gold_diff(
        paths,
        metadata,
        "--- expected\r\n+++ actual\r\n@@\r\n-old\r\n+new\r\n",
    )

    assert paths.gold_diff_path.read_text(encoding="utf-8") == (
        "scenario_id: parse-basic\n"
        "gold_path: scenarios/gold/parse-basic.gold\n"
        "actual_normalized_output_path: "
        "raw/scenarios/parse-basic.out\n"
        "comparison_result: mismatch\n"
        "normalization_version: scenario-default-v1\n"
        "---\n"
        "--- expected\n"
        "+++ actual\n"
        "@@\n"
        "-old\n"
        "+new\n"
    )
    assert record.kind is ScenarioArtifactKind.GOLD_DIFF
    assert record.source_run_relative_path == ("raw/scenarios/parse-basic.out")
    assert record.normalization_version == "scenario-default-v1"


def test_gold_diff_rejects_foreign_metadata(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    metadata = GoldDiffMetadata(
        scenario_id=ScenarioId("other-scenario"),
        gold_path="scenarios/gold/other-scenario.gold",
        actual_normalized_output_path=("raw/scenarios/other-scenario.out"),
        comparison_result="mismatch",
        normalization_version="v1",
    )

    with pytest.raises(ValueError, match="scenario_id does not match"):
        write_gold_diff(paths, metadata, "diff\n")


def test_verify_scenario_artifact_detects_empty_required_diff(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    paths.gold_diff_path.write_bytes(b"")

    with pytest.raises(ArtifactError, match="empty") as captured:
        verify_scenario_artifact(
            paths,
            kind=ScenarioArtifactKind.GOLD_DIFF,
        )

    assert captured.value.code == "GF-WB-SCENARIO-001"
    assert captured.value.evidence_paths == ("raw/scenarios/parse-basic.gold.diff",)


def test_verify_generated_artifact_records_exact_bytes_and_media_type(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    artifact = paths.generated_output_directory / "parse-tree.json"
    payload = b'{"tree":"Parse"}\n'
    artifact.write_bytes(payload)

    record = verify_generated_scenario_artifact(
        paths,
        artifact,
        source_run_relative_path="raw/scenarios/parse-basic.out",
        media_type="application/json",
    )

    assert record.kind is ScenarioArtifactKind.GENERATED_OUTPUT
    assert record.run_relative_path == "artifacts/out/parse-tree.json"
    assert record.size_bytes == len(payload)
    assert record.sha256 == _sha256(payload)
    assert record.media_type == "application/json"
    assert record.source_run_relative_path == ("raw/scenarios/parse-basic.out")


def test_verify_generated_artifact_rejects_escape_empty_and_long_name(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")

    with pytest.raises(PathSecurityError, match="escapes"):
        verify_generated_scenario_artifact(paths, outside)

    empty = paths.generated_output_directory / "empty.bin"
    empty.write_bytes(b"")
    with pytest.raises(ArtifactError, match="empty"):
        verify_generated_scenario_artifact(paths, empty)

    long_name = "a" * (MAX_GENERATED_BASENAME_LENGTH + 1)
    too_long = paths.generated_output_directory / long_name
    too_long.write_bytes(b"x")
    with pytest.raises(ArtifactError, match="basename is too long"):
        verify_generated_scenario_artifact(paths, too_long)


def test_collect_existing_artifacts_is_complete_and_deterministic(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    write_scenario_stdout(paths, b"stdout")
    write_scenario_stderr(paths, b"stderr")
    write_normalized_output(
        paths,
        "normalized\n",
        normalization_version="v1",
    )
    metadata = GoldDiffMetadata(
        scenario_id=paths.scenario_id,
        gold_path="scenarios/gold/parse-basic.gold",
        actual_normalized_output_path=paths.run_relative(paths.normalized_output_path),
        comparison_result="mismatch",
        normalization_version="v1",
    )
    write_gold_diff(paths, metadata, "-expected\n+actual\n")
    generated_b = paths.generated_output_directory / "B.bin"
    generated_a = paths.generated_output_directory / "a.bin"
    generated_b.write_bytes(b"B")
    generated_a.write_bytes(b"A")

    records = collect_existing_scenario_artifacts(
        paths,
        required_kinds=(
            ScenarioArtifactKind.STDOUT,
            ScenarioArtifactKind.STDERR,
            ScenarioArtifactKind.NORMALIZED_OUTPUT,
            ScenarioArtifactKind.GOLD_DIFF,
        ),
        generated_artifacts=(generated_b, generated_a),
    )

    assert tuple(record.kind for record in records) == (
        ScenarioArtifactKind.STDOUT,
        ScenarioArtifactKind.STDERR,
        ScenarioArtifactKind.NORMALIZED_OUTPUT,
        ScenarioArtifactKind.GOLD_DIFF,
        ScenarioArtifactKind.GENERATED_OUTPUT,
        ScenarioArtifactKind.GENERATED_OUTPUT,
    )
    assert tuple(record.run_relative_path for record in records[-2:]) == (
        "artifacts/out/a.bin",
        "artifacts/out/B.bin",
    )


def test_collect_existing_artifacts_reports_missing_required_kind(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(ArtifactError, match="missing") as captured:
        collect_existing_scenario_artifacts(
            paths,
            required_kinds=(ScenarioArtifactKind.STDOUT,),
        )

    assert captured.value.operation == "collect-artifacts"
    assert captured.value.evidence_paths == ("raw/scenarios/parse-basic.stdout.txt",)


def test_collect_rejects_generated_kind_in_required_kinds(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)

    with pytest.raises(ValueError, match="supplied explicitly"):
        collect_existing_scenario_artifacts(
            paths,
            required_kinds=(ScenarioArtifactKind.GENERATED_OUTPUT,),
        )


def test_run_relative_artifact_path_supports_future_owned_output(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    future = paths.generated_output_directory / "future" / "result.bin"

    assert (
        run_relative_artifact_path(
            future,
            run_directory=paths.run_directory,
        )
        == "artifacts/out/future/result.bin"
    )


def test_run_relative_artifact_path_rejects_run_root_and_escape(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(PathSecurityError, match="escapes"):
        run_relative_artifact_path(
            paths.run_directory,
            run_directory=paths.run_directory,
        )
    with pytest.raises(PathSecurityError, match="escapes"):
        run_relative_artifact_path(
            outside,
            run_directory=paths.run_directory,
        )


def test_artifact_record_rejects_nonportable_relative_path(
    tmp_path: Path,
) -> None:
    absolute = (tmp_path / "artifact.bin").resolve()

    with pytest.raises(ValueError, match="portable relative path"):
        ScenarioArtifactRecord(
            scenario_id=ScenarioId("parse-basic"),
            kind=ScenarioArtifactKind.GENERATED_OUTPUT,
            path=absolute,
            run_relative_path="artifacts\\out\\artifact.bin",
            size_bytes=1,
            sha256="0" * 64,
            media_type="application/octet-stream",
        )
