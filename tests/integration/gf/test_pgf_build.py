from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.gf

_GF_EXECUTABLE_ENV = "GF_WORDBENCH_TEST_GF"
_TIMEOUT_SECONDS = 60.0


def _resolve_gf_executable() -> Path:
    configured = os.environ.get(_GF_EXECUTABLE_ENV, "").strip()
    if configured:
        executable = Path(configured).expanduser().resolve()
        if not executable.is_file():
            pytest.fail(
                f"{_GF_EXECUTABLE_ENV} does not identify a file: {executable}"
            )
        return executable

    discovered = shutil.which("gf")
    if discovered is None:
        pytest.skip(
            "real GF integration requires GF_WORDBENCH_TEST_GF or gf on PATH"
        )
    return Path(discovered).resolve()


def _write_grammar(
    root: Path,
    *,
    abstract_name: str,
    concrete_name: str,
    valid: bool = True,
) -> tuple[Path, Path]:
    abstract_path = root / f"{abstract_name}.gf"
    concrete_path = root / f"{concrete_name}.gf"

    abstract_path.write_text(
        "\n".join(
            (
                f"abstract {abstract_name} = {{",
                "  flags startcat = S ;",
                "  cat S ;",
                "  fun Hello : S ;",
                "}",
                "",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )

    linearization = '"hello"' if valid else "UndefinedLinearization"
    concrete_path.write_text(
        "\n".join(
            (
                f"concrete {concrete_name} of {abstract_name} = {{",
                "  lincat S = Str ;",
                f"  lin Hello = {linearization} ;",
                "}",
                "",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )

    return abstract_path, concrete_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_pgf_build(
    executable: Path,
    *,
    working_directory: Path,
    entrypoints: tuple[Path, ...],
) -> subprocess.CompletedProcess[bytes]:
    command = (
        str(executable),
        "-make",
        "-optimize-pgf",
        *(path.name for path in entrypoints),
    )
    environment = os.environ.copy()
    environment.pop("GF_LIB_PATH", None)

    return subprocess.run(
        command,
        cwd=working_directory,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=_TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )


def _failure_message(result: subprocess.CompletedProcess[bytes]) -> str:
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    return (
        f"command={result.args!r}\n"
        f"exit_code={result.returncode}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}"
    )


def test_real_gf_builds_current_non_empty_optimized_pgf(
    tmp_path: Path,
) -> None:
    executable = _resolve_gf_executable()
    grammar_root = tmp_path / "grammar"
    grammar_root.mkdir()

    abstract_path, concrete_path = _write_grammar(
        grammar_root,
        abstract_name="WordbenchMini",
        concrete_name="WordbenchMiniEng",
    )
    expected_pgf = grammar_root / "WordbenchMini.pgf"
    previous_pgf = tmp_path / "previous" / expected_pgf.name
    previous_pgf.parent.mkdir()
    previous_pgf.write_bytes(b"reviewed-previous-pgf")
    expected_pgf.write_bytes(b"stale-pgf")

    source_hashes = {
        abstract_path: _sha256(abstract_path),
        concrete_path: _sha256(concrete_path),
    }
    previous_hash = _sha256(previous_pgf)
    stale_hash = _sha256(expected_pgf)

    result = _run_pgf_build(
        executable,
        working_directory=grammar_root,
        entrypoints=(concrete_path,),
    )

    assert result.returncode == 0, _failure_message(result)
    assert expected_pgf.is_file(), _failure_message(result)
    assert expected_pgf.stat().st_size > 0
    assert _sha256(expected_pgf) != stale_hash
    assert _sha256(previous_pgf) == previous_hash
    assert {
        path: _sha256(path)
        for path in source_hashes
    } == source_hashes


def test_real_gf_rejects_invalid_pgf_entrypoint_without_false_artifact(
    tmp_path: Path,
) -> None:
    executable = _resolve_gf_executable()
    grammar_root = tmp_path / "invalid-grammar"
    grammar_root.mkdir()

    abstract_path, concrete_path = _write_grammar(
        grammar_root,
        abstract_name="WordbenchBroken",
        concrete_name="WordbenchBrokenEng",
        valid=False,
    )
    expected_pgf = grammar_root / "WordbenchBroken.pgf"
    source_hashes = {
        abstract_path: _sha256(abstract_path),
        concrete_path: _sha256(concrete_path),
    }

    result = _run_pgf_build(
        executable,
        working_directory=grammar_root,
        entrypoints=(concrete_path,),
    )

    assert result.returncode != 0 or not expected_pgf.exists(), (
        _failure_message(result)
    )
    assert not expected_pgf.exists(), _failure_message(result)
    assert result.stdout or result.stderr
    assert {
        path: _sha256(path)
        for path in source_hashes
    } == source_hashes
