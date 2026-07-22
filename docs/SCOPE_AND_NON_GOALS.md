# GF Wordbench — Scope and Non-Goals

**Document ID:** `GF-WB-SCOPE-NON-GOALS`  
**Status:** Normative  
**Applies to:** GF Wordbench framework and its active language-project contract  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\SCOPE_AND_NON_GOALS.md`  
**Scope version:** `1.0.0`  
**Last reviewed:** `2026-07-21`

---

## 1. Purpose

This document defines the product boundary of GF Wordbench.

It states:

- what GF Wordbench is;
- which problems it is designed to solve;
- which capabilities belong to the framework;
- which responsibilities remain owned by Grammatical Framework;
- which responsibilities belong to the active language project;
- which features are intentionally excluded;
- which future additions are acceptable;
- which additions would represent architectural drift.

This document is normative.

When another document, implementation detail, user-interface behavior, or proposed feature conflicts with this scope, this document takes precedence unless the scope is deliberately revised.

The goal is not to minimize capability.

The goal is to keep every capability useful, owned, testable, and aligned with the actual development and validation of one GF language project.

---

## 2. Product definition

GF Wordbench is a local development and validation workbench for one active Grammatical Framework language project.

It coordinates:

```text
project configuration
→ source selection
→ static source checks
→ GF compilation
→ final PGF construction
→ native GF scenario execution
→ assertion and gold comparison
→ diagnostic classification
→ regression comparison
→ evidence preservation
→ human, machine, and AI-ready reporting
```

GF Wordbench does not replace GF.

GF remains the authoritative engine for:

- GF syntax;
- type checking;
- module loading;
- dependency resolution;
- `.gf` to `.gfo` compilation;
- `.pgf` construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF runtime behavior;
- GF diagnostics.

GF Wordbench is authoritative for:

- selecting what to validate;
- constructing reproducible GF commands;
- resolving the execution environment;
- applying timeouts and process limits;
- capturing raw evidence;
- normalizing unstable output;
- evaluating project-defined assertions;
- comparing results with reviewed gold files;
- distinguishing validation failure from tool or framework failure;
- classifying likely direct and downstream failures;
- preserving run history;
- producing reports;
- enforcing documented project and schema contracts.

---

## 3. Primary product objective

The primary objective is:

> Make the development state of one GF language project reproducible, diagnosable, reviewable, and objectively releasable.

A language project should not be considered complete merely because one file compiles.

GF Wordbench must support evidence across multiple validation layers:

```text
source integrity
module compilation
dependency coherence
entrypoint compilation
PGF construction
grammar loading
scenario execution
linguistic examples
regression stability
release criteria
```

The framework exists to turn these checks into one controlled workflow.

---

## 4. Intended users

GF Wordbench is designed primarily for:

- developers implementing or repairing GF language resources;
- maintainers validating a language before release;
- researchers extending a concrete grammar;
- developers migrating an existing GF language into a controlled workflow;
- maintainers using AI assistance while preserving direct evidence;
- contributors reviewing changes across dependent GF modules;
- automation systems executing the same validations non-interactively.

The framework assumes that the user understands basic GF concepts or works from project documentation that defines them.

GF Wordbench is not intended to teach GF from first principles.

Introductory examples may exist, but language and GF education are not the product’s primary function.

---

## 5. Core design principles

### 5.1 One active language project

One GF Wordbench copy represents one active language project.

Language-specific information belongs in:

```text
project/project.toml
project/docs/
project/validation/
the active GF source tree
```

Framework modules must remain language-neutral.

A user may duplicate or reset GF Wordbench to work on another language.

GF Wordbench does not need to manage several active languages simultaneously inside one runtime or one project configuration.

### 5.2 GF as execution authority

GF Wordbench must invoke GF for GF semantics.

It must not implement a competing parser, type checker, module resolver, runtime, generator, or PGF engine.

Static scanning may identify suspicious source patterns, but scan results remain heuristic evidence.

GF execution remains authoritative for compile, load, parse, linearize, generate, and runtime truth.

### 5.3 Evidence before interpretation

Raw evidence must be preserved before it is normalized or interpreted.

The framework should retain, where applicable:

- executable path;
- ordered arguments;
- working directory;
- relevant environment values;
- standard input source;
- exit code;
- timeout state;
- duration;
- stdout;
- stderr;
- generated artifacts;
- normalized output;
- comparison result.

Reports must be derived from existing evidence.

Report generators must not rerun GF.

### 5.4 Explicit contracts

Behavior crossing a file, process, schema, scenario, module, or artifact boundary must be documented and testable.

GF Wordbench uses dedicated contract locks for:

- Python and framework interfile contracts;
- external-tool contracts;
- persisted schemas;
- active-project interfile contracts.

Internal refactoring is permitted when externally visible promises remain compatible.

### 5.5 Deterministic validation

Given equivalent:

- source content;
- project configuration;
- GF version;
- execution environment;
- scenario inputs;
- normalization version;

GF Wordbench should produce deterministically ordered and semantically equivalent results.

Unstable values may be normalized only through documented rules.

### 5.6 Safe defaults

Normal validation must be observational.

It must not silently:

- modify GF sources;
- rewrite project configuration;
- update gold files;
- remove project files;
- alter external dependencies;
- accept a missing required artifact;
- convert an error into success.

Destructive or baseline-changing operations require explicit commands.

### 5.7 Structured source of truth

Machine-readable data must have one canonical structured source.

For run results, that source is `summary.json`.

Markdown and plain-text reports are derived views.

They must not become alternate machine schemas.

---

## 6. In-scope capabilities

## 6.1 Active-project configuration

GF Wordbench includes a versioned project configuration contract.

The project configuration may define:

- project identity;
- language identity;
- source directory;
- source-file selection rules;
- GF path components;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- release targets;
- expected artifacts;
- project-specific validation policy.

Configuration must be validated before execution.

Language identity must not be inferred from GUI state, previous run folders, or hardcoded framework defaults.

---

## 6.2 Environment resolution

GF Wordbench may resolve and validate:

- project root;
- RGL root;
- GF executable;
- output root;
- process working directories;
- required path components;
- supported GF version;
- optional environment overrides.

The resolved environment used for a run must be recorded.

Convenient discovery may be supported, but execution must use an explicit resolved configuration.

---

## 6.3 Source-file selection

GF Wordbench may select GF source files using:

- project-relative source roots;
- glob patterns;
- inclusion expressions;
- exclusion expressions;
- target files;
- checkpoints;
- entrypoints;
- validation mode;
- maximum-file limits.

Selection must be deterministic.

Excluded noise, backups, temporary files, and disabled files must not be compiled accidentally.

File selection is not dependency resolution.

GF remains authoritative for GF imports and module resolution.

---

## 6.4 Static source scanning

GF Wordbench may perform bounded static checks for known risky source patterns.

Examples may include:

- suspicious slash or arrow forms;
- runtime string matching;
- untyped string-pattern constructs;
- formatting anomalies relevant to source integrity;
- project-specific forbidden patterns when explicitly configured.

Static scanning must:

- preserve source files;
- mask comments and strings correctly;
- produce structured counts;
- preserve detailed findings;
- remain separate from compile status;
- avoid claiming complete GF parsing.

A scan finding may be a warning or project-policy failure.

It is not automatically a GF compilation failure.

---

## 6.5 GF version probing

GF Wordbench may execute a controlled version probe.

It may:

- record the resolved executable;
- capture the reported version;
- compare it with a supported-version policy;
- reject known incompatible versions;
- warn about unknown newer versions;
- skip probing only through explicit configuration.

Version probing must not be treated as language validation.

---

## 6.6 Module compilation

GF Wordbench includes reproducible compilation of GF modules.

Compilation support includes:

- explicit executable selection;
- ordered arguments;
- explicit GF path;
- explicit working directory;
- per-process timeout;
- stdout and stderr capture;
- exit-code capture;
- generated `.gfo` collection;
- diagnostic extraction;
- evidence preservation.

Module compilation may be performed:

- on one target;
- on selected files;
- on checkpoints;
- on entrypoints;
- as part of a larger release workflow.

---

## 6.7 PGF construction

GF Wordbench includes construction and verification of final `.pgf` artifacts when required by the active project.

PGF validation may include:

- final entrypoint selection;
- deterministic command construction;
- required artifact existence;
- artifact size and hash recording;
- load verification;
- release-policy checks.

A successful command without the required `.pgf` artifact is not a successful PGF build.

---

## 6.8 Native `.gfs` scenario execution

GF Wordbench includes execution of native GF shell scenarios.

Scenarios may exercise:

- grammar import;
- module loading;
- missing-linearization inspection;
- parsing;
- linearization;
- generation;
- morphology;
- type or source inspection;
- project-defined smoke tests;
- release examples.

The scenario runner must execute GF.

It must not reimplement GF shell command semantics.

Scenario files are executable project inputs and must be treated as trusted project code or explicitly isolated according to policy.

---

## 6.9 Scenario markers and assertions

GF Wordbench may define stable markers around scenario sections.

It may validate:

- marker presence;
- marker completion;
- required sections;
- forbidden output;
- required output;
- exact normalized output;
- artifact production;
- bounded result counts;
- scenario-specific success rules.

A zero GF exit code alone is not sufficient proof that every scenario command and assertion succeeded.

---

## 6.10 Golden-output testing

GF Wordbench includes reviewed golden-output comparison.

It may:

- normalize unstable output;
- compare normalized output with `.gold`;
- generate readable diffs;
- record normalization version;
- require gold files for release scenarios;
- support an explicit gold-update workflow.

Normal validation must never silently rewrite `.gold` files.

Golden outputs are regression contracts, not proof that every linguistic result is universally correct.

---

## 6.11 Diagnostic extraction and normalization

GF Wordbench may extract stable diagnostic information from GF and framework execution.

It may record:

- primary error;
- detailed error;
- error kind;
- source path;
- line and column when available;
- tool failure;
- timeout;
- launch failure;
- configuration failure;
- artifact failure;
- scenario assertion failure.

Raw diagnostics must remain available.

Normalization must not rewrite the semantic meaning of a GF error.

---

## 6.12 Failure classification

GF Wordbench may classify failure relationships.

Canonical causal classes include:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

These classes describe likely causal position, not the technical kind of error.

Technical error kinds are tracked separately.

The classifier may infer likely blockers from evidence and dependency information.

It must not claim certainty where evidence is insufficient.

---

## 6.13 Regression comparison

GF Wordbench may compare a run with a previous compatible run.

It may classify changes as:

```text
unchanged
improved
regressed
new
removed
```

Comparison must use structured persisted summaries.

Markdown report parsing must not be the primary comparison mechanism.

A missing or unreadable previous run must not corrupt the current result.

---

## 6.14 Result and artifact persistence

GF Wordbench includes versioned persisted formats for:

- project configuration;
- application state;
- run summaries;
- file results;
- scenario results;
- diff entries;
- top-error records;
- artifact manifests;
- normalized scenario output;
- golden expectations.

Persisted-format changes require explicit versioning and migration policy.

---

## 6.15 Artifact manifests and integrity

GF Wordbench may generate an artifact manifest.

The manifest may record:

- artifact path;
- semantic role;
- media type;
- required or optional state;
- byte size;
- SHA-256 hash;
- producing component.

The manifest may be used to verify that run evidence has not changed after finalization.

---

## 6.16 Human-readable reporting

GF Wordbench includes human-readable run reporting.

Reports may summarize:

- environment;
- selected validation mode;
- file results;
- scenario results;
- direct and downstream failures;
- regressions;
- top errors;
- artifact locations;
- release-gate outcome.

Human reports remain derived views.

---

## 6.17 Machine-readable reporting

GF Wordbench includes a versioned machine-readable run summary.

The machine summary is intended for:

- previous-run comparison;
- automated checks;
- GUI result loading;
- external analysis;
- migration tools;
- validation of report consistency.

Its schema is governed by `PERSISTED_SCHEMA_LOCK.md`.

---

## 6.18 AI-ready handoff

GF Wordbench includes an AI-ready report derived from completed run evidence.

It may contain:

- run context;
- primary failures;
- causal classification;
- bounded raw excerpts;
- scan findings;
- failed scenarios;
- relevant artifact paths;
- previous-run changes;
- known uncertainty.

The AI report must not:

- rerun validation;
- invent missing evidence;
- expose secrets;
- replace raw evidence;
- claim linguistic correctness unsupported by tests.

---

## 6.19 CLI

GF Wordbench includes a complete command-line interface.

The CLI is the authoritative automation surface.

It must support non-interactive execution of all required validation workflows.

CLI behavior includes:

- configuration selection;
- mode selection;
- target selection;
- run execution;
- exit-code mapping;
- report and artifact discovery;
- schema checks;
- explicit migration or update operations where supported.

---

## 6.20 GUI

GF Wordbench may include a graphical interface.

The GUI is a convenience layer over the same application and audit contracts used by the CLI.

The GUI may provide:

- path selection;
- project overview;
- validation-mode selection;
- progress display;
- result summaries;
- report opening;
- last-run state.

The GUI must not define alternate validation semantics.

A project must remain fully usable without the GUI.

---

## 6.21 Validation modes

The final product may provide these principal modes:

```text
quick
checkpoint
release
diagnostic
```

Their intent is:

### `quick`

Fast feedback for a focused development change.

### `checkpoint`

Validation of a declared subsystem or development layer.

### `release`

All required evidence for project completion and release.

### `diagnostic`

Expanded evidence for difficult failures and dependency cascades.

Mode definitions belong to `VALIDATION_MODES.md`.

This document locks only their product-level purpose.

---

## 6.22 Project lifecycle

GF Wordbench includes a controlled project lifecycle.

It may support:

- creating a project from a clean template;
- initializing one active language;
- migrating an existing GF language;
- resetting project-specific state;
- clearing generated run data;
- preserving framework code and tests;
- removing old-language project content;
- validating project completeness.

Reset and initialization operations must distinguish:

- framework assets;
- project assets;
- generated assets;
- local environment state.

---

## 6.23 Documentation and anti-drift controls

GF Wordbench includes normative documentation and anti-drift controls.

These controls may cover:

- interfile contracts;
- external-tool contracts;
- persisted schemas;
- module dependencies;
- category and lincat contracts;
- language architecture;
- validation specifications;
- release criteria;
- decision records;
- status ledgers.

Documentation is part of the project contract where implementation or validation depends on it.

Documentation is not a substitute for executable tests where automation is possible.

---

## 6.24 Framework tests

GF Wordbench includes tests for its own implementation.

Testing may include:

- unit tests;
- contract tests;
- schema tests;
- migration tests;
- process-runner tests;
- scanner tests;
- classifier tests;
- report tests;
- scenario-runner tests;
- CLI smoke tests;
- GUI-independent application tests;
- optional integration tests using a real GF installation.

Tests must not require a developer’s undocumented global environment.

---

## 6.25 Automation and CI

GF Wordbench may run in local automation and continuous integration.

Automation may:

- install or locate GF;
- validate schemas;
- run framework tests;
- run project validation;
- enforce release gates;
- publish run artifacts.

CI integration does not turn GF Wordbench into a general CI platform.

The external CI system remains responsible for job scheduling, agents, secrets, and repository events.

---

# 7. Explicit non-goals

## 7.1 Multiple active languages in parallel

GF Wordbench is not a multi-project language dashboard.

It does not need to:

- load several active project configurations simultaneously;
- switch languages dynamically inside one run;
- compare unrelated languages as peers;
- maintain one shared run history for many active languages;
- provide a language registry;
- orchestrate cross-language releases.

A new language is handled by:

- creating or duplicating a clean GF Wordbench project;
- resetting project-specific content;
- initializing the new active language.

Cross-language research files may exist outside the active project, but they are not simultaneous active-project state.

---

## 7.2 Replacement for Grammatical Framework

GF Wordbench is not a replacement implementation of GF.

It must not implement:

- a GF lexer or parser intended to replace GF;
- a GF type checker;
- a GF dependency resolver;
- a GF compiler;
- a PGF compiler or runtime;
- GF parse or generation algorithms;
- a competing GF shell;
- undocumented reverse engineering of GF internals as a normal execution path.

Small source-aware scanners are permitted only as bounded heuristics.

---

## 7.3 Universal language-development framework

GF Wordbench is designed specifically around GF projects.

It is not intended to validate arbitrary programming languages, grammar frameworks, compilers, or natural-language platforms.

Generic process helpers may be reusable internally, but product requirements must remain driven by GF language development.

---

## 7.4 Linguistic truth oracle

GF Wordbench cannot independently prove that a grammar is linguistically complete or universally correct.

It can prove only that declared validations pass.

It does not replace:

- native-speaker review;
- linguistic analysis;
- corpus evaluation;
- domain-specific acceptance;
- expert review of ambiguous constructions;
- project decisions about acceptable variation.

A passing release means the project’s documented release contract passed.

It does not mean that no linguistic defect exists.

---

## 7.5 Autonomous language implementation

GF Wordbench is not an autonomous code generator or repair agent.

It does not need to:

- design a language grammar automatically;
- modify GF sources without explicit user action;
- accept AI-generated patches automatically;
- infer final linguistic policy from examples alone;
- resolve open research questions;
- replace maintainers’ decisions.

AI-assisted workflows may consume reports and propose changes.

Source modification remains outside normal validation execution and under maintainer control.

---

## 7.6 Integrated development environment

GF Wordbench is not a full IDE.

It does not need to provide:

- a general source-code editor;
- semantic code completion;
- project-wide refactoring;
- integrated Git history;
- debugger breakpoints inside GF;
- terminal emulation;
- arbitrary editor extensions.

It may open files, reports, or external tools as a convenience.

Dedicated editors remain responsible for source editing.

---

## 7.7 Version-control system

GF Wordbench is not a replacement for Git or another version-control system.

It does not own:

- branches;
- commits;
- merges;
- conflict resolution;
- source history;
- repository hosting;
- pull-request review.

Run comparisons are validation comparisons, not source-control diffs.

GF Wordbench may record commit metadata when available, but Git remains authoritative.

---

## 7.8 General build system

GF Wordbench is not a universal build orchestrator.

It should not become responsible for unrelated:

- application builds;
- website generation;
- documentation-site deployment;
- package publication;
- installer creation;
- arbitrary shell pipelines.

It may execute external steps only when they are directly required to validate or release the active GF language project.

---

## 7.9 General task runner

GF Wordbench is not a wrapper for arbitrary commands.

An external tool may be integrated only when:

- it provides a missing GF-project validation capability;
- its inputs and outputs are documented;
- its failure semantics are understood;
- its security boundary is defined;
- it has tests;
- it receives an external-tool contract.

Convenience alone is not sufficient justification.

---

## 7.10 Plugin marketplace or unconstrained plugin framework

GF Wordbench does not require:

- runtime plugin discovery;
- third-party plugin installation;
- a plugin marketplace;
- arbitrary code loading;
- dynamic dependency injection across all components;
- user-defined executable extensions without contracts.

A small explicit extension interface may be introduced when at least two real use cases require the same stable boundary.

Extension mechanisms must remain narrower than the core product.

---

## 7.11 Cloud service

GF Wordbench is not initially a hosted service.

It does not require:

- user accounts;
- remote project storage;
- central telemetry;
- subscription management;
- distributed workers;
- browser-based execution;
- multi-tenant isolation;
- cloud databases;
- remote secrets management.

Local-first execution is the baseline.

Remote automation may invoke the CLI in an existing CI environment.

---

## 7.12 Distributed execution

GF Wordbench does not need to distribute one validation run across machines.

Parallel local execution may be considered when safe and useful.

Distributed coordination, worker queues, remote caching, and cluster scheduling are outside the core product.

---

## 7.13 Package manager

GF Wordbench is not a GF package manager.

It does not need to:

- publish GF packages;
- resolve arbitrary dependency versions;
- download RGL releases automatically;
- maintain a global language-package registry;
- replace installation instructions.

It may verify required paths and versions.

Dependency acquisition remains an environment or project-setup responsibility unless a narrow installer is later justified.

---

## 7.14 Corpus-management system

GF Wordbench is not a corpus database.

It does not need to provide:

- large-scale corpus ingestion;
- annotation interfaces;
- corpus search;
- translation memory;
- terminology databases;
- lexical database editing;
- dataset licensing workflows.

Small project-owned input files used by validation scenarios are in scope.

---

## 7.15 Translation product

GF Wordbench is not an end-user translation application.

It does not need to provide:

- translation workflows;
- interactive multilingual chat;
- production translation APIs;
- terminology management;
- user-facing language selection;
- document translation.

Parse and linearization operations exist for validation of a GF project.

---

## 7.16 Performance benchmarking platform

GF Wordbench may record durations and detect timeouts.

It is not primarily a statistical benchmarking suite.

It does not need to provide:

- microbenchmark harnesses;
- hardware-normalized performance scores;
- distributed benchmark databases;
- profiler integration;
- formal performance regression analysis.

Performance gates may be added only where a real project requirement defines stable measurement conditions.

---

## 7.17 Security sandbox

GF Wordbench is not a complete sandbox for untrusted code.

GF modules and `.gfs` scenarios may cause external-tool execution and resource use.

The framework should validate paths, avoid unsafe shell construction, and restrict known dangerous behavior.

It cannot guarantee hostile-project isolation.

Untrusted projects should be executed inside an operating-system or container sandbox managed outside GF Wordbench.

---

## 7.18 Secret manager

GF Wordbench does not manage secrets.

It must avoid persisting secrets and must not dump complete environments.

If external automation requires credentials, the automation platform remains responsible for secure injection and storage.

---

## 7.19 Automatic gold acceptance

GF Wordbench does not automatically decide that new output is correct.

Gold updates require explicit maintainer action.

A changed output may represent:

- an intended improvement;
- an unintended regression;
- an environment difference;
- a normalization defect;
- an incompatible GF-version change.

The tool may show the difference.

The maintainer decides whether to accept it.

---

## 7.20 Automatic source mutation during validation

Normal validation must not:

- format source files;
- rewrite module imports;
- rename symbols;
- patch errors;
- update project configuration;
- delete stale files;
- rewrite scenarios;
- rewrite gold files.

Separate explicit maintenance commands may be introduced with previews, backups, and contracts.

---

## 7.21 Human reports as APIs

Human-readable reports are not stable machine APIs.

External automation must consume:

- `summary.json`;
- `manifest.json`;
- versioned structured schemas.

Automation must not depend on Markdown wording when structured data exists.

---

## 7.22 Permanent compatibility with every historical prototype

GF Wordbench must provide deliberate migration from known predecessor formats.

It does not promise indefinite support for every undocumented experimental file ever produced.

Compatibility support must be:

- identified;
- versioned;
- tested;
- documented;
- eventually deprecable.

Raw historical evidence may remain readable by dedicated migration tools without constraining all future writers.

---

## 7.23 Duplication of project policy in framework code

The framework must not hardcode:

- active-language names;
- module suffixes;
- language-specific source directories;
- specific entrypoint names;
- language-specific known issues;
- project-specific accepted warnings;
- project-specific gold expectations;
- one language’s module architecture.

These belong to the active project.

Framework tests should use neutral fixtures unless explicitly testing migration from a historical project.

---

## 7.24 Undocumented fallbacks

GF Wordbench must not silently change semantics to make a run pass.

Examples of prohibited fallback behavior:

- omitting a failed required scenario;
- switching entrypoints after a failure;
- reducing a release run to quick mode;
- ignoring a missing PGF;
- treating unknown output as success;
- rebuilding a GF path differently in another stage;
- replacing a missing gold file with current output;
- suppressing a timeout.

Fallbacks may exist only when explicit, visible, documented, and compatible with the selected validation mode.

---

# 8. Deferred capabilities

The following are neither required core features nor permanently prohibited.

They may be added when justified by real use:

- safe local parallel compilation;
- Graphviz dependency visualization;
- additional PGF runtime checks;
- bounded coverage measurements;
- structured source-index generation;
- editor-launch integration;
- richer GUI dashboards;
- reusable project-template packs;
- export of signed release evidence;
- optional archive creation;
- performance gates for stable project cases;
- platform support beyond the tested baseline.

A deferred capability must satisfy the extension criteria below.

---

# 9. Extension acceptance criteria

A proposed capability belongs in GF Wordbench only when all applicable questions can be answered positively.

## 9.1 Problem evidence

- Does the capability solve a demonstrated GF-language development or validation problem?
- Has the problem occurred in a real project?
- Is the problem likely to recur?
- Is the capability more than convenience duplication?

## 9.2 Ownership

- Is one component clearly responsible?
- Are inputs and outputs explicit?
- Are failure semantics defined?
- Are persisted effects versioned?
- Are external-tool boundaries documented?

## 9.3 Reuse

- Does the capability apply beyond one isolated language-specific workaround?
- Can project-specific policy remain outside framework code?
- Is a general framework implementation smaller and safer than repeated local scripts?

## 9.4 Testability

- Can the behavior be tested without relying on one developer’s machine?
- Can success and failure be represented structurally?
- Can evidence be preserved?
- Can compatibility be validated?

## 9.5 Complexity balance

- Is the capability simpler than the problem it solves?
- Does it avoid a new abstraction layer where a configuration field or explicit function is sufficient?
- Does it avoid runtime plugins unless truly necessary?
- Does it preserve the core execution flow?

## 9.6 Security

- Are paths and inputs validated?
- Is shell execution avoided or explicitly controlled?
- Are output and runtime limits defined?
- Are untrusted inputs treated appropriately?

A proposal failing these criteria should remain project-local, external, or deferred.

---

# 10. Platform scope

GF Wordbench is local-first and Python-based.

The final architecture should avoid unnecessary platform dependence.

Portable behavior includes:

- structured subprocess invocation;
- explicit working directories;
- normalized persisted paths;
- UTF-8 text;
- LF canonical output;
- Windows and POSIX path acceptance at input boundaries;
- platform-neutral result schemas.

Windows is a primary execution environment and requires first-class support for:

- `gf.exe`;
- drive-letter paths;
- launcher scripts;
- path separators;
- process termination;
- GUI execution.

Other platforms may be supported when:

- GF is available;
- process behavior is tested;
- path behavior is validated;
- launchers or installation documentation exist.

A platform is considered supported only when it has explicit tests or documented release evidence.

---

# 11. Product-layer boundaries

## 11.1 Framework layer

The framework layer owns:

```text
app/
tests/
docs/
templates/
```

It contains:

- orchestration;
- generic GF integration;
- result models;
- schema handling;
- diagnostics;
- reports;
- CLI and GUI;
- clean project templates.

It must not contain active-language assumptions.

## 11.2 Active-project layer

The active-project layer owns:

```text
project/project.toml
project/docs/
project/validation/
active language sources
```

It contains:

- language identity;
- module architecture;
- category and lincat contracts;
- morphology and syntax policy;
- scenarios;
- inputs;
- gold expectations;
- release criteria;
- known issues;
- project decisions.

## 11.3 Generated-run layer

The generated-run layer contains:

```text
run_<run-id>/
```

It contains:

- raw evidence;
- normalized evidence;
- summaries;
- details;
- manifests;
- generated GF artifacts.

Generated-run content is disposable as project input but valuable as evidence.

It must not become the authoritative location for active project configuration.

## 11.4 Environment layer

The environment layer includes:

- GF installation;
- RGL checkout or installation;
- Python environment;
- operating system;
- CI agent;
- local output location.

GF Wordbench validates and records the resolved environment.

It does not own external installation internals.

---

# 12. Validation outcome boundary

GF Wordbench reports whether the declared validation contract passed.

A successful release result means:

- required configuration was valid;
- required GF tool capabilities were available;
- required source selections were evaluated;
- required compilation targets succeeded;
- required entrypoints succeeded;
- required PGF artifacts were produced when configured;
- required scenarios completed;
- required assertions passed;
- required gold comparisons matched;
- required artifacts were preserved;
- schema and manifest checks passed;
- no release-blocking known issue remained;
- the run satisfied the active project’s release criteria.

It does not mean:

- every possible GF tree was tested;
- every sentence in the language is handled;
- no linguistic error exists;
- the grammar is optimal;
- every external application will accept the PGF;
- all future GF versions will behave identically.

---

# 13. Final-product completion criteria

GF Wordbench reaches its intended final product scope when the following capabilities are implemented and documented.

## 13.1 Framework foundation

- one canonical application identity;
- one validated configuration pipeline;
- one active-project loader;
- one run-path builder;
- one process-execution layer;
- one structured result vocabulary.

## 13.2 GF execution

- GF version probing;
- module compilation;
- checkpoint compilation;
- entrypoint compilation;
- PGF construction;
- native `.gfs` execution;
- raw evidence capture;
- timeout and termination handling.

## 13.3 Validation

- deterministic file selection;
- static scanning;
- scenario markers;
- assertions;
- output normalization;
- gold comparison;
- direct/downstream classification;
- previous-run comparison;
- release gates.

## 13.4 Persistence

- versioned `project.toml`;
- versioned application state;
- versioned `summary.json`;
- versioned `manifest.json`;
- normalized scenario output format;
- gold format;
- tested legacy migration.

## 13.5 Interfaces

- complete CLI;
- optional but production-ready GUI;
- meaningful exit codes;
- progress and error reporting;
- artifact discovery.

## 13.6 Reports

- machine summary;
- human summary;
- AI-ready report;
- raw logs;
- top errors;
- artifact manifest.

## 13.7 Project lifecycle

- clean template;
- project initialization;
- existing-language migration;
- project reset;
- generated-output cleanup;
- completion checklist.

## 13.8 Quality

- unit tests;
- contract tests;
- schema tests;
- migration tests;
- scenario-runner tests;
- integration tests with supported GF versions;
- release process;
- compatibility policy;
- anti-drift validation.

---

# 14. Relationship to other normative documents

This document owns the overall product boundary.

Detailed contracts belong to the following documents.

| Topic | Authoritative document |
|---|---|
| Python and framework file boundaries | `INTERFILE_CONTRACT_LOCK.md` |
| External executables and GF process behavior | `EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted JSON, TOML, gold, output, and artifact schemas | `PERSISTED_SCHEMA_LOCK.md` |
| Active GF project file relationships | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Product description | `PRODUCT_OVERVIEW.md` |
| Repository organization | `REPOSITORY_STRUCTURE.md` |
| Framework components | `architecture/COMPONENT_MAP.md` |
| Execution order | `architecture/EXECUTION_FLOW.md` |
| Validation stages | `validation/VALIDATION_PIPELINE.md` |
| Validation modes | `validation/VALIDATION_MODES.md` |
| Scenarios | `scenarios/SCENARIO_FORMAT.md` |
| Diagnostics | `diagnostics/DIAGNOSTIC_OVERVIEW.md` |
| Configuration | `configuration/CONFIGURATION_OVERVIEW.md` |
| Project lifecycle | `projects/PROJECT_MODEL.md` |
| Release requirements | `validation/RELEASE_GATES.md` |
| Architectural decisions | `decisions/` |

Detailed documents may refine this scope.

They must not silently expand it.

---

# 15. Scope-change policy

A scope change is architectural.

It must not be introduced only through code.

A proposed scope change requires:

```text
[ ] Problem statement
[ ] Demonstrated use case
[ ] In-scope or non-goal section affected
[ ] Authority boundary reviewed
[ ] Project/framework ownership reviewed
[ ] External-tool impact reviewed
[ ] Persisted-schema impact reviewed
[ ] Security impact reviewed
[ ] Test strategy defined
[ ] Migration or compatibility impact defined
[ ] Relevant ADR created or updated
[ ] This document updated
```

A scope change that introduces:

- multiple active projects;
- a replacement GF engine;
- arbitrary plugins;
- cloud multi-tenancy;
- automatic source mutation;
- undocumented command execution;

requires an explicit major architectural decision.

---

# 16. Anti-drift decision rule

When deciding where a proposed feature belongs, use this order:

1. **Does GF already provide the semantic capability?**  
   Integrate GF; do not reimplement it.

2. **Is the behavior specific to one active language project?**  
   Put it in `project/`.

3. **Is it generated evidence from one run?**  
   Put it in the run directory.

4. **Is it local environment preference?**  
   Put it in application state or environment configuration.

5. **Is it reusable orchestration or validation logic for GF projects?**  
   Put it in the framework.

6. **Is it unrelated to GF language development or validation?**  
   Keep it outside GF Wordbench.

7. **Does it require a broad abstraction for only one current use case?**  
   Keep the implementation explicit until reuse is demonstrated.

---

# 17. Final scope statement

GF Wordbench is:

> A local-first, reproducible, evidence-preserving development and validation workbench for one active GF language project.

It combines:

```text
GF-native execution
+ project-defined validation
+ deterministic orchestration
+ regression evidence
+ anti-drift contracts
+ final release gates
```

It is deliberately not:

```text
a replacement for GF
a multi-language management platform
a universal build system
an autonomous grammar author
a general IDE
a cloud service
an unconstrained plugin host
```

Complexity is accepted when it protects a real, recurring project contract.

Complexity is rejected when it duplicates GF, hides project policy, weakens evidence, or introduces infrastructure without a demonstrated validation need.
