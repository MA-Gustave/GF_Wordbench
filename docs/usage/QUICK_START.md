# GF Wordbench — Quick Start

**Document ID:** `GF-WB-QUICK-START`  
**Status:** User guide  
**Applies to:** First local installation, first active-project validation, CLI and GUI startup  
**Owner:** GF Wordbench maintainers  
**Canonical path:** `docs/usage/QUICK_START.md`  
**Guide version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Goal

This guide takes a new GF Wordbench checkout from zero to a first validated GF source file.

The shortest successful path is:

```text
install Python environment
→ identify GF and RGL
→ verify project/project.toml
→ check configuration
→ run quick validation
→ open the generated summary
```

One GF Wordbench workspace contains exactly one active GF language project.

The active project is defined by:

```text
project/project.toml
```

GF remains the execution engine.

GF Wordbench selects targets, invokes GF, captures evidence, classifies results and writes reports.

Multi-workspace and multilingual aggregation belong to the independent `gf-portfolio` product. GF Wordbench does not require `gf-portfolio` to install, validate or report one active project.

---

## 2. Open the repository root

Open PowerShell, Command Prompt or a POSIX shell in the GF Wordbench repository root.

PowerShell:

```powershell
Set-Location "<WORKSPACE_ROOT>"
```

Command Prompt:

```bat
cd /d "<WORKSPACE_ROOT>"
```

POSIX shell:

```bash
cd "<WORKSPACE_ROOT>"
```

The repository root contains at least:

```text
app/
docs/
project/
templates/
tests/
pyproject.toml
```

The active project contains:

```text
project/
├── project.toml
├── docs/
└── validation/
```

GF language sources may live inside the repository or at the project-relative source location declared by `project/project.toml`.

---

## 3. Prerequisites

Required:

```text
Python version supported by pyproject.toml
Grammatical Framework executable: gf or gf.exe
GF Resource Grammar Library sources or another configured GF library root
one initialized active project
```

Useful local tools:

```text
Git
PowerShell on Windows
an editor with TOML and Markdown support
```

GF Wordbench does not install or replace Grammatical Framework.

Before continuing, identify:

```text
<WORKSPACE_ROOT>  GF Wordbench repository root
<GF>              absolute path to gf or gf.exe
<RGL>             absolute path to the RGL source root
<OUT>             writable output root for run directories
```

Paths containing spaces are supported when passed as one quoted argument.

---

## 4. Verify GF directly

Run GF outside GF Wordbench first.

PowerShell:

```powershell
& "<GF>" --version
```

Command Prompt:

```bat
"<GF>" --version
```

POSIX shell:

```bash
"<GF>" --version
```

A version line must be returned.

A missing executable, launch failure or timeout must be corrected before required GF validation can run.

Do not rely on an unknown `gf` from `PATH` when several GF installations exist. GF Wordbench records the exact executable used for each run.

---

## 5. Create the Python environment

From the repository root:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it in Command Prompt:

```bat
.venv\Scripts\activate.bat
```

On POSIX systems:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade packaging tools:

```powershell
python -m pip install --upgrade pip
```

Install GF Wordbench in editable mode:

```powershell
python -m pip install -e .
```

Install development dependencies when working on the framework:

```powershell
python -m pip install -e ".[dev]"
```

The optional dependency groups are defined by `pyproject.toml`.

---

## 6. Verify the installation

Run:

```powershell
gf-wordbench --version
gf-wordbench --help
```

The command must be available inside the activated virtual environment.

The canonical source entrypoint is:

```powershell
python -m app.main_cli --help
```

The installed `gf-wordbench` command remains the primary interface.

Command names, options and argument semantics are owned by:

```text
docs/usage/CLI_REFERENCE.md
```

---

## 7. Verify the active project

Open:

```text
project/project.toml
```

It identifies the single active language project for the workspace.

Verify at least:

```text
project ID
project name
language code
source directory
source glob
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release PGF policy
```

A simplified project configuration resembles:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "example"
name = "Example Language"
language_code = "xxx"
root = "."

[sources]
directory = "lib/src/example"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "(\\.bak\\.gf$|\\.tmp\\.gf$)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/example",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarXxx.gf",
]
checkpoints = [
  "MorphoXxx.gf",
  "NounXxx.gf",
  "VerbXxx.gf",
]

[validation]
required_scenarios = [
  "load-main",
  "linearize-basic",
]
optional_scenarios = [
  "generation-bounded",
]
release_requires_pgf = true
```

Use the exact schema documented in:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
```

Do not store local absolute paths to GF, the RGL or run output inside `project.toml`. Those values belong to local environment configuration or explicit run input.

---

## 8. Validate configuration before running GF

Run the configuration checker:

```powershell
gf-wordbench config check `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Single-line equivalent:

```powershell
gf-wordbench config check --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

The checker validates:

```text
project schema
required project fields
source paths
entrypoints
checkpoints
scenario registration
required input and gold paths
GF executable
GF version policy
RGL root
effective GF search path
output-root writability
mode and target compatibility
```

Correct configuration errors before starting a validation run.

Typical failures include:

```text
configured entrypoint does not exist
GF executable cannot launch
RGL root is missing
required scenario is not registered
required gold file is missing
project-relative path escapes the project root
unsupported project schema version
```

---

## 9. Choose a first target

Choose one small GF source file that is expected to compile.

Use a project-relative path, for example:

```text
lib/src/example/MorphoXxx.gf
```

Start with focused validation rather than release validation.

The normal progression is:

```text
quick
→ checkpoint
→ release
```

Use `diagnostic` whenever the cause of failure is unclear.

---

## 10. Run the first quick validation

```powershell
gf-wordbench validate `
  --mode quick `
  --target "file:lib/src/example/MorphoXxx.gf" `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Single-line equivalent:

```powershell
gf-wordbench validate --mode quick --target "file:lib/src/example/MorphoXxx.gf" --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

A `quick` run performs a bounded workflow:

```text
configuration
local environment resolution
GF version probe
target selection
static scan
fingerprint
GF compilation
failure classification
report generation
run finalization
```

`quick` answers:

```text
Did this focused target satisfy its configured source, scan and compilation contract?
```

It does not prove release readiness.

Every run has a global budget, stage budgets and a protected finalization reserve. The reserve is used to stop child processes, preserve available evidence and publish a coherent terminal result when normal execution times out or is cancelled.

---

## 11. Understand the first result

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

| Status | Meaning |
|---|---|
| `OK` | The selected validation contract passed |
| `FAIL` | Execution completed, but a validation criterion failed |
| `ERROR` | GF Wordbench could not reliably execute or interpret a required criterion |
| `SKIPPED` | Work was explicitly omitted under the selected mode or dependency policy |

Execution state is separate:

```text
completed
timed_out
cancelled
launch_failed
not_started
```

A completed operation may still have validation status `FAIL`.

A timed-out or cancelled required operation cannot produce an overall `OK` result.

---

## 12. Open the run directory

Each run creates an owned directory:

```text
<OUT>/run_<run-id>/
```

Canonical structure:

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── details/
├── raw/
│   ├── master.log
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

Start with:

```text
summary.md
```

For machine-readable truth, use:

```text
summary.json
```

For AI-assisted diagnosis, use:

```text
AI_READY.md
```

For exact GF evidence, inspect:

```text
raw/compile/
raw/scenarios/
raw/master.log
```

Reports are projections of captured structured evidence. They do not rerun GF.

---

## 13. A successful quick run

A successful focused run shows:

```text
mode: quick
target: selected file
execution state: completed
validation status: OK
compile status: OK
required reports: present
```

A generated `.gfo`, when required and retained, appears under the current run’s artifact tree.

A successful `quick` run proves only the selected quick contract. Continue to the applicable checkpoint before treating a subsystem as validated.

---

## 14. A failed quick run

A failed or errored run preserves, when available:

```text
exact GF executable
GF version
working directory
ordered command
timeout
exit code
stdout
stderr
source fingerprint
scan findings
primary diagnostic
causal classification
artifact paths
```

Canonical causal classes:

```text
direct
downstream
ambiguous
noise
skipped
```

For a focused file, inspect:

```text
summary.md
AI_READY.md
raw/compile/<safe-target-key>.stdout.txt
raw/compile/<safe-target-key>.stderr.txt
raw/scan/<safe-target-key>.scan.txt
```

Do not edit a gold file to repair a compilation failure. Gold files validate reviewed scenario output, not compiler success.

---

## 15. Run a checkpoint

After the focused providers compile, validate a configured subsystem.

```powershell
gf-wordbench validate `
  --mode checkpoint `
  --target "checkpoint:morphology" `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Checkpoint IDs come from the active project configuration.

A checkpoint run may validate:

```text
checkpoint prerequisites
owned source files
checkpoint modules
relevant entrypoint reachability
applicable required scenarios
declared gold comparisons
```

An arbitrary file group is not a checkpoint unless the project contract defines it as one.

---

## 16. Run a scenario directly

Use a registered scenario ID:

```powershell
gf-wordbench validate `
  --mode quick `
  --target "scenario:load-main" `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Scenarios are stored under:

```text
project/validation/scenarios/
```

A scenario is registered in the active-project configuration.

A zero process exit code is insufficient. GF Wordbench also checks:

```text
timeout
fatal diagnostics
required markers
required sections
assertions
gold comparison
required artifacts
```

Normal validation never updates `.gold` files.

---

## 17. Use diagnostic mode

Use `diagnostic` when:

```text
the first failing provider is unclear
several modules fail downstream
a scenario fails without a clear cause
broader raw evidence is required
a regression must be compared
```

```powershell
gf-wordbench validate `
  --mode diagnostic `
  --target "entrypoint:GrammarXxx" `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Diagnostic mode may continue after independent failures to collect bounded evidence safely.

It is not release evidence. After repairing the defect, rerun the mode that owns the required proof.

---

## 18. Run release validation

Run `release` when:

```text
required checkpoints are defined
required entrypoints exist
required scenarios are registered
required gold files are reviewed
release criteria are documented
known blocking issues are resolved
```

```powershell
gf-wordbench validate `
  --mode release `
  --project-root "<WORKSPACE_ROOT>" `
  --gf-executable "<GF>" `
  --rgl-root "<RGL>" `
  --output-root "<OUT>"
```

Release mode validates the complete configured release scope, including applicable:

```text
required source scans
required checkpoints
required entrypoints
PGF construction
required scenarios
required assertions
required gold comparisons
release gates
required reports
artifact manifest
manifest verification
```

Only a completed successful `release` run is release-eligible.

A successful `quick`, `checkpoint` or `diagnostic` run cannot be promoted afterward into release evidence.

---

## 19. Start the GUI

When GUI dependencies are installed:

```powershell
gf-wordbench gui
```

The GUI resolves the same inputs as the CLI:

```text
workspace root
GF executable
RGL root
output root
mode
target
allowed run options
```

Equivalent GUI and CLI inputs produce equivalent resolved run configuration.

The GUI does not define separate validation behavior.

---

## 20. Use a Windows launcher

Repository launchers are convenience entrypoints only.

PowerShell launcher:

```powershell
.\run-gf-wordbench.ps1 --help
.\run-gf-wordbench.ps1 gui
.\run-gf-wordbench.ps1 validate --mode quick --target "file:lib/src/example/MorphoXxx.gf"
```

Command Prompt launcher:

```bat
run-gf-wordbench.cmd --help
run-gf-wordbench.cmd gui
run-gf-wordbench.cmd validate --mode quick --target "file:lib/src/example/MorphoXxx.gf"
```

A launcher forwards arguments to the canonical CLI. It does not contain hidden validation policy, project identity or personal absolute paths.

GF Wordbench remains runnable without launchers.

---

## 21. Remember local paths

GF Wordbench may store local convenience values in:

```text
.gf_wordbench_state.json
```

Typical values include:

```text
workspace root
RGL root
GF executable
output root
last mode
last target
last run path
```

The state file is local and disposable.

It does not define:

```text
language identity
source directory
entrypoints
checkpoints
required scenarios
release requirements
project registry
portfolio membership
```

Deleting it does not damage the active project or change its contract.

---

## 22. First-day workflow

```text
1. verify gf --version
2. create and activate .venv
3. install gf-wordbench
4. inspect project/project.toml
5. run gf-wordbench config check
6. run quick on one small source file
7. fix direct compile failures
8. run quick on an entrypoint or load scenario
9. run one configured checkpoint
10. inspect summary.md and raw evidence
```

Preserve the first diagnostic evidence. It provides a useful regression baseline.

---

## 23. Typical development loop

```text
edit one coherent provider/consumer change
→ quick validation
→ inspect result
→ fix direct failure
→ rerun quick
→ checkpoint validation
→ update scenario or gold only when behavior intentionally changed
→ rerun checkpoint
```

When a public GF contract changes, review:

```text
direct consumers
downstream entrypoints
scenario coverage
gold expectations
module dependency map
known issues
release criteria
decision log
project interfile contract
```


---

## 24. Gold changes

A normal run never changes:

```text
project/validation/gold/*.gold
```

When an intentional grammar change modifies normalized scenario output:

1. run the scenario;
2. inspect raw and normalized output;
3. verify linguistic correctness;
4. inspect the diff;
5. use the explicit gold-update workflow;
6. commit the reviewed gold change;
7. rerun the proving mode.

Never accept a new gold merely to make a failure disappear.

---

## 25. Exit-code expectations

The exact mapping is defined in:

```text
docs/reference/EXIT_CODES.md
```

General expectation:

```text
0  selected validation passed
1  validation failures were found
2  invalid command or configuration input
3+ runtime, tool or framework error according to the reference
```

Automation uses documented exit codes and `summary.json`. It does not parse human report prose.

---

## 26. Common setup failures

### 26.1 `gf-wordbench` is not recognized

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip show gf-wordbench
python -m pip install -e .
```

Reopen the shell when environment activation changes are not visible.

### 26.2 GF executable is missing

```powershell
Test-Path "<GF>"
& "<GF>" --version
```

Select the executable file, not its parent directory.

### 26.3 RGL root is wrong

Run:

```powershell
gf-wordbench config check --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Inspect the resolved GF path reported by the checker.

### 26.4 Source directory is missing

Correct `project/project.toml` or restore the project files.

GF Wordbench does not create a missing source directory automatically.

### 26.5 Entrypoint is missing

Correct the configured filename or create the intended GF module.

GF Wordbench does not guess another entrypoint from naming conventions.

### 26.6 Required scenario is missing

Restore or create:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Then verify that the registry and script ID agree.

### 26.7 Required gold is missing

Create it only through the reviewed gold-update workflow.

A release run does not create it automatically.

### 26.8 Output root is not writable

Select a writable directory outside protected source locations.

Run-owned directories may be created automatically under the approved output root.

### 26.9 Paths contain spaces

Pass each path as one quoted argument.

Do not store embedded quote characters inside path values.

### 26.10 GF works manually but not in GF Wordbench

Compare:

```text
resolved executable
working directory
effective GF path
GF version
ordered command arguments
environment overrides
```

Use raw run evidence rather than the rendered summary alone.

---

## 27. What not to do

Do not:

- hardcode the active language in framework configuration;
- store the GF executable in portable `project.toml`;
- use application state as project truth;
- define several active projects in one Wordbench workspace;
- store or read private `gf-portfolio` state from Wordbench;
- run release mode with required stages disabled;
- treat a zero scenario exit code as complete success;
- update gold during ordinary validation;
- parse `summary.md` in automation when `summary.json` exists;
- reuse old `.gfo` files as unverified release proof;
- run untrusted `.gfs` scenarios outside an appropriate trust boundary;
- edit raw evidence after the run;
- infer project identity from an old run directory;
- treat incomplete finalization as an `OK` run.

---

## 28. Minimal command set

Installation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Verification:

```powershell
gf-wordbench --version
gf-wordbench --help
```

Configuration:

```powershell
gf-wordbench config check --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Focused validation:

```powershell
gf-wordbench validate --mode quick --target "file:<PROJECT-RELATIVE-PATH>" --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Checkpoint:

```powershell
gf-wordbench validate --mode checkpoint --target "checkpoint:<ID>" --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Diagnostic:

```powershell
gf-wordbench validate --mode diagnostic --target "entrypoint:<MODULE>" --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Release:

```powershell
gf-wordbench validate --mode release --project-root "<WORKSPACE_ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

GUI:

```powershell
gf-wordbench gui
```

---

## 29. Next documents

### Installation and environment

```text
docs/usage/INSTALLATION.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_VERSION_COMPATIBILITY.md
```

### Configuration

```text
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
```

### Validation

```text
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
```

### Scenarios

```text
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/GOLDEN_TESTS.md
```

### Interfaces

```text
docs/usage/CLI_REFERENCE.md
docs/usage/GUI_REFERENCE.md
docs/operations/WINDOWS_LAUNCHERS.md
```

### Project lifecycle

```text
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
```

### Diagnostics and reports

```text
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
```

### Run lifecycle

```text
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md
```

---

## 30. Quick-start completion checklist

```text
[ ] Repository root opened
[ ] Supported Python available
[ ] Virtual environment created
[ ] GF Wordbench installed
[ ] GF executable launches
[ ] GF version recorded
[ ] RGL root identified
[ ] project/project.toml validated
[ ] Source directory exists
[ ] Entrypoint exists
[ ] Output root is writable
[ ] Configuration check passes
[ ] First quick target selected
[ ] Quick run completed
[ ] summary.md reviewed
[ ] summary.json preserved
[ ] Raw GF evidence available
[ ] Next checkpoint identified
```

---

## 31. Governing rule

A reliable first run has:

```text
one active project
+ one explicit GF executable
+ one explicit RGL root
+ one writable output root
+ one bounded quick target
```

Then execute:

```text
config check
→ quick
→ checkpoint
→ release
```

Use `diagnostic` whenever a failure needs broader evidence.

Do not weaken a mode to make it pass. Correct the project, configuration or local environment, then rerun the mode that owns the required proof.
