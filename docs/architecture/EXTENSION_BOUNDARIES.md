# GF Wordbench — Extension Boundaries

**Document ID:** `GF-WB-ARCH-EXTENSION-BOUNDARIES`  
**Status:** Normative  
**Applies to:** GF Wordbench framework, active language project, project template, validation assets, reports, and supported external-tool integrations  
**Owner:** GF Wordbench maintainers  
**Architecture version:** `1.0.0`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines where GF Wordbench may be extended, how each extension must integrate, and which architectural boundaries must remain closed.

GF Wordbench must remain adaptable without becoming an unbounded plugin platform or a generic workflow engine. Extension is therefore permitted only through explicit, documented seams that preserve:

- one active GF language project per GF Wordbench copy;
- deterministic validation;
- typed and structured results;
- immutable raw evidence;
- stable artifact ownership;
- versioned persisted schemas;
- identical CLI and GUI semantics;
- GF as the language-execution engine;
- Python as the orchestration, evidence, classification, comparison, and reporting layer;
- backward compatibility or explicit migration;
- contract-test coverage.

The central rule is:

> Extend GF Wordbench through an owned boundary, never by bypassing ownership or creating a parallel execution path.

---

## 2. Scope

This document governs extensions to:

- the active language project;
- project configuration;
- file selection;
- static scan rules;
- compilation validation;
- GF diagnostic parsing;
- failure classification;
- validation stages;
- `.gfs` scenarios;
- scenario markers and assertions;
- output normalization;
- gold comparison;
- result models;
- reports;
- artifact manifests;
- CLI and GUI surfaces;
- state handling;
- external tools;
- automation and CI;
- project templates.

This document also identifies architecture that is intentionally not extensible.

---

## 3. Related normative documents

The following documents own adjacent contracts:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Responsibility is divided as follows:

| Document | Owns |
|---|---|
| `INTERFILE_CONTRACT_LOCK.md` | Python-to-Python and framework file contracts |
| `EXTERNAL_TOOL_CONTRACT_LOCK.md` | GF, operating-system, process, shell, and optional external-tool boundaries |
| `PERSISTED_SCHEMA_LOCK.md` | Persistent configuration, state, summaries, manifests, outputs, and gold schemas |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | Active language GF module, scenario, gold, input, and artifact contracts |
| `EXTENSION_BOUNDARIES.md` | Authorized extension seams and the rules for using them |

This document does not duplicate field-level schemas or command-level contracts. It defines where a new capability belongs.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented reason justifies an exception.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **EXTENSION POINT**: an approved boundary through which new behavior may be added.
- **EXTENSION OWNER**: the component responsible for the extension point.
- **EXTENSION IMPLEMENTATION**: code or project data added through an extension point.
- **CORE PATH**: the normal execution path shared by CLI, GUI, tests, and automation.
- **BYPASS**: an alternate path that avoids an owner, validator, model, or contract.
- **REGISTRATION**: explicit declaration that makes an extension discoverable.
- **DYNAMIC PLUGIN**: code loaded at runtime from arbitrary or externally supplied modules.
- **COMPATIBLE EXTENSION**: additive behavior that preserves all existing contracts.
- **BREAKING EXTENSION**: behavior requiring a contract, schema, command, or migration change.
- **PROJECT EXTENSION**: language-specific behavior kept under `project/`.
- **FRAMEWORK EXTENSION**: language-neutral behavior implemented under `app/`.

---

## 5. Extension philosophy

### 5.1 Explicit before generic

GF Wordbench MUST prefer a small explicit registry or direct orchestration call over:

- runtime plugin discovery;
- dependency-injection containers;
- event buses;
- generic hook systems;
- generic workflow-definition languages;
- reflection-driven execution;
- implicit import side effects.

A general extension mechanism may be introduced only when at least two real, stable use cases require the same abstraction and an ADR approves the design.

### 5.2 Language-specific behavior belongs to the project

Language-specific modules, paths, scenarios, expectations, morphology checks, and linguistic policy MUST remain under:

```text
project/
```

The framework MUST NOT contain language-specific module names, language suffixes, lexical assumptions, or hard-coded source directories.

### 5.3 The framework owns orchestration

The active project may declare what to validate, but it MUST NOT replace:

- process execution;
- timeout handling;
- raw evidence capture;
- status semantics;
- result serialization;
- report ownership;
- manifest generation;
- release-status calculation.

### 5.4 GF remains authoritative for GF semantics

An extension MUST use GF for operations such as:

- module loading;
- compilation;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology or grammar introspection;
- missing-function inspection.

Python MUST NOT reimplement GF language semantics merely to simplify an extension.

### 5.5 Additive by default

Extensions SHOULD be additive.

An extension SHOULD NOT change existing behavior unless:

- the change fixes incorrect behavior;
- the old behavior is deprecated;
- a migration is provided;
- the relevant contract and schema versions are updated;
- tests cover old and new behavior where compatibility is promised.

---

## 6. Boundary model

GF Wordbench uses the following layers:

```text
User surfaces
    CLI
    GUI
    automation

Configuration
    application defaults
    environment configuration
    project/project.toml
    application state

Orchestration
    bootstrap
    audit core
    mode policy
    release policy

Validation stages
    file selection
    static scanning
    compilation
    scenarios
    PGF build
    regression comparison

Infrastructure
    process execution
    path handling
    filesystem I/O
    logging

Interpretation
    diagnostic parsing
    causal classification
    result construction

Presentation
    JSON report
    Markdown report
    AI-ready report
    logs
    details
    manifest

Active project
    GF sources
    scenarios
    inputs
    gold files
    project documents
```

Allowed dependency flow:

```text
CLI / GUI / automation
    → bootstrap
    → audit core
    → validation stages
    → infrastructure
    → external tools

validation stages
    → shared models
    → diagnostic parsing
    → result construction

audit core
    → classification
    → regression comparison
    → report writers

report writers
    → structured results
    → owned artifacts

active project
    → project loader
    → audit policy and scenario registry
```

An extension MUST preserve this direction.

---

## 7. Extension maturity states

Every framework extension with a public contract SHOULD have one state:

| State | Meaning |
|---|---|
| `experimental` | Available for development; contract may change; excluded from release requirements unless explicitly enabled |
| `active` | Supported and covered by contract tests |
| `deprecated` | Still supported temporarily; replacement and removal plan documented |
| `retired` | No longer active; identifier retained in history and MUST NOT be reused |

Project scenarios may use:

| State | Meaning |
|---|---|
| `required` | Must execute and pass for the modes that include it |
| `optional` | Executes when selected; failure remains visible but release policy decides whether it blocks |
| `disabled` | Registered but intentionally not executed; reason documented |
| `retired` | Removed from active execution; ID retained in project history |

Extension states MUST NOT be inferred from filenames or directory location alone.

---

# 8. Approved extension points

## 8.1 Active language project

**Owner**

```text
project/project.toml
project/
```

**Permitted extensions**

- adding or changing GF source modules;
- declaring entrypoints and checkpoints;
- adding language-specific scenarios;
- adding scenario inputs;
- adding or updating reviewed gold files;
- defining project release requirements;
- documenting language architecture and module contracts;
- registering optional language-specific validation coverage.

**Required integration**

- project configuration validation;
- module-to-module contract update;
- dependency-map update;
- scenario and gold review;
- checkpoint compilation;
- release-level validation when applicable.

**Forbidden**

- importing project Python code into the framework;
- placing project-specific defaults in `app/config.py`;
- writing project identity into GUI state as the authoritative source;
- changing framework status semantics from project configuration;
- letting project files select arbitrary Python callables;
- supporting multiple active language profiles in one project file.

The active project is a data-and-GF extension boundary, not a Python plugin boundary.

---

## 8.2 Project template

**Owner**

```text
templates/project/
```

**Permitted extensions**

- adding required project files;
- adding placeholders for new project-level contracts;
- adding generic scenario or documentation templates;
- adding safe default configuration fields.

**Required integration**

A template change MUST be reviewed against:

```text
project/
docs/projects/
docs/configuration/
docs/PERSISTED_SCHEMA_LOCK.md
```

**Forbidden**

- embedding the active language’s identity or linguistic content;
- introducing template fields not understood by the project loader;
- allowing the active project and template structures to drift silently.

The template SHOULD mirror the required project structure while keeping all language-specific values as explicit placeholders.

---

## 8.3 Project configuration fields

**Owner**

```text
app/project_config.py
project/project.toml
```

or the final designated project loader and schema.

**Permitted extension**

A new project field MAY be added when it represents a stable project concern such as:

- source selection;
- entrypoints;
- checkpoints;
- GF path parts;
- scenario registration;
- release targets;
- project identity;
- validation policy.

**Requirements**

- one authoritative field definition;
- type validation;
- explicit default or required status;
- canonical TOML example;
- `ProjectConfig` model update;
- bootstrap integration;
- persisted-schema version review;
- configuration tests;
- migration behavior where required.

**Forbidden**

- arbitrary key/value bags consumed differently by separate modules;
- hidden fields interpreted only by GUI or CLI;
- executable Python references;
- absolute machine-specific paths for project-owned files;
- secrets;
- transient UI state.

A configuration field is not an extension point until the loader, model, documentation, and tests recognize it.

---

## 8.4 Application defaults

**Owner**

```text
app/config.py
```

**Permitted extension**

- adding language-neutral framework defaults;
- adding canonical filenames;
- adding safe timeout or retention defaults;
- adding supported mode-independent behavior flags.

**Requirements**

- default must be platform-safe or explicitly platform-scoped;
- default must not identify the active language;
- CLI and GUI must resolve the same default through bootstrap;
- a persisted value must follow the schema lock.

**Forbidden**

- active-project module names;
- active-project source paths;
- developer-specific absolute paths;
- duplicate constants owned by `RunPaths` or another component;
- default values that silently change release semantics.

---

## 8.5 Validation modes

**Owner**

```text
app/bootstrap.py
app/audit/audit_core.py
```

and the designated mode-policy implementation.

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

**Permitted extension**

A new mode MAY be proposed only when it defines a stable, reusable selection of existing validation capabilities that cannot be expressed safely as an option to an existing mode.

**Requirements**

- clear purpose and non-goals;
- stage inclusion policy;
- required/optional stage semantics;
- CLI and GUI parity;
- exit-code behavior;
- report representation;
- persisted summary representation;
- backward-compatibility analysis;
- ADR approval;
- contract tests.

**Forbidden**

- a mode implemented only in CLI or only in GUI;
- a mode that invokes a separate audit engine;
- aliases treated as new canonical modes;
- language-specific modes in framework code;
- a mode whose behavior depends on undocumented environment state.

Historical aliases such as `file` and `all` may be read for migration but MUST NOT be emitted as canonical modes.

---

## 8.6 Validation pipeline stages

**Owner**

```text
app/audit/audit_core.py
```

**Permitted extension**

A new validation stage MAY be added when it produces distinct evidence or a distinct release criterion that does not belong inside an existing stage.

Examples:

- PGF build validation;
- scenario validation;
- artifact-integrity validation;
- project-contract validation.

**Stage contract**

Each stage MUST define:

```text
stage_id
purpose
owner module
input models
output models
required configuration
owned artifacts
status mapping
execution-state mapping
error behavior
ordering constraints
mode inclusion
tests
```

**Stage implementation rules**

- accept explicit typed inputs;
- return structured results;
- preserve raw evidence before interpretation;
- use `RunPaths` for run-owned paths;
- avoid writing another stage’s artifacts;
- avoid directly rendering user-facing reports;
- be deterministic for equivalent input and environment;
- expose cancellation or timeout distinctly where applicable;
- leave the current run structurally valid after recoverable failure.

**Registration**

The canonical pipeline SHOULD use one explicit ordered registry or an equally explicit orchestration sequence.

Example conceptual structure:

```python
VALIDATION_STAGES = (
    "select",
    "scan",
    "compile",
    "scenario",
    "pgf",
    "compare",
)
```

This example does not require a plugin API. The real registry, if used, MUST contain known framework stages rather than dynamically imported project code.

**Forbidden**

- stage discovery through arbitrary installed packages;
- stage activation through import side effects;
- report writers acting as validation stages;
- stages reparsing another stage’s human report;
- stages launching external tools without the common process layer;
- stages mutating gold files during normal validation;
- stage-local definitions of global status semantics.

---

## 8.7 File-selection policies

**Owner**

```text
app/audit/file_selector.py
```

**Permitted extension**

- additional language-neutral include/exclude rules;
- checkpoint-aware selection;
- deterministic source grouping;
- explicit project-configured source roots;
- additional safe file metadata.

**Requirements**

- selection remains deterministic;
- every exclusion has a structured reason;
- paths remain project-relative in canonical results;
- project-root containment is enforced;
- selection does not read generated run output as source;
- maximum-file limits are applied predictably;
- mode policy remains outside low-level enumeration where possible.

**Forbidden**

- compile attempts during discovery;
- linguistic inference from filename content;
- hidden global ignore files;
- scanning outside configured roots without explicit authorization;
- nondeterministic filesystem order.

---

## 8.8 Static scan rules

**Owner**

```text
app/audit/scanner.py
```

or a future language-neutral scan-rule package owned by the scanner.

**Permitted extension**

A new static scan rule MAY be added when it detects a source-level condition without requiring GF execution.

Each rule MUST define:

```text
rule_id
title
purpose
scope
severity
input representation
false-positive constraints
finding fields
normalization behavior
tests
```

**Rule behavior**

A scan rule SHOULD be a deterministic pure analysis over normalized source text and structural masks.

A finding SHOULD include:

```text
rule_id
file_path
line
column when available
message
evidence excerpt
severity
```

**Registration**

Rules MAY be held in an explicit scanner-owned registry.

The registry MUST:

- use stable rule identifiers;
- preserve deterministic order;
- reject duplicate identifiers;
- expose enabled rules in run evidence;
- remain language-neutral unless the rule is project-declared data interpreted by a documented framework feature.

**Forbidden**

- calling GF from a static rule;
- writing reports directly;
- classifying interfile causal relationships;
- editing source files;
- silently changing an existing rule’s meaning under the same ID;
- using regex directly on comments or string literals when the rule claims structural GF analysis;
- loading arbitrary project Python code as a scan rule.

A rule-meaning change requires fixture review and may require a rule-version or identifier change.

---

## 8.9 GF compilation validation

**Owner**

```text
app/audit/compiler.py
```

**Permitted extension**

- additional supported compile targets;
- explicit compilation policies;
- additional captured metadata;
- version-gated command construction;
- artifact verification.

**Requirements**

- use the common process runner;
- use the common GF path resolver;
- preserve stdout and stderr;
- record or reconstruct the exact command;
- distinguish success, validation failure, launch failure, timeout, and skipped execution;
- return structured compile data;
- leave causal classification to the classifier.

**Forbidden**

- adding language-specific command behavior in the compiler;
- invoking reports;
- invoking GUI code;
- classifying a result as downstream;
- interpreting zero exit code as proof that every required artifact exists;
- bypassing external-tool contract review.

---

## 8.10 GF diagnostic parsers

**Owner**

```text
app/audit/diagnostics.py
```

or the final designated diagnostic-normalization module.

**Permitted extension**

A new parser rule MAY recognize:

- a new GF diagnostic family;
- a GF-version-specific diagnostic form;
- an additional structured source location;
- an artifact or process contract failure;
- an unsupported-version signal.

Each parser rule MUST define:

```text
diagnostic_rule_id
source stream
recognition pattern
priority
normalized kind
captured fields
version applicability
fallback behavior
fixtures
```

**Parsing rules**

- raw output remains authoritative evidence;
- parser order is deterministic;
- specific patterns precede generic fallbacks;
- unmatched diagnostics remain visible as `OTHER` or the canonical fallback;
- a parser MUST NOT erase unrecognized lines;
- parser failure MUST NOT destroy compile or scenario evidence;
- output wording changes across GF versions require compatibility fixtures.

**Forbidden**

- assigning `direct`, `downstream`, or `ambiguous`;
- launching GF;
- reading Markdown reports;
- changing global validation status independently;
- hiding a GF error because no parser recognized it;
- relying on only stdout or only stderr without documented command behavior.

---

## 8.11 Failure classifiers

**Owner**

```text
app/audit/classifier.py
```

**Permitted extension**

- new evidence-based causal rules;
- better blocker resolution;
- additional ambiguity handling;
- project dependency data used through a documented model.

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

**Requirements**

- consume structured results and dependency evidence;
- preserve the original error kind;
- never alter raw tool output;
- provide deterministic classification;
- record blockers when known;
- prefer `ambiguous` over unsupported certainty;
- include tests for ordering and multi-failure cases.

**Forbidden**

- launching processes;
- scanning files independently;
- writing reports;
- redefining validation status;
- assigning a root cause solely from processing order;
- treating every non-zero result as direct.

Technical execution failures belong to execution state or error kind, not causal classification.

---

## 8.12 Scenario types

**Owner**

```text
app/audit/scenario_runner.py
project/validation/scenarios/
```

**Permitted extension**

New scenarios may validate:

- module loading;
- missing functions;
- linearization;
- parsing;
- bounded generation;
- morphology;
- grammar introspection;
- PGF behavior;
- language-specific regression cases.

**Scenario registration**

Every scenario MUST have:

```text
scenario_id
script path
required or optional status
applicable modes
timeout policy
entrypoint or target
assertion strategy
gold path when applicable
normalization version
```

**Requirements**

- use native `.gfs` scripts;
- execute through GF;
- use stable markers or another documented completion protocol;
- preserve raw output;
- normalize only after raw capture;
- produce `ScenarioResult`;
- keep scenario IDs stable;
- use deterministic execution order;
- make random or unbounded operations unsuitable for exact gold comparison unless constrained.

**Forbidden**

- Python reimplementation of the GF shell;
- arbitrary Python callbacks declared by project configuration;
- scenario-specific process runners;
- unregistered scenarios influencing release status;
- normal runs rewriting gold;
- successful exit code being the only completion assertion;
- shell escape or operating-system execution unless explicitly authorized by external-tool policy.

---

## 8.13 Scenario markers and assertions

**Owner**

```text
app/audit/scenario_runner.py
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

**Permitted extension**

New assertion types MAY be added for stable, machine-verifiable conditions such as:

- required marker observed;
- section completed;
- output contains or excludes a stable token;
- normalized output equals gold;
- artifact exists;
- parse count meets a declared condition;
- missing-function output is empty.

**Requirements**

Every assertion type MUST define:

```text
assertion_type
input source
comparison semantics
failure representation
serialization
human-report rendering
tests
```

**Forbidden**

- assertions evaluated only from rendered Markdown;
- undocumented substring conventions;
- assertions that discard contradictory raw evidence;
- language-specific Python code loaded from the project;
- treating an unknown assertion type as pass.

---

## 8.14 Output normalization rules

**Owner**

```text
app/audit/output_normalization.py
```

or the final designated normalization component.

**Permitted extension**

A normalization rule MAY remove or replace only unstable presentation noise such as:

- platform newline differences;
- approved absolute path prefixes;
- run-directory identifiers;
- non-semantic timing values;
- approved ANSI sequences;
- known tool banners when the scenario contract excludes them.

**Requirements**

- stable normalization-rule IDs;
- explicit normalization version;
- deterministic rule order;
- raw evidence retained unchanged;
- normalized output traceable to raw evidence;
- fixtures before and after normalization;
- gold review when semantics or comparison output changes.

**Forbidden**

Normalization MUST NOT remove or rewrite:

- GF error meaning;
- abstract trees;
- linearized strings;
- parse ambiguity evidence;
- missing-function lists;
- morphology output;
- Unicode distinctions relevant to the language;
- required markers;
- evidence that a section failed to execute;
- semantically meaningful punctuation or whitespace.

Normalization is not a repair mechanism and MUST NOT turn failure into success.

---

## 8.15 Gold-comparison strategies

**Owner**

```text
app/audit/gold.py
```

or the final designated scenario-comparison component.

**Permitted extension**

Supported comparison strategies MAY include:

- exact normalized text;
- normalized section equality;
- declared unordered-set comparison;
- structured count comparison;
- explicit pattern-based assertion.

**Requirements**

- strategy declared by scenario configuration;
- deterministic comparison;
- human-readable diff;
- machine-readable failure;
- missing required gold treated as failure;
- gold update performed only by an explicit operation;
- strategy identity serialized in scenario results.

**Forbidden**

- choosing a strategy from output content;
- silently accepting missing gold;
- automatic gold regeneration on mismatch;
- fuzzy comparison without explicit thresholds and tests;
- comparison against raw output when normalization is contractually required.

---

## 8.16 Result models

**Owner**

```text
app/models.py
app/audit/result_model.py
```

**Permitted extension**

- optional fields with safe defaults;
- new structured result types for approved stages;
- additive metadata required by reports or manifests;
- explicit compatibility adapters.

**Requirements**

A model extension MUST define:

```text
field name
type
required or optional
default
producer
consumers
serialization form
compatibility behavior
validation invariants
```

**Rules**

- models contain data, not orchestration;
- model construction remains centralized where designated;
- producers and consumers update together;
- serialized fields follow the schema lock;
- derived values SHOULD have one canonical computation owner;
- unknown enum values are not silently reinterpreted.

**Forbidden**

- report rendering methods in core result models;
- GUI objects in shared models;
- process handles or open streams in persisted results;
- arbitrary dictionaries where a stable typed structure exists;
- adding required persisted fields without schema review.

---

## 8.17 Report writers

**Owner**

```text
app/reports/
```

**Permitted extension**

A new report MAY be added when it serves a distinct consumer or format, for example:

- machine integration;
- human review;
- AI handoff;
- CI annotations;
- artifact inventory.

**Report contract**

Each report MUST define:

```text
report_id
consumer
input model
owned path
media type
required or optional status
stable sections or schema
failure behavior
manifest role
tests
```

**Requirements**

- consume completed structured results;
- use paths provided by `RunPaths`;
- write only owned artifacts;
- never rerun validation;
- never reclassify failures independently;
- preserve deterministic ordering;
- expose report-generation failure without invalidating already captured evidence;
- include new persistent formats in schema review.

**Forbidden**

```text
reports → compiler
reports → scanner
reports → scenario runner
reports → process runner
reports → GUI
```

A report is a projection of results, not a validation stage.

---

## 8.18 Artifact types and manifest roles

**Owner**

```text
app/artifacts.py
app/reports/manifest.py
```

or the final designated artifact and manifest owners.

**Permitted extension**

A new artifact role MAY be added for a new approved stage or report.

**Requirements**

- stable role identifier;
- producing component;
- required or optional status;
- canonical path ownership;
- media type;
- hash policy;
- retention policy;
- summary linkage;
- manifest tests.

**Forbidden**

- reconstructing artifact paths independently in consumers;
- two owners writing the same artifact;
- changing an artifact filename without schema and migration review;
- excluding required evidence from the manifest;
- modifying raw evidence after capture.

---

## 8.19 CLI commands and options

**Owner**

```text
app/main_cli.py
app/bootstrap.py
```

**Permitted extension**

- exposing an approved framework capability;
- adding an explicit maintenance command;
- adding safe overrides for documented configuration;
- adding schema, contract, or project checks.

**Requirements**

- reuse bootstrap and core services;
- preserve CLI/GUI semantic parity for shared capabilities;
- validate inputs before execution;
- use documented exit codes;
- document defaults and precedence;
- add parser and integration tests;
- avoid exposing internal-only implementation switches as stable user API.

**Forbidden**

- direct GF execution from CLI handlers;
- separate result or report models;
- hidden project mutation;
- CLI-only validation semantics;
- options that bypass project containment or security policy;
- command names that silently alias behavior with different status semantics.

---

## 8.20 GUI actions and panels

**Owner**

```text
app/main_gui.py
app/gui/
app/bootstrap.py
```

**Permitted extension**

- exposing approved configuration;
- displaying structured results;
- adding navigation to owned artifacts;
- adding explicit maintenance operations;
- adding progress presentation.

**Requirements**

- construct configuration through bootstrap;
- execute validation through the same core path as CLI;
- keep UI state disposable;
- keep worker-thread or process boundaries explicit;
- map errors from structured results;
- avoid blocking the UI during external execution;
- maintain equivalent meaning with CLI options.

**Forbidden**

- widget-level GF execution;
- widget-level command construction;
- GUI-only project configuration fields;
- GUI state becoming authoritative project configuration;
- recomputing classifications in presentation code;
- editing gold without an explicit dedicated operation.

---

## 8.21 Application state

**Owner**

```text
app/state.py
```

**Permitted extension**

State may store disposable local preferences such as:

- last selected environment paths;
- last mode;
- display preferences;
- last output location;
- recent run pointers.

**Requirements**

- safe defaults;
- atomic writes;
- schema version review;
- malformed-state recovery;
- no restoration of an active running state;
- no project authority;
- no secrets.

**Forbidden**

- active language identity as authoritative data;
- project entrypoints or scenario policy;
- result objects;
- process handles;
- credentials;
- release decisions.

Deleting state MUST leave the project valid.

---

## 8.22 External tools

**Owner**

```text
app/utils/process_utils.py
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

and a tool-specific adapter when approved.

**Permitted extension**

A new external tool MAY be integrated only when GF, the Python standard library, and existing components do not sufficiently provide the required capability.

**Required approval data**

```text
tool identity
purpose
license
supported versions
installation method
platform support
command contract
working directory
environment use
inputs
outputs
timeouts
artifacts
failure semantics
security implications
fallback behavior
tests
```

**Requirements**

- explicit adapter or command builder;
- common process layer;
- exact command evidence;
- captured stdout and stderr;
- timeout and cancellation policy;
- artifact verification;
- external-tool contract ID;
- optional behavior unless deliberately made a prerequisite;
- no hidden automatic download or installation.

**Forbidden**

- shell command strings assembled from untrusted project text;
- optional tools becoming required accidentally;
- external tools launched from reports or GUI widgets;
- different GF path rules per caller;
- silent fallback to different semantics;
- tool output replacing raw GF evidence.

---

## 8.23 Automation and CI adapters

**Owner**

```text
app/main_cli.py
docs/operations/AUTOMATION_AND_CI.md
```

**Permitted extension**

- CI wrappers;
- machine-readable annotations derived from `summary.json`;
- archive or publication steps;
- contract and schema checks;
- release-gate integration.

**Requirements**

- call supported CLI or public application services;
- consume structured artifacts;
- preserve exit-code semantics;
- avoid developer-machine assumptions;
- expose the exact GF version and project identity;
- archive raw evidence for failed release runs where policy requires it.

**Forbidden**

- parsing human Markdown when JSON exists;
- changing validation status after the run;
- bypassing required release stages;
- editing project sources or gold during ordinary CI validation;
- relying on global unrecorded environment configuration.

---

# 9. Closed boundaries

The following are intentionally not extension points.

## 9.1 Arbitrary Python project plugins

GF Wordbench MUST NOT load arbitrary Python modules from the active project.

Reasons:

- project files may be untrusted;
- execution would no longer be reproducible from configuration alone;
- language-specific code would leak into framework behavior;
- plugin compatibility would become an independent product surface;
- security and packaging complexity would increase without demonstrated need.

A future plugin system requires a separate ADR, threat model, versioned API, isolation policy, and compatibility plan.

## 9.2 Shared status semantics

The following concepts are centrally owned and MUST NOT be locally extended with undocumented values:

```text
validation status
execution state
error kind
diagnostic causal class
extension maturity state
```

New values require model, schema, report, CLI/GUI, and migration review.

## 9.3 Core process execution

External processes MUST run through the common process layer.

No extension may provide a second process runner merely to support a new stage or tool.

## 9.4 Artifact path construction

Artifact paths and filenames MUST be owned centrally through `RunPaths`, project configuration, or the designated artifact registry.

Consumers MUST NOT reconstruct filenames.

## 9.5 Raw evidence

Raw stdout, stderr, commands, exit codes, and tool-produced evidence are immutable after capture.

Extensions may derive normalized or summarized artifacts but MUST NOT replace raw evidence.

## 9.6 Release decision

One designated release-policy owner computes the final release result from structured stage results.

Individual stages, reports, GUI panels, or project scripts MUST NOT independently declare a release successful.

## 9.7 Multi-language runtime profiles

One GF Wordbench copy represents one active language project.

Runtime switching among multiple language profiles is outside the architecture.

Supporting another language means cloning or resetting the project boundary and supplying one new active project.

---

# 10. Extension package placement

New files SHOULD be placed by responsibility.

```text
app/
├── audit/
│   ├── stage implementations
│   ├── scanner rules
│   ├── diagnostic parsing
│   ├── scenario execution
│   ├── normalization
│   └── comparison
├── reports/
│   └── report writers and manifest projection
├── gui/
│   └── presentation-only components
├── utils/
│   └── language-neutral infrastructure
├── models.py
├── bootstrap.py
├── project_config.py
└── state.py

project/
├── project.toml
├── GF source tree
├── validation/
│   ├── scenarios/
│   ├── inputs/
│   └── gold/
└── docs/

templates/project/
└── generic mirror of required project structure
```

A new top-level package SHOULD NOT be created when an existing owner clearly fits the responsibility.

---

# 11. Registration rules

An extension that participates in execution MUST be explicitly registered.

A registry entry SHOULD contain only stable declarative metadata and a known framework implementation reference.

Conceptual example:

```python
StageDefinition(
    stage_id="scenario",
    implementation=run_required_scenarios,
    applicable_modes=("checkpoint", "release", "diagnostic"),
    required_for_release=True,
)
```

Registration requirements:

- stable ID;
- one owner;
- deterministic order;
- duplicate-ID rejection;
- explicit applicable modes;
- explicit required/optional semantics;
- no import-time execution;
- no project-provided Python callable;
- no hidden environment-controlled registration;
- visible representation in diagnostics or run metadata where useful.

Registration does not eliminate direct typed contracts. A registry MUST NOT become an untyped service locator.

---

# 12. Compatibility rules

## 12.1 Internal extension

An extension is internal when it changes no:

- public symbol;
- result field;
- schema;
- command;
- artifact path;
- status meaning;
- project contract;
- CLI/GUI behavior.

It requires normal tests but no compatibility migration.

## 12.2 Compatible public extension

Examples:

- optional result metadata with a safe default;
- optional report;
- optional scenario;
- optional manifest role;
- new scan rule with a new stable ID;
- new diagnostic parser preserving fallback behavior;
- new project field with a safe default.

A compatible extension MUST:

1. update its owner;
2. review all consumers;
3. add tests;
4. update documentation;
5. update the relevant lock;
6. increment a minor schema or contract version when persisted or public data changes.

## 12.3 Breaking extension

Examples:

- changing a stage order with semantic effects;
- making an optional stage required;
- renaming an ID;
- changing a model field type;
- changing artifact ownership;
- changing normalization that invalidates gold;
- changing status meaning;
- changing a command contract;
- adding required project configuration;
- changing release criteria.

A breaking extension MUST:

1. identify affected contract IDs;
2. document the reason;
3. enumerate producers and consumers;
4. define migration or deprecation;
5. update all affected files together;
6. update fixtures and gold deliberately;
7. update schema or contract major versions;
8. add compatibility tests where support is promised;
9. update changelog and migration documentation;
10. pass release-level validation.

---

# 13. Security boundaries

Extensions MUST treat the following as untrusted unless explicitly controlled:

- project paths;
- scenario files;
- scenario inputs;
- external-tool paths;
- environment variables;
- previous-run artifacts;
- imported legacy state;
- copied project templates.

Security rules:

- validate path containment;
- avoid shell interpretation;
- do not execute project Python;
- prohibit unauthorized GF shell escape behavior;
- do not persist secrets;
- do not log complete environments;
- do not auto-install external tools;
- validate schemas before use;
- write state and persistent artifacts atomically;
- reject path traversal;
- separate raw evidence from rendered output;
- preserve failure evidence.

An extension introducing a new executable or executable input requires external-tool and security review.

---

# 14. Performance boundaries

Performance work MAY change internal implementation but MUST preserve observable contracts.

Extensions SHOULD:

- avoid reading the same large source repeatedly;
- avoid recompiling solely for reports;
- avoid unbounded output capture without policy;
- preserve deterministic result ordering;
- respect per-operation timeout policy;
- keep quick mode meaningfully bounded;
- avoid global caches whose invalidation cannot be proven;
- record truncation explicitly when evidence limits apply.

A cache becomes an architectural component when another run or process depends on it. Such a cache requires ownership, invalidation, schema, and corruption policy.

---

# 15. Testing requirements

Every extension MUST have tests appropriate to its boundary.

## 15.1 Unit tests

Use unit tests for:

- configuration validation;
- registration;
- rule matching;
- parser behavior;
- classifier rules;
- normalization;
- comparison strategies;
- result construction;
- report rendering;
- path containment;
- migration helpers.

## 15.2 Contract tests

Use contract tests for:

- public signatures;
- required model fields;
- artifact ownership;
- deterministic order;
- schema round trips;
- CLI/GUI parity;
- process result semantics;
- stage registration;
- required/optional scenario behavior;
- gold immutability;
- external-tool command construction.

Recommended location:

```text
tests/contracts/
```

## 15.3 Integration tests

Use integration tests for:

- full pipeline orchestration;
- a successful fixture grammar;
- a failing fixture grammar;
- GF version probing;
- compilation;
- `.gfs` execution;
- timeout containment;
- PGF production;
- report and manifest completeness;
- previous-run comparison.

Tests requiring real GF SHOULD be separately marked so unit suites remain runnable without GF.

## 15.4 Regression fixtures

A bug fix that changes extension behavior MUST add a fixture reproducing the original failure when practical.

---

# 16. Documentation requirements

An extension is incomplete until documentation is updated.

Depending on scope, update:

```text
docs/architecture/
docs/validation/
docs/scenarios/
docs/diagnostics/
docs/reports/
docs/configuration/
docs/usage/
docs/development/
docs/operations/
docs/release/
docs/reference/
docs/decisions/
```

Minimum extension documentation:

```text
purpose
owner
public ID
inputs
outputs
side effects
failure behavior
configuration
artifacts
compatibility
security implications
tests
```

Rules MUST have one authoritative owner. Other documents SHOULD link to that owner rather than restating the full rule.

---

# 17. ADR threshold

An ADR is required when an extension:

- adds a new architectural layer;
- introduces a new required external tool;
- adds runtime plugin discovery;
- adds a new canonical validation mode;
- changes single-active-language architecture;
- introduces a database or remote service;
- changes artifact ownership;
- changes release-status computation;
- changes the persistent schema major version;
- introduces executable project code outside GF scenarios;
- replaces an established core component;
- changes dependency direction.

Small additive rules, reports, parsers, and scenarios do not require separate ADRs when they follow an existing approved boundary.

---

# 18. Anti-overengineering constraints

The final GF Wordbench architecture intentionally does not require:

- a general plugin marketplace;
- a dependency-injection framework;
- an event bus;
- a message broker;
- a database;
- a web service;
- a remote execution service;
- a generic DAG engine;
- a custom GF scripting language;
- a custom test-description language replacing `.gfs`;
- simultaneous language profiles;
- runtime discovery of third-party Python packages.

One of these may be introduced only when:

1. a concrete requirement cannot be met by the existing boundary;
2. at least two stable use cases justify a reusable abstraction;
3. operational and security costs are documented;
4. a simpler explicit design has been evaluated;
5. an ADR is accepted;
6. migration and removal strategies exist.

Complexity is acceptable when it protects a real contract or enables a real capability. Complexity is not acceptable merely to anticipate unspecified future use.

---

# 19. Extension review checklist

Use this checklist for every extension.

```text
[ ] Extension purpose is concrete
[ ] Existing owner cannot already provide the capability cleanly
[ ] Extension point is identified
[ ] Extension owner is identified
[ ] Framework or project placement is correct
[ ] Stable extension ID is assigned
[ ] Inputs and outputs are typed or schema-defined
[ ] Required and optional behavior is explicit
[ ] Applicable validation modes are explicit
[ ] Status, execution state, error kind, and causal class remain distinct
[ ] Artifact ownership is explicit
[ ] Raw evidence remains immutable
[ ] Process execution uses the common runner
[ ] GF semantics remain delegated to GF
[ ] Project Python execution is not introduced
[ ] Path containment is validated
[ ] Deterministic ordering is preserved
[ ] CLI and GUI semantics are aligned
[ ] Persisted-schema impact is reviewed
[ ] External-tool impact is reviewed
[ ] Security impact is reviewed
[ ] Compatibility classification is recorded
[ ] Migration or deprecation is defined when needed
[ ] Unit tests are added
[ ] Contract tests are added
[ ] Integration tests are added where appropriate
[ ] Documentation owner is updated
[ ] Relevant lock files are updated
[ ] ADR added when threshold is met
[ ] Release validation passes
```

---

# 20. Extension registry

The final system SHOULD maintain a concise registry in this document or a generated reference derived from code.

Initial architectural registry:

| Extension domain | Owner | Mechanism | Dynamic project code allowed |
|---|---|---|---|
| Active language sources | `project/` | GF files and project configuration | No Python |
| Project scenarios | `project/validation/scenarios/` | Registered `.gfs` files | No Python |
| Scenario inputs | `project/validation/inputs/` | Declared data files | No executable code |
| Gold expectations | `project/validation/gold/` | Explicit reviewed files | No |
| Project configuration | `project_config.py` | Versioned TOML fields | No callables |
| Validation modes | bootstrap and audit policy | Explicit canonical mode registry | No |
| Validation stages | `audit_core.py` and stage owners | Explicit ordered registration | Framework code only |
| Static scan rules | `scanner.py` | Explicit rule registry | Framework code only |
| Diagnostic parsers | `diagnostics.py` | Ordered parser registry | Framework code only |
| Causal classifiers | `classifier.py` | Explicit rule functions | Framework code only |
| Output normalizers | normalization owner | Versioned ordered rules | Framework code only |
| Gold strategies | comparison owner | Explicit strategy registry | Framework code only |
| Reports | `app/reports/` | Explicit writer registration or orchestration | Framework code only |
| Artifact roles | artifact/manifest owner | Stable role registry | Framework code only |
| CLI | `main_cli.py` | Explicit commands and options | No |
| GUI | `main_gui.py`, `app/gui/` | Explicit actions calling core services | No |
| External tools | process layer and adapter | Contract-approved adapter | No arbitrary discovery |
| CI integrations | supported CLI and artifacts | External wrapper | No internal bypass |

A registry entry is descriptive unless the corresponding code registry is explicitly defined. Documentation MUST NOT imply runtime discovery that the implementation does not provide.

---

# 21. Drift indicators

Extension-boundary drift is probable when:

- project-specific names appear in framework modules;
- a report imports a validation stage;
- a GUI widget builds or executes a GF command;
- CLI and GUI use different configuration builders;
- a new stage writes an existing stage’s artifacts;
- a result field appears without a documented producer;
- a report computes a different status from the run result;
- a scanner rule executes GF;
- a diagnostic parser assigns causal classification;
- a classifier launches a process;
- a project configuration field selects a Python callable;
- a `.gfs` scenario updates gold during a normal run;
- an extension depends on import order or side effects;
- a new status literal appears outside its owner;
- a consumer reconstructs an artifact filename;
- raw output is modified after capture;
- a new tool is invoked without an external-tool contract;
- a language project changes framework code to add linguistic behavior;
- multiple language profiles are introduced into one active project;
- an optional extension silently becomes release-required;
- a schema changes without a version increment;
- a new abstraction exists without a concrete second use case.

Any drift indicator requires either:

1. restoration of the existing boundary; or
2. an explicit architectural change with contracts, tests, migration, and documentation.

---

# 22. Final enforcement rule

GF Wordbench is extensible, but it is not open-ended.

A valid extension:

- has one owner;
- enters through one approved boundary;
- preserves dependency direction;
- produces structured evidence;
- respects artifact ownership;
- uses common infrastructure;
- remains deterministic;
- is documented and tested;
- does not introduce hidden behavior;
- does not weaken the separation between framework and active project.

Therefore:

> No extension may create a second source of truth, a second execution engine, a second status system, or an undocumented path around the core architecture.
