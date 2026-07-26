"""Unit tests for canonical CLI parsing and normalization."""

from __future__ import annotations

import argparse
from dataclasses import FrozenInstanceError
from enum import Enum
from pathlib import Path
from typing import Final

import pytest

from gf_wordbench.entrypoints.cli.parser import (
    CliArgumentParser,
    CliCommand,
    CliRequest,
    CliUsageError,
    build_parser,
    parse_args,
    parse_cli_namespace,
    parse_cli_request,
)
from gf_wordbench.version import __version__

_ROOT_COMMANDS: Final = {
    "validate",
    "project",
    "scenarios",
    "gold",
    "schemas",
    "reports",
}

_CANONICAL_COMMANDS: Final = {
    "validate",
    "project-check",
    "scenarios-check",
    "gold-update",
    "schemas-check",
    "reports-check",
}


def _enum_value(value: object) -> object:
    return value.value if isinstance(value, Enum) else value


def _subparser_choices(
    parser: argparse.ArgumentParser,
) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    raise AssertionError(f"{parser.prog!r} does not define subcommands")


def _request_value(
    request: CliRequest,
    *names: str,
) -> object:
    for name in names:
        value = request.get(name)
        if value is not None:
            return value
    return None


def _warning_texts(request: CliRequest) -> tuple[str, ...]:
    return tuple(str(item) for item in request.compatibility_warnings)


def test_cli_command_vocabulary_is_fixed() -> None:
    assert {item.value for item in CliCommand} == _CANONICAL_COMMANDS


def test_build_parser_returns_the_non_exiting_parser_type() -> None:
    parser = build_parser()

    assert isinstance(parser, CliArgumentParser)
    assert parser.prog == "gf-wordbench"


def test_build_parser_exposes_the_documented_command_tree() -> None:
    parser = build_parser()
    root = _subparser_choices(parser)

    assert set(root) == _ROOT_COMMANDS
    assert set(_subparser_choices(root["project"])) == {"check"}
    assert set(_subparser_choices(root["scenarios"])) == {"check"}
    assert set(_subparser_choices(root["gold"])) == {"update"}
    assert set(_subparser_choices(root["schemas"])) == {"check"}
    assert set(_subparser_choices(root["reports"])) == {"check"}


def test_global_help_lists_every_supported_root_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["--help"])

    assert caught.value.code == 0
    output = capsys.readouterr()
    assert output.err == ""
    for command in sorted(_ROOT_COMMANDS):
        assert command in output.out


def test_global_version_is_successful_and_uses_package_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["--version"])

    assert caught.value.code == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert __version__ in output.out


@pytest.mark.parametrize(
    "argv",
    [
        (),
        ("unknown-command",),
        ("validate", "--unknown-option"),
        ("project", "unknown-action"),
    ],
)
def test_usage_failures_raise_cli_usage_error_without_process_exit(
    argv: tuple[str, ...],
) -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli_namespace(argv)

    assert str(caught.value).strip()


def test_parse_args_is_the_namespace_compatibility_entrypoint() -> None:
    expected = parse_cli_namespace(["validate"])
    actual = parse_args(["validate"])

    assert isinstance(actual, argparse.Namespace)
    assert vars(actual) == vars(expected)


def test_validate_defaults_to_diagnostic_mode() -> None:
    namespace = parse_cli_namespace(["validate"])
    request = parse_cli_request(["validate"])

    assert _enum_value(namespace.command) == "validate"
    assert _enum_value(namespace.mode) == "diagnostic"
    assert request.command is CliCommand.VALIDATE
    assert _enum_value(request.require("mode")) == "diagnostic"
    assert request.compatibility_warnings == ()


def test_validate_parses_paths_repeatable_ids_and_policy_flags() -> None:
    request = parse_cli_request(
        [
            "validate",
            "--mode",
            "diagnostic",
            "--target",
            "project/src/Main.gf",
            "--scenario",
            "parse-basic",
            "--scenario",
            "linearize-basic",
            "--strict",
            "--no-version-probe",
            "--no-compile",
            "--compile-timeout",
            "41",
            "--scenario-timeout",
            "42",
            "--pgf-timeout",
            "43",
            "--max-files",
            "12",
            "--cpu-stats",
            "--keep-ok-details",
            "--no-compare-previous",
            "--baseline",
            "_gf_wordbench/run_baseline",
            "--project-root",
            "C:/work/GF Wordbench",
            "--gf-exe",
            "C:/Program Files/GF/bin/gf.exe",
            "--rgl-root",
            "C:/Program Files/GF/lib",
            "--out-root",
            "C:/work/GF Wordbench/_gf_wordbench",
            "--verbose",
        ]
    )

    assert request.command is CliCommand.VALIDATE
    assert _enum_value(request.require("mode")) == "diagnostic"
    assert request.require("target") == Path("project/src/Main.gf")
    assert request.require("scenarios") == (
        "parse-basic",
        "linearize-basic",
    )
    assert request.require("strict") is True
    assert request.require("skip_version_probe") is True
    assert request.require("no_compile") is True
    assert _request_value(
        request,
        "compile_timeout_sec",
        "compile_timeout",
    ) == 41
    assert _request_value(
        request,
        "scenario_timeout_sec",
        "scenario_timeout",
    ) == 42
    assert _request_value(
        request,
        "pgf_timeout_sec",
        "pgf_timeout",
    ) == 43
    assert request.require("max_files") == 12
    assert request.require("emit_cpu_stats") is True
    assert request.require("keep_ok_details") is True
    assert _request_value(
        request,
        "diff_previous",
        "compare_previous",
    ) is False
    assert request.require("baseline") == Path("_gf_wordbench/run_baseline")
    assert request.require("project_root") == Path("C:/work/GF Wordbench")
    assert _request_value(
        request,
        "gf_executable",
        "gf_exe",
    ) == Path("C:/Program Files/GF/bin/gf.exe")
    assert request.require("rgl_root") == Path("C:/Program Files/GF/lib")
    assert _request_value(
        request,
        "output_root",
        "out_root",
    ) == Path("C:/work/GF Wordbench/_gf_wordbench")
    assert request.require("verbose") is True
    assert request.require("quiet") is False


def test_cli_request_is_frozen_and_owns_detached_immutable_mappings() -> None:
    request = parse_cli_request(
        [
            "validate",
            "--mode",
            "diagnostic",
            "--scenario",
            "parse-basic",
        ]
    )

    assert isinstance(request, CliRequest)

    with pytest.raises(FrozenInstanceError):
        request.command = CliCommand.REPORTS_CHECK  # type: ignore[misc]

    with pytest.raises(TypeError):
        request.arguments["mode"] = "release"  # type: ignore[index]

    with pytest.raises(TypeError):
        request.project_overrides["scan_glob"] = "*.gf"  # type: ignore[index]

    copied = request.as_dict()
    copied["mode"] = "release"

    assert _enum_value(request.require("mode")) == "diagnostic"
    assert request.get("missing") is None
    with pytest.raises(KeyError):
        request.require("missing")


@pytest.mark.parametrize(
    ("argv", "message_fragment"),
    [
        (
            ("validate", "--quiet", "--verbose"),
            "not allowed",
        ),
        (
            ("validate", "--compile-timeout", "0"),
            "positive",
        ),
        (
            ("validate", "--max-files", "-1"),
            "non-negative",
        ),
        (
            (
                "validate",
                "--scenario",
                "parse-basic",
                "--scenario",
                "parse-basic",
            ),
            "duplicate",
        ),
        (
            ("validate", "--scenario", "not valid"),
            "scenario",
        ),
    ],
)
def test_validate_rejects_invalid_syntactic_arguments(
    argv: tuple[str, ...],
    message_fragment: str,
) -> None:
    with pytest.raises(CliUsageError) as caught:
        parse_cli_request(argv)

    assert message_fragment.casefold() in str(caught.value).casefold()


@pytest.mark.parametrize(
    "argv",
    [
        ("validate", "--mode", "quick"),
        (
            "validate",
            "--mode",
            "quick",
            "--target",
            "project/src/Main.gf",
            "--checkpoint",
            "morphology",
        ),
        (
            "validate",
            "--mode",
            "checkpoint",
            "--target",
            "project/src/Main.gf",
        ),
        (
            "validate",
            "--mode",
            "release",
            "--no-compile",
        ),
        (
            "validate",
            "--mode",
            "release",
            "--max-files",
            "10",
        ),
    ],
)
def test_validate_enforces_mode_specific_argument_contracts(
    argv: tuple[str, ...],
) -> None:
    with pytest.raises(CliUsageError):
        parse_cli_request(argv)


def test_checkpoint_and_quick_modes_keep_canonical_target_kinds() -> None:
    quick = parse_cli_request(
        [
            "validate",
            "--mode",
            "quick",
            "--target",
            "project/src/Main.gf",
        ]
    )
    checkpoint = parse_cli_request(
        [
            "validate",
            "--mode",
            "checkpoint",
            "--checkpoint",
            "morphology",
        ]
    )

    assert quick.require("target") == Path("project/src/Main.gf")
    assert checkpoint.require("checkpoints") == ("morphology",)


def test_legacy_validate_aliases_are_normalized_once_with_warnings() -> None:
    request = parse_cli_request(
        [
            "validate",
            "--mode",
            "quick",
            "--target-file",
            "project/src/Main.gf",
            "--skip-version-probe",
            "--emit-cpu-stats",
            "--timeout-sec",
            "77",
        ]
    )

    assert request.require("target") == Path("project/src/Main.gf")
    assert request.require("skip_version_probe") is True
    assert request.require("emit_cpu_stats") is True
    assert _request_value(
        request,
        "compile_timeout_sec",
        "compile_timeout",
    ) == 77
    assert _warning_texts(request)
    assert not hasattr(
        parse_cli_namespace(
            [
                "validate",
                "--mode",
                "quick",
                "--target-file",
                "project/src/Main.gf",
            ]
        ),
        "target_file",
    )


def test_legacy_project_overrides_are_separated_from_run_arguments() -> None:
    request = parse_cli_request(
        [
            "validate",
            "--scan-dir",
            "project/src",
            "--scan-glob",
            "**/*.gf",
            "--include-regex",
            r"^[A-Z].*\\.gf$",
            "--exclude-regex",
            r"/generated/",
            "--gf-path",
            "project/src",
            "--gf-path",
            "vendor/rgl",
        ]
    )

    assert request.project_overrides
    assert request.project_overrides["scan_dir"] == Path("project/src")
    assert request.project_overrides["scan_glob"] == "**/*.gf"
    assert request.project_overrides["include_regex"] == r"^[A-Z].*\\.gf$"
    assert request.project_overrides["exclude_regex"] == r"/generated/"
    assert request.project_overrides["gf_path"] == (
        Path("project/src"),
        Path("vendor/rgl"),
    )
    assert _warning_texts(request)


@pytest.mark.parametrize(
    ("argv", "expected_command"),
    [
        (
            (
                "project",
                "check",
                "--strict",
                "--probe-gf",
                "--project-root",
                "C:/work/GF",
            ),
            CliCommand.PROJECT_CHECK,
        ),
        (
            (
                "scenarios",
                "check",
                "--scenario",
                "parse-basic",
                "--scenario",
                "linearize-basic",
                "--strict",
            ),
            CliCommand.SCENARIOS_CHECK,
        ),
        (
            (
                "gold",
                "update",
                "parse-basic",
                "linearize-basic",
                "--yes",
                "--show-diff",
            ),
            CliCommand.GOLD_UPDATE,
        ),
        (
            (
                "schemas",
                "check",
                "project/project.toml",
                ".gf_wordbench_state.json",
                "--recursive",
                "--strict",
            ),
            CliCommand.SCHEMAS_CHECK,
        ),
        (
            (
                "reports",
                "check",
                "_gf_wordbench/run_20260725_120000",
                "--verify-hashes",
                "--strict",
            ),
            CliCommand.REPORTS_CHECK,
        ),
    ],
)
def test_non_validate_commands_map_to_one_canonical_command(
    argv: tuple[str, ...],
    expected_command: CliCommand,
) -> None:
    request = parse_cli_request(argv)

    assert request.command is expected_command
    assert request.compatibility_warnings == ()


def test_project_check_options_are_typed() -> None:
    request = parse_cli_request(
        [
            "project",
            "check",
            "--strict",
            "--probe-gf",
            "--project-root",
            "C:/work/GF",
            "--gf-exe",
            "C:/tools/gf.exe",
            "--rgl-root",
            "C:/tools/rgl",
            "--quiet",
        ]
    )

    assert request.require("strict") is True
    assert request.require("probe_gf") is True
    assert request.require("project_root") == Path("C:/work/GF")
    assert _request_value(
        request,
        "gf_executable",
        "gf_exe",
    ) == Path("C:/tools/gf.exe")
    assert request.require("rgl_root") == Path("C:/tools/rgl")
    assert request.require("quiet") is True


def test_scenario_check_normalizes_repeatable_selection_to_tuple() -> None:
    request = parse_cli_request(
        [
            "scenarios",
            "check",
            "--scenario",
            "parse-basic",
            "--scenario",
            "linearize-basic",
        ]
    )

    assert request.require("scenarios") == (
        "parse-basic",
        "linearize-basic",
    )


@pytest.mark.parametrize(
    "argv",
    [
        ("gold", "update"),
        ("gold", "update", "parse-basic", "--all"),
        ("gold", "update", "--all", "--all"),
    ],
)
def test_gold_update_requires_one_unambiguous_selection(
    argv: tuple[str, ...],
) -> None:
    with pytest.raises(CliUsageError):
        parse_cli_request(argv)


def test_gold_update_all_selection_is_canonical() -> None:
    request = parse_cli_request(
        [
            "gold",
            "update",
            "--all",
            "--yes",
            "--scenario-timeout",
            "30",
        ]
    )

    assert request.command is CliCommand.GOLD_UPDATE
    assert request.require("all_scenarios") is True
    assert request.require("scenarios") == ()
    assert request.require("yes") is True
    assert _request_value(
        request,
        "scenario_timeout_sec",
        "scenario_timeout",
    ) == 30


@pytest.mark.parametrize(
    "argv",
    [
        ("schemas", "check"),
        ("reports", "check"),
    ],
)
def test_path_consuming_commands_require_their_positional_paths(
    argv: tuple[str, ...],
) -> None:
    with pytest.raises(CliUsageError):
        parse_cli_request(argv)


def test_schema_and_report_paths_are_path_objects() -> None:
    schemas = parse_cli_request(
        [
            "schemas",
            "check",
            "project/project.toml",
            "_gf_wordbench/run_a/summary.json",
        ]
    )
    reports = parse_cli_request(
        [
            "reports",
            "check",
            "_gf_wordbench/run_a",
        ]
    )

    assert schemas.require("paths") == (
        Path("project/project.toml"),
        Path("_gf_wordbench/run_a/summary.json"),
    )
    assert reports.require("run_dir") == Path("_gf_wordbench/run_a")


def test_argument_values_are_frozen_recursively() -> None:
    request = parse_cli_request(
        [
            "schemas",
            "check",
            "project/project.toml",
            "_gf_wordbench/run_a/summary.json",
        ]
    )

    paths = request.require("paths")
    assert isinstance(paths, tuple)
    with pytest.raises(TypeError):
        paths[0] = Path("replacement")  # type: ignore[index]


def test_nul_is_rejected_in_path_and_text_arguments() -> None:
    with pytest.raises(CliUsageError):
        parse_cli_request(
            [
                "validate",
                "--target",
                "project/src/Main.gf\x00other",
            ]
        )

    with pytest.raises(CliUsageError):
        parse_cli_request(
            [
                "validate",
                "--checkpoint",
                "checkpoint\x00other",
            ]
        )
