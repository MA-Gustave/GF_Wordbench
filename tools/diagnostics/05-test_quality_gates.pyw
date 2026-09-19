"""N05 — Run the complete local test and quality gate set."""

from __future__ import annotations

import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from diag_core import (
    FAIL,
    PASS,
    WARN,
    DiagConfig,
    DiagReport,
    LogFn,
    StepResult,
    console_python,
    execute_python_module,
    execute_step,
    run_level_app,
)

LEVEL_ID = "N05"
LEVEL_NAME = "Test and Quality Gates"
PURPOSE = (
    "Run the CI-aligned compile, exhaustive import, discovery, formatting, lint, "
    "typing, architecture, contract, schema, coverage, and non-real-GF test gates; "
    "then aggregate every observable issue into one file-oriented inventory."
)

_INVENTORY_SCHEMA: Final[str] = "wordbench.quality-bug-inventory.v1"
_IMPORT_TIMEOUT_SECONDS: Final[int] = 20
_MAX_ERRORS_PER_FILE: Final[int] = 25
_DIRECT_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {
        "confirmed_source_defect",
        "confirmed_test_defect",
        "architecture_violation",
        "contract_violation",
        "schema_violation",
        "type_error",
        "lint_only",
        "unresolved_failure",
    }
)


def _required_script(
    config: DiagConfig,
    report: DiagReport,
    relative: str,
) -> Path | None:
    path = (config.repo_root / relative).resolve(strict=False)
    if path.is_file():
        return path
    report.add(
        f"quality.script.{path.stem}.missing",
        FAIL,
        "quality",
        f"Required quality script is missing: {relative}",
        evidence=str(path),
    )
    return None


def _add_file_artifact(
    report: DiagReport,
    path: Path,
    *,
    kind: str,
    description: str,
) -> None:
    if path.is_file() and path.stat().st_size > 0:
        report.add_artifact(kind, path, description)


def _discover_import_targets(repo_root: Path) -> list[tuple[str, str]]:
    package_root = repo_root / "src" / "gf_wordbench"
    if not package_root.is_dir():
        return []

    targets: list[tuple[str, str]] = []
    for path in sorted(package_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(repo_root / "src")
        if path.name == "__init__.py":
            module_parts = relative.parent.parts
        else:
            module_parts = relative.with_suffix("").parts
        if not module_parts:
            continue
        targets.append((".".join(module_parts), relative.as_posix()))
    return targets


def _import_environment(config: DiagConfig) -> dict[str, str]:
    environment = dict(os.environ)
    source_root = str((config.repo_root / "src").resolve(strict=False))
    existing = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = (
        source_root if not existing else os.pathsep.join((source_root, existing))
    )
    return environment


def _run_import_sweep(
    config: DiagConfig,
    report: DiagReport,
    log: LogFn,
) -> list[dict[str, Any]]:
    targets = _discover_import_targets(config.repo_root)
    records: list[dict[str, Any]] = []
    json_path = report.artifact_dir / "import-sweep.json"
    text_path = report.artifact_dir / "import-sweep.txt"

    if not targets:
        report.add(
            "quality.import-sweep",
            FAIL,
            "imports",
            "No gf_wordbench Python modules were found for isolated import checks",
            evidence=str(config.repo_root / "src" / "gf_wordbench"),
        )
        return records

    command_prefix = [
        console_python(),
        "-c",
        "import importlib, sys; importlib.import_module(sys.argv[1])",
    ]
    environment = _import_environment(config)
    log(f"RUN Isolated module import sweep: {len(targets)} modules")

    for index, (module_name, relative_path) in enumerate(targets, start=1):
        started_status = "PASS"
        exit_code: int | None = None
        output = ""
        try:
            completed = subprocess.run(
                [*command_prefix, module_name],
                cwd=config.repo_root,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_IMPORT_TIMEOUT_SECONDS,
                check=False,
            )
            exit_code = completed.returncode
            output = completed.stdout or ""
            if completed.returncode != 0:
                started_status = "FAIL"
        except subprocess.TimeoutExpired as exc:
            started_status = "TIMEOUT"
            output = exc.stdout if isinstance(exc.stdout, str) else ""
            output += (
                f"\nTimeoutExpired: import exceeded "
                f"{_IMPORT_TIMEOUT_SECONDS} seconds"
            )
        except (OSError, ValueError) as exc:
            started_status = "ERROR"
            output = f"{type(exc).__name__}: {exc}"

        records.append(
            {
                "module": module_name,
                "path": relative_path,
                "status": started_status,
                "exit_code": exit_code,
                "output": output,
            }
        )
        if started_status != "PASS":
            log(f"  FAIL import {module_name}")
        elif index % 25 == 0 or index == len(targets):
            log(f"  imported {index}/{len(targets)} modules")

    failed = [record for record in records if record["status"] != "PASS"]
    json_path.write_text(
        json.dumps(
            {
                "schema": "wordbench.module-import-sweep.v1",
                "module_count": len(records),
                "failed_count": len(failed),
                "records": records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    text_lines = [
        "GF Wordbench isolated module import sweep",
        f"Modules: {len(records)}",
        f"Failures: {len(failed)}",
        "",
    ]
    for record in failed:
        text_lines.append(
            f"[{record['status']}] {record['module']} ({record['path']})"
        )
        output = str(record["output"]).strip()
        if output:
            text_lines.extend(f"  {line}" for line in output.splitlines())
        text_lines.append("")
    text_path.write_text("\n".join(text_lines), encoding="utf-8")
    report.add_artifact(
        "import-sweep-json",
        json_path,
        "Structured isolated import results for every gf_wordbench module",
    )
    report.add_artifact(
        "import-sweep-text",
        text_path,
        "Human-readable isolated module import failures",
    )
    report.add(
        "quality.import-sweep",
        PASS if not failed else FAIL,
        "imports",
        (
            f"All {len(records)} gf_wordbench modules imported successfully"
            if not failed
            else f"{len(failed)} of {len(records)} isolated module imports failed"
        ),
        evidence=str(text_path),
        recommendation=(
            None
            if not failed
            else "Correct root import failures first, then rerun N05 to expose deeper defects."
        ),
        data={
            "module_count": len(records),
            "failed_count": len(failed),
            "json": str(json_path),
            "text": str(text_path),
        },
    )
    log(
        f"{'PASS' if not failed else 'FAIL'} Isolated module import sweep "
        f"({len(failed)} failures)"
    )
    return records


def _module_to_repo_path(module_name: str, repo_root: Path) -> str | None:
    relative = Path("src", *module_name.split("."))
    module_file = repo_root / relative.with_suffix(".py")
    package_file = repo_root / relative / "__init__.py"
    if module_file.is_file():
        return module_file.relative_to(repo_root).as_posix()
    if package_file.is_file():
        return package_file.relative_to(repo_root).as_posix()
    return None


def _normalize_repo_path(raw: str, repo_root: Path) -> str | None:
    candidate = raw.strip().strip("'\"()[]{}.,").replace("\\", "/")
    if not candidate:
        return None

    root_text = str(repo_root.resolve(strict=False)).replace("\\", "/").rstrip("/")
    lowered = candidate.casefold()
    lowered_root = root_text.casefold()
    if lowered.startswith(lowered_root + "/"):
        candidate = candidate[len(root_text) + 1 :]

    while candidate.startswith("./"):
        candidate = candidate[2:]
    if candidate.startswith("../") or "/../" in candidate:
        return None

    allowed_prefixes = (
        "src/",
        "tests/",
        "scripts/",
        "tools/",
        ".github/",
    )
    allowed_root_files = {
        "launch_cli.bat",
        "launch_gui.bat",
        "pyproject.toml",
    }
    if not candidate.startswith(allowed_prefixes) and candidate not in allowed_root_files:
        return None
    return candidate


def _extract_repo_paths(text: str, repo_root: Path) -> list[str]:
    found: set[str] = set()
    patterns = (
        re.compile(r'File\s+["\']([^"\']+\.(?:pyw?|bat))["\']'),
        re.compile(
            r"(?im)^(?:FAILED\s+)?((?:src|tests|scripts|tools|\.github)"
            r"[/\\][^\n:]+?\.(?:pyw?|bat))(?:[:\s]|::|$)"
        ),
        re.compile(r"([A-Za-z]:[/\\][^\n\r\"']+?\.(?:pyw?|bat))"),
    )
    for pattern in patterns:
        for match in pattern.finditer(text):
            normalized = _normalize_repo_path(match.group(1), repo_root)
            if normalized is not None:
                found.add(normalized)
    return sorted(found)


def _extract_module_paths(text: str, repo_root: Path) -> list[str]:
    modules = set(
        re.findall(r"\bgf_wordbench(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b", text)
    )
    paths = {
        path
        for module in modules
        if (path := _module_to_repo_path(module, repo_root)) is not None
    }
    return sorted(paths)


def _last_error_line(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped[:1000]
    return "Import failed without diagnostic output"


def _root_import_path(
    record: Mapping[str, Any],
    repo_root: Path,
) -> str | None:
    output = str(record.get("output", ""))
    import_match = re.search(
        r"cannot import name .+? from ['\"]"
        r"(?P<module>gf_wordbench(?:\.[A-Za-z_][A-Za-z0-9_]*)+)['\"]",
        output,
    )
    if import_match is not None:
        mapped = _module_to_repo_path(import_match.group("module"), repo_root)
        if mapped is not None:
            return mapped

    traceback_paths = _extract_repo_paths(output, repo_root)
    source_paths = [path for path in traceback_paths if path.startswith("src/")]
    if source_paths:
        return source_paths[-1]

    module_name = str(record.get("module", ""))
    return _module_to_repo_path(module_name, repo_root)


def _new_inventory_entry(path: str) -> dict[str, Any]:
    return {
        "path": path,
        "classifications": set(),
        "sources": set(),
        "errors": [],
        "affected_tests": set(),
        "impacted_modules": set(),
        "direct_observations": 0,
    }


def _record_inventory_issue(
    inventory: dict[str, dict[str, Any]],
    *,
    path: str,
    classification: str,
    source: str,
    error: str,
    affected_test: str | None = None,
    impacted_module: str | None = None,
    direct: bool = True,
) -> None:
    entry = inventory.setdefault(path, _new_inventory_entry(path))
    entry["classifications"].add(classification)
    entry["sources"].add(source)
    normalized_error = " ".join(error.split())[:1000]
    if normalized_error and normalized_error not in entry["errors"]:
        if len(entry["errors"]) < _MAX_ERRORS_PER_FILE:
            entry["errors"].append(normalized_error)
    if affected_test is not None:
        entry["affected_tests"].add(affected_test)
    if impacted_module is not None:
        entry["impacted_modules"].add(impacted_module)
    if direct:
        entry["direct_observations"] += 1


def _add_import_failures_to_inventory(
    inventory: dict[str, dict[str, Any]],
    records: Sequence[Mapping[str, Any]],
    repo_root: Path,
) -> None:
    for record in records:
        if record.get("status") == "PASS":
            continue
        module_name = str(record.get("module", ""))
        output = str(record.get("output", ""))
        target_path = str(record.get("path", ""))
        root_path = _root_import_path(record, repo_root) or target_path
        error = _last_error_line(output)
        _record_inventory_issue(
            inventory,
            path=root_path,
            classification="confirmed_source_defect",
            source="module_import_sweep",
            error=error,
            impacted_module=module_name,
        )
        for path in _extract_repo_paths(output, repo_root):
            if path == root_path:
                continue
            _record_inventory_issue(
                inventory,
                path=path,
                classification="cascade_from_other_file",
                source="module_import_sweep",
                error=f"Import of {module_name} cascaded through this file",
                impacted_module=module_name,
                direct=False,
            )


def _source_classification(source: str) -> str:
    if source.startswith("ruff"):
        return "lint_only"
    if source == "mypy":
        return "type_error"
    if source == "architecture":
        return "architecture_violation"
    if source == "contracts":
        return "contract_violation"
    if source == "schemas":
        return "schema_violation"
    if source == "compileall":
        return "confirmed_source_defect"
    return "unresolved_failure"


def _matching_output_line(output: str, path: str, source: str) -> str:
    variants = {path, path.replace("/", "\\"), Path(path).name}
    for line in output.splitlines():
        if any(variant in line for variant in variants):
            return line.strip()[:1000]
    return f"{source} reported an issue involving {path}"


def _add_command_output_to_inventory(
    inventory: dict[str, dict[str, Any]],
    *,
    source: str,
    output: str,
    repo_root: Path,
) -> None:
    if not output.strip():
        return
    classification = _source_classification(source)
    paths = set(_extract_repo_paths(output, repo_root))
    paths.update(_extract_module_paths(output, repo_root))
    failed_tests = set(
        re.findall(
            r"(?m)^FAILED\s+((?:tests)[/\\][^:\s]+\.py)(?:::|\s|$)",
            output,
        )
    )
    normalized_tests = {
        path
        for raw in failed_tests
        if (path := _normalize_repo_path(raw, repo_root)) is not None
    }

    for path in sorted(paths):
        affected_test = path if path.startswith("tests/") else None
        _record_inventory_issue(
            inventory,
            path=path,
            classification=classification,
            source=source,
            error=_matching_output_line(output, path, source),
            affected_test=affected_test,
        )
    for test_path in normalized_tests:
        _record_inventory_issue(
            inventory,
            path=test_path,
            classification=classification,
            source=source,
            error=_matching_output_line(output, test_path, source),
            affected_test=test_path,
        )


def _test_path_from_classname(classname: str, repo_root: Path) -> str | None:
    if not classname.startswith("tests."):
        return None
    parts = classname.split(".")
    for length in range(len(parts), 1, -1):
        candidate = Path(*parts[:length]).with_suffix(".py")
        if (repo_root / candidate).is_file():
            return candidate.as_posix()
    return None


def _add_junit_to_inventory(
    inventory: dict[str, dict[str, Any]],
    junit_path: Path,
    repo_root: Path,
) -> None:
    if not junit_path.is_file():
        return
    try:
        root = ET.parse(junit_path).getroot()
    except (ET.ParseError, OSError):
        return

    for testcase in root.iter("testcase"):
        failure = testcase.find("failure")
        if failure is None:
            failure = testcase.find("error")
        if failure is None:
            continue
        classname = testcase.attrib.get("classname", "")
        test_path = _test_path_from_classname(classname, repo_root)
        details = (failure.text or failure.attrib.get("message", "")).strip()
        message = _last_error_line(details)
        trace_paths = _extract_repo_paths(details, repo_root)
        if test_path is not None:
            _record_inventory_issue(
                inventory,
                path=test_path,
                classification="unresolved_failure",
                source="pytest_junit",
                error=message,
                affected_test=test_path,
            )
        for path in trace_paths:
            _record_inventory_issue(
                inventory,
                path=path,
                classification="unresolved_failure",
                source="pytest_junit",
                error=message,
                affected_test=test_path,
            )


def _finalize_inventory_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    impacted_modules = sorted(entry["impacted_modules"])
    classifications = sorted(entry["classifications"])
    direct = bool(set(classifications) & _DIRECT_CLASSIFICATIONS)
    return {
        "path": entry["path"],
        "classifications": classifications,
        "sources": sorted(entry["sources"]),
        "errors": list(entry["errors"]),
        "affected_tests": sorted(entry["affected_tests"]),
        "impacted_modules": impacted_modules,
        "cascade_count": max(0, len(impacted_modules) - 1),
        "directly_implicated": direct,
        "direct_observations": int(entry["direct_observations"]),
    }


def _write_bug_inventory(
    config: DiagConfig,
    report: DiagReport,
    *,
    import_records: Sequence[Mapping[str, Any]],
    command_results: Sequence[tuple[str, StepResult | None]],
    junit_path: Path,
) -> None:
    inventory: dict[str, dict[str, Any]] = {}
    _add_import_failures_to_inventory(inventory, import_records, config.repo_root)
    for source, result in command_results:
        if result is None:
            continue
        output = str(getattr(result, "output", ""))
        exit_code = getattr(result, "exit_code", None)
        if exit_code == 0 and source not in {"ruff_format", "ruff_lint", "mypy"}:
            continue
        _add_command_output_to_inventory(
            inventory,
            source=source,
            output=output,
            repo_root=config.repo_root,
        )
    _add_junit_to_inventory(inventory, junit_path, config.repo_root)

    entries = sorted(
        (_finalize_inventory_entry(entry) for entry in inventory.values()),
        key=lambda item: (not item["directly_implicated"], item["path"]),
    )
    direct_entries = [entry for entry in entries if entry["directly_implicated"]]
    cascade_entries = [entry for entry in entries if not entry["directly_implicated"]]
    classification_counts: dict[str, int] = {}
    for entry in entries:
        for classification in entry["classifications"]:
            classification_counts[classification] = (
                classification_counts.get(classification, 0) + 1
            )

    json_path = report.artifact_dir / "bug-inventory.json"
    text_path = report.artifact_dir / "bug-inventory.txt"
    payload = {
        "schema": _INVENTORY_SCHEMA,
        "repository": str(config.repo_root),
        "direct_file_count": len(direct_entries),
        "cascade_only_file_count": len(cascade_entries),
        "classification_counts": dict(sorted(classification_counts.items())),
        "files": entries,
    }
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    text_lines = [
        "GF Wordbench N05 bug inventory",
        f"Directly implicated files: {len(direct_entries)}",
        f"Cascade-only files: {len(cascade_entries)}",
        "",
        "DIRECTLY IMPLICATED FILES",
    ]
    if not direct_entries:
        text_lines.append("- none")
    for entry in direct_entries:
        text_lines.append(entry["path"])
        text_lines.append(
            "  classifications: " + ", ".join(entry["classifications"])
        )
        text_lines.append("  sources: " + ", ".join(entry["sources"]))
        for error in entry["errors"]:
            text_lines.append(f"  - {error}")
        if entry["affected_tests"]:
            text_lines.append(
                "  affected tests: " + ", ".join(entry["affected_tests"])
            )
        if entry["cascade_count"]:
            text_lines.append(f"  cascade count: {entry['cascade_count']}")
        text_lines.append("")

    text_lines.append("CASCADE-ONLY FILES")
    if not cascade_entries:
        text_lines.append("- none")
    for entry in cascade_entries:
        text_lines.append(entry["path"])
        text_lines.append("  sources: " + ", ".join(entry["sources"]))
        if entry["impacted_modules"]:
            text_lines.append(
                "  impacted modules: " + ", ".join(entry["impacted_modules"])
            )
        text_lines.append("")
    text_path.write_text("\n".join(text_lines) + "\n", encoding="utf-8")

    report.add_artifact(
        "bug-inventory-json",
        json_path,
        "Aggregated machine-readable issue inventory grouped by repository file",
    )
    report.add_artifact(
        "bug-inventory-text",
        text_path,
        "Aggregated human-readable issue inventory grouped by repository file",
    )
    report.metadata["bug_inventory"] = {
        "direct_file_count": len(direct_entries),
        "cascade_only_file_count": len(cascade_entries),
        "classification_counts": dict(sorted(classification_counts.items())),
        "json": str(json_path),
        "text": str(text_path),
    }
    report.add(
        "quality.bug-inventory",
        PASS if not direct_entries else WARN,
        "inventory",
        (
            "No directly implicated repository files were found"
            if not direct_entries
            else f"N05 identified {len(direct_entries)} directly implicated files"
        ),
        evidence=str(text_path),
        recommendation=(
            None
            if not direct_entries
            else "Fix root import and architecture defects first, then rerun N05."
        ),
        data=report.metadata["bug_inventory"],
    )


def run_checks(config: DiagConfig, report: DiagReport, log: LogFn) -> None:
    normal_timeout = config.timeout("normal", 180)
    tests_timeout = config.timeout("tests", 1200)
    command_results: list[tuple[str, StepResult | None]] = []

    compile_result = execute_step(
        config,
        report,
        log,
        step_id="quality.compileall",
        title="Compile all maintained Python sources",
        command=[
            console_python(),
            "-m",
            "compileall",
            "-q",
            "src",
            "tests",
            "scripts",
            "tools/diagnostics",
        ],
        timeout=normal_timeout,
    )
    command_results.append(("compileall", compile_result))

    import_records = _run_import_sweep(config, report, log)

    collect_result = execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=[
            "--collect-only",
            "--continue-on-collection-errors",
            "--maxfail=0",
            "-q",
        ],
        step_id="quality.pytest.collect",
        title="Collect the complete pytest suite without stopping at import errors",
        timeout=tests_timeout,
        required=True,
    )
    command_results.append(("pytest_collect", collect_result))

    ruff_format_result = execute_python_module(
        config,
        report,
        log,
        module="ruff",
        arguments=["format", "--check", "."],
        step_id="quality.ruff.format",
        title="Ruff formatting check",
        timeout=normal_timeout,
        required=True,
    )
    command_results.append(("ruff_format", ruff_format_result))

    ruff_lint_result = execute_python_module(
        config,
        report,
        log,
        module="ruff",
        arguments=["check", "."],
        step_id="quality.ruff.lint",
        title="Ruff lint",
        timeout=normal_timeout,
        required=True,
    )
    command_results.append(("ruff_lint", ruff_lint_result))

    mypy_result = execute_python_module(
        config,
        report,
        log,
        module="mypy",
        arguments=[],
        step_id="quality.mypy",
        title="Mypy strict type check",
        timeout=tests_timeout,
        required=True,
    )
    command_results.append(("mypy", mypy_result))

    script_checks = (
        (
            "scripts/verify_architecture.py",
            "quality.architecture",
            "Verify canonical architecture",
            ["--root", ".", "--warnings-as-errors"],
            "architecture",
        ),
        (
            "scripts/validate_contracts.py",
            "quality.contracts",
            "Validate interfile and project contracts",
            ["--workspace-root", ".", "--strict"],
            "contracts",
        ),
        (
            "scripts/validate_schemas.py",
            "quality.schemas",
            "Validate persisted schemas",
            ["--root", ".", "--strict"],
            "schemas",
        ),
    )
    for relative, step_id, title, arguments, source in script_checks:
        script = _required_script(config, report, relative)
        if script is None:
            continue
        result = execute_step(
            config,
            report,
            log,
            step_id=step_id,
            title=title,
            command=[console_python(), str(script), *arguments],
            timeout=tests_timeout,
        )
        command_results.append((source, result))

    junit_path = report.artifact_dir / "pytest-non-real-gf.xml"
    coverage_path = report.artifact_dir / "coverage.xml"
    pytest_result = execute_python_module(
        config,
        report,
        log,
        module="pytest",
        arguments=[
            "-ra",
            "--tb=short",
            "--durations=25",
            "--continue-on-collection-errors",
            "--maxfail=0",
            "-m",
            "not gf",
            f"--junitxml={junit_path}",
            "--cov=gf_wordbench",
            "--cov-branch",
            "--cov-report=term-missing",
            f"--cov-report=xml:{coverage_path}",
            "--cov-fail-under=85",
        ],
        step_id="quality.pytest.non-real-gf",
        title="Complete non-real-GF pytest suite with exhaustive failure collection",
        timeout=tests_timeout,
        required=True,
    )
    command_results.append(("pytest_non_real_gf", pytest_result))
    if pytest_result is not None:
        _add_file_artifact(
            report,
            junit_path,
            kind="junit",
            description="Complete non-real-GF pytest JUnit report",
        )
        _add_file_artifact(
            report,
            coverage_path,
            kind="coverage",
            description="Coverage XML for the complete non-real-GF suite",
        )

    _write_bug_inventory(
        config,
        report,
        import_records=import_records,
        command_results=command_results,
        junit_path=junit_path,
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
