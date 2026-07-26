from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.kernel.errors import SchemaValidationError, StateWriteError
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.state import repository as state_repository
from gf_wordbench.state.models import AppState, StateDiagnosticCode
from gf_wordbench.state.repository import (
    CANONICAL_STATE_FILENAME,
    LEGACY_STATE_FILENAME,
    StateRepository,
    load_app_state,
    save_app_state,
)
from gf_wordbench.state.schema import (
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
    DEFAULT_DIFF_PREVIOUS,
    DEFAULT_EMIT_CPU_STATS,
    DEFAULT_KEEP_OK_DETAILS,
    DEFAULT_MAX_FILES,
    DEFAULT_MODE,
    DEFAULT_NO_COMPILE,
    DEFAULT_SKIP_VERSION_PROBE,
    DEFAULT_TIMEOUT_SEC,
    default_app_state,
    default_app_state_document,
    parse_app_state,
    serialize_app_state,
)
from gf_wordbench.version import __version__

pytestmark = pytest.mark.schema


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _custom_state() -> AppState:
    state = default_app_state()
    return replace(
        state,
        environment=replace(
            state.environment,
            project_root="C:/work/project",
            rgl_root="C:/gf-rgl",
            gf_executable="C:/gf/bin/gf.exe",
            output_root="C:/work/output",
        ),
        selection=replace(
            state.selection,
            mode=ValidationMode.CHECKPOINT,
            target_file="src/Main.gf",
            timeout_sec=91,
            max_files=17,
            keep_ok_details=True,
            diff_previous=False,
            skip_version_probe=True,
            no_compile=True,
            emit_cpu_stats=True,
        ),
        last_run=replace(
            state.last_run,
            run_dir="runs/run_20260725_144207",
            summary_path="runs/run_20260725_144207/summary.json",
            status_message="validation completed",
        ),
    )


def test_default_state_matches_locked_canonical_defaults() -> None:
    state = default_app_state()

    assert state.schema_id == APP_STATE_SCHEMA_ID
    assert state.schema_version == APP_STATE_SCHEMA_VERSION
    assert state.producer is None
    assert state.environment.project_root is None
    assert state.environment.rgl_root is None
    assert state.environment.gf_executable is None
    assert state.environment.output_root is None
    assert state.selection.mode is DEFAULT_MODE
    assert state.selection.target_file == ""
    assert state.selection.timeout_sec == DEFAULT_TIMEOUT_SEC
    assert state.selection.max_files == DEFAULT_MAX_FILES
    assert state.selection.keep_ok_details is DEFAULT_KEEP_OK_DETAILS
    assert state.selection.diff_previous is DEFAULT_DIFF_PREVIOUS
    assert state.selection.skip_version_probe is DEFAULT_SKIP_VERSION_PROBE
    assert state.selection.no_compile is DEFAULT_NO_COMPILE
    assert state.selection.emit_cpu_stats is DEFAULT_EMIT_CPU_STATS
    assert state.last_run.run_dir is None
    assert state.last_run.summary_path is None
    assert state.last_run.status_message == ""


def test_default_document_contains_only_persisted_state_groups() -> None:
    document = default_app_state_document()

    assert tuple(document) == (
        "schema_id",
        "schema_version",
        "environment",
        "selection",
        "last_run",
    )
    assert "producer" not in document
    assert set(document["environment"]) == {
        "project_root",
        "rgl_root",
        "gf_executable",
        "output_root",
    }
    assert set(document["selection"]) == {
        "mode",
        "target_file",
        "timeout_sec",
        "max_files",
        "keep_ok_details",
        "diff_previous",
        "skip_version_probe",
        "no_compile",
        "emit_cpu_stats",
    }
    assert set(document["last_run"]) == {
        "run_dir",
        "summary_path",
        "status_message",
    }


def test_tolerant_parser_recovers_invalid_convenience_values() -> None:
    document: dict[str, Any] = json.loads(
        json.dumps(default_app_state_document())
    )
    document["unknown_optional_root"] = "ignored"
    selection = document["selection"]
    assert isinstance(selection, dict)
    selection["mode"] = "unsupported"
    selection["timeout_sec"] = 0
    selection["max_files"] = -1
    selection["keep_ok_details"] = "yes"
    del selection["diff_previous"]

    state, warnings = parse_app_state(document)

    assert state.selection.mode is ValidationMode.DIAGNOSTIC
    assert state.selection.timeout_sec == DEFAULT_TIMEOUT_SEC
    assert state.selection.max_files == DEFAULT_MAX_FILES
    assert state.selection.keep_ok_details is DEFAULT_KEEP_OK_DETAILS
    assert state.selection.diff_previous is DEFAULT_DIFF_PREVIOUS
    assert any("$.selection.mode" in warning for warning in warnings)
    assert any("$.selection.timeout_sec" in warning for warning in warnings)
    assert any("$.selection.max_files" in warning for warning in warnings)
    assert any("$.selection.keep_ok_details" in warning for warning in warnings)
    assert any("$.selection.diff_previous" in warning for warning in warnings)


def test_serializer_requires_and_emits_canonical_producer() -> None:
    state = default_app_state()

    with pytest.raises(SchemaValidationError):
        serialize_app_state(state)

    document = serialize_app_state(state, producer_version="9.8.7")

    assert document["producer"] == {
        "name": "gf-wordbench",
        "version": "9.8.7",
    }
    assert set(document) == {
        "schema_id",
        "schema_version",
        "producer",
        "environment",
        "selection",
        "last_run",
    }


def test_missing_state_returns_defaults_and_structured_diagnostic(
    tmp_path: Path,
) -> None:
    repository = StateRepository(tmp_path)

    result = repository.load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.source_path == tmp_path / CANONICAL_STATE_FILENAME
    assert result.migrated is False
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        StateDiagnosticCode.MISSING,
    )
    assert not result.source_path.exists()


def test_save_and_load_round_trip_canonical_typed_state(tmp_path: Path) -> None:
    state = _custom_state()

    destination = save_app_state(state, tmp_path)
    loaded = load_app_state(tmp_path)
    document = _read_json(destination)

    assert destination == tmp_path / CANONICAL_STATE_FILENAME
    assert document["schema_id"] == APP_STATE_SCHEMA_ID
    assert document["schema_version"] == APP_STATE_SCHEMA_VERSION
    assert document["producer"] == {
        "name": "gf-wordbench",
        "version": __version__,
    }
    assert document["selection"]["mode"] == "checkpoint"
    assert document["selection"]["timeout_sec"] == 91
    assert loaded == replace(
        state,
        producer=ProducerInfo(name="gf-wordbench", version=__version__),
    )


def test_malformed_state_falls_back_and_can_be_quarantined(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    malformed = b'{"schema_id": "gf-wordbench.app-state",'
    state_path.write_bytes(malformed)

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.migrated is False
    assert result.diagnostics[0].code is StateDiagnosticCode.MALFORMED
    assert any(
        diagnostic.code is StateDiagnosticCode.QUARANTINED
        for diagnostic in result.diagnostics
    )
    assert state_path.read_bytes() == malformed
    quarantines = tuple(
        tmp_path.glob(".gf_wordbench_state.invalid-*.json")
    )
    assert len(quarantines) == 1
    assert quarantines[0].read_bytes() == malformed


def test_future_major_fails_closed_without_rewriting_source(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document: dict[str, Any] = json.loads(
        json.dumps(default_app_state_document())
    )
    document["schema_version"] = "2.0"
    original = json.dumps(document, separators=(",", ":"))
    state_path.write_text(original, encoding="utf-8")

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.diagnostics[0].code is StateDiagnosticCode.VERSION_UNSUPPORTED
    assert state_path.read_text(encoding="utf-8") == original
    assert not tuple(tmp_path.glob(".gf_wordbench_state.invalid-*.json"))


def test_future_minor_recovers_known_fields_without_rewriting_source(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document: dict[str, Any] = json.loads(
        json.dumps(default_app_state_document())
    )
    document["schema_version"] = "1.1"
    selection = document["selection"]
    assert isinstance(selection, dict)
    selection["timeout_sec"] = 77
    document["future_optional_field"] = {"value": True}
    original = json.dumps(document, separators=(",", ":"))
    state_path.write_text(original, encoding="utf-8")

    result = StateRepository(tmp_path).load_with_diagnostics()

    assert result.state.schema_version == APP_STATE_SCHEMA_VERSION
    assert result.state.selection.timeout_sec == 77
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        StateDiagnosticCode.PARTIALLY_DEFAULTED,
    )
    assert state_path.read_text(encoding="utf-8") == original


def test_legacy_state_migrates_once_and_preserves_legacy_source(
    tmp_path: Path,
) -> None:
    legacy_path = tmp_path / LEGACY_STATE_FILENAME
    legacy_document = {
        "selected_mode": "file",
        "selected_target_file": "src/Main.gf",
        "selected_project_root": "C:/work/project",
        "selected_timeout_sec": "90",
        "selected_max_files": 12,
        "selected_keep_ok_details": "true",
        "selected_diff_previous": False,
        "selected_skip_version_probe": False,
        "selected_no_compile": True,
        "selected_emit_cpu_stats": True,
        "last_run_dir": "runs/run_1",
        "last_summary_path": "runs/run_1/summary.json",
        "status_message": "done",
        "is_running": True,
        "selected_scan_dir": "project/src",
        "unknown_legacy_field": "ignored",
    }
    _write_json(legacy_path, legacy_document)
    original_legacy = legacy_path.read_bytes()

    first = StateRepository(tmp_path).load_with_diagnostics()
    second = StateRepository(tmp_path).load_with_diagnostics()

    assert first.migrated is True
    assert first.diagnostics[0].code is StateDiagnosticCode.MIGRATED
    assert first.state.selection.mode is ValidationMode.QUICK
    assert first.state.selection.target_file == "src/Main.gf"
    assert first.state.selection.timeout_sec == 90
    assert first.state.selection.max_files == 12
    assert first.state.selection.keep_ok_details is True
    assert first.state.last_run.status_message == "done"
    assert legacy_path.read_bytes() == original_legacy
    assert (tmp_path / CANONICAL_STATE_FILENAME).is_file()
    assert second.migrated is False
    assert second.diagnostics[0].code is StateDiagnosticCode.LOADED


def test_existing_canonical_state_takes_precedence_over_legacy(
    tmp_path: Path,
) -> None:
    canonical = default_app_state()
    save_app_state(canonical, tmp_path)
    _write_json(
        tmp_path / LEGACY_STATE_FILENAME,
        {"selected_mode": "release", "status_message": "legacy"},
    )

    result = StateRepository(tmp_path).load_with_diagnostics()

    assert result.migrated is False
    assert result.diagnostics[0].code is StateDiagnosticCode.LOADED
    assert result.state.selection.mode is ValidationMode.DIAGNOSTIC
    assert result.state.last_run.status_message == ""


def test_reset_is_idempotent_and_does_not_touch_owned_data(
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "project" / "project.toml"
    run_file = tmp_path / "runs" / "run_1" / "summary.json"
    project_file.parent.mkdir()
    run_file.parent.mkdir(parents=True)
    project_file.write_text("schema_version = '1.0'\n", encoding="utf-8")
    run_file.write_text("{}\n", encoding="utf-8")
    repository = StateRepository(tmp_path)
    saved = repository.save(default_app_state())

    first = repository.reset()
    second = repository.reset()

    assert first == saved
    assert second is None
    assert not saved.exists()
    assert project_file.is_file()
    assert run_file.is_file()


def test_reset_can_replace_state_with_canonical_defaults(tmp_path: Path) -> None:
    repository = StateRepository(tmp_path)
    repository.save(_custom_state())

    destination = repository.reset(replace_with_defaults=True)
    loaded = repository.load()

    assert destination == tmp_path / CANONICAL_STATE_FILENAME
    assert loaded == replace(
        default_app_state(),
        producer=ProducerInfo(name="gf-wordbench", version=__version__),
    )


def test_repository_rejects_non_absolute_and_run_owned_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="workspace_root must be absolute"):
        StateRepository(Path("relative-workspace"))

    with pytest.raises(ValueError, match="canonical filename"):
        StateRepository(
            tmp_path,
            state_path=tmp_path / "state.json",
        )

    with pytest.raises(ValueError, match="must not be stored inside runs"):
        StateRepository(
            tmp_path,
            state_path=tmp_path / "runs" / CANONICAL_STATE_FILENAME,
        )


def test_alternate_parent_creation_is_explicit(tmp_path: Path) -> None:
    state_path = tmp_path / "portable" / CANONICAL_STATE_FILENAME

    with pytest.raises(StateWriteError):
        StateRepository(tmp_path, state_path=state_path).save(
            default_app_state()
        )

    destination = StateRepository(
        tmp_path,
        state_path=state_path,
        create_alternate_parent=True,
    ).save(default_app_state())

    assert destination == state_path
    assert destination.is_file()


def test_publication_failure_is_wrapped_and_preserves_last_valid_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = StateRepository(tmp_path)
    destination = repository.save(default_app_state())
    original = destination.read_bytes()

    def fail_atomic_write(*args: object, **kwargs: object) -> Path:
        del args, kwargs
        raise OSError("simulated publication failure")

    monkeypatch.setattr(
        state_repository,
        "atomic_write_bytes",
        fail_atomic_write,
    )

    with pytest.raises(StateWriteError) as captured:
        repository.save(_custom_state())

    assert captured.value.__cause__ is not None
    assert destination.read_bytes() == original
