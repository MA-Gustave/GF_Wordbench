# GF Wordbench — Validation Overview

**Document ID:** `GF-WB-VALIDATION-OVERVIEW`  
**Status:** Normative  
**Applies to:** GF Wordbench validation architecture and one selected GF language context  
**Owner:** GF Wordbench maintainers  
**Validation contract version:** `1.0.0`  
**Canonical path:** `docs/validation/VALIDATION_OVERVIEW.md`  
**Last structural review:** 2026-08-05

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---
## 1. Purpose

GF Wordbench validates the coherence, compilability, behavior, release readiness, and regression stability of exactly one selected Grammatical Framework language context per workspace and per run.

This document defines the validation system at overview level:

- what validation means;
- what is authoritative;
- which validation dimensions exist;
- how the pipeline is organized;
- how the four canonical modes differ;
- how statuses, failures, evidence, and release decisions relate;
- which outputs every run must preserve;
- which responsibilities belong to the framework and which belong to the selected language context.

This document is normative for GF Wordbench validation.

Detailed algorithms, command syntax, schemas, scenario formats, and release criteria belong to the specialized documents referenced later.

The central rule is:

> Validation is a structured evidence-producing process, not a single compile command and not a report-generation exercise.

---

## 2. Validation objective

A GF Wordbench run answers one or more of the following questions:

1. Is the selected language context configuration valid?
2. Are the intended GF source files present and correctly selected?
3. Do source-level checks detect known suspicious patterns?
4. Can the required modules compile with the configured GF toolchain?
5. Which failures are direct, downstream, ambiguous, environmental, or infrastructural?
6. Do the configured grammar entrypoints load and behave as expected?
7. Do required parsing, linearization, generation, morphology, or introspection scenarios pass?
8. Do normalized scenario outputs match reviewed expectations?
9. Are required `.gfo` and `.pgf` artifacts produced?
10. Has the project improved, regressed, or remained stable relative to a previous run?
11. Does the accumulated evidence satisfy the requested validation mode and release gates?

GF Wordbench does not claim that a language implementation is linguistically complete merely because it compiles.

Compilation, scenario behavior, gold comparison, coverage, known issues, and release policy are separate validation dimensions.

---

## 3. Scope

The validation system governs:

- project configuration validation;
- GF executable and version validation;
- GF path resolution;
- source discovery and filtering;
- source fingerprinting;
- static source scanning;
- module compilation;
- checkpoint compilation;
- entrypoint compilation;
- diagnostic parsing;
- causal failure classification;
- `.gfs` scenario execution;
- marker and assertion verification;
- normalized-output production;
- gold comparison;
- PGF construction and verification;
- previous-run comparison;
- run-level aggregation;
- release-gate evaluation;
- evidence capture;
- report and manifest production.

---

## 4. Non-scope

GF Wordbench validation does not:

- replace the GF parser, type checker, compiler, runtime, or module resolver;
- prove the linguistic correctness of every possible sentence;
- infer project intent from filenames when project configuration is explicit;
- silently fix GF source files;
- silently update gold files;
- silently change release requirements;
- execute arbitrary Python supplied by the selected language context;
- support multiple active language profiles or several selected language contexts in one workspace;
- perform cross-workspace or multilingual portfolio aggregation;
- treat human-readable reports as the primary machine data source;
- use a zero process exit code as the only success criterion;
- treat all failed modules as independent root failures;
- guarantee that optional or unbounded generation is deterministic;
- convert warnings into accepted behavior without project policy;
- replace expert linguistic review where automation cannot establish correctness.

---

## 5. Authority model

### 5.1 GF is authoritative for

Grammatical Framework is authoritative for:

- GF syntax;
- GF type checking;
- module loading;
- dependency resolution;
- `.gf` to `.gfo` compilation;
- `.pgf` construction;
- parsing;
- linearization;
- generation;
- morphology commands;
- grammar introspection;
- GF-native diagnostics;
- GF shell command semantics.

### 5.2 GF Wordbench is authoritative for

GF Wordbench is authoritative for:

- project and environment configuration resolution;
- command construction;
- executable selection;
- working-directory selection;
- timeout and cancellation handling;
- process execution policy;
- stdout and stderr capture;
- source selection;
- static scan rules;
- artifact collection;
- diagnostic normalization;
- causal failure classification;
- scenario registration;
- scenario completion assertions;
- output normalization;
- gold comparison;
- run history;
- regression comparison;
- release-gate evaluation;
- reports;
- manifests;
- persistent schema compatibility.

### 5.3 Validation profile is authoritative for

The selected language context is authoritative for:

- resolved language identity;
- language-specific GF modules;
- source root;
- module suffix;
- entrypoints;
- checkpoints;
- required and optional scenarios;
- scenario inputs;
- reviewed gold expectations;
- language-specific validation policy;
- accepted known issues;
- release targets;
- project-level interfile contracts;
- linguistic design documentation.

### 5.4 Portfolio boundary

Multi-workspace discovery, multilingual aggregation, cross-project comparison, and portfolio readiness belong to the independent `gf-portfolio` product.

The dependency direction is one-way:

```text
gf-portfolio → public versioned GF Wordbench artifacts
GF Wordbench -X→ gf-portfolio runtime, storage, code, or configuration
```

GF Wordbench validation starts, executes, reports, and passes its tests without `gf-portfolio`.

### 5.5 No duplicated authority

No component may create a second source of truth for a responsibility owned elsewhere.

Examples:

- GUI state must not replace `<validation-profile-root>/project.toml`;
- reports must not recompute validation independently;
- the compiler must not classify downstream failures;
- scenario files must not choose a different project implicitly;
- project configuration must not replace the common process runner;
- static scanning must not claim to be GF compilation truth.

---

## 6. Core validation principles

### 6.1 Evidence before interpretation

Raw evidence must be captured before normalization, classification, summarization, or report rendering.

Raw evidence includes:

- executable;
- ordered arguments;
- working directory;
- relevant environment overrides;
- start and end timestamps;
- duration;
- exit code;
- timeout state;
- cancellation state;
- launch error;
- stdout;
- stderr;
- generated artifacts.

### 6.2 Structured results before reports

Every stage must return or contribute to a structured result.

Reports consume structured results.

Reports must not:

- rerun GF;
- rescan source files;
- reconstruct missing stage evidence;
- independently classify failures;
- invent artifact paths;
- become the only source for later comparisons.

### 6.3 Determinism

Given equivalent:

- source files;
- project configuration;
- environment configuration;
- GF version;
- scenario scripts;
- scenario inputs;
- normalization version;
- gold files;

GF Wordbench produces equivalent validation decisions and deterministically ordered results.

Where an operation is inherently variable, the scenario must:

- bound it;
- use non-exact assertions;
- exclude unstable output from exact gold comparison;
- or remain diagnostic rather than release-blocking.

### 6.4 Failure isolation

One source or scenario failure does not unnecessarily destroy evidence from independent validation work.

GF Wordbench continues sufficiently to:

- identify direct and downstream failures;
- collect remaining safe evidence;
- produce a valid run summary;
- expose incomplete stages;
- distinguish project failure from framework failure.

### 6.5 Explicit requiredness

Every validation stage, checkpoint, scenario, assertion, and expected artifact that affects the final decision must be explicitly classified as required or optional for the selected mode.

Required behavior must not be inferred from directory presence alone.

### 6.6 No silent mutation

Normal validation must not modify:

- GF source files;
- project configuration;
- scenario scripts;
- scenario inputs;
- gold files;
- previous-run evidence;
- captured raw output.

Explicit maintenance commands may update controlled assets under separate policy.

### 6.7 One selected language context

One GF Wordbench workspace validates exactly one selected language context.

The resolved language identity is resolved from the selected language context configuration, not from:

- previous output;
- UI history;
- source-name guessing;
- a list of runtime profiles;
- a `gf-portfolio` workspace registry.

### 6.8 Run budget and finalization reserve

Every run has one global budget, explicit stage budgets, and a protected finalization reserve.

Normal validation stages cannot consume the finalization reserve. When the usable execution budget is exhausted, insufficient, or cancelled:

- no new validation stage starts;
- active child processes receive controlled termination;
- partial evidence remains preserved;
- unstarted work receives an explicit reason;
- the run enters finalization using the protected reserve.

A run cannot be `OK` or release-ready when required work or required evidence is incomplete.

The governing decision is `docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md`.

---

## 7. Canonical validation modes

GF Wordbench defines four canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Historical values are accepted only as migration aliases:

```text
file → quick
all  → diagnostic
```

Canonical writers, reports, state, and summaries must emit only the canonical names.

---

## 8. Mode intent

### 8.1 Quick mode

**Purpose**

Provide rapid, focused feedback during active development.

**Typical scope**

- validate configuration needed for the target;
- select one target file or a tightly bounded target set;
- run applicable static scans;
- compile the selected target;
- preserve direct evidence;
- classify the immediate result;
- produce a complete but bounded run record.

**Expected use**

- editing one module;
- checking a suspected source-level issue;
- verifying a local repair;
- obtaining focused diagnostics.

**Not a release claim**

Quick success does not prove:

- checkpoint coherence;
- all entrypoints compile;
- required scenarios pass;
- PGF is buildable;
- release gates are satisfied.

### 8.2 Checkpoint mode

**Purpose**

Validate a defined development layer or milestone and its required dependencies.

**Typical scope**

- validate project configuration;
- select configured checkpoint modules;
- include required supporting modules according to dependency policy;
- run static scans;
- compile checkpoint targets;
- classify direct and downstream failures;
- run scenarios assigned to checkpoint mode;
- compare required checkpoint gold files;
- compare with a previous compatible run;
- produce checkpoint-level evidence.

**Expected use**

- morphology milestone;
- syntax milestone;
- structural-module milestone;
- extension-family milestone;
- pre-merge validation.

**Not necessarily a release claim**

Checkpoint success proves only the declared checkpoint contract.

### 8.3 Release mode

**Purpose**

Decide whether the selected language context satisfies all configured release requirements.

**Typical scope**

- strict project and environment preflight;
- full required source selection;
- required static scans;
- required checkpoint compilation;
- required entrypoint compilation;
- required scenarios;
- required marker and assertion checks;
- required gold comparison;
- required PGF construction;
- required artifact verification;
- known-issue and release-policy evaluation;
- regression comparison;
- complete reports and manifest.

**Expected use**

- release candidate validation;
- publication gate;
- tagged version preparation;
- language-project acceptance.

**Release semantics**

Release mode must fail when any required release criterion fails or cannot be evaluated.

### 8.4 Diagnostic mode

**Purpose**

Maximize actionable evidence and causal understanding.

**Typical scope**

- broad source selection;
- static scans;
- compilation of the configured diagnostic set;
- enhanced raw evidence retention;
- causal classification;
- optional diagnostic scenarios;
- optional introspection;
- previous-run comparison;
- detailed reports;
- non-release observations.

**Expected use**

- investigating widespread failure;
- separating root and downstream failures;
- auditing migration from another language;
- diagnosing toolchain or path problems;
- collecting evidence for AI-assisted review.

**Diagnostic semantics**

Diagnostic mode seeks completeness of evidence, not minimum runtime and not automatic release approval.

---

## 9. Mode comparison

| Capability | Quick | Checkpoint | Release | Diagnostic |
|---|---:|---:|---:|---:|
| Project configuration validation | Required | Required | Required, strict | Required |
| GF executable resolution | Required when GF is used | Required | Required, strict | Required |
| GF version probe | Normally required | Required | Required | Required unless explicitly skipped |
| Focused target selection | Primary | Optional | No | Optional |
| Configured checkpoints | No, unless targeted | Required for selected checkpoint | All required | Configurable |
| Required entrypoints | Only when targeted | As declared | All required | Configurable |
| Static scanning | Targeted | Required for selected set | Required policy | Broad |
| Compilation | Targeted | Required for checkpoint set | Required full set | Broad |
| Required checkpoint scenarios | No, unless selected | Required | Required | Included for diagnosis |
| Required release scenarios | No | Only if assigned | Required | May run, not a release claim |
| Optional diagnostic scenarios | Normally no | Optional | Policy-controlled | Yes |
| Gold comparison | When target scenario requires it | Required where declared | Required where declared | Yes where useful |
| PGF build | No | Optional | Required when configured | Optional diagnostic |
| Previous-run comparison | Optional | Recommended | Required when policy demands | Recommended |
| Detailed evidence retention | Bounded | Standard | Complete required evidence | Maximum practical evidence |
| Release decision | No | No | Yes | No |

The detailed inclusion and override rules belong to `VALIDATION_MODES.md`.

---

## 10. Validation dimensions

GF Wordbench treats validation as multiple dimensions rather than one binary operation.

### 10.1 Configuration validity

Checks whether the requested run can be interpreted safely and deterministically.

Examples:

- project file exists;
- schema is supported;
- resolved language identity is complete;
- source root exists;
- entrypoints and checkpoints are registered;
- scenario IDs are unique;
- required scenario files exist;
- required gold files exist where applicable;
- path containment rules hold;
- mode requirements are satisfied;
- timeout values are valid.

### 10.2 Toolchain validity

Checks whether GF Wordbench can invoke the configured toolchain.

Examples:

- GF executable resolves;
- executable is runnable;
- GF version can be probed;
- version is supported or policy-allowed;
- required RGL paths exist;
- GF path construction is valid;
- working directory is explicit;
- encoding policy is available.

### 10.3 Source inventory validity

Checks whether the intended source set is known and stable.

Examples:

- candidates are enumerated deterministically;
- include and exclude rules are applied;
- exclusions have reasons;
- target file is inside the project;
- configured modules exist;
- module identity can be determined;
- generated output is not mistaken for source;
- old-language identifiers are detected when migration policy requires it.

### 10.4 Static source validity

Checks source-level patterns without executing GF.

Examples:

- suspicious escape or arrow patterns;
- string-sensitive pattern misuse;
- structurally suspicious untyped cases;
- trailing whitespace where policy tracks it;
- project-specific anti-drift scans implemented through approved declarative mechanisms.

Static scanning provides findings, not GF compile truth.

### 10.5 Compilation validity

Checks whether selected GF modules compile through the configured GF executable and GF path.

Compilation validation includes:

- command construction;
- process execution;
- timeout handling;
- stdout and stderr capture;
- exit-code capture;
- diagnostic parsing;
- required artifact verification;
- structured compile result construction.

### 10.6 Dependency and causal validity

Checks whether failures are interpreted according to dependency relationships.

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

This dimension prevents one root failure from being presented as many unrelated root failures.

### 10.7 Scenario validity

Checks configured grammar behavior through native `.gfs` scripts.

Scenario validation may cover:

- load;
- missing functions;
- linearization;
- parsing;
- bounded generation;
- morphology;
- grammar introspection;
- PGF runtime behavior.

Scenario success requires more than process exit.

It may require:

- expected markers;
- completed sections;
- required assertions;
- expected artifacts;
- gold match.

### 10.8 Golden-output validity

Checks whether normalized scenario output matches reviewed project expectations.

Gold comparison requires:

- raw output retained;
- normalization version known;
- expected gold registered;
- deterministic comparison strategy;
- mismatch diff;
- explicit update workflow.

### 10.9 Artifact validity

Checks whether required generated artifacts exist and satisfy their contract.

Examples:

- `.gfo` exists after a successful compile when required;
- `.pgf` exists after a release build;
- expected concrete language is included;
- manifest entries exist;
- required reports exist;
- file hashes and sizes match the finalized manifest.

### 10.10 Regression validity

Checks how the current run compares with a previous compatible run.

Canonical change kinds:

```text
unchanged
improved
regressed
new
removed
```

Regression comparison consumes structured summaries, not Markdown.

### 10.11 Release-policy validity

Checks whether all required evidence meets project release policy.

Release policy may include:

- all checkpoints compile;
- all required entrypoints compile;
- all required scenarios pass;
- all required gold comparisons match;
- required PGF exists;
- no blocking known issue remains;
- no prohibited temporary implementation remains;
- required documentation and contract checks pass;
- no unsupported toolchain condition remains.

---

## 11. High-level validation pipeline

The validation pipeline consists of the following logical phases.

```text
1. Resolve request
2. Load and validate configuration
3. Initialize run and evidence paths
4. Validate toolchain
5. Select validation targets
6. Scan sources
7. Fingerprint sources
8. Compile targets and checkpoints
9. Parse diagnostics
10. Classify causal relationships
11. Run scenarios
12. Normalize and compare outputs
13. Build and verify PGF when applicable
14. Compare with previous run
15. Evaluate mode and release gates
16. Build structured run result
17. Write reports and manifest
18. Finalize run
```

A specialized document may split or combine implementation steps while preserving these responsibilities.

---

## 12. Phase 1 — Resolve request

Inputs may come from:

- CLI;
- GUI;
- automation;
- tests;
- a supported public application service.

The request resolution phase determines:

- canonical mode;
- target file or checkpoint when applicable;
- selected language context root;
- environment paths;
- GF executable;
- output root;
- documented overrides;
- execution flags.

Rules:

- CLI and GUI must use the same configuration builder;
- historical mode aliases are normalized here;
- raw user input must not flow directly into process command strings;
- explicit values override defaults only according to documented precedence;
- project release requirements must not be disabled by disposable UI state.

---

## 13. Phase 2 — Load and validate configuration

Configuration sources are resolved in documented precedence.

Conceptual order:

```text
framework defaults
→ project configuration
→ environment-specific configuration
→ explicit CLI or GUI overrides
→ validated RunConfig
```

Project identity remains authoritative in:

```text
<validation-profile-root>/project.toml
```

The resolved configuration must be explicit enough to reproduce the run.

A configuration failure must occur before affected validation stages launch.

---

## 14. Phase 3 — Initialize run and evidence paths

GF Wordbench creates one unique run directory.

The run path model must identify at least:

- run ID;
- run directory;
- raw evidence directory;
- scan evidence directory;
- compile evidence directory;
- scenario evidence directory;
- generated-artifact directories;
- details directory;
- summary paths;
- manifest path.

Rules:

- paths are created before stages use them;
- stages consume paths from the path model;
- reports do not choose filenames independently;
- run initialization failure is an execution error;
- an incomplete run should remain inspectable when safe.

---

## 15. Phase 4 — Validate toolchain

Toolchain preflight may include:

- executable-path validation;
- GF version probe;
- minimum-version check;
- known-incompatible-version check;
- RGL root validation;
- GF path validation;
- working-directory validation;
- encoding validation.

A toolchain failure must be distinguished from a language-project validation failure.

Examples:

| Condition | Category |
|---|---|
| GF executable missing | Configuration or launch error |
| GF process cannot start | Launch error |
| GF version unsupported | Unsupported-version error |
| Module has GF type error | Validation failure |
| Process exceeds timeout | Timeout execution state |
| Expected `.pgf` missing after apparent success | Artifact or contract failure |

---

## 16. Phase 5 — Select validation targets

Target selection consumes:

- mode;
- resolved source root;
- configured source glob;
- include and exclude policy;
- target file;
- checkpoint registry;
- entrypoint registry;
- maximum-file limit;
- project containment policy.

Selection produces:

- files seen;
- files included;
- files excluded;
- exclusion reasons;
- ordered target list;
- module identities where available.

Selection must be deterministic.

A required configured target that does not exist is not a normal exclusion; it is a configuration or validation failure according to context.

---

## 17. Phase 6 — Scan sources

Static scans execute on selected files.

Each scan result must preserve:

- file identity;
- rule identity;
- count;
- location where available;
- evidence excerpt where appropriate;
- scan log path.

Static scan findings and compilation results remain separate.

A source may:

- compile successfully while having scan findings;
- fail compilation without any scan finding;
- be excluded from compilation but still appear in inventory evidence if policy requires it.

---

## 18. Phase 7 — Fingerprint sources

Fingerprints support:

- previous-run comparison;
- stable source identity;
- change detection;
- evidence integrity.

Canonical fingerprints use the algorithm defined by the persisted schema.

Fingerprint failure must not erase:

- scan evidence;
- compile evidence;
- scenario evidence.

A fingerprint is evidence about source content, not a validation verdict by itself.

---

## 19. Phase 8 — Compile targets and checkpoints

Compilation operates through the common process runner.

For every compile operation, GF Wordbench records:

- target;
- module identity;
- executable;
- ordered arguments;
- GF path;
- working directory;
- start and end time;
- duration;
- exit code;
- timeout state;
- stdout path;
- stderr path;
- parsed primary diagnostic;
- produced artifacts;
- missing required artifact condition.

Compilation proceeds in deterministic target order.

Dependency-aware ordering may improve diagnostics but must not be used as unsupported proof of causality.

---

## 20. Phase 9 — Parse diagnostics

Diagnostic parsing transforms raw GF and process evidence into structured technical information.

The parser may derive:

- normalized error kind;
- source file;
- line and column;
- primary message;
- relevant detail;
- tool or contract failure kind.

Canonical technical error kinds are defined in the reference and schema documents.

Unrecognized diagnostic text must remain visible.

Parser inability must not turn a failure into success.

---

## 21. Phase 10 — Classify causal relationships

Causal classification operates after structured file results exist.

It distinguishes:

- a direct failure in the file being evaluated;
- a downstream failure caused by another failed dependency;
- an ambiguous relationship;
- known excluded noise;
- intentionally skipped work;
- successful results.

The classifier may use:

- normalized diagnostic paths;
- module identities;
- dependency information;
- known failed providers;
- processing context.

The classifier must not:

- launch GF;
- mutate raw diagnostics;
- redefine the technical error kind;
- claim certainty without evidence.

---

## 22. Phase 11 — Run scenarios

Scenarios are registered project assets.

Each scenario result records at least:

- scenario ID;
- script path;
- required or optional status;
- applicable mode;
- command;
- working directory;
- exit code;
- timeout state;
- duration;
- stdout path;
- stderr path;
- normalized output path;
- gold path where applicable;
- assertion results;
- produced artifacts;
- primary failure information.

Required scenarios must not be silently skipped.

An unsupported scenario command or incomplete marker sequence must not pass solely because GF returned zero.

---

## 23. Phase 12 — Normalize and compare outputs

Normalization occurs only after raw output capture.

Normalization may stabilize:

- line endings;
- approved root paths;
- run IDs;
- approved timing noise;
- ANSI sequences;
- explicitly excluded tool banners.

Normalization must preserve linguistic and diagnostic meaning.

Gold comparison then applies the scenario’s declared comparison strategy.

A gold mismatch is a validation failure, not a process launch error.

A missing required gold file is a failure.

Normal validation must not create or update gold automatically.

---

## 24. Phase 13 — Build and verify PGF

PGF validation applies when:

- release policy requires a PGF;
- a checkpoint explicitly validates PGF construction;
- diagnostic mode requests PGF investigation.

PGF success requires:

1. process contract succeeds;
2. required output artifact exists;
3. artifact path matches configuration;
4. expected grammar or concrete-language requirement is satisfied where verifiable;
5. artifact is catalogued.

A zero exit code with no required PGF is not success.

---

## 25. Phase 14 — Compare with previous run

Previous-run comparison must:

- locate a compatible previous run deterministically;
- load structured summary data;
- support documented legacy schemas;
- normalize stable identities;
- compare files and scenarios;
- classify changes;
- preserve current-run validity if previous data is missing or invalid.

A missing previous run produces no comparison.

It does not produce a current validation failure unless a release policy explicitly requires regression evidence.

---

## 26. Phase 15 — Evaluate gates

Gate evaluation consumes structured stage results.

It determines:

- whether required work executed;
- whether required work passed;
- whether optional failures are visible;
- whether required artifacts exist;
- whether blocking known issues remain;
- whether the selected mode’s success criteria are met;
- whether release approval is possible.

Gate evaluation must not reparse raw logs when structured results exist.

---

## 27. Phase 16 — Build structured run result

The structured run result aggregates:

- resolved configuration;
- run paths;
- timestamps and duration;
- GF version;
- file inventory totals;
- file results;
- scenario results;
- artifact results;
- regression entries;
- top errors;
- stage completion;
- warnings;
- overall status.

The structured run result is the source of truth for report generation.

---

## 28. Phase 17 — Write reports and manifest

The report phase produces the configured stable artifacts.

Canonical outputs include:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw evidence
detail evidence
generated GF artifacts
```

Reports must remain projections of the same structured result.

The manifest is generated after all owned artifacts have been written and stabilized.

The manifest must not hash itself.

---

## 29. Phase 18 — Finalize run

Finalization uses the protected reserve defined by ADR-0010 and must:

- stop or account for every owned child process;
- preserve partial stdout, stderr, timing, and artifact evidence;
- set the finish timestamp;
- compute the run duration;
- lock aggregate totals;
- lock the overall status;
- record incomplete, cancelled, timed-out, and unstarted work explicitly;
- ensure required report paths are recorded;
- verify required artifacts;
- write terminal results atomically or through a recoverable replacement protocol;
- write and publish the manifest;
- leave the run directory inspectable.

Finalization is idempotent. Repeating it cannot erase valid evidence, corrupt published artifacts, or transform an incomplete run into success.

A report-generation error remains distinguishable from a language validation failure.

Already captured evidence remains available.

---

## 30. Status model

GF Wordbench keeps four concepts separate.

### 30.1 Validation status

Canonical per-item validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Meanings:

| Status | Meaning |
|---|---|
| `OK` | Requested validation executed and its criteria passed |
| `FAIL` | Validation executed, but one or more criteria failed |
| `ERROR` | GF Wordbench could not execute, complete, or interpret the required contract |
| `SKIPPED` | Work was intentionally not executed under explicit policy |

### 30.2 Execution state

Canonical execution states:

```text
completed
timed_out
cancelled
launch_failed
not_started
```

Execution state is not validation status.

Examples:

- `timed_out` normally maps to validation `ERROR` or `FAIL` according to the stage contract;
- `cancelled` records user or controller action;
- `launch_failed` means the process did not start;
- `completed` does not imply validation success.

### 30.3 Technical error kind

Error kind describes the technical nature of a result.

Canonical families include:

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

Specialized reference documents may define additional approved kinds through a versioned change.

### 30.4 Causal diagnostic class

Causal class describes the relationship of a file or scenario result to root failure.

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Technical execution failures must not be inserted into this causal enum.

---

## 31. Overall run status

Canonical overall statuses:

```text
OK
FAIL
ERROR
```

Canonical precedence:

```text
ERROR > FAIL > OK
```

### 31.1 Overall `OK`

The run is `OK` when:

- every required stage for the selected mode executed;
- every required criterion passed;
- every required artifact exists;
- no blocking configuration, toolchain, contract, or report-finalization error remains.

Optional warnings may coexist with overall `OK` only when policy explicitly permits them and reports preserve them.

### 31.2 Overall `FAIL`

The run is `FAIL` when:

- required validation executed;
- the system interpreted the result successfully;
- one or more required project criteria failed.

Examples:

- GF syntax or type failure;
- required scenario assertion failure;
- required gold mismatch;
- required missing linearization;
- required PGF criterion failure;
- blocking known issue.

### 31.3 Overall `ERROR`

The run is `ERROR` when a required contract could not be executed or interpreted reliably.

Examples:

- invalid required configuration;
- GF executable cannot launch;
- required process times out under error policy;
- scenario script cannot be read;
- required evidence cannot be written;
- result schema is internally inconsistent;
- required manifest cannot be finalized;
- required tool version is unsupported.

### 31.4 Skipped required work

Required work must not disappear into a neutral `SKIPPED`.

When required work is skipped without an approved mode policy, the run must become `FAIL` or `ERROR` according to cause.

---

## 32. Required and optional validation

### 32.1 Required item

A required item:

- belongs to the selected mode;
- must exist;
- must execute unless an explicit approved exception applies;
- must pass;
- contributes to overall failure;
- must remain visible in structured results.

### 32.2 Optional item

An optional item:

- may execute according to mode or user request;
- remains visible when executed;
- may warn or fail without automatically blocking release;
- must not be silently promoted to required;
- must not be silently omitted from evidence after execution.

### 32.3 Disabled item

A disabled project item must have:

- stable ID;
- reason;
- owner;
- expected reactivation or retirement policy;
- release impact.

### 32.4 Requiredness ownership

Requiredness is defined by:

- project configuration;
- mode policy;
- release policy;
- approved framework contracts.

Disposable GUI state must not change mandatory release requiredness.

---

## 33. Stop and continue policy

GF Wordbench uses controlled continuation.

### 33.1 Conditions that normally stop affected execution

- project configuration cannot be interpreted;
- required paths are unsafe or unresolved;
- required GF executable cannot be launched;
- run directory cannot be initialized;
- required source root does not exist;
- internal result contract is corrupted;
- user cancellation requests termination.

### 33.2 Conditions that normally allow continued evidence collection

- one source fails compilation;
- one optional scenario fails;
- one direct failure causes downstream failures;
- a static scan reports findings;
- previous-run summary is missing;
- one detail report cannot be written while core summary remains writable;
- an optional diagnostic tool is unavailable.

### 33.3 Release-mode continuation

Release mode may continue after a blocking failure to collect complete evidence, provided continued execution is:

- safe;
- bounded;
- useful;
- clearly marked as occurring after release failure became inevitable.

Continuing does not convert a failed gate into success.

---

## 34. Evidence model

GF Wordbench distinguishes three evidence levels.

### 34.1 Raw evidence

Unmodified evidence from source and external execution.

Examples:

- selected source identity;
- stdout;
- stderr;
- command;
- exit code;
- generated file;
- raw scenario transcript.

### 34.2 Normalized evidence

A stable representation derived through versioned rules.

Examples:

- normalized scenario output;
- normalized source path;
- parsed diagnostic;
- structured artifact entry.

### 34.3 Interpretive evidence

A conclusion derived from structured evidence.

Examples:

- direct failure;
- downstream blocker;
- regression;
- release gate failure;
- top-error group.

Derived evidence must remain traceable to raw evidence.

---

## 35. Artifact ownership

Each artifact has one writer.

| Artifact | Owner |
|---|---|
| Source scan log | Scanner |
| Compile stdout/stderr | Compiler through process layer |
| Scenario stdout/stderr | Scenario runner through process layer |
| Normalized scenario output | Normalization/scenario owner |
| Gold diff | Gold-comparison owner |
| `.gfo` | GF execution stage, catalogued by Wordbench |
| `.pgf` | PGF build stage, catalogued by Wordbench |
| `summary.json` | JSON report writer |
| `summary.md` | Markdown report writer |
| `AI_READY.md` | AI-ready report writer |
| `top_errors.txt` | Top-error report owner |
| `manifest.json` | Manifest writer |
| State file | State manager |
| Gold files | Project maintainer through explicit update workflow |

No observer may rewrite an artifact owned by another component.

---

## 36. Regression semantics

Regression is not equivalent to current failure.

Examples:

| Previous | Current | Change |
|---|---|---|
| `FAIL` | `OK` | Improved |
| `OK` | `FAIL` | Regressed |
| Missing | Present | New |
| Present | Missing | Removed |
| Same status and identity | Same | Unchanged |

A current run may:

- be `FAIL` but improved;
- be `OK` with removed optional coverage;
- be `ERROR` without a meaningful regression comparison.

Release policy decides whether a regression blocks release beyond the current required status.

---

## 37. Direct and downstream failure overview

A direct failure originates in the evaluated provider or target according to available evidence.

A downstream failure is caused by a failed dependency or provider.

An ambiguous failure cannot be assigned confidently.

Rules:

- directness must be evidence-based;
- processing order alone is insufficient;
- a blocker should be recorded when known;
- downstream results remain failures but do not inflate root-cause counts;
- reports must preserve both the immediate diagnostic and causal classification.

Detailed rules belong to:

```text
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
```

---

## 38. Scenario overview

A scenario is a registered `.gfs` asset that validates an explicit project contract.

A scenario may use:

- stable output markers;
- assertions;
- input files;
- gold comparison;
- generated-artifact checks.

A scenario must declare:

- ID;
- purpose;
- script;
- target entrypoint;
- requiredness;
- applicable modes;
- timeout policy;
- assertion strategy;
- gold file where applicable;
- normalization version.

Scenario IDs are stable project contracts.

---

## 39. Gold overview

A gold file is reviewed expected normalized output.

Gold files are:

- project source assets;
- version controlled;
- scenario-specific;
- read-only during normal validation;
- updated only through an explicit reviewed workflow.

Gold files are not:

- raw GF logs;
- automatic snapshots;
- substitutes for scenario purpose;
- proof of linguistic correctness without review.

---

## 40. Release-gate overview

Release mode evaluates at least the configured required domains.

The release policy requires:

1. valid project configuration;
2. supported GF toolchain;
3. required source inventory present;
4. required checkpoints compile;
5. required entrypoints compile;
6. required scenarios pass;
7. required gold comparisons match;
8. required PGF builds and exists;
9. required artifacts are catalogued;
10. no blocking known issue remains;
11. no prohibited fallback remains;
12. required documentation and project contracts are current;
13. final reports and manifest are valid.

The selected language context may add stricter language-specific gates.

It must not weaken mandatory framework integrity or security gates.

---

## 41. Legacy compatibility with `gf-audit`

GF Wordbench preserves the useful validation semantics inherited from `gf-audit`:

- deterministic file selection and exclusion reasons;
- static scanning;
- source fingerprinting;
- GF version probing;
- per-file compilation;
- diagnostic parsing;
- direct, downstream, and ambiguous causal classification;
- previous-run comparison;
- structured run results;
- JSON, Markdown, AI-ready, raw-log, and detail reports;
- CLI and GUI entrypoints.

Canonical Wordbench validation adds the contracts defined in this documentation set:

- canonical modes;
- one active-project configuration;
- checkpoint policy;
- native `.gfs` scenario execution;
- marker and assertion verification;
- output normalization;
- reviewed gold comparison;
- PGF release validation;
- manifest publication;
- explicit execution state;
- run budgets and protected finalization;
- release gates;
- contract and schema validation.

Compatibility readers may accept documented legacy aliases and schemas. Canonical writers emit only canonical GF Wordbench names, statuses, schemas, and artifact contracts.

Legacy compatibility never restores a multi-project model, duplicates project authority, or weakens release requirements.

---

## 42. Component responsibility map

| Responsibility | Designated owner |
|---|---|
| Application defaults | `app/config.py` |
| Configuration construction | `app/bootstrap.py` |
| Active-project loading | `app/project_config.py` |
| Shared models | `app/models.py` |
| Run-path construction | bootstrap/path owner |
| File discovery | `app/audit/file_selector.py` |
| Static source checks | `app/audit/scanner.py` |
| Source fingerprints | `app/audit/fingerprint.py` |
| GF compilation | `app/audit/compiler.py` |
| Process execution | `app/utils/process_utils.py` |
| GF path utilities | GF path service |
| Diagnostic parsing | `app/audit/diagnostics.py` |
| Causal classification | `app/audit/classifier.py` |
| Scenario execution | `app/audit/scenario_runner.py` |
| Output normalization | normalization service |
| Gold comparison | gold-comparison service |
| PGF build | PGF build service |
| Regression comparison | `app/audit/diff.py` |
| Result construction | `app/audit/result_model.py` |
| Audit orchestration | `app/audit/audit_core.py` |
| JSON summary | `app/reports/report_json.py` |
| Markdown summary | `app/reports/report_md.py` |
| AI-ready packet | `app/reports/report_ai_ready.py` |
| Raw and aggregate logs | `app/reports/report_logs.py` |
| Detail evidence | `app/reports/report_details.py` |
| Manifest | manifest writer |
| CLI | `app/main_cli.py` |
| GUI | `app/main_gui.py`, `app/gui/` |
| Persistent UI state | `app/state.py` |
| Project validation policy | `<validation-profile-root>/project.toml` |
| Project scenarios | `<validation-profile-root>/validation/scenarios/` |
| Project gold files | `<validation-profile-root>/validation/gold/` |

Concrete filenames may evolve through coordinated contract changes, but responsibility ownership remains singular and documented.

---

## 43. Dependency directions

Expected:

```text
CLI / GUI
    → bootstrap
    → audit core
    → stages
    → process and filesystem infrastructure

audit core
    → result construction
    → classification
    → regression comparison
    → reports

reports
    → structured models

project configuration
    → project loader
    → resolved run configuration
```

Prohibited:

```text
reports → compiler
reports → scanner
reports → scenario runner
models → reports
models → GUI
scanner → compiler
compiler → reports
classifier → process execution
GUI widgets → GF executable
project configuration → GUI state
project scenario → arbitrary Python plugin
```

Circular dependencies between validation layers are prohibited.

---

## 44. Configuration overview

Validation configuration is divided into:

### 44.1 Framework defaults

Language-neutral defaults such as:

- filenames;
- safe timeout defaults;
- default retention behavior;
- default output root;
- supported canonical modes.

### 44.2 Active-project configuration

Language-specific project contracts such as:

- resolved language identity;
- source root;
- source glob;
- entrypoints;
- checkpoints;
- GF path parts;
- required scenarios;
- optional scenarios;
- release targets;
- expected artifacts.

### 44.3 Environment configuration

Machine-local facts such as:

- GF executable;
- RGL root;
- output root;
- environment-specific path overrides.

### 44.4 Disposable application state

Convenience preferences such as:

- last mode;
- last local paths;
- last run pointer;
- display preferences.

State must not define project truth or release policy.

---

## 45. Security and trust boundaries

Validation executes external tools and executable GF scenario scripts.

The system must therefore:

- validate path containment;
- avoid shell invocation by default;
- represent commands as ordered arguments;
- use explicit working directories;
- use finite timeouts;
- treat `.gfs` scenarios as executable input;
- prohibit unauthorized shell escape behavior;
- avoid project-supplied Python execution;
- avoid secret persistence;
- avoid complete environment dumps;
- preserve raw evidence;
- distinguish launch failure from GF failure;
- reject traversal outside authorized roots;
- write persistent files atomically where required.

Security failure is not a language validation failure.

---

## 46. Performance policy

Validation remains useful at different feedback speeds.

### 46.1 Quick responsiveness

Quick mode:

- avoid unrelated full-project work;
- bound target count;
- avoid optional scenarios by default;
- avoid rebuilding PGF unless targeted;
- still preserve valid evidence.

### 46.2 Checkpoint efficiency

Checkpoint mode:

- execute only the declared layer and dependencies;
- reuse configuration resolution;
- avoid duplicated compilation caused only by reporting;
- preserve deterministic order.

### 46.3 Release completeness

Release mode prioritizes complete required evidence over minimum runtime.

### 46.4 Diagnostic depth

Diagnostic mode may retain more evidence and execute broader checks, but must still:

- use finite timeouts;
- bound generation;
- record truncation;
- avoid uncontrolled process accumulation.

### 46.5 Concurrency

Concurrency may be introduced only when:

- result ordering remains deterministic;
- artifact paths cannot collide;
- GF and filesystem behavior are safe;
- cancellation is controlled;
- logs remain attributable;
- contract tests prove equivalence.

Sequential execution remains the default until concurrency provides measured value and preserves every validation contract.

---

## 47. Testing overview

The validation system requires several test levels.

### 47.1 Unit tests

Unit tests cover:

- mode normalization;
- configuration validation;
- file selection;
- static scan rules;
- diagnostic parsers;
- causal classification;
- normalization;
- gold comparison;
- result aggregation;
- release-gate calculation;
- report projection.

### 47.2 Contract tests

Contract tests cover:

- component boundaries;
- public result fields;
- status semantics;
- process evidence;
- artifact ownership;
- schema round trips;
- canonical mode names;
- CLI/GUI parity;
- scenario requiredness;
- gold immutability;
- report non-execution;
- manifest completeness.

### 47.3 Integration tests

Integration tests with a small fixture grammar cover:

- successful compile;
- failed compile;
- downstream failure;
- GF version probe;
- `.gfs` load;
- parse;
- linearize;
- bounded generation;
- PGF build;
- scenario mismatch;
- timeout containment;
- full report set.

### 47.4 Release tests

Release tests cover:

- complete required pipeline;
- missing checkpoint;
- missing required scenario;
- missing gold;
- missing PGF;
- blocking known issue;
- unsupported GF version;
- report or manifest failure;
- legacy mode migration;
- legacy summary loading.

Tests requiring a real GF installation should be marked separately from pure unit tests.

---

## 48. Validation invariants

The following invariants apply to every mode.

### 48.1 Configuration invariants

- selected language context identity is explicit;
- canonical mode is known;
- required mode inputs exist;
- all resolved paths are normalized;
- unsafe path traversal is rejected;
- required configuration is validated before dependent work starts.

### 48.2 Process invariants

- executable is explicit;
- arguments are ordered;
- working directory is explicit;
- timeout is finite;
- stdout and stderr are captured separately;
- launch failure is distinct from non-zero exit;
- raw evidence precedes normalization.

### 48.3 Result invariants

- every executed item has one structured result;
- status and execution state are separate;
- technical error kind and causal class are separate;
- deterministic order is preserved;
- required skipped work affects overall status;
- raw evidence remains traceable.

### 48.4 Scenario invariants

- IDs are unique;
- required scripts exist;
- applicable modes are explicit;
- expected markers are checked;
- gold comparison follows normalization;
- normal execution does not modify gold;
- unknown assertion types do not pass.

### 48.5 Reporting invariants

- reports consume one structured run result;
- reports do not launch validation;
- artifact paths come from their owner;
- canonical persistent schemas are versioned;
- report failure does not erase raw evidence;
- manifest entries refer to finalized artifacts.

### 48.6 Release invariants

- every required checkpoint passes;
- every required scenario passes;
- every required artifact exists;
- accepted exceptions are explicit;
- blocking issues remain blocking;
- missing evidence is not treated as proof of success.

---

## 49. Anti-drift indicators

Probable validation drift exists when:

- CLI and GUI select different stages for the same mode;
- `file` or `all` appears in canonical new output;
- a required scenario is absent without failure;
- a report launches GF;
- a stage invents an artifact filename;
- static scanning is reported as GF truth;
- stdout is retained but stderr is discarded;
- timeout is reported as a syntax failure;
- one module defines a new status literal;
- causal classification occurs in the process layer;
- gold changes during normal execution;
- a zero exit code overrides missing markers;
- a required PGF is absent but release passes;
- previous-run Markdown is parsed instead of JSON;
- resolved language identity comes from UI state;
- one run resolves several selected language contexts;
- Wordbench validation reads a `gf-portfolio` registry or private state;
- source selection depends on filesystem order;
- language-specific paths appear in framework defaults;
- optional work silently becomes release-required;
- a schema changes without migration;
- raw evidence is overwritten by normalized output;
- a failed report causes the run to appear as if validation never occurred.

Every indicator must trigger review of the relevant owner and lock.

---

## 50. Detailed documentation map

This overview delegates details as follows.

```text
docs/validation/VALIDATION_PIPELINE.md
    Exact stage sequence, stage inputs, outputs, and continuation policy

docs/validation/VALIDATION_MODES.md
    Exact quick, checkpoint, release, and diagnostic policies

docs/validation/FILE_SELECTION.md
    Candidate discovery, include/exclude rules, target identity

docs/validation/STATIC_SCANNING.md
    Scan rules, masking, findings, false-positive policy

docs/validation/COMPILATION_VALIDATION.md
    GF compilation commands, evidence, artifact checks

docs/validation/SCENARIO_VALIDATION.md
    Scenario registry, execution, assertions, result semantics

docs/validation/REGRESSION_COMPARISON.md
    Previous-run discovery and change classification

docs/validation/RELEASE_GATES.md
    Release requirements and exception policy

docs/scenarios/
    Scenario format, markers, normalization, gold workflow

docs/diagnostics/
    Diagnostic parsing, error kinds, direct/downstream rules

docs/reports/
    Summary, AI-ready, raw-log, and manifest contracts

docs/configuration/
    Project, environment, state, and precedence rules

docs/gf/
    GF toolchain, path, compilation, script, PGF, and version rules
```

Normative lock documents remain authoritative when a detail overlaps:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 51. Validation-system conformance

The validation system conforms to this contract when:

```text
[ ] Canonical modes govern every entrypoint
[ ] Legacy mode aliases migrate correctly
[ ] Active-project configuration is authoritative
[ ] CLI and GUI use the same core path
[ ] Project and environment preflight precede dependent work
[ ] File selection is deterministic
[ ] Static scans preserve structured findings
[ ] Compile evidence includes command, stdout, stderr, exit, duration, and timeout
[ ] Diagnostic parsing preserves unrecognized evidence
[ ] Direct/downstream/ambiguous classification follows preserved evidence
[ ] Scenario runner executes native .gfs scripts
[ ] Marker and assertion verification follows the scenario contract
[ ] Output normalization is versioned
[ ] Gold comparison is explicit and deterministic
[ ] Normal validation cannot update gold
[ ] PGF release validation enforces artifact and release contracts
[ ] Previous-run comparison uses structured summaries
[ ] Requiredness is mode-aware
[ ] Overall status uses documented semantics
[ ] Raw evidence remains immutable
[ ] Reports consume the structured run result
[ ] Manifest verifies stabilized artifacts
[ ] Persistent schemas are versioned
[ ] Contract tests cover component boundaries
[ ] Real-GF integration tests cover the core pipeline
[ ] Release gates are enforced
[ ] Documentation and lock files agree
```

---

## 52. Governing rule

GF Wordbench validation is valid only when the result can be explained from preserved evidence.

A successful run is not defined by:

- one process returning zero;
- one module compiling;
- one report being generated;
- one scenario producing output;
- one previous run being better or worse.

A successful run is defined by the selected mode’s required contracts executing and passing with complete, structured, attributable evidence.

Therefore:

> No validation decision may be produced by bypassing configuration ownership, external-tool contracts, structured results, evidence preservation, requiredness policy, or final gate evaluation.
