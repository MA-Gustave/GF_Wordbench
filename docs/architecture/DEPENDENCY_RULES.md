# GF Wordbench — Dependency Rules

**Document ID:** `GF-WB-ARCH-DEPENDENCY-RULES`  
**Status:** Normative  
**Rules version:** `2.0.0`  
**Applies to:** GF Wordbench framework, framework tests, active-project integration boundaries, generated artifacts, public exports, and optional external consumers  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Target path:** `docs/architecture/DEPENDENCY_RULES.md`

---

## 1. Purpose

This document defines the allowed dependency directions in GF Wordbench.

It prevents architectural drift caused by:

- circular imports;
- modules bypassing public contracts;
- user interfaces bypassing application use cases;
- report writers executing validation;
- duplicated configuration or path resolution;
- framework code depending on one active language;
- project files controlling framework internals;
- duplicated artifact ownership;
- hidden process execution;
- readers mutating data owned by writers;
- adapters redefining domain policy;
- Wordbench depending on private `gf-portfolio` code, state, or storage;
- tests depending on one developer's machine.

The core rule is:

> Dependencies point from orchestration and mechanisms toward stable contracts, while stable domain rules remain independent of external mechanisms and delivery surfaces.

---

## 2. Relationship to other normative documents

This document owns architectural dependency direction.

It complements, but does not replace:

| Topic | Authoritative document |
|---|---|
| Architectural decision | `docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md` |
| Exact provider-consumer contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External executables and process behavior | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats and migrations | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Product boundary | `docs/architecture/PRODUCT_BOUNDARIES.md` |
| Component responsibilities | `docs/architecture/COMPONENT_MAP.md` |
| Runtime order | `docs/architecture/EXECUTION_FLOW.md` |
| Shared data structures | `docs/architecture/DATA_MODEL.md` |
| Artifact ownership | `docs/architecture/ARTIFACT_MODEL.md` |
| Active-project GF dependencies | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Active-project module graph | `project/docs/MODULE_DEPENDENCY_MAP.md` |

When documents disagree, accepted ADRs and specialized contract locks govern their respective boundaries.

---

## 3. Normative terms

- **MUST / MUST NOT**: mandatory or prohibited.
- **SHOULD / SHOULD NOT**: expected unless a reviewed exception exists.
- **MAY**: optional.
- **DEPENDENCY**: an import, call, callback, schema assumption, file access, process invocation, shared constant, or runtime data flow.
- **OWNER**: the module or component authorized to define or mutate a contract, state domain, or artifact.
- **OBSERVER**: a component authorized to read, summarize, compare, or display owned data without mutating it.
- **PUBLIC CONTRACT**: an explicitly documented API, port, model, schema, artifact, or event shape intended for consumers.
- **PRIVATE IMPLEMENTATION**: a symbol, file, database, state object, or behavior not declared as a public contract.
- **POLICY**: a rule deciding what must happen or how an outcome is interpreted.
- **MECHANISM**: a bounded operation that performs work without owning global workflow policy.
- **CYCLE**: a direct or indirect dependency path that returns to its origin.
- **ACTIVE PROJECT**: the single GF language project represented by `project/`.
- **PUBLIC ARTIFACT**: a versioned Wordbench artifact explicitly intended for external read-only consumption.

---

## 4. Architectural model

GF Wordbench is one deployable modular monolith with two complementary dimensions:

1. five functional modules;
2. six hexagonal rings.

### 4.1 Functional modules

```text
projects
runs
validation
diagnostics
reporting
```

| Module | Ownership |
|---|---|
| `projects` | Active-project identity, configuration, loading, paths, and lifecycle |
| `runs` | Run identity, orchestration, budgets, continuation, finalization, and history |
| `validation` | Selection, scanning, compilation, PGF construction, scenarios, gold comparison, regression comparison, and release gates |
| `diagnostics` | Diagnostic normalization, findings, causal classification, pattern interpretation, and diagnostic tools |
| `reporting` | Schemas, renderers, manifests, artifact publication, and public exports |

A module owns a cohesive product responsibility. It is not a separate service and does not communicate through a network merely because it has a boundary.

GF Wordbench has no functional `languages` or portfolio module. Multi-workspace inventory, aggregation, comparison, and portfolio views belong to `gf-portfolio`.

### 4.2 Hexagonal rings

```text
domain
application
ports
adapters
entrypoints
bootstrap
```

The rings are ordered from stable rules to composition and delivery.

| Ring | Responsibility |
|---|---|
| `domain` | Stable models, invariants, statuses, result semantics, and decision rules |
| `application` | Use cases and coordination of domain behavior |
| `ports` | Narrow contracts for external or unstable boundaries |
| `adapters` | Concrete implementations for GF, processes, filesystem, TOML, JSON, persistence, clocks, and other mechanisms |
| `entrypoints` | CLI, GUI, and automation surfaces |
| `bootstrap` | Composition root and concrete dependency wiring |

Functional modules and rings are orthogonal. A functional module may contain domain, application, port, and adapter elements. The repository does not require one package for every possible module-by-ring combination.

---

## 5. Ring dependency rules

### 5.1 Domain

Domain code MAY depend on:

- Python standard-library primitives;
- pure domain types within the same module;
- explicitly shared value objects with a single owner.

Domain code MUST NOT depend on:

- application services;
- ports or adapter implementations;
- CLI or GUI code;
- bootstrap;
- filesystem, subprocess, TOML, JSON, database, or network libraries;
- framework state files;
- active-project paths;
- report formatting;
- `gf-portfolio`.

Domain models remain passive. They may validate their own invariants and expose pure derived values, but they do not perform I/O or launch work.

### 5.2 Application

Application code MAY depend on:

- domain contracts;
- port interfaces;
- public application APIs of another functional module when explicitly allowed;
- immutable or controlled request and result models.

Application code MUST NOT depend on:

- concrete adapters;
- GUI widgets or CLI parser objects;
- bootstrap implementation details;
- human-readable reports as data;
- private symbols from another module.

Application services own use-case sequencing. They do not construct ad hoc external commands or bypass ports.

### 5.3 Ports

Ports define contracts for external or unstable boundaries.

A port MAY depend on:

- domain value objects;
- application request and result types;
- standard typing primitives.

A port MUST NOT depend on:

- its adapter implementation;
- entrypoints;
- bootstrap;
- third-party mechanism-specific types that leak through the boundary;
- active-language hardcoded identities.

A new port requires a real external or unstable boundary. Internal helpers do not receive interfaces solely for symmetry.

### 5.4 Adapters

Adapters MAY depend on:

- the port they implement;
- domain and application types required by that port;
- approved external libraries or executables;
- bounded mechanism utilities.

Adapters MUST NOT:

- redefine domain statuses or release policy;
- orchestrate the complete run;
- call entrypoints or bootstrap;
- import GUI widgets;
- mutate artifacts outside their declared ownership;
- expose private external representations as canonical Wordbench models;
- depend on `gf-portfolio` internals.

Adapters translate between external representations and Wordbench contracts.

### 5.5 Entrypoints

Entrypoints MAY depend on:

- public application use cases;
- public presentation models;
- state services limited to non-authoritative preferences;
- bootstrap entry functions.

Entrypoints MUST NOT depend directly on:

- validation-stage internals;
- process or filesystem adapters;
- GF command builders;
- schema-writer internals;
- project TOML parser internals;
- diagnostic private helpers;
- report-writer private helpers.

CLI, GUI, and automation may differ in presentation, but equivalent inputs must resolve to equivalent application requests and domain outcomes.

### 5.6 Bootstrap

Bootstrap MAY depend on public constructors from every ring required for composition.

Bootstrap owns:

- concrete adapter selection;
- dependency construction;
- application assembly;
- environment-specific wiring;
- public application entry construction.

Bootstrap MUST NOT:

- execute a run during import;
- parse raw CLI arguments;
- display GUI dialogs;
- contain validation algorithms;
- write reports;
- redefine project policy;
- create hidden defaults;
- mutate files or state through import side effects.

---

## 6. Functional-module dependency rules

### 6.1 `projects`

`projects` owns the active-project boundary.

It MAY expose:

- project identity;
- resolved project configuration;
- validated project paths;
- entrypoints and checkpoints;
- scenario registrations;
- release policy;
- project lifecycle operations.

It MUST NOT depend on:

- run history to infer project identity;
- GUI state as project authority;
- validation results;
- diagnostics;
- reports;
- `gf-portfolio` membership;
- language-specific constants in framework defaults.

Other modules consume a resolved project contract rather than reading `project.toml` independently.

### 6.2 `runs`

`runs` owns complete-run orchestration and finalization.

It MAY depend on public contracts from:

- `projects`;
- `validation`;
- `diagnostics`;
- `reporting`;
- clock, cancellation, persistence, and process-budget ports.

It MUST NOT:

- implement validation-stage internals;
- parse GF diagnostics directly;
- render reports directly;
- infer project identity from generated artifacts;
- mutate project-owned sources, scenarios, inputs, or golds;
- allow a report or interface to redefine run status.

### 6.3 `validation`

`validation` owns bounded validation operations and release criteria.

It MAY consume:

- resolved project contracts;
- run-scoped requests and artifact paths;
- GF and process ports;
- filesystem and clock ports;
- diagnostic parsing contracts;
- project-owned scenarios, inputs, and golds.

It MUST NOT:

- depend on report writers;
- depend on GUI or CLI code;
- mutate golds during normal validation;
- use previous human-readable reports as machine truth;
- implement portfolio aggregation;
- let one validation stage invoke another unless the composition is an explicit application use case.

Static scan and GF execution remain distinct operations.

### 6.4 `diagnostics`

`diagnostics` owns interpretation of preserved evidence.

It MAY consume:

- structured validation results;
- raw evidence references;
- normalized diagnostic inputs;
- dependency evidence;
- controlled diagnostic-tool ports.

It MUST NOT:

- launch GF through validation-private helpers;
- mutate raw evidence;
- rewrite validation results;
- generate authoritative run status independently;
- depend on GUI wording;
- use AI output as normative evidence;
- invoke arbitrary commands.

Direct, downstream, ambiguous, tool, configuration, timeout, and framework interpretations must remain traceable to preserved evidence.

### 6.5 `reporting`

`reporting` owns persisted and rendered outputs.

It MAY consume:

- completed or explicitly partial run results;
- project identity snapshots;
- validation and diagnostic result models;
- artifact references;
- schema and serialization contracts.

It MUST NOT:

- run GF;
- rerun scanning or scenarios;
- invoke validation application services;
- repair missing evidence by executing tools;
- alter run or release status;
- rewrite raw evidence;
- update golds;
- parse Markdown when a structured schema exists.

All reports derive from the same structured result set.

---

## 7. Intermodule direction matrix

`✓` means allowed through a public contract.  
`C` means allowed only through a narrow data or port contract.  
`—` means prohibited.

| Caller \ Provider | `projects` | `runs` | `validation` | `diagnostics` | `reporting` |
|---|---:|---:|---:|---:|---:|
| `projects` | C | — | — | — | — |
| `runs` | ✓ | C | ✓ | ✓ | ✓ |
| `validation` | C | C | C | C | — |
| `diagnostics` | — | C | C | C | — |
| `reporting` | C | C | C | C | C |

Interpretation:

- `runs` coordinates the complete workflow.
- `validation` may receive run-scoped contracts but does not control run orchestration.
- `diagnostics` consumes evidence and structured results but does not call validation execution.
- `reporting` observes public result contracts and never calls execution behavior.
- `projects` does not depend on consumers of project data.
- Same-module dependencies remain acyclic and use public internal contracts where a package boundary exists.

---

## 8. Canonical runtime and result flow

Execution flow:

```text
CLI / GUI / automation
    → bootstrap
    → application use case
    → projects resolves one active project
    → runs creates and coordinates one run
    → validation executes bounded stages
    → diagnostics interprets preserved evidence
    → runs finalizes the structured result
    → reporting writes artifacts
```

External execution flow:

```text
validation or approved diagnostics use case
    → external-tool port
    → adapter
    → process port
    → local process adapter
    → GF or approved executable
```

Result flow:

```text
raw external response
    → process result
    → stage result
    → diagnostic interpretation
    → finalized run result
    → reports, manifest, CLI outcome, GUI display
```

No reverse path may cause a report, UI, or external consumer to execute or alter the originating validation.

---

## 9. Configuration dependencies

Configuration has distinct owners:

```text
framework defaults
    language-neutral application behavior

project/project.toml
    active-project identity and project validation policy

application state
    local non-authoritative UI and environment preferences

resolved run request
    one execution's immutable or controlled configuration
```

Rules:

- each value has one authoritative source;
- all consumers use the canonical resolution pipeline;
- GUI state and previous runs do not redefine active-project identity;
- project configuration does not contain private adapter objects or Python callables;
- environment-specific executable paths remain outside portable project identity;
- one run resolves one active project and one normative target;
- Wordbench configuration contains no Portfolio registry or aggregation state.

---

## 10. External-process dependencies

All external process execution passes through one approved process boundary.

A structured request identifies:

- executable;
- ordered arguments;
- working directory;
- environment changes;
- standard input;
- timeout or run budget;
- cancellation;
- output limits;
- expected artifact roots.

Rules:

- normal execution does not use an uncontrolled shell;
- direct `subprocess` use outside the approved adapter is prohibited;
- process mechanisms do not know project release policy;
- GF-specific command construction remains inside the GF anti-corruption boundary;
- version-specific behavior is isolated in capability probes or adapters;
- raw stdout, stderr, exit state, timeout state, duration, and artifacts are preserved;
- classifiers and reports do not depend only on rendered command text;
- individual stages do not create incompatible process behavior.

---

## 11. Artifact ownership dependencies

An artifact has one writer and zero or more observers.

| Artifact | Owner | Allowed observers |
|---|---|---|
| `project/project.toml` | project initializer, migrator, or maintainer | `projects`, documentation checks |
| application state | designated state adapter | bootstrap, entrypoints |
| raw process evidence | external-tool adapter within its run | validation, diagnostics, reporting, users |
| normalized evidence | validation normalization owner | comparison, diagnostics, reporting |
| `.gold` files | explicit reviewed gold-update workflow | validation comparison |
| structured run result | `runs` | reporting, entrypoints |
| `summary.json` | reporting schema writer | users, automation, compatible external consumers |
| `summary.md` | reporting renderer | users and entrypoints |
| `AI_READY.md` | reporting renderer | users and AI-assisted workflows |
| `manifest.json` | reporting/finalization owner | verification, cleanup, compatible external consumers |
| collected `.gfo` / `.pgf` artifacts | validation artifact collector | release gates, reporting, users |

Observers MUST NOT rewrite owned artifacts.

Consumers use canonical artifact references or manifest entries. They do not reconstruct filenames independently.

---

## 12. Framework, active project, and template boundaries

Framework-owned areas:

```text
app/
tests/
docs/
templates/
```

Active-project-owned areas:

```text
project/project.toml
project/docs/
project/validation/
active GF source files
```

Rules:

- framework production code remains language-neutral;
- active-language names, module suffixes, concrete source paths, and linguistic policy remain project-owned;
- project files depend on documented framework contracts, not private Python modules;
- template files define generic structure and placeholders, not active-project facts;
- project GF module dependencies are governed by project lock files;
- generated run directories never become project identity sources.

---

## 13. `gf-portfolio` boundary

The permitted direction is:

```text
gf-portfolio
    → public versioned GF Wordbench artifacts

GF Wordbench
    -X→ gf-portfolio runtime, code, database, state, schemas, or configuration
```

Rules:

- Wordbench starts, validates, reports, and passes tests without Portfolio;
- Portfolio may read only public finalized Wordbench artifacts;
- Portfolio-specific adapters, indexing, aggregation, scoring, and migrations remain in `gf-portfolio`;
- Portfolio does not import private Wordbench modules;
- Wordbench does not discover Portfolio workspaces;
- an ingestion failure cannot alter a completed Wordbench run;
- Portfolio schemas do not enter Wordbench configuration or persisted state.

---

## 14. Public and private API rules

A cross-module dependency uses one of:

- an explicitly exported function or class;
- a documented request, result, event, or value object;
- a documented port;
- a versioned schema;
- a documented artifact.

Rules:

- names beginning with `_` are private unless explicitly documented otherwise;
- `__init__.py` may re-export stable public symbols but must not eagerly load all submodules or trigger work;
- wildcard imports are prohibited in production code;
- type-only imports may avoid runtime cycles but must not hide a conceptual dependency;
- a helper used across modules becomes a public contract or moves to a clearly owned shared boundary;
- a generic shared package must not become an ownerless dumping ground.

---

## 15. Circular dependencies and callbacks

Direct and indirect cycles are prohibited between rings and functional modules.

Examples of prohibited cycles:

```text
runs ↔ reporting
validation ↔ diagnostics execution
projects ↔ runs
domain ↔ adapters
bootstrap ↔ entrypoints
```

Cycle-breaking order:

1. pass a value explicitly;
2. move a passive shared type to its legitimate owner;
3. introduce a narrow port or protocol;
4. split policy from mechanism;
5. create a public facade;
6. use a local import only as a temporary code migration technique.

Callbacks flow upward only as injected neutral behavior.

A lower component may emit a progress event through an injected callback. It must not import GUI code or call an entrypoint.

---

## 16. Side-effect rules

Importing a module MUST NOT:

- create directories;
- write files;
- load the active project;
- execute GF or another process;
- start a GUI event loop;
- parse process arguments;
- mutate environment variables;
- update golds;
- migrate schemas automatically;
- delete runs;
- connect to Portfolio.

Mutation occurs only through explicit named operations.

Global mutable application state is prohibited. Runtime state is represented through explicit objects, function parameters, controlled services, cancellation tokens, or neutral event payloads.

---

## 17. Error, progress, cancellation, and concurrency dependencies

### 17.1 Errors

- adapters expose bounded mechanism outcomes;
- validation converts expected tool outcomes into structured stage results;
- diagnostics interprets evidence without replacing it;
- runs determines complete-run continuation and terminal outcome;
- entrypoints map the finalized result to CLI or GUI presentation;
- reporting displays structured errors without creating new classifications.

Lower rings do not depend on CLI exit codes or GUI wording.

### 17.2 Progress

Neutral progress events may contain:

- run or stage identity;
- subject identity;
- completed and total counts;
- a short message;
- severity;
- timestamp.

They contain no GUI widget, terminal object, or adapter instance.

### 17.3 Cancellation

Cancellation flows downward through a neutral token, event, or port contract.

Completed evidence is preserved. Reporting occurs only after `runs` has produced a structured terminal or partial result.

### 17.4 Concurrency

When concurrency is used:

- `runs` owns scheduling policy;
- stages remain isolated;
- artifact paths remain unique;
- result ordering remains deterministic;
- state mutation is serialized;
- cancellation propagates through neutral contracts;
- stages do not create unmanaged pools.

---

## 18. Test dependency rules

Production code MUST NOT depend on tests or fixtures.

Tests may depend on public production contracts.

### 18.1 Unit and component tests

Unit and component tests isolate:

- domain rules;
- application use cases;
- command construction;
- project loading;
- scanners;
- classifiers;
- normalization and comparison;
- schemas;
- report rendering.

### 18.2 Integration tests

Integration tests may use:

- controlled GF installations;
- neutral fixture grammars;
- temporary directories;
- explicit environment configuration;
- fake process adapters.

They must not require:

- one developer's global paths;
- personal run directories;
- GUI interaction;
- network access unless explicitly isolated;
- `gf-portfolio` for Wordbench core tests.

### 18.3 Architecture tests

Architecture tests MUST verify:

- no forbidden inward-to-outward imports;
- no intermodule cycles;
- reports do not import execution behavior;
- entrypoints do not import process adapters;
- scanners and compilers do not invoke each other;
- domain models remain passive;
- production code does not import tests;
- framework code remains language-neutral;
- artifact constants have one owner;
- direct subprocess use is confined to the approved adapter;
- Wordbench does not import `gf-portfolio`;
- normal validation cannot rewrite golds.

Mocks replace external boundaries rather than every internal function.

---

## 19. Optional dependencies

A new Python package, executable, operating-system service, or adapter is permitted only when:

1. the capability belongs to Wordbench scope;
2. the capability is not adequately provided by existing components;
3. ownership is explicit;
4. failure behavior is defined;
5. platform support is defined;
6. security and licensing are reviewed;
7. compatibility is documented;
8. tests cover the boundary;
9. the dependency is replaceable through a bounded adapter where appropriate;
10. Wordbench remains independently operable.

Optional dependencies fail with explicit capability errors. They do not corrupt unrelated workflows or become hidden mandatory dependencies.

Dependency injection remains explicit and small. A general runtime service container is not required.

---

## 20. Dependency exceptions

A dependency exception requires a new or amended accepted ADR when it changes:

- ring direction;
- functional-module ownership;
- external execution;
- persisted schemas;
- project/framework separation;
- artifact ownership;
- security boundaries;
- the Wordbench/Portfolio boundary.

An exception must identify:

```text
affected modules
unusual dependency
reason
alternatives considered
risks
containment
tests
removal or review condition
authorizing ADR
```

One exception does not authorize similar dependencies elsewhere.

---

## 21. Review checklist

A change that adds or modifies a dependency is complete only when:

```text
[ ] caller module and ring are identified
[ ] provider module and ring are identified
[ ] the direction is permitted
[ ] a public contract is used
[ ] no private symbol is imported across a boundary
[ ] no direct or indirect cycle is introduced
[ ] configuration ownership remains unique
[ ] artifact ownership remains unique
[ ] external process access uses an approved port and adapter
[ ] framework and active-project boundaries remain intact
[ ] Wordbench remains independent of gf-portfolio
[ ] error and cancellation semantics remain intact
[ ] tests enforce the dependency rule
[ ] affected contract locks and owner documents agree
[ ] an ADR authorizes any architectural exception
```

---

## 22. Drift indicators

Dependency drift is probable when:

- a report imports validation execution;
- a GUI widget imports a process adapter;
- two components resolve the same path differently;
- a domain model imports a formatter, adapter, or entrypoint;
- a diagnostic classifier launches an external process directly;
- a diff component parses `summary.md`;
- project identity is inferred from application state or a previous run;
- framework source contains an active-language module suffix;
- a consumer imports another module's private helper;
- one artifact filename is independently declared in several modules;
- import side effects create files or launch work;
- a launcher supplies hidden validation defaults;
- direct `subprocess` calls appear outside the process adapter;
- a normal validation path can update gold;
- Wordbench imports `gf-portfolio`;
- Portfolio state appears in Wordbench configuration or schemas;
- an adapter decides release policy;
- bootstrap contains business rules;
- a port exists only to wrap a private helper.

Each indicator requires restoration of the documented direction or an accepted architectural decision changing the contract.

---

## 23. Enforcement rule

GF Wordbench preserves one dependency model:

```text
entrypoints
    → application use cases
    → domain rules and ports
    → adapters at explicit external boundaries

bootstrap
    → composes all required implementations

runs
    → coordinates projects, validation, diagnostics, and reporting
```

Results and evidence return as data. Control does not flow backward from reports, interfaces, generated artifacts, active-project files, or external consumers into validation execution.

A dependency is accepted only when it makes ownership and evidence flow clearer. It is rejected when it creates hidden policy, duplicate authority, reverse control, a cycle, or an undocumented route around the modular hexagonal architecture.
