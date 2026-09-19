# GF Wordbench — Documentation Alignment Lock

**Document ID:** `GF-WB-DOC-ALIGNMENT-LOCK`
**Status:** Normative
**Contract version:** `2.0.0`
**Applies to:** all GF Wordbench documentation, framework contracts, path-resolved language startup, optional validation profiles, project templates and documentation correction work
**Does not govern:** private implementation details that do not affect a documented contract; the independent `gf-portfolio` repository except at the public interoperability boundary
**Owner:** GF Wordbench maintainers
**Last reviewed:** `2026-07-30`
**Change authority:** `ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`
**Change policy:** coordinated update of every affected owner document and lock

---

## 1. Purpose

This file prevents semantic drift while GF Wordbench documentation is corrected in parallel conversations.

Every correction MUST preserve the accepted product identity, architectural decisions, ownership boundaries and implementation-status distinctions defined here. A local rewrite MUST NOT invent a different product model merely because the source file is ambiguous, incomplete, historical or obsolete.

This lock is a cross-document interpretation lock. It does not replace specialized contract locks or accepted ADRs.

Version `2.0.0` aligns the documentation baseline with path-resolved language startup under ADR-0015. It replaces the earlier assumptions that normal startup requires one repository-local active project, a static language catalog or a mandatory language bundle.

## 2. Authority and precedence

When two documents disagree, use this order:

1. accepted ADRs that have not been superseded for the disputed subject;
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
templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md
```

Supersession must be applied before general precedence. In particular:

```text
ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
    supersedes ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md

ADR-0015
    supersedes the workspace-coupled startup portions of ADR-0001

ADR-0001
    remains authoritative for one active language context per session
    and one language identity per ordinary run
```

A contradiction MUST NOT be resolved silently. Mark the affected correction `BLOCKED` or `REVIEW_REQUIRED` in `docs/DOCUMENTATION_CORRECTION_LEDGER.md`, identify both authorities and update the owner documents together.

## 3. Accepted product decisions

### 3.1 One active resolved language context

A running GF Wordbench session has either:

```text
no resolved language context
or
exactly one resolved language context
```

Every ordinary validation run resolves exactly one language identity, one source context and one immutable effective configuration.

Wordbench may offer an introduction surface and language selection workflow. It does not provide:

- simultaneous active language contexts in one runtime;
- one run combining sources, scenarios, golds, baselines or release evidence from several languages;
- a Wordbench-owned registry of several independent workspaces;
- portfolio-wide readiness, comparison or navigation;
- cross-workspace orchestration.

Changing language ends the current runtime and resolves a new context. It is not an in-place mutation of an active run.

### 3.2 Path-resolved language startup

Normal startup begins from one explicit path supplied by the user, CLI or automation:

```text
one GF language directory
or
one .gf file inside that language directory
```

Wordbench may derive a bounded language candidate from that path. It MUST reuse the existing public services that own:

```text
source enumeration and filtering
path normalization and containment
module-name extraction
GF path resolution
preflight validation
GF execution
canonical diagnostics
run evidence and reporting
```

The probe or startup orchestrator MUST NOT implement a second production scanner, GF path resolver, compiler, process runner or diagnostic parser.

Normal startup does not require:

- `rgl-language-catalog.json`;
- a catalog language ID;
- a mandatory `language.toml`;
- a mandatory language bundle;
- `project/project.toml`;
- scenarios, inputs or gold files;
- language-specific Wordbench documentation;
- a successful release build.

A static RGL catalog may exist only as a non-authoritative, regenerable inventory, diagnostic artifact, migration aid or test fixture. It MUST NOT control normal startup.

A language bundle or `project.toml` may exist as an explicit optional validation profile. It MUST NOT be inferred or required merely to browse, scan or compile a standard language source directory.

### 3.3 Capability levels

Documentation MUST distinguish the capability actually established by evidence:

```text
source-ready
scan-ready
compile-ready
scenario-ready
release-ready
```

A higher capability may depend on additional tools or profile-owned assets. Failure of one optional capability MUST NOT erase an unrelated valid capability.

Examples:

```text
GF executable unavailable
→ source-ready and scan-ready may remain available
→ compile-ready is unavailable

no scenario profile
→ source browsing and compilation may remain available
→ scenario-ready is unavailable

no release profile
→ ordinary validation may remain available
→ release-ready is not claimed
```

### 3.4 GF authority

Grammatical Framework is the authority for GF parsing, type checking, module resolution, compilation, scenario execution and generated GF artifacts.

Wordbench owns orchestration, bounded static prechecks, evidence capture, normalization, classification, comparison, reporting and policy gates.

A static scan MUST NOT be described as equivalent to GF compilation. Scan and compile remain distinct validation stages.

The path-resolved startup service may classify filename candidates and coordinate validation. It MUST NOT claim to reproduce GF import or module semantics.

### 3.5 Native scenarios and golds

Native `.gfs` scenarios remain the scenario execution format.

Native `.gfs` scenarios remain the scenario execution format when an explicit scenario profile is loaded.

Raw tool evidence is preserved before normalization. Stable markers, normalization profiles and reviewed gold files are validation-profile-owned contracts.

Scenarios and golds are not prerequisites for `source-ready`, `scan-ready` or ordinary targeted compilation unless an explicit profile or requested mode makes them required.

### 3.6 Wordbench architecture

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

Path-resolved language orchestration belongs to the `projects` application boundary. Existing owners retain their responsibilities:

```text
file selection       → validation
GF path resolution   → GF anti-corruption boundary
preflight            → runs/application services
GF execution         → validation through GfToolPort
canonical diagnostics→ diagnostics
run evidence         → runs and reporting
local remembered path→ state repository
```

An accepted target architecture is not proof that the current code already implements it. Documentation MUST state implementation and verification status separately.

### 3.7 Independent Portfolio product

Multi-workspace management, multilingual portfolio aggregation, cross-project readiness and portfolio views belong to the independent companion product `gf-portfolio`.

The dependency direction is:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
GF Wordbench -X-> gf-portfolio runtime, code, private schemas, storage or configuration
```

GF Wordbench MUST start, browse, scan, validate, report, release and pass its tests without `gf-portfolio` installed or reachable.

Interoperability is optional, versioned and consumer-oriented. Wordbench owns the public artifacts it emits. Consumer-specific adapters belong to `gf-portfolio` unless a separate accepted decision assigns otherwise.

### 3.8 Diagnostic tool registry

Executable diagnostic tools are controlled by a static allowlist with explicit command contracts, paths, flags, timeouts, output limits, mutability and evidence roles.

Arbitrary command execution is outside the accepted design. AI-assisted tools are optional, visible and non-normative.

The language probe does not bypass the diagnostic registry, external-tool boundary or process-execution contracts.

## 4. Product ownership boundary

| Capability or fact | Owner |
|---|---|
| Explicit selected language path | GUI, CLI or automation request |
| Language candidate orchestration | GF Wordbench `projects` application service |
| Published `ResolvedLanguageContext` | GF Wordbench runtime composition |
| GF source enumeration, filtering and deterministic ordering | GF Wordbench validation selection service |
| GF path canonicalization and effective-path construction | GF anti-corruption boundary |
| Static scanning, compilation and scenarios | GF Wordbench validation services |
| Structural and capability-specific preflight | GF Wordbench run/application services |
| Wordbench run lifecycle and evidence | GF Wordbench |
| Diagnostics and Wordbench reports | GF Wordbench |
| Last selected machine-local path | GF Wordbench application state |
| Optional validation profile | The explicitly selected profile and its owner |
| Existing `project/project.toml` | Optional repository-local validation profile |
| Profile-owned scenarios, inputs, golds and release policy | Explicit validation profile |
| Reusable validation-profile initialization structure | `templates/validation-profile/` |
| Public versioned run artifacts | GF Wordbench |
| Registry of several Wordbench workspaces | `gf-portfolio` |
| Cross-workspace or multilingual aggregation | `gf-portfolio` |
| Portfolio readiness, comparison and navigation | `gf-portfolio` |
| Consumer-specific artifact ingestion adapters | `gf-portfolio` |

Wordbench documentation may describe the public artifact boundary. It MUST NOT define `gf-portfolio` internals as part of Wordbench.

No optional profile, catalog, template or remembered state value may replace the published resolved language context as the runtime authority.

## 5. Canonical paths and identities

### 5.1 Path-resolved startup concepts

```text
selected language path:
    one explicit machine-local directory or .gf file

candidate language directory:
    selected directory, or parent of selected .gf file

RGL source root:
    nearest validated supported ancestor, normally <rgl-root>/src

RGL root:
    parent of the resolved standard RGL source root when applicable

resolved language context:
    immutable runtime model created after structural validation
```

### 5.2 Optional profile paths

```text
repository-local optional profile: project/project.toml
repository-local optional profile docs: project/docs/
repository-local optional profile validation: project/validation/
reusable optional profile template: templates/validation-profile/
```

These paths remain canonical for the bundled example/profile layout. They are not mandatory startup paths and do not own a language selected elsewhere.

### 5.3 Framework and run paths

```text
framework documentation: docs/
run directory: run_<run-id>/
public run artifacts: summary.json, manifest.json, summary.md, AI_READY.md and documented raw evidence
companion product identity: gf-portfolio
```

### 5.4 Identity rules

Portable language identity is derived from the validated source context, not from an absolute machine path, translated display label, stale application-state value or prior run directory.

Documentation may use concepts such as:

```text
portable language key
language directory relative to the RGL source root
optional unambiguous module suffix
selected target identity
optional validation-profile identity and digest
```

The exact persisted field names belong to the persisted-schema owner documents.

Environment-specific absolute paths are examples or permitted local state only. Historical machine paths MUST NOT be presented as portable repository contracts.

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

Do not convert `Accepted` ADR status into `IMPLEMENTED`.

Do not state that a command, GUI feature, probe service, schema, migration, capability status or test exists without source or reproducible run evidence.

Documentation written before ADR-0015 may describe catalog-driven or mandatory-project startup only as historical behavior unless current code evidence establishes a compatibility path.

## 7. Prohibited drift

A correction MUST NOT introduce or normalize any of the following inside Wordbench:

- `projects/<id>/` as a multi-project runtime registry;
- several simultaneously active resolved language contexts;
- one run combining several language identities or source contexts;
- a Wordbench-owned portfolio registry;
- portfolio fields in optional profiles, Wordbench application state, run summaries or manifests;
- a shared private database or mandatory service between Wordbench and `gf-portfolio`;
- imports or runtime calls from Wordbench to `gf-portfolio`;
- Portfolio as a prerequisite for Wordbench startup, validation or tests;
- `rgl-language-catalog.json` as a normal startup or runtime authority;
- a mandatory `language.toml` or language bundle for source browsing, static scan or targeted compilation;
- `project/project.toml` as an unconditional application-startup authority;
- an unbounded filesystem-wide language search;
- fuzzy, newest-file or first-enumerated-candidate selection;
- a second production source enumerator that duplicates the validation selection service;
- a second production GF path resolver;
- a second production GF compiler or direct subprocess path in the language probe;
- independent GUI and CLI language-resolution algorithms;
- application state treated as trusted executable context;
- all sibling language directories added automatically to the GF path;
- static-scan results described as GF compilation results;
- normalized output replacing or destroying raw evidence;
- planned behavior described as current implementation;
- language-specific facts hard-coded into framework defaults;
- template placeholders presented as verified selected-language facts;
- optional profile facts silently applied to a different selected language context.

## 8. Owner documents

| Subject | Primary owner |
|---|---|
| Product identity and non-goals | `docs/PRODUCT_OVERVIEW.md`, `docs/SCOPE_AND_NON_GOALS.md` |
| Single-language runtime boundary | ADR-0001 and `docs/architecture/PRODUCT_BOUNDARIES.md` |
| Path-resolved startup and language switching | ADR-0015 |
| Historical catalog-driven startup | ADR-0014 |
| Portfolio separation | ADR-0011, ADR-0012 |
| Architecture target and actual alignment | ADR-0008, `docs/architecture/IMPLEMENTATION_ALIGNMENT.md` |
| Component ownership and execution flow | `docs/architecture/COMPONENT_MAP.md`, `docs/architecture/EXECUTION_FLOW.md` |
| Framework file boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| GF and external processes | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats, application state and public artifacts | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Selected-path and environment semantics | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| Optional profile contract | `docs/configuration/PROJECT_TOML_REFERENCE.md`, profile-local contracts |
| GF path resolution | `docs/gf/GF_PATH_RESOLUTION.md` |
| File selection ownership | `docs/validation/FILE_SELECTION.md` |
| GUI language-open workflow | `docs/usage/GUI_REFERENCE.md` |
| CLI language-path workflow | `docs/usage/CLI_REFERENCE.md`, command registry |
| Generic optional-profile initialization structure | `templates/validation-profile/` |
| Documentation correction state | `docs/DOCUMENTATION_CORRECTION_LEDGER.md` |

An overview may summarize an owner document but MUST NOT create a second independently maintained normative definition.

## 9. Parallel correction protocol

Each parallel conversation MUST:

1. receive the current version of this lock;
2. receive exactly one target file unless a coordinated update is explicitly assigned;
3. receive any directly relevant ADR or specialized lock;
4. apply ADR supersession before interpreting older wording;
5. preserve the target file's legitimate subject matter;
6. remove or qualify contradictions, obsolete names, stale paths and unsupported implementation claims;
7. preserve the distinction between path-resolved startup and optional validation profiles;
8. report which decisions and owners were applied;
9. return the complete corrected file;
10. update one ledger row after integration.

A parallel conversation MUST NOT edit this lock or reinterpret the product boundary locally unless it was explicitly assigned the coordinated alignment-lock update.

## 10. Correction acceptance checklist

A corrected file is `VALIDATED` only when:

```text
[ ] it agrees with accepted, non-superseded ADR rules
[ ] it agrees with this alignment lock
[ ] it agrees with the relevant specialized lock
[ ] ADR-0015 supersession of ADR-0014 is applied where relevant
[ ] one active resolved language context per session remains explicit
[ ] one language identity per ordinary run remains explicit
[ ] Wordbench and gf-portfolio ownership are not mixed
[ ] normal startup is not made dependent on a catalog or mandatory profile
[ ] selected-path discovery is bounded and explicit
[ ] existing selection, GF path, preflight and execution owners are reused
[ ] optional profile facts are identified as optional and explicitly loaded
[ ] capability claims distinguish source, scan, compile, scenario and release readiness
[ ] planned and implemented behavior are distinguished
[ ] paths, names, statuses and links are canonical
[ ] absolute machine paths are not presented as portable identities
[ ] template content remains generic
[ ] no unsupported capability was invented
[ ] contradictions were escalated rather than hidden
[ ] migration or historical behavior is labeled accurately
[ ] the ledger records the result
```

## 11. Migration interpretation

Until all owner documents are aligned, apply these rules:

```text
“catalog-driven startup”
    → historical ADR-0014 behavior

“catalog language ID is the startup authority”
    → obsolete for normal startup

“project/project.toml is the active-language startup authority”
    → obsolete for normal startup
    → valid only when explicitly loaded as an optional profile

“one language per workspace”
    → reinterpret as one active resolved language context per session
      and one language identity per ordinary run

“language bundle is required”
    → obsolete for source-ready, scan-ready and ordinary compile-ready use
    → may remain an optional profile or release asset layout

“last_language_id”
    → catalog-era state
    → migrate toward a revalidated last selected path

“project-owned scenarios and golds”
    → profile-owned scenarios and golds
    → required only by the selected validation mode or release profile
```

Compatibility adapters may temporarily support historical inputs, but documentation MUST NOT present compatibility behavior as the new normative authority.

## 12. Change control

Changing this lock requires:

1. identifying the accepted ADR or coordinated decision that authorizes the change;
2. updating every affected specialized lock;
3. updating owner documents;
4. reviewing path-resolved startup, optional-profile, state and template consequences;
5. recording migration or deprecation effects;
6. incrementing this lock's contract version;
7. updating the correction ledger;
8. verifying that architecture, contract and documentation tests reference the new baseline.

A single-file documentation correction MUST NOT change this baseline.
