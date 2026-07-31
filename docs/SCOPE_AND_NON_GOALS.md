# GF Wordbench — Product Overview

**Document ID:** `GF-WB-PRODUCT-OVERVIEW`  
**Applies to:** GF Wordbench framework, path-resolved active language context, optional validation profiles, and validation runs  
**Owner:** GF Wordbench maintainers  
**Product name:** GF Wordbench  
**Package name:** `gf-wordbench`  
**Primary command:** `gf-wordbench`  
**Document version:** `1.2.0`  
**Last reviewed:** `2026-07-30`  
**Governing startup decision:** `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`

---

## 1. Product definition

GF Wordbench is a development, validation, and release workbench for exactly one resolved Grammatical Framework language context at a time.

A user opens one GF language directory or one `.gf` source file. Wordbench derives a bounded language candidate from that explicit selection, validates the candidate with its existing source-selection, path-resolution, preflight, compilation, and diagnostic services, and publishes one immutable `ResolvedLanguageContext` before executable validation begins.

GF Wordbench does not replace GF. It uses GF as the authoritative execution engine and adds the workflow and evidence controls that GF alone does not provide:

- path-resolved language startup;
- deterministic source selection;
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

A successful basic language load requires a valid selected source path and a structurally valid resolved context. It does not require a global language catalog, a mandatory language bundle, scenarios, gold files, release documentation, or `project/project.toml`.

Advanced scenario, regression, checkpoint, and release behavior is supplied through an explicit optional validation profile. Existing `project/project.toml` projects remain supported as validation profiles, but they are not the mandatory startup authority.

One Wordbench session may open or switch between languages sequentially, but only one resolved language context may be active at a time and one ordinary run may contain only one language identity. Cross-run and cross-workspace portfolio aggregation belongs to the independent `gf-portfolio` product, which consumes public versioned artifacts and is never required by GF Wordbench.

---

## 2. Product purpose

Developing a GF language is not a single compilation task.

A language can contain many modules, interfaces, instances, resources, paradigms, helpers, constructors, entrypoints, scenarios, and generated artifacts. A locally correct edit can still break another module, invalidate a scenario, change expected linguistic output, or create a downstream failure that hides the root cause.

GF Wordbench exists to make those relationships observable and testable without requiring a second manually maintained representation of the RGL source tree.

The product first establishes a trustworthy working context:

```text
explicit language directory or .gf file
→ bounded language candidate
→ deterministic source inventory
→ one effective GF path resolution
→ structural preflight
→ immutable ResolvedLanguageContext
```

It then provides a controlled path from an individual source edit to the strongest validation level supported by the current context and optional profile:

```text
source change
→ static checks
→ GF compilation
→ failure classification
→ optional project checkpoints
→ optional GF scenarios
→ optional golden comparison
→ optional final grammar build
→ evidence and reports
→ release decision when release-ready
```

The product is successful when a developer can answer, from one run:

1. Which language path and identity were resolved?
2. What was tested?
3. Which GF commands were executed?
4. What passed?
5. What failed?
6. Which failure is likely direct?
7. Which failures are probably downstream?
8. What changed since the previous compatible run?
9. Which requested capabilities or release criteria remain unavailable or unsatisfied?
10. Where is the raw evidence?
11. Can another developer or AI system inspect the result without rerunning GF?

---

## 3. Product goals

GF Wordbench MUST provide the following product-level outcomes.

### 3.1 Repeatable validation

Equivalent source content, selected-path semantics, resolved context, toolchain, explicit profile, and scenario inputs SHOULD produce equivalent normalized results.

Every executable run MUST record enough resolved context to explain what was executed.

### 3.2 Fast development feedback

A developer MUST be able to open a standard RGL language path, browse and scan its sources, and validate one changed file or focused target without configuring a complete release project.

### 3.3 Authoritative release validation

A final release mode MUST verify more than individual source compilation. It requires an explicit release-capable validation profile and MUST include its configured final entrypoints, required scenarios, required golden comparisons, and required generated artifacts.

Loading or compiling a language without such a profile MUST NOT be presented as release readiness.

### 3.4 Root-cause-oriented diagnostics

GF Wordbench MUST distinguish likely direct failures from downstream cascades and ambiguous failures.

The product MUST preserve raw GF evidence so classifications can be reviewed.

### 3.5 Drift prevention

Contracts between Python files, external tools, persisted schemas, resolved language contexts, optional validation profiles, GF sources, scenarios, gold files, and generated artifacts MUST be explicit and testable.

### 3.6 Reusable language workflow

The framework MUST support another standard GF language by resolving a new explicit language path rather than redesigning the validation engine, cloning framework code, or maintaining a mandatory global runtime catalog.

Switching language MUST create a new resolved context and runtime rather than mutate an active runtime in place.

### 3.7 Human, automation, and AI usability

The same run MUST produce:

- a machine-readable result;
- a concise human-readable result;
- an AI-ready diagnostic packet;
- detailed raw evidence.

### 3.8 Evidence preservation

A partial failure MUST NOT erase already captured logs, diagnostics, fingerprints, or artifacts.

### 3.9 Progressive capability

Wordbench MUST expose only the capabilities supported by the resolved environment:

```text
source-ready
scan-ready
compile-ready
scenario-ready
release-ready
```

Failure of a stronger capability MUST NOT erase a weaker valid capability. For example, a missing GF executable may prevent compilation while source browsing and static scanning remain available.

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

GF Wordbench separates four layers.

### 5.1 Framework layer

The framework contains reusable Python code and permanent documentation.

It owns:

- language-path probing orchestration;
- source selection;
- GF path resolution coordination;
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

The language probe is an application orchestration service. It MUST reuse the public contracts of existing selection, path, preflight, compilation, and diagnostic components rather than reproduce their internal rules.

### 5.2 Resolved language context layer

The active runtime contains exactly one immutable `ResolvedLanguageContext`.

The context owns the resolved facts used by the current session and its runs, including:

- language key and recorded display identity;
- selected path and selected-path kind;
- language source directory;
- RGL source root and RGL root when resolved;
- focused source file when applicable;
- module suffix when unambiguous;
- available standard entrypoint candidates;
- deterministic source inventory or its stable reference;
- effective GF path requirements and resolution provenance;
- structural diagnostics;
- capability statuses.

Consumers MUST use this context. They MUST NOT independently rediscover the language directory, language identity, or GF path.

### 5.3 Optional validation profile layer

An explicit validation profile extends the resolved language context with project-level policy.

A profile may own:

- source filters beyond the basic language directory;
- configured entrypoints;
- checkpoints;
- required and optional scenarios;
- scenario inputs;
- gold files;
- PGF and release targets;
- language architecture and specification documents;
- known issues and decision records;
- release criteria.

An existing `project/project.toml`, a reviewed language bundle, or another supported versioned profile format may provide these values. A profile MUST be explicitly selected, associated, or supplied by automation and MUST agree with the resolved language context before execution.

### 5.4 External tool layer

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

One GF Wordbench session has either no loaded language or exactly one published `ResolvedLanguageContext`. Every ordinary run resolves exactly one language identity.

This is a deliberate product constraint, but it is a runtime constraint rather than a requirement for one physical Wordbench clone per language.

The interactive application MAY allow the user to:

- open a language directory;
- open a `.gf` file;
- reopen the last successfully resolved selected path;
- switch to another language after the current run has ended.

A language switch MUST:

```text
end or leave the current runtime
→ resolve the new explicit path
→ publish a new immutable context
→ compose a new runtime
```

It MUST NOT mutate the active language identity, effective GF path, selected sources, profile, or prior-run eligibility while a run is active.

Benefits include:

- clear language identity per run;
- no cross-language state leakage;
- no mixed source or evidence sets;
- centralized path resolution;
- smaller failure surface;
- easier AI handoff;
- reproducible run evidence.

A single installed executable or package MAY serve many languages sequentially. Simultaneous multi-language dashboards, cross-language aggregation, and portfolio readiness remain responsibilities of the independent `gf-portfolio` product.

The active language identity MUST come from the validated, published `ResolvedLanguageContext`.

It MUST NOT come from:

```text
GUI labels alone
application-state labels
old output directories
historical reports
a static catalog entry alone
an unvalidated filename guess
```

Application state MAY remember the last successful selected path as local convenience, but that path MUST be revalidated before a new context is published.

---

## 7. Core capabilities

### 7.1 Path-resolved language startup

GF Wordbench accepts one explicit primary language selection:

```text
one readable GF language directory
or
one readable .gf source file
```

It performs bounded structural resolution, creates a language candidate, and validates that candidate through shared application services.

Normal startup MUST NOT require:

- `rgl-language-catalog.json`;
- a mandatory `language.toml`;
- a mandatory language bundle;
- scenarios or gold files;
- a release profile.

Discovery produces candidate facts only. Executable work uses an explicit immutable resolved context.

### 7.2 Environment validation

GF Wordbench may validate, according to the requested capability:

- selected language path;
- language source directory;
- RGL source root and RGL root when applicable;
- source containment and readability;
- GF executable;
- GF version;
- effective GF path components;
- output root;
- process working directories;
- optional validation profile;
- required source, scenario, input, gold, and artifact paths for the requested mode;
- required write permissions.

A missing optional or stronger-capability requirement MUST NOT invalidate a weaker capability that remains structurally sound.

### 7.3 Source selection

The framework selects GF source files using:

- the resolved language directory;
- source glob rules;
- include rules;
- exclude rules;
- focused target selection;
- optional profile checkpoints;
- optional profile entrypoints;
- validation mode;
- maximum-file limits.

Selection order MUST be deterministic.

The shared file-selection component owns enumeration, path safety, filtering, target resolution, deduplication, and ordering. Startup and run orchestration MUST NOT duplicate those rules.

### 7.4 Static scanning

Static scanning detects documented suspicious GF source patterns without claiming to replace GF compilation.

Scan findings remain separate from compile results.

Static scanning may remain available when GF is not installed.

### 7.5 Module compilation

GF Wordbench runs GF compilation with:

- explicit executable;
- explicit working directory;
- one resolved effective GF path;
- bounded timeout;
- stdout capture;
- stderr capture;
- exit-code capture;
- artifact collection;
- normalized diagnostic extraction.

GF remains authoritative for import and module resolution. Wordbench may use missing-module diagnostics to provide bounded path assistance, but it MUST NOT reimplement GF dependency semantics.

### 7.6 Failure classification

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

### 7.7 Source fingerprinting

Each relevant source file may be fingerprinted so a run can be associated with the exact source content that produced it.

### 7.8 Scenario execution

When an explicit scenario-capable profile is loaded, native `.gfs` scripts may exercise the resolved grammar through GF.

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

### 7.9 Golden-output testing

Normalized scenario output may be compared with reviewed `.gold` files declared by an explicit profile.

Normal validation MUST NOT rewrite gold files.

Gold updates require a deliberate, explicit workflow.

### 7.10 PGF build validation

Release validation may require construction and verification of configured `.pgf` artifacts.

A missing required PGF is a failure when the active release profile requires it.

### 7.11 Run comparison

A run may be compared with a compatible previous run.

Compatibility MUST include the relevant resolved language identity, source/profile contract, and schema policy. A previous run directory MUST NOT be used to reconstruct the current language identity.

The comparison identifies:

```text
unchanged
improved
regressed
new
removed
```

### 7.12 Reporting

Each finalized run produces the configured combination of:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- `top_errors.txt`;
- `manifest.json`;
- raw logs;
- detailed evidence;
- GF artifacts.

Reports MUST record the resolved language context and effective GF path evidence appropriate to their schema and privacy classification.

### 7.13 Contract validation

GF Wordbench may validate:

- Python interfile contracts;
- external-tool contracts;
- persisted-schema contracts;
- resolved-context contracts;
- optional validation-profile interfile contracts.

### 7.14 Schema validation and migration

Persisted formats use explicit schema identities and versions.

Supported legacy GF Audit formats and catalog-era Wordbench state or profiles may be migrated into canonical current formats through explicit tested policies.

### 7.15 Capability readiness

The resolved context reports independent capability status:

- `source-ready`: sources can be browsed, selected, and fingerprinted;
- `scan-ready`: selected sources can be statically scanned;
- `compile-ready`: GF, effective GF path, targets, and preflight permit compilation;
- `scenario-ready`: an explicit scenario profile and required assets are valid;
- `release-ready`: an explicit release profile and all release gates are satisfied.

Unavailable stronger capabilities MUST be reported explicitly and MUST NOT be converted into false success.

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

GF Wordbench defines four product modes. Every mode is gated by the capabilities of the published resolved context and any explicit validation profile.

### 9.1 `quick`

Purpose: rapid feedback during an edit loop.

Typical scope:

- one focused source target;
- static scan when scan-ready;
- file compilation when compile-ready;
- optional minimal smoke scenario when scenario-ready.

Expected characteristic: fastest meaningful validation supported by the current context.

### 9.2 `checkpoint`

Purpose: validate a completed module family or development milestone.

Typical scope:

- explicitly requested targets or configured profile checkpoints;
- relevant scenarios when configured;
- required gold comparisons when configured;
- compatible regression comparison.

A named configured checkpoint requires an explicit validation profile. The mode MUST fail clearly rather than invent checkpoint policy from filenames.

### 9.3 `diagnostic`

Purpose: investigate complex failures and cascades.

Typical scope:

- broad deterministic source inventory;
- verbose evidence;
- static scanning;
- individual compilation when compile-ready;
- detailed classification;
- extended diagnostics;
- full logs.

Diagnostic mode may remain partly useful at source-ready or scan-ready capability even when GF execution is unavailable. Unexecuted stages remain explicit.

### 9.4 `release`

Purpose: determine whether the active resolved language and explicit release profile are releasable.

Typical scope:

- required profile checkpoints;
- configured final entrypoints;
- PGF construction;
- all required scenarios;
- all required gold comparisons;
- release-specific artifact checks;
- schema and contract checks;
- final manifest;
- release criteria evaluation.

Release mode requires `release-ready` capability. It MUST NOT synthesize release policy from basic path discovery.

Legacy mode aliases may be supported during migration:

```text
file → quick
all  → diagnostic
```

Canonical output uses only the canonical mode names.

---

## 10. Status model

This section defines validation-result semantics. It does not classify documentation or implementation progress.

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

- resolved language context and optional profile;
- outcome;
- failed files;
- failed scenarios;
- regression changes;
- artifact locations.

### 11.3 AI-ready handoff

`AI_READY.md` provides a bounded, evidence-based diagnostic packet without rerunning GF.

It includes:

- resolved language and run context;
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

GF Wordbench uses coordinated anti-drift authorities. Base language startup and optional validation profiles have distinct contracts and MUST NOT become competing sources of runtime truth.

### 12.1 Documentation alignment lock

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
```

Locks cross-document product identity, authority order, ownership boundaries, canonical terminology, and correction rules.

### 12.2 Documentation correction ledger

```text
docs/DOCUMENTATION_CORRECTION_LEDGER.md
```

Coordinates parallel documentation corrections by repository path. It records correction work but does not define product behavior.

### 12.3 Framework interfile lock

```text
docs/INTERFILE_CONTRACT_LOCK.md
```

Locks Python-to-Python requests, responses, ownership, dependency directions, and the public boundary between the language probe and reused validation services.

### 12.4 External tool lock

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Locks commands, process behavior, GF integration, effective GF path use, artifact expectations, and tool compatibility.

### 12.5 Persisted schema lock

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Locks machine-readable formats, stable artifact names, schema versions, compatibility, migrations, and the persisted representation of resolved-language evidence and local convenience state.

### 12.6 Optional validation-profile interfile lock

An explicit profile may provide a profile-specific lock, for example:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

It locks relationships among configured GF modules, entrypoints, scenarios, inputs, gold files, artifacts, and profile documentation. It is authoritative only after that profile is explicitly associated with the resolved language context.

### 12.7 Validation-profile template lock

A reusable profile template may provide:

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

It locks a reusable, language-neutral validation-profile structure without making the template or an initialized profile mandatory for basic language loading.

The startup authority and supersession rules are defined by:

```text
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
```

These authorities define stable boundaries and correction ownership. They do not freeze internal changes that preserve the documented contracts.

---

## 13. User interfaces

### 13.1 CLI

The CLI is the complete automation-capable interface.

It MUST support every required validation capability without the GUI.

It MUST accept the same selected-language-path semantics as the GUI: one language directory or one `.gf` source file, plus explicit optional profile selection when advanced validation is requested.

Primary command:

```text
gf-wordbench
```

Final command and option names are governed by the CLI command registry and reference documentation.

### 13.2 GUI

The GUI provides an introduction surface for:

- opening a language directory;
- opening a GF source file;
- reopening the last successful selected path after revalidation;
- viewing probe diagnostics and capability status;
- attaching an optional validation profile;
- starting validation;
- viewing progress and reports;
- switching language when no run is active.

It MUST use the same language-probe, configuration, and audit application services as the CLI.

The GUI MUST NOT implement separate discovery, path-resolution, or validation semantics.

### 13.3 Windows launchers

Batch launchers may simplify startup.

They are convenience entrypoints and MUST NOT be the only supported execution path or provide hidden language defaults.

### 13.4 Filesystem interface

Selected GF source trees, optional validation profiles, and run directories are supported product interfaces.

Stable persisted formats are governed by the persisted-schema lock. Absolute selected paths remain machine-local state or permitted environment evidence rather than portable language identity.

---

## 14. Language and validation lifecycle

A language context and its optional validation profile move through these states.

### 14.1 Open and resolve

The user explicitly selects:

```text
one language directory
or
one .gf source file
```

Wordbench resolves and validates the candidate structure, then publishes one immutable `ResolvedLanguageContext`.

### 14.2 Explore

At `source-ready` or `scan-ready`, the user may:

- browse sources;
- select targets;
- inspect metadata;
- compute fingerprints;
- run static scans.

A complete project profile and GF executable are not required for every exploration operation.

### 14.3 Attach an optional profile

When checkpoint, scenario, regression, or release policy is needed, the user or automation explicitly attaches a compatible validation profile.

The profile may add:

- source filters;
- checkpoints;
- entrypoints;
- scenarios;
- inputs and golds;
- release targets and criteria;
- project documentation.

### 14.4 Baseline

Record the first trustworthy diagnostic run for a compatible resolved language context and profile contract.

A baseline may contain failures, but its environment, language identity, effective GF path, and evidence must be valid.

### 14.5 Develop

Use quick and diagnostic runs while implementing or repairing the language.

### 14.6 Checkpoint and stabilize

Validate explicit or profile-defined module families and resolve or document:

- temporary workarounds;
- fallbacks;
- warnings;
- blocked symbols;
- stale comments;
- incomplete scenarios.

### 14.7 Release

Attach or load an explicit release-capable profile, attain `release-ready`, run the complete release gate, and preserve its manifest and reports.

### 14.8 Switch, archive, or reopen

After active work is complete and no run is executing, the session may:

- switch to another explicit language path through a new resolution;
- reopen the same path through revalidation;
- archive or retain the optional validation profile and run history.

Old-language runtime state MUST NOT leak into the newly resolved context.

---

## 15. Release definition

A language is not release-ready merely because its directory can be opened or its selected `.gf` files compile.

A final release requires:

- one valid immutable resolved language context;
- one explicit compatible release validation profile;
- `release-ready` capability;
- every release criterion declared by that profile.

A release profile normally requires:

- supported GF toolchain;
- valid effective GF path;
- required modules present;
- required checkpoints passing;
- final entrypoints compiling;
- required grammar-load scenarios passing;
- required parse and linearization scenarios passing;
- required gold comparisons passing;
- required PGF artifacts present;
- no unresolved release blockers;
- contract checks passing;
- schema checks passing;
- complete run evidence;
- final manifest generated.

When the profile uses the legacy or template project layout, project-specific criteria may belong in:

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

Other supported profile formats may provide equivalent versioned authorities.

Without an explicit release profile, Wordbench may provide source, scan, compilation, and focused diagnostic capabilities, but it MUST report release readiness as unavailable rather than failed or passed.

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

Selected source paths, optional validation profiles, and scenarios are executable or semi-executable inputs and must be treated accordingly.

Reports must not expose secrets or complete environment dumps.

### 16.9 Performance

Quick validation must remain focused.

Expensive generation, exhaustive scenarios, and full diagnostics must be bounded and mode-appropriate.

---

## 17. Product boundaries

GF Wordbench is:

- a GF language development workbench;
- a path-resolved single-language runtime;
- a validation orchestrator;
- an evidence recorder;
- a regression-testing system when a compatible profile is supplied;
- a release-gating system when a release profile is supplied;
- an anti-drift framework;
- a reusable language-neutral application with optional validation-profile templates.

GF Wordbench is not:

- a replacement for GF;
- a new GF parser or type checker;
- a universal programming-language validator;
- a simultaneous multi-language dashboard;
- a cross-workspace orchestrator or portfolio aggregator;
- a mandatory global catalog of all RGL languages;
- a second GF dependency resolver;
- a language-theory decision engine;
- an automatic proof that linguistic behavior is correct;
- an automatic gold-file approval system;
- an AI system that edits source without review;
- a package manager for GF;
- a general CI platform.

Bounded discovery after an explicit user selection is permitted to construct a candidate context. Unbounded filesystem scanning, silent path repair, automatic profile adoption, and execution from an unvalidated candidate are outside the product contract.

Cross-workspace inventory, comparison, trends, and portfolio readiness belong to the independent `gf-portfolio` product. GF Wordbench exposes only public, versioned artifacts for optional read-only consumption and has no reverse dependency on `gf-portfolio`.

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

GF Wordbench retains those proven capabilities and combines them with the following product contracts:

- path-resolved language startup from one explicit source path;
- one immutable resolved language context per session runtime;
- progressive capability status;
- centralized effective GF path resolution;
- optional language-neutral validation profiles;
- native `.gfs` scenarios;
- golden-output testing;
- grammar execution validation;
- PGF release validation;
- explicit scenario results;
- artifact manifests;
- versioned persisted schemas;
- contract checking;
- release gates.

Migration must preserve working behavior before replacing it. Catalog-era startup and mandatory-project startup may be supported temporarily through bounded compatibility adapters, but new runtime authority belongs to the resolved context defined by ADR-0015.

---

## 19. Documentation authority

This overview defines the product at a high level.

Detailed authority is distributed as follows:

| Topic | Authoritative document or runtime authority |
|---|---|
| Cross-document alignment | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Documentation correction coordination | `docs/DOCUMENTATION_CORRECTION_LEDGER.md` |
| Product scope | `docs/SCOPE_AND_NON_GOALS.md` |
| Path-resolved startup and supersession | `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` |
| Architecture | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Python boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| GF and external tools | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Active runtime language identity | Published immutable `ResolvedLanguageContext` |
| Last selected path | Local application state, convenience only and revalidated |
| Effective GF path | One canonical GF path resolution reused by all GF operations |
| Source selection | `docs/validation/FILE_SELECTION.md` |
| Validation flow | `docs/validation/VALIDATION_PIPELINE.md` |
| Validation modes | `docs/validation/VALIDATION_MODES.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Validation-result status semantics | `docs/reference/STATUS_VALUES.md` |
| Optional validation profile | Explicit supported profile, including `project/project.toml` where used |
| Profile GF module relationships | Profile-specific interfile lock, where supplied |
| Profile validation and release criteria | Profile-specific validation and release documents, where supplied |

When this overview conflicts with an accepted ADR, normative lock, versioned schema, or the published resolved-context contract in its owned domain, the more specific authority governs.

---

## 20. Product guarantees

GF Wordbench satisfies its product definition through the following guarantees:

1. a standard GF language can be opened from one explicit directory or `.gf` file without modifying language-neutral framework logic;
2. no executable run begins before one immutable resolved language context is published;
3. only one language identity is active per runtime and per ordinary run;
4. language switching creates a new resolution and runtime and is blocked during an active run;
5. source selection, GF path resolution, preflight, compilation, and diagnostics reuse their canonical application services rather than parallel startup implementations;
6. quick, checkpoint, diagnostic, and release modes use one documented orchestration model and explicit capability gating;
7. GF commands are executed only through documented process contracts;
8. file and scenario results are both represented explicitly when those stages participate;
9. optional `.gfs` scenarios and `.gold` comparisons are supported through explicit validation profiles;
10. PGF release validation is supported through explicit release profiles;
11. all persisted machine formats are versioned;
12. legacy GF Audit state, catalog-era state, and supported profile formats have tested migration or compatibility policies;
13. contract and schema validation can be executed automatically;
14. CLI and GUI use the same language-probe and validation orchestration path;
15. every run preserves raw evidence and structured results;
16. release criteria can be evaluated without manual reconstruction when a release profile is active;
17. profile documentation and source contracts can be checked for drift;
18. weaker valid capabilities remain usable when stronger capabilities are unavailable;
19. application state is convenience only and cannot silently restore an executable context;
20. the framework test suite, integration suite, schema suite, and contract suite pass;
21. the framework contains no accidental dependency on a specific language, a mandatory runtime RGL catalog, or `gf-portfolio`.

---

## 21. Product statement

> GF Wordbench is a one-language-at-a-time GF development and release workbench that resolves an explicit source path into one immutable runtime context, reuses authoritative GF execution and existing Wordbench validation services, and adds progressive validation, evidence-preserving diagnostics, optional regression and release profiles, anti-drift contracts, and structured reporting.

Its purpose is not to make GF development abstract or bureaucratic.

Its purpose is to make a complex language implementation discoverable, understandable, testable, recoverable, and releasable while avoiding duplicate source/path logic and leaving cross-workspace portfolio aggregation to `gf-portfolio`.
