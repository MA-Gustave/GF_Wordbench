"""N04 — Exercise the public Wordbench runtime surfaces."""

from __future__ import annotations

import sys

from diag_core import (
    FAIL,
    PASS,
    SKIP,
    DiagConfig,
    DiagReport,
    common_path_arguments,
    execute_step,
    inspect_summary,
    newest_changed_summary,
    run_level_app,
    summary_snapshot,
    wordbench_command,
)

LEVEL_ID = "N04"
LEVEL_NAME = "Runtime Smoke"
PURPOSE = "Smoke-test public CLI and GUI imports, project checks, and an optional quick validation run."


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    short = config.timeout("short", 30)
    normal = config.timeout("normal", 180)
    execute_step(
        config,
        report,
        log,
        step_id="runtime.cli.help",
        title="Wordbench CLI help",
        command=wordbench_command(config, "--help"),
        timeout=short,
    )
    execute_step(
        config,
        report,
        log,
        step_id="runtime.gui.import",
        title="Wordbench GUI entrypoint import",
        command=[
            sys.executable,
            "-c",
            "import gf_wordbench.entrypoints.gui.main; print('GUI entrypoint import OK')",
        ],
        timeout=short,
    )
    execute_step(
        config,
        report,
        log,
        step_id="runtime.project.check",
        title="Active project contract check",
        command=wordbench_command(
            config,
            "project",
            "check",
            *common_path_arguments(config, include_output=False),
        ),
        timeout=normal,
    )
    execute_step(
        config,
        report,
        log,
        step_id="runtime.scenarios.check",
        title="Scenario contract check",
        command=wordbench_command(
            config,
            "scenarios",
            "check",
            "--project-root",
            str(config.project_root),
        ),
        timeout=normal,
    )
    execute_step(
        config,
        report,
        log,
        step_id="runtime.schemas.check",
        title="CLI schema check",
        command=wordbench_command(config, "schemas", "check"),
        timeout=normal,
    )

    if not bool(config.get("runtime_smoke.run_quick", False)):
        report.add(
            "runtime.quick.disabled",
            SKIP,
            "runtime",
            "Quick validation is disabled in diag.config.local.json",
            recommendation="Enable runtime_smoke.run_quick after configuring GF, RGL, output root, and an optional target.",
        )
        return

    before = summary_snapshot(config)
    args = ["validate", "--mode", "quick"]
    if bool(config.get("runtime_smoke.strict", False)):
        args.append("--strict")
    target = str(config.get("runtime_smoke.target", "")).strip()
    if target:
        args.extend(["--target", target])
    args.extend(common_path_arguments(config, include_output=True))
    execute_step(
        config,
        report,
        log,
        step_id="runtime.quick.run",
        title="Wordbench quick validation",
        command=wordbench_command(config, *args),
        timeout=config.timeout("quick", 900),
    )
    summary = newest_changed_summary(config, before)
    if summary is None:
        report.add(
            "runtime.quick.summary",
            FAIL,
            "evidence",
            "Quick validation did not create or update a discoverable summary.json",
            recommendation="Set output_root or summary_globs in diag.config.local.json.",
        )
    else:
        report.add(
            "runtime.quick.summary",
            PASS,
            "evidence",
            f"Quick run summary discovered: {summary}",
        )
        inspect_summary(report, summary, expected_mode="quick", require_success=True)


if __name__ == "__main__":
    raise SystemExit(run_level_app(LEVEL_ID, LEVEL_NAME, PURPOSE, run_checks))
