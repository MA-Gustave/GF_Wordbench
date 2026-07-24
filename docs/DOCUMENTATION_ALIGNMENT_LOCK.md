# GF Wordbench — Documentation Alignment Lock

**Document ID:** `GF-WB-DOC-ALIGNMENT-LOCK`  
**Status:** Normative  
**Contract version:** `1.0.0`  
**Applies to:** all GF Wordbench documentation, framework contracts, active-project documentation, project templates and documentation correction work  
**Does not govern:** private implementation details that do not affect a documented contract; the independent `gf-portfolio` repository except at the public interoperability boundary  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Change policy:** coordinated update of every affected owner document and lock

---

## 1. Purpose

This file prevents semantic drift while GF Wordbench documentation is corrected in parallel conversations.

Every correction MUST preserve the accepted product identity, architectural decisions, ownership boundaries and implementation-status distinctions defined here. A local rewrite MUST NOT invent a different product model merely because the source file is ambiguous or obsolete.

This lock is a cross-document interpretation lock. It does not replace the specialized contract locks or the accepted ADRs.

## 2. Authority and precedence

When two documents disagree, use this order:

1. accepted ADRs;
2. this documentation alignment lock for cross-document interpretation;
3. specialized normative locks;
4. the document that owns the specific fact or contract;
5. overview, tutorial, quick-start, example and historical documents.

The specialized locks are:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

A contradiction MUST NOT be resolved silently. Mark the affected correction `BLOCKED` or `REVIEW_REQUIRED` in `docs/DOCUMENTATION_CORRECTION_LEDGER.md`, identify both authorities and update the owner documents together.

## 3. Accepted product decisions

### 3.1 One active project

One GF Wordbench workspace contains exactly one active GF language project. Every validation run resolves exactly one active project identity and one normative language target.

Wordbench does not provide:

- a runtime language-profile selector;
- a multi-project registry inside one workspace;
- simultaneous validation of several active language projects in one run;
- a portfolio-wide readiness or comparison view;
- cross-workspace orchestration.

A single executable or package may serve several isolated Wordbench workspaces. The restriction applies per workspace and per run.

### 3.2 GF authority

Grammatical Framework is the authority for GF parsing, type checking, compilation, scenario execution and generated GF artifacts. Wordbench owns orchestration, static prechecks, evidence capture, normalization, classification, comparison, reporting and release gates.

A static scan MUST NOT be described as equivalent to GF compilation. Scan and compile remain distinct validation stages.

### 3.3 Native scenarios and golds

Native `.gfs` scenarios remain the scenario execution format. Raw tool evidence is preserved before normalization. Stable markers, normalization profiles and reviewed gold files are project-owned validation contracts.

### 3.4 Wordbench architecture

The accepted target architecture is one deployable hexagonal modular monolith. Its functional modules are:

```text
projects
runs
validation
diagnostics
reporting
```

Its architectural rings are:

```text
domain
application
ports
adapters
entrypoints
bootstrap
```

An accepted target architecture is not proof that the current code already implements it. Documentation MUST state implementation and verification status separately.

### 3.5 Independent Portfolio product

Multi-workspace management, multilingual portfolio aggregation, cross-project readiness and portfolio views belong to the independent companion product `gf-portfolio`.

The dependency direction is:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
GF Wordbench -X-> gf-portfolio runtime, code, private schemas, storage or configuration
```

GF Wordbench MUST start, validate, report, release and pass its tests without `gf-portfolio` installed or reachable.

Interoperability is optional, versioned and consumer-oriented. Wordbench owns the public artifacts it emits. Consumer-specific adapters belong to `gf-portfolio` unless a separate accepted decision assigns otherwise.

### 3.6 Diagnostic tool registry

Executable diagnostic tools are controlled by a static allowlist with explicit command contracts, paths, flags, timeouts, output limits, mutability and evidence roles. Arbitrary command execution is outside the accepted design. AI-assisted tools are optional, visible and non-normative.

## 4. Product ownership boundary

| Capability or fact | Owner |
|---|---|
| Active project identity and `project/project.toml` | GF Wordbench active project |
| GF source selection, scanning, compilation and scenarios | GF Wordbench |
| Wordbench run lifecycle and evidence | GF Wordbench |
| Diagnostics and Wordbench reports | GF Wordbench |
| Language-specific architecture, contracts and research evidence | Active project under `project/` |
| Reusable single-project initialization structure | `templates/project/` |
| Public versioned run artifacts | GF Wordbench |
| Registry of several Wordbench workspaces | `gf-portfolio` |
| Cross-workspace or multilingual aggregation | `gf-portfolio` |
| Portfolio readiness, comparison and navigation | `gf-portfolio` |
| Consumer-specific artifact ingestion adapters | `gf-portfolio` |

Wordbench documentation may describe the public artifact boundary. It MUST NOT define `gf-portfolio` internals as part of Wordbench.

## 5. Canonical paths and identities

```text
active project root: project/
active project configuration: project/project.toml
active project documentation: project/docs/
active project validation: project/validation/
reusable project template: templates/project/
framework documentation: docs/
run directory: run_<run-id>/
public run artifacts: summary.json, manifest.json, summary.md, AI_READY.md and documented raw evidence
companion product identity: gf-portfolio
```

Environment-specific absolute paths are examples only unless an owner schema explicitly permits them. Historical machine paths MUST NOT be presented as portable repository contracts.

## 6. Implementation-truth labels

Every material capability claim MUST be classified by evidence:

| Label | Meaning |
|---|---|
| `IMPLEMENTED` | Current code or artifact exists and has reproducible evidence |
| `PARTIALLY_IMPLEMENTED` | Some required behavior exists; named gaps remain |
| `PLANNED` | Accepted target or documented work not yet implemented |
| `PROPOSED` | Not accepted as a governing decision |
| `HISTORICAL` | Retained only for migration or audit context |
| `UNKNOWN` | The supplied evidence cannot establish the state |

Do not convert `Accepted` ADR status into `IMPLEMENTED`. Do not state that a command, GUI feature, schema, migration or test exists without source or reproducible run evidence.

## 7. Prohibited drift

A correction MUST NOT introduce or normalize any of the following inside Wordbench:

- `projects/<id>/` as a multi-project runtime model;
- selectable language profiles in GUI state or CLI state;
- a Wordbench-owned portfolio registry;
- one run combining several active projects;
- portfolio fields in `project.toml`, Wordbench application state, run summaries or manifests;
- a shared private database or mandatory service between Wordbench and `gf-portfolio`;
- imports or runtime calls from Wordbench to `gf-portfolio`;
- Portfolio as a prerequisite for Wordbench startup, validation or tests;
- static-scan results described as GF compilation results;
- normalized output replacing or destroying raw evidence;
- planned behavior described as current implementation;
- language-specific facts moved from `project/` into framework defaults;
- template placeholders presented as verified active-project facts.

## 8. Owner documents

| Subject | Primary owner |
|---|---|
| Product identity and non-goals | `docs/PRODUCT_OVERVIEW.md`, `docs/SCOPE_AND_NON_GOALS.md` |
| Product boundary | `docs/architecture/PRODUCT_BOUNDARIES.md`, ADR-0001, ADR-0011, ADR-0012 |
| Architecture target and actual alignment | ADR-0008, `docs/architecture/IMPLEMENTATION_ALIGNMENT.md` |
| Framework file boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| GF and external processes | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats and public artifacts | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Active language facts and GF interfile contracts | `project/project.toml`, `project/docs/` |
| Generic initialized-project structure | `templates/project/` |
| Documentation correction state | `docs/DOCUMENTATION_CORRECTION_LEDGER.md` |

An overview may summarize an owner document but MUST NOT create a second independently maintained normative definition.

## 9. Parallel correction protocol

Each parallel conversation MUST:

1. receive this file unchanged;
2. receive exactly one target file;
3. receive any directly relevant ADR or specialized lock;
4. modify only the target file unless explicitly assigned a coordinated lock update;
5. preserve the target file's legitimate subject matter;
6. remove or qualify contradictions, obsolete names, stale paths and unsupported implementation claims;
7. report which decisions and owners were applied;
8. return the complete corrected file;
9. update one ledger row after integration.

A parallel conversation MUST NOT edit this lock or reinterpret the product boundary locally.

## 10. Correction acceptance checklist

A corrected file is `VALIDATED` only when:

```text
[ ] it agrees with accepted ADRs
[ ] it agrees with this alignment lock
[ ] it agrees with the relevant specialized lock
[ ] Wordbench and gf-portfolio ownership are not mixed
[ ] mono-project and one-target-per-run rules remain explicit where relevant
[ ] planned and implemented behavior are distinguished
[ ] paths, names, statuses and links are canonical
[ ] project facts remain under project/
[ ] template content remains generic
[ ] no unsupported capability was invented
[ ] contradictions were escalated rather than hidden
[ ] the ledger records the result
```

## 11. Change control

Changing this lock requires:

1. identifying the accepted ADR or coordinated decision that authorizes the change;
2. updating every affected specialized lock;
3. updating owner documents;
4. reviewing active-project and template consequences;
5. recording migration or deprecation effects;
6. incrementing this lock's contract version;
7. updating the correction ledger.

A single-file documentation correction MUST NOT change this baseline.
