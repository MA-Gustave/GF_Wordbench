# GF Wordbench — Architecture Decision Records

**Document role:** ADR registry and process
**Decision status:** Accepted
**Implementation status:** Not established by this documentation update
**Verification status:** Requires current code and reproducible test evidence
**Owner:** GF Wordbench maintainers
**Last reviewed:** `2026-07-30`

## Purpose

Architecture Decision Records capture durable choices that constrain implementation, public contracts, ownership, persisted meaning, execution boundaries or release behavior.

ADR status and implementation status are separate. `Accepted` means the direction is decided; it does not mean the code is complete or verified.

## Required metadata

Every ADR records its identifier, title, decision status, implementation status, verification status, owners, decision date, consequences, alternatives and evidence required.

Every ADR identifier is unique. Two independent decisions must not use the same ADR number.

When a later ADR changes only part of an earlier decision:

* the earlier ADR remains in the registry;
* its status identifies the partial supersession;
* the later ADR identifies the exact rules it replaces;
* the preserved invariants remain explicitly documented.

When a later ADR replaces an earlier decision in full:

* the earlier ADR remains available as historical reasoning;
* its status becomes `Superseded`;
* the registry identifies the replacing ADR;
* implementation and documentation follow only the replacing decision where the two conflict.

## Registry

| ADR                                                     | Decision                                                                                                                              | Status                                    |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [ADR-0001](ADR-0001-SINGLE-ACTIVE-LANGUAGE.md)          | One resolved language context per session and one language identity per ordinary run                                                  | Accepted — superseded in part by ADR-0015 |
| [ADR-0002](ADR-0002-GF-AS-EXECUTION-ENGINE.md)          | GF remains the semantic execution authority                                                                                           | Accepted                                  |
| [ADR-0003](ADR-0003-SEPARATE-SCAN-AND-COMPILE.md)       | Static scan and GF compilation remain separate evidence stages                                                                        | Accepted                                  |
| [ADR-0004](ADR-0004-NATIVE-GFS-SCENARIOS.md)            | Runtime scenarios use native `.gfs` scripts                                                                                           | Accepted                                  |
| [ADR-0005](ADR-0005-FILE-AND-SCENARIO-RESULTS.md)       | File and scenario validation use distinct structured result models                                                                    | Accepted                                  |
| [ADR-0006](ADR-0006-AI-READY-REPORT.md)                 | AI-ready output is bounded and non-normative                                                                                          | Accepted                                  |
| [ADR-0007](ADR-0007-GOLDEN-OUTPUT-TESTING.md)           | Reviewed gold files provide deterministic regression references                                                                       | Accepted                                  |
| [ADR-0008](ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md)      | Wordbench is a modular monolith with hexagonal boundaries                                                                             | Accepted                                  |
| [ADR-0009](ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md)     | All GF integration is isolated behind one boundary                                                                                    | Accepted                                  |
| [ADR-0010](ADR-0010-RUN-BUDGET-AND-FINALIZATION.md)     | Runs reserve explicit execution and finalization budgets                                                                              | Accepted                                  |
| [ADR-0011](ADR-0011-SEPARATE-PORTFOLIO.md)              | Multi-workspace portfolio responsibilities are separate                                                                               | Accepted                                  |
| [ADR-0012](ADR-0012-INDEPENDENT-PRODUCTS.md)            | Companion products are optional and independently deployable                                                                          | Accepted                                  |
| [ADR-0013](ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md)        | Executable diagnostic tools are allowlisted                                                                                           | Accepted                                  |
| [ADR-0014](ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md) | Language selection and startup are driven by a versioned RGL language catalog                                                         | Superseded by ADR-0015                    |
| [ADR-0015](ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md)  | Language startup begins from one selected source path and reuses Wordbench validation services to resolve the active language context | Accepted                                  |

## Identifier and filename rules

The canonical ADR filename format is:

```text
ADR-NNNN-STABLE-UPPERCASE-SLUG.md
```

The ADR number is the stable identity of the decision.

Renaming an ADR file does not create a new decision. Reusing an existing ADR number for another decision is prohibited.

Obsolete abbreviated ADR files must be removed after their normative content has been preserved in the canonical ADR. In particular, the registry recognizes only:

```text
ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
ADR-0005-FILE-AND-SCENARIO-RESULTS.md
```

The following older abbreviated filenames are not canonical registry entries:

```text
ADR-0001-SINGLE-ACTIVE-PROJECT.md
ADR-0005-STRUCTURED-RESULTS.md
```

A superseded ADR remains under its canonical filename. Supersession does not authorize deleting or renumbering its historical record.

## Supersession relationships

### ADR-0015 supersedes ADR-0014

`ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` supersedes `ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md` in full.

The following ADR-0014 rules are no longer authoritative for normal startup:

* `rgl-language-catalog.json` as the exclusive registry of loadable languages;
* a catalog language identifier as the only startup selector;
* a mandatory catalog entry for every loadable language;
* mandatory `wordbench_config` and `language.toml` files;
* mandatory language bundles under `gf-rgl/wordbench/languages/`;
* catalog-owned GF search paths;
* prohibition of bounded discovery after one explicit user path selection;
* refusal to load a language that lacks scenarios, golds or language-specific Wordbench documentation.

ADR-0014 remains in the registry as historical reasoning and must identify ADR-0015 as its replacement.

### ADR-0015 partially supersedes ADR-0001

`ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` supersedes the portions of `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` that:

* require one physical Wordbench workspace or repository copy per language;
* make `project/project.toml` the mandatory startup authority;
* prohibit a language-selection introduction surface;
* prohibit application state from remembering the last selected language path;
* require a complete project bundle before Wordbench can browse, scan or compile a language;
* require language-specific documentation, scenarios and golds for basic source access;
* prohibit bounded language discovery from an explicitly selected source path.

`ADR-0001` continues to govern:

* at most one completely resolved language context in a running session;
* exactly one language identity per ordinary run;
* prohibition of language changes during an active run;
* runtime recreation when switching languages;
* prohibition of cross-language source, scenario, gold, baseline or release-evidence mixing;
* separation between GF Wordbench and `gf-portfolio`;
* prohibition of multilingual aggregation inside an ordinary Wordbench run.

Where `ADR-0001` and `ADR-0015` conflict on startup, workspace placement, selected-path resolution, optional validation profiles or application-state convenience paths, `ADR-0015` is authoritative.

Where `ADR-0014` and `ADR-0015` conflict, `ADR-0015` is authoritative.

## Current startup authority

Normal language startup is governed by ADR-0015.

The user supplies exactly one primary path:

```text
a GF language directory
or
a .gf file inside a GF language directory
```

Wordbench then reuses its existing services to resolve and validate the active context:

```text
explicit selected path
→ bounded language probe
→ existing source-selection service
→ existing GF path resolver
→ existing preflight service
→ existing GF and diagnostic boundaries
→ immutable ResolvedLanguageContext
→ main runtime
```

The language probe may propose candidate facts, but it does not become a second scanner, compiler, path resolver or diagnostic parser.

The following are optional advanced validation inputs rather than startup prerequisites:

```text
project.toml validation profile
scenario registry
.gfs scenarios
inputs
gold files
release targets
language-specific documentation
```

## Lifecycle

```text
Proposed → Accepted → Superseded
             ↘ Rejected
```

An ADR may also be superseded only in part.

```text
Accepted
    → Accepted — superseded in part
    → Superseded
```

Accepted ADRs are not edited to hide previous reasoning. A later decision supersedes them explicitly and identifies the exact replacement boundary.

A superseded ADR remains part of the architectural history but does not define current behavior where it conflicts with its replacement.

## Verification

An ADR is considered implemented only when its implementation checklist is complete.

It is considered verified only when named unit, contract, schema, process, real-GF or end-to-end tests reproduce the declared behavior.

A registry entry must not claim implementation or verification solely because its ADR status is `Accepted`.

Registry verification must also confirm:

* every registered link resolves to one canonical ADR file;
* every ADR number appears only once;
* no canonical ADR has an unregistered conflicting sibling;
* every declared supersession target exists;
* every replacing ADR exists;
* reciprocal supersession references are consistent;
* partially superseded ADRs identify the preserved rules;
* fully superseded ADRs do not remain documented as current authority;
* abbreviated or obsolete duplicate ADR files are absent;
* documentation and architecture tests use the canonical filenames.

For the ADR-0015 transition, verification must additionally confirm:

* ADR-0014 is marked `Superseded`;
* ADR-0001 refers to ADR-0015 for current startup behavior;
* normal startup does not require `rgl-language-catalog.json`;
* normal startup does not require `language.toml`;
* GUI and CLI use the same path-resolved language-probe service;
* one immutable resolved language context gates main runtime creation;
* existing file-selection, GF path, preflight, compilation and diagnostic services are reused rather than duplicated.

## Ownership rule

ADRs decide architecture.

Detailed contracts remain in their owning documents, including:

* dependency rules;
* process execution;
* GF integration;
* file selection;
* validation;
* reporting;
* persisted schemas;
* application state;
* selected-path handling;
* path-resolved language startup;
* resolved-language-context construction;
* optional validation profiles;
* project-specific scenarios, golds and release contracts.

The ADR registry owns:

* canonical ADR identifiers;
* canonical ADR filenames;
* decision titles;
* decision status;
* supersession relationships;
* links to the normative decision documents.

It does not replace the detailed behavioral contracts owned by those documents.
