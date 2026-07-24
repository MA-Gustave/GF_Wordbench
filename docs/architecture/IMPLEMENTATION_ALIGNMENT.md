# GF Wordbench — Implementation Alignment

| Champ | Valeur |
|---|---|
| Document role | Architecture-to-code alignment contract |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |

## 1. Purpose

This document defines how the accepted GF Wordbench architecture is reflected across source code, tests, configuration, persisted artifacts and documentation.

It does not track implementation progress. The repository is expected to conform directly to the contracts listed here.

## 2. Alignment rules

- Accepted ADRs define architectural decisions.
- Contract locks define stable boundaries between components, tools, schemas and project-owned files.
- Source code implements those contracts without introducing competing ownership.
- Tests verify observable behavior, dependency direction and artifact integrity.
- Reference documentation describes the same commands, schemas, paths and status values used by the application.
- A component must not claim authority already assigned to another component or document.
- GF Wordbench remains independent from `gf-portfolio`; Portfolio may consume only public, versioned Wordbench artifacts.
- One Wordbench workspace contains one active GF language project, and one run resolves one project and one normative language target.

## 3. Architecture alignment matrix

| Domain | Governing decision or contract | Code ownership | Required verification |
|---|---|---|---|
| Active project | ADR-0001 and project configuration contracts | `projects` module and `project/project.toml` | project loading, schema validation, path resolution and single-project invariants |
| Modular hexagonal monolith | ADR-0008 and `docs/INTERFILE_CONTRACT_LOCK.md` | domain, application, ports, adapters, entrypoints and bootstrap | dependency-direction and forbidden-import tests |
| GF Anti-Corruption Layer | ADR-0009 and `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` | `GfToolPort` and GF adapters | structured request/result tests, diagnostic parsing and real-GF integration tests |
| Process execution | external-tool contract | process port and operating-system adapter | launch, timeout, cancellation, stdout/stderr, exit-state and process-tree tests |
| Validation pipeline | ADR-0003 and validation owner documents | validation module | stage ordering, quick/full/release behavior and prerequisite propagation |
| Native scenarios and golds | ADR-0004, ADR-0007 and scenario contracts | validation module and `project/validation/` | marker extraction, normalization, regression comparison and gold immutability |
| Diagnostics | diagnostic owner documents and ADR-0013 | diagnostics module | direct/downstream classification, controlled tool registry and evidence preservation |
| Reporting and manifests | ADR-0005, ADR-0006 and persisted-schema lock | reporting module | deterministic serialization, schema validation, artifact ownership and manifest integrity |
| Run lifecycle | ADR-0010 and run lifecycle contracts | runs module | timeout budgets, cancellation, finalization, partial-result and cleanup tests |
| Release gates | validation and release owner documents | application use cases and reporting | end-to-end release validation with required artifacts and scenarios |
| CLI and GUI | entrypoint contracts | CLI and GUI adapters | equivalent requests, results, exit semantics and shared application behavior |
| Public Portfolio boundary | ADR-0011 and ADR-0012 | public artifact schemas only | Wordbench independence and read-only consumer compatibility tests |

## 4. Component alignment

### 4.1 Domain

The domain contains business concepts and invariants. It does not depend on:

- GUI or CLI frameworks;
- filesystem implementations;
- subprocess APIs;
- JSON or TOML libraries;
- concrete GF commands;
- `gf-portfolio`.

### 4.2 Application

The application layer coordinates use cases through ports. It owns:

- project loading requests;
- validation orchestration;
- run lifecycle coordination;
- release-gate evaluation;
- report-generation requests.

It does not construct operating-system commands or render user interfaces.

### 4.3 Ports

Ports define stable contracts for external capabilities, including:

- GF execution;
- generic process execution;
- filesystem access;
- clock and run identity;
- persisted state;
- artifact publication.

Ports expose structured requests and results rather than framework-specific objects or shell commands.

### 4.4 Adapters

Adapters implement ports for:

- GF and the operating system;
- filesystems and persisted formats;
- CLI and GUI technologies;
- optional public artifact export.

Adapters translate external behavior without changing domain meaning.

### 4.5 Entrypoints

CLI and GUI entrypoints call the same application use cases. They may differ in presentation but not in validation semantics, project identity, diagnostics or release decisions.

### 4.6 Bootstrap

Bootstrap assembles ports, adapters and application services. It does not contain validation rules or project-specific linguistic facts.

## 5. Documentation ownership

| Subject | Primary owner |
|---|---|
| Product identity and scope | `docs/PRODUCT_OVERVIEW.md`, `docs/SCOPE_AND_NON_GOALS.md` |
| Repository placement | `docs/REPOSITORY_STRUCTURE.md` |
| Component boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| GF and process execution | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted schemas and artifacts | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Architecture decisions | `docs/decisions/` |
| Validation behavior | `docs/validation/` |
| Diagnostic behavior | `docs/diagnostics/` |
| Report formats | `docs/reports/` |
| Active language contracts | `project/docs/` |
| Reusable project structure | `templates/project/` |

A secondary document may summarize an owner document but must not redefine its contract.

## 6. Required repository checks

The repository verification suite must cover:

- allowed and forbidden dependency directions;
- absence of active-language facts in framework code;
- absence of Wordbench dependencies on `gf-portfolio`;
- one active project per workspace;
- one project and normative target per run;
- exclusive GF invocation through `GfToolPort`;
- separation between static scan and GF execution;
- preservation of raw process evidence;
- deterministic structured reports;
- persisted-schema compatibility;
- project/template structural alignment;
- gold-file immutability during normal validation;
- CLI and GUI parity;
- release-gate completeness.

## 7. Change rule

A change is aligned only when all affected elements are updated together:

1. accepted ADR or governing contract;
2. domain and application models;
3. ports and adapters;
4. entrypoints;
5. persisted schemas and migrations;
6. tests;
7. owner documentation;
8. release or compatibility notes when required.

No local implementation may redefine a contract without updating its governing decision and owner documents.
