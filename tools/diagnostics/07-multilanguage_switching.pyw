"""N07 — Validate clean language replacement and cross-language isolation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from diag_core import (
    BLOCKED,
    PASS,
    SKIP,
    DiagConfig,
    DiagReport,
    console_python,
    execute_python_module,
    execute_step,
    module_available,
    run_level_app,
    wordbench_command,
)

LEVEL_ID = "N07"
LEVEL_NAME = "Multilanguage Switching"
PURPOSE = (
    "Verify explicit English-to-second-language replacement, active-run blocking, "
    "runtime disposal, failure behavior, and complete path, target, scenario, and "
    "context isolation."
)

_SWITCHING_CONTRACT_PROBE = r"""

from gf_wordbench.entrypoints.gui import startup

switcher = getattr(startup, "LanguageRuntimeSwitcher", None)
if not isinstance(switcher, type):
    raise SystemExit("LanguageRuntimeSwitcher is missing")

for name in ("open_language", "switch_language", "shutdown"):
    if not callable(getattr(switcher, name, None)):
        raise SystemExit(f"LanguageRuntimeSwitcher.{name} is missing")

for name in ("active_context", "active_runtime"):
    if getattr(switcher, name, None) is None:
        raise SystemExit(f"LanguageRuntimeSwitcher.{name} is missing")

services = getattr(startup, "StartupServices", None)
if not isinstance(services, type):
    raise SystemExit("StartupServices is missing")

service_signature = inspect.signature(services)
if "has_active_run" not in service_signature.parameters:
    raise SystemExit(
        "StartupServices must expose has_active_run so replacement can be "
        "rejected during an active run"
    )

disposition = getattr(startup, "LanguageSwitchDisposition", None)
if disposition is None:
    raise SystemExit("LanguageSwitchDisposition is missing")

expected = {"opened", "switched", "busy"}
actual = {
    str(getattr(value, "value", value)).strip().casefold()
    for value in disposition
}
if actual != expected:
    raise SystemExit(f"unexpected LanguageSwitchDisposition values: {sorted(actual)}")

print("Canonical multilanguage switching API: OK")
""".strip()


def _require_gui_dependencies(report: DiagReport, log) -> bool:
    missing = [
        name
        for name in ("pytest", "PySide6")
        if not module_available(name)
    ]
    if not missing:
        return True
    report.add(
        "multilanguage.dependencies",
        BLOCKED,
        "tooling",
        "Required GUI test dependencies are unavailable",
        evidence=", ".join(missing),
        recommendation=(
            "Install the declared project and development dependencies with "
            '`pip install -e ".[dev]"`.'
        ),
    )
    log(f"BLOCKED Missing GUI test dependencies: {', '.join(missing)}")
    return False


def _config_value(config: DiagConfig, name: str, default: Any = None) -> Any:
    value = getattr(config, name, None)
    if value is not None:
        return value
    return config.get(name, default)


def _configured_path(config: DiagConfig, name: str) -> Path | None:
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


def _candidate_source_roots(config: DiagConfig) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if config.rgl_root is not None:
        candidates.append(Path(config.rgl_root) / "src")
    candidates.extend(
        (
            config.repo_root / "gf-rgl" / "src",
            config.repo_root.parent / "gf-rgl" / "src",
            config.repo_root.parent.parent / "gf-rgl" / "src",
        )
    )

    result: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        normalized = candidate.expanduser().resolve(strict=False)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _language_directory(path: Path) -> Path:
    return path.parent if path.suffix.casefold() == ".gf" else path


def _resolve_real_language_pair(
    config: DiagConfig,
) -> tuple[Path | None, Path | None, str]:
    primary = _configured_path(config, "language_path")
    source = "configured_language_path" if primary is not None else "unresolved"

    if primary is None:
        for source_root in _candidate_source_roots(config):
            english = (source_root / "english").resolve(strict=False)
            if english.is_dir():
                primary = english
                source = "diagnostic_english_fallback"
                break

    secondary = _configured_path(config, "multilanguage.second_language_path")
    if secondary is None and primary is not None:
        source_root = _language_directory(primary).parent
        for directory_name in ("french", "german", "spanish"):
            candidate = (source_root / directory_name).resolve(strict=False)
            if candidate.is_dir():
                secondary = candidate
                break

    return primary, secondary, source


def _environment_arguments(config: DiagConfig) -> list[str]:
    arguments: list[str] = []
    if config.gf_executable:
        arguments.extend(["--gf-exe", config.gf_executable])
    if config.rgl_root is not None:
        arguments.extend(["--rgl-root", str(config.rgl_root)])
    return arguments


def _add_junit(report: DiagReport, path: Path, description: str) -> None:
    if path.is_file() and path.stat().st_size > 0:
        report.add_artifact("junit", path, description)


def _run_pytest(
    config: DiagConfig,
    report: DiagReport,
    log,
    *,
    step_id: str,
    title: str,
    arguments: list[str],
) -> None:
    junit_path = report.artifact_dir / f"{step_id.replace('.', '-')}.xml"
    result = execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=[
            "-q",
            "-ra",
            "--tb=short",
            *arguments,
            f"--junitxml={junit_path}",
        ],
        step_id=step_id,
        title=title,
        timeout=config.timeout("tests", 1200),
        required=True,
    )
    if result is not None:
        _add_junit(report, junit_path, title)


def _run_real_pair_probes(
    config: DiagConfig,
    report: DiagReport,
    log,
) -> None:
    primary, secondary, source = _resolve_real_language_pair(config)
    report.metadata["multilanguage_primary_path"] = (
        str(primary) if primary is not None else None
    )
    report.metadata["multilanguage_secondary_path"] = (
        str(secondary) if secondary is not None else None
    )
    report.metadata["multilanguage_primary_source"] = source

    if primary is None or secondary is None:
        report.add(
            "multilanguage.real-pair.configuration",
            SKIP,
            "configuration",
            "A real two-language RGL pair is not available for optional probe evidence",
            evidence=(
                f"primary={primary!s}; secondary={secondary!s}; "
                f"source={source}"
            ),
            recommendation=(
                "Set language_path and multilanguage.second_language_path, or "
                "provide sibling English and French RGL directories."
            ),
        )
        return

    report.add(
        "multilanguage.real-pair.configuration",
        PASS,
        "configuration",
        "Resolved a real two-language pair for additional probe evidence",
        evidence=f"{primary} -> {secondary}",
    )

    environment_arguments = _environment_arguments(config)
    for label, path in (("primary", primary), ("secondary", secondary)):
        execute_step(
            config,
            report,
            log,
            step_id=f"multilanguage.real-probe.{label}",
            title=f"Probe real {label} language",
            command=wordbench_command(
                config,
                "language",
                "probe",
                str(path),
                *environment_arguments,
            ),
            timeout=config.timeout("normal", 180),
        )


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    if not _require_gui_dependencies(report, log):
        return

    previous_platform = os.environ.get("QT_QPA_PLATFORM")
    if previous_platform is None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    report.metadata["qt_qpa_platform"] = os.environ.get("QT_QPA_PLATFORM")

    try:
        execute_step(
            config,
            report,
            log,
            step_id="multilanguage.public-contract",
            title="Canonical multilanguage switching public contract",
            command=[
                console_python(),
                "-c",
                _SWITCHING_CONTRACT_PROBE,
            ],
            timeout=config.timeout("short", 30),
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="multilanguage.gui-switching-tests",
            title="GUI language replacement integration tests",
            arguments=["tests/integration/gui/test_language_switching.py"],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="multilanguage.path-resolution-tests",
            title="Path-resolved English and second-language isolation tests",
            arguments=[
                "tests/integration/end_to_end/"
                "test_path_resolved_language_startup.py"
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="multilanguage.probe-unit-tests",
            title="Language probe unit tests",
            arguments=["tests/unit/projects/test_language_probe.py"],
        )
        _run_real_pair_probes(config, report, log)
    finally:
        if previous_platform is None:
            os.environ.pop("QT_QPA_PLATFORM", None)
        else:
            os.environ["QT_QPA_PLATFORM"] = previous_platform


if __name__ == "__main__":
    raise SystemExit(
        run_level_app(
            LEVEL_ID,
            LEVEL_NAME,
            PURPOSE,
            run_checks,
        )
    )
