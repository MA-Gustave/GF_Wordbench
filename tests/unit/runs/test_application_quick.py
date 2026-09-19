"""Focused coverage for the production path-resolved Quick application service."""

from __future__ import annotations

from pathlib import Path

import pytest

from gf_wordbench.bootstrap import build_framework_defaults
from gf_wordbench.config.models import ConfigurationResolutionRequest, ValidationTarget
from gf_wordbench.config.precedence import ConfigurationSource
from gf_wordbench.config.resolver import resolve_configuration
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    OverallStatus,
    TargetKind,
    ValidationMode,
    ValidationStatus,
)
from gf_wordbench.projects.languages.models import (
    CapabilityAvailability,
    LanguageCapability,
    LanguageCapabilityStatus,
    LanguageModuleCandidate,
    LanguageModuleRole,
    ResolvedLanguageContext,
    SelectedPathKind,
)
from gf_wordbench.runs import application
from gf_wordbench.validation.compilation.models import CompileSummary, CompileTargetKind


def _context(tmp_path: Path) -> ResolvedLanguageContext:
    language_directory = tmp_path / "external" / "GF" / "lib" / "src" / "albanian"
    language_directory.mkdir(parents=True)
    grammar = language_directory / "GrammarSqi.gf"
    grammar.write_text("abstract GrammarSqi = { cat S ; }\n", encoding="utf-8")

    rgl_root = tmp_path / "gf-rgl"
    rgl_source_root = rgl_root / "src"
    for name in ("abstract", "common", "prelude", "api"):
        (rgl_source_root / name).mkdir(parents=True)

    return ResolvedLanguageContext(
        language_key="albanian",
        selected_path=language_directory,
        selected_path_kind=SelectedPathKind.DIRECTORY,
        language_directory=language_directory,
        rgl_source_root=rgl_source_root,
        rgl_root=rgl_root,
        focused_target=None,
        module_suffix="Sqi",
        available_entrypoints=(
            LanguageModuleCandidate(grammar, LanguageModuleRole.GRAMMAR, "Sqi"),
        ),
        source_inventory=(grammar,),
        gf_path_requirements=(
            language_directory,
            language_directory.parent,
            rgl_source_root / "abstract",
            rgl_source_root / "common",
            rgl_source_root / "prelude",
            rgl_source_root / "api",
        ),
        capability_statuses=(
            LanguageCapabilityStatus(
                LanguageCapability.SOURCE_READY,
                CapabilityAvailability.AVAILABLE,
            ),
            LanguageCapabilityStatus(
                LanguageCapability.SCAN_READY,
                CapabilityAvailability.AVAILABLE,
            ),
        ),
    )


def _run_config(tmp_path: Path):
    context = _context(tmp_path)
    executable = tmp_path / "bin" / "gf.exe"
    executable.parent.mkdir()
    executable.write_bytes(b"fixture")
    executable.chmod(0o755)

    resolution = resolve_configuration(
        ConfigurationResolutionRequest(
            defaults=build_framework_defaults(),
            language_context=context,
            source_values={
                ConfigurationSource.GUI: {
                    "gf_executable": executable,
                    "rgl_root": context.rgl_root,
                    "output_root": tmp_path / "runs",
                    "mode": ValidationMode.QUICK,
                    "target": ValidationTarget(TargetKind.FILE, "GrammarSqi.gf"),
                    "timeout_sec": 60,
                    "max_files": 0,
                    "keep_ok_details": False,
                    "diff_previous": False,
                    "skip_version_probe": False,
                    "no_compile": False,
                    "emit_cpu_stats": False,
                }
            },
        )
    )
    return resolution.require()


def _fake_compile_summary(*, status: ValidationStatus, run_paths, source_path: Path) -> CompileSummary:
    stdout_path = run_paths.raw_compile_dir / "GrammarSqi.out.txt"
    stderr_path = run_paths.raw_compile_dir / "GrammarSqi.err.txt"
    stdout_path.write_text("fixture compile output\n", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")

    if status is ValidationStatus.OK:
        artifact = run_paths.gfo_dir / "GrammarSqi.gfo"
        artifact.write_bytes(b"fixture-gfo")
        produced = (artifact,)
        expected = (artifact,)
        error_kind = ErrorKind.OK
        first_error = ""
        exit_code = 0
        checks = True
    else:
        artifact = run_paths.gfo_dir / "GrammarSqi.gfo"
        produced = ()
        expected = (artifact,)
        error_kind = ErrorKind.TYPE
        first_error = "fixture type error"
        exit_code = 1
        checks = False

    return CompileSummary(
        target_id=source_path.name,
        target_kind=CompileTargetKind.SOURCE,
        status=status,
        command=("gf.exe", source_path.name),
        working_directory=source_path.parent,
        exit_code=exit_code,
        launched=True,
        timed_out=False,
        cancelled=False,
        duration_ms=5,
        error_kind=error_kind,
        first_error=first_error,
        error_detail="",
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        expected_artifacts=expected,
        produced_artifacts=produced,
        artifact_checks_passed=checks,
    )


def test_quick_application_builds_run_evidence_and_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_config = _run_config(tmp_path)
    monkeypatch.setattr(application, "_probe_version", lambda *args, **kwargs: "3.12")

    def compile_target(run_config, *, source_path, relative, run_paths, run_id, gf_version, token):
        del run_config, relative, run_id, gf_version, token
        return _fake_compile_summary(
            status=ValidationStatus.OK,
            run_paths=run_paths,
            source_path=source_path,
        )

    monkeypatch.setattr(application, "_compile_target", compile_target)
    events: list[object] = []

    result = application.execute_quick_run(
        run_config,
        events.append,
        lambda: None,
        run_id="20260917_084500",
    )

    assert result.overall_status is OverallStatus.OK
    assert result.gf_version == "3.12"
    assert len(result.file_results) == 1
    assert result.file_results[0].file_path.name == "GrammarSqi.gf"
    assert result.file_results[0].status is ValidationStatus.OK
    assert result.run_paths.summary_md.is_file()
    assert (result.run_paths.raw_scan_dir / "GrammarSqi.scan.txt").is_file()
    assert (result.run_paths.gfo_dir / "GrammarSqi.gfo").is_file()
    assert events


def test_quick_application_preserves_compile_failure_as_direct_file_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_config = _run_config(tmp_path)
    monkeypatch.setattr(application, "_probe_version", lambda *args, **kwargs: "3.12")

    def compile_target(run_config, *, source_path, relative, run_paths, run_id, gf_version, token):
        del run_config, relative, run_id, gf_version, token
        return _fake_compile_summary(
            status=ValidationStatus.FAIL,
            run_paths=run_paths,
            source_path=source_path,
        )

    monkeypatch.setattr(application, "_compile_target", compile_target)

    result = application.execute_quick_run(
        run_config,
        lambda _event: None,
        lambda: None,
        run_id="20260917_084501",
    )

    assert result.overall_status is OverallStatus.FAIL
    assert result.file_results[0].status is ValidationStatus.FAIL
    assert result.file_results[0].is_direct is True
    assert result.file_results[0].compile_summary.first_error == "fixture type error"
    assert result.run_paths.summary_md.is_file()


def test_run_validation_provider_uses_resolved_run_config_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_config = _run_config(tmp_path)
    sentinel = object()
    calls: list[tuple[object, object, object]] = []

    def execute(config, event_sink, cancellation_check, **_kwargs):
        calls.append((config, event_sink, cancellation_check))
        return sentinel

    monkeypatch.setattr(application, "execute_quick_run", execute)

    result = application.run_validation(run_config)

    assert result is sentinel
    assert calls and calls[0][0] is run_config
    with pytest.raises(Exception, match="resolved RunConfig"):
        application.run_validation(object())
