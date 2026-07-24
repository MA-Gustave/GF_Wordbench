# GF Wordbench — Extension Boundaries

**Document ID:** `GF-WB-ARCH-EXTENSION-BOUNDARIES`  
**Status:** Normative  
**Applies to:** GF Wordbench framework, active project, project template, validation assets, reports and approved external-tool integrations  
**Owner:** GF Wordbench maintainers  
**Architecture version:** `2.0.0`  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines where GF Wordbench may be extended, how each extension integrates, and which architectural boundaries remain closed.

GF Wordbench is extensible through explicit, owned seams. It is not an open-ended plugin platform, a generic workflow engine or a multi-project orchestration product.

The governing rule is:

> Extend GF Wordbench through an owned boundary; never bypass ownership or create a parallel execution path.

Every extension preserves:

- one active GF language project per Wordbench workspace;
- one normative project target per run;
- GF as the language-execution authority;
- deterministic validation;
- typed and structured results;
- immutable raw evidence;
- stable artifact ownership;
- versioned persisted schemas;
- equivalent CLI and GUI semantics;
- explicit migrations for incompatible public changes;
- contract and integration tests.

---

## 2. Product boundary

GF Wordbench owns validation, diagnostics, evidence, reports and release gates for one active GF project.

The independent companion product `gf-portfolio` owns multi-workspace inventory, multilingual aggregation, cross-project comparison and portfolio views.

Allowed dependency direction:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

Prohibited dependency direction:

```text
GF Wordbench -> gf-portfolio runtime
GF Wordbench -> gf-portfolio private schemas
GF Wordbench -> gf-portfolio storage
GF Wordbench -> gf-portfolio configuration
GF Wordbench -> gf-portfolio services
```

An extension to Wordbench must not introduce a portfolio registry, several active projects in one workspace, several active targets in one run or a reverse dependency on `gf-portfolio`.

---

## 3. Related authorities

Adjacent contracts are owned by:

| Document | Authority |
|---|---|
| `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` | Cross-document product and architecture alignment |
| `docs/INTERFILE_CONTRACT_LOCK.md` | Framework component and file contracts |
| `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` | GF, process, filesystem and approved executable boundaries |
| `docs/PERSISTED_SCHEMA_LOCK.md` | Configuration, state, summaries, manifests, outputs and gold schemas |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | Active-project GF modules, scenarios, inputs, golds and artifacts |
| `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` | Generic initialized-project structure |
| `docs/architecture/EXTENSION_BOUNDARIES.md` | Approved extension seams and closed boundaries |

This document defines where a capability belongs. Field-level schemas and command construction remain with their owner documents.

---

## 4. Normative terms

- **MUST / MUST NOT**: mandatory or prohibited.
- **SHOULD / SHOULD NOT**: expected unless a reviewed exception exists.
- **MAY**: optional.
- **EXTENSION POINT**: an approved boundary through which behavior may be added.
- **EXTENSION OWNER**: the component responsible for that boundary.
- **CORE PATH**: the shared execution path used by CLI, GUI, tests and automation.
- **BYPASS**: an alternate path that avoids an owner, validator, model or contract.
- **REGISTRATION**: explicit declaration that makes an extension discoverable.
- **DYNAMIC PLUGIN**: runtime-loaded code from arbitrary or externally supplied modules.
- **PROJECT EXTENSION**: language-specific GF or data content under `project/`.
- **FRAMEWORK EXTENSION**: language-neutral behavior in the Wordbench application.

---

## 5. Extension principles

### 5.1 Explicit before generic

Prefer:

- explicit registries;
- direct typed calls;
- owned adapters;
- clear orchestration sequences.

Do not introduce:

- arbitrary runtime plugin discovery;
- dependency-injection containers as service locators;
- generic event buses;
- generic hook systems;
- workflow-definition languages;
- reflection-driven execution;
- import-side-effect registration.

A reusable abstraction requires at least two concrete, stable use cases and an accepted architectural decision when it changes dependency direction or public contracts.

### 5.2 Language-specific behavior belongs to the project

Language-specific modules, paths, scenarios, expectations, morphology checks and linguistic policies remain under:

```text
project/
```

Framework code must not contain active-language module names, suffixes, lexical assumptions or hard-coded language source directories.

### 5.3 Framework ownership remains central

The active project declares what is validated. It does not replace:

- process execution;
- timeout handling;
- raw evidence capture;
- status semantics;
- result serialization;
- report ownership;
- manifest generation;
- release-gate calculation.

### 5.4 GF remains authoritative

Extensions use GF for:

- module loading;
- type checking;
- compilation;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology and grammar introspection;
- missing-function inspection.

Python orchestrates, captures, normalizes, classifies, compares and reports. It does not reimplement GF semantics.

### 5.5 Additive by default

Extensions should preserve existing public behavior.

A change that alters a public symbol, field, command, artifact, status, normalization rule, project contract or release criterion requires coordinated contract and migration work.

---

## 6. Architectural model

GF Wordbench uses one deployable hexagonal modular monolith.

Functional modules:

```text
projects
runs
validation
diagnostics
reporting
```

Architectural rings:

```text
domain
application
ports
adapters
entrypoints
bootstrap
```

Expected dependency direction:

```text
entrypoints -> application
bootstrap -> application + ports + adapters
application -> domain + ports
adapters -> ports + external systems
domain -> no GUI, CLI, filesystem, subprocess or external-tool implementation
```

Extensions preserve this direction.

Reports consume results. They do not execute validation.

GUI and CLI call the same application use cases.

Active-project data enters through the projects boundary and never through arbitrary executable Python supplied by the project.

---

## 7. Approved extension points

## 7.1 Active project

**Owner**

```text
project/project.toml
project/
```

**Permitted**

- add or change GF source modules;
- declare entrypoints and checkpoints;
- add native `.gfs` scenarios;
- add scenario inputs;
- add or update reviewed gold files;
- define project release requirements;
- document language architecture and module contracts;
- register language-specific validation coverage.

**Required integration**

- validate project configuration;
- update affected GF interfile contracts;
- update the dependency map;
- review scenarios and golds;
- run affected checkpoint and release validation.

**Forbidden**

- importing project Python into the framework;
- placing project-specific defaults in framework configuration;
- using GUI state as project authority;
- changing framework-wide status semantics from project data;
- selecting arbitrary Python callables from project configuration;
- defining several active language profiles in one project file.

The active project is a GF-and-data extension boundary, not a Python plugin boundary.

---

## 7.2 Project template

**Owner**

```text
templates/project/
```

**Permitted**

- add required project files;
- add generic placeholders for project contracts;
- add generic scenario, input, gold or documentation templates;
- add safe configuration defaults.

**Required integration**

Review changes against:

```text
project/
docs/projects/
docs/configuration/
docs/PERSISTED_SCHEMA_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

**Forbidden**

- active-language identity or linguistic content;
- fields unknown to the project loader;
- structural drift between initialized projects and the template.

---

## 7.3 Project configuration

**Owner**

```text
projects module
project/project.toml
docs/configuration/PROJECT_TOML_REFERENCE.md
```

A new field may represent:

- project identity;
- language identity;
- source selection;
- entrypoints;
- checkpoints;
- GF path parts;
- scenario registration;
- release targets;
- validation policy.

Every field defines:

```text
name
type
required or optional policy
default
validation
path base
consumer
serialization
compatibility behavior
```

**Forbidden**

- arbitrary key-value bags with different meanings per consumer;
- GUI-only or CLI-only project fields;
- executable Python references;
- machine-specific absolute paths for project-owned files;
- secrets;
- transient UI state;
- Portfolio-owned fields.

---

## 7.4 Framework defaults

**Owner**

```text
bootstrap and configuration owners
```

Permitted defaults are language-neutral:

- canonical filenames;
- safe timeouts;
- output limits;
- retention defaults;
- mode-independent behavior defaults.

Defaults must be resolved consistently for CLI and GUI.

They must not encode active-language names, project source paths, developer-specific paths or duplicate an artifact-path owner.

---

## 7.5 Validation modes

Canonical modes are:

```text
quick
checkpoint
release
diagnostic
```

A new mode requires:

- a stable purpose;
- explicit stage policy;
- required and optional semantics;
- CLI and GUI parity;
- exit-code behavior;
- report and schema representation;
- compatibility analysis;
- an accepted ADR;
- contract tests.

A mode must not introduce another audit engine or language-specific framework behavior.

Legacy aliases may be accepted by migrations but are not canonical output values.

---

## 7.6 Validation stages

**Owner**

```text
validation application orchestration
```

A stage produces distinct evidence or evaluates a distinct validation concern.

Each stage defines:

```text
stage ID
purpose
owner
typed inputs
typed outputs
configuration
owned artifacts
status mapping
execution-state mapping
error behavior
ordering constraints
mode inclusion
tests
```

A stage must:

- preserve raw evidence before interpretation;
- use owned run paths;
- write only its artifacts;
- return structured results;
- expose timeout and cancellation explicitly;
- leave the run structurally valid after recoverable failure.

A stage must not:

- discover arbitrary packages;
- register through import side effects;
- render user-facing reports;
- parse another stage's Markdown report;
- launch tools outside the common process boundary;
- update golds during normal validation;
- redefine global status semantics.

---

## 7.7 File selection

**Owner**

```text
validation file-selection component
```

Permitted extensions include:

- language-neutral include and exclude rules;
- checkpoint-aware selection;
- deterministic source grouping;
- project-configured source roots;
- structured selection metadata.

Requirements:

- deterministic order;
- a structured reason for every exclusion;
- canonical project-relative result paths;
- containment within approved roots;
- generated run output excluded from source discovery;
- predictable limits.

File discovery must not compile files, infer linguistic meaning from names or scan outside approved roots.

---

## 7.8 Static scan rules

**Owner**

```text
validation scanner
```

Each rule defines:

```text
rule ID
title
purpose
scope
severity
input representation
finding fields
false-positive constraints
normalization behavior
tests
```

Rules are deterministic analyses of normalized source text and structural masks.

A finding contains, when available:

```text
rule ID
file path
line
column
message
evidence excerpt
severity
```

The registry uses stable unique IDs and deterministic order.

Static rules must not:

- execute GF;
- edit sources;
- write reports;
- classify interfile causality;
- load project Python;
- silently change meaning under an existing ID.

---

## 7.9 GF compilation

**Owner**

```text
validation compiler and GF adapter
```

Permitted extensions include:

- additional compile targets;
- explicit compilation policies;
- captured metadata;
- version-aware command construction;
- artifact verification.

Compilation must:

- use the common process port;
- use the common GF path resolver;
- preserve stdout and stderr;
- record executable, arguments and working directory;
- distinguish validation failure, launch failure, timeout, cancellation and skipped execution;
- return structured compile results;
- leave causal classification to diagnostics.

Compilation must not contain language-specific command branches, invoke reports or treat zero exit status as proof that every required artifact exists.

---

## 7.10 Diagnostic parsing

**Owner**

```text
diagnostics module
```

A parser rule defines:

```text
rule ID
source stream
recognition pattern
priority
normalized kind
captured fields
GF-version applicability
fallback behavior
fixtures
```

Requirements:

- raw output remains authoritative;
- parser order is deterministic;
- specific patterns precede fallbacks;
- unmatched evidence remains visible;
- parser failure does not destroy process evidence.

Diagnostic parsers do not assign direct, downstream or ambiguous causality and do not launch processes.

---

## 7.11 Failure classification

**Owner**

```text
diagnostics causal classifier
```

Canonical causal classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

A classifier extension may add evidence-based causal rules or blocker resolution.

It must:

- consume structured results and dependency evidence;
- preserve error kind and raw output;
- record blockers when known;
- remain deterministic;
- prefer ambiguity to unsupported certainty.

It must not execute processes, scan sources independently, render reports or redefine validation status.

---

## 7.12 Native GF scenarios

**Owners**

```text
validation scenario runner
project/validation/scenarios/
```

Scenarios may validate:

- loading;
- missing functions;
- parsing;
- linearization;
- bounded generation;
- morphology;
- grammar introspection;
- PGF behavior;
- language-specific regressions.

Every scenario defines:

```text
scenario ID
script path
required or optional policy
applicable modes
timeout
entrypoint or target
assertion strategy
gold path when applicable
normalization identity
```

Scenarios:

- use native `.gfs`;
- execute through GF;
- use stable markers or another documented completion protocol;
- preserve raw output;
- normalize only after capture;
- produce structured scenario results;
- run in deterministic configured order.

Scenarios must not use project Python callbacks, private process runners, implicit gold mutation or unregistered release-gating behavior.

---

## 7.13 Scenario assertions

**Owners**

```text
scenario runner
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

An assertion type defines:

```text
type ID
input source
comparison semantics
failure representation
serialization
report rendering
tests
```

Supported assertion families may include:

- required markers;
- section completion;
- stable contains or excludes checks;
- normalized equality;
- artifact existence;
- declared parse-count conditions;
- empty missing-function output.

Assertions must not depend on rendered Markdown, discard contradictory evidence or treat unknown assertion types as success.

---

## 7.14 Output normalization

**Owner**

```text
validation normalization component
```

Normalization may remove documented presentation instability such as:

- line-ending differences;
- approved absolute path prefixes;
- run-directory identifiers;
- non-semantic timing values;
- approved ANSI sequences;
- excluded tool banners.

Every normalization rule has a stable ID and deterministic order. Comparison-affecting changes use an explicit normalization version and reviewed gold updates.

Normalization must not remove or rewrite:

- GF error meaning;
- abstract trees;
- linearized strings;
- parse ambiguity;
- missing-function lists;
- morphology output;
- relevant Unicode distinctions;
- required markers;
- failure evidence;
- meaningful punctuation or whitespace.

Raw evidence remains unchanged.

---

## 7.15 Gold comparison

**Owner**

```text
validation comparison component
```

Comparison strategies may include:

- exact normalized text;
- normalized section equality;
- declared unordered-set equality;
- structured count comparison;
- explicit pattern assertions.

Each strategy is declared by scenario configuration and produces a machine-readable result and human-readable diff.

Missing required gold is a failure.

Gold files are changed only through an explicit reviewed operation.

The comparison strategy must not be inferred from output content or silently changed on mismatch.

---

## 7.16 Result models

**Owner**

```text
domain and application result models
```

A model extension defines:

```text
field name
type
required or optional policy
default
producer
consumers
serialization form
compatibility behavior
validation invariants
```

Models contain data and invariants, not orchestration or presentation code.

Producers and consumers change together.

Persisted fields follow the schema lock.

Models must not contain GUI objects, open process handles, streams or untyped extension bags when a stable typed structure is appropriate.

---

## 7.17 Reports

**Owner**

```text
reporting module
```

Each report defines:

```text
report ID
consumer
input model
owned path
media type
required or optional policy
stable sections or schema
failure behavior
manifest role
tests
```

Reports:

- consume structured results;
- use owned paths;
- write only owned artifacts;
- never rerun validation;
- never reclassify failures independently;
- preserve deterministic ordering;
- isolate writer failures from captured evidence.

Prohibited dependencies:

```text
reports -> compiler
reports -> scanner
reports -> scenario runner
reports -> process runner
reports -> GUI
```

---

## 7.18 Artifact roles and manifest entries

**Owner**

```text
runs and reporting artifact owners
```

A new role defines:

```text
stable role ID
producer
required or optional policy
owned path
media type
hash policy
retention
summary linkage
tests
```

Two components must not write the same artifact.

Consumers must not reconstruct filenames already owned by a path or artifact model.

Raw evidence is immutable after capture.

---

## 7.19 CLI

**Owner**

```text
CLI entrypoint and bootstrap
```

A CLI extension:

- exposes an approved application capability;
- reuses bootstrap and application services;
- validates inputs before execution;
- uses documented exit codes;
- documents defaults and precedence;
- has parser and integration tests.

CLI handlers must not execute GF directly, create separate result models, mutate hidden project state or define validation semantics that differ from GUI behavior.

The normative command surface belongs to `docs/usage/CLI_REFERENCE.md`.

---

## 7.20 GUI

**Owner**

```text
GUI entrypoint and presentation adapters
```

A GUI extension may:

- expose approved configuration;
- display structured results;
- navigate to owned artifacts;
- invoke explicit maintenance operations;
- show progress.

The GUI:

- uses the same application services as the CLI;
- keeps local UI state disposable;
- maps structured errors for presentation;
- keeps external execution away from widget code;
- preserves CLI-equivalent semantics.

GUI widgets must not construct GF commands, execute tools directly, own project configuration or recompute diagnostics.

---

## 7.21 Application state

**Owner**

```text
application-state adapter
```

State may store disposable local preferences such as:

- environment selections;
- last mode;
- display preferences;
- output location;
- recent run pointers.

State must use safe defaults, atomic writes, schema validation and corruption recovery.

It must not become authority for project identity, entrypoints, scenario policy, results, credentials or release decisions.

Deleting application state must leave the project valid.

---

## 7.22 External tools

**Owners**

```text
external-tool port and adapter
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

A tool integration defines:

```text
tool ID
purpose
license
supported versions
installation expectations
platform support
command contract
working directory
environment
inputs
outputs
timeouts
artifacts
failure semantics
security implications
fallback behavior
tests
```

All tools use the common process boundary and explicit command contracts.

Arbitrary command execution and dynamic discovery are prohibited.

Optional tools must not silently become prerequisites.

Tool output supplements but does not replace GF evidence.

---

## 7.23 Automation and CI

**Owner**

```text
supported CLI and public run artifacts
```

Automation may:

- invoke supported commands;
- consume `summary.json` and `manifest.json`;
- generate machine annotations;
- archive artifacts;
- enforce release gates.

Automation must preserve exit-code semantics and project identity, avoid machine-specific assumptions, and retain required evidence.

It must not parse Markdown when structured data exists, rewrite validation status, bypass required stages or mutate sources and golds during ordinary validation.

---

## 8. Closed boundaries

The following are not extension points.

### 8.1 Arbitrary project Python

Wordbench does not load Python modules or callables from the active project.

Language-specific executable behavior is expressed through GF sources and reviewed `.gfs` scenarios.

### 8.2 Global result semantics

Validation status, execution state, error kind and diagnostic causal class are centrally owned.

New values require coordinated model, schema, report, CLI, GUI and migration updates.

### 8.3 Process execution

All external processes use the common process port and adapter.

No stage, report or interface owns a private process runner.

### 8.4 Artifact paths

Paths and filenames are owned centrally by project configuration, run paths or the artifact registry.

Consumers do not reconstruct them.

### 8.5 Raw evidence

Captured commands, stdout, stderr, exit status and tool artifacts remain immutable.

Derived normalization and summaries never replace them.

### 8.6 Release decision

One release-policy owner computes the run's release result from structured stage results.

Stages, reports, GUI panels and project scripts do not independently declare release success.

### 8.7 Multiple active projects

A Wordbench workspace does not contain several active projects or runtime-switchable language profiles.

Cross-workspace and multilingual capabilities belong to `gf-portfolio`.

---

## 9. Placement rules

New files are placed by responsibility:

```text
app/
├── projects/
├── runs/
├── validation/
├── diagnostics/
├── reporting/
├── domain/
├── application/
├── ports/
├── adapters/
├── entrypoints/
└── bootstrap/

project/
├── project.toml
├── GF sources
├── validation/
│   ├── scenarios/
│   ├── inputs/
│   └── gold/
└── docs/

templates/project/
└── generic mirror of required project structure
```

A new top-level package is not created when an existing owner fits the responsibility.

---

## 10. Registration rules

Extensions participating in execution are explicitly registered.

A registration entry contains stable declarative metadata and a known framework implementation reference.

Conceptual example:

```python
StageDefinition(
    stage_id="scenario",
    implementation=run_required_scenarios,
    applicable_modes=("checkpoint", "release", "diagnostic"),
    required_for_release=True,
)
```

Registration requires:

- stable unique ID;
- one owner;
- deterministic order;
- explicit applicable modes;
- explicit required or optional semantics;
- no import-time execution;
- no project-supplied Python callable;
- no hidden environment-controlled registration.

A registry must not become an untyped service locator.

---

## 11. Compatibility

### 11.1 Internal change

An internal change alters no public symbol, result field, schema, command, artifact path, status meaning, project contract or CLI/GUI behavior.

It requires tests but no migration.

### 11.2 Compatible public extension

Examples:

- optional result metadata with a defined default;
- optional report;
- optional scenario;
- optional manifest role;
- new scan rule with a unique ID;
- new parser preserving fallback behavior;
- new project field with a safe default.

A compatible extension updates its owner, consumers, tests, documentation and relevant locks. Persisted public additions follow schema versioning rules.

### 11.3 Breaking extension

Examples:

- semantically changing stage order;
- making an optional stage required;
- renaming an ID;
- changing a field type;
- moving artifact ownership;
- changing normalization in a way that invalidates gold;
- changing status meaning;
- changing a command contract;
- adding required project configuration;
- changing release criteria.

A breaking extension requires coordinated provider and consumer changes, migration or deprecation, version updates, tests, changelog entries and release validation.

---

## 12. Security boundaries

Treat these inputs as untrusted unless explicitly controlled:

- project paths;
- scenario files and inputs;
- executable paths;
- environment variables;
- previous-run artifacts;
- imported state;
- copied templates.

Extensions must:

- validate path containment;
- avoid shell interpretation;
- prohibit project Python execution;
- control GF shell escape behavior;
- avoid secrets and full environment dumps;
- avoid automatic tool installation;
- validate persisted schemas;
- write state and artifacts atomically;
- reject path traversal;
- preserve failure evidence.

A new executable or executable input requires external-tool and security review.

---

## 13. Performance boundaries

Performance changes preserve observable contracts.

Extensions should:

- avoid repeated reads of large sources;
- avoid recompilation for report generation;
- bound captured output;
- preserve deterministic ordering;
- respect timeout and cancellation policies;
- keep quick mode bounded;
- avoid caches without explicit ownership and invalidation;
- record truncation.

A cache shared across runs or processes requires an owner, invalidation policy, persistence contract and corruption behavior.

---

## 14. Testing requirements

Every extension has tests appropriate to its boundary.

### Unit tests

Use unit tests for:

- configuration validation;
- registration;
- scanner rules;
- diagnostic parsing;
- classification;
- normalization;
- comparison;
- result construction;
- report rendering;
- path containment;
- migrations.

### Contract tests

Use contract tests for:

- public signatures;
- required model fields;
- artifact ownership;
- deterministic ordering;
- schema round trips;
- CLI/GUI parity;
- process result semantics;
- stage registration;
- scenario requirements;
- gold immutability;
- command construction;
- prohibited dependency directions.

### Integration tests

Use integration tests for:

- pipeline orchestration;
- successful and failing fixture grammars;
- GF version probing;
- compilation;
- native `.gfs` execution;
- timeout containment;
- PGF production;
- report and manifest completeness;
- previous-run comparison.

Tests requiring real GF remain separable from the unit suite.

---

## 15. Documentation rule

Documentation changes are required when an extension changes a public contract, command, schema, artifact, user workflow, project structure, security boundary or architectural ownership.

The authoritative owner document is updated once. Other documents link to it instead of duplicating the complete rule.

Extension documentation identifies:

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

Internal implementation edits that preserve every documented contract do not require broad documentation rewrites.

---

## 16. ADR threshold

An ADR is required when an extension:

- adds an architectural layer;
- introduces a required external tool;
- adds runtime plugin discovery;
- adds a canonical validation mode;
- changes the one-active-project model;
- introduces a database or remote service;
- changes artifact ownership;
- changes release-result computation;
- changes a persisted schema major version;
- introduces executable project code outside GF;
- replaces a core component;
- changes dependency direction;
- changes the Wordbench/Portfolio boundary.

Small additive rules, reports, parsers and scenarios do not require a separate ADR when they remain inside an existing approved boundary.

---

## 17. Anti-overengineering constraints

GF Wordbench does not require:

- a plugin marketplace;
- a dependency-injection framework;
- an event bus;
- a message broker;
- a database;
- a web service;
- remote execution;
- a generic DAG engine;
- a custom language replacing `.gfs`;
- simultaneous language profiles;
- runtime discovery of third-party Python packages.

Such a mechanism requires a concrete unmet need, at least two stable use cases, documented security and operational costs, comparison with a simpler design and an accepted ADR.

---

## 18. Review checklist

```text
[ ] Purpose is concrete
[ ] Existing owner cannot provide the capability cleanly
[ ] Extension point and owner are identified
[ ] Framework or project placement is correct
[ ] Stable ID is assigned
[ ] Inputs and outputs are typed or schema-defined
[ ] Applicable modes are explicit
[ ] Required and optional behavior is explicit
[ ] Artifact ownership is explicit
[ ] Raw evidence remains immutable
[ ] Process execution uses the common boundary
[ ] GF semantics remain delegated to GF
[ ] Project Python execution is not introduced
[ ] Path containment is validated
[ ] Deterministic ordering is preserved
[ ] CLI and GUI semantics agree
[ ] Schema impact is reviewed
[ ] External-tool impact is reviewed
[ ] Security impact is reviewed
[ ] Compatibility and migration are handled
[ ] Tests are added
[ ] Owner documentation and locks are updated
[ ] ADR is added when required
[ ] Relevant validation passes
[ ] Wordbench remains independent from gf-portfolio
```

---

## 19. Extension registry

| Domain | Owner | Mechanism | Project code allowed |
|---|---|---|---|
| Active language sources | `project/` | GF files and project configuration | GF only |
| Project scenarios | `project/validation/scenarios/` | Registered `.gfs` files | GF only |
| Scenario inputs | `project/validation/inputs/` | Declared data files | No executable code |
| Gold expectations | `project/validation/gold/` | Reviewed expected outputs | No |
| Project configuration | projects module | Versioned TOML | No callables |
| Validation modes | application policy | Explicit mode registry | No |
| Validation stages | validation module | Explicit ordered registration | Framework code only |
| Static scan rules | validation scanner | Explicit rule registry | Framework code only |
| Diagnostic parsers | diagnostics module | Ordered parser registry | Framework code only |
| Causal classifiers | diagnostics module | Explicit typed rules | Framework code only |
| Normalizers | validation module | Versioned ordered rules | Framework code only |
| Gold strategies | validation module | Explicit strategy registry | Framework code only |
| Reports | reporting module | Explicit writer orchestration | Framework code only |
| Artifact roles | runs/reporting | Stable role registry | Framework code only |
| CLI | entrypoints | Explicit commands | No |
| GUI | entrypoints/adapters | Application use cases | No |
| External tools | adapters | Approved command contracts | No dynamic discovery |
| CI integration | public CLI and artifacts | External wrappers | No private bypass |
| Portfolio integration | public Wordbench artifacts | Read-only external consumer | No reverse dependency |

---

## 20. Drift indicators

Boundary drift is present when:

- project-specific names appear in framework defaults;
- a report imports a validation stage;
- a GUI widget constructs or executes a GF command;
- CLI and GUI use different application rules;
- a stage writes another stage's artifacts;
- a result field has no owner;
- a report recomputes status;
- a scanner rule executes GF;
- a parser assigns causal classification;
- a classifier launches a process;
- project configuration selects Python code;
- a scenario changes gold during normal validation;
- registration depends on import order or hidden environment state;
- a consumer reconstructs an artifact filename;
- raw output is modified after capture;
- a tool is invoked without an approved contract;
- several active projects appear in one Wordbench workspace;
- Wordbench imports or requires `gf-portfolio`;
- a schema changes without versioning;
- a generic abstraction has no concrete second use case.

Drift is resolved by restoring the existing boundary or accepting a coordinated architectural change.

---

## 21. Enforcement

A valid extension:

- has one owner;
- enters through one approved boundary;
- preserves dependency direction;
- produces structured evidence;
- respects artifact ownership;
- uses common infrastructure;
- remains deterministic;
- is documented and tested;
- introduces no hidden behavior;
- preserves framework/project separation;
- preserves Wordbench/Portfolio independence.

Therefore:

> No extension may create a second source of truth, a second execution engine, a second status system, a second active-project model or an undocumented path around the core architecture.
