# GF Wordbench — Start Here

**Document ID:** `GF-WB-DOC-START`  
**Status:** Normative navigation document  
**Applies to:** GF Wordbench framework, active language project, validation assets, generated runs, and project templates  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\00_START_HERE.md`  
**Documentation version:** `1.0.0`

---

## 1. Purpose

This document is the primary entry point for GF Wordbench.

Read it before:

- modifying the framework;
- creating or cloning a language project;
- changing validation behavior;
- adding a GF scenario;
- changing a persisted format;
- integrating a new external tool;
- editing a public interfile contract;
- preparing a checkpoint or release;
- interpreting a generated run.

GF Wordbench is designed around one principle:

> The framework coordinates and verifies language development, while GF remains authoritative for GF compilation and runtime behavior.

GF Wordbench does not replace GF. It organizes the work around GF, preserves evidence, detects regressions, classifies failures, executes repeatable scenarios, and produces stable reports.

---

## 2. What GF Wordbench is

GF Wordbench is a reusable development and validation framework for one active GF language project per workspace.

A GF Wordbench workspace contains:

1. a stable Python framework;
2. one active language project;
3. reusable project templates;
4. validation scenarios and gold expectations;
5. generated run evidence;
6. normative documentation and anti-drift locks.

The expected lifecycle is:

```text
clone GF Wordbench
→ reset the previous active project
→ initialize the new language project
→ develop and validate incrementally
→ pass checkpoints
→ build final PGF artifacts
→ satisfy release gates
```

GF Wordbench does not orchestrate several active language projects inside one workspace. Multi-workspace portfolio aggregation belongs to the independent `gf-portfolio` product, which is not a runtime dependency of GF Wordbench.

---

## 3. What GF Wordbench is not

GF Wordbench is not:

- a replacement for the GF compiler;
- a replacement for the GF shell;
- a new parser for the complete GF language;
- a generic plugin marketplace;
- a multi-language dashboard;
- a repository of all language implementations;
- a system that silently repairs GF source files;
- a system that declares a language correct only because it compiles;
- a report generator that reruns validation to reconstruct missing evidence.

The framework may inspect GF source heuristically, but GF execution remains the final authority for compilation, loading, parsing, linearization, generation, and PGF construction.

---

## 4. Core operating model

GF Wordbench separates four responsibilities.

### 4.1 Framework responsibility

The Python framework owns:

- configuration loading;
- file selection;
- static GF scanning;
- external process execution;
- timeout handling;
- evidence capture;
- diagnostic normalization;
- direct/downstream classification;
- scenario execution;
- gold comparison;
- regression comparison;
- run manifests;
- human-readable reports;
- machine-readable reports;
- AI-ready handoff reports.

### 4.2 GF responsibility

GF owns:

- parsing GF source;
- type checking;
- compilation;
- import resolution;
- `.gfo` generation;
- `.pgf` generation;
- grammar loading;
- parsing input text;
- linearizing trees;
- generation;
- GF shell semantics;
- GF error wording and runtime behavior.

### 4.3 Active project responsibility

The active language project owns:

- language-specific source locations;
- entrypoint modules;
- checkpoint modules;
- GF path additions;
- required validation scenarios;
- optional validation scenarios;
- gold expectations;
- language architecture;
- morphology and syntax rules;
- category and lincat contracts;
- module dependency map;
- project decision log;
- release criteria.

### 4.4 Maintainer responsibility

Maintainers own:

- normative decisions;
- reviewed gold updates;
- schema migrations;
- contract-lock updates;
- release approvals;
- language-specific exceptions;
- acceptance or rejection of known issues.

---

## 5. Repository zones

GF Wordbench separates permanent framework content from replaceable project content.

```text
GF_Wordbench/
├── app/                    framework implementation
├── tests/                  framework and contract tests
├── docs/                   permanent framework documentation
├── project/                one active language project
├── templates/project/      clean reusable project template
├── scripts/                maintenance and project lifecycle tools
├── run_<id>/               generated validation evidence
├── README.md               repository entry point
└── pyproject.toml          Python package and tool configuration
```

### 5.1 Permanent framework zone

Normally preserved when changing language:

```text
app/
tests/
docs/
templates/
scripts/
README.md
pyproject.toml
```

### 5.2 Replaceable active-project zone

Replaced or reinitialized for a new language:

```text
project/
```

### 5.3 Generated zone

Disposable and reproducible:

```text
run_<id>/
.gf_wordbench_state.json
```

Generated evidence may be archived, but it is not source configuration.

---

## 6. Documentation authority order

When two documents appear to overlap, use this authority order:

1. accepted ADRs;
2. `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` for cross-document interpretation;
3. specialized normative locks;
4. the document that owns the specific fact or contract;
5. overview, tutorial, quick-start, example and historical documents.

A lower-authority document must not contradict a higher-authority document.

If a contradiction is found:

1. stop the affected change;
2. identify the conflicting authorities and normative owner;
3. record the conflict in `docs/DOCUMENTATION_CORRECTION_LEDGER.md`;
4. update the correct source document and every affected dependent document together;
5. update tests or migrations when required;
6. record the decision when it changes architecture.

---

## 7. Anti-drift documents

Seven coordinated documents prevent silent contract and documentation drift.

### 7.1 Documentation alignment lock

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
```

Use it to preserve product identity, authority order, ownership boundaries and cross-document correction rules.

### 7.2 Documentation correction ledger

```text
docs/DOCUMENTATION_CORRECTION_LEDGER.md
```

Use it to coordinate documentation corrections performed across branches and to record conflicts that require joint resolution.

### 7.3 Framework interfile lock

```text
docs/INTERFILE_CONTRACT_LOCK.md
```

Use it when changing:

- Python function signatures;
- public models;
- stage inputs and outputs;
- ownership of generated artifacts;
- CLI or GUI calls into the framework;
- calls between audit stages;
- report dependencies;
- configuration construction.

It answers:

```text
which file calls
→ which provider
→ with which request
→ expecting which response
```

### 7.4 External tool lock

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Use it when changing:

- `gf` or `gf.exe` invocation;
- command-line arguments;
- standard input;
- working directory;
- environment variables;
- timeout behavior;
- stdout/stderr interpretation;
- expected `.gfo` or `.pgf` artifacts;
- supported GF versions;
- platform-specific process handling.

### 7.5 Persisted schema lock

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Use it when changing:

- `project/project.toml`;
- `.gf_wordbench_state.json`;
- `summary.json`;
- `manifest.json`;
- scenario `.out` files;
- `.gold` files;
- status values;
- diagnostic enum values;
- artifact names;
- run-directory layout;
- schema versions;
- compatibility or migration behavior.

### 7.6 Active project interfile lock

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Use it when changing:

- GF module imports;
- public GF symbols;
- lincat structures crossing module boundaries;
- module responsibilities;
- entrypoints;
- checkpoints;
- scenario-to-entrypoint relationships;
- scenario input files;
- scenario-to-gold relationships;
- expected `.gfo` or `.pgf` outputs.

### 7.7 Template project lock

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

This is the reusable blank normative template for new language projects.

It may contain placeholders.

The active project lock must not contain unresolved placeholders when the project is considered initialized.

---

## 8. Required reading by task

### 8.1 First-time user

Read:

```text
README.md
docs/00_START_HERE.md
docs/PRODUCT_OVERVIEW.md
docs/usage/INSTALLATION.md
docs/usage/QUICK_START.md
docs/validation/VALIDATION_MODES.md
```

### 8.2 Framework developer

Read:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/development/CODEBASE_GUIDE.md
docs/development/TESTING_GF_WORDBENCH.md
```

### 8.3 External-tool integration developer

Read:

```text
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
```

### 8.4 Language-project developer

Read:

```text
project/README.md
project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

### 8.5 Scenario author

Read:

```text
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
project/validation/README.md
```

### 8.6 Report or schema developer

Read:

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
```

### 8.7 Release maintainer

Read:

```text
docs/validation/RELEASE_GATES.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/release/MIGRATION_AND_DEPRECATION.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
```

---

## 9. Validation modes

GF Wordbench defines four canonical validation modes.

### 9.1 `quick`

Purpose:

- support the normal edit-test cycle;
- validate one changed file or a small target set;
- provide fast feedback.

Expected work:

- validate configuration;
- select the target;
- perform static scan;
- compile the target;
- optionally run a short smoke scenario;
- write a compact run summary.

A `quick` run is not release evidence.

### 9.2 `checkpoint`

Purpose:

- validate one development layer or subsystem;
- prove that a family of modules remains coherent.

Expected work:

- validate checkpoint modules;
- run required subsystem scenarios;
- compare reviewed gold outputs;
- detect regressions against the previous checkpoint;
- write full evidence for the checkpoint.

### 9.3 `release`

Purpose:

- prove that the active language project satisfies its declared completion criteria.

Expected work:

- validate every required checkpoint;
- compile final entrypoints;
- build required PGF artifacts;
- run every required scenario;
- verify required gold files;
- check missing or incomplete GF functions where configured;
- run bounded robustness tests;
- validate artifact manifest;
- compare against the previous release;
- enforce project release criteria.

A release run must not pass when a required stage is skipped.

### 9.4 `diagnostic`

Purpose:

- investigate difficult failures;
- preserve maximum evidence;
- distinguish local faults from downstream cascades.

Expected work:

- broad file selection;
- static scans;
- per-file compilation;
- full raw stdout/stderr;
- detailed classification;
- introspection scenarios when configured;
- complete reports.

Legacy aliases may be accepted only through documented migration:

```text
file → quick
all  → diagnostic
```

Canonical writers and documentation must use the canonical names.

---

## 10. Validation pipeline

The canonical pipeline is:

```text
load framework defaults
→ load active project configuration
→ apply explicit CLI or GUI overrides
→ validate configuration
→ create run paths
→ probe GF environment
→ select files and modules
→ fingerprint sources
→ run static scans
→ compile selected modules
→ normalize diagnostics
→ classify failures
→ run GF scenarios
→ normalize scenario output
→ compare gold expectations
→ build required PGF artifacts
→ compare with previous run
→ build RunResult
→ write reports
→ write manifest
→ validate final run invariants
```

A mode may omit optional stages, but stage ownership and result semantics remain stable.

---

## 11. Result semantics

GF Wordbench keeps separate concepts separate.

### 11.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

Meaning:

- `OK`: executed and satisfied its criterion;
- `FAIL`: executed correctly but did not satisfy its criterion;
- `ERROR`: GF Wordbench could not execute or interpret the validation correctly;
- `SKIPPED`: intentionally not executed.

### 11.2 Execution state

```text
completed
timed_out
cancelled
launch_failed
```

Execution state does not replace validation status.

### 11.3 Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Diagnostic class describes the causal relationship of the failure.

### 11.4 Error kind

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

Error kind describes the nature of the problem.

These vocabularies must not be merged.

---

## 12. Source of truth

Use the following sources of truth.

| Question | Source of truth |
|---|---|
| What should the framework do? | framework architecture and lock files |
| What language is active? | `project/project.toml` |
| What must the language implement? | project specification documents |
| Which GF command was executed? | raw run evidence |
| Did GF compile or load successfully? | GF process result |
| What is the canonical machine run record? | `summary.json` |
| Which artifacts belong to the run? | `manifest.json` |
| What result is expected for a scenario? | reviewed `.gold` file |
| What changed since the previous run? | structured diff entries |
| Is the project releasable? | release run plus project release criteria |
| What limitations or blocking issues remain? | `project/docs/KNOWN_ISSUES.md` |

Human-readable reports are views of structured results. They are not substitutes for canonical machine data.

---

## 13. Active project configuration

The active project is defined by:

```text
project/project.toml
```

It should describe:

- project identity;
- language identity;
- source directory;
- source glob;
- inclusion and exclusion rules;
- GF path additions;
- entrypoint modules;
- checkpoint modules;
- required scenarios;
- optional scenarios;
- release artifact requirements.

Environment-specific values such as local `gf.exe`, RGL root, or output root should remain outside the portable project contract unless the schema explicitly allows them.

---

## 14. Scenario model

GF Wordbench uses native GF scripts.

Canonical scenario files:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Expected outputs:

```text
project/validation/gold/<scenario-id>.gold
```

Runtime normalized output:

```text
run_<id>/raw/scenarios/<scenario-id>.out
```

A scenario should:

- have a stable identifier;
- load the intended grammar;
- emit stable begin and end markers;
- exercise one coherent validation concern;
- terminate cleanly;
- produce bounded output;
- avoid depending on local absolute paths;
- use reviewed inputs;
- preserve raw output before normalization.

A normal validation run must never rewrite a gold file.

Gold updates require an explicit, reviewed operation.

---

## 15. Static scans

Static scans detect suspicious source patterns before or alongside compilation.

They may detect:

- malformed slash patterns;
- risky runtime matching on strings;
- untyped case or table patterns;
- trailing whitespace;
- future project-specific anti-patterns.

Static findings are heuristic.

They must not be represented as GF compiler truth.

A source file may compile while still carrying a static warning.

A source file may fail compilation without any static finding.

---

## 16. Failure classification

GF Wordbench distinguishes:

### Direct failure

Evidence indicates the selected file or scenario is the likely local source of failure.

### Downstream failure

Evidence indicates the file or scenario is blocked by a failure in another provider.

### Ambiguous failure

Evidence is insufficient to determine whether the problem is local or downstream.

### Noise

The item was excluded or identified as non-actionable under documented rules.

### Skipped

The validation was intentionally not executed.

Reports must not flatten these distinctions into one undifferentiated failure list.

---

## 17. Generated run evidence

Canonical run structure:

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

Primary roles:

- `summary.json`: machine-readable source of truth;
- `summary.md`: human overview;
- `AI_READY.md`: bounded diagnostic handoff;
- `manifest.json`: artifact identity and integrity;
- `raw/`: original evidence;
- `details/`: focused per-result views;
- `artifacts/`: GF-produced or validation-produced build outputs.

---

## 18. Documentation map

### General

```text
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/GLOSSARY.md
docs/REPOSITORY_STRUCTURE.md
docs/DOCUMENTATION_MAP.md
```

### Architecture

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/architecture/DEPENDENCY_RULES.md
```

### GF integration

```text
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/gf/GF_OUTPUT_NORMALIZATION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
```

### Validation

```text
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/validation/FILE_SELECTION.md
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/REGRESSION_COMPARISON.md
docs/validation/RELEASE_GATES.md
```

### Scenarios and gold

```text
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
```

### Diagnostics

```text
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
```

### Reports

```text
docs/reports/REPORTING_OVERVIEW.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/reports/RAW_LOGS_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
```

### Configuration and usage

```text
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/INSTALLATION.md
docs/usage/QUICK_START.md
docs/usage/CLI_REFERENCE.md
docs/usage/GUI_REFERENCE.md
```

### Project lifecycle

```text
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/CLONING_AND_RESETTING.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
```

### Development, operations, and release

```text
docs/development/
docs/operations/
docs/release/
docs/decisions/
docs/reference/
```

---

## 19. Change discipline

Before changing a file, answer:

1. Is this an internal change or a boundary change?
2. Does another file import, call, parse, load, or compare it?
3. Does it alter a persisted field or path?
4. Does it alter an external GF invocation?
5. Does it alter project module behavior?
6. Does it alter a gold expectation?
7. Does it alter release criteria?
8. Which lock owns the change?
9. Which tests prove compatibility?
10. Is a migration required?

A change that crosses a boundary must be coordinated.

An isolated edit is not complete when another file depends on the changed promise.

---

## 20. Framework change checklist

```text
[ ] Read the relevant lock and documentation alignment rules
[ ] Identify provider and all consumers
[ ] Update public models or schemas
[ ] Update unit tests
[ ] Update integration tests
[ ] Update persisted fixtures when needed
[ ] Update migration logic when needed
[ ] Update documentation owner
[ ] Run the complete framework test suite
[ ] Run schema and contract checks
[ ] Record architectural decisions when applicable
```

---

## 21. Active project change checklist

```text
[ ] Identify the GF provider module
[ ] Identify direct consumers
[ ] Identify downstream entrypoints
[ ] Review lincat and category contracts
[ ] Review project dependency map
[ ] Update scenarios
[ ] Update input fixtures
[ ] Update gold only through explicit review
[ ] Update project contract lock
[ ] Run quick validation
[ ] Run checkpoint validation
[ ] Run release validation when closing a subsystem
```

---

## 22. Release readiness

GF Wordbench framework release requires:

- all framework tests pass;
- all contract tests pass;
- all schema tests pass;
- documentation links resolve;
- no canonical schema remains unversioned;
- no language-specific path remains in framework defaults;
- templates contain no active-language data;
- migration behavior is documented;
- release notes are complete.

Active language release requires:

- all required checkpoints pass;
- all required scenarios pass;
- all required gold comparisons pass;
- required PGF artifacts are built;
- manifest validation passes;
- required entrypoints compile;
- no unaccepted blocking issue remains;
- project release criteria are satisfied;

---

## 23. When information conflicts

When code, documentation, and generated evidence disagree:

### Code versus lock

The lock defines the intended contract.

Either:

- restore the code to the lock; or
- deliberately revise the lock and every affected consumer.

### Documentation versus persisted schema lock

The persisted schema lock governs canonical persisted structure.

### Human report versus raw evidence

Raw evidence and structured results govern.

### Active project document versus template

The active project document governs the active language.

The template governs initialization of future projects only.

### Current run versus previous run

The current run describes current behavior.

The previous run is comparison evidence, not current truth.

---

## 24. Safe defaults

When GF Wordbench cannot safely infer intent:

- do not modify source files;
- do not update gold files;
- do not overwrite project configuration;
- do not delete prior runs;
- do not migrate in place without a backup;
- do not treat missing evidence as success;
- do not treat a zero external exit code as sufficient proof when expected markers or artifacts are missing;
- return a structured `ERROR` or configuration failure.

---

## 25. Navigation rule

Use the smallest authoritative document that owns the question.

Examples:

```text
How is a Python boundary changed?
→ docs/INTERFILE_CONTRACT_LOCK.md
```

```text
How is gf.exe invoked?
→ docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

```text
Can summary.json change?
→ docs/PERSISTED_SCHEMA_LOCK.md
```

```text
Which GF module provides a public helper?
→ project/docs/INTERFILE_CONTRACT_LOCK.md
```

```text
What proves this language is complete?
→ project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
→ project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

```text
What happened in this run?
→ run_<id>/summary.json
→ run_<id>/manifest.json
→ raw evidence
```

---

## 26. Governing rule

GF Wordbench is correct only when its components agree across boundaries.

A file may be internally correct and still break the system when it changes what another file expects.

Therefore:

> Every public promise, persisted format, external command, project dependency, scenario expectation, and release criterion must have one documented owner and one coordinated change path.
