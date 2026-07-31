# GF Wordbench — Architecture Overview

**Document ID:** `GF-WB-ARCH-OVERVIEW`  
**Status:** Normative architectural overview  
**Applies to:** GF Wordbench framework, path-resolved language startup, optional validation profiles, generated run artifacts, and the public interoperability boundary  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Architecture version:** `2.1`  
**Last reviewed:** 2026-07-30  

---

## 1. Purpose

This document defines the high-level architecture of GF Wordbench.

It explains:

- what the system is;
- what the system is not;
- where each responsibility belongs;
- how the main components collaborate;
- how GF is invoked;
- how validation results and artifacts flow through the system;
- how one user-selected GF source location becomes one immutable resolved language context;
- how optional validation profiles add scenarios, golds, release gates and project policy without becoming startup prerequisites;
- which architectural constraints prevent drift and duplicate implementations.

This document is an overview. Accepted ADRs and the documentation alignment lock govern cross-document interpretation. `ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` governs language startup and supersedes the catalog-driven startup model. Detailed boundary contracts remain authoritative in:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

The project and template locks apply when an optional validation profile uses those layouts. They do not make `project/project.toml` mandatory for opening a language source tree.

When documents appear to disagree, use the precedence defined by `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`. This overview must summarize owner documents rather than create a competing contract.

---

## 2. Product definition

GF Wordbench is a local development, validation, diagnostic and release workbench for one active Grammatical Framework language context at a time.

A normal interactive session contains:

```text
one permanent Python framework
zero or one immutable resolved language context
zero or one optional validation profile
zero or more generated validation runs
```

The intended basic workflow is:

```text
start GF Wordbench
        ↓
select one GF language directory or one .gf file
        ↓
resolve and validate the source context through existing Wordbench services
        ↓
browse, scan or compile according to available capabilities
        ↓
optionally load a validation profile for scenarios, golds and release policy
        ↓
produce evidence and reports
```

Normal startup does not require:

```text
rgl-language-catalog.json
language.toml
project/project.toml
scenario files
gold files
language-specific Wordbench documentation
```

Those assets may exist as maintenance inventories or optional validation profiles. They are not authorities for basic source-ready or scan-ready startup.

GF Wordbench does not keep several active language contexts concurrently. It may switch languages only by disposing the current runtime, returning to the introduction surface and resolving a new explicit source selection. Every ordinary run belongs to exactly one resolved language context.

A multi-language GF grammar may still be compiled when the selected source context and explicit target define such a grammar. The architectural rule concerns Wordbench runtime identity and evidence isolation, not GF's language capabilities.

Multi-workspace registration, cross-project aggregation, portfolio readiness, comparison and navigation belong to the independent companion product `gf-portfolio`. Interoperability is optional and uses public versioned GF Wordbench artifacts only.

```text
gf-portfolio → public versioned GF Wordbench artifacts
GF Wordbench -X→ gf-portfolio runtime, code, private schemas, storage, or configuration
```

GF Wordbench must start, validate, report, release and pass its tests without `gf-portfolio` installed or reachable.

---

## 3. Architectural goals

The architecture is designed to achieve the following goals.

### 3.1 Correctness

- Use GF as the authority for GF semantics.
- Preserve raw tool evidence.
- Separate execution failures from language validation failures.
- Make validation results deterministic and reviewable.
- Require explicit release criteria.

### 3.2 Reusability

- Keep the framework independent of any active language.
- Resolve language-specific source facts from one explicit user-selected path.
- Reuse existing selection, path, preflight, GF and diagnostic services.
- Keep optional validation policy in explicit profiles rather than framework defaults.
- Provide `templates/project/` only for optional advanced validation-profile initialization.
- Make language replacement possible without rewriting framework code.

### 3.3 Traceability

- Record the resolved configuration used for each run.
- Record the executable, arguments, working directory, timeout, and outputs.
- Link normalized diagnostics to raw evidence.
- Catalog generated artifacts in a manifest.
- Keep previous-run comparison explicit.

### 3.4 Anti-drift

- Give each responsibility and artifact one owner.
- Use typed shared models at component boundaries.
- Version persisted schemas.
- Lock provider-consumer relationships.
- Prohibit duplicated path construction and duplicated execution logic.

### 3.5 Maintainability

- Prefer cohesive modules with narrow responsibilities.
- Keep CLI and GUI thin.
- Keep reports passive.
- Keep process handling centralized.
- Add complexity only when it corresponds to a stable responsibility.

### 3.6 Portability

- Support Windows as a first-class platform.
- Avoid dependence on shell-specific behavior.
- Normalize persisted paths.
- Keep machine-local selected paths separate from portable language identity and optional profile configuration.
- Avoid mandatory network services.

---

## 4. Non-goals

The architecture does not include:

- a replacement GF parser;
- a replacement GF type checker;
- a replacement GF module resolver;
- a replacement GF runtime;
- a competing PGF implementation;
- a general-purpose integrated development environment;
- a hosted validation service;
- a mandatory database;
- a mandatory web server;
- a package marketplace;
- an unrestricted runtime plugin system;
- simultaneous execution of unrelated active language contexts;
- a Wordbench-owned portfolio registry of several workspaces;
- cross-workspace or multilingual portfolio aggregation;
- a mandatory dependency on `gf-portfolio` or another external product;
- automatic linguistic design decisions;
- automatic acceptance of changed gold outputs;
- report generators that rerun validation stages.

These capabilities may exist in external tools or future companion products, but they are outside the GF Wordbench core.

---

## 5. System context

```text
┌─────────────────────────────────────────────────────────────┐
│                         User or CI                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                explicit directory or .gf file
                              │
                     CLI or desktop GUI
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      GF Wordbench                           │
│                                                             │
│ language probe → resolved context → validation → reporting │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
     selected GF source tree               run artifacts
                │                               │
┌───────────────▼──────────────┐   ┌────────────▼─────────────┐
│ .gf modules and optional     │   │ raw logs, summaries,     │
│ profile/scenario/gold assets │   │ manifests, .gfo, .pgf    │
└───────────────┬──────────────┘   └──────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│         Grammatical Framework executable and RGL           │
└─────────────────────────────────────────────────────────────┘
```

External actors are:

- the user;
- CI or automation;
- the selected GF source tree;
- an optional explicit validation profile;
- the GF executable;
- the GF Resource Grammar Library;
- the local filesystem;
- optional explicitly contracted tools;
- optional consumers of public versioned artifacts, including `gf-portfolio`.

The core architecture does not require remote services. Optional consumers remain outside the Wordbench runtime boundary and cannot control resolved language identity, validation semantics or release outcomes.

---

## 6. Authority boundaries

### 6.1 GF is authoritative for

- GF syntax;
- GF type checking;
- module loading;
- GF dependency resolution;
- `.gf` to `.gfo` compilation;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- native GF diagnostics.

### 6.2 GF Wordbench is authoritative for

- selected-path normalization and containment;
- bounded language-candidate resolution;
- deterministic source selection through the existing selection service;
- centralized GF path resolution;
- capability classification;
- optional validation-profile loading and conflict checks;
- executable selection;
- command construction;
- process launch;
- working-directory selection;
- environment preparation;
- timeouts and cancellation;
- stdout and stderr capture;
- static source checks;
- scenario coordination;
- output normalization;
- assertion and gold comparison;
- failure classification;
- run history;
- artifact collection;
- report production;
- schema migration;
- release gates.

### 6.3 Selected GF source tree is authoritative for

- observable source layout;
- available `.gf` files;
- exact module filenames;
- source contents;
- source-local RGL conventions;
- source revision and fingerprints.

The source tree does not by itself declare mandatory scenarios, golds or release policy.

### 6.4 Resolved language context is authoritative for

- the one active language identity of the session;
- selected path and path kind;
- language directory;
- resolved RGL source root;
- focused target, when one file was selected;
- detected module suffix, when unambiguous;
- available entrypoint candidates;
- effective source inventory or inventory reference;
- GF path requirements and provenance;
- capability statuses;
- runtime language and source facts used by run construction.

The context is immutable. Changing its source selection, identity or path requirements requires a new resolution and a new runtime.

### 6.5 Optional validation profile is authoritative for

- explicit source include and exclude policy beyond the base source context;
- required entrypoints and checkpoints;
- required and optional scenarios;
- expected gold output;
- PGF targets and expected artifacts;
- linguistic architecture documentation;
- category and lincat contracts;
- release criteria;
- known language-specific limitations.

An optional profile may use `project/project.toml` or another versioned profile contract. It cannot contradict or replace the resolved source context.

### 6.6 Framework maintainers are authoritative for

- framework architecture;
- shared models;
- process semantics;
- persisted schemas;
- public command behavior;
- diagnostic vocabulary;
- artifact layout;
- compatibility policy;
- framework release policy.

### 6.7 `gf-portfolio` is authoritative for

- registration of several isolated Wordbench workspaces or published runs;
- cross-workspace and multilingual aggregation;
- portfolio readiness, comparison and navigation;
- consumer-specific ingestion adapters for Wordbench public artifacts.

Wordbench documentation may define the artifacts it publishes. It must not define `gf-portfolio` internals, private storage, registry schemas or runtime behavior.

---

## 7. Repository partitions

The architecture distinguishes the Wordbench repository, externally selected GF sources, optional validation profiles and generated runs.

```text
GF_Wordbench/
├── src/gf_wordbench/       permanent Python framework
├── docs/                   permanent framework documentation
├── tests/                  framework and contract tests
├── project/                optional validation-profile example
├── templates/project/      optional profile template
└── <output-root>/          generated run directories

<selected-source-tree>/
└── <language-directory>/   user-selected GF sources
```

### 7.1 Permanent framework

The permanent framework contains:

- application assembly;
- path-resolved language probing;
- configuration and schema loading;
- orchestration;
- deterministic source selection;
- static scanning;
- GF path resolution and process execution;
- scenario execution;
- diagnostics;
- result models;
- report generation;
- state handling;
- CLI and GUI interfaces.

It must not contain hard-coded active-language paths, module names or linguistic policy.

### 7.2 Selected language source tree

The selected source tree is external input. A standard RGL selection may be:

```text
<rgl-root>/src/english
<rgl-root>/src/english/LangEng.gf
```

Wordbench treats normal startup as read-only for the selected source tree. It derives a bounded candidate, validates it through existing services and publishes one immutable resolved language context.

### 7.3 Optional validation profile

An optional profile may contain:

```text
project/
├── project.toml
├── README.md
├── docs/
└── validation/
    ├── scenarios/
    ├── gold/
    └── inputs/
```

The profile adds explicit validation and release policy. It is not required to browse, select, fingerprint or statically scan standard GF sources.

### 7.4 Project template

`templates/project/` provides generic initialization material for optional validation profiles. It contains:

- generic placeholders;
- generic instructions;
- no active-language decisions;
- no copied local paths;
- no stale gold expectations;
- no generated artifacts.

The template is never rendered implicitly during normal startup.

### 7.5 Generated runs

Run directories contain evidence and derived reports.

They are outputs, not startup configuration.

A run must be reproducible from:

- the resolved language-context evidence;
- the selected source revision or fingerprints;
- the resolved run configuration;
- the GF version;
- the captured command contracts;
- the optional validation-profile revision and digest;
- the scenario and gold revisions when those assets participate.

---

## 8. Hexagonal modular monolith

GF Wordbench is one deployable modular monolith with five stable functional modules:

```text
projects
runs
validation
diagnostics
reporting
```

| Module | Architectural ownership |
|---|---|
| `projects` | Selected-path language probing, resolved language identity, source-boundary publication, optional validation-profile loading, template initialization, and source fingerprints. |
| `runs` | Run identity, lifecycle, budgets, cancellation, finalization, history, and release-gate coordination. |
| `validation` | File selection, static scanning, GF-backed compilation, PGF construction, scenarios, normalization, assertions, and gold comparison. |
| `diagnostics` | Diagnostic vocabulary, normalization, causal classification, known-pattern handling, and controlled diagnostic-tool registry. |
| `reporting` | Machine and human reports, artifact manifests, raw-log publication, and public versioned exports. |

Each module follows the same architectural rings:

```text
domain
application
ports
adapters
entrypoints
bootstrap
```

The domain and application rings own Wordbench rules. Ports describe external or unstable boundaries. Adapters implement filesystem, process, GF, persistence, and presentation concerns. Entrypoints translate CLI or GUI requests into application calls. Bootstrap assembles the product.

Public intermodule APIs must remain narrow and typed. A module must not depend on another module's private implementation. External processes, GF syntax, persisted formats, and interface frameworks must not leak into the domain model.

The detailed sections below describe responsibilities within these modules and rings; they do not define a second competing layer model.

---

## 9. Entrypoint adapters

### 9.1 Command-line interface

Architectural owner:

```text
entrypoints.cli
```

Responsibilities:

- define CLI syntax;
- validate syntactic argument constraints;
- accept one explicit language directory or `.gf` path;
- accept an optional explicit validation-profile path;
- invoke the shared language-probe application service;
- invoke the run orchestrator only after a context is resolved;
- render concise terminal and structured probe output;
- convert completed outcomes into documented process exit codes.

The CLI must not:

- enumerate source trees independently;
- infer a language through CLI-only rules;
- launch GF directly;
- parse GF diagnostics directly;
- construct report files;
- duplicate profile-loading rules;
- invent its own artifact paths.

### 9.2 Desktop GUI

Architectural owner:

```text
entrypoints.gui
```

Responsibilities:

- show an introduction surface before the main runtime;
- collect a language directory or `.gf` file selection;
- offer revalidation of the last successful selected path;
- display the resolved language context and capability statuses;
- request explicit user choice when probe results are ambiguous;
- start a run through the same application boundary as the CLI;
- display progress and completed results;
- persist disposable local preferences;
- link to generated artifacts.

The GUI must not:

- enumerate or classify GF files in widgets;
- resolve GF paths in view models;
- launch GF from widgets;
- own language or profile semantics;
- mutate gold files during a normal run;
- derive results by scraping human reports;
- hold a second implementation of probe or validation logic.

### 9.3 Shared interface rule

CLI and GUI are alternative front ends over the same language-probe, configuration and run application services.

Equivalent explicit selections and profile inputs must produce equivalent resolved contexts, diagnostics and validation behavior.

Interface differences may affect presentation and interactive remediation, not source identity, path resolution or audit semantics.

---

## 10. Bootstrap and composition

Architectural owner:

```text
bootstrap
```

Collaborating boundaries:

```text
projects.application
runs.application
validation.application
diagnostics.application
reporting.application
ports
adapters
```

Bootstrap has two composition phases.

### 10.1 Startup composition

Responsibilities:

- load framework defaults;
- load disposable local application state;
- construct the introduction or CLI probe runtime;
- wire the filesystem, selection, GF-path, preflight and diagnostic dependencies required by `LanguageProbeService`;
- avoid constructing the main language runtime before one context resolves.

### 10.2 Language-runtime composition

Responsibilities:

- receive one immutable `ResolvedLanguageContext`;
- load an optional explicitly selected validation profile;
- validate profile-to-context consistency;
- apply local environment configuration;
- apply explicit CLI or GUI run overrides;
- construct immutable or controlled run configuration;
- construct run paths;
- select required services;
- reject invalid combinations before execution.

Bootstrap is a composition boundary.

It must not:

- enumerate language files itself;
- perform validation stages;
- contain language-specific defaults;
- generate reports;
- call GF directly;
- render templates during normal startup;
- silently load the first `project.toml` found in an ancestor;
- silently bypass release requirements.

---

## 11. Configuration model

Configuration is divided by ownership and capability.

### 11.1 Framework defaults

Architectural owner:

```text
bootstrap configuration provider
```

Examples:

- application name;
- package version;
- default timeout policy;
- supported schema versions;
- default output conventions;
- framework-wide limits;
- supported standard source-layout predicates;
- bounded discovery limits.

Framework defaults must not name an active language, module or machine-local source path.

### 11.2 Explicit selected path

Normative source for startup intent:

```text
one user- or caller-supplied directory or .gf file
```

Examples:

```text
C:/work/gf-rgl/src/english
C:/work/gf-rgl/src/english/LangEng.gf
```

The selected path is machine-local input. It is normalized and validated, not treated as a portable identity.

### 11.3 Resolved language context

Architectural owner:

```text
projects.application through LanguageProbeService
```

The context contains the validated language and source facts needed by the runtime, including selected-path evidence, language directory, RGL source root, focused target, module-suffix evidence, source inventory, GF-path requirements and capability statuses.

It is constructed once and is immutable for the lifetime of the language runtime.

### 11.4 Optional validation profile

Possible normative source:

```text
an explicitly selected versioned profile
including project/project.toml when used
```

Examples of profile-owned facts:

- source inclusion and exclusion policy beyond the base context;
- required entrypoints;
- required checkpoints;
- GF path requirements beyond standard resolution;
- required and optional scenarios;
- inputs and golds;
- PGF and release requirements.

A profile is optional for source-ready and scan-ready operation. It cannot contradict the resolved source context.

### 11.5 Local application state

Architectural owner:

```text
local-state persistence adapter
.gf_wordbench_state.json
```

Examples:

- last successful selected language path;
- last explicitly selected validation profile;
- local GF executable;
- output root;
- last selected mode;
- display preferences;
- previous run pointer.

Local state is disposable and non-authoritative. Deleting it must not alter GF sources or validation profiles. Remembered paths are fully revalidated before reuse.

### 11.6 Explicit run overrides

CLI or GUI values may override documented local defaults.

They must not replace selected-source identity, create path escapes or silently disable mandatory profile release gates.

### 11.7 Configuration precedence

Startup resolution follows:

```text
framework defaults
        ↓
explicit selected path or revalidated remembered path
        ↓
bounded candidate resolution
        ↓
ResolvedLanguageContext
        ↓
optional explicit validation profile
        ↓
local environment/state
        ↓
explicit invocation overrides
        ↓
cross-field and capability validation
        ↓
resolved RunConfig
```

The source and provenance of each significant resolved value must remain inspectable.

---

## 12. Domain models and published contracts

Each functional module owns its domain models. Cross-module data is exposed only through narrow, typed published contracts. A central catch-all model module must not become a dependency shortcut.

The contract model set includes, at minimum:

```text
AppConfig
LanguageProbeRequest
LanguageCandidate
LanguageProbeDiagnostic
ResolvedLanguageContext
CapabilityStatus
ValidationProfile
ProjectConfig
RunConfig
RunBudget
RunPaths
GfOperationRequest
GfOperationResult
ProcessRequest
ProcessResult
ScanCounts
SourceFingerprint
CompileSummary
FileResult
ScenarioResult
DiagnosticToolSpec
DiffEntry
ArtifactRecord
RunResult
```

### 12.1 Model responsibilities

Shared models:

- define stable component boundaries;
- make status and path semantics explicit;
- prevent consumers from depending on private dictionaries;
- centralize serialization meaning;
- provide safe defaults for optional fields;
- distinguish runtime-only fields from persisted fields.

### 12.2 No dynamic contract rule

Consumers must not add undocumented attributes to shared result objects.

A new cross-component field requires:

- model update;
- producer update;
- consumer review;
- serialization review;
- tests;
- contract update when externally visible.

### 12.3 Internal versus persisted models

Internal Python models may use:

- `Path`;
- enums;
- dataclasses;
- richer process objects.

Persisted schemas use canonical serializable forms defined in `PERSISTED_SCHEMA_LOCK.md`.

Serialization occurs at designated boundaries, not opportunistically throughout the codebase.

---

## 13. Run orchestration

Architectural owner:

```text
runs.application
```

The orchestrator coordinates the run but does not absorb stage implementation.

Responsibilities:

1. require one immutable resolved language context;
2. validate capability compatibility and the resolved run configuration;
3. create the run directory;
4. initialize logging and run metadata;
5. establish the global run budget, stage budgets, and finalization reserve;
6. probe GF when required by the requested capability;
7. select files and optional profile-owned checkpoints, entrypoints, and scenarios;
8. invoke validation stages in mode-defined order;
9. collect stage results;
10. classify causal relationships;
11. compare with the previous compatible language-context run;
12. evaluate applicable release gates;
13. finalize the run through the designated finalizer;
14. invoke report writers and manifest creation within the reserved budget;
15. return one authoritative `RunResult`.

### 13.1 Run budget and finalization

Every run has:

- one global duration budget;
- bounded budgets for process-backed and non-process stages;
- a reserved budget for child-process cleanup, result persistence, report completion, and manifest publication.

Timeout, cancellation, or a late failure must still produce a terminal, inspectable run state when safe persistence remains possible. The finalizer writes available results atomically, preserves completed evidence, records incomplete stages explicitly, terminates owned child processes, and never publishes an incomplete release as `OK`.

The orchestrator must not:

- implement GF command details;
- scan source text directly;
- parse GF diagnostics directly;
- render report prose;
- write gold files;
- hide stage failures;
- continue past an unsafe configuration failure.

---

## 14. Validation stage architecture

Validation is a pipeline of independent stages coordinated by the orchestrator.

```text
resolved-language and capability validation
        ↓
optional profile validation
        ↓
tool/version probe when required
        ↓
file discovery
        ↓
static scanning
        ↓
module compilation
        ↓
entrypoint / PGF build
        ↓
scenario execution
        ↓
normalization and assertions
        ↓
gold comparison
        ↓
classification
        ↓
previous-run comparison
        ↓
release-gate evaluation
        ↓
reports and manifest
```

Not every mode executes every stage.

### 14.1 Stage contract

Each stage must define:

- inputs;
- outputs;
- owner;
- allowed side effects;
- status behavior;
- raw evidence;
- timeout policy when process-backed;
- deterministic ordering;
- failure-containment behavior;
- tests.

A stage must not modify another stage’s result after ownership has transferred, except through an explicit aggregation or classification step.

---

## 15. File discovery and language probing

Architectural owners:

```text
projects.application       language-probe orchestration
validation.application     source enumeration and target selection
```

The language probe interprets one explicit selected path and coordinates existing public services. It does not implement a second source scanner.

The existing selection service owns:

- source-root validation;
- candidate `.gf` enumeration;
- readability and regular-file checks;
- path containment;
- inclusion and exclusion rules;
- maximum-file constraints;
- deduplication;
- deterministic ordering;
- explicit target resolution;
- module-name expectation from filenames;
- exclusion reasons.

The probe owns only:

- candidate language-directory derivation from the selected path;
- bounded RGL source-root detection through selected-path ancestors;
- classification of standard module-role candidates;
- collection of structural diagnostics;
- decisions about when explicit user input is required;
- construction of the immutable resolved language context.

Run-time file selection consumes the resolved context and optional profile policy to:

- select a focused file for a file-based request;
- select target files for `quick`;
- select explicit profile checkpoints for `checkpoint`;
- select the resolved language source scope for `diagnostic`;
- select explicit profile release scope for `release`;
- return deterministic paths relative to the resolved source root or profile root as appropriate.

File discovery and probing must not:

- build a competing GF import graph;
- launch GF directly;
- parse GF diagnostics independently;
- write reports;
- enumerate every RGL language during normal startup;
- add every RGL source directory to the GF path;
- choose an ambiguous suffix or entrypoint silently.

---

## 16. Static scanning

Architectural owner:

```text
validation.application
```

Responsibilities:

- read GF source safely;
- distinguish code from comments and strings;
- detect documented suspicious source patterns;
- count and describe findings;
- preserve a scan log;
- return structured scan results.

Static scanning is advisory or policy-driven evidence.

It is not a substitute for GF compilation.

A scanner finding must not be described as a GF type error unless GF independently reports such an error.

Language-specific lint rules must be declared by an explicit validation profile or implemented through an explicit extension boundary.

---

## 17. GF anti-corruption and process boundary

Canonical application port:

```text
GfToolPort
```

Canonical adapters include the designated GF anti-corruption layer and the shared process runner, such as:

```text
app/adapters/gf/
app/utils/process_runner.py
```

Concrete paths may evolve, but the port and ownership boundary remain stable.

### 17.1 GF anti-corruption responsibilities

All GF interactions pass through `GfToolPort` and the dedicated anti-corruption layer. This boundary owns:

- typed GF operation requests;
- operation-specific command construction;
- executable and version differences;
- GF search-path and working-directory translation;
- stdin and `.gfs` invocation details;
- expected `.gfo`, `.pgf`, and other GF artifact verification;
- interpretation of GF stdout, stderr, exit state, and native diagnostics;
- links from interpreted results to preserved raw evidence.

Validation stages express the operation they require. They must not embed GF command syntax, version branches, or private parsing rules.

### 17.2 Process runner responsibilities

The process runner owns:

- shell-free process launch;
- ordered argument execution;
- explicit working directory;
- controlled environment overlay;
- stdin handling;
- timeout enforcement;
- cancellation handling;
- child-process termination policy;
- separate stdout and stderr capture;
- duration and exit-code capture;
- launch-error capture;
- output-size policy;
- raw process result creation.

The process runner is tool-neutral. It does not assign GF meaning, validation status, or causal classification.

### 17.3 No duplicate execution logic

CLI, GUI, reports, classifiers, project loaders, and validation stages must not launch GF directly.

All GF execution passes through `GfToolPort`, its anti-corruption adapter, and the shared process boundary.

---

## 18. GF compilation

Architectural owner:

```text
validation.application
```

Responsibilities:

- select the configured compilation subject and required outcome;
- submit a typed compilation operation through `GfToolPort`;
- consume the returned process evidence, GF diagnostics, and artifact verification;
- preserve references to raw stdout and stderr;
- produce a `CompileSummary`;
- hand structured diagnostics to classification and reporting.

Compilation status must consider:

- launch success;
- timeout;
- exit code;
- GF diagnostics;
- required artifact existence;
- contract completeness.

A zero exit code alone is not sufficient when a required artifact is missing.

---

## 19. PGF construction

Architectural owner:

```text
validation.application
```

Responsibilities:

- select explicit profile-owned release entrypoints;
- submit a typed PGF-build operation through `GfToolPort`;
- require the anti-corruption layer to verify the expected `.pgf`;
- catalog the verified artifact;
- return a process-backed build result with raw-evidence references.

PGF construction is required only when an explicit validation profile and validation mode require it.

The PGF builder must not:

- decide language architecture;
- choose undocumented entrypoints;
- accept an absent PGF as success;
- rewrite PGF contents.

---

## 20. Scenario execution

Architectural owner:

```text
validation.application
```

Scenario sources:

```text
project/validation/scenarios/*.gfs
```

Related assets:

```text
project/validation/inputs/
project/validation/gold/
```

Responsibilities:

- load the configured scenario registry;
- validate scenario paths and identifiers;
- submit the native `.gfs` operation through `GfToolPort`;
- apply the scenario timeout and output limits through the shared run budget;
- preserve separate stdout and stderr references;
- verify required markers and sections;
- normalize stable output;
- compare with gold when configured;
- catalog scenario artifacts;
- return one `ScenarioResult` per scenario.

The scenario runner must not implement a second GF shell.

Native `.gfs` scripts remain the execution language.

---

## 21. Output normalization

Architectural owner:

```text
validation.application
```

Normalization is exposed through an explicit versioned contract.

Responsibilities:

- normalize CRLF to LF;
- remove ANSI control sequences;
- replace explicitly unstable environment paths with stable tokens;
- remove explicitly declared unstable timing values;
- preserve linguistically meaningful Unicode and punctuation;
- preserve trees, strings, counts, missing-function lists, and morphology output;
- write a versioned normalized output;
- retain a reference to raw evidence.

Normalization must be:

- deterministic;
- versioned;
- tested;
- narrow;
- reversible only where the contract requires it.

A normalization change that affects gold comparison is a contract change.

---

## 22. Diagnostics and classification

Diagnostics are divided into two architectural responsibilities.

### 22.1 Diagnostic normalization

Architectural owner:

```text
diagnostics.application
```

Responsibilities:

- inspect stdout and stderr together;
- normalize known GF diagnostic structures;
- identify error kinds;
- preserve source location and original evidence;
- distinguish launch, timeout, tool, contract, artifact, and configuration failures.

It must not decide upstream versus downstream causality.

### 22.2 Causal classification

Architectural owner:

```text
diagnostics.domain
```

Responsibilities:

- classify results as direct, downstream, ambiguous, noise, skipped, or okay;
- identify known blockers;
- preserve uncertainty;
- avoid turning heuristic relationships into unsupported certainty.

### 22.3 Orthogonal result dimensions

The architecture keeps four dimensions distinct.

```text
validation_status
execution_state
error_kind
diagnostic_class
```

Canonical meanings:

```text
validation_status:
  OK | FAIL | ERROR | SKIPPED

execution_state:
  completed | timed_out | cancelled | launch_failed

error_kind:
  OK | OTHER | TYPE | SYNTAX | INTERNAL | TIMEOUT |
  SCRIPT | CONFIG | IO | TOOL | CONTRACT | ARTIFACT |
  NORMALIZATION | GOLD

diagnostic_class:
  ok | direct | downstream | ambiguous | noise | skipped
```

A process layer does not assign direct or downstream causality.

A classifier does not rewrite raw process evidence.

### 22.4 Diagnostic tool registry

Executable diagnostic tools are controlled by a static allowlist. Each registered tool contract declares:

- stable tool identity and owner;
- executable resolution policy;
- permitted commands and flags;
- input and output contracts;
- timeout and output-size limits;
- mutability and filesystem effects;
- evidence role and trust level;
- whether the result is normative, advisory, or informational.

Arbitrary command execution and unrestricted runtime plugins are prohibited. AI-assisted tools are optional, visible, and non-normative; their output cannot replace GF evidence or release criteria.

---

## 23. Fingerprints and regression comparison

### 23.1 Source fingerprints

Architectural owner:

```text
projects.domain
```

Responsibilities:

- compute deterministic source fingerprints;
- use SHA-256 for canonical output;
- record size and modification metadata;
- support change detection without replacing version control.

### 23.2 Previous-run comparison

Architectural owner:

```text
runs.application
```

Responsibilities:

- locate a previous compatible summary;
- load it through the schema reader;
- compare stable subject identities;
- classify changes as unchanged, improved, regressed, new, or removed;
- remain deterministic;
- tolerate absence of a previous run.

The diff component must not compare Markdown prose.

`summary.json` is the machine source of truth.

---

## 24. Validation modes

GF Wordbench defines four validation modes.

### 24.1 Quick

Purpose:

- validate one selected file or a tightly bounded target;
- provide fast developer feedback.

Expected scope:

- configuration validation;
- relevant file discovery;
- static scan;
- targeted compile;
- limited diagnostics;
- concise reports.

### 24.2 Checkpoint

Purpose:

- validate a declared architectural layer.

Expected scope:

- configured checkpoint modules;
- their required supporting stages;
- selected required scenarios;
- regression comparison.

### 24.3 Diagnostic

Purpose:

- collect broad evidence for investigation.

Expected scope:

- all selected source files;
- static scans;
- compilation;
- extended diagnostics;
- optional diagnostic scenarios;
- detailed reports.

Diagnostic mode may continue after isolated language failures when evidence collection remains safe.

### 24.4 Release

Purpose:

- prove all project-defined release criteria.

Expected scope:

- clean configuration;
- required source validation;
- entrypoint validation;
- required PGF build;
- all required scenarios;
- gold comparison;
- required artifact verification;
- manifest integrity;
- no unresolved release blockers.

Release mode is strict.

Mandatory release requirements cannot be silently disabled by state or presentation defaults.

---

## 25. Run result aggregation

`RunResult` is the authoritative in-memory aggregate of a completed or terminal run.

It includes:

- resolved configuration;
- run paths;
- timing;
- GF version;
- file results;
- scenario results;
- PGF build results when applicable;
- totals;
- diagnostic groups;
- top errors;
- diff entries;
- release-gate outcomes;
- artifact records;
- framework errors;
- overall status.

### 25.1 Overall status

```text
ERROR
```

means GF Wordbench could not execute or interpret a required operation.

```text
FAIL
```

means required validation executed but did not meet its criterion.

```text
OK
```

means every required criterion passed.

`SKIPPED` applies to individual operations, not normally to a finalized required release run.

### 25.2 Partial evidence

A terminal framework error must not erase evidence already captured.

The run result should preserve completed-stage results and identify the stage that prevented completion.

---

## 26. Reporting architecture

Architectural owner:

```text
reporting.application
```

Filesystem and format-specific writers are reporting adapters.

### 26.1 Report rules

Reports:

- consume completed results;
- do not rerun validation;
- do not launch GF;
- do not silently modify raw evidence;
- use owned paths from `RunPaths`;
- preserve deterministic ordering;
- fail independently where possible.

### 26.2 Machine summary

```text
summary.json
```

is the primary persisted run record.

It supports:

- automation;
- GUI reload;
- previous-run comparison;
- migration;
- report verification;
- historical analysis.

### 26.3 Human summary

```text
summary.md
```

provides a concise reviewable explanation.

It is not a machine schema.

### 26.4 AI handoff

```text
AI_READY.md
```

provides:

- bounded evidence;
- direct/downstream separation;
- failing files and scenarios;
- artifact references;
- no second execution.

### 26.5 Manifest

```text
manifest.json
```

catalogs completed-run artifacts with:

- role;
- path;
- size;
- SHA-256;
- owner;
- required status.

---

## 27. Run artifact architecture

Canonical run layout:

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

### 27.1 Artifact classes

#### Raw evidence

Examples:

- stdout;
- stderr;
- scan logs;
- command records;
- process metadata.

Raw evidence is immutable after capture.

#### Tool-generated artifacts

Examples:

- `.gfo`;
- `.pgf`;
- GF-generated exports.

GF creates them. GF Wordbench catalogs or copies them without changing their meaning.

#### Derived artifacts

Examples:

- normalized scenario output;
- gold diff;
- summary;
- diagnostic aggregation.

Derived artifacts retain references to source evidence.

### 27.2 Ownership rule

Every artifact has one writer.

Readers do not rewrite artifacts owned by another component.

---

## 28. Persistence architecture

Canonical persisted schemas include:

```text
gf-wordbench.project/1.0                 optional validation profile
gf-wordbench.app-state/1.1               machine-local convenience state
gf-wordbench.run-summary/1.0
gf-wordbench.artifact-manifest/1.0
gf-wordbench.scenario-output/1.0
gf-wordbench.scenario-gold/1.0
```

The resolved language context is a runtime model. Persisted run schemas record its portable identity, source-root-relative facts, effective GF path evidence and optional profile identity. They do not persist an executable context as future startup authority.

Persistence rules include:

- explicit schema identity;
- explicit schema version;
- UTF-8;
- deterministic ordering;
- portable source-root-relative, profile-relative and run-relative paths where applicable;
- explicit UTC timestamps;
- atomic writes;
- tested migration;
- no secret persistence;
- no automatic trust of stale absolute selected paths.

Application state may contain machine-local absolute paths such as `last_selected_language_path`. Those paths are revalidated on every load and are not portable project facts.

No new unversioned machine-readable format may be introduced.

---

## 29. Path architecture

Paths belong to four classes.

### 29.1 Selected source paths

Examples:

```text
C:/work/gf-rgl/src/english
C:/work/gf-rgl/src/english/LangEng.gf
```

Rules:

- supplied explicitly or restored from disposable local state;
- may be absolute machine-local paths;
- normalized and containment-checked before use;
- revalidated on every load;
- recorded only in permitted local evidence;
- converted to portable source-root-relative facts for interoperable artifacts;
- never guessed through an unbounded filesystem search.

### 29.2 Validation-profile paths

Examples:

```text
validation/scenarios/parse.gfs
validation/gold/parse.gold
```

Rules:

- relative to the explicit profile root;
- `/` separators in canonical persistence;
- no path escape;
- portable across profile clones;
- optional for source-ready and scan-ready operation.

### 29.3 Run-owned paths

Examples:

```text
raw/compile/LangEng.stdout.txt
artifacts/pgf/Lang.pgf
```

Rules:

- relative to the run directory in summaries and manifests;
- owned by `RunPaths`;
- never reconstructed through duplicated filename logic.

### 29.4 Environment paths

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
```

Rules:

- may be absolute;
- resolved before execution;
- recorded according to local-evidence and redaction policy;
- not stored as portable validation-profile facts;
- reused through one centralized path resolution.

---

## 30. Dependency rules

### 30.1 Allowed high-level direction

```text
CLI ─┐
     ├→ startup runtime → LanguageProbeService → public selection/path/preflight contracts
GUI ─┘                                      │
                                             ↓
                                  ResolvedLanguageContext
                                             │
                                             ↓
                 bootstrap → orchestrator → stages → process runner → GF
                                             │
                                             ↓
                                           models
                                             ↓
                                      reports/persistence
```

### 30.2 Prohibited directions

The following are prohibited:

- models importing CLI or GUI;
- process utilities importing reports;
- reports importing CLI or GUI;
- reports launching validation;
- GUI widgets enumerating source files or resolving GF paths;
- language probe launching GF or subprocesses directly;
- language probe duplicating selection filtering, ordering or containment;
- language probe importing private helpers from another functional module;
- scanner importing report writers;
- classifier launching external tools;
- optional profile loader importing active-language Python code;
- framework defaults importing language-specific constants;
- selected source mutation of framework files;
- template files depending on selected-source content;
- runtime catalog readers controlling normal language startup.

### 30.3 Shared utility rule

A utility module is permitted only when:

- its responsibility is cohesive;
- it has more than one legitimate consumer;
- it does not become a hidden service locator;
- it does not own business policy that belongs to a domain component.

When an existing owner already provides file selection, path resolution, process execution or diagnostics, new orchestration code must use its public contract rather than create another implementation.

---

## 31. Failure containment

The architecture separates failures by layer.

### 31.1 Configuration failure

Examples:

- selected path does not exist or is unreadable;
- selected file is not an eligible `.gf` file;
- selected directory contains no eligible GF sources;
- RGL source root cannot be determined for the requested standard mode;
- module suffix or missing-module remediation is ambiguous;
- optional profile schema is invalid;
- optional profile conflicts with the resolved source context;
- unresolved required path;
- duplicate scenario ID.

A structural language-resolution failure is terminal before the main runtime is composed. A capability-specific configuration failure disables or fails that capability without erasing valid source-ready or scan-ready status.

### 31.2 Launch failure

The executable could not be started.

This is not a GF language failure.

### 31.3 Timeout or cancellation

The process did not complete under the execution contract.

This is not equivalent to a normal non-zero GF exit.

### 31.4 Tool-reported failure

GF ran and reported a failure.

Raw diagnostics remain authoritative evidence.

### 31.5 Contract or artifact failure

The process returned but required markers or artifacts are absent.

A zero exit code does not override this failure.

### 31.6 Validation failure

The operation executed correctly but the resolved language context or explicit validation profile failed the required criterion.

### 31.7 Reporting failure

A report writer failed after evidence existed.

The run records the reporting error without erasing raw evidence or relabeling GF results.

---

## 32. Security and trust boundaries

GF Wordbench is a local developer tool, but it executes external processes and executable scenario scripts.

### 32.1 Untrusted inputs

Treat as untrusted:

- selected language paths and source trees;
- `.gfs` scenarios;
- validation input files;
- optional validation profiles;
- external executable paths;
- legacy persisted files.

### 32.2 Process safety

Required controls:

- `shell=False` or equivalent by default;
- ordered arguments;
- explicit working directory;
- bounded timeout;
- bounded output policy;
- static allowlisting for executable diagnostic tools;
- controlled environment overlay;
- child-process termination policy;
- separate stdout and stderr capture.

### 32.3 Filesystem safety

Required controls:

- path containment;
- atomic writes;
- no silent overwrite of source files;
- no normal-run gold updates;
- no artifact paths escaping the configured root;
- no symlink-based escape in strict operations.

### 32.4 Secret handling

Reports and persisted files must not include:

- tokens;
- passwords;
- private keys;
- cookies;
- complete environment dumps;
- secret command arguments.

### 32.5 Scenario execution

A `.gfs` file is executable input.

Operating-system escape or pipeline behavior must be prohibited by default unless an explicit policy and contract enable it.

---

## 33. Extension architecture

GF Wordbench supports controlled extension, not unrestricted plugins.

### 33.1 Supported extension points

- a new validation stage;
- a new static diagnostic rule;
- a new GF command capability;
- a new scenario assertion;
- a new report field;
- a new report format;
- a new schema minor version;
- a new optional external tool contract registered in the diagnostic tool allowlist;
- a new project documentation specialization.

### 33.2 Extension requirements

An extension must define:

- owner;
- inputs;
- outputs;
- side effects;
- status behavior;
- configuration;
- persistence impact;
- tests;
- compatibility impact;
- documentation;
- contract updates.

### 33.3 When not to extend

Do not add a new component when an existing owner can absorb the behavior without:

- mixing responsibilities;
- creating a second implementation;
- changing its public contract incoherently;
- increasing coupling.

---

## 34. Testing architecture

Testing is organized by architectural boundary.

### 34.1 Unit tests

Cover:

- configuration validation;
- file selection;
- static scanning;
- command construction;
- diagnostic normalization;
- classification;
- fingerprints;
- comparison;
- serialization;
- report rendering.

### 34.2 Contract tests

Recommended location:

```text
tests/contracts/
```

Cover:

- provider-consumer interfaces;
- artifact ownership;
- dependency direction;
- path ownership;
- status vocabulary;
- no duplicate execution;
- CLI/GUI equivalence at the application boundary.

### 34.3 Schema tests

Recommended location:

```text
tests/schemas/
```

Cover:

- canonical round trips;
- required fields;
- version rejection;
- legacy migration;
- deterministic ordering;
- atomic-write behavior;
- path normalization.

### 34.4 Process integration tests

Cover:

- shell-free launch;
- stdout/stderr separation;
- timeout;
- cancellation;
- launch failure;
- non-zero exit;
- required artifact verification;
- encoding behavior.

### 34.5 GF integration tests

Cover, when GF is available:

- version probe;
- simple module compilation;
- checkpoint compilation;
- PGF creation;
- `.gfs` execution;
- marker detection;
- gold match and mismatch.

Tests must not depend silently on a developer’s global GF environment.

### 34.6 End-to-end tests

Cover:

```text
project fixture
  → resolved config
  → validation run
  → reports
  → manifest
  → reload and diff
```

---

## 35. Backward compatibility

The architecture supports migration from both the GF Audit baseline and the catalog-driven startup design.

Legacy elements include:

```text
.gf_audit_state.json
unversioned summary.json
mode=file
mode=all
ai_brief_path
absolute artifact paths
SHA-1 short fingerprints
language defaults in app/config.py
project/project.toml as mandatory startup authority
rgl-language-catalog.json as runtime authority
mandatory language-bundle configuration
last_language_id without a selected path
```

Canonical replacements include:

```text
.gf_wordbench_state.json with revalidated last_selected_language_path
versioned run summary
mode=quick
mode=diagnostic
artifacts.ai_ready
run-relative artifact paths
SHA-256 fingerprints
explicit selected directory or .gf file
immutable ResolvedLanguageContext
optional explicit validation profile
path-resolved language identity and effective GF-path evidence
```

Migration principles:

- read legacy through isolated compatibility adapters;
- validate what can be validated;
- preserve the source;
- write canonical output separately;
- report ambiguous or lossy conversions;
- do not search the filesystem globally to convert a stale catalog ID;
- allow an existing `project.toml` to be selected explicitly as a validation profile;
- emit only canonical formats from new writers.

A temporary catalog compatibility adapter may translate an explicit catalog selection into an explicit source path during a documented compatibility period. The resolved runtime must not preserve catalog authority.

Compatibility code must remain isolated in loaders or migrators. It must not spread legacy aliases or startup assumptions through current domain logic.

---

## 36. Operational model

GF Wordbench runs as a local foreground application.

It does not require:

- a daemon;
- a queue;
- a remote scheduler;
- a database;
- a network service.

A run may be initiated by:

- CLI;
- GUI;
- CI;
- a documented local automation wrapper.

The process completes by returning:

- an exit code to CLI or automation;
- a completed result to the GUI;
- persisted run artifacts.

Cancellation is cooperative through the application and process boundaries.

---

## 37. Release architecture

A framework release and a language-profile release are related but distinct.

### 37.1 Framework release

Proves:

- package correctness;
- contract compliance;
- schema compatibility;
- supported GF compatibility;
- framework tests;
- documentation consistency.

### 37.2 Language-profile release

Proves:

- resolved language-context validity;
- explicit validation-profile validity;
- required module compilation;
- required PGF build;
- required scenario success;
- required gold matches;
- profile release criteria;
- no unresolved blocking issues;
- complete evidence manifest.

A framework version does not imply that a selected source tree is release-ready. Source-ready, scan-ready and compile-ready capabilities may exist without a release profile.

A language-profile release must record the resolved language identity, source revision, profile digest, GF Wordbench version and GF version used.

---

## 38. Architectural decision summary

| Decision | Accepted choice |
|---|---|
| Active language model | Zero or one immutable resolved language context per session; one language identity per ordinary run |
| Startup input | One explicit language directory or `.gf` file |
| Startup resolution | Bounded `LanguageProbeService` coordination using existing public selection, path, preflight and diagnostic contracts |
| Runtime catalog | No static language catalog authority in normal startup |
| Validation profile | Optional explicit profile; `project/project.toml` is supported as a profile rather than mandatory startup configuration |
| Capability model | Source-ready, scan-ready, compile-ready, scenario-ready and release-ready are distinct |
| GF semantics | Delegated to native GF |
| Framework role | Orchestration, evidence, classification, comparison and reporting |
| Interfaces | Shared language-probe and application boundaries for CLI and GUI |
| Scenario format | Native `.gfs` |
| Regression expectations | Versioned normalized output and reviewed `.gold` when an explicit profile requires them |
| Machine result | Versioned `summary.json` |
| Artifact integrity | Versioned `manifest.json` with SHA-256 |
| Local preferences | `.gf_wordbench_state.json`; remembered paths are revalidated |
| Product structure | One deployable hexagonal modular monolith |
| Functional modules | `projects`, `runs`, `validation`, `diagnostics`, `reporting` |
| GF boundary | `GfToolPort` and a dedicated anti-corruption layer |
| Process execution | Centralized, shell-free by default |
| Run lifecycle | Global budget, bounded stages and reserved finalization |
| Diagnostic tools | Static allowlist with explicit contracts and limits |
| Portfolio boundary | Independent `gf-portfolio`; optional public-artifact consumption only |
| Storage | Filesystem; no mandatory database |
| Extensibility | Controlled explicit extension points |
| Compatibility | Versioned schemas, isolated adapters and tested migrations |
| Anti-drift | Alignment, correction-ledger, interfile, external-tool, persisted-schema and optional-profile/template locks |

---

## 39. Architecture invariants

The following invariants define the architecture.

1. A running Wordbench session has zero or one immutable resolved language context.
2. Every ordinary run records exactly one portable language identity and one resolved source context.
3. Normal startup begins from one explicit directory or `.gf` file selection.
4. Normal startup does not require a language catalog, language bundle, scenario, gold or `project.toml`.
5. Remembered paths are convenience state and are fully revalidated.
6. The permanent framework contains no active-language defaults, paths or module names.
7. The language probe coordinates public services and does not duplicate file selection, GF-path resolution, process execution or diagnostic parsing.
8. Source enumeration and target selection remain owned by the existing selection service.
9. One centralized GF-path resolution is reused by all GF operations in a run.
10. GF remains authoritative for GF semantics and dependency resolution.
11. GF interaction passes through `GfToolPort` and the dedicated anti-corruption layer.
12. CLI and GUI use the same probe, configuration and orchestration boundaries.
13. Wordbench remains one deployable hexagonal modular monolith.
14. External execution is centralized.
15. Every external process has an explicit executable, ordered arguments, working directory and finite timeout.
16. Every run reserves time for safe finalization.
17. Stdout and stderr are preserved separately.
18. Raw evidence is captured before normalization.
19. Reports consume results and never rerun validation.
20. Every generated artifact has one owner.
21. Machine-consumed data uses explicit versioned schemas.
22. Selected-source, optional-profile and run paths use explicit path models.
23. Optional validation profiles cannot contradict the resolved source context.
24. Required release artifacts must exist; exit code alone is insufficient.
25. Gold files change only through an explicit update workflow.
26. Validation status, execution state, error kind, diagnostic class and capability status remain distinct.
27. Executable diagnostic tools are statically allowlisted with explicit contracts.
28. Legacy and catalog compatibility remains isolated in loaders or migrators.
29. GF Wordbench has no runtime, storage or private-schema dependency on `gf-portfolio`.
30. Switching language disposes the old runtime and is prohibited during an active run.
31. A component may change internally when its external contracts remain compatible.
32. A cross-file contract change is one coordinated change.
33. A failure in a later stage must not erase valid earlier evidence or capabilities.
34. Complexity must correspond to a stable responsibility or contract.

---

## 40. Architecture compliance checklist

A codebase is architecture-compliant when:

```text
[ ] Framework code contains no active-language paths or module names
[ ] GUI always starts with an introduction or explicit language-open flow
[ ] CLI and GUI accept equivalent language-directory or .gf-file inputs
[ ] normal startup does not require rgl-language-catalog.json
[ ] normal startup does not require language.toml or project.toml
[ ] one immutable ResolvedLanguageContext gates main-runtime construction
[ ] remembered selected paths are revalidated before reuse
[ ] LanguageProbeService uses public selection, path, preflight and diagnostic contracts
[ ] LanguageProbeService does not launch GF or subprocesses directly
[ ] source enumeration and ordering are not duplicated outside the selection owner
[ ] one effective GFPathResolution is reused across GF consumers
[ ] source-ready and scan-ready operation can work without GF installed
[ ] compile-ready operation requires GF-specific preflight
[ ] optional profiles cannot override or escape the resolved source context
[ ] CLI and GUI resolve equivalent RunConfig values for equivalent inputs
[ ] runs.application is the only run orchestrator
[ ] functional modules respect hexagonal dependency direction
[ ] all GF operations pass through GfToolPort and the GF anti-corruption layer
[ ] all process launches use the shared process runner
[ ] compilation, PGF and scenarios have distinct stage owners
[ ] every run has global, stage and finalization budgets
[ ] executable diagnostic tools are statically allowlisted
[ ] Wordbench starts and runs without gf-portfolio
[ ] public interoperability uses versioned Wordbench artifacts only
[ ] raw stdout and stderr are preserved
[ ] every process-backed result records command and working directory
[ ] reports do not launch GF or rescan sources
[ ] summary.json is versioned and reloadable
[ ] manifest.json verifies required artifacts
[ ] selected-source, profile and run paths are canonical and contained
[ ] state is disposable and contains no executable language architecture
[ ] gold updates are explicit
[ ] required release gates cannot be silently bypassed
[ ] status vocabularies are centralized
[ ] compatibility aliases and catalog authority are not emitted by canonical writers
[ ] switching language recreates the runtime and leaves no old path contamination
[ ] contract tests cover component boundaries
[ ] schema tests cover canonical and legacy forms
[ ] end-to-end tests cover at least two structurally different language selections
[ ] documentation ownership contains no conflicting normative duplicates
```

---

## 41. Related documents

### Architecture details

```text
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/architecture/DEPENDENCY_RULES.md
```

### Normative locks and documentation governance

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/DOCUMENTATION_CORRECTION_LEDGER.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

The project and template locks govern optional validation profiles and templates, not normal path-resolved startup.

### GF and validation

```text
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_PATH_RESOLUTION.md
docs/validation/FILE_SELECTION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/GOLDEN_TESTS.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/TOOL_CATALOG.md
```

### Configuration and reports

```text
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
```

### Decisions

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md
docs/decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
docs/decisions/ADR-0004-NATIVE-GFS-SCENARIOS.md
docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md
docs/decisions/ADR-0006-AI-READY-REPORT.md
docs/decisions/ADR-0007-GOLDEN-OUTPUT-TESTING.md
docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md
docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md
docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md
docs/decisions/ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
```

ADR-0014 is retained as a superseded historical decision. ADR-0015 governs normal startup.

---

## 42. Coherence rule

GF Wordbench is not a collection of independent utilities.

It is one coordinated validation system in which:

```text
the user selects one source location
the language probe coordinates existing owners
the resolved language context defines the active source boundary
an optional profile defines advanced validation and release policy
GF executes GF semantics
the framework controls and records the execution
models carry explicit results
reports expose those results
schemas preserve them across time
contracts keep every boundary aligned
```

A local implementation change is acceptable only when the complete architectural path remains coherent and no second implementation of selection, path resolution, external execution or diagnostic parsing is introduced.
