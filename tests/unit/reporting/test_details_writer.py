"""Unit tests for deterministic per-result Markdown detail reports."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)
from gf_wordbench.reporting.details import writer
from gf_wordbench.validation.compilation.models import CompileWarning, CompileWarningKind
from gf_wordbench.reporting.details.writer import (
    DetailWritePolicy,
    file_detail_key,
    render_file_detail,
    render_scenario_detail,
    scenario_detail_key,
    write_detail_reports,
    write_file_detail,
    write_scenario_detail,
)


@dataclass(slots=True)
class _CompileSummary:
    execution_state: ExecutionState | None = ExecutionState.COMPLETED
    exit_code: int | None = 1
    timed_out: bool = False
    duration_ms: int = 1_250
    error_kind: ErrorKind = ErrorKind.SYNTAX
    error_detail: str = "syntax detail"
    stdout_path: Path | None = None
    stderr_path: Path | None = None


@dataclass(slots=True)
class _Artifact:
    path: Path
    role: str = "gfo"
    required: bool = True
    size_bytes: int | None = 7


@dataclass(slots=True)
class _FileResult:
    file_path: Path
    module_name: str = "GrammarDemo"
    status: ValidationStatus = ValidationStatus.FAIL
    diagnostic_class: DiagnosticClass = DiagnosticClass.DIRECT
    error_kind: ErrorKind = ErrorKind.SYNTAX
    is_direct: bool = True
    primary_message: str = "The parser rejected `Demo` <input>."
    blocked_by: tuple[str, ...] = ()
    scan_counts: object = field(
        default_factory=lambda: {
            "runtime_str_match": 1,
            "trailing_spaces": 2,
        }
    )
    compile_summary: _CompileSummary | None = field(default_factory=_CompileSummary)
    scan_log_path: Path | None = None
    artifacts: tuple[_Artifact, ...] = ()


@dataclass(slots=True)
class _Section:
    id: str
    completed: bool
    required: bool = True
    message: str = ""


@dataclass(slots=True)
class _Assertion:
    assertion_id: str
    assertion_kind: str
    status: str
    section_id: str | None = None
    message: str = ""
    evidence_path: Path | None = None


@dataclass(slots=True)
class _Diagnostic:
    kind: str
    source: str
    message: str
    marker: str
    line_number: int | None = None
    is_failure: bool = True


@dataclass(slots=True)
class _ScenarioResult:
    scenario_id: str
    script_path: Path = Path("project/tests/scenarios/demo.gfs")
    required: bool = True
    status: ValidationStatus = ValidationStatus.FAIL
    execution_state: ExecutionState | None = ExecutionState.COMPLETED
    diagnostic_class: DiagnosticClass = DiagnosticClass.DIRECT
    error_kind: ErrorKind = ErrorKind.SCRIPT
    exit_code: int | None = 1
    timed_out: bool = False
    duration_ms: int = 2_500
    primary_message: str = "Scenario output did not match."
    command: tuple[str, ...] = ("gf", "--run", "demo.gfs")
    working_directory: Path = Path("project")
    blocked_by: tuple[str, ...] = ()
    sections: tuple[_Section, ...] = ()
    assertions: tuple[_Assertion, ...] = ()
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    normalized_output_path: Path | None = None
    gold_path: Path | None = None
    gold_match: bool | None = None
    gold_diff_path: Path | None = None
    artifacts: tuple[_Artifact, ...] = ()
    diagnostics: tuple[_Diagnostic, ...] = ()


@dataclass(slots=True)
class _RunPaths:
    run_dir: Path
    details_dir: Path

    def require_owned_path(self, value: Path) -> Path:
        resolved = value.resolve(strict=False)
        resolved.relative_to(self.run_dir)
        return resolved


@dataclass(slots=True)
class _RunResult:
    run_paths: _RunPaths
    keep_ok_details: bool = False
    file_results: tuple[object, ...] = ()
    scenario_results: tuple[object, ...] = ()

    @property
    def run_config(self) -> object:
        return SimpleNamespace(keep_ok_details=self.keep_ok_details)


def _run_layout(tmp_path: Path) -> tuple[Path, Path]:
    run_root = (tmp_path / "run_20260725_120000").resolve()
    details_root = run_root / "details"
    run_root.mkdir()
    details_root.mkdir()
    return run_root, details_root


def _write(path: Path, content: str = "evidence\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


@pytest.mark.parametrize(
    ("kwargs", "error_type", "message"),
    [
        ({"keep_ok_details": 1}, TypeError, "keep_ok_details"),
        ({"max_rows": True}, ValueError, "max_rows"),
        ({"max_rows": 0}, ValueError, "max_rows"),
        ({"max_text_characters": 0}, ValueError, "max_text_characters"),
    ],
)
def test_detail_write_policy_rejects_invalid_values(
    kwargs: dict[str, object],
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        DetailWritePolicy(**kwargs)  # type: ignore[arg-type]


def test_detail_keys_are_safe_deterministic_and_collision_resistant() -> None:
    first = file_detail_key(Path("lib/src/a/Grammar.gf"))
    second = file_detail_key(Path("lib/src/b/Grammar.gf"))

    assert first == file_detail_key("lib/src/a/Grammar.gf")
    assert first != second
    assert first.startswith("Grammar.gf--")
    assert len(first.rsplit("--", 1)[1]) == 16
    assert scenario_detail_key("parse / Unicode: élève") == scenario_detail_key(
        "parse / Unicode: élève"
    )
    assert "/" not in scenario_detail_key("parse / Unicode: élève")
    assert " " not in scenario_detail_key("parse / Unicode: élève")
    assert scenario_detail_key("CON").startswith("_CON--")


def test_detail_keys_bound_the_readable_prefix() -> None:
    identity = "folder/" + ("x" * 200) + ".gf"
    key = file_detail_key(identity)
    readable, digest = key.rsplit("--", 1)

    assert len(readable) <= 96
    assert digest == hashlib.sha256(identity.encode()).hexdigest()[:16]
    assert len(f"{key}.md") <= 120


@pytest.mark.parametrize("value", ["", "   ", "bad\x00id"])
def test_detail_keys_reject_invalid_identities(value: str) -> None:
    with pytest.raises(ValueError):
        scenario_detail_key(value)


def test_render_file_detail_is_bounded_deterministic_and_links_evidence(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    report_path = details_root / "files" / "GrammarDemo.md"
    scan = _write(run_root / "raw" / "scan" / "élève scan.txt")
    stdout = _write(run_root / "raw" / "compile" / "Grammar Demo.out.txt")
    stderr = _write(run_root / "raw" / "compile" / "Grammar Demo.err.txt")
    artifact = _write(run_root / "artifacts" / "gfo" / "GrammarDemo.gfo")
    result = _FileResult(
        file_path=Path("lib/src/demo/GrammarDemo.gf"),
        primary_message="first line\nsecond *line*",
        blocked_by=("zeta", "Alpha", "zeta"),
        compile_summary=_CompileSummary(
            stdout_path=stdout,
            stderr_path=stderr,
            error_detail="line 1\nline 2",
        ),
        scan_log_path=scan,
        artifacts=(_Artifact(path=artifact),),
    )

    rendered = render_file_detail(
        result,  # type: ignore[arg-type]
        report_path=report_path,
        run_root=run_root,
    )

    assert rendered == render_file_detail(
        result,  # type: ignore[arg-type]
        report_path=report_path,
        run_root=run_root,
    )
    assert rendered.startswith("# File Detail\n")
    assert "- File: `lib/src/demo/GrammarDemo.gf`" in rendered
    assert "- Status: `FAIL`" in rendered
    assert "- Diagnostic class: `direct`" in rendered
    assert "- Error kind: `SYNTAX`" in rendered
    assert "first line  \nsecond \\*line\\*" in rendered
    assert rendered.index("- `Alpha`") < rendered.index("- `zeta`")
    assert rendered.count("- `zeta`") == 1
    assert "    line 1\n    line 2" in rendered
    assert "| Runtime Str Match | 1 |" in rendered
    assert "| Trailing Spaces | 2 |" in rendered
    assert "%C3%A9l%C3%A8ve%20scan.txt" in rendered
    assert "Grammar%20Demo.out.txt" in rendered
    assert "../../artifacts/gfo/GrammarDemo.gfo" in rendered
    assert rendered.endswith("\n")
    assert "\r" not in rendered


def test_render_file_detail_marks_missing_and_external_evidence(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    outside = (tmp_path / "outside.log").resolve()
    missing = run_root / "raw" / "compile" / "missing.err.txt"
    result = _FileResult(
        file_path=Path("Grammar.gf"),
        scan_log_path=outside,
        compile_summary=_CompileSummary(stderr_path=missing),
    )

    rendered = render_file_detail(
        result,  # type: ignore[arg-type]
        report_path=details_root / "files" / "Grammar.md",
        run_root=run_root,
    )

    assert f"`{outside.as_posix()}`" in rendered
    assert f"Missing: `{missing.as_posix()}`" in rendered
    assert outside.as_uri() not in rendered


def test_render_scenario_detail_records_markers_assertions_and_gold(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    report_path = details_root / "scenarios" / "parse.md"
    stdout = _write(run_root / "raw" / "scenarios" / "parse output.txt")
    assertion_evidence = _write(run_root / "raw" / "scenarios" / "assertion.txt")
    gold = _write(run_root / "gold" / "parse.txt")
    diff = _write(run_root / "raw" / "scenarios" / "parse.diff.txt")
    result = _ScenarioResult(
        scenario_id="parse-unicode",
        stdout_path=stdout,
        gold_path=gold,
        gold_match=False,
        gold_diff_path=diff,
        sections=(
            _Section("setup", True, message="ready"),
            _Section("result", False, message="missing marker"),
        ),
        assertions=(
            _Assertion(
                assertion_id="contains-é",
                assertion_kind="contains",
                status="FAIL",
                section_id="result",
                message="Expected | value",
                evidence_path=assertion_evidence,
            ),
        ),
        diagnostics=(
            _Diagnostic(
                kind="gf_shell_error",
                source="stderr",
                line_number=7,
                marker="constant not found:",
                message="constant not found: C0351",
            ),
        ),
    )

    rendered = render_scenario_detail(
        result,  # type: ignore[arg-type]
        report_path=report_path,
        run_root=run_root,
    )

    assert rendered.startswith("# Scenario Detail\n")
    assert "- Scenario: `parse-unicode`" in rendered
    assert "- Duration: 2.500 s" in rendered
    assert "    gf --run demo.gfs" in rendered
    assert "| setup | Yes | Yes | ready |" in rendered
    assert "| result | No | Yes | missing marker |" in rendered
    assert "Expected \\| value" in rendered
    assert "../../raw/scenarios/assertion.txt" in rendered
    assert "## Observed Diagnostics" in rendered
    assert (
        r"| gf\_shell\_error | stderr | 7 | Yes | constant not found: | "
        "constant not found: C0351 |"
    ) in rendered
    assert "- State: `Mismatch`" in rendered
    assert "[gold](../../gold/parse.txt)" in rendered
    assert "parse%20output.txt" in rendered


def test_rendering_enforces_row_and_text_limits(tmp_path: Path) -> None:
    run_root, details_root = _run_layout(tmp_path)
    result = _ScenarioResult(
        scenario_id="bounded",
        primary_message="abcdefghij",
        sections=(
            _Section("one", True),
            _Section("two", True),
            _Section("three", True),
        ),
    )
    policy = DetailWritePolicy(max_rows=2, max_text_characters=8)

    rendered = render_scenario_detail(
        result,  # type: ignore[arg-type]
        report_path=details_root / "scenarios" / "bounded.md",
        run_root=run_root,
        policy=policy,
    )

    assert "Showing 2 of 3." in rendered
    assert "| three |" not in rendered
    assert "abcdefghij" not in rendered
    assert r"… \[trun" in rendered


def test_write_file_and_scenario_details_use_owned_names_and_lf(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    file_result = _FileResult(file_path=Path("lib/src/demo/Grammar Demo.gf"))
    scenario_result = _ScenarioResult(scenario_id="parse / demo")

    file_path = write_file_detail(
        file_result,  # type: ignore[arg-type]
        details_root=details_root,
        run_root=run_root,
    )
    scenario_path = write_scenario_detail(
        scenario_result,  # type: ignore[arg-type]
        details_root=details_root,
        run_root=run_root,
    )

    assert file_path == details_root / "files" / (f"{file_detail_key(file_result.file_path)}.md")
    assert scenario_path == details_root / "scenarios" / (
        f"{scenario_detail_key(scenario_result.scenario_id)}.md"
    )
    assert file_path.read_bytes().startswith(b"# File Detail\n")
    assert scenario_path.read_bytes().startswith(b"# Scenario Detail\n")
    assert b"\r\n" not in file_path.read_bytes()
    assert b"\r\n" not in scenario_path.read_bytes()


@pytest.mark.parametrize(
    ("details_root_factory", "run_root_factory", "message"),
    [
        (lambda root: Path("relative"), lambda root: root, "details_root must be absolute"),
        (lambda root: root / "details", lambda root: Path("relative"), "run_root must be absolute"),
        (lambda root: root.parent / "outside", lambda root: root, "details_root escapes run_root"),
    ],
)
def test_writers_reject_unowned_or_relative_roots(
    tmp_path: Path,
    details_root_factory: object,
    run_root_factory: object,
    message: str,
) -> None:
    run_root, _ = _run_layout(tmp_path)
    details_factory = details_root_factory  # keep parametrized callables typed locally
    root_factory = run_root_factory

    with pytest.raises((TypeError, ValueError), match=message):
        write_file_detail(
            _FileResult(Path("Grammar.gf")),  # type: ignore[arg-type]
            details_root=details_factory(run_root),  # type: ignore[operator]
            run_root=root_factory(run_root),  # type: ignore[operator]
        )


def test_write_detail_reports_honors_keep_ok_details_configuration(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    failed_file = _FileResult(Path("z/Failure.gf"))
    ok_file = _FileResult(
        Path("a/Okay.gf"),
        status=ValidationStatus.OK,
        diagnostic_class=DiagnosticClass.OK,
        error_kind=ErrorKind.OK,
    )
    ok_scenario = _ScenarioResult(
        "ok-scenario",
        status=ValidationStatus.OK,
        diagnostic_class=DiagnosticClass.OK,
        error_kind=ErrorKind.OK,
        exit_code=0,
    )
    run_result = _RunResult(
        run_paths=_RunPaths(run_root, details_root),
        keep_ok_details=False,
        file_results=(failed_file, ok_file),
        scenario_results=(ok_scenario,),
    )

    result = write_detail_reports(run_result)  # type: ignore[arg-type]

    assert result.ok is True
    assert [artifact.subject_id for artifact in result.artifacts] == ["z/Failure.gf"]
    assert result.skipped_subjects == (
        "file:a/Okay.gf",
        "scenario:ok-scenario",
    )
    assert result.paths == tuple(artifact.path for artifact in result.artifacts)
    assert result.paths[0].is_file()


def test_explicit_policy_can_retain_successful_details(tmp_path: Path) -> None:
    run_root, details_root = _run_layout(tmp_path)
    run_result = _RunResult(
        run_paths=_RunPaths(run_root, details_root),
        file_results=(
            _FileResult(
                Path("Okay.gf"),
                status=ValidationStatus.OK,
                diagnostic_class=DiagnosticClass.OK,
                error_kind=ErrorKind.OK,
            ),
        ),
    )

    result = write_detail_reports(
        run_result,  # type: ignore[arg-type]
        policy=DetailWritePolicy(keep_ok_details=True),
    )

    assert result.ok is True
    assert result.skipped_subjects == ()
    assert len(result.artifacts) == 1
    assert result.artifacts[0].path.is_file()


def test_write_detail_reports_isolates_failures_and_sorts_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    file_z = _FileResult(Path("z/Failure.gf"))
    file_a = _FileResult(Path("a/Failure.gf"))
    scenario = _ScenarioResult("middle")
    run_result = _RunResult(
        run_paths=_RunPaths(run_root, details_root),
        file_results=(file_z, file_a),
        scenario_results=(scenario,),
    )
    real_write_file_detail = writer.write_file_detail

    def selective_write(file_result: _FileResult, **kwargs: object) -> Path:
        if str(file_result.file_path) == "z/Failure.gf":
            raise OSError("simulated detail failure")
        return real_write_file_detail(file_result, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(writer, "write_file_detail", selective_write)

    result = write_detail_reports(run_result)  # type: ignore[arg-type]

    assert result.ok is False
    assert [(item.subject_kind, item.subject_id) for item in result.artifacts] == [
        ("file", "a/Failure.gf"),
        ("scenario", "middle"),
    ]
    assert [(item.subject_kind, item.subject_id) for item in result.failures] == [
        ("file", "z/Failure.gf")
    ]
    assert "OSError: simulated detail failure" in result.failures[0].message
    assert all(path.is_file() for path in result.paths)


def test_write_detail_reports_rejects_non_boolean_configuration(
    tmp_path: Path,
) -> None:
    run_root, details_root = _run_layout(tmp_path)
    run_result = SimpleNamespace(
        run_paths=_RunPaths(run_root, details_root),
        run_config=SimpleNamespace(keep_ok_details=1),
        file_results=(),
        scenario_results=(),
    )

    with pytest.raises(TypeError, match="RunConfig.keep_ok_details"):
        write_detail_reports(run_result)  # type: ignore[arg-type]


def test_compiler_warning_summary_groups_structural_sites() -> None:
    warnings = (
        CompileWarning(
            CompileWarningKind.STRUCTURAL_LOCK,
            "missing lock field lock_VP",
            source_path="ExtendSqi.gf",
            source_line=10,
            operation="demo",
        ),
        CompileWarning(
            CompileWarningKind.STRUCTURAL_LOCK,
            "missing lock field lock_VP",
            source_path="ExtendSqi.gf",
            source_line=10,
            operation="demo",
        ),
        CompileWarning(
            CompileWarningKind.NAMESPACE_CONFLICT,
            "atomic term Prep",
        ),
    )
    run_result = SimpleNamespace(
        file_results=(SimpleNamespace(compile_summary=SimpleNamespace(compiler_warnings=warnings)),)
    )

    summary = writer._compiler_warning_summary(run_result)

    assert summary["total"] == 3
    assert summary["structural_lock"] == 2
    assert summary["namespace_conflict"] == 1
    assert summary["other"] == 0
    assert summary["unique_structural_lock_sites"] == 1
    assert summary["structural_lock_sites"][0]["occurrences"] == 2
