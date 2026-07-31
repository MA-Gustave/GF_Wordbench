"""N03 — Run public and persisted contract tests."""

from __future__ import annotations

import json

from diag_core import (
    DiagConfig,
    DiagReport,
    console_python,
    execute_python_module,
    execute_step,
    run_level_app,
)

LEVEL_ID = "N03"
LEVEL_NAME = "Contracts"
PURPOSE = (
    "Verify CLI dispatch, path-resolved language startup, CLI/GUI parity, "
    "architectural contracts, and persisted schemas."
)


def _build_validate_arguments(config: DiagConfig) -> list[str]:
    """Build one explicit language-bound diagnostic request."""

    if config.language_path is None:
        raise ValueError(
            "N03 requires an explicit language_path. Set language_path in "
            "diag.config.local.json or define WORDBENCH_DIAG_LANGUAGE_PATH."
        )

    arguments = [
        "validate",
        "--language-path",
        str(config.language_path),
        "--mode",
        "diagnostic",
        "--no-compile",
    ]

    if config.validation_profile is not None:
        arguments.extend(
            [
                "--profile",
                str(config.validation_profile),
            ]
        )

    if config.rgl_root is not None:
        arguments.extend(["--rgl-root", str(config.rgl_root)])

    if config.output_root is not None:
        arguments.extend(["--out-root", str(config.output_root)])

    return arguments


def _build_cli_probe(config: DiagConfig) -> str:
    schema_path = config.repo_root / "DOCUMENT_MANIFEST.json"
    report_run_dir = config.artifact_root
    validate_arguments = _build_validate_arguments(config)

    return f"""
from gf_wordbench.entrypoints.cli.main import dispatch_cli_request
from gf_wordbench.entrypoints.cli.parser import CliCommand, parse_cli_request

samples = (
    (
        {json.dumps(validate_arguments)},
        CliCommand.VALIDATE,
    ),
    (
        ["project", "check"],
        CliCommand.PROJECT_CHECK,
    ),
    (
        ["scenarios", "check"],
        CliCommand.SCENARIOS_CHECK,
    ),
    (
        ["schemas", "check", {json.dumps(str(schema_path))}],
        CliCommand.SCHEMAS_CHECK,
    ),
    (
        ["reports", "check", {json.dumps(str(report_run_dir))}],
        CliCommand.REPORTS_CHECK,
    ),
)

for argv, expected_command in samples:
    request = parse_cli_request(argv)

    if request.command is not expected_command:
        raise SystemExit(
            f"{{argv!r}}: expected {{expected_command!r}}, "
            f"received {{request.command!r}}"
        )

    command_value = getattr(request.command, "value", request.command)
    print(f"{{argv!r}} -> {{command_value}}")

if not callable(dispatch_cli_request):
    raise SystemExit("dispatch_cli_request is not callable")

print("CLI import, parser mapping, and dispatcher contract: OK")
""".strip()


def run_checks(
    config: DiagConfig,
    report: DiagReport,
    log,
) -> None:
    execute_step(
        config,
        report,
        log,
        step_id="contracts.cli.import-and-parser",
        title=(
            "Import CLI and validate explicit language-bound parser "
            "command mapping"
        ),
        command=[
            console_python(),
            "-c",
            _build_cli_probe(config),
        ],
        timeout=config.timeout("short", 30),
    )

    test_commands = (
        (
            "contracts.pytest.cli-entrypoints",
            "CLI entrypoint unit tests",
            [
                "-q",
                "--tb=short",
                "tests/unit/entrypoints/test_cli_parser.py",
                "tests/unit/entrypoints/test_cli_commands.py",
                "tests/unit/entrypoints/test_cli_exit_codes.py",
            ],
        ),
        (
            "contracts.pytest.contracts",
            "Contract test suite",
            [
                "-q",
                "--tb=short",
                "tests/contracts",
            ],
        ),
        (
            "contracts.pytest.schemas",
            "Schema test suite",
            [
                "-q",
                "--tb=short",
                "tests/schemas",
            ],
        ),
        (
            "contracts.pytest.cli-gui-parity",
            "CLI/GUI parity tests",
            [
                "-q",
                "--tb=short",
                "tests/components/test_cli_gui_parity.py",
            ],
        ),
    )

    for step_id, title, arguments in test_commands:
        execute_python_module(
            config,
            report,
            log,
            module="pytest",
            arguments=arguments,
            step_id=step_id,
            title=title,
            timeout=config.timeout("tests", 1200),
            required=True,
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
