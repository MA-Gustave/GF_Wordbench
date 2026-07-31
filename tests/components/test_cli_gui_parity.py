"""Component contract tests for canonical CLI and GUI request parity.

The canonical interface contract follows ADR-0015:

* one explicit GF language directory or ``.gf`` file starts language resolution;
* an optional validation profile adds checkpoint, scenario, and release policy;
* machine-local GF, RGL, and output paths remain separate inputs;
* deprecated project-era aliases may be normalized, but they are not canonical
  language identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.entrypoints.cli.parser import (
    CliCommand,
    CliRequest,
    parse_cli_request,
)
from gf_wordbench.entrypoints.gui.view_model import GuiRunRequest
from gf_wordbench.kernel.statuses import ValidationMode

_UNSET: Final[object] = object()
_LANGUAGE_DIRECTORY: Final[Path] = Path("C:/work/gf-rgl/src/french")
_LANGUAGE_FILE: Final[Path] = _LANGUAGE_DIRECTORY / "NounFre.gf"
_VALIDATION_PROFILE: Final[Path] = Path(
    "C:/work/GF Wordbench Profiles/french/project.toml"
)
_GF_EXECUTABLE: Final[Path] = Path("C:/Program Files/GF/bin/gf.exe")
_RGL_ROOT: Final[Path] = Path("C:/work/gf-rgl")
_OUTPUT_ROOT: Final[Path] = Path("C:/work/GF Wordbench Runs")


@dataclass(frozen=True, slots=True)
class _CanonicalInterfaceRequest:
    selected_language_path: Path | None
    validation_profile_path: Path | None
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


def _request_value(
    request: CliRequest,
    *names: str,
    default: object = _UNSET,
) -> object:
    found = [request.arguments[name] for name in names if name in request.arguments]
    if not found:
        if default is _UNSET:
            joined = ", ".join(names)
            raise AssertionError(
                f"CLI request does not expose any of: {joined}"
            )
        return default

    first = found[0]
    if any(value != first for value in found[1:]):
        joined = ", ".join(names)
        raise AssertionError(
            f"CLI request exposes conflicting values for: {joined}"
        )
    return first


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise AssertionError(
        "expected a path-like value, "
        f"received {type(value).__name__}"
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, str):
        return value
    raise AssertionError(
        f"expected a text value, received {type(value).__name__}"
    )


def _mode(value: object) -> ValidationMode:
    if isinstance(value, ValidationMode):
        return value
    if isinstance(value, str):
        return ValidationMode(value)
    raise AssertionError(
        f"expected a validation mode, received {type(value).__name__}"
    )


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)) and all(
        isinstance(item, str) for item in value
    ):
        return tuple(value)
    raise AssertionError("expected a string or sequence of strings")


def _integer_or_none(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    raise AssertionError(
        f"expected an integer or None, received {type(value).__name__}"
    )


def _plain_int(value: object, *, default: int = 0) -> int:
    if value is None:
        return default
    if type(value) is int:
        return value
    raise AssertionError(
        f"expected an integer, received {type(value).__name__}"
    )


def _plain_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if type(value) is bool:
        return value
    raise AssertionError(
        f"expected a boolean, received {type(value).__name__}"
    )


def _cli_projection(request: CliRequest) -> _CanonicalInterfaceRequest:
    return _CanonicalInterfaceRequest(
        selected_language_path=_optional_path(
            _request_value(
                request,
                "selected_language_path",
                "language_path",
                default=None,
            )
        ),
        validation_profile_path=_optional_path(
            _request_value(
                request,
                "validation_profile_path",
                "validation_profile",
                "profile_path",
                default=None,
            )
        ),
        gf_executable=_optional_path(
            _request_value(
                request,
                "gf_executable",
                "gf_exe",
                default=None,
            )
        ),
        rgl_root=_optional_path(
            _request_value(request, "rgl_root", default=None)
        ),
        output_root=_optional_path(
            _request_value(
                request,
                "output_root",
                "out_root",
                default=None,
            )
        ),
        mode=_mode(_request_value(request, "mode")),
        target_file=_text(
            _request_value(
                request,
                "target_file",
                "target",
                default="",
            )
        ),
        checkpoint_id=_text(
            _request_value(
                request,
                "checkpoint_id",
                "checkpoint",
                default="",
            )
        ),
        scenario_filter=_strings(
            _request_value(
                request,
                "scenario_filter",
                "scenario_ids",
                "scenarios",
                "scenario",
                default=(),
            )
        ),
        timeout_override=_integer_or_none(
            _request_value(
                request,
                "timeout_override",
                "compile_timeout",
                "timeout_sec",
                default=None,
            )
        ),
        max_files=_plain_int(
            _request_value(request, "max_files", default=0)
        ),
        keep_ok_details=_plain_bool(
            _request_value(request, "keep_ok_details", default=False)
        ),
        diff_previous=_plain_bool(
            _request_value(
                request,
                "diff_previous",
                "compare_previous",
                default=False,
            )
        ),
        skip_version_probe=_plain_bool(
            _request_value(
                request,
                "skip_version_probe",
                "no_version_probe",
                default=False,
            )
        ),
        no_compile=_plain_bool(
            _request_value(request, "no_compile", default=False)
        ),
        emit_cpu_stats=_plain_bool(
            _request_value(
                request,
                "emit_cpu_stats",
                "cpu_stats",
                default=False,
            )
        ),
        strict=_plain_bool(
            _request_value(request, "strict", default=False)
        ),
    )


def _gui_projection(request: GuiRunRequest) -> _CanonicalInterfaceRequest:
    return _CanonicalInterfaceRequest(
        selected_language_path=request.selected_language_path,
        validation_profile_path=request.validation_profile_path,
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


def _parse_validate(*arguments: str) -> CliRequest:
    request = parse_cli_request(["validate", *arguments])
    if request.command is not CliCommand.VALIDATE:
        raise AssertionError(
            f"expected validate command, received {request.command!r}"
        )
    return request


def _gui_request(
    *,
    mode: ValidationMode,
    selected_language_path: Path = _LANGUAGE_DIRECTORY,
    validation_profile_path: Path | None = None,
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
        selected_language_path=selected_language_path,
        validation_profile_path=validation_profile_path,
        gf_executable=_GF_EXECUTABLE,
        rgl_root=_RGL_ROOT,
        output_root=_OUTPUT_ROOT,
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


def _base_cli_paths(*, include_profile: bool = False) -> tuple[str, ...]:
    values = (
        "--language-path",
        _LANGUAGE_DIRECTORY.as_posix(),
        "--gf-exe",
        _GF_EXECUTABLE.as_posix(),
        "--rgl-root",
        _RGL_ROOT.as_posix(),
        "--out-root",
        _OUTPUT_ROOT.as_posix(),
    )
    if include_profile:
        return (
            *values,
            "--validation-profile",
            _VALIDATION_PROFILE.as_posix(),
        )
    return values


@pytest.mark.parametrize(
    ("arguments", "gui_request"),
    (
        (
            (
                *_base_cli_paths(),
                "--mode",
                "quick",
                "--target",
                "NounFre.gf",
                "--compile-timeout",
                "73",
                "--keep-ok-details",
                "--compare-previous",
            ),
            _gui_request(
                mode=ValidationMode.QUICK,
                target_file="NounFre.gf",
                timeout_override=73,
                keep_ok_details=True,
                diff_previous=True,
            ),
        ),
        (
            (
                *_base_cli_paths(include_profile=True),
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
                validation_profile_path=_VALIDATION_PROFILE,
                checkpoint_id="morphology",
                timeout_override=91,
                strict=True,
            ),
        ),
        (
            (
                *_base_cli_paths(include_profile=True),
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
                validation_profile_path=_VALIDATION_PROFILE,
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
                *_base_cli_paths(include_profile=True),
                "--mode",
                "release",
                "--compile-timeout",
                "120",
                "--compare-previous",
                "--strict",
            ),
            _gui_request(
                mode=ValidationMode.RELEASE,
                validation_profile_path=_VALIDATION_PROFILE,
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


def test_selected_gf_file_is_preserved_as_language_selection() -> None:
    cli_request = _cli_projection(
        _parse_validate(
            "--language-path",
            _LANGUAGE_FILE.as_posix(),
            "--gf-exe",
            _GF_EXECUTABLE.as_posix(),
            "--rgl-root",
            _RGL_ROOT.as_posix(),
            "--out-root",
            _OUTPUT_ROOT.as_posix(),
            "--mode",
            "quick",
            "--target",
            "NounFre.gf",
        )
    )
    gui_request = _gui_projection(
        _gui_request(
            mode=ValidationMode.QUICK,
            selected_language_path=_LANGUAGE_FILE,
            target_file="NounFre.gf",
        )
    )

    assert cli_request == gui_request
    assert cli_request.selected_language_path == _LANGUAGE_FILE
    assert cli_request.target_file == "NounFre.gf"


def test_validation_profile_is_optional_for_source_level_workflows() -> None:
    request = _gui_projection(
        _gui_request(
            mode=ValidationMode.DIAGNOSTIC,
            no_compile=True,
        )
    )

    assert request.selected_language_path == _LANGUAGE_DIRECTORY
    assert request.validation_profile_path is None


def test_repeatable_scenario_order_is_preserved_across_interfaces() -> None:
    scenario_ids = ("scenario-z", "scenario-a", "scenario-m")
    namespace = _parse_validate(
        *_base_cli_paths(include_profile=True),
        "--mode",
        "diagnostic",
        *(item for scenario_id in scenario_ids for item in ("--scenario", scenario_id)),
    )
    gui_request = _gui_request(
        mode=ValidationMode.DIAGNOSTIC,
        validation_profile_path=_VALIDATION_PROFILE,
        scenario_filter=scenario_ids,
    )

    assert _cli_projection(namespace).scenario_filter == scenario_ids
    assert _cli_projection(namespace) == _gui_projection(gui_request)


def test_legacy_cli_aliases_normalize_to_the_same_gui_request() -> None:
    canonical = _parse_validate(
        *_base_cli_paths(),
        "--mode",
        "quick",
        "--target",
        "NounFre.gf",
        "--compile-timeout",
        "66",
        "--compare-previous",
        "--no-version-probe",
        "--cpu-stats",
    )
    legacy = _parse_validate(
        *_base_cli_paths(),
        "--mode",
        "file",
        "--target-file",
        "NounFre.gf",
        "--timeout-sec",
        "66",
        "--diff-previous",
        "--skip-version-probe",
        "--emit-cpu-stats",
    )
    gui_request = _gui_request(
        mode=ValidationMode.QUICK,
        target_file="NounFre.gf",
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
        *_base_cli_paths(),
        "--mode",
        "diagnostic",
        "--no-compare-previous",
    )
    gui_request = _gui_request(
        mode=ValidationMode.DIAGNOSTIC,
        diff_previous=False,
    )

    assert _cli_projection(namespace) == _gui_projection(gui_request)


def test_project_root_is_not_part_of_the_canonical_interface_request() -> None:
    fields = set(_CanonicalInterfaceRequest.__dataclass_fields__)

    assert "project_root" not in fields
    assert "catalog_path" not in fields
    assert "language_id" not in fields
    assert "selected_language_path" in fields
    assert "validation_profile_path" in fields


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
