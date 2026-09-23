# GF Wordbench

**GF Wordbench** is a validation, diagnostics, regression-testing, and
release-readiness workbench for
[Grammatical Framework](https://www.grammaticalframework.org/) languages.

It combines static source checks with native GF execution, structured
diagnostics, scripted scenarios, reviewed golden outputs, previous-run
comparison, and reproducible audit artifacts.

```text
explicit selected language path
    → bounded language probe
    → resolved language context
    → static scan
    → GF compilation
    → optional validation-profile scenarios and release policy
    → normalized evidence
    → classification and regression analysis
    → human, machine, and AI-ready reports
```

A running session has zero or one resolved language context. An ordinary run
resolves exactly one portable language identity and one immutable source
context. Portfolio-scale aggregation belongs to the independent
`gf-portfolio` product; GF Wordbench has no runtime dependency on it.

Diagnostic Global Scan also emits Compendium-aligned certification evidence. In
a standard RGL layout it expands the language census to same-suffix root API
facades, fingerprints the exact census with a source-lock SHA-256, records
module-level RGL coverage, and emits a TEST_RGL matrix that keeps structural
compilation separate from linguistic scenario/golden certification.

---

## Contents

- [Goals](#goals)
- [Core principles](#core-principles)
- [Language startup](#language-startup)
- [Validation profiles](#validation-profiles)
- [Validation modes](#validation-modes)
- [Validation pipeline](#validation-pipeline)
- [Quick start](#quick-start)
- [Run outputs](#run-outputs)
- [Status and diagnostic semantics](#status-and-diagnostic-semantics)
- [Architecture](#architecture)
- [Anti-drift contracts](#anti-drift-contracts)
- [Repository layout](#repository-layout)
- [Documentation](#documentation)
- [Native GF scenarios](#native-gf-scenarios)
- [Output normalization](#output-normalization)
- [Development](#development)
- [Compatibility](#compatibility)
- [Security](#security)
- [Non-goals](#non-goals)
- [Contributing](#contributing)
- [License](#license)

---

## Goals

GF Wordbench provides a reproducible workflow for answering questions such as:

- Do selected GF sources satisfy the framework's static source rules?
- Does a selected module compile with the intended GF executable and search
  path?
- Which language directory, source root, and portable language identity were
  resolved from the selected path?
- Do configured checkpoints and final entrypoints load successfully when an
  explicit validation profile supplies that policy?
- Do parsing, linearization, morphology, and bounded-generation scenarios
  behave as expected?
- Did the current run improve, regress, or remain unchanged relative to a
  compatible previous run?
- Which failures are direct, downstream, ambiguous, or infrastructure-related?
- Which raw files prove every reported conclusion?
- Is the resolved language ready for a profile-defined release build?

The workbench is intended for:

- GF language maintainers;
- contributors repairing or extending an RGL language;
- reviewers validating cross-file changes;
- automation and continuous integration;
- AI-assisted diagnosis grounded in preserved evidence.

---

## Core principles

### GF remains authoritative

GF Wordbench does not reimplement the GF parser, type checker, module resolver,
runtime, generation engine, or PGF format.

Static scanning can identify suspicious source patterns. Native GF execution
remains authoritative for GF syntax, typing, loading, parsing, linearization,
generation, and artifact production.

### Startup begins with an explicit language path

Normal startup begins from one explicit selected language path. The selected
value may identify a language directory or a `.gf` source file.

The language probe performs bounded inspection, coordinates the existing source
selection, GF-path, structural-preflight, and diagnostic services, and publishes
a `ResolvedLanguageContext` only after required structural validation.

Candidate discovery is provisional. A `LanguageCandidate` cannot authorize an
ordinary run.

### One resolved context per run

A resolved language context is the sole runtime authority for:

- the selected machine-local path;
- the validated language directory;
- the approved source root;
- the portable language identity;
- the effective GF path;
- capability status;
- bounded diagnostics and remediation choices.

Application state, GUI widgets, old run directories, and framework defaults must
not redefine those facts.

### Validation policy is optional

A validation profile is optional for:

- browsing;
- source selection;
- static scanning;
- targeted compilation.

A profile is required only for policy it explicitly owns, such as configured
checkpoints, scenarios, gold comparisons, release gates, and profile-specific
artifacts.

A validation profile augments the resolved language context. It must not replace
the selected language, escape the approved source root, or redefine the
effective language identity.

### Evidence before interpretation

Every process-backed validation preserves raw evidence before diagnostics or
normalization:

- executable and ordered arguments;
- working directory;
- effective GF search path;
- start and finish times;
- duration;
- exit code;
- timeout, cancellation, or launch state;
- stdout;
- stderr;
- produced artifacts.

A parser or report failure must not erase valid GF evidence.

### Structured results

Files and scenarios produce typed results. Reports consume finalized results;
they do not rerun GF or reconstruct missing evidence.

The primary persisted run record is:

```text
run_<run-id>/summary.json
```

Human-readable reports are projections of structured results, not independent
sources of truth.

### Deterministic validation

Given equivalent sources, configuration, GF version, and scenario inputs, the
workbench aims to produce deterministic:

- file selection;
- execution order;
- normalized outputs;
- result ordering;
- regression comparisons;
- manifests;
- reports.

### Explicit compatibility

Persisted formats have schema identities and versions. Breaking changes require
an explicit migration or documented compatibility policy.

Cross-file, external-tool, persisted-schema, and language-profile contracts are
maintained explicitly.

---

## Language startup

The normal startup boundary is path-resolved rather than repository-project
resolved.

```text
selected path
    → language candidate
    → structural and capability checks
    → resolved language context
    → runtime composition
```

The probe may:

- interpret one explicit selected file or directory;
- derive the candidate language directory;
- inspect supported ancestors within documented bounds;
- classify common GF module roles from filenames;
- coordinate public source-selection and GF-path services;
- offer bounded exact-name remediation for a typed missing-module diagnostic;
- publish one resolved context after required checks pass.

The probe must not:

- recursively enumerate source files by itself;
- parse full GF import semantics;
- construct native GF commands;
- call subprocess APIs directly;
- write reports or state;
- require a global language catalog;
- require a validation profile for source-ready startup;
- mutate language sources or profile files.

Switching languages disposes the old runtime and constructs a new resolved
context. Active-run language mutation is forbidden.

---

## Validation profiles

A validation profile is an optional, explicit, external policy package. It is
not the normal language-startup authority.

The repository-owned reusable template lives at:

```text
templates/validation-profile/
```

Create or inspect a profile with:

```text
python scripts/init_project.py --help
```

Initialization reads the language-neutral template and writes to an explicit
destination selected by the caller. It must not recreate a repository-owned
active project directory.

A profile may contain:

```text
<explicit-profile-destination>/
├── project.toml
├── docs/
└── validation/
    ├── scenarios/
    ├── gold/
    └── inputs/
```

Profile-owned paths are interpreted relative to the explicit profile root.
Machine-local executable, RGL, output, and state paths remain environment or
application concerns.

Profiles may define:

- project and profile identity;
- source filters that remain inside the resolved language context;
- checkpoints;
- final entrypoints;
- validation modes and targets;
- required and optional scenarios;
- normalization and gold policy;
- release gates;
- expected release artifacts.

---

## Validation modes

GF Wordbench exposes four canonical modes.

| Mode | Purpose | Typical scope |
|---|---|---|
| `quick` | Fast local feedback | One explicit file or module, static scan, targeted compilation |
| `checkpoint` | Validate a coherent profile-defined layer | Configured checkpoint modules and required checkpoint scenarios |
| `release` | Prove profile-defined release readiness | Checkpoints, final entrypoints, required scenarios, PGF build, and release gates |
| `diagnostic` | Collect broad evidence | Expanded source, scenario, and diagnostic coverage within approved bounds |

Legacy mode names may be accepted only through explicit compatibility handling:

```text
file → quick
all  → diagnostic
```

### Quick

Quick mode is designed for focused source work. It may run without a validation
profile when the selected target and resolved context provide sufficient
information.

Expected work includes:

- resolve the explicit target inside the language directory;
- run static checks;
- compile the target when enabled;
- preserve evidence;
- emit normal run results and reports.

Quick mode is not release evidence.

### Checkpoint

Checkpoint mode requires profile-owned checkpoint policy.

Expected work includes:

- resolve configured checkpoint modules inside the resolved language context;
- execute required checkpoint scenarios;
- compare applicable gold files;
- detect regressions relative to a compatible previous run.

### Release

Release mode requires an explicit compatible validation profile.

Expected work includes:

- profile and schema validation;
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

Diagnostic mode is optimized for evidence collection and fault isolation.

It may include:

- broader approved source enumeration;
- configured scans and compilations;
- optional scenarios;
- introspection commands;
- extended logs;
- additional retained details.

A diagnostic run may be slower and larger than a normal development run.

---

## Validation pipeline

The orchestration layer owns execution order. Individual stages remain isolated.

```text
1. Accept one explicit selected language path
2. Probe and publish one resolved language context
3. Load an optional explicit validation profile
4. Resolve local environment and the GF toolchain
5. Build one immutable run configuration
6. Create the owned run directory
7. Select source files through the canonical selection service
8. Capture source fingerprints
9. Run static source scans
10. Compile selected GF modules
11. Classify direct and downstream file failures
12. Execute profile-defined native GF scenarios when applicable
13. Normalize scenario output
14. Compare reviewed gold files
15. Build final PGF when required
16. Compare with a compatible previous run
17. Build structured file and scenario results
18. Write reports and raw logs
19. Generate and verify the artifact manifest
20. Evaluate mode-specific success criteria
```

A failure in one report writer must not invalidate raw evidence captured by an
earlier stage.

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
- Git for normal development and reviewed changes.

GF Wordbench records the exact executable and effective GF path used for each
run.

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

On Windows, an explicit path to `gf.exe` may be configured instead of relying
on `PATH`.

### 4. Inspect the command surfaces

```text
python -m gf_wordbench --help
gf-wordbench --help
gf-wordbench-gui
```

Use the CLI help for the integrated command and option names of the checked-out
revision.

### 5. Select a language

Start from an explicit language directory or `.gf` file. The CLI, GUI, or
automation must pass that selection through the normal language probe before
constructing an ordinary run.

An environment-provided selected path is still untrusted input and must pass the
same probe.

### 6. Add a validation profile only when needed

For checkpoint, scenario, gold, or release policy, create or select an explicit
validation profile:

```text
python scripts/init_project.py --help
```

The profile destination is external and explicit. Source-ready startup does not
depend on it.

### 7. Inspect generated evidence

A finalized run normally contains:

```text
summary.md
AI_READY.md
summary.json
manifest.json
details/
raw/
artifacts/
```

Do not diagnose from a summary alone when raw stdout, stderr, or scenario
transcripts are available.

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

The canonical machine-readable run record contains versioned:

- metadata;
- totals;
- artifact paths;
- file results;
- scenario results;
- diff entries;
- top errors.

Automation, GUI projections, comparison logic, and migration tooling should
consume this file rather than parse Markdown reports.

### `summary.md`

A human-readable audit summary containing:

- run summary;
- outcome;
- file results;
- scenario results;
- regression comparison;
- artifact references.

### `AI_READY.md`

A bounded evidence packet for human or AI-assisted diagnosis. It must:

- derive conclusions from structured results;
- distinguish direct and downstream failures;
- reference raw evidence;
- avoid rerunning GF;
- avoid unsupported diagnosis;
- exclude secrets.

### `manifest.json`

The artifact inventory for a finalized run records, as applicable:

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

Normalization, diagnostic parsing, and reporting produce derived evidence
without replacing original process output.

---

## Status and diagnostic semantics

Process execution and validation interpretation are separate dimensions.

### Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

| Status | Meaning |
|---|---|
| `OK` | Validation completed and met its criteria |
| `FAIL` | Validation executed but did not meet its criteria |
| `ERROR` | GF Wordbench could not correctly execute or interpret validation |
| `SKIPPED` | Validation was intentionally not executed |

### Execution state

Process-level facts include:

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
| `direct` | Evidence indicates that this subject directly owns the failure |
| `downstream` | The subject is blocked by another known failure |
| `ambiguous` | Available evidence does not safely establish ownership |
| `noise` | The result is excluded or non-actionable under policy |
| `skipped` | Validation did not run |

### Error kind

Error kind describes the nature of a failure separately from causal ownership.

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

A non-zero process exit does not by itself determine whether a failure is direct
or downstream.

---

## Architecture

GF Wordbench is one deployable hexagonal modular monolith.

```text
CLI / GUI
    → public application and project use cases
        → resolved-language probe
        → configuration resolution
        → run planning and orchestration
            → source selection
            → static scanning
            → GF compilation
            → scenario execution
            → diagnostics and classification
            → regression comparison
            → result construction
        → report writers
        → persisted artifacts
```

### Dependency direction

Expected high-level direction:

```text
entrypoints → application/use cases → domain models + ports
bootstrap   → use cases + ports + adapters
adapters    → ports + infrastructure + external systems
reporting   → finalized results + artifact readers
```

Foundation packages remain below projects, state, entrypoints, and concrete
composition.

Prohibited examples include:

```text
reports → compiler execution
reports → scanner execution
domain models → concrete adapters
kernel → projects or entrypoints
language probe → GUI widgets
language probe → subprocess
runtime packages → gf-portfolio
```

Reports consume completed results. They do not create new validation evidence.

### Canonical implementation areas

| Responsibility | Canonical area |
|---|---|
| Shared kernel contracts | `src/gf_wordbench/kernel/` |
| Configuration | `src/gf_wordbench/config/` |
| Infrastructure and process execution | `src/gf_wordbench/infrastructure/` |
| Language probing and optional profiles | `src/gf_wordbench/projects/` |
| Disposable application state | `src/gf_wordbench/state/` |
| Run planning and result construction | `src/gf_wordbench/runs/` |
| Validation stages | `src/gf_wordbench/validation/` |
| Diagnostics and classification | `src/gf_wordbench/diagnostics/` |
| Reporting and schemas | `src/gf_wordbench/reporting/` |
| CLI and GUI | `src/gf_wordbench/entrypoints/` |
| Runtime composition | `src/gf_wordbench/bootstrap.py` |

See
[`docs/architecture/ARCHITECTURE_OVERVIEW.md`](docs/architecture/ARCHITECTURE_OVERVIEW.md).

---

## Anti-drift contracts

GF Wordbench maintains coordinated anti-drift authorities.

| Path | Scope |
|---|---|
| [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](docs/DOCUMENTATION_ALIGNMENT_LOCK.md) | Cross-document product identity, authority order, and correction rules |
| [`docs/DOCUMENTATION_CORRECTION_LEDGER.md`](docs/DOCUMENTATION_CORRECTION_LEDGER.md) | Coordination of documentation corrections |
| [`docs/INTERFILE_CONTRACT_LOCK.md`](docs/INTERFILE_CONTRACT_LOCK.md) | Python ownership, imports, re-exports, and provider-consumer boundaries |
| [`docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`](docs/EXTERNAL_TOOL_CONTRACT_LOCK.md) | GF, process, filesystem, and platform boundaries |
| [`docs/PERSISTED_SCHEMA_LOCK.md`](docs/PERSISTED_SCHEMA_LOCK.md) | Versioned persisted formats and migrations |
| [`templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md`](templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md) | Language-neutral validation-profile lock template |

### Contract-change rule

A provider and every consumer form one coordinated change unit when their shared
contract changes.

A contract-changing edit must review, as applicable:

- the owner;
- direct and downstream consumers;
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

The command surface is defined by the integrated CLI implementation and its
reference documentation. Verify the checked-out revision with:

```text
python -m gf_wordbench --help
```

---

## Repository layout

```text
GF_Wordbench/
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.md
├── DOCUMENT_MANIFEST.json
├── pyproject.toml
├── src/
│   └── gf_wordbench/
│       ├── config/
│       ├── diagnostics/
│       ├── entrypoints/
│       ├── infrastructure/
│       ├── kernel/
│       ├── projects/
│       ├── reporting/
│       ├── runs/
│       ├── state/
│       └── validation/
├── scripts/
├── tools/
│   └── diagnostics/
├── tests/
├── docs/
└── templates/
    └── validation-profile/
```

Generated runs belong under an explicitly configured output root. They must not
be mixed into language source directories.

The repository does not require or recreate an authoritative active
`project/` directory.

---

## Documentation

Start with:

- [`docs/00_START_HERE.md`](docs/00_START_HERE.md)
- [`docs/DOCUMENTATION_MAP.md`](docs/DOCUMENTATION_MAP.md)
- [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md)
- [`docs/GLOSSARY.md`](docs/GLOSSARY.md)

### Architecture

- [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](docs/architecture/ARCHITECTURE_OVERVIEW.md)
- [`docs/architecture/CANONICAL_FILE_ARCHITECTURE.md`](docs/architecture/CANONICAL_FILE_ARCHITECTURE.md)
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

Scenarios are `.gfs` files executed through the GF process boundary.

They may validate:

- grammar loading;
- missing functions;
- parsing;
- linearization;
- morphology;
- abstract-tree inspection;
- bounded generation;
- PGF-facing behavior.

A profile-defined scenario must have:

- a unique configured identifier;
- a declared required or optional status;
- a known grammar entrypoint;
- bounded behavior;
- stable begin and end markers;
- explicit success criteria;
- preserved raw stdout and stderr;
- a normalization version;
- a reviewed gold file when comparison is required.

Normal validation is read-only with respect to `.gold` files.

Gold updates require an explicit reviewed operation. A missing required gold file
is a failure, not an automatic creation request.

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

It must not remove linguistically or diagnostically meaningful information,
including:

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

Any normalization change that alters existing gold comparisons is a contract
change and requires deliberate gold review.

---

## Development

Install development dependencies:

```text
python -m pip install -e ".[dev]"
```

Core checks:

```text
python -m compileall -q src tools scripts
python -m gf_wordbench --help
python -m pytest --collect-only -q
python -m pytest tests/contracts -q
python -m pytest tests/components -q
python -m pytest tests/unit -q
python tools/diagnostics/run_safe_suite.py
```

Repository checks:

```text
git diff --check
git status --short
```

Real-GF integration tests should remain clearly separated from fast unit tests.

Development changes should preserve:

- CLI and GUI semantic equivalence;
- typed component boundaries;
- single artifact and symbol ownership;
- resolved-language authority;
- optional-profile boundaries;
- raw evidence;
- deterministic serialization;
- backward-compatible schema behavior;
- source, profile, and framework separation.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`docs/development/CODING_STANDARDS.md`](docs/development/CODING_STANDARDS.md).

---

## Compatibility

GF Wordbench maintains separate compatibility policies for:

- Python package versions;
- GF executable versions;
- validation-profile schema versions;
- application state;
- run summaries;
- manifests;
- normalized scenario outputs;
- gold files;
- cross-file contracts.

Legacy data may be imported only through documented migrations or explicit
compatibility aliases.

Examples include:

```text
.gf_audit_state.json → .gf_wordbench_state.json
unversioned summary.json → gf-wordbench.run-summary/1.0
mode=file → mode=quick
mode=all → mode=diagnostic
ai_brief_path → artifacts.ai_ready
```

Canonical writers emit only current GF Wordbench formats. Legacy aliases are
read-only compatibility inputs.

See:

- [`docs/development/BACKWARD_COMPATIBILITY.md`](docs/development/BACKWARD_COMPATIBILITY.md)
- [`docs/release/MIGRATION_AND_DEPRECATION.md`](docs/release/MIGRATION_AND_DEPRECATION.md)
- [`docs/PERSISTED_SCHEMA_LOCK.md`](docs/PERSISTED_SCHEMA_LOCK.md)

---

## Security

Selected language paths, profile paths, scenario files, and external-tool
arguments cross trust boundaries.

GF Wordbench must:

- launch normal GF processes without an implicit command shell;
- pass executable arguments as an ordered list;
- validate paths before use;
- keep owned artifacts inside approved roots;
- prevent profiles from escaping the resolved language context;
- treat `.gfs` scenarios as executable input;
- prohibit operating-system escape commands unless explicitly enabled;
- avoid complete environment dumps;
- avoid persisting passwords, tokens, private keys, or credentials;
- preserve enough evidence to audit external execution safely.

Do not run untrusted profile scenarios without reviewing them.

See [`SECURITY.md`](SECURITY.md).

---

## Non-goals

GF Wordbench is not intended to:

- replace GF;
- require a global runtime language catalog;
- require a repository-owned language bundle for normal startup;
- require a validation profile for source browsing or targeted compilation;
- edit GF source automatically during normal validation;
- update gold files implicitly;
- run multiple active language contexts in one ordinary session;
- infer release readiness from one successful file;
- hide raw tool output behind a diagnosis;
- use GUI state as authoritative language configuration;
- treat human-readable reports as stable machine schemas;
- silently accommodate breaking persisted-format changes;
- import or require `gf-portfolio` at runtime.

---

## Contributing

Contributions should be small enough to review but complete across every
affected contract.

Before submitting a change:

1. identify affected owners, providers, and consumers;
2. classify the change as internal, compatible, or breaking;
3. update tests and scenarios when their contracts or assertions change;
4. review gold impact;
5. preserve or migrate persisted formats;
6. update the relevant contract authority;
7. update user and developer documentation;
8. run the appropriate validation evidence;
9. verify `git diff --check` and a clean intended worktree.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

GF Wordbench is distributed under the terms documented in
[`LICENSE.md`](LICENSE.md).

Third-party components, including Grammatical Framework and language resources,
retain their own licenses.
