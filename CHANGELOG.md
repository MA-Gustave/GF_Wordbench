# Changelog

All notable changes to **GF Wordbench** are documented in this file.

GF Wordbench uses semantic versioning for application releases and explicit versioning for persisted schemas and inter-component contracts.

The project is currently under active development. Until the first release is published, all completed work remains under **Unreleased**.

---

## Changelog rules

### Release headings

Published releases use:

```text
## [MAJOR.MINOR.PATCH] - YYYY-MM-DD
```

Example:

```text
## [1.2.0] - 2026-09-15
```

The date is the actual publication date in ISO 8601 format.

### Change categories

Each release may contain:

- **Added** — new capabilities, files, commands, schemas, reports, scenarios, or supported workflows;
- **Changed** — compatible changes to existing behavior;
- **Deprecated** — supported behavior scheduled for removal;
- **Removed** — deleted behavior or compatibility support;
- **Fixed** — defect corrections;
- **Security** — security, trust-boundary, path-safety, process-safety, or data-protection changes;
- **Migration** — actions required when upgrading existing installations or projects.

Empty categories should be omitted.

### Required changelog entries

A changelog entry is required when a change affects any of the following:

- CLI or GUI behavior;
- validation modes;
- public Python interfaces;
- GF command construction;
- external-tool behavior;
- persisted schemas;
- artifact paths or filenames;
- status or diagnostic values;
- project configuration;
- scenario or gold-file formats;
- release gates;
- migration behavior;
- backward compatibility;
- documented interfile contracts.

Internal refactoring that preserves all observable contracts does not require an entry unless it materially affects maintainability, performance, or risk.

### Contract and schema references

Changes to locked contracts should identify the affected contract or schema when practical.

Examples:

```text
- Changed `IFC-AUDIT-005` to preserve raw compiler output before normalization.
- Added `gf-wordbench.run-summary/1.1`.
```

A schema or contract version must not be inferred from the application version.

### Unreleased section

All completed but unpublished changes are recorded under `Unreleased`.

When a release is published:

1. copy the relevant `Unreleased` entries into a versioned release section;
2. add the release date;
3. remove entries that were not included in the release;
4. leave a fresh `Unreleased` section at the top;
5. verify migration notes and compatibility claims.

---

## [Unreleased]

### Added

#### Product identity and scope

- Established the product name **GF Wordbench**.
- Defined GF Wordbench as a reusable validation and development workbench for one active GF language project per repository copy.
- Defined the framework as an orchestrator around native GF tooling rather than a replacement for the GF compiler, runtime, shell, parser, linearizer, or generator.
- Defined the separation between:
  - the permanent framework;
  - the active language project;
  - the reusable project template;
  - generated run artifacts.

#### Contract locks

- Added the framework interfile contract lock:
  - `docs/INTERFILE_CONTRACT_LOCK.md`
- Added the external-tool contract lock:
  - `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- Added the persisted-schema lock:
  - `docs/PERSISTED_SCHEMA_LOCK.md`
- Added the active-project interfile contract lock:
  - `project/docs/INTERFILE_CONTRACT_LOCK.md`
- Added the reusable project contract-lock template:
  - `templates/project/docs/INTERFILE_CONTRACT_LOCK.md`
- Defined coordinated-change rules for providers, consumers, schemas, configuration, tests, artifacts, and migrations.
- Defined ownership rules for generated artifacts.
- Defined dependency-direction constraints between orchestration, stages, models, reports, GUI, CLI, and process utilities.

#### Persisted schemas

- Defined canonical schema identities for:
  - `gf-wordbench.project`;
  - `gf-wordbench.app-state`;
  - `gf-wordbench.run-summary`;
  - `gf-wordbench.artifact-manifest`;
  - `gf-wordbench.scenario-output`;
  - `gf-wordbench.scenario-gold`.
- Defined explicit `schema_id` and `schema_version` requirements.
- Defined canonical UTF-8, newline, timestamp, integer, path, ordering, and atomic-write rules.
- Defined the canonical run-directory structure.
- Defined canonical file-result and scenario-result persistence.
- Defined canonical manifest roles and SHA-256 integrity checks.
- Defined compatibility and migration rules for legacy GF Audit state and summary files.

#### Validation model

- Defined the target validation modes:
  - `quick`;
  - `checkpoint`;
  - `release`;
  - `diagnostic`.
- Defined legacy mode aliases:
  - `file` → `quick`;
  - `all` → `diagnostic`.
- Defined separate validation layers:
  - static source scanning;
  - module compilation;
  - final PGF construction;
  - native GF scenario execution;
  - normalized-output comparison;
  - regression comparison;
  - release gates.
- Defined separate result models for file validation and scenario validation.
- Defined the distinction between:
  - validation status;
  - execution state;
  - diagnostic class;
  - error kind.

#### Native GF scenarios

- Selected native `.gfs` scripts as the scenario execution format.
- Defined stable scenario markers and section completion checks.
- Defined normalized `.out` files.
- Defined reviewed `.gold` files for regression comparison.
- Defined explicit gold-update operations.
- Prohibited silent gold updates during normal validation.
- Defined bounded parse, linearization, generation, morphology, loading, and missing-linearization scenarios.

#### Reporting

- Preserved `summary.json` as the primary machine-readable run record.
- Preserved `summary.md` as the primary human-readable summary.
- Preserved `AI_READY.md` as the bounded AI handoff packet.
- Defined `manifest.json` for artifact identity and integrity.
- Defined stable ownership for:
  - compiler logs;
  - scan logs;
  - scenario logs;
  - normalized outputs;
  - detail files;
  - `.gfo` artifacts;
  - `.pgf` artifacts.
- Defined deterministic top-error ordering and canonical `top_errors.txt` formatting.

#### Documentation system

- Defined the final documentation architecture for:
  - product overview;
  - framework architecture;
  - GF integration;
  - validation;
  - scenarios and gold testing;
  - diagnostics;
  - reporting;
  - configuration;
  - usage;
  - project lifecycle;
  - framework development;
  - operations;
  - release management;
  - architectural decisions;
  - reference material.
- Defined the active-language documentation set.
- Defined a clean reusable project-template documentation set.
- Defined anti-drift ownership rules to prevent the same normative rule from being independently maintained in multiple documents.

### Changed

#### Framework direction

- Refined the original GF Audit concept into GF Wordbench.
- Replaced the proposed multi-language profile model with a single-active-language project model.
- Rejected simultaneous language management as a core requirement.
- Replaced the idea of a large external plugin system with direct, documented integration points.
- Limited extensibility to validated stages, schemas, reports, diagnostic rules, and project assets with explicit contracts.

#### Configuration ownership

- Moved language-specific configuration responsibility away from application defaults and toward `project/project.toml`.
- Reserved application state for local paths, UI preferences, and last-run information.
- Prohibited active-language architecture, entrypoints, checkpoints, and scenario policy from being stored in GUI state.
- Centralized application name and version metadata.
- Defined project-relative canonical paths for project assets.
- Defined run-relative canonical paths for generated artifacts.

#### Diagnostic semantics

- Reserved diagnostic classes for causal relationships:
  - `ok`;
  - `direct`;
  - `downstream`;
  - `ambiguous`;
  - `noise`;
  - `skipped`.
- Moved technical failure categories into `error_kind`.
- Moved cancellation, timeout, and launch failure into execution-state semantics.
- Defined `ERROR` as a framework or execution inability to perform or interpret a required validation.
- Defined `FAIL` as a completed validation that did not satisfy its criterion.

#### GF integration

- Confirmed GF as the execution authority for:
  - compilation;
  - PGF construction;
  - loading;
  - parsing;
  - linearization;
  - generation;
  - grammar introspection.
- Limited Python responsibilities to:
  - configuration;
  - orchestration;
  - process control;
  - evidence capture;
  - normalization;
  - classification;
  - comparison;
  - reporting.
- Prohibited Python reimplementation of GF language semantics.
- Defined raw-evidence preservation before normalization.
- Defined process timeouts and launch failures as distinct from GF-reported failures.

#### Existing GF Audit baseline

- Corrected static scanning of GF string literals containing doubled quotes.
- Prevented structural scans from treating code-like content inside strings as executable GF syntax.
- Aligned CLI tests with report generation owned by the audit core.
- Corrected report-test syntax.
- Added complete top-error output to the AI-ready report.
- Centralized package version metadata.
- Validated the corrected GF Audit baseline with all available tests passing.

### Deprecated

- The application name `gf-audit` is deprecated for the future GF Wordbench implementation.
- The state filename `.gf_audit_state.json` is deprecated.
- Unversioned persisted summaries are deprecated.
- The artifact field alias `ai_brief_path` is deprecated.
- The legacy modes `file` and `all` are deprecated as canonical values.
- Language-specific defaults embedded in framework configuration are deprecated.
- Absolute project-file paths in canonical persisted summaries are deprecated.
- SHA-1 short fingerprints are deprecated for new canonical output.
- Report consumers parsing Markdown as machine data are deprecated.
- Normal workflows that rebuild artifact paths from duplicated filename constants are deprecated.

### Removed

- Removed simultaneous multi-language project management from the target scope.
- Removed the proposed requirement for a runtime language-profile registry.
- Removed the proposed requirement for a general-purpose plugin marketplace.
- Removed the requirement to create a separate documentation file for every minor subtopic.
- Removed `script_error` and `framework_error` from the target diagnostic-class vocabulary.
- Removed `CANCELLED` from the target validation-status vocabulary.
- Removed silent gold-file rewriting from accepted validation behavior.

### Fixed

- Fixed false-positive static diagnostics caused by doubled GF quotes inside string literals.
- Fixed outdated CLI smoke-test assumptions about report ownership.
- Fixed an invalid assignment-expression assertion in the report test suite.
- Fixed incomplete AI-ready top-error presentation.
- Fixed duplicated version values across package and application configuration.
- Fixed ambiguity between validation status, execution state, error kind, and diagnostic class.
- Fixed ownership ambiguity between application state and active-project configuration.
- Fixed path-contract ambiguity between project-relative, run-relative, and environment-specific paths.
- Fixed documentation over-fragmentation by consolidating documents that shared the same owner and change cycle.

### Security

- Prohibited credentials, tokens, private keys, cookies, and secret arguments from persisted files.
- Required explicit process working directories and controlled environment overlays.
- Required path containment checks for project-owned and run-owned artifacts.
- Required atomic writes for state, summary, manifest, project migrations, and gold updates.
- Required raw-evidence preservation before normalization.
- Required explicit confirmation or dedicated automation flags for gold updates.
- Required SHA-256 integrity hashes for final run manifests.
- Prohibited consumers from silently rewriting artifacts owned by another component.

### Migration

#### GF Audit to GF Wordbench

The planned migration includes:

- rename the application identity from `gf-audit` to `gf-wordbench`;
- replace `.gf_audit_state.json` with `.gf_wordbench_state.json`;
- introduce `project/project.toml`;
- move active-language settings from application defaults and state into the project file;
- migrate `file` mode to `quick`;
- migrate `all` mode to `diagnostic`;
- migrate unversioned summaries to `gf-wordbench.run-summary/1.0`;
- map `ai_brief_path` and legacy `ai_ready_path` to `artifacts.ai_ready`;
- migrate legacy top-error mappings to canonical arrays;
- migrate SHA-1 short fingerprints to canonical SHA-256 fingerprints;
- convert project-owned absolute paths to project-relative paths when possible;
- convert generated artifact paths to run-relative paths;
- preserve legacy source files until canonical destinations are validated and written successfully.

#### Project initialization

A new active-language project will require:

- `project/project.toml`;
- project architecture documentation;
- module dependency mapping;
- category and lincat contracts;
- morphology and syntax specifications;
- validation specification;
- status and decision ledgers;
- required `.gfs` scenarios;
- reviewed `.gold` expectations;
- project interfile contract declarations.

---

## Release history

No public GF Wordbench release has been published yet.

The first published release will be added below this line using an explicit version and publication date.

<!--
Example release structure:

## [1.0.0] - YYYY-MM-DD

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

### Migration
-->
