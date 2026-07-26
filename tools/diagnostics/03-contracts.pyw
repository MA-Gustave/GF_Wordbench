"""N03 — Run public and persisted contract tests."""

from __future__ import annotations

import sys

from diag_core import (
    DiagConfig,
    DiagReport,
    execute_python_module,
    execute_step,
    run_level_app,
)

LEVEL_ID = "N03"
LEVEL_NAME = "Contracts"
PURPOSE = "Verify CLI dispatch, CLI/GUI parity, architectural contracts, and persisted schemas."


def run_checks(config: DiagConfig, report: DiagReport, log) -> None:
    probe = """
from gf_wordbench.entrypoints.cli.parser import CliCommand, parse_cli_request
from gf_wordbench.entrypoints.cli.main import dispatch_cli_request
samples = {
CliCommand.VALIDATE: [\"validate\", \"--mode\", \"quick\"],
CliCommand.PROJECT_CHECK: [\"project\", \"check\"],
CliCommand.SCENARIOS_CHECK: [\"scenarios\", \"check\"],
CliCommand.SCHEMAS_CHECK: [\"schemas\", \"check\"],
CliCommand.REPORTS_CHECK: [\"reports\", \"check\"],
}
for expected, argv in samples.items():
request = parse_cli_request(argv)
if request.command is not expected:
    raise SystemExit(f\"{argv}: expected {expected}, got {request.command}\")
print(\"parser command mapping OK\")
""".strip()
    execute_step(
        config,
        report,
        log,
        step_id="contracts.cli.import-and-parser",
        title="Import CLI and validate parser command mapping",
        command=[sys.executable, "-c", probe],
        timeout=config.timeout("short", 30),
    )

    execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=["-q", "tests/contracts"],
        step_id="contracts.pytest.contracts",
        title="Contract test suite",
        timeout=config.timeout("tests", 1200),
        required=True,
    )
    execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=["-q", "tests/schemas"],
        step_id="contracts.pytest.schemas",
        title="Schema test suite",
        timeout=config.timeout("tests", 1200),
        required=True,
    )
    execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=["-q", "tests/components/test_cli_gui_parity.py"],
        step_id="contracts.pytest.cli-gui-parity",
        title="CLI/GUI parity tests",
        timeout=config.timeout("tests", 1200),
        required=True,
    )


if __name__ == "__main__":
    raise SystemExit(run_level_app(LEVEL_ID, LEVEL_NAME, PURPOSE, run_checks))
