# GF Wordbench — Product Boundaries

| Champ | Valeur |
|---|---|
| Document role | Product boundary authority |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |
| Alignment authority | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Related decisions | ADR-0001, ADR-0011, ADR-0012 |

## 1. Purpose

This document defines the product boundaries between GF Wordbench, Grammatical Framework and independent companion products.

It is authoritative for ownership, dependency direction and independence requirements.

## 2. GF Wordbench

GF Wordbench is responsible for validating one active GF language project in one workspace.

Each run resolves:

```text
one active project
one normative language target
one run identity
```

GF Wordbench owns:

- active-project loading and validation;
- static source scanning;
- GF execution orchestration;
- scenario execution orchestration;
- evidence capture;
- output normalization;
- diagnostic classification;
- regression comparison;
- run lifecycle and finalization;
- human-readable and machine-readable reports;
- release gates;
- public versioned run artifacts.

GF Wordbench does not own:

- a registry of several Wordbench workspaces;
- multilingual portfolio aggregation;
- cross-project comparison;
- portfolio readiness scoring;
- cross-workspace orchestration;
- companion-product storage or services.

## 3. Grammatical Framework

Grammatical Framework is authoritative for:

- GF syntax;
- type checking;
- module resolution;
- compilation;
- runtime behavior;
- parsing;
- linearization;
- generation;
- native GF diagnostics;
- GF-produced artifacts.

GF Wordbench must not present static scanning as equivalent to GF parsing, type checking or compilation.

GF Wordbench may classify, normalize, compare and report GF evidence, but it does not replace GF as the language execution authority.

## 4. Active-project ownership

Language-specific facts belong to the active project:

```text
project/project.toml
project/docs/
project/validation/
the configured GF source tree
```

These facts include:

- project and language identity;
- source roots;
- GF module suffixes;
- entrypoints and checkpoints;
- linguistic architecture;
- category and lincat contracts;
- morphology and syntax rules;
- scenarios, inputs and gold files;
- project release criteria.

Framework documentation and code remain language-neutral.

## 5. Companion product

The canonical companion product is:

```text
gf-portfolio
```

`gf-portfolio` may consume public, versioned GF Wordbench artifacts in read-only mode.

It may own:

- a registry of Wordbench workspaces;
- multi-project inventory;
- multilingual aggregation;
- cross-project comparison;
- portfolio readiness and trends;
- portfolio-specific schemas, storage and reports.

GF Wordbench does not depend on:

- the `gf-portfolio` runtime;
- its private Python modules;
- its schemas;
- its database or storage;
- its configuration;
- its services;
- its user-interface state.

## 6. Dependency direction

Allowed:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

Prohibited:

```text
GF Wordbench -> gf-portfolio runtime
GF Wordbench -> gf-portfolio private schemas
GF Wordbench -> gf-portfolio storage
GF Wordbench -> gf-portfolio configuration
GF Wordbench -> gf-portfolio services
gf-portfolio -> private GF Wordbench implementation modules
```

The interoperability boundary is formed by public Wordbench artifacts and their documented schema versions.

## 7. Public artifact boundary

Public Wordbench artifacts may include:

```text
summary.json
manifest.json
summary.md
AI_READY.md
documented raw evidence references
```

Public artifacts identify, as applicable:

- schema version;
- run identity;
- active project identity;
- validation mode;
- terminal outcome;
- GF version;
- timestamps;
- artifact references.

External consumers must not require private Wordbench state or reconstruct internal behavior from undocumented files.

## 8. Independence requirement

GF Wordbench must be installable, executable, testable and usable when every companion product is absent.

The independence test requires that Wordbench can:

- load its active project;
- resolve its GF environment;
- execute validation;
- capture evidence;
- generate reports;
- evaluate release gates;
- pass its test suite;

without `gf-portfolio` installed, configured or reachable.

A companion-product failure must not alter a completed Wordbench run or its artifacts.

## 9. Non-goals

GF Wordbench does not:

- manage several active projects in one workspace;
- validate several active projects in one run;
- provide a portfolio dashboard;
- compare maturity across workspaces;
- require a shared private database;
- expose private modules as an integration contract;
- use companion-product state as project authority;
- delegate GF execution authority to a companion product.

## 10. Change rule

A change to this boundary requires coordinated updates to:

- the relevant ADRs;
- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`;
- `docs/INTERFILE_CONTRACT_LOCK.md`;
- public artifact contracts;
- dependency tests;
- product overview and scope documentation.

A local documentation correction must not redefine these boundaries.
