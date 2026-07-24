# GF Wordbench — Architecture Decision Records

**Document role:** ADR registry and process  
**Decision status:** Accepted  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`

## Purpose

Architecture Decision Records capture durable choices that constrain implementation, public contracts, ownership, persisted meaning, execution boundaries or release behavior.

ADR status and implementation status are separate. `Accepted` means the direction is decided; it does not mean the code is complete or verified.

## Required metadata

Every ADR records its identifier, title, decision status, implementation status, verification status, owners, decision date, consequences, alternatives and evidence required.

## Registry

| ADR | Decision | Status |
|---|---|---|
| [ADR-0001](ADR-0001-SINGLE-ACTIVE-PROJECT.md) | One active project per workspace | Accepted |
| [ADR-0002](ADR-0002-GF-AS-EXECUTION-ENGINE.md) | GF remains the semantic execution authority | Accepted |
| [ADR-0003](ADR-0003-SEPARATE-SCAN-AND-COMPILE.md) | Static scan and GF compilation remain separate evidence stages | Accepted |
| [ADR-0004](ADR-0004-NATIVE-GFS-SCENARIOS.md) | Runtime scenarios use native `.gfs` scripts | Accepted |
| [ADR-0005](ADR-0005-STRUCTURED-RESULTS.md) | Validation outputs use structured result types | Accepted |
| [ADR-0006](ADR-0006-AI-READY-REPORT.md) | AI-ready output is bounded and non-normative | Accepted |
| [ADR-0007](ADR-0007-GOLDEN-OUTPUT-TESTING.md) | Reviewed gold files provide deterministic regression references | Accepted |
| [ADR-0008](ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md) | Wordbench is a modular monolith with hexagonal boundaries | Accepted |
| [ADR-0009](ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md) | All GF integration is isolated behind one boundary | Accepted |
| [ADR-0010](ADR-0010-RUN-BUDGET-AND-FINALIZATION.md) | Runs reserve explicit execution and finalization budgets | Accepted |
| [ADR-0011](ADR-0011-SEPARATE-PORTFOLIO.md) | Multi-workspace portfolio responsibilities are separate | Accepted |
| [ADR-0012](ADR-0012-INDEPENDENT-PRODUCTS.md) | Companion products are optional and independently deployable | Accepted |
| [ADR-0013](ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md) | Executable diagnostic tools are allowlisted | Accepted |

## Lifecycle

```text
Proposed → Accepted → Superseded
             ↘ Rejected
```

Accepted ADRs are not edited to hide previous reasoning. A later decision supersedes them explicitly.

## Verification

An ADR is considered implemented only when its implementation checklist is complete. It is considered verified only when named unit, contract, schema, process, real-GF or end-to-end tests reproduce the declared behavior.

## Ownership rule

ADRs decide architecture. Detailed contracts remain in their owning documents, including dependency rules, process execution, GF integration, validation, reporting and project-specific contracts.
