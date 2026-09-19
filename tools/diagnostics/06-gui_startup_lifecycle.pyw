"""N06 — Validate the path-resolved GUI startup lifecycle."""

from __future__ import annotations

import os
from pathlib import Path

from diag_core import (
    BLOCKED,
    DiagConfig,
    DiagReport,
    console_python,
    execute_python_module,
    execute_step,
    module_available,
    run_level_app,
)

LEVEL_ID = "N06"
LEVEL_NAME = "GUI Startup Lifecycle"
PURPOSE = (
    "Verify the canonical GUI startup API, inert pre-launch construction, introduction "
    "window ordering, explicit language opening, executable Quick-runtime composition, "
    "and clean shutdown."
)

_STARTUP_CONTRACT_PROBE = r"""
import inspect
import weakref

from gf_wordbench import bootstrap
from gf_wordbench.entrypoints.gui import startup

factory = getattr(bootstrap, "build_gui_startup_runtime", None)
if not callable(factory):
    raise SystemExit("bootstrap.build_gui_startup_runtime is missing or not callable")

for legacy_name in ("build_gui_runtime", "build_startup_gui_runtime"):
    if hasattr(bootstrap, legacy_name):
        raise SystemExit(f"deprecated bootstrap symbol remains exported: {legacy_name}")

startup_factory = getattr(startup, "build_startup_runtime", None)
if not callable(startup_factory):
    raise SystemExit("startup.build_startup_runtime is missing or not callable")

signature = inspect.signature(startup_factory)
try:
    signature.bind(object(), ())
except TypeError as exc:
    raise SystemExit(
        "build_startup_runtime must accept application and argv without another "
        f"required argument; detected {signature}: {exc}"
    ) from exc

runtime_type = getattr(startup, "PathResolvedGuiRuntime", None)
if not isinstance(runtime_type, type):
    raise SystemExit("PathResolvedGuiRuntime is missing")

for name in ("start", "shutdown"):
    if not callable(getattr(runtime_type, name, None)):
        raise SystemExit(f"PathResolvedGuiRuntime.{name} is missing")

window_property = getattr(runtime_type, "window", None)
if window_property is None:
    raise SystemExit("PathResolvedGuiRuntime.window is missing")

controller_type = getattr(startup, "_StartupController", None)
if not isinstance(controller_type, type):
    raise SystemExit("_StartupController is missing")
try:
    weakref.ref(object.__new__(controller_type))
except TypeError as exc:
    raise SystemExit(
        "_StartupController must support weak references for PySide6 bound-slot connections: "
        f"{exc}"
    ) from exc

print("Canonical GUI startup API: OK")
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
        "gui.startup.dependencies",
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
            step_id="gui.startup.public-contract",
            title="Canonical GUI startup public contract",
            command=[
                console_python(),
                "-c",
                _STARTUP_CONTRACT_PROBE,
            ],
            timeout=config.timeout("short", 30),
        )

        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.bootstrap-tests",
            title="Bootstrap startup composition tests",
            arguments=[
                "tests/components/test_bootstrap.py",
                "-k",
                "build_gui_startup_runtime",
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.entrypoint-tests",
            title="GUI entrypoint lifecycle tests",
            arguments=["tests/integration/gui/test_startup.py"],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.prelaunch-tests",
            title="Inert startup and explicit remembered-path tests",
            arguments=[
                "tests/integration/gui/test_language_switching.py",
                "-k",
                (
                    "startup_and_construction_do_not_probe_or_build_automatically "
                    "or explicit_open_probes_builds_then_persists "
                    "or external_project_prompts_for_rgl_dependency_and_retries "
                    "or default_startup_services_use_standard_workspace_defaults_and_remember_overrides"
                ),
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.path-selection-tests",
            title="Explicit file selection and no-fallback tests",
            arguments=[
                "tests/integration/end_to_end/"
                "test_path_resolved_language_startup.py",
                "-k",
                (
                    "explicit_english_file_selection_preserves_focused_target "
                    "or missing_selection_fails_closed_without_language_fallback"
                ),
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.external-rgl-tests",
            title="External GF project with explicit RGL dependency root",
            arguments=[
                "tests/unit/projects/test_language_probe.py",
                "-k",
                (
                    "external_language_accepts_explicit_disjoint_rgl_dependency_root "
                    "or explicit_rgl_root_must_be_a_supported_checkout"
                ),
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.main-runtime-tests",
            title="Path-resolved main runtime composition tests",
            arguments=[
                "tests/integration/gui/test_main_runtime_composition.py",
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.quick-application-tests",
            title="Path-resolved Quick application service tests",
            arguments=[
                "tests/unit/runs/test_application_quick.py",
            ],
        )
        _run_pytest(
            config,
            report,
            log,
            step_id="gui.startup.state-default-tests",
            title="Startup state default tests",
            arguments=[
                "tests/components/test_app_state.py",
                "-k",
                "default_state_matches_locked_canonical_defaults",
            ],
        )
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
