"""Component contract tests for canonical CLI and GUI request parity."""

from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.entrypoints.cli.parser import build_parser
from gf_wordbench.entrypoints.gui.view_model import GuiRunRequest
from gf_wordbench.kernel.statuses import ValidationMode

_UNSET: Final[object] = object()


@dataclass(frozen=True, slots=True)
class _CanonicalInterfaceRequest:
    project_root: Path | None
    gf_executable: Path | None
    rgl_root: Path | None
    output_root: Path | None
    mode: ValidationMode
    target_file: str
    checkpoint_id: str
    scenario_filter: tuple[str, ...]
    timeout_override: int | None
    max_files: int
    keep_ok_details: bool
    diff_previous: bool
    skip_version_probe: bool
    no_compile: bool
    emit_cpu_stats: bool
    strict: bool


def _namespace_value(
    namespace: Namespace,
    *names: str,
    default: object = _UNSET,
) -> object:
    found = [getattr(namespace, name) for name in names if hasattr(namespace, name)]
    if not found:
        if default is _UNSET:
            joined = ", ".join(names)
            raise AssertionError(f"CLI namespace does not expose any of: {joined}")
        return default

    first = found[0]
    if any(value != first for value in found[1:]):
        joined = ", ".join(names)
        raise AssertionError(f"CLI namespace exposes conflicting values for: {joined}")
    return first


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise AssertionError(f"expected a path-like CLI value, received {type(value).__name__}")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, str):
        return value
    raise AssertionError(f"expected a text CLI value, received {type(value).__name__}")


def _mode(value: object) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    if isinstance(value, str):
        return ValidationMode(value)
    raise AssertionError(f"expected a validation mode, received {type(value).__name__}")


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise AssertionError("expected a CLI string or sequence of strings")


def _integer_or_none(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    raise AssertionError(f"expected an integer or None, received {type(value).__name__}")


def _plain_int(value: object) -> int:
    if type(value) is int:
        return value
    raise AssertionError(f"expected an integer, received {type(value).__name__}")


def _plain_bool(value: object) -> bool:
    if type(value) is bool:
        return value
    raise AssertionError(f"expected a boolean, received {type(value).__name__}")


def _cli_projection(namespace: Namespace) -> _CanonicalInterfaceRequest:
    return _CanonicalInterfaceRequest(
        project_root=_optional_path(
            _namespace_value(namespace, "project_root", default=None)
        ),
        gf_executable=_optional_path(
            _namespace_value(namespace, "gf_executable", "gf_exe", default=None)
        ),
        rgl_root=_optional_path(
            _namespace_value(namespace, "rgl_root", default=None)
        ),
        output_root=_optional_path(
            _namespace_value(namespace, "output_root", "out_root", default=None)
        ),
        mode=_mode(_namespace_value(namespace, "mode")),
        target_file=_text(
            _namespace_value(namespace, "target_file", "target", default="")
        ),
        checkpoint_id=_text(
            _namespace_value(namespace, "checkpoint_id", "checkpoint", default="")
        ),
        scenario_filter=_strings(
            _namespace_value(
                namespace,
                "scenario_filter",
                "scenario_ids",
                "scenarios",
                "scenario",
                default=(),
            )
        ),
        timeout_override=_integer_or_none(
            _namespace_value(
                namespace,
                "timeout_override",
                "compile_timeout",
                "timeout_sec",
                default=None,
            )
        ),
        max_files=_plain_int(
            _namespace_value(namespace, "max_files", default=0)
        ),
        keep_ok_details=_plain_bool(
            _namespace_value(namespace, "keep_ok_details", default=False)
        ),
        diff_previous=_plain_bool(
            _namespace_value(
                namespace,
                "diff_previous",
                "compare_previous",
                default=False,
            )
        ),
        skip_version_probe=_plain_bool(
            _namespace_value(
                namespace,
                "skip_version_probe",
                "no_version_probe",
                default=False,
            )
        ),
        no_compile=_plain_bool(
            _namespace_value(namespace, "no_compile", default=False)
        ),
        emit_cpu_stats=_plain_bool(
            _namespace_value(
                namespace,
                "emit_cpu_stats",
                "cpu_stats",
                default=False,
            )
        ),
        strict=_plain_bool(_namespace_value(namespace, "strict", default=False)),
    )


def _gui_projection(request: GuiRunRequest) -> _CanonicalInterfaceRequest:
    return _CanonicalInterfaceRequest(
        project_root=request.project_root,
        gf_executable=request.gf_executable,
        rgl_root=request.rgl_root,
        output_root=request.output_root,
        mode=request.mode,
        target_file=request.target_file,
        checkpoint_id=request.checkpoint_id,
        scenario_filter=request.scenario_filter,
        timeout_override=request.timeout_override,
        max_files=request.max_files,
        keep_ok_details=request.keep_ok_details,
        diff_previous=request.diff_previous,
        skip_version_probe=request.skip_version_probe,
        no_compile=request.no_compile,
        emit_cpu_stats=request.emit_cpu_stats,
        strict=request.strict,
    )


def _parse_validate(*arguments: str) -> Namespace:
    parser = build_parser()
    namespace = parser.parse_args(["validate", *arguments])
    if not isinstance(namespace, Namespace):
        raise AssertionError("CLI parser must return argparse.Namespace")
    return namespace


def _gui_request(
    *,
    mode: ValidationMode,
    target_file: str = "",
    checkpoint_id: str = "",
    scenario_filter: tuple[str, ...] = (),
    timeout_override: int | None = None,
    max_files: int = 0,
    keep_ok_details: bool = False,
    diff_previous: bool = False,
    skip_version_probe: bool = False,
    no_compile: bool = False,
    emit_cpu_stats: bool = False,
    strict: bool = False,
) -> GuiRunRequest:
    return GuiRunRequest(
        project_root=Path("C:/work/GF Wordbench"),
        gf_executable=Path("C:/Program Files/GF/bin/gf.exe"),
        rgl_root=Path("C:/work/gf-rgl/src"),
        output_root=Path("C:/work/GF Wordbench Runs"),
        mode=mode,
        target_file=target_file,
        checkpoint_id=checkpoint_id,
        scenario_filter=scenario_filter,
        timeout_override=timeout_override,
        max_files=max_files,
        keep_ok_details=keep_ok_details,
        diff_previous=diff_previous,
        skip_version_probe=skip_version_probe,
        no_compile=no_compile,
        emit_cpu_stats=emit_cpu_stats,
        strict=strict,
    )


@pytest.mark.parametrize(
    ("arguments", "gui_request"),
    (
        (
            (
                "--project-root",
                "C:/work/GF Wordbench",
                "--gf-exe",
                "C:/Program Files/GF/bin/gf.exe",
                "--rgl-root",
                "C:/work/gf-rgl/src",
                "--out-root",
                "C:/work/GF Wordbench Runs",
                "--mode",
                "quick",
                "--target",
                "lib/src/french/NounFre.gf",
                "--compile-timeout",
                "73",
                "--keep-ok-details",
                "--compare-previous",
            ),
            _gui_request(
                mode=ValidationMode.QUICK,
                target_file="lib/src/french/NounFre.gf",
                timeout_override=73,
                keep_ok_details=True,
                diff_previous=True,
            ),
        ),
        (
            (
                "--project-root",
                "C:/work/GF Wordbench",
                "--gf-exe",
                "C:/Program Files/GF/bin/gf.exe",
                "--rgl-root",
                "C:/work/gf-rgl/src",
                "--out-root",
                "C:/work/GF Wordbench Runs",
                "--mode",
                "checkpoint",
                "--checkpoint",
                "morphology",
                "--compile-timeout",
                "91",
                "--strict",
            ),
            _gui_request(
                mode=ValidationMode.CHECKPOINT,
                checkpoint_id="morphology",
                timeout_override=91,
                strict=True,
            ),
        ),
        (
            (
                "--project-root",
                "C:/work/GF Wordbench",
                "--gf-exe",
                "C:/Program Files/GF/bin/gf.exe",
                "--rgl-root",
                "C:/work/gf-rgl/src",
                "--out-root",
                "C:/work/GF Wordbench Runs",
                "--mode",
                "diagnostic",
                "--scenario",
                "parse-negation",
                "--scenario",
                "generation-smoke",
                "--compile-timeout",
                "47",
                "--max-files",
                "17",
                "--keep-ok-details",
                "--compare-previous",
                "--no-version-probe",
                "--no-compile",
                "--cpu-stats",
                "--strict",
            ),
            _gui_request(
                mode=ValidationMode.DIAGNOSTIC,
                scenario_filter=("parse-negation", "generation-smoke"),
                timeout_override=47,
                max_files=17,
                keep_ok_details=True,
                diff_previous=True,
                skip_version_probe=True,
                no_compile=True,
                emit_cpu_stats=True,
                strict=True,
            ),
        ),
        (
            (
                "--project-root",
                "C:/work/GF Wordbench",
                "--gf-exe",
                "C:/Program Files/GF/bin/gf.exe",
                "--rgl-root",
                "C:/work/gf-rgl/src",
                "--out-root",
                "C:/work/GF Wordbench Runs",
                "--mode",
                "release",
                "--compile-timeout",
                "120",
                "--compare-previous",
                "--strict",
            ),
            _gui_request(
                mode=ValidationMode.RELEASE,
                timeout_override=120,
                diff_previous=True,
                strict=True,
            ),
        ),
    ),
)
def test_equivalent_explicit_inputs_have_equal_canonical_projection(
    arguments: tuple[str, ...],
    gui_request: GuiRunRequest,
) -> None:
    cli_request = _cli_projection(_parse_validate(*arguments))

    assert cli_request == _gui_projection(gui_request)


def test_repeatable_scenario_order_is_preserved_across_interfaces() -> None:
    scenario_ids = ("scenario-z", "scenario-a", "scenario-m")
    namespace = _parse_validate(
        "--project-root",
        "C:/work/GF Wordbench",
        "--gf-exe",
        "C:/Program Files/GF/bin/gf.exe",
        "--rgl-root",
        "C:/work/gf-rgl/src",
        "--out-root",
        "C:/work/GF Wordbench Runs",
        "--mode",
        "diagnostic",
        *(item for scenario_id in scenario_ids for item in ("--scenario", scenario_id)),
    )
    gui_request = _gui_request(
        mode=ValidationMode.DIAGNOSTIC,
        scenario_filter=scenario_ids,
    )

    assert _cli_projection(namespace).scenario_filter == scenario_ids
    assert _cli_projection(namespace) == _gui_projection(gui_request)


def test_legacy_cli_aliases_normalize_to_the_same_gui_request() -> None:
    canonical = _parse_validate(
        "--project-root",
        "C:/work/GF Wordbench",
        "--gf-exe",
        "C:/Program Files/GF/bin/gf.exe",
        "--rgl-root",
        "C:/work/gf-rgl/src",
        "--out-root",
        "C:/work/GF Wordbench Runs",
        "--mode",
        "quick",
        "--target",
        "lib/src/french/NounFre.gf",
        "--compile-timeout",
        "66",
        "--compare-previous",
        "--no-version-probe",
        "--cpu-stats",
    )
    legacy = _parse_validate(
        "--project-root",
        "C:/work/GF Wordbench",
        "--gf-exe",
        "C:/Program Files/GF/bin/gf.exe",
        "--rgl-root",
        "C:/work/gf-rgl/src",
        "--out-root",
        "C:/work/GF Wordbench Runs",
        "--mode",
        "file",
        "--target-file",
        "lib/src/french/NounFre.gf",
        "--timeout-sec",
        "66",
        "--diff-previous",
        "--skip-version-probe",
        "--emit-cpu-stats",
    )
    gui_request = _gui_request(
        mode=ValidationMode.QUICK,
        target_file="lib/src/french/NounFre.gf",
        timeout_override=66,
        diff_previous=True,
        skip_version_probe=True,
        emit_cpu_stats=True,
    )

    expected = _gui_projection(gui_request)
    assert _cli_projection(canonical) == expected
    assert _cli_projection(legacy) == expected


def test_no_compare_previous_matches_the_gui_false_value() -> None:
    namespace = _parse_validate(
        "--project-root",
        "C:/work/GF Wordbench",
        "--gf-exe",
        "C:/Program Files/GF/bin/gf.exe",
        "--rgl-root",
        "C:/work/gf-rgl/src",
        "--out-root",
        "C:/work/GF Wordbench Runs",
        "--mode",
        "diagnostic",
        "--no-compare-previous",
    )
    gui_request = _gui_request(
        mode=ValidationMode.DIAGNOSTIC,
        diff_previous=False,
    )

    assert _cli_projection(namespace) == _gui_projection(gui_request)


def test_gui_presentation_state_is_not_part_of_request_parity() -> None:
    fields = set(_CanonicalInterfaceRequest.__dataclass_fields__)

    assert fields.isdisjoint(
        {
            "dialogs",
            "visual_progress",
            "browser_controls",
            "interactive_cancellation",
            "artifact_actions",
            "activity",
            "notices",
            "run_state",
        }
    )
