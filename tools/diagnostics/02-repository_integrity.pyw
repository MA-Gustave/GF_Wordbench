"""N02 — Run the repository's static integrity checks."""

from __future__ import annotations

from pathlib import Path
import sys

from diag_core import (
    FAIL,
    DiagConfig,
    DiagReport,
    execute_python_module,
    execute_step,
    run_level_app,
)

LEVEL_ID = "N02"
LEVEL_NAME = "Repository Integrity"
PURPOSE = "Compile Python sources and run Wordbench's architecture, contract, schema, lint, and type checks."


def _required_script(config: DiagConfig, report: DiagReport, relative: str) -> Path | None:
    path = config.repo_root / relative
    if path.is_file():
        return path
    report.add(
        f"repository.script.{path.stem}.missing",
        FAIL,
        "repository",
        f"Required repository script is missing: {relative}",
    )
    return None


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    execute_step(
        config,
        report,
        log,
        step_id="repository.compileall",
        title="Compile Python sources",
        command=[
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "src",
            "tests",
            "scripts",
            "tools/diagnostics",
        ],
        timeout=config.timeout("normal", 180),
    )

    for relative, step_id, title in (
        ("scripts/verify_architecture.py", "repository.architecture", "Verify architecture"),
        ("scripts/validate_contracts.py", "repository.contracts", "Validate repository contracts"),
        ("scripts/validate_schemas.py", "repository.schemas", "Validate persisted schemas"),
    ):
        script = _required_script(config, report, relative)
        if script is not None:
            execute_step(
                config,
                report,
                log,
                step_id=step_id,
                title=title,
                command=[sys.executable, str(script)],
                timeout=config.timeout("normal", 180),
            )

    execute_python_module(
        config,
        report,
        log,
        module="ruff",
        arguments=["check", "."],
        step_id="repository.ruff",
        title="Ruff lint",
        timeout=config.timeout("normal", 180),
        required=False,
    )
    execute_python_module(
        config,
        report,
        log,
        module="mypy",
        arguments=[],
        step_id="repository.mypy",
        title="Mypy strict type check",
        timeout=config.timeout("tests", 1200),
        required=False,
    )


if __name__ == "__main__":
    raise SystemExit(run_level_app(LEVEL_ID, LEVEL_NAME, PURPOSE, run_checks))
