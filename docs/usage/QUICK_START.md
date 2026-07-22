# GF Wordbench — Quick Start

**Document ID:** `GF-WB-QUICK-START`  
**Status:** Final user guide  
**Applies to:** First local installation, first active-project validation, CLI and GUI startup  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\usage\QUICK_START.md`  
**Guide version:** `1.0.0`  
**Last reviewed:** `2026-07-21`

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

GF Wordbench manages one active GF language project per copy.

The active project is defined by:

```text
project/project.toml
```

GF remains the execution engine.

GF Wordbench selects, runs, captures, classifies and reports the validation evidence.

---

## 2. Expected repository root

Examples in this guide assume the repository root is:

```text
C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench
```

Open PowerShell or Command Prompt in that directory before running commands.

PowerShell example:

```powershell
Set-Location "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench"
```

The repository root should contain at least:

```text
app/
docs/
project/
templates/
tests/
pyproject.toml
```

The active project should contain:

```text
project/
├── project.toml
├── docs/
└── validation/
```

The GF language sources may live inside the repository or in the project-relative source location declared by `project.toml`.

---

## 3. Prerequisites

Required:

```text
Python supported by pyproject.toml
Grammatical Framework executable: gf or gf.exe
GF Resource Grammar Library sources or equivalent GF library root
one initialized active project
```

Recommended:

```text
Git
PowerShell on Windows
an editor with TOML and Markdown support
```

GF Wordbench does not install or replace Grammatical Framework.

Before continuing, know the local paths to:

```text
GF executable
RGL root
output root
```

Windows example:

```text
GF executable:
C:\tools\gf\gf.exe

RGL root:
C:\work\gf-rgl\src

Output root:
C:\work\gf-wordbench-runs
```

Paths containing spaces are supported.

---

## 4. Verify GF directly

Run GF outside GF Wordbench first.

PowerShell:

```powershell
& "C:\tools\gf\gf.exe" --version
```

Command Prompt:

```bat
"C:\tools\gf\gf.exe" --version
```

A version line should be returned.

A missing executable, launch failure or timeout must be corrected before required GF validation can run.

Do not rely on an unknown `gf` from `PATH` when several GF installations exist.

GF Wordbench records the exact executable used for each run.

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

Install development dependencies only when working on the framework:

```powershell
python -m pip install -e ".[dev]"
```

The exact optional dependency groups are defined by `pyproject.toml`.

---

## 6. Verify the installation

Run:

```powershell
gf-wordbench --version
```

Then:

```powershell
gf-wordbench --help
```

The command should be available inside the activated virtual environment.

When the console script is unavailable during source development, the package module entrypoint may be used if supported by the final package configuration:

```powershell
python -m app.main_cli --help
```

The installed console command remains the preferred interface.

---

## 7. Verify the active project

Open:

```text
project/project.toml
```

It must identify one active language project.

At minimum, verify:

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

Do not store local absolute paths to `gf.exe`, the RGL or run output inside `project.toml`.

Those values belong to local environment configuration or explicit run input.

---

## 8. Validate configuration before running GF

Use the configuration checker:

```powershell
gf-wordbench config check `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Single-line equivalent:

```powershell
gf-wordbench config check --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" --gf-executable "C:\tools\gf\gf.exe" --rgl-root "C:\work\gf-rgl\src" --output-root "C:\work\gf-wordbench-runs"
```

The checker should verify:

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

Typical configuration failures:

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

For the first run, choose one small GF source file that should compile.

Use a project-relative path.

Example:

```text
lib/src/example/MorphoXxx.gf
```

Do not begin with `release` mode when the project has not yet passed a focused compile.

The recommended progression is:

```text
quick
→ checkpoint
→ release
```

Use `diagnostic` whenever the cause of failure is unclear.

---

## 10. Run the first quick validation

Canonical command:

```powershell
gf-wordbench validate `
  --mode quick `
  --target "file:lib/src/example/MorphoXxx.gf" `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Single-line equivalent:

```powershell
gf-wordbench validate --mode quick --target "file:lib/src/example/MorphoXxx.gf" --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" --gf-executable "C:\tools\gf\gf.exe" --rgl-root "C:\work\gf-rgl\src" --output-root "C:\work\gf-wordbench-runs"
```

A standard `quick` run performs the bounded workflow:

```text
configuration
environment resolution
GF version probe
target selection
static scan
fingerprint
GF compilation
failure classification
report generation
```

`quick` answers:

```text
Did this focused change introduce an obvious source, scan or compilation problem?
```

It does not prove release readiness.

---

## 11. Understand the first result

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Interpretation:

| Status | Meaning |
|---|---|
| `OK` | The selected validation contract passed |
| `FAIL` | Execution completed, but a validation criterion failed |
| `ERROR` | GF Wordbench could not reliably evaluate a required criterion |
| `SKIPPED` | A stage was explicitly omitted under an allowed non-release policy |

Execution state is separate.

Examples:

```text
completed
timed_out
cancelled
launch_failed
```

A completed diagnostic run may still have validation status `FAIL`.

---

## 12. Open the run directory

Each run creates an owned directory:

```text
<output-root>\run_<run-id>\
```

Typical structure:

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

Reports do not rerun GF.

They are derived from captured evidence.

---

## 13. A successful quick run

A successful focused run should show:

```text
mode: quick
target: selected file
execution state: completed
validation status: OK
compile status: OK
required reports: present
```

The generated `.gfo`, when expected and retained, appears under the current run’s artifact tree.

A successful `quick` run proves only the selected quick contract.

Continue to a checkpoint before treating a subsystem as complete.

---

## 14. A failed quick run

A failed run should preserve:

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
classification
artifact paths
```

Common causal classes:

```text
direct
downstream
ambiguous
noise
skipped
```

For a focused file, the most useful files are usually:

```text
summary.md
AI_READY.md
raw/compile/<target>.stdout.txt
raw/compile/<target>.stderr.txt
raw/scan/<target>.scan.txt
```

Do not edit a gold file to fix a compilation failure.

Gold files validate reviewed scenario output, not compiler success.

---

## 15. Run a checkpoint

After the focused files compile, validate a configured subsystem.

Example:

```powershell
gf-wordbench validate `
  --mode checkpoint `
  --target "checkpoint:morphology" `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Checkpoint IDs come from the active project.

A checkpoint run may validate:

```text
checkpoint prerequisites
owned source files
checkpoint modules
relevant entrypoint reachability
applicable required scenarios
declared gold comparisons
```

An arbitrary file group is not automatically a checkpoint.

---

## 16. Run a scenario directly

Use a registered scenario ID:

```powershell
gf-wordbench validate `
  --mode quick `
  --target "scenario:load-main" `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Scenarios are stored under:

```text
project/validation/scenarios/
```

A scenario must be registered in the active-project configuration.

A scenario result requires more than a zero process exit code.

GF Wordbench also checks:

```text
timeout
fatal diagnostics
required markers
required sections
assertions
gold comparison
required artifacts
```

Normal validation never updates `.gold`.

---

## 17. Use diagnostic mode

Use `diagnostic` when:

```text
the first failing file is unclear
several modules fail downstream
a scenario fails without a clear cause
full raw evidence is needed
a previous regression must be compared
```

Example:

```powershell
gf-wordbench validate `
  --mode diagnostic `
  --target "entrypoint:GrammarXxx" `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Diagnostic mode may continue after independent failures to collect broader evidence.

It is not release evidence.

After fixing the defect, rerun the mode that must prove the change.

---

## 18. Run release validation

Run `release` only when:

```text
required checkpoints are defined
required entrypoints exist
required scenarios are registered
required gold files are reviewed
release criteria are documented
known blocking issues are resolved
```

Command:

```powershell
gf-wordbench validate `
  --mode release `
  --project-root "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench" `
  --gf-executable "C:\tools\gf\gf.exe" `
  --rgl-root "C:\work\gf-rgl\src" `
  --output-root "C:\work\gf-wordbench-runs"
```

Release mode validates the complete configured release scope.

It may require:

```text
all required source scans
all required checkpoints
all required entrypoints
PGF construction
all required scenarios
all required assertions
all required gold comparisons
release gates
required reports
artifact manifest
manifest verification
```

Only a completed successful `release` run may be release-eligible.

A successful `quick`, `checkpoint` or `diagnostic` run cannot be promoted afterward.

---

## 19. Start the GUI

When the GUI dependencies are installed:

```powershell
gf-wordbench gui
```

The Windows convenience launcher may also be used:

```powershell
.\launch_gui.bat
```

The GUI should request or resolve the same values as the CLI:

```text
project root
GF executable
RGL root
output root
mode
target
allowed run options
```

Equivalent GUI and CLI inputs must produce equivalent resolved run configuration.

The GUI does not define separate validation behavior.

---

## 20. Use the Windows CLI launcher

When supplied by the repository:

```powershell
.\launch_cli.bat --help
```

Example forwarding a validation request:

```powershell
.\launch_cli.bat validate --mode quick --target "file:lib/src/example/MorphoXxx.gf"
```

Launchers are convenience entrypoints.

They must not contain hidden validation policy.

The Python package must remain runnable without them.

---

## 21. Remember local paths

After a valid GUI or CLI run, GF Wordbench may store local preferences in:

```text
.gf_wordbench_state.json
```

Typical remembered values:

```text
project root
RGL root
GF executable
output root
last mode
last target
last run path
```

This file is local and disposable.

It must not define:

```text
language identity
source directory
entrypoints
checkpoints
required scenarios
release requirements
```

Deleting it must not damage the active project.

---

## 22. First-day workflow

Recommended first-day sequence:

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

Do not begin by rewriting multiple project contracts before a baseline run exists.

Preserve the first diagnostic evidence.

It becomes useful for regression comparison.

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

When a public GF contract changes, also review:

```text
direct consumers
downstream entrypoints
scenario coverage
gold expectations
module dependency map
status ledger
project interfile contract
```

---

## 24. Gold changes

A normal run must never change:

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

The exact exit-code mapping is defined in:

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

Automation should use the documented exit codes and `summary.json`.

It should not parse human report prose.

---

## 26. Common setup failures

### 26.1 `gf-wordbench` is not recognized

Check:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip show gf-wordbench
python -m pip install -e .
```

Then reopen the shell if required.

### 26.2 GF executable is missing

Verify the path directly:

```powershell
Test-Path "C:\tools\gf\gf.exe"
& "C:\tools\gf\gf.exe" --version
```

Do not select a directory instead of the executable file.

### 26.3 RGL root is wrong

The configured root must lead to the path components required by the active project.

Run:

```powershell
gf-wordbench config check ...
```

Inspect the effective GF path reported by the checker.

### 26.4 Source directory is missing

Correct `project.toml` or restore the project files.

GF Wordbench must not create a missing source directory automatically.

### 26.5 Entrypoint is missing

Correct the configured filename or create the intended GF module.

GF Wordbench must not guess another entrypoint from filename conventions.

### 26.6 Required scenario is missing

Restore or create:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Then verify that the registry and script ID agree.

### 26.7 Required gold is missing

Create it only through the explicit reviewed gold workflow.

A release run must not create it automatically.

### 26.8 Output root is not writable

Select a writable directory outside the source tree.

Run-owned directories may be created automatically.

### 26.9 Paths contain spaces

Pass them as one quoted argument.

Do not add embedded quote characters inside stored path values.

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

Use the raw run evidence rather than the rendered summary alone.

---

## 27. What not to do

Do not:

- hardcode the active language in framework configuration;
- store `gf.exe` in portable `project.toml`;
- use application state as project truth;
- run release mode with required stages disabled;
- treat a zero scenario exit code as full success;
- update gold during ordinary validation;
- parse `summary.md` in automation when `summary.json` exists;
- reuse old `.gfo` files as unverified release proof;
- run untrusted `.gfs` scenarios outside a suitable sandbox;
- edit raw evidence after the run;
- infer project identity from an old run directory.

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
gf-wordbench config check --project-root "<ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Focused validation:

```powershell
gf-wordbench validate --mode quick --target "file:<PROJECT-RELATIVE-PATH>" --project-root "<ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Checkpoint:

```powershell
gf-wordbench validate --mode checkpoint --target "checkpoint:<ID>" --project-root "<ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Diagnostic:

```powershell
gf-wordbench validate --mode diagnostic --target "entrypoint:<MODULE>" --project-root "<ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

Release:

```powershell
gf-wordbench validate --mode release --project-root "<ROOT>" --gf-executable "<GF>" --rgl-root "<RGL>" --output-root "<OUT>"
```

GUI:

```powershell
gf-wordbench gui
```

---

## 29. Next documents

Read next according to the task.

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
[ ] Active project.toml validated
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

## 31. Final quick-start rule

The reliable first run is:

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

Use `diagnostic` whenever the failure needs more evidence.

Do not weaken a mode to make it pass.

Fix the project, configuration or environment, then rerun the mode that must provide the proof.
