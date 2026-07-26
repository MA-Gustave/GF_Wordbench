#!/usr/bin/env python3
"""Run the canonical GF Wordbench contract checks.

This maintenance entrypoint deliberately contains no contract-validation
business logic. It delegates to the documented ``gf-wordbench`` commands and
preserves the canonical process exit-code meanings.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

EXIT_OK: Final[int] = 0
EXIT_NONCOMPLIANT: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_RUNTIME_ERROR: Final[int] = 3
EXIT_CANCELLED: Final[int] = 4

_KNOWN_EXIT_CODES: Final[frozenset[int]] = frozenset(
    {
        EXIT_OK,
        EXIT_NONCOMPLIANT,
        EXIT_USAGE_ERROR,
        EXIT_RUNTIME_ERROR,
        EXIT_CANCELLED,
    }
)
_REQUIRED_FRAMEWORK_PATHS: Final[tuple[str, ...]] = (
    "pyproject.toml",
    "src/gf_wordbench",
    "docs/DOCUMENTATION_ALIGNMENT_LOCK.md",
    "docs/INTERFILE_CONTRACT_LOCK.md",
    "docs/EXTERNAL_TOOL_CONTRACT_LOCK.md",
    "docs/PERSISTED_SCHEMA_LOCK.md",
    "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md",
)
_PROJECT_REQUIRED_PATHS: Final[tuple[str, ...]] = (
    "project/project.toml",
    "project/docs/INTERFILE_CONTRACT_LOCK.md",
    "templates/project/docs/INTERFILE_CONTRACT_LOCK.md",
)


@dataclass(frozen=True, slots=True)
class CheckCommand:
    name: str
    arguments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScriptOptions:
    workspace_root: Path
    strict: bool
    include_external: bool
    include_project: bool
    fail_fast: bool
    cli_executable: Path | None
    print_only: bool
    quiet: bool


class ArgumentParser(argparse.ArgumentParser):
    """Argument parser that maps invalid invocation to the canonical code 2."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE_ERROR, f"{self.prog}: error: {message}\n")


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Run GF Wordbench Python, external-tool, and active-project "
            "contract checks through the canonical CLI."
        )
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help=(
            "GF Wordbench workspace root. Defaults to GF_WORDBENCH_ROOT, "
            "then the parent of this script's scripts directory."
        ),
    )
    strict_group = parser.add_mutually_exclusive_group()
    strict_group.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        default=True,
        help="Enable strict contract checking (default).",
    )
    strict_group.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Run the supported checks without strict mode.",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Skip the external-tool contract check.",
    )
    parser.add_argument(
        "--skip-project",
        action="store_true",
        help="Skip the active-project contract check.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first non-zero check result.",
    )
    parser.add_argument(
        "--cli",
        type=Path,
        default=None,
        help=(
            "Explicit gf-wordbench executable. By default the script checks "
            "the workspace virtual environment, PATH, then Python module mode."
        ),
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the resolved commands without executing them.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress wrapper headings; checker output is unchanged.",
    )
    return parser


def parse_options(argv: Sequence[str] | None = None) -> ScriptOptions:
    namespace = build_parser().parse_args(argv)
    workspace_root = resolve_workspace_root(namespace.workspace_root)
    cli_executable = (
        _absolute_existing_file(namespace.cli, "CLI executable")
        if namespace.cli is not None
        else None
    )
    return ScriptOptions(
        workspace_root=workspace_root,
        strict=bool(namespace.strict),
        include_external=not bool(namespace.skip_external),
        include_project=not bool(namespace.skip_project),
        fail_fast=bool(namespace.fail_fast),
        cli_executable=cli_executable,
        print_only=bool(namespace.print_only),
        quiet=bool(namespace.quiet),
    )


def resolve_workspace_root(explicit_root: Path | None) -> Path:
    candidate = explicit_root
    if candidate is None:
        environment_root = os.environ.get("GF_WORDBENCH_ROOT")
        if environment_root:
            candidate = Path(environment_root)
    if candidate is None:
        script_path = Path(__file__).resolve()
        candidate = (
            script_path.parent.parent
            if script_path.parent.name.casefold() == "scripts"
            else Path.cwd()
        )

    root = candidate.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"workspace root is not a directory: {root}")

    missing = tuple(
        relative_path
        for relative_path in _REQUIRED_FRAMEWORK_PATHS
        if not (root / relative_path).exists()
    )
    if missing:
        rendered = ", ".join(missing)
        raise ValueError(
            f"not a complete GF Wordbench workspace: {root}; "
            f"missing: {rendered}"
        )
    return root


def build_checks(options: ScriptOptions) -> tuple[CheckCommand, ...]:
    strict = ("--strict",) if options.strict else ()
    checks: list[CheckCommand] = [
        CheckCommand(
            name="Python interfile contracts",
            arguments=("contracts", "check", *strict),
        )
    ]
    if options.include_external:
        checks.append(
            CheckCommand(
                name="External-tool contracts",
                arguments=("contracts", "check-external", *strict),
            )
        )
    if options.include_project:
        missing = tuple(
            relative_path
            for relative_path in _PROJECT_REQUIRED_PATHS
            if not (options.workspace_root / relative_path).exists()
        )
        if missing:
            rendered = ", ".join(missing)
            raise ValueError(
                "active-project contract checking was requested, but required "
                f"project paths are missing: {rendered}"
            )
        checks.append(
            CheckCommand(
                name="Active-project contracts",
                arguments=("project", "contracts", "check", *strict),
            )
        )
    return tuple(checks)


def resolve_cli_prefix(options: ScriptOptions) -> tuple[str, ...]:
    if options.cli_executable is not None:
        return (os.fspath(options.cli_executable),)

    root = options.workspace_root
    candidates = (
        root / ".venv" / "Scripts" / "gf-wordbench.exe",
        root / ".venv" / "Scripts" / "gf-wordbench",
        root / ".venv" / "bin" / "gf-wordbench",
    )
    for candidate in candidates:
        if candidate.is_file():
            return (os.fspath(candidate.resolve()),)

    discovered = shutil.which("gf-wordbench")
    if discovered:
        return (discovered,)

    return (sys.executable, "-m", "gf_wordbench")


def build_environment(workspace_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"

    source_root = os.fspath(workspace_root / "src")
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_python_path
        else os.pathsep.join((source_root, existing_python_path))
    )
    return environment


def run_checks(options: ScriptOptions) -> int:
    checks = build_checks(options)
    cli_prefix = resolve_cli_prefix(options)
    environment = build_environment(options.workspace_root)
    final_code = EXIT_OK

    for index, check in enumerate(checks, start=1):
        command = (*cli_prefix, *check.arguments)
        if not options.quiet:
            print(
                f"[{index}/{len(checks)}] {check.name}",
                flush=True,
            )
            print(f"  {format_command(command)}", flush=True)

        if options.print_only:
            continue

        try:
            completed = subprocess.run(
                command,
                cwd=options.workspace_root,
                env=environment,
                check=False,
                shell=False,
            )
        except KeyboardInterrupt:
            print("Contract validation cancelled.", file=sys.stderr)
            return EXIT_CANCELLED
        except OSError as exception:
            print(
                f"Unable to execute the contract checker: {exception}",
                file=sys.stderr,
            )
            return EXIT_RUNTIME_ERROR

        code = normalize_exit_code(completed.returncode, check.name)
        final_code = max(final_code, code)

        if code == EXIT_CANCELLED:
            return EXIT_CANCELLED
        if options.fail_fast and code != EXIT_OK:
            return code

    return final_code


def normalize_exit_code(return_code: int, check_name: str) -> int:
    if return_code in _KNOWN_EXIT_CODES:
        return return_code
    if return_code < 0:
        print(
            f"{check_name} was terminated by signal {-return_code}.",
            file=sys.stderr,
        )
    else:
        print(
            f"{check_name} returned unsupported exit code {return_code}; "
            "mapping it to runtime error 3.",
            file=sys.stderr,
        )
    return EXIT_RUNTIME_ERROR


def format_command(command: Sequence[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(list(command))
    return shlex.join(command)


def _absolute_existing_file(value: Path, label: str) -> Path:
    path = value.expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {path}")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = parse_options(argv)
        return run_checks(options)
    except ValueError as exception:
        print(f"validate_contracts.py: {exception}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except KeyboardInterrupt:
        print("Contract validation cancelled.", file=sys.stderr)
        return EXIT_CANCELLED
    except Exception as exception:
        print(
            f"validate_contracts.py: unexpected runtime error: {exception}",
            file=sys.stderr,
        )
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
