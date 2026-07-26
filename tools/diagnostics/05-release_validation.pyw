"""N05 — Run Wordbench release validation and inspect its evidence."""

from __future__ import annotations

import json
from pathlib import Path

from diag_core import (
    BLOCKED,
    CONFIG_ERROR,
    ERROR,
    FAIL,
    PASS,
    WARN,
    DiagConfig,
    DiagReport,
    build_env,
    common_path_arguments,
    inspect_summary,
    newest_changed_summary,
    run_command,
    run_level_app,
    summary_snapshot,
    wordbench_command,
)

LEVEL_ID = "N05"
LEVEL_NAME = "Release Validation"
PURPOSE = "Run Wordbench's authoritative release mode and verify the resulting structured evidence."


def _exit_severity(code: int | None, status: str) -> tuple[str, str]:
    if status != PASS and code is None:
        return ERROR, "Release command could not complete"
    if code == 0:
        return PASS, "Wordbench release command completed successfully"
    if code == 1:
        return FAIL, "Wordbench evaluated the release and rejected it"
    if code == 2:
        return CONFIG_ERROR, "Wordbench rejected the invocation or configuration"
    if code == 3:
        return ERROR, "Wordbench reported a framework or execution error"
    if code == 4:
        return BLOCKED, "Wordbench release validation was cancelled"
    return ERROR, f"Wordbench returned unexpected exit code {code}"


def _nested(data, *path):
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    before = summary_snapshot(config)
    command = wordbench_command(
        config,
        "validate",
        "--mode",
        "release",
        "--strict",
        *common_path_arguments(config, include_output=True),
    )
    log("RUN authoritative Wordbench release validation")
    result = run_command(
        command,
        cwd=config.repo_root,
        timeout=config.timeout("release", 7200),
        env=build_env(config),
        name="Wordbench release validation",
    )
    report.steps.append(result)
    command_log = report.artifact_dir / "wordbench-release-command.log"
    command_log.write_text(result.output, encoding="utf-8", errors="replace")
    report.add_artifact("command-log", command_log, "Complete release command output")
    severity, message = _exit_severity(result.exit_code, result.status)
    report.add(
        "release.command",
        severity,
        "release",
        message,
        evidence=(result.output[-3000:].strip() or None),
        recommendation=None if severity == PASS else f"Review {command_log} and the Wordbench run evidence.",
        data={
            "command": command,
            "exit_code": result.exit_code,
            "duration_seconds": result.duration_seconds,
        },
    )

    summary = newest_changed_summary(config, before)
    if summary is None:
        report.add(
            "release.summary.discovered",
            FAIL,
            "evidence",
            "Release validation did not create or update a discoverable summary.json",
            recommendation="Configure output_root or summary_globs so the mini-suite can locate Wordbench run evidence.",
        )
        return

    report.add(
        "release.summary.discovered",
        PASS,
        "evidence",
        f"Release summary discovered: {summary}",
    )
    data = inspect_summary(report, summary, expected_mode="release", require_success=True)
    run_dir = summary.parent

    required_files = config.get("release.required_files", [])
    for filename in required_files:
        path = run_dir / str(filename)
        exists = path.is_file() and path.stat().st_size > 0
        report.add(
            f"release.artifact.{str(filename).replace('.', '-')}",
            PASS if exists else FAIL,
            "evidence",
            f"Required release artifact {'exists' if exists else 'is missing or empty'}: {filename}",
            evidence=str(path),
        )
        if exists:
            report.add_artifact("wordbench-release-artifact", path, str(filename))

    manifest_path = run_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("manifest root is not an object")
            report.add(
                "release.manifest.read",
                PASS,
                "evidence",
                "Release manifest is valid JSON",
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            report.add(
                "release.manifest.read",
                FAIL,
                "evidence",
                f"Release manifest is unreadable: {exc}",
            )

    require_pgf = config.get("release.require_pgf", None)
    if require_pgf is None and isinstance(data, dict):
        for path in (
            ("release_requires_pgf",),
            ("project", "release_requires_pgf"),
            ("release", "requires_pgf"),
        ):
            value = _nested(data, *path)
            if isinstance(value, bool):
                require_pgf = value
                break
    pgf_files = [path for path in run_dir.rglob("*.pgf") if path.is_file()]
    if require_pgf is True:
        report.add(
            "release.pgf",
            PASS if pgf_files else FAIL,
            "evidence",
            f"Required PGF artifact count: {len(pgf_files)}",
            evidence=", ".join(str(path) for path in pgf_files[:10]) or None,
        )
    elif require_pgf is False:
        report.add(
            "release.pgf",
            PASS,
            "evidence",
            "Project policy does not require a PGF artifact",
        )
    else:
        report.add(
            "release.pgf.policy",
            WARN,
            "evidence",
            "The mini-suite could not determine whether the project requires a PGF",
            recommendation="Set release.require_pgf in diag.config.local.json if the summary does not expose the policy.",
        )


if __name__ == "__main__":
    raise SystemExit(run_level_app(LEVEL_ID, LEVEL_NAME, PURPOSE, run_checks))
