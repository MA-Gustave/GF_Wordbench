# GF Wordbench — Documentation Map

**Document ID:** `GF-WB-DOCUMENTATION-MAP`  
**Status:** Normative navigation index  
**Applies to:** Framework documentation, active-project documentation, project templates and documentation governance  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Update rule:** Update this map whenever a permanent document is added, removed, renamed or changes authority.

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---

## 2026-08-05 — ADR-0015 source/profile terminology alignment

Corrected user, validation, GF-toolchain, release, development and reference documentation so that:

- Wordbench opens selected GF/RGL sources in place;
- `ResolvedLanguageContext` owns source and identity facts;
- `ValidationProfile` is explicit, optional and policy-only;
- `project/project.toml` and root `project/` are legacy compatibility inputs, not startup requirements;
- `templates/validation-profile/` is the reusable policy template;
- run outputs are separated from selected source trees.

Historical migration examples retain legacy paths only when explicitly labeled as legacy.

## 1. Purpose

This file is the canonical map of the GF Wordbench documentation system.

It defines:

- where each topic is documented;
- which document is authoritative for a rule;
- which reading path applies to each audience;
- how framework documentation is separated from active-language documentation;
- how project templates mirror the active-project structure;
- how documentation changes avoid duplication and drift.

This map does not replace the documents it indexes.

---

## 2. Documentation authority

When two documents appear to overlap, use the following precedence.

1. Accepted architectural decision records.
2. [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](DOCUMENTATION_ALIGNMENT_LOCK.md) for cross-document interpretation.
3. Specialized contract locks for framework, external-tool, persisted-schema, active-project and template boundaries.
4. The document that owns the specific topic, schema, command surface or procedure.
5. Overview, tutorial, quick-start, example and historical documents.

A lower-authority document must link to the authoritative source instead of redefining it. The correction ledger coordinates work but does not create normative product behavior.

### 2.1 Documentation governance and contract locks

| Document | Role |
|---|---|
| [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](DOCUMENTATION_ALIGNMENT_LOCK.md) | Cross-document product identity, authority order, ownership boundaries and correction rules. |
| [`docs/DOCUMENTATION_CORRECTION_LEDGER.md`](DOCUMENTATION_CORRECTION_LEDGER.md) | Coordination record for parallel documentation corrections and integration review. |
| [`docs/INTERFILE_CONTRACT_LOCK.md`](INTERFILE_CONTRACT_LOCK.md) | Python and framework file-boundary contracts. |
| [`docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`](EXTERNAL_TOOL_CONTRACT_LOCK.md) | GF, process, filesystem, environment and platform contracts. |
| [`docs/PERSISTED_SCHEMA_LOCK.md`](PERSISTED_SCHEMA_LOCK.md) | Persisted formats, schema versions, paths and migrations. |
| Explicit validation profile | Owns profile-local checkpoints, scenarios, golds, artifacts and release policy when loaded. |
| [`templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md`](../templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md) | Reusable profile-local contract structure. |

---

## 3. Reading paths

### 3.1 New user

1. [`README.md`](../README.md)
1. [`docs/00_START_HERE.md`](00_START_HERE.md)
1. [`docs/PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md)
1. [`docs/usage/INSTALLATION.md`](usage/INSTALLATION.md)
1. [`docs/usage/QUICK_START.md`](usage/QUICK_START.md)
1. [`docs/validation/VALIDATION_MODES.md`](validation/VALIDATION_MODES.md)

### 3.2 Language-project maintainer

1. Select the language directory or `.gf` file in its existing RGL/GF source tree.
1. Read [`docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`](decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md).
1. Read [`docs/usage/QUICK_START.md`](usage/QUICK_START.md).
1. When advanced policy is required, start from [`templates/validation-profile/README.md`](../templates/validation-profile/README.md).
1. Maintain profile-local scenarios, golds and release criteria outside the selected source tree.

### 3.3 Framework contributor

1. [`CONTRIBUTING.md`](../CONTRIBUTING.md)
1. [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](architecture/ARCHITECTURE_OVERVIEW.md)
1. [`docs/architecture/COMPONENT_MAP.md`](architecture/COMPONENT_MAP.md)
1. [`docs/architecture/DEPENDENCY_RULES.md`](architecture/DEPENDENCY_RULES.md)
1. [`docs/INTERFILE_CONTRACT_LOCK.md`](INTERFILE_CONTRACT_LOCK.md)
1. [`docs/development/CODEBASE_GUIDE.md`](development/CODEBASE_GUIDE.md)
1. [`docs/development/TESTING_GF_WORDBENCH.md`](development/TESTING_GF_WORDBENCH.md)

### 3.4 Release maintainer

1. [`docs/release/VERSIONING_POLICY.md`](release/VERSIONING_POLICY.md)
1. [`docs/release/RELEASE_PROCESS.md`](release/RELEASE_PROCESS.md)
1. [`docs/validation/RELEASE_GATES.md`](validation/RELEASE_GATES.md)
1. [`docs/PERSISTED_SCHEMA_LOCK.md`](PERSISTED_SCHEMA_LOCK.md)
1. Release criteria from the explicitly loaded validation profile, when release mode is used
1. [`CHANGELOG.md`](../CHANGELOG.md)

### 3.5 Diagnostics investigator

1. [`docs/diagnostics/DIAGNOSTIC_OVERVIEW.md`](diagnostics/DIAGNOSTIC_OVERVIEW.md)
1. [`docs/diagnostics/ERROR_CLASSIFICATION.md`](diagnostics/ERROR_CLASSIFICATION.md)
1. [`docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md`](diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md)
1. [`docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`](diagnostics/GF_DIAGNOSTIC_PARSING.md)
1. [`docs/diagnostics/TOOL_CATALOG.md`](diagnostics/TOOL_CATALOG.md)
1. [`docs/reports/RAW_LOGS_REFERENCE.md`](reports/RAW_LOGS_REFERENCE.md)
1. [`docs/reports/AI_READY_REFERENCE.md`](reports/AI_READY_REFERENCE.md)

### 3.6 Documentation maintainer

1. [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](DOCUMENTATION_ALIGNMENT_LOCK.md)
1. [`docs/DOCUMENTATION_MAP.md`](DOCUMENTATION_MAP.md)
1. [`docs/DOCUMENTATION_CORRECTION_LEDGER.md`](DOCUMENTATION_CORRECTION_LEDGER.md)
1. [`docs/decisions/README.md`](decisions/README.md)
1. [`docs/REPOSITORY_STRUCTURE.md`](REPOSITORY_STRUCTURE.md)

---

## 4. Canonical topic ownership

| Topic | Authoritative document |
|---|---|
| Product purpose and audience | [`docs/PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md) |
| Product and `gf-portfolio` boundaries | [`docs/architecture/PRODUCT_BOUNDARIES.md`](architecture/PRODUCT_BOUNDARIES.md) |
| Scope and non-goals | [`docs/SCOPE_AND_NON_GOALS.md`](SCOPE_AND_NON_GOALS.md) |
| Cross-document interpretation | [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](DOCUMENTATION_ALIGNMENT_LOCK.md) |
| Parallel correction coordination | [`docs/DOCUMENTATION_CORRECTION_LEDGER.md`](DOCUMENTATION_CORRECTION_LEDGER.md) |
| Terminology | [`docs/GLOSSARY.md`](GLOSSARY.md) |
| Repository layout | [`docs/REPOSITORY_STRUCTURE.md`](REPOSITORY_STRUCTURE.md) |
| System architecture | [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](architecture/ARCHITECTURE_OVERVIEW.md) |
| Component ownership | [`docs/architecture/COMPONENT_MAP.md`](architecture/COMPONENT_MAP.md) |
| Dependency direction | [`docs/architecture/DEPENDENCY_RULES.md`](architecture/DEPENDENCY_RULES.md) |
| Framework interfile contracts | [`docs/INTERFILE_CONTRACT_LOCK.md`](INTERFILE_CONTRACT_LOCK.md) |
| External-tool contracts | [`docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`](EXTERNAL_TOOL_CONTRACT_LOCK.md) |
| Persisted schema contracts | [`docs/PERSISTED_SCHEMA_LOCK.md`](PERSISTED_SCHEMA_LOCK.md) |
| GF executable and RGL paths | [`docs/gf/GF_PATH_RESOLUTION.md`](gf/GF_PATH_RESOLUTION.md) |
| GF command construction | [`docs/gf/GF_COMMAND_CONSTRUCTION.md`](gf/GF_COMMAND_CONSTRUCTION.md) |
| Compilation | [`docs/gf/GF_COMPILATION.md`](gf/GF_COMPILATION.md) |
| PGF construction | [`docs/gf/GF_PGF_BUILD.md`](gf/GF_PGF_BUILD.md) |
| Validation modes | [`docs/validation/VALIDATION_MODES.md`](validation/VALIDATION_MODES.md) |
| Scenario format | [`docs/scenarios/SCENARIO_FORMAT.md`](scenarios/SCENARIO_FORMAT.md) |
| Gold updates | [`docs/scenarios/UPDATING_GOLD_FILES.md`](scenarios/UPDATING_GOLD_FILES.md) |
| Status values | [`docs/reference/STATUS_VALUES.md`](reference/STATUS_VALUES.md) |
| Diagnostic kinds | [`docs/reference/DIAGNOSTIC_KINDS.md`](reference/DIAGNOSTIC_KINDS.md) |
| Diagnostic tool registry | [`docs/diagnostics/TOOL_CATALOG.md`](diagnostics/TOOL_CATALOG.md) |
| Run-summary schema | [`docs/reports/SUMMARY_JSON_REFERENCE.md`](reports/SUMMARY_JSON_REFERENCE.md) |
| Project configuration | [`docs/configuration/PROJECT_TOML_REFERENCE.md`](configuration/PROJECT_TOML_REFERENCE.md) |
| CLI | [`docs/usage/CLI_REFERENCE.md`](usage/CLI_REFERENCE.md) |
| GUI | [`docs/usage/GUI_REFERENCE.md`](usage/GUI_REFERENCE.md) |
| Resolved language identity | `ResolvedLanguageContext` built from the selected source |
| Language architecture | selected source repository documentation or explicit profile reference |
| Profile-local validation contracts | explicit `ValidationProfile` |
| Release criteria | explicit validation profile |

---

## 5. Complete documentation inventory

The inventory below defines the permanent target documentation set.

### 5.1 Repository root

| Path | Responsibility |
|---|---|
| [`README.md`](../README.md) | Primary repository entry point, product summary, quick start and navigation. |
| [`CHANGELOG.md`](../CHANGELOG.md) | Release-by-release record of user-visible and contract-relevant changes. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution workflow, review expectations and required validation. |
| [`SECURITY.md`](../SECURITY.md) | Security policy, trust boundaries and vulnerability reporting. |
| [`LICENSE.md`](../LICENSE.md) | License terms for GF Wordbench. |

### 5.2 Core documentation

| Path | Responsibility |
|---|---|
| [`docs/00_ERRATUM.md`](00_ERRATUM.md) | Controlled reconciliation record for legacy contradictions; it cannot override current owner documents. |
| [`docs/00_START_HERE.md`](00_START_HERE.md) | First documentation entry point and recommended reading order. |
| [`docs/PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md) | Product purpose, capabilities, users and value. |
| [`docs/SCOPE_AND_NON_GOALS.md`](SCOPE_AND_NON_GOALS.md) | Authoritative scope boundaries and explicit non-goals. |
| [`docs/GLOSSARY.md`](GLOSSARY.md) | Canonical terminology used across framework and project documentation. |
| [`docs/REPOSITORY_STRUCTURE.md`](REPOSITORY_STRUCTURE.md) | Repository directories, ownership and permitted contents. |
| [`docs/DOCUMENTATION_MAP.md`](DOCUMENTATION_MAP.md) | Canonical map of the documentation system. |

### 5.3 Architecture

| Path | Responsibility |
|---|---|
| [`docs/architecture/ARCHITECTURE_OVERVIEW.md`](architecture/ARCHITECTURE_OVERVIEW.md) | System layers, responsibilities and architectural principles. |
| [`docs/architecture/PRODUCT_BOUNDARIES.md`](architecture/PRODUCT_BOUNDARIES.md) | Product boundary, independent-product rules and public interoperability with `gf-portfolio`. |
| [`docs/architecture/IMPLEMENTATION_ALIGNMENT.md`](architecture/IMPLEMENTATION_ALIGNMENT.md) | Traceability from accepted architecture to code ownership, interfaces, tests and evidence. |
| [`docs/architecture/COMPONENT_MAP.md`](architecture/COMPONENT_MAP.md) | Component inventory, owners, inputs, outputs and dependencies. |
| [`docs/architecture/EXECUTION_FLOW.md`](architecture/EXECUTION_FLOW.md) | End-to-end control flow for all validation modes. |
| [`docs/architecture/DATA_MODEL.md`](architecture/DATA_MODEL.md) | In-memory models, field semantics and lifecycle. |
| [`docs/architecture/ARTIFACT_MODEL.md`](architecture/ARTIFACT_MODEL.md) | Generated artifact ownership, lifecycle and relationships. |
| [`docs/architecture/PROCESS_EXECUTION_MODEL.md`](architecture/PROCESS_EXECUTION_MODEL.md) | Process launch, capture, timeout, cancellation and termination. |
| [`docs/architecture/ERROR_HANDLING_MODEL.md`](architecture/ERROR_HANDLING_MODEL.md) | Exceptions, structured failures, containment and propagation. |
| [`docs/architecture/EXTENSION_BOUNDARIES.md`](architecture/EXTENSION_BOUNDARIES.md) | Supported extension points and forbidden bypasses. |
| [`docs/architecture/DEPENDENCY_RULES.md`](architecture/DEPENDENCY_RULES.md) | Allowed and forbidden dependency directions. |

### 5.4 Documentation governance and contract locks

| Path | Responsibility |
|---|---|
| [`docs/DOCUMENTATION_ALIGNMENT_LOCK.md`](DOCUMENTATION_ALIGNMENT_LOCK.md) | Normative cross-document alignment and interpretation contract. |
| [`docs/DOCUMENTATION_CORRECTION_LEDGER.md`](DOCUMENTATION_CORRECTION_LEDGER.md) | Coordination ledger for parallel corrections and integration review. |
| [`docs/INTERFILE_CONTRACT_LOCK.md`](INTERFILE_CONTRACT_LOCK.md) | Normative Python/framework interfile contracts. |
| [`docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`](EXTERNAL_TOOL_CONTRACT_LOCK.md) | Normative GF, process, filesystem and platform contracts. |
| [`docs/PERSISTED_SCHEMA_LOCK.md`](PERSISTED_SCHEMA_LOCK.md) | Normative persisted schemas, versions and migrations. |

### 5.5 GF integration

| Path | Responsibility |
|---|---|
| [`docs/gf/GF_TOOLCHAIN_INTEGRATION.md`](gf/GF_TOOLCHAIN_INTEGRATION.md) | Complete boundary between GF Wordbench and GF. |
| [`docs/gf/GF_PATH_RESOLUTION.md`](gf/GF_PATH_RESOLUTION.md) | GF executable, RGL and search-path resolution rules. |
| [`docs/gf/GF_COMMAND_CONSTRUCTION.md`](gf/GF_COMMAND_CONSTRUCTION.md) | Structured GF argument construction, working directory and invocation rules. |
| [`docs/gf/GF_COMPILATION.md`](gf/GF_COMPILATION.md) | Module compilation commands, evidence and success criteria. |
| [`docs/gf/GF_PGF_BUILD.md`](gf/GF_PGF_BUILD.md) | Final PGF build, artifact verification and release behavior. |
| [`docs/gf/GF_SCRIPT_EXECUTION.md`](gf/GF_SCRIPT_EXECUTION.md) | Native GF shell and `.gfs` scenario execution. |
| [`docs/gf/GF_OUTPUT_NORMALIZATION.md`](gf/GF_OUTPUT_NORMALIZATION.md) | Normalization policy for GF-generated output. |
| [`docs/gf/GF_VERSION_COMPATIBILITY.md`](gf/GF_VERSION_COMPATIBILITY.md) | Supported GF versions, capability checks and incompatibilities. |

### 5.6 Validation

| Path | Responsibility |
|---|---|
| [`docs/validation/VALIDATION_OVERVIEW.md`](validation/VALIDATION_OVERVIEW.md) | Validation concepts, stage boundaries and evidence model. |
| [`docs/validation/VALIDATION_PIPELINE.md`](validation/VALIDATION_PIPELINE.md) | Canonical stage order and orchestration behavior. |
| [`docs/validation/VALIDATION_MODES.md`](validation/VALIDATION_MODES.md) | Quick, checkpoint, release and diagnostic mode contracts. |
| [`docs/validation/FILE_SELECTION.md`](validation/FILE_SELECTION.md) | Selection, inclusion, exclusion and target resolution. |
| [`docs/validation/STATIC_SCANNING.md`](validation/STATIC_SCANNING.md) | Static GF source checks and their limitations. |
| [`docs/validation/COMPILATION_VALIDATION.md`](validation/COMPILATION_VALIDATION.md) | Compilation result interpretation and artifact checks. |
| [`docs/validation/SCENARIO_VALIDATION.md`](validation/SCENARIO_VALIDATION.md) | Scenario registry, execution, assertions and outcomes. |
| [`docs/validation/REGRESSION_COMPARISON.md`](validation/REGRESSION_COMPARISON.md) | Previous-run selection and change classification. |
| [`docs/validation/RELEASE_GATES.md`](validation/RELEASE_GATES.md) | Mandatory conditions for release readiness. |

### 5.7 Scenarios and gold

| Path | Responsibility |
|---|---|
| [`docs/scenarios/SCENARIO_FORMAT.md`](scenarios/SCENARIO_FORMAT.md) | Canonical `.gfs` scenario structure and metadata. |
| [`docs/scenarios/WRITING_GFS_SCENARIOS.md`](scenarios/WRITING_GFS_SCENARIOS.md) | Authoring guidance for bounded native GF scenarios. |
| [`docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md`](scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md) | Stable markers, sections and assertion semantics. |
| [`docs/scenarios/OUTPUT_NORMALIZATION.md`](scenarios/OUTPUT_NORMALIZATION.md) | Scenario-facing normalization profiles and rules. |
| [`docs/scenarios/GOLDEN_TESTS.md`](scenarios/GOLDEN_TESTS.md) | Gold comparison semantics and review policy. |
| [`docs/scenarios/UPDATING_GOLD_FILES.md`](scenarios/UPDATING_GOLD_FILES.md) | Explicit, reviewed gold update workflow. |

### 5.8 Diagnostics

| Path | Responsibility |
|---|---|
| [`docs/diagnostics/DIAGNOSTIC_OVERVIEW.md`](diagnostics/DIAGNOSTIC_OVERVIEW.md) | Diagnostic pipeline and evidence hierarchy. |
| [`docs/diagnostics/ERROR_CLASSIFICATION.md`](diagnostics/ERROR_CLASSIFICATION.md) | Status, error kind and diagnostic-class semantics. |
| [`docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md`](diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md) | Causal ownership and blocker relationships. |
| [`docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`](diagnostics/GF_DIAGNOSTIC_PARSING.md) | Parsing GF stdout and stderr without losing evidence. |
| [`docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md`](diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md) | Versioned registry of recognized GF diagnostic patterns. |
| [`docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`](diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md) | Launch, timeout, cancellation and process failure handling. |
| [`docs/diagnostics/TOOL_CATALOG.md`](diagnostics/TOOL_CATALOG.md) | Allowlisted diagnostic tools, prerequisites, budgets, evidence and result contracts. |

### 5.9 Reports

| Path | Responsibility |
|---|---|
| [`docs/reports/REPORTING_OVERVIEW.md`](reports/REPORTING_OVERVIEW.md) | Report set, ownership and derivation rules. |
| [`docs/reports/SUMMARY_JSON_REFERENCE.md`](reports/SUMMARY_JSON_REFERENCE.md) | Human-readable reference for canonical `summary.json`. |
| [`docs/reports/SUMMARY_MARKDOWN_REFERENCE.md`](reports/SUMMARY_MARKDOWN_REFERENCE.md) | Required structure of `summary.md`. |
| [`docs/reports/AI_READY_REFERENCE.md`](reports/AI_READY_REFERENCE.md) | Required structure and evidence rules for `AI_READY.md`. |
| [`docs/reports/RAW_LOGS_REFERENCE.md`](reports/RAW_LOGS_REFERENCE.md) | Raw and aggregate log locations and semantics. |
| [`docs/reports/ARTIFACT_MANIFEST.md`](reports/ARTIFACT_MANIFEST.md) | Manifest roles, hashes and verification behavior. |

### 5.10 Configuration

| Path | Responsibility |
|---|---|
| [`docs/configuration/CONFIGURATION_OVERVIEW.md`](configuration/CONFIGURATION_OVERVIEW.md) | Configuration layers, precedence and ownership. |
| [`docs/configuration/PROJECT_TOML_REFERENCE.md`](configuration/PROJECT_TOML_REFERENCE.md) | Legacy profile format and compatibility reference; not startup authority. |
| [`docs/configuration/APPLICATION_STATE_REFERENCE.md`](configuration/APPLICATION_STATE_REFERENCE.md) | Disposable local UI/application state reference. |
| [`docs/configuration/ENVIRONMENT_AND_PATHS.md`](configuration/ENVIRONMENT_AND_PATHS.md) | Executable, RGL, output and environment-path behavior. |

### 5.11 Usage

| Path | Responsibility |
|---|---|
| [`docs/usage/INSTALLATION.md`](usage/INSTALLATION.md) | Supported installation methods and prerequisites. |
| [`docs/usage/QUICK_START.md`](usage/QUICK_START.md) | Shortest reliable path to a first successful run. |
| [`docs/usage/CLI_REFERENCE.md`](usage/CLI_REFERENCE.md) | Canonical CLI commands, arguments, defaults and exit behavior. |
| [`docs/usage/GUI_REFERENCE.md`](usage/GUI_REFERENCE.md) | GUI workflows and parity with the CLI. |

### 5.12 Project lifecycle

| Path | Responsibility |
|---|---|
| [`docs/projects/PROJECT_MODEL.md`](projects/PROJECT_MODEL.md) | Single-active-language project model. |
| [`docs/projects/CREATING_A_PROJECT.md`](projects/CREATING_A_PROJECT.md) | Create a project from the canonical template. |
| [`docs/projects/CLONING_AND_RESETTING.md`](projects/CLONING_AND_RESETTING.md) | Duplicate or reset a GF Wordbench project safely. |
| [`docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md`](projects/MIGRATING_AN_EXISTING_LANGUAGE.md) | Migrate an existing GF language audit into the project model. |
| [`docs/projects/PROJECT_COMPLETION_CHECKLIST.md`](projects/PROJECT_COMPLETION_CHECKLIST.md) | Definition of a complete project integration. |

### 5.13 Development

| Path | Responsibility |
|---|---|
| [`docs/development/DEVELOPMENT_SETUP.md`](development/DEVELOPMENT_SETUP.md) | Developer environment and local toolchain setup. |
| [`docs/development/CODEBASE_GUIDE.md`](development/CODEBASE_GUIDE.md) | Implementation-oriented walkthrough of the codebase. |
| [`docs/development/CODING_STANDARDS.md`](development/CODING_STANDARDS.md) | Python, tests, paths, typing and documentation standards. |
| [`docs/development/TESTING_GF_WORDBENCH.md`](development/TESTING_GF_WORDBENCH.md) | Unit, contract, integration and real-GF test strategy. |
| [`docs/development/EXTENDING_GF_WORDBENCH.md`](development/EXTENDING_GF_WORDBENCH.md) | Adding stages, diagnostics, reports and integrations. |
| [`docs/development/BACKWARD_COMPATIBILITY.md`](development/BACKWARD_COMPATIBILITY.md) | Compatibility guarantees and migration obligations. |
| [`docs/development/DEBUGGING_THE_FRAMEWORK.md`](development/DEBUGGING_THE_FRAMEWORK.md) | Framework-level debugging and evidence collection. |

### 5.14 Operations

| Path | Responsibility |
|---|---|
| [`docs/operations/RUN_DIRECTORY_LIFECYCLE.md`](operations/RUN_DIRECTORY_LIFECYCLE.md) | Creation, finalization, verification and immutability of runs. |
| [`docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md`](operations/CLEANUP_BACKUP_AND_RECOVERY.md) | Retention, cleanup, backup and recovery procedures. |
| [`docs/operations/WINDOWS_LAUNCHERS.md`](operations/WINDOWS_LAUNCHERS.md) | Windows launchers and platform-specific behavior. |
| [`docs/operations/AUTOMATION_AND_CI.md`](operations/AUTOMATION_AND_CI.md) | Headless operation, CI gates and artifact publishing. |

### 5.15 Release

| Path | Responsibility |
|---|---|
| [`docs/release/VERSIONING_POLICY.md`](release/VERSIONING_POLICY.md) | Application, schema, contract and project versioning. |
| [`docs/release/RELEASE_PROCESS.md`](release/RELEASE_PROCESS.md) | Framework release procedure and evidence requirements. |
| [`docs/release/MIGRATION_AND_DEPRECATION.md`](release/MIGRATION_AND_DEPRECATION.md) | Migration windows, aliases and deprecation lifecycle. |

### 5.16 Architectural decisions

| Path | Responsibility |
|---|---|
| [`docs/decisions/README.md`](decisions/README.md) | ADR conventions, status values and index. |
| [`docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`](decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md) | Decision to resolve one selected GF language context per Wordbench workspace and run. |
| [`docs/decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md`](decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md) | Decision to keep GF authoritative for GF semantics. |
| [`docs/decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md`](decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md) | Decision to separate static scanning from native compilation. |
| [`docs/decisions/ADR-0004-NATIVE-GFS-SCENARIOS.md`](decisions/ADR-0004-NATIVE-GFS-SCENARIOS.md) | Decision to use native GF shell scenarios. |
| [`docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md`](decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md) | Decision to model file and scenario outcomes separately. |
| [`docs/decisions/ADR-0006-AI-READY-REPORT.md`](decisions/ADR-0006-AI-READY-REPORT.md) | Decision to generate a bounded AI-ready evidence packet. |
| [`docs/decisions/ADR-0007-GOLDEN-OUTPUT-TESTING.md`](decisions/ADR-0007-GOLDEN-OUTPUT-TESTING.md) | Decision to use reviewed normalized golden outputs. |
| [`docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md`](decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md) | Decision to use a hexagonal modular-monolith architecture. |
| [`docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md`](decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md) | Decision to isolate GF through an anti-corruption boundary. |
| [`docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md`](decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md) | Decision to enforce run budgets and controlled finalization. |
| [`docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md`](decisions/ADR-0011-SEPARATE-PORTFOLIO.md) | Decision to move multi-workspace aggregation to the separate `gf-portfolio` product. |
| [`docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md`](decisions/ADR-0012-INDEPENDENT-PRODUCTS.md) | Decision that Wordbench and `gf-portfolio` remain independently operable products. |
| [`docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`](decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md) | Decision to use an explicit allowlisted diagnostic-tool registry. |

### 5.17 Reference

| Path | Responsibility |
|---|---|
| [`docs/reference/TERMINOLOGY_REFERENCE.md`](reference/TERMINOLOGY_REFERENCE.md) | Compact canonical term reference. |
| [`docs/reference/EXIT_CODES.md`](reference/EXIT_CODES.md) | CLI and process exit-code reference. |
| [`docs/reference/FILE_NAMING_CONVENTIONS.md`](reference/FILE_NAMING_CONVENTIONS.md) | Repository, artifact, scenario and module naming rules. |
| [`docs/reference/STATUS_VALUES.md`](reference/STATUS_VALUES.md) | Canonical validation and execution-state values. |
| [`docs/reference/DIAGNOSTIC_KINDS.md`](reference/DIAGNOSTIC_KINDS.md) | Canonical error kinds and diagnostic classes. |
| [`docs/reference/SCHEMA_INDEX.md`](reference/SCHEMA_INDEX.md) | Index of all persisted schema identities and versions. |
| [`docs/reference/COMMAND_REFERENCE.md`](reference/COMMAND_REFERENCE.md) | Compact GF Wordbench and native GF command reference. |

### 5.18 Active language project

The selected language is not stored under a canonical repository-local `project/` directory.

Current authorities:

| Subject | Authority |
|---|---|
| Selected path, source root, RGL root, language identity and discovered entrypoints | `ResolvedLanguageContext` |
| GF executable and environment facts | environment/tool configuration |
| Checkpoints, scenarios, inputs, golds, PGF targets, artifact requirements and release gates | explicitly loaded `ValidationProfile` |
| Run logs, reports and artifacts | configured output root |

Legacy `project/` paths belong only to compatibility and migration documentation.

### 5.19 Project template

The reusable optional policy template is:

```text
templates/validation-profile/
```

It contains profile-local documentation, scenarios, inputs, golds and release policy. It must not contain selected-language identity, source paths, GF executable paths, output roots or run state.

## 6. Framework, project and template separation

### 6.1 Framework documentation

Framework documentation under `docs/` describes reusable GF Wordbench behavior.

It must not depend on the identity of the active language except in explicitly marked examples, migration fixtures or historical compatibility notes. Multi-workspace aggregation belongs to the independent `gf-portfolio` product; Wordbench documentation may define only its public export and interoperability boundary.

### 6.2 Active-project documentation

Language-specific documentation may remain with the language source repository or be referenced by an explicit validation profile.

Wordbench does not require a root `project/docs/` tree. Profile-local documents may describe non-derivable validation policy, known limitations, scenario coverage and release criteria, but they must not redefine resolved source facts.

### 6.3 Template documentation

Documentation under `templates/validation-profile/` defines the reusable shape of optional validation policy.

It must retain generic placeholders, remain source-location neutral and avoid machine-local paths. It is not a template for copying the selected RGL language tree.

## 7. Duplication rules

Documentation must follow a single-source-of-truth rule.

### 7.1 Required behavior

- Define a rule once in its authoritative document.
- Link to the authoritative rule from overview and usage documents.
- Keep examples subordinate to the normative rule.
- Keep enumerations synchronized with their reference owner.
- Keep project-specific facts out of framework specifications.
- Keep implementation details out of user procedures unless required to operate the system.
- State accepted contracts directly instead of attaching progress labels to every material assertion.
- Use code, tests and reproducible run artifacts when executable behavior must be verified; an accepted ADR establishes a decision, not execution evidence.

### 7.2 Prohibited behavior

- Reproducing full schema definitions outside the schema lock and schema reference.
- Maintaining competing command lists in multiple documents.
- Defining status semantics in report, GUI and diagnostic documents independently.
- Copying active-language module names into framework architecture.
- Treating a README as a substitute for a normative contract.
- Maintaining a cross-document taxonomy of per-claim implementation progress labels.
- Introducing Wordbench dependencies on `gf-portfolio` or Portfolio-owned registry concepts.
- Leaving renamed paths in navigation indexes.

---

## 8. Document status model

Permanent documents may declare one of the following statuses:

```text
Normative
Reference
Operational
Guidance
Decision
Template
Historical
```

| Status | Meaning |
|---|---|
| `Normative` | Defines required behavior or a locked contract. |
| `Reference` | Canonical lookup for fields, values or commands. |
| `Operational` | Defines an executable procedure. |
| `Guidance` | Explains recommended practice without redefining contracts. |
| `Decision` | Records an accepted architectural choice and its consequences. |
| `Template` | Reusable structure requiring project-specific completion. |
| `Historical` | Retained for migration or audit history; not current authority. |

---

## 9. Documentation change workflow

A documentation change is complete only when the following applicable checks pass:

```text
[ ] Authoritative owner identified
[ ] Duplicate definitions removed
[ ] Incoming links updated
[ ] Outgoing links validated
[ ] DOCUMENTATION_MAP.md updated
[ ] DOCUMENTATION_CORRECTION_LEDGER.md updated for coordinated correction work
[ ] README navigation reviewed
[ ] Alignment and specialized locks updated when authority or behavior changed
[ ] ADR added or updated when architecture changed
[ ] Project and template structures synchronized
[ ] Examples match current schemas and commands
[ ] Renamed files removed from every index
[ ] Documentation tests or link checks pass
```

A filename change is a coordinated change affecting:

- this map;
- root and section README files;
- all direct links;
- contract-lock references;
- CLI or generated-report references when applicable;
- project-template mirrors when applicable.

---

## 10. Naming rules

- Permanent Markdown filenames use uppercase `SNAKE_CASE.md`, except conventional root files.
- ADR filenames use `ADR-NNNN-SHORT-TITLE.md`.
- Section directories use lowercase names.
- The active project and its template use corresponding relative paths and roles. For `00_PROJECT_START_HERE`, `VALIDATION_SPEC`, `TEST_COVERAGE_MATRIX`, `STATUS_LEDGER` and `RELEASE_CRITERIA`, active-project files end in `__PROJECT_DOCS.md` and template files end in `__TEMPLATES_PROJECT_DOCS.md`.
- A document name must describe one stable responsibility.
- A new document is justified only when it has a distinct owner, audience or change lifecycle.
- Tiny subtopics remain sections of an existing authoritative document.

---

## 11. Validation

The documentation set is validated through the documentation checker.

Canonical command:

```text
gf-wordbench docs check
```

The checker should verify:

1. every inventory path exists;
2. internal links resolve;
3. no undocumented permanent Markdown files exist;
4. active-project and template structures expose matching required roles, including the canonical project/template filename mapping;
5. framework documents do not contain active-language identifiers outside allowed examples;
6. all seven anti-drift documents are present and mutually linked;
7. referenced schema IDs and validation status values are canonical;
8. ADR numbers are unique and accepted ADR paths are current;
9. required document metadata is present where applicable;
10. deprecated paths are absent from current navigation;
11. Wordbench documents do not define Portfolio registries or cross-workspace orchestration;
12. no document requires per-claim implementation progress labels.

Strict mode:

```text
gf-wordbench docs check --strict
```

---

## 12. Inventory count

The permanent target inventory contains **155 files**:

- repository and framework documentation: **113**;
- active-language project documentation and configuration: **21**;
- reusable project-template documentation and configuration: **21**.

Generated run reports, scenario files, gold files, language source files and test fixtures are not counted as permanent documentation inventory entries unless explicitly listed above.

---

## 13. Governing rule

> Every permanent document must have one clear responsibility, one authoritative owner and one place in this map.

A document that duplicates another document's authority creates drift and must be merged, narrowed or converted into a link.
