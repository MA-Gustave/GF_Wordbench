"""N01 — Verify the local Wordbench environment."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

from diag_core import (
    BLOCKED,
    FAIL,
    PASS,
    WARN,
    DiagConfig,
    DiagReport,
    executable_available,
    execute_step,
    module_available,
    run_level_app,
)

LEVEL_ID = "N01"
LEVEL_NAME = "Environment"
PURPOSE = "Verify Python, repository paths, GF, development tools, and public imports."


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    version = sys.version_info
    supported = (3, 11) <= version[:2] < (3, 15)
    report.add(
        "environment.python.version",
        PASS if supported else FAIL,
        "environment",
        f"Python {version.major}.{version.minor}.{version.micro}",
        recommendation=None if supported else "Use Python 3.11 through 3.14.",
    )

    root_valid = (config.repo_root / "pyproject.toml").is_file() and (
        config.repo_root / "src" / "gf_wordbench"
    ).is_dir()
    report.add(
        "environment.repository.root",
        PASS if root_valid else FAIL,
        "environment",
        f"Detected repository root: {config.repo_root}",
        recommendation=None if root_valid else "Extract the suite at the GF Wordbench repository root.",
    )

    for relative in config.get("required_paths", []):
        path = config.repo_root / str(relative)
        report.add(
            f"environment.path.{str(relative).replace('/', '.')}",
            PASS if path.exists() else FAIL,
            "paths",
            f"Required path {'exists' if path.exists() else 'is missing'}: {relative}",
            evidence=str(path),
        )

    try:
        config.artifact_root.mkdir(parents=True, exist_ok=True)
        probe = config.artifact_root / ".write-probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        report.add(
            "environment.artifacts.write",
            PASS,
            "paths",
            f"Artifact directory is writable: {config.artifact_root}",
        )
    except OSError as exc:
        report.add(
            "environment.artifacts.write",
            FAIL,
            "paths",
            f"Artifact directory is not writable: {exc}",
            evidence=str(config.artifact_root),
        )

    execute_step(
        config,
        report,
        log,
        step_id="environment.wordbench.import",
        title="Import gf_wordbench",
        command=[
            sys.executable,
            "-c",
            "import gf_wordbench; print(getattr(gf_wordbench, '__version__', 'imported'))",
        ],
        timeout=config.timeout("short", 30),
    )
    execute_step(
        config,
        report,
        log,
        step_id="environment.wordbench.cli-version",
        title="Wordbench CLI version",
        command=[sys.executable, "-m", "gf_wordbench", "--version"],
        timeout=config.timeout("short", 30),
    )

    if executable_available(config.gf_executable):
        result = execute_step(
            config,
            report,
            log,
            step_id="environment.gf.version",
            title="GF executable version",
            command=[config.gf_executable, "--version"],
            timeout=config.timeout("short", 30),
        )
        if result.exit_code not in {0, None}:
            execute_step(
                config,
                report,
                log,
                step_id="environment.gf.version-fallback",
                title="GF executable version fallback",
                command=[config.gf_executable, "-v"],
                timeout=config.timeout("short", 30),
                required=False,
            )
    else:
        report.add(
            "environment.gf.available",
            BLOCKED,
            "toolchain",
            f"GF executable is unavailable: {config.gf_executable}",
            recommendation="Set WORDBENCH_DIAG_GF_EXECUTABLE or diag.config.local.json.",
        )

    if config.rgl_root is None:
        report.add(
            "environment.rgl.configured",
            WARN,
            "toolchain",
            "RGL root is not configured in the mini-suite",
            recommendation="Set rgl_root when Wordbench cannot resolve it from its own state or environment.",
        )
    else:
        report.add(
            "environment.rgl.path",
            PASS if config.rgl_root.is_dir() else FAIL,
            "toolchain",
            f"RGL root: {config.rgl_root}",
        )

    for tool in ("git",):
        available = shutil.which(tool) is not None
        report.add(
            f"environment.tool.{tool}",
            PASS if available else WARN,
            "tooling",
            f"{tool} {'is available' if available else 'is not available'}",
        )
    for module in ("pytest", "ruff", "mypy", "PySide6"):
        available = module_available(module)
        report.add(
            f"environment.module.{module.lower()}",
            PASS if available else WARN,
            "tooling",
            f"Python module {module} {'is installed' if available else 'is not installed'}",
            recommendation=None if available else "Install the Wordbench development dependencies.",
        )


if __name__ == "__main__":
    raise SystemExit(run_level_app(LEVEL_ID, LEVEL_NAME, PURPOSE, run_checks))
