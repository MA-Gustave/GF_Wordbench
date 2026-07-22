# GF Wordbench

**GF Wordbench** is a validation, diagnostics, regression-testing and release-readiness workbench for [Grammatical Framework](https://www.grammaticalframework.org/) language projects.

It combines static source checks with native GF execution, structured diagnostics, scripted scenarios, reviewed golden outputs, previous-run comparison and reproducible audit artifacts.

```text
GF sources
    → static scan
    → GF compilation
    → native .gfs scenarios
    → normalized evidence
    → gold comparison
    → classification and regression analysis
    → human, machine and AI-ready reports
```

GF Wordbench is designed for **one active GF language project per repository copy**. It is not a multi-language orchestration platform.

---

## Contents

- [Goals](#goals)
- [Core principles](#core-principles)
- [Validation modes](#validation-modes)
- [Validation pipeline](#validation-pipeline)
- [Quick start](#quick-start)
- [Project model](#project-model)
- [Run outputs](#run-outputs)
- [Status and diagnostic semantics](#status-and-diagnostic-semantics)
- [Architecture](#architecture)
- [Anti-drift contracts](#anti-drift-contracts)
- [Repository layout](#repository-layout)
- [Documentation](#documentation)
- [Development](#development)
- [Compatibility](#compatibility)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Goals

GF Wordbench provides a single, reproducible workflow for answering the following questions:

- Do the selected GF source files satisfy the framework's static source rules?
- Do individual modules compile with the intended GF executable and search path?
- Do configured checkpoints and final entrypoints load successfully?
- Does the final grammar expose missing functions?
- Do parsing, linearization, morphology and bounded-generation scenarios behave as expected?
- Did the current run improve, regress or remain unchanged relative to the previous run?
- Which failures are direct, downstream, ambiguous or infrastructure-related?
- Which raw files prove every reported conclusion?
- Is the active language project ready for a release-level PGF build?

The workbench is intended for:

- GF language maintainers;
- contributors repairing or extending an RGL language;
- reviewers validating cross-file changes;
- automation and continuous integration;
- AI-assisted diagnosis grounded in preserved evidence.

---

## Core principles

### GF remains authoritative

GF Wordbench does not reimplement the GF parser, type checker, module resolver, runtime, generation engine or PGF format.

Static scanning can identify suspicious source patterns. Native GF execution remains authoritative for GF syntax, typing, loading, parsing, linearization, generation and artifact production.

### One active language project

Each repository copy contains one authoritative active project:

```text
project/project.toml
```

Language identity, source roots, module suffixes, entrypoints, checkpoints, scenarios and release targets come from that project configuration.

GUI state, old run directories and framework defaults must not redefine the active language.

### Evidence before interpretation

Every process-backed validation preserves raw evidence before diagnostics or normalization:

- executable and ordered arguments;
- working directory;
- effective GF search path;
- start and finish times;
- duration;
- exit code;
- timeout or launch state;
- stdout;
- stderr;
- produced artifacts.

A parser or report failure must not erase valid GF evidence.

### Structured results

Files and scenarios produce structured results. Reports consume those results; they do not rerun GF or reconstruct missing evidence.

The primary persisted record is:

```text
run_<run-id>/summary.json
```

Human-readable reports are projections of the structured result, not independent sources of truth.

### Deterministic validation

Given equivalent sources, configuration, GF version and scenario inputs, the workbench aims to produce deterministic:

- file selection;
- execution order;
- normalized outputs;
- result ordering;
- regression comparisons;
- manifests;
- reports.

### Explicit compatibility

Persisted formats have schema identities and versions. Breaking changes require a migration.

Cross-file, external-tool, persisted-schema and project-language contracts are maintained explicitly.

---

## Validation modes

GF Wordbench exposes four canonical modes.

| Mode | Purpose | Typical scope |
|---|---|---|
| `quick` | Fast local feedback | Modified or selected file, static scan, compile and smoke validation |
| `checkpoint` | Validate a coherent development layer | Configured checkpoint modules and required checkpoint scenarios |
| `release` | Prove release readiness | Checkpoints, final entrypoints, required scenarios, PGF build and release gates |
| `diagnostic` | Collect broad evidence | Exhaustive configured source, scenario and diagnostic coverage |

Legacy mode names may be accepted only during migration:

```text
file → quick
all  → diagnostic
```

### Quick

Use after a focused source edit.

Expected work includes:

- resolve the requested target;
- run static checks;
- compile the target when enabled;
- run configured smoke validation;
- preserve evidence and emit a normal run report.

Quick mode is optimized for speed. It is not release evidence.

### Checkpoint

Use after completing or repairing a subsystem such as morphology, categories, syntax, structural vocabulary or extensions.

Expected work includes:

- validate configured checkpoint modules;
- execute required checkpoint scenarios;
- compare applicable gold files;
- detect regressions relative to the previous compatible run.

### Release

Use before declaring the active project releasable.

Expected work includes:

- project and schema validation;
- checkpoint validation;
- final grammar and API entrypoint validation;
- required native GF scenarios;
- missing-function inspection;
- parsing and linearization coverage;
- bounded generation where configured;
- final PGF construction;
- required artifact verification;
- manifest generation;
- release-gate evaluation.

Individual `.gfo` success does not prove release readiness.

### Diagnostic

Use when the primary goal is evidence collection and fault isolation.

Diagnostic mode may include:

- broad source enumeration;
- all configured scans and compilations;
- optional scenarios;
- introspection commands;
- extended logs;
- additional retained details.

A diagnostic run may be slower and larger than normal development runs.

---

## Validation pipeline

The orchestration layer owns execution order. Individual stages remain isolated.

```text
1. Bootstrap
2. Load and validate project configuration
3. Resolve local environment and GF toolchain
4. Create the owned run directory
5. Select source files
6. Capture source fingerprints
7. Run static source scans
8. Compile selected GF modules
9. Classify direct and downstream file failures
10. Execute configured native GF scenarios
11. Normalize scenario output
12. Compare reviewed gold files
13. Build final PGF when required
14. Compare with the previous compatible run
15. Build structured file and scenario results
16. Write reports and raw logs
17. Generate and verify the artifact manifest
18. Evaluate mode-specific success criteria
```

A failure in one report writer must not invalidate raw evidence already captured by an earlier stage.

See:

- [`docs/validation/VALIDATION_PIPELINE.md`](docs/validation/VALIDATION_PIPELINE.md)
- [`docs/architecture/EXECUTION_FLOW.md`](docs/architecture/EXECUTION_FLOW.md)
- [`docs/validation/RELEASE_GATES.md`](docs/validation/RELEASE_GATES.md)

---

## Quick start

### 1. Prerequisites

Install:

- a Python version supported by `pyproject.toml`;
- a compatible GF executable (`gf` or `gf.exe`);
- the required GF RGL source tree;
- Git for normal development and reviewed gold changes.

GF Wordbench must record the exact executable and effective GF path used for each run.

### 2. Create a local environment

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Windows Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
```

POSIX shell:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### 3. Verify GF

```text
gf --version
```

On Windows, an explicit path to `gf.exe` may be configured instead of relying on `PATH`.

### 4. Configure the active project

Review:

```text
project/project.toml
```

At minimum, confirm:

- project identity;
- active language code and module suffix;
- source directory and glob;
- GF path components;
- checkpoints;
- final entrypoints;
- required and optional scenarios;
- expected release artifacts.

Project-owned paths should be relative to the project root. Local executable, RGL and output paths belong to the local environment or application state.

### 5. Inspect the command surface

```text
gf-wordbench --help
gf-wordbench audit --help
```

Canonical audit pattern:

```text
gf-wordbench audit --mode <quick|checkpoint|release|diagnostic>
```

The CLI and GUI must build equivalent run configuration for equivalent inputs.

See [`docs/usage/CLI_REFERENCE.md`](docs/usage/CLI_REFERENCE.md) for the complete command contract.

### 6. Run a quick audit

```text
gf-wordbench audit --mode quick
```

### 7. Inspect the generated run

Open:

```text
summary.md
AI_READY.md
summary.json
manifest.json
raw/
artifacts/
```

Do not diagnose from the summary alone when raw stdout, stderr or scenario transcripts are available.

---

## Project model

### Active project

The active project lives under:

```text
project/
├── README.md
├── project.toml
├── docs/
└── validation/
    ├── scenarios/
    ├── gold/
    └── inputs/
```

It contains language-specific information and may refer to the active language's GF source tree.

### Project template

A clean reusable template lives under:

```text
templates/project/
```

The template mirrors the project documentation and validation structure, but contains generic placeholders rather than active-language facts.

### Separation rule

Framework code must not contain active-language assumptions except in clearly identified examples, migration fixtures or historical compatibility tests.

```text
framework
    app/
    tests/
    docs/
    templates/

active language
    project/project.toml
    project/docs/
    project/validation/
    language GF sources
```

### Project initialization

A new language project should be created from the template and then completed deliberately:

1. assign the project identity;
2. declare source roots and GF paths;
3. register checkpoints and entrypoints;
4. define required scenarios;
5. create reviewed gold files;
6. replace project-document placeholders;
7. validate project contracts;
8. establish release criteria.

See:

- [`docs/projects/PROJECT_MODEL.md`](docs/projects/PROJECT_MODEL.md)
- [`docs/projects/CREATING_A_PROJECT.md`](docs/projects/CREATING_A_PROJECT.md)
- [`docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md`](docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md)

---

## Run outputs

Each run owns a separate directory:

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
│   ├── ALL_SCAN_LOGS.TXT
│   ├── ALL_LOGS.TXT
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

### `summary.json`

The canonical machine-readable run record.

It contains versioned:

- metadata;
- totals;
- artifact paths;
- file results;
- scenario results;
- diff entries;
- top errors.

Automation, the GUI, comparison logic and migration tooling should consume this file rather than parse Markdown reports.

### `summary.md`

A human-readable audit summary containing:

- run summary;
- outcome;
- file results;
- scenario results;
- regression comparison;
- artifact references.

### `AI_READY.md`

A bounded evidence packet designed for human or AI-assisted diagnosis.

It must:

- derive conclusions from structured results;
- distinguish direct and downstream failures;
- reference raw evidence;
- avoid rerunning GF;
- avoid unsupported diagnosis;
- exclude secrets.

### `manifest.json`

The artifact inventory for the finalized run.

It records, as applicable:

- run-relative path;
- role;
- media type;
- required status;
- file size;
- SHA-256 hash;
- producing component.

The manifest does not hash itself.

### Raw evidence

Raw stdout and stderr are immutable after capture.

Normalization, diagnostic parsing and reporting produce derived evidence without replacing the original process output.

---

## Status and diagnostic semantics

Process execution and validation interpretation are separate.

### Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

| Status | Meaning |
|---|---|
| `OK` | The validation completed and met its criteria |
| `FAIL` | The validation executed but did not meet its criteria |
| `ERROR` | GF Wordbench could not correctly execute or interpret the validation |
| `SKIPPED` | The validation was intentionally not executed |

### Execution state

Process-level state records facts such as:

```text
completed
timed_out
cancelled
launch_failed
```

Cancellation and timeout are execution conditions, not causal classifications.

### Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

| Class | Meaning |
|---|---|
| `ok` | No relevant failure |
| `direct` | Evidence indicates the selected file or scenario directly owns the failure |
| `downstream` | The result is blocked by another known failure |
| `ambiguous` | Available evidence does not safely establish ownership |
| `noise` | The result is excluded or non-actionable under the configured policy |
| `skipped` | The validation did not run |

### Error kind

The error kind describes the nature of the failure, separately from causal ownership.

Canonical kinds include:

```text
OK
OTHER
TYPE
SYNTAX
INTERNAL
TIMEOUT
SCRIPT
CONFIG
IO
TOOL
```

A non-zero process exit does not by itself determine whether a failure is direct or downstream.

---

## Architecture

GF Wordbench uses explicit layers and ownership.

```text
CLI / GUI
    → bootstrap and configuration
    → audit orchestration
        → file selection
        → static scanner
        → GF compiler
        → scenario runner
        → diagnostic parser
        → classifier
        → regression diff
        → result construction
    → report writers
    → persisted artifacts
```

### Main framework responsibilities

| Responsibility | Canonical owner |
|---|---|
| Application defaults | `app/config.py` |
| Configuration construction | `app/bootstrap.py` |
| Shared models | `app/models.py` |
| File selection | `app/audit/file_selector.py` |
| Static GF scanning | `app/audit/scanner.py` |
| GF compilation | `app/audit/compiler.py` |
| Native GF scenarios | `app/audit/scenario_runner.py` |
| Diagnostic parsing | `app/audit/diagnostics.py` |
| Failure classification | `app/audit/classifier.py` |
| Fingerprints | `app/audit/fingerprint.py` |
| Regression comparison | `app/audit/diff.py` |
| Result construction | `app/audit/result_model.py` |
| Audit orchestration | `app/audit/audit_core.py` |
| JSON report | `app/reports/report_json.py` |
| Markdown report | `app/reports/report_md.py` |
| AI-ready report | `app/reports/report_ai_ready.py` |
| Raw and aggregate logs | `app/reports/report_logs.py` |
| Detail reports | `app/reports/report_details.py` |
| Process execution | `app/utils/process_utils.py` |
| Persistent UI state | `app/state.py` |

### Dependency direction

Expected direction:

```text
CLI / GUI
    → bootstrap
    → audit core
    → stages
    → process and filesystem utilities
    → typed models
    → reports
```

Prohibited examples:

```text
reports → compiler
reports → scanner
reports → scenario runner
models → GUI
compiler → reports
scanner → compiler
classifier → process execution
```

Reports consume completed results. They do not create new audit evidence.

See [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](docs/architecture/ARCHITECTURE_OVERVIEW.md).

---

## Anti-drift contracts

GF Wordbench maintains five contract-lock files with separate scopes.

| Path | Scope |
|---|---|
| [`docs/INTERFILE_CONTRACT_LOCK.md`](docs/INTERFILE_CONTRACT_LOCK.md) | Python and framework file boundaries |
| [`docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`](docs/EXTERNAL_TOOL_CONTRACT_LOCK.md) | GF, process, filesystem and platform boundaries |
| [`docs/PERSISTED_SCHEMA_LOCK.md`](docs/PERSISTED_SCHEMA_LOCK.md) | Versioned persisted formats and migrations |
| [`project/docs/INTERFILE_CONTRACT_LOCK.md`](project/docs/INTERFILE_CONTRACT_LOCK.md) | Active language GF modules, scenarios and artifacts |
| [`templates/project/docs/INTERFILE_CONTRACT_LOCK.md`](templates/project/docs/INTERFILE_CONTRACT_LOCK.md) | Generic project-lock template |

### Contract-change rule

A provider and every consumer form one coordinated change unit when their shared contract changes.

A contract-changing edit must review, as applicable:

- provider;
- direct consumers;
- downstream consumers;
- typed models;
- configuration;
- process requests;
- persisted schemas;
- scenarios;
- gold files;
- reports;
- tests;
- documentation;
- migration notes.

### Suggested contract checks

```text
gf-wordbench contracts check
gf-wordbench contracts check --strict
gf-wordbench contracts check-external
gf-wordbench project contracts check
gf-wordbench schemas check
gf-wordbench schemas check --strict
```

The exact implemented command surface is defined by the CLI reference and must remain synchronized with the code.

---

## Repository layout

```text
GF_Wordbench/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.md
├── pyproject.toml
├── app/
│   ├── audit/
│   ├── gui/
│   ├── reports/
│   └── utils/
├── tests/
├── docs/
│   ├── architecture/
│   ├── configuration/
│   ├── decisions/
│   ├── development/
│   ├── diagnostics/
│   ├── gf/
│   ├── operations/
│   ├── projects/
│   ├── reference/
│   ├── release/
│   ├── reports/
│   ├── scenarios/
│   ├── usage/
│   └── validation/
├── project/
│   ├── project.toml
│   ├── docs/
│   └── validation/
└── templates/
    └── project/
```

Generated runs should be written to an explicitly configured output root, not mixed into language source directories.

---

## Documentation

Start with:

- [`docs/00_START_HERE.md`](docs/00_START_HERE.md)
- [`docs/DOCUMENTATION_MAP.md`](docs/DOCUMENTATION_MAP.md)
- [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md)
- [`docs/GLOSSARY.md`](docs/GLOSSARY.md)

### Architecture

- [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](docs/architecture/ARCHITECTURE_OVERVIEW.md)
- [`docs/architecture/COMPONENT_MAP.md`](docs/architecture/COMPONENT_MAP.md)
- [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md)
- [`docs/architecture/ARTIFACT_MODEL.md`](docs/architecture/ARTIFACT_MODEL.md)
- [`docs/architecture/DEPENDENCY_RULES.md`](docs/architecture/DEPENDENCY_RULES.md)

### GF integration

- [`docs/gf/GF_TOOLCHAIN_INTEGRATION.md`](docs/gf/GF_TOOLCHAIN_INTEGRATION.md)
- [`docs/gf/GF_COMPILATION.md`](docs/gf/GF_COMPILATION.md)
- [`docs/gf/GF_SCRIPT_EXECUTION.md`](docs/gf/GF_SCRIPT_EXECUTION.md)
- [`docs/gf/GF_PGF_BUILD.md`](docs/gf/GF_PGF_BUILD.md)
- [`docs/gf/GF_VERSION_COMPATIBILITY.md`](docs/gf/GF_VERSION_COMPATIBILITY.md)

### Validation and scenarios

- [`docs/validation/VALIDATION_OVERVIEW.md`](docs/validation/VALIDATION_OVERVIEW.md)
- [`docs/validation/VALIDATION_MODES.md`](docs/validation/VALIDATION_MODES.md)
- [`docs/scenarios/SCENARIO_FORMAT.md`](docs/scenarios/SCENARIO_FORMAT.md)
- [`docs/scenarios/GOLDEN_TESTS.md`](docs/scenarios/GOLDEN_TESTS.md)
- [`docs/validation/REGRESSION_COMPARISON.md`](docs/validation/REGRESSION_COMPARISON.md)

### Reports and configuration

- [`docs/reports/REPORTING_OVERVIEW.md`](docs/reports/REPORTING_OVERVIEW.md)
- [`docs/reports/SUMMARY_JSON_REFERENCE.md`](docs/reports/SUMMARY_JSON_REFERENCE.md)
- [`docs/configuration/PROJECT_TOML_REFERENCE.md`](docs/configuration/PROJECT_TOML_REFERENCE.md)
- [`docs/configuration/APPLICATION_STATE_REFERENCE.md`](docs/configuration/APPLICATION_STATE_REFERENCE.md)

### Usage and development

- [`docs/usage/INSTALLATION.md`](docs/usage/INSTALLATION.md)
- [`docs/usage/QUICK_START.md`](docs/usage/QUICK_START.md)
- [`docs/usage/CLI_REFERENCE.md`](docs/usage/CLI_REFERENCE.md)
- [`docs/usage/GUI_REFERENCE.md`](docs/usage/GUI_REFERENCE.md)
- [`docs/development/DEVELOPMENT_SETUP.md`](docs/development/DEVELOPMENT_SETUP.md)
- [`docs/development/TESTING_GF_WORDBENCH.md`](docs/development/TESTING_GF_WORDBENCH.md)

---

## Native GF scenarios

Scenarios are `.gfs` files executed by GF Wordbench through the GF shell.

They may validate:

- grammar loading;
- missing functions;
- parsing;
- linearization;
- morphology;
- abstract-tree inspection;
- bounded generation;
- PGF-facing behavior.

A scenario must have:

- a unique configured identifier;
- a declared required or optional status;
- a known grammar entrypoint;
- bounded behavior;
- stable begin/end markers;
- explicit success criteria;
- preserved raw stdout and stderr;
- a normalization version;
- a reviewed gold file when comparison is required.

Normal validation is read-only with respect to project `.gold` files.

Gold updates require an explicit reviewed operation:

```text
gf-wordbench gold update <scenario-id>
```

A missing required gold file is a failure, not an automatic creation request.

---

## Output normalization

Normalization exists only to produce stable comparison material.

It may normalize documented unstable elements such as:

- CRLF to LF;
- trailing spaces;
- known prompts;
- temporary or run-directory prefixes;
- timestamps;
- measured durations;
- platform path separators;
- explicitly version-independent banners.

It must not remove linguistically or diagnostically meaningful information, including:

- GF errors;
- relevant source filenames;
- line and column locations unless explicitly excluded;
- abstract trees;
- linearized strings;
- ambiguity counts;
- missing-function lists;
- morphology results;
- meaningful punctuation;
- Unicode distinctions.

Raw output remains unchanged.

Any normalization change that alters existing gold comparisons is a contract change and requires deliberate gold review.

---

## Development

Install development dependencies as defined by `pyproject.toml`, then run the repository's test suite.

Typical checks:

```text
python -m pytest
python -m compileall app tests
gf-wordbench contracts check --strict
gf-wordbench schemas check --strict
```

Real-GF integration tests should be clearly separated from fast unit tests.

Development changes should preserve:

- CLI/GUI semantic equivalence;
- typed component boundaries;
- single artifact ownership;
- raw evidence;
- deterministic serialization;
- backward-compatible schema behavior;
- project/framework separation.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/development/CODING_STANDARDS.md`](docs/development/CODING_STANDARDS.md).

---

## Compatibility

GF Wordbench maintains separate compatibility policies for:

- Python package versions;
- GF executable versions;
- project schema versions;
- application state;
- run summaries;
- manifests;
- normalized scenario outputs;
- gold files;
- cross-file contracts.

Legacy GF Audit data may be imported through documented migrations.

Examples include:

```text
.gf_audit_state.json → .gf_wordbench_state.json
unversioned summary.json → gf-wordbench.run-summary/1.0
mode=file → mode=quick
mode=all → mode=diagnostic
ai_brief_path → artifacts.ai_ready
```

Canonical writers emit only current GF Wordbench formats. Legacy aliases are read-only compatibility inputs.

See:

- [`docs/development/BACKWARD_COMPATIBILITY.md`](docs/development/BACKWARD_COMPATIBILITY.md)
- [`docs/release/MIGRATION_AND_DEPRECATION.md`](docs/release/MIGRATION_AND_DEPRECATION.md)
- [`docs/PERSISTED_SCHEMA_LOCK.md`](docs/PERSISTED_SCHEMA_LOCK.md)

---

## Security

GF project paths, scenario files and external-tool arguments cross trust boundaries.

GF Wordbench must:

- launch normal GF processes without an implicit command shell;
- pass executable arguments as an ordered list;
- validate paths before use;
- keep owned artifacts inside approved roots;
- treat `.gfs` scenarios as executable input;
- prohibit operating-system escape commands unless explicitly enabled;
- avoid complete environment dumps;
- avoid persisting passwords, tokens, private keys or credentials;
- preserve enough evidence to audit external execution safely.

Do not run untrusted project scenarios without reviewing them.

See [`SECURITY.md`](SECURITY.md).

---

## Non-goals

GF Wordbench is not intended to:

- replace GF;
- edit GF source automatically during normal validation;
- update gold files implicitly;
- support multiple active languages in one repository copy;
- infer release readiness from one successful file;
- hide raw tool output behind a diagnosis;
- use GUI state as authoritative project configuration;
- treat human-readable reports as stable machine schemas;
- silently accommodate breaking persisted-format changes.

---

## Contributing

Contributions should be small enough to review but complete across every affected contract.

Before submitting a change:

1. identify affected providers and consumers;
2. classify the change as internal, compatible or breaking;
3. update tests and scenarios;
4. review gold impact;
5. preserve or migrate persisted formats;
6. update the relevant contract lock;
7. update user and developer documentation;
8. run the appropriate checkpoint or release validation.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

GF Wordbench is distributed under the terms documented in [`LICENSE.md`](LICENSE.md).

Third-party components, including Grammatical Framework and language resources, retain their own licenses.
