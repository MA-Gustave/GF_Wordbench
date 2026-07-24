# ADR-0002 — GF as the Execution Engine

**Document role:** Architectural decision record  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Decision

GF is the authoritative engine for GF semantics. GF Wordbench orchestrates GF, preserves evidence, interprets results, and applies project policy; it does not reimplement GF parsing, type checking, module resolution, compilation, PGF construction, shell semantics, parsing, linearization, generation, morphology, or grammar introspection.

The boundary is:

```text
Wordbench use case
→ GfToolPort / GF anti-corruption layer
→ ProcessExecutorPort
→ GF executable
→ raw stdout, stderr and artifacts
→ structured Wordbench result
```

## Wordbench responsibilities

- resolve project and local toolchain configuration;
- build structured GF requests without shell concatenation;
- impose timeouts, cancellation and output limits;
- preserve command metadata, stdout, stderr and produced artifacts;
- verify expected `.gfo` and `.pgf` artifacts;
- normalize only after preserving raw evidence;
- execute project scenarios and assertions;
- classify failures and apply release gates;
- render machine and human reports from structured results.

## Constraints

- No GF command syntax belongs in the domain, CLI, GUI or report writer.
- No process launch occurs outside the process adapter.
- An exit code alone is insufficient when an artifact is required.
- Static scanning never replaces GF validation.
- Tool-version differences are handled by the GF boundary, not scattered through the application.
- Wordbench must run without any companion product.

## Evidence required

Implementation is verified only when tests demonstrate command construction, process isolation, raw-output preservation, artifact verification, version handling, and at least one real-GF end-to-end run.

## Consequences

This decision creates one semantic authority, keeps Wordbench testable with fake process adapters, and prevents a second incomplete implementation of GF behavior.
