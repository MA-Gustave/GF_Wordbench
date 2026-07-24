# ADR-0008 — Hexagonal Modular Monolith

**ADR ID:** `ADR-0008`  
**Status:** Accepted  
**Decision scope:** GF Wordbench framework architecture, module ownership, dependency boundaries, ports, adapters, entrypoints, and bootstrap composition  
**Decision owner:** GF Wordbench maintainers  
**Decision date:** `2026-07-23`  
**Last reviewed:** `2026-07-24`  
**Target path:** `docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md`

---

## 1. Context

GF Wordbench has several stable responsibilities: active-project configuration, validation orchestration, GF execution, diagnostics, result construction, reporting, artifact persistence, and release verification.

These responsibilities require explicit ownership and testable boundaries, but they do not require independently deployed services. GF Wordbench is a local product operating on one active GF language project per workspace. Distributed coordination, service discovery, network contracts, and independently scaled components would add failure modes without solving a demonstrated product requirement.

Multi-workspace inventory, aggregation, comparison, and portfolio views belong to the separate `gf-portfolio` product. They are not a sixth Wordbench module.

---

## 2. Decision

GF Wordbench is implemented as a **single deployable modular monolith with hexagonal boundaries**.

Its architecture has two complementary dimensions:

1. five functional modules that own product responsibilities;
2. six architectural rings that control dependency direction and external interaction.

### 2.1 Functional modules

| Module | Primary responsibility |
|---|---|
| `projects` | Active-project identity, configuration, path resolution, loading, and project lifecycle |
| `runs` | Run orchestration, execution budgets, continuation policy, finalization, and run history |
| `validation` | File selection, static scanning, GF compilation, PGF construction, scenarios, gold comparison, regression comparison, and release gates |
| `diagnostics` | Diagnostic normalization, findings, causal classification, pattern interpretation, and diagnostic audits |
| `reporting` | Persisted schemas, report rendering, manifests, artifact publication, and public exports |

The modules are cohesive ownership boundaries. They are not separate services, packages requiring network communication, or independently deployed products.

GF Wordbench has no `languages` module for discovering or aggregating multiple workspaces. Language-specific facts remain under the active `project/` boundary. Cross-workspace aggregation belongs to `gf-portfolio`.

### 2.2 Hexagonal rings

The rings are listed from the stable core to the composition edge:

```text
domain
→ application
→ ports
→ adapters
→ entrypoints
→ bootstrap
```

- **domain** owns stable models, statuses, invariants, result semantics, continuation rules, and release rules;
- **application** owns use cases and coordination between domain capabilities;
- **ports** define narrow contracts for external systems or genuinely unstable boundaries;
- **adapters** implement ports for GF, processes, filesystems, TOML, JSON, persistence, clocks, and other external mechanisms;
- **entrypoints** expose CLI, GUI, and automation surfaces without duplicating domain or application policy;
- **bootstrap** is the composition root that selects concrete adapters and assembles the application.

Functional modules and architectural rings are orthogonal. A functional module may contain domain, application, port, and adapter elements when its responsibility requires them. The architecture does not require one package per cell of the module-by-ring matrix.

---

## 3. Boundary rules

1. Public intermodule APIs remain narrow, typed, and owned by the providing module.
2. A consumer must not import another module's private implementation details.
3. Domain code must not depend on adapters, entrypoints, bootstrap, GUI frameworks, process libraries, or filesystem implementations.
4. Application use cases access GF, processes, filesystems, persistence, clocks, and similar external mechanisms through explicit ports.
5. Ports are introduced only for external or unstable boundaries. Internal helpers do not receive interfaces solely for architectural symmetry.
6. Adapters translate between external representations and canonical Wordbench models. They must not redefine domain status, validation, or release semantics.
7. CLI, GUI, and automation entrypoints invoke the same application use cases and must not maintain competing orchestration rules.
8. Bootstrap owns dependency construction and concrete implementation selection. Business behavior must not depend on bootstrap side effects.
9. Report writers consume completed structured results and preserved evidence. They do not execute validation stages or reconstruct missing evidence.
10. GF interaction remains behind the dedicated anti-corruption boundary defined by ADR-0009.
11. GF Wordbench must operate without importing, starting, or accessing private state from `gf-portfolio`, SemantiK Architect, or Kristal.
12. The complete Wordbench application remains buildable, testable, and deployable as one product.

---

## 4. Consequences

### 4.1 Benefits

- Responsibilities have explicit owners without distributed-system overhead.
- The core remains testable with fake or controlled adapters.
- External mechanisms can change without leaking their representations into domain rules.
- CLI, GUI, and automation can share one application behavior.
- Deployment, local development, debugging, and evidence collection remain straightforward.
- Module boundaries can be enforced by import tests and contract tests.

### 4.2 Constraints

- Cross-module changes must update the provider, consumers, contracts, tests, and owner documentation together.
- Bootstrap must remain the only general composition root.
- Adapters must not become alternate owners of domain rules.
- Shared models must have a clear owner rather than becoming an unrestricted common namespace.
- A new module requires a stable product responsibility that cannot remain cohesive within an existing module.
- A new port requires a real external or unstable boundary, not merely a desire to wrap a helper.

---

## 5. Alternatives rejected

### 5.1 Microservices

Independent services would introduce deployment coordination, network failures, service discovery, distributed observability, versioned remote APIs, and data-consistency problems without a demonstrated scaling or isolation requirement.

### 5.2 CQRS and Event Sourcing

GF Wordbench does not require separate read and write models or an event log as the primary source of truth. Structured run results, manifests, and preserved evidence already provide the required auditability.

### 5.3 Generic event bus or plugin architecture

Implicit dispatch and unrestricted runtime extension would weaken ownership, dependency visibility, deterministic execution, and security. Explicit orchestration and small registries are preferred.

### 5.4 Interface for every helper

An interface-per-class approach would create indirection without protecting a meaningful boundary. Ports are reserved for external or unstable dependencies.

### 5.5 Layer-only architecture without functional modules

Technical layers alone do not establish ownership for project, run, validation, diagnostic, and reporting responsibilities. Functional modules are required in addition to hexagonal rings.

---

## 6. Verification criteria

The decision is satisfied when reproducible architecture and contract tests demonstrate that:

- domain and application code do not import forbidden outer-ring implementations;
- external process, GF, filesystem, persistence, and clock access occurs through approved ports and adapters;
- CLI, GUI, and automation invoke shared application use cases;
- intermodule consumers use public contracts rather than private implementations;
- report writers remain passive consumers of completed results and evidence;
- bootstrap is the composition root;
- the five functional module responsibilities are not duplicated;
- no Wordbench module implements cross-workspace portfolio ownership or imports `gf-portfolio`;
- the application builds and operates as one independently deployable product;
- architecture owner documents and specialized contract locks preserve the same boundaries.

---

## 7. Related decisions and owner documents

### Related ADRs

- `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`
- `ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md`
- `ADR-0010-RUN-BUDGET-AND-FINALIZATION.md`
- `ADR-0011-SEPARATE-PORTFOLIO.md`
- `ADR-0012-INDEPENDENT-PRODUCTS.md`
- `ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`

### Owner documents

- `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/COMPONENT_MAP.md`
- `docs/architecture/DEPENDENCY_RULES.md`
- `docs/architecture/PRODUCT_BOUNDARIES.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
