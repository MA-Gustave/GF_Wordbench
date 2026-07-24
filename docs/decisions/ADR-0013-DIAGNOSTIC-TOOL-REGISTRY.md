# ADR-0013 — Diagnostic Tool Registry

| Field | Value |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |

## Context

GF Wordbench may use several diagnostic tools in addition to the Grammatical Framework executable. These tools can differ significantly in purpose, permissions, mutability, output volume, execution time, network access and evidentiary value.

Without a controlled registry, diagnostic execution could bypass the normal process boundary, introduce arbitrary command execution, mutate project files unexpectedly, expose sensitive data, produce unbounded output or confuse optional analysis with normative GF evidence.

The diagnostic subsystem therefore needs one explicit source of authority for every executable tool it may invoke.

## Decision

> **Every executable diagnostic tool used by GF Wordbench MUST be registered in a static allowlist with an explicit execution contract.**

The registry is owned by the diagnostics module and is enforced through the standard external-tool boundary.

Each registered tool defines at least:

```text
tool identifier
purpose
executable resolution policy
allowed arguments and flags
working-directory policy
input policy
timeout
output-size limits
mutability
network policy
evidence role
normalization policy
diagnostic parser
availability requirements
```

The following rules apply:

- arbitrary user-supplied commands are prohibited;
- a registered tool cannot bypass the central process runner;
- executable paths and arguments are resolved and validated before launch;
- shell interpolation is prohibited unless a separate accepted security contract explicitly requires it;
- project-controlled text cannot become a host command;
- read-only tools are the default;
- mutating tools require explicit user intent and a dedicated workflow;
- mutating tools cannot run during normal validation or release checks unless their mutation is the declared purpose of that workflow;
- timeouts, cancellation, output limits and process termination are mandatory parts of the contract;
- stdout, stderr, exit state, timing and produced artifacts are preserved as raw evidence;
- normalization and diagnostic parsing occur only after raw evidence has been captured;
- tool launch failures, timeouts, non-zero exits, malformed output and missing expected artifacts remain distinct outcomes;
- optional diagnostic-tool failure does not invalidate authoritative GF evidence unless the tool is explicitly required by the relevant validation contract.

## AI-assisted tools

AI-assisted diagnostic tools are permitted only as optional registered tools.

They must be:

- explicitly identified as AI-assisted;
- visible in configuration, execution evidence and reports;
- isolated from normative GF validation results;
- prevented from silently modifying project sources, scenarios, gold files or release artifacts;
- subject to the same timeout, output, path, network and evidence controls as other tools;
- treated as advisory rather than authoritative.

An AI-assisted result may explain, summarize or propose. It cannot replace GF compilation, native `.gfs` scenario execution, reviewed gold comparison or other project-owned release evidence.

## Product boundary

The registry belongs to GF Wordbench and applies to diagnostic execution for one active project in one run.

It does not provide:

- arbitrary plugin execution;
- cross-workspace orchestration;
- a multi-project diagnostic scheduler;
- Portfolio-owned tool configuration;
- a runtime dependency on `gf-portfolio`.

`gf-portfolio` may consume public, versioned Wordbench artifacts. Any executable-tool registry specific to Portfolio belongs to that independent product.

## Consequences

### Positive consequences

- executable diagnostics remain auditable and reproducible;
- command construction and process execution stay inside one controlled boundary;
- mutating and read-only tools are clearly separated;
- security review can reason about a finite set of tools and behaviors;
- reports can distinguish authoritative evidence from advisory diagnostics;
- tests can validate each tool contract independently;
- optional tools cannot silently redefine release readiness.

### Costs and constraints

- adding a diagnostic tool requires a registry change and review;
- tool-specific adapters, parsers and fixtures must be maintained;
- supported flags and versions must remain synchronized with the registry contract;
- tools that cannot operate within the required path, timeout, output and evidence controls cannot be integrated.

## Alternatives rejected

### Arbitrary command execution

Allowing users or project files to provide unrestricted commands would bypass the process boundary and create unacceptable command-injection, path, mutation and reproducibility risks.

### Dynamic plugin discovery

Automatically discovering executable plugins would make the effective execution surface environment-dependent and difficult to audit, test and secure.

### Direct execution from diagnostics code

Letting individual diagnostic components invoke subprocesses directly would duplicate timeout, cancellation, evidence and security behavior and would break the external-tool contract.

### Treating AI tools as normative validators

AI-generated analysis is not a substitute for GF execution, deterministic checks or reviewed project evidence.

## Required documentation alignment

The following documents must remain consistent with this decision:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/TOOL_CATALOG.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/COMPONENT_MAP.md
docs/security documentation where executable-tool controls are described
```

## Verification criteria

The decision is satisfied when:

- every executable diagnostic tool is represented by one registry entry;
- unregistered tools cannot be executed through GF Wordbench;
- registry entries define executable resolution, arguments, paths, timeouts, output limits, mutability, network policy and evidence role;
- all tools execute through the central external-tool boundary;
- raw process evidence is preserved before normalization or parsing;
- mutating tools require an explicit workflow and cannot run during ordinary read-only validation;
- AI-assisted tools remain optional, visible and non-normative;
- tests cover accepted requests, rejected requests, launch failures, timeouts, output limits and mutation restrictions;
- documentation does not describe arbitrary command or plugin execution as supported behavior;
- GF Wordbench remains independent from `gf-portfolio`.
