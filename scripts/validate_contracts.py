#!/usr/bin/env python3
"""Run the canonical GF Wordbench contract checks.

This maintenance entrypoint contains no contract-validation business logic.
It delegates framework contract checks to the canonical pytest contract suite
and delegates an optional explicit validation-profile check to the public
``gf-wordbench project check`` command.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Final, Never

EXIT_OK: Final[int] = 0
EXIT_NONCOMPLIANT: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_RUNTIME_ERROR: Final[int] = 3
EXIT_CANCELLED: Final[int] = 4

_REQUIRED_FRAMEWORK_PATHS: Final[tuple[str, ...]] = (
    "pyproject.toml",
    "src/gf_wordbench",
    "tests/contracts",
    "docs/DOCUMENTATION_ALIGNMENT_LOCK.md",
    "docs/INTERFILE_CONTRACT_LOCK.md",
    "docs/EXTERNAL_TOOL_CONTRACT_LOCK.md",
    "docs/PERSISTED_SCHEMA_LOCK.md",
    "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md",
    "templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md",
)

_EXTERNAL_CONTRACT_TESTS: Final[tuple[str, ...]] = (
    "tests/contracts/test_environment_contract.py",
    "tests/contracts/test_filesystem_contract.py",
    "tests/contracts/test_process_contract.py",
    "tests/contracts/test_windows_contract.py",
)


class ExitCodeFamily(StrEnum):
    PYTEST = "pytest"
    WORDBENCH = "wordbench"


@dataclass(frozen=True, slots=True)
class CheckCommand:
    name: str
    command: tuple[str, ...]
    exit_code_family: ExitCodeFamily


@dataclass(frozen=True, slots=True)
class ScriptOptions:
    workspace_root: Path
    strict: bool
    include_external: bool
    include_project: bool
    validation_profile: Path | None
    language_path: Path | None
    probe_gf: bool
    gf_executable: Path | None
    rgl_root: Path | None
    fail_fast: bool
    cli_executable: Path | None
    print_only: bool
    quiet: bool


class ArgumentParser(argparse.ArgumentParser):
    """Argument parser that maps invalid invocation to the canonical code 2."""

    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE_ERROR, f"{self.prog}: error: {message}\n")


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Run GF Wordbench framework contract tests and, when explicitly "
            "requested, validate one optional validation profile."
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
        help="Enable strict profile checking when a profile is requested.",
    )
    strict_group.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Check an explicit profile without strict mode.",
    )

    parser.add_argument(
        "--skip-external",
        action="store_true",
        help=(
            "Skip contract-test modules dedicated to environment, filesystem, "
            "process, and Windows external boundaries."
        ),
    )

    project_group = parser.add_mutually_exclusive_group()
    project_group.add_argument(
        "--include-project",
        action="store_true",
        help=(
            "Validate an explicit profile, or project/project.toml when that "
            "legacy-compatible profile exists."
        ),
    )
    project_group.add_argument(
        "--skip-project",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--profile",
        "--validation-profile",
        dest="validation_profile",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional explicit validation-profile file. Providing this option "
            "automatically enables the project check."
        ),
    )
    parser.add_argument(
        "--language-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional GF language directory or .gf file associated with the profile.",
    )
    parser.add_argument(
        "--probe-gf",
        action="store_true",
        help="Ask the optional profile check to probe GF capabilities.",
    )
    parser.add_argument(
        "--gf-exe",
        dest="gf_executable",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional GF executable for the explicit profile check.",
    )
    parser.add_argument(
        "--rgl-root",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional RGL root for the explicit profile check.",
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
            "Explicit gf-wordbench executable for the optional profile check. "
            "By default the script checks the workspace virtual environment, "
            "PATH, then Python module mode."
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

    validation_profile = _resolve_optional_path(
        namespace.validation_profile,
        workspace_root=workspace_root,
        label="validation profile",
        require_file=True,
    )
    language_path = _resolve_optional_path(
        namespace.language_path,
        workspace_root=workspace_root,
        label="language path",
        require_file=False,
    )
    gf_executable = _resolve_optional_path(
        namespace.gf_executable,
        workspace_root=workspace_root,
        label="GF executable",
        require_file=True,
    )
    rgl_root = _resolve_optional_path(
        namespace.rgl_root,
        workspace_root=workspace_root,
        label="RGL root",
        require_directory=True,
    )
    cli_executable = _resolve_optional_path(
        namespace.cli,
        workspace_root=workspace_root,
        label="CLI executable",
        require_file=True,
    )

    include_project = bool(
        not namespace.skip_project and (namespace.include_project or validation_profile is not None)
    )
    if include_project and validation_profile is None:
        validation_profile = _default_validation_profile(workspace_root)

    if not include_project:
        if language_path is not None:
            raise ValueError("--language-path requires --include-project or --profile")
        if namespace.probe_gf:
            raise ValueError("--probe-gf requires --include-project or --profile")
        if gf_executable is not None:
            raise ValueError("--gf-exe requires --include-project or --profile")
        if rgl_root is not None:
            raise ValueError("--rgl-root requires --include-project or --profile")

    return ScriptOptions(
        workspace_root=workspace_root,
        strict=bool(namespace.strict),
        include_external=not bool(namespace.skip_external),
        include_project=include_project,
        validation_profile=validation_profile,
        language_path=language_path,
        probe_gf=bool(namespace.probe_gf),
        gf_executable=gf_executable,
        rgl_root=rgl_root,
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
        raise ValueError(f"not a complete GF Wordbench workspace: {root}; missing: {rendered}")
    return root


def build_checks(options: ScriptOptions) -> tuple[CheckCommand, ...]:
    pytest_arguments = [
        sys.executable,
        "-m",
        "pytest",
        "tests/contracts",
        "-m",
        "not gf",
        "-ra",
        "--tb=short",
    ]
    if not options.include_external:
        pytest_arguments.extend(
            f"--ignore={relative_path}" for relative_path in _EXTERNAL_CONTRACT_TESTS
        )

    checks = [
        CheckCommand(
            name="Framework contract tests",
            command=tuple(pytest_arguments),
            exit_code_family=ExitCodeFamily.PYTEST,
        )
    ]

    if options.include_project:
        profile = options.validation_profile
        if profile is None:
            raise ValueError("project checking requires an explicit profile")

        command = [
            *resolve_cli_prefix(options),
            "project",
            "check",
            "--profile",
            os.fspath(profile),
        ]
        if options.strict:
            command.append("--strict")
        if options.language_path is not None:
            command.extend(("--language-path", os.fspath(options.language_path)))
        if options.probe_gf:
            command.append("--probe-gf")
        if options.gf_executable is not None:
            command.extend(("--gf-exe", os.fspath(options.gf_executable)))
        if options.rgl_root is not None:
            command.extend(("--rgl-root", os.fspath(options.rgl_root)))

        checks.append(
            CheckCommand(
                name="Explicit validation-profile contracts",
                command=tuple(command),
                exit_code_family=ExitCodeFamily.WORDBENCH,
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
    environment = build_environment(options.workspace_root)
    final_code = EXIT_OK

    for index, check in enumerate(checks, start=1):
        if not options.quiet:
            print(f"[{index}/{len(checks)}] {check.name}", flush=True)
            print(f"  {format_command(check.command)}", flush=True)

        if options.print_only:
            continue

        try:
            completed = subprocess.run(
                check.command,
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

        code = normalize_exit_code(
            completed.returncode,
            check_name=check.name,
            family=check.exit_code_family,
        )
        final_code = _combine_exit_codes(final_code, code)

        if code == EXIT_CANCELLED:
            return EXIT_CANCELLED
        if options.fail_fast and code != EXIT_OK:
            return code

    return final_code


def normalize_exit_code(
    return_code: int,
    *,
    check_name: str,
    family: ExitCodeFamily,
) -> int:
    if family is ExitCodeFamily.WORDBENCH:
        if return_code in {
            EXIT_OK,
            EXIT_NONCOMPLIANT,
            EXIT_USAGE_ERROR,
            EXIT_RUNTIME_ERROR,
            EXIT_CANCELLED,
        }:
            return return_code
    elif family is ExitCodeFamily.PYTEST:
        pytest_codes = {
            0: EXIT_OK,
            1: EXIT_NONCOMPLIANT,
            2: EXIT_CANCELLED,
            3: EXIT_RUNTIME_ERROR,
            4: EXIT_USAGE_ERROR,
            5: EXIT_RUNTIME_ERROR,
        }
        if return_code in pytest_codes:
            return pytest_codes[return_code]
    else:
        raise TypeError(f"unsupported exit-code family: {family!r}")

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


def _combine_exit_codes(current: int, new: int) -> int:
    precedence = {
        EXIT_OK: 0,
        EXIT_NONCOMPLIANT: 1,
        EXIT_USAGE_ERROR: 2,
        EXIT_RUNTIME_ERROR: 3,
        EXIT_CANCELLED: 4,
    }
    return new if precedence[new] > precedence[current] else current


def _default_validation_profile(workspace_root: Path) -> Path:
    candidate = workspace_root / "project" / "project.toml"
    if candidate.is_file():
        return candidate.resolve()
    raise ValueError(
        "--include-project requires --profile because project/project.toml does not exist"
    )


def _resolve_optional_path(
    value: Path | None,
    *,
    workspace_root: Path,
    label: str,
    require_file: bool = False,
    require_directory: bool = False,
) -> Path | None:
    if value is None:
        return None
    if require_file and require_directory:
        raise ValueError("a path cannot require both file and directory")

    path = value.expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    path = path.resolve(strict=False)

    if require_file and not path.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {path}")
    if require_directory and not path.is_dir():
        raise ValueError(f"{label} does not exist or is not a directory: {path}")
    if not require_file and not require_directory and not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
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
