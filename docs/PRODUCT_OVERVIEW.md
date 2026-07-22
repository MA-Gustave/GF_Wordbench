# GF Wordbench — Product Overview

**Document ID:** `GF-WB-PRODUCT-OVERVIEW`  
**Status:** Final product definition  
**Applies to:** GF Wordbench framework and its active GF language project  
**Owner:** GF Wordbench maintainers  
**Product name:** GF Wordbench  
**Package name:** `gf-wordbench`  
**Primary command:** `gf-wordbench`  
**Document version:** `1.0.0`

---

## 1. Product definition

GF Wordbench is a development, validation, and release workbench for one active Grammatical Framework language project.

It coordinates the tools and evidence required to build a GF language implementation with repeatable quality controls. It does not replace GF. It uses GF as the authoritative execution engine and adds the project-level workflow that GF alone does not provide:

- deterministic project configuration;
- source selection;
- static source checks;
- module compilation;
- grammar loading;
- PGF construction;
- scripted `.gfs` validation;
- parse, linearization, generation, morphology, and introspection scenarios;
- golden-output regression testing;
- direct, downstream, and ambiguous failure classification;
- run-to-run comparison;
- evidence preservation;
- human-readable, machine-readable, and AI-ready reporting;
- contract and schema controls that prevent drift across files and releases.

Each GF Wordbench copy manages one active language project. To start another language, the framework is cloned or reset and the active project is replaced.

---

## 2. Product purpose

Developing a GF language is not a single compilation task.

A language can contain many modules, interfaces, instances, resources, paradigms, helpers, constructors, entrypoints, scenarios, and generated artifacts. A locally correct edit can still break another module, invalidate a scenario, change expected linguistic output, or create a downstream failure that hides the root cause.

GF Wordbench exists to make those relationships observable and testable.

The product provides a controlled path from an individual source edit to a release decision:

```text
source change
→ static checks
→ GF compilation
→ failure classification
→ project checkpoints
→ GF scenarios
→ golden comparison
→ final grammar build
→ evidence and reports
→ release decision
```

The product is successful when a developer can answer, from one run:

1. What was tested?
2. Which GF commands were executed?
3. What passed?
4. What failed?
5. Which failure is likely direct?
6. Which failures are probably downstream?
7. What changed since the previous run?
8. Which release criteria remain unsatisfied?
9. Where is the raw evidence?
10. Can another developer or AI system inspect the result without rerunning GF?

---

## 3. Product goals

GF Wordbench MUST provide the following product-level outcomes.

### 3.1 Repeatable validation

Equivalent source, configuration, toolchain, and scenario inputs SHOULD produce equivalent normalized results.

Every run MUST record enough context to explain what was executed.

### 3.2 Fast development feedback

A developer MUST be able to validate one changed file or a focused checkpoint without executing the full release suite.

### 3.3 Authoritative release validation

A final release mode MUST verify more than individual source compilation. It MUST include the configured final entrypoints, required scenarios, required golden comparisons, and required generated artifacts.

### 3.4 Root-cause-oriented diagnostics

GF Wordbench MUST distinguish likely direct failures from downstream cascades and ambiguous failures.

The product MUST preserve raw GF evidence so classifications can be reviewed.

### 3.5 Drift prevention

Contracts between Python files, external tools, persisted schemas, GF project files, scenarios, gold files, and generated artifacts MUST be explicit and testable.

### 3.6 Reusable language-project workflow

The framework MUST be reusable for a different language by replacing the active project rather than redesigning the validation engine.

### 3.7 Human, automation, and AI usability

The same run MUST produce:

- a machine-readable result;
- a concise human-readable result;
- an AI-ready diagnostic packet;
- detailed raw evidence.

### 3.8 Evidence preservation

A partial failure MUST NOT erase already captured logs, diagnostics, fingerprints, or artifacts.

---

## 4. Target users

### 4.1 GF language implementers

Primary users who create or repair:

- morphology;
- syntax;
- lexicons;
- structural modules;
- paradigms;
- extensions;
- concrete grammars;
- language APIs.

### 4.2 GF project maintainers

Users responsible for:

- architecture;
- module contracts;
- entrypoints;
- validation policy;
- regression expectations;
- releases;
- migrations.

### 4.3 Framework maintainers

Users who evolve GF Wordbench itself:

- process execution;
- diagnostics;
- result models;
- schemas;
- reports;
- CLI and GUI;
- compatibility with GF versions.

### 4.4 Automated systems

Supported consumers include:

- continuous integration;
- release scripts;
- schema validators;
- report processors;
- archival and comparison tools.

### 4.5 AI-assisted development workflows

AI systems may consume `AI_READY.md`, structured summaries, and selected evidence. They are consumers of recorded results, not authorities over GF semantics.

---

## 5. Product operating model

GF Wordbench separates three layers.

### 5.1 Framework layer

The framework contains reusable Python code and permanent documentation.

It owns:

- orchestration;
- process execution;
- source scanning;
- result models;
- diagnostics;
- classification;
- run comparison;
- reporting;
- schema validation;
- contract validation;
- CLI and GUI behavior.

Framework code MUST remain language-neutral.

### 5.2 Active project layer

The active project contains one GF language implementation and its validation contract.

It owns:

- project identity;
- source root;
- GF path components;
- module entrypoints;
- checkpoints;
- required and optional scenarios;
- scenario inputs;
- gold files;
- language architecture;
- morphology and syntax specifications;
- status and decision records;
- release criteria.

### 5.3 External tool layer

GF and the operating system execute authoritative tool operations.

GF owns:

- GF syntax and type checking;
- module resolution;
- source compilation;
- grammar loading;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF diagnostics.

GF Wordbench owns how those operations are requested, captured, normalized, classified, compared, and reported.

---

## 6. Single active language principle

One GF Wordbench copy represents one active language project.

This is a deliberate product constraint.

The framework does not manage several language projects simultaneously through a profile selector. Instead, it provides a clean project boundary that can be:

- initialized;
- migrated;
- cloned;
- reset;
- replaced;
- archived.

Benefits:

- simpler configuration;
- clearer project identity;
- no cross-language state leakage;
- no mixed run history;
- smaller failure surface;
- easier AI handoff;
- stronger anti-drift rules;
- reproducible project archives.

The active language identity MUST come from:

```text
project/project.toml
```

It MUST NOT be inferred from GUI state, old output directories, filenames, or historical reports.

---

## 7. Core capabilities

### 7.1 Environment validation

GF Wordbench validates:

- project root;
- project configuration;
- GF executable;
- GF version;
- RGL root or configured GF libraries;
- output root;
- required source and scenario files;
- required write permissions.

### 7.2 Source selection

The framework selects GF source files using:

- source directory;
- source glob;
- include rules;
- exclude rules;
- focused target selection;
- checkpoint selection;
- release entrypoints.

Selection order MUST be deterministic.

### 7.3 Static scanning

Static scanning detects documented suspicious GF source patterns without claiming to replace GF compilation.

Scan findings remain separate from compile results.

### 7.4 Module compilation

GF Wordbench runs GF compilation with:

- explicit executable;
- explicit working directory;
- explicit GF path;
- bounded timeout;
- stdout capture;
- stderr capture;
- artifact collection;
- normalized diagnostic extraction.

### 7.5 Failure classification

File failures are classified as:

```text
direct
downstream
ambiguous
```

Non-failure and non-actionable classes include:

```text
ok
noise
skipped
```

The classification describes causal relationship. It does not replace error kind, process state, or validation status.

### 7.6 Source fingerprinting

Each relevant source file may be fingerprinted so a run can be associated with the exact source content that produced it.

### 7.7 Scenario execution

Native `.gfs` scripts exercise the loaded grammar through GF.

Scenarios may cover:

- grammar loading;
- missing linearizations;
- parsing;
- linearization;
- round trips;
- bounded generation;
- morphology;
- grammar introspection;
- project-specific regression cases.

### 7.8 Golden-output testing

Normalized scenario output may be compared with reviewed `.gold` files.

Normal validation MUST NOT rewrite gold files.

Gold updates require a deliberate, explicit workflow.

### 7.9 PGF build validation

Release validation may require construction and verification of configured `.pgf` artifacts.

A missing required PGF is a failure.

### 7.10 Run comparison

A run may be compared with a compatible previous run.

The comparison identifies:

```text
unchanged
improved
regressed
new
removed
```

### 7.11 Reporting

Each finalized run produces the configured combination of:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- `top_errors.txt`;
- `manifest.json`;
- raw logs;
- detailed evidence;
- GF artifacts.

### 7.12 Contract validation

GF Wordbench may validate:

- Python interfile contracts;
- external-tool contracts;
- persisted-schema contracts;
- active-project interfile contracts.

### 7.13 Schema validation and migration

Persisted formats use explicit schema identities and versions.

Supported legacy GF Audit formats may be migrated into canonical GF Wordbench formats.

---

## 8. Validation model

GF Wordbench uses four complementary validation layers.

### 8.1 Static layer

Answers:

- Does the source contain a known suspicious pattern?
- Is the file eligible for validation?
- Does source metadata satisfy project rules?

Static results are advisory unless project policy promotes a rule to a gate.

### 8.2 Compilation layer

Answers:

- Does GF accept the source module?
- What authoritative GF diagnostic was produced?
- Was the tool launched correctly?
- Did execution time out?
- Were expected `.gfo` artifacts created?

### 8.3 Grammar execution layer

Answers:

- Can the configured grammar be loaded?
- Can required trees be linearized?
- Can required phrases be parsed?
- Do required generation and morphology checks complete?
- Are missing functions acceptable under project policy?

### 8.4 Regression and release layer

Answers:

- Does normalized output match reviewed expectations?
- Has behavior improved or regressed?
- Are all checkpoints satisfied?
- Were final artifacts produced?
- Does the project meet its release criteria?

No single layer is sufficient to declare a language complete.

---

## 9. Validation modes

GF Wordbench defines four product modes.

### 9.1 `quick`

Purpose: rapid feedback during an edit loop.

Typical scope:

- one target file;
- static scan;
- file compilation;
- optional minimal smoke scenario.

Expected characteristic: fastest meaningful validation.

### 9.2 `checkpoint`

Purpose: validate a completed module family or development milestone.

Typical scope:

- configured checkpoint modules;
- relevant scenarios;
- required gold comparisons;
- regression comparison.

### 9.3 `diagnostic`

Purpose: investigate complex failures and cascades.

Typical scope:

- broad source inventory;
- verbose evidence;
- individual compilation;
- detailed classification;
- extended diagnostics;
- full logs.

### 9.4 `release`

Purpose: determine whether the active language project is releasable.

Typical scope:

- required checkpoints;
- configured final entrypoints;
- PGF construction;
- all required scenarios;
- all required gold comparisons;
- release-specific artifact checks;
- schema and contract checks;
- final manifest;
- release criteria evaluation.

Legacy mode aliases may be supported during migration:

```text
file → quick
all  → diagnostic
```

Canonical output uses only the final mode names.

---

## 10. Status model

GF Wordbench keeps four concepts separate.

### 10.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

- `OK`: validation ran and passed.
- `FAIL`: validation ran but did not satisfy its criterion.
- `ERROR`: GF Wordbench could not execute or interpret the validation correctly.
- `SKIPPED`: validation was intentionally not executed.

### 10.2 Execution state

Examples:

```text
completed
timed_out
cancelled
launch_failed
```

Execution state describes process execution, not validation meaning.

### 10.3 Error kind

Examples:

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

Error kind describes the nature of a failure.

### 10.4 Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Diagnostic class describes causal position in the audit.

These concepts MUST NOT be collapsed into one status field.

---

## 11. Product outputs

### 11.1 Machine-readable summary

`summary.json` is the primary structured run record.

It supports:

- automation;
- previous-run comparison;
- GUI loading;
- migrations;
- schema validation;
- external analysis.

### 11.2 Human-readable summary

`summary.md` provides a concise overview of:

- configuration;
- outcome;
- failed files;
- failed scenarios;
- regression changes;
- artifact locations.

### 11.3 AI-ready handoff

`AI_READY.md` provides a bounded, evidence-based diagnostic packet without rerunning GF.

It includes:

- run context;
- primary failures;
- direct/downstream distinctions;
- selected raw excerpts;
- scenario failures;
- artifact paths.

### 11.4 Raw evidence

Raw evidence includes:

- exact command;
- working directory;
- stdout;
- stderr;
- exit code;
- timeout state;
- duration;
- produced artifacts.

Normalization never replaces raw evidence.

### 11.5 Artifact manifest

`manifest.json` inventories final run artifacts and may record:

- path;
- role;
- media type;
- size;
- hash;
- owner.

---

## 12. Anti-drift system

GF Wordbench uses four complementary locks.

### 12.1 Framework interfile lock

```text
docs/INTERFILE_CONTRACT_LOCK.md
```

Locks Python-to-Python requests, responses, ownership, and dependency directions.

### 12.2 External tool lock

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Locks commands, process behavior, GF integration, artifact expectations, and tool compatibility.

### 12.3 Persisted schema lock

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Locks machine-readable formats, stable artifact names, schema versions, compatibility, and migrations.

### 12.4 Active project interfile lock

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Locks relationships among GF modules, entrypoints, scenarios, inputs, gold files, artifacts, and project documentation.

The locks define boundaries. They do not freeze internal implementation that preserves the boundary.

---

## 13. User interfaces

### 13.1 CLI

The CLI is the complete automation-capable interface.

It MUST support every required validation capability without the GUI.

Primary command:

```text
gf-wordbench
```

### 13.2 GUI

The GUI provides convenient configuration, execution, progress display, and report access.

It MUST use the same configuration and audit entrypoints as the CLI.

The GUI MUST NOT implement separate validation semantics.

### 13.3 Windows launchers

Batch launchers may simplify startup.

They are convenience entrypoints and MUST NOT be the only supported execution path.

### 13.4 Filesystem interface

Run directories and project assets are a supported product interface.

Their stable formats are governed by the persisted-schema lock.

---

## 14. Project lifecycle

A language project moves through these states.

### 14.1 Initialize

Create:

- `project.toml`;
- project documentation;
- validation directories;
- initial entrypoints;
- initial checkpoints;
- initial scenarios.

### 14.2 Baseline

Record the first trustworthy diagnostic run.

A baseline may contain failures, but its environment and evidence must be valid.

### 14.3 Develop

Use quick and diagnostic runs while implementing or repairing the language.

### 14.4 Checkpoint

Validate completed module families against focused criteria.

### 14.5 Stabilize

Resolve or explicitly document:

- temporary implementations;
- fallbacks;
- warnings;
- blocked symbols;
- stale comments;
- incomplete scenarios.

### 14.6 Release

Run the full release gate and preserve its manifest and reports.

### 14.7 Archive or replace

Archive the completed active project or reset the framework for another language.

Old-language identity and state MUST NOT leak into the replacement project.

---

## 15. Release definition

A project is not complete merely because all selected `.gf` files compile.

A final release requires every criterion declared by the active project, normally including:

- valid project configuration;
- supported GF toolchain;
- required modules present;
- required checkpoints passing;
- final entrypoints compiling;
- required grammar load scenarios passing;
- required parse and linearization scenarios passing;
- required gold comparisons passing;
- required PGF artifacts present;
- no unresolved release-blocking status entries;
- contract checks passing;
- schema checks passing;
- complete run evidence;
- final manifest generated.

Project-specific criteria belong in:

```text
project/docs/RELEASE_CRITERIA.md
project/docs/VALIDATION_SPEC.md
```

---

## 16. Quality attributes

### 16.1 Correctness

GF remains authoritative for GF semantics.

GF Wordbench must not substitute heuristics for GF execution truth.

### 16.2 Determinism

Selection, ordering, serialization, normalization, and comparison should be deterministic.

### 16.3 Traceability

Every interpreted result should reference the raw evidence from which it was derived.

### 16.4 Recoverability

Partial failures should leave a usable run directory.

### 16.5 Portability

The core framework should remain platform-neutral where practical.

Windows-specific behavior must remain isolated.

### 16.6 Maintainability

Major file boundaries use typed models, clear ownership, and documented contracts.

### 16.7 Extensibility

New validation stages may be added without bypassing the central orchestration, result, evidence, and reporting contracts.

### 16.8 Security

Project paths and scenarios are executable or semi-executable inputs and must be treated accordingly.

Reports must not expose secrets or complete environment dumps.

### 16.9 Performance

Quick validation must remain focused.

Expensive generation, exhaustive scenarios, and full diagnostics must be bounded and mode-appropriate.

---

## 17. Product boundaries

GF Wordbench is:

- a GF language development workbench;
- a validation orchestrator;
- an evidence recorder;
- a regression-testing system;
- a release-gating system;
- an anti-drift framework;
- a reusable single-project template.

GF Wordbench is not:

- a replacement for GF;
- a new GF parser or type checker;
- a universal programming-language validator;
- a simultaneous multi-language dashboard;
- a language-theory decision engine;
- an automatic proof that linguistic behavior is correct;
- an automatic gold-file approval system;
- an AI system that edits source without review;
- a package manager for GF;
- a general CI platform.

The detailed boundary is defined in:

```text
docs/SCOPE_AND_NON_GOALS.md
```

---

## 18. Relationship to the earlier GF Audit tool

GF Wordbench evolves from a working GF Audit foundation.

The existing foundation already demonstrates:

- project and target-file audit;
- GF-aware static scanning;
- per-file compilation with timeout;
- compile-error normalization;
- direct/downstream/ambiguous classification;
- source fingerprinting;
- previous-run comparison;
- structured reports;
- CLI and GUI workflows;
- AI-ready handoff.

GF Wordbench retains those proven capabilities and adds the missing final-product layers:

- language-neutral project configuration;
- one replaceable active project;
- native `.gfs` scenarios;
- golden-output testing;
- grammar execution validation;
- PGF release validation;
- explicit scenario results;
- artifact manifests;
- versioned persisted schemas;
- contract checking;
- final release gates.

Migration must preserve working behavior before replacing it.

---

## 19. Documentation authority

This overview defines the product at a high level.

Detailed authority is distributed as follows:

| Topic | Authoritative document |
|---|---|
| Product scope | `docs/SCOPE_AND_NON_GOALS.md` |
| Architecture | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Python boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| GF and external tools | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Validation flow | `docs/validation/VALIDATION_PIPELINE.md` |
| Validation modes | `docs/validation/VALIDATION_MODES.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Status semantics | `docs/reference/STATUS_VALUES.md` |
| Active project identity | `project/project.toml` |
| GF module relationships | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Project validation | `project/docs/VALIDATION_SPEC.md` |
| Project release | `project/docs/RELEASE_CRITERIA.md` |

When this overview conflicts with a normative lock or versioned schema, the normative lock or schema governs its specific domain.

---

## 20. Product success criteria

GF Wordbench reaches its intended final state when:

1. the active project can be replaced without modifying language-neutral framework logic;
2. quick, checkpoint, diagnostic, and release modes are implemented;
3. GF commands are executed only through documented process contracts;
4. file and scenario results are both represented explicitly;
5. required `.gfs` scenarios and `.gold` comparisons are supported;
6. PGF release validation is supported;
7. all persisted machine formats are versioned;
8. legacy GF Audit state and summaries have tested migration paths;
9. contract and schema validation can be executed automatically;
10. CLI and GUI use the same orchestration path;
11. every run preserves raw evidence and structured results;
12. final release criteria can be evaluated without manual reconstruction of the run;
13. project documentation and source contracts can be checked for drift;
14. the framework test suite, integration suite, schema suite, and contract suite pass;
15. the framework contains no accidental dependency on a specific active language.

---

## 21. Product statement

> GF Wordbench is a single-language GF development and release workbench that combines authoritative GF execution with repeatable validation, regression scenarios, evidence-preserving diagnostics, anti-drift contracts, and structured reporting.

Its purpose is not to make GF development abstract or bureaucratic.

Its purpose is to make a complex language project understandable, testable, recoverable, and releasable.
