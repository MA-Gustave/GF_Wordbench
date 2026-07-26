# GF Wordbench Mini Diagnostics

A lightweight set of standalone diagnostic windows for the GF Wordbench repository.

The suite is deliberately thin. It launches Wordbench's public CLI, pytest suites, and existing repository validation scripts. It does **not** reimplement GF compilation, scenarios, gold comparison, diagnostics classification, report generation, or release policy.

## Install

Extract the ZIP at the GF Wordbench repository root so the files resolve to:

```text
tools/diagnostics/
```

Add this generated-artifact directory to the repository `.gitignore`:

```gitignore
.wordbench-diagnostics/
```

No Python package installation is required for the mini-suite itself. Wordbench and its development dependencies must be installed according to the repository instructions.

## Start

Windows:

```bat
tools\diagnostics\launch_diagnostics.bat
```

Python:

```text
python tools/diagnostics/00-control_panel.pyw
```

Run the safe suite without graphical windows:

```text
python tools/diagnostics/run_safe_suite.py
```

Run one level headlessly:

```text
python tools/diagnostics/03-contracts.pyw --headless
```

## Levels

| Level | Purpose |
|---|---|
| N01 Environment | Python, paths, imports, GF, RGL, and development tools |
| N02 Repository Integrity | compileall, architecture, contracts, schemas, Ruff, and mypy |
| N03 Contracts | CLI parser/import probe, contract tests, schema tests, and CLI/GUI parity |
| N04 Runtime Smoke | CLI help, GUI import, project/scenario/schema checks, and optional quick mode |
| N05 Release Validation | authoritative Wordbench release run plus external evidence inspection |

`run_safe_suite.py` runs N01 through N04. Release validation is never included automatically.

## Configuration

Built-in defaults work when the suite is under `tools/diagnostics/` in a normal checkout.

For machine-specific paths, copy:

```text
diag.config.local.json.example
```

to:

```text
diag.config.local.json
```

Then configure the GF executable, RGL root, Wordbench output root, and optional quick target.

Environment overrides are also supported:

```text
WORDBENCH_DIAG_REPO_ROOT
WORDBENCH_DIAG_PROJECT_ROOT
WORDBENCH_DIAG_OUTPUT_ROOT
WORDBENCH_DIAG_GF_EXECUTABLE
WORDBENCH_DIAG_RGL_ROOT
WORDBENCH_DIAG_ARTIFACT_DIR
```

## Quick validation

N04 does not launch a GF quick run by default. Enable it explicitly:

```json
{
  "runtime_smoke": {
    "run_quick": true,
    "target": "project/src/YourConcrete.gf"
  }
}
```

This prevents an unconfigured diagnostic window from unexpectedly starting a long or invalid GF operation.

## Release validation

N05 launches the canonical Wordbench command:

```text
python -m gf_wordbench validate --mode release --strict ...
```

It interprets Wordbench's exit code and then looks for a newly created or updated `summary.json`. It checks the recorded mode and overall status, verifies required release files, parses `manifest.json`, and checks for a PGF when project policy requires one.

N05 does not replace Wordbench's release gate. Wordbench remains authoritative.

## Artifacts

Reports and command logs are written under:

```text
.wordbench-diagnostics/
```

Each execution receives a timestamped directory containing:

```text
Nxx-report.json
Nxx-report.txt
*.log
```

Verdicts are:

```text
PASS WARN FAIL SKIP BLOCKED PARTIAL ERROR INFRA_ERROR CONFIG_ERROR
```

## Safety

N01 through N03 are static or read-only except for normal Python cache files and diagnostic logs.

N04 creates a Wordbench run only when `runtime_smoke.run_quick` is enabled.

N05 intentionally starts a full release validation and may take significant time. Launching N05 is the explicit user action authorizing that run.
