"""N04 — Exercise the public Wordbench runtime surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from diag_core import (
    BLOCKED,
    CONFIG_ERROR,
    FAIL,
    PASS,
    SKIP,
    DiagConfig,
    DiagReport,
    console_python,
    execute_step,
    inspect_summary,
    newest_changed_summary,
    run_level_app,
    summary_snapshot,
    wordbench_command,
)

LEVEL_ID = "N04"
LEVEL_NAME = "Runtime Smoke"
PURPOSE = (
    "Smoke-test public CLI and GUI imports, path-resolved language startup, "
    "optional validation-profile contracts, schema checks, and an optional "
    "quick validation run."
)


def _config_value(config: DiagConfig, name: str, default: Any = None) -> Any:
    """Read a migrated DiagConfig field with a raw-config fallback."""

    value = getattr(config, name, None)
    if value is not None:
        return value
    return config.get(name, default)


def _configured_path(config: DiagConfig, name: str) -> Path | None:
    """Resolve one optional diagnostic path relative to the repository root."""

    raw = _config_value(config, name, "")
    if raw is None:
        return None

    text = str(raw).strip()
    if not text:
        return None

    path = Path(text).expanduser()
    if not path.is_absolute():
        path = config.repo_root / path
    return path.resolve(strict=False)


def _environment_arguments(
    config: DiagConfig,
    *,
    include_output: bool,
) -> list[str]:
    """Build non-authoritative GF environment arguments for one CLI call."""

    arguments: list[str] = []
    if config.gf_executable:
        arguments.extend(["--gf-exe", config.gf_executable])
    if config.rgl_root is not None:
        arguments.extend(["--rgl-root", str(config.rgl_root)])
    if include_output and config.output_root is not None:
        arguments.extend(["--out-root", str(config.output_root)])
    return arguments


def _language_arguments(
    language_path: Path,
    validation_profile: Path | None,
) -> list[str]:
    """Build the explicit ADR-0015 language/profile selection arguments."""

    arguments = ["--language-path", str(language_path)]
    if validation_profile is not None:
        arguments.extend(["--profile", str(validation_profile)])
    return arguments


def _add_profile_skips(
    report: DiagReport,
    log,
    *,
    reason: str,
    recommendation: str,
    severity: str = SKIP,
) -> None:
    """Record profile-owned runtime checks that cannot or need not run."""

    for step_id, title in (
        ("runtime.project.check", "Validation-profile contract check"),
        ("runtime.scenarios.check", "Scenario contract check"),
        ("runtime.schemas.check", "Validation-profile schema check"),
    ):
        report.add(
            step_id,
            severity,
            "runtime",
            f"{title} skipped: {reason}",
            recommendation=recommendation,
        )
        log(f"{severity} {title}: {reason}")


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    short_timeout = config.timeout("short", 30)
    normal_timeout = config.timeout("normal", 180)

    execute_step(
        config,
        report,
        log,
        step_id="runtime.cli.help",
        title="Wordbench CLI help",
        command=wordbench_command(config, "--help"),
        timeout=short_timeout,
    )

    execute_step(
        config,
        report,
        log,
        step_id="runtime.gui.import",
        title="Wordbench GUI entrypoint import",
        command=[
            console_python(),
            "-c",
            (
                "import gf_wordbench.entrypoints.gui.main; "
                "print('GUI entrypoint import OK')"
            ),
        ],
        timeout=short_timeout,
    )

    language_path = _configured_path(config, "language_path")
    validation_profile = _configured_path(config, "validation_profile")

    if language_path is None:
        report.add(
            "runtime.language.configuration",
            CONFIG_ERROR,
            "configuration",
            "N04 requires one explicit GF language directory or .gf file",
            recommendation=(
                "Set language_path in diag.config.local.json or define "
                "WORDBENCH_DIAG_LANGUAGE_PATH."
            ),
        )
        log("CONFIG_ERROR N04 requires language_path")
        _add_profile_skips(
            report,
            log,
            reason="no language path is configured",
            recommendation="Configure language_path, then rerun N04.",
            severity=BLOCKED,
        )
        report.add(
            "runtime.quick.blocked",
            BLOCKED,
            "runtime",
            "Quick validation is blocked because no language path is configured",
            recommendation="Configure language_path, then rerun N04.",
        )
        return

    usable_profile = validation_profile
    if validation_profile is not None and not validation_profile.is_file():
        report.add(
            "runtime.profile.configuration",
            CONFIG_ERROR,
            "configuration",
            "The configured validation profile is not a readable file",
            evidence=str(validation_profile),
            recommendation=(
                "Correct validation_profile or leave it empty for a "
                "language-only runtime smoke test."
            ),
        )
        log(f"CONFIG_ERROR invalid validation profile: {validation_profile}")
        usable_profile = None

    probe_arguments = [
        "language",
        "probe",
        str(language_path),
    ]
    if usable_profile is not None:
        probe_arguments.extend(["--profile", str(usable_profile)])
    probe_arguments.extend(
        _environment_arguments(config, include_output=False)
    )

    probe_result = execute_step(
        config,
        report,
        log,
        step_id="runtime.language.probe",
        title="Path-resolved language probe",
        command=wordbench_command(config, *probe_arguments),
        timeout=normal_timeout,
    )

    if probe_result.exit_code != 0:
        _add_profile_skips(
            report,
            log,
            reason="the language path did not resolve successfully",
            recommendation=(
                "Correct language_path and the language-probe failure before "
                "checking profile-owned contracts."
            ),
            severity=BLOCKED,
        )
        report.add(
            "runtime.quick.blocked",
            BLOCKED,
            "runtime",
            "Quick validation is blocked by the failed language probe",
            recommendation="Correct the language-probe failure, then rerun N04.",
        )
        return

    if validation_profile is None:
        _add_profile_skips(
            report,
            log,
            reason="no optional validation profile is configured",
            recommendation=(
                "Set validation_profile only when profile, scenario, and "
                "profile-schema contracts should be checked."
            ),
        )
    elif usable_profile is None:
        _add_profile_skips(
            report,
            log,
            reason="the configured validation profile is invalid",
            recommendation="Correct validation_profile, then rerun N04.",
            severity=BLOCKED,
        )
    else:
        startup_arguments = _language_arguments(
            language_path,
            usable_profile,
        )

        execute_step(
            config,
            report,
            log,
            step_id="runtime.project.check",
            title="Validation-profile contract check",
            command=wordbench_command(
                config,
                "project",
                "check",
                *startup_arguments,
                *_environment_arguments(config, include_output=False),
            ),
            timeout=normal_timeout,
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
                *startup_arguments,
            ),
            timeout=normal_timeout,
        )

        execute_step(
            config,
            report,
            log,
            step_id="runtime.schemas.check",
            title="Validation-profile schema check",
            command=wordbench_command(
                config,
                "schemas",
                "check",
                str(usable_profile),
            ),
            timeout=normal_timeout,
        )

    if not bool(config.get("runtime_smoke.run_quick", False)):
        report.add(
            "runtime.quick.disabled",
            SKIP,
            "runtime",
            "Quick validation is disabled in diag.config.local.json",
            recommendation=(
                "Enable runtime_smoke.run_quick only after configuring GF, "
                "RGL, the output root, and any required quick target."
            ),
        )
        return

    target_value = config.get("runtime_smoke.target", "")
    target = "" if target_value is None else str(target_value).strip()

    if not target and language_path.suffix.casefold() != ".gf":
        report.add(
            "runtime.quick.target-missing",
            CONFIG_ERROR,
            "configuration",
            (
                "Quick validation is enabled for a language directory but "
                "runtime_smoke.target is empty"
            ),
            recommendation=(
                "Set runtime_smoke.target to one explicit source target, or "
                "configure language_path as the target .gf file."
            ),
        )
        log("CONFIG_ERROR Quick validation requires runtime_smoke.target")
        return

    if validation_profile is not None and usable_profile is None:
        report.add(
            "runtime.quick.blocked",
            BLOCKED,
            "runtime",
            "Quick validation is blocked by the invalid validation profile",
            recommendation="Correct validation_profile, then rerun N04.",
        )
        return

    before = summary_snapshot(config)

    arguments = [
        "validate",
        *_language_arguments(language_path, usable_profile),
        "--mode",
        "quick",
    ]

    if target:
        arguments.extend(["--target", target])

    if bool(config.get("runtime_smoke.strict", False)):
        arguments.append("--strict")

    arguments.extend(
        _environment_arguments(config, include_output=True)
    )

    execute_step(
        config,
        report,
        log,
        step_id="runtime.quick.run",
        title="Wordbench quick validation",
        command=wordbench_command(config, *arguments),
        timeout=config.timeout("quick", 900),
    )

    summary_path = newest_changed_summary(config, before)

    if summary_path is None:
        report.add(
            "runtime.quick.summary",
            FAIL,
            "evidence",
            (
                "Quick validation did not create or update a discoverable "
                "summary.json"
            ),
            recommendation=(
                "Verify the Wordbench output root and the configured "
                "summary_globs."
            ),
        )
        return

    report.add(
        "runtime.quick.summary",
        PASS,
        "evidence",
        f"Quick run summary discovered: {summary_path}",
    )

    inspect_summary(
        report,
        summary_path,
        expected_mode="quick",
        require_success=True,
    )


if __name__ == "__main__":
    raise SystemExit(
        run_level_app(
            LEVEL_ID,
            LEVEL_NAME,
            PURPOSE,
            run_checks,
        )
    )
