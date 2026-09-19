"""Real-GF integration coverage for Unicode paths, sources, and evidence."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
from typing import Final

import pytest

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessInputKind,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.runner import run_process
from gf_wordbench.kernel.ids import SectionId, validate_section_id
from gf_wordbench.kernel.statuses import ExecutionState
from gf_wordbench.validation.compilation.commands import (
    GfCommand,
    GfCommandProfile,
    ValueOptionStyle,
    build_module_compile_command,
)
from gf_wordbench.validation.scenarios.execution import (
    ScenarioScriptInput,
    build_scenario_process_request,
    execute_scenario_process,
)
from gf_wordbench.validation.scenarios.markers import (
    format_begin_marker,
    format_end_marker,
    validate_scenario_markers,
)
from gf_wordbench.validation.scenarios.normalization import (
    DEFAULT_NORMALIZATION_PROFILE,
    ExtractedScenarioSection,
    normalize_scenario_section,
)

pytestmark = pytest.mark.gf

_GF_EXECUTABLE_ENV: Final[str] = "GF_WORDBENCH_TEST_GF_EXE"
_TIMEOUT_SECONDS: Final[float] = 30.0
_OUTPUT_LIMIT_BYTES: Final[int] = 2 * 1024 * 1024
_MODULE_NAME: Final[str] = "UnicodeRoundTrip"
_CONCRETE_MODULE_NAME: Final[str] = f"{_MODULE_NAME}Eng"
_SCENARIO_ID: Final[str] = "integration-unicode"
_SECTION_ID: Final[SectionId] = validate_section_id("unicode-roundtrip")
_EXPECTED_TEXT: Final[str] = "élève naïve — cœur · Ελληνικά 日本語 العربية"
_UTF8_BOM: Final[bytes] = b"\xef\xbb\xbf"


def _resolve_test_gf_executable() -> Path:
    configured = os.environ.get(_GF_EXECUTABLE_ENV, "").strip()
    if not configured:
        pytest.skip(f"real GF integration requires {_GF_EXECUTABLE_ENV} to name the GF executable")

    candidate = Path(os.path.expandvars(configured)).expanduser()
    if not candidate.is_absolute():
        discovered = shutil.which(configured)
        if discovered is None:
            pytest.fail(f"{_GF_EXECUTABLE_ENV}={configured!r} does not resolve to an executable")
        candidate = Path(discovered)

    try:
        executable = candidate.resolve(strict=True)
    except OSError as exc:
        pytest.fail(
            f"{_GF_EXECUTABLE_ENV} does not resolve to an existing file: {candidate}: {exc}"
        )

    if not executable.is_file():
        pytest.fail(f"{_GF_EXECUTABLE_ENV} must identify a regular file: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        pytest.fail(f"configured GF executable is not executable: {executable}")

    return executable


def _command_profile() -> GfCommandProfile:
    return GfCommandProfile(
        profile_id="integration-unicode",
        path_separator=os.pathsep,
        value_option_style=ValueOptionStyle.EQUALS,
        gfo_dir_option="--gfo-dir",
        output_dir_option="--output-dir",
    )


def _write_utf8(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    payload = path.read_bytes()
    assert not payload.startswith(_UTF8_BOM)
    assert payload.decode("utf-8", errors="strict") == text
    return path


def _write_grammar(source_root: Path) -> tuple[Path, Path]:
    abstract_path = _write_utf8(
        source_root / f"{_MODULE_NAME}.gf",
        f"abstract {_MODULE_NAME} = {{\n"
        "  flags startcat = Utt ;\n"
        "  cat Utt ;\n"
        "  fun Greeting : Utt ;\n"
        "}\n",
    )
    concrete_path = _write_utf8(
        source_root / f"{_CONCRETE_MODULE_NAME}.gf",
        f"concrete {_CONCRETE_MODULE_NAME} of {_MODULE_NAME} = {{\n"
        "  lincat Utt = Str ;\n"
        f'  lin Greeting = "{_EXPECTED_TEXT}" ;\n'
        "}\n",
    )
    return abstract_path, concrete_path


def _source_hashes(paths: tuple[Path, ...]) -> dict[Path, str]:
    return {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def _assert_sources_unchanged(expected: dict[Path, str]) -> None:
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in expected} == expected


def _build_compile_command(
    *,
    executable: Path,
    source_root: Path,
    concrete_path: Path,
    gfo_root: Path,
    output_root: Path,
) -> GfCommand:
    return build_module_compile_command(
        executable=executable,
        working_directory=source_root,
        source_file=concrete_path,
        gf_search_paths=(source_root,),
        profile=_command_profile(),
        gfo_dir=gfo_root,
        output_dir=output_root,
        quiet=True,
        emit_cpu_stats=False,
    )


def _assert_unicode_command_paths(
    command: GfCommand,
    *,
    source_root: Path,
    concrete_path: Path,
    gfo_root: Path,
    output_root: Path,
) -> None:
    expected_arguments = {
        f"--path={source_root}",
        f"--gfo-dir={gfo_root}",
        f"--output-dir={output_root}",
        os.fspath(concrete_path),
    }

    assert any(ord(character) > 127 for character in os.fspath(source_root))
    assert expected_arguments.issubset(command.arguments)
    assert command.working_directory == source_root
    assert command.gf_search_paths == (source_root,)
    assert command.argv == (os.fspath(command.executable), *command.arguments)
    assert all("\x00" not in argument for argument in command.arguments)
    assert all(
        not (len(argument) >= 2 and argument[0] == argument[-1] and argument[0] in {'"', "'"})
        for argument in command.arguments
    )


def _read_strict_utf8(path: Path) -> tuple[bytes, str]:
    assert path.is_file(), f"missing process evidence: {path}"
    payload = path.read_bytes()
    text = payload.decode("utf-8", errors="strict")
    assert "\ufffd" not in text
    return payload, text


def _scenario_script() -> str:
    return (
        f"i {_CONCRETE_MODULE_NAME}.gf\n"
        f'ps "{format_begin_marker(_SECTION_ID)}"\n'
        "l Greeting\n"
        f'ps "{format_end_marker(_SECTION_ID)}"\n'
        "q\n"
    )


def _extract_section_text(output: str) -> str:
    lines = output.splitlines()
    begin_marker = format_begin_marker(_SECTION_ID)
    end_marker = format_end_marker(_SECTION_ID)

    begin_index = lines.index(begin_marker)
    end_index = lines.index(end_marker, begin_index + 1)
    section_lines = lines[begin_index + 1 : end_index]

    assert section_lines
    return "\n".join(section_lines) + "\n"


def test_real_gf_compiles_from_unicode_paths_without_mutating_sources(
    tmp_path: Path,
) -> None:
    executable = _resolve_test_gf_executable()

    source_root = (tmp_path / "projet-épreuve-世界" / "sources-grammaire").resolve()
    run_root = (tmp_path / "résultats-δοκιμή-日本").resolve()
    gfo_root = run_root / "artefacts-compilés"
    output_root = run_root / "sorties-générales"
    log_root = run_root / "preuves-brutes"

    for directory in (source_root, gfo_root, output_root, log_root):
        directory.mkdir(parents=True, exist_ok=True)

    abstract_path, concrete_path = _write_grammar(source_root)
    expected_gfo = gfo_root / f"{_CONCRETE_MODULE_NAME}.gfo"
    stdout_path = log_root / "compilation-sortie-é.out.txt"
    stderr_path = log_root / "compilation-erreur-é.err.txt"
    source_hashes = _source_hashes((abstract_path, concrete_path))

    command = _build_compile_command(
        executable=executable,
        source_root=source_root,
        concrete_path=concrete_path,
        gfo_root=gfo_root,
        output_root=output_root,
    )
    _assert_unicode_command_paths(
        command,
        source_root=source_root,
        concrete_path=concrete_path,
        gfo_root=gfo_root,
        output_root=output_root,
    )

    request = ProcessRequest(
        request_id="integration-gf-unicode-compile",
        tool_id="gf",
        operation_id="compile-unicode-paths",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=command.executable,
        args=command.arguments,
        cwd=command.working_directory,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=_TIMEOUT_SECONDS,
        approved_read_roots=(source_root, executable.parent),
        approved_write_roots=(run_root,),
        evidence_policy="retain-raw-streams-v1",
        environment_policy="controlled-inherit-v1",
        env_removals=frozenset({"GF_LIB_PATH"}),
        expected_artifacts=(
            ArtifactExpectation(
                path=expected_gfo,
                role="gfo",
                required=True,
                kind=ArtifactKind.FILE,
                minimum_size_bytes=1,
            ),
        ),
        metadata={
            "gf_operation_kind": "compile_module",
            "target_module": _CONCRETE_MODULE_NAME,
            "unicode_contract": "paths-and-source",
        },
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )

    result = run_process(request)

    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.capture_complete is True
    assert result.output_limit_exceeded is False
    assert result.launch_error_kind is None
    assert result.launch_error_message == ""
    assert result.cancellation_reason is None
    assert result.executable == executable
    assert result.args == command.arguments
    assert result.cwd == source_root

    stdout_bytes, _stdout = _read_strict_utf8(stdout_path)
    stderr_bytes, _stderr = _read_strict_utf8(stderr_path)
    assert result.stdout_size_bytes == len(stdout_bytes)
    assert result.stderr_size_bytes == len(stderr_bytes)

    assert len(result.artifact_observations) == 1
    observation = result.artifact_observations[0]
    assert observation.path == expected_gfo
    assert observation.role == "gfo"
    assert observation.required is True
    assert observation.exists is True
    assert observation.kind_matches is True
    assert observation.size_bytes is not None
    assert observation.size_bytes > 0
    assert expected_gfo.is_file()
    assert expected_gfo.stat().st_size == observation.size_bytes

    _assert_sources_unchanged(source_hashes)
    assert not (source_root / expected_gfo.name).exists()


def test_real_gf_preserves_linguistic_unicode_through_scenario_and_normalization(
    tmp_path: Path,
) -> None:
    executable = _resolve_test_gf_executable()

    source_root = (tmp_path / "scénarios-世界" / "grammaire-épreuve").resolve()
    evidence_root = (tmp_path / "preuves-entrée-sortie" / "δοκιμή-日本語" / "raw").resolve()
    source_root.mkdir(parents=True)
    evidence_root.mkdir(parents=True)

    abstract_path, concrete_path = _write_grammar(source_root)
    script_path = _write_utf8(
        source_root / "scénario-linéarisation-日本語.gfs",
        _scenario_script(),
    )
    stdout_path = evidence_root / "résultat-unicode.out.txt"
    stderr_path = evidence_root / "erreur-unicode.err.txt"
    source_hashes = _source_hashes((abstract_path, concrete_path, script_path))

    script = ScenarioScriptInput.from_bytes(
        scenario_id=_SCENARIO_ID,
        script_path=script_path,
        content=script_path.read_bytes(),
    )
    request = build_scenario_process_request(
        script,
        executable=executable,
        args=(),
        working_directory=source_root,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_sec=_TIMEOUT_SECONDS,
        output_limit_bytes=_OUTPUT_LIMIT_BYTES,
        approved_read_roots=(source_root, executable.parent),
        approved_write_roots=(evidence_root,),
        request_id="integration-gf-unicode-scenario",
        operation_id="scenario-unicode-roundtrip",
        env_removals=frozenset({"GF_LIB_PATH"}),
        metadata={
            "fixture_kind": "real-gf",
            "unicode_contract": "utf8-roundtrip",
        },
    )

    assert request.operation_kind is ProcessOperationKind.SCENARIO
    assert request.stdin.kind is ProcessInputKind.TEXT
    assert request.stdin.encoding.casefold().replace("_", "-") == "utf-8"
    assert request.stdin.text == script_path.read_text(encoding="utf-8")
    assert request.stdin.path is None
    assert request.cwd == source_root
    assert request.metadata["scenario_id"] == _SCENARIO_ID
    assert request.metadata["script_path"] == script_path.as_posix()
    assert request.metadata["script_sha256"] == hashlib.sha256(script_path.read_bytes()).hexdigest()

    result = execute_scenario_process(request)

    assert result.operation_kind is ProcessOperationKind.SCENARIO
    assert result.execution_state is ExecutionState.COMPLETED
    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.cancelled is False
    assert result.output_limit_exceeded is False
    assert result.capture_complete is True
    assert result.executable == executable
    assert result.args == ()
    assert result.cwd == source_root
    assert result.stdout_path == stdout_path
    assert result.stderr_path == stderr_path

    stdout_bytes, stdout = _read_strict_utf8(stdout_path)
    stderr_bytes, _stderr = _read_strict_utf8(stderr_path)
    assert result.stdout_size_bytes == len(stdout_bytes)
    assert result.stderr_size_bytes == len(stderr_bytes)
    assert _EXPECTED_TEXT.encode("utf-8") in stdout_bytes
    assert _EXPECTED_TEXT in stdout

    markers = validate_scenario_markers(
        stdout,
        (_SECTION_ID,),
        raw_output_path=stdout_path,
    )
    assert markers.valid is True
    assert markers.complete is True
    assert tuple(map(str, markers.completed_section_ids)) == (_SECTION_ID,)
    assert markers.raw_output_path == stdout_path

    extracted_text = _extract_section_text(stdout)
    assert _EXPECTED_TEXT in extracted_text

    normalized = normalize_scenario_section(
        ExtractedScenarioSection(
            section_id=_SECTION_ID,
            text=extracted_text,
            source_evidence=stdout_path.as_posix(),
        ),
        profile=DEFAULT_NORMALIZATION_PROFILE,
    )

    assert normalized.normalized_text == extracted_text
    assert _EXPECTED_TEXT in normalized.normalized_text
    assert normalized.changed is False
    assert normalized.source_size_bytes == len(extracted_text.encode("utf-8"))
    assert normalized.normalized_size_bytes == normalized.source_size_bytes
    assert normalized.source_sha256 == hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()
    assert normalized.normalized_sha256 == normalized.source_sha256

    _assert_sources_unchanged(source_hashes)
