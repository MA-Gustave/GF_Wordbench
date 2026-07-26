"""Unit tests for application-state filesystem persistence."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
import json
import logging
from pathlib import Path
from typing import Any, cast

import pytest

from gf_wordbench.kernel.errors import SchemaValidationError, StateWriteError
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.state import repository as repository_module
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
    default_app_state,
    default_app_state_document,
)
from gf_wordbench.version import __version__

pytestmark = pytest.mark.schema


def _document() -> dict[str, Any]:
    return deepcopy(cast(dict[str, Any], default_app_state_document()))


def _write_document(path: Path, document: object) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _custom_state() -> AppState:
    state = default_app_state()
    return replace(
        state,
        environment=replace(
            state.environment,
            project_root="C:/workspace/project",
            rgl_root="C:/GF/RGL",
            gf_executable="C:/Program Files/GF/gf.exe",
            output_root="C:/workspace/runs",
        ),
        selection=replace(
            state.selection,
            mode=ValidationMode.CHECKPOINT,
            target_file="src/UnicodeÉ.gf",
            timeout_sec=75,
            max_files=12,
            keep_ok_details=True,
            diff_previous=False,
            emit_cpu_stats=True,
        ),
        last_run=replace(
            state.last_run,
            run_dir="runs/run_20260725_190423",
            summary_path="runs/run_20260725_190423/summary.json",
            status_message="terminé",
        ),
    )



def test_default_paths_are_workspace_owned_and_resolved(tmp_path: Path) -> None:
    repository = StateRepository(tmp_path)

    assert repository.workspace_root == tmp_path.resolve()
    assert repository.resolved_state_path == (
        tmp_path / CANONICAL_STATE_FILENAME
    )
    assert repository.legacy_state_path == tmp_path / LEGACY_STATE_FILENAME


def test_explicit_state_path_keeps_legacy_file_beside_it(tmp_path: Path) -> None:
    portable = tmp_path / "portable"
    portable.mkdir()
    state_path = portable / CANONICAL_STATE_FILENAME

    repository = StateRepository(tmp_path, state_path=state_path)

    assert repository.resolved_state_path == state_path
    assert repository.legacy_state_path == portable / LEGACY_STATE_FILENAME


@pytest.mark.parametrize(
    ("field", "value", "error", "message"),
    (
        ("workspace_root", ".", TypeError, "workspace_root must be pathlib.Path"),
        (
            "workspace_root",
            Path("relative"),
            ValueError,
            "workspace_root must be absolute",
        ),
        (
            "create_alternate_parent",
            1,
            TypeError,
            "create_alternate_parent must be a bool",
        ),
        (
            "quarantine_invalid",
            1,
            TypeError,
            "quarantine_invalid must be a bool",
        ),
    ),
)
def test_constructor_rejects_invalid_boundary_values(
    tmp_path: Path,
    field: str,
    value: object,
    error: type[Exception],
    message: str,
) -> None:
    arguments: dict[str, object] = {"workspace_root": tmp_path}
    arguments[field] = value

    with pytest.raises(error, match=message):
        StateRepository(**arguments)  # type: ignore[arg-type]


def test_constructor_requires_existing_workspace_directory(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"
    regular_file = tmp_path / "workspace.txt"
    regular_file.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        StateRepository(missing)

    with pytest.raises(NotADirectoryError):
        StateRepository(regular_file)


def test_constructor_rejects_noncanonical_and_run_owned_state_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="canonical filename"):
        StateRepository(tmp_path, state_path=tmp_path / "state.json")

    with pytest.raises(ValueError, match="must not be stored inside runs"):
        StateRepository(
            tmp_path,
            state_path=tmp_path / "runs" / "nested" / CANONICAL_STATE_FILENAME,
        )


def test_constructor_rejects_symlink_alias_into_runs(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    alias = tmp_path / "portable"
    try:
        alias.symlink_to(runs, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("directory symlinks are unavailable")

    with pytest.raises(ValueError, match="must not be stored inside runs"):
        StateRepository(
            tmp_path,
            state_path=alias / CANONICAL_STATE_FILENAME,
        )


def test_missing_state_returns_defaults_without_creating_a_file(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=repository_module.__name__)
    repository = StateRepository(tmp_path)

    result = repository.load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.source_path == tmp_path / CANONICAL_STATE_FILENAME
    assert result.migrated is False
    assert tuple(item.code for item in result.diagnostics) == (
        StateDiagnosticCode.MISSING,
    )
    assert not result.source_path.exists()
    record = caplog.records[-1]
    assert record.levelno == logging.WARNING
    assert getattr(record, "operation") == "load"
    assert (
        getattr(record, "state_diagnostic")
        == StateDiagnosticCode.MISSING.value
    )


def test_valid_canonical_state_loads_with_structured_loaded_diagnostic(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = StateRepository(tmp_path)
    destination = repository.save(_custom_state())
    caplog.clear()
    caplog.set_level(logging.INFO, logger=repository_module.__name__)

    result = repository.load_with_diagnostics()

    assert result.state.producer == ProducerInfo(
        name="gf-wordbench",
        version=__version__,
    )
    assert result.state.selection.mode is ValidationMode.CHECKPOINT
    assert result.state.selection.target_file == "src/UnicodeÉ.gf"
    assert result.source_path == destination
    assert result.migrated is False
    assert tuple(item.code for item in result.diagnostics) == (
        StateDiagnosticCode.LOADED,
    )
    record = caplog.records[-1]
    assert record.levelno == logging.INFO
    assert getattr(record, "operation") == "load"
    assert (
        getattr(record, "state_diagnostic")
        == StateDiagnosticCode.LOADED.value
    )


@pytest.mark.parametrize(
    "payload",
    (
        b"",
        b"   \r\n",
        b"{",
        b"[]\n",
        b'"text"\n',
        b'{"schema_id":"a","schema_id":"b"}\n',
        b'{"schema_id":NaN}\n',
        b"\xff\xfe\x00\x00",
    ),
)
def test_malformed_state_bytes_fail_safe_without_mutation(
    tmp_path: Path,
    payload: bytes,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    state_path.write_bytes(payload)

    result = StateRepository(tmp_path).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.migrated is False
    assert result.diagnostics[0].code is StateDiagnosticCode.MALFORMED
    assert state_path.read_bytes() == payload


def test_schema_identifier_mismatch_is_not_quarantined(tmp_path: Path) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document = _document()
    document["schema_id"] = "another-product.state"
    _write_document(state_path, document)
    original = state_path.read_bytes()

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.diagnostics[0].code is StateDiagnosticCode.SCHEMA_MISMATCH
    assert state_path.read_bytes() == original
    assert not tuple(tmp_path.glob(".gf_wordbench_state.invalid-*.json"))


@pytest.mark.parametrize(
    "schema_version",
    (None, 1, "", "1", "1.", ".0", "1.a", "01.０"),
)
def test_invalid_schema_version_is_malformed_and_may_be_quarantined(
    tmp_path: Path,
    schema_version: object,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document = _document()
    document["schema_version"] = schema_version
    _write_document(state_path, document)

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.diagnostics[0].code is StateDiagnosticCode.MALFORMED
    assert any(
        item.code is StateDiagnosticCode.QUARANTINED
        for item in result.diagnostics
    )


def test_unsupported_major_fails_closed_without_quarantine(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document = _document()
    document["schema_version"] = "2.0"
    _write_document(state_path, document)
    original = state_path.read_bytes()

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.diagnostics[0].code is StateDiagnosticCode.VERSION_UNSUPPORTED
    assert state_path.read_bytes() == original
    assert not tuple(tmp_path.glob(".gf_wordbench_state.invalid-*.json"))


def test_supported_recovery_returns_one_diagnostic_per_warning(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    document = _document()
    selection = cast(dict[str, object], document["selection"])
    selection["mode"] = "unsupported"
    selection["timeout_sec"] = 0
    document["unknown_optional"] = True
    _write_document(state_path, document)

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state.selection.mode is ValidationMode.DIAGNOSTIC
    assert result.state.selection.timeout_sec == 60
    assert result.migrated is False
    assert result.diagnostics
    assert all(
        item.code is StateDiagnosticCode.PARTIALLY_DEFAULTED
        for item in result.diagnostics
    )
    assert any("$.selection.mode" in item.message for item in result.diagnostics)
    assert any(
        "$.selection.timeout_sec" in item.message
        for item in result.diagnostics
    )
    assert not tuple(tmp_path.glob(".gf_wordbench_state.invalid-*.json"))


def test_quarantine_preserves_original_bytes_beside_state_file(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    payload = b'{"schema_id":'
    state_path.write_bytes(payload)

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    quarantine = next(
        item.path
        for item in result.diagnostics
        if item.code is StateDiagnosticCode.QUARANTINED
    )
    assert quarantine.parent == state_path.parent
    assert quarantine.name.startswith(".gf_wordbench_state.invalid-")
    assert quarantine.suffix == ".json"
    assert quarantine.read_bytes() == payload
    assert state_path.read_bytes() == payload


def test_quarantine_failure_does_not_prevent_default_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME
    state_path.write_text("{", encoding="utf-8")

    def fail_copy(*args: object, **kwargs: object) -> Path:
        del args, kwargs
        raise OSError("simulated quarantine failure")

    monkeypatch.setattr(repository_module, "copy_file", fail_copy)
    caplog.set_level(logging.WARNING, logger=repository_module.__name__)

    result = StateRepository(
        tmp_path,
        quarantine_invalid=True,
    ).load_with_diagnostics()

    assert result.state == default_app_state()
    assert tuple(item.code for item in result.diagnostics) == (
        StateDiagnosticCode.MALFORMED,
    )
    assert "application state quarantine failed" in caplog.text


def test_existing_canonical_file_prevents_legacy_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = StateRepository(tmp_path)
    repository.save(default_app_state())
    _write_document(
        tmp_path / LEGACY_STATE_FILENAME,
        {"selected_mode": "release"},
    )

    def unexpected_migration(*args: object, **kwargs: object) -> None:
        del args, kwargs
        pytest.fail("legacy migration must not run when canonical state exists")

    monkeypatch.setattr(
        repository_module,
        "migrate_legacy_state",
        unexpected_migration,
    )

    result = repository.load_with_diagnostics()

    assert result.migrated is False
    assert result.diagnostics[0].code is StateDiagnosticCode.LOADED
    assert result.state.selection.mode is ValidationMode.DIAGNOSTIC


def test_legacy_migration_failure_preserves_source_and_uses_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_path = tmp_path / LEGACY_STATE_FILENAME
    _write_document(legacy_path, {"selected_mode": "file"})
    original = legacy_path.read_bytes()

    def fail_migration(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ValueError("simulated migration failure")

    monkeypatch.setattr(
        repository_module,
        "migrate_legacy_state",
        fail_migration,
    )

    result = StateRepository(tmp_path).load_with_diagnostics()

    assert result.state == default_app_state()
    assert result.source_path == tmp_path / CANONICAL_STATE_FILENAME
    assert result.migrated is False
    assert result.diagnostics[0].code is StateDiagnosticCode.MALFORMED
    assert "legacy state migration failed" in result.diagnostics[0].message
    assert legacy_path.read_bytes() == original
    assert not result.source_path.exists()


def test_save_uses_atomic_writer_with_canonical_validated_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = StateRepository(tmp_path)
    captured: dict[str, object] = {}

    def capture_atomic_write(
        destination: object,
        data: object,
        **kwargs: object,
    ) -> Path:
        captured["destination"] = destination
        captured["data"] = data
        captured.update(kwargs)
        candidate = tmp_path / ".candidate.json"
        candidate.write_bytes(bytes(cast(bytes, data)))
        validator = cast(Callable[[Path], None], kwargs["validator"])
        validator(candidate)
        return cast(Path, destination)

    monkeypatch.setattr(
        repository_module,
        "atomic_write_bytes",
        capture_atomic_write,
    )

    destination = repository.save(_custom_state())
    payload = cast(bytes, captured["data"])
    document = cast(dict[str, Any], json.loads(payload.decode("utf-8")))

    assert destination == tmp_path / CANONICAL_STATE_FILENAME
    assert captured["destination"] == destination
    assert captured["root"] == tmp_path
    assert captured["create_parents"] is False
    assert captured["role"] == "application state"
    assert document["schema_id"] == APP_STATE_SCHEMA_ID
    assert document["schema_version"] == APP_STATE_SCHEMA_VERSION
    assert document["producer"] == {
        "name": "gf-wordbench",
        "version": __version__,
    }
    assert document["selection"]["mode"] == "checkpoint"
    assert payload.startswith(b"{\n")
    assert payload.endswith(b"\n")
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert "UnicodeÉ.gf" in payload.decode("utf-8")


def test_save_validates_typed_state_before_calling_atomic_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def unexpected_write(*args: object, **kwargs: object) -> Path:
        nonlocal called
        del args, kwargs
        called = True
        return tmp_path / CANONICAL_STATE_FILENAME

    monkeypatch.setattr(
        repository_module,
        "atomic_write_bytes",
        unexpected_write,
    )

    with pytest.raises(TypeError, match="state must be an AppState"):
        StateRepository(tmp_path).save(cast(AppState, object()))

    assert called is False


def test_candidate_validation_requires_exact_canonical_document(
    tmp_path: Path,
) -> None:
    repository = StateRepository(tmp_path)
    candidate = tmp_path / ".candidate.json"
    document = _document()
    document["producer"] = {
        "name": "gf-wordbench",
        "version": __version__,
    }
    _write_document(candidate, document)

    repository._validate_candidate(candidate)

    document["unknown"] = True
    _write_document(candidate, document)
    with pytest.raises(SchemaValidationError):
        repository._validate_candidate(candidate)


def test_state_write_error_from_atomic_adapter_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StateWriteError("adapter rejected publication")

    def fail_atomic_write(*args: object, **kwargs: object) -> Path:
        del args, kwargs
        raise expected

    monkeypatch.setattr(
        repository_module,
        "atomic_write_bytes",
        fail_atomic_write,
    )

    with pytest.raises(StateWriteError) as captured:
        StateRepository(tmp_path).save(default_app_state())

    assert captured.value is expected
    assert captured.value.__cause__ is None


def test_unexpected_save_failure_is_wrapped_with_path_and_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME

    def fail_atomic_write(*args: object, **kwargs: object) -> Path:
        del args, kwargs
        raise OSError("simulated disk failure")

    monkeypatch.setattr(
        repository_module,
        "atomic_write_bytes",
        fail_atomic_write,
    )
    caplog.set_level(logging.WARNING, logger=repository_module.__name__)

    with pytest.raises(StateWriteError) as captured:
        StateRepository(tmp_path).save(default_app_state())

    error = captured.value
    assert error.subject == str(state_path)
    assert error.evidence_paths == (str(state_path),)
    assert isinstance(error.__cause__, OSError)
    assert "application state could not be written atomically" == error.message
    assert any(
        getattr(record, "state_diagnostic", None)
        == StateDiagnosticCode.WRITE_FAILED.value
        for record in caplog.records
    )


def test_alternate_parent_creation_is_never_implicit(tmp_path: Path) -> None:
    state_path = tmp_path / "portable" / "nested" / CANONICAL_STATE_FILENAME

    with pytest.raises(StateWriteError) as captured:
        StateRepository(tmp_path, state_path=state_path).save(
            default_app_state()
        )

    assert isinstance(captured.value.__cause__, FileNotFoundError)
    assert not state_path.parent.exists()

    destination = StateRepository(
        tmp_path,
        state_path=state_path,
        create_alternate_parent=True,
    ).save(default_app_state())

    assert destination == state_path
    assert destination.is_file()


def test_reset_deletes_only_the_state_file_and_is_idempotent(
    tmp_path: Path,
) -> None:
    repository = StateRepository(tmp_path)
    state_path = repository.save(_custom_state())
    project = tmp_path / "project" / "project.toml"
    run_summary = tmp_path / "runs" / "run_1" / "summary.json"
    project.parent.mkdir()
    run_summary.parent.mkdir(parents=True)
    project.write_text("schema_version = '1.0'\n", encoding="utf-8")
    run_summary.write_text("{}\n", encoding="utf-8")

    assert repository.reset() == state_path
    assert repository.reset() is None
    assert not state_path.exists()
    assert project.is_file()
    assert run_summary.is_file()


def test_reset_can_replace_existing_state_with_canonical_defaults(
    tmp_path: Path,
) -> None:
    repository = StateRepository(tmp_path)
    repository.save(_custom_state())

    destination = repository.reset(replace_with_defaults=True)
    loaded = repository.load()

    assert destination == tmp_path / CANONICAL_STATE_FILENAME
    assert loaded == replace(
        default_app_state(),
        producer=ProducerInfo(name="gf-wordbench", version=__version__),
    )


def test_reset_requires_a_real_boolean(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="replace_with_defaults must be a bool"):
        StateRepository(tmp_path).reset(
            replace_with_defaults=cast(bool, 1)
        )


def test_reset_preserves_adapter_state_write_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StateWriteError("adapter rejected removal")

    def fail_unlink(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise expected

    monkeypatch.setattr(repository_module, "unlink_file", fail_unlink)

    with pytest.raises(StateWriteError) as captured:
        StateRepository(tmp_path).reset()

    assert captured.value is expected


def test_unexpected_reset_failure_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / CANONICAL_STATE_FILENAME

    def fail_unlink(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise PermissionError("simulated removal failure")

    monkeypatch.setattr(repository_module, "unlink_file", fail_unlink)

    with pytest.raises(StateWriteError) as captured:
        StateRepository(tmp_path).reset()

    assert captured.value.subject == str(state_path)
    assert captured.value.evidence_paths == (str(state_path),)
    assert isinstance(captured.value.__cause__, PermissionError)


def test_public_load_helper_forwards_explicit_options(
    tmp_path: Path,
) -> None:
    portable = tmp_path / "portable"
    portable.mkdir()
    state_path = portable / CANONICAL_STATE_FILENAME
    StateRepository(tmp_path, state_path=state_path).save(_custom_state())

    loaded = load_app_state(
        tmp_path,
        state_path=state_path,
        quarantine_invalid=True,
    )

    assert loaded.selection.mode is ValidationMode.CHECKPOINT
    assert loaded.environment.gf_executable == "C:/Program Files/GF/gf.exe"


def test_public_save_helper_forwards_parent_creation_option(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "portable" / CANONICAL_STATE_FILENAME

    destination = save_app_state(
        _custom_state(),
        tmp_path,
        state_path=state_path,
        create_alternate_parent=True,
    )

    assert destination == state_path
    assert destination.is_file()
