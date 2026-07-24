# GF Wordbench — Documentation Correction Ledger

**Document ID:** `GF-WB-DOC-CORRECTION-LEDGER`  
**Status:** Active tracking document  
**Applies to:** coordinated correction of the audited GF Wordbench documentation set  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Last updated:** `2026-07-24`

---

## 1. Rules

- One row represents one repository path.
- One parallel conversation edits one target file only.
- Every conversation receives the unchanged alignment lock and any directly relevant specialized lock or ADR.
- `CORRECTED` means a complete candidate exists; `VALIDATED` means it has passed cross-document and owner-contract review.
- A contradiction is recorded as `BLOCKED` or `REVIEW_REQUIRED`; it is never silently resolved in the target file.
- The integration conversation is the only place that changes row status.

## 2. Status values

| Status | Meaning |
|---|---|
| `TODO` | Not assigned or not corrected |
| `IN_PROGRESS` | Assigned to one active correction conversation |
| `CORRECTED` | Complete corrected candidate returned |
| `REVIEW_REQUIRED` | Candidate needs an owner or cross-document decision |
| `BLOCKED` | Conflicting authority or missing evidence prevents correction |
| `VALIDATED` | Corrected and checked against ADRs, locks and owner documents |

## 3. Baseline counts

```text
audited path set at ledger creation: 153
repository paths excluded after reconciliation: 2
current managed path set: 151
previously corrected minor set: 53
current correction queue: 98
queue files corrected by this anti-drift update: 3
queue files not yet edited after this update: 95
new anti-drift controls validated: 2
existing anti-drift locks corrected: 5
```

The previously corrected 53-file set is not duplicated in the queue. Two of its project locks are nevertheless listed in the management table because the global Wordbench/Portfolio boundary required a coordinated lock update.

The two excluded paths are recorded explicitly in section 5. They are not considered pending documentation files and do not block completion.

## 4. Anti-drift management set

| Path | Status | Change | Conversation | Validation |
|---|---|---|---|---|
| `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` | `VALIDATED` | New cross-document normative lock | anti-drift integration | aligned `2026-07-24` |
| `docs/DOCUMENTATION_CORRECTION_LEDGER.md` | `VALIDATED` | Correction tracking ledger; repository exclusions and targeted template-reference repairs recorded | anti-drift integration | aligned `2026-07-24` |
| `docs/INTERFILE_CONTRACT_LOCK.md` | `CORRECTED` | Rewritten clean framework boundary and contract registry | anti-drift integration | aligned `2026-07-24` |
| `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` | `CORRECTED` | Rewritten clean GF/process boundary and tool allowlist contract | anti-drift integration | aligned `2026-07-24` |
| `docs/PERSISTED_SCHEMA_LOCK.md` | `CORRECTED` | Rewritten clean schema ownership, versioning and public-artifact boundary | anti-drift integration | aligned `2026-07-24` |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | `CORRECTED` | Rewritten clean Albanian active-project contract; open release locks preserved | anti-drift integration | aligned `2026-07-24` |
| `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` | `CORRECTED` | Rewritten clean generic single-project template contract | anti-drift integration | aligned `2026-07-24` |

## 5. Repository reconciliation exclusions

| Path | Disposition | Reason | Required follow-up |
|---|---|---|---|
| `CHANGELOG.md` | Excluded | The file was intentionally deleted and is not maintained as part of the documentation correction program. | Do not recreate it and do not include it in completion counts. |
| `docs/development/GF_AUDIT_CAPABILITY_MIGRATION.md` | Excluded | The path does not exist and no replacement document is expected. | Remove stale references to this path from `docs/DOCUMENTATION_MAP.md` and any generated inventory. |

## 6. Remaining correction queue

| # | Path | Status | Correction class | Assigned conversation | Dependencies or validation note |
|---:|---|---|---|---|---|
| 1 | `docs/00_ERRATUM.md` | `TODO` | Merge then retire or rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 2 | `docs/reference/COMMAND_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 3 | `docs/INTERFILE_CONTRACT_LOCK.md` | `CORRECTED` | Normative lock alignment | — | Rewritten against accepted ADRs; implementation verification remains required. |
| 4 | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` | `CORRECTED` | Normative lock alignment | — | Rewritten against accepted ADRs; implementation verification remains required. |
| 5 | `docs/PERSISTED_SCHEMA_LOCK.md` | `CORRECTED` | Normative lock alignment | — | Rewritten against accepted ADRs; implementation verification remains required. |
| 6 | `README.md` | `TODO` | Root document reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 7 | `CONTRIBUTING.md` | `TODO` | Root document reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 8 | `SECURITY.md` | `TODO` | Root document reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 9 | `docs/00_START_HERE.md` | `TODO` | Documentation reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 10 | `docs/PRODUCT_OVERVIEW.md` | `TODO` | Documentation reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 11 | `docs/SCOPE_AND_NON_GOALS.md` | `TODO` | Documentation reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 12 | `docs/DOCUMENTATION_MAP.md` | `TODO` | Targeted path and inventory reconciliation | — | Replace the five stale `templates/project/docs/*__PROJECT_DOCS.md` paths with their `*__TEMPLATES_PROJECT_DOCS.md` paths; remove the stale `GF_AUDIT_CAPABILITY_MIGRATION.md` entry. |
| 13 | `docs/REPOSITORY_STRUCTURE.md` | `TODO` | Documentation reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 14 | `docs/GLOSSARY.md` | `TODO` | Documentation reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 15 | `docs/architecture/PRODUCT_BOUNDARIES.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 16 | `docs/architecture/IMPLEMENTATION_ALIGNMENT.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 17 | `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 18 | `docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 19 | `docs/decisions/ADR-0006-AI-READY-REPORT.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 20 | `docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 21 | `docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 22 | `docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 23 | `docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 24 | `docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 25 | `docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md` | `TODO` | ADR normative review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 26 | `docs/architecture/ARCHITECTURE_OVERVIEW.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 27 | `docs/architecture/COMPONENT_MAP.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 28 | `docs/architecture/DEPENDENCY_RULES.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 29 | `docs/architecture/DATA_MODEL.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 30 | `docs/architecture/PROCESS_EXECUTION_MODEL.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 31 | `docs/architecture/ERROR_HANDLING_MODEL.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 32 | `docs/architecture/EXECUTION_FLOW.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 33 | `docs/architecture/EXTENSION_BOUNDARIES.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 34 | `docs/architecture/ARTIFACT_MODEL.md` | `TODO` | Architecture merge or normative rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 35 | `docs/configuration/CONFIGURATION_OVERVIEW.md` | `TODO` | Configuration contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 36 | `docs/configuration/PROJECT_TOML_REFERENCE.md` | `TODO` | Configuration contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 37 | `docs/configuration/ENVIRONMENT_AND_PATHS.md` | `TODO` | Configuration contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 38 | `docs/configuration/APPLICATION_STATE_REFERENCE.md` | `TODO` | Configuration contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 39 | `docs/projects/PROJECT_MODEL.md` | `TODO` | Project model rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 40 | `docs/projects/CREATING_A_PROJECT.md` | `TODO` | Project model rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 41 | `docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md` | `TODO` | Project model rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 42 | `docs/projects/CLONING_AND_RESETTING.md` | `TODO` | Project model rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 43 | `docs/projects/PROJECT_COMPLETION_CHECKLIST.md` | `TODO` | Project model rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 44 | `docs/gf/GF_TOOLCHAIN_INTEGRATION.md` | `TODO` | GF boundary or execution contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 45 | `docs/gf/GF_PATH_RESOLUTION.md` | `TODO` | GF boundary or execution contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 46 | `docs/gf/GF_COMPILATION.md` | `TODO` | GF boundary or execution contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 47 | `docs/gf/GF_COMMAND_CONSTRUCTION.md` | `TODO` | GF boundary or execution contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 48 | `docs/validation/VALIDATION_OVERVIEW.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 49 | `docs/validation/VALIDATION_MODES.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 50 | `docs/validation/VALIDATION_PIPELINE.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 51 | `docs/validation/FILE_SELECTION.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 52 | `docs/validation/STATIC_SCANNING.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 53 | `docs/validation/COMPILATION_VALIDATION.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 54 | `docs/validation/SCENARIO_VALIDATION.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 55 | `docs/validation/REGRESSION_COMPARISON.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 56 | `docs/validation/RELEASE_GATES.md` | `TODO` | Validation contract rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 57 | `docs/diagnostics/DIAGNOSTIC_OVERVIEW.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 58 | `docs/diagnostics/ERROR_CLASSIFICATION.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 59 | `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 60 | `docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 61 | `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 62 | `docs/diagnostics/TOOL_CATALOG.md` | `TODO` | Diagnostic contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 63 | `docs/reports/REPORTING_OVERVIEW.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 64 | `docs/reports/SUMMARY_JSON_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 65 | `docs/reports/SUMMARY_MARKDOWN_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 66 | `docs/reports/AI_READY_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 67 | `docs/reports/ARTIFACT_MANIFEST.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 68 | `docs/reports/RAW_LOGS_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 69 | `docs/reference/SCHEMA_INDEX.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 70 | `docs/reference/STATUS_VALUES.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 71 | `docs/reference/DIAGNOSTIC_KINDS.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 72 | `docs/reference/EXIT_CODES.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 73 | `docs/reference/FILE_NAMING_CONVENTIONS.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 74 | `docs/reference/TERMINOLOGY_REFERENCE.md` | `TODO` | Schema and reference reconciliation | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 75 | `docs/usage/CLI_REFERENCE.md` | `TODO` | User contract and implementation-status review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 76 | `docs/usage/GUI_REFERENCE.md` | `TODO` | User contract and implementation-status review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 77 | `docs/usage/INSTALLATION.md` | `TODO` | User contract and implementation-status review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 78 | `docs/usage/QUICK_START.md` | `TODO` | User contract and implementation-status review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 79 | `docs/operations/RUN_DIRECTORY_LIFECYCLE.md` | `TODO` | Operational contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 80 | `docs/operations/AUTOMATION_AND_CI.md` | `TODO` | Operational contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 81 | `docs/development/DEVELOPMENT_SETUP.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 82 | `docs/development/CODEBASE_GUIDE.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 83 | `docs/development/TESTING_GF_WORDBENCH.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 84 | `docs/development/DEBUGGING_THE_FRAMEWORK.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 85 | `docs/development/EXTENDING_GF_WORDBENCH.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 86 | `docs/development/BACKWARD_COMPATIBILITY.md` | `TODO` | Implementation-alignment rewrite | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 87 | `docs/release/RELEASE_PROCESS.md` | `TODO` | Release contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 88 | `docs/release/MIGRATION_AND_DEPRECATION.md` | `TODO` | Release contract review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 89 | `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md` | `TODO` | Active-project source-evidence review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 90 | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` | `TODO` | Active-project source-evidence review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 91 | `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` | `TODO` | Active-project source-evidence review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 92 | `project/docs/STATUS_LEDGER__PROJECT_DOCS.md` | `TODO` | Active-project source-evidence review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 93 | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` | `TODO` | Active-project source-evidence review | — | Apply alignment lock; inspect owner ADRs and specialized locks. |
| 94 | `templates/project/docs/00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md` | `TODO` | Targeted template-reference reconciliation | — | Replace stale template-local and repository paths ending in `__PROJECT_DOCS.md` with the corresponding `__TEMPLATES_PROJECT_DOCS.md` paths; do not alter active-project paths. |
| 95 | `templates/project/docs/VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md` | `TODO` | Targeted template-reference reconciliation | — | Replace stale template-local and repository paths ending in `__PROJECT_DOCS.md` with the corresponding `__TEMPLATES_PROJECT_DOCS.md` paths; do not alter active-project paths. |
| 96 | `templates/project/docs/TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` | `TODO` | Targeted template-reference reconciliation | — | Replace stale template-local and repository paths ending in `__PROJECT_DOCS.md` with the corresponding `__TEMPLATES_PROJECT_DOCS.md` paths; do not alter active-project paths. |
| 97 | `templates/project/docs/STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md` | `TODO` | Targeted template-reference reconciliation | — | Replace stale template-local and repository paths ending in `__PROJECT_DOCS.md` with the corresponding `__TEMPLATES_PROJECT_DOCS.md` paths; do not alter active-project paths. |
| 98 | `templates/project/docs/RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` | `TODO` | Targeted template-reference reconciliation | — | Replace stale template-local and repository paths ending in `__PROJECT_DOCS.md` with the corresponding `__TEMPLATES_PROJECT_DOCS.md` paths; do not alter active-project paths. |

## 7. Per-file integration record

For each completed correction, replace the row note with:

```text
conversation: <identifier>
source snapshot: <identifier or hash>
decisions applied: <ADR and lock IDs>
material changes: <short summary>
evidence checked: <source, tests, run or unknown>
remaining conflicts: <none or explicit list>
validated by: <integration review>
```

## 8. Completion condition

The documentation correction program is complete only when every queue row is `VALIDATED`, all temporary errata are integrated or explicitly retained, links and canonical paths are checked, and no owner document contradicts the accepted Wordbench/Portfolio product boundary.
