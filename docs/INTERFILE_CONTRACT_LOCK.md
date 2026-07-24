# GF Wordbench — Interfile Contract Lock

**Document ID:** `GF-WB-ARCH-INTERFILE-LOCK`  
**Status:** Normative  
**Contract version:** `2.0.0`  
**Applies to:** GF Wordbench framework, its active-project boundary, its project template and its public artifact boundary  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Implementation note:** this file defines the accepted target contracts; `docs/architecture/IMPLEMENTATION_ALIGNMENT.md` must state which contracts are currently implemented and verified

---

## 1. Purpose

This file prevents drift between Wordbench components and repository files. It locks externally observable responsibilities, ownership and dependency direction without pretending that every target contract is already implemented.

Internal code may change freely when every documented boundary remains compatible. A boundary change requires coordinated updates to its provider, consumers, schemas, tests, owner documentation and this lock.

## 2. Product boundary

One Wordbench workspace contains exactly one active GF language project. Every run resolves exactly one active project identity and one normative language target.

Wordbench does not own:

- a runtime language-profile selector;
- a multi-project registry inside one workspace;
- simultaneous validation of several active projects in one run;
- cross-workspace orchestration or portfolio aggregation.

Those capabilities belong to the independent product `gf-portfolio`.

```text
gf-portfolio -> public versioned GF Wordbench artifacts
GF Wordbench -X-> gf-portfolio runtime, code, storage or configuration
```

Wordbench must start, validate, report and pass its tests without `gf-portfolio`.

## 3. Normative terms

- **MUST / MUST NOT**: mandatory or prohibited.
- **SHOULD / SHOULD NOT**: expected unless an explicit reviewed exception exists.
- **MAY**: optional.
- **PROVIDER**: component or file that owns a public behavior or artifact.
- **CONSUMER**: component or file that relies on that behavior or artifact.
- **OWNER**: sole authority allowed to define or mutate a contract.
- **PUBLIC ARTIFACT**: versioned Wordbench output intended for external read-only consumption.
- **TARGET CONTRACT**: accepted design that may still be unimplemented.
- **IMPLEMENTED CONTRACT**: target contract supported by current source and reproducible evidence.

An accepted ADR establishes a target contract. It does not prove implementation.

## 4. Architectural shape

GF Wordbench is one deployable hexagonal modular monolith.

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

Dependency direction:

```text
entrypoints -> application
bootstrap -> application + ports + adapters
application -> domain + ports
domain -> no framework, UI, process or filesystem implementation
adapters -> ports + external systems
```

Prohibited dependencies:

- domain to GUI, CLI, filesystem, subprocess, JSON/TOML library or GF executable;
- application to concrete GUI, CLI or external-tool implementation;
- one functional module reaching into another module's private implementation;
- Wordbench code importing or requiring `gf-portfolio`;
- active-project language facts hard-coded in framework defaults.

## 5. Ownership map

| Subject | Owner |
|---|---|
| Active project identity and configuration | `project/project.toml` and the projects module |
| Active language source facts and linguistic contracts | `project/docs/` and current GF sources |
| Reusable project initialization structure | `templates/project/` |
| Run identity, lifecycle and finalization | runs module |
| Static scan, GF compile, scenario and regression orchestration | validation module |
| Diagnostic classification and tool registry | diagnostics module |
| Summary, manifest, reports and public exports | reporting module |
| GF invocation and process evidence | external-tool adapter under the relevant port |
| Persisted formats and versions | `docs/PERSISTED_SCHEMA_LOCK.md` |
| External executable boundary | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Cross-document decisions | accepted ADRs and `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Multi-workspace aggregation | independent `gf-portfolio` product |

An overview may summarize an owner but must not define a competing normative contract.

## 6. Locked contracts

### IFC-WB-001 — Workspace to active project

**Provider:** workspace structure.  
**Consumer:** project loading use case.

Locked rules:

- the workspace exposes one canonical active-project boundary at `project/`;
- `project/project.toml` identifies one active project;
- GUI state, previous runs and filename guessing cannot override project identity;
- arbitrary project-root selection is not a hidden second project model;
- failure to resolve the active project is explicit and prevents execution.

### IFC-WB-002 — Project configuration to projects module

**Provider:** `project/project.toml`.  
**Consumer:** projects module.

Locked rules:

- configuration is parsed and validated before validation begins;
- project-relative paths resolve against the active project root;
- ordered lists remain deterministic;
- environment-specific executable and output locations do not become language-project facts;
- normal validation does not silently rewrite project configuration;
- one configuration never describes multiple active projects.

### IFC-WB-003 — Entrypoints to application use cases

**Providers:** CLI and GUI entrypoints.  
**Consumer:** application layer.

Locked rules:

- CLI and GUI call the same application use cases;
- neither entrypoint implements validation, diagnostic or reporting rules independently;
- entrypoints translate user intent into typed requests and render typed results;
- UI preferences cannot become project authority;
- a feature documented for both entrypoints must have equivalent domain meaning.

### IFC-WB-004 — Application to validation module

**Provider:** application run request.  
**Consumer:** validation module.

Locked rules:

- a request identifies one active project and one run;
- validation stages are explicit and ordered;
- static scan and GF compilation remain distinct stages;
- scenario execution uses registered native `.gfs` scenarios;
- normal validation does not mutate project sources, scenarios, inputs or gold files;
- cancellation, timeout and run budgets are represented explicitly.

### IFC-WB-005 — Validation to external-tool port

**Provider:** validation module.  
**Consumer:** external-tool port and GF adapter.

Locked rules:

- the request is structured; it is not a shell command string;
- executable, arguments, working directory, environment, stdin and timeout are explicit;
- raw stdout, stderr, exit status, timing and produced artifacts are returned as evidence;
- GF remains authoritative for GF parsing, type checking, compilation and scenario execution;
- process and GF details do not leak into domain models beyond defined result types.

The detailed boundary is owned by `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`.

### IFC-WB-006 — Validation evidence to diagnostics

**Provider:** validation results and raw evidence.  
**Consumer:** diagnostics module.

Locked rules:

- raw evidence is preserved before classification or normalization;
- direct failures are distinguished from downstream failures when evidence supports the distinction;
- tool failure, launch failure, timeout, contract failure and validation failure remain distinct;
- diagnostic identifiers and severities come from controlled registries;
- AI-assisted analysis may annotate evidence but cannot replace normative GF evidence.

### IFC-WB-007 — Results to reporting

**Provider:** finalized typed run results.  
**Consumer:** reporting module.

Locked rules:

- reports do not rerun validation or reinterpret project identity;
- machine-readable output is versioned and deterministic;
- human-readable reports derive from the same finalized results;
- partial or interrupted runs are not represented as complete successes;
- planned report fields are not emitted as if implemented;
- public artifacts identify schema version, run identity and active project identity.

### IFC-WB-008 — Run finalization to artifact bundle

**Provider:** runs module.  
**Consumers:** reporting, cleanup, automation and optional external readers.

Locked rules:

- one run owns one run directory;
- finalization records terminal status and artifact completeness;
- stale artifacts from another run cannot satisfy the current run;
- raw evidence, normalized evidence and reports have distinct ownership;
- cleanup cannot remove project-owned assets;
- recovery distinguishes temporary, incomplete and finalized artifacts.

### IFC-WB-009 — Wordbench public artifacts to `gf-portfolio`

**Provider:** public versioned Wordbench artifacts.  
**Consumer:** optional `gf-portfolio` adapter.

Locked rules:

- the boundary is read-only from the consumer's perspective;
- Wordbench does not know whether Portfolio is installed;
- Portfolio-specific storage, indexing, aggregation and readiness logic remain outside Wordbench;
- consumer adapters do not use private Wordbench modules or state;
- compatibility is governed by public schema versions and migrations;
- a Portfolio ingestion failure does not alter a completed Wordbench run.

### IFC-WB-010 — Project template to initialized project

**Provider:** `templates/project/`.  
**Consumer:** explicit project initialization or reset operation.

Locked rules:

- one template instance creates one active project boundary;
- required placeholders are replaced or initialization fails;
- initialized project files become project-owned;
- template structure stays synchronized with the active-project contract structure;
- the template contains no active language identity and no Portfolio registry.

## 7. Artifact ownership

| Artifact | Writer | Readers | Mutation rule |
|---|---|---|---|
| `project/project.toml` | explicit project initialization or migration | projects module, documentation | no silent mutation during normal validation |
| project GF sources | project maintainers | GF and validation | Wordbench reads; normal validation does not edit |
| `.gfs` scenarios and inputs | project maintainers | validation and GF | no normal-run mutation |
| gold files | explicit reviewed update workflow | regression comparison | never auto-accepted during validation |
| raw process logs | external-tool adapter | diagnostics, reports, users | immutable after capture |
| normalized output | validation normalization stage | comparison, reports | derived; raw evidence retained |
| run summary and manifest | reporting/finalization owners | users, automation, Portfolio | immutable after finalized publication except versioned repair workflow |
| application state | designated state adapter | entrypoints/application | never project authority |

## 8. Project and template boundary

Framework code and framework documentation must remain language-neutral. Language identifiers such as `Sqi`, Albanian module names or Albanian source paths belong only in the active project, explicit examples or historical migration fixtures.

The active-project lock governs real project relationships:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The template lock governs generic initialization structure:

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

The template must not be treated as evidence that an active project implements every placeholder contract.

## 9. Change control

A contract-changing edit requires:

1. identify the contract ID;
2. identify provider, all consumers and owner documents;
3. classify the change as compatible, breaking or documentation repair;
4. update models, ports, adapters and entrypoints as applicable;
5. update persisted schemas and migrations when applicable;
6. update tests and reproducible evidence;
7. update implementation alignment;
8. update this lock and the documentation correction ledger;
9. publish deprecation or migration notes for breaking changes.

A documentation-only edit is compatible only when it does not change normative meaning.

## 10. Validation checklist

```text
[ ] one active project per workspace remains true
[ ] one active project and target per run remain true
[ ] provider and consumers agree
[ ] dependency direction remains hexagonal
[ ] CLI and GUI do not duplicate domain rules
[ ] scan and compile remain distinct
[ ] raw evidence is preserved
[ ] artifacts have one owner
[ ] persisted changes are versioned
[ ] project facts remain under project/
[ ] template content remains generic
[ ] Wordbench has no reverse dependency on gf-portfolio
[ ] implementation claims have source or reproducible evidence
[ ] ledger and implementation alignment are updated
```
